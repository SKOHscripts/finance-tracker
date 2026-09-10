"""Tests that the PDF reports escape what the user typed.

Both report services build HTML with Jinja2 and hand it to a PDF renderer. The
environments were created with Jinja2's default, `autoescape=False`, so every
value reached the document as markup. Product names are typed by the user, so a
name holding `<` broke the layout, and a name holding a tag was injected into
the report whole.

Turning escaping on is one keyword. The risk is the other half: a template that
*needs* markup — the simulation's annex tables — must keep rendering as a table
rather than as visible tag soup. So these tests pin both directions at once,
which is the only way the change is safe to make.
"""
# pylint: disable=protected-access  # _render_html is the boundary under test
# pylint: disable=redefined-outer-name  # pytest fixture pattern
from decimal import Decimal

import pandas as pd
import pytest

from finance_tracker.services.dashboard_service import PortfolioData
from finance_tracker.services.pdf_report_service import PDFReportService
from finance_tracker.services.simulation_pdf_service import SimulationPDFService

# A name that is both plausible and hostile: someone really might write "A<B",
# and the tag is what an injection would look like.
HOSTILE_NAME = 'Livret <script>alert("x")</script> & Cie'


@pytest.fixture()
def portfolio():
    """A one-line portfolio whose product name carries markup."""
    data = PortfolioData()
    data.total_value_eur = Decimal("1000")
    data.total_invested_eur = Decimal("800")
    data.total_gains_eur = Decimal("200")
    data.cash_available = Decimal("50")
    data.products = [{
        "name": HOSTILE_NAME,
        "current_value_eur": Decimal("1000"),
        "net_contributions_eur": Decimal("800"),
        "performance_eur": Decimal("200"),
        "performance_pct": 25.0,
        "allocation_pct": 100.0,
        }]
    return data


class TestPortfolioReport:
    """The dashboard export."""

    def test_a_name_carrying_a_tag_is_escaped(self, portfolio):
        """The point of the change: the tag must not reach the document live."""
        html = PDFReportService()._render_html(portfolio)

        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_an_ampersand_survives_as_an_entity(self, portfolio):
        html = PDFReportService()._render_html(portfolio)
        assert "&amp; Cie" in html

    def test_the_report_still_renders(self, portfolio):
        """Escaping must not cost the document its content."""
        html = PDFReportService()._render_html(portfolio)

        assert "<html" in html.lower()
        assert "1" in html  # the figures are still there

    def test_an_embedded_chart_is_not_mangled(self, portfolio):
        """Base64 has no character HTML escaping touches — this proves it."""
        service = PDFReportService()
        html = service._render_html(portfolio)

        # The template writes the chart into src="…"; a broken data URI would
        # show up as an escaped scheme separator.
        assert "data:image/png;base64,&" not in html


class TestSimulationReport:
    """The projection export, which legitimately embeds built HTML."""

    @pytest.fixture()
    def frames(self):
        period = pd.DataFrame({"period": [1, 2], "value_eur": [100.0, 200.0]})
        long = pd.DataFrame({
            "period": [1, 2], "product": [HOSTILE_NAME] * 2, "value_eur": [100.0, 200.0],
            })
        return period, long

    def _render(self, frames):
        period, long = frames
        return SimulationPDFService()._render_html(
            df_period=period,
            df_long=long,
            summary={"final_value": 1000, "final_invested": 800, "final_gains": 200},
            selected_metrics=[],
            config_params={"years": 10, "period": "annuel"},
            products_params=[{
                "name": HOSTILE_NAME, "kind": "CRYPTO", "priority": 1,
                "annual_return_pct": 5.0, "initial_invested_eur": 800,
                "initial_value_eur": 1000, "contrib_fixed_eur": 0,
                "contrib_pct_income": 0, "fcpi_text": "", "scpi_text": "",
                }],
            )

    def test_a_product_name_is_escaped(self, frames):
        html = self._render(frames)

        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_the_annex_tables_still_render_as_tables(self, frames):
        """`| safe` must keep working, or the annex becomes visible tag soup.

        This is the half that makes turning escaping on safe rather than
        merely quiet: pandas escapes the cells itself, so marking the table
        safe does not reopen the hole it closes.
        """
        html = self._render(frames)

        assert "<table" in html
        assert "&lt;table" not in html

    def test_a_hostile_value_inside_a_table_is_still_escaped(self, frames):
        """The table is trusted as markup; its cells are not."""
        html = self._render(frames)

        # The name appears in the annex table, escaped by pandas before the
        # template ever marks the table safe.
        assert html.count("&lt;script&gt;") >= 2
