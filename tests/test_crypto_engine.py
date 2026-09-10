"""Tests for the rotation engine.

The engine's job is to refuse most of the time. So most of these tests check
that a barrier holds — that a move is *not* proposed — because a false rotation
costs two legs of fees, and a false stop exit sells a position that was fine.

The priority order between mechanisms gets its own section: it encodes a
judgement (protect capital, then bank the stake, then chase) that a refactor
could quietly invert without any single gate looking wrong.
"""
# pylint: disable=redefined-outer-name  # pytest fixture pattern
import pytest

from finance_tracker.domain.enums import MarketRegime, SignalVerdict
from finance_tracker.services.crypto.engine import (
    AssetMetrics,
    Position,
    PriorScan,
    candidate_filters,
    evaluate_profit_taking,
    evaluate_regime,
    evaluate_rotation,
    evaluate_temporisation,
    evaluate_trailing_stop,
    investable,
    run_scan,
    score_universe,
    select_candidate,
    )
from finance_tracker.services.crypto.rules import (
    GateRules,
    ProfitTakingRules,
    RegimeRules,
    Rules,
    TemporisationRules,
    TrailingStopRules,
    load_rules,
    with_overrides,
    )


@pytest.fixture()
def rules():
    """The shipped thresholds, so tests exercise real defaults."""
    return load_rules()


def asset(coin_id, symbol, *, ret_slow=10.0, ret_fast=None, vol=50.0, dd=-15.0,
          volume=1e9, price=100.0, dist_high=-5.0, long_avg=90.0, sample=300):
    """Build a plausible ranked asset, overriding only what a test cares about."""
    return AssetMetrics(
        id=coin_id,
        symbol=symbol,
        name=symbol,
        price=price,
        volume_24h=volume,
        ret_slow=ret_slow,
        ret_fast=ret_slow if ret_fast is None else ret_fast,
        vol_30d=vol,
        max_dd_90d=dd,
        dist_high_90d=dist_high,
        dist_high_stop=dist_high,
        long_average=long_avg,
        sample_days=sample,
        )


def position(**kwargs):
    """A held line with sensible defaults: 10 units at 100, so 1000 EUR."""
    defaults = {
        "product_id": 1,
        "coingecko_id": "monero",
        "symbol": "XMR",
        "units": 10.0,
        "cost_basis_eur": 500.0,
        }
    return Position(**{**defaults, **kwargs})


class TestPositionValuation:
    """How a line's value and gain are derived."""

    def test_units_times_price_wins_over_a_stored_amount(self):
        """Units revalue at today's price; a stored figure is frozen."""
        held = asset("monero", "XMR", price=250.0)
        pos = position(units=4.0, notional_eur=1.0)
        assert pos.current_value(held) == pytest.approx(1000.0)

    def test_stored_amount_is_the_fallback_without_units(self):
        held = asset("monero", "XMR", price=250.0)
        assert position(units=None, notional_eur=800.0).current_value(held) == 800.0

    def test_gas_reserve_is_withheld_from_what_can_move(self):
        held = asset("monero", "XMR", price=100.0)
        pos = position(units=10.0, gas_reserve_eur=300.0)
        assert pos.current_value(held) == pytest.approx(1000.0)
        assert pos.arbitrable_value(held) == pytest.approx(700.0)

    def test_a_reserve_larger_than_the_line_leaves_nothing(self):
        held = asset("monero", "XMR", price=100.0)
        pos = position(units=1.0, gas_reserve_eur=500.0)
        assert pos.arbitrable_value(held) == 0.0

    def test_gain_is_unknown_without_a_cost_basis(self):
        held = asset("monero", "XMR", price=100.0)
        assert position(cost_basis_eur=None).gain_pct(held) is None

    def test_gain_against_the_cost_basis(self):
        held = asset("monero", "XMR", price=100.0)
        assert position(units=10.0, cost_basis_eur=500.0).gain_pct(held) == pytest.approx(100.0)


class TestScoringAndCandidate:
    """Ranking, and which asset the portfolio is arbitrated against."""

    def test_volatility_is_penalised_at_equal_momentum(self, rules):
        rows = [
            asset("a", "A", ret_slow=50.0, vol=30.0),
            asset("b", "B", ret_slow=50.0, vol=120.0),
            asset("c", "C", ret_slow=10.0, vol=60.0),
            ]
        score_universe(rows, rules)
        assert rows[0].id == "a"

    def test_ranking_is_sorted_best_first(self, rules):
        rows = [
            asset("low", "LOW", ret_slow=-20.0),
            asset("high", "HIGH", ret_slow=80.0),
            asset("mid", "MID", ret_slow=10.0),
            ]
        score_universe(rows, rules)
        assert [r.id for r in rows] == ["high", "mid", "low"]

    def test_a_held_asset_cannot_be_its_own_candidate(self, rules):
        rows = [asset("a", "A", ret_slow=80.0), asset("b", "B", ret_slow=10.0)]
        score_universe(rows, rules)
        candidate, _ = select_candidate(rows, ["a"], rules)
        assert candidate.id == "b"

    def test_fallback_walks_past_an_ineligible_leader(self, rules):
        """Without this, a very volatile leader blocks rotation every week."""
        rows = [
            asset("wild", "WILD", ret_slow=90.0, vol=250.0),
            asset("calm", "CALM", ret_slow=40.0, vol=45.0),
            ]
        score_universe(rows, rules)
        candidate, discarded = select_candidate(rows, [], rules)
        assert candidate.id == "calm"
        assert [d["id"] for d in discarded] == ["wild"]
        assert "volatilité" in discarded[0]["reasons"][0]

    def test_fallback_can_be_switched_off(self, rules):
        rows = [
            asset("wild", "WILD", ret_slow=90.0, vol=250.0),
            asset("calm", "CALM", ret_slow=40.0, vol=45.0),
            ]
        score_universe(rows, rules)
        strict = with_overrides(rules, gates=GateRules(use_fallback_candidate=False))
        candidate, discarded = select_candidate(rows, [], strict)
        assert candidate.id == "wild"
        assert not discarded

    def test_no_candidate_when_everything_is_held(self, rules):
        rows = [asset("a", "A"), asset("b", "B")]
        candidate, _ = select_candidate(rows, ["a", "b"], rules)
        assert candidate is None

    def test_illiquid_asset_fails_the_intrinsic_filters(self, rules):
        failures = candidate_filters(asset("x", "X", volume=1_000_000), rules)
        assert any("volume" in f for f in failures)

    def test_unknown_metrics_fail_rather_than_pass(self, rules):
        """A missing figure must never be read as a satisfied threshold."""
        blank = AssetMetrics(id="x", symbol="X", volume_24h=1e9)
        failures = candidate_filters(blank, rules)
        assert any("inconnue" in f for f in failures)
        assert any("inconnu" in f for f in failures)

    def test_stablecoins_and_wrappers_are_not_investable(self):
        rows = [asset("bitcoin", "BTC"), asset("tether", "USDT"),
                asset("wrapped-bitcoin", "WBTC")]
        assert [r.id for r in investable(rows)] == ["bitcoin"]


class TestRegime:
    """The two-measure reading of the market's observed state."""

    def test_both_measures_favourable_is_bull(self, rules):
        rows = [
            asset("bitcoin", "BTC", price=100.0, long_avg=80.0, ret_slow=20.0),
            asset("b", "B", ret_slow=15.0),
            asset("c", "C", ret_slow=5.0),
            ]
        assert evaluate_regime(rows, rules).state is MarketRegime.BULL

    def test_neither_measure_favourable_is_bear(self, rules):
        rows = [
            asset("bitcoin", "BTC", price=70.0, long_avg=100.0, ret_slow=-20.0),
            asset("b", "B", ret_slow=-15.0),
            asset("c", "C", ret_slow=-5.0),
            ]
        assert evaluate_regime(rows, rules).state is MarketRegime.BEAR

    def test_one_measure_favourable_is_mixed(self, rules):
        rows = [
            asset("bitcoin", "BTC", price=120.0, long_avg=100.0, ret_slow=5.0),
            asset("b", "B", ret_slow=-15.0),
            asset("c", "C", ret_slow=-5.0),
            ]
        assert evaluate_regime(rows, rules).state is MarketRegime.MIXTE

    def test_missing_long_average_reads_as_unknown(self, rules):
        """A 200-day regime call on 60 days of history is not a regime call."""
        rows = [
            asset("bitcoin", "BTC", price=120.0, long_avg=None, ret_slow=20.0),
            asset("b", "B", ret_slow=15.0),
            ]
        reading = evaluate_regime(rows, rules)
        assert reading.state is MarketRegime.INCONNU
        assert "insuffisant" in reading.reason

    def test_disabled_regime_is_not_applicable(self, rules):
        off = with_overrides(rules, regime=RegimeRules(enabled=False))
        reading = evaluate_regime([asset("bitcoin", "BTC")], off)
        assert reading.applicable is False
        assert reading.state is MarketRegime.INCONNU


class TestRotationGates:
    """Six barriers between a held line and the candidate."""

    def _bull(self):
        return evaluate_regime(
            [asset("bitcoin", "BTC", price=120.0, long_avg=100.0, ret_slow=30.0),
             asset("x", "X", ret_slow=20.0)],
            load_rules(),
            )

    @staticmethod
    def _scored(rules, held, candidate):
        """Score a realistic ranking, not just the two assets under test.

        A z-score needs a population: with two assets every score collapses to
        zero and the score-gap gate fails for a reason that has nothing to do
        with what the test is checking.
        """
        rows = [held, candidate,
                asset("solana", "SOL", ret_slow=5.0),
                asset("cardano", "ADA", ret_slow=0.0)]
        score_universe(rows, rules)
        return rows

    def test_a_clearly_better_candidate_still_needs_persistence(self, rules):
        """Week one never rotates, however strong the case looks."""
        held = asset("monero", "XMR", ret_slow=-10.0)
        candidate = asset("ethereum", "ETH", ret_slow=90.0)
        self._scored(rules, held, candidate)

        outcome = evaluate_rotation(position(), held, candidate, rules, [], self._bull())
        persistence = next(g for g in outcome.gates if g.name == "persistance")

        assert outcome.verdict is SignalVerdict.CONSERVER
        assert persistence.passed is False
        assert persistence.value == 1
        assert outcome.extra["all_gates_but_persistence"] is True

    def test_the_streak_completes_after_enough_scans(self, rules):
        held = asset("monero", "XMR", ret_slow=-10.0)
        candidate = asset("ethereum", "ETH", ret_slow=90.0)
        self._scored(rules, held, candidate)
        history = [PriorScan("ethereum", True, False)] * 2

        outcome = evaluate_rotation(position(), held, candidate, rules, history, self._bull())
        assert outcome.verdict is SignalVerdict.ROTATION
        assert outcome.extra["streak_weeks"] == 3

    def test_a_streak_on_a_different_candidate_does_not_count(self, rules):
        """Switching candidate restarts the count; otherwise the gate is noise."""
        held = asset("monero", "XMR", ret_slow=-10.0)
        candidate = asset("ethereum", "ETH", ret_slow=90.0)
        self._scored(rules, held, candidate)
        history = [PriorScan("solana", True, False)] * 5

        outcome = evaluate_rotation(position(), held, candidate, rules, history, self._bull())
        assert outcome.verdict is SignalVerdict.CONSERVER
        assert outcome.extra["streak_weeks"] == 1

    def test_an_interrupted_streak_restarts(self, rules):
        held = asset("monero", "XMR", ret_slow=-10.0)
        candidate = asset("ethereum", "ETH", ret_slow=90.0)
        self._scored(rules, held, candidate)
        # Newest first: it held, then it lapsed, then it held twice.
        history = [
            PriorScan("ethereum", True, False),
            PriorScan("ethereum", False, False),
            PriorScan("ethereum", True, False),
            ]
        outcome = evaluate_rotation(position(), held, candidate, rules, history, self._bull())
        assert outcome.extra["streak_weeks"] == 2
        assert outcome.verdict is SignalVerdict.CONSERVER

    def test_a_bear_regime_blocks_a_rotation_that_otherwise_passes(self, rules):
        held = asset("monero", "XMR", ret_slow=-10.0)
        candidate = asset("ethereum", "ETH", ret_slow=90.0)
        self._scored(rules, held, candidate)
        bear = evaluate_regime(
            [asset("bitcoin", "BTC", price=70.0, long_avg=100.0, ret_slow=-30.0),
             asset("x", "X", ret_slow=-20.0)],
            rules,
            )
        history = [PriorScan("ethereum", True, False)] * 5

        outcome = evaluate_rotation(position(), held, candidate, rules, history, bear)
        regime_gate = next(g for g in outcome.gates if g.name == "regime_favorable")

        assert regime_gate.passed is False
        assert outcome.verdict is SignalVerdict.CONSERVER

    def test_a_small_line_needs_a_bigger_edge(self, rules):
        """The flat chain fee is what makes a small position harder to move."""
        held = asset("monero", "XMR", ret_slow=0.0, price=100.0)
        candidate = asset("ethereum", "ETH", ret_slow=25.0)
        self._scored(rules, held, candidate)
        history = [PriorScan("ethereum", True, False)] * 5

        big = evaluate_rotation(
            position(units=100.0), held, candidate, rules, history, self._bull())
        small = evaluate_rotation(
            position(units=1.0), held, candidate, rules, history, self._bull())

        assert big.extra["required_edge_pct"] < small.extra["required_edge_pct"]

    def test_no_candidate_makes_the_mechanism_inapplicable(self, rules):
        held = asset("monero", "XMR")
        outcome = evaluate_rotation(position(), held, None, rules, [], self._bull())
        assert outcome.applicable is False
        assert outcome.verdict is None


class TestTrailingStop:
    """Full exit when a winning line breaks down."""

    def test_fires_on_a_winner_that_gave_back_too_much(self, rules):
        held = asset("monero", "XMR", price=100.0, dist_high=-45.0)
        outcome = evaluate_trailing_stop(position(cost_basis_eur=500.0), held, rules)
        assert outcome.verdict is SignalVerdict.SORTIE_STOP

    def test_does_nothing_on_a_losing_line(self, rules):
        """On a loss it is the regime temporisation that decides, not the stop."""
        held = asset("monero", "XMR", price=100.0, dist_high=-45.0)
        outcome = evaluate_trailing_stop(position(cost_basis_eur=5000.0), held, rules)
        gain_gate = next(g for g in outcome.gates if g.name == "position_en_gain")
        assert gain_gate.passed is False
        assert outcome.verdict is SignalVerdict.CONSERVER

    def test_does_nothing_while_near_the_high(self, rules):
        held = asset("monero", "XMR", price=100.0, dist_high=-10.0)
        outcome = evaluate_trailing_stop(position(cost_basis_eur=500.0), held, rules)
        assert outcome.verdict is SignalVerdict.CONSERVER

    def test_cannot_run_without_a_cost_basis(self, rules):
        held = asset("monero", "XMR", price=100.0, dist_high=-45.0)
        outcome = evaluate_trailing_stop(position(cost_basis_eur=None), held, rules)
        assert outcome.applicable is False
        assert "prix de revient" in outcome.reason

    def test_disabled_stop_is_not_applicable(self, rules):
        off = with_overrides(rules, trailing_stop=TrailingStopRules(enabled=False))
        held = asset("monero", "XMR", price=100.0, dist_high=-45.0)
        assert evaluate_trailing_stop(position(), held, off).applicable is False


class TestProfitTaking:
    """Recovering the stake, once."""

    def test_fires_past_the_gain_threshold(self, rules):
        held = asset("monero", "XMR", price=100.0)
        outcome = evaluate_profit_taking(
            position(units=100.0, cost_basis_eur=2000.0), held, rules, already_taken=False)
        assert outcome.verdict is SignalVerdict.ALLEGER

    def test_the_fraction_returns_the_stake_net_of_fees(self, rules):
        """Proceeds after fees must cover the stake, not merely approach it."""
        held = asset("monero", "XMR", price=100.0)
        pos = position(units=100.0, cost_basis_eur=2000.0)
        outcome = evaluate_profit_taking(pos, held, rules, already_taken=False)

        fee_pct = rules.costs.worst_case_pct()
        net = outcome.extra["proceeds"] * (1 - fee_pct / 100.0)
        assert net == pytest.approx(2000.0, rel=0.01)

    def test_the_fraction_is_capped(self, rules):
        """This mechanism recovers a stake; it never liquidates the line."""
        held = asset("monero", "XMR", price=100.0)
        pos = position(units=100.0, cost_basis_eur=9000.0)
        capped = with_overrides(
            rules, profit_taking=ProfitTakingRules(trigger_gain_pct=0.0, max_fraction=0.6))
        outcome = evaluate_profit_taking(pos, held, capped, already_taken=False)
        assert outcome.extra["fraction"] <= 0.6

    def test_only_once_per_line(self, rules):
        held = asset("monero", "XMR", price=100.0)
        pos = position(units=100.0, cost_basis_eur=2000.0)
        outcome = evaluate_profit_taking(pos, held, rules, already_taken=True)
        gate = next(g for g in outcome.gates if g.name == "jamais_pris")
        assert gate.passed is False
        assert outcome.verdict is SignalVerdict.CONSERVER

    def test_a_trim_too_small_to_be_worth_its_fees_is_refused(self, rules):
        held = asset("monero", "XMR", price=1.0)
        pos = position(units=100.0, cost_basis_eur=20.0)
        outcome = evaluate_profit_taking(pos, held, rules, already_taken=False)
        gate = next(g for g in outcome.gates if g.name == "montant_vendu_suffisant")
        assert gate.passed is False


class TestTemporisation:
    """The one-way exit into a refuge."""

    def _degraded(self, rules):
        held = asset("monero", "XMR", ret_slow=-40.0, dd=-50.0, price=100.0)
        peers = [asset(f"p{i}", f"P{i}", ret_slow=-20.0) for i in range(5)]
        refuge = asset("usd-coin", "USDC", price=1.0, volume=5e9)
        bear = evaluate_regime(
            [asset("bitcoin", "BTC", price=70.0, long_avg=100.0, ret_slow=-30.0),
             asset("x", "X", ret_slow=-20.0)],
            rules,
            )
        return held, [held] + peers, refuge, bear

    def test_a_degraded_market_still_needs_persistence(self, rules):
        held, rows, refuge, bear = self._degraded(rules)
        outcome = evaluate_temporisation(
            position(), held, rows, refuge, rules, [], bear)
        assert outcome.verdict is SignalVerdict.CONSERVER
        assert outcome.extra["all_gates_but_persistence"] is True

    def test_it_fires_once_the_conditions_have_held(self, rules):
        held, rows, refuge, bear = self._degraded(rules)
        history = [PriorScan("ethereum", False, True)]
        outcome = evaluate_temporisation(
            position(), held, rows, refuge, rules, history, bear)
        assert outcome.verdict is SignalVerdict.TEMPORISER

    def test_no_liquid_refuge_blocks_it(self, rules):
        held, rows, _refuge, bear = self._degraded(rules)
        history = [PriorScan("ethereum", False, True)] * 3
        outcome = evaluate_temporisation(
            position(), held, rows, None, rules, history, bear)
        gate = next(g for g in outcome.gates if g.name == "liquidite_refuge")
        assert gate.passed is False
        assert outcome.verdict is SignalVerdict.CONSERVER

    def test_a_mild_decline_does_not_justify_the_fees(self, rules):
        held = asset("monero", "XMR", ret_slow=-3.0, dd=-8.0, price=100.0)
        peers = [asset(f"p{i}", f"P{i}", ret_slow=5.0) for i in range(5)]
        refuge = asset("usd-coin", "USDC", price=1.0, volume=5e9)
        bull = evaluate_regime(
            [asset("bitcoin", "BTC", price=120.0, long_avg=100.0, ret_slow=30.0),
             asset("x", "X", ret_slow=20.0)],
            rules,
            )
        outcome = evaluate_temporisation(
            position(), held, [held] + peers, refuge, rules,
            [PriorScan("e", False, True)] * 3, bull,
            )
        assert outcome.verdict is SignalVerdict.CONSERVER


class TestPriorityOrder:
    """Which mechanism wins when several fire on the same line.

    This ordering is a judgement, not an implementation detail: protecting
    capital outranks banking a gain, which outranks chasing another asset.
    """

    def _market(self):
        return [
            asset("bitcoin", "BTC", price=60000.0, long_avg=50000.0, ret_slow=30.0),
            asset("ethereum", "ETH", ret_slow=95.0),
            asset("monero", "XMR", ret_slow=-20.0, price=100.0, dist_high=-50.0, dd=-40.0),
            asset("solana", "SOL", ret_slow=10.0),
            ]

    def test_the_stop_outranks_everything(self, rules):
        rows = self._market()
        # In profit and 50 % off its high: stop and profit taking both qualify.
        pos = position(units=100.0, cost_basis_eur=2000.0)
        result = run_scan(
            rows, [pos], rules,
            history={1: [PriorScan("ethereum", True, True)] * 5},
            profit_already_taken=set(),
            refuge=asset("usd-coin", "USDC", price=1.0, volume=5e9),
            )
        outcome = result.positions[0]
        assert outcome.trailing_stop.verdict is SignalVerdict.SORTIE_STOP
        assert outcome.profit_taking.verdict is SignalVerdict.ALLEGER
        assert outcome.verdict is SignalVerdict.SORTIE_STOP

    def test_profit_taking_outranks_rotation(self, rules):
        rows = self._market()
        # Near its high, so the stop stays quiet, but deeply in profit.
        rows[2] = asset("monero", "XMR", ret_slow=-20.0, price=100.0, dist_high=-2.0)
        pos = position(units=100.0, cost_basis_eur=2000.0)
        result = run_scan(
            rows, [pos], rules,
            history={1: [PriorScan("ethereum", True, True)] * 5},
            profit_already_taken=set(),
            refuge=asset("usd-coin", "USDC", price=1.0, volume=5e9),
            )
        outcome = result.positions[0]
        assert outcome.rotation.verdict is SignalVerdict.ROTATION
        assert outcome.verdict is SignalVerdict.ALLEGER

    def test_a_passing_rotation_skips_the_temporisation(self, rules):
        """Exiting to a stable while a valid candidate exists pays a leg for nothing."""
        rows = self._market()
        rows[2] = asset("monero", "XMR", ret_slow=-40.0, price=100.0, dist_high=-2.0, dd=-50.0)
        pos = position(units=10.0, cost_basis_eur=None)
        result = run_scan(
            rows, [pos], rules,
            history={1: [PriorScan("ethereum", True, True)] * 5},
            profit_already_taken=set(),
            refuge=asset("usd-coin", "USDC", price=1.0, volume=5e9),
            )
        outcome = result.positions[0]
        assert outcome.verdict is SignalVerdict.ROTATION
        assert outcome.temporisation.applicable is False
        assert "rotation" in outcome.temporisation.reason.lower()


class TestRunScan:
    """Whole-scan behaviour."""

    def test_a_line_fully_covered_by_its_reserve_is_not_arbitrated(self, rules):
        rows = [asset("monero", "XMR", price=100.0), asset("ethereum", "ETH", ret_slow=90.0)]
        pos = position(units=1.0, gas_reserve_eur=500.0)
        result = run_scan(rows, [pos], rules, {}, set())
        outcome = result.positions[0]
        assert outcome.arbitrated is False
        assert outcome.verdict is SignalVerdict.CONSERVER
        assert "réserve" in outcome.reason

    def test_a_line_switched_off_is_reported_but_not_arbitrated(self, rules):
        rows = [asset("monero", "XMR", price=100.0), asset("ethereum", "ETH", ret_slow=90.0)]
        result = run_scan(rows, [position(arbitrated=False)], rules, {}, set())
        outcome = result.positions[0]
        assert outcome.arbitrated is False
        assert outcome.current_value == pytest.approx(1000.0)

    def test_an_unknown_market_id_is_reported_clearly(self, rules):
        rows = [asset("ethereum", "ETH", ret_slow=90.0)]
        result = run_scan(rows, [position(coingecko_id="nonexistent")], rules, {}, set())
        outcome = result.positions[0]
        assert outcome.arbitrated is False
        assert "introuvable" in outcome.reason

    def test_the_global_verdict_is_the_most_engaging_one(self, rules):
        rows = [
            asset("bitcoin", "BTC", price=60000.0, long_avg=50000.0, ret_slow=30.0),
            asset("ethereum", "ETH", ret_slow=95.0),
            asset("monero", "XMR", ret_slow=-20.0, price=100.0, dist_high=-50.0),
            asset("cardano", "ADA", ret_slow=5.0, price=1.0),
            ]
        stopping = position(product_id=1, units=100.0, cost_basis_eur=2000.0)
        quiet = Position(product_id=2, coingecko_id="cardano", symbol="ADA",
                         units=10.0, cost_basis_eur=100.0)
        result = run_scan(rows, [stopping, quiet], rules, {}, set(),
                          refuge=asset("usd-coin", "USDC", price=1.0, volume=5e9))
        assert result.verdict is SignalVerdict.SORTIE_STOP

    def test_short_history_assets_are_flagged(self, rules):
        rows = [
            asset("monero", "XMR", price=100.0, sample=20),
            asset("ethereum", "ETH", ret_slow=90.0, sample=300),
            ]
        result = run_scan(rows, [position()], rules, {}, set())
        assert "XMR" in result.insufficient_history

    def test_a_position_already_in_a_refuge_skips_the_temporisation(self, rules):
        rows = [
            asset("usd-coin", "USDC", price=1.0, ret_slow=0.0, volume=5e9),
            asset("ethereum", "ETH", ret_slow=90.0),
            ]
        pos = Position(product_id=1, coingecko_id="usd-coin", symbol="USDC", units=1000.0)
        result = run_scan(rows, [pos], rules, {}, set(),
                          refuge=asset("usd-coin", "USDC", price=1.0, volume=5e9))
        outcome = result.positions[0]
        assert outcome.temporisation.applicable is False
        assert "refuge" in outcome.temporisation.reason.lower()


class TestPlans:
    """The parameters handed to the user when a move is proposed."""

    def test_a_plan_states_a_floor_below_the_reference(self, rules):
        rows = [
            asset("bitcoin", "BTC", price=60000.0, long_avg=50000.0, ret_slow=30.0),
            asset("ethereum", "ETH", ret_slow=95.0, price=2000.0),
            asset("monero", "XMR", ret_slow=-20.0, price=100.0),
            ]
        result = run_scan(
            rows, [position(cost_basis_eur=None)], rules,
            {1: [PriorScan("ethereum", True, False)] * 5}, set(),
            )
        plan = result.positions[0].plan
        assert plan is not None
        assert plan["kind"] == "ROTATION"
        assert plan["min_accept_units"] < plan["units_at_reference"]
        assert plan["quotes_to_compare"]

    def test_no_plan_when_nothing_is_proposed(self, rules):
        rows = [asset("monero", "XMR", price=100.0), asset("ethereum", "ETH", ret_slow=12.0)]
        result = run_scan(rows, [position()], rules, {}, set())
        assert result.positions[0].plan is None


class TestRulesValidation:
    """The thresholds file rejects what the engine cannot act on."""

    def test_shipped_rules_are_valid(self):
        assert load_rules().quote_currency == "EUR"

    def test_windows_must_differ(self):
        from finance_tracker.services.crypto.rules import RulesError, parse_rules
        with pytest.raises(RulesError, match="fast_window_days"):
            parse_rules({"signal": {"fast_window_days": 90, "slow_window_days": 90}})

    def test_an_unknown_threshold_is_rejected(self):
        from finance_tracker.services.crypto.rules import RulesError, parse_rules
        with pytest.raises(RulesError, match="Clé inconnue"):
            parse_rules({"gates": {"min_score_deltaa": 1.5}})

    def test_temporisation_needs_a_refuge(self):
        from finance_tracker.services.crypto.rules import RulesError, parse_rules
        with pytest.raises(RulesError, match="refuge"):
            parse_rules({"temporisation": {"enabled": True, "refuges": []}})

    def test_cost_of_a_zero_line_is_infinite(self, rules):
        """Infinity makes every cost gate fail instead of dividing by zero."""
        assert rules.costs.round_trip_pct(0) == float("inf")
        assert rules.costs.one_way_pct(0) == float("inf")

    def test_lookback_never_exceeds_the_free_plan(self):
        from finance_tracker.services.crypto.rules import MAX_LOOKBACK_DAYS
        deep = Rules(trailing_stop=TrailingStopRules(window_days=9000))
        assert deep.lookback_days() <= MAX_LOOKBACK_DAYS

    def test_refuges_are_empty_when_temporisation_is_off(self):
        assert not Rules(temporisation=TemporisationRules(enabled=False)).refuge_ids()
