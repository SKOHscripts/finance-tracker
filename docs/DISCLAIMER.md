# ⚠️ Avertissement

> **Finance Tracker n'est pas un conseiller en investissement.**
> Cet outil est éducatif. Rien de ce qu'il affiche ne constitue un conseil, une
> recommandation, une sollicitation ou une offre d'achat ou de vente d'un
> quelconque actif financier.

---

## Ce que cet outil n'est pas

Finance Tracker n'est **ni un conseiller en investissement financier (CIF), ni
un prestataire de services d'investissement, ni un prestataire de services sur
actifs numériques (PSAN/CASP)**. Il n'est enregistré ni auprès de l'AMF, ni
auprès d'aucune autorité de marché, en France ou ailleurs.

Il ne détient aucun fonds, aucune clé privée, et n'exécute aucune transaction.
Il n'a accès à aucun compte, aucun exchange, aucun portefeuille en écriture.

## Ce que fait le signal crypto

Il applique des règles écrites à l'avance — visibles dans
[`config/signal_rules.toml`](../config/signal_rules.toml) — à des métriques
**rétrospectives** : rendements passés, volatilité constatée, repli depuis un
plus haut, part du classement en momentum positif.

Quand toutes les barrières d'un mécanisme passent, l'outil propose un mouvement
et en chiffre les paramètres.

**C'est tout.** Il ne calcule aucune probabilité, n'entraîne aucun modèle, et
n'anticipe aucun prix. Un « verdict de rotation » est le résultat d'une
comparaison de chiffres passés à des seuils que tu peux relire et modifier.

## Ce qu'il ne fait pas, et ne peut pas faire

**Il ne prédit rien.** Aucun mécanisme n'anticipe une hausse ou une baisse.
Personne ne sait le faire de façon fiable, et un outil qui prétend le contraire
fait perdre de l'argent avec assurance.

**Il ne te connaît pas.** Il ignore ta situation financière, tes revenus, tes
charges, tes objectifs, ton horizon de placement, ta tolérance au risque et ton
niveau d'expérience. Un conseil en investissement digne de ce nom commence par
là. Cet outil ne le fait pas et ne peut pas le faire.

**Il n'exécute rien.** Un plan de swap est une liste de paramètres. Tu les
saisis toi-même, chez le fournisseur de ton choix, sous ta responsabilité.

## Les limites que tu dois connaître avant d'agir

### Les métriques décrivent le passé

Un actif qui a bien tenu pendant quatre-vingt-dix jours peut s'effondrer le
lendemain du scan. Les performances passées ne préjugent pas des performances
futures — la formule est banale, elle est aussi exacte.

### Les seuils sont des choix, pas des vérités

`min_score_delta = 1.5`, `required_consecutive_weeks = 3`, `repli_max_pct = 30` :
ces nombres viennent d'un calibrage sur un comportement observé, pas d'une
démonstration. Un autre calibrage donnerait d'autres verdicts. Ils sont dans un
fichier lisible précisément pour que tu puisses les contester.

### Un prix de revient reconstitué depuis une blockchain est une estimation

Une chaîne enregistre des **mouvements**, jamais un **prix d'achat**. Trois
sources d'erreur, aucune corrigeable depuis les données on-chain :

- un token reçu d'un swap est valorisé au cours du jour, alors que son vrai prix
  de revient est celui de l'actif cédé, qui vit sur une autre ligne ;
- un virement depuis un de tes propres portefeuilles non suivis est compté comme
  un achat, et gonfle le capital investi ;
- au-delà d'un an, le plan gratuit des données de marché ne sert plus de cours :
  ces unités sont comptées comme non expliquées.

L'outil affiche systématiquement la part non expliquée et un indice de confiance.
**Corrige la valeur à la main dès que tu connais ton vrai prix.** Ta valeur
remplace l'estimation partout, y compris dans le moteur.

Le stop suiveur et la prise de bénéfice se déclenchent sur cette plus-value. Une
sortie déclenchée sur un prix de revient deviné est une sortie sur une
hypothèse.

### Les coûts de swap sont des moyennes

Les frais affichés viennent de paramètres calibrés, pas de devis réels. L'écart
entre le meilleur et le pire fournisseur sur une même route est régulièrement de
plusieurs pourcents. **Comparer les devis pèse plus lourd sur le résultat que le
choix du candidat.** Demande toujours plusieurs devis.

### La donnée de marché peut être fausse ou absente

L'outil dépend d'une API publique gratuite. Un actif peut être mal classé, un
volume mal reporté, un historique trop court. Quand une métrique est inconnue,
la barrière correspondante **échoue** plutôt que de passer — mais un chiffre
erroné, lui, ne se détecte pas.

## Risques propres aux crypto-actifs

- **Volatilité extrême.** Des variations de plusieurs dizaines de pourcents en
  quelques jours sont ordinaires. **Tu peux perdre la totalité de ta mise.**
- **Risque technologique.** Bug de protocole, faille de pont, erreur d'adresse :
  une transaction envoyée est irréversible.
- **Risque de contrepartie.** Un stablecoin peut rompre son ancrage. Un émetteur
  peut geler des adresses.
- **Risque réglementaire.** Le cadre applicable change, et peut changer
  rétroactivement.
- **Risque de liquidité.** Un actif liquide au moment du scan peut ne plus
  l'être au moment où tu passes l'ordre.

## Fiscalité

Un échange entre crypto-actifs, et une cession contre monnaie ayant cours légal,
sont **généralement des faits générateurs d'imposition**.

Cet outil **ne calcule aucun impôt** et **ne produit aucun document fiscal**. Il
ne tient pas de registre au sens fiscal du terme. Les prix de revient qu'il
affiche sont conçus pour alimenter des règles de gestion, pas une déclaration.

Consulte un professionnel qualifié pour ta situation.

## Protection des données et vie privée

Tes données restent dans **ta** base SQLite. L'outil n'envoie rien à un serveur
central. Deux exceptions, toutes deux explicites :

1. **Les cours de marché** sont demandés à une API publique. Cette requête ne
   contient ni ton portefeuille, ni tes montants — seulement des identifiants
   d'actifs.
2. **Les portefeuilles suivis.** Interroger un indexeur **révèle ton adresse**
   à celui qui l'exploite. C'est pour cette raison que la synchronisation est
   activable par portefeuille, qu'une adresse enregistrée sans synchronisation
   n'est jamais envoyée, et que tu peux pointer l'outil vers ton propre nœud.

Les clés d'API que tu saisis sont stockées dans ta base : **elles partent avec le
fichier quand tu l'exportes**. Ne partage pas une sauvegarde qui en contient.

## En clair

Si tu suis une proposition de cet outil, **c'est ta décision et ton risque**.

Les auteurs et contributeurs de Finance Tracker déclinent toute responsabilité
quant aux pertes financières, directes ou indirectes, résultant de l'usage de ce
logiciel. Il est fourni « en l'état », sans garantie d'aucune sorte, comme le
précise sa [licence](../LICENSE).

Investis uniquement ce que tu peux te permettre de perdre entièrement. En cas de
doute, consulte un conseiller en investissement financier enregistré.

---

*Cet avertissement fait partie intégrante de la documentation. Il est affiché
dans l'application sur chaque page produisant un verdict, et rappelé à côté de
chaque plan de swap.*
