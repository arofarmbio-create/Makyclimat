# Validation du modèle de crue sur le périmètre pilote

Généré le 2026-10-28 par `scripts/validate_floods.py`. Cahier des charges §7 et §13.

> **Résultat incomplet** : le quota gratuit d'Open-Meteo a été atteint. Relancer le workflow « 10 » pour compléter.

**Données**
- Périmètre : 162 communes (136 mailles GloFAS) avec un seuil de crue (Analamanga, Vakinankaratra, Antananarivo).
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

## 2. Épisodes de dépassement sur les cours d'eau principaux (20 mailles de plus fort débit)

Saisons de pluie de novembre 2015 à avril 2015 (0 saisons). Un épisode = au moins 10 % des mailles au-dessus de la crue de 2 ans ; des jours séparés de plus de 5 jours forment des épisodes distincts.

- **0 épisodes**, soit environ 0,0 par saison.
- 0 correspondent à un événement documenté dans le périmètre.
- 0 correspondent à un événement documenté ailleurs à Madagascar, sans mention du périmètre.
- **0 sans aucune correspondance.** Ce sont des fausses alertes possibles, à comparer avec la liste BNGRC des inondations non cycloniques.

| Début | Fin | Part max des mailles | Événement (périmètre) | Événement (ailleurs) |
|---|---|---|---|---|

## 3. Communes inondées selon le satellite (Copernicus EMS)

Aucune activation EMS sourcée avec au moins 5 communes du périmètre.

## Limites

- Les seuils sont calculés sur le même débit simulé : on teste la cohérence du modèle avec les inondations, pas sa justesse en m³/s.
- Les mailles GloFAS (~5 km) sont plus grossières que l'inondation urbaine d'Antananarivo, qui dépend du drainage, des digues et du pompage. L'inondation pluviale (§7.A) n'est pas représentée.
- Avec si peu d'événements, les taux sont très incertains.

**Données qui rendraient la validation complète :** débits observés (DGRE), archive des prévisions GloFAS (compte CDS), liste BNGRC des inondations non cycloniques, cartes Sentinel-1 des zones inondées (GFM).
