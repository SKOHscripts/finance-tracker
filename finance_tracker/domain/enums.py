"""Énumérations domaine."""
from enum import Enum


class ProductType(str, Enum):
    """Type de produit d'investissement."""

    CASH = "CASH"
    SCPI = "SCPI"
    BITCOIN = "BITCOIN"
    SAVINGS = "SAVINGS"
    INSURANCE = "INSURANCE"
    PER = "PER"
    FCPI = "FCPI"


class QuantityUnit(str, Enum):
    """Unité de quantité pour les produits."""

    NONE = "NONE"  # Pas de quantité, juste EUR
    SCPI_SHARES = "SCPI_SHARES"  # Parts SCPI
    BTC_SATS = "BTC_SATS"  # Satoshis Bitcoin


class TransactionType(str, Enum):
    """Type de transaction."""

    DEPOSIT = "DEPOSIT"  # Dépôt argent
    WITHDRAW = "WITHDRAW"  # Retrait argent
    FEE = "FEE"  # Frais
    DISTRIBUTION = "DISTRIBUTION"  # Distribution (dividende, intérêt)
    BUY = "BUY"  # Achat produit
    SELL = "SELL"  # Vente produit
    INTEREST = "INTEREST"  # Intérêt calculé (épargne)
