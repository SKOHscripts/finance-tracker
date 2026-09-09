# Routes de sortie XMR depuis un wallet auto-heberge

Etat au 5 septembre 2026. A reverifier tous les six mois : le paysage bouge par
vagues reglementaires, pas par evolution graduelle.

## Pourquoi il n'y a pas de carnet d'ordres

OKX a retire les paires XMR le 5 janvier 2024. Binance a delistee XMR
mondialement le 20 fevrier 2024. Kraken a retire XMR en Irlande et Belgique en
juin 2024, puis sur toute la zone EEE le 31 octobre 2024, puis au Canada et en
Inde en avril 2026. En France, MiCA et l'AMLR rendent un retour improbable, et
l'AMLR monte en charge jusqu'au 1er juillet 2027.

Consequence pratique : depuis Feather, aucun ordre limite. Chaque mouvement est
un swap au comptant, a un prix qu'il faut negocier en comparant.

## Les trois familles de routes

### Atomic swap XMR <-> BTC

Le protocole COMIT (`xmr-btc-swap`) et UnstoppableSwap. Sans tiers de confiance,
sans compte. Le swap reussit entierement ou echoue entierement. Contrepartie :
delai en confirmations multiples, exigence technique reelle, et il faut ensuite
une seconde jambe BTC vers la cible.

C'est la route de reference quand le montant justifie la complexite.

### P2P avec escrow

Haveno, en multisig 2 sur 3, via Tor. Pas d'atomic swap au sens strict mais
minimisation de la confiance. Liquidite variable selon l'heure et le montant.

### Agregateurs non-custodial instantanes

Reglement en minutes plutot qu'en heures. Pas de compte, mais un operateur voit
les adresses et les montants. Adapte quand la vitesse prime.

## Le chiffre qui compte

Un releve du 31 aout 2026 portant sur plus de 1 000 cotations de huit
fournisseurs, sur 17 paires et 171 jeux comparables, donne un ecart median de
2,55 % entre la meilleure et la pire offre, moyenne 2,77 %.

Ce n'est pas une commission. C'est la dispersion entre fournisseurs sur une
meme demande. Sur 1 000 USD, ignorer cette comparaison coute environ 25 USD par
jambe, soit 50 USD sur un aller-retour. Le meme montant que plusieurs mois de
mouvement de prix sur un actif calme.

D'ou la regle : demander quatre devis, prendre le meilleur, refuser sous le
minimum calcule.

## Sequence de securite

1. Devis chez les quatre fournisseurs, dans la meme fenetre de dix minutes.
2. Comparer au `min_accept_units` du plan de swap.
3. Verifier l'adresse de reception sur l'ecran de l'appareil.
4. Montant test si la route est nouvelle.
5. Consigner l'operation dans `state/trades.md`.

## Ce qui n'est pas resolu par cette routine

Le risque de contrepartie sur un agregateur, la disponibilite d'un fournisseur
un dimanche matin, et la volatilite du XMR pendant les confirmations d'un atomic
swap. Aucun script ne couvre ces trois points.

## Sortie vers un stablecoin

La temporisation ajoute une cible qui n'existait pas dans la version initiale de
ce document. Trois points la distinguent d'une rotation.

Aucune route XMR vers un stablecoin n'est atomique de bout en bout. Le protocole
COMIT ne connait que la paire XMR <-> BTC. Sortir vers l'USDC, c'est donc soit
deux jambes (XMR -> BTC en atomic swap, puis BTC -> USDC), soit un agregateur
non-custodial en une seule operation, avec l'exposition de contrepartie que cela
suppose. Haveno couvre des paires fiat et crypto selon les offres du carnet, pas
systematiquement les stables.

La chaine cible pese autant que le devis. Le meme USDC coute des frais tres
differents selon qu'il arrive sur Ethereum, sur une L2 ou sur Solana. Un
avantage de 2 % gagne en comparant quatre fournisseurs disparait si la reception
se fait sur la chaine la plus chere. Demander le devis chaine par chaine.

Le refuge n'est pas sans risque. Un stablecoin remplace le risque de prix par un
risque d'emetteur : gel d'adresse, depeg, contrainte reglementaire. Un USDC gele
ne se debloque pas. C'est le prix de la temporisation, et il ne figure dans
aucune barriere du script.

## Retour depuis le stablecoin

Le retour se paie une seconde jambe et repasse par les memes fournisseurs. Le
plan de temporisation n'affiche que le cout de l'aller : la barriere
`baisse_vs_cout` compare la baisse constatee au cout d'une seule jambe, pas d'un
aller-retour. Si tu temporises puis reviens dans le mois, tu auras paye deux
fois environ 2,6 % pour un mouvement que la barriere n'avait justifie qu'une
fois.

C'est la raison de `required_consecutive_weeks` a deux semaines : la persistance
coute moins cher qu'un aller-retour premature.

## Alerte de route : Liquid Network, septembre 2026

Le 6 septembre 2026, environ 4 000 BTC ont quitte le portefeuille de federation
de Liquid Network par abus d'une cle d'autorisation de peg-out. Blockstream a
suspendu le reseau et bloque les rachats : les detenteurs de L-BTC ne pouvaient
plus les reconvertir en bitcoin.

Ce point ne concerne pas la chaine principale, mais il concerne les routes. Le
chemin de reference depuis le XMR passe par le BTC. Certaines plateformes et
services de swap reglent leurs transferts BTC via Liquid, et un rachat bloque
transforme un devis honore sur le papier en solde immobilise.

Consequence pratique, a verifier avant chaque jambe BTC : demander au
fournisseur sur quelle chaine il livre. Un BTC livre en L-BTC n'est pas un BTC
tant que le peg-out fonctionne. La question vaut d'etre posee meme apres
retablissement du reseau, parce qu'elle ne coute rien et qu'elle revele la
plomberie du fournisseur.

Correctifs confirmes par Blockstream le 7 septembre 2026. Fiche complete dans
playbook/candidats.md.
