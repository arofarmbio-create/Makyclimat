# Analyse de puissance : T2 contre T2L, dépôt de chlorure mesuré, blocs neufs (T-H2.1)

Générée par `scripts/puissance_chlorure_independant.py` (2000 tirages par case, graine 20261116), selon `validation/protocole_chlorure_independant.md`. **Planification seulement** : aucune donnée du test n'existe ; les 33 blocs de R-50 dans le domaine T2L (déjà vus, après coup) servent de vraisemblance.

- **H-I1 (niveau)** : test du signe unilatéral sur log₁₀(T2 / R), p < 0,05, dépôt mesuré × 1,5.
- **H-I2 (structure)** : écart centré c = |e − médiane(e)| ; Wilcoxon apparié unilatéral sur c(T2) − c(T2L), p < 0,05, **et** médiane de c réduite d'au moins 30 %. Invariant à une erreur uniforme du dépôt.
- σ_e : bruit propre à chaque bloc (médiane d'au moins 3 forages, forme du dépôt) ; σ_u = 0,1 : erreur commune du dépôt mesuré (log₁₀).

## 1. La référence échoue-t-elle sur les données déjà vues ?

« T2 décalé » = T2 × 0.19 : même niveau médian que T2L, structure de T2. Avec le critère des écarts absolus (premier jet abandonné), T2 décalé battait T2 dans les scénarios bas et central : ce critère testait le niveau, pas la correction par roche. H-I2 retire le niveau.

| Scénario R-50 | H-I1 : T2 surestime (dépôt × 1,5) | H-I2 : T2L contre T2 (p ; réduction) | H-I2 : T2 décalé contre T2 (p ; réduction) |
|---|---|---|---|
| bas | oui | non (0.999 ; -59 %) | non (1.000 ; +0 %) |
| central | oui | non (0.999 ; -55 %) | non (1.000 ; +0 %) |
| haut | non | non (0.999 ; -39 %) | non (1.000 ; +0 %) |

## 2. Blocs neufs possibles (plafond)

Blocs de 20 km de la grille fixe couverts au moins à moitié par le domaine T2L (où T2L ≠ T2) : 229 ; à au moins 20 km de tout bloc R-50 : **189** (autres : 67, socle : 122). Plafond géométrique : un bloc ne compte que s'il reçoit au moins 3 forages neufs valides.

## 3. Puissance de H-I1 (niveau)

| Vérité supposée | σ_e | n = 6 | n = 8 | n = 10 | n = 12 | n = 15 | n = 18 | n = 24 | n = 30 |
|---|---|---|---|---|---|---|---|---|---|
| blocs R-50, bas | 0.1 | 98 % | 100 % | 100 % | 100 % | 100 % | 100 % | 100 % | 100 % |
| blocs R-50, bas | 0.2 | 93 % | 99 % | 99 % | 100 % | 100 % | 100 % | 100 % | 100 % |
| blocs R-50, bas | 0.3 | 84 % | 98 % | 96 % | 100 % | 100 % | 100 % | 100 % | 100 % |
| blocs R-50, central | 0.1 | 73 % | 91 % | 89 % | 96 % | 98 % | 100 % | 100 % | 100 % |
| blocs R-50, central | 0.2 | 67 % | 88 % | 82 % | 92 % | 97 % | 99 % | 100 % | 100 % |
| blocs R-50, central | 0.3 | 55 % | 80 % | 75 % | 88 % | 93 % | 98 % | 99 % | 100 % |
| blocs R-50, haut | 0.1 | 1 % | 2 % | 0 % | 1 % | 1 % | 2 % | 2 % | 2 % |
| blocs R-50, haut | 0.2 | 1 % | 2 % | 1 % | 1 % | 1 % | 3 % | 1 % | 3 % |
| blocs R-50, haut | 0.3 | 0 % | 3 % | 0 % | 1 % | 2 % | 3 % | 2 % | 3 % |
| paramétrique, structure 0 % | 0.1 | 72 % | 91 % | 88 % | 95 % | 97 % | 100 % | 100 % | 100 % |
| paramétrique, structure 0 % | 0.2 | 65 % | 89 % | 84 % | 93 % | 96 % | 99 % | 100 % | 100 % |
| paramétrique, structure 0 % | 0.3 | 55 % | 81 % | 73 % | 89 % | 94 % | 98 % | 99 % | 100 % |
| paramétrique, structure 30 % | 0.1 | 73 % | 92 % | 89 % | 96 % | 98 % | 100 % | 100 % | 100 % |
| paramétrique, structure 30 % | 0.2 | 67 % | 87 % | 84 % | 93 % | 96 % | 99 % | 100 % | 100 % |
| paramétrique, structure 30 % | 0.3 | 56 % | 81 % | 75 % | 87 % | 92 % | 99 % | 99 % | 100 % |
| paramétrique, structure 50 % | 0.1 | 71 % | 92 % | 89 % | 95 % | 98 % | 100 % | 100 % | 100 % |
| paramétrique, structure 50 % | 0.2 | 66 % | 87 % | 83 % | 92 % | 96 % | 99 % | 100 % | 100 % |
| paramétrique, structure 50 % | 0.3 | 56 % | 81 % | 75 % | 88 % | 93 % | 99 % | 99 % | 100 % |

## 4. Puissance de H-I2 (structure)

| Vérité supposée | σ_e | n = 6 | n = 8 | n = 10 | n = 12 | n = 15 | n = 18 | n = 24 | n = 30 |
|---|---|---|---|---|---|---|---|---|---|
| blocs R-50, bas | 0.1 | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % |
| blocs R-50, bas | 0.2 | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % |
| blocs R-50, bas | 0.3 | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % |
| blocs R-50, central | 0.1 | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % |
| blocs R-50, central | 0.2 | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % |
| blocs R-50, central | 0.3 | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % |
| blocs R-50, haut | 0.1 | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % |
| blocs R-50, haut | 0.2 | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % |
| blocs R-50, haut | 0.3 | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % |
| paramétrique, structure 0 % | 0.1 | 1 % | 1 % | 1 % | 1 % | 1 % | 1 % | 0 % | 0 % |
| paramétrique, structure 0 % | 0.2 | 2 % | 1 % | 1 % | 1 % | 0 % | 0 % | 0 % | 0 % |
| paramétrique, structure 0 % | 0.3 | 1 % | 1 % | 1 % | 0 % | 0 % | 0 % | 0 % | 0 % |
| paramétrique, structure 30 % | 0.1 | 15 % | 16 % | 18 % | 21 % | 26 % | 30 % | 33 % | 35 % |
| paramétrique, structure 30 % | 0.2 | 12 % | 12 % | 16 % | 19 % | 19 % | 23 % | 24 % | 26 % |
| paramétrique, structure 30 % | 0.3 | 11 % | 10 % | 11 % | 14 % | 16 % | 16 % | 15 % | 17 % |
| paramétrique, structure 50 % | 0.1 | 28 % | 35 % | 43 % | 54 % | 59 % | 70 % | 76 % | 82 % |
| paramétrique, structure 50 % | 0.2 | 23 % | 27 % | 35 % | 40 % | 47 % | 57 % | 62 % | 67 % |
| paramétrique, structure 50 % | 0.3 | 18 % | 19 % | 24 % | 29 % | 31 % | 38 % | 41 % | 45 % |

Lecture : pour H-I2, « structure 0 % » donne le taux de faux positifs (T2L n'apporte que son niveau) ; pour H-I1, la ligne « haut » est proche de l'absence d'effet.
