import streamlit as st
import pandas as pd

from sqlmodel import Session

from finance_tracker.domain.enums import ProductType, QuantityUnit
from finance_tracker.domain.models import Product
from finance_tracker.i18n import t
from finance_tracker.repositories.sqlmodel_repo import (
    SQLModelProductRepository,
    SQLModelTransactionRepository,
    SQLModelValuationRepository,
    )


def _enum_from_value(enum_cls, value: str):
    """Retrieve the enum member matching the given value."""
    for e in enum_cls:
        if e.value == value:
            return e
    raise ValueError(f"Valeur enum inconnue: {value!r}")


def render(session: Session) -> None:
    """Render the Products management page in the Streamlit application."""
    st.title(t("products.title"))
    st.caption(t("products.caption"))

    # Initialize repositories for database operations
    product_repo = SQLModelProductRepository(session)
    tx_repo = SQLModelTransactionRepository(session)
    val_repo = SQLModelValuationRepository(session)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1: ADD PRODUCT FORM
    # ═══════════════════════════════════════════════════════════════════════════

    with st.expander(f"➕ {t('products.add_expander')}", expanded=False):
        with st.form("product_add_form", clear_on_submit=True):
            c1, c2 = st.columns([2, 2])

            with c1:
                name = st.text_input(t("products.field_name"))
                ptype = st.selectbox(t("products.field_type"), [e.value for e in ProductType])
                unit = st.selectbox(t("products.field_unit"), [e.value for e in QuantityUnit])
                risk = st.text_input(t("products.field_risk"), value="")

            with c2:
                description = st.text_area(t("products.field_description"), height=80)
                fees = st.text_area(t("products.field_fees"), height=80)
                tax = st.text_area(t("products.field_tax"), height=80)

            submitted = st.form_submit_button(t("products.create_btn"), width="stretch")

            if submitted:
                try:
                    if not name.strip():
                        st.error(t("products.name_required"))
                        st.stop()

                    existing = product_repo.get_by_name(name.strip())

                    if existing:
                        st.error(t("products.name_duplicate").format(name=name))
                        st.stop()

                    p = Product(
                        name=name.strip(),
                        type=_enum_from_value(ProductType, ptype),
                        quantity_unit=_enum_from_value(QuantityUnit, unit),
                        description=str(description or "").strip(),
                        risk_level=str(risk or "").strip(),
                        fees_description=str(fees or "").strip(),
                        tax_info=str(tax or "").strip(),
                        )
                    product_repo.create(p)
                    st.success(t("products.created_success"))
                    st.rerun()
                except Exception as e:
                    st.error(t("products.error").format(e=e))

    st.markdown("---")

    # Retrieve all products for the editable table
    products = product_repo.get_all()

    if not products:
        st.info(t("products.empty"))
        return

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2: EDITABLE PRODUCTS TABLE
    # ═══════════════════════════════════════════════════════════════════════════

    delete_col = t("products.col_delete")
    rows = []

    for p in products:
        rows.append(
            {
                "id": p.id,
                "name": p.name,
                "type": p.type.value,
                "quantity_unit": p.quantity_unit.value,
                "risk_level": p.risk_level or "",
                "description": p.description or "",
                "fees_description": p.fees_description or "",
                "tax_info": p.tax_info or "",
                "created_at": p.created_at.date() if getattr(p, "created_at", None) else None,
                delete_col: False,
                }
            )

    df = pd.DataFrame(rows)

    st.subheader(t("products.list_title"))
    edited = st.data_editor(
        df,
        key="products_editor",
        hide_index=True,
        width="stretch",
        num_rows="fixed",
        column_config={
            "id": st.column_config.NumberColumn(t("products.col_id"), disabled=True),
            "name": st.column_config.TextColumn(t("products.col_name"), required=True),
            "type": st.column_config.SelectboxColumn(t("products.col_type"), options=[e.value for e in ProductType], required=True),
            "quantity_unit": st.column_config.SelectboxColumn(t("products.col_unit"), options=[e.value for e in QuantityUnit], required=True),
            "risk_level": st.column_config.TextColumn(t("products.col_risk")),
            "description": st.column_config.TextColumn(t("products.col_description")),
            "fees_description": st.column_config.TextColumn(t("products.col_fees")),
            "tax_info": st.column_config.TextColumn(t("products.col_tax")),
            "created_at": st.column_config.DateColumn(t("products.col_created_at"), disabled=True, format="YYYY-MM-DD"),
            delete_col: st.column_config.CheckboxColumn(delete_col),
            },
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3: ADVANCED DELETION TOOLS
    # ═══════════════════════════════════════════════════════════════════════════

    with st.expander(t("products.advanced_delete_expander"), expanded=False):
        st.write(t("products.advanced_delete_help"))
        st.write(t("products.advanced_delete_tip"))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 4: ACTION BUTTONS
    # ═══════════════════════════════════════════════════════════════════════════

    c1, c2 = st.columns([2, 1])

    with c1:
        if st.button(t("products.apply_btn"), width="stretch"):
            try:
                edited_rows = edited.to_dict(orient="records")

                names = [
                    str(r.get("name", "")).strip()
                    for r in edited_rows
                    if not bool(r.get(delete_col, False))
                    ]

                if any(not n for n in names):
                    raise ValueError(t("products.name_empty_error"))

                if len(set(names)) != len(names):
                    raise ValueError(t("products.name_unique_error"))

                for r in edited_rows:
                    pid = r.get("id", None)

                    if pid is None or (isinstance(pid, float) and pd.isna(pid)):
                        continue

                    pid = int(pid)

                    if bool(r.get(delete_col, False)):
                        product_repo.delete(pid)
                        continue

                    p = product_repo.get_by_id(pid)

                    if not p:
                        continue

                    new_name = str(r.get("name", "")).strip()

                    if not new_name:
                        raise ValueError(t("products.name_required"))

                    p.name = new_name
                    p.type = _enum_from_value(ProductType, r["type"])
                    p.quantity_unit = _enum_from_value(QuantityUnit, r["quantity_unit"])
                    p.risk_level = str(r.get("risk_level") or "").strip()
                    p.description = str(r.get("description") or "").strip()
                    p.fees_description = str(r.get("fees_description") or "").strip()
                    p.tax_info = str(r.get("tax_info") or "").strip()

                    product_repo.update(p)

                st.success(t("products.applied_success"))
                st.rerun()
            except Exception as e:
                st.error(t("products.error").format(e=e))

    with c2:
        if st.button(t("products.reload_btn"), width="stretch"):
            st.rerun()
