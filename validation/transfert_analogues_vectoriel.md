# Transfert par analogues : recharge, typage par la GLiM vectorielle (reprise annoncée)

Généré le 2026-11-04 par `scripts/transfert_analogues.py`, selon `validation/protocole_transfert_analogues.md` (fixé avant le calcul). Sources : Wan, Döll et Müller Schmied 2024 (CC BY 4.0) ; GLiM 0,5° (Hartmann et Moosdorf 2012, CC BY 3.0) ; Madagascar : MGMERL (HT) et Carrière et al. 2021 (GROSoM).

332 sites sources avec type d'aquifère. Accord de la règle GLiM avec le type du BGS sur les sites africains : 58% sur 99 sites.

## Niveau 1 : dans les sources (pays laissé de côté)

Le modèle par analogues bat la référence naïve dans 22 pays sur 29 (test du signe, p = 0.004). Erreur médiane : modèle 0.35, naïve 0.54 (log10 de la recharge).

## H-R1 : le modèle africain hors d'Afrique, selon le type d'aquifère

158 sites hors d'Afrique. Surestimation : socle 32%, sédimentaire et non consolidé 49% ; Fisher unilatéral p = 0.962. **H-R1 non soutenue**.

## H-T1 et H-T2 : les sites malgaches mesurés (fluctuation de nappe)

| Site | Type d'aquifère (GLiM) | Mesurée (mm/an) | Transfert mondial (mm/an) | T2 africain (mm/an) | Plus proche : |
|---|---|---|---|---|---|
| Andaboly | Basement | 6 | 75 | 144 | mondial |
| Sihanamaro | Unconsolidated | 27 | 148 | 92 | T2 |
| Ihazoambo | Basement | 46 | 104 | 262 | mondial |
| Ankaramena | Basement | 198 | 200 | 184 | mondial |
| AnKaranabO | Basement | 46 | 63 | 77 | mondial |
| Nosiomby | Volcanic | 19 | 142 | 208 | mondial |
| Mahavelo | Unconsolidated | 48 | 205 | 241 | mondial |
| Maroarivo | Unconsolidated | 185 | 60 | 38 | mondial |
| Ambatofotsy | Unconsolidated | 96 | 60 | 38 | mondial |
| Ankandy | Unconsolidated | 192 | 60 | 38 | mondial |
| Ankazomanga_P06 | Unconsolidated | 80 | 60 | 38 | mondial |
| Ankazomanga_P01 | Unconsolidated | 195 | 60 | 38 | mondial |

**H-T1** : transfert mondial plus proche sur 11 sites sur 12 (règle : au moins 10 sur 12 ; test du signe p = 0.003). **Soutenue**.
**H-T2** : Spearman entre transfert mondial et mesure ρ = -0.37 (p = 0.237) ; ordre socle / sédimentaire non respecté. **Non soutenue**.


Règle de la reprise (fixée avant calcul) : conclusion relevée à « démontré » seulement si H-T1 et H-T2 réussissent et si l'accord avec le BGS dépasse 70 % (ici 58%). **Conclusion : inchangée (plausible, non démontré)**.
