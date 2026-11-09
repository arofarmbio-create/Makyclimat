# Protocole : combinaison des preuves sur la recharge du Grand Sud

*Rédigé le 09/11/2026, **avant** le calcul de la combinaison. Suite de `analyse_puissance.md` : nos tests séparés
manquent de puissance ; on rassemble les lignes de preuve dans un seul cadre. Toute modification sera datée en
section 7.*

## 1. Statut honnête

Toutes les lignes de preuve ci-dessous **ont déjà été vues**. La combinaison d'aujourd'hui est une **synthèse
rétrospective** : elle résume des résultats connus et ne compte pas comme une preuve nouvelle. Les règles fixées ici
s'appliqueront telles quelles aux preuves **futures** (MERRA-2, nouvelles mesures), qui, elles, seront prospectives.

## 2. Deux questions

- **Q1** : dans le Grand Sud, T2 surestime-t-elle la recharge ?
- **Q2** : T2L (corrigée par les mesures malgaches) est-elle plus juste que T2 ?

## 3. Lignes de preuve et statistique de chaque ligne

Chaque ligne est ramenée à un score z unilatéral (positif = dans le sens de la question), à partir de ses **unités
indépendantes** :

| Ligne | Unités | Q1 : z | Q2 : z |
|---|---|---|---|
| L1 fluctuation de nappe (`recharge_locale_sites.csv`) | groupes de sites (moins de 20 km) | test des rangs signés de Wilcoxon sur log₁₀(T2 / mesurée), médiane par groupe | Wilcoxon sur la différence des erreurs absolues, T2 − T2L (prédictions des groupes laissés de côté), médiane par groupe |
| L2 puits à sec (`puits_a_sec.md`) | blocs de 20 km | sans objet | différence d'AUC / erreur type (intervalle à 95 % / 3,92) |
| L3 bilan de chlorure (`recharge_chlorure_blocs_zones.csv`, analyse après coup) | blocs de 20 km | Wilcoxon sur log₁₀(T2 / chlorure) | Wilcoxon sur la différence des erreurs absolues, blocs du domaine de T2L |

Wilcoxon : p unilatéral exact (ou approché au-delà de 25 unités), z = Φ⁻¹(1 − p).

## 4. Combinaison

Z de Stouffer pondéré par la racine du nombre d'unités : Z = Σ wᵢ zᵢ / √(Σ wᵢ²), wᵢ = √nᵢ.

- La ligne L3 dépend du dépôt de chlorure : la combinaison est calculée **pour chacun des trois scénarios**. Le
  scénario retenu sera **celui dont le dépôt est le plus proche de MERRA-2** (médiane des mailles terrestres, scénario à
  P = 500 mm et à la distance médiane des blocs à la côte), dès que MERRA-2 sera disponible ; d'ici là, aucun scénario
  n'est retenu.
- **Verdict** pour une question : « établi » si Z ≥ 1,96 dans le scénario retenu **et** aucune ligne n'a z ≤ −1,96
  (contradiction forte) ; « indice » si 1,0 ≤ Z < 1,96 ; « non établi » sinon.
- **Dépendances déclarées** : L2 et L3 couvrent la même région (les mêmes forages BushProof servent de référence en L2
  et de mesure en L3) ; L3 est fragilisée par le chlorure venu des roches (Cl/Na médian 0,96, `nappe_regionale.md`).
  La combinaison est aussi publiée **sans L3**.

## 5. Preuves futures

Toute nouvelle ligne (sites de fluctuation hors des groupes actuels, nouvelles analyses de chlorure, puits à sec d'une
autre zone) est ajoutée avec les mêmes règles, sans modifier les lignes existantes. Une ligne nouvelle n'est
« prospective » que si ses données n'ont pas servi à construire T2L.

## 6. Sorties

`validation/combinaison_preuves.md` ; script `scripts/combinaison_preuves.py`.

## 7. Journal des modifications

- 09/11/2026 : version initiale.
- 09/11/2026 (après MERRA-2) : la règle désigne le scénario **haut** (MERRA-2, mailles terrestres à 30-100 km :
  médiane 5 786 mg/m²/an de chlorure ; scénario haut à 97 km : environ 1 980). Verdicts appliqués tels quels : Q1
  « indice », Q2 « non établi ». **Réserve déclarée** : MERRA-2 dépasse toutes les mesures de terrain connues (côte du
  Kenya 2 435 à 3 334 ; intérieur sud-africain 260) d'un facteur 2 à 13, et même le scénario haut d'un facteur 3 ; la
  moitié de son dépôt vient de la sédimentation des grosses particules, et les mailles côtières contiennent de la mer.
  La règle supposait MERRA-2 crédible : sa validation sur des sites mesurés (Kwale, Afrique du Sud) devient nécessaire
  avant de lui donner le dernier mot. Les verdicts ne sont pas modifiés.
- 09/11/2026 (avant la validation de MERRA-2) : **validation de MERRA-2 aux sites mesurés**, même collection et mêmes
  variables, 2011-2020 (120 mois). Sites : Kwale, Kenya, station MWC (39,378 E ; 4,462 S ; dépôt humide mesuré
  3 334 mg/m²/an, Ferrer, Folch et Thomas 2019) ; intérieur semi-aride sud-africain, stations de Van Wyk et al. (2011)
  Kuruman (23,43 E ; 27,45 S), Stella (24,86 E ; 26,55 S) et Alldays (29,10 E ; 22,67 S), dépôt total de l'intérieur
  260 mg/m²/an (p. 153-154). Comparaison : Kwale, dépôt humide MERRA-2 (humide + lessivage) ; intérieur, dépôt total
  MERRA-2 (médiane des trois stations). **Règle** : MERRA-2 est jugé crédible s'il est à moins d'un facteur 2 des deux
  références ; sinon, un facteur de correction f = moyenne géométrique des rapports mesuré / MERRA-2 aux deux sites est
  appliqué aux mailles du Grand Sud, et le scénario est choisi à nouveau avec le dépôt corrigé. Les verdicts de la
  combinaison sont alors recalculés avec ce scénario ; les deux versions (brute et corrigée) sont publiées.
- 09/11/2026 (validation de MERRA-2, `data/mdg/depot_chlorure_merra2_validation.csv`) : Kwale, dépôt humide MERRA-2
  11 043 contre 3 334 mesurés (rapport 0,30) ; intérieur sud-africain, dépôt total 452 (médiane de 3 stations) contre
  260 (rapport 0,58). MERRA-2 n'est pas à moins d'un facteur 2 des deux références : facteur de correction 0,42
  appliqué ; Grand Sud corrigé environ 2 400 mg/m²/an à 30-100 km ; **scénario haut retenu, brut comme corrigé** ;
  verdicts inchangés (Q1 indice, Q2 non établie).
