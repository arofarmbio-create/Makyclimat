# Inondation pluviale : deux indicateurs fondés sur la pluie, validés sur le périmètre pilote

Généré le 2026-10-28 par `scripts/validate_pluvial.py`. Cahier des charges §7.A, §7.B, §8, §13. À comparer avec le modèle de rivière : `crues_validation.md`.

**Périmètre** : 1977 fokontany de 174 communes (Analamanga, Vakinankaratra, Antananarivo). Pluie CHIRPS journalière, 11 saisons de test (novembre 2015 à avril 2026).

**Indicateurs**
- **Pluie** : cumul sur 3 jours, comparé au maximum saisonnier de retour 2 ans (vigilance) et 5 ans (alerte) du fokontany (15 saisons, 2006-2020).
- **Ruissellement** (idée du porteur du projet : infiltration urbaine faible mais non nulle) : lame ruisselée SCS-CN du cumul sur 3 jours.
  - CN de l'occupation du sol et du sol : médiane 85,3, de 71,2 à 91,9. En ville, il vaut environ 92, soit une infiltration faible mais non nulle.
  - CN ajusté selon la pluie des 5 jours précédents (sol sec ou humide, règle NRCS).
  - Fokontany sans CN calculé : 0 (médiane du périmètre utilisée à la place).
  - Seuils communs au périmètre : 74,1 mm (retour 2 ans), 96,8 mm (retour 5 ans).

**Limites** : pas d'intensité horaire ; drainage, digues et pompage non représentés ; CN tabulés, non calés ; les saisons 2015-2020 servent aussi aux seuils. La validation est **partielle**.

## Comparaison des deux indicateurs (seuil : 10 % des fokontany)

| Indicateur | Inondations documentées détectées | Épisodes simulés | Dont événement du périmètre | Sans aucune correspondance | AUC communes inondées (EMS) |
|---|---|---|---|---|---|
| Pluie sur 3 jours (seuil local) | 2 / 3 | 9 | 1 | 4 | 0,36 |
| Ruissellement SCS-CN (seuil commun au périmètre) | 3 / 3 | 15 | 2 | 7 | 0,17 |

Pour le modèle de rivière (GloFAS) au même seuil : voir `crues_validation.md`.

## Pluie sur 3 jours (seuil local)

### Inondations documentées

| Événement | Dates | Fokontany ≥ 2 ans | Fokontany ≥ 5 ans | Valeur max (mm) | Max / seuil 2 ans | Vigilance | Alerte |
|---|---|---|---|---|---|---|---|
| batsirai-2022 | 2022-01-24 → 2022-02-10 | 81 % | 67 % | 238 | 1,83 | oui | oui |
| ana-2022 | 2022-01-21 → 2022-01-25 | 81 % | 67 % | 238 | 1,83 | oui | oui |
| fytia-2026 | 2026-01-29 → 2026-02-03 | 0 % | 0 % | 126 | 1,09 | **non** | non |

### Sensibilité au seuil

| Seuil (part des fokontany) | Événements détectés | Épisodes | Dont événement du périmètre | Sans aucune correspondance |
|---|---|---|---|---|
| au moins 1 | 3 / 3 | 44 | 3 | 24 |
| 5 % | 2 / 3 | 14 | 1 | 7 |
| 10 % | 2 / 3 | 9 | 1 | 4 |
| 25 % | 2 / 3 | 6 | 1 | 3 |

### Épisodes (seuil de 10 %)

| Début | Fin | Part max | Événement (périmètre) | Événement (ailleurs) | GDACS |
|---|---|---|---|---|---|
| 2018-01-06 | 2018-01-07 | 94 % | — | ava-2018 | gdacs-fl-1000155;gdacs-tc-1000429 |
| 2019-01-11 | 2019-01-12 | 30 % | — | — | — |
| 2020-01-01 | 2020-01-04 | 48 % | — | — | — |
| 2020-01-22 | 2020-01-22 | 11 % | — | diane-2020 | — |
| 2020-02-20 | 2020-02-22 | 57 % | — | — | gdacs-tc-1000651 |
| 2021-02-12 | 2021-02-12 | 13 % | — | — | — |
| 2022-01-18 | 2022-01-25 | 81 % | batsirai-2022;ana-2022 | — | gdacs-tc-1000858;gdacs-tc-1000859 |
| 2023-01-12 | 2023-01-13 | 28 % | — | — | — |
| 2024-01-07 | 2024-01-07 | 20 % | — | alvaro-2024 | gdacs-tc-1001040 |

### Communes inondées selon le satellite (Copernicus EMS)

| Activation | Communes | Inondées | Non inondées | AUC | Inondées ≥ seuil 2 ans | Non inondées ≥ seuil 2 ans |
|---|---|---|---|---|---|---|
| EMSR264 (Ava) | 58 | 47 | 11 | 0,36 | 100 % | 100 % |

## Ruissellement SCS-CN (seuil commun au périmètre)

### Inondations documentées

| Événement | Dates | Fokontany ≥ 2 ans | Fokontany ≥ 5 ans | Valeur max (mm) | Max / seuil 2 ans | Vigilance | Alerte |
|---|---|---|---|---|---|---|---|
| batsirai-2022 | 2022-01-24 → 2022-02-10 | 88 % | 76 % | 200 | 2,70 | oui | oui |
| ana-2022 | 2022-01-21 → 2022-01-25 | 88 % | 76 % | 200 | 2,70 | oui | oui |
| fytia-2026 | 2026-01-29 → 2026-02-03 | 25 % | 6 % | 105 | 1,41 | oui | non |

### Sensibilité au seuil

| Seuil (part des fokontany) | Événements détectés | Épisodes | Dont événement du périmètre | Sans aucune correspondance |
|---|---|---|---|---|
| au moins 1 | 3 / 3 | 40 | 2 | 23 |
| 5 % | 3 / 3 | 23 | 2 | 12 |
| 10 % | 3 / 3 | 15 | 2 | 7 |
| 25 % | 3 / 3 | 9 | 2 | 4 |

### Épisodes (seuil de 10 %)

| Début | Fin | Part max | Événement (périmètre) | Événement (ailleurs) | GDACS |
|---|---|---|---|---|---|
| 2015-12-28 | 2015-12-29 | 24 % | — | — | — |
| 2016-01-16 | 2016-01-16 | 14 % | — | — | — |
| 2018-01-05 | 2018-01-08 | 86 % | — | ava-2018 | gdacs-fl-1000155;gdacs-tc-1000429 |
| 2019-01-10 | 2019-01-13 | 75 % | — | — | — |
| 2020-01-02 | 2020-01-04 | 60 % | — | — | — |
| 2020-01-22 | 2020-01-23 | 25 % | — | diane-2020 | — |
| 2020-02-20 | 2020-02-23 | 77 % | — | — | gdacs-tc-1000651 |
| 2021-01-27 | 2021-01-27 | 24 % | — | — | gdacs-tc-1000760 |
| 2021-02-11 | 2021-02-13 | 43 % | — | — | — |
| 2022-01-17 | 2022-01-25 | 88 % | batsirai-2022;ana-2022 | — | gdacs-tc-1000858;gdacs-tc-1000859 |
| 2023-01-13 | 2023-01-13 | 26 % | — | — | — |
| 2023-01-27 | 2023-01-27 | 28 % | — | — | gdacs-tc-1000957 |
| 2024-01-07 | 2024-01-07 | 11 % | — | alvaro-2024 | gdacs-tc-1001040 |
| 2025-12-25 | 2025-12-25 | 13 % | — | — | — |
| 2026-01-31 | 2026-01-31 | 25 % | fytia-2026 | — | gdacs-tc-1001250;gdacs-tc-1001254 |

### Communes inondées selon le satellite (Copernicus EMS)

| Activation | Communes | Inondées | Non inondées | AUC | Inondées ≥ seuil 2 ans | Non inondées ≥ seuil 2 ans |
|---|---|---|---|---|---|---|
| EMSR264 (Ava) | 58 | 47 | 11 | 0,17 | 100 % | 100 % |

**Données qui amélioreraient les indicateurs :** pluie horaire (GPM IMERG, compte NASA Earthdata ; pluviographes de Météo Madagascar), inventaire BNGRC des inondations urbaines, réseau de drainage et zones de pompage d'Antananarivo, CN calés sur des mesures.
