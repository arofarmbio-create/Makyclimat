# Phase 0 : audit des forages et référence S0 (module eaux souterraines)

Généré le 2026-11-03 par `scripts/audit_nappes_phase0.py`, selon `validation/protocole_cadre_eaux_souterraines.md` (section 3, critères fixés avant le calcul). Forages : MGMERL ; carte mondiale : Fan et al. (2017), valeurs non republiées. Analyse exploratoire (forages déjà utilisés en H-C1 à H-C2b).

## 1. Diagramme de flux des données

**1000** : Relevés lus (tableau MGMERL du 02/11/2026)

↓ **1000** : Après contrôle (0-200 m, à Madagascar, doublons)

↓ **999** : Avec une valeur de la carte de Fan

↓ **999** : Situés dans un fokontany (région connue)

↓ **980** : Dans une région d'au moins 10 forages (validation par région)

## 2. Densité des forages par région

| Région | Forages | Part | Forages pour 1 000 km² |
|---|---|---|---|
| Androy | 346 | 34.6% | 18.25 |
| Atsimo Andrefana | 296 | 29.6% | 4.44 |
| Anosy | 168 | 16.8% | 5.69 |
| Atsimo Atsinanana | 55 | 5.5% | 3.31 |
| Sava | 50 | 5.0% | 2.10 |
| Analanjirofo | 25 | 2.5% | 2.45 |
| Boeny | 24 | 2.4% | 0.77 |
| Menabe | 16 | 1.6% | 0.33 |
| Ambatosoa | 7 | 0.7% | 0.61 |
| Fitovinany | 6 | 0.6% | 0.80 |
| Analamanga | 3 | 0.3% | 0.17 |
| Vatovavy | 2 | 0.2% | 0.15 |
| Amoron I Mania | 1 | 0.1% | 0.06 |

## 3. Dates et saisons des relevés

Relevés datés de 06/2023 à 09/2026. Par année : 2023 : 236, 2024 : 95, 2025 : 601, 2026 : 68. Saison des pluies (novembre à avril) : 368 ; saison sèche : 632.

## 4. Référence S0 (validation par région entière)

| Méthode | Critère 1 : erreur moyennée par région (m) [IC 95 %] | Critère 2 : erreur à plus de 50 km (m) [IC 95 %] | Biais moyen (m) |
|---|---|---|---|
| Carte de Fan seule | 9.14 [4.13 ; 14.75] | 8.02 [3.80 ; 14.26] | +15.73 |
| Krigeage | 4.09 [3.15 ; 5.36] | 3.52 [3.23 ; 3.94] | -0.28 |
| Hybride (forêt de quantiles) | 3.39 [1.93 ; 5.64] | 3.17 [1.79 ; 4.27] | -1.20 |

Avec 8 régions, les intervalles de confiance sont larges : ils mesurent ce que la phase 0 permet de conclure.

## 5. Couverture de l'intervalle de 80 % de l'hybride

| Région | Forages | Couverture |
|---|---|---|
| Analanjirofo | 25 | 76% |
| Androy | 346 | 88% |
| Anosy | 168 | 75% |
| Atsimo Andrefana | 296 | 64% |
| Atsimo Atsinanana | 55 | 78% |
| Boeny | 24 | 75% |
| Menabe | 16 | 50% |
| Sava | 50 | 88% |

| Distance au forage d'apprentissage le plus proche | Forages | Couverture | Erreur Fan (m) | Erreur krigeage (m) | Erreur hybride (m) |
|---|---|---|---|---|---|
| 0-25 km | 248 | 84% | 21.9 | 2.9 | 2.4 |
| 25-50 km | 288 | 80% | 20.6 | 3.1 | 2.8 |
| 50-100 km | 248 | 75% | 10.2 | 3.5 | 3.4 |
| plus de 100 km | 196 | 65% | 6.7 | 3.5 | 2.9 |
