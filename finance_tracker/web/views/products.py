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
    for e in enum_cls:
        if e.value == value:
            return e
    raise ValueError(f"Valeur enum inconnue: {value!r}")


def render(session: Session) -> None:
    st.title("🧾 Produits")
    st.caption("Créez, éditez et supprimez vos produits. (La suppression peut échouer si des transactions/valorisations existent.)")

    product_repo = SQLModelProductRepository(session)
    tx_repo = SQLModelTransactionRepository(session)
    val_repo = SQLModelValuationRepository(session)

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

            submitted = st.form_submit_button("Créer", use_container_width=True)

            if submitted:
                try:
                    if not name.strip():
                        st.error("Le nom est obligatoire.")
                        st.stop()

                    existing = product_repo.get_by_name(name.strip())

                    if existing:
                        st.error(f"Un produit nommé '{name}' existe déjà.")
                        st.stop()

                    p = Product(
                        name=name.strip(),
                        type=_enum_from_value(ProductType, ptype),
                        quantity_unit=_enum_from_value(QuantityUnit, unit),
                        description=str(description or "").strip(),        # Corrigé
                        risk_level=str(risk or "").strip(),                # Corrigé
                        fees_description=str(fees or "").strip(),          # Corrigé
                        tax_info=str(tax or "").strip(),                   # Corrigé
                    )
                    product_repo.create(p)
                    st.success("✅ Produit créé.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")

    st.markdown("---")

    products = product_repo.get_all()

    if not products:
        st.info("Aucun produit pour l’instant.")

        return

    # Table éditable
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
                "🗑️ Supprimer": False,
            }
        )

    df = pd.DataFrame(rows)

    st.subheader("Liste des produits (éditable)")
    edited = st.data_editor(
        df,
        key="products_editor",
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
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

    # Option UX : zone “danger” pour suppression en cascade (manuelle)
    with st.expander("🧨 Outils suppression (avancé)", expanded=False):
        st.write("Si une suppression de produit échoue, supprimez d’abord les transactions/valorisations associées.")
        st.write("Astuce: utilisez la page Transactions / Valorisations, filtrez par produit, cochez 🗑️ puis appliquez.")

    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button("💾 Appliquer les changements", use_container_width=True):
            try:
                edited_rows = edited.to_dict(orient="records")

                # Petite validation: noms non vides et uniques (dans l'éditeur)
                names = [str(r.get("name", "")).strip() for r in edited_rows if not bool(r.get("🗑️ Supprimer", False))]

                if any(not n for n in names):
                    raise ValueError("Tous les produits (non supprimés) doivent avoir un nom.")

                if len(set(names)) != len(names):
                    raise ValueError("Les noms de produits doivent être uniques (au moins parmi les lignes non supprimées).")

                for r in edited_rows:
                    pid = r.get("id", None)

                    if pid is None or (isinstance(pid, float) and pd.isna(pid)):
                        continue

                    pid = int(pid)

                    # 1. Traitement de la suppression en priorité

                    if bool(r.get("🗑️ Supprimer", False)):
                        # Peut échouer si des lignes enfant existent (intégrité référentielle SQLite).
                        product_repo.delete(pid)

                        continue

                    # 2. Mise à jour des autres lignes
                    p = product_repo.get_by_id(pid)

                    if not p:
                        continue

                    new_name = str(r.get("name", "")).strip()

                    if not new_name:
                        raise ValueError("Nom produit vide.")

                    p.name = new_name
                    p.type = _enum_from_value(ProductType, r["type"])
                    p.quantity_unit = _enum_from_value(QuantityUnit, r["quantity_unit"])

                    p.risk_level = str(r.get("risk_level") or "").strip()                 # Corrigé
                    p.description = str(r.get("description") or "").strip()               # Corrigé
                    p.fees_description = str(r.get("fees_description") or "").strip()     # Corrigé
                    p.tax_info = str(r.get("tax_info") or "").strip()                     # Corrigé

                    product_repo.update(p)

                st.success("✅ Changements appliqués.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur : {e}")

    with c2:
        if st.button("↩️ Recharger depuis la DB", use_container_width=True):
            st.rerun()
