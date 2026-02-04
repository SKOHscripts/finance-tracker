import streamlit as st
from datetime import datetime, date
from sqlmodel import Session

from finance_tracker.domain.enums import TransactionType
from finance_tracker.domain.models import Transaction
from finance_tracker.repositories.sqlmodel_repo import SQLModelProductRepository, SQLModelTransactionRepository
from finance_tracker.web.ui.formatters import to_decimal


def render_add(session: Session) -> None:
    """Render form to add a new transaction."""
    st.header("Ajouter une transaction")

    # Initialize repositories for products and transactions
    product_repo = SQLModelProductRepository(session)
    tx_repo = SQLModelTransactionRepository(session)

    # Fetch all available products
    products = product_repo.get_all()

    # Prevent transaction creation if no products exist

    if not products:
        st.info("Aucun produit. Ajoute un produit d'abord.")

        return

    # UI elements for transaction input
    product_name = st.selectbox("Produit", [p.name for p in products])
    tx_type = st.selectbox("Type de transaction", list(TransactionType), format_func=lambda e: e.value)
    tx_date = st.date_input("Date", value=date.today())
    amount = st.number_input("Montant EUR", value=0.0, step=1.0)
    quantity = st.number_input("Quantité (parts/sats)", value=0.0, step=1.0)
    note = st.text_input("Note", value="")

    # Handle transaction creation on button click

    if st.button("➕ Ajouter transaction"):
        try:
            # Retrieve selected product by name
            product = product_repo.get_by_name(product_name)

            if not product:
                st.error(f"Produit '{product_name}' non trouvé")

                return

            # Create and save new transaction
            tx = Transaction(
                product_id=product.id or 0,
                date=datetime.combine(tx_date, datetime.min.time()),
                type=tx_type,
                amount_eur=to_decimal(amount) if amount > 0 else None,
                quantity=to_decimal(quantity) if quantity > 0 else None,
                note=note,
            )
            tx_repo.create(tx)
            st.success(f"✅ Transaction ajoutée pour {product_name}")
        except Exception as e:
            st.error(f"❌ Erreur : {e}")


def render_list(session: Session) -> None:
    """Render list of transactions with optional product filter."""
    st.header("Historique des transactions")

    # Initialize repositories
    tx_repo = SQLModelTransactionRepository(session)
    product_repo = SQLModelProductRepository(session)

    # Fetch products for filter dropdown
    products = product_repo.get_all()
    product_names = ["Tous"] + [p.name for p in products]
    selected_product = st.selectbox("Filtrer par produit", product_names)

    # Retrieve all transactions
    all_txs = tx_repo.get_all()

    # Apply product filter if not "Tous"

    if selected_product != "Tous":
        product = product_repo.get_by_name(selected_product)

        if product:
            all_txs = [t for t in all_txs if t.product_id == product.id]

    # Format transactions for display
    rows = []

    for tx in all_txs:
        product = product_repo.get_by_id(tx.product_id)
        rows.append({
            "ID": tx.id,
            "Date": tx.date.strftime("%Y-%m-%d"),
            "Produit": product.name if product else "?",
            "Type": tx.type.value,
            "Montant EUR": f"{float(tx.amount_eur):.2f}" if tx.amount_eur else "-",
            "Quantité": f"{float(tx.quantity):.2f}" if tx.quantity else "-",
            "Note": tx.note,
        })

    # Display transactions or info message

    if rows:
        st.dataframe(rows, width="stretch")
    else:
        st.info("Aucune transaction")
