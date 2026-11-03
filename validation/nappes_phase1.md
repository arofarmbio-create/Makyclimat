# Phase 1 : conditions de mesure (module eaux souterraines)

Généré le 2026-11-03 par `scripts/nappes_phase1.py`, selon `validation/protocole_cadre_eaux_souterraines.md` (section 3, précisions du 03/11/2026 fixées avant le calcul). 980 forages MGMERL, validation par région entière (mêmes régions que la phase 0) ; 962 avec un SPI (grilles CHIRPS 2022-10 à 2026-09). Analyse exploratoire.

Variables ajoutées à l'hybride S0 : saison du relevé, SPI-3 et SPI-12 du mois du relevé à la maille du forage.

| Critère | S0 (m) [IC 95 %] | S1 = S0 + conditions de mesure (m) [IC 95 %] | Écart S1 − S0 [IC 95 %] |
|---|---|---|---|
| 1 : erreur moyennée par région | 3.39 [1.93 ; 5.64] | 3.53 [2.10 ; 5.73] | +0.14 [-0.00 ; +0.29] |
| 2 : erreur à plus de 50 km | 3.17 [1.79 ; 4.27] | 3.10 [1.89 ; 4.34] | -0.08 [-0.15 ; +0.32] |

Décision (règle fixée avant le calcul) : variables **rejetées** : au moins un critère principal ne s'améliore pas.

## Couverture de l'intervalle de 80 % par classe de distance

| Distance | Forages | Couverture S0 | Couverture S1 | Erreur S0 (m) | Erreur S1 (m) |
|---|---|---|---|---|---|
| 0-25 km | 248 | 84% | 85% | 2.4 | 2.3 |
| 25-50 km | 288 | 80% | 79% | 2.8 | 2.8 |
| 50-100 km | 248 | 75% | 73% | 3.4 | 3.5 |
| plus de 100 km | 196 | 65% | 65% | 2.9 | 2.8 |
