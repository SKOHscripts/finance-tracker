"""Correcting a position's figures by hand.

Every number the engine arbitrates on is derived — from a chain, from the
ledger, from a reconstruction. Each derivation can be right about its source
and still wrong about reality: an address the user does not watch, a transfer
between two of their own wallets read as a purchase, a price history that stops
at a year. Without a way to say "no, it is this", the only recourse would be to
distrust the whole verdict.

So a correction here is not an escape hatch bolted on: it is the last rank of
the same precedence the rest of the pipeline follows, and it sits at the top
because the user is the only source that knows things no chain records.

Three properties make it safe to give a correction that much authority:

- **It is stored, not applied and forgotten.** It survives a sync, a rescan and
  a restart, so a figure corrected once stays corrected.
- **It is labelled.** The interface reports the line's provenance as *manual*,
  so a corrected figure is never mistaken for a derived one.
- **It is reversible.** Clearing it returns the line to whichever automatic
  source applied before, with nothing left behind.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlmodel import Session

from finance_tracker.domain.models import CryptoAsset, WalletHolding


class OverrideError(ValueError):
    """Raised when a correction would describe an impossible position.

    A ValueError subclass so the view catches one type and shows the message,
    which is written for the user.
    """


@dataclass(frozen=True)
class Divergence:
    """A correction that contradicts what the chain reports.

    Not an error: the user may well be right, and the whole point of the
    correction is that they can be. But a silent contradiction between the
    displayed figure and the synced balance is how a portfolio drifts without
    anyone noticing, so it is surfaced rather than swallowed.
    """

    symbol: str
    manual_units: Decimal
    chain_units: Decimal

    @property
    def difference(self) -> Decimal:
        """Signed gap, manual minus chain."""
        return self.manual_units - self.chain_units


def _chain_units(session: Session, product_id: int) -> Optional[Decimal]:
    """Units the watched addresses report for *product_id*, or None."""
    rows = session.exec(
        select(WalletHolding).where(
            WalletHolding.product_id == product_id,
            WalletHolding.ignored == False,  # noqa: E712  # pylint: disable=singleton-comparison
            )
        ).scalars().all()
    if not rows:
        return None
    return sum((Decimal(str(r.units or 0)) for r in rows), Decimal("0"))


def divergence(session: Session, asset: CryptoAsset, symbol: str = "") -> Optional[Divergence]:
    """Report a corrected quantity that disagrees with the synced balance.

    Parameters
    ----------
    session : Session
        Open database session.
    asset : CryptoAsset
        The line to check.
    symbol : str, optional
        Label for the message; falls back to the asset's ticker.

    Returns
    -------
    Divergence or None
        None when there is no correction, no watched address feeding the line,
        or the two agree.
    """
    if asset.manual_units is None:
        return None

    chain = _chain_units(session, asset.product_id)
    if chain is None:
        return None

    manual = Decimal(str(asset.manual_units))
    if manual == chain:
        return None

    return Divergence(
        symbol=(symbol or asset.symbol or "").upper(),
        manual_units=manual,
        chain_units=chain,
        )


def resolve_cost(
    units: Optional[Decimal],
    unit_cost_eur: Optional[Decimal],
    total_cost_eur: Optional[Decimal],
    ) -> Optional[Decimal]:
    """Turn whichever cost figure was given into a total.

    Both forms are accepted because both are how people hold the number: some
    remember what they paid per unit, others what left their bank account.

    Parameters
    ----------
    units : Decimal, optional
        Quantity the per-unit form is multiplied by. Required for that form.
    unit_cost_eur : Decimal, optional
        What one unit cost. Mutually exclusive with *total_cost_eur*.
    total_cost_eur : Decimal, optional
        What the whole holding cost.

    Returns
    -------
    Decimal or None
        Total invested, or None when neither form was given.

    Raises
    ------
    OverrideError
        When both forms are given, a figure is negative, or a per-unit cost is
        given with no quantity to multiply it by.
    """
    if unit_cost_eur is not None and total_cost_eur is not None:
        raise OverrideError(
            "Renseigne le prix de revient unitaire ou le capital total, pas les "
            "deux : les deux chiffres se contrediraient."
            )

    if unit_cost_eur is not None:
        if unit_cost_eur < 0:
            raise OverrideError("Le prix de revient ne peut pas être négatif.")
        if units is None:
            raise OverrideError(
                "Un prix de revient unitaire a besoin d'une quantité pour donner "
                "un capital. Renseigne la quantité, ou saisis directement le total."
                )
        return (unit_cost_eur * units).quantize(Decimal("0.01"))

    if total_cost_eur is not None:
        if total_cost_eur < 0:
            raise OverrideError("Le capital investi ne peut pas être négatif.")
        return total_cost_eur.quantize(Decimal("0.01"))

    return None


def set_overrides(
    session: Session,
    asset: CryptoAsset,
    *,
    units: Optional[Decimal] = None,
    cost_basis_eur: Optional[Decimal] = None,
    clear_units: bool = False,
    clear_cost_basis: bool = False,
    ) -> CryptoAsset:
    """Write, change or clear the corrections on one line.

    Absence and clearing are kept apart on purpose. Passing ``units=None``
    means "leave the quantity as it is", while ``clear_units=True`` means
    "return the quantity to its automatic source" — a distinction the caller
    needs, since a form that submits every field at once would otherwise wipe
    a correction it never touched.

    Parameters
    ----------
    session : Session
        Open database session. Committed here.
    asset : CryptoAsset
        The line to correct.
    units : Decimal, optional
        Corrected quantity. Must be positive or zero.
    cost_basis_eur : Decimal, optional
        Corrected total invested. Must be positive or zero.
    clear_units : bool, optional
        Drop the quantity correction, whatever *units* holds.
    clear_cost_basis : bool, optional
        Drop the cost correction, whatever *cost_basis_eur* holds.

    Returns
    -------
    CryptoAsset
        The updated line.

    Raises
    ------
    OverrideError
        On a negative figure.
    """
    if clear_units:
        asset.manual_units = None
    elif units is not None:
        if units < 0:
            raise OverrideError(
                "Une quantité détenue ne peut pas être négative. Mets zéro pour "
                "une ligne vidée, ou laisse le champ vide pour revenir à l'automatique."
                )
        asset.manual_units = units

    if clear_cost_basis:
        asset.manual_cost_basis_eur = None
    elif cost_basis_eur is not None:
        if cost_basis_eur < 0:
            raise OverrideError("Le capital investi ne peut pas être négatif.")
        asset.manual_cost_basis_eur = cost_basis_eur

    session.commit()
    session.refresh(asset)
    return asset


def clear_all(session: Session, asset: CryptoAsset) -> CryptoAsset:
    """Return one line entirely to its automatic sources."""
    return set_overrides(session, asset, clear_units=True, clear_cost_basis=True)


def set_reserve_and_arbitration(
    session: Session,
    asset: CryptoAsset,
    *,
    gas_reserve_eur: Optional[Decimal] = None,
    arbitrated: Optional[bool] = None,
    ) -> CryptoAsset:
    """Adjust the fee reserve and whether the engine may move this line.

    Neither is a correction — they are settings on the line — but they are
    edited from the same table, so they are written the same way.

    Raises
    ------
    OverrideError
        When the reserve is negative.
    """
    if gas_reserve_eur is not None:
        if gas_reserve_eur < 0:
            raise OverrideError("La réserve de frais ne peut pas être négative.")
        asset.gas_reserve_eur = gas_reserve_eur

    if arbitrated is not None:
        asset.arbitrated = bool(arbitrated)

    session.commit()
    session.refresh(asset)
    return asset
