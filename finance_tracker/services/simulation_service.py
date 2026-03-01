"""Complete simulator service"""
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
    """Convert a value to a Decimal for precise financial calculations.

    Converts the input to a string first to avoid floating-point precision issues.
    """

    return Decimal(str(x))


def steps_per_year(period: Period) -> int:
    """Return the number of periods per year for a given period type.

    Parameters
    ----------
        period: The period type ('monthly', 'quarterly', or 'annual').

    Returns
    -------
        Number of periods per year (12, 4, or 1 respectively).
    """

    if period == "monthly":
        return 12

    if period == "quarterly":
        return 4

    return 1


def periodic_rate(annual_rate: Decimal, dt_years: Decimal) -> Decimal:
    """Calculate the periodic interest rate from an annual rate.

    Parameters
    ----------
        annual_rate: The annual interest rate as a Decimal.
        dt_years: The time period in years as a Decimal.

    Returns
    -------
        The periodic interest rate as a Decimal.
    """

    return (D(1) + annual_rate) ** dt_years - D(1)


@dataclass
class IncomeConfig:
    """Configuration for income simulation.

    Defines the gross annual income and its growth rate over time.
    """
    gross_annual_start: Decimal
    annual_growth: Decimal
    gross_annual_previous: Optional[Decimal] = None  # revenu N-1 (PER 10% N-1)


@dataclass
class BudgetConfig:
    """Configuration for budget and emergency fund settings.

    Defines living costs and emergency fund requirements.
    """
    annual_living_costs: Decimal
    emergency_fund_target: Decimal
    enforce_emergency_fund_first: bool = True


@dataclass
class TaxBracket:
    """Represents a tax bracket with its upper limit and rate.

    Attributes
    ----------
        up_to: The upper limit of the bracket (None for the last bracket).
        rate: The tax rate for this bracket.
    """
    up_to: Optional[Decimal]
    rate: Decimal


@dataclass
class TaxConfig:
    """Configuration for tax calculation.

    Defines tax brackets, household parts, deductions, and initial tax due.
    """
    brackets: List[TaxBracket]
    household_parts: Decimal = D(1)
    standard_deduction_rate: Decimal = D(0.10)
    initial_tax_due_annual: Decimal = D(0)


@dataclass
class PERCapConfig:
    """Configuration for PER (Plan d'Épargne Retraite) capital limits.

    Defines the percentage of previous year's income and annual limits.
    """
    rate_of_income_prev_year: Decimal = D(0.10)
    annual_min: Decimal = D(0)
    annual_max: Optional[Decimal] = None


@dataclass
class PERConfig:
    """Configuration for PER (Plan d'Épargne Retraite) settings.

    Currently empty placeholder for future PER-specific configuration.
    """
    pass


@dataclass
class FCPIConfig:
    """Configuration for FCPI (Fonds Communs de Placement dans l'Innovation).

    Defines tax reduction rate, annual caps, holding period, and exit mode.
    """
    tax_reduction_rate: Decimal = D(0.18)     # ex: 18%
    annual_eligible_cap: Decimal = D(12000)   # configurable (ex: 12k)
    holding_years: int = 8
    exit_mode: FCPIExitMode = "principal"     # principal (par défaut) ou full_value


@dataclass
class SCPIConfig:
    """Configuration for SCPI (Société Civile de Placement Immobilier).

    Defines part price, acquisition rate, distribution, and revaluation.
    """
    part_price: Decimal
    parts_per_year: int
    distribution_annual: Decimal
    dividends_to_cash: bool = True
    revaluation_annual: Decimal = D(0)
    dividend_frequency: DividendFrequency = "quarterly"  # NOUVEAU


@dataclass
class ProductSimConfig:
    """Configuration for a single investment product in the simulation.

    Defines product name, type, returns, contributions, and product-specific settings.
    """
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
    """Main configuration for a complete financial simulation.

    Defines simulation period, inflation, income, budget, tax, and PER settings.
    """
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
    """Represents a single period row in the simulation results.

    Contains all financial data for one simulation period including income,
    taxes, contributions, values, and dividends.
    """
    # Period identification: tracks position in simulation timeline
    period_index: int
    year_index: int
    year_number: int
    step_in_year: int

    # Income and expenses for the current period
    income_annual: Decimal
    income_period: Decimal
    living_costs_period: Decimal

    # Tax tracking: paid this period vs year-to-date, plus year-end settlement
    tax_paid_period: Decimal
    tax_paid_year_to_date: Decimal
    tax_due_for_year: Optional[Decimal]

    # FCPI: tax reduction calculated at year-end (based on FCPI contributions)
    fcpi_tax_reduction_for_year: Optional[Decimal]

    # Personal contribution caps and tracking (versements PER)
    per_cap_for_year: Decimal
    per_contrib_year_to_date: Decimal

    # Cash flow: available before investment decisions, after executing them
    cash_before_invest: Decimal
    cash_after_invest: Decimal

    # Product-level tracking: contributions made, dividends received, SCPI units acquired
    contributions_by_product: Dict[str, Decimal]
    dividends_by_product: Dict[str, Decimal]
    scpi_parts_by_product: Dict[str, int]

    # FCPI: montants sortis cette période (cash-in)
    redemptions_by_product: Dict[str, Decimal]

    # Current market value and total invested per product
    value_by_product: Dict[str, Decimal]
    invested_by_product: Dict[str, Decimal]

    # Aggregated totals across all products
    total_value: Decimal
    total_invested: Decimal
    total_gains: Decimal

    # Inflation adjustment: converts nominal values to real purchasing power
    inflation_index: Decimal
    total_value_real: Decimal


@dataclass
class SimulationResult:
    """Contains the complete results of a financial simulation.

    Includes all simulation rows, product names, cash product identifier,
    and carryforward tax due.
    """
    rows: List[SimulationRow]
    product_names: List[str]
    cash_product: str
    tax_due_next_year: Decimal


def compute_progressive_tax(taxable: Decimal, tax_cfg: TaxConfig) -> Decimal:
    """Compute progressive tax for a given taxable amount and tax configuration.

    Applies tax brackets sequentially to each household part, summing the results.

    Parameters
    ----------
    taxable : Decimal
        The total taxable income amount.
    tax_cfg : TaxConfig
        Tax configuration containing brackets and household parts.

    Returns
    -------
    Decimal
        The computed total tax amount.
    """
    # No tax on non-positive income

    if taxable <= 0:
        return D(0)

    # Ensure at least one part to avoid division by zero
    parts = max(tax_cfg.household_parts, D(1))
    # Apply tax to each part separately, then sum (standard progressive taxation)
    taxable_per_part = taxable / parts

    t = D(0)
    prev = D(0)

    for b in tax_cfg.brackets:
        upper = b.up_to

        # Unlimited top bracket: tax remaining income at this rate

        if upper is None:
            t += (taxable_per_part - prev) * b.rate

            break

        # Calculate taxable amount within current bracket
        band = min(taxable_per_part, upper) - prev

        # Only apply rate if income falls within this bracket

        if band > 0:
            t += band * b.rate
        prev = upper

        # Stop early if we've processed all taxable income

        if taxable_per_part <= upper:
            break

    # Multiply by household parts; ensure non-negative result

    return max(t, D(0)) * parts


def compute_per_cap_from_income_prev(income_prev: Decimal, per_cap: PERCapConfig) -> Decimal:
    """Calculate per-capita amount based on previous year's income.

    Applies income-based rate with configurable minimum and maximum thresholds.

    Parameters
    ----------
    income_prev : Decimal
        The previous year's income amount.
    per_cap : PERCapConfig
        Configuration object containing rate, annual_min, and optional annual_max.

    Returns
    -------
    Decimal
        The calculated per-capita amount after applying income rate and constraints.
    """
    # Apply income-based rate to determine initial cap
    cap = income_prev * per_cap.rate_of_income_prev_year
    # Enforce minimum threshold regardless of income
    cap = max(cap, per_cap.annual_min)

    # Apply maximum ceiling only if configured (optional constraint)

    if per_cap.annual_max is not None:
        cap = min(cap, per_cap.annual_max)

    # Guard against negative values as safety net

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
    """Convert dividend frequency to number of payments per year.

    Maps common frequency strings to their annual payment count.

    Parameters
    ----------
    freq : DividendFrequency
        The dividend frequency (e.g., 'monthly', 'quarterly', 'semiannual', 'annual').

    Returns
    -------
    int
        Number of dividend payments per year.
    """

    if freq == "monthly":
        return 12

    if freq == "quarterly":
        return 4

    if freq == "semiannual":
        return 2

    return 1


def should_pay_dividend(period: Period, step_in_year: int, freq: DividendFrequency) -> bool:
    """
    Determine if a dividend should be paid based on reporting period, step, and frequency.

    This function evaluates the reporting period, step within the year, and dividend
    frequency to determine whether a dividend payment is due.

    Parameters
    ----------
    period : Period
        The reporting period type, either "yearly", "quarterly", or "monthly".
    step_in_year : int
        The step index within the year (0-11 for monthly, 0-3 for quarterly).
    freq : DividendFrequency
        The dividend payment frequency: "monthly", "quarterly", "semiannual", or "annual".

    Returns
    -------
    bool
        True if a dividend should be paid for the given period, step, and frequency;
        False otherwise.
    """
    # Yearly reporting: dividend paid once per year regardless of frequency

    if period == "yearly":
        return True  # une fois par an

    if period == "quarterly":
        # 4 steps: 0..3

        # Dividend frequency meets or exceeds reporting frequency

        if freq in ("monthly", "quarterly"):
            return True

        # Semiannual dividend aligns with quarter 1 (mid-year) and quarter 3 (year-end)

        if freq == "semiannual":
            return step_in_year in (1, 3)  # fin S1 et fin S2

        # Annual dividend paid at year-end (quarter 3)

        return step_in_year == 3
    # monthly

    # Monthly frequency: dividend paid every month

    if freq == "monthly":
        return True

    # Quarterly dividend aligns with quarter-end months (Mar, Jun, Sep, Dec)

    if freq == "quarterly":
        return step_in_year in (2, 5, 8, 11)

    # Semiannual dividend aligns with half-year and year-end (Jun, Dec)

    if freq == "semiannual":
        return step_in_year in (5, 11)

    # Annual dividend paid at year-end

    return step_in_year == 11


class SimulationService:
    """
    Service for running multi-product financial simulations.

    This service orchestrates the simulation of a portfolio containing various
    financial products (cash, SCPI, FCPI, PER, etc.) over multiple years,
    accounting for income, expenses, taxes, dividends, and inflation.

    The simulation runs in discrete time steps (monthly, quarterly, or yearly)
    and tracks the evolution of each product's value, contributions, and returns.

    Attributes
    ----------
    None : This is a stateless service.

    Methods
    -------
    run(cfg, products)
        Execute the simulation with the given configuration and products.

    Examples
    --------
    >>> service = SimulationService()
    >>> config = SimulationConfig(years=10, period="monthly", ...)
    >>> products = [ProductSimConfig(name="Cash", kind="cash", ...), ...]
    >>> result = service.run(config, products)
    >>> print(result.rows[0].total_value)
    """

    def run(self, cfg: SimulationConfig, products: List[ProductSimConfig]) -> SimulationResult:
        """
        Execute the financial simulation over the configured time period.

        This method runs a discrete-time simulation that models the evolution
        of a portfolio containing multiple financial products. It handles:

        - Income generation and living expenses
        - Tax calculations (progressive tax, PER deductions, FCPI reductions)
        - SCPI dividend payments and revaluation
        - FCPI maturity and redemption
        - PER contribution tracking
        - Inflation adjustment for real returns

        Parameters
        ----------
        cfg : SimulationConfig
            Global simulation configuration including years, period granularity,
            inflation rate, income parameters, budget settings, and tax rules.
        products : List[ProductSimConfig]
            List of product configurations to simulate. Must contain exactly
            one product of kind "cash" which serves as the liquidity buffer.

        Returns
        -------
        SimulationResult
            Object containing all simulation rows with period-by-period data,
            product names, cash product identifier, and pending tax for next year.

        Raises
        ------
        ValueError
            If no cash product is found in the products list.
            If multiple cash products are detected (ambiguous).

        Examples
        --------
        >>> service = SimulationService()
        >>> result = service.run(config, products)
        >>> for row in result.rows:
        ...     print(f"Year {row.year_number}: {row.total_value:.2f}€")

        Notes
        -----
        The simulation uses Decimal for precise financial calculations.
        All monetary values are in euros (EUR).

        The cash product is special: it receives income, pays expenses and taxes,
        and serves as the source for all investments into other products.

        FCPI lots are tracked separately to handle maturity-based redemptions.
        Each FCPI contribution creates a "lot" that matures after holding_years.
        """
        # Calculate number of periods per year and time step
        n_per_year = steps_per_year(cfg.period)
        dt_years = D(1) / D(n_per_year)
        n_steps = cfg.years * n_per_year

        # Identify the cash product (required exactly one)
        cash_candidates = [p.name for p in products if p.kind == "cash"]

        if not cash_candidates:
            raise ValueError("Simulation: at least one 'cash' product is required.")

        if len(cash_candidates) > 1:
            raise ValueError(
                f"Simulation: multiple 'cash' products detected: {cash_candidates}. "
                "Please keep only one."
                )
        cash_name = cash_candidates[0]

        product_names = [p.name for p in products]

        # Initialize tracking dictionaries for each product
        value: Dict[str, Decimal] = {}           # Current nominal value
        invested: Dict[str, Decimal] = {}        # Total amount invested (cost basis)
        scpi_parts: Dict[str, int] = {}          # Number of SCPI parts owned
        scpi_part_price: Dict[str, Decimal] = {}  # Current price per SCPI part

        # FCPI lots: each lot tracks (maturity_step_index, principal_amount)
        # This allows tracking multiple FCPI investments with different maturity dates
        fcpi_lots: Dict[str, List[Tuple[int, Decimal]]] = {}

        # Initialize product values and invested amounts

        for p in products:
            # Initial invested amount defaults to initial value if not specified
            inv0 = p.initial_invested_eur if p.initial_invested_eur is not None else p.initial_value_eur

            if p.kind == "scpi" and p.scpi:
                # SCPI: track parts and part price separately
                scpi_part_price[p.name] = p.scpi.part_price
                parts0 = p.initial_scpi_parts

                # Calculate initial parts from value if not provided

                if parts0 is None:
                    parts0 = int(floor(p.initial_value_eur / p.scpi.part_price)) if p.scpi.part_price > 0 else 0

                scpi_parts[p.name] = max(0, int(parts0))
                value[p.name] = D(scpi_parts[p.name]) * scpi_part_price[p.name]
                invested[p.name] = inv0
            else:
                # Other products: value equals monetary amount
                value[p.name] = p.initial_value_eur
                invested[p.name] = inv0

            # Initialize empty lots list for FCPI products

            if p.kind == "fcpi":
                fcpi_lots[p.name] = []

        # Inflation index (starts at 1, compounds over time)
        infl_idx = D(1)

        # Tax tracking: amount due per year (paid in following year)
        tax_due_by_year: Dict[int, Decimal] = {}
        tax_paid_ytd = D(0)
        tax_to_pay_this_year_annual = cfg.tax.initial_tax_due_annual

        # PER contribution tracking (for tax deduction cap calculation)
        per_contrib_ytd = D(0)

        # FCPI contributions tracking per year (for tax reduction calculation)
        fcpi_contrib_ytd_by_product: Dict[str, Decimal] = {
            p.name: D(0) for p in products if p.kind == "fcpi"
            }

        # Store annual income by year (needed for PER cap calculation in year N+1)
        income_annual_by_year: Dict[int, Decimal] = {}

        # Results storage
        rows: List[SimulationRow] = []

        # Main simulation loop

        for i in range(n_steps):
            year_idx = i // n_per_year          # Zero-based year index
            step_in_year = i % n_per_year       # Position within the year (0 to n_per_year-1)
            year_number = year_idx + 1          # Human-readable year number (1-based)

            # At the start of each year, set up tax payment for the year
            # Year 0: use initial tax due from config
            # Year N: pay tax calculated at end of year N-1

            if step_in_year == 0:
                if year_idx == 0:
                    tax_to_pay_this_year_annual = cfg.tax.initial_tax_due_annual
                else:
                    tax_to_pay_this_year_annual = tax_due_by_year.get(year_idx - 1, D(0))
                tax_paid_ytd = D(0)

            # Compound inflation index
            infl_idx *= (D(1) + cfg.inflation_annual) ** dt_years

            # Calculate income for this year (with annual growth)
            income_annual = cfg.income.gross_annual_start * ((D(1) + cfg.income.annual_growth) ** D(year_idx))
            income_annual_by_year[year_idx] = income_annual
            income_period = income_annual * dt_years

            # Apply income to cash
            value[cash_name] += income_period

            # Deduct living costs
            living_costs_period = cfg.budget.annual_living_costs * dt_years
            value[cash_name] -= living_costs_period

            # Deduct tax payment (spread evenly across periods)
            tax_paid_period = (tax_to_pay_this_year_annual * dt_years)
            value[cash_name] -= tax_paid_period
            tax_paid_ytd += tax_paid_period

            # Process FCPI maturities: credit cash for matured lots
            redemptions: Dict[str, Decimal] = {p.name: D(0) for p in products}

            for p in products:
                if p.kind != "fcpi" or not p.fcpi:
                    continue

                lots = fcpi_lots.get(p.name, [])

                if not lots:
                    continue

                remaining_lots: List[Tuple[int, Decimal]] = []

                for maturity_step, principal in lots:
                    # Check if this lot has matured

                    if i >= maturity_step:
                        # Determine redemption amount based on exit mode

                        if p.fcpi.exit_mode == "full_value":
                            redeemed = value[p.name]
                        else:
                            # Capital preservation mode: redeem up to principal
                            redeemed = min(principal, value[p.name])

                        if redeemed > 0:
                            # Transfer from FCPI to cash
                            value[p.name] -= redeemed
                            value[cash_name] += redeemed
                            redemptions[p.name] += redeemed
                            # Adjust invested amount to prevent artificial gains
                            invested[p.name] = max(D(0), invested[p.name] - redeemed)
                    else:
                        # Lot not yet matured, keep tracking
                        remaining_lots.append((maturity_step, principal))

                fcpi_lots[p.name] = remaining_lots

            # Record cash before investments
            cash_before = value[cash_name]

            # Calculate investment budget (cash above emergency fund threshold)
            invest_budget = max(D(0), value[cash_name] - cfg.budget.emergency_fund_target)

            # Optionally enforce emergency fund before any investing

            if cfg.budget.enforce_emergency_fund_first and value[cash_name] < cfg.budget.emergency_fund_target:
                invest_budget = D(0)

            # Calculate desired contributions for non-SCPI products
            desired: Dict[str, Decimal] = {}

            for p in products:
                if p.name == cash_name:
                    continue

                # SCPI handled separately (parts-based)

                if p.kind == "scpi" and p.scpi:
                    continue

                # Desired contribution = fixed amount + percentage of income
                want = p.contribution_per_period + (p.contribution_pct_income * income_period)
                desired[p.name] = max(D(0), want)

            # Calculate SCPI parts to buy this period (based on dividend payment schedule)
            scpi_parts_plan_this_period: Dict[str, int] = {}

            for p in products:
                if p.kind == "scpi" and p.scpi:
                    # Only buy SCPI parts on dividend payment periods
                    # This aligns purchases with income from distributions

                    if should_pay_dividend(cfg.period, step_in_year, p.scpi.dividend_frequency):
                        n_payments = payments_per_year(p.scpi.dividend_frequency)
                        # Distribute parts evenly across payment periods
                        parts_this_time = int(p.scpi.parts_per_year) // n_payments
                        # Handle remainder (e.g., 10 parts over 4 payments → 2,2,3,3)
                        remainder = int(p.scpi.parts_per_year) % n_payments
                        # Count how many payments already made this year
                        payments_done = sum(
                            1 for s in range(step_in_year)

                            if should_pay_dividend(cfg.period, s, p.scpi.dividend_frequency)
                            )
                        # Add extra part for first 'remainder' payments

                        if payments_done < remainder:
                            parts_this_time += 1
                        scpi_parts_plan_this_period[p.name] = parts_this_time
                    else:
                        scpi_parts_plan_this_period[p.name] = 0

            # Initialize contribution and dividend tracking for this period
            contributions: Dict[str, Decimal] = {p.name: D(0) for p in products}
            dividends: Dict[str, Decimal] = {p.name: D(0) for p in products}

            remaining = invest_budget

            # Execute investments by priority order

            for p in sorted([x for x in products if x.name != cash_name], key=lambda x: x.priority):
                if remaining <= 0:
                    break

                # Handle SCPI investments (parts-based)

                if p.kind == "scpi" and p.scpi:
                    planned_parts = scpi_parts_plan_this_period.get(p.name, 0)

                    if planned_parts <= 0:
                        continue

                    price = scpi_part_price[p.name]
                    # Maximum parts affordable with remaining budget
                    max_by_remaining_parts = int(floor(remaining / price)) if price > 0 else 0
                    # Maximum parts affordable with actual cash
                    max_by_cash_parts = int(floor(value[cash_name] / price)) if price > 0 else 0
                    parts_to_buy = min(planned_parts, max_by_remaining_parts, max_by_cash_parts)

                    if parts_to_buy <= 0:
                        continue

                    spent = D(parts_to_buy) * price
                    value[cash_name] -= spent
                    remaining -= spent

                    # Update SCPI holdings
                    scpi_parts[p.name] = scpi_parts.get(p.name, 0) + parts_to_buy
                    value[p.name] = D(scpi_parts[p.name]) * scpi_part_price[p.name]

                    invested[p.name] += spent
                    contributions[p.name] += spent

                    continue

                # Handle non-SCPI investments (monetary amount)
                want = desired.get(p.name, D(0))

                if want <= 0:
                    continue

                alloc = min(want, remaining)

                # Ensure we don't exceed available cash

                if value[cash_name] < alloc:
                    alloc = max(D(0), value[cash_name])

                if alloc <= 0:
                    continue

                value[cash_name] -= alloc
                remaining -= alloc

                value[p.name] += alloc
                invested[p.name] += alloc
                contributions[p.name] += alloc

                # Track PER contributions for tax deduction cap

                if p.kind == "per":
                    per_contrib_ytd += alloc

                # Track FCPI contributions for tax reduction

                if p.kind == "fcpi":
                    fcpi_contrib_ytd_by_product[p.name] = fcpi_contrib_ytd_by_product.get(p.name, D(0)) + alloc
                    # Create a lot that matures after holding_years
                    holding = p.fcpi.holding_years if p.fcpi else 8
                    maturity_year_idx = year_idx + holding
                    # Matures at the last period of the target year
                    maturity_step = (maturity_year_idx + 1) * n_per_year - 1
                    fcpi_lots[p.name].append((maturity_step, alloc))

            cash_after = value[cash_name]

            # Apply returns and dividends for all products

            for p in products:
                if p.kind == "scpi" and p.scpi:
                    # SCPI: apply revaluation to part price
                    r_revalo = periodic_rate(p.scpi.revaluation_annual, dt_years)
                    scpi_part_price[p.name] *= (D(1) + r_revalo)
                    value[p.name] = D(scpi_parts.get(p.name, 0)) * scpi_part_price[p.name]

                    # Pay dividends on scheduled periods

                    if should_pay_dividend(cfg.period, step_in_year, p.scpi.dividend_frequency):
                        if cfg.period == "yearly":
                            div = value[p.name] * p.scpi.distribution_annual
                        else:
                            n_pay = payments_per_year(p.scpi.dividend_frequency)
                            div = value[p.name] * (p.scpi.distribution_annual / D(n_pay))

                        if div > 0:
                            dividends[p.name] += div

                            # Distribute to cash or reinvest

                            if p.scpi.dividends_to_cash:
                                value[cash_name] += div
                            else:
                                value[p.name] += div

                    continue

                # Other products: apply simple return rate
                r_p = periodic_rate(p.annual_return, dt_years)
                value[p.name] *= (D(1) + r_p)

            # Calculate totals
            total_value = sum(value.values())
            total_value_real = (total_value / infl_idx) if infl_idx > 0 else total_value

            # Total invested excludes cash (income/expenses would distort it)
            total_invested = sum(
                invested[p.name]

                for p in products

                if p.kind != "cash"
                )

            # Real gains (inflation-adjusted) exclude cash
            total_gains = sum(
                ((value[p.name] / infl_idx) if infl_idx > 0 else value[p.name]) - invested[p.name]

                for p in products

                if p.kind != "cash"
                )

            # Calculate PER contribution cap (based on previous year income)

            if year_idx == 0:
                income_prev = (
                    cfg.income.gross_annual_previous

                    if cfg.income.gross_annual_previous is not None
                    else income_annual
                    )
            else:
                income_prev = income_annual_by_year[year_idx - 1]
            per_cap_for_year = compute_per_cap_from_income_prev(income_prev, cfg.per_cap)

            # Initialize year-end calculations
            tax_due_for_year: Optional[Decimal] = None
            fcpi_tax_reduction_for_year: Optional[Decimal] = None

            # End of year: calculate tax due (paid in following year)

            if step_in_year == n_per_year - 1:
                # Calculate taxable income after standard deduction
                taxable_base = max(D(0), income_annual * (D(1) - cfg.tax.standard_deduction_rate))

                # Apply PER deduction (capped)
                per_deduction = min(per_contrib_ytd, per_cap_for_year)
                taxable_after_per = max(D(0), taxable_base - per_deduction)

                tax_due = compute_progressive_tax(taxable_after_per, cfg.tax)

                # Calculate FCPI tax reduction (25% of eligible contributions, capped per product)
                tax_due_before_fcpi = tax_due
                fcpi_reduction_total = D(0)

                for p in products:
                    if p.kind != "fcpi" or not p.fcpi:
                        continue
                    contrib_y = fcpi_contrib_ytd_by_product.get(p.name, D(0))
                    eligible = min(contrib_y, p.fcpi.annual_eligible_cap)
                    fcpi_reduction_total += eligible * p.fcpi.tax_reduction_rate

                # Tax reduction cannot exceed tax due
                fcpi_tax_reduction_for_year = min(fcpi_reduction_total, tax_due_before_fcpi)

                tax_due = max(D(0), tax_due_before_fcpi - fcpi_reduction_total)

                tax_due_by_year[year_idx] = tax_due
                tax_due_for_year = tax_due

                # Reset annual trackers
                per_contrib_ytd = D(0)

                for k in list(fcpi_contrib_ytd_by_product.keys()):
                    fcpi_contrib_ytd_by_product[k] = D(0)

            # Record this period's data
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

        # Tax due for the year after simulation ends
        tax_due_next_year = tax_due_by_year.get(cfg.years - 1, D(0))

        return SimulationResult(
            rows=rows,
            product_names=product_names,
            cash_product=cash_name,
            tax_due_next_year=tax_due_next_year,
            )
