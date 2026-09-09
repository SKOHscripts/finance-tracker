"""Bitcoin, through a public Esplora-style API.

The cleanest of the three connectors: no key, no account, a complete history,
and an exact balance. Bitcoin's UTXO model also makes the cost basis unusually
honest — every transaction has a signed net effect on the address, so a
purchase and a self-transfer are told apart by whether the counterparty inputs
belong to the same address.

The default host is mempool.space; any Esplora-compatible endpoint works,
including a self-hosted one, which is the point of the override.
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import requests

from finance_tracker.config import MEMPOOL_API_URL, WALLET_HTTP_TIMEOUT
from finance_tracker.domain.enums import Chain, TransferDirection

from .base import (
    RawTransfer,
    TokenBalance,
    WalletProviderError,
    WalletSnapshot,
    scale,
    )

SATS_PER_BTC = Decimal("100000000")
BITCOIN_DECIMALS = 8

# The API returns 25 transactions per page. Stop after this many pages: an
# address with 1 250 transactions is an exchange's, not a personal wallet's,
# and the history is marked incomplete rather than paged forever.
_MAX_PAGES = 50


class BitcoinProvider:
    """Read the balance and transaction history of one Bitcoin address.

    Parameters
    ----------
    base_url : str, optional
        Esplora-compatible API root. Override it to use your own node.
    timeout : int, optional
        Per-request timeout in seconds.
    session : requests.Session, optional
        Session to reuse.
    """

    chain = Chain.BITCOIN
    supports_history = True

    def __init__(
        self,
        base_url: str = MEMPOOL_API_URL,
        timeout: int = WALLET_HTTP_TIMEOUT,
        session: Optional[requests.Session] = None,
        ) -> None:
        self.base_url = (base_url or MEMPOOL_API_URL).rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()

    def _get(self, path: str):
        """GET *path* below the API root and return decoded JSON."""
        try:
            response = self._session.get(f"{self.base_url}{path}", timeout=self.timeout)
            if response.status_code == 400:
                raise WalletProviderError(
                    "Adresse Bitcoin invalide, ou non reconnue par l'indexeur."
                    )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            raise WalletProviderError(f"Indexeur Bitcoin injoignable : {exc}") from exc
        except ValueError as exc:
            raise WalletProviderError(f"Réponse illisible de l'indexeur Bitcoin : {exc}") from exc

    def _balance_sats(self, address: str) -> Decimal:
        """Confirmed balance in satoshis: funded outputs minus spent ones."""
        payload = self._get(f"/address/{address}")
        stats = (payload or {}).get("chain_stats", {})
        funded = Decimal(str(stats.get("funded_txo_sum", 0)))
        spent = Decimal(str(stats.get("spent_txo_sum", 0)))
        return funded - spent

    def _transactions(self, address: str) -> tuple[list[dict], bool]:
        """Walk the address's confirmed transaction history.

        Returns
        -------
        tuple
            The transactions, newest first, and whether the walk reached the
            end of the history.
        """
        collected: list[dict] = []
        last_seen: Optional[str] = None

        for _ in range(_MAX_PAGES):
            path = f"/address/{address}/txs"
            if last_seen:
                path = f"{path}/chain/{last_seen}"
            page = self._get(path)
            if not isinstance(page, list) or not page:
                return collected, True
            collected.extend(page)
            last_seen = page[-1].get("txid")
            if len(page) < 25:
                return collected, True

        return collected, False

    @staticmethod
    def _net_effect(tx: dict, address: str) -> tuple[Decimal, bool, str]:
        """Net satoshis this transaction moved for *address*.

        Returns
        -------
        tuple
            The signed amount, whether the address also funded the inputs (a
            self-send or a spend with change), and a counterparty address.
        """
        received = Decimal("0")
        sent = Decimal("0")
        counterparty = ""
        funded_inputs = False

        for vin in tx.get("vin", []):
            prevout = vin.get("prevout") or {}
            if prevout.get("scriptpubkey_address") == address:
                sent += Decimal(str(prevout.get("value", 0)))
                funded_inputs = True
            elif not counterparty:
                counterparty = prevout.get("scriptpubkey_address", "") or ""

        for vout in tx.get("vout", []):
            if vout.get("scriptpubkey_address") == address:
                received += Decimal(str(vout.get("value", 0)))
            elif not counterparty:
                counterparty = vout.get("scriptpubkey_address", "") or ""

        return received - sent, funded_inputs, counterparty

    def fetch(self, address: str, with_history: bool = True) -> WalletSnapshot:
        """Read the balance, and the transaction history when asked.

        Parameters
        ----------
        address : str
            Bitcoin address in any standard encoding.
        with_history : bool, optional
            Whether to walk the transaction history as well.

        Returns
        -------
        WalletSnapshot
            Balance, transfers, and any caveat worth showing.

        Raises
        ------
        WalletProviderError
            When the indexer is unreachable or rejects the address.
        """
        balance = TokenBalance(
            contract_address="",
            symbol="BTC",
            name="Bitcoin",
            decimals=BITCOIN_DECIMALS,
            units=self._balance_sats(address) / SATS_PER_BTC,
            is_native=True,
            )

        snapshot = WalletSnapshot(balances=[balance])
        if not with_history:
            return snapshot

        transactions, complete = self._transactions(address)
        transfers: list[RawTransfer] = []

        for index, tx in enumerate(transactions):
            status = tx.get("status", {})
            if not status.get("confirmed"):
                continue
            block_time = status.get("block_time")
            if not block_time:
                continue

            net, _funded, counterparty = self._net_effect(tx, address)
            if net == 0:
                # A transaction that consolidated the address's own outputs:
                # nothing entered or left, only fees were paid.
                continue

            transfers.append(RawTransfer(
                tx_hash=str(tx.get("txid", "")),
                log_index=index,
                timestamp=datetime.fromtimestamp(int(block_time), tz=timezone.utc),
                direction=TransferDirection.IN if net > 0 else TransferDirection.OUT,
                contract_address="",
                symbol="BTC",
                decimals=BITCOIN_DECIMALS,
                units=abs(net) / SATS_PER_BTC,
                counterparty=counterparty,
                is_native=True,
                ))

        transfers.sort(key=lambda t: t.timestamp)
        snapshot.transfers = transfers
        snapshot.history_complete = complete
        if not complete:
            snapshot.notes.append(
                "Historique tronqué : cette adresse a plus de transactions que la "
                "synchronisation n'en récupère. Le prix de revient dérivé est incomplet."
                )
        return snapshot


def sats_to_btc(sats) -> Decimal:
    """Convert satoshis to bitcoin, for the tracker's existing BTC products."""
    return scale(sats, BITCOIN_DECIMALS)
