# SPEI : ce qu'on peut vraiment faire sans série d'évapotranspiration historique

**Niveau de preuve : exploratoire.** Section 6B du cahier des charges scientifique demande un indice
combinant précipitation et évapotranspiration (SPEI). Ce document explique honnêtement pourquoi
MakyClimat n'a **pas** de vrai SPEI, ce qu'on a testé à la place avec les données déjà disponibles, et
ce que ça donne sur le seul épisode de sécheresse documenté (même vérité terrain que
`secheresse_pod_far.md`).

## Pourquoi pas un vrai SPEI

Un SPEI correct (Vicente-Serrano et al. 2010) a besoin d'une série pluie moins évapotranspiration
**qui varie chaque mois de chaque année**, ajustée par une loi log-logistique à 3 paramètres (parce
que P − ETP peut être négatif, contrairement à la pluie seule qui va dans la loi gamma du SPI).

MakyClimat ne dispose que d'une **climatologie d'évapotranspiration fixe** (`build_soilwater.py`,
ET0_YEARS = 2016-2020) : 12 valeurs mensuelles moyennes par point de grille, obtenues via l'API archive
ERA5-Land d'Open-Meteo, mais volontairement limitées à cette fenêtre de 5 ans pour garder une
climatologie homogène — pas une série 1981-aujourd'hui comme pour la pluie CHIRPS. Étendre cette
récupération à 40+ ans, pour chaque point de grille, multiplierait par ~8 le volume d'appels API déjà
goulot d'étranglement du pipeline (`max_et0_batches`, pause de rythme) ; et ajuster une loi
log-logistique correctement (méthode des L-moments) est un morceau de statistique neuf qu'il serait
irresponsable de livrer sans validation indépendante poussée. Ni l'un ni l'autre n'a été fait cette
nuit — ce serait fabriquer une précision qu'on n'a pas.

## Ce qu'on a testé à la place

Deux indices déjà calculés par le bilan hydrique de Thornthwaite-Mather (`soilwater_core.run_balance`,
qui combine la pluie CHIRPS réelle ET la climatologie d'évapotranspiration à chaque pas de temps,
contrairement au SPI qui n'utilise que la pluie) :

- **sm_z** : humidité du sol relative, standardisée par mois calendaire (0 = normal pour ce mois).
- **recharge12_z** : recharge nette cumulée sur 12 mois (eau qui dépasse la capacité de rétention du
  sol), standardisée.

Testés sur les mêmes 6 paires région-saison positives (Androy/Anosy/Atsimo Andrefana, 2020-21 et
2021-22) et les mêmes négatives que `secheresse_pod_far.md` :

| Indicateur | Seuil | TP | FN | FP | TN | POD | FAR |
|---|---|---|---|---|---|---|---|
| sm_z, minimum de la saison | ≤ -1,0 | 1 | 5 | 141 | 189 | 0,17 | 0,99 |
| sm_z, minimum de la saison | ≤ -1,5 | 0 | 6 | 55 | 275 | 0,00 | 1,00 |
| recharge12_z, minimum de la saison | ≤ -1,0 | 0 | 6 | 0 | 330 | 0,00 | — |

## Résultat, dit franchement

**Les deux indices font pire que le SPI-12 minimum de saison** (qui atteignait POD = 1,00, voir
`secheresse_pod_far.md`) pour détecter ce même épisode. Deux explications distinctes :

1. **recharge12_z est inutilisable ici, pour une raison de conception, pas de bug** : la « recharge »
   au sens de ce bilan ne se produit que quand le sol dépasse sa capacité de rétention (percolation
   au-delà du réservoir utile) — un événement rare dans le Grand Sud, aride une bonne partie de
   l'année, donc presque toujours proche de 0 et peu variable (écart-type observé sur l'ensemble du
   pays : 0,016, contre ~0,76 pour sm_z). Cet indice a été conçu pour suivre la tendance des nappes sur
   plusieurs années, pas pour détecter un déficit saisonnier aigu — mauvais choix d'indice pour cette
   question, pas un signal de sécheresse manqué.
2. **sm_z fait moins bien que le SPI**, alors qu'il intègre en principe plus d'information (pluie +
   évapotranspiration + mémoire du sol). Hypothèse la plus probable : le bilan hydrique a de l'inertie
   (le stock du sol se vide progressivement, pas instantanément), ce qui peut *amortir* un déficit de
   pluie plutôt que l'amplifier, alors que les régions du Grand Sud ont une faible capacité de
   rétention (sols sableux) et étaient déjà proches de leur minimum climatologique avant même
   l'épisode documenté — la standardisation par mois ne voit alors qu'un écart modéré, puisqu'être sec
   est déjà la normale saisonnière sur place.

**Conclusion honnête : la climatologie d'évapotranspiration fixe ne suffit pas à améliorer la détection
de cet épisode par rapport au SPI seul** — au contraire. Ça ne veut pas dire qu'un vrai SPEI (avec une
évapotranspiration qui varie chaque année) ferait pire : ça veut dire qu'avec les données qu'on a
*actuellement*, ajouter l'évapotranspiration n'aide pas, et qu'il ne faut pas présenter sm_z ou
recharge12_z comme des indicateurs de sécheresse plus fiables que le SPI sur le site.

## Ce que ça veut dire pour MakyClimat

1. **Ne pas ajouter de nouvel indicateur « SPEI » en production** sur la base de ce test — ça ajouterait
   de la complexité pour une performance inférieure au SPI déjà affiché.
2. **sm_z et recharge12_z restent utiles pour ce qu'ils mesurent déjà** (humidité du sol affichée dans
   la fiche de zone, tendance de nappe) — ce test ne remet pas en cause leur usage actuel, seulement
   leur usage comme substitut au SPI pour la détection de sécheresse aiguë.
3. **Un vrai SPEI reste une piste valable**, mais seulement si on investit dans une série
   d'évapotranspiration qui varie réellement par année (élargir `read_et0_points` à l'historique complet,
   coût : ~8x le volume d'appels API actuel, à étaler sur plusieurs jours) et un ajustement log-logistique
   correctement validé — travail estimé à plusieurs jours, pas une nuit, à planifier séparément.
4. Même limite que les deux autres fichiers de validation sécheresse : **N = 1 événement documenté**,
   donc aucune conclusion ferme n'est possible sur la performance réelle de ces indices en général —
   seulement sur ce cas précis.
