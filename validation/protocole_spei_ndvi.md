# Protocole : SPI ou SPEI pour anticiper le stress de la végétation à Madagascar ?

*Rédigé le 29/10/2026, **avant** tout calcul. Modifications datées en section 6. Cahier des charges §6B (SPEI), §6D
(NDVI), §13. Remplace l'approche provisoire de `validation/spei_approche.md`, qui n'avait pas de série
d'évapotranspiration.*

## 1. Question

Par district, l'indice qui tient compte de la demande évaporatoire (SPEI) suit-il mieux le stress de la végétation
observé par satellite (anomalie de NDVI MODIS) que l'indice de pluie seule (SPI) ? Et cet avantage dépend-il du
climat (sud et ouest secs contre est humide) ?

Intérêt pour la thèse :
- Le choix de l'indice de sécheresse agricole n'a jamais été évalué à cette échelle pour Madagascar.
- La réponse conditionne le module sécheresse (§6) et sa transposition à d'autres pays.

## 2. Données

| Variable | Source | Période | Résolution |
|---|---|---|---|
| Pluie mensuelle | CHIRPS v2.0 | 1981-2025 | 0,05° |
| ET0 mensuelle | ERA5-Land, moyennes mensuelles (température, point de rosée, vent à 10 m, rayonnement solaire, pression), Penman-Monteith FAO-56 | 1981-2025 | 0,1° |
| NDVI mensuel | MODIS MOD13C2 v6.1 (AppEEARS, NASA), pixels de fiabilité 0 ou 1 seulement | 2000-2025 | 0,05° |

Valeurs par district : moyenne pondérée par la surface des fokontany, en prenant la maille valide la plus proche de
chaque centroïde.

Limites de l'ET0 :
- Calculée sur des moyennes mensuelles (le Tmax et le Tmin journaliers ne sont pas disponibles), avec un flux de
  chaleur du sol nul et Rso = 0,75 Ra.
- Un contrôle est fait contre la climatologie d'ET0 Open-Meteo 2016-2020 déjà utilisée par le site.

## 3. Indices

- SPI-n : loi gamma par mois du calendrier (fonction existante `soilwater_core.spi`).
- SPEI-n : bilan P − ET0 cumulé sur n mois, loi log-logistique à 3 paramètres par L-moments non biaisés
  (Vicente-Serrano et al. 2010 ; Beguería et al. 2014), par mois du calendrier, borné à ±3,09.
- n = 1, 3, 6. Ajustement sur 1981-2025.
- NDVI : anomalie standardisée par mois du calendrier (scores normaux), sur 2001-2025.

## 4. Mesure et hypothèses fixées à l'avance

- Corrélation de Pearson entre l'indice au mois t − L et l'anomalie de NDVI au mois t, sur les mois de végétation
  active (décembre à mai), 2001-2025.
- **Choix principal fixé à l'avance : n = 3, L = 1.** On rapporte aussi la meilleure combinaison (n, L) de chaque
  indice, dans la même grille pour les deux indices, comme analyse secondaire.
- Districts « secs » : ceux des régions Androy, Anosy, Atsimo-Andrefana, Menabe, Melaky, Boeny et Ihorombe. Les
  autres sont « humides ».
- **H1** : dans les districts secs, r(SPEI) > r(SPI) dans plus de la moitié des districts (test du signe unilatéral,
  5 %).
- **H2** : dans les districts humides, pas de gain systématique (test du signe non significatif). Cela confirmerait
  qu'il s'agit d'un effet de la limitation par l'eau, et non d'un artefact.
- **H3** (descriptif) : sur la sécheresse documentée du Grand Sud (2020-2022), on compare la date du premier mois où
  SPEI-6 ≤ −1 avec celle du SPI-6, et la durée de l'épisode pour chacun.

## 5. Limites connues

- Le NDVI réagit aussi à l'irrigation, aux feux, aux cyclones et à la saturation en forêt dense : la corrélation est
  attendue faible dans l'est.
- ERA5-Land est une réanalyse, pas une observation.
- Les autocorrélations rendent les p-valeurs par district optimistes : seul le test du signe entre districts est
  utilisé pour conclure.

## 6. Journal des modifications

- 29/10/2026 : version initiale.
