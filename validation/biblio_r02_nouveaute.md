# R-02 est-il nouveau ? Recherche bibliographique du 02/11/2026

**Résultat examiné (R-02, `methodologie_these.md` §4.2).**
- Au niveau de la région, le vent et la pluie d'un cyclone classent bien les régions touchées (AUC 0,84).
- À l'intérieur des zones déjà touchées, au niveau du fokontany, ils ne séparent presque plus les fokontany inondés ou
  endommagés des autres (AUC 0,51 à 0,52).
- C'est alors le terrain qui décide (hauteur au-dessus du cours d'eau HAND, altitude, pente, distance à la rivière,
  densité) : AUC 0,79 au fokontany et 0,82 à la commune, probabilités calibrées.
- Vérité terrain : 8 activations Copernicus EMS, un événement laissé de côté à chaque fois.

Niveau de lecture : **[lu]** texte intégral ou large extrait ; **[résumé]** résumé ou notice seulement.

## 1. Ce qui existe déjà

- **Dépendance d'échelle des dégâts cycloniques** : Tang et al. (2023, *Earth's Future*, doi:10.1029/2023EF003762),
  Chine continentale [résumé]. Ils comparent des fonctions de dommages calées par cyclone et par province : plus
  l'unité spatiale est grande, plus l'aléa, l'exposition et la vulnérabilité expliquent les dommages. **L'idée que
  l'aléa compte davantage aux grandes échelles est donc déjà publiée.**
- **Modèles d'impact des typhons aux Philippines** :
  - modèle opérationnel de la Croix-Rouge (510) par municipalité, depuis 2019 [résumé] ;
  - Kooshki Forooshani et al. (2024, *NHESS* 24, 309-329), grille de 0,1°, un typhon laissé de côté [lu, en grande
    partie] : le vent et la pluie sont les variables les plus importantes. Le relief joue un rôle secondaire : les
    zones plates sont plus touchées que les zones pentues, et l'altitude seule ne donne pas de signal clair.
- **Hauteur au-dessus du cours d'eau (HAND) et inondation à Madagascar** : chaîne de traitement Sentinel-1 avec un
  seuil HAND de 5 m, appliquée à toute l'île après Batsirai (prépublication) [résumé]. Le HAND y sert à **cartographier
  l'inondation**, pas à expliquer où se concentrent les dégâts face à l'intensité du cyclone.
- **Inondations composées cycloniques à Madagascar** : modèle couplé (*Natural Hazards*, 2025), taux de réussite de
  0,83 contre une carte satellite [résumé].
- **Biais d'agrégation** : les relations changent quand on agrège les données (vulnérabilité sociale, 2025 ;
  glissements de terrain, 2026) [résumé].

## 2. Verdict

**R-02 n'est pas une découverte sans précédent, mais une contribution réelle.**
- Ce qui est déjà connu : le principe de la dépendance d'échelle (Tang et al. 2023) et le rôle du relief dans la
  localisation des inondations.
- Ce qui semble nouveau (aucune étude trouvée qui fasse les trois) :
  1. un plan d'analyse **conditionnel** : à l'intérieur des zones déjà touchées, l'intensité de l'aléa cesse
     d'expliquer où sont les dégâts, et c'est le terrain qui prend le relais ;
  2. au niveau du **village** (fokontany, environ 12 km²) en Afrique, avec une **vérité terrain satellitaire**
     (Copernicus EMS) et une **validation par événement laissé de côté** ;
  3. **à Madagascar**, où aucune étude de ce type n'a été trouvée.
- Pour la thèse : le présenter comme une **extension** de Tang et al. (2023) à une échelle bien plus fine et à un pays
  sans données, pas comme une première absolue.

## 3. La faiblesse à traiter avant de le défendre

**L'aléa est décrit trop grossièrement.** Le vent vient d'un modèle de trajectoire (IBTrACS) et la pluie de CHIRPS à
0,05°, au pas journalier. À l'intérieur d'une zone touchée, ces champs varient peu d'un fokontany à l'autre. Une AUC
de 0,5 peut donc venir de cette résolution, et pas d'une vraie absence de rôle de l'aléa. Kooshki Forooshani et al.
utilisent la pluie maximale sur 6 heures (GPM), qu'ils trouvent plus parlante que le cumul sur 24 heures.

**Test proposé (R-02 bis, protocole à écrire avant calcul)** : refaire la comparaison avec un aléa plus fin, à savoir
la pluie maximale sur 1, 3 et 6 heures d'IMERG (0,1°, toutes les 30 minutes ; déjà téléchargée pour le périmètre
pilote) et les rafales d'ERA5. Deux issues possibles :
- l'aléa reste proche de 0,5 alors que le terrain reste autour de 0,8 : le résultat devient beaucoup plus solide ;
- l'aléa fin regagne du pouvoir de discrimination : le résultat change, et cela se publie aussi (l'échelle de l'aléa
  compte autant que celle de l'unité d'analyse).

Autre limite connue, déjà notée : Copernicus EMS cartographie surtout les zones accessibles ou urbaines, ce qui biaise
la vérité terrain elle-même.

## 4. Sources

- Tang R. et al. (2023). Spatial scale dependence of tropical cyclone damage function: evidence from the mainland of
  China. *Earth's Future*. https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2023EF003762
- Kooshki Forooshani M., van den Homberg M., Kalimeri K. et al. (2024). Towards a global impact-based forecasting
  model for tropical cyclones. *NHESS* 24, 309-329. https://nhess.copernicus.org/articles/24/309/2024/
- Impact-based forecasting for anticipatory action to typhoons in the Philippines (PreventionWeb).
  https://www.preventionweb.net/resource/case-study/impact-based-forecasting-anticipatory-action-typhoons-philippines
- Detection of large-scale floods (prépublication, HAND et Sentinel-1, Madagascar).
  https://www.preprints.org/manuscript/202309.1375/v1/download
- Tropical cyclone induced compound flooding in Madagascar: a coupled modeling approach. *Natural Hazards* (2025).
  https://link.springer.com/article/10.1007/s11069-025-07209-z
- The influence of scale in modeling social vulnerability and disaster assistance (2025).
  https://doi.org/10.1080/24694452.2025.2549057
