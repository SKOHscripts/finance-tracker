"""Domain models (SQLModel)."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Column, DateTime, Field, ForeignKey, Numeric, SQLModel

from .enums import ProductType, QuantityUnit, TransactionType


class Product(SQLModel, table=True):
    """Investment product model for portfolio tracking.

    Stores product details such as name, type, risk level, fees, and tax information.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    name : str
        Unique product name, indexed for fast lookup.
    type : ProductType
        Type of investment product (stock, crypto, SCPI, etc.).
    quantity_unit : QuantityUnit
        Unit for quantity (NONE for non-quantity products).
    description : str
        Optional product description.
    risk_level : str
        User-friendly risk level display (e.g., "Très faible", "Faible").
    fees_description : str
        Description of applicable fees.
    tax_info : str
        Tax-related information.
    created_at : datetime
        Timestamp of product creation, timezone-aware.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)  # Unique name prevents duplicates
    type: ProductType
    quantity_unit: QuantityUnit = QuantityUnit.NONE  # Default to NONE for non-quantity products
    description: str = ""
    risk_level: str = ""  # User-friendly display: "Très faible", "Faible", etc.
    fees_description: str = ""
    tax_info: str = ""
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),  # Store timezone-aware timestamps
        )


class Transaction(SQLModel, table=True):
    """
    Transaction model for database records.

    Tracks financial or quantity-based movements associated with products.

    Parameters
    ----------
    product_id : int
        Foreign key to the associated product.
    date : datetime
        Date and time of the transaction.
    type : TransactionType
        Type of transaction (e.g., buy, sell, deposit, withdrawal).
    amount_eur : Decimal, optional
        Transaction amount in EUR (max 10^10, 12 digits total, 2 decimal places).
    quantity : Decimal, optional
        Transaction quantity for asset-based transactions (up to 20 digits, 8 decimal places).
    note : str, optional
        Optional note or description for the transaction (default: empty string).
    created_at : datetime, optional
        Timestamp when the record was created (default: current UTC time).

    Returns
    -------
    Transaction
        SQLModel instance representing a transaction record in the database.

    Raises
    ------
    None
        This model does not raise exceptions; database constraints handle validation.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    date: datetime  # Date of the transaction
    type: TransactionType
    # EUR amount: max 10^10 (12 digits total, 2 after decimal) - covers billions
    amount_eur: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=12, scale=2)),
        )
    # Quantity: high precision for crypto (8 decimals) and large amounts (20 digits total)
    quantity: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=20, scale=8)),
        )
    note: str = ""
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


class Valuation(SQLModel, table=True):
    """Value snapshot at a specific date for portfolio tracking.

    Represents a historical record of portfolio or product valuation for
    financial tracking and analysis purposes.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    product_id : int
        Foreign key referencing the product being valued.
    date : datetime
        Date of the valuation snapshot.
    total_value_eur : Decimal
        Total portfolio value in EUR (precision: 12, scale: 2).
    unit_price_eur : Optional[Decimal]
        Unit price for per-unit priced products (e.g., SCPI shares, BTC).
        Null if not applicable.
    created_at : datetime
        Timestamp of record creation, defaults to UTC now.

    Returns
    -------
    Valuation
        A database model instance representing a valuation snapshot.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    date: datetime
    # Total portfolio value in EUR: sufficient for large portfolios
    total_value_eur: Decimal = Field(
        sa_column=Column(Numeric(precision=12, scale=2))
        )
    # Unit price for products priced per unit (SCPI shares, BTC, etc.)
    unit_price_eur: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=12, scale=2)),
        )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


class RateSchedule(SQLModel, table=True):
    """Interest rate schedule for savings products such as term deposits or bonds.

    Stores effective dates and annual interest rates with four decimal precision.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    product_id : int
        Foreign key referencing the associated product.
    date_effective : datetime
        Date when the rate becomes effective.
    annual_rate : Decimal
        Annual interest rate with four decimal places (e.g., 0.0300 = 3%).
    created_at : datetime
        Timestamp of record creation, defaults to current UTC time.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    date_effective: datetime
    # Annual rate with 4 decimal places (e.g., 0.0300 = 3%)
    annual_rate: Decimal = Field(
        sa_column=Column(Numeric(precision=5, scale=4))
        )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )
