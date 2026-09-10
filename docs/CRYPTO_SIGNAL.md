# 📡 Signal Crypto & Suivi de Portefeuilles

> Arbitrage de positions crypto contre le classement du marché, sur des règles
> écrites à l'avance, et suivi automatique des soldes depuis des adresses
> publiques.

> ⚠️ **Ceci n'est pas un conseil en investissement.** Outil éducatif.
> Lis [DISCLAIMER.md](./DISCLAIMER.md) avant d'agir sur quoi que ce soit.

---

## 📑 Table des matières

- [Le principe](#le-principe)
- [Les cinq verdicts](#les-cinq-verdicts)
- [Les quatre mécanismes](#les-quatre-mécanismes)
- [Le régime de marché](#le-régime-de-marché)
- [Le score et le candidat](#le-score-et-le-candidat)
- [Le coût d'un mouvement](#le-coût-dun-mouvement)
- [Les portefeuilles suivis](#les-portefeuilles-suivis)
- [Le prix de revient reconstitué](#le-prix-de-revient-reconstitué)
- [Mise en route](#mise-en-route)
- [En ligne de commande](#en-ligne-de-commande)
- [Régler les seuils](#régler-les-seuils)
- [Le playbook d'actualité](#le-playbook-dactualité)
- [Ce que le moteur ne fait pas](#ce-que-le-moteur-ne-fait-pas)

---

## Le principe

Le moteur ne prédit rien. Il applique des **règles asymétriques** à des
métriques rétrospectives :

- récupérer la mise quand le gain est là ;
- couper quand le prix décroche de son plus haut ;
- refuser d'acheter dans un marché baissier constaté.

Aucune de ces règles ne demande de savoir ce qui va se passer. C'est
volontaire : c'est la seule catégorie de règles dont on peut vérifier
qu'elle fonctionne.

Chaque position est arbitrée **indépendamment des autres**, contre le même
candidat, avec son propre montant et donc son propre coût de mouvement. Un
verdict par ligne, jamais un verdict unique pour l'ensemble.

---

## Les cinq verdicts

| Verdict | Quand | Effet |
|---|---|---|
| **Conserver** | Le cas par défaut, et le plus fréquent | Rien ne bouge |
| **Rotation** | Les six barrières de rotation passent | Swap vers le candidat du classement |
| **Temporiser** | Aucune rotation ne passe, le marché est dégradé, les six barrières de temporisation passent | Aller simple vers un stablecoin |
| **Alléger** | La plus-value dépasse le seuil, une seule fois par ligne | Vente partielle qui rend le capital investi |
| **Sortie stop** | Ligne en gain, décrochée de son plus haut au-delà du seuil | Sortie complète vers le refuge |

L'ordre de priorité est fixe et il compte :

```
Sortie stop  >  Alléger  >  Rotation  >  Temporiser  >  Conserver
```

Protéger le capital passe avant d'encaisser. Encaisser passe avant de courir
après un autre actif.

Le verdict global affiché en haut d'un scan n'est qu'un **résumé** : il porte
l'action la plus engageante présente sur une ligne. Ce n'est pas le verdict du
portefeuille.

---

## Les quatre mécanismes

### 1. La rotation — six barrières

Toutes doivent passer.

| Barrière | Seuil par défaut | Ce qu'elle empêche |
|---|---|---|
| Écart de score | 1,5 écart-type | Bouger pour une différence de bruit |
| Avantage momentum vs coût | 2× le coût aller-retour | Payer deux jambes pour un gain marginal |
| Volatilité du candidat | 110 % annualisé max | Sauter dans un actif ingérable |
| Drawdown du candidat | -45 % max sur 90j | Acheter quelque chose de cassé |
| Liquidité du candidat | 275 M € de volume 24h | Entrer dans un actif dont on ne sort pas |
| Persistance | 3 scans consécutifs | Réagir à un pic d'une semaine |

La persistance ne compte un scan que si **toutes les autres barrières passent ce
jour-là**. Un candidat qui clignote n'accumule jamais de série. Changer de
candidat remet le compteur à zéro.

Quand la lecture de régime est active, une septième barrière s'ajoute : un
marché en `BEAR` bloque toutes les rotations.

### 2. Le stop suiveur

Sortie complète vers le refuge quand une ligne **en gain** décroche de plus de
30 % de son plus haut sur 180 jours.

Sur une ligne **en perte**, il ne fait rien : c'est la temporisation de régime
qui décide. Le stop protège un gain, il ne juge pas la suite.

Exige un capital investi connu.

### 3. La prise de bénéfice

Au-delà de 100 % de plus-value latente, vend **la fraction qui rend le capital
investi net de frais**, et rien de plus. Le reste continue de rouler, protégé
par le stop suiveur.

Plafonnée à 60 % de la ligne : ce mécanisme récupère une mise, il ne liquide
jamais une position. Une seule fois par ligne.

Exige un capital investi connu.

### 4. La temporisation — six barrières

Évaluée **seulement** quand aucune rotation ne passe et que l'actif détenu n'est
pas déjà un refuge. Sortir vers un stable alors qu'un candidat valide existe
reviendrait à payer une jambe pour rien.

| Barrière | Seuil par défaut |
|---|---|
| Momentum 90j de la position | -12 % ou pire |
| Drawdown 90j de la position | -30 % ou pire |
| Part du classement en momentum négatif | 60 % minimum, ou régime `BEAR` |
| Baisse constatée vs coût aller simple | 1,5× le coût |
| Liquidité du refuge | 275 M € de volume 24h |
| Persistance | 2 scans consécutifs |

La sortie du refuge n'a **aucune règle propre** : on n'en sort que par les six
barrières de rotation. Un stablecoin a un momentum nul, c'est donc la barrière
d'avantage momentum qui fait le tri, pas l'écart de score.

---

## Le régime de marché

Deux mesures indépendantes :

1. **Le bitcoin au-dessus ou sous sa moyenne 200 jours.**
2. **La part du classement en momentum 90j positif** (seuil : 50 %).

| Les deux favorables | Une seule | Aucune |
|---|---|---|
| `BULL` | `MIXTE` | `BEAR` |

En `BEAR`, les rotations sont bloquées et la barrière de marché de la
temporisation est satisfaite. C'est la traduction mécanique de « surfer le bull,
temporiser le bear ».

Quand l'historique est trop court pour lire la moyenne longue, l'état vaut
`INCONNU` et la barrière de régime ne s'applique pas. Le moteur préfère ne rien
dire plutôt que deviner.

---

## Le score et le candidat

Le score composite mélange trois z-scores calculés **sur le classement du
jour** :

```
score = 0,5 × z(momentum 90j) + 0,3 × z(momentum 30j) − 0,2 × z(volatilité 30j)
```

La volatilité est soustraite : à momentum égal, l'actif qui y est arrivé le plus
calmement gagne.

Le fait que ce soient des z-scores compte : un choc macro qui déplace tout le
marché dans le même sens **s'annule de lui-même**. Le score répond à « lequel de
ceux-là fait mieux que les autres », jamais à « le marché monte-t-il ».

Le **candidat** est le mieux classé non détenu qui passe les trois filtres
intrinsèques — volatilité, drawdown, volume. Si le leader échoue, le moteur
descend au suivant, et le rapport dit lequel a été écarté et pourquoi.

Sans ce repli, un leader très volatil resterait candidat chaque semaine,
échouerait chaque semaine, et bloquerait toute rotation vers le suivant. Le
comportement se désactive avec `gates.use_fallback_candidate = false`.

Les stablecoins et les wrappers sont exclus du classement : un peg n'a pas de
momentum exploitable, et un wrapper est l'actif sous-jacent une deuxième fois.

---

## Le coût d'un mouvement

Les frais de chaîne sont **fixes en euros**. Ils pèsent donc proportionnellement
plus lourd sur une petite ligne :

| Montant de la ligne | Aller-retour | Aller simple |
|---|---|---|
| 1 000 € | 5,10 % | 2,55 % |
| 400 € | 6,75 % | 3,38 % |
| 100 € | 15,00 % | 7,50 % |

La barrière `avantage_momentum_vs_cout` exige **le double** de ces chiffres. Sur
une ligne de 100 €, il faut donc 30 % d'avantage pour justifier un mouvement.

Ce n'est pas une pénalité arbitraire, c'est le coût réel.

**Le point le plus important de toute cette page :** l'écart entre le meilleur et
le pire fournisseur sur une même route est régulièrement de plusieurs pourcents.
Comparer les devis change davantage ton résultat que choisir le bon actif. Voir
[`playbook/routes-swap.md`](./playbook/routes-swap.md).

---

## Les portefeuilles suivis

Ajoute une adresse publique, et l'outil lit les soldes qu'elle détient. Ces
soldes alimentent les quantités des produits que tu leur associes, et donc le
moteur de signal.

| Chaîne | Soldes | Historique | Clé nécessaire |
|---|---|---|---|
| Ethereum, Base, Arbitrum, Optimism, Polygon, BSC | ✅ | ✅ | Clé d'explorateur gratuite |
| Bitcoin | ✅ | ✅ | Aucune |
| Solana | ✅ | ❌ | Aucune |
| **Monero** | ❌ | ❌ | *Impossible* |

**Monero ne peut pas être lu depuis une adresse seule.** C'est le principe même
du protocole : sans clé de vue, une adresse XMR ne révèle rien. Ces positions se
saisissent à la main — section « Ajouter un actif sans adresse » de la même
page, décrite en [Mise en route](#1-associer-un-produit-à-une-cotation) — et
c'est très bien ainsi.

**Solana : soldes seulement.** Reconstituer l'historique demanderait de parcourir
les signatures et de décoder chaque instruction, soit des centaines d'appels
contre un point d'accès public limité, pour un résultat moins fiable qu'une
saisie manuelle.

### Vie privée

Interroger un indexeur **révèle ton adresse** à celui qui l'exploite. Trois
garde-fous :

1. La synchronisation s'active **par portefeuille**. Une adresse enregistrée
   sans synchronisation n'est jamais envoyée nulle part.
2. Tu peux pointer l'outil vers **ton propre nœud** (Bitcoin et Solana) plutôt
   que vers un service public.
3. Rien n'est jamais envoyé à un serveur de Finance Tracker : il n'y en a pas.

### Ce qu'une synchronisation écrase, et ce qu'elle préserve

Les soldes et les mouvements appartiennent à la chaîne : ils sont rafraîchis
intégralement. Un solde disparu on-chain disparaît ici.

**Tout ce que tu as décidé survit** : l'association d'un solde à un produit, le
marquage d'un token en poussière, une correction de prix de revient.

---

## Le prix de revient reconstitué

Une chaîne enregistre des **mouvements**, jamais un **prix d'achat**. Ce que
l'outil calcule est donc une reconstitution, par moyenne mobile :

- une **acquisition** — des unités arrivant d'une adresse que tu ne suis pas —
  est valorisée au cours du jour du bloc, et augmente le capital ;
- une **cession** — des unités partant vers une adresse que tu ne suis pas —
  retire le **coût moyen** des unités vendues, pas leur prix de vente ;
- un mouvement **interne**, entre deux adresses que tu suis, ne change rien.

### Trois erreurs structurelles

Aucune n'est corrigeable depuis les données on-chain :

1. **Un swap ressemble à une acquisition.** Échanger A contre B apparaît comme
   B qui arrive. Son vrai prix de revient est celui de A, qui vit sur une autre
   ligne.
2. **Un virement depuis un de tes propres portefeuilles non suivis compte comme
   un achat.** Ajoute ce portefeuille et le mouvement se reclasse tout seul.
3. **Les cours s'arrêtent à un an.** Le plan gratuit ne sert pas plus loin. Ces
   unités sont comptées comme non expliquées.

### L'indice de confiance

| Indice | Signification |
|---|---|
| 🟢 élevée | 95 % des unités rattachées à une acquisition valorisée |
| 🟡 moyenne | 60 % au moins, ou un historique tronqué |
| 🟠 faible | Large part d'unités sans origine valorisée |
| ⚪ aucune | Rien n'a pu être reconstitué |

Un historique tronqué **ne peut jamais** donner une confiance élevée, quel que
soit le ratio : ce ratio lui-même a été calculé sur un enregistrement partiel.

### Ta valeur gagne toujours

Une correction manuelle remplace l'estimation **partout**, y compris dans le
moteur. Une resynchronisation ne l'écrase jamais.

C'est important : le stop suiveur et la prise de bénéfice se déclenchent sur la
plus-value, donc sur le prix de revient. Une sortie déclenchée sur un chiffre
deviné est une sortie sur une hypothèse.

---

## Mise en route

### 1. Associer un produit à une cotation

Deux chemins.

**Depuis un portefeuille** (le plus simple) : page **👛 Portefeuilles Crypto**,
ajoute une adresse, synchronise, puis « Créer » à côté d'un solde découvert.
Produit, cotation et association sont créés en une fois.

**À la main**, pour un avoir qu'aucune adresse ne peut révéler : même page,
section **« Ajouter un actif sans adresse »**. Cherche la cotation par nom ou
par symbole, choisis-la dans la liste, puis renseigne la quantité et le prix de
revient.

La cotation se choisit dans une liste plutôt que se tape, et ce n'est pas du
confort : **un symbole n'est pas unique**. Plusieurs jetons répondent à trois
mêmes lettres, et un identifiant choisi de travers ne signale rien — il price
simplement un autre actif à chaque scan. Le rang de capitalisation affiché à
côté de chaque résultat est là pour départager.

Deux choses à savoir sur la saisie :

- **La quantité est en unités natives** — XMR, BTC, ETH — jamais en satoshis ni
  en wei. C'est ce que le moteur multiplie par un cours.
- **Le prix de revient peut rester vide.** Un airdrop ou du minage n'a pas de
  prix d'achat. Le moteur traite alors le capital investi comme *inconnu* et
  désactive le stop suiveur sur cette ligne, au lieu de lire l'absence comme un
  gain total.

Quantité et prix de revient sont enregistrés **comme un achat dans le journal**,
pas dans un champ à part. Ils restent donc modifiables depuis la page
Transactions, comme pour n'importe quel produit, et alimentent le tableau de
bord comme le reste.

### 2. Renseigner le capital investi

Sans lui, ni stop suiveur ni prise de bénéfice. Trois sources, par ordre de
préférence :

1. ta saisie manuelle ;
2. tes transactions d'achat en base ;
3. l'estimation reconstituée depuis la chaîne.

### 3. Lancer un scan

Page **📡 Signal Crypto**, bouton *Lancer un scan*. Vérifie d'abord le tableau
« Ce qui sera arbitré » : un verdict ne vaut que ce que valent ses entrées.

### 4. Attendre

La première semaine ne produira aucun mouvement, quelle que soit la force du
signal : la barrière de persistance exige trois scans consécutifs. C'est le but.

---

## En ligne de commande

```bash
# Vérifier ce qui sera arbitré, et d'où viennent les chiffres
finance-tracker crypto-positions

# Lancer un scan
finance-tracker crypto-scan
finance-tracker crypto-scan --json > state/latest_scan.json
finance-tracker crypto-scan --dry-run    # n'enregistre rien, n'avance aucune série

# Relire l'historique
finance-tracker crypto-history

# Synchroniser les portefeuilles et recalculer les prix de revient
finance-tracker wallet-sync
```

Un scan hebdomadaire par cron, le dimanche à 9 h :

```cron
0 9 * * 0 cd /chemin/vers/finance-tracker && finance-tracker crypto-scan >> state/scan.log 2>&1
```

`--dry-run` n'enregistre rien, donc **ne fait progresser aucune série de
persistance**. Utile pour explorer un réglage, pas pour un scan de routine.

---

## Régler les seuils

Tout est dans [`config/signal_rules.toml`](../config/signal_rules.toml). Ce
fichier ne contient **que des règles** : aucune position, aucun montant, aucune
adresse. C'est ce qui permet à ce dépôt d'être public.

Une clé mal orthographiée est **rejetée au chargement** avec un message qui
nomme le coupable, plutôt que de garder silencieusement sa valeur par défaut.

Fais chaque changement de seuil dans un **commit dédié qui explique pourquoi**.
Dans six mois, le chiffre seul ne dira plus rien.

> **Ne modifie jamais un seuil pour faire passer un mouvement que les barrières
> refusent.** C'est exactement ce que les barrières sont là pour empêcher.

---

## Le playbook d'actualité

[`docs/playbook/`](./playbook/) relie un type d'information à une trajectoire de
marché constatée : réglementaire et accès, contrepartie et sécurité, protocole
et chaîne, macro.

C'est un **outil de développement**, pas une fonction de l'application : il
s'utilise depuis Claude Code, via `/news-scan` puis
`scripts/apply_news_veto.py`.

Un veto ne déclenche **jamais** un mouvement. Il ne fait que le suspendre.
L'asymétrie est le principe : une information peut retenir la main, jamais la
forcer.

Deux garde-fous. Un drapeau ne suspend rien tant qu'il n'est pas approuvé
manuellement. Et aucune règle ne porte sur le domaine macro, parce qu'un choc
macro déplace tout le classement dans le même sens et s'annule déjà dans les
z-scores.

---

## Ce que le moteur ne fait pas

- **Il ne prédit aucun prix.** Voir [DISCLAIMER.md](./DISCLAIMER.md).
- **Il n'exécute rien.** Aucune clé, aucune signature, aucun ordre.
- **Il ne connaît pas ta situation.** Ni tes objectifs, ni ton horizon, ni ta
  tolérance au risque.
- **Il ne calcule aucun impôt.** Un swap est généralement imposable ; l'outil
  l'ignore complètement.
- **Il ne fusionne jamais deux positions** dans un même plan : les montants et
  les minimums acceptables diffèrent d'une ligne à l'autre.

---

## 🔗 Liens

- [DISCLAIMER.md](./DISCLAIMER.md) — portée et limites, à lire en entier
- [BASE_DONNEES.md](./BASE_DONNEES.md) — les tables et les migrations
- [playbook/README.md](./playbook/README.md) — le playbook d'actualité
- [config/signal_rules.toml](../config/signal_rules.toml) — tous les seuils
