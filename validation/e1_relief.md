# E1, H3-E1 : l'erreur des sources de pluie selon le relief

Généré le 2026-11-03 par `scripts/validate_e1_relief.py`, selon `validation/protocole_e1_fusion_pluie.md` (section 6.2, seuils fixés le 03/11/2026 avant ce calcul). Triple collocation sur l'apprentissage 2001-2015, pentades de novembre à avril ; relief Copernicus GLO-90. Analyse descriptive.

r : corrélation médiane avec la pluie vraie (1 = parfaite). Variance d'erreur médiane en mm² par pentade (croît avec la quantité de pluie).

| Découpage | Classe | Mailles | r chirps | r imerg | r era5 | variance chirps | variance imerg | variance era5 |
|---|---|---|---|---|---|---|---|---|
| altitude | moins de 1 000 m | 4421 | 0.87 | 0.90 | 0.84 | 291 | 261 | 404 |
| altitude | Hautes Terres (≥ 1 000 m) | 844 | 0.87 | 0.89 | 0.82 | 314 | 261 | 406 |
| rugosité | moyen | 1755 | 0.88 | 0.89 | 0.84 | 285 | 267 | 401 |
| rugosité | plat | 1755 | 0.89 | 0.91 | 0.85 | 245 | 217 | 373 |
| rugosité | accidenté | 1755 | 0.86 | 0.89 | 0.83 | 366 | 287 | 442 |
| exposition | sans grand versant | 1421 | 0.89 | 0.90 | 0.85 | 259 | 228 | 377 |
| exposition | au vent (est) | 1659 | 0.84 | 0.92 | 0.81 | 562 | 285 | 664 |
| exposition | sous le vent (ouest) | 2185 | 0.88 | 0.88 | 0.85 | 254 | 265 | 352 |
| côte | côte (moins de 20 km) | 511 | 0.84 | 0.94 | 0.82 | 357 | 190 | 477 |
| côte | intérieur | 4754 | 0.87 | 0.89 | 0.84 | 291 | 267 | 401 |

Corrélation de Spearman, sur les mailles, entre r et la rugosité (négative : la source se dégrade en relief accidenté) : chirps -0.21 ; imerg -0.10 ; era5 -0.24.

