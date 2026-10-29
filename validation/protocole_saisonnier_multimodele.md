# Protocole : prévision saisonnière hybride (multi-modèles C3S + ENSO/IOD) par région

*Rédigé le 29/10/2026, **avant** tout calcul de score. Les modifications seront datées en section 7. Cahier des
charges §5 (comparer plusieurs organismes et modèles indépendants), §8 (approches 1 et 3), §9 (horizon saisonnier),
§13 (validation sans fuite).*

## 1. Question

À la date d'émission de début octobre, une combinaison de la moyenne multi-modèles C3S (10 systèmes, 8 centres) et
des indices océaniques ENSO (ONI) et IOD (DMI) prévoit-elle mieux la pluie régionale de novembre-janvier et de
janvier-mars que :
- le modèle statistique ENSO/IOD seul ;
- chaque modèle dynamique seul ;
- la moyenne multi-modèles seule ?

## 2. Nouveauté revendiquée (à confirmer par la revue de littérature)

- Comparaison systématique, **région par région**, des 10 systèmes C3S opérationnels pour Madagascar, recalibrés sur
  CHIRPS. Aucune comparaison de ce type n'a été trouvée lors de la recherche du 29/10/2026.
- Modèle hybride statistique-dynamique, où l'IOD est un prédicteur explicite à côté des modèles dynamiques. On teste
  ainsi si les modèles captent déjà le signal de l'océan Indien.
- Même cadre de validation que le modèle statistique déjà publié (`validation/teleconnexions.md`), donc les résultats
  sont directement comparables. Méthode transférable par `config/countries`.

## 3. Données

- Prévisions : C3S `seasonal-monthly-single-levels`, lancées le 1er octobre, tous les membres, maille 1°.
  Rétroprévisions 1993-2016 (24 saisons) ; prévision opérationnelle d'octobre 2026.
  Script : `scripts/build_c3s_seasonal.py`.
- Observations : pluie CHIRPS mensuelle par région, moyenne pondérée par la surface des fokontany (même fonction que
  le modèle ENSO/IOD).
- Indices : ONI de juillet-septembre (NOAA CPC) et DMI de juillet-septembre (ERSST v5), connus avant l'émission.

## 4. Cibles et prédicteurs

- Cibles : cumul de novembre-janvier (échéances 2 à 4) et de janvier-mars (échéances 4 à 6). La saison novembre-avril
  n'est pas couverte : avril serait l'échéance 7.
- Prédicteur d'un système : cumul régional de sa moyenne d'ensemble sur les mois cibles, la région étant la maille la
  plus proche de chaque fokontany, pondérée par la surface.
- Moyenne multi-modèles (MME) : moyenne des anomalies standardisées des systèmes disponibles. La standardisation est
  recalculée **sans la saison testée**.

## 5. Approches comparées (toutes linéaires, moindres carrés)

| Code | Prédicteurs |
|---|---|
| `stat_oni` | ONI |
| `stat_oni_dmi` | ONI, DMI |
| `sys:<centre>_<système>` | prédicteur du système (10 approches) |
| `mme` | MME |
| `hybride` | MME, DMI (**approche principale, fixée à l'avance**) |
| `hybride_complet` | MME, ONI, DMI |

## 6. Validation et critères

- Validation croisée en laissant une saison de côté : corrélation, MSSS par rapport à la climatologie (également sans
  la saison testée).
- Test chronologique : ajustement sur les saisons terminées jusqu'en 2008 (15), évaluation sur 2009-2017 (9).
- Permutation unilatérale (300 tirages, toute la procédure refaite à chaque tirage), puis contrôle des tests multiples
  (Benjamini-Hochberg, 10 %), pour chaque cible et chaque approche.
- Une région est **prévisible** par une approche si MSSS LOO > 0, MSSS chronologique > 0 et corrélation significative
  (même règle que `validation/teleconnexions.md`).
- **H1** : la MME a plus de régions prévisibles et un MSSS médian plus élevé que chaque système seul.
- **H2** : l'hybride bat la MME seule dans plus de la moitié des régions (test du signe).
- **H3** : l'hybride bat le modèle statistique ONI + DMI dans plus de la moitié des régions (test du signe).
- La prévision 2026-2027 n'est publiée que pour les régions prévisibles selon l'**approche principale**. Aucun choix
  de la meilleure approche après coup.
- Limite connue : 24 saisons seulement. La prévision opérationnelle compte plus de membres que les rétroprévisions
  (par exemple 51 contre 25 pour ECMWF), donc sa moyenne d'ensemble est un peu moins dispersée.

## 7. Journal des modifications

- 29/10/2026 : version initiale.
