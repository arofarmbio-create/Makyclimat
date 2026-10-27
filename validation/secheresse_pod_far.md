# Seuil opérationnel de sécheresse (pct pluie/normale) : POD/FAR, dit franchement

**Niveau de preuve : exploratoire, N beaucoup trop faible pour calibrer quoi que ce soit.** Même
méthode que `declencheurs_anticipation.md` (taux de détection POD, taux de fausses alertes FAR), mais
appliquée à la sécheresse plutôt qu'aux cyclones — avec une limite structurelle bien plus sévère que
pour les cyclones : on ne dispose que d'**un seul épisode documenté** (pas 13 comme pour les cyclones).

## Vérité terrain disponible

Un seul épisode de sécheresse largement documenté dans les sources ouvertes pour Madagascar sur la
période couverte par nos données (CHIRPS 1981-aujourd'hui) : la **sécheresse du Grand Sud et Grand
Sud-Est, 2020-10-01 à 2022-04-30** (GRFC 2024 : 2,2 millions de personnes en IPC phase 3+ au pic,
nov. 2022-mars 2023 ; `evenements.csv`). Régions citées : Androy, Anosy, Atsimo Andrefana. On retient
ces 3 régions × les 2 saisons climatiques couvertes par la fenêtre de l'événement (saison de pluie
nov. 2020-avril 2021 = « saison_fin 2021 », et nov. 2021-avril 2022 = « saison_fin 2022 ») comme les
**6 seules paires région-saison positives** du jeu de test. « Grand Sud-Est » (Atsimo Atsinanana,
Ihorombe, Vatovavy, Fitovinany) n'est volontairement pas inclus : le partage précis des régions entre
« Sud » et « Sud-Est » varie selon les sources, et ajouter des régions sans certitude gonflerait
artificiellement le POD ou le FAR selon le sens de l'erreur.

**Toutes les autres paires région-saison (258 sur 264, ou 2016-2026) sont traitées comme négatives**,
avec exactement la même réserve que pour les cyclones : une région non citée dans un rapport de grande
sécheresse n'est pas forcément épargnée (manque de données fines et continues de sécurité alimentaire
par région et par saison) -- **le FAR est donc probablement surestimé**, pas sous-estimé.

## Ce qui a été testé

Sur `validation/pluie_saison_par_region.csv` (24 régions × 11 saisons, pluie cumulée nov-avril en % de
la normale CHIRPS 1982-aujourd'hui) et `validation/spi_regions.csv` (SPI-3/6/12 mensuels, mêmes régions,
2014-2026) :

| Indicateur testé | Seuil | TP | FN | FP | TN | POD | FAR |
|---|---|---|---|---|---|---|---|
| Seuil opérationnel actuel (pluie % normale) | < 75 % (= niveau « Alerte » actuel) | 3 | 3 | 27 | 231 | **0,50** | 0,90 |
| idem | < 90 % (= niveau « Veille » actuel) | 5 | 1 | 94 | 164 | 0,83 | 0,95 |
| idem | < 50 % (= niveau « Urgence » actuel) | 0 | 6 | 0 | 258 | 0,00 | — |
| SPI-3 de mars (fin de saison) | ≤ -1,0 | 0 | 6 | 58 | 224 | 0,00 | 1,00 |
| SPI-6 de mars | ≤ -1,0 | 3 | 3 | 66 | 216 | 0,50 | 0,96 |
| SPI-12 de mars | ≤ -1,0 | 3 | 3 | 57 | 225 | 0,50 | 0,95 |
| SPI-12, minimum de la saison (méthode de `secheresse_spi.md`) | ≤ -1,0 | 6 | 0 | 153 | 177 | 1,00 | 0,96 |
| idem | ≤ -1,5 | 5 | 1 | 85 | 245 | 0,83 | 0,94 |
| idem | ≤ -2,0 | 2 | 4 | 31 | 299 | 0,33 | 0,94 |

## Résultat principal

**Le seuil opérationnel actuel (pluie < 75 % de la normale) rate la moitié de l'épisode documenté**
(Atsimo Andrefana 2020-21 à 88 %, Anosy et Androy 2021-22 à 89-92 % -- tous classés « Veille » ou
« Normal » alors que la région traversait une crise alimentaire majeure cette année-là). Baisser le
seuil à 90 % (niveau « Veille ») améliore le POD (0,83) mais au prix d'un FAR encore plus élevé (0,95),
exactement comme pour les cyclones : plus un seuil est sensible, plus il couvre de fausses alertes.

**Aucun indicateur testé seul ne fait mieux que le hasard dans une fenêtre d'un mois donné** (SPI-3 de
mars rate carrément tout l'épisode -- POD 0). Seul le minimum du SPI-12 **sur l'ensemble de la saison**
(la méthode déjà documentée dans `secheresse_spi.md`) atteint un POD parfait (1,00), mais avec un FAR
de 0,96 -- aussi inutilisable comme règle de décision qu'un déclencheur qui sonne l'alarme presque
partout, presque tout le temps.

**Explication probable, déjà pressentie dans `secheresse_spi.md`** : la crise IPC 2022-23 résulte de
**plusieurs saisons déficitaires qui s'accumulent**, pas d'un seul mauvais mois ni d'une seule mauvaise
saison isolée -- un indicateur ponctuel (pluie d'une saison, SPI d'un mois) ne peut structurellement
pas voir cet effet cumulatif. C'est probablement pourquoi même le meilleur indicateur testé ici
(SPI-12 minimum de la saison) sur-détecte à ce point : il capture la sécheresse météorologique
instantanée, pas la vulnérabilité alimentaire qui en résulte avec un décalage de plusieurs saisons.

## Limite structurelle, à ne pas minimiser

Avec **N = 1 événement documenté** (contre 13 pour les cyclones), ce tableau ne permet de calibrer
**aucun** seuil de façon fiable -- il permet seulement de montrer que le seuil actuel rate une partie
significative du seul cas connu, ce qui suffit à confirmer que la mention « PROVISOIRE » déjà présente
dans `config/countries/mdg.yml` reste justifiée. Pour aller plus loin, il faudrait une série
longitudinale de classifications IPC par région (pas seulement le pic national du dernier épisode) --
donnée qui n'est pour l'instant pas accessible en open data pour Madagascar sur la durée nécessaire.

## Ce que ça veut dire pour MakyClimat

1. **Ne pas afficher le niveau d'alerte sécheresse actuel comme un verdict fiable d'action** -- c'est
   déjà le cas (fiche de fiabilité, mention « seuils provisoires »), et ce test confirme qu'il faut
   continuer à le présenter ainsi.
2. **Explorer un indicateur cumulatif multi-saison** (ex. somme ou moyenne glissante du déficit sur
   2-3 saisons, pas seulement la saison en cours) comme piste d'amélioration la plus prometteuse,
   puisque l'effet cumulatif est l'explication la plus probable de l'écart observé ici -- à tester
   explicitement dès qu'une deuxième série d'événements de sécheresse documentés sera disponible.
3. **Ne pas publier de seuil « calibré »** pour la sécheresse tant qu'un seul événement sert de vérité
   terrain -- même conclusion que pour les cyclones, pour une raison encore plus forte ici.
