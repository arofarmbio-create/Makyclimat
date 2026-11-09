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


## Variantes pour gagner en puissance (simulation du 09/11/2026, avant tout calcul)

Un seul vrai lien ; part des saisons extrêmes 30% pour la version binaire ; 4000 simulations.

| r | Binaire, 9 tests (protocole actuel) | Continu, 9 tests | Binaire, 1 test | **Continu, 1 test** |
|---|---|---|---|---|
| 0.2 | 5% | 11% | 12% | **23%** |
| 0.3 | 10% | 28% | 21% | **47%** |
| 0.4 | 18% | 54% | 35% | **74%** |
| 0.5 | 29% | 79% | 51% | **91%** |

Lecture : le résultat continu et le test unique ajoutent chacun de la puissance ; ensemble, ils rendent détectable un lien d'environ 0,4 et donnent une chance réelle à un lien de 0,3. Un lien de 0,2 reste hors de portée avec 45 saisons.

