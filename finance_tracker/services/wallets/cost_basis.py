"""Reconstructing a cost basis from on-chain movements.

What this can and cannot do
---------------------------
A blockchain records that units moved. It does not record what they cost, why
they moved, or whether both sides of a movement belong to the same person. So
this is a reconstruction, and it is only as good as the classification it
starts from.

The method is a moving average over classified movements:

* an **acquisition** — units arriving from an address the user does not watch —
  is priced at the market rate on the day of the block, and raises the basis;
* a **disposal** — units leaving to an address the user does not watch — removes
  the *average cost* of the units sold, not their sale price, so what remains
  keeps carrying what it actually cost;
* an **internal** movement, between two watched addresses, changes nothing.

Where it is wrong, and why it says so
-------------------------------------
Three failure modes are real and none of them can be fixed from chain data:

1. **A swap looks like an acquisition.** Trading token A for token B shows up
   as B arriving. Its true basis is what A cost, which lives on a different
   line. Priced at B's market rate, the number is right in euros and wrong as
   accounting.
2. **A transfer from an unwatched wallet of your own reads as a purchase.**
   Add that wallet and it reclassifies; until then it inflates the basis.
3. **Prices run out.** The free market-data plan serves a year. Anything older
   is recorded unpriced and counted in ``uncovered_units``.

Which is why every result carries its uncovered share and a confidence band,
why the interface labels it an estimate, and why a manual figure always wins.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable, Optional

from sqlalchemy import select
from sqlmodel import Session

from finance_tracker.domain.enums import (
    CostBasisConfidence,
    TransferDirection,
    TransferKind,
    )
from finance_tracker.domain.models import (
    CostBasisEstimate,
    Wallet,
    WalletHolding,
    WalletTransfer,
    )

from ..crypto.coingecko_client import CoinGeckoClient

#: Identifier of the method, stored so a figure can be traced to how it was made.
METHOD = "MOVING_AVERAGE_ONCHAIN_V1"

# Share of units that must be traced to a priced acquisition for each band.
_HIGH_COVERAGE = Decimal("0.95")
_MEDIUM_COVERAGE = Decimal("0.60")


@dataclass
class BasisResult:
    """A reconstructed cost basis, with what it fails to explain.

    Parameters
    ----------
    units : Decimal
        Units the walk ended on.
    cost_basis : Decimal
        Capital attributed to those units.
    unit_cost : Optional[Decimal]
        Average cost per unit, None when nothing could be priced.
    uncovered_units : Decimal
        Units whose origin could not be priced.
    confidence : CostBasisConfidence
        Coverage band.
    notes : list[str]
        Caveats to show next to the figure.
    priced_acquisitions : int
        How many incoming movements were priced.
    unpriced_acquisitions : int
        How many could not be.
    """

    units: Decimal = Decimal("0")
    cost_basis: Decimal = Decimal("0")
    unit_cost: Optional[Decimal] = None
    uncovered_units: Decimal = Decimal("0")
    confidence: CostBasisConfidence = CostBasisConfidence.NONE
    notes: list[str] = field(default_factory=list)
    priced_acquisitions: int = 0
    unpriced_acquisitions: int = 0


def classify(
    transfer: WalletTransfer | object, watched_addresses: set[str]
    ) -> TransferKind:
    """Decide what a movement means for cost basis.

    Parameters
    ----------
    transfer : WalletTransfer
        The movement, with a direction and a counterparty.
    watched_addresses : set[str]
        Every address the user watches, lower-cased. A movement between two of
        them is the same person moving their own coins.

    Returns
    -------
    TransferKind
        ``INTERNAL`` when both ends are watched, otherwise ``ACQUISITION`` for
        an inbound movement and ``DISPOSAL`` for an outbound one.
    """
    counterparty = (getattr(transfer, "counterparty", "") or "").lower()
    if counterparty and counterparty in watched_addresses:
        return TransferKind.INTERNAL
    if transfer.direction is TransferDirection.IN:
        return TransferKind.ACQUISITION
    return TransferKind.DISPOSAL


def own_addresses(session: Session) -> set[str]:
    """Every watched address, lower-cased, for internal-transfer detection."""
    rows = session.exec(select(Wallet.address)).scalars().all()
    return {a.lower() for a in rows if a}


def derive_basis(
    transfers: Iterable[WalletTransfer],
    coingecko_id: str,
    client: Optional[CoinGeckoClient] = None,
    quote_currency: str = "eur",
    history_complete: bool = True,
    ) -> BasisResult:
    """Walk classified movements and return the resulting cost basis.

    Movements must already be classified: this function trusts ``kind`` and
    prices only what it is told to price.

    Parameters
    ----------
    transfers : Iterable[WalletTransfer]
        Movements for one asset, in any order; sorted here.
    coingecko_id : str
        Market identifier used to price acquisitions. Empty means the asset is
        unlisted and nothing can be priced.
    client : CoinGeckoClient, optional
        Price source. Without one, no acquisition is priced and every unit is
        reported uncovered.
    quote_currency : str, optional
        Currency to price in.
    history_complete : bool, optional
        False when the connector truncated the history, which caps confidence.

    Returns
    -------
    BasisResult
        The reconstruction and its caveats.
    """
    result = BasisResult()
    ordered = sorted(transfers, key=lambda t: t.timestamp)

    units = Decimal("0")
    basis = Decimal("0")
    uncovered = Decimal("0")

    for transfer in ordered:
        amount = Decimal(str(transfer.units or 0))
        if amount <= 0:
            continue

        if transfer.kind is TransferKind.INTERNAL:
            continue

        if transfer.kind is TransferKind.ACQUISITION:
            price = _price_for(transfer, coingecko_id, client, quote_currency)
            units += amount
            if price is None:
                uncovered += amount
                result.unpriced_acquisitions += 1
            else:
                basis += amount * price
                result.priced_acquisitions += 1

        elif transfer.kind is TransferKind.DISPOSAL:
            if units <= 0:
                # Units left an address that, as far as the fetched history
                # shows, never received them. The history starts too late.
                continue
            sold = min(amount, units)
            share = sold / units
            basis -= basis * share
            uncovered -= uncovered * share
            units -= sold

    result.units = units
    result.cost_basis = basis.quantize(Decimal("0.01"))
    result.uncovered_units = max(uncovered, Decimal("0"))

    covered = units - result.uncovered_units
    if units > 0 and covered > 0 and basis > 0:
        # Spread the known capital over the units it actually explains, then
        # apply that rate to the whole line. Better than dividing by every
        # unit, which would understate the basis by the unpriced share.
        result.unit_cost = (basis / covered).quantize(Decimal("0.00000001"))
        result.cost_basis = (result.unit_cost * units).quantize(Decimal("0.01"))

    result.confidence = _confidence(units, result.uncovered_units, history_complete, basis)
    result.notes = _notes(result, history_complete, coingecko_id)
    return result


def _price_for(
    transfer: WalletTransfer,
    coingecko_id: str,
    client: Optional[CoinGeckoClient],
    quote_currency: str,
    ) -> Optional[Decimal]:
    """Price one acquisition, preferring a price already stored on the row."""
    if transfer.unit_price_eur is not None:
        return Decimal(str(transfer.unit_price_eur))
    if client is None or not coingecko_id:
        return None
    day = transfer.timestamp
    if isinstance(day, datetime):
        day = day.astimezone(timezone.utc).date()
    price = client.price_on(coingecko_id, day, quote_currency)
    return None if price is None else Decimal(str(price))


def _confidence(
    units: Decimal, uncovered: Decimal, history_complete: bool, basis: Decimal
    ) -> CostBasisConfidence:
    """Band the estimate by how much of the position it explains."""
    if units <= 0 or basis <= 0:
        return CostBasisConfidence.NONE
    covered_ratio = (units - uncovered) / units
    if not history_complete:
        # A truncated history cannot be high confidence whatever the ratio
        # says: the ratio itself was computed on a partial record.
        return (
            CostBasisConfidence.MEDIUM if covered_ratio >= _MEDIUM_COVERAGE
            else CostBasisConfidence.LOW
            )
    if covered_ratio >= _HIGH_COVERAGE:
        return CostBasisConfidence.HIGH
    if covered_ratio >= _MEDIUM_COVERAGE:
        return CostBasisConfidence.MEDIUM
    return CostBasisConfidence.LOW


def _notes(result: BasisResult, history_complete: bool, coingecko_id: str) -> list[str]:
    """Assemble the caveats worth showing next to the figure."""
    notes = [
        "Prix de revient reconstitué depuis la chaîne : c'est une estimation, "
        "pas un prix d'achat enregistré. Corrige-la à la main si tu connais le tien."
        ]
    if not coingecko_id:
        notes.append(
            "Cet actif n'est associé à aucune cotation : aucune entrée n'a pu être "
            "valorisée."
            )
    if not history_complete:
        notes.append(
            "L'historique récupéré est incomplet : le calcul démarre après le premier "
            "mouvement réel de l'adresse."
            )
    if result.unpriced_acquisitions:
        notes.append(
            f"{result.unpriced_acquisitions} entrée(s) sans cours disponible — "
            "souvent des mouvements de plus d'un an, hors de portée du plan gratuit."
            )
    if result.priced_acquisitions:
        notes.append(
            "Un token reçu d'un swap est valorisé au cours du jour, alors que son "
            "vrai prix de revient est celui de l'actif cédé."
            )
    return notes


def store_estimate(
    session: Session, product_id: int, result: BasisResult, keep_manual: bool = True
    ) -> CostBasisEstimate:
    """Persist a reconstruction, leaving any manual figure untouched.

    Parameters
    ----------
    session : Session
        Open database session. Committed here.
    product_id : int
        Product the estimate applies to.
    result : BasisResult
        What the walk produced.
    keep_manual : bool, optional
        Whether to preserve an existing manual unit cost. True by default:
        a resync must never silently discard a correction the user made.

    Returns
    -------
    CostBasisEstimate
        The stored row.
    """
    row = session.exec(
        select(CostBasisEstimate).where(CostBasisEstimate.product_id == product_id)
        ).scalars().first()

    if row is None:
        row = CostBasisEstimate(product_id=product_id)
        session.add(row)

    manual = row.manual_unit_cost_eur if keep_manual else None

    row.units = result.units
    row.cost_basis_eur = result.cost_basis
    row.unit_cost_eur = result.unit_cost
    row.uncovered_units = result.uncovered_units
    row.confidence = result.confidence
    row.method = METHOD
    row.computed_at = datetime.now(timezone.utc)
    row.note = " ".join(result.notes)
    row.manual_unit_cost_eur = manual

    session.commit()
    session.refresh(row)
    return row


def set_manual_unit_cost(
    session: Session, product_id: int, unit_cost: Optional[Decimal]
    ) -> CostBasisEstimate:
    """Set or clear the user's own unit cost for a product.

    Parameters
    ----------
    session : Session
        Open database session. Committed here.
    product_id : int
        Product to correct.
    unit_cost : Decimal or None
        The figure, or None to fall back to the derived estimate.

    Returns
    -------
    CostBasisEstimate
        The stored row.
    """
    row = session.exec(
        select(CostBasisEstimate).where(CostBasisEstimate.product_id == product_id)
        ).scalars().first()

    if row is None:
        row = CostBasisEstimate(product_id=product_id, method="MANUAL")
        session.add(row)

    row.manual_unit_cost_eur = unit_cost
    row.computed_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(row)
    return row


def recompute_for_product(
    session: Session,
    product_id: int,
    coingecko_id: str,
    client: Optional[CoinGeckoClient] = None,
    quote_currency: str = "eur",
    ) -> Optional[BasisResult]:
    """Reclassify and reprice every movement feeding one product.

    Parameters
    ----------
    session : Session
        Open database session.
    product_id : int
        Product to recompute.
    coingecko_id : str
        Market identifier used for pricing.
    client : CoinGeckoClient, optional
        Price source.
    quote_currency : str, optional
        Currency to price in.

    Returns
    -------
    BasisResult or None
        The reconstruction, or None when no watched address feeds this
        product — in which case there is nothing to derive and the cost basis
        stays whatever the ledger says.
    """
    holdings = session.exec(
        select(WalletHolding).where(WalletHolding.product_id == product_id)
        ).scalars().all()
    if not holdings:
        return None

    mine = own_addresses(session)
    wallet_ids = {h.wallet_id for h in holdings}
    contracts = {(h.contract_address or "").lower() for h in holdings}

    transfers = session.exec(
        select(WalletTransfer).where(WalletTransfer.wallet_id.in_(wallet_ids))
        ).scalars().all()
    relevant = [
        t for t in transfers
        if (t.contract_address or "").lower() in contracts
        ]

    for transfer in relevant:
        transfer.kind = classify(transfer, mine)

    incomplete = session.exec(
        select(Wallet).where(Wallet.id.in_(wallet_ids))
        ).scalars().all()
    history_complete = all(not w.last_sync_error for w in incomplete)

    result = derive_basis(
        relevant, coingecko_id, client, quote_currency, history_complete=history_complete
        )

    # Cache the price found for each acquisition so a later recompute does not
    # call the API again for a day whose price will never change.
    for transfer in relevant:
        if transfer.kind is TransferKind.ACQUISITION and transfer.unit_price_eur is None:
            price = _price_for(transfer, coingecko_id, client, quote_currency)
            if price is not None:
                transfer.unit_price_eur = price
                transfer.value_eur = (price * Decimal(str(transfer.units or 0))).quantize(
                    Decimal("0.01"))
                transfer.price_source = "coingecko"

    session.commit()
    store_estimate(session, product_id, result)
    return result
