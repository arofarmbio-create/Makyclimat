# Protocole : nappe régionale profonde — inverser le raisonnement depuis la base

*Rédigé le 09/11/2026, **avant** tout calcul de ce protocole. Suite du bilan de chlorure et du test des puits à sec.
Toute modification sera datée en section 9.*

## 1. Point de départ : les inversions comme indice

Deux tests indépendants rangent les zones du Grand Sud **à l'envers** de nos cartes de recharge :
- puits à sec 2024-2025 : T2 sépare à l'envers (AUC 0,450) ;
- bilan de chlorure (analyse après coup, 36 blocs) : T2 et T2L ordonnent les zones à l'envers (Spearman −0,22 à −0,33).

Idée du porteur du projet : **ces inversions ne sont pas un mauvais signe ; elles disent qu'il faut inverser le
raisonnement depuis la base.** Nos cartes supposent que l'eau d'un forage vient de la pluie tombée au-dessus (recharge
locale et verticale). La littérature du Grand Sud décrit autre chose (`biblio_hydrogeologie_grand_sud.md`) :
- des nappes peu profondes et des nappes profondes, séparées par un substratum ;
- une nappe générale alimentée **à distance**, depuis les hautes terres du socle et l'Isalo ;
- des pics de recharge lissés avec la profondeur (isotopes) ;
- une recharge épisodique (AVSF 2016 ; Taylor et al. 2013).

**Raisonnement inversé** : partir de la nappe régionale (où elle se recharge, comment elle s'écoule, ce qu'elle
accumule en chemin), puis seulement descendre au local. Si ce cadre est juste, le chlorure d'un forage reflète son
**trajet** dans la nappe régionale plus que la pluie locale, et appliquer un bilan local (T2, ou un bilan de chlorure
supposé vertical) produit mécaniquement des rangs inversés.

## 2. Ce qui est déjà connu (à déclarer)

- Vu : la médiane du chlorure par zone (blocs de 20 km et zones en chaîne) et son accord avec T2 et T2L.
- **Pas encore regardé** : la relation du chlorure avec le niveau piézométrique, la profondeur captée et la distance
  le long de l'écoulement ; la relation des puits à sec avec ces mêmes grandeurs.

## 3. Données

Forages BushProof (Al-Zoubaidy, Monteleone et Bünzli 2023), mêmes 538 forages qu'au bilan de chlorure (mêmes
filtres) :
- **charge hydraulique** h = `NivPiezo_m` (altitude de la nappe, m) ; si absente, `Alt_m` − `SWL_m` ;
- **profondeur captée** z = base de la crépine la plus profonde (max des `BasCrep*_m`) ; si absente, forage exclu de
  H-D2 ;
- type d'aquifère `TypeAquif1` ; chlorure `Cl-_mg/l`.
Puits à sec : mêmes 87 cas et 1 452 forages de référence que `puits_a_sec.md`.

## 4. Hypothèses (fixées avant calcul)

Inférence : corrélation de Spearman au niveau du forage ; intervalle à 95 % par rééchantillonnage de blocs de 20 km
(2 000 tirages, graine 20261109), parce que les forages voisins ne sont pas indépendants.

- **H-D1 (écoulement régional, principale)** : le chlorure diminue quand la charge augmente (l'eau se charge en sels
  vers l'aval) : ρ(Cl, h) < 0, intervalle entièrement sous 0. Publiée aussi par type d'aquifère (au moins 30
  forages).
- **H-D2 (profondeur)** : le chlorure dépend de la profondeur captée : intervalle de ρ(Cl, z) sans 0 (bilatéral ; le
  sens n'est pas connu d'avance : eau profonde plus ancienne et plus chargée, ou eau venue de loin et plus douce).
- **H-D3 (le régional explique mieux que le local)** : |ρ(Cl, h)| > |ρ(Cl, P)|, P = pluie locale de la maille ;
  différence avec intervalle sans 0.
- **H-D4 (les inversions s'expliquent)** : au niveau des 36 blocs, la corrélation partielle de Spearman entre T2 et la
  recharge par chlorure (scénario central), à charge médiane du bloc fixée, n'est plus négative (≥ 0), alors que la
  corrélation brute l'est. Descriptif si les 36 blocs donnent un intervalle trop large.
- **H-D5 (puits à sec)** : les puits à sec sont à une charge plus basse ou plus haute que la référence (AUC de la
  charge, bilatéral, intervalle sans 0,5). Descriptif du sens.

**Contrôle préalable (leçon du test karst)** : la référence « locale » doit échouer pour que le test ait un sens. On
publie d'abord ρ(Cl, P) ; si |ρ(Cl, P)| ≥ 0,3 avec un intervalle sans 0, le cadre local n'échoue pas, et H-D3 est
déclarée sans objet.

## 5. Décision

- H-D1 et H-D3 soutenues : le cadre « nappe régionale » devient le cadre de travail du module M3 pour le Grand Sud.
  Conséquences prévues : (a) un bilan de chlorure **le long des lignes d'écoulement** (recharge en amont) remplace le
  bilan vertical ; (b) la recharge est rattachée aux zones d'alimentation (hautes terres, Isalo) plutôt qu'à la maille
  ; (c) les bassins hydrogéologiques sont refaits avec la charge mesurée des forages.
- Sinon : le cadre local reste ; les inversions restent inexpliquées et sont publiées comme telles.

## 6. Sorties

`validation/nappe_regionale.md` (corrélations, intervalles, par type d'aquifère, verdicts) ; valeurs agrégées
seulement, données brutes hors dépôt.

## 7. Limites

- Charge mesurée à des dates différentes (pas de campagne synchrone) ; niveau statique parfois mesuré à la foration.
- Zone ZH10 absente ; forages surtout dans le socle fracturé.
- Une corrélation chlorure-charge peut aussi venir de l'altitude (embruns plus forts près de la côte, en bas) : on
  publie ρ(Cl, h) à distance à la côte fixée (corrélation partielle), à titre descriptif.

## 8. Lien avec la littérature

Ce cadre reprend les observations du Grand Sud (AVSF 2016, citant Aurouze 1959, Guyot 2002 ; isotopes du plateau
Mahafaly) et la notion de recharge à distance. Ce que ce protocole ajoute : le tester sur des centaines de forages
avec leur charge, leur profondeur et leur chimie, et relier ce cadre aux échecs des cartes de recharge locales.

## 9. Journal des modifications

- 09/11/2026 : version initiale.
- 09/11/2026 (avant le calcul, demande du porteur du projet) : **la géologie reste le guide.** Ce qui vaut dans le
  socle fracturé du Grand Sud ne vaut pas forcément dans les bassins sédimentaires (Morondava, Mahajanga) ni sur la
  côte : les résultats seront publiés **par type d'aquifère** et ne seront pas généralisés hors du domaine testé.
  Trois autres origines du chlorure, à ne pas confondre avec un trajet dans la nappe régionale, sont déclarées comme
  explications concurrentes : (1) **l'intrusion d'eau de mer** près de la côte (forages à moins de 5 km déjà exclus ;
  la corrélation partielle à distance à la côte fixée sert de contrôle) ; (2) **les eaux fossiles**, anciennes et
  piégées, qui ne sont pas une intrusion actuelle ; (3) **les ions venus des sols et des roches** (dissolution,
  évaporites, sédiments marins anciens). Contrôle prévu, descriptif : rapport Cl/Na (proche de 1,17 en masse pour l'eau
  de mer et les embruns ; nettement plus bas si le sodium vient des roches) et part du chlorure dans la minéralisation,
  par type d'aquifère.
