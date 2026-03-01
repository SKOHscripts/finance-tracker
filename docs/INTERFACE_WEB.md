# 💻 Guide Interface Web (Streamlit)

> Tutoriel complet page par page de l'interface web

---

## 🎯 Vue d'ensemble

L'interface web Streamlit de Finance Tracker est le cœur interactif de l'application. Elle offre une expérience ergonomique avec plusieurs pages spécialisées.

**Accès:** `http://localhost:8501` (après avoir lancé `streamlit run app.py`)

---

## 📑 Architecture de l'App

```
Finance Tracker (Streamlit)
├── 📊 Dashboard (page principale)
├── ➕ Ajouter Transaction
├── 💰 Ajouter Valorisation
├── ₿ Bitcoin (suivi temps réel)
├── 📋 Listes & Édition
│   ├── Produits
│   ├── Transactions
│   └── Valorisations
├── 📄 Rapport PDF
└── 📈 Simulateur
```

---

## 📊 Page 1: Dashboard (Accueil)

La page principale affiche une synthèse globale de votre portefeuille.

### Vue Générale

```
┌─────────────────────────────────────────┐
│         📊 TABLEAU DE BORD              │
├─────────────────────────────────────────┤
│                                         │
│  Valeur Totale: 45 000€                │
│  Performance: +5 400€ (+13.6%)          │
│  Investissement Net: 39 600€            │
│  Cash Disponible: 2 500€                │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  Allocation du Portefeuille (Graphique) │
│                                         │
│  SCPI Eurizon:     35% (15 750€)       │
│  Bitcoin:          40% (18 000€)        │
│  Livret A:         15% (6 750€)         │
│  Cash:              8% (3 600€)         │
│                                         │
└─────────────────────────────────────────┘
```

### Indicateurs Clés

| Indicateur | Calcul | Signification |
|-----------|--------|---------------|
| **Valeur Totale** | Σ (dernier prix × quantité) | La richesse actuelle |
| **Investissement Net** | Σ DEPOSIT - Σ WITHDRAW | L'argent réellement investi |
| **Performance (€)** | Valeur Totale - Inv. Net | Gain/Perte brut |
| **Performance (%)** | (Performance € / Inv. Net) × 100 | Rendement en % |
| **Cash** | Solde du compte Cash | Argent disponible immédiatement |

### Interactions

- **Rafraîchir:** Bouton "F5" ou clic du navigateur
- **Graphique:** Hover pour voir les détails
- **Zoom:** Clic sur légende pour masquer/afficher

---

## ➕ Page 2: Ajouter Transaction

Formulaire pour enregistrer un mouvement financier.

### Types de Transactions

#### 1. **DEPOSIT** (Dépôt d'argent)

Vous versez de l'argent frais dans votre portefeuille.

```
Formulaire:
├── Type: DEPOSIT
├── Produit: Cash (compte courant)
├── Montant: [1000] EUR
├── Date: [15/02/2024]
├── Description: Versement initial
└── [Ajouter]
```

**Impact:**
- Investissement Net +1 000€
- Cash +1 000€

#### 2. **WITHDRAW** (Retrait d'argent)

Vous retirez de l'argent de votre portefeuille.

```
Formulaire:
├── Type: WITHDRAW
├── Produit: Cash
├── Montant: [500] EUR
├── Date: [20/02/2024]
├── Description: Retrait partiel
└── [Ajouter]
```

**Impact:**
- Investissement Net -500€
- Cash -500€

#### 3. **BUY** (Achat d'actif)

Vous achetez un actif (parts, crypto, etc.).

```
Formulaire:
├── Type: BUY
├── Produit: [SCPI Eurizon ▼]
├── Quantité: [10] parts
├── Prix unitaire: [250] EUR/part
├── Montant total: [2500] EUR (automatique)
├── Date: [15/02/2024]
├── Description: Achat de 10 parts SCPI
└── [Ajouter]
```

**Impact:**
- SCPI Eurizon +10 parts
- Investissement Net -2 500€
- Cash -2 500€

#### 4. **SELL** (Vente d'actif)

Vous vendez un actif que vous possédiez.

```
Formulaire:
├── Type: SELL
├── Produit: [SCPI Eurizon ▼]
├── Quantité: [5] parts
├── Prix unitaire: [260] EUR/part
├── Montant total: [1300] EUR (automatique)
├── Date: [28/02/2024]
├── Description: Vente de 5 parts
└── [Ajouter]
```

**Impact:**
- SCPI Eurizon -5 parts
- Investissement Net +1 300€
- Cash +1 300€

#### 5. **DISTRIBUTION** (Dividende/Coupon)

Vous recevez une distribution (loyer, dividende).

```
Formulaire:
├── Type: DISTRIBUTION
├── Produit: [SCPI Eurizon ▼]
├── Montant: [150] EUR
├── Date: [28/02/2024]
├── Description: Coupon semestriel février
└── [Ajouter]
```

**Impact:**
- Investissement Net +150€
- Cash +150€
- Quantité SCPI inchangée

#### 6. **FEE** (Frais)

Vous payez des frais (commission, gestion, etc.).

```
Formulaire:
├── Type: FEE
├── Produit: [SCPI Eurizon ▼]
├── Montant: [50] EUR
├── Date: [28/02/2024]
├── Description: Frais de gestion annuels
└── [Ajouter]
```

**Impact:**
- Investissement Net -50€
- Cash -50€

### Conseils de Saisie

✅ **À faire:**
- Dater précisément chaque transaction
- Utiliser des descriptions claires
- Saisir les frais comme des FEE séparées
- Vérifier le produit sélectionné

❌ **À éviter:**
- Antédater les transactions (sauf si justifié)
- Mélanger types (BUY vs SELL)
- Oublier les frais
- Laisser descriptions vides

---

## 💰 Page 3: Ajouter Valorisation

Enregistrer la valeur actuelle d'un produit à une date donnée.

### Qu'est-ce qu'une Valorisation?

C'est le prix actuel d'une unité de votre produit, permettant de mettre à jour sa valeur totale.

### Formulaire de Saisie

```
Formulaire:
├── Produit: [SCPI Eurizon ▼]
├── Prix unitaire: [262.5] EUR/part
├── Date: [28/02/2024]
├── Source: [Manuel ▼]  (ou API pour BTC)
├── Notes: Selon relevé officiel
└── [Enregistrer]
```

### Cas d'Usage

**Scenario 1: SCPI**
```
Vous avez 40 parts achetées à 250€ = 10 000€
Le relevé du mois indique 262.5€/part
Vous saisissez:
  - Produit: SCPI Eurizon
  - Prix unitaire: 262.5
  - Date: 28/02/2024

Résultat:
  - Valeur actuelle: 40 × 262.5 = 10 500€
  - Gain latent: 10 500 - 10 000 = +500€ (+5%)
```

**Scenario 2: Bitcoin (Auto)**
```
Bitcoin peut être mis à jour automatiquement
via l'API CoinGecko.
Voir page dédiée "₿ Bitcoin" pour plus d'infos.
```

### Mise à Jour Régulière

**Recommandations:**
- **Hebdomadaire:** Pour suivi actif
- **Mensuel:** Standard recommandé
- **Trimestriel:** Minimum acceptable

---

## ₿ Page 4: Bitcoin

Page spécialisée pour le suivi du Bitcoin avec intégration API temps réel.

### Vue Générale

```
┌─────────────────────────────────────┐
│      ₿ SUIVI BITCOIN               │
├─────────────────────────────────────┤
│                                     │
│  Prix BTC/EUR:      47 500€         │
│  Mise à jour:       Automatique     │
│  Source:            CoinGecko API   │
│                                     │
├─────────────────────────────────────┤
│                                     │
│  Vos Satoshis:      2 000 000 sats  │
│                     (0.02 BTC)       │
│  Valeur actuelle:   950€            │
│  Investissement:    900€            │
│  Gain latent:       +50€ (+5.6%)    │
│                                     │
├─────────────────────────────────────┤
│  Historique des prix (Graphique)    │
│                                     │
│  [Courbe 30 derniers jours]         │
│                                     │
└─────────────────────────────────────┘
```

### Fonctionnalités

#### 1. **Mise à jour Automatique**
```
- L'API CoinGecko récupère le prix BTC/EUR en temps réel
- Mise à jour toutes les heures automatiquement
- Bouton "Rafraîchir maintenant" pour forcer
```

#### 2. **Historique des Prix**
```
- Graphique des 30 derniers jours
- Zoom et navigation possibles
- Affichage du min/max/moyenne
```

#### 3. **Calcul du PRU (Prix de Revient Unitaire)**
```
PRU = Investissement total / Quantité totale (en satoshis)

Exemple:
- Achat 1: 500 000 sats à 45 000€/BTC
  Montant: (500 000 / 100 000 000) × 45 000 = 225€
- Achat 2: 1 000 000 sats à 46 000€/BTC
  Montant: (1 000 000 / 100 000 000) × 46 000 = 460€

PRU = (225 + 460) / 1 500 000 sats = 0.000457€/sat
```

#### 4. **P&L Latente (Gains/Pertes)**
```
P&L = (Prix actuel - PRU) × Quantité

Exemple:
- PRU: 0.000457€/sat
- Prix actuel: 47 500€/BTC = 0.000475€/sat
- Quantité: 1 500 000 sats

P&L = (0.000475 - 0.000457) × 1 500 000 = +27€
```

### Gestion des Satoshis

**Important:** Les satoshis sont gérés sans double conversion:

```
1 BTC = 100 000 000 satoshis

Transactionssaisies:
- Type: BUY
- Produit: Bitcoin
- Quantité: 2 000 000 (satoshis)
- Prix unitaire: 0.000475 (EUR/sat)
- Montant: 950€

Valorisation:
- Produit: Bitcoin
- Prix unitaire: 0.000475 (EUR/sat)
- Date: 28/02/2024
```

---

## 📋 Page 5: Listes & Édition (CRUD)

Gérer, modifier et supprimer vos données.

### 5a) Liste des Produits

```
┌──────────────────────────────────────────┐
│         LISTE DES PRODUITS              │
├──────────────────────────────────────────┤
│                                          │
│ 1. SCPI Eurizon (SCPI) - Modéré          │
│    Unité: Parts | EUR | Créé 15/01/24   │
│    [Éditer] [Supprimer]                  │
│                                          │
│ 2. Bitcoin (Crypto) - Très Élevé         │
│    Unité: Satoshis | EUR | Créé 01/02/24│
│    [Éditer] [Supprimer]                  │
│                                          │
│ 3. Livret A (Cash) - Très Faible         │
│    Unité: Aucun | EUR | Créé 10/01/24   │
│    [Éditer] [Supprimer]                  │
│                                          │
└──────────────────────────────────────────┘
```

**Actions:**
- **Éditer:** Modifier nom, type, risque
- **Supprimer:** Supprimer le produit (attention: vérifie les références)

### 5b) Liste des Transactions

```
┌────────────────────────────────────────────┐
│       LISTE DES TRANSACTIONS               │
├────────────────────────────────────────────┤
│                                            │
│ ID  Date    Type  Produit  Montant  Desc  │
│─────────────────────────────────────────── │
│ 1   15/02   BUY   SCPI     -2500€   Ach10 │
│     [Éditer] [Supprimer]                   │
│                                            │
│ 2   20/02   DIST  SCPI     +150€    Coup  │
│     [Éditer] [Supprimer]                   │
│                                            │
│ 3   28/02   BUY   Bitcoin  -950€    Ach2M │
│     [Éditer] [Supprimer]                   │
│                                            │
└────────────────────────────────────────────┘
```

**Filtres disponibles:**
- Par produit
- Par type (DEPOSIT, SELL, etc.)
- Par date (depuis/jusqu'à)

### 5c) Liste des Valorisations

```
┌─────────────────────────────────────────┐
│     LISTE DES VALORISATIONS             │
├─────────────────────────────────────────┤
│                                         │
│ Produit      Date      Prix    Source  │
│──────────────────────────────────────── │
│ SCPI Eurizon 28/02 262.5€   Manuel     │
│              [Éditer] [Supprimer]      │
│                                         │
│ Bitcoin      28/02 47500€   API        │
│              (Lecture seule)            │
│                                         │
│ SCPI Eurizon 15/02 260€     Manuel     │
│              [Éditer] [Supprimer]      │
│                                         │
└─────────────────────────────────────────┘
```

---

## 📄 Page 6: Rapport PDF

Générer un rapport imprimable de votre portefeuille.

### Contenu du Rapport

```
┌────────────────────────────────────┐
│   RAPPORT DE PORTEFEUILLE         │
│   Finance Tracker v1.0.0           │
│   Généré le: 28/02/2024            │
├────────────────────────────────────┤
│                                    │
│ 1. RÉSUMÉ EXÉCUTIF                 │
│    Valeur Totale: 45 000€          │
│    Performance: +13.6%              │
│    Investissement: 39 600€          │
│                                    │
│ 2. ALLOCATION DU PORTEFEUILLE      │
│    [Graphique camembert]            │
│    SCPI: 35%                        │
│    Bitcoin: 40%                     │
│    Autres: 25%                      │
│                                    │
│ 3. DÉTAIL PAR PRODUIT              │
│    SCPI Eurizon                     │
│    ├─ Quantité: 40 parts            │
│    ├─ PRU: 250€/part                │
│    ├─ Prix actuel: 262.5€/part      │
│    ├─ Valeur: 10 500€               │
│    ├─ Gain: +500€ (+5%)             │
│                                    │
│ 4. HISTORIQUE DES TRANSACTIONS     │
│    [Tableau complet]                │
│                                    │
│ 5. ÉVOLUTION TEMPORELLE            │
│    [Graphique valeur dans le temps] │
│                                    │
└────────────────────────────────────┘
```

### Téléchargement

- Format: **PDF** (A4)
- Qualité: Impression prête
- Bouton: "Télécharger PDF"

---

## 📈 Page 7: Simulateur

Projeter la croissance future de votre portefeuille avec intérêts composés.

### Formulaire

```
Simulateur de Croissance
├── Capital Initial: [39600] EUR
├── Rendement annuel: [8] %
├── Années: [20] ans
├── Versements mensuels: [500] EUR (optionnel)
└── [Simuler]
```

### Résultats

```
Projection sur 20 ans:

Sans versements:
  Capital initial: 39 600€
  Valeur à 20 ans: 183 874€
  Gain total: 144 274€

Avec versements de 500€/mois:
  Valeur à 20 ans: 323 156€
  Gain total: 283 556€ (intérêts composés)

Graphique de croissance:
[Courbe exponentielle 1: Capital seul]
[Courbe exponentielle 2: Capital + versements]
```

### Formules Utilisées

Voir [FORMULES_CALCULS.md](./FORMULES_CALCULS.md) pour les détails mathématiques.

---

## ⌨️ Raccourcis Clavier

| Raccourci | Action |
|-----------|--------|
| `F5` | Rafraîchir la page |
| `Ctrl+K` | Commande (selon Streamlit) |
| `Esc` | Fermer modales |

---

## 💡 Conseils d'Utilisation

### Flux Recommandé pour Débuter

1. Aller à **Ajouter Transaction** → DEPOSIT (versement initial)
2. Aller à **Ajouter Transaction** → BUY (acheter des actifs)
3. Aller à **Ajouter Valorisation** (enregistrer les prix)
4. Consulter **Dashboard** pour voir le résumé
5. Générer **PDF** pour imprimer

### Optimisations

- **Mises à jour Bitcoin:** Automatiques, pas d'action requise
- **Refresh du Dashboard:** Clic F5 ou navigation
- **Édition en masse:** Voir CLI_GUIDE.md pour scripts Python

---

## 🔗 Liens Connexes

- [CONCEPTS_FONDAMENTAUX.md](./CONCEPTS_FONDAMENTAUX.md) - Comprendre les piliers
- [CLI_GUIDE.md](./CLI_GUIDE.md) - Utiliser en ligne de commande
- [FORMULES_CALCULS.md](./FORMULES_CALCULS.md) - Mathématiques détaillées
