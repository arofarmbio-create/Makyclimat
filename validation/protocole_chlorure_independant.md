# Protocole : T2 contre T2L par bilan de chlorure, dépôt mesuré et blocs neufs (étape T-H2.1)

*Rédigé le 16/11/2026, **avant** toute donnée du test : aucun collecteur de pluie n'est posé et aucun forage neuf
n'est reçu. Suite de R-50 (`protocole_recharge_chlorure.md`) et de R-53 (`protocole_combinaison_preuves.md`).
Rattachement : module M3, expériences E3 et E7, hypothèse H2. Analyse de puissance :
[`puissance_chlorure_independant.md`](puissance_chlorure_independant.md) (script
`scripts/puissance_chlorure_independant.py`). **Le calcul fixé ici (étape T-H2.2) n'est lancé qu'après validation
du porteur du projet.** Toute modification sera datée en section 11.*

## 1. Question

R-50 et R-53 ont laissé deux réserves : (1) le verdict dépend du dépôt de chlorure, jamais mesuré à Madagascar
(scénarios bas et central : T2L meilleure ; haut, désigné par MERRA-2 : non) ; (2) les 36 blocs ont été définis après
coup, sur des forages déjà vus. **Avec un dépôt mesuré sur un transect côte-intérieur et des blocs de forages neufs,
T2 surestime-t-elle la recharge, et la correction par roche de T2L apporte-t-elle quelque chose au-delà d'un simple
changement de niveau ?**

Question transférable : quand une recharge transférée est corrigée par quelques mesures locales, comment séparer, sur
une validation indépendante, ce qui relève du **niveau** (biais d'ensemble) de ce qui relève de la **structure**
(répartition spatiale) de la correction, alors que la référence elle-même porte une erreur d'échelle inconnue ?

## 2. Leçon de la préparation (déclarée)

Le premier jet reprenait le critère de R-50 (H-Cl2 : écart absolu de T2L inférieur d'au moins 30 % à celui de T2).
Le contrôle sur les données déjà vues (section 1 de l'analyse de puissance) montre que **T2 « décalé »**, c'est-à-dire
T2 multipliée par une constante amenant son niveau médian à celui de T2L (× 0,19), passe ce critère aussi bien que T2L
dans les scénarios bas et central : le critère mesurait le niveau, pas la correction par roche. Il est abandonné comme
critère de décision et remplacé par deux hypothèses séparées. Sur les mêmes blocs déjà vus, une fois le niveau retiré,
**l'écart centré de T2L est plus grand que celui de T2** (de 39 à 59 % selon le scénario) : la structure de T2L n'y
apporte rien. Ce constat, fait sur des données vues, ne décide rien ; il fixe l'attente et la puissance.

## 3. Unités indépendantes : blocs neufs (fixées avant toute donnée)

- **Grille fixe** de blocs de 20 km : indice de latitude ⌊lat / (20/111)⌋, de longitude
  ⌊lon / (20 / (111 cos 23°))⌋ (latitude de référence fixe, contrairement à R-50 où elle dépendait des données).
- **Forage neuf** : chlorure mesuré, positif, coordonnées connues, **absent des 538 forages de R-50** (mêmes
  coordonnées à 5 décimales et même chlorure = doublon, retiré). Sources possibles : ministère de l'Eau (X-MEAH),
  zone ZH10 de BushProof (X-BUSHPROOF), tout autre jeu reçu. Filtres de R-50 inchangés : côte ≥ 5 km, nitrate
  ≤ 50 mg/L, exclusion si conductivité > 3 000 µS/cm et Cl < 10 % de la somme des ions majeurs. Filtre ajouté :
  si le bromure est mesuré, exclusion si Cl/Br (massique) > 3 fois la médiane Cl/Br des pluies mesurées (chlorure
  venu des roches) ; forages sans bromure gardés, part publiée.
- **Bloc neuf** : au moins 3 forages neufs valides ; centre à au moins 20 km du centre de tout bloc R-50
  (`recharge_chlorure_blocs_zones.csv`) ; maille T2L la plus proche du centre **dans le domaine** et avec T2L ≠ T2
  (hors domaine, T2L = T2 et le bloc n'apporte rien à la comparaison). Valeur du bloc : médiane de Cl_n.
- **Sensibilité d'indépendance** : sous-ensemble sans blocs voisins (bord ou coin communs), choisi en gardant le bloc
  qui a le plus de forages ; publié, ne décide rien.
- Plafond géométrique : 189 blocs possibles hors R-50 dans le domaine (analyse de puissance, section 2). Le nombre
  réel dépend des forages reçus.

## 4. Dépôt de chlorure mesuré (fixé avant de lire les chlorures des forages neufs)

- **Mesures** (démarche X-CHLORURE) : 4 à 5 collecteurs ouverts en permanence (dépôt « bulk », humide et une part du
  sec) à environ 5, 30, 100 et plus de 150 km de la côte, une saison des pluies au moins ; Cl, Na, Br mensuels ;
  hauteur de pluie relevée au collecteur.
- **Par collecteur** : concentration moyenne pondérée par le volume, Cl_p (mg/L).
- **Forme** : Cl_p(d) = Cl_i + (Cl_c − Cl_i) exp(−d / L), ajustée en log par moindres carrés sur les collecteurs.
  Si l'ajustement échoue (non-convergence, L hors de [1 ; 500] km ou moins de 4 collecteurs valides) :
  interpolation linéaire de log Cl_p en fonction de d entre collecteurs, constante au-delà des extrêmes.
- **Dépôt** D = P × Cl_p(d), P = pluie moyenne de la maille (`LTA_P_mmpa`, comme R-50), d = distance au trait de côte
  Natural Earth 10 m, au centre du bloc. Pas de facteur de dépôt sec ajouté : le collecteur ouvert en capte une part,
  le reste est couvert par l'encadrement.
- **Encadrement fixé** : dépôt mesuré ÷ 1,5 ; mesuré ; × 1,5 (dépôt sec non capté, variabilité d'une année à
  l'autre, une seule saison).
- **Scellement** : D est calculé, publié avec son empreinte SHA-256 et noté en section 11 **avant** l'ouverture des
  chlorures des forages neufs. MERRA-2 n'entre pas dans le test (sa vérification est l'étape T-H6.4).
- Recharge de référence du bloc : R = D / Cl_n (mm/an).

## 5. Modèles confrontés (cartes figées, aucun recalcul)

T2 (`recharge_transferee.csv`) et T2L (`inputs/hydrogeologie/recharge_t2l.csv`, SHA-256 `2dc024a9…2291`), maille la
plus proche du centre du bloc. T2K n'est pas testée (aucun forage karstique en main ; étape T-H2.7). Contrôle :
« T2 décalé » = T2 × médiane(T2L / T2) **sur les blocs neufs** (calculée sur les cartes seules, sans la référence).

## 6. Hypothèses et règles de décision (fixées avant toute donnée)

e = log₁₀(modèle / R) par bloc.

- **H-I1 (niveau, confirmatoire)** : T2 surestime. Test du signe unilatéral sur e(T2), p < 0,05, **avec le dépôt
  × 1,5** (le scénario le moins favorable). Publiés aussi : médiane de e(T2) et de e(T2L) dans les trois scénarios.
- **H-I2 (structure, exploratoire dès le départ)** : écart centré c = |e − médiane(e)| de chaque modèle ; Wilcoxon
  apparié unilatéral sur c(T2) − c(T2L), p < 0,05, **et** médiane de c(T2L) inférieure d'au moins 30 % à celle de
  c(T2). Invariant à une erreur uniforme du dépôt : une seule décision, valable dans les trois scénarios.
  **Contrôle de la référence** : le même test appliqué à T2 décalé contre T2 donne une différence nulle par
  construction (même structure) et échoue ; vérifié sur les données vues.
- **H-I3 (comparaison d'ensemble, descriptive)** : le critère H-Cl2 de R-50 (écart absolu réduit d'au moins 30 %,
  Wilcoxon p < 0,05, dans les trois scénarios) est publié pour la continuité avec R-50 et R-53, avec T2 décalé à
  côté ; il ne décide rien (section 2).
- **Corrélation de rang** de Spearman de chaque modèle avec R, publiée (descriptive).

**Condition de puissance** : le test n'est confirmatoire pour H-I1 que si **au moins 12 blocs neufs** sont réunis et
si le dépôt est mesuré par au moins 4 collecteurs sur une saison complète. En dessous : tout est exploratoire, déclaré
comme tel avant le calcul.

## 7. Puissance (résumé ; détail dans l'analyse de puissance)

Vraisemblance de planification : les 33 blocs R-50 du domaine (déjà vus), tirés avec remise, plus un bruit propre au
bloc σ_e de 0,1 à 0,3 (log₁₀) et une erreur commune du dépôt σ_u = 0,1 ; et une famille paramétrique où la structure
de T2L corrige 0, 30 ou 50 % de l'écart centré de T2. Résultats : voir la section 12, remplie à partir du rapport
généré.

## 8. Décision

- **H-I1 soutenue** : « T2 surestime la recharge du Grand Sud » passe de *provisoire* à *soutenue* (après relecture).
  La carte T2 est alors publiée comme **borne haute** dans le Grand Sud ; le choix d'une nouvelle valeur centrale
  (T2L ou T2 décalé) n'est pas tranché par ce test et revient au porteur du projet.
- **H-I1 non soutenue** : la surestimation reste un indice ; T2 reste la valeur centrale.
- **H-I2** (exploratoire) : ne change aucune carte. Positive : elle justifie un protocole confirmatoire de la
  correction par roche sur d'autres blocs (étapes T-H2.3 et T-H2.4). Négative : elle confirme que l'apport de T2L est
  un niveau et non une structure, ce qui oriente T-H2.3 vers une correction par classe d'aquifère mieux renseignée.

## 9. Ce qui reste à l'étape T-H2.2

Écrire le script de test **avant** l'ouverture des données (commit daté), sceller D (section 4), puis appliquer ce
protocole sans le modifier. Données requises : D-CHLORURE-PLUIE et D-RECHARGE-REF (chlorure sur forages neufs).

## 10. Limites

- Chlorure des roches : filtres et rapport Cl/Br le réduisent sans le supprimer ; le Cl/Na médian de R-50 (0,96)
  laisse soupçonner un apport des roches qui abaisse R et favorise H-I1.
- Une saison de collecte ne mesure pas la variabilité d'une année à l'autre : l'encadrement × 1,5 est un choix.
- Bilan de chlorure = recharge de long terme ; recharge concentrée (rivières, dépressions) mal vue.
- Les blocs neufs peuvent être concentrés là où le ministère a foré : biais géographique, publié avec la carte des
  blocs.
- La vraisemblance de planification vient de blocs déjà vus du Grand Sud ; d'autres roches peuvent se comporter
  autrement.

## 11. Journal des modifications

- 16/11/2026 : version initiale (premier jet à critère d'écart absolu abandonné avant toute donnée, section 2).

## 12. Résultats de l'analyse de puissance

2 000 tirages par case, graine 20261116 ([rapport](puissance_chlorure_independant.md),
[table](puissance_chlorure_independant.csv)).

- **H-I1 (niveau)** : à 12 blocs, puissance de 88 à 96 % si la vérité ressemble au scénario central (σ_e de 0,3 à
  0,1), et de 100 % si elle ressemble au scénario bas ; faux positifs de 1 à 3 % si elle ressemble au scénario haut
  (T2 non biaisée vers le haut). La puissance n'augmente pas régulièrement avec n (test du signe discret : 10 blocs
  font moins bien que 8) ; **seuil fixé à 12 blocs**, qui dépasse 80 % dans tous les cas favorables.
- **H-I2 (structure)** : faux positifs ≤ 2 %. Si la structure de T2L corrige 50 % de l'écart centré de T2 :
  puissance de 29 à 54 % à 12 blocs, de 45 à 82 % à 30 blocs ; si elle en corrige 30 % : 35 % au mieux. Si la vérité
  ressemble aux blocs déjà vus (structure de T2L moins bonne que celle de T2), puissance nulle dans les trois
  scénarios. **Sous 50 % dans les cas réalistes : H-I2 est exploratoire dès le départ** (règle de méthode du
  09/11/2026).
- **Contrôle de la référence** : sur les données vues, T2 décalé contre T2 échoue à H-I2 (différence nulle) ; H-I1
  passe dans les scénarios bas et central et échoue dans le haut, ce qui montre que H-I1 dépend bien du dépôt que
  la mesure va fixer.
- Plafond : 189 blocs neufs possibles dans le domaine T2L (67 « autres », 122 socle) ; 12 blocs suffisent pour H-I1,
  au moins 30 seraient nécessaires pour viser 80 % sur H-I2 avec un gain de structure de 50 % et un bruit faible.
