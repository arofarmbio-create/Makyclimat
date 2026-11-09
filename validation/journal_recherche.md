# Journal de recherche : réussites, échecs et décisions

*Tenu à jour à chaque étape, pour la thèse et la soutenance (jury : Nations Unies, gouvernement, BNGRC ; prévue vers
avril 2027). Chaque entrée est datée, dit ce qui a été tenté, ce qui a marché ou échoué, et pourquoi. Un échec
documenté est un résultat. Les résultats chiffrés détaillés sont dans les fichiers cités ; la synthèse
méthodologique est `validation/methodologie_these.md`, et les limites antérieures au 29/10/2026 y sont déjà décrites
(section 6).*

Légende : ✅ réussite · ❌ échec · ⚠️ réussite partielle ou réserve · 🔧 correction · 📌 décision

---

## 29/10/2026

### Comptes et accès aux données
- ✅ Comptes NASA Earthdata, Copernicus CDS et Copernicus EWDS vérifiés par une vraie requête chacun (workflow 12),
  sans afficher les secrets.
- ❌ puis 🔧 Le serveur CHIRPS a été réorganisé le 28/10 (`CHIRPS-2.0/` déplacé vers `CHIRPS/v2.0/`). Toutes les
  mises à jour automatiques du site ont échoué pendant environ 9 heures. Les adresses ont été corrigées dans les
  trois fichiers concernés, après vérification que les quatre types de fichiers existent bien à la nouvelle adresse.
  **Leçon :** une dépendance à une adresse externe peut casser sans prévenir. Une surveillance de l'échec des mises à
  jour est nécessaire (à faire).
- ⚠️ Les crédits Firecrawl (recherche web) sont épuisés. La recherche bibliographique passe par un autre moteur.

### Prévision de crue d'ensemble (cahier des charges §8 approche 3, §11)
- ✅ Ensemble GloFAS (contrôle + 50 membres, 30 jours) branché via Open-Meteo, sur exactement les mêmes points de
  rivière que les seuils de crue, pour les 171 communes ayant un seuil valide. Le site affiche la probabilité de
  dépasser les crues de 2, 5 et 20 ans à côté du niveau d'alerte. Une seule récupération par jour (cache), pour
  respecter la limite d'appels. Vérifié en production : 51 membres, 171 communes.
- 📌 Le niveau d'alerte reste celui du scénario de contrôle, la méthode déjà validée. La probabilité l'accompagne sans
  le modifier tant que sa fiabilité n'est pas mesurée (voir le chapitre suivant).

### Chapitre « vérification par l'impact » (GloFAS contre DesInventar)
- ✅ Recherche bibliographique : aucune évaluation publiée de GloFAS pour Madagascar n'a été trouvée. Travaux les
  plus proches : Ouganda et Kenya (Mitheu et al. 2025, avec stations), Mali (Kuipers et al. 2026), et une
  prépublication sur les crues cycloniques en Afrique australe (2025, par événement). Positionnement écrit dans
  `protocole_verification_impact.md`.
- ✅ Base DesInventar Madagascar (UNDRR, fiches BNGRC) trouvée et lue : 2 402 fiches, dont 2 086 au niveau district,
  toutes rattachées aux districts actuels (district de 2011 découpé ; région Vatovavy-Fitovinany renommée).
- 📌 Aucune licence de données explicite n'existe pour DesInventar : les fiches brutes ne sont jamais republiées (même
  règle que pour EM-DAT). Seuls des décomptes agrégés le sont.
- ❌ puis 🔧 Premier essai de téléchargement EWDS refusé : deux paramètres étaient mal nommés.
- ✅ Essai réussi : un mois d'anciennes prévisions pèse 101 Mo et demande environ 9 minutes. Après réduction
  (mailles de rivière, maximum par fenêtre d'échéance), il ne pèse plus que 8,5 Mo, sans perte pour l'usage prévu.
- ❌ Les anciennes prévisions GloFAS v4 n'existent sur EWDS qu'**à partir de 2003**, et non de 1999. Vérifié par
  l'API de contraintes. **Conséquence mesurée :** aucune perte de vérité terrain, car aucune fiche de 1999-2002
  n'était utilisable (datée au jour, au district, avec impact).
- ❌ **Qualité des données d'impact :** 87 des 88 fiches cycloniques de 2018 (et 1 de mai 2017) portent comme date
  d'événement leur date de saisie (juin-juillet 2018, hors saison cyclonique), sans code GLIDE ni commentaire. Elles
  sont impossibles à attribuer à Ava (janvier) ou Eliakim (mars). 📌 Elles sont exclues, sans attribution supposée.
  ✅ Une règle de détection transférable a été écrite et testée.
  **Résultat en soi :** une base de pertes nationale peut contenir des dates de saisie à la place des dates
  d'événement. Tout usage pour la vérification doit le contrôler.
- ⚠️ La vérité terrain utilisable compte 425 fiches, mais seulement environ 19 épisodes indépendants, presque tous
  cycloniques. Une seule saison (2003-2004) en fournit 112. Les incertitudes seront larges, et l'hypothèse H4 (crues
  non cycloniques, 18 fiches) sera difficile à trancher.
- ✅ Script de vérification, tests et protocole écrits avant tout calcul. Téléchargement des 21 saisons en cours.

### Chapitre « prévision saisonnière hybride » (C3S multi-modèles + ENSO/IOD)
- ✅ Dix systèmes de prévision saisonnière C3S (8 centres) ont des rétroprévisions 1993-2016 lancées en octobre ;
  vérifié par l'API.
- ❌ puis 🔧 Avec le produit « moyenne d'ensemble », le CDS ne propose que les années de prévision, pas les
  rétroprévisions. Le téléchargement passe par les membres individuels.
- ✅ Protocole (hypothèses H1-H3, approche principale fixée d'avance), téléchargeur et validation écrits. Exécution en
  cours.

### Chapitre « intensité infra-journalière » (IMERG)
- ✅ IMERG V07 Final, au pas de 30 min, couvre 1998 à septembre 2025.
- ❌ L'accès local au serveur NASA était instable (délais dépassés). 🔧 Tous les essais passent par GitHub Actions.
- ❌ puis 🔧 Le lecteur OPeNDAP attendait un autre format de ligne. Corrigé et testé sur une vraie réponse.
- ⚠️ La saison 2025-2026 (Fytia) n'est pas couverte par IMERG Final. Il faudra la version « Late » pour l'inclure.
- ✅ Protocole fixé avant calcul : même produit pour toutes les durées, afin d'isoler l'effet de la durée.
  Téléchargement des 11 saisons en cours.

### Chapitre « SPI ou SPEI face au NDVI » (sécheresse agricole)
- ✅ Le manque documenté le 27/10 (pas de vrai SPEI faute de série d'évapotranspiration) est levé grâce au compte CDS :
  ET0 Penman-Monteith FAO-56 calculée depuis ERA5-Land. Contrôle : l'exemple 17 du guide FAO-56 est retrouvé à 2 %
  près (5,61 contre 5,72 mm/jour).
- ❌ puis 🔧 Un test automatique a montré que la paramétrisation log-logistique de Vicente-Serrano (2010) échoue pour un
  échantillon faiblement asymétrique vers la gauche : la moitié des mois restaient vides. Elle est remplacée par la
  loi logistique généralisée de Hosking, celle du paquet SPEI de référence. **Leçon :** tester les cas limites avant
  les données réelles a évité un SPEI faux.
- ✅ NDVI MODIS (MOD13C2) via AppEEARS, et protocole fixé avant calcul (districts secs et humides).

### Produit sous-saisonnier (§9)
- ✅ Tendance des crues à 2-4 semaines (jours 17-30) tirée de l'ensemble GloFAS déjà récupéré chaque jour, publiée au
  **district et à la région seulement**, conformément au §9 (pas de prévision déterministe par commune). Testée.
- ⚠️ Sa fiabilité n'est pas mesurée : nos anciennes prévisions s'arrêtent à 15 jours d'échéance. Les mesurer à 16-30
  jours demandera de télécharger les échéances 16 à 30 (à faire, même workflow).

### Mises à jour automatiques
- ✅ 16 workflows programmés (de 6 h à annuel), calendrier dans `README.md` (section 8). La vérification des sources
  est hebdomadaire : elle aurait signalé le déplacement de CHIRPS. Les comptes NASA et Copernicus sont vérifiés chaque
  mois.
- 📌 Garde-fous : une validation programmée ne publie rien sur des données incomplètes. C3S ajoute chaque octobre la
  prévision de l'année sans retélécharger les rétroprévisions.

### Planification à 12 mois (saison 2027-2028)
- ✅ Module construit, protocole fixé avant calcul (quatre épreuves de fiabilité, dont le RPSS des probabilités).
  Personnes en sécheresse, cibles et personnes sous pluies excessives publiées par zone, avec médiane et fourchette.
- ❌ puis 🔧 Deux défauts trouvés par les tests sur données simulées, avant les données réelles :
  - les poids n'étaient pas égaux sans signal ;
  - une moyenne pouvait sortir de sa fourchette, d'où le passage à la médiane.
- 📊 **Résultat sur données réelles : aucune région sur 24 n'a de signal de pluie validé à 12 mois**, pour aucune
  période ni aucun modèle (MSSS médian −0,03 à −0,08 ; RPSS médian −0,01 à −0,05).
  L'outil affiche donc des **scénarios climatologiques** chiffrés.
  **Résultat de thèse :** la limite de prévisibilité réelle de la pluie régionale à Madagascar se situe entre 3 mois
  (3 régions sur 24 avec le modèle El Niño / océan Indien) et 12 mois (aucune région).
- ✅ Contexte physique robuste : après les 8 années El Niño comparables à 2026 depuis 1950, l'année suivante n'a jamais
  été El Niño (4 La Niña, 4 neutres). La **phase** El Niño est prévisible à 12 mois ; son **effet sur la pluie
  régionale** ne l'est pas à cette échéance.

### Couverture des besoins des décideurs (bilan du 29/10/2026)
- ✅ De la prévision à la décision (qui, quelles cultures, quand) : largement couvert.
- ⚠️ Anticipation El Niño / La Niña : couvert, avec une compétence démontrée seulement dans quelques régions.
- ❌ Priorisation des investissements (coût-bénéfice des mesures d'adaptation) : absente. Un module de
  coût-efficacité « et si ? » est proposé, avec la réserve scientifique que la forêt réduit les crues petites et
  moyennes, pas les crues extrêmes (FAO et CIFOR 2005).

### Organisation
- 📌 Chaque nouveau chapitre a un protocole écrit **avant** tout calcul de score, avec un journal daté des
  modifications. Les ajustements imposés par les données y sont consignés avant de voir les résultats.
- 📌 Toute source de données utile au système doit se mettre à jour automatiquement (exigence du porteur du projet,
  29/10/2026). Voir la section « Mises à jour automatiques » de `README.md`.

## 02/11/2026

### Cadre : protocole doctoral
- 📌 Le protocole doctoral du 31/10/2026 (`protocole_doctoral_modelisation_climatique_Madagascar.txt`) devient le cadre
  prioritaire. `prompt_maitre.md` reste en vigueur et a été aligné sur lui : section 0 (priorité), modules M0-M7,
  échelles N1-N4, données hydrogéologiques et projections CMIP6, modèles hybrides et ablations (E3), trois types de
  simulation et règle d'absence de fuite temporelle (E4), sensibilité (E7), hypothèses H1-H6, reproductibilité,
  risques, et documentation obligatoire des méthodes et résultats, échecs compris (section 21). La numérotation des
  sections 1 à 17 est conservée, car le code et les notes y renvoient.

### Mises à jour automatiques
- ❌ puis 🔧 Depuis le 01/11, la mise à jour principale échouait au contrôle qualité (« données de pluie trop anciennes,
  186 jours »). Cause : au début de la saison (1er novembre), CHIRPS n'a encore rien publié pour la nouvelle saison ;
  le pipeline affiche alors la saison précédente (jusqu'au 30/04), comme prévu, mais le contrôle mesurait l'âge depuis
  le 30/04. L'âge est désormais compté depuis le début de la saison en cours ; le seuil de 75 jours est inchangé.
  **Leçon :** un garde-fou doit être testé sur les transitions de calendrier, pas seulement en pleine saison.

### État des lieux et registre (protocole §19 et §22)
- ✅ `validation/etat_des_lieux_registre.md` : réponses aux cinq questions du protocole, registre de 34 méthodes avec
  leurs résultats (réussites et échecs), couverture des modules M0-M7 et des expériences E1-E7.
- 📊 **Constat de résolution :** 74 % des 17 465 fokontany (surface médiane 12,6 km²) sont plus petits qu'une maille
  CHIRPS (~30 km²). La pluie publiée au fokontany a donc la résolution de la maille, pas celle du fokontany.
- ❌ **Quatre chapitres lancés le 29/10 n'ont encore aucun résultat**, bloqués par des téléchargements : GloFAS
  2005-2011 (limite de 6 heures), C3S (tâche annulée après 6 heures), IMERG (6 saisons sur 11, serveur NASA), ET0
  ERA5-Land (requête refusée par le CDS). Ils deviennent la priorité.
- ⚠️ Manques principaux face au protocole : aucune station (DGM ou hydrométrique), pas de projections CMIP6, pas
  d'expérience E1 de fusion, pas de validation spatiale par blocs, pas de séparation explicite reconstitution,
  anticipation et en cours d'événement.

### Chapitres bloqués : causes trouvées et corrigées
- ❌ puis 🔧 **ERA5-Land (SPEI, R-24) et GloFAS (vérification par l'impact, R-21)** : le refus « job rejected » venait
  de Copernicus : « Maximum number queued requests for this dataset has been reached. Please configure your scripts to
  request data sequentially ». Les relances successives du 29/10 et les années GloFAS lancées deux par deux
  remplissaient la file d'attente du compte. Sur GloFAS, 2012 à 2023 « réussissaient » en 2 minutes sans rien
  télécharger : seuls 17 mois sur 126 étaient faits. 🔧 Toutes les requêtes Copernicus passent par une même
  fonction qui attend 15 minutes et réessaie (6 fois) quand la file est pleine (`common.cds_retrieve`, testée) ;
  GloFAS télécharge une année à la fois. **Leçon :** une tâche « réussie » doit être vérifiée par ce qu'elle a
  produit, pas par son statut.
- ❌ puis 🔧 **C3S (prévision hybride, R-22)** : la tâche a tourné 6 heures et a été arrêtée sans rien garder, car
  les fichiers n'étaient publiés qu'à la fin. 🔧 Chaque système est publié dès qu'il est téléchargé, et un lancement
  chaque mercredi complète les systèmes manquants.
- ❌ puis 🔧 **IMERG (R-23)** : 6 saisons sur 11 échouées sur « liste des fichiers inaccessible » (coupures du
  serveur NASA de plus d'une minute). 🔧 Attente portée à environ 18 minutes avant d'abandonner.

### Expérience E1 : fusion et qualité des sources de pluie
- ✅ Recherche bibliographique **avant** le protocole. Travaux déjà publiés : Ollivier et al. (2023, J. Hydrol. Reg.
  Stud. 47) fusionnent 21 produits contre 24 pluviomètres au pas mensuel, et la fusion l'emporte ; Randriatsara et al.
  (2022, Int. J. Climatol.) comparent 15 jeux de 1983 à 2015, et CHIRPS a les biais les plus faibles. 📌 E1 ne refait
  donc pas leur comparaison. Elle ajoute :
  - l'échelle de 5 jours ;
  - une erreur estimée partout sans pluviomètre (triple collocation, jamais appliquée à Madagascar d'après la
    recherche) ;
  - une évaluation par les impacts ;
  - uniquement des sources disponibles en temps quasi réel.
- ✅ Protocole écrit avant tout téléchargement : `validation/protocole_e1_fusion_pluie.md` (hypothèses H1-E1 et H3-E1,
  apprentissage 2001-2015 et test 2016-2025, critère principal KGE par pentade).
- ✅ 25 stations synoptiques GSOD (NOAA) actives à Madagascar ont été trouvées. ⚠️ Contrôle du 02/11 : jusqu'à 60 % des
  jours d'une station (Ivato, 2015) portent le drapeau « I » (aucune pluie déclarée, sans certitude) ; Toliara n'a que
  3 jours en 2024. 📌 Le drapeau « I » sera traité comme manquant, pas comme zéro. Le compter comme zéro aurait
  faussé la référence.
- 📌 Autres stations à obtenir : la DGM (démarche du porteur du projet), les stations météorologiques MGMERL (signalées
  par le porteur du projet le 02/11) et les 24 pluviomètres d'Ollivier et al. (à demander aux auteurs).
- ✅ Téléchargeur (`build_e1_sources.py`, 13 tests réussis) et workflow mensuel 20 (le 25 de chaque mois).
- ❌ puis 🔧 Ma relance du 02/11 au matin du workflow GloFAS (14) ne traitait que 2018 : un lancement manuel prend la
  valeur par défaut du formulaire. Relancé avec les 21 années. **Leçon :** relire les valeurs par défaut d'un
  formulaire avant un lancement manuel.

### Audit de sécurité et de licences du dépôt (demandé par le porteur du projet)
- ✅ Aucune clé, aucun jeton et aucun mot de passe dans le code ni dans les 353 commits de l'historique.
- 📌 Le dépôt **reste public** (décision du porteur du projet) : les minutes GitHub Actions sont illimitées.
  En privé, les quelque 6 000 minutes par mois mesurées dépasseraient le quota gratuit de 2 000.
- 🔧 Données personnelles retirées des extraits mWater (`inputs/mwater/`) : noms et identifiants des contributeurs
  (« Added by user », « Last modified by user », « Custom ID assigned by ») et liens vers les photos. Le système ne
  s'en servait pas (seule la position GPS est utilisée) ; nombre de sites inchangé (27 981 écoles, 3 837 centres de
  santé). ⚠️ Ces colonnes restent dans l'historique git ; l'en effacer demanderait de réécrire l'historique (non fait).
- 🔧 `emdat_corroboration.md` recopiait les chiffres d'EM-DAT, alors que sa licence (CC BY-NC-ND) l'interdit dans un
  dépôt public. Le tableau ne garde plus que le verdict de la comparaison. **Leçon :** une note qui affirme un usage
  « interne » doit être relue en sachant où elle est publiée.

### MGMERL : sources trouvées pour la sécheresse et les nappes (exploration du 02/11/2026)
- 📌 Le porteur du projet précise que les données MGMERL sont publiques ; MGMERL demande seulement d'être cité dans
  la thèse.
- ✅ Inventaire de « Ressources en eau » : 22 stations météo et 14 prévues (Tatirano, Maharo, RainMadagascar, PAM, PAH,
  UNICEF, WHH), 8 stations « hydromet » (niveaux de puits, pas de débits ; une avec salinité), des dataloggers de
  nappe (HT Analytics, Water Missions, Lorentz, relevés manuels ACF), et des rapports techniques de forage
  (lithologie, essais de pompage).
- ⚠️ Stations météo Tatirano (Fort Dauphin, Tsihombe, Farafangana) : données de décembre 2025 à octobre 2026 seulement,
  donc hors de la période de test d'E1. Pluviomètres douteux : Tsihombe à 0 mm en décembre, janvier et mars ;
  Farafangana à environ 0 mm d'avril à juillet.
- ✅ **16 séries de nappe HT Analytics téléchargées** (niveau et conductivité, toutes les 4 heures environ). Une dizaine
  couvrent au moins 2 ans, dont 5 qui commencent en 2019 et couvrent la sécheresse de 2020-2022 : Andaboly,
  Ankaramena, Ankaranabo, Ihazoambo, Sihanamaro. Conductivité médiane au-dessus du seuil de 3 000 µS/cm à Ankaramena
  et Sihanamaro. ⚠️ Défauts de capteur visibles (niveaux positifs, saut à −37 m, conductivité à 0) : un contrôle
  qualité sera nécessaire. Fichiers bruts rangés hors git (`data/mdg/mgmerl_raw/`).
- ✅ **Bulletins de sécheresse UNICEF du Grand Sud**, mensuels depuis décembre 2018 (unicef.org, publics), et synthèses
  trimestrielles UNICEF-ACF des nappes (2021-2022). 📌 Réserve méthodologique : l'étendue de la sécheresse publiée
  dans ces bulletins vient de CHIRPS et du NDVI MODIS, comme nos propres indices. S'en servir de vérité terrain serait
  circulaire. L'état mensuel des nappes suivies (une vingtaine de sites) est en revanche une observation
  indépendante.
- ❌ ERA5-Land 2015 (essai E1) : la file d'attente Copernicus est restée pleine 1 h 45, malgré les 6 nouveaux essais.
  Cause probable : des demandes orphelines laissées par des tâches annulées. À traiter.

### Protocole M3 : niveaux de nappe mesurés contre indices du système
- ✅ Protocole écrit avant calcul (`validation/protocole_nappes_mgmerl.md`) : H-N1, r(SPI-12, anomalie de niveau) > 0 ;
  H-N2, l'indice de recharge fait mieux que le SPI-12. Contrôle qualité fixé à l'avance (bornes, pics, sauts de
  capteur, mois d'au moins 10 jours, sites d'au moins 24 mois). Positionnement : Bloomfield et Marchant (2013),
  Kumar et al. (2016), observatoire du sud-ouest (EGU 2025).
- ❌ puis 🔧 Les tests sur données simulées ont trouvé un défaut avant toute donnée réelle : le regroupement par jour
  mélangeait deux séries de longueurs différentes. Corrigé ; 16 tests réussis.
- 📌 Répartition du calcul : les indices aux sites (pluie depuis 1981, SPI-1 à 24, recharge) sont calculés sur GitHub
  avec les fonctions de production (le téléchargement de la pluie y est rapide) ; les niveaux de nappe sont traités
  sur ce PC (fichiers MGMERL locaux, calculs légers). Décision du porteur du projet : calcul local quand c'est plus
  rapide.
- 🔧 Copernicus : quand la file du compte est pleine, les demandes orphelines (plus de 6 heures en attente) sont
  désormais annulées automatiquement (testé). ERA5-Land 2015 relancé.
- ❌ puis 🔧 **Défaut de production trouvé en préparant le protocole M3** : depuis le 27/10, le bilan hydrique retirait
  un ruissellement SCS-CN calculé sur le cumul du mois. Cette formule d'averse isolée, appliquée à 600 mm de pluie
  mensuelle, compte 490 à 570 mm de ruissellement. Conséquences :
  - l'excédent (« recharge ») valait 0 dans 99,6 % des fokontany ;
  - l'« indice relatif de nappe » publié était constant ;
  - le potentiel pour point d'eau (où la recharge pèse 25 %) était faussé.
  🔧 Le bilan ne retire plus de SCS-CN mensuel ; l'excédent hydrique est publié sous ce nom (recharge potentielle et
  ruissellement confondus), et le ruissellement SCS-CN reste indicatif. **Leçon :** un indicateur constant sur tout
  un pays doit déclencher une alerte automatique ; un contrôle de variance minimale est à ajouter au contrôle qualité.
- ❌ puis 🔧 **Publication dégradée** : en relançant deux fois le workflow 6 en 15 minutes, CHIRPS a refusé des
  téléchargements (erreur 429). La série de pluie s'est arrêtée en 2008, et le bilan publié a perdu 8 indicateurs sur
  11. 🔧 La version complète précédente a été restaurée par un nouveau commit. Ajouts : un garde-fou (une série en
  retard de plus de 3 mois n'est jamais publiée), un cache des mois déjà téléchargés et 3 téléchargements simultanés
  au lieu de 6.
- 📊 **Résultats M3 (`validation/nappes_mgmerl.md`), une fois les défauts corrigés.** 7 sites sur 16 retenus (au
  moins 24 mois valides ; Betioky F2 compte 23 sauts de capteur).
  - **H-N1 non soutenue** : r(SPI-12, anomalie de niveau) > 0 dans 5 sites sur 7, p = 0,23. Avec 7 sites, il
    faudrait 7 sur 7 pour conclure.
  - **H-N2, H-N3a et H-N3b non soutenues** : ni l'excédent du bilan (1 sur 5), ni l'ET0 de référence (SPEI-12,
    3 sur 7), ni l'ETR réelle (P − ETR, 2 sur 7) ne suivent mieux les nappes que la pluie seule. Avec une ET0
    climatologique, le SPEI est presque identique au SPI (Ankaramena 0,71 contre 0,69).
  - Le cumul le mieux corrélé varie de 9 à 24 mois selon le site, ce qui confirme Kumar et al. (2016) : une durée
    unique pour tout le pays ne convient pas.
  - Les deux sites les plus secs (Andaboly et Sihanamaro, environ 500 mm/an, ETR/ET0 de 0,28 à 0,29) réagissent à
    l'inverse de la pluie de 12 mois. Explications possibles : pompage, ou recharge lointaine. À Sihanamaro, la
    conductivité monte quand le niveau baisse (r = −0,74), sur une eau déjà salée (environ 3 800 µS/cm).
  - Sécheresse de 2019-2022 : le niveau le plus bas arrive le même mois que le SPI-12 le plus bas à Ankaramena,
    Ankaranabo et Sihanamaro, mais 11 à 13 mois plus tard à Ihazoambo et Andaboly.
  - **Conclusion provisoire :** l'indice de nappe du système reste « non validé ». Le SPI seul suit les nappes au
    moins aussi bien, avec une mémoire propre à chaque site. Il faut plus de sites (Water Missions, Lorentz,
    relevés ACF, observatoire du sud-ouest) pour un test concluant.

### Bibliographie : hydrogéologie du Grand Sud (`validation/biblio_hydrogeologie_grand_sud.md`)
- ✅ L'hypothèse du porteur du projet est confirmée par la littérature. Le Sud a une nappe générale profonde et
  régionale (socle ou Isalo, puis calcaires, puis côte ; 150 à 200 m sous le plateau Karimbola) et des nappes peu
  profondes (alluviales et sous-écoulement des rivières, sables côtiers, socle altéré). Un bilan annuel ou mensuel
  conclut à tort à l'absence de recharge : la recharge vient d'épisodes brutaux (cyclones) et de zones amont (AVSF
  2016, Guyot 2002). Sur le plateau Mahafaly, le signal de recharge se lisse avec la profondeur (Carrière et al.
  2023).
- 📌 Ces lectures expliquent nos résultats M3 (excédent nul dans le Sud, mémoire de 9 à 24 mois, sites qui ne suivent
  pas la pluie locale). Mais elles arrivent après les résultats : ce sont des hypothèses nouvelles (H-N4 à H-N6),
  à tester sur des sites indépendants dans un protocole M3 bis écrit avant calcul.
- ❌ Trois documents n'ont pas pu être téléchargés (pages de protection) : l'article Carrière et al. 2023 en texte
  intégral, la thèse de Rabemanana et la synthèse de Rakotondraibe (2006). Ils ne sont cités que d'après leur résumé.
- 📌 Observation de terrain du porteur du projet, consignée : lors de forages dans le Sud, les failles et les
  discontinuités lithologiques alimentaient les nappes profondes, et l'on a rencontré des eaux très anciennes et
  salées.
- ✅ Bibliographie élargie aux analogues du Gondwana et de l'Afrique semi-aride, à la demande du porteur du projet.
  Trois résultats transposables :
  - le modèle altérites-fissures du socle du sud de l'Inde (Maréchal, Dewandel) ;
  - la recharge liée aux mois de pluie extrême, renforcés par ENSO et l'IOD (Taylor et al. 2013, Tanzanie), qui relie
    les modules nappes et téléconnexions ;
  - des eaux de fractures très anciennes (plus de 10 000 ans dans le Karoo, équivalent de l'Isalo).
  Deux hypothèses ajoutées au futur protocole M3 bis : H-N7 (95e centile) et H-N8 (failles).

### ERA5-Land bloqué : la vraie cause
- ❌ Les relances d'ERA5-Land (E1 et SPEI) ont encore été refusées tout l'après-midi, alors que la file ERA5-Land du
  compte était vide (« 0 demande pour reanalysis-era5-land »). La seule demande en file était celle du chapitre C3S,
  lancé à 07 h 30 UTC et toujours bloqué 5 heures plus tard sans rien livrer. D'après le forum ECMWF, la limite porte
  sur les demandes de l'utilisateur vers ce type d'archive, pas seulement sur un jeu de données.
- 🔧 C3S est mis en pause (reprise automatique mercredi, ou manuelle une fois ERA5-Land téléchargé). Un script de
  ménage (`scripts/cds_menage.py`, testé) liste les demandes du compte et annule celles qui sont en file depuis plus
  de 30 minutes, tous jeux confondus ; il tourne avant chaque série ERA5-Land d'E1. 📌 Règle : une seule famille de
  téléchargements Copernicus à la fois.

### Protocole H-N7 : océan, pluies extrêmes et recharge des nappes du Grand Sud
- ✅ Protocole écrit avant calcul (`validation/protocole_climat_extremes_nappes.md`). Chaîne en trois maillons :
  l'état de l'océan en juillet-septembre (ONI, DMI, SIOD), puis les mois de pluie au-delà du 95e centile (seuil de
  Taylor et al. 2013), puis les remontées des nappes. Le maillon A doit passer les quatre épreuves déjà utilisées
  pour la planification ; tests bilatéraux, car la littérature malgache juge le lien ENSO-fortes pluies « moins
  clair » dans le sud-ouest.
- 📌 Honnêteté sur les données : les 7 sites MGMERL ont déjà servi en M3, donc le maillon B y est exploratoire. La
  confirmation se fera sur des sites indépendants (Water Missions, Lorentz, ACF, GROSoM, ou mesures postérieures à
  juin 2025).
- 📌 À la demande du porteur du projet, avant tout calcul : le protocole H-N7 intègre le relief du sud-ouest (sous le
  vent des Hautes Terres), le canal de Mozambique (température de surface en juillet-septembre comme prédicteur ;
  creux du canal en attribution, d'après Barimalala et al. 2018) et la géologie des sites (karst ou socle).

### Carte nationale des nappes (`validation/protocole_carte_nappes.md`, registre R-38)
- 📌 Idée du porteur du projet : un outil national où l'on pointe un lieu (carte ou coordonnées GPS) pour obtenir une
  estimation de la profondeur de la nappe, de son type, de son âge, de sa qualité et de son potentiel, avec une marge
  d'erreur. L'outil oriente les foreurs sans remplacer la géophysique. Sources multiples : cartes mondiales, analogues
  étrangers et mesures malgaches (MGMERL n'en est qu'une).
- ✅ Protocole écrit avant tout calcul :
  - H-C1 : biais de la carte mondiale de Fan face aux forages malgaches ;
  - H-C2 : le modèle hybride bat la carte mondiale et le krigeage, en validation par blocs d'environ 100 km ;
  - H-C3 : fiabilité de la carte du fluor ;
  - H-C4 : salinité plus forte sur les côtes et dans le socle de l'Androy ;
  - règles d'expert pour le type de nappe et l'âge de l'eau.
- ✅ Couches mondiales recadrées sur Madagascar (`scripts/build_nappes_mondiales.py`, workflow 21, 7 tests) :
  - profondeur de nappe Fan et al. 2017 (environ 1 km ; 740 695 mailles ; médiane 15,5 m sous la surface) ;
  - fluor Podgorski et Berg 2022 (250 m ; 11,7 millions de mailles ; en % de 0 à 100) ;
  - GLHYMPS 2.0 (4 754 polygones de perméabilité et de porosité) ;
  - GLiM à 0,5° (204 mailles, surtout métamorphiques) ;
  - profondeur du socle SoilGrids 2017 (250 m ; 11,7 millions de mailles ; médiane 48 m), lue à distance sans
    télécharger les 8,5 Go du fichier mondial.
- 📌 Licences respectées : Fan (usage de recherche, redistribution non prévue) et le fluor (licence non précisée) sont
  gardés dans le cache des Actions, jamais republiés. GLHYMPS (CC BY 4.0), GLiM (CC BY 3.0) et le socle (ODbL) sont
  publiés dans la version GitHub `nappes-mondiales`, avec leur citation.
- ❌ La base mondiale de salinité (Thorslund et van Vliet 2020, plus de 200 000 points) ne contient **aucun point
  d'eau souterraine à Madagascar**. **Résultat en soi :** Madagascar est absent des bases mondiales de qualité de
  l'eau, et les données MGMERL comblent un vide.
- ❌ La recharge mondiale de Jung et al. (2024) n'est pas publiée en accès libre : le dépôt Zenodo cité ne contient
  que des données d'entraînement de la péninsule arabique. La recharge africaine de MacDonald et al. (2021, licence
  OGL) passe par un formulaire du BGS, impossible à automatiser : téléchargement manuel à faire.
- 📌 Fan et al. disposent de très peu de puits à Madagascar. Leur médiane (15,5 m) est plus profonde que celle des
  relevés MGMERL (4,5 m, `groundwater_limites.md`) : c'est exactement ce que H-C1 testera, sans conclusion
  aujourd'hui (pas de comparaison point à point faite).


### R-02 est-il nouveau ? (`validation/biblio_r02_nouveaute.md`)
- ⚠️ Verdict honnête : **contribution réelle, mais pas une première absolue.** La dépendance d'échelle des dégâts
  cycloniques est déjà publiée (Tang et al. 2023, Chine : l'aléa compte davantage aux grandes échelles). Ce qui
  semble nouveau : le plan conditionnel (à l'intérieur des zones touchées, l'aléa ne sépare plus et le terrain prend
  le relais), au niveau du village, avec une vérité Copernicus EMS et un événement laissé de côté, à Madagascar.
- ❌ Faiblesse identifiée : l'aléa est trop grossier (vent IBTrACS, pluie CHIRPS journalière à 0,05°), ce qui peut
  expliquer à lui seul une AUC de 0,5. 📌 Test R-02 bis proposé : pluie maximale sur 1, 3 et 6 heures d'IMERG et
  rafales d'ERA5, avec un protocole écrit avant calcul.
- ✅ Protocole R-02 bis écrit avant calcul (`validation/protocole_r02bis_echelle_alea.md`). On compare quatre modèles
  (aléa grossier, aléa fin, terrain, terrain et aléa fin), avec un événement laissé de côté et un bootstrap par
  événement. H-R1 (principale) : le terrain bat l'aléa fin au fokontany. Les trois issues possibles et leur lecture
  sont fixées à l'avance. 📌 Le porteur du projet demande des conclusions fermes : la nouveauté sera établie par une
  recherche bibliographique systématique et traçable (bases, requêtes, nombre de travaux examinés, motifs de rejet),
  pas par une impression.

### Agent de téléchargement (décision du porteur du projet, 02/11/2026)
- 📌 Un seul agent gère désormais tous les téléchargements, petit à petit, sans demandes simultanées auprès d'un même
  fournisseur. État tenu dans `validation/etat_telechargements.md`.
- ❌ puis 🔧 **IMERG, la vraie cause** : une requête seule passe en 3 secondes, mais dès que plusieurs partent en
  parallèle, le serveur NASA répond 503 puis coupe les connexions. Nos 3 tâches de 6 fils épuisaient chaque jour en
  retentatives. Le code est maintenant séquentiel, avec une attente de 60 à 300 s sur les refus et un arrêt après
  10 jours d'échec de suite (testé). IMERG E1 tourne une année à la fois ; IMERG pilote, GloFAS et C3S sont en pause
  dans l'ordre de la file.
- ✅ Relief sur la grille E1 (altitude, rugosité, exposition aux alizés) depuis GLO-90, pour les zones de H3-E1 :
  5 432 mailles, dont 844 au-dessus de 1 000 m. Contrôles : Antananarivo à 1 260 m ; la façade est majoritairement au
  vent (+5,9 m/km en médiane), l'ouest des Hautes Terres sous le vent.
- ✅ Script et workflow de l'indice du canal de Mozambique (ERA5 850 hPa, H-N7) prêts, en attente de leur tour dans la
  file Copernicus.

### Carte des nappes : test H-C1 (`validation/nappes_hc1.md`)
- 📊 999 forages MGMERL comparés à la carte mondiale de Fan et al. (2017) aux mêmes points. Profondeur médiane mesurée
  5,8 m ; Fan 20,9 m ; écart médian +12,9 m ; erreur absolue médiane 14,3 m.
- ⚠️ **H-C1 non confirmée selon la règle fixée à l'avance.** Le test de Wilcoxon point par point est très
  significatif, mais le contrôle par blocs de 1° ne l'est pas : Fan est plus profond dans 16 blocs sur 36 seulement
  (p = 0,62). Le biais vient surtout de quelques zones où les forages sont nombreux. **Leçon :** sans le contrôle par
  blocs, on aurait conclu à tort à un biais général, uniquement à cause du regroupement des forages.
- ❌ **Fan ne sait pas classer les sites** : corrélation de Spearman de 0,02 avec les mesures. Utilisée telle quelle,
  la carte mondiale n'aide pas un foreur à Madagascar.
- 📊 **L'écart dépend du relief** (analyse descriptive) :
  - en fond de vallée (HAND < 5 m), Fan est proche des mesures (2,5 m contre 5,0 m) ;
  - sur versant ou plateau (HAND > 15 m, 576 forages), Fan donne 30,9 m contre 6,0 m mesurés.
  Deux explications envisagées avant le calcul sont confortées : la maille de 1 km mélange vallée et versant, et sur
  les versants et plateaux les forages captent probablement des nappes d'altérites perchées, ou un niveau captif qui
  remonte dans le forage.
- 📌 Conséquence : c'est un argument fort pour le modèle hybride recalé sur les forages malgaches (H-C2), avec la
  position dans le relief comme variable explicative.

### Carte des nappes : transfert de connaissances (note du porteur du projet)
- ✅ Le porteur du projet a téléchargé lui-même les données du BGS (MacDonald et al. 2021) : la carte africaine de
  recharge, qui couvre Madagascar (médiane 109 mm/an ; Grand Sud environ 78 mm/an, cohérent avec les 20 à 100 mm/an
  du BRGM), et la base des 134 sites de recharge mesurée (30 pays, aucun à Madagascar). Fichiers bruts gardés hors
  git en attendant la vérification de la licence.
- ✅ Sa note « modélisation par transfert de connaissances » est versée au dépôt
  (`validation/notes_porteur/`) et traduite en section 10 du protocole, avant tout calcul. Elle prévoit des
  analogues par distance de Gower sur le climat, les sols, le relief, la végétation et l'aquifère (pas la géologie
  seule, selon sa réserve), une bibliothèque de paramètres, trois versions de transfert (T0, T1, T2), une validation
  en laissant un pays de côté (H-C5) et une calibration sur les références malgaches (H-C6).
- ✅ Reprise après la pause (02/11, 16 h 30 UTC). CHIRPS est complet de 2001 à 2025 ; IMERG Late de 2001 à 2011,
  en séquentiel (environ 20 min par année, plus aucun refus) ; ERA5-Land 2015 obtenu : le ménage de la file
  Copernicus a levé le blocage. Premiers contrôles : écarts connus entre sources (IMERG Late sous-estime la côte est,
  ERA5-Land surestime les Hautes Terres), utiles pour E1.
- ❌ puis 🔧 CHIRPS 2026 échouait, car le serveur répond « 403 » et non « 404 » pour un jour pas encore publié ;
  corrigé. ERA5-Land découpé en une tâche par année (environ 1 h chacune, une seule à la fois), car 25 années d'affilée
  dépasseraient la limite de 6 heures. Le script IMERG du périmètre pilote est rendu séquentiel lui aussi.

### MGMERL : exports des rapports de forage refusés
- ❌ Les liens CSV de la console « Ressources en eau > Exportation » (lithologie, essais par palier et de longue durée)
  répondent « client not found », même connecté avec le compte du porteur du projet et après avoir autorisé
  api.mwater.co dans l'extension Chrome. C'est le même refus qu'au 27/10/2026 : l'export est réservé aux membres de
  l'organisation mWater qui gère la console. La consultation reste possible, l'export non. 📌 Pistes : demander
  l'export ou une adhésion à MGMERL ; à défaut, relever les tableaux affichés à l'écran (limités aux 1 000 lignes
  les plus récentes).

### Carte des nappes : H-C5 confirmée (`validation/transfert_recharge_hc5.md`)
- ✅ Sur les 134 sites du BGS (30 pays), chaque pays est prédit par un modèle qui ne l'a jamais vu. Erreur médiane
  sur log10(R + 1) : 0,62 pour la référence naïve (un facteur 4 environ sur la recharge), 0,28 pour T1 (régression
  ridge), 0,24 pour T2 (5 analogues selon la distance de Gower, un facteur 1,7 à 1,8 environ). T1 bat la référence
  dans 26 pays sur 30, T2 dans 24 sur 29 (p < 0,001 pour les deux).
- ⚠️ Les pays où le transfert échoue (Burkina Faso, Cameroun, Éthiopie, Maroc) sont des cas de socle ou de relief.
  C'est à surveiller pour les Hautes Terres malgaches.
- 📌 Le transfert vers Madagascar (H-C6) est justifié. Il reste à calculer les variables malgaches (pluie, jours de
  pluie, ETP, aridité, NDVI, aquifère, sol, occupation des terres) et à rassembler les références locales.
- 📌 Le porteur du projet choisit de relever les tableaux MGMERL affichés à l'écran plutôt que de demander les exports.

### MGMERL : relevé des tableaux affichés (choix du porteur du projet)
- ✅ L'extension Chrome ne pouvait pas cliquer sur la page (elle restait « en chargement »), mais la lecture par
  script fonctionne. Relevés le 02/11/2026 (1 000 lignes au plus par tableau, les plus récentes ; fichiers bruts hors
  git dans `data/mdg/mgmerl_raw/tableaux_affiches_2026-11-02/`) :
  - **profondeur des forages** (nouveau) : 1 000 forages, médiane 25,0 m (quartiles 18,8 et 35,9 m, maximum 98 m) ;
  - **résultat des essais de pompage** (nouveau) : 1 000 forages, 565 aptes, 215 non aptes, 219 à refaire, avec leurs
    coordonnées GPS. C'est un indicateur direct du potentiel des forages ;
  - niveau statique et conductivité, mis à jour (998 forages communs avec le 27/10) ;
  - récapitulatif MGMERL : **25 272 forages**, dont 10 283 en socle, 7 655 en sédimentaire non consolidé, 3 813 en
    sédimentaire consolidé fissuré et 1 403 en roches intrusives.
- 📊 Observation descriptive (pas un test) : 861 forages ont à la fois une profondeur et un niveau statique. La
  profondeur médiane des forages (25 m) est bien plus grande que celle du niveau statique (5,8 m) : l'eau remonte
  dans le forage au-dessus de la zone captée. Cela conforte l'une des explications de l'écart avec la carte de Fan
  (H-C1), dont la médiane (20,9 m) est plus proche de la profondeur des forages. À intégrer comme variable du modèle
  hybride (H-C2), sans conclure avant le test.
- ✅ H-C6 préparé avant calcul. Précisions fixées : les variables malgaches viennent des **mêmes sources** que la base
  africaine (CRU TS 1981-2010, MOD13, carte BGS des aquifères, sol WRB, Globcover) pour ne pas confondre l'écart
  entre sources avec l'effet recherché ; version T2 retenue sur H-C5 ; intervalle de 80 % tiré des résidus par pays ;
  références malgaches (Sud 20-100 mm/an, plateau Mahafaly environ 60 mm/an, fluctuation de nappe aux sites MGMERL).
  Script et 5 tests prêts ; variables malgaches demandées à l'agent de téléchargement.

### Carte des nappes : H-C2 (`validation/nappes_hc2.md`)
- 📊 999 forages MGMERL, validation par blocs de 1° (25 blocs, chacun prédit sans aucun de ses forages). Erreur
  absolue médiane entre blocs : carte de Fan seule 6,4 m ; krigeage des seules mesures 3,1 m ; **modèle hybride
  2,8 m**. L'intervalle de 80 % de l'hybride couvre 76 % des forages : il est bien calibré.
- ✅ L'hybride bat la carte mondiale dans 23 blocs sur 25 (p < 0,001) : la correction apprise sur les forages
  malgaches divise l'erreur par plus de deux.
- ⚠️ **H-C2 non confirmée selon la règle fixée** : face au krigeage, l'hybride ne fait mieux que dans 16 blocs sur
  25 (p = 0,115). Lecture : les niveaux statiques mesurés varient peu (médiane de 5 à 6 m), donc une simple
  interpolation des mesures voisines est déjà difficile à battre là où il y a des forages. L'avantage attendu de
  l'hybride se situe loin des forages, ce que des blocs de 1° entourés d'autres blocs mesurés ne testent pas.
- 📌 Pistes, qui demanderont un nouveau protocole écrit avant calcul : (1) une validation par grandes régions
  laissées de côté, qui teste vraiment l'extrapolation loin des forages ; (2) ajouter une carte des failles et la
  profondeur des forages, quand elles seront disponibles ; (3) l'export complet des 25 272 forages restant
  inaccessible, élargir avec d'autres sources.
- ✅ Covariables H-C6 de la recharge BGS (654 mailles de 0,28°) : climat CRU TS 4.10 1981-2010 (pluie de 424 à
  3 075 mm/an, aridité de 0,31 à 2,74), groupe d'aquifère (socle 418, sédimentaire 176, non consolidé 57), géologie
  GLG, sol WRB et occupation du sol (WorldCover, car Globcover 2009 est inaccessible). Le NDVI MOD13C2 viendra après
  IMERG E1.
- ❌ puis 🔧 La première lecture de SoilGrids donnait la même classe de sol (Ferralsols) aux 654 mailles : la carte
  est en degrés, et le facteur de réduction calculé en mètres la ramenait à un seul pixel. Corrigé et testé : 8
  classes, dont Ferralsols 294, Luvisols 122, Cambisols 94 et Arenosols 52. **Leçon :** une colonne constante sur
  tout un pays signale une erreur de traitement.

### Carte des nappes : H-C2b, régions entières laissées de côté (`validation/nappes_hc2b.md`)
- ⚠️ **Non confirmée selon la règle fixée** : l'hybride bat le krigeage dans 6 régions sur 8 (condition 2 remplie),
  mais le test de Wilcoxon sur l'ensemble des forages n'est pas significatif (p = 0,16). Ce test est dominé par
  Androy, Anosy et Atsimo-Andrefana (810 forages sur 980), où les deux méthodes se valent.
- 📊 Descriptif :
  - **loin des forages connus, l'hybride fait nettement mieux** : Sava (270 km du forage le plus proche) 1,4 m contre
    3,9 m ; Analanjirofo 1,8 contre 5,0 ; Atsimo-Atsinanana 1,7 contre 3,4 ; Boeny 2,3 contre 2,9 ;
  - Menabe (16 forages) est l'exception : l'hybride fait 10,8 m d'erreur, contre 8,1 pour le krigeage ;
  - au-delà de 100 km, 2,9 m contre 3,5 m.
- 📊 **La carte mondiale de Fan se trompe surtout dans le Sud sec** (21,7 m d'erreur dans l'Androy, 23,9 dans
  l'Atsimo-Andrefana), bien moins sur la côte est (2,4 à 4,0 m). Lecture probable : le modèle mondial place une nappe
  régionale profonde là où la pluie est faible, alors que les forages du Sud trouvent souvent de l'eau peu profonde
  (nappes alluviales ou d'altérites, niveau qui remonte dans le forage). C'est cohérent avec la distinction entre
  nappe profonde et nappes locales (`biblio_hydrogeologie_grand_sud.md`).
- 📌 Conclusion de thèse prudente : l'hybride n'est jamais nettement moins bon que le krigeage, sauf en Menabe ; il
  est bien meilleur que la carte mondiale partout, et prometteur loin des forages. La confirmation demande des
  forages indépendants dans les régions peu couvertes.

## 03/11/2026

### Module eaux souterraines : protocole-cadre (`validation/protocole_cadre_eaux_souterraines.md`)
- ✅ Écrit avant tout nouveau calcul. Il rassemble les demandes du porteur du projet (carte précise du niveau statique ;
  recharge, volume, renouvellement, risque d'épuisement ; court, moyen et long terme), les deux textes d'audit du
  02/11 et les résultats déjà obtenus.
- 📌 Critères principaux fixés pour toutes les phases : erreur moyennée par région (chaque région pèse autant) et
  erreur à plus de 50 km du forage connu le plus proche, avec intervalles de confiance par rééchantillonnage des
  régions.
- 📌 Phases du niveau statique : 0 (audit, référence S0), 1 (conditions de mesure), 2 (S1 failles et lithologie
  cartographiées, S2 linéaments), 3 (régression-krigeage), 4 (confirmation sur forages indépendants), 5 (cartes avec
  domaine de fiabilité).
- 📌 Formules fixées à l'avance : volume = 10⁶ × épaisseur saturée × Sy ; renouvellement τ = V / R ; risque =
  prélèvements / recharge, en classes.

### Phase 0 : audit des forages et référence S0 (`validation/nappes_phase0_audit.md`)
- ✅ Diagramme de flux : 1 000 relevés lus ; 1 000 après contrôle ; 999 avec une valeur de Fan ; 999 dans un
  fokontany ; 980 dans une région d'au moins 10 forages. L'écart de 999 à 980 (19 forages) vient des 5 régions qui en
  ont moins de 10.
- 📊 **Déséquilibre géographique** : de 18,3 forages pour 1 000 km² dans l'Androy à 0,06 dans l'Amoron'i Mania, soit
  un rapport de 300. **11 régions sur 24 n'ont aucun forage** dans ce relevé, dont presque toutes les Hautes Terres.
- 📊 Relevés de juin 2023 à septembre 2026 : 368 en saison des pluies, 632 en saison sèche (323 en juin).
- 📊 Référence S0, par région entière laissée de côté :
  - critère 1 (moyenne par région) : Fan 9,1 m [4,1 ; 14,8], krigeage 4,1 m [3,2 ; 5,4], hybride 3,4 m [1,9 ; 5,6] ;
  - critère 2 (forages à plus de 50 km) : Fan 8,0 m, krigeage 3,5 m [3,2 ; 3,9], hybride 3,2 m [1,8 ; 4,3] ;
  - biais moyen de Fan : +15,7 m.
  Les intervalles se recouvrent : la phase 0 ne permet pas de départager l'hybride et le krigeage. C'est la référence
  des phases suivantes.
- ❌ **L'intervalle de 80 % devient trop étroit loin des forages** : il couvre 84 % des forages à moins de 25 km, mais
  65 % au-delà de 100 km (50 % en Menabe, 64 % en Atsimo-Andrefana). Le modèle est trop sûr de lui là où il n'a pas de
  données. 📌 À corriger avant la carte nationale : élargir l'intervalle selon la distance au forage le plus proche
  (calibration par classe de distance), pour un domaine de fiabilité honnête.

### E1 : fusion contrôlée des sources de pluie (`validation/e1_fusion_pluie.md`, workflow 25)
- ✅ Calcul complet sur 2001-2025 (9 131 jours communs aux trois sources) : triple collocation sur l'apprentissage
  2001-2015 (pentades de novembre à avril), test sur les stations GSOD 2016-2025.
- 📊 Triple collocation, médianes sur les mailles terrestres : IMERG Late r = 0,90 (variance d'erreur 261 mm² par
  pentade), CHIRPS r = 0,87 (297), ERA5-Land r = 0,84 (405). Poids moyens de la fusion : IMERG 0,42, CHIRPS 0,32,
  ERA5-Land 0,26. La triple collocation échoue (variance négative) sur 24 mailles terrestres seulement sur 5 265. Le
  rapport affiche 6 359 mailles « à poids égaux » : ce nombre compte aussi les mailles de mer, sans objet.
- ❌ **H1-E1 non soutenue** (fusion C contre IMERG, la meilleure source seule fixée sur l'apprentissage) : 2 stations
  favorables sur 5, p = 0,81. **H1-E1b non soutenue** (C contre la moyenne simple B) : 2 sur 5, p = 0,81.
- ❌ **Limite principale : 5 stations seulement** ont assez de pentades sur 2016-2025, sur les 24 stations GSOD
  téléchargées. Avec 5 stations, le test du signe ne peut conclure dans aucun sens (même 5 sur 5 donnerait p = 0,03
  au mieux). Le résultat est donc « non démontré », pas « la fusion est inutile ».
- 📊 Lecture station par station : la fusion gagne nettement à Sainte-Marie (KGE 0,79 contre 0,46 pour IMERG), perd à
  Toamasina, où CHIRPS est le meilleur (0,55). CHIRPS intègre des stations GTS, probablement en partie celles-ci
  (protocole §7) : la comparaison le favorise.
- 📌 Suite fixée par le protocole : zones de relief H3-E1 (altitude, rugosité, exposition) et évaluation de l'effet
  sur les sorties du système (§6.3). Pour une validation plus puissante, il faut d'autres pluviomètres indépendants ;
  la triple collocation, elle, ne dépend pas des stations et reste valable sur toute l'île.

### Phase 1 eaux souterraines : conditions de mesure (`validation/nappes_phase1.md`)
- ✅ Précisions écrites dans le protocole-cadre avant le calcul (date du rapport MGMERL, saison, SPI-3 et SPI-12 du
  mois du relevé à la maille CHIRPS). Grilles SPI des 48 derniers mois produites sur GitHub (workflow 26, release
  « spi-grilles », mise à jour le 26 de chaque mois) : octobre 2022 à septembre 2026. 962 forages sur 980 ont un SPI
  (les autres n'ont pas de date ou une date antérieure aux grilles).
- 📊 La référence S0 est reproduite à l'identique (3,39 m et 3,17 m) : même code que la phase 0.
- ❌ **Variables rejetées** (règle fixée avant le calcul) : le critère 1 se dégrade (3,39 → 3,53 m, écart +0,14 m
  [0,00 ; +0,29]) ; le critère 2 baisse à peine (3,17 → 3,10 m, écart −0,08 m [−0,15 ; +0,32], non démontré). La
  couverture de l'intervalle de 80 % ne change pas (65 % au-delà de 100 km).
- 📌 Lecture : à l'échelle de l'île, la pluie des mois précédant le relevé n'explique pas les écarts entre forages ;
  ce sont la position et le terrain qui comptent. Cela ne dit rien des variations d'un même forage dans le temps, qui
  relèvent du suivi aux 16 sites (court terme, M3). Phase 2 (failles et lithologie) sur la base S0, sans ces
  variables.

- ✅ Colonne NDVI des covariables H-C6 : MOD13C2 v6.1, moyenne 2001-2010 (120 mois sur 120, pixels fiables). Vérifié :
  forêt 0,76, prairie 0,45, corrélation de 0,69 avec la pluie CRU.
  ❌ puis 🔧 Deux obstacles franchis avant les données :
  - le service OPeNDAP cloud de la NASA refusait la connexion par redirections (400) ; un jeton Earthdata (Bearer)
    l'a remplacée ;
  - le jeu n'est pas servi en DAP2 ; passage au DAP4.
  Gain : 120 petits sous-ensembles au lieu d'environ 11 Go de fichiers mondiaux.
- ✅ E1 complet ; l'ETP ERA5-Land du SPEI est enfin téléchargée. ⚠️ La validation SPEI qui suit échoue sur un bogue de
  lecture de `et0_cache.json` (`validate_spei_ndvi.py`, `control_et0`), signalé.

### H-C6 : recharge transférée d'Afrique à Madagascar (`validation/transfert_recharge_hc6.md`)
- ✅ Colonne NDVI remplie par l'agent (MOD13C2 v6.1, moyenne 2001-2010, 120 mois ; sous-ensembles OPeNDAP DAP4 au lieu
  d'environ 11 Go de fichiers mondiaux). Version T2 (5 analogues, distance de Gower), choisie sur H-C5 avant tout
  calcul malgache.
- 📊 Recharge médiane : T2 75 mm/an (Grand Sud 70, Nord 131) ; carte BGS 108 ; T1 (ridge) 233, avec 799 au Nord.
  276 mailles sur 650 (42 %) n'ont aucun analogue africain proche : la carte y extrapole.
- ❌ **H-C6 non confirmée** : 3 références malgaches sur 8 dans l'intervalle de 80 % (règle : au moins 60 %). La
  référence régionale du Sud (BRGM, 20 à 100 mm/an) passe ; 2 sites MGMERL sur 7 passent (Ankaramena, Ankaranabo).
- 📊 **Les 5 échecs vont dans le même sens** : le transfert surestime la recharge aux sites suivis (prédit 92 à 262
  mm/an, mesuré 6 à 48 mm/an par fluctuation de nappe). Deux lectures possibles, que les données actuelles ne
  départagent pas : les analogues africains de socle rechargent davantage que le socle du Sud malgache ; ou la
  fluctuation de nappe sous-estime (Sy de socle de 0,01 à 0,05, remontées mensuelles seulement).
- ❌ Défaut trouvé : la référence du plateau Mahafaly n'a pas été évaluée. Le filtre cherchait « Eocene » ou
  « calcaire » dans la classe géologique BGS, qui n'emploie que des classes larges (« Cretaceous-Tertiary
  sedimentary »). Même réussie, elle donnerait 4 sur 9 (44 %) : le verdict ne change pas. Non corrigé après coup.
- 📌 Conséquence pour le protocole-cadre : la recharge reste une **approximation** ; le volume, le renouvellement et
  le risque d'épuisement porteront une fourchette large de recharge (T2 et fluctuation de nappe), et les sites MGMERL
  servent de contrôle local.

### SPEI contre SPI face au NDVI (`validation/spei_ndvi.md`, R-24)
- 🔧 Échec du 03/11 (run 41579128422) : le contrôle de l'ET0 lisait la clé « _years » du cache Open-Meteo comme une
  série de 12 mois. Corrigé, test ajouté, relancé avec succès.
- ✅ **H1 soutenue** : dans les districts secs, le SPEI suit mieux le NDVI que le SPI dans 31 districts sur 36
  (p < 0,001 ; r médian 0,52 contre 0,50).
- ❌ **H2 non soutenue** : on attendait l'absence de gain dans les districts humides ; le SPEI y gagne aussi (51 sur
  84, p = 0,03 ; 55 sur 84 pour la meilleure combinaison, p = 0,003), avec des écarts de corrélation très faibles.
- 📊 Sécheresse du Grand Sud 2020-2022 : SPEI-6 sous −1 pendant 21 mois (minimum −2,32) contre 14 mois pour le
  SPI-6 (minimum −1,81), même mois de début (février 2020) : le SPEI montre un épisode plus long et plus intense.
- 📊 Contrôle de l'ET0 : la Penman-Monteith ERA5-Land de ce travail est **plus basse que celle d'Open-Meteo** tous les
  mois, de 7 % (décembre) à 27 % (juillet), l'écart étant plus fort en saison sèche. Cause probable déjà signalée
  dans les limites : ET0 calculée sur moyennes mensuelles, qui lissent le déficit de vapeur. À garder en tête pour
  les bilans d'eau ; le SPEI, standardisé, y est moins sensible.

### Données SEAM du ministère de l'Eau (`validation/seam_utilite.md`, R-42)
- ✅ Protocole écrit et commité avant calcul (`protocole_seam_points_eau.md`). Données lues sans connexion par l'agent
  (GET seul, une requête à la fois) : 86 049 points d'eau géolocalisés, 5 173 systèmes AEP, tableaux par commune.
  Hors dépôt ; aucune liaison avec d'autres bases (demande du porteur du projet).
- ❌ **Qualité** : 45,8 % des forages et puits partagent leurs coordonnées exactes (jusqu'à 955 au même point) :
  positions par défaut. Le critère Q1 (positions à Madagascar) était atteint mais ne détectait pas ce défaut.
- 📊 **Représentativité** : les 1 000 relevés MGMERL sont plus secs que les 15 384 forages SEAM (pluie 962 contre
  1 300 mm/an, DMS +0,46) ; 24 % des forages du pays sont hors de l'étendue des relevés pour au moins une variable de
  terrain. Utile pour le domaine de fiabilité de la carte. (Deux exécutions donnent 23,8 % et 24,0 % : écart non
  expliqué, sans effet sur la conclusion.)
- ❌ **H-S1 non soutenue** avec toutes les positions (ρ = −0,04). **H-S1b** (positions uniques, enregistrée après
  le premier calcul) : ρ = −0,11, p = 0,001, négatif dans 6 régions sur 7 ; ajoutée à l'hybride, la part de puits
  est **gardée selon la règle mais sans gain réel** (critère 1 : 3,39 → 3,38 m ; critère 2 : 3,17 → 3,15 m ; IC des
  écarts contenant 0). Lien réel mais trop faible pour améliorer la carte.
- ✅ **Pression** : population par commune complète (99,1 % des communes, 29,9 millions, −1,3 % de la projection) ;
  médiane de 1 884 habitants par ouvrage d'eau souterraine fonctionnel. Retenue pour l'indice d'épuisement.
- 📊 Exploratoire : plus de forages en panne dans les districts où la nappe mesurée est profonde (ρ = +0,37, 31
  districts, p = 0,04).
- 📌 Verdict : SEAM est **utile** pour la pression (risque d'épuisement) et la représentativité ; **pas** comme source
  de niveau statique ni comme variable de la carte.

### E1, H3-E1 : erreur des sources selon le relief (`validation/e1_relief.md`)
- ✅ Seuils des zones fixés et commités avant le calcul par zone (altitude 1 000 m, tiers de rugosité, exposition
  ±2 m/km, côte à moins de 20 km).
- 📊 **IMERG tient sur les versants au vent et sur la côte** : r = 0,92 sur les versants est (CHIRPS 0,84, ERA5-Land
  0,81) et 0,94 sur la côte (0,84 et 0,82). La variance d'erreur de CHIRPS et d'ERA5-Land y double presque (562 et
  664 mm² par pentade contre 285 pour IMERG). Sous le vent, CHIRPS et IMERG sont à égalité (0,88).
- 📊 Toutes les sources se dégradent en relief accidenté, ERA5-Land le plus (Spearman entre r et rugosité −0,24),
  puis CHIRPS (−0,21), IMERG le moins (−0,10). Les Hautes Terres en tant que telles changent peu (r presque égal
  au-dessus et au-dessous de 1 000 m) : c'est l'exposition et la rugosité qui comptent, pas l'altitude.
- 📌 Lecture : là où les pluviomètres manquent (versant est), CHIRPS s'appuie sur l'infrarouge et sa climatologie, qui
  voient mal la pluie de relief des alizés ; IMERG, avec ses micro-ondes passives, la voit mieux. C'est l'argument
  physique d'une fusion pondérée **par zone**, que les 5 stations GSOD ne permettent pas de tester.

### Intervalle du niveau statique calibré selon la distance (`validation/nappes_intervalle.md`)
- ✅ Méthode fixée et commitée avant le calcul (calibration conforme par classe de distance, facteurs estimés sans la
  région évaluée).
- ✅ **Critère atteint** : couverture de l'intervalle de 80 % entre 76 et 84 % dans toutes les classes (avant : 65 à
  84 %). Au-delà de 100 km, 65 % → 76 % pour un intervalle élargi de 9,0 à 11,4 m (médiane). Facteurs pour la carte
  nationale : 0,93 (0-25 km), 1,01, 1,18, 1,24 (plus de 100 km).
- ❌ **Limite** : la distance ne suffit pas partout. Atsimo-Andrefana reste à 65 % et Menabe à 50 % ; d'autres régions
  passent au-dessus de 90 % (Boeny 96 %, Sava 94 %). L'erreur dépend aussi de la région (géologie : sédimentaire de
  l'Ouest), ce que la phase 2 (lithologie et failles) doit traiter. 
  La valeur de 76 % au-delà de 100 km est juste au-dessus du seuil.

### Grille de pluie de Météo Madagascar (map.meteomadagascar.mg) : examinée, non ajoutée à E1
- ✅ Examinée le 03/11 (lecture seule, OPeNDAP) : « Madagascar_v3 » (ALL, CLM, MON), pluie journalière, décadaire et
  mensuelle à 0,0375°, 267 × 387 mailles, 476 mois (environ 1981-2020) ; pages mises à jour en 2021. Organisation
  typique d'ENACTS (pluviomètres nationaux fusionnés au satellite), non nommée sur le site. Aucun jeu de stations
  brutes exposé.
- 📌 **Décision : non ajoutée**, pour trois raisons. (1) Elle s'arrête vers 2020 : inutilisable dans un système mis à
  jour automatiquement. (2) Elle contient les pluviomètres : la comparer aux stations ne serait pas une validation
  indépendante, ce qui est justement le manque d'E1. (3) Sa part satellite est probablement proche de celle de
  CHIRPS : l'hypothèse d'erreurs indépendantes de la triple collocation serait violée. Une source de plus
  n'apporterait pas l'information manquante (des pluviomètres indépendants) et ajouterait du bruit au modèle.
- 📌 Ce qui ferait avancer E1 : les relevés bruts des pluviomètres nationaux, non publiés sur ce site.

### E1, section 6.3 : les versions de la pluie face aux impacts (`validation/e1_impacts.md`)
- ✅ Précisions fixées et commitées avant le calcul. Données journalières des trois sources téléchargées depuis la
  release ; ❌ une coupure réseau a tronqué 8 fichiers, et un premier contrôle (erreur de guillemets dans mon script)
  les a déclarés bons à tort. Le calcul a planté, sans résultat faux. Contrôle refait par taille exacte et lecture ;
  fichiers retéléchargés.
- 📊 **Inondations du périmètre pilote** (saisons 2016-2017 à 2024-2025) : CHIRPS, IMERG, B et C détectent 3
  inondations sur 4, ERA5-Land 2. Épisodes sans événement : 3 pour B et C, 4 pour CHIRPS, 5 pour ERA5-Land, 6 pour
  IMERG. Les AUC des trois événements EMS changent de classement d'un événement à l'autre (CHIRPS 0,18 à 0,81) :
  aucune version ne domine. Lecture descriptive : la moyenne des sources réduit les fausses alertes à détection égale.
- 📊 **Sécheresse du Grand Sud 2019-2023** (résultat corrigé, voir ci-dessous) : au SPI-12, toutes les versions
  placent la sécheresse parmi les plus fortes du pays : Androy rang 1 avec CHIRPS, ERA5-Land, B et C (rang 3 avec
  IMERG) ; Anosy rang 2 à 7 ; Atsimo-Andrefana rang 4 à 11. Au SPI-3, les rangs sont plus dispersés (IMERG et C
  classent Atsimo-Andrefana loin, rangs 19 et 20). Un seul épisode : aucune version n'est départagée.
- ❌ Deux écarts trouvés et corrigés, résultats recalculés :
  - le premier passage omettait le seuil de normale minimale du SPI de production prévu par les précisions ;
  - **cause réelle des SPI-3 de CHIRPS à −3,09** (que j'avais d'abord attribués, à tort, au seuil) : les 31 jours de
    décembre 2021 sont vides dans le fichier CHIRPS d'E1 (téléchargement échoué à la construction ; IMERG et
    ERA5-Land sont complets), et `soilwater_core.spi` comptait un mois manquant comme 0 mm. Le premier résultat
    (« CHIRPS classe la sécheresse plus bas au SPI-12 : rangs 8, 6, 9 ») était faux pour la même raison.
  - Correction de `spi` : un cumul contenant un mois manquant est manquant (comme le SPEI) ; et chaque série choisit
    ses propres mois valides (avant, un trou dans la première série retirait ce mois de l'ajustement de toutes les
    séries). Sans mois manquant, le SPI est strictement inchangé : la production n'est pas modifiée. Test ajouté.
  - 📌 Décembre 2021 de CHIRPS est à récupérer dans la release E1 (agent).
- 📌 Lecture d'ensemble d'E1 : aucune hypothèse confirmatoire n'est soutenue (5 stations) ; H3-E1 montre un net
  avantage d'IMERG sur les versants au vent ; les impacts ne départagent pas les versions, la fusion ne fait jamais
  nettement pire et réduit les fausses alertes de crue. Le système garde CHIRPS (règle 6.4) ; le levier pour aller
  plus loin est un jeu de pluviomètres indépendants.

### Carte nationale du niveau statique, version 1 (`validation/nappes_carte_nationale.md`, figure `validation/figures/nappes_carte_v1.svg`)
- ✅ Précisions fixées et commitées avant le calcul. 17 453 fokontany estimés sur 17 465 (12 sans valeur de la carte
  de Fan). Profondeur, intervalle de 80 % calibré selon la distance, erreur attendue, drapeau d'extrapolation ;
  agrégats par commune, district et région. Sortie séparée (`external/nappes_carte.csv`), le produit en service
  (`watertable.csv`) n'est pas remplacé.
- 📊 Profondeurs médianes régionales de 3,8 m (Ambatosoa) à 7,3 m (Androy). Le Grand Sud (Androy, Anosy,
  Atsimo-Andrefana : 6,9 à 7,3 m) ressort plus profond que l'Est (Analanjirofo 3,9 m, Fitovinany 3,9 m).
- ❌ **52 % des fokontany sont en extrapolation** : leur terrain sort de ce que les 980 forages ont vu. C'est
  presque tout le cœur des Hautes Terres : Analamanga 99 %, Amoron'i Mania 98 %, Itasy 97 %, Vakinankaratra 96 %,
  Haute Matsiatra 96 %. Les forages MGMERL sont en basse altitude ; l'altitude des Hautes Terres dépasse leur
  étendue. Dans ces zones, l'erreur affichée (2,4 à 3,4 m, tirée de la distance seule) **n'est pas une erreur
  mesurée** : la précision y est inconnue. La carte y est un ordre de grandeur, pas une estimation validée.
- 📊 Fiable au sens mesuré : le Grand Sud et le Sud-Est (Androy 2 % d'extrapolation, Atsimo-Andrefana 15 %, Anosy
  31 %, Atsimo-Atsinanana 23 %), avec un forage connu à moins de 10 km en médiane et une erreur médiane de 2,4 m.
- 📊 Comparaison au produit en service (plus proche relevé à 15 km) sur 5 161 fokontany : écart médian 2,3 m, du même
  ordre que l'erreur de l'hybride ; rien ne dit lequel est juste.
- 📌 Limites connues : l'hybride resserre les estimations vers la moyenne des forages (profondeurs régionales entre 4
  et 7 m) ; les nappes profondes de fissures ne sont pas représentées ; Atsimo-Andrefana et Menabe ont une
  couverture d'intervalle trop faible (65 et 50 %). Ce qui améliorerait le plus la carte : des forages des Hautes
  Terres (archives du porteur du projet, phase 4) et la lithologie et les failles (phase 2).

### ⚠️ Avertissement : les forages MGMERL utilisés depuis le 02/11 ne sont qu'un extrait de 1 000 lignes
- ❌ Constaté le 03/11 sur remarque du porteur du projet : les quatre tableaux MGMERL extraits le 02/11 (niveau
  statique, conductivité, profondeur de forage, essais de pompage) ont **tous exactement 1 000 lignes**. La plateforme
  n'affichait que les 1 000 premières lignes. MGMERL compte 64 701 points d'eau et 25 272 forages (tableau par type
  d'aquifère).
- 📌 Résultats concernés (ils restent publiés, signalés comme portant sur cet extrait) : H-C1, H-C2, H-C2b, phase 0
  (dont « 11 régions sur 24 sans forage », artefact de l'extrait), phase 1, étude SEAM (Q2, H-S1, H-S1b), intervalle
  calibré et carte nationale v1. Les méthodes et protocoles restent valables ; seules les données changent.
- 📌 Suite : extraction complète par l'agent de téléchargement (lecture seule, découpage sous la limite d'affichage,
  totaux contrôlés), puis relance de la chaîne avec les mêmes protocoles (phase 0, intervalle, carte v2).
- 📌 **Leçon** : un total rond (1 000) est un signal de troncature ; tout extrait doit être comparé au total annoncé
  par la source avant usage.

### Recharge, volume, renouvellement, risque : code prêt, calcul en attente des données MGMERL complètes
- ✅ Mise en œuvre fixée avant calcul (protocole-cadre, 03/11) ; script `nappes_ressource.py` et 12 tests.
- ✅ Essai de bout en bout sur la carte v1 (extrait de 1 000 relevés), **non publié** : la chaîne tourne sur les
  17 465 fokontany ; 79 % des communes SEAM appariées par leur nom.
- 📌 Limite repérée à l'essai : la règle « toute la population prélève dans la nappe » gonfle le risque en ville
  (Analamanga), où l'eau vient surtout de surface. Elle reste appliquée telle quelle (règle fixée) et sera signalée
  dans le rapport v2 ; une correction par la source d'approvisionnement demanderait un nouveau protocole.

### Taux de desserte JIRAMA des grandes villes : recherche du 03/11 (incomplète)
- 📊 Trouvé et vérifié dans le texte :
  - Antananarivo : 47 % de desserte (Ognard et Taglioni 2019, données ARTELIA 2014 et 2012), une seule production
    (Mandroseza, eau de l'Ikopa, 140 500 m³/j) ; **mais** l'étude préparatoire de la JICA sur Toamasina (tableau 2022)
    écrit « le taux d'accès à l'eau potable est aujourd'hui de 30 % seulement [à Toamasina], alors qu'il s'élève à
    70 % à Antananarivo ». Les deux chiffres ne mesurent peut-être pas la même chose (desserte par le réseau,
    bornes-fontaines comprises ou non) ni la même zone (commune urbaine ou agglomération).
  - Toamasina : taux d'accès 30 % (JICA, vers 2022-2023) ; source d'eau brute non encore lue.
  - JIRAMA (site officiel) : 67 centres d'exploitation, 80 lieux de captage, sans détail par ville.
- 📌 Pistes repérées, non lues (crédits Firecrawl épuisés pour la journée) : étude d'impact de l'adduction d'eau
  de Toliara (projet PIC 2), document sur la rivière Besokatra (taux de desserte de 79,1 % d'après les statistiques
  JIRAMA, ville à identifier), suite du rapport JICA de Toamasina, appel d'offres JIRAMA de 21 forages de production à
  Mahajanga, Antsiranana et Antsirabe (ces villes utilisent donc aussi la nappe).
- 📌 Aucune valeur n'est changée dans le protocole avant d'avoir lu ces sources.

### Extraction complète MGMERL (03/11) et nouvelles sources de nappe
- ✅ **Tableaux MGMERL complets** (agent, lecture seule, requête de la page rejouée par tranches d'identifiants, une
  requête à la fois ; aucune tranche à 1 000 lignes) : niveau statique 1 400 relevés (l'histogramme de la page en
  annonce 1 398, écart de 2 non expliqué), profondeur 1 643, conductivité 13 700, essais de pompage 1 427. Les 1 000
  lignes du 02/11 y sont toutes. Hors dépôt (`data/mdg/mgmerl_raw/complet_2026-11-03/`).
- ❌ **Correction** : les 400 relevés de niveau statique ajoutés sont presque tous dans le Sud (Atsimo-Andrefana +164,
  Androy +161, Anosy +26, Atsimo-Atsinanana +23, Boeny +21). **10 régions sur 24 restent sans aucun niveau statique**
  même avec toutes les données MGMERL ; l'hypothèse « 11 régions sans forage = artefact de l'extrait » était fausse.
  Les relevés complets vont de 1994 à 2026 (l'extrait commençait en 2023).
- 📌 Chaîne relancée sur les données complètes (phase 0, intervalle, carte v2), mêmes protocoles.
- ✅ **Nouvelle source trouvée** (catalogue GGIS de l'IGRAC, sur une piste du porteur du projet) : observatoire des nappes
  du Sud-Ouest (Carrière et al. 2021, réseau GROSoM, Action contre la Faim), 10 puits suivis : 7 dans les grès et
  calcaires de la région de Toliara (2014-2020, 8 700 à 53 000 mesures chacun), 3 dans les sables côtiers d'Anosy
  (2018-2019). Indépendants de MGMERL. Usages : réponse des nappes sédimentaires à la pluie (M3), référence de recharge
  du plateau calcaire (absente en H-C6), 10 niveaux indépendants. Licence et séries à vérifier, téléchargement par
  l'agent.
- ❌ Couche SADC « gip_BHdata_madagascar » : inaccessible (le portail SADC-GIP a été remplacé par un nouveau site ; la
  couche n'existe pas dans le catalogue de l'IGRAC). Document IRD (horizon, 010080238) : site en maintenance le
  03/11, à réessayer.

### Rectification : les 1 400 niveaux statiques ne sont peut-être pas les seuls de MGMERL
- ❌ J'ai écrit que « la plupart des 25 272 forages n'ont pas de niveau statique ». **Ce n'est pas démontré.** Les 1 400
  relevés sont ceux dont le champ « Niveau statique d'eau » de la **fiche du point d'eau** est rempli. D'autres
  tableaux de MGMERL (rapports techniques de forage, tableaux de projets, piézomètres…) peuvent porter un niveau
  statique dans leurs propres colonnes (remarque du porteur du projet). Recensement systématique confié à l'agent.

### Chaîne relancée sur les 1 400 relevés (phase 0, intervalle, carte v2)
- 📊 Flux : 1 400 lus, 1 400 après contrôle, 1 399 avec Fan, 1 385 dans une région d'au moins 10 forages (9 régions).
- 📊 Référence S0 : hybride 3,26 m [1,98 ; 5,21] (critère 1) et 3,03 m [1,73 ; 3,90] (critère 2) ; krigeage 4,06 et
  3,49 m ; Fan seule 8,56 et 8,05 m (biais +17,6 m). Proche de l'extrait (3,39 et 3,17 m) : la conclusion ne change
  pas, l'hybride reste devant sans écart démontré.
- 📊 Intervalle calibré : couverture de 80 à 81 % dans chaque classe de distance (avant : 68 à 82 %) ; facteurs 0,95 à
  1,26. Menabe reste à 44 % (16 forages), Atsimo-Atsinanana à 68 %.
- 📊 Carte v2 : 54 % des fokontany en extrapolation (52 % en v1) ; les Hautes Terres restent à 95-99 %. Grand Sud :
  erreur médiane attendue 2,1 m (2,4 m en v1). Betsiboka a désormais un forage. 10 régions sans aucun niveau statique.
- 📌 Phases 1 et étude SEAM (H-S1) non relancées : leurs conclusions portent sur l'extrait de 1 000 relevés.

### Séries GROSoM téléchargées (04/11) ; CHIRPS 2021 réparé
- ✅ **GROSoM** (Carrière et al. 2021, Hydrological Processes 35:e14108 ; IGRAC-GGIS, jeu 2538) : 10 puits, mesures
  horaires (sondes TD-Diver, UTC), **cotes du niveau d'eau en m au-dessus du niveau de la mer**, pas des profondeurs
  (la fiche des puits donne l'altitude du sol pour convertir). 9 séries complètes ; Ambatofotsy partielle (30 452 sur
  53 085 mesures : manquent 2014-05 à 2016-05 et 2019-11 à 2020-05 ; l'autre accès demanderait environ 5 300
  requêtes, non lancé). Trous longs : Maroarivo 503 jours, Ankazomanga P06 420 jours. Hors dépôt.
- ⚠️ **Licence des données non indiquée** (fiche IGRAC sans texte ; l'article est en CC BY-NC-ND, ce qui ne couvre pas
  les données ; le dépôt Mendeley cité n'existe plus). Usage : analyse de recherche citée (Carrière et al. 2021,
  IGRAC-GGIS), aucune redistribution des séries ; seuls des résultats agrégés seront publiés.
- ✅ **CHIRPS 2021 réparé** (agent) : décembre 2021 n'existait sur le serveur qu'en .tif non compressé ; le script le
  gère et ne retélécharge que les jours vides. Contrôle des 25 années des 3 sources : plus aucun jour vide. E1
  (workflow 25) et §6.3 relancés.
- 📊 E1 §6.3 recalculé avec décembre 2021 complet : chiffres légèrement modifiés (CHIRPS : 8 épisodes au lieu de 9,
  AUC 0,18 ; 0,73 ; 0,80 ; SPI-12 Androy rang 2 au lieu de 1), **conclusions inchangées** : aucune version ne
  domine ; B et C gardent le moins d'épisodes sans correspondance (3) ; toutes classent la sécheresse du Sud parmi
  les plus fortes.
- 📊 E1 principal (workflow 25) relancé avec décembre 2021 complet : triple collocation inchangée (apprentissage
  2001-2015, non concerné) ; KGE aux stations modifiés d'au plus 0,01 ; H1-E1 et H1-E1b toujours non soutenues
  (2 sur 5, p = 0,81).

### Recensement de toutes les colonnes « niveau statique / niveau d'eau » de MGMERL (04/11)
- ✅ Recensement par la définition de la console « Ressources en eau » et le schéma des tables (tous onglets, widgets
  et couches). Les 1 400 relevés de la fiche point d'eau sont des colonnes **combinées**, calculées à partir des
  rapports techniques de forage (RTF) et des essais de pompage : les niveaux des RTF y sont donc déjà.
- 📊 Tableau des autorisations ANDEA : 322 lignes, 317 niveaux statiques ; 310 identiques à la fiche point d'eau, 1 à
  moins de 50 m ; **1 seul nouveau point localisable** (Anosy, 7,51 m). Autres colonnes du schéma (RTF « longue
  durée », water_asset) : affichées dans aucun tableau, inaccessibles. Bulletin de sécheresse : moyennes régionales.
- ✅ Nouveau : lectures des 16 capteurs HT Analytics, **58 713 lectures de juin 2019 au 31 mai 2026** (nos séries
  M3 s'arrêtaient en 2025) ; sans coordonnées dans la table (rattachement par code de site à faire).
- 📌 **Conclusion** : les 1 400 relevés (+1) constituent bien l'ensemble des niveaux statiques par forage accessibles
  dans MGMERL. La carte v2 repose donc sur toutes les données MGMERL disponibles ; les 10 régions sans mesure le
  restent. Pas de carte v3 nécessaire pour l'instant.

### Ressource en eau souterraine v1 (carte v2) : recharge, stock, renouvellement, risque (`validation/nappes_ressource.md`)
- ✅ Règles fixées avant le calcul (protocole-cadre, 03-04/11) : norme Sphère 15 L/j, fourchette d'Antananarivo,
  autres usages non comptés faute de données vérifiées (bétail : licence de la carte FAO de densité incertaine,
  normes publiées de 9 à 50 L par tête et par jour ; irrigation et industrie sans localisation).
- 📊 Renouvellement (valeurs centrales) : 41 % renouvelable (moins de 10 ans), 45 % lent, 13 % peu renouvelable. Les
  plus longs : Menabe 245 ans, Melaky 173, Boeny 163, Atsimo-Andrefana 131 (recharge faible, socle profond) ; les
  plus courts sur la côte est (2 à 3 ans).
- 📊 Risque d'épuisement (pression domestique) : 93 % faible, 6 % modéré, 1 % élevé (2 % à 20 L, 6 % à 50 L).
- 📊 **Antananarivo** : risque élevé dans 13 % des 192 fokontany si le réseau JIRAMA dessert 47 % de la population,
  **86 % s'il est coupé** ; 145 fokontany changent de classe. La desserte réelle du réseau est le facteur dominant du
  risque en ville.
- ❌ **Limites qui biaisent le risque vers le bas dans le Grand Sud** : (1) la recharge transférée surestime d'un
  facteur 3 à 30 aux sites suivis (6 à 48 mm/an mesurés contre 77 à 262 transférés) ; (2) le bétail abreuvé aux
  puits n'est pas compté. Le risque « faible » du Sud n'est donc pas une conclusion ; c'est une borne basse.
- 📌 Niveau de preuve : approximation non validée. Améliorations possibles sans le ministère : recharge du Sud par
  fluctuation de nappe (capteurs HT jusqu'en 2026, puits GROSoM), bétail si une source est vérifiée.

### Recharge mesurée par fluctuation des nappes, Grand Sud (`validation/recharge_fluctuation.md`)
- ✅ Protocole fixé et commité avant le calcul. 25 séries (15 capteurs HT 2019-2026, 10 puits GROSoM) ; **12 sites
  retenus** (au moins 24 mois valides) ; 13 écartés (séries trop courtes, dont 6 puits GROSoM d'un an).
- ❌ **Règle de correction non remplie** : rapport médian mesurée / T2 = 0,83 [IC 95 % 0,19 ; 3,71], 50 % des sites
  sous 1. T2 n'est pas jugée surestimée dans l'ensemble du Grand Sud ; aucune correction n'est appliquée.
- 📊 **Résultat exploratoire important (non prévu par une hypothèse)** : l'écart dépend de la géologie.
  - Socle (capteurs HT d'Androy, Anosy, Atsimo-Atsinanana) : T2 **surestime** sur 6 des 7 sites (rapports 0,04 à 0,60 ;
    Ankaramena 1,07).
  - Formations sédimentaires de la région de Toliara (GROSoM, classées « non consolidé » par la carte BGS) : T2
    **sous-estime** sur les 5 sites (rapports 2,1 à 5,2 ; recharge mesurée 80 à 195 mm/an contre 38 transférés).
  Une correction régionale unique serait donc fausse ; une correction par type d'aquifère demanderait une hypothèse
  écrite à l'avance et plus de sites.
- ❌ La méthode journalière (sensibilité) donne des valeurs parfois très élevées (852 mm/an à Sihanamaro) : le bruit de
  capteur passe le seuil de 1 cm/jour. Elle n'est pas fiable telle quelle ; le pas mensuel reste la référence.
- 📌 Conséquence pour le risque d'épuisement : dans le socle du Grand Sud, la recharge T2 est probablement trop forte
  (risque sous-estimé) ; dans les grès et calcaires de Toliara, elle est probablement trop faible (risque surestimé).
  À écrire comme hypothèse H-R1 (biais du transfert selon le type d'aquifère) avant tout test confirmatoire.

### Transfert de connaissances depuis des régions analogues : recharge (`validation/transfert_analogues.md`, R-43)
- ✅ Protocole et mise en œuvre fixés et commités avant le calcul. Sources : Wan, Döll et Müller Schmied 2024
  (821 estimations, CC BY 4.0), GLiM 0,5° (CC BY 3.0) ; 335 sites sources gardés (type d'aquifère connu).
- ✅ **Niveau 1 atteint (dans les sources)** : en laissant chaque pays de côté, le transfert par analogues bat la
  référence naïve dans 22 pays sur 29 (p = 0,004) ; erreur médiane 0,31 contre 0,49 (log10 de la recharge).
- ✅ **H-T1 soutenue** : sur les 12 sites malgaches mesurés, le transfert mondial est plus proche de la mesure que le
  transfert africain T2 sur 10 sites (p = 0,019). Il corrige surtout les grosses surestimations du socle (Ihazoambo :
  87 contre 262 mm/an transférés par T2, 46 mesurés) et rapproche les sites sédimentaires de Toliara (60 contre 38).
- ❌ **H-T2 non soutenue** : le transfert mondial ne classe pas les sites dans le bon ordre (ρ = −0,46, p = 0,14) ; il
  sous-estime encore le sédimentaire de Toliara (60 contre 80 à 195 mesurés) et surestime le socle d'Andaboly (104
  contre 6).
- ❌ **H-R1 non soutenue sur la base mondiale** : le modèle africain hors d'Afrique ne surestime pas plus le socle (31 %)
  que le sédimentaire (49 %), p = 0,95. Le biais vu à Madagascar n'est pas une règle générale.
- ❌ Point faible repéré : la règle GLiM à 0,5° ne s'accorde avec le type d'aquifère du BGS que sur **47 %** des sites
  africains ; à Madagascar, Nosiomby est classé « non consolidé » et Mahavelo « volcanique ». La maille de 0,5° (environ
  55 km) est trop grossière pour typer un forage. Amélioration possible, à écrire avant tout recalcul : GLiM vectorielle
  ou carte géologique nationale (phase 2).
- 📌 **Verdict selon le protocole (section 5)** : niveau 1 réussi ; niveau 2 partagé (H-T1 réussie, H-T2 échouée) :
  **transfert plausible pour l'ordre de grandeur, non démontré pour la répartition spatiale**. À ne pas présenter comme
  démontré.

### Transfert par analogues : reprise annoncée avec la GLiM vectorielle (`validation/transfert_analogues_vectoriel.md`)
- ✅ Reprise inscrite au protocole avant calcul, avec une règle de conclusion plus exigeante. GLiM vectorielle v1.1
  (Hambourg, 1,14 Go) lue sur GitHub (workflow 27) ; seules les classes aux 847 points sont publiées (4 sans classe).
  Coordonnées réelles des sites sources (Map_Latitude, Map_Longitude) au lieu du centre de maille.
- 🔧 Bogue corrigé pendant la reprise : un site (« AnKaranabO ») n'était pas apparié à cause des majuscules.
- 📊 Accord du typage avec le BGS sur les sites africains : 58 % (47 % avec la grille 0,5°) : mieux, mais sous le
  seuil fixé de 70 %.
- 📊 Niveau 1 inchangé (22 pays sur 29, p = 0,004). **H-T1 soutenue, plus nettement** : 11 sites sur 12 (p = 0,003).
  **H-T2 toujours non soutenue** (ρ = −0,37, p = 0,24) ; H-R1 toujours non soutenue (p = 0,96).
- 📌 **Conclusion selon la règle : inchangée, transfert plausible, non démontré.** Le transfert mondial donne le bon
  ordre de grandeur mais ne reproduit pas le contraste spatial : les puits sédimentaires de la région de Toliara
  (80 à 195 mm/an mesurés) restent prédits à 60 mm/an.
- 📌 Piste (non testée, à écrire avant tout test) : ces formations de Toliara sont en partie calcaires ; la compilation
  de Wan donne une fraction karstique (fkarst) par site. Une recharge karstique, plus forte, pourrait expliquer l'écart.

### H-K1 : le karst dans le transfert par analogues (`validation/transfert_analogues_karst.md`)
- ✅ Hypothèse et définition de la fraction karstique (formule de Wan et al. 2024 sur WOKAM) fixées et commitées avant
  le calcul. WOKAM (BGR) : licence d'usage sans redistribution ; seules les fractions aux sites sont publiées.
- 📊 Les 5 puits sédimentaires de la région de Toliara (et Betioky F2, Analalentika, Vovomena) sont en karst continu
  (fraction 0,61) ; Behavandra 0,38 ; aucun autre site.
- ❌ **H-K1 non soutenue (test confirmatoire dans les sources)** : ajouter la fraction karstique à la distance entre
  analogues ne réduit l'erreur que dans 8 pays sur 23 (p = 0,95) ; erreur médiane inchangée (0,351 contre 0,354).
- 📊 Exploratoire Madagascar : les sites karstiques passent de 60 à 74 mm/an prédits (mesurés 80 à 195) ; l'ordre
  spatial reste faux (ρ = −0,37).
- 📌 Lecture : le karst seul, comme simple variable de distance, ne suffit pas à expliquer la forte recharge de Toliara.
  Le karst agit sans doute sur la **dynamique** (infiltration rapide) plus que sur la moyenne climatique des analogues :
  c'est précisément ce que THMS permet de tester (H-M3).

### Test THMS (mémoire hydrique du sous-sol) dans le Grand Sud (`validation/thms_test_sud.md`, R-44)
- ✅ Protocole fixé et commité avant le calcul ; idée du porteur du projet (note gardée hors du dépôt public). Précision
  de mise en œuvre : capacité du sol prise dans une grille fixe de 8 valeurs (25 à 400 mm) pour un calage rapide.
  12 sites (7 capteurs HT sur le socle, 5 puits GROSoM karstiques de Toliara) ; calage sur 60 %, validation sur 40 %.
- ❌ **H-M1 non soutenue** : le modèle à plusieurs mémoires choisi par l'AIC ne bat la mémoire unique en validation que
  sur 2 sites sur 12 (Andaboly 0,03 → 0,24 ; Nosiomby 0,48 → 0,62) ; l'AIC garde une seule mémoire sur 7 sites.
  Selon la règle fixée, **pas d'extension nationale** de THMS sous cette forme.
- ❌ Ajustements faibles sur plusieurs sites (KGE de validation négatif à Sihanamaro, Ankazomanga P06 ; −20 à
  Ankaramena, probablement un décalage du capteur entre calage et validation) ; Sy souvent à sa borne : le rapport
  recharge / Sy est mal identifié avec 1 à 3 ans de données par site.
- 📊 **Signal exploratoire (H-M2, H-M3), cohérent avec le karst** : les 5 puits karstiques de Toliara sont tous
  décrits par **une seule mémoire rapide** (temps de 1 à 10 jours sur 4 d'entre eux, 55 jours sur P06), alors que les
  sites du socle retenant 2 ou 3 mémoires ont une part rapide faible (0,07 à 0,49) et une partie lente. Le karst agit
  donc bien sur la **dynamique** (transfert rapide), ce que la variable de distance de H-K1 ne voyait pas. Ce n'est
  pas une preuve : peu de sites, hypothèse suggérée en partie par ces mêmes données.
- 📌 Pour un test probant de THMS : séries plus longues (5 ans et plus), plus de sites hors du Sud (ministère),
  séparation du ruissellement, et un test spatial (paramètres prédits par la géologie sur des sites non calés).

### Atlas des nappes par bassin versant, v1 (`validation/atlas_bassins.md`)
- ✅ Protocole fixé avant calcul. 108 grands bassins ; fiches : niveau statique, fiabilité, recharge, stock,
  renouvellement, bilan prélèvements / recharge, relief, eau du sol. Fichier `external/nappes_bassins.csv`.
- 📊 **Fiabilité** : 9 bassins « mesurés » (2,9 millions d'habitants, tous dans le Sud et le Sud-Ouest : Saint
  Augustin, Berano, Marolinta, Androka, Antaritarika, Farafangana…), 75 « partiels » (17,8 millions), 24 « non mesurés »
  (3,3 millions). Le plus grand bassin habité (n° 1, Boanamary, 56 000 km², 4,8 millions d'habitants, Antananarivo
  compris) n'a que 31 relevés et reste « partiel » ; celui de la Tsiribihina (3,4 millions) n'en a qu'un.
- 📊 **À l'échelle du bassin, la pression domestique est faible partout** : bilan prélèvements / recharge de 0,018 au
  plus (médiane 0,002), même avec le réseau d'Antananarivo coupé (0,005 pour le bassin n° 1). La pression sur la nappe
  est donc un problème **local** (fokontany denses, villes, Sud aride), dilué à l'échelle du bassin. Bilans les plus forts
  dans les petits bassins côtiers arides du Sud-Ouest (recharge de 6 à 28 mm/an).
- ❌ Limites : recharge non validée (biais selon la géologie) ; bétail, irrigation et industrie non comptés ; noms de
  bassins non uniques (nom de la localité de l'embouchure) : numéro ajouté ; population totale rattachée 24,1 millions
  (fokontany dont le point tombe hors d'un grand bassin non comptés).
- 📌 Suite : bassins hydrogéologiques (lignes de partage de la nappe) dans les plaines côtières où ils peuvent
  s'écarter des bassins de surface ; demande ciblée au ministère pour les bassins n° 1 et Tsiribihina.

### Atlas par sous-bassin (`validation/atlas_sousbassins.md`)
- ✅ Déclinaison fixée avant calcul. 1 420 sous-bassins avec au moins un fokontany ; fiabilité : 27 mesurés, 867
  partiels, 526 non mesurés.
- 📊 Bilan prélèvements / recharge : 1 310 faibles, 74 modérés, **36 élevés**, tous dans de petits bassins côtiers de
  l'Ouest autour des villes : Toliara (Toliary-I et II), Mahajanga I, Morondava, Maintirano, Morombe. La pression
  apparaît à l'échelle fine et disparaît à l'échelle du grand bassin.
- ❌ **Réserve majeure, vérifiée** : ces bilans dépendent de la recharge transférée T2, fausse à ces endroits.
  Mahajanga : T2 = 6,8 mm/an pour 1 472 mm de pluie (carte BGS : 124 mm/an) : le bilan y est surestimé d'un facteur
  proche de 18 ; c'est en grande partie un **artefact**. Toliara : T2 = 20 mm/an, alors que les puits karstiques
  voisins mesurent 80 à 195 mm/an. Les villes côtières de l'Ouest sont bien les points de pression les plus probables,
  mais l'ampleur n'est pas connue.
- 📌 Correctif à écrire avant tout recalcul : contrôle de vraisemblance de la recharge (rapport recharge / pluie
  comparé aux fourchettes publiées par type de roche) avant tout calcul de bilan.


### Bassins hydrogéologiques (`validation/bassins_hydrogeologiques.md`)
- ✅ Protocole fixé avant calcul (04/11/2026) ; charge de la nappe = altitude GLO-90 − niveau statique (carte v2) ;
  mêmes calculs de bassins que pour la surface, écoulement sur la nappe (workflow 28).
- ✅ **H-B1 soutenue** : 2,6 % des mailles terrestres changent de bassin (règle : au plus 5 %). La nappe suit le relief
  (Tóth 1963 ; Haitjema et Mitchell-Bruker 2005).
- ✅ **H-B2 soutenue** : 5,0 % en terrain plat (pente < 2 %) contre 1,1 % en relief, rapport 4,8 (règle : au moins 2).
- ✅ **Test de sensibilité H-B2-L** (ajouté le 09/11 avant son calcul) : profondeur lissée sur 8 fokontany (1/d²)
  pour supprimer les marches aux limites des fokontany : 2,4 % ; plat 4,4 %, relief 1,0 %, rapport 4,5. **H-B2 robuste.**
- 📊 Les écarts se concentrent dans les **petits bassins côtiers** (12,4 % ; 11,1 % lissé) contre 1,6 % (1,4 %) dans
  les grands bassins ; plus concerné des grands : Androka (n° 20), environ 3 %. Hautes Terres sous 1 %.
- ❌ **Le classement par région n'est pas robuste** (Boeny 12,8 % → 7,6 % ; Androy 3,7 % → 1,0 % ; Sofia 6,3 % →
  7,8 %) : il n'est pas présenté comme résultat.
- ❌ Limites : profondeur approximative hors du Grand Sud ; pompages et échanges nappe-rivière ignorés ; un écart est un
  passage possible, pas un flux mesuré.
- 📌 Suite : les petits bassins côtiers, où la nappe peut passer d'un bassin à l'autre, sont aussi ceux des 36
  sous-bassins à bilan élevé ; à croiser une fois la recharge corrigée (contrôle de vraisemblance de la recharge).

### Contrôle de vraisemblance de la recharge, T2c (`validation/controle_recharge.md`)
- ✅ Protocole fixé avant calcul (09/11/2026) : bornes de R/P (quantiles 10 et 90 %) tirées des 134 sites africains du
  BGS par groupe d'aquifère × climat ; T2 ramenée dans ces bornes (T2c). Calcul local (entrées hors dépôt).
- ❌ **H-R2 non soutenue** : T2c place 2 références malgaches sur 8 dans son intervalle, contre 3 pour T2 (règle : au
  moins 5). Ankaranabo sort de l'intervalle : la borne basse remonte à 56 mm/an pour 46 mesurés.
- ❌ **H-R1 non vérifiée pour le Grand Sud** : aucune maille au-dessus de la borne haute. Les recharges trop fortes du
  Sud (Ihazoambo 262, Mahavelo 241, Nosiomby 208 mm/an, contre 22 à 48 mesurés) restent **plausibles au regard des
  sites africains** (R/P jusqu'à 0,25 sur le socle). Lecture : l'erreur du Sud n'est pas une invraisemblance
  physique ; c'est un écart propre à Madagascar (socle du Sud moins rechargé que ses analogues africains, ou
  fluctuation de nappe qui sous-estime), que des bornes africaines ne peuvent pas corriger.
- 📊 La borne basse joue : 30 % des mailles remontées (33 % hors du Grand Sud, 14 % dans le Grand Sud) ; recharge
  médiane 75 → 84 mm/an. Mahajanga : 7 → 67 mm/an (carte BGS : 124), correction dans le bon sens.
- ❌ Toliara inchangée (20 mm/an ; puits karstiques : 80 à 195) : la grille classe la maille en « Unconsolidated »,
  pas en sédimentaire ; la limite karstique annoncée par le protocole se vérifie.
- 📌 Décision fixée d'avance : T2 reste la valeur centrale ; le bilan de l'atlas est publié avec la fourchette T2 / T2c,
  et les sous-bassins dont la classe change sont marqués « incertains ». Piste ouverte pour la thèse : une
  correction propre à Madagascar, appuyée sur les mesures locales (fluctuation de nappe, puits karstiques), avec une
  validation croisée par site.

### Atlas avec la fourchette de recharge T2 / T2c (`validation/atlas_fourchette_recharge.md`)
- ✅ Décision appliquée telle que fixée avant le calcul (protocole du contrôle de recharge, section 5) : T2 reste la
  valeur centrale ; unité « incertaine » si sa classe de bilan change avec T2c. L'atlas T2 se reproduit à l'identique.
- 📊 Grands bassins : 108 sur 108 restent en bilan faible avec les deux recharges.
- 📊 Sous-bassins : **4 incertains sur 1 420**. Sur les 36 en bilan élevé, 33 le restent avec T2c ; 3 passent en
  modéré, tous à Mahajanga I (n° 7346, 7218, 7235). Un sous-bassin passe de faible à modéré.
- 📊 Mahajanga I : recharge 7 → 67 mm/an, bilan divisé par 10 (9,7 → 1,0 au plus fort), mais 8 sous-bassins restent
  au-dessus du seuil « élevé » : la pression de Mahajanga résiste à la correction.
- ❌ **« Stable » ne veut pas dire « robuste »** : à Toliara, Morombe, Maintirano et Morondava, T2c = T2 (8 à 31 mm/an,
  dans les bornes africaines du non consolidé aride). Leur classe ne change pas parce que la correction ne les touche
  pas, pas parce que leur recharge est confirmée. Toliara reste suspecte (puits karstiques : 80 à 195 mm/an).
- 📌 Suite : piste 2, correction de la recharge par les mesures malgaches (protocole à fixer avant calcul).

### Recharge corrigée par les mesures malgaches, T2L (`validation/recharge_locale.md`)
- ✅ Protocole fixé avant calcul (09/11/2026), effet du groupe d'aquifère déclaré comme déjà vu. 12 sites retenus
  (6 socle MGMERL, Sihanamaro, 5 puits GROSoM près de Toliara) ; 8 groupes de sites à moins de 20 km.
- 📊 Facteurs appris sur les 12 sites : socle ×0,19 ; autres ×3,52 ; unique ×0,80.
- ❌ **H-L1 non soutenue** : en laissant de côté les groupes de sites, M2 retrouve 2 sites sur 12 (M0 : 1) et l'erreur
  médiane passe de 0,69 à 0,90 (log₁₀). **H-L2 non soutenue** (M3 : 1 sur 12 ; 0,91 ; même conclusion à 10 et 50 km).
- 📊 **La validation site par site surestime la performance** : M2 y retrouve 4 sites et divise l'erreur par deux
  (0,33). L'écart vient des sites voisins (les 5 puits GROSoM forment un seul groupe) : 12 sites ne valent que 8
  informations indépendantes.
- 📊 Cause principale : le groupe « autres » du BGS réunit deux nappes de comportement opposé. Sihanamaro (Androy)
  reçoit moins que T2 ; les puits de Toliara, en partie karstiques, beaucoup plus. Sans Toliara, rien ne permet de la
  prédire, et réciproquement (Sihanamaro prédit à 449 mm/an pour 27 mesurés).
- 📊 Exploratoire (calculé après coup, pas un résultat) : sur le socle seul, l'erreur médiane passe d'environ 0,73 à
  0,43 avec M2 ; la correction du socle va dans le bon sens.
- 📌 Décision fixée d'avance : T2 reste la valeur centrale ; T2L est publiée comme sensibilité et **figée** (SHA-256
  dans le rapport) pour la validation prospective sur de nouvelles mesures.
- 📌 Conclusion de la série H-C6 → H-R2 → H-L1 : le transfert continental se trompe à Madagascar, dans des sens opposés
  selon la géologie ; des bornes continentales ne le corrigent pas ; une correction locale ne se généralise pas tant
  que la classification des aquifères ne sépare pas les nappes de comportement différent (karst, sables, socle) et
  que les sites mesurés ne couvrent pas plusieurs groupes indépendants par classe.

### Recharge du karst, T2K (`validation/recharge_karst.md`)
- ✅ Protocole fixé avant calcul et avant réception de la grille (09/11/2026). Part karstique f : grille à 0,5° de Wan,
  Döll et Müller Schmied (2024), CC BY 4.0. R/P du karst hors Madagascar, f ≥ 0,3 : aride 0,072 (47 mailles),
  humide 0,289 (32).
- ✅ Emprise plausible : 261 mailles sur 650 avec f > 0, 129 avec f ≥ 0,3, surtout dans la bande sédimentaire de l'Ouest
  (Mahafaly, Bemaraha, plateau de Mahajanga) ; Toliara f = 0,79 ; Ankarana seulement 0,06 à 0,5°.
- 📊 Formellement, **H-K1 soutenue** (3 sur 8, comme T2) et **H-K2 soutenue** (5 sur 5).
- ❌ **Mais H-K2 ne départage rien** : T2 place déjà les 5 puits dans son intervalle (11 à 195 mm/an). Le protocole
  affirmait à tort « T2 : 0 sur 5 » ; l'erreur est notée dans le protocole, sans changer la règle. Les valeurs
  centrales restent loin des mesures : puits GROSoM 80 à 195 mesurés, T2 38, T2K 43 ; maille de Toliara 20 → 30.
  **Aucune amélioration démontrée** à l'endroit qui motivait la correction.
- 📊 Effet fort ailleurs, non contrôlé par des mesures : Ouest humide 33 → 133 mm/an (médiane), Mahajanga 7 → 178
  (carte BGS : 124), recharge médiane des mailles karstiques 63 → 163.
- 📌 Décision : la règle fixée d'avance dit « T2K remplace T2 », mais la preuve est nulle (H-K1 sans gain, H-K2 non
  discriminante). **Application soumise au porteur du projet** avant tout recalcul de l'atlas. Carte T2K figée
  (SHA-256 dans le rapport) pour le test prospectif.
- 📌 Leçon de méthode : avant de fixer une hypothèse, vérifier sur les données déjà vues que la référence (ici T2)
  échoue bien au test ; sinon le test ne départage rien.
- 📌 Décision du porteur du projet (09/11/2026) : **option A**, T2K reste une sensibilité figée ; T2 reste la valeur
  centrale ; pas de recalcul de l'atlas.

### Puits à sec et recharge, test secondaire de T2, T2L et T2K (`validation/puits_a_sec.md`)
- ✅ Protocole fixé avant calcul (09/11/2026) ; cartes T2L et T2K figées, empreintes vérifiées conformes. 87 puits à sec
  (UNESCO 2024-2025, sans panne mécanique) contre 1 452 forages BushProof, 120 blocs de 20 km. Chlorure non lu.
- ❌ **H-P1 non soutenue** (sélection principale) : T2L − T2 = +0,111 d'AUC, intervalle −0,004 à +0,227 (manque de
  peu) ; T2K − T2 = +0,027 (−0,008 à +0,060).
- 📊 **T2 sépare à l'envers** : AUC 0,450 (0,359 à 0,536) ; les puits à sec sont plutôt là où T2 prédit plus de
  recharge (médiane 59 contre 55 mm/an). **T2L va dans le bon sens** : AUC 0,561 ; médiane 21 mm/an chez les puits à
  sec contre 52 chez la référence.
- 📊 Sensibilité (tous les puits « à sec », 310) : T2L − T2 = +0,138 (+0,051 à +0,221), gain atteint ; T2K sans gain.
- 📌 Lecture : sur des données indépendantes et récentes, la correction locale T2L (qui avait échoué en validation
  croisée, H-L1) va dans le bon sens et T2 dans le mauvais, mais le gain n'est pas établi selon la règle principale.
  Indice favorable à T2L, pas une preuve ; à confronter au bilan de chlorure (en pause). T2 reste la valeur centrale.
- ❌ Limites : puits signalés seulement ; causes d'assèchement multiples ; 2024-2025 ; zone ZH10 absente ; mailles
  grossières (nombreux ex aequo).

### Recharge par bilan de chlorure, Grand Sud (`validation/recharge_chlorure.md`, `recharge_chlorure_blocs.md`)
- ✅ Dépôt de chlorure de la pluie fixé avant lecture des chlorures (3 scénarios : Kwale, Kenya ; Van Wyk et al. 2011,
  Afrique du Sud ; valeurs vérifiées sur les sources primaires). 559 forages BushProof avec chlorure, 538 après filtres.
- ❌ **Le découpage fixé d'avance a échoué** : le lien simple à 20 km enchaîne les forages denses en 2 zones ; aucun
  test d'ordre possible. H-Cl1, H-Cl2 non soutenues faute de puissance ; H-Cl3 (karst) infaisable ; H-Cl4 sur un seul
  site. Leçon : avec un réseau dense, le lien simple fait une chaîne ; fixer des blocs ou un lien complet.
- 📊 Robuste dans les trois scénarios malgré tout : **T2 surestime** la recharge (biais +0,45 à +1,44 en log₁₀).
- 📊 **Analyse après coup, exploratoire** (blocs de 20 km, 36 zones, 530 forages ; aucune décision) :
  - recharge par chlorure médiane 4, 8 et 48 mm/an selon le scénario bas, central, haut ;
  - T2 surestime d'un facteur 6 à 11 (scénarios bas et central) et n'a pas de biais dans le haut ;
  - **T2L réduit l'écart d'au moins 30 % dans les scénarios bas et central** (1,16 → 0,62 ; 0,87 → 0,49), mais pas dans
    le haut (0,34 → 0,88), où T2L sous-estime ;
  - **les deux cartes ordonnent les zones à l'envers** (Spearman de −0,22 à −0,33), comme T2 pour les puits à sec.
- 📌 Lecture : le verdict entre T2 et T2L dépend du dépôt de chlorure de la pluie, **inconnu à Madagascar**. Mesurer
  le chlorure de la pluie dans le Sud (quelques collecteurs sur une saison) départagerait les deux. Aucune des deux
  cartes ne reproduit la répartition spatiale de la recharge : cohérent avec une recharge épisodique et en partie
  venue de loin (AVSF 2016 ; Taylor et al. 2013), que des cartes fondées sur le climat moyen local ne voient pas.

### Nappe régionale profonde : inverser le raisonnement (`validation/nappe_regionale.md`)
- ✅ Protocole fixé avant calcul (09/11/2026), avec trois ajouts du porteur du projet avant le calcul : inverser le
  raisonnement depuis la base ; la géologie reste le guide (intrusion marine, eaux fossiles, ions des sols) ; recharge
  étagée dans le temps (H-D6). Correction notée avant calcul : Cl/Na de l'eau de mer = 1,80 en masse.
- 📊 538 forages BushProof (517 en socle fracturé), 43 blocs de 20 km. Le cadre local n'explique pas le chlorure :
  ρ(Cl, pluie locale) = +0,20 [+0,03 ; +0,35].
- ✅ **H-D1 soutenue** : le chlorure diminue quand la charge augmente, ρ = −0,31 [−0,44 ; −0,18].
- ⚠️ **Mais le contrôle côtier l'efface** : à distance à la côte fixée, ρ = +0,08 [−0,08 ; +0,16]. La relation
  chlorure-charge passe par la position par rapport à la côte (charges basses près de la mer) ; ce test ne sépare pas
  un trajet le long de la nappe régionale d'une influence côtière.
- ✅ **H-D2 soutenue** : le chlorure augmente avec la profondeur captée, ρ = +0,18 [+0,10 ; +0,29].
- ❌ **H-D3 non soutenue** : la charge n'explique pas nettement mieux que la pluie locale (+0,11 [−0,09 ; +0,31]).
- ✅ **H-D4 soutenue** : au bloc, le rangement inversé de T2 disparaît à charge fixée (−0,22 → +0,09). L'inversion
  vient de la position dans le paysage (charge, donc côte et altitude), pas d'une erreur aléatoire.
- ❌ **H-D5 non soutenue** : la charge (interpolée) ne distingue pas les puits à sec (AUC 0,498).
- ❌ **H-D6 non soutenue de peu** : la minéralisation augmente avec la profondeur, ρ = +0,22 [+0,13 ; +0,32] (partie
  soutenue) ; le rapport Cl/Na baisse, ρ = −0,09 [−0,19 ; +0,01] (manque de peu). Le sens va dans celui de la recharge
  étagée dans le temps.
- 📊 **Cl/Na médian = 0,96, contre 1,80 pour l'eau de mer** : excès de sodium, venu des roches et des sols. Le sel
  des nappes du socle du Sud ne vient majoritairement ni d'une intrusion marine ni seulement des embruns ; il porte
  la marque de l'échange eau-roche (« ions des sols », hypothèse du porteur du projet).
- 📌 Décision fixée d'avance : H-D3 non soutenue → le cadre local reste. Mais trois acquis : (1) les inversions ont une
  cause de position (côte, altitude), pas le hasard ; (2) l'eau profonde est plus minéralisée ; (3) le chlorure des
  nappes du socle n'est pas un simple traceur de la pluie (Cl/Na bas), ce qui **fragilise le bilan de chlorure** lui-même
  dans le socle : une partie du chlorure peut venir des roches, et la recharge par chlorure y est alors sous-estimée.
- 📌 Suite : séparer côte et trajet régional (lignes d'écoulement BushProof, isotopes) ; tester les bassins
  sédimentaires et la côte avec d'autres données ; dater les eaux (tritium, carbone 14) pour mesurer le retard des
  nappes profondes.

### Analyse de puissance des tests de la recharge (`validation/analyse_puissance.md`)
- ✅ Aucune hypothèse testée : estimation, à partir de résultats publiés, du nombre d'unités indépendantes nécessaires
  (seuil 5 %, puissance 80 %, 4 000 simulations).
- 📊 **Puits à sec** : le gain observé de T2L (+0,11 d'AUC) n'avait qu'environ 46 % de chances d'être déclaré avec 120
  blocs ; le seuil de 0,05 du protocole aurait demandé environ 1 300 blocs. **Bilan de chlorure** : avec 36 blocs, ρ = 0,3
  n'avait que 43 % de puissance (85 blocs nécessaires).
- 📊 **Correction locale (type H-L1)** : la puissance plafonne vers 40 % et **baisse quand on ajoute des sites**, parce que
  la dispersion entre groupes de sites (0,53 en log₁₀) dépasse la demi-largeur de l'intervalle de mesure (0,29) : la
  règle « moitié des sites retrouvés » devient impossible. Avec une dispersion moitié moindre, 4 groupes par classe
  suffiraient (82 %).
- 📊 **Test prospectif** (« 60 % retrouvés ») : 41 nouveaux sites si la carte en retrouve vraiment 80 %, 177 si 70 %.
- 📌 Conséquences : (1) nos « non soutenus de peu » sont surtout des manques de puissance ; (2) pour la correction locale,
  il faut d'abord **réduire la dispersion** (classer les roches plus finement) et **l'incertitude de mesure** (essais de
  pompage pour le rendement spécifique), pas seulement ajouter des sites ; (3) **règle de méthode désormais appliquée** :
  calculer la puissance avant de fixer une hypothèse ; sous 50 %, le test est déclaré exploratoire dès le départ.

### Combinaison des preuves sur la recharge (`validation/combinaison_preuves.md`)
- ✅ Règles fixées avant le calcul (`protocole_combinaison_preuves.md`) ; **synthèse rétrospective** déclarée (lignes déjà
  vues). Lignes : L1 fluctuation de nappe (8 groupes), L2 puits à sec (120 blocs), L3 chlorure par blocs (36, après coup).
- 📊 **Q1, T2 surestime dans le Grand Sud** : L1 z = +1,76 ; L3 z = +5,23 (scénarios bas et central), +0,53 (haut).
  Combinée : +5,48 (bas, central), +1,23 (haut). Sans le chlorure : +1,76, indice.
- 📊 **Q2, T2L plus juste que T2** : L1 z = −0,20 ; L2 z = +1,88 ; L3 z = +3,94 (bas), +2,56 (central), −3,28 (haut).
  Combinée : +3,37 (bas), +2,74 (central), +0,10 (haut, avec contradiction forte). Sans le chlorure : +1,77, indice.
- 📌 **Le verdict dépend entièrement du dépôt de chlorure** : « établi » pour Q1 et Q2 si le dépôt est bas ou central,
  « indice » ou « non établi » s'il est haut. Aucun verdict global tant que MERRA-2 n'a pas désigné le scénario.
  Sans le chlorure, les deux questions restent au rang d'**indice concordant**.
- ⚠️ Réserves : L2 et L3 partagent la région et les forages ; le chlorure venu des roches (Cl/Na 0,96) abaisse la
  recharge par chlorure et favorise Q1 ; L1 a servi à construire T2L.
