"""
Documentation page for Finance Tracker Streamlit application.

This module renders a comprehensive documentation hub with tabs for
different documentation sections, optimized for Streamlit display.
All documentation links point to the GitHub repository markdown files.
"""

import streamlit as st
from sqlmodel import Session
from pathlib import Path

from finance_tracker.i18n import t


# GitHub repository base URL for markdown files
GITHUB_BASE_URL = "https://github.com/SKOHscripts/finance-tracker/blob/main"
DOCS_GITHUB_URL = f"{GITHUB_BASE_URL}/docs"


def _get_docs_path() -> Path:
    """Get the absolute path to the docs directory."""
    current_dir = Path(__file__).parent.parent.parent.parent
    return current_dir / "docs"


def _load_markdown_file(filename: str) -> str:
    """Load markdown content from a file in the docs directory."""
    try:
        docs_path = _get_docs_path()
        file_path = docs_path / filename

        if not file_path.exists():
            return t("documentation.file_not_found").format(filename=filename)

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return t("documentation.file_load_error").format(error=str(e))


def _render_section_card(title: str, description: str, icon: str, link_url: str) -> None:
    """Render a clickable section card with icon and description."""
    read_more = t("documentation.card_read_more")
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e3a5f 0%, #2d4a6f 100%);
                padding: 1.2rem;
                border-radius: 10px;
                margin-bottom: 1rem;
                border-left: 4px solid #4da6ff;">
        <h4 style="margin: 0; color: #ffffff;">{icon} {title}</h4>
        <p style="margin: 0.5rem 0 0 0; color: #b8c9d9; font-size: 0.9rem;">{description}</p>
        <a href="{link_url}" target="_blank" style="color: #4da6ff; font-size: 0.85rem;">{read_more}</a>
    </div>
    """, unsafe_allow_html=True)


def _render_tab_home() -> None:
    """Render the home/welcome tab with project overview."""

    st.markdown(f"## {t('documentation.home_title')}")
    st.markdown(t("documentation.home_intro"))

    # Badges
    st.markdown("""
    [![Version](https://img.shields.io/github/v/release/SKOHscripts/finance-tracker?display_name=tag)](https://github.com/SKOHscripts/finance-tracker/releases)
    [![License](https://img.shields.io/github/license/SKOHscripts/finance-tracker)](https://github.com/SKOHscripts/finance-tracker/blob/main/LICENSE)
    [![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
    """)

    st.divider()

    st.markdown(f"### {t('documentation.home_features_title')}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(t("documentation.home_feature_tracking"))

    with col2:
        st.markdown(t("documentation.home_feature_analysis"))

    with col3:
        st.markdown(t("documentation.home_feature_privacy"))

    st.divider()

    st.markdown(f"### {t('documentation.home_quickstart_title')}")
    st.markdown(t("documentation.home_quickstart_table"))

    st.divider()

    st.markdown(f"### {t('documentation.home_explore_title')}")
    st.markdown(t("documentation.home_explore_text"))
    st.info(t("documentation.home_tip"))


def _render_tab_concepts() -> None:
    """Render the fundamental concepts documentation tab."""

    st.markdown(f"## {t('documentation.concepts_title')}")
    st.markdown(t("documentation.concepts_intro"))

    st.divider()

    st.markdown(f"### {t('documentation.concepts_products_title')}")
    st.markdown("""
    Un **Produit** représente le contenant de votre investissement. C'est l'objet stable
    créé une seule fois qui ne change jamais.

    **Types supportés:**
    | Type | Unité | Exemple | Risque |
    |------|-------|---------|--------|
    | Cash | Aucun | Compte courant | Très faible |
    | SCPI | Parts | SCPI Eurizon | Modéré |
    | Bitcoin | Satoshis | BTC | Très élevé |
    | Livret | Aucun | Livret A | Très faible |
    | Assurance Vie | Parts | AV Multi-fonds | Variable |
    | PER | Aucun | PER Retraite | Variable |
    """)

    st.markdown(f"### {t('documentation.concepts_transactions_title')}")
    st.markdown("""
    Une **Transaction** enregistre un flux d'argent ou de quantité à un instant T.

    **6 types de transactions:**
    | Type | Direction | Description |
    |------|-----------|-------------|
    | DEPOSIT | → Entrée | Apport d'argent frais |
    | WITHDRAW | ← Sortie | Retrait d'argent |
    | BUY | ← Sortie | Achat d'un actif |
    | SELL | → Entrée | Vente d'un actif |
    | DISTRIBUTION | → Entrée | Dividende/Coupon reçu |
    | FEE | ← Sortie | Frais payés |
    """)

    st.markdown(f"### {t('documentation.concepts_valuations_title')}")
    st.markdown("""
    Une **Valorisation** capture la valeur unitaire d'un produit à un instant donné.
    C'est une "photographie" qui permet de calculer les gains/pertes latents.

    **Exemple:**
    ```
    Achat: 40 parts SCPI à 250€ = 10 000€ investi
    Valorisation: 262.5€ par part → Valeur totale: 10 500€
    Gain latent: +500€ (+5%)
    ```
    """)

    st.divider()

    st.markdown(t("documentation.full_doc_link").format(
        title="Concepts Fondamentaux",
        url=f"{DOCS_GITHUB_URL}/CONCEPTS_FONDAMENTAUX.md",
    ))

    with st.expander(t("documentation.expand_full_doc"), expanded=False):
        content = _load_markdown_file("CONCEPTS_FONDAMENTAUX.md")
        st.markdown(content)


def _render_tab_calculs() -> None:
    """Render the formulas and calculations documentation tab."""

    st.markdown(f"## {t('documentation.calculs_title')}")
    st.markdown(t("documentation.calculs_intro"))

    st.divider()

    st.markdown(f"### {t('documentation.calculs_key_metrics')}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Investissement Net**
        ```
        Inv. Net = Σ Entrées - Σ Sorties
                 = DEPOSIT + SELL + DISTRIBUTION
                   - WITHDRAW - BUY - FEE
        ```

        **Valeur Actuelle**
        ```
        Valeur = Σ (Quantité × Prix Unitaire)
        ```

        **Performance Absolue**
        ```
        Perf (€) = Valeur Actuelle - Investissement Net
        ```
        """)

    with col2:
        st.markdown("""
        **Performance Relative**
        ```
        Perf (%) = (Perf € / Inv. Net) × 100
        ```

        **PRU (Prix de Revient Unitaire)**
        ```
        PRU = Σ(Qtté × Prix) / Σ Qtté
        ```

        **Gain Latent**
        ```
        Gain = (Prix Actuel - PRU) × Quantité
        ```
        """)

    st.divider()

    st.markdown(f"### {t('documentation.calculs_compound')}")

    st.markdown("""
    **Formule classique:**
    $$VF = VP \\times (1 + r)^n$$

    **Avec versements mensuels:**
    $$VF = VP \\times (1 + r)^n + V \\times \\frac{(1 + r)^n - 1}{r} \\times (1 + r)$$

    Où:
    - **VF** = Valeur Future
    - **VP** = Valeur Présente (capital initial)
    - **r** = Rendement (mensuel ou annuel selon contexte)
    - **n** = Nombre de périodes
    - **V** = Versement périodique
    """)

    st.divider()

    st.markdown(f"### {t('documentation.calculs_bitcoin_title')}")

    st.markdown("""
    **Conversion sans double passage:**
    - 1 BTC = 100 000 000 satoshis
    - Prix toujours en **EUR/Satoshi** (pas de conversion BTC intermédiaire)

    ```
    Valeur = Satoshis × Prix(EUR/Sat)
           = 2 000 000 × 0.000475 = 950€
    ```
    """)

    st.divider()

    st.markdown(t("documentation.full_doc_link").format(
        title="Formules & Calculs",
        url=f"{DOCS_GITHUB_URL}/FORMULES_CALCULS.md",
    ))

    with st.expander(t("documentation.expand_full_doc"), expanded=False):
        content = _load_markdown_file("FORMULES_CALCULS.md")
        st.markdown(content)


def _render_tab_inflation() -> None:
    """Render the inflation profiles documentation tab."""

    st.markdown(f"## {t('documentation.inflation_title')}")
    st.markdown(t("documentation.inflation_intro"))

    st.divider()

    st.markdown(f"### {t('documentation.inflation_profiles_title')}")

    st.markdown("""
| Profil | Taux | Plage indicative | Cas d'usage |
|---|---|---|---|
| **Standard IPC** (défaut) | 2,0 %/an | 1,7–2,0 % | Neutraliser l'inflation officielle sur les dépenses courantes |
| **Urbain locataire** | 2,3 %/an | 2,2–2,5 % | Locataire en ville avec un loyer significatif |
| **Vie urbaine + projet immo** | 3,0 %/an | 2,7–3,2 % | Utilisateur visant l'accession à la propriété en ville |
| **Indexé m² de ville** | 4,0 %/an | 3,5–5,0 % | Suivi du patrimoine au prix du m² immobilier urbain |
| **Personnalisé** | libre | — | Saisir manuellement tout autre taux |
""")

    st.divider()

    st.markdown(f"### {t('documentation.inflation_how_title')}")
    st.markdown(t("documentation.inflation_how"))

    st.divider()

    st.markdown(t("documentation.inflation_sources"))

    st.divider()

    st.markdown(t("documentation.full_doc_link").format(
        title="Inflation Paramétrable",
        url=f"{GITHUB_BASE_URL}/README.md#-inflation-param%C3%A9trable",
    ))


def _render_tab_interface() -> None:
    """Render the web interface documentation tab."""

    st.markdown(f"## {t('documentation.interface_title')}")
    st.markdown(t("documentation.interface_intro"))

    st.divider()

    st.markdown(f"### {t('documentation.interface_architecture')}")

    pages_data = {
        "📊 Tableau de Bord": "Vue globale du portefeuille, répartition, graphiques temporels",
        "🔮 Simulation Long Terme": "Projections avec intérêts composés, scénarios multi-hypothèses",
        "🏷️ Mes Produits": "CRUD des produits financiers (création, édition, suppression)",
        "💸 Mes Transactions": "Historique et saisie des mouvements (DEPOSIT, BUY, SELL, etc.)",
        "📈 Mes Valorisations": "Mise à jour des prix unitaires par produit",
        "₿ Espace Bitcoin": "Prix temps réel (CoinGecko), historique, conversions",
        }

    for page, desc in pages_data.items():
        st.markdown(f"**{page}**")
        st.markdown(f"└─ {desc}")
        st.markdown("")

    st.divider()

    st.markdown(f"### {t('documentation.interface_workflow')}")

    st.markdown("""
    ```
    1. 🏷️ Mes Produits
       └─ Créer le produit (ex: SCPI Eurizon)

    2. 💸 Mes Transactions
       └─ DEPOSIT (versement initial)
       └─ BUY (achat de parts)

    3. 📈 Mes Valorisations
       └─ Mettre à jour le prix unitaire

    4. 📊 Tableau de Bord
       └─ Consulter la performance
    ```
    """)

    st.divider()

    st.markdown(f"### {t('documentation.interface_tx_types')}")

    st.markdown("""
    | Type | Quand l'utiliser | Impact sur Cash | Impact Investissement Net |
    |------|------------------|-----------------|---------------------------|
    | DEPOSIT | Versement d'argent | +Montant | +Montant |
    | WITHDRAW | Retrait d'argent | -Montant | -Montant |
    | BUY | Achat d'actif | -Montant | -Montant |
    | SELL | Vente d'actif | +Montant | +Montant |
    | DISTRIBUTION | Dividende/Coupon | +Montant | +Montant |
    | FEE | Frais payés | -Montant | -Montant |
    """)

    st.divider()

    st.markdown(t("documentation.full_doc_link").format(
        title="Interface Web",
        url=f"{DOCS_GITHUB_URL}/INTERFACE_WEB.md",
    ))

    with st.expander(t("documentation.expand_full_doc"), expanded=False):
        content = _load_markdown_file("INTERFACE_WEB.md")
        st.markdown(content)


def _render_tab_installation() -> None:
    """Render the installation and developer documentation tab."""

    st.markdown(f"## {t('documentation.install_title')}")
    st.markdown(t("documentation.install_intro"))

    st.divider()

    st.markdown(f"### {t('documentation.install_quickstart')}")

    st.code("""
# Cloner le dépôt
git clone https://github.com/SKOHscripts/finance-tracker.git
cd finance-tracker

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\\Scripts\\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Initialiser la base de données
finance-tracker init-db
finance-tracker seed-products

# Lancer l'application
streamlit run app.py
    """, language="bash")

    st.divider()

    st.markdown(f"### {t('documentation.install_architecture')}")

    st.markdown("""
    ```
    finance-tracker/
    ├── finance_tracker/
    │   ├── web/           # Interface Streamlit
    │   │   ├── app.py     # Point d'entrée
    │   │   └── views/     # Pages individuelles
    │   ├── cli/           # Interface CLI
    │   ├── core/          # Modèles et calculs
    │   └── services/      # Services métier
    ├── docs/              # Documentation
    ├── tests/             # Tests automatiques
    └── pyproject.toml     # Configuration Poetry
    ```
    """)

    st.divider()

    st.markdown(f"### {t('documentation.install_dev_docs')}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        **Installation complète:**
        [{DOCS_GITHUB_URL}/INSTALLATION_SETUP.md]({DOCS_GITHUB_URL}/INSTALLATION_SETUP.md)

        **Guide CLI:**
        [{DOCS_GITHUB_URL}/CLI_GUIDE.md]({DOCS_GITHUB_URL}/CLI_GUIDE.md)
        """)

    with col2:
        st.markdown(f"""
        **Base de données:**
        [{DOCS_GITHUB_URL}/BASE_DONNEES.md]({DOCS_GITHUB_URL}/BASE_DONNEES.md)

        **Documentation technique:**
        [{DOCS_GITHUB_URL}/DOCUMENTATION_TECHNIQUE.md]({DOCS_GITHUB_URL}/DOCUMENTATION_TECHNIQUE.md)
        """)


def _render_tab_database() -> None:
    """Render the database documentation tab."""

    st.markdown(f"## {t('documentation.database_title')}")
    st.markdown(t("documentation.database_intro"))

    st.divider()

    st.markdown(f"### {t('documentation.database_tables')}")

    st.markdown("""
    **PRODUCTS (Produits)**
    ```
    ├── id (PK)
    ├── name            # Nom du produit
    ├── type            # SCPI, Bitcoin, Cash, etc.
    ├── currency        # EUR, USD
    ├── unit            # Parts, Satoshis, Aucun
    ├── risk_level      # Low, Medium, High, VeryHigh
    └── created_at
    ```

    **TRANSACTIONS (Mouvements)**
    ```
    ├── id (PK)
    ├── product_id (FK) # → PRODUCTS
    ├── type            # DEPOSIT, BUY, SELL, etc.
    ├── date
    ├── quantity        # Nombre d'unités
    ├── unit_price      # Prix par unité
    ├── total_amount    # Montant total en EUR
    ├── description
    └── created_at
    ```

    **VALUATIONS (Valorisations)**
    ```
    ├── id (PK)
    ├── product_id (FK) # → PRODUCTS
    ├── date
    ├── unit_price      # Valeur actuelle par unité
    ├── source          # manual, api
    └── created_at
    ```
    """)

    st.divider()

    st.markdown(f"### {t('documentation.database_relations')}")

    st.markdown("""
    ```
    PRODUCTS ──┬──< TRANSACTIONS (1:N)
               │
               └──< VALUATIONS (1:N)
    ```

    Un produit peut avoir:
    - Plusieurs transactions (achats, ventes, distributions)
    - Plusieurs valorisations (historique des prix)
    """)

    st.divider()

    st.markdown(t("documentation.full_doc_link").format(
        title="Base de Données",
        url=f"{DOCS_GITHUB_URL}/BASE_DONNEES.md",
    ))

    with st.expander(t("documentation.expand_full_doc"), expanded=False):
        content = _load_markdown_file("BASE_DONNEES.md")
        st.markdown(content)


def _render_tab_help() -> None:
    """Render the help and support tab."""

    st.markdown(f"## {t('documentation.help_title')}")

    st.divider()

    st.markdown(f"### {t('documentation.help_faq_title')}")

    faq_items = [
        ("Comment créer mon premier portefeuille?", """
1. Allez à **🏷️ Mes Produits**
2. Cliquez "Ajouter un produit"
3. Remplissez le formulaire (nom, type, devise)
4. Allez à **💸 Mes Transactions**
5. Ajoutez une transaction DEPOSIT
6. Consultez votre **📊 Tableau de Bord**
        """),

        ("Comment mettre à jour la valeur de mon portefeuille?", """
1. Allez à **📈 Mes Valorisations**
2. Cliquez "Ajouter une valorisation"
3. Sélectionnez le produit
4. Entrez la nouvelle valeur unitaire
5. Validez

Les gains latents seront calculés automatiquement!
        """),

        ("Comment sauvegarder mes données?", """
1. Dans la **sidebar gauche**, section "Gestion des Données"
2. Cliquez "📥 Sauvegarder la base (PC)"
3. Fichier `.db` téléchargé sur votre ordinateur

Pour restaurer: utilisez "Importer votre sauvegarde"
        """),

        ("Le prix Bitcoin se met-il à jour automatiquement?", """
Oui! L'**₿ Espace Bitcoin** utilise l'API CoinGecko pour récupérer
le prix en temps réel. Les mises à jour sont automatiques.
        """),
        ]

    for question, answer in faq_items:
        with st.expander(question):
            st.markdown(answer)

    st.divider()

    st.markdown(f"### {t('documentation.help_resources_title')}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(t("documentation.help_resources_official"))
        st.markdown(t("documentation.help_resources_web"))
        st.markdown(t("documentation.help_resources_github"))

    with col2:
        st.markdown(t("documentation.help_resources_support"))
        st.markdown(t("documentation.help_resources_bug"))
        st.markdown(t("documentation.help_resources_feature"))

    with col3:
        st.markdown(t("documentation.help_resources_docs"))
        st.markdown(t("documentation.help_resources_readme").format(url=GITHUB_BASE_URL))
        st.markdown(t("documentation.help_resources_roadmap").format(url=DOCS_GITHUB_URL))

    st.divider()

    st.markdown(f"### {t('documentation.help_tips_title')}")
    st.info(t("documentation.help_tips"))


def render(session: Session) -> None:
    """Render the documentation page."""

    st.title(t("documentation.title"))
    st.markdown(t("documentation.subtitle"))

    st.divider()

    tabs = st.tabs([
        t("documentation.tab_home"),
        t("documentation.tab_concepts"),
        t("documentation.tab_calculs"),
        t("documentation.tab_inflation"),
        t("documentation.tab_interface"),
        t("documentation.tab_database"),
        t("documentation.tab_install"),
        t("documentation.tab_help"),
        ])

    tab_home, tab_concepts, tab_calculs, tab_inflation, tab_interface, tab_database, tab_install, tab_help = tabs

    with tab_home:
        _render_tab_home()

    with tab_concepts:
        _render_tab_concepts()

    with tab_calculs:
        _render_tab_calculs()

    with tab_inflation:
        _render_tab_inflation()

    with tab_interface:
        _render_tab_interface()

    with tab_database:
        _render_tab_database()

    with tab_install:
        _render_tab_installation()

    with tab_help:
        _render_tab_help()
