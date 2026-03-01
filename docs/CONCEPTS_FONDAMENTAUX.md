# 📖 Concepts Fondamentaux

> Comprendre l'architecture conceptuelle de Finance Tracker

---

## 🎯 Introduction

Finance Tracker repose sur trois concepts fondamentaux qui forment les piliers de tout le système. Comprendre ces trois éléments est essentiel pour utiliser efficacement l'application.

## 🏗️ Les 3 Piliers

### 1️⃣ **Produits (Products)**

Un **Produit** représente le "contenant" — le type de placement financier.

#### Définition
C'est l'objet stable créé une seule fois qui ne change jamais. Il représente un actif spécifique (ex: "SCPI Eurizon", "Mon Livret A", "Bitcoin").

#### Caractéristiques

```
Produit: SCPI Eurizon
├── ID: 1
├── Nom: SCPI Eurizon
├── Type: SCPI
├── Unité: Parts (nombre de parts possédées)
├── Devise: EUR
├── Niveau de risque: Modéré
└── Créé le: 2024-01-15
```

#### Types de Produits Supportés

| Type | Unité | Exemple | Caractéristique |
|------|-------|---------|-----------------|
| **Cash** | Aucun | Compte courant | Valeur = quantité |
| **SCPI** | Parts | SCPI Eurizon | Valeur variable par part |
| **Bitcoin** | Satoshis | BTC | Très volatile, API en temps réel |
| **Assurance Vie** | Aucun/Parts | AV Multi-fonds | Peut contenir plusieurs fonds |
| **PER** | Aucun | PER Retraite | Compte de retraite bloqué |
| **Livret** | Aucun | Livret A | Épargne réglementée |
| **Autre** | Variable | Immobilier direct | Extensible |

#### Attributs Clés

```python
{
    "id": 1,
    "name": "SCPI Eurizon",
    "type": "SCPI",
    "currency": "EUR",
    "unit": "Parts",
    "risk_level": "Moderate",
    "created_at": "2024-01-15T10:00:00"
}
```

#### Exemples Concrets

**Produit: SCPI Eurizon**
- Type: SCPI (Société Civile de Placement Immobilier)
- Unité: Parts
- Risque: Modéré
- Cas d'usage: Investissement immobilier indirect

**Produit: Mon Bitcoin**
- Type: Crypto
- Unité: Satoshis (1 BTC = 100 000 000 Sats)
- Risque: Très élevé
- Cas d'usage: Crypto-monnaie native

**Produit: Livret A**
- Type: Cash
- Unité: Aucun (quantité = valeur)
- Risque: Très faible
- Cas d'usage: Épargne liquide garantie

---

### 2️⃣ **Transactions (Movements)**

Une **Transaction** enregistre un flux d'argent ou de quantité.

#### Définition
C'est un événement ponctuel qui modifie la composition du portefeuille. Les transactions créent l'historique et permettent de calculer l'investissement net total.

#### Types de Transactions

Finance Tracker supporte **6 types** de transactions :

| Type | Direction | Description | Exemple |
|------|-----------|-------------|---------|
| **DEPOSIT** | → Entrée | Apport d'argent frais | Versement de 5 000€ |
| **WITHDRAW** | ← Sortie | Retrait d'argent | Retraite de 1 000€ |
| **BUY** | ← Sortie | Achat d'un actif | 10 parts SCPI à 250€ = 2 500€ |
| **SELL** | → Entrée | Vente d'un actif | 5 parts SCPI à 260€ = 1 300€ |
| **DISTRIBUTION** | → Entrée | Dividende/Loyer reçu | Coupon SCPI: 150€ |
| **FEE** | ← Sortie | Frais payés | Commission: -50€ |

#### Structure d'une Transaction

```python
{
    "id": 42,
    "product_id": 1,
    "type": "BUY",
    "date": "2024-02-15",
    "quantity": 10,           # Nombre de parts achetées
    "unit_price": 250.0,      # Prix par part
    "total_amount": 2500.0,   # 10 × 250 = 2500
    "description": "Achat de 10 parts SCPI Eurizon",
    "created_at": "2024-02-15T14:30:00"
}
```

#### Cas d'Usage Complets

**Cas 1: Achat de SCPI**
```
Type: BUY
Produit: SCPI Eurizon
Quantité: 10 parts
Prix unitaire: 250€
Montant total: 2 500€
Date: 15/02/2024
```

**Cas 2: Distribution reçue**
```
Type: DISTRIBUTION
Produit: SCPI Eurizon
Quantité: Aucun (distribution simple)
Montant: 150€ (coupon semestriel)
Date: 28/02/2024
```

**Cas 3: Achat de Bitcoin**
```
Type: BUY
Produit: Mon Bitcoin
Quantité: 2 000 000 satoshis (0.02 BTC)
Prix unitaire: 0.000025€ par satoshi
Montant total: 50€
Date: 01/02/2024
```

#### Logique Métier des Transactions

**Investissement Net** = Ce que vous avez réellement investi en argent frais

```
Investissement Net = Σ DEPOSIT + Σ SELL + Σ DISTRIBUTION - Σ WITHDRAW - Σ BUY - Σ FEE
```

Ou plus simplement :
```
Investissement Net = Argent entré - Argent sorti
```

**Exemple:**
```
Opérations:
- DEPOSIT 10 000€ (versement initial)
- BUY 2 500€ (achat SCPI)
- DISTRIBUTION 150€ (coupon reçu)
- WITHDRAW 500€ (retraite partielle)
- FEE 50€ (frais)

Investissement Net = (10000 + 150) - (2500 + 500 + 50) = 7 100€
```

---

### 3️⃣ **Valorisations (Valuations/Snapshots)**

Une **Valorisation** capture la valeur d'un produit à un instant T.

#### Définition
C'est une photographie de la valeur unitaire d'un produit à un moment donné. Elle permet de comparer l'investissement initial à la valeur actuelle.

#### Structure d'une Valorisation

```python
{
    "id": 99,
    "product_id": 1,
    "date": "2024-02-28",
    "unit_price": 262.5,      # Nouvelle valeur de la part
    "total_value": None,       # Calculée en frontend si besoin
    "source": "manual",        # ou "api" pour Bitcoin
    "created_at": "2024-02-28T09:00:00"
}
```

#### Exemple Concret: SCPI Eurizon

**Historique:**
```
Achat: 40 parts à 250€ = 10 000€ investi
Valorisation 01/02: 255€ par part → Valeur totale: 10 200€
Valorisation 15/02: 260€ par part → Valeur totale: 10 400€
Valorisation 28/02: 262.5€ par part → Valeur totale: 10 500€
```

**Gains/Pertes:**
```
Valeur actuelle: 10 500€
Investissement net: 10 000€
Gain latent: 500€ (+5%)
```

#### Bitcoin: Cas Particulier

Pour Bitcoin, la valorisation peut provenir d'une **API en temps réel** (CoinGecko) ou être saisie manuellement.

```python
{
    "product_id": 3,  # Bitcoin
    "date": "2024-02-28",
    "unit_price": 47500,  # EUR par BTC (0.475€ par sat en 100M sats)
    "source": "api"        # Récupéré automatiquement de CoinGecko
}
```

---

## 🔄 Les Interactions Entre Piliers

### Flux Complet: Achat de SCPI

**Étape 1: Créer le Produit** (une seule fois)
```
PRODUIT créé:
- Nom: SCPI Eurizon
- Type: SCPI
- Unité: Parts
```

**Étape 2: Enregistrer la Transaction**
```
TRANSACTION enregistrée:
- Type: BUY
- Produit: SCPI Eurizon
- Quantité: 10 parts
- Prix: 250€ par part
- Montant: 2 500€
- Date: 15/02/2024
```

**Étape 3: Enregistrer la Valorisation**
```
VALORISATION enregistrée:
- Produit: SCPI Eurizon
- Valeur: 255€ par part
- Date: 28/02/2024
```

**Étape 4: Calculs Automatiques**
```
Le système calcule automatiquement:
- Quantité possédée: 10 parts (depuis BUY)
- Valeur actuelle: 10 × 255€ = 2 550€
- Investissement net pour ce produit: 2 500€
- Gain latent: 2 550€ - 2 500€ = 50€ (+2%)
```

---

## 📊 Modèle de Données

```
PRODUCTS (Produits)
├── id (PK)
├── name
├── type (SCPI, Bitcoin, Cash, etc.)
├── currency (EUR, USD, etc.)
├── unit (Parts, Satoshis, Aucun)
├── risk_level (Low, Medium, High, VeryHigh)
└── created_at

TRANSACTIONS (Mouvements)
├── id (PK)
├── product_id (FK → PRODUCTS)
├── type (DEPOSIT, WITHDRAW, BUY, SELL, DISTRIBUTION, FEE)
├── date
├── quantity (optionnel, 0 pour Cash/Distribution)
├── unit_price (prix par unité ou par part)
├── total_amount (montant total en EUR)
├── description
└── created_at

VALUATIONS (Valorisations)
├── id (PK)
├── product_id (FK → PRODUCTS)
├── date
├── unit_price (valeur actuelle par unité)
├── source (manual, api)
└── created_at
```

---

## 💡 Bonnes Pratiques

### ✅ À Faire

1. **Créer des produits clairs et uniques**
   - Noms explicites: "SCPI Eurizon" plutôt que "SCPI 1"
   - Un produit = une entité uniquement

2. **Enregistrer chaque transaction précisément**
   - Respecter les types (BUY ≠ SELL)
   - Inclure les frais comme des transactions FEE séparées
   - Dater correctement

3. **Mettre à jour régulièrement les valorisations**
   - Hebdomadaire pour le suivi actif
   - Mensuel minimum pour l'archivage
   - Bitcoin: Laisser l'API mettre à jour automatiquement

### ❌ À Éviter

1. **Mélanger produits et transactions**
   - Ne pas créer un produit pour chaque transaction
   - Réutiliser les produits existants

2. **Négliger les dates**
   - Les dates sont critiques pour les calculs
   - Ne pas ante-dater les transactions

3. **Oublier les frais**
   - Les frais = transactions FEE explicites
   - Ils réduisent votre investissement net réel

---

## 🔗 Liens Connexes

- [INTERFACE_WEB.md](./INTERFACE_WEB.md) - Comment ajouter des produits et transactions
- [BASE_DONNEES.md](./BASE_DONNEES.md) - Schéma détaillé des tables
- [FORMULES_CALCULS.md](./FORMULES_CALCULS.md) - Mathématiques complètes
