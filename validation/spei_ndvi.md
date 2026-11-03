# SPI ou SPEI pour suivre le stress de la végétation (NDVI MODIS), par district

Généré le 2026-11-03 par `scripts/validate_spei_ndvi.py`, selon `validation/protocole_spei_ndvi.md` (fixé avant les calculs).

- 120 districts (36 secs, 84 humides) ; indices calculés sur 1981-01 - 2026-09 ; NDVI 2001-2025, mois de décembre à mai.
- Pluie CHIRPS, ET0 Penman-Monteith FAO-56 depuis ERA5-Land (moyennes mensuelles), NDVI MOD13C2 (pixels fiables).

## 1. Hypothèses fixées à l'avance (test du signe unilatéral entre districts)

| Districts | Combinaison | SPEI meilleur que SPI | p | r médian SPI | r médian SPEI |
|---|---|---|---|---|---|
| secs | principale (3 mois, décalage 1) | 31 / 36 | 0,000 | 0,50 | 0,52 |
| secs | meilleure de chaque indice | 22 / 36 | 0,121 | 0,56 | 0,59 |
| humides | principale (3 mois, décalage 1) | 51 / 84 | 0,031 | 0,34 | 0,35 |
| humides | meilleure de chaque indice | 55 / 84 | 0,003 | 0,37 | 0,37 |

- **H1** (gain du SPEI dans les districts secs) : **soutenue**.
- **H2** (pas de gain systématique dans les districts humides) : **non soutenue**.

## 2. Sécheresse du Grand Sud 2020-2022 (moyenne des districts d'Androy, Anosy, Atsimo-Andrefana ; juillet 2019 - juin 2023)

| Indice | Premier mois ≤ −1 | Mois ≤ −1 | Minimum |
|---|---|---|---|
| SPI-6 | 2020-02 | 14 | -1,81 |
| SPEI-6 | 2020-02 | 21 | -2,32 |

## 3. Contrôle de l'ET0 (moyenne nationale des districts, 2016-2020, mm/mois)

| Mois | ERA5-Land Penman-Monteith (ce travail) | Open-Meteo (site) |
|---|---|---|
| 1 | 126 | 136 |
| 2 | 114 | 125 |
| 3 | 112 | 127 |
| 4 | 99 | 119 |
| 5 | 84 | 112 |
| 6 | 71 | 97 |
| 7 | 78 | 107 |
| 8 | 97 | 127 |
| 9 | 116 | 144 |
| 10 | 137 | 164 |
| 11 | 137 | 157 |
| 12 | 140 | 153 |

Détail par district : `validation/spei_ndvi_districts.csv`.

## Limites

- ET0 à partir de moyennes mensuelles (pas de Tmax/Tmin journaliers) : légère sous-estimation possible du déficit de vapeur.
- Le NDVI réagit aussi aux feux, à l'irrigation et aux cyclones ; il sature en forêt dense (est humide).
- Autocorrélation des séries : seules les comparaisons entre districts (test du signe) servent à conclure.
