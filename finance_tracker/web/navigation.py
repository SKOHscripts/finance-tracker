"""
Module: navigation.py

Navigation centralisée de l'application.
Les imports sont volontairement "lazy" pour éviter de charger des modules lourds au démarrage.
"""

from sqlmodel import Session
from typing import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Page:
    label: str
    render: Callable[[Session], None]


def build_pages() -> list[Page]:
    # Lazy imports avoid loading heavy modules at startup
    from finance_tracker.web.views.dashboard import render as dashboard_render
    from finance_tracker.web.views.simulation import render as simulation_render
    from finance_tracker.web.views.bitcoin import render as bitcoin_render

    # Nouvelles vues "tout-en-un" (liste + ajout + édition + suppression)
    from finance_tracker.web.views.products import render as products_render
    from finance_tracker.web.views.transactions import render as transactions_render
    from finance_tracker.web.views.valuations import render as valuations_render

    return [
        Page("📊 Dashboard", dashboard_render),
        Page("🧮 Simulation long terme", simulation_render),
        Page("🧾 Produits", products_render),
        Page("💸 Transactions", transactions_render),
        Page("📈 Valorisations", valuations_render),
        Page("₿ Bitcoin", bitcoin_render),
    ]
