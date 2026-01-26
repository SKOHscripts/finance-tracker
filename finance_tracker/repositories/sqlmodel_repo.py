"""Repository SQLModel - implémentation concrète."""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import desc, select
from sqlmodel import Session, SQLModel, create_engine

from finance_tracker.config import DATABASE_URL
from finance_tracker.domain.enums import ProductType, TransactionType
from finance_tracker.domain.models import Product, RateSchedule, Transaction, Valuation

from .base import IProductRepository, ITransactionRepository, IValuationRepository


class SQLModelProductRepository(IProductRepository):
    """Repository SQLModel pour Products."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, product: Product) -> Product:
        """Créer un produit."""
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)

        return product

    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Récupérer un produit par ID."""

        return self.session.get(Product, product_id)

    def get_by_name(self, name: str) -> Optional[Product]:
        stmt = select(Product).where(Product.name == name)

        return self.session.exec(stmt).scalars().first()

    def get_all(self) -> List[Product]:
        stmt = select(Product)

        return list(self.session.exec(stmt).scalars())

    def update(self, product: Product) -> Product:
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)

        return product

    def delete(self, product_id: int) -> bool:
        product = self.session.get(Product, product_id)

        if product:
            self.session.delete(product)
            self.session.commit()

            return True

        return False


class SQLModelTransactionRepository(ITransactionRepository):
    """Repository SQLModel pour Transactions."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, transaction: Transaction) -> Transaction:
        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)

        return transaction

    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        return self.session.get(Transaction, transaction_id)

    def get_by_product_id(self, product_id: int) -> List[Transaction]:
        stmt = (
            select(Transaction)
            .where(Transaction.product_id == product_id)
            .order_by(Transaction.date)
            )

        return list(self.session.exec(stmt).scalars())

    def get_all(self) -> List[Transaction]:
        stmt = select(Transaction).order_by(Transaction.date)

        return list(self.session.exec(stmt).scalars())

    def get_all_by_type(self, transaction_type: TransactionType) -> List[Transaction]:
        stmt = select(Transaction).where(Transaction.type == transaction_type)

        return list(self.session.exec(stmt).scalars())

    def update(self, transaction: Transaction) -> Transaction:
        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)

        return transaction

    def delete(self, transaction_id: int) -> bool:
        transaction = self.session.get(Transaction, transaction_id)

        if transaction:
            self.session.delete(transaction)
            self.session.commit()

            return True

        return False


class SQLModelValuationRepository(IValuationRepository):
    """Repository SQLModel pour Valuations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, valuation: Valuation) -> Valuation:
        self.session.add(valuation)
        self.session.commit()
        self.session.refresh(valuation)

        return valuation

    def get_by_id(self, valuation_id: int) -> Optional[Valuation]:
        return self.session.get(Valuation, valuation_id)

    def get_latest_by_product_id(self, product_id: int) -> Optional[Valuation]:
        stmt = (
            select(Valuation)
            .where(Valuation.product_id == product_id)
            .order_by(desc(Valuation.date))
            .limit(1)
            )

        return self.session.exec(stmt).scalars().first()

    def get_by_product_id(self, product_id: int) -> List[Valuation]:
        stmt = (
            select(Valuation)
            .where(Valuation.product_id == product_id)
            .order_by(Valuation.date)
            )

        return list(self.session.exec(stmt).scalars())

    def get_all(self) -> List[Valuation]:
        stmt = select(Valuation).order_by(Valuation.date)

        return list(self.session.exec(stmt).scalars())

    def update(self, valuation: Valuation) -> Valuation:
        self.session.add(valuation)
        self.session.commit()
        self.session.refresh(valuation)

        return valuation

    def delete(self, valuation_id: int) -> bool:
        valuation = self.session.get(Valuation, valuation_id)

        if valuation:
            self.session.delete(valuation)
            self.session.commit()

            return True

        return False


class SQLModelRateScheduleRepository:
    """Repository SQLModel pour RateSchedules."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, rate_schedule: RateSchedule) -> RateSchedule:
        self.session.add(rate_schedule)
        self.session.commit()
        self.session.refresh(rate_schedule)

        return rate_schedule

    def get_by_product_id(self, product_id: int) -> List[RateSchedule]:
        stmt = (
            select(RateSchedule)
            .where(RateSchedule.product_id == product_id)
            .order_by(RateSchedule.date_effective)
            )

        return list(self.session.exec(stmt).scalars())

    def get_rate_at_date(self, product_id: int, at_date: datetime):
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


def get_engine():
    return create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
