"""
Bitcoin — Page de transition.
Le contenu Bitcoin a été intégré dans le Tableau de Bord (section "Détail par produit").
"""
import streamlit as st
from sqlmodel import Session

from finance_tracker.i18n import t


def render(session: Session) -> None:
    """Render the Bitcoin transition page."""
    st.title(t("bitcoin.title"))
    st.info(t("bitcoin.redirect_info"))
    st.markdown(t("bitcoin.redirect_link"))
