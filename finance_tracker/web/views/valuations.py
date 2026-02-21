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


def render(session: Session) -> None:
    st.title("📈 Valorisations")
    st.caption("Snapshots de valeur : ajout, édition et suppression depuis une table unique.")

    product_repo = SQLModelProductRepository(session)
    val_repo = SQLModelValuationRepository(session)

    products = product_repo.get_all()

    if not products:
        st.info("Aucun produit. Créez un produit avant d’ajouter des valorisations.")

        return

    product_names = [p.name for p in products]
    product_by_name = {p.name: p for p in products}
    product_by_id = {p.id: p for p in products if p.id is not None}

    with st.expander("➕ Ajouter une valorisation", expanded=False):
        # Sélecteur sorti du form pour dynamique
        add_product_name = st.selectbox("Produit", product_names, key="val_add_product")
        is_btc = add_product_name.lower() == "bitcoin"

        with st.form("val_add_form", clear_on_submit=True):
            c1, c2 = st.columns([2, 2])
            with c1:
                add_date = st.date_input("Date", value=date.today(), key="val_add_date")
            with c2:
                add_total = st.number_input("Valeur totale EUR", value=0.0, step=0.01, format="%.2f", key="val_add_total")

                # Le libellé change pour être précis
                unit_label = "Prix d'un BTC plein (EUR)" if is_btc else "Prix unitaire (EUR, optionnel)"
                add_unit = st.number_input(unit_label, value=0.0, step=0.01, format="%.2f", key="val_add_unit")

            submitted = st.form_submit_button("Ajouter", width="stretch")

            if submitted:
                try:
                    p = product_by_name.get(add_product_name)

                    if not p or p.id is None:
                        st.stop()

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

    f1, f2 = st.columns([2, 2])
    with f1:
        filter_product = st.selectbox("Filtrer produit", ["Tous"] + product_names, index=0)
    with f2:
        sort_mode = st.selectbox("Tri", ["Date décroissante", "Date croissante", "ID décroissant"], index=0)

    vals = val_repo.get_all()

    if filter_product != "Tous":
        pid = product_by_name[filter_product].id
        vals = [v for v in vals if v.product_id == pid]

    if sort_mode == "Date croissante":
        vals = sorted(vals, key=lambda v: v.date)
    elif sort_mode == "ID décroissant":
        vals = sorted(vals, key=lambda v: (v.id or 0), reverse=True)
    else:
        vals = sorted(vals, key=lambda v: v.date, reverse=True)

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

    if not rows:
        st.info("Aucune valorisation pour ce filtre.")

        return

    df = pd.DataFrame(rows)

    st.subheader("Historique (éditable)")
    edited = st.data_editor(
        df,
        key="val_editor",
        hide_index=True,
        width="stretch",
        num_rows="fixed",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
            "produit": st.column_config.SelectboxColumn("Produit", options=product_names, required=True),
            "valeur_totale_eur": st.column_config.NumberColumn("Valeur totale EUR", min_value=0.0, step=0.01, format="%.2f"),
            "prix_unitaire_eur": st.column_config.NumberColumn("Prix unitaire EUR", min_value=0.0, step=0.01, format="%.2f"),
            "🗑️ Supprimer": st.column_config.CheckboxColumn("🗑️ Supprimer"),
        },
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button("💾 Appliquer les changements", width="stretch"):
            try:
                edited_rows = edited.to_dict(orient="records")

                for r in edited_rows:
                    val_id = r.get("id", None)

                    if val_id is None or (isinstance(val_id, float) and pd.isna(val_id)):
                        continue

                    if bool(r.get("🗑️ Supprimer", False)):
                        val_repo.delete(int(val_id))

                        continue

                    v = val_repo.get_by_id(int(val_id))

                    if not v:
                        continue

                    prod_name = r["produit"]
                    p = product_by_name.get(prod_name)

                    if not p or p.id is None:
                        raise ValueError(f"Produit invalide: {prod_name!r}")

                    total = float(r.get("valeur_totale_eur") or 0.0)
                    unit = float(r.get("prix_unitaire_eur") or 0.0)

                    if total <= 0:
                        raise ValueError("La valeur totale doit être > 0.")

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
        if st.button("↩️ Recharger depuis la DB", width="stretch"):
            st.rerun()
