"""
Bitcoin Valuation Management Module

This module provides a Streamlit interface for managing Bitcoin valuations within a finance tracking application.
It allows users to fetch the latest Bitcoin price in EUR from an external API, display it, and create new valuations
associated with the Bitcoin product in the database. It integrates with various components such as repositories
for data access, services for fetching prices, and UI formatters for displaying data.

The main entry point is the `render` function which takes a database session and renders the UI accordingly.
"""
import streamlit as st
from datetime import datetime
from sqlmodel import Session

from finance_tracker.domain.models import Valuation
from finance_tracker.repositories.sqlmodel_repo import SQLModelProductRepository, SQLModelValuationRepository
from finance_tracker.services.btc_price_service import BTCPriceService, BTCPriceServiceError
from finance_tracker.web.ui.formatters import to_decimal


def render(session: Session) -> None:
    """
    Display the Bitcoin valuation management interface.

    This function allows viewing the current Bitcoin price in EUR,
    refreshing it via an external API, and creating a new valuation
    associated with the Bitcoin product in the database.

    Parameters
    ----------
    session : Session
        Database session used for read and write operations.

    Returns
    -------
    None
        No return value, the function updates the Streamlit interface.

    Raises
    ------
    BTCPriceServiceError
        If an error occurs while retrieving the Bitcoin price via the API.
    """
    # Display the Bitcoin management section header
    st.header("Gestion Bitcoin")

    # Retrieve the Bitcoin product from the database
    product_repo = SQLModelProductRepository(session)
    btc_product = product_repo.get_by_name("Bitcoin")

    # Exit early if Bitcoin product is not found

    if not btc_product:
        st.error("Produit Bitcoin non trouvé")

        return

    # Display current BTC/EUR price section
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Prix BTC/EUR actuel")
    with col2:
        # Button to refresh the BTC price from external API

        if st.button("🔄 Rafraîchir", key="btc_refresh"):
            btc_service = BTCPriceService()
            try:
                price = btc_service.get_btc_price_eur()
                st.session_state.btc_price = price
            except BTCPriceServiceError as e:
                st.error(f"❌ Erreur API : {e}")

    # Show the current BTC price if available

    if "btc_price" in st.session_state:
        st.metric("Prix BTC/EUR", f"{st.session_state.btc_price}€")
    else:
        st.info("Cliquez sur 'Rafraîchir' pour récupérer le prix")

    # Separator before the valuation creation form
    st.markdown("---")
    st.subheader("Créer valorisation BTC")

    # Input fields for BTC valuation details
    col1, col2 = st.columns(2)
    with col1:
        btc_total_value = st.number_input("Valeur totale EUR", value=0.0, step=1.0)
    with col2:
        btc_unit_price = st.number_input("Prix par BTC EUR", value=0.0, step=1.0)

    # Handle valuation creation when button is clicked

    if st.button("💾 Créer valorisation BTC"):
        try:
            val_repo = SQLModelValuationRepository(session)
            val = Valuation(
                product_id=btc_product.id or 0,
                date=datetime.utcnow(),
                total_value_eur=to_decimal(btc_total_value),
                unit_price_eur=to_decimal(btc_unit_price) if btc_unit_price > 0 else None,
            )
            val_repo.create(val)
            st.success("✅ Valorisation BTC créée")
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
