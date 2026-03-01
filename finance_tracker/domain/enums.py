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


class QuantityUnit(str, Enum):
    """Quantity units for products."""

    NONE = "NONE"  # No quantity, just eur
    SCPI_SHARES = "SCPI_SHARES"  # Parts SCPI
    BTC_SATS = "BTC_SATS"  # Satoshis Bitcoin


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
