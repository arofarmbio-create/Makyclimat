# H-K1 : la fraction karstique améliore-t-elle le transfert par analogues ?

Généré le 2026-11-04 par `scripts/transfert_analogues.py --typage vectoriel --karst`, selon `validation/protocole_transfert_analogues.md` (H-K1, fixée avant le calcul). Karst : WOKAM v1 (Chen et al. 2017, BGR), formule de Wan et al. 2024 ; couche non redistribuée.

## Test confirmatoire (sources, indépendant de Madagascar)

En laissant chaque pays de côté, le modèle avec karst a une erreur plus faible que sans karst dans 8 pays sur 23 (6 égalités écartées) ; test du signe p = 0.953. Erreur médiane : sans karst 0.351, avec karst 0.354. **H-K1 non soutenue**.

## Exploratoire (Madagascar, 12 sites)

| Site | Fraction karstique | Mesurée (mm/an) | Sans karst | Avec karst | T2 africain |
|---|---|---|---|---|---|
| Andaboly | 0.00 | 6 | 75 | 104 | 144 |
| Sihanamaro | 0.00 | 27 | 148 | 179 | 92 |
| Ihazoambo | 0.00 | 46 | 104 | 87 | 262 |
| Ankaramena | 0.00 | 198 | 200 | 200 | 184 |
| AnKaranabO | 0.00 | 46 | 63 | 104 | 77 |
| Nosiomby | 0.00 | 19 | 142 | 142 | 208 |
| Mahavelo | 0.00 | 48 | 205 | 205 | 241 |
| Maroarivo | 0.61 | 185 | 60 | 74 | 38 |
| Ambatofotsy | 0.61 | 96 | 60 | 74 | 38 |
| Ankandy | 0.61 | 192 | 60 | 74 | 38 |
| Ankazomanga_P06 | 0.61 | 80 | 60 | 74 | 38 |
| Ankazomanga_P01 | 0.61 | 195 | 60 | 74 | 38 |

Avec karst : plus proche que T2 sur 10 sites sur 12 ; Spearman avec la mesure ρ = -0.37 (p = 0.236). Exploratoire : ces sites ont suggéré l'hypothèse.

