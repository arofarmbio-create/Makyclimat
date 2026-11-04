# Protocole : recharge mesurée par la fluctuation des nappes dans le Grand Sud

*Rédigé le 04/11/2026, **avant** tout calcul. Complète `protocole_cadre_eaux_souterraines.md` (section 4) et
`protocole_carte_nappes.md` (H-C6). Motif : la recharge transférée d'Afrique (T2) surestime d'un facteur 3 à 30 aux 7
sites MGMERL utilisés en H-C6, ce qui rend le risque d'épuisement du Grand Sud trop optimiste. Toute modification sera
datée en section 7.*

## 1. Question

Quelle est la recharge annuelle des nappes du Grand Sud mesurée sur les nappes elles-mêmes, et de combien la
recharge transférée (T2) s'en écarte-t-elle ?

## 2. Données

- **Capteurs HT Analytics** (MGMERL, citer « MGMERL ») : 15 sites, lectures de juin 2019 au 31 mai 2026 (extraction
  complète du 04/11/2026), niveau en m sous le repère (valeurs négatives). Coordonnées :
  `inputs/mgmerl/mgmerl_dataloggers_ht_analytics_sites.csv`.
- **Observatoire GROSoM** (Carrière et al. 2021 ; IGRAC-GGIS) : 10 puits, mesures horaires 2014 à 2020, en cote
  (m au-dessus de la mer), ramenées en profondeur par l'altitude du sol de la fiche des puits. Licence des données non
  indiquée : usage de recherche cité, aucune redistribution des séries.

## 3. Contrôle qualité

Règles 1 à 6 de `protocole_nappes_mgmerl.md` (bornes, pics, sauts durables, conductivité, au moins 10 jours par mois,
au moins 24 mois), appliquées telles quelles aux deux sources.

## 4. Méthode (fluctuation de nappe, Healy et Cook 2002)

- **Principale** (identique à H-C6) : moyennes mensuelles ; recharge d'une saison = Sy × somme des remontées
  mensuelles de novembre à avril ; saison retenue si au moins 4 de ses 6 mois sont valides ; recharge du site = moyenne
  des saisons retenues.
- **Sensibilité** : moyennes journalières, somme des remontées journalières supérieures à 1 cm de novembre à avril (le
  pas mensuel manque les remontées brèves et sous-estime).
- **Sy** (comme H-C6) : socle 0,01 à 0,05 ; sédimentaire et non consolidé 0,05 à 0,15 ; groupe d'aquifère BGS de la
  maille la plus proche (`covariables_hc6.csv`). Recharge publiée en fourchette (Sy bas, Sy haut) et valeur centrale
  (milieu de la fourchette).
- **Comparaison** : au même point, rapport recharge mesurée (centrale) / T2. Mesure principale : médiane des rapports
  sur les sites retenus, avec intervalle de confiance par rééchantillonnage des sites (2 000 tirages).

## 5. Règle de décision (fixée avant calcul)

- Si au moins 80 % des sites retenus ont un rapport inférieur à 1 **et** si la borne haute de l'intervalle de
  confiance de la médiane est inférieure à 1, T2 est jugée **surestimée dans le Grand Sud** (au sud de 23° S). Une
  recharge corrigée est alors publiée **à côté** de T2 : T2 × médiane des rapports, pour les fokontany au sud de 23° S
  seulement, et le risque d'épuisement est recalculé avec elle (deuxième colonne, sans remplacer la première).
- Sinon, rien n'est corrigé et le résultat est publié tel quel.
- Limite connue : les sites sont peu nombreux et concentrés (Androy, Anosy, Atsimo-Atsinanana pour HT ; Toliara et
  côte d'Anosy pour GROSoM) ; la correction est une approximation régionale, pas une carte de recharge.

## 6. Sorties

`validation/recharge_fluctuation.md` et CSV par site (agrégés, sans séries) ; journal et registre (R-38, R-41).

## 7. Journal des modifications

- 04/11/2026 : version initiale.
