# Ressource en eau souterraine par fokontany : recharge, volume, renouvellement, risque (version 1)

Généré le 2026-11-04 par `scripts/nappes_ressource.py`, selon `validation/protocole_cadre_eaux_souterraines.md` (section 5, mise en œuvre du 03/11/2026 fixée avant le calcul). **Toutes ces grandeurs sont des approximations** : aucune mesure de volume ni d'âge ne les valide ; la recharge (transfert T2) n'est pas confirmée à Madagascar (H-C6) et surestime aux sites suivis du Sud.

Population : WorldPop 2015 ramenée aux totaux communaux SEAM 2025 (79% des communes appariées par leur nom ; facteur 1 ailleurs). Prélèvements : 15 L par personne et par jour (norme Sphère 2018), sensibilité 20 et 50 L (OMS). Commune urbaine d'Antananarivo : seule la population non desservie par le réseau JIRAMA (eau de l'Ikopa, desserte 47 %) prélève dans la nappe.

- Renouvellement : 41% renouvelable, 45% lent, 13% peu renouvelable (valeurs centrales).
- Risque d'épuisement : 93% faible, 6% modéré, 1% élevé (sensibilité : élevé 2% à 20 L, 6% à 50 L).

| Région | Recharge médiane (mm/an) | Stock médian (mm d'eau) | Renouvellement médian (ans) | Indice d'exploitation médian | Part en risque élevé |
|---|---|---|---|---|---|
| Alaotra Mangoro | 244 | 1766 | 8 | 0.002 | 0% |
| Ambatosoa | 257 | 548 | 2 | 0.002 | 0% |
| Amoron I Mania | 181 | 1370 | 9 | 0.007 | 0% |
| Analamanga | 179 | 2048 | 12 | 0.010 | 3% |
| Analanjirofo | 306 | 638 | 2 | 0.002 | 0% |
| Androy | 71 | 3570 | 48 | 0.006 | 1% |
| Anosy | 92 | 1794 | 15 | 0.002 | 0% |
| Atsimo Andrefana | 23 | 3314 | 131 | 0.008 | 4% |
| Atsimo Atsinanana | 208 | 1363 | 7 | 0.004 | 0% |
| Atsinanana | 305 | 740 | 3 | 0.002 | 0% |
| Betsiboka | 44 | 2790 | 51 | 0.003 | 3% |
| Boeny | 42 | 6107 | 163 | 0.007 | 6% |
| Bongolava | 75 | 2666 | 37 | 0.005 | 0% |
| Diana | 187 | 4246 | 23 | 0.002 | 1% |
| Fitovinany | 267 | 1064 | 4 | 0.003 | 0% |
| Haute Matsiatra | 93 | 1840 | 20 | 0.012 | 3% |
| Ihorombe | 71 | 1908 | 23 | 0.001 | 1% |
| Itasy | 136 | 2548 | 17 | 0.006 | 0% |
| Melaky | 33 | 5498 | 173 | 0.002 | 2% |
| Menabe | 27 | 5906 | 245 | 0.006 | 4% |
| Sava | 332 | 930 | 3 | 0.002 | 0% |
| Sofia | 196 | 2630 | 13 | 0.001 | 1% |
| Vakinankaratra | 172 | 1885 | 11 | 0.008 | 0% |
| Vatovavy | 311 | 688 | 2 | 0.001 | 0% |

Commune urbaine d'Antananarivo (192 fokontany) : risque élevé dans 13% des fokontany si le réseau JIRAMA dessert 47 % de la population, 86% s'il est coupé ; 145 fokontany changent de classe entre les deux.

Non comptés (aucune donnée publique vérifiée) : bétail, irrigation par la nappe, industrie et mines. L'indice mesure la pression **domestique** ; dans le Grand Sud, le bétail abreuvé aux puits l'augmente sans doute fortement.

Contrôle local (sites MGMERL suivis, recharge par fluctuation de nappe, H-C6) :

| Site | Fluctuation de nappe (mm/an) | Transfert T2 (mm/an) |
|---|---|---|
| Site MGMERL Andaboly (Basement, fluctuation de nappe) | 6 | 144 |
| Site MGMERL Ankaramena (Basement, fluctuation de nappe) | 198 | 184 |
| Site MGMERL Ankaranabo (Basement, fluctuation de nappe) | 46 | 77 |
| Site MGMERL Ihazoambo (Basement, fluctuation de nappe) | 46 | 262 |
| Site MGMERL Mahavelo (Basement, fluctuation de nappe) | 48 | 241 |
| Site MGMERL Nosiomby (Basement, fluctuation de nappe) | 22 | 208 |
| Site MGMERL Sihanamaro (Unconsolidated, fluctuation de nappe) | 27 | 92 |
