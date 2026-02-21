"""
Bitcoin Valuation Management Module
"""
import streamlit as st
from datetime import datetime, date

from sqlmodel import Session
from finance_tracker.domain.models import Valuation
from finance_tracker.repositories.sqlmodel_repo import SQLModelProductRepository, SQLModelValuationRepository
from finance_tracker.services.btc_price_service import BTCPriceService, BTCPriceServiceError
from finance_tracker.web.ui.formatters import to_decimal


def render(session: Session) -> None:
    st.title("₿ Espace Bitcoin")
    st.caption("Consultez le cours en temps réel et mettez à jour votre valorisation.")

    product_repo = SQLModelProductRepository(session)
    btc_product = product_repo.get_by_name("Bitcoin")

    if not btc_product:
        st.warning("⚠️ Le produit 'Bitcoin' n'existe pas dans votre portefeuille. Veuillez le créer dans l'onglet 'Produits'.")

        return

    # --- Section Marché en Direct ---
    st.markdown("### 🌐 Marché en direct")

    # Boîte grise pour le style
    with st.container():
        c1, c2, c3 = st.columns([1.5, 2, 1])

        with c1:
            if "btc_price" in st.session_state:
                st.metric(label="Cours BTC/EUR", value=f"{st.session_state.btc_price:,.2f} €".replace(',', ' '))
            else:
                st.metric(label="Cours BTC/EUR", value="--- €")

        with c2:
            st.write("")  # Espace vertical

            if st.button("🔄 Actualiser le cours actuel", use_container_width=True):
                with st.spinner("Interrogation de l'API..."):
                    try:
                        btc_service = BTCPriceService()
                        st.session_state.btc_price = btc_service.get_btc_price_eur()
                        st.rerun()
                    except BTCPriceServiceError as e:
                        st.error(f"❌ Erreur API : {e}")

        with c3:
            # Petite image ou logo symbolique (si besoin)
            st.markdown("<h1 style='text-align: center; color: #F7931A;'>₿</h1>", unsafe_allow_html=True)

    st.markdown("---")

    # --- Formulaire d'ajout de snapshot ---
    st.markdown("### 📸 Enregistrer un nouveau Snapshot")
    st.write("Ajoutez une nouvelle valorisation pour votre ligne Bitcoin.")

    with st.form("btc_val_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)

        with c1:
            val_date = st.date_input("Date du snapshot", value=date.today())
        with c2:
            # Si on a le prix, on l'utilise comme valeur par défaut pour faciliter la saisie
            default_price = float(st.session_state.get("btc_price", 0.0))
            btc_unit_price = st.number_input("Prix d'un BTC (EUR)", value=default_price, step=100.0)
        with c3:
            btc_quantity = st.number_input("Quantité possédée (Nb de BTC)", value=0.0, step=0.01, format="%.8f")

        submit = st.form_submit_button("💾 Enregistrer la valorisation dans l'historique", type="primary", use_container_width=True)

        if submit:
            if btc_quantity <= 0 or btc_unit_price <= 0:
                st.error("La quantité et le prix unitaire doivent être supérieurs à 0.")
            else:
                try:
                    val_repo = SQLModelValuationRepository(session)
                    total_val = btc_quantity * btc_unit_price

                    val = Valuation(
                        product_id=btc_product.id,
                        date=datetime.combine(val_date, datetime.min.time()),
                        total_value_eur=to_decimal(total_val),
                        unit_price_eur=to_decimal(btc_unit_price)
                    )
                    val_repo.create(val)
                    st.success(f"✅ Valorisation ajoutée avec succès ! (Valeur totale : {total_val:,.2f} €)")
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'enregistrement : {e}")
