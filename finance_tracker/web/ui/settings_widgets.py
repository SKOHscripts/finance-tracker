"""The panel that lets a user move a rotation threshold.

Exposing thresholds is only useful if the reader can state what each one does.
A figure they cannot explain is a figure they cannot set responsibly, and the
whole reason the engine shows its barriers rather than a verdict alone is that
the arbitrage should stay theirs. So every control here carries the sentence
that says what it changes, and a moved threshold is marked as moved with its
shipped value alongside — otherwise a portfolio slowly acquires settings nobody
remembers choosing.

Saving is per section rather than per field. A threshold is only ever right in
relation to the others (a fast window has to stay shorter than a slow one), so
the whole section is validated together and refused together.
"""
import streamlit as st

from finance_tracker.i18n import t
from finance_tracker.services.crypto.settings import (
    SECTION_ORDER,
    SettingsError,
    describe,
    parameters_by_section,
    reset_all,
    set_many,
    )


def _fmt(param, value) -> str:
    """Render a value the way the control shows it."""
    if param.kind == "bool":
        return t("settings.on") if value else t("settings.off")
    if param.kind == "int":
        return f"{int(value):,}".replace(",", " ") + (f" {param.unit}" if param.unit else "")
    text = f"{float(value):,.4f}".rstrip("0").rstrip(".").replace(",", " ")
    return text + (f" {param.unit}" if param.unit else "")


def _control(param, value, default):
    """Draw the widget for one parameter, with its role stated underneath.

    The label carries the sentence as Streamlit help; the caption below repeats
    the shipped value when the current one differs, so a moved threshold is
    never silently different from what the documentation describes.
    """
    label = t(param.label_key)
    if param.kind == "bool":
        new = st.checkbox(label, value=bool(value), help=t(param.help_key),
                          key=f"set_{param.key}")
    else:
        step = param.step if param.step is not None else 0.1
        new = st.number_input(
            label,
            value=float(value),
            min_value=float(param.minimum) if param.minimum is not None else None,
            max_value=float(param.maximum) if param.maximum is not None else None,
            step=float(step),
            help=t(param.help_key),
            key=f"set_{param.key}",
            )
        if param.kind == "int":
            new = int(round(new))

    st.caption(t(param.help_key))
    if value != default:
        st.caption(f"↩︎ {t('settings.default_is').format(value=_fmt(param, default))}")

    return new


def render_settings(session) -> bool:
    """Draw the whole panel. Returns whether anything was written."""
    rows = {entry["param"].key: entry for entry in describe(session)}
    grouped = parameters_by_section()
    moved = sum(1 for entry in rows.values() if entry["changed"])

    st.caption(t("settings.help"))
    if moved:
        st.info(t("settings.moved_count").format(n=moved))

    written = False

    for section in SECTION_ORDER:
        params = grouped.get(section, ())
        if not params:
            continue

        section_moved = sum(1 for p in params if rows[p.key]["changed"])
        title = t(f"section.{section}")
        if section_moved:
            title = f"{title} · ✍️ {section_moved}"

        with st.expander(title, expanded=False):
            st.caption(t(f"sectionhelp.{section}"))

            with st.form(f"settings_{section}"):
                typed = {}
                for param in params:
                    entry = rows[param.key]
                    typed[param.key] = _control(param, entry["value"], entry["default"])
                    st.markdown("")

                if st.form_submit_button(t("settings.save_section"), width="stretch"):
                    try:
                        # One call, so a refusal leaves the section untouched
                        # rather than applied up to the offending field.
                        set_many(session, typed)
                    except SettingsError as exc:
                        st.error(str(exc))
                    else:
                        written = True
                        st.success(t("settings.saved"))

    if st.button(t("settings.reset_all"), width="stretch"):
        dropped = reset_all(session)
        written = True
        if dropped:
            st.success(t("settings.reset_done").format(n=dropped))
        else:
            st.info(t("settings.reset_nothing"))

    return written
