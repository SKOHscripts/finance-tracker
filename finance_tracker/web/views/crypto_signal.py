"""The crypto rotation signal page.

Shows what the engine concluded and, above all, why. A verdict on its own is
worth very little — the value is in the barriers underneath it, each with the
figure that made it pass or fail, so the reader can disagree with a specific
number rather than with a black box.
"""
import json
from datetime import datetime

import pandas as pd
import streamlit as st
from sqlmodel import Session

from finance_tracker.domain.enums import SignalVerdict
from finance_tracker.i18n import t
from finance_tracker.services.crypto.coingecko_client import CoinGeckoClient
from finance_tracker.services.crypto.portfolio import load_positions
from finance_tracker.services.crypto.rules import RulesError, load_rules
from finance_tracker.services.crypto.settings import SettingsError, effective_rules
from finance_tracker.services.crypto.scan_service import (
    ScanError,
    latest_run,
    run_history,
    run_signal_scan,
    verdicts_for_run,
    )
from finance_tracker.services.wallets.registry import COINGECKO, get_credential
from finance_tracker.web.ui.disclaimer import render_disclaimer, render_disclaimer_expander
from finance_tracker.web.ui.position_editor import render_editor
from finance_tracker.web.ui.settings_widgets import render_settings
from finance_tracker.web.ui.signal_widgets import (
    render_gates,
    render_plan,
    render_regime,
    source_label,
    verdict_badge,
    )


def _fmt_eur(value) -> str:
    """Format an amount for display, blank-safe."""
    if value is None:
        return "—"
    return f"{float(value):,.2f} €".replace(",", " ")


def _fmt_pct(value) -> str:
    """Format a percentage for display, blank-safe."""
    if value is None:
        return "—"
    return f"{float(value):+.1f} %"


def _render_positions_overview(session: Session) -> bool:
    """Show what the engine will arbitrate. Returns whether anything will be.

    Rendered before any scan so the user can check the inputs — units, cost
    basis, where each came from — rather than discovering a wrong figure after
    it has already produced a verdict.
    """
    resolved = load_positions(session)

    if not resolved:
        st.info(t("signal.no_positions"))
        return False

    frame = pd.DataFrame([{
        t("signal.col_asset"): r.position.symbol,
        t("signal.col_units"): (
            "—" if r.position.units is None
            else f"{r.position.units:,.8f}".rstrip("0").rstrip(".")
            ),
        t("signal.col_units_source"): source_label(r.sources.units_from),
        t("signal.col_cost_basis"): _fmt_eur(r.position.cost_basis_eur),
        t("signal.col_cost_source"): source_label(r.sources.cost_basis_from),
        t("signal.col_reserve"): _fmt_eur(r.position.gas_reserve_eur),
        t("signal.col_arbitrated"): "✅" if r.position.arbitrated else "⏸️",
        } for r in resolved])

    st.dataframe(frame, hide_index=True, width="stretch")

    notes = [r.sources.note for r in resolved if r.sources.note]
    for note in dict.fromkeys(notes):
        st.caption(f"ℹ️ {note}")

    missing = [r.position.symbol for r in resolved if r.position.cost_basis_eur is None]
    if missing:
        st.caption(t("signal.missing_cost_basis").format(assets=", ".join(missing)))

    # Correcting a figure belongs where the figure is wrong, not on another page.
    with st.expander(f"✏️ {t('editor.title')}", expanded=False):
        if render_editor(session, resolved):
            st.rerun()

    return True


def _render_outcome(outcome, currency: str) -> None:
    """Render one position's verdict, its mechanisms and its plan."""
    header = f"{verdict_badge(outcome.verdict.value)} — {outcome.position.symbol}"
    expanded = outcome.verdict is not SignalVerdict.CONSERVER

    with st.expander(header, expanded=expanded):
        if not outcome.arbitrated:
            st.info(outcome.reason or t("signal.not_arbitrated"))
            return

        col1, col2, col3 = st.columns(3)
        col1.metric(t("signal.col_value"), _fmt_eur(outcome.current_value))
        col2.metric(t("signal.col_gain"), _fmt_pct(outcome.gain_pct))
        col3.metric(
            t("signal.col_cost_of_move"),
            "—" if outcome.round_trip_cost_pct is None
            else f"{outcome.round_trip_cost_pct:.2f} %",
            help=t("signal.cost_of_move_help"),
            )

        if outcome.plan:
            render_plan(outcome.plan, currency)
            render_disclaimer(compact=True)
            st.markdown("---")

        mechanisms = [
            ("signal.mech_rotation", outcome.rotation),
            ("signal.mech_stop", outcome.trailing_stop),
            ("signal.mech_profit", outcome.profit_taking),
            ("signal.mech_temporisation", outcome.temporisation),
            ]

        tabs = st.tabs([t(key) for key, _ in mechanisms])
        for tab, (_, mechanism) in zip(tabs, mechanisms):
            with tab:
                if not mechanism.applicable:
                    st.caption(mechanism.reason or t("signal.not_evaluated"))
                    continue
                render_gates(mechanism.gates)


def _render_result(result, currency: str) -> None:
    """Render a completed scan."""
    st.subheader(t("signal.section_market"))
    render_regime(result.regime.as_dict())

    if result.candidate:
        st.markdown(
            t("signal.candidate_line").format(
                symbol=result.candidate.symbol,
                name=result.candidate.name or result.candidate.id,
                score=f"{result.candidate.score:.3f}",
                )
            )
    else:
        st.caption(t("signal.no_candidate"))

    if result.discarded_candidates:
        with st.expander(t("signal.discarded_title"), expanded=False):
            st.caption(t("signal.discarded_help"))
            for row in result.discarded_candidates:
                st.markdown(f"- **{row['symbol']}** — {', '.join(row['reasons'])}")

    if result.insufficient_history:
        st.caption(
            t("signal.insufficient_history").format(
                assets=", ".join(result.insufficient_history))
            )

    st.markdown("---")
    st.subheader(t("signal.section_positions"))
    for outcome in result.positions:
        _render_outcome(outcome, currency)

    with st.expander(t("signal.ranking_title"), expanded=False):
        st.dataframe(
            pd.DataFrame([{
                t("signal.col_asset"): r.symbol,
                t("signal.col_score"): round(r.score, 3),
                t("signal.col_mom_slow"): _fmt_pct(r.ret_slow),
                t("signal.col_mom_fast"): _fmt_pct(r.ret_fast),
                t("signal.col_vol"): "—" if r.vol_30d is None else f"{r.vol_30d:.0f} %",
                t("signal.col_dd"): _fmt_pct(r.max_dd_90d),
                } for r in result.ranking]),
            hide_index=True,
            width="stretch",
            )


def _render_stored_run(session: Session, run) -> None:
    """Render the last recorded scan, read back from the database."""
    st.caption(t("signal.last_scan").format(
        date=run.scan_date.strftime("%d/%m/%Y %H:%M"),
        verdict=t(f"verdict.{run.verdict.value.lower()}"),
        ))

    try:
        render_regime(json.loads(run.regime_json or "{}"))
    except json.JSONDecodeError:
        pass

    verdicts = verdicts_for_run(session, run.id)
    if not verdicts:
        return

    st.dataframe(
        pd.DataFrame([{
            t("signal.col_asset"): v.symbol,
            t("signal.col_verdict"): verdict_badge(v.verdict.value),
            t("signal.col_value"): _fmt_eur(v.notional_eur),
            t("signal.col_gain"): _fmt_pct(v.unrealised_gain_pct),
            t("signal.col_streak"): v.streak_weeks,
            } for v in verdicts]),
        hide_index=True,
        width="stretch",
        )

    for verdict in verdicts:
        if verdict.verdict is SignalVerdict.CONSERVER:
            continue
        try:
            detail = json.loads(verdict.detail_json or "{}")
        except json.JSONDecodeError:
            continue
        plan = detail.get("plan")
        if plan:
            with st.expander(f"{verdict_badge(verdict.verdict.value)} — {verdict.symbol}"):
                render_plan(plan, run.quote_currency)
                render_disclaimer(compact=True)


def _render_history(session: Session) -> None:
    """Render past scans, so a streak can be read rather than trusted."""
    runs = run_history(session)
    if len(runs) < 2:
        return

    with st.expander(t("signal.history_title"), expanded=False):
        st.caption(t("signal.history_help"))
        st.dataframe(
            pd.DataFrame([{
                t("signal.col_date"): r.scan_date.strftime("%d/%m/%Y"),
                t("signal.col_verdict"): verdict_badge(r.verdict.value),
                t("signal.regime"): r.regime.value,
                t("signal.col_candidate"): r.candidate_symbol or "—",
                } for r in runs]),
            hide_index=True,
            width="stretch",
            )


def render(session: Session) -> None:
    """Render the crypto signal page."""
    st.title(t("signal.title"))
    st.caption(t("signal.caption"))

    render_disclaimer()

    try:
        rules = effective_rules(session)
    except RulesError as exc:
        st.error(t("signal.rules_error").format(e=exc))
        return
    except SettingsError as exc:
        # A stored threshold has become incoherent — say so and fall back to
        # the shipped values, so the panel that fixes it can still be drawn.
        st.error(t("signal.settings_error").format(e=exc))
        try:
            rules = load_rules()
        except RulesError as inner:
            st.error(t("signal.rules_error").format(e=inner))
            return

    with st.expander(f"⚙️ {t('settings.title')}", expanded=False):
        if render_settings(session):
            st.rerun()

    st.subheader(t("signal.section_inputs"))
    st.caption(t("signal.inputs_help"))
    has_positions = _render_positions_overview(session)

    st.markdown("---")

    col_run, col_opts = st.columns([1, 2])
    with col_run:
        launch = st.button(
            t("signal.run_btn"),
            type="primary",
            width="stretch",
            disabled=not has_positions,
            )
    with col_opts:
        persist = st.checkbox(t("signal.persist_opt"), value=True, help=t("signal.persist_help"))

    if launch:
        credential = get_credential(session, COINGECKO)
        client = CoinGeckoClient(
            api_key=credential.api_key,
            base_url=credential.base_url or None,
            request_delay=rules.universe.request_delay_seconds,
            )

        progress = st.progress(0.0, text=t("signal.scanning"))

        def on_progress(step) -> None:
            ratio = (step.current / step.total) if step.total else 0.0
            progress.progress(min(ratio, 1.0), text=step.step)

        try:
            result, _run = run_signal_scan(
                session, rules=rules, client=client,
                persist=persist, on_progress=on_progress,
                )
        except ScanError as exc:
            progress.empty()
            st.error(t("signal.scan_error").format(e=exc))
            return
        finally:
            st.session_state.signal_last_attempt = datetime.utcnow()

        progress.empty()
        st.success(t("signal.scan_done").format(
            verdict=t(f"verdict.{result.verdict.value.lower()}")))
        _render_result(result, rules.quote_currency)
        render_disclaimer_expander()
        return

    run = latest_run(session)
    if run is not None:
        st.subheader(t("signal.section_last"))
        _render_stored_run(session, run)
        _render_history(session)
    elif has_positions:
        st.info(t("signal.never_scanned"))

    render_disclaimer_expander()
