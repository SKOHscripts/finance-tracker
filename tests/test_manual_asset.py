"""Tests for declaring a crypto position by hand.

The feature exists for the assets the wallet importer structurally cannot see —
Monero above all, whose balance cannot be read from an address without its view
key. So the thing worth pinning down is not that a row gets written: it is that
a declared position reaches the engine carrying the *same* three numbers a
synced one does, from the same sources, and that the ways a user can get it
wrong are refused with something they can act on.
"""
# pylint: disable=redefined-outer-name  # pytest fixture pattern
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlmodel import Session, create_engine

from finance_tracker.domain.enums import ProductType, QuantityUnit, TransactionType
from finance_tracker.domain.models import CryptoAsset, Product, Transaction
from finance_tracker.repositories.sqlmodel_repo import init_db
from finance_tracker.services.crypto.manual_asset import (
    ManualAssetError,
    add_manual_asset,
    attach_listing,
    find_by_coingecko_id,
    )
from finance_tracker.services.crypto.portfolio import load_positions


@pytest.fixture()
def session():
    """An in-memory database at the current schema."""
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    with Session(engine) as active:
        yield active


def _asset(session, product_id) -> CryptoAsset:
    return session.exec(
        select(CryptoAsset).where(CryptoAsset.product_id == product_id)
        ).scalars().first()


def _transactions(session, product_id) -> list[Transaction]:
    return list(session.exec(
        select(Transaction).where(Transaction.product_id == product_id)
        ).scalars().all())


class TestDeclaringAnAsset:
    """The happy path, and what it actually writes."""

    def test_the_product_gains_a_market_identity(self, session):
        """Without this row the engine cannot price the line at all."""
        product = add_manual_asset(
            session, name="Monero", coingecko_id="monero", symbol="xmr",
            units=Decimal("12.5"), unit_cost_eur=Decimal("140"),
            )

        asset = _asset(session, product.id)
        assert asset is not None
        assert asset.coingecko_id == "monero"
        assert asset.symbol == "XMR"

    def test_the_holding_is_recorded_as_a_purchase(self, session):
        """Not a private field: the ledger is where every product's figures live."""
        product = add_manual_asset(
            session, name="Monero", coingecko_id="monero",
            units=Decimal("12.5"), unit_cost_eur=Decimal("140"),
            )

        rows = _transactions(session, product.id)
        assert len(rows) == 1
        assert rows[0].type == TransactionType.BUY
        assert rows[0].quantity == Decimal("12.5")
        assert rows[0].amount_eur == Decimal("1750.00")  # 12.5 × 140

    def test_a_total_investment_is_taken_as_given(self, session):
        """The other way people hold the number: what left the bank account."""
        product = add_manual_asset(
            session, name="Monero", coingecko_id="monero",
            units=Decimal("12.5"), total_cost_eur=Decimal("1600"),
            )

        assert _transactions(session, product.id)[0].amount_eur == Decimal("1600.00")

    def test_a_declared_asset_reaches_the_engine(self, session):
        """The whole point. A position the importer cannot see must still arbitrate."""
        add_manual_asset(
            session, name="Monero", coingecko_id="monero", symbol="XMR",
            units=Decimal("12.5"), unit_cost_eur=Decimal("140"),
            )

        resolved = load_positions(session)
        assert len(resolved) == 1

        position = resolved[0].position
        assert position.coingecko_id == "monero"
        assert position.units == pytest.approx(12.5)
        assert position.cost_basis_eur == pytest.approx(1750.0)
        assert resolved[0].sources.units_from == "transactions"
        assert resolved[0].sources.cost_basis_from == "transactions"

    def test_the_recorded_date_is_the_one_given(self, session):
        """A holding built years ago should not land in today's ledger."""
        product = add_manual_asset(
            session, name="Monero", coingecko_id="monero",
            units=Decimal("1"), unit_cost_eur=Decimal("100"),
            acquired_on=datetime(2021, 3, 14),
            )

        assert _transactions(session, product.id)[0].date.date() == datetime(2021, 3, 14).date()

    def test_the_listing_is_stored_lower_case(self, session):
        """Every price call is made with it; CoinGecko ids are lower case."""
        product = add_manual_asset(
            session, name="Monero", coingecko_id="  MONERO  ", units=Decimal("1"),
            )
        assert _asset(session, product.id).coingecko_id == "monero"

    def test_the_gas_reserve_and_the_switch_are_carried(self, session):
        add_manual_asset(
            session, name="Ether", coingecko_id="ethereum", units=Decimal("2"),
            gas_reserve_eur=Decimal("150"), arbitrated=False,
            )

        position = load_positions(session)[0].position
        assert position.gas_reserve_eur == pytest.approx(150.0)
        assert position.arbitrated is False


class TestUnitsAreNativeCoins:
    """The quantity typed in is the quantity the engine prices."""

    def test_bitcoin_is_typed_in_coins_not_satoshis(self, session):
        """Labelling the line in satoshis would invite a figure 1e8 too large.

        The engine multiplies units by a coin price, so the unit the user is
        asked for has to be the coin. This is the one place the manual path
        deliberately differs from the wallet importer's labelling.
        """
        product = add_manual_asset(
            session, name="Bitcoin froid", coingecko_id="bitcoin",
            units=Decimal("0.35"), unit_cost_eur=Decimal("30000"),
            )

        assert product.quantity_unit == QuantityUnit.CRYPTO_UNITS
        assert load_positions(session)[0].position.units == pytest.approx(0.35)

    def test_bitcoin_still_lands_in_the_bitcoin_space(self, session):
        """The type is what routes it; only the unit label changes."""
        product = add_manual_asset(
            session, name="Bitcoin froid", coingecko_id="bitcoin", units=Decimal("0.35"),
            )
        assert product.type == ProductType.BITCOIN

    def test_anything_else_is_a_crypto_product(self, session):
        product = add_manual_asset(
            session, name="Monero", coingecko_id="monero", units=Decimal("1"),
            )
        assert product.type == ProductType.CRYPTO


class TestAnAssetWithoutAPurchasePrice:
    """An airdrop or a mined holding has no cost, and that is not zero."""

    def test_units_without_a_cost_are_accepted(self, session):
        add_manual_asset(session, name="Monero", coingecko_id="monero", units=Decimal("3"))

        resolved = load_positions(session)[0]
        assert resolved.position.units == pytest.approx(3.0)
        assert resolved.position.cost_basis_eur is None

    def test_an_unknown_cost_is_not_read_as_a_total_gain(self, session):
        """None disables the trailing stop; zero would read as +infinity."""
        add_manual_asset(session, name="Monero", coingecko_id="monero", units=Decimal("3"))

        assert load_positions(session)[0].sources.cost_basis_from == "none"

    def test_a_line_can_be_created_with_no_position_at_all(self, session):
        """Declare the asset now, enter the purchases in the ledger afterwards."""
        product = add_manual_asset(session, name="Monero", coingecko_id="monero")

        assert not _transactions(session, product.id)
        assert _asset(session, product.id) is not None


class TestRefusals:
    """Every way a user can make the portfolio wrong, and the answer."""

    def test_a_second_product_on_the_same_listing_is_refused(self, session):
        """Two products on one listing would count the same holding twice."""
        add_manual_asset(session, name="Monero", coingecko_id="monero", units=Decimal("1"))

        with pytest.raises(ManualAssetError, match="déjà associé"):
            add_manual_asset(
                session, name="Monero bis", coingecko_id="monero", units=Decimal("1"),
                )

    def test_the_refusal_names_the_product_already_holding_it(self, session):
        """A message the user can act on, not a constraint violation."""
        add_manual_asset(session, name="Mon Monero", coingecko_id="monero")

        with pytest.raises(ManualAssetError, match="Mon Monero"):
            add_manual_asset(session, name="Autre", coingecko_id="monero")

    def test_a_duplicate_product_name_is_refused(self, session):
        session.add(Product(name="Monero", type=ProductType.CRYPTO))
        session.commit()

        with pytest.raises(ManualAssetError, match="s'appelle déjà"):
            add_manual_asset(session, name="Monero", coingecko_id="monero")

    def test_an_empty_name_is_refused(self, session):
        with pytest.raises(ManualAssetError, match="nom de produit"):
            add_manual_asset(session, name="   ", coingecko_id="monero")

    def test_an_empty_listing_is_refused(self, session):
        """Without a listing nothing can price the line, so it would be inert."""
        with pytest.raises(ManualAssetError, match="cotation"):
            add_manual_asset(session, name="Monero", coingecko_id="")

    def test_both_cost_forms_at_once_are_refused(self, session):
        """They would contradict each other; silently preferring one hides that."""
        with pytest.raises(ManualAssetError, match="pas les deux"):
            add_manual_asset(
                session, name="Monero", coingecko_id="monero", units=Decimal("1"),
                unit_cost_eur=Decimal("100"), total_cost_eur=Decimal("250"),
                )

    def test_a_cost_without_a_quantity_is_refused(self, session):
        """A price of revient on nothing describes no position."""
        with pytest.raises(ManualAssetError, match="quantité"):
            add_manual_asset(
                session, name="Monero", coingecko_id="monero",
                unit_cost_eur=Decimal("100"),
                )

    @pytest.mark.parametrize("quantity", [Decimal("0"), Decimal("-1")])
    def test_a_non_positive_quantity_is_refused(self, session, quantity):
        with pytest.raises(ManualAssetError, match="supérieure à zéro"):
            add_manual_asset(
                session, name="Monero", coingecko_id="monero", units=quantity,
                )

    @pytest.mark.parametrize("field", ["unit_cost_eur", "total_cost_eur"])
    def test_a_negative_cost_is_refused(self, session, field):
        with pytest.raises(ManualAssetError, match="négati"):
            add_manual_asset(
                session, name="Monero", coingecko_id="monero", units=Decimal("1"),
                **{field: Decimal("-10")},
                )

    def test_a_negative_reserve_is_refused(self, session):
        with pytest.raises(ManualAssetError, match="négative"):
            add_manual_asset(
                session, name="Monero", coingecko_id="monero", units=Decimal("1"),
                gas_reserve_eur=Decimal("-5"),
                )

    def test_a_refused_declaration_leaves_nothing_behind(self, session):
        """No half-created product from a validation that failed."""
        with pytest.raises(ManualAssetError):
            add_manual_asset(
                session, name="Monero", coingecko_id="monero", units=Decimal("-1"),
                )

        assert not session.exec(select(Product)).scalars().all()


class TestAttachingToAnExistingProduct:
    """The other half: a product that predates the crypto features."""

    @pytest.fixture()
    def legacy_product(self, session):
        """A Bitcoin product created before the signal engine existed."""
        product = Product(
            name="Bitcoin", type=ProductType.BITCOIN,
            quantity_unit=QuantityUnit.CRYPTO_UNITS,
            )
        session.add(product)
        session.commit()
        session.refresh(product)
        session.add(Transaction(
            product_id=product.id, date=datetime(2024, 1, 1),
            type=TransactionType.BUY,
            quantity=Decimal("0.5"), amount_eur=Decimal("20000"),
            ))
        session.commit()
        return product

    def test_an_existing_product_joins_the_arbitrage(self, session, legacy_product):
        """It already holds real units and a real cost basis; it needed one row."""
        assert not load_positions(session)

        attach_listing(session, legacy_product, coingecko_id="bitcoin", symbol="BTC")

        resolved = load_positions(session)
        assert len(resolved) == 1
        assert resolved[0].position.units == pytest.approx(0.5)
        assert resolved[0].position.cost_basis_eur == pytest.approx(20000.0)

    def test_attaching_twice_updates_rather_than_duplicates(self, session, legacy_product):
        """A product maps to exactly one listing."""
        attach_listing(session, legacy_product, coingecko_id="bitcoin", symbol="BTC")
        attach_listing(session, legacy_product, coingecko_id="monero", symbol="XMR")

        rows = session.exec(
            select(CryptoAsset).where(CryptoAsset.product_id == legacy_product.id)
            ).scalars().all()
        assert len(rows) == 1
        assert rows[0].coingecko_id == "monero"

    def test_stealing_another_product_s_listing_is_refused(self, session, legacy_product):
        add_manual_asset(session, name="Monero", coingecko_id="monero", units=Decimal("1"))

        with pytest.raises(ManualAssetError, match="déjà associé"):
            attach_listing(session, legacy_product, coingecko_id="monero")

    def test_re_attaching_its_own_listing_is_not_a_clash(self, session, legacy_product):
        """Changing only the reserve must not trip the uniqueness check."""
        attach_listing(session, legacy_product, coingecko_id="bitcoin")
        asset = attach_listing(
            session, legacy_product, coingecko_id="bitcoin",
            gas_reserve_eur=Decimal("50"),
            )
        assert asset.gas_reserve_eur == Decimal("50")

    def test_an_empty_listing_is_refused(self, session, legacy_product):
        with pytest.raises(ManualAssetError, match="cotation"):
            attach_listing(session, legacy_product, coingecko_id="  ")


class TestFindByListing:
    """The lookup the uniqueness checks are built on."""

    def test_a_mapped_listing_is_found_case_insensitively(self, session):
        add_manual_asset(session, name="Monero", coingecko_id="monero")
        assert find_by_coingecko_id(session, "MONERO") is not None

    def test_an_unmapped_listing_is_not_found(self, session):
        assert find_by_coingecko_id(session, "monero") is None

    def test_an_empty_query_finds_nothing(self, session):
        """Must not match the first row just because the string is falsy."""
        add_manual_asset(session, name="Monero", coingecko_id="monero")
        assert find_by_coingecko_id(session, "") is None
