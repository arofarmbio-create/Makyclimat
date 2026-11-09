# Revue de littérature ciblée : nouveauté des trois contributions (09/11/2026)

Recherche rapide (moteurs web, une dizaine de requêtes), **pas une revue systématique**. À approfondir avant rédaction.

## C1 : quand une recharge transférée d'une base continentale devient utilisable dans un pays pauvre en données

- **Wan, Döll et Müller Schmied (2024)**, *Water Resources Research* 60, e2023WR036182,
  doi:10.1029/2023WR036182. Recharge mondiale (WaterGAP 2.2e) réglée séparément pour le **karst** (carte mondiale des
  aquifères karstiques WOKAM) et le non-karst (422 mailles mesurées). Dans le karst, la recharge est proche de
  l'écoulement total. → **Que le karst se comporte à part est déjà établi** ; notre résultat (Toliara sous-estimée)
  le confirme, il n'est pas nouveau en soi. Conséquence pratique : la carte **WOKAM** est sans doute plus adaptée que
  la GLiM pour délimiter le karst.
- **METIS-IPSL (S. Carrière), poste de post-doctorat 2024-2025** : cartographier la recharge à 1 km dans le
  **Sud-Ouest de Madagascar** (GROSoM, fluctuation de nappe ESPERE, GRACE, modèle de réservoir). → Travail
  **directement voisin** du nôtre, sur la même zone et les mêmes puits. À citer et à distinguer : approche locale et
  physique sur le Sud-Ouest, contre transfert continental à l'échelle de l'île, testé par hypothèses fixées
  d'avance. Leurs publications pourront servir de référence indépendante.
- Études de recharge en pays pauvres en données (Éthiopie 2024 ; bassin de la Densu au Ghana, BGS) : estimation
  locale, pas d'évaluation d'un transfert continental.
- **Bilan provisoire** : pas trouvé d'étude qui teste, par une suite d'hypothèses fixées d'avance, si un transfert
  continental de recharge est utilisable à l'échelle d'un pays et pourquoi il échoue. **Nouveauté plausible, à
  formuler étroitement.**

## C2 : la validation site par site surestime la performance

- Principe **bien établi** : Roberts et al. 2017 (*Ecography*) ; Ploton et al. 2020 (*Nature Communications*) ;
  Meyer et Pebesma (domaine d'applicabilité) ; en eaux souterraines, Tziachris et al. 2023 (*Water* 15, 2278,
  salinité) et une prépublication ESS Open Archive sur la conductivité hydraulique.
- Pas trouvé d'application à un transfert de recharge avec très peu de sites.
- **Bilan provisoire** : **pas une contribution principale** ; illustration chiffrée utile, qui appuie C1.

## C3 : hypothèses fixées d'avance (préenregistrement), échecs publiés, carte figée pour un test futur

- Pas trouvé de politique de préenregistrement dans *Water Resources Research* ni *HESS*. Débat sur le test
  d'hypothèses en hydrologie (Kirchner et Pfister, EGU 2017 ; série de débats WRR 2017) ; préenregistrement
  « adaptatif » pour la modélisation en écologie (Gould et al., *Methods in Ecology and Evolution* 17, 2026).
- **Bilan provisoire** : pratique **rare en hydrogéologie** ; nouveauté plausible de méthode, surtout si elle est
  couplée à la validation prospective (carte T2L figée, SHA-256).

## Reformulation proposée de la contribution

Une **évaluation préenregistrée, par réfutation, d'un transfert de recharge continental vers un pays pauvre en
données** (C1 + C3), qui montre que la limite n'est pas le nombre de mesures mais la classification des aquifères (le
karst à part, comme Wan et al. 2024 l'ont établi à l'échelle mondiale) et l'indépendance spatiale des sites (C2), avec
un test prospectif figé.

## À faire

1. Lire en entier Wan et al. 2024 ; vérifier la licence de **WOKAM** (Chen et al. 2017) et l'ajouter à l'agent de
   téléchargement.
2. Chercher les publications issues du post-doctorat METIS-IPSL et de GROSoM (Carrière et al.).
3. Recherche systématique (Scopus ou Web of Science) : « groundwater recharge » ET (transfer OU upscaling) ET
   (Africa OU data-scarce) ; « preregistration » ET (hydrology OU hydrogeology).

## Mise à jour du 09/11/2026 : WOKAM et Wan et al. 2024

- **Texte intégral de Wan et al. 2024 non lu** : la page de l'éditeur renvoie une erreur 403 aux outils automatiques.
  Lu : le résumé, le résumé EGU 2023 (Wan et Döll, EGU23-15656) et le jeu de données figshare 23592666 (CC BY 4.0).
  Selon le résumé EGU 2023, 818 mailles de 0,5° mesurées, dont 75 en karst ; R/P de 2 à 66 % dans le karst ; hors
  karst, la part simulée dépasse rarement 25 %. Chiffres de la version publiée à vérifier sur le PDF.
- **Le projet utilise déjà ce jeu de données** (`data/mdg/analogues/recharge_mondiale/figshare_23592666/`,
  821 mailles, colonne `fkarst` = part karstique de la maille d'après WOKAM).
- **Exploratoire** (calculé après coup ; ce n'est pas un résultat) : R/P médian en climat aride = 0,032 sans karst
  (195 mailles), 0,072 si le karst couvre au moins 30 % de la maille (47 mailles) ; quantile à 90 % : 0,114 contre
  0,305. Pour Toliara (P = 452 mm), cela donnerait une médiane d'environ 33 mm/an et un quantile à 90 % d'environ
  138 mm/an, à rapprocher des 80 à 195 mm/an mesurés aux puits GROSoM. → **Hypothèse à fixer dans un protocole avant
  tout test.**
- **Licence WOKAM** (Chen et al. 2017, BGR, IAH, KIT, UNESCO) : métadonnées BGR « pas de restriction d'accès » ;
  conditions générales de la BGR (https://www.bgr.bund.de/AGB_en, page non lisible par les outils automatiques) ;
  citation obligatoire : « Datenquelle: WHYMAP WOKAM, (C) BGR Berlin, IAH Reading, KIT Karlsruhe, UNESCO Paris
  2017 ». **Republication de données dérivées dans un dépôt public : non vérifiée** ; à lire dans les conditions de
  la BGR avant de publier autre chose que des chiffres agrégés.
- Alternative sous licence vérifiée : la grille mondiale de part karstique `fkarst` à 0,5° publiée avec Wan et al.
  (figshare 23592666, **CC BY 4.0**), plus grossière que WOKAM.
