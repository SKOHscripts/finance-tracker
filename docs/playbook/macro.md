# Macro

Decisions de taux, inflation, dollar.

## Pourquoi ce domaine ne produit aucun veto

Un choc macro deplace tout le classement dans le meme sens. Le score du script
est construit sur des z-scores : il compare chaque actif a la population du top
10, pas a zero. Un mouvement commun s'annule donc dans l'ecart de score, et la
barriere `avantage_momentum_vs_cout` compare deja deux actifs entre eux.

Poser un veto macro reviendrait a corriger deux fois la meme chose, et a
suspendre des mouvements sur la base d'une information deja dans les chiffres.

Les fiches de ce fichier servent a lire un rapport, pas a bloquer un swap.
`veto.toml` ne contient aucune regle de categorie `macro.*`, et c'est
intentionnel.

## Ce qu'on y consigne quand meme

Une fiche macro a un usage precis : expliquer pourquoi tout le classement bouge
ensemble une semaine donnee, pour eviter de lire un mouvement general comme un
signal propre a un actif.

### gabarit-fiche-macro

- Date : AAAA-MM-JJ
- Categorie : macro.decision_taux | macro.inflation | macro.choc_dollar
- Portee : marche
- Statut : a_mesurer
- Source : <communique de la banque centrale, publication statistique>

<ce qui a ete decide ou publie, et l'ecart au consensus s'il est source>

| Fenetre | Absolu top 10 median | Dispersion du classement |
|---------|----------------------|--------------------------|
| J+1     |                      |                          |
| J+7     |                      |                          |

Trajectoire retenue : <une phrase, au passe>

La colonne de droite est celle qui compte. Un choc macro qui laisse la
dispersion intacte n'a rien change au classement relatif, donc rien change au
verdict.

## Fiches

Aucune pour l'instant. Le premier scan d'actualite en ajoutera dans
`candidats.md`.
