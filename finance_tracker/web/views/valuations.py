"""
valuations.py — Streamlit UI for valuation management.
"""

import streamlit as st
import pandas as pd

from datetime import datetime, date
from sqlmodel import Session

from finance_tracker.domain.models import Valuation
from finance_tracker.i18n import t
from finance_tracker.repositories.sqlmodel_repo import (
    SQLModelProductRepository,
    SQLModelValuationRepository,
    )
from finance_tracker.web.ui.formatters import to_decimal


def render(session: Session) -> None:
    """Render the Valuations management page in the Streamlit application."""
    st.title(t("valuations.title"))
    st.caption(t("valuations.caption"))

    product_repo = SQLModelProductRepository(session)
    val_repo = SQLModelValuationRepository(session)

    products = product_repo.get_all()

    if not products:
        st.info(t("valuations.no_products"))
        return

    product_names = [p.name for p in products]
    product_by_name = {p.name: p for p in products}
    product_by_id = {p.id: p for p in products if p.id is not None}

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1: ADD VALUATION FORM
    # ═══════════════════════════════════════════════════════════════════════════
    with st.expander(f"➕ {t('valuations.add_expander')}", expanded=False):
        add_product_name = st.selectbox(t("valuations.field_product"), product_names, key="val_add_product")

        is_btc = add_product_name.lower() == "bitcoin"

        with st.form("val_add_form", clear_on_submit=True):
            c1, c2 = st.columns([2, 2])
            with c1:
                add_date = st.date_input(t("valuations.field_date"), value=date.today(), key="val_add_date")
            with c2:
                add_total = st.number_input(t("valuations.field_total"), value=0.0, step=0.01, format="%.2f", key="val_add_total")

                unit_label = t("valuations.field_unit_price_btc") if is_btc else t("valuations.field_unit_price")
                add_unit = st.number_input(unit_label, value=0.0, step=0.01, format="%.2f", key="val_add_unit")

            submitted = st.form_submit_button(t("valuations.add_btn"), width="stretch")

            if submitted:
                try:
                    p = product_by_name.get(add_product_name)

                    if not p or p.id is None:
                        st.stop()

                    if add_total <= 0:
                        st.error(t("valuations.total_positive_error"))
                        st.stop()

                    val = Valuation(
                        product_id=p.id,
                        date=datetime.combine(add_date, datetime.min.time()),
                        total_value_eur=to_decimal(add_total),
                        unit_price_eur=to_decimal(add_unit) if add_unit and add_unit > 0 else None,
                        )
                    val_repo.create(val)
                    st.success(t("valuations.added_success"))
                    st.rerun()
                except Exception as e:
                    st.error(t("valuations.error").format(e=e))

    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2: VALUATION LIST WITH FILTERS AND EDITABLE TABLE
    # ═══════════════════════════════════════════════════════════════════════════

    filter_all = t("valuations.filter_all")
    sort_date_desc = t("valuations.sort_date_desc")
    sort_date_asc = t("valuations.sort_date_asc")
    sort_id_desc = t("valuations.sort_id_desc")

    f1, f2 = st.columns([2, 2])
    with f1:
        filter_product = st.selectbox(t("valuations.filter_product"), [filter_all] + product_names, index=0)
    with f2:
        sort_mode = st.selectbox(t("valuations.sort_label"), [sort_date_desc, sort_date_asc, sort_id_desc], index=0)

    vals = val_repo.get_all()

    if filter_product != filter_all:
        pid = product_by_name[filter_product].id
        vals = [v for v in vals if v.product_id == pid]

    if sort_mode == sort_date_asc:
        vals = sorted(vals, key=lambda v: v.date)
    elif sort_mode == sort_id_desc:
        vals = sorted(vals, key=lambda v: (v.id or 0), reverse=True)
    else:
        vals = sorted(vals, key=lambda v: v.date, reverse=True)

    delete_col = t("valuations.col_delete")
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
                delete_col: False,
                }
            )

    if not rows:
        st.info(t("valuations.empty_filter"))
        return

    df = pd.DataFrame(rows)

    st.subheader(t("valuations.list_title"))

    edited = st.data_editor(
        df,
        key="val_editor",
        hide_index=True,
        width="stretch",
        num_rows="fixed",
        column_config={
            "id": st.column_config.NumberColumn(t("valuations.col_id"), disabled=True),
            "date": st.column_config.DateColumn(t("valuations.col_date"), format="YYYY-MM-DD"),
            "produit": st.column_config.SelectboxColumn(t("valuations.col_product"), options=product_names, required=True),
            "valeur_totale_eur": st.column_config.NumberColumn(t("valuations.col_total"), min_value=0.0, step=0.01, format="%.2f"),
            "prix_unitaire_eur": st.column_config.NumberColumn(t("valuations.col_unit_price"), min_value=0.0, step=0.01, format="%.2f"),
            delete_col: st.column_config.CheckboxColumn(delete_col),
            },
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3: ACTION BUTTONS
    # ═══════════════════════════════════════════════════════════════════════════
    c1, c2 = st.columns([2, 1])

    with c1:
        if st.button(t("valuations.apply_btn"), width="stretch"):
            try:
                edited_rows = edited.to_dict(orient="records")

                for r in edited_rows:
                    val_id = r.get("id", None)

                    if val_id is None or (isinstance(val_id, float) and pd.isna(val_id)):
                        continue

                    if bool(r.get(delete_col, False)):
                        val_repo.delete(int(val_id))
                        continue

                    v = val_repo.get_by_id(int(val_id))

                    if not v:
                        continue

                    prod_name = r["produit"]
                    p = product_by_name.get(prod_name)

                    if not p or p.id is None:
                        raise ValueError(t("valuations.invalid_product").format(name=prod_name))

                    total = float(r.get("valeur_totale_eur") or 0.0)
                    unit = float(r.get("prix_unitaire_eur") or 0.0)

                    if total <= 0:
                        raise ValueError(t("valuations.total_positive_update_error"))

                    v.product_id = p.id
                    v.date = datetime.combine(r["date"], datetime.min.time())
                    v.total_value_eur = to_decimal(total)
                    v.unit_price_eur = to_decimal(unit) if unit > 0 else None

                    val_repo.update(v)

                st.success(t("valuations.applied_success"))
                st.rerun()
            except Exception as e:
                st.error(t("valuations.error").format(e=e))

    with c2:
        if st.button(t("valuations.reload_btn"), width="stretch"):
            st.rerun()
