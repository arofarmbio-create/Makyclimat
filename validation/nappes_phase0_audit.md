# Phase 0 : audit des forages et référence S0 (module eaux souterraines)

Généré le 2026-11-03 par `scripts/audit_nappes_phase0.py`, selon `validation/protocole_cadre_eaux_souterraines.md` (section 3, critères fixés avant le calcul). Forages : MGMERL ; carte mondiale : Fan et al. (2017), valeurs non republiées. Analyse exploratoire (forages déjà utilisés en H-C1 à H-C2b).

## 1. Diagramme de flux des données

**1400** : Relevés lus (tableau MGMERL complet, extrait le 03/11/2026)

↓ **1400** : Après contrôle (0-200 m, à Madagascar, doublons)

↓ **1399** : Avec une valeur de la carte de Fan

↓ **1399** : Situés dans un fokontany (région connue)

↓ **1385** : Dans une région d'au moins 10 forages (validation par région)

## 2. Densité des forages par région

| Région | Forages | Part | Forages pour 1 000 km² |
|---|---|---|---|
| Androy | 507 | 36.2% | 26.74 |
| Atsimo Andrefana | 460 | 32.9% | 6.90 |
| Anosy | 194 | 13.9% | 6.57 |
| Atsimo Atsinanana | 78 | 5.6% | 4.69 |
| Sava | 50 | 3.6% | 2.10 |
| Boeny | 45 | 3.2% | 1.44 |
| Analanjirofo | 25 | 1.8% | 2.45 |
| Menabe | 16 | 1.1% | 0.33 |
| Ambatosoa | 10 | 0.7% | 0.87 |
| Fitovinany | 6 | 0.4% | 0.80 |
| Vatovavy | 3 | 0.2% | 0.23 |
| Analamanga | 3 | 0.2% | 0.17 |
| Betsiboka | 1 | 0.1% | 0.03 |
| Amoron I Mania | 1 | 0.1% | 0.06 |

## 3. Dates et saisons des relevés

Relevés datés de 09/1994 à 09/2026. Par année : 1994 : 1, 2001 : 50, 2002 : 60, 2003 : 72, 2004 : 59, 2008 : 1, 2021 : 1, 2022 : 49, 2023 : 340, 2024 : 95, 2025 : 604, 2026 : 68. Saison des pluies (novembre à avril) : 533 ; saison sèche : 867.

## 4. Référence S0 (validation par région entière)

| Méthode | Critère 1 : erreur moyennée par région (m) [IC 95 %] | Critère 2 : erreur à plus de 50 km (m) [IC 95 %] | Biais moyen (m) |
|---|---|---|---|
| Carte de Fan seule | 8.56 [3.84 ; 14.37] | 8.05 [3.74 ; 14.33] | +17.60 |
| Krigeage | 4.06 [3.30 ; 5.18] | 3.49 [3.33 ; 3.88] | -0.03 |
| Hybride (forêt de quantiles) | 3.26 [1.98 ; 5.21] | 3.03 [1.73 ; 3.90] | -0.95 |

Avec 8 régions, les intervalles de confiance sont larges : ils mesurent ce que la phase 0 permet de conclure.

## 5. Couverture de l'intervalle de 80 % de l'hybride

| Région | Forages | Couverture |
|---|---|---|
| Ambatosoa | 10 | 60% |
| Analanjirofo | 25 | 76% |
| Androy | 507 | 85% |
| Anosy | 194 | 72% |
| Atsimo Andrefana | 460 | 73% |
| Atsimo Atsinanana | 78 | 65% |
| Boeny | 45 | 73% |
| Menabe | 16 | 44% |
| Sava | 50 | 90% |

| Distance au forage d'apprentissage le plus proche | Forages | Couverture | Erreur Fan (m) | Erreur krigeage (m) | Erreur hybride (m) |
|---|---|---|---|---|---|
| 0-25 km | 396 | 82% | 21.7 | 3.1 | 2.1 |
| 25-50 km | 441 | 79% | 23.2 | 3.0 | 2.5 |
| 50-100 km | 340 | 74% | 10.0 | 3.4 | 3.1 |
| plus de 100 km | 208 | 68% | 6.5 | 3.6 | 3.0 |
