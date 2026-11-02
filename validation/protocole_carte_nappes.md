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

