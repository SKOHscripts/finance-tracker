# ⌨️ Guide CLI (Command Line Interface)

> Utiliser Finance Tracker depuis le terminal avec Typer

---

## 🎯 Introduction

La CLI (Command Line Interface) permet de contrôler Finance Tracker entièrement depuis votre terminal sans interface graphique. Parfait pour l'automatisation, les scripts et l'utilisation serveur.

**Commandement principal:**
```bash
finance-tracker [COMMANDE] [OPTIONS]
```

---

## 🚀 Commandes Disponibles

### 1️⃣ **Initialisation & Configuration**

#### `init-db`
Initialise la base de données SQLite.

```bash
finance-tracker init-db
```

**Output:**
```
✓ Base de données initialisée à: ./finance_tracker.db
✓ Tables créées: products, transactions, valuations
```

**Quand l'utiliser:**
- Première utilisation
- Réinitialisation complète (attention: supprime les données)

---

#### `seed-products`
Ajoute les produits de base prédéfinis.

```bash
finance-tracker seed-products
```

**Produits ajoutés:**
```
1. Cash Account (Cash)
2. SCPI Eurizon (SCPI)
3. Bitcoin (Crypto)
4. Livret A (Cash)
5. Assurance Vie (Insurance)
6. PER (PER)
```

**Quand l'utiliser:**
- Après `init-db` pour démarrer
- Pour tester rapidement

---

### 2️⃣ **Ajouter des Données**

#### `add-transaction`
Enregistrer une nouvelle transaction (mouvement financier).

```bash
finance-tracker add-transaction \
  --product "SCPI Eurizon" \
  --type BUY \
  --amount 2500 \
  --quantity 10 \
  --unit-price 250 \
  --date 2024-02-15 \
  --description "Achat de 10 parts SCPI"
```

**Options:**

| Option | Type | Requis | Exemple |
|--------|------|--------|---------|
| `--product` | str | ✓ | "SCPI Eurizon" |
| `--type` | str | ✓ | BUY, SELL, DEPOSIT, WITHDRAW, DISTRIBUTION, FEE |
| `--amount` | float | ✓ | 2500.00 |
| `--quantity` | float | ✗ | 10 (pour BUY/SELL) |
| `--unit-price` | float | ✗ | 250.00 (pour BUY/SELL) |
| `--date` | str | ✓ | 2024-02-15 (format ISO) |
| `--description` | str | ✗ | "Description..." |

**Exemples de Cas d'Usage:**

```bash
# Dépôt d'argent (DEPOSIT)
finance-tracker add-transaction \
  --product "Cash Account" \
  --type DEPOSIT \
  --amount 5000 \
  --date 2024-02-15 \
  --description "Versement initial"

# Retrait (WITHDRAW)
finance-tracker add-transaction \
  --product "Cash Account" \
  --type WITHDRAW \
  --amount 500 \
  --date 2024-02-20 \
  --description "Retrait partiel"

# Achat d'actif (BUY)
finance-tracker add-transaction \
  --product "Bitcoin" \
  --type BUY \
  --quantity 2000000 \
  --unit-price 0.000475 \
  --amount 950 \
  --date 2024-02-15 \
  --description "Achat 0.02 BTC"

# Distribution reçue (DISTRIBUTION)
finance-tracker add-transaction \
  --product "SCPI Eurizon" \
  --type DISTRIBUTION \
  --amount 150 \
  --date 2024-02-28 \
  --description "Coupon semestriel"

# Frais (FEE)
finance-tracker add-transaction \
  --product "SCPI Eurizon" \
  --type FEE \
  --amount 50 \
  --date 2024-02-28 \
  --description "Frais de gestion annuels"
```

---

#### `add-valuation`
Enregistrer une nouvelle valorisation (mise à jour de prix).

```bash
finance-tracker add-valuation \
  --product "SCPI Eurizon" \
  --unit-price 262.5 \
  --date 2024-02-28 \
  --source manual
```

**Options:**

| Option | Type | Requis | Exemple |
|--------|------|--------|---------|
| `--product` | str | ✓ | "SCPI Eurizon" |
| `--unit-price` | float | ✓ | 262.50 |
| `--date` | str | ✓ | 2024-02-28 |
| `--source` | str | ✗ | manual, api |

**Exemple:**
```bash
# Mise à jour SCPI
finance-tracker add-valuation \
  --product "SCPI Eurizon" \
  --unit-price 265.00 \
  --date 2024-02-28 \
  --source manual

# Mise à jour Bitcoin (normalement auto via API)
finance-tracker add-valuation \
  --product "Bitcoin" \
  --unit-price 47500 \
  --date 2024-02-28 \
  --source api
```

---

### 3️⃣ **Consulter les Données**

#### `dashboard`
Afficher un résumé du portefeuille.

```bash
finance-tracker dashboard
```

**Output par défaut (tableau):**
```
╔════════════════════════════════════════╗
║         📊 TABLEAU DE BORD             ║
╠════════════════════════════════════════╣
║                                        ║
║  Valeur Totale:        45 000.00 EUR   ║
║  Investissement Net:   39 600.00 EUR   ║
║  Performance (€):       5 400.00 EUR   ║
║  Performance (%):          13.63 %     ║
║  Cash Disponible:       2 500.00 EUR   ║
║                                        ║
╚════════════════════════════════════════╝

ALLOCATION DU PORTEFEUILLE
─────────────────────────────
SCPI Eurizon        35%  (15 750.00 EUR)
Bitcoin             40%  (18 000.00 EUR)
Livret A            15%  (6 750.00 EUR)
Cash                 8%  (3 600.00 EUR)
```

#### `dashboard --json`
Afficher en format JSON pour intégration.

```bash
finance-tracker dashboard --json
```

**Output JSON:**
```json
{
  "portfolio_value": 45000.00,
  "invested_net": 39600.00,
  "performance_euro": 5400.00,
  "performance_percent": 13.63,
  "cash_available": 2500.00,
  "allocation": {
    "SCPI Eurizon": {
      "percent": 35.0,
      "value": 15750.00
    },
    "Bitcoin": {
      "percent": 40.0,
      "value": 18000.00
    }
  }
}
```

**Cas d'usage:**
- Intégration dans des scripts
- Envoi vers un serveur/API
- Stockage pour historique

---

#### `list-products`
Lister tous les produits.

```bash
finance-tracker list-products
```

**Output:**
```
╔════════════════════════════════════════════╗
║         📋 LISTE DES PRODUITS             ║
╠════════════════════════════════════════════╣
║                                            ║
║ ID  Nom               Type        Unité   ║
║ ─────────────────────────────────────────  ║
║  1  Cash Account      Cash        -        ║
║  2  SCPI Eurizon      SCPI        Parts   ║
║  3  Bitcoin           Crypto      Satoshis║
║  4  Livret A          Cash        -        ║
║  5  Assurance Vie     Insurance   -        ║
║  6  PER               PER         -        ║
║                                            ║
╚════════════════════════════════════════════╝
```

---

#### `list-transactions`
Lister toutes les transactions.

```bash
finance-tracker list-transactions
```

**Avec filtres:**
```bash
# Filtrer par produit
finance-tracker list-transactions --product "SCPI Eurizon"

# Filtrer par type
finance-tracker list-transactions --type BUY

# Filtrer par date
finance-tracker list-transactions --since 2024-01-01 --until 2024-02-28

# Combiner filtres
finance-tracker list-transactions --product "Bitcoin" --type SELL
```

**Output:**
```
╔══════════════════════════════════════════════════════════╗
║           📋 LISTE DES TRANSACTIONS                     ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║ ID  Date      Type    Produit       Montant  Description║
║ ──────────────────────────────────────────────────────   ║
║  1  2024-02-15 BUY    SCPI Eurizon  -2500   Ach 10 parts║
║  2  2024-02-20 DEPOSIT Cash Account +5000   Initial     ║
║  3  2024-02-28 DIST   SCPI Eurizon  +150    Coupon      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

---

#### `list-valuations`
Lister toutes les valorisations.

```bash
finance-tracker list-valuations
```

**Avec filtres:**
```bash
# Filtrer par produit
finance-tracker list-valuations --product "SCPI Eurizon"

# Filtrer par date
finance-tracker list-valuations --since 2024-02-01

# Dernières valorisations
finance-tracker list-valuations --limit 10
```

---

### 4️⃣ **Gestion Spécialisée**

#### `update-btc`
Forcer la mise à jour du prix Bitcoin depuis CoinGecko.

```bash
finance-tracker update-btc
```

**Output:**
```
✓ Prix Bitcoin mis à jour
  BTC/EUR: 47 500.00
  Dernière mise à jour: 2024-02-28 14:32:00
  Source: CoinGecko API
```

**Options:**
```bash
# Avec verbosité
finance-tracker update-btc --verbose

# Dry-run (vérifier sans enregistrer)
finance-tracker update-btc --dry-run
```

---

#### `project`
Lancer des projections financières (intérêts composés).

```bash
finance-tracker project \
  --initial-capital 39600 \
  --annual-return 8 \
  --years 20 \
  --monthly-contribution 500
```

**Options:**

| Option | Type | Défaut |
|--------|------|--------|
| `--initial-capital` | float | Valeur actuelle du portefeuille |
| `--annual-return` | float | 8.0 (%) |
| `--years` | int | 10 |
| `--monthly-contribution` | float | 0 (optionnel) |

**Output:**
```
╔════════════════════════════════════════════╗
║     📈 PROJECTION SUR 20 ANS               ║
╠════════════════════════════════════════════╣
║                                            ║
║  Capital initial:       39 600.00 EUR      ║
║  Rendement annuel:           8.00 %        ║
║  Versements mensuels:       500.00 EUR     ║
║                                            ║
║  ─ RÉSULTAT ─                              ║
║  Valeur à 20 ans:      323 156.50 EUR      ║
║  Gain total:           283 556.50 EUR      ║
║  Ratio de croissance:         8.16 x       ║
║                                            ║
╚════════════════════════════════════════════╝
```

---

#### `export`
Exporter les données en différents formats.

```bash
# Export CSV
finance-tracker export --format csv --output portfolio.csv

# Export JSON
finance-tracker export --format json --output portfolio.json

# Export PDF
finance-tracker export --format pdf --output rapport.pdf

# Export Excel
finance-tracker export --format excel --output portfolio.xlsx
```

---

### 5️⃣ **Maintenance**

#### `validate-db`
Vérifier l'intégrité de la base de données.

```bash
finance-tracker validate-db
```

**Output:**
```
✓ Vérification de la base de données
  ✓ Tables présentes
  ✓ Intégrité referentielle OK
  ✓ 42 transactions
  ✓ 6 produits
  ✓ 50 valorisations
```

---

#### `backup-db`
Créer une sauvegarde de la base de données.

```bash
finance-tracker backup-db
```

**Output:**
```
✓ Sauvegarde créée
  Fichier: ./backups/finance_tracker_2024-02-28_143200.db
  Taille: 256 KB
```

---

#### `restore-db`
Restaurer depuis une sauvegarde.

```bash
finance-tracker restore-db \
  --backup-file ./backups/finance_tracker_2024-02-28_143200.db
```

---

## 📜 Exemples de Workflows

### Workflow 1: Initialisation Complète

```bash
# 1. Initialiser la BD
finance-tracker init-db

# 2. Charger les produits de base
finance-tracker seed-products

# 3. Faire un versement initial
finance-tracker add-transaction \
  --product "Cash Account" \
  --type DEPOSIT \
  --amount 10000 \
  --date 2024-02-15

# 4. Acheter de la SCPI
finance-tracker add-transaction \
  --product "SCPI Eurizon" \
  --type BUY \
  --quantity 10 \
  --unit-price 250 \
  --amount 2500 \
  --date 2024-02-15

# 5. Afficher le résumé
finance-tracker dashboard
```

---

### Workflow 2: Mise à Jour Régulière (Script Cron)

```bash
#!/bin/bash
# update-portfolio.sh - À exécuter mensuellement

# Mettre à jour Bitcoin
finance-tracker update-btc

# Mettre à jour SCPI
finance-tracker add-valuation \
  --product "SCPI Eurizon" \
  --unit-price 265.00 \
  --date $(date +%Y-%m-%d)

# Exporter en JSON
finance-tracker dashboard --json > portfolio_$(date +%Y%m%d).json

# Sauvegarde
finance-tracker backup-db

echo "✓ Portefeuille mis à jour"
```

**Utilisation cron:**
```bash
# Chaque 1er du mois à 09:00
0 9 1 * * /home/user/update-portfolio.sh
```

---

### Workflow 3: Analyse Programmée (Python)

```python
import json
import subprocess

# Récupérer le dashboard en JSON
result = subprocess.run(
    ["finance-tracker", "dashboard", "--json"],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)

# Analyser
valeur_totale = data["portfolio_value"]
perf_pct = data["performance_percent"]

if perf_pct > 15:
    print(f"🎉 Excellent: {perf_pct}% de gain!")
elif perf_pct < 0:
    print(f"⚠️  Attention: {perf_pct}% de perte")

# Envoyer notification (ex. email)
if valeur_totale > 100000:
    send_alert(f"Portefeuille > 100k€: {valeur_totale}€")
```

---

## 🎯 Aide Intégrée

```bash
# Aide générale
finance-tracker --help

# Aide pour une commande spécifique
finance-tracker add-transaction --help

# Version
finance-tracker --version
```

---

## ⚙️ Options Globales

```bash
# Mode verbeux (debug)
finance-tracker --verbose add-transaction ...

# Fichier de configuration personnalisé
finance-tracker --config ./config.json dashboard

# Fichier DB personnalisé
finance-tracker --db-path ./mon-portfolio.db dashboard
```

---

## 🔗 Liens Connexes

- [INTERFACE_WEB.md](./INTERFACE_WEB.md) - Guide web (Streamlit)
- [BASE_DONNEES.md](./BASE_DONNEES.md) - Structure SQLite
- [FORMULES_CALCULS.md](./FORMULES_CALCULS.md) - Mathématiques
