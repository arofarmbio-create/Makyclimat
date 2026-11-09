# Recharge par bilan de chlorure dans le Grand Sud

Généré le 2026-11-09 par `scripts/recharge_chlorure.py`, selon `validation/protocole_recharge_chlorure.md` (fixé avant le calcul ; dépôt de chlorure et filtres fixés le 09/11/2026 avant toute lecture des chlorures). Forages : Al-Zoubaidy, Monteleone et Bünzli (2023), BushProof / DDC, 1 487 sur 2 880 récupérés (zone ZH10 absente). Chlorure de la pluie : Kwale, Kenya (Ferrer, Folch et Thomas 2019) et Van Wyk et al. (2011). Calcul local ; données brutes hors dépôt.

## Sélection

| Étape | Forages |
|---|---|
| avec chlorure positif | 559 |
| après côte (≥ 5 km) | 559 |
| après nitrate (≤ 50 mg/L) | 539 |
| après autre source de sels | 538 |
| zones de validation (lien simple à 20 km, au moins 3 forages) | 2 zones, 537 forages |

Distance médiane des zones à la côte : 62 km ; chlorure médian des zones : 564 mg/L (de 60 à 1069).

## Recharge par chlorure et accord avec les cartes figées

Écart = médiane de |log₁₀(modèle / chlorure)| (0,3 = facteur 2) ; biais = médiane de log₁₀(modèle / chlorure) (positif : modèle trop fort).

| Scénario | Recharge médiane (mm/an) | T2 : écart | T2 : biais | T2 : Spearman (p) | T2L : écart | T2L : biais | T2L : Spearman (p) | Domaine T2L : écart T2 → T2L (2 zones) |
|---|---|---|---|---|---|---|---|---|
| bas | 3 | 1.44 | +1.44 | +1.00 (nan) | 1.35 | +1.35 | -1.00 (nan) | 1.44 → 1.35 |
| central | 6 | 1.11 | +1.11 | +1.00 (nan) | 1.02 | +1.02 | -1.00 (nan) | 1.11 → 1.02 |
| haut | 36 | 0.45 | +0.45 | +1.00 (nan) | 1.03 | +0.36 | -1.00 (nan) | 0.45 → 1.03 |

Contrôle préalable : T2 déjà à moins d'un facteur 1,5 dans les trois scénarios ? **non**.

- **H-Cl1 non soutenue** (T2 suit l'ordre des zones et reste à un facteur 2, dans les trois scénarios ; bas : non, central : non, haut : non).
- **H-Cl2 non soutenue** (T2L réduit l'écart d'au moins 30 % dans son domaine, dans les trois scénarios ; bas : non, central : non, haut : non).
- H-Cl3 (karst) : infaisable, aucun forage karstique dans les données récupérées.
- **H-Cl4 soutenue** (fluctuation et chlorure dans un facteur 3 pour au moins la moitié des sites, scénario central : 1 sur 1 ; bas : 1 sur 1 ; haut : 0 sur 1).

## Sites de fluctuation de nappe proches d'une zone (H-Cl4)

| Site | Source | Distance (km) | Fluctuation (mm/an) | Chlorure, central (mm/an) | Rapport bas / central / haut |
|---|---|---|---|---|---|
| Andaboly | HT (MGMERL) | 0.2 | 6 | 10 | 1.09 / 0.57 / 0.09 |

## Décision (fixée avant le calcul)

T2 reste la valeur centrale ; la recharge par chlorure est publiée comme estimation indépendante du Grand Sud, avec ses trois scénarios.

Limites : chlorure d'autres origines (roches marines, évaporites, embruns, pollution) seulement en partie filtré ; recharge de long terme (décennies) contre années récentes pour la fluctuation ; recharge concentrée mal vue ; base compilée de qualité hétérogène ; dépôt de chlorure non mesuré à Madagascar (sources kényane et sud-africaine) ; longueur de décroissance L choisie.

