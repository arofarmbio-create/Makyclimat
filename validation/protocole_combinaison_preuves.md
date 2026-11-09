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
