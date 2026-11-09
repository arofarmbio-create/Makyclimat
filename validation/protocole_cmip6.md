# Protocole : projections climatiques CMIP6 pour Madagascar (expérience E6)

*Rédigé le 09/11/2026, **avant** tout téléchargement et tout calcul. Exigé par le protocole doctoral (E6, horizons
2030, 2050, 2070, 2100 ; scénarios SSP1-2.6, SSP2-4.5, SSP5-8.5) et par `prompt_maitre.md` (section 9). Toute
modification sera datée en section 10.*

## 1. Questions

1. **Évaluation** : les modèles CMIP6 régionalisés reproduisent-ils le climat observé de Madagascar (1981-2014) ?
2. **Projections** : comment changent, par région et par scénario, la pluie de saison, la fréquence des mois de pluie
   extrême et la température, aux horizons 2021-2040, 2041-2060, 2061-2080 et 2081-2100 ?
3. **Lien avec la thèse** : la recharge du Grand Sud étant épisodique (`methodologie_these.md`, section 7.1), la
   fréquence des mois extrêmes compte plus que la pluie moyenne. Les projections portent donc sur les **moteurs** de la
   recharge, pas sur des valeurs de recharge : T2 n'est pas assez fiable pour être projetée.

## 2. Données

- **NEX-GDDP-CMIP6** (NASA) : projections journalières régionalisées et corrigées des biais, 0,25°, historique
  1950-2014 et SSP1-2.6, SSP2-4.5, SSP5-8.5 jusqu'en 2100 ; un membre par modèle (r1i1p1f1 ou le premier disponible) ;
  tous les modèles qui ont les trois scénarios. Variables : pluie (pr), température moyenne (tas), maximale (tasmax).
  **Licence à vérifier par modèle avant tout téléchargement** (l'agent la consigne ; les modèles sous licence
  restrictive sont exclus).
- **Observations** : CHIRPS v2.0 mensuel (pluie), ERA5-Land (température), déjà dans le système.
- Emprise : 43 à 51° E, 26 à 11,5° S. Agrégation au mois puis par région (moyenne pondérée par la surface des
  fokontany, même méthode que `build_teleconnections.region_series`).
- Volume : le journalier complet est trop lourd pour la connexion locale ; le calcul tourne sur GitHub, qui ne garde que
  les agrégats mensuels par région (release du dépôt).

## 3. Évaluation des modèles (1981-2014, contre CHIRPS)

Par modèle et par région :
- biais relatif de la pluie de saison (novembre-avril) ;
- corrélation du cycle annuel (12 mois) ;
- rapport des écarts-types interannuels de la pluie de saison ;
- fréquence des mois au-dessus du 95e centile des mois de novembre à avril (seuil de chaque source, calculé sur
  1981-2014).

**Règle de sélection fixée maintenant** : un modèle est retenu pour une région si le biais de la pluie de saison est
compris entre −20 et +20 %, la corrélation du cycle annuel est au moins 0,9, et le rapport des écarts-types est compris
entre 0,5 et 2. Les projections sont publiées pour l'ensemble complet **et** pour l'ensemble retenu.

## 4. Changements projetés

Par région, scénario et horizon, par rapport à 1995-2014 : changement relatif de la pluie de saison et de la pluie de
janvier à mars ; changement de la fréquence des mois extrêmes (seuil historique de chaque modèle) ; changement de
température moyenne et maximale.

## 5. Robustesse (méthode du GIEC, AR6, Atlas : approche « C »)

Un changement est dit :
- **robuste** si au moins 80 % des modèles donnent le même signe **et** si au moins 66 % des modèles ont un changement
  supérieur à la variabilité interne (écart-type des moyennes sur 20 ans de la période de contrôle × √2) ;
- **incertain** (signal faible) si moins de 66 % des modèles dépassent la variabilité interne ;
- **contradictoire** si au moins 66 % dépassent la variabilité interne mais moins de 80 % s'accordent sur le signe.

## 6. Hypothèses (fixées avant calcul)

Puissance : le critère porte sur l'accord entre modèles (au moins une vingtaine de modèles attendus), pas sur un test à
faible effectif ; l'analyse de puissance n'est pas pertinente au sens des tests précédents. Le nombre de modèles
disponibles sera publié en premier.

- **H-P1** : la température moyenne augmente de façon robuste dans toutes les régions pour SSP2-4.5 et SSP5-8.5 en
  2041-2060 et 2081-2100 (attendu, contrôle de cohérence).
- **H-P2** : dans le Grand Sud (Atsimo-Andrefana, Androy, Anosy), le changement de la pluie de saison en 2081-2100
  sous SSP5-8.5 est robuste (signe non fixé d'avance : bilatéral).
- **H-P3** : dans le Grand Sud, le changement de la fréquence des mois extrêmes est robuste en 2081-2100 sous SSP5-8.5
  (signe non fixé d'avance).
- **Contrôle** : les modèles retenus reproduisent le signe du lien El Niño → pluie du Sud-Ouest observé (`hn7_maillon_a.md`,
  ρ = −0,24), à titre descriptif.

## 7. Sorties

`validation/cmip6_evaluation.md` (tableau des modèles par région), `validation/cmip6_projections.md` (changements,
robustesse, cartes par région), agrégats mensuels par région en release ; pour le site, des fourchettes et non des
valeurs uniques.

## 8. Limites

- NEX-GDDP corrige les biais par rapport à son propre jeu de référence, pas CHIRPS ; l'évaluation de la section 3 le
  mesure.
- Un seul membre par modèle : la variabilité interne est estimée sur la période de contrôle, pas par des ensembles.
- La régionalisation statistique ne crée pas de processus absents des modèles globaux (cyclones mal résolus).
- Les projections de recharge ne sont pas faites (section 1, question 3).

## 9. Mise en œuvre

1. L'agent de téléchargement vérifie la liste des modèles et leurs licences, puis prépare un workflow GitHub qui lit
   NEX-GDDP-CMIP6 par sous-ensemble (emprise de Madagascar), agrège au mois et par région, et publie les agrégats.
2. Un modèle d'abord (essai), puis tous, un à la fois.
3. Calcul de l'évaluation, puis des projections, selon ce protocole.

## 10. Journal des modifications

- 09/11/2026 : version initiale.
