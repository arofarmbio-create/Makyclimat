# Nappe régionale profonde : inverser le raisonnement

Généré le 2026-11-09 par `scripts/nappe_regionale.py`, selon `validation/protocole_nappe_regionale.md` (fixé avant le calcul). Forages : Al-Zoubaidy, Monteleone et Bünzli (2023), BushProof / DDC. Calcul local, données brutes hors dépôt.

538 forages avec chlorure (511 avec charge, 516 avec profondeur de crépine) ; 43 blocs de 20 km. Spearman au forage ; intervalles à 95 % par blocs.

## Contrôle préalable : le cadre local échoue-t-il ?

ρ(chlorure, pluie locale) = +0.20 [+0.03 ; +0.35] → **le cadre local n explique pas le chlorure**.

## Hypothèses

| Hypothèse | Valeur | Intervalle à 95 % | Verdict |
|---|---|---|---|
| H-D1 : ρ(chlorure, charge) < 0 | -0.31 | -0.44 ; -0.18 | **soutenue** |
| H-D2 : ρ(chlorure, profondeur captée) ≠ 0 | +0.18 | +0.10 ; +0.29 | **soutenue** |
| H-D3 : \|ρ(Cl, charge)\| − \|ρ(Cl, pluie)\| > 0 | +0.11 | -0.09 ; +0.31 | **non soutenue** |
| H-D4 : T2 / recharge par chlorure au bloc (36 blocs), brute → à charge fixée | -0.22 → +0.09 | — | **soutenue** |
| H-D5 : charge des puits à sec (87) contre référence (1109), AUC | 0.498 | 0.394 ; 0.609 | **non soutenue** |
| H-D6 : avec la profondeur, minéralisation ↑ et Cl/Na ↓ | +0.22 et -0.09 | +0.13 ; +0.32 et -0.19 ; +0.01 | **non soutenue** |

Descriptif : ρ(chlorure, charge) à distance à la côte fixée = +0.08 [-0.08 ; +0.16] (contrôle de l'effet des embruns, plus forts en bas près de la côte).

## Par type d'aquifère (au moins 30 forages)

| Type | Forages | ρ(Cl, charge) | ρ(Cl, profondeur) | ρ(minéralisation, profondeur) | ρ(Cl/Na, profondeur) | Cl/Na médian (eau de mer : 1,80) |
|---|---|---|---|---|---|---|
| Fracturé | 517 | -0.29 | +0.17 | +0.21 | -0.11 | 0.93 |

Cl/Na médian, tous forages : 0.96 (eau de mer et embruns : 1,80 en masse ; nettement plus bas : sodium venu des roches ou des sols ; nettement plus haut : autre source de chlorure).

## Décision (fixée avant le calcul)

Le cadre local reste ; les inversions restent inexpliquées par ce test et sont publiées comme telles.

Limites : charges mesurées à des dates différentes ; zone ZH10 absente ; socle fracturé majoritaire ; charge des puits à sec interpolée (8 forages les plus proches, 1/d²).

