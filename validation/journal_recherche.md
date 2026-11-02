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
