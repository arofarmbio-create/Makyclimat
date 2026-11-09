# Recharge du karst (T2K)

Généré le 2026-11-09 par `scripts/recharge_karst.py`, selon `validation/protocole_recharge_karst.md` (fixé avant le calcul). Part karstique et mesures de référence : Wan, Döll et Müller Schmied (2024), figshare 23592666, CC BY 4.0. Calcul local.

## Part de la pluie qui recharge le karst (mailles mesurées, hors Madagascar)

| Seuil de part karstique | Climat | Mailles | R/P 10 % | R/P médiane | R/P 90 % |
|---|---|---|---|---|---|
| f ≥ 0.3 (principal) | aride | 47 | 0.013 | 0.072 | 0.305 |
| f ≥ 0.3 (principal) | humide | 32 | 0.049 | 0.289 | 0.579 |
| f ≥ 0.5 (sensibilité) | aride | 21 | 0.018 | 0.097 | 0.352 |
| f ≥ 0.5 (sensibilité) | humide | 24 | 0.110 | 0.329 | 0.591 |

## Emprise du karst à Madagascar (grille à 0,5°)

261 mailles sur 650 avec f > 0 ; 129 avec f ≥ 0.3. Recharge médiane des mailles avec f > 0 : T2 63 → T2K 163 mm/an (sensibilité f ≥ 0.5 : 178).

| Zone (maille la plus proche) | f | Pluie | T2 | T2K (intervalle) |
|---|---|---|---|---|
| Toliara | 0.79 | 452 | 20 | 30 (6 à 131) |
| Plateau Mahafaly (Betioky) | 0.61 | 647 | 33 | 41 (9 à 186) |
| Bemaraha | 0.24 | 1150 | 33 | 106 (21 à 292) |
| Ankarana | 0.06 | 1475 | 183 | 197 (56 à 921) |
| Mahajanga | 0.41 | 1472 | 7 | 178 (30 à 370) |

## H-K1 : non-régression sur les références de H-C6

T2 : 3 sur 8 ; T2K : 3 sur 8. **H-K1 soutenue**.

## H-K2 : puits GROSoM (contrôle, un seul groupe de sites)

| Puits | f | Mesurée | T2 (intervalle) | T2K (intervalle) | Dans T2K |
|---|---|---|---|---|---|
| Maroarivo | 0.61 | 185 | 38 (11 à 195) | 43 (9 à 196) | oui |
| Ambatofotsy | 0.61 | 96 | 38 (11 à 195) | 43 (9 à 196) | oui |
| Ankandy | 0.61 | 192 | 38 (11 à 195) | 43 (9 à 196) | oui |
| Ankazomanga_P06 | 0.61 | 80 | 38 (11 à 195) | 43 (9 à 196) | oui |
| Ankazomanga_P01 | 0.61 | 195 | 38 (11 à 195) | 43 (9 à 196) | oui |

5 sur 5 (T2 : 5). **H-K2 soutenue** (règle : au moins 3).

## Validation prospective

Carte figée le 2026-11-09 : `inputs/hydrogeologie/recharge_t2k.csv`, SHA-256 `c844a8bcc417ef3f59c86562a2af77f68177f81a99f944d4819a8baf6a6e1e4a` (fin de ligne LF). Réussite future si au moins 60 % des nouveaux sites karstiques hors Toliara sont retrouvés.

## Décision (fixée avant le calcul)

T2K remplace T2 dans les mailles avec f > 0 ; l'atlas par sous-bassin est refait.

