# Protocole : recharge par bilan de chlorure dans le Grand Sud, test indépendant des recharges T2, T2L et T2K

*Rédigé le 09/11/2026, **avant** la réception des données et avant tout calcul. Données : base « Contribution à
l'hydrogéologie du Sud de Madagascar » (Al-Zoubaidy, Monteleone et Bünzli 2023, BushProof / DDC), libre
d'utilisation, vente et appropriation interdites ; données brutes hors du dépôt. Toute modification sera datée en
section 10.*

## 1. Question

Les recharges T2 (transfert africain), T2L (corrigée par les mesures malgaches) et T2K (karst) n'ont été confrontées
qu'à 12 sites formant 8 groupes indépendants, et deux tests sur trois n'ont rien départagé (H-L1, H-K2). **Sur des
dizaines de zones indépendantes du Grand Sud, laquelle des trois recharges s'accorde le mieux avec une recharge
estimée par une autre méthode, le bilan de chlorure ?**

## 2. Méthode du bilan de chlorure

Recharge diffuse à long terme : R = D / Cl_n, où D est le dépôt atmosphérique de chlorure (mg/m²/an, pluie et dépôt
sec) et Cl_n le chlorure de la nappe (mg/L) ; R en mm/an. Hypothèses classiques : tout le chlorure de la nappe vient
de l'atmosphère, régime permanent, pas d'apport ni de perte en surface.

## 3. Sélection des forages (fixée avant calcul)

- Forage gardé s'il a un chlorure mesuré, positif, et des coordonnées dans le Grand Sud.
- **Exclus** : forages à moins de 5 km de la côte (intrusion marine, embruns) ; nitrate > 50 mg/L (pollution humaine,
  souvent accompagnée de chlorure) ; conductivité > 3 000 µS/cm sans lien avec le chlorure (Cl < 10 % de la
  minéralisation totale, signe d'une autre source de sels). Sensibilité publiée sans exclusions.
- **Zones de validation** : forages regroupés par lien simple à moins de 20 km ; zone gardée si au moins 3 forages
  valides. Valeur de la zone : médiane de Cl_n. C'est l'unité indépendante du test.
- Type d'aquifère de la zone (fracturé, karstique, poreux) : type majoritaire des forages de la base BushProof.

## 4. Dépôt de chlorure (fixé avant de voir les chlorures de la nappe)

La source de D sera choisie parmi celles que l'agent de téléchargement aura trouvées, **avant** toute lecture des
valeurs de Cl_n, et notée en section 10. Trois scénarios : bas, central, haut. Si aucune source propre au Sud de
Madagascar n'existe, D suit une décroissance avec la distance à la côte tirée d'une source publiée, et les scénarios
bas et haut couvrent au moins un facteur 2 de part et d'autre du central. **Une hypothèse n'est soutenue que si elle
l'est dans les trois scénarios.**

## 5. Recharges confrontées

T2, T2L (carte figée, SHA-256 `2dc024a9…2291`) et T2K (carte figée, SHA-256 `c844a8bc…e4a`), valeur de la maille la
plus proche du centre de la zone. **Aucune n'est recalculée** : c'est un test prospectif des cartes figées.

## 6. Mesures d'accord (par zone, puis médiane sur les zones)

- Écart : |log₁₀(recharge du modèle / R_chlorure)| ; biais : médiane de log₁₀(modèle / R_chlorure).
- Rang : corrélation de Spearman entre modèle et R_chlorure sur les zones (insensible à une erreur uniforme de D).

## 7. Hypothèses (fixées avant calcul)

**Leçon du test karst** : chaque hypothèse compare un modèle à T2. Un test que T2 réussit déjà ne compte pas comme
une confirmation du nouveau modèle.

- **H-Cl1 (validité du transfert)** : T2 suit l'ordre des zones (Spearman ≥ 0,3, p < 0,05) **et** son écart
  médian est au plus 0,3 (facteur 2). Descriptif de la qualité de T2 ; pas de décision à lui seul.
- **H-Cl2 (correction locale)** : dans les zones du domaine de T2L, l'écart médian de T2L est inférieur d'au moins
  30 % à celui de T2.
- **H-Cl3 (karst)** : dans les zones karstiques (type BushProof), l'écart médian de T2K est inférieur d'au moins
  30 % à celui de T2 ; **et** dans les zones non karstiques, il n'est pas supérieur de plus de 10 % à celui de T2.
- **H-Cl4 (cohérence des méthodes)** : aux sites de fluctuation de nappe (MGMERL, GROSoM) situés à moins de 10 km
  d'une zone, la recharge par fluctuation et celle par chlorure sont dans le même ordre de grandeur (rapport compris
  entre 1/3 et 3) pour au moins la moitié des sites. Descriptif : il dit si les deux méthodes de « vérité terrain »
  s'accordent.

## 8. Décision

- H-Cl2 soutenue : T2L devient la valeur centrale dans son domaine ; l'atlas par sous-bassin est refait.
- H-Cl3 soutenue : T2K devient la valeur centrale dans les mailles karstiques ; l'atlas est refait.
- Aucune soutenue : T2 reste la valeur centrale ; la recharge par chlorure est publiée comme estimation indépendante
  du Grand Sud, avec ses scénarios.

## 9. Limites

- Chlorure d'autres origines : évaporites, roches marines, embruns, pollution. Les filtres réduisent ce risque sans
  le supprimer, et le Grand Sud est proche de la mer.
- Le bilan de chlorure mesure une recharge de long terme, souvent sur des décennies, alors que la fluctuation de
  nappe mesure quelques années récentes.
- Recharge concentrée (rivières, dépressions karstiques) mal vue par la méthode.
- Base compilée de sources multiples : dates, laboratoires et qualité d'analyse hétérogènes ; d'éventuels doublons
  avec les données MGMERL seront recherchés et retirés.

## 10. Journal des modifications

- 09/11/2026 : version initiale.
- 09/11/2026 (avant toute lecture des chlorures de nappe, scellés depuis l'inventaire) : **choix fixés.**
  - **Données disponibles** : 1 487 forages BushProof sur 2 880 (zone ZH10 perdue), 559 avec chlorure ; **aucun forage
    karstique** : H-Cl3 (karst) est **infaisable** et ne sera pas calculée.
  - **Dépôt de chlorure** D = P × Cl_p(d) × (1 + s), P = pluie moyenne de la maille (`LTA_P_mmpa` de la grille T2), d =
    distance au trait de côte Natural Earth 10 m (UTM 38S), Cl_p(d) = Cl_i + (Cl_c − Cl_i) × exp(−d / L), s = part de
    dépôt sec. Recharge R (mm/an) = D (mg/m²/an) / Cl_n (mg/L). Valeurs (`data/mdg/chlorure_pluie.json`, vérifiées
    sur les sources primaires) :

    | Scénario | Cl_c côte (mg/L) | Cl_i intérieur (mg/L) | L (km) | s | Origine |
    |---|---|---|---|---|---|
    | bas | 1,8 | 0,3 | 10 | 0 | Kwale (Kenya), stations à 13-15 km ; intérieur sud-africain bas (Van Wyk et al. 2011) |
    | central | 2,2 | 0,4 | 30 | 0,3 | médiane Kwale ; intérieur sud-africain ; dépôt sec 30 % (Van Wyk et al. 2011) |
    | haut | 5,4 | 1,0 | 100 | 0,5 | côte du KwaZulu-Natal, saison sèche ; intérieur sud-africain, saison sèche |

    La longueur L n'est donnée par aucune source : c'est un choix encadré par les trois scénarios.
  - **Filtre « autre source de sels »** : la minéralisation totale est approchée par la somme des ions majeurs mesurés
    (Na, K, Ca, Mg, HCO3, CO3, SO4, Cl, NO3) ; exclusion si conductivité > 3 000 µS/cm et Cl < 10 % de cette somme.
    Forages sans conductivité : gardés.
  - **Doublons** : même coordonnées à 5 décimales et même chlorure.
  - **H-Cl4** : rapport fluctuation / chlorure évalué dans le scénario central ; publié dans les trois.
  - **Contrôle préalable (leçon du test karst)** : avant de juger H-Cl2, on publie l'écart médian de T2 ; si T2 est
    déjà à moins d'un facteur 1,5 de la recharge par chlorure dans les trois scénarios, H-Cl2 est déclarée sans
    objet (rien à améliorer), et non soutenue.
- 09/11/2026 (après le calcul) : **échec du découpage en zones fixé d'avance.** Le lien simple à 20 km enchaîne les
  forages denses du Sud : 537 forages forment 2 zones seulement ; aucun test d'ordre possible ; H-Cl1, H-Cl2 non
  soutenues faute de puissance ; H-Cl4 évaluée sur 1 seul site (Andaboly). Résultat robuste malgré tout : T2 surestime
  dans les trois scénarios (biais +0,45 à +1,44 en log₁₀). **Analyse complémentaire déclarée APRÈS COUP (exploratoire,
  ne change aucune décision)** : zones = blocs carrés de 20 km (même découpage que `protocole_puits_a_sec.md`), au
  moins 3 forages par bloc ; mêmes scénarios, filtres et hypothèses ; publiée séparément.
