# Protocole E1 : la fusion contrôlée de plusieurs sources de pluie améliore-t-elle l'analyse à Madagascar ?

*Rédigé le 02/11/2026, **avant** tout téléchargement et tout calcul. Protocole doctoral : expérience E1 (§10),
hypothèses H1 et H3 (§5), module M0 (§6), validation temporelle (§11), indicateurs (§12). Prompt maître §4, §8, §13.
Toute modification sera datée et justifiée en section 9, avant de voir les résultats concernés.*

## 1. Question

La pluie est l'entrée de presque tous les modules (sécheresse, crues, scénarios). Aujourd'hui le système n'utilise
qu'une source, CHIRPS. On compare trois façons de construire la pluie :

- **A** : chaque source seule ;
- **B** : la moyenne simple des sources, sans harmonisation ;
- **C** : les sources contrôlées, ramenées sur une grille commune, puis fusionnées avec des poids fondés sur leur
  erreur estimée.

Questions :
1. C est-elle plus juste que la meilleure source seule, et que B ?
2. Où et quand chaque source se trompe-t-elle (relief, côtes, Sud sec, saison) ?
3. Le choix de la pluie change-t-il la détection des impacts observés (inondations, sécheresse) ?

## 2. Positionnement (recherche bibliographique du 02/11/2026)

- **Ollivier et al. (2023)**, *Journal of Hydrology: Regional Studies* 47, 101400 : 21 produits comparés à
  24 pluviomètres au pas **mensuel** ; produits les plus justes au niveau national : WFDEI, CMORPH-BLD et MSWEP ;
  forts écarts entre régions bioclimatiques ; une moyenne pondérée des 21 produits fait mieux que chacun.
  Réseau national d'environ 30 stations.
- **Randriatsara et al. (2022)**, *International Journal of Climatology* (doi:10.1002/joc.7628) : 15 jeux de données,
  1983-2015, échelles annuelle et saisonnière. CHIRPS a les biais les plus faibles ; selon les auteurs, un classement
  unique n'a pas de sens.
- Ramahaimandimby et al. (2022), *Remote Sensing* 14, 3940 : 6 produits contre 14 pluviomètres sur 2 ans
  (bassin de l'Ankavia).
- Triple collocation de la pluie : appliquée en Australie, en Iran, en Inde et sur l'Afrique entière ; **aucune
  application trouvée pour Madagascar**.

Ce qui est déjà établi : au pas mensuel et sur les stations, fusionner aide. **Ce que E1 ajoute :**
1. **Une échelle plus fine** (pentades de 5 jours, puis jour), celle des alertes, au lieu du mois.
2. **Une erreur estimée partout, sans pluviomètre**, par triple collocation, au lieu des seuls 24 points de mesure.
3. **Une évaluation par les impacts** (inondations cartographiées, fiches de catastrophes, sécheresse documentée),
   jamais faite pour le choix de la pluie à Madagascar.
4. **Uniquement des sources disponibles en temps quasi réel.** WFDEI s'arrête en 2016 et MSWEP est sous licence :
   ils ne peuvent pas alimenter un système qui tourne chaque jour. Ce choix respecte aussi la règle « aucune fuite
   temporelle » (protocole E4) : la fusion n'utilise que ce qui aurait été disponible au moment voulu.

## 3. Données

| Source | Nature | Résolution native | Période | Lien avec les stations |
|---|---|---|---|---|
| CHIRPS v2.0 journalier (CHC, UCSB) | Satellite infrarouge et pluviomètres | 0,05° | 1981 à aujourd'hui | Intègre des stations du réseau mondial (GTS) |
| IMERG V07 Late journalier (NASA, GPM_3IMERGDL) | Satellite micro-ondes et infrarouge | 0,1° | depuis juin 2000 | **Aucun** recalage sur pluviomètres (contrairement à la version Final) |
| ERA5-Land (Copernicus) | Réanalyse (modèle) | 0,1° | depuis 1950 | Aucune assimilation de pluviomètres |
| GSOD (NOAA NCEI) | Stations synoptiques | point | variable | 25 stations malgaches actives depuis 2020 dans l'inventaire (02/11/2026) |

Période commune : **2001-2025**.

Références de stations à rechercher en parallèle, intégrées dès qu'elles sont obtenues (section 9) :
- séries de la Direction générale de la météorologie (démarche en cours du porteur du projet) ;
- stations météorologiques MGMERL, signalées par le porteur du projet le 02/11/2026 ;
- les 24 pluviomètres d'Ollivier et al. (2023), à demander aux auteurs (IRD, INRAE).

Grille commune : 0,1°, alignée sur IMERG (centres à −179,95 + 0,1 i), emprise de Madagascar (43 à 51°E, 26 à 11,5°S).
- CHIRPS : moyenne des 4 mailles de 0,05° contenues dans chaque maille de 0,1°.
- ERA5-Land : ses centres tombent sur les bords des mailles IMERG ; moyenne des 4 mailles voisines, poids 1/4 chacune.
  Cela lisse légèrement ERA5-Land, ce qui est documenté.
- Aucune grille n'est rééchantillonnée plus finement que sa résolution native.

Jour : ERA5-Land, valeur cumulée à 00 h UTC du jour J+1, soit le total du jour J en UTC. IMERG : jour UTC. CHIRPS et
les stations n'ont pas exactement la même journée. C'est la raison du choix de la **pentade** comme échelle principale
(section 5).

## 4. Contrôle qualité (part « harmonisée » de C)

Règles fixées à l'avance, appliquées pareillement à toutes les sources :
- valeur négative ou absente : manquante ;
- pluie journalière > 1 000 mm : manquante (au-dessus du record mondial, donc une erreur) ;
- stations GSOD : seuls les jours dont le cumul couvre **toute la journée** sont gardés : drapeaux **D** (4 relevés
  de 6 heures), **F** (2 relevés de 12 heures) et **G** (1 relevé de 24 heures). Les drapeaux A, B, C et E (cumuls
  partiels de 6 ou 12 heures), H (donnée incomplète) et I (« aucune pluie déclarée ») sont traités comme manquants,
  jamais comme zéro (modification du 02/11/2026, section 9). Le test du 02/11 montre que ce drapeau
  couvre jusqu'à 60 % des jours d'une station (Ivato, 2015) : le compter comme zéro fausserait la référence ;
- une pentade de station est gardée si ses 5 jours sont valides ; une station est gardée si elle a au moins
  100 pentades valides dans la période de test ;
- les taux de données manquantes par source, maille et année sont publiés (mesure demandée par le protocole E1).

## 5. Méthodes

**Échelle principale fixée à l'avance : la pentade (cumul de 5 jours).** Le jour et le mois sont des analyses
secondaires.

**Découpage temporel (protocole §11) :** apprentissage 2001-2015 (poids de C, choix de la meilleure source seule) ;
**test 2016-2025**, jamais utilisé pour rien régler.

**Triple collocation (TC) :** CHIRPS, IMERG Late et ERA5-Land, par maille, sur les pentades de la saison des pluies
(novembre à avril) de la période d'apprentissage. Forme étendue (McColl et al. 2014) : variance d'erreur de chaque
source et corrélation avec la pluie vraie inconnue. Hypothèses : erreurs indépendantes entre sources et
indépendantes du signal. CHIRPS et IMERG Late partagent une partie de l'infrarouge géostationnaire : ce lien
possible est une limite (section 7).

**Fusion C :**
1. Chaque source est ramenée à la moyenne et à l'écart-type de CHIRPS sur la période d'apprentissage, par maille et
   par mois du calendrier.
2. Moyenne pondérée par l'inverse de la variance d'erreur estimée par TC.
3. Si une source manque un jour, les poids des autres sont renormalisés.
4. Une maille où la TC donne une variance négative ou non définie reçoit des poids égaux, et elle est comptée.

**B :** moyenne simple des trois sources brutes.

**Meilleure source seule :** celle qui a la plus faible erreur TC médiane sur la période d'apprentissage, choisie
avant le test.

## 6. Mesures et hypothèses fixées à l'avance

### 6.1 Contre les stations (période de test, pentades)
Mesures : KGE (critère principal), MAE, RMSE, biais moyen, corrélation, comparaison maille et station.

- **H1-E1 (principale)** : KGE(C) > KGE(meilleure source seule) dans plus de la moitié des stations retenues.
  Test du signe unilatéral, seuil de 5 %.
- **H1-E1b** : KGE(C) > KGE(B), même test.
- La comparaison d'un point à une maille de 0,1° pénalise toutes les sources de la même façon : on compare les
  sources entre elles, on ne lit pas le KGE comme une vérité absolue.

### 6.2 Partout, sans station
- Cartes de la variance d'erreur TC et de la corrélation avec la pluie vraie, pour chaque source.
- **H3-E1 (descriptive)** : l'erreur dépend de la zone. Comparaison des médianes par grande zone (Est humide,
  Hautes Terres au-dessus de 1 000 m, Ouest et Sud secs) et entre côte (moins de 20 km de la mer) et intérieur.

### 6.3 Par les impacts (secondaire, période 2016-2025 si possible)
On relance, avec chaque version de la pluie (3 sources, B, C), les tests déjà établis :
- inondations pluviales : pluie sur 3 jours contre les communes inondées cartographiées par Copernicus EMS (AUC,
  comme R-09) ;
- épisodes de DesInventar : détection à partir de la pluie sur 3 jours (POD, FAR) ;
- sécheresse du Grand Sud 2019-2022 : SPI-3 et SPI-12 régionaux (rangs et détection, comme R-14 et R-15).

Le nombre d'événements est faible : ces résultats sont descriptifs, sans test de signification.

### 6.4 Lecture des résultats
- Si C ne bat pas la meilleure source seule, le système garde cette source et le résultat négatif est publié.
- Si C l'emporte, elle peut remplacer CHIRPS dans le système, mais seulement après un protocole séparé pour les
  modules concernés (la validation d'un module ne valide pas les autres).

## 7. Limites connues

- CHIRPS intègre des stations GTS, qui sont probablement en partie les stations GSOD : **la comparaison aux stations
  favorise CHIRPS et C**. Les impacts (6.3) et la TC (6.2) ne dépendent pas des stations.
- La TC suppose des erreurs indépendantes. Un lien entre CHIRPS et IMERG par l'infrarouge sous-estimerait leurs
  erreurs.
- Stations : les 25 stations synoptiques sont surtout sur les côtes et dans les villes, et le Sud intérieur est peu
  couvert.
- Les jours ne sont pas définis pareillement d'une source à l'autre ; la pentade réduit cet effet sans le supprimer.
- La résolution de 0,1° reste plus grande que 74 % des fokontany (registre, question 1).

## 8. Mise en œuvre et mises à jour automatiques

- Téléchargement : `scripts/build_e1_sources.py`, workflow « 20 - E1 : sources de pluie ». Les fichiers sont rangés
  par source et par année dans la version GitHub `e1-pluie`. Une exécution mensuelle complète l'année en cours.
- Calcul : `scripts/validate_e1.py`, écrit avant de voir les résultats, en suivant ce protocole.
- Résultats : `validation/e1_fusion_pluie.md`, puis inscription au registre (`etat_des_lieux_registre.md`) et au
  journal de recherche, que les résultats soient positifs ou négatifs.

## 9. Journal des modifications

- 02/11/2026 : version initiale.
- 02/11/2026, après le premier téléchargement (stations GSOD et CHIRPS 2015) et **avant tout calcul de score** : la
  règle « drapeaux A à H » gardait des cumuls partiels. D'après la documentation GSOD, A, B et C sont des sommes de 1 à
  3 relevés de 6 heures, E un seul relevé de 12 heures, et H une donnée incomplète. Ils sous-estiment la pluie du jour.
  Seuls D, F et G (journée complète) sont gardés. Sur l'ensemble 2001-2026 : 47 149 jours G, 2 673 D et 530 F ;
  47 344 jours I.
- 02/11/2026, même constat : en 2015, CHIRPS à la maille de Toamasina (2 951 mm) et la station de Toamasina (2 945 mm
  sur 301 jours valides) sont presque égaux. Cela confirme que CHIRPS intègre cette station (section 7). Aucune règle
  ne change : la limite était prévue, et ce chiffre la documente.
