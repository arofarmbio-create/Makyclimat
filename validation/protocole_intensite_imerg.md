# Protocole : l'intensité infra-journalière (IMERG) détecte-t-elle mieux les inondations pluviales que le cumul ?

*Rédigé le 29/10/2026, **avant** tout calcul. Modifications datées en section 5. Cahier des charges §7.A (cumuls 1, 3,
6, 24, 72 heures), §13.*

## 1. Question

Sur le périmètre pilote (Antananarivo, Analamanga, Vakinankaratra), les inondations documentées sont-elles mieux
distinguées des autres jours de saison par l'intensité courte (1 h, 3 h, 6 h) que par le cumul long (24 h, 72 h) ?
On utilise **le même produit** (GPM IMERG V07 Final) pour toutes les durées : la comparaison isole l'effet de la
durée, sans effet de produit.

Pourquoi c'est utile pour la thèse : l'indicateur de ruissellement SCS-CN (CHIRPS, 3 jours) détecte 3 événements
sur 3, mais avec seulement 2 événements indépendants. L'inondation urbaine d'Antananarivo est réputée liée aux orages
courts, une hypothèse jamais testée sur des données locales.

## 2. Données

- IMERG V07 Final au pas de 30 min et à 0,1°, saisons novembre-avril 2014-2015 à 2024-2025 (11 saisons). On garde les
  mailles qui contiennent le centroïde d'au moins un fokontany du périmètre.
- Événements : `validation/evenements.csv` (zones citées dans le périmètre), plus les fiches DesInventar cyclone ou
  inondation datées, au district, dans les districts du périmètre, avec impact, et sans date douteuse.

## 3. Méthode

- Pour chaque maille et chaque durée D (1, 3, 6, 24, 72 h) : maximum journalier du cumul glissant sur D.
- Seuils par maille et par durée : médiane (vigilance, environ 2 ans) et 80e centile (alerte, environ 5 ans) des
  maxima saisonniers. Ils sont calculés **sans la saison testée**.
- Score journalier : part des mailles au-dessus du seuil de vigilance.
- Jours d'événement :
  - pour `evenements.csv`, la fenêtre [début − 2 j, fin + 10 j], comme pour les autres validations ;
  - pour DesInventar, la date ± 1 jour.
- Mesures, par durée :
  - (a) aire sous la courbe ROC du score journalier, jours d'événement contre autres jours de saison ;
  - (b) détection des événements (part ≥ 10 %) ;
  - (c) épisodes et épisodes sans aucune correspondance (évenements, DesInventar, GDACS), aux seuils de part 1, 5,
    10 et 25 %.
- Incertitude de l'aire ROC : bootstrap par saison (1 000 tirages).

## 4. Hypothèse fixée à l'avance

- **H1** : l'aire ROC de l'intensité sur 3 h est supérieure à celle du cumul sur 72 h. Le test porte sur l'intervalle
  de confiance de la différence, apparié par saison.
- Un résultat contraire est publiable : il dirait que le cumul, donc la saturation, domine à l'échelle de 0,1°.

Limites connues :
- IMERG sous-estime les pics convectifs très locaux, et une maille fait environ 11 km.
- L'inondation urbaine dépend aussi du drainage et des digues.
- Il y a peu d'événements.

## 5. Journal des modifications

- 29/10/2026 : version initiale.
