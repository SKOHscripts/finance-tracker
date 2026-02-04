"""Service génération PDF."""

from datetime import datetime
from pathlib import Path
from weasyprint import HTML, CSS
from finance_tracker.config import REPORTS_DIR, TEMPLATES_DIR
from finance_tracker.services.dashboard_service import PortfolioData
from finance_tracker.utils.money import format_eur
import matplotlib.pyplot as plt
import base64
from io import BytesIO


class PDFReportService:
    """Service de génération de PDF."""

    def __init__(self, templates_dir: Path = TEMPLATES_DIR, reports_dir: Path = REPORTS_DIR):
        self.templates_dir = templates_dir
        self.reports_dir = reports_dir

    def generate_report(self, portfolio: PortfolioData) -> str:
        """Génère un PDF rapport et le sauvegarde.

        Args:
            portfolio: PortfolioData à exporter

        Returns:
            Chemin fichier PDF généré
        """
        # Générer HTML
        html_content = self._render_html(portfolio)

        # Sauvegarder PDF
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
        filename = f"report_{timestamp}.pdf"
        filepath = self.reports_dir / filename

        HTML(string=html_content).write_pdf(str(filepath))

        return str(filepath)

    def _render_html(self, portfolio: PortfolioData) -> str:
        """Rendu template Jinja2."""
        from jinja2 import Environment, FileSystemLoader
        from finance_tracker.utils.money import format_eur

        env = Environment(loader=FileSystemLoader(self.templates_dir))
        template = env.get_template("report.html")

        # Calculer total_gains_pct correctement
        total_gains_pct = (
            f"{(portfolio.total_gains_eur / portfolio.total_invested_eur * 100):.2f}%"

            if portfolio.total_invested_eur > 0
            else "0.00%"
        )

        # Générer les graphiques
        chart_allocation = self._generate_allocation_chart(portfolio.products)
        chart_performance = self._generate_performance_chart(portfolio.products)

        return template.render(
            generated_at=datetime.utcnow().strftime("%d/%m/%Y %H:%M"),
            total_value_eur=format_eur(portfolio.total_value_eur),
            total_invested_eur=format_eur(portfolio.total_invested_eur),
            total_gains_eur=portfolio.total_gains_eur,  # Decimal brut
            total_gains_eur_formatted=format_eur(portfolio.total_gains_eur),
            total_gains_pct=total_gains_pct,  # String formaté
            total_gains_class="positive" if portfolio.total_gains_eur >= 0 else "negative",  # Classe CSS
            cash_available=format_eur(portfolio.cash_available),
            chart_allocation=chart_allocation,
            chart_performance=chart_performance,
            products=[
                {
                    "name": p["name"],
                    "current_value_eur": p["current_value_eur"],
                    "net_contributions_eur": p["net_contributions_eur"],
                    "performance_eur": p["performance_eur"],  # Decimal brut
                    "performance_eur_formatted": format_eur(p["performance_eur"]),
                    "performance_pct": f"{p['performance_pct']:.2f}%",
                    "allocation_pct": f"{p['allocation_pct']:.2f}%",
                    "performance_class": "positive" if p["performance_eur"] >= 0 else "negative",
                }

                for p in portfolio.products
            ],
        )

    def _generate_allocation_chart(self, products: list) -> str:
        """Génère un graphique donut de l'allocation par produit (style pro)."""
        import matplotlib as mpl

        # --- Données
        items = [(p["name"], float(p["current_value_eur"])) for p in products]
        items = [(n, v) for (n, v) in items if v > 0]

        if not items:
            return ""

        # Trier + (option) regrouper le reste
        items.sort(key=lambda x: x[1], reverse=True)
        max_slices = 8

        if len(items) > max_slices:
            top = items[: max_slices - 1]
            other_sum = sum(v for _, v in items[max_slices - 1:])
            items = top + [("Autres", other_sum)]

        labels = [n for n, _ in items]
        sizes = [v for _, v in items]
        total = sum(sizes)

        # --- Style global (sobre)
        mpl.rcParams.update({
            "font.size": 10,
            "axes.titlesize": 12,
            "text.color": "#111827",
            "axes.labelcolor": "#111827",
        })

        fig, ax = plt.subplots(figsize=(10, 5.6), dpi=160)
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        # Palette moderne (tons doux)
        colors = plt.cm.Blues([0.35, 0.45, 0.55, 0.62, 0.70, 0.78, 0.86, 0.92, 0.97])[:len(labels)]

        def autopct(pct):
            # N’affiche que si >= 3% pour éviter la surcharge

            return f"{pct:.0f}%" if pct >= 3 else ""

        wedges, texts, autotexts = ax.pie(
            sizes,
            startangle=90,
            counterclock=False,
            colors=colors,
            autopct=autopct,
            pctdistance=0.78,
            wedgeprops=dict(width=0.42, edgecolor="white", linewidth=1.2),  # donut
            textprops=dict(color="#111827", fontsize=9),
        )

        # Légende (nom + montant + %)
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

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format="png", bbox_inches="tight")
        img_buffer.seek(0)
        img_str = base64.b64encode(img_buffer.read()).decode()
        plt.close(fig)

        return f"data:image/png;base64,{img_str}"

    def _generate_performance_chart(self, products: list) -> str:
        """Histogramme des performances (%) par produit (style pro)."""
        import matplotlib as mpl

        # --- Données (on exclut cash si tu veux)
        prods = [p for p in products if p["name"].lower() != "cash"]
        data = [(p["name"], float(p["performance_pct"])) for p in prods]

        # On garde même les 0, mais on peut filtrer si tu préfères

        if not data:
            return ""

        # Trier du meilleur au pire
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

        colors = ["#16A34A" if v >= 0 else "#DC2626" for v in values]

        y = range(len(labels))
        bars = ax.barh(y, values, color=colors, edgecolor="none", height=0.6)

        # Ligne 0 + grille légère
        ax.axvline(0, color="#111827", linewidth=1.0, alpha=0.6)
        ax.xaxis.grid(True, color="#E5E7EB", linewidth=1.0, alpha=0.8)
        ax.set_axisbelow(True)

        ax.set_yticks(list(y))
        ax.set_yticklabels(labels, fontsize=9)
        ax.invert_yaxis()  # meilleur en haut

        ax.set_xlabel("Performance (%)")
        ax.set_title("Performance par produit", pad=14)

        # Labels de valeurs

        for bar, v in zip(bars, values):
            x = bar.get_width()
            y_text = bar.get_y() + bar.get_height() / 2

            if v >= 0:
                ax.text(x + 0.3, y_text, f"{v:.1f}%", va="center", ha="left", fontsize=9, color="#111827")
            else:
                ax.text(x - 0.3, y_text, f"{v:.1f}%", va="center", ha="right", fontsize=9, color="#111827")

        # Marges auto pour que les labels ne soient pas coupés
        xmin = min(values) if values else -1
        xmax = max(values) if values else 1
        pad = max(2.0, (xmax - xmin) * 0.12)
        ax.set_xlim(xmin - pad, xmax + pad)

        # Enlever le “cadre” inutile

        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)

        plt.tight_layout()

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format="png", bbox_inches="tight")
        img_buffer.seek(0)
        img_str = base64.b64encode(img_buffer.read()).decode()
        plt.close(fig)

        return f"data:image/png;base64,{img_str}"
