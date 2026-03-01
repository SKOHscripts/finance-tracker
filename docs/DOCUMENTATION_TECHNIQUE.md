# 🔧 Documentation Technique - Finance Tracker

> Guide complet pour développeurs, architectes et contributeurs

---

## 📑 Table des Matières

1. [Architecture Générale](#-architecture-générale)
2. [Structure du Projet](#-structure-du-projet)
3. [Concepts Fondamentaux](#-concepts-fondamentaux)
4. [Base de Données](#-base-de-données)
5. [Formules & Calculs](#-formules--calculs)
6. [Interface Web (Streamlit)](#-interface-web-streamlit)
7. [Interface CLI](#-interface-cli)
8. [Setup Développeur](#-setup-développeur)
9. [Roadmap Technique](#-roadmap-technique)

---

## 🏗️ Architecture Générale

### Diagramme Global

```
┌─────────────────────────────────────────────────┐
│          Utilisateur Final                       │
│     (Web GUI ou Terminal)                        │
└────────────────┬────────────────────────────────┘
                 │
         ┌───────┴───────┐
         │               │
    ┌────▼────┐    ┌────▼────┐
    │ Streamlit│    │   CLI   │
    │  (Web)   │    │ (Term)  │
    └────┬────┘    └────┬────┘
         │               │
    ┌────▼───────────────▼────┐
    │   Services Layer        │
    │  (Business Logic)       │
    │  - PortfolioService     │
    │  - CalculationEngine    │
    │  - TransactionService   │
    └────┬───────────────────┘
         │
    ┌────▼───────────────────┐
    │   Repository Layer      │
    │  (Data Access)         │
    │  - SQLModelRepository   │
    │  - Queries & ORM        │
    └────┬───────────────────┘
         │
    ┌────▼───────────────────┐
    │   Data Layer            │
    │  SQLite Database        │
    │  (Local File)           │
    └────────────────────────┘
```

### Principes Architecturaux

- **Couches séparées** - UI / Services / Repositories / Data
- **Pas de logique métier en UI** - Tous les calculs dans Services
- **Repos pattern** - Abstraction de la base de données
- **Stateless services** - Pas de state global persistant
- **Testing-friendly** - Dépendances injectables

---

## 📂 Structure du Projet

```
finance-tracker/
├── README.md                          ← Pour utilisateurs finaux
├── DOCUMENTATION_TECHNIQUE.md         ← Ce fichier
│
├── app.py                             ← Point d'entrée Streamlit
│
├── pyproject.toml                     ← Config dépendances (Poetry)
├── requirements.txt                   ← Dépendances pip
│
├── finance_tracker/                   ← Package principal
│   │
│   ├── web/                           ← Interface Streamlit
│   │   ├── __init__.py
│   │   ├── app.py                    ← Configuration Streamlit
│   │   ├── db.py                     ← Gestion sessions DB
│   │   ├── navigation.py             ← Système navigation pages
│   │   │
│   │   └── views/                    ← Pages Streamlit (render functions)
│   │       ├── dashboard.py          ← Page Tableau de Bord
│   │       ├── documentation.py      ← Page Documentation (NEW)
│   │       ├── products.py           ← Gestion produits
│   │       ├── transactions.py       ← Gestion transactions
│   │       ├── valuations.py         ← Gestion valorisations
│   │       ├── bitcoin.py            ← Suivi Bitcoin
│   │       ├── simulation.py         ← Simulator intérêts composés
│   │       └── reports.py            ← Génération PDF
│   │
│   ├── cli/                           ← Interface Terminal
│   │   ├── __init__.py
│   │   ├── main.py                  ← Entry point CLI (Click)
│   │   ├── commands/
│   │   │   ├── dashboard.py
│   │   │   ├── products.py
│   │   │   ├── transactions.py
│   │   │   ├── valuations.py
│   │   │   └── ...
│   │   └── formatters.py            ← Output formatting
│   │
│   ├── core/                          ← Logique métier pure
│   │   ├── __init__.py
│   │   └── models.py                ← Modèles de données (SQLModel)
│   │       ├── Product
│   │       ├── Transaction
│   │       ├── Valuation
│   │       └── ...
│   │
│   ├── services/                      ← Services métier
│   │   ├── __init__.py
│   │   ├── portfolio_service.py      ← Calculs portefeuille
│   │   ├── calculation_engine.py     ← Moteur de calcul
│   │   ├── transaction_service.py    ← Logique transactions
│   │   ├── product_service.py        ← Logique produits
│   │   ├── valuation_service.py      ← Logique valorisations
│   │   ├── bitcoin_service.py        ← Intégration CoinGecko
│   │   └── export_service.py         ← Export/import données
│   │
│   ├── repositories/                  ← Couche données
│   │   ├── __init__.py
│   │   ├── base_repository.py        ← Classe de base
│   │   ├── sqlmodel_repo.py          ← Implémentation SQLModel
│   │   ├── queries.py                ← Requêtes SQL courantes
│   │   └── migrations.py             ← Gestion schema
│   │
│   └── utils/                         ← Utilitaires
│       ├── __init__.py
│       ├── formatting.py             ← Formatage nombres/devises
│       ├── dates.py                  ← Utilitaires dates
│       ├── validation.py             ← Validation inputs
│       ├── constants.py              ← Constantes app
│       └── exceptions.py             ← Exceptions custom
│
├── tests/                             ← Suite de tests
│   ├── test_calculation_engine.py
│   ├── test_services.py
│   ├── test_models.py
│   └── fixtures.py
│
├── docs/                              ← Documentation utilisateur
│   ├── CONCEPTS_FONDAMENTAUX.md
│   ├── INTERFACE_WEB.md
│   ├── CLI_GUIDE.md
│   ├── FORMULES_CALCULS.md
│   ├── BASE_DONNEES.md
│   ├── INSTALLATION_SETUP.md
│   ├── ROADMAP.md
│   └── INDEX_COMPLET.md
│
└── .env.example                       ← Variables d'environnement
```

---

## 🎯 Concepts Fondamentaux

### Modèles de Données (SQLModel)

```python
# models.py

class Product(SQLModel, table=True):
    """Représente un actif (SCPI, Bitcoin, Livret, etc.)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str                           # Nom du produit
    type: str                          # SCPI, CRYPTO, LIVRET, FONDS, AUTRE
    currency: str                      # EUR, USD, BTC, ETH, etc.
    created_at: datetime
    updated_at: datetime

    # Relationship
    transactions: List["Transaction"] = Relationship(back_populates="product")
    valuations: List["Valuation"] = Relationship(back_populates="product")


class Transaction(SQLModel, table=True):
    """Enregistre un mouvement financier"""
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    transaction_type: str               # DEPOSIT, WITHDRAWAL, GAIN, DIVIDEND, FEE, SPLIT
    amount: Decimal                    # Montant en devise du produit
    quantity: Optional[Decimal]        # Quantité (pour actions, BTC, etc.)
    date: datetime
    description: Optional[str]

    # Relationship
    product: Product = Relationship(back_populates="transactions")


class Valuation(SQLModel, table=True):
    """Capture la valeur d'un produit à une date"""
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    value: Decimal                     # Valeur totale actuelle
    quantity: Optional[Decimal]        # Quantité associée
    date: datetime

    # Relationship
    product: Product = Relationship(back_populates="valuations")
```

### Services - Couche Métier

```python
# services/calculation_engine.py

class CalculationEngine:
    """Moteur de calcul de tous les indicateurs financiers"""

    @staticmethod
    def calculate_invested_amount(transactions: List[Transaction]) -> Decimal:
        """
        Investissement Net = DEPOSIT - WITHDRAWAL - GAIN + FEE
        (excluant les dividendes qui sont des revenus)
        """
        total = Decimal(0)
        for txn in transactions:
            if txn.type == TransactionType.DEPOSIT:
                total += txn.amount
            elif txn.type == TransactionType.WITHDRAWAL:
                total -= txn.amount
            elif txn.type == TransactionType.GAIN:
                total -= txn.amount  # Réduction de capital
            elif txn.type == TransactionType.FEE:
                total -= txn.amount
        return total

    @staticmethod
    def calculate_pru(transactions: List[Transaction],
                     quantity_filter: Optional[Decimal] = None) -> Decimal:
        """
        Prix de Revient Unitaire = Investissement Net / Quantité Totale
        """
        invested = CalculationEngine.calculate_invested_amount(transactions)
        quantity = CalculationEngine.calculate_total_quantity(transactions)

        if quantity == 0:
            return Decimal(0)
        return invested / quantity

    @staticmethod
    def calculate_performance(current_value: Decimal,
                            invested_amount: Decimal) -> Decimal:
        """
        Performance € = Valeur Actuelle - Investissement Net
        Performance % = (Performance € / Investissement Net) × 100
        """
        if invested_amount == 0:
            return Decimal(0)
        return ((current_value - invested_amount) / invested_amount) * 100
```

### Repositories - Couche Données

```python
# repositories/sqlmodel_repo.py

class SQLModelRepository:
    """Abstraction d'accès aux données via SQLModel"""

    def __init__(self, engine):
        self.engine = engine

    def get_all_products(self) -> List[Product]:
        """Récupère tous les produits"""
        with Session(self.engine) as session:
            return session.query(Product).all()

    def get_product_with_transactions(self, product_id: int) -> Optional[Product]:
        """Récupère un produit avec toutes ses transactions"""
        with Session(self.engine) as session:
            return session.query(Product).options(
                selectinload(Product.transactions)
            ).filter(Product.id == product_id).first()

    def create_transaction(self, txn: Transaction) -> Transaction:
        """Crée une nouvelle transaction"""
        with Session(self.engine) as session:
            session.add(txn)
            session.commit()
            session.refresh(txn)
            return txn
```

---

## 🗄️ Base de Données

### Schéma SQLite

```sql
-- products table
CREATE TABLE product (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('SCPI', 'CRYPTO', 'LIVRET', 'FONDS', 'AUTRE')),
    currency TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name)
);

-- transactions table
CREATE TABLE transaction (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN
        ('DEPOSIT', 'WITHDRAWAL', 'GAIN', 'DIVIDEND', 'FEE', 'SPLIT')),
    amount DECIMAL NOT NULL,
    quantity DECIMAL,
    date TIMESTAMP NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- valuations table
CREATE TABLE valuation (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    value DECIMAL NOT NULL,
    quantity DECIMAL,
    date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices pour optimisation
CREATE INDEX idx_transaction_product_id ON transaction(product_id);
CREATE INDEX idx_transaction_date ON transaction(date);
CREATE INDEX idx_valuation_product_id ON valuation(product_id);
CREATE INDEX idx_valuation_date ON valuation(date);
```

### Requêtes Courantes

```python
# Dernier investissement net par produit
SELECT
    p.id,
    p.name,
    SUM(CASE
        WHEN t.transaction_type = 'DEPOSIT' THEN t.amount
        WHEN t.transaction_type = 'WITHDRAWAL' THEN -t.amount
        WHEN t.transaction_type = 'GAIN' THEN -t.amount
        WHEN t.transaction_type = 'FEE' THEN -t.amount
        ELSE 0
    END) as invested_net
FROM product p
LEFT JOIN transaction t ON p.id = t.product_id
GROUP BY p.id;

# Dernière valorisation de chaque produit
SELECT DISTINCT ON (p.id)
    p.id, p.name, v.value, v.date
FROM product p
LEFT JOIN valuation v ON p.id = v.product_id
ORDER BY p.id, v.date DESC;
```

---

## 🧮 Formules & Calculs

### Investissement Net

```
Investissement Net = Σ(DEPOSIT) - Σ(WITHDRAWAL) - Σ(GAIN) - Σ(FEE)
```

Exclut les DIVIDEND car ce sont des revenus (plus-values non réalisées).

### PRU (Prix de Revient Unitaire)

```
PRU = Investissement Net / Quantité Totale

Quantité Totale = Σ(DEPOSIT.quantity) - Σ(WITHDRAWAL.quantity) - Σ(GAIN.quantity)
```

### Performance

```
Performance € = Valeur Actuelle - Investissement Net

Performance % = (Performance € / Investissement Net) × 100

Exemple:
- Investi: 10 000€
- Valeur actuelle: 11 500€
- Performance €: 1 500€
- Performance %: 15%
```

### Gain Latent vs Réalisé

```
Gain Latent = (Dernière Valuation - Investissement Net) [non vendu]

Gain Réalisé = Σ(GAIN.amount) [vendu et comptabilisé]

Gain Total = Gain Latent + Gain Réalisé
```

### Intérêts Composés

```
V(n) = V0 × (1 + r)^n + V_monthly × [((1 + r)^n - 1) / r]

Où:
- V(n) = Valeur après n périodes
- V0 = Investissement initial
- r = Taux de rendement par période
- V_monthly = Versement mensuel
- n = Nombre de périodes
```

### Cas Bitcoin

Bitcoin est suivi en temps réel via API CoinGecko :

```
Valeur BTC € = Quantité BTC × Prix BTC/EUR (actuel)

PRU BTC = Σ(Cost in EUR) / Quantité totale BTC
```

---

## 💻 Interface Web (Streamlit)

### Structure Navigation

```python
# navigation.py
@dataclass(frozen=True)
class Page:
    label: str                          # Affiché en UI
    render: Callable[[Session], None]   # Fonction de rendu

def build_pages() -> list[Page]:
    return [
        Page("📖 Documentation", doc_render),     # Premier !
        Page("--- Analyses ---", None),           # Titre section
        Page("📊 Tableau de Bord", dashboard_render),
        Page("📈 Simulation", simulation_render),
        # ...
    ]
```

### Création d'une Nouvelle Page

1. **Créer la fonction render:**

```python
# views/my_page.py
import streamlit as st
from sqlmodel import Session

def render(session: Session) -> None:
    st.title("Ma Nouvelle Page")

    # Logique métier via services
    from finance_tracker.services.portfolio_service import PortfolioService

    portfolio = PortfolioService(session)
    stats = portfolio.get_portfolio_stats()

    # Affichage Streamlit
    st.metric("Valeur Portefeuille", f"{stats.total_value:.2f}€")
    st.bar_chart(stats.allocation_data)
```

2. **Enregistrer dans navigation.py:**

```python
from finance_tracker.web.views.my_page import render as my_page_render

def build_pages():
    return [
        # ...
        Page("🆕 Ma Page", my_page_render),
    ]
```

### Intégration Documentation dans Streamlit

```python
# views/documentation.py
import streamlit as st
import os

def render(session: Session) -> None:
    st.title("📖 Documentation")

    tab1, tab2, tab3, tab4 = st.tabs([
        "👋 Accueil",
        "📚 Concepts",
        "📐 Calculs",
        "🗄️ Base de Données"
    ])

    docs_path = os.path.join(
        os.path.dirname(__file__),
        "../../../docs"
    )

    with tab1:
        # Charger README.md
        with open("README.md", "r", encoding="utf-8") as f:
            st.markdown(f.read())

    with tab2:
        # Charger CONCEPTS_FONDAMENTAUX.md
        with open(
            os.path.join(docs_path, "CONCEPTS_FONDAMENTAUX.md"),
            "r", encoding="utf-8"
        ) as f:
            st.markdown(f.read())

    # ... autres onglets
```

### Patterns Streamlit Courants

```python
# Formulaire avec validation
with st.form("add_transaction"):
    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input("Montant", min_value=0.0)
    with col2:
        txn_type = st.selectbox("Type", ["DEPOSIT", "WITHDRAWAL", "GAIN"])

    if st.form_submit_button("Ajouter"):
        if amount <= 0:
            st.error("Montant doit être > 0")
        else:
            # Appel service
            TransactionService.create(session, ...)
            st.success("Transaction ajoutée!")
            st.rerun()

# Affichage données
products = repository.get_all_products()
df = pd.DataFrame([
    {
        "Nom": p.name,
        "Type": p.type,
        "Prix": f"{p.current_price:.2f}€"
    }
    for p in products
])
st.dataframe(df, use_container_width=True)

# Graphiques
st.line_chart(performance_data)
st.bar_chart(allocation_data)
st.pie_chart(asset_distribution)
```

---

## 🖥️ Interface CLI

### Structure

```bash
# Main entry point
python -m finance_tracker.cli.main [COMMAND] [OPTIONS]

# Exemples
python -m finance_tracker.cli.main dashboard
python -m finance_tracker.cli.main product list
python -m finance_tracker.cli.main transaction add --product-id 1 --amount 1000
```

### Implémenter une Commande CLI

```python
# cli/commands/my_command.py
import click
from sqlmodel import Session
from finance_tracker.services import MyService

@click.group()
def my_group():
    """Groupe de commandes"""
    pass

@my_group.command()
@click.option('--param', required=True, help='Description')
def my_command(param):
    """Description de ma commande"""
    session = get_session()
    service = MyService(session)

    result = service.do_something(param)

    click.echo(f"Résultat: {result}")
```

### Enregistrer dans main.py

```python
# cli/main.py
import click
from finance_tracker.cli.commands.my_command import my_group

@click.group()
def cli():
    pass

cli.add_command(my_group, name="my_group")

if __name__ == "__main__":
    cli()
```

---

## 🔨 Setup Développeur

### 1. Installation Environnement

```bash
# Cloner repo
git clone https://github.com/SKOHscripts/finance-tracker.git
cd finance-tracker

# Créer venv
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows

# Installer dépendances dev
pip install -e ".[dev]"
# ou avec Poetry
poetry install --with dev
```

### 2. Dépendances Clés

```toml
# pyproject.toml
[project]
dependencies = [
    "sqlmodel>=0.0.8",           # ORM & validation
    "streamlit>=1.28",           # Web UI
    "click>=8.1",                # CLI
    "requests>=2.31",            # HTTP requests
    "pandas>=2.0",               # Data manipulation
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black>=23.0",
    "flake8>=6.0",
    "mypy>=1.0",
    "pytest-cov>=4.0",
]
```

### 3. Lancer en Développement

```bash
# Web
streamlit run app.py --logger.level=debug

# CLI
python -m finance_tracker.cli.main dashboard

# Tests
pytest tests/ -v
pytest tests/ --cov=finance_tracker
```

### 4. Code Style

```bash
# Formater
black finance_tracker/

# Lint
flake8 finance_tracker/

# Type checking
mypy finance_tracker/
```

---

## 🚀 Roadmap Technique

### V1.0.0 (Actuelle) ✅
- ✅ CRUD complet produits/transactions/valorisations
- ✅ Calculs financiers (PRU, performance, gains)
- ✅ Dashboard Streamlit
- ✅ Suivi Bitcoin temps réel
- ✅ Export PDF
- ✅ CLI basique

### V2.0.0
- 📋 Import CSV historique
- 📊 Calculs TRI/XIRR
- 🔗 Intégration APIs brokers (Interactive Brokers, Degiro)
- 📈 Alertes performance
- 🎯 Recommandations allocation

### V3.0.0
- 👥 Multi-portefeuilles
- 🏛️ Gestion fiscalité (Plus/moins values)
- 📊 Rapports fiscaux PDF
- 🤖 Suggestions intelligentes
- 📱 App mobile (React Native)

### V4.0.0
- 🌐 Plateforme complète (multi-users)
- 🔐 Authentification OAuth
- ☁️ Sync cloud optionnel (AWS)
- 📊 Analytics avancées
- 🔌 Marketplace extensions

---

## 🧪 Tests

### Structure Tests

```python
# tests/test_calculation_engine.py
import pytest
from decimal import Decimal
from finance_tracker.services.calculation_engine import CalculationEngine
from finance_tracker.core.models import Transaction, TransactionType

def test_calculate_invested_amount():
    """Test calcul investissement net"""
    transactions = [
        Transaction(type=TransactionType.DEPOSIT, amount=Decimal(1000)),
        Transaction(type=TransactionType.WITHDRAWAL, amount=Decimal(100)),
        Transaction(type=TransactionType.DIVIDEND, amount=Decimal(50)),
    ]

    result = CalculationEngine.calculate_invested_amount(transactions)

    # DEPOSIT - WITHDRAWAL (DIVIDEND n'est pas inclus)
    assert result == Decimal(900)

def test_calculate_pru():
    """Test calcul PRU"""
    transactions = [
        Transaction(amount=Decimal(1000), quantity=Decimal(10)),
    ]

    result = CalculationEngine.calculate_pru(transactions)

    assert result == Decimal(100)  # 1000 / 10
```

### Lancer Tests

```bash
# Tous les tests
pytest

# Avec coverage
pytest --cov=finance_tracker

# Test spécifique
pytest tests/test_calculation_engine.py::test_calculate_pru -v

# Watch mode
pytest-watch
```

---

## 🔐 Sécurité & Bonnes Pratiques

### Validation Input

```python
# Toujours valider en Services/Repositories
from finance_tracker.utils.validation import validate_amount

def create_transaction(self, amount: Decimal, ...):
    if not validate_amount(amount):
        raise ValueError("Invalid amount")
    # ...
```

### Gestion Erreurs

```python
from finance_tracker.utils.exceptions import AppException

try:
    product = repository.get_product(product_id)
except ProductNotFound:
    st.error(f"Produit {product_id} introuvable")
except DatabaseError as e:
    st.error(f"Erreur base de données: {e}")
```

### Variables d'Environnement

```bash
# .env.example
DATABASE_URL=sqlite:///./finance_tracker.db
COINGECKO_API_KEY=
LOG_LEVEL=INFO
```

```python
# core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./finance_tracker.db"
    coingecko_api_key: Optional[str] = None
    log_level: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 📖 Ressources

- 📚 [SQLModel Docs](https://sqlmodel.tiangolo.com)
- 🎯 [Streamlit Docs](https://docs.streamlit.io)
- 🖥️ [Click CLI Docs](https://click.palletsprojects.com)
- 🧪 [Pytest Docs](https://docs.pytest.org)
