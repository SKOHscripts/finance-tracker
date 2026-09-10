"""Tests for the on-chain cost-basis reconstruction.

This is the part of the app most likely to be believed more than it deserves,
so the tests are weighted towards what it gets wrong: units it cannot price,
transfers it cannot classify, history it never saw. A reconstruction that
quietly reports high confidence over a partial record would be worse than no
reconstruction at all.
"""
# pylint: disable=redefined-outer-name  # pytest fixture pattern
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlmodel import Session, create_engine

from finance_tracker.domain.enums import (
    Chain,
    CostBasisConfidence,
    TransferDirection,
    TransferKind,
    )
from finance_tracker.domain.models import Wallet, WalletTransfer
from finance_tracker.repositories.sqlmodel_repo import init_db
from finance_tracker.services.wallets.cost_basis import (
    classify,
    derive_basis,
    own_addresses,
    set_manual_unit_cost,
    store_estimate,
    )

START = datetime(2025, 3, 1, tzinfo=timezone.utc)


class FixedPrices:
    """A price source with a known answer, or none at all."""

    def __init__(self, price=None):
        self.price = price
        self.calls = 0

    def price_on(self, _coin_id, _day, _currency):
        self.calls += 1
        return self.price


def transfer(direction, units, *, days=0, kind=None, counterparty="0xother",
             tx_hash=None, price=None):
    """Build a movement without touching the database."""
    row = WalletTransfer(
        wallet_id=1,
        tx_hash=tx_hash or f"0x{days}{units}{direction.value}",
        log_index=0,
        timestamp=START + timedelta(days=days),
        direction=direction,
        contract_address="",
        symbol="ETH",
        units=Decimal(str(units)),
        counterparty=counterparty,
        )
    row.kind = kind or (
        TransferKind.ACQUISITION if direction is TransferDirection.IN
        else TransferKind.DISPOSAL
        )
    if price is not None:
        row.unit_price_eur = Decimal(str(price))
    return row


@pytest.fixture()
def session():
    """An in-memory database at the current schema."""
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    with Session(engine) as active:
        yield active


class TestClassification:
    """What a movement means for cost basis."""

    def test_an_inbound_transfer_from_a_stranger_is_an_acquisition(self):
        row = transfer(TransferDirection.IN, 1)
        assert classify(row, {"0xme"}) is TransferKind.ACQUISITION

    def test_an_outbound_transfer_to_a_stranger_is_a_disposal(self):
        row = transfer(TransferDirection.OUT, 1)
        assert classify(row, {"0xme"}) is TransferKind.DISPOSAL

    def test_a_move_between_your_own_wallets_is_internal(self):
        """Otherwise moving coins to a second ledger would look like buying them."""
        row = transfer(TransferDirection.IN, 1, counterparty="0xMyOther")
        assert classify(row, {"0xmyother"}) is TransferKind.INTERNAL

    def test_matching_is_case_insensitive(self):
        row = transfer(TransferDirection.IN, 1, counterparty="0xABCdef")
        assert classify(row, {"0xabcdef"}) is TransferKind.INTERNAL

    def test_own_addresses_are_read_lowercased(self, session):
        session.add(Wallet(label="a", chain=Chain.ETHEREUM, address="0xAbC"))
        session.commit()
        assert own_addresses(session) == {"0xabc"}


class TestDeriveBasis:
    """The moving-average walk."""

    def test_a_single_priced_purchase(self):
        result = derive_basis(
            [transfer(TransferDirection.IN, 2)], "ethereum", FixedPrices(2000.0))
        assert result.units == Decimal("2")
        assert result.cost_basis == Decimal("4000.00")
        assert result.unit_cost == Decimal("2000.00000000")
        assert result.confidence is CostBasisConfidence.HIGH

    def test_a_disposal_removes_cost_proportionally(self):
        """Selling half the units removes half the capital, not half the proceeds."""
        result = derive_basis(
            [transfer(TransferDirection.IN, 2, days=0),
             transfer(TransferDirection.OUT, 1, days=30)],
            "ethereum", FixedPrices(2000.0),
            )
        assert result.units == Decimal("1")
        assert result.cost_basis == Decimal("2000.00")

    def test_internal_movements_change_nothing(self):
        result = derive_basis(
            [transfer(TransferDirection.IN, 2, days=0),
             transfer(TransferDirection.IN, 5, days=10, kind=TransferKind.INTERNAL),
             transfer(TransferDirection.OUT, 5, days=11, kind=TransferKind.INTERNAL)],
            "ethereum", FixedPrices(2000.0),
            )
        assert result.units == Decimal("2")
        assert result.cost_basis == Decimal("4000.00")

    def test_a_stored_price_is_reused_without_calling_the_api(self):
        source = FixedPrices(9999.0)
        result = derive_basis(
            [transfer(TransferDirection.IN, 1, price=1500.0)], "ethereum", source)
        assert result.cost_basis == Decimal("1500.00")
        assert source.calls == 0

    def test_unpriced_units_are_counted_as_uncovered(self):
        """Beyond the free plan's year of history, there is simply no price."""
        result = derive_basis(
            [transfer(TransferDirection.IN, 3)], "ethereum", FixedPrices(None))
        assert result.units == Decimal("3")
        assert result.uncovered_units == Decimal("3")
        assert result.unit_cost is None
        assert result.confidence is CostBasisConfidence.NONE
        assert result.unpriced_acquisitions == 1

    def test_the_unit_cost_is_spread_over_the_units_it_explains(self):
        """Dividing by every unit would understate the basis by the unpriced share."""
        priced = transfer(TransferDirection.IN, 1, days=0, price=1000.0)
        unpriced = transfer(TransferDirection.IN, 1, days=1)
        result = derive_basis([priced, unpriced], "ethereum", FixedPrices(None))

        assert result.units == Decimal("2")
        assert result.uncovered_units == Decimal("1")
        # 1000 EUR explains one unit, so the rate is 1000, not 500.
        assert result.unit_cost == Decimal("1000.00000000")
        assert result.cost_basis == Decimal("2000.00")

    def test_partial_coverage_lands_in_the_middle_band(self):
        """Two units of three priced is 67 % coverage: medium, not high."""
        rows = [
            transfer(TransferDirection.IN, 1, days=0, price=1000.0),
            transfer(TransferDirection.IN, 1, days=1, price=1200.0),
            transfer(TransferDirection.IN, 1, days=2),
            ]
        result = derive_basis(rows, "ethereum", FixedPrices(None))
        assert result.uncovered_units == Decimal("1")
        assert result.confidence is CostBasisConfidence.MEDIUM

    def test_low_coverage_is_reported_as_low(self):
        rows = [transfer(TransferDirection.IN, 1, days=0, price=1000.0)]
        rows += [transfer(TransferDirection.IN, 1, days=i) for i in range(1, 10)]
        result = derive_basis(rows, "ethereum", FixedPrices(None))
        assert result.confidence is CostBasisConfidence.LOW

    def test_a_truncated_history_can_never_be_high_confidence(self):
        """The coverage ratio itself was computed on a partial record."""
        result = derive_basis(
            [transfer(TransferDirection.IN, 2)], "ethereum", FixedPrices(2000.0),
            history_complete=False,
            )
        assert result.confidence is CostBasisConfidence.MEDIUM

    def test_an_unlisted_asset_derives_nothing_and_says_why(self):
        result = derive_basis(
            [transfer(TransferDirection.IN, 2)], "", FixedPrices(2000.0))
        assert result.confidence is CostBasisConfidence.NONE
        assert any("aucune cotation" in n for n in result.notes)

    def test_a_disposal_before_any_acquisition_is_skipped(self):
        """The fetched history starts too late; it must not go negative."""
        result = derive_basis(
            [transfer(TransferDirection.OUT, 5, days=0),
             transfer(TransferDirection.IN, 2, days=1)],
            "ethereum", FixedPrices(2000.0),
            )
        assert result.units == Decimal("2")
        assert result.cost_basis == Decimal("4000.00")

    def test_movements_are_walked_in_chronological_order(self):
        """Order decides the average, so an unsorted input must not change it."""
        rows = [
            transfer(TransferDirection.OUT, 1, days=30),
            transfer(TransferDirection.IN, 2, days=0, price=1000.0),
            ]
        result = derive_basis(rows, "ethereum", FixedPrices(None))
        assert result.units == Decimal("1")
        assert result.cost_basis == Decimal("1000.00")

    def test_the_swap_caveat_is_always_stated(self):
        """A token received from a swap carries the basis of the asset given up."""
        result = derive_basis(
            [transfer(TransferDirection.IN, 1)], "ethereum", FixedPrices(1000.0))
        assert any("swap" in n for n in result.notes)

    def test_no_movements_derive_nothing(self):
        result = derive_basis([], "ethereum", FixedPrices(1000.0))
        assert result.units == Decimal("0")
        assert result.confidence is CostBasisConfidence.NONE


class TestPersistence:
    """Storing an estimate, and the user's right to overrule it."""

    def test_an_estimate_is_stored_with_its_method_and_caveats(self, session):
        result = derive_basis(
            [transfer(TransferDirection.IN, 2)], "ethereum", FixedPrices(2000.0))
        row = store_estimate(session, product_id=1, result=result)

        assert row.cost_basis_eur == Decimal("4000.00")
        assert row.confidence is CostBasisConfidence.HIGH
        assert row.method == "MOVING_AVERAGE_ONCHAIN_V1"
        assert row.note

    def test_recomputing_never_discards_a_manual_correction(self, session):
        """A resync that silently undid a correction would be worse than useless."""
        set_manual_unit_cost(session, product_id=1, unit_cost=Decimal("123.45"))

        result = derive_basis(
            [transfer(TransferDirection.IN, 2)], "ethereum", FixedPrices(2000.0))
        row = store_estimate(session, product_id=1, result=result)

        assert row.manual_unit_cost_eur == Decimal("123.45000000")
        assert row.unit_cost_eur == Decimal("2000.00000000")

    def test_clearing_the_manual_figure_falls_back_to_the_estimate(self, session):
        set_manual_unit_cost(session, product_id=1, unit_cost=Decimal("123.45"))
        row = set_manual_unit_cost(session, product_id=1, unit_cost=None)
        assert row.manual_unit_cost_eur is None
