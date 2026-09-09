---
description: Scan crypto hebdomadaire — lance market_scan.py, produit le rapport et, si les barrières passent, le plan de swap ou de temporisation.
---

Exécute la routine hebdomadaire `crypto-signal`. Suis les étapes dans l'ordre.
Ne saute rien, ne devance rien.

## 1. Scan

```bash
finance-tracker crypto-scan --json > state/latest_scan.json
```

Si le script échoue, montre-moi la sortie brute et arrête-toi. Ne comble
aucune donnée manquante avec des chiffres de ta mémoire, et ne relance pas
plus de deux fois : un échec réseau répété se traite plus tard, pas en
insistant.

## 2. Lecture

Lis `state/latest_scan.json` puis `l'historique en base (finance-tracker crypto-history)`.

Tout le calcul est déjà fait. Tu ne recalcules aucune métrique, tu ne
réordonnes aucun classement, tu n'ajoutes aucune vue sur la direction future
des prix.

Le JSON porte une liste `positions`. Chaque entrée a son propre verdict, ses
propres barrières, son propre notionnel et son propre coût. Traite-les une par
une : je détiens plusieurs lignes, elles ne se compensent pas.

Le champ `verdict` à la racine n'est qu'un résumé — l'action la plus engageante
présente sur une ligne. Ne le présente jamais comme le verdict du portefeuille.

Le champ `candidats_ecartes` liste les actifs mieux classés que le candidat
retenu, sautés parce qu'ils échouent un filtre intrinsèque. Fais-le figurer :
sans lui, je ne comprends pas pourquoi le candidat n'est pas le premier du
classement.

Chaque position vaut `CONSERVER`, `ALLEGER`, `SORTIE_STOP`, `ROTATION` ou
`TEMPORISER`, dans cet ordre de priorité : protéger le capital passe avant
encaisser, encaisser passe avant courir après un autre actif.

Commence le rapport par le bloc `regime` : son état et ses deux mesures. C'est
le contexte qui explique tout le reste. En `BEAR`, aucune rotation ne peut
passer, et c'est voulu. Le bloc
`temporisation` de chaque position porte son propre jeu de barrières ; quand
`applicable` est faux, reprends la phrase du champ `reason` au lieu du tableau.
Une position dont `arbitre` est faux n'a ni barrières ni coût.

Ce verdict n'est pas encore le verdict final : le veto d'actualité s'applique à
l'étape 5.

## 3. Rapport

Rédige selon le gabarit de `SKILL.md`, en français, mode impératif, phrases
courtes. Applique la skill `stop-slop`. Pas d'introduction thématique, pas de
récapitulatif final.

Écris-le dans `reports/AAAA-MM-JJ.md` et affiche-le dans le chat.

Si une barrière bloque, nomme-la et donne l'écart restant en chiffres. Une
barrière qui bloque suffit à conclure : n'aligne pas les autres comme un
argument en faveur du mouvement.

Formule les métriques au passé. Le momentum 90 jours décrit ce qui s'est
produit, rien d'autre. Une temporisation constate une dégradation passée ; ne
la présente jamais comme une anticipation de baisse.

## 4. Plan de swap

Un bloc par position dont `swap_plan` n'est pas nul. Reprends le bloc de
`SKILL.md` avec les valeurs de cette position, dont son `min_accept_units` et
son `montant de la ligne` propres. Ne fusionne jamais deux positions dans un plan
unique.

Rappelle systématiquement que l'écart entre fournisseurs sur les routes XMR
atteint plusieurs pourcents, et que comparer quatre devis pèse plus lourd que
le choix du candidat. Détail dans `docs/playbook/routes-swap.md`.

## 5. Plan de temporisation

Un bloc par position dont `temporisation_plan` n'est pas nul. Reprends le bloc
dédié de `SKILL.md`, avec le `min_accept_units` de cette position et le champ
`route_note` tel quel.

Trois rappels obligatoires dans ce bloc :

- Une jambe, pas deux. Le coût affiché ne couvre pas le retour.
- La chaîne de réception du stable pèse autant que le devis.
- Après exécution, l'`id` du bloc `produit associe a un identifiant de marche` concerné doit passer
  à l'identifiant du refuge dans `config/signal_rules.toml`, sinon le scan suivant
  compare le mauvais actif. Ce changement-là justifie un commit.

Ne propose jamais une temporisation partielle : le script raisonne sur la
position entière.

Tu ne prépares aucune transaction. Tu ne demandes jamais de seed phrase, tu ne
manipules aucune clé, tu n'ouvres aucun wallet.

## 4 bis. Plans d'allègement et de sortie

Un bloc par position dont `allegement_plan` ou `sortie_stop_plan` n'est pas nul.

Pour un allègement, donne la fraction vendue, le montant, le minimum acceptable
en unités du refuge, et ce qui reste en position. Reprends le champ `note` tel
quel : il contient la mise à jour de config à faire après exécution.

Pour une sortie sur stop, dis de combien la ligne a décroché depuis son plus
haut. Ne commente pas la suite : un stop protège un gain, il ne prédit rien.

Rappelle-moi de consigner l'opération dans `state/trades.md`. Sans prix de
revient à jour, la prise de bénéfice suivante sera fausse.

## 5. Veto d'actualité

Lance `/news-scan`, sauf si je te dis que l'actualité de la semaine est déjà
collectée. Dans ce cas, lance seulement :

```bash
python scripts/apply_news_veto.py
```

Lis `state/latest_verdict.json`. Si `verdict_final` vaut `SUSPENDU`, produis le
bloc de suspension de `SKILL.md` et supprime le bloc de swap ou de
temporisation que tu venais d'écrire. Un plan de swap affiché sous un verdict
suspendu est un plan exécuté.

Fais toujours figurer le tableau des drapeaux en attente d'approbation, même
vide. Un drapeau en `a_mesurer` ne suspend rien : c'est en le relisant que je
lui donne son effet.

## 6. Clôture

Rappelle-moi de consigner l'opération dans `state/trades.md` si j'exécute le
swap.

Signale-moi tout écart entre le verdict et les semaines précédentes de
`history.json`, en deux phrases maximum, uniquement sur les barrières qui ont
basculé.

## Git

`l'historique en base (finance-tracker crypto-history)` est versionné. Tout le reste de `state/` et tout
`reports/` sont ignorés : ne les commite pas, ne suggère pas de les suivre.

Quand je lance le scan à la main, ne me propose pas de commit pour autant.
L'historique se pousse depuis la Routine hebdomadaire, pas depuis chaque
exécution manuelle. Si je te le demande explicitement, commite le seul
`l'historique en base (finance-tracker crypto-history)`, en `chore(state)`, et pousse sans ouvrir de pull request.

Deux autres cas justifient un commit : un changement de seuil dans
`config/signal_rules.toml`, et un basculement de l'`id` ou du `montant de la ligne` d'un bloc
`produit associe a un identifiant de marche` après un swap exécuté. Dans ces deux cas, lis le template depuis le buffer de commit et fais
figurer dans le corps l'ancienne valeur, la nouvelle, et la raison que je t'ai
donnée. Si je ne t'ai pas donné de raison, demande-la avant de commiter.

## Interdits

- Ne contourne aucune barrière, même si le candidat est attirant. Si je veux
  assouplir une règle, je modifie `rules.toml` moi-même.
- Ne propose aucune crypto absente du classement produit par le script, ni
  aucun refuge absent de `temporisation.refuges`.
- Ne traite aucune actualité comme une raison de bouger. Le veto retient, il ne
  pousse pas. Une bonne nouvelle sur un actif ne change rien au verdict.
- Ne modifie jamais `docs/playbook/veto.toml`, et ne passe jamais un drapeau en
  `approuve`.
- Ne me demande jamais un solde en unités ni la chaîne d'une position. Le
  notionnel arrondi en EUR suffit, le reste est une empreinte on-chain.
- Ne compense pas une position par une autre. Chaque ligne est arbitrée seule.
- Ne suggère pas d'augmenter la fréquence des scans ni le capital engagé.
- N'ajoute pas de recommandation d'achat, de vente ou de conservation qui ne
  découle pas des barrières.
