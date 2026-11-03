# Carte nationale du niveau statique (version 1)

Générée le 2026-11-03 par `scripts/nappes_carte_nationale.py`, selon `validation/protocole_cadre_eaux_souterraines.md` (phase 5, précisions du 03/11/2026 fixées avant le calcul). Modèle : hybride S0 entraîné sur 980 forages MGMERL ; intervalle de 80 % calibré selon la distance. **Niveau de preuve : approximation**, validée par région entière sur 8 régions ; pas encore de confirmation sur des forages indépendants (phase 4).

17453 fokontany estimés sur 17465 ; 52% en extrapolation (terrain hors de l'étendue des forages).

| Région | Forages d'apprentissage | Fokontany | Profondeur médiane (m) | Erreur attendue (m) | Distance médiane au forage (km) | Part en extrapolation |
|---|---|---|---|---|---|---|
| Alaotra Mangoro | **aucun** | 692 | 5.1 | 3.4 | 90 | 41% |
| Ambatosoa | oui | 366 | 3.8 | 2.9 | 50 | 77% |
| Amoron I Mania | oui | 785 | 5.7 | 2.8 | 28 | 98% |
| Analamanga | oui | 1660 | 5.0 | 2.4 | 21 | 99% |
| Analanjirofo | oui | 385 | 3.9 | 2.4 | 8 | 75% |
| Androy | oui | 1039 | 7.3 | 2.4 | 6 | 2% |
| Anosy | oui | 623 | 7.1 | 2.4 | 7 | 31% |
| Atsimo Andrefana | oui | 1524 | 6.9 | 2.4 | 7 | 15% |
| Atsimo Atsinanana | oui | 745 | 4.7 | 2.4 | 9 | 23% |
| Atsinanana | **aucun** | 1075 | 4.3 | 2.9 | 113 | 60% |
| Betsiboka | **aucun** | 370 | 5.1 | 2.9 | 87 | 28% |
| Boeny | oui | 488 | 5.4 | 2.4 | 14 | 23% |
| Bongolava | **aucun** | 300 | 5.6 | 2.9 | 130 | 41% |
| Diana | **aucun** | 525 | 5.4 | 2.9 | 104 | 53% |
| Fitovinany | oui | 631 | 3.9 | 2.4 | 18 | 25% |
| Haute Matsiatra | **aucun** | 787 | 5.7 | 3.4 | 53 | 96% |
| Ihorombe | **aucun** | 245 | 7.1 | 3.4 | 54 | 39% |
| Itasy | **aucun** | 556 | 6.0 | 2.8 | 49 | 97% |
| Melaky | **aucun** | 293 | 6.0 | 2.9 | 193 | 35% |
| Menabe | oui | 541 | 6.1 | 2.9 | 57 | 28% |
| Sava | oui | 808 | 4.5 | 2.4 | 19 | 46% |
| Sofia | **aucun** | 1326 | 5.4 | 2.9 | 114 | 34% |
| Vakinankaratra | **aucun** | 998 | 5.6 | 3.4 | 78 | 96% |
| Vatovavy | oui | 691 | 5.0 | 2.8 | 41 | 46% |

## Comparaison avec le produit en service (`watertable.csv`, plus proche relevé à 15 km)

Fokontany communs : 5161 ; écart médian absolu 2.3 m. Sans donnée indépendante, cet écart ne dit pas lequel est juste (règle fixée avant le calcul).

