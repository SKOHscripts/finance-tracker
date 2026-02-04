"""
products.py

This module provides Streamlit UI components for managing financial products within the Finance Tracker application.
It includes functionality for adding new products, editing existing product details, and modifying related
transactions and valuations. The module interacts with a SQLModel-based repository layer to perform database
operations and ensures data integrity through user input validation.

Key features:
- Add new financial products with type, unit, and optional metadata
- Edit or delete existing transactions and valuations
- Modify product information such as name, description, risk level, fees, and tax info
"""

import streamlit as st
from sqlmodel import Session

from finance_tracker.domain.enums import ProductType, QuantityUnit, TransactionType
from finance_tracker.domain.models import Product
from finance_tracker.repositories.sqlmodel_repo import (
    SQLModelProductRepository,
    SQLModelTransactionRepository,
    SQLModelValuationRepository,
    )
from finance_tracker.web.ui.formatters import to_decimal


def render_add(session: Session) -> None:
    """
    Render the user interface for adding a new product.

    This function displays input fields for product details and handles the creation process.

    Parameters
    ----------
    session : Session
        The database session used for product operations.

    Returns
    -------
    None

    Raises
    ------
    Exception
        If an error occurs during product creation or validation.
    """
    st.header("Ajouter un nouveau produit")

    # Initialize repository for product operations
    product_repo = SQLModelProductRepository(session)

    # Collect product details from user input
    name = st.text_input("Nom du produit")
    product_type = st.selectbox("Type de produit", list(ProductType), format_func=lambda e: e.value)
    quantity_unit = st.selectbox("Unité de quantité", list(QuantityUnit), format_func=lambda e: e.value)
    description = st.text_area("Description (optionnel)", height=80)
    risk_level = st.text_input("Niveau de risque (optionnel)", value="")
    fees_description = st.text_area("Frais (optionnel)", height=80)
    tax_info = st.text_area("Fiscalité (optionnel)", height=80)

    # Handle product creation on button click

    if st.button("💾 Créer le produit"):
        try:
            # Validate that product name is provided

            if not name.strip():
                st.error("Le nom du produit est obligatoire.")

                return

            # Check for duplicate product name
            existing = product_repo.get_by_name(name)

            if existing:
                st.error(f"Un produit nommé '{name}' existe déjà.")

                return

            # Create and save new product
            product = Product(
                name=name,
                type=product_type,
                quantity_unit=quantity_unit,
                description=description or None,
                risk_level=risk_level or None,
                fees_description=fees_description or None,
                tax_info=tax_info or None,
                )
            product_repo.create(product)
            st.success(f"✅ Produit '{name}' créé")
        except Exception as e:
            st.error(f"❌ Erreur : {e}")


def render_edit(session: Session) -> None:
    """
    Render the user interface for editing existing financial data entries.

    This function provides an interactive UI allowing users to select and modify
    transactions, valuations, or product records within the current session.

    Parameters
    ----------
    session : Session
        The active database session used to fetch and modify data.

    Returns
    -------
    None
        This function renders UI components and does not return any value.

    Raises
    ------
    NotImplementedError
        If the selected edit type does not have a corresponding handler implemented.
    """
    st.header("Éditer les données")

    # Let user choose which type of data to edit
    edit_type = st.radio("Que voulez-vous éditer ?", ["Transactions", "Valorisations", "Produits"])

    # Route to appropriate editing function

    if edit_type == "Transactions":
        _edit_transactions(session)
    elif edit_type == "Valorisations":
        _edit_valuations(session)
    else:
        _edit_products(session)


def _edit_transactions(session: Session) -> None:
    """
    Edit or delete an existing transaction.

    This function provides an interactive UI to select, modify, or remove a transaction
    from the database using Streamlit components.

    Parameters
    ----------
    session : Session
        The database session used to interact with the database.

    Returns
    -------
    None

    Raises
    ------
    Exception
        If an error occurs during transaction update or deletion.
    """
    from datetime import datetime

    st.subheader("Éditer une transaction")

    # Initialize repositories for transaction and product data
    tx_repo = SQLModelTransactionRepository(session)
    product_repo = SQLModelProductRepository(session)

    # Fetch all transactions for selection
    all_txs = tx_repo.get_all()

    if not all_txs:
        st.info("Aucune transaction")

        return

    # Create user-friendly selection keys for transactions
    choices = {f"ID {t.id} | {t.date.strftime('%Y-%m-%d')} | {t.type.value}": t.id for t in all_txs}
    selected_key = st.selectbox("Sélectionner une transaction", list(choices.keys()))
    tx_id = choices[selected_key]
    tx = tx_repo.get_by_id(tx_id)

    # Validate transaction exists

    if not tx:
        st.error("Transaction introuvable.")

        return

    # Display editable transaction fields with current values
    new_date = st.date_input("Date", value=tx.date.date())
    new_type = st.selectbox("Type", list(TransactionType), index=list(TransactionType).index(tx.type), format_func=lambda e: e.value)
    new_amount = st.number_input("Montant EUR", value=float(tx.amount_eur) if tx.amount_eur else 0.0, step=1.0)
    new_quantity = st.number_input("Quantité", value=float(tx.quantity) if tx.quantity else 0.0, step=1.0)
    new_note = st.text_input("Note", value=tx.note or "")

    # Layout save and delete buttons side by side
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Sauvegarder transaction"):
            try:
                # Update transaction with new values
                tx.date = datetime.combine(new_date, datetime.min.time())
                tx.type = new_type
                tx.amount_eur = to_decimal(new_amount) if new_amount > 0 else None
                tx.quantity = to_decimal(new_quantity) if new_quantity > 0 else None
                tx.note = new_note
                tx_repo.update(tx)
                st.success("✅ Transaction mise à jour")
            except Exception as e:
                st.error(f"❌ Erreur : {e}")

    with c2:
        if st.button("🗑️ Supprimer transaction"):
            try:
                # Delete transaction and refresh UI
                tx_repo.delete(tx_id)
                st.success("✅ Transaction supprimée")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur : {e}")


def _edit_valuations(session: Session) -> None:
    """
    Edit or delete an existing valuation record.

    This function provides an interactive UI to select, modify, or remove a valuation entry.

    Parameters
    ----------
    session : Session
        The database session used for performing CRUD operations on valuations.

    Returns
    -------
    None

    Raises
    ------
    Exception
        If any error occurs during database operations (e.g., update or delete).
    """
    from datetime import datetime

    st.subheader("Éditer une valorisation")

    # Initialize repository for valuation operations
    val_repo = SQLModelValuationRepository(session)

    # Fetch all valuations for selection
    all_vals = val_repo.get_all()

    if not all_vals:
        st.info("Aucune valorisation")

        return

    # Create user-friendly selection keys for valuations
    choices = {f"ID {v.id} | {v.date.strftime('%Y-%m-%d')} | {float(v.total_value_eur):.2f}€": v.id for v in all_vals}
    selected_key = st.selectbox("Sélectionner une valorisation", list(choices.keys()))
    val_id = choices[selected_key]
    v = val_repo.get_by_id(val_id)

    # Validate valuation exists

    if not v:
        st.error("Valorisation introuvable.")

        return

    # Display editable valuation fields with current values
    new_date = st.date_input("Date", value=v.date.date())
    new_total_value = st.number_input("Valeur totale EUR", value=float(v.total_value_eur), step=1.0)
    new_unit_price = st.number_input("Prix unitaire EUR", value=float(v.unit_price_eur) if v.unit_price_eur else 0.0, step=1.0)

    # Layout save and delete buttons side by side
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Sauvegarder valorisation"):
            try:
                # Update valuation with new values
                v.date = datetime.combine(new_date, datetime.min.time())
                v.total_value_eur = to_decimal(new_total_value)
                v.unit_price_eur = to_decimal(new_unit_price) if new_unit_price > 0 else None
                val_repo.update(v)
                st.success("✅ Valorisation mise à jour")
            except Exception as e:
                st.error(f"❌ Erreur : {e}")

    with c2:
        if st.button("🗑️ Supprimer valorisation"):
            try:
                # Delete valuation and refresh UI
                val_repo.delete(val_id)
                st.success("✅ Valorisation supprimée")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur : {e}")


def _edit_products(session: Session) -> None:
    """
    Edit an existing product in the database.

    This function allows the user to select and modify the details of an existing product,
    including its name, description, risk level, fees, and tax information.

    Parameters
    ----------
    session : Session
        The database session used to interact with the products table.

    Returns
    -------
    None

    Raises
    ------
    Exception
        If an error occurs during the update process, it will be caught and displayed.
    """
    st.subheader("Éditer un produit")

    # Initialize repository and fetch all products
    product_repo = SQLModelProductRepository(session)
    products = product_repo.get_all()

    if not products:
        st.info("Aucun produit")

        return

    # Let user select a product to edit
    selected_name = st.selectbox("Sélectionner un produit", [p.name for p in products])
    p = product_repo.get_by_name(selected_name)

    if not p:
        st.error("Produit introuvable.")

        return

    # Display editable product fields with current values
    new_name = st.text_input("Nom", value=p.name)
    new_description = st.text_area("Description", value=p.description or "")
    new_risk = st.text_input("Niveau de risque", value=p.risk_level or "")
    new_fees = st.text_area("Frais", value=p.fees_description or "")
    new_tax = st.text_area("Fiscalité", value=p.tax_info or "")

    # Handle product update on button click

    if st.button("💾 Sauvegarder produit"):
        try:
            # Update product with new values
            p.name = new_name
            p.description = new_description or None
            p.risk_level = new_risk or None
            p.fees_description = new_fees or None
            p.tax_info = new_tax or None
            product_repo.update(p)
            st.success("✅ Produit mis à jour")
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
