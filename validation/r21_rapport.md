# R-21 — Rapport de clôture : les prévisions d'ensemble GloFAS anticipent-elles les impacts de crue à Madagascar ?

*Rédigé le 12/11/2026 après les scores. Pièces : [protocole](protocole_verification_impact.md) (section 9 pour
toutes les modifications datées), [fiche de méthode](r21_fiche_methode.md), [éligibilité](r21_eligibilite.md),
[puissance](r21_puissance.md), [sensibilité sur jours témoins](r21_cci_temoins.md), [scores](r21_scores.md).*

## 1. Question et contexte

Dans un pays sans série de débit publique, les probabilités d'ensemble de GloFAS v4 anticipent-elles les impacts de
crue déclarés au niveau du district ? Aucune évaluation de GloFAS publiée pour Madagascar n'a été trouvée (recherche
du 29/10/2026) ; les travaux proches (Mitheu et al. 2025 ; Kuipers et al. 2026) s'appuient sur des stations
hydrométriques. Ici, la vérification repose uniquement sur les impacts (DesInventar).

## 2. Ce qui a été décidé avant les scores

| Date | Décision | Par |
|---|---|---|
| 29/10 | Protocole écrit avant tout calcul | Claude |
| 09/11 | Portée réduite : décembre-mars des années à événement, plus les mois déjà téléchargés ; biais d'échantillon enrichi déclaré ; verrou des scores | Porteur, après l'audit de Codex |
| 10/11 | Critère principal de H1 : **gain de détection à 1-3 jours de l'ensemble sur le contrôle, à charge d'alerte comparable** ; AUC secondaire ; Brier, fiabilité, valeur économique descriptifs | Porteur |
| 11/11 | Méthode figée (seuils par blocs mensuels, unités épisode × district, test par permutation des signes par saison) ; gain pertinent 30 points ; lot de 7 mois autorisé | Claude, relu sans blocage par Codex ; porteur |
| 11/11 | Mars 2015 indisponible chez ECMWF (bande endommagée) : population finale 425 unités, 22 épisodes, 12 saisons | Constat |
| 12/11 | Sensibilité : CCI des différences sur jours témoins 0,045 [0,035 ; 0,054] ; transportabilité aux épisodes non démontrée | Claude, relu sans blocage |
| 12/11 | **H1 exploratoire**, avant les scores | Porteur |

## 3. Résultat principal

Détails et tableau par saison : [r21_scores.md](r21_scores.md) ; calcul `scripts/r21_scores.py` (commit `d7e5611`,
relu sans blocage par Codex le 12/11).

- Charge comparable selon la tolérance prévue, sur l'apprentissage de chacun des 12 plis (écart −2 à −4 %, tolérance
  ± 20 %) ; les charges en test diffèrent et sont publiées par pli dans [r21_scores.md](r21_scores.md).
- Détection 1 à 3 jours avant, sur 425 unités épisode × district :
  **ensemble 16,0 %** [7,0 ; 26,8], **contrôle 14,8 %** [6,6 ; 25,5], **écart 1,2 point** [−1,0 ; 2,5]
  (intervalles à 95 %, bootstrap des saisons).
- Discordances : 8 unités détectées par l'ensemble seul, 3 par le contrôle seul.
- Test A (permutation exacte des signes, 4 096 combinaisons, unilatéral) : **p = 0,31**.

**Conclusion (exploratoire) : à charge comparable sur l'apprentissage, aucun gain de détection de l'ensemble GloFAS v4
sur son scénario de contrôle n'est mis en évidence pour les impacts de crue déclarés par district, 1 à 3 jours avant ;
H1 n'est pas soutenue.** Ce n'est pas une preuve d'absence de gain. La borne supérieure de l'intervalle bootstrap
estimé de l'écart (2,5 points, sous ses hypothèses : saisons indépendantes, échantillon de cette portée) reste très
loin des 30 points jugés pertinents.

## 4. Ce que le résultat apprend

1. **Les deux méthodes détectent peu** : environ 15 % des districts touchés, et aucune détection dans 5 saisons sur
   12. À cette résolution et avec des seuils de période de retour de 2 ans, GloFAS ne repère pas la plupart des
   impacts déclarés, avec ou sans ensemble. Plusieurs causes plausibles, non séparées ici : inondations pluviales
   ou côtières hors du réseau de rivières de GloFAS (28 unités sans maille de rivière retenue), impacts cycloniques
   dus au vent, déclarations groupées par district, dates de fiche imprécises.
2. **Peu de différences entre les deux méthodes à charge comparable** : l'information du test tient dans 11
   discordances.
3. **Les hypothèses de puissance ne correspondaient pas aux données** : la simulation supposait une détection du
   contrôle de 40 % ; observée : 14,8 %. Les puissances simulées ne sont pas transposables aux résultats, et la
   puissance pour un autre gain n'a pas été évaluée. La CCI observée sur les épisodes (0,065) est, elle, proche de
   celle des témoins (0,045).
4. Résultat cohérent avec R-23 (l'intensité IMERG ne repère pas les jours d'inondation) et avec le pilote GloFAS
   (un événement sur trois en vigilance, aucun en alerte, audit du 09/11) : **à Madagascar, les produits mondiaux
   repèrent mal les impacts déclarés à l'échelle du district.**

## 5. Limites

- Statut exploratoire ; 22 épisodes, 12 saisons ; échantillon enrichi en événements (portée réduite).
- Une absence de fiche n'est pas une absence d'impact : la charge est mesurée sur des jours sans impact confirmé.
- Seuils estimés sur des saisons partielles ; blocs mensuels non indépendants (persistance des débits).
- Mars 2015 indisponible chez ECMWF (15 unités exclues).
- **Écart déclaré au protocole** : les analyses secondaires (AUC, Brier, fiabilité, valeur économique), prévues comme
  descriptives, ne sont pas calculées à cette clôture. Elles reposeraient sur les mêmes 425 unités à détection très
  faible, et l'ancien script (`validate_reforecast_impact.py`) n'est pas aligné sur la population figée ; il reste
  verrouillé. Les calculer demanderait une décision du porteur.

## 6. Suites possibles (aucune engagée)

Toute suite serait un nouveau protocole déclaré avant calcul, de préférence confirmatoire :
- unité plus fine que le district (commune, maille du cours d'eau touché), pour réduire le bruit des déclarations ;
- impacts d'inondation fluviale seulement (hors vent cyclonique et inondations pluviales) ;
- autres saisons (hors portée réduite) ou autre pays avec stations, pour séparer la compétence hydrologique de la
  qualité des déclarations.

Pour la thèse, ce chapitre apporte un **résultat négatif documenté et reproductible** : protocole figé avant calcul,
décisions datées, puissance calculée avant les scores, statut fixé avant les résultats.
