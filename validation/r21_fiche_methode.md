# R-21 — Fiche de méthode avant puissance et avant scores (proposition de Claude, 11/11/2026)

Proposition soumise à la relecture de Codex et aux décisions du porteur du projet. Elle répond aux trois points de la
[relecture de Codex](../pilotage/etat/coordination/codex-r21-revue-fiche-20261110.md) et applique l'option 1 de la
[section 9 du protocole](protocole_verification_impact.md#9-journal-des-modifications-du-protocole). Le verrou des scores
est maintenu : aucun score n'a été calculé.

Pièces chiffrées : [couverture des seuils](r21_couverture_seuils.md) ([script](../scripts/r21_couverture_seuils.py)),
[puissance](r21_puissance.md) ([script](../scripts/r21_puissance.py)), [inventaire de Codex](inventaire_r21_avant_puissance.md).

## 1. Ce que montrent les fichiers (53 mois de la release, contrôlés le 11/11)

- **17 saisons** ont au moins un mois, mais leur contenu varie de 1 mois (2013, 2020, 2022) à 6 mois (2003-2005).
- **Couverture actuelle des seuils** : 91 % des 16 689 mailles éligibles ont un seuil, quelle que soit la saison
  testée. Le minimum de 15 saisons n'est donc pas le problème principal.
- **Biais de la règle actuelle**, qui prend le maximum sur les mois disponibles : sur les 4 saisons où décembre à mars
  sont complets, le maximum d'un seul mois vaut en médiane 23 % (déc.), 79 % (jan.), 72 % (fév.) et 47 % (mars) du
  maximum de décembre à mars. Les seuils sont donc tirés vers le bas, différemment selon la composition des saisons.
- **Janvier seul** (mêmes mois partout) : 14 saisons d'apprentissage au plus, sous le minimum de 15. Écarté.
- Sept copies locales étaient tronquées (téléchargements interrompus) ; elles ont été remplacées depuis la release
  avant le calcul.

## 2. Seuils proposés : blocs mensuels de décembre à mars

Chaque mois disponible de décembre à mars est un bloc ; seuil de Gumbel (moments) sur les maxima mensuels du contrôle,
par maille et fenêtre, sans la saison testée, au moins 30 blocs (40 à 43 disponibles). Couverture : 93 à 95 %.
Période de retour mensuelle T_m = 1 / (1 − 0,5^(1/4)) ≈ 6,3, équivalente à la crue de 2 ans sur décembre-mars si
les mois étaient indépendants. Réserves déclarées : persistance des débits d'un mois à l'autre, et maxima de décembre
plus faibles que ceux de janvier-février (blocs non identiquement distribués). Sensibilité : règle actuelle.

Pour H1, ce niveau est surtout un repère commun aux deux méthodes : la comparaison se fait à charge d'alerte égale
(section 4), ce qui recale le seuil de décision de chaque méthode sur les saisons d'apprentissage.

## 3. Population éligible et épisodes

- **Fiches** : filtres du script R-21 (cyclone ou inondation, date valide non douteuse, district rattaché, personnes
  touchées ou maisons endommagées ou détruites), décembre à mars, saisons 2003 à 2018.
- **Épisode** : dates de fiches regroupées tant que l'écart entre deux dates successives est de 3 jours au plus,
  tous districts confondus. Les districts et dates d'un même épisode ne comptent qu'une fois.
- **Unité d'analyse (version du 11/11 après-midi)** : l'épisode × district, conformément à la vérification
  « district par district » du protocole. Un district est détecté par une méthode si une alerte (fenêtre 1-3 jours)
  le concerne sur une initialisation de 1 à 3 jours avant l'une des dates de l'épisode.
- **Initialisations deux fois par semaine** (reprévisions v4) : une unité n'est éligible que si une initialisation
  publiée tombe 1 à 3 jours avant l'une de ses dates ; les initialisations du mois précédent comptent (frontières).
- **Effectifs figés** ([table](r21_eligibilite.md), [unités](r21_eligibilite.csv)) : 468 unités avec fiche dans
  25 épisodes ; **376 éligibles (20 épisodes, 11 saisons)** avec les mois locaux ; 28 unités (2 épisodes) sans
  initialisation utile ; 64 unités (3 épisodes) attendent février-mars 2015. **Projection : 440 unités, 23 épisodes,
  12 saisons.**
- **Témoins** : jours-districts des mois publiés sans fiche, hors janvier-mars 2019 (aucune fiche datée dans
  l'export) et hors saison 2017-2018 (fiches exclues pour date douteuse). Une absence de fiche n'est pas une absence
  d'impact : les alertes sur témoins sont des « alertes sans impact confirmé ».
- Table saison × mois avec districts témoins et jours-districts : [r21_eligibilite.md](r21_eligibilite.md).

## 4. Charge comparable

Unité : épisodes d'alerte pour 100 jours-districts témoins observés. Une alerte commence au premier jour de
dépassement et se termine après 3 jours sans dépassement ; chaque initialisation couvre les jours de sa fenêtre
1-3 jours. Mêmes jours-districts pour les deux méthodes. Sur les saisons d'apprentissage de chaque pli, on fixe la
charge cible égale à celle du contrôle au seuil de la section 2, puis on choisit pour l'ensemble le seuil de
probabilité (pas de 0,02) dont la charge est la plus proche de la cible, avec un écart toléré de ± 20 %. Si la cible est
inaccessible, le pli est signalé et le résultat présenté comme exploratoire. La charge réellement obtenue sur la saison
testée est publiée.

## 5. Test et puissance (2e version, après les relectures de Codex de 12:45, 13:25 et 13:28)

**Test principal (A)** : permutation exacte des signes par saison (2^S combinaisons) sur
T = Σ_s (b_s − c_s) / √n_s, où b_s et c_s comptent les districts détectés par l'ensemble seul et par le contrôle seul
dans la saison s. La saison est l'unité d'échange : la dépendance entre districts et épisodes d'une même saison est
respectée. Unilatéral, α = 0,05. **Test B** (McNemar par épisode, détecté si un district l'est) : écarté, car un
épisode de plusieurs dizaines de districts est presque toujours détecté par les deux méthodes ; puissance de 6 à 50 %.

Simulation, 3e version après les relectures de Codex de 13:52 et 13:55 ([détail](r21_puissance.md),
[projection](r21_puissance_projection.md), [script](../scripts/r21_puissance.py)), 4 000 simulations par case :
structure réelle des unités ; détection de chaque méthode simulée séparément (quatre issues) ; contrôle à 0,40 en
moyenne ; gain moyen recalé exactement à 30 points ; τ = écart type du gain entre saisons (0 à 0,2). La dépendance
est exprimée par la **CCI des différences** : corrélation intra-épisode, entre districts, de (détection ensemble −
détection contrôle). C'est la grandeur observable ; le paramètre de mélange r du simulateur n'en est qu'un moyen
(CCI ≈ r², plus l'hétérogénéité entre épisodes). Erreur de type I du test A : 4,0 à 5,5 % (± 0,7).

| CCI des différences (τ = 0 / 0,1 / 0,2) | 376 unités, 20 épisodes, 11 saisons | 440 unités, 23 épisodes, 12 saisons |
|---|---:|---:|
| 0,12 à 0,21 | 95 à 100 % | 96 à 100 % |
| 0,26 à 0,33 | 86 à 93 % | 89 à 96 % |
| 0,36 à 0,43 | 79 à 87 % | 84 à 91 % |
| 0,48 à 0,53 | 75 à 80 % | 79 à 84 % |
| 0,79 à 0,82 | 62 à 68 % | 67 à 71 % |

Erreur de Monte-Carlo : ± 1,5 point au plus (IC à 95 %).

**Lecture** (repères conservateurs, conditionnels aux hypothèses simulées : P_C, σ_C, κ, ω et forme de la
dépendance). Le seuil de CCI est dérivé dans [la puissance](r21_puissance.md#seuil-de-cci-pour-80--de-puissance-dérivation)
et [la projection](r21_puissance_projection.md#seuil-de-cci-pour-80--de-puissance-dérivation) : pour chaque τ,
interpolation linéaire entre les deux scénarios qui encadrent 80 %, sur la **borne basse à 95 % de Monte-Carlo** de la
puissance, puis plus petit seuil sur τ. Résultat : **CCI ≤ 0,40** avec la population actuelle, **CCI ≤ 0,49** avec la
projection (février-mars 2015 publiés). Ce sont des bornes prudentes, pas des limites franches : des scénarios
au-dessus atteignent encore 80 % (86,7 % à CCI 0,37 pour 376 unités ; 84,0 % à CCI 0,49 pour 440 unités), et
l'interpolation porte sur des scénarios espacés d'environ 0,1 de CCI.

**Estimation de la CCI avant tout score, sans information d'impact** : calculer les alertes des deux méthodes (seuils
de la section 2, charge comparable de la section 4) sur les **initialisations témoins**, c'est-à-dire sans fiche dans
les districts concernés. On appliquerait à ces jours les groupes de districts des épisodes réels et on ne retiendrait
que les jours-groupes où au moins une méthode alerte dans le groupe (situation d'activité comparable à un épisode). La
CCI des différences s'estime alors par ANOVA, avec un intervalle par bootstrap des saisons. Aucune unité d'impact n'est
lue : les résultats des épisodes réels restent cachés.

**Transportabilité non démontrée (relecture Codex du 11/11, 14:37).** Rien ne garantit que la CCI des jours témoins
soit celle des épisodes d'impact : un aléa fort commun à tout un épisode peut rapprocher les décisions des deux
méthodes dans les districts touchés, donc changer la corrélation des différences, et la sélection « au moins une
méthode alerte » ne reproduit qu'en partie cette situation. Le bootstrap mesure l'incertitude d'échantillonnage, pas
ce biais. En conséquence :

1. L'estimation sur témoins sert d'**analyse de sensibilité** : on publie, avant les scores, la CCI estimée, son
   intervalle et la puissance correspondante lue sur les tableaux (avec la borne haute de l'intervalle et avec cette
   borne augmentée de 0,10, soit un pas de la grille simulée).
2. Elle **n'attribue pas automatiquement** le statut confirmatoire. H1 reste exploratoire par défaut ; le porteur du
   projet décide, au vu de cette sensibilité et avant les scores, s'il retient le statut confirmatoire (section 6).
3. Après les scores, la CCI des différences observée sur les épisodes est calculée et publiée, avec la puissance
   qu'elle implique. Elle ne modifie pas le statut fixé avant les scores.

## 6. Décisions demandées au porteur du projet

1. **Gain de détection jugé pertinent**, fixé avant les scores. Proposition : 30 points.
2. **Télécharger les 7 mois** de la section 3 (Copernicus, un mois par job, file unique). Coût : 7 jobs, quelques heures
   au total d'après les derniers mois. Gain : 10 épisodes et 5 saisons. Sans ce lot, H1 est déclaré exploratoire.
3. Statut final, décidé avant les scores : exploratoire par défaut. Confirmatoire seulement si le porteur le retient au
   vu de l'analyse de sensibilité de la section 5 (CCI estimée sur témoins, puissance à sa borne haute et à cette
   borne + 0,10) ; dans tous les cas, intervalles de confiance publiés.

**Décisions du porteur du projet (11/11/2026, 11:19 Nairobi)** : (1) gain pertinent fixé à **30 points** ; (2) lot de
7 mois **autorisé**. Avec 25 épisodes, la puissance pour 30 points est de 72 % : selon le point 3, H1 restera
**exploratoire**. Collecte lancée par Claude en trois lots successifs (une seule file Copernicus) : mars 2007, 2008 et
2014 ([run 42987384953](https://github.com/arofarmbio-create/Makyclimat/actions/runs/42987384953)), puis février 2011
et 2016, puis février et mars 2015. Consigné au [protocole, section 9](protocole_verification_impact.md#9-journal-des-modifications-du-protocole).

**Mise à jour du 11/11/2026 après-midi** : le porteur du projet maintient l'objectif de 80 % (le statut exploratoire est
jugé insuffisant). Le passage à l'unité épisode × district avec inférence par saisons (section 5) le rend atteignable
si la CCI des différences ne dépasse pas 0,40 (population actuelle) ou 0,49 (avec 2015), repères conservateurs dérivés
en section 5 ; elle sera estimée sur les seules prévisions avant tout score, à titre de sensibilité (sa transportabilité
aux épisodes n'est pas démontrée) : le porteur tranche alors le statut avant les scores.
