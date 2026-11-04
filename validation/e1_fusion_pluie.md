# E1 : fusion contrôlée des sources de pluie

Généré le 2026-11-04 par `scripts/validate_e1.py`, selon `validation/protocole_e1_fusion_pluie.md` (fixé avant les calculs). Années disponibles : 2001-2025 (9131 jours communs).

## Triple collocation (apprentissage 2001-2015, pentades de novembre à avril)

| Source | Variance d'erreur médiane (mm² par pentade) | Corrélation médiane avec la pluie vraie (r) |
|---|---|---|
| chirps | 296.70 | 0.87 |
| imerg | 260.80 | 0.90 |
| era5 | 404.67 | 0.84 |

Meilleure source seule (fixée sur l'apprentissage) : **imerg**. Mailles avec poids égaux (variance négative ou indéfinie) : 6359.

## Stations GSOD (test 2016-2025, pentades)

| Hypothèse | Stations favorables | Stations | p (test du signe) | Conclusion |
|---|---|---|---|---|
| H1-E1 : KGE(C) > KGE(imerg) | 2 | 5 | 0.81 | non soutenue |
| H1-E1b : KGE(C) > KGE(B) | 2 | 5 | 0.81 | non soutenue |

| Station | Pentades | KGE CHIRPS | KGE IMERG | KGE ERA5-Land | KGE B | KGE C |
|---|---|---|---|---|---|---|
| FASCENE | 102 | 0.60 | 0.56 | 0.51 | 0.62 | 0.55 |
| SAMBAVA | 115 | 0.43 | 0.46 | 0.12 | 0.38 | 0.42 |
| SAINTE MARIE | 140 | 0.61 | 0.46 | 0.50 | 0.54 | 0.79 |
| TOAMASINA | 303 | 0.55 | 0.40 | 0.44 | 0.51 | 0.47 |
| TOLAGNARO | 109 | 0.20 | 0.39 | 0.28 | 0.35 | 0.34 |

Rappel (protocole §7) : CHIRPS intègre des stations GTS, probablement en partie celles-ci ; la comparaison aux stations le favorise, ainsi que C.
