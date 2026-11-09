# Données à demander au ministère de l'Eau, de l'Assainissement et de l'Hygiène (MEAH)

*Préparé le 04/11/2026 pour la démarche du porteur du projet. Appuyé sur l'atlas des nappes par bassin
(`atlas_bassins.md`, `atlas_sousbassins.md`) et sur l'état des données (`journal_recherche.md`). Les données obtenues
resteront hors du dépôt public ; seuls des résultats agrégés seront publiés, avec citation du ministère, et toute
condition d'utilisation sera respectée.*

## 1. Pourquoi ces données

Les seules mesures publiques de niveau statique (MGMERL, 1 400 relevés) sont concentrées dans le Grand Sud :
**10 régions sur 24 n'en ont aucune** et **9 bassins versants sur 108 seulement** ont une connaissance mesurée de leur
nappe. Dans le reste du pays, la carte du niveau statique est une extrapolation dont l'erreur n'est pas connue. Les
données du ministère permettraient de **valider** la carte, le transfert de connaissances et le modèle THMS hors du
Sud, ce qu'aucune autre source ne permet.

## 2. Données demandées, par ordre de priorité

### Priorité 1 : relevés de forages et de puits (inventaire national, rapports de fin de travaux)
Pour chaque ouvrage : identifiant, **coordonnées GPS**, type (forage, puits, source), **profondeur totale**, **niveau
statique** avec **date de mesure** et repère (sol ou margelle), niveau dynamique et débit d'essai, date de réalisation,
entreprise, **coupe lithologique** (épaisseur d'altérites, profondeur du socle, venues d'eau), conductivité et
qualité si mesurées, état de fonctionnement.
- Format souhaité : tableur (Excel, CSV) ou base de données ; à défaut, rapports PDF.
- Période : toutes les années disponibles (les relevés anciens restent utiles s'ils sont datés).

### Priorité 2 : séries de suivi des nappes (piézométrie)
Tout réseau de suivi (piézomètres, dataloggers) avec dates et niveaux : indispensables pour la recharge mesurée et le
test THMS, qui demandent des séries d'au moins 5 ans.

### Priorité 3 : essais de pompage et paramètres d'aquifère
Transmissivité, perméabilité, coefficient d'emmagasinement ou porosité efficace, avec la méthode d'interprétation.

### Priorité 4 : cartes et études
Cartes hydrogéologiques, études hydrogéologiques et géophysiques régionales, carte géologique numérique (1:100 000
PGRM si disponible), carte des failles.

### Priorité 5 : approvisionnement des villes
Pour les centres JIRAMA et les adductions : source de chaque captage (rivière ou forage), volumes produits et
distribués, taux de desserte réel, pour estimer la part de la consommation prélevée dans la nappe.

### Mise à jour du 09/11/2026 : ce que les tests de la recharge demandent en plus

Les tests de la recharge (`methodologie_these.md`, section 7.1) et l'analyse de puissance (`analyse_puissance.md`)
précisent les besoins ; le détail est dans `plan_mesures.md` :
- **Séries de niveaux** : au moins 2 ans suffisent pour la recharge par fluctuation, à condition d'avoir **4 à 6 groupes
  de sites indépendants (distants de plus de 20 km) par type de roche** : socle, sables et alluvions, calcaires.
- **Chimie de l'eau** : chlorure, sodium et **brome** si mesuré (le rapport Cl/Br distingue le chlorure de la pluie de
  celui des roches), conductivité, nitrate, avec les dates.
- **Profondeur des crépines** et **forages captant deux niveaux au même endroit** : pour tester une recharge des nappes
  profondes plus lente que celle des nappes peu profondes.
- **Essais de pompage longs avec piézomètre d'observation** : pour le coefficient d'emmagasinement (rendement
  spécifique) ; les essais sur un seul forage donnent surtout la transmissivité.

## 3. Zones prioritaires (d'après l'atlas)

| Priorité | Bassin versant | Population | Relevés MGMERL | Fokontany en extrapolation | Pourquoi |
|---|---|---|---|---|---|
| 1 | n° 1 Boanamary (Betsiboka-Ikopa, Antananarivo) | 4,8 millions | 31 | 83 % | plus grand bassin habité, Hautes Terres |
| 2 | n° 3 Belo-sur-Tsiribihina (Tsiribihina, Vakinankaratra) | 3,4 millions | 1 | 83 % | presque aucune mesure |
| 3 | n° 2 Antongo Vaovao (Mangoky, Haute Matsiatra) | 2,1 millions | 26 | 76 % | Hautes Terres du Sud |
| 4 | n° 7 Ambodiharina (Mangoro, Alaotra) | 1,5 million | 0 | 87 % | aucune mesure |
| 5 | n° 11 Ampasina Maningory, n° 5 Mahadrodroka, n° 12 Analalava (Est, Nord-Ouest) | 2,5 millions | 5 | 32 à 43 % | Est humide et Nord-Ouest |
| 6 | Villes côtières de l'Ouest : Toliara, Mahajanga, Morondava, Maintirano | — | variable | — | pression la plus forte à l'échelle fine ; recharge mal connue |

Ajout du 09/11/2026, d'après les échecs des tests de la recharge : zones calcaires hors de Toliara (nord du plateau
Mahafaly, Bemaraha, Namoroka) ; sables et alluvions de la côte Ouest (Morombe, Morondava) ; socle hors de l'Androy et
de l'Anosy.

Régions sans aucun niveau statique mesuré : Itasy, Vakinankaratra, Haute Matsiatra, Alaotra-Mangoro, Atsinanana,
Sofia, Diana, Melaky, Bongolava, Ihorombe.

## 4. Ce que le ministère y gagne

Une carte nationale du niveau statique et de la ressource avec sa **précision affichée**, un atlas par bassin, et des
outils de prévision (sécheresse, nappe), réutilisables pour la planification des forages et le suivi des ODD 6.

## 5. Engagements proposés

Citation du ministère dans tous les produits ; pas de diffusion des données brutes sans accord ; restitution des
résultats (cartes, atlas, rapports) au ministère.
