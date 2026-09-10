"""Tests for the manual-asset form itself, not just the service behind it.

Written because the last bug that reached production was exactly here: the
service was covered, the widget was not, and the mismatch between them crashed
every page that drew it. A form that reads a field the service does not take,
or hands it a string where it expects a Decimal, fails the same way — at the
user, on first use.

So these drive the real view function through a recorded Streamlit and check
what actually lands in the database, plus the refusals it must show instead of
raising.
"""
# pylint: disable=redefined-outer-name  # pytest fixture pattern
# pylint: disable=unused-argument  # the fakes mirror Streamlit's signatures
# pylint: disable=too-few-public-methods  # the fakes are recorders, not objects
# pylint: disable=protected-access  # the view function under test is private
# pylint: disable=redefined-builtin  # `help` and `type` are Streamlit's own kwarg names
from contextlib import contextmanager
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlmodel import Session, create_engine

from finance_tracker.domain.models import CryptoAsset, Product, Transaction
from finance_tracker.repositories.sqlmodel_repo import init_db
from finance_tracker.services.crypto.coingecko_client import CoinGeckoError, Listing
from finance_tracker.web.views import crypto_wallets

XMR = Listing(id="monero", symbol="XMR", name="Monero", rank=30)
XMC = Listing(id="monero-classic", symbol="XMC", name="Monero Classic")


class Rerun(Exception):
    """Stands in for Streamlit's rerun, which unwinds the script."""


class FakeClient:
    """A CoinGecko client that answers from a script."""

    def __init__(self, hits=None, error=None):
        self.hits = hits or []
        self.error = error
        self.queries = []

    def search(self, query, limit=12):
        self.queries.append(query)
        if self.error:
            raise self.error
        return self.hits


class FakeStreamlit:
    """Enough of Streamlit to run the form and record what it drew.

    Widget values are looked up by label — which, with `t` patched to identity,
    is the translation key. Anything not scripted falls back to the widget's own
    default, so a test only states the fields it cares about.
    """

    def __init__(self, values=None, clicks=None):
        self.values = values or {}
        self.clicks = clicks or {}
        self.calls = []
        self.session_state = {}

    # ── containers ────────────────────────────────────────────────────────────

    @contextmanager
    def expander(self, label, expanded=False):
        yield self

    @contextmanager
    def form(self, key, clear_on_submit=False):
        yield self

    def columns(self, spec, **kwargs):
        count = spec if isinstance(spec, int) else len(spec)
        return [self for _ in range(count)]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    # ── inputs ────────────────────────────────────────────────────────────────

    def text_input(self, label, value="", key=None, placeholder=None, help=None,
                   type=None, label_visibility=None):
        return self.values.get(label, value)

    def selectbox(self, label, options, format_func=None, index=0, key=None,
                  label_visibility=None):
        options = list(options)
        return self.values.get(label, options[index] if options else None)

    def radio(self, label, options, format_func=None, horizontal=False, key=None):
        options = list(options)
        return self.values.get(label, options[0] if options else None)

    def date_input(self, label, value=None, key=None):
        return self.values.get(label, value)

    def checkbox(self, label, value=False, key=None, help=None):
        return self.values.get(label, value)

    def button(self, label, key=None, type=None, width=None):
        return bool(self.clicks.get(key or label, False))

    def form_submit_button(self, label, width=None):
        return bool(self.clicks.get(label, False))

    # ── output ────────────────────────────────────────────────────────────────

    def caption(self, body, **kwargs):
        self.calls.append(("caption", body))

    def info(self, body, **kwargs):
        self.calls.append(("info", body))

    def error(self, body, **kwargs):
        self.calls.append(("error", body))

    def success(self, body, **kwargs):
        self.calls.append(("success", body))

    def warning(self, body, **kwargs):
        self.calls.append(("warning", body))

    def rerun(self):
        raise Rerun()

    # ── assertions ────────────────────────────────────────────────────────────

    @property
    def errors(self):
        return [body for kind, body in self.calls if kind == "error"]

    @property
    def successes(self):
        return [body for kind, body in self.calls if kind == "success"]


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    with Session(engine) as active:
        yield active


@pytest.fixture()
def render(monkeypatch):
    """Run the form with a scripted Streamlit, and hand back the recorder."""
    def run(session, client, values=None, clicks=None, state=None):
        fake = FakeStreamlit(values, clicks)
        fake.session_state.update(state or {})
        monkeypatch.setattr(crypto_wallets, "st", fake)
        monkeypatch.setattr(crypto_wallets, "t", lambda key: key)
        try:
            crypto_wallets._render_add_manual(session, client)
        except Rerun:
            pass
        return fake
    return run


# Field labels, as the patched translator yields them.
QUERY = "wallets.manual_search"
NAME = "wallets.manual_name"
UNITS = "wallets.manual_units"
COST = "wallets.manual_cost"
COST_MODE = "wallets.manual_cost_mode"
RESERVE = "wallets.manual_reserve"
LISTING = "wallets.manual_listing"
SEARCH_BTN = "manual_search_btn"
ADD_BTN = "wallets.manual_add_btn"


class TestSearching:
    """Finding the listing before anything is written."""

    def test_a_search_stores_its_hits(self, session, render):
        client = FakeClient(hits=[XMR, XMC])

        fake = render(session, client,
                      values={QUERY: "xmr"}, clicks={SEARCH_BTN: True})

        assert client.queries == ["xmr"]
        assert fake.session_state["manual_hits"] == [XMR, XMC]

    def test_an_empty_query_is_refused_without_a_call(self, session, render):
        client = FakeClient(hits=[XMR])

        fake = render(session, client, values={QUERY: "  "}, clicks={SEARCH_BTN: True})

        assert not client.queries
        assert "wallets.manual_query_required" in fake.errors

    def test_an_api_failure_is_shown_not_raised(self, session, render):
        """A rate limit must not take the page down with it."""
        client = FakeClient(error=CoinGeckoError("429"))

        fake = render(session, client, values={QUERY: "xmr"}, clicks={SEARCH_BTN: True})

        assert fake.errors
        assert fake.session_state["manual_hits"] == []

    def test_no_hit_says_so(self, session, render):
        fake = render(session, FakeClient(hits=[]),
                      values={QUERY: "zzz"}, clicks={SEARCH_BTN: True})
        assert ("caption", "wallets.manual_no_hit") in fake.calls

    def test_nothing_is_drawn_before_a_search(self, session, render):
        """No stale form from a previous visit to the page."""
        fake = render(session, FakeClient(hits=[XMR]))
        assert not fake.errors
        assert not fake.successes


class TestSubmitting:
    """What the form actually writes."""

    def test_a_declared_asset_lands_in_the_database(self, session, render):
        fake = render(
            session, FakeClient(),
            values={NAME: "Monero", UNITS: "12.5", COST: "140"},
            clicks={ADD_BTN: True},
            state={"manual_hits": [XMR]},
            )

        assert fake.successes
        product = session.exec(select(Product)).scalars().first()
        assert product.name == "Monero"

        asset = session.exec(select(CryptoAsset)).scalars().first()
        assert asset.coingecko_id == "monero"
        assert asset.symbol == "XMR"

    def test_a_unit_price_is_multiplied_by_the_quantity(self, session, render):
        """The default cost mode. 12.5 × 140 must reach the ledger as 1750."""
        render(session, FakeClient(),
               values={NAME: "Monero", UNITS: "12.5", COST: "140"},
               clicks={ADD_BTN: True}, state={"manual_hits": [XMR]})

        transaction = session.exec(select(Transaction)).scalars().first()
        assert transaction.quantity == Decimal("12.5")
        assert transaction.amount_eur == Decimal("1750.00")

    def test_a_total_is_taken_as_given(self, session, render):
        render(session, FakeClient(),
               values={NAME: "Monero", UNITS: "12.5", COST: "1600",
                       COST_MODE: "total"},
               clicks={ADD_BTN: True}, state={"manual_hits": [XMR]})

        assert session.exec(
            select(Transaction)).scalars().first().amount_eur == Decimal("1600.00")

    def test_a_comma_decimal_is_accepted(self, session, render):
        """French keyboards type 12,5 — refusing it would be a needless wall."""
        render(session, FakeClient(),
               values={NAME: "Monero", UNITS: "12,5", COST: "140"},
               clicks={ADD_BTN: True}, state={"manual_hits": [XMR]})

        assert session.exec(
            select(Transaction)).scalars().first().quantity == Decimal("12.5")

    def test_the_chosen_listing_is_the_one_stored(self, session, render):
        """Two namesakes were offered; the pick must not silently be the first."""
        render(session, FakeClient(),
               values={NAME: "Monero Classic", UNITS: "1", LISTING: XMC},
               clicks={ADD_BTN: True}, state={"manual_hits": [XMR, XMC]})

        assert session.exec(
            select(CryptoAsset)).scalars().first().coingecko_id == "monero-classic"

    def test_the_hits_are_cleared_after_a_success(self, session, render):
        """Otherwise the next rerun redraws a form for an asset already added."""
        fake = render(session, FakeClient(),
                      values={NAME: "Monero", UNITS: "1"},
                      clicks={ADD_BTN: True}, state={"manual_hits": [XMR]})

        assert fake.session_state["manual_hits"] is None

    def test_a_cleared_date_does_not_take_the_page_down(self, session, render):
        """The field can be emptied; combining None with a time would raise."""
        render(session, FakeClient(),
               values={NAME: "Monero", UNITS: "1", "wallets.manual_date": None},
               clicks={ADD_BTN: True}, state={"manual_hits": [XMR]})

        transaction = session.exec(select(Transaction)).scalars().first()
        assert transaction is not None
        assert transaction.date is not None

    def test_an_asset_with_no_cost_is_accepted(self, session, render):
        render(session, FakeClient(), values={NAME: "Monero", UNITS: "3"},
               clicks={ADD_BTN: True}, state={"manual_hits": [XMR]})

        assert session.exec(select(Transaction)).scalars().first().amount_eur is None

    def test_a_reserve_reaches_the_asset(self, session, render):
        render(session, FakeClient(),
               values={NAME: "Monero", UNITS: "3", RESERVE: "150"},
               clicks={ADD_BTN: True}, state={"manual_hits": [XMR]})

        assert session.exec(
            select(CryptoAsset)).scalars().first().gas_reserve_eur == Decimal("150")


class TestSubmitRefusals:
    """A bad entry shows a message; it never takes the page down."""

    @pytest.mark.parametrize("field,value,message", [
        (UNITS, "douze", "wallets.manual_units_invalid"),
        (COST, "beaucoup", "wallets.manual_cost_invalid"),
        (RESERVE, "un peu", "wallets.manual_reserve_invalid"),
        ])
    def test_an_unreadable_figure_is_reported(self, session, render, field, value, message):
        fake = render(session, FakeClient(),
                      values={NAME: "Monero", UNITS: "1", field: value},
                      clicks={ADD_BTN: True}, state={"manual_hits": [XMR]})

        assert message in fake.errors
        assert not session.exec(select(Product)).scalars().all()

    def test_a_service_refusal_is_shown_to_the_user(self, session, render):
        """The message is written for them; it must not surface as a traceback."""
        render(session, FakeClient(), values={NAME: "Monero", UNITS: "1"},
               clicks={ADD_BTN: True}, state={"manual_hits": [XMR]})

        fake = render(session, FakeClient(), values={NAME: "Monero bis", UNITS: "1"},
                      clicks={ADD_BTN: True}, state={"manual_hits": [XMR]})

        assert any("déjà associé" in e for e in fake.errors)
        assert len(session.exec(select(Product)).scalars().all()) == 1

    def test_a_cost_without_a_quantity_is_reported(self, session, render):
        fake = render(session, FakeClient(), values={NAME: "Monero", COST: "140"},
                      clicks={ADD_BTN: True}, state={"manual_hits": [XMR]})

        assert any("quantité" in e for e in fake.errors)
        assert not session.exec(select(Product)).scalars().all()

    def test_the_form_draws_without_being_submitted(self, session, render):
        """Merely rendering it must not write anything or raise."""
        fake = render(session, FakeClient(), state={"manual_hits": [XMR]})

        assert not fake.errors
        assert not session.exec(select(Product)).scalars().all()
