# R-21 bis — Diagnostic de la faible détection : rapport

*13/11/2026, 01:30 (Nairobi). Rédigé par Claude pendant la délégation du porteur du projet (12-13/11). Statut :
**exploratoire**, comme le protocole ([protocole](protocole_r21_diagnostic.md), 7e version `c60baf1`, relu sans
blocage par le relecteur attitré le 12/11 à 21:43). Version corrigée le 13/11 à 05:55 après la relecture
attitrée du rapport (01:14) : causes présentées comme non établies ; test EMS présenté comme une dérogation. Calcul : run GitHub `43282884932` (6e tentative, après une
indisponibilité de DesInventar), code [`scripts/r21_diagnostic.py`](../scripts/r21_diagnostic.py). Sorties
complètes : [r21_diagnostic.md](r21_diagnostic.md) et les fichiers `r21_diagnostic_*.csv`.*

## 1. Question

R-21 a trouvé une détection faible des impacts d'inondation par les prévisions GloFAS (contrôle 14,8 %, ensemble
16,0 %, 425 unités épisode × district). Cette faiblesse vient-elle de la **prévision** (C), ou de la
**détectabilité** des impacts par le modèle hydrologique, même avec la météo observée (A : observation des impacts ;
B : impacts non fluviaux ou mal localisés ; erreur du modèle hydrologique) ?

## 2. Contrôle de cohérence

Le contrôle et l'ensemble recalculés redonnent exactement les taux de R-21 (14,8 % et 16,0 % sur 425 unités) :
le diagnostic part bien de la même base. Aucun pli hors tolérance de charge (0 sur 12, districts et bassins).

## 3. Résultat principal (D2, règle fixée avant calcul)

| Unités | n | Contrôle P_c | Ensemble | Réanalyse P | Écart P − P_c, IC 95 % |
|---|---|---|---|---|---|
| Épisode × district | 425 | 14,8 % | 16,0 % | **14,6 %** | [−6,0 ; +7,0] pts |
| Sans les 28 unités sans rivière | 397 | 15,9 % | 17,1 % | 15,6 % | [−6,3 ; +7,6] pts |
| Épisode × bassin (rattachement à 20 %) | 275 | 18,9 % | 20,0 % | 18,5 % | [−8,6 ; +7,6] pts |
| Épisode × bassin (tout recoupement) | 565 | 18,6 % | 17,9 % | 15,8 % | [−8,7 ; +3,9] pts |

Intervalles : bootstrap des saisons (2 000 tirages). Sensibilités : à ± 1 jour, contrôle et réanalyse 24,2 %,
ensemble 24,7 % ; seuil de réanalyse non ajusté (k = 1), réanalyse 13,6 %.

**Lecture selon la règle du protocole : P = 14,6 % ≤ 25 % → « référence basse ».** Même avec la météo observée,
le modèle GloFAS ne repère pas plus d'impacts que la prévision. Hypothèses privilégiées : (A), erreur du modèle
hydrologique, ou (B). L'hypothèse (C), une perte de compétence de la prévision, n'est **pas** privilégiée : P ne
dépasse pas P_c. Le passage au bassin hydrologique ne change pas la lecture.

Conséquence pour R-21 : son résultat se lit **« peu informatif sur la compétence de prévision »** plutôt que
« GloFAS sans compétence ». La plupart des unités ne sont pas détectées par la réanalyse dans les conditions
évaluées (modèle, seuils, dates des fiches) ; les causes restent indéterminées.

## 4. Contexte cyclonique (D4, descriptif)

Distance minimale entre le centre démographique du district et une position IBTrACS à 6 h, pendant l'épisode :

| Distance au cyclone | n | Contrôle | Ensemble | Réanalyse |
|---|---|---|---|---|
| < 100 km | 47 | 44,7 % | 51,1 % | 31,9 % |
| 100–300 km | 80 | 23,8 % | 25,0 % | 23,8 % |
| > 300 km | 279 | 5,4 % | 5,7 % | 7,9 % |
| aucun cyclone dans l'emprise | 19 | 42,1 % | 42,1 % | 31,6 % |

La détection dépend fortement du contexte. Près d'un cyclone, près de la moitié des unités sont détectées. Loin
de tout cyclone, ce sont les deux tiers de l'échantillon (279 sur 425), et la détection tombe à 5-8 %, **réanalyse
comprise**. Pistes possibles, non établies par ce diagnostic : pluies locales, ruissellement ou crues de petits
bassins sous la résolution de GloFAS, dates ou lieux imprécis dans les fiches, erreur du modèle ou des seuils. Ce
tableau est descriptif ; il n'a pas de règle de lecture propre (protocole, section 7).

## 5. Limites

- Référence **conditionnelle** au modèle LISFLOOD et aux seuils de Gumbel ; ce n'est pas une borne supérieure.
- Exploratoire : aucune conclusion causale ; les classes (A), (B) et erreur hydrologique ne sont pas séparées ici.
- Le croisement des classes D1 (table 6 × 6) et la comparaison par épisode (D3) sont publiés dans les sorties
  complètes, sans lecture supplémentaire.
- CHIRPS différé ; observations Copernicus EMS non utilisées (réservées au test confirmatoire).

## 6. Suite proposée (à décider par le porteur)

1. **Test par sous-bassin avec les observations EMS** : *nouvelle proposition*. La section 8 du protocole ne
   l'engageait que si la référence dépassait 25 %, condition non remplie (14,6 %). Elle y dérogerait donc et doit
   être décidée par le porteur avant tout calcul. Des impacts cartographiés indépendamment des fiches aideraient à
   départager (A) et (B), sans garantir cette séparation.
2. **Restreindre la vérification par l'impact aux épisodes cycloniques** (< 300 km), où GloFAS « voit » les impacts.
   Toute hypothèse sur ce sous-ensemble doit être déclarée **avant** un nouveau calcul ; les chiffres ci-dessus ne
   peuvent pas servir à la fixer.
3. Pour la thèse : ce diagnostic montre qu'une vérification par l'impact sans station hydrométrique doit d'abord
   établir la détectabilité hydrologique des impacts, avant de juger la prévision. C'est un apport de méthode
   transférable.
