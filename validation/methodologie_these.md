# MakyClimat — note méthodologique pour la thèse

*Document de travail destiné à servir de socle au chapitre méthodologie. Toutes les figures citées sont
reproductibles à partir du dépôt public `arofarmbio-create/Makyclimat` (scripts `scripts/validate_*.py`,
sorties dans `validation/`) ; aucune n'est simulée ou arrondie pour l'exposé — elles sont copiées des
sorties réelles des pipelines à la date indiquée (26-27 octobre 2026).*

## 1. Problématique et positionnement

MakyClimat teste une hypothèse opérationnelle plutôt qu'un seul modèle statistique : **une plateforme de
suivi/anticipation climatique peut-elle rester utile à la décision tout en publiant, pour chacun de ses
indicateurs, un niveau de preuve honnête et vérifiable, plutôt que la précision apparente habituelle des
tableaux de bord ?** La littérature sur les systèmes d'alerte précoce (FEWS NET, IPC, INFORM, ICPAC/SADC)
documente abondamment la tension entre urgence opérationnelle (publier vite, avec les données
disponibles) et rigueur scientifique (ne publier que ce qui est validé). MakyClimat prend parti pour une
troisième voie : publier tout ce qui est disponible, mais accompagné d'une étiquette de fiabilité
vérifiable et d'une documentation de ses limites, plutôt que de choisir entre silence et fausse certitude.

Le terrain d'application est Madagascar, pays multirisque (cyclones, sécheresse, inondations) où la
donnée administrative fine (fokontany, ~17 000 unités) est rarement croisée avec la donnée climatique
satellitaire à cette résolution.

## 2. Principes méthodologiques transversaux

Trois règles structurent l'ensemble du projet et sont appliquées au code, pas seulement énoncées :

1. **Aucune donnée simulée n'est présentée comme réelle.** Les données synthétiques (`tests/make_synthetic.py`)
   n'existent que pour les tests automatisés (CI) et le pays de démonstration `demo` ; le pays réel (`mdg`)
   n'utilise que des sources citées (CHIRPS, IBTrACS, Copernicus EMS, HDX HAPI, WFP, SoilGrids, ERA5-Land,
   OpenStreetMap, DHS, GLO-90, WorldCover, ONI/NOAA).
2. **Exposition ≠ dégât ≠ besoin humanitaire.** Chaque indicateur déclare explicitement à quel maillon de
   cette chaîne il appartient (voir `config/indicators.yml`, champ `source`) : un indicateur d'exposition
   topographique (ex. `cult_basse5_ha`) n'est jamais présenté comme un dégât constaté, et un dégât constaté
   par satellite (ex. `susc_inond_pct`, calibré sur Copernicus EMS) n'est jamais présenté comme un besoin
   humanitaire chiffré.
3. **Étiquetage de fiabilité à 4 niveaux, appliqué indicateur par indicateur** (voir §5), affiché sur le
   site (tableau de confiance, `docs/index.html`) et dans la documentation technique (`validation/README.md`
   et les notes dédiées `*_limites.md`).

## 3. Architecture des données et pipeline

```
Sources ouvertes (CHIRPS, IBTrACS, Copernicus EMS, HDX HAPI, WFP/HDX,
SoilGrids, ERA5-Land, OSM/HeiGIT, DHS, ONI/NOAA, GLO-90, WorldCover)
        │
        ▼
scripts/connector_*.py, scripts/build_*.py   (GitHub Actions, automatisé)
        │  → data/<pays>/external/*.csv  (format commun : pcode, indicateur, valeur, date, source)
        ▼
scripts/compute_metrics.py                   (agrégation par unité administrative, règles déclarées
        │                                      dans config/indicators.yml : sum / mean / popmean / none)
        ▼
scripts/build_catalogue.py, scripts/validate.py   (catalogue, contrôle qualité — bloque la publication
        │                                            si une anomalie structurelle est détectée)
        ▼
docs/ (site statique, Leaflet + JS natif)     → GitHub Pages
        ▲
        └── scripts/validate_events.py, validate_fokontany.py, build_triggers.py   (validation
            indépendante du pipeline de production, résultats publiés dans validation/)
```

Point méthodologique important : la validation (`validate_events.py`, `validate_fokontany.py`) est un
pipeline **séparé** du pipeline de production (`compute_metrics.py`). Les modèles qui en sortent (ex. le
modèle « terrain seul » utilisé par `build_susceptibility.py`) sont réintégrés explicitement, avec leurs
coefficients appris stockés dans `validation/*.json`, jamais recalculés silencieusement en production.

## 4. Modules et stratégie de validation, par échelle

### 4.1 Niveau région — cyclones et régions touchées (régression logistique, validation leave-one-out)

- **Question testée :** à partir des caractéristiques du cyclone (couverture en vent ≥ 34/50/64 nœuds,
  pluie prévue, ratio local/national), peut-on classer correctement les régions les plus touchées ?
- **Méthode :** régression logistique sur les 24 régions de Madagascar, caractéristiques normalisées
  (moyenne/écart-type), évaluée en **laissant chaque cyclone de côté** (leave-one-event-out), pour éviter
  que le modèle soit simplement évalué sur les données qui l'ont entraîné.
- **Base d'événements :** 21 cyclones documentés 1994-2026 (`validation/evenements.csv`), listes de
  régions touchées tirées de rapports OCHA/IFRC/presse cités (colonne `source_url`) ; 16 cyclones ont une
  liste de régions utilisable pour ce test (5 exclus : Emnati 2022, Geralda 1994 — trajectoire IBTrACS
  introuvable —, Eline 2000, Elita 2004, Giovanna 2012).
- **Résultat (26 oct. 2026) :** AUC 0,84 (vent + pluie) ; 87 % des régions citées comme touchées figurent
  dans les 8 premières sur 24 du classement du modèle.
- **Limite assumée et publiée :** les listes de régions touchées sont elles-mêmes partielles dans les
  rapports sources, surtout avant 2017 ; le modèle n'est pas calibré en probabilité (c'est un classement,
  pas une probabilité d'occurrence).
- **Extension non concluante, documentée honnêtement plutôt que cachée :** une exploration de seuils
  opérationnels univariés pour l'action anticipée (`scripts/build_triggers.py`) n'a trouvé aucun seuil
  simple avec un bon compromis détection/fausses alertes (meilleur cas : POD 0,92 mais FAR 0,71) — publié
  comme « non validé » plutôt qu'omis, avec l'explication qu'il manque des données de dégâts réels pour
  calibrer un vrai protocole (`validation/declencheurs_anticipation.md`).

### 4.2 Niveau fokontany et commune — validation satellite (Copernicus EMS)

- **Question testée :** parmi les fokontany d'une zone déjà touchée par un cyclone, quelles variables
  distinguent ceux réellement inondés ou endommagés (vérité de terrain = cartographie satellite) ?
- **Méthode :** régression logistique sur 5 880 fokontany-événements (8 activations Copernicus EMS, après
  exclusion de 3 activations ciblées mais non exploitables — fichier zip invalide pour l'une, aucune couche
  publiée pour les deux autres, voir `validation/evenements_2020_2026_note.md`), comparant trois jeux de
  variables : vent+pluie seuls, terrain seul (HAND, altitude, pente, rivière, densité de population), et la
  combinaison des deux — toujours évalué en laissant un événement de côté.
- **Résultat central, contre-intuitif et publié tel quel :** le vent et la pluie seuls ne discriminent
  presque pas une fois qu'on se limite aux zones déjà touchées (AUC 0,51-0,52 — proche du hasard), alors
  que le terrain seul discrimine nettement (AUC 0,79 au fokontany, 0,82 à la commune, probabilités
  calibrées : Brier 0,176-0,180 contre 0,234-0,236 pour la fréquence moyenne). Interprétation : une fois
  qu'une zone est touchée par l'aléa, c'est la topographie locale — pas l'intensité du cyclone — qui
  explique où le dommage se concentre.
- **Limite assumée :** les dégâts aux bâtiments seuls restent mal et instablement prédits (AUC 0,16-0,62
  selon la variante) — seulement 159 cas positifs sur 5 880, signal insuffisant, et absence du type de
  construction dans les données disponibles.

### 4.3 Validation descriptive — sécheresse (SPI)

- **Méthode :** SPI-12 régional (loi gamma mensuelle, méthodologie OMM N° 1090) comparé à la sécheresse
  documentée du Grand Sud 2019-2021 (Androy, Anosy, Atsimo Andrefana).
- **Résultat :** les trois régions ressortent effectivement en tête du classement national en 2020-21
  (SPI ≤ -1,91, rangs 1, 3 et 8 sur 24), contre des régions témoins du nord restées normales.
- **Nature du test, assumée explicitement :** comparaison descriptive à 3 régions citées, pas un test
  statistique au sens strict (`validation/secheresse_spi.md`).

### 4.4 Indices composites expérimentaux — étiquetés « non validé » par construction

Deux indices combinent plusieurs signaux déjà validés séparément, par une pondération raisonnée plutôt
qu'apprise statistiquement (faute de vérité de terrain pour les calibrer) :

- **Vulnérabilité cumulative** (`vuln_cumul_idx`) : chocs cyclone + sécheresse des ~3,5 dernières années,
  pondération par récence (demi-vie 18 mois) et saturation (le choc le plus sévère pèse plein, les suivants
  de moins en moins, jamais plus de 100). N'inclut aucune donnée de prix, d'inflation ou de résilience
  réelle des ménages (aucune source fiable identifiée à l'échelle du fokontany).
- **Potentiel pour point d'eau peu profond** (`potentiel_eau_pct`, ajouté le 26 oct. 2026) : classement
  multicritère (recharge hydrique 40 %, proximité du réseau de drainage 25 %, pente inversée 20 %,
  rétention du sol 15 %), analyse multicritère par somme pondérée. N'inclut aucune géologie (facteur le
  plus déterminant d'un forage réel, donnée non disponible) ni aucune donnée réelle de forage pour
  calibrer les poids. Compromis documenté et non résolu : une zone bien notée (proche d'un cours d'eau)
  est aussi plus exposée aux inondations — à lire avec `susc_inond_pct`, jamais seule.

Ces deux indices sont volontairement étiquetés « Non validé » (pas « Approximation ») : la différence de
niveau entre `susc_inond_pct` (calibré sur une vérité de terrain satellite, leave-one-out, AUC connu) et
ces deux indices (construction raisonnée, non calibrée) est elle-même un résultat méthodologique du
projet — la hiérarchie des niveaux de preuve n'est pas décorative, elle reflète une différence réelle de
robustesse epistémique.

## 5. Cadre d'étiquetage de fiabilité

Quatre niveaux, appliqués à chaque ligne du tableau de confiance (`docs/index.html`) :

| Niveau | Critère d'attribution | Exemple |
|---|---|---|
| **Validé** | Calibré sur une vérité de terrain indépendante, évalué en leave-one-out ou équivalent, métrique de performance publiée | Régions touchées (AUC 0,84), susceptibilité aux inondations (AUC 0,79-0,82) |
| **Standard** | Source officielle ou méthode reconnue (OMM, FAO-56, etc.), pas de calibrage spécifique au contexte malgache nécessaire | SPI, bilan hydrique FAO-56 |
| **Approximation** | Construction raisonnée avec une source vérifiable, couverture ou précision partielle documentée | Prix du riz WFP (couverture partielle, prix nominal) |
| **Non validé** | Construction raisonnée sans vérité de terrain disponible pour calibrer ou valider ; exploration honnête d'une piste qui n'a pas abouti | Vulnérabilité cumulative, potentiel pour point d'eau, seuils d'action anticipée |

Un indicateur ne change de niveau que lorsqu'une source ou une méthode de calibrage nouvelle est
identifiée et documentée (voir les sections « Pour l'améliorer » de chaque note `*_limites.md`) — jamais
par décision éditoriale isolée.

## 6. Limites transversales et perspectives (état au 27 octobre 2026)

- **Corroboration externe avec EM-DAT (CRED, UCLouvain) effectuée le 27/10/2026** — voir
  `validation/emdat_corroboration.md` pour le détail événement par événement. Usage interne uniquement
  (licence CC BY-NC-ND de l'archive, confirmé avec l'utilisateur) : aucune donnée EM-DAT brute ou dérivée
  n'est republiée sur le site public. Résultat résumé : les chiffres de « personnes touchées » de
  `evenements.csv` concordent quasi exactement avec EM-DAT pour 7/9 événements comparables ; les bilans de
  décès sont systématiquement plus bas côté MKC (sources = rapports de situation précoces, pas des bilans
  consolidés finaux) — à lire comme une limite documentée, pas une erreur. Aucune incohérence
  structurelle détectée.
- **Donnée de dégâts réels manquante pour calibrer les seuils d'action anticipée** (demande adressée au
  BNGRC, réponse en attente).
- **Géologie absente** du module eau souterraine — piste prioritaire identifiée pour passer ce module au
  niveau « Approximation ».
- **Formations sanitaires (`mwater_sante`, ajouté le 27/10/2026) :** source mWater Portal (entrepôt
  communautaire alimenté par des ONG/ministères, dont MGMERL/UNICEF), 3 837 établissements avec GPS,
  assignés par point dans polygone (pas une approximation de distance) — 2 589/17 465 fokontany (15 %)
  avec au moins une formation sanitaire. Couverture nettement supérieure à `osm_sante` (cartographie
  bénévole OpenStreetMap), mais **ce n'est toujours pas le registre officiel du Ministère de la Santé
  Publique** (environ 3 000-3 300 CSB officiels recensés par ailleurs ; les 3 837 ici peuvent inclure des
  doublons, établissements fermés non retirés, ou catégories plus larges que les seuls CSB publics).
  Étiqueté « Approximation », pas « Validé ». Extraction manuelle (pas d'API publique identifiée) — à
  refaire périodiquement.
- **Écoles (`mwater_ecoles`, ajouté le 27/10/2026) :** même source et même méthode que `mwater_sante` —
  27 981 écoles avec GPS, 10 260/17 465 fokontany (59 %) avec au moins une école. Couverture nettement
  meilleure que les CSB (proportionnelle au nombre d'écoles réel, bien supérieur à celui des CSB) et bien
  supérieure à `osm_ecoles`. Mêmes réserves que `mwater_sante` : pas le registre officiel du Ministère de
  l'Éducation, peut inclure doublons/établissements fermés. Étiqueté « Approximation ».
- **Couverture Copernicus EMS limitée** aux zones urbaines/accessibles cartographiées quelques jours après
  l'événement — un biais structurel du jeu de vérité de terrain lui-même, pas seulement du modèle qui s'y
  calibre, à discuter explicitement dans la thèse comme limite de toute validation basée sur l'imagerie de
  crise.
- **Échecs techniques documentés plutôt que masqués :** sur 4 nouvelles activations EMS ciblées pour
  étendre la base de validation, une seule a été exploitable (format de fichier invalide pour une, aucune
  couche publiée pour les deux autres) — ce taux d'échec (75 %) est en soi une donnée sur la fiabilité
  pratique de Copernicus EMS comme source de vérité de terrain à l'échelle fokontany, à documenter dans la
  discussion méthodologique.

## 7. Contribution méthodologique revendiquée pour la thèse

1. Un cadre reproductible de validation multi-échelle (région, fokontany, commune) pour un système
   d'alerte climatique, avec code et données de validation publics et versionnés (pas seulement les
   résultats finaux).
2. Une démonstration empirique que le signal utile change de nature selon l'échelle d'analyse (le vent et
   la pluie discriminent au niveau région mais pas au niveau fokontany une fois la zone touchée connue ;
   c'est le terrain qui prend le relais) — résultat qui a sa propre valeur scientifique indépendamment de
   l'outil qui l'a produit.
3. Un protocole d'étiquetage de fiabilité à 4 niveaux appliqué systématiquement et vérifiable dans le
   code, proposé comme alternative aux tableaux de bord qui n'affichent pas leur propre niveau de preuve.
4. Une documentation honnête des échecs (triggers non validés, extension EMS en grande partie infructueuse,
   modules sans vérité de terrain disponible) comme partie intégrante du résultat scientifique, pas comme
   un défaut à corriger avant publication.

## 8. Sources de données (référencement pour la bibliographie)

- **Pluie :** CHIRPS (Climate Hazards Group, UCSB)
- **Trajectoires et intensité des cyclones :** IBTrACS (NOAA NCEI)
- **Cartographie de crise satellite :** Copernicus Emergency Management Service — Rapid Mapping
- **Sécurité alimentaire et pauvreté :** HDX HAPI (OCHA Centre for Humanitarian Data)
- **Prix des denrées :** WFP/HDX, Food Prices for Madagascar
- **Sols :** SoilGrids (ISRIC)
- **Évapotranspiration :** ERA5-Land (Copernicus Climate Change Service), méthode FAO-56
- **Terrain :** Copernicus GLO-90 DEM
- **Occupation du sol :** ESA WorldCover
- **Routes, accessibilité, services :** OpenStreetMap (© contributeurs, ODbL) via HeiGIT/Overpass
- **Santé, eau, assainissement :** enquêtes DHS
- **Indice ENSO :** ONI, NOAA Climate Prediction Center
- **Limites administratives et population :** OCHA COD-AB / COD-PS
