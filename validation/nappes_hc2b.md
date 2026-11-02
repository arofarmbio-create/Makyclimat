# H-C2b : prédire la profondeur de l'eau dans une région entière laissée de côté

Généré le 2026-11-02 par `scripts/validate_nappes_hc2b.py`, selon `validation/protocole_carte_nappes.md` (ajout du 02/11/2026, fixé avant le calcul ; conçu après H-C2, sur les mêmes forages : test complémentaire). Forages : MGMERL (999) ; carte mondiale : Fan et al. (2017), valeurs non republiées.

## Par région laissée de côté

| Région | Forages | Distance médiane au forage d'apprentissage le plus proche (km) | Erreur hybride (m) | Erreur krigeage (m) | Erreur Fan (m) |
|---|---|---|---|---|---|
| Analanjirofo | 25 | 91 | 1.8 | 5.0 | 2.4 |
| Androy | 346 | 26 | 2.2 | 2.7 | 21.7 |
| Anosy | 168 | 41 | 3.3 | 3.0 | 7.2 |
| Atsimo Andrefana | 296 | 71 | 3.6 | 3.7 | 23.9 |
| Atsimo Atsinanana | 55 | 86 | 1.7 | 3.4 | 4.0 |
| Boeny | 24 | 284 | 2.3 | 2.9 | 4.8 |
| Menabe | 16 | 103 | 10.8 | 8.1 | 6.4 |
| Sava | 50 | 270 | 1.4 | 3.9 | 2.7 |

## Par distance au forage d'apprentissage le plus proche

| Distance | Forages | Erreur hybride (m) | Erreur krigeage (m) | Erreur Fan (m) |
|---|---|---|---|---|
| 0-25 km | 248 | 2.4 | 2.9 | 21.9 |
| 25-50 km | 288 | 2.8 | 3.1 | 20.6 |
| 50-100 km | 248 | 3.4 | 3.5 | 10.2 |
| plus de 100 km | 196 | 2.9 | 3.5 | 6.7 |

Wilcoxon apparié (hybride < krigeage) : p = 0.161 ; l'hybride fait mieux dans 6 régions sur 8.

**H-C2b non confirmée.**

