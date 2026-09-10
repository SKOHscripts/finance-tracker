"""Tests for the user-adjustable rotation thresholds.

The design decision under test is that the database stores *deviations*, not a
copy of the settings. That choice is what lets a released default reach a user
who never touched it, while keeping the figure of a user who deliberately moved
one. Almost every test here is really about that distinction.

The second theme is refusal. A threshold is only ever right in relation to the
others, so the engine's own coherence checks have to run over an adjusted set
before it is stored — otherwise the interface becomes a way to reach states the
rules file itself would reject.
"""
# pylint: disable=redefined-outer-name  # pytest fixture pattern
import pytest
from sqlalchemy import select
from sqlmodel import Session, create_engine

from finance_tracker.domain.models import SignalSetting
from finance_tracker.repositories.sqlmodel_repo import init_db
from finance_tracker.services.crypto.rules import Rules, load_rules
from finance_tracker.services.crypto.settings import (
    PARAMETERS,
    SECTION_ORDER,
    SettingsError,
    apply_overrides,
    coerce,
    default_value,
    describe,
    effective_rules,
    parameter,
    parameters_by_section,
    reset_all,
    reset_setting,
    serialise,
    set_many,
    set_setting,
    stored_overrides,
    )


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    with Session(engine) as active:
        yield active


@pytest.fixture()
def defaults():
    """The shipped thresholds."""
    return load_rules()


def rows(session):
    return session.exec(select(SignalSetting)).scalars().all()


class TestTheRegistry:
    """The list of adjustable parameters must describe the real dataclasses."""

    def test_every_parameter_names_a_real_setting(self, defaults):
        """A typo here would offer a control that changes nothing."""
        for param in PARAMETERS:
            section = getattr(defaults, param.section)
            assert hasattr(section, param.field), param.key

    def test_every_section_is_in_the_display_order(self):
        """A section missing from the order would never be drawn."""
        assert {p.section for p in PARAMETERS} <= set(SECTION_ORDER)

    def test_keys_are_unique(self):
        keys = [p.key for p in PARAMETERS]
        assert len(keys) == len(set(keys))

    def test_every_parameter_is_reachable_by_key(self):
        for param in PARAMETERS:
            assert parameter(param.key) is param

    def test_an_unknown_key_is_refused(self):
        with pytest.raises(SettingsError, match="inconnu"):
            parameter("gates.no_such_threshold")

    def test_grouping_covers_every_parameter(self):
        grouped = parameters_by_section()
        assert sum(len(v) for v in grouped.values()) == len(PARAMETERS)

    def test_bounds_contain_the_shipped_value(self, defaults):
        """A default the interface would refuse to display is a broken bound."""
        for param in PARAMETERS:
            if param.kind == "bool":
                continue
            value = float(default_value(param, defaults))
            if param.minimum is not None:
                assert value >= param.minimum, param.key
            if param.maximum is not None:
                assert value <= param.maximum, param.key


class TestDeviationsOnly:
    """The database holds what the user moved, and nothing else."""

    def test_an_untouched_install_stores_nothing(self, session):
        assert stored_overrides(session) == {}
        assert not rows(session)

    def test_a_moved_threshold_is_stored(self, session):
        assert set_setting(session, "gates.min_score_delta", 2.5) is True
        assert stored_overrides(session) == {"gates.min_score_delta": "2.5"}

    def test_setting_a_value_back_to_the_default_drops_the_row(self, session, defaults):
        """Storing it would pin the user to today's figure without them asking.

        This is the whole reason deviations are stored rather than a copy: a
        user who returns a threshold to the shipped value should go back to
        following it, including through a later release that changes it.
        """
        set_setting(session, "gates.min_score_delta", 2.5)
        shipped = default_value(parameter("gates.min_score_delta"), defaults)

        assert set_setting(session, "gates.min_score_delta", shipped) is False
        assert not rows(session)

    def test_an_untouched_threshold_follows_a_changed_default(self, session):
        """The point of the design, stated as a test.

        A release that improves a default must reach a user who never touched
        that threshold. Here the "release" is a different base handed in.
        """
        set_setting(session, "gates.min_score_delta", 2.5)

        from dataclasses import replace
        shipped = load_rules()
        next_release = replace(
            shipped, gates=replace(shipped.gates, max_candidate_vol_pct=90.0))

        rules = effective_rules(session, next_release)
        assert rules.gates.max_candidate_vol_pct == 90.0  # followed the new default
        assert rules.gates.min_score_delta == 2.5  # kept the user's figure

    def test_a_row_from_a_removed_setting_is_ignored(self, session):
        """A threshold dropped upstream must not stop the page from loading."""
        session.add(SignalSetting(key="gates.threshold_that_no_longer_exists", value="1"))
        session.commit()

        assert stored_overrides(session) == {}
        assert isinstance(effective_rules(session), Rules)


class TestEffectiveRules:
    """What the engine actually runs with."""

    def test_no_deviation_means_the_shipped_thresholds(self, session, defaults):
        assert effective_rules(session, defaults) == defaults

    def test_a_deviation_reaches_the_engine(self, session, defaults):
        set_setting(session, "trailing_stop.max_drawdown_pct", 20.0)
        assert effective_rules(session, defaults).trailing_stop.max_drawdown_pct == 20.0

    def test_deviations_in_several_sections_all_apply(self, session, defaults):
        set_setting(session, "gates.min_score_delta", 2.5)
        set_setting(session, "profit_taking.trigger_gain_pct", 150.0)
        set_setting(session, "regime.enabled", False)

        rules = effective_rules(session, defaults)
        assert rules.gates.min_score_delta == 2.5
        assert rules.profit_taking.trigger_gain_pct == 150.0
        assert rules.regime.enabled is False

    def test_other_fields_of_a_touched_section_keep_their_value(self, session, defaults):
        """Replacing one field must not reset its neighbours to dataclass defaults."""
        set_setting(session, "gates.min_score_delta", 2.5)

        rules = effective_rules(session, defaults)
        assert rules.gates.min_volume_24h == defaults.gates.min_volume_24h
        assert rules.gates.required_consecutive_weeks == \
            defaults.gates.required_consecutive_weeks

    def test_the_base_is_not_mutated(self, session, defaults):
        before = defaults.gates.min_score_delta
        set_setting(session, "gates.min_score_delta", 2.5)
        effective_rules(session, defaults)

        assert defaults.gates.min_score_delta == before

    def test_a_deviation_changes_the_lookback(self, session, defaults):
        """Adjusted windows must reach the derived figures, not just the fields."""
        set_setting(session, "trailing_stop.window_days", 300)
        assert effective_rules(session, defaults).lookback_days() > defaults.lookback_days()


class TestCoherenceIsEnforced:
    """The interface must not reach a state the rules file would reject."""

    def test_a_fast_window_longer_than_the_slow_one_is_refused(self, session):
        """The score would count the same measurement twice."""
        with pytest.raises(SettingsError, match="fast_window_days"):
            set_setting(session, "signal.fast_window_days", 120)

    def test_the_refusal_stores_nothing(self, session):
        with pytest.raises(SettingsError):
            set_setting(session, "signal.fast_window_days", 120)
        assert not rows(session)

    def test_a_positive_temporisation_momentum_is_refused(self, session):
        """It describes a fall; a positive figure describes the opposite."""
        with pytest.raises(SettingsError):
            set_setting(session, "temporisation.max_held_slow_momentum_pct", 5)

    def test_a_combination_only_wrong_together_is_refused(self, session):
        """Each figure is fine alone; the pair is not.

        Setting the slow window below the fast one is legal in isolation and
        incoherent once the other field is read — which is why the whole set
        is validated rather than the field.
        """
        set_setting(session, "signal.fast_window_days", 60)
        with pytest.raises(SettingsError):
            set_setting(session, "signal.slow_window_days", 30)

    def test_a_value_below_the_bound_is_refused(self, session):
        with pytest.raises(SettingsError, match="au moins"):
            set_setting(session, "universe.top_n", 1)

    def test_a_value_above_the_bound_is_refused(self, session):
        with pytest.raises(SettingsError, match="dépasser"):
            set_setting(session, "profit_taking.max_fraction", 5)

    def test_an_unreadable_value_is_refused(self, session):
        with pytest.raises(SettingsError, match="illisible"):
            set_setting(session, "gates.min_score_delta", "beaucoup")

    def test_an_incoherent_stored_set_is_reported_not_crashed(self, session):
        """A row written by an older release could be incoherent today."""
        session.add(SignalSetting(key="signal.fast_window_days", value="200"))
        session.commit()

        with pytest.raises(SettingsError):
            effective_rules(session)


class TestSetMany:
    """A section is accepted or refused as one."""

    def test_several_deviations_are_stored_together(self, session, defaults):
        stored = set_many(session, {
            "gates.min_score_delta": 2.5,
            "gates.required_consecutive_weeks": 4,
            })

        assert stored == 2
        rules = effective_rules(session, defaults)
        assert rules.gates.min_score_delta == 2.5
        assert rules.gates.required_consecutive_weeks == 4

    def test_a_refusal_writes_nothing_at_all(self, session):
        """Not even the fields that were fine on their own.

        A fast window of 20 is legal; a slow window of 10 is not once the fast
        one is read. Writing them one at a time would store the first.
        """
        with pytest.raises(SettingsError):
            set_many(session, {
                "signal.fast_window_days": 20,
                "signal.slow_window_days": 10,
                })

        assert stored_overrides(session) == {}

    def test_a_value_back_at_its_default_drops_its_row(self, session, defaults):
        set_setting(session, "gates.min_score_delta", 2.5)
        shipped = default_value(parameter("gates.min_score_delta"), defaults)

        assert set_many(session, {"gates.min_score_delta": shipped}) == 0
        assert not rows(session)

    def test_an_out_of_bounds_value_refuses_the_whole_call(self, session):
        with pytest.raises(SettingsError, match="au moins"):
            set_many(session, {
                "universe.request_delay_seconds": 3.0,
                "universe.top_n": 1,
                })

        assert stored_overrides(session) == {}

    def test_an_unknown_key_refuses_the_whole_call(self, session):
        with pytest.raises(SettingsError, match="inconnu"):
            set_many(session, {"gates.min_score_delta": 2.5, "gates.nope": 1})

        assert stored_overrides(session) == {}

    def test_nothing_to_do_is_not_an_error(self, session):
        assert set_many(session, {}) == 0

    def test_it_does_not_disturb_deviations_it_was_not_given(self, session, defaults):
        set_setting(session, "regime.enabled", False)
        set_many(session, {"gates.min_score_delta": 2.5})

        assert effective_rules(session, defaults).regime.enabled is False


class TestReading:
    """Text in, typed value out."""

    @pytest.mark.parametrize("raw,expected", [
        ("true", True), ("false", False), ("1", True), ("0", False),
        ("oui", True), ("non", False), ("TRUE", True),
        ])
    def test_a_boolean_is_read_from_its_spellings(self, raw, expected):
        assert coerce(parameter("regime.enabled"), raw) is expected

    def test_an_unspelled_boolean_is_refused(self):
        with pytest.raises(SettingsError, match="illisible"):
            coerce(parameter("regime.enabled"), "peut-être")

    def test_an_integer_setting_stays_an_integer(self):
        value = coerce(parameter("universe.top_n"), "12.0")
        assert value == 12
        assert isinstance(value, int)

    def test_a_float_setting_accepts_an_integer_spelling(self):
        assert coerce(parameter("gates.min_score_delta"), "2") == 2.0

    def test_a_value_survives_a_round_trip(self):
        param = parameter("gates.min_score_delta")
        assert coerce(param, serialise(param, 2.5)) == 2.5

    def test_a_boolean_survives_a_round_trip(self):
        param = parameter("regime.enabled")
        assert coerce(param, serialise(param, False)) is False


class TestResetting:
    """Returning to the shipped values."""

    def test_one_setting_goes_back(self, session, defaults):
        set_setting(session, "gates.min_score_delta", 2.5)
        reset_setting(session, "gates.min_score_delta")

        assert effective_rules(session, defaults) == defaults

    def test_resetting_an_untouched_setting_is_harmless(self, session):
        reset_setting(session, "gates.min_score_delta")
        assert not rows(session)

    def test_resetting_an_unknown_setting_is_refused(self, session):
        """Silence would hide a typo in a caller."""
        with pytest.raises(SettingsError, match="inconnu"):
            reset_setting(session, "gates.nope")

    def test_everything_goes_back_at_once(self, session, defaults):
        set_setting(session, "gates.min_score_delta", 2.5)
        set_setting(session, "regime.enabled", False)

        assert reset_all(session) == 2
        assert effective_rules(session, defaults) == defaults

    def test_resetting_nothing_reports_nothing(self, session):
        assert reset_all(session) == 0


class TestDescribe:
    """What the panel draws."""

    def test_every_parameter_is_described(self, session):
        assert len(describe(session)) == len(PARAMETERS)

    def test_an_untouched_parameter_is_not_marked_changed(self, session):
        entries = {e["param"].key: e for e in describe(session)}
        assert not any(e["changed"] for e in entries.values())

    def test_a_moved_parameter_carries_both_figures(self, session):
        set_setting(session, "gates.min_score_delta", 2.5)

        entry = next(e for e in describe(session) if e["param"].key == "gates.min_score_delta")
        assert entry["changed"] is True
        assert entry["value"] == 2.5
        assert entry["default"] == 1.5

    def test_an_incoherent_stored_set_still_describes(self, session):
        """The panel that fixes the problem must still be drawable.

        Refusing to describe would leave the user with an error and no control
        to correct it — locked out by their own setting.
        """
        session.add(SignalSetting(key="signal.fast_window_days", value="200"))
        session.commit()

        entries = describe(session)
        assert len(entries) == len(PARAMETERS)


class TestApplyOverrides:
    """The pure function underneath, without a database."""

    def test_no_override_returns_the_base(self, defaults):
        assert apply_overrides(defaults, {}) is defaults

    def test_an_unknown_key_is_refused(self, defaults):
        with pytest.raises(SettingsError, match="inconnu"):
            apply_overrides(defaults, {"gates.nope": "1"})

    def test_a_boolean_override_applies(self, defaults):
        assert apply_overrides(
            defaults, {"regime.enabled": "false"}).regime.enabled is False
