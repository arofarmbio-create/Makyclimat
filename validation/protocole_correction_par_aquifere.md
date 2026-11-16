# Protocole : correction de T2 par classe d'aquifère, classes tirées des coupes de forage (étape T-H2.3)

*Rédigé le 16/11/2026, **avant** toute donnée du test : aucune référence de recharge neuve ni aucune coupe de forage
n'est reçue (D-RECHARGE-REF, D-SY, D-FORAGES-MEAH manquantes). Suite de R-47 (`protocole_recharge_locale.md`,
`recharge_locale.md`) et de T-H2.1 (`protocole_chlorure_independant.md`). Rattachement : module M3, expériences E3 et
E7, hypothèse H2. Analyse de puissance : [`puissance_correction_aquifere.md`](puissance_correction_aquifere.md)
(script `scripts/puissance_correction_aquifere.py`). **Le calcul fixé ici (étape T-H2.4) n'est lancé qu'après
validation du porteur du projet.** Toute modification sera datée en section 11.*

## 1. Question

R-47 a corrigé la recharge transférée T2 par un facteur par groupe d'aquifère appris sur 12 sites malgaches (T2L) ;
la correction ne s'est pas généralisée par groupes de sites (2 sites retrouvés sur 12, erreur 0,90 contre 0,69 pour
T2). Deux causes possibles, non séparées : (1) deux classes trop grossières (« socle » et « autres », où des sables
à recharge faible côtoyaient des calcaires karstiques à recharge forte) ; (2) une seule référence hors socle, donc
rien à apprendre. **Avec 4 à 6 groupes de sites indépendants par classe de roche, classes lues sur les coupes de
forage, une correction par classe prédit-elle mieux la recharge d'un groupe jamais vu qu'un simple facteur
commun ?**

Question transférable : dans un pays presque sans mesures, combien de références locales par classe de roche
faut-il pour qu'une correction par classe d'une recharge transférée apporte plus qu'un changement de niveau, et la
classe lue sur la coupe de forage fait-elle mieux que la classe lue sur une carte au 1 : 1 000 000 ?

## 2. Leçon de la préparation (déclarée)

Le premier jet reprenait le critère de R-47 (Wilcoxon apparié sur les erreurs absolues **et** réduction de
l'erreur médiane d'au moins 30 %) et comparait aussi la correction à T2 (règle « au moins la moitié des groupes
retrouvés et erreur divisée par deux »). L'analyse de puissance (sections 3, 6 et 7 du rapport) montre que :
- le critère de R-47 manque de puissance : le gain d'une correction par classe se concentre dans la classe qui
  s'écarte (les calcaires dans les données vues), alors que la réduction de 30 % de la **médiane** porte sur tous les
  groupes ;
- la comparaison à T2 « passe » aussi quand les classes ne diffèrent pas : elle récompense le changement de niveau
  commun (T2 surestime le socle d'un facteur 5 environ), pas la classe. C'est l'erreur repérée en T-H2.1.

Les deux sont abandonnés comme critères de décision. Le critère retenu (section 6) compare la correction par classe
au **facteur commun** (M1, l'analogue de « T2 décalé » de T-H2.1) et tire sa loi nulle de **classes permutées**
entre groupes : le contrôle de la référence (des classes sans rapport avec la roche doivent échouer) est la loi
nulle même du test.

## 3. Unités indépendantes et références de recharge

- **Site neuf** : point de mesure absent des 12 sites de R-47 et des 16 sites HT Analytics (D-HT-ANALYTICS), avec
  coordonnées connues et une référence de recharge de l'un des deux types suivants (D-RECHARGE-REF) :
  - **fluctuation de nappe** : au moins 24 mois valides, méthode mensuelle de `protocole_recharge_fluctuation.md`
    inchangée ; Sy mesuré sur le site (D-SY : essai long avec piézomètre, ou géophysique) si disponible, sinon Sy
    par défaut de ce protocole (socle 0,01 à 0,05 ; sédimentaire et non consolidé 0,05 à 0,15 ; calcaires rangés
    avec le sédimentaire), valeur centrale au milieu ;
  - **bilan de chlorure** sur forage neuf, avec le dépôt mesuré et scellé de T-H2.1 (section 4 de
    `protocole_chlorure_independant.md`, scénario central) et les mêmes filtres ; R = D / Cl.
- **Groupe** : sites neufs à moins de 20 km les uns des autres (lien simple, comme R-47). Valeur du groupe :
  e = médiane de log₁₀(R / T2) de ses sites, T2 de la maille la plus proche de `recharge_transferee.csv`.
- Les 12 sites de R-47 **n'entrent pas** dans le test confirmatoire (déjà vus ; leurs classes ont été déclarées
  après les avoir vus). Sensibilité publiée : les 8 groupes de R-47 ajoutés à l'apprentissage (socle : 6 groupes ;
  sables : Sihanamaro ; calcaires : GROSoM).
- Un même forage neuf peut servir à T-H2.2 (bloc de chlorure) et ici (groupe par classe) : les deux tests
  portent sur des questions différentes (niveau de T2 ; apport de la classe) et sont publiés ensemble.

## 4. Classe d'aquifère lue sur la coupe de forage (fixée avant de lire toute recharge)

Classes : **socle** (granite, gneiss, migmatite, quartzite, micaschiste, et leurs altérites et arènes quand la roche
saine est atteinte ou notée sous l'altération) ; **sables et alluvions** (sable, gravier, alluvions, dunes, argile
sableuse non consolidée) ; **calcaires** (calcaire, dolomie, marno-calcaire, calcaire gréseux, karst noté) ; **grès**
(grès, conglomérat consolidés) ; **volcanique** (basalte, tuf).

- **Règle du site** : lithologie de l'intervalle crépiné ; si les crépines ne sont pas décrites, lithologie de plus
  grande épaisseur entre le niveau statique et le fond ; puits sans coupe : classe « carte » (ci-dessous), marquée.
  Argile seule, latérite seule ou coupe illisible : « indéterminée ».
- **Règle du groupe** : classe majoritaire (plus de la moitié des sites) ; sinon « mixte ».
- **Classe carte** (pour H-A3 et les puits sans coupe) : groupe d'aquifère BGS de la maille la plus proche
  (Basement → socle, Unconsolidated → sables et alluvions, Sedimentary → calcaires si la part karstique de Wan et al.
  2024 (D-FKARST) de la maille dépasse 0,5, grès sinon).
- **Aveugle** : la table site → classe est établie à partir des seules coupes, commitée et publiée avec son
  empreinte SHA-256 **avant** l'ouverture des recharges (séries de niveaux, chlorures). Les coupes restent hors du
  dépôt si leurs droits l'exigent ; seule la table de classes agrégée est publiée.
- Groupes « indéterminés » ou « mixtes » : hors du test confirmatoire, publiés à part.

## 5. Modèles confrontés (aucune carte recalculée avant le test)

Validation par groupe laissé de côté sur les groupes neufs : chaque groupe est retiré, le facteur est appris sur les
autres groupes neufs, puis appliqué à T2 au groupe retiré.
- **M0** : T2, sans correction.
- **M1** : facteur commun, T2 × 10^médiane(e) des groupes d'apprentissage (niveau seul).
- **M2c** : facteur de classe, T2 × 10^médiane(e) des groupes d'apprentissage **de la même classe** ; repli sur M1 si
  la classe a moins de 2 groupes d'apprentissage.
- **M2c-carte** : M2c avec la classe carte (section 4) au lieu de la classe de coupe.
- **T2L figée** (`inputs/hydrogeologie/recharge_t2l.csv`, SHA-256 `2dc024a9…2291`) : sa validation prospective,
  fixée en R-47 (section 6 de `protocole_recharge_locale.md` : au moins 60 % des sites neufs du domaine retrouvés), est
  appliquée telle quelle aux sites neufs à fluctuation de nappe situés dans son domaine.

## 6. Hypothèses et règles de décision (fixées avant toute donnée)

Erreur d'un groupe : err = log₁₀(prédite / R).

- **H-A1 (confirmatoire si la condition de puissance est remplie)** : la classe apporte une information au-delà du
  niveau. Statistique G = moyenne |err M1| − moyenne |err M2c| sur les groupes de classe déterminée, dans les classes d'au moins 3 groupes (section 10). p = part des
  999 permutations des classes entre ces groupes (effectifs conservés) dont le G est au moins égal au G observé
  (rang compté +1). **Soutenue si p < 0,05.** G est invariant à une erreur uniforme de la référence (dépôt de chlorure
  ou Sy commun) : une seule décision.
- **Robustesse au Sy par défaut** : si des sites à fluctuation de nappe utilisent le Sy par défaut, le test est refait
  pour chaque coin (Sy bas ou Sy haut choisi indépendamment pour chaque classe concernée). Si un coin donne p ≥ 0,05,
  H-A1 est déclarée « soutenue sous réserve du Sy » et reste exploratoire. Sensibilité : test restreint aux
  références sans Sy par défaut (chlorure, Sy mesuré), publié.
- **H-A2 (exploratoire)** : la coupe fait mieux que la carte. Même statistique avec M2c-carte à la place de M1
  (G' = moyenne |err M2c-carte| − moyenne |err M2c|), Wilcoxon apparié unilatéral, p < 0,05 ; publié avec la part des
  groupes dont la classe de coupe diffère de la classe carte. Puissance non calculable avant de connaître cette part
  (elle est nulle si les deux classes coïncident partout) : exploratoire dès le départ.
- **Descriptifs** : erreurs médianes et sites retrouvés (prédiction dans la fourchette de la référence) de M0, M1,
  M2c ; facteur de chaque classe et intervalle de bootstrap par groupes ; critère de R-47 (section 2), pour la
  continuité, avec la mention qu'il ne décide rien.

**Condition de puissance** (section 12) : H-A1 n'est confirmatoire qu'avec au moins 5 groupes de classe
déterminée dans chacune d'au moins 3 classes, dont les calcaires. En dessous, tout est exploratoire, déclaré comme
tel avant le calcul.

## 7. Puissance (résumé ; détail dans l'analyse de puissance)

Vraisemblance de planification : les 8 groupes de R-47 (déjà vus). Moyennes de classe (log₁₀ R / T2) : socle −0,73,
sables −0,53, calcaires +0,69 ; écart-type entre groupes de socle 0,53 ; grille σ = 0,3 ; 0,5 ; 0,7. Scénarios :
différences entre classes telles que vues, réduites de moitié, au quart, nulles (faux positifs), ou seuls les
calcaires à part. Plans : 3 classes de 3 à 8 groupes, plans inégaux (socle 6 ; sables 4 ou 5 ; calcaires 4 ou 3),
2 classes sans calcaires. Résultats : section 12.

## 8. Décision

- **H-A1 soutenue (confirmatoire)** : « une correction par classe de roche se généralise » passe de *aucune* à
  *soutenue* (après relecture). Une carte T2A (T2 × facteur de classe appris sur tous les groupes neufs, classe carte
  là où il n'y a pas de coupe) est **proposée** au porteur comme valeur centrale dans les classes couvertes ; sa
  construction est une étape à part, sans recalcul du test.
- **H-A1 non soutenue** : la classe de roche n'apporte rien au-delà du niveau aux échelles testées ; T2 (ou T2
  décalée selon T-H2.2) reste la valeur centrale ; la piste passe aux covariables continues (étape T-H2.9).
- **H-A2** (exploratoire) : positive, elle justifie de demander les coupes plutôt que de se fier à la carte
  (argument pour X-MEAH) ; négative, la carte suffit pour transférer.
- La validation prospective de T2L (section 5) est publiée avec son verdict propre, déjà fixé en R-47.

## 9. Ce qui reste à l'étape T-H2.4

Écrire le script de test **avant** l'ouverture des données (commit daté) ; publier la table de classes (section 4)
avant d'ouvrir les recharges ; appliquer ce protocole sans le modifier. Données requises : D-RECHARGE-REF (séries de
niveaux d'au moins 2 ans ou chlorure de forages neufs, 4 à 6 groupes par classe), coupes de forage (D-FORAGES-MEAH ;
zone ZH10 de BushProof si reçue), D-SY si possible, et le dépôt scellé de T-H2.1 pour les références de chlorure.

## 10. Limites

- Le Sy par défaut diffère entre socle et sédimentaire : il crée à lui seul un écart entre classes pour les
  références à fluctuation de nappe. La règle de robustesse (section 6) le contrôle sans le supprimer.
- La vraisemblance de planification vient de 8 groupes du Grand Sud, dont un seul de sables et un seul de calcaires :
  l'écart entre classes peut être bien plus faible ailleurs (scénarios « moitié » et « quart »).
- Bilan de chlorure et fluctuation de nappe ne mesurent pas la même recharge (long terme diffus ; saisonnière
  locale) ; les deux sources sont publiées séparément en sensibilité.
- Les coupes du ministère décrivent souvent mal les crépines ; la règle de repli (plus grande épaisseur saturée)
  peut classer en socle un forage qui capte surtout les altérites.
- Une classe n'entre dans le test que si elle réunit au moins 3 groupes (en dessous, M2c s'y replie sur M1 et
  n'apprend rien) ; ses groupes sont alors publiés à part. Les grès et le volcanique y entrent comme classes à part
  entière s'ils atteignent ce seuil.

## 11. Journal des modifications

- 16/11/2026 : version initiale (premier jet au critère de R-47 abandonné avant toute donnée, section 2).

## 12. Résultats de l'analyse de puissance

500 tirages par case, 199 permutations par tirage, graine 20261116 ([rapport](puissance_correction_aquifere.md),
[table](puissance_correction_aquifere.csv)).

- **Données vues** (descriptif) : avec un seul groupe en sables et en calcaires, M2c ne peut rien apprendre hors du
  socle ; permutation p = 0,22, critère de R-47 p = 0,08 (rapport des erreurs 0,89) : l'échec de R-47 se retrouve.
- **H-A1, 3 classes de k groupes, σ = 0,5 (écart observé)** : 58 % (k = 3), 67 % (k = 4), **88 %** (k = 5),
  86 % (k = 6), 95 % (k = 8) si les écarts entre classes sont ceux vus ; de 71 à 92 % si seuls les calcaires se
  distinguent. σ = 0,7 : 59 à 74 % de k = 5 à 8. Écarts réduits de moitié : 34 % à k = 5 (73 % si σ = 0,3).
- **Faux positifs** : 3 à 6 % (scénario nul), et 4 à 6 % avec des classes tirées au hasard : le test est au niveau
  annoncé. Le critère de R-47 a, à k = 5 et σ = 0,5, une puissance de 43 % seulement.
- **Plans inégaux** (σ = 0,5, écarts vus) : socle 6, sables 4, calcaires 4 : 73 % ; socle 6, sables 5,
  calcaires 3 : 69 %.
- **Sans calcaires** (socle et sables seuls) : 0 à 12 % dans tous les cas : socle et sables ne diffèrent presque pas
  dans les données vues (−0,73 contre −0,53).
- **Comparaison à T2** (abandonnée) : 52 à 73 % de « réussites » dans le scénario nul avec σ = 0,3 ; elle mesure le
  niveau (section 2).

**Condition de puissance fixée** : H-A1 est **confirmatoire** si au moins **5 groupes de classe déterminée dans
chacune d'au moins 3 classes, dont les calcaires** (puissance de 86 à 95 % pour les écarts vus et σ ≤ 0,5 ; elle
reste sous 80 % si les écarts réels sont deux fois plus faibles, ce qui est déclaré). Avec 4 groupes par classe ou un
plan inégal : exploratoire (67 à 73 %). Sans calcaires : H-A1 n'est pas testée comme confirmatoire (puissance
≤ 12 %), seulement décrite. La cible de collecte « 4 à 6 groupes par classe » de D-RECHARGE-REF devient donc
**au moins 5 groupes par classe, calcaires compris**.
