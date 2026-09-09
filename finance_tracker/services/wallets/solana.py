"""Solana, through a public JSON-RPC endpoint.

Balances only, and that is a limit worth stating rather than working around.
``getTokenAccountsByOwner`` returns every SPL balance in one call with no key
and no account. Reconstructing history is a different matter: it means walking
signatures and fetching each transaction, then decoding instructions that vary
by program — hundreds of calls against a public endpoint that rate-limits, to
produce a cost basis less reliable than one the user can type in a few seconds.

So :attr:`SolanaProvider.supports_history` is False, the sync says so, and the
cost basis for a Solana position is entered by hand.
"""
from decimal import Decimal
from typing import Optional

import requests

from finance_tracker.config import SOLANA_RPC_URL, WALLET_HTTP_TIMEOUT
from finance_tracker.domain.enums import Chain

from .base import TokenBalance, WalletProviderError, WalletSnapshot, optional_int

LAMPORTS_PER_SOL = Decimal("1000000000")

# The SPL token programs. A wallet's balances can sit under either, so both are
# queried; Token-2022 is the newer one and is far from universal yet.
_TOKEN_PROGRAMS = (
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
    )


class SolanaProvider:
    """Read SPL and native balances for one Solana address.

    Parameters
    ----------
    base_url : str, optional
        JSON-RPC endpoint. Override it to use a private node — public
        endpoints rate-limit aggressively.
    timeout : int, optional
        Per-request timeout in seconds.
    session : requests.Session, optional
        Session to reuse.
    """

    chain = Chain.SOLANA
    #: History is not read. See the module docstring for why.
    supports_history = False

    def __init__(
        self,
        base_url: str = SOLANA_RPC_URL,
        timeout: int = WALLET_HTTP_TIMEOUT,
        session: Optional[requests.Session] = None,
        ) -> None:
        self.base_url = (base_url or SOLANA_RPC_URL).rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()
        self._request_id = 0

    def _rpc(self, method: str, params: list):
        """Issue one JSON-RPC call and return its ``result``.

        Raises
        ------
        WalletProviderError
            On a transport failure or an RPC-level error.
        """
        self._request_id += 1
        body = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
            }
        try:
            response = self._session.post(self.base_url, json=body, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.RequestException as exc:
            raise WalletProviderError(f"Nœud Solana injoignable : {exc}") from exc
        except ValueError as exc:
            raise WalletProviderError(f"Réponse illisible du nœud Solana : {exc}") from exc

        if "error" in payload:
            message = payload["error"].get("message", "erreur inconnue")
            raise WalletProviderError(f"Le nœud Solana a refusé la requête : {message}")
        return payload.get("result")

    def _native_balance(self, address: str) -> Decimal:
        """Native SOL balance, in whole SOL."""
        result = self._rpc("getBalance", [address])
        lamports = (result or {}).get("value", 0)
        return Decimal(str(lamports)) / LAMPORTS_PER_SOL

    def _token_balances(self, address: str) -> list[TokenBalance]:
        """Every non-empty SPL balance held by *address*."""
        balances: list[TokenBalance] = []

        for program in _TOKEN_PROGRAMS:
            result = self._rpc("getTokenAccountsByOwner", [
                address,
                {"programId": program},
                {"encoding": "jsonParsed"},
                ])
            for account in (result or {}).get("value", []):
                info = (
                    account.get("account", {})
                    .get("data", {})
                    .get("parsed", {})
                    .get("info", {})
                    )
                amount = info.get("tokenAmount", {})
                units = Decimal(str(amount.get("uiAmountString") or amount.get("uiAmount") or 0))
                if units <= 0:
                    continue
                mint = str(info.get("mint", ""))
                balances.append(TokenBalance(
                    contract_address=mint,
                    # The RPC does not carry a ticker; the mint is resolved to
                    # a symbol later, when the token is matched to a listing.
                    symbol="",
                    name=mint,
                    decimals=optional_int(amount.get("decimals"), 9),
                    units=units,
                    ))

        return balances

    def fetch(  # pylint: disable=unused-argument  # protocol signature
        self, address: str, with_history: bool = True
        ) -> WalletSnapshot:
        """Read native and SPL balances.

        Parameters
        ----------
        address : str
            Solana address, base58.
        with_history : bool, optional
            Accepted and ignored: this connector reads no history.

        Returns
        -------
        WalletSnapshot
            Balances, with ``history_complete`` False and a note saying why.

        Raises
        ------
        WalletProviderError
            When the node is unreachable or rejects the request.
        """
        balances: list[TokenBalance] = []

        native = self._native_balance(address)
        if native > 0:
            balances.append(TokenBalance(
                contract_address="",
                symbol="SOL",
                name="Solana",
                decimals=9,
                units=native,
                is_native=True,
                ))

        balances.extend(self._token_balances(address))

        return WalletSnapshot(
            balances=balances,
            transfers=[],
            # Not "no movements": no history was read at all. The distinction
            # is what stops a cost basis from being derived as zero.
            history_complete=False,
            notes=[
                "Solana : soldes seulement. L'historique n'est pas reconstitué, donc le "
                "prix de revient de ces lignes est à saisir à la main."
                ],
            )
