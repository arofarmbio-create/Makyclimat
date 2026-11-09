# État des téléchargements (agent de téléchargement)

*Tenu par l'agent de téléchargement depuis le 02/11/2026, décision du porteur du projet : un seul agent pour tous les
téléchargements et liaisons API, petit à petit, sans demandes forcées ni simultanées auprès d'un même fournisseur.
Mis à jour à chaque étape. Dernière mise à jour : 03/11/2026, 08 h 45 UTC.*

## Règles de rythme appliquées

| Fournisseur | Règle | Où elle est appliquée |
|---|---|---|
| Copernicus CDS et EWDS | Une seule demande à la fois pour tout le compte, toutes familles confondues. Ménage des demandes orphelines (`scripts/cds_menage.py`, plus de 30 min en file) avant chaque série. Ordre : ERA5-Land E1, puis ERA5-Land mensuel (SPEI), puis indice MCT (ERA5 850 hPa), puis GloFAS (EWDS), puis C3S | `common.cds_retrieve`, workflow 20 (tâche era5), workflow 22, lancement manuel dans cet ordre |
| CHIRPS (CHC) | Au plus 2 téléchargements simultanés, une tâche à la fois, attente de 60 à 300 s sur les refus 429. Les années E1 attendent hors des créneaux de la mise à jour du site (HH:05-HH:50 toutes les 6 h) et du bilan hydrique (03:35-04:00 UTC) | `common.download`, `build_e1_sources.part_chirps`, workflow 20 (tâche chirps, max-parallel 1) |
| NASA GES DISC (IMERG) | Une tâche à la fois, requêtes séquentielles (0,5 s entre deux), attente de 60 à 300 s sur 503 ou coupure, arrêt après 10 jours de suite en échec | `build_e1_sources.part_imerg` et `fetch_imerg_day`, workflow 20 (tâche imerg, max-parallel 1) |
| AppEEARS (NDVI), NOAA (GSOD, PSL), Amazon S3 (GLO-90) | Une demande à la fois | workflows 19, 20, 8 ; calcul local du relief (3 tuiles à la fois) |

## État par source

| Source | Fournisseur | Attendu | Obtenu | Manque | Dernière erreur et cause | Statut |
|---|---|---|---|---|---|---|
| E1 CHIRPS journalier | CHC | 2001-2026 (26 ans) | 2001-2025 | 2026 (année incomplète) | — | ✅ ; 2026 au passage mensuel (25/11), sans forcer |
| E1 IMERG Late journalier | NASA GES DISC | 2001-2026 | 2001-2025 | 2026 (année incomplète) | — | ✅ ; 2026 au passage mensuel |
| E1 ERA5-Land journalier | Copernicus CDS | 2001-2026 | 2001-2026 | — | — | ✅ |
| E1 stations GSOD | NOAA NCEI | 2001-2026, stations de Madagascar | 24 stations | — | — | ✅ |
| E1 relief (altitude, rugosité, exposition) | Amazon S3 (GLO-90) | grille 0,1° | 5 432 mailles terrestres | — | — | ✅ `data/mdg/e1/relief_01deg.npz`, calculé sur ce PC le 02/11 |
| SPEI : pluie par district | CHC | 1981-2025 | oui | — | — | ✅ |
| SPEI : NDVI par district | AppEEARS (NASA) | 2000-2025 | version d'octobre | mise à jour en cours | — | ⏳ (run 41406634717) |
| SPEI : ET0 ERA5-Land mensuelle | Copernicus CDS | 1981-2025 | `et0_districts.csv` (release secheresse-series) | — | la validation qui suit (`validate_spei_ndvi.py`, `control_et0`, ligne 117) échoue en lisant `et0_cache.json` : erreur de calcul, pas de téléchargement, signalée au coordinateur | ✅ données (run 41579128422) |
| Indice MCT (ERA5 850 hPa) | Copernicus CDS | déc.-févr. 1981-2025 | — | tout | — | ⏳ lancé le 03/11 (run 41581251323) |
| Reprévisions GloFAS v4 | Copernicus EWDS | 21 saisons x 6 mois = 126 mois | 18 mois | 108 mois | file d'attente pleine (années lancées 2 par 2, 01/11) ; puis en concurrence avec ERA5-Land | ⏸ mis en pause le 02/11 (run 41411661636 annulé) : après l'indice MCT |
| R-02 bis : IMERG V07 Final demi-horaire, 7 activations EMS | NASA GES DISC | 7 événements (77 jours au total, environ 3 700 requêtes) | — | tout | — (script, fenêtres et workflow 23 prêts, testés) | ⏸ en attente : après IMERG E1 et IMERG pilote, un événement à la fois |
| R-02 bis : rafales ERA5 (instantaneous_10m_wind_gust) | Copernicus CDS | 7 fenêtres, emprise de Madagascar | — | tout | — (même script, partie « rafales ») | ⏸ en attente : file Copernicus, après l'indice MCT |
| H-C6 : covariables de la recharge BGS | UEA/CRU, BGS, ISRIC, ESA, NASA | 654 mailles de 0,28° | toutes les colonnes : climat CRU, Aquifer_group, GLG, Soil_group, Landcover, NDVI MOD13C2 2001-2010 (120 mois sur 120) | — | — | ✅ `data/mdg/nappes_mondiales/covariables_hc6.csv` complet le 03/11 |
| SEAM, données publiques du ministère de l'Eau (MEAH) | seam.meah.gov.mg | résumés, points d'eau et systèmes AEP par région (24), tableau, indicateurs ODD | 52 fichiers JSON bruts (6,7 Mo) : 86 049 points d'eau et 5 173 systèmes, conformes aux totaux des résumés | — | Python refuse le certificat (certificat intermédiaire non envoyé par le serveur) ; curl sous Windows complète la chaîne et la valide. Vérification jamais désactivée | ✅ `data/mdg/seam_raw/` (hors git), GET seulement, une requête à la fois, 3,5 s d'écart, le 03/11 |
| Prévisions C3S (10 systèmes) | Copernicus CDS | 10 systèmes | 0 | 10 | demande bloquée 5 h sans livraison, qui gênait ERA5-Land | ⏸ en pause depuis le 02/11 : en dernier |
| IMERG demi-horaire, périmètre pilote | NASA GES DISC | 11 saisons (2014-2024) | 2014, 2015, 2017, 2018, 2022, 2023, 2024 | 2016 (en cours), 2019, 2020, 2021 | — | ⏳ une saison à la fois (run 41583633699) |
| ONI, DMI, SIOD, MOZ (ERSST) | NOAA | mensuel depuis 1950 | ONI, DMI, SIOD et MOZ (921 mois, jusqu'à 2026-09) | — | prévision saisonnière Open-Meteo du même workflow : délai dépassé (TimeoutError), sans lien avec ERSST | ✅ SIOD et MOZ produits et commités le 02/11 (workflow 8, run 41444771537) ; la prévision Open-Meteo se refera lundi |
| Niveaux de nappe HT Analytics | MGMERL (dossier partagé) | 16 sites | 16 séries (juin 2025) | Water Missions, Lorentz, relevés ACF | — | ✅ manuel, hors git |
| Rapports de forage, exports MGMERL | MGMERL (api.mwater.co) | lithologie, essais de pompage | — | tout | l'extension Chrome n'a pas le droit d'accéder à api.mwater.co | ⛔ décision humaine : autoriser le site dans l'extension |

## Journal des actions de l'agent

- 02/11, 12 h 25 UTC : sonde IMERG lue ; cause de la lenteur trouvée (concurrence). Code séquentiel, attentes et arrêt de
  sécurité, testés ; lancement E1 précédent annulé et relancé avec une seule année IMERG à la fois.
- 02/11, 12 h 30 UTC : créneaux CHIRPS ajoutés au workflow 20 ; relief E1 calculé sur ce PC ; script et workflow de
  l'indice MCT prêts ; GloFAS et IMERG pilote mis en pause pour respecter la règle « un fournisseur à la fois ».
- 02/11, 12 h 50 UTC : R-02 bis préparé (fenêtres des 7 cyclones dans `validation/r02bis_fenetres.csv`, script
  `build_r02bis_sources.py`, workflow 23 manuel, tests). Placé dans les files NASA et Copernicus, non lancé.
- 02/11, 16 h 30 UTC : reprise après la pause. Contrôle des premières données : CHIRPS 2001 (Toamasina 2 964 mm,
  Toliara 437 mm), IMERG Late 2001 (Toamasina 1 452 mm), ERA5-Land 2015 (Ivato 1 829 mm). Ce sont des écarts connus
  (IMERG Late sous-estime la côte est, ERA5-Land surestime les Hautes Terres) : utiles pour E1, pas des erreurs de
  téléchargement. ERA5-Land découpé en une tâche par année ; CHIRPS 2026 relancé.

## Suite de la file (à lancer dans cet ordre, quand l'étape précédente est finie)

| File | Après | Lancement |
|---|---|---|
| Copernicus | ERA5-Land E1 (run 41482839480) | 1. `gh workflow run build-drought-spei-ndvi.yml` (ET0 mensuelle) ; 2. `gh workflow run build-mct-era5.yml` ; 3. `gh workflow run build-r02bis-sources.yml -f part=rafales` ; 4. `gh workflow run build-glofas-reforecast.yml -f years="2003 2004 … 2023"` ; 5. `gh workflow run build-c3s-seasonal.yml` |
| NASA GES DISC | IMERG E1 (run 41444684197) | 1. `gh workflow run build-imerg-pilot.yml -f seasons="2015 2016 2019 2020 2021"` (code pilote rendu séquentiel le 02/11 : 1 fil, attente de 30 à 180 s) ; 2. `gh workflow run build-r02bis-sources.yml -f part=imerg` |
- 02/11, 17 h 40 UTC : covariables H-C6 produites. Licences : CRU TS v4.10 (ODbL, citation Harris et al. 2020 ; les
  bases dérivées restent sous ODbL), SoilGrids (CC BY 4.0), carte hydrogéologique BGS de Madagascar (CC BY-SA), ESA
  WorldCover (CC BY 4.0) ; Globcover 2009 inaccessible (serveur ESA), donc WorldCover, indiqué dans la colonne
  Landcover_source. La recharge BGS (MacDonald et al. 2021) vient du fichier déposé par le porteur du projet ; sa
  licence est à confirmer par le coordinateur.
- 03/11, 05 h 10 UTC : E1 complet (CHIRPS et IMERG 2001-2025, ERA5-Land 2001-2026, GSOD). ETP ERA5-Land du SPEI
  obtenue. NDVI MOD13C2 : 120 sous-ensembles DAP4 au lieu de 11 Go de fichiers mondiaux, avec un jeton Earthdata ;
  lancé. Indice du canal de Mozambique lancé. Ensuite, côté NASA : IMERG pilote puis IMERG R-02 bis ; côté
  Copernicus : rafales R-02 bis, GloFAS, C3S.
- 03/11, 06 h UTC : colonne NDVI de H-C6 prête (moyenne 0,53 ; forêt 0,76, prairie 0,45 ; corrélation de 0,69 avec la
  pluie CRU). IMERG pilote relancé (5 saisons, une à la fois). Indice MCT en cours côté Copernicus.
- 03/11, 08 h 45 UTC : SEAM téléchargé (52 fichiers). Le premier passage s'était arrêté sur le dernier fichier, à
  cause d'un contrôle trop strict (réponse précédée de sauts de ligne, pourtant valide) ; ce fichier a été repris
  une seule fois. L'indice MCT tourne depuis 3 h 44 sans résultat (file Copernicus probable), et sa limite de 4 h
  approche.

## 09/11/2026 : GLiM vectorielle, licence de la carte géologique nationale, part karstique (Wan et al. 2024)

### 1. GLiM vectorielle (Hartmann et Moosdorf 2012)

- **Source.** PANGAEA (doi:10.1594/PANGAEA.788537, https://doi.pangaea.de/10.1594/PANGAEA.788537) ne contient que la
  version grillée à 0,5° (37,8 ko ; licence affichée : « Creative Commons Attribution 3.0 Unported (CC-BY-3.0) »). La
  version en polygones est donnée par la page de l'Université de Hambourg
  (https://www.geo.uni-hamburg.de/en/geologie/forschung/aquatische-geochemie/glim.html) : « The original GIS data are
  downloadable using the link of CCGM.ORG », lien Dropbox
  https://www.dropbox.com/s/9vuowtebp9f1iud/LiMW_GIS%202015.gdb.zip?dl=0, fichier `LiMW_GIS 2015.gdb.zip`
  (géodatabase ESRI, 1 138 691 332 octets annoncés). C'est la version SIG de la *Lithological Map of the World*
  (CCGM 2015), fondée sur GLiM v1.1 d'après CSDMS (https://csdms.colorado.edu/wiki/Alldata:GLiM), et non v1.0 ou v1.2.
- **Licence.** Non vérifiée pour les polygones : ni la page de Hambourg ni le lien Dropbox n'indiquent de licence ;
  la carte imprimée est vendue par la CCGM. CC BY 3.0 n'est vérifiée que pour la grille 0,5° de PANGAEA. Avant de
  publier des géométries, confirmer la licence ; publier des surfaces agrégées en citant la source paraît sans risque.
  Le service ArcGIS Online « World Lithology » (même GLiM) n'est pas une solution : service image, licence « Esri
  Master License Agreement », abonnement d'organisation requis.
- **Téléchargement.** Un seul téléchargement, sans parallélisme. Débit très faible : 7 à 65 ko/s (la connexion
  locale ne dépasse pas ~37 ko/s sur un serveur de test). Le premier curl a été arrêté à 26,9 Mo, puis relancé
  après 35 s en processus détaché avec reprise (`curl -C -`, PID 18632) pour qu'il survive à la session. À 08 h 37
  (heure locale), 47,8 Mo sur 1 139 Mo ; fin estimée vers 13 h. Journal :
  `data/mdg/nappes_mondiales/glim_vecteur_telechargement.log` (et `.log.err`). **La découpe Madagascar et les
  surfaces (dont la classe `sc`) ne sont donc pas encore calculées.**
- **À lancer à la fin du téléchargement** (vérifier d'abord que la taille vaut 1 138 691 332 octets et que le
  `.log` contient `code=200` ou `code=206`) :
  `.venv/Scripts/python.exe -I scripts/glim_vecteur_inspect.py "/vsizip/data/mdg/nappes_mondiales/glim_vecteur_raw/LiMW_GIS_2015.gdb.zip"`
  (nom de la couche et des champs), puis
  `.venv/Scripts/python.exe -I scripts/glim_vecteur_mdg.py <source> <couche> data/mdg/nappes_mondiales/glim_vecteur_mdg.gpkg data/mdg/nappes_mondiales/glim_vecteur_surfaces.json`,
  et reporter les chiffres dans `glim_vecteur.json`. geopandas 1.2.0 et pyogrio 0.13.0 sont installés ; fiona ne
  l'est pas (inutile).
- **Git.** Le dossier `glim_vecteur_raw/` n'était pas ignoré : ajout de `data/*/nappes_mondiales/glim_vecteur_raw/`
  et `data/*/nappes_mondiales/glim_vecteur_telechargement.log*` dans `.gitignore` (vérifié par `git check-ignore`).
  Le `.gpkg` est déjà ignoré ; `glim_vecteur.json` (métadonnées, provisoire) est versionnable comme `glim.json`.

### 2. Licence de la carte géologique nationale (PGRM)

- **Auteurs et diffuseurs.** La carte à 1/1 000 000 (Roig, Tucker, Delor, Peters, Théveniaut 2012) a été faite par
  le BRGM et l'USGS (et non BGS–USGS–GLW, qui ont fait les feuilles à 1/100 000 du Nord et du Centre), sur
  financement de la Banque mondiale, pour le ministère des Mines (PGRM). BRGM : « trois cartes papier assorties d'une
  notice générale [...] également fournies sous formes de bases de données numériques au sein d'un SIG »
  (https://www.brgm.fr/fr/reference-projet-acheve/synthese-geologique-miniere-madagascar). La carte imprimée est
  vendue par la CCGM (fiche https://ccgm.org/en/wp-json/wp/v2/product/1218, sans prix ni licence affichés).
- **Seule mention de droits trouvée** (page de garde de la notice explicative BRGM/PGRM, contrat n° 1493, lue sur une
  copie Scribd, donc source secondaire : https://fr.scribd.com/document/813873858/2-Notice-Mada-Million) :
  « Ce document est la propriété du PGRM et ne peut être reproduit ou communiqué sans son autorisation ».
- **Feuilles à 1/100 000 (BGS).** NORA (https://nora.nerc.ac.uk/id/eprint/6517/) les publie comme cartes du
  « Ministère de l'énergie et des Mines, Projet de Gouvernance Minérales (PGRM) », Antananarivo ; seule une fiche
  « Information only » est téléchargeable ; l'URL officielle `http://www.pgrm.mg/` ne répond plus
  (`curl: (6) Could not resolve host: www.pgrm.mg`).
- **Distribution actuelle.** OMNIS (https://omnis.mg/database/mining/?lang=en) annonce « data consultation; samples
  Consultation; data sales » pour des données géologiques en raster, vecteur et tableaux, sans prix ni licence en
  ligne (renvoi à des « guides and procedures »). Le site du ministère (https://www.mines.gov.mg/) ne montre rien de
  lisible sans JavaScript. Aucune licence ouverte ni téléchargement SIG sans inscription trouvés (BRGM, USGS, BGS,
  Banque mondiale).
- **Conclusion.** Vérifié : propriété du PGRM (ministère), reproduction et communication soumises à autorisation
  (d'après la notice) ; diffusion numérique par vente (OMNIS). Non vérifié : prix, texte d'une licence, droit de
  publier des résultats agrégés. Par prudence : ne rien redistribuer de la carte dans le dépôt public ; des résultats
  agrégés (surfaces, statistiques par sous-bassin) supposeraient l'accord écrit du ministère, à demander par le
  porteur du projet. Recherche écourtée : crédits Firecrawl épuisés en cours de route (« Insufficient credits for
  this connected-app request »), suite faite avec WebSearch et WebFetch.

### 3. Part karstique mondiale à 0,5° (Wan, Döll et Müller Schmied 2024)

- **Source.** API figshare https://api.figshare.com/v2/articles/23592666 : version 3 du 13/01/2024, titre « Global-scale
  groundwater recharge modeling is improved by tuning against ground-based estimates for karst and non-karst areas »
  (différent du titre annoncé), licence **CC BY 4.0 vérifiée** (https://creativecommons.org/licenses/by/4.0/),
  doi:10.6084/m9.figshare.23592666.v3.
- **Fichier téléchargé** (un seul ; les deux Excel déjà présents n'ont pas été repris) :
  `3_Updated_grid_mean_GWR_recharge_factors.csv`, 12 470 002 octets, md5 `7400dd6111d0ddcb6b01f41683b5aeea`
  (identique à celui de l'API), dans `data/mdg/analogues/recharge_mondiale/figshare_23592666/` (ignoré :
  `data/*/analogues/`). Colonnes utiles : `fkarst`, `fkarstlandmax`, `fland`, `Rg_grid`, `Rg_wwh`, `Rg_land`,
  `Recharge_mmpa`, `prep_cont_w5e5`. Le sens de `Rg_grid` (recharge mise à jour, avec karst) et de `Rg_wwh` (recharge
  WaterGAP d'origine) est déduit des noms et des valeurs, pas d'une documentation : à confirmer dans l'article.
  `Recharge_mmpa` (estimations au sol) est vide pour toutes les mailles malgaches.
- **Extraction** (`scripts/fkarst_mdg.py`) : `data/mdg/nappes_mondiales/fkarst_mdg.csv`, 261 mailles avec des terres
  (`fland > 0`). **fkarst > 0 : 97 mailles ; > 0,1 : 71 ; > 0,3 : 48 ; > 0,5 : 23.** Recharge moyenne : `Rg_grid`
  342 mm/an, `Rg_wwh` 301 mm/an.
- **Repérage approximatif des mailles fkarst > 0,3** (centres de maille ; attribution indicative) : plateau Mahafaly et
  région de Toliara (43,75 à 44,25 E ; −22,75 à −24,75 S : 0,58 à 0,84) ; Bemaraha et Manambolo (44,25 à 44,75 E ;
  −18,75 à −19,75 : 0,40 à 0,83) ; bassin de Mahajanga, Namoroka et plateaux éocènes (45,25 à 47,25 E ; −15,25 à
  −16,75 : 0,31 à 0,89) ; extrême nord, Antsiranana, Montagne des Français, Ankarana (49,25 à 49,75 E ; −12,25 : 0,38
  et 0,90, mais la maille à 0,90 n'a que 3 % de terres) ; sud du socle (45,75 à 46,75 E ; −22,25 à −22,75 : 0,38 à
  0,58) et côte est, Mananara-Masoala (48,75 à 49,25 E ; −15,25 à −16,75 : 0,32 à 0,49), **douteux** car ce sont des
  terrains cristallins (marbres locaux ou erreur de la carte des karsts utilisée) : à contrôler avec la GLiM vectorielle.

### Fichiers produits ou modifiés le 09/11

| Fichier | Statut git |
|---|---|
| `data/mdg/nappes_mondiales/glim_vecteur_raw/LiMW_GIS_2015.gdb.zip` | ignoré (téléchargement en cours) |
| `data/mdg/nappes_mondiales/glim_vecteur.json` | versionnable, provisoire (chiffres à compléter) |
| `data/mdg/analogues/recharge_mondiale/figshare_23592666/3_Updated_grid_mean_GWR_recharge_factors.csv` | ignoré |
| `data/mdg/nappes_mondiales/fkarst_mdg.csv` | ignoré (motif `*.csv`) ; sous CC BY 4.0, donc versionnable si on le souhaite |
| `scripts/glim_vecteur_inspect.py`, `scripts/glim_vecteur_mdg.py`, `scripts/fkarst_mdg.py` | nouveaux, non commités |
| `.gitignore` | deux lignes ajoutées, non commité |

