"""
Module: navigation.py

This module defines the structure and configuration for the web application's navigation system.
It provides a way to declare and organize different pages of the application, each associated
with a label and a rendering function. The rendering functions are responsible for displaying
the content of each page when navigated to.

The module uses lazy imports to avoid loading heavy dependencies at startup, improving the
application's initial load time. It centralizes the page definitions, making it easier to manage
and extend the navigation structure of the web interface.

Key Components:
- Page: A dataclass representing a navigable page with a label and a render function.
- build_pages: A function that constructs and returns a list of Page objects, each corresponding
  to a specific view in the web application.
"""

from sqlmodel import Session
from typing import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Page:
    """
    Représente une page unique et navigable dans l'application web.

    Cette classe encapsule les informations nécessaires pour afficher une page,
    notamment son étiquette et sa fonction de rendu.

    Parameters
    ----------
    label : str
        Le libellé de la page, utilisé pour l'affichage dans l'interface.
    render : Callable[[Session], None]
        La fonction appelée pour afficher le contenu de la page. Prend une
        instance de Session en argument et ne retourne rien.
    """
    label: str
    render: Callable[[Session], None]


def build_pages():
    # Lazy imports avoid loading heavy modules at startup
    from finance_tracker.web.views.dashboard import render as dashboard_render
    from finance_tracker.web.views.simulation import render as simulation_render
    from finance_tracker.web.views.transactions import render_add as tx_add_render
    from finance_tracker.web.views.valuations import render_add as val_add_render
    from finance_tracker.web.views.products import render_add as prod_add_render
    from finance_tracker.web.views.bitcoin import render as bitcoin_render
    from finance_tracker.web.views.transactions import render_list as tx_list_render
    from finance_tracker.web.views.valuations import render_list as val_list_render
    from finance_tracker.web.views.products import render_edit as edit_data_render
    from finance_tracker.web.views.report_pdf import render as pdf_render

    # Each Page maps a UI label to its render function

    return [
        Page("📊 Dashboard", dashboard_render),
        Page("🧮 Simulation long terme", simulation_render),
        Page("➕ Ajouter Transaction", tx_add_render),
        Page("➕ Ajouter Valorisation", val_add_render),
        Page("➕ Ajouter Produits", prod_add_render),
        Page("₿ Bitcoin", bitcoin_render),
        Page("📋 Liste Transactions", tx_list_render),
        Page("📋 Liste Valorisations", val_list_render),
        Page("✏️ Éditer Données", edit_data_render),
        Page("📄 Rapport PDF", pdf_render),
        ]
