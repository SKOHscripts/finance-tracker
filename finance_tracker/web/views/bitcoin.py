"""
Bitcoin — Page enrichie avec historique, indicateurs et graphique.
"""
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date

from sqlmodel import Session
from finance_tracker.domain.models import Valuation
from finance_tracker.repositories.sqlmodel_repo import (
    SQLModelProductRepository,
    SQLModelValuationRepository,
)
from finance_tracker.services.btc_price_service import BTCPriceService, BTCPriceServiceError
from finance_tracker.web.ui.formatters import to_decimal


# ─── Helpers ────────────────────────────────────────────────────────────────
def _fmt_eur(v: float) -> str:
    return f"{v:,.2f} €".replace(",", " ")


def _delta_color(v: float) -> str:
    return "#16a34a" if v >= 0 else "#dc2626"


def _delta_icon(v: float) -> str:
    return "▲" if v >= 0 else "▼"


# ─── Rendu ──────────────────────────────────────────────────────────────────
def render(session: Session) -> None:
    product_repo = SQLModelProductRepository(session)
    val_repo = SQLModelValuationRepository(session)

    btc_product = product_repo.get_by_name("Bitcoin")

    if not btc_product:
        st.warning("⚠️ Le produit 'Bitcoin' n'existe pas. Créez-le dans **🏷️ Mes Produits**.")

        return

    # ── Récupération des valorisations historiques ──
    all_vals = [v for v in val_repo.get_all() if v.product_id == btc_product.id]
    all_vals_sorted = sorted(all_vals, key=lambda v: v.date)

    live_price: float | None = st.session_state.get("btc_price")
    last_snapshot_price = float(all_vals_sorted[-1].unit_price_eur) if all_vals_sorted and all_vals_sorted[-1].unit_price_eur else None
    latest_total = float(all_vals_sorted[-1].total_value_eur) if all_vals_sorted else 0.0

    # ── Calcul du PRU (prix de revient unitaire) depuis les transactions ──
    from finance_tracker.repositories.sqlmodel_repo import SQLModelTransactionRepository
    from finance_tracker.domain.enums import TransactionType
    tx_repo = SQLModelTransactionRepository(session)
    all_txs = [t for t in tx_repo.get_all() if t.product_id == btc_product.id]
    buy_txs = [t for t in all_txs if t.type == TransactionType.BUY]
    total_invested = sum(float(t.amount_eur) for t in buy_txs if t.amount_eur)
    total_qty = sum(float(t.quantity) for t in buy_txs if t.quantity)
    pru = total_invested / total_qty if total_qty > 0 else None

    # ── P&L latente ──
    ref_price = live_price or last_snapshot_price
    pnl_pct = ((ref_price - pru) / pru * 100) if (ref_price and pru and pru > 0) else None
    pnl_eur = ((ref_price - pru) * total_qty) if (ref_price and pru and total_qty > 0) else None

    # ════════════════════════════════════════════════
    # 1. HERO PANEL
    # ════════════════════════════════════════════════
    price_display = f"{live_price:,.0f} €".replace(",", " ") if live_price else "---"
    status_badge = (
        "<span style='background:#16a34a;color:white;border-radius:20px;"
        "padding:2px 10px;font-size:12px;font-weight:600;'>● LIVE</span>"

        if live_price else
        "<span style='background:#6b7280;color:white;border-radius:20px;"
        "padding:2px 10px;font-size:12px;font-weight:600;'>● OFFLINE</span>"
    )

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
            border-radius: 16px;
            padding: 32px 40px;
            margin-bottom: 24px;
            border: 1px solid #F7931A44;
        ">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div style="color:#F7931A; font-size:48px; font-weight:900; letter-spacing:-1px;">₿</div>
                    <div style="color:#9ca3af; font-size:14px; margin-top:-8px;">Bitcoin · BTC/EUR</div>
                </div>
                <div style="text-align:right;">
                    {status_badge}
                    <div style="color:white; font-size:42px; font-weight:800; margin-top:4px; letter-spacing:-1px;">{price_display}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Bouton de refresh compact, en dehors du hero
    col_refresh, col_spacer = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 Actualiser le cours", use_container_width=True):
            with st.spinner("Connexion aux APIs..."):
                try:
                    st.session_state.btc_price = float(
                        BTCPriceService().get_btc_price_eur()
                    )
                    st.session_state.api_error = None
                    st.rerun()
                except BTCPriceServiceError:
                    st.session_state.api_error = True

    if st.session_state.get("api_error"):
        st.warning("📡 **Hors ligne** — Réseau inaccessible. Saisissez le prix manuellement ci-dessous.")

    # ════════════════════════════════════════════════
    # 2. INDICATEURS CLÉS
    # ════════════════════════════════════════════════
    st.markdown("### 📊 Indicateurs")

    i1, i2, i3, i4 = st.columns(4)
    with i1:
        st.metric("💼 Valeur actuelle", _fmt_eur(latest_total) if latest_total else "—")
    with i2:
        st.metric("💸 Total investi", _fmt_eur(total_invested) if total_invested else "—")
    with i3:
        if pru:
            st.metric("📌 PRU (Prix de revient)", _fmt_eur(pru))
        else:
            st.metric("📌 PRU (Prix de revient)", "—")
    with i4:
        if pnl_eur is not None and pnl_pct is not None:
            st.metric(
                "📈 P&L Latente",
                _fmt_eur(pnl_eur),
                delta=f"{pnl_pct:+.2f}%",
                delta_color="normal"
            )
        else:
            st.metric("📈 P&L Latente", "—")

    # ════════════════════════════════════════════════
    # 3. GRAPHIQUE HISTORIQUE DES SNAPSHOTS
    # ════════════════════════════════════════════════
    if len(all_vals_sorted) >= 2:
        st.markdown("### 📉 Historique des prix (snapshots)")

        chart_data = pd.DataFrame([
            {
                "date": v.date.date(),
                "Prix snapshot (€)": float(v.unit_price_eur) if v.unit_price_eur else None,
                "Valeur totale (€)": float(v.total_value_eur),
            }
            for v in all_vals_sorted
            if v.unit_price_eur
        ])

        if not chart_data.empty:
            # Ligne prix + ligne de PRU si disponible
            base = alt.Chart(chart_data).encode(
                x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %Y")),
            )

            line_price = base.mark_line(
                color="#F7931A", strokeWidth=2.5
            ).encode(
                y=alt.Y("Prix snapshot (€):Q", title="Prix BTC (€)"),
                tooltip=[
                    alt.Tooltip("date:T", title="Date", format="%d/%m/%Y"),
                    alt.Tooltip("Prix snapshot (€):Q", title="Prix (€)", format=",.0f"),
                ]
            )

            points = base.mark_circle(
                color="#F7931A", size=60
            ).encode(
                y="Prix snapshot (€):Q",
            )

            chart = (line_price + points).properties(height=260)

            # Ligne PRU de référence en pointillés si disponible
            if pru:
                pru_data = pd.DataFrame([
                    {"date": chart_data["date"].min(), "PRU": pru},
                    {"date": chart_data["date"].max(), "PRU": pru},
                ])
                pru_line = alt.Chart(pru_data).mark_line(
                    color="#6366f1", strokeDash=[6, 4], strokeWidth=1.8
                ).encode(
                    x="date:T",
                    y=alt.Y("PRU:Q"),
                    tooltip=[alt.Tooltip("PRU:Q", title="PRU (€)", format=",.0f")]
                )
                chart = (chart + pru_line).properties(height=260)

            st.altair_chart(chart, use_container_width=True)
            st.caption("🟠 Courbe de prix · 🟣 Ligne pointillée = PRU")

    elif all_vals_sorted:
        st.info("💡 Ajoutez au moins 2 snapshots avec un prix unitaire pour afficher l'évolution historique.")

    # ════════════════════════════════════════════════
    # 4. FORMULAIRE D'AJOUT DE SNAPSHOT
    # ════════════════════════════════════════════════
    st.markdown("### 📸 Nouveau Snapshot")

    with st.form("btc_val_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            val_date = st.date_input("Date", value=date.today())
        with c2:
            default_price = live_price or (last_snapshot_price or 0.0)
            btc_unit_price = st.number_input("Prix d'un BTC (EUR)", value=default_price, step=100.0)
        with c3:
            btc_quantity = st.number_input(
                "Quantité (BTC)",
                value=round(total_qty, 8) if total_qty > 0 else 0.0,
                step=0.001,
                format="%.8f",
                help="Vous pouvez pré-remplir avec votre quantité connue."
            )

        if btc_unit_price > 0 and btc_quantity > 0:
            st.info(f"💶 Valeur calculée : **{_fmt_eur(btc_unit_price * btc_quantity)}**"
                    + (f" · P&L vs PRU : **{((btc_unit_price - pru) / pru * 100):+.2f}%**" if pru else ""))

        submit = st.form_submit_button(
            "💾 Enregistrer le snapshot",
            type="primary",
            use_container_width=True
        )

        if submit:
            if btc_quantity <= 0 or btc_unit_price <= 0:
                st.error("La quantité et le prix doivent être > 0.")
            else:
                try:
                    val_repo.create(Valuation(
                        product_id=btc_product.id,
                        date=datetime.combine(val_date, datetime.min.time()),
                        total_value_eur=to_decimal(btc_quantity * btc_unit_price),
                        unit_price_eur=to_decimal(btc_unit_price),
                    ))
                    st.success(f"✅ Snapshot enregistré — Valeur : {_fmt_eur(btc_unit_price * btc_quantity)}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")

    # ════════════════════════════════════════════════
    # 5. DERNIERS SNAPSHOTS
    # ════════════════════════════════════════════════
    if all_vals_sorted:
        st.markdown("### 🗓️ Derniers snapshots")

        recent = list(reversed(all_vals_sorted))[:8]
        rows = []
        for v in recent:
            rows.append({
                "Date": v.date.strftime("%d/%m/%Y"),
                "Prix BTC (€)": f"{float(v.unit_price_eur):,.0f}".replace(",", " ") if v.unit_price_eur else "—",
                "Valeur totale (€)": f"{float(v.total_value_eur):,.2f}".replace(",", " "),
                "vs PRU": (
                    f"{((float(v.unit_price_eur) - pru) / pru * 100):+.2f}%"
                    if (v.unit_price_eur and pru)
                    else "—"
                ),
            })

        st.dataframe(
            pd.DataFrame(rows),
            hide_index=True,
            use_container_width=True,
        )
