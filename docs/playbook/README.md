# Playbook

Ce dossier relie un type d'information a une trajectoire de marche constatee.
Il ne predit rien. Il consigne ce qui s'est produit, mesure par mesure, pour
qu'un evenement du meme type soit reconnu la prochaine fois.

Il sert a une seule chose dans la routine : opposer un veto. Une fiche du
playbook peut suspendre une rotation ou une temporisation. Aucune ne peut en
declencher une. L'asymetrie est deliberee.

## Statut d'une fiche

Trois valeurs, et une seule progression possible.

`a_mesurer` : l'evenement est date et source, sa consequence chiffree n'a pas
encore ete relevee. La fiche ne compte pas dans les regles de veto.

`mesure` : `scripts/measure_event.py` a releve la trajectoire sur les fenetres
J+1, J+7 et J+30, en absolu et en relatif au bitcoin. Les chiffres sont dans la
fiche, avec la date du relevé.

`approuve` : la mesure a ete relue et la fiche entre dans le jeu de regles.
Toi seul approuves. L'agente propose, elle ne promeut pas.

Une fiche ne redescend jamais d'un cran sans commit dedie expliquant pourquoi.

## Standard de preuve

Une fiche sans source verifiable n'existe pas. Une fiche sans date precise non
plus : un evenement etale sur un trimestre ne se mesure pas.

Aucun chiffre de memoire. Les magnitudes viennent de `measure_event.py`, qui
interroge CoinGecko, ou d'une source citee dans la fiche. Si le chiffre n'est
ni mesure ni source, la case reste vide et le statut reste `a_mesurer`.

Le relatif au bitcoin compte plus que l'absolu. Un actif qui perd 12 % pendant
que le marche perd 14 % n'a rien subi de particulier.

## Format d'une fiche

    ### <identifiant-court>

    - Date : AAAA-MM-JJ
    - Categorie : <domaine>.<type>
    - Portee : <liste d'identifiants CoinGecko, ou "marche">
    - Statut : a_mesurer | mesure | approuve
    - Source : <URL ou reference verifiable>

    <deux phrases : ce qui s'est passe, factuellement>

    | Fenetre | Absolu | Relatif BTC |
    |---------|--------|-------------|
    | J+1     |        |             |
    | J+7     |        |             |
    | J+30    |        |             |

    Trajectoire retenue : <une phrase, au passe, sans extrapolation>

## Les quatre domaines

`reglementaire.md` — delistages, restrictions par juridiction, approbations
d'instruments, enquetes. Le domaine le plus directement lie a une position en
XMR sur wallet auto-heberge.

`contrepartie.md` — faillites de plateformes, hacks de ponts, depeg de
stablecoin, gel d'adresses. Le domaine qui concerne les refuges de
temporisation.

`protocole.md` — forks, halvings, mises a jour majeures, incidents reseau,
changements d'emission.

`macro.md` — decisions de taux, inflation, dollar. Ce domaine ne produit
jamais de veto, et la raison est ecrite en tete du fichier.

`candidats.md` — les observations que l'agente ajoute apres un scan
d'actualite. Antichambre, pas playbook.

## Regles de veto

`veto.toml` fait la traduction : quelle categorie, sur quel role d'actif,
suspend quel verdict, pendant combien de jours. Le fichier est lu par
`scripts/apply_news_veto.py`, qui n'interprete rien. Modifier une regle se fait
la, avec un commit dedie.

## Ce que l'agente peut faire seule

Ajouter une observation dans `candidats.md` apres un scan, avec ses sources.
Lancer `measure_event.py` sur une fiche `a_mesurer` et remplir le tableau.

## Ce qu'elle ne fait pas

Promouvoir une fiche en `approuve`. Modifier `veto.toml`. Inventer une
magnitude. Ajouter une fiche sans source. Deduire d'une fiche qu'un actif va
monter ou baisser : une fiche decrit un passe, elle n'ouvre aucun futur.
