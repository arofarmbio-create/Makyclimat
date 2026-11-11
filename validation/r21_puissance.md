# R-21 — Analyse de puissance du critère H1 (inférence par saisons)

Calcul du 11/11/2026 par [`scripts/r21_puissance.py`](../scripts/r21_puissance.py), 4000 simulations par case, graine fixe. Structure réelle tirée de [`r21_eligibilite.csv`](r21_eligibilite.csv) : **376 unités épisode × district, 20 épisodes, 11 saisons**. Détection du contrôle par unité : 0.4 en moyenne (écart type 0.15 entre épisodes) ; corrélation des méthodes par unité : 0.5. Gain moyen recalé exactement. Test A (principal) : permutation exacte des signes par saison. Le McNemar par épisode est écarté (fiche, section 5). Unilatéraux, α = 0,05. τ : écart type du gain entre saisons ; ω = 0,10 entre épisodes ; r : part des districts d'un épisode qui reprennent le tirage commun (paramètre du simulateur, non observable). La **CCI des différences** (corrélation intra-épisode de ens. − contrôle par district) est la grandeur observable qui relie chaque scénario à une estimation sur les prévisions.

## Erreur de type I (gain nul)

| τ | r | CCI des différences | Test A (saisons) | ± erreur Monte-Carlo |
|---:|---:|---:|---:|---:|
| 0,00 | 0,3 | 0,12 | 4,9 % | 0,7 |
| 0,00 | 0,5 | 0,26 | 5,0 % | 0,7 |
| 0,00 | 0,6 | 0,36 | 4,5 % | 0,6 |
| 0,00 | 0,7 | 0,47 | 4,2 % | 0,6 |
| 0,00 | 0,9 | 0,77 | 4,4 % | 0,6 |
| 0,10 | 0,3 | 0,14 | 5,1 % | 0,7 |
| 0,10 | 0,5 | 0,28 | 4,5 % | 0,6 |
| 0,10 | 0,6 | 0,37 | 4,8 % | 0,7 |
| 0,10 | 0,7 | 0,49 | 4,2 % | 0,6 |
| 0,10 | 0,9 | 0,78 | 4,0 % | 0,6 |
| 0,20 | 0,3 | 0,20 | 4,7 % | 0,7 |
| 0,20 | 0,5 | 0,33 | 4,7 % | 0,7 |
| 0,20 | 0,6 | 0,42 | 4,5 % | 0,6 |
| 0,20 | 0,7 | 0,53 | 4,3 % | 0,6 |
| 0,20 | 0,9 | 0,81 | 4,2 % | 0,6 |

## Gain de 30 points (fixé par le porteur)

| τ | r | CCI des différences | Test A (saisons) | ± erreur Monte-Carlo |
|---:|---:|---:|---:|---:|
| 0,00 | 0,3 | 0,12 | 99,6 % | 0,2 |
| 0,00 | 0,5 | 0,26 | 93,2 % | 0,8 |
| 0,00 | 0,6 | 0,37 | 86,7 % | 1,1 |
| 0,00 | 0,7 | 0,49 | 79,9 % | 1,2 |
| 0,00 | 0,9 | 0,80 | 67,5 % | 1,5 |
| 0,10 | 0,3 | 0,14 | 99,0 % | 0,3 |
| 0,10 | 0,5 | 0,28 | 91,5 % | 0,9 |
| 0,10 | 0,6 | 0,38 | 84,7 % | 1,1 |
| 0,10 | 0,7 | 0,50 | 77,0 % | 1,3 |
| 0,10 | 0,9 | 0,81 | 67,6 % | 1,5 |
| 0,20 | 0,3 | 0,19 | 95,1 % | 0,7 |
| 0,20 | 0,5 | 0,32 | 86,3 % | 1,1 |
| 0,20 | 0,6 | 0,42 | 79,4 % | 1,3 |
| 0,20 | 0,7 | 0,53 | 75,1 % | 1,3 |
| 0,20 | 0,9 | 0,82 | 62,3 % | 1,5 |

