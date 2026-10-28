# Modèle de prévision saisonnière El Niño / dipôle de l'océan Indien, par région

Généré le 2026-10-28 par `scripts/build_teleconnections.py`. Cahier des charges §5, §8 (approche 1), §9, §13.
Saisons 1981-1982 à 2025-2026 (45 saisons). Pluie CHIRPS par région.
Prédicteurs connus avant la saison : ONI de juillet-septembre (NOAA CPC) et DMI de juillet-septembre (ERSST v5, `connector_dmi.py`).

Une région est dite **prévisible** seulement si les trois conditions suivantes sont réunies :
- score de compétence en validation croisée (MSSS, saison laissée de côté) > 0 ;
- score de compétence au test chronologique (ajusté jusqu'en 2005, testé après) > 0 ;
- corrélation POSITIVE et significative entre prévision croisée et observation (permutation unilatérale, modèle réajusté à chaque tirage), après contrôle des tests multiples (Benjamini-Hochberg, 10 %).

Sinon, la meilleure prévision est la climatologie.

## Combien de régions sont prévisibles ?

| Cible | Modèle | Régions prévisibles | MSSS médian (LOO) |
|---|---|---|---|
| novembre-janvier | ONI seul | 1 / 24 | -0,00 |
| novembre-janvier | ONI + DMI | 2 / 24 | -0,02 |
| janvier-mars | ONI seul | 0 / 24 | -0,01 |
| janvier-mars | ONI + DMI | 0 / 24 | -0,05 |
| novembre-avril | ONI seul | 0 / 24 | -0,01 |
| novembre-avril | ONI + DMI | 0 / 24 | -0,04 |

## Détail par région (novembre-avril)

| Région | Modèle | r (LOO) | MSSS LOO | MSSS chrono | p permutation | Coef. ONI | Coef. DMI | Prévisible |
|---|---|---|---|---|---|---|---|---|
| Alaotra Mangoro | ONI | -0,21 | -0,02 | 0,01 | 0,415 | 0,16 | — | non |
| Alaotra Mangoro | ONI+DMI | -0,25 | -0,06 | 0,01 | 0,577 | 0,07 | 0,23 | non |
| Ambatosoa | ONI | -0,06 | -0,01 | 0,03 | 0,234 | 0,25 | — | non |
| Ambatosoa | ONI+DMI | -0,02 | -0,03 | 0,06 | 0,291 | 0,11 | 0,39 | non |
| Amoron I Mania | ONI | 0,05 | 0,02 | 0,03 | 0,126 | -0,32 | — | non |
| Amoron I Mania | ONI+DMI | -0,04 | -0,03 | 0,03 | 0,311 | -0,28 | -0,10 | non |
| Analamanga | ONI | -0,14 | -0,02 | 0,02 | 0,341 | 0,20 | — | non |
| Analamanga | ONI+DMI | -0,19 | -0,07 | -0,02 | 0,521 | 0,11 | 0,25 | non |
| Analanjirofo | ONI | -0,14 | -0,03 | 0,02 | 0,301 | 0,20 | — | non |
| Analanjirofo | ONI+DMI | -0,24 | -0,07 | 0,01 | 0,591 | 0,16 | 0,13 | non |
| Androy | ONI | 0,25 | 0,09 | 0,04 | 0,018 | -0,52 | — | non |
| Androy | ONI+DMI | 0,28 | 0,10 | -0,04 | 0,030 | -0,35 | -0,47 | non |
| Anosy | ONI | 0,16 | 0,04 | 0,01 | 0,054 | -0,44 | — | non |
| Anosy | ONI+DMI | 0,13 | 0,02 | -0,18 | 0,114 | -0,35 | -0,27 | non |
| Atsimo Andrefana | ONI | 0,30 | 0,12 | -0,14 | 0,012 | -0,57 | — | non |
| Atsimo Andrefana | ONI+DMI | 0,31 | 0,12 | -0,21 | 0,014 | -0,42 | -0,43 | non |
| Atsimo Atsinanana | ONI | -0,05 | -0,03 | 0,06 | 0,234 | -0,32 | — | non |
| Atsimo Atsinanana | ONI+DMI | -0,13 | -0,07 | -0,04 | 0,433 | -0,33 | 0,02 | non |
| Atsinanana | ONI | -0,84 | -0,03 | -0,04 | 0,980 | -0,00 | — | non |
| Atsinanana | ONI+DMI | -0,37 | -0,06 | -0,02 | 0,725 | -0,09 | 0,24 | non |
| Betsiboka | ONI | -0,59 | -0,04 | -0,02 | 0,750 | 0,05 | — | non |
| Betsiboka | ONI+DMI | -0,64 | -0,09 | -0,07 | 0,942 | 0,01 | 0,11 | non |
| Boeny | ONI | -0,11 | -0,02 | 0,00 | 0,313 | -0,23 | — | non |
| Boeny | ONI+DMI | -0,19 | -0,06 | -0,04 | 0,515 | -0,29 | 0,16 | non |
| Bongolava | ONI | -0,71 | -0,05 | -0,01 | 0,870 | 0,03 | — | non |
| Bongolava | ONI+DMI | -0,79 | -0,11 | -0,07 | 0,986 | 0,05 | -0,05 | non |
| Diana | ONI | 0,15 | 0,04 | 0,07 | 0,056 | 0,40 | — | non |
| Diana | ONI+DMI | 0,23 | 0,07 | 0,15 | 0,042 | 0,19 | 0,59 | non |
| Fitovinany | ONI | 0,04 | 0,00 | 0,06 | 0,120 | -0,35 | — | non |
| Fitovinany | ONI+DMI | 0,04 | -0,02 | 0,08 | 0,208 | -0,47 | 0,33 | non |
| Haute Matsiatra | ONI | 0,13 | 0,04 | 0,02 | 0,048 | -0,41 | — | non |
| Haute Matsiatra | ONI+DMI | 0,06 | -0,01 | 0,01 | 0,176 | -0,38 | -0,09 | non |
| Ihorombe | ONI | 0,25 | 0,09 | 0,01 | 0,006 | -0,54 | — | non |
| Ihorombe | ONI+DMI | 0,20 | 0,05 | -0,03 | 0,062 | -0,50 | -0,12 | non |
| Itasy | ONI | -0,41 | -0,03 | -0,03 | 0,613 | 0,10 | — | non |
| Itasy | ONI+DMI | -0,58 | -0,09 | -0,07 | 0,904 | 0,09 | 0,04 | non |
| Melaky | ONI | -0,17 | -0,03 | 0,01 | 0,373 | -0,19 | — | non |
| Melaky | ONI+DMI | -0,29 | -0,07 | -0,04 | 0,653 | -0,17 | -0,06 | non |
| Menabe | ONI | 0,13 | 0,04 | -0,06 | 0,062 | -0,38 | — | non |
| Menabe | ONI+DMI | 0,16 | 0,04 | 0,00 | 0,072 | -0,21 | -0,48 | non |
| Sava | ONI | 0,23 | 0,08 | 0,12 | 0,016 | 0,49 | — | non |
| Sava | ONI+DMI | 0,31 | 0,12 | 0,20 | 0,024 | 0,28 | 0,60 | non |
| Sofia | ONI | -0,67 | -0,04 | -0,01 | 0,838 | 0,04 | — | non |
| Sofia | ONI+DMI | -0,52 | -0,08 | 0,00 | 0,834 | -0,03 | 0,19 | non |
| Vakinankaratra | ONI | -0,43 | -0,03 | 0,00 | 0,611 | -0,09 | — | non |
| Vakinankaratra | ONI+DMI | -0,58 | -0,08 | 0,01 | 0,900 | -0,06 | -0,08 | non |
| Vatovavy | ONI | 0,01 | 0,01 | 0,05 | 0,170 | -0,29 | — | non |
| Vatovavy | ONI+DMI | 0,00 | -0,02 | 0,07 | 0,228 | -0,40 | 0,29 | non |

## Prévision 2026-2027

ONI de juillet-septembre 2026 : **2,16**. DMI de juillet-septembre 2026 : **0,23**.

| Région | Période | Modèle | Anomalie (écart-type) | % de la normale |
|---|---|---|---|---|
| Diana | novembre-janvier | ONI+DMI | 0,03 | 101 % |
| Menabe | novembre-janvier | ONI | -1,02 | 77 % |
| Sava | novembre-janvier | ONI+DMI | 0,35 | 110 % |

## Limites

- Le modèle est linéaire : un El Niño très fort (ONI > 2, très rare dans l'échantillon) est extrapolé, et son effet réel peut différer.
- La pluie est estimée par CHIRPS, sans stations au sol. La moyenne régionale lisse les contrastes internes (relief, façade est et ouest).
- Aucune autre source de prévisibilité n'est prise en compte : autres modes de l'océan Indien (SIOD), cyclones, MJO.
- Les seuils de décision (MSSS > 0, FDR 10 %) sont des conventions, à discuter avec Météo Madagascar.
- Cette prévision complète celle des modèles dynamiques (ECMWF SEAS5, Météo Madagascar, SARCOF). Elle ne la remplace pas.
