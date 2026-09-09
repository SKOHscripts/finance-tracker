"""Loading and validation of the signal thresholds.

The thresholds live in a TOML file rather than in the code so a user can change
what the engine does without editing Python, and so a change to the rules shows
up as its own diff. The file holds *only* rules: no position, no amount, no
address. Everything about the portfolio comes from the database.

Frozen dataclasses rather than raw dicts, because a typo in a threshold name
should fail at load time with a usable message, not three functions later as a
KeyError inside a gate.
"""
import tomllib
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Optional

from finance_tracker.config import SIGNAL_RULES_PATH

# Stablecoins and wrapped assets, excluded from the investable ranking. A peg
# has no momentum to exploit, and a wrapper is the underlying asset a second
# time — keeping either would let the ranking recommend a position the user
# already holds under another name.
EXCLUDED_IDS: frozenset[str] = frozenset({
    "tether", "usd-coin", "dai", "first-digital-usd", "ethena-usde",
    "usds", "paypal-usd", "binance-peg-busd", "tether-gold", "pax-gold",
    "wrapped-bitcoin", "wrapped-steth", "staked-ether", "weth",
    "wrapped-eeth", "coinbase-wrapped-btc", "binance-staked-sol",
    "jito-staked-sol", "rocket-pool-eth", "wbnb", "wrapped-beacon-eth",
    "lombard-staked-btc", "solv-btc", "susds", "ethena-staked-usde",
    })

# The free CoinGecko plan serves 365 days of history. Asking for more returns
# less, not more, so every lookback is capped below it.
MAX_LOOKBACK_DAYS = 360


class RulesError(ValueError):
    """Raised when the rules file is missing, malformed, or incoherent."""


@dataclass(frozen=True)
class UniverseRules:
    """Which assets get ranked, and how fast they may be fetched."""

    top_n: int = 10
    quote_currency: str = "eur"
    request_delay_seconds: float = 2.5


@dataclass(frozen=True)
class SignalRules:
    """Weights of the composite score.

    Volatility is subtracted, not added: two assets with the same momentum are
    separated by which one got there more calmly.
    """

    fast_window_days: int = 30
    slow_window_days: int = 90
    weight_slow_momentum: float = 0.5
    weight_fast_momentum: float = 0.3
    weight_volatility: float = 0.2


@dataclass(frozen=True)
class CostRules:
    """What moving a position actually costs.

    Percentages are per leg; ``network_fees_total`` is a flat amount covering
    a round trip. The flat part is the whole reason a small line is harder to
    justify moving than a large one.
    """

    swap_spread_pct: float = 1.5
    provider_fee_pct: float = 0.5
    network_fees_total: float = 11.0
    max_extra_slippage_pct: float = 1.0

    def round_trip_pct(self, notional: float) -> float:
        """Cost of a two-leg move, as a percentage of *notional*.

        Parameters
        ----------
        notional : float
            Value being moved, in the quote currency.

        Returns
        -------
        float
            Percentage cost, or infinity for a non-positive notional — which
            makes every cost gate fail rather than divide by zero.
        """
        if notional <= 0:
            return float("inf")
        return 2 * (self.swap_spread_pct + self.provider_fee_pct) + \
            self.network_fees_total / notional * 100.0

    def one_way_pct(self, notional: float) -> float:
        """Cost of a single leg, as a percentage of *notional*.

        A move to a refuge does not come back, so it carries one leg's fees
        and half the flat network cost.
        """
        if notional <= 0:
            return float("inf")
        return self.swap_spread_pct + self.provider_fee_pct + \
            self.network_fees_total / 2 / notional * 100.0

    def worst_case_pct(self) -> float:
        """Worst acceptable loss on one leg, quote included and slipped.

        Used to set the minimum number of units worth accepting before a swap
        is called off.
        """
        return self.swap_spread_pct + self.provider_fee_pct + self.max_extra_slippage_pct


@dataclass(frozen=True)
class GateRules:
    """The six rotation barriers. All must pass for a move to be proposed."""

    min_score_delta: float = 1.5
    cost_margin_multiple: float = 2.0
    max_candidate_vol_pct: float = 110.0
    max_candidate_drawdown_pct: float = 45.0
    min_volume_24h: float = 275_000_000.0
    required_consecutive_weeks: int = 3
    use_fallback_candidate: bool = True


@dataclass(frozen=True)
class RegimeRules:
    """Two independent readings of the market's observed state."""

    enabled: bool = True
    reference_id: str = "bitcoin"
    long_average_days: int = 200
    min_breadth_pct: float = 50.0


@dataclass(frozen=True)
class TemporisationRules:
    """Barriers for a one-way exit into a stablecoin refuge."""

    enabled: bool = True
    refuges: tuple[str, ...] = ("usd-coin", "tether", "dai")
    max_held_slow_momentum_pct: float = -12.0
    min_held_drawdown_pct: float = 30.0
    min_bearish_share_pct: float = 60.0
    cost_margin_multiple: float = 1.5
    required_consecutive_weeks: int = 2


@dataclass(frozen=True)
class ProfitTakingRules:
    """Recovering the stake once, then letting the rest run."""

    enabled: bool = True
    trigger_gain_pct: float = 100.0
    max_fraction: float = 0.60
    min_notional: float = 250.0
    once_only: bool = True


@dataclass(frozen=True)
class TrailingStopRules:
    """Full exit when a winning line gives back too much of its peak."""

    enabled: bool = True
    max_drawdown_pct: float = 30.0
    window_days: int = 180
    min_gain_pct: float = 0.0


@dataclass(frozen=True)
class RouteRules:
    """Providers worth quoting. The engine quotes nothing; it reminds."""

    providers_to_quote: tuple[str, ...] = ()
    atomic_swap_note: str = ""
    stable_providers_to_quote: tuple[str, ...] = ()
    stable_note: str = ""


@dataclass(frozen=True)
class Rules:
    """Every threshold the engine reads, validated and typed."""

    universe: UniverseRules = field(default_factory=UniverseRules)
    signal: SignalRules = field(default_factory=SignalRules)
    costs: CostRules = field(default_factory=CostRules)
    gates: GateRules = field(default_factory=GateRules)
    regime: RegimeRules = field(default_factory=RegimeRules)
    temporisation: TemporisationRules = field(default_factory=TemporisationRules)
    profit_taking: ProfitTakingRules = field(default_factory=ProfitTakingRules)
    trailing_stop: TrailingStopRules = field(default_factory=TrailingStopRules)
    routes: RouteRules = field(default_factory=RouteRules)

    @property
    def quote_currency(self) -> str:
        """Upper-case currency code every figure is denominated in."""
        return self.universe.quote_currency.upper()

    def lookback_days(self) -> int:
        """History depth to request, deep enough for every active mechanism.

        Returns
        -------
        int
            Days of history, capped at ``MAX_LOOKBACK_DAYS`` because the free
            CoinGecko plan serves no more than a year.
        """
        needs = [self.signal.slow_window_days, 90]
        if self.regime.enabled:
            needs.append(self.regime.long_average_days)
        if self.trailing_stop.enabled:
            needs.append(self.trailing_stop.window_days)
        return min(max(needs) + 5, MAX_LOOKBACK_DAYS)

    def refuge_ids(self) -> tuple[str, ...]:
        """Refuge identifiers in preference order, empty when disabled."""
        return self.temporisation.refuges if self.temporisation.enabled else ()


def _section(raw: dict, name: str) -> dict:
    """Return section *name* from *raw*, or an empty dict when absent."""
    value = raw.get(name, {})
    if not isinstance(value, dict):
        raise RulesError(f"La section [{name}] doit être une table TOML.")
    return value


def _build(cls, data: dict, section: str, **overrides):
    """Instantiate a rules dataclass from a TOML section.

    Unknown keys are rejected rather than ignored: a misspelt threshold that
    silently keeps its default is the kind of bug that only shows up as a
    verdict nobody can explain.

    Parameters
    ----------
    cls : type
        The dataclass to build.
    data : dict
        The TOML section.
    section : str
        Section name, used in error messages.
    **overrides
        Values computed by the caller, bypassing *data*.

    Returns
    -------
    Any
        An instance of *cls*.

    Raises
    ------
    RulesError
        If *data* holds a key the dataclass does not define.
    """
    known = {f.name for f in cls.__dataclass_fields__.values()}
    unknown = set(data) - known - set(overrides)
    if unknown:
        raise RulesError(
            f"Clé inconnue dans [{section}] de la configuration : "
            f"{', '.join(sorted(unknown))}. "
            f"Clés acceptées : {', '.join(sorted(known))}."
            )
    kwargs = {k: v for k, v in data.items() if k in known}
    kwargs.update(overrides)
    try:
        return cls(**kwargs)
    except TypeError as exc:
        raise RulesError(f"Section [{section}] invalide : {exc}") from exc


def parse_rules(raw: dict) -> Rules:
    """Turn a decoded TOML mapping into a validated :class:`Rules`.

    Parameters
    ----------
    raw : dict
        Mapping as returned by ``tomllib``.

    Returns
    -------
    Rules
        Validated thresholds.

    Raises
    ------
    RulesError
        On an unknown key, a wrong type, or an incoherent combination.
    """
    routes_raw = _section(raw, "routes")
    stable_raw = routes_raw.get("stable", {})

    rules = Rules(
        universe=_build(UniverseRules, _section(raw, "universe"), "universe"),
        signal=_build(SignalRules, _section(raw, "signal"), "signal"),
        costs=_build(CostRules, _section(raw, "costs"), "costs"),
        gates=_build(GateRules, _section(raw, "gates"), "gates"),
        regime=_build(RegimeRules, _section(raw, "regime"), "regime"),
        temporisation=_build(
            TemporisationRules,
            {k: v for k, v in _section(raw, "temporisation").items() if k != "refuges"},
            "temporisation",
            refuges=tuple(_section(raw, "temporisation").get(
                "refuges", TemporisationRules.refuges)),
            ),
        profit_taking=_build(ProfitTakingRules, _section(raw, "profit_taking"), "profit_taking"),
        trailing_stop=_build(TrailingStopRules, _section(raw, "trailing_stop"), "trailing_stop"),
        routes=RouteRules(
            providers_to_quote=tuple(routes_raw.get("providers_to_quote", ())),
            atomic_swap_note=str(routes_raw.get("atomic_swap_note", "")),
            stable_providers_to_quote=tuple(
                stable_raw.get("providers_to_quote", routes_raw.get("providers_to_quote", ()))),
            stable_note=str(stable_raw.get("note", "")),
            ),
        )
    _validate(rules)
    return rules


def _validate(rules: Rules) -> None:
    """Reject threshold combinations the engine cannot act on.

    Raises
    ------
    RulesError
        With a message naming the offending setting.
    """
    if rules.universe.top_n < 2:
        raise RulesError("universe.top_n doit valoir au moins 2 pour qu'un classement existe.")
    if rules.signal.fast_window_days >= rules.signal.slow_window_days:
        raise RulesError(
            "signal.fast_window_days doit être strictement inférieur à "
            "signal.slow_window_days : sans deux horizons distincts, le score "
            "compte deux fois la même mesure."
            )
    if rules.gates.required_consecutive_weeks < 1:
        raise RulesError("gates.required_consecutive_weeks doit valoir au moins 1.")
    if rules.temporisation.required_consecutive_weeks < 1:
        raise RulesError("temporisation.required_consecutive_weeks doit valoir au moins 1.")
    if not 0 < rules.profit_taking.max_fraction <= 1:
        raise RulesError(
            "profit_taking.max_fraction doit être strictement entre 0 et 1 : "
            "ce mécanisme récupère la mise, il ne liquide pas la ligne."
            )
    if rules.temporisation.enabled and not rules.temporisation.refuges:
        raise RulesError(
            "temporisation.enabled est vrai mais aucun refuge n'est déclaré : "
            "renseigne temporisation.refuges ou désactive la temporisation."
            )
    if rules.temporisation.max_held_slow_momentum_pct > 0:
        raise RulesError(
            "temporisation.max_held_slow_momentum_pct décrit une dégradation : "
            "il doit être négatif ou nul."
            )
    if rules.trailing_stop.max_drawdown_pct <= 0:
        raise RulesError("trailing_stop.max_drawdown_pct doit être strictement positif.")


def load_rules(path: Optional[Path] = None) -> Rules:
    """Read and validate the rules file.

    Parameters
    ----------
    path : Path, optional
        File to read. Defaults to the packaged ``config/signal_rules.toml``.

    Returns
    -------
    Rules
        Validated thresholds.

    Raises
    ------
    RulesError
        If the file is missing, is not valid TOML, or fails validation.
    """
    target = Path(path) if path else SIGNAL_RULES_PATH
    if not target.exists():
        raise RulesError(
            f"Fichier de règles introuvable : {target}. "
            "Il fait partie du dépôt ; restaure-le ou passe un chemin explicite."
            )
    try:
        with open(target, "rb") as handle:
            raw: dict[str, Any] = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise RulesError(f"TOML invalide dans {target} : {exc}") from exc
    return parse_rules(raw)


def with_overrides(rules: Rules, **sections) -> Rules:
    """Return a copy of *rules* with whole sections replaced.

    Used by tests and by the settings page, which lets a user tighten a
    threshold for one scan without editing the file.

    Parameters
    ----------
    rules : Rules
        Base thresholds.
    **sections
        Section name to replacement dataclass.

    Returns
    -------
    Rules
        A new instance; *rules* is untouched.
    """
    return replace(rules, **sections)
