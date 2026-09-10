"""Tests for correcting a position's figures by hand.

A correction is given more authority than the chain, so the tests that matter
are the ones about that authority: it must actually outrank every derived
source, it must be reversible without residue, and it must not be able to
describe a position that cannot exist.

The precedence is the point. A correction the wallet sync silently wins over
would be worse than no correction at all — the user would believe a figure the
engine never used.
"""
# pylint: disable=redefined-outer-name  # pytest fixture pattern
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlmodel import Session, create_engine

from finance_tracker.domain.enums import Chain, ProductType, TransactionType
from finance_tracker.domain.models import (
    CryptoAsset,
    Transaction,
    Wallet,
    WalletHolding,
    )
from finance_tracker.repositories.sqlmodel_repo import init_db
from finance_tracker.services.crypto.manual_asset import add_manual_asset
from finance_tracker.services.crypto.overrides import (
    OverrideError,
    clear_all,
    divergence,
    resolve_cost,
    set_overrides,
    set_reserve_and_arbitration,
    )
from finance_tracker.services.crypto.portfolio import load_positions


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    with Session(engine) as active:
        yield active


@pytest.fixture()
def line(session):
    """A declared position: 10 XMR bought for 1000 EUR."""
    product = add_manual_asset(
        session, name="Monero", coingecko_id="monero", symbol="XMR",
        units=Decimal("10"), total_cost_eur=Decimal("1000"),
        )
    return session.exec(
        select(CryptoAsset).where(CryptoAsset.product_id == product.id)
        ).scalars().first()


def only(session):
    """The single resolved position."""
    resolved = load_positions(session)
    assert len(resolved) == 1
    return resolved[0]


def watch_address(session, product_id, units):
    """Point a synced wallet at the product, reporting *units*."""
    wallet = Wallet(label="w", chain=Chain.ETHEREUM, address="0xabc")
    session.add(wallet)
    session.commit()
    session.refresh(wallet)
    session.add(WalletHolding(
        wallet_id=wallet.id, contract_address="", symbol="XMR",
        units=Decimal(str(units)), product_id=product_id,
        ))
    session.commit()


class TestPrecedence:
    """A correction outranks every derived source. That is its whole job."""

    def test_a_corrected_quantity_beats_the_ledger(self, session, line):
        set_overrides(session, line, units=Decimal("7.5"))

        resolved = only(session)
        assert resolved.position.units == pytest.approx(7.5)
        assert resolved.sources.units_from == "manual"

    def test_a_corrected_quantity_beats_the_chain(self, session, line):
        """The chain is not an opinion, but it is not the whole truth either.

        A balance can be read correctly and still be wrong about what is held:
        an address the user does not watch, or one they do not control.
        """
        watch_address(session, line.product_id, 42)
        assert only(session).sources.units_from == "wallet"

        set_overrides(session, line, units=Decimal("7.5"))

        resolved = only(session)
        assert resolved.position.units == pytest.approx(7.5)
        assert resolved.sources.units_from == "manual"

    def test_a_corrected_capital_beats_the_purchases(self, session, line):
        set_overrides(session, line, cost_basis_eur=Decimal("640"))

        resolved = only(session)
        assert resolved.position.cost_basis_eur == pytest.approx(640.0)
        assert resolved.sources.cost_basis_from == "manual"

    def test_the_two_corrections_are_independent(self, session, line):
        """Correcting the quantity must not disturb the capital, or the reverse."""
        set_overrides(session, line, units=Decimal("7.5"))

        resolved = only(session)
        assert resolved.position.units == pytest.approx(7.5)
        assert resolved.position.cost_basis_eur == pytest.approx(1000.0)
        assert resolved.sources.cost_basis_from == "transactions"


class TestReversibility:
    """Clearing must leave nothing behind."""

    def test_clearing_the_quantity_returns_it_to_the_ledger(self, session, line):
        set_overrides(session, line, units=Decimal("7.5"))
        set_overrides(session, line, clear_units=True)

        resolved = only(session)
        assert resolved.position.units == pytest.approx(10.0)
        assert resolved.sources.units_from == "transactions"

    def test_clearing_the_quantity_returns_it_to_the_chain(self, session, line):
        watch_address(session, line.product_id, 42)
        set_overrides(session, line, units=Decimal("7.5"))
        set_overrides(session, line, clear_units=True)

        resolved = only(session)
        assert resolved.position.units == pytest.approx(42.0)
        assert resolved.sources.units_from == "wallet"

    def test_clearing_everything_returns_the_whole_line(self, session, line):
        set_overrides(session, line, units=Decimal("1"), cost_basis_eur=Decimal("1"))
        clear_all(session, line)

        resolved = only(session)
        assert resolved.sources.units_from == "transactions"
        assert resolved.sources.cost_basis_from == "transactions"
        assert resolved.position.cost_basis_eur == pytest.approx(1000.0)

    def test_absence_is_not_clearing(self, session, line):
        """A form submitting every field must not wipe a correction it never touched."""
        set_overrides(session, line, units=Decimal("7.5"))
        set_overrides(session, line, cost_basis_eur=Decimal("640"))

        assert only(session).position.units == pytest.approx(7.5)

    def test_clearing_wins_over_a_value_passed_alongside(self, session, line):
        """The explicit intent beats the field that happened to carry a number."""
        set_overrides(session, line, units=Decimal("7.5"))
        set_overrides(session, line, units=Decimal("3"), clear_units=True)

        assert only(session).sources.units_from == "transactions"


class TestZeroIsAClaim:
    """Zero and unknown are different statements about a line."""

    def test_a_corrected_quantity_of_zero_is_kept(self, session, line):
        """An emptied line is a fact, not an absence of information."""
        set_overrides(session, line, units=Decimal("0"))

        resolved = only(session)
        assert resolved.position.units == pytest.approx(0.0)
        assert resolved.sources.units_from == "manual"

    def test_a_corrected_capital_of_zero_is_kept(self, session, line):
        """An airdrop cost nothing; reporting that as unknown loses the claim."""
        set_overrides(session, line, cost_basis_eur=Decimal("0"))

        resolved = only(session)
        assert resolved.position.cost_basis_eur == pytest.approx(0.0)
        assert resolved.sources.cost_basis_from == "manual"


class TestRefusals:
    """A correction may be wrong; it may not be impossible."""

    def test_a_negative_quantity_is_refused(self, session, line):
        with pytest.raises(OverrideError, match="négative"):
            set_overrides(session, line, units=Decimal("-1"))

    def test_a_negative_capital_is_refused(self, session, line):
        with pytest.raises(OverrideError, match="négatif"):
            set_overrides(session, line, cost_basis_eur=Decimal("-1"))

    def test_a_negative_reserve_is_refused(self, session, line):
        with pytest.raises(OverrideError, match="négative"):
            set_reserve_and_arbitration(session, line, gas_reserve_eur=Decimal("-1"))

    def test_a_refused_correction_leaves_the_line_alone(self, session, line):
        set_overrides(session, line, units=Decimal("7.5"))

        with pytest.raises(OverrideError):
            set_overrides(session, line, units=Decimal("-1"))

        assert only(session).position.units == pytest.approx(7.5)


class TestCostForms:
    """Per unit or in total — both are how people hold the number."""

    def test_a_unit_cost_is_multiplied_by_the_quantity(self):
        assert resolve_cost(Decimal("10"), Decimal("64"), None) == Decimal("640.00")

    def test_a_total_is_taken_as_given(self):
        assert resolve_cost(Decimal("10"), None, Decimal("640")) == Decimal("640.00")

    def test_neither_form_means_no_correction(self):
        assert resolve_cost(Decimal("10"), None, None) is None

    def test_both_forms_at_once_are_refused(self):
        with pytest.raises(OverrideError, match="pas les deux"):
            resolve_cost(Decimal("10"), Decimal("64"), Decimal("700"))

    def test_a_unit_cost_without_a_quantity_is_refused(self):
        """Nothing to multiply by, and guessing one would invent a capital."""
        with pytest.raises(OverrideError, match="quantité"):
            resolve_cost(None, Decimal("64"), None)

    @pytest.mark.parametrize("unit,total", [(Decimal("-1"), None), (None, Decimal("-1"))])
    def test_a_negative_figure_is_refused(self, unit, total):
        with pytest.raises(OverrideError, match="négati"):
            resolve_cost(Decimal("10"), unit, total)


class TestDivergence:
    """A correction that contradicts the chain is surfaced, never swallowed."""

    def test_a_gap_is_reported(self, session, line):
        watch_address(session, line.product_id, 42)
        set_overrides(session, line, units=Decimal("7.5"))

        gap = divergence(session, line, "XMR")
        assert gap is not None
        assert gap.chain_units == Decimal("42")
        assert gap.manual_units == Decimal("7.5")
        assert gap.difference == Decimal("-34.5")

    def test_agreement_reports_nothing(self, session, line):
        watch_address(session, line.product_id, 42)
        set_overrides(session, line, units=Decimal("42"))

        assert divergence(session, line) is None

    def test_no_correction_reports_nothing(self, session, line):
        watch_address(session, line.product_id, 42)
        assert divergence(session, line) is None

    def test_no_watched_address_reports_nothing(self, session, line):
        """Nothing to contradict: the ledger is not a second opinion here."""
        set_overrides(session, line, units=Decimal("7.5"))
        assert divergence(session, line) is None

    def test_an_ignored_holding_does_not_count_as_the_chain(self, session, line):
        wallet = Wallet(label="w", chain=Chain.ETHEREUM, address="0xabc")
        session.add(wallet)
        session.commit()
        session.refresh(wallet)
        session.add(WalletHolding(
            wallet_id=wallet.id, contract_address="0x1", symbol="SPAM",
            units=Decimal("999"), product_id=line.product_id, ignored=True,
            ))
        session.commit()
        set_overrides(session, line, units=Decimal("7.5"))

        assert divergence(session, line) is None


class TestLineSettings:
    """The reserve and the arbitration switch, edited from the same table."""

    def test_the_reserve_reaches_the_engine(self, session, line):
        set_reserve_and_arbitration(session, line, gas_reserve_eur=Decimal("150"))
        assert only(session).position.gas_reserve_eur == pytest.approx(150.0)

    def test_switching_a_line_off_keeps_it_visible(self, session, line):
        set_reserve_and_arbitration(session, line, arbitrated=False)

        resolved = only(session)
        assert resolved.position.arbitrated is False

    def test_omitting_a_field_leaves_it_alone(self, session, line):
        set_reserve_and_arbitration(session, line, gas_reserve_eur=Decimal("150"))
        set_reserve_and_arbitration(session, line, arbitrated=False)

        assert only(session).position.gas_reserve_eur == pytest.approx(150.0)


class TestCorrectionsSurvive:
    """A correction is stored, not applied and forgotten."""

    def test_a_correction_survives_a_later_purchase(self, session, line):
        """The ledger moving must not quietly take the line back."""
        set_overrides(session, line, units=Decimal("7.5"))

        session.add(Transaction(
            product_id=line.product_id, date=datetime(2025, 8, 1),
            type=TransactionType.BUY,
            quantity=Decimal("5"), amount_eur=Decimal("700"),
            ))
        session.commit()

        assert only(session).position.units == pytest.approx(7.5)

    def test_a_correction_survives_a_wallet_sync(self, session, line):
        set_overrides(session, line, units=Decimal("7.5"))
        watch_address(session, line.product_id, 42)

        assert only(session).position.units == pytest.approx(7.5)

    def test_a_product_without_a_correction_is_untouched(self, session, line):
        """The default remains automatic; nothing is opted in by existing."""
        assert line.manual_units is None
        assert line.manual_cost_basis_eur is None
        assert only(session).sources.units_from == "transactions"


def test_a_non_crypto_product_is_unaffected(session):
    """A savings account has no correction columns to acquire."""
    from finance_tracker.domain.models import Product
    session.add(Product(name="Livret A", type=ProductType.CASH))
    session.commit()

    assert not load_positions(session)
