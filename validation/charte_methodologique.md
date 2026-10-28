# Charte méthodologique MakyClimat — adaptée du cahier des charges scientifique du 27/10/2026

Ce document reprend, section par section, le cahier des charges scientifique fourni par le porteur du
projet (« système de modélisation et de prévision des inondations et sécheresses à Madagascar ») et dit,
pour chaque section, ce que MakyClimat fait réellement aujourd'hui, ce qui est un écart assumé, et où
trouver le détail. Règle d'or du projet, reprise de la section 1 du cahier des charges : rigueur
scientifique, transparence totale sur les incertitudes, jamais de donnée inventée ni de validation
prétendue. Ce document est vivant — à mettre à jour à chaque avancée, pas une photo figée.

## 1-2. Rôle, expertise, objectif général

Objectif inchangé : prévoir/modéliser les aléas à l'avance, estimer les populations à risque avec des
méthodes défendables, proposer des actions. MakyClimat couvre aujourd'hui sécheresse (météorologique),
inondation/crue fluviale, vent fort/cyclone, chaleur, et éboulement (proxy pente+pluie) — pas encore
l'inondation pluviale urbaine ni les glissements de terrain validés sur inventaire réel (§7, voir plus
bas). Saison climatique courante couverte en continu depuis le déploiement initial.

## 3. Zone géographique

Madagascar entier, du national au fokontany (4 niveaux administratifs), via les limites officielles
OCHA COD-AB. Pas de biais de couverture délibéré par région — toute la typologie listée (Grand Sud,
côte Est, Hautes Terres/Analamanga, bassins d'Antananarivo, Nord/Nord-Ouest) est couverte par la même
grille nationale de pluie (CHIRPS) et la même liste de fokontany. Les analyses plus fines (crue,
cyclone, éboulement) ne sont disponibles que là où leurs données sources le permettent (ex. crue :
seulement les communes avec seuil de retour calibré, `n_valid_thresholds` dans meta.json).

## 4. Collecte et contrôle des données

Chaque connecteur (`scripts/connector_*.py`, `scripts/build_*.py`) documente en tête de fichier : source,
URL, fréquence, méthode, limites. Principe non négociable du projet : **une donnée absente reste
absente** (jamais remplacée par une valeur inventée) — voir `validation/groundwater_limites.md`,
`validation/vuln_cumul_limites.md` pour des exemples assumés de lacunes documentées plutôt que
masquées. Sources effectivement utilisées aujourd'hui :

| Catégorie (cahier des charges) | Ce qu'on utilise | Écart assumé |
|---|---|---|
| Météo/climat | CHIRPS (pluie, 1981-aujourd'hui), ERA5-Land via Open-Meteo (prévision 16j, ETo), ECMWF SEAS5 (prévision saisonnière) | Pas d'ERA5 brut, pas de GPM IMERG, pas de comparaison multi-sources (voir §5) |
| ENSO/Océan Indien | Indice ONI (NOAA) | Pas de suivi du dipôle de l'océan Indien séparément |
| Hydro/géo | GloFAS (débit, via Open-Meteo), SRTM/pente, réseau hydrographique OSM | Pas de HEC-HMS/HEC-RAS (voir §7) |
| Agricole/environnement | — | **NDVI/végétation non connecté** (voir §6D) |
| Exposition/vulnérabilité | OCHA COD-PS (population), WorldPop âge/sexe (-5 ans), mWater/HeiGIT (structures), IPC, taux de pauvreté national | Pas de données d'accès à l'eau/revenu fin par ménage |

## 5. Contexte climatique actuel

Pluie récente par dékade (définitive ou provisoire) depuis le dernier mois CHIRPS définitif, comparée à
1991-2020, ajoutée le 28/10/2026 (`scripts/update_recent_rain.py`, `validation/pluie_recente_regions.csv`).
Le lien El Niño → pluie locale est désormais **testé** région par région (§8, approche 1) : il n'est démontré
que pour 1 région sur 24.
ENSO (ONI) suivi et affiché par saison, mais **jamais utilisé comme cause automatique** d'un niveau
d'alerte local (règle du projet, reprise du cahier des charges §5) — seulement comme facteur de
contexte dans les scénarios de fin de saison (`connector_enso.py`, `scenarios.py`). Pas de comparaison
systématique entre plusieurs organismes de prévision (un seul modèle saisonnier : ECMWF SEAS5).

## 6. Module sécheresse

- **SPI-1/3/6/12** : calculés (loi gamma, OMM N° 1090) — voir `scripts/soilwater_core.py`. SPI-1 ajouté le 28/10/2026 ;
  SPI vide là où la normale du cumul est < 25 mm (saison sèche). Période de référence : 1981-aujourd'hui (pas 1991-2020).
  État à fin septembre 2026 : `validation/spi_fin_septembre_2026.md` (SPI-12 ≤ −1 dans 6 régions du Sud/Sud-Est ;
  saison sèche anormalement humide sur les Hautes Terres, recoupée avec ERA5).
  **Écart restant** : octobre 2026 (CHIRPS provisoire) non lu ; `sm_z` contradictoire avec le SPI en saison sèche, non résolu.
- **SPEI** : **pas de vrai SPEI** — voir `validation/spei_approche.md` (audit du 27/10/2026) : les deux
  proxys combinant pluie et évapotranspiration déjà calculés (sm_z, recharge12_z) font *moins bien* que
  le SPI seul sur l'épisode de référence ; un vrai SPEI demanderait une série d'évapotranspiration
  pluriannuelle (coût ~8x les appels API actuels) et un ajustement log-logistique non encore validé.
- **Bilan hydrique du sol** : fait (`build_soilwater.py`, Thornthwaite-Mather, Saxton & Rawls, NRCS
  NEH-4) avec ses limites documentées en tête de fichier (ruissellement journalier non représenté,
  ETo climatologique fixe, etc.).
- **Stress de la végétation (NDVI/EVI)** : **non connecté**. Recherché cette nuit (audit du 27/10/2026) :
  toutes les sources accessibles identifiées (USGS eMODIS — capteur MODIS vieillissant, mises à jour
  arrêtées depuis 2022 ; son remplaçant eVIIRS ; Copernicus Global Land Service) demandent soit un
  compte/mot de passe (inscription par le porteur du projet, puis un secret GitHub à configurer — pas
  quelque chose que Claude peut faire seul), soit un traitement raster zonal neuf comparable à
  `build_population_grid.py` mais pour une série temporelle — plusieurs jours de travail, pas une nuit.
  Reste listé `status: planned` dans `config/indicators.yml` (jamais présenté comme actif).
- **Seuil opérationnel (pluie < 75 % de la normale)** : testé POD/FAR contre le seul épisode documenté —
  rate la moitié des cas (`validation/secheresse_pod_far.md`, audit du 27/10/2026). Reste marqué
  PROVISOIRE dans `config/countries/mdg.yml`, à juste titre.

## 7. Module inondation

- **Analyse des précipitations** : cumuls 1/3/7 jours disponibles via la prévision (`early_warning.py`,
  `rain_day_mm`, `rain_3day_mm`). Pas de cumul horaire (1h/3h/6h) — la prévision Open-Meteo utilisée est
  à résolution journalière, pas infra-journalière.
- **Bassins versants** : délimités (réseau hydrographique OSM, pente SRTM) pour le calcul du modèle de
  crue (voir ci-dessous) ; pas de calcul explicite du temps de concentration.
- **Modélisation hydrologique** : modèle pluie-débit simplifié, pas HEC-HMS — débit prévu (GloFAS via
  Open-Meteo) comparé aux seuils de retour 2/5/10/20 ans ajustés par la loi de Gumbel sur les débits
  annuels maximaux (`update_floods.py`). Résolution ~5 km, incertaine sur petits bassins — déjà indiqué
  dans le code et sur le site.
- **Validation du modèle de crue (28/10/2026, `validation/crues_validation.md`)** sur le périmètre pilote
  (Ikopa, Sisaony ; 162 communes, 136 mailles GloFAS) :
  - **Détection** : 1 événement documenté sur 3. Fytia 2026 est détecté ; **Ana 2022**, la grande inondation
    d'Antananarivo, et Batsirai 2022 sont manqués (4 % des communes au-dessus de la crue de 2 ans).
  - **Satellite** : sur les communes cartographiées par Copernicus EMS (Ava 2018), AUC de 0,55, soit à peine
    mieux que le hasard.
  - **Épisodes** : sur 12 épisodes simulés de 2015 à 2026 (seuil 10 %, 174 communes), 4 correspondent à un
    événement documenté et 5 à un cyclone GDACS. GDACS est une source indépendante
    (`connector_gdacs_events.py`) : ses inondations de source GloFAS sont écartées. Il reste
    **3 épisodes sans aucune correspondance**, soit **25 % au plus de fausses alertes**. C'est une borne
    haute : les inondations non cycloniques du BNGRC manquent.
  - **Sensibilité au seuil** : avec « au moins 1 commune », les 3 événements sont détectés, dont Ana 2022,
    mais on obtient 20 épisodes, dont 6 sans correspondance. Avec 25 %, 1 événement sur 3 est détecté, pour
    7 épisodes dont 1 sans correspondance. Le choix du seuil opérationnel revient au BNGRC et à la DGRE.
  - **Lecture** : le modèle de rivière à ~5 km capte les grandes crues fluviales, pas l'inondation urbaine
    et pluviale d'Antananarivo (drainage, digues, pompage).
  - **Écart majeur** : il manque un module « inondation pluviale / crue éclair » fondé sur la pluie (§7.A).
    À valider sur les mêmes événements.
- **Modélisation hydraulique (HEC-RAS 2D)** : **non implémentée**. Pas de carte de profondeur/vitesse
  d'inondation — seulement un niveau de crue (0-3) par commune. Écart assumé : construire un modèle
  hydraulique 2D demanderait un MNT fin, un maillage, et un calibrage que le projet n'a pas les moyens
  de faire valider correctement dans les délais actuels. Le site ne prétend jamais avoir cette précision.
- **Glissements de terrain** : règle proxy (seuil mondial pluie/pente, Guzzetti et al. 2008), pas un
  modèle calibré sur un inventaire local de glissements passés — limite documentée dans
  `config/countries/mdg.yml` (`risks.landslide_threshold`) et sur la fiche de zone elle-même.

## 8. Fusion des données et modèles prédictifs

- **Approche 1 (physique/statistique)** : seuils documentés (pluie, débit, vent) + régression logistique
  pour les cyclones (`declencheurs_anticipation.md`, AUC 0,83). **Ajouté le 28/10/2026** : modèle saisonnier
  par région ONI/DMI de juillet-septembre → pluie novembre-janvier, janvier-mars, novembre-avril
  (`scripts/build_teleconnections.py`, `validation/teleconnexions.md`). Validation croisée + test
  chronologique + permutation unilatérale avec réajustement + Benjamini-Hochberg. DMI calculé depuis
  ERSST v5 (`connector_dmi.py`, à jour au mois précédent, sans compte). **Résultat : 3 régions sur 24, toutes
  pour novembre-janvier seulement** : Menabe (ONI, ~77 % de la normale prévu en 2026-2027), Sava et Diana
  (ONI+DMI, ~110 % et ~101 %). Rien n'est prévisible pour janvier-mars ni pour la saison entière. Signal faible
  (El Niño → plus sec) dans le Sud et le Sud-Ouest, non retenu après contrôle des tests multiples.
  **Écart** : le contrôle multiple porte sur chaque combinaison période × modèle séparément, pas sur les 6 à la fois ;
  ces 3 régions sont à confirmer.
- **Approche 2 (apprentissage automatique)** : **pas de Random Forest/XGBoost évalué**. Choix assumé :
  les jeux de vérité terrain disponibles (13 cyclones, 1 épisode de sécheresse documenté) sont bien trop
  petits pour entraîner et valider un modèle ML sans surapprentissage — un modèle plus complexe sur un
  N aussi faible donnerait une fausse impression de robustesse. À reconsidérer si la base d'événements
  documentés s'élargit (ex. plusieurs cyclones et sécheresses supplémentaires archivés).
- **Approche 3 (ensemble)** : prévision saisonnière ECMWF SEAS5 déjà une moyenne d'ensemble ; pas de
  fusion inter-modèles au-delà (un seul modèle saisonnier, un seul modèle hydrologique).

## 8bis. Détection de changement d'état (demande explicite du porteur du projet)

Fait cette nuit (audit du 27/10/2026, `scripts/state_change.py`) : durée au niveau d'alerte saisonnier
actuel et tendance récente (s'aggrave/stable/s'améliore), région et district uniquement, à partir de
l'archive déjà collectée à chaque dékade (`archive_snapshot.py`) — aucune nouvelle source. Nombre
d'aléas météo simultanés (niveau vigilance ou plus) à tous les niveaux, à partir de l'alerte à 7 jours
déjà calculée. Limite assumée : l'archive ne couvre pas encore le niveau commune/fokontany, et avec un
historique encore court, « depuis combien de temps » peut vouloir dire « depuis le début de
l'archivage », pas un vrai changement — signalé explicitement à l'écran plutôt que présenté comme
une durée réelle.

## 9. Horizons de prévision

Trois horizons réels aujourd'hui (corrigé le 27/10/2026 après relecture du code — il y en a plus que le
« seulement 7 jours » dit plus tôt dans la session) :

1. **0-7 jours** : alerte précoce complète (pluie, vent, chaleur, sécheresse courte, crue), avec
   population exposée et cibles — `ewU`/`ewt`/`ewe5` dans les données de zone.
2. **8-16 jours** (nouveau, ajouté cette nuit — audit du 27/10/2026) : même méthode, niveau de tendance
   seul (pas de population calculée, fiabilité plus faible assumée) — `ew2` dans les données de zone,
   section « Tendance indicative » de la fiche. Les données étaient déjà récupérées (`forecast_days: 16`)
   mais jamais lues au-delà du jour 7 jusqu'ici.
3. **Saisonnier (1-6 mois)** : prévision ECMWF SEAS5 (probabilités sec/normal/humide par tercile,
   bornées 15-50 %, `connector_seasonal.py`) + scénarios par analogie historique ENSO (44 ans).

**Écart assumé** : pas de produit sous-saisonnier distinct à résolution hebdomadaire (2-4 semaines) —
la fenêtre 8-16 jours couvre une partie de ce rôle mais à la même résolution journalière que l'alerte à
7 jours, pas une agrégation hebdomadaire dédiée avec sa propre fiabilité documentée séparément.

## 10. Cartographie des risques

Séparation danger/exposition/vulnérabilité/risque **strictement appliquée** — règle fondatrice du
projet, jamais transgressée (ni dans le code ni dans l'affichage : `vs`/« vulnérabilité économique »
toujours affichée à part de l'exposition géographique brute). Pas de carte de profondeur d'inondation
(voir §7). Couche SIG reproductible en Python (pandas/numpy/rasterio-like via `sample_grid`), pas de
QGIS dans le pipeline de production (utilisé ponctuellement pour l'exploration manuelle).

## 11. Système d'alerte précoce

4 niveaux déjà en place (Normal/Veille/Alerte/Urgence pour la saison ; Aucune/Vigilance/Alerte/Alerte
maximale pour les 7 jours) — proches en esprit du vert/jaune/orange/rouge proposé, nommés différemment.
Seuils marqués PROVISOIRE, jamais présentés comme validés par les services officiels. **Pas de canal
SMS/email** — uniquement le site web. Écart assumé : un canal push demanderait un fournisseur SMS/email,
des contacts collectés avec consentement, et une astreinte de vérification humaine avant tout envoi —
hors périmètre technique de ce qu'un outil de visualisation peut décider seul.

## 12. Anticipation humanitaire et agricole

Fait : `playbook.yml` (anticipation/atténuation/réponse/résilience par secteur), conseils ménage par
scénario et par aléa (section « Tendance », « Scénarios », fiche de zone). Pas de distinction formelle
documentée entre actions « sans regret » et actions coûteuses nécessitant plus de confiance — ce
classement existe informellement dans le choix des conseils (toujours des actions à faible coût/réversibles)
mais n'est pas explicité comme tel dans l'interface.

## 13. Validation scientifique

Le point le plus mûr et le plus honnête du projet :
- **Cyclones** : POD/FAR/AUC, leave-one-out par événement, 13 événements (`declencheurs_anticipation.md`,
  `cyclones_indicateurs_par_region.csv`).
- **Sécheresse** : POD/FAR exploratoire sur N=1 événement documenté (`secheresse_pod_far.md`) + SPEI
  testé et écarté (`spei_approche.md`) — tous deux de l'audit du 27/10/2026.
- **Crue** : seuils de retour Gumbel ajustés sur débit annuel maximal observé ; pas encore de comparaison
  emprise simulée vs observation satellite.
- **Éboulement** : seuil mondial, jamais calibré localement (pas d'inventaire de glissements passés
  accessible).
Écart assumé général : aucun modèle n'atteint le niveau de robustesse statistique qu'un plus grand
nombre d'événements documentés permettrait — c'est une limite de la donnée disponible pour Madagascar
en open data, pas un manque d'effort de validation.

## 14. Environnement technique

Python (pandas, numpy, requests), pas de PostGIS (fichiers JSON/CSV statiques servis par GitHub Pages),
pas de QGIS ni HEC-HMS/HEC-RAS en production. Choix assumé : volume de données et complexité du modèle
actuels ne justifient pas une base de données géospatiale dédiée.

## 15-16. Livrables et méthode de travail

Le présent document, la thèse (`validation/methodologie_these.md`), et les fichiers de validation
listés ci-dessus constituent les livrables 1 (diagnostic), 2 (protocole) et 4 (résultats documentés) du
cahier des charges. Le livrable 3 (prototype reproductible) est le dépôt GitHub public lui-même. Le
livrable 5 (tableau de bord) est le site. Le livrable 6 (plan d'action/budget) n'a pas d'équivalent —
hors périmètre d'un outil technique.

La méthode de travail obligatoire du cahier des charges (étapes 1 à 7 : rechercher les données
réellement accessibles avant toute simulation) est déjà la pratique par défaut du projet, reprise dans
chaque fichier de validation produit cette nuit : recherche d'abord (NDVI, SPEI), calcul honnête ensuite,
conclusion assumée même quand elle est négative (SPEI qui ne marche pas mieux que le SPI, seuil
sécheresse qui rate la moitié des cas).
