# E1, section 6.3 : les versions de la pluie face aux impacts

Généré le 2026-11-04 par `scripts/validate_e1_impacts.py`, selon `validation/protocole_e1_fusion_pluie.md` (précisions du 03/11/2026, fixées avant ce calcul). Descriptif : peu d'événements, aucun test de signification.

## Inondations pluviales du périmètre pilote (pluie sur 3 jours, seuils locaux de 2001-2015, saisons 2016-2017 à 2024-2025)

| Version | Événements détectés | Épisodes | Épisodes sans correspondance | AUC des communes EMS |
|---|---|---|---|---|
| chirps | 3 / 4 | 8 | 4 | 0.18;0.73;0.80 |
| imerg | 3 / 4 | 11 | 5 | 0.72;0.29;0.10 |
| era5 | 2 / 4 | 16 | 5 | 0.68;0.21;0.50 |
| B | 3 / 4 | 13 | 3 | 0.43;0.39;0.60 |
| C | 3 / 4 | 14 | 3 | 0.57;0.53;0.25 |

## Sécheresse du Grand Sud (2019-07 à 2023-06) : SPI minimum et rang parmi 24 régions (1 = la plus sèche)

| Version | Indice | Androy | Anosy | Atsimo Andrefana |
|---|---|---|---|---|
| chirps | SPI-3 | -2.22 (rang 5) | -2.25 (rang 4) | -2.40 (rang 2) |
| chirps | SPI-12 | -2.55 (rang 2) | -2.38 (rang 4) | -2.20 (rang 8) |
| imerg | SPI-3 | -2.37 (rang 10) | -2.29 (rang 14) | -2.10 (rang 20) |
| imerg | SPI-12 | -2.92 (rang 3) | -2.76 (rang 7) | -2.60 (rang 11) |
| era5 | SPI-3 | -2.48 (rang 6) | -2.44 (rang 9) | -2.47 (rang 7) |
| era5 | SPI-12 | -2.95 (rang 1) | -2.84 (rang 3) | -2.74 (rang 4) |
| B | SPI-3 | -2.57 (rang 1) | -2.45 (rang 4) | -2.11 (rang 14) |
| B | SPI-12 | -2.91 (rang 1) | -2.79 (rang 2) | -2.57 (rang 6) |
| C | SPI-3 | -2.43 (rang 1) | -2.38 (rang 5) | -1.89 (rang 19) |
| C | SPI-12 | -2.98 (rang 1) | -2.75 (rang 2) | -2.57 (rang 5) |
