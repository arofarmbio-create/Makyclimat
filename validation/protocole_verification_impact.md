# Protocole : vérification par l'impact des prévisions d'ensemble de crue (GloFAS) dans un pays sans station hydrométrique

*Protocole rédigé le 29/10/2026, **avant** tout calcul de score, pour éviter d'ajuster la méthode aux résultats.
Toute modification ultérieure sera datée et justifiée dans la section 9. Chapitre de thèse visé : vérification des
prévisions (cahier des charges §8 approche 3, §11, §13).*

## 1. Question de recherche

Dans un pays insulaire où aucune série de débit observé n'est publique, les probabilités d'ensemble d'un système mondial
de prévision des crues (GloFAS v4) anticipent-elles les **impacts déclarés** au niveau du district ? Si oui, avec quel
délai, avec quelle fiabilité, et à partir de quelle probabilité une action anticipée a-t-elle une valeur économique
positive ?

## 2. Positionnement et nouveauté revendiquée

Travaux existants les plus proches :
- Mitheu et al. (2025), *Journal of Flood Risk Management* 18, e12911 : vérification de GloFAS v3.1 (2007-2018) en
  Ouganda et au Kenya contre des données d'impact (DFO, DesInventar, EM-DAT, sources locales), **aux emplacements des
  stations hydrométriques**, qui restent la référence.
- Zsoter et al. (2020), *Journal of Flood Risk Management* : seuils de crue tirés des reprévisions d'ensemble elles-mêmes.
- Reprévisions GloFAS et leur compétence mondiale face à la persistance (HESS 27, 1, 2023).
- Kuipers et al. (2026), *Journal of Flood Risk Management*, e70247 : GloFAS v4.0/v3.0 et Google Flood Hub au Mali,
  évalués avec des données d'impact **et** des débits observés ; compétence suffisante au-delà de 4 jours dans les
  régions souvent inondées.
- Prépublication EGUsphere-2025-3473 : prévision du nombre de personnes exposées aux crues cycloniques en Afrique
  australe orientale (ECMWF + GloFAS + cartes Fathom + WorldPop) sur des événements récents. C'est une chaîne de
  prévision d'exposition étudiée événement par événement, pas une vérification statistique pluriannuelle contre une
  base de pertes.
- Recherche du 29/10/2026 (moteur web) : **aucune évaluation de GloFAS publiée pour Madagascar n'a été trouvée.**

Ce que ce protocole ajoute (à confirmer par une revue de littérature complète avant rédaction) :
1. **Aucune station** : l'impact déclaré est la seule vérité terrain, et non un complément aux stations.
2. **Couverture nationale par district** (environ 114 districts), et non quelques points de station.
3. **Régime dominé par les cyclones tropicaux** : la crue y est un aléa composé (vent, pluie, crue). On sépare les
   épisodes cycloniques et non cycloniques.
4. **GloFAS v4** (maille 0,05°), probabilités d'ensemble complètes : fiabilité, valeur économique relative et choix du
   seuil de déclenchement, comparés au seul scénario de contrôle.
5. **Méthode transférable et reproductible** : tout passe par `config/countries/<pays>.yml` (code DesInventar, emprise).
   GloFAS est mondial et DesInventar couvre environ 90 pays ; le code et les décomptes agrégés sont publics.
6. Premier travail de ce type à notre connaissance pour **Madagascar**.

## 3. Données

| Rôle | Jeu de données | Période | Remarque |
|---|---|---|---|
| Prévision | Reprévisions GloFAS v4 (`cems-glofas-reforecast`, Copernicus EWDS) : contrôle + 10 membres, échéances 1 à 15 jours | 1999-2023 (vérification sur 1999-2019, années couvertes par DesInventar) | Débit journalier, maille 0,05° |
| Seuils | (a) climat du modèle de reprévision, par échéance ; (b) réanalyse GloFAS (seuils actuels du site) | 1999-2018 / 1984-2025 | (a) est la référence, (b) un test de sensibilité |
| Vérité terrain | DesInventar Madagascar (UNDRR, fiches BNGRC) : fiches « cyclone » et « inondation » par district | 1999-2018 | `scripts/connector_desinventar.py` ; 723 fiches, 113 districts |
| Vérité secondaire | `validation/evenements.csv`, GDACS (sources indépendantes de GloFAS), Copernicus EMS | variable | Corroboration seulement |

Les fiches DesInventar brutes ne sont ni versionnées ni republiées : aucune licence de données explicite n'existe, on
applique donc la même règle que pour EM-DAT.

## 4. Unités et appariement

- **Unité de vérification** : district × date d'initialisation de la prévision.
- **Cellules de rivière d'un district** : cellules GloFAS dans le district dont le débit moyen simulé dépasse
  `q_min`. On fixe `q_min = 5 m³/s`, déjà utilisé pour l'alerte du site, et on teste aussi 1 et 20 m³/s.
- **Prévision** : P = part des membres pour lesquels au moins une cellule de rivière du district dépasse sa crue de
  période de retour T (T = 2 et 5 ans) dans la fenêtre d'échéance [L1, L2]. On teste trois fenêtres : 1-3, 4-7 et
  8-15 jours.
- **Observation** : 1 s'il existe au moins une fiche cyclone ou inondation dans le district, datée dans
  [t + L1 − 1 j, t + L2 + 1 j], avec au moins une personne touchée ou une maison endommagée. Sinon 0.
- Les fiches sans jour précis sont exclues de l'appariement et seulement comptées.

## 5. Biais de déclaration (limite principale, traitée explicitement)

L'absence de fiche ne prouve pas l'absence d'impact. On applique donc les règles suivantes :
- Analyse limitée aux saisons des pluies (novembre-avril) et aux saisons où la base contient au moins une fiche
  cyclone ou inondation pour le pays.
- Les fausses alertes sont présentées comme une **borne haute**.
- On réalise une analyse de sensibilité avec les seuls districts ayant déclaré au moins un événement sur la période.

## 6. Scores

- Score de Brier et Brier Skill Score par rapport à la climatologie d'impact du district (fréquence d'impact par
  saison, calculée sans la saison testée).
- Diagramme de fiabilité (10 classes, ou moins si les effectifs sont faibles) et aire sous la courbe ROC.
- Taux de détection et taux de fausses alertes, aux seuils de probabilité 10, 20, …, 90 %.
- Valeur économique relative (Richardson 2000) pour des rapports coût/perte de 0,01 à 0,99. Seuil de déclenchement
  optimal selon ce rapport.
- Toutes ces mesures par fenêtre d'échéance, pour le contrôle seul et pour l'ensemble, et séparément pour les épisodes
  cycloniques et non cycloniques.
- Incertitude : intervalles de confiance à 95 % par bootstrap **par saison** (blocs), pour respecter la dépendance
  entre districts touchés par un même cyclone.

## 7. Absence de fuite de données

- Les seuils du climat du modèle sont calculés en validation croisée, en laissant une saison de côté.
- Aucun paramètre (`q_min`, T, seuil de probabilité) n'est choisi sur les données de test : le choix est fait dans
  la validation croisée par saison, et les valeurs de remplacement sont toujours rapportées.

## 8. Résultats attendus et critères de réussite fixés à l'avance

- **H1** : l'ensemble a une aire ROC supérieure à 0,5 à 1-3 jours (intervalle de confiance au-dessus de 0,5).
- **H2** : la compétence décroît avec l'échéance.
- **H3** : l'ensemble apporte une valeur économique supérieure au contrôle seul pour au moins une partie des rapports
  coût/perte.
- **H4** : la compétence est plus forte pour les épisodes cycloniques que pour les autres.

Un résultat négatif (aucune compétence démontrable) est un résultat publiable et sera présenté comme tel.

## 9. Journal des modifications du protocole

- 29/10/2026 : version initiale.
- 29/10/2026, avant tout calcul de score (précisions imposées par le format des données, pas par des résultats) :
  - **Cellules de rivière** : le débit moyen n'est pas conservé par la réduction des reprévisions (maximum par fenêtre
    d'échéance seulement). Le critère « débit moyen > `q_min` » devient « crue de 2 ans du modèle ≥ `q_min` ». C'est
    la règle déjà appliquée par l'alerte du site (`flood.min_q2_m3s`), avec `q_min = 5 m³/s` comme référence et
    20 et 50 m³/s comme sensibilité. Le seuil de 1 m³/s est sans objet, car les mailles sous 5 m³/s ne sont pas
    conservées.
  - **Seuils du climat du modèle** : pour chaque maille et chaque fenêtre d'échéance, Gumbel (méthode des moments)
    ajusté sur les maxima saisonniers (novembre-avril) du scénario de contrôle. Seules les saisons complètes sont
    retenues (novembre 1999 - avril 2023, soit 24 saisons), et il faut au moins 15 saisons disponibles par maille.
    La saison testée est exclue de l'ajustement.
  - **Saisons vérifiées** : novembre 1999 - avril 2019 (20 saisons), limite de DesInventar.

## Références

- Mitheu F. et al. (2025). The utility of impact data in flood forecast verification for anticipatory actions: case
  studies from Uganda and Kenya. *J. Flood Risk Manag.* 18, e12911. https://onlinelibrary.wiley.com/doi/10.1111/jfr3.12911
- Zsoter E. et al. (2020). Using ensemble reforecasts to generate flood thresholds for improved global flood
  forecasting. *J. Flood Risk Manag.* https://onlinelibrary.wiley.com/doi/full/10.1111/jfr3.12658
- Daily ensemble river discharge reforecasts and real-time forecasts from the operational Global Flood Awareness
  System. *HESS* 27, 1 (2023). https://hess.copernicus.org/articles/27/1/2023/
- Kuipers et al. (2026). Assessing the riverine flood forecast skill of GloFAS and Google Flood Hub with impact data
  and discharge observations to support early actions in Mali. *J. Flood Risk Manag.* https://onlinelibrary.wiley.com/doi/10.1111/jfr3.70247
- Forecasting people exposed to tropical cyclone flooding in Southeast Africa: lessons learned from recent events.
  Prépublication EGUsphere-2025-3473. https://egusphere.copernicus.org/preprints/2025/egusphere-2025-3473/
- Richardson D. S. (2000). Skill and relative economic value of the ECMWF ensemble prediction system. *Q. J. R.
  Meteorol. Soc.* 126, 649-667.
