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


## 09/11/2026 : base BushProof / DDC « Contribution à l'hydrogéologie du Sud de Madagascar » ; chlorure de la pluie

### 1. Conditions d'utilisation (citées mot pour mot)

- Page d'accueil https://hydro-madagascar.weebly.com/, rubrique « Condition d'utilisation et citation » (lue le
  09/11/2026) : « Toutes les données sur ce site sont libres d'accès et peuvent être librement utilisées. Il est par
  contre interdit de les vendre ou de s'en approprier la propriété intellectuelle. Ces données sont mises à la
  disposition du public grâce au soutien de la Direction du Développement et de la Coopération de la Confédération
  suisse, Berne et de BushProof Sàrl, Antananarivo. » Même page, rubrique « Méthodologie » : « Toutes les données
  regroupées pour la réalisation de ces travaux sont libre d'accès et doivent être mises à disposition de tous. »
- Citation demandée (même page et `Citation_référence.pdf` du dépôt de fichiers) : « Al-Zoubaidy M., Monteleone M. et
  Bünzli, M. - A., 2023, Contribution à l'hydrogéologie du Sud de Madagascar, Base de données géoréférencées et site
  interactif https://hydro-madagascar.weebly.com/ ; Editeurs: Direction pour le Développement et la Coopération,
  Berne et BushProof Sàrl, Antananarivo. » Le PDF de citation donne une seconde forme avec l'adresse
  qgis.bushproof.com.
- qgis.bushproof.com : simple index Apache de fichiers, sans autre condition. Le catalogue des données (PDF de
  66 pages) n'en contient pas non plus. Le billet RWSN du 09/10/2023
  (https://rwsn.blog/2023/10/09/hydrogeology-of-southern-madagascar-new-mapping-tool/) reprend les mêmes conditions
  en anglais. Aucune licence nommée (ni CC ni autre).

### 2. Téléchargement : serveur disparu, copies partielles de la Wayback Machine

- **Échec du serveur d'origine** : `https://qgis.bushproof.com/content/Hydro%20Sud%20Madagascar/?`, 3 essais
  (06 h 03, 06 h 06 et 06 h 16 UTC) : `curl: (6) Could not resolve host: qgis.bushproof.com`. Confirmé par deux
  résolveurs publics : `*** dns.google can't find qgis.bushproof.com: Non-existent domain` (8.8.8.8), même réponse
  avec 1.1.1.1 ; `bushproof.com` résout toujours (50.6.5.9). Le sous-domaine a été supprimé.
- **Wayback Machine** : index du répertoire capturés de 2023 à septembre 2024. Le dernier index (19/09/2024) liste :
  `Cartes thématiques/`, `Catalogue des données_Hydrogéologie Sud Madagascar_2023.pdf` (4,5 Mo),
  `Citation_référence.pdf`, `Geopacakages QGIS/`, `Présentation_…_2023.pdf` et `Références_…_2023.pdf`. **Aucun
  fichier Excel** dans l'index racine ni dans les captures ; l'index du dossier `Geopacakages QGIS/` n'est pas
  archivé (« The Wayback Machine has not archived that URL »). **La base Excel n'est donc pas récupérable.**
- **Geopackages archivés (captures de mars 2024) : tous coupés à 1 048 576 octets** (1 Mio). La troncature vient
  de la capture elle-même : les PDF de 4,7 Mo arrivent entiers. SQLite refuse de les ouvrir (« database disk image
  is malformed ») et la version installée de `sqlite3` (3.50.6) n'a pas `.recover` (« unknown command »).
  Récupération partielle par lecture directe des pages SQLite (`scripts/sqlite_tronque.py`) : une couche est
  complète si aucune page de son arbre ne manque.

| Fichier (dans `data/mdg/bushproof_raw/`, ignoré par git) | Pages présentes | Contenu lisible |
|---|---|---|
| `Hydrogeologie.gpkg` | 256 / 1 108 | Econd générale 2 046 / 2 048, Econd basses eaux 1 039 (complète), Econd hautes eaux 338 (complète), 3 couches de direction d'écoulement ; **Forages : 65 / 2 880** (349 pages manquantes) ; couches de piézométrie absentes |
| `Carte_thematique_ZH20.gpkg` | 256 / 915 | forages exploités 685 + abandonnés 111, failles, dykes : **complets** |
| `Carte_thematique_ZH30.gpkg` | 256 / 545 | 6 couches de forages (267) : **complètes** |
| `Carte_thematique_ZH40.gpkg` | 256 / 757 | 5 couches de forages (400) : **complètes** |
| `Climat.gpkg` | 256 / 52 400 | stations (24), isohyètes 2009-2013, tableau P-ETI ; le reste manque |
| `Geographie.gpkg` | 256 / 121 251 | 105 communes ; le reste manque |
| `Catalogue_donnees_2023.pdf`, `Citation_reference.pdf` | entiers | descriptions des couches, citation |

- **Échecs Wayback** (3 essais par URL, 2 min d'écart) :
  - `Geologie.gpkg` : `curl: (56) Recv failure: Connection was reset`, puis deux fois `curl: (6) Could not resolve
    host: web.archive.org` ;
  - `Hydrologie.gpkg` : trois réponses HTTP 429 ;
  - `Carte_thematique_ZH10.gpkg` : deux séries de 3 essais (429, `curl: (6) …`, `curl: (56) schannel: server closed
    abruptly (missing close_notify)`, 429).

  Les 429 (« Too Many Requests ») sont venus malgré une seule requête à la fois. Le résolveur DNS local a aussi
  échoué par intermittence (`DNS request timed out`).
- **Firecrawl** : crédits épuisés (« Insufficient credits for this connected-app request ») ; pages lues avec curl.

### 3. Inventaire (`data/mdg/bushproof_inventaire.json`, sans donnée brute ; `scripts/bushproof_inventaire.py`)

- **Forages réunis** : 1 487 forages distincts (dédoublonnés par ID) sur 2 880 annoncés. Les zones ZH20 (820),
  ZH30 (267) et ZH40 (400) sont complètes ; **la zone ZH10 manque** (son fichier n'a pas pu être téléchargé).
  Emprise : 43,874 à 46,600 E ; −25,508 à −23,038. Régions : Atsimo Andrefana et Androy.
- **152 colonnes** (liste dans le JSON) ; colonnes clés : `Cl-_mg/l`, `DateChimie`, `NO3-_mg/l`, `EC_µ/cm`, `SWL_m`,
  `DateSWL`, `QPal1…5_m3/h`, `Rabat1…5_m`, `Qexpl_m3/h`, `Tran_m2/s`, `TypeAquif1…3`, `Lat_DD`, `Long_DD`,
  `Région`, `ZH_code`, `Alt_DEM_m`, `NivPiezo_m`.
- **Chlorure** : 559 forages avec Cl mesuré et positif (aucune valeur censurée « < »), dont 558 avec une date de
  chimie et 516 avec du nitrate. Par type d'aquifère (`TypeAquif1`) : fracturé 536, poreux 10, fissuré 2, non
  renseigné 11, karstique 0. Par région : Atsimo Andrefana 311, Androy 248.
- **Unité du chlorure : mg/L, vérifiée** de trois façons :
  - nom de la colonne ;
  - page Hydrogéologie du site : « Cl-_mg/l= Concentration de ion chlore en mg/l » ;
  - balance ionique calculée en mg/L sur 556 analyses complètes : erreur médiane −1,8 %, 85 % des analyses à moins
    de 10 %. En meq/L, la balance serait fausse.
- **Types d'aquifère (tous forages)** : fracturé 639, poreux 26, fissuré 2, karstique 2, non renseigné 818.
- **Autres effectifs** :
  - date de chimie : 980 ;
  - nitrate : 517 ;
  - conductivité : 1 133 ;
  - niveau statique : 1 121, dont 734 datés ;
  - essai de pompage (débit et rabattement du 1er palier) : 551 ;
  - débit d'exploitation : 620.
- **Basses eaux et hautes eaux : 0 forage mesuré aux deux saisons.** La table n'a qu'un `SWL_m`/`DateSWL` et une
  `DateChimie` par forage, et les couches saisonnières en sont des sous-ensembles. Vérifié sur les couches de
  conductivité (complètes) : 1 039 forages en basses eaux, 338 en hautes eaux, aucun identifiant commun. Les couches
  de piézométrie saisonnières (734 et 215 annoncés) ne sont pas dans la partie lisible, mais elles sont construites
  de la même façon (« forages possédant une mesure de niveau statique prise durant les périodes de saison sèche »).
- **Quantiles du chlorure (10, 50 et 90 %, par type et par région) : calculés mais scellés** dans
  `data/mdg/bushproof_inventaire_cl_scelle.json` (ignoré par git, non affiché). Le protocole
  `validation/protocole_recharge_chlorure.md` (section 4) impose de choisir le dépôt de chlorure avant toute lecture
  des chlorures de la nappe.
- **Biais** : la zone ZH10 manque, et les zones ZH20 à ZH40 sont presque uniquement du socle fracturé (536 des
  559 forages avec Cl). Avec ces données, le test ne pourra rien dire du karst (H-Cl3).

### 4. Chlorure dans la pluie : sources trouvées

Aucune mesure publiée du chlorure de la pluie dans le Sud de Madagascar n'a été trouvée.

| Source | Ce qui est vérifié | Valeurs |
|---|---|---|
| Rabemanana V., Violette S., de Marsily G., Robain H., Deffontaines B., Andrieux P., Bensimon M., Parriaux A. (2005). Origin of the high variability of water mineral content in the bedrock aquifers of Southern Madagascar. *Journal of Hydrology* 310, 143-156, doi:10.1016/j.jhydrol.2004.11.025 | résumé seulement (notices EPFL et manuscript.isc.ac) : sels marins apportés par la pluie, concentrés par évaporation ; conductivités de 300 à 30 000 µS/cm | aucune valeur pour la pluie ; texte intégral payant. La thèse (Rabemanana 2002, Paris VI) est sur le serveur IRD, « Site en maintenance » ce jour |
| Van Wyk E., van Tonder G. J., Vermeulen D. (2011). Characteristics of local groundwater recharge cycles in South African semi-arid hard rock terrains: rainwater input. *Water SA* 37(2) | texte intégral en ligne (SciELO), lu par extraction automatique : à recontrôler sur le PDF | pluie d'été de l'intérieur : 0,3 à 0,5 mg/L (moyennes harmoniques de 0,4 en pointe, 0,8 en début et 1,0 en saison sèche) ; côte du Cap : 3,5 à 16,8 mg/L ; Langebaan Road : 5 à 10 mg/L ; dépôt total de 260 mg/m²/an (Kuruman, Beaufort West, Vryburg, Pretoria Est), dont environ 80 mg/m²/an de dépôt sec ; dépôt sec « approximately 400 mg·m2·yr-1 » pour l'Afrique australe (d'après Eriksson 1960 et Gieske 1992). Pas d'équation en fonction de la distance à la côte |
| Guan H., Love A. J., Simmons C. T., Makhnin O., Kayaalp A. S. (2010). Factors influencing chloride deposition in a coastal hilly area and application to chloride deposition mapping. *HESS* 14, 801-813, doi:10.5194/hess-14-801-2010 (CC BY 3.0) | **PDF lu** (tableau 1) | Mount Lofty, Australie du Sud, 17 sites : 3,7 à 12,2 mg/L et 1,33 à 6,97 g/m²/an ; la distance à la côte explique 70 % de la variabilité. Analogue de méthode, sous un climat différent |
| Banks E. W., Cook P., Owor M., Kebede S., Mleta P., Bonsor H., MacDonald A. (2018). Chloride deposition in rainfall to estimate regional groundwater recharge in Africa. EGU2018-14713 (CC BY 4.0) | **résumé lu** | revue des mesures africaines d'au moins un an, en vue d'une carte régionale ; aucune valeur ; publication finale non trouvée |
| Ferrer N., Folch A., Thomas M. (2019). Gro for GooD project Chloride rainwater results, Kwale County, Kenya. BGS, doi:10.5285/e5c1dd99-f97b-4670-9d78-c2ae6133a722 (Open Government Licence) | fiche lue | chlorure mensuel de la pluie (mg/L), 11 stations, avril 2016 à novembre 2017, côte du Kenya (océan Indien occidental) ; **valeurs non lues** (accès par la page d'accessions BGS, en JavaScript) |
| Vet R. et al. (2014). A global assessment of precipitation chemistry and deposition… *Atmospheric Environment* 93, 3-100, doi:10.1016/j.atmosenv.2013.10.060 | notice seulement | cartes mondiales des ions majeurs annoncées ; figures non vues |
| GROSoM (Carrière et al. 2021, *Hydrol. Process.* 35:e14108 ; Carrière et al. 2023, *Hydrogeology Journal* 31, 2337-2346) | résumés | isotopes et piézométrie ; **aucune mesure de chlorure de la pluie** trouvée (Wiley : HTTP 403 ; Springer : authentification ; IRD en maintenance) |
| Fareze L. P. et al., Isotope characterization of shallow aquifers in the Horombe region (arXiv:1204.1500) | **PDF lu** | isotopes de la pluie, pas de chlorure de la pluie |

Pistes non abouties :
- thèses de Rabemanana (2002), Garo (2012) et Guyot (2002) ;
- rapport JICA de 2006 (le DNS de openjicareport.jica.go.jp a échoué ce jour) ;
- données de Kwale, à obtenir par la page d'accessions du BGS.

### Fichiers produits ou modifiés

| Fichier | Statut git |
|---|---|
| `data/mdg/bushproof_raw/` (7 geopackages tronqués, 2 PDF, CSV récupérés dans `recuperation/`) | ignoré (`data/*/bushproof_raw/`, vérifié par `git check-ignore`) |
| `data/mdg/bushproof_inventaire.json` | versionnable (effectifs et colonnes seulement) |
| `data/mdg/bushproof_inventaire_cl_scelle.json` | ignoré (quantiles scellés) |
| `scripts/bushproof_inventaire.py`, `scripts/sqlite_tronque.py` | nouveaux, non commités |
| `.gitignore` | trois lignes ajoutées, non commité |

## 09/11/2026 : chlorure de la pluie (Kwale, Van Wyk et al. 2011), pour fixer le dépôt de chlorure

But : fixer le dépôt de chlorure du protocole `validation/protocole_recharge_chlorure.md` (section 4) **avant** toute
lecture des chlorures de la nappe. Le fichier scellé `data/mdg/bushproof_inventaire_cl_scelle.json` n'a pas été
ouvert. Rythme : une requête à la fois par serveur, sans relance automatique. Une coupure réseau (ENOTFOUND) a
interrompu la session ; le travail a repris sans perte (fichier Kwale déjà téléchargé).

### 1. Kwale (côte du Kenya) : données téléchargées et recalculées

- **Source** : Ferrer N., Folch A., Thomas M. (2019), BGS, doi:10.5285/e5c1dd99-f97b-4670-9d78-c2ae6133a722.
  **Licence OGL vérifiée** sur la fiche DOI et sur l'accession (« Contains data supplied by UKRI »).
- **Accès** : la page d'accessions est en JavaScript, mais son API est publique :
  `https://webservices.bgs.ac.uk/accessions/items/125757` (métadonnées) puis
  `.../accessions/download/125757?fileName=GroforGooD_Rainwater%20Chloride_ARCH.xlsx` (22 952 octets, HTTP 200).
- **Contenu** : 11 stations, pluie mensuelle (mm) et Cl mensuel (mg/L), avril 2016 à novembre 2017, coordonnées en
  UTM Arc 1960 zone 37S (EPSG:21037). Le fichier dit « mm/d », mais ce sont des cumuls mensuels (jusqu'à 795 mm).
- **Méthode** (`scripts/chlorure_pluie_kwale.py`) :
  - Cl pondéré par la pluie = Σ(P·C)/ΣP sur les mois où P et C sont connus ;
  - dépôt = Cl pondéré × pluie de décembre 2016 à novembre 2017 ;
  - distance à la côte : conversion en WGS84, puis distance euclidienne en UTM 37S au trait de côte Natural Earth
    10 m (domaine public, téléchargé). Précision d'environ 1 km.
- **Résultats** :

| Station | Distance à la côte (km) | Échantillons Cl | Cl pondéré (mg/L) | Pluie avr. 2016-nov. 2017 (mm) | Pluie déc. 2016-nov. 2017 (mm) | Dépôt (mg/m²/an) | Fiabilité |
|---|---|---|---|---|---|---|---|
| MSD Msambweni | 1,0 | 9 | 4,00 | 1 938 (3 mois manquants) | 814 (incomplète) | 3 256 | bonne |
| GZW Gazi | 1,8 | 4 | 0,99 | 1 836 | 1 344 | 1 337 | faible |
| KIN Kinondo | 1,8 | 6 | 3,43 | 1 896 | 1 280 | 4 393 | faible |
| FHM Fahamuni | 2,7 | 3 (2 utilisables) | 2,03 | 1 389 | 1 143 | 2 326 | très faible (7 % de la pluie couverte) |
| PS14 KISCOL | 3,3 | 4 | 1,27 | 2 461 | 1 601 | 2 040 | faible |
| MWK Muhaka | 5,7 | 4 | 1,55 | 2 254 | 1 463 | 2 266 | faible |
| PS13 KISCOL | 5,9 | 4 | 1,56 | 2 359 | 1 555 | 2 424 | faible |
| BTC Base Titanium | 8,6 | 15 | 2,40 | 1 921 (1 mois manquant) | 1 112 (incomplète) | 2 665 | bonne |
| MWC Mwachande | 9,6 | 17 | 2,18 | 2 427 | 1 528 | 3 334 | bonne |
| SH Shimba Hills | 12,9 | 16 | 1,78 | 2 017 | 1 389 | 2 478 | bonne |
| FTP Foot Print | 15,1 | 13 | 1,93 | 1 948 | 1 264 | 2 435 | bonne |

  Stations fiables (5) : Cl pondéré médian **2,2 mg/L** (1,8 à 4,0) ; dépôt médian **2 665 mg/m²/an**. Toutes
  stations : 1,0 à 4,0 mg/L, 1 337 à 4 393 mg/m²/an. Pas de gradient net au-delà de 3 km sur 15 km.
- **Douteux** : FHM 2017-02 (44,6 mg/L pour 1 mm), BTC 2017-02 (31,6 mg/L pour 7 mm), KIN 2017-07 (12,8 mg/L pour
  0 mm, impossible), MWC 2016-07 (21,8 mg/L), MSD 2016-06 (19,1 mg/L) ; pluie de GZW en avril 2016 (4,2 mm contre 178
  à 618 mm ailleurs) ; valeurs de juin 2016 arrondies à une décimale. Leur poids est faible : sans les mois de moins de
  10 mm, les moyennes bougent de moins de 0,15 mg/L, sauf FHM. Type de collecteur (humide ou bulk) non précisé.

### 2. Van Wyk et al. (2011), Water SA 37(2), 147-154 : vérifié sur le PDF

PDF SciELO (`/pdf/wsa/v37n2/v37n2a03.pdf`) et figure 2 (`a03fig02m.jpg`) téléchargés et lus. Les valeurs de
l'entrée du 09/11 (section 4 ci-dessus) sont **confirmées**, avec leurs pages :
- intérieur, pluie d'été (moyennes harmoniques) : 0,8 mg/L au début, 0,4 en pointe, 1,0 en saison sèche, pour 30, 65
  et 5 % de la pluie (p. 152) ; pointe de 0,3 à 0,5 mg/L sur 19 stations (p. 152, figure 2 p. 153) ; tableau 1
  (p. 150) : 0,44 mg/L en été, 2,67 mg/L en hiver ;
- côte : Cap 3,5 à 16,8 mg/L, Langebaan Road 5 à 10 mg/L (p. 152, tableau 4) ; **côte nord du KwaZulu-Natal (océan
  Indien) : 3,3 / 4,9 / 5,4 mg/L** (début, pointe, sec ; lu sur la figure 2, p. 153) ;
- dépôt total de 260 mg/m²/an (Kuruman, Beaufort West, Vryburg, Pretoria Est), dont environ 30 %, soit
  80 mg/m²/an, de dépôt sec (p. 153 et 154) ; « approximately 400 mg·m2·yr-1 » de dépôt sec cité d'après Eriksson
  (1960) et Gieske (1992), source secondaire (p. 153) ;
- **aucune équation en fonction de la distance à la côte** : seulement « almost an order of magnitude higher » sur
  la côte (p. 154).

### 3. Autres mesures dans l'océan Indien occidental

Aucune mesure du chlorure de la pluie trouvée pour Madagascar, le Mozambique, Maurice, les Comores ou la Tanzanie.
Pistes notées dans `data/mdg/chlorure_pluie.json` :
- application « RainfallChloride » (Hydrogeological Repository, bêta, licence non indiquée) : 85 sites
  sud-africains, Cl = exp(1,866 − 0,192·ln(1+d) − 0,000446·z + décalage selon la convention de mesure). Non vérifiée ;
- La Réunion : Join (1991) et Grünberger (1989) attribuent le chlorure des nappes aux pluies, mais aucune valeur de
  pluie n'a été trouvée.

Échecs : CORE (core.ac.uk) HTTP 403 ; AJOL HTTP 403 ; SciELO en HTTP : réponse vide, puis succès en HTTPS.

### Fichiers produits ou modifiés

| Fichier | Statut git |
|---|---|
| `data/mdg/chlorure_pluie_raw/` (xlsx et métadonnées Kwale, trait de côte Natural Earth, PDF, HTML et figure de Van Wyk) | ignoré (`data/*/chlorure_pluie_raw/`, vérifié par `git check-ignore`) |
| `data/mdg/chlorure_pluie.json` | versionnable (valeurs agrégées, références, licences, statut de vérification) |
| `scripts/chlorure_pluie_kwale.py` | nouveau, non commité |
| `.gitignore` | deux lignes ajoutées, non commité |

## 09/11/2026 : dépôt atmosphérique de chlorure (MERRA-2, littérature), pour situer les trois scénarios

But : une estimation du dépôt de chlorure (mg/m²/an) dans le Grand Sud (lon 43 à 47,5 ; lat −25,7 à −22,5)
indépendante des choix de `validation/protocole_recharge_chlorure.md`. Résultat : **MERRA-2 non calculé** (compte
Earthdata absent de ce poste) ; script, tests et workflow prêts ; aucune mesure malgache trouvée.

### 1. MERRA-2 : collection et variables vérifiées, téléchargement bloqué

- **Spécification lue** (Bosilovich, Lucchesi et Suarez 2016, GMAO Office Note No. 9 v1.1, PDF téléchargé) : les
  dépôts de sel de mer sont dans **tavg1_2d_adg_Nx / tavgM_2d_adg_Nx (M2TMNXADG, « Aerosol Diagnostics (extended) »)**,
  p. 25-26, et **non dans aer_Nx (M2TMNXAER)**, qui ne porte que masses et épaisseurs optiques (p. 29). Variables, en
  kg m⁻² s⁻¹, 5 classes de taille chacune : SSDP001-005 (dépôt sec), SSWT001-005 (dépôt humide), SSSV001-005
  (lessivage convectif), SSSD001-005 (sédimentation). DOI M2TMNXADG : 10.5067/RZIK2TV7PP38 (tableau 6.2, p. 59).
  CMR : collection C1276812865-GES_DISC, granules `MERRA2_x00.tavgM_2d_adg_Nx.AAAAMM.nc4`.
- **Accès** : l'ancien OPeNDAP (goldsmr4) répond **410** ; l'OPeNDAP cloud (opendap.earthdata.nasa.gov) répond **302
  vers /login/urs** (un essai chacun). Les scripts du projet lisent `EARTHDATA_USER` / `EARTHDATA_PASSWORD`, qui
  n'existent que comme **secrets GitHub** : absents de l'environnement local (vérifié sans afficher de valeur), pas de
  `.netrc`. Lancer un workflow avec un nouveau script supposerait un commit et un push, exclus ici.
- **Prêt à lancer** : `scripts/depot_chlorure_merra2.py` (sous-ensemble DAP4 de 10 × 10 mailles, 240 mois 2001-2020,
  une requête par mois pour les 20 variables, 3 essais au plus espacés de 30 s, jeton Bearer comme MOD13C2 ;
  chlorure = 0,55 × sel de mer, Millero et al. 2008 : 19,352 / 35,165 g/kg) ; `tests/test_depot_chlorure_merra2.py`
  (8 contrôles, 0 échec) ; `.github/workflows/build-depot-chlorure-merra2.yml` (workflow 29, sonde d'abord).
  Suite : commit, `gh workflow run build-depot-chlorure-merra2.yml -f sonde=true` (vérifier le format CSV), puis
  `-f sonde=false`, puis en local `python scripts/depot_chlorure_merra2.py --part synthese` (distance à la côte,
  classes, mise à jour de `data/mdg/depot_chlorure.json`). File NASA : après les tâches déjà en attente.
- Déjà calculé : sur la grille MERRA-2, **39 mailles** de l'emprise ont leur centre sur terre (Natural Earth 10 m) :
  10 à moins de 30 km de la côte, 15 entre 30 et 100 km, 14 au-delà (jusqu'à 219 km).

### 2. Scénarios du protocole à P = 500 mm (D = P × Cl_p(d) × (1 + s), mg/m²/an)

| Scénario | 10 km | 30 km | 100 km | 200 km |
|---|---|---|---|---|
| bas | 426 | 187 | 150 | 150 |
| central | 1 098 | 690 | 302 | 261 |
| haut | 3 736 | 3 195 | 1 964 | 1 197 |

### 3. Littérature locale

- **Carrière et al. 2023**, Hydrogeology Journal 31:2337-2346 (accès libre) : **vérifié sur la source**. Aucune chimie
  de la pluie ; chlorure seulement en rapport Cl/Br des nappes (fig. S4, matériel supplémentaire non téléchargé) ; le
  suivi de la pluie « has not been carried out until now due to the access difficulties of the area » (p. 2345) ;
  pluie d'environ 400 mm près de la côte (p. 2338).
- **Rabemanana et al. 2005**, J. Hydrol. 310:143-156 : **non vérifié**. Notice Infoscience EPFL 116948 sans PDF,
  notice HAL bioemco-00396172 sans fichier, résumé retiré par l'éditeur (OpenAlex, Semantic Scholar).
- **Fareze et al. 2016** (Mahafaly, hal-01476517) et **Carrière 2024** (HDR, tel-04791954, CC BY-NC) : résumés lus
  par l'API HAL (recharge d'environ 60 mm/an par le tritium pour Fareze ; pas de chlorure de la pluie) ; PDF bloqués
  par la protection anti-robots de HAL (y compris via WebFetch). **Non vérifié** au-delà des résumés.
- **Rahobisoa 2006** (mémoire, Université d'Antananarivo, Morondava, hors zone) : serveur injoignable, 3 essais.
- Recherche web (WebSearch) indisponible (limite atteinte) ; recherches faites par les API OpenAlex, Crossref, HAL et
  Semantic Scholar (un refus 429, réussite au second essai).

### 4. Comparaison (sans conclusion sur la recharge)

Aucune valeur MERRA-2 pour l'instant. Avec la littérature déjà vérifiée (Kwale transposé à 500 mm : 900 à 1 200
mg/m²/an à 3-15 km sans dépôt sec ; intérieur sud-africain de Van Wyk : 260 mg/m²/an), le **scénario central** est le
plus proche (1 098 à 10 km, 261 à 200 km) ; bas trop faible près de la côte, haut 4 à 5 fois trop fort à l'intérieur.
**Comparaison circulaire** : ces sources ont servi à fixer les scénarios ; seul MERRA-2 donnera un contrôle indépendant.

### Fichiers produits ou modifiés

| Fichier | Statut git |
|---|---|
| `data/mdg/depot_chlorure_raw/` (PDF de Carrière et al. 2023 et son texte) | ignoré (`data/*/depot_chlorure_raw/`, vérifié par `git check-ignore`) |
| `data/mdg/depot_chlorure.json` | versionnable (valeurs agrégées, références, licences, statut de vérification) |
| `scripts/depot_chlorure_merra2.py`, `tests/test_depot_chlorure_merra2.py` | nouveaux, non commités |
| `.github/workflows/build-depot-chlorure-merra2.yml` | nouveau, non commité |
| `.gitignore` | deux lignes ajoutées, non commité |

## 09/11/2026 (après-midi) : GLiM vectorielle, fin du téléchargement, découpe Madagascar, licence

### 1. Téléchargement

- Reprise du fichier partiel (241 713 152 octets) par `curl -L -C - --ssl-no-revoke --retry 3 --retry-delay 30`, un
  seul téléchargement à la fois. Dropbox a accepté la reprise à chaque fois (`code=206`, `type=application/binary`).
  Deux coupures : `curl: (56) Recv failure: Connection was reset` (à 279,6 Mo, 12 h 56) et `curl: (56) schannel:
  server closed abruptly (missing close_notify)` (vers 998 Mo) ; `--retry` ne relance pas sur l'erreur 56, d'où une
  boucle de reprise (30 s de pause, 40 essais au plus ; 2 utilisés). Débit de 70 à 200 ko/s.
- **Fichier complet à 14 h 09 : 1 138 691 332 octets (taille annoncée exacte)**, signatures `PK\x03\x04` et fin de
  répertoire central présentes ; `zipfile.testzip()` : aucun CRC faux, 47 entrées (`LiMW_GIS 2015.gdb/...`).
  Journal : `data/mdg/nappes_mondiales/glim_vecteur_telechargement.log` (ignoré).

### 2. Inspection et découpe

- Sous Git Bash, le chemin `/vsizip/...` est réécrit par MSYS (échec : « does not exist in the file system ») ;
  solution : `MSYS_NO_PATHCONV=1` et chemin absolu avec le dossier interne :
  `/vsizip/C:/Users/user/Makyclimat/data/mdg/nappes_mondiales/glim_vecteur_raw/LiMW_GIS_2015.gdb.zip/LiMW_GIS 2015.gdb`.
- `scripts/glim_vecteur_inspect.py` : une couche `GLiM_export` (MultiPolygon), **1 235 259 polygones**, projection
  World Eckert IV (ESRI:54012), champs `IDENTITY_`, `Litho`, `xx`, `Shape_Length`, `Shape_Area`.
- `scripts/glim_vecteur_mdg.py ... GLiM_export glim_vecteur_mdg.gpkg glim_vecteur_surfaces.json` (emprise 43-51 E,
  26-11,5 S ; surfaces en Albers équivalente centrée sur Madagascar) : **2 243 polygones** (2 239 `MDG`, 4 `AFR`),
  **592 833 km²** au total.

| Classe (xx) | km² | % |
|---|---|---|
| mt (métamorphiques) | 238 889 | 40,30 |
| pa (plutoniques acides) | 81 596 | 13,76 |
| ss (silicoclastiques) | 81 462 | 13,74 |
| su (sédiments meubles) | 76 262 | 12,86 |
| sm (sédimentaires mixtes) | 67 753 | 11,43 |
| vb (volcaniques basiques) | 32 907 | 5,55 |
| va (volcaniques acides) | 5 542 | 0,93 |
| pb (plutoniques basiques) | 4 527 | 0,76 |
| **sc (carbonates)** | **2 092** | **0,35** |
| pi (plutoniques intermédiaires) | 1 024 | 0,17 |
| wb (eau) | 761 | 0,13 |
| nd (non défini) | 18 | 0,00 |

- **Carbonates.** `sc` ne contient qu'une sous-classe, `scpumt` (carbonates purs associés aux métamorphiques, c'est-à-
  dire marbres et cipolins du socle) : 2 091,8 km², 65 polygones, surtout entre 45 et 47 E et 20 et 22 S. **Les
  karsts sédimentaires connus ne sont pas en `sc`** : des points tests à Bemaraha (44,75 E ; 18,8 S), Ankarana
  (49,1 ; 12,9), Namoroka (45,35 ; 16,4), plateau Mahafaly (43,9 ; 24,0) et Toliara (43,75 ; 23,4) tombent tous en
  `smmx` (sédimentaire mixte). La carte source de la GLiM pour Madagascar a donc regroupé les calcaires
  sédimentaires avec d'autres roches : **`sc` ne peut pas servir de masque karstique**, et la GLiM ne permet pas de
  contrôler les mailles fkarst de Wan et al. 2024. Elle confirme seulement que la côte est (Mananara-Masoala) n'a pas
  de carbonates cartographiés hors marbres du socle (à vérifier maille par maille si utile).
- Sorties : `data/mdg/nappes_mondiales/glim_vecteur_surfaces.json` (agrégats, versionnable sous réserve de la
  licence ci-dessous) ; `glim_vecteur_mdg.gpkg` (géométries, ignoré par `*.gpkg`) ; `glim_vecteur.json` mis à jour.

### 3. Licence des polygones

- **Vérifié** : la page de l'Université de Hambourg n'indique ni licence ni conditions (seulement « © 2026 University
  of Hamburg. All rights reserved » pour le site) ; la fiche CCGM du produit (https://ccgm.org/en/wp-json/wp/v2/product/863)
  donne le lien Dropbox et « ©CCGM-CGMW 2015 », crédite Moosdorf et Hartmann, sans licence ni conditions d'usage ;
  PANGAEA (doi:10.1594/PANGAEA.788537) : CC BY 3.0 pour la seule grille à 0,5°. Pour un autre produit SIG de la CCGM
  (carte géologique du monde au 1/35 M, https://ccgm.org/en/?p=588), un contrat de licence signé est exigé avant
  l'envoi du lien : rien de tel pour la carte lithologique, diffusée par lien public.
- **Non vérifié** : page CSDMS (accès refusé à l'outil de lecture), mention de données dans l'article de 2012, texte
  du contrat de licence générique de la CCGM. Recherche Firecrawl impossible (crédits épuisés) ; faite avec WebSearch
  et WebFetch.
- **Conclusion** : droits « ©CCGM-CGMW 2015 » sans licence ouverte ; aucune géométrie dans le dépôt. Des surfaces
  agrégées citant Hartmann et Moosdorf (2012) et la CCGM (2015) paraissent acceptables, mais ce n'est pas confirmé.
