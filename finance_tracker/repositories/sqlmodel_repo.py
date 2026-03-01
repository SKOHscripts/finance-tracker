"""Repository SQLModel - implémentation concrète."""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import desc, select
from sqlmodel import Session, SQLModel

from finance_tracker.config import DATABASE_URL
from finance_tracker.domain.enums import ProductType, TransactionType
from finance_tracker.domain.models import Product, RateSchedule, Transaction, Valuation

from .base import IProductRepository, ITransactionRepository, IValuationRepository


class SQLModelProductRepository(IProductRepository):
    """SQLModel repository implementation for Product entities.

    Provides CRUD operations for products using SQLModel and SQLAlchemy sessions.
    """

    def __init__(self, session: Session) -> None:
        """Initialize the ProductRepository.

        Parameters
        ----------
        session : Session
            Database session for executing queries.
        """
        self.session = session

    def create(self, product: Product) -> Product:
        """Create a new product in the database.

        Parameters
        ----------
        product : Product
            Product instance to be created.

        Returns
        -------
        Product
            The created product with updated database fields.
        """
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)

        return product

    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Retrieve a product by its ID.

        Parameters
        ----------
        product_id : int
            Unique identifier of the product.

        Returns
        -------
        Optional[Product]
            The product if found, None otherwise.
        """

        return self.session.get(Product, product_id)

    def get_by_name(self, name: str) -> Optional[Product]:
        """Retrieve a product by its name.

        Parameters
        ----------
        name : str
            Name of the product to search for.

        Returns
        -------
        Optional[Product]
            The product if found, None otherwise.
        """
        stmt = select(Product).where(Product.name == name)

        return self.session.exec(stmt).scalars().first()

    def get_all(self) -> List[Product]:
        """Retrieve all products from the database.

        Returns
        -------
        List[Product]
            List of all products.
        """
        stmt = select(Product)

        return list(self.session.exec(stmt).scalars())

    def update(self, product: Product) -> Product:
        """Update an existing product in the database.

        Parameters
        ----------
        product : Product
            Product instance with updated fields.

        Returns
        -------
        Product
            The updated product with refreshed database fields.
        """
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)

        return product

    def delete(self, product_id: int) -> bool:
        """Delete a product from the database.

        Parameters
        ----------
        product_id : int
            Unique identifier of the product to delete.

        Returns
        -------
        bool
            True if the product was deleted, False otherwise.
        """
        product = self.session.get(Product, product_id)

        if product:
            self.session.delete(product)
            self.session.commit()

            return True

        return False


class SQLModelTransactionRepository(ITransactionRepository):
    """SQLModel-based repository for Transaction CRUD operations.

    Provides methods for creating, reading, updating, and deleting Transaction entities.

    Parameters
    ----------
    session : Session
        Database session for executing queries.
    """

    def __init__(self, session: Session) -> None:
        """Initialize the TransactionRepository with a database session.

        The session is used for all database operations.

        Parameters
        ----------
        session : Session
            SQLAlchemy session for database operations.
        """
        self.session = session

    def create(self, transaction: Transaction) -> Transaction:
        """Create a new transaction in the database.

        The transaction is added, committed, and refreshed to get the generated ID.

        Parameters
        ----------
        transaction : Transaction
            The transaction object to create.

        Returns
        -------
        Transaction
            The created transaction with generated ID.
        """
        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)

        return transaction

    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Retrieve a transaction by its ID.

        Returns None if no transaction exists with the given ID.

        Parameters
        ----------
        transaction_id : int
            The ID of the transaction to retrieve.

        Returns
        -------
        Optional[Transaction]
            The transaction if found, None otherwise.
        """

        return self.session.get(Transaction, transaction_id)

    def get_by_product_id(self, product_id: int) -> List[Transaction]:
        """Retrieve all transactions for a specific product.

        Results are ordered by date in ascending order.

        Parameters
        ----------
        product_id : int
            The ID of the product to filter transactions by.

        Returns
        -------
        List[Transaction]
            List of transactions for the specified product.
        """
        stmt = (
            select(Transaction)
            .where(Transaction.product_id == product_id)
            .order_by(Transaction.date)
            )

        return list(self.session.exec(stmt).scalars())

    def get_all(self) -> List[Transaction]:
        """Retrieve all transactions from the database.

        Results are ordered by date in ascending order.

        Returns
        -------
        List[Transaction]
            List of all transactions.
        """
        stmt = select(Transaction).order_by(Transaction.date)

        return list(self.session.exec(stmt).scalars())

    def get_all_by_type(self, transaction_type: TransactionType) -> List[Transaction]:
        """Retrieve all transactions of a specific type.

        Parameters
        ----------
        transaction_type : TransactionType
            The type of transactions to retrieve.

        Returns
        -------
        List[Transaction]
            List of transactions matching the specified type.
        """
        stmt = select(Transaction).where(Transaction.type == transaction_type)

        return list(self.session.exec(stmt).scalars())

    def update(self, transaction: Transaction) -> Transaction:
        """Update an existing transaction in the database.

        The transaction is added, committed, and refreshed.

        Parameters
        ----------
        transaction : Transaction
            The transaction object with updated values.

        Returns
        -------
        Transaction
            The updated transaction.
        """
        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)

        return transaction

    def delete(self, transaction_id: int) -> bool:
        """Delete a transaction by its ID.

        Returns True if the transaction was deleted, False otherwise.

        Parameters
        ----------
        transaction_id : int
            The ID of the transaction to delete.

        Returns
        -------
        bool
            True if the transaction was deleted, False if not found.
        """
        transaction = self.session.get(Transaction, transaction_id)

        if transaction:
            self.session.delete(transaction)
            self.session.commit()

            return True

        return False


class SQLModelValuationRepository(IValuationRepository):
    """SQLModel repository for valuations.

    Implements the IValuationRepository interface using SQLModel for database
    operations.
    """

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session.

        Parameters
        ----------
        session : Session
            SQLModel database session.
        """
        self.session = session

    def create(self, valuation: Valuation) -> Valuation:
        """Create a new valuation record.

        Parameters
        ----------
        valuation : Valuation
            The valuation object to create.

        Returns
        -------
        Valuation
            The created valuation with committed data.
        """
        self.session.add(valuation)
        self.session.commit()
        self.session.refresh(valuation)

        return valuation

    def get_by_id(self, valuation_id: int) -> Optional[Valuation]:
        """Retrieve a valuation by its ID.

        Parameters
        ----------
        valuation_id : int
            The unique identifier of the valuation.

        Returns
        -------
        Optional[Valuation]
            The valuation if found, None otherwise.
        """

        return self.session.get(Valuation, valuation_id)

    def get_latest_by_product_id(self, product_id: int) -> Optional[Valuation]:
        """Retrieve the most recent valuation for a product.

        Parameters
        ----------
        product_id : int
            The unique identifier of the product.

        Returns
        -------
        Optional[Valuation]
            The latest valuation for the product, or None if not found.
        """
        stmt = (
            select(Valuation)
            .where(Valuation.product_id == product_id)
            .order_by(desc(Valuation.date))
            .limit(1)
            )

        return self.session.exec(stmt).scalars().first()

    def get_by_product_id(self, product_id: int) -> List[Valuation]:
        """Retrieve all valuations for a product.

        Parameters
        ----------
        product_id : int
            The unique identifier of the product.

        Returns
        -------
        List[Valuation]
            List of all valuations for the product, ordered by date.
        """
        stmt = (
            select(Valuation)
            .where(Valuation.product_id == product_id)
            .order_by(Valuation.date)
            )

        return list(self.session.exec(stmt).scalars())

    def get_all(self) -> List[Valuation]:
        """Retrieve all valuations.

        Returns
        -------
        List[Valuation]
            List of all valuations, ordered by date.
        """
        stmt = select(Valuation).order_by(Valuation.date)

        return list(self.session.exec(stmt).scalars())

    def update(self, valuation: Valuation) -> Valuation:
        """Update an existing valuation.

        Parameters
        ----------
        valuation : Valuation
            The valuation object with updated data.

        Returns
        -------
        Valuation
            The updated valuation with committed changes.
        """
        self.session.add(valuation)
        self.session.commit()
        self.session.refresh(valuation)

        return valuation

    def delete(self, valuation_id: int) -> bool:
        """Delete a valuation by its ID.

        Parameters
        ----------
        valuation_id : int
            The unique identifier of the valuation to delete.

        Returns
        -------
        bool
            True if the valuation was deleted, False if not found.
        """
        valuation = self.session.get(Valuation, valuation_id)

        if valuation:
            self.session.delete(valuation)
            self.session.commit()

            return True

        return False


class SQLModelRateScheduleRepository:
    """SQLModel repository for managing RateSchedule entities.

    Provides database operations for creating and retrieving rate schedules
    associated with products.
    """

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session.

        Parameters
        ----------
        session : Session
            SQLModel database session for executing queries.
        """
        self.session = session

    def create(self, rate_schedule: RateSchedule) -> RateSchedule:
        """Create a new rate schedule in the database.

        Parameters
        ----------
        rate_schedule : RateSchedule
            The rate schedule entity to create.

        Returns
        -------
        RateSchedule
            The created rate schedule with updated database fields.
        """
        self.session.add(rate_schedule)
        self.session.commit()
        self.session.refresh(rate_schedule)

        return rate_schedule

    def get_by_product_id(self, product_id: int) -> List[RateSchedule]:
        """Retrieve all rate schedules for a specific product.

        Parameters
        ----------
        product_id : int
            The identifier of the product.

        Returns
        -------
        List[RateSchedule]
            List of rate schedules ordered by effective date.
        """
        stmt = (
            select(RateSchedule)
            .where(RateSchedule.product_id == product_id)
            .order_by(RateSchedule.date_effective)
            )

        return list(self.session.exec(stmt).scalars())

    def get_rate_at_date(self, product_id: int, at_date: datetime):
        """Retrieve the applicable rate for a product at a specific date.

        Parameters
        ----------
        product_id : int
            The identifier of the product.
        at_date : datetime
            The date for which to retrieve the applicable rate.

        Returns
        -------
        Optional[float]
            The annual rate applicable at the given date, or None if no rate exists.
        """
        stmt = (
            select(RateSchedule)
            .where(
                RateSchedule.product_id == product_id,
                RateSchedule.date_effective <= at_date,
                )
            .order_by(desc(RateSchedule.date_effective))
            .limit(1)
            )
        result = self.session.exec(stmt).scalars().first()

        return result.annual_rate if result else None


def init_db(engine):
    """Initialize database by creating all missing tables.

    This function uses SQLModel metadata to create tables in the provided
    database engine.

    Parameters
    ----------
    engine : sqlalchemy.engine.Engine
        Database engine used to create the tables.

    Returns
    -------
    None

    Raises
    ------
    Exception
        Any exception raised by SQLModel.metadata.create_all() during table
        creation.
    """
    SQLModel.metadata.create_all(engine)
