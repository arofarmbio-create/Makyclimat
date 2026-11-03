# Les données SEAM du ministère de l'Eau sont-elles utiles à MakyClimat ?

Généré le 2026-11-03 par `scripts/etude_seam.py`, selon `validation/protocole_seam_points_eau.md` (fixé avant le calcul). Source : MEAH / SEAM, lecture publique. Analyse exploratoire.

## Q1. Qualité des positions (forages et puits)

32630 ouvrages ; positions valides 100.0% ; coordonnées partagées par plusieurs ouvrages 45.8% ; coordonnées arrondies au millième de degré 1.3%. Critère (plus de 90 % valides) : **atteint**.

## Q2. Représentativité des 1 000 relevés MGMERL parmi les forages du pays

Forages SEAM (forages et FPMH) : 15384.

| Variable | Moyenne MGMERL | Moyenne SEAM | DMS | Forages SEAM hors étendue (P1-P99) |
|---|---|---|---|---|
| altitude_m | 307.4 | 274.4 | -0.13 | 12.9% |
| hand | 37.4 | 28.3 | -0.20 | 1.0% |
| pente | 0.9 | 1.0 | +0.04 | 2.1% |
| pluie_mm | 961.9 | 1299.8 | +0.46 | 8.9% |
| socle_m | 42.5 | 43.9 | +0.09 | 2.2% |

Forages SEAM hors de l'étendue des relevés pour au moins une variable : **24.0%** (la carte y extrapole). Une DMS au-delà de 0,25 en valeur absolue signale un déséquilibre. Classes lithologiques GLiM : distance de variation totale entre les deux répartitions 0.18 (0 : identiques, 1 : disjointes).

## Q3. La part de puits autour d'un forage signale-t-elle une nappe peu profonde ?

45.8% des forages et puits partagent leurs coordonnées exactes avec d'autres (positions par défaut). H-S1 (protocole initial) utilise toutes les positions ; H-S1b (modification datée du 03/11/2026, après le premier calcul) les seules positions uniques.

### H-S1 (toutes positions)

Rayon 5 km (ouvrages à moins de 200 m exclus, au moins 5 ouvrages) : ρ de Spearman = -0.04 (p = 0.2, 879 forages) ; ρ négatif dans 2 régions sur 7. **Non soutenue**.

| Région | ρ |
|---|---|
| Analanjirofo | -0.29 |
| Androy | +0.07 |
| Anosy | -0.14 |
| Atsimo Andrefana | +0.04 |
| Atsimo Atsinanana | +0.17 |
| Boeny | +0.09 |
| Sava | +0.12 |

Sensibilité au rayon : 2 km : ρ = -0.07 (n = 581) ; 5 km : ρ = -0.04 (n = 879) ; 10 km : ρ = -0.05 (n = 974).

Test d'apport à l'hybride non fait : hypothèse non soutenue (règle du protocole).

### H-S1b (positions uniques)

Rayon 5 km (ouvrages à moins de 200 m exclus, au moins 5 ouvrages) : ρ de Spearman = -0.11 (p = 0.001, 845 forages) ; ρ négatif dans 6 régions sur 7. **Soutenue**.

| Région | ρ |
|---|---|
| Analanjirofo | -0.27 |
| Androy | -0.01 |
| Anosy | -0.14 |
| Atsimo Andrefana | -0.12 |
| Atsimo Atsinanana | +0.20 |
| Boeny | -0.04 |
| Sava | -0.01 |

Sensibilité au rayon : 2 km : ρ = -0.15 (n = 493) ; 5 km : ρ = -0.11 (n = 845) ; 10 km : ρ = -0.12 (n = 948).

Apport à l'hybride S0 (critères de la phase 0) :

| Critère | S0 (m) | S0 + part de puits (m) | Écart [IC 95 %] |
|---|---|---|---|
| 1 : erreur moyennée par région | 3.39 | 3.38 | -0.01 [-0.08 ; +0.06] |
| 2 : erreur à plus de 50 km | 3.17 | 3.15 | -0.03 [-0.14 ; +0.20] |

Décision : variable **gardée** (amélioration non démontrée).

## Q4. Pression sur la ressource par commune

1721 communes ; population non nulle dans 99.1% ; total 29.9 millions (écart à la projection nationale -1.3%) ; médiane 1884 habitants par ouvrage d'eau souterraine fonctionnel. Critère (plus de 80 % non nulles, écart sous 15 %) : **atteint**.

## Q5. Pannes de forages par district (exploratoire)

Corrélation de Spearman, par district (au moins 20 forages), entre la part de forages en panne ou abandonnés et la profondeur médiane mesurée des relevés MGMERL du district : ρ = +0.37 sur 31 districts.

