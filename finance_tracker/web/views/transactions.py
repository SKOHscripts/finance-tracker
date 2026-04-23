"""
transactions.py — Streamlit UI for transaction management.
"""

import streamlit as st
import pandas as pd

from datetime import datetime, date
from sqlmodel import Session

from finance_tracker.domain.enums import TransactionType
from finance_tracker.domain.models import Transaction
from finance_tracker.i18n import t
from finance_tracker.repositories.sqlmodel_repo import (
    SQLModelProductRepository,
    SQLModelTransactionRepository,
    )
from finance_tracker.web.ui.formatters import to_decimal

SATS_PER_BTC = 100_000_000


def _enum_from_value(enum_cls, value: str):
    for e in enum_cls:
        if e.value == value:
            return e
    raise ValueError(f"Valeur enum inconnue: {value!r}")


def render(session: Session) -> None:
    """Render the Transactions management page in the Streamlit application."""
    st.title(t("transactions.title"))
    st.caption(t("transactions.caption"))

    product_repo = SQLModelProductRepository(session)
    tx_repo = SQLModelTransactionRepository(session)

    products = product_repo.get_all()
    product_names = [p.name for p in products]
    product_by_name = {p.name: p for p in products}
    product_by_id = {p.id: p for p in products if p.id is not None}

    if not products:
        st.info(t("transactions.no_products"))
        return

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1: ADD TRANSACTION FORM
    # ═══════════════════════════════════════════════════════════════════════════
    with st.expander(f"➕ {t('transactions.add_expander')}", expanded=False):
        add_product_name = st.selectbox(t("transactions.field_product"), product_names, key="tx_add_product")

        is_btc = add_product_name.lower() == "bitcoin"
        qty_label = t("transactions.field_qty_sats") if is_btc else t("transactions.field_qty_units")
        qty_step = 100_000.0 if is_btc else 0.01
        qty_format = "%d" if is_btc else "%.2f"
        qty_help = t("transactions.field_qty_help_btc") if is_btc else ""

        with st.form("tx_add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 2, 3])
            with c1:
                add_type = st.selectbox(t("transactions.field_type"), [e.value for e in TransactionType], key="tx_add_type")
                add_date = st.date_input(t("transactions.field_date"), value=date.today(), key="tx_add_date")
            with c2:
                add_amount = st.number_input(t("transactions.field_amount"), value=0.0, step=0.01, format="%.2f", key="tx_add_amount")
                add_quantity = st.number_input(qty_label, value=0.0, step=qty_step, format=qty_format, help=qty_help, key="tx_add_qty")
            with c3:
                add_note = st.text_input(t("transactions.field_note"), value="", key="tx_add_note")

            submitted = st.form_submit_button(t("transactions.add_btn"), width="stretch")

            if submitted:
                try:
                    p = product_by_name.get(add_product_name)

                    if not p or p.id is None:
                        st.stop()

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
                    st.success(t("transactions.added_success"))
                    st.rerun()
                except Exception as e:
                    st.error(t("transactions.error").format(e=e))

    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2: TRANSACTION LIST WITH FILTERS AND EDITABLE TABLE
    # ═══════════════════════════════════════════════════════════════════════════

    filter_all = t("transactions.filter_all")
    sort_date_desc = t("transactions.sort_date_desc")
    sort_date_asc = t("transactions.sort_date_asc")
    sort_id_desc = t("transactions.sort_id_desc")

    f1, f2, f3 = st.columns([2, 2, 2])
    with f1:
        filter_product = st.selectbox(t("transactions.filter_product"), [filter_all] + product_names, index=0)
    with f2:
        filter_type = st.selectbox(t("transactions.filter_type"), [filter_all] + [e.value for e in TransactionType], index=0)
    with f3:
        sort_mode = st.selectbox(t("transactions.sort_label"), [sort_date_desc, sort_date_asc, sort_id_desc], index=0)

    txs = tx_repo.get_all()

    if filter_product != filter_all:
        pid = product_by_name[filter_product].id
        txs = [tx for tx in txs if tx.product_id == pid]

    if filter_type != filter_all:
        txs = [tx for tx in txs if tx.type.value == filter_type]

    if sort_mode == sort_date_asc:
        txs = sorted(txs, key=lambda tx: tx.date)
    elif sort_mode == sort_id_desc:
        txs = sorted(txs, key=lambda tx: (tx.id or 0), reverse=True)
    else:
        txs = sorted(txs, key=lambda tx: tx.date, reverse=True)

    delete_col = t("transactions.col_delete")
    rows = []

    for tx in txs:
        p = product_by_id.get(tx.product_id)
        rows.append({
            "id": tx.id,
            "date": tx.date.date(),
            "produit": p.name if p else f"#{tx.product_id}",
            "type": tx.type.value,
            "montant_eur": float(tx.amount_eur) if tx.amount_eur is not None else 0.0,
            "quantite": float(tx.quantity) if tx.quantity is not None else 0.0,
            "note": tx.note or "",
            delete_col: False,
            })

    if not rows:
        st.info(t("transactions.empty_filter"))
        return

    df = pd.DataFrame(rows)

    st.subheader(t("transactions.list_title"))
    st.info(t("transactions.btc_qty_info"))

    edited = st.data_editor(
        df,
        key="tx_editor",
        hide_index=True,
        width="stretch",
        num_rows="fixed",
        column_config={
            "id": st.column_config.NumberColumn(t("transactions.col_id"), disabled=True),
            "date": st.column_config.DateColumn(t("transactions.col_date"), format="YYYY-MM-DD"),
            "produit": st.column_config.SelectboxColumn(t("transactions.col_product"), options=product_names, required=True),
            "type": st.column_config.SelectboxColumn(t("transactions.col_type"), options=[e.value for e in TransactionType], required=True),
            "montant_eur": st.column_config.NumberColumn(t("transactions.col_amount"), min_value=0.0, step=0.01, format="%.2f"),
            "quantite": st.column_config.NumberColumn(t("transactions.col_qty"), min_value=0.0, step=0.01, format="%.2f"),
            "note": st.column_config.TextColumn(t("transactions.col_note")),
            delete_col: st.column_config.CheckboxColumn(delete_col),
            },
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3: ACTION BUTTONS
    # ═══════════════════════════════════════════════════════════════════════════
    c1, c2 = st.columns([2, 1])

    with c1:
        if st.button(t("transactions.apply_btn"), width="stretch"):
            try:
                edited_rows = edited.to_dict(orient="records")

                for r in edited_rows:
                    tx_id = r.get("id", None)

                    if tx_id is None or (isinstance(tx_id, float) and pd.isna(tx_id)):
                        continue

                    if bool(r.get(delete_col, False)):
                        tx_repo.delete(int(tx_id))
                        continue

                    tx = tx_repo.get_by_id(int(tx_id))

                    if not tx:
                        continue

                    prod_name = r["produit"]
                    p = product_by_name.get(prod_name)

                    if not p or p.id is None:
                        raise ValueError(t("transactions.invalid_product").format(name=prod_name))

                    tx.product_id = p.id
                    tx.date = datetime.combine(r["date"], datetime.min.time())
                    tx.type = _enum_from_value(TransactionType, r["type"])

                    amount = float(r.get("montant_eur") or 0.0)
                    raw_qty = float(r.get("quantite") or 0.0)

                    if prod_name.lower() == "bitcoin":
                        raw_qty = float(int(raw_qty))

                    tx.amount_eur = to_decimal(amount) if amount > 0 else None
                    tx.quantity = to_decimal(raw_qty) if raw_qty > 0 else None
                    tx.note = str(r.get("note") or "").strip()

                    tx_repo.update(tx)

                st.success(t("transactions.applied_success"))
                st.rerun()
            except Exception as e:
                st.error(t("transactions.error").format(e=e))

    with c2:
        if st.button(t("transactions.reload_btn"), width="stretch"):
            st.rerun()
