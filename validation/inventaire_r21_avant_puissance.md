# R‑21 — Inventaire avant l’analyse de puissance

10 novembre 2026. Inventaire préparatoire au critère H1 de la [section 9 du protocole](protocole_verification_impact.md#9-journal-des-modifications-du-protocole).

Croisement des 50 fichiers mensuels de la [release GloFAS](https://github.com/arofarmbio-create/Makyclimat/releases/tag/reprevisions-glofas-v4) avec l’export DesInventar local. Les filtres reproduisent les conditions d’impact du script R‑21 pour les dates valides, les dates signalées comme douteuses, le district rapproché et la présence de personnes touchées ou de dommages aux maisons. Les chiffres comptent les fiches avant l’éclatement des districts et l’appariement aux initialisations GloFAS. Une saison porte l’année de son début en novembre.

| Saison | Mois publiés de novembre à avril | Mois avec fiches filtrées | Fiches | Dates distinctes |
|---|---|---|---:|---:|
| 2003 | nov.–avr. | jan. 2004 (36), mars (75), avr. (1) | 112 | 3 |
| 2004 | nov.–avr. | mars 2005 (4) | 4 | 3 |
| 2005 | nov.–avr. | — | 0 | 0 |
| 2006 | nov., jan.–fév. | — | 0 | 0 |
| 2007 | jan.–fév. | fév. 2008 (52) | 52 | 2 |
| 2008 | jan.–fév. | — | 0 | 0 |
| 2009 | jan. | — | 0 | 0 |
| 2010 | déc., jan. | — | 0 | 0 |
| 2011 | jan.–mars | fév. 2012 (54) | 54 | 2 |
| 2012 | déc.–mars | déc. 2012 (1), jan. 2013 (12), fév. (10) | 23 | 4 |
| 2013 | déc. | — | 0 | 0 |
| 2016 | jan.–mars | mars 2017 (46) | 46 | 2 |
| 2017 | déc., jan. | — | 0 | 0 |
| 2018 | jan.–mars | — | 0 | 0 |

Le rapprochement par mois donne **291 fiches réparties sur 16 dates et 6 saisons avec des fiches** parmi les mois publiés de la période de vérification. Les deux mois manquants apporteraient **24 fiches sur deux dates**, toutes dans la saison 2009. Ce sont des candidats pour l’appariement. Les dates, les fiches et les districts d’un même événement peuvent relever du même épisode. Seules 64 fiches des mois publiés portent un GLIDE, ce qui impose de documenter le rapprochement des autres fiches avec les événements connus.

La présence d’un mois GloFAS permet de préparer le rapprochement. La couverture des déclarations reste à documenter séparément avant d’utiliser un mois sans fiche comme témoin. En particulier, janvier à mars 2019 ne compte aucune fiche de cyclone ou d’inondation datée dans l’export. Il faut aussi contrôler les fenêtres à cheval sur deux mois.

Sur les 44 mois publiés de la période de vérification, 20 ont au moins une fiche datée non signalée comme douteuse, tous types confondus. Onze ont une fiche de cyclone ou d’inondation rattachée à un district et dix ont une fiche qui franchit aussi le filtre de dommages. Février 2009 est le seul mois où des fiches de cyclone ou d’inondation sont rattachées à un district et où aucune ne franchit ce filtre. L’export ne contient aucune fiche datée, tous types confondus, de janvier à mars 2019. Ces traces de déclaration sont des indices de couverture à approfondir au niveau des jours et des districts.

Le rapprochement préliminaire des dates avec le [catalogue des événements](evenements.csv) associe sans écart de date les 36 fiches du 26 janvier 2004 à la période d’Elita et les 75 fiches du 7 mars 2004 à celle de Gafilo. Pour Haruna, le GLIDE correspond à celui du lien du catalogue et les dates diffèrent de trois jours. Pour Hubert, le numéro et le pays du GLIDE concordent, le préfixe diffère et les dates sont espacées d’un jour. Les 46 fiches des 15 et 16 mars 2017 se situent après la fin de la période d’Enawo indiquée dans le catalogue. Vérifier la nature de ces dates avant de regrouper les fiches ou de fixer une tolérance commune.

Les fichiers publiés couvrent **16 saisons potentielles pour les seuils** de novembre 2003 à avril 2023, d’après les noms des fichiers. Le code exige au moins 15 saisons d’apprentissage par maille et par fenêtre. Quand on retire une saison testée, il reste au plus 15 saisons actuellement. Une seule saison manquante à une maille ou à une fenêtre peut donc rendre son seuil indisponible. Les deux mois 2010 complètent une saison déjà présente et les fichiers 2022–2023 pourraient ajouter des saisons. La vérification suivante doit mesurer la couverture effective des seuils et des paires contrôle–ensemble à partir des fichiers, avant les scores.

Contrôle partiel sur les saisons dont tous les fichiers de cette release étaient déjà copiés localement (2003 à 2007 et 2013). Pour les saisons testées 2003, 2004 et 2007, au plus **15 647 mailles** par fenêtre satisfont la condition de présence dans toutes les saisons d’apprentissage déjà lues, sur respectivement 20 034, 18 910 et 19 043 mailles observées et rattachées à un district. Cette borne de 78 à 83 % vaut pour la release de 50 fichiers. Les autres saisons peuvent réduire le décompte effectif, et une nouvelle livraison peut modifier le nombre de saisons disponibles.

Pour l’analyse de puissance, regrouper les épisodes entre districts et établir le nombre de saisons utilisables après appariement. La marge de charge et le gain de détection pertinent seront fixés avant les scores. Le calcul des scores reste verrouillé.
