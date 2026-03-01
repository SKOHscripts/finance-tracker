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
    """Display the centralized data management interface (Add & Edit).

    Provides tabs for adding new portfolio items and editing existing history.

    Parameters
    ----------
    session : Session
        The user session object.

    Returns
    -------
    None

    Raises
    ------
    None
    """
    st.title("🗂️ Gestion des Données")
    st.markdown("Ajoutez de nouveaux éléments à votre portefeuille ou modifiez l'historique existant.")

    # Split into two tabs to keep the UI clean and focused
    tab_add, tab_edit = st.tabs(["➕ Ajouter", "✏️ Éditer l'historique"])

    with tab_add:
        _render_add_tab(session)

    with tab_edit:
        _render_edit_tab(session)


def _render_add_tab(session: Session) -> None:
    """Render the add tab interface for selecting and displaying add forms.

    This function displays a radio button to choose the entity type and routes
    to the appropriate form based on the user's selection.

    Parameters
    ----------
    session : Session
        The database session for executing queries.

    Returns
    -------
    None

    Raises
    ------
    None
    """
    entity_to_add = st.radio(
        "Que souhaitez-vous ajouter ?",
        ["Transaction", "Valorisation", "Nouveau Produit"],
        horizontal=True
        )

    # Visual separator to distinguish header from form content
    st.markdown("---")

    # Route to the appropriate form based on user selection

    if entity_to_add == "Transaction":
        _add_transaction_form(session)
    elif entity_to_add == "Valorisation":
        _add_valuation_form(session)
    else:
        _add_product_form(session)


def _render_edit_tab(session: Session) -> None:
    """Render the edit tab for modifying entities in the finance tracker.

    Allows users to select and edit transactions, valuations, or products.

    Parameters
    ----------
    session : Session
        Database session for executing queries.

    Returns
    -------
    None
    """
    # Let user choose which entity to modify
    entity_to_edit = st.radio(
        "Que souhaitez-vous éditer ?",
        ["Transactions", "Valorisations", "Produits"],
        horizontal=True,
        key="radio_edit"
        )

    st.markdown("---")

    # Import here to avoid circular dependencies with Streamlit's module loading
    from finance_tracker.web.views.products import (
        _edit_transactions,
        _edit_valuations,
        _edit_products
        )

    # Route to the appropriate edit function based on user selection

    if entity_to_edit == "Transactions":
        _edit_transactions(session)
    elif entity_to_edit == "Valorisations":
        _edit_valuations(session)
    else:
        _edit_products(session)


def _add_transaction_form(session: Session) -> None:
    """Display and handle a form for adding a new transaction to the database.

    The form allows users to select a product, transaction type, date, amount,
    quantity, and an optional note.

    Parameters
    ----------
    session : Session
        Database session for repository operations.

    Returns
    -------
    None

    Raises
    ------
    None
    """
    product_repo = SQLModelProductRepository(session)
    tx_repo = SQLModelTransactionRepository(session)
    products = product_repo.get_all()

    if not products:
        st.warning("⚠️ Aucun produit disponible. Veuillez d'abord créer un produit.")
        # Early return prevents form from rendering with empty product list

        return

    # Form groups inputs together and handles submission as one atomic action
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

        submitted = st.form_submit_button("➕ Ajouter la transaction", width="stretch")

        if submitted:
            try:
                product = product_repo.get_by_name(product_name)
                # Convert date (from date_input) to datetime for the model
                tx = Transaction(
                    product_id=product.id,
                    date=datetime.combine(tx_date, datetime.min.time()),
                    type=tx_type,
                    # None is more explicit than 0 for optional monetary fields
                    amount_eur=to_decimal(amount) if amount > 0 else None,
                    quantity=to_decimal(quantity) if quantity > 0 else None,
                    note=note,
                    )
                tx_repo.create(tx)
                st.success(f"✅ Transaction ajoutée avec succès sur {product_name} !")
            except Exception as e:
                # Display user-friendly error instead of crashing
                st.error(f"❌ Erreur : {e}")


def _add_valuation_form(session: Session) -> None:
    """Display a form to create a new valuation for a product.

    The form allows users to select a product, set a valuation date, and enter
    total and unit values in EUR.

    Parameters
    ----------
    session : Session
        Database session for repository operations.

    Returns
    -------
    None

    Raises
    ------
    Exception
        Any database or validation error during valuation creation.
    """
    product_repo = SQLModelProductRepository(session)
    val_repo = SQLModelValuationRepository(session)
    products = product_repo.get_all()

    # Prevent valuation creation when no products exist

    if not products:
        st.warning("⚠️ Aucun produit disponible. Veuillez d'abord créer un produit.")

        return

    with st.form("form_add_valuation", clear_on_submit=True):
        st.subheader("Nouvelle Valorisation")

        col1, col2 = st.columns(2)
        with col1:
            product_name = st.selectbox("Produit", [p.name for p in products])
            # Default to today since valuations typically reflect current state
            val_date = st.date_input("Date du snapshot", value=date.today())

        with col2:
            total_value = st.number_input("Valeur totale (EUR)", value=0.0, step=100.0)
            # Allow null unit price - 0 means "not specified" rather than free
            unit_price = st.number_input("Prix unitaire optionnel (EUR)", value=0.0, step=1.0)

        submitted = st.form_submit_button("📈 Enregistrer la valorisation", width="stretch")

        if submitted:
            try:
                product = product_repo.get_by_name(product_name)
                # Combine date with min time to create a full datetime for storage
                val = Valuation(
                    product_id=product.id,
                    date=datetime.combine(val_date, datetime.min.time()),
                    # Convert floats to Decimal for precise financial calculations
                    total_value_eur=to_decimal(total_value),
                    unit_price_eur=to_decimal(unit_price) if unit_price > 0 else None,
                    )
                val_repo.create(val)
                st.success(f"✅ Valorisation de {total_value}€ ajoutée pour {product_name} !")
            except Exception as e:
                st.error(f"❌ Erreur : {e}")


def _add_product_form(session: Session) -> None:
    """Display a form to create a new financial product in the database.

    The form collects product details and saves them to the database.

    Parameters
    ----------
    session : Session
        Database session for repository operations.

    Returns
    -------
    None

    Raises
    ------
    Exception
        Any database error during product creation.
    """
    # Repository instance for database operations
    product_repo = SQLModelProductRepository(session)

    # Form context batches all inputs and clears them after successful submission
    with st.form("form_add_product", clear_on_submit=True):
        st.subheader("Nouveau Produit Financier")

        # Two-column layout: essential info on left, optional details on right
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

        submitted = st.form_submit_button("💾 Créer le produit", width="stretch")

        if submitted:
            # Validate required field

            if not name.strip():
                st.error("Le nom du produit est obligatoire.")
            # Check for duplicate before attempting creation
            elif product_repo.get_by_name(name):
                st.error(f"Un produit nommé '{name}' existe déjà.")
            else:
                try:
                    # Convert empty strings to None for database (NULL vs empty string)
                    product = Product(
                        name=name, type=product_type, quantity_unit=quantity_unit,
                        description=description or None, risk_level=risk_level or None,
                        fees_description=fees_description or None, tax_info=tax_info or None,
                        )
                    product_repo.create(product)
                    st.success(f"✅ Produit '{name}' créé avec succès !")
                except Exception as e:
                    st.error(f"❌ Erreur lors de la création : {e}")
