"""
CLI Typer - Command-line interface for Finance Tracker.

This module provides a comprehensive command-line interface for managing
financial portfolios, including products, transactions, valuations,
and reporting capabilities.

The CLI is built with Typer and provides commands for:
- Database management (init, seed)
- Product CRUD operations
- Transaction management
- Valuation tracking
- Bitcoin price updates
- Dashboard display
- Investment projections
- Documentation generation
- PDF report export

Installation
------------
The CLI is installed as part of the finance-tracker package:

    pip install finance-tracker

Usage
-----
    finance-tracker --help              # Show all commands
    finance-tracker init-db             # Initialize database
    finance-tracker seed-products       # Create default products
    finance-tracker dashboard           # Display portfolio summary
    finance-tracker update-btc          # Fetch BTC price and create valuation

Commands Overview
-----------------
Database Commands:
    init-db-cmd         Initialize the database schema
    seed-products       Create default product templates

Listing Commands:
    list-products       Display all products in a table
    list-transactions   Display transactions with optional filters
    list-valuations     Display valuations with optional filters

Add Commands:
    add-transaction     Add a new transaction
    add-valuation       Add a new valuation snapshot

Bitcoin Commands:
    update-btc          Fetch current BTC/EUR price and create valuation

Display Commands:
    dashboard           Display portfolio dashboard
    project             Calculate compound interest projection

Export Commands:
    product-doc         Generate markdown documentation for products
    export-pdf          Generate PDF portfolio report

Examples
--------
Initialize and seed the database:

    $ finance-tracker init-db
    $ finance-tracker seed-products

Add a transaction:

    $ finance-tracker add-transaction \\
        --product-name "SCPI" \\
        --transaction-type "BUY" \\
        --amount "2500" \\
        --quantity "10" \\
        --date "2024-01-15"

View the dashboard:

    $ finance-tracker dashboard
    $ finance-tracker dashboard --json  # JSON output

Project compound growth:

    $ finance-tracker project \\
        --initial-amount 10000 \\
        --monthly-contribution 500 \\
        --annual-return 0.08 \\
        --years 20

See Also
--------
finance_tracker.web.app : Streamlit web interface
finance_tracker.services.dashboard_service : Dashboard business logic
"""

from tabulate import tabulate
from datetime import datetime
from decimal import Decimal

import typer
from sqlmodel import Session, create_engine
from sqlmodel import SQLModel

from finance_tracker.config import DATABASE_URL, DOCS_DIR
from finance_tracker.domain.enums import ProductType, QuantityUnit, TransactionType
from finance_tracker.domain.models import Product, RateSchedule, Transaction, Valuation
from finance_tracker.repositories.sqlmodel_repo import (
    SQLModelProductRepository,
    SQLModelTransactionRepository,
    SQLModelValuationRepository,
    SQLModelRateScheduleRepository,
    init_db,
    )
from finance_tracker.services.btc_price_service import BTCPriceService, BTCPriceServiceError
from finance_tracker.services.dashboard_service import DashboardService
from finance_tracker.services.doc_service import DocService
from finance_tracker.services.pdf_report_service import PDFReportService
from finance_tracker.services.projection_service import ProjectionResult, ProjectionFrequency
from finance_tracker.services.seed_service import seed_default_products
from finance_tracker.utils.money import to_decimal

# Create the Typer application instance
app = typer.Typer(help="Finance Tracker - Suivi portefeuille d'investissement")


def get_session() -> Session:
    """
    Create and return a new database session.

    This function initializes a database connection using the DATABASE_URL
    configuration and returns a SQLModel session associated with this connection.

    Returns
    -------
    Session
        A SQLModel session instance connected to the database.

    Notes
    -----
    Each call creates a new engine and session. This is suitable for CLI
    commands that run once per invocation. For long-running applications,
    consider using a session factory or dependency injection.

    Examples
    --------
    >>> session = get_session()
    >>> repo = SQLModelProductRepository(session)
    >>> products = repo.get_all()
    """
    engine = create_engine(DATABASE_URL, echo=False)

    return Session(engine)


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@app.command()
def init_db_cmd() -> None:
    """
    Initialize the database schema.

    This command creates all necessary tables in the database if they
    do not already exist. It should be run once when setting up the
    application for the first time.

    Raises
    ------
    Exception
        If an error occurs during database initialization.

    Examples
    --------
    $ finance-tracker init-db
    ✅ Base de données initialisée
    """
    init_db()
    typer.echo("✅ Base de données initialisée")


@app.command()
def seed_products() -> None:
    """
    Create default product templates in the database.

    This command creates a set of predefined financial products commonly
    used in French portfolios:

    - Cash: Liquid treasury accounts
    - Épargne: Regulated savings accounts (Livret A, LDDS, CEL)
    - SCPI: Real estate investment trusts (parts)
    - Bitcoin: Cryptographic asset
    - Assurance Vie: Life insurance contracts
    - PER: Retirement savings plans
    - FCPI: Innovation investment funds

    It also creates a default 3% annual rate for the "Épargne" product.

    Notes
    -----
    Products are only created if they don't already exist in the database.
    This command is idempotent and can be run multiple times safely.

    Examples
    --------
    $ finance-tracker seed-products
    ✅ 7 produits par défaut créés
    """
    session = get_session()
    created_count = seed_default_products(session)

    if created_count > 0:
        typer.echo(f"✅ {created_count} produits par défaut créés")
    else:
        typer.echo("✅ Les produits existent déjà")

# ═══════════════════════════════════════════════════════════════════════════════
# LISTING COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════


@app.command()
def list_products() -> None:
    """
    List all products in a formatted table.

    Displays a table with product ID, name, type, and quantity unit
    for all products in the database.

    Examples
    --------
    $ finance-tracker list-products
    ╒══════╤═════════════════╤══════════╤═════════════╕
    │   ID │ Nom             │ Type     │ Unité       │
    ╞══════╪═════════════════╪══════════╪═════════════╡
    │    1 │ Cash            │ CASH     │ NONE        │
    │    2 │ Épargne         │ SAVINGS  │ NONE        │
    │    3 │ SCPI            │ SCPI     │ SCPI_SHARES │
    ╘══════╧═════════════════╧══════════╧═════════════╛
    """
    session = get_session()
    repo = SQLModelProductRepository(session)
    products = repo.get_all()

    table = [(p.id, p.name, p.type, p.quantity_unit) for p in products]
    headers = ["ID", "Nom", "Type", "Unité"]
    typer.echo(tabulate(table, headers=headers, tablefmt="fancy_grid"))


@app.command()
def list_transactions(
        product_name=None,
        limit: int = typer.Option(50, "--limit"),
        ) -> None:
    """
    List transactions in a formatted table.

    Displays a table with transaction date, type, amount, quantity,
    and note. Can be filtered by product name and limited in count.

    Parameters
    ----------
    product_name : str, optional
        Filter transactions by product name. If None, shows all transactions.
    limit : int
        Maximum number of transactions to display (default: 50).

    Examples
    --------
    Show last 50 transactions:

    $ finance-tracker list-transactions

    Show last 20 transactions for SCPI:

    $ finance-tracker list-transactions --product-name "SCPI" --limit 20
    """
    session = get_session()
    repo = SQLModelTransactionRepository(session)
    transactions = repo.get_all()

    # Apply product filter if specified

    if product_name:
        product_repo = SQLModelProductRepository(session)
        product = product_repo.get_by_name(product_name)

        if product:
            transactions = repo.get_by_product_id(product.id or 0)

    # Limit the number of transactions displayed
    transactions = transactions[-limit:]

    table = [
        (
            tx.date.date(),
            tx.type,
            f"{tx.amount_eur}€" if tx.amount_eur is not None else "",
            tx.quantity if tx.quantity is not None else "",
            tx.note
            )

        for tx in transactions
        ]
    headers = ["Date", "Type", "Montant (€)", "Quantité", "Note"]
    typer.echo(tabulate(table, headers=headers, tablefmt="fancy_grid"))


@app.command()
def list_valuations(product_name: str = None) -> None:
    """
    List valuations in a formatted table.

    Displays a table with valuation date, product ID, total value,
    and unit price. Can be filtered by product name.

    Parameters
    ----------
    product_name : str, optional
        Filter valuations by product name. If None, shows all valuations.

    Examples
    --------
    Show all valuations:

    $ finance-tracker list-valuations

    Show valuations for Bitcoin:

    $ finance-tracker list-valuations --product-name "Bitcoin"
    """
    session = get_session()
    repo = SQLModelValuationRepository(session)
    valuations = repo.get_all()

    # Apply product filter if specified

    if product_name:
        product_repo = SQLModelProductRepository(session)
        product = product_repo.get_by_name(product_name)

        if product:
            valuations = repo.get_by_product_id(product.id or 0)
        else:
            typer.echo(f"Aucun produit trouvé avec le nom : {product_name}")

            return

    # Prepare data for the table
    table_data = [
        [v.date.date(), v.product_id, f"{v.total_value_eur}€", f"{v.unit_price_eur}€/u"]

        for v in valuations
        ]

    # Display the table
    headers = ["Date", "ID Produit", "Valeur Totale", "Prix Unitaire"]
    typer.echo(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSACTION COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@app.command()
def add_transaction(product_name: str = typer.Option(..., help="Nom du produit"),
                    transaction_type: str = typer.Option(..., help="Type: DEPOSIT, WITHDRAW, FEE, DISTRIBUTION, BUY, SELL, INTEREST"),
                    amount: str | None = typer.Option(None, help="Montant EUR"),
                    quantity: str | None = typer.Option(None, help="Quantité (parts/sats)"),
                    date: str = typer.Option(None, help="Date au format YYYY-MM-DD"),
                    note: str = typer.Option("", help="Note")) -> None:
    """
    Add a new transaction to the database.

    Creates a transaction record for the specified product with the
    given type, amount, quantity, date, and optional note.

    Parameters
    ----------
    product_name : str
        Name of the product (required). Must exist in the database.
    transaction_type : str
        Type of transaction. Valid values: DEPOSIT, WITHDRAW, FEE,
        DISTRIBUTION, BUY, SELL, INTEREST.
    amount : str, optional
        Amount in EUR as a decimal string (e.g., "2500.00").
    quantity : str, optional
        Quantity as a decimal string (e.g., "10" for 10 SCPI parts,
        or "1000000" for 1M satoshis).
    date : str, optional
        Transaction date in YYYY-MM-DD format. Defaults to current UTC time.
    note : str, optional
        Optional note or description for the transaction.

    Raises
    ------
    typer.Exit
        If the product is not found or the date format is invalid.

    Examples
    --------
    Add a buy transaction for SCPI:

    $ finance-tracker add-transaction \\
        --product-name "SCPI" \\
        --transaction-type "BUY" \\
        --amount "2500" \\
        --quantity "10" \\
        --date "2024-01-15" \\
        --note "Achat initial"

    Add a deposit:

    $ finance-tracker add-transaction \\
        --product-name "Cash" \\
        --transaction-type "DEPOSIT" \\
        --amount "10000"
    """
    # Convert string inputs to appropriate types
    amount = to_decimal(amount) if amount else None
    quantity = to_decimal(quantity) if quantity else None

    session = get_session()
    product_repo = SQLModelProductRepository(session)
    product = product_repo.get_by_name(product_name)

    if not product:
        typer.echo(f"❌ Produit '{product_name}' non trouvé", err=True)
        raise typer.Exit(1)

    # Parse date or use current time

    if date:
        try:
            date_obj = datetime.fromisoformat(date)
        except ValueError:
            typer.echo("❌ Date invalide (format: YYYY-MM-DD)", err=True)
            raise typer.Exit(1)
    else:
        date_obj = datetime.utcnow()

    # Create and persist the transaction
    tx = Transaction(
        product_id=product.id or 0,
        date=date_obj,
        type=TransactionType[transaction_type],
        amount_eur=amount,
        quantity=quantity,
        note=note,
        )

    tx_repo = SQLModelTransactionRepository(session)
    tx_repo.create(tx)

    typer.echo(f"✅ Transaction ajoutée: {product_name} {transaction_type}")


# ═══════════════════════════════════════════════════════════════════════════════
# VALUATION COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@app.command()
def add_valuation(product_name: str = typer.Option(..., help="Nom du produit"),
                  total_value_eur: str = typer.Option(..., help="Valeur totale en EUR"),
                  unit_price_eur: str | None = typer.Option(None, help="Prix unitaire (SCPI/BTC)"),
                  date: str = typer.Option(None, help="Date au format YYYY-MM-DD")) -> None:
    """
    Add a new valuation snapshot to the database.

    Creates a valuation record capturing the total value and optionally
    the unit price of a product at a specific point in time.

    Parameters
    ----------
    product_name : str
        Name of the product (required). Must exist in the database.
    total_value_eur : str
        Total value of the position in EUR as a decimal string.
    unit_price_eur : str, optional
        Unit price in EUR (e.g., price per SCPI share or full BTC price).
    date : str, optional
        Valuation date in YYYY-MM-DD format. Defaults to current UTC time.

    Raises
    ------
    typer.Exit
        If the product is not found or the date format is invalid.

    Examples
    --------
    Add a valuation for SCPI:

    $ finance-tracker add-valuation \\
        --product-name "SCPI" \\
        --total-value-eur "10500" \\
        --unit-price-eur "262.50" \\
        --date "2024-02-28"

    Add a valuation for Cash (no unit price needed):

    $ finance-tracker add-valuation \\
        --product-name "Cash" \\
        --total-value-eur "5000"
    """
    # Convert string inputs to appropriate types
    total_value_eur = to_decimal(total_value_eur) if total_value_eur else None
    unit_price_eur = to_decimal(unit_price_eur) if unit_price_eur else None

    session = get_session()
    product_repo = SQLModelProductRepository(session)
    product = product_repo.get_by_name(product_name)

    if not product:
        typer.echo(f"❌ Produit '{product_name}' non trouvé", err=True)
        raise typer.Exit(1)

    # Parse date or use current time

    if date:
        try:
            date_obj = datetime.fromisoformat(date)
        except ValueError:
            typer.echo("❌ Date invalide (format: YYYY-MM-DD)", err=True)
            raise typer.Exit(1)
    else:
        date_obj = datetime.utcnow()

    # Create and persist the valuation
    val = Valuation(
        product_id=product.id or 0,
        date=date_obj,
        total_value_eur=total_value_eur,
        unit_price_eur=unit_price_eur,
        )

    val_repo = SQLModelValuationRepository(session)
    val_repo.create(val)

    typer.echo(f"✅ Valorisation ajoutée: {product_name} = {total_value_eur}€")


# ═══════════════════════════════════════════════════════════════════════════════
# BITCOIN COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@app.command()
def update_btc(create_valuation: bool = typer.Option(True, help="Créer valorisation pour BTC")) -> None:
    """
    Fetch current BTC/EUR price and optionally create a valuation.

    This command retrieves the current Bitcoin price in EUR from the
    configured price service (CoinGecko by default) and optionally
    creates a valuation record based on the current BTC holdings.

    Parameters
    ----------
    create_valuation : bool
        If True (default), creates a valuation record for the Bitcoin
        product with the fetched price and calculated total value.

    Raises
    ------
    typer.Exit
        If the Bitcoin product is not found or if the price service fails.

    Notes
    -----
    The valuation is calculated by:
    1. Summing all BUY quantities minus SELL quantities to get total satoshis
    2. Converting satoshis to BTC (dividing by 100,000,000)
    3. Multiplying by the current BTC/EUR price

    If no Bitcoin holdings exist (total_sats <= 0), no valuation is created.

    Examples
    --------
    Fetch BTC price and create valuation:

    $ finance-tracker update-btc
    ✅ Prix BTC/EUR: 47500€
    ✅ Valorisation BTC créée: 950.00€

    Fetch BTC price only (no valuation):

    $ finance-tracker update-btc --no-create-valuation
    ✅ Prix BTC/EUR: 47500€
    """
    session = get_session()
    product_repo = SQLModelProductRepository(session)
    btc_product = product_repo.get_by_name("Bitcoin")

    if not btc_product:
        typer.echo("❌ Produit Bitcoin non trouvé", err=True)
        raise typer.Exit(1)

    service = BTCPriceService()
    try:
        price_eur = service.get_btc_price_eur()
        typer.echo(f"✅ Prix BTC/EUR: {price_eur}€")

        if create_valuation:
            # Calculate total satoshis from all transactions
            tx_repo = SQLModelTransactionRepository(session)
            transactions = tx_repo.get_by_product_id(btc_product.id or 0)
            total_sats = Decimal(0)

            for tx in transactions:
                if tx.type == TransactionType.BUY and tx.quantity:
                    total_sats += tx.quantity
                elif tx.type == TransactionType.SELL and tx.quantity:
                    total_sats -= tx.quantity

            if total_sats > 0:
                # Convert satoshis to BTC and calculate total value
                total_value = (total_sats / Decimal("100000000")) * price_eur
                val = Valuation(
                    product_id=btc_product.id or 0,
                    date=datetime.utcnow(),
                    total_value_eur=total_value,
                    unit_price_eur=price_eur,
                    )
                val_repo = SQLModelValuationRepository(session)
                val_repo.create(val)
                typer.echo(f"✅ Valorisation BTC créée: {total_value:.2f}€")
            else:
                typer.echo("⚠️  Aucune quantité BTC enregistrée")

    except BTCPriceServiceError as e:
        typer.echo(f"❌ Erreur: {e}", err=True)
        raise typer.Exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@app.command()
def dashboard(json_output: bool = typer.Option(False, "--json", help="Sortie JSON")) -> None:
    """
    Display the portfolio dashboard.

    Shows a summary of the portfolio including total value, net
    investment, performance, and breakdown by product.

    Parameters
    ----------
    json_output : bool
        If True, outputs the dashboard data as JSON instead of a
        formatted table. Useful for scripting and automation.

    Examples
    --------
    Display formatted dashboard:

    $ finance-tracker dashboard
    ╭─────────────────────────────────────────────────────╮
    │           FINANCE TRACKER - PORTFOLIO               │
    ├─────────────────────────────────────────────────────┤
    │ Total Value:          45,000.00 €                   │
    │ Net Investment:       39,600.00 €                   │
    │ Performance:          +5,400.00 € (+13.6%)          │
    ╰─────────────────────────────────────────────────────╯

    Output as JSON:

    $ finance-tracker dashboard --json
    {"total_value": 45000.00, "net_investment": 39600.00, ...}
    """
    session = get_session()
    service = DashboardService(session)
    portfolio = service.build_portfolio()

    if json_output:
        print(service.export_json(portfolio))
    else:
        print(service.display_dashboard(portfolio))


# ═══════════════════════════════════════════════════════════════════════════════
# PROJECTION COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@app.command()
def project(initial_amount: str = typer.Option(10000, help="Montant initial EUR"),
            monthly_contribution: str = typer.Option(500, help="Versement mensuel EUR"),
            annual_return: str = typer.Option(0.04, help="Rendement annuel (ex: 0.04 pour 4%)"),
            years: int = typer.Option(10, help="Durée en années"),
            frequency: str = typer.Option("MONTHLY", help="Fréquence: MONTHLY, QUARTERLY, ANNUAL")) -> None:
    """
    Calculate compound interest projection.

    Projects the growth of an investment over time using compound
    interest with optional regular contributions.

    Parameters
    ----------
    initial_amount : str
        Initial investment amount in EUR (default: 10000).
    monthly_contribution : str
        Monthly contribution amount in EUR (default: 500).
    annual_return : str
        Expected annual return as decimal (default: 0.04 for 4%).
    years : int
        Investment duration in years (default: 10).
    frequency : str
        Compounding frequency. Valid values: MONTHLY, QUARTERLY, ANNUAL
        (default: MONTHLY).

    Raises
    ------
    typer.Exit
        If the frequency value is invalid.

    Examples
    --------
    Project with default parameters (10 years, 4% return):

    $ finance-tracker project

    Custom projection with 8% return over 20 years:

    $ finance-tracker project \\
        --initial-amount 50000 \\
        --monthly-contribution 1000 \\
        --annual-return 0.08 \\
        --years 20

    Quarterly compounding:

    $ finance-tracker project --frequency QUARTERLY
    """
    # Convert string inputs to Decimal
    initial_amount = to_decimal(initial_amount) if initial_amount else None
    monthly_contribution = to_decimal(monthly_contribution) if monthly_contribution else None
    annual_return = to_decimal(annual_return) if annual_return else None

    # Validate frequency
    try:
        freq = ProjectionFrequency[frequency]
    except KeyError:
        typer.echo(f"❌ Fréquence invalide: {frequency}", err=True)
        raise typer.Exit(1)

    # Create projection and calculate
    projection = ProjectionResult(
        initial_amount=initial_amount,
        monthly_contribution=monthly_contribution,
        annual_return=annual_return,
        years=years,
        frequency=freq,
        )
    projection.calculate()

    print(projection.display_table())


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENTATION COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@app.command()
def product_doc() -> None:
    """
    Generate markdown documentation for products.

    Creates a markdown file documenting all products in the database,
    including their types, descriptions, risk levels, fees, and tax
    information.

    The documentation is saved to DOCS_DIR/products.md.

    Examples
    --------
    $ finance-tracker product-doc
    ✅ Documentation générée: /path/to/docs/products.md
    """
    session = get_session()
    service = DocService(session)
    doc_content = service.generate_products_doc()

    doc_path = DOCS_DIR / "products.md"
    doc_path.write_text(doc_content, encoding="utf-8")

    typer.echo(f"✅ Documentation générée: {doc_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@app.command()
def export_pdf() -> None:
    """
    Generate a PDF portfolio report.

    Creates a comprehensive PDF report of the current portfolio,
    including product valuations, performance metrics, and
    transaction history.

    The report is saved with a timestamped filename.

    Examples
    --------
    $ finance-tracker export-pdf
    ✅ PDF généré: /path/to/reports/portfolio_20240228_143052.pdf
    """
    session = get_session()
    dashboard_service = DashboardService(session)
    portfolio = dashboard_service.build_portfolio()

    pdf_service = PDFReportService()
    filepath = pdf_service.generate_report(portfolio)

    typer.echo(f"✅ PDF généré: {filepath}")


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app()
