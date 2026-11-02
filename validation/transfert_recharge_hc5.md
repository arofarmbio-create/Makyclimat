# H-C5 : transfert de la recharge entre pays africains (base BGS)

Généré le 2026-11-02 par `scripts/validate_transfert_recharge.py`, selon `validation/protocole_carte_nappes.md` (section 10 et précisions du 02/11/2026, fixées avant le calcul). Données : MacDonald et al. (2021), 134 sites dans 30 pays ; aucun à Madagascar.

Erreur d'un pays laissé de côté : médiane des erreurs absolues de ses sites sur log10(R + 1). Une erreur de 0,3 correspond à un facteur 2 environ sur la recharge, 1,0 à un facteur 10.

| Version | Erreur médiane entre pays | Pays où elle bat la référence naïve | p (signe) | H-C5 (p < 0,025) |
|---|---|---|---|---|
| Référence naïve | 0.62 | — | — | — |
| T1 | 0.28 | 26 sur 30 | 0.000 | passe |
| T2 | 0.24 | 24 sur 29 | 0.000 | passe |

**Conclusion : H-C5 confirmée pour T1 et T2 ; le transfert vers Madagascar peut être tenté (H-C6).**

Résultats par pays : `validation/transfert_recharge_hc5_pays.csv`.
