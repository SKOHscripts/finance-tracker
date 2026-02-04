"""
simulation.py — UI Streamlit (V3) avec st.form + persistance des résultats + export PDF.
"""

from __future__ import annotations

from datetime import date, datetime

import altair as alt
import pandas as pd
import streamlit as st
from sqlmodel import Session

from finance_tracker.repositories.sqlmodel_repo import SQLModelProductRepository
from finance_tracker.services.dashboard_service import DashboardService
from finance_tracker.services.simulation_pdf_service import SimulationPDFService
from finance_tracker.services.simulation_service import (
    BudgetConfig,
    FCPIConfig,
    IncomeConfig,
    PERCapConfig,
    ProductSimConfig,
    SCPIConfig,
    SimulationConfig,
    SimulationService,
    TaxBracket,
    TaxConfig,
)
from finance_tracker.web.ui.formatters import to_decimal


def eur(x: float):
    return to_decimal(x)


def pct(x: float):
    return to_decimal(x / 100.0)


def _init_state():
    st.session_state.setdefault("sim_df_period", None)
    st.session_state.setdefault("sim_df_long", None)
    st.session_state.setdefault("sim_summary", None)
    st.session_state.setdefault("sim_selected_metrics", ["value_eur", "value_real_eur"])
    st.session_state.setdefault("sim_products_params", [])  # pour le PDF


def _fmt_eur(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")


def _fmt_pct(x: float) -> str:
    return f"{x:.2f}"


def _serialize_products_for_pdf(sim_products: list[ProductSimConfig]) -> list[dict]:
    out: list[dict] = []

    for p in sim_products:
        scpi_text = "-"

        if p.scpi is not None:
            scpi_text = (
                f"prix_part={float(p.scpi.part_price):.0f}€, "
                f"parts/an={int(p.scpi.parts_per_year)}, "
                f"dist/an={float(p.scpi.distribution_annual) * 100:.2f}%, "
                f"revalo/an={float(p.scpi.revaluation_annual) * 100:.2f}%, "
                f"freq={p.scpi.dividend_frequency}, "
                f"vers_cash={bool(p.scpi.dividends_to_cash)}"
            )

        fcpi_text = "-"

        if p.fcpi is not None:
            fcpi_text = (
                f"reduc={float(p.fcpi.tax_reduction_rate) * 100:.2f}%, "
                f"plafond={float(p.fcpi.annual_eligible_cap):.0f}€, "
                f"blocage={int(p.fcpi.holding_years)}a, "
                f"sortie={p.fcpi.exit_mode}"
            )

        out.append(
            {
                "name": p.name,
                "kind": p.kind,
                "priority": int(p.priority),
                "annual_return_pct": _fmt_pct(float(p.annual_return) * 100.0),
                "contrib_fixed_eur": _fmt_eur(float(p.contribution_per_period)),
                "contrib_pct_income": _fmt_pct(float(p.contribution_pct_income) * 100.0),
                "initial_value_eur": _fmt_eur(float(p.initial_value_eur)),
                "initial_invested_eur": (
                    f"{_fmt_eur(float(p.initial_invested_eur))}€" if p.initial_invested_eur is not None else "-"
                ),
                "scpi_text": scpi_text,
                "fcpi_text": fcpi_text,
            }
        )

    return out


def render(session: Session) -> None:
    _init_state()
    st.header("🧮 Simulation long terme")

    # Produits DB
    product_repo = SQLModelProductRepository(session)
    products_db = product_repo.get_all()
    product_names = [p.name for p in products_db]

    if not product_names:
        st.info("Ajoute au moins un produit dans '➕ Ajouter Produits' avant de simuler.")
        st.stop()

    # Defaults depuis la DB (dashboard)
    portfolio = DashboardService(session).build_portfolio()
    defaults_by_name = {
        p["name"]: {
            "initial_value": float(p.get("current_value_eur", 0) or 0),
            "initial_invested": float(p.get("net_contributions_eur", 0) or 0),
        }

        for p in portfolio.products
    }

    st.caption("Tous les paramètres sont regroupés dans un formulaire : rien n'est recalculé tant que tu ne soumets pas.")

    # ---------------------------
    # FORMULAIRE
    # ---------------------------
    with st.form(key="sim_form", clear_on_submit=False):
        st.subheader("Paramètres globaux")
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            years = st.number_input("Durée (années)", min_value=1, max_value=80, value=20, step=1)
            period = st.selectbox("Période", ["monthly", "quarterly", "yearly"], index=0)

        with c2:
            inflation_pct = st.number_input("Inflation annuelle (%)", 0.0, 20.0, 2.0, 0.1)

        with c3:
            income_start = st.number_input("Revenu brut annuel initial N (€)", 0.0, value=50000.0, step=1000.0)
            income_prev = st.number_input("Revenu brut annuel N-1 (€) (PER 10% N-1)", 0.0, value=50000.0, step=1000.0)

        with c4:
            income_growth_pct = st.number_input("Augmentation revenu/an (%)", 0.0, 20.0, 2.0, 0.1)

        c1, c2, c3 = st.columns(3)
        with c1:
            annual_living_costs = st.number_input("Dépenses annuelles (€)", 0.0, value=24000.0, step=500.0)
        with c2:
            emergency_target = st.number_input("Cible épargne de précaution (€)", 0.0, value=5000.0, step=500.0)
        with c3:
            initial_tax_due = st.number_input("Impôt dû N-1 à payer en année 1 (€)", 0.0, value=0.0, step=100.0)

        st.markdown("---")

        st.subheader("Fiscalité (barème progressif)")
        c1, c2 = st.columns(2)
        with c1:
            household_parts = st.number_input("Parts (quotient familial simplifié)", min_value=1.0, value=1.0, step=0.5)
        with c2:
            std_deduction_pct = st.number_input("Abattement forfaitaire (%)", 0.0, 30.0, 10.0, 0.5)

        default_brackets = [
            {"up_to": 11294, "rate_pct": 0.0},
            {"up_to": 28797, "rate_pct": 11.0},
            {"up_to": 82341, "rate_pct": 30.0},
            {"up_to": 177106, "rate_pct": 41.0},
            {"up_to": None, "rate_pct": 45.0},
        ]
        st.caption("Tranches annuelles; laisse `up_to` vide pour la dernière tranche.")
        df_brackets = st.data_editor(pd.DataFrame(default_brackets), width="stretch", num_rows="dynamic")

        brackets: list[TaxBracket] = []

        for _, r in df_brackets.iterrows():
            up_to = r.get("up_to", None)
            rate_pct = float(r.get("rate_pct", 0.0))
            up_to_val = None if pd.isna(up_to) else to_decimal(float(up_to))
            brackets.append(TaxBracket(up_to=up_to_val, rate=pct(rate_pct)))

        st.markdown("---")

        st.subheader("PER (plafond basé sur 10% du revenu N-1)")
        c1, c2, c3 = st.columns(3)
        with c1:
            per_rate_prev_income_pct = st.number_input("Plafond PER = % du revenu N-1", 0.0, 50.0, 10.0, 0.5)
        with c2:
            per_min = st.number_input("Plafond PER minimum (€/an)", 0.0, value=0.0, step=100.0)
        with c3:
            per_max = st.number_input("Plafond PER maximum (€/an, 0=illimité)", 0.0, value=0.0, step=500.0)

        st.markdown("---")

        st.subheader("Paramètres par produit (auto-remplis depuis la base)")

        default_returns_pct = {
            "Cash": 0.0,
            "Épargne": 2.0,
            "SCPI": 0.0,
            "Bitcoin": 6.0,
            "PER": 5.0,
            "FCPI": 4.0,
        }

        sim_products: list[ProductSimConfig] = []

        for name in product_names:
            defaults = defaults_by_name.get(name, {"initial_value": 0.0, "initial_invested": 0.0})

            with st.expander(f"⚙️ {name}", expanded=False):
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    kind = st.selectbox(
                        "Catégorie",
                        ["cash", "savings", "scpi", "per", "fcpi", "other"],
                        index=0 if name.lower() == "cash" else 5,
                        key=f"v3_kind_{name}",
                    )
                with c2:
                    initial_value = st.number_input(
                        "Valorisation initiale (€)",
                        min_value=0.0,
                        value=float(defaults["initial_value"]),
                        step=500.0,
                        key=f"v3_init_val_{name}",
                    )
                with c3:
                    initial_invested = st.number_input(
                        "Investi initial (€)",
                        min_value=0.0,
                        value=float(defaults["initial_invested"]),
                        step=500.0,
                        key=f"v3_init_inv_{name}",
                    )
                    use_initial_invested = st.checkbox(
                        "Utiliser 'Investi initial'",
                        value=True,
                        key=f"v3_use_init_inv_{name}",
                    )
                with c4:
                    priority = st.number_input(
                        "Priorité (1=prioritaire)",
                        min_value=1,
                        max_value=999,
                        value=50,
                        step=1,
                        key=f"v3_prio_{name}",
                    )

                annual_return_pct = st.number_input(
                    "Rendement annuel nominal (%) (capitalisation)",
                    min_value=-50.0,
                    max_value=50.0,
                    value=float(default_returns_pct.get(name, 3.0)),
                    step=0.1,
                    key=f"v3_ret_{name}",
                )

                contrib_fixed = st.number_input(
                    "Apport fixe par période (€) (hors SCPI parts/an)",
                    min_value=0.0,
                    value=0.0,
                    step=50.0,
                    key=f"v3_contrib_fixed_{name}",
                )
                contrib_pct_income = st.number_input(
                    "Apport = % du revenu par période (%) (hors SCPI parts/an)",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=0.5,
                    key=f"v3_contrib_pct_income_{name}",
                )

                # SCPI
                with st.expander("Paramètres SCPI (utilisé si catégorie = scpi)", expanded=False):
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        part_price = st.number_input(
                            "Prix part (€)", min_value=0.0, value=250.0, step=1.0, key=f"v3_scpi_part_{name}"
                        )
                    with c2:
                        parts_per_year = st.number_input(
                            "Parts achetées par an", min_value=0, value=0, step=1, key=f"v3_scpi_parts_year_{name}"
                        )
                    with c3:
                        distribution_pct = st.number_input(
                            "Taux distribution annuel (%)", 0.0, 20.0, 4.5, 0.1, key=f"v3_scpi_dist_{name}"
                        )
                    with c4:
                        revalo_pct = st.number_input(
                            "Revalo prix part/an (%)", -10.0, 20.0, 0.0, 0.1, key=f"v3_scpi_revalo_{name}"
                        )

                    c5, c6 = st.columns(2)
                    with c5:
                        dividend_frequency = st.selectbox(
                            "Fréquence de redistribution",
                            ["monthly", "quarterly", "semiannual", "yearly"],
                            index=1,
                            key=f"v3_scpi_freq_{name}",
                        )
                    with c6:
                        dividends_to_cash = st.checkbox(
                            "Redistributions versées en cash", value=True, key=f"v3_scpi_to_cash_{name}"
                        )

                    init_scpi_parts_value = st.number_input(
                        "Nombre de parts initial (optionnel, sinon dérivé de la valorisation initiale)",
                        min_value=0,
                        value=0,
                        step=1,
                        key=f"v3_scpi_init_parts_{name}",
                    )
                    use_init_parts = st.checkbox(
                        "Utiliser 'parts initial'", value=False, key=f"v3_scpi_use_init_parts_{name}"
                    )
                    init_scpi_parts = int(init_scpi_parts_value) if use_init_parts else None

                scpi_cfg = None

                if kind == "scpi":
                    scpi_cfg = SCPIConfig(
                        part_price=eur(part_price),
                        parts_per_year=int(parts_per_year),
                        distribution_annual=pct(distribution_pct),
                        dividends_to_cash=bool(dividends_to_cash),
                        revaluation_annual=pct(revalo_pct),
                        dividend_frequency=dividend_frequency,
                    )

                # FCPI
                with st.expander("Paramètres FCPI (utilisé si catégorie = fcpi)", expanded=False):
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        fcpi_tax_rate_pct = st.number_input(
                            "Taux réduction d'impôt (%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=18.0,
                            step=0.5,
                            key=f"v3_fcpi_tax_rate_{name}",
                        )
                    with c2:
                        fcpi_eligible_cap = st.number_input(
                            "Plafond annuel éligible (€)",
                            min_value=0.0,
                            value=12000.0,
                            step=500.0,
                            key=f"v3_fcpi_cap_{name}",
                        )
                    with c3:
                        fcpi_holding_years = st.number_input(
                            "Durée blocage (années)",
                            min_value=1,
                            max_value=30,
                            value=8,
                            step=1,
                            key=f"v3_fcpi_years_{name}",
                        )
                    with c4:
                        fcpi_exit_mode = st.selectbox(
                            "Sortie à échéance",
                            ["principal", "full_value"],
                            index=0,
                            key=f"v3_fcpi_exit_{name}",
                        )

                fcpi_cfg = None

                if kind == "fcpi":
                    fcpi_cfg = FCPIConfig(
                        tax_reduction_rate=pct(fcpi_tax_rate_pct),
                        annual_eligible_cap=eur(fcpi_eligible_cap),
                        holding_years=int(fcpi_holding_years),
                        exit_mode=fcpi_exit_mode,
                    )

                sim_products.append(
                    ProductSimConfig(
                        name=name,
                        kind=kind,
                        annual_return=pct(annual_return_pct),
                        contribution_per_period=eur(contrib_fixed),
                        contribution_pct_income=pct(contrib_pct_income),
                        initial_value_eur=eur(initial_value),
                        initial_invested_eur=(eur(initial_invested) if use_initial_invested else None),
                        scpi=scpi_cfg,
                        initial_scpi_parts=(init_scpi_parts if kind == "scpi" else None),
                        fcpi=fcpi_cfg,
                        priority=int(priority),
                    )
                )

        if not any(p.kind == "cash" for p in sim_products):
            st.error("Il faut définir au moins un produit en catégorie 'cash'.")
            st.stop()

        submitted = st.form_submit_button("▶️ Recalculer la simulation (V3)")

    # ---------------------------
    # CALCUL (uniquement au submit)
    # ---------------------------

    if submitted:
        cfg = SimulationConfig(
            start=date.today(),
            years=int(years),
            period=period,
            inflation_annual=pct(inflation_pct),
            income=IncomeConfig(
                gross_annual_start=eur(income_start),
                annual_growth=pct(income_growth_pct),
                gross_annual_previous=eur(income_prev),
            ),
            budget=BudgetConfig(
                annual_living_costs=eur(annual_living_costs),
                emergency_fund_target=eur(emergency_target),
                enforce_emergency_fund_first=True,
            ),
            tax=TaxConfig(
                brackets=brackets,
                household_parts=to_decimal(household_parts),
                standard_deduction_rate=pct(std_deduction_pct),
                initial_tax_due_annual=eur(initial_tax_due),
            ),
            per_cap=PERCapConfig(
                rate_of_income_prev_year=pct(per_rate_prev_income_pct),
                annual_min=eur(per_min),
                annual_max=None if per_max == 0 else eur(per_max),
            ),
        )

        result = SimulationService().run(cfg, sim_products)
        rows = result.rows
        last = rows[-1]

        df_period = pd.DataFrame(
            [
                {
                    "period": r.period_index + 1,
                    "year": r.year_number,
                    "step_in_year": r.step_in_year + 1,
                    "income_period_eur": float(r.income_period),
                    "living_costs_period_eur": float(r.living_costs_period),
                    "tax_paid_period_eur": float(r.tax_paid_period),
                    "tax_due_for_year_eur": float(r.tax_due_for_year) if r.tax_due_for_year is not None else None,
                    "fcpi_tax_reduction_for_year_eur": float(r.fcpi_tax_reduction_for_year)

                    if r.fcpi_tax_reduction_for_year is not None
                    else None,
                    "per_cap_for_year_eur": float(r.per_cap_for_year),
                    "per_contrib_ytd_eur": float(r.per_contrib_year_to_date),
                    "cash_before_invest_eur": float(r.cash_before_invest),
                    "cash_after_invest_eur": float(r.cash_after_invest),
                    "total_value_eur": float(r.total_value),
                    "total_invested_eur": float(r.total_invested),
                    "total_gains_eur": float(r.total_gains),
                    "total_value_real_eur": float(r.total_value_real),
                }

                for r in rows
            ]
        )

        long_rows: list[dict] = []

        for r in rows:
            for pname in result.product_names:
                v = r.value_by_product.get(pname, to_decimal(0))
                inv = r.invested_by_product.get(pname, to_decimal(0))
                div = r.dividends_by_product.get(pname, to_decimal(0))
                contrib = r.contributions_by_product.get(pname, to_decimal(0))
                parts = r.scpi_parts_by_product.get(pname, 0)
                redeem = (r.redemptions_by_product or {}).get(pname, to_decimal(0))

                long_rows.append(
                    {
                        "period": r.period_index + 1,
                        "year": r.year_number,
                        "product": pname,
                        "value_eur": float(v),
                        "invested_cum_eur": float(inv),
                        "gains_eur": float(v - inv),
                        "contrib_period_eur": float(contrib),
                        "dividends_period_eur": float(div),
                        "redemption_period_eur": float(redeem),
                        "scpi_parts": int(parts),
                        "value_real_eur": float(v / r.inflation_index) if float(r.inflation_index) != 0 else float(v),
                    }
                )

        df_long = pd.DataFrame(long_rows)

        st.session_state.sim_df_period = df_period
        st.session_state.sim_df_long = df_long
        st.session_state.sim_summary = {
            "final_value": float(last.total_value),
            "final_value_real": float(last.total_value_real),
            "final_invested": float(last.total_invested),
            "final_gains": float(last.total_gains),
            "tax_due_next_year": float(result.tax_due_next_year),
        }
        st.session_state.sim_products_params = _serialize_products_for_pdf(sim_products)

    # ---------------------------
    # AFFICHAGE (persistant)
    # ---------------------------

    if st.session_state.sim_df_long is None:
        st.info("Soumets le formulaire pour lancer la simulation et afficher les résultats.")

        return

    df_period = st.session_state.sim_df_period
    df_long = st.session_state.sim_df_long
    summary = st.session_state.sim_summary or {}

    st.subheader("Résumé final")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Valeur finale", f"{summary.get('final_value', 0):,.0f}€".replace(",", " "))
    with c2:
        st.metric("Valeur finale réelle", f"{summary.get('final_value_real', 0):,.0f}€".replace(",", " "))
    with c3:
        st.metric("Investi cumulé", f"{summary.get('final_invested', 0):,.0f}€".replace(",", " "))
    with c4:
        st.metric("Gains", f"{summary.get('final_gains', 0):,.0f}€".replace(",", " "))
    with c5:
        st.metric("Impôt dû (N) à payer N+1", f"{summary.get('tax_due_next_year', 0):,.0f}€".replace(",", " "))

    st.subheader("Tableaux")
    tab1, tab2 = st.tabs(["Par période", "Par produit (long)"])
    with tab1:
        st.dataframe(df_period, width="stretch")
    with tab2:
        st.dataframe(df_long, width="stretch")

    st.subheader("Graphiques")
    metrics = [
        "value_eur",
        "value_real_eur",
        "invested_cum_eur",
        "gains_eur",
        "contrib_period_eur",
        "dividends_period_eur",
        "redemption_period_eur",
    ]
    selected_metrics = st.multiselect(
        "Séries à afficher",
        metrics,
        default=st.session_state.sim_selected_metrics,
        key="sim_selected_metrics",
    )

    for m in selected_metrics:
        # Sélection : accroche sur la période X la plus proche
        hover = alt.selection_point(
            fields=["period"],
            nearest=True,
            on="pointerover",
            empty=False
        )

        # Ligne de base
        lines = alt.Chart(df_long).mark_line().encode(
            x=alt.X("period:Q", title="Période"),
            y=alt.Y(f"{m}:Q", title=m.replace("_", " ")),
            color=alt.Color("product:N", title="Produit"),
        )

        # Points sur chaque courbe (visibles au hover)
        points = lines.mark_point(size=80, filled=True).encode(
            opacity=alt.condition(hover, alt.value(1), alt.value(0)),
            tooltip=[
                alt.Tooltip("product:N", title="Produit"),
                alt.Tooltip("period:Q", title="Période"),
                alt.Tooltip("year:Q", title="Année"),
                alt.Tooltip(f"{m}:Q", title=m.replace("_", " "), format=",.2f"),
                alt.Tooltip("contrib_period_eur:Q", title="Contrib", format=",.0f"),
                alt.Tooltip("dividends_period_eur:Q", title="Div", format=",.0f"),
                alt.Tooltip("redemption_period_eur:Q", title="Red", format=",.0f"),
                alt.Tooltip("scpi_parts:Q", title="SCPI", format=",.0f"),
            ]
        ).add_params(hover)

        # Règle verticale grise
        rule = alt.Chart(df_long).mark_rule(color="gray", strokeDash=[3, 3]).encode(
            x="period:Q",
        ).transform_filter(hover)

        # Texte : affiche les valeurs de TOUS les produits à cette période
        text = alt.Chart(df_long).mark_text(
            align="left",
            dx=5,
            dy=-5,
            fontSize=10,
            fontWeight="bold"
        ).encode(
            x="period:Q",
            y=alt.Y(f"{m}:Q"),
            text=alt.Text(f"{m}:Q", format=",.0f"),
            color=alt.Color("product:N"),
        ).transform_filter(hover)

        # Combiner
        chart = alt.layer(lines, points, rule, text).properties(height=320)

        st.altair_chart(chart, width="stretch")

    st.subheader("Exports")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "⬇️ CSV périodes",
            data=df_period.to_csv(index=False).encode("utf-8"),
            file_name="simulation_periods_v3.csv",
            mime="text/csv",
        )
    with c2:
        st.download_button(
            "⬇️ CSV produits",
            data=df_long.to_csv(index=False).encode("utf-8"),
            file_name="simulation_products_v3.csv",
            mime="text/csv",
        )
    with c3:
        pdf_service = SimulationPDFService()
        config_params = {
            "years": int(years),
            "period": period,
            "inflation_pct": float(inflation_pct),
            "income_start": float(income_start),
            "income_growth_pct": float(income_growth_pct),
            "annual_living_costs": float(annual_living_costs),
        }

        pdf_bytes = pdf_service.generate_report(
            df_period=df_period,
            df_long=df_long,
            summary=summary,
            selected_metrics=st.session_state.sim_selected_metrics,
            config_params=config_params,
            products_params=st.session_state.sim_products_params,
        )

        st.download_button(
            "⬇️ PDF Rapport",
            data=pdf_bytes,
            file_name=f"simulation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
        )
