"""Interface repositories."""
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional

from finance_tracker.domain.enums import TransactionType
from finance_tracker.domain.models import Product, Transaction, Valuation


class IProductRepository(ABC):
    """Interface pour repository de produits."""

    @abstractmethod
    def create(self, product: Product) -> Product:
        """Créer un produit."""
        pass

    @abstractmethod
    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Récupérer par ID."""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Product]:
        """Récupérer par nom."""
        pass

    @abstractmethod
    def get_all(self) -> list[Product]:
        """Récupérer tous."""
        pass

    @abstractmethod
    def update(self, product: Product) -> Product:
        """Mettre à jour."""
        pass

    @abstractmethod
    def delete(self, product_id: int) -> bool:
        """Supprimer."""
        pass


class ITransactionRepository(ABC):
    """Interface pour repository de transactions."""

    @abstractmethod
    def create(self, transaction: Transaction) -> Transaction:
        """Créer une transaction."""
        pass

    @abstractmethod
    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Récupérer par ID."""
        pass

    @abstractmethod
    def get_by_product_id(self, product_id: int) -> list[Transaction]:
        """Récupérer par produit."""
        pass

    @abstractmethod
    def get_all(self) -> list[Transaction]:
        """Récupérer tous."""
        pass

    @abstractmethod
    def get_all_by_type(self, transaction_type: TransactionType) -> list[Transaction]:
        """Récupérer par type."""
        pass

    @abstractmethod
    def update(self, transaction: Transaction) -> Transaction:
        """Mettre à jour."""
        pass

    @abstractmethod
    def delete(self, transaction_id: int) -> bool:
        """Supprimer."""
        pass


class IValuationRepository(ABC):
    """Interface pour repository de valorisations."""

    @abstractmethod
    def create(self, valuation: Valuation) -> Valuation:
        """Créer une valorisation."""
        pass

    @abstractmethod
    def get_by_id(self, valuation_id: int) -> Optional[Valuation]:
        """Récupérer par ID."""
        pass

    @abstractmethod
    def get_latest_by_product_id(self, product_id: int) -> Optional[Valuation]:
        """Récupérer la plus récente."""
        pass

    @abstractmethod
    def get_by_product_id(self, product_id: int) -> list[Valuation]:
        """Récupérer par produit."""
        pass

    @abstractmethod
    def get_all(self) -> list[Valuation]:
        """Récupérer tous."""
        pass

    @abstractmethod
    def update(self, valuation: Valuation) -> Valuation:
        """Mettre à jour."""
        pass

    @abstractmethod
    def delete(self, valuation_id: int) -> bool:
        """Supprimer."""
        pass
