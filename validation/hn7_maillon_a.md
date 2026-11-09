# H-N7, maillon A : océan avant la saison → pluies extrêmes du Grand Sud

Généré le 2026-11-09 par `scripts/hn7_maillon_a.py`, selon `validation/protocole_climat_extremes_nappes.md` (test principal fixé le 09/11/2026 avant tout calcul, après `puissance_hn7.md`). Pluie : CHIRPS v2.0 par région ; ONI : NOAA CPC ; DMI, SIOD et canal de Mozambique : ERSST v5.

## Test principal

ONI de juillet-septembre contre pluie du mois le plus fort de la saison, Atsimo-Andrefana, 45 saisons complètes : **ρ = -0.24, p = 0.113** (bilatéral, permutation). **Lien non retenu** (seuil 5 %). Statut : exploratoire de justesse (puissance 47 % pour ρ = 0,3).

Descriptif : MSSS en validation croisée -0.00 ; MSSS chronologique (apprentissage jusqu'en 2005) +0.05 (positif = meilleur que la moyenne historique).

## Exploratoire (Benjamini-Hochberg 10 % par type de résultat)

| Région | Indice | Résultat | ρ | p | Retenu après correction |
|---|---|---|---|---|---|
| Atsimo-Andrefana | ONI | pluie maximale | -0.24 | 0.105 | non |
| Atsimo-Andrefana | ONI | au moins un mois extrême | -0.03 | 0.855 | non |
| Atsimo-Andrefana | DMI | pluie maximale | -0.23 | 0.116 | non |
| Atsimo-Andrefana | DMI | au moins un mois extrême | -0.13 | 0.393 | non |
| Atsimo-Andrefana | SIOD | pluie maximale | +0.00 | 0.997 | non |
| Atsimo-Andrefana | SIOD | au moins un mois extrême | +0.17 | 0.279 | non |
| Atsimo-Andrefana | canal de Mozambique | pluie maximale | -0.06 | 0.722 | non |
| Atsimo-Andrefana | canal de Mozambique | au moins un mois extrême | -0.13 | 0.425 | non |
| Androy | ONI | pluie maximale | -0.21 | 0.166 | non |
| Androy | ONI | au moins un mois extrême | -0.03 | 0.839 | non |
| Androy | DMI | pluie maximale | -0.29 | 0.053 | non |
| Androy | DMI | au moins un mois extrême | -0.12 | 0.439 | non |
| Androy | SIOD | pluie maximale | +0.08 | 0.611 | non |
| Androy | SIOD | au moins un mois extrême | +0.11 | 0.502 | non |
| Androy | canal de Mozambique | pluie maximale | +0.09 | 0.549 | non |
| Androy | canal de Mozambique | au moins un mois extrême | -0.03 | 0.876 | non |
| Anosy | ONI | pluie maximale | -0.12 | 0.442 | non |
| Anosy | ONI | au moins un mois extrême | -0.23 | 0.131 | non |
| Anosy | DMI | pluie maximale | -0.26 | 0.082 | non |
| Anosy | DMI | au moins un mois extrême | -0.26 | 0.082 | non |
| Anosy | SIOD | pluie maximale | +0.01 | 0.974 | non |
| Anosy | SIOD | au moins un mois extrême | -0.04 | 0.801 | non |
| Anosy | canal de Mozambique | pluie maximale | -0.06 | 0.685 | non |
| Anosy | canal de Mozambique | au moins un mois extrême | -0.05 | 0.753 | non |

Seuils du 95e centile mensuel (mm/mois) : Atsimo-Andrefana 273 ; Androy 181 ; Anosy 301.

Limites : 45 saisons au plus ; CHIRPS sous-estime souvent les extrêmes ; ce maillon ne dit rien des nappes (maillon B).

