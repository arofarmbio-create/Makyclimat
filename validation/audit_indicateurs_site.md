# Audit des indicateurs affichés sur le site MakyClimat (09/11/2026)

*Catalogue en ligne (`data/mdg/catalogue.json`, construit par `scripts/build_catalogue.py`) : 126 indicateurs, dont 116
actifs et 10 prévus. Critères : cohérence avec nos résultats de recherche, honnêteté de la formulation (pas plus que ce
qui est prouvé), clarté pour un utilisateur humanitaire, conformité au protocole doctoral (H6 incertitude, E4 type de
résultat, M7 preuves).*

## 1. En contradiction avec nos résultats : à corriger en priorité

| Indicateur | Libellé actuel | Problème | Correction proposée |
|---|---|---|---|
| `recharge12_z` | « Indice relatif de nappe (…) ; négatif = nappe probablement basse » | H-N1 (R-36) : cet indice ne suit pas les niveaux mesurés (non établi, puissance faible) ; et le bilan mensuel ne voit pas la recharge épisodique du Sud | « Excédent hydrique standardisé sur 12 mois (indice de recharge potentielle, **non comparé avec succès aux niveaux mesurés**) » ; retirer « nappe probablement basse » |
| `water_table_depth_m` | « Profondeur de nappe publiée à l'échelle régionale (ordre de grandeur) » | Dépassé : la carte nationale v2 donne le niveau statique par fokontany avec sa fourchette à 80 % | Remplacer par le niveau statique v2, sa fourchette et la part extrapolée (déjà dans l'onglet Nappes) |
| `susc_inond_pct` | « probabilité estimée d'être inondé ou endommagé » | R-02/R-03 : AUC instable d'un événement à l'autre (8 activations ; dégâts aux bâtiments 0,16 à 0,62) : ce n'est pas une probabilité calibrée | « Score relatif de susceptibilité aux inondations (classement, pas une probabilité) » |
| `ruiss_prevu_*` | « EXPÉRIMENTAL - … » | R-23 : ni le cumul ni l'intensité des pluies ne repèrent les inondations pluviales du périmètre (AUC 0,38 à 0,48) | Garder, mais avec le niveau « Non validé » et le renvoi vers R-23, au lieu d'un préfixe en capitales |
| `aquifer_productivity_pct`, `aquifer_yield_lsec_mid` | classes BGS (socle, sédimentaire, volcanique, karst) | Les classes BGS mélangent des nappes de comportement opposé (sables de l'Androy et karst de Toliara) et se contredisent avec la GLiM pour un site sur douze | Ajouter « classe cartographique à 1/5 000 000 : à confirmer par la coupe du forage » |

## 2. Formulations qui en disent plus que la preuve

- `rain_trend_signif_share` : « tendance statistiquement significative (p < 0,10) » sur des milliers de mailles sans
  correction des tests multiples : une part de mailles « significatives » apparaît même sans tendance (environ 10 %).
  Ajouter « sans correction des tests multiples ; environ 10 % attendus par hasard ».
- `enso_corr` : corrélation affichée sans indication de significativité ; R-25 montre que la plupart des régions ne
  passent pas la correction. Ajouter « lien non démontré dans la plupart des régions (`teleconnexions.md`) ».
- `response_coverage` et l'écart « cibles moins bénéficiaires déclarés » : les déclarations des partenaires sont
  incomplètes ; un écart n'est pas un besoin non couvert. Ajouter « écart de déclaration, pas besoin non couvert ».
- `vuln_cumul_idx`, `potentiel_eau_pct` : bien formulés (« classement », « PAS une probabilité ») ; garder.

## 3. Clarté et forme

- « Cibles potentiels » : faute d'accord ; écrire **« Cibles potentielles »** (deux endroits).
- Couche « Population exposée » : préciser l'aléa, comme dans le catalogue (« à la sécheresse »).
- 27 indicateurs sont des **valeurs de région ou de district** (EDS, accès, crues, prix du riz, prévision saisonnière).
  Affichés au fokontany, ils peuvent faire croire à une différence locale qui n'existe pas. Afficher « valeur de la
  région, identique pour tous ses fokontany » dans l'infobulle et la légende.
- Termes techniques sans traduction : « trunk à tertiary » (OSM), « kt », « CN », « HAND ». Ajouter une explication courte.
- Préfixe « EXPÉRIMENTAL » en capitales : remplacer par le niveau de preuve du site (Validé / Standard / Approximation /
  Non validé), pour un seul système de signalement.
- **10 indicateurs « prévus » font doublon** avec des indicateurs actifs : `ndvi_anomaly` (actif : `ndvi_anom_z`),
  `et0_water_balance` (actifs : `sm_rel_pct`, `whc_mm`…), `flood_exposure` (actifs : `crue_rp10_*`, `crue_rp100_*`),
  `cyclone_exposure` (actifs : `choc_cyc_*`). Les retirer ou les fusionner ; garder seulement les vrais manques (air,
  santé, scolarité, élevage, production agricole).

## 4. Manques structurels face au protocole doctoral

| Exigence | Situation | Proposition |
|---|---|---|
| **Niveau de preuve par indicateur** (M7) | Donné par module dans l'onglet Fiabilité, pas par indicateur | Ajouter au catalogue un champ « preuve » (niveau et identifiants R-xx) affiché dans l'infobulle |
| **Type de résultat** (E4) | Absent | Champ « type » : reconstitution, anticipation, suivi (déjà défini par module dans l'onglet Preuves) |
| **Incertitude** (H6) | Aucun intervalle hors prévision saisonnière et nappes | Afficher les fourchettes existantes ; écrire « estimation centrale, sans intervalle » ailleurs (population exposée, cibles) |
| **Date de la donnée** | Fréquence indiquée, pas la date de la dernière valeur | Ajouter la date de la dernière mise à jour à chaque indicateur |

## 5. Ce qui est bien fait

- Sources citées pour chaque indicateur, fréquence indiquée.
- Plusieurs libellés disent déjà honnêtement leurs limites (« nombre minimal », « PAS une prévision de débit », « ordre de
  grandeur »).
- Rattachement aux secteurs et aux ODD.
- Distinction exposition / dégât / besoin rappelée dans l'onglet Fiabilité.

## 6. Ordre de correction proposé

1. Section 1 (contradictions avec nos résultats) et la faute « Cibles potentielles » : modifications de texte dans
   `scripts/build_catalogue.py` et `docs/app.js`.
2. Champs « preuve » et « type » au catalogue, affichés dans l'infobulle (relus dans le registre, comme l'onglet Preuves).
3. Mention « valeur de la région » pour les 27 indicateurs hérités ; nettoyage des 10 indicateurs prévus.
4. Date de la dernière valeur.
