"""Rendering pieces shared by the crypto pages.

A verdict is only worth acting on if its reasoning is visible, so gates are
rendered with the measured value beside the threshold rather than as a bare
pass/fail. The same goes for provenance: a cost basis reconstructed from a
chain and one typed from a receipt are shown differently on purpose.
"""
from typing import Any, Iterable, Optional

import pandas as pd
import streamlit as st

from finance_tracker.domain.enums import MarketRegime, SignalVerdict
from finance_tracker.i18n import t

# Colour and icon per verdict. Held is deliberately unremarkable: doing nothing
# is the most common outcome and should not look like a failure.
VERDICT_STYLE: dict[str, tuple[str, str]] = {
    SignalVerdict.CONSERVER.value: ("⚪", "#6c757d"),
    SignalVerdict.TEMPORISER.value: ("🟡", "#c9a227"),
    SignalVerdict.ROTATION.value: ("🔵", "#0d6efd"),
    SignalVerdict.ALLEGER.value: ("🟢", "#198754"),
    SignalVerdict.SORTIE_STOP.value: ("🔴", "#dc3545"),
    }

REGIME_STYLE: dict[str, str] = {
    MarketRegime.BULL.value: "🟢",
    MarketRegime.MIXTE.value: "🟡",
    MarketRegime.BEAR.value: "🔴",
    MarketRegime.INCONNU.value: "⚪",
    }

# How a derived figure is labelled, so an estimate never passes for a fact.
SOURCE_LABELS: dict[str, str] = {
    "wallet": "signal.source_wallet",
    "transactions": "signal.source_transactions",
    "manual": "signal.source_manual",
    "onchain": "signal.source_onchain",
    "valuation": "signal.source_valuation",
    "none": "signal.source_none",
    }


def verdict_badge(verdict: str) -> str:
    """Return the icon and label for a verdict."""
    icon, _ = VERDICT_STYLE.get(verdict, ("⚪", "#6c757d"))
    return f"{icon} {t(f'verdict.{verdict.lower()}')}"


def source_label(source: str) -> str:
    """Return the human label for a provenance key."""
    return t(SOURCE_LABELS.get(source, "signal.source_none"))


def gate_fields(gate: Any) -> dict:
    """Read one barrier, whichever shape it arrives in.

    A live scan hands out `Gate` dataclasses straight from the engine; a scan
    read back from the database hands out the same barriers serialised to
    dicts. This widget sits on the boundary between the two, so it accepts
    either rather than making every caller remember which one it is holding —
    which is exactly the mistake that made this function crash on a real scan.

    Note the key: a serialised gate spells it `pass`, the dataclass spells it
    `passed`. Both are read, and an absent one is treated as a failure, never
    as a pass.

    Parameters
    ----------
    gate : Gate or dict
        One barrier.

    Returns
    -------
    dict
        Normalised fields: name, passed, value, threshold, unit.
    """
    if isinstance(gate, dict):
        return {
            "name": gate.get("name", ""),
            "passed": bool(gate.get("pass", gate.get("passed", False))),
            "value": gate.get("value"),
            "threshold": gate.get("threshold"),
            "unit": gate.get("unit", "") or "",
            }
    return {
        "name": getattr(gate, "name", ""),
        "passed": bool(getattr(gate, "passed", False)),
        "value": getattr(gate, "value", None),
        "threshold": getattr(gate, "threshold", None),
        "unit": getattr(gate, "unit", "") or "",
        }


def render_gates(gates: Iterable[Any], caption: Optional[str] = None) -> None:
    """Render a mechanism's barriers as a table.

    Parameters
    ----------
    gates : Iterable[Gate or dict]
        The barriers, as engine dataclasses or as their serialised form.
    caption : str, optional
        Line shown above the table.
    """
    rows = [gate_fields(g) for g in gates or []]
    if not rows:
        return
    if caption:
        st.caption(caption)

    frame = pd.DataFrame([{
        t("signal.gate"): t(f"gate.{row['name']}"),
        t("signal.gate_status"): "✅" if row["passed"] else "❌",
        t("signal.gate_value"): _fmt(row["value"]),
        t("signal.gate_threshold"): _fmt(row["threshold"]),
        t("signal.gate_unit"): row["unit"],
        } for row in rows])

    st.dataframe(frame, hide_index=True, width="stretch")


def _fmt(value) -> str:
    """Format a gate figure without inventing precision it does not have."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "oui" if value else "non"
    if isinstance(value, (int, float)):
        if abs(value) >= 1_000_000:
            return f"{value / 1e6:,.0f} M".replace(",", " ")
        return f"{value:,.2f}".replace(",", " ").rstrip("0").rstrip(".")
    return str(value)


def render_regime(regime: dict) -> None:
    """Render the market-regime reading as three metrics."""
    state = regime.get("state", MarketRegime.INCONNU.value)
    icon = REGIME_STYLE.get(state, "⚪")

    col1, col2, col3 = st.columns(3)
    col1.metric(t("signal.regime"), f"{icon} {state}")

    above = regime.get("above_average")
    col2.metric(
        t("signal.regime_reference").format(
            symbol=regime.get("reference_symbol") or "—",
            days=regime.get("long_average_days") or 0,
            ),
        "—" if above is None else ("✅" if above else "❌"),
        )

    breadth = regime.get("breadth_pct")
    col3.metric(
        t("signal.regime_breadth"),
        "—" if breadth is None else f"{breadth:.0f} %",
        delta=None if breadth is None else f"seuil {regime.get('min_breadth_pct', 0):.0f} %",
        delta_color="off",
        )

    if regime.get("reason"):
        st.caption(regime["reason"])


def render_plan(plan: dict, currency: str = "EUR") -> None:
    """Render a swap plan as parameters to carry out by hand.

    The minimum acceptable units matter more than the reference figure: they
    are the line below which the quote no longer matches what the scan
    measured, and therefore the point of calling the swap off.
    """
    if not plan:
        return

    st.markdown(f"**{t('signal.plan_title')}**")
    col1, col2, col3 = st.columns(3)
    col1.metric(t("signal.plan_from"), plan.get("from_symbol", "—"))
    col2.metric(t("signal.plan_to"), plan.get("to_symbol", "—"))
    col3.metric(t("signal.plan_amount"), f"{plan.get('amount', 0):,.2f} {currency}".replace(",", " "))

    col4, col5 = st.columns(2)
    units = plan.get("units_at_reference")
    floor = plan.get("min_accept_units")
    col4.metric(
        t("signal.plan_units"),
        "—" if units is None else f"{units:,.8f}".rstrip("0").rstrip("."),
        )
    col5.metric(
        t("signal.plan_min_units"),
        "—" if floor is None else f"{floor:,.8f}".rstrip("0").rstrip("."),
        help=t("signal.plan_min_units_help").format(pct=plan.get("max_acceptable_loss_pct", 0)),
        )

    quotes = plan.get("quotes_to_compare") or []
    if quotes:
        st.markdown(f"*{t('signal.plan_quotes')}*")
        for quote in quotes:
            st.markdown(f"- {quote}")

    if plan.get("note"):
        st.info(plan["note"])
