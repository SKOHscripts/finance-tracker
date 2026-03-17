"""PDF generation service for simulations."""

# Standard library
import base64
from datetime import datetime
from io import BytesIO
from pathlib import Path

# Third-party
import matplotlib.pyplot as plt
import pandas as pd
from weasyprint import HTML, CSS

# Local application
from finance_tracker.config import REPORTS_DIR, TEMPLATES_DIR


class SimulationPDFService:
    """PDF generation service for long-term simulations."""

    def __init__(self, templates_dir: Path = TEMPLATES_DIR, reports_dir: Path = REPORTS_DIR):
        self.templates_dir = templates_dir
        self.reports_dir = reports_dir

    def generate_report(self,
                        df_period: pd.DataFrame,
                        df_long: pd.DataFrame,
                        summary: dict,
                        selected_metrics: list,
                        config_params: dict,
                        products_params: list[dict]) -> bytes:
        """Generate a PDF simulation report and return it as bytes.

        Uses HTML as an intermediate format for PDF rendering.

        Parameters
        ----------
        df_period : pd.DataFrame
            DataFrame containing period-based data.
        df_long : pd.DataFrame
            DataFrame containing product data in long format.
        summary : dict
            Dictionary with final values (final_value, final_gains, etc.).
        selected_metrics : list
            List of metrics to display in charts.
        config_params : dict
            Dictionary of simulation parameters (years, inflation, etc.).
        products_params : list[dict]
            List of product configuration parameters.

        Returns
        -------
        bytes
            PDF document content as bytes.
        """
        # HTML serves as an intermediate format for PDF generation
        html_content = self._render_html(
            df_period=df_period,
            df_long=df_long,
            summary=summary,
            selected_metrics=selected_metrics,
            config_params=config_params,
            products_params=products_params,
            )
        # PDF library requires HTML input to render the final document

        return HTML(string=html_content).write_pdf()

    def _render_html(self,
                     df_period: pd.DataFrame,
                     df_long: pd.DataFrame,
                     summary: dict,
                     selected_metrics: list,
                     config_params: dict,
                     products_params: list[dict]) -> str:
        """Render Jinja2 simulation report template with formatted data and charts.

        Generates HTML tables, formats summary values with European separators,
        and embeds metric charts.

        Parameters
        ----------
        df_period : pd.DataFrame
            Period summary data for the simulation.
        df_long : pd.DataFrame
            Long format product data with historical values.
        summary : dict
            Summary statistics including final values, gains, and tax information.
        selected_metrics : list
            List of metric names to generate charts for.
        config_params : dict
            Configuration parameters including years, period, inflation, and income settings.
        products_params : list[dict]
            Product-specific parameters for the report.

        Returns
        -------
        str
            Rendered HTML report as string ready for display or export.

        Raises
        ------
        jinja2.TemplateNotFound
            If the Jinja2 template file cannot be located in the templates directory.
        jinja2.TemplateSyntaxError
            If the template contains invalid syntax.
        """
        from jinja2 import Environment, FileSystemLoader
        from finance_tracker.utils.money import format_eur

        # Template directory must be set at instance level for Jinja2 to locate files
        env = Environment(loader=FileSystemLoader(self.templates_dir))
        template = env.get_template("simulation_report.html")

        # Generate charts only for metrics present in data to avoid empty/broken images
        charts_base64 = {}

        for metric in selected_metrics:
            if metric in df_long.columns:
                chart_img = self._generate_metric_chart(df_long, metric)

                if chart_img:
                    charts_base64[metric] = chart_img

        # Large row limits ensure complete data export for detailed analysis
        periods_html = self._dataframe_to_html_table(df_period, max_rows=2000)
        products_html = self._dataframe_to_html_table(df_long, max_rows=2000)

        return template.render(
            generated_at=datetime.utcnow().strftime("%d/%m/%Y %H:%M"),
            # Format summary values with space as thousand separator for European readability
            final_value=f"{summary.get('final_value', 0):,.0f}".replace(",", " "),
            final_value_real=f"{summary.get('final_value_real', 0):,.0f}".replace(",", " "),
            final_invested=f"{summary.get('final_invested', 0):,.0f}".replace(",", " "),
            final_gains=f"{summary.get('final_gains', 0):,.0f}".replace(",", " "),
            # Calculate percentage only when invested amount exists to avoid division by zero
            gains_pct=(
                f"{(summary.get('final_gains', 0) / summary.get('final_invested', 1) * 100):.2f}%"

                if summary.get('final_invested', 0) > 0
                else "0.00%"
                ),
            tax_due_next_year=f"{summary.get('tax_due_next_year', 0):,.0f}".replace(",", " "),
            # Pass config params for display in report header/summary section
            config_years=config_params.get("years", "N/A"),
            config_period=config_params.get("period", "N/A"),
            config_inflation=f"{config_params.get('inflation_pct', 0):.1f}%",
            config_inflation_profile=config_params.get("inflation_profile", ""),
            config_income_start=f"{config_params.get('income_start', 0):,.0f}".replace(",", " "),
            config_income_growth=f"{config_params.get('income_growth_pct', 0):.1f}%",
            config_living_costs=f"{config_params.get('annual_living_costs', 0):,.0f}".replace(",", " "),
            # Include generated charts and metadata for template rendering
            charts=charts_base64,
            metrics_count=len(selected_metrics),
            # Embed full tables as HTML for detailed reference in annexes
            periods_table_html=periods_html,
            products_table_html=products_html,
            products_params=products_params,
            )

    # Translates internal metric keys into user-friendly French labels for display
    _METRIC_LABELS: dict[str, str] = {
        "value_eur": "Valeur (€)",
        "value_real_eur": "Valeur réelle inflation (€)",
        "invested_cum_eur": "Investi cumulé (€)",
        "gains_eur": "Gains (€)",
        "contrib_period_eur": "Contributions par période (€)",
        "dividends_period_eur": "Dividendes par période (€)",
        "redemption_period_eur": "Remboursements FCPI (€)",
        "scpi_parts": "Parts SCPI détenues",
        }

    def _generate_metric_chart(self, df_long: pd.DataFrame, metric: str) -> str:
        """Generate a base64-encoded chart for a given metric.

        Displays all curves with final value labels and uses a push-up/push-down
        algorithm to prevent label overlap.

        Parameters
        ----------
        df_long : pd.DataFrame
            DataFrame containing long-format data with columns for product, period,
            and the metric values.
        metric : str
            Name of the metric column to plot.

        Returns
        -------
        str or None
            Base64-encoded PNG image as data URI, or None if generation fails.

        Raises
        ------
        Exception
            Catches and prints any errors during chart generation, returns None on
            failure.
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.ticker as mtick
            import numpy as np

            # Palette: tab20 supports up to 20 distinct colors for multiple product lines
            N_MAX = 20
            cmap = plt.cm.get_cmap("tab20", N_MAX)
            palette = [cmap(i) for i in range(N_MAX)]

            fig, ax = plt.subplots(figsize=(13, 6))
            fig.patch.set_facecolor("white")
            ax.set_facecolor("#f5f6f8")

            # Detect metric type to apply appropriate formatting and scaling
            ml = metric.lower()
            is_eur = ml.endswith("_eur") or any(
                kw in ml for kw in ("value", "gains", "contrib", "dividend", "tax", "cash", "invest", "redempt")
                )
            is_count = "parts" in ml or ml.endswith("_count")

            # Determine Y-axis scale: use k€ or M€ for large EUR values to improve readability
            series = df_long[metric].dropna() if metric in df_long.columns else pd.Series([], dtype=float)
            max_abs = float(series.abs().max()) if not series.empty else 1.0

            if is_eur:
                if max_abs >= 1_000_000:
                    scale, unit = 1_000_000, "M€"
                elif max_abs >= 1_000:
                    scale, unit = 1_000, "k€"
                else:
                    scale, unit = 1, "€"
            elif is_count:
                scale, unit = 1, "parts"
            else:
                if max_abs >= 1_000_000:
                    scale, unit = 1_000_000, "M"
                elif max_abs >= 1_000:
                    scale, unit = 1_000, "k"
                else:
                    scale, unit = 1, ""

            def fmt_val(v: float, short: bool = False) -> str:
                """Format a raw numeric value for display.

                Converts a raw value to a human-readable string representation,
                applying appropriate scaling and European-style formatting with
                space as thousands separator.

                Parameters
                ----------
                v : float
                    The raw numeric value to format.
                short : bool, optional
                    Whether to use short format (default False).

                Returns
                -------
                str
                    The formatted string representation with unit suffix, or
                    empty string if value is None or NaN.
                """

                if v is None or (isinstance(v, float) and np.isnan(v)):
                    return ""
                vv = float(v) / scale

                if is_count:
                    return f"{int(round(vv))} {unit}".strip()

                # Use space as thousands separator for European formatting preference

                if abs(vv) >= 1_000:
                    s = f"{vv:,.0f}".replace(",", " ")
                elif abs(vv) >= 10:
                    s = f"{vv:.1f}"
                else:
                    s = f"{vv:.2f}"

                return f"{s} {unit}".strip() if unit else s

            ax.yaxis.set_major_formatter(
                mtick.FuncFormatter(lambda x, _: fmt_val(x, short=True))
                )

            # Infer periodicity from data: detect if monthly (12), quarterly (4), or annual (1)
            n_per_year = 12

            if "year" and "period" in df_long.columns:
                try:
                    n_per_year = int(df_long[df_long["year"] == 1]["period"].nunique())

                    if n_per_year not in (1, 4, 12):
                        n_per_year = int(df_long.groupby("year")["period"].nunique().mode().iloc[0])
                except Exception:
                    pass

            max_period = int(df_long["period"].max()) if not df_long.empty else 0

            # Configure X-axis: show year labels for periodic data, otherwise use auto-scaling

            if n_per_year in (4, 12) and max_period > 0:
                year_ticks = list(range(n_per_year, max_period + 1, n_per_year))
                ax.xaxis.set_major_locator(mtick.FixedLocator(year_ticks))
                ax.xaxis.set_major_formatter(
                    mtick.FuncFormatter(lambda x, _: f"An {int(round(x / n_per_year))}")
                    )

                # Add quarterly markers for monthly data, yearly markers for quarterly

                if n_per_year == 12:
                    ax.xaxis.set_minor_locator(mtick.MultipleLocator(3))
                else:
                    ax.xaxis.set_minor_locator(mtick.MultipleLocator(1))
            else:
                ax.xaxis.set_major_locator(mtick.MaxNLocator(nbins=10, integer=True))
                ax.xaxis.set_minor_locator(mtick.AutoMinorLocator())

            ax.tick_params(axis="x", labelrotation=0, labelsize=8.5)
            ax.tick_params(axis="y", labelsize=8.5)

            # Plot each product as a separate line with consistent coloring
            products_all = list(df_long["product"].dropna().unique())
            end_labels: list[dict] = []

            for idx, product in enumerate(products_all):
                color = palette[idx % N_MAX]
                pdata = df_long[df_long["product"] == product].sort_values("period")

                if metric not in pdata.columns or pdata[metric].isna().all():
                    continue

                x = pdata["period"].to_numpy(dtype=float)
                y = pdata[metric].to_numpy(dtype=float)
                mask = ~np.isnan(y)

                if not mask.any():
                    continue

                ax.plot(
                    x[mask], y[mask],
                    color=color, label=str(product),
                    linewidth=2.0, alpha=0.92,
                    solid_capstyle="round",
                    )

                # Capture terminal point for label placement
                x_end, y_end = float(x[mask][-1]), float(y[mask][-1])
                ax.plot(x_end, y_end, "o", color=color, markersize=5, zorder=6)

                end_labels.append({
                    "x": x_end,
                    "y_raw": y_end,
                    "text": f"{product}: {fmt_val(y_end)}",
                    "color": color,
                    })

            # Resolve label overlap using push-up then push-down passes
            # This ensures labels spread outward from their original positions

            if end_labels:
                # Get Y-axis bounds after plotting to calculate relative spacing
                ax.autoscale(axis="y", tight=False)
                y_lo, y_hi = ax.get_ylim()
                y_span = max(y_hi - y_lo, 1.0)
                # Minimum gap: ~3% of Y range to prevent visual crowding
                gap = y_span * 0.032

                # Sort by raw Y value to process in order
                end_labels.sort(key=lambda d: d["y_raw"])
                positions = [d["y_raw"] for d in end_labels]

                # Upward pass: push overlapping labels upward

                for i in range(1, len(positions)):
                    if positions[i] - positions[i - 1] < gap:
                        positions[i] = positions[i - 1] + gap

                # Downward pass: push overlapping labels downward to recover space

                for i in range(len(positions) - 2, -1, -1):
                    if positions[i + 1] - positions[i] < gap:
                        positions[i] = positions[i + 1] - gap

                # Offset labels horizontally to the right of the terminal points
                x_offset = max_period * 0.018 if max_period > 0 else 2

                for i, d in enumerate(end_labels):
                    y_adj = positions[i]
                    # Draw connector line only when label position differs significantly from original
                    # This visual cue helps readers trace the label back to its data point

                    if abs(y_adj - d["y_raw"]) > y_span * 0.004:
                        ax.plot(
                            [d["x"], d["x"] + x_offset * 0.6],
                            [d["y_raw"], y_adj],
                            color=d["color"], linewidth=0.6,
                            alpha=0.55, linestyle=":",
                            )

                    ax.annotate(
                        d["text"],
                        xy=(d["x"], d["y_raw"]),
                        xytext=(d["x"] + x_offset, y_adj),
                        fontsize=7.5,
                        color=d["color"],
                        fontweight="semibold",
                        va="center",
                        annotation_clip=False,
                        bbox=dict(
                            boxstyle="round,pad=0.3",
                            facecolor="white",
                            edgecolor=d["color"],
                            alpha=0.88,
                            linewidth=0.8,
                            ),
                        )

            # Clean visual style: remove top and right spines for modern look
            ax.grid(True, which="major", linestyle="-", linewidth=0.5, alpha=0.55, color="#c0c0c0")
            ax.grid(True, which="minor", linestyle=":", linewidth=0.4, alpha=0.35, color="#d8d8d8")
            ax.minorticks_on()
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            for sp in ["left", "bottom"]:
                ax.spines[sp].set_edgecolor("#aaaaaa")

            # Title uses friendly label if available, otherwise capitalizes metric name
            friendly = self._METRIC_LABELS.get(metric, metric.replace("_", " ").title())
            ax.set_title(friendly, fontsize=13, fontweight="bold", pad=14, color="#1a1a2e")
            ax.set_xlabel("Année", fontsize=9.5, color="#555555")

            if unit:
                ax.set_ylabel(unit, fontsize=9.5, color="#555555")

            # Legend layout: increase columns for many products to avoid vertical scrolling
            n_prod = len(products_all)
            ncol = min(max(n_prod, 1), 5)
            ax.legend(
                fontsize=8, loc="upper left", ncol=ncol,
                framealpha=0.92, edgecolor="#cccccc",
                fancybox=True, labelspacing=0.4,
                )

            # Adjust right margin based on product count: more products need more space for labels
            right_margin = 0.75 if n_prod > 3 else 0.82
            plt.subplots_adjust(right=right_margin, left=0.09, top=0.90, bottom=0.10)

            img_buffer = BytesIO()
            plt.savefig(img_buffer, format="png", dpi=160, bbox_inches="tight")
            img_buffer.seek(0)
            img_b64 = base64.b64encode(img_buffer.read()).decode()
            plt.close(fig)

            return f"data:image/png;base64,{img_b64}"

        except Exception as e:
            print(f"Erreur génération graphique {metric}: {e}")
            try:
                plt.close("all")
            except Exception:
                pass

            return None

    def _dataframe_to_html_table(self, df: pd.DataFrame, max_rows: int = 100) -> str:
        """Convert a pandas DataFrame to an HTML table.

        Formats columns with '_eur' or 'value' in their names as formatted
        numbers and limits the number of rows displayed.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to convert to HTML.
        max_rows : int, optional
            Maximum number of rows to display (default is 100).

        Returns
        -------
        str
            HTML string representation of the DataFrame.
        """

        if df.empty:
            return "<p>Aucune donnée</p>"

        # Prevent rendering massive tables that freeze the browser
        display_df = df.head(max_rows).copy()

        # Format currency/value columns with thousand separators for readability

        for col in display_df.columns:
            if "_eur" in col.lower() or "value" in col.lower():
                try:
                    # Use non-breaking space as separator, handle NaN gracefully
                    display_df[col] = display_df[col].apply(
                        lambda x: f"{float(x):,.0f}".replace(",", " ") if pd.notna(x) else ""
                        )
                except:
                    pass

        html = display_df.to_html(
            index=False,
            classes="table table-striped table-small",
            float_format=lambda x: f"{x:.2f}" if pd.notna(x) else "",
            border=0,
            )

        # Inform user when results were truncated

        if len(df) > max_rows:
            html += f"<p style='font-size: 0.8em; color: #666;'>... ({len(df) - max_rows} lignes omises)</p>"

        return html
