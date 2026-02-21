from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from math import floor
from typing import Dict, List, Literal, Optional, Tuple

Period = Literal["monthly", "quarterly", "yearly"]
ProductKind = Literal["cash", "savings", "scpi", "per", "fcpi", "other"]
DividendFrequency = Literal["monthly", "quarterly", "semiannual", "yearly"]
FCPIExitMode = Literal["principal", "full_value"]


def D(x) -> Decimal:
    return Decimal(str(x))


def steps_per_year(period: Period) -> int:
    if period == "monthly":
        return 12

    if period == "quarterly":
        return 4

    return 1


def periodic_rate(annual_rate: Decimal, dt_years: Decimal) -> Decimal:
    return (D(1) + annual_rate) ** dt_years - D(1)


@dataclass
class IncomeConfig:
    gross_annual_start: Decimal
    annual_growth: Decimal
    gross_annual_previous: Optional[Decimal] = None  # revenu N-1 (PER 10% N-1)


@dataclass
class BudgetConfig:
    annual_living_costs: Decimal
    emergency_fund_target: Decimal
    enforce_emergency_fund_first: bool = True


@dataclass
class TaxBracket:
    up_to: Optional[Decimal]
    rate: Decimal


@dataclass
class TaxConfig:
    brackets: List[TaxBracket]
    household_parts: Decimal = D(1)
    standard_deduction_rate: Decimal = D(0.10)
    initial_tax_due_annual: Decimal = D(0)


@dataclass
class PERCapConfig:
    rate_of_income_prev_year: Decimal = D(0.10)
    annual_min: Decimal = D(0)
    annual_max: Optional[Decimal] = None


@dataclass
class PERConfig:
    pass


@dataclass
class FCPIConfig:
    tax_reduction_rate: Decimal = D(0.18)     # ex: 18%
    annual_eligible_cap: Decimal = D(12000)   # configurable (ex: 12k)
    holding_years: int = 8
    exit_mode: FCPIExitMode = "principal"     # principal (par défaut) ou full_value


@dataclass
class SCPIConfig:
    part_price: Decimal
    parts_per_year: int
    distribution_annual: Decimal
    dividends_to_cash: bool = True
    revaluation_annual: Decimal = D(0)
    dividend_frequency: DividendFrequency = "quarterly"  # NOUVEAU


@dataclass
class ProductSimConfig:
    name: str
    kind: ProductKind

    annual_return: Decimal = D(0)

    contribution_per_period: Decimal = D(0)
    contribution_pct_income: Decimal = D(0)

    initial_value_eur: Decimal = D(0)
    initial_invested_eur: Optional[Decimal] = None  # si None -> initial_value

    # SCPI
    scpi: Optional[SCPIConfig] = None
    initial_scpi_parts: Optional[int] = None

    # FCPI
    fcpi: Optional[FCPIConfig] = None

    priority: int = 50


@dataclass
class SimulationConfig:
    start: date
    years: int
    period: Period
    inflation_annual: Decimal

    income: IncomeConfig
    budget: BudgetConfig
    tax: TaxConfig
    per_cap: PERCapConfig


@dataclass
class SimulationRow:
    period_index: int
    year_index: int
    year_number: int
    step_in_year: int

    income_annual: Decimal
    income_period: Decimal
    living_costs_period: Decimal

    tax_paid_period: Decimal
    tax_paid_year_to_date: Decimal
    tax_due_for_year: Optional[Decimal]

    # FCPI: réduction d'impôt calculée fin d'année (sur base versements FCPI)
    fcpi_tax_reduction_for_year: Optional[Decimal]

    per_cap_for_year: Decimal
    per_contrib_year_to_date: Decimal

    cash_before_invest: Decimal
    cash_after_invest: Decimal

    contributions_by_product: Dict[str, Decimal]
    dividends_by_product: Dict[str, Decimal]
    scpi_parts_by_product: Dict[str, int]

    # FCPI: montants sortis cette période (cash-in)
    redemptions_by_product: Dict[str, Decimal]

    value_by_product: Dict[str, Decimal]
    invested_by_product: Dict[str, Decimal]

    total_value: Decimal
    total_invested: Decimal
    total_gains: Decimal

    inflation_index: Decimal
    total_value_real: Decimal


@dataclass
class SimulationResult:
    rows: List[SimulationRow]
    product_names: List[str]
    cash_product: str
    tax_due_next_year: Decimal


def compute_progressive_tax(taxable: Decimal, tax_cfg: TaxConfig) -> Decimal:
    if taxable <= 0:
        return D(0)

    parts = max(tax_cfg.household_parts, D(1))
    taxable_per_part = taxable / parts

    t = D(0)
    prev = D(0)

    for b in tax_cfg.brackets:
        upper = b.up_to

        if upper is None:
            t += (taxable_per_part - prev) * b.rate

            break
        band = min(taxable_per_part, upper) - prev

        if band > 0:
            t += band * b.rate
        prev = upper

        if taxable_per_part <= upper:
            break

    return max(t, D(0)) * parts


def compute_per_cap_from_income_prev(income_prev: Decimal, per_cap: PERCapConfig) -> Decimal:
    cap = income_prev * per_cap.rate_of_income_prev_year
    cap = max(cap, per_cap.annual_min)

    if per_cap.annual_max is not None:
        cap = min(cap, per_cap.annual_max)

    return max(cap, D(0))


def distribute_integer_over_periods(total: int, n: int) -> List[int]:
    """
    Distribute an integer total evenly across n periods, with any remainder distributed as extras.

    This function divides the total into n parts as evenly as possible, ensuring the sum of parts equals the total.

    Parameters
    ----------
    total : int
        The total integer amount to be distributed.
    n : int
        The number of periods over which to distribute the total.

    Returns
    -------
    List[int]
        A list of n integers representing the distribution, where the difference between any two elements is at most 1.

    Raises
    ------
    None
    """
    # Return empty list if no periods to distribute over

    if n <= 0:
        return []

    # If total is zero or negative, return list of zeros

    if total <= 0:
        return [0] * n

    # Calculate base amount each period will receive
    base = total // n
    # Calculate remainder to distribute as extra units
    rem = total % n

    # Distribute base amount to all periods, add 1 to first 'rem' periods

    return [base + (1 if i < rem else 0) for i in range(n)]


def payments_per_year(freq: DividendFrequency) -> int:
    if freq == "monthly":
        return 12

    if freq == "quarterly":
        return 4

    if freq == "semiannual":
        return 2

    return 1


def should_pay_dividend(period: Period, step_in_year: int, freq: DividendFrequency) -> bool:
    # On ramène tout au concept "mois 1..12" si period=monthly.

    if period == "yearly":
        return True  # une fois par an

    if period == "quarterly":
        # 4 steps: 0..3

        if freq in ("monthly", "quarterly"):
            return True

        if freq == "semiannual":
            return step_in_year in (1, 3)  # fin S1 et fin S2

        return step_in_year == 3
    # monthly

    if freq == "monthly":
        return True

    if freq == "quarterly":
        return step_in_year in (2, 5, 8, 11)

    if freq == "semiannual":
        return step_in_year in (5, 11)

    return step_in_year == 11


class SimulationService:
    def run(self, cfg: SimulationConfig, products: List[ProductSimConfig]) -> SimulationResult:
        n_per_year = steps_per_year(cfg.period)
        dt_years = D(1) / D(n_per_year)
        n_steps = cfg.years * n_per_year

        cash_candidates = [p.name for p in products if p.kind == "cash"]

        if not cash_candidates:
            raise ValueError("Simulation: il faut au moins un produit de type 'cash'.")

        if len(cash_candidates) > 1:
            raise ValueError(f"Simulation: plusieurs produits 'cash' détectés: {cash_candidates}. Garde-en un seul.")
        cash_name = cash_candidates[0]

        product_names = [p.name for p in products]

        value: Dict[str, Decimal] = {}
        invested: Dict[str, Decimal] = {}
        scpi_parts: Dict[str, int] = {}
        scpi_part_price: Dict[str, Decimal] = {}

        # FCPI lots: product -> list of (maturity_step_index, principal)
        fcpi_lots: Dict[str, List[Tuple[int, Decimal]]] = {}

        for p in products:
            inv0 = p.initial_invested_eur if p.initial_invested_eur is not None else p.initial_value_eur

            if p.kind == "scpi" and p.scpi:
                scpi_part_price[p.name] = p.scpi.part_price
                parts0 = p.initial_scpi_parts

                if parts0 is None:
                    parts0 = int(floor(p.initial_value_eur / p.scpi.part_price)) if p.scpi.part_price > 0 else 0
                scpi_parts[p.name] = max(0, int(parts0))
                value[p.name] = D(scpi_parts[p.name]) * scpi_part_price[p.name]
                invested[p.name] = inv0
            else:
                value[p.name] = p.initial_value_eur
                invested[p.name] = inv0

            if p.kind == "fcpi":
                fcpi_lots[p.name] = []

        infl_idx = D(1)

        tax_due_by_year: Dict[int, Decimal] = {}
        tax_paid_ytd = D(0)
        tax_to_pay_this_year_annual = cfg.tax.initial_tax_due_annual

        per_contrib_ytd = D(0)

        # FCPI contributions suivi annuel (pour réduction IR fin d'année)
        fcpi_contrib_ytd_by_product: Dict[str, Decimal] = {p.name: D(0) for p in products if p.kind == "fcpi"}

        income_annual_by_year: Dict[int, Decimal] = {}

        rows: List[SimulationRow] = []

        for i in range(n_steps):
            year_idx = i // n_per_year
            step_in_year = i % n_per_year
            year_number = year_idx + 1

            # Année: armer le paiement impôt de l'année précédente

            if step_in_year == 0:
                if year_idx == 0:
                    tax_to_pay_this_year_annual = cfg.tax.initial_tax_due_annual
                else:
                    tax_to_pay_this_year_annual = tax_due_by_year.get(year_idx - 1, D(0))
                tax_paid_ytd = D(0)

            # Inflation
            infl_idx *= (D(1) + cfg.inflation_annual) ** dt_years

            # Revenu
            income_annual = cfg.income.gross_annual_start * ((D(1) + cfg.income.annual_growth) ** D(year_idx))
            income_annual_by_year[year_idx] = income_annual
            income_period = income_annual * dt_years

            # Flux: revenu / dépenses / impôt payé
            value[cash_name] += income_period
            living_costs_period = cfg.budget.annual_living_costs * dt_years
            value[cash_name] -= living_costs_period

            tax_paid_period = (tax_to_pay_this_year_annual * dt_years)
            value[cash_name] -= tax_paid_period
            tax_paid_ytd += tax_paid_period

            # FCPI maturities: on crédite le cash (avant investissement de la période)
            redemptions: Dict[str, Decimal] = {p.name: D(0) for p in products}

            for p in products:
                if p.kind != "fcpi" or not p.fcpi:
                    continue
                lots = fcpi_lots.get(p.name, [])

                if not lots:
                    continue
                remaining_lots: List[Tuple[int, Decimal]] = []

                for maturity_step, principal in lots:
                    if i >= maturity_step:
                        if p.fcpi.exit_mode == "full_value":
                            redeemed = value[p.name]
                        else:
                            redeemed = min(principal, value[p.name])

                        if redeemed > 0:
                            value[p.name] -= redeemed
                            value[cash_name] += redeemed
                            redemptions[p.name] += redeemed
                            # Invested doit devenir "net" (sinon gains faux si on retire)
                            invested[p.name] = max(D(0), invested[p.name] - redeemed)
                    else:
                        remaining_lots.append((maturity_step, principal))
                fcpi_lots[p.name] = remaining_lots

            cash_before = value[cash_name]

            # Budget investissable
            invest_budget = max(D(0), value[cash_name] - cfg.budget.emergency_fund_target)

            if cfg.budget.enforce_emergency_fund_first and value[cash_name] < cfg.budget.emergency_fund_target:
                invest_budget = D(0)

            # Demandes hors SCPI
            desired: Dict[str, Decimal] = {}

            for p in products:
                if p.name == cash_name:
                    continue

                if p.kind == "scpi" and p.scpi:
                    continue
                want = p.contribution_per_period + (p.contribution_pct_income * income_period)
                desired[p.name] = max(D(0), want)

            # Plan d'achat SCPI (parts) par période - basé sur dividend_frequency
            scpi_parts_plan_this_period: Dict[str, int] = {}

            for p in products:
                if p.kind == "scpi" and p.scpi:
                    # Acheter seulement aux périodes où on paie les dividendes

                    if should_pay_dividend(cfg.period, step_in_year, p.scpi.dividend_frequency):
                        n_payments = payments_per_year(p.scpi.dividend_frequency)
                        # Répartir équitablement les N parts sur les périodes de paiement
                        parts_this_time = int(p.scpi.parts_per_year) // n_payments
                        # Gérer le reste (ex: 10 parts en 4 paiements → 2,2,3,3)
                        remainder = int(p.scpi.parts_per_year) % n_payments
                        # Compter combien de paiements on a déjà fait cette année
                        payments_done = sum(1 for s in range(step_in_year) if should_pay_dividend(cfg.period, s, p.scpi.dividend_frequency))
                        # Si on est dans les premiers paiements du reste, ajouter +1

                        if payments_done < remainder:
                            parts_this_time += 1
                        scpi_parts_plan_this_period[p.name] = parts_this_time
                    else:
                        scpi_parts_plan_this_period[p.name] = 0

            contributions: Dict[str, Decimal] = {p.name: D(0) for p in products}
            dividends: Dict[str, Decimal] = {p.name: D(0) for p in products}

            remaining = invest_budget

            for p in sorted([x for x in products if x.name != cash_name], key=lambda x: x.priority):
                if remaining <= 0:
                    break

                if p.kind == "scpi" and p.scpi:
                    planned_parts = scpi_parts_plan_this_period.get(p.name, 0)

                    if planned_parts <= 0:
                        continue

                    price = scpi_part_price[p.name]
                    max_by_remaining_parts = int(floor(remaining / price)) if price > 0 else 0
                    max_by_cash_parts = int(floor(value[cash_name] / price)) if price > 0 else 0
                    parts_to_buy = min(planned_parts, max_by_remaining_parts, max_by_cash_parts)

                    if parts_to_buy <= 0:
                        continue

                    spent = D(parts_to_buy) * price
                    value[cash_name] -= spent
                    remaining -= spent

                    scpi_parts[p.name] = scpi_parts.get(p.name, 0) + parts_to_buy
                    value[p.name] = D(scpi_parts[p.name]) * scpi_part_price[p.name]

                    invested[p.name] += spent
                    contributions[p.name] += spent

                    continue

                want = desired.get(p.name, D(0))

                if want <= 0:
                    continue

                alloc = min(want, remaining)

                if value[cash_name] < alloc:
                    alloc = max(D(0), value[cash_name])

                if alloc <= 0:
                    continue

                value[cash_name] -= alloc
                remaining -= alloc

                value[p.name] += alloc
                invested[p.name] += alloc
                contributions[p.name] += alloc

                if p.kind == "per":
                    per_contrib_ytd += alloc

                if p.kind == "fcpi":
                    fcpi_contrib_ytd_by_product[p.name] = fcpi_contrib_ytd_by_product.get(p.name, D(0)) + alloc
                    # Enregistre un lot à maturité (début de l'année year_idx + holding_years)
                    holding = p.fcpi.holding_years if p.fcpi else 8
                    maturity_year_idx = year_idx + holding
                    maturity_step = (maturity_year_idx + 1) * n_per_year - 1  # Dernière période de l'année
                    fcpi_lots[p.name].append((maturity_step, alloc))

            cash_after = value[cash_name]

            # Rendements & dividendes

            for p in products:
                if p.kind == "scpi" and p.scpi:
                    r_revalo = periodic_rate(p.scpi.revaluation_annual, dt_years)
                    scpi_part_price[p.name] *= (D(1) + r_revalo)
                    value[p.name] = D(scpi_parts.get(p.name, 0)) * scpi_part_price[p.name]

                    if should_pay_dividend(cfg.period, step_in_year, p.scpi.dividend_frequency):
                        if cfg.period == "yearly":
                            div = value[p.name] * p.scpi.distribution_annual
                        else:
                            n_pay = payments_per_year(p.scpi.dividend_frequency)
                            div = value[p.name] * (p.scpi.distribution_annual / D(n_pay))

                        if div > 0:
                            dividends[p.name] += div

                            if p.scpi.dividends_to_cash:
                                value[cash_name] += div
                            else:
                                value[p.name] += div

                    continue

                r_p = periodic_rate(p.annual_return, dt_years)
                value[p.name] *= (D(1) + r_p)

            total_value = sum(value.values())
            total_value_real = (total_value / infl_idx) if infl_idx > 0 else total_value

            # Totaux "investissement" = uniquement hors cash (sinon le revenu/dépenses polluent)
            total_invested = sum(
                invested[p.name]

                for p in products

                if p.kind != "cash"
            )

            # Gains réels (inflation) uniquement hors cash, cohérent avec total_value_real
            total_gains = sum(
                ((value[p.name] / infl_idx) if infl_idx > 0 else value[p.name]) - invested[p.name]

                for p in products

                if p.kind != "cash"
            )

            # Plafond PER = 10% revenu N-1

            if year_idx == 0:
                income_prev = cfg.income.gross_annual_previous if cfg.income.gross_annual_previous is not None else income_annual
            else:
                income_prev = income_annual_by_year[year_idx - 1]
            per_cap_for_year = compute_per_cap_from_income_prev(income_prev, cfg.per_cap)

            tax_due_for_year: Optional[Decimal] = None
            fcpi_tax_reduction_for_year: Optional[Decimal] = None

            # Fin d'année: calcul impôt dû N (PER déduit + réduction FCPI), payé en N+1

            if step_in_year == n_per_year - 1:
                taxable_base = max(D(0), income_annual * (D(1) - cfg.tax.standard_deduction_rate))
                per_deduction = min(per_contrib_ytd, per_cap_for_year)
                taxable_after_per = max(D(0), taxable_base - per_deduction)

                tax_due = compute_progressive_tax(taxable_after_per, cfg.tax)

                # Réduction FCPI (agrégée par produit, capée)
                tax_due_before_fcpi = tax_due  # impôt avant réduction FCPI

                fcpi_reduction_total = D(0)

                for p in products:
                    if p.kind != "fcpi" or not p.fcpi:
                        continue
                    contrib_y = fcpi_contrib_ytd_by_product.get(p.name, D(0))
                    eligible = min(contrib_y, p.fcpi.annual_eligible_cap)
                    fcpi_reduction_total += eligible * p.fcpi.tax_reduction_rate

                # Réduction "effective" (on ne peut pas réduire plus que l'impôt dû)
                fcpi_tax_reduction_for_year = min(fcpi_reduction_total, tax_due_before_fcpi)

                tax_due = max(D(0), tax_due_before_fcpi - fcpi_reduction_total)

                tax_due_by_year[year_idx] = tax_due
                tax_due_for_year = tax_due

                # Reset annuels
                per_contrib_ytd = D(0)

                for k in list(fcpi_contrib_ytd_by_product.keys()):
                    fcpi_contrib_ytd_by_product[k] = D(0)

            rows.append(
                SimulationRow(
                    period_index=i,
                    year_index=year_idx,
                    year_number=year_number,
                    step_in_year=step_in_year,
                    income_annual=income_annual,
                    income_period=income_period,
                    living_costs_period=living_costs_period,
                    tax_paid_period=tax_paid_period,
                    tax_paid_year_to_date=tax_paid_ytd,
                    tax_due_for_year=tax_due_for_year,
                    fcpi_tax_reduction_for_year=fcpi_tax_reduction_for_year,
                    per_cap_for_year=per_cap_for_year,
                    per_contrib_year_to_date=per_contrib_ytd,
                    cash_before_invest=cash_before,
                    cash_after_invest=cash_after,
                    contributions_by_product={k: v for k, v in contributions.items()},
                    dividends_by_product={k: v for k, v in dividends.items()},
                    scpi_parts_by_product={k: (scpi_parts.get(k, 0)) for k in product_names},
                    redemptions_by_product={k: v for k, v in redemptions.items()},
                    value_by_product={k: v for k, v in value.items()},
                    invested_by_product={k: v for k, v in invested.items()},
                    total_value=total_value,
                    total_value_real=total_value_real,
                    total_invested=total_invested,
                    total_gains=total_gains,
                    inflation_index=infl_idx,
                )
            )

        tax_due_next_year = tax_due_by_year.get(cfg.years - 1, D(0))

        return SimulationResult(
            rows=rows,
            product_names=product_names,
            cash_product=cash_name,
            tax_due_next_year=tax_due_next_year,
        )
