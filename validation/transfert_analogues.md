# Transfert de connaissances depuis des régions analogues : recharge

Généré le 2026-11-04 par `scripts/transfert_analogues.py`, selon `validation/protocole_transfert_analogues.md` (fixé avant le calcul). Sources : Wan, Döll et Müller Schmied 2024 (CC BY 4.0) ; GLiM 0,5° (Hartmann et Moosdorf 2012, CC BY 3.0) ; Madagascar : MGMERL (HT) et Carrière et al. 2021 (GROSoM).

335 sites sources avec type d'aquifère. Accord de la règle GLiM avec le type du BGS sur les sites africains : 47% sur 97 sites.

## Niveau 1 : dans les sources (pays laissé de côté)

Le modèle par analogues bat la référence naïve dans 22 pays sur 29 (test du signe, p = 0.004). Erreur médiane : modèle 0.31, naïve 0.49 (log10 de la recharge).

## H-R1 : le modèle africain hors d'Afrique, selon le type d'aquifère

161 sites hors d'Afrique. Surestimation : socle 31%, sédimentaire et non consolidé 49% ; Fisher unilatéral p = 0.948. **H-R1 non soutenue**.

## H-T1 et H-T2 : les sites malgaches mesurés (fluctuation de nappe)

| Site | Type d'aquifère (GLiM) | Mesurée (mm/an) | Transfert mondial (mm/an) | T2 africain (mm/an) | Plus proche : |
|---|---|---|---|---|---|
| Andaboly | Basement | 6 | 104 | 144 | mondial |
| Sihanamaro | Unconsolidated | 27 | 120 | 92 | T2 |
| Ihazoambo | Basement | 46 | 87 | 262 | mondial |
| Ankaramena | Basement | 198 | 200 | 184 | mondial |
| AnKaranabO | Basement | 46 | 104 | 77 | T2 |
| Nosiomby | Unconsolidated | 19 | 205 | 208 | mondial |
| Mahavelo | Volcanic | 48 | 115 | 241 | mondial |
| Maroarivo | Sedimentary | 185 | 60 | 38 | mondial |
| Ambatofotsy | Sedimentary | 96 | 60 | 38 | mondial |
| Ankandy | Sedimentary | 192 | 60 | 38 | mondial |
| Ankazomanga_P06 | Sedimentary | 80 | 60 | 38 | mondial |
| Ankazomanga_P01 | Sedimentary | 195 | 60 | 38 | mondial |

**H-T1** : transfert mondial plus proche sur 10 sites sur 12 (règle : au moins 10 sur 12 ; test du signe p = 0.019). **Soutenue**.
**H-T2** : Spearman entre transfert mondial et mesure ρ = -0.46 (p = 0.135) ; ordre socle / sédimentaire non respecté. **Non soutenue**.

