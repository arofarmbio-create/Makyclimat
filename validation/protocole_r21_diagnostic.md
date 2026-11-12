# Protocole R-21 bis : diagnostic de la faible détection, plafond de détectabilité et raisonnement par bassin

*Rédigé le 12/11/2026 par Claude, à la demande du porteur du projet, **avant tout calcul de diagnostic**. Fait suite à
la clôture de R-21 ([rapport](r21_rapport.md)) et aux avis de Codex et de Claude
([fiche du chantier](../coordination/chantiers/r21.md#avis-et-améliorations)). Toute modification sera datée et
justifiée en section 9.*

## 1. Question

R-21 n'a mis en évidence aucun gain de l'ensemble GloFAS sur son contrôle, mais surtout : **les deux méthodes ne
détectent qu'environ 15 % des unités épisode × district touchées**. Avant tout nouveau test de compétence, il faut
savoir **d'où vient cette perte** :

- **(A) Lien rivière-impact** : les impacts déclarés ne sont pas des crues de rivière (vent, pluie locale, côte) ou
  sont mal localisés ou datés. Même un débit parfait ne les repérerait pas.
- **(B) Seuils et fenêtre** : un signal de crue existe, mais sous le seuil retenu ou hors de la fenêtre de 1 à 3 jours.
- **(C) Prévision** : la crue est présente dans le débit calculé avec la météo observée, mais la prévision la manque.

Seul (C) relève de la compétence de prévision. R-21 ne pouvait pas séparer ces trois causes.

## 2. Statut et garde-fous

- **Diagnostic exploratoire** : aucune hypothèse confirmatoire n'est testée ici. Les résultats servent à concevoir un
  protocole confirmatoire ultérieur, sur des données réservées (section 8).
- **Données du diagnostic** : seulement celles déjà utilisées par R-21 (saisons 2003 à 2016, 425 unités, DesInventar),
  plus la réanalyse GloFAS (D2). **Les observations communales des activations Copernicus EMS restent réservées** au
  test confirmatoire par sous-bassin : elles ne sont pas lues ici.
- Règles et seuils de lecture fixés ci-dessous, avant calcul. Aucun réglage ne sera ensuite présenté comme confirmé
  sur les mêmes données.

## 3. Constat déjà connu, déclaré avant calcul (aucune détection lue)

Composition des 425 unités éligibles par type de fiche DesInventar : **417 « cyclone », 8 « inondation »**. La
comparaison des taux de détection par type de fiche, proposée le 12/11, est donc impossible. Elle est remplacée par le
contexte cyclonique (D4). Ce constat rend l'hypothèse (A) a priori plausible : une fiche « cyclone » peut relever
du vent seul.

## 4. D1 — Classement de chaque unité (reprévisions déjà publiées)

Pour chaque unité épisode × district (425), sur les mailles de rivière du district retenues dans R-21, avec les seuils
de R-21 (section 2 de la [fiche](r21_fiche_methode.md), saison testée exclue) et le **membre de contrôle** :

| Classe | Règle (fixée avant calcul) |
|---|---|
| a. Sans rivière | Aucune maille de rivière retenue dans le district |
| b. Aucun signal | Rapport débit / seuil maximal < 0,5 sur les dates de l'unité ± 3 jours, toutes échéances 1 à 3 jours |
| c. Signal sous le seuil | Rapport maximal entre 0,5 et 1 sur la même fenêtre |
| d. Hors fenêtre | Dépassement dans les ± 3 jours, mais pas sur un jour de l'unité (alerte R-21 absente) |
| e. Détecté | Alerte R-21 présente (contrôle) |

Même classement pour l'ensemble (part des membres au-dessus du seuil ≥ pi du pli R-21). Sorties : effectifs par
classe, par saison et par épisode.

## 5. D2 — Plafond de détectabilité (réanalyse GloFAS)

**Idée** : le débit GloFAS v4 calculé avec la météo observée (réanalyse, `cems-glofas-historical`) est la meilleure
prévision possible du modèle. Sa détection est le **plafond** que la prévision ne peut pas dépasser avec ces impacts.

- **Données** : réanalyse GloFAS v4, débit journalier, emprise de Madagascar, mois de décembre à mars des saisons 2003
  à 2016, **aux mêmes mailles de rivière que R-21**. Source EWDS (Copernicus), une demande par saison, collecte
  reprenable comme R-40. **Téléchargement soumis à l'autorisation du porteur** (environ 14 demandes).
- **Seuils** : même règle que R-21 (blocs mensuels de décembre à mars, Gumbel des moments, saison testée exclue, au
  moins 30 blocs, T_m ≈ 6,3, seuil ≥ 5 m³/s), appliquée aux maxima mensuels de la réanalyse.
- **Détection** : une unité est détectée si une maille du district dépasse le seuil un jour de l'unité (principal) ;
  sensibilité : à ± 1 jour (dates imprécises). Charge sur les jours-districts témoins de R-21, publiée.
- **Lecture fixée avant calcul**, P = détection de la réanalyse (principal) :
  - **P ≤ 25 %** : plafond bas. La perte vient surtout de (A) ou (B). Ces impacts ne permettent pas de juger la
    compétence de prévision ; R-21 se lit « peu informatif » plutôt que « GloFAS sans compétence ».
  - **P ≥ 40 %** : la réanalyse repère nettement plus que la prévision (environ 15 %) : la perte vient surtout de la
    prévision (C).
  - **Entre 25 et 40 %** : causes mêlées, à départager par D1 et D4.
- Croisement avec D1 : pour chaque unité, classe de la réanalyse contre classe de la prévision (table 5 × 5).

## 6. D3 — Raisonnement par bassin hydrologique

Unités hydrologiques : bassins et sous-bassins de l'atlas (`data/mdg/hydro_units.csv`, fokontany → bassin (109) →
sous-bassin (1 262)).

- **D3a, par bassin (principal)** : un épisode touche un bassin si un district déclaré contient au moins **20 % de sa
  population** dans ce bassin (populations des fokontany, `data/mdg/units.csv`) ; sensibilité : tout bassin
  recoupant un district déclaré. Une méthode détecte l'unité épisode × bassin si une maille de rivière du bassin
  est en alerte un jour de l'épisode (contrôle, ensemble au pi du pli R-21, réanalyse D2). Charge par
  jours-bassins témoins. Comparaison descriptive avec le district (même épisode).
- **Présentation** : résultats par bassin, avec la liste des districts concernés et, pour chaque district, ses
  communes et sous-bassins, pour lire où se situent les détections et les manques.
- **Sous-bassins** : impossible avec DesInventar (impacts au district seulement). Le niveau sous-bassin est réservé au
  test confirmatoire avec les observations communales Copernicus EMS (section 8).

## 7. D4 — Contexte cyclonique (trajectoires IBTrACS, `docs/data/mdg/cyclones.json`)

Pour chaque unité : distance minimale entre le district (centroïde pondéré par la population des fokontany) et le
centre du cyclone, sur les dates de l'unité ± 1 jour. Classes : < 100 km, 100 à 300 km, > 300 km ou aucun cyclone.
Détection (prévision et réanalyse) par classe. Lecture : une détection faible près de la trajectoire et une
réanalyse elle aussi muette suggèrent des impacts dus au vent (A). La pluie quotidienne (CHIRPS) est ajoutée
seulement si sa couverture locale suffit (fichier pilote actuel : 2 040 jours) ; sinon, c'est déclaré.

## 8. Suite prévue : test confirmatoire par sous-bassin (non engagé)

Si le diagnostic montre un plafond suffisant, un protocole confirmatoire sera écrit **avant tout calcul**, sur des
données non utilisées ici. Candidat : **observations communales des activations Copernicus EMS** (zones inondées
cartographiées par satellite, indépendantes des déclarations) pour les activations dont les reprévisions existent
(EMSR264 en janvier 2018, EMSR424 en janvier 2020, EMSR645 en janvier 2023). Il sera rattaché aux sous-bassins
(commune → fokontany → sous-bassin), avec une analyse de puissance réaliste, calée sur la détection observée ici.

## 9. Journal des modifications

- 12/11/2026 : rédaction initiale, avant tout calcul de diagnostic.

## 10. Apport attendu pour la thèse

Une méthode de vérification par l'impact sans station hydrométrique qui **sépare trois sources d'erreur** :
l'observation des impacts, la détectabilité hydrologique (plafond par la réanalyse) et la compétence de prévision,
puis qui raisonne par unité hydrologique plutôt qu'administrative. Les travaux proches (Mitheu et al. 2025 ; Kuipers
et al. 2026) s'appuient sur des stations hydrométriques. Aucune évaluation publiée pour Madagascar n'a été trouvée
le 29/10/2026.

## 11. Décisions demandées au porteur du projet

1. Valider ce protocole (après relecture de Codex).
2. Autoriser le téléchargement de la réanalyse GloFAS (D2), environ 14 demandes Copernicus, une à la fois, après R-40.
3. Confirmer que les observations communales EMS restent réservées au test confirmatoire (section 8).
