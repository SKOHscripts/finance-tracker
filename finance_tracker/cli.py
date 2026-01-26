"""CLI Typer - interface utilisateur."""
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
from finance_tracker.utils.money import to_decimal

app = typer.Typer(help="Finance Tracker - Suivi portefeuille d'investissement")


def get_session() -> Session:
    """
    Crée et retourne une nouvelle session de base de données.

    Cette fonction initialise une connexion à la base de données en utilisant
    l'URL définie dans DATABASE_URL, puis retourne une session SQLAlchemy
    associée à cette connexion.

    Returns
    -------
    Session
        Une instance de session SQLAlchemy connectée à la base de données.
    """
    engine = create_engine(DATABASE_URL, echo=False)

    return Session(engine)


# ==================== Commandes DB ====================


@app.command()
def init_db_cmd() -> None:
    """
    Initialise la base de données.

    Cette fonction configure la base de données en créant les tables nécessaires
    et en appliquant les migrations si elles ne sont pas déjà présentes.

    Raises
    ------
    Exception
        Si une erreur survient lors de l'initialisation de la base de données.
    """
    init_db()
    typer.echo("✅ Base de données initialisée")


@app.command()
def seed_products() -> None:
    """Crée les produits par défaut."""
    session = get_session()

    products = [
        Product(
            name="Cash",
            type=ProductType.CASH,
            quantity_unit=QuantityUnit.NONE,
            description="Comptes de trésorerie liquide",
            risk_level="Très faible",
            fees_description="Aucun",
            tax_info="Intérêts imposables au barème",
            ),
        Product(
            name="Épargne",
            type=ProductType.SAVINGS,
            quantity_unit=QuantityUnit.NONE,
            description="Livrets d'épargne réglementés",
            risk_level="Très faible",
            fees_description="Aucun",
            tax_info="Exonéré d'impôt (livrets A, LDDS, CEL)",
            ),
        Product(
            name="SCPI",
            type=ProductType.SCPI,
            quantity_unit=QuantityUnit.SCPI_SHARES,
            description="Sociétés Civiles de Placement Immobilier - Parts",
            risk_level="Modéré",
            fees_description="Frais de gestion 8-10% annuels, entrée 5-7%",
            tax_info="Distributions imposables, abattement de 40% possible en IR",
            ),
        Product(
            name="Bitcoin",
            type=ProductType.BITCOIN,
            quantity_unit=QuantityUnit.BTC_SATS,
            description="Actif cryptographique",
            risk_level="Élevé",
            fees_description="Frais d'exchange 0.1-2%",
            tax_info="Gains en capital à déclarer, régime micro-BIC ou réel",
            ),
        Product(
            name="Assurance Vie",
            type=ProductType.INSURANCE,
            quantity_unit=QuantityUnit.NONE,
            description="Contrats d'assurance-vie euros et/ou unités de compte",
            risk_level="Faible à Modéré",
            fees_description="Frais de gestion 0.5-2% annuels",
            tax_info="Exonération après 8 ans (impôt sur les gains)",
            ),
        Product(
            name="PER",
            type=ProductType.PER,
            quantity_unit=QuantityUnit.NONE,
            description="Plan d'Épargne Retraite",
            risk_level="Faible à Modéré",
            fees_description="Frais de gestion 0.5-1.5%",
            tax_info="Réduction d'impôt sur cotisations, imposition retraite",
            ),
        Product(
            name="FCPI",
            type=ProductType.FCPI,
            quantity_unit=QuantityUnit.NONE,
            description="Fonds Commun de Placement dans l'Innovation",
            risk_level="Élevé",
            fees_description="Frais de gestion 2-3%",
            tax_info="Réduction d'impôt 18%, imposition gains",
            ),
        ]

    # Ajouter taux initial épargne

    for product in products:
        existing = SQLModelProductRepository(session).get_by_name(product.name)

        if not existing:
            session.add(product)

    session.commit()

    # Ajouter taux initial épargne
    savings_product = SQLModelProductRepository(session).get_by_name("Épargne")

    if savings_product:
        rate_repo = SQLModelRateScheduleRepository(session)
        existing_rates = rate_repo.get_by_product_id(savings_product.id or 0)

        if not existing_rates:
            rate = RateSchedule(
                product_id=savings_product.id or 0,
                date_effective=datetime.utcnow(),
                annual_rate=to_decimal("0.03"),  # 3% par défaut
                )
            session.add(rate)
            session.commit()

    typer.echo("✅ Produits par défaut créés")


@app.command()
def list_products() -> None:
    """Liste tous les produits dans un tableau."""
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
    """Liste les transactions dans un tableau."""
    session = get_session()
    repo = SQLModelTransactionRepository(session)
    transactions = repo.get_all()

    if product_name:
        product_repo = SQLModelProductRepository(session)
        product = product_repo.get_by_name(product_name)

        if product:
            transactions = repo.get_by_product_id(product.id or 0)

    # Limite les transactions à afficher
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
    """Liste les valorisations dans un tableau propre."""
    session = get_session()
    repo = SQLModelValuationRepository(session)
    valuations = repo.get_all()

    if product_name:
        product_repo = SQLModelProductRepository(session)
        product = product_repo.get_by_name(product_name)

        if product:
            valuations = repo.get_by_product_id(product.id or 0)
        else:
            typer.echo(f"Aucun produit trouvé avec le nom : {product_name}")

            return

    # Préparer les données pour le tableau
    table_data = [
        [v.date.date(), v.product_id, f"{v.total_value_eur}€", f"{v.unit_price_eur}€/u"]

        for v in valuations
    ]

    # Afficher le tableau
    headers = ["Date", "ID Produit", "Valeur Totale", "Prix Unitaire"]
    typer.echo(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))

# ==================== Transactions ====================


@app.command()
def add_transaction(
        product_name: str = typer.Option(..., help="Nom du produit"),
        transaction_type: str = typer.Option(..., help="Type: DEPOSIT, WITHDRAW, FEE, DISTRIBUTION, BUY, SELL, INTEREST"),
        amount: str | None = typer.Option(None, help="Montant EUR"),
        quantity: str | None = typer.Option(None, help="Quantité (parts/sats)"),
        date: str = typer.Option(None, help="Date au format YYYY-MM-DD"),
        note: str = typer.Option("", help="Note"),
        ) -> None:
    """Ajoute une transaction."""
    # Conversion
    amount = to_decimal(amount) if amount else None
    quantity = to_decimal(quantity) if quantity else None

    session = get_session()
    product_repo = SQLModelProductRepository(session)

    product = product_repo.get_by_name(product_name)

    if not product:
        typer.echo(f"❌ Produit '{product_name}' non trouvé", err=True)
        raise typer.Exit(1)

    # Parsers date

    if date:
        try:
            date_obj = datetime.fromisoformat(date)
        except ValueError:
            typer.echo("❌ Date invalide (format: YYYY-MM-DD)", err=True)
            raise typer.Exit(1)
    else:
        date_obj = datetime.utcnow()

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


# ==================== Valorisations ====================


@app.command()
def add_valuation(
        product_name: str = typer.Option(..., help="Nom du produit"),
        total_value_eur: str = typer.Option(..., help="Valeur totale en EUR"),
        unit_price_eur: str | None = typer.Option(None, help="Prix unitaire (SCPI/BTC)"),
        date: str = typer.Option(None, help="Date au format YYYY-MM-DD"),
        ) -> None:
    """Ajoute une valorisation."""
    # Conversion
    total_value_eur = to_decimal(total_value_eur) if total_value_eur else None
    unit_price_eur = to_decimal(unit_price_eur) if unit_price_eur else None

    session = get_session()
    product_repo = SQLModelProductRepository(session)

    product = product_repo.get_by_name(product_name)

    if not product:
        typer.echo(f"❌ Produit '{product_name}' non trouvé", err=True)
        raise typer.Exit(1)

    if date:
        try:
            date_obj = datetime.fromisoformat(date)
        except ValueError:
            typer.echo("❌ Date invalide (format: YYYY-MM-DD)", err=True)
            raise typer.Exit(1)
    else:
        date_obj = datetime.utcnow()

    val = Valuation(
        product_id=product.id or 0,
        date=date_obj,
        total_value_eur=total_value_eur,
        unit_price_eur=unit_price_eur,
        )

    val_repo = SQLModelValuationRepository(session)
    val_repo.create(val)

    typer.echo(f"✅ Valorisation ajoutée: {product_name} = {total_value_eur}€")


# ==================== Bitcoin ====================


@app.command()
def update_btc(
        create_valuation: bool = typer.Option(True, help="Créer valorisation pour BTC"),
        ) -> None:
    """Récupère le prix BTC/EUR et crée valorisation."""
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
            # Récupérer dernière quantité BTC
            tx_repo = SQLModelTransactionRepository(session)
            transactions = tx_repo.get_by_product_id(btc_product.id or 0)

            total_sats = Decimal(0)

            for tx in transactions:
                if tx.type == TransactionType.BUY and tx.quantity:
                    total_sats += tx.quantity
                elif tx.type == TransactionType.SELL and tx.quantity:
                    total_sats -= tx.quantity

            if total_sats > 0:
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


# ==================== Dashboard ====================


@app.command()
def dashboard(
        json_output: bool = typer.Option(False, "--json", help="Sortie JSON"),
        ) -> None:
    """Affiche le dashboard portefeuille."""
    session = get_session()
    service = DashboardService(session)
    portfolio = service.build_portfolio()

    if json_output:
        print(service.export_json(portfolio))
    else:
        print(service.display_dashboard(portfolio))


# ==================== Projection ====================


@app.command()
def project(
        initial_amount: str = typer.Option(10000, help="Montant initial EUR"),
        monthly_contribution: str = typer.Option(500, help="Versement mensuel EUR"),
        annual_return: str = typer.Option(0.04, help="Rendement annuel (ex: 0.04 pour 4%)"),
        years: int = typer.Option(10, help="Durée en années"),
        frequency: str = typer.Option("MONTHLY", help="Fréquence: MONTHLY, QUARTERLY, ANNUAL"),
        ) -> None:
    """Projette rendement composé."""
    # Conversion
    initial_amount = to_decimal(initial_amount) if initial_amount else None
    monthly_contribution = to_decimal(monthly_contribution) if monthly_contribution else None
    annual_return = to_decimal(annual_return) if annual_return else None

    try:
        freq = ProjectionFrequency[frequency]
    except KeyError:
        typer.echo(f"❌ Fréquence invalide: {frequency}", err=True)
        raise typer.Exit(1)

    projection = ProjectionResult(
        initial_amount=initial_amount,
        monthly_contribution=monthly_contribution,
        annual_return=annual_return,
        years=years,
        frequency=freq,
        )
    projection.calculate()

    print(projection.display_table())


# ==================== Documentation ====================


@app.command()
def product_doc() -> None:
    """Génère la documentation markdown des produits."""
    session = get_session()
    service = DocService(session)
    doc_content = service.generate_products_doc()

    doc_path = DOCS_DIR / "products.md"
    doc_path.write_text(doc_content, encoding="utf-8")

    typer.echo(f"✅ Documentation générée: {doc_path}")


# ==================== Export ====================


@app.command()
def export_pdf() -> None:
    """Génère un PDF rapport."""
    session = get_session()
    dashboard_service = DashboardService(session)
    portfolio = dashboard_service.build_portfolio()

    pdf_service = PDFReportService()
    filepath = pdf_service.generate_report(portfolio)

    typer.echo(f"✅ PDF généré: {filepath}")


if __name__ == "__main__":
    app()
