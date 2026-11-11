# R-21 — Analyse de puissance du critère H1 (inférence par saisons)

Calcul du 11/11/2026 par [`scripts/r21_puissance.py`](../scripts/r21_puissance.py), 4000 simulations par case, graine fixe. Structure réelle tirée de [`r21_eligibilite.csv`](r21_eligibilite.csv) : **440 unités épisode × district, 23 épisodes, 12 saisons**. Détection du contrôle par unité : 0.4 en moyenne (écart type 0.15 entre épisodes) ; corrélation des méthodes par unité : 0.5. Gain moyen recalé exactement. Test A (principal) : permutation exacte des signes par saison. Le McNemar par épisode est écarté (fiche, section 5). Unilatéraux, α = 0,05. τ : écart type du gain entre saisons ; ω = 0,10 entre épisodes ; r : part des districts d'un épisode qui reprennent le tirage commun (paramètre du simulateur, non observable). La **CCI des différences** (corrélation intra-épisode de ens. − contrôle par district) est la grandeur observable qui relie chaque scénario à une estimation sur les prévisions.

## Erreur de type I (gain nul)

| τ | r | CCI des différences | Test A (saisons) | ± erreur Monte-Carlo |
|---:|---:|---:|---:|---:|
| 0,00 | 0,3 | 0,12 | 5,3 % | 0,7 |
| 0,00 | 0,5 | 0,26 | 5,5 % | 0,7 |
| 0,00 | 0,6 | 0,36 | 4,8 % | 0,7 |
| 0,00 | 0,7 | 0,48 | 4,8 % | 0,7 |
| 0,00 | 0,9 | 0,79 | 4,5 % | 0,6 |
| 0,10 | 0,3 | 0,15 | 4,4 % | 0,6 |
| 0,10 | 0,5 | 0,28 | 4,4 % | 0,6 |
| 0,10 | 0,6 | 0,38 | 4,9 % | 0,7 |
| 0,10 | 0,7 | 0,50 | 4,2 % | 0,6 |
| 0,10 | 0,9 | 0,80 | 4,3 % | 0,6 |
| 0,20 | 0,3 | 0,21 | 4,0 % | 0,6 |
| 0,20 | 0,5 | 0,33 | 4,2 % | 0,6 |
| 0,20 | 0,6 | 0,43 | 4,7 % | 0,7 |
| 0,20 | 0,7 | 0,53 | 4,6 % | 0,6 |
| 0,20 | 0,9 | 0,81 | 5,0 % | 0,7 |

## Gain de 30 points (fixé par le porteur)

| τ | r | CCI des différences | Test A (saisons) | ± erreur Monte-Carlo |
|---:|---:|---:|---:|---:|
| 0,00 | 0,3 | 0,12 | 99,8 % | 0,1 |
| 0,00 | 0,5 | 0,26 | 96,0 % | 0,6 |
| 0,00 | 0,6 | 0,37 | 90,5 % | 0,9 |
| 0,00 | 0,7 | 0,49 | 84,0 % | 1,1 |
| 0,00 | 0,9 | 0,80 | 71,4 % | 1,4 |
| 0,10 | 0,3 | 0,14 | 99,5 % | 0,2 |
| 0,10 | 0,5 | 0,28 | 94,0 % | 0,7 |
| 0,10 | 0,6 | 0,38 | 88,6 % | 1,0 |
| 0,10 | 0,7 | 0,51 | 81,7 % | 1,2 |
| 0,10 | 0,9 | 0,81 | 70,3 % | 1,4 |
| 0,20 | 0,3 | 0,19 | 96,2 % | 0,6 |
| 0,20 | 0,5 | 0,33 | 89,0 % | 1,0 |
| 0,20 | 0,6 | 0,43 | 84,0 % | 1,1 |
| 0,20 | 0,7 | 0,53 | 79,1 % | 1,3 |
| 0,20 | 0,9 | 0,82 | 66,8 % | 1,5 |

