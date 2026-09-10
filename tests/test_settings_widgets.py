"""Tests for the panel that moves a rotation threshold.

Two things must hold, and neither would announce itself if broken.

Every control has to carry the sentence saying what its threshold does — the
whole reason for exposing these figures is that the arbitrage stays the user's,
and a figure they cannot explain is one they cannot set responsibly. A missing
translation would render as a raw key, which is not an error anywhere.

And a panel that refuses an incoherent value must still draw itself, or a user
who stores one is locked out by their own setting, staring at an error with no
control to fix it.
"""
# pylint: disable=redefined-outer-name  # pytest fixture pattern
# pylint: disable=unused-argument  # the fakes mirror Streamlit's signatures
# pylint: disable=too-few-public-methods  # the fakes are recorders
from contextlib import contextmanager

import pytest
from sqlmodel import Session, create_engine

from finance_tracker.domain.models import SignalSetting
from finance_tracker.i18n import en, fr
from finance_tracker.repositories.sqlmodel_repo import init_db
from finance_tracker.services.crypto.settings import (
    PARAMETERS,
    SECTION_ORDER,
    effective_rules,
    set_setting,
    stored_overrides,
    )
from finance_tracker.web.ui import settings_widgets


class FakeStreamlit:
    """Enough of Streamlit to run the panel and record what it drew."""

    def __init__(self, values=None, clicks=None):
        self.values = values or {}
        self.clicks = clicks or {}
        self.calls = []
        self.helps = []
        self.session_state = {}
        self.current_form = None

    @contextmanager
    def expander(self, label, expanded=False):
        self.calls.append(("expander", label))
        yield self

    @contextmanager
    def form(self, key, clear_on_submit=False):
        """Each form is its own submission, as it is in the real app."""
        previous, self.current_form = self.current_form, key
        try:
            yield self
        finally:
            self.current_form = previous

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def number_input(self, label, value=None, min_value=None, max_value=None,
                     step=None, help=None, key=None):  # pylint: disable=redefined-builtin
        self.calls.append(("number", label, value))
        self.helps.append(help)
        return self.values.get(key, value)

    def checkbox(self, label, value=False, help=None, key=None):  # pylint: disable=redefined-builtin
        self.calls.append(("checkbox", label, value))
        self.helps.append(help)
        return self.values.get(key, value)

    def caption(self, body, **kwargs):
        self.calls.append(("caption", body))

    def markdown(self, body="", **kwargs):
        self.calls.append(("markdown", body))

    def info(self, body, **kwargs):
        self.calls.append(("info", body))

    def error(self, body, **kwargs):
        self.calls.append(("error", body))

    def success(self, body, **kwargs):
        self.calls.append(("success", body))

    def button(self, label, key=None, width=None, type=None):  # pylint: disable=redefined-builtin
        return bool(self.clicks.get(key or label, False))

    def form_submit_button(self, label, width=None):
        """Clickable by form key, to submit one section, or by label, to submit all."""
        current = self.current_form
        if current in self.clicks:
            return bool(self.clicks[current])
        return bool(self.clicks.get(label, False))

    def _bodies(self, kind):
        """Recorded rows vary in width — widgets carry a value, output does not."""
        return [c[1] for c in self.calls if c[0] == kind]

    @property
    def errors(self):
        return self._bodies("error")

    @property
    def successes(self):
        return self._bodies("success")

    @property
    def captions(self):
        return self._bodies("caption")

    @property
    def expanders(self):
        return self._bodies("expander")

    @property
    def controls(self):
        return [c for c in self.calls if c[0] in ("number", "checkbox")]


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    with Session(engine) as active:
        yield active


@pytest.fixture()
def render(monkeypatch):
    """Run the panel with a scripted Streamlit and a passthrough translator."""
    def run(session, values=None, clicks=None, translate=None):
        fake = FakeStreamlit(values, clicks)
        monkeypatch.setattr(settings_widgets, "st", fake)
        monkeypatch.setattr(
            settings_widgets, "t", translate or (lambda key: key))
        settings_widgets.render_settings(session)
        return fake
    return run


SAVE = "settings.save_section"
RESET = "settings.reset_all"


class TestEveryThresholdIsExplained:
    """The reason the panel exists at all."""

    @pytest.mark.parametrize("catalogue,name", [(fr.STRINGS, "fr"), (en.STRINGS, "en")])
    def test_every_parameter_has_a_label_and_a_sentence(self, catalogue, name):
        for param in PARAMETERS:
            assert param.label_key in catalogue, f"{name}: {param.label_key}"
            assert param.help_key in catalogue, f"{name}: {param.help_key}"

    @pytest.mark.parametrize("catalogue,name", [(fr.STRINGS, "fr"), (en.STRINGS, "en")])
    def test_every_section_has_a_label_and_a_sentence(self, catalogue, name):
        for section in SECTION_ORDER:
            assert f"section.{section}" in catalogue, f"{name}: {section}"
            assert f"sectionhelp.{section}" in catalogue, f"{name}: {section}"

    @pytest.mark.parametrize("catalogue,name", [(fr.STRINGS, "fr"), (en.STRINGS, "en")])
    def test_a_sentence_is_a_sentence_not_a_word(self, catalogue, name):
        """A three-word gloss restates the label instead of explaining it."""
        for param in PARAMETERS:
            text = catalogue[param.help_key]
            assert len(text.split()) >= 8, f"{name}: {param.help_key} trop court"
            assert text.rstrip().endswith("."), f"{name}: {param.help_key} sans point"

    def test_a_label_is_not_the_raw_field_name(self):
        """A key rendered raw looks like a label and reads like a bug."""
        for param in PARAMETERS:
            assert fr.STRINGS[param.label_key] != param.field

    def test_the_sentence_reaches_the_control(self, session, render):
        """Streamlit shows it as the field's help; a missing one renders blank."""
        fake = render(session)

        assert len(fake.helps) == len(PARAMETERS)
        assert all(h for h in fake.helps)


class TestDrawing:
    """What the panel puts on screen."""

    def test_every_section_gets_an_expander(self, session, render):
        fake = render(session)
        assert len(fake.expanders) == len(SECTION_ORDER)

    def test_every_parameter_gets_a_control(self, session, render):
        fake = render(session)
        assert len(fake.controls) == len(PARAMETERS)

    def test_a_boolean_gets_a_checkbox_not_a_number(self, session, render):
        fake = render(session)
        checkboxes = [c for c in fake.controls if c[0] == "checkbox"]
        assert len(checkboxes) == len([p for p in PARAMETERS if p.kind == "bool"])

    def test_an_untouched_panel_shows_no_moved_count(self, session, render):
        fake = render(session)
        assert not any("moved_count" in str(c) for c in fake.calls)

    def test_a_moved_threshold_is_announced(self, session, render):
        set_setting(session, "gates.min_score_delta", 2.5)

        fake = render(session)

        assert any("settings.moved_count" in str(c) for c in fake.calls)

    def test_a_moved_threshold_shows_its_shipped_value(self, session, render):
        """Otherwise a setting silently diverges from what the docs describe."""
        set_setting(session, "gates.min_score_delta", 2.5)

        fake = render(session)

        assert any("settings.default_is" in c for c in fake.captions)

    def test_the_section_holding_it_is_marked(self, session, render):
        set_setting(session, "gates.min_score_delta", 2.5)

        fake = render(session)

        assert any("✍️" in label for label in fake.expanders)


class TestSaving:
    """What lands in the database."""

    def test_submitting_a_section_stores_the_change(self, session, render):
        render(session,
               values={"set_gates.min_score_delta": 2.5},
               clicks={SAVE: True})

        assert stored_overrides(session).get("gates.min_score_delta") == "2.5"

    def test_a_value_left_at_its_default_stores_nothing(self, session, render):
        """Submitting a form must not pin every threshold in it."""
        render(session, clicks={SAVE: True})

        assert stored_overrides(session) == {}

    def test_a_boolean_can_be_switched_off(self, session, render):
        render(session, values={"set_regime.enabled": False}, clicks={SAVE: True})

        assert effective_rules(session).regime.enabled is False

    def test_an_integer_stays_an_integer(self, session, render):
        """`number_input` hands back a float; the rules field wants an int."""
        render(session, values={"set_universe.top_n": 12.0}, clicks={SAVE: True})

        value = effective_rules(session).universe.top_n
        assert value == 12
        assert isinstance(value, int)

    def test_nothing_is_stored_without_the_button(self, session, render):
        render(session, values={"set_gates.min_score_delta": 2.5})

        assert stored_overrides(session) == {}


class TestRefusing:
    """An incoherent set is refused, and the panel still works."""

    def test_an_incoherent_value_is_reported(self, session, render):
        fake = render(session,
                      values={"set_signal.fast_window_days": 200.0},
                      clicks={SAVE: True})

        assert fake.errors

    def test_a_refused_submission_reports_no_success(self, session, render):
        fake = render(session,
                      values={"set_signal.fast_window_days": 200.0},
                      clicks={"settings_signal": True})

        assert not fake.successes

    def test_a_refused_section_is_left_entirely_untouched(self, session, render):
        """Atomicity: the fields before the bad one must not look accepted.

        The two window widths are submitted together, in that order. A fast
        window of 20 is perfectly legal on its own; a slow window of 10 is not,
        once the fast one is read. A loop would therefore store the first and
        refuse the second, leaving a section half applied that the user never
        asked for and cannot see.
        """
        render(session,
               values={
                   "set_signal.fast_window_days": 20.0,
                   "set_signal.slow_window_days": 10.0,
                   },
               clicks={"settings_signal": True})

        assert stored_overrides(session) == {}

    def test_the_panel_draws_over_an_already_incoherent_set(self, session, render):
        """The user must be able to reach the control that fixes their mistake."""
        session.add(SignalSetting(key="signal.fast_window_days", value="200"))
        session.commit()

        fake = render(session)

        assert len(fake.controls) == len(PARAMETERS)


class TestResetting:
    """Getting back to the shipped values."""

    def test_the_reset_button_clears_everything(self, session, render):
        set_setting(session, "gates.min_score_delta", 2.5)
        set_setting(session, "regime.enabled", False)

        render(session, clicks={RESET: True})

        assert stored_overrides(session) == {}

    def test_resetting_nothing_says_so(self, session, render):
        fake = render(session, clicks={RESET: True})

        assert any("settings.reset_nothing" in str(c) for c in fake.calls)


class TestFormatting:
    """How a shipped value is shown back."""

    def test_a_boolean_reads_as_a_word(self, monkeypatch):
        monkeypatch.setattr(settings_widgets, "t", lambda key: key)
        param = next(p for p in PARAMETERS if p.kind == "bool")

        assert settings_widgets._fmt(param, True) == "settings.on"  # pylint: disable=protected-access
        assert settings_widgets._fmt(param, False) == "settings.off"  # pylint: disable=protected-access

    def test_a_figure_keeps_its_unit(self, monkeypatch):
        monkeypatch.setattr(settings_widgets, "t", lambda key: key)
        param = next(p for p in PARAMETERS if p.unit == "%")

        assert "%" in settings_widgets._fmt(param, 30.0)  # pylint: disable=protected-access

    def test_a_large_integer_is_grouped(self, monkeypatch):
        monkeypatch.setattr(settings_widgets, "t", lambda key: key)
        param = next(p for p in PARAMETERS if p.kind == "int")

        assert settings_widgets._fmt(param, 1000) .startswith("1 000")  # pylint: disable=protected-access

    def test_a_float_does_not_trail_zeros(self, monkeypatch):
        monkeypatch.setattr(settings_widgets, "t", lambda key: key)
        param = next(p for p in PARAMETERS if p.kind == "float" and not p.unit)

        assert settings_widgets._fmt(param, 1.5) == "1.5"  # pylint: disable=protected-access
