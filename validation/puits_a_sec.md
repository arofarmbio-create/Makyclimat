# Puits à sec et recharge (test secondaire de T2, T2L et T2K)

Généré le 2026-11-09 par `scripts/puits_a_sec.py`, selon `validation/protocole_puits_a_sec.md` (fixé avant le calcul). Cas : Kaltsas, UNESCO IHP-WINS 2025 (doi:10.63253/r2yrjane, CC BY-SA). Référence : forages de Al-Zoubaidy, Monteleone et Bünzli 2023 (BushProof / DDC), coordonnées seulement. Calcul local, données brutes hors dépôt.

## Cartes figées utilisées

| Carte | Empreinte recalculée | Conforme à l'empreinte publiée |
|---|---|---|
| `recharge_t2l.csv` | `2dc024a9315b…` | oui |
| `recharge_t2k.csv` | `c844a8bcc417…` | oui |

## Sélection : principal

87 puits à sec et 1452 forages de référence dans l'emprise BushProof (120 blocs de 20 km). Part dans le domaine de T2L : cas 93%, référence 89%.

| Recharge | Médiane cas (mm/an) | Médiane référence | AUC (recharge faible) | Intervalle à 95 % |
|---|---|---|---|---|
| T2 | 59 | 55 | 0.450 | 0.359 à 0.536 |
| T2L | 21 | 52 | 0.561 | 0.465 à 0.655 |
| T2K | 59 | 59 | 0.477 | 0.385 à 0.564 |

| Comparaison | Différence d'AUC | Intervalle à 95 % | Gain exigé (≥ 0,05, intervalle sans 0) |
|---|---|---|---|
| T2L − T2 | +0.111 | -0.004 à +0.227 | non atteint |
| T2K − T2 | +0.027 | -0.008 à +0.060 | non atteint |

## Sélection : sensibilité (tous « Dry = Yes »)

310 puits à sec et 1382 forages de référence dans l'emprise BushProof (134 blocs de 20 km). Part dans le domaine de T2L : cas 85%, référence 89%.

| Recharge | Médiane cas (mm/an) | Médiane référence | AUC (recharge faible) | Intervalle à 95 % |
|---|---|---|---|---|
| T2 | 65 | 55 | 0.438 | 0.371 à 0.506 |
| T2L | 27 | 52 | 0.576 | 0.506 à 0.637 |
| T2K | 71 | 59 | 0.446 | 0.380 à 0.515 |

| Comparaison | Différence d'AUC | Intervalle à 95 % | Gain exigé (≥ 0,05, intervalle sans 0) |
|---|---|---|---|
| T2L − T2 | +0.138 | +0.051 à +0.221 | atteint |
| T2K − T2 | +0.008 | -0.016 à +0.030 | non atteint |

**H-P1 non soutenue** (sélection principale ; règle fixée avant le calcul).

Usage (protocole, section 6) : ce test appuie ou affaiblit le verdict du bilan de chlorure (en pause), sans décider seul.

Limites : seuls les points signalés sont visibles ; un puits peut sécher pour d'autres raisons (profondeur, pompage, année sèche) ; 2024-2025 n'est pas une année moyenne ; zone ZH10 de BushProof absente ; recharge en mailles de 0,25 à 0,5°, donc beaucoup d'ex aequo.

