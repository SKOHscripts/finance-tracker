"""
Main module of the Finance Tracker application.

This module configures and launches the user interface of the financial tracking application
using Streamlit. It initializes the database session, sets up navigation
between the different pages of the application, and displays the main interface elements
such as the title, navigation bar, and contextual information.

The application allows for complete management of an investment portfolio including
support for SCPIs, cryptocurrencies like Bitcoin, savings accounts, and other
financial assets.
"""
import streamlit as st

from finance_tracker.web.db import get_session
from finance_tracker.web.navigation import build_pages

# Configure the Streamlit page with title, icon, and layout
st.set_page_config(
    page_title="Finance Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
    )

# Display the main title and description
st.title("💰 Finance Tracker")
st.markdown("Gestion complète de votre portefeuille d'investissement")

# Initialize database session for the application
session = get_session()

# Add a visual separator in the sidebar
st.sidebar.markdown("---")

# Build navigation pages and extract their labels
pages = build_pages()
labels = [p.label for p in pages]

# Create sidebar navigation radio buttons
selected = st.sidebar.radio("Navigation", labels)

# Add another visual separator in the sidebar
st.sidebar.markdown("---")

# Display application information in the sidebar
st.sidebar.info(
    "**Finance Tracker v0.1.0**\n\n"
    "Outil de suivi de portefeuille avec support SCPI, Bitcoin, épargne et plus."
    )

# Find and render the selected page
page = next(p for p in pages if p.label == selected)
page.render(session)
