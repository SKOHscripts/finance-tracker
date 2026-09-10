"""Tests for the correctable table, driven through a recorded Streamlit.

The table is where a wrong figure gets fixed, so the way it can fail is
particular: not a crash, but a correction that lands on the wrong line, or an
untouched row that silently freezes today's derived figure as a permanent
override. Neither would raise. Both would be discovered weeks later, as a
verdict nobody can explain.

So these tests drive the real widget and then read the database.
"""
# pylint: disable=redefined-outer-name  # pytest fixture pattern
# pylint: disable=unused-argument  # the fakes mirror Streamlit's signatures
# pylint: disable=too-few-public-methods  # the fakes are recorders
# pylint: disable=protected-access  # the widget's internals are the boundary
# pylint: disable=redefined-builtin  # `help` and `type` are Streamlit's kwarg names
from contextlib import contextmanager
from decimal import Decimal

import pandas as pd
import pytest
from sqlalchemy import select
from sqlmodel import Session, create_engine

from finance_tracker.domain.enums import Chain
from finance_tracker.domain.models import CryptoAsset, Wallet, WalletHolding
from finance_tracker.repositories.sqlmodel_repo import init_db
from finance_tracker.services.crypto.manual_asset import add_manual_asset
from finance_tracker.services.crypto.overrides import set_overrides
from finance_tracker.services.crypto.portfolio import load_positions
from finance_tracker.web.ui import position_editor


class Rerun(Exception):
    """Stands in for Streamlit's rerun."""


class FakeColumnConfig:
    """The column_config namespace, which the widget only ever constructs."""

    @staticmethod
    def TextColumn(label, **kwargs):  # noqa: N802
        return ("text", label, kwargs)

    @staticmethod
    def NumberColumn(label, **kwargs):  # noqa: N802
        return ("number", label, kwargs)

    @staticmethod
    def CheckboxColumn(label, **kwargs):  # noqa: N802
        return ("checkbox", label, kwargs)


class FakeStreamlit:
    """Enough of Streamlit to run the editor and record what it drew."""

    column_config = FakeColumnConfig()

    def __init__(self, edits=None, clicks=None, values=None):
        self.edits = edits
        self.clicks = clicks or {}
        self.values = values or {}
        self.calls = []
        self.session_state = {}
        self.drawn = None

    @contextmanager
    def expander(self, label, expanded=False):
        yield self

    def columns(self, spec, **kwargs):
        count = spec if isinstance(spec, int) else len(spec)
        return [self for _ in range(count)]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def radio(self, label, options, format_func=None, horizontal=False, key=None):
        options = list(options)
        return self.values.get(label, options[0])

    def data_editor(self, data, **kwargs):
        """Hand back the scripted edits, or the frame unchanged."""
        self.drawn = data
        return data if self.edits is None else self.edits(data)

    def button(self, label, key=None, type=None, width=None):
        return bool(self.clicks.get(key or label, False))

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

    @property
    def errors(self):
        return [b for k, b in self.calls if k == "error"]

    @property
    def warnings(self):
        return [b for k, b in self.calls if k == "warning"]

    @property
    def successes(self):
        return [b for k, b in self.calls if k == "success"]


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    with Session(engine) as active:
        yield active


@pytest.fixture()
def two_lines(session):
    """Two positions, so a correction landing on the wrong one is visible."""
    add_manual_asset(session, name="Monero", coingecko_id="monero", symbol="XMR",
                     units=Decimal("10"), total_cost_eur=Decimal("1000"))
    add_manual_asset(session, name="Ether", coingecko_id="ethereum", symbol="ETH",
                     units=Decimal("2"), total_cost_eur=Decimal("4000"))
    return load_positions(session)


@pytest.fixture()
def render(monkeypatch):
    """Run the editor with a scripted Streamlit."""
    def run(session, resolved, edits=None, clicks=None, values=None):
        fake = FakeStreamlit(edits, clicks, values)
        monkeypatch.setattr(position_editor, "st", fake)
        monkeypatch.setattr(position_editor, "t", lambda key: key)
        monkeypatch.setattr(position_editor, "source_label", lambda s: s)
        try:
            position_editor.render_editor(session, resolved)
        except Rerun:
            pass
        return fake
    return run


APPLY = "editor.apply"
RESET = "editor.reset_all"
UNITS_FIX = "editor.col_units_fix"
COST_FIX = "editor.col_cost_fix"
RESERVE = "editor.col_reserve"
ARBITRATED = "editor.col_arbitrated"


def asset_of(session, symbol) -> CryptoAsset:
    return session.exec(
        select(CryptoAsset).where(CryptoAsset.symbol == symbol)
        ).scalars().first()


def edit_row(index, column, value):
    """Build an edit function that changes one cell of one row."""
    def apply(frame):
        out = frame.copy()
        out.loc[index, column] = value
        return out
    return apply


class TestTheFrame:
    """What the table shows before anything is edited."""

    def test_derived_figures_are_shown_with_their_source(self, session, two_lines,
                                                         monkeypatch):
        monkeypatch.setattr(position_editor, "t", lambda key: key)
        monkeypatch.setattr(position_editor, "source_label", lambda s: s)

        frame = position_editor.build_frame(two_lines)

        assert "transactions" in frame["editor.col_units_auto"].iloc[0]
        assert "transactions" in frame["editor.col_cost_auto"].iloc[0]

    def test_correction_columns_start_empty(self, session, two_lines, monkeypatch):
        """An empty column is what makes an untouched row mean 'leave it alone'."""
        monkeypatch.setattr(position_editor, "t", lambda key: key)
        monkeypatch.setattr(position_editor, "source_label", lambda s: s)

        frame = position_editor.build_frame(two_lines)

        assert frame[UNITS_FIX].isna().all()
        assert frame[COST_FIX].isna().all()

    def test_an_existing_correction_is_shown(self, session, two_lines, monkeypatch):
        monkeypatch.setattr(position_editor, "t", lambda key: key)
        monkeypatch.setattr(position_editor, "source_label", lambda s: s)
        set_overrides(session, two_lines[1].asset, units=Decimal("7.5"))

        frame = position_editor.build_frame(load_positions(session))

        assert frame[UNITS_FIX].dropna().tolist() == [7.5]


class TestApplying:
    """What lands in the database."""

    def test_an_untouched_table_writes_no_correction(self, session, two_lines, render):
        """The trap this design exists to avoid: freezing today's derived figure."""
        render(session, two_lines, clicks={APPLY: True})

        for symbol in ("XMR", "ETH"):
            asset = asset_of(session, symbol)
            assert asset.manual_units is None
            assert asset.manual_cost_basis_eur is None

    def test_a_corrected_quantity_is_written(self, session, two_lines, render):
        render(session, two_lines,
               edits=edit_row(0, UNITS_FIX, 7.5), clicks={APPLY: True})

        assert asset_of(session, "ETH").manual_units == Decimal("7.5")

    def test_the_correction_lands_on_the_row_it_was_typed_in(self, session, two_lines,
                                                             render):
        """Rows are matched by position; a shifted match would corrupt a line.

        `load_positions` orders by product name, so row 0 is Ether and row 1
        is Monero. Correcting row 1 must move Monero and leave Ether alone.
        """
        render(session, two_lines,
               edits=edit_row(1, UNITS_FIX, 3.25), clicks={APPLY: True})

        assert asset_of(session, "XMR").manual_units == Decimal("3.25")
        assert asset_of(session, "ETH").manual_units is None

    def test_a_corrected_total_is_written(self, session, two_lines, render):
        render(session, two_lines,
               edits=edit_row(0, COST_FIX, 640.0), clicks={APPLY: True},
               values={"editor.cost_mode": "total"})

        assert asset_of(session, "ETH").manual_cost_basis_eur == Decimal("640.00")

    def test_a_unit_cost_is_multiplied_by_the_derived_quantity(self, session, two_lines,
                                                               render):
        """2 ETH held; 100 per unit must store 200, not 100."""
        render(session, two_lines,
               edits=edit_row(0, COST_FIX, 100.0), clicks={APPLY: True},
               values={"editor.cost_mode": "unit"})

        assert asset_of(session, "ETH").manual_cost_basis_eur == Decimal("200.00")

    def test_a_unit_cost_uses_the_corrected_quantity_when_there_is_one(
        self, session, two_lines, render
        ):
        """Both cells edited in the same submission must agree with each other."""
        def edits(frame):
            out = frame.copy()
            out.loc[0, UNITS_FIX] = 5.0
            out.loc[0, COST_FIX] = 100.0
            return out

        render(session, two_lines, edits=edits, clicks={APPLY: True},
               values={"editor.cost_mode": "unit"})

        asset = asset_of(session, "ETH")
        assert asset.manual_units == Decimal("5")
        assert asset.manual_cost_basis_eur == Decimal("500.00")  # 5 × 100

    def test_the_reserve_and_the_switch_are_written(self, session, two_lines, render):
        def edits(frame):
            out = frame.copy()
            out.loc[0, RESERVE] = 150.0
            out.loc[0, ARBITRATED] = False
            return out

        render(session, two_lines, edits=edits, clicks={APPLY: True})

        asset = asset_of(session, "ETH")
        assert asset.gas_reserve_eur == Decimal("150")
        assert asset.arbitrated is False

    def test_a_zero_correction_is_written_rather_than_read_as_empty(
        self, session, two_lines, render
        ):
        """An emptied line is a claim; treating zero as blank would lose it."""
        render(session, two_lines,
               edits=edit_row(0, UNITS_FIX, 0.0), clicks={APPLY: True})

        assert asset_of(session, "ETH").manual_units == Decimal("0")

    def test_nothing_is_written_without_the_button(self, session, two_lines, render):
        render(session, two_lines, edits=edit_row(0, UNITS_FIX, 7.5))

        assert asset_of(session, "ETH").manual_units is None


class TestClearing:
    """Emptying a cell is how a correction is undone."""

    def test_emptying_the_cell_drops_the_correction(self, session, two_lines, render):
        set_overrides(session, two_lines[0].asset, units=Decimal("7.5"))
        resolved = load_positions(session)

        render(session, resolved,
               edits=edit_row(0, UNITS_FIX, float("nan")), clicks={APPLY: True})

        assert asset_of(session, "ETH").manual_units is None

    def test_the_reset_button_clears_every_line(self, session, two_lines, render):
        set_overrides(session, two_lines[0].asset, units=Decimal("7.5"))
        set_overrides(session, two_lines[1].asset, cost_basis_eur=Decimal("99"))
        resolved = load_positions(session)

        render(session, resolved, clicks={RESET: True})

        for symbol in ("XMR", "ETH"):
            asset = asset_of(session, symbol)
            assert asset.manual_units is None
            assert asset.manual_cost_basis_eur is None


class TestRefusals:
    """A bad figure is reported; it never takes the page down."""

    def test_a_negative_quantity_is_reported(self, session, two_lines, render):
        fake = render(session, two_lines,
                      edits=edit_row(0, UNITS_FIX, -1.0), clicks={APPLY: True})

        assert fake.errors
        assert asset_of(session, "ETH").manual_units is None

    def test_a_negative_capital_is_reported(self, session, two_lines, render):
        fake = render(session, two_lines,
                      edits=edit_row(0, COST_FIX, -1.0), clicks={APPLY: True},
                      values={"editor.cost_mode": "total"})

        assert fake.errors


class TestDivergence:
    """A correction contradicting the chain is surfaced."""

    def test_a_gap_against_a_watched_address_is_warned_about(self, session, two_lines,
                                                             render):
        asset = asset_of(session, "XMR")
        wallet = Wallet(label="w", chain=Chain.ETHEREUM, address="0xabc")
        session.add(wallet)
        session.commit()
        session.refresh(wallet)
        session.add(WalletHolding(
            wallet_id=wallet.id, contract_address="", symbol="XMR",
            units=Decimal("42"), product_id=asset.product_id,
            ))
        session.commit()
        set_overrides(session, asset, units=Decimal("7.5"))

        fake = render(session, load_positions(session))

        assert fake.warnings

    def test_no_gap_means_no_warning(self, session, two_lines, render):
        fake = render(session, two_lines)
        assert not fake.warnings


class TestReadingCells:
    """The one function that decides empty from zero."""

    @pytest.mark.parametrize("value", [None, float("nan"), "", "   ", "nan"])
    def test_an_empty_cell_reads_as_none(self, value):
        assert position_editor._num(value) is None

    def test_zero_reads_as_zero(self):
        assert position_editor._num(0.0) == Decimal("0")

    def test_a_comma_decimal_is_accepted(self):
        assert position_editor._num("12,5") == Decimal("12.5")

    def test_an_unreadable_cell_is_refused(self, monkeypatch):
        monkeypatch.setattr(position_editor, "t", lambda key: "{value}")
        from finance_tracker.services.crypto.overrides import OverrideError
        with pytest.raises(OverrideError):
            position_editor._num("douze")


class TestFormatting:
    """Figures are shown without inventing precision."""

    def test_units_lose_their_trailing_zeros_without_losing_the_number(self):
        assert position_editor._fmt_units(100.0) == "100"
        assert position_editor._fmt_units(12.5) == "12.5"

    def test_an_unknown_figure_is_a_dash(self):
        assert position_editor._fmt_units(None) == "—"
        assert position_editor._fmt_eur(None) == "—"

    def test_zero_units_is_shown_as_zero_not_blank(self):
        """`rstrip` on '0.00000000' would otherwise leave an empty string."""
        assert position_editor._fmt_units(0.0) == "0"

    def test_an_amount_carries_its_currency(self):
        assert position_editor._fmt_eur(1750.0).endswith("€")


def test_the_frame_has_one_row_per_position(session, two_lines, monkeypatch):
    monkeypatch.setattr(position_editor, "t", lambda key: key)
    monkeypatch.setattr(position_editor, "source_label", lambda s: s)

    assert len(position_editor.build_frame(two_lines)) == 2


def test_an_empty_portfolio_builds_an_empty_frame(monkeypatch):
    monkeypatch.setattr(position_editor, "t", lambda key: key)
    assert isinstance(position_editor.build_frame([]), pd.DataFrame)
