# Intensité infra-journalière (IMERG) contre cumul, pour les inondations pluviales du périmètre pilote

Généré le 2026-11-09 par `scripts/validate_imerg_pluvial.py`, selon `validation/protocole_intensite_imerg.md` (fixé avant les calculs).

- GPM IMERG V07 Final, pas de 30 min, 0,1° : 11 saisons (novembre 2014 à avril 2025), 406 mailles contenant au moins un fokontany du périmètre.
- Événements : 3 de `evenements.csv` (périmètre), 13 dates DesInventar (districts du périmètre, avec impact).
- Seuils par maille et par durée sans la saison testée ; score = part des mailles au-dessus du seuil de vigilance.

## 1. Jours d'événement contre autres jours (aire sous la courbe ROC, IC à 95 % par bootstrap des saisons)

| Durée | Jours | Jours d'événement | AUC | IC 95 % |
|---|---|---|---|---|
| 1.0 h | 1994.0 | 43.0 | 0,40 | [0,33 ; 0,60] |
| 3.0 h | 1994.0 | 43.0 | 0,40 | [0,34 ; 0,58] |
| 6.0 h | 1994.0 | 43.0 | 0,38 | [0,35 ; 0,46] |
| 24.0 h | 1994.0 | 43.0 | 0,42 | [0,40 ; 0,48] |
| 72.0 h | 1994.0 | 43.0 | 0,48 | [0,43 ; 0,64] |

**H1** (AUC 3 h > AUC 72 h) : différence, IC 95 % [-0,28 ; -0,01] -> **contredite (le cumul l’emporte)**.

## 2. Détection des événements (part des mailles ≥ 10 %)

| Durée | Événements couverts | Détectés |
|---|---|---|
| 1 h | 6 | 0 |
| 3 h | 6 | 0 |
| 6 h | 6 | 0 |
| 24 h | 6 | 2 |
| 72 h | 6 | 0 |

## 3. Épisodes et fausses alertes possibles (borne haute)

| Durée | Seuil de part | Épisodes | Avec événement du périmètre | Sans aucune correspondance |
|---|---|---|---|---|
| 1 h | au moins 1 | 104 | 5 | 68 |
| 1 h | 5 % | 21 | 0 | 13 |
| 1 h | 10 % | 6 | 0 | 4 |
| 1 h | 25 % | 0 | 0 | 0 |
| 3 h | au moins 1 | 106 | 8 | 69 |
| 3 h | 5 % | 19 | 0 | 13 |
| 3 h | 10 % | 4 | 0 | 3 |
| 3 h | 25 % | 0 | 0 | 0 |
| 6 h | au moins 1 | 111 | 5 | 77 |
| 6 h | 5 % | 28 | 0 | 16 |
| 6 h | 10 % | 8 | 0 | 5 |
| 6 h | 25 % | 1 | 0 | 0 |
| 24 h | au moins 1 | 98 | 5 | 67 |
| 24 h | 5 % | 26 | 1 | 13 |
| 24 h | 10 % | 13 | 1 | 5 |
| 24 h | 25 % | 5 | 1 | 1 |
| 72 h | au moins 1 | 83 | 4 | 55 |
| 72 h | 5 % | 31 | 2 | 14 |
| 72 h | 10 % | 16 | 0 | 7 |
| 72 h | 25 % | 5 | 0 | 2 |

## Limites

- IMERG (0,1°, ~11 km) lisse les orages très locaux ; l'inondation urbaine dépend aussi du drainage.
- Peu d'événements : les intervalles sont larges.
- Les fiches DesInventar sont des déclarations ; leur absence n'est pas une absence d'impact.
