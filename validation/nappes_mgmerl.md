# Niveaux de nappe MGMERL contre indices du système (protocole M3)

Généré le 2026-11-02 par `scripts/validate_nappes_mgmerl.py`, selon `validation/protocole_nappes_mgmerl.md` (fixé avant les calculs). Données de niveaux de nappe : MGMERL (HT Analytics, UNICEF).

Séries brutes : `data/mdg/mgmerl_raw/ht_analytics_csv_2025-06` (hors git). Indices : `data/mdg/nappes_sites_indices.csv`.

## Hypothèses fixées à l'avance

| Hypothèse | Sites favorables | Sites testés | p (test du signe unilatéral) | Conclusion |
|---|---|---|---|---|
| H-N1 : r(SPI-12) > 0 | 5 | 7 | 0.23 | non soutenue |
| H-N2 : r(recharge12_z) > r(SPI-12) | 1 | 5 | 0.97 | non soutenue |
| H-N3a : r(SPEI-12, ET0 de référence) > r(SPI-12) | 3 | 7 | 0.77 | non soutenue |
| H-N3b : r(bilan P - ETR réelle) > r(SPI-12) | 2 | 7 | 0.94 | non soutenue |

## Par site

| Site | Mois valides | Retenu | r(SPI-12) | r(recharge12_z) | n* | r(n*) | r(CE, niveau) | Décalage sécheresse 2019-2022 (mois) |
|---|---|---|---|---|---|---|---|---|
| Ampasimalemy | 14 | non | — | — | — | — | — | — |
| Andaboly | 28 | oui | -0.24 | — | 24.00 | 0.79 | 0.34 | 13.00 |
| Ankaramena | 29 | oui | 0.69 | 0.10 | 9.00 | 0.74 | 0.60 | 0.00 |
| Ankaranabo | 39 | oui | 0.44 | 0.15 | 10.00 | 0.55 | 0.29 | 0.00 |
| Behavandra | 20 | non | — | — | — | — | — | — |
| Belamoty | 0 | non | — | — | — | — | — | — |
| Betioky_F2 | 11 | non | — | — | — | — | — | — |
| Ihazoambo | 27 | oui | 0.36 | -0.01 | 18.00 | 0.83 | 0.59 | 11.00 |
| Karimbary | 1 | non | — | — | — | — | — | — |
| Mahafasa | 8 | non | — | — | — | — | — | — |
| Mahatsinjo | 2 | non | — | — | — | — | — | — |
| Mahavelo | 30 | oui | 0.24 | 0.06 | 13.00 | 0.36 | -0.38 | — |
| Manasoa | 0 | non | — | — | — | — | — | — |
| Marokibo | 3 | non | — | — | — | — | — | — |
| Nosiomby | 30 | oui | 0.54 | 0.70 | 11.00 | 0.67 | 0.70 | — |
| Sihanamaro | 53 | oui | -0.35 | — | 1.00 | -0.04 | -0.74 | 0.00 |

## Évaporation de référence et évaporation réelle (protocole doctoral E2-B)

Moyennes annuelles à la maille de chaque site, sur ses mois mesurés. ET0 : FAO-56 Penman-Monteith (ERA5-Land, climatologie 2016-2020). ETR : bilan de Thornthwaite-Mather, limitée par l'eau disponible dans le sol.

| Site | Pluie (mm/an) | ET0 (mm/an) | ETR (mm/an) | ETR/ET0 | Recharge (mm/an) | r(SPI-12) | r(SPEI-12) | r(P - ETR) |
|---|---|---|---|---|---|---|---|---|
| Andaboly | 509.00 | 1771.00 | 502.00 | 0.28 | 0.00 | -0.24 | -0.25 | -0.65 |
| Ankaramena | 875.00 | 1455.00 | 838.00 | 0.58 | 22.00 | 0.69 | 0.71 | 0.62 |
| Ankaranabo | 744.00 | 1623.00 | 724.00 | 0.45 | 0.00 | 0.44 | 0.44 | 0.46 |
| Ihazoambo | 1349.00 | 1304.00 | 1006.00 | 0.77 | 293.00 | 0.36 | 0.39 | -0.01 |
| Mahavelo | 2581.00 | 1251.00 | 1136.00 | 0.91 | 1417.00 | 0.24 | 0.21 | 0.13 |
| Nosiomby | 2322.00 | 1254.00 | 1079.00 | 0.86 | 1226.00 | 0.54 | 0.54 | 0.69 |
| Sihanamaro | 476.00 | 1639.00 | 476.00 | 0.29 | 0.00 | -0.35 | -0.34 | -0.53 |

## Contrôle qualité (règles de la section 4)

| Site | Mesures | Hors bornes | Pics | Coupures | Hors segment gardé | Conductivité rejetée |
|---|---|---|---|---|---|---|
| Ampasimalemy | 3124 | 0 | 1 | 1 | 700 | 701 |
| Andaboly | 5280 | 25 | 1 | 1 | 2035 | 1040 |
| Ankaramena | 5760 | 0 | 358 | 3 | 617 | 1338 |
| Ankaranabo | 5249 | 1 | 383 | 0 | 0 | 0 |
| Behavandra | 4499 | 1 | 1481 | 3 | 1341 | 4 |
| Belamoty | 187 | 0 | 0 | 0 | 0 | 187 |
| Betioky_F2 | 6838 | 0 | 2107 | 23 | 3378 | 29 |
| Ihazoambo | 3020 | 0 | 0 | 0 | 0 | 0 |
| Karimbary | 340 | 36 | 20 | 1 | 32 | 288 |
| Mahafasa | 1478 | 0 | 24 | 0 | 0 | 24 |
| Mahatsinjo | 190 | 3 | 4 | 0 | 0 | 2 |
| Mahavelo | 5897 | 4 | 19 | 1 | 576 | 580 |
| Manasoa | 55 | 2 | 2 | 0 | 0 | 4 |
| Marokibo | 366 | 0 | 26 | 0 | 0 | 20 |
| Nosiomby | 5299 | 4 | 27 | 0 | 0 | 31 |
| Sihanamaro | 7715 | 1 | 1 | 0 | 0 | 0 |

n* : durée de cumul du SPI la mieux corrélée (descriptif, jamais une performance). Corrélations de Spearman sur les anomalies mensuelles de niveau (cycle saisonnier retiré).
