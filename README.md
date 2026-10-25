# MakyClimat

**Couche ouverte d'intégration et de décision climatique, de la région au fokontany.**
Pays pilote : Madagascar. Projet de doctorat.

MakyClimat ne cherche pas à remplacer les systèmes existants (IPC, INFORM, ICPAC, SADC, FEWS NET, Flood Hub…).
Il les relie et comble des lacunes documentées : ciblage à l'échelle fine, seuils d'alerte ouverts et versionnés,
suivi de la réponse des partenaires, simulation « et si ? », alignement avec les ODD et les cadres nationaux, et réplicabilité
dans d'autres pays par simple fichier de configuration.

> Version actuelle (phase 1) : sécheresse et pluie (CHIRPS), population exposée, cibles potentiels, simulation de la pluie,
> suivi des bénéficiaires, catalogue d'indicateurs par secteur et ODD. Les autres aléas et secteurs sont déjà déclarés
> dans le catalogue (statut « Prévu ») et seront ajoutés par connecteurs.

## 1. Mise en ligne en 6 étapes (sans programmer)

1. Créer un compte GitHub gratuit, puis un dépôt **public** nommé `makyclimat`.
2. Dans le dépôt : *Add file > Upload files*, glisser tout le contenu de ce dossier (y compris le dossier caché `.github`), puis *Commit changes*.
   Si le dossier `.github` n'apparaît pas à l'envoi, créer les 4 fichiers de workflow à la main (*Add file > Create new file*, nom `.github/workflows/<nom>.yml`).
3. *Settings > Actions > General > Workflow permissions* : choisir **Read and write permissions**, puis Save.
4. *Settings > Pages > Build and deployment > Source* : choisir **GitHub Actions**.
5. Onglet **Actions**, lancer dans cet ordre (bouton *Run workflow*) :
   1. « 1 - Construire les limites et la population » (avec `mdg`)
   2. « 2 - Construire la normale de pluie » (avec `mdg`, 10 à 20 minutes)
   3. « Mise à jour des données et publication » (avec `mdg`)
6. L'adresse publique apparaît à la fin du dernier workflow (forme `https://<compte>.github.io/makyclimat/`).

Ensuite, tout est automatique : le workflow de mise à jour tourne les **3, 13 et 23 de chaque mois**, après la fin de chaque dékade de pluie.
Si le contrôle qualité échoue, rien n'est publié et le site garde ses dernières données valides.

### Liste de vérification au premier lancement
Ces points n'ont **pas pu être testés en conditions réelles** (accès réseau limité lors de la construction). Le premier lancement peut demander un petit ajustement :
- **Limites** : noms des fichiers et champs du jeu OCHA COD-AB (`scripts/build_boundaries.py` affiche les niveaux trouvés).
- **Population** : colonnes du fichier COD-PS (`scripts/build_population.py` affiche la colonne retenue).
- **Pluie** : modèles d'adresses CHIRPS dans `config/countries/mdg.yml` (rubrique `rainfall`).
- Taille des fichiers de limites (le niveau fokontany compte environ 17 000 polygones). Si la publication est lente, augmenter la tolérance de simplification dans `build_boundaries.py`.

## 2. Alimenter l'outil avec vos données (sans programmer)

| Fichier | Contenu | Effet |
|---|---|---|
| `inputs/vulnerabilite.csv` | `pcode, part_vulnerable (0 à 1), source, date` pour une région, un district, une commune ou un fokontany | remplace la part vulnérable par défaut (provisoire) dans le calcul des cibles |
| `inputs/interventions.csv` | `partenaire, secteur, activite, pcode, beneficiaires, statut, debut, fin, source` | affiche les bénéficiaires déclarés et l'écart restant par zone |

Modifier un fichier directement sur GitHub (icône crayon) : la prochaine mise à jour l'intègre. Les codes `pcode` sont ceux de l'export CSV de l'outil.

### Indicateurs externes (ONU/OCHA et autres) — sans programmer

Tout fichier CSV déposé dans `inputs/indicateurs/` (colonnes `pcode, indicateur, valeur, date, source`) devient une couche de la carte, une ligne de la fiche de zone et une colonne de l'export, **à condition que l'indicateur soit déclaré dans `config/indicators.yml`** (champs `format` : pct, int ou float ; `aggregate` : sum, mean, popmean ou none). La valeur la plus récente est retenue ; les zones supérieures sont agrégées selon la règle `aggregate`.

Déjà branchés : **IPC phase 3 ou plus** (part et nombre de personnes) et **pauvreté multidimensionnelle**, lus automatiquement depuis l'API HDX HAPI de l'OCHA par `scripts/connector_hapi.py`. Là où une analyse IPC existe, sa part de population remplace la part vulnérable par défaut (ordre de priorité : `inputs/vulnerabilite.csv`, puis IPC, puis valeur par défaut).
Activation : générer gratuitement un « app identifier » dans la documentation interactive de HAPI (https://hapi.humdata.org/docs), puis l'enregistrer dans GitHub : *Settings → Secrets and variables → Actions → New repository secret*, nom `HAPI_APP_IDENTIFIER`. Sans ce secret, l'étape est simplement ignorée. Au premier lancement, vérifier dans le journal le taux de correspondance des codes HAPI avec les limites OCHA.

### Changement climatique et El Niño / La Niña (cœur de la thèse)

Le workflow « 2 - Construire la normale de pluie » télécharge aussi l'indice **ONI** de la NOAA (`scripts/connector_enso.py`) et construit, pour **chaque saison des pluies depuis 1982**, la pluie CHIRPS en % de la normale 1991-2020, classée **El Niño / La Niña / neutre** (`scripts/build_climate_change.py`, module `scripts/enso.py`).
Par zone, l'outil publie : la tendance de la pluie saisonnière (points de % par décennie) et sa significativité ; la pluie moyenne lors des El Niño et des La Niña passés ; la corrélation pluie/ONI ; et une courbe historique (une barre par saison, colorée par phase ENSO) dans la fiche de chaque région, district, commune ou fokontany (courbe du district). L'état ENSO du moment (ONI le plus récent) s'affiche dans l'en-tête et est rafraîchi à chaque mise à jour.
À refaire une fois par an après la saison (relancer le workflow 2). **Limites** : 40 à 45 saisons seulement, classement simplifié (moyenne de l'ONI sur la saison, seuils ±0,5), pluie satellitaire, et pas encore de projections climatiques futures (CMIP6), de température ni de prévision saisonnière : prévus ensuite.

### Population précise (fokontany)

Le workflow « 1 - Construire les limites et la population » remplace, par défaut, la population OCHA COD-PS (référence 2018) par la somme de la grille **WorldPop 100 m** (version R2025A, estimation modélisée) dans chaque fokontany (`scripts/build_population_grid.py`). Si la grille est introuvable, COD-PS est conservée. La source de population est indiquée dans l'outil ; à valider avec l'INSTAT et à comparer au recensement quand il sera disponible.

## 3. Ajouter une source de données (connecteur)

1. Déclarer l'indicateur dans `config/indicators.yml` (secteurs, ODD, cadre national, source, fréquence, statut). Le test de cohérence refuse les références inconnues.
2. Écrire un script `scripts/<source>.py` qui télécharge la donnée, la ramène à une valeur par unité administrative (par exemple en échantillonnant une grille au centroïde, comme `compute_metrics.py` le fait pour la pluie) et écrit un fichier dans `data/<pays>/`.
3. Brancher le calcul dans `scripts/compute_metrics.py`, ajouter l'étape dans `.github/workflows/update-data.yml`, puis une couche dans `docs/app.js` (`LAYERS`).
4. Ajouter un test dans `tests/test_pipeline.py`.

Sources prévues (à vérifier une à une : disponibilité, licence, fréquence) : prévisions de crue (Flood Hub, GloFAS), cyclones, évapotranspiration et humidité du sol (ERA5-Land), végétation (MODIS/VIIRS, Sentinel-2), qualité de l'air (Copernicus CAMS), accès à l'eau (JMP), établissements de santé et écoles (listes officielles), (l'IPC est déjà branché).
**Vérifier la licence de chaque source avant toute redistribution.**

## 4. Ajouter un pays

Copier `config/countries/mdg.yml` vers `config/countries/<code>.yml`, adapter (zone, niveaux administratifs, jeux HDX, saison des pluies), puis lancer les trois workflows avec ce code.
Le site s'ouvre avec `?pays=<code>`.

## 5. Cadre méthodologique (version 1)

- **Pluie** : cumul de la saison / normale 1991–2020 pour la même période (CHIRPS, grille de 0,05°), lue au centroïde de chaque zone, moyenne pondérée par la surface pour les zones qui ont des sous-zones.
- **Alerte** : urgence < 50 %, alerte < 75 %, veille < 90 %. **Seuils provisoires**, à calibrer sur des crises passées avec Météo Madagascar, BNGRC et le groupe IPC.
- **Exposés** : population des fokontany au niveau « alerte » ou plus. **Cibles potentiels** : exposés × part vulnérable.
- **Simulation** : multiplication de la pluie observée par un facteur (×0,50 à ×1,50), tous les calculs sont refaits. Analyse de sensibilité, pas une prévision.
- **Alignement des politiques** : ODD (Agenda 2030, qui ont remplacé les OMD), PMO/PGE-R et six priorités budgétaires 2026 (sources : analyse du budget 2026 de l'UNICEF, loi de finances 2026). Les rattachements indicateur → cadre sont des propositions à valider (`config/policy_frameworks.yml`).

### Limites connues
- Population et limites des fokontany : estimations anciennes (référence 2018, révision des limites de 2024 signalée comme à améliorer par OCHA).
- Pluie satellitaire moins fiable en zones montagneuses et côtières.
- La part vulnérable par défaut (80 %) est une approximation fondée sur la pauvreté nationale : à remplacer par IPC ou enquêtes.
- Aucun chiffre ne remplace l'analyse officielle IPC.

## 6. Plan de validation pour la thèse

1. **Validation rétrospective** : l'archive `archive/<pays>/` conserve un instantané des districts à chaque mise à jour. Rejouer des crises passées (par exemple 2020–2021 et 2023–2024 dans le Grand Sud) et comparer avec les phases IPC et les activations d'action anticipée.
2. **Calibration des seuils** sur ces crises, à comparer aux travaux existants sur la calibration des déclencheurs avec des données d'impact historiques.
3. **Incertitude** : ajouter des intervalles de confiance et comparer CHIRPS avec les stations de la Météo.
4. **Co-conception** avec les utilisateurs (BNGRC, Météo Madagascar, Start Network, MapAction, PAM, NRC) et mesure d'usage.

## 7. Tests

```bash
python tests/make_synthetic.py        # données simulées (pays « demo »)
python scripts/build_catalogue.py --country demo
python tests/test_pipeline.py         # cohérence des calculs (hors réseau)
python tests/test_connectors.py       # lecture des limites, population et fichiers CHIRPS (faux fichiers)
npm install --no-save jsdom && node tests/ui_test.js demo   # interface
```
Les tests tournent aussi automatiquement à chaque modification sur GitHub.

## Structure

```
config/        pays, secteurs, indicateurs, cadres de politique (ODD, PGE-R…)
scripts/       connecteurs et calculs (Python)
inputs/        fichiers que les partenaires peuvent modifier
data/          limites, population et normale de pluie (versionnés)
archive/       instantanés des districts par date (historique de validation)
docs/          site web publié (carte, simulation, catalogue)
tests/         tests automatiques
.github/       mises à jour et publication automatiques
```

## Scénarios, prévision et alerte précoce

**Chaîne de précision** : climat (normale CHIRPS 1991–2020, tendance, ENSO) → corrigé par la prévision météo (Open-Meteo, 16 jours, actualisée toutes les 6 h) → corrigé par les observations du jour (CHIRPS). Les jours de pluie connus remplacent l'analogue climatique jusqu'à l'horizon connu.

- **Scénarios de saison** (`scripts/scenarios.py`) : ensemble d'analogues sur ~44 saisons (sec P10, médian, humide P90, El Niño, La Niña, et « prévision saisonnière » si `inputs/prevision_saisonniere.csv` est fourni). Sorties : probabilité d'alerte, population exposée attendue, excès de pluie.
- **Alerte précoce** (`scripts/early_warning.py`) : pluie (jour / 3 jours), rafales, chaleur, saison sèche prolongée, crue (débit GloFAS vs crues de 2, 5, 20 ans par commune, loi de Gumbel). Niveaux 0–3 (Vigilance, Alerte, Alerte maximale). **Les seuils de `config/countries/*.yml` sont provisoires** : à valider avec Météo Madagascar / BNGRC.
- **Seuils de crue** : workflow « 3 - Seuils de crue des rivières » (une fois, `update_floods.py --thresholds`).
- **Plan d'action** par secteur et conseils ménages : `config/playbook.yml` (parts de population par secteur approximatives, à valider avec les clusters).
- **Alertes sectorielles existantes** : importées depuis `inputs/alertes_secteurs.csv` et affichées sans être remplacées.
- **Vue simple « Chez moi »** : messages en langage courant pour ménages, paysans, pêcheurs.

Limites : données de pluie, vent et température modélisées/satellitaires, pas des mesures de station ; la fiabilité mesurée (hindcast sur 44 saisons) et le branchement des API BNGRC/Météo sont les prochaines étapes.

## Profils, risques par horizon et fiabilité mesurée

- **Mon profil** (ménage, agriculteur/éleveur, pêcheur, commune, ONG/ONU) : la fiche d'une zone affiche un tableau des risques propres au profil, sur trois horizons : 7 jours (alerte précoce), saison (scénarios), climat (tendance et ENSO). Définition dans `config/risks.yml`. Un risque dont la donnée n'est pas encore intégrée (éboulement/pente, niveau des puits, choléra, calendrier cultural, houle) est affiché « Données à intégrer », jamais estimé à l'aveugle ; un risque suivi par un indicateur indirect est marqué « indicatif ». Les listes de dégâts possibles sont qualitatives et provisoires, à valider avec les services techniques et les clusters.
- **Fiabilité mesurée** (`scripts/build_hindcast.py`, lancé par le workflow 2) : validation croisée « une saison laissée de côté » du moteur de scénarios. Résultats (erreur, gain par rapport à la climatologie, couverture P10–P90, score de Brier, courbe de fiabilité, erreur par phase ENSO) affichés dans l'onglet Méthode et écrits dans `docs/data/<pays>/hindcast.json`.

## Comparer, différence, indicateurs couplés

- **Saisons passées** : le sélecteur de période propose, en plus des scénarios, chacune des ~44 saisons observées (avec la phase El Niño / La Niña). Niveaux d'alerte, population exposée et cibles sont recalculés avec les seuils et la population d'aujourd'hui (« que se passerait-il aujourd'hui avec la pluie de cette année-là »).
- **Deux cartes** côte à côte et synchronisées (indicateur et période propres à chaque carte) ; **Différence** B − A d'un même indicateur entre deux périodes (rouge = plus de risque en B).
- **Indicateurs couplés** : jusqu'à 3 indicateurs, poids et sens choisis, combinés en un indice 0–100 (classement relatif dans la vue) par moyenne pondérée, « au moins un élevé » (maximum) ou « tous élevés à la fois » (minimum). Le lien de la page garde le mode, les périodes et la recette de l'indice.

## Historique des événements et de la réponse

- **Événements** (GLIDE, IDMC) et **réponse** : projets des plans de réponse (HRP/FTS), activités géolocalisées des partenaires (IATI), et **import 3W/4W** (`inputs/reponses_humanitaires.csv` ou `inputs/interventions.csv`, modèle : `inputs/reponses_humanitaires_modele.csv`). Colonnes obligatoires : `date_debut`, `pcode` (région, district, commune ou fokontany), `cluster`, `organisation`, `beneficiaires`. Les lignes invalides sont ignorées et signalées dans le journal du workflow « 4 - Historique ».
- Aucune source publique ne donne de bénéficiaires par zone : IATI et HRP indiquent une **présence et un budget**, pas un résultat ; seule la couche 3W contient des bénéficiaires.
- La carte propose filtres (période, types d'événements, secteur, organisation, sources), couches (événements, personnes affectées, bénéficiaires, écart cibles − bénéficiaires, projets, budget), marqueurs d'événements, et, par zone, une frise annuelle, la répartition par secteur et le nombre d'événements selon la phase ENSO de la saison.
- Les événements de GLIDE et d'IDMC proches (même type, 10 jours) sont fusionnés pour ne pas être comptés deux fois.

## Hydrologie de terrain

`scripts/hydro_core.py` calcule, à partir d'un modèle numérique de terrain : écoulement (Priority-Flood), aire drainée, réseau hydrographique et ordre de Strahler, bassins versants, hauteur au-dessus du drainage (HAND) et pente. Les algorithmes sont testés sur des terrains dont la réponse est connue (`tests/test_hydro.py`).

## Eau et terrain (workflow « 5 - Hydrologie »)

`scripts/build_hydro.py` lit le modèle numérique de terrain Copernicus GLO-90 (accès libre), le ré-échantillonne à ~550 m et calcule avec `scripts/hydro_core.py` : remplissage des cuvettes et directions d'écoulement (Priority-Flood, Barnes et al. 2014), accumulation (surface drainée), ordre de Strahler, bassins et sous-bassins, hauteur au-dessus du drainage (HAND, Rennó 2008) et pente. Résultats : cours d'eau, bassins et sous-bassins affichables sur la carte (carte « Eau et terrain »), bassin de chaque fokontany dans sa fiche, et six indicateurs par zone (HAND < 5 m et < 15 m, pente moyenne, part en pente > 30 %, altitude, plus grande surface drainée).
Limites : maille de ~550 m (les petits bassins et ruisseaux ne sont pas résolus), pas de digues ni de canaux, HAND = susceptibilité à l'inondation et non carte de crue. Contrôle : la Betsiboka ressort à ~48 000 km² (valeur de référence ~49 000 km²).

## Eau dans le sol et éboulements (workflow « 6 - Eau dans le sol »)

Uniquement des données réelles et des méthodes publiées (`scripts/soilwater_core.py`, tests dans `tests/test_soilwater.py`) :
- **Humidité du sol et excédent hydrique** : bilan mensuel de Thornthwaite & Mather (1957, forme de Steenhuis & Van der Molen 1986), de novembre 1981 à aujourd'hui, avec la pluie CHIRPS, l'évapotranspiration de référence FAO-56 d'ERA5-Land (Open-Meteo, normale 2016-2020), la réserve utile du sol (Saxton & Rawls 2006 sur la texture et le carbone organique de SoilGrids, profondeurs racinaires FAO-56 selon l'occupation du sol ESA WorldCover).
- **Indices standardisés** : scores normaux mois par mois (méthode SPI/SGI, McKee 1993 ; Bloomfield & Marchant 2013). L'**indice relatif de nappe** est la recharge des 12 derniers mois standardisée : ce n'est pas un niveau en mètres. Pour des mètres, il faut des mesures de puits (`inputs/niveau_statique_puits.csv`, à prévoir).
- **Ruissellement** : courbe-numéro SCS (USDA NEH-4) avec groupe hydrologique déduit de la texture ; indicateur `cn2` par zone.
- **Éboulements** : la pluie prévue (jour et 3 jours) est comparée au seuil mondial de déclenchement de Guzzetti et al. (2008), E = 2,28 D^0,8 mm (D en heures), pour les zones dont une part du territoire est en pente de 15 % ou plus (classe « collines » de la FAO). Niveaux : 1, 2 et 3 fois le seuil (convention MakyClimat). Seuil mondial minimal : à calibrer avec un inventaire d'éboulements du BNGRC ou du Cluster Logistique.
Limites : bilan mensuel (pas d'intensité journalière), pas de coefficient cultural, texture SoilGrids pour des sols ferrallitiques plus perméables que leur texture, pente à ~550 m sous-estimée. Les limites sont aussi dans `docs/data/<pays>/soilwater/status.json`.

## Priorités de réponse (pour les gestionnaires d'information)

La carte « Priorités de réponse » classe les zones de la vue (région, district, commune ou fokontany) selon le critère choisi : écart entre les cibles et les bénéficiaires déclarés (3W/4W importés, avec les filtres de « Historique et réponse »), personnes exposées, cibles, niveau d'alerte ou couverture la plus faible. Aucun poids composite n'est inventé. Elle liste aussi les zones où une alerte de niveau « Alerte » ou plus est prévue sous 7 jours (déclencheurs d'action anticipée), génère une note de situation à copier et exporte la liste en CSV. Limite : la réponse non déclarée est invisible ; un écart élevé peut venir d'un manque de rapportage.
