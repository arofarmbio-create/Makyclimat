# R-21 — Couverture effective des seuils de crue

Calcul du 11/11/2026 par [`scripts/r21_couverture_seuils.py`](../scripts/r21_couverture_seuils.py) sur 53 fichiers mensuels de la release `reprevisions-glofas-v4`. Aucun score calculé (verrou R-21). Mailles : union des 20570 mailles des fichiers ; éligibles = rattachées à un district et crue de 2 ans ≥ 5 m³/s (règle du script R-21). Minimum d'apprentissage : 15 blocs hors saison testée. Fenêtres : 1-3 j, 4-7 j, 8-15 j.

## 1. Mois disponibles par saison

| Saison | Mois | Nombre |
|---|---|---:|
| 2003 | nov., déc., jan., fév., mars, avr. | 6 |
| 2004 | nov., déc., jan., fév., mars, avr. | 6 |
| 2005 | nov., déc., jan., fév., mars, avr. | 6 |
| 2006 | nov., jan., fév. | 3 |
| 2007 | jan., fév. | 2 |
| 2008 | jan., fév. | 2 |
| 2009 | jan., fév., mars | 3 |
| 2010 | déc., jan. | 2 |
| 2011 | jan., fév., mars | 3 |
| 2012 | déc., jan., fév., mars | 4 |
| 2013 | déc. | 1 |
| 2016 | jan., fév., mars | 3 |
| 2017 | déc., jan. | 2 |
| 2018 | jan., fév., mars | 3 |
| 2019 | déc., jan., fév. | 3 |
| 2020 | déc. | 1 |
| 2022 | jan. | 1 |

17 saisons ont au moins un mois. Retirer la saison testée en laisse au plus 16.

## 2. Règle actuelle : maximum sur les mois disponibles

Mailles éligibles : 16689 (crue de 2 ans estimée sur toutes les saisons disponibles, au moins 3, ≥ 5 m³/s pour une fenêtre, district connu). Le script R-21 applique ce filtre saison par saison.

| Saison testée | Saisons d'apprentissage | Mailles éligibles avec seuil (min–max sur les fenêtres) |
|---|---:|---|
| 2003 | 16 au plus | 91 – 91 % |
| 2004 | 16 au plus | 91 – 91 % |
| 2005 | 16 au plus | 91 – 91 % |
| 2006 | 16 au plus | 91 – 91 % |
| 2007 | 16 au plus | 91 – 91 % |
| 2008 | 16 au plus | 91 – 91 % |
| 2009 | 16 au plus | 91 – 91 % |
| 2010 | 16 au plus | 91 – 91 % |
| 2011 | 16 au plus | 91 – 91 % |
| 2012 | 16 au plus | 91 – 91 % |
| 2013 | 16 au plus | 94 – 94 % |
| 2016 | 16 au plus | 91 – 91 % |
| 2017 | 16 au plus | 92 – 92 % |
| 2018 | 16 au plus | 91 – 91 % |

## 3. Biais d'un maximum calculé sur un seul mois

Saisons où déc.-mars sont tous disponibles : 2003, 2004, 2005, 2012. Pour chacune, rapport entre le maximum d'un mois et le maximum de déc.-mars, médiane sur les mailles éligibles et les fenêtres (1 = aucun biais).

| Mois seul | Rapport médian | Part des cas où le mois porte le maximum |
|---|---:|---:|
| déc. | 0,23 | 11 % |
| jan. | 0,79 | 38 % |
| fév. | 0,72 | 36 % |
| mars | 0,47 | 20 % |

Un seuil appris sur des saisons d'un ou deux mois est donc trop bas : il gonfle les dépassements prévus, différemment selon les saisons.

## 4. Corrections à mois identiques

**A. Janvier seul** (maximum de janvier, une valeur par saison). **B. Blocs mensuels déc.-mars** : chaque mois disponible est un bloc, seuil de Gumbel sur les maxima mensuels ; la période de retour mensuelle T_m = 1 / (1 − 0,5^(1/4)) ≈ 6,3 correspond à la crue de 2 ans sur déc.-mars si les mois étaient indépendants (hypothèse à discuter : persistance des débits d'un mois à l'autre). Seuil exigé : 30 blocs.

| Saison testée | A : saisons avec janvier | A : couverture | B : blocs déc.-mars | B : couverture |
|---|---:|---|---:|---|
| 2003 | 14 | 0 – 0 % | 40 | 93 – 93 % |
| 2004 | 14 | 0 – 0 % | 40 | 93 – 93 % |
| 2005 | 14 | 0 – 0 % | 40 | 94 – 94 % |
| 2006 | 14 | 0 – 0 % | 42 | 94 – 94 % |
| 2007 | 14 | 0 – 0 % | 42 | 94 – 94 % |
| 2008 | 14 | 0 – 0 % | 42 | 94 – 94 % |
| 2009 | 14 | 0 – 0 % | 41 | 94 – 94 % |
| 2010 | 14 | 0 – 0 % | 42 | 95 – 95 % |
| 2011 | 14 | 0 – 0 % | 41 | 94 – 94 % |
| 2012 | 14 | 0 – 0 % | 40 | 94 – 94 % |
| 2013 | 15 | 87 – 87 % | 43 | 95 – 95 % |
| 2016 | 14 | 0 – 0 % | 41 | 94 – 94 % |
| 2017 | 14 | 0 – 0 % | 42 | 95 – 95 % |
| 2018 | 14 | 0 – 0 % | 41 | 94 – 94 % |

Saisons sans janvier : 2013, 2014, 2015, 2020, 2021 (5 mois à télécharger pour avoir janvier sur les 20 saisons 2003-2022). Mois de déc.-mars manquants sur ces saisons : 36.

