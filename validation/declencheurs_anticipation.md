# Déclencheurs d'action anticipée — ce qu'on peut dire aujourd'hui, honnêtement

**Niveau de preuve : exploratoire (non validé comme protocole opérationnel).** Calcul sur les mêmes
données que la validation principale (`cyclones_indicateurs_par_region.csv`), mais ce n'est **pas**
un protocole d'action anticipée (AA) au sens humanitaire — il manque la pièce centrale : des données
de dégâts ou de besoins réels pour calibrer le seuil sur un coût mesuré, pas sur une simple citation
dans un rapport.

## Méthode

Un déclencheur d'action anticipée doit être une règle simple (« si X dépasse un seuil, on agit »), pas
un score composite. On a donc testé, région par région et pour chaque cyclone (13 événements,
312 paires région-événement, 37 citées touchées), deux variables prises séparément :

- **Vent** : part de la population du fokontany dans le rayon de vent publié par le JTWC
  (`cov34` = tempête tropicale ≥ 34 nœuds, `cov64` = force cyclonique ≥ 64 nœuds).
- **Pluie** : période de retour locale du cumul maximal sur 3 jours (`rp90`, 90e centile des
  fokontany de la région), calculée sur la climatologie CHIRPS 1981-aujourd'hui.

Pour chaque seuil testé, on mesure directement, sans ajustement de paramètre (donc pas de risque de
surapprentissage du seuil lui-même) : le taux de détection (POD = régions citées touchées
correctement signalées) et le taux de fausses alertes (FAR = part des signalements qui ne
correspondent à aucune région citée). Détail dans `declencheurs_anticipation.csv`.

## Résultat principal, dit franchement

**Aucun seuil testé sur une seule variable n'atteint un bon compromis POD/FAR.**

| Seuil | POD | FAR |
|---|---|---|
| Vent ≥ 34 nds sur 10 % de la population | 0,92 | 0,71 |
| Vent ≥ 64 nds (force cyclonique) sur 1 % de la population | 0,38 | 0,22 |
| Pluie 3j, retour ≥ 2 ans | 0,57 | 0,77 |
| Pluie 3j, retour ≥ 5 ans | 0,30 | 0,78 |
| Vent ≥ 34 nds/10 % **OU** pluie retour ≥ 5 ans (combiné) | 0,95 | 0,74 |

Deux familles de seuils, deux problèmes différents :

- Les seuils **sensibles** (vent ≥ 34 nds, pluie à faible période de retour) détectent presque tout
  (POD 0,9 et plus) mais déclenchent une fausse alerte dans environ 7 signalements sur 10 : on
  retrouve ici exactement les limites déjà connues du modèle complet (AUC 0,83) — le vent ou la pluie
  seuls touchent une grande partie du territoire à chaque cyclone, sans que la région soit forcément
  citée comme sinistrée dans les rapports.
- Les seuils **stricts** (vent de force cyclonique) ont moins de fausses alertes (FAR ~0,22-0,30) mais
  ratent la majorité des régions citées (POD 0,16-0,38) : la plupart des impacts cités dans les
  rapports ne correspondent pas à un passage à pleine force cyclonique sur la région entière.

**Le FAR affiché est probablement surestimé**, pas sous-estimé : une région non citée dans un rapport
n'est pas forcément épargnée (listes de régions touchées souvent incomplètes, surtout pour les
cyclones les plus anciens — voir `evenements_historiques_note.md`). Mais même avec cette réserve,
l'écart entre POD et FAR reste trop grand pour qu'un seul seuil physique serve de déclencheur fiable.

## Ce que ça veut dire pour MakyClimat

1. **Pas de seuil « officiel » publié sur le site pour l'instant.** Publier un déclencheur avec un FAR
   de 70 % donnerait l'impression d'un système d'alerte précoce opérationnel alors que ce n'est pas le
   cas : ce serait moins honnête que de ne rien publier.
2. **Le modèle combiné (AUC 0,83, régression logistique vent+pluie) reste la meilleure option
   disponible**, mais ses probabilités ne sont pas calibrées non plus (déjà noté dans le tableau de
   confiance du site) — il sert à classer les régions les plus probablement touchées, pas à décider
   seul d'un déclenchement.
3. **Pour un vrai protocole d'action anticipée (type CERF/START Network), il manque la pièce
   centrale : une mesure de dégât ou de besoin réel** (pas juste « citée dans un rapport ») pour
   calibrer le seuil sur un coût humain, avec une analyse coûts-bénéfices propre à l'action anticipée
   (combien coûte une fausse alerte en ressources mobilisées pour rien, combien coûte un retard
   d'action en vies ou en moyens de subsistance perdus). C'est un travail que le BNGRC et les
   partenaires humanitaires sont mieux placés pour faire, avec leurs propres contraintes
   opérationnelles — MakyClimat peut fournir les indicateurs d'exposition (vent, pluie, période de
   retour) en entrée de ce travail, pas décider du seuil à leur place.

## Pour aller plus loin

- Demander au BNGRC/aux partenaires humanitaires des données de dégâts ou de déclenchements passés
  (même approximatives) pour recalibrer sur un impact réel plutôt que sur « citée dans un rapport ».
- Si un protocole existe déjà (CERF anticipatory action, ou autre), comparer ses seuils à nos
  variables (`cov34`, `cov64`, `rp90`) pour voir s'ils coïncident avec une zone de bon compromis
  POD/FAR dans nos données.
- Étendre l'exercice à la sécheresse (SPI) une fois que des données d'impact comparables existeront.
