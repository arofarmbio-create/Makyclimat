# Potentiel pour point d'eau peu profond — ce qu'il montre et ce qu'il ne montre pas

**Niveau de preuve : non validé.** Pas une approximation calibrée sur un signal réel comme
`susc_inond_pct` (dégâts satellite) : c'est une construction raisonnée, jamais comparée à un résultat
de forage réel, faute de donnée.

## Ce qu'il calcule

Pour chaque fokontany, un classement relatif de 0 à 100 combinant 4 critères de terrain déjà calculés
par MakyClimat, chacun transformé en rang percentile (0-1) sur l'ensemble du pays avant pondération :

| Critère | Poids | Source | Sens |
|---|---|---|---|
| Recharge standardisée sur 12 mois (`recharge12_z`) | 40 % | Bilan de Thornthwaite-Mather (CHIRPS + ET0 ERA5-Land) | Plus haut = mieux |
| Part de la zone à moins de 15 m au-dessus du cours d'eau (`hand_lt15_pct`) | 25 % | HAND, Copernicus GLO-90 | Plus haut = mieux |
| Pente moyenne (`slope_mean_pct`) | 20 % | Copernicus GLO-90 | Plus bas = mieux (inversé) |
| Capacité de rétention en eau du sol (`whc_mm`) | 15 % | SoilGrids | Plus haut = mieux |

Méthode : analyse multicritère par somme pondérée (« weighted overlay »), une approche standard en
l'absence de données de forage pour entraîner un modèle statistique. Un fokontany sans au moins 70 %
des critères disponibles n'est pas noté (pas de valeur inventée).

## Ce qu'il NE calcule PAS, et pourquoi c'est important

1. **Aucune géologie.** Le facteur le plus déterminant du succès réel d'un forage — nature du socle
   (cristallin, sédimentaire), failles, aquifères connus — n'est inclus nulle part. Nous n'avons
   identifié aucune carte géologique ou hydrogéologique numérique à résolution utile pour Madagascar
   accessible librement à ce jour. Tant qu'elle ne l'est pas, ce score ne peut PAS remplacer une étude
   hydrogéologique.
2. **Aucune donnée réelle de forage** (succès, débit, profondeur de la nappe, salinité, qualité de
   l'eau) pour calibrer ou valider les poids choisis (40/25/20/15). Les poids reflètent un raisonnement
   hydrologique de bon sens, pas un ajustement statistique.
3. **Compromis non résolu, affiché mais pas corrigé :** une zone HAND basse (proche d'un cours d'eau,
   bien notée ici car la nappe y est souvent moins profonde) est aussi plus exposée aux inondations et
   au risque de contamination d'un puits peu profond (voir `susc_inond_pct`, qui mesure justement ce
   risque). Un score élevé ici ne dit rien sur ce risque — les deux indicateurs doivent être lus
   ensemble, jamais `potentiel_eau_pct` seul.
4. **Un classement relatif, pas une probabilité.** 80/100 ne signifie pas « 80 % de chances de succès » :
   cela signifie seulement « mieux classé que la plupart des autres fokontany du pays sur ces 4
   critères ». La distribution dépend de l'étendue du pays analysé.

## Comment l'interpréter

Un score élevé justifie d'inscrire la zone dans une liste de présélection pour une étude
hydrogéologique de terrain (sondage électrique, piézomètre d'essai), pas une décision de forage. Un
score bas ne signifie pas qu'un forage y est impossible (la géologie, absente du calcul, peut très bien
compenser un terrain par ailleurs peu favorable).

## Pour l'améliorer

1. Une carte géologique/hydrogéologique numérique de Madagascar (BRGM, services miniers nationaux, ou
   programme type AfricaGroundwaterAtlas du British Geological Survey) : le critère qui manque le plus.
2. Des retours réels de forages (succès/échec, débit, profondeur) auprès d'ONG WASH ou du ministère de
   l'Eau — même quelques dizaines de points suffiraient pour une première validation croisée.
3. Une couche de qualité/salinité de l'eau souterraine dans les zones côtières, où l'intrusion saline
   limite l'usage même d'un forage par ailleurs productif.

Tant que ces données manquent, l'indicateur reste étiqueté « non validé » et n'est jamais présenté comme
une recommandation de forage.
