# 🗄️ Base de Données SQLite

> Structure, schéma et gestion des données

---

## 🎯 Introduction

Finance Tracker utilise **SQLite** comme base de données locale. C'est une base de données relationnelle légère, parfaite pour une utilisation personnelle.

**Fichier:** `finance_tracker.db` (créé automatiquement dans le répertoire courant)

---

## 🏗️ Schéma de Base de Données

```
FINANCE_TRACKER.DB
├── schema_version (Migrations appliquées)
│
├── Patrimoine
│   ├── products (Produits)
│   ├── transactions (Mouvements)
│   ├── valuations (Valorisations)
│   └── rateschedule (Barèmes de taux)
│
├── Signal crypto
│   ├── cryptoasset (Identité de marché d'un produit)
│   ├── scanrun (Un scan, et son état de marché)
│   ├── positionverdict (Le verdict d'une position sur un scan)
│   ├── profittaken (Mise déjà récupérée sur une ligne)
│   └── swapexecution (Un swap réellement exécuté)
│
├── Portefeuilles suivis
│   ├── wallet (Adresse publique surveillée)
│   ├── walletholding (Solde découvert à une adresse)
│   ├── wallettransfer (Mouvement lu sur la chaîne)
│   ├── costbasisestimate (Prix de revient reconstitué)
│   └── providercredential (Clés d'API de l'utilisateur)
│
└── [Indices & Contraintes]
```

> ⚠️ Les tables du signal crypto alimentent un outil **éducatif**. Voir
> [DISCLAIMER.md](./DISCLAIMER.md).

---

## 🔄 Migrations de schéma

Jusqu'à la v1.0.0, le schéma était créé par `SQLModel.metadata.create_all()`
seul. Cet appel ajoute les **tables manquantes**, ce qui suffit tant qu'une
version n'ajoute que des tables — mais il ne touche jamais à une table existante.
Dès qu'une version ajoute une **colonne**, tout fichier `.db` exporté avant elle
s'ouvrirait normalement puis échouerait à la première requête mentionnant cette
colonne.

Chaque changement de schéma porte donc désormais un numéro, un nom et une
fonction, dans `finance_tracker/repositories/migrations.py`. Les versions
appliquées sont consignées dans `schema_version`.

### Ce qui se passe à l'ouverture d'une base

1. `create_all()` crée les tables manquantes.
2. `run_migrations()` applique, dans l'ordre, les migrations numérotées au-dessus
   de la version enregistrée.

Les deux étapes ignorent ce qui est déjà fait, donc l'opération est sûre à chaque
démarrage. Elle se déclenche aussi **à l'import d'une sauvegarde** : c'est
précisément le cas où le fichier peut venir d'une version antérieure.

### Migrations existantes

| Version | Nom | Effet |
|---|---|---|
| 1 | `crypto_and_wallet_tables` | Crée les dix tables du signal et des portefeuilles. Aucune table existante n'est touchée. |
| 2 | `valuation_source` | Ajoute `valuation.source`, rétro-rempli à `MANUAL`. |

`MANUAL` est la valeur **juste** pour les lignes antérieures, pas seulement la
plus commode : elles ont toutes été saisies à la main. Cette colonne est ce qui
empêche une actualisation automatique des cours d'écraser une valeur corrigée.

### Vérifier l'état d'une base

```python
from sqlmodel import create_engine
from finance_tracker.repositories.migrations import applied_migrations, current_version

engine = create_engine("sqlite:///data/finance.db")
print(current_version(engine))
print(applied_migrations(engine))
```

Une base créée de zéro et une base migrée depuis la v1.0.0 aboutissent au **même
schéma**, table pour table et colonne pour colonne. C'est vérifié par
`tests/test_migrations.py::test_fresh_and_migrated_schemas_match`, et c'est ce
qui garantit qu'une sauvegarde ancienne reste utilisable.

---

## 📋 Table 1: PRODUCTS (Produits)

Contient les définitions de tous les placements.

### Structure

```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    unit VARCHAR(50),
    risk_level VARCHAR(20),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Colonnes

| Colonne | Type | Contrainte | Description |
|---------|------|-----------|-------------|
| `id` | INTEGER | PK, AUTO | Identifiant unique |
| `name` | VARCHAR(255) | NOT NULL, UNIQUE | Nom du produit (ex: "SCPI Eurizon") |
| `type` | VARCHAR(50) | NOT NULL | Type (SCPI, Cash, Crypto, Insurance, PER, etc.) |
| `currency` | VARCHAR(3) | DEFAULT 'EUR' | Devise (EUR, USD, GBP) |
| `unit` | VARCHAR(50) | - | Unité (Parts, Satoshis, Aucun) |
| `risk_level` | VARCHAR(20) | - | Niveau de risque (Low, Medium, High, VeryHigh) |
| `description` | TEXT | - | Description optionnelle |
| `created_at` | TIMESTAMP | DEFAULT NOW | Date de création |
| `updated_at` | TIMESTAMP | DEFAULT NOW | Dernière modification |

### Exemples de Données

```sql
INSERT INTO products VALUES
(1, 'SCPI Eurizon', 'SCPI', 'EUR', 'Parts', 'Medium', 'SCPI avec revenus réguliers', '2024-01-15 10:00:00', '2024-01-15 10:00:00'),
(2, 'Bitcoin', 'Crypto', 'EUR', 'Satoshis', 'VeryHigh', 'Bitcoin natif', '2024-02-01 08:30:00', '2024-02-28 14:32:00'),
(3, 'Livret A', 'Cash', 'EUR', NULL, 'Low', 'Compte épargne sécurisé', '2024-01-10 09:15:00', '2024-01-10 09:15:00'),
(4, 'Assurance Vie', 'Insurance', 'EUR', NULL, 'Medium', 'Contrat d''assurance vie multi-fonds', '2024-01-20 11:00:00', '2024-01-20 11:00:00');
```

### Types Supportés

```
CASH, SCPI, BITCOIN, SAVINGS, INSURANCE, PER, FCPI, CRYPTO
```

`CRYPTO` couvre tout crypto-actif autre que le bitcoin. Un produit rejoint
l'arbitrage du signal en recevant une ligne dans `cryptoasset` : c'est tout
l'opt-in, et un produit qui n'en a pas est totalement ignoré par le moteur.

---

## 💳 Table 2: TRANSACTIONS (Mouvements)

Enregistre tous les flux financiers.

### Structure

```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    type VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    quantity DECIMAL(20,8),
    unit_price DECIMAL(10,6),
    total_amount DECIMAL(15,2) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);
```

### Colonnes

| Colonne | Type | Contrainte | Description |
|---------|------|-----------|-------------|
| `id` | INTEGER | PK, AUTO | Identifiant unique |
| `product_id` | INTEGER | FK → products | Référence au produit |
| `type` | VARCHAR(20) | NOT NULL | Type (DEPOSIT, WITHDRAW, BUY, SELL, DISTRIBUTION, FEE) |
| `date` | DATE | NOT NULL | Date de la transaction |
| `quantity` | DECIMAL(20,8) | - | Quantité (parts, satoshis) |
| `unit_price` | DECIMAL(10,6) | - | Prix par unité |
| `total_amount` | DECIMAL(15,2) | NOT NULL | Montant total en EUR |
| `description` | TEXT | - | Description détaillée |
| `created_at` | TIMESTAMP | DEFAULT NOW | Date de création |
| `updated_at` | TIMESTAMP | DEFAULT NOW | Dernière modification |

### Types Acceptés

```
DEPOSIT       : Versement d'argent
WITHDRAW      : Retrait d'argent
BUY           : Achat d'actif
SELL          : Vente d'actif
DISTRIBUTION  : Dividende/Coupon reçu
FEE           : Frais payés
```

### Exemples de Données

```sql
INSERT INTO transactions VALUES
(1, 1, 'BUY', '2024-02-15', 10, 250.00, 2500.00, 'Achat 10 parts SCPI', '2024-02-15 14:30:00', '2024-02-15 14:30:00'),
(2, 3, 'DEPOSIT', '2024-02-15', NULL, NULL, 5000.00, 'Versement initial', '2024-02-15 10:00:00', '2024-02-15 10:00:00'),
(3, 1, 'DISTRIBUTION', '2024-02-28', NULL, NULL, 150.00, 'Coupon semestriel février', '2024-02-28 09:00:00', '2024-02-28 09:00:00'),
(4, 2, 'BUY', '2024-02-20', 2000000, 0.00045, 950.00, 'Achat 0.02 BTC', '2024-02-20 11:15:00', '2024-02-20 11:15:00'),
(5, 3, 'WITHDRAW', '2024-02-25', NULL, NULL, 500.00, 'Retrait partiel', '2024-02-25 15:45:00', '2024-02-25 15:45:00');
```

### Contraintes Métier

```sql
-- Vérifier que le type est valide
CHECK (type IN ('DEPOSIT', 'WITHDRAW', 'BUY', 'SELL', 'DISTRIBUTION', 'FEE'))

-- Vérifier que le montant est positif
CHECK (total_amount > 0)

-- Vérifier que la quantité est positive (si présente)
CHECK (quantity IS NULL OR quantity > 0)

-- Vérifier que le prix unitaire est positif (si présent)
CHECK (unit_price IS NULL OR unit_price > 0)

-- Vérifier que la date n'est pas futur
CHECK (date <= DATE('now'))
```

---

## 📊 Table 3: VALUATIONS (Valorisations)

Enregistre l'évolution des prix au fil du temps.

### Structure

```sql
CREATE TABLE valuations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    date DATE NOT NULL,
    unit_price DECIMAL(10,6) NOT NULL,
    source VARCHAR(20) DEFAULT 'manual',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(product_id, date)
);
```

### Colonnes

| Colonne | Type | Contrainte | Description |
|---------|------|-----------|-------------|
| `id` | INTEGER | PK, AUTO | Identifiant unique |
| `product_id` | INTEGER | FK → products | Référence au produit |
| `date` | DATE | NOT NULL | Date de la valorisation |
| `unit_price` | DECIMAL(10,6) | NOT NULL | Prix par unité |
| `source` | VARCHAR(20) | DEFAULT 'manual' | Origine (manual, api, broker) |
| `notes` | TEXT | - | Notes additionnelles |
| `created_at` | TIMESTAMP | DEFAULT NOW | Date de création |
| `updated_at` | TIMESTAMP | DEFAULT NOW | Dernière modification |

### Contrainte Unique

```sql
-- Une seule valorisation par produit par date
UNIQUE(product_id, date)
```

### Source Acceptées

```
manual  : Saisie manuelle
api     : Récupéré automatiquement (ex: CoinGecko pour Bitcoin)
broker  : Données du courtier
```

### Exemples de Données

```sql
INSERT INTO valuations VALUES
(1, 1, '2024-02-15', 250.00, 'manual', 'Selon relevé officiel', '2024-02-15 10:00:00', '2024-02-15 10:00:00'),
(2, 1, '2024-02-28', 262.50, 'manual', 'Mise à jour mensuelle', '2024-02-28 09:00:00', '2024-02-28 09:00:00'),
(3, 2, '2024-02-28', 47500.00, 'api', 'CoinGecko API EUR', '2024-02-28 14:32:00', '2024-02-28 14:32:00'),
(4, 1, '2024-02-01', 255.00, 'manual', 'Semaine 1', '2024-02-01 10:00:00', '2024-02-01 10:00:00');
```

---

## 🔗 Relations Entre Tables

```
products ──┬──→ transactions (product_id → id)
           │
           └──→ valuations (product_id → id)
```

### Schéma Relationnel

```
PRODUCTS
┌──────────────────────────┐
│ id (PK)                  │
│ name (UNIQUE)            │
│ type                     │
│ currency                 │
│ unit                     │
│ risk_level               │
│ description              │
│ created_at               │
│ updated_at               │
└──────────────────────────┘
        ▲          ▲
        │          │
        │ FK       │ FK
        │          │
   ┌────┴────┐  ┌──┴────────┐
   │          │  │           │
TRANSACTIONS VALUATIONS
│ id (PK)    │  │ id (PK)    │
│ product_id │  │ product_id │
│ type       │  │ date       │
│ date       │  │ unit_price │
│ quantity   │  │ source     │
│ unit_price │  │ notes      │
│ amount     │  │ created_at │
│ created_at │  │ updated_at │
└────────────┘  └────────────┘
```

---

## 📈 Indices & Optimisations

Pour améliorer les performances sur les requêtes fréquentes :

```sql
-- Index sur product_id (clé étrangère)
CREATE INDEX idx_transactions_product_id ON transactions(product_id);
CREATE INDEX idx_valuations_product_id ON valuations(product_id);

-- Index sur date (filtrage courant)
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_valuations_date ON valuations(date);

-- Index combiné pour requêtes fréquentes
CREATE INDEX idx_transactions_product_date ON transactions(product_id, date);
CREATE INDEX idx_valuations_product_date ON valuations(product_id, date DESC);
```

---

## 🔄 Requêtes Courantes

### 1. Valeur Actuelle du Portefeuille

```sql
SELECT 
    p.id,
    p.name,
    SUM(CASE 
        WHEN t.type IN ('BUY', 'DEPOSIT') THEN t.quantity 
        WHEN t.type IN ('SELL', 'WITHDRAW') THEN -t.quantity
        ELSE 0
    END) as current_quantity,
    (SELECT unit_price FROM valuations 
     WHERE product_id = p.id 
     ORDER BY date DESC LIMIT 1) as current_price,
    SUM(CASE 
        WHEN t.type IN ('BUY', 'DEPOSIT') THEN t.quantity 
        WHEN t.type IN ('SELL', 'WITHDRAW') THEN -t.quantity
        ELSE 0
    END) * (SELECT unit_price FROM valuations 
            WHERE product_id = p.id 
            ORDER BY date DESC LIMIT 1) as current_value
FROM products p
LEFT JOIN transactions t ON p.id = t.product_id
GROUP BY p.id, p.name
ORDER BY current_value DESC;
```

### 2. Investissement Net par Produit

```sql
SELECT 
    p.name,
    SUM(CASE 
        WHEN t.type IN ('DEPOSIT', 'DISTRIBUTION', 'SELL') THEN t.total_amount
        WHEN t.type IN ('WITHDRAW', 'BUY', 'FEE') THEN -t.total_amount
        ELSE 0
    END) as invested_net
FROM products p
LEFT JOIN transactions t ON p.id = t.product_id
GROUP BY p.id, p.name
ORDER BY invested_net DESC;
```

### 3. Performance Globale

```sql
WITH portfolio_value AS (
    SELECT 
        SUM(CASE 
            WHEN t.type IN ('BUY', 'DEPOSIT') THEN t.quantity 
            WHEN t.type IN ('SELL', 'WITHDRAW') THEN -t.quantity
            ELSE 0
        END) * (SELECT COALESCE(unit_price, 0) FROM valuations 
                ORDER BY date DESC LIMIT 1)) as total_value
    FROM transactions t
),
invested_net AS (
    SELECT 
        SUM(CASE 
            WHEN type IN ('DEPOSIT', 'DISTRIBUTION', 'SELL') THEN total_amount
            WHEN type IN ('WITHDRAW', 'BUY', 'FEE') THEN -total_amount
            ELSE 0
        END) as net
    FROM transactions
)
SELECT 
    (SELECT total_value FROM portfolio_value) as portfolio_value,
    (SELECT net FROM invested_net) as invested_net,
    ((SELECT total_value FROM portfolio_value) - (SELECT net FROM invested_net)) as performance_euro,
    (((SELECT total_value FROM portfolio_value) - (SELECT net FROM invested_net)) / 
     (SELECT net FROM invested_net) * 100) as performance_percent;
```

### 4. Historique Valorisations d'un Produit

```sql
SELECT 
    date,
    unit_price,
    source,
    LAG(unit_price) OVER (ORDER BY date) as previous_price,
    (unit_price - LAG(unit_price) OVER (ORDER BY date)) as price_change,
    ((unit_price - LAG(unit_price) OVER (ORDER BY date)) / 
     LAG(unit_price) OVER (ORDER BY date) * 100) as percent_change
FROM valuations
WHERE product_id = 1
ORDER BY date DESC;
```

### 5. Dernière Valorisation par Produit

```sql
SELECT 
    p.id,
    p.name,
    v.date,
    v.unit_price,
    v.source
FROM products p
LEFT JOIN LATERAL (
    SELECT * FROM valuations 
    WHERE product_id = p.id 
    ORDER BY date DESC 
    LIMIT 1
) v ON TRUE
ORDER BY p.name;
```

---

## 🔒 Intégrité Référentielle

### Contraintes de Clés Étrangères

```sql
-- Transactions MUST point to existing product
ALTER TABLE transactions
ADD CONSTRAINT fk_transactions_product
FOREIGN KEY (product_id) REFERENCES products(id)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- Valuations MUST point to existing product
ALTER TABLE valuations
ADD CONSTRAINT fk_valuations_product
FOREIGN KEY (product_id) REFERENCES products(id)
ON DELETE CASCADE
ON UPDATE CASCADE;
```

### Suppression en Cascade

Si vous supprimez un produit, toutes ses transactions et valorisations sont automatiquement supprimées.

```sql
-- Danger! Supprime aussi tous les mouvements associés
DELETE FROM products WHERE id = 1;
```

---

## 💾 Sauvegarde & Restauration

### Sauvegarde Manuelle

```bash
# Copier le fichier DB
cp finance_tracker.db finance_tracker_backup_2024-02-28.db

# Ou avec SQLite
sqlite3 finance_tracker.db ".backup backup.db"
```

### Restauration

```bash
# Remplacer par la sauvegarde
cp finance_tracker_backup_2024-02-28.db finance_tracker.db

# Ou via CLI
finance-tracker restore-db --backup backup.db
```

---

## 🔄 Migrations & Changements de Schéma

### Ajouter une Colonne

```sql
ALTER TABLE products 
ADD COLUMN custom_field VARCHAR(255) DEFAULT NULL;
```

### Renommer une Table

```sql
ALTER TABLE products RENAME TO products_old;
```

### Modifier une Contrainte

SQLite ne supporte pas `ALTER COLUMN`. Solution:
1. Créer nouvelle table avec schema correct
2. Copier les données
3. Renommer anciennes table en `_old`
4. Renommer nouvelle table

---

## 📊 Statistiques de la BD

### Taille du Fichier

```bash
# Vérifier la taille
ls -lh finance_tracker.db
```

Exemple:
```
-rw-r--r--  1 user  group  256K  Feb 28 14:32 finance_tracker.db
```

### Nombre de Lignes

```sql
SELECT 
    'products' as table_name, COUNT(*) as row_count FROM products
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL
SELECT 'valuations', COUNT(*) FROM valuations;
```

---

## ⚙️ Configuration SQLite

### PRAGMA Recommandés

```sql
-- Mode journal plus rapide
PRAGMA journal_mode = WAL;

-- Synchronisation moins agressive
PRAGMA synchronous = NORMAL;

-- Cache plus grand
PRAGMA cache_size = 10000;

-- Vérification de l'intégrité
PRAGMA integrity_check;
```

---

## 🔗 Liens Connexes

- [CONCEPTS_FONDAMENTAUX.md](./CONCEPTS_FONDAMENTAUX.md) - Comprendre les piliers
- [INTERFACE_WEB.md](./INTERFACE_WEB.md) - Utiliser l'app web
- [CLI_GUIDE.md](./CLI_GUIDE.md) - Commandes disponibles
- [FORMULES_CALCULS.md](./FORMULES_CALCULS.md) - Calculs utilisés
