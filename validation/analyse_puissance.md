# Analyse de puissance des tests de la recharge

Généré le 2026-11-09 par `scripts/analyse_puissance.py`. **Aucune hypothèse n'est testée ici** : on estime combien d'unités indépendantes il faudrait pour détecter un effet plausible, à partir de résultats déjà publiés. Seuil 5 % bilatéral, puissance visée 80 %, 4000 simulations par cas (graine 20261109).

## 1. Correction locale par classe d'aquifère (type H-L1)

Paramètres tirés des sites du socle, un résidu par groupe de sites indépendants (6 groupes) : résidu médian log₁₀(mesurée / T2) = -0.73 (T2 trop forte d'un facteur 5.3), dispersion entre groupes 0.53, demi-largeur médiane de l'intervalle de mesure (rendement spécifique) 0.29.

| Groupes indépendants par classe | Puissance de la règle (dispersion observée) | Si la dispersion était moitié moindre |
|---|---|---|
| 3 | 18% | 56% |
| 4 | 42% | 82% |
| 6 | 39% | 85% |
| 8 | 37% | 90% |
| 10 | 35% | 93% |
| 15 | 24% | 95% |
| 20 | 27% | 98% |
| 30 | 23% | 100% |

Lecture : avec 6 groupes dans le socle aujourd'hui, la règle réussit rarement même si la correction est juste. Même 30 groupes ne suffisent pas avec la dispersion observée : la règle « moitié des sites retrouvés » est trop exigeante tant que la dispersion entre sites dépasse la largeur de l'intervalle de mesure ; il faut réduire l'incertitude des mesures (rendement spécifique) ou expliquer la dispersion (géologie plus fine).

## 2. Différence d'AUC entre deux cartes (puits à sec)

Observé : T2L − T2 = +0.111, intervalle -0.004 à +0.227 avec 120 blocs, soit une erreur type de 0.059.

| Différence à détecter | Puissance avec les blocs actuels | Blocs nécessaires (80 %) |
|---|---|---|
| 0.05 | 13% | 1308 |
| 0.08 | 27% | 511 |
| 0.11 | 46% | 270 |

Lecture : le gain observé (+0,11) avait environ une chance sur deux d'être déclaré ; une différence de 0,05 (seuil du protocole) demande plusieurs fois plus de blocs que le Grand Sud n'en compte. Le test des puits à sec ne peut départager les cartes que si l'effet est grand, ou en étendant la zone.

## 3. Corrélation de Spearman entre blocs (bilan de chlorure)

Blocs disponibles : 36.

| ρ à détecter | Puissance avec les blocs actuels | Blocs nécessaires (80 %) |
|---|---|---|
| 0.2 | 21% | 194 |
| 0.3 | 43% | 85 |
| 0.4 | 68% | 47 |
| 0.5 | 88% | 29 |

Lecture : avec 36 blocs, seule une corrélation forte (au moins 0,45) est détectable de façon fiable ; la règle H-Cl1 (ρ ≥ 0,3 dans les trois scénarios) était presque impossible à remplir.

## 4. Test prospectif des cartes figées (« au moins 60 % des nouveaux sites retrouvés »)

| Vraie part de sites retrouvés | Nouveaux sites indépendants nécessaires pour que la borne basse dépasse 60 % (80 %) |
|---|---|
| 70% | 177 |
| 75% | 76 |
| 80% | 41 |
| 90% | 14 |

Lecture : pour qu'un test prospectif soit concluant, il faut des dizaines de sites indépendants, sauf si la carte est très bonne. Les règles actuelles (« au moins 60 % ») sont donc trop faibles en petit nombre : à remplacer par la borne basse d'un intervalle, comme ci-dessus.

## Conséquences

1. **Nos « non soutenus de peu » sont surtout des manques de puissance** (sections 2 et 3) : ils ne réfutent pas les idées.
2. **La correction locale bute d'abord sur la dispersion entre sites** (section 1) : plus de sites ne suffit pas, il faut aussi réduire l'incertitude de mesure (essais de pompage pour le rendement spécifique) et classer les roches plus finement.
3. **Plan de mesures** : viser par classe d'aquifère le nombre de groupes indépendants de la section 1, et pour un test prospectif le nombre de sites de la section 4.
4. **Règle de méthode** (à appliquer aux prochains protocoles) : calculer la puissance avant de fixer une hypothèse ; si elle est inférieure à 50 %, le test est déclaré exploratoire dès le départ.

