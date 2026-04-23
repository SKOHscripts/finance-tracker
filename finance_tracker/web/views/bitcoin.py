"""
Bitcoin — Page de transition.
Le contenu Bitcoin a été intégré dans le Tableau de Bord (section "Détail par produit").
"""
import streamlit as st
from sqlmodel import Session


def render(session: Session) -> None:
    """Render the Bitcoin transition page."""
    st.title("₿ Espace Bitcoin")
    st.info(
        "**Cette page a été fusionnée dans le Tableau de Bord.**\n\n"
        "Toutes les fonctionnalités Bitcoin sont désormais accessibles depuis "
        "**📊 Tableau de Bord → 🔍 Détail par produit → Bitcoin** :\n\n"
        "- 🔴 Cours live BTC/EUR avec badge LIVE / OFFLINE\n"
        "- 📦 Quantité en Satoshis\n"
        "- 📌 PRU et 📈 P&L latente\n"
        "- 📉 Historique des prix (snapshots)\n"
        "- 📸 Formulaire de nouveau snapshot\n"
        "- 🗓️ Tableau des derniers snapshots"
    )
    st.markdown("➡️ Rendez-vous dans **📊 Tableau de Bord** pour accéder à votre espace Bitcoin.")
