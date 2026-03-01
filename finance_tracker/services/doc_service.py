"""Product documentation service."""
from sqlmodel import Session

from finance_tracker.repositories.sqlmodel_repo import SQLModelProductRepository


class DocService:
    """Service for generating documentation.

    Provides functionality to create documentation in various formats
    for different entities within the system.
    """

    def __init__(self, session: Session):
        self.session = session
        self.product_repo = SQLModelProductRepository(session)

    def generate_products_doc(self) -> str:
        """Generate markdown documentation for investment products.

        Queries all products from the repository and formats them as
        markdown with detailed information including type, description,
        risk level, fees, and tax information.

        Returns
        -------
        str
            Markdown formatted documentation string containing all products.
        """
        products = self.product_repo.get_all()

        lines = []
        # Header section with title and generation timestamp note
        lines.append("# Documentation des Produits d'Investissement")
        lines.append("")
        lines.append("*Généré automatiquement. Mise à jour: Documentez vos produits via l'UI.*")
        lines.append("")

        # Early return when no products exist to avoid empty section headers

        if not products:
            lines.append("Aucun produit configuré.")

            return "\n".join(lines)

        for product in products:
            lines.append(f"## {product.name}")
            lines.append("")

            lines.append(f"**Type:** {product.type.value}")
            lines.append("")

            # Optional sections only included when data exists

            if product.description:
                lines.append("### Description")
                lines.append(product.description)
                lines.append("")

            if product.risk_level:
                lines.append(f"**Niveau de risque:** {product.risk_level}")
                lines.append("")

            if product.fees_description:
                lines.append("### Frais")
                lines.append(product.fees_description)
                lines.append("")

            if product.tax_info:
                lines.append("### Fiscalité")
                lines.append(product.tax_info)
                lines.append("")

            # Visual separator between products for readability
            lines.append("---")
            lines.append("")

        return "\n".join(lines)
