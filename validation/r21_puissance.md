# R-21 — Analyse de puissance du critère H1 (inférence par saisons)

Calcul du 11/11/2026 par [`scripts/r21_puissance.py`](../scripts/r21_puissance.py), 2000 simulations par case, graine fixe. Structure réelle tirée de [`r21_eligibilite.csv`](r21_eligibilite.csv) : **376 unités épisode × district, 20 épisodes, 11 saisons**. Détection du contrôle par unité : 0.4 en moyenne (écart type 0.15 entre épisodes) ; corrélation des méthodes par unité : 0.5. Gain moyen recalé exactement. Test A (principal) : permutation exacte des signes par saison. Test B : McNemar exact par épisode. Unilatéraux, α = 0,05. τ : écart type du gain entre saisons ; ω = 0,10 entre épisodes ; r : part des districts d'un épisode qui partagent le même résultat.

## Erreur de type I (gain nul)

| τ | r | Test A (saisons) | Test B (épisodes) |
|---:|---:|---:|---:|
| 0,00 | 0,3 | 5 % | 0 % |
| 0,00 | 0,6 | 5 % | 0 % |
| 0,00 | 0,9 | 5 % | 1 % |
| 0,10 | 0,3 | 4 % | 0 % |
| 0,10 | 0,6 | 4 % | 0 % |
| 0,10 | 0,9 | 5 % | 1 % |
| 0,20 | 0,3 | 4 % | 0 % |
| 0,20 | 0,6 | 5 % | 0 % |
| 0,20 | 0,9 | 4 % | 1 % |

## Gain de 20 points

| τ | r | Test A (saisons) | Test B (épisodes) |
|---:|---:|---:|---:|
| 0,00 | 0,3 | 91 % | 3 % |
| 0,00 | 0,6 | 63 % | 8 % |
| 0,00 | 0,9 | 44 % | 21 % |
| 0,10 | 0,3 | 85 % | 3 % |
| 0,10 | 0,6 | 62 % | 7 % |
| 0,10 | 0,9 | 42 % | 20 % |
| 0,20 | 0,3 | 70 % | 2 % |
| 0,20 | 0,6 | 50 % | 5 % |
| 0,20 | 0,9 | 39 % | 16 % |

## Gain de 30 points

| τ | r | Test A (saisons) | Test B (épisodes) |
|---:|---:|---:|---:|
| 0,00 | 0,3 | 100 % | 8 % |
| 0,00 | 0,6 | 87 % | 15 % |
| 0,00 | 0,9 | 67 % | 46 % |
| 0,10 | 0,3 | 99 % | 7 % |
| 0,10 | 0,6 | 86 % | 15 % |
| 0,10 | 0,9 | 68 % | 41 % |
| 0,20 | 0,3 | 94 % | 6 % |
| 0,20 | 0,6 | 79 % | 12 % |
| 0,20 | 0,9 | 65 % | 38 % |

