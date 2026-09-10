# 🔮 Roadmap & Évolutions Futures

> Planification des développements futurs

---

## 🎯 Vision Générale

Finance Tracker évolue progressivement d'une solution simple de suivi vers une **plateforme complète de gestion patrimoniale intelligente**.

### Principes Directeurs
- 📊 **Précision:** Calculs financiers avancés et exacts
- 🎯 **Contrôle:** L'utilisateur garde la maîtrise totale de ses données
- 📈 **Pédagogie:** Comprendre le pouvoir des intérêts composés
- 🔒 **Confidentialité:** Données locales, aucun cloud requis
- ⚡ **Simplicité:** Interface intuitive malgré la complexité

---

## 📅 Roadmap Détaillée

### ✅ V1.0.0 (Version Actuelle)

**Statut:** ✅ Disponible

**Fonctionnalités implémentées:**

#### Core Features
- ✅ Gestion de 3 piliers: Produits, Transactions, Valorisations
- ✅ 6 types de transactions (DEPOSIT, WITHDRAW, BUY, SELL, DISTRIBUTION, FEE)
- ✅ Base SQLite locale avec intégrité referentielle
- ✅ Dashboard avec 5 KPIs (Valeur, Performance, Investi, Cash, Allocation)

#### Web UI (Streamlit)
- ✅ Dashboard synthétique
- ✅ Ajout transactions et valorisations
- ✅ Suivi spécialisé Bitcoin (API CoinGecko)
- ✅ Listes & CRUD complet
- ✅ Export PDF imprimable
- ✅ Simulateur d'intérêts composés simples

#### CLI (Terminal)
- ✅ Initialisation BD (`init-db`, `seed-products`)
- ✅ Ajout données (`add-transaction`, `add-valuation`)
- ✅ Consultations (`dashboard`, `list-*`)
- ✅ Gestion Bitcoin (`update-btc`)
- ✅ Projections financières (`project`)
- ✅ Maintenance (`backup-db`, `validate-db`)

#### Quality
- ✅ Tests unitaires avec Pytest (>80% coverage)
- ✅ Linting (Ruff)
- ✅ Formatage (Black)
- ✅ Type checking (Mypy)
- ✅ Documentation complète (7 fichiers Markdown)

---

### ✅ V1.1.0 — Signal crypto & portefeuilles

**Statut:** ✅ Livré

- ✅ **Migrations de schéma versionnées** — une base exportée par une version
  antérieure reste utilisable ; c'est le prérequis de tout le reste
- ✅ **Moteur de rotation crypto** — quatre mécanismes, barrières explicites,
  chaque verdict accompagné du chiffre qui l'a produit
- ✅ **Régime de marché** — deux mesures indépendantes, bull / mixte / bear
- ✅ **Suivi de portefeuilles** — Bitcoin, Solana, six chaînes EVM
- ✅ **Prix de revient reconstitué** depuis l'historique on-chain, avec indice de
  confiance et correction manuelle prioritaire
- ✅ **Avertissement** sur chaque page produisant un verdict et chaque plan de swap
- ✅ Commandes CLI : `crypto-scan`, `crypto-positions`, `crypto-history`,
  `wallet-sync`

**Limites assumées:** Monero illisible depuis une adresse seule (principe du
protocole) ; historique Solana non reconstitué ; tout prix de revient dérivé
d'une chaîne est une estimation.

---

### 🚀 V?

**Focus:** Calculs Avancés & Automatisation

#### Calculs Financiers
- ⏳ **TRI / XIRR** (Taux de Rendement Interne)
  - Prise en compte du timing exact des cash-flows
  - Calcul du rendement "réel" vs rendement simple
  - Comparaison avec indices de marché

- 🎯 **Allocations Cibles**
  - Alertes de dérive (ex: BTC dépasse 50%)
  - Recommandations de rééquilibrage

#### Automatisation & Imports
- 📥 **Import CSV**
  - Parser fichiers CSV de courtiers
  - Mapping automatique de colonnes
  - Import en masse des transactions

- 🔗 **Synchronisation Courtiers**
  - API Boursorama (stock français)
  - API Interactive Brokers (actions US)
  - API Revolut (crypto brutes)
  - Synchronisation quotidienne

- ⏰ **Tâches Programmées**
  - Mise à jour automatique des prix
  - Génération rapports mensuels
  - Alertes personnalisées

#### Interface Web
- 📊 Graphiques de volatilité / corrélations
- 🏠 Dashboard amélioré avec plus d'indicateurs
- ⚙️ Panneau de configuration personnalisé

---

### 🎯 V?

**Focus:** Multi-Portefeuille & Gestion Fiscale

#### Multi-Portefeuille
- 👥 **Plusieurs Portefeuilles**
  - Portefeuille Personnel vs Professionnel
  - Portefeuille Conjoint
  - Héritages séparés
  - Vue consolidée

- 📱 **Partage & Permissions**
  - Lecture seule pour conseiller
  - Édition limitée pour conjoint
  - Chiffrement des données sensibles

#### Gestion Fiscale
- 🏛️ **Calcul des Impôts**
  - Impôt sur les plus-values
  - Prélèvement forfaitaire
  - Déclaration 2086-TER (SCPI)
  - Export données fiscales

- 💰 **Optimisation Fiscale**
  - Suggestions prise de pertes
  - Planification fiscale annuelle
  - Projeção impact fiscal

- 📄 **Rapports Fiscaux**
  - Export données pour comptable
  - Formulaires pré-remplis
  - Historique des déclarations

#### Notifications & Alertes
- 🔔 **Alertes Intelligentes**
  - Distribution reçue (date approximative)
  - Rééquilibrage nécessaire
  - Performance anormale
  - Notif email / SMS / Telegram

---

### 🌟 V?

**Focus:** Plateforme Complète

#### Analyse
- 📊 **Backtesting du signal**
  - Rejouer les barrières sur l'historique de marché
  - Mesurer ce qu'un jeu de seuils aurait donné
  - Comparer plusieurs calibrages sur la même période

> ⚠️ **Pas de prédiction de prix.** Ce n'était pas un oubli de roadmap : aucun
> mécanisme de cet outil n'anticipe une hausse ou une baisse, parce que personne
> ne sait le faire de façon fiable et qu'un outil qui prétend le contraire fait
> perdre de l'argent avec assurance. Voir [DISCLAIMER.md](./DISCLAIMER.md).

#### Multi-Devise
- 🌍 **Support Complet**
  - Gestion EUR, USD, GBP, JPY
  - Conversion réelle (historique des taux)
  - Rapports multi-devise

#### Collaboration
- 👨‍👩‍👧 **Partage Avancé**
  - Partage de portefeuille famille
  - Collaboration conseiller/client

---

## 🛠️ Architecture Évolutive

### Design Patterns Pour Scale

```
Couche Présentation
├── Web (Streamlit)
├── CLI (Typer)
└── Mobile (Flutter)

Couche API
├── REST (FastAPI)
├── GraphQL (optionnel)
└── WebSocket (real-time)

Couche Métier
├── Services
├── Calculs
├── Validations
└── Règles Métier

Couche Données
├── SQLite (local)
├── PostgreSQL (optionnel)
└── Cache (Redis)
```
---

## 💡 Idées Futures (Long Terme)

### Analyse Avancée
- 📊 Backtesting de stratégies
- 🎲 Monte Carlo simulations
- 🔄 Corrélations actifs
- 📈 Efficient frontier (Markowitz)

### Intégrations
- 🏦 Open Banking (PSD2)
- 🔗 Blockchain (NFT, DeFi)
- 📡 IoT (prix en temps réel)
- 🌐 APIs décentralisées

### Communauté
- 👥 Benchmarking social
- 💬 Forum utilisateurs
- 📚 Tutoriels vidéo
- 🎓 Cours financiers intégrés

---

## 🤝 Comment Contribuer à la Roadmap

### Reporter une Bug
1. Aller à [Issues GitHub](https://github.com/SKOHscripts/finance-tracker/issues)
2. Cliquer "New Issue"
3. Décrire le problème avec:
   - Étapes de reproduction
   - Comportement attendu
   - Screenshots si pertinent

### Proposer une Fonctionnalité
1. Aller à [Issues GitHub](https://github.com/SKOHscripts/finance-tracker/issues)
2. Catégorie "Feature Request"
3. Expliquer:
   - Cas d'usage
   - Bénéfices
   - Exemples d'utilisation

### Contribuer du Code
1. Fork le dépôt
2. Créer branche feature: `git checkout -b feature/awesome-feature`
3. Commit: `git commit -m 'Add awesome feature'`
4. Push: `git push origin feature/awesome-feature`
5. Ouvrir Pull Request

---

## 📊 Métriques de Succès

### Qualité
- [ ] Couverture tests: ≥90%
- [ ] 0 bugs critiques
- [ ] Documentation: 100% complet

---

## 🗣️ Communication

### Canaux
- 📧 **Email:** Contact via GitHub

### Fréquence des Updates
- 📌 Version majeure: Quand je peux
- 🔧 Version mineure: Quand je peux
- 🐛 Bugfixes: Quand je peux

---

## 🎉 Merci pour Votre Intérêt!

Finance Tracker est un projet communautaire. Vos suggestions, bug reports et contributions façonnent le futur de l'application.

**Ensemble, rendons la gestion patrimoniale accessible et transparente! 🚀** Enlevons les tabous sur la gestion financière et rendons la gestion budgétaire démocratisée.

---

## 🔗 Liens Connexes

- [README.md](../README.md) - Vue d'ensemble générale
- [CONCEPTS_FONDAMENTAUX.md](./CONCEPTS_FONDAMENTAUX.md) - Comprendre les piliers
- [INSTALLATION_SETUP.md](./INSTALLATION_SETUP.md) - Guide d'installation
