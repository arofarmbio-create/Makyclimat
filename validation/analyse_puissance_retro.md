# Analyse de puissance rétrospective des tests antérieurs

Généré le 2026-11-09 par `scripts/analyse_puissance_retro.py`. **Aucune hypothèse n'est testée** : on demande si ces tests avaient une chance réelle de conclure. Effectifs tirés des rapports publiés.

## 1. Tests du signe entre sites ou événements (seuil 5 %, unilatéral)

| Test | Unités | n | Résultat publié | Favorables nécessaires | Puissance si p = 0,6 | 0,7 | 0,8 | 0,9 |
|---|---|---|---|---|---|---|---|---|
| E1, fusion des pluies (R-35) | stations GSOD | 5 | 2 sur 5, p = 0,81 | 5 sur 5 | 8% | 17% | 33% | 59% |
| Nappes contre SPI-12, H-N1 (R-36) | sites MGMERL | 7 | 5 sur 7, p = 0,23 | 7 sur 7 | 3% | 8% | 21% | 48% |
| THMS, H-M1 (R-44) | sites de nappe | 12 | 2 sur 12 | 10 sur 12 | 8% | 25% | 56% | 89% |
| Fokontany touchés, R-02 (8 activations EMS) | événements | 8 | AUC 0,16 à 0,62 selon l'événement | 7 sur 8 | 11% | 26% | 50% | 81% |

p = probabilité qu'une unité donnée soit favorable si l'effet existe. Avec 5 stations, le test du signe exige 5 sur 5 : il ne réussit qu'environ une fois sur trois même si la fusion aide 80 % des stations.

## 2. Téléconnexions par région (R-25 : 144 tests, Benjamini-Hochberg à 10 %, 45 saisons)

| r | 5 vrais liens | 20 vrais liens | 50 vrais liens |
|---|---|---|---|
| 0.2 | 10% | 35% | 70% |
| 0.3 | 39% | 88% | 100% |
| 0.4 | 80% | 100% | 100% |
| 0.5 | 99% | 100% | 100% |

Probabilité de retenir au moins un vrai lien. Avec 144 tests, un lien modéré (r = 0,3) n'est retenu que s'il est répandu dans beaucoup de régions et de cibles.

## 3. Ce que cela change pour la rédaction

| Résultat publié | Avant | Lecture corrigée |
|---|---|---|
| E1 : fusion non démontrée | « non soutenue » | **test sans puissance** (5 stations) : ni confirmé ni réfuté ; il faut des stations DGM |
| H-N1 : SPI-12 et nappes | « non soutenue » | **puissance faible** (7 sites ; 7 sur 7 exigés) : 5 sur 7 va dans le sens attendu |
| THMS, H-M1 | « non soutenue » | 2 sur 12 : **résultat négatif réel** (10 favorables exigés ; on en est loin) |
| R-02 : fokontany touchés | AUC instable | l'unité indépendante est l'événement : **8 seulement** ; la stabilité ne peut pas être établie |
| R-25 : téléconnexions | quelques régions non prévisibles | la correction sur 144 tests ne laisse passer que des liens forts ou répandus ; les régions « non prévisibles » ne prouvent pas l'absence de lien |
| R-01 : régions touchées par un cyclone | AUC 0,84, 21 cyclones | effet fort : la puissance n'est pas en cause |

Règle (adoptée le 09/11/2026) : ces lectures corrigées remplacent « non soutenue » par « non établi, puissance insuffisante » dans la thèse, sauf pour THMS (négatif réel).

