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
