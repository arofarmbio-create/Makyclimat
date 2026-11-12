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

**Rapport R(j)** pour un jour j, dans l'ordre exact des opérations de R-21 (`scripts/r21_cci_temoins.py`, fonction
`alertes` ; 3e version après la relecture Codex du 12/11, 16:24). Les reprévisions publiées ne donnent pas un débit
par jour : pour chaque initialisation t, la valeur q[t, m, maille] est le **maximum du débit sur la fenêtre de 1 à 3
jours** après t. Une initialisation t « couvre » le jour j si j vaut t + 1, t + 2 ou t + 3.
1. Par initialisation t et membre m : r(t, m) = maximum, sur les mailles retenues du district, de q[t, m, maille] / seuil.
2. Par initialisation t :
   - **contrôle** : R(t) = r(t, cf) ;
   - **ensemble** : R(t) = k-ième plus grande des 11 valeurs r(t, m), avec k = ⌈11 × pi⌉ (pi du pli R-21). R(t) ≥ 1
     équivaut à « part des membres au-dessus du seuil ≥ pi » pour cette initialisation.
3. Par jour j : R(j) = maximum de R(t) sur les initialisations qui couvrent j. Comme R-21 garde la probabilité
   maximale des initialisations couvrant le jour, R(j) ≥ 1 équivaut exactement à l'alerte de R-21 ce jour-là.
- **Réanalyse (D2)**, même construction pour rester comparable : aux **mêmes dates d'initialisation t** que les
  reprévisions, q[t, maille] = maximum du débit journalier de la réanalyse sur t + 1 à t + 3 ; R(t) = maximum sur les
  mailles de q / seuil ; R(j) = maximum sur les t qui couvrent j. Ses seuils sont estimés sur les maxima mensuels
  de ces mêmes valeurs de fenêtre (section 5).

**Classes**, attribuées dans cet ordre de priorité (la première vraie l'emporte), J = jours de l'unité, J±3 = ces
jours étendus de 3 jours de part et d'autre :

| Priorité | Classe | Règle (fixée avant calcul) |
|---|---|---|
| 1 | a. Sans rivière | Aucune maille de rivière retenue dans le district |
| 1 bis | n. Non évaluable | Aucun jour de J avec une valeur R(j) valide (jour couvert par une initialisation et donnée présente et finie), même si J±3 en contient |
| 2 | e. Détecté | R(j) ≥ 1 pour un jour valide j de J (alerte R-21) |
| 3 | d. Hors fenêtre | R(j) ≥ 1 pour un jour valide de J±3 hors de J, aucun dans J |
| 4 | c. Signal sous le seuil | max de R sur les jours valides de J±3 entre 0,5 inclus et 1 exclu |
| 5 | b. Aucun signal | max de R sur les jours valides de J±3 < 0,5 |

**Non évaluable** (relectures Codex du 12/11, 16:24 et 16:28) : une donnée absente n'est jamais comptée comme une
absence de signal. Les classes b, c, d et e exigent **au moins un jour valide dans J** ; une valeur valide dans J±3
seulement ne suffit pas. **Couverture partielle** : seuls les jours valides comptent, et la part de jours valides de J
est publiée par unité et par méthode ; une unité dont moins de la moitié des jours de J sont valides est signalée.

**Mêmes unités pour toutes les comparaisons** : les comparaisons entre méthodes (contrôle, ensemble, réanalyse) se font
sur l'ensemble **commun** des unités évaluables pour toutes les méthodes comparées. Le taux du contrôle y est
recalculé (descriptif), au lieu de reprendre les 14,8 % de R-21 sur 425 unités. Les exclusions sont publiées par
méthode et par motif ; les unités non évaluables pour l'une des méthodes forment une ligne et une colonne à part dans
les croisements. Pour les reprévisions, les 425 unités ont par construction une initialisation de 1 à 3 jours avant
l'une de leurs dates ; la classe n vise surtout la réanalyse.

Sorties : effectifs par classe et par méthode (contrôle, ensemble, réanalyse), par saison et par épisode.

## 5. D2 — Référence diagnostique par la réanalyse GloFAS

**Idée** : le débit GloFAS v4 calculé avec la météo observée (réanalyse, `cems-glofas-historical`) indique ce que le
modèle « voit » lorsque la météo est connue. Ce n'est **pas une borne supérieure garantie** (relecture Codex du 12/11,
16:21) : rien n'assure que les détections des prévisions soient incluses dans celles de la réanalyse. C'est une
**référence diagnostique, conditionnelle** au modèle hydrologique et aux seuils.

- **Données** : réanalyse GloFAS v4, débit journalier, emprise de Madagascar, saisons 2003 à 2016, de la fin novembre
  au début avril (pour couvrir les fenêtres des initialisations de décembre à mars) ; **aux mêmes mailles de rivière que R-21**. Source EWDS (Copernicus), une demande par saison, collecte
  reprenable comme R-40. **Téléchargement soumis à l'autorisation du porteur** (environ 14 demandes).
- **Seuils** : même règle que R-21 (blocs mensuels de décembre à mars, Gumbel des moments, saison testée exclue, au
  moins 30 blocs, T_m ≈ 6,3, seuil ≥ 5 m³/s), appliquée aux maxima mensuels des valeurs de fenêtre de la réanalyse
  aux dates d'initialisation (section 4).
- **Charge comparable** (relecture Codex du 12/11, 16:21) : la comparaison avec la prévision se fait à charge
  d'alerte comparable, avec la règle de la section 4 de la fiche. Pour chaque pli (saison testée exclue), on
  multiplie le seuil de la réanalyse par un facteur k (de 0,50 à 2,00, pas de 0,05) choisi sur les saisons
  d'apprentissage pour que sa charge sur les jours-districts témoins soit la plus proche de celle du contrôle, avec un
  écart toléré de ± 20 %. Un pli hors tolérance est signalé. Les charges obtenues en test sont publiées.
- **Détection** : classe e de D1 (dépassement du seuil ajusté un jour de l'unité) ; sensibilité : à ± 1 jour (dates
  imprécises). La détection au seuil non ajusté (k = 1) est publiée à titre descriptif seulement.
- **Lecture fixée avant calcul**, P = détection de la réanalyse à charge comparable et P_c = celle du contrôle,
  **toutes deux sur les mêmes unités évaluables** (section 4) ; les attributions sont des **hypothèses privilégiées**, pas des conclusions :
  - **P ≤ 25 %** : référence basse. Hypothèses privilégiées : (A), ou erreur du modèle hydrologique, ou (B) ; ces
    impacts renseignent peu sur la compétence de prévision, et R-21 se lit « peu informatif » plutôt que « GloFAS
    sans compétence ».
  - **P ≥ 40 % et P − P_c ≥ 15 points**, avec l'intervalle à 95 % de l'écart apparié P − P_c (bootstrap des
    saisons, comme R-21, sur les mêmes unités évaluables) entièrement au-dessus de 0 : la réanalyse repère nettement
    plus que la prévision à charge comparable. Hypothèse privilégiée : (C), une perte liée à la prévision
    (relecture Codex du 12/11, 16:40).
  - **P ≥ 40 % sans cette condition sur P − P_c** (le contrôle atteint lui aussi un taux proche) : aucune attribution ;
    le seuil de 40 % n'est qu'un repère descriptif, et l'écart P − P_c est publié avec son intervalle.
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
- 12/11/2026, 3e version avant tout calcul (relecture Codex de 16:24) : ordre des opérations de R-21 repris exactement
  (maximum de fenêtre par initialisation, puis membres, puis initialisations couvrant le jour) ; réanalyse construite
  aux mêmes initialisations ; classe « non évaluable » séparée de « aucun signal » ; apport formulé sous hypothèses.
- 12/11/2026, 4e version avant tout calcul (relecture Codex de 16:28) : jour valide exigé dans J pour toute classe
  autre que « non évaluable » ; couverture partielle publiée ; comparaisons sur les mêmes unités évaluables, taux du
  contrôle recalculé ; section 11 présentée comme décisions acquises.
- 12/11/2026, 5e version avant tout calcul (relecture Codex de 16:40) : l'hypothèse (C) n'est privilégiée que si
  P ≥ 40 % **et** P − P_c ≥ 15 points avec un intervalle bootstrap (saisons) au-dessus de 0 ; sinon le seuil de 40 %
  reste descriptif, sans attribution.
- 12/11/2026, 6e version avant tout calcul : section 12, choix de codage (valeurs manquantes, départage de k,
  bassins témoins, unités sans rivière, D4), fixés par Claude par délégation du porteur sur les questions de Codex.
- **12/11/2026 — Décisions du porteur du projet** : protocole validé (sous réserve de la relecture de Codex de cette
  version) ; téléchargement de la réanalyse GloFAS autorisé ; observations communales Copernicus EMS réservées au
  test confirmatoire par sous-bassin (section 8).

## 10. Apport attendu pour la thèse

Une méthode de vérification par l'impact sans station hydrométrique qui **aide à départager, sous hypothèses**,
trois sources d'erreur possibles : l'observation des impacts, la détectabilité hydrologique (référence conditionnelle
par la réanalyse) et la compétence de prévision,
puis qui raisonne par unité hydrologique plutôt qu'administrative. Les travaux proches (Mitheu et al. 2025 ; Kuipers
et al. 2026) s'appuient sur des stations hydrométriques. Aucune évaluation publiée pour Madagascar n'a été trouvée
le 29/10/2026.

## 11. Décisions du porteur du projet (acquises le 12/11/2026)

1. Protocole validé, sous réserve de la relecture de Codex de la version en vigueur.
2. Téléchargement de la réanalyse GloFAS (D2) autorisé : environ 14 demandes Copernicus (EWDS), une à la fois.
3. Observations communales Copernicus EMS réservées au test confirmatoire par sous-bassin (section 8).

## 12. Choix de codage fixés avant calcul (12/11/2026, 17:45, Claude par délégation du porteur)

Réponses aux questions de Codex (fiche R-21, « Code du diagnostic »), fixées **avant toute lecture de détection**.
Règle générale : reprendre R-21 à l'identique et, à défaut, l'option la plus prudente.

1. **Valeurs manquantes (D1, D2).** Contrôle et ensemble : les fonctions de `scripts/r21_scores.py` sont reprises
   telles quelles (même traitement des NaN que R-21 : NaN = pas de dépassement). Réanalyse : une fenêtre n'est
   valide que si **tous ses jours** sont présents ; sinon l'initialisation compte comme « non évaluable » pour la
   réanalyse (classe n si aucune autre n'est valide). Une maille dont le seuil est NaN ne déclenche jamais d'alerte.
   Un bloc mensuel entièrement NaN est retiré du calcul de Gumbel ; la règle « au moins 30 blocs » s'applique après ce retrait.
2. **Facteur k (D2).** À écart de charge égal, on retient le k **le plus proche de 1**, puis le plus petit. Charge
   cible nulle ou pli sans témoin valide commun : k = 1, pli déclaré **hors tolérance** (compté dans la règle des
   3 plis sur 12).
3. **Bassins (D3a).** Bassins témoins d'un mois : ceux qui ne recoupent **aucun** district déclaré ce mois-là, comme
   les districts témoins de R-21. k est **recalibré** sur les jours-bassins témoins, avec la règle 2. Jours d'une unité
   épisode × bassin : union des dates des fiches des seuls districts rattachés à ce bassin (règle des 20 %).
4. **Unités sans rivière.** Comme dans R-21, elles restent au dénominateur de P et de P_c, comptées non détectées
   (comparabilité avec les 16,0 % et 14,8 %). Sensibilité publiée : P et P_c sans ces unités. Le croisement de D1 est
   une table 6 × 6 (a à e, plus n).
5. **Contexte cyclonique (D4).** Le complément CHIRPS est **différé** (descriptif, non nécessaire aux règles de lecture).
   Distance : positions IBTrACS publiées (pas de 3 heures), sans autre interpolation.
