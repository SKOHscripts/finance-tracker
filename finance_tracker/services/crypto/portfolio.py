"""Turning the tracker's database into positions the engine can arbitrate.

The engine needs three numbers per line: how many units are held, what they
are worth, and what they cost. None of the three is stored directly — each is
derived, and each has more than one possible source. This module settles the
order of preference and says, in the returned object, which source won, so the
UI can show where a figure came from instead of presenting every number with
the same false confidence.

Units, most trustworthy first:

1. **Wallet holdings.** What the chain says is at the address. Not an opinion.
2. **Transactions.** Bought minus sold, from the ledger the user keeps.
3. **Latest valuation.** No units at all, only a euro amount — enough to
   display and to arbitrate on, not enough to revalue at today's price.

Cost basis, most trustworthy first:

1. **A manual figure**, when the user has entered one. They know things no
   chain and no ledger records.
2. **Transactions.** Real purchases in euros, with fees.
3. **A derived on-chain estimate.** A reconstruction; see
   :mod:`finance_tracker.services.crypto.cost_basis`.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlmodel import Session

from finance_tracker.domain.enums import TransactionType
from finance_tracker.domain.models import (
    CostBasisEstimate,
    CryptoAsset,
    Product,
    Transaction,
    Valuation,
    WalletHolding,
    )

from .engine import Position

# Transaction types that add units to a line, and those that remove them. A
# DEPOSIT is cash arriving, not an asset bought, so it is deliberately absent.
_INFLOW_TYPES = (TransactionType.BUY,)
_OUTFLOW_TYPES = (TransactionType.SELL,)


@dataclass
class PositionSources:
    """Where each derived figure came from, for one position.

    Carried alongside the position so the interface can label an estimate as
    an estimate. A cost basis reconstructed from a chain and one typed from a
    bank statement are not the same claim.
    """

    units_from: str = "none"  # "wallet" | "transactions" | "none"
    cost_basis_from: str = "none"  # "manual" | "transactions" | "onchain" | "none"
    value_from: str = "none"  # "units" | "valuation" | "none"
    note: str = ""


@dataclass
class ResolvedPosition:
    """A position ready for the engine, plus its provenance and its product."""

    position: Position
    product: Product
    asset: CryptoAsset
    sources: PositionSources


def _units_from_wallets(session: Session, product_id: int) -> Optional[Decimal]:
    """Sum the on-chain balances mapped to *product_id*.

    Returns
    -------
    Decimal or None
        Total units across every non-ignored holding, or None when no wallet
        feeds this product. Zero is a real answer — an emptied address — and
        is returned as zero, not as None.
    """
    rows = session.exec(
        select(WalletHolding).where(
            WalletHolding.product_id == product_id,
            WalletHolding.ignored == False,  # noqa: E712  # pylint: disable=singleton-comparison
            )
        ).scalars().all()
    if not rows:
        return None
    return sum((Decimal(str(r.units or 0)) for r in rows), Decimal("0"))


def _units_from_transactions(session: Session, product_id: int) -> Optional[Decimal]:
    """Net units from the ledger: bought minus sold.

    Returns
    -------
    Decimal or None
        Net quantity, or None when no transaction on this product carries one.
    """
    rows = session.exec(
        select(Transaction).where(Transaction.product_id == product_id)
        ).scalars().all()

    total = Decimal("0")
    seen = False
    for tx in rows:
        if tx.quantity is None:
            continue
        if tx.type in _INFLOW_TYPES:
            total += Decimal(str(tx.quantity))
            seen = True
        elif tx.type in _OUTFLOW_TYPES:
            total -= Decimal(str(tx.quantity))
            seen = True
    return total if seen else None


def _cost_basis_from_transactions(session: Session, product_id: int) -> Optional[Decimal]:
    """Capital still invested in the line, from the ledger.

    Uses a moving average: a sale removes the average cost of the units sold,
    not their sale price, so a partial sale leaves the remaining units carrying
    what they actually cost. Fees paid on the line are added to the basis.

    Returns
    -------
    Decimal or None
        Remaining invested capital, or None when the ledger has no priced
        purchase to work from.
    """
    rows = session.exec(
        select(Transaction)
        .where(Transaction.product_id == product_id)
        .order_by(Transaction.date, Transaction.id)
        ).scalars().all()

    basis = Decimal("0")
    units = Decimal("0")
    seen_purchase = False

    for tx in rows:
        amount = Decimal(str(tx.amount_eur)) if tx.amount_eur is not None else None
        quantity = Decimal(str(tx.quantity)) if tx.quantity is not None else None

        if tx.type in _INFLOW_TYPES and amount is not None:
            basis += abs(amount)
            if quantity is not None:
                units += quantity
            seen_purchase = True

        elif tx.type in _OUTFLOW_TYPES and quantity is not None:
            if units > 0:
                # Remove what those units cost, not what they sold for.
                sold = min(quantity, units)
                basis -= basis * (sold / units)
                units -= sold
            elif amount is not None:
                basis -= abs(amount)

        elif tx.type == TransactionType.FEE and amount is not None:
            # A fee paid on the line is capital sunk into it.
            basis += abs(amount)

    if not seen_purchase:
        return None
    return max(basis, Decimal("0"))


def _latest_valuation(session: Session, product_id: int) -> Optional[Valuation]:
    """Most recent valuation for *product_id*, or None."""
    return session.exec(
        select(Valuation)
        .where(Valuation.product_id == product_id)
        .order_by(Valuation.date.desc(), Valuation.id.desc())
        .limit(1)
        ).scalars().first()


def _cost_basis_estimate(session: Session, product_id: int) -> Optional[CostBasisEstimate]:
    """Stored on-chain cost-basis reconstruction for *product_id*, or None."""
    return session.exec(
        select(CostBasisEstimate).where(CostBasisEstimate.product_id == product_id)
        ).scalars().first()


def resolve_position(session: Session, product: Product, asset: CryptoAsset) -> ResolvedPosition:
    """Build one engine position from the database.

    Parameters
    ----------
    session : Session
        Open database session.
    product : Product
        The tracked product.
    asset : CryptoAsset
        Its market identity.

    Returns
    -------
    ResolvedPosition
        The position, its provenance, and the rows it was built from.
    """
    sources = PositionSources()

    units = _units_from_wallets(session, product.id)
    if units is not None:
        sources.units_from = "wallet"
    else:
        units = _units_from_transactions(session, product.id)
        if units is not None:
            sources.units_from = "transactions"

    notional: Optional[Decimal] = None
    if units is not None:
        sources.value_from = "units"
    else:
        valuation = _latest_valuation(session, product.id)
        if valuation is not None:
            notional = Decimal(str(valuation.total_value_eur))
            sources.value_from = "valuation"
            sources.note = (
                "Aucune quantité connue sur cette ligne : sa valeur est celle de la "
                "dernière valorisation saisie et ne suit pas le cours du jour."
                )

    estimate = _cost_basis_estimate(session, product.id)
    cost_basis: Optional[Decimal] = None

    if estimate is not None and estimate.manual_unit_cost_eur is not None and units is not None:
        cost_basis = Decimal(str(estimate.manual_unit_cost_eur)) * units
        sources.cost_basis_from = "manual"
    else:
        cost_basis = _cost_basis_from_transactions(session, product.id)
        if cost_basis is not None:
            sources.cost_basis_from = "transactions"
        elif estimate is not None and estimate.cost_basis_eur:
            cost_basis = Decimal(str(estimate.cost_basis_eur))
            sources.cost_basis_from = "onchain"
            sources.note = (
                f"{sources.note} Prix de revient reconstitué depuis la chaîne "
                f"(confiance : {estimate.confidence.value.lower()}). "
                "C'est une estimation, corrigeable à la main."
                ).strip()

    position = Position(
        product_id=product.id,
        coingecko_id=asset.coingecko_id,
        symbol=(asset.symbol or product.name).upper(),
        units=float(units) if units is not None else None,
        notional_eur=float(notional) if notional is not None else None,
        gas_reserve_eur=float(asset.gas_reserve_eur or 0),
        cost_basis_eur=float(cost_basis) if cost_basis else None,
        arbitrated=bool(asset.arbitrated),
        )

    return ResolvedPosition(position=position, product=product, asset=asset, sources=sources)


def load_positions(session: Session) -> list[ResolvedPosition]:
    """Build every crypto position the database describes.

    A product joins the arbitrage by having a :class:`CryptoAsset` row: that
    is the whole opt-in. Products without one — a savings account, an SCPI —
    are untouched by any of this.

    Parameters
    ----------
    session : Session
        Open database session.

    Returns
    -------
    list[ResolvedPosition]
        One entry per mapped product, ordered by product name.
    """
    pairs = session.exec(
        select(Product, CryptoAsset)
        .join(CryptoAsset, CryptoAsset.product_id == Product.id)
        .order_by(Product.name)
        ).all()

    return [resolve_position(session, product, asset) for product, asset in pairs]


def held_coingecko_ids(session: Session) -> list[str]:
    """Every market identifier the portfolio currently maps to."""
    rows = session.exec(select(CryptoAsset.coingecko_id)).scalars().all()
    return [r for r in rows if r]
