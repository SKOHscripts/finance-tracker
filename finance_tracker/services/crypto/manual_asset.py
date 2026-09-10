"""Declaring a crypto position no address can reveal.

The wallet importer covers assets that live at a readable address. Some do not:
Monero cannot be read from an address without its view key, an exchange balance
sits behind an account rather than a chain, and a cold-stored asset may simply
not be worth exposing to an indexer. Those positions still have to reach the
engine, or the arbitrage is being run on a portfolio that is missing a piece.

So this module is the manual counterpart of
:mod:`finance_tracker.services.wallets.sync_service`: same destination — a
product carrying a market identity, with units and a cost basis the engine can
read — reached by declaration instead of by synchronisation.

Units and cost basis are recorded as a purchase in the ledger, not as a private
field. That is deliberate. The ledger is where every other product's figures
live, so a declared position stays visible in the transactions page, corrects
itself there, and flows into the dashboard like anything else. A position that
could only be edited through the form that created it would be a second,
invisible source of truth.
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlmodel import Session

from finance_tracker.domain.enums import (
    ProductType,
    QuantityUnit,
    TransactionType,
    )
from finance_tracker.domain.models import CryptoAsset, Product, Transaction

# Bitcoin gets its own product type so it lands in the tracker's Bitcoin space.
# Its unit stays CRYPTO_UNITS on this path, unlike elsewhere: the quantity typed
# into the form is what the engine prices, and the engine prices coins. Labelling
# the line BTC_SATS would invite a figure 100 000 000 times too large.
_BITCOIN_ID = "bitcoin"


class ManualAssetError(ValueError):
    """Raised when a declared asset would be unusable or ambiguous.

    A ValueError subclass so the view can catch one type and show the message,
    which is written for the user rather than for a log.
    """


def _clean(value: Optional[str]) -> str:
    return (value or "").strip()


def find_by_coingecko_id(session: Session, coingecko_id: str) -> Optional[CryptoAsset]:
    """Return the asset already mapped to *coingecko_id*, if any."""
    wanted = _clean(coingecko_id).lower()
    if not wanted:
        return None
    return session.exec(
        select(CryptoAsset).where(CryptoAsset.coingecko_id == wanted)
        ).scalars().first()


def _resolve_cost(
    units: Decimal,
    unit_cost_eur: Optional[Decimal],
    total_cost_eur: Optional[Decimal],
    ) -> Optional[Decimal]:
    """Turn whichever cost figure was given into a total.

    Both forms are accepted because both are how people actually hold the
    number: some remember what they paid per unit, others what left their bank
    account.

    Returns
    -------
    Decimal or None
        Total invested, or None when no cost was declared. None is a real
        answer — see :func:`add_manual_asset`.

    Raises
    ------
    ManualAssetError
        When both forms are given, or a figure is negative.
    """
    if unit_cost_eur is not None and total_cost_eur is not None:
        raise ManualAssetError(
            "Renseigne le prix de revient unitaire ou le montant total investi, "
            "pas les deux : les deux chiffres se contrediraient."
            )

    if unit_cost_eur is not None:
        if unit_cost_eur < 0:
            raise ManualAssetError("Le prix de revient ne peut pas être négatif.")
        return (unit_cost_eur * units).quantize(Decimal("0.01"))

    if total_cost_eur is not None:
        if total_cost_eur < 0:
            raise ManualAssetError("Le montant investi ne peut pas être négatif.")
        return total_cost_eur.quantize(Decimal("0.01"))

    return None


def attach_listing(
    session: Session,
    product: Product,
    *,
    coingecko_id: str,
    symbol: str = "",
    gas_reserve_eur: Decimal = Decimal("0"),
    arbitrated: bool = True,
    ) -> CryptoAsset:
    """Give an existing product the market identity the engine needs.

    The other half of declaring an asset: a Bitcoin product created before the
    crypto features existed holds real units and a real cost basis, and needs
    nothing but this row to join the arbitrage.

    Parameters
    ----------
    session : Session
        Open database session. Committed here.
    product : Product
        The product to price.
    coingecko_id : str
        CoinGecko identifier, e.g. ``"monero"``.
    symbol : str, optional
        Ticker, upper-cased for display.
    gas_reserve_eur : Decimal, optional
        Share never proposed for a swap, for an asset that also pays fees.
    arbitrated : bool, optional
        Whether the engine may propose a move on the line.

    Returns
    -------
    CryptoAsset
        The created or updated market identity.

    Raises
    ------
    ManualAssetError
        When the identifier is empty, or already belongs to another product —
        two products on one listing would count the same holding twice.
    """
    listing = _clean(coingecko_id).lower()
    if not listing:
        raise ManualAssetError("Il faut une cotation : sans elle, rien ne peut être prixé.")
    if gas_reserve_eur < 0:
        raise ManualAssetError("La réserve de frais ne peut pas être négative.")

    clash = find_by_coingecko_id(session, listing)
    if clash is not None and clash.product_id != product.id:
        other = session.get(Product, clash.product_id)
        raise ManualAssetError(
            f"« {listing} » est déjà associé au produit "
            f"« {other.name if other else clash.product_id} ». "
            "Deux produits sur la même cotation compteraient deux fois le même avoir."
            )

    existing = session.exec(
        select(CryptoAsset).where(CryptoAsset.product_id == product.id)
        ).scalars().first()

    if existing is None:
        existing = CryptoAsset(product_id=product.id)
        session.add(existing)

    existing.coingecko_id = listing
    existing.symbol = _clean(symbol).upper()
    existing.gas_reserve_eur = gas_reserve_eur
    existing.arbitrated = arbitrated
    session.commit()
    session.refresh(existing)
    return existing


def add_manual_asset(
    session: Session,
    *,
    name: str,
    coingecko_id: str,
    symbol: str = "",
    units: Optional[Decimal] = None,
    unit_cost_eur: Optional[Decimal] = None,
    total_cost_eur: Optional[Decimal] = None,
    acquired_on: Optional[datetime] = None,
    gas_reserve_eur: Decimal = Decimal("0"),
    arbitrated: bool = True,
    note: str = "",
    ) -> Product:
    """Declare a held asset the wallet importer cannot see.

    Creates the product, gives it its market identity, and records the holding
    as a purchase so units and cost basis come from the same place they do for
    every other product.

    Parameters
    ----------
    session : Session
        Open database session. Committed here.
    name : str
        Product name, unique across the portfolio.
    coingecko_id : str
        CoinGecko identifier the price will be fetched with.
    symbol : str, optional
        Ticker, upper-cased for display.
    units : Decimal, optional
        Quantity held. Omit to create the line and enter purchases later.
    unit_cost_eur : Decimal, optional
        What one unit cost. Mutually exclusive with *total_cost_eur*.
    total_cost_eur : Decimal, optional
        What the whole holding cost. Mutually exclusive with *unit_cost_eur*.
    acquired_on : datetime, optional
        Date carried by the recorded purchase. Defaults to now.
    gas_reserve_eur : Decimal, optional
        Share never proposed for a swap.
    arbitrated : bool, optional
        Whether the engine may propose a move on the line.
    note : str, optional
        Note carried by the recorded purchase.

    Returns
    -------
    Product
        The created product.

    Raises
    ------
    ManualAssetError
        When the name is missing or taken, the listing is missing or already
        used, the quantity is not positive, or the cost is contradictory.

    Notes
    -----
    Declaring units without a cost is allowed and is not an oversight: an
    airdropped or mined holding has no purchase price, and the engine treats an
    unknown cost basis as unknown — it disables the trailing stop on that line
    rather than reading a missing figure as a total gain.
    """
    label = _clean(name)
    if not label:
        raise ManualAssetError("Il faut un nom de produit.")

    listing = _clean(coingecko_id).lower()
    if not listing:
        raise ManualAssetError("Il faut une cotation : sans elle, rien ne peut être prixé.")

    if session.exec(
        select(Product).where(Product.name == label)
        ).scalars().first() is not None:
        raise ManualAssetError(
            f"Un produit s'appelle déjà « {label} ». "
            "Choisis un autre nom, ou associe la cotation au produit existant."
            )

    clash = find_by_coingecko_id(session, listing)
    if clash is not None:
        other = session.get(Product, clash.product_id)
        raise ManualAssetError(
            f"« {listing} » est déjà associé au produit "
            f"« {other.name if other else clash.product_id} ». "
            "Deux produits sur la même cotation compteraient deux fois le même avoir."
            )

    if gas_reserve_eur < 0:
        raise ManualAssetError("La réserve de frais ne peut pas être négative.")

    if units is not None and units <= 0:
        raise ManualAssetError(
            "La quantité doit être supérieure à zéro. Laisse le champ vide pour "
            "créer la ligne sans position."
            )
    if units is None and (unit_cost_eur is not None or total_cost_eur is not None):
        raise ManualAssetError(
            "Un prix de revient sans quantité ne décrit aucune position : "
            "renseigne la quantité détenue."
            )

    cost = _resolve_cost(units, unit_cost_eur, total_cost_eur) if units is not None else None

    is_bitcoin = listing == _BITCOIN_ID
    product = Product(
        name=label,
        type=ProductType.BITCOIN if is_bitcoin else ProductType.CRYPTO,
        quantity_unit=QuantityUnit.CRYPTO_UNITS,
        description=_clean(note) or "Saisi à la main : aucune adresse ne peut le révéler.",
        )
    session.add(product)
    session.commit()
    session.refresh(product)

    session.add(CryptoAsset(
        product_id=product.id,
        coingecko_id=listing,
        symbol=_clean(symbol).upper(),
        gas_reserve_eur=gas_reserve_eur,
        arbitrated=arbitrated,
        ))

    if units is not None:
        session.add(Transaction(
            product_id=product.id,
            date=acquired_on or datetime.now(timezone.utc),
            type=TransactionType.BUY,
            quantity=units,
            amount_eur=cost,
            note=_clean(note) or "Position déclarée à la main",
            ))

    session.commit()
    session.refresh(product)
    return product
