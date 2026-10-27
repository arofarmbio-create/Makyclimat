# Potentiel pour point d'eau peu profond — ce qu'il montre et ce qu'il ne montre pas

**Niveau de preuve : non validé.** Pas une approximation calibrée sur un signal réel comme
`susc_inond_pct` (dégâts satellite) : c'est une construction raisonnée, jamais comparée à un résultat
de forage réel malgache, faute de donnée.

## Mise à jour : géologie réelle ajoutée ; profondeur de nappe en attente d'une source accessible

Une carte géologique/hydrogéologique de Madagascar existe bel et bien en accès libre : l'**Africa
Groundwater Atlas** du British Geological Survey (shapefile pays, 1:5 000 000, licence CC BY-SA,
https://africagroundwateratlas.org/). Elle donne, pour chaque zone, le type d'aquifère (socle
cristallin, sédimentaire consolidé/non consolidé, volcanique, karst) et sa classe de productivité
(débit indicatif en L/s). Elle est maintenant intégrée (voir `scripts/connector_geology.py`), ce qui
corrige la lacune géologique signalée dans la version précédente de cette note.

Une **profondeur de nappe publiée à l'échelle continentale** existe aussi dans la littérature
(MacDonald, Bonsor, Ó Dochartaigh & Taylor, 2012, *Environ. Res. Lett.* 7:024009 ; profondeur : Bonsor &
MacDonald 2011, BGS OR/11/067 ; grille ~5 km), mais **n'est, à ce jour, pas accessible par un lien de
téléchargement stable** : le service qui la republiait (UNESCO-IHP) a retiré le fichier de sa
plateforme, et la version hébergée par le BGS lui-même est derrière un bouton de téléchargement
JavaScript sans URL directe (hors de portée d'un script automatisé sans navigateur). Le connecteur
(`scripts/connector_watertable.py`) reste en place et prêt à fonctionner le jour où une source stable
sera identifiée ; en attendant, `water_table_depth_m` n'est pas produit et le score ci-dessous se
rabat automatiquement sur les 5 critères restants (voir "Pour l'améliorer encore").

## Ce qu'il calcule

Pour chaque fokontany, un classement relatif de 0 à 100 combinant 6 critères, chacun transformé en rang
percentile (0-1) sur l'ensemble du pays avant pondération :

| Critère | Poids | Source | Sens |
|---|---|---|---|
| Productivité d'aquifère (`aquifer_productivity_pct`) | 30 % | BGS Africa Groundwater Atlas (géologie réelle, 1:5 000 000) | Plus haut = mieux |
| Profondeur de nappe (`water_table_depth_m`) | 20 % | MacDonald et al. (2012), grille ~5 km — **actuellement sans donnée, source pas encore accessible, voir ci-dessus** | Plus bas = mieux (inversé) |
| Recharge standardisée sur 12 mois (`recharge12_z`) | 25 % | Bilan de Thornthwaite-Mather (CHIRPS + ET0 ERA5-Land) | Plus haut = mieux |
| Part de la zone à moins de 15 m au-dessus du cours d'eau (`hand_lt15_pct`) | 8 % | HAND, Copernicus GLO-90 | Plus haut = mieux |
| Pente moyenne (`slope_mean_pct`) | 9 % | Copernicus GLO-90 | Plus bas = mieux (inversé) |
| Capacité de rétention en eau du sol (`whc_mm`) | 8 % | SoilGrids | Plus haut = mieux |

Méthode : analyse multicritère par somme pondérée (« weighted overlay »), une approche standard en
l'absence de données de forage malgaches pour entraîner un modèle statistique. Un fokontany sans au
moins 70 % des critères disponibles n'est pas noté (pas de valeur inventée).

## Ce qu'il NE calcule PAS, et pourquoi c'est encore « non validé »

1. **Géologie et profondeur de nappe à l'échelle continentale seulement.** La carte BGS est au
   1:5 000 000 et la grille de profondeur à ~5 km : ni l'une ni l'autre ne résout une faille, une
   structure locale ou une variation de nappe à l'échelle d'un village. Elles donnent un ordre de
   grandeur régional, pas un diagnostic de site.
2. **Aucune donnée réelle de forage malgache** (succès, débit, profondeur de la nappe mesurée, salinité,
   qualité de l'eau) pour calibrer ou valider les poids choisis (30/20/25/8/9/8). Les poids reflètent un
   raisonnement hydrologique de bon sens — la géologie et la profondeur de nappe pèsent maintenant plus
   que la recharge climatique, car elles sont documentées comme les facteurs les plus déterminants d'un
   forage réel — mais ce n'est toujours pas un ajustement statistique sur des résultats réels.
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
3. Une couche de qualité/salinité de l'eau souterraine dans les zones côtières, où l'intrusion saline
   limite l'usage même d'un forage par ailleurs productif.

Tant que ces données manquent, l'indicateur reste étiqueté « non validé » et n'est jamais présenté comme
une recommandation de forage.
