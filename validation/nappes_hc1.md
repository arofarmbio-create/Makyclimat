# H-C1 : la profondeur de nappe de Fan et al. face aux forages malgaches

Généré le 2026-11-02 par `scripts/validate_nappes_hc1.py`, selon `validation/protocole_carte_nappes.md` (section 6 et modification du 02/11/2026, fixées avant le calcul). Données de forage : MGMERL ; carte mondiale : Fan et al. (2017), valeurs non republiées.

Relevés lus : 1000 ; gardés après contrôle et avec une valeur de Fan : 999.

## Résultat

- Profondeur médiane mesurée : **5.78 m** ; profondeur médiane de Fan aux mêmes points : **20.87 m**.
- Écart médian (Fan − mesure) : 12.91 m ; biais moyen : 15.50 m ; erreur absolue médiane : 14.33 m.
- Test de Wilcoxon (principal) : p = 0.00.
- Contrôle par blocs de 1° : 36 blocs ; Fan plus profond dans 16 sur 36 ; test du signe p = 0.62.
- Corrélation de Spearman entre Fan et la mesure : 0.02 (Fan classe-t-il les sites dans le bon ordre ?).
- **H-C1 (biais significatif, solide aux deux tests) : non confirmée.**

## Par classe (descriptif)

| Variable | Classe | Points | Mesure médiane (m) | Fan médiane (m) | Écart médian (m) | Erreur absolue médiane (m) |
|---|---|---|---|---|---|---|
| classe_relief | bas de versant (5-15 m) | 175 | 6.30 | 12.04 | 3.29 | 6.40 |
| classe_relief | fond de vallée (HAND < 5 m) | 248 | 5.02 | 2.53 | -1.41 | 5.08 |
| classe_relief | versant ou plateau (> 15 m) | 576 | 6.00 | 30.86 | 24.17 | 24.22 |
| productivite | inconnue | 20 | 14.57 | 0.00 | -14.02 | 14.02 |
| productivite | productivité BGS 40 % | 592 | 5.04 | 24.67 | 18.98 | 18.98 |
| productivite | productivité BGS 50 % | 65 | 7.39 | 3.08 | -2.23 | 5.08 |
| productivite | productivité BGS 67 % | 88 | 8.91 | 30.96 | 20.57 | 20.57 |
| productivite | productivité BGS 72 % | 180 | 6.10 | 14.51 | 6.03 | 8.33 |
| productivite | productivité BGS 90 % | 54 | 7.21 | 15.51 | 5.05 | 7.25 |

Limites (protocole §7) : relevés regroupés autour des projets WASH, surtout dans le Sud ; niveau statique ponctuel (saison, pompage) ; niveau d'un forage captif possiblement au-dessus du toit de la nappe ; maille de 1 km de Fan qui mélange vallée et versant.
