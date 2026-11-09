# Protocole : recharge du karst (T2K)

*Rédigé le 09/11/2026, **avant** tout calcul et avant la réception de la grille de part karstique. Suite de H-R2 et
H-L1 (non soutenues) et de la revue `validation/revue_litterature_contributions.md`. Toute modification sera datée
en section 9.*

## 1. Question

T2 sous-estime fortement la recharge près de Toliara (20 mm/an transférés, 80 à 195 mm/an mesurés aux puits GROSoM),
où la nappe est en partie karstique. Wan, Döll et Müller Schmied (2024) ont montré, à l'échelle mondiale, que le
karst se recharge davantage et doit être traité à part. **Une recharge propre au karst, tirée des mesures mondiales et
sans aucune donnée malgache, corrige-t-elle T2 là où la roche est karstique, sans la dégrader ailleurs ?**

## 2. Ce qui est déjà connu (à déclarer)

Calcul exploratoire du 09/11/2026 (revue, section « Mise à jour ») sur les 821 mailles mesurées de Wan et al. : part
de la pluie qui recharge la nappe (R/P) en climat aride, médiane 0,032 sans karst et 0,072 quand le karst couvre au
moins 30 % de la maille (quantile à 90 % : 0,114 contre 0,305). Le seuil de 30 % et l'ordre de grandeur sont donc
connus avant ce protocole. Les puits GROSoM ont déjà été regardés : leur contrôle n'est pas une preuve.

## 3. Données

- Grille T2 (`recharge_transferee.csv`) : T2, intervalle de 80 %, pluie `LTA_P_mmpa`, aridité.
- Part karstique f de chaque maille malgache : grille mondiale à 0,5° de Wan et al. (figshare 23592666, CC BY 4.0,
  d'après WOKAM), maille la plus proche. Fichier `data/mdg/nappes_mondiales/fkarst_mdg.csv` (agent de
  téléchargement).
- Rapports de référence : les mailles mesurées de Wan et al. (`1_Ground-based-estimates.xlsx`, colonnes `fkarst`,
  `Obs_gwr/p`, `arid1_humid0`), **hors Madagascar**.

## 4. Méthode (fixée avant calcul)

1. Mailles de référence karstiques : f ≥ 0,3, hors Madagascar. Pour chaque climat (aride ou humide, colonne
   `arid1_humid0` de Wan et al.) : médiane r_k et quantiles à 10 et 90 % de R/P. Climat d'une maille malgache :
   aride si P/ETP < 0,5. Ce n'est peut-être pas exactement la définition de Wan et al. ; l'écart sera signalé.
2. Recharge karstique d'une maille malgache : K = r_k × P, intervalle [q10 × P ; q90 × P].
3. **Mélange selon la part karstique** : T2K = (1 − f) × T2 + f × K ; même mélange pour les bornes de l'intervalle.
   Une maille sans karst (f = 0) garde T2.
4. Sensibilité publiée sans changer la décision : seuil de référence f ≥ 0,5 au lieu de 0,3.

## 5. Hypothèses et contrôles (fixés avant calcul)

- **H-K1 (non-régression)** : sur les 8 références de H-C6 (même évaluation), T2K en place au moins autant que T2
  (3 sur 8).
- **H-K2 (contrôle karstique, pas une preuve)** : l'intervalle de T2K contient la valeur mesurée centrale d'au moins
  3 des 5 puits GROSoM retenus (T2 : 0 sur 5). Les 5 puits forment un seul groupe de sites : même réussi, ce contrôle
  vaut une seule information indépendante.
- **Contrôle d'emprise** : part des mailles malgaches avec f > 0 et f ≥ 0,3 ; on vérifie que les zones calcaires
  connues (plateau Mahafaly, Bemaraha, Ankarana) en font partie. Si la maille de Toliara a f = 0, la méthode ne peut
  pas y corriger T2 ; ce sera dit comme un échec de résolution, sans changer la règle.
- **Validation prospective** : carte T2K figée et publiée avec son empreinte SHA-256. Toute nouvelle mesure de
  recharge en zone karstique (hors Toliara) sera comparée à ces valeurs sans recalcul ; réussite si au moins 60 % des
  nouveaux sites karstiques sont retrouvés.

## 6. Décision

- Si H-K1 et H-K2 sont soutenues : T2K remplace T2 dans les mailles avec f > 0 ; l'atlas par sous-bassin est refait,
  en particulier les sous-bassins de Toliara, Morombe et Morondava. Les sous-bassins dont la classe de bilan change
  sont publiés.
- Sinon : T2 reste la valeur centrale ; T2K est publiée comme sensibilité et figée pour le test prospectif.

## 7. Sorties

`validation/recharge_karst.md`, `inputs/hydrogeologie/recharge_t2k.csv` (maille : f, T2, K, T2K, intervalle), calcul
local (grille T2 et séries hors dépôt). Les valeurs de f viennent d'un jeu sous CC BY 4.0 et peuvent être publiées
avec la citation de Wan et al. (2024).

## 8. Limites

- Grille de f à 0,5° (environ 55 km) : les petits affleurements calcaires et les limites fines du karst sont perdus.
  WOKAM vectoriel serait plus fin ; sa licence de republication n'est pas vérifiée.
- R/P du karst tiré de mailles mondiales de 0,5°, où la recharge est souvent mesurée à une autre échelle.
- Un seul groupe de sites karstiques mesurés à Madagascar.

## 9. Journal des modifications

- 09/11/2026 : version initiale.
- 09/11/2026 (après le calcul) : **erreur du protocole relevée, non corrigée après coup.** La section 5 affirmait que
  T2 place 0 des 5 puits GROSoM dans son intervalle. C'est faux : l'intervalle de 80 % de T2 (11 à 195 mm/an) les
  contient déjà tous les 5. H-K2 ne pouvait donc pas départager T2 et T2K. Les règles restent inchangées ; la décision
  d'application est soumise au porteur du projet (voir `validation/recharge_karst.md` et le journal).
- 09/11/2026 (décision du porteur du projet) : **option A**. T2 reste la valeur centrale ; T2K est conservée comme
  sensibilité, figée (SHA-256 dans `validation/recharge_karst.md`) pour le test prospectif. L'atlas n'est pas refait.
