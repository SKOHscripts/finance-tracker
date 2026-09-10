"""Running a scan: fetch, decide, record.

Everything with a side effect lives here, so :mod:`engine` can stay pure. The
service pulls the ranking from CoinGecko, hands the engine a portfolio built
from the database, and writes back what the next scan will need: the verdicts,
the two persistence flags the streak counters read, and the trace of a stake
already recovered.

It also refreshes the valuation of each priced line, marking those rows as
fetched rather than typed — a later price refresh will overwrite them, and
will leave a figure the user corrected by hand alone.
"""
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable, Optional

from sqlalchemy import select
from sqlmodel import Session

from finance_tracker.domain.enums import SignalVerdict, ValuationSource
from finance_tracker.domain.models import (
    PositionVerdict,
    ProfitTaken,
    ScanRun,
    Valuation,
    )

from .coingecko_client import CoinGeckoClient, CoinGeckoError, MarketRow
from .engine import AssetMetrics, PriorScan, ScanResult, build_metrics, run_scan
from .metrics import daily_closes
from .portfolio import ResolvedPosition, load_positions
from .rules import EXCLUDED_IDS, Rules, load_rules

# Extra depth requested from the ranking endpoint. Stablecoins and wrappers are
# filtered out afterwards, so asking for exactly top_n would return fewer.
_RANKING_OVERSHOOT = 20

# How many prior scans to load per position. The longest persistence
# requirement is a handful of weeks; a year of history is far more than any
# streak can consume, and keeps the query bounded.
_HISTORY_DEPTH = 52


class ScanError(RuntimeError):
    """Raised when a scan cannot be completed."""


@dataclass
class ScanProgress:
    """Progress callback payload, so a long scan can show where it is."""

    step: str
    current: int = 0
    total: int = 0


ProgressCallback = Callable[[ScanProgress], None]


def _noop(_: ScanProgress) -> None:
    """Default progress sink."""


def load_history(session: Session, product_id: int) -> list[PriorScan]:
    """Prior scans for one position, most recent first.

    The candidate identifier lives on the scan, not the verdict, because every
    position in a scan is arbitrated against the same one. Joining here keeps
    the streak comparison honest: a streak only counts while the candidate
    stays the same.

    Parameters
    ----------
    session : Session
        Open database session.
    product_id : int
        Product whose history to read.

    Returns
    -------
    list[PriorScan]
        Newest first, capped at ``_HISTORY_DEPTH`` entries.
    """
    rows = session.exec(
        select(PositionVerdict, ScanRun)
        .join(ScanRun, ScanRun.id == PositionVerdict.scan_run_id)
        .where(PositionVerdict.product_id == product_id)
        .order_by(ScanRun.scan_date.desc(), PositionVerdict.id.desc())
        .limit(_HISTORY_DEPTH)
        ).all()

    return [
        PriorScan(
            candidate_id=run.candidate_coingecko_id or "",
            rotation_ok=bool(verdict.rotation_gates_but_persistence),
            temporisation_ok=bool(verdict.temporisation_gates_but_persistence),
            )
        for verdict, run in rows
        ]


def profit_already_taken(session: Session) -> set[int]:
    """Product ids whose stake has already been recovered once."""
    rows = session.exec(select(ProfitTaken.product_id)).scalars().all()
    return {r for r in rows if r is not None}


def _metrics_for(
    client: CoinGeckoClient, market: MarketRow, rules: Rules
    ) -> AssetMetrics:
    """Fetch the price history of one asset and reduce it to metrics."""
    series = client.price_series(
        market.id, rules.universe.quote_currency, rules.lookback_days()
        )
    return build_metrics(
        daily_closes(series),
        market.id,
        market.symbol,
        rules,
        name=market.name,
        rank=market.rank,
        price=market.price,
        market_cap=market.market_cap,
        volume_24h=market.volume_24h,
        )


def build_universe(
    client: CoinGeckoClient, rules: Rules, held_ids: list[str]
    ) -> list[MarketRow]:
    """Assemble the assets to score: the ranking plus everything held.

    A held asset is always included even when it has fallen out of the top of
    the ranking — otherwise the engine would have no metrics for the very line
    it is being asked to arbitrate.

    Parameters
    ----------
    client : CoinGeckoClient
        Market data client.
    rules : Rules
        Thresholds.
    held_ids : list[str]
        Market identifiers currently held.

    Returns
    -------
    list[MarketRow]
        The ranking, filtered of stablecoins and wrappers, plus held assets.

    Raises
    ------
    ScanError
        When a held asset cannot be found on CoinGecko at all.
    """
    depth = rules.universe.top_n + _RANKING_OVERSHOOT
    markets = client.top_markets(rules.universe.quote_currency, depth)

    ranked = [m for m in markets if m.id not in EXCLUDED_IDS]
    universe = ranked[: rules.universe.top_n]
    present = {m.id for m in universe}

    missing = [pid for pid in dict.fromkeys(held_ids) if pid and pid not in present]
    if missing:
        found = client.markets_by_ids(missing, rules.universe.quote_currency)
        for pid in missing:
            row = found.get(pid) or next((m for m in markets if m.id == pid), None)
            if row is None:
                raise ScanError(
                    f"L'actif « {pid} » est introuvable sur CoinGecko. "
                    "Corrige son identifiant de marché dans la fiche du produit."
                    )
            universe.append(row)

    return universe


def select_refuge(
    client: CoinGeckoClient, rules: Rules
    ) -> tuple[Optional[AssetMetrics], list[dict]]:
    """Pick the first configured refuge that is liquid enough.

    Returns
    -------
    tuple
        The retained refuge (None when none qualifies) and every refuge
        examined, each with why it was or was not kept.
    """
    ids = list(rules.refuge_ids())
    if not ids:
        return None, []

    found = client.markets_by_ids(ids, rules.universe.quote_currency)
    floor = rules.gates.min_volume_24h
    examined: list[dict] = []
    chosen: Optional[AssetMetrics] = None

    for cid in ids:
        market = found.get(cid)
        liquid = bool(market and (market.volume_24h or 0) >= floor)
        examined.append({
            "id": cid,
            "symbol": market.symbol if market else None,
            "name": market.name if market else None,
            "price": market.price if market else None,
            "volume_24h": market.volume_24h if market else None,
            "found": market is not None,
            "liquid": liquid,
            })
        if chosen is None and market is not None and liquid and market.price:
            chosen = AssetMetrics(
                id=market.id,
                symbol=market.symbol,
                name=market.name,
                price=market.price,
                volume_24h=market.volume_24h,
                )

    return chosen, examined


def _persist(
    session: Session,
    result: ScanResult,
    resolved: dict[int, ResolvedPosition],
    scan_date: datetime,
    ) -> ScanRun:
    """Write the scan and its verdicts, and record any stake recovered.

    Parameters
    ----------
    session : Session
        Open database session. Committed here.
    result : ScanResult
        What the engine returned.
    resolved : dict[int, ResolvedPosition]
        Positions by product id, for provenance metadata.
    scan_date : datetime
        Timestamp recorded for the run.

    Returns
    -------
    ScanRun
        The persisted run, refreshed with its identifier.
    """
    run = ScanRun(
        scan_date=scan_date,
        verdict=result.verdict,
        regime=result.regime.state,
        candidate_coingecko_id=result.candidate.id if result.candidate else "",
        candidate_symbol=result.candidate.symbol if result.candidate else "",
        quote_currency=result.quote_currency,
        regime_json=json.dumps(result.regime.as_dict(), ensure_ascii=False),
        ranking_json=json.dumps(
            [vars(r) for r in result.ranking], ensure_ascii=False, default=str),
        discarded_json=json.dumps(result.discarded_candidates, ensure_ascii=False),
        insufficient_history_json=json.dumps(result.insufficient_history, ensure_ascii=False),
        )
    session.add(run)
    session.commit()
    session.refresh(run)

    for outcome in result.positions:
        detail = outcome.as_dict()
        source = resolved.get(outcome.position.product_id)
        if source is not None:
            detail["sources"] = vars(source.sources)

        session.add(PositionVerdict(
            scan_run_id=run.id,
            product_id=outcome.position.product_id,
            coingecko_id=outcome.position.coingecko_id,
            symbol=outcome.position.symbol,
            verdict=outcome.verdict,
            arbitrated=outcome.arbitrated,
            notional_eur=Decimal(str(round(outcome.current_value, 2))),
            gas_reserve_eur=Decimal(str(round(outcome.position.gas_reserve_eur or 0, 2))),
            arbitrable_eur=Decimal(str(round(outcome.arbitrable_value, 2))),
            cost_basis_eur=(
                None if outcome.position.cost_basis_eur is None
                else Decimal(str(round(outcome.position.cost_basis_eur, 2)))
                ),
            unrealised_gain_pct=(
                None if outcome.gain_pct is None
                else Decimal(str(round(outcome.gain_pct, 2)))
                ),
            score_delta=(
                None if outcome.score_delta is None
                else Decimal(str(round(float(outcome.score_delta), 3)))
                ),
            round_trip_cost_pct=(
                None if outcome.round_trip_cost_pct is None
                else Decimal(str(round(float(outcome.round_trip_cost_pct), 2)))
                ),
            required_edge_pct=(
                None if outcome.required_edge_pct is None
                else Decimal(str(round(float(outcome.required_edge_pct), 2)))
                ),
            streak_weeks=outcome.streak_weeks,
            rotation_gates_but_persistence=outcome.rotation_gates_but_persistence,
            temporisation_gates_but_persistence=outcome.temporisation_gates_but_persistence,
            detail_json=json.dumps(detail, ensure_ascii=False, default=str),
            ))

        # A proposed trim is recorded now, not when it is executed. The rule is
        # "propose this once": proposing it again next week because the user
        # has not acted yet would defeat its purpose.
        if outcome.verdict is SignalVerdict.ALLEGER:
            session.add(ProfitTaken(
                product_id=outcome.position.product_id,
                coingecko_id=outcome.position.coingecko_id,
                scan_date=scan_date,
                fraction=Decimal(str(outcome.profit_taking.extra.get("fraction", 0))),
                amount_eur=Decimal(str(outcome.profit_taking.extra.get("proceeds", 0))),
                cost_basis_eur=(
                    None if outcome.position.cost_basis_eur is None
                    else Decimal(str(round(outcome.position.cost_basis_eur, 2)))
                    ),
                ))

    session.commit()
    return run


def _refresh_valuations(session: Session, result: ScanResult, scan_date: datetime) -> int:
    """Record today's value of each priced line as a fetched valuation.

    Only lines whose units are known are written: without units there is no
    way to revalue, and copying yesterday's number under today's date would
    fabricate a data point.

    Returns
    -------
    int
        Number of valuations written.
    """
    written = 0
    for outcome in result.positions:
        if outcome.row is None or not outcome.row.price:
            continue
        if outcome.position.units is None:
            continue

        session.add(Valuation(
            product_id=outcome.position.product_id,
            date=scan_date,
            total_value_eur=Decimal(str(round(outcome.current_value, 2))),
            unit_price_eur=Decimal(str(round(float(outcome.row.price), 2))),
            source=ValuationSource.COINGECKO,
            ))
        written += 1

    if written:
        session.commit()
    return written


def run_signal_scan(
    session: Session,
    rules: Optional[Rules] = None,
    client: Optional[CoinGeckoClient] = None,
    persist: bool = True,
    refresh_valuations: bool = True,
    on_progress: ProgressCallback = _noop,
    ) -> tuple[ScanResult, Optional[ScanRun]]:
    """Run a full scan against live market data.

    Parameters
    ----------
    session : Session
        Open database session, used both to read the portfolio and to record
        the outcome.
    rules : Rules, optional
        Thresholds. Loaded from the packaged file when omitted.
    client : CoinGeckoClient, optional
        Market data client. One is built from the rules when omitted.
    persist : bool, optional
        Whether to record the run. False runs a scan without touching history,
        which also means it does not advance any persistence streak.
    refresh_valuations : bool, optional
        Whether to write a valuation per priced line.
    on_progress : ProgressCallback, optional
        Called as the scan advances, for a progress bar.

    Returns
    -------
    tuple
        The engine result, and the persisted run (None when ``persist`` is
        False).

    Raises
    ------
    ScanError
        When the portfolio holds no crypto position, or when market data
        cannot be retrieved.
    """
    rules = rules or load_rules()
    client = client or CoinGeckoClient(request_delay=rules.universe.request_delay_seconds)

    resolved_list = load_positions(session)
    if not resolved_list:
        raise ScanError(
            "Aucune position crypto à arbitrer. Associe au moins un produit à un "
            "identifiant de marché, ou ajoute un wallet à suivre."
            )

    positions = [r.position for r in resolved_list]
    resolved = {r.position.product_id: r for r in resolved_list}
    held_ids = [p.coingecko_id for p in positions]

    try:
        on_progress(ScanProgress("Récupération du classement"))
        universe = build_universe(client, rules, held_ids)

        rows: list[AssetMetrics] = []
        for index, market in enumerate(universe, start=1):
            on_progress(ScanProgress(
                f"Historique de {market.symbol}", current=index, total=len(universe)
                ))
            rows.append(_metrics_for(client, market, rules))

        on_progress(ScanProgress("Sélection du refuge"))
        refuge, refuges_examined = select_refuge(client, rules)
    except CoinGeckoError as exc:
        raise ScanError(str(exc)) from exc

    on_progress(ScanProgress("Application des barrières"))
    history = {p.product_id: load_history(session, p.product_id) for p in positions}

    result = run_scan(
        rows=rows,
        positions=positions,
        rules=rules,
        history=history,
        profit_already_taken=profit_already_taken(session),
        refuge=refuge,
        refuges_examined=refuges_examined,
        )

    scan_date = datetime.now(timezone.utc)
    run: Optional[ScanRun] = None

    if persist:
        on_progress(ScanProgress("Enregistrement du verdict"))
        run = _persist(session, result, resolved, scan_date)

    if refresh_valuations:
        _refresh_valuations(session, result, scan_date)

    return result, run


def latest_run(session: Session) -> Optional[ScanRun]:
    """Most recent recorded scan, or None when there has never been one."""
    return session.exec(
        select(ScanRun).order_by(ScanRun.scan_date.desc(), ScanRun.id.desc()).limit(1)
        ).scalars().first()


def verdicts_for_run(session: Session, scan_run_id: int) -> list[PositionVerdict]:
    """Every position verdict recorded for one scan."""
    return session.exec(
        select(PositionVerdict)
        .where(PositionVerdict.scan_run_id == scan_run_id)
        .order_by(PositionVerdict.symbol)
        ).scalars().all()


def run_history(session: Session, limit: int = 26) -> list[ScanRun]:
    """The most recent scans, newest first."""
    return session.exec(
        select(ScanRun).order_by(ScanRun.scan_date.desc(), ScanRun.id.desc()).limit(limit)
        ).scalars().all()
