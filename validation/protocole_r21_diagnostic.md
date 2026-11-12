# Protocole R-21 bis : diagnostic de la faible détection, référence par la réanalyse et raisonnement par bassin

*Rédigé le 12/11/2026 par Claude, à la demande du porteur du projet, **avant tout calcul de diagnostic**. Fait suite à
la clôture de R-21 ([rapport](r21_rapport.md)) et aux avis de Codex et de Claude
([fiche du chantier](../coordination/chantiers/r21.md#avis-et-améliorations)). Toute modification sera datée et
justifiée en section 9.*

## 1. Question

R-21 n'a mis en évidence aucun gain de l'ensemble GloFAS sur son contrôle, mais surtout : **les deux méthodes ne
détectent qu'environ 15 % des unités épisode × district touchées**. Avant tout nouveau test de compétence, il faut
savoir **d'où peut venir cette perte**. Trois **hypothèses**, non exclusives :

- **(A) Lien rivière-impact** : les impacts déclarés ne sont pas des crues de rivière (vent, pluie locale, côte) ou
  sont mal localisés ou datés.
- **(B) Seuils et fenêtre** : un signal de crue existe, mais sous le seuil retenu ou hors de la fenêtre de 1 à 3 jours.
- **(C) Prévision** : la crue est présente dans le débit calculé avec la météo observée, mais la prévision la manque.

Seul (C) relève de la compétence de prévision. R-21 ne pouvait pas les départager. **Le diagnostic ne les tranche
pas non plus de façon certaine** (relecture Codex du 12/11, 16:21) : il donne des indices et privilégie une hypothèse
lorsque les règles de la section 5 sont remplies, sans conclusion causale acquise. En particulier, une réanalyse qui
détecte peu ne sépare pas les impacts non fluviaux (A) des erreurs du modèle hydrologique lui-même.

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
de R-21 (section 2 de la [fiche](r21_fiche_methode.md), saison testée exclue).

**Rapport journalier R(j)**, pour un jour de validité j (version précisée après la relecture Codex du 12/11, 16:21) :
- **contrôle** : maximum, sur les mailles du district et sur les initialisations d'échéance 1 à 3 jours valides le
  jour j, de débit / seuil ;
- **ensemble** : pour chaque membre m, r_m(j) = même maximum pour ce membre ; R(j) = k-ième plus grande des 11 valeurs
  r_m(j), avec k = ⌈11 × pi⌉ (pi du pli R-21). Ainsi R(j) ≥ 1 équivaut exactement à « part des membres au-dessus du seuil ≥ pi »,
  c'est-à-dire à l'alerte de R-21 ;
- **réanalyse (D2)** : débit / seuil du jour j, maximum sur les mailles du district (pas d'échéance).

**Classes**, attribuées dans cet ordre de priorité (la première vraie l'emporte), J = jours de l'unité, J±3 = ces
jours étendus de 3 jours de part et d'autre :

| Priorité | Classe | Règle (fixée avant calcul) |
|---|---|---|
| 1 | a. Sans rivière | Aucune maille de rivière retenue dans le district |
| 2 | e. Détecté | R(j) ≥ 1 pour un jour j de J (alerte R-21 ; pour la réanalyse, dépassement un jour de l'unité) |
| 3 | d. Hors fenêtre | R(j) ≥ 1 pour un jour de J±3, aucun dans J |
| 4 | c. Signal sous le seuil | max de R sur J±3 entre 0,5 inclus et 1 exclu |
| 5 | b. Aucun signal | max de R sur J±3 < 0,5, ou aucune donnée valide |

Sorties : effectifs par classe et par méthode (contrôle, ensemble, réanalyse), par saison et par épisode.

## 5. D2 — Référence diagnostique par la réanalyse GloFAS

**Idée** : le débit GloFAS v4 calculé avec la météo observée (réanalyse, `cems-glofas-historical`) indique ce que le
modèle « voit » lorsque la météo est connue. Ce n'est **pas une borne supérieure garantie** (relecture Codex du 12/11,
16:21) : rien n'assure que les détections des prévisions soient incluses dans celles de la réanalyse. C'est une
**référence diagnostique, conditionnelle** au modèle hydrologique et aux seuils.

- **Données** : réanalyse GloFAS v4, débit journalier, emprise de Madagascar, mois de décembre à mars des saisons 2003
  à 2016, **aux mêmes mailles de rivière que R-21**. Source EWDS (Copernicus), une demande par saison, collecte
  reprenable comme R-40. **Téléchargement soumis à l'autorisation du porteur** (environ 14 demandes).
- **Seuils** : même règle que R-21 (blocs mensuels de décembre à mars, Gumbel des moments, saison testée exclue, au
  moins 30 blocs, T_m ≈ 6,3, seuil ≥ 5 m³/s), appliquée aux maxima mensuels de la réanalyse.
- **Charge comparable** (relecture Codex du 12/11, 16:21) : la comparaison avec la prévision se fait à charge
  d'alerte comparable, avec la règle de la section 4 de la fiche. Pour chaque pli (saison testée exclue), on
  multiplie le seuil de la réanalyse par un facteur k (de 0,50 à 2,00, pas de 0,05) choisi sur les saisons
  d'apprentissage pour que sa charge sur les jours-districts témoins soit la plus proche de celle du contrôle, avec un
  écart toléré de ± 20 %. Un pli hors tolérance est signalé. Les charges obtenues en test sont publiées.
- **Détection** : classe e de D1 (dépassement du seuil ajusté un jour de l'unité) ; sensibilité : à ± 1 jour (dates
  imprécises). La détection au seuil non ajusté (k = 1) est publiée à titre descriptif seulement.
- **Lecture fixée avant calcul**, P = détection de la réanalyse à charge comparable, P_c = celle du contrôle (R-21,
  14,8 %) ; les attributions sont des **hypothèses privilégiées**, pas des conclusions :
  - **P ≤ 25 %** : référence basse. Hypothèses privilégiées : (A), ou erreur du modèle hydrologique, ou (B) ; ces
    impacts renseignent peu sur la compétence de prévision, et R-21 se lit « peu informatif » plutôt que « GloFAS
    sans compétence ».
  - **P ≥ 40 %** : la réanalyse repère nettement plus que la prévision à charge comparable. Hypothèse privilégiée :
    (C), une perte liée à la prévision.
  - **Entre 25 et 40 %** : hypothèses mêlées, à éclairer par D1 et D4.
  - Si plus de 3 plis sur 12 sont hors tolérance de charge, aucune hypothèse n'est privilégiée : écart décrit seulement.
- Croisement avec D1 : pour chaque unité, classe de la réanalyse contre classe de la prévision (table 5 × 5),
  descriptif.

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

Si la référence par la réanalyse dépasse 25 % à charge comparable (section 5), un protocole confirmatoire sera écrit **avant tout calcul**, sur des
données non utilisées ici. Candidat : **observations communales des activations Copernicus EMS** (zones inondées
cartographiées par satellite, indépendantes des déclarations) pour les activations dont les reprévisions existent
(EMSR264 en janvier 2018, EMSR424 en janvier 2020, EMSR645 en janvier 2023). Il sera rattaché aux sous-bassins
(commune → fokontany → sous-bassin), avec une analyse de puissance réaliste, calée sur la détection observée ici.

## 9. Journal des modifications

- 12/11/2026 : rédaction initiale, avant tout calcul de diagnostic.
- 12/11/2026, 2e version avant tout calcul (relecture Codex de 16:21) : « plafond » remplacé par une référence
  diagnostique conditionnelle ; hypothèses A/B/C présentées comme telles ; comparaison réanalyse-prévision à charge
  comparable (facteur k) ; rapport journalier de l'ensemble et de la réanalyse, bornes et priorité des classes fixés.

## 10. Apport attendu pour la thèse

Une méthode de vérification par l'impact sans station hydrométrique qui **sépare trois sources d'erreur** :
l'observation des impacts, la détectabilité hydrologique (référence par la réanalyse) et la compétence de prévision,
puis qui raisonne par unité hydrologique plutôt qu'administrative. Les travaux proches (Mitheu et al. 2025 ; Kuipers
et al. 2026) s'appuient sur des stations hydrométriques. Aucune évaluation publiée pour Madagascar n'a été trouvée
le 29/10/2026.

## 11. Décisions demandées au porteur du projet

1. Valider ce protocole (après relecture de Codex).
2. Autoriser le téléchargement de la réanalyse GloFAS (D2), environ 14 demandes Copernicus, une à la fois, après R-40.
3. Confirmer que les observations communales EMS restent réservées au test confirmatoire (section 8).
