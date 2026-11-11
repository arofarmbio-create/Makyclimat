# R-21 — Analyse de puissance du critère H1 (inférence par saisons)

Calcul du 11/11/2026 par [`scripts/r21_puissance.py`](../scripts/r21_puissance.py), 2000 simulations par case, graine fixe. Structure réelle tirée de [`r21_eligibilite.csv`](r21_eligibilite.csv) : **440 unités épisode × district, 23 épisodes, 12 saisons**. Détection du contrôle par unité : 0.4 en moyenne (écart type 0.15 entre épisodes) ; corrélation des méthodes par unité : 0.5. Gain moyen recalé exactement. Test A (principal) : permutation exacte des signes par saison. Test B : McNemar exact par épisode. Unilatéraux, α = 0,05. τ : écart type du gain entre saisons ; ω = 0,10 entre épisodes ; r : part des districts d'un épisode qui partagent le même résultat.

## Erreur de type I (gain nul)

| τ | r | Test A (saisons) | Test B (épisodes) |
|---:|---:|---:|---:|
| 0,00 | 0,3 | 5 % | 0 % |
| 0,00 | 0,6 | 4 % | 0 % |
| 0,00 | 0,9 | 4 % | 1 % |
| 0,10 | 0,3 | 4 % | 0 % |
| 0,10 | 0,6 | 5 % | 0 % |
| 0,10 | 0,9 | 4 % | 1 % |
| 0,20 | 0,3 | 5 % | 0 % |
| 0,20 | 0,6 | 4 % | 0 % |
| 0,20 | 0,9 | 4 % | 1 % |

## Gain de 20 points

| τ | r | Test A (saisons) | Test B (épisodes) |
|---:|---:|---:|---:|
| 0,00 | 0,3 | 95 % | 6 % |
| 0,00 | 0,6 | 67 % | 11 % |
| 0,00 | 0,9 | 48 % | 26 % |
| 0,10 | 0,3 | 89 % | 4 % |
| 0,10 | 0,6 | 65 % | 10 % |
| 0,10 | 0,9 | 46 % | 25 % |
| 0,20 | 0,3 | 74 % | 3 % |
| 0,20 | 0,6 | 55 % | 6 % |
| 0,20 | 0,9 | 41 % | 22 % |

## Gain de 30 points

| τ | r | Test A (saisons) | Test B (épisodes) |
|---:|---:|---:|---:|
| 0,00 | 0,3 | 100 % | 10 % |
| 0,00 | 0,6 | 90 % | 23 % |
| 0,00 | 0,9 | 71 % | 48 % |
| 0,10 | 0,3 | 100 % | 9 % |
| 0,10 | 0,6 | 89 % | 20 % |
| 0,10 | 0,9 | 71 % | 50 % |
| 0,20 | 0,3 | 96 % | 9 % |
| 0,20 | 0,6 | 85 % | 17 % |
| 0,20 | 0,9 | 67 % | 45 % |

