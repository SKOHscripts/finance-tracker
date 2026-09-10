"""Tests for the retrospective price metrics.

These functions decide whether a gate passes, so the cases that matter most are
the ones where the honest answer is "not enough data". A metric that returns a
plausible number from a too-short history is worse than one that returns None:
the gate would pass on a figure nobody could defend.
"""
# pylint: disable=redefined-outer-name  # pytest fixture pattern
import math

import pytest

from finance_tracker.services.crypto.metrics import (
    MIN_VOL_OBSERVATIONS,
    annualised_vol,
    daily_closes,
    dist_from_high,
    max_drawdown,
    moving_average,
    pct_return,
    zscore,
    )

# One day in milliseconds, for building synthetic CoinGecko series.
DAY_MS = 86_400_000
EPOCH_MS = 1_735_689_600_000  # 2025-01-01T00:00:00Z


def series(values, start_ms=EPOCH_MS, step_ms=DAY_MS):
    """Build a CoinGecko-shaped `[[timestamp, price], ...]` series."""
    return [[start_ms + i * step_ms, v] for i, v in enumerate(values)]


class TestDailyCloses:
    """Reducing an API series to one close per UTC day."""

    def test_one_point_per_day_passes_through(self):
        assert daily_closes(series([1.0, 2.0, 3.0])) == [1.0, 2.0, 3.0]

    def test_intraday_points_collapse_to_the_last_of_the_day(self):
        """Several samples in one day must yield one close, the latest."""
        hour = 3_600_000
        raw = [
            [EPOCH_MS, 10.0],
            [EPOCH_MS + hour, 11.0],
            [EPOCH_MS + 2 * hour, 12.0],
            [EPOCH_MS + DAY_MS, 20.0],
            ]
        assert daily_closes(raw) == [12.0, 20.0]

    def test_out_of_order_input_is_sorted_by_day(self):
        raw = [[EPOCH_MS + 2 * DAY_MS, 30.0], [EPOCH_MS, 10.0], [EPOCH_MS + DAY_MS, 20.0]]
        assert daily_closes(raw) == [10.0, 20.0, 30.0]

    def test_empty_input_gives_empty_output(self):
        assert daily_closes([]) == []


class TestPctReturn:
    """Percentage change over a window."""

    def test_simple_gain(self):
        assert pct_return([100.0, 110.0], 1) == pytest.approx(10.0)

    def test_simple_loss(self):
        assert pct_return([100.0, 75.0], 1) == pytest.approx(-25.0)

    def test_window_uses_the_right_starting_point(self):
        """A 2-day return must start two closes back, not at the series head."""
        assert pct_return([50.0, 100.0, 150.0], 2) == pytest.approx(200.0)
        assert pct_return([50.0, 100.0, 150.0], 1) == pytest.approx(50.0)

    def test_history_shorter_than_the_window_is_unknown(self):
        """None, never a number: a gate handed None fails rather than passing."""
        assert pct_return([100.0, 110.0], 5) is None

    def test_non_positive_start_is_unknown(self):
        assert pct_return([0.0, 110.0], 1) is None


class TestAnnualisedVol:
    """Annualised dispersion of daily log-returns."""

    def test_too_few_observations_is_unknown(self):
        short = [100.0 + i for i in range(MIN_VOL_OBSERVATIONS - 1)]
        assert annualised_vol(short, 30) is None

    def test_a_flat_series_has_zero_volatility(self):
        assert annualised_vol([100.0] * 40, 30) == pytest.approx(0.0)

    def test_a_noisier_series_scores_higher(self):
        calm = [100.0 * (1.001 ** i) for i in range(40)]
        wild = [100.0 * (1.05 if i % 2 else 0.95) ** i for i in range(40)]
        assert annualised_vol(wild, 30) > annualised_vol(calm, 30)

    def test_annualisation_uses_365_days(self):
        """The scale factor is calendar days: crypto trades every day."""
        alternating = [100.0, 110.0] * 20
        value = annualised_vol(alternating, 30)
        assert value is not None
        # Recomputed independently from the same definition.
        logs = [math.log(alternating[i] / alternating[i - 1]) for i in range(1, 31)]
        import statistics
        expected = statistics.stdev(logs) * math.sqrt(365) * 100.0
        assert value == pytest.approx(expected, rel=0.2)


class TestMaxDrawdown:
    """Worst peak-to-trough decline inside the window."""

    def test_a_rising_series_never_drew_down(self):
        assert max_drawdown([100.0, 110.0, 120.0], 3) == pytest.approx(0.0)

    def test_a_fall_from_the_peak_is_measured_from_the_peak(self):
        assert max_drawdown([100.0, 200.0, 100.0], 3) == pytest.approx(-50.0)

    def test_recovery_does_not_erase_the_drawdown(self):
        """The worst point stands even if the price came back."""
        assert max_drawdown([100.0, 200.0, 100.0, 200.0], 4) == pytest.approx(-50.0)

    def test_a_single_close_is_unknown(self):
        assert max_drawdown([100.0], 5) is None


class TestDistFromHigh:
    """Where the price stands now relative to the window's peak."""

    def test_at_the_high_is_zero(self):
        assert dist_from_high([100.0, 200.0], 2) == pytest.approx(0.0)

    def test_below_the_high_is_negative(self):
        assert dist_from_high([100.0, 200.0, 150.0], 3) == pytest.approx(-25.0)

    def test_differs_from_drawdown_after_a_recovery(self):
        """This is why the trailing stop uses this and not max drawdown."""
        prices = [100.0, 200.0, 100.0, 190.0]
        assert max_drawdown(prices, 4) == pytest.approx(-50.0)
        assert dist_from_high(prices, 4) == pytest.approx(-5.0)

    def test_empty_window_is_unknown(self):
        assert dist_from_high([], 5) is None


class TestMovingAverage:
    """Long average, used only by the regime reading."""

    def test_mean_of_the_window(self):
        assert moving_average([10.0, 20.0, 30.0], 3) == pytest.approx(20.0)

    def test_uses_only_the_last_n_closes(self):
        assert moving_average([0.0, 10.0, 20.0, 30.0], 3) == pytest.approx(20.0)

    def test_too_short_history_is_unknown(self):
        """A 200-day average over 60 days would read as a regime signal."""
        assert moving_average([100.0] * 60, 200) is None


class TestZscore:
    """Standard score within the ranking of the day."""

    def test_the_mean_scores_zero(self):
        assert zscore(20.0, [10.0, 20.0, 30.0]) == pytest.approx(0.0)

    def test_above_the_mean_scores_positive(self):
        assert zscore(30.0, [10.0, 20.0, 30.0]) > 0

    def test_unknown_value_scores_neutral(self):
        """Zero neither favours nor penalises the asset."""
        assert zscore(None, [10.0, 20.0, 30.0]) == 0.0

    def test_population_too_small_scores_neutral(self):
        assert zscore(10.0, [10.0, 20.0]) == 0.0

    def test_identical_population_scores_neutral(self):
        """Zero spread would divide by zero; neutral is the honest answer."""
        assert zscore(10.0, [10.0, 10.0, 10.0]) == 0.0

    def test_none_entries_are_dropped_from_the_population(self):
        with_gaps = zscore(30.0, [10.0, None, 20.0, 30.0, None])
        without = zscore(30.0, [10.0, 20.0, 30.0])
        assert with_gaps == pytest.approx(without)
