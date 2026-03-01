"""
Finance Tracker Dashboard Module
"""
# Third-party imports (par ordre alphabétique)
import altair as alt
import pandas as pd
from sqlmodel import Session
import streamlit as st

# Local imports (par ordre alphabétique)
from finance_tracker.services.dashboard_service import DashboardService
from finance_tracker.services.pdf_report_service import PDFReportService
from finance_tracker.web.ui.formatters import format_eur


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
                        pdf_service = PDFReportService()
                        filepath = pdf_service.generate_report(portfolio)

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
