"""Watched addresses, discovered holdings, and derived cost bases.

The page that makes the rest of the crypto tracking automatic: add an address,
sync it, and the balances it holds become positions the signal engine can
arbitrate. Two things are stated on screen rather than buried in a document —
that syncing discloses the address to an indexer, and that a cost basis
reconstructed from a chain is an estimate.
"""
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st
from sqlalchemy import select
from sqlmodel import Session

from finance_tracker.domain.enums import Chain, CostBasisConfidence
from finance_tracker.domain.models import (
    CostBasisEstimate,
    Product,
    Wallet,
    WalletHolding,
    )
from finance_tracker.i18n import t
from finance_tracker.services.crypto.coingecko_client import CoinGeckoClient
from finance_tracker.services.wallets.cost_basis import set_manual_unit_cost
from finance_tracker.services.wallets.registry import (
    COINGECKO,
    ETHERSCAN,
    KEY_REQUIRED,
    MEMPOOL,
    SOLANA_RPC,
    get_credential,
    set_credential,
    )
from finance_tracker.services.wallets.sync_service import (
    create_product_for_holding,
    link_holding_to_product,
    refresh_cost_bases,
    sync_all,
    )
from finance_tracker.web.ui.disclaimer import render_disclaimer

# How confidently a derived cost basis is presented. NONE gets no green tick
# anywhere: nothing was derived at all.
CONFIDENCE_ICON: dict[str, str] = {
    CostBasisConfidence.HIGH.value: "🟢",
    CostBasisConfidence.MEDIUM.value: "🟡",
    CostBasisConfidence.LOW.value: "🟠",
    CostBasisConfidence.NONE.value: "⚪",
    }


def _decimal_or_none(raw: str):
    """Parse a user-typed amount, accepting a comma as decimal separator."""
    text = (raw or "").strip().replace(",", ".").replace(" ", "")
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _render_credentials(session: Session) -> None:
    """Let the user supply their own keys and endpoints."""
    with st.expander(t("wallets.settings_title"), expanded=False):
        st.caption(t("wallets.settings_help"))
        st.warning(t("wallets.key_storage_warning"))

        etherscan = get_credential(session, ETHERSCAN)
        coingecko = get_credential(session, COINGECKO)
        mempool = get_credential(session, MEMPOOL)
        solana = get_credential(session, SOLANA_RPC)

        with st.form("wallet_credentials"):
            evm_key = st.text_input(
                t("wallets.etherscan_key"), value=etherscan.api_key, type="password",
                help=t("wallets.etherscan_help"),
                )
            gecko_key = st.text_input(
                t("wallets.coingecko_key"), value=coingecko.api_key, type="password",
                help=t("wallets.coingecko_help"),
                )
            btc_url = st.text_input(
                t("wallets.mempool_url"), value=mempool.base_url,
                placeholder="https://mempool.space/api",
                help=t("wallets.mempool_help"),
                )
            sol_url = st.text_input(
                t("wallets.solana_url"), value=solana.base_url,
                placeholder="https://api.mainnet-beta.solana.com",
                help=t("wallets.solana_help"),
                )

            if st.form_submit_button(t("wallets.save_settings"), width="stretch"):
                set_credential(session, ETHERSCAN, api_key=evm_key)
                set_credential(session, COINGECKO, api_key=gecko_key)
                set_credential(session, MEMPOOL, base_url=btc_url)
                set_credential(session, SOLANA_RPC, base_url=sol_url)
                st.success(t("wallets.settings_saved"))
                st.rerun()


def _render_add_wallet(session: Session) -> None:
    """Form to start watching an address."""
    with st.expander(f"➕ {t('wallets.add_title')}", expanded=False):
        st.info(t("wallets.privacy_notice"))

        with st.form("wallet_add", clear_on_submit=True):
            col1, col2 = st.columns([2, 3])
            with col1:
                label = st.text_input(t("wallets.field_label"))
                chain_value = st.selectbox(
                    t("wallets.field_chain"),
                    options=[c.value for c in Chain],
                    format_func=lambda c: (
                        f"{c} ⚠️" if Chain(c) in KEY_REQUIRED else c
                        ),
                    )
            with col2:
                address = st.text_input(t("wallets.field_address"))
                derive = st.checkbox(t("wallets.field_derive"), value=True,
                                     help=t("wallets.derive_help"))
                auto = st.checkbox(t("wallets.field_autosync"), value=True,
                                   help=t("wallets.autosync_help"))

            if st.form_submit_button(t("wallets.add_btn"), width="stretch"):
                if not address.strip():
                    st.error(t("wallets.address_required"))
                    return

                chain = Chain(chain_value)
                existing = session.exec(
                    select(Wallet).where(
                        Wallet.chain == chain,
                        Wallet.address == address.strip(),
                        )
                    ).scalars().first()
                if existing is not None:
                    st.error(t("wallets.duplicate"))
                    return

                session.add(Wallet(
                    label=label.strip() or address.strip()[:12],
                    chain=chain,
                    address=address.strip(),
                    derive_cost_basis=derive,
                    auto_sync=auto,
                    ))
                session.commit()
                st.success(t("wallets.added"))
                st.rerun()


def _render_wallets(session: Session) -> list[Wallet]:
    """List watched addresses with their sync state."""
    wallets = session.exec(select(Wallet).order_by(Wallet.label)).scalars().all()

    if not wallets:
        st.info(t("wallets.empty"))
        return []

    st.dataframe(
        pd.DataFrame([{
            t("wallets.col_label"): w.label,
            t("wallets.col_chain"): w.chain.value,
            t("wallets.col_address"): f"{w.address[:10]}…{w.address[-6:]}",
            t("wallets.col_sync"): "✅" if w.auto_sync else "⏸️",
            t("wallets.col_last"): (
                w.last_synced_at.strftime("%d/%m/%Y %H:%M") if w.last_synced_at else "—"
                ),
            t("wallets.col_error"): w.last_sync_error or "—",
            } for w in wallets]),
        hide_index=True,
        width="stretch",
        )

    with st.expander(t("wallets.manage_title"), expanded=False):
        for wallet in wallets:
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.markdown(f"**{wallet.label}** — `{wallet.address}`")
            toggled = col2.toggle(
                t("wallets.toggle_sync"), value=wallet.auto_sync, key=f"sync_{wallet.id}"
                )
            if toggled != wallet.auto_sync:
                wallet.auto_sync = toggled
                session.commit()
                st.rerun()
            if col3.button(t("wallets.delete"), key=f"del_{wallet.id}"):
                # Holdings and transfers reference the wallet; remove them
                # first so the database is never left with orphan rows.
                for holding in session.exec(
                    select(WalletHolding).where(WalletHolding.wallet_id == wallet.id)
                    ).scalars().all():
                    session.delete(holding)
                session.delete(wallet)
                session.commit()
                st.rerun()

    return wallets


def _render_holdings(session: Session) -> None:
    """List discovered balances and let the user map them to products."""
    holdings = session.exec(
        select(WalletHolding)
        .where(WalletHolding.ignored == False)  # noqa: E712  # pylint: disable=singleton-comparison
        .order_by(WalletHolding.symbol)
        ).scalars().all()

    if not holdings:
        st.caption(t("wallets.no_holdings"))
        return

    products = session.exec(select(Product).order_by(Product.name)).scalars().all()
    product_names = {p.id: p.name for p in products}

    st.dataframe(
        pd.DataFrame([{
            t("wallets.col_asset"): h.symbol or h.contract_address[:10],
            t("wallets.col_units"): f"{h.units:,.8f}".rstrip("0").rstrip("."),
            t("wallets.col_listing"): h.coingecko_id or "⚠️ —",
            t("wallets.col_product"): product_names.get(h.product_id, "—"),
            } for h in holdings]),
        hide_index=True,
        width="stretch",
        )

    unlisted = [h for h in holdings if not h.coingecko_id]
    if unlisted:
        st.caption(t("wallets.unlisted_note").format(
            assets=", ".join(h.symbol or h.contract_address[:10] for h in unlisted)))

    with st.expander(t("wallets.map_title"), expanded=False):
        st.caption(t("wallets.map_help"))
        for holding in holdings:
            name = holding.symbol or holding.contract_address[:10]
            col1, col2, col3 = st.columns([2, 2, 1])
            col1.markdown(f"**{name}** — {holding.units:,.6f}".rstrip("0").rstrip("."))

            options = [None] + [p.id for p in products]
            choice = col2.selectbox(
                t("wallets.map_to"),
                options=options,
                index=options.index(holding.product_id) if holding.product_id in options else 0,
                format_func=lambda pid: product_names.get(pid, t("wallets.map_none")),
                key=f"map_{holding.id}",
                label_visibility="collapsed",
                )
            if choice != holding.product_id:
                link_holding_to_product(session, holding, choice)
                st.rerun()

            if holding.product_id is None and holding.coingecko_id:
                if col3.button(t("wallets.create_product"), key=f"create_{holding.id}"):
                    try:
                        create_product_for_holding(session, holding)
                        st.success(t("wallets.product_created").format(name=name))
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

            if holding.ignored is False and holding.product_id is None:
                if col3.button(t("wallets.ignore"), key=f"ignore_{holding.id}"):
                    holding.ignored = True
                    session.commit()
                    st.rerun()


def _render_cost_bases(session: Session) -> None:
    """Show derived cost bases and let the user override any of them."""
    rows = session.exec(
        select(CostBasisEstimate, Product)
        .join(Product, Product.id == CostBasisEstimate.product_id)
        .order_by(Product.name)
        ).all()

    if not rows:
        st.caption(t("wallets.no_basis"))
        return

    st.warning(t("wallets.basis_estimate_warning"))

    st.dataframe(
        pd.DataFrame([{
            t("wallets.col_product"): product.name,
            t("wallets.col_unit_cost"): (
                f"{estimate.manual_unit_cost_eur:,.2f} € ✍️"
                if estimate.manual_unit_cost_eur is not None
                else ("—" if estimate.unit_cost_eur is None
                      else f"{estimate.unit_cost_eur:,.2f} €")
                ),
            t("wallets.col_total"): f"{estimate.cost_basis_eur:,.2f} €",
            t("wallets.col_confidence"): (
                f"{CONFIDENCE_ICON.get(estimate.confidence.value, '⚪')} "
                f"{t(f'confidence.{estimate.confidence.value.lower()}')}"
                ),
            t("wallets.col_uncovered"): (
                f"{estimate.uncovered_units:,.4f}".rstrip("0").rstrip(".")
                ),
            } for estimate, product in rows]),
        hide_index=True,
        width="stretch",
        )

    with st.expander(t("wallets.override_title"), expanded=False):
        st.caption(t("wallets.override_help"))
        for estimate, product in rows:
            col1, col2, col3 = st.columns([2, 2, 1])
            col1.markdown(f"**{product.name}**")
            typed = col2.text_input(
                t("wallets.override_field"),
                value=("" if estimate.manual_unit_cost_eur is None
                       else str(estimate.manual_unit_cost_eur)),
                key=f"basis_{estimate.id}",
                label_visibility="collapsed",
                placeholder=t("wallets.override_placeholder"),
                )
            if col3.button(t("wallets.override_save"), key=f"basis_save_{estimate.id}"):
                value = _decimal_or_none(typed)
                if typed.strip() and value is None:
                    st.error(t("wallets.override_invalid"))
                else:
                    set_manual_unit_cost(session, product.id, value)
                    st.success(t("wallets.override_saved").format(name=product.name))
                    st.rerun()

            if estimate.note:
                col1.caption(estimate.note)


def render(session: Session) -> None:
    """Render the wallets page."""
    st.title(t("wallets.title"))
    st.caption(t("wallets.caption"))

    render_disclaimer()

    _render_credentials(session)
    _render_add_wallet(session)

    st.subheader(t("wallets.section_wallets"))
    wallets = _render_wallets(session)

    if wallets:
        col1, col2 = st.columns(2)
        with col1:
            sync_clicked = st.button(
                t("wallets.sync_btn"), type="primary", width="stretch")
        with col2:
            basis_clicked = st.button(t("wallets.basis_btn"), width="stretch")

        credential = get_credential(session, COINGECKO)
        client = CoinGeckoClient(
            api_key=credential.api_key,
            base_url=credential.base_url or None,
            )

        if sync_clicked:
            status = st.empty()
            reports = sync_all(session, client, on_progress=status.info)
            status.empty()
            for report in reports:
                if report.ok:
                    st.success(t("wallets.sync_ok").format(
                        label=report.label,
                        balances=report.balances_seen,
                        transfers=report.transfers_added,
                        ))
                else:
                    st.error(t("wallets.sync_failed").format(
                        label=report.label, error=report.error))
                for note in report.notes:
                    st.caption(f"ℹ️ {note}")

        if basis_clicked:
            status = st.empty()
            results = refresh_cost_bases(session, client, on_progress=status.info)
            status.empty()
            if results:
                st.success(t("wallets.basis_done").format(n=len(results)))
            else:
                st.info(t("wallets.basis_nothing"))

    st.markdown("---")
    st.subheader(t("wallets.section_holdings"))
    _render_holdings(session)

    st.markdown("---")
    st.subheader(t("wallets.section_basis"))
    _render_cost_bases(session)
