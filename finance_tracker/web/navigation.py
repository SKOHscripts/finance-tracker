"""
Module: navigation.py
Navigation centralisée de l'application.
"""

from sqlmodel import Session
from typing import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Page:
    label: str
    render: Callable[[Session], None]


def build_pages() -> list[Page]:
    # Lazy imports
    from finance_tracker.web.views.dashboard import render as dashboard_render
    from finance_tracker.web.views.simulation import render as simulation_render
    from finance_tracker.web.views.bitcoin import render as bitcoin_render
    from finance_tracker.web.views.products import render as products_render
    from finance_tracker.web.views.transactions import render as transactions_render
    from finance_tracker.web.views.valuations import render as valuations_render
    from finance_tracker.web.views.documentation import render as documentation_render

    return [
        # --- Documentation ---
        Page("📖 Documentation", documentation_render),

        # --- Analyses ---
        Page("📊 Tableau de Bord", dashboard_render),
        Page("🔮 Simulation Long Terme", simulation_render),

        # --- Gestion des Données ---
        Page("🏷️ Mes Produits", products_render),
        Page("💸 Mes Transactions", transactions_render),
        Page("📈 Mes Valorisations", valuations_render),

        # --- Outils Spécifiques ---
        Page("₿ Espace Bitcoin", bitcoin_render),
    ]
