"""Internationalisation helpers for Finance Tracker."""

import streamlit as st

from finance_tracker.i18n import fr, en

_LANGS: dict[str, dict[str, str]] = {
    "fr": fr.STRINGS,
    "en": en.STRINGS,
}

SUPPORTED_LANGS = list(_LANGS.keys())


def detect_language() -> str:
    """Detect the browser's preferred language from the Accept-Language header."""
    try:
        accept_lang: str = st.context.headers.get("Accept-Language", "fr")
        return "en" if accept_lang.lower().startswith("en") else "fr"
    except Exception:
        return "fr"


def t(key: str) -> str:
    """Return the UI string for *key* in the currently active language.

    Falls back to French if the key is missing in the active language,
    and returns the key itself as a last resort.
    """
    lang = st.session_state.get("lang", "fr")
    strings = _LANGS.get(lang, fr.STRINGS)
    return strings.get(key, fr.STRINGS.get(key, key))
