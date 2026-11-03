# Protocole : validation prospective de la pluie par les stations météo MGMERL du Grand Sud

*Rédigé le 03/11/2026, **avant** toute extraction et tout calcul. Complète `protocole_e1_fusion_pluie.md` : E1 n'a
pu être jugée que sur 5 stations GSOD (test sans puissance), et ces stations sont en partie intégrées à CHIRPS.
Toute modification sera datée en section 8.*

## 1. Question

Sur des pluviomètres **indépendants** (hors du réseau international utilisé par CHIRPS), et sur des saisons
**postérieures** au réglage de la fusion, quelle version de la pluie est la plus proche de la mesure : CHIRPS,
IMERG Late, ERA5-Land, la moyenne simple B ou la fusion C ?

C'est une validation **prospective** : les poids de la fusion C sont gelés (triple collocation 2001-2015, `e1_tc.npz`)
et les stations n'ont jamais servi à rien régler.

## 2. Données

- Stations météo automatiques (Davis Vantage Vue) du réseau Tatirano, affichées publiquement sur MGMERL (onglet
  « St. Météorologiques ») : Fort Dauphin (−25,029 ; 46,969), Tsihombe (−25,316 ; 45,485), Farafangana (−22,818 ;
  47,829). Relevés journaliers depuis le 31/12/2025. Source citée : MGMERL.
- Les autres stations de l'inventaire MGMERL (RainMadagascar, PAM, WHH…) seront ajoutées si leurs relevés deviennent
  visibles, avec les mêmes règles.
- Extraction : lecture des tableaux affichés (aucune requête d'écriture) ; l'export CSV de la plateforme est réservé
  à l'organisation mWater. Données brutes hors du dépôt (`data/mdg/mgmerl_raw/meteo/`) ; seuls des scores agrégés
  sont publiés.
- Limite : l'extraction n'est pas automatisable aujourd'hui. Elle sera refaite à la fin de chaque saison des pluies
  (mai), et la date d'extraction sera notée.

## 3. Contrôle qualité (fixé avant de regarder les écarts aux produits)

1. Valeur journalière rejetée si négative ou supérieure à 400 mm.
2. **Pluviomètre bloqué** : un mois de saison des pluies (novembre à avril) est exclu si la station totalise moins de
   5 mm alors que la médiane des trois produits (CHIRPS, IMERG, ERA5-Land) à sa maille dépasse 50 mm ce mois-là. Le
   contrôle du 02/11 a déjà relevé ce cas (Tsihombe à 0 mm en décembre, janvier et mars).
3. Jour manquant : manquant, jamais zéro.
4. **Contrôle croisé** Fort Dauphin et station GSOD de Tolagnaro (environ 1 km) : sur les jours complets communs,
   rapport des cumuls et corrélation par pentade. Le pluviomètre Davis est jugé fiable si le rapport est compris entre
   0,7 et 1,3 et la corrélation dépasse 0,7 ; sinon ses scores sont publiés à part, signalés « douteux ».
5. Une station garde ses scores d'une saison si elle a au moins 15 pentades complètes de novembre à avril.

## 4. Méthode

- Échelle : pentade (comme E1) ; produits à la maille de 0,1° de la station (grille E1).
- C : fusion avec les poids gelés ; les sources sont ramenées à CHIRPS avec les moments de 2001-2015, sans réglage.
- Mesures : KGE (principal), biais, corrélation, erreur absolue moyenne ; par station et par saison.

## 5. Règle de décision

- Tant qu'il y a moins de 10 couples « station-saison » valides : résultats **descriptifs** seulement.
- À partir de 10 : test du signe unilatéral, comme H1-E1 (KGE de C contre celui de la meilleure source seule fixée
  sur l'apprentissage, IMERG) et H1-E1b (C contre B), au seuil de 5 %.

## 6. Ce qui n'est pas fait

Les stations ne servent jamais d'entrée au modèle ni à régler un seuil : elles jugent seulement.

## 7. Sorties

`validation/pluie_prospective.md` et CSV de scores ; journal et registre (R-35).

## 8. Journal des modifications

- 03/11/2026 : version initiale.
