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

