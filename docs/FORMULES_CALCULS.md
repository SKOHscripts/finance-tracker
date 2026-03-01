# 📐 Formules & Calculs Financiers

> Explications détaillées des formules mathématiques utilisées

---

## 🎯 Vue d'ensemble

Cette page détaille toutes les formules utilisées par Finance Tracker pour calculer les performances, gains, et projections.

---

## 📊 Indicateurs de Performance du Dashboard

### 1. Investissement Net (Invested Amount)

**Définition:** Le montant réel d'argent que vous avez investi (argent entré - argent sorti).

**Formule:**
$$\text{Investissement Net} = \sum_{i=1}^{n} \text{DEPOSIT}_i + \sum_{j=1}^{m} \text{DISTRIBUTION}_j + \sum_{k=1}^{p} \text{SELL}_k - \sum_{l=1}^{q} \text{WITHDRAW}_l - \sum_{r=1}^{s} \text{BUY}_r - \sum_{t=1}^{u} \text{FEE}_t$$

**Simplifiée:**
$$\text{Investissement Net} = \text{(Argent entré)} - \text{(Argent sorti)}$$

**Exemple:**
```
Opérations:
- DEPOSIT:      +10 000€  (versement)
- BUY SCPI:      -2 500€  (achat 10 parts)
- DISTRIBUTION:    +150€  (coupon)
- WITHDRAW:       -500€   (retraite)
- FEE:             -50€   (frais)

Investissement Net = (10000 + 150) - (2500 + 500 + 50)
                   = 10150 - 3050
                   = 7 100€
```

**Interprétation:**
- ✅ Positif: Vous avez plus investi que retiré
- ❌ Négatif: Vous avez retiré plus que vous n'avez investi

---

### 2. Valeur Actuelle (Current Portfolio Value)

**Définition:** La valeur actuelle totale de tous vos actifs selon les dernières valorisations.

**Formule (Par Produit):**
$$\text{Valeur du Produit} = \text{Quantité Possédée} \times \text{Prix Unitaire Actuel}$$

**Formule (Portefeuille Complet):**
$$\text{Valeur Actuelle} = \sum_{i=1}^{n} \text{Quantité}_i \times \text{PrixUnitaire}_i$$

**Exemple Complet:**
```
Produit 1: SCPI Eurizon
  - Quantité: 40 parts
  - Prix actuel: 262.5€/part
  - Valeur: 40 × 262.5 = 10 500€

Produit 2: Bitcoin
  - Quantité: 2 000 000 satoshis
  - Prix actuel: 0.000475€/sat
  - Valeur: 2 000 000 × 0.000475 = 950€

Produit 3: Cash
  - Quantité: 2 500€
  - Prix: 1€ (par convention)
  - Valeur: 2 500€

Valeur Actuelle = 10 500 + 950 + 2 500 = 13 950€
```

**Note Bitcoin:** Les satoshis sont JAMAIS convertis en BTC alors en EUR. La formule reste:
$$\text{Valeur BTC} = \text{Satoshis} \times \text{Prix EUR/Satoshi}$$

Pas de conversion intermédiaire BTC → EUR → ou inversement.

---

### 3. Performance Absolue (Absolute Performance)

**Définition:** Le gain ou la perte en euros.

**Formule:**
$$\text{Performance (€)} = \text{Valeur Actuelle} - \text{Investissement Net}$$

**Exemple:**
```
Valeur Actuelle: 13 950€
Investissement Net: 7 100€

Performance (€) = 13 950 - 7 100 = 6 850€
```

**Interprétation:**
- ✅ Positif (+6 850€): Vous avez gagné 6 850€
- ❌ Négatif: Vous avez une perte latente

---

### 4. Performance Relative (Percentage Return)

**Définition:** Le rendement exprimé en pourcentage.

**Formule:**
$$\text{Performance (\%)} = \frac{\text{Performance (€)}}{\text{Investissement Net}} \times 100$$

**Exemple:**
```
Performance (€): 6 850€
Investissement Net: 7 100€

Performance (%) = (6 850 / 7 100) × 100 = 96.48%
```

**Interprétation:**
- 96.48% : Vous avez un rendement de 96.48% sur votre investissement net
- Cette métrique permet de comparer des portefeuilles de tailles différentes

---

### 5. Gain/Perte Latente par Produit

**Définition:** Le gain ou la perte non réalisés d'un produit spécifique.

**Formule (Produit avec Prix Unitaire):**
$$\text{Gain Latent} = (\text{Prix Actuel} - \text{PRU}) \times \text{Quantité}$$

Où PRU = Prix de Revient Unitaire (voir section suivante)

**Exemple SCPI:**
```
Produit: SCPI Eurizon
  - Quantité possédée: 40 parts
  - PRU: 250€/part (prix moyen d'achat)
  - Prix actuel: 262.5€/part

Gain Latent = (262.5 - 250) × 40
            = 12.5 × 40
            = 500€
```

---

### 6. Prix de Revient Unitaire (PRU)

**Définition:** Le prix moyen d'achat pondéré d'une unité de votre produit.

**Formule:**
$$\text{PRU} = \frac{\sum (\text{Quantité}_i \times \text{Prix}_i)}{\sum \text{Quantité}_i}$$

**Exemple SCPI:**
```
Historique d'achats:
- Transaction 1: 20 parts à 250€/part = 5 000€
- Transaction 2: 20 parts à 260€/part = 5 200€

PRU = (5 000 + 5 200) / (20 + 20)
    = 10 200 / 40
    = 255€/part
```

**Cas Particulier: Bitcoin (sans double conversion)**

Pour Bitcoin, le PRU en EUR/Satoshi:
```
Achats:
- 500 000 sats à 45 000€/BTC (0.00045€/sat) = 225€
- 1 000 000 sats à 46 000€/BTC (0.00046€/sat) = 460€

PRU = (225 + 460) / 1 500 000 sats
    = 685 / 1 500 000
    = 0.000457€/sat
```

---

## 📈 Simulateur: Intérêts Composés

### 1. Formule Classique d'Intérêts Composés

**Définition:** Projection de la croissance exponentielle d'un capital sur N années.

**Formule (Capital seul):**
$$\text{VF} = \text{VP} \times (1 + r)^n$$

Où:
- **VF** = Valeur Future
- **VP** = Valeur Présente (capital initial)
- **r** = Rendement annuel (en décimal)
- **n** = Nombre d'années

**Exemple:**
```
Capital initial: 10 000€
Rendement annuel: 8%
Durée: 10 ans

VF = 10 000 × (1 + 0.08)^10
   = 10 000 × 2.1589
   = 21 589€

Gain: 21 589 - 10 000 = 11 589€ (+115.89%)
```

---

### 2. Avec Versements Mensuels Réguliers

**Définition:** Projection avec apports mensuels constants (l'effet "boule de neige").

**Formule:**
$$\text{VF} = \text{VP} \times (1 + r)^n + V \times \left[\frac{(1 + r)^n - 1}{r}\right] \times (1 + r)$$

Où:
- **V** = Versement mensuel
- **r** = Rendement mensuel = Rendement annuel / 12
- **n** = Nombre total de mois

**Exemple:**
```
Capital initial: 10 000€
Rendement annuel: 8%  (0.667% mensuel)
Versements mensuels: 500€
Durée: 10 ans (120 mois)

Rendement mensuel: r = 0.08 / 12 = 0.00667

Partie 1 (Capital):
  10 000 × (1.00667)^120 = 21 589€

Partie 2 (Versements):
  500 × [((1.00667)^120 - 1) / 0.00667] × 1.00667
  = 500 × 162.88 × 1.00667
  = 81 824€

VF Total = 21 589 + 81 824 = 103 413€

Investissement total = 10 000 + (500 × 120) = 70 000€
Gain: 103 413 - 70 000 = 33 413€ (+47.73%)
```

---

### 3. Tableau de Croissance Temporelle

**Définition:** Affichage année par année (ou mois par mois) de la progression.

**Formule pour l'année N:**
$$\text{VF}_N = \text{VP} \times (1 + r)^N + V \times \left[\frac{(1 + r)^N - 1}{r}\right] \times (1 + r)$$

**Exemple (tableau 10 ans, capital seul):**
```
Année | Capital Initial | Croissance | Valeur Cumulative
───────────────────────────────────────────────────────
  0   |    10 000€     |     0€     |     10 000€
  1   |    10 000€     |    +800€   |     10 800€
  2   |    10 000€     |    +864€   |     11 664€
  3   |    10 000€     |    +933€   |     12 597€
  4   |    10 000€     |   +1 008€  |     13 605€
  5   |    10 000€     |   +1 088€  |     14 693€
  6   |    10 000€     |   +1 175€  |     15 868€
  7   |    10 000€     |   +1 269€  |     17 138€
  8   |    10 000€     |   +1 371€  |     18 509€
  9   |    10 000€     |   +1 481€  |     19 990€
 10   |    10 000€     |   +1 599€  |     21 589€
```

**Observation:** La croissance s'accélère chaque année (effet composé).

---

## 💰 Cas Spéciaux: Bitcoin

### 1. Gestion des Satoshis

**Rappel:** 1 BTC = 100 000 000 satoshis

**Aucune conversion intermédiaire!**

Les satoshis se gèrent directement en EUR sans passer par une valeur BTC intermédiaire.

**Formule:**
$$\text{Valeur BTC (EUR)} = \text{Satoshis} \times \text{Prix (EUR/Satoshi)}$$

**Exemple:**
```
Vous possédez: 2 000 000 satoshis (0.02 BTC)
Prix BTC/EUR: 47 500€
Prix par satoshi: 47 500 / 100 000 000 = 0.000475€/sat

Valeur = 2 000 000 × 0.000475 = 950€
```

**PAS de conversion intermédiaire:**
```
❌ FAUX:  2 000 000 sats → 0.02 BTC → 0.02 × 47 500 EUR
✅ CORRECT: 2 000 000 × 0.000475 EUR
```

---

### 2. PRU Bitcoin Détaillé

**Exemple Multiple Achats:**
```
Achat 1: 500 000 sats à 45 000€/BTC
  Price/sat = 45 000 / 100M = 0.00045€/sat
  Cost = 500 000 × 0.00045 = 225€

Achat 2: 1 000 000 sats à 46 000€/BTC
  Price/sat = 46 000 / 100M = 0.00046€/sat
  Cost = 1 000 000 × 0.00046 = 460€

Achat 3: 500 000 sats à 47 000€/BTC
  Price/sat = 47 000 / 100M = 0.00047€/sat
  Cost = 500 000 × 0.00047 = 235€

Total Satoshis: 500K + 1M + 500K = 2 000 000 sats
Total Cost: 225 + 460 + 235 = 920€

PRU = 920 / 2 000 000 = 0.00046€/sat
```

---

## 🧮 Formules de Distributions

### SCPI: Coupon Semestriel

**Définition:** Rendement versé aux propriétaires de parts.

**Exemple:**
```
Vous possédez: 40 parts de SCPI Eurizon
Coupon semestriel par part: 3.75€

Distribution = 40 × 3.75€ = 150€
```

**Impact:**
- L'investissement net augmente de 150€
- Aucun changement de quantité
- Le cash disponible augmente

---

### Bitcoin: Aucune Distribution

**Particularité:** Bitcoin n'a pas de dividendes ou coupons. Aucune transaction DISTRIBUTION pour Bitcoin.

---

## 🔄 Formules de Vente & Gains Réalisés

### Gain Réalisé à la Vente

**Définition:** Le gain/perte quand vous vendez une partie de vos actifs.

**Formule:**
$$\text{Gain Réalisé} = \text{Prix Vente Total} - \text{Prix Achat Total Vendu}$$

Où le prix d'achat utilise le PRU.

**Exemple:**
```
Vous vendez 5 parts SCPI:
- PRU: 255€/part
- Prix Vente: 260€/part
- Quantité: 5 parts

Prix Achat Total (PRU): 5 × 255 = 1 275€
Prix Vente Total: 5 × 260 = 1 300€

Gain Réalisé = 1 300 - 1 275 = 25€
```

**Note:** Ce gain est intégré dans l'Investissement Net car SELL enregistre un flux positif.

---

## 📊 Récapitulatif des Formules Clés

| Indicateur | Formule | Utilité |
|-----------|---------|---------|
| **Inv. Net** | ∑ Entrées - ∑ Sorties | Capital réellement investi |
| **Valeur** | ∑ (Qtté × Prix) | Richesse actuelle |
| **Performance €** | Valeur - Inv. Net | Gain/Perte brut |
| **Performance %** | (Perf € / Inv. Net) × 100 | Rendement comparable |
| **PRU** | ∑ (Qtté × Prix) / ∑ Qtté | Prix moyen d'achat |
| **Gain Latent** | (Prix Actuel - PRU) × Qtté | Gain non réalisé |
| **Composé** | VP × (1+r)^n | Croissance exponentielle |
| **Composé + Versements** | Capital + Versements Composés | Projection réaliste long terme |

---

## ⚠️ Limites & Hypothèses

1. **Rendements constants:** Le simulateur suppose un rendement annuel constant (simplifié)
2. **Pas de fiscalité:** Les calculs ne tiennent pas compte des impôts ou frais supplémentaires
3. **Valeurs discrètes:** Les valorisations sont des snapshots (pas continu)
4. **Arrondi:** Les calculs affichent 2 décimales maximum

---

## 🚀 Évolutions Futures (V0.2.0+)

- ✨ **TRI / XIRR:** Prise en compte du timing réel des cash-flows
- 📊 **Dividendes Réinvestis:** Simulation du réinvestissement automatique
- 🌍 **Multi-Devise:** Gestion EUR/USD/GBP avec conversions
- 🏛️ **Fiscalité:** Calcul des impôts selon régime français

---

## 🔗 Liens Connexes

- [CONCEPTS_FONDAMENTAUX.md](./CONCEPTS_FONDAMENTAUX.md) - Concepts clés
- [INTERFACE_WEB.md](./INTERFACE_WEB.md) - Utilisation web
- [BASE_DONNEES.md](./BASE_DONNEES.md) - Structure des données
