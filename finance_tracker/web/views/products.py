import streamlit as st
import pandas as pd

from sqlmodel import Session

from finance_tracker.domain.enums import ProductType, QuantityUnit
from finance_tracker.domain.models import Product
from finance_tracker.repositories.sqlmodel_repo import (
    SQLModelProductRepository,
    SQLModelTransactionRepository,
    SQLModelValuationRepository,
    )


def _enum_from_value(enum_cls, value: str):
    """Retrieve the enum member matching the given value.

    Iterates through the enum class and returns the first member whose
    value equals the provided string.

    Parameters
    ----------
    enum_cls : type
        The enum class to search within.
    value : str
        The string value to match against enum members.

    Returns
    -------
    enum.Enum
        The enum member whose value matches the input string.

    Raises
    ------
    ValueError
        If no enum member matches the provided value.
    """

    for e in enum_cls:
        if e.value == value:
            return e
    raise ValueError(f"Valeur enum inconnue: {value!r}")


def render(session: Session) -> None:
    """
    Render the Products management page in the Streamlit application.

    This page provides a CRUD (Create, Read, Update, Delete) interface for
    managing financial products in the portfolio. Users can add new products,
    edit existing ones, and delete products (with referential integrity checks).

    The page is organized into three main sections:

    1. Add Product Form - Expander with form for creating new products
    2. Products Table - Editable data editor with inline modifications
    3. Advanced Deletion Tools - Guidance for cascade deletion scenarios

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
    Product creation validates:
    - Name is mandatory and must be unique
    - Type and unit are selected from predefined enums

    Product deletion may fail if:
    - Transactions reference the product (foreign key constraint)
    - Valuations reference the product (foreign key constraint)

    In case of deletion failure, users are guided to manually delete
    related transactions/valuations first.

    The editable table uses st.data_editor with a delete checkbox column.
    Changes are applied in batch via a single "Apply" button.

    Examples
    --------
    >>> from finance_tracker.web.db import get_session
    >>> session = get_session()
    >>> render(session)  # Renders the Products page in Streamlit
    """
    st.title("🏷️ Mes Produits")
    st.caption("Créez, éditez et supprimez vos produits. (La suppression peut échouer si des transactions/valorisations existent.)")

    # Initialize repositories for database operations
    product_repo = SQLModelProductRepository(session)
    tx_repo = SQLModelTransactionRepository(session)
    val_repo = SQLModelValuationRepository(session)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1: ADD PRODUCT FORM
    # ═══════════════════════════════════════════════════════════════════════════

    with st.expander("➕ Ajouter un produit", expanded=False):
        with st.form("product_add_form", clear_on_submit=True):
            c1, c2 = st.columns([2, 2])

            with c1:
                name = st.text_input("Nom *")
                ptype = st.selectbox("Type", [e.value for e in ProductType])
                unit = st.selectbox("Unité", [e.value for e in QuantityUnit])
                risk = st.text_input("Niveau de risque (optionnel)", value="")

            with c2:
                description = st.text_area("Description", height=80)
                fees = st.text_area("Frais", height=80)
                tax = st.text_area("Fiscalité", height=80)

            submitted = st.form_submit_button("Créer", width="stretch")

            if submitted:
                try:
                    # Validate mandatory name field

                    if not name.strip():
                        st.error("Le nom est obligatoire.")
                        st.stop()

                    # Check for duplicate product names
                    existing = product_repo.get_by_name(name.strip())

                    if existing:
                        st.error(f"Un produit nommé '{name}' existe déjà.")
                        st.stop()

                    # Create new product with form data
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
                    st.success("✅ Produit créé.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")

    st.markdown("---")

    # Retrieve all products for the editable table
    products = product_repo.get_all()

    # Early return if no products exist

    if not products:
        st.info("Aucun produit pour l'instant.")

        return

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2: EDITABLE PRODUCTS TABLE
    # ═══════════════════════════════════════════════════════════════════════════

    # Build rows for the data editor
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
                "🗑️ Supprimer": False,  # Checkbox for deletion marking
                }
            )

    df = pd.DataFrame(rows)

    st.subheader("Liste des produits (éditable)")
    edited = st.data_editor(
        df,
        key="products_editor",
        hide_index=True,
        width="stretch",
        num_rows="fixed",  # Prevent adding/deleting rows directly in editor
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "name": st.column_config.TextColumn("Nom", required=True),
            "type": st.column_config.SelectboxColumn("Type", options=[e.value for e in ProductType], required=True),
            "quantity_unit": st.column_config.SelectboxColumn("Unité", options=[e.value for e in QuantityUnit], required=True),
            "risk_level": st.column_config.TextColumn("Risque"),
            "description": st.column_config.TextColumn("Description"),
            "fees_description": st.column_config.TextColumn("Frais"),
            "tax_info": st.column_config.TextColumn("Fiscalité"),
            "created_at": st.column_config.DateColumn("Créé le", disabled=True, format="YYYY-MM-DD"),
            "🗑️ Supprimer": st.column_config.CheckboxColumn("🗑️ Supprimer"),
            },
        )

    # ══════════════════════════════════════════════════���════════════════════════
    # SECTION 3: ADVANCED DELETION TOOLS (Guidance)
    # ═══════════════════════════════════════════════════════════════════════════

    with st.expander("🧨 Outils suppression (avancé)", expanded=False):
        st.write("Si une suppression de produit échoue, supprimez d'abord les transactions/valorisations associées.")
        st.write("Astuce: utilisez la page Transactions / Valorisations, filtrez par produit, cochez 🗑️ puis appliquez.")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 4: ACTION BUTTONS
    # ═══════════════════════════════════════════════════════════════════════════

    c1, c2 = st.columns([2, 1])

    with c1:
        if st.button("💾 Appliquer les changements", width="stretch"):
            try:
                edited_rows = edited.to_dict(orient="records")

                # ═══════════════════════════════════════════════════════════════
                # VALIDATION: Check for empty and duplicate names
                # ═══════════════════════════════════════════════════════════════
                names = [
                    str(r.get("name", "")).strip()

                    for r in edited_rows

                    if not bool(r.get("🗑️ Supprimer", False))
                    ]

                if any(not n for n in names):
                    raise ValueError("Tous les produits (non supprimés) doivent avoir un nom.")

                if len(set(names)) != len(names):
                    raise ValueError("Les noms de produits doivent être uniques (au moins parmi les lignes non supprimées).")

                # ═══════════════════════════════════════════════════════════════
                # PROCESS EACH ROW: Delete or Update
                # ═══════════════════════════════════════════════════════════════

                for r in edited_rows:
                    pid = r.get("id", None)

                    # Skip rows without valid ID (should not happen in fixed rows mode)

                    if pid is None or (isinstance(pid, float) and pd.isna(pid)):
                        continue

                    pid = int(pid)

                    # Handle deletion first (priority over updates)

                    if bool(r.get("🗑️ Supprimer", False)):
                        # May fail if child records exist (referential integrity)
                        product_repo.delete(pid)

                        continue

                    # Handle updates for non-deleted rows
                    p = product_repo.get_by_id(pid)

                    if not p:
                        continue

                    new_name = str(r.get("name", "")).strip()

                    if not new_name:
                        raise ValueError("Nom produit vide.")

                    # Update product fields
                    p.name = new_name
                    p.type = _enum_from_value(ProductType, r["type"])
                    p.quantity_unit = _enum_from_value(QuantityUnit, r["quantity_unit"])
                    p.risk_level = str(r.get("risk_level") or "").strip()
                    p.description = str(r.get("description") or "").strip()
                    p.fees_description = str(r.get("fees_description") or "").strip()
                    p.tax_info = str(r.get("tax_info") or "").strip()

                    product_repo.update(p)

                st.success("✅ Changements appliqués.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur : {e}")

    with c2:
        # Reload button to discard edits and fetch fresh data

        if st.button("↩️ Recharger depuis la DB", width="stretch"):
            st.rerun()
