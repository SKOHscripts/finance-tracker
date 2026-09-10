# Candidats

Antichambre du playbook. L'agente ecrit ici apres un scan d'actualite, avec
ses sources. Rien de ce fichier ne produit de veto.

## Regles

Une entree par observation, au format des fiches du playbook, avec le statut
`a_mesurer` et la mention de l'agent qui l'a remontee.

Une observation sans source verifiable ne descend pas ici : elle est jetee.

Une observation deja couverte par une fiche existante ne descend pas non plus.
Ajouter une ligne au tableau de la fiche existante vaut mieux qu'un doublon.

## Promotion vers le playbook

1. L'agente lance `scripts/measure_event.py` et remplit le tableau.
2. Elle propose la promotion dans le rapport de scan, avec la mesure.
3. Tu relis et deplaces la fiche dans le fichier de domaine, en passant
   le statut a `approuve`, par un commit dedie.

L'agente ne fait jamais l'etape 3.

## Entrees

Dix au total. Cinq du scan du 5 septembre 2026, trois du scan du 6 septembre,
deux du scan du 8 septembre.

### 2026-08-07-ravencoin-consensus-kawpow

- Date : 2026-08-07
- Categorie : protocole.incident_reseau
- Portee : ravencoin
- Statut : mesure
- Source : https://x.com/Ravencoin/status/2086862580014850412
- Remonte par : agent protocole, news-scan 2026-09-06

Une faille de validation du champ nHeight dans l'en-tete KAWPOW a permis a un
attaquant de faire accepter des blocs invalides par des noeuds vulnerables du
reseau Ravencoin. Le premier bloc invalide est apparu au bloc 4 487 776 le
7 aout 2026 a 15:44:01 UTC ; les pools majoritaires ont ensuite mine une
chaine excluant la branche exploitee, avec un risque de reorganisation
d'environ trois jours.

Ravencoin n'appartient ni au classement suivi ni aux positions ni aux
refuges : le drapeau ne correspond a aucun role de ce scan, comportement
attendu.

| Fenetre | Absolu | Relatif BTC |
|---------|--------|-------------|
| J-30    | -3,19 %  | -7,32 %  |
| J+1     | +1,47 %  | +1,38 %  |
| J+7     | -24,75 % | -21,64 % |
| J+30    | -13,54 % | -36,55 % |

Trajectoire retenue : chute marquee sur la fenetre lente, largement au-dela du
marche, avant une reprise partielle a J+30.

### 2026-08-21-mantra-cosmos-evm-exploit

- Date : 2026-08-21
- Categorie : protocole.incident_reseau
- Portee : mantra
- Statut : a_mesurer
- Source : https://github.com/cosmos/security/blob/main/communications/cosmos_evm_GHSA-7g4w-cg88-2cq2_post_mortem.md
- Remonte par : agent protocole, news-scan 2026-09-06

Une vulnerabilite chainee (underflow puis overflow de solde) dans le
precompile de staking de Cosmos EVM a permis l'extraction de tokens depuis des
comptes bloques sur plusieurs chaines Cosmos. MANTRA a arrete la production de
blocs le 21 aout 2026 a 23:13:01 UTC au bloc 17 449 398 et a repris le
22 aout avec la version corrigee 8.4.0.

MANTRA n'appartient ni au classement suivi ni aux positions ni aux refuges :
le drapeau ne correspond a aucun role de ce scan, comportement attendu.

| Fenetre | Absolu | Relatif BTC |
|---------|--------|-------------|
| J-30    | -25,32 % | -44,17 % |
| J+1     | -8,07 %  | -6,22 %  |
| J+7     | -11,17 % | -10,27 % |
| J+30    |          |          |

Trajectoire retenue : a mesurer a J+30, soit le 20 septembre 2026 ; baisse
deja marquee des J+1 et J+7.

### 2026-08-20-ethereum-glamsterdam-testnet

- Date : 2026-08-20
- Categorie : protocole.mise_a_jour_majeure
- Portee : aucune, voir ci-dessous
- Statut : a_mesurer
- Source : https://blog.ethereum.org/en/2026/08/17/plataberget-testnet
- Remonte par : agent protocole, news-scan 2026-09-06

La Ethereum Foundation a active le fork Glamsterdam sur le testnet public
Platåberget le 20 aout 2026.

CORRECTION DE CADRAGE. L'agent avait remonte ce fait sans preciser qu'il
s'agit d'un testnet. La chaine principale d'Ethereum n'a subi aucun
changement : aucune mise a jour n'a ete activee sur le mainnet. La categorie
`protocole.mise_a_jour_majeure` n'existe d'ailleurs pas dans `veto.toml`,
qui ne couvre que `protocole.incident_reseau` et `protocole.fork` : ce fait
ne produit aucun drapeau, meme s'il avait touche le mainnet.

Trajectoire retenue : sans objet pour le classement suivi, evenement de
testnet.

### 2026-09-03-binance-delistage-icx-scrt-storj

- Date : 2026-09-03
- Categorie : reglementaire.delistage
- Portee : icon, secret, storj
- Statut : a_mesurer
- Source : https://www.binance.com/en/support/announcement/detail/d72915ed7a60473b92f0818d959a227a
- Remonte par : agent reglementaire, news-scan 2026-09-05

Binance a suspendu le trading au comptant d'ICON, Secret et Storj le 3 septembre
2026 a 03:00 UTC. Les soldes restants apres le 3 novembre 2026 peuvent etre
convertis automatiquement en stablecoin.

Aucun des trois n'appartient au classement suivi ni aux refuges. Le drapeau est
ecrit dans news_flags.json et ne correspond a aucun role de ce scan : c'est le
comportement attendu, pas un echec. Secret est une chaine de confidentialite,
ce qui rend la fiche interessante a suivre pour un detenteur de XMR sans en
faire un evenement sur XMR.

| Fenetre | Absolu | Relatif BTC |
|---------|--------|-------------|
| J+1     |        |             |
| J+7     |        |             |
| J+30    |        |             |

Trajectoire retenue : a mesurer apres J+30, soit le 3 octobre 2026.

### 2026-08-30-scission-bip110-blake2b

- Date : 2026-08-30
- Categorie : protocole.fork
- Portee : aucune, voir ci-dessous
- Statut : a_mesurer
- Source : https://bitcoin-blake2b.org/ et
  https://github.com/bitcoinknots/bitcoin/pull/359
- Remonte par : agent protocole, news-scan 2026-09-05

Une chaine issue de BIP-110 s'est separee de Bitcoin au bloc 961 632 le 8 aout
2026, avec 2,53 % du hashrate a l'entree en phase obligatoire, puis a bascule sa
preuve de travail de SHA-256d vers BLAKE2b au bloc 961 640 le 30 aout 2026.

CORRECTION DE CADRAGE. L'agent avait rapporte ce fait comme un changement
d'algorithme de Bitcoin. C'est faux : la chaine reconnue par les mineurs, les
plateformes et les portefeuilles reste sur SHA-256d et n'a pas change. Il s'agit
d'une scission minoritaire creant une chaine distincte.

Cette fiche ne produit aucun drapeau. Ecrire un `protocole.fork` sur `bitcoin`
suspendrait une rotation vers BTC sur la base d'un evenement qui ne touche pas
BTC. Le seul angle qui la rendrait pertinente est le risque de confusion de
route — recevoir la mauvaise chaine sur une jambe XMR vers BTC — et il est
negligeable chez un fournisseur grand public.

Trajectoire retenue : sans objet pour le classement suivi.

### 2026-08-27-moonwell-mamo-base

- Date : 2026-08-27
- Categorie : contrepartie.hack
- Portee : aucune, voir ci-dessous
- Statut : a_mesurer
- Source : https://forum.moonwell.fi/t/post-mortem-mamo-market-incident-on-base/2208
- Remonte par : agent contrepartie, news-scan 2026-09-05

Un acteur a manipule le prix du token MAMO sur Base et emprunte 11 028 762 USD
de principal sur Moonwell en le postant en collateral. Le post-mortem chiffre a
environ 9 131 342 USD la dette residuelle non couverte.

CORRECTION DE CADRAGE. L'agent avait liste usd-coin, ethereum et bitcoin comme
actifs concernes. Ils ont ete empruntes puis sortis du protocole : aucun n'a
subi de defaillance, de rupture de peg, de gel ni de compromission. La perte est
portee par Moonwell et ses fournisseurs de liquidite.

Cette fiche ne produit aucun drapeau. Un `contrepartie.hack` sur `usd-coin`
suspendrait une temporisation vers l'USDC alors que l'USDC n'a rien subi.

Trajectoire retenue : sans objet pour le classement suivi.

### 2026-08-26-pce-juillet-2026

- Date : 2026-08-26
- Categorie : macro.inflation
- Portee : marche
- Statut : a_mesurer
- Source : https://www.bea.gov/news/2026/personal-income-and-outlays-july-2026
- Remonte par : agent macro, news-scan 2026-09-05

Communique BEA du 26 aout 2026, portant sur juillet 2026. Indice de prix PCE en
hausse de 0,2 % sur le mois et de 3,7 % sur un an ; PCE sous-jacent en hausse de
0,2 % sur le mois et de 3,3 % sur un an.

Aucun drapeau : le domaine macro ne produit aucun veto, par construction. Voir
playbook/macro.md.

### 2026-09-01-hicp-flash-aout-2026

- Date : 2026-09-01
- Categorie : macro.inflation
- Portee : marche
- Statut : a_mesurer
- Source : https://ec.europa.eu/eurostat/web/products-euro-indicators/w/2-01092026-ap
- Remonte par : agent macro, news-scan 2026-09-05

Estimation rapide Eurostat du 1er septembre 2026 : inflation annuelle de la zone
euro a 3,3 % en aout, contre 2,9 % en juillet. Composante energie a 14,3 % sur un
an, contre 10,3 % le mois precedent.

Aucun drapeau, meme raison.

### 2026-09-06-liquid-network-pegout

- Date : 2026-09-06
- Categorie : contrepartie.hack
- Portee : aucune, voir ci-dessous
- Statut : mesure
- Source : https://cryptobriefing.com/blockstream-liquid-network-exploit-funds-return/
  et https://www.coindesk.com/markets/2026/09/07/bitcoin-network-used-by-exchanges-hit-by-usd320-million-exploit-hackers-claim-they-re-the-good-guys
- Remonte par : agent contrepartie, news-scan 2026-09-08

Environ 4 000 BTC ont quitte le portefeuille de federation de Liquid Network le
6 septembre 2026 a 14h28 UTC, par abus d'une cle d'autorisation de peg-out chez
un membre de la federation, sur un bug du logiciel Elements. Aucune cle privee
n'a ete volee ; Blockstream a suspendu le reseau et bloque les rachats, puis
confirme des correctifs le 7 septembre, les auteurs se declarant white hats et
proposant de rendre la majeure partie des fonds.

CADRAGE. L'entite touchee est Liquid Network et les detenteurs de L-BTC, pas
Bitcoin. La chaine principale n'a subi ni defaillance ni interruption. Ecrire
un `contrepartie.hack` sur `bitcoin` suspendrait une rotation vers BTC pour un
incident qui ne touche pas BTC.

Aucun drapeau produit. Mesure conservee parce qu'elle calibre une categorie :
un exploit de 320 M USD sur une chaine laterale d'un actif majeur.

| Fenetre | Absolu | Relatif ETHEREUM |
|---------|--------|------------------|
| J-7     |  +2.08 % |          +0.53 % |
| J+1     |  -1.40 % |          -0.37 % |
| J+2     |  -1.49 % |          -1.07 % |

Trajectoire retenue : le bitcoin a cede 1,49 % en absolu et 1,07 point face a
l'ethereum dans les deux jours suivants. Fenetres J+7 et J+30 a mesurer les 13
septembre et 6 octobre 2026.

### 2026-09-03-sec-nasdaq-texas-5711d

- Date : 2026-09-03
- Categorie : reglementaire.approbation_instrument
- Portee : bitcoin, ethereum, solana, ripple
- Statut : a_mesurer
- Source : https://www.sec.gov/files/rules/sro/nasdaqtx/2026/34-106268.pdf
- Remonte par : agent reglementaire, news-scan 2026-09-08

Ordre SEC 34-106268 du 3 septembre 2026 : approbation acceleree de la
modification de la regle 5711(d) de Nasdaq Texas sur les Commodity-Based Trust
Shares, deposee le 20 aout 2026. Le texte ajoute une definition de digital
commodity, autorise un tampon allant jusqu'a 15 % de la valeur liquidative en
actifs ne satisfaisant pas les criteres generiques, et ouvre aux strategies
gerees activement. Bitcoin, Ether, Solana et XRP figurent nommement dans le
document.

Verification faite en extrayant le texte du PDF servi par sec.gov : la date, le
numero d'ordre, la regle, le seuil de 15 % et les quatre actifs sont confirmes.

Aucun drapeau produit, et ce n'est pas un oubli. `veto.toml` ne porte aucune
regle sur `reglementaire.approbation_instrument`, par construction : un
evenement reglementaire favorable ne doit jamais suspendre un mouvement. Le
veto est asymetrique.

| Fenetre | Absolu | Relatif ETHEREUM |
|---------|--------|------------------|
| J+1     |          |                  |
| J+7     |          |                  |
| J+30    |          |                  |

Trajectoire retenue : a mesurer sur bitcoin a partir du 10 septembre 2026.
