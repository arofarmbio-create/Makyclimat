# E1, section 6.3 : les versions de la pluie face aux impacts

Généré le 2026-11-03 par `scripts/validate_e1_impacts.py`, selon `validation/protocole_e1_fusion_pluie.md` (précisions du 03/11/2026, fixées avant ce calcul). Descriptif : peu d'événements, aucun test de signification.

## Inondations pluviales du périmètre pilote (pluie sur 3 jours, seuils locaux de 2001-2015, saisons 2016-2017 à 2024-2025)

| Version | Événements détectés | Épisodes | Épisodes sans correspondance | AUC des communes EMS |
|---|---|---|---|---|
| chirps | 3 / 4 | 9 | 4 | 0.18;0.58;0.81 |
| imerg | 3 / 4 | 12 | 6 | 0.72;0.19;0.12 |
| era5 | 2 / 4 | 15 | 5 | 0.68;0.28;0.44 |
| B | 3 / 4 | 13 | 3 | 0.43;0.22;0.56 |
| C | 3 / 4 | 14 | 3 | 0.57;0.42;0.12 |

## Sécheresse du Grand Sud (2019-07 à 2023-06) : SPI minimum et rang parmi 24 régions (1 = la plus sèche)

| Version | Indice | Androy | Anosy | Atsimo Andrefana |
|---|---|---|---|---|
| chirps | SPI-3 | -2.31 (rang 4) | -2.35 (rang 3) | -2.40 (rang 2) |
| chirps | SPI-12 | -2.64 (rang 1) | -2.54 (rang 3) | -2.19 (rang 7) |
| imerg | SPI-3 | -2.37 (rang 10) | -2.29 (rang 14) | -2.10 (rang 20) |
| imerg | SPI-12 | -2.92 (rang 3) | -2.76 (rang 7) | -2.60 (rang 11) |
| era5 | SPI-3 | -2.48 (rang 6) | -2.44 (rang 9) | -2.47 (rang 7) |
| era5 | SPI-12 | -2.95 (rang 1) | -2.84 (rang 3) | -2.74 (rang 4) |
| B | SPI-3 | -2.53 (rang 2) | -2.40 (rang 6) | -2.11 (rang 15) |
| B | SPI-12 | -2.89 (rang 1) | -2.75 (rang 3) | -2.58 (rang 6) |
| C | SPI-3 | -2.42 (rang 6) | -2.35 (rang 9) | -1.89 (rang 19) |
| C | SPI-12 | -2.97 (rang 1) | -2.73 (rang 2) | -2.57 (rang 5) |
