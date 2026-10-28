# Diagnostic initial — saison 2026-2027 (date de référence : 28/10/2026)

Réponse à la section 17 du cahier des charges (`prompt_maitre.md`). Complète `charte_methodologique.md`
(27/10/2026), qui décrit déjà ce que MakyClimat fait section par section ; ce document ne la répète pas.

Convention : **[vérifié]** = consulté directement à la source le 28/10/2026 ; **[secondaire]** = repris
d'une synthèse (presse, agrégateur), source primaire non lue ; **[calcul MakyClimat]** = sortie du
pipeline publiée sur le site, mise à jour du 27/10/2026 22:21 UTC ; **[non fait]** = pas encore analysé.

## 1. État climatique actuel

| Élément | Constat | Source, date | Statut |
|---|---|---|---|
| ENSO | Avis El Niño en cours. Niño-3.4 à +2,1 °C. El Niño fort à très fort probable jusqu'en janvier-mars 2027 (> 83 %). | NOAA CPC, discussion ENSO du 08/10/2026 | [vérifié] |
| ENSO (indice) | ONI de juillet-septembre 2026 : +2,16 | NOAA, via `connector_enso.py` | [calcul MakyClimat] |
| Dipôle de l'océan Indien (IOD) | Neutre fin septembre ; épisode positif bref possible, force et durée incertaines | BoM, perspectives du 24/09/2026 et vidéo du 01/10/2026 | [secondaire] : pas de bulletin d'octobre trouvé, à vérifier |
| Perspective nationale | Octobre-décembre : sous la normale sur une partie du Sud et du Sud-Ouest ; normale à supérieure sur le Nord et l'Est. Températures au-dessus de la normale. 0 à 2 systèmes cycloniques impactant directement le pays. | Météo Madagascar, perspectives 2026-2027 du 01/10/2026 | [secondaire] : le PDF officiel a été téléchargé mais son texte n'a pas pu être extrait ici |
| Perspective régionale | Janvier-mars 2027 : normale à sous la normale sur Madagascar. Le découpage en zones est confus dans les extraits. | SARCOF-33 (SADC), 28/08/2026 | [secondaire] : PDF officiel inaccessible (connexion coupée) |
| Prévision saisonnière par région | Les 24 régions sont plafonnées à 50 % de probabilité de pluie sous la normale (borne de l'outil). Anomalie de novembre à mars : de −25 % (Atsimo-Andrefana) à −7 % (Sava). | ECMWF SEAS5 via Open-Meteo, émise le 26/10/2026 | [calcul MakyClimat] |
| Sécurité alimentaire | IPC phase 3 à Toliara II et Amboasary Atsimo, en extension sur le Grand Sud et le Grand Sud-Est à partir d'octobre. Soudure précoce : stocks épuisés en septembre. Manioc semé tôt dans l'Androy, vulnérable. | FEWS NET, Key Message Update septembre 2026 - janvier 2027 | [vérifié] |
| Événement récent | Premier système de la saison (Agueda) formé au large d'Antsiranana le 20/10/2026, sans alerte cyclonique | Presse malgache, 21/10/2026 | [secondaire] |
| Pluie observée depuis le début de l'année hydrologique | **Fait jusqu'à fin septembre** (mise à jour du 28/10) : SPI-12 ≤ −1 dans 6 régions du Sud et du Sud-Est (Anosy −1,63) ; juillet-septembre 2026 anormalement humide sur les Hautes Terres (1er ou 2e rang sur 36 ans d'après ERA5). Voir `spi_fin_septembre_2026.md`. **Octobre** (CHIRPS provisoire jusqu'au 20/10) : pas encore lu. | CHIRPS + ERA5, calcul du 28/10/2026 | [calcul MakyClimat] jusqu'à septembre ; [non fait] pour octobre |
| Sols et végétation | Bilan hydrique mensuel en place. NDVI non connecté. | `build_soilwater.py` | Partiel |

### Divergences entre prévisions

1. **Nord et Est.**
   - SEAS5 donne une saison **plus sèche que la normale partout**, y compris Sava (−7 %), Diana (−10 %), Analanjirofo et Atsinanana (environ −14 %).
   - Météo Madagascar et la synthèse régionale annoncent au contraire **normal à supérieur** sur le Nord et l'Est.
   - C'est la divergence principale. Elle ne peut pas être tranchée sans la fiabilité historique de SEAS5 sur ces régions, qui n'a pas encore été mesurée.
2. **Grand Sud.** Les sources convergent (SEAS5, Météo Madagascar, FEWS NET) vers une saison sous la normale. C'est le signal le plus cohérent.
3. **Plafond de 50 %.** La borne de 15 à 50 % appliquée par MakyClimat écrase le signal : on ne peut pas distinguer une région à 51 % d'une région à 80 %. À revoir.

### Ce qu'El Niño permet de dire, et ce qu'il ne permet pas

La validation croisée du moteur de scénarios par analogie (`hindcast.json`, 45 saisons de 1982 à 2026,
une saison laissée de côté) donne, **avant le début de saison** (0 mois observé) :
- une **compétence nulle** par rapport à la climatologie (skill = 0,0 ; Brier skill = 0,0) ;
- un biais moyen des saisons El Niño de **+0,8 point**, alors qu'une sécheresse généralisée se traduirait par un biais négatif.

Autrement dit, sur un échantillon national de points de grille, la seule phase ENSO **ne prédit pas** la pluie
saisonnière à Madagascar. Le lien El Niño → sécheresse ne peut donc être affirmé que régionalement
(Grand Sud) et à condition d'être démontré : c'est l'analyse 3 du point 6.

## 2. Jeux de données réellement accessibles (testés le 28/10/2026)

| Donnée | Accès | Testé | Déjà dans MakyClimat |
|---|---|---|---|
| CHIRPS v2.0, décadaire, Afrique (définitif) | Libre, sans compte | HTTP 200, dernière décade 2026.09.3 | Oui |
| CHIRPS v2.0 provisoire (prelim) | Libre | HTTP 200, dernière décade 2026.10.2 | À vérifier |
| ERA5 / ERA5-Land via Open-Meteo (archive : pluie, ETo FAO) | Libre (CC-BY) | HTTP 200, données jusqu'au 27/10/2026 | Oui (ETo) |
| ECMWF SEAS5 / EC46 via Open-Meteo | Libre | HTTP 200 | Oui |
| GloFAS (débits) via Open-Meteo Flood API | Libre | HTTP 200 | Oui (162 communes) |
| Copernicus C3S (multi-modèles saisonniers, ERA5 brut) | Compte CDS gratuit + clé API | Catalogue HTTP 200 ; téléchargement non testé | Non |
| GPM IMERG (pluie toutes les 30 min) | Compte NASA Earthdata gratuit | Liste des fichiers HTTP 200 (jusqu'à 2026/10) ; téléchargement non testé | Non |
| Indice IOD (DMI), NOAA PSL | Libre | Page HTTP 200 ; fichier de données non localisé | Non |
| OCHA HDX HAPI (IPC, pauvreté) | Libre | HTTP 200 | Oui |
| Débits observés et stations pluviométriques nationales (DGRE, Météo Madagascar) | **Pas d'accès public identifié** | — | Non |
| NDVI (eVIIRS, Copernicus Land, MODIS) | Compte requis | Voir la charte §6D | Non |

## 3. Tableau des données, résolution et limites

| Donnée | Type | Résolution | Limites principales |
|---|---|---|---|
| CHIRPS | Satellite + stations | 0,05° (~5 km), décade | Peu de stations malgaches intégrées ; sous-estime les pluies orographiques (falaise Est) ; version provisoire révisée environ 3 semaines plus tard |
| ERA5-Land | Réanalyse | 0,1° (~9 km), horaire | Pluie de modèle, biais sur la convection ; pas une observation |
| IMERG Final / Late | Satellite | 0,1°, 30 min | Final disponible environ 3,5 mois plus tard, Late environ 14 h ; sous-estime les fortes pluies orographiques |
| SEAS5 | Prévision d'ensemble | ~36 km natif, mensuel | Compétence sur Madagascar **non mesurée** dans MakyClimat ; probabilités bornées à 15-50 % |
| GloFAS | Modèle hydrologique (réanalyse et prévision) | ~5 km (0,05°) | Non calibré sur les débits malgaches ; incertain pour les bassins < ~1 000 km² |
| SRTM / Copernicus DEM | Observation | 30 m | Trop grossier pour la profondeur d'eau (règle §7D) |
| OCHA COD-PS | Estimation démographique | Fokontany | Année de référence 2018 |
| FEWS NET / IPC | Analyse d'experts | District / zone de moyens d'existence | Couverture centrée sur le Sud |

## 4. Proposition de périmètre pilote

Deux pilotes, un par aléa, choisis là où les données et les enjeux se recoupent :

1. **Sécheresse : Grand Sud** (Androy, Anosy, Atsimo-Andrefana ; 3 régions, 17 districts selon les limites OCHA).
   - **Pourquoi :** c'est le seul signal concordant entre sources, avec une crise IPC 3 déjà en cours et un épisode de référence documenté pour la validation (2020-2021).
   - **Limites :** très peu de stations au sol, et une validation qui repose sur peu d'événements.
2. **Inondation : bassin de l'Ikopa et de la Sisaony, plaine d'Antananarivo** (Betsimitatatra).
   - **Pourquoi :** forte exposition, inondations historiques documentées (activations Copernicus EMS) et réseau hydrographique connu.
   - **Point d'attention :** une saison globalement plus sèche n'exclut pas des épisodes intenses. Le pilote porte donc sur l'horizon de 0 à 7 jours, pas sur le saisonnier.
   - **Limites :** pas de débits observés publics ; un DEM à 30 m insuffisant pour une cartographie hydraulique fine.

Le Nord et l'Est restent en **surveillance**, sans pilote, tant que la divergence du point 1 n'est pas tranchée.

## 5. Protocole scientifique du premier prototype

1. **Données :** CHIRPS (définitif et provisoire), ERA5-Land et ETo via Open-Meteo, SEAS5, GloFAS. Rien d'autre tant que l'accès n'est pas confirmé.
2. **Sécheresse :**
   - SPI-1, 3, 6 et 12 sur la normale 1991-2020 (loi gamma, probabilité de mois sans pluie, données manquantes laissées manquantes) ;
   - suivi mensuel **toute l'année**, et non plus seulement de novembre à avril ;
   - bilan hydrique existant.
3. **Prévision saisonnière :**
   - mesurer la compétence de SEAS5 sur les hindcasts 1993-2016, par région et par mois de départ (score de Brier par terciles, ROC) ;
   - n'utiliser les probabilités par région que là où cette compétence est supérieure à la climatologie.
4. **Contexte océanique :**
   - tester la relation, sur 1982-2026, entre ONI et DMI d'une part et SPI-3 de décembre à février par région d'autre part (corrélation, test de permutation) ;
   - El Niño n'est retenu comme facteur que pour les régions où le lien est significatif.
5. **Inondation (pilote Ikopa) :**
   - comparer les seuils de retour GloFAS avec les dates des inondations connues (EM-DAT, activations EMS, presse) ;
   - mesurer le taux de détection, le taux de fausses alertes et le délai d'anticipation.
6. **Validation :** tests chronologiques uniquement. Comparaison systématique avec la climatologie et la persistance. Toute validation partielle est déclarée comme telle.

## 6. Premières analyses à exécuter (dans l'ordre)

| # | Analyse | Où | Prérequis |
|---|---|---|---|
| 1 | ~~Réparer les tests en échec~~ **fait le 28/10** (commit 4d7ccc9 : le test se contredisait) | GitHub Actions | — |
| 2 | ~~SPI-1/3/6/12 à fin septembre 2026~~ **fait le 28/10** (`spi_fin_septembre_2026.md`) ; anomalie provisoire du 1er au 20 octobre : **reste à faire** | `build_soilwater.py` + lecture du CHIRPS provisoire | Aucun |
| 3 | ~~Lien ONI / DMI ↔ pluie par région~~ **fait le 28/10** sous forme de modèle prédictif validé (`teleconnexions.md`) : prévisible dans 1 région sur 24 seulement. Reste : DMI de l'année en cours | `build_teleconnections.py` | DMI récent (BoM ou OISST) |
| 4 | Compétence de SEAS5 par région (hindcasts) | Script C3S | **Compte CDS gratuit, à créer par toi** |
| 5 | Lever le plafond de 50 % ou afficher « ≥ 50 % » | `connector_seasonal.py` | Aucun |
| 6 | Seuils GloFAS confrontés aux inondations historiques sur l'Ikopa | Script de validation | Liste d'événements (déjà partiellement dans `validation/evenements.csv`) |
| 7 | Connexion du NDVI | Nouveau connecteur | Compte Earthdata ou Copernicus Land |

## 7. Obstacles et incertitudes qui peuvent empêcher une prévision fiable

1. **Pas d'observations au sol publiques** (pluviomètres de Météo Madagascar, débits de la DGRE). Toute la chaîne repose sur des estimations satellitaires et des modèles. Un partenariat est indispensable pour valider.
2. **Compétence saisonnière non démontrée.** La compétence de SEAS5 n'est pas mesurée sur Madagascar, et le moteur par analogie ENSO n'a aucune compétence avant le début de saison.
3. **Peu d'événements documentés** : 13 cyclones et 1 sécheresse de référence. L'apprentissage automatique (approche 2) n'est pas défendable pour l'instant.
4. **Pas de pluie infra-journalière** pour les crues éclair : IMERG demande un compte et n'a pas encore été testé.
5. **Pas de suivi en dehors de la saison des pluies.** Le tableau de bord affiche encore les données de la saison 2025-2026 (au 30/04/2026). Les « 3,3 millions de personnes exposées » affichés ne décrivent donc **pas** la situation actuelle.
6. **Divergence non résolue** sur le Nord et l'Est (point 1).
7. **Machine locale limitée** : 5,6 Go libres, pas de Python installé. Les calculs passent par GitHub Actions, ce qui convient au volume actuel.

## Sources consultées le 28/10/2026

- NOAA CPC, ENSO Diagnostic Discussion, 08/10/2026 — https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml
- FEWS NET Madagascar, Key Message Update (septembre 2026 - janvier 2027) — https://fews.net/southern-africa/madagascar
- Météo Madagascar, perspectives climatiques 2026-2027 (PDF non lu) — https://www.meteomadagascar.mg/izepoons/perspectives_climatiques_2026-2027.pdf
- Synthèses secondaires des perspectives Météo Madagascar et SWIOCOF — https://www.cycloneoi.com/archives-blog/infos-diverses/ete-austral-2026-2027-forte-chaleur-pluies-contrastees-et-activite-cyclonique-sous-la-normale.html ; https://midi-madagasikara.mg/saison-cyclonique-2026-2027-le-premier-systeme-de-la-saison-au-nord-est-de-madagascar/
- SARCOF-33 Statement, 28/08/2026 (PDF non lu) — https://www.sadc.int/sites/default/files/2026-08/EN_FINAL%20SARCOF-33%20STATEMENT-final-28Aug1600hrs_0.pdf
- BoM, perspectives du 24/09/2026 — https://www.bom.gov.au/climate/ahead/outlooks/archive/20260924-outlook.shtml
- MakyClimat, données publiées le 27/10/2026 — https://arofarmbio-create.github.io/Makyclimat/
