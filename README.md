# 💼 Finance Tracker – Gestion de Portefeuille Intelligente

[![Version](https://img.shields.io/github/v/release/SKOHscripts/finance-tracker?display_name=tag)](https://github.com/SKOHscripts/finance-tracker/releases)
[![License](https://img.shields.io/github/license/SKOHscripts/finance-tracker)](./LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/SKOHscripts/finance-tracker/tests.yml?label=tests)](https://github.com/SKOHscripts/finance-tracker/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)

> Finance Tracker un outil complet et facile à utiliser pour gérer, analyser et
> optimiser vos investissements, comprendre l'impact des intérêts composés et
> des impôts, ou simplement planifier un budget. Bien que pensée d'abord pour
> les francophones, elle sera bientôt traduite pour une diffusion maximale. La
> protection de votre vie privée et de votre souveraineté est assurée par le
> stockage local des informations.

---

## 📑 Table des Matières

- [✨ Présentation Générale](#-présentation-générale)
- [⚡ Quick Start](#-quick-start)
  - [Utilisateur – Zéro installation](#utilisateur--zéro-installation)
  - [Développeur – Démarrage rapide](#développeur--démarrage-rapide)
- [🌐 Fonctionnalités Principales](#-fonctionnalités-principales)
- [📚 Documentation Spécialisée](#-documentation-spécialisée)
  - [Concepts fondamentaux](#concepts-fondamentaux)
  - [Interface web](#interface-web)
  - [Base de données](#base-de-données)
  - [Formules & modèles](#formules--modèles)
  - [Lignes de commande & installation avancée](#lignes-de-commande--installation-avancée)
- [🧱 Architecture du Projet](#-architecture-du-projet)
- [🧪 Tests & Qualité](#-tests--qualité)
- [🤝 Contribution](#-contribution)
- [📄 Licence](#-licence)

---

## ✨ Présentation Générale

**Finance Tracker** est une application de gestion de portefeuille qui permet de :

- Centraliser vos **produits financiers** (cash, SCPI, assurance-vie, PER, Bitcoin, etc.) ou vos projets (achat de vélo électrique, etc.).
- Suivre vos **transactions** et **valorisations** dans le temps.
- Calculer des indicateurs de performance réalistes (MWRR, rendement annualisé, etc.).
- Visualiser l’évolution de votre patrimoine via un **dashboard web** clair.
- Générer des **rapports PDF** et utiliser une **CLI** pour les utilisateurs avancés.

Deux publics cibles :

- 👤 **Utilisateurs finaux** : veulent utiliser l’application web et suivre leurs investissements.
- 💻 **Développeurs / power users** : veulent installer en local, utiliser la CLI ou contribuer au projet.

---

## ⚡ Quick Start

### Utilisateur – Zéro installation

1. Ouvrez l’application hébergée :
   👉 **https://finance-tracker-skohscripts.streamlit.app/**
2. Créez / chargez quelques produits et transactions de test.
3. Explorez le **📊 Tableau de bord** et les graphiques.
4. Consultez la page **📖 Documentation** intégrée pour les explications rapides.

> Toutes les données restent stockées côté app / base configurée, vous n’avez rien à installer localement.

### Développeur – Démarrage rapide

Pour un setup minimal de développement :

```bash
git clone https://github.com/SKOHscripts/finance-tracker.git
cd finance-tracker

python3 -m venv venv
source venv/bin/activate      # macOS / Linux
# ou
venv\Scripts\activate         # Windows

pip install -r requirements.txt

# Initialiser la base de données
finance-tracker init-db
finance-tracker seed-products

# Lancer l'application web
streamlit run app.py
```

Pour un guide complet, voir :
👉 **[docs/INSTALLATION_SETUP.md](./docs/INSTALLATION_SETUP.md)**

---

## 🌐 Fonctionnalités Principales

### Interface Web (Streamlit)

- **📊 Tableau de bord**
  Vue globale du portefeuille, répartition par produit/catégorie, graphiques temporels, performance globale vs objectifs.

- **➕ Gestion des transactions**
  Achat / vente, rebalance, historique détaillé, filtrage et export.

- **💰 Valorisation des positions**
  Suivi des valorisations, comparaison valeur actuelle vs coût d’acquisition, distributions reçues.

- **₿ Espace Bitcoin**
  Prix en temps réel (API CoinGecko), conversions EUR/BTC, historique sur 1 an, scénarios simples.

- **📄 Rapports PDF**
  Génération de rapports complets, prêts à être partagés (PDF via WeasyPrint).

- **📈 Simulateur long terme**
  Projections multi‑scénarios, croissance composée, analyse de sensibilité.

- **📊 Inflation paramétrable**
  Profils d'inflation prédéfinis (IPC standard, urbain locataire, projet immo, m² de ville) ou taux personnalisé. Voir la section [Inflation](#-inflation-paramétrable) ci-dessous.

👉 Détails : **[docs/INTERFACE_WEB.md](./docs/INTERFACE_WEB.md)**

---

## 📊 Inflation Paramétrable

Le simulateur long terme propose quatre profils d'inflation prédéfinis, plus une option personnalisée :

| Profil | Taux | Plage indicative | Cas d'usage |
|---|---|---|---|
| **Standard IPC** (défaut) | 2,0 %/an | 1,7–2,0 % | Neutraliser l'inflation officielle sur les dépenses courantes |
| **Urbain locataire** | 2,3 %/an | 2,2–2,5 % | Locataire en ville avec un loyer significatif |
| **Vie urbaine + projet immo** | 3,0 %/an | 2,7–3,2 % | Utilisateur visant l'accession à la propriété en ville |
| **Indexé m² de ville** | 4,0 %/an | 3,5–5,0 % | Suivi du patrimoine au prix du m² immobilier urbain |
| **Personnalisé** | libre | — | Saisir manuellement tout autre taux |

Les taux sont basés sur les séries longues [INSEE IPC](https://www.insee.fr/fr/statistiques/4268033), les indices de référence des loyers ([IRL — ANIL](https://www.anil.org/outils/indices-et-plafonds/tableau-de-lirl/)) et les travaux [IGEDD/Friggit](https://www.cgedd.fr/prix-immobilier-friggit.pdf) sur l'évolution des prix immobiliers.

> **Comment ça marche ?** Dans le simulateur, remplace le simple champ *Inflation annuelle (%)* par un sélecteur de profil. Le taux correspondant est appliqué automatiquement à toutes les projections et apparaît dans le rapport PDF exporté.

---

## 📚 Documentation Spécialisée

La documentation est découpée en plusieurs guides thématiques pour rester claire et ciblée :

### Concepts fondamentaux

Comprendre les **types de produits** supportés (cash, SCPI, assurance‑vie, PER, crypto…), les notions de rendement, risque, distributions, valorisation, etc.

- 👉 **[docs/CONCEPTS_FONDAMENTAUX.md](./docs/CONCEPTS_FONDAMENTAUX.md)**

### Interface web

Guide pas à pas de chaque page Streamlit :

- Tableau de bord
- Formulaires d’ajout / édition
- Espace Bitcoin
- Rapports PDF
- Simulateur long terme

- 👉 **[docs/INTERFACE_WEB.md](./docs/INTERFACE_WEB.md)**

### Base de données

Description de la **structure SQLite** (tables `products`, `transactions`, `valuations`, etc.), types de champs, contraintes, et conventions de nommage.

- 👉 **[docs/BASE_DONNEES.md](./docs/BASE_DONNEES.md)**
- 👉 **[docs/DOCUMENTATION_TECHNIQUE.md](./docs/DOCUMENTATION_TECHNIQUE.md)**

### Formules & modèles

Détail des formules de calcul utilisées par le cœur métier :

- Modified Dietz Return (MWRR)
- Rendement annualisé
- Concepts issus de la **théorie moderne du portefeuille (MPT)** pour la volatilité et la corrélation
- Autres indicateurs clés utilisés par les vues et services.

- 👉 **[docs/FORMULES_CALCULS.md](./docs/FORMULES_CALCULS.md)**

### Lignes de commande & installation avancée

Pour les utilisateurs qui veulent **toucher aux lignes de commande** ou **développer dans le projet** :

- Installation détaillée.
- Commandes CLI principales (`dashboard`, `add-transaction`, `report`, etc.).
- Structure du projet et organisation des modules.
- Déploiement et troubleshooting.

- 👉 **Guide installation & setup complet : [docs/INSTALLATION_SETUP.md](./docs/INSTALLATION_SETUP.md)**
- 👉 **Guide CLI : [docs/CLI_GUIDE.md](./docs/CLI_GUIDE.md)**

---

## 🧱 Architecture du Projet

Structure simplifiée du dépôt :

```bash
finance-tracker/
├── README.md                    # Ce fichier
├── requirements.txt             # Dépendances pip
├── pyproject.toml               # Config Poetry
├── docs/                        # Documentation spécialisée
│   ├── CONCEPTS_FONDAMENTAUX.md
│   ├── INTERFACE_WEB.md
│   ├── BASE_DONNEES.md
│   ├── FORMULES_CALCULS.md
│   ├── CLI_GUIDE.md
│   ├── INSTALLATION_SETUP.md
│   └── ROADMAP.md
├── finance_tracker/
│   ├── web/                     # Interface Streamlit
│   │   ├── app.py               # Point d'entrée Streamlit
│   │   └── views/               # Pages individuelles
│   │       ├── dashboard.py
│   │       ├── transactions.py
│   │       ├── valuations.py
│   │       ├── bitcoin.py
│   │       ├── products.py
│   │       ├── simulation.py
│   │       └── documentation.py
│   ├── cli/                     # Interface en ligne de commande
│   │   ├── main.py
│   │   ├── commands.py
│   │   └── formatters.py
│   ├── core/                    # Logique métier
│   │   ├── models.py            # Modèles SQLModel
│   │   ├── schemas.py           # Schémas Pydantic
│   │   ├── database.py          # Accès / init BD
│   │   └── calculations.py      # Calculs financiers
│   └── services/                # Services métier
│       ├── portfolio.py
│       ├── bitcoin.py
│       ├── export.py
│       └── simulator.py
├── tests/                       # Tests automatiques
│   ├── test_models.py
│   ├── test_calculations.py
│   └── conftest.py
└── finance_tracker.db           # Base SQLite (générée)
```

👉 Pour une description plus détaillée de chaque dossier et composant, voir :
**[docs/INSTALLATION_SETUP.md](./docs/INSTALLATION_SETUP.md)** et **[docs/ROADMAP.md](./docs/ROADMAP.md)**.

---

## 🧪 Tests & Qualité

Le projet s’appuie sur un ensemble d’outils pour garantir la qualité :

- **Tests** : `pytest`, `pytest-cov`
- **Formatage** : `black`
- **Linting** : `ruff`
- **Typing** : `mypy`

Commandes usuelles :

```bash
# Lancer la suite de tests
pytest

# Couverture
pytest --cov=finance_tracker

# Formatage
black finance_tracker tests

# Lint
ruff check finance_tracker tests

# Typage
mypy finance_tracker
```

---

## 🤝 Contribution

Les contributions sont les bienvenues !

1. Forker le dépôt.
2. Créer une branche de fonctionnalité :
   ```bash
   git checkout -b feature/ma-fonctionnalite
   ```
3. Installer en mode développement :
   ```bash
   pip install -e ".[dev]"
   ```
4. Lancer les tests et le lint :
   ```bash
   pytest
   black finance_tracker tests
   ruff check finance_tracker tests
   ```
5. Ouvrir une Pull Request avec une description claire.

Ou simplement proposer une feature dans les issues.

Pour plus de détails sur les conventions et la roadmap :
👉 **[docs/ROADMAP.md](./docs/ROADMAP.md)**

---

## 📄 Licence

Voir le fichier **[LICENSE](./LICENSE)** pour plus de détails.

---

## 🔗 Liens Utiles

- 🌐 **Application web** : https://finance-tracker-skohscripts.streamlit.app/
- 💻 **Code source** : https://github.com/SKOHscripts/finance-tracker
- 🐛 **Issues** : https://github.com/SKOHscripts/finance-tracker/issues
