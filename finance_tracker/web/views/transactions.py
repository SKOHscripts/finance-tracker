"""
transactions.py — Streamlit UI for transaction management.

This module provides the transaction management interface for Finance Tracker.
Users can add, edit, and delete financial transactions through an editable
data table with filtering and sorting capabilities.

The module handles multiple transaction types:
- DEPOSIT: Cash inflow to the portfolio
- WITHDRAW: Cash outflow from the portfolio
- BUY: Asset purchase (reduces cash, increases position)
- SELL: Asset sale (increases cash, decreases position)
- DISTRIBUTION: Dividend or coupon received
- FEE: Fees paid

Special handling is provided for Bitcoin transactions, where quantities
are stored and displayed in satoshis (1 BTC = 100,000,000 satoshis).

Key Features
------------
- Add transaction form with dynamic quantity labels for Bitcoin
- Editable data table with inline modification
- Filtering by product and transaction type
- Sorting by date or ID (ascending/descending)
- Batch apply changes with validation
- Automatic satoshi rounding for Bitcoin quantities

Module Constants
----------------
SATS_PER_BTC : int
    Number of satoshis in one Bitcoin (100,000,000).

Examples
--------
>>> from finance_tracker.web.views.transactions import render
>>> from sqlmodel import Session
>>> session = Session(engine)
>>> render(session)  # Renders the transactions page in Streamlit

See Also
--------
finance_tracker.domain.enums.TransactionType : Transaction type enum
finance_tracker.repositories.sqlmodel_repo.SQLModelTransactionRepository : Data access
"""

import streamlit as st
import pandas as pd

from datetime import datetime, date
from sqlmodel import Session

from finance_tracker.domain.enums import TransactionType
from finance_tracker.domain.models import Transaction
from finance_tracker.repositories.sqlmodel_repo import (
    SQLModelProductRepository,
    SQLModelTransactionRepository,
    )
from finance_tracker.web.ui.formatters import to_decimal

SATS_PER_BTC = 100_000_000
"""Number of satoshis in one Bitcoin (used for display/formatting)."""


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _enum_from_value(enum_cls, value: str):
    """
    Retrieve an enum member by its string value.

    This function performs a reverse lookup to find an enum member
    whose value attribute matches the provided string.

    Parameters
    ----------
    enum_cls : type
        The enum class to search in (e.g., TransactionType, ProductType).
    value : str
        The string value to match against enum member values.

    Returns
    -------
    Enum
        The enum member with matching value.

    Raises
    ------
    ValueError
        If no enum member has the specified value.

    Examples
    --------
    >>> from finance_tracker.domain.enums import TransactionType
    >>> _enum_from_value(TransactionType, "BUY")
    <TransactionType.BUY: 'BUY'>
    >>> _enum_from_value(TransactionType, "INVALID")
    ValueError: Valeur enum inconnue: 'INVALID'
    """

    for e in enum_cls:
        if e.value == value:
            return e
    raise ValueError(f"Valeur enum inconnue: {value!r}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def render(session: Session) -> None:
    """
    Render the Transactions management page in the Streamlit application.

    This page provides a CRUD interface for financial transactions with
    an editable data table. Users can add new transactions via a form,
    and modify or delete existing transactions inline.

    The page is organized into two main sections:

    1. Add Transaction Form - Expander with product selector and form fields
    2. Transaction List - Editable data table with filters and sort options

    Parameters
    ----------
    session : Session
        SQLModel database session for repository operations.

    Returns
    -------
    None
        This function renders UI components directly to Streamlit.

    Notes
    -----
    Bitcoin Handling:
    - Bitcoin quantities are displayed and edited in satoshis (integers)
    - The form adapts labels and step values for Bitcoin products
    - Quantities are rounded to integers before saving for Bitcoin

    Transaction Types:
    - DEPOSIT: Cash inflow (positive for invested amount calculation)
    - WITHDRAW: Cash outflow (negative for invested amount calculation)
    - BUY: Asset purchase (negative for invested amount, increases position)
    - SELL: Asset sale (positive for invested amount, decreases position)
    - DISTRIBUTION: Dividend/coupon received (positive for invested amount)
    - FEE: Fees paid (negative for invested amount calculation)

    The editable table uses st.data_editor with fixed rows (no inline addition).
    Changes are applied in batch via the "Appliquer les changements" button.

    Examples
    --------
    >>> from finance_tracker.web.db import get_session
    >>> session = get_session()
    >>> render(session)  # Renders the transactions page in Streamlit
    """
    st.title("💸 Mes Transactions")
    st.caption("Ajout, modification et suppression directement depuis la liste.")

    # Initialize repositories
    product_repo = SQLModelProductRepository(session)
    tx_repo = SQLModelTransactionRepository(session)

    # Load products for selectors
    products = product_repo.get_all()
    product_names = [p.name for p in products]
    product_by_name = {p.name: p for p in products}
    product_by_id = {p.id: p for p in products if p.id is not None}

    # Early return if no products exist

    if not products:
        st.info("Aucun produit. Créez d'abord un produit pour pouvoir ajouter des transactions.")

        return

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1: ADD TRANSACTION FORM
    # ═══════════════════════════════════════════════════════════════════════════
    with st.expander("➕ Ajouter une transaction", expanded=False):
        # Product selector placed OUTSIDE the form for dynamic field adaptation
        # This allows the quantity field to change based on selected product
        add_product_name = st.selectbox("Produit", product_names, key="tx_add_product")

        # Adapt quantity field for Bitcoin (satoshis) vs other products
        is_btc = add_product_name.lower() == "bitcoin"
        qty_label = "Quantité (en Satoshis)" if is_btc else "Quantité (Parts / Unités)"
        qty_step = 100_000.0 if is_btc else 0.01
        qty_format = "%d" if is_btc else "%.2f"
        qty_help = "Rappel: 1 BTC = 100 000 000 Sats" if is_btc else ""

        with st.form("tx_add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 2, 3])
            with c1:
                add_type = st.selectbox("Type", [e.value for e in TransactionType], key="tx_add_type")
                add_date = st.date_input("Date", value=date.today(), key="tx_add_date")
            with c2:
                add_amount = st.number_input("Montant EUR (optionnel)", value=0.0, step=0.01, format="%.2f", key="tx_add_amount")
                # Quantity field adapts based on product selector above
                add_quantity = st.number_input(qty_label, value=0.0, step=qty_step, format=qty_format, help=qty_help, key="tx_add_qty")
            with c3:
                add_note = st.text_input("Note", value="", key="tx_add_note")

            submitted = st.form_submit_button("Ajouter", width="stretch")

            if submitted:
                try:
                    p = product_by_name.get(add_product_name)

                    if not p or p.id is None:
                        st.stop()

                    # For Bitcoin, store raw satoshis (no decimal conversion)
                    final_qty = float(add_quantity)

                    tx = Transaction(
                        product_id=p.id,
                        date=datetime.combine(add_date, datetime.min.time()),
                        type=_enum_from_value(TransactionType, add_type),
                        amount_eur=to_decimal(add_amount) if add_amount and add_amount > 0 else None,
                        quantity=to_decimal(final_qty) if final_qty > 0 else None,
                        note=add_note.strip(),
                        )
                    tx_repo.create(tx)
                    st.success("✅ Transaction ajoutée.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")

    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2: TRANSACTION LIST WITH FILTERS AND EDITABLE TABLE
    # ═══════════════════════════════════════════════════════════════════════════

    # Filter controls
    f1, f2, f3 = st.columns([2, 2, 2])
    with f1:
        filter_product = st.selectbox("Filtrer produit", ["Tous"] + product_names, index=0)
    with f2:
        filter_type = st.selectbox("Filtrer type", ["Tous"] + [e.value for e in TransactionType], index=0)
    with f3:
        sort_mode = st.selectbox("Tri", ["Date décroissante", "Date croissante", "ID décroissant"], index=0)

    # Load and filter transactions
    txs = tx_repo.get_all()

    # Apply product filter

    if filter_product != "Tous":
        pid = product_by_name[filter_product].id
        txs = [t for t in txs if t.product_id == pid]

    # Apply type filter

    if filter_type != "Tous":
        txs = [t for t in txs if t.type.value == filter_type]

    # Apply sorting

    if sort_mode == "Date croissante":
        txs = sorted(txs, key=lambda t: t.date)
    elif sort_mode == "ID décroissant":
        txs = sorted(txs, key=lambda t: (t.id or 0), reverse=True)
    else:  # Date décroissante (default)
        txs = sorted(txs, key=lambda t: t.date, reverse=True)

    # Build rows for data editor
    rows = []

    for t in txs:
        p = product_by_id.get(t.product_id)
        rows.append({
            "id": t.id,
            "date": t.date.date(),
            "produit": p.name if p else f"#{t.product_id}",
            "type": t.type.value,
            "montant_eur": float(t.amount_eur) if t.amount_eur is not None else 0.0,
            "quantite": float(t.quantity) if t.quantity is not None else 0.0,
            "note": t.note or "",
            "🗑️ Supprimer": False,
            })

    # Early return if no transactions match filters

    if not rows:
        st.info("Aucune transaction pour ce filtre.")

        return

    df = pd.DataFrame(rows)

    st.subheader("Historique (éditable)")

    # Informational message about Bitcoin quantities
    st.info("ℹ️ Les quantités concernant Bitcoin sont affichées et enregistrées en **Satoshis** (nombres entiers). Les autres produits restent en unités standards.")

    # Editable data table
    edited = st.data_editor(
        df,
        key="tx_editor",
        hide_index=True,
        width="stretch",
        num_rows="fixed",  # Prevent inline row addition
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
            "produit": st.column_config.SelectboxColumn("Produit", options=product_names, required=True),
            "type": st.column_config.SelectboxColumn("Type", options=[e.value for e in TransactionType], required=True),
            "montant_eur": st.column_config.NumberColumn("Montant EUR", min_value=0.0, step=0.01, format="%.2f"),
            # Step at 0.01 to handle all products (SCPI need decimals, Bitcoin handled separately)
            "quantite": st.column_config.NumberColumn("Quantité (Sats ou Unités)", min_value=0.0, step=0.01, format="%.2f"),
            "note": st.column_config.TextColumn("Note"),
            "🗑️ Supprimer": st.column_config.CheckboxColumn("🗑️ Supprimer"),
            },
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3: ACTION BUTTONS
    # ═══════════════════════════════════════════════════════════════════════════
    c1, c2 = st.columns([2, 1])

    with c1:
        if st.button("💾 Appliquer les changements", width="stretch"):
            try:
                edited_rows = edited.to_dict(orient="records")

                for r in edited_rows:
                    tx_id = r.get("id", None)

                    # Skip rows without valid ID (should not happen in fixed rows mode)

                    if tx_id is None or (isinstance(tx_id, float) and pd.isna(tx_id)):
                        continue

                    # Handle deletion first (priority over updates)

                    if bool(r.get("🗑️ Supprimer", False)):
                        tx_repo.delete(int(tx_id))

                        continue

                    # Handle updates for non-deleted rows
                    tx = tx_repo.get_by_id(int(tx_id))

                    if not tx:
                        continue

                    # Validate and resolve product
                    prod_name = r["produit"]
                    p = product_by_name.get(prod_name)

                    if not p or p.id is None:
                        raise ValueError(f"Produit invalide: {prod_name!r}")

                    # Update transaction fields
                    tx.product_id = p.id
                    tx.date = datetime.combine(r["date"], datetime.min.time())
                    tx.type = _enum_from_value(TransactionType, r["type"])

                    amount = float(r.get("montant_eur") or 0.0)
                    raw_qty = float(r.get("quantite") or 0.0)

                    # Force integer rounding for Bitcoin (pure satoshis)

                    if prod_name.lower() == "bitcoin":
                        raw_qty = float(int(raw_qty))

                    tx.amount_eur = to_decimal(amount) if amount > 0 else None
                    tx.quantity = to_decimal(raw_qty) if raw_qty > 0 else None
                    tx.note = str(r.get("note") or "").strip()

                    tx_repo.update(tx)

                st.success("✅ Changements appliqués.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur : {e}")

    with c2:
        # Reload button to discard edits and fetch fresh data

        if st.button("↩️ Recharger depuis la DB", width="stretch"):
            st.rerun()
