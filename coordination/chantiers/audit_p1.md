# Audit du 09/11 — points P1

Responsable : Codex. Exécution `exec:codex:20261112-1731-audit-p1`.
Début : 12/11/2026 17:23 Nairobi. Livraison à relire puis à commiter par Claude.
Référence : [audit, section D](../../validation/audit_codex_2026-11-09.md).
Prérequis licence CMIP6 livré séparément, puis commité par Claude (`90aff20`).

## Lot A — NPZ sans pickle

Tous les appels NumPy `load` des scripts utilisent explicitement `allow_pickle=False`,
y compris les lecteurs de releases et leurs caches. Le lecteur commun ferme aussi
l'archive en cas de refus. Pas de conversion automatique des anciennes archives
contenant des objets : elles sont refusées. Les producteurs examinés des archives
RX3 et E1 écrivent des tableaux numériques et Unicode.

`tests/test_npz_safety.py` inspecte l'AST de tous les scripts, reconnaît les alias
NumPy et les imports directs, exige le booléen littéral False ; vérifie aussi le
rejet d'un tableau d'objets et la lecture de tableaux numériques et Unicode.

## Lot B — Dépendances directes figées

Versions exactes dans les deux fichiers requirements et dans chaque installation
Python des workflows, sondes et CI incluses. Le socle reprend les versions déjà
figées du workflow GloFAS (NumPy 2.2.6, SciPy 1.15.3, xarray 2025.6.1, etc.),
complétées par des versions explicites des autres dépendances directes.
`tests/test_workflow_dependencies.py` lit tous les YAML et les requirements
référencés, puis refuse les dépendances directes sans `==` exact.

Limite explicite : ce n'est pas un verrou de toutes les dépendances transitives
avec empreintes. Aucun paquet installé ni téléchargé pendant cette intervention ;
la résolution et l'installation de cet environnement sous Linux restent à vérifier
dans un lancement ultérieurement autorisé. Les tests locaux utilisent le venv
existant, dont les versions diffèrent (notamment NumPy 2.5.4 et pandas 3.1.0).

## Lot C — Garde de publication

`scripts/validate.py` contrôle les alertes météo/crue, l'ensemble GloFAS, le
ruissellement prévu et les bornes des indicateurs de susceptibilité, potentiel
d'eau, profondeur, productivité et excédent hydrique présents dans les sorties.
Il parcourt les régions/districts et tous leurs détails commune/fokontany.
Dates de collecte, périodes, disponibilités, niveaux, probabilités, effectifs,
valeurs finies et statut expérimental du ruissellement sont vérifiés.
Le seuil de fraîcheur est celui déjà configuré pour la météo (3 jours par défaut),
appliqué également aux crues et au ruissellement. Une couche facultative absente
reste admise si aucune valeur active contradictoire n'est publiée.
Ces contrôles sont un contrat logiciel, pas une validation scientifique des cartes.

Le garde existant du workflow principal reste obligatoire avant l'artefact Pages ;
son emplacement et le code de sortie bloquant sont testés. Les trois nouveaux
fichiers de tests sont inscrits dans la CI, sans lancer de workflow.

## Vérifications locales

Commande de chaque suite : `.venv/Scripts/python.exe -B -X utf8 tests/test_<nom>.py`.
18 suites réussies : `npz_safety`, `workflow_dependencies`, `publication_guard`,
`validate`, `pluvial_forecast`, `validate_pluvial`, `shocks`, `e1_sources`,
`e1_fusion`, `e1_relief`, `e1_impacts`, `imerg`, `verification_impact`,
`glofas_reanalyse`, `build_cmip6_nexgddp`, `nappes_hc2`, `covariables_hc6`, `soilwater`.
Les trois nouvelles suites ont été repassées après les derniers changements :
2 tests NPZ, 1 contrôle global des workflows et 12 tests du garde, tous réussis.

Fixtures préparées par `tests/make_synthetic.py` ; intégration avec
`scripts/compute_metrics.py --country demo --today 2026-02-21`, puis appel du
garde sur les sorties du pays démo (332 unités), à cette date simulée : accepté.
Le premier passage a correctement refusé les valeurs de ruissellement restantes
après le scénario « source indisponible » de `test_pluvial_forecast.py` ; après
régénération locale par `update_pluvial_forecast.main` avec RX3/CN synthétiques,
aucune erreur. Un test négatif initial a été ajusté pour dépasser la tolérance
d'arrondi existante de 1 personne (22 cibles pour 20 exposés, au lieu de 21).
`git diff --check` : sans erreur.

Aucun téléchargement, workflow, calcul scientifique réel, commit ou push.
Suite : Claude relit les trois lots, puis commite ; installation Linux des versions
figées à vérifier lors d'un lancement autorisé. Aucun chantier R-21 bis traité ici.

## Fichiers modifiés par lot

<!-- inventaire complété mécaniquement à la livraison -->

### A

- `scripts/build_c3s_seasonal.py`
- `scripts/build_covariables_hc6.py`
- `scripts/build_e1_sources.py`
- `scripts/build_rx3_clim.py`
- `scripts/build_shocks.py`
- `scripts/build_soilwater.py`
- `scripts/common.py`
- `scripts/r21_cci_temoins.py`
- `scripts/r21_couverture_seuils.py`
- `scripts/r21_eligibilite.py`
- `scripts/update_pluvial_forecast.py`
- `scripts/validate_c3s_hybrid.py`
- `scripts/validate_e1.py`
- `scripts/validate_e1_impacts.py`
- `scripts/validate_e1_relief.py`
- `scripts/validate_events.py`
- `scripts/validate_fokontany.py`
- `scripts/validate_imerg_pluvial.py`
- `scripts/validate_landslides.py`
- `scripts/validate_nappes_hc2.py`
- `scripts/validate_pluvial.py`
- `scripts/validate_reforecast_impact.py`
- `tests/test_npz_safety.py`

### B

- `.github/workflows/build-c3s-seasonal.yml`
- `.github/workflows/build-cmip6-nexgddp.yml`
- `.github/workflows/build-covariables-hc6.yml`
- `.github/workflows/build-depot-chlorure-merra2.yml`
- `.github/workflows/build-drought-spei-ndvi.yml`
- `.github/workflows/build-e1-sources.yml`
- `.github/workflows/build-glofas-reforecast.yml`
- `.github/workflows/build-imerg-pilot.yml`
- `.github/workflows/build-mct-era5.yml`
- `.github/workflows/build-nappes-mondiales.yml`
- `.github/workflows/build-ndvi-mod13c2.yml`
- `.github/workflows/build-r02bis-sources.yml`
- `.github/workflows/glim-points.yml`
- `.github/workflows/probe-accounts.yml`
- `.github/workflows/probe-glofas-reforecast.yml`
- `.github/workflows/probe.yml`
- `.github/workflows/validate-e1.yml`
- `.github/workflows/validate-fokontany.yml`
- `.github/workflows/validate-imerg.yml`
- `.github/workflows/validate-nappes-hc1.yml`
- `.github/workflows/validate-reforecast-impact.yml`
- `requirements-update.txt`
- `requirements.txt`
- `tests/test_workflow_dependencies.py`

### C

- `scripts/validate.py`
- `tests/test_publication_guard.py`

### CI commune aux trois lots

- `.github/workflows/tests.yml`

### Suivi

- `COORDINATION.md`
- `coordination/chantiers/audit_p1.md`
- `pilotage/etat/reprise_codex.md (local, non versionné)`

Livraison : 12/11/2026 17:33 Nairobi, à relire et à commiter par Claude.
