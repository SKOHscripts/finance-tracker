import streamlit as st
from datetime import datetime, date
from sqlmodel import Session

from finance_tracker.domain.models import Valuation
from finance_tracker.repositories.sqlmodel_repo import SQLModelProductRepository, SQLModelValuationRepository
from finance_tracker.web.ui.formatters import to_decimal


def render_add(session: Session) -> None:
    st.header("Ajouter une valorisation")

    product_repo = SQLModelProductRepository(session)
    val_repo = SQLModelValuationRepository(session)

    products = product_repo.get_all()

    if not products:
        st.info("Aucun produit. Ajoute un produit d'abord.")

        return

    product_name = st.selectbox("Produit", [p.name for p in products])
    val_date = st.date_input("Date", value=date.today())
    total_value = st.number_input("Valeur totale EUR", value=0.0, step=1.0)
    unit_price = st.number_input("Prix unitaire EUR (optionnel)", value=0.0, step=1.0)

    if st.button("📈 Ajouter valorisation"):
        try:
            product = product_repo.get_by_name(product_name)

            if not product:
                st.error(f"Produit '{product_name}' non trouvé")

                return

            val = Valuation(
                product_id=product.id or 0,
                date=datetime.combine(val_date, datetime.min.time()),
                total_value_eur=to_decimal(total_value),
                unit_price_eur=to_decimal(unit_price) if unit_price > 0 else None,
            )
            val_repo.create(val)
            st.success(f"✅ Valorisation ajoutée pour {product_name}")
        except Exception as e:
            st.error(f"❌ Erreur : {e}")


def render_list(session: Session) -> None:
    st.header("Historique des valorisations")

    val_repo = SQLModelValuationRepository(session)
    product_repo = SQLModelProductRepository(session)

    products = product_repo.get_all()
    product_names = ["Tous"] + [p.name for p in products]
    selected_product = st.selectbox("Filtrer par produit", product_names)

    all_vals = val_repo.get_all()

    if selected_product != "Tous":
        product = product_repo.get_by_name(selected_product)

        if product:
            all_vals = [v for v in all_vals if v.product_id == product.id]

    rows = []

    for val in all_vals:
        product = product_repo.get_by_id(val.product_id)
        rows.append({
            "ID": val.id,
            "Date": val.date.strftime("%Y-%m-%d"),
            "Produit": product.name if product else "?",
            "Valeur EUR": f"{float(val.total_value_eur):.2f}",
            "Prix unitaire": f"{float(val.unit_price_eur):.2f}" if val.unit_price_eur else "-",
        })

    if rows:
        st.dataframe(rows, width="stretch")
    else:
        st.info("Aucune valorisation")
