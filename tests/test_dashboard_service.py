"""Tests for DashboardService per-product methods."""
from datetime import datetime
from decimal import Decimal

import pytest
from sqlmodel import Session, SQLModel, create_engine

from finance_tracker.domain.enums import ProductType, QuantityUnit, TransactionType
from finance_tracker.domain.models import Product, Transaction, Valuation
from finance_tracker.services.dashboard_service import (
    DEPOSIT_BASED_TYPES,
    PRODUCT_COLORS,
    DashboardService,
)


@pytest.fixture()
def session():
    """Create an in-memory SQLite session with tables."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture()
def bitcoin_product(session):
    """Seed a Bitcoin product with valuations and BUY transactions."""
    product = Product(name="Bitcoin", type=ProductType.BITCOIN, quantity_unit=QuantityUnit.BTC_SATS)
    session.add(product)
    session.commit()
    session.refresh(product)

    # Two valuations
    session.add(Valuation(
        product_id=product.id,
        date=datetime(2025, 1, 1),
        total_value_eur=Decimal("5000"),
        unit_price_eur=Decimal("50000"),
    ))
    session.add(Valuation(
        product_id=product.id,
        date=datetime(2025, 6, 1),
        total_value_eur=Decimal("8000"),
        unit_price_eur=Decimal("80000"),
    ))

    # BUY transaction: 4000 EUR
    session.add(Transaction(
        product_id=product.id,
        date=datetime(2025, 1, 1),
        type=TransactionType.BUY,
        amount_eur=Decimal("4000"),
        quantity=Decimal("0.08"),
    ))
    session.commit()
    return product


@pytest.fixture()
def savings_product(session):
    """Seed a savings product with DEPOSIT transactions."""
    product = Product(name="Livret A", type=ProductType.SAVINGS, quantity_unit=QuantityUnit.NONE)
    session.add(product)
    session.commit()
    session.refresh(product)

    session.add(Valuation(
        product_id=product.id,
        date=datetime(2025, 3, 1),
        total_value_eur=Decimal("10500"),
        unit_price_eur=None,
    ))

    session.add(Transaction(
        product_id=product.id,
        date=datetime(2025, 1, 1),
        type=TransactionType.DEPOSIT,
        amount_eur=Decimal("10000"),
    ))
    session.commit()
    return product


@pytest.fixture()
def empty_product(session):
    """Seed a product with no valuations or transactions."""
    product = Product(name="Empty", type=ProductType.CASH, quantity_unit=QuantityUnit.NONE)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


class TestGetProductHistory:
    def test_returns_chronological_valuations(self, session, bitcoin_product):
        svc = DashboardService(session)
        history = svc.get_product_history(bitcoin_product.id)

        assert len(history) == 2
        assert history[0]["date"] == datetime(2025, 1, 1)
        assert history[1]["date"] == datetime(2025, 6, 1)
        assert history[0]["total_value_eur"] == 5000.0
        assert history[1]["total_value_eur"] == 8000.0

    def test_empty_history(self, session, empty_product):
        svc = DashboardService(session)
        history = svc.get_product_history(empty_product.id)

        assert history == []

    def test_includes_unit_price(self, session, bitcoin_product):
        svc = DashboardService(session)
        history = svc.get_product_history(bitcoin_product.id)

        assert history[0]["unit_price_eur"] == 50000.0
        assert history[1]["unit_price_eur"] == 80000.0

    def test_null_unit_price(self, session, savings_product):
        svc = DashboardService(session)
        history = svc.get_product_history(savings_product.id)

        assert len(history) == 1
        assert history[0]["unit_price_eur"] is None


class TestGetProductPru:
    def test_buy_based_pru(self, session, bitcoin_product):
        svc = DashboardService(session)
        pru = svc.get_product_pru(bitcoin_product.id)

        # BUY total = 4000 EUR, latest valuation: 8000 / 80000 = 0.1 BTC
        # PRU = 4000 / 0.1 = 40000
        assert pru is not None
        assert abs(pru - 40000.0) < 1.0

    def test_deposit_based_pru(self, session, savings_product):
        svc = DashboardService(session)
        pru = svc.get_product_pru(savings_product.id)

        # DEPOSIT total = 10000
        assert pru == 10000.0

    def test_no_transactions_returns_none(self, session, empty_product):
        svc = DashboardService(session)
        pru = svc.get_product_pru(empty_product.id)

        assert pru is None

    def test_nonexistent_product_returns_none(self, session):
        svc = DashboardService(session)
        pru = svc.get_product_pru(99999)

        assert pru is None

    def test_deposit_types_constant(self):
        assert ProductType.CASH in DEPOSIT_BASED_TYPES
        assert ProductType.SAVINGS in DEPOSIT_BASED_TYPES
        assert ProductType.INSURANCE in DEPOSIT_BASED_TYPES
        assert ProductType.PER in DEPOSIT_BASED_TYPES
        assert ProductType.BITCOIN not in DEPOSIT_BASED_TYPES


class TestGetProductDetails:
    def test_returns_full_structure(self, session, bitcoin_product):
        svc = DashboardService(session)
        details = svc.get_product_details(bitcoin_product.id)

        assert details is not None
        assert details["name"] == "Bitcoin"
        assert details["type"] == "BITCOIN"
        assert details["color"] == "#F7931A"
        assert len(details["history"]) == 2
        assert details["pru"] is not None
        assert details["current_value"] == 8000.0
        assert details["net_invested"] == 4000.0
        assert details["gains_eur"] == 4000.0
        assert abs(details["gains_pct"] - 100.0) < 0.1

    def test_nonexistent_returns_none(self, session):
        svc = DashboardService(session)
        details = svc.get_product_details(99999)

        assert details is None

    def test_empty_product_details(self, session, empty_product):
        svc = DashboardService(session)
        details = svc.get_product_details(empty_product.id)

        assert details is not None
        assert details["current_value"] == 0.0
        assert details["history"] == []
        assert details["pru"] is None

    def test_savings_product_details(self, session, savings_product):
        svc = DashboardService(session)
        details = svc.get_product_details(savings_product.id)

        assert details is not None
        assert details["name"] == "Livret A"
        assert details["color"] == PRODUCT_COLORS["SAVINGS"]
        assert details["current_value"] == 10500.0
        assert details["net_invested"] == 10000.0
        assert details["gains_eur"] == 500.0


class TestProductColors:
    def test_all_product_types_have_colors(self):
        for pt in ProductType:
            assert pt.value in PRODUCT_COLORS, f"Missing color for {pt.value}"
