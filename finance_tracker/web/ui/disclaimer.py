"""The disclaimer, and where it has to appear.

Not decoration. The signal engine produces something that reads like advice —
a verdict, an amount, a target asset — and the closer output gets to that
shape, the more explicitly it has to say what it is not. So the banner sits at
the top of every page that shows a verdict, and a compact version rides along
with each swap plan, where the temptation to just follow the number is highest.
"""
import streamlit as st

from finance_tracker.i18n import t


def render_disclaimer(compact: bool = False) -> None:
    """Show the educational-purpose disclaimer.

    Parameters
    ----------
    compact : bool, optional
        True for the short form shown next to a swap plan, False for the full
        banner at the top of a page.
    """
    if compact:
        st.caption(f"⚠️ {t('disclaimer.compact')}")
        return

    st.warning(f"**{t('disclaimer.title')}**\n\n{t('disclaimer.body')}")


def render_disclaimer_expander() -> None:
    """Show the long form, folded, for a page that already carries the banner."""
    with st.expander(t("disclaimer.more_title"), expanded=False):
        st.markdown(t("disclaimer.long"))
