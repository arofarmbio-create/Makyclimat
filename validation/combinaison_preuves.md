# Combinaison des preuves sur la recharge du Grand Sud

Généré le 2026-11-09 par `scripts/combinaison_preuves.py`, selon `validation/protocole_combinaison_preuves.md` (fixé avant le calcul). **Synthèse rétrospective** : toutes les lignes avaient déjà été vues ; elle résume, elle ne prouve pas à nouveau.

Scénario de dépôt de chlorure retenu : **aucun (MERRA-2 pas encore disponible)**.

## Scores par ligne (z unilatéral ; positif = dans le sens de la question)

| Ligne | Q1 : T2 surestime | Q2 : T2L plus juste que T2 |
|---|---|---|
| L1 fluctuation de nappe (groupes de sites) | +1.76 (n = 8) | -0.20 (n = 8) |
| L2 puits à sec (blocs) | sans objet | +1.88 (n = 120) |
| L3 chlorure, scénario bas (blocs, après coup) | +5.23 (n = 36) | +3.94 (n = 33) |
| L3 chlorure, scénario central (blocs, après coup) | +5.23 (n = 36) | +2.56 (n = 33) |
| L3 chlorure, scénario haut (blocs, après coup) | +0.53 (n = 36) | -3.28 (n = 33) |

## Combinaison (Z de Stouffer pondéré par √n)

| Scénario de dépôt | Q1 : Z | Q1 : verdict | Q2 : Z | Q2 : verdict |
|---|---|---|---|---|
| bas | +5.48 | établi | +3.37 | établi |
| central | +5.48 | établi | +2.74 | établi |
| haut | +1.23 | indice | +0.10 | non établi (contradiction forte d'une ligne) |
| sans le chlorure | +1.76 | indice | +1.77 | indice |

Règle (fixée avant le calcul) : « établi » si Z ≥ 1,96 dans le scénario retenu et aucune ligne à z ≤ −1,96 ; « indice » si 1,0 ≤ Z < 1,96 ; « non établi » sinon. Sans scénario retenu, aucun verdict global n'est prononcé.

Dépendances : L2 et L3 couvrent la même région et les mêmes forages BushProof ; L3 est fragilisée par le chlorure venu des roches (Cl/Na médian 0,96), ce qui abaisse la recharge par chlorure et favorise Q1. L1 n'est pas indépendante de la construction de T2L (ses sites ont servi à T2L ; chacun est évalué en laissant son groupe de côté).

