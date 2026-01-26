"""Service de projection de rendement composé."""
from decimal import Decimal
from enum import Enum

from finance_tracker.utils.money import round_decimal


class ProjectionFrequency(str, Enum):
    """Fréquence de versement/composition."""

    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUAL = "ANNUAL"


class ProjectionResult:
    """Résultat de projection."""

    def __init__(
        self,
        initial_amount: Decimal,
        monthly_contribution: Decimal,
        annual_return: Decimal,
        years: int,
        frequency: ProjectionFrequency,
            ):
        self.initial_amount = initial_amount
        self.monthly_contribution = monthly_contribution
        self.annual_return = annual_return
        self.years = years
        self.frequency = frequency
        self.yearly_details: list[dict] = []
        self.final_value = Decimal(0)
        self.total_contributed = Decimal(0)
        self.total_gains = Decimal(0)

    def calculate(self) -> None:
        """Effectue la projection."""
        current_value = self.initial_amount
        total_contrib = self.initial_amount

        # Déterminer nombre de périodes par an
        periods_per_year = {
            ProjectionFrequency.MONTHLY: 12,
            ProjectionFrequency.QUARTERLY: 4,
            ProjectionFrequency.ANNUAL: 1,
            }[self.frequency]

        rate_per_period = (Decimal(1) + Decimal(str(self.annual_return))) ** (
            Decimal(1) / Decimal(periods_per_year)
            ) - Decimal(1)

        for year in range(1, self.years + 1):
            year_start = current_value
            year_contributions = Decimal(0)
            year_gains = Decimal(0)

            for period in range(periods_per_year):
                # Ajouter versement
                current_value += self.monthly_contribution
                year_contributions += self.monthly_contribution
                total_contrib += self.monthly_contribution

                # Appliquer rendement
                gain = current_value * rate_per_period
                current_value += gain
                year_gains += gain

            self.yearly_details.append({
                "year": year,
                "value_start": round_decimal(year_start),
                "contributions": round_decimal(year_contributions),
                "gains": round_decimal(year_gains),
                "value_end": round_decimal(current_value),
                })

        self.final_value = round_decimal(current_value)
        self.total_contributed = total_contrib
        self.total_gains = round_decimal(self.final_value - total_contrib)

    def display_table(self) -> str:
        """Formate un tableau de projection avec tabulate et style 'fancy_grid'.

        Returns:
            String contenant le tableau
        """
        from tabulate import tabulate

        headers = ["Année", "Valeur Début", "Versements", "Gains", "Valeur Fin"]
        rows = [
            [
                detail["year"],
                f"{detail['value_start']:.2f}",
                f"{detail['contributions']:.2f}",
                f"{detail['gains']:.2f}",
                f"{detail['value_end']:.2f}",
                ]

            for detail in self.yearly_details
            ]

        total_row = [
            "TOTAL",
            "",
            f"{self.total_contributed:.2f}",
            f"{self.total_gains:.2f}",
            f"{self.final_value:.2f}",
            ]
        rows.append(total_row)

        table = tabulate(rows, headers, tablefmt="fancy_grid")

        title = (
            f"Projection: {self.monthly_contribution}€/mois, "
            f"{self.annual_return * 100:.2f}% rendement, "
            f"{self.years} ans"
            )

        return f"{title}\n\n{table}"
