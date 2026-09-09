"""Domain enumerations."""
from enum import Enum


class ProductType(str, Enum):
    """Enumeration of supported investment product types.

    This enum extends str to enable seamless string comparisons and JSON serialization.
    """

    CASH = "CASH"
    SCPI = "SCPI"
    BITCOIN = "BITCOIN"
    SAVINGS = "SAVINGS"
    INSURANCE = "INSURANCE"
    PER = "PER"
    FCPI = "FCPI"
    CRYPTO = "CRYPTO"  # Any crypto-asset other than Bitcoin, arbitrated by the signal engine.


class QuantityUnit(str, Enum):
    """Quantity units for products."""

    NONE = "NONE"  # No quantity, just eur
    SCPI_SHARES = "SCPI_SHARES"  # Parts SCPI
    BTC_SATS = "BTC_SATS"  # Satoshis Bitcoin
    CRYPTO_UNITS = "CRYPTO_UNITS"  # Native units of a crypto-asset (XMR, ETH, ...)


class TransactionType(str, Enum):
    """Transaction types."""

    # Define transaction types for clarity and consistency.
    DEPOSIT = "DEPOSIT"  # Money added to the account.
    WITHDRAW = "WITHDRAW"  # Money removed from the account.
    FEE = "FEE"  # Transaction costs deducted.
    DISTRIBUTION = "DISTRIBUTION"  # Passive income received (dividends/interest).
    BUY = "BUY"  # Purchase of an asset.
    SELL = "SELL"  # Sale of an asset.
    INTEREST = "INTEREST"  # Calculated interest earned on savings.


class ValuationSource(str, Enum):
    """Origin of a valuation record.

    Distinguishes values typed by the user from values fetched automatically,
    so a manual correction is never silently overwritten by a price refresh.
    """

    MANUAL = "MANUAL"  # Entered by the user.
    COINGECKO = "COINGECKO"  # Fetched from the CoinGecko public API.


class SignalVerdict(str, Enum):
    """Verdict produced by the crypto rotation engine for a single position.

    Ordered by how engaging the action is: a stop-loss exit protects capital
    and outranks everything, taking profit outranks chasing another asset, and
    holding is always the fallback.
    """

    CONSERVER = "CONSERVER"  # Do nothing this week.
    TEMPORISER = "TEMPORISER"  # One-way exit to a stablecoin refuge.
    ROTATION = "ROTATION"  # Swap the position into the ranked candidate.
    ALLEGER = "ALLEGER"  # Partial sale to recover the invested capital.
    SORTIE_STOP = "SORTIE_STOP"  # Full exit triggered by the trailing stop.


class MarketRegime(str, Enum):
    """Observed state of the market at scan time. Describes, never predicts."""

    BULL = "BULL"  # Both regime measures favourable.
    MIXTE = "MIXTE"  # Exactly one of the two favourable.
    BEAR = "BEAR"  # Neither favourable: rotations are suspended.
    INCONNU = "INCONNU"  # Not enough history to decide.


class Chain(str, Enum):
    """Blockchains the wallet importer can read.

    EVM chains share one connector; Bitcoin and Solana each need their own,
    because their address model and their history endpoints differ.
    """

    BITCOIN = "BITCOIN"
    ETHEREUM = "ETHEREUM"
    BASE = "BASE"
    ARBITRUM = "ARBITRUM"
    OPTIMISM = "OPTIMISM"
    POLYGON = "POLYGON"
    BSC = "BSC"
    SOLANA = "SOLANA"


# EVM chain ids, used by the multichain block-explorer API. Bitcoin and Solana
# are absent on purpose: they are not EVM and take a different connector.
EVM_CHAIN_IDS: dict[Chain, int] = {
    Chain.ETHEREUM: 1,
    Chain.OPTIMISM: 10,
    Chain.BSC: 56,
    Chain.POLYGON: 137,
    Chain.BASE: 8453,
    Chain.ARBITRUM: 42161,
}


class TransferDirection(str, Enum):
    """Whether a transfer added units to the wallet or removed them."""

    IN = "IN"
    OUT = "OUT"


class TransferKind(str, Enum):
    """What a transfer means for cost basis.

    A chain shows movements, not intent. This classification is the tool's
    reading of a movement, and it is what makes an estimated cost basis
    auditable: every unit is attributed to one of these, or to nothing.
    """

    ACQUISITION = "ACQUISITION"  # Units entering from outside: priced, raises the basis.
    DISPOSAL = "DISPOSAL"  # Units leaving to outside: lowers the basis proportionally.
    INTERNAL = "INTERNAL"  # Between the user's own wallets: no effect on basis.
    FEE = "FEE"  # Chain fee paid: a cost, not an acquisition.
    UNKNOWN = "UNKNOWN"  # Could not be classified; left out and counted as uncovered.


class CostBasisConfidence(str, Enum):
    """How much of a position's units the derived cost basis actually explains.

    An on-chain basis is an estimate. This says how much of one, so the UI can
    show it as such instead of passing it off as a known purchase price.
    """

    HIGH = "HIGH"  # Nearly every unit traced to a priced acquisition.
    MEDIUM = "MEDIUM"  # Most units traced; some gaps.
    LOW = "LOW"  # Large share of units with no priced origin.
    NONE = "NONE"  # Nothing could be derived.
