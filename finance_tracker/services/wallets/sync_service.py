"""Syncing watched addresses into the tracker.

Reads each wallet the user has turned on, records what it holds and how it got
there, matches every token to a listing so it can be priced, and — where the
chain allows — reconstructs a cost basis.

Two rules govern what a sync is allowed to overwrite. Balances and transfers
belong to the chain, so they are refreshed wholesale. Everything the user
decided — which product a holding feeds, which tokens are dust, a corrected
cost basis — survives untouched. A sync that quietly undid a mapping would
make the feature worse than typing the numbers.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable, Optional

from sqlalchemy import select
from sqlmodel import Session

from finance_tracker.domain.enums import (
    Chain,
    ProductType,
    QuantityUnit,
    )
from finance_tracker.domain.models import (
    CryptoAsset,
    Product,
    Wallet,
    WalletHolding,
    WalletTransfer,
    )

from ..crypto.coingecko_client import CoinGeckoClient
from .base import RawTransfer, TokenBalance, WalletProviderError, WalletSnapshot
from .cost_basis import classify, own_addresses, recompute_for_product
from .registry import missing_requirements, provider_for

# Native coins, mapped straight to their listing: there is no contract to look
# up, and the chain does not name its own currency in a machine-readable way.
_NATIVE_IDS: dict[Chain, str] = {
    Chain.BITCOIN: "bitcoin",
    Chain.ETHEREUM: "ethereum",
    Chain.BASE: "ethereum",
    Chain.ARBITRUM: "ethereum",
    Chain.OPTIMISM: "ethereum",
    Chain.POLYGON: "matic-network",
    Chain.BSC: "binancecoin",
    Chain.SOLANA: "solana",
    }


@dataclass
class SyncReport:
    """What one wallet's sync produced.

    Parameters
    ----------
    wallet_id : int
        The wallet synced.
    label : str
        Its user-facing name.
    ok : bool
        Whether the sync completed.
    error : str
        Failure message, empty on success.
    balances_seen : int
        Holdings recorded.
    transfers_added : int
        New movements recorded; a resync adds only what it had not seen.
    unresolved : list[str]
        Symbols that could not be matched to a listing, and so cannot be
        priced or arbitrated.
    notes : list[str]
        Caveats from the connector, surfaced as-is.
    """

    wallet_id: int
    label: str = ""
    ok: bool = True
    error: str = ""
    balances_seen: int = 0
    transfers_added: int = 0
    unresolved: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


ProgressCallback = Callable[[str], None]


def _noop(_: str) -> None:
    """Default progress sink."""


def _resolve_listing(
    chain: Chain, balance: TokenBalance, client: Optional[CoinGeckoClient]
    ) -> tuple[str, str]:
    """Match a holding to a market listing.

    Returns
    -------
    tuple
        The CoinGecko identifier and the resolved symbol. Both may be empty:
        an airdropped token nobody trades has no listing, which is a normal
        outcome and not an error.
    """
    if balance.is_native or not balance.contract_address:
        native = _NATIVE_IDS.get(chain, "")
        return native, balance.symbol or native.upper()

    if client is None:
        return "", balance.symbol

    listing = client.resolve_contract(chain.value, balance.contract_address)
    if not listing:
        return "", balance.symbol
    return listing["id"], balance.symbol or listing["symbol"]


def _upsert_holding(
    session: Session, wallet: Wallet, balance: TokenBalance,
    coingecko_id: str, symbol: str, seen_at: datetime,
    ) -> WalletHolding:
    """Record a balance, preserving the user's mapping and dust flag."""
    contract = (balance.contract_address or "").lower()
    row = session.exec(
        select(WalletHolding).where(
            WalletHolding.wallet_id == wallet.id,
            WalletHolding.contract_address == contract,
            )
        ).scalars().first()

    if row is None:
        row = WalletHolding(wallet_id=wallet.id, contract_address=contract)
        session.add(row)

    row.symbol = (symbol or balance.symbol or "").upper()
    row.name = balance.name or row.symbol
    row.decimals = balance.decimals
    row.units = balance.units
    row.last_seen_at = seen_at
    # Only fill the listing when it was resolved: a failed lookup must not
    # erase a mapping the user fixed by hand.
    if coingecko_id:
        row.coingecko_id = coingecko_id

    return row


def _store_transfers(
    session: Session, wallet: Wallet, transfers: list[RawTransfer], mine: set[str]
    ) -> int:
    """Record movements not already stored. Returns how many were added."""
    if not transfers:
        return 0

    existing = {
        (t.tx_hash, t.log_index)
        for t in session.exec(
            select(WalletTransfer).where(WalletTransfer.wallet_id == wallet.id)
            ).scalars().all()
        }

    added = 0
    for transfer in transfers:
        key = (transfer.tx_hash, transfer.log_index)
        if key in existing:
            continue
        row = WalletTransfer(
            wallet_id=wallet.id,
            tx_hash=transfer.tx_hash,
            log_index=transfer.log_index,
            timestamp=transfer.timestamp,
            direction=transfer.direction,
            contract_address=(transfer.contract_address or "").lower(),
            symbol=transfer.symbol,
            units=transfer.units,
            counterparty=transfer.counterparty,
            )
        row.kind = classify(row, mine)
        session.add(row)
        existing.add(key)
        added += 1

    return added


def sync_wallet(
    session: Session,
    wallet: Wallet,
    client: Optional[CoinGeckoClient] = None,
    with_history: bool = True,
    on_progress: ProgressCallback = _noop,
    ) -> SyncReport:
    """Read one wallet and record what it holds.

    Parameters
    ----------
    session : Session
        Open database session. Committed here.
    wallet : Wallet
        The wallet to sync. Its ``auto_sync`` flag is honoured: a wallet the
        user turned off is never sent to an indexer.
    client : CoinGeckoClient, optional
        Used to match tokens to listings.
    with_history : bool, optional
        Whether to fetch transfers as well as balances.
    on_progress : ProgressCallback, optional
        Called with a short status line as the sync advances.

    Returns
    -------
    SyncReport
        What happened, including any failure. Failures are reported, not
        raised: one unreachable indexer must not abort the other wallets.
    """
    report = SyncReport(wallet_id=wallet.id, label=wallet.label or wallet.address)

    if not wallet.auto_sync:
        report.ok = False
        report.error = "Synchronisation désactivée sur ce portefeuille."
        return report

    blocker = missing_requirements(session, wallet.chain)
    if blocker:
        report.ok = False
        report.error = blocker
        wallet.last_sync_error = blocker
        session.commit()
        return report

    try:
        on_progress(f"Lecture de {report.label}")
        provider = provider_for(wallet.chain, session)
        snapshot: WalletSnapshot = provider.fetch(
            wallet.address, with_history=with_history and wallet.derive_cost_basis
            )
    except WalletProviderError as exc:
        report.ok = False
        report.error = str(exc)
        wallet.last_sync_error = str(exc)
        session.commit()
        return report

    seen_at = datetime.now(timezone.utc)
    mine = own_addresses(session)

    for balance in snapshot.balances:
        coingecko_id, symbol = _resolve_listing(wallet.chain, balance, client)
        _upsert_holding(session, wallet, balance, coingecko_id, symbol, seen_at)
        if not coingecko_id:
            report.unresolved.append(symbol or balance.contract_address)
        report.balances_seen += 1

    report.transfers_added = _store_transfers(session, wallet, snapshot.transfers, mine)

    wallet.last_synced_at = seen_at
    wallet.last_sync_error = "" if snapshot.history_complete else (
        "Historique incomplet : le prix de revient dérivé est partiel."
        )
    session.commit()

    report.notes = list(snapshot.notes)
    return report


def sync_all(
    session: Session,
    client: Optional[CoinGeckoClient] = None,
    on_progress: ProgressCallback = _noop,
    ) -> list[SyncReport]:
    """Sync every wallet the user has left switched on.

    Parameters
    ----------
    session : Session
        Open database session.
    client : CoinGeckoClient, optional
        Used to match tokens to listings.
    on_progress : ProgressCallback, optional
        Called with a short status line per wallet.

    Returns
    -------
    list[SyncReport]
        One report per wallet, successes and failures alike.
    """
    wallets = session.exec(
        select(Wallet).where(Wallet.auto_sync == True)  # noqa: E712  # pylint: disable=singleton-comparison
        ).scalars().all()
    return [sync_wallet(session, w, client, on_progress=on_progress) for w in wallets]


def link_holding_to_product(
    session: Session, holding: WalletHolding, product_id: Optional[int]
    ) -> WalletHolding:
    """Point a holding at a tracker product, or unlink it.

    Parameters
    ----------
    session : Session
        Open database session. Committed here.
    holding : WalletHolding
        The balance to map.
    product_id : int or None
        Product to feed, or None to unlink.

    Returns
    -------
    WalletHolding
        The updated row.
    """
    holding.product_id = product_id
    session.commit()
    session.refresh(holding)
    return holding


def create_product_for_holding(
    session: Session, holding: WalletHolding, name: Optional[str] = None
    ) -> Product:
    """Create a tracked product from a discovered holding, and map it.

    This is the one-click path from "an address holds this" to "the engine
    arbitrates this": it creates the product, gives it the market identity the
    signal needs, and links the balance that feeds it.

    Parameters
    ----------
    session : Session
        Open database session. Committed here.
    holding : WalletHolding
        The balance to promote.
    name : str, optional
        Product name. Defaults to the holding's symbol.

    Returns
    -------
    Product
        The created or reused product.

    Raises
    ------
    ValueError
        When the holding has no listing, so nothing could price it.
    """
    if not holding.coingecko_id:
        raise ValueError(
            f"« {holding.symbol or holding.contract_address} » n'est associé à aucune "
            "cotation : impossible de le suivre tant qu'il n'a pas d'identifiant de marché."
            )

    label = (name or holding.symbol or holding.coingecko_id).strip()
    product = session.exec(select(Product).where(Product.name == label)).scalars().first()

    if product is None:
        product = Product(
            name=label,
            type=ProductType.BITCOIN if holding.coingecko_id == "bitcoin" else ProductType.CRYPTO,
            quantity_unit=(
                QuantityUnit.BTC_SATS if holding.coingecko_id == "bitcoin"
                else QuantityUnit.CRYPTO_UNITS
                ),
            description=f"Créé depuis un portefeuille suivi ({holding.symbol}).",
            risk_level="Très élevé",
            )
        session.add(product)
        session.commit()
        session.refresh(product)

    asset = session.exec(
        select(CryptoAsset).where(CryptoAsset.product_id == product.id)
        ).scalars().first()
    if asset is None:
        session.add(CryptoAsset(
            product_id=product.id,
            coingecko_id=holding.coingecko_id,
            symbol=(holding.symbol or "").upper(),
            ))

    holding.product_id = product.id
    session.commit()
    session.refresh(product)
    return product


def refresh_cost_bases(
    session: Session,
    client: Optional[CoinGeckoClient] = None,
    quote_currency: str = "eur",
    on_progress: ProgressCallback = _noop,
    ) -> dict[int, object]:
    """Recompute the derived cost basis of every wallet-fed product.

    Parameters
    ----------
    session : Session
        Open database session.
    client : CoinGeckoClient, optional
        Price source for historical rates.
    quote_currency : str, optional
        Currency to price in.
    on_progress : ProgressCallback, optional
        Called with a short status line per product.

    Returns
    -------
    dict[int, BasisResult]
        Results keyed by product id, skipping products no wallet feeds.
    """
    pairs = session.exec(
        select(Product, CryptoAsset)
        .join(CryptoAsset, CryptoAsset.product_id == Product.id)
        ).all()

    results: dict[int, object] = {}
    for product, asset in pairs:
        on_progress(f"Prix de revient de {product.name}")
        outcome = recompute_for_product(
            session, product.id, asset.coingecko_id, client, quote_currency
            )
        if outcome is not None:
            results[product.id] = outcome
    return results


def unresolved_holdings(session: Session) -> list[WalletHolding]:
    """Holdings with no listing: visible, but impossible to price."""
    return session.exec(
        select(WalletHolding).where(
            WalletHolding.coingecko_id == "",
            WalletHolding.ignored == False,  # noqa: E712  # pylint: disable=singleton-comparison
            )
        ).scalars().all()


def wallet_totals(session: Session) -> dict[int, Decimal]:
    """Units held per product, summed across every non-ignored holding."""
    rows = session.exec(
        select(WalletHolding).where(
            WalletHolding.ignored == False,  # noqa: E712  # pylint: disable=singleton-comparison
            WalletHolding.product_id.is_not(None),
            )
        ).scalars().all()

    totals: dict[int, Decimal] = {}
    for row in rows:
        totals[row.product_id] = totals.get(row.product_id, Decimal("0")) + Decimal(
            str(row.units or 0))
    return totals
