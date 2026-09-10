"""The table of what will be arbitrated, made correctable in place.

The figures the engine reasons on are all derived, and every derivation has a
way of being right about its source and wrong about reality. This table is
where that shows up — so it is also where it should be fixable, rather than
sending the reader off to another page to correct a number they are looking at.

Two columns per figure, deliberately. The derived value stays visible and
read-only next to its provenance; the correction is a separate, empty column.
Editing a single column showing the derived value would mean that saving an
untouched row silently freezes today's automatic figure as a permanent
override — the opposite of what the reader intended by not touching it.

An empty correction cell means "follow the automatic source". That is the only
way to say it, and it is also how a correction is undone.
"""
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

import pandas as pd
import streamlit as st

from finance_tracker.i18n import t
from finance_tracker.services.crypto.overrides import (
    OverrideError,
    divergence,
    resolve_cost,
    set_overrides,
    set_reserve_and_arbitration,
    )
from .signal_widgets import source_label


def _num(value: Any) -> Optional[Decimal]:
    """Read a cell from the editor as a Decimal, or None when it is empty.

    A cleared numeric cell arrives as NaN, not as an empty string, and NaN is
    the signal that the user wants the automatic source back.
    """
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip().replace(",", ".").replace(" ", "").replace(" ", "")
    if not text or text.lower() == "nan":
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        raise OverrideError(t("editor.unreadable").format(value=value)) from None


def _fmt_units(value: Optional[float]) -> str:
    """Units as a figure a human reads, without inventing precision."""
    if value is None:
        return "—"
    return f"{value:,.8f}".rstrip("0").rstrip(".").replace(",", " ") or "0"


def _fmt_eur(value: Optional[float]) -> str:
    if value is None:
        return "—"
    return f"{value:,.2f} €".replace(",", " ")


def _auto_cell(shown: str, source: str) -> str:
    """A derived figure with its provenance, in one column instead of two."""
    return f"{shown} · {source_label(source)}"


def build_frame(resolved: list) -> pd.DataFrame:
    """Lay out one row per position: what is derived, and what is corrected."""
    return pd.DataFrame([{
        t("editor.col_asset"): r.position.symbol,
        t("editor.col_units_auto"): _auto_cell(
            _fmt_units(r.position.units), r.sources.units_from),
        t("editor.col_units_fix"): (
            float(r.asset.manual_units) if r.asset.manual_units is not None else None
            ),
        t("editor.col_cost_auto"): _auto_cell(
            _fmt_eur(r.position.cost_basis_eur), r.sources.cost_basis_from),
        t("editor.col_cost_fix"): (
            float(r.asset.manual_cost_basis_eur)
            if r.asset.manual_cost_basis_eur is not None else None
            ),
        t("editor.col_reserve"): float(r.asset.gas_reserve_eur or 0),
        t("editor.col_arbitrated"): bool(r.asset.arbitrated),
        } for r in resolved])


def _column_config(cost_mode: str) -> dict:
    """Which columns are text, which are numbers, and which may be edited."""
    cost_label = (
        t("editor.col_cost_fix_unit") if cost_mode == "unit"
        else t("editor.col_cost_fix_total")
        )
    return {
        t("editor.col_asset"): st.column_config.TextColumn(
            t("editor.col_asset"), disabled=True),
        t("editor.col_units_auto"): st.column_config.TextColumn(
            t("editor.col_units_auto"), disabled=True,
            help=t("editor.col_units_auto_help")),
        t("editor.col_units_fix"): st.column_config.NumberColumn(
            t("editor.col_units_fix"), min_value=0.0, format="%.8f",
            help=t("editor.col_units_fix_help")),
        t("editor.col_cost_auto"): st.column_config.TextColumn(
            t("editor.col_cost_auto"), disabled=True,
            help=t("editor.col_cost_auto_help")),
        t("editor.col_cost_fix"): st.column_config.NumberColumn(
            cost_label, min_value=0.0, format="%.2f",
            help=t("editor.col_cost_fix_help")),
        t("editor.col_reserve"): st.column_config.NumberColumn(
            t("editor.col_reserve"), min_value=0.0, format="%.2f",
            help=t("editor.col_reserve_help")),
        t("editor.col_arbitrated"): st.column_config.CheckboxColumn(
            t("editor.col_arbitrated"), help=t("editor.col_arbitrated_help")),
        }


def apply_edits(session, resolved: list, edited: pd.DataFrame, cost_mode: str) -> int:
    """Write back whatever the table now says. Returns how many lines changed.

    Rows keep the order they were drawn in, so each edited row is matched to
    the position it came from by position rather than by a label the user can
    change.

    Raises
    ------
    OverrideError
        On a figure that cannot be read or would describe an impossible
        position. Nothing is written for that line; earlier lines keep their
        writes, which is why the caller reports the count.
    """
    rows = edited.to_dict(orient="records")
    changed = 0

    for entry, row in zip(resolved, rows):
        asset = entry.asset

        units = _num(row.get(t("editor.col_units_fix")))
        cost_raw = _num(row.get(t("editor.col_cost_fix")))
        reserve = _num(row.get(t("editor.col_reserve"))) or Decimal("0")
        arbitrated = bool(row.get(t("editor.col_arbitrated"), True))

        # A per-unit correction needs a quantity: the corrected one when there
        # is one, the derived one otherwise.
        effective_units = units
        if effective_units is None and entry.position.units is not None:
            effective_units = Decimal(str(entry.position.units))

        cost = resolve_cost(
            effective_units,
            unit_cost_eur=cost_raw if cost_mode == "unit" else None,
            total_cost_eur=cost_raw if cost_mode == "total" else None,
            )

        before = (asset.manual_units, asset.manual_cost_basis_eur,
                  asset.gas_reserve_eur, asset.arbitrated)

        set_overrides(
            session, asset,
            units=units, clear_units=units is None,
            cost_basis_eur=cost, clear_cost_basis=cost is None,
            )
        set_reserve_and_arbitration(
            session, asset, gas_reserve_eur=reserve, arbitrated=arbitrated)

        after = (asset.manual_units, asset.manual_cost_basis_eur,
                 asset.gas_reserve_eur, asset.arbitrated)
        if before != after:
            changed += 1

    return changed


def render_divergences(session, resolved: list) -> None:
    """Warn where a corrected quantity contradicts the synced balance.

    Not an error — the user may well be right, and that is the point of the
    correction. But a silent contradiction between the displayed figure and
    what the chain reports is how a portfolio drifts unnoticed.
    """
    for entry in resolved:
        gap = divergence(session, entry.asset, entry.position.symbol)
        if gap is None:
            continue
        st.warning(t("editor.divergence").format(
            symbol=gap.symbol,
            manual=_fmt_units(float(gap.manual_units)),
            chain=_fmt_units(float(gap.chain_units)),
            ))


def render_editor(session, resolved: list) -> bool:
    """Draw the correctable table. Returns whether anything was written."""
    st.caption(t("editor.help"))

    cost_mode = st.radio(
        t("editor.cost_mode"),
        options=("total", "unit"),
        format_func=lambda m: t(f"editor.cost_mode_{m}"),
        horizontal=True,
        key="position_cost_mode",
        )

    edited = st.data_editor(
        build_frame(resolved),
        key="position_editor",
        hide_index=True,
        width="stretch",
        num_rows="fixed",
        column_config=_column_config(cost_mode),
        )

    col_apply, col_reset = st.columns([2, 1])
    applied = False

    with col_apply:
        if st.button(t("editor.apply"), type="secondary", width="stretch"):
            try:
                count = apply_edits(session, resolved, edited, cost_mode)
            except OverrideError as exc:
                st.error(str(exc))
            else:
                applied = True
                if count:
                    st.success(t("editor.applied").format(n=count))
                else:
                    st.info(t("editor.nothing_changed"))

    with col_reset:
        if st.button(t("editor.reset_all"), width="stretch"):
            for entry in resolved:
                set_overrides(
                    session, entry.asset, clear_units=True, clear_cost_basis=True)
            applied = True
            st.success(t("editor.reset_done"))

    render_divergences(session, resolved)
    return applied
