# Protocole : puits à sec et recharge (test secondaire de T2, T2L et T2K)

*Rédigé le 09/11/2026, **avant** tout calcul et avant la réception de la base BushProof. Test **secondaire** de la
même question que `protocole_recharge_chlorure.md` : quelle recharge est la plus juste ? Il ne décide rien à lui
seul. Toute modification sera datée en section 8.*

## 1. Question

Les puits signalés à sec en 2024-2025 se trouvent-ils plus souvent là où une recharge prédit peu d'eau ? Et laquelle
des trois recharges figées (T2, T2L, T2K) sépare le mieux les puits à sec des autres forages ?

## 2. Données

- **Cas** : « Dry and seasonal boreholes and wells – Madagascar » (Kaltsas, UNESCO IHP-WINS, 2025,
  doi:10.63253/r2yrjane, CC BY-SA), 477 points signalés de mars 2024 à juillet 2025. Données brutes hors du dépôt.
- **Référence** : les forages de la base BushProof (Al-Zoubaidy, Monteleone et Bünzli 2023), qui représentent les
  points d'eau existants. Données brutes hors du dépôt.
- **Emprise** : la zone commune aux deux bases (rectangle des forages BushProof). Hors de cette zone, aucun calcul.

## 3. Sélection (fixée avant calcul)

- Cas principal : signalé « à sec » avec une cause qui contient « well is dry » ou « débit insuffisant », **sans**
  panne mécanique, problème d'entretien, panne irréparable ni mauvaise gestion. Sensibilité : tous les points
  « Dry = Yes ».
- Référence : tous les forages BushProof, sauf ceux à moins de 200 m d'un cas (doublon possible).

## 4. Mesure

Pour chaque recharge, valeur de la maille la plus proche, sans aucun recalcul (cartes figées : T2 ; T2L
SHA-256 `2dc024a9…2291` ; T2K `c844a8bc…e4a`). Pouvoir de séparation : **AUC** de « recharge faible » pour
distinguer les cas de la référence (0,5 = aucun pouvoir). Intervalle de confiance à 95 % par rééchantillonnage
de blocs de 20 km (les points voisins ne sont pas indépendants), 2 000 tirages, graine fixée à 20261109.

## 5. Hypothèse (fixée avant calcul)

- **H-P1 (principale)** : T2L ou T2K sépare mieux que T2 : AUC supérieure d'au moins 0,05, et l'intervalle de la
  différence avec T2 ne contient pas 0. Ce test compare toujours à T2 : si T2 sépare déjà bien, un nouveau modèle
  ne gagne que s'il fait **mieux**.
- Publié sans hypothèse : l'AUC de T2 elle-même, et le même calcul sur la sensibilité « tous les points à sec ».

## 6. Usage du résultat

Le test des puits **appuie ou affaiblit** le verdict du bilan de chlorure ; il ne le remplace pas. Une recharge
retenue par le chlorure (H-Cl2 ou H-Cl3) qui sépare **moins bien** que T2 les puits à sec (AUC inférieure de plus
de 0,05) sera signalée comme contradictoire, et la décision sera rediscutée avec le porteur du projet.

## 7. Limites

- On ne voit que les points signalés : la campagne de signalement (lieux, dates) peut ne pas couvrir tout le Sud.
- Un puits peut sécher pour des raisons sans lien avec la recharge (puits trop peu profond, pompage excessif, année
  sèche). Les données ne donnent pas la profondeur des puits signalés.
- 2024-2025 est une période particulière ; la recharge des modèles est une moyenne de long terme.

## 8. Journal des modifications

- 09/11/2026 : version initiale.
