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
from finance_tracker.services.seed_service import seed_default_products

# Used for linking to GitHub documentation from the UI
GITHUB_BASE_URL = "https://github.com/SKOHscripts/finance-tracker/blob/main"
LOGO_ICON_URL = "https://raw.githubusercontent.com/SKOHscripts/finance-tracker/main/images/logo_monochrome_64x64.png"

# Must be called before any other Streamlit commands that modify the page
st.set_page_config(
    page_title="Finance Tracker",
    page_icon=LOGO_ICON_URL,
    layout="wide",
    initial_sidebar_state="expanded",
    )

# Create a right-aligned title using column layout
col1, col2 = st.columns([5, 2])

with col1:
    st.markdown("")

with col2:
    # get theme
    theme_type = st.context.theme.type

    if theme_type == "light":
        LOGO_URL = "https://raw.githubusercontent.com/SKOHscripts/finance-tracker/main/images/logo_color_horizontal_white.png"
    else:
        LOGO_URL = "https://raw.githubusercontent.com/SKOHscripts/finance-tracker/main/images/logo_color_horizontal.png"

    st.markdown(
        f'<a href="{GITHUB_BASE_URL}/README.md" target="_blank" '
        f'title="Voir le projet">'
        f'<img src="{LOGO_URL}" height="80" style="vertical-align:middle;"></a>',
        unsafe_allow_html=True
        )


def render_db_manager():
    """Manage database lifecycle operations in the sidebar.

    Handles importing, creating, and exporting SQLite database files for the application.
    Also seeds default products when creating a new database.
    """
    st.sidebar.markdown("### 💾 Gestion des Données")
    db_path = get_db_path()

    # IMPORT
    # Allow users to restore a previously exported database file
    uploaded_file = st.sidebar.file_uploader("Importer votre sauvegarde (.db)", type=["db", "sqlite", "sqlite3"])

    if uploaded_file is not None and not st.session_state.get("db_loaded", False):
        with open(db_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.db_loaded = True
        st.sidebar.success("Base de données chargée !")
        # Force Streamlit to re-run to proceed with the loaded database
        st.rerun()

    # INITIALISATION IF EMPTY
    # Create a fresh database if none exists

    if not os.path.exists(db_path):
        if st.sidebar.button("Créer un nouveau portefeuille"):
            # Each user gets their own database instance via dynamic engine
            engine = get_engine()
            init_db(engine)

            # Seed default products for new databases
            session = get_session()
            created_count = seed_default_products(session)
            session.close()

            st.session_state.db_loaded = True

            if created_count > 0:
                st.sidebar.success(f"✅ Base initialisée avec {created_count} produits par défaut")
            else:
                st.sidebar.success("✅ Base initialisée")

            st.rerun()

        st.warning("Veuillez importer ou créer une base pour commencer.")
        # Stop execution here - no point loading the rest of the app without a database
        st.stop()

    # EXPORT
    # Provide a way to backup the current database state

    if os.path.exists(db_path):
        with open(db_path, "rb") as f:
            st.sidebar.download_button(
                label="📥 Sauvegarder la base (PC)",
                data=f,
                file_name="finance_tracker_backup.db",
                mime="application/octet-stream"
                )


# 1. Validate and setup database before any page logic runs
render_db_manager()

# 2. At this point, database is guaranteed to exist (st.stop() would have blocked otherwise)
# Safe to create a session for database queries
session = get_session()

st.sidebar.markdown("---")
pages = build_pages()
labels = [p.label for p in pages]
selected = st.sidebar.radio("Navigation", labels)
st.sidebar.link_button(
    "📖 Documentation (README)",
    f"{GITHUB_BASE_URL}/README.md",
    )
st.sidebar.markdown("---")

# donation button
st.sidebar.link_button(
    "☕ Buy me a Bitcoffee",
    "https://html-preview.github.io/?url=https://github.com/SKOHscripts/donate.github.io/blob/main/donate%2Fredirect.html"
    )
st.sidebar.markdown("---")

st.sidebar.info("**Finance Tracker v1.0.0**\n\nOutil de suivi de portefeuille avec support SCPI, Bitcoin, épargne et plus.")

# 3. Render the selected navigation page with database access
page = next(p for p in pages if p.label == selected)
page.render(session)
