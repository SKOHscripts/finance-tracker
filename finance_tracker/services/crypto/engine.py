"""The rotation engine.

Pure decision logic: it takes a scored market, a portfolio and a history, and
returns a verdict per position. No network, no database, no clock — which is
what makes a verdict reproducible and testable, and what lets the report say
exactly why it landed where it did.

Four mechanisms run on each position, in a fixed order of priority:

1. **Trailing stop.** A winning line that has given back too much of its peak
   exits entirely. Protecting realised capital outranks everything else.
2. **Profit taking.** Once, when the latent gain is large enough, sell exactly
   the fraction that returns the stake net of fees. The rest keeps running.
3. **Rotation.** Six barriers against the ranked candidate. All must pass.
4. **Temporisation.** Only when no rotation passes: a one-way exit to a
   stablecoin while the market is measurably degraded.

None of them predicts anything. They are asymmetric rules — take the stake
back when the gain is there, cut when the price breaks down, refuse to buy
into a decline that has already been measured — and not one of them requires
knowing what happens next.
"""
from dataclasses import dataclass, field
from typing import Iterable, Optional

from finance_tracker.domain.enums import MarketRegime, SignalVerdict

from . import metrics as mx
from .rules import EXCLUDED_IDS, Rules

# Which verdict wins when several mechanisms fire on the same portfolio. Used
# only to summarise a scan in one word; every position keeps its own.
_VERDICT_PRIORITY: dict[SignalVerdict, int] = {
    SignalVerdict.SORTIE_STOP: 4,
    SignalVerdict.ALLEGER: 3,
    SignalVerdict.ROTATION: 2,
    SignalVerdict.TEMPORISER: 1,
    SignalVerdict.CONSERVER: 0,
    }


@dataclass
class AssetMetrics:
    """One ranked asset with every metric the gates read.

    Parameters
    ----------
    id : str
        CoinGecko identifier.
    symbol : str
        Ticker in upper case.
    name : str
        Display name.
    rank : Optional[int]
        Market-capitalisation rank.
    price : Optional[float]
        Current price in the quote currency.
    market_cap : Optional[float]
        Market capitalisation.
    volume_24h : Optional[float]
        24-hour traded volume.
    ret_7d, ret_fast, ret_slow : Optional[float]
        Returns over a week, the fast window and the slow window, in percent.
    vol_30d : Optional[float]
        Annualised 30-day volatility, in percent.
    max_dd_90d : Optional[float]
        Worst 90-day peak-to-trough decline, in percent.
    dist_high_90d : Optional[float]
        Distance below the 90-day high, in percent.
    dist_high_stop : Optional[float]
        Distance below the high of the trailing-stop window, in percent.
    long_average : Optional[float]
        Long moving average used by the regime reading.
    sample_days : int
        Number of daily closes actually available.
    z_slow, z_fast, z_vol : float
        Standard scores within the ranking, filled by :func:`score_universe`.
    score : float
        Composite score, filled by :func:`score_universe`.
    """

    id: str
    symbol: str
    name: str = ""
    rank: Optional[int] = None
    price: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    ret_7d: Optional[float] = None
    ret_fast: Optional[float] = None
    ret_slow: Optional[float] = None
    vol_30d: Optional[float] = None
    max_dd_90d: Optional[float] = None
    dist_high_90d: Optional[float] = None
    dist_high_stop: Optional[float] = None
    long_average: Optional[float] = None
    sample_days: int = 0
    z_slow: float = 0.0
    z_fast: float = 0.0
    z_vol: float = 0.0
    score: float = 0.0


@dataclass
class Position:
    """A held line, as the engine needs to see it.

    Units are the honest input where they exist: the value of the line is
    recomputed at the scan's price rather than carried over from whenever the
    user last typed a number. ``notional_eur`` is the fallback for a line
    tracked in euros only.

    Parameters
    ----------
    product_id : int
        Tracker product this line belongs to.
    coingecko_id : str
        Market identifier used to price it.
    symbol : str
        Ticker, for display.
    units : Optional[float]
        Units held. Preferred over ``notional_eur`` whenever available.
    notional_eur : Optional[float]
        Value of the line, used when units are unknown.
    gas_reserve_eur : float
        Share never proposed for a swap, for an asset that also pays fees.
    cost_basis_eur : Optional[float]
        Capital invested. Without it neither the stop nor profit taking can
        run, because both are defined against the stake.
    arbitrated : bool
        False to price and display the line but keep it out of every verdict.
    """

    product_id: int
    coingecko_id: str
    symbol: str = ""
    units: Optional[float] = None
    notional_eur: Optional[float] = None
    gas_reserve_eur: float = 0.0
    cost_basis_eur: Optional[float] = None
    arbitrated: bool = True

    def current_value(self, row: Optional[AssetMetrics]) -> float:
        """Value of the line at the scan's price.

        Parameters
        ----------
        row : AssetMetrics or None
            Market row for this asset.

        Returns
        -------
        float
            Units times price when both are known, otherwise the stored
            notional, otherwise zero.
        """
        if self.units is not None and row is not None and row.price:
            return float(self.units) * float(row.price)
        return float(self.notional_eur or 0.0)

    def arbitrable_value(self, row: Optional[AssetMetrics]) -> float:
        """Value a proposed move would actually carry, reserve excluded."""
        return max(self.current_value(row) - float(self.gas_reserve_eur or 0.0), 0.0)

    def gain_pct(self, row: Optional[AssetMetrics]) -> Optional[float]:
        """Latent gain in percent, or None when the stake is unknown."""
        if not self.cost_basis_eur:
            return None
        value = self.current_value(row)
        if value <= 0:
            return None
        return (value / float(self.cost_basis_eur) - 1.0) * 100.0


@dataclass
class PriorScan:
    """One earlier scan, as the persistence gates read it.

    Parameters
    ----------
    candidate_id : str
        Candidate that scan was arbitrated against.
    rotation_ok : bool
        Whether every rotation gate but persistence passed then.
    temporisation_ok : bool
        Same, for the refuge gates.
    """

    candidate_id: str
    rotation_ok: bool
    temporisation_ok: bool


@dataclass
class Gate:
    """One barrier, with the figure that made it pass or fail.

    Storing the measured value and the threshold side by side is the point:
    a verdict nobody can audit is a verdict nobody should act on.
    """

    name: str
    passed: bool
    value: object = None
    threshold: object = None
    unit: str = ""

    def as_dict(self) -> dict:
        """Serialise for storage and rendering."""
        return {
            "name": self.name,
            "pass": self.passed,
            "value": self.value,
            "threshold": self.threshold,
            "unit": self.unit,
            }


@dataclass
class Mechanism:
    """Outcome of one of the four mechanisms on one position.

    Parameters
    ----------
    applicable : bool
        False when the mechanism was not evaluated at all.
    reason : str
        Why it was not evaluated, when ``applicable`` is False.
    verdict : Optional[SignalVerdict]
        What the mechanism concluded, None when not applicable.
    gates : list[Gate]
        The barriers it evaluated.
    extra : dict
        Mechanism-specific figures kept for the report.
    """

    applicable: bool = True
    reason: str = ""
    verdict: Optional[SignalVerdict] = None
    gates: list[Gate] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    @property
    def all_gates_pass(self) -> bool:
        """Whether every gate passed. False on an empty gate list."""
        return bool(self.gates) and all(g.passed for g in self.gates)

    def as_dict(self) -> dict:
        """Serialise for storage and rendering."""
        return {
            "applicable": self.applicable,
            "reason": self.reason,
            "verdict": self.verdict.value if self.verdict else None,
            "gates": [g.as_dict() for g in self.gates],
            **self.extra,
            }


@dataclass
class PositionOutcome:
    """Everything one position produced in one scan."""

    position: Position
    verdict: SignalVerdict = SignalVerdict.CONSERVER
    arbitrated: bool = True
    reason: str = ""
    row: Optional[AssetMetrics] = None
    current_value: float = 0.0
    arbitrable_value: float = 0.0
    gain_pct: Optional[float] = None
    rotation: Mechanism = field(default_factory=Mechanism)
    trailing_stop: Mechanism = field(default_factory=Mechanism)
    profit_taking: Mechanism = field(default_factory=Mechanism)
    temporisation: Mechanism = field(default_factory=Mechanism)
    plan: Optional[dict] = None
    round_trip_cost_pct: Optional[float] = None
    required_edge_pct: Optional[float] = None
    score_delta: Optional[float] = None
    streak_weeks: int = 0
    rotation_gates_but_persistence: bool = False
    temporisation_gates_but_persistence: bool = False

    def as_dict(self) -> dict:
        """Serialise the detail kept alongside the stored verdict."""
        return {
            "rotation": self.rotation.as_dict(),
            "trailing_stop": self.trailing_stop.as_dict(),
            "profit_taking": self.profit_taking.as_dict(),
            "temporisation": self.temporisation.as_dict(),
            "plan": self.plan,
            "reason": self.reason,
            }


@dataclass
class RegimeReading:
    """Observed state of the market, with the two measures behind it."""

    applicable: bool
    state: MarketRegime
    reference_id: str = ""
    reference_symbol: str = ""
    reference_price: Optional[float] = None
    long_average: Optional[float] = None
    long_average_days: int = 0
    above_average: Optional[bool] = None
    breadth_pct: Optional[float] = None
    min_breadth_pct: float = 0.0
    reason: str = ""

    def as_dict(self) -> dict:
        """Serialise for storage and rendering."""
        return {
            "applicable": self.applicable,
            "state": self.state.value,
            "reference_id": self.reference_id,
            "reference_symbol": self.reference_symbol,
            "reference_price": self.reference_price,
            "long_average": self.long_average,
            "long_average_days": self.long_average_days,
            "above_average": self.above_average,
            "breadth_pct": self.breadth_pct,
            "min_breadth_pct": self.min_breadth_pct,
            "reason": self.reason,
            }


@dataclass
class ScanResult:
    """The whole outcome of one scan."""

    verdict: SignalVerdict
    regime: RegimeReading
    candidate: Optional[AssetMetrics]
    discarded_candidates: list[dict]
    ranking: list[AssetMetrics]
    positions: list[PositionOutcome]
    refuge: Optional[AssetMetrics] = None
    refuges_examined: list[dict] = field(default_factory=list)
    insufficient_history: list[str] = field(default_factory=list)
    quote_currency: str = "EUR"


# ── ranking ────────────────────────────────────────────────────────────────────


def build_metrics(closes: list[float], row_id: str, symbol: str, rules: Rules,
                  **market) -> AssetMetrics:
    """Compute every metric for one asset from its daily closes.

    Parameters
    ----------
    closes : list[float]
        Daily closes, oldest first.
    row_id : str
        CoinGecko identifier.
    symbol : str
        Ticker.
    rules : Rules
        Thresholds, for the window lengths.
    **market
        Passthrough market fields (name, rank, price, market_cap, volume_24h).

    Returns
    -------
    AssetMetrics
        Metrics, with None wherever the history was too short.
    """
    fast = rules.signal.fast_window_days
    slow = rules.signal.slow_window_days
    stop_window = rules.trailing_stop.window_days if rules.trailing_stop.enabled else 90

    return AssetMetrics(
        id=row_id,
        symbol=symbol,
        name=market.get("name", ""),
        rank=market.get("rank"),
        price=market.get("price"),
        market_cap=market.get("market_cap"),
        volume_24h=market.get("volume_24h"),
        ret_7d=mx.pct_return(closes, 7),
        ret_fast=mx.pct_return(closes, fast),
        ret_slow=mx.pct_return(closes, slow),
        vol_30d=mx.annualised_vol(closes, 30),
        max_dd_90d=mx.max_drawdown(closes, 90),
        dist_high_90d=mx.dist_from_high(closes, 90),
        dist_high_stop=mx.dist_from_high(closes, stop_window),
        long_average=mx.moving_average(closes, rules.regime.long_average_days),
        sample_days=len(closes),
        )


def score_universe(rows: list[AssetMetrics], rules: Rules) -> list[AssetMetrics]:
    """Score and sort the ranking in place, best first.

    Each term is a z-score against the ranking of the day, so a macro shock
    that moves the whole market in one direction cancels out on its own — the
    score answers "which of these is doing better than the others", never
    "is the market going up".

    Parameters
    ----------
    rows : list[AssetMetrics]
        Assets to score. Mutated: z-scores and score are filled in.
    rules : Rules
        Weights.

    Returns
    -------
    list[AssetMetrics]
        The same objects, sorted by descending score.
    """
    weights = rules.signal
    slow_pop = [r.ret_slow for r in rows]
    fast_pop = [r.ret_fast for r in rows]
    vol_pop = [r.vol_30d for r in rows]

    for row in rows:
        row.z_slow = mx.zscore(row.ret_slow, slow_pop)
        row.z_fast = mx.zscore(row.ret_fast, fast_pop)
        row.z_vol = mx.zscore(row.vol_30d, vol_pop)
        row.score = (
            weights.weight_slow_momentum * row.z_slow
            + weights.weight_fast_momentum * row.z_fast
            - weights.weight_volatility * row.z_vol
            )

    rows.sort(key=lambda r: r.score, reverse=True)
    return rows


def candidate_filters(row: AssetMetrics, rules: Rules) -> list[str]:
    """Return the intrinsic filters *row* fails, empty when it is eligible.

    These three say nothing about the position being replaced: they ask
    whether the asset is worth holding at all.
    """
    gates = rules.gates
    failures: list[str] = []

    if row.vol_30d is None or row.vol_30d > gates.max_candidate_vol_pct:
        shown = "inconnue" if row.vol_30d is None else f"{row.vol_30d:.1f} %"
        failures.append(f"volatilité {shown} > {gates.max_candidate_vol_pct} %")

    if row.max_dd_90d is None or row.max_dd_90d < -gates.max_candidate_drawdown_pct:
        shown = "inconnu" if row.max_dd_90d is None else f"{row.max_dd_90d:.1f} %"
        failures.append(f"drawdown {shown} < -{gates.max_candidate_drawdown_pct} %")

    volume = row.volume_24h or 0
    if volume < gates.min_volume_24h:
        failures.append(
            f"volume {volume / 1e6:.0f} M < {gates.min_volume_24h / 1e6:.0f} M"
            )

    return failures


def select_candidate(
    rows: list[AssetMetrics], held_ids: Iterable[str], rules: Rules
    ) -> tuple[Optional[AssetMetrics], list[dict]]:
    """Pick the asset every position is arbitrated against.

    By default the engine walks down the ranking until it finds an asset that
    clears the three intrinsic filters. Without that fallback a very volatile
    leader stays the candidate every week, fails every week, and blocks any
    rotation towards the asset behind it.

    Parameters
    ----------
    rows : list[AssetMetrics]
        Scored ranking, best first.
    held_ids : Iterable[str]
        Identifiers already held; they cannot be their own candidate.
    rules : Rules
        Thresholds.

    Returns
    -------
    tuple
        The candidate (None when every ranked asset is already held) and the
        higher-ranked assets skipped, each with the filters it failed.
    """
    mine = set(held_ids)
    free = [r for r in rows if r.id not in mine]
    if not free:
        return None, []

    if not rules.gates.use_fallback_candidate:
        return free[0], []

    discarded: list[dict] = []
    for row in free:
        failures = candidate_filters(row, rules)
        if not failures:
            return row, discarded
        discarded.append({
            "id": row.id,
            "symbol": row.symbol,
            "score": round(row.score, 3),
            "reasons": failures,
            })

    # Nothing is eligible. Keep the top-ranked asset so the position gates can
    # say why, rather than reporting nothing at all.
    return free[0], discarded[1:]


# ── regime ─────────────────────────────────────────────────────────────────────


def evaluate_regime(rows: list[AssetMetrics], rules: Rules) -> RegimeReading:
    """Read the market's observed state from two independent measures.

    The reference asset above or below its long moving average, and the share
    of the ranking in positive slow momentum. Both favourable is BULL, one is
    MIXTE, neither is BEAR. It describes the market at the scan date and
    predicts nothing.
    """
    conf = rules.regime
    if not conf.enabled:
        return RegimeReading(
            applicable=False,
            state=MarketRegime.INCONNU,
            reason="La lecture de régime est désactivée dans la configuration.",
            )

    reference = next((r for r in rows if r.id == conf.reference_id), None)
    above: Optional[bool] = None
    if reference is not None and reference.long_average and reference.price:
        above = reference.price >= reference.long_average

    population = [r for r in rows if r.ret_slow is not None]
    breadth: Optional[float] = None
    if population:
        breadth = 100.0 * sum(1 for r in population if r.ret_slow > 0) / len(population)
    breadth_ok = breadth is not None and breadth >= conf.min_breadth_pct

    signals = [s for s in (above, breadth_ok) if s is not None]
    if len(signals) < 2:
        state = MarketRegime.INCONNU
    elif all(signals):
        state = MarketRegime.BULL
    elif any(signals):
        state = MarketRegime.MIXTE
    else:
        state = MarketRegime.BEAR

    return RegimeReading(
        applicable=True,
        state=state,
        reference_id=conf.reference_id,
        reference_symbol=reference.symbol if reference else "",
        reference_price=reference.price if reference else None,
        long_average=reference.long_average if reference else None,
        long_average_days=conf.long_average_days,
        above_average=above,
        breadth_pct=None if breadth is None else round(breadth, 1),
        min_breadth_pct=conf.min_breadth_pct,
        reason="" if state is not MarketRegime.INCONNU else (
            "Historique insuffisant sur l'actif de référence : le régime n'est pas lu."
            ),
        )


# ── streaks ────────────────────────────────────────────────────────────────────


def _rotation_streak(history: list[PriorScan], candidate_id: str) -> int:
    """Consecutive prior scans where the same candidate cleared every gate.

    Counted from the most recent scan backwards and stopped at the first miss:
    a candidate that held for three weeks, lapsed, then held again has not
    held for four.
    """
    streak = 0
    for entry in history:
        if entry.rotation_ok and entry.candidate_id == candidate_id:
            streak += 1
        else:
            break
    return streak


def _temporisation_streak(history: list[PriorScan]) -> int:
    """Consecutive prior scans where the refuge conditions all held."""
    streak = 0
    for entry in history:
        if entry.temporisation_ok:
            streak += 1
        else:
            break
    return streak


# ── mechanisms ─────────────────────────────────────────────────────────────────


def evaluate_rotation(
    position: Position,
    held: AssetMetrics,
    candidate: Optional[AssetMetrics],
    rules: Rules,
    history: list[PriorScan],
    regime: RegimeReading,
    ) -> Mechanism:
    """Six barriers between a held line and the ranked candidate.

    All must pass. The persistence gate is evaluated last and only counts a
    streak once every other gate is satisfied, so a candidate that flickers in
    and out of eligibility never accumulates one.
    """
    if candidate is None:
        return Mechanism(
            applicable=False,
            reason="Aucun candidat disponible : tout le classement est déjà détenu.",
            )

    gates_conf = rules.gates
    arbitrable = position.arbitrable_value(held)
    cost = rules.costs.round_trip_pct(arbitrable)
    required_edge = cost * gates_conf.cost_margin_multiple

    score_delta = candidate.score - held.score
    momentum_edge = None
    if candidate.ret_slow is not None and held.ret_slow is not None:
        momentum_edge = candidate.ret_slow - held.ret_slow

    gates = [
        Gate(
            "ecart_de_score",
            score_delta >= gates_conf.min_score_delta,
            round(score_delta, 3), gates_conf.min_score_delta, "écart-type",
            ),
        Gate(
            "avantage_momentum_vs_cout",
            momentum_edge is not None and momentum_edge >= required_edge,
            None if momentum_edge is None else round(momentum_edge, 2),
            round(required_edge, 2), "% sur la fenêtre lente",
            ),
        Gate(
            "volatilite_candidat",
            candidate.vol_30d is not None and candidate.vol_30d <= gates_conf.max_candidate_vol_pct,
            None if candidate.vol_30d is None else round(candidate.vol_30d, 1),
            gates_conf.max_candidate_vol_pct, "% annualisé",
            ),
        Gate(
            "drawdown_candidat",
            candidate.max_dd_90d is not None
            and candidate.max_dd_90d >= -gates_conf.max_candidate_drawdown_pct,
            None if candidate.max_dd_90d is None else round(candidate.max_dd_90d, 1),
            -gates_conf.max_candidate_drawdown_pct, "% sur 90j",
            ),
        Gate(
            "liquidite_candidat",
            (candidate.volume_24h or 0) >= gates_conf.min_volume_24h,
            candidate.volume_24h, gates_conf.min_volume_24h, "volume 24h",
            ),
        ]

    if regime.applicable:
        gates.append(Gate(
            "regime_favorable",
            regime.state is not MarketRegime.BEAR,
            regime.state.value, "BULL ou MIXTE", "régime constaté",
            ))

    all_but_persistence = all(g.passed for g in gates)
    # The current scan counts towards the streak only if it qualifies.
    streak = _rotation_streak(history, candidate.id) + (1 if all_but_persistence else 0)

    gates.append(Gate(
        "persistance",
        all_but_persistence and streak >= gates_conf.required_consecutive_weeks,
        streak, gates_conf.required_consecutive_weeks, "scans consécutifs",
        ))

    passed = all(g.passed for g in gates)
    return Mechanism(
        applicable=True,
        verdict=SignalVerdict.ROTATION if passed else SignalVerdict.CONSERVER,
        gates=gates,
        extra={
            "candidate_id": candidate.id,
            "candidate_symbol": candidate.symbol,
            "score_delta": round(score_delta, 3),
            "round_trip_cost_pct": round(cost, 2),
            "required_edge_pct": round(required_edge, 2),
            "streak_weeks": streak,
            "all_gates_but_persistence": all_but_persistence,
            },
        )


def evaluate_trailing_stop(position: Position, row: AssetMetrics, rules: Rules) -> Mechanism:
    """Full exit when a line in profit gives back too much of its peak.

    Does nothing on a losing line: there, the regime temporisation decides.
    The stop protects a gain; it does not judge what comes next.
    """
    conf = rules.trailing_stop
    if not conf.enabled:
        return Mechanism(applicable=False, reason="Le stop suiveur est désactivé.")

    gain = position.gain_pct(row)
    if gain is None:
        return Mechanism(
            applicable=False,
            reason=(
                "Capital investi inconnu sur cette ligne. Renseigne un prix de revient "
                "— saisi à la main ou dérivé d'un wallet — pour que le stop puisse agir."
                ),
            )

    pullback = row.dist_high_stop
    gates = [
        Gate(
            "position_en_gain",
            gain > conf.min_gain_pct,
            round(gain, 1), conf.min_gain_pct, "% de plus-value latente",
            ),
        Gate(
            "repli_depuis_le_haut",
            pullback is not None and pullback <= -conf.max_drawdown_pct,
            None if pullback is None else round(pullback, 1),
            -conf.max_drawdown_pct, f"% sous le plus haut {conf.window_days}j",
            ),
        ]

    passed = all(g.passed for g in gates)
    return Mechanism(
        applicable=True,
        verdict=SignalVerdict.SORTIE_STOP if passed else SignalVerdict.CONSERVER,
        gates=gates,
        extra={"gain_pct": round(gain, 1)},
        )


def evaluate_profit_taking(
    position: Position, row: AssetMetrics, rules: Rules, already_taken: bool
    ) -> Mechanism:
    """Recover the stake once, when the latent gain is large enough.

    The fraction sold is exactly the one that returns the invested capital net
    of fees, capped so this mechanism can never liquidate a whole line. It
    answers a specific failure mode: never selling anything, ever.
    """
    conf = rules.profit_taking
    if not conf.enabled:
        return Mechanism(applicable=False, reason="La prise de bénéfice est désactivée.")

    gain = position.gain_pct(row)
    if gain is None or not position.cost_basis_eur:
        return Mechanism(
            applicable=False,
            reason=(
                "Capital investi inconnu sur cette ligne. Renseigne un prix de revient "
                "pour que la récupération de la mise puisse être calculée."
                ),
            )

    invested = float(position.cost_basis_eur)
    value = position.current_value(row)
    fee_pct = rules.costs.worst_case_pct()
    # Sell enough that the proceeds, after fees, return the stake exactly.
    gross_needed = invested / (1 - fee_pct / 100.0)
    fraction = min(gross_needed / value, conf.max_fraction) if value > 0 else 0.0
    proceeds = fraction * value

    gates = [
        Gate(
            "plus_value",
            gain >= conf.trigger_gain_pct,
            round(gain, 1), conf.trigger_gain_pct, "% de plus-value latente",
            ),
        Gate(
            "montant_vendu_suffisant",
            proceeds >= conf.min_notional,
            round(proceeds, 2), conf.min_notional, "montant vendu",
            ),
        Gate(
            "jamais_pris",
            (not conf.once_only) or not already_taken,
            "oui" if already_taken else "non", "non", "récupération déjà faite",
            ),
        ]

    passed = all(g.passed for g in gates)
    return Mechanism(
        applicable=True,
        verdict=SignalVerdict.ALLEGER if passed else SignalVerdict.CONSERVER,
        gates=gates,
        extra={
            "gain_pct": round(gain, 1),
            "fraction": round(fraction, 4),
            "proceeds": round(proceeds, 2),
            "cost_basis": round(invested, 2),
            },
        )


def evaluate_temporisation(
    position: Position,
    held: AssetMetrics,
    rows: list[AssetMetrics],
    refuge: Optional[AssetMetrics],
    rules: Rules,
    history: list[PriorScan],
    regime: RegimeReading,
    ) -> Mechanism:
    """Six barriers for a one-way exit into a stablecoin refuge.

    Every one of them is retrospective: a decline already measured, a share of
    the ranking already negative. Waiting it out is the third choice, never an
    alternative to a rotation that passes.
    """
    conf = rules.temporisation
    arbitrable = position.arbitrable_value(held)
    one_way = rules.costs.one_way_pct(arbitrable)
    required_drop = one_way * conf.cost_margin_multiple

    peers = [r for r in rows if r.id != held.id and r.ret_slow is not None]
    bearish_share = None
    if peers:
        bearish_share = 100.0 * sum(1 for r in peers if r.ret_slow < 0) / len(peers)

    slow, drawdown = held.ret_slow, held.max_dd_90d
    regime_bear = regime.state is MarketRegime.BEAR

    gates = [
        Gate(
            "momentum_actif_detenu",
            slow is not None and slow <= conf.max_held_slow_momentum_pct,
            None if slow is None else round(slow, 2),
            conf.max_held_slow_momentum_pct, "% sur la fenêtre lente",
            ),
        Gate(
            "drawdown_actif_detenu",
            drawdown is not None and drawdown <= -conf.min_held_drawdown_pct,
            None if drawdown is None else round(drawdown, 1),
            -conf.min_held_drawdown_pct, "% sur 90j",
            ),
        Gate(
            # Satisfied by the breadth of the ranking, or directly by an
            # observed BEAR regime: two readings of the same fact.
            "regime_marche",
            (bearish_share is not None and bearish_share >= conf.min_bearish_share_pct)
            or regime_bear,
            "BEAR" if regime_bear else (
                None if bearish_share is None else round(bearish_share, 1)),
            conf.min_bearish_share_pct,
            "% du classement en momentum lent négatif, ou régime BEAR",
            ),
        Gate(
            "baisse_vs_cout",
            slow is not None and -slow >= required_drop,
            None if slow is None else round(-slow, 2),
            round(required_drop, 2), "% contre le coût d'un aller simple",
            ),
        Gate(
            "liquidite_refuge",
            refuge is not None,
            None if refuge is None else refuge.volume_24h,
            rules.gates.min_volume_24h, "volume 24h",
            ),
        ]

    all_but_persistence = all(g.passed for g in gates)
    streak = _temporisation_streak(history) + (1 if all_but_persistence else 0)

    gates.append(Gate(
        "persistance",
        all_but_persistence and streak >= conf.required_consecutive_weeks,
        streak, conf.required_consecutive_weeks, "scans consécutifs",
        ))

    passed = all(g.passed for g in gates)
    return Mechanism(
        applicable=True,
        verdict=SignalVerdict.TEMPORISER if passed else SignalVerdict.CONSERVER,
        gates=gates,
        extra={
            "refuge_id": refuge.id if refuge else None,
            "refuge_symbol": refuge.symbol if refuge else None,
            "one_way_cost_pct": round(one_way, 2),
            "required_drop_pct": round(required_drop, 2),
            "streak_weeks": streak,
            "all_gates_but_persistence": all_but_persistence,
            },
        )


# ── swap plans ─────────────────────────────────────────────────────────────────
#
# A plan is a set of parameters to carry out by hand. Nothing here executes,
# quotes or signs anything. `min_accept_units` is the number below which the
# quote no longer matches what the scan measured — the point of calling it off.


def _units_at(amount: float, price: Optional[float]) -> Optional[float]:
    """Units *amount* buys at *price*, or None when the price is unknown."""
    if not price:
        return None
    return amount / price


def _plan(rules: Rules, from_symbol: str, to_symbol: str, to_id: str,
          amount: float, price: Optional[float], providers: tuple[str, ...],
          note: str = "", **extra) -> dict:
    """Assemble the common shape of every swap plan."""
    worst_case = rules.costs.worst_case_pct()
    units = _units_at(amount, price)
    return {
        "from_symbol": from_symbol,
        "to_symbol": to_symbol,
        "to_id": to_id,
        "amount": round(amount, 2),
        "reference_price": price,
        "units_at_reference": None if units is None else round(units, 8),
        "min_accept_units": None if units is None else round(units * (1 - worst_case / 100), 8),
        "max_acceptable_loss_pct": round(worst_case, 2),
        "quotes_to_compare": list(providers),
        "note": note,
        **extra,
        }


def rotation_plan(position: Position, held: AssetMetrics,
                  candidate: AssetMetrics, rules: Rules) -> dict:
    """Parameters of the two-leg swap into the candidate."""
    return _plan(
        rules, held.symbol, candidate.symbol, candidate.id,
        position.arbitrable_value(held), candidate.price,
        rules.routes.providers_to_quote,
        note=rules.routes.atomic_swap_note,
        kind="ROTATION",
        )


def temporisation_plan(position: Position, held: AssetMetrics,
                       refuge: AssetMetrics, rules: Rules) -> dict:
    """Parameters of the one-way exit into the refuge."""
    return _plan(
        rules, held.symbol, refuge.symbol, refuge.id,
        position.arbitrable_value(held), refuge.price,
        rules.routes.stable_providers_to_quote,
        note=(
            f"{rules.routes.stable_note} "
            "Après exécution, enregistre le swap : la position bascule sur le refuge, "
            "et on n'en ressort que par les six barrières de rotation habituelles."
            ).strip(),
        kind="TEMPORISATION",
        )


def trim_plan(position: Position, row: AssetMetrics, refuge: Optional[AssetMetrics],
              mechanism: Mechanism, rules: Rules) -> Optional[dict]:
    """Parameters of the partial sale that returns the stake."""
    if refuge is None:
        return None
    value = position.current_value(row)
    amount = float(mechanism.extra.get("proceeds", 0.0))
    fraction = float(mechanism.extra.get("fraction", 0.0))
    return _plan(
        rules, row.symbol, refuge.symbol, refuge.id, amount, refuge.price,
        rules.routes.stable_providers_to_quote,
        note=(
            f"Vente partielle : {fraction * 100:.1f} % de la ligne, pour récupérer "
            f"les {mechanism.extra.get('cost_basis')} € investis nets de frais. Le reste "
            "continue de rouler, protégé par le stop suiveur."
            ),
        kind="ALLEGEMENT",
        fraction_of_line=fraction,
        remaining_after=round(value - amount, 2),
        )


def stop_exit_plan(position: Position, row: AssetMetrics, refuge: Optional[AssetMetrics],
                   mechanism: Mechanism, rules: Rules) -> Optional[dict]:
    """Parameters of the full exit triggered by the trailing stop."""
    if refuge is None:
        return None
    pullback = next(
        (g.value for g in mechanism.gates if g.name == "repli_depuis_le_haut"), None
        )
    return _plan(
        rules, row.symbol, refuge.symbol, refuge.id,
        position.arbitrable_value(row), refuge.price,
        rules.routes.stable_providers_to_quote,
        note=(
            f"Sortie complète : la ligne a cédé {abs(pullback) if pullback is not None else '?'} % "
            f"depuis son plus haut, au-delà du seuil de {rules.trailing_stop.max_drawdown_pct} %. "
            "Le stop protège un gain, il ne juge pas la suite."
            ),
        kind="SORTIE_STOP",
        )


# ── orchestration ──────────────────────────────────────────────────────────────


def run_scan(
    rows: list[AssetMetrics],
    positions: list[Position],
    rules: Rules,
    history: dict[int, list[PriorScan]],
    profit_already_taken: set[int],
    refuge: Optional[AssetMetrics] = None,
    refuges_examined: Optional[list[dict]] = None,
    ) -> ScanResult:
    """Run every mechanism over every position and assemble the result.

    Parameters
    ----------
    rows : list[AssetMetrics]
        Metrics for the ranking and for every held asset. Scored here.
    positions : list[Position]
        Portfolio lines to arbitrate.
    rules : Rules
        Thresholds.
    history : dict[int, list[PriorScan]]
        Prior scans per product id, most recent first.
    profit_already_taken : set[int]
        Product ids whose stake has already been recovered once.
    refuge : AssetMetrics, optional
        Refuge retained for this scan, None when none is liquid enough.
    refuges_examined : list[dict], optional
        Every refuge considered, with why it was or was not retained.

    Returns
    -------
    ScanResult
        Ranking, regime, candidate and one outcome per position.
    """
    score_universe(rows, rules)
    by_id = {r.id: r for r in rows}

    held_ids = [p.coingecko_id for p in positions]
    candidate, discarded = select_candidate(rows, held_ids, rules)
    regime = evaluate_regime(rows, rules)
    refuge_ids = set(rules.refuge_ids())

    outcomes: list[PositionOutcome] = []

    for position in positions:
        row = by_id.get(position.coingecko_id)
        outcome = PositionOutcome(position=position, row=row)

        if row is None:
            outcome.arbitrated = False
            outcome.reason = (
                f"Actif « {position.coingecko_id} » introuvable sur CoinGecko. "
                "Corrige l'identifiant de marché de ce produit."
                )
            outcomes.append(outcome)
            continue

        outcome.current_value = position.current_value(row)
        outcome.arbitrable_value = position.arbitrable_value(row)
        outcome.gain_pct = position.gain_pct(row)

        if not position.arbitrated:
            outcome.arbitrated = False
            outcome.reason = "Ligne exclue de l'arbitrage à ta demande."
            outcomes.append(outcome)
            continue

        if outcome.arbitrable_value <= 0:
            outcome.arbitrated = False
            outcome.reason = (
                "Notionnel arbitrable nul : la réserve de frais couvre toute la ligne."
                )
            outcomes.append(outcome)
            continue

        position_history = history.get(position.product_id, [])
        stop = evaluate_trailing_stop(position, row, rules)
        profit = evaluate_profit_taking(
            position, row, rules, position.product_id in profit_already_taken
            )
        rotation = evaluate_rotation(position, row, candidate, rules, position_history, regime)

        if rotation.verdict is SignalVerdict.ROTATION:
            temporisation = Mechanism(
                applicable=False,
                reason="Une rotation passe les barrières : la temporisation n'est pas évaluée.",
                )
        elif position.coingecko_id in refuge_ids:
            temporisation = Mechanism(
                applicable=False,
                reason=f"Position déjà en refuge ({row.symbol}).",
                )
        elif not refuge_ids:
            temporisation = Mechanism(
                applicable=False,
                reason="La temporisation est désactivée ou aucun refuge n'est configuré.",
                )
        else:
            temporisation = evaluate_temporisation(
                position, row, rows, refuge, rules, position_history, regime
                )

        # Priority: the stop protects capital, so it outranks everything.
        # Recovering the stake outranks chasing another asset.
        if stop.verdict is SignalVerdict.SORTIE_STOP:
            verdict = SignalVerdict.SORTIE_STOP
            plan = stop_exit_plan(position, row, refuge, stop, rules)
        elif profit.verdict is SignalVerdict.ALLEGER:
            verdict = SignalVerdict.ALLEGER
            plan = trim_plan(position, row, refuge, profit, rules)
        elif rotation.verdict is SignalVerdict.ROTATION:
            verdict = SignalVerdict.ROTATION
            plan = rotation_plan(position, row, candidate, rules)
        elif temporisation.verdict is SignalVerdict.TEMPORISER:
            verdict = SignalVerdict.TEMPORISER
            plan = temporisation_plan(position, row, refuge, rules)
        else:
            verdict = SignalVerdict.CONSERVER
            plan = None

        outcome.verdict = verdict
        outcome.plan = plan
        outcome.rotation = rotation
        outcome.trailing_stop = stop
        outcome.profit_taking = profit
        outcome.temporisation = temporisation
        outcome.score_delta = rotation.extra.get("score_delta")
        outcome.round_trip_cost_pct = rotation.extra.get("round_trip_cost_pct")
        outcome.required_edge_pct = rotation.extra.get("required_edge_pct")
        outcome.streak_weeks = int(rotation.extra.get("streak_weeks", 0) or 0)
        outcome.rotation_gates_but_persistence = bool(
            rotation.extra.get("all_gates_but_persistence", False)
            )
        outcome.temporisation_gates_but_persistence = bool(
            temporisation.extra.get("all_gates_but_persistence", False)
            )
        outcomes.append(outcome)

    global_verdict = max(
        (o.verdict for o in outcomes),
        key=lambda v: _VERDICT_PRIORITY[v],
        default=SignalVerdict.CONSERVER,
        )

    stale = [r.symbol for r in rows if r.sample_days < rules.signal.slow_window_days]

    return ScanResult(
        verdict=global_verdict,
        regime=regime,
        candidate=candidate,
        discarded_candidates=discarded,
        ranking=rows,
        positions=outcomes,
        refuge=refuge,
        refuges_examined=refuges_examined or [],
        insufficient_history=stale,
        quote_currency=rules.quote_currency,
        )


def investable(rows: Iterable[AssetMetrics]) -> list[AssetMetrics]:
    """Drop stablecoins and wrapped assets from a ranking."""
    return [r for r in rows if r.id not in EXCLUDED_IDS]
