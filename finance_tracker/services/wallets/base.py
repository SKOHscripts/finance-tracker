"""What every chain connector must provide.

One shared vocabulary — a balance, a transfer — so the sync service and the
cost-basis reconstruction never need to know which chain a figure came from.
Each connector reports its own limits through :attr:`WalletProvider.supports_history`
rather than silently returning an empty history that would read as "this
address has never moved".
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from finance_tracker.domain.enums import Chain, TransferDirection


class WalletProviderError(RuntimeError):
    """Raised when an indexer cannot be reached or rejects a request."""


class UnsupportedChainError(WalletProviderError):
    """Raised when no connector exists for the requested chain."""


@dataclass
class TokenBalance:
    """One asset held at an address.

    Parameters
    ----------
    contract_address : str
        Token contract, empty string for the chain's native coin. Empty rather
        than None because it takes part in a uniqueness constraint, and SQLite
        treats NULLs as distinct.
    symbol : str
        Ticker as reported by the chain, upper case.
    name : str
        Token name as reported by the chain.
    decimals : int
        Decimals used to scale the raw on-chain amount.
    units : Decimal
        Balance in whole units, already scaled.
    is_native : bool
        Whether this is the chain's own coin rather than a token.
    """

    contract_address: str
    symbol: str
    name: str
    decimals: int
    units: Decimal
    is_native: bool = False


@dataclass
class RawTransfer:
    """One movement of one asset in or out of a watched address.

    Parameters
    ----------
    tx_hash : str
        Transaction hash.
    log_index : int
        Position within the transaction, so several movements in one
        transaction stay distinct.
    timestamp : datetime
        Block time, in UTC.
    direction : TransferDirection
        Whether units entered or left the address.
    contract_address : str
        Token contract, empty for the native coin.
    symbol : str
        Ticker of the asset moved.
    decimals : int
        Decimals of the asset moved.
    units : Decimal
        Amount moved, in whole units, always positive.
    counterparty : str
        The other address involved.
    is_native : bool
        Whether the native coin moved.
    """

    tx_hash: str
    log_index: int
    timestamp: datetime
    direction: TransferDirection
    contract_address: str
    symbol: str
    decimals: int
    units: Decimal
    counterparty: str = ""
    is_native: bool = False


@dataclass
class WalletSnapshot:
    """Everything one connector could read about one address.

    Parameters
    ----------
    balances : list[TokenBalance]
        Assets currently held.
    transfers : list[RawTransfer]
        Movements, oldest first. Empty when the connector cannot read history.
    history_complete : bool
        False when the history was truncated or is not available at all. A
        cost basis built on an incomplete history is reported as low
        confidence rather than presented as a fact.
    notes : list[str]
        Human-readable caveats to surface next to the figures.
    """

    balances: list[TokenBalance] = field(default_factory=list)
    transfers: list[RawTransfer] = field(default_factory=list)
    history_complete: bool = True
    notes: list[str] = field(default_factory=list)


class WalletProvider(Protocol):
    """A read-only connector for one family of chains."""

    chain: Chain

    #: Whether this connector can return transfer history. False means a cost
    #: basis cannot be derived and must be entered by hand.
    supports_history: bool

    def fetch(self, address: str, with_history: bool = True) -> WalletSnapshot:
        """Read balances, and history when asked and available.

        Parameters
        ----------
        address : str
            Public address to read.
        with_history : bool, optional
            Whether to also fetch transfers. Ignored by connectors that cannot.

        Returns
        -------
        WalletSnapshot
            What could be read.

        Raises
        ------
        WalletProviderError
            When the indexer is unreachable or rejects the request.
        """
        ...


def scale(raw: str | int, decimals: int) -> Decimal:
    """Convert a raw on-chain amount to whole units.

    Parameters
    ----------
    raw : str or int
        Amount in the asset's smallest unit.
    decimals : int
        Number of decimals the asset uses.

    Returns
    -------
    Decimal
        The scaled amount, or zero when *raw* cannot be read as an integer.
        Decimal throughout: a token with 18 decimals loses precision as a
        float, and a balance that is quietly wrong is worse than one missing.
    """
    try:
        value = Decimal(str(raw))
    except (ValueError, ArithmeticError):
        return Decimal("0")
    if decimals <= 0:
        return value
    return value / (Decimal(10) ** decimals)


def optional_int(value, default: int = 18) -> int:
    """Read an integer that an indexer may return as a string or omit."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
