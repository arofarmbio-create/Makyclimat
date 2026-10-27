# Potentiel pour point d'eau peu profond — ce qu'il montre et ce qu'il ne montre pas

**Niveau de preuve : non validé.** Pas une approximation calibrée sur un signal réel comme
`susc_inond_pct` (dégâts satellite) : c'est une construction raisonnée, jamais comparée à un résultat
de forage réel malgache, faute de donnée.

## Mise à jour : géologie réelle ajoutée ; profondeur de nappe désormais mesurée (MGMERL), plus continentale

Une carte géologique/hydrogéologique de Madagascar existe bel et bien en accès libre : l'**Africa
Groundwater Atlas** du British Geological Survey (shapefile pays, 1:5 000 000, licence CC BY-SA,
https://africagroundwateratlas.org/). Elle donne, pour chaque zone, le type d'aquifère (socle
cristallin, sédimentaire consolidé/non consolidé, volcanique, karst) et sa classe de productivité
(débit indicatif en L/s). Elle est maintenant intégrée (voir `scripts/connector_geology.py`), ce qui
corrige la lacune géologique signalée dans la version précédente de cette note.

La **profondeur de nappe publiée à l'échelle continentale** (MacDonald, Bonsor, Ó Dochartaigh & Taylor,
2012, *Environ. Res. Lett.* 7:024009 ; profondeur : Bonsor & MacDonald 2011, BGS OR/11/067 ; grille
~5 km) a été définitivement écartée pour Madagascar : le fichier source, obtenu directement auprès du
BGS, inspecté point par point, a une emprise qui s'arrête à 40,8°E et ne couvre pas l'île (43°E–51°E) —
aucun retraitement ne pouvait y remédier.

À la place, `water_table_depth_m` est maintenant produit à partir de **mesures réelles de forages
malgaches**, extraites de **MGMERL** (mgmerl.org), plateforme publique de suivi des ressources en eau de
Madagascar (mWater, avec l'appui de l'UNICEF). Contrairement à la grille continentale, ce ne sont pas
des valeurs modélisées : chaque valeur vient d'un relevé de terrain réel (niveau statique d'eau mesuré
sur un forage, avec coordonnées GPS et date). Voir `scripts/connector_watertable.py` pour la méthode
complète et ses limites (extraction manuelle faute d'API publique accessible, échantillon des ~1000
relevés les plus récents sur 25 271 forages enregistrés, assignation par plus proche voisin dans un
rayon de 15 km → **environ 30 % des fokontany** reçoivent une valeur, les autres restent sans donnée
plutôt que d'en recevoir une inventée).

MGMERL fournit aussi des mesures réelles de **conductivité électrique** (µS/cm, indicateur indirect de
salinité/minéralisation), maintenant intégrées séparément dans `data/<pays>/external/water_quality.csv`
(`conductivity_uscm`, voir `scripts/connector_mgmerl_quality.py`, ~23 % des fokontany couverts). Cet
indicateur répond au point 3 de "Pour l'améliorer encore" ci-dessous (couche qualité/salinité, utile
notamment en zone côtière). **Il n'entre volontairement PAS dans le score `potentiel_eau_pct`** : une
conductivité élevée est un signal de risque qui peut coexister avec un site par ailleurs favorable — le
fondre dans une note positive unique masquerait ce risque. Conformément au principe du projet (exposition
≠ dommage ≠ besoin), il reste un indicateur à lire à côté du score, jamais mélangé dedans. MakyClimat ne
le classe pas "bon"/"mauvais" : la conductivité seule ne suffit pas à juger la potabilité (composition
ionique, normes retenues), donc seule la valeur mesurée est publiée, à charge pour l'utilisateur de
l'interpréter avec les seuils pertinents pour son usage.

## Ce qu'il calcule

Pour chaque fokontany, un classement relatif de 0 à 100 combinant 6 critères, chacun transformé en rang
percentile (0-1) sur l'ensemble du pays avant pondération :

| Critère | Poids | Source | Sens |
|---|---|---|---|
| Productivité d'aquifère (`aquifer_productivity_pct`) | 30 % | BGS Africa Groundwater Atlas (géologie réelle, 1:5 000 000) | Plus haut = mieux |
| Profondeur de nappe (`water_table_depth_m`) | 20 % | MGMERL — mesures réelles de forages, ~30 % des fokontany (voir ci-dessus) | Plus bas = mieux (inversé) |
| Recharge standardisée sur 12 mois (`recharge12_z`) | 25 % | Bilan de Thornthwaite-Mather (CHIRPS + ET0 ERA5-Land) | Plus haut = mieux |
| Part de la zone à moins de 15 m au-dessus du cours d'eau (`hand_lt15_pct`) | 8 % | HAND, Copernicus GLO-90 | Plus haut = mieux |
| Pente moyenne (`slope_mean_pct`) | 9 % | Copernicus GLO-90 | Plus bas = mieux (inversé) |
| Capacité de rétention en eau du sol (`whc_mm`) | 8 % | SoilGrids | Plus haut = mieux |

Méthode : analyse multicritère par somme pondérée (« weighted overlay »), une approche standard en
l'absence de données de forage malgaches pour entraîner un modèle statistique. Un fokontany sans au
moins 70 % des critères disponibles n'est pas noté (pas de valeur inventée).

## Ce qu'il NE calcule PAS, et pourquoi c'est encore « non validé »

1. **Géologie à l'échelle continentale seulement, profondeur de nappe ponctuelle et partielle.** La
   carte BGS est au 1:5 000 000 : elle ne résout aucune faille ni structure locale, c'est un ordre de
   grandeur régional. La profondeur de nappe MGMERL, elle, est une mesure réelle mais ponctuelle (un
   forage, pas une zone) et ne couvre qu'environ 30 % des fokontany (rayon de 15 km) — les 70 % restants
   n'ont toujours aucune valeur pour ce critère, pas une valeur approximative.
2. **Pas encore de calibrage statistique des poids sur des résultats réels de forage malgache**
   (succès/échec, débit, salinité). Les poids (30/20/25/8/9/8) reflètent un raisonnement hydrologique de
   bon sens — la géologie et la profondeur de nappe pèsent plus que la recharge climatique, documentées
   comme les facteurs les plus déterminants d'un forage réel — mais MGMERL donne des *niveaux* mesurés,
   pas des *résultats de forage* (succès/débit) qui permettraient de valider ou ajuster ces poids.
3. **Compromis non résolu, affiché mais pas corrigé :** une zone HAND basse (proche d'un cours d'eau,
   bien notée ici car la nappe y est souvent moins profonde) est aussi plus exposée aux inondations et
   au risque de contamination d'un puits peu profond (voir `susc_inond_pct`, qui mesure justement ce
   risque). Un score élevé ici ne dit rien sur ce risque — les deux indicateurs doivent être lus
   ensemble, jamais `potentiel_eau_pct` seul.
4. **Un classement relatif, pas une probabilité.** 80/100 ne signifie pas « 80 % de chances de succès » :
   cela signifie seulement « mieux classé que la plupart des autres fokontany du pays sur ces 6
   critères ». La distribution dépend de l'étendue du pays analysé.
5. **Licence de la grille de profondeur de nappe :** republiée par l'UNESCO-IHP avec l'autorisation du
   BGS/NERC, mais la page de catalogue ne précise pas de licence ouverte claire pour la grille
   elle-même (« tous droits réservés » sur le fichier d'origine). MakyClimat n'affiche jamais la grille
   brute, seulement une valeur agrégée par fokontany/sous-bassin, avec attribution complète.

## Bilan hydrique par sous-bassin versant

En plus du niveau fokontany, le bilan hydrique (recharge, humidité du sol, SPI, productivité
d'aquifère, profondeur de nappe) est désormais aussi agrégé par **sous-bassin versant** — les
sous-bassins déjà délimités par MakyClimat à partir du MNT Copernicus GLO-90 (voir
`scripts/build_hydro.py`), pas des unités administratives. Une moyenne par sous-bassin a plus de sens
hydrologique qu'une moyenne par fokontany, puisqu'un sous-bassin suit une ligne de partage des eaux. Elle
lisse en revanche les écarts internes à un grand sous-bassin, et hérite de toutes les limites
ci-dessus. Voir `scripts/build_subbasin_balance.py`.

## Comment l'interpréter

Un score élevé justifie d'inscrire la zone dans une liste de présélection pour une étude
hydrogéologique de terrain (sondage électrique, piézomètre d'essai), pas une décision de forage. Un
score bas ne signifie pas qu'un forage y est impossible (la géologie et la nappe, à l'échelle
continentale, peuvent très bien ne pas refléter une structure locale favorable).

## Pour l'améliorer encore

1. Une carte géologique nationale plus fine que 1:5 000 000 (ex. les cartes BRGM/PGRM au 1:1 000 000 ou
   1:100 000, citées dans la littérature mais pas identifiées en téléchargement numérique libre à ce
   jour) : résoudrait les failles et structures locales.
2. Des retours réels de forages malgaches (succès/échec, débit, profondeur) auprès d'ONG WASH ou du
   ministère de l'Eau — même quelques dizaines de points suffiraient pour une première validation
   croisée et un calibrage statistique des poids.
3. **Partiellement fait** : une couche de conductivité électrique (`conductivity_uscm`, MGMERL) est
   intégrée depuis le 27/10/2026 (~23 % du pays). Reste à faire : élargir sa couverture (même piste que
   le point 4) et, si une donnée de composition ionique devient disponible, affiner au-delà de la seule
   conductivité pour les zones côtières à risque d'intrusion saline.
4. Élargir la couverture de la profondeur de nappe au-delà des ~30 % actuels : obtenir un accès membre
   à MGMERL (export complet des 25 271 forages plutôt que les ~1000 relevés les plus récents visibles
   publiquement), ou croiser avec d'autres bases WASH malgaches (ONG, ministère de l'Eau), ou relâcher
   prudemment le rayon de 15 km avec un indicateur de confiance décroissant selon la distance.

Tant que ces données manquent, l'indicateur reste étiqueté « non validé » et n'est jamais présenté comme
une recommandation de forage.
