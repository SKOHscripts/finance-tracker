"""EVM chains, through the multichain block-explorer API.

One connector for Ethereum, Base, Arbitrum, Optimism, Polygon and BSC: the V2
API serves all of them from a single host, selected by a ``chainid`` parameter,
so adding a chain is a line in a mapping rather than another integration.

Balances are derived from the transfer log rather than read from a balance
endpoint. That is deliberate: the per-address token-balance endpoint is a paid
feature, while the transfer log is free — and the same call that nets a balance
also yields the history a cost basis needs. The trade-off is that a rebasing or
fee-on-transfer token, whose balance changes without a transfer, will be
slightly off; those are flagged rather than silently trusted.
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import requests

from finance_tracker.config import ETHERSCAN_API_URL, WALLET_HTTP_TIMEOUT
from finance_tracker.domain.enums import EVM_CHAIN_IDS, Chain, TransferDirection

from .base import (
    RawTransfer,
    TokenBalance,
    UnsupportedChainError,
    WalletProviderError,
    WalletSnapshot,
    optional_int,
    scale,
    )

# Rows per page. The API caps a page at 10 000; asking for less and paging is
# gentler on the free tier's rate limit.
_PAGE_SIZE = 1000

# Stop after this many pages of each kind. A wallet with more than 20 000
# transfers is beyond what a weekly scan should be pulling on a free key: the
# history is marked incomplete and the cost basis drops to low confidence
# rather than the sync hanging.
_MAX_PAGES = 20

# Native coin of each supported chain, for display.
_NATIVE_SYMBOLS: dict[Chain, str] = {
    Chain.ETHEREUM: "ETH",
    Chain.BASE: "ETH",
    Chain.ARBITRUM: "ETH",
    Chain.OPTIMISM: "ETH",
    Chain.POLYGON: "POL",
    Chain.BSC: "BNB",
    }

# Balances below this many units are treated as dust and left out. Airdropped
# spam tokens arrive in the millions, so this filters by value being zero, not
# by amount being small.
_DUST_THRESHOLD = Decimal("0")


class EvmProvider:
    """Read balances and transfers for one EVM address.

    Parameters
    ----------
    chain : Chain
        Which EVM chain to query.
    api_key : str, optional
        Explorer API key. Without one the API allows a very low request rate
        and will usually refuse; the error message says so plainly.
    base_url : str, optional
        Endpoint override, for a self-hosted or alternative explorer.
    timeout : int, optional
        Per-request timeout in seconds.
    session : requests.Session, optional
        Session to reuse.
    """

    supports_history = True

    def __init__(
        self,
        chain: Chain,
        api_key: str = "",
        base_url: str = ETHERSCAN_API_URL,
        timeout: int = WALLET_HTTP_TIMEOUT,
        session: Optional[requests.Session] = None,
        ) -> None:
        if chain not in EVM_CHAIN_IDS:
            raise UnsupportedChainError(f"{chain.value} n'est pas une chaîne EVM supportée.")
        self.chain = chain
        self.chain_id = EVM_CHAIN_IDS[chain]
        self.api_key = api_key or ""
        self.base_url = (base_url or ETHERSCAN_API_URL).rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()

    # ── transport ─────────────────────────────────────────────────────────────

    def _call(self, module: str, action: str, **params) -> Any:
        """Call the explorer and return the ``result`` field.

        Raises
        ------
        WalletProviderError
            On a transport failure or an explorer-level error. "No transactions
            found" is not an error: it comes back as an empty list.
        """
        query = {
            "chainid": self.chain_id,
            "module": module,
            "action": action,
            **params,
            }
        if self.api_key:
            query["apikey"] = self.api_key

        try:
            response = self._session.get(self.base_url, params=query, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.RequestException as exc:
            raise WalletProviderError(
                f"Explorateur {self.chain.value} injoignable : {exc}"
                ) from exc
        except ValueError as exc:
            raise WalletProviderError(
                f"Réponse illisible de l'explorateur {self.chain.value} : {exc}"
                ) from exc

        status = str(payload.get("status", ""))
        message = str(payload.get("message", ""))
        result = payload.get("result")

        if status == "1":
            return result

        # An empty history is a normal answer, not a failure.
        if "no transactions found" in message.lower() or "no records found" in message.lower():
            return []

        detail = result if isinstance(result, str) else message
        if not self.api_key:
            raise WalletProviderError(
                f"L'explorateur {self.chain.value} a refusé la requête ({detail}). "
                "Une clé d'API gratuite est nécessaire pour les chaînes EVM : "
                "renseigne-la dans les réglages."
                )
        raise WalletProviderError(
            f"L'explorateur {self.chain.value} a refusé la requête : {detail}"
            )

    def _paged(self, action: str, address: str) -> list[dict]:
        """Fetch every page of *action* for *address*.

        Returns
        -------
        list[dict]
            Concatenated rows. A short page ends the walk; hitting
            ``_MAX_PAGES`` ends it too, and the caller marks the history
            incomplete.
        """
        rows: list[dict] = []
        for page in range(1, _MAX_PAGES + 1):
            chunk = self._call(
                "account", action,
                address=address, startblock=0, endblock=99999999,
                page=page, offset=_PAGE_SIZE, sort="asc",
                )
            if not isinstance(chunk, list) or not chunk:
                break
            rows.extend(chunk)
            if len(chunk) < _PAGE_SIZE:
                break
        return rows

    # ── reading ───────────────────────────────────────────────────────────────

    def _native_balance(self, address: str) -> Decimal:
        """Exact native-coin balance, read from the chain rather than netted."""
        result = self._call("account", "balance", address=address, tag="latest")
        return scale(result, 18)

    @staticmethod
    def _row_transfer(row: dict, address: str, index: int) -> Optional[RawTransfer]:
        """Turn one explorer row into a transfer, or None when unusable."""
        try:
            timestamp = datetime.fromtimestamp(int(row["timeStamp"]), tz=timezone.utc)
        except (KeyError, ValueError, TypeError):
            return None

        sender = str(row.get("from", "")).lower()
        recipient = str(row.get("to", "")).lower()
        owner = address.lower()

        if owner == recipient:
            direction, counterparty = TransferDirection.IN, sender
        elif owner == sender:
            direction, counterparty = TransferDirection.OUT, recipient
        else:
            # Neither side is the watched address: not this wallet's movement.
            return None

        contract = str(row.get("contractAddress", "")).lower()
        is_native = not contract
        decimals = optional_int(row.get("tokenDecimal"), 18)
        units = scale(row.get("value", "0"), decimals)
        if units <= 0:
            return None

        return RawTransfer(
            tx_hash=str(row.get("hash", "")),
            # The explorer does not expose a log index on these endpoints;
            # position within the fetched page keeps rows distinct.
            log_index=index,
            timestamp=timestamp,
            direction=direction,
            contract_address=contract,
            symbol=str(row.get("tokenSymbol", "")).upper(),
            decimals=decimals,
            units=units,
            counterparty=counterparty,
            is_native=is_native,
            )

    def fetch(self, address: str, with_history: bool = True) -> WalletSnapshot:
        """Read balances, and transfers when asked.

        Parameters
        ----------
        address : str
            EVM address, checksummed or not.
        with_history : bool, optional
            Whether to fetch transfer history as well.

        Returns
        -------
        WalletSnapshot
            Balances, transfers, and any caveat worth showing.

        Raises
        ------
        WalletProviderError
            When the explorer is unreachable or rejects the request.
        """
        notes: list[str] = []
        snapshot = WalletSnapshot()

        native_symbol = _NATIVE_SYMBOLS.get(self.chain, "ETH")
        native_units = self._native_balance(address)

        # Token transfers: one call serving both the balances and the history.
        token_rows = self._paged("tokentx", address)
        history_complete = len(token_rows) < _PAGE_SIZE * _MAX_PAGES

        transfers: list[RawTransfer] = []
        for index, row in enumerate(token_rows):
            transfer = self._row_transfer(row, address, index)
            if transfer is not None:
                transfers.append(transfer)

        if with_history:
            native_rows = self._paged("txlist", address)
            history_complete = history_complete and len(native_rows) < _PAGE_SIZE * _MAX_PAGES
            for index, row in enumerate(native_rows):
                # A failed transaction moved nothing but still cost gas.
                if str(row.get("isError", "0")) == "1":
                    continue
                row = {**row, "tokenSymbol": native_symbol, "tokenDecimal": 18,
                       "contractAddress": ""}
                transfer = self._row_transfer(row, address, index)
                if transfer is not None:
                    transfers.append(transfer)

        # Net the token transfers into balances. The native balance is read
        # directly, so it is exact; token balances are a reconstruction.
        netted: dict[str, dict] = {}
        for transfer in transfers:
            if transfer.is_native:
                continue
            entry = netted.setdefault(transfer.contract_address, {
                "symbol": transfer.symbol,
                "decimals": transfer.decimals,
                "units": Decimal("0"),
                })
            if transfer.direction is TransferDirection.IN:
                entry["units"] += transfer.units
            else:
                entry["units"] -= transfer.units

        balances = [TokenBalance(
            contract_address="",
            symbol=native_symbol,
            name=native_symbol,
            decimals=18,
            units=native_units,
            is_native=True,
            )]

        for contract, entry in netted.items():
            if entry["units"] <= _DUST_THRESHOLD:
                continue
            balances.append(TokenBalance(
                contract_address=contract,
                symbol=entry["symbol"],
                name=entry["symbol"],
                decimals=entry["decimals"],
                units=entry["units"],
                ))

        if not history_complete:
            notes.append(
                "Historique tronqué : cette adresse a plus de mouvements que la "
                "synchronisation n'en récupère. Les soldes de tokens et le prix de "
                "revient dérivé sont incomplets."
                )
        notes.append(
            "Soldes de tokens reconstitués depuis le journal des transferts. Un token "
            "à solde variable (rebase, taxe au transfert) peut s'en écarter."
            )

        transfers.sort(key=lambda t: t.timestamp)
        snapshot.balances = balances
        snapshot.transfers = transfers if with_history else []
        snapshot.history_complete = history_complete
        snapshot.notes = notes
        return snapshot
