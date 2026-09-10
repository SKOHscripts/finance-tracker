"""Retrospective price metrics.

Pure functions over a series of daily closes, oldest first. Every one of them
describes something that already happened — a return, a dispersion, a decline
from a peak. None of them says anything about what comes next, and the report
built on top of them has to read the same way.

Each returns None rather than a wrong number when the history is too short.
That distinction matters downstream: a gate handed None fails, it does not
silently pass on a zero.
"""
import math
import statistics
from datetime import datetime, timezone
from typing import Optional, Sequence

# A standard deviation over fewer than ten observations is noise. Below this
# many usable log-returns, volatility is reported as unknown.
MIN_VOL_OBSERVATIONS = 10

# A z-score needs a population to mean anything. Under three peers, every asset
# scores zero and the ranking carries no information.
MIN_ZSCORE_POPULATION = 3


def daily_closes(prices: Sequence[Sequence[float]]) -> list[float]:
    """Reduce a CoinGecko price series to one close per UTC day.

    CoinGecko returns ``[[timestamp_ms, price], ...]`` at an interval that
    varies with the requested range. Collapsing to one point per UTC day makes
    every window below mean the same thing whatever the API returned.

    Parameters
    ----------
    prices : Sequence[Sequence[float]]
        Pairs of millisecond timestamp and price, in any order.

    Returns
    -------
    list[float]
        One close per day, ordered oldest first. The last sample of a day wins.
    """
    by_day: dict = {}
    for ts_ms, price in prices:
        day = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).date()
        by_day[day] = price
    return [by_day[d] for d in sorted(by_day)]


def pct_return(series: Sequence[float], days: int) -> Optional[float]:
    """Percentage change over the last *days* closes.

    Parameters
    ----------
    series : Sequence[float]
        Daily closes, oldest first.
    days : int
        Length of the window, in days.

    Returns
    -------
    float or None
        The change in percent, or None when the history is shorter than the
        window or the starting price is not positive.
    """
    if len(series) < days + 1:
        return None
    past, now = series[-(days + 1)], series[-1]
    if past <= 0:
        return None
    return (now / past - 1.0) * 100.0


def annualised_vol(series: Sequence[float], days: int) -> Optional[float]:
    """Annualised standard deviation of daily log-returns, in percent.

    Parameters
    ----------
    series : Sequence[float]
        Daily closes, oldest first.
    days : int
        Length of the window, in days.

    Returns
    -------
    float or None
        Annualised volatility in percent, or None when fewer than
        ``MIN_VOL_OBSERVATIONS`` usable returns are available.
    """
    window = list(series[-(days + 1):])
    if len(window) < MIN_VOL_OBSERVATIONS:
        return None
    logs = [
        math.log(window[i] / window[i - 1])
        for i in range(1, len(window))
        if window[i - 1] > 0 and window[i] > 0
        ]
    if len(logs) < MIN_VOL_OBSERVATIONS:
        return None
    return statistics.stdev(logs) * math.sqrt(365) * 100.0


def max_drawdown(series: Sequence[float], days: int) -> Optional[float]:
    """Worst peak-to-trough decline within the window, in percent.

    Parameters
    ----------
    series : Sequence[float]
        Daily closes, oldest first.
    days : int
        Length of the window, in days.

    Returns
    -------
    float or None
        A negative percentage, 0.0 for a series that only ever rose, or None
        when the window holds fewer than two closes.
    """
    window = list(series[-(days + 1):])
    if len(window) < 2:
        return None
    peak, worst = window[0], 0.0
    for price in window:
        peak = max(peak, price)
        if peak > 0:
            worst = min(worst, (price / peak - 1.0) * 100.0)
    return worst


def dist_from_high(series: Sequence[float], days: int) -> Optional[float]:
    """Distance from the highest close of the window, in percent.

    Unlike :func:`max_drawdown`, this measures where the price stands *now*
    relative to the peak, which is what a trailing stop acts on.

    Parameters
    ----------
    series : Sequence[float]
        Daily closes, oldest first.
    days : int
        Length of the window, in days.

    Returns
    -------
    float or None
        A percentage at or below zero, or None on an empty or non-positive
        window.
    """
    window = list(series[-(days + 1):])
    if not window:
        return None
    high = max(window)
    return (window[-1] / high - 1.0) * 100.0 if high > 0 else None


def moving_average(series: Sequence[float], days: int) -> Optional[float]:
    """Mean of the last *days* closes, or None when history is too short.

    Parameters
    ----------
    series : Sequence[float]
        Daily closes, oldest first.
    days : int
        Number of closes to average.

    Returns
    -------
    float or None
        The mean, or None when fewer than *days* closes are available. The
        None matters: a 200-day average computed over 60 days would read as a
        regime signal while being nothing of the sort.
    """
    if len(series) < days:
        return None
    return statistics.fmean(series[-days:])


def zscore(value: Optional[float], population: Sequence[Optional[float]]) -> float:
    """Standard score of *value* within *population*, ignoring None entries.

    Parameters
    ----------
    value : float or None
        The observation to score.
    population : Sequence[float or None]
        Peer observations. None entries are dropped.

    Returns
    -------
    float
        The z-score, or 0.0 when the value is unknown, the population is too
        small to be meaningful, or every peer is identical. Zero is the
        neutral score: it neither favours nor penalises the asset.
    """
    clean = [v for v in population if v is not None]
    if value is None or len(clean) < MIN_ZSCORE_POPULATION:
        return 0.0
    mean = statistics.fmean(clean)
    sd = statistics.pstdev(clean)
    return 0.0 if sd == 0 else (value - mean) / sd
