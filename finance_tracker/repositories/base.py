"""Interface repositories."""
from abc import ABC, abstractmethod
from typing import Optional

from finance_tracker.domain.enums import TransactionType
from finance_tracker.domain.models import Product, Transaction, Valuation


class IProductRepository(ABC):
    """Interface defining the contract for product repository operations."""

    @abstractmethod
    def create(self, product: Product) -> Product:
        """Create a new product in the repository.

        Parameters
        ----------
        product : Product
            Product instance to be created.

        Returns
        -------
        Product
            Created product with generated identifier.

        Raises
        ------
        DuplicateProductError
            If a product with the same name already exists.
        """
        pass

    @abstractmethod
    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Retrieve a product by its unique identifier.

        Parameters
        ----------
        product_id : int
            Unique identifier of the product.

        Returns
        -------
        Product or None
            Product instance if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Product]:
        """Retrieve a product by its name.

        Parameters
        ----------
        name : str
            Name of the product to search for.

        Returns
        -------
        Product or None
            Product instance if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_all(self) -> list[Product]:
        """Retrieve all products from the repository.

        Returns
        -------
        list[Product]
            List of all product instances.
        """
        pass

    @abstractmethod
    def update(self, product: Product) -> Product:
        """Update an existing product in the repository.

        Parameters
        ----------
        product : Product
            Product instance with updated data.

        Returns
        -------
        Product
            Updated product instance.

        Raises
        ------
        ProductNotFoundError
            If the product does not exist in the repository.
        """
        pass

    @abstractmethod
    def delete(self, product_id: int) -> bool:
        """Delete a product from the repository.

        Parameters
        ----------
        product_id : int
            Unique identifier of the product to delete.

        Returns
        -------
        bool
            True if deletion was successful, False otherwise.
        """
        pass


class ITransactionRepository(ABC):
    """Interface for transaction repository."""

    @abstractmethod
    def create(self, transaction: Transaction) -> Transaction:
        """
        Create a new transaction.

        Parameters
        ----------
        transaction : Transaction
            The transaction to create.

        Returns
        -------
        Transaction
            The created transaction.
        """
        pass

    @abstractmethod
    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """
        Retrieve a transaction by its ID.

        Parameters
        ----------
        transaction_id : int
            The unique identifier of the transaction.

        Returns
        -------
        Optional[Transaction]
            The transaction if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_by_product_id(self, product_id: int) -> list[Transaction]:
        """
        Retrieve all transactions for a specific product.

        Parameters
        ----------
        product_id : int
            The unique identifier of the product.

        Returns
        -------
        list[Transaction]
            List of transactions associated with the product.
        """
        pass

    @abstractmethod
    def get_all(self) -> list[Transaction]:
        """
        Retrieve all transactions.

        Returns
        -------
        list[Transaction]
            List of all transactions in the repository.
        """
        pass

    @abstractmethod
    def get_all_by_type(self, transaction_type: TransactionType) -> list[Transaction]:
        """
        Retrieve all transactions of a specific type.

        Parameters
        ----------
        transaction_type : TransactionType
            The type of transaction to filter by.

        Returns
        -------
        list[Transaction]
            List of transactions matching the specified type.
        """
        pass

    @abstractmethod
    def update(self, transaction: Transaction) -> Transaction:
        """
        Update an existing transaction.

        Parameters
        ----------
        transaction : Transaction
            The transaction with updated data.

        Returns
        -------
        Transaction
            The updated transaction.
        """
        pass

    @abstractmethod
    def delete(self, transaction_id: int) -> bool:
        """
        Delete a transaction by its ID.

        Parameters
        ----------
        transaction_id : int
            The unique identifier of the transaction to delete.

        Returns
        -------
        bool
            True if the transaction was deleted, False otherwise.
        """
        pass


class IValuationRepository(ABC):
    """Abstract repository interface for Valuation domain objects.

    Provides CRUD operations for managing product valuations in the system.
    """

    @abstractmethod
    def create(self, valuation: Valuation) -> Valuation:
        """Create a new valuation record in the repository.

        Parameters
        ----------
        valuation : Valuation
            The valuation entity to persist.

        Returns
        -------
        Valuation
            The created valuation with assigned identifier.

        Raises
        ------
        ValidationError
            If the valuation data is invalid.
        """
        pass

    @abstractmethod
    def get_by_id(self, valuation_id: int) -> Optional[Valuation]:
        """Retrieve a valuation by its unique identifier.

        Parameters
        ----------
        valuation_id : int
            The unique identifier of the valuation.

        Returns
        -------
        Optional[Valuation]
            The valuation if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_latest_by_product_id(self, product_id: int) -> Optional[Valuation]:
        """Retrieve the most recent valuation for a given product.

        Parameters
        ----------
        product_id : int
            The unique identifier of the product.

        Returns
        -------
        Optional[Valuation]
            The latest valuation for the product, None if none exists.
        """
        pass

    @abstractmethod
    def get_by_product_id(self, product_id: int) -> list[Valuation]:
        """Retrieve all valuations associated with a specific product.

        Parameters
        ----------
        product_id : int
            The unique identifier of the product.

        Returns
        -------
        list[Valuation]
            List of all valuations for the product, empty list if none found.
        """
        pass

    @abstractmethod
    def get_all(self) -> list[Valuation]:
        """Retrieve all valuation records from the repository.

        Returns
        -------
        list[Valuation]
            Complete list of all stored valuations.
        """
        pass

    @abstractmethod
    def update(self, valuation: Valuation) -> Valuation:
        """Update an existing valuation record.

        Parameters
        ----------
        valuation : Valuation
            The valuation entity with updated data.

        Returns
        -------
        Valuation
            The updated valuation.

        Raises
        ------
        ValidationError
            If the updated data is invalid.
        """
        pass

    @abstractmethod
    def delete(self, valuation_id: int) -> bool:
        """Delete a valuation from the repository.

        Parameters
        ----------
        valuation_id : int
            The unique identifier of the valuation to remove.

        Returns
        -------
        bool
            True if deletion succeeded, False if valuation not found.
        """
        pass
