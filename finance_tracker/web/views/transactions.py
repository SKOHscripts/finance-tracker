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


def _enum_from_value(enum_cls, value: str):
    for e in enum_cls:
        if e.value == value:
            return e
    raise ValueError(f"Valeur enum inconnue: {value!r}")


def render(session: Session) -> None:
    st.title("💸 Transactions")
    st.caption("Ajout, modification et suppression directement depuis la liste.")

    product_repo = SQLModelProductRepository(session)
    tx_repo = SQLModelTransactionRepository(session)

    products = product_repo.get_all()
    product_names = [p.name for p in products]
    product_by_name = {p.name: p for p in products}
    product_by_id = {p.id: p for p in products if p.id is not None}

    if not products:
        st.info("Aucun produit. Créez d’abord un produit pour pouvoir ajouter des transactions.")

        return

    with st.expander("➕ Ajouter une transaction", expanded=False):
        with st.form("tx_add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 2, 3])
            with c1:
                add_product_name = st.selectbox("Produit", product_names, key="tx_add_product")
                add_type = st.selectbox(
                    "Type",
                    [e.value for e in TransactionType],
                    key="tx_add_type",
                )
                add_date = st.date_input("Date", value=date.today(), key="tx_add_date")
            with c2:
                add_amount = st.number_input("Montant EUR (optionnel)", value=0.0, step=10.0, key="tx_add_amount")
                add_quantity = st.number_input("Quantité (optionnel)", value=0.0, step=1.0, key="tx_add_qty")
            with c3:
                add_note = st.text_input("Note", value="", key="tx_add_note")

            submitted = st.form_submit_button("Ajouter", width="stretch")

            if submitted:
                try:
                    p = product_by_name.get(add_product_name)

                    if not p or p.id is None:
                        st.error("Produit invalide.")
                        st.stop()

                    tx = Transaction(
                        product_id=p.id,
                        date=datetime.combine(add_date, datetime.min.time()),
                        type=_enum_from_value(TransactionType, add_type),
                        amount_eur=to_decimal(add_amount) if add_amount and add_amount > 0 else None,
                        quantity=to_decimal(add_quantity) if add_quantity and add_quantity > 0 else None,
                        note=add_note.strip(),  # CORRIGÉ ICI (Pas de 'or None')
                    )
                    tx_repo.create(tx)
                    st.success("✅ Transaction ajoutée.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")

    st.markdown("---")

    # Filtres
    f1, f2, f3 = st.columns([2, 2, 2])
    with f1:
        filter_product = st.selectbox("Filtrer produit", ["Tous"] + product_names, index=0)
    with f2:
        filter_type = st.selectbox("Filtrer type", ["Tous"] + [e.value for e in TransactionType], index=0)
    with f3:
        sort_mode = st.selectbox("Tri", ["Date décroissante", "Date croissante", "ID décroissant"], index=0)

    txs = tx_repo.get_all()

    # Filtrage

    if filter_product != "Tous":
        pid = product_by_name[filter_product].id
        txs = [t for t in txs if t.product_id == pid]

    if filter_type != "Tous":
        txs = [t for t in txs if t.type.value == filter_type]

    # Tri

    if sort_mode == "Date croissante":
        txs = sorted(txs, key=lambda t: t.date)
    elif sort_mode == "ID décroissant":
        txs = sorted(txs, key=lambda t: (t.id or 0), reverse=True)
    else:
        txs = sorted(txs, key=lambda t: t.date, reverse=True)

    rows = []

    for t in txs:
        p = product_by_id.get(t.product_id)
        rows.append(
            {
                "id": t.id,
                "date": t.date.date(),
                "produit": p.name if p else f"#{t.product_id}",
                "type": t.type.value,
                "montant_eur": float(t.amount_eur) if t.amount_eur is not None else 0.0,
                "quantite": float(t.quantity) if t.quantity is not None else 0.0,
                "note": t.note or "",
                "🗑️ Supprimer": False,
            }
        )

    if not rows:
        st.info("Aucune transaction pour ce filtre.")

        return

    df = pd.DataFrame(rows)

    st.subheader("Historique (éditable)")
    st.write("Modifiez des cellules puis cliquez sur “Appliquer les changements”.")

    edited = st.data_editor(
        df,
        key="tx_editor",
        hide_index=True,
        width="stretch",
        num_rows="fixed",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
            "produit": st.column_config.SelectboxColumn("Produit", options=product_names, required=True),
            "type": st.column_config.SelectboxColumn("Type", options=[e.value for e in TransactionType], required=True),
            "montant_eur": st.column_config.NumberColumn("Montant EUR", min_value=0.0, step=10.0),
            "quantite": st.column_config.NumberColumn("Quantité", min_value=0.0, step=1.0),
            "note": st.column_config.TextColumn("Note"),
            "🗑️ Supprimer": st.column_config.CheckboxColumn("🗑️ Supprimer"),
        },
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button("💾 Appliquer les changements", width="stretch"):
            try:
                edited_rows = edited.to_dict(orient="records")

                for r in edited_rows:
                    tx_id = r.get("id", None)

                    if tx_id is None or (isinstance(tx_id, float) and pd.isna(tx_id)):
                        continue

                    # 1. Traitement de la suppression en priorité

                    if bool(r.get("🗑️ Supprimer", False)):
                        tx_repo.delete(int(tx_id))

                        continue

                    # 2. Mise à jour des autres lignes
                    tx = tx_repo.get_by_id(int(tx_id))

                    if not tx:
                        continue

                    prod_name = r["produit"]
                    p = product_by_name.get(prod_name)

                    if not p or p.id is None:
                        raise ValueError(f"Produit invalide: {prod_name!r}")

                    tx.product_id = p.id
                    tx.date = datetime.combine(r["date"], datetime.min.time())
                    tx.type = _enum_from_value(TransactionType, r["type"])

                    amount = float(r.get("montant_eur") or 0.0)
                    qty = float(r.get("quantite") or 0.0)
                    tx.amount_eur = to_decimal(amount) if amount > 0 else None
                    tx.quantity = to_decimal(qty) if qty > 0 else None

                    tx.note = str(r.get("note") or "").strip()  # CORRIGÉ ICI (Chaîne vide assurée)

                    tx_repo.update(tx)

                st.success("✅ Changements appliqués.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur : {e}")

    with c2:
        if st.button("↩️ Recharger depuis la DB", width="stretch"):
            st.rerun()
