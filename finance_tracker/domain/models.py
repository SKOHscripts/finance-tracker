"""Modèles de domaine (SQLModel)."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Column, DateTime, Field, ForeignKey, Numeric, SQLModel

from .enums import ProductType, QuantityUnit, TransactionType


class Product(SQLModel, table=True):
    """Produit d'investissement."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    type: ProductType
    quantity_unit: QuantityUnit = QuantityUnit.NONE
    description: str = ""
    risk_level: str = ""  # "Très faible", "Faible", "Modéré", "Élevé"
    fees_description: str = ""
    tax_info: str = ""
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


class Transaction(SQLModel, table=True):
    """
    Represents a transaction record in the database.

    This model tracks financial or quantity-based movements associated with a product.
    It supports both cash transactions (EUR) and quantity-based transactions (e.g., shares, satoshis).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    date: datetime  # Date of the transaction
    type: TransactionType
    amount_eur: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=12, scale=2)),
        )  # Amount in EUR
    quantity: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=20, scale=8)),
        )  # Quantity (shares, sats, etc.)
    note: str = ""
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


class Valuation(SQLModel, table=True):
    """Snapshot de valeur à une date."""

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    date: datetime
    total_value_eur: Decimal = Field(
        sa_column=Column(Numeric(precision=12, scale=2))
        )
    unit_price_eur: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=12, scale=2)),
        )  # Prix unitaire (SCPI, BTC)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


class RateSchedule(SQLModel, table=True):
    """Calendrier de taux d'épargne."""

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    date_effective: datetime
    annual_rate: Decimal = Field(
        sa_column=Column(Numeric(precision=5, scale=4))
        )  # Ex: 0.0300 pour 3%
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )
