"""User-adjustable rotation thresholds.

The thresholds ship in `config/signal_rules.toml`, which is public, versioned
and the same for everyone. That is right for a default and wrong for a setting:
a hosted app has no writable copy of the file per user, and even locally,
editing a repository file to change how the engine behaves means a change no
backup carries and a merge conflict on the next pull.

So the file stays the source of defaults and the database holds *deviations*:
a row exists only for a threshold the user moved. Two consequences, both
deliberate:

- A user who never touched a threshold picks up an improved default on the
  next release. A stored full copy would freeze them on today's figures and
  they would never learn the default had changed.
- A user who deliberately tightened a barrier keeps their figure through every
  release, and can see at a glance which figures are theirs.

Every parameter here carries a sentence saying what it does. That is not
documentation politeness: a threshold whose role the user cannot state is a
threshold they cannot set responsibly, and the whole point of exposing these is
that the arbitrage stays theirs rather than the engine's.
"""
from dataclasses import dataclass, fields, replace
from typing import Any, Optional

from sqlalchemy import select
from sqlmodel import Session

from finance_tracker.domain.models import SignalSetting

from .rules import Rules, RulesError, load_rules

# Sections of `Rules` that hold adjustable settings, in the order the interface
# shows them: what gets ranked, how it is scored, what a move costs, then each
# mechanism that can act on a position.
SECTION_ORDER: tuple[str, ...] = (
    "universe", "signal", "costs", "gates",
    "regime", "temporisation", "profit_taking", "trailing_stop",
    )


class SettingsError(ValueError):
    """Raised when a value cannot be read, or would make the engine incoherent.

    A ValueError subclass so the view catches one type and shows the message,
    which is written for the user.
    """


@dataclass(frozen=True)
class Parameter:
    """One adjustable threshold, and what the interface needs to show it.

    Parameters
    ----------
    section : str
        Name of the `Rules` section holding it, e.g. ``"gates"``.
    field : str
        Field name inside that section.
    kind : str
        ``"int"``, ``"float"`` or ``"bool"`` — how the value is read back.
    minimum, maximum : float, optional
        Bounds the interface enforces before the engine's own coherence
        checks run. They stop a typo, not a bad idea.
    step : float, optional
        Increment for the numeric input.
    unit : str
        Suffix shown after the figure (``"%"``, ``"j"``, ``"€"``, …). Display
        only; it never scales the value.
    """

    section: str
    field: str
    kind: str = "float"
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    step: Optional[float] = None
    unit: str = ""

    @property
    def key(self) -> str:
        """Dotted path, as stored in the database."""
        return f"{self.section}.{self.field}"

    @property
    def label_key(self) -> str:
        """Translation key of the short label."""
        return f"param.{self.key}"

    @property
    def help_key(self) -> str:
        """Translation key of the sentence stating what the setting does."""
        return f"paramhelp.{self.key}"


# Every threshold a user may move, with its bounds. Text settings are absent on
# purpose: the quote currency, the regime's reference asset, the refuge list
# and the providers to quote are identifiers and prose, not thresholds, and a
# mistyped identifier only reveals itself at the next scan.
PARAMETERS: tuple[Parameter, ...] = (
    # ── universe ──────────────────────────────────────────────────────────────
    Parameter("universe", "top_n", "int", 2, 50, 1),
    Parameter("universe", "request_delay_seconds", "float", 0.0, 30.0, 0.5, "s"),
    # ── signal ────────────────────────────────────────────────────────────────
    Parameter("signal", "fast_window_days", "int", 5, 180, 1, "j"),
    Parameter("signal", "slow_window_days", "int", 10, 360, 1, "j"),
    Parameter("signal", "weight_slow_momentum", "float", 0.0, 2.0, 0.05),
    Parameter("signal", "weight_fast_momentum", "float", 0.0, 2.0, 0.05),
    Parameter("signal", "weight_volatility", "float", 0.0, 2.0, 0.05),
    # ── costs ─────────────────────────────────────────────────────────────────
    Parameter("costs", "swap_spread_pct", "float", 0.0, 20.0, 0.1, "%"),
    Parameter("costs", "provider_fee_pct", "float", 0.0, 20.0, 0.1, "%"),
    Parameter("costs", "network_fees_total", "float", 0.0, 500.0, 1.0, "€"),
    Parameter("costs", "max_extra_slippage_pct", "float", 0.0, 20.0, 0.1, "%"),
    # ── gates ─────────────────────────────────────────────────────────────────
    Parameter("gates", "min_score_delta", "float", 0.0, 10.0, 0.1, "σ"),
    Parameter("gates", "cost_margin_multiple", "float", 1.0, 10.0, 0.1, "×"),
    Parameter("gates", "max_candidate_vol_pct", "float", 10.0, 500.0, 5.0, "%"),
    Parameter("gates", "max_candidate_drawdown_pct", "float", 5.0, 95.0, 5.0, "%"),
    Parameter("gates", "min_volume_24h", "float", 0.0, 5e9, 1e7, "€"),
    Parameter("gates", "required_consecutive_weeks", "int", 1, 12, 1),
    Parameter("gates", "use_fallback_candidate", "bool"),
    # ── regime ────────────────────────────────────────────────────────────────
    Parameter("regime", "enabled", "bool"),
    Parameter("regime", "long_average_days", "int", 20, 360, 10, "j"),
    Parameter("regime", "min_breadth_pct", "float", 0.0, 100.0, 5.0, "%"),
    # ── temporisation ─────────────────────────────────────────────────────────
    Parameter("temporisation", "enabled", "bool"),
    Parameter("temporisation", "max_held_slow_momentum_pct", "float", -100.0, 0.0, 1.0, "%"),
    Parameter("temporisation", "min_held_drawdown_pct", "float", 0.0, 95.0, 5.0, "%"),
    Parameter("temporisation", "min_bearish_share_pct", "float", 0.0, 100.0, 5.0, "%"),
    Parameter("temporisation", "cost_margin_multiple", "float", 1.0, 10.0, 0.1, "×"),
    Parameter("temporisation", "required_consecutive_weeks", "int", 1, 12, 1),
    # ── profit_taking ─────────────────────────────────────────────────────────
    Parameter("profit_taking", "enabled", "bool"),
    Parameter("profit_taking", "trigger_gain_pct", "float", 10.0, 1000.0, 10.0, "%"),
    Parameter("profit_taking", "max_fraction", "float", 0.05, 1.0, 0.05),
    Parameter("profit_taking", "min_notional", "float", 0.0, 10000.0, 50.0, "€"),
    Parameter("profit_taking", "once_only", "bool"),
    # ── trailing_stop ─────────────────────────────────────────────────────────
    Parameter("trailing_stop", "enabled", "bool"),
    Parameter("trailing_stop", "max_drawdown_pct", "float", 1.0, 95.0, 1.0, "%"),
    Parameter("trailing_stop", "window_days", "int", 20, 360, 10, "j"),
    Parameter("trailing_stop", "min_gain_pct", "float", -50.0, 500.0, 5.0, "%"),
    )

_BY_KEY: dict[str, Parameter] = {p.key: p for p in PARAMETERS}


def parameter(key: str) -> Parameter:
    """Look one parameter up by its dotted key.

    Raises
    ------
    SettingsError
        When the key names no adjustable parameter — which is what a stale row
        from an older release looks like.
    """
    try:
        return _BY_KEY[key]
    except KeyError as exc:
        raise SettingsError(f"Paramètre inconnu : {key}.") from exc


def parameters_by_section() -> dict[str, tuple[Parameter, ...]]:
    """Parameters grouped by section, in display order."""
    return {
        section: tuple(p for p in PARAMETERS if p.section == section)
        for section in SECTION_ORDER
        }


def coerce(param: Parameter, raw: Any) -> Any:
    """Read a stored string back into the type the rules dataclass expects.

    Raises
    ------
    SettingsError
        When the text does not parse, naming the parameter rather than the
        offending characters — the user is looking at a form, not a file.
    """
    text = str(raw).strip()
    try:
        if param.kind == "bool":
            if text.lower() in ("true", "1", "yes", "oui"):
                return True
            if text.lower() in ("false", "0", "no", "non"):
                return False
            raise ValueError(text)
        if param.kind == "int":
            return int(float(text))
        return float(text)
    except (TypeError, ValueError) as exc:
        raise SettingsError(
            f"Valeur illisible pour {param.key} : « {raw} »."
            ) from exc


def serialise(param: Parameter, value: Any) -> str:
    """Render a value for storage."""
    if param.kind == "bool":
        return "true" if value else "false"
    return str(value)


def default_value(param: Parameter, defaults: Optional[Rules] = None) -> Any:
    """The shipped value of *param*, from the rules file."""
    base = defaults if defaults is not None else load_rules()
    return getattr(getattr(base, param.section), param.field)


def stored_overrides(session: Session) -> dict[str, str]:
    """Every deviation currently recorded, as raw text keyed by dotted path.

    Rows naming a parameter this release no longer has are dropped from the
    result rather than raising: a threshold removed upstream should not stop
    the page from loading.
    """
    rows = session.exec(select(SignalSetting)).scalars().all()
    return {r.key: r.value for r in rows if r.key in _BY_KEY}


def apply_overrides(base: Rules, overrides: dict[str, str]) -> Rules:
    """Return *base* with the given deviations applied.

    Parameters
    ----------
    base : Rules
        Shipped thresholds.
    overrides : dict
        Dotted key to raw text.

    Returns
    -------
    Rules
        A new instance; *base* is untouched.

    Raises
    ------
    SettingsError
        When a value cannot be read, or when the result is a combination the
        engine cannot act on — the message is the engine's own.
    """
    if not overrides:
        return base

    by_section: dict[str, dict[str, Any]] = {}
    for key, raw in overrides.items():
        param = parameter(key)
        by_section.setdefault(param.section, {})[param.field] = coerce(param, raw)

    updated = base
    for section, changes in by_section.items():
        updated = replace(updated, **{section: replace(getattr(base, section), **changes)})

    _revalidate(updated)
    return updated


def _revalidate(rules: Rules) -> None:
    """Run the engine's own coherence checks over adjusted thresholds.

    The checks live in :mod:`rules` and are reached by re-parsing, so a
    combination the file would reject is rejected here too. Without this a user
    could set a fast window longer than the slow one from the interface and get
    a verdict built on the same measurement counted twice.
    """
    try:
        # `_validate` is the module's own gate; calling it through parse_rules
        # would need a TOML round trip that adds nothing.
        from .rules import _validate  # pylint: disable=import-outside-toplevel
        _validate(rules)
    except RulesError as exc:
        raise SettingsError(str(exc)) from exc


def effective_rules(session: Session, defaults: Optional[Rules] = None) -> Rules:
    """The thresholds the engine should actually run with.

    Parameters
    ----------
    session : Session
        Open database session.
    defaults : Rules, optional
        Shipped thresholds; read from the file when omitted.

    Returns
    -------
    Rules
        Defaults with the user's deviations applied.

    Raises
    ------
    SettingsError
        When a stored deviation is unreadable or makes the set incoherent.
    """
    base = defaults if defaults is not None else load_rules()
    return apply_overrides(base, stored_overrides(session))


def set_setting(session: Session, key: str, value: Any, defaults: Optional[Rules] = None) -> bool:
    """Record one deviation, or drop it when it matches the shipped value.

    A single-value front door onto :func:`set_many`, so both go through exactly
    one validation path — a second copy of these checks is how the two would
    drift into disagreeing about what is allowed.

    Storing a deviation identical to the default would pin the user to today's
    figure and silently opt them out of a later improvement, so a value equal
    to the default clears the row instead of writing it.

    Parameters
    ----------
    session : Session
        Open database session. Committed here.
    key : str
        Dotted path of the parameter.
    value : Any
        The user's value, already typed or as text.
    defaults : Rules, optional
        Shipped thresholds, to compare against.

    Returns
    -------
    bool
        True when a deviation is now stored, False when the setting follows
        the default again.

    Raises
    ------
    SettingsError
        On an unreadable value, a value outside the parameter's bounds, or a
        combination the engine cannot act on. Nothing is written in that case.
    """
    return set_many(session, {key: value}, defaults) > 0


def set_many(
    session: Session, values: dict, defaults: Optional[Rules] = None
    ) -> int:
    """Record several deviations at once, all of them or none.

    A threshold is only ever right in relation to the others, so a section
    submitted as one form has to be accepted or refused as one. Writing them in
    a loop would leave a section half applied on the first refusal — a state
    the user never asked for and cannot see, and the harder half of it is that
    the fields *before* the bad one would look accepted.

    Parameters
    ----------
    session : Session
        Open database session. Committed here, once.
    values : dict
        Dotted key to the user's value.
    defaults : Rules, optional
        Shipped thresholds, to compare against.

    Returns
    -------
    int
        How many deviations are stored as a result — a value returned to its
        shipped figure drops its row and does not count.

    Raises
    ------
    SettingsError
        On an unreadable value, one outside its bounds, or a combination the
        engine cannot act on. Nothing is written in that case.
    """
    if not values:
        return 0

    base = defaults if defaults is not None else load_rules()

    typed = {}
    for key, value in values.items():
        param = parameter(key)
        coerced = coerce(param, value)

        if param.kind != "bool":
            if param.minimum is not None and coerced < param.minimum:
                raise SettingsError(f"{param.key} doit valoir au moins {param.minimum}.")
            if param.maximum is not None and coerced > param.maximum:
                raise SettingsError(f"{param.key} ne peut pas dépasser {param.maximum}.")

        typed[key] = coerced

    # Validate the whole set — existing deviations included — before touching a
    # single row. This is what makes the call atomic.
    candidate = dict(stored_overrides(session))
    for key, coerced in typed.items():
        param = parameter(key)
        if coerced == default_value(param, base):
            candidate.pop(key, None)
        else:
            candidate[key] = serialise(param, coerced)
    apply_overrides(base, candidate)

    existing = {
        r.key: r for r in session.exec(select(SignalSetting)).scalars().all()
        }
    stored = 0

    for key, coerced in typed.items():
        param = parameter(key)
        row = existing.get(key)

        if coerced == default_value(param, base):
            if row is not None:
                session.delete(row)
            continue

        if row is None:
            row = SignalSetting(key=key)
            session.add(row)
        row.value = serialise(param, coerced)
        stored += 1

    session.commit()
    return stored


def reset_setting(session: Session, key: str) -> None:
    """Return one setting to its shipped value."""
    parameter(key)  # refuse an unknown key rather than silently doing nothing
    row = session.exec(
        select(SignalSetting).where(SignalSetting.key == key)
        ).scalars().first()
    if row is not None:
        session.delete(row)
        session.commit()


def reset_all(session: Session) -> int:
    """Return every setting to its shipped value.

    Returns
    -------
    int
        How many deviations were dropped.
    """
    rows = session.exec(select(SignalSetting)).scalars().all()
    for row in rows:
        session.delete(row)
    if rows:
        session.commit()
    return len(rows)


def describe(session: Session, defaults: Optional[Rules] = None) -> list[dict]:
    """Every parameter with its current value, its default, and whether it moved.

    Returns
    -------
    list of dict
        One entry per parameter: ``param``, ``value``, ``default``,
        ``changed``.
    """
    base = defaults if defaults is not None else load_rules()
    try:
        current = effective_rules(session, base)
    except SettingsError:
        # A stored deviation has become incoherent — show the defaults rather
        # than refusing to draw the page the user needs in order to fix it.
        current = base

    rows = []
    for param in PARAMETERS:
        value = getattr(getattr(current, param.section), param.field)
        shipped = getattr(getattr(base, param.section), param.field)
        rows.append({
            "param": param,
            "value": value,
            "default": shipped,
            "changed": value != shipped,
            })
    return rows


def _known_sections() -> set[str]:
    """Section names `Rules` actually declares, for the registry's own check."""
    return {f.name for f in fields(Rules)}
