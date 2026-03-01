"""
Module: navigation.py
Centralized navigation for the application.
"""

from sqlmodel import Session
from typing import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Page:
    """Represents a navigation item that can be rendered with a database session."""
    label: str
    render: Callable[[Session], None]


def build_pages() -> list[Page]:
    # Lazy imports avoid circular dependencies since views may import navigation
    from finance_tracker.web.views.dashboard import render as dashboard_render
    from finance_tracker.web.views.simulation import render as simulation_render
    from finance_tracker.web.views.bitcoin import render as bitcoin_render
    from finance_tracker.web.views.products import render as products_render
    from finance_tracker.web.views.transactions import render as transactions_render
    from finance_tracker.web.views.valuations import render as valuations_render
    from finance_tracker.web.views.documentation import render as documentation_render

    return [
        # Documentation section
        Page("📖 Documentation", documentation_render),

        # Analysis tools
        Page("📊 Tableau de Bord", dashboard_render),
        Page("🔮 Simulation Long Terme", simulation_render),

        # Data management
        Page("🏷️ Mes Produits", products_render),
        Page("💸 Mes Transactions", transactions_render),
        Page("📈 Mes Valorisations", valuations_render),

        # Specialized tools
        Page("₿ Espace Bitcoin", bitcoin_render),
        ]
