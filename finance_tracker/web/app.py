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
import os
from finance_tracker.web.db import get_session, get_db_path, get_engine
from finance_tracker.web.navigation import build_pages
from finance_tracker.repositories.sqlmodel_repo import init_db

st.set_page_config(page_title="Finance Tracker", page_icon="💰", layout="wide", initial_sidebar_state="expanded")

st.title("💰 Finance Tracker")
st.markdown("Gestion complète de votre portefeuille d'investissement")


def render_db_manager():
    st.sidebar.markdown("### 💾 Gestion des Données")
    db_path = get_db_path()

    # IMPORT
    uploaded_file = st.sidebar.file_uploader("Importer votre sauvegarde (.db)", type=["db", "sqlite", "sqlite3"])

    if uploaded_file is not None and not st.session_state.get("db_loaded", False):
        with open(db_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.db_loaded = True
        st.sidebar.success("Base de données chargée !")
        st.rerun()

    # INITIALISATION SI VIDE

    if not os.path.exists(db_path):
        if st.sidebar.button("Créer un nouveau portefeuille"):
            # Il est très important de passer l'engine dynamique à init_db
            engine = get_engine()
            init_db(engine)
            st.session_state.db_loaded = True
            st.rerun()

        st.warning("Veuillez importer ou créer une base pour commencer.")
        st.stop()  # <-- Empêche l'exécution de la suite si pas de base

    # EXPORT

    if os.path.exists(db_path):
        with open(db_path, "rb") as f:
            st.sidebar.download_button(
                label="📥 Sauvegarder la base (PC)",
                data=f,
                file_name="finance_tracker_backup.db",
                mime="application/octet-stream"
            )


# 1. On exécute le gestionnaire de base de données
render_db_manager()

# 2. Si on arrive ici, c'est que la base existe (sinon st.stop() a bloqué plus haut).
# On peut donc ouvrir la session en toute sécurité.
session = get_session()

st.sidebar.markdown("---")
pages = build_pages()
labels = [p.label for p in pages]
selected = st.sidebar.radio("Navigation", labels)
st.sidebar.markdown("---")

st.sidebar.info("**Finance Tracker v0.1.0**\n\nOutil de suivi de portefeuille avec support SCPI, Bitcoin, épargne et plus.")

# 3. On rend la page
page = next(p for p in pages if p.label == selected)
page.render(session)
