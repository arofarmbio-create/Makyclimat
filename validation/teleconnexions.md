# Modèle de prévision saisonnière El Niño / dipôle de l'océan Indien, par région

Généré le 2026-10-28 par `scripts/build_teleconnections.py`. Cahier des charges §5, §8 (approche 1), §9, §13.
Saisons 1981-1982 à 2025-2026 (45 saisons). Pluie CHIRPS par région.
Prédicteurs connus avant la saison : ONI de juillet-septembre (NOAA CPC) et DMI de juillet-septembre (NOAA PSL, HadISST).

Une région est dite **prévisible** seulement si les trois conditions suivantes sont réunies :
- score de compétence en validation croisée (MSSS, saison laissée de côté) > 0 ;
- score de compétence au test chronologique (ajusté jusqu'en 2005, testé après) > 0 ;
- corrélation POSITIVE et significative entre prévision croisée et observation (permutation unilatérale, modèle réajusté à chaque tirage), après contrôle des tests multiples (Benjamini-Hochberg, 10 %).

Sinon, la meilleure prévision est la climatologie.

## Combien de régions sont prévisibles ?

| Cible | Modèle | Régions prévisibles | MSSS médian (LOO) |
|---|---|---|---|
| novembre-janvier | ONI seul | 1 / 24 | -0,00 |
| novembre-janvier | ONI + DMI | 0 / 24 | -0,04 |
| janvier-mars | ONI seul | 0 / 24 | -0,01 |
| janvier-mars | ONI + DMI | 0 / 24 | -0,05 |
| novembre-avril | ONI seul | 0 / 24 | -0,01 |
| novembre-avril | ONI + DMI | 0 / 24 | -0,05 |

## Détail par région (novembre-avril)

| Région | Modèle | r (LOO) | MSSS LOO | MSSS chrono | p permutation | Coef. ONI | Coef. DMI | Prévisible |
|---|---|---|---|---|---|---|---|---|
| Alaotra Mangoro | ONI | -0,21 | -0,02 | 0,01 | 0,415 | 0,16 | — | non |
| Alaotra Mangoro | ONI+DMI | -0,36 | -0,07 | 0,01 | 0,743 | 0,18 | -0,09 | non |
| Ambatosoa | ONI | -0,06 | -0,01 | 0,03 | 0,234 | 0,25 | — | non |
| Ambatosoa | ONI+DMI | -0,16 | -0,05 | 0,03 | 0,491 | 0,25 | 0,00 | non |
| Amoron I Mania | ONI | 0,05 | 0,02 | 0,03 | 0,126 | -0,32 | — | non |
| Amoron I Mania | ONI+DMI | -0,06 | -0,04 | 0,02 | 0,329 | -0,25 | -0,24 | non |
| Analamanga | ONI | -0,14 | -0,02 | 0,02 | 0,341 | 0,20 | — | non |
| Analamanga | ONI+DMI | -0,28 | -0,07 | 0,02 | 0,623 | 0,19 | 0,06 | non |
| Analanjirofo | ONI | -0,14 | -0,03 | 0,02 | 0,301 | 0,20 | — | non |
| Analanjirofo | ONI+DMI | -0,11 | -0,05 | 0,06 | 0,409 | 0,32 | -0,42 | non |
| Androy | ONI | 0,25 | 0,09 | 0,04 | 0,018 | -0,52 | — | non |
| Androy | ONI+DMI | 0,24 | 0,07 | 0,02 | 0,034 | -0,39 | -0,49 | non |
| Anosy | ONI | 0,16 | 0,04 | 0,01 | 0,054 | -0,44 | — | non |
| Anosy | ONI+DMI | 0,11 | 0,01 | -0,21 | 0,136 | -0,36 | -0,32 | non |
| Atsimo Andrefana | ONI | 0,30 | 0,12 | -0,14 | 0,012 | -0,57 | — | non |
| Atsimo Andrefana | ONI+DMI | 0,30 | 0,11 | -0,06 | 0,020 | -0,42 | -0,58 | non |
| Atsimo Atsinanana | ONI | -0,05 | -0,03 | 0,06 | 0,234 | -0,32 | — | non |
| Atsimo Atsinanana | ONI+DMI | -0,13 | -0,08 | -0,09 | 0,429 | -0,34 | 0,09 | non |
| Atsinanana | ONI | -0,84 | -0,03 | -0,04 | 0,980 | -0,00 | — | non |
| Atsinanana | ONI+DMI | -0,79 | -0,08 | -0,04 | 0,970 | 0,03 | -0,13 | non |
| Betsiboka | ONI | -0,59 | -0,04 | -0,02 | 0,750 | 0,05 | — | non |
| Betsiboka | ONI+DMI | -0,67 | -0,08 | -0,02 | 0,924 | 0,08 | -0,12 | non |
| Boeny | ONI | -0,11 | -0,02 | 0,00 | 0,313 | -0,23 | — | non |
| Boeny | ONI+DMI | -0,24 | -0,06 | -0,03 | 0,577 | -0,20 | -0,11 | non |
| Bongolava | ONI | -0,71 | -0,05 | -0,01 | 0,870 | 0,03 | — | non |
| Bongolava | ONI+DMI | -0,66 | -0,10 | 0,00 | 0,928 | 0,08 | -0,19 | non |
| Diana | ONI | 0,15 | 0,04 | 0,07 | 0,056 | 0,40 | — | non |
| Diana | ONI+DMI | 0,12 | 0,02 | 0,07 | 0,122 | 0,30 | 0,37 | non |
| Fitovinany | ONI | 0,04 | 0,00 | 0,06 | 0,120 | -0,35 | — | non |
| Fitovinany | ONI+DMI | -0,00 | -0,03 | 0,06 | 0,240 | -0,45 | 0,34 | non |
| Haute Matsiatra | ONI | 0,13 | 0,04 | 0,02 | 0,048 | -0,41 | — | non |
| Haute Matsiatra | ONI+DMI | 0,07 | -0,01 | 0,01 | 0,156 | -0,33 | -0,29 | non |
| Ihorombe | ONI | 0,25 | 0,09 | 0,01 | 0,006 | -0,54 | — | non |
| Ihorombe | ONI+DMI | 0,21 | 0,05 | -0,03 | 0,054 | -0,46 | -0,28 | non |
| Itasy | ONI | -0,41 | -0,03 | -0,03 | 0,613 | 0,10 | — | non |
| Itasy | ONI+DMI | -0,59 | -0,09 | -0,04 | 0,896 | 0,12 | -0,06 | non |
| Melaky | ONI | -0,17 | -0,03 | 0,01 | 0,373 | -0,19 | — | non |
| Melaky | ONI+DMI | -0,14 | -0,06 | 0,01 | 0,441 | -0,06 | -0,45 | non |
| Menabe | ONI | 0,13 | 0,04 | -0,06 | 0,062 | -0,38 | — | non |
| Menabe | ONI+DMI | 0,19 | 0,05 | 0,07 | 0,060 | -0,18 | -0,75 | non |
| Sava | ONI | 0,23 | 0,08 | 0,12 | 0,016 | 0,49 | — | non |
| Sava | ONI+DMI | 0,21 | 0,06 | 0,12 | 0,066 | 0,40 | 0,35 | non |
| Sofia | ONI | -0,67 | -0,04 | -0,01 | 0,838 | 0,04 | — | non |
| Sofia | ONI+DMI | -0,80 | -0,08 | -0,02 | 0,976 | 0,05 | -0,03 | non |
| Vakinankaratra | ONI | -0,43 | -0,03 | 0,00 | 0,611 | -0,09 | — | non |
| Vakinankaratra | ONI+DMI | -0,56 | -0,08 | -0,00 | 0,872 | -0,05 | -0,16 | non |
| Vatovavy | ONI | 0,01 | 0,01 | 0,05 | 0,170 | -0,29 | — | non |
| Vatovavy | ONI+DMI | -0,08 | -0,04 | 0,04 | 0,337 | -0,37 | 0,28 | non |

## Prévision 2026-2027

ONI de juillet-septembre 2026 : **2,16**. DMI de juillet-septembre 2026 : **indisponible** (la série HadISST de NOAA PSL a plusieurs mois de retard) : seul le modèle ONI est appliqué.

| Région | Période | Modèle | Anomalie (écart-type) | % de la normale |
|---|---|---|---|---|
| Menabe | novembre-janvier | ONI | -1,02 | 77 % |

## Limites

- Le modèle est linéaire : un El Niño très fort (ONI > 2, très rare dans l'échantillon) est extrapolé, et son effet réel peut différer.
- La pluie est estimée par CHIRPS, sans stations au sol. La moyenne régionale lisse les contrastes internes (relief, façade est et ouest).
- Aucune autre source de prévisibilité n'est prise en compte : autres modes de l'océan Indien (SIOD), cyclones, MJO.
- Les seuils de décision (MSSS > 0, FDR 10 %) sont des conventions, à discuter avec Météo Madagascar.
- Cette prévision complète celle des modèles dynamiques (ECMWF SEAS5, Météo Madagascar, SARCOF). Elle ne la remplace pas.
