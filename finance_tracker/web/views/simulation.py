"""
simulation.py — UI Streamlit (V3) avec formulaire, persistance et export PDF.
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


# ── Helpers ────────────────────────────────────────────────────────────────────
def eur(x: float):
    return to_decimal(x)


def pct(x: float):
    return to_decimal(x / 100.0)


def _fmt_eur(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")


def _fmt_pct(x: float) -> str:
    return f"{x:.2f}"


# ── Méta-données par catégorie ─────────────────────────────────────────────────
_KIND_META: dict[str, dict] = {
    "cash": {"icon": "💵", "label": "Cash", "color": "#e8f5e9", "border": "#43a047"},
    "savings": {"icon": "🏦", "label": "Épargne", "color": "#e3f2fd", "border": "#1e88e5"},
    "scpi": {"icon": "🏢", "label": "SCPI", "color": "#fff3e0", "border": "#fb8c00"},
    "per": {"icon": "📋", "label": "PER", "color": "#f3e5f5", "border": "#8e24aa"},
    "fcpi": {"icon": "📈", "label": "FCPI", "color": "#fce4ec", "border": "#e91e63"},
    "other": {"icon": "💼", "label": "Autre", "color": "#f5f5f5", "border": "#757575"},
}

_DEFAULT_RETURN_BY_KIND: dict[str, float] = {
    "cash": 0.0, "savings": 3.0, "scpi": 0.0,
    "per": 5.0, "fcpi": 4.0, "other": 3.0,
}

_KIND_HELP: dict[str, str] = {
    "cash": "💡 Le cash reçoit les revenus et paie les dépenses. Aucun rendement applicable.",
    "savings": "💡 Compte d'épargne : les intérêts sont capitalisés chaque période.",
    "scpi": "💡 SCPI : le rendement est géré via le **taux de distribution** ci-dessous. Le rendement nominal est donc 0.",
    "per": "💡 PER : les versements sont **déduits du revenu imposable** dans la limite du plafond défini dans les paramètres globaux.",
    "fcpi": "💡 FCPI : **réduction d'impôt** sur les versements, capital bloqué pendant la durée définie.",
    "other": "💡 Produit générique : rendement annuel capitalisé.",
}

_METRIC_LABELS: dict[str, str] = {
    "value_eur": "Valeur (€)",
    "value_real_eur": "Valeur réelle inflation (€)",
    "invested_cum_eur": "Investi cumulé (€)",
    "gains_eur": "Gains (€)",
    "contrib_period_eur": "Contributions par période (€)",
    "dividends_period_eur": "Dividendes par période (€)",
    "redemption_period_eur": "Remboursements FCPI (€)",
    "scpi_parts": "Parts SCPI détenues",
}


# ── Init session state ─────────────────────────────────────────────────────────
def _init_state() -> None:
    st.session_state.setdefault("sim_df_period", None)
    st.session_state.setdefault("sim_df_long", None)
    st.session_state.setdefault("sim_summary", None)
    st.session_state.setdefault("sim_selected_metrics", ["value_eur", "value_real_eur"])
    st.session_state.setdefault("sim_products_params", [])
    st.session_state.setdefault("sim_config_params", None)


# ── Sérialisation pour PDF ─────────────────────────────────────────────────────
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
        out.append({
            "name": p.name,
            "kind": p.kind,
            "priority": int(p.priority),
            "annual_return_pct": _fmt_pct(float(p.annual_return) * 100.0),
            "contrib_fixed_eur": _fmt_eur(float(p.contribution_per_period)),
            "contrib_pct_income": _fmt_pct(float(p.contribution_pct_income) * 100.0),
            "initial_value_eur": _fmt_eur(float(p.initial_value_eur)),
            "initial_invested_eur": (
                f"{_fmt_eur(float(p.initial_invested_eur))}€"

                if p.initial_invested_eur is not None else "-"
            ),
            "scpi_text": scpi_text,
            "fcpi_text": fcpi_text,
        })

    return out


# ── Blocs de paramètres spécifiques ───────────────────────────────────────────
def _render_scpi_params(name: str) -> dict:
    """Bloc SCPI : appelé uniquement si kind == 'scpi', rendu dans le formulaire."""
    st.markdown(
        "<div style='background:#fff3e0;border-left:4px solid #fb8c00;"
        "padding:8px 14px;border-radius:4px;margin:10px 0 6px 0'>"
        "🏢 <strong>Paramètres SCPI</strong></div>",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        part_price = st.number_input(
            "Prix d'une part (€)", min_value=0.0, value=250.0, step=1.0,
            key=f"v3_scpi_part_{name}",
        )
    with c2:
        parts_per_year = st.number_input(
            "Parts achetées / an", min_value=0, value=0, step=1,
            key=f"v3_scpi_parts_year_{name}",
            help="Nombre de parts achetées par an (réparties selon la fréquence).",
        )
    with c3:
        distribution_pct = st.number_input(
            "Taux de distribution annuel (%)", 0.0, 20.0, 4.5, 0.1,
            key=f"v3_scpi_dist_{name}",
            help="TDVR — Taux de Distribution sur Valeur de Réalisation.",
        )
    with c4:
        revalo_pct = st.number_input(
            "Revalorisation prix part / an (%)", -10.0, 20.0, 0.0, 0.1,
            key=f"v3_scpi_revalo_{name}",
        )

    c5, c6, c7 = st.columns(3)
    with c5:
        dividend_frequency = st.selectbox(
            "Fréquence des dividendes",
            ["monthly", "quarterly", "semiannual", "yearly"],
            format_func=lambda f: {
                "monthly": "🗓️ Mensuelle", "quarterly": "🗓️ Trimestrielle",
                "semiannual": "🗓️ Semestrielle", "yearly": "🗓️ Annuelle",
            }[f],
            index=1,
            key=f"v3_scpi_freq_{name}",
        )
    with c6:
        dividends_to_cash = st.checkbox(
            "Dividendes versés en cash", value=True,
            key=f"v3_scpi_to_cash_{name}",
            help="Si coché, les dividendes alimentent le compte cash et peuvent être réinvestis.",
        )
    with c7:
        init_scpi_parts_value = st.number_input(
            "Parts initiales (0 = dérivé de la valorisation)",
            min_value=0, value=0, step=1,
            key=f"v3_scpi_init_parts_{name}",
        )
        use_init_parts = st.checkbox(
            "Forcer ce nombre de parts initial", value=False,
            key=f"v3_scpi_use_init_parts_{name}",
        )

    return {
        "part_price": part_price,
        "parts_per_year": parts_per_year,
        "distribution_pct": distribution_pct,
        "revalo_pct": revalo_pct,
        "dividend_frequency": dividend_frequency,
        "dividends_to_cash": dividends_to_cash,
        "init_scpi_parts": int(init_scpi_parts_value) if use_init_parts else None,
    }


def _render_fcpi_params(name: str) -> dict:
    """Bloc FCPI : appelé uniquement si kind == 'fcpi', rendu dans le formulaire."""
    st.markdown(
        "<div style='background:#fce4ec;border-left:4px solid #e91e63;"
        "padding:8px 14px;border-radius:4px;margin:10px 0 6px 0'>"
        "📈 <strong>Paramètres FCPI</strong></div>",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        fcpi_tax_rate_pct = st.number_input(
            "Réduction d'impôt (%)",
            min_value=0.0, max_value=100.0, value=18.0, step=0.5,
            key=f"v3_fcpi_tax_rate_{name}",
            help="Taux appliqué aux versements éligibles pour calculer la réduction IR (18% par défaut).",
        )
    with c2:
        fcpi_eligible_cap = st.number_input(
            "Plafond versements éligibles (€/an)",
            min_value=0.0, value=12000.0, step=500.0,
            key=f"v3_fcpi_cap_{name}",
            help="12 000€ pour célibataire, 24 000€ pour couple.",
        )
    with c3:
        fcpi_holding_years = st.number_input(
            "Durée de blocage (années)",
            min_value=1, max_value=30, value=8, step=1,
            key=f"v3_fcpi_years_{name}",
            help="Durée minimale pour conserver l'avantage fiscal (généralement 5-10 ans).",
        )
    with c4:
        fcpi_exit_mode = st.selectbox(
            "Mode de sortie à échéance",
            ["principal", "full_value"],
            format_func=lambda m: (
                "💰 Capital initial seulement" if m == "principal"
                else "📊 Valeur totale du fonds"
            ),
            index=0,
            key=f"v3_fcpi_exit_{name}",
            help="'Capital' = récupère les versements. 'Valeur totale' = récupère la valorisation réelle.",
        )

    return {
        "tax_rate_pct": fcpi_tax_rate_pct,
        "eligible_cap": fcpi_eligible_cap,
        "holding_years": fcpi_holding_years,
        "exit_mode": fcpi_exit_mode,
    }


# ── Sélecteurs de catégorie (HORS formulaire) ──────────────────────────────────
def _render_kind_selectors(product_names: list[str]) -> None:
    """
    Selectboxes de catégorie hors du formulaire.
    Changer la catégorie déclenche un rerun immédiat → le formulaire
    s'adapte sans attendre la soumission.
    """
    st.markdown("#### 🏷️ Catégories des produits")
    st.caption(
        "Sélectionne la catégorie de chaque produit. "
        "Les paramètres spécifiques (SCPI, FCPI…) apparaissent automatiquement dans le formulaire ci-dessous."
    )

    categories = list(_KIND_META.keys())
    n_cols = min(len(product_names), 4)
    cols = st.columns(n_cols)

    for i, name in enumerate(product_names):
        name_lower = name.lower()
        default_kind = name_lower if name_lower in categories else "other"
        current_kind = st.session_state.get(f"v3_kind_{name}", default_kind)
        meta = _KIND_META.get(current_kind, _KIND_META["other"])

        with cols[i % n_cols]:
            # Badge coloré au-dessus du selectbox
            st.markdown(
                f"<div style='background:{meta['color']};border:1px solid {meta['border']};"
                f"border-radius:6px;padding:4px 10px;font-size:13px;font-weight:600;"
                f"text-align:center;margin-bottom:4px'>"
                f"{meta['icon']} {name}</div>",
                unsafe_allow_html=True,
            )
            st.selectbox(
                "Catégorie",
                options=categories,
                format_func=lambda k: f"{_KIND_META[k]['icon']} {_KIND_META[k]['label']}",
                index=categories.index(current_kind),
                key=f"v3_kind_{name}",
                label_visibility="collapsed",
            )


# ── Rendu principal ────────────────────────────────────────────────────────────
def render(session: Session) -> None:
    _init_state()
    st.header("🧮 Simulation long terme")

    product_repo = SQLModelProductRepository(session)
    products_db = product_repo.get_all()
    product_names = [p.name for p in products_db]

    if not product_names:
        st.info("Ajoute au moins un produit dans '➕ Ajouter Produits' avant de simuler.")
        st.stop()

    portfolio = DashboardService(session).build_portfolio()
    defaults_by_name = {
        p["name"]: {
            "initial_value": float(p.get("current_value_eur", 0) or 0),
            "initial_invested": float(p.get("net_contributions_eur", 0) or 0),
        }

        for p in portfolio.products
    }

    # ── Sélecteurs de catégorie HORS formulaire ────────────────────────────
    _render_kind_selectors(product_names)
    st.markdown("---")

    # ── Formulaire ─────────────────────────────────────────────────────────
    with st.form(key="sim_form", clear_on_submit=False):

        # Paramètres globaux
        st.markdown("### ⚙️ Paramètres globaux")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            years = st.number_input("Durée (années)", min_value=1, max_value=80, value=20, step=1)
            period = st.selectbox(
                "Période de calcul",
                ["monthly", "quarterly", "yearly"],
                format_func=lambda p: {
                    "monthly": "Mensuelle", "quarterly": "Trimestrielle", "yearly": "Annuelle"
                }[p],
                index=0,
            )
        with c2:
            inflation_pct = st.number_input("Inflation annuelle (%)", 0.0, 20.0, 2.0, 0.1)
        with c3:
            income_start = st.number_input("Revenu brut annuel N (€)", 0.0, value=50000.0, step=1000.0)
            income_prev = st.number_input(
                "Revenu brut annuel N-1 (€)", 0.0, value=50000.0, step=1000.0,
                help="Utilisé pour le plafond PER (10% du revenu N-1).",
            )
        with c4:
            income_growth_pct = st.number_input("Augmentation revenu / an (%)", 0.0, 20.0, 2.0, 0.1)

        c1, c2, c3 = st.columns(3)
        with c1:
            annual_living_costs = st.number_input("Dépenses annuelles (€)", 0.0, value=24000.0, step=500.0)
        with c2:
            emergency_target = st.number_input(
                "Épargne de précaution (€)", 0.0, value=5000.0, step=500.0,
                help="Seuil minimum de cash maintenu avant tout investissement.",
            )
        with c3:
            initial_tax_due = st.number_input("Impôt dû N-1 à payer en année 1 (€)", 0.0, value=0.0, step=100.0)

        st.markdown("---")

        # Fiscalité
        st.markdown("### 🧾 Fiscalité (barème progressif)")
        c1, c2 = st.columns(2)
        with c1:
            household_parts = st.number_input(
                "Parts fiscales (quotient familial)", min_value=1.0, value=1.0, step=0.5,
            )
        with c2:
            std_deduction_pct = st.number_input("Abattement forfaitaire (%)", 0.0, 30.0, 10.0, 0.5)

        default_brackets = [
            {"up_to": 11294, "rate_pct": 0.0},
            {"up_to": 28797, "rate_pct": 11.0},
            {"up_to": 82341, "rate_pct": 30.0},
            {"up_to": 177106, "rate_pct": 41.0},
            {"up_to": None, "rate_pct": 45.0},
        ]
        st.caption("Tranches annuelles — laisse `up_to` vide pour la dernière tranche.")
        df_brackets = st.data_editor(
            pd.DataFrame(default_brackets), width="stretch", num_rows="dynamic",
        )
        brackets: list[TaxBracket] = []

        for _, r in df_brackets.iterrows():
            up_to = r.get("up_to", None)
            up_to_val = None if pd.isna(up_to) else to_decimal(float(up_to))
            brackets.append(TaxBracket(up_to=up_to_val, rate=pct(float(r.get("rate_pct", 0.0)))))

        st.markdown("---")

        # PER
        st.markdown("### 📋 PER — Plafond déductible")
        c1, c2, c3 = st.columns(3)
        with c1:
            per_rate_prev_income_pct = st.number_input("% du revenu N-1", 0.0, 50.0, 10.0, 0.5)
        with c2:
            per_min = st.number_input("Plafond PER minimum (€/an)", 0.0, value=0.0, step=100.0)
        with c3:
            per_max = st.number_input("Plafond PER maximum (€/an, 0 = illimité)", 0.0, value=0.0, step=500.0)

        st.markdown("---")

        # Produits
        st.markdown("### 🗂️ Paramètres par produit")
        st.caption("Seuls les paramètres pertinents s'affichent selon la catégorie définie ci-dessus.")

        categories = list(_KIND_META.keys())
        sim_products: list[ProductSimConfig] = []

        for name in product_names:
            defaults = defaults_by_name.get(name, {"initial_value": 0.0, "initial_invested": 0.0})
            name_lower = name.lower()
            default_kind = name_lower if name_lower in categories else "other"
            kind = st.session_state.get(f"v3_kind_{name}", default_kind)
            meta = _KIND_META.get(kind, _KIND_META["other"])

            # Titre de l'expander avec indicateur visuel de catégorie
            with st.expander(
                f"{meta['icon']} **{name}** — {meta['label']}",
                expanded=False,
            ):
                # Info contextuelle

                if kind in _KIND_HELP:
                    st.info(_KIND_HELP[kind])

                # Paramètres communs
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    initial_value = st.number_input(
                        "Valorisation initiale (€)",
                        min_value=0.0, value=float(defaults["initial_value"]), step=500.0,
                        key=f"v3_init_val_{name}",
                    )
                with c2:
                    initial_invested = st.number_input(
                        "Investi initial (€)",
                        min_value=0.0, value=float(defaults["initial_invested"]), step=500.0,
                        key=f"v3_init_inv_{name}",
                        help="Base de calcul des plus-values.",
                    )
                    use_initial_invested = st.checkbox(
                        "Utiliser 'Investi initial'", value=True,
                        key=f"v3_use_init_inv_{name}",
                    )
                with c3:
                    priority = st.number_input(
                        "Priorité d'allocation (1 = max)",
                        min_value=1, max_value=999, value=50, step=1,
                        key=f"v3_prio_{name}",
                        help="Ordre dans lequel le budget disponible est alloué.",
                    )
                with c4:
                    default_ret = _DEFAULT_RETURN_BY_KIND.get(kind, 3.0)
                    ret_label = (
                        "Rendement nominal (%) — non utilisé pour SCPI"

                        if kind == "scpi" else "Rendement annuel nominal (%)"
                    )
                    annual_return_pct = st.number_input(
                        ret_label,
                        min_value=-50.0, max_value=50.0,
                        value=default_ret,
                        step=0.1,
                        key=f"v3_ret_{name}",
                        help="Pour SCPI : laisser à 0, le rendement est calculé via le taux de distribution."

                        if kind == "scpi" else None,
                    )

                # Contributions (masquées pour SCPI)

                if kind != "scpi":
                    c5, c6 = st.columns(2)
                    with c5:
                        contrib_fixed = st.number_input(
                            "Apport fixe par période (€)",
                            min_value=0.0, value=0.0, step=50.0,
                            key=f"v3_contrib_fixed_{name}",
                        )
                    with c6:
                        contrib_pct_income = st.number_input(
                            "Apport en % du revenu par période (%)",
                            min_value=0.0, max_value=100.0, value=0.0, step=0.5,
                            key=f"v3_contrib_pct_income_{name}",
                        )
                else:
                    contrib_fixed = 0.0
                    contrib_pct_income = 0.0
                    st.caption("ℹ️ Pour une SCPI, les apports sont définis via **'Parts achetées / an'** ci-dessous.")

                # Blocs spécifiques (conditionnels)
                scpi_cfg = None
                fcpi_cfg = None
                init_scpi_parts = None

                if kind == "scpi":
                    sd = _render_scpi_params(name)
                    scpi_cfg = SCPIConfig(
                        part_price=eur(sd["part_price"]),
                        parts_per_year=int(sd["parts_per_year"]),
                        distribution_annual=pct(sd["distribution_pct"]),
                        dividends_to_cash=bool(sd["dividends_to_cash"]),
                        revaluation_annual=pct(sd["revalo_pct"]),
                        dividend_frequency=sd["dividend_frequency"],
                    )
                    init_scpi_parts = sd["init_scpi_parts"]

                elif kind == "fcpi":
                    fd = _render_fcpi_params(name)
                    fcpi_cfg = FCPIConfig(
                        tax_reduction_rate=pct(fd["tax_rate_pct"]),
                        annual_eligible_cap=eur(fd["eligible_cap"]),
                        holding_years=int(fd["holding_years"]),
                        exit_mode=fd["exit_mode"],
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
            st.error("⚠️ Il faut au moins un produit de catégorie 'cash'.")

        submitted = st.form_submit_button(
            "▶️ Lancer la simulation", type="primary", width="stretch",
        )

    # ── Calcul ─────────────────────────────────────────────────────────────

    if submitted:
        st.session_state["sim_pdf_needs_update"] = True  # Force la regénération du PDF

        if not any(p.kind == "cash" for p in sim_products):
            st.stop()

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
        st.session_state.sim_config_params = {
            "years": int(years), "period": period,
            "inflation_pct": float(inflation_pct),
            "income_start": float(income_start),
            "income_growth_pct": float(income_growth_pct),
            "annual_living_costs": float(annual_living_costs),
        }

        with st.spinner("⏳ Calcul de la simulation en cours…"):
            result = SimulationService().run(cfg, sim_products)

        cash_name = result.cash_product
        rows = result.rows
        last = rows[-1]

        df_period = pd.DataFrame([
            {
                "period": r.period_index + 1,
                "year": r.year_number,
                "step_in_year": r.step_in_year + 1,
                "income_period_eur": float(r.income_period),
                "living_costs_period_eur": float(r.living_costs_period),
                "tax_paid_period_eur": float(r.tax_paid_period),
                "tax_due_for_year_eur": float(r.tax_due_for_year) if r.tax_due_for_year is not None else None,
                "fcpi_tax_reduction_for_year_eur": float(r.fcpi_tax_reduction_for_year)

                if r.fcpi_tax_reduction_for_year is not None else None,
                "per_cap_for_year_eur": float(r.per_cap_for_year),
                "per_contrib_ytd_eur": float(r.per_contrib_year_to_date),
                "cash_before_invest_eur": float(r.cash_before_invest),
                "cash_after_invest_eur": float(r.cash_after_invest),
                "total_value_eur": float(r.total_value),
                "total_value_real_eur": float(r.total_value_real),
                "total_invested_eur": float(r.total_invested),
                "total_gains_eur": float(r.total_gains),
            }

            for r in rows
        ])

        long_rows: list[dict] = []

        for r in rows:
            for pname in result.product_names:
                v = r.value_by_product.get(pname, to_decimal(0))
                inv = r.invested_by_product.get(pname, to_decimal(0))
                div = r.dividends_by_product.get(pname, to_decimal(0))
                contrib = r.contributions_by_product.get(pname, to_decimal(0))
                parts = r.scpi_parts_by_product.get(pname, 0)
                redeem = (r.redemptions_by_product or {}).get(pname, to_decimal(0))
                gains = None if pname == cash_name else float(v - inv)
                long_rows.append({
                    "period": r.period_index + 1,
                    "year": r.year_number,
                    "product": pname,
                    "value_eur": float(v),
                    "invested_cum_eur": float(inv),
                    "gains_eur": gains,
                    "contrib_period_eur": float(contrib),
                    "dividends_period_eur": float(div),
                    "redemption_period_eur": float(redeem),
                    "scpi_parts": int(parts),
                    "value_real_eur": float(v / r.inflation_index)

                    if float(r.inflation_index) != 0 else float(v),
                })

        df_long = pd.DataFrame(long_rows)
        st.session_state.sim_df_period = df_period
        st.session_state.sim_df_long = df_long
        gains_val = float(last.total_gains)
        invested_val = float(last.total_invested)
        st.session_state.sim_summary = {
            "final_value": float(last.total_value),
            "final_value_real": float(last.total_value_real),
            "final_invested": invested_val,
            "final_gains": gains_val,
            "gains_pct": (gains_val / invested_val * 100) if invested_val > 0 else 0.0,
            "tax_due_next_year": float(result.tax_due_next_year),
        }
        st.session_state.sim_products_params = _serialize_products_for_pdf(sim_products)

    # ── Affichage persistant ────────────────────────────────────────────────

    if st.session_state.sim_df_long is None:
        st.info("Soumets le formulaire pour lancer la simulation.")

        return

    df_period = st.session_state.sim_df_period
    df_long = st.session_state.sim_df_long
    summary = st.session_state.sim_summary or {}

    st.markdown("---")
    st.subheader("📊 Résumé final")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Valeur finale", f"{summary.get('final_value', 0):,.0f}€".replace(",", " "))
    with c2:
        st.metric("Valeur réelle (inflation)", f"{summary.get('final_value_real', 0):,.0f}€".replace(",", " "))
    with c3:
        st.metric("Investi cumulé (hors cash)", f"{summary.get('final_invested', 0):,.0f}€".replace(",", " "))
    with c4:
        st.metric(
            "Gains (hors cash)",
            f"{summary.get('final_gains', 0):,.0f}€".replace(",", " "),
            delta=f"{summary.get('gains_pct', 0):.1f}%",
        )
    with c5:
        st.metric("Impôt dû N à payer N+1", f"{summary.get('tax_due_next_year', 0):,.0f}€".replace(",", " "))

    st.subheader("📋 Tableaux de données")
    tab1, tab2 = st.tabs(["Par période", "Par produit (long)"])
    with tab1:
        st.dataframe(df_period, width="stretch")
    with tab2:
        st.dataframe(df_long, width="stretch")

    st.subheader("📈 Graphiques")
    selected_metrics = st.multiselect(
        "Métriques à afficher",
        options=list(_METRIC_LABELS.keys()),
        format_func=lambda m: _METRIC_LABELS.get(m, m),
        default=st.session_state.sim_selected_metrics,
        key="sim_selected_metrics",
    )

    for m in selected_metrics:
        friendly = _METRIC_LABELS.get(m, m)
        st.markdown(f"**{friendly}**")
        hover = alt.selection_point(fields=["period"], nearest=True, on="pointerover", empty=False)
        lines = alt.Chart(df_long).mark_line(strokeWidth=2).encode(
            x=alt.X("period:Q", title="Période"),
            y=alt.Y(f"{m}:Q", title=friendly),
            color=alt.Color("product:N", title="Produit"),
        )
        points = lines.mark_point(size=80, filled=True).encode(
            opacity=alt.condition(hover, alt.value(1), alt.value(0)),
            tooltip=[
                alt.Tooltip("product:N", title="Produit"),
                alt.Tooltip("period:Q", title="Période"),
                alt.Tooltip("year:Q", title="Année"),
                alt.Tooltip(f"{m}:Q", title=friendly, format=",.0f"),
                alt.Tooltip("contrib_period_eur:Q", title="Contrib (€)", format=",.0f"),
                alt.Tooltip("dividends_period_eur:Q", title="Dividendes (€)", format=",.0f"),
                alt.Tooltip("redemption_period_eur:Q", title="Rembt FCPI (€)", format=",.0f"),
                alt.Tooltip("scpi_parts:Q", title="Parts SCPI", format=",.0f"),
            ],
        ).add_params(hover)
        rule = alt.Chart(df_long).mark_rule(color="#cccccc", strokeDash=[4, 4]).encode(
            x="period:Q",
        ).transform_filter(hover)
        chart = alt.layer(lines, points, rule).properties(height=340)
        st.altair_chart(chart, width="stretch")

    st.subheader("Exports")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.download_button(
            "⬇️ CSV périodes",
            data=df_period.to_csv(index=False).encode("utf-8"),
            file_name="simulation_periods.csv",
            mime="text/csv",
            width="stretch"
        )

    with c2:
        st.download_button(
            "⬇️ CSV produits",
            data=df_long.to_csv(index=False).encode("utf-8"),
            file_name="simulation_products.csv",
            mime="text/csv",
            width="stretch"
        )

    with c3:
        # Clé unique pour forcer la regénération si les données de simulation changent
        pdf_cache_key = "sim_pdf_bytes"

        # Si le PDF n'a pas encore été généré pour cette session

        if pdf_cache_key not in st.session_state or st.session_state.get("sim_pdf_needs_update", True):
            if st.button("⚙️ Préparer le rapport PDF", width="stretch"):
                with st.spinner("⏳ Génération du rapport PDF avec graphiques en cours (cela peut prendre quelques secondes)..."):
                    try:
                        config_params = st.session_state.sim_config_params or {}
                        pdf_bytes = SimulationPDFService().generate_report(
                            df_period=df_period,
                            df_long=df_long,
                            summary=summary,
                            selected_metrics=st.session_state.sim_selected_metrics,
                            config_params=config_params,
                            products_params=st.session_state.sim_products_params,
                        )
                        st.session_state[pdf_cache_key] = pdf_bytes
                        st.session_state["sim_pdf_needs_update"] = False
                        st.rerun()  # Rafraîchit l'interface pour afficher le bouton de téléchargement
                    except Exception as e:
                        st.error(f"Erreur lors de la génération du PDF : {e}")

        # Si le PDF est prêt dans le cache de la session
        else:
            st.download_button(
                "⬇️ Télécharger le PDF",
                data=st.session_state[pdf_cache_key],
                file_name=f"simulation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                type="primary",
                width="stretch"
            )
