# Contrepartie et securite

Faillites de plateformes, hacks de ponts, depeg de stablecoin, gel d'adresses.

Le domaine qui concerne les refuges de temporisation. Un stablecoin remplace un
risque de prix par un risque d'emetteur, et ce fichier est l'endroit ou ce
risque se documente.

### terra-ust-depeg

- Date : 2022-05-09
- Categorie : contrepartie.depeg
- Portee : marche
- Statut : a_mesurer
- Source : a confirmer — verifier la date de rupture du peg avant de mesurer

Rupture du peg d'un stablecoin algorithmique, suivie d'une contagion sur
l'ensemble du marche. Reference du domaine : un depeg ne reste pas confine a
l'actif concerne.

| Fenetre | Absolu | Relatif BTC |
|---------|--------|-------------|
| J+1     |        |             |
| J+7     |        |             |
| J+30    |        |             |

Trajectoire retenue : a mesurer.

### usdc-depeg-svb

- Date : 2023-03-10
- Categorie : contrepartie.depeg
- Portee : usd-coin
- Statut : a_mesurer
- Source : a confirmer — verifier la date de la rupture et celle du retour au peg

Depeg temporaire d'un stablecoin adosse a des reserves bancaires, declenche par
la defaillance d'une banque depositaire. Fiche directement pertinente : c'est le
scenario qui frappe un refuge de temporisation.

| Fenetre | Absolu | Relatif BTC |
|---------|--------|-------------|
| J+1     |        |             |
| J+7     |        |             |
| J+30    |        |             |

Trajectoire retenue : a mesurer. Mesurer ici l'ecart au peg, pas seulement le
rendement : un stablecoin ne se lit pas comme un actif de momentum.

### ftx-faillite

- Date : 2022-11-11
- Categorie : contrepartie.faillite_plateforme
- Portee : marche
- Statut : a_mesurer
- Source : a confirmer — verifier la date du depot de bilan

Defaillance d'une plateforme majeure, avec contagion sur les contreparties
exposees. Cas de reference d'un choc de contrepartie a portee marche.

| Fenetre | Absolu | Relatif BTC |
|---------|--------|-------------|
| J+1     |        |             |
| J+7     |        |             |
| J+30    |        |             |

Trajectoire retenue : a mesurer.

### celsius-gel-retraits

- Date : 2022-06-12
- Categorie : contrepartie.gel_adresses
- Portee : marche
- Statut : a_mesurer
- Source : a confirmer — verifier la date de suspension des retraits

Suspension des retraits par un preteur centralise. Precede une faillite, et
sert de test : le gel est-il lu comme un incident isole ou comme un signal de
systeme.

| Fenetre | Absolu | Relatif BTC |
|---------|--------|-------------|
| J+1     |        |             |
| J+7     |        |             |
| J+30    |        |             |

Trajectoire retenue : a mesurer.

### ronin-bridge-hack

- Date : 2022-03-23
- Categorie : contrepartie.hack
- Portee : marche
- Statut : a_mesurer
- Source : a confirmer — verifier la date de l'exploitation et celle de la
  divulgation publique, qui different

Vol sur un pont inter-chaines. La fiche doit distinguer les deux dates : le
marche reagit a la divulgation, pas a l'exploitation.

| Fenetre | Absolu | Relatif BTC |
|---------|--------|-------------|
| J+1     |        |             |
| J+7     |        |             |
| J+30    |        |             |

Trajectoire retenue : a mesurer.
