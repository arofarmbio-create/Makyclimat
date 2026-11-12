# R-21 — CCI des différences estimée sur jours témoins (analyse de sensibilité, avant scores)

Calcul du 12/11/2026 par [`scripts/r21_cci_temoins.py`](../scripts/r21_cci_temoins.py), 59 mois GloFAS v4, 51 blocs mensuels décembre-mars, 22 groupes de districts d'épisodes éligibles. Méthode : [fiche, section 5](r21_fiche_methode.md). **Aucune unité d'impact n'est lue** (DesInventar lu sur quatre colonnes : type, date, district, date douteuse) **; le verrou des scores est maintenu.** Détail par pli : [`r21_cci_temoins.csv`](r21_cci_temoins.csv).

## Résultat

- **CCI des différences : 0,045**, intervalle à 95 % par bootstrap des saisons (2000 tirages) : **0,035 à 0,054** ; borne haute + 0,10 : 0,154.
- Seuil de 80 % de puissance (population finale, 30 points) : CCI ≤ 0,46. Borne haute sous ce seuil ; borne haute + 0,10 sous ce seuil.
- Puissance du test A ([grille simulée](r21_puissance.md), population finale, gain de 30 points), interpolation linéaire entre scénarios d'un même τ ; une valeur hors de la grille n'a pas de puissance directement évaluée et seul le scénario simulé le plus proche est cité :
  - borne haute 0,054 : τ = 0,0 : hors grille, sous la plus petite CCI simulée (0,12 : 99,8 %) ; τ = 0,1 : hors grille, sous la plus petite CCI simulée (0,14 : 99,2 %) ; τ = 0,2 : hors grille, sous la plus petite CCI simulée (0,19 : 96,4 %) ;
  - borne haute + 0,10 = 0,154 : τ = 0,0 : 98,8 % (entre 0,12 et 0,26) ; τ = 0,1 : 98,6 % (entre 0,14 et 0,28) ; τ = 0,2 : hors grille, sous la plus petite CCI simulée (0,19 : 96,4 %).
- Jours-groupes retenus : 4782 (taille médiane 21 districts, de 2 à 76) ; part médiane de districts où les méthodes diffèrent : 0%, part moyenne 5.4% (toutes unités : 4.1%). Les discordances sont rares sur témoins ; la simulation de puissance suppose un gain de 30 points sur les épisodes, donc bien plus de discordances.
- Plis hors tolérance de charge (± 20%) : 0 sur 14.

**Réserves.** Transportabilité non démontrée (relecture Codex du 11/11, 14:37) : la CCI des jours témoins peut différer de celle des épisodes d'impact. Les jours-groupes consécutifs se recouvrent (mêmes initialisations, groupes qui partagent des districts) : l'estimation ponctuelle les pondère tous. Le bootstrap rééchantillonne des saisons entières : il préserve les dépendances au sein de chaque saison et suppose les saisons indépendantes entre elles. H1 reste exploratoire par défaut ; le porteur décide du statut avant les scores.

## Plis (saison testée)

| Saison | pi | Charge cible | Charge ensemble (app.) | Écart | Contrôle (test) | Ensemble (test) | Jours-districts témoins | Jours-groupes |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2003 | 0.38 | 1.008 | 0.989 | -2% | 1.001 | 1.086 | 10494 | 427 |
| 2004 | 0.38 | 0.972 | 0.943 | -3% | 0.798 | 0.798 | 13912 | 534 |
| 2005 | 0.38 | 1.01 | 0.984 | -3% | 0.264 | 0.207 | 14036 | 220 |
| 2006 | 0.38 | 0.945 | 0.91 | -4% | 2.716 | 2.654 | 9572 | 922 |
| 2007 | 0.38 | 1.008 | 0.978 | -3% | 0.976 | 0.93 | 8814 | 278 |
| 2008 | 0.38 | 0.945 | 0.926 | -2% | 1.291 | 1.086 | 6816 | 312 |
| 2009 | 0.38 | 0.966 | 0.944 | -2% | 1.155 | 1.144 | 9437 | 458 |
| 2010 | 0.38 | 0.979 | 0.958 | -2% | 0.932 | 0.922 | 9656 | 298 |
| 2011 | 0.38 | 0.935 | 0.908 | -3% | 1.741 | 1.718 | 8787 | 464 |
| 2012 | 0.38 | 0.969 | 0.946 | -2% | 0.72 | 0.659 | 13198 | 346 |
| 2013 | 0.38 | 0.993 | 0.976 | -2% | 0.115 | 0.086 | 6944 | 48 |
| 2014 | 0.38 | 0.963 | 0.935 | -3% | 2.468 | 2.338 | 1540 | 144 |
| 2015 | 0.38 | 0.963 | 0.94 | -2% | 1.243 | 1.087 | 3219 | 219 |
| 2016 | 0.38 | 1.008 | 0.982 | -3% | 0.483 | 0.528 | 8704 | 112 |

Charges : épisodes d'alerte pour 100 jours-districts témoins (district avec maille de rivière).
