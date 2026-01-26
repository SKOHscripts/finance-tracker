"""Service de documentation produits."""
from sqlmodel import Session

from finance_tracker.repositories.sqlmodel_repo import SQLModelProductRepository


class DocService:
    """Service de génération de documentation."""

    def __init__(self, session: Session):
        self.session = session
        self.product_repo = SQLModelProductRepository(session)

    def generate_products_doc(self) -> str:
        """Génère la documentation markdown des produits.

        Returns:
            Markdown string
        """
        products = self.product_repo.get_all()

        lines = []
        lines.append("# Documentation des Produits d'Investissement")
        lines.append("")
        lines.append("*Généré automatiquement. Mise à jour: Documentez vos produits via l'UI.*")
        lines.append("")

        if not products:
            lines.append("Aucun produit configuré.")
            return "\n".join(lines)

        for product in products:
            lines.append(f"## {product.name}")
            lines.append("")

            lines.append(f"**Type:** {product.type.value}")
            lines.append("")

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

            lines.append("---")
            lines.append("")

        return "\n".join(lines)
