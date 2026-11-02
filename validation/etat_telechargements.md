# État des téléchargements (agent de téléchargement)

*Tenu par l'agent de téléchargement depuis le 02/11/2026, décision du porteur du projet : un seul agent pour tous les
téléchargements et liaisons API, petit à petit, sans demandes forcées ni simultanées auprès d'un même fournisseur.
Mis à jour à chaque étape. Dernière mise à jour : 02/11/2026, 12 h 40 UTC.*

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
| E1 CHIRPS journalier | CHC | 2001-2026 (26 ans) | 2001-2012, 2015 | 2013-2014, 2016-2026 | 429 (32 requêtes simultanées, 02/11 matin) ; corrigé | ⏳ en cours, une année à la fois (run 41444684197) |
| E1 IMERG Late journalier | NASA GES DISC | 2001-2026 | — | tout | 503 puis coupures : 3 tâches de 6 fils en parallèle saturaient le compte (sonde du 02/11, run 41441586107) ; corrigé, séquentiel | ⏳ 2001 en cours (run 41444684197) |
| E1 ERA5-Land journalier | Copernicus CDS | 2001-2026 | — | tout | « Maximum number queued requests » alors que la file ERA5-Land du compte était vide ; une demande C3S bloquée occupait la file du compte | ⏳ 2015 en cours, après ménage (run 41443140863) ; les autres années ensuite |
| E1 stations GSOD | NOAA NCEI | 2001-2026, stations de Madagascar | 24 stations | — | — | ✅ |
| E1 relief (altitude, rugosité, exposition) | Amazon S3 (GLO-90) | grille 0,1° | 5 432 mailles terrestres | — | — | ✅ `data/mdg/e1/relief_01deg.npz`, calculé sur ce PC le 02/11 |
| SPEI : pluie par district | CHC | 1981-2025 | oui | — | — | ✅ |
| SPEI : NDVI par district | AppEEARS (NASA) | 2000-2025 | version d'octobre | mise à jour en cours | — | ⏳ (run 41406634717) |
| SPEI : ET0 ERA5-Land mensuelle | Copernicus CDS | 1981-2025 | — | tout | même blocage Copernicus que ci-dessus | ⏸ en attente : après ERA5-Land d'E1 |
| Indice MCT (ERA5 850 hPa) | Copernicus CDS | déc.-févr. 1981-2025 | — | tout | — (script et workflow 22 prêts, testés) | ⏸ en attente : après l'ET0 du SPEI |
| Reprévisions GloFAS v4 | Copernicus EWDS | 21 saisons x 6 mois = 126 mois | 18 mois | 108 mois | file d'attente pleine (années lancées 2 par 2, 01/11) ; puis en concurrence avec ERA5-Land | ⏸ mis en pause le 02/11 (run 41411661636 annulé) : après l'indice MCT |
| Prévisions C3S (10 systèmes) | Copernicus CDS | 10 systèmes | 0 | 10 | demande bloquée 5 h sans livraison, qui gênait ERA5-Land | ⏸ en pause depuis le 02/11 : en dernier |
| IMERG demi-horaire, périmètre pilote | NASA GES DISC | 11 saisons (2014-2024) | 2014, 2017, 2018, 2022, 2023, 2024 | 2015, 2016, 2019, 2020, 2021 | concurrence avec IMERG E1 sur le même compte | ⏸ mis en pause le 02/11 (run 41406653970 annulé) : après IMERG E1 |
| ONI, DMI, SIOD, MOZ (ERSST) | NOAA | mensuel | ONI, DMI ; SIOD et MOZ en cours | — | — | ⏳ workflow 8 lancé le 02/11 (run 41444771537) |
| Niveaux de nappe HT Analytics | MGMERL (dossier partagé) | 16 sites | 16 séries (juin 2025) | Water Missions, Lorentz, relevés ACF | — | ✅ manuel, hors git |
| Rapports de forage, exports MGMERL | MGMERL (api.mwater.co) | lithologie, essais de pompage | — | tout | l'extension Chrome n'a pas le droit d'accéder à api.mwater.co | ⛔ décision humaine : autoriser le site dans l'extension |

## Journal des actions de l'agent

- 02/11, 12 h 25 UTC : sonde IMERG lue ; cause de la lenteur trouvée (concurrence). Code séquentiel, attentes et arrêt de
  sécurité, testés ; lancement E1 précédent annulé et relancé avec une seule année IMERG à la fois.
- 02/11, 12 h 30 UTC : créneaux CHIRPS ajoutés au workflow 20 ; relief E1 calculé sur ce PC ; script et workflow de
  l'indice MCT prêts ; GloFAS et IMERG pilote mis en pause pour respecter la règle « un fournisseur à la fois ».
