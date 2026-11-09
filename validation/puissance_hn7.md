# Analyse de puissance du maillon A de H-N7 (avant tout calcul)

Généré le 2026-11-09 par `scripts/puissance_hn7.py`. Simulation seule, sans les données de pluie : 45 saisons, 9 tests (3 régions × 3 indices), Benjamini-Hochberg à 10%, 3000 simulations par case. r = corrélation entre l'indice de juillet-septembre et la pluie latente de la saison ; p = part des saisons avec au moins un mois extrême. Seule l'épreuve 3 (Spearman) est simulée : la puissance réelle, avec les quatre épreuves, est au plus celle-ci.

## 1 vrai(s) lien(s) parmi les 9 tests

| r | p = 20 % | p = 30 % | p = 45 % |
|---|---|---|---|
| 0.2 | 5% | 7% | 7% |
| 0.3 | 11% | 16% | 17% |
| 0.4 | 25% | 31% | 34% |
| 0.5 | 44% | 53% | 60% |

## 3 vrai(s) lien(s) parmi les 9 tests

| r | p = 20 % | p = 30 % | p = 45 % |
|---|---|---|---|
| 0.2 | 16% | 17% | 20% |
| 0.3 | 33% | 41% | 45% |
| 0.4 | 59% | 70% | 74% |
| 0.5 | 83% | 90% | 94% |

## Lecture

- Avec 45 saisons et un résultat binaire, seul un lien fort (r d'au moins 0,4 à 0,5) a de bonnes chances d'être retenu après correction ; un lien modéré (r = 0,2 à 0,3), plausible d'après la littérature (« moins clair » dans le sud-ouest), est presque indétectable.
- Règle adoptée le 09/11/2026 : si la puissance est inférieure à 50 % pour l'effet plausible, le test est déclaré **exploratoire dès le départ** ; un résultat négatif ne réfutera alors pas le lien océan → pluies extrêmes.
- Gains possibles sans changer l'hypothèse : remplacer le résultat binaire par le **nombre de mois extrêmes** ou par la pluie maximale mensuelle (variable continue, plus puissante) ; réduire le nombre de tests (une région, un indice choisis par la littérature). Ces changements seraient datés dans le protocole avant tout calcul.

