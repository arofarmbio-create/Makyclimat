# Test THMS (mémoire hydrique du sous-sol) dans le Grand Sud

Généré le 2026-11-04 par `scripts/thms_test_sud.py`, selon `validation/protocole_thms_test_sud.md` (fixé avant le calcul ; idée du porteur du projet). Niveaux : MGMERL (HT) et Carrière et al. 2021 (GROSoM) ; pluie CHIRPS ; ET0 Open-Meteo (ERA5-Land). Calage sur les 60 % premiers jours de chaque série, validation sur les 40 % suivants.

| Site | Aquifère | Jours (calage / validation) | M choisi (AIC) | KGE validation M = 1 | KGE validation M choisi | Poids rapide w1 | T1 (jours) |
|---|---|---|---|---|---|---|---|
| Andaboly | Basement | 506 / 338 | 2 | 0.03 | 0.24 | 0.49 | 28 |
| Sihanamaro | Unconsolidated | 954 / 636 | 1 | -0.31 | -0.31 | 1.00 | 110 |
| Ihazoambo | Basement | 489 / 326 | 3 | 0.47 | 0.46 | 0.25 | 2 |
| Ankaramena | Basement | 513 / 342 | 1 | -20.30 | -20.30 | 1.00 | 344 |
| AnKaranabO | Basement | 709 / 474 | 3 | 0.42 | 0.37 | 0.29 | 1 |
| Nosiomby | Basement | 645 / 431 | 2 | 0.48 | 0.62 | 0.07 | 1 |
| Mahavelo | Basement | 622 / 415 | 2 | 0.17 | 0.12 | 0.21 | 2 |
| Maroarivo | Unconsolidated | 576 / 385 | 1 | 0.18 | 0.18 | 1.00 | 1 |
| Ambatofotsy | Unconsolidated | 762 / 508 | 1 | 0.73 | 0.73 | 1.00 | 8 |
| Ankandy | Unconsolidated | 1210 / 807 | 1 | 0.46 | 0.46 | 1.00 | 1 |
| Ankazomanga_P06 | Unconsolidated | 901 / 602 | 1 | -0.77 | -0.77 | 1.00 | 55 |
| Ankazomanga_P01 | Unconsolidated | 1242 / 829 | 1 | 0.70 | 0.70 | 1.00 | 10 |

**H-M1** : le modèle choisi par l'AIC bat la mémoire unique en validation sur 2 sites sur 12 (règle : au moins 9 sur 12 ; test du signe p = 0.997). **Non soutenue**.
Sites où l'AIC garde une seule mémoire : 7 (égalité, comptée comme non-victoire).

H-M2 et H-M3 (exploratoires) : voir les colonnes w1 et T1 selon l'aquifère ; aucune conclusion confirmatoire.

