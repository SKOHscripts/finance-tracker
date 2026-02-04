"""
Finance Tracker Dashboard Module

This module implements the main dashboard interface for the finance tracker application.
It provides a comprehensive overview of a user's investment portfolio, displaying key
metrics such as total value, invested amount, gains, and performance percentage.

The dashboard is built using Streamlit and presents data in an organized manner:
- Key portfolio metrics at the top
- Detailed product breakdown with current value, investments, gains, and allocation
- Additional information like available cash and product count
- Export functionality to download portfolio data as JSON

The module relies on the DashboardService to fetch and process portfolio data,
and uses UI formatters for proper currency display.
"""

import streamlit as st
from sqlmodel import Session

from finance_tracker.services.dashboard_service import DashboardService
from finance_tracker.services.pdf_report_service import PDFReportService
from finance_tracker.web.ui.formatters import format_eur


def render(session: Session) -> None:
    """
    Display the portfolio dashboard.

    This function generates the dashboard user interface, including key metrics,
    product details, and export options.

    Parameters
    ----------
    session : Session
        User session containing authentication information.

    Returns
    -------
    None
        Directly displays the dashboard in the Streamlit interface.

    Raises
    ------
    Exception
        If an error occurs while constructing the portfolio or displaying it.
    """
    st.header("Tableau de bord")

    # Initialize the service and build the portfolio data
    service = DashboardService(session)
    portfolio = service.build_portfolio()

    # Display key portfolio metrics in a horizontal row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Valeur Totale", format_eur(portfolio.total_value_eur))
    with col2:
        st.metric("Investi", format_eur(portfolio.total_invested_eur))
    with col3:
        st.metric("Gains", format_eur(portfolio.total_gains_eur))
    with col4:
        # Calculate performance percentage; avoid division by zero
        perf_pct = float(portfolio.total_gains_eur / portfolio.total_invested_eur * 100) if portfolio.total_invested_eur > 0 else 0
        st.metric("Performance %", f"{perf_pct:.2f}%")

    st.markdown("---")
    st.subheader("Détail par produit")

    # Prepare rows for the product details table
    rows = []

    for p in portfolio.products:
        # Only include products with value or contributions

        if p.get("current_value_eur", 0) > 0 or p.get("net_contributions_eur", 0) > 0:
            rows.append({
                "Produit": p["name"],
                "Valeur": f"{float(p['current_value_eur']):.2f}€",
                "Investi": f"{float(p['net_contributions_eur']):.2f}€",
                "Gains": f"{float(p['performance_eur']):.2f}€",
                "Perf %": f"{float(p['performance_pct']):.2f}%",
                "Allocation %": f"{float(p['allocation_pct']):.2f}%",
                })

    # Display product details or a message if none exist

    if rows:
        st.dataframe(rows, width="stretch")
    else:
        st.info("Aucun produit avec valorisation")

    st.markdown("---")
    # Display additional portfolio information
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Cash disponible", format_eur(portfolio.cash_available))
    with col2:
        st.metric("Nombre de produits", len(portfolio.products))

    # Provide JSON export functionality

    if st.button("📥 Exporter données en JSON"):
        json_data = service.export_json(portfolio)
        st.download_button(
            label="Télécharger JSON",
            data=json_data,
            file_name="dashboard.json",
            mime="application/json",
            )

    if st.button("📥 Générer PDF"):
        try:
            # Generate the PDF report using the portfolio data
            pdf_service = PDFReportService()
            filepath = pdf_service.generate_report(portfolio)
            st.success(f"✅ PDF généré : {filepath}")

            # Provide a download button for the generated PDF
            with open(filepath, "rb") as f:
                st.download_button(
                    label="⬇️ Télécharger le PDF",
                    data=f.read(),
                    file_name=filepath.split("/")[-1],
                    mime="application/pdf",
                    )
        except Exception as e:
            # Display any error that occurs during PDF generation
            st.error(f"❌ Erreur : {e}")
