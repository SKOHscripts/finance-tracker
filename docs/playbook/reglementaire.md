# Reglementaire et acces

Delistages, restrictions par juridiction, approbations d'instruments, enquetes.

Le domaine le plus directement lie a une position en XMR sur wallet
auto-heberge : il ne touche pas au prix seul, il touche a la capacite de sortir.

Les fiches marquees `approuve` ci-dessous viennent de `docs/playbook/routes-swap.md`,
document fourni et date par toi. Leur occurrence n'est pas en doute. Leur
magnitude reste a mesurer : le veto se declenche sur le type d'evenement, pas
sur son amplitude. L'amplitude sert plus tard, a recalibrer les durees.

### okx-retrait-xmr-2024

- Date : 2024-01-05
- Categorie : reglementaire.delistage
- Portee : monero
- Statut : approuve
- Source : docs/playbook/routes-swap.md

OKX retire les paires XMR. Premier des trois retraits majeurs de 2024, qui
ferment ensemble l'acces au carnet d'ordres depuis l'Europe.

| Fenetre | Absolu | Relatif BTC |
|---------|--------|-------------|
| J+1     |        |             |
| J+7     |        |             |
| J+30    |        |             |

Trajectoire retenue : a mesurer.

### binance-delistage-xmr-2024

- Date : 2024-02-20
- Categorie : reglementaire.delistage
- Portee : monero
- Statut : approuve
- Source : docs/playbook/routes-swap.md

Binance delistait XMR mondialement. Retrait du plus gros carnet d'ordres
disponible sur la paire.

| Fenetre | Absolu | Relatif BTC |
|---------|--------|-------------|
| J+1     |        |             |
| J+7     |        |             |
| J+30    |        |             |

Trajectoire retenue : a mesurer.

### kraken-retrait-eee-2024

- Date : 2024-10-31
- Categorie : reglementaire.restriction_juridiction
- Portee : monero
- Statut : approuve
- Source : docs/playbook/routes-swap.md

Kraken retire XMR sur toute la zone EEE, apres l'Irlande et la Belgique en juin
2024. Le retrait se poursuit au Canada et en Inde en avril 2026.

| Fenetre | Absolu | Relatif BTC |
|---------|--------|-------------|
| J+1     |        |             |
| J+7     |        |             |
| J+30    |        |             |

Trajectoire retenue : a mesurer.

### mica-amlr-montee-en-charge

- Date : 2027-07-01
- Categorie : reglementaire.restriction_juridiction
- Portee : marche
- Statut : approuve
- Source : docs/playbook/routes-swap.md

L'AMLR monte en charge jusqu'au 1er juillet 2027. Echeance connue a l'avance,
donc sans effet de surprise : elle ne produit pas de choc datable, elle deplace
la structure d'acces. Fiche conservee comme reperage, pas comme evenement.

Trajectoire retenue : sans objet, echeance et non choc. Ne declenche aucun veto.

### etf-spot-bitcoin-us

- Date : 2024-01-10
- Categorie : reglementaire.approbation_instrument
- Portee : bitcoin
- Statut : a_mesurer
- Source : a confirmer — decision SEC, verifier la date exacte d'approbation et
  celle de premiere cotation avant de mesurer

Approbation des ETF spot bitcoin aux Etats-Unis. Cas d'ecole d'un evenement
reglementaire favorable et longuement anticipe : la mesure doit distinguer le
mouvement de la decision de celui de l'anticipation.

| Fenetre | Absolu | Relatif BTC |
|---------|--------|-------------|
| J+1     |        |             |
| J+7     |        |             |
| J+30    |        |             |

Trajectoire retenue : a mesurer.

### sanctions-ofac-tornado-cash

- Date : 2022-08-08
- Categorie : reglementaire.enquete
- Portee : marche
- Statut : a_mesurer
- Source : a confirmer — designation OFAC, verifier la date

Sanctions americaines visant un outil de confidentialite. Pertinent ici parce
qu'il teste la reaction du marche a une action sur la confidentialite elle-meme
plutot que sur un actif.

| Fenetre | Absolu | Relatif BTC |
|---------|--------|-------------|
| J+1     |        |             |
| J+7     |        |             |
| J+30    |        |             |

Trajectoire retenue : a mesurer.
