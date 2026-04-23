"""
Finance Tracker Dashboard Module
"""
# Standard library
from datetime import datetime, date

# Third-party imports (par ordre alphabétique)
import altair as alt
import pandas as pd
from sqlmodel import Session
import streamlit as st

# Local imports (par ordre alphabétique)
from finance_tracker.domain.models import Valuation
from finance_tracker.services.btc_price_service import BTCPriceService, BTCPriceServiceError
from finance_tracker.services.dashboard_service import DashboardService
from finance_tracker.services.pdf_report_service import PDFReportService
from finance_tracker.web.ui.formatters import format_eur, to_decimal

SATS_PER_BTC = 100_000_000


def _fmt_sats(v: float) -> str:
    return f"{int(v):,} Sats".replace(",", " ")


def _render_bitcoin_expander(details: dict, product_id: int, service: "DashboardService") -> None:
    """Render the Bitcoin-specific product detail section inside an expander."""
    live_price: float | None = st.session_state.get("btc_price")
    history = details["history"]

    last_unit_price = history[-1]["unit_price_eur"] if history else None
    latest_total = details["current_value"]
    total_qty_btc = (latest_total / last_unit_price) if (last_unit_price and last_unit_price > 0) else 0.0
    total_qty_sats = int(total_qty_btc * SATS_PER_BTC)

    pru = details["pru"]
    ref_price = live_price or last_unit_price
    pnl_pct = ((ref_price - pru) / pru * 100) if (ref_price and pru and pru > 0) else None
    pnl_eur = ((ref_price - pru) * total_qty_btc) if (ref_price and pru and total_qty_btc > 0) else None

    # ── Hero panel ──────────────────────────────────────────────────────────────
    price_display = f"{live_price:,.0f} €".replace(",", " ") if live_price else "---"
    status_badge = (
        "<span style='background:#16a34a;color:white;border-radius:20px;"
        "padding:2px 10px;font-size:12px;font-weight:600;'>● LIVE</span>"
        if live_price else
        "<span style='background:#6b7280;color:white;border-radius:20px;"
        "padding:2px 10px;font-size:12px;font-weight:600;'>● OFFLINE</span>"
    )
    st.markdown(
        f"""
<div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 60%,#0f3460 100%);
    border-radius:12px;padding:20px 28px;margin-bottom:16px;border:1px solid #F7931A44;">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
            <span style="color:#F7931A;font-size:32px;font-weight:900;">₿</span>
            <span style="color:#9ca3af;font-size:13px;margin-left:8px;">Bitcoin · BTC/EUR</span>
        </div>
        <div style="text-align:right;">
            {status_badge}
            <div style="color:white;font-size:28px;font-weight:800;margin-top:4px;">{price_display}</div>
        </div>
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    col_refresh, _ = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 Actualiser le cours", key=f"btc_refresh_{product_id}", width="stretch"):
            with st.spinner("Connexion aux APIs..."):
                try:
                    st.session_state.btc_price = float(BTCPriceService().get_btc_price_eur())
                    st.session_state.api_error = None
                    st.rerun()
                except BTCPriceServiceError:
                    st.session_state.api_error = True

    if st.session_state.get("api_error"):
        st.warning("📡 **Hors ligne** — Réseau inaccessible. Saisissez le prix manuellement ci-dessous.")

    # ── Key indicators ───────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("💼 Valeur actuelle", format_eur(latest_total) if latest_total else "—")
    with k2:
        st.metric("📦 Quantité", _fmt_sats(total_qty_sats) if total_qty_sats > 0 else "—")
    with k3:
        st.metric("📌 PRU", format_eur(pru) if pru else "—")
    with k4:
        if pnl_eur is not None and pnl_pct is not None:
            st.metric("📈 P&L Latente", format_eur(pnl_eur), delta=f"{pnl_pct:+.2f}%", delta_color="normal")
        else:
            st.metric("📈 P&L Latente", "—")

    # ── Price history chart ──────────────────────────────────────────────────────
    if len(history) >= 2:
        st.markdown("##### 📉 Historique des prix (snapshots)")
        price_rows = [
            {"date": pd.Timestamp(v["date"]), "Prix BTC (€)": v["unit_price_eur"]}
            for v in history if v["unit_price_eur"]
        ]
        if price_rows:
            chart_df = pd.DataFrame(price_rows)
            base = alt.Chart(chart_df).encode(
                x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %Y")),
            )
            line = base.mark_line(color="#F7931A", strokeWidth=2.5).encode(
                y=alt.Y("Prix BTC (€):Q", title="Prix BTC (€)"),
                tooltip=[
                    alt.Tooltip("date:T", title="Date", format="%d/%m/%Y"),
                    alt.Tooltip("Prix BTC (€):Q", title="Prix (€)", format=",.0f"),
                ],
            )
            pts = base.mark_circle(color="#F7931A", size=40).encode(y="Prix BTC (€):Q")
            chart = (line + pts).properties(height=240)
            if pru:
                pru_df = pd.DataFrame([
                    {"date": chart_df["date"].min(), "PRU": pru},
                    {"date": chart_df["date"].max(), "PRU": pru},
                ])
                pru_line = alt.Chart(pru_df).mark_line(
                    color="#6366f1", strokeDash=[6, 4], strokeWidth=1.8,
                ).encode(
                    x="date:T",
                    y=alt.Y("PRU:Q"),
                    tooltip=[alt.Tooltip("PRU:Q", title="PRU (€)", format=",.0f")],
                )
                chart = (chart + pru_line).properties(height=240)
            st.altair_chart(chart, use_container_width=True)
            legend_parts = ["<span style='color:#F7931A'>■</span> Prix BTC"]
            if pru:
                legend_parts.append("<span style='color:#6366f1'>- -</span> PRU")
            st.markdown(
                "<span style='font-size:0.85em;color:gray'>" + " · ".join(legend_parts) + "</span>",
                unsafe_allow_html=True,
            )

    # ── Snapshot form ────────────────────────────────────────────────────────────
    st.markdown("##### 📸 Nouveau Snapshot")
    default_price = live_price or (last_unit_price or 0.0)
    with st.form(f"btc_snapshot_{product_id}", clear_on_submit=True):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            val_date = st.date_input("Date", value=date.today())
        with fc2:
            btc_unit_price = st.number_input(
                "Prix d'un BTC plein (EUR)",
                value=float(default_price),
                step=100.0,
            )
        with fc3:
            input_sats = st.number_input(
                "Quantité (en Satoshis)",
                value=int(total_qty_sats),
                step=100_000,
                format="%d",
                help="1 BTC = 100 000 000 Sats",
            )
        if btc_unit_price > 0 and input_sats > 0:
            qty_btc_preview = input_sats / SATS_PER_BTC
            st.info(f"💶 Valeur calculée : **{format_eur(btc_unit_price * qty_btc_preview)}**")
        if st.form_submit_button("💾 Enregistrer le snapshot", type="primary", width="stretch"):
            if input_sats <= 0 or btc_unit_price <= 0:
                st.error("La quantité (en sats) et le prix doivent être > 0.")
            else:
                try:
                    qty_btc_final = input_sats / SATS_PER_BTC
                    total_val = qty_btc_final * btc_unit_price
                    service.valuation_repo.create(Valuation(
                        product_id=product_id,
                        date=datetime.combine(val_date, datetime.min.time()),
                        total_value_eur=to_decimal(total_val),
                        unit_price_eur=to_decimal(btc_unit_price),
                    ))
                    st.success(f"✅ Snapshot enregistré — Valeur : {format_eur(total_val)}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")

    # ── Recent snapshots table ───────────────────────────────────────────────────
    if history:
        recent_btc = list(reversed(history))[:8]
        rows_btc = []
        for v in recent_btc:
            val_eur = v["total_value_eur"]
            prix_unit = v["unit_price_eur"] or 0.0
            sats = int((val_eur / prix_unit) * SATS_PER_BTC) if prix_unit > 0 else 0
            d = v["date"]
            rows_btc.append({
                "Date": d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else str(d),
                "Prix BTC (€)": f"{prix_unit:,.0f}".replace(",", " ") if prix_unit > 0 else "—",
                "Satoshis": f"{sats:,}".replace(",", " ") if sats > 0 else "—",
                "Valeur totale (€)": f"{val_eur:,.2f}".replace(",", " "),
            })
        st.dataframe(pd.DataFrame(rows_btc), hide_index=True, use_container_width=True)


def _render_generic_expander(details: dict) -> None:
    """Render the generic product detail section inside an expander."""
    # Mini KPI row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Valeur actuelle", format_eur(details["current_value"]))
    with k2:
        st.metric("Investi net", format_eur(details["net_invested"]))
    with k3:
        st.metric(
            "Gains",
            format_eur(details["gains_eur"]),
            delta=f"{details['gains_pct']:.2f}%",
            delta_color="normal",
        )
    with k4:
        if details["pru"] is not None:
            st.metric("PRU", format_eur(details["pru"]))
        else:
            st.metric("PRU", "—")

    # Valuation curve chart
    if len(details["history"]) >= 2:
        chart_df = pd.DataFrame(details["history"])
        chart_df["date"] = pd.to_datetime(chart_df["date"])

        base = alt.Chart(chart_df).encode(
            x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %Y")),
        )
        area = base.mark_area(
            color=details["color"],
            opacity=0.15,
            line={"color": details["color"], "strokeWidth": 2.5},
        ).encode(
            y=alt.Y("total_value_eur:Q", title="Valeur (€)"),
            tooltip=[
                alt.Tooltip("date:T", title="Date", format="%d/%m/%Y"),
                alt.Tooltip("total_value_eur:Q", title="Valeur (€)", format=",.2f"),
            ],
        )
        points = base.mark_circle(color=details["color"], size=40).encode(y="total_value_eur:Q")
        chart = (area + points).properties(height=240)

        if details["pru"] is not None:
            pru_df = pd.DataFrame([
                {"date": chart_df["date"].min(), "PRU": details["pru"]},
                {"date": chart_df["date"].max(), "PRU": details["pru"]},
            ])
            pru_line = alt.Chart(pru_df).mark_line(
                color="#6366f1", strokeDash=[6, 4], strokeWidth=1.8,
            ).encode(
                x="date:T",
                y=alt.Y("PRU:Q"),
                tooltip=[alt.Tooltip("PRU:Q", title="PRU (€)", format=",.2f")],
            )
            chart = (chart + pru_line).properties(height=240)

        st.altair_chart(chart, use_container_width=True)

        legend_parts = [f"<span style='color:{details['color']}'>■</span> Valeur"]
        if details["pru"] is not None:
            legend_parts.append("<span style='color:#6366f1'>- -</span> PRU")
        st.markdown(
            "<span style='font-size:0.85em;color:gray'>" + " · ".join(legend_parts) + "</span>",
            unsafe_allow_html=True,
        )

    # Recent valuations table
    recent = list(reversed(details["history"]))[:8]
    if recent:
        table_rows = []
        for v in recent:
            row = {
                "Date": v["date"].strftime("%d/%m/%Y") if hasattr(v["date"], "strftime") else str(v["date"]),
                "Valeur (€)": f"{v['total_value_eur']:,.2f}".replace(",", " "),
            }
            if v.get("unit_price_eur"):
                row["Prix unitaire (€)"] = f"{v['unit_price_eur']:,.2f}".replace(",", " ")
            table_rows.append(row)
        st.dataframe(pd.DataFrame(table_rows), hide_index=True, use_container_width=True)


def render(session: Session) -> None:
    """
    Render the main dashboard page in the Streamlit application.

    This page provides a comprehensive overview of the investment portfolio,
    including key performance indicators, allocation breakdown, and export
    capabilities.

    The page is organized into three main sections:

    1. Overview KPIs - Total value, invested amount, gains, and cash
    2. Portfolio Allocation - Horizontal bar chart and detailed table
    3. Exports & Reports - PDF and JSON download functionality

    Parameters
    ----------
    session : Session
        SQLModel database session for repository operations.

    Returns
    -------
    None
        This function renders UI components directly to Streamlit.

    Notes
    -----
    - Performance percentage is calculated as (gains / invested) * 100
    - Allocation chart uses Altair with horizontal bars
    - PDF and JSON exports are cached in st.session_state to avoid
      regenerating on each page refresh
    - A refresh button allows clearing the cache to force regeneration

    The function gracefully handles empty portfolios by displaying
    an informational message guiding users to add valuations.

    Examples
    --------
    >>> from finance_tracker.web.db import get_session
    >>> session = get_session()
    >>> render(session)  # Renders the dashboard in Streamlit
    """
    st.title("📊 Tableau de bord")
    st.caption("Aperçu global et performances de votre portefeuille d'investissement.")

    # Initialize dashboard service and build portfolio data
    service = DashboardService(session)

    try:
        portfolio = service.build_portfolio()
    except Exception as e:
        st.error(f"Impossible de charger le portefeuille : {e}")

        return

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1: KEY PERFORMANCE INDICATORS
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("### 📈 Vue d'ensemble")

    # Calculate performance percentage (handle division by zero)
    perf_pct = (
        float(portfolio.total_gains_eur / portfolio.total_invested_eur * 100)

        if portfolio.total_invested_eur > 0
        else 0
    )

    # Display four main KPIs in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="💼 Valeur Totale", value=format_eur(portfolio.total_value_eur))
    with col2:
        st.metric(label="📥 Total Investi", value=format_eur(portfolio.total_invested_eur))
    with col3:
        st.metric(
            label="📈 Plus-values",
            value=format_eur(portfolio.total_gains_eur),
            delta=f"{perf_pct:.2f}%",
            delta_color="normal",
        )

    with col4:
        st.metric(label="💶 Cash disponible", value=format_eur(portfolio.cash_available))

    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2: PORTFOLIO ALLOCATION
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("### 🧩 Répartition du portefeuille")

    # Build rows for products with non-zero value or contributions
    rows = []

    for p in portfolio.products:
        if p.get("current_value_eur", 0) > 0 or p.get("net_contributions_eur", 0) > 0:
            rows.append(
                {
                    "Produit": p["name"],
                    "Valeur_brute": float(p["current_value_eur"]),  # For sorting
                    "Valeur": f"{float(p['current_value_eur']):.2f} €",
                    "Investi": f"{float(p['net_contributions_eur']):.2f} €",
                    "Gains": f"{float(p['performance_eur']):.2f} €",
                    "Perf %": f"{float(p['performance_pct']):.2f} %",
                    "Allocation": float(p["allocation_pct"]),
                }
            )

    if rows:
        df = pd.DataFrame(rows)
        # Sort by allocation ascending (for horizontal bar chart)
        df_sorted = df.sort_values("Allocation", ascending=True)

        c_chart, c_table = st.columns([1, 1.6])

        # ═════════════════════════════════════════════════════════════════════
        # ALLOCATION CHART (Altair Horizontal Bar)
        # ═════════════════════════════════════════════════════════════════════
        with c_chart:
            chart = (
                alt.Chart(df_sorted)
                .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                .encode(
                    x=alt.X(
                        "Allocation:Q",
                        title="Poids (%)",
                        scale=alt.Scale(domain=[0, 100]),
                    ),
                    y=alt.Y(
                        "Produit:N",
                        sort=None,  # Preserve dataframe order
                        title="",
                        axis=alt.Axis(labelLimit=150),
                    ),
                    color=alt.Color(
                        "Produit:N",
                        legend=None,  # Legend in table instead
                        scale=alt.Scale(scheme="tableau10"),
                    ),
                    tooltip=[
                        alt.Tooltip("Produit:N", title="Produit"),
                        alt.Tooltip("Allocation:Q", title="Poids (%)", format=".1f"),
                        alt.Tooltip("Valeur:N", title="Valeur"),
                    ],
                )
                .properties(height=min(40 * len(df_sorted) + 40, 400))
            )
            st.altair_chart(chart, width="stretch")

        # ═════════════════════════════════════════════════════════════════════
        # ALLOCATION TABLE (DataFrame with Progress Column)
        # ═════════════════════════════════════════════════════════════════════
        with c_table:
            # Remove raw value column for display
            display_df = df.drop(columns=["Valeur_brute"])

            st.dataframe(
                display_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Allocation": st.column_config.ProgressColumn(
                        "Poids (%)", min_value=0, max_value=100, format="%.1f%%"
                    )
                },
            )
    else:
        # Empty portfolio message
        st.info(
            "💡 Votre portefeuille est vide. Ajoutez des valorisations dans l'onglet correspondant."
        )

    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2b: PER-PRODUCT DETAIL SECTIONS
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("### 🔍 Détail par produit")

    for p in portfolio.products:
        if p.get("current_value_eur", 0) <= 0:
            continue

        product_id = p["id"]
        details = service.get_product_details(product_id)
        if not details or not details["history"]:
            continue

        with st.expander(f"**{p['name']}** — {format_eur(details['current_value'])}"):
            if details["type"] == "BITCOIN":
                _render_bitcoin_expander(details, product_id, service)
            else:
                _render_generic_expander(details)

    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3: EXPORTS & REPORTS
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("### 🖨️ Exports & Rapports")
    c1, c2, _ = st.columns([1, 1, 2])

    # ═══════════════════════════════════════════════════════════════════════════
    # PDF EXPORT
    # ═══════════════════════════════════════════════════════════════════════════

    with c1:
        # Cache key for PDF bytes in session state
        pdf_cache_key = "dashboard_pdf_bytes"

        if pdf_cache_key not in st.session_state:
            # First state: show generate button

            if st.button("⚙️ Préparer le rapport PDF", width="stretch"):
                with st.spinner("⏳ Génération du rapport PDF..."):
                    try:
                        # Build per-product chart data for PDF
                        chart_details = []
                        for p in portfolio.products:
                            if p.get("current_value_eur", 0) > 0:
                                d = service.get_product_details(p["id"])
                                if d and d.get("history") and len(d["history"]) >= 2:
                                    chart_details.append(d)

                        pdf_service = PDFReportService()
                        filepath = pdf_service.generate_report(portfolio, chart_details or None)

                        # Read and cache PDF bytes
                        with open(filepath, "rb") as f:
                            st.session_state[pdf_cache_key] = f.read()

                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        else:
            # Cached state: show download button
            st.download_button(
                "⬇️ Télécharger le PDF",
                data=st.session_state[pdf_cache_key],
                file_name="rapport_portefeuille.pdf",
                mime="application/pdf",
                type="primary",
                width="stretch",
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # JSON EXPORT
    # ═══════════════════════════════════════════════════════════════════════════

    with c2:
        # Cache key for JSON data in session state
        json_cache_key = "dashboard_json_bytes"

        if json_cache_key not in st.session_state:
            # First state: show generate button

            if st.button("⚙️ Préparer l'export JSON", width="stretch"):
                with st.spinner("⏳ Structuration des données..."):
                    try:
                        json_data = service.export_json(portfolio)
                        st.session_state[json_cache_key] = json_data
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        else:
            # Cached state: show download button
            st.download_button(
                "⬇️ Télécharger le JSON",
                data=st.session_state[json_cache_key],
                file_name="dashboard_data.json",
                mime="application/json",
                type="primary",
                width="stretch",
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # CACHE REFRESH BUTTON
    # ═══════════════════════════════════════════════════════════════════════════

    # Show refresh button only if there's cached data

    if pdf_cache_key in st.session_state or json_cache_key in st.session_state:
        if st.button("🔄 Rafraîchir les données d'export", type="secondary"):
            # Clear cached exports to force regeneration
            st.session_state.pop(pdf_cache_key, None)
            st.session_state.pop(json_cache_key, None)
            st.rerun()
