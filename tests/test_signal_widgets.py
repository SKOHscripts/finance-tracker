"""Tests for the crypto rendering widgets.

These exist because of a bug that reached production: the view handed
`render_gates` the engine's `Gate` dataclasses while the function subscripted
them like dicts, so every scan that arbitrated a position crashed the page.
Nothing caught it, because nothing exercised the widgets at all.

So the point here is the *contract between the engine and the widgets*: feed
each widget exactly what the engine really produces, in both the live shape
(dataclasses) and the stored shape (dicts read back from the database), and
check it renders rather than raises.
"""
# pylint: disable=redefined-outer-name  # pytest fixture pattern
# pylint: disable=unused-argument  # the fakes mirror Streamlit's signatures
# pylint: disable=protected-access  # _fmt is the formatting under test
import json

import pytest

from finance_tracker.domain.enums import SignalVerdict
from finance_tracker.services.crypto.engine import (
    AssetMetrics,
    Gate,
    Position,
    PriorScan,
    run_scan,
    )
from finance_tracker.services.crypto.rules import load_rules
from finance_tracker.web.ui import signal_widgets


class FakeColumn:
    """A Streamlit column that records what was drawn on it."""

    def __init__(self, sink):
        self.sink = sink

    def metric(self, label, value, **kwargs):
        self.sink.append(("metric", label, value))

    def markdown(self, body, **kwargs):
        self.sink.append(("markdown", body))

    def caption(self, body, **kwargs):
        self.sink.append(("caption", body))

    def button(self, label, **kwargs):
        self.sink.append(("button", label))
        return False


class FakeStreamlit:
    """Enough of Streamlit to run the widgets and record their output.

    Deliberately not a mock that accepts anything: each method mirrors the real
    signature the widgets use, so a call the real Streamlit would reject fails
    here too.
    """

    def __init__(self):
        self.calls = []

    def caption(self, body, **kwargs):
        self.calls.append(("caption", body))

    def markdown(self, body, **kwargs):
        self.calls.append(("markdown", body))

    def info(self, body, **kwargs):
        self.calls.append(("info", body))

    def warning(self, body, **kwargs):
        self.calls.append(("warning", body))

    def dataframe(self, data, **kwargs):
        self.calls.append(("dataframe", data))

    def columns(self, spec, **kwargs):
        count = spec if isinstance(spec, int) else len(spec)
        return [FakeColumn(self.calls) for _ in range(count)]

    def metric(self, label, value, **kwargs):
        self.calls.append(("metric", label, value))

    @property
    def rendered_frames(self):
        """Every dataframe the widgets drew."""
        return [c[1] for c in self.calls if c[0] == "dataframe"]

    @property
    def metrics(self):
        """Every metric the widgets drew, as (label, value)."""
        return [(c[1], c[2]) for c in self.calls if c[0] == "metric"]


@pytest.fixture()
def fake_st(monkeypatch):
    """Swap Streamlit out for a recorder, and the translator for a passthrough."""
    fake = FakeStreamlit()
    monkeypatch.setattr(signal_widgets, "st", fake)
    # t() needs a session; the widgets only use it for labels, so the key
    # itself is a fine stand-in and keeps assertions readable.
    monkeypatch.setattr(signal_widgets, "t", lambda key: key)
    return fake


@pytest.fixture()
def rules():
    """The shipped thresholds."""
    return load_rules()


@pytest.fixture()
def scan_result(rules):
    """A real scan, run through the real engine, with a verdict on the line.

    Built to fire the trailing stop so several mechanisms have gates: that is
    the state the crashing page was in.
    """
    rows = [
        AssetMetrics(id="bitcoin", symbol="BTC", name="Bitcoin", price=60000.0,
                     volume_24h=2e9, ret_slow=30.0, ret_fast=20.0, vol_30d=45.0,
                     max_dd_90d=-15.0, dist_high_90d=-5.0, dist_high_stop=-5.0,
                     long_average=50000.0, sample_days=300),
        AssetMetrics(id="ethereum", symbol="ETH", name="Ethereum", price=2500.0,
                     volume_24h=1.5e9, ret_slow=95.0, ret_fast=80.0, vol_30d=60.0,
                     max_dd_90d=-20.0, dist_high_90d=-3.0, dist_high_stop=-3.0,
                     long_average=2000.0, sample_days=300),
        AssetMetrics(id="solana", symbol="SOL", name="Solana", price=150.0,
                     volume_24h=9e8, ret_slow=10.0, ret_fast=8.0, vol_30d=80.0,
                     max_dd_90d=-25.0, dist_high_90d=-10.0, dist_high_stop=-10.0,
                     long_average=140.0, sample_days=300),
        AssetMetrics(id="monero", symbol="XMR", name="Monero", price=100.0,
                     volume_24h=8e8, ret_slow=-20.0, ret_fast=-15.0, vol_30d=55.0,
                     max_dd_90d=-40.0, dist_high_90d=-50.0, dist_high_stop=-50.0,
                     long_average=120.0, sample_days=300),
        ]
    held = Position(product_id=1, coingecko_id="monero", symbol="XMR",
                    units=100.0, cost_basis_eur=2000.0)
    refuge = AssetMetrics(id="usd-coin", symbol="USDC", name="USDC",
                          price=1.0, volume_24h=5e9)

    return run_scan(
        rows=rows,
        positions=[held],
        rules=rules,
        history={1: [PriorScan("ethereum", True, True)] * 5},
        profit_already_taken=set(),
        refuge=refuge,
        )


class TestGateFields:
    """Reading one barrier, whichever shape it arrives in."""

    def test_a_dataclass_gate_is_read(self):
        gate = Gate("ecart_de_score", True, 2.05, 1.5, "écart-type")
        assert signal_widgets.gate_fields(gate) == {
            "name": "ecart_de_score",
            "passed": True,
            "value": 2.05,
            "threshold": 1.5,
            "unit": "écart-type",
            }

    def test_a_serialised_gate_reads_identically(self):
        """`pass` in the dict, `passed` on the dataclass — same answer."""
        gate = Gate("persistance", False, 1, 3, "scans consécutifs")
        assert signal_widgets.gate_fields(gate) == signal_widgets.gate_fields(gate.as_dict())

    def test_a_failing_gate_stays_failing_through_both_shapes(self):
        """A barrier that blocks must never render as passed."""
        gate = Gate("liquidite_candidat", False, 1_000_000, 275_000_000, "volume 24h")
        assert signal_widgets.gate_fields(gate)["passed"] is False
        assert signal_widgets.gate_fields(gate.as_dict())["passed"] is False

    def test_a_missing_verdict_is_read_as_a_failure(self):
        """Absent means not established, and not established is not a pass."""
        assert signal_widgets.gate_fields({"name": "x"})["passed"] is False


class TestRenderGates:
    """The function that crashed."""

    def test_engine_dataclasses_render(self, fake_st, scan_result):
        """The exact call the page makes, with the exact objects it holds."""
        outcome = scan_result.positions[0]
        assert outcome.rotation.gates, "le montage doit produire des barrières"

        signal_widgets.render_gates(outcome.rotation.gates)

        frame = fake_st.rendered_frames[0]
        assert len(frame) == len(outcome.rotation.gates)

    def test_serialised_gates_render_the_same(self, fake_st, scan_result):
        """A scan read back from the database must render like a live one."""
        gates = scan_result.positions[0].rotation.gates

        signal_widgets.render_gates(gates)
        signal_widgets.render_gates([g.as_dict() for g in gates])

        live, stored = fake_st.rendered_frames
        assert live.equals(stored)

    def test_gates_survive_a_round_trip_through_json(self, fake_st, scan_result):
        """Stored detail is JSON, so that is the shape the history page holds."""
        detail = json.loads(json.dumps(
            scan_result.positions[0].as_dict(), default=str))

        signal_widgets.render_gates(detail["rotation"]["gates"])

        assert fake_st.rendered_frames

    def test_every_mechanism_of_a_real_scan_renders(self, fake_st, scan_result):
        """The page draws four mechanisms per position; none may raise."""
        outcome = scan_result.positions[0]
        for mechanism in (outcome.rotation, outcome.trailing_stop,
                          outcome.profit_taking, outcome.temporisation):
            signal_widgets.render_gates(mechanism.gates)

        assert fake_st.rendered_frames

    def test_no_gates_draws_nothing(self, fake_st):
        signal_widgets.render_gates([])
        assert not fake_st.calls

    def test_a_caption_is_drawn_above_the_table(self, fake_st):
        signal_widgets.render_gates([Gate("persistance", True, 3, 3, "scans")], "titre")
        assert ("caption", "titre") in fake_st.calls


class TestRenderRegime:
    """The market-state reading, always handed as a dict."""

    def test_a_live_reading_renders(self, fake_st, scan_result):
        signal_widgets.render_regime(scan_result.regime.as_dict())
        assert len(fake_st.metrics) == 3

    def test_a_reading_round_tripped_through_json_renders(self, fake_st, scan_result):
        stored = json.loads(json.dumps(scan_result.regime.as_dict(), default=str))
        signal_widgets.render_regime(stored)
        assert len(fake_st.metrics) == 3

    def test_an_empty_reading_does_not_raise(self, fake_st):
        """A scan stored before the regime existed leaves an empty blob."""
        signal_widgets.render_regime({})
        assert len(fake_st.metrics) == 3


class TestRenderPlan:
    """The swap parameters, produced as a dict by the engine."""

    def test_a_real_plan_renders(self, fake_st, scan_result):
        outcome = scan_result.positions[0]
        assert outcome.plan, "le montage doit produire un plan"

        signal_widgets.render_plan(outcome.plan, "EUR")

        labels = [label for label, _ in fake_st.metrics]
        assert "signal.plan_from" in labels
        assert "signal.plan_min_units" in labels

    def test_a_plan_round_tripped_through_json_renders(self, fake_st, scan_result):
        stored = json.loads(json.dumps(scan_result.positions[0].plan, default=str))
        signal_widgets.render_plan(stored, "EUR")
        assert fake_st.metrics

    def test_no_plan_draws_nothing(self, fake_st):
        signal_widgets.render_plan(None, "EUR")
        assert not fake_st.calls


class TestFormatting:
    """Figures are shown without inventing precision they do not have."""

    def test_an_unknown_figure_is_a_dash(self):
        assert signal_widgets._fmt(None) == "—"

    def test_trailing_zeros_are_trimmed_without_eating_the_number(self):
        """`rstrip('0')` on '100.00' must stop at the dot, not return '1'."""
        assert signal_widgets._fmt(100.0) == "100"
        assert signal_widgets._fmt(1000.0) == "1 000"
        assert signal_widgets._fmt(0.0) == "0"

    def test_a_decimal_keeps_its_significant_digits(self):
        assert signal_widgets._fmt(2.05) == "2.05"
        assert signal_widgets._fmt(-12.5) == "-12.5"

    def test_large_volumes_are_shown_in_millions(self):
        assert signal_widgets._fmt(275_000_000) == "275 M"

    def test_a_regime_state_passes_through_as_text(self):
        assert signal_widgets._fmt("MIXTE") == "MIXTE"


class TestBadges:
    """Labels for a verdict and for the provenance of a figure."""

    def test_every_verdict_has_a_badge(self, monkeypatch):
        monkeypatch.setattr(signal_widgets, "t", lambda key: key)
        for verdict in SignalVerdict:
            badge = signal_widgets.verdict_badge(verdict.value)
            assert verdict.value.lower() in badge

    def test_an_unknown_provenance_falls_back_rather_than_raising(self, monkeypatch):
        monkeypatch.setattr(signal_widgets, "t", lambda key: key)
        assert signal_widgets.source_label("something_else") == "signal.source_none"
