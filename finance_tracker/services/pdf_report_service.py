"""Service génération PDF."""
from datetime import datetime
from pathlib import Path

from weasyprint import HTML, CSS

from finance_tracker.config import REPORTS_DIR, TEMPLATES_DIR
from finance_tracker.services.dashboard_service import PortfolioData
from finance_tracker.utils.money import format_eur


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

        return template.render(
            generated_at=datetime.utcnow().strftime("%d/%m/%Y %H:%M"),
            total_value_eur=format_eur(portfolio.total_value_eur),
            total_invested_eur=format_eur(portfolio.total_invested_eur),
            total_gains_eur=portfolio.total_gains_eur,  # Decimal brut
            total_gains_eur_formatted=format_eur(portfolio.total_gains_eur),
            total_gains_pct=total_gains_pct,  # String formaté
            total_gains_class="positive" if portfolio.total_gains_eur >= 0 else "negative",  # Classe CSS
            cash_available=format_eur(portfolio.cash_available),
            products=[
                {
                    "name": p["name"],
                    "current_value_eur": format_eur(p["current_value_eur"]),
                    "net_contributions_eur": format_eur(p["net_contributions_eur"]),
                    "performance_eur": p["performance_eur"],  # Decimal brut
                    "performance_eur_formatted": format_eur(p["performance_eur"]),
                    "performance_pct": f"{p['performance_pct']:.2f}%",
                    "allocation_pct": f"{p['allocation_pct']:.2f}%",
                    "performance_class": "positive" if p["performance_eur"] >= 0 else "negative"
                }

                for p in portfolio.products
            ],
        )

    # def _render_html(self, portfolio: PortfolioData) -> str:
    #     """Crée le HTML pour le PDF."""
    #     # Générer HTML brut (pas de template HTML fichier en v1, direct string)
    #     now = datetime.utcnow().isoformat()
    #
    #     total_gained = portfolio.total_gains_eur
    #     total_perf_pct = (
    #         (portfolio.total_gains_eur / portfolio.total_invested_eur * 100)
    #         if portfolio.total_invested_eur > 0
    #         else 0
    #     )
    #
    #     html = f"""
    #     <html>
    #     <head>
    #         <meta charset="UTF-8">
    #         <style>
    #             body {{
    #                 font-family: Arial, sans-serif;
    #                 margin: 20px;
    #                 background-color: #f5f5f5;
    #             }}
    #             .container {{
    #                 background: white;
    #                 padding: 40px;
    #                 border-radius: 5px;
    #             }}
    #             h1 {{
    #                 color: #333;
    #                 border-bottom: 2px solid #007bff;
    #                 padding-bottom: 10px;
    #             }}
    #             h2 {{
    #                 color: #555;
    #                 margin-top: 30px;
    #                 border-bottom: 1px solid #ddd;
    #                 padding-bottom: 5px;
    #             }}
    #             .metadata {{
    #                 font-size: 12px;
    #                 color: #666;
    #                 margin-bottom: 20px;
    #             }}
    #             table {{
    #                 width: 100%;
    #                 border-collapse: collapse;
    #                 margin-bottom: 20px;
    #             }}
    #             th {{
    #                 background-color: #007bff;
    #                 color: white;
    #                 padding: 10px;
    #                 text-align: left;
    #             }}
    #             td {{
    #                 padding: 8px;
    #                 border-bottom: 1px solid #ddd;
    #             }}
    #             tr:nth-child(even) {{
    #                 background-color: #f9f9f9;
    #             }}
    #             .summary {{
    #                 display: flex;
    #                 gap: 40px;
    #                 margin-bottom: 30px;
    #             }}
    #             .summary-item {{
    #                 flex: 1;
    #             }}
    #             .summary-item h3 {{
    #                 margin: 0;
    #                 color: #555;
    #             }}
    #             .summary-item .value {{
    #                 font-size: 20px;
    #                 font-weight: bold;
    #                 color: #007bff;
    #                 margin-top: 5px;
    #             }}
    #             .positive {{ color: #28a745; }}
    #             .negative {{ color: #dc3545; }}
    #         </style>
    #     </head>
    #     <body>
    #         <div class="container">
    #             <h1>Rapport Portefeuille</h1>
    #             <div class="metadata">Généré le: {now}</div>
    #
    #             <div class="summary">
    #                 <div class="summary-item">
    #                     <h3>Valeur totale</h3>
    #                     <div class="value">{format_eur(portfolio.total_value_eur)}</div>
    #                 </div>
    #                 <div class="summary-item">
    #                     <h3>Investissement net</h3>
    #                     <div class="value">{format_eur(portfolio.total_invested_eur)}</div>
    #                 </div>
    #                 <div class="summary-item">
    #                     <h3>Gains</h3>
    #                     <div class="value {'positive' if total_gained >= 0 else 'negative'}">
    #                         {format_eur(total_gained)}
    #                     </div>
    #                 </div>
    #                 <div class="summary-item">
    #                     <h3>Performance</h3>
    #                     <div class="value {'positive' if total_perf_pct >= 0 else 'negative'}">
    #                         {total_perf_pct:.2f}%
    #                     </div>
    #                 </div>
    #             </div>
    #
    #             <h2>Détail par produit</h2>
    #             <table>
    #                 <thead>
    #                     <tr>
    #                         <th>Produit</th>
    #                         <th>Valeur actuelle</th>
    #                         <th>Investi</th>
    #                         <th>Gains</th>
    #                         <th>Performance %</th>
    #                         <th>Allocation %</th>
    #                     </tr>
    #                 </thead>
    #                 <tbody>
    #     """
    #
    #     for product in portfolio.products:
    #         perf_class = "positive" if product["performance_eur"] >= 0 else "negative"
    #         html += f"""
    #                     <tr>
    #                         <td>{product['name']}</td>
    #                         <td>{product['current_value_eur']:,.2f}€</td>
    #                         <td>{product['net_contributions_eur']:,.2f}€</td>
    #                         <td class="{perf_class}">{product['performance_eur']:,.2f}€</td>
    #                         <td class="{perf_class}">{product['performance_pct']:.2f}%</td>
    #                         <td>{product['allocation_pct']:.2f}%</td>
    #                     </tr>
    #         """
    #
    #     html += """
    #                 </tbody>
    #             </table>
    #
    #             <h2>Informations supplémentaires</h2>
    #             <p>
    #                 <strong>Cash disponible:</strong> {}<br>
    #                 <strong>Nombre de produits:</strong> {}
    #             </p>
    #         </div>
    #     </body>
    #     </html>
    #     """.format(
    #         format_eur(portfolio.cash_available),
    #         len(portfolio.products),
    #     )
    #
    #     return html
