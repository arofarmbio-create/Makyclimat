# Protocole M3 : les indices de sécheresse et de recharge du système suivent-ils les niveaux de nappe mesurés dans le Grand Sud ?

*Rédigé le 02/11/2026, **avant** tout calcul sur les séries. Seul un résumé descriptif (dates, nombre de mesures,
médianes) a été produit au téléchargement pour vérifier les fichiers. Protocole doctoral : module M3, hypothèses H3 et
H6, risque 7 (données hydrogéologiques insuffisantes). Prompt maître §6C et §13. Toute modification sera datée en
section 9, avant de voir les résultats concernés.*

## 1. Question

Le système publie un indice de recharge (`recharge12_z`, bilan de Thornthwaite-Mather) et des SPI. Jusqu'ici, aucun n'a
été comparé à un niveau de nappe mesuré : le registre classe le module « non validé » (R-18, R-19). Les séries de
dataloggers publiées par MGMERL permettent pour la première fois cette comparaison.

1. Le SPI suit-il les variations du niveau des nappes, et sur quelle durée de cumul (n mois) ?
2. L'indice de recharge du système fait-il mieux que le SPI de même durée ?
3. La salinité (conductivité) augmente-t-elle quand le niveau baisse ?
4. Compter l'évaporation aide-t-il à suivre les nappes, et laquelle ? Le protocole doctoral (E2-B) demande de
   distinguer l'**évapotranspiration de référence** (ET0, FAO-56 Penman-Monteith : la demande de l'atmosphère sur un
   gazon bien arrosé) de l'**évapotranspiration réelle** (ETR : ce qui s'évapore vraiment, limité par l'eau du sol).

## 2. Positionnement (recherche du 02/11/2026)

- Bloomfield et Marchant (2013, *HESS* 17, 4769) : indice standardisé de niveau de nappe (SGI), comparé au SPI ; la
  durée de cumul la mieux corrélée dépend de l'aquifère.
- Kumar et al. (2016), plus de 2 000 puits en Allemagne et aux Pays-Bas : une durée de cumul unique pour toute une
  région dégrade nettement la corrélation SPI-SGI.
- Sud-ouest de Madagascar : un observatoire suit 16 forages heure par heure depuis 2014 et estime la recharge par la
  méthode de fluctuation de nappe (communication EGU 2025, HAL hal-05208015). Il ne relie pas ces niveaux aux indices
  de sécheresse d'un système d'alerte.
- **Ce que ce chapitre ajoute :** la première comparaison, à Madagascar, entre les indices de sécheresse et de recharge
  d'un système d'alerte et des niveaux mesurés dans le Grand Sud (Androy, Anosy, Atsimo-Andrefana, Atsimo-Atsinanana),
  sur une période qui couvre la sécheresse de 2020-2022.

## 3. Données

| Donnée | Source | Détail |
|---|---|---|
| Niveau de nappe et conductivité | **MGMERL**, dataloggers HT Analytics (dossier partagé, version du 17/06/2025) | 16 sites, une mesure toutes les 4 heures environ, 2019-2025 selon les sites |
| Coordonnées des sites | MGMERL, onglet « St. Piézométriques » | — |
| Pluie mensuelle | CHIRPS v2.0, maille de 0,05° du site | 1981 à aujourd'hui |
| Indice de recharge | Bilan du système (`soilwater_core.run_balance`), recalculé à la maille du site sur toute la période | Mêmes réserve utile, CN et ET0 qu'en production |
| Type d'aquifère | Carte hydrogéologique BGS (déjà utilisée par le système) | Pour l'analyse descriptive |

Attribution obligatoire : « Données de niveaux de nappe : MGMERL (HT Analytics, UNICEF) ». Les fichiers bruts sont
gardés hors du dépôt git (`data/mdg/mgmerl_raw/`). Seuls des résultats agrégés par site sont publiés.

## 4. Contrôle qualité (règles fixées à l'avance)

Le résumé du téléchargement montre des défauts de capteur : niveaux positifs, saut à −37 m, conductivité à 0. Règles :

1. Le niveau est une profondeur négative. Une valeur **> 0 m ou < −60 m** est manquante.
2. Pic isolé : écart à la médiane glissante sur 7 jours **> 2 m**, valeur manquante.
3. Saut durable (capteur déplacé) : la médiane journalière change de **plus de 3 m** d'un jour à l'autre et le
   nouveau niveau dure au moins 7 jours. La série est coupée à cet endroit, et seul le plus long segment est gardé.
4. Conductivité **≤ 0 ou > 20 mS/cm** : manquante.
5. Moyenne mensuelle calculée si le mois a au moins **10 jours** de mesures valides.
6. Un site est retenu s'il a au moins **24 mois valides**.

Tout ce qui est retiré est compté et publié par site.

## 5. Indices

- **Anomalie de niveau (critère principal) :** niveau mensuel moins la moyenne du même mois du calendrier sur la
  période du site. Elle retire le cycle saisonnier, qui sinon dominerait toute corrélation. Écart assumé à Bloomfield
  et Marchant, qui standardisent par mois du calendrier sur des séries de plusieurs décennies : nos séries durent de
  2 à 6 ans.
- **SGI simplifié (secondaire) :** scores normaux du niveau mensuel brut, cycle saisonnier compris.
- **SPI-n**, n = 1 à 24 mois : loi gamma par mois du calendrier sur 1981-2025 (fonction existante `soilwater_core.spi`).
- **`recharge12_z`** : excédent hydrique cumulé sur 12 mois, en scores normaux, recalculé comme en production
  (corrigé le 02/11/2026, section 9).
- **Trois façons de compter l'évaporation** (ajout du 02/11/2026, section 9) :
  - aucune : SPI-n (pluie seule) ;
  - **référence** : SPEI-n (n = 3, 6, 12, 24) sur P − ET0, loi logistique généralisée (`soilwater_core.spei`) ;
  - **réelle** : `bilan12_z`, P − ETR cumulé sur 12 mois en scores normaux, l'ETR venant du bilan de
    Thornthwaite-Mather ; et `recharge12_z`, l'excédent qui s'infiltre une fois le sol rempli.
- Pour chaque site : pluie, ET0, ETR et recharge moyennes annuelles, et rapport ETR/ET0 sur les mois mesurés.

## 6. Mesures et hypothèses fixées à l'avance

Corrélation de Spearman entre l'indice du mois t et l'anomalie de niveau du mois t, par site.

- **H-N1 (principale)** : r(SPI-12) > 0 dans plus de la moitié des sites retenus. Test du signe unilatéral, 5 %.
  Le cumul de 12 mois est fixé à l'avance, car c'est celui de l'indice de recharge du système.
- **H-N2** : r(`recharge12_z`) > r(SPI-12) dans plus de la moitié des sites, même test. Une réponse négative
  confirmerait le résultat R-16 : le bilan hydrique simple n'apporte rien de plus que le SPI.
- **H-N3a** : r(SPEI-12) > r(SPI-12) dans plus de la moitié des sites (test du signe). Compter l'ET0 de référence
  améliore-t-il le suivi ?
- **H-N3b** : r(`bilan12_z`, P − ETR) > r(SPI-12), même test. Compter l'ETR réelle améliore-t-il le suivi ?
- **Descriptif (Q1)** : durée de cumul n* qui maximise r pour chaque site, rapprochée du type d'aquifère et de la
  profondeur médiane. On attend des n* différents d'un site à l'autre (Kumar et al. 2016).
- **Descriptif (Q3)** : r(conductivité, anomalie de niveau) par site. On attend r < 0 là où l'eau se concentre quand la
  nappe baisse.
- **Sécheresse 2020-2022** : pour les sites qui la couvrent, mois du niveau le plus bas comparé au mois du SPI-12 le
  plus bas (décalage en mois).

Puissance : avec une dizaine de sites, le test du signe n'est significatif à 5 % qu'à partir de 9 sites sur 10. Un
résultat non significatif sera publié comme tel, sans changer de seuil.

Aucun modèle n'est ajusté : il n'y a pas de fuite d'information entre apprentissage et test. Le seul choix lié aux
données (n*) est présenté comme descriptif, jamais comme une performance.

## 7. Limites connues

- **Pompage** : ces dataloggers sont posés sur des points d'eau exploités. Le niveau mesuré peut être un niveau
  dynamique, abaissé par le pompage, et pas un niveau statique. C'est la principale source de confusion possible : on
  la signale site par site quand le profil journalier montre des cycles de pompage.
- La référence de mesure (sol ou haut du tubage) n'est pas connue : seules les variations sont interprétées, pas les
  profondeurs absolues.
- Séries courtes (2 à 6 ans) : peu d'années par mois du calendrier.
- Comparaison d'un point avec une maille de pluie de 0,05°.
- L'indice de recharge et le SPEI utilisent une ET0 **climatologique** fixe (2016-2020) : ils ne voient pas les
  années plus chaudes que la normale. Une ET0 qui varie d'une année à l'autre viendra de la série ERA5-Land du
  chapitre SPEI-NDVI (R-24), dès qu'elle sera téléchargée ; le calcul sera alors refait et les deux versions publiées.
- L'ETR est modélisée, pas mesurée : aucune mesure d'évaporation (tour de flux, bac) n'existe dans le Grand Sud.

## 8. Mise en œuvre

- Calcul sur ce PC (décision du porteur du projet le 02/11/2026 : le calcul local est utilisé quand il est plus
  simple ; ici les fichiers sont déjà sur place et les calculs sont légers).
- Script : `scripts/validate_nappes_mgmerl.py`, avec des tests sur des données simulées, avant toute exécution sur les
  séries réelles.
- Résultats : `validation/nappes_mgmerl.md` et `validation/nappes_mgmerl_sites.csv`, puis registre et journal, que les
  résultats soient positifs ou négatifs.
- Mise à jour : les séries ne sont accessibles que par téléchargement manuel dans le dossier partagé MGMERL. C'est une
  exception documentée à la règle des mises à jour automatiques, comme pour les relevés de forage
  (`connector_watertable.py`).

## 9. Journal des modifications

- 02/11/2026 : version initiale.
- 02/11/2026, **avant tout calcul de corrélation** (les indices aux sites venaient d'être produits, les niveaux pas
  encore traités) : à la demande du porteur du projet, ajout de la distinction entre évapotranspiration de référence
  (ET0) et réelle (ETR) exigée par le protocole doctoral (E2-B). Nouvelles colonnes (et0_mm, etr_mm, recharge_mm,
  spei3/6/12/24, bilan12_z), nouvelle question 4 et hypothèses H-N3a et H-N3b. H-N1 et H-N2 sont inchangées.
- 02/11/2026, **avant tout calcul de corrélation** : en contrôlant les indices aux sites, la recharge s'est révélée
  nulle à tous les sites et pour tous les mois depuis 1981. Cause : depuis le 27/10, le bilan de production retirait
  un ruissellement SCS-CN calculé sur le cumul du mois. Or cette formule est faite pour une averse isolée : pour 600 mm
  dans le mois, elle compte 490 à 570 mm de ruissellement. En production, l'excédent valait 0 dans 99,6 % des
  fokontany, et `recharge12_z` était constant. **H-N2 aurait testé un indice dégénéré.** Corrigé en production et
  ici : le bilan ne retire plus de SCS-CN mensuel, et `recharge12_z` devient l'excédent hydrique standardisé (recharge
  potentielle et ruissellement confondus). H-N2 garde le même énoncé, avec cet indice corrigé. Le défaut est publié au
  journal de recherche comme un échec.
