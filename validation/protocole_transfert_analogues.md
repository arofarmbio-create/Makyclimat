# Protocole : transfert de connaissances depuis des régions analogues (géologie et climat) vers Madagascar

*Rédigé le 04/11/2026, **avant** toute collecte de données d'analogues et tout calcul. Axe central de la thèse
(porteur du projet : « je compte beaucoup sur le transfert de connaissances, mais il faut le démontrer »). Prolonge
la section 10 de `protocole_carte_nappes.md` (H-C5, H-C6 : transfert depuis 134 sites africains, non confirmé à
Madagascar) et `protocole_recharge_fluctuation.md` (biais du transfert selon le type d'aquifère, observé après coup).
Toute modification sera datée en section 9.*

## 1. Idée

Madagascar a peu de mesures de nappe hors du Grand Sud. D'autres régions du monde, aux roches et climats semblables,
en ont beaucoup : l'Inde du Sud et le Sri Lanka (même socle précambrien, soudés à Madagascar dans le Gondwana),
l'Afrique de l'Est et de l'Ouest sur socle altéré, les bassins sédimentaires semi-arides. On prend leurs chiffres
publiés, on les vérifie, on en tire des règles, et on **démontre** sur les mesures malgaches indépendantes que ces
règles prédisent mieux que les références actuelles. Un transfert non démontré n'est pas utilisé comme résultat.

## 2. Analogie : définition fixée à l'avance

Deux lieux sont analogues s'ils sont proches selon une distance de Gower sur : classe lithologique (GLiM, niveau 1),
groupe d'aquifère (socle, sédimentaire consolidé, non consolidé, volcanique), indice d'aridité (P/ETP), pluie annuelle,
pente. Domaine d'applicabilité : un point malgache dont l'analogue le plus proche est au-delà du 95e centile des
distances au plus proche voisin entre sites sources est « hors domaine » ; il est signalé et exclu des tests.

## 3. Sources de chiffres (vérifiées avant usage : licence, définition, unités)

1. **Recharge** : base mondiale de recharge mesurée (Moeck et al. 2020, DOI 10.25678/0001NG) et sa mise à jour (Berghuijs
   et al. 2022) ; base africaine du BGS (déjà utilisée en H-C5).
2. **Porosité efficace (Sy)** : tableau tiré de la littérature (Inde du Sud : Maréchal, Dewandel et coll. ; Afrique de
   l'Ouest ; bassins sédimentaires), chaque valeur avec sa référence, sa méthode et son type de roche.
3. **Niveau statique** (plus tard, protocole précis à écrire avant collecte) : réseaux publics de suivi de régions
   analogues (Inde : Central Ground Water Board), si l'accès et la licence le permettent.

## 4. Hypothèses (fixées avant calcul)

- **H-T1 (recharge, transfert mondial par analogues)** : la recharge transférée depuis la base mondiale (plus proches
  analogues au sens de la section 2, k = 5, méthode T2 de H-C5) est plus proche de la recharge mesurée aux sites malgaches
  que T2 (base africaine seule). Mesure : erreur absolue sur le logarithme de la recharge, site par site, sur les 12
  sites malgaches retenus par `recharge_fluctuation.md` (et tout nouveau site mesuré). **Soutenue** si l'erreur est plus
  faible sur au moins 10 sites sur 12 (test du signe unilatéral, p < 0,05).
- **H-R1 (biais selon le type d'aquifère)**, observée le 04/11 : le transfert africain T2 surestime la recharge sur le
  socle et la sous-estime dans le sédimentaire. Elle ne peut pas être confirmée sur les 12 sites qui l'ont suggérée ;
  elle sera testée **sur la base mondiale** (validation en laissant un pays de côté) : signe de l'erreur de T2 selon le
  groupe d'aquifère, test exact de Fisher, p < 0,05.
- **H-T2 (le transfert garde l'ordre)** : la recharge transférée par H-T1 classe les 12 sites malgaches dans le même
  ordre que la mesure (Spearman ρ > 0, p < 0,05), et sépare socle et sédimentaire dans le bon sens.

## 5. Démontrer le transfert : trois niveaux de preuve

1. **Dans les sources** : validation en laissant un pays de côté (comme H-C5) ; le transfert doit battre une
   référence naïve (médiane du même groupe d'aquifère).
2. **À Madagascar, hors échantillon** : tests H-T1 et H-T2 sur des mesures malgaches jamais utilisées pour régler le
   transfert.
3. **Physique** : les chiffres transférés doivent rester dans les fourchettes publiées pour le même type de roche
   (section 3.2) ; un écart est signalé.

Conclusion autorisée selon le niveau atteint : « transfert démontré » (1 et 2 réussis), « transfert plausible » (1
réussi, 2 non concluant faute de sites), « transfert rejeté » (2 échoue).

## 6. Puissance et limites connues

12 sites malgaches seulement, concentrés dans le Sud : un échec de H-T1 peut venir du manque de puissance. Les sites
seront complétés au fil des données (ministère, autres réseaux), sans changer les règles.

## 7. Mise en œuvre

Téléchargement des bases par un agent dédié (licences d'abord, une requête à la fois) ; scripts testés sur données
simulées ; données brutes hors dépôt si la licence l'impose ; résultats agrégés publiés.

## 8. Sorties

`validation/transfert_analogues.md` ; tableau des Sy de la littérature (`validation/sy_litterature.csv`, avec
références) ; journal et registre (nouvelle entrée R-43).

## 9. Journal des modifications

- 04/11/2026 : version initiale.
- 04/11/2026, **avant tout calcul** : sources effectivement disponibles (vérifiées par l'agent, licences comprises).
  - **Source principale de H-T1 et H-R1** : compilation de Wan, Döll et Müller Schmied (2024, figshare
    10.6084/m9.figshare.23592666, CC BY 4.0) : 821 estimations de recharge mesurée regroupées par maille de 0,5°
    (Moeck, MacDonald, Mohan, Scanlon, Hartmann, Döll…), avec pluie, ETP, aridité, sol, pente, occupation du sol, méthode
    et niveau de confiance. Moeck et al. 2020 (CC0, 5 207 estimations) n'a que la position et la recharge : réservé à une
    vérification de robustesse. Berghuijs et al. 2022 ne contient que des grilles : non utilisé. Aucun site malgache ni
    sri-lankais.
  - **Type d'aquifère** (absent pour 709 des 821 sites) : attribué **à tous les sites, malgaches compris**, à partir de la
    carte lithologique mondiale GLiM (Hartmann et Moosdorf 2012), même règle partout : métamorphiques et plutoniques
    (mt, pa, pb, pi) → socle ; sédimentaires siliciclastiques, carbonatés et mixtes (ss, sc, sm) → sédimentaire ;
    sédiments non consolidés (su) → non consolidé ; volcaniques (va, vb, vi, py) → volcanique ; autres → inconnu
    (exclus des tests). Contrôle : accord entre cette règle et le type d'aquifère du BGS sur les sites africains
    (publié, sans critère de rejet).
  - Variables du transfert (distance de Gower) : pluie annuelle, ETP, aridité, type d'aquifère (GLiM), occupation du
    sol, pente ; mêmes définitions pour les sites sources et malgaches, tirées des mêmes produits.
- 04/11/2026, **avant tout calcul** : mise en œuvre.
  - GLiM utilisée : grille à 0,5° (Hartmann et Moosdorf 2012, PANGAEA 10.1594/PANGAEA.788537, CC BY 3.0), classe
    dominante de la maille (codes 1 à 16). Point sans classe (mer à 0,5°) : maille voisine la plus proche avec une classe.
  - Variables de la distance de Gower : pluie annuelle, ETP, aridité, type d'aquifère (GLiM). **Pente et occupation du
    sol exclues** : leurs définitions dans la compilation de Wan ne peuvent pas être reproduites pour les sites malgaches
    (vocabulaires et produits différents). Sites malgaches : pluie, ETP et aridité de la maille la plus proche de
    `covariables_hc6.csv` (définitions du BGS, reprises par la compilation). k = 5 analogues, prédiction = médiane des
    log-recharges des analogues.
  - Référence T2 de H-T1 : valeurs T2 déjà publiées aux sites (`recharge_fluctuation_sites.csv`), sans recalcul.
  - H-R1 sur la base mondiale : modèle « africain » = mêmes k = 5 analogues mais pris parmi les seuls sites africains de
    la compilation ; il prédit chaque site non africain ; surestimation = prédiction > mesure. Test exact de Fisher
    unilatéral : la surestimation est plus fréquente sur le socle que sur le sédimentaire et le non consolidé réunis.
  - Niveau 1 (sources) : modèle mondial en laissant un pays de côté, contre la référence naïve (médiane du même type
    d'aquifère parmi les autres pays) ; test du signe sur les pays (au moins 3 sites), comme H-C5.
- 04/11/2026, **après le premier calcul** (`transfert_analogues.md` : H-T1 soutenue, H-T2 et H-R1 non soutenues ;
  règle GLiM 0,5° d'accord avec le BGS sur 47 % seulement) : **typage du terrain au point** par la GLiM vectorielle
  (polygones, même classification et même règle de correspondance qu'en section 4 précisée le 04/11), à la place de la
  grille à 0,5°.
  - Statut : **reprise annoncée d'un test déjà fait** (risque de choix après coup). Les deux versions sont publiées
    côte à côte ; aucune n'est retenue sur la base de son résultat. La conclusion du protocole (démontré, plausible,
    rejeté) ne peut être relevée que si H-T1 **et** H-T2 réussissent avec la GLiM vectorielle **et** si l'accord avec le
    type du BGS sur les sites africains dépasse 70 % (sinon le typage reste jugé insuffisant).
  - Toutes les autres règles (variables, k = 5, sites, tests, seuils) restent inchangées.
  - Mise en œuvre : téléchargement lourd sur GitHub (workflow), qui ne renvoie que la classe GLiM aux points demandés.
- 04/11/2026, **avant tout calcul de ce test** : hypothèse **H-K1 (karst)**, suggérée par les résultats (les puits
  sédimentaires de la région de Toliara, en partie calcaires, sont sous-estimés) ; elle est donc **exploratoire à
  Madagascar** et ne peut y être confirmée qu'avec d'autres sites.
  - Variable : fraction karstique de la maille (WOKAM, carte mondiale des aquifères karstiques, Chen et al. 2017),
    même définition que la colonne fkarst de la compilation de Wan ; pour les sites malgaches, lue sur WOKAM au point
    (fraction 0 ou 1 selon que le point est dans un polygone karstique ; la définition exacte de fkarst sera vérifiée
    et notée avant le calcul).
  - **Test confirmatoire (sources, indépendant de Madagascar)** : ajout de la fraction karstique comme cinquième variable
    de la distance de Gower ; en laissant chaque pays de côté, le modèle avec karst bat le modèle sans karst dans plus
    de la moitié des pays (test du signe unilatéral, p < 0,05). **H-K1 soutenue** si ce test réussit.
  - **Test exploratoire (Madagascar)** : H-T1 et H-T2 recalculées avec la variable karst ; rapportées comme
    exploratoires, quelle qu'en soit l'issue.
  - Typage GLiM : version vectorielle (reprise du 04/11).
- 04/11/2026, **avant le calcul de H-K1** : définition de la fraction karstique vérifiée (documentation ReWaterGAP,
  résumé de Wan et al. 2024, WRR, doi:10.1029/2023WR036182, éq. 4) : f_karst = min(0,9 ; Σ part_i × aire karstique_i /
  aire continentale de la maille de 0,5°), part = 0,4 pour le karst discontinu et 0,9 pour le karst continu ou mixte.
  Sites malgaches : même formule appliquée à WOKAM v1 (BGR ; couche non redistribuée, licence BGR), valeurs dans
  `inputs/analogues/fkarst_mdg.csv` (0 pour les sites absents du fichier). La compilation de Wan fournit fkarst pour
  les sites sources (colonne « fkarst »).

