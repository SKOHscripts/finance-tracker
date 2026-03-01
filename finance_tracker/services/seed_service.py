"""
seed_service.py — Service for seeding default data.

This module provides functions to populate the database with default
products and initial configuration when setting up a new portfolio.
"""

from datetime import datetime

from sqlmodel import Session

from finance_tracker.domain.enums import ProductType, QuantityUnit
from finance_tracker.domain.models import Product, RateSchedule
from finance_tracker.repositories.sqlmodel_repo import (
    SQLModelProductRepository,
    SQLModelRateScheduleRepository,
    )
from finance_tracker.utils.money import to_decimal


def seed_default_products(session: Session) -> int:
    """
    Seed the database with default financial products.

    Creates a set of predefined financial products commonly used in French
    portfolios. Products are only created if they don't already exist,
    making this function idempotent.

    Default Products Created
    ------------------------
    - Cash: Liquid treasury accounts (risk: very low)
    - Épargne: Regulated savings accounts - Livret A, LDDS, CEL (risk: very low)
    - SCPI: Real estate investment trusts - parts (risk: moderate)
    - Bitcoin: Cryptographic asset (risk: high)
    - Assurance Vie: Life insurance contracts (risk: low to moderate)
    - PER: Retirement savings plans (risk: low to moderate)
    - FCPI: Innovation investment funds (risk: high)

    A default 2% annual interest rate is also created for the "Épargne" product.

    Parameters
    ----------
    session : Session
        SQLModel database session for repository operations.

    Returns
    -------
    int
        Number of new products created.

    Examples
    --------
    >>> from sqlmodel import Session
    >>> session = Session(engine)
    >>> count = seed_default_products(session)
    >>> print(f"Created {count} products")
    Created 7 products
    """
    product_repo = SQLModelProductRepository(session)
    rate_repo = SQLModelRateScheduleRepository(session)

    # Define default product templates
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

    # Add products that don't already exist
    created_count = 0

    for product in products:
        existing = product_repo.get_by_name(product.name)

        if not existing:
            session.add(product)
            created_count += 1

    session.commit()

    # Add initial interest rate for savings product
    savings_product = product_repo.get_by_name("Épargne")

    if savings_product:
        existing_rates = rate_repo.get_by_product_id(savings_product.id or 0)

        if not existing_rates:
            rate = RateSchedule(
                product_id=savings_product.id or 0,
                date_effective=datetime.utcnow(),
                annual_rate=to_decimal("0.02"),  # 2% default rate
                )
            session.add(rate)
            session.commit()

    return created_count
