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
import html as _html
import streamlit as st
import os
from finance_tracker.web.db import get_session, get_db_path, get_engine
from finance_tracker.web.navigation import build_pages
from finance_tracker.repositories.sqlmodel_repo import init_db
from finance_tracker.services.seed_service import seed_default_products
from finance_tracker.i18n import t, detect_language, SUPPORTED_LANGS

# Used for linking to GitHub documentation from the UI
GITHUB_BASE_URL = "https://github.com/SKOHscripts/finance-tracker/blob/main"
LOGO_ICON_URL = "https://raw.githubusercontent.com/SKOHscripts/finance-tracker/main/images/logo-icon.svg"

# Must be called before any other Streamlit commands that modify the page
st.set_page_config(
    page_title="Finance Tracker",
    page_icon=LOGO_ICON_URL,
    layout="wide",
    initial_sidebar_state="expanded",
    )

# ── Language selection ─────────────────────────────────────────────────────────
# Detect browser preference on first load; allow manual override afterwards.
if "lang" not in st.session_state:
    st.session_state.lang = detect_language()

lang_choice = st.sidebar.selectbox(
    t("app.lang_selector"),
    options=SUPPORTED_LANGS,
    index=SUPPORTED_LANGS.index(st.session_state.lang),
    format_func=lambda x: "Français" if x == "fr" else "English",
    key="lang_select",
)
if lang_choice != st.session_state.lang:
    st.session_state.lang = lang_choice
    st.rerun()

st.sidebar.markdown("---")

# ── Logo ───────────────────────────────────────────────────────────────────────
# Create a right-aligned title using column layout
col1, col2 = st.columns([5, 2])

with col1:
    st.markdown("")

with col2:
    # get theme
    theme_type = st.context.theme.type

    if theme_type == "light":
        LOGO_URL = "https://raw.githubusercontent.com/SKOHscripts/finance-tracker/main/images/logo_horizontal_light.svg"
    else:
        LOGO_URL = "https://raw.githubusercontent.com/SKOHscripts/finance-tracker/main/images/logo_horizontal_dark.svg"

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
    st.sidebar.markdown(f"### {t('app.db_section')}")
    db_path = get_db_path()

    # IMPORT
    # Allow users to restore a previously exported database file
    uploaded_file = st.sidebar.file_uploader(t("app.import_label"), type=["db", "sqlite", "sqlite3"])

    if uploaded_file is not None and not st.session_state.get("db_loaded", False):
        with open(db_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.db_loaded = True
        st.sidebar.success(t("app.db_loaded_msg"))
        # Force Streamlit to re-run to proceed with the loaded database
        st.rerun()

    # INITIALISATION IF EMPTY
    # Create a fresh database if none exists

    if not os.path.exists(db_path):
        if st.sidebar.button(t("app.create_portfolio_btn")):
            # Each user gets their own database instance via dynamic engine
            engine = get_engine()
            init_db(engine)

            # Seed default products for new databases
            _session = get_session()
            created_count = seed_default_products(_session)
            _session.close()

            st.session_state.db_loaded = True

            if created_count > 0:
                st.sidebar.success(t("app.db_init_with_products").format(n=created_count))
            else:
                st.sidebar.success(t("app.db_init"))

            st.rerun()

        # Animated ↖ arrow pointing at the sidebar toggle, shown only while the
        # sidebar is collapsed and after 20 s of inactivity. Pure CSS — no JS, no
        # iframe (st.components.v1.html is deprecated and its timers die on every
        # Streamlit re-render, which is why earlier JS versions never appeared).
        #
        # In Streamlit 1.57 the sidebar <section data-testid="stSidebar"> carries
        # aria-expanded="false" when collapsed and "true" when open. The :has()
        # selector below shows the hint only when collapsed, so it disappears the
        # instant the user opens the sidebar. animation-delay handles the 20 s wait.
        hint_label = _html.escape(t("app.sidebar_hint"))
        st.markdown(
            "<style>"
            "#_sb_hint{position:fixed;top:68px;left:44px;z-index:99999;display:none;"
            "flex-direction:column;align-items:flex-start;gap:3px;pointer-events:none;opacity:0}"
            'body:has(section[data-testid="stSidebar"][aria-expanded="false"]) #_sb_hint{'
            "display:flex;animation:sb-reveal .4s ease-out 20s forwards}"
            "@keyframes sb-reveal{to{opacity:1}}"
            "#_sb_hint ._a{font-size:22px;color:#0088ff;line-height:1;"
            "animation:sb-bounce 1.1s ease-in-out infinite}"
            "@keyframes sb-bounce{0%,100%{transform:translate(0,0)}50%{transform:translate(-9px,-9px)}}"
            "#_sb_hint ._t{background:#0088ff;color:#fff;padding:3px 9px;border-radius:10px;"
            "font-size:11px;white-space:nowrap;font-family:sans-serif;font-weight:600;"
            "box-shadow:0 2px 6px rgba(0,136,255,.4)}"
            "</style>"
            '<div id="_sb_hint"><div class="_a">&#x2196;</div>'
            f'<div class="_t">{hint_label}</div></div>',
            unsafe_allow_html=True,
        )

        # Show documentation (needs no DB) so users aren't stranded on a blank page
        from finance_tracker.web.views.documentation import render as doc_render
        doc_render(None)
        st.stop()

    # EXPORT
    # Provide a way to backup the current database state

    if os.path.exists(db_path):
        with open(db_path, "rb") as f:
            st.sidebar.download_button(
                label=t("app.export_btn"),
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

# Use stable page IDs in the radio widget so the selected page survives language changes.
selected_id = st.sidebar.radio(
    t("app.nav_label"),
    options=[p.id for p in pages],
    format_func=lambda pid: next(p.label for p in pages if p.id == pid),
)
# donation button
donate_url = "https://html-preview.github.io/?url=https://github.com/SKOHscripts/donate.github.io/blob/main/donate%2Fredirect.html"
st.sidebar.markdown(f"""
<div style="margin: 0.5rem 0;">
  <a href="{donate_url}" target="_blank" style="
    display: block;
    background: linear-gradient(135deg, #c67c2d 0%, #e8943a 100%);
    color: white;
    text-align: center;
    padding: 0.6rem 1rem;
    border-radius: 8px;
    text-decoration: none;
    font-weight: bold;
    font-size: 0.9rem;
    border: 1px solid #f0a545;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
  ">{t("app.donate_btn")}</a>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

st.sidebar.info(f"**{t('app.sidebar_version')}**\n\n{t('app.sidebar_description')}")

# 3. Render the selected navigation page with database access
page = next(p for p in pages if p.id == selected_id)
page.render(session)
