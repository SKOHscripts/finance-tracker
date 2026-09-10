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
- [📡 Signal Crypto & Portefeuilles](#-signal-crypto--portefeuilles)
- [📚 Documentation Spécialisée](#-documentation-spécialisée)
  - [Concepts fondamentaux](#concepts-fondamentaux)
  - [Interface web](#interface-web)
  - [Signal crypto](#signal-crypto)
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
- Suivre ses **portefeuilles crypto** depuis une simple adresse publique, avec récupération automatique des soldes et reconstitution du prix de revient.
- Obtenir un **signal de rotation crypto** : des règles écrites à l'avance, appliquées à des métriques passées, qui proposent — ou refusent — un swap.
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

- **📡 Signal Crypto**
  Arbitrage de chaque position crypto contre le classement du marché, sur six barrières explicites. Cinq verdicts possibles, avec le chiffre qui a fait passer ou échouer chaque barrière. Chaque figure dont le moteur se sert est corrigeable à la main, à l'endroit même où elle s'affiche — et les 36 seuils qui décident d'un mouvement sont réglables, chacun avec la phrase qui dit ce qu'il change. ⚠️ *Outil éducatif, pas un conseil en investissement.*

- **👛 Portefeuilles Crypto**
  Suivi d'adresses publiques sur Bitcoin, Solana et les chaînes EVM (Ethereum, Base, Arbitrum, Optimism, Polygon, BSC). Soldes récupérés automatiquement, prix de revient reconstitué depuis l'historique on-chain — avec son indice de confiance. Et pour ce qu'aucune adresse ne peut révéler — Monero, un solde d'échange, un avoir gardé au froid — une saisie à la main : la cotation se cherche par nom ou par symbole, la quantité et le prix de revient s'entrent une fois.

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

## 📡 Signal Crypto & Portefeuilles

> ⚠️ **Ceci n'est pas un conseil en investissement.** Finance Tracker n'est ni
> conseiller en investissement, ni intermédiaire financier, et n'est enregistré
> auprès d'aucune autorité de marché. Le signal applique des règles écrites à
> l'avance à des métriques **passées** : il ne prédit aucun prix et n'exécute
> rien. Les crypto-actifs sont extrêmement volatils et vous pouvez perdre la
> totalité de votre mise.
> 👉 **[Lire l'avertissement complet](./docs/DISCLAIMER.md)**

### Ce que fait le signal

Chaque position crypto est arbitrée **indépendamment des autres**, avec son
propre montant et donc son propre coût de mouvement. Quatre mécanismes, dans un
ordre de priorité fixe :

| Priorité | Mécanisme | Ce qu'il fait |
|---|---|---|
| 1 | **Stop suiveur** | Sort une ligne en gain qui a décroché de plus de 30 % de son plus haut |
| 2 | **Prise de bénéfice** | Récupère la mise, une fois, au-delà de 100 % de plus-value |
| 3 | **Rotation** | Swap vers le candidat du classement, si six barrières passent |
| 4 | **Temporisation** | Aller simple vers un stablecoin quand le marché est mesurablement dégradé |

Protéger le capital passe avant d'encaisser ; encaisser passe avant de courir
après un autre actif.

Une barrière de **persistance** exige que les conditions tiennent trois scans
consécutifs. La première semaine ne produit donc jamais de mouvement, quelle que
soit la force apparente du signal. C'est le but.

### Suivi automatique des portefeuilles

| Chaîne | Soldes | Historique et prix de revient | Clé nécessaire |
|---|---|---|---|
| Ethereum, Base, Arbitrum, Optimism, Polygon, BSC | ✅ | ✅ | Clé d'explorateur gratuite, apportée par l'utilisateur |
| Bitcoin | ✅ | ✅ | Aucune |
| Solana | ✅ | ❌ (saisie manuelle) | Aucune |
| Monero | ❌ | ❌ | *Impossible depuis une adresse seule — saisie à la main* |

**Deux limites, dites franchement.** Une chaîne enregistre des mouvements,
jamais un prix d'achat : tout prix de revient reconstitué est une **estimation**,
affichée avec sa part non expliquée et son indice de confiance, et corrigeable à
la main — votre valeur gagne toujours. Et interroger un indexeur **révèle votre
adresse** à celui qui l'exploite : la synchronisation s'active portefeuille par
portefeuille, et vous pouvez pointer l'outil vers votre propre nœud.

### En ligne de commande

```bash
finance-tracker crypto-positions   # ce qui sera arbitré, et d'où viennent les chiffres
finance-tracker crypto-scan        # lancer un scan
finance-tracker crypto-history     # relire les scans passés
finance-tracker wallet-sync        # synchroniser les adresses suivies
```

👉 Détails : **[docs/CRYPTO_SIGNAL.md](./docs/CRYPTO_SIGNAL.md)**

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

### Signal crypto

Les cinq verdicts, les quatre mécanismes, le calcul du score, le coût réel d'un
swap, le suivi de portefeuilles et la reconstitution du prix de revient.

- 👉 **[docs/CRYPTO_SIGNAL.md](./docs/CRYPTO_SIGNAL.md)**
- ⚠️ **[docs/DISCLAIMER.md](./docs/DISCLAIMER.md)** — portée et limites

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
