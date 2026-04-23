"""PDF generation service."""

# Standard library
import base64
from datetime import datetime
from io import BytesIO
from pathlib import Path

# Third-party
import matplotlib.pyplot as plt
from weasyprint import HTML, CSS

# Local application
from finance_tracker.config import REPORTS_DIR, TEMPLATES_DIR
from finance_tracker.services.dashboard_service import PRODUCT_COLORS, PortfolioData
from finance_tracker.utils.money import format_eur


class PDFReportService:
    """Service for generating PDF reports."""

    def __init__(self, templates_dir: Path = TEMPLATES_DIR, reports_dir: Path = REPORTS_DIR):
        self.templates_dir = templates_dir
        self.reports_dir = reports_dir

    def generate_report(self, portfolio: PortfolioData, products_with_charts: list | None = None) -> str:
        """Generate a PDF report and save it to disk.

        Parameters
        ----------
        portfolio : PortfolioData
            Portfolio data to export as PDF.
        products_with_charts : list | None
            Optional list of per-product detail dicts (from DashboardService.get_product_details)
            to include per-product valuation charts in the report.

        Returns
        -------
        str
            Path to the generated PDF file.
        """
        # Render template to HTML first, then convert to PDF
        html_content = self._render_html(portfolio, products_with_charts)

        # Use timestamp in filename to ensure uniqueness and traceability
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
        filename = f"report_{timestamp}.pdf"
        filepath = self.reports_dir / filename

        # Write PDF directly to disk (weasyprint requires a file path)
        HTML(string=html_content).write_pdf(str(filepath))

        return str(filepath)

    def _render_html(self, portfolio: PortfolioData, products_with_charts: list | None = None) -> str:
        """Render portfolio data using Jinja2 template.

        Parameters
        ----------
        portfolio : PortfolioData
            Portfolio data to render.
        products_with_charts : list | None
            Optional per-product detail dicts for chart sections.

        Returns
        -------
        str
            Rendered HTML content.
        """
        from jinja2 import Environment, FileSystemLoader
        from finance_tracker.utils.money import format_eur

        env = Environment(loader=FileSystemLoader(self.templates_dir))
        template = env.get_template("report.html")

        # Calculate percentage manually to handle zero division edge case
        total_gains_pct = (
            f"{(portfolio.total_gains_eur / portfolio.total_invested_eur * 100):.2f}%"

            if portfolio.total_invested_eur > 0
            else "0.00%"
            )

        # Generate charts as base64 images to embed directly in HTML
        chart_allocation = self._generate_allocation_chart(portfolio.products)
        chart_performance = self._generate_performance_chart(portfolio.products)

        # Build per-product chart data for the template
        product_chart_data = []
        if products_with_charts:
            for details in products_with_charts:
                if not details.get("history") or len(details["history"]) < 2:
                    continue
                chart_b64 = self._generate_product_history_chart(
                    details["name"],
                    details["history"],
                    details.get("pru"),
                    details.get("color", "#6B7280"),
                    )
                gains_class = "positive" if details["gains_eur"] >= 0 else "negative"
                product_chart_data.append({
                    "name": details["name"],
                    "current_value": format_eur(details["current_value"]),
                    "net_invested": format_eur(details["net_invested"]),
                    "pru": format_eur(details["pru"]) if details.get("pru") else "—",
                    "gains_eur": format_eur(details["gains_eur"]),
                    "gains_pct": f"{details['gains_pct']:.2f}%",
                    "gains_class": gains_class,
                    "chart_base64": chart_b64,
                    })

        # Pass both raw values and formatted strings to template
        # Raw values enable calculations in template if needed

        return template.render(
            generated_at=datetime.utcnow().strftime("%d/%m/%Y %H:%M"),
            total_value_eur=format_eur(portfolio.total_value_eur),
            total_invested_eur=format_eur(portfolio.total_invested_eur),
            total_gains_eur=portfolio.total_gains_eur,  # Raw Decimal for potential calculations
            total_gains_eur_formatted=format_eur(portfolio.total_gains_eur),
            total_gains_pct=total_gains_pct,  # Pre-formatted string
            total_gains_class="positive" if portfolio.total_gains_eur >= 0 else "negative",  # CSS class for styling
            cash_available=format_eur(portfolio.cash_available),
            chart_allocation=chart_allocation,
            chart_performance=chart_performance,
            products=[
                {
                    "name": p["name"],
                    "current_value_eur": p["current_value_eur"],
                    "net_contributions_eur": p["net_contributions_eur"],
                    "performance_eur": p["performance_eur"],  # Raw Decimal
                    "performance_eur_formatted": format_eur(p["performance_eur"]),
                    "performance_pct": f"{p['performance_pct']:.2f}%",
                    "allocation_pct": f"{p['allocation_pct']:.2f}%",
                    "performance_class": "positive" if p["performance_eur"] >= 0 else "negative",
                    }

                for p in portfolio.products
                ],
            products_with_charts=product_chart_data,
            )

    def _generate_allocation_chart(self, products: list) -> str:
        """Generate a donut chart showing allocation by product.

        Parameters
        ----------
        products : list
            List of products with their current values.

        Returns
        -------
        str
            Base64-encoded PNG image data URL.
        """
        import matplotlib as mpl

        # Extract non-zero values only (zero values distort the chart)
        items = [(p["name"], float(p["current_value_eur"])) for p in products]
        items = [(n, v) for (n, v) in items if v > 0]

        if not items:
            return ""

        # Sort by value descending and group small slices into "Autres" for readability
        items.sort(key=lambda x: x[1], reverse=True)
        max_slices = 8

        if len(items) > max_slices:
            top = items[: max_slices - 1]
            other_sum = sum(v for _, v in items[max_slices - 1:])
            items = top + [("Autres", other_sum)]

        labels = [n for n, _ in items]
        sizes = [v for _, v in items]
        total = sum(sizes)

        # Use muted color palette for professional look
        mpl.rcParams.update({
            "font.size": 10,
            "axes.titlesize": 12,
            "text.color": "#111827",
            "axes.labelcolor": "#111827",
            })

        fig, ax = plt.subplots(figsize=(10, 5.6), dpi=160)
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        # Generate blue gradient from light to dark
        colors = plt.cm.Blues([0.35, 0.45, 0.55, 0.62, 0.70, 0.78, 0.86, 0.92, 0.97])[:len(labels)]

        def autopct(pct):
            # Only show percentage if significant (>3%) to avoid visual clutter

            return f"{pct:.0f}%" if pct >= 3 else ""

        wedges, texts, autotexts = ax.pie(
            sizes,
            startangle=90,
            counterclock=False,
            colors=colors,
            autopct=autopct,
            pctdistance=0.78,
            wedgeprops=dict(width=0.42, edgecolor="white", linewidth=1.2),  # Create donut hole
            textprops=dict(color="#111827", fontsize=9),
            )

        # Build legend with name, amount and percentage for clarity
        legend_labels = [
            f"{name} — {value:,.0f}€ ({(value / total * 100):.1f}%)".replace(",", " ")

            for name, value in items
            ]
        ax.legend(
            wedges,
            legend_labels,
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
            fontsize=9,
            )

        ax.set_title("Répartition du portefeuille", pad=14)
        ax.set(aspect="equal")

        plt.tight_layout()

        # Encode to base64 for inline embedding in HTML
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format="png", bbox_inches="tight")
        img_buffer.seek(0)
        img_str = base64.b64encode(img_buffer.read()).decode()
        plt.close(fig)

        return f"data:image/png;base64,{img_str}"

    def _generate_performance_chart(self, products: list) -> str:
        """Generate a horizontal bar chart showing performance by product.

        Parameters
        ----------
        products : list
            List of products with their performance metrics.

        Returns
        -------
        str
            Base64-encoded PNG image data URL.
        """
        import matplotlib as mpl

        # Exclude cash from performance chart (cash has no performance metric)
        prods = [p for p in products if p["name"].lower() != "cash"]
        data = [(p["name"], float(p["performance_pct"])) for p in prods]

        if not data:
            return ""

        # Sort best performers at top (reverse order for horizontal bar)
        data.sort(key=lambda x: x[1], reverse=True)
        labels = [n for n, _ in data]
        values = [v for _, v in data]

        mpl.rcParams.update({
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.edgecolor": "#E5E7EB",
            "axes.labelcolor": "#111827",
            "xtick.color": "#6B7280",
            "ytick.color": "#111827",
            })

        fig, ax = plt.subplots(figsize=(10, 6), dpi=160)
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        # Green for gains, red for losses
        colors = ["#16A34A" if v >= 0 else "#DC2626" for v in values]

        y = range(len(labels))
        bars = ax.barh(y, values, color=colors, edgecolor="none", height=0.6)

        # Add zero line and light grid for reference
        ax.axvline(0, color="#111827", linewidth=1.0, alpha=0.6)
        ax.xaxis.grid(True, color="#E5E7EB", linewidth=1.0, alpha=0.8)
        ax.set_axisbelow(True)

        ax.set_yticks(list(y))
        ax.set_yticklabels(labels, fontsize=9)
        ax.invert_yaxis()  # Best performers at top

        ax.set_xlabel("Performance (%)")
        ax.set_title("Performance par produit", pad=14)

        # Position value labels outside bars, adjusting side based on sign

        for bar, v in zip(bars, values):
            x = bar.get_width()
            y_text = bar.get_y() + bar.get_height() / 2

            if v >= 0:
                ax.text(x + 0.3, y_text, f"{v:.1f}%", va="center", ha="left", fontsize=9, color="#111827")
            else:
                ax.text(x - 0.3, y_text, f"{v:.1f}%", va="center", ha="right", fontsize=9, color="#111827")

        # Dynamic padding ensures labels don't get clipped regardless of value range
        xmin = min(values) if values else -1
        xmax = max(values) if values else 1
        pad = max(2.0, (xmax - xmin) * 0.12)
        ax.set_xlim(xmin - pad, xmax + pad)

        # Remove unnecessary frame borders for cleaner look

        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)

        plt.tight_layout()

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format="png", bbox_inches="tight")
        img_buffer.seek(0)
        img_str = base64.b64encode(img_buffer.read()).decode()
        plt.close(fig)

        return f"data:image/png;base64,{img_str}"

    def _generate_product_history_chart(
        self,
        product_name: str,
        history: list[dict],
        pru: float | None,
        color: str = "#008080",
    ) -> str:
        """Generate a line chart for a product's valuation history with optional PRU line.

        Returns base64-encoded PNG data URL.
        """
        import matplotlib as mpl
        import matplotlib.dates as mdates

        dates = [h["date"] for h in history]
        values = [h["total_value_eur"] for h in history]

        mpl.rcParams.update({
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.edgecolor": "#E5E7EB",
            "axes.labelcolor": "#333",
            "xtick.color": "#666",
            "ytick.color": "#333",
            })

        fig, ax = plt.subplots(figsize=(10, 4), dpi=160)
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        ax.plot(dates, values, color=color, linewidth=2.2, marker="o", markersize=4, zorder=3)
        ax.fill_between(dates, values, alpha=0.10, color=color, zorder=2)

        if pru is not None:
            ax.axhline(y=pru, color="#6366f1", linewidth=1.6, linestyle="--", zorder=2, label=f"PRU ({pru:,.0f} €)")
            ax.legend(loc="upper left", fontsize=9, frameon=False)

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate(rotation=30)

        ax.yaxis.grid(True, color="#E5E7EB", linewidth=0.8, alpha=0.8)
        ax.set_axisbelow(True)

        ax.set_ylabel("Valeur (€)")
        ax.set_title(f"Historique — {product_name}", pad=12)

        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)

        plt.tight_layout()

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format="png", bbox_inches="tight")
        img_buffer.seek(0)
        img_str = base64.b64encode(img_buffer.read()).decode()
        plt.close(fig)

        return f"data:image/png;base64,{img_str}"
