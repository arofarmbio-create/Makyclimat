# H-C2 : modèle hybride de profondeur de l'eau contre la carte mondiale et le krigeage

Généré le 2026-11-02 par `scripts/validate_nappes_hc2.py`, selon `validation/protocole_carte_nappes.md` (précisions du 02/11/2026, fixées avant le calcul). Forages : MGMERL (999 points) ; carte mondiale : Fan et al. (2017), valeurs non republiées.

Validation par blocs de 1° (au moins 5 forages) : 25 blocs, chacun prédit sans aucun de ses forages.

| Méthode | Erreur absolue médiane entre blocs (m) | Blocs où l'hybride fait mieux | p (signe) |
|---|---|---|---|
| Carte de Fan seule | 6.4 | 23 sur 25 | 0.000 |
| Krigeage des mesures | 3.1 | 16 sur 25 | 0.115 |
| **Modèle hybride** | **2.8** | — | — |

Couverture médiane de l'intervalle de 80 % de l'hybride : 76% (attendu : 80 %).

**H-C2 non confirmée** (l'hybride doit battre les deux références, p < 0,05 chacune).

Limites : forages regroupés autour des projets, surtout dans le Sud ; pas de carte des failles ; niveau statique ponctuel ; le modèle prédit le niveau de l'eau dans un forage, pas la profondeur à forer.
