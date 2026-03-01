"""
Bitcoin — Enriched page with history, indicators, and chart.
Consistent input and display in Satoshis (Sats), without double conversion from transactions.
"""
# Standard library
from datetime import datetime, date

# Third-party packages
import altair as alt
import pandas as pd
import streamlit as st
from sqlmodel import Session

# Local application imports
from finance_tracker.domain.models import Valuation
from finance_tracker.repositories.sqlmodel_repo import (
    SQLModelProductRepository,
    SQLModelValuationRepository,
    )
from finance_tracker.services.btc_price_service import BTCPriceService, BTCPriceServiceError
from finance_tracker.web.ui.formatters import to_decimal


# 1 BTC = 100 million satoshis, the smallest unit of Bitcoin
SATS_PER_BTC = 100_000_000


def _fmt_eur(v: float) -> str:
    # French locale uses space as thousands separator, not comma

    return f"{v:,.2f} €".replace(",", " ")


def _fmt_sats(v: float) -> str:
    # Satoshis are integers; float input must be converted before formatting

    return f"{int(v):,} Sats".replace(",", " ")


def render(session: Session) -> None:
    """
    Render the Bitcoin tracking page in the Streamlit application.

    This page provides a comprehensive Bitcoin portfolio tracking interface,
    including live price display, historical valuations chart, P&L calculations,
    and a form to record new snapshots.

    The page is organized into five main sections:

    1. Hero Panel - Live/offline price display with status badge
    2. Key Indicators - Current value, quantity, PRU, and P&L
    3. Historical Chart - Price evolution over time with PRU reference line
    4. Snapshot Form - Input new valuations with auto-calculated totals
    5. Recent Snapshots - Table of the last 8 recorded valuations

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
    - Live price is fetched from CoinGecko API via BTCPriceService
    - Price is cached in st.session_state to avoid API rate limits
    - Quantity is calculated from the latest snapshot (not from transactions)
    - PRU (Prix de Revient Unitaire) is calculated from BUY transactions
    - Quantity is displayed in Satoshis (1 BTC = 100,000,000 Sats)

    The function requires a 'Bitcoin' product to exist in the database.
    If not found, displays a warning and returns early.

    Examples
    --------
    >>> from finance_tracker.web.db import get_session
    >>> session = get_session()
    >>> render(session)  # Renders the Bitcoin page in Streamlit
    """
    # Initialize repositories for database access
    product_repo = SQLModelProductRepository(session)
    val_repo = SQLModelValuationRepository(session)

    # Retrieve the Bitcoin product from database
    btc_product = product_repo.get_by_name("Bitcoin")

    # Early return if Bitcoin product doesn't exist

    if not btc_product:
        st.warning("⚠️ Le produit 'Bitcoin' n'existe pas. Créez-le dans **🏷️ Mes Produits**.")

        return

    # ═══════════════════════════════════════════════════════════════════════════
    # HISTORICAL VALUATIONS RETRIEVAL
    # ═══════════════════════════════════════════════════════════════════════════

    # Fetch all valuations for Bitcoin product, sorted chronologically
    all_vals = [v for v in val_repo.get_all() if v.product_id == btc_product.id]
    all_vals_sorted = sorted(all_vals, key=lambda v: v.date)

    # Get live price from session state (cached from API)
    live_price: float | None = st.session_state.get("btc_price")

    # Extract price and total value from the most recent snapshot
    last_snapshot_price = (
        float(all_vals_sorted[-1].unit_price_eur)

        if all_vals_sorted and all_vals_sorted[-1].unit_price_eur
        else None
        )
    latest_total = float(all_vals_sorted[-1].total_value_eur) if all_vals_sorted else 0.0

    # ═══════════════════════════════════════════════════════════════════════════
    # QUANTITY CALCULATION
    # ═══════════════════════════════════════════════════════════════════════════

    # Deduce quantity owned from the latest snapshot only
    # This is more reliable than summing transactions for BTC
    total_qty_sats = 0
    total_qty_btc = 0.0

    if latest_total > 0 and last_snapshot_price and last_snapshot_price > 0:
        total_qty_btc = latest_total / last_snapshot_price
        total_qty_sats = int(total_qty_btc * SATS_PER_BTC)

    # ═══════════════════════════════════════════════════════════════════════════
    # PRU CALCULATION (Average Purchase Price)
    # ═══════════════════════════════════════════════════════════════════════════

    from finance_tracker.repositories.sqlmodel_repo import SQLModelTransactionRepository
    from finance_tracker.domain.enums import TransactionType
    tx_repo = SQLModelTransactionRepository(session)

    # Retrieve all transactions for Bitcoin product
    all_txs = [t for t in tx_repo.get_all() if t.product_id == btc_product.id]

    # Filter only BUY transactions for PRU calculation
    buy_txs = [t for t in all_txs if t.type == TransactionType.BUY]

    # Sum all EUR amounts from purchases
    total_invested = sum(float(t.amount_eur) for t in buy_txs if t.amount_eur)

    # Calculate PRU (Price of Unit) only if we own BTC
    pru = None

    if total_qty_btc > 0 and total_invested > 0:
        pru = total_invested / total_qty_btc

    # ═══════════════════════════════════════════════════════════════════════════
    # P&L CALCULATION (Profit & Loss)
    # ═══════════════════════════════════════════════════════════════════════════

    # Use live price if available, otherwise fallback to last snapshot
    ref_price = live_price or last_snapshot_price

    # Calculate percentage P&L
    pnl_pct = (
        ((ref_price - pru) / pru * 100)

        if (ref_price and pru and pru > 0)
        else None
        )

    # Calculate absolute P&L in EUR
    pnl_eur = (
        ((ref_price - pru) * total_qty_btc)

        if (ref_price and pru and total_qty_btc > 0)
        else None
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1: HERO PANEL
    # ═══════════════════════════════════════════════════════════════════════════

    # Format price for display (thousands separator with space)
    price_display = f"{live_price:,.0f} €".replace(",", " ") if live_price else "---"

    # Status badge: green "LIVE" if API connected, gray "OFFLINE" otherwise
    status_badge = (
        "<span style='background:#16a34a;color:white;border-radius:20px;"
        "padding:2px 10px;font-size:12px;font-weight:600;'>● LIVE</span>"

        if live_price else
        "<span style='background:#6b7280;color:white;border-radius:20px;"
        "padding:2px 10px;font-size:12px;font-weight:600;'>● OFFLINE</span>"
        )

    # Render hero panel with Bitcoin branding (orange #F7931A)
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

    # Refresh button to fetch live price from API
    col_refresh, col_spacer = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 Actualiser le cours", width="stretch"):
            with st.spinner("Connexion aux APIs..."):
                try:
                    # Fetch live price from CoinGecko
                    st.session_state.btc_price = float(
                        BTCPriceService().get_btc_price_eur()
                        )
                    st.session_state.api_error = None
                    st.rerun()
                except BTCPriceServiceError:
                    st.session_state.api_error = True

    # Show offline warning if API failed
    if st.session_state.get("api_error"):
        st.warning("📡 **Hors ligne** — Réseau inaccessible. Saisissez le prix manuellement ci-dessous.")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2: KEY INDICATORS
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown("### 📊 Indicateurs")

    i1, i2, i3, i4 = st.columns(4)

    with i1:
        st.metric("💼 Valeur actuelle", _fmt_eur(latest_total) if latest_total else "—")

    with i2:
        st.metric("📦 Quantité", _fmt_sats(total_qty_sats) if total_qty_sats > 0 else "—")

    with i3:
        st.metric("📌 PRU (Prix de revient)", _fmt_eur(pru) if pru else "—")

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

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3: HISTORICAL CHART
    # ═══════════════════════════════════════════════════════════════════════════

    if len(all_vals_sorted) >= 2:
        st.markdown("### 📉 Historique des prix (snapshots)")

        # Build dataframe for chart
        chart_data = pd.DataFrame([
            {
                "date": v.date.date(),
                "Prix snapshot (€)": float(v.unit_price_eur) if v.unit_price_eur else None,
                }
            for v in all_vals_sorted
            if v.unit_price_eur
            ])

        if not chart_data.empty:
            # Base chart encoding
            base = alt.Chart(chart_data).encode(
                x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %Y")),
                )

            # Main price line (Bitcoin orange)
            line_price = base.mark_line(color="#F7931A", strokeWidth=2.5).encode(
                y=alt.Y("Prix snapshot (€):Q", title="Prix BTC (€)"),
                tooltip=[
                    alt.Tooltip("date:T", title="Date", format="%d/%m/%Y"),
                    alt.Tooltip("Prix snapshot (€):Q", title="Prix (€)", format=",.0f"),
                    ]
                )

            # Data points on the line
            points = base.mark_circle(color="#F7931A", size=60).encode(
                y="Prix snapshot (€):Q"
                )

            chart = (line_price + points).properties(height=260)

            # Add PRU reference line if available
            if pru:
                pru_data = pd.DataFrame([
                    {"date": chart_data["date"].min(), "PRU": pru},
                    {"date": chart_data["date"].max(), "PRU": pru},
                    ])

                # Purple dashed line for PRU
                pru_line = alt.Chart(pru_data).mark_line(
                    color="#6366f1", strokeDash=[6, 4], strokeWidth=1.8
                    ).encode(
                        x="date:T",
                        y=alt.Y("PRU:Q"),
                        tooltip=[alt.Tooltip("PRU:Q", title="PRU (€)", format=",.0f")]
                        )
                chart = (chart + pru_line).properties(height=260)

            st.altair_chart(chart, width="stretch")
            st.caption("🟠 Courbe de prix · 🟣 Ligne pointillée = PRU")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 4: SNAPSHOT FORM
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("### 📸 Nouveau Snapchot")

    with st.form("btc_val_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)

        with c1:
            val_date = st.date_input("Date", value=date.today())

        with c2:
            # Default to live price or last known snapshot price
            default_price = live_price or (last_snapshot_price or 0.0)
            btc_unit_price = st.number_input(
                "Prix d'un BTC plein (EUR)",
                value=float(default_price),
                step=100.0,
                )

        with c3:
            # User enters quantity in Satoshis (more intuitive for small holdings)
            input_sats = st.number_input(
                "Quantité (en Satoshis)",
                value=int(total_qty_sats),
                step=100_000,
                format="%d",
                help="1 BTC = 100,000,000 Sats"
                )

        # Real-time value calculation
        if btc_unit_price > 0 and input_sats > 0:
            qty_btc_calc = input_sats / SATS_PER_BTC
            st.info(
                f"💶 Valeur calculée : **{_fmt_eur(btc_unit_price * qty_btc_calc)}** "
                )

        submit = st.form_submit_button("💾 Enregistrer le snapshot", type="primary", width="stretch")

        if submit:
            # Validation
            if input_sats <= 0 or btc_unit_price <= 0:
                st.error("La quantité (en sats) et le prix doivent être > 0.")
            else:
                try:
                    # Convert sats to BTC and calculate total value
                    qty_btc_final = input_sats / SATS_PER_BTC
                    total_val = qty_btc_final * btc_unit_price

                    # Persist valuation to database
                    val_repo.create(Valuation(
                        product_id=btc_product.id,
                        date=datetime.combine(val_date, datetime.min.time()),
                        total_value_eur=to_decimal(total_val),
                        unit_price_eur=to_decimal(btc_unit_price),
                        ))
                    st.success(f"✅ Snapshot enregistré — Valeur : {_fmt_eur(total_val)}")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 5: RECENT SNAPSHOTS TABLE
    # ═══════════════════════════════════════════════════════════════════════════

    if all_vals_sorted:
        st.markdown("### 🗓️ Derniers snapshots")

        # Display last 8 snapshots in reverse chronological order
        recent = list(reversed(all_vals_sorted))[:8]
        rows = []

        for v in recent:
            val_eur = float(v.total_value_eur)
            prix_unit = float(v.unit_price_eur) if v.unit_price_eur else 0.0

            # Calculate satoshis from total value and unit price
            sats_snapshot = int((val_eur / prix_unit) * SATS_PER_BTC) if prix_unit > 0 else 0

            rows.append({
                "Date": v.date.strftime("%d/%m/%Y"),
                "Prix BTC (€)": f"{prix_unit:,.0f}".replace(",", " ") if prix_unit > 0 else "—",
                "Satoshis": f"{sats_snapshot:,}".replace(",", " ") if sats_snapshot > 0 else "—",
                "Valeur totale (€)": f"{val_eur:,.2f}".replace(",", " "),
                })

        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
