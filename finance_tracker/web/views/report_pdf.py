"""
Module report_pdf.py

This module provides functionality for generating and downloading a PDF report of a user's financial portfolio.
It integrates with Streamlit to render an interactive interface where users can trigger the creation of a detailed
PDF document containing portfolio summary, asset details, and performance metrics. The module relies on services
from the finance tracker application to build the portfolio and generate the PDF content.
"""
import streamlit as st
from sqlmodel import Session

from finance_tracker.services.dashboard_service import DashboardService
from finance_tracker.services.pdf_report_service import PDFReportService


def render(session: Session) -> None:
    """
    Render the PDF generation interface and handle report creation.

    This function displays the PDF generation section, builds the user's portfolio,
    and manages the PDF creation and download process upon user interaction.

    Parameters
    ----------
    session : Session
        The user session containing necessary data to build the portfolio.

    Returns
    -------
    None
        This function does not return any value.

    Raises
    ------
    Exception
        If an error occurs during PDF generation, it will be caught and displayed.
    """
    # Display the PDF generation section header
    st.header("Générer un rapport PDF")

    # Build the user's portfolio using the dashboard service
    service = DashboardService(session)
    portfolio = service.build_portfolio()

    # Inform the user about the PDF report content
    st.info("Générez un PDF complet de votre portefeuille avec résumé, détails et performances.")

    # Trigger PDF generation on button click

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
