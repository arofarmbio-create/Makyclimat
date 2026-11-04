# État des lieux et registre des méthodes et des résultats

*Établi le 02/11/2026, en réponse aux sections 19 et 22 du protocole doctoral
(`protocole_doctoral_modelisation_climatique_Madagascar.txt`). Méthode : inventaire du dépôt (code, données, notes de
validation), de l'historique des workflows GitHub Actions et des sorties publiées, à cette date. Chaque chiffre est
copié d'un fichier cité ; aucun n'est arrondi ou recalculé pour ce document. Ce registre est tenu à jour à chaque
nouveau calcul, qu'il réussisse ou qu'il échoue (`prompt_maitre.md`, section 21).*

Légende des statuts : ✅ réussite (résultat validé ou positif) · ⚠️ partiel ou réserve · ❌ échec ou résultat négatif ·
⏳ en cours, pas encore de résultat · ⬜ pas commencé.

---

## 1. Réponses aux cinq questions du protocole (§19)

### Question 1 : résolution spatiale actuelle

**Réponse : variable selon les sources. La résolution dominante des données climatiques est 0,05° (environ 5,5 km).
Les résultats sont publiés jusqu'au fokontany, qui est souvent plus fin que la donnée.**

| Source | Résolution native | Niveau du protocole |
|---|---|---|
| CHIRPS v2.0 (pluie) | 0,05° (~5,5 km, ~30 km²), journalière, décadaire, mensuelle | N1 |
| GloFAS v4 (débits) | 0,05°, journalière | N1, N2 |
| ERA5-Land (ET0, sol) | 0,1° (~11 km), mensuelle | N1 |
| GPM IMERG V07 | 0,1°, 30 min | N1 |
| MODIS MOD13A3 (NDVI) | 1 km, mensuelle, agrégée à ~0,05° | N1 |
| Copernicus GLO-90 (relief, bassins) | 90 m | N1, N2 |
| WorldPop (population, moins de 5 ans) | 100 m | N3 |
| ESA WorldCover | 10 m | N1 |
| Unités administratives (OCHA COD-AB) | 24 régions, 120 districts, 1 645 communes, 17 465 fokontany | N3, N4 |

Surface des unités (calculée le 02/11/2026 depuis `data/mdg/units.csv`) :

| Niveau | Nombre | Surface médiane | Plus petites qu'une maille CHIRPS (~30 km²) |
|---|---|---|---|
| Région | 24 | 20 422 km² | 0 % |
| District | 120 | 4 564 km² | 5 % |
| Commune | 1 645 | 196 km² | 9 % |
| Fokontany | 17 465 | 12,6 km² | **74 %** |

**Constat (risque 2 du protocole, résolution artificielle) :** pour les trois quarts des fokontany, la valeur de pluie
publiée est celle d'une maille plus grande que le fokontany lui-même (lecture au centroïde). Deux fokontany voisins
reçoivent souvent la même valeur. La résolution effective de la pluie au fokontany est donc la maille CHIRPS, pas le
fokontany. Action : afficher la résolution effective sur chaque indicateur et privilégier la commune ou le district pour
les indicateurs de pluie (voir section 4).

### Question 2 : profondeur historique des données

**Réponse : plus de 20 ans pour le climat, beaucoup moins pour les impacts observés, qui limitent la validation.**

| Donnée | Période disponible |
|---|---|
| Pluie CHIRPS | 1981 à aujourd'hui (45 saisons) |
| ERA5-Land | 1981-2025 utilisé (disponible depuis 1950) |
| ENSO (ONI) et dipôle de l'océan Indien (DMI, ERSST v5) | 1950 à aujourd'hui |
| IMERG V07 Final | 1998 à septembre 2025 |
| NDVI MODIS | 2000 à aujourd'hui |
| Rétroprévisions GloFAS v4 (EWDS) | 2003 à aujourd'hui (pas 1999 : vérifié par l'API) |
| Rétroprévisions saisonnières C3S | 1993-2016 |
| Cyclones documentés (`evenements.csv`) | 21 cyclones, 1994-2026, dont 16 avec liste de régions touchées |
| Cartographie satellite de crise (Copernicus EMS) | 8 activations exploitables (2018-2026) |
| DesInventar (fiches BNGRC) | 2 402 fiches, dont 425 utilisables pour la vérification (~19 épisodes indépendants) |
| Sécheresse documentée | 1 épisode (Grand Sud 2019-2022) |
| Glissements de terrain (NASA COOLR) | 8 événements |

**Constat (risque 1 du protocole) :** le facteur limitant n'est pas le climat mais la vérité terrain des impacts. Un
seul épisode de sécheresse et 8 glissements ne permettent pas de calibrer un seuil ; ils permettent seulement une
vérification descriptive.

### Question 3 : observations hydrogéologiques

**Réponse : quelques relevés directs, sans série temporelle. Aucun réseau piézométrique suivi.**

- Niveau statique de forages et puits MGMERL (UNICEF, mWater) : environ 1 000 relevés récents extraits à la main le
  27/10/2026, sur 25 271 forages enregistrés. Couverture : 5 162 fokontany sur 17 465 (30 %) à moins de 15 km d'un
  forage mesuré ; profondeur médiane 4,5 m.
- Conductivité électrique (indicateur indirect de salinité), même source : environ 23 % du pays.
- Pas de série piézométrique dans le temps, donc pas de fluctuation saisonnière observée.
- Pas d'API : l'extraction ne peut pas être automatisée (exception documentée à la règle des mises à jour
  automatiques).
- Géologie : carte au 1:5 000 000 seulement.
- Source abandonnée : carte continentale BGS (MacDonald et al. 2012). Son emprise s'arrête à 40,8°E et **ne couvre pas
  Madagascar** (vérifié le 27/10/2026).

**Constat (risque 7 du protocole) :** le module M3 ne peut pas calibrer un modèle de nappe (MODFLOW exclu à ce stade).
Il reste au niveau « diagnostic et indicateurs non validés » (`groundwater_limites.md`). L'export complet MGMERL
(accès membre) ou des données du ministère de l'Eau changeraient cette situation.

### Question 4 : hébergement de la plateforme

**Réponse : cloud gratuit, sans serveur propre.**

- Calculs : GitHub Actions (26 workflows, dont 16 programmés, de toutes les 6 heures à une fois par an).
- Site : GitHub Pages (statique, `docs/`).
- Gros fichiers intermédiaires : versions (releases) GitHub (par exemple `secheresse-series`).
- Comptes de données : NASA Earthdata, Copernicus CDS et EWDS (secrets GitHub, vérifiés chaque mois).
- Limites : 6 heures par tâche, ce qui fait échouer ou annuler les téléchargements longs (voir R-21 à R-24), et un
  réseau parfois instable vers les serveurs de la NASA.

### Question 5 : documentation technique disponible

**Réponse : plusieurs éléments existent déjà.**

- Code source Python : 74 scripts (11 527 lignes), 39 fichiers de tests automatiques (CI à chaque envoi).
- Notes de validation et protocoles : 24 documents dans `validation/`, dont 5 protocoles écrits avant calcul.
- Journal daté des réussites et échecs : `validation/journal_recherche.md` (depuis le 29/10/2026).
- Synthèse méthodologique : `validation/methodologie_these.md` ; correspondance avec le cahier des charges :
  `validation/charte_methodologique.md`.
- Mode d'emploi et calendrier des mises à jour : `README.md`.
- Manque : une fiche de reproductibilité par simulation avec tous les champs du protocole §15 (version des données,
  paramètres, résolution effective). Le présent registre en est la première étape.

---

## 2. Registre des méthodes et des résultats

Colonnes : identifiant, module (M) et expérience (E) du protocole, méthode, données et validation, résultat chiffré,
statut, document détaillé.

### 2.1 Cyclones et impacts (M4, M5 ; E4)

| ID | Méthode | Données et validation | Résultat | Statut | Détail |
|---|---|---|---|---|---|
| R-01 | Régression logistique : classement des régions touchées par un cyclone (vent ≥ 34/50/64 nœuds, pluie) | 16 cyclones 1994-2026, 24 régions ; un événement laissé de côté | AUC 0,84 ; 87 % des régions citées dans les 8 premières sur 24 ; probabilités non calibrées | ✅ | `README.md`, `cyclones_*.csv`, `modele_cyclone.json` |
| R-02 | Régression logistique : quels fokontany sont touchés, dans une zone déjà atteinte | 5 880 fokontany-événements, 8 activations Copernicus EMS ; événement laissé de côté | Vent et pluie : AUC 0,51-0,52 (hasard). Terrain seul : AUC 0,79 (fokontany), 0,82 (commune) ; Brier 0,176-0,180 contre 0,234-0,236 pour la référence | ✅ résultat de thèse : le signal utile change avec l'échelle | `methodologie_these.md` §4.2 |
| R-40 | R-02 bis : avec un aléa fin (pluie IMERG sur 1, 3 et 6 heures, vent de Holland), le terrain domine-t-il encore l'aléa à l'intérieur des zones touchées ? | `protocole_r02bis_echelle_alea.md` ; recherche bibliographique systématique à consigner | Protocole écrit avant calcul ; données IMERG et ERA5 demandées à l'agent de téléchargement | ⏳ | `biblio_r02_nouveaute.md` |
| R-03 | Même modèle pour les dégâts aux bâtiments | 159 cas positifs sur 5 880 | AUC 0,16-0,62 selon la variante, instable | ❌ | idem |
| R-04 | Seuils simples d'action anticipée pour les cyclones | Mêmes données que R-01 | Meilleur cas POD 0,92, FAR 0,71 : aucun seuil acceptable | ❌ | `declencheurs_anticipation.md` |
| R-05 | Extension de la vérité terrain EMS | 4 activations ciblées | 1 seule exploitable (fichier invalide pour une, aucune couche pour deux) : 75 % d'échec | ❌ | `evenements_2020_2026_note.md` |
| R-06 | Corroboration des chiffres d'impact avec EM-DAT (usage interne) | 9 événements comparables | Personnes touchées : accord quasi exact pour 7 sur 9 ; décès plus bas chez nous (rapports précoces) | ✅ | `emdat_corroboration.md` |

### 2.2 Inondations (M2, M4 ; E2, E4)

| ID | Méthode | Données et validation | Résultat | Statut | Détail |
|---|---|---|---|---|---|
| R-07 | Seuils de crue par commune : débit GloFAS contre crues de 2, 5 et 20 ans (loi de Gumbel) | 174 communes (148 mailles GloFAS) du périmètre pilote | Avec au moins 1 commune en alerte : 3 inondations documentées sur 3 détectées, 6 épisodes simulés sans correspondance sur 20 | ⚠️ détection bonne, fausses alertes à vérifier | `crues_validation.md` |
| R-08 | Débit simulé contre communes inondées (EMS, Ava) | 58 communes (47 inondées) | AUC 0,55 ; 26 % des inondées et 27 % des non inondées en vigilance | ❌ ne sépare pas les communes | idem |
| R-09 | Inondation pluviale : pluie sur 3 jours, seuil local | 1 977 fokontany, 11 saisons (2015-2026) | 2 inondations sur 3 détectées ; 4 épisodes sans correspondance sur 9 ; AUC communes EMS 0,36 | ❌ | `crues_pluviales_validation.md` |
| R-10 | Inondation pluviale : ruissellement SCS-CN | idem | 3 sur 3 détectées ; 7 sans correspondance sur 15 ; AUC 0,17 | ❌ | idem |
| R-11 | Prévision de crue d'ensemble (GloFAS, 51 membres, 30 jours) | 171 communes ; affichée à côté du niveau d'alerte | En production ; fiabilité des probabilités non mesurée | ⏳ dépend de R-21 | `journal_recherche.md` |
| R-12 | Tendance des crues à 2-4 semaines (jours 17-30), district et région | Ensemble GloFAS | En production ; fiabilité non mesurée (rétroprévisions limitées à 15 jours) | ⏳ | idem |
| R-13 | Glissements de terrain : seuil mondial pluie et pente (Guzzetti et al. 2008) | 8 événements COOLR | Règle non calibrée localement | ⚠️ non validé | `eboulements_pluie.csv`, `charte_methodologique.md` |

### 2.3 Sécheresse et eau (M1, M2, M3 ; E2)

| ID | Méthode | Données et validation | Résultat | Statut | Détail |
|---|---|---|---|---|---|
| R-14 | SPI-12 régional (loi gamma, OMM n° 1090) | CHIRPS 1981-2025 ; sécheresse du Grand Sud 2019-2022 | Les 3 régions sont en tête en 2020-2021 (SPI ≤ −1,91, rangs 1, 3 et 8 sur 24) | ✅ descriptif, N = 1 épisode | `secheresse_spi.md` |
| R-15 | Seuil opérationnel (pluie < 75 % de la normale) | 6 paires région-saison | POD 0,50 ; SPI-12 minimum : POD 1,00 mais FAR 0,96 | ❌ | `secheresse_pod_far.md` |
| R-16 | Proxys de type SPEI tirés du bilan hydrique (sm_z, recharge12_z) | Même épisode | POD 0,17 et 0,00 : moins bons que le SPI | ❌ | `spei_approche.md` |
| R-17 | SPI-1/3/6/12 à fin septembre 2026 | CHIRPS | État avant la saison 2026-2027, par région | ✅ | `spi_fin_septembre_2026.md` |
| R-18 | Bilan hydrique mensuel FAO-56, recharge, humidité du sol, par fokontany et sous-bassin | CHIRPS, ERA5-Land, SoilGrids, GLO-90 | En production ; pas de mesure de sol ni de débit pour valider | ⚠️ standard, non validé localement | `groundwater_limites.md` |
| R-37 | Défaut trouvé le 02/11 : ruissellement SCS-CN appliqué au cumul mensuel dans le bilan (depuis le 27/10) | Contrôle des indices aux 16 sites MGMERL | Excédent nul dans 99,6 % des fokontany ; indice de nappe constant, et potentiel pour point d'eau faussé (recharge pesant 25 %). Corrigé le 02/11 : plus de SCS-CN mensuel | ❌ 🔧 | `journal_recherche.md`, `protocole_nappes_mgmerl.md` §9 |
| R-19 | Potentiel pour point d'eau peu profond (somme pondérée de 4 critères) | Pas de forage réel pour calibrer | Classement relatif, poids non appris | ⚠️ non validé | idem |
| R-20 | Vulnérabilité cumulative (chocs cyclone et sécheresse, demi-vie 18 mois) | Pas d'enquête de résilience pour valider | Construction raisonnée | ⚠️ non validé | `vuln_cumul_limites.md` |

### 2.4 Chapitres de recherche lancés le 29/10/2026 (protocoles écrits avant calcul)

| ID | Question | Protocole | État au 02/11/2026 | Statut |
|---|---|---|---|---|
| R-21 | Les probabilités de crue GloFAS sont-elles fiables, vérifiées par les impacts DesInventar ? | `protocole_verification_impact.md` | Téléchargement des rétroprévisions 2003-2023 : 14 années réussies ; **2005 à 2011 annulées** à la limite de 6 heures (01/11). Validation pas encore lancée. Cause trouvée le 02/11 : file d'attente EWDS pleine (années lancées deux par deux), 17 mois sur 126 seulement ; corrigé et relancé le 02/11 | ⏳ 🔧 |
| R-22 | Une prévision saisonnière hybride (C3S et ENSO/IOD) bat-elle chaque source seule ? | `protocole_saisonnier_multimodele.md` | Tâche annulée après 6 heures le 29/10, rien gardé (publication en fin de tâche) ; corrigé (publication système par système) et relancé le 02/11 | ⏳ 🔧 |
| R-23 | L'intensité infra-journalière (IMERG) détecte-t-elle mieux les inondations pluviales que le cumul ? | `protocole_intensite_imerg.md` | 5 saisons sur 11 téléchargées ; 2014, 2015, 2016, 2019, 2020, 2021 en échec (« liste des fichiers inaccessible » sur le serveur NASA) ; attente allongée et 6 saisons relancées le 02/11 | ⏳ 🔧 |
| R-24 | Le SPEI suit-il mieux le stress de la végétation (NDVI) que le SPI ? | `protocole_spei_ndvi.md` | Fait le 03/11 (`spei_ndvi.md`) : H1 soutenue (secs : SPEI meilleur dans 31 districts sur 36, p < 0,001) ; H2 non soutenue (le SPEI gagne aussi en zone humide, écarts faibles) ; ET0 ERA5-Land inférieure de 7 à 27 % à Open-Meteo | ✅ H1 |

### 2.4 bis Expérience E1 : fusion et qualité des sources de pluie

| ID | Question | Protocole | État au 02/11/2026 | Statut |
|---|---|---|---|---|
| R-35 | La fusion contrôlée de CHIRPS, IMERG Late et ERA5-Land, pondérée par triple collocation, bat-elle la meilleure source seule (stations GSOD, pentades, 2016-2025) ? | `protocole_e1_fusion_pluie.md` | Fait le 03/11 (`e1_fusion_pluie.md`) : triple collocation IMERG r = 0,90, CHIRPS 0,87, ERA5-Land 0,84 ; H1-E1 et H1-E1b non soutenues (2 stations sur 5, p = 0,81) ; seulement 5 stations GSOD utilisables, test sans puissance ; H3-E1 : IMERG nettement meilleur sur les versants au vent et la côte (`e1_relief.md`) ; §6.3 : impacts non départagés, moins de fausses alertes de crue pour B et C (`e1_impacts.md`) | ❌ non démontré |

### 2.4 ter Eaux souterraines : niveaux mesurés (MGMERL)

| ID | Question | Protocole | État au 02/11/2026 | Statut |
|---|---|---|---|---|
| R-36 | Le SPI et l'indice de recharge du système suivent-ils les niveaux de nappe mesurés par 16 dataloggers MGMERL dans le Grand Sud (2019-2025) ? | `protocole_nappes_mgmerl.md` | 7 sites retenus sur 16. H-N1 : 5/7 sites avec r(SPI-12) > 0, p = 0,23 (non soutenue) ; H-N2, H-N3a, H-N3b non soutenues (excédent, SPEI-12 avec ET0, bilan P − ETR : pas mieux que le SPI). Cumul optimal de 9 à 24 mois selon le site | ❌ négatif, faible puissance (`nappes_mgmerl.md`) |
| R-38 | Carte nationale des nappes interrogeable en un point GPS (profondeur, type, âge, salinité, fluor, potentiel) : les cartes mondiales sont-elles justes à Madagascar, et un modèle hybride recalé sur les forages malgaches fait-il mieux hors des zones d'apprentissage ? | `protocole_carte_nappes.md` | Protocole écrit avant calcul (H-C1 à H-C4, validation par blocs d'environ 100 km). Couches obtenues le 02/11 : profondeur de nappe (Fan), fluor, GLHYMPS, GLiM, profondeur du socle ; base mondiale de salinité sans aucun point à Madagascar ; recharge mondiale de Jung et al. 2024 non publiée en accès libre ; recharge africaine de MacDonald et al. 2021 derrière un formulaire BGS H-C1 (02/11) : écart médian Fan − forages +12,9 m (Wilcoxon p < 0,001), mais non confirmé par blocs (16/36, p = 0,62) ; Spearman 0,02 ; écart faible en fond de vallée, +24 m sur versants et plateaux (`nappes_hc1.md`). H-C5 (02/11) confirmée : transfert de la recharge entre pays africains, erreur médiane 0,24-0,28 contre 0,62 pour la référence naïve, T1 26/30, T2 24/29 (`transfert_recharge_hc5.md`). H-C2 (02/11) non confirmée : hybride 2,8 m contre Fan 6,4 m (23/25 blocs, p < 0,001) et krigeage 3,1 m (16/25, p = 0,115) ; intervalle de 80 % couvrant 76 % (`nappes_hc2.md`). H-C2b (02/11) non confirmée : régions laissées de côté, hybride meilleur que le krigeage dans 6 régions sur 8 (Sava 1,4 contre 3,9 m), Wilcoxon p = 0,16 (`nappes_hc2b.md`). H-C6 (03/11) non confirmée : 3 références malgaches sur 8 dans l'intervalle de 80 % (seuil 60 %), surestimation aux 5 sites manqués ; 42 % des mailles sans analogue africain proche (`transfert_recharge_hc6.md`). ⚠️ (03/11) Calculé sur un extrait de 1 000 relevés MGMERL (limite d'affichage) : à refaire sur les données complètes. Recharge par fluctuation (04/11, 12 sites) : T2 surestime sur le socle (6 sur 7), sous-estime dans le sédimentaire de Toliara (5 sur 5) ; pas de correction régionale (`recharge_fluctuation.md`). | ⏳ |

### 2.4 quater Océan, pluies extrêmes et recharge des nappes (H-N7)

| ID | Question | Protocole | État au 02/11/2026 | Statut |
|---|---|---|---|---|
| R-39 | L'état de l'océan avant la saison (ONI, DMI, SIOD, canal de Mozambique) annonce-t-il les mois de pluie extrême du Grand Sud, et ces mois font-ils remonter les nappes ? Relief (au vent ou sous le vent) et géologie (karst ou socle) décrits à part | `protocole_climat_extremes_nappes.md` | Protocole écrit avant calcul ; maillon B exploratoire sur les 7 sites MGMERL, confirmatoire sur des sites indépendants à obtenir | ⏳ |

### 2.4 quinquies Module eaux souterraines (protocole-cadre)

| ID | Question | Protocole | État au 03/11/2026 | Statut |
|---|---|---|---|---|
| R-41 | Carte nationale du niveau statique avec sa précision connue, puis recharge, volume, renouvellement et risque d'épuisement, prévus à court, moyen et long terme | `protocole_cadre_eaux_souterraines.md` | Phase 0 faite (03/11) : 11 régions sur 24 sans forage ; S0 par région, hybride 3,4 m [1,9 ; 5,6], krigeage 4,1 m [3,2 ; 5,4], Fan 9,1 m ; intervalle de 80 % trop étroit loin des forages (65 % au-delà de 100 km) (`nappes_phase0_audit.md`). Phase 1 faite (03/11) : saison, SPI-3 et SPI-12 rejetés (critère 1 : 3,39 → 3,53 m ; critère 2 : 3,17 → 3,10 m, non démontré) (`nappes_phase1.md`). Intervalle calibré selon la distance (03/11) : couverture 76 à 84 % dans chaque classe (critère atteint), mais 65 % en Atsimo-Andrefana et 50 % en Menabe (`nappes_intervalle.md`). Carte nationale v1 (03/11) : 17 453 fokontany ; 52 % en extrapolation, dont presque toutes les Hautes Terres (précision inconnue) ; Grand Sud fiable au sens mesuré, erreur médiane 2,4 m (`nappes_carte_nationale.md`) ⚠️ (03/11) Calculé sur un extrait de 1 000 relevés MGMERL (limite d'affichage) : à refaire sur les données complètes. Ressource v1 (04/11, carte v2) : renouvellement 41 % rapide, 13 % peu renouvelable ; risque domestique faible à 93 % (borne basse : recharge du Sud surestimée, bétail non compté) ; Antananarivo 13 % à 86 % en risque élevé selon la desserte JIRAMA (`nappes_ressource.md`). | ⏳ |
| R-42 | Les données SEAM du ministère de l'Eau (points d'eau, population par commune) sont-elles utiles à MakyClimat ? | `protocole_seam_points_eau.md` | Fait le 03/11 (`seam_utilite.md`) : 45,8 % de positions par défaut ; relevés MGMERL plus secs que les forages du pays (24 % hors étendue) ; part de puits : lien faible (H-S1b, ρ = −0,11) sans gain pour la carte ; population par commune complète, retenue pour le risque d'épuisement ⚠️ (03/11) Calculé sur un extrait de 1 000 relevés MGMERL (limite d'affichage) : à refaire sur les données complètes. | ✅ partiel |
| R-43 | Le transfert de connaissances depuis des régions analogues (géologie, climat) prédit-il la recharge malgache mieux que le transfert africain ? | `protocole_transfert_analogues.md` | Fait le 04/11 (`transfert_analogues.md`) : niveau 1 réussi (22 pays sur 29, p = 0,004) ; H-T1 soutenue (10 sites sur 12, p = 0,019) ; H-T2 non soutenue (ordre spatial faux) ; H-R1 non soutenue ; typage GLiM 0,5° trop grossier (47 % d'accord) Reprise GLiM vectorielle (04/11) : H-T1 11/12 (p = 0,003), H-T2 toujours non soutenue, accord 58 % < 70 % : conclusion inchangée (`transfert_analogues_vectoriel.md`). | 🟡 plausible, non démontré |

### 2.5 Prévision saisonnière et planification (M1, M7 ; E6)

| ID | Méthode | Données et validation | Résultat | Statut | Détail |
|---|---|---|---|---|---|
| R-25 | Régression ONI et DMI de juillet-septembre → pluie de la saison, par région | 45 saisons ; validation croisée, test chronologique, permutation, Benjamini-Hochberg | Novembre-janvier : 3 régions sur 24 (Menabe avec ONI ; Sava et Diana avec ONI + DMI). Janvier-mars et saison entière : 0 sur 24 | ⚠️ signal faible et local, à confirmer (contrôle multiple par combinaison seulement) | `teleconnexions.md` |
| R-26 | Même approche à 12 mois (saison 2027-2028), 4 épreuves dont le RPSS | 45 saisons | 0 région sur 24 pour toutes les périodes et modèles (MSSS médian −0,03 à −0,08 ; RPSS −0,01 à −0,05) : scénarios climatologiques | ❌ résultat négatif, publié | `planification_12mois.md` |
| R-27 | Scénarios de fin de saison par analogues, en laissant une saison de côté | 45 saisons, 3 000 points | En début de saison (0 mois observé) : erreur 15,3 points, comme la climatologie ; couverture P10-P90 0,77 | ⚠️ pas de gain en début de saison, attendu | `docs/data/mdg/hindcast.json` |
| R-28 | Tendance de la pluie de saison et effet d'El Niño et de La Niña depuis 1982 | CHIRPS, ONI | Publié par région et district | ✅ descriptif | `scripts/build_climate_change.py` |
| R-29 | Persistance d'El Niño | 8 années comparables depuis 1950 | L'année suivante n'a jamais été El Niño (4 La Niña, 4 neutres) | ✅ | `journal_recherche.md` |

### 2.6 Données et chaîne de traitement (M0 ; E1)

| ID | Méthode | Résultat | Statut |
|---|---|---|---|
| R-30 | Contrôle qualité avant publication (`validate.py`) | Bloque la publication sur anomalie. Fausse alerte du 01/11 au 02/11 (repli de début de saison jugé trop ancien), corrigée le 02/11 | ⚠️ 🔧 |
| R-31 | Surveillance des adresses des sources | Déplacement du serveur CHIRPS (28/10) : environ 9 heures de mises à jour en échec | ❌ 🔧 |
| R-32 | Dates des fiches DesInventar | 87 fiches cycloniques de 2018 portent leur date de saisie : exclues ; règle de détection écrite et testée | ✅ résultat transférable |
| R-33 | ET0 Penman-Monteith depuis des moyennes mensuelles ERA5-Land | Exemple 17 du guide FAO-56 retrouvé à 2 % près (5,61 contre 5,72 mm/jour) | ✅ |
| R-34 | Loi log-logistique du SPEI (Vicente-Serrano 2010) | Échoue sur un échantillon faiblement asymétrique (test automatique) ; remplacée par la loi logistique généralisée de Hosking | ❌ 🔧 |

---

## 3. Couverture du protocole doctoral

| Élément du protocole | Couverture actuelle | Manque principal |
|---|---|---|
| M0 Gouvernance des données | Partielle : format commun, contrôle qualité, sources citées, historique git | Données brutes pas toujours conservées à part ; pas d'indicateur de qualité par observation ; pas de version des données par simulation |
| M1 Climatologie | Pluie forte ; température seulement à travers l'ET0 et les alertes à 7 jours | Aucune station DGM ; pas de comparaison satellite et stations |
| M2 Hydrologie de surface | Bassins (GLO-90), bilan hydrique, seuils GloFAS | Aucune station hydrométrique publique ; pas de modèle pluie-débit calibré (GR4J, HBV) |
| M3 Hydrogéologie | Relevés ponctuels MGMERL, conductivité | Pas de série piézométrique (voir question 3) |
| M4 Géorisques | Cyclones, inondations, sécheresse ; glissements par règle mondiale | Inventaire local des glissements ; érosion absente |
| M5 Impacts territoriaux | Population, moins de 5 ans, routes, écoles, santé, cultures | Ponts et bâtiments ; dommages observés pour la validation |
| M6 Analyse humanitaire | Personnes exposées et ciblées, femmes enceintes estimées, prix du riz | Indicateurs sectoriels JIAF (WASH, santé, éducation…) seulement partiels |
| M7 Validation et prospective | Validation par événement laissé de côté, scores de compétence saisonniers | Pas de projections CMIP6 ; pas d'analyse de sensibilité systématique |
| E1 Fusion et qualité | Non fait comme expérience | Comparaison source seule, sources combinées et sources harmonisées |
| E2 Modèles physiques | Bilan hydrique, SCS-CN, ET0 FAO-56 | Modèle pluie-débit ; bilan P + I = ET + Q + ΔS fermé par bassin |
| E3 Physique, statistique, IA, hybride | Statistique (régressions) ; hybride C3S lancé (R-22) | Pas d'IA ni d'ablations ; jeux d'impacts trop petits pour l'apprentissage automatique |
| E4 Validation historique | Événement laissé de côté (R-01, R-02) | Séparer reconstitution, anticipation et en cours d'événement ; journal des données disponibles à chaque date |
| E5 Humanitaire | Indicateurs d'exposition | Rattachement explicite au JIAF 2 |
| E6 Prospective | Saisonnier et 12 mois (R-25, R-26) | Projections CMIP6 SSP1-2.6, SSP2-4.5, SSP5-8.5 |
| E7 Sensibilité | Multiplication de la pluie de ×0,5 à ×1,5 sur le site | Sensibilité aux paramètres, cartes d'incertitude |
| §11 Validation spatiale par blocs | Absente | Validation croisée par blocs spatiaux |
| §15 Reproductibilité | Code et résultats versionnés | Fiche par simulation (champs du §15) |

---

## 4. Ce que l'état des lieux impose pour la suite

Le protocole (§22) dit que la prochaine étape n'est pas d'ajouter des modèles. Les priorités qui découlent des
constats ci-dessus :

1. **Terminer les quatre chapitres déjà lancés (R-21 à R-24)** : protocoles écrits, données presque prêtes, seuls des
   téléchargements bloquent. Ce sont les résultats les plus proches et les plus originaux.
2. **Résolution effective (risque 2)** : publier la résolution effective de chaque indicateur et mesurer combien de
   fokontany partagent la même maille de pluie.
3. **Expérience E1** : comparer CHIRPS, IMERG et ERA5-Land entre eux, sans station, sur les mêmes zones et périodes.
   Le désaccord entre sources est une mesure d'incertitude de l'observation.
4. **E4 sans fuite temporelle** : rejouer les scores d'anticipation avec seulement les données disponibles à chaque date.
5. **E6** : projections CMIP6 pour la pluie et la température, avec un protocole écrit avant calcul.

Noyau scientifique proposé (protocole §21), cohérent avec les résultats déjà obtenus : **vérification des prévisions
d'aléas hydroclimatiques par les impacts observés, dans un pays presque sans stations**. R-02, R-07, R-21 et R-24 en
sont les briques ; l'hydrogéologie et les glissements restent des extensions, faute de données.

## 5. Tenue du registre

- Chaque nouveau calcul reçoit un identifiant R-xx, une ligne ici et une entrée datée dans `journal_recherche.md`.
- Un échec n'est jamais effacé : il change de statut (par exemple ❌ 🔧 puis ✅) et garde son historique.
- Les chiffres sont mis à jour seulement à partir d'une sortie réelle d'un script, avec son fichier cité.
