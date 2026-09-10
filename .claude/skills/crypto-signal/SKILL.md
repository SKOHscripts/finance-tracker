---
name: crypto-signal
description: Rapport hebdomadaire de rotation crypto pour Finance Tracker. Lance le scan, lit le verdict de chaque position, applique le veto d'actualite du playbook, et redige un rapport chiffre avec, seulement si toutes les barrieres passent et qu'aucun veto n'est actif, un plan de swap pret a copier. Cinq verdicts par position : conserver, tourner vers un autre actif, temporiser en stablecoin quand le regime est degrade, alleger pour recuperer la mise, ou sortir sur stop suiveur ; plus un sixieme, suspendu, quand un veto bloque le mouvement. A utiliser des que l'utilisateur lance "/crypto-signal", demande le scan hebdo, le rapport crypto, "faut-il bouger", "est-ce que je sors de telle position", "est-ce que je passe en stable", ou toute revue de son allocation crypto. A utiliser aussi pour reviser les seuils de config/signal_rules.toml, relire l'historique des verdicts, ou consulter le playbook d'actualite.
---

# crypto-signal

Routine hebdomadaire. Elle produit un verdict, pas une prediction.

Ce rapport n'est pas un conseil en investissement. Il decrit des regles
appliquees a des metriques passees. Chaque rapport le rappelle une fois, en
tete, sans s'excuser et sans en faire un paragraphe.

## Ou vivent les choses

Le moteur est dans l'application, pas dans un script isole :

- **Les positions** sont en base, pas dans un fichier. Elles viennent des
  produits associes a un identifiant de marche, alimentes soit par un
  portefeuille suivi, soit par les transactions saisies.
- **Les seuils** sont dans `config/signal_rules.toml`. Ce fichier ne contient
  que des regles : aucune position, aucun montant, aucune adresse. C'est ce qui
  permet au depot d'etre public.
- **L'historique** est en base, dans les tables `scanrun` et `positionverdict`.
  Ce sont elles que lisent les barrieres de persistance.
- **Le playbook** est dans `docs/playbook/`, versionne integralement : c'est de
  la connaissance sourcee, pas de la position.
- **Les drapeaux d'actualite** sont dans `state/news_flags.json`, hors du depot.

Tout est libelle en euros.

## Ce que fait la routine

`finance-tracker crypto-scan --json` recupere les donnees CoinGecko, calcule des
metriques reproductibles sur le top 10 plus les positions detenues, applique les
barrieres et ecrit le resultat en base. Ton role : lancer la commande, lire le
JSON, rediger le rapport.

Chaque position est arbitree independamment des autres, contre le meme candidat,
avec son propre montant. Un verdict par ligne, jamais un verdict unique pour
l'ensemble.

Le montant change le resultat. Les frais de chaine sont fixes en euros, donc une
petite ligne paie proportionnellement plus cher : un aller-retour coute 5,1 % sur
1000 EUR et 15 % sur 100 EUR. La barriere `avantage_momentum_vs_cout` exige donc
davantage d'une petite position. Ce n'est pas un biais, c'est le cout reel.

Tout le calcul est dans le moteur. Tu ne recalcules rien a la main et tu
n'ajoutes aucun jugement sur la direction future des prix.

## Ce que cette routine ne fait pas

Elle ne predit rien. Aucun mecanisme ici n'anticipe une hausse ou une baisse,
parce que personne ne sait le faire de facon fiable et qu'un outil qui pretend
le contraire fait perdre de l'argent avec assurance.

Ce qu'elle fait, c'est appliquer des regles asymetriques et mecaniques :
recuperer la mise quand le gain est la, couper quand le prix decroche, refuser
d'acheter dans un marche baissier constate. Aucune ne demande de savoir la suite.

Elle n'execute rien non plus. Aucune cle, aucune signature, aucun ordre. Un plan
de swap est une liste de parametres a executer a la main.

## Les six verdicts

- `CONSERVER` : rien ne bouge. C'est le verdict par defaut et le plus frequent.
- `ROTATION` : les six barrieres de `[gates]` passent. Swap vers le candidat du
  classement.
- `TEMPORISER` : aucune rotation ne passe, le regime est degrade, et les six
  barrieres de `[temporisation]` passent. Swap vers un refuge stable pour
  attendre.
- `ALLEGER` : la plus-value depasse le seuil, vendre la fraction qui rend le
  capital investi. Le reste continue de rouler.
- `SORTIE_STOP` : la ligne est en gain mais a decroche de son plus haut au-dela
  du seuil. Sortie complete vers le refuge.
- `SUSPENDU` : un mouvement etait retenu, un veto d'actualite le bloque. Ne sort
  jamais d'un CONSERVER : ne rien faire ne demande aucune route de swap.

L'ordre de priorite est fixe et il compte : `SORTIE_STOP` avant `ALLEGER`, puis
`ROTATION`, puis `TEMPORISER`, puis `CONSERVER`. Proteger le capital passe avant
d'encaisser, et encaisser passe avant de courir apres un autre actif.

Un verdict par position. Le champ `verdict` a la racine du JSON n'est qu'un
resume : il porte l'action la plus engageante presente sur une ligne. Ne le
presente jamais comme le verdict du portefeuille.

Les cinq premiers viennent du moteur, qui ne lit aucune actualite. Le sixieme
vient de `scripts/apply_news_veto.py`, qui lit les drapeaux de
`state/news_flags.json` et les regles de `docs/playbook/veto.toml`. Les deux
etages restent separes : le calcul est reproductible, le veto est tracable.

## Etapes

1. Verifier que des positions existent :

```bash
finance-tracker crypto-positions
```

Si la liste est vide, dis-le et arrete-toi : il n'y a rien a arbitrer.

2. Regarder d'ou viennent les chiffres. La colonne `Source` dit si une quantite
   vient de la chaine ou des transactions, et si un capital investi est saisi,
   derive de la chaine, ou inconnu. **Un prix de revient estime depuis la chaine
   est une estimation** : signale-le dans le rapport partout ou il alimente le
   stop suiveur ou la prise de benefice.

3. Lancer le scan :

```bash
finance-tracker crypto-scan --json > state/latest_scan.json
```

4. Lire `state/latest_scan.json`.

5. Situer la semaine dans la serie :

```bash
finance-tracker crypto-history
```

6. Lancer `/news-scan` si l'actualite de la semaine n'a pas encore ete
   collectee, puis :

```bash
python scripts/apply_news_veto.py
```

et lire `state/latest_verdict.json`.

7. Rediger le rapport selon le gabarit ci-dessous.
8. Si un verdict final vaut ROTATION, TEMPORISER, ALLEGER ou SORTIE_STOP,
   produire le bloc de swap correspondant.
9. Si un verdict final vaut SUSPENDU, produire le bloc de suspension et aucun
   plan de swap.

Si la commande echoue sur le reseau, dis-le et arrete-toi. Ne remplace pas les
donnees manquantes par des chiffres de memoire.

## Gabarit du rapport

Ecris en francais, mode imperatif, phrases courtes. Pas d'introduction
thematique, pas de conclusion recapitulative. Applique la skill `stop-slop`.

```
# Scan crypto - <date>

Outil educatif. Ni conseil en investissement, ni recommandation.

Candidat du classement : <symbole>

## Verdicts par position

<tableau : position | valeur | verdict | serie | barrieres qui bloquent>

## Barrieres, position par position

<un bloc par position :>
### <symbole> — <valeur> EUR — <verdict>
<tableau rotation : barriere | mesure | seuil | passe>
<tableau du mecanisme declencheur si le verdict n'est pas CONSERVER>
<ou, si un mecanisme n'est pas applicable, la phrase de son champ reason>

## Classement

<tableau : rang | actif | score | 90j % | 30j % | vol 30j % | drawdown 90j %>

## Candidats ecartes

<tableau : actif | score | motif>
<ou : aucun, le mieux classe passe les filtres>

## Cout d'un mouvement

<tableau : position | valeur | aller-retour % | avantage exige % | avantage
constate %>

Fais apparaitre l'ecart de cout entre les lignes. C'est l'information que le
montant ajoute au rapport.

## Fiabilite des entrees

<une ligne par position dont le capital investi est estime ou inconnu>

## Ce qui a change depuis le dernier scan

<deux phrases maximum, uniquement sur les barrieres qui ont bascule>
```

Si une barriere bloque, nomme laquelle et donne l'ecart restant en chiffres. Une
seule barriere qui bloque suffit : ne presente pas les autres comme un argument
en faveur du mouvement.

Une position dont `arbitre` est faux n'a ni barrieres ni cout : reprends la
phrase de son champ `reason` et passe a la suivante.

Une position dont le capital investi est inconnu n'a ni stop suiveur ni prise de
benefice. Dis-le une fois, dans la section « Fiabilite des entrees », plutot que
d'afficher deux mecanismes vides.

## Bloc de swap

A produire pour chaque position dont `plan` n'est pas nul. Un bloc par position,
jamais un bloc agrege : les montants et les minimums acceptables different d'une
ligne a l'autre.

```
## Mouvement a executer — <symbole>

Depuis : <from_symbol>   Vers : <to_symbol>
Montant : <amount> EUR
Prix de reference : <reference_price> EUR
Unites attendues : <units_at_reference>
Minimum acceptable : <min_accept_units>   (perte max toleree <max_acceptable_loss_pct> %)

Avant d'envoyer quoi que ce soit :
1. Demander un devis a chacun des fournisseurs listes.
2. Rejeter tout devis sous le minimum acceptable.
3. Verifier l'adresse de reception sur l'appareil, caractere par caractere.
4. Envoyer d'abord un montant test si la route n'a jamais ete utilisee.
5. Consigner date, route, montant envoye, montant recu.

Apres execution : enregistrer le swap dans l'application, pour que la quantite
et le prix de revient de la ligne suivent. Sans ca, le scan suivant compare le
mauvais actif.
```

Rappelle a chaque bloc de swap que l'ecart entre fournisseurs est de l'ordre de
plusieurs pourcents. Comparer les devis pese plus lourd que le choix du
candidat. Voir `docs/playbook/routes-swap.md`.

Pour une temporisation, ajoute : une jambe, pas deux, le cout affiche ne couvre
pas le retour ; et choisir la chaine cible du stable, un stablecoin sur une
chaine chere annulant l'economie du meilleur devis.

Pour un allegement, reprends le champ `note` du plan tel quel : il dit quelle
fraction est vendue et pourquoi.

## Bloc de suspension

A produire pour chaque position dont `verdict_final` vaut SUSPENDU dans
`state/latest_verdict.json`. Le veto s'applique ligne par ligne : une nouvelle
sur le candidat suspend toutes les rotations, une nouvelle sur un refuge ne
touche que les temporisations.

```
## Mouvement suspendu — <symbole>

Verdict du scan : <verdict_scan>   Suspendu jusqu'au <date d'expiration la plus lointaine>

<tableau : drapeau | categorie | portee | expire le | motif>

Le calcul retenait un mouvement. Un evenement du playbook le bloque. Aucun plan
de swap n'est produit tant qu'un veto est actif.

Le scan se relance chaque semaine : si le veto expire et que les barrieres
passent toujours, le mouvement reviendra de lui-meme.
```

Reprends le champ `motif` de chaque veto tel quel, sans le reformuler : il vient
de `docs/playbook/veto.toml`, que l'utilisateur a ecrit.

Ne produis aucun bloc de swap sous un verdict SUSPENDU, meme partiel, meme a
titre indicatif. Un plan de swap affiche est un plan de swap execute.

## Le regime de marche

`regime` dans le JSON porte l'etat constate, jamais une prevision. Deux mesures
independantes : l'actif de reference au-dessus ou sous sa moyenne longue, et la
part du classement en momentum lent positif. Les deux favorables donnent `BULL`,
une seule `MIXTE`, aucune `BEAR`.

En `BEAR`, toutes les rotations sont bloquees et la barriere de marche de la
temporisation est satisfaite. C'est la traduction mecanique de « surfer le bull,
temporiser le bear ».

Quand `state` vaut `INCONNU`, dis que l'historique est insuffisant pour lire le
regime. Ne devine pas.

## La prise de benefice et le stop suiveur

Les deux exigent un capital investi connu. Sans lui, ils ne s'appliquent pas, et
le champ `reason` du mecanisme le dit. Ne presente pas leur absence comme un
signal.

Quand le capital investi vient d'une estimation on-chain, dis-le a cote du
verdict. Une sortie de stop declenchee sur un prix de revient devine est une
sortie sur une hypothese.

## Reviser un seuil

Les seuils sont dans `config/signal_rules.toml`. Un changement de seuil change
le comportement du moteur sans toucher au code : fais-le dans un commit dedie
qui explique pourquoi. Dans six mois, le chiffre seul ne dira plus rien.

Ne modifie jamais un seuil pour faire passer un mouvement que les barrieres
refusent. C'est exactement ce que les barrieres sont la pour empecher.
