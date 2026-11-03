# Protocole-cadre : module « eaux souterraines » de MakyClimat

*Rédigé le 03/11/2026, **avant** tout nouveau calcul. Il rassemble les demandes du porteur du projet (carte précise du
niveau statique ; recharge, volume, renouvellement, risque d'épuisement ; prévision à court, moyen et long terme), les
deux textes d'audit qu'il a transmis le 02/11/2026, et les résultats déjà obtenus (H-C1, H-C2, H-C2b, H-C5, M3).
Protocole doctoral : module M3, expériences E3 (comparaison, ablation), E4, E6 et E7, validation §11. Les protocoles
détaillés existants restent en vigueur : `protocole_carte_nappes.md`, `protocole_nappes_mgmerl.md`,
`protocole_climat_extremes_nappes.md`. Toute modification sera datée en section 10, avant les résultats concernés.*

## 1. Objectif

En tout point de Madagascar, l'outil doit estimer, **avec sa précision connue** :

1. la profondeur du **niveau statique** ;
2. la **recharge** (quantité d'eau qui réalimente la nappe) ;
3. le **volume d'eau disponible** (stock) ;
4. la **vitesse de renouvellement** ;
5. le **risque d'épuisement** ;

et prévoir leur évolution à **court terme** (semaines à 3 mois), **moyen terme** (une saison à 2 ans) et **long terme**
(2030 à 2100).

L'outil ne remplace pas une étude géophysique ni un essai de pompage. « Précis » veut dire ici : **dont la précision
est mesurée et affichée en chaque point**.

## 2. Principes

- **Chaque grandeur porte son niveau de preuve** (validé, standard, approximation, non validé), comme le reste du
  système. Le volume, le renouvellement et le risque restent des « approximations » tant qu'aucune mesure ne les
  valide.
- **On n'ajoute une variable que si une expérience comparative montre son apport** (texte d'audit du 02/11/2026).
- **Exploratoire ou confirmatoire** : toute analyse faite sur les forages MGMERL déjà utilisés est exploratoire. La
  confirmation demande des forages indépendants (archives du porteur du projet, autres sources).
- **Pas de multiplication des modèles** (risque 4 du protocole doctoral) : l'hybride (forêt de quantiles) et un seul
  modèle comparatif ajouté, la régression-krigeage.
- **Niveau statique et recharge sont deux grandeurs distinctes** : la première est un état, la seconde un flux.

## 3. Niveau statique : la base de tout

**Phase 0 : audit et cadre d'évaluation (aucune donnée nouvelle).**
- Diagramme de flux des données pour chaque expérience (relevés lus, puis contrôlés, puis avec valeur de Fan, puis
  utilisés), carte et tableau de densité des forages par région, dates et saisons des relevés.
- **Critères d'évaluation, fixés ici** et utilisés dans toutes les phases suivantes :
  - **critère principal 1** : erreur médiane absolue **moyennée par région** (chaque région laissée de côté pèse
    autant), validation par région entière d'au moins 10 forages ;
  - **critère principal 2** : erreur médiane absolue des forages situés **à plus de 50 km** du forage
    d'apprentissage le plus proche (les zones sans forages, celles qui comptent pour un foreur) ;
  - incertitude de chaque critère : intervalle de confiance à 95 % par rééchantillonnage des régions (bootstrap,
    2 000 tirages) ;
  - **couverture de l'intervalle de 80 %** par région et par classe de distance (0-25, 25-50, 50-100, plus de 100 km) ;
  - critères secondaires : erreur par blocs de 1° (comme H-C2), biais moyen.
- **S0** : les modèles actuels (Fan seule, krigeage, hybride, réglages de H-C2), recalculés avec ces critères. C'est
  la référence de toutes les comparaisons suivantes.
- La puissance statistique est faible (8 régions) : les écarts sont présentés avec leurs intervalles de confiance,
  sans conclure au-delà.

**Phase 1 : conditions de mesure.** Ajout de la saison du relevé (saison des pluies : novembre à avril) et de la pluie
des 3 et 12 mois précédant le relevé (SPI-3, SPI-12 à la maille du forage). **Règle fixée** : elles ne sont gardées
pour les phases suivantes que si les deux critères principaux s'améliorent par rapport à S0.

**Phase 2 : axe structural (failles et lithologie).**
- **S1** : lithologie et failles **cartographiées sur le terrain** (synthèse BRGM-USGS au 1:1 000 000, puis feuilles
  PGRM au 1:100 000 si elles sont obtenues auprès de l'OMNIS ou du ministère des Mines). Variables : type de roche,
  distance à la faille la plus proche, densité de failles dans un rayon de 5 km, direction dominante. La distance à
  la faille n'est utilisée que si la précision de position de la carte le permet (1:100 000) ; au 1:1 000 000, seules
  la densité et la direction sont utilisées.
- **S2** : S1 plus les linéaments tirés du relief GLO-90 et les paramètres structuraux dérivés, **nommés
  « linéaments », jamais « failles »**. On mesure aussi la part des failles cartographiées que les linéaments
  retrouvent.
- Une étape est retenue si elle améliore les deux critères principaux ; sinon elle est rejetée, et c'est publié.
- **Analyse de sensibilité** : importance de chaque variable par permutation, à l'intérieur de la validation par
  région.

**Phase 3 : un modèle comparatif.** Régression-krigeage (prédiction de l'hybride, puis krigeage de ses résidus) sur
le meilleur jeu de variables de la phase 2, comparée à l'hybride avec les mêmes critères.

**Phase 4 : confirmation indépendante** sur des forages jamais utilisés (archives du porteur du projet ; autres
sources). C'est la seule phase confirmatoire.

**Phase 5 : cartes nationales.** Profondeur estimée (médiane), intervalle de 80 %, densité des forages, et **domaine
de fiabilité** : en chaque maille, l'erreur attendue tirée de la classe de distance au forage le plus proche (phase 0).
Agrégation par fokontany, commune, district et région.

## 4. Recharge

- Long terme (moyenne annuelle) : transfert de connaissances (section 10 de `protocole_carte_nappes.md`). H-C5 est
  confirmée ; H-C6 attend le NDVI.
- Variabilité d'une année à l'autre : chaîne océan, pluies extrêmes, recharge (`protocole_climat_extremes_nappes.md`,
  H-N7).

## 5. Volume disponible, renouvellement, risque d'épuisement (formules fixées à l'avance)

- **Épaisseur saturée** (m) : b = épaisseur des altérites (profondeur du socle, SoilGrids) − niveau statique, ramenée
  à 0 si elle est négative. Valable pour la nappe d'altérites et les nappes superficielles. Les nappes profondes de
  fissures et de grès ne sont pas estimées faute de données : elles sont signalées comme « non estimées ».
- **Volume** (m³ par km²) : V = 10⁶ × b × Sy. Sy (porosité efficace) : socle altéré 0,02 à 0,08 (Maréchal, Dewandel) ;
  sédimentaire et non consolidé 0,05 à 0,15 (bibliothèque de paramètres). On publie une fourchette (Sy bas et b bas ;
  Sy haut et b haut), jamais une valeur unique.
- **Temps de renouvellement** (années) : τ = V / (10³ × R), avec R la recharge en mm/an. Fourchette issue des
  fourchettes de V et de R. Lecture : moins de 10 ans, renouvelable ; 10 à 100 ans, lent ; plus de 100 ans, ressource
  peu renouvelable.
- **Risque d'épuisement** :
  - prélèvements (mm/an équivalents) = population × besoin unitaire (20 L par personne et par jour, norme Sphère ;
    sensibilité de 15 à 50 L) ÷ surface ;
  - indice d'exploitation = prélèvements / recharge ;
  - classes : moins de 0,1 faible ; 0,1 à 0,4 modéré ; plus de 0,4 élevé (seuils de stress inspirés de l'indice
    d'exploitation de l'eau, à justifier dans la thèse) ;
  - aggravé d'une classe si les niveaux mesurés baissent d'une année à l'autre (séries MGMERL), et si la conductivité
    dépasse 3 000 µS/cm (risque de salinisation).
- Ces trois grandeurs sont des **approximations** : aucune mesure de volume ni d'âge ne les valide aujourd'hui.
  Contrôle de vraisemblance : comparaison des temps de renouvellement aux âges d'eau de la littérature (eaux anciennes
  de fissures, section 3 ter de `biblio_hydrogeologie_grand_sud.md`) et à l'observation de terrain du porteur du
  projet.

## 6. Prévision par horizon

| Horizon | Méthode | Validation |
|---|---|---|
| Court terme (semaines à 3 mois) | réponse de chaque nappe suivie à la pluie récente (SPI-n propre au site, M3), prévisions de pluie du système | prévision du niveau du mois suivant, sur les années non utilisées pour l'apprentissage, aux 16 sites suivis |
| Moyen terme (saison à 2 ans) | chaîne H-N7 et prévision saisonnière SEAS5 | maillons A et B de H-N7 |
| Long terme (2030-2100) | projections CMIP6 (pluie, évapotranspiration ; SSP1-2.6, SSP2-4.5, SSP5-8.5) appliquées au modèle de recharge ; croissance de la population pour les prélèvements | scénarios, pas de validation possible ; sensibilité (protocole doctoral E7) et cohérence avec le passé (1981-2025) |

## 7. Calendrier (soutenance vers avril 2027)

- Novembre à décembre 2026 : phases 0 à 3 (niveau statique), H-C6 (recharge).
- Janvier 2027 : volume, renouvellement, risque ; phase 5 (cartes).
- Février 2027 : moyen terme (H-N7), scénarios CMIP6 ; court terme aux sites suivis.
- Mars 2027 : phase 4 si les forages indépendants sont obtenus ; rédaction.

## 8. Données à obtenir par le porteur du projet

- Failles et lithologie numériques : synthèse BRGM-USGS au 1:1 000 000 (base de données SIG) et feuilles PGRM au
  1:100 000 (OMNIS, ministère des Mines).
- Archives de ses propres forages : position, profondeur, niveau statique, coupe lithologique, failles rencontrées,
  salinité, date.

## 9. Mise en œuvre

Scripts testés sur données simulées avant les données réelles ; calculs légers sur le PC, téléchargements par
l'agent dédié ; résultats publiés agrégés (jamais les valeurs point par point de Fan, licence) ; registre (R-41) et
journal à chaque étape, réussite ou échec.

## 10. Journal des modifications

- 03/11/2026 : version initiale.
