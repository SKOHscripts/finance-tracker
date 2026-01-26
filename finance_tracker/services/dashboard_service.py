"""Service Dashboard - calcule et formate les données portefeuille."""
import json
from decimal import Decimal

from sqlmodel import Session

from tabulate import tabulate

from finance_tracker.domain.enums import TransactionType
from finance_tracker.domain.models import Product, Transaction, Valuation
from finance_tracker.repositories.sqlmodel_repo import (
    SQLModelProductRepository,
    SQLModelTransactionRepository,
    SQLModelValuationRepository,
    )
from finance_tracker.utils.money import format_eur, round_decimal, safe_divide


class PortfolioData:
    """Données du portefeuille."""

    def __init__(self):
        self.total_value_eur = Decimal(0)
        self.total_invested_eur = Decimal(0)
        self.total_gains_eur = Decimal(0)
        self.cash_available = Decimal(0)
        self.products: list[dict] = []

    def to_dict(self) -> dict:
        """Convertir l'objet en dictionnaire Python avec les valeurs numériques formatées.

        Les valeurs décimales sont converties en flottants, avec gestion sécurisée des divisions nulles.

        Returns
        -------
        dict
            Dictionnaire contenant les champs : total_value_eur, total_invested_eur,
            total_gains_eur, total_gains_pct, cash_available, et products.
        """

        return {
            "total_value_eur": float(self.total_value_eur),
            "total_invested_eur": float(self.total_invested_eur),
            "total_gains_eur": float(self.total_gains_eur),
            "total_gains_pct": float(
                safe_divide(self.total_gains_eur, self.total_invested_eur, 2)

                if self.total_invested_eur > 0
                else Decimal(0)
                ),
            "cash_available": float(self.cash_available),
            "products": self.products,
            }


class DashboardService:
    """Service de dashboard."""

    def __init__(self, session: Session):
        self.session = session
        self.product_repo = SQLModelProductRepository(session)
        self.transaction_repo = SQLModelTransactionRepository(session)
        self.valuation_repo = SQLModelValuationRepository(session)

    def build_portfolio(self) -> PortfolioData:
        """
        Construit les données du portefeuille à partir des produits, valorisations et transactions.

        Génère les indicateurs de performance, d'allocation et le cash disponible.

        Returns
        -------
            PortfolioData avec tous les calculs
        """
        portfolio = PortfolioData()
        products = self.product_repo.get_all()

        for product in products:
            # Dernière valorisation
            latest_val = self.valuation_repo.get_latest_by_product_id(product.id or 0)
            current_value = latest_val.total_value_eur if latest_val else Decimal(0)

            # Contributions nettes (DEPOSIT - WITHDRAW)
            transactions = self.transaction_repo.get_by_product_id(product.id or 0)
            net_contributions = self._calc_net_contributions(transactions)

            # Performance simple v1
            perf_eur = current_value - net_contributions
            perf_pct = safe_divide(perf_eur, net_contributions, 2) if net_contributions > 0 else Decimal(0)

            allocation_pct = Decimal(0)

            product_data = {
                "id": product.id,
                "name": product.name,
                "type": product.type.value,
                "current_value_eur": float(current_value),
                "net_contributions_eur": float(net_contributions),
                "performance_eur": float(perf_eur),
                "performance_pct": float(perf_pct),
                "allocation_pct": float(allocation_pct),  # Calculé après total
                "latest_valuation": {
                    "date": latest_val.date.isoformat() if latest_val else None,
                    "total_value_eur": float(latest_val.total_value_eur) if latest_val else 0,
                    "unit_price_eur": float(latest_val.unit_price_eur) if latest_val and latest_val.unit_price_eur else None,
                    },
                }

            portfolio.products.append(product_data)
            portfolio.total_value_eur += current_value
            portfolio.total_invested_eur += net_contributions

            # Déterminer le cash

            if product.name.lower() == "cash":
                portfolio.cash_available = current_value

        # Calculer gains totaux
        portfolio.total_gains_eur = portfolio.total_value_eur - portfolio.total_invested_eur

        # Calculer allocations

        for product in portfolio.products:
            if portfolio.total_value_eur > 0:
                product["allocation_pct"] = float(
                    safe_divide(
                        Decimal(str(product["current_value_eur"])),
                        portfolio.total_value_eur,
                        2,
                        )
                    * 100
                    )

        return portfolio

    def _calc_net_contributions(self, transactions: list[Transaction]):
        """Calcule les contributions nettes (DEPOSIT - WITHDRAW)."""
        net = Decimal(0)

        for tx in transactions:
            if tx.type == TransactionType.DEPOSIT and tx.amount_eur:
                net += tx.amount_eur
            elif tx.type == TransactionType.WITHDRAW and tx.amount_eur:
                net -= tx.amount_eur

        return net

    def display_dashboard(self, portfolio: PortfolioData) -> str:
        """Formate un affichage texte du dashboard avec tabulate.

        Returns:
            String formaté pour affichage CLI
        """
        output = []

        # Header
        # output.append("PORTFOLIO DASHBOARD".center(80))
        output.append(tabulate([["PORTFOLIO DASHBOARD"]], tablefmt="fancy_grid"))
        output.append("")

        # Summary Table
        output.append("RÉSUMÉ GLOBAL")
        output.append("-" * 80)

        summary_data = [
            ["Valeur totale", format_eur(portfolio.total_value_eur)],
            ["Investissement net", format_eur(portfolio.total_invested_eur)],
            ["Gains", format_eur(portfolio.total_gains_eur)],
            ]

        if portfolio.total_invested_eur > 0:
            perf_pct = safe_divide(portfolio.total_gains_eur, portfolio.total_invested_eur, 2) * 100
            summary_data.append(["Performance %", f"{float(perf_pct):.2f}%"])

        summary_data.append(["Cash disponible", format_eur(portfolio.cash_available)])

        output.append(tabulate(summary_data, tablefmt="fancy_grid"))
        output.append("")

        # Products Table
        output.append("DÉTAIL PAR PRODUIT")
        output.append("-" * 80)

        product_headers = ["Produit", "Valeur", "Investi", "Gains", "Perf %", "Alloc %"]
        product_rows = []

        for p in portfolio.products:
            product_rows.append([
                p['name'],
                f"{float(p['current_value_eur']):,.2f}€",
                f"{float(p['net_contributions_eur']):,.2f}€",
                f"{float(p['performance_eur']):,.2f}€",
                f"{float(p['performance_pct']):.2f}%",
                f"{float(p['allocation_pct']):.2f}%"
                ])

        output.append(tabulate(product_rows, headers=product_headers, tablefmt="fancy_grid"))

        return "\n".join(output)

    def export_json(self, portfolio: PortfolioData) -> str:
        """Exporte les données du portefeuille au format JSON.

        Convertit les données du portefeuille en une chaîne JSON formatée.

        Parameters
        ----------
        portfolio : PortfolioData
            Les données du portefeuille à exporter.

        Returns
        -------
        str
            Une chaîne JSON représentant les données du portefeuille.

        Raises
        ------
        TypeError
            Si le portefeuille n'est pas une instance de PortfolioData.
        """

        return json.dumps(portfolio.to_dict(), indent=2, ensure_ascii=False)
