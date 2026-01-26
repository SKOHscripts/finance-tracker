# Finance Tracker v0.1.0

Outil de suivi de portefeuille d'investissement personnel en Python. Gère SCPI, Bitcoin, assurance vie, PER, épargne, et liquidités avec historique de transactions, valorisations, projections et rapports PDF.

## 🎯 Caractéristiques

- ✅ Suivi multi-produits : SCPI (parts), Bitcoin (satoshis), épargne (EUR), assurance vie, PER, FCPI, liquidités
- ✅ Historique complet : dépôts, retraits, distributions, frais, achats/ventes
- ✅ Valorisations snapshots (prix BTC/EUR à la demande via CoinGecko)
- ✅ Dashboard CLI avec JSON export
- ✅ Projections rendement composé (mensuel/trimestriel/annuel)
- ✅ Génération PDF rapport (valeur totale, allocation, perfs)
- ✅ Comptes d'épargne avec taux ajustables dans le temps
- ✅ Documentation produits (markdown généré)
- ✅ SQLite local, code propre (type hints, Decimal pour l'argent)

## 📦 Installation

### Prérequis
- Python 3.11+
- pip/venv

### Setup

```bash
git clone <repo>
cd finance-tracker

# Créer venv
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou: venv\Scripts\activate (Windows)

# Installer (mode dev recommandé)
pip install -e ".[dev]"

# Initialiser la base de données
finance-tracker init-db

# Créer les produits par défaut
finance-tracker seed-products

# (Optionnel) installer dépendances PDF
# WeasyPrint peut demander libpango/libcairo selon système
# Ubuntu: sudo apt-get install python3-dev libpango-1.0-0 libpango1.0-dev libcairo2 libcairo2-dev
```

## 🚀 Utilisation rapide

### 1. Ajouter une transaction (dépôt cash)

```bash
finance-tracker add-transaction \
  --product-name "Cash" \
  --type "DEPOSIT" \
  --amount 5000 \
  --date "2025-01-26" \
  --note "Dépôt initial"
```

### 2. Ajouter une valorisation SCPI

```bash
finance-tracker add-valuation \
  --product-name "SCPI" \
  --total-value-eur 12000 \
  --unit-price-eur 250 \
  --date "2025-01-26"
```

### 3. Récupérer le prix BTC en EUR et créer valorisation

```bash
finance-tracker update-btc
```

### 4. Afficher le dashboard

```bash
finance-tracker dashboard

# Ou en JSON pour traitement
finance-tracker dashboard --json > dashboard.json
```

### 5. Projeter un placement SCPI

```bash
finance-tracker project \
  --product-type "SCPI" \
  --initial-amount 10000 \
  --monthly-contribution 500 \
  --annual-return 0.045 \
  --years 10
```

### 6. Générer la documentation des produits

```bash
finance-tracker product-doc
# Crée docs/products.md
```

### 7. Exporter un PDF

```bash
finance-tracker export-pdf
# Crée reports/report_2025-01-26_095430.pdf
```

## 📊 Structure de la base de données

### Produits (Products)
- `id` : int PK
- `name` : str unique (Cash, SCPI, BTC, Épargne, etc.)
- `type` : enum (CASH, SCPI, BITCOIN, SAVINGS, INSURANCE, PER, FCPI)
- `quantity_unit` : enum (NONE, SCPI_SHARES, BTC_SATS)
- `description` : str (texte libre pour doc)
- `risk_level` : str (Très faible, Faible, Modéré, Élevé)
- `fees_description` : str (frais si pertinent)
- `tax_info` : str (spécificités fiscales)
- `created_at` : datetime

### Transactions (Transactions)
- `id` : int PK
- `product_id` : int FK
- `date` : date
- `type` : enum (DEPOSIT, WITHDRAW, FEE, DISTRIBUTION, BUY, SELL, INTEREST)
- `amount_eur` : Decimal (optionnel, pour montants EUR)
- `quantity` : Decimal (optionnel, parts/sats selon produit)
- `note` : str
- `created_at` : datetime

### Valorisations (Valuations)
- `id` : int PK
- `product_id` : int FK
- `date` : date
- `total_value_eur` : Decimal
- `unit_price_eur` : Decimal | None (utile SCPI/BTC)
- `created_at` : datetime

### Taux d'épargne (RateSchedules)
- `id` : int PK
- `product_id` : int FK (référence produit SAVINGS)
- `date_effective` : date
- `annual_rate` : Decimal (ex: 0.03 pour 3%)
- `created_at` : datetime

## 📝 Modèle de données

Les modèles utilisent **SQLModel** : classe unique = table + validation Pydantic.

Exemple SCPI (parts) :
```
Product(name="SCPI", type=SCPI, quantity_unit=SCPI_SHARES)
Transaction(product=SCPI, type=BUY, amount_eur=10000, quantity=40) 
  → 40 parts à 250€ chacune
Valuation(product=SCPI, date=today, total_value_eur=12000, unit_price_eur=260)
  → 40 parts × 260€ = 10400€
```

Exemple Bitcoin (satoshis) :
```
Product(name="Bitcoin", type=BITCOIN, quantity_unit=BTC_SATS)
Transaction(product=BTC, type=BUY, amount_eur=500, quantity=1500000)
  → 1.5M sats à ~333 satoshi/EUR
Valuation(product=BTC, date=today, total_value_eur=510, unit_price_eur=34000)
  → Prix BTC/EUR = 34000, quantité = 1.5M sats → valeur ~510€
```

## 🧮 Performance v1

Le dashboard calcule :

1. **Valeur actuelle** : dernière valorisation par produit
2. **Somme contributions** : DEPOSIT - WITHDRAW par produit
3. **Performance** : `perf_eur = valeur_actuelle - contributions_nettes`
4. **Perf %** : `perf_pct = perf_eur / abs(contributions_nettes) * 100` (si > 0)
5. **Allocation %** : `value / total_portfolio * 100`

⚠️ *Limites v1* : ne tient pas compte des DISTRIBUTION réinvesties, du timing des CF. À améliorer en v2 avec TRI/XIRR.

## 🔧 Développement

### Lint + Format

```bash
# Format code
black finance_tracker tests

# Lint
ruff check finance_tracker tests --fix

# Type check
mypy finance_tracker
```

### Tests

```bash
pytest tests/ -v

# Avec couverture
pytest tests/ --cov=finance_tracker --cov-report=html
```

### Ajouter un produit custom

Éditer `finance_tracker/cli.py`, fonction `seed_products()` :

```python
Product(
    name="Mon PEA",
    type=ProductType.SAVINGS,
    quantity_unit=QuantityUnit.NONE,
    description="Plan d'épargne en actions...",
    risk_level="Modéré",
)
```

## 📋 Roadmap

**v0.1.0 (current)** :
- [x] Modèles domaine
- [x] Repos SQLite
- [x] CLI de base
- [x] Dashboard simple
- [x] Projections composées
- [x] Récupération BTC/EUR
- [x] Export PDF
- [x] Tests

**v0.2.0 (proposé)** :
- [ ] TRI/XIRR pour perfs
- [ ] Web UI (Django/FastAPI)
- [ ] Budget / allocations cibles
- [ ] Alertes fiscalité
- [ ] Import CSV
- [ ] Graphiques tendance
- [ ] Synchronisation API courtiers

## 📞 Support

Issues : GitHub
Docs complètes : `docs/products.md` (généré après `product-doc`)

---

**Licence** : MIT  
**Auteur** : Finance Tracker Contributors  
**Python** : 3.11+
