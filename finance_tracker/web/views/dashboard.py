"""
Finance Tracker Dashboard Module
"""
import streamlit as st
import pandas as pd
import altair as alt

from sqlmodel import Session
from finance_tracker.services.dashboard_service import DashboardService
from finance_tracker.services.pdf_report_service import PDFReportService
from finance_tracker.web.ui.formatters import format_eur


def render(session: Session) -> None:
    st.title("📊 Tableau de bord")
    st.caption("Aperçu global et performances de votre portefeuille d'investissement.")

    service = DashboardService(session)
    try:
        portfolio = service.build_portfolio()
    except Exception as e:
        st.error(f"Impossible de charger le portefeuille : {e}")

        return

    # --- KPIs ---
    st.markdown("### 📈 Vue d'ensemble")
    perf_pct = (
        float(portfolio.total_gains_eur / portfolio.total_invested_eur * 100)

        if portfolio.total_invested_eur > 0
        else 0
    )

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

    # --- Tableau et graphique d'allocation ---
    st.markdown("### 🧩 Répartition du portefeuille")

    rows = []

    for p in portfolio.products:
        if p.get("current_value_eur", 0) > 0 or p.get("net_contributions_eur", 0) > 0:
            rows.append(
                {
                    "Produit": p["name"],
                    "Valeur_brute": float(p["current_value_eur"]),
                    "Valeur": f"{float(p['current_value_eur']):.2f} €",
                    "Investi": f"{float(p['net_contributions_eur']):.2f} €",
                    "Gains": f"{float(p['performance_eur']):.2f} €",
                    "Perf %": f"{float(p['performance_pct']):.2f} %",
                    "Allocation": float(p["allocation_pct"]),
                }
            )

    if rows:
        df = pd.DataFrame(rows)
        df_sorted = df.sort_values("Allocation", ascending=True)

        c_chart, c_table = st.columns([1, 1.6])

        with c_chart:
            # Barres horizontales d'allocation via Altair (déjà dépendance du projet)
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
                        sort=None,
                        title="",
                        axis=alt.Axis(labelLimit=150),
                    ),
                    color=alt.Color(
                        "Produit:N",
                        legend=None,
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

        with c_table:
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
        st.info(
            "💡 Votre portefeuille est vide. Ajoutez des valorisations dans l'onglet correspondant."
        )

    st.markdown("---")

    # --- Exports ---
    st.markdown("### 🖨️ Exports & Rapports")
    c1, c2, _ = st.columns([1, 1, 2])

    with c1:
        if st.button("📄 Générer un rapport PDF", width="stretch"):
            with st.spinner("Génération du rapport en cours..."):
                try:
                    pdf_service = PDFReportService()
                    filepath = pdf_service.generate_report(portfolio)
                    with open(filepath, "rb") as f:
                        st.download_button(
                            "⬇️ Télécharger le PDF",
                            data=f.read(),
                            file_name="rapport_portefeuille.pdf",
                            mime="application/pdf",
                            type="primary",
                            width="stretch",
                        )
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")

    with c2:
        if st.button("💾 Exporter la Data (JSON)", width="stretch"):
            try:
                json_data = service.export_json(portfolio)
                st.download_button(
                    "⬇️ Télécharger le JSON",
                    data=json_data,
                    file_name="dashboard_data.json",
                    mime="application/json",
                    type="primary",
                    width="stretch",
                )
            except Exception as e:
                st.error(f"❌ Erreur : {e}")
