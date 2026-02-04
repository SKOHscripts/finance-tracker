"""Service génération PDF pour les simulations."""

from datetime import datetime
from pathlib import Path
from weasyprint import HTML, CSS
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import pandas as pd
from finance_tracker.config import REPORTS_DIR, TEMPLATES_DIR


class SimulationPDFService:
    """Service de génération de PDF pour simulations long terme."""

    def __init__(self, templates_dir: Path = TEMPLATES_DIR, reports_dir: Path = REPORTS_DIR):
        self.templates_dir = templates_dir
        self.reports_dir = reports_dir

    def generate_report(
        self,
        df_period: pd.DataFrame,
        df_long: pd.DataFrame,
        summary: dict,
        selected_metrics: list,
        config_params: dict,
        products_params: list[dict],   # <-- AJOUT
    ) -> bytes:
        """Génère un PDF rapport simulation et le retourne en bytes.

        Args:
            df_period: DataFrame des données par période
            df_long: DataFrame des données par produit (long format)
            summary: Dict avec valeurs finales (final_value, final_gains, etc.)
            selected_metrics: Liste des métriques à afficher en graphiques
            config_params: Dict des paramètres de simulation (années, inflation, etc.)

        Returns:
            Bytes du PDF
        """
        # Générer HTML
        html_content = self._render_html(
            df_period=df_period,
            df_long=df_long,
            summary=summary,
            selected_metrics=selected_metrics,
            config_params=config_params,
            products_params=products_params,  # <-- AJOUT
        )
        # Convertir en PDF

        return HTML(string=html_content).write_pdf()

    def _render_html(
        self,
        df_period: pd.DataFrame,
        df_long: pd.DataFrame,
        summary: dict,
        selected_metrics: list,
        config_params: dict,
        products_params: list[dict],   # <-- AJOUT
    ) -> str:
        """Rendu template Jinja2 avec données simulation."""
        from jinja2 import Environment, FileSystemLoader
        from finance_tracker.utils.money import format_eur

        env = Environment(loader=FileSystemLoader(self.templates_dir))
        template = env.get_template("simulation_report.html")

        # Générer graphiques en base64
        charts_base64 = {}

        for metric in selected_metrics:
            if metric in df_long.columns:
                chart_img = self._generate_metric_chart(df_long, metric)

                if chart_img:
                    charts_base64[metric] = chart_img

        # Préparer données pour tableaux HTML
        periods_html = self._dataframe_to_html_table(df_period, max_rows=2000)
        products_html = self._dataframe_to_html_table(df_long, max_rows=2000)

        return template.render(
            generated_at=datetime.utcnow().strftime("%d/%m/%Y %H:%M"),
            # Résumé
            final_value=f"{summary.get('final_value', 0):,.0f}".replace(",", " "),
            final_value_real=f"{summary.get('final_value_real', 0):,.0f}".replace(",", " "),
            final_invested=f"{summary.get('final_invested', 0):,.0f}".replace(",", " "),
            final_gains=f"{summary.get('final_gains', 0):,.0f}".replace(",", " "),
            gains_pct=(
                f"{(summary.get('final_gains', 0) / summary.get('final_invested', 1) * 100):.2f}%"

                if summary.get('final_invested', 0) > 0
                else "0.00%"
            ),
            tax_due_next_year=f"{summary.get('tax_due_next_year', 0):,.0f}".replace(",", " "),
            # Paramètres de simulation
            config_years=config_params.get("years", "N/A"),
            config_period=config_params.get("period", "N/A"),
            config_inflation=f"{config_params.get('inflation_pct', 0):.1f}%",
            config_income_start=f"{config_params.get('income_start', 0):,.0f}".replace(",", " "),
            config_income_growth=f"{config_params.get('income_growth_pct', 0):.1f}%",
            config_living_costs=f"{config_params.get('annual_living_costs', 0):,.0f}".replace(",", " "),
            # Graphiques
            charts=charts_base64,
            metrics_count=len(selected_metrics),
            # Tableaux (annexes)
            periods_table_html=periods_html,
            products_table_html=products_html,
            products_params=products_params,  # <-- AJOUT
        )

    def _generate_metric_chart(self, df_long: pd.DataFrame, metric: str) -> str:
        """Génère un graphique pour une métrique en base64.
        - Toutes les courbes
        - Étiquettes (début/milieu/fin) seulement sur les top 3 produits si >3 produits
        - X axis: ticks "fin d'année" (12/24/36 en mensuel, 4/8/12 en trimestriel)
        """
        try:
            import matplotlib.ticker as mtick

            plt.figure(figsize=(10, 5))
            ax = plt.gca()

            # ---------- Helpers format ----------
            metric_l = metric.lower()
            is_eur = (
                metric_l.endswith("_eur")
                or "value" in metric_l
                or "gains" in metric_l
                or "contrib" in metric_l
                or "dividend" in metric_l
                or "tax" in metric_l
                or "cash" in metric_l
            )
            is_count = ("parts" in metric_l) or metric_l.endswith("_count")

            # Échelle Y + unité (k/M) pour éviter les valeurs brutes illisibles
            series = df_long[metric].dropna() if metric in df_long.columns else pd.Series([], dtype=float)
            max_abs = float(series.abs().max()) if not series.empty else 0.0

            if is_eur:
                if max_abs >= 1_000_000:
                    scale, unit = 1_000_000, "M€"
                elif max_abs >= 1_000:
                    scale, unit = 1_000, "k€"
                else:
                    scale, unit = 1, "€"
            elif is_count:
                scale, unit = 1, ""  # "nb" sera mis dans le label d'axe
            else:
                if max_abs >= 1_000_000:
                    scale, unit = 1_000_000, "M"
                elif max_abs >= 1_000:
                    scale, unit = 1_000, "k"
                else:
                    scale, unit = 1, ""

            def fmt_scaled(v: float, for_tick: bool = False) -> str:
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    return ""
                vv = float(v) / scale if scale else float(v)

                if is_count:
                    return f"{int(round(vv))}"
                # ticks plus courts

                if for_tick:
                    if abs(vv) >= 100:
                        s = f"{vv:,.0f}".replace(",", " ")
                    elif abs(vv) >= 10:
                        s = f"{vv:,.1f}".replace(",", " ")
                    else:
                        s = f"{vv:,.2f}".replace(",", " ")
                else:
                    # annotations un peu plus lisibles
                    s = f"{vv:,.2f}".replace(",", " ") if abs(vv) < 100 else f"{vv:,.0f}".replace(",", " ")

                return s + (unit if unit else "")

            ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, pos: fmt_scaled(x, for_tick=True)))  # [web:176][web:179]

            # ---------- X axis: ticks "fin d'année" ----------
            # On infère n_per_year depuis les données (colonne year)
            # Exemple: year=1 a 12 periods uniques => mensuel.
            n_per_year = None

            if "year" in df_long.columns and "period" in df_long.columns:
                try:
                    n_per_year = int(df_long[df_long["year"] == 1]["period"].nunique())
                except Exception:
                    n_per_year = None

            if n_per_year not in (1, 4, 12):
                # fallback: mode sur toutes les années
                try:
                    n_per_year = int(df_long.groupby("year")["period"].nunique().mode().iloc[0])
                except Exception:
                    n_per_year = 12

            max_period = int(df_long["period"].max()) if "period" in df_long.columns and not df_long.empty else 0

            if n_per_year in (4, 12) and max_period > 0:
                year_ticks = list(range(n_per_year, max_period + 1, n_per_year))
                ax.xaxis.set_major_locator(mtick.FixedLocator(year_ticks))
                ax.xaxis.set_major_formatter(
                    mtick.FuncFormatter(lambda x, pos: f"Année {int(round(x / n_per_year))}")
                )  # [web:176][web:179]
                ax.tick_params(axis="x", labelrotation=45)

                for lab in ax.get_xticklabels():
                    lab.set_ha("right")
                # minor: trimestriel en mensuel, mensuel en trimestriel

                if n_per_year == 12:
                    ax.xaxis.set_minor_locator(mtick.MultipleLocator(3))  # [web:181]
                else:  # 4
                    ax.xaxis.set_minor_locator(mtick.MultipleLocator(1))  # [web:181]
            else:
                # annuel (ou inconnu): limiter le nombre de ticks
                ax.xaxis.set_major_locator(mtick.MaxNLocator(nbins=8, integer=True))  # [web:182]
                ax.xaxis.set_minor_locator(mtick.AutoMinorLocator())
                ax.tick_params(axis="x", labelrotation=45)

                for lab in ax.get_xticklabels():
                    lab.set_ha("right")

            # ---------- Courbes ----------
            products_all = list(df_long["product"].dropna().unique())

            # Top 3 produits pour étiquettes: basé sur la DERNIÈRE valeur de metric
            top_for_labels = set(products_all)

            if len(products_all) > 3 and metric in df_long.columns:
                tmp = df_long[["product", "period", metric]].dropna(subset=[metric]).sort_values("period")
                last_rows = tmp.groupby("product", as_index=False).tail(1)  # [web:175]
                top3 = last_rows.nlargest(3, metric)["product"].tolist()
                top_for_labels = set(top3)

            for product in products_all:
                product_data = df_long[df_long["product"] == product].sort_values("period")

                if metric not in product_data.columns or product_data.empty:
                    continue

                x = product_data["period"].to_numpy()
                y = product_data[metric].to_numpy()

                line, = ax.plot(
                    x, y,
                    marker="o",
                    label=str(product),
                    linewidth=1.6,
                    markersize=3,
                    alpha=0.95,
                )

                # Étiquettes seulement pour top_for_labels

                if product not in top_for_labels:
                    continue

                valid_idx = [i for i, val in enumerate(y) if pd.notna(val)]

                if not valid_idx:
                    continue

                i0 = valid_idx[0]
                im = valid_idx[len(valid_idx) // 2]
                i1 = valid_idx[-1]

                def annotate_point(i: int, where: str):
                    xv, yv = x[i], y[i]
                    label = fmt_scaled(yv, for_tick=False)

                    if not label:
                        return

                    if where == "start":
                        xytext, ha = (8, 8), "left"
                    elif where == "middle":
                        xytext, ha = (0, 10), "center"
                    else:  # end
                        xytext, ha = (8, 0), "left"

                    ax.annotate(  # [web:151]
                        label,
                        xy=(xv, yv),
                        xycoords="data",
                        xytext=xytext,
                        textcoords="offset points",
                        ha=ha,
                        va="bottom",
                        fontsize=8,
                        color=line.get_color(),
                        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.75),
                    )

                annotate_point(i0, "start")
                annotate_point(im, "middle")
                annotate_point(i1, "end")

            # ---------- Style ----------
            ax.grid(True, which="major", linestyle="-", linewidth=0.5, alpha=0.7)
            ax.grid(True, which="minor", linestyle=":", linewidth=0.5, alpha=0.5)
            ax.minorticks_on()

            ax.set_xlabel("Période", fontsize=10)

            if is_eur:
                ax.set_ylabel(f"{metric.replace('_', ' ').title()} ({unit})", fontsize=10)
            elif is_count:
                ax.set_ylabel(f"{metric.replace('_', ' ').title()} (nb)", fontsize=10)
            else:
                ax.set_ylabel(f"{metric.replace('_', ' ').title()}{(' (' + unit + ')') if unit else ''}", fontsize=10)

            ax.set_title(f"Évolution - {metric.replace('_', ' ').title()}", fontsize=12)
            ax.legend(fontsize=8, loc="best")

            plt.tight_layout()

            img_buffer = BytesIO()
            plt.savefig(img_buffer, format="png", bbox_inches="tight", dpi=120)
            img_buffer.seek(0)
            img_str = base64.b64encode(img_buffer.read()).decode()
            plt.close()

            return f"data:image/png;base64,{img_str}"

        except Exception as e:
            print(f"Erreur génération graphique {metric}: {e}")
            plt.close()

            return None

    def _dataframe_to_html_table(self, df: pd.DataFrame, max_rows: int = 100) -> str:
        """Convertit un DataFrame en table HTML simple."""

        if df.empty:
            return "<p>Aucune donnée</p>"

        # Limiter les lignes pour éviter les énormes tableaux
        display_df = df.head(max_rows).copy()

        # Formater nombres décimaux

        for col in display_df.columns:
            if "_eur" in col.lower() or "value" in col.lower():
                try:
                    display_df[col] = display_df[col].apply(lambda x: f"{float(x):,.0f}".replace(",", " ") if pd.notna(x) else "")
                except:
                    pass

        html = display_df.to_html(
            index=False,
            classes="table table-striped table-small",
            float_format=lambda x: f"{x:.2f}" if pd.notna(x) else "",
            border=0,
        )

        # Note si truncature

        if len(df) > max_rows:
            html += f"<p style='font-size: 0.8em; color: #666;'>... ({len(df) - max_rows} lignes omises)</p>"

        return html
