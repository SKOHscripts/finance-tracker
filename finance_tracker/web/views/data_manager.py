import streamlit as st
from datetime import datetime, date
from sqlmodel import Session

from finance_tracker.domain.enums import ProductType, QuantityUnit, TransactionType
from finance_tracker.domain.models import Product, Transaction, Valuation
from finance_tracker.repositories.sqlmodel_repo import (
    SQLModelProductRepository,
    SQLModelTransactionRepository,
    SQLModelValuationRepository,
)
from finance_tracker.web.ui.formatters import to_decimal


def render(session: Session) -> None:
    """Affiche le gestionnaire de données centralisé (Ajout & Édition)"""
    st.title("🗂️ Gestion des Données")
    st.markdown("Ajoutez de nouveaux éléments à votre portefeuille ou modifiez l'historique existant.")

    # Séparation en deux onglets principaux pour plus de clarté
    tab_add, tab_edit = st.tabs(["➕ Ajouter", "✏️ Éditer l'historique"])

    with tab_add:
        _render_add_tab(session)

    with tab_edit:
        _render_edit_tab(session)


def _render_add_tab(session: Session) -> None:
    entity_to_add = st.radio(
        "Que souhaitez-vous ajouter ?",
        ["Transaction", "Valorisation", "Nouveau Produit"],
        horizontal=True
    )

    # Ligne de séparation esthétique
    st.markdown("---")

    if entity_to_add == "Transaction":
        _add_transaction_form(session)
    elif entity_to_add == "Valorisation":
        _add_valuation_form(session)
    else:
        _add_product_form(session)


def _render_edit_tab(session: Session) -> None:
    entity_to_edit = st.radio(
        "Que souhaitez-vous éditer ?",
        ["Transactions", "Valorisations", "Produits"],
        horizontal=True,
        key="radio_edit"
    )

    st.markdown("---")

    # Nous appelons ici les fonctions d'édition issues de votre fichier products.py d'origine
    # (Supposant que vous avez gardé les fonctions _edit_transactions, etc.)
    from finance_tracker.web.views.products import (
        _edit_transactions,
        _edit_valuations,
        _edit_products
    )

    if entity_to_edit == "Transactions":
        _edit_transactions(session)
    elif entity_to_edit == "Valorisations":
        _edit_valuations(session)
    else:
        _edit_products(session)


# ==========================================
# SOUS-FORMULAIRES D'AJOUT
# ==========================================

def _add_transaction_form(session: Session) -> None:
    product_repo = SQLModelProductRepository(session)
    tx_repo = SQLModelTransactionRepository(session)
    products = product_repo.get_all()

    if not products:
        st.warning("⚠️ Aucun produit disponible. Veuillez d'abord créer un produit.")

        return

    # Utilisation d'un formulaire pour regrouper les saisies visuellement
    with st.form("form_add_transaction", clear_on_submit=True):
        st.subheader("Nouvelle Transaction")

        col1, col2 = st.columns(2)
        with col1:
            product_name = st.selectbox("Produit", [p.name for p in products])
            tx_type = st.selectbox("Type", list(TransactionType), format_func=lambda e: e.value)
            tx_date = st.date_input("Date", value=date.today())

        with col2:
            amount = st.number_input("Montant EUR", value=0.0, step=10.0)
            quantity = st.number_input("Quantité (parts/sats)", value=0.0, step=1.0)
            note = st.text_input("Note (optionnel)")

        submitted = st.form_submit_button("➕ Ajouter la transaction", use_container_width=True)

        if submitted:
            try:
                product = product_repo.get_by_name(product_name)
                tx = Transaction(
                    product_id=product.id,
                    date=datetime.combine(tx_date, datetime.min.time()),
                    type=tx_type,
                    amount_eur=to_decimal(amount) if amount > 0 else None,
                    quantity=to_decimal(quantity) if quantity > 0 else None,
                    note=note,
                )
                tx_repo.create(tx)
                st.success(f"✅ Transaction ajoutée avec succès sur {product_name} !")
            except Exception as e:
                st.error(f"❌ Erreur : {e}")


def _add_valuation_form(session: Session) -> None:
    product_repo = SQLModelProductRepository(session)
    val_repo = SQLModelValuationRepository(session)
    products = product_repo.get_all()

    if not products:
        st.warning("⚠️ Aucun produit disponible. Veuillez d'abord créer un produit.")

        return

    with st.form("form_add_valuation", clear_on_submit=True):
        st.subheader("Nouvelle Valorisation")

        col1, col2 = st.columns(2)
        with col1:
            product_name = st.selectbox("Produit", [p.name for p in products])
            val_date = st.date_input("Date du snapshot", value=date.today())

        with col2:
            total_value = st.number_input("Valeur totale (EUR)", value=0.0, step=100.0)
            unit_price = st.number_input("Prix unitaire optionnel (EUR)", value=0.0, step=1.0)

        submitted = st.form_submit_button("📈 Enregistrer la valorisation", use_container_width=True)

        if submitted:
            try:
                product = product_repo.get_by_name(product_name)
                val = Valuation(
                    product_id=product.id,
                    date=datetime.combine(val_date, datetime.min.time()),
                    total_value_eur=to_decimal(total_value),
                    unit_price_eur=to_decimal(unit_price) if unit_price > 0 else None,
                )
                val_repo.create(val)
                st.success(f"✅ Valorisation de {total_value}€ ajoutée pour {product_name} !")
            except Exception as e:
                st.error(f"❌ Erreur : {e}")


def _add_product_form(session: Session) -> None:
    product_repo = SQLModelProductRepository(session)

    with st.form("form_add_product", clear_on_submit=True):
        st.subheader("Nouveau Produit Financier")

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nom du produit *")
            product_type = st.selectbox("Catégorie", list(ProductType), format_func=lambda e: e.value)
            quantity_unit = st.selectbox("Unité", list(QuantityUnit), format_func=lambda e: e.value)
            risk_level = st.text_input("Niveau de risque (1 à 7)")

        with col2:
            description = st.text_area("Description", height=68)
            fees_description = st.text_area("Structure de frais", height=68)
            tax_info = st.text_area("Règles fiscales", height=68)

        submitted = st.form_submit_button("💾 Créer le produit", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("Le nom du produit est obligatoire.")
            elif product_repo.get_by_name(name):
                st.error(f"Un produit nommé '{name}' existe déjà.")
            else:
                try:
                    product = Product(
                        name=name, type=product_type, quantity_unit=quantity_unit,
                        description=description or None, risk_level=risk_level or None,
                        fees_description=fees_description or None, tax_info=tax_info or None,
                    )
                    product_repo.create(product)
                    st.success(f"✅ Produit '{name}' créé avec succès !")
                except Exception as e:
                    st.error(f"❌ Erreur lors de la création : {e}")
