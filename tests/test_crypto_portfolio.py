"""Tests for deriving engine positions from the database.

Three numbers per line — units, value, cost basis — each with several possible
sources. What these tests pin down is the order of preference and, just as
importantly, that the reported provenance matches the figure actually used. A
correct number labelled as coming from the wrong place is still a bug: the
interface uses that label to decide whether to call it an estimate.
"""
# pylint: disable=redefined-outer-name  # pytest fixture pattern
from datetime import datetime
from decimal import Decimal

import pytest
from sqlmodel import Session, create_engine

from finance_tracker.domain.enums import (
    Chain,
    CostBasisConfidence,
    ProductType,
    QuantityUnit,
    TransactionType,
    )
from finance_tracker.domain.models import (
    CostBasisEstimate,
    CryptoAsset,
    Product,
    Transaction,
    Valuation,
    Wallet,
    WalletHolding,
    )
from finance_tracker.repositories.sqlmodel_repo import init_db
from finance_tracker.services.crypto.portfolio import load_positions, resolve_position


@pytest.fixture()
def session():
    """An in-memory database at the current schema."""
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    with Session(engine) as active:
        yield active


@pytest.fixture()
def product(session):
    """A crypto product mapped to a market listing."""
    row = Product(
        name="Monero",
        type=ProductType.CRYPTO,
        quantity_unit=QuantityUnit.CRYPTO_UNITS,
        )
    session.add(row)
    session.commit()
    session.refresh(row)
    session.add(CryptoAsset(product_id=row.id, coingecko_id="monero", symbol="XMR"))
    session.commit()
    return row


def crypto_asset(session, product_id):
    """Read back the market identity of a product."""
    from sqlalchemy import select
    return session.exec(
        select(CryptoAsset).where(CryptoAsset.product_id == product_id)
        ).scalars().first()


def buy(session, product_id, amount, quantity, day=datetime(2025, 1, 1)):
    """Record a purchase."""
    session.add(Transaction(
        product_id=product_id, date=day, type=TransactionType.BUY,
        amount_eur=Decimal(str(amount)), quantity=Decimal(str(quantity)),
        ))
    session.commit()


def sell(session, product_id, amount, quantity, day=datetime(2025, 6, 1)):
    """Record a sale."""
    session.add(Transaction(
        product_id=product_id, date=day, type=TransactionType.SELL,
        amount_eur=Decimal(str(amount)), quantity=Decimal(str(quantity)),
        ))
    session.commit()


class TestUnitsResolution:
    """Where the number of units comes from."""

    def test_transactions_net_buys_against_sells(self, session, product):
        buy(session, product.id, 1000, 10)
        sell(session, product.id, 400, 3)

        resolved = resolve_position(session, product, crypto_asset(session, product.id))
        assert resolved.position.units == pytest.approx(7.0)
        assert resolved.sources.units_from == "transactions"

    def test_a_wallet_balance_outranks_the_ledger(self, session, product):
        """The chain is not an opinion: it wins over what was typed."""
        buy(session, product.id, 1000, 10)

        wallet = Wallet(label="w", chain=Chain.ETHEREUM, address="0xabc")
        session.add(wallet)
        session.commit()
        session.refresh(wallet)
        session.add(WalletHolding(
            wallet_id=wallet.id, contract_address="", symbol="XMR",
            units=Decimal("42.5"), product_id=product.id,
            ))
        session.commit()

        resolved = resolve_position(session, product, crypto_asset(session, product.id))
        assert resolved.position.units == pytest.approx(42.5)
        assert resolved.sources.units_from == "wallet"

    def test_ignored_holdings_are_excluded(self, session, product):
        wallet = Wallet(label="w", chain=Chain.ETHEREUM, address="0xabc")
        session.add(wallet)
        session.commit()
        session.refresh(wallet)
        session.add(WalletHolding(
            wallet_id=wallet.id, contract_address="0x1", symbol="XMR",
            units=Decimal("10"), product_id=product.id,
            ))
        session.add(WalletHolding(
            wallet_id=wallet.id, contract_address="0x2", symbol="SPAM",
            units=Decimal("999"), product_id=product.id, ignored=True,
            ))
        session.commit()

        resolved = resolve_position(session, product, crypto_asset(session, product.id))
        assert resolved.position.units == pytest.approx(10.0)

    def test_an_emptied_address_reports_zero_not_unknown(self, session, product):
        """Zero units is a fact; None would send it back to the ledger."""
        wallet = Wallet(label="w", chain=Chain.ETHEREUM, address="0xabc")
        session.add(wallet)
        session.commit()
        session.refresh(wallet)
        session.add(WalletHolding(
            wallet_id=wallet.id, contract_address="", symbol="XMR",
            units=Decimal("0"), product_id=product.id,
            ))
        session.commit()

        resolved = resolve_position(session, product, crypto_asset(session, product.id))
        assert resolved.position.units == pytest.approx(0.0)
        assert resolved.sources.units_from == "wallet"

    def test_a_valuation_is_the_last_resort(self, session, product):
        """No units at all: the line carries a frozen amount, and says so."""
        session.add(Valuation(
            product_id=product.id, date=datetime(2025, 5, 1),
            total_value_eur=Decimal("1234.56"),
            ))
        session.commit()

        resolved = resolve_position(session, product, crypto_asset(session, product.id))
        assert resolved.position.units is None
        assert resolved.position.notional_eur == pytest.approx(1234.56)
        assert resolved.sources.value_from == "valuation"
        assert "ne suit pas le cours" in resolved.sources.note

    def test_the_latest_valuation_wins(self, session, product):
        session.add(Valuation(
            product_id=product.id, date=datetime(2025, 1, 1),
            total_value_eur=Decimal("100"),
            ))
        session.add(Valuation(
            product_id=product.id, date=datetime(2025, 9, 1),
            total_value_eur=Decimal("900"),
            ))
        session.commit()

        resolved = resolve_position(session, product, crypto_asset(session, product.id))
        assert resolved.position.notional_eur == pytest.approx(900.0)


class TestCostBasisResolution:
    """Where the invested capital comes from."""

    def test_from_purchases(self, session, product):
        buy(session, product.id, 1000, 10)
        resolved = resolve_position(session, product, crypto_asset(session, product.id))
        assert resolved.position.cost_basis_eur == pytest.approx(1000.0)
        assert resolved.sources.cost_basis_from == "transactions"

    def test_a_sale_removes_what_the_units_cost_not_what_they_sold_for(
        self, session, product
        ):
        """A moving average: what remains keeps carrying its real cost."""
        buy(session, product.id, 1000, 10)  # 100 EUR per unit
        sell(session, product.id, 900, 5)  # sold at 180, cost was 100

        resolved = resolve_position(session, product, crypto_asset(session, product.id))
        assert resolved.position.cost_basis_eur == pytest.approx(500.0)

    def test_fees_are_capital_sunk_into_the_line(self, session, product):
        buy(session, product.id, 1000, 10)
        session.add(Transaction(
            product_id=product.id, date=datetime(2025, 2, 1),
            type=TransactionType.FEE, amount_eur=Decimal("25"),
            ))
        session.commit()

        resolved = resolve_position(session, product, crypto_asset(session, product.id))
        assert resolved.position.cost_basis_eur == pytest.approx(1025.0)

    def test_selling_everything_leaves_nothing_invested(self, session, product):
        buy(session, product.id, 1000, 10)
        sell(session, product.id, 1500, 10)

        resolved = resolve_position(session, product, crypto_asset(session, product.id))
        assert resolved.position.cost_basis_eur is None or \
            resolved.position.cost_basis_eur == pytest.approx(0.0)

    def test_no_purchase_means_unknown_not_zero(self, session, product):
        """Unknown disables the stop; zero would read as a total gain."""
        resolved = resolve_position(session, product, crypto_asset(session, product.id))
        assert resolved.position.cost_basis_eur is None
        assert resolved.sources.cost_basis_from == "none"

    def test_an_onchain_estimate_fills_in_when_the_ledger_is_silent(
        self, session, product
        ):
        session.add(CostBasisEstimate(
            product_id=product.id,
            units=Decimal("10"),
            cost_basis_eur=Decimal("777"),
            unit_cost_eur=Decimal("77.7"),
            confidence=CostBasisConfidence.MEDIUM,
            ))
        session.commit()

        resolved = resolve_position(session, product, crypto_asset(session, product.id))
        assert resolved.position.cost_basis_eur == pytest.approx(777.0)
        assert resolved.sources.cost_basis_from == "onchain"
        assert "estimation" in resolved.sources.note

    def test_real_purchases_outrank_an_onchain_estimate(self, session, product):
        """A receipt beats a reconstruction."""
        buy(session, product.id, 1000, 10)
        session.add(CostBasisEstimate(
            product_id=product.id, units=Decimal("10"),
            cost_basis_eur=Decimal("777"), unit_cost_eur=Decimal("77.7"),
            ))
        session.commit()

        resolved = resolve_position(session, product, crypto_asset(session, product.id))
        assert resolved.position.cost_basis_eur == pytest.approx(1000.0)
        assert resolved.sources.cost_basis_from == "transactions"

    def test_a_manual_figure_outranks_everything(self, session, product):
        """The user knows things no chain and no ledger records."""
        buy(session, product.id, 1000, 10)
        session.add(CostBasisEstimate(
            product_id=product.id, units=Decimal("10"),
            cost_basis_eur=Decimal("777"), unit_cost_eur=Decimal("77.7"),
            manual_unit_cost_eur=Decimal("50"),
            ))
        session.commit()

        resolved = resolve_position(session, product, crypto_asset(session, product.id))
        assert resolved.position.cost_basis_eur == pytest.approx(500.0)  # 50 × 10 units
        assert resolved.sources.cost_basis_from == "manual"


class TestLoadPositions:
    """Which products the engine is handed."""

    def test_only_products_with_a_market_identity_are_included(
        self, session, product,  # pylint: disable=unused-argument  # fixture side effect
        ):
        """An SCPI has no business in a crypto rotation."""
        session.add(Product(name="SCPI Machin", type=ProductType.SCPI))
        session.commit()

        resolved = load_positions(session)
        assert [r.product.name for r in resolved] == ["Monero"]

    def test_the_gas_reserve_carries_over(self, session, product):
        asset = crypto_asset(session, product.id)
        asset.gas_reserve_eur = Decimal("150")
        session.commit()

        resolved = load_positions(session)
        assert resolved[0].position.gas_reserve_eur == pytest.approx(150.0)

    def test_a_line_switched_off_is_still_loaded(self, session, product):
        """It must be displayed; the engine is what declines to arbitrate it."""
        asset = crypto_asset(session, product.id)
        asset.arbitrated = False
        session.commit()

        resolved = load_positions(session)
        assert len(resolved) == 1
        assert resolved[0].position.arbitrated is False

    def test_an_empty_portfolio_returns_nothing(self, session):
        assert not load_positions(session)
