# Carte nationale du niveau statique (version 2 (tableau MGMERL complet du 03/11/2026))

Générée le 2026-11-03 par `scripts/nappes_carte_nationale.py`, selon `validation/protocole_cadre_eaux_souterraines.md` (phase 5, précisions du 03/11/2026 fixées avant le calcul). Modèle : hybride S0 entraîné sur 1399 forages MGMERL ; intervalle de 80 % calibré selon la distance. **Niveau de preuve : approximation**, validée par région entière sur 8 régions ; pas encore de confirmation sur des forages indépendants (phase 4).

17453 fokontany estimés sur 17465 ; 54% en extrapolation (terrain hors de l'étendue des forages).

| Région | Forages d'apprentissage | Fokontany | Profondeur médiane (m) | Erreur attendue (m) | Distance médiane au forage (km) | Part en extrapolation |
|---|---|---|---|---|---|---|
| Alaotra Mangoro | **aucun** | 692 | 4.7 | 3.1 | 89 | 48% |
| Ambatosoa | oui | 366 | 3.7 | 2.5 | 44 | 81% |
| Amoron I Mania | oui | 785 | 5.5 | 2.5 | 28 | 99% |
| Analamanga | oui | 1660 | 5.0 | 2.1 | 21 | 99% |
| Analanjirofo | oui | 385 | 3.8 | 2.1 | 8 | 83% |
| Androy | oui | 1039 | 7.7 | 2.1 | 6 | 3% |
| Anosy | oui | 623 | 6.9 | 2.1 | 7 | 32% |
| Atsimo Andrefana | oui | 1524 | 6.8 | 2.1 | 5 | 15% |
| Atsimo Atsinanana | oui | 745 | 5.2 | 2.1 | 8 | 24% |
| Atsinanana | **aucun** | 1075 | 4.3 | 3.0 | 113 | 67% |
| Betsiboka | oui | 370 | 5.1 | 3.0 | 57 | 28% |
| Boeny | oui | 488 | 4.7 | 2.1 | 12 | 23% |
| Bongolava | **aucun** | 300 | 5.6 | 3.0 | 128 | 42% |
| Diana | **aucun** | 525 | 5.0 | 3.0 | 104 | 53% |
| Fitovinany | oui | 631 | 3.9 | 2.1 | 18 | 31% |
| Haute Matsiatra | **aucun** | 787 | 5.7 | 3.1 | 53 | 95% |
| Ihorombe | **aucun** | 245 | 6.6 | 3.0 | 51 | 41% |
| Itasy | **aucun** | 556 | 6.0 | 2.5 | 49 | 97% |
| Melaky | **aucun** | 293 | 5.4 | 3.0 | 176 | 34% |
| Menabe | oui | 541 | 5.7 | 3.0 | 57 | 27% |
| Sava | oui | 808 | 4.3 | 2.1 | 19 | 50% |
| Sofia | **aucun** | 1326 | 5.1 | 3.0 | 111 | 34% |
| Vakinankaratra | **aucun** | 998 | 5.4 | 3.1 | 78 | 97% |
| Vatovavy | oui | 691 | 4.7 | 2.5 | 40 | 58% |

## Comparaison avec le produit en service (`watertable.csv`, plus proche relevé à 15 km)

Fokontany communs : 5161 ; écart médian absolu 2.3 m. Sans donnée indépendante, cet écart ne dit pas lequel est juste (règle fixée avant le calcul).

