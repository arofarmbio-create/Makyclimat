# Validation du modèle de crue sur le périmètre pilote

Généré le 2026-10-28 par `scripts/validate_floods.py`. Cahier des charges §7 et §13.

**Données**
- Périmètre : 174 communes (148 mailles GloFAS) avec un seuil de crue (Analamanga, Vakinankaratra, Antananarivo).
- Débit simulé : GloFAS, réanalyse journalière via Open-Meteo.
- Seuils : crue de 2 ans = vigilance, crue de 5 ans = alerte (loi de Gumbel sur les maxima annuels simulés 1984-2025).

**Ce qui n'est pas validé ici**
- La prévision et son délai d'anticipation : les archives de prévision GloFAS demandent un compte Copernicus CDS.
- Les débits réels : aucune station hydrométrique publique n'est disponible.

La validation est donc **partielle** (règle §13).

## 1. Les inondations documentées sont-elles détectées ?

3 événements documentés citent le périmètre. Un événement est détecté si au moins 10 % des communes dépassent le seuil dans la fenêtre [début − 2 j, fin + 10 j].

| Événement | Dates | Communes ≥ crue de 2 ans | Communes ≥ crue de 5 ans | Débit max / crue de 2 ans | Détecté (vigilance) | Détecté (alerte) |
|---|---|---|---|---|---|---|
| batsirai-2022 | 2022-01-24 → 2022-02-10 | 3 % | 0 % | 1,51 | **non** | non |
| ana-2022 | 2022-01-21 → 2022-01-25 | 7 % | 2 % | 1,56 | **non** | non |
| fytia-2026 | 2026-01-29 → 2026-02-03 | 32 % | 5 % | 1,60 | oui | non |

**Taux de détection : 1 / 3 en vigilance, 0 / 3 en alerte.**

## 2. Épisodes de dépassement sur les cours d'eau principaux (20 mailles de plus fort débit)

Saisons de pluie de novembre 2015 à avril 2026 (11 saisons). Un épisode = au moins 10 % des mailles au-dessus de la crue de 2 ans ; des jours séparés de plus de 5 jours forment des épisodes distincts.

- **12 épisodes**, soit environ 1,1 par saison.
- 1 correspondent à un événement documenté dans le périmètre.
- 3 correspondent à un événement documenté ailleurs à Madagascar, sans mention du périmètre.
- 5 correspondent seulement à un cyclone ou une inondation GDACS (37 événements indépendants de GloFAS, `validation/evenements_gdacs.csv`) : explication possible, région non précisée.
- **3 sans aucune correspondance.** Ce sont des fausses alertes possibles, à comparer avec la liste BNGRC des inondations non cycloniques.

| Début | Fin | Part max des mailles | Événement (périmètre) | Événement (ailleurs) | GDACS |
|---|---|---|---|---|---|
| 2017-03-08 | 2017-03-10 | 90 % | — | enawo-2017 | gdacs-tc-1000341;gdacs-fl-1000070 |
| 2018-01-06 | 2018-01-07 | 20 % | — | ava-2018 | gdacs-fl-1000155;gdacs-tc-1000429 |
| 2018-03-17 | 2018-03-19 | 55 % | — | — | gdacs-tc-1000438;gdacs-fl-1000176;gdacs-tc-1000441 |
| 2020-01-03 | 2020-01-03 | 10 % | — | — | — |
| 2020-01-21 | 2020-01-24 | 15 % | — | diane-2020 | — |
| 2020-02-21 | 2020-02-21 | 65 % | — | — | gdacs-tc-1000651 |
| 2023-01-21 | 2023-01-23 | 90 % | — | — | gdacs-tc-1000957 |
| 2024-01-19 | 2024-01-20 | 30 % | — | — | gdacs-tc-1001041 |
| 2024-02-16 | 2024-02-19 | 80 % | — | — | — |
| 2025-02-05 | 2025-02-05 | 10 % | — | — | gdacs-tc-1001139;gdacs-tc-1001138 |
| 2025-02-20 | 2025-02-20 | 20 % | — | — | — |
| 2026-02-01 | 2026-02-02 | 55 % | fytia-2026 | gezani-2026 | gdacs-tc-1001254 |

## 2 bis. Sensibilité au seuil : arbitrage entre détection et fausses alertes

Le seuil s'applique à la part des communes pour la détection des événements du périmètre, et à la part des mailles principales pour les épisodes.

| Seuil | Événements du périmètre détectés | Épisodes simulés | Dont événement du périmètre | Sans aucune correspondance |
|---|---|---|---|---|
| au moins 1 | 3 / 3 | 20 | 3 | 6 |
| 5 % | 2 / 3 | 20 | 3 | 6 |
| 10 % | 1 / 3 | 12 | 1 | 3 |
| 25 % | 1 / 3 | 7 | 1 | 1 |

Abaisser le seuil fait détecter plus d'événements, mais crée plus d'épisodes sans correspondance. Le choix du seuil opérationnel revient aux services (BNGRC, DGRE) : il n'est pas fixé ici.

## 3. Communes inondées selon le satellite (Copernicus EMS)

| Activation | Communes comparées | Inondées | Non inondées | AUC du débit simulé | Inondées en vigilance (≥ crue de 2 ans) | Non inondées en vigilance |
|---|---|---|---|---|---|---|
| EMSR264 (Ava) | 58 | 47 | 11 | 0,55 | 26 % | 27 % |

AUC : 0,5 = pas mieux que le hasard, 1 = séparation parfaite. Avec si peu d'activations, le résultat est indicatif.

## Limites

- Les seuils sont calculés sur le même débit simulé : on teste la cohérence du modèle avec les inondations, pas sa justesse en m³/s.
- Les mailles GloFAS (~5 km) sont plus grossières que l'inondation urbaine d'Antananarivo, qui dépend du drainage, des digues et du pompage. L'inondation pluviale (§7.A) n'est pas représentée.
- Avec si peu d'événements, les taux sont très incertains.

**Données qui rendraient la validation complète :** débits observés (DGRE), archive des prévisions GloFAS (compte CDS), liste BNGRC des inondations non cycloniques, cartes Sentinel-1 des zones inondées (GFM).
