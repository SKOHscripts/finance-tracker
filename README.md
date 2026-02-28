# 💼 Finance Tracker - Gestion de Portefeuille Intelligente

> Une application complète pour suivre, analyser et optimiser votre portefeuille d'investissements. Conçue pour les investisseurs francophones qui veulent garder le contrôle total de leurs données.

---

## 📑 Table des Matières

### 🚀 Démarrage Rapide
- [**Utiliser l'Application**](#-utiliser-lapplication) - Accès direct en ligne (recommandé)
- [**Guide Installation**](#-guide-dinstallation-pour-développeurs) - Pour développeurs locaux

### 📚 Documentation Principale
- [**Concepts Fondamentaux**](#-concepts-fondamentaux) - Comprendre l'architecture
- [**Interface Web**](#-interface-web) - Tour des fonctionnalités
- [**Calculs & Formules**](#-calculs--formules) - Mathématiques appliquées
- [**Base de Données**](#-base-de-données) - Structure des données
- [**CLI Guide**](#-cli-guide) - Utilisation en ligne de commande

### 🛠️ Pour les Développeurs
- [**Architecture Technique**](#-architecture-technique) - Structure du projet
- [**Contribution**](#-contribution) - Contribuer au projet
- [**Roadmap**](#-roadmap) - Évolutions prévues

### 🔗 Liens Rapides
- [🌐 Application Web](https://finance-tracker-skohscripts.streamlit.app/)
- [💻 GitHub Repository](https://github.com/SKOHscripts/finance-tracker)
- [📖 Documentation Complète](#-documentation-complète)

---

## 🎯 Utiliser l'Application

### Option 1: Application Web (Recommandé) ✨

**Aucune installation requise!**

👉 **[Accès direct: https://finance-tracker-skohscripts.streamlit.app/](https://finance-tracker-skohscripts.streamlit.app/)**

#### Avantages:
✅ Pas d'installation  
✅ Toujours à jour  
✅ Accès depuis n'importe quel navigateur  
✅ Données persistantes  

#### Premiers pas:
1. Accédez au lien ci-dessus
2. Découvrez les **concepts fondamentaux** dans la page Documentation
3. Commencez à ajouter vos produits et transactions
4. Explorez le tableau de bord et les simulations

---

## 📖 Guide d'Installation pour Développeurs

### ✅ Prérequis

| Composant | Version | Vérification |
|-----------|---------|-------------|
| **Python** | 3.11+ | `python3 --version` |
| **Git** | Dernière | `git --version` |
| **Système** | Win 10+, macOS 10.14+, Linux | N/A |

### 💻 Installation Locale

#### 1️⃣ Cloner le Dépôt

```bash
git clone https://github.com/SKOHscripts/finance-tracker.git
cd finance-tracker
```

#### 2️⃣ Créer un Environnement Virtuel

**Avec venv (natif Python):**
```bash
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
# ou
venv\Scripts\activate       # Windows
```

**Avec Poetry (recommandé):**
```bash
pip install poetry
poetry install
poetry shell
```

#### 3️⃣ Installer les Dépendances

**Avec pip:**
```bash
pip install -r requirements.txt
```

**Avec Poetry:**
```bash
poetry install
```

#### 4️⃣ Initialiser la Base de Données

```bash
# Créer la BD et les tables
finance-tracker init-db

# Charger les produits par défaut
finance-tracker seed-products
```

#### 5️⃣ Lancer l'Application

```bash
streamlit run app.py
```

Ouvrez: **http://localhost:8501**

### 🔌 Troubleshooting Installation

**❌ "command not found: finance-tracker"**
```bash
# Réinstaller dans l'env actif
pip install -e .
```

**❌ "ModuleNotFoundError: No module named 'streamlit'"**
```bash
# Vérifier l'env est activé
source venv/bin/activate
pip install -r requirements.txt
```

**❌ Port 8501 déjà utilisé**
```bash
streamlit run app.py --server.port 8502
```

[📚 Guide complet d'installation →](./INSTALLATION_GUIDE_DEV.md)

---

## 🎓 Concepts Fondamentaux

### 💰 Produits Supportés

Finance Tracker supporte 6 catégories d'investissements:

| Produit | Type | Rendement | Risque |
|---------|------|-----------|--------|
| **💵 Cash** | Liquide | 🟢 Faible | 🟢 Minimal |
| **📋 Livret A** | Épargne | 🟢 Faible | 🟢 Minimal |
| **🏘️ SCPI** | Immobilier | 🟡 Moyen | 🟡 Moyen |
| **💳 Assurance Vie** | Assurance | 🟡 Moyen | 🟡 Moyen |
| **🎯 PER** | Retraite | 🟡 Moyen | 🟡 Moyen |
| **₿ Bitcoin** | Crypto | 🔴 Élevé | 🔴 Élevé |

### 📊 Principes Clés

**Performance Totale = Gains + Distributions + Évolutions**

L'application calcule automatiquement:
- 📈 Rendement en % (annualisé si pertinent)
- 💹 Évolution du capital
- 💵 Distributions reçues
- 📋 Valeur actuelle vs coût d'acquisition

[📚 Lire plus sur les concepts →](./docs/CONCEPTS_FONDAMENTAUX.md)

---

## 🌐 Interface Web

### Pages Principales

#### 📊 Tableau de Bord
- **Vue globale** de votre portefeuille
- **Répartition** par produit et par catégorie
- **Graphiques** d'évolution temporelle
- **Performance** globale vs objectifs

#### ➕ Ajouter Transaction
- **Acheter** des produits
- **Vendre** des produits
- **Rebalancer** le portefeuille
- Historique complet des transactions

#### 💰 Ajouter Valorisation
- **Évaluer** les positions actuelles
- **Tracker** les variations de valeur
- **Comparer** vs coût d'acquisition
- Gérer les distributions reçues

#### ₿ Espace Bitcoin
- **Prix en temps réel** (API CoinGecko)
- **Conversions** EUR/BTC
- **Historique** sur 1 an
- **Prévisions** simples

#### 📋 Listes & Édition
- **Voir tous** les produits et transactions
- **Éditer** ou **supprimer** des entrées
- **Filtrer** par critères
- **Exporter** les données

#### 📄 Rapport PDF
- **Générer** un rapport complet
- **Personnaliser** date et contenu
- **Télécharger** au format PDF
- Idéal pour présentation/archivage

#### 📈 Simulateur Long Terme
- **Projeter** votre portefeuille
- **Tester** différents scénarios
- **Visualiser** croissance composée
- **Analyser** sensibilité aux paramètres

[📚 Lire le guide complet →](./docs/INTERFACE_WEB.md)

---

## 📐 Calculs & Formules

### Performance (MWRR)

L'application calcule la **Modified Dietz Return** (rendement pondéré par le temps):

```
Rendement = (Valeur Finale - Valeur Initiale - Flux) / Valeur Initiale
```

Plus précis que TIR pour les portefeuilles avec flux multiples.

### Rendement Annualisé

```
Rendement Annualisé = (1 + Rendement) ^ (365 / Jours) - 1
```

Permet de comparer des périodes différentes équitablement.

### Répartition Optimale

Basée sur la **théorie moderne du portefeuille (MPT)**:

```
σ_p = √(w₁²σ₁² + w₂²σ₂² + 2w₁w₂ρ₁₂σ₁σ₂)
```

Où:
- `w` = poids du produit
- `σ` = volatilité
- `ρ` = corrélation

[📚 Formules détaillées →](./docs/FORMULES_CALCULS.md)

---

## 🗄️ Base de Données

### Structure

L'application utilise **SQLite** (fourni avec l'app):

#### Table `products`
```sql
- id (int, clé primaire)
- name (str): Nom du produit
- category (str): Cash | SCPI | Crypto | Insurance | PER
- risk_level (float): 0-10
- created_at (datetime)
```

#### Table `transactions`
```sql
- id (int, clé primaire)
- product_id (int, FK)
- type (str): "buy" | "sell"
- quantity (float)
- unit_price (float)
- date (date)
- notes (str)
```

#### Table `valuations`
```sql
- id (int, clé primaire)
- product_id (int, FK)
- market_value (float): Valeur actuelle
- date (date)
- notes (str)
```

[📚 Lire le modèle complet →](./docs/BASE_DONNEES.md)

---

## ⌨️ CLI Guide

### Commandes de Base

```bash
# Voir le portefeuille actuel
finance-tracker dashboard

# Avec format JSON
finance-tracker dashboard --json

# Ajouter une transaction
finance-tracker add-transaction \
  --product "Bitcoin" \
  --quantity 0.5 \
  --price 45000 \
  --type buy

# Générer un rapport
finance-tracker report --format pdf
```

[📚 Toutes les commandes →](./docs/CLI_GUIDE.md)

---

## 🏗️ Architecture Technique

### Structure du Projet

```
finance-tracker/
├── 📄 README.md                           # Ce fichier
├── 📄 INSTALLATION_GUIDE_DEV.md           # Guide d'installation complet
│
├── finance_tracker/                       # 📦 Package principal
│   ├── web/                               # 🌐 Interface Streamlit
│   │   ├── app.py                         # Point d'entrée
│   │   └── views/                         # Pages individuelles
│   │       ├── dashboard.py
│   │       ├── transactions.py
│   │       ├── valuations.py
│   │       ├── bitcoin.py
│   │       ├── products.py
│   │       ├── simulation.py
│   │       ├── reports.py
│   │       └── documentation.py           # Page d'aide
│   │
│   ├── cli/                               # ⌨️ Interface CLI
│   │   ├── main.py
│   │   ├── commands.py
│   │   └── formatters.py
│   │
│   ├── core/                              # 🎯 Logique métier
│   │   ├── models.py                      # Modèles SQLModel
│   │   ├── schemas.py                     # Schémas Pydantic
│   │   ├── database.py                    # Gestion BD
│   │   └── calculations.py                # Calculs financiers
│   │
│   └── services/                          # 🔧 Services métier
│       ├── portfolio.py
│       ├── bitcoin.py
│       ├── export.py
│       └── simulator.py
│
├── docs/                                  # 📚 Documentation
│   ├── CONCEPTS_FONDAMENTAUX.md
│   ├── INTERFACE_WEB.md
│   ├── CALCULS_FORMULES.md
│   ├── BASE_DONNEES.md
│   ├── CLI_GUIDE.md
│   ├── INSTALLATION_GUIDE_DEV.md
│   └── ROADMAP.md
│
├── tests/                                 # 🧪 Tests
│   ├── test_models.py
│   ├── test_calculations.py
│   └── conftest.py
│
├── pyproject.toml                         # 📋 Configuration Poetry
├── requirements.txt                       # 📋 Dépendances pip
└── finance_tracker.db                     # 💾 Base de données
```

### Stack Technologique

| Couche | Technologies |
|--------|--------------|
| **Frontend** | Streamlit 1.30+, Altair, Markdown |
| **Backend** | Python 3.11+, Pydantic, SQLModel |
| **BD** | SQLite 3, SQLAlchemy ORM |
| **CLI** | Typer, Click, Rich |
| **Export** | WeasyPrint (PDF), Jinja2 |
| **APIs** | CoinGecko (prix Bitcoin) |
| **Testing** | Pytest, Pytest-cov |

---

## 🤝 Contribution

Nous accueillons les contributions! Voici comment:

### 1. Fork le Projet
```bash
# Sur GitHub: cliquez "Fork"
```

### 2. Clone Votre Fork
```bash
git clone https://github.com/YOUR_USERNAME/finance-tracker.git
cd finance-tracker
```

### 3. Créer une Branche
```bash
git checkout -b feature/ma-fonctionnalite
```

### 4. Faire les Changements
```bash
# Installer en mode développement
pip install -e ".[dev]"

# Tester vos modifications
pytest

# Vérifier le style
black finance_tracker tests
ruff check finance_tracker tests
```

### 5. Committer et Pousser
```bash
git add .
git commit -m "feat: ajouter ma fonctionnalité"
git push origin feature/ma-fonctionnalite
```

### 6. Créer une Pull Request
- Sur GitHub, cliquez "New Pull Request"
- Décrivez votre changement
- Attendez la review

### Bonnes Pratiques

✅ **Types de commits:**
- `feat:` Nouvelle fonctionnalité
- `fix:` Correction de bug
- `docs:` Documentation
- `refactor:` Refactorisation
- `test:` Tests

✅ **Avant de committer:**
- Tester localement: `pytest`
- Vérifier le style: `black`, `ruff`
- Documenter si nécessaire

✅ **Contributions bienvenues:**
- 🐛 Rapporter des bugs
- 🚀 Proposer des fonctionnalités
- 📚 Améliorer la documentation
- ♻️ Refactoriser le code
- 🧪 Ajouter des tests

---

## 🗺️ Roadmap

### Phase 1: Fondamentaux (✅ Complété)
- ✅ Architecture multi-couches
- ✅ Gestion produits/transactions/valorisations
- ✅ Interface Streamlit
- ✅ CLI basique
- ✅ Export PDF

### Phase 2: Optimisation (🟡 En cours)
- 🟡 Recommandations ML
- 🟡 Allocation optimale (MPT)
- 🟡 Backtesting stratégies
- 🟡 Performance cache

### Phase 3: Intégrations (📅 Planifié)
- 📅 Import données brokers
- 📅 Sync API bancaires
- 📅 Alertes temps réel
- 📅 Collaboration portefeuille

### Phase 4: Analytics (📅 Futur)
- 📅 Graphs avancés
- 📅 Rapports détaillés
- 📅 Risk analytics
- 📅 Dashboard mobile

[📚 Roadmap technique détaillée →](./docs/ROADMAP.md)

---

## 📚 Documentation Complète

### Pour les Utilisateurs
| Document | Contenu |
|----------|---------|
| 📖 [Concepts Fondamentaux](./docs/CONCEPTS_FONDAMENTAUX.md) | Comprendre les principes |
| 🌐 [Interface Web](./docs/INTERFACE_WEB.md) | Tour complet de l'appli |
| 📐 [Calculs & Formules](./docs/FORMULES_CALCULS.md) | Mathématiques appliquées |
| 🗄️ [Base de Données](./docs/BASE_DONNEES.md) | Structure des données |

### Pour les Développeurs
| Document | Contenu |
|----------|---------|
| 💻 [Installation Dev](./INSTALLATION_GUIDE_DEV.md) | Setup local complet |
| ⌨️ [CLI Guide](./docs/CLI_GUIDE.md) | Commandes disponibles |
| 📋 [Architecture](./DOCUMENTATION_TECHNIQUE.md) | Structure technique |
| 🗺️ [Roadmap](./docs/ROADMAP.md) | Évolutions prévues |

---

## 🔗 Liens Rapides

| Lien | Description |
|------|-------------|
| 🌐 [Application Web](https://finance-tracker-skohscripts.streamlit.app/) | **Utiliser l'app** |
| 💻 [GitHub](https://github.com/SKOHscripts/finance-tracker) | Voir le code |
| 📧 [Issues](https://github.com/SKOHscripts/finance-tracker/issues) | Rapporter un bug |
| 🤝 [Discussions](https://github.com/SKOHscripts/finance-tracker/discussions) | Idées & Questions |

---

## 📄 Licence

Ce projet est sous licence **MIT**. Consultez le fichier [LICENSE](./LICENSE) pour plus de détails.

---

## 💬 Support & Questions

### ❓ Questions?

1. **Consultez la FAQ** dans l'application → Page "📖 Documentation" → Onglet "🆘 Help & Support"

2. **Parcourez la documentation** pour votre cas d'usage

3. **Ouvrez une Discussion** sur GitHub si vous avez une question générale

4. **Créez une Issue** si vous avez trouvé un bug

### 🐛 Bug Report?

Créez une [Issue GitHub](https://github.com/SKOHscripts/finance-tracker/issues) avec:
- Description claire du problème
- Étapes pour reproduire
- Version de l'app
- Captures d'écran si pertinent

### 💡 Suggestion?

Utilisez [Discussions GitHub](https://github.com/SKOHscripts/finance-tracker/discussions) pour:
- Proposer une fonctionnalité
- Demander une amélioration
- Discuter de l'architecture

---

## 🙏 Remerciements

Merci à:
- **Streamlit** pour l'excellent framework
- **SQLModel** et **Pydantic** pour la validation de données
- **CoinGecko** pour les données Bitcoin
- **Tous les contributeurs** pour améliorations et corrections

---

## 📊 Statistiques

| Métrique | Valeur |
|----------|--------|
| Python Version | 3.11+ |
| License | MIT |
| Last Updated | 2026 |
| Contributors | 🤝 Contribution Ouverte |

---

**Dernière mise à jour: 28/02/2026** ✨

**[🌐 Accédez à l'application →](https://finance-tracker-skohscripts.streamlit.app/)**
