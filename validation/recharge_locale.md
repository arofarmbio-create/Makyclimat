# Recharge corrigée par les mesures malgaches (T2L)

Généré le 2026-11-09 par `scripts/recharge_locale.py`, selon `validation/protocole_recharge_locale.md` (fixé avant le calcul). Calcul local (séries MGMERL et GROSoM hors dépôt).

Facteurs appris sur les 12 sites : unique ×0.80 ; socle ×0.19 ; autres ×3.52.

## Validation (8 groupes de sites à moins de 20 km laissés de côté : critère principal)

| Modèle | Sites retrouvés (groupes) | Erreur médiane log₁₀ (groupes) | Sites retrouvés (site par site) | Erreur (site par site) |
|---|---|---|---|---|
| M0 : T2 sans correction | 1 sur 12 | 0.69 (facteur 4.9) | 1 sur 12 | 0.69 |
| M1 : facteur unique | 1 sur 12 | 1.05 (facteur 11.2) | 1 sur 12 | 0.76 |
| M2 : facteur par groupe d'aquifère | 2 sur 12 | 0.90 (facteur 8.0) | 4 sur 12 | 0.33 |
| M3 : M2 + correction locale (L = 25 km) | 1 sur 12 | 0.91 (facteur 8.1) | 4 sur 12 | 0.28 |

Sensibilité de M3 au rayon (groupes) : L = 10 km : 2 retrouvés, erreur 0.90 ; L = 50 km : 1 retrouvés, erreur 0.93.

**H-L1 non soutenue** (M2 : au moins 6 sites sur 12 et erreur au plus la moitié de M0).
**H-L2 non soutenue** (M3 : au moins un site de plus que M2 et erreur plus faible).

## Sites (prédictions des groupes laissés de côté, mm/an)

| Site | Source | Groupe | Mesurée [Sy bas ; haut] | M0 | M1 | M2 | M3 |
|---|---|---|---|---|---|---|---|
| Andaboly | HT (MGMERL) | Basement | 6 [2 ; 9] | 144 | 155 | 29 | 31 |
| Sihanamaro | HT (MGMERL) | Unconsolidated | 27 [14 ; 41] | 92 | 99 | 449 | 449 |
| Ihazoambo | HT (MGMERL) | Basement | 46 [15 ; 76] | 262 | 281 | 52 | 78 |
| Ankaramena | HT (MGMERL) | Basement | 198 [66 ; 330] | 184 | 110 | 32 | 32 |
| AnKaranabO | HT (MGMERL) | Basement | 46 [15 ; 77] | 77 | 83 | 14 | 13 |
| Nosiomby | HT (MGMERL) | Basement | 19 [6 ; 31] | 208 | 223 | 42 | 42 |
| Mahavelo | HT (MGMERL) | Basement | 48 [16 ; 81] | 241 | 259 | 42 | 42 |
| Maroarivo | GROSoM | Unconsolidated | 185 [92 ; 277] | 38 | 8 | 8 | 8 |
| Ambatofotsy | GROSoM | Unconsolidated | 96 [48 ; 144] | 38 | 8 | 8 | 8 |
| Ankandy | GROSoM | Unconsolidated | 192 [96 ; 287] | 38 | 8 | 8 | 8 |
| Ankazomanga_P06 | GROSoM | Unconsolidated | 80 [40 ; 119] | 38 | 8 | 8 | 8 |
| Ankazomanga_P01 | GROSoM | Unconsolidated | 195 [98 ; 293] | 38 | 8 | 8 | 8 |

## Carte T2L (modèle M2)

105 mailles sur 650 dans le domaine de validité (16%). Recharge médiane dans le domaine : T2 90 → T2L 39 mm/an.

| Groupe | Mailles dans le domaine | T2 médiane | T2L médiane |
|---|---|---|---|
| autres | 36 | 32 | 112 |
| socle | 69 | 151 | 28 |

## Validation prospective (section 6 du protocole)

Carte figée le 2026-11-09 : `inputs/hydrogeologie/recharge_t2l.csv`, empreinte SHA-256 `2dc024a9315b51c90a12256b1b69914671d616cd2925f84736a6b089c2dd2291`. Toute nouvelle mesure de recharge sera comparée à ces valeurs, sans recalcul ; réussite si au moins 60 % des nouveaux sites du domaine sont retrouvés.

## Décision (fixée avant le calcul)

T2 reste la valeur centrale ; T2L est publiée comme sensibilité.

Limites : 12 sites, tous dans le Sud et le Sud-Ouest ; fourchette de Sy d'un facteur 3 à 5 ; méthode mensuelle (la journalière donne des recharges plus fortes) ; puits GROSoM en partie karstiques, classés non consolidés.

