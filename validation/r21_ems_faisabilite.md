# R-21 bis — Faisabilité du test EMS

**13/11/2026 — Codex — À relire.** Étape autorisée par le porteur le 13/11 à 08:00,
exécution `exec:codex:20261113-0805-ems-faisabilite`. Référence du dépôt : `afa4a62`.
Module M5, validation par événement E4 ; nouvelle question issue de R-21 bis,
sans modification de R-21, de H1 ni des résultats du diagnostic.

## 1. Périmètre et protocole de faisabilité

Audit documentaire, inventaire des métadonnées publiques et calcul de puissance
**théorique uniquement**. Aucun lancement scientifique, aucune lecture des fichiers
de débits, aucun téléchargement de carte, image, vecteur ou archive EMS.
Les AOI sont des zones demandées/cartographiées, pas des observations positives.
Leur nombre ne mesure ni le nombre de crues ni le nombre de répétitions indépendantes.

Traçabilité de lecture : une recherche textuelle initiale trop large a également
affiché `validation/ems_resultats.json`, fichier de résultats agrégés préexistant.
Ce n'était pas une lecture de géométries, mais cela dépasse la lecture des seules
métadonnées ; cet incident est signalé, sans réutiliser ces valeurs dans le choix
de l'effet, le calcul de puissance ou l'inventaire. Les recherches suivantes ont
été restreintes aux scripts et documents. Aucun fichier d'observations EMS CSV,
GeoJSON, SHP, raster ou archive n'a été ouvert.

**Plan fixé avant le calcul de puissance de cette note :**

- Critère principal proposé : reproductibilité, entre saisons, d'une discrimination
  hydrologique utile des sous-bassins cartographiés par EMS. Par événement, AUC du
  signal de réanalyse GloFAS pour distinguer les sous-bassins inondés des autres,
  exclusivement dans les AOI observées ; puis moyenne des AUC des événements de
  chaque saison, à poids égaux. Une saison réussit si cette moyenne dépasse 0,60.
  Une égalité compte comme échec. L'événement doit avoir les deux classes ; sinon
  il est non évaluable, sans remplacement opportuniste. Ce critère testerait la
  détectabilité spatiale, **pas la compétence d'une prévision anticipée**.
- Effet pertinent proposé : probabilité de réussite d'une saison indépendante
  de 0,80, contre H0 : p ≤ 0,50. AUC > 0,60 demande une discrimination dépassant
  modestement le hasard ; la retrouver dans quatre saisons sur cinq exige une
  stabilité utile, au lieu d'un succès sur un cyclone choisi. Ces valeurs sont
  des exigences méthodologiques proposées, pas des estimations sur EMS.
- Test exact binomial unilatéral, alpha = 0,05, non randomisé ; rejet pour K ≥ k,
  où k est le plus petit entier tel que P[Bin(n, 0,5) ≥ k] ≤ 0,05.
  Puissance = P[Bin(n, 0,8) ≥ k]. Sans seuil de rejet accessible, puissance nulle.
  Pas de simulation, pas de paramètre de dispersion appris sur les observations.
- Unité indépendante : **saison**, après regroupement des événements ; les
  activations d'un même cyclone et leurs suivis ne sont jamais des répétitions.
  Les calculs par événement sont des scénarios optimistes explicitement séparés.
  L'indépendance entre saisons reste une hypothèse, non une garantie fournie par
  le catalogue. Les AOI, communes et sous-bassins ne font jamais croître n.
- Pour cette faisabilité uniquement, on suppose tous les événements évaluables,
  sans pertes d'imagerie : hypothèse favorable. Les dates, seuils de rattachement
  et définitions d'inondation devraient être fixés et relus dans un protocole
  confirmatoire distinct avant tout score, **seulement si la porte de faisabilité
  s'ouvrait**. Aucun protocole de calcul réel n'est autorisé par cette note.
- Condition du porteur : indépendance garantie **et** puissance ≥ 80 %. À défaut,
  verdict « non faisable », option 3, sans prolongation exploratoire.

## 2. Audit des usages antérieurs

Les références ci-dessous désignent l'état `afa4a62` ; elles permettent de vérifier
les usages sans rouvrir les observations ou recalculer les scores.

| Usage | Preuve fichier:ligne | Conséquence pour l'indépendance |
|---|---|---|
| R-02, choix nominatif des cas et validation fokontany/commune | `scripts/validate_fokontany.py:33`, `:184`, `:238`, `:260` | Onze codes ciblés ; modèles et prédictions hors événement produits sur la même source EMS. Laisser un événement de côté ne rend pas le corpus inédit pour la conception d'une nouvelle question. |
| Échecs d'extension | `validation/evenements_2020_2026_note.md:26`, `:29`, `:32` ; `validation/README.md:18` | Ana : archive invalide ; Fytia/Gezani : anciennes couches non reconnues ; Enawo : format ancien jugé inexploitable. Échec technique ne signifie ni absence d'inondation ni absence de produits actuels. Exclure après inspection peut sélectionner les événements. |
| Choix des impacts corroborants | `validation/evenements_2020_2026_note.md:3`, `:16` | Diane ajouté à partir d'EMS ; région déduite des zones EMS. Les listes d'événements et EMS ne sont donc pas entièrement indépendants. |
| R-02 bis | `validation/protocole_r02bis_echelle_alea.md:39`, `:54`, `:68`, `:109` | Sept activations reprises de R-02 ; nouvelles variables proposées après examen de R-02 ; statut exploratoire déjà déclaré pour faible puissance. Une nouvelle partition spatiale ne remet pas à zéro cet historique. |
| R-40 : sources et workflow | `scripts/build_r02bis_sources.py:31` ; `.github/workflows/build-r02bis-sources.yml:40` ; `validation/protocole_r02bis_echelle_alea.md:47` | Ava, Eliakim, Diane, Batsirai, Emnati, Cheneso, Freddy sont explicitement ciblés ; fenêtres IBTrACS prédéfinies. Collecter pluie/rafales ne prouve pas un ajustement des seuils GloFAS sur EMS, mais ces événements sont déjà dans le circuit de développement. |
| Validation des crues GloFAS | `scripts/validate_floods.py:217`, `:222`, `:237` ; `validation/crues_validation.md:70` | Les communes EMS ont déjà été confrontées au débit et au seuil q2, notamment Ava. Il existe donc une exposition antérieure directe de l'évaluation hydrologique à EMS. |
| Validation pluviale et fusion pluie | `scripts/validate_pluvial.py:212` ; `scripts/validate_e1_impacts.py:114` ; `validation/protocole_e1_fusion_pluie.md:129` | EMS sert aussi de critère de comparaison d'autres variantes ; risque de sélection de méthode après résultats, sans démontrer à lui seul un réglage intentionnel. |
| Seuils opérationnels GloFAS | `scripts/update_floods.py:28`, `:46`, `:65` | Gumbel sur maxima annuels simulés, sans cible EMS dans l'estimation. Recouvrement temporel possible avec la validation : ce n'est pas une calibration hors échantillon, même sans apprentissage supervisé EMS. |
| R-21 initial puis méthode révisée | `validation/protocole_verification_impact.md:49`, `:89`, `:157` ; `validation/r21_fiche_methode.md:23`, `:60` ; `scripts/r21_cci_temoins.py:77` ; `scripts/r21_scores.py:35` | EMS annoncé comme corroboration secondaire ; méthode finale fondée sur DesInventar, seuils hors saison et charge sur témoins. Pas d'entrée EMS repérée dans le chemin final des scores ; cela n'efface pas les usages des autres études. La collecte réduite ciblée ne constitue pas un échantillonnage aléatoire des saisons. |
| R-21 bis et choix des trois cas | `scripts/r21_diagnostic.py:8` ; `validation/protocole_r21_diagnostic.md:147`, `:152` ; `validation/r21_bis_rapport.md:66` | EMS non utilisé dans D1–D4, mais Ava/Diane/Cheneso sélectionnés pour les reprévisions disponibles et déjà utilisés ailleurs. « Réservé au diagnostic » ne veut pas dire « jamais vu dans le projet ». |
| Affichage opérationnel | `scripts/connector_ems_live.py:1`, `:35` ; `.github/workflows/update-data.yml:132` | Ingestion régulière de cartes pour le site : autre voie d'exposition ; ce n'est pas une preuve d'ajustement scientifique. |

Le workflow `.github/workflows/validate-fokontany.yml:6` prévoit aussi une
validation trimestrielle (`:35`), et `.github/workflows/validate-floods.yml:3`
annonce explicitement la confrontation GloFAS–EMS. Le filtre de stockage des
reprévisions, `scripts/build_glofas_reforecast.py:24` et `:51`, conserve les
mailles atteignant 5 m³/s ; il n'utilise pas EMS. Les mois 2018, 2020 et 2023
ne doivent toutefois pas être considérés comme totalement vierges : ils
participent au corpus de seuils, même si leur saison est retirée dans le pli
qui la teste (`validation/r21_couverture_seuils.md:21`). Un changement de cible
ne transforme pas les seuils opérationnels en seuils indépendamment validés.

**Verdict d'audit : indépendance confirmatoire non garantie.** Il existe un risque
élevé de sélection des cas et de conception informée par les résultats passés,
et une réutilisation certaine du corpus. Aucun réglage direct des seuils GloFAS
sur les étiquettes EMS n'est démontré par les scripts examinés ; ne pas confondre
ce constat avec une preuve d'absence de toute adaptation historique. Des
observations satellitaires indépendantes des déclarations administratives ne
sont pas nécessairement un jeu de test indépendant du développement. Une
partition par sous-bassin ou un bootstrap spatial ne répare ni cette exposition
ni la dépendance entre bassins touchés par le même cyclone.

## 3. Inventaire des seules métadonnées

Consultation le 13/11/2026, requêtes séquentielles :

- [Catalogue général, 1 069 entrées, une page complète](https://mapping.emergency.copernicus.eu/activations/api/activations/?limit=2000),
  filtre local exact `countries[].short_name == Madagascar` : **12 activations**,
  toutes EMSR. Le paramètre `search=Madagascar` testé auparavant n'a pas filtré
  le résultat ; il n'a pas servi à établir l'exhaustivité.
- [Catalogue Rapid Mapping](https://rapidmapping.emergency.copernicus.eu/backend/dashboard-api/public-activations-info/?limit=1000) :
  268 entrées, sans page suivante, mais seulement Fytia et Gezani pour Madagascar.
  Il ne suffit donc pas pour l'historique. Détails récents par
  `public-activations/?code=EMSR863` et `?code=EMSR867` sur le même serveur.
  La même requête pour EMSR197 renvoie une liste vide.
- Pour les cas anciens, pages d'activation liées dans le tableau : uniquement
  texte descriptif et noms des onglets AOI, sans images, cartes ou archives.
  Le catalogue STAC documenté répond 403 sans authentification ; aucun
  contournement ni accès aux produits n'a été tenté.

Les champs sont décrits par la [documentation du catalogue](https://mapping.emergency.copernicus.eu/about/how-to-harvest-cems-mapping-data/)
et la [documentation des métadonnées d'acquisition](https://mapping.emergency.copernicus.eu/about/how-to-harvest-cems-mapping-data/emergency-response-data/).
Seuls `eventTime`, `activationTime`, noms d'AOI et dates des images `new=true`
ont été exploités dans les réponses détaillées ; ni statistiques d'impacts,
ni géométries, ni couches. **Date d'activation, date d'événement, date de livraison
et date d'acquisition ne sont pas interchangeables.**

Convention : saison s = novembre s à avril s+1 ; réanalyse collectée du
25/11/s au 05/04/s+1, s = 2003…2016. « Oui » indique seulement un chevauchement
calendaire ; aucune disponibilité spatiale ou journalière n'est déduite sans
lecture des données. Dates ci-dessous en calendrier UTC des sources.
**NR** = non renseigné dans les métadonnées accessibles consultées, pas absence
d'acquisition. Les périodes IBTrACS de R-40 ne remplacent pas ces dates.

| Activation | Aléa / cyclone associé | Événement (source, précision) | Activation | Acquisition post-événement | Saison | Réanalyse / reprévisions dans les saisons 2003–2016 |
|---|---|---|---|---|---|---|
| [EMSR034](https://mapping.emergency.copernicus.eu/activations/EMSR034/) | Accident industriel ; aucun cyclone | NR ; mission à Toamasina | 04/04/2013 | NR | 2012–2013 selon activation, événement NR | Date d'activation dans la fenêtre ; exclu : aléa non hydrologique |
| [EMSR197](https://mapping.emergency.copernicus.eu/activations/EMSR197/) | Tempête / Enawo | 07/03/2017, atterrissage prévu dans le texte d'activation | 07/03/2017 | NR | 2016–2017 | Oui / mars 2017 présent dans l'inventaire documentaire ; exploitabilité EMS non établie |
| [EMSR264](https://mapping.emergency.copernicus.eu/activations/EMSR264/) | Tempête / Ava | 05/01/2018, atterrissage décrit | 06/01/2018 | NR | 2017–2018 | Non / hors période ; janvier 2018 existe séparément |
| [EMSR274](https://mapping.emergency.copernicus.eu/activations/EMSR274/) | Tempête / Eliakim | Mars 2018 ; jour non précisé sur la page d'activation | 16/03/2018 | NR | 2017–2018 | Non / hors période ; mars absent de l'inventaire de cette saison |
| [EMSR424](https://mapping.emergency.copernicus.eu/activations/EMSR424/) | Inondation et glissement / « Diane » dans le dépôt, perturbation tropicale non nommée dans la page EMS | Janvier 2020 ; jour NR | 30/01/2020 | NR | 2019–2020 | Non / hors période ; janvier 2020 existe séparément |
| [EMSR559](https://mapping.emergency.copernicus.eu/activations/EMSR559/) | Inondation / « Ana » dans le dépôt ; la page EMS décrit deux systèmes successifs | Janvier 2022 ; jour NR sur la page | 25/01/2022 | NR | 2021–2022 | Non / hors période, aucun mois de cette saison dans l'inventaire retenu |
| [EMSR564](https://mapping.emergency.copernicus.eu/activations/EMSR564/) | Tempête / Batsirai | 05/02/2022 attendu (samedi suivant l'activation), non date `eventTime` vérifiée | 04/02/2022 | NR | 2021–2022 | Non / hors période |
| [EMSR565](https://mapping.emergency.copernicus.eu/activations/EMSR565/) | Tempête / Emnati | 22/02/2022, atterrissage décrit | 23/02/2022 | NR | 2021–2022 | Non / hors période |
| [EMSR645](https://mapping.emergency.copernicus.eu/activations/EMSR645/) | Tempête / Cheneso | 19/01/2023 matin, atterrissage décrit | 25/01/2023 | NR | 2022–2023 | Non / hors période ; janvier 2023 existe séparément |
| [EMSR652](https://mapping.emergency.copernicus.eu/activations/EMSR652/) | Tempête / Freddy | 21/02/2023 attendu dans la page d'activation | 19/02/2023 | NR | 2022–2023 | Non / hors période ; février absent de l'inventaire de cette saison |
| [EMSR863](https://mapping.emergency.copernicus.eu/activations/EMSR863/) | Tempête / Fytia | 30/01/2026 23:00 (`eventTime`) | 02/02/2026 | 03, 04, 09 et 17/02/2026 | 2025–2026 | Non / non |
| [EMSR867](https://mapping.emergency.copernicus.eu/activations/EMSR867/) | Tempête / Gezani | 10/02/2026 15:00 (`eventTime`) | 11/02/2026 | 14, 15, 16, 17, 18, 20 et 21/02/2026 | 2025–2026 | Non / non |

Les dates anciennes incomplètes sont une **limite réelle de cet inventaire** :
il ne permet pas d'aligner un score sur les acquisitions. Les compléter par
inspection des cartes violerait le périmètre fixé. Les listes de catalogue sont
exhaustives pour le filtre pays à la date de consultation, pas une preuve de
couverture exhaustive des crues de Madagascar. L'appellation Ana/Diane ne suffit
pas à attribuer toute l'inondation au seul cyclone nommé.

### Zones d'intérêt et produits annoncés

Les nombres sont ceux du catalogue général (AOI / produits) ; la liste textuelle
est celle des onglets présents sur les pages historiques ou des AOI de l'API
détaillée récente. Un onglet ou une AOI demandée ne garantit pas une observation
utilisable. Les divergences sont conservées plutôt que résolues par inspection
des cartes.

| Code | AOI / produits | Noms des AOI visibles dans les métadonnées |
|---|---:|---|
| EMSR034 | 1 / 4 | Toamasina |
| EMSR197 | 23 / 14 | Maroantsetra (01 et 07), Vangaindrano North, Vangaindrano, Sambava, Antalaha, Ambodiadabo, Ratsianarana, Fampotabe, Anororo, Sambava Area, Antalaha Area, Moramanga, Iakora (14 onglets) |
| EMSR264 | 18 / 37 | Ambilope, Ambanja, Antsohihy, Boriziny, Marovoay, Mahambo, Ambatobe, Vatomandry, Mahanoro, Masomeloka, Nosy Varika, Farafangana, Ihorombe, Vangaindrano, Antananarivo, Miandrivazo, Belon'i_Tsiribihina, Miandrivazo Detail |
| EMSR274 | 22 / 21 | Ambilobe, Ambanja, Befotaka, Antsohihy, Toamasina, Brickaville, Vatomandry, Mahanoro, Nosy Varika, Mananjary, Vohimasina, Antalaha, Maroantsetra, Mahajanga, Fenerive, Mananara, Soanierana Ivongo, Lokintsy, Ambodifototra, NosyBe, Vavatenina (21 onglets) |
| EMSR424 | 5 / 10 | Mahajanga, Ambohitrarivo, Madirovalo, Maevatanana, Mampikony |
| EMSR559 | 4 / 8 | Ambatoboeny Marovoay, Amparafaravola, Antananarivo, Moramanga |
| EMSR564 | 8 / 9 | Tsiribihina, Fianarantsoa, Mananjary, Nosy Varika, Ambahi, Mananjary City, Manakara (7 onglets) |
| EMSR565 | 6 / 10 | Fianarantsoa, Namorona, Manakara, Vohipeno, Farafangana, Vangaindrano |
| EMSR645 | 10 / 25 | Ambatoboeny, Analaiva, Andapa, Belo sur Tsiribihina, Mahajanga, Mampikony, Mananjary, Maroantsetra, Morombe, Maintirano |
| EMSR652 | 6 / 11 | Mahanoro, Nosyvarika, Mananjary, Ambohitsara, Manakara (5 onglets) |
| EMSR863 | 20 / 6 | API détaillée : Vatomandry, Manakambahiny, Amboditavolo, Maroleo, Village de Baly, Ambato Boeny (6 AOI ; le catalogue récent en annonce 6 aussi) |
| EMSR867 | 8 / 11 | Toamasina, Mahavelona, Ambatondrazaka, Antananarivo, Brickaville, Moramanga, Toamasina North West, Toamasina South West |

Acquisitions récentes par AOI (UTC, dates ; précision horaire disponible dans
l'API) : Fytia — Vatomandry 04/02, Manakambahiny et Amboditavolo 03/02,
Village de Baly 17/02, Ambato Boeny 09/02, Maroleo NR. Gezani — Toamasina
15 et 20/02, Mahavelona 15/02, Ambatondrazaka 14 et 16/02, Antananarivo 18/02,
Brickaville 17/02, Toamasina North West et South West 20 et 21/02, Moramanga NR.
L'absence de date dans une AOI n'est pas codée comme une absence d'eau.

### Effectifs indépendants et chevauchement

- Catalogue hydrométéorologique maximal : **11 activations dans 6 saisons**
  (2016, 2017, 2019, 2021, 2022, 2025). C'est au plus onze groupes événementiels,
  pas onze événements indépendants garantis : Ana précède Batsirai et Emnati,
  Fytia précède Gezani, et EMSR559 englobe plusieurs systèmes.
- Corpus R-02 bis/R-40 : **7 activations dans 4 saisons** (2017, 2019, 2021, 2022).
- Trois candidats du §8 de R-21 bis : **3 événements dans 3 saisons**, tous hors
  de la réanalyse collectée. Existence de certains mois de reprévision ≠ support
  commun avec cette réanalyse. Références :
  `validation/r21_couverture_seuils.md:7`, `:20`, `:21`, `:23`, `:25` ;
  `validation/protocole_r21_diagnostic.md:95`. Les compléments de collecte du
  11/11 consignés dans `coordination/chantiers/r21.md` concernent 2007–2016,
  pas de nouveaux mois des trois candidats.
- Support réanalyse/reprévisions des **saisons 2003–2016** : au plus **1 événement
  hydrométéorologique, 1 saison**, Enawo en mars 2017. Ne pas l'exclure au seul
  motif que l'année civile est 2017. Mars 2017 figure en saison 2016 dans
  `validation/r21_couverture_seuils.md:20` ; son format EMS avait déjà été écarté
  (`validation/README.md:18`). Sans vérifier les produits, **zéro événement
  indépendant et exploitable n'est certifié**. EMSR034 ne fournit pas un second
  événement de crue.

## 4. Puissance théorique

Calcul exact effectué localement après rédaction de la section 1, avec la
bibliothèque standard Python (`math.comb`) ; aucune donnée scientifique en
entrée. n est le nombre de saisons indépendantes supposées, sauf les deux
lignes explicitement optimistes par événement.

| Scénario | n | Succès requis k | Taille effective sous p=0,5 | Puissance sous p=0,8 |
|---|---:|---:|---:|---:|
| Échantillon indépendant/exploitable certifié sur le support actuel | 0 | Rejet impossible | 0 % | 0 % |
| Enawo supposé exploitable et indépendant | 1 | Rejet impossible | 0 % | 0 % |
| Ava, Diane, Cheneso, même en supposant la réanalyse étendue | 3 | Rejet impossible | 0 % | 0 % |
| Sept cas R-40 regroupés par saison | 4 | Rejet impossible | 0 % | 0 % |
| Tous les cas hydrométéorologiques, regroupés par saison | 6 | 6 | 1,5625 % | **26,2144 %** |
| Sept événements R-40 supposés indépendants (optimiste, non retenu) | 7 | 7 | 0,78125 % | 20,9715 % |
| Onze événements supposés indépendants (optimiste, non retenu) | 11 | 9 | 3,2715 % | 61,7402 % |
| Repère de dimensionnement | 16 | 12 | 3,8406 % | 79,8245 % |
| Premier n atteignant 80 % pour ce test | **18** | **13** | **4,8126 %** | **86,7084 %** |

La puissance exacte peut baisser quand n augmente d'une unité, parce que k
augmente par paliers : 18 est le premier effectif admissible, pas une promesse
que tous les effectifs supérieurs ont la même puissance. Sensibilité de l'effet
(test inchangé) : premier n atteignant 80 % = 37 pour p=0,70, 18 pour p=0,80,
8 pour p=0,90. Même six saisons indépendantes toutes favorables n'offrent que
0,90^6 = 53,14 % de puissance sous cette dernière hypothèse très forte.

Reproduction sans aucun fichier de données :

```python
from math import comb

def queue(n, k, p):
    return sum(comb(n, j) * p**j * (1-p)**(n-j)
               for j in range(k, n+1))

def puissance(n, p=0.8):
    k = next((k for k in range(n+1) if queue(n, k, 0.5) <= 0.05), n+1)
    return k, queue(n, k, 0.5), queue(n, k, p)

for n in (0, 1, 3, 4, 6, 7, 11, 16, 18):
    print(n, puissance(n))
assert puissance(4)[2] == 0
assert abs(puissance(7)[2] - 0.8**7) < 1e-12
assert next(n for n in range(1, 101) if puissance(n)[2] >= 0.8) == 18
```

Ces résultats sont propres au critère proposé et aux hypothèses annoncées,
pas une borne universelle sur tous les tests possibles. Ils ne sont ni une
puissance observée a posteriori ni une preuve d'absence de compétence GloFAS.
Changer le critère après avoir vu cette puissance pour obtenir artificiellement
80 % ne créerait pas un échantillon indépendant. La condition d'indépendance
échoue d'ailleurs séparément, quel que soit ce choix.

## 5. Décision

**NON FAISABLE dans le périmètre autorisé.** Les deux conditions cumulatives
du porteur ne sont pas satisfaites :

1. L'indépendance du test vis-à-vis du développement n'est pas garantie ; des
   usages directs antérieurs, dont GloFAS–EMS, sont documentés. Les six saisons
   du catalogue sont au mieux des grappes supposées indépendantes, pas un jeu
   confirmatoire réservé et audité.
2. La puissance pour l'effet proposé est inférieure à 80 %, même avec les
   six saisons et sans aucune perte technique (26,2 %). Le support collecté
   2003–2016 ne contient au plus qu'une saison candidate, avec puissance nulle
   pour le test exact retenu. Les trois cas cités dans R-21 bis sont hors de
   cette réanalyse et restent insuffisants même dans un scénario d'extension.

**Application de la décision du 13/11 à 08:00 : option 3, clôture et apport de
méthode, sans prolongation exploratoire.** Cette note est soumise à relecture ;
elle n'autorise ni collecte complémentaire, ni réparation des archives EMS,
ni calcul d'AUC, ni réglage, ni nouveau score. Les dates d'acquisition anciennes
manquantes et les divergences d'AOI sont signalées ; aucune n'est comblée par
une supposition favorable. La relecture doit notamment contrôler la distinction
année civile/saison, l'exposition passée et la pertinence du critère proposé.

## 6. Vérifications et transmission

- `.venv/Scripts/python.exe tests/test_r21_diagnostic.py` : **24 tests réussis**,
  exclusivement synthétiques ; aucun calcul D1–D4 sur les données du projet.
- Bloc Python de la section 4 exécuté indépendamment et assertions réussies ;
  références de fichiers et numéros de lignes contrôlés, corrections des repères
  de saisons effectuées ; UTF-8 et `git diff --check` contrôlés.
- À relire puis à commiter par Claude : cette note, `COORDINATION.md` et
  `coordination/chantiers/r21.md`. Exécution cochée, reprise locale mise à jour.
  Aucun commit ou push effectué par Codex.
