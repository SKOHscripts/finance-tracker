"""
Documentation page for Finance Tracker Streamlit application.

This module renders a comprehensive documentation hub with tabs for
different documentation sections, optimized for Streamlit display.
All documentation links point to the GitHub repository markdown files.
"""

import streamlit as st
from sqlmodel import Session
from pathlib import Path


# GitHub repository base URL for markdown files
GITHUB_BASE_URL = "https://github.com/SKOHscripts/finance-tracker/blob/main"
DOCS_GITHUB_URL = f"{GITHUB_BASE_URL}/docs"


def _get_docs_path() -> Path:
    """Get the absolute path to the docs directory."""
    current_dir = Path(__file__).parent.parent.parent.parent

    return current_dir / "docs"


def _load_markdown_file(filename: str) -> str:
    """
    Load markdown content from docs directory.

    Args:
        filename: Name of the markdown file (e.g., "CONCEPTS_FONDAMENTAUX.md")

    Returns:
        Content of the file as string, or error message if not found
    """
    try:
        docs_path = _get_docs_path()
        file_path = docs_path / filename

        if not file_path.exists():
            return f"⚠️ Fichier {filename} introuvable."

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"❌ Erreur lors du chargement du fichier: {str(e)}"


def _render_github_link(filename: str, label: str = "Voir sur GitHub") -> str:
    """Generate a GitHub link for a documentation file."""

    if filename.startswith("docs/"):
        url = f"{GITHUB_BASE_URL}/{filename}"
    else:
        url = f"{DOCS_GITHUB_URL}/{filename}"

    return f"🔗 [{label}]({url})"


def _render_section_card(title: str, description: str, icon: str, link_url: str) -> None:
    """Render a clickable section card with icon and description."""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e3a5f 0%, #2d4a6f 100%);
                padding: 1.2rem;
                border-radius: 10px;
                margin-bottom: 1rem;
                border-left: 4px solid #4da6ff;">
        <h4 style="margin: 0; color: #ffffff;">{icon} {title}</h4>
        <p style="margin: 0.5rem 0 0 0; color: #b8c9d9; font-size: 0.9rem;">{description}</p>
        <a href="{link_url}" target="_blank" style="color: #4da6ff; font-size: 0.85rem;">📖 Lire la documentation complète →</a>
    </div>
    """, unsafe_allow_html=True)


def _render_tab_home() -> None:
    """Render the home/welcome tab with project overview."""

    st.markdown("""
    ## 👋 Bienvenue dans Finance Tracker

    **Finance Tracker** est une application complète de gestion de portefeuille d'investissement,
    conçue pour les investisseurs francophones soucieux de leur vie privée.
    """)

    # Badges
    st.markdown("""
    [![Version](https://img.shields.io/github/v/release/SKOHscripts/finance-tracker?display_name=tag)](https://github.com/SKOHscripts/finance-tracker/releases)
    [![License](https://img.shields.io/github/license/SKOHscripts/finance-tracker)](https://github.com/SKOHscripts/finance-tracker/blob/main/LICENSE)
    [![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
    """)

    st.divider()

    # Features overview
    st.markdown("### ✨ Fonctionnalités Principales")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **📊 Suivi Complet**
        - Portefeuille multi-actifs
        - SCPI, Bitcoin, Livrets
        - Assurance-vie, PER
        """)

    with col2:
        st.markdown("""
        **📈 Analyses Avancées**
        - Performance MWRR
        - Intérêts composés
        - Projections long terme
        """)

    with col3:
        st.markdown("""
        **🔒 Vie Privée**
        - Données locales
        - Aucun cloud requis
        - Export/Import facile
        """)

    st.divider()

    # Quick start
    st.markdown("### 🚀 Démarrage Rapide")

    st.markdown("""
    | Étape | Action | Page |
    |-------|--------|------|
    | 1️⃣ | Créer vos produits | 🏷️ **Mes Produits** |
    | 2️⃣ | Ajouter des transactions | 💸 **Mes Transactions** |
    | 3️⃣ | Mettre à jour les valorisations | 📈 **Mes Valorisations** |
    | 4️⃣ | Consulter le tableau de bord | 📊 **Tableau de Bord** |
    """)

    st.divider()

    # Links to documentation
    st.markdown("### 📚 Explorer la Documentation")

    st.markdown("Utilisez les **onglets ci-dessus** pour accéder aux différentes sections de documentation.")

    st.info("""
    **💡 Astuce:** Commencez par l'onglet **📚 Concepts** pour comprendre les 3 piliers
    du système (Produits, Transactions, Valorisations) avant d'utiliser l'application.
    """)


def _render_tab_concepts() -> None:
    """Render the fundamental concepts documentation tab."""

    st.markdown("""
    ## 📚 Concepts Fondamentaux

    Finance Tracker repose sur **trois piliers** essentiels. Comprendre ces concepts
    est la clé pour utiliser efficacement l'application.
    """)

    st.divider()

    # Pillar 1: Products
    st.markdown("### 1️⃣ Produits (Products)")
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

    # Pillar 2: Transactions
    st.markdown("### 2️⃣ Transactions (Mouvements)")
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

    # Pillar 3: Valuations
    st.markdown("### 3️⃣ Valorisations (Snapshots)")
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

    # Link to full documentation
    st.markdown(f"""
    🔗 **[Lire la documentation complète: Concepts Fondamentaux]({DOCS_GITHUB_URL}/CONCEPTS_FONDAMENTAUX.md)**
    """)

    # Expandable full content
    with st.expander("📄 Voir le document complet", expanded=False):
        content = _load_markdown_file("CONCEPTS_FONDAMENTAUX.md")
        st.markdown(content)


def _render_tab_calculs() -> None:
    """Render the formulas and calculations documentation tab."""

    st.markdown("""
    ## 📐 Formules & Calculs

    Toutes les formules mathématiques utilisées par Finance Tracker pour calculer
    les performances, gains et projections.
    """)

    st.divider()

    # Key indicators
    st.markdown("### 📊 Indicateurs Clés")

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

    # Compound interest
    st.markdown("### 📈 Intérêts Composés")

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

    # Bitcoin specifics
    st.markdown("### ₿ Cas Spécial: Bitcoin")

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

    # Link to full documentation
    st.markdown(f"""
    🔗 **[Lire la documentation complète: Formules & Calculs]({DOCS_GITHUB_URL}/FORMULES_CALCULS.md)**
    """)

    with st.expander("📄 Voir le document complet", expanded=False):
        content = _load_markdown_file("FORMULES_CALCULS.md")
        st.markdown(content)


def _render_tab_interface() -> None:
    """Render the web interface documentation tab."""

    st.markdown("""
    ## 💻 Guide Interface Web

    Guide complet page par page de l'interface Streamlit.
    """)

    st.divider()

    # Pages overview
    st.markdown("### 📑 Architecture de l'Application")

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

    # Key workflows
    st.markdown("### 🔄 Flux de Travail Recommandé")

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

    # Transaction types detail
    st.markdown("### 💰 Types de Transactions")

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

    # Link to full documentation
    st.markdown(f"""
    🔗 **[Lire la documentation complète: Interface Web]({DOCS_GITHUB_URL}/INTERFACE_WEB.md)**
    """)

    with st.expander("📄 Voir le document complet", expanded=False):
        content = _load_markdown_file("INTERFACE_WEB.md")
        st.markdown(content)


def _render_tab_installation() -> None:
    """Render the installation and developer documentation tab."""

    st.markdown("""
    ## 🛠️ Installation & Développement

    Guides pour installer, configurer et contribuer au projet.
    """)

    st.divider()

    # Quick start
    st.markdown("### ⚡ Démarrage Rapide (Développeur)")

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

    # Architecture
    st.markdown("### 🧱 Architecture du Projet")

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

    # Links to full documentation
    st.markdown("### 🔗 Documentation Développeur")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        **Installation complète:**
        🔗 [INSTALLATION_SETUP.md]({DOCS_GITHUB_URL}/INSTALLATION_SETUP.md)

        **Guide CLI:**
        🔗 [CLI_GUIDE.md]({DOCS_GITHUB_URL}/CLI_GUIDE.md)
        """)

    with col2:
        st.markdown(f"""
        **Base de données:**
        🔗 [BASE_DONNEES.md]({DOCS_GITHUB_URL}/BASE_DONNEES.md)

        **Documentation technique:**
        🔗 [DOCUMENTATION_TECHNIQUE.md]({DOCS_GITHUB_URL}/DOCUMENTATION_TECHNIQUE.md)
        """)


def _render_tab_database() -> None:
    """Render the database documentation tab."""

    st.markdown("""
    ## 🗄️ Structure de la Base de Données

    Finance Tracker utilise **SQLite** avec **SQLModel** pour la persistance des données.
    """)

    st.divider()

    # Main tables
    st.markdown("### 📊 Tables Principales")

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

    # Relations
    st.markdown("### 🔗 Relations")

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

    # Link to full documentation
    st.markdown(f"""
    🔗 **[Lire la documentation complète: Base de Données]({DOCS_GITHUB_URL}/BASE_DONNEES.md)**
    """)

    with st.expander("📄 Voir le document complet", expanded=False):
        content = _load_markdown_file("BASE_DONNEES.md")
        st.markdown(content)


def _render_tab_help() -> None:
    """Render the help and support tab."""

    st.markdown("""
    ## 🆘 Aide & Support
    """)

    st.divider()

    # FAQ
    st.markdown("### ❓ FAQ Rapide")

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
1. Dans la **sidebar gauche**, section "💾 Gestion des Données"
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
        with st.expander(f"❓ {question}"):
            st.markdown(answer)

    st.divider()

    # Resources
    st.markdown("### 🌐 Ressources")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **📱 Liens Officiels**

        [🌐 Application Web](https://finance-tracker-skohscripts.streamlit.app/)

        [💻 GitHub](https://github.com/SKOHscripts/finance-tracker)
        """)

    with col2:
        st.markdown("""
        **💬 Support**

        [🐛 Signaler un bug](https://github.com/SKOHscripts/finance-tracker/issues)

        [💡 Proposer une fonctionnalité](https://github.com/SKOHscripts/finance-tracker/discussions)
        """)

    with col3:
        st.markdown("""
        **📚 Documentation**

        [📖 README complet]({github}/README.md)

        [🗺️ Roadmap]({docs}/ROADMAP.md)
        """.format(github=GITHUB_BASE_URL, docs=DOCS_GITHUB_URL))

    st.divider()

    # Tips
    st.markdown("### 💡 Conseils d'Utilisation")

    st.info("""
    **Conseil #1:** Commencez par lire les **📚 Concepts** pour comprendre les 3 piliers du système.

    **Conseil #2:** Mettez à jour vos **📈 Valorisations** régulièrement (mensuellement minimum).

    **Conseil #3:** Utilisez le **🔮 Simulateur** pour planifier vos investissements futurs.

    **Conseil #4:** Sauvegardez régulièrement votre base de données via la sidebar.
    """)


def render(session: Session) -> None:
    """
    Render the documentation page.

    Main entry point called from navigation.py.
    Displays documentation in multiple tabs for better organization.

    Args:
        session: SQLModel database session (required by navigation pattern)
    """

    # Page title
    st.title("📖 Documentation")
    st.markdown("Guide complet pour utiliser et comprendre Finance Tracker")

    st.divider()

    # Create tabs
    tabs = st.tabs([
        "👋 Accueil",
        "📚 Concepts",
        "📐 Calculs",
        "💻 Interface Web",
        "🗄️ Base de Données",
        "🛠️ Installation",
        "🆘 Aide"
    ])

    tab_home, tab_concepts, tab_calculs, tab_interface, tab_database, tab_install, tab_help = tabs

    with tab_home:
        _render_tab_home()

    with tab_concepts:
        _render_tab_concepts()

    with tab_calculs:
        _render_tab_calculs()

    with tab_interface:
        _render_tab_interface()

    with tab_database:
        _render_tab_database()

    with tab_install:
        _render_tab_installation()

    with tab_help:
        _render_tab_help()
