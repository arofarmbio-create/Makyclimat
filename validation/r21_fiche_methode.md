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
- **Détection** d'un épisode par une méthode : une alerte (fenêtre 1-3 jours) dans au moins un district de
  l'épisode, sur une initialisation de 1 à 3 jours avant l'une de ses dates.
- **Effectifs** : 15 épisodes dans 7 saisons avec les mois publiés ; **25 épisodes dans 12 saisons** si l'on ajoute
  7 mois (mars 2007, mars 2008, février 2011, mars 2014, février et mars 2015, février 2016).
- **Témoins** : jours-districts des mois publiés sans fiche, hors janvier-mars 2019 (aucune fiche datée dans
  l'export) et hors saison 2017-2018 (fiches exclues pour date douteuse). Une absence de fiche n'est pas une absence
  d'impact : les alertes sur témoins sont des « alertes sans impact confirmé ».
- Reste à produire (étape suivante) : la table saison × mois × district qui fige cette population.

## 4. Charge comparable

Unité : épisodes d'alerte pour 100 jours-districts témoins observés. Une alerte commence au premier jour de
dépassement et se termine après 3 jours sans dépassement ; chaque initialisation couvre les jours de sa fenêtre
1-3 jours. Mêmes jours-districts pour les deux méthodes. Sur les saisons d'apprentissage de chaque pli, on fixe la
charge cible égale à celle du contrôle au seuil de la section 2, puis on choisit pour l'ensemble le seuil de
probabilité (pas de 0,02) dont la charge est la plus proche de la cible, avec un écart toléré de ± 20 %. Si la cible est
inaccessible, le pli est signalé et le résultat présenté comme exploratoire. La charge réellement obtenue sur la saison
testée est publiée.

## 5. Test et puissance

Résultat binaire par épisode et par méthode ; test apparié exact de McNemar unilatéral (ensemble meilleur),
α = 0,05, sur les épisodes discordants. Sensibilité : permutation des signes par saison (saison = bloc).

| Épisodes (saisons) | Gain de 20 points | Gain de 30 points | Gain de 40 points |
|---|---:|---:|---:|
| 15 (7), mois publiés | 19 % | 41 % | 62 % |
| 25 (12), avec 7 mois de plus | 43 % | 72 % | 89 % |

Puissance pour p(contrôle seul) = 0,05, sans corrélation intra-saison ; ρ = 0,1 à 0,3 change peu ces valeurs (voir le
[détail](r21_puissance.md)). **Avec les mois publiés, H1 ne peut être que exploratoire.** Avec 7 mois de plus, un test
confirmatoire n'atteint 80 % que pour un gain d'environ 35 à 40 points.

## 6. Décisions demandées au porteur du projet

1. **Gain de détection jugé pertinent**, fixé avant les scores. Proposition : 30 points.
2. **Télécharger les 7 mois** de la section 3 (Copernicus, un mois par job, file unique). Coût : 7 jobs, quelques heures
   au total d'après les derniers mois. Gain : 10 épisodes et 5 saisons. Sans ce lot, H1 est déclaré exploratoire.
3. Statut final : confirmatoire seulement si l'effectif obtenu donne au moins 80 % de puissance au gain retenu ;
   sinon exploratoire, avec intervalles de confiance.
