"""
valuations.py — Streamlit UI for valuation management.

This module provides the valuation management interface for Finance Tracker.
Users can add, edit, and delete valuation snapshots through an editable
data table with filtering and sorting capabilities.

A valuation (or snapshot) captures the value of a product at a specific
point in time. This enables:
- Tracking portfolio value evolution over time
- Calculating unrealized gains/losses
- Computing performance metrics (MWRR, returns)
- Generating historical charts and reports

Key Features
------------
- Add valuation form with dynamic labels for Bitcoin (BTC price vs unit price)
- Editable data table with inline modification
- Filtering by product
- Sorting by date or ID (ascending/descending)
- Batch apply changes with validation
- Automatic timestamp handling

Valuation Fields
----------------
total_value_eur : Decimal
    Total value of the position in EUR (required, must be > 0).
unit_price_eur : Decimal, optional
    Price per unit/share in EUR. For Bitcoin, this represents the price
    of one full BTC (not satoshi price).
date : datetime
    Snapshot date (stored as datetime at midnight for consistency).

Notes
-----
For Bitcoin products, the unit_price_eur field displays as "Prix d'un BTC plein (EUR)"
to clarify that users should enter the full Bitcoin price, not the satoshi price.

Examples
--------
>>> from finance_tracker.web.views.valuations import render
>>> from sqlmodel import Session
>>> session = Session(engine)
>>> render(session)  # Renders the valuations page in Streamlit

See Also
--------
finance_tracker.domain.models.Valuation : Valuation model definition
finance_tracker.repositories.sqlmodel_repo.SQLModelValuationRepository : Data access
"""

import streamlit as st
import pandas as pd

from datetime import datetime, date
from sqlmodel import Session

from finance_tracker.domain.models import Valuation
from finance_tracker.repositories.sqlmodel_repo import (
    SQLModelProductRepository,
    SQLModelValuationRepository,
    )
from finance_tracker.web.ui.formatters import to_decimal


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def render(session: Session) -> None:
    """
    Render the Valuations management page in the Streamlit application.

    This page provides a CRUD interface for valuation snapshots with
    an editable data table. Users can add new valuations via a form,
    and modify or delete existing valuations inline.

    The page is organized into two main sections:

    1. Add Valuation Form - Expander with product selector and form fields
    2. Valuation List - Editable data table with filters and sort options

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
    Valuations are snapshots that capture:
    - The total value of a position at a specific date
    - Optionally, the unit price (useful for tracking price evolution)

    For Bitcoin products:
    - The unit price field label changes to "Prix d'un BTC plein (EUR)"
    - Users should enter the full Bitcoin price, not satoshi price
    - This allows tracking BTC price evolution alongside total value

    Validation:
    - Total value must be strictly positive (> 0)
    - Unit price is optional but must be positive if provided
    - Date is required and defaults to today

    The editable table uses st.data_editor with fixed rows (no inline addition).
    Changes are applied in batch via the "Appliquer les changements" button.

    Examples
    --------
    >>> from finance_tracker.web.db import get_session
    >>> session = get_session()
    >>> render(session)  # Renders the valuations page in Streamlit
    """
    st.title("📈 Mes Valorisations")
    st.caption("Snapshots de valeur : ajout, édition et suppression depuis une table unique.")

    # Initialize repositories
    product_repo = SQLModelProductRepository(session)
    val_repo = SQLModelValuationRepository(session)

    # Load products for selectors
    products = product_repo.get_all()

    # Early return if no products exist

    if not products:
        st.info("Aucun produit. Créez un produit avant d'ajouter des valorisations.")

        return

    product_names = [p.name for p in products]
    product_by_name = {p.name: p for p in products}
    product_by_id = {p.id: p for p in products if p.id is not None}

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1: ADD VALUATION FORM
    # ═══════════════════════════════════════════════════════════════════════════
    with st.expander("➕ Ajouter une valorisation", expanded=False):
        # Product selector placed OUTSIDE the form for dynamic field adaptation
        # This allows the unit price label to change based on selected product
        add_product_name = st.selectbox("Produit", product_names, key="val_add_product")

        # Adapt unit price label for Bitcoin (full BTC price) vs other products
        is_btc = add_product_name.lower() == "bitcoin"

        with st.form("val_add_form", clear_on_submit=True):
            c1, c2 = st.columns([2, 2])
            with c1:
                add_date = st.date_input("Date", value=date.today(), key="val_add_date")
            with c2:
                add_total = st.number_input("Valeur totale EUR", value=0.0, step=0.01, format="%.2f", key="val_add_total")

                # Label changes to be explicit for Bitcoin pricing
                unit_label = "Prix d'un BTC plein (EUR)" if is_btc else "Prix unitaire (EUR, optionnel)"
                add_unit = st.number_input(unit_label, value=0.0, step=0.01, format="%.2f", key="val_add_unit")

            submitted = st.form_submit_button("Ajouter", width="stretch")

            if submitted:
                try:
                    p = product_by_name.get(add_product_name)

                    if not p or p.id is None:
                        st.stop()

                    # Validate that total value is positive

                    if add_total <= 0:
                        st.error("La valeur totale doit être > 0.")
                        st.stop()

                    val = Valuation(
                        product_id=p.id,
                        date=datetime.combine(add_date, datetime.min.time()),
                        total_value_eur=to_decimal(add_total),
                        unit_price_eur=to_decimal(add_unit) if add_unit and add_unit > 0 else None,
                        )
                    val_repo.create(val)
                    st.success("✅ Valorisation ajoutée.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")

    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2: VALUATION LIST WITH FILTERS AND EDITABLE TABLE
    # ═══════════════════════════════════════════════════════════════════════════

    # Filter controls
    f1, f2 = st.columns([2, 2])
    with f1:
        filter_product = st.selectbox("Filtrer produit", ["Tous"] + product_names, index=0)
    with f2:
        sort_mode = st.selectbox("Tri", ["Date décroissante", "Date croissante", "ID décroissant"], index=0)

    # Load and filter valuations
    vals = val_repo.get_all()

    # Apply product filter

    if filter_product != "Tous":
        pid = product_by_name[filter_product].id
        vals = [v for v in vals if v.product_id == pid]

    # Apply sorting

    if sort_mode == "Date croissante":
        vals = sorted(vals, key=lambda v: v.date)
    elif sort_mode == "ID décroissant":
        vals = sorted(vals, key=lambda v: (v.id or 0), reverse=True)
    else:  # Date décroissante (default)
        vals = sorted(vals, key=lambda v: v.date, reverse=True)

    # Build rows for data editor
    rows = []

    for v in vals:
        p = product_by_id.get(v.product_id)
        rows.append(
            {
                "id": v.id,
                "date": v.date.date(),
                "produit": p.name if p else f"#{v.product_id}",
                "valeur_totale_eur": float(v.total_value_eur),
                "prix_unitaire_eur": float(v.unit_price_eur) if v.unit_price_eur is not None else 0.0,
                "🗑️ Supprimer": False,
                }
            )

    # Early return if no valuations match filters

    if not rows:
        st.info("Aucune valorisation pour ce filtre.")

        return

    df = pd.DataFrame(rows)

    st.subheader("Historique (éditable)")

    # Editable data table
    edited = st.data_editor(
        df,
        key="val_editor",
        hide_index=True,
        width="stretch",
        num_rows="fixed",  # Prevent inline row addition
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
            "produit": st.column_config.SelectboxColumn("Produit", options=product_names, required=True),
            "valeur_totale_eur": st.column_config.NumberColumn("Valeur totale EUR", min_value=0.0, step=0.01, format="%.2f"),
            "prix_unitaire_eur": st.column_config.NumberColumn("Prix unitaire EUR", min_value=0.0, step=0.01, format="%.2f"),
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
                    val_id = r.get("id", None)

                    # Skip rows without valid ID (should not happen in fixed rows mode)

                    if val_id is None or (isinstance(val_id, float) and pd.isna(val_id)):
                        continue

                    # Handle deletion first (priority over updates)

                    if bool(r.get("🗑️ Supprimer", False)):
                        val_repo.delete(int(val_id))

                        continue

                    # Handle updates for non-deleted rows
                    v = val_repo.get_by_id(int(val_id))

                    if not v:
                        continue

                    # Validate and resolve product
                    prod_name = r["produit"]
                    p = product_by_name.get(prod_name)

                    if not p or p.id is None:
                        raise ValueError(f"Produit invalide: {prod_name!r}")

                    # Extract and validate values
                    total = float(r.get("valeur_totale_eur") or 0.0)
                    unit = float(r.get("prix_unitaire_eur") or 0.0)

                    # Validate that total value is positive

                    if total <= 0:
                        raise ValueError("La valeur totale doit être > 0.")

                    # Update valuation fields
                    v.product_id = p.id
                    v.date = datetime.combine(r["date"], datetime.min.time())
                    v.total_value_eur = to_decimal(total)
                    v.unit_price_eur = to_decimal(unit) if unit > 0 else None

                    val_repo.update(v)

                st.success("✅ Changements appliqués.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur : {e}")

    with c2:
        # Reload button to discard edits and fetch fresh data

        if st.button("↩️ Recharger depuis la DB", width="stretch"):
            st.rerun()
