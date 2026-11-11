# R-21 — Analyse de puissance du critère H1

Calcul du 11/11/2026 par [`scripts/r21_puissance.py`](../scripts/r21_puissance.py) (20000 simulations par case, graine fixe). Test apparié exact de McNemar unilatéral, α = 0,05. Épisodes répartis au mieux entre les saisons ; ρ = corrélation intra-saison des discordances.

Scénarios : p(ensemble seul) – p(contrôle seul) = gain de détection. Le gain jugé pertinent est à fixer par le porteur du projet avant les scores.

## ρ = 0,0

| Épisodes (saisons) | 0,25 / 0,05 (gain 20 pts) | 0,35 / 0,05 (gain 30 pts) | 0,45 / 0,05 (gain 40 pts) |
|---:|---:|---:|---:|
| 15 (7) | 19 % | 41 % | 62 % |
| 25 (12) | 43 % | 72 % | 89 % |
| 10 (6) | 6 % | 17 % | 35 % |
| 20 (8) | 31 % | 58 % | 80 % |
| 30 (12) | 52 % | 82 % | 95 % |
| 50 (16) | 81 % | 97 % | 100 % |

## ρ = 0,1

| Épisodes (saisons) | 0,25 / 0,05 (gain 20 pts) | 0,35 / 0,05 (gain 30 pts) | 0,45 / 0,05 (gain 40 pts) |
|---:|---:|---:|---:|
| 15 (7) | 19 % | 41 % | 62 % |
| 25 (12) | 43 % | 71 % | 90 % |
| 10 (6) | 6 % | 19 % | 35 % |
| 20 (8) | 31 % | 58 % | 79 % |
| 30 (12) | 52 % | 81 % | 95 % |
| 50 (16) | 80 % | 97 % | 100 % |

## ρ = 0,3

| Épisodes (saisons) | 0,25 / 0,05 (gain 20 pts) | 0,35 / 0,05 (gain 30 pts) | 0,45 / 0,05 (gain 40 pts) |
|---:|---:|---:|---:|
| 15 (7) | 18 % | 40 % | 62 % |
| 25 (12) | 42 % | 71 % | 89 % |
| 10 (6) | 6 % | 19 % | 35 % |
| 20 (8) | 31 % | 57 % | 78 % |
| 30 (12) | 52 % | 80 % | 94 % |
| 50 (16) | 79 % | 96 % | 100 % |

