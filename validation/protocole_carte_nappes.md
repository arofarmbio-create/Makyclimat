# Protocole : carte nationale des nappes de Madagascar (profondeur, type, âge, qualité, potentiel), interrogeable en un point GPS

*Rédigé le 02/11/2026, **avant** tout calcul de modèle ou de score. Protocole doctoral : modules M3 (hydrogéologie) et
M5 (impacts, accès à l'eau), expériences E3 (modèles physiques, statistiques, hybrides) et E7 (incertitudes),
validation spatiale par blocs (§11), risque 7 (données hydrogéologiques insuffisantes). Toute modification sera datée
en section 10, avant de voir les résultats concernés.*

## 1. Question et usage visé

Un foreur, une ONG ou une commune pointe un lieu sur la carte ou donne des coordonnées GPS. L'outil répond, avec une
fourchette et un niveau de confiance :

| Sortie | Unité ou classes |
|---|---|
| Profondeur probable de la nappe | m, avec un intervalle de 80 % |
| Type de nappe | alluviale ou sous-écoulement, sables côtiers, socle altéré, socle fracturé profond, grès (Isalo, Karoo), calcaires karstiques |
| Âge probable de l'eau | jeune (moins de 50 ans) ou ancienne (plus de 1 000 ans), en classes ; jamais une date |
| Salinité | conductivité probable (µS/cm) et probabilité de dépasser 1 500 et 3 000 µS/cm |
| Fluor | probabilité de dépasser 1,5 mg/L (norme OMS) |
| Potentiel | productivité probable (débit attendu d'un forage), réserve (épaisseur saturée × porosité), recharge (mm/an) |
| Confiance | élevée, moyenne ou faible selon la densité de mesures proches et l'accord entre sources |

Chaque réponse rappelle : **« Estimation pour orienter une étude, pas pour décider d'un forage. Une étude
géophysique et hydrogéologique de terrain reste nécessaire. »**

Questions de recherche :
1. Les cartes mondiales déjà publiées (profondeur de nappe, fluor, perméabilité, épaisseur du régolithe) sont-elles
   justes à Madagascar, comparées aux forages malgaches ?
2. Un modèle hybride (carte mondiale recalée sur les forages malgaches) fait-il mieux, **y compris dans des régions
   sans forage** ?
3. Quelles grandeurs restent impossibles à estimer sans mesure locale (âge de l'eau, débit) ?

## 2. Positionnement

**Couches mondiales ou continentales existantes :**
- Fan et al. (2013, *Science* 339, 940-943) : profondeur de nappe mondiale à environ 1 km, calée sur plus d'un million
  de puits, dont très peu en Afrique et à Madagascar. Version utilisée : Fan et al. (2017, *PNAS* 114, 10572), même
  modèle mis à jour (projet EartH2Observe).
- Podgorski et Berg (2022, *Nature Communications* 13, 4232) : probabilité de fluor au-delà de 1,5 mg/L, forêt
  aléatoire sur plus de 400 000 mesures, 250 m.
- Thorslund et van Vliet (2020, *Scientific Data* 7, 231) : base mondiale de conductivité de plus de 200 000 points
  d'eau souterraine.
- Huscroft et al. (2018, *GRL*), GLHYMPS 2.0 : perméabilité et porosité des formations, polygones tirés de GLiM.
- Hartmann et Moosdorf (2012, *G-cubed*), GLiM : carte lithologique mondiale.
- Shangguan et al. (2017, *JAMES*), SoilGrids : profondeur absolue du socle à 250 m.
- MacDonald et al. (2021, *Environmental Research Letters* 16, 034012) : recharge en Afrique tirée de 134 sites
  d'observation.
- Jung et al. (2024, *Water Resources Research* 60) : recharge mondiale par réseau de neurones à 0,25°.
- Atlas BGS des eaux souterraines d'Afrique : carte hydrogéologique de Madagascar au 1:5 000 000, déjà dans le
  système.

**Connaissances régionales et analogues** (`biblio_hydrogeologie_grand_sud.md`) :
- AVSF (2016) et Guyot (2002) : nappe générale profonde (150 à 200 m sous le plateau Karimbola), nappes alluviales,
  recharge épisodique.
- Carrière et al. (2023) : lissage de la recharge avec la profondeur sur le plateau Mahafaly.
- Maréchal, Dewandel et al. : modèle altérites-fissures du socle du sud de l'Inde (épaisseur des altérites = réserve,
  zone fissurée = débit).
- Taylor et al. (2013) : recharge liée aux pluies extrêmes.
- Observation de terrain du porteur du projet : rôle des failles, eaux anciennes et salées.

**Ce que ce travail ajoute :**
- l'évaluation, à Madagascar, de cartes mondiales jamais confrontées aux forages malgaches ;
- un modèle hybride validé hors des zones d'apprentissage ;
- un outil national interrogeable en un point, avec une incertitude affichée. Aucun outil équivalent n'a été trouvé
  pour Madagascar ; la méthode est transposable à d'autres pays sur socle.

## 3. Données

Les couches mondiales (section 9) sont recadrées sur Madagascar (43-51°E, 26-11,5°S). Chaque couche garde sa
résolution native ; aucune n'est rééchantillonnée plus finement.

Mesures malgaches servant de référence :
- **MGMERL** : niveaux statiques (25 271 forages recensés, environ 1 000 extraits aujourd'hui), conductivité,
  rapports techniques de forage (lithologie, profondeur, essais de pompage : exports à obtenir) et 16 séries de
  dataloggers. Citer MGMERL.
- **ACF** (relevés manuels) et **GROSoM** (observatoire du sud-ouest, Carrière et al. 2021) : à demander.
- Points malgaches de la base mondiale de salinité.
- Rapports de forage et expérience du porteur du projet : comme règles d'expert, jamais comme données inventées.

## 4. Méthode

**Référence 1, carte mondiale seule :** la valeur de la couche mondiale au point (profondeur de Fan, probabilité de
fluor de Podgorski).

**Référence 2, krigeage des seules mesures malgaches**, sans couche explicative.

**Modèle hybride** (protocole doctoral E3, forme Y = Y_mondial + correction) :
- la correction est apprise sur les forages malgaches à partir de variables explicatives : lithologie (GLiM, BGS),
  perméabilité et porosité (GLHYMPS), épaisseur du régolithe (SoilGrids), relief et hauteur au-dessus du drainage
  (GLO-90, HAND du système), distance au cours d'eau, pluie et excédent hydrique (CHIRPS, bilan du système), distance
  aux failles cartographiées ;
- forêt aléatoire avec quantiles (intervalle de 80 %) ;
- la contrainte physique (profondeur ≥ 0) est contrôlée.

**Classes non mesurables directement** (type de nappe, âge) : règles d'expert écrites à l'avance (section 6), tirées
de la littérature et des rapports de forage, et affichées comme des règles, pas comme une prédiction validée.

**Potentiel :**
- réserve = épaisseur saturée du régolithe × porosité efficace (2 à 8 % dans le socle altéré, d'après Maréchal et
  Dewandel ; porosité GLHYMPS ailleurs) ;
- débit : classes de productivité BGS, recalées sur les essais de pompage MGMERL s'ils sont obtenus ;
- recharge : comparaison de MacDonald 2021, du bilan du système et de la littérature locale (20 à 100 mm/an dans le
  Sud, BRGM 2005).

## 5. Validation (protocole doctoral §11)

- **Validation croisée par blocs géographiques** : l'île est découpée en blocs d'environ 100 km. Chaque bloc est
  prédit par un modèle qui n'a vu aucun de ses forages. Il n'y a pas de découpage aléatoire, qui serait trop optimiste
  avec des forages voisins (hypothèse H4 du protocole doctoral).
- Mesures :
  - profondeur : erreur absolue médiane, biais, couverture de l'intervalle de 80 % ;
  - salinité et fluor : score de Brier et courbe de fiabilité pour les probabilités ;
  - type de nappe : matrice de confusion, si des rapports de forage le renseignent.
- Les résultats sont publiés par grande région hydrogéologique (socle, bassin sédimentaire ouest, Sud), car les
  performances varient (hypothèse H3).

## 6. Hypothèses fixées à l'avance

- **H-C1** : la profondeur de Fan et al. a un biais significatif face aux forages malgaches (test de Wilcoxon sur
  les écarts, 5 %). Ce modèle mondial est peu calé en Afrique.
- **H-C2** : en validation par blocs, le modèle hybride a une erreur absolue médiane plus faible que la carte mondiale
  seule et que le krigeage seul, dans plus de la moitié des blocs (test du signe, 5 %).
- **H-C3** : la probabilité de fluor de Podgorski et Berg est fiable à Madagascar : écart de calibration inférieur à
  0,1 sur la courbe de fiabilité. Testable seulement si des mesures de fluor malgaches sont trouvées ; sinon, l'écrire.
- **H-C4** : la conductivité est plus élevée près des côtes et dans le socle de l'Androy qu'ailleurs (test de
  Mann-Whitney, 5 %), comme le décrivent AVSF (2016) et Rabemanana (2005).
- Règles d'expert (âge et type), écrites avant de voir les forages :
  - alluvial ou sous-écoulement : à moins de 1 km d'un cours d'eau de rang au moins 4, et profondeur de l'eau de moins
    de 15 m ;
  - eau probablement ancienne : profondeur de plus de 50 m en socle fracturé ou en grès de l'Isalo, ou forage sur une
    faille cartographiée dans une zone de pluie annuelle inférieure à 600 mm.

## 7. Limites connues

- Fan et al. disposent de très peu de puits à Madagascar : leur carte y est surtout un modèle.
- Les forages MGMERL sont regroupés autour des projets WASH, surtout dans le Sud : grands vides ailleurs, d'où la
  validation par blocs et un niveau de confiance faible loin des mesures.
- Le niveau statique mesuré dépend de la date (saison) et du pompage.
- L'âge de l'eau ne peut pas être estimé sans isotopes : l'outil ne donne qu'une classe tirée de règles, signalée
  comme telle.
- Les failles de la carte au 1:5 000 000 sont trop grossières pour un forage précis : c'est une limite majeure pour
  l'hypothèse des failles.
- Licences : Fan et al. (usage de recherche avec citation) et la carte du fluor (licence non précisée) ne sont pas
  republiées. Seuls des résultats dérivés et cités le seront.

## 8. Mise en œuvre et mises à jour automatiques

- Téléchargement : `scripts/build_nappes_mondiales.py`, workflow « 21 - Couches mondiales des nappes ». Lancement
  manuel, plus une vérification annuelle, car ces couches changent rarement.
- Couches à licence ouverte (CC BY, ODbL, OGL) : recadrées et rangées dans la version GitHub `nappes-mondiales`, avec
  leur attribution.
- Couches à licence restreinte ou non précisée : gardées dans le cache des Actions, jamais republiées.
- Le modèle et la validation feront l'objet d'un script séparé, écrit avant de voir les résultats.

## 9. Sources mondiales (vérifiées le 02/11/2026)

| Couche | Source officielle | Licence | Résolution, unité |
|---|---|---|---|
| Profondeur de nappe | Fan et al. 2017 (mise à jour de 2013), THREDDS de l'université de Saint-Jacques-de-Compostelle, `GLOBALWTDFTP/annualmeans/AFRICA_WTD_annualmean.nc` | usage de recherche libre, citation obligatoire ; redistribution non prévue | 30″ (~1 km), m, moyenne annuelle |
| Fluor | Podgorski et Berg 2022, Eawag doi:10.25678/0006GQ (`maps.zip`, 2 Go, `global_F_hazard_model.tif`) | « open data », licence non précisée | 250 m, probabilité en % (0-100) de dépasser 1,5 mg/L |
| Perméabilité et porosité | GLHYMPS 2.0, Borealis doi:10.5683/SP2/TTJNIU (`GLHYMPS.zip`, 2,6 Go) | CC BY 4.0 | polygones ; log10 k (m²), porosité |
| Lithologie | GLiM, PANGAEA doi:10.1594/PANGAEA.788537 (grille à 0,5°) | CC BY 3.0 | 0,5° (la version fine est intégrée aux polygones de GLHYMPS) |
| Profondeur du socle | SoilGrids 2017, `BDTICM_M_250m_ll.tif` (ISRIC), Shangguan et al. 2017 | ODbL (partage à l'identique) | 250 m, cm |
| Salinité | Thorslund et van Vliet 2020, PANGAEA doi:10.1594/PANGAEA.913939 (`Groundwaters_summary.csv`) | CC BY 4.0 | points, µS/cm ; **aucun point à Madagascar** |
| Recharge, Afrique | MacDonald et al. 2021, BGS doi:10.5285/45d2b71c-d413-44d4-8b4b-6190527912ff | Open Government Licence | carte de 1970-2020, mm/an ; téléchargement par formulaire BGS (non automatisable), couverture de Madagascar à vérifier |
| Recharge, monde | Jung et al. 2024 | — | **non publiée en accès libre** : le dépôt Zenodo cité ne contient que des données d'entraînement (péninsule arabique) |

## 10. Journal des modifications

- 02/11/2026 : version initiale.
- 02/11/2026, au téléchargement, **avant tout calcul de modèle ou de score** :
  - la base mondiale de salinité (Thorslund et van Vliet 2020) ne contient **aucun point d'eau souterraine à
    Madagascar**. H-C4 sera testée sur la conductivité MGMERL seule ; la base mondiale ne sert à rien ici ;
  - la carte du fluor est en pourcentage (0 à 100), pas en probabilité de 0 à 1 ;
  - dans la carte de Fan, le niveau de la nappe est négatif sous la surface. La profondeur utilisée est sa valeur
    absolue.
- 02/11/2026, **avant le calcul de H-C1**. Le porteur du projet juge trop grand l'écart entre la médiane de Fan
  (15,5 m sur toute l'île) et celle des relevés MGMERL, et demande un test point par point. Précisions fixées avant
  calcul :
  - **Relevés** : `inputs/mgmerl/mgmerl_niveau_statique.csv` (1 000 points, dont 988 forages ; extraction du
    27/10/2026). Un point est gardé si la profondeur est comprise entre 0 et 200 m et si ses coordonnées sont à
    Madagascar ; un doublon d'identifiant ne garde que le relevé le plus récent.
  - **Fan** : valeur de la maille de 1 km du point, profondeur = − valeur du fichier ; une valeur positive (eau
    au-dessus du sol, zone humide) compte comme 0 m.
  - **H-C1, test principal inchangé** : test de Wilcoxon bilatéral sur les écarts (Fan − mesure), seuil de 5 %.
  - **Contrôle de robustesse ajouté** : les forages sont regroupés autour des projets, ce qui rend le test point par
    point trop optimiste. On calcule donc aussi l'écart médian par bloc de 1° (environ 100 km), puis un test du signe
    entre blocs. H-C1 n'est déclarée solide que si les deux tests sont significatifs dans le même sens.
  - **Analyses descriptives, pour comprendre l'écart** (pas de test) :
    - position dans le relief, d'après la hauteur au-dessus du cours d'eau (HAND) au point : moins de 5 m (fond de
      vallée), 5 à 15 m, plus de 15 m. Attendu : un écart plus grand hors des fonds de vallée, car la maille de 1 km
      de Fan mélange vallée et versant ;
    - productivité de l'aquifère (carte BGS) du fokontany du point ;
    - corrélation de Spearman entre Fan et la mesure : Fan classe-t-il au moins les sites dans le bon ordre ?
  - **Publication** : seulement des statistiques par classe et par bloc. Les valeurs de Fan point par point ne sont
    pas republiées (licence).
- 02/11/2026, **avant tout calcul de recharge** : ajout de la section « Transfert de connaissances et calibration
  régionale », à partir de la note du porteur du projet
  (`validation/notes_porteur/modelisation_transfert_connaissance.txt`) et des données du BGS qu'il a téléchargées.

## 10. Transfert de connaissances et calibration régionale (recharge et paramètres des aquifères)

**Principe, proposé par le porteur du projet.** Madagascar n'a presque pas de mesures de recharge. On transfère donc
les connaissances acquises dans des zones africaines analogues, puis on les calibre sur les données malgaches
disponibles. La réserve du porteur du projet est retenue comme règle : *une géologie similaire ne signifie pas une
recharge similaire* ; le climat, les sols, le relief, la végétation et l'occupation des terres comptent aussi.

**Données (téléchargées par le porteur du projet le 02/11/2026, fichiers bruts hors git en attendant la vérification
de la licence)** :
- carte africaine de recharge à long terme (MacDonald et al. 2021), environ 0,28°. Elle couvre Madagascar : 654
  mailles, médiane 109 mm/an (Grand Sud environ 78, Nord environ 141) ;
- base de 134 sites de recharge mesurée dans 30 pays, **aucun à Madagascar**. Pour chaque site : recharge (meilleure
  estimation, basse et haute), méthode, confiance, pluie, nombre de jours de pluie, évapotranspiration potentielle,
  aridité, NDVI, groupe d'aquifère (sédimentaire 80, socle 35, non consolidé 19), sol, occupation des terres.

**Étapes :**
1. **Analogues.** Pour chaque maille malgache, on calcule les mêmes variables que dans la base (pluie CHIRPS, jours de
   pluie, ETP ERA5-Land, aridité, NDVI MODIS, groupe d'aquifère selon la carte BGS de Madagascar, sol SoilGrids,
   occupation des terres WorldCover). On cherche les sites africains les plus proches selon une distance de Gower sur
   toutes ces variables, pas sur la géologie seule. **Domaine d'applicabilité** : une maille dont le site le plus
   proche est au-delà du 95e centile des distances entre sites africains est signalée « extrapolation », avec une
   confiance faible.
2. **Bibliothèque de paramètres** (`validation/bibliotheque_parametres_aquiferes.csv`) : recharge (base BGS),
   porosité et perméabilité (GLHYMPS), porosité efficace du socle altéré et fissuré (2 à 8 %, Maréchal, Dewandel,
   sud de l'Inde), productivité (BGS), âges et salinité des analogues (section 3 ter de
   `biblio_hydrogeologie_grand_sud.md`). Chaque ligne indique la source, le pays, la formation et le niveau de
   confiance.
3. **Transfert, trois versions comparées** :
   - **T0** : la carte BGS telle quelle ;
   - **T1** : un modèle reconstruit sur les 134 sites (régression de la recharge, en logarithme, sur les variables
     ci-dessus), puis appliqué avec nos variables malgaches, plus fines ;
   - **T2** : moyenne pondérée des recharges des k sites analogues les plus proches (k = 5, poids selon la distance de
     Gower).
4. **Validation du transfert, avant Madagascar** : on laisse un pays africain de côté à chaque fois (pas de découpage
   aléatoire, protocole doctoral §11), pour mesurer ce que vaut un transfert vers un pays inconnu.
5. **Calibration et contrôle malgaches.** Références locales indépendantes :
   - fourchettes de la littérature (20 à 100 mm/an dans le Sud, BRGM 2005 ; environ 60 mm/an sur le plateau
     Mahafaly) ;
   - recharge estimée aux sites de nappe MGMERL par fluctuation de nappe, R = Sy × Δh, avec Sy tiré de la
     bibliothèque (fourchette, pas une valeur unique) ;
   - observatoire GROSoM quand ses données seront obtenues.
6. **Sorties à plusieurs niveaux** (maille, fokontany, commune, district, région), chacune avec un intervalle et un
   niveau de confiance (dans le domaine des analogues ou en extrapolation).
7. **Scénarios** : sensibilité de la recharge transférée à la pluie (±10 %, protocole doctoral E7) et aux scénarios
   climatiques, quand le module de projections existera.

**Hypothèses fixées à l'avance :**
- **H-C5** : en laissant un pays de côté, T1 ou T2 a une erreur (sur le logarithme de la recharge) plus faible que la
  référence naïve (médiane africaine). Test du signe entre pays, 5 %.
- **H-C6** : à Madagascar, au moins 60 % des références locales indépendantes tombent dans l'intervalle de 80 % de la
  meilleure version de transfert retenue en H-C5. La version est choisie **avant** la comparaison aux références
  malgaches.
- Si H-C5 échoue, aucune recharge transférée n'est publiée comme estimation : seule la carte BGS reste affichée,
  avec sa source et la mention « modèle africain non validé à Madagascar ».

**Limites propres au transfert** : peu de sites de socle (35) et surtout en Afrique australe et de l'Ouest ; pas de
site insulaire ni sous influence cyclonique comparable ; recharge de long terme (moyenne), pas année par année ;
incertitude des méthodes de mesure des sites (bilan de chlorure, fluctuation de nappe), déjà fournie par la base.

**Précisions de mise en œuvre de H-C5 (02/11/2026, fixées avant le calcul, après lecture des seules statistiques
descriptives de la base)** :
- variable modélisée : log10(R + 1), car 7 sites sur 134 ont une recharge nulle ;
- T1 : régression ridge (λ = 1) sur la pluie, les jours de pluie, l'ETP, l'aridité et le NDVI standardisés, plus le
  groupe d'aquifère et l'occupation des terres (indicatrices). Le type de sol (21 classes, souvent 1 ou 2 sites) est
  écarté de T1 pour éviter le surapprentissage ; il reste dans la distance de T2 ;
- T2 : 5 plus proches voisins selon la distance de Gower (variables numériques ramenées à leur étendue ; variables
  qualitatives : 0 si identiques, 1 sinon), poids 1 / (distance + 0,01) ;
- référence naïve : médiane de log10(R + 1) des pays d'apprentissage ;
- erreur d'un pays : médiane des erreurs absolues de ses sites (en log10) ;
- deux versions testées : chacune passe H-C5 si le test du signe entre pays donne p < 0,025 (correction de
  Bonferroni) ;
- T0 (carte BGS) ne peut pas être évaluée en laissant un pays de côté, puisqu'elle a été construite avec tous les
  sites : elle n'est donc pas candidate en H-C6 si T1 ou T2 passe H-C5.

**Précisions de mise en œuvre de H-C6 (02/11/2026, fixées avant tout calcul sur Madagascar)** :
- **Mêmes sources que la base africaine** (métadonnées du BGS), pour ne pas confondre l'écart entre sources avec
  l'effet recherché :
  - pluie, jours de pluie, ETP et aridité (pluie / ETP) : CRU TS v4, moyennes annuelles 1981-2010 ;
  - NDVI : MODIS MOD13 (MOD13C2, 0,05°), moyenne annuelle 2001-2010, MODIS commençant en 2000 ;
  - groupe d'aquifère : carte hydrogéologique de Madagascar du BGS (Africa Groundwater Atlas), codes regroupés comme
    dans MacDonald et al. 2012 : B, I, V → « Basement » ; CSF, CSI, CSIF, CSK → « Sedimentary » ; U →
    « Unconsolidated » ;
  - sol : groupe de sol de référence WRB le plus probable de SoilGrids, codé sur deux lettres comme l'Atlas des sols
    d'Afrique (AR, LP, CM…), l'Atlas n'étant pas téléchargeable librement ; écart de source documenté ;
  - occupation des terres : Globcover 2009 regroupé en cropland, grassland, sparse, shrubland, forest et urban comme
    la base ; à défaut, ESA WorldCover regroupé de la même façon, écart documenté.
- **Grille** : les 654 mailles terrestres de la carte BGS de recharge (environ 0,28°), pour comparer directement T0,
  T1 et T2.
- **Version retenue pour H-C6, choisie sur H-C5 et avant toute comparaison malgache** : T2 (erreur médiane entre pays
  la plus faible, 0,24 contre 0,28 pour T1). T1 est calculée et publiée à titre de comparaison.
- **Intervalle de 80 %** : prédiction ± les 10e et 90e centiles des résidus de T2 obtenus en laissant un pays de
  côté (H-C5), en log10(R + 1).
- **Références malgaches indépendantes** (aucune ne vient de la base BGS) et règle de comparaison : la valeur
  centrale de chaque référence est comparée à l'intervalle de 80 % de la maille (ou à l'intervalle médian des
  mailles de la zone) :
  1. Sud de Madagascar, 20 à 100 mm/an (BRGM 2005, cité par AVSF 2016) : valeur centrale 60 mm/an, comparée aux
     mailles au sud de 23°S ;
  2. plateau Mahafaly, environ 60 mm/an (profil USAID/Winrock) : mailles du plateau (calcaires éocènes de la carte
     géologique) ;
  3. sites de nappe MGMERL retenus en M3 : recharge annuelle par fluctuation de nappe, R = Sy × somme des remontées
     de saison des pluies, avec Sy de 0,01 à 0,05 dans le socle et de 0,05 à 0,15 dans le sédimentaire (bibliothèque
     de paramètres) ; valeur centrale au milieu de la fourchette.
- **H-C6 confirmée** si au moins 60 % de ces références tombent dans l'intervalle (règle fixée plus haut). Avec
  2 références de la littérature et jusqu'à 7 sites, le résultat reste indicatif ; il est publié comme tel.

**Précisions de mise en œuvre de H-C2 (02/11/2026, fixées avant le calcul ; seul H-C1 a été calculé sur ces
forages)** :
- **Mesures** : niveau statique des forages MGMERL relevé le 02/11/2026 (tableau affiché, 1 000 forages), contrôlé
  comme en H-C1 (0 à 200 m, à Madagascar, doublons -> relevé le plus récent).
- **Variables au point** :
  - profondeur de Fan (maille de 1 km) ;
  - HAND, pente et accumulation d'écoulement (logarithme), et distance au cours d'eau le plus proche (cellules dont
    l'accumulation dépasse 1 000 cellules), tirées du relief GLO-90 du système ;
  - lithologie GLiM (classe de la maille de 0,5°) ;
  - logarithme de la perméabilité et porosité GLHYMPS (polygone du point) ;
  - épaisseur des altérites, c'est-à-dire la profondeur du socle de SoilGrids ;
  - pluie annuelle normale (CHIRPS, normale du système) ;
  - altitude moyenne et rugosité de la maille de 0,1° (relief E1) ;
  - productivité de l'aquifère (carte BGS, fokontany du point).
- **Failles** : aucune carte numérique des failles de Madagascar n'est disponible dans nos sources ; la variable est
  absente de cette version. C'est une limite, compte tenu de l'observation de terrain du porteur du projet.
- **Modèle hybride** : correction = mesure − Fan, apprise par une forêt aléatoire de quantiles (bibliothèque
  quantile-forest, 500 arbres, au moins 5 forages par feuille, paramètres fixés ici sans réglage). Prédiction = Fan +
  médiane de la correction, ramenée à 0 m si elle est négative ; intervalle de 80 % = Fan + 10e et 90e centiles.
- **Krigeage** : krigeage ordinaire des seules profondeurs mesurées (bibliothèque PyKrige), variogramme exponentiel
  ajusté automatiquement sur les forages d'apprentissage.
- **Validation par blocs de 1°** : chaque bloc d'au moins 5 forages est prédit par des modèles qui n'ont vu aucun de
  ses forages. Erreur du bloc = médiane des erreurs absolues (m).
- **H-C2 confirmée** si le modèle hybride bat à la fois la carte de Fan et le krigeage dans plus de la moitié des
  blocs (deux tests du signe unilatéraux, chacun à 5 %). La couverture de l'intervalle de 80 % est publiée.

**H-C2b : extrapolation loin des forages (ajout du 02/11/2026, après le résultat de H-C2 et avant son propre calcul)**

*Statut honnête : ce test est conçu après avoir vu H-C2. Il est plus exigeant, car il mesure ce que H-C2 ne mesurait
pas (prédire loin de tout forage connu). Mais il utilise les mêmes forages : c'est donc un test complémentaire, à
confirmer plus tard sur d'autres forages.*

- **Découpage** : chaque **région administrative** comptant au moins 10 forages est laissée de côté entière. Les
  modèles (hybride et krigeage, réglages identiques à H-C2) sont appris sur toutes les autres régions.
- **Mesures** : erreur absolue de chaque forage de la région laissée de côté ; distance de chaque forage au forage
  d'apprentissage le plus proche.
- **H-C2b confirmée** si les deux conditions suivantes sont réunies :
  1. sur l'ensemble des forages des régions laissées de côté, l'erreur absolue de l'hybride est plus faible que celle
     du krigeage (test de Wilcoxon apparié, unilatéral, 5 %) ;
  2. l'hybride a l'erreur médiane la plus faible dans plus de la moitié des régions laissées de côté.
- **Analyse descriptive** : erreurs des deux méthodes par classe de distance au forage d'apprentissage le plus proche
  (0-25, 25-50, 50-100, plus de 100 km). Attendu : l'erreur du krigeage croît avec la distance plus vite que celle de
  l'hybride.
- La carte de Fan seule est rapportée à titre de référence.

