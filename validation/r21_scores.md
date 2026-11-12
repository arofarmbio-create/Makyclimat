# R-21 — Scores de H1 (exploratoire)

Calcul du 12/11/2026 par [`scripts/r21_scores.py`](../scripts/r21_scores.py), méthode figée de la [fiche](r21_fiche_methode.md) (sections 2 à 5), sans paramètre nouveau. **Statut : exploratoire**, décidé par le porteur du projet le 12/11/2026 avant les scores ; il ne change pas au vu des résultats. Un résultat net appelle un test confirmatoire déclaré d'avance sur des données indépendantes (autres saisons ou pays). 59 mois GloFAS v4, 51 blocs mensuels. Détail : [plis](r21_scores_plis.csv), [unités](r21_scores_unites.csv).

## Résultat

- Population figée : 425 unités épisode × district, 22 épisodes, 12 saisons ; 28 unités sans maille de rivière retenue (non détectables par les deux méthodes).
- Détection 1 à 3 jours avant : **ensemble 16,0 %** (68), **contrôle 14,8 %** (63) ; écart 1,2 points. Discordances : ensemble seul 8, contrôle seul 3.
- **Test A** (permutation exacte des signes sur 12 saisons, 4096 combinaisons, unilatéral) : T = 0,39, **p = 0,3125** ; au seuil de 0,05 : pas de gain de l’ensemble mis en évidence.
- Plis hors tolérance de charge (± 20 %) : 0 sur 12.
- CCI des différences observée sur les épisodes (section 5, point 3) : 0,065 ; puissance pour un gain de 30 points : τ = 0,0 : hors grille, sous la plus petite CCI simulée (0,12 : 99,8 %) ; τ = 0,1 : hors grille, sous la plus petite CCI simulée (0,14 : 99,2 %) ; τ = 0,2 : hors grille, sous la plus petite CCI simulée (0,19 : 96,4 %).

**Lecture des hypothèses de puissance.** La simulation supposait une détection moyenne du contrôle de 40 % et un gain de 30 points. Observé : contrôle 14,8 %, et 11 unités discordantes seulement : l'information du test tient dans ces discordances. Les repères de puissance ci-dessus, conditionnels à ces hypothèses, surestiment donc la puissance réelle pour un gain plausible à ce niveau de détection ; l'absence de gain démontré n'est pas une preuve d'absence de gain. La détection est nulle pour les deux méthodes dans 5 saisons sur 12.

**Réserves.** Statut exploratoire (transportabilité de la CCI des témoins non démontrée). Une absence de fiche n'est pas une absence d'impact : la charge est mesurée sur des jours sans impact confirmé. Échantillon enrichi en événements (décembre-mars des saisons à fiches) ; 22 épisodes seulement.

## Plis (saison testée)

| Saison | Unités | Épisodes | pi | Charge cible | Écart (app.) | Charge contrôle (test) | Charge ensemble (test) | Ensemble | Contrôle | Ensemble seul | Contrôle seul |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2003 | 120 | 2 | 0,38 | 1,01 | -2 % | 1,00 | 1,09 | 14 | 11 | 3 | 0 |
| 2004 | 4 | 2 | 0,38 | 0,97 | -3 % | 0,80 | 0,80 | 0 | 0 | 0 | 0 |
| 2006 | 24 | 2 | 0,38 | 0,94 | -4 % | 2,72 | 2,65 | 0 | 0 | 0 | 0 |
| 2007 | 63 | 3 | 0,38 | 1,01 | -3 % | 0,98 | 0,93 | 25 | 22 | 3 | 0 |
| 2009 | 24 | 2 | 0,38 | 0,97 | -2 % | 1,16 | 1,14 | 6 | 8 | 1 | 3 |
| 2010 | 21 | 2 | 0,38 | 0,98 | -2 % | 0,93 | 0,92 | 2 | 2 | 0 | 0 |
| 2011 | 41 | 1 | 0,38 | 0,94 | -3 % | 1,74 | 1,72 | 0 | 0 | 0 | 0 |
| 2012 | 18 | 3 | 0,38 | 0,97 | -2 % | 0,72 | 0,66 | 0 | 0 | 0 | 0 |
| 2013 | 6 | 1 | 0,38 | 0,99 | -2 % | 0,12 | 0,09 | 3 | 3 | 0 | 0 |
| 2014 | 49 | 2 | 0,38 | 0,96 | -3 % | 2,47 | 2,34 | 14 | 13 | 1 | 0 |
| 2015 | 4 | 1 | 0,38 | 0,96 | -2 % | 1,24 | 1,09 | 4 | 4 | 0 | 0 |
| 2016 | 51 | 1 | 0,38 | 1,01 | -3 % | 0,48 | 0,53 | 0 | 0 | 0 | 0 |

Charges : épisodes d'alerte pour 100 jours-districts témoins (district avec maille de rivière).
