# Plan de mesures pour rendre robustes les résultats sur la recharge des nappes

*Rédigé le 09/11/2026 à partir de `analyse_puissance.md`, `combinaison_preuves.md`, `nappe_regionale.md` et des
protocoles de la recharge. Document de travail pour les demandes au ministère de l'Eau (MEAH) et aux partenaires.*

## 1. Pourquoi ce plan

Les tests de la recharge du Grand Sud vont dans le même sens (T2 trop forte, T2L dans le bon sens), mais aucun n'est
encore robuste. L'analyse de puissance en donne les causes, chiffrées :
- trop peu d'unités indépendantes : 8 groupes de sites de fluctuation, tous dans le Sud et presque tous dans le socle ;
- une dispersion entre sites (0,53 en log₁₀) plus grande que la précision de chaque mesure (0,29) ;
- deux paramètres jamais mesurés à Madagascar : le **chlorure de la pluie** (il fait basculer le verdict) et le
  **rendement spécifique** Sy (incertitude d'un facteur 3 à 5 sur chaque recharge mesurée) ;
- un désaccord entre le modèle MERRA-2 (dépôt de chlorure 3 500 à 11 700 mg/m²/an) et les mesures de terrain voisines
  (260 à 3 300).

## 2. Mesures prioritaires

| Priorité | Mesure | Combien, où | Ce qu'elle tranche |
|---|---|---|---|
| 1 | **Chlorure de la pluie** (collecteurs de pluie ; analyses mensuelles de Cl, Na et Br) | 4 à 5 collecteurs sur un transect côte-intérieur du Grand Sud (environ 5, 30, 100 et plus de 150 km de la côte), une saison des pluies | Le dépôt de chlorure, donc le verdict entre T2 et T2L (`combinaison_preuves.md`) ; la crédibilité de MERRA-2. Le rapport Cl/Br sépare le chlorure de l'atmosphère de celui des roches |
| 2 | **Séries de niveaux** (capteurs automatiques, pas horaire à journalier) | Par classe d'aquifère (socle, sables et alluvions, karst) : au moins 4 à 6 groupes de sites distants de plus de 20 km, 2 sites par groupe, au moins 2 ans | La correction locale (T2L) par classe ; la puissance devient suffisante (au moins 80 %) si la dispersion est réduite de moitié par une classification plus fine |
| 3 | **Rendement spécifique Sy** | Sur une partie des sites de la priorité 2 : essais de pompage longs avec piézomètre d'observation, ou géophysique (résonance magnétique des protons) | Divise l'incertitude des recharges mesurées. **Les essais sur un seul forage (551 dans BushProof) donnent surtout la transmissivité, pas Sy** |
| 4 | **Paires de forages à deux profondeurs** (isotopes stables, tritium, chimie complète) | Une dizaine de sites où une nappe peu profonde et une nappe profonde sont captées côte à côte | La recharge étagée dans le temps (H-D6) : âge et minéralisation selon la profondeur |
| 5 | **Données existantes du ministère** (séries de niveaux, analyses chimiques, rapports de forage) | Toutes régions, en priorité hors du Grand Sud | Sortir du Grand Sud et du socle ; test prospectif des cartes figées |

## 3. Emplacements prioritaires (d'après nos échecs)

- **Karst hors de Toliara** : nord du plateau Mahafaly, Bemaraha, Namoroka (aujourd'hui un seul groupe de sites, près
  de Toliara).
- **Sables et alluvions hors de l'Androy** : côte Ouest (Morombe, Morondava).
- **Socle hors de l'Androy et de l'Anosy**, et socle en climat humide (Hautes Terres, Est) : aucun site aujourd'hui.
- **Transect côte-intérieur** pour le chlorure de la pluie : le dépôt varie surtout avec la distance à la mer.

## 3 bis. Classer les sites par leur coupe de forage (ajout du 09/11/2026)

Les cartes mondiales ne suffisent pas à classer un site ponctuel : la GLiM range les sables de l'Androy et les puits de
Toliara dans la même classe, et contredit le BGS pour un site sur douze (`journal_recherche.md`, GLiM vectorielle).
Chaque nouveau site doit avoir sa **coupe lithologique** (rapport de forage). Objectif : au moins 4 groupes
indépendants dans chacune des classes sables et alluvions, socle métamorphique, granites, et calcaires (aujourd'hui :
3, 3, 1 et 0).

## 4. Combien de sites pour un test prospectif des cartes figées

Pour montrer qu'une carte retrouve au moins 60 % des sites (borne basse de l'intervalle au-dessus de 60 %, puissance
80 %) : **41 nouveaux sites indépendants** si la carte en retrouve vraiment 80 %, 76 si 75 %, 177 si 70 %
(`analyse_puissance.md`, section 4).

## 5. Partenaires possibles

- Ministère de l'Eau, de l'Assainissement et de l'Hygiène (MEAH) : séries et analyses existantes (demande en cours de
  préparation, `demande_donnees_ministere.md`).
- Observatoire GROSoM et laboratoire METIS-IPSL (S. Carrière) : réseau de suivi dans le Sud-Ouest ; le suivi de la
  chimie de la pluie n'y a pas été fait « en raison des difficultés d'accès » (Carrière et al. 2023).
- BushProof et la DDC : base complète (zone ZH10, base Excel) par le formulaire de contact du site
  hydro-madagascar.
- ONG de l'eau présentes dans le Sud (forages et suivi).

## 6. Ce que chaque résultat permettra d'écrire dans la thèse

- Avec la priorité 1 seule : un verdict sur T2 contre T2L dans le Grand Sud, et une validation de MERRA-2 pour le dépôt
  de chlorure dans l'océan Indien occidental.
- Avec les priorités 1 à 3 : une correction locale de la recharge testée par classe d'aquifère, avec une puissance
  suffisante.
- Avec la priorité 4 : une première mesure du retard de la recharge des nappes profondes.
- Avec la priorité 5 : un test prospectif des cartes figées hors du Grand Sud.
