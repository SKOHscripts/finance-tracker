---
description: Scan d'actualité financière — déploie quatre agents Haiku, en tire des drapeaux rattachés au playbook, et applique le veto au verdict du scan.
---

Construis le panorama d'actualité de la semaine et confronte-le au verdict
chiffré. Suis les étapes dans l'ordre.

Rappel du principe avant de commencer : l'actualité ne déclenche jamais un
mouvement. Elle peut seulement le suspendre. Si tu te surprends à écrire qu'une
nouvelle rend un actif attractif, tu es sorti du cadre.

## 1. Lire le playbook

Lis `docs/playbook/README.md`, puis les quatre fichiers de domaine et
`docs/playbook/veto.toml`. Tu as besoin de la liste exacte des catégories : un
drapeau dont la catégorie n'existe pas dans `veto.toml` ne servira à rien.

Lis aussi `state/news_flags.json` pour savoir ce qui est déjà remonté. Un
doublon coûte plus cher qu'un manque : il fait croire à deux événements.

## 2. Déployer les quatre agents

Lance les quatre en parallèle, dans un seul message, avec l'outil Agent,
`subagent_type: "general-purpose"` et `model: "haiku"`. Un agent par domaine :
réglementaire et accès, macro, contrepartie et sécurité, protocole et chaîne.

Donne à chacun ce brief, en remplaçant le domaine et sa définition par celle
du fichier de playbook correspondant :

    Tu collectes des faits d'actualité sur le domaine <domaine>, pour la
    période des sept derniers jours, plus tout événement plus ancien dont les
    effets sont encore en cours.

    Périmètre exact : <recopier la définition en tête du fichier de domaine>

    Utilise WebSearch et WebFetch. Pour chaque fait retenu, rends :
    - une date précise, au format AAAA-MM-JJ
    - une URL de source primaire : communiqué officiel, dépôt réglementaire,
      annonce de l'émetteur. Un article qui cite une source vaut moins que la
      source elle-même.
    - les actifs concernés, en identifiants CoinGecko quand tu les connais
    - deux phrases factuelles, sans adjectif d'appréciation

    Règles absolues :
    - Un fait sans source primaire vérifiable n'est pas rendu. Ne le rends pas
      avec une réserve : ne le rends pas du tout.
    - Aucune prévision, aucune interprétation de direction de prix, aucune
      recommandation. Tu rapportes ce qui s'est produit.
    - Aucun chiffre de ta mémoire. Si tu ne l'as pas lu dans une source de
      cette recherche, il n'existe pas.
    - Si rien ne remonte, réponds "rien à signaler" et arrête-toi. Une réponse
      vide est un résultat valable et fréquent.

    Rends une liste, la plus courte possible. Cinq faits bien sourcés valent
    mieux que vingt approximatifs.

Ne leur demande ni synthèse, ni classement, ni avis. La mise en relation avec
le playbook est ton travail, pas le leur.

## 3. Trier

Écarte, dans cet ordre :

- tout fait sans source primaire
- tout doublon d'un fait déjà présent dans `state/news_flags.json`
- tout fait déjà couvert par une fiche du playbook, sauf s'il en constitue une
  occurrence nouvelle et datable
- tout fait dont tu ne sais pas dire à quelle catégorie de `veto.toml` il
  appartient

Le dernier point est le plus important. Une catégorie inventée ne produit
aucun veto et pollue le fichier. En cas de doute, la place du fait est
`docs/playbook/candidats.md`, pas `news_flags.json`.

## 4. Écrire les drapeaux

Ajoute les faits retenus à `state/news_flags.json`, au format :

```json
{
  "id": "AAAA-MM-JJ-slug-court",
  "date": "AAAA-MM-JJ",
  "categorie": "domaine.type",
  "actifs": ["identifiant-coingecko"],
  "portee": "actif",
  "statut": "a_mesurer",
  "resume": "deux phrases factuelles",
  "sources": ["https://..."],
  "ajoute_par": "news-scan AAAA-MM-JJ"
}
```

`portee` vaut `"actif"` ou `"marche"`. Un fait à portée marché laisse `actifs`
vide.

Le statut est toujours `a_mesurer`. Jamais `approuve` : tu proposes, tu ne
promeus pas. Conséquence directe, à énoncer dans ton rapport : tant que
tu n'as pas approuvé un drapeau, il ne suspend rien.

Ajoute la même observation à `docs/playbook/candidats.md`, au format de fiche.

## 5. Mesurer ce qui est mesurable

Pour chaque fiche `a_mesurer` du playbook ou des candidats dont la date tombe
dans les 365 derniers jours :

```bash
python scripts/measure_event.py --asset <id> --date <AAAA-MM-JJ>
```

Pour un stablecoin, ajoute `--peg` : un refuge se lit en écart au peg, pas en
rendement.

Colle le tableau rendu dans la fiche et passe son statut à `mesure`. Écris la
trajectoire retenue en une phrase, au passé, sans extrapolation.

Si le script refuse parce que l'événement dépasse la fenêtre du plan gratuit,
laisse la fiche en `a_mesurer` et dis-le. Ne remplis pas le tableau autrement.

## 6. Appliquer le veto

```bash
python scripts/apply_news_veto.py
```

Lis `state/latest_verdict.json`. Il contient le verdict du scan, le verdict
final, les vetos appliqués avec leur motif et leur date d'expiration, et les
drapeaux écartés avec la raison de l'écartement.

Si `state/latest_scan.json` est absent, dis-le et arrête-toi là : il n'y a pas
de verdict à suspendre. Lance `/crypto-signal` d'abord.

## 7. Rapport

Écris dans `reports/news-AAAA-MM-JJ.md` et affiche dans le chat :

```
# Actualité - <date>

Verdict du scan : <...> | Verdict final : <...>

## Vetos actifs

<tableau : drapeau | catégorie | portée | expire le | motif>
<ou : aucun>

## En attente d'approbation

<tableau : drapeau | catégorie | actifs | ce qu'il suspendrait s'il était approuvé>
<ou : aucun>

## Remontées de la semaine

<un paragraphe par domaine, deux phrases maximum, avec la source en lien>
<pour un domaine sans remontée : "rien à signaler">

## Fiches mesurées

<liste des fiches dont le tableau a été rempli ce scan>
```

Le tableau « en attente d'approbation » est le plus important du rapport. Il
te dit ce que tu gagnerais à relire. Ne le range pas plus bas, ne le
fusionne pas avec les remontées.

Français, mode impératif, phrases courtes. Applique la skill `stop-slop`. Pas
d'introduction thématique, pas de récapitulatif final.

## 8. Git

Commite `state/news_flags.json`, `docs/playbook/candidats.md` et les fiches de
domaine que tu as mesurées. Rien d'autre : `reports/` et
`state/latest_verdict.json` sont ignorés.

Lis `.gitmessage` et suis son format. Sujets attendus :

    chore(state): consigne les drapeaux du scan du AAAA-MM-JJ
    docs(playbook): mesure la trajectoire de <fiche>

Pousse directement, sans ouvrir de pull request.

## Interdits

- Ne modifie jamais `docs/playbook/veto.toml`. Les règles appartiennent à
  l'utilisateur.
- Ne passe jamais un drapeau ou une fiche en `approuve`.
- N'écris aucune phrase qui prête une direction future à un actif. Une fiche
  décrit un passé.
- Ne présente pas un veto comme une raison de bouger. Un veto ne fait que
  retenir.
- N'ajoute aucun fait rendu sans source par un agent, même s'il te semble
  exact. Si tu le sais, tu peux le sourcer ; si tu ne peux pas le sourcer, tu
  ne le sais pas.
- Ne relance pas les agents plus d'une fois. Une semaine sans actualité est un
  résultat, pas un échec de collecte.
