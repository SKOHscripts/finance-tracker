"""Service Dashboard - calculates and formats portfolio data."""
# Standard library
import json
from decimal import Decimal

# Third-party
from sqlmodel import Session
from tabulate import tabulate

# Local application
from finance_tracker.domain.enums import ProductType, TransactionType
from finance_tracker.domain.models import Product, Transaction, Valuation
from finance_tracker.repositories.sqlmodel_repo import (
    SQLModelProductRepository,
    SQLModelTransactionRepository,
    SQLModelValuationRepository,
    )
from finance_tracker.utils.money import format_eur, round_decimal, safe_divide


PRODUCT_COLORS = {
    "BITCOIN": "#F7931A",
    "SCPI": "#2563EB",
    "CASH": "#16A34A",
    "SAVINGS": "#8B5CF6",
    "INSURANCE": "#EC4899",
    "PER": "#F59E0B",
    "FCPI": "#06B6D4",
    }

DEPOSIT_BASED_TYPES = {ProductType.CASH, ProductType.SAVINGS, ProductType.INSURANCE, ProductType.PER}


class PortfolioData:
    """Portfolio data container.

    Stores portfolio metrics including total value, invested amount,
    gains, available cash, and product holdings.
    """

    def __init__(self):
        """Initialize a new Portfolio instance.

        Sets all monetary values to zero and initializes an empty products list.

        """
        self.total_value_eur = Decimal(0)
        self.total_invested_eur = Decimal(0)
        self.total_gains_eur = Decimal(0)
        self.cash_available = Decimal(0)
        self.products: list[dict] = []

    def to_dict(self) -> dict:
        """Convert the portfolio data to a dictionary with formatted numeric values.

        Decimal values are converted to floats with safe handling of
        zero division cases.

        Returns
        -------
        dict
            Dictionary containing the fields: total_value_eur, total_invested_eur,
            total_gains_eur, total_gains_pct, cash_available, and products.
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
    """Dashboard service for portfolio management and visualization."""

    def __init__(self, session: Session):
        """Initialize the unit of work with a database session.

        Sets up repositories for product, transaction, and valuation data access.

        Parameters
        ----------
        session : Session
            Database session for managing transactions and repository connections.

        Returns
        -------
        None

        Raises
        ------
        None
        """
        # Store session to coordinate transactions across all repositories
        self.session = session
        # Product repository for inventory and pricing operations
        self.product_repo = SQLModelProductRepository(session)
        # Transaction repository for recording buy/sell operations
        self.transaction_repo = SQLModelTransactionRepository(session)
        # Valuation repository for portfolio value calculations
        self.valuation_repo = SQLModelValuationRepository(session)

    def build_portfolio(self) -> PortfolioData:
        """Build portfolio data from products, valuations, and transactions.

        Generates performance metrics, allocation percentages, and available cash.

        Returns
        -------
        PortfolioData
            PortfolioData object containing all calculated metrics.

        Raises
        ------
        None
        """
        portfolio = PortfolioData()
        products = self.product_repo.get_all()

        for product in products:
            # Use 0 as fallback when product.id is None to avoid passing None to repo
            latest_val = self.valuation_repo.get_latest_by_product_id(product.id or 0)
            current_value = latest_val.total_value_eur if latest_val else Decimal(0)

            # Net contributions = deposits - withdrawals (positive = net inflow)
            transactions = self.transaction_repo.get_by_product_id(product.id or 0)
            net_contributions = self._calc_net_contributions(transactions)

            # Performance = current value minus money invested (not time-weighted)
            perf_eur = current_value - net_contributions
            perf_pct = safe_divide(perf_eur, net_contributions, 2) * 100 if net_contributions > 0 else Decimal(0)

            allocation_pct = Decimal(0)

            product_data = {
                "id": product.id,
                "name": product.name,
                "type": product.type.value,
                "current_value_eur": float(current_value),
                "net_contributions_eur": float(net_contributions),
                "performance_eur": float(perf_eur),
                "performance_pct": float(perf_pct),
                "allocation_pct": float(allocation_pct),  # Will be calculated after we know total
                "latest_valuation": {
                    "date": latest_val.date.isoformat() if latest_val else None,
                    "total_value_eur": float(latest_val.total_value_eur) if latest_val else 0,
                    "unit_price_eur": float(latest_val.unit_price_eur) if latest_val and latest_val.unit_price_eur else None,
                    },
                }

            portfolio.products.append(product_data)
            portfolio.total_value_eur += current_value
            portfolio.total_invested_eur += net_contributions

            # Identify cash product by name (convention over configuration)

            if product.name.lower() == "cash":
                portfolio.cash_available = current_value

        # Total gains = unrealized profit + realized gains
        portfolio.total_gains_eur = portfolio.total_value_eur - portfolio.total_invested_eur

        # Second pass: now that total portfolio value is known, calculate allocations

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
        """Calculate net contributions (DEPOSIT - WITHDRAW).

        Sums deposits and buys, subtracts withdrawals.

        Parameters
        ----------
        transactions : list[Transaction]
            List of transactions to calculate net contributions from.

        Returns
        -------
        Decimal
            Net contribution amount (positive for deposits, negative for withdrawals).

        Raises
        ------
        None
        """
        net = Decimal(0)

        for tx in transactions:
            # Deposits increase available funds

            if tx.type == TransactionType.DEPOSIT and tx.amount_eur:
                net += tx.amount_eur
            # Buys increase portfolio value (crypto received for EUR paid)
            elif tx.type == TransactionType.BUY and tx.amount_eur:
                net += tx.amount_eur
            # Withdrawals decrease available funds
            elif tx.type == TransactionType.WITHDRAW and tx.amount_eur:
                net -= tx.amount_eur

        return net

    def get_product_history(self, product_id: int) -> list[dict]:
        """Return chronological list of valuations for a product.

        Each dict: {date, total_value_eur, unit_price_eur}
        """
        valuations = self.valuation_repo.get_by_product_id(product_id)
        return [
            {
                "date": v.date,
                "total_value_eur": float(v.total_value_eur),
                "unit_price_eur": float(v.unit_price_eur) if v.unit_price_eur else None,
                }
            for v in valuations
            ]

    def get_product_pru(self, product_id: int) -> float | None:
        """Calculate PRU for a product.

        For BUY-based products: sum(BUY amount_eur) / quantity from latest valuation.
        For DEPOSIT-based products: sum(DEPOSIT amount_eur).
        Returns None if no data.
        """
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return None

        transactions = self.transaction_repo.get_by_product_id(product_id)

        if product.type in DEPOSIT_BASED_TYPES:
            total = sum(
                float(t.amount_eur)
                for t in transactions
                if t.type == TransactionType.DEPOSIT and t.amount_eur
                )
            return total if total > 0 else None

        # BUY-based products (BITCOIN, SCPI, FCPI)
        buy_total = sum(
            float(t.amount_eur)
            for t in transactions
            if t.type == TransactionType.BUY and t.amount_eur
            )
        if buy_total <= 0:
            return None

        latest_val = self.valuation_repo.get_latest_by_product_id(product_id)
        if not latest_val or not latest_val.unit_price_eur or float(latest_val.unit_price_eur) <= 0:
            return None

        total_value = float(latest_val.total_value_eur)
        unit_price = float(latest_val.unit_price_eur)
        if unit_price <= 0:
            return None

        quantity = total_value / unit_price
        if quantity <= 0:
            return None

        return buy_total / quantity

    def get_product_details(self, product_id: int) -> dict | None:
        """Return comprehensive per-product data for dashboard display."""
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return None

        history = self.get_product_history(product_id)
        pru = self.get_product_pru(product_id)

        latest_val = self.valuation_repo.get_latest_by_product_id(product_id)
        current_value = float(latest_val.total_value_eur) if latest_val else 0.0

        transactions = self.transaction_repo.get_by_product_id(product_id)
        net_invested = float(self._calc_net_contributions(transactions))

        gains_eur = current_value - net_invested
        gains_pct = (gains_eur / net_invested * 100) if net_invested > 0 else 0.0

        color = PRODUCT_COLORS.get(product.type.value, "#6B7280")

        return {
            "id": product.id,
            "name": product.name,
            "type": product.type.value,
            "color": color,
            "history": history,
            "pru": pru,
            "current_value": current_value,
            "net_invested": net_invested,
            "gains_eur": gains_eur,
            "gains_pct": gains_pct,
            }

    def display_dashboard(self, portfolio: PortfolioData) -> str:
        """Format a text dashboard display using tabulate.

        Create a formatted CLI output with portfolio summary and product details.

        Parameters
        ----------
        portfolio : PortfolioData
            The portfolio data object containing products and summary information.

        Returns
        -------
        str
            Formatted string for CLI display with tables showing portfolio summary and product details.

        Raises
        ------
        None
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
        """Export portfolio data to JSON format.

        Converts portfolio data to a formatted JSON string.

        Parameters
        ----------
        portfolio : PortfolioData
            The portfolio data to export.

        Returns
        -------
        str
            A JSON string representing the portfolio data.

        Raises
        ------
        TypeError
            If the portfolio is not an instance of PortfolioData.
        """

        return json.dumps(portfolio.to_dict(), indent=2, ensure_ascii=False)
