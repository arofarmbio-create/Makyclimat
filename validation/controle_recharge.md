# Contrôle de vraisemblance de la recharge transférée (T2c)

Généré le 2026-11-09 par `scripts/controle_recharge.py`, selon `validation/protocole_controle_recharge.md` (fixé avant le calcul). Calcul local : la base BGS, la grille T2 et les séries MGMERL sont hors du dépôt, comme pour H-C6.

## Bornes de la part de la pluie qui recharge la nappe (sites africains du BGS)

| Groupe d'aquifère | Climat | Sites | R/P à 10 % | R/P à 90 % |
|---|---|---|---|---|
| Basement | aride | 13 | 0.014 | 0.246 |
| Basement | humide | 22 | 0.047 | 0.251 |
| Sedimentary | aride | 62 | 0.002 | 0.121 |
| Sedimentary | humide | 18 | 0.045 | 0.248 |
| Unconsolidated | aride | 19 | 0.007 | 0.112 |
| Basement | tous | 35 | 0.028 | 0.270 |
| Sedimentary | tous | 80 | 0.004 | 0.156 |
| Unconsolidated | tous | 19 | 0.007 | 0.112 |
| tous | tous | 134 | 0.009 | 0.185 |

Classes de moins de 10 sites : repli sur le groupe seul, puis sur tous les sites.

## H-R1 : mailles hors bornes

Sur 650 mailles : 30% sous la borne basse, 0% au-dessus de la borne haute. Recharge médiane : T2 75 mm/an, T2c 84 mm/an.

| Zone | Mailles | Sous la borne basse | Au-dessus de la borne haute |
|---|---|---|---|
| Grand Sud (au sud de 23° S) | 102 | 14% | 0% |
| reste de l'île | 548 | 33% | 0% |

| Région | Mailles | Sous la borne basse | Au-dessus de la borne haute |
|---|---|---|---|
| Alaotra Mangoro | 29 | 3% | 0% |
| Ambatosoa | 13 | 0% | 0% |
| Amoron I Mania | 20 | 50% | 0% |
| Analamanga | 21 | 33% | 0% |
| Analanjirofo | 11 | 0% | 0% |
| Androy | 21 | 14% | 0% |
| Anosy | 32 | 9% | 0% |
| Atsimo Andrefana | 74 | 31% | 0% |
| Atsimo Atsinanana | 20 | 5% | 0% |
| Atsinanana | 23 | 0% | 0% |
| Betsiboka | 30 | 70% | 0% |
| Boeny | 36 | 67% | 0% |
| Bongolava | 22 | 41% | 0% |
| Diana | 21 | 5% | 5% |
| Fitovinany | 9 | 0% | 0% |
| Haute Matsiatra | 20 | 30% | 0% |
| Ihorombe | 30 | 20% | 0% |
| Itasy | 6 | 0% | 0% |
| Melaky | 43 | 60% | 0% |
| Menabe | 54 | 67% | 0% |
| Sava | 27 | 4% | 0% |
| Sofia | 55 | 16% | 0% |
| Vakinankaratra | 20 | 45% | 0% |
| Vatovavy | 13 | 0% | 0% |

| Groupe d'aquifère | Mailles | Sous la borne basse | Au-dessus de la borne haute |
|---|---|---|---|
| Basement | 417 | 18% | 0% |
| Sedimentary | 176 | 69% | 0% |
| Unconsolidated | 57 | 2% | 2% |

## H-R2 : références malgaches (vérification indépendante, même évaluation que H-C6)

| Référence | Valeur centrale | T2 (intervalle) | T2c (intervalle) | T2 | T2c |
|---|---|---|---|---|---|
| Sud de Madagascar (BRGM 2005, cité par AVSF 2016) | 60 | 70 (21 à 359) | 70 (50 à 245) | oui | oui |
| Plateau Mahafaly (profil USAID/Winrock) | 60 | — (— à —) | — (— à —) | — | — |
| Site MGMERL Andaboly (Basement, fluctuation de nappe) | 6 | 144 (43 à 731) | 144 (58 à 314) | non | non |
| Site MGMERL Ankaramena (Basement, fluctuation de nappe) | 198 | 184 (55 à 933) | 184 (73 à 396) | oui | oui |
| Site MGMERL Ankaranabo (Basement, fluctuation de nappe) | 46 | 77 (23 à 394) | 77 (56 à 302) | oui | non |
| Site MGMERL Ihazoambo (Basement, fluctuation de nappe) | 46 | 262 (79 à 1324) | 262 (79 à 391) | non | non |
| Site MGMERL Mahavelo (Basement, fluctuation de nappe) | 48 | 241 (73 à 1220) | 241 (82 à 444) | non | non |
| Site MGMERL Nosiomby (Basement, fluctuation de nappe) | 22 | 208 (63 à 1054) | 208 (80 à 430) | non | non |
| Site MGMERL Sihanamaro (Unconsolidated, fluctuation de nappe) | 27 | 92 (27 à 470) | 92 (27 à 145) | non | non |

T2 : 3 sur 8 ; T2c : 2 sur 8. **H-R2 non soutenue** (règle : au moins 5 sur 8).

## Contrôles nommés (descriptifs : ce sont eux qui ont révélé le problème)

| Lieu | Pluie (mm/an) | Groupe | Bornes R/P | T2 | T2c (intervalle) | Comparaison |
|---|---|---|---|---|---|---|
| Mahajanga | 1472 | Sedimentary | 0.045 à 0.248 (Sedimentary / humide) | 7 | 67 (67 à 365) | carte BGS : 124 mm/an |
| Toliara | 452 | Unconsolidated | 0.007 à 0.112 (Unconsolidated / aride) | 20 | 20 (6 à 51) | puits karstiques voisins : 80 à 195 mm/an |

## Décision (fixée avant le calcul)

T2 reste la valeur centrale ; le bilan est publié avec la fourchette T2 / T2c, et les sous-bassins dont la classe de bilan change sont marqués « incertains ».

Limites : le karst n'est pas un groupe BGS distinct (classé « Sedimentary ») ; bornes tirées de sites africains ; pluie de la grille BGS ; la fluctuation de nappe des sites du Sud peut elle-même sous-estimer la recharge.

