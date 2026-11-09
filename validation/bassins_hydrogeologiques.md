# Bassins hydrogéologiques et bassins de surface

Généré le 2026-11-09 par `scripts/bassins_hydrogeologiques.py` (workflow 28), selon `validation/protocole_bassins_hydrogeologiques.md` (fixé avant le calcul ; test H-B2-L ajouté le 09/11/2026, avant son calcul). Terrain : Copernicus GLO-90 à 0,005° ; profondeur : carte du niveau statique v2.

| Profondeur utilisée | Mailles dans un autre bassin | Pente < 2 % | Pente ≥ 2 % | Rapport plat/pente | H-B1 | H-B2 |
|---|---|---|---|---|---|---|
| fokontany le plus proche (calcul initial) | 2.6% | 5.0% | 1.1% | 4.8 | soutenue | soutenue |
| lissée : 8 fokontany, 1/d² (test H-B2-L) | 2.4% | 4.4% | 1.0% | 4.5 | soutenue | soutenue |

**Test H-B2-L : H-B2 robuste** (règle fixée avant le test : rapport plat/pente d'au moins 2 avec la profondeur lissée).

## Par taille de bassin

| Groupe | Mailles | Profondeur la plus proche | Profondeur lissée |
|---|---|---|---|
| grands bassins (nommés) | 1,854,344 | 1.6% | 1.4% |
| petits bassins côtiers | 197,192 | 12.4% | 11.1% |

## Par région (région du fokontany le plus proche)

| Région | Mailles | Profondeur la plus proche | Profondeur lissée |
|---|---|---|---|
| Boeny | 107,150 | 12.8% | 7.6% |
| Sofia | 176,703 | 6.3% | 7.8% |
| Diana | 68,817 | 3.9% | 3.9% |
| Androy | 69,008 | 3.7% | 1.0% |
| Vatovavy | 45,875 | 3.2% | 2.2% |
| Melaky | 141,774 | 3.0% | 2.7% |
| Menabe | 169,462 | 2.7% | 3.2% |
| Atsimo Andrefana | 238,478 | 2.4% | 2.2% |
| Ambatosoa | 37,260 | 2.3% | 1.9% |
| Sava | 80,302 | 1.7% | 1.2% |
| Betsiboka | 97,351 | 1.5% | 1.5% |
| Fitovinany | 26,057 | 1.3% | 0.9% |
| Atsinanana | 76,119 | 1.3% | 1.4% |
| Analanjirofo | 34,630 | 1.2% | 0.9% |
| Anosy | 102,996 | 0.9% | 0.7% |
| Atsimo Atsinanana | 60,856 | 0.8% | 0.6% |
| Bongolava | 63,879 | 0.6% | 0.5% |
| Alaotra Mangoro | 94,447 | 0.4% | 0.4% |
| Haute Matsiatra | 72,347 | 0.2% | 0.6% |
| Analamanga | 58,695 | 0.2% | 0.4% |
| Amoron I Mania | 54,612 | 0.1% | 0.3% |
| Vakinankaratra | 61,138 | 0.1% | 0.0% |
| Ihorombe | 90,913 | 0.0% | 0.0% |
| Itasy | 22,667 | 0.0% | 0.0% |

## Bassins de surface les plus concernés (au moins 20 000 mailles, environ 500 km²)

| Bassin | Mailles | Profondeur la plus proche | Profondeur lissée |
|---|---|---|---|
| Bassin de Androka (n° 20) | 22,004 | 3.1% | 2.8% |
| Bassin de Analalava (n° 12) | 42,835 | 0.6% | 1.0% |
| Bassin de Boanamary (n° 1) | 191,121 | 0.3% | 0.4% |
| Bassin de Antaritarika (n° 21) | 20,878 | 0.3% | 0.1% |
| Bassin de Andovoranto (n° 17) | 26,365 | 0.2% | 0.1% |
| Bassin de Morondava (n° 19) | 21,530 | 0.2% | 0.2% |
| Bassin de Mahadrodroka (n° 5) | 93,762 | 0.2% | 0.0% |
| Bassin de Marolinta (n° 13) | 30,987 | 0.2% | 0.1% |
| Bassin de Ambodiharina (n° 7) | 61,221 | 0.1% | 0.1% |
| Bassin de Matsakabanja (n° 6) | 64,450 | 0.1% | 0.1% |
| Bassin de Antongo Vaovao (n° 2) | 187,045 | 0.1% | 0.2% |
| Bassin de Belo Sur Tsiribihina (n° 3) | 164,750 | 0.1% | 0.2% |
| Bassin de Mananjary (n° 18) | 24,518 | 0.1% | 0.1% |
| Bassin de Aboalimena (n° 10) | 44,889 | 0.1% | 0.1% |
| Bassin de Ampasina Maningory (n° 11) | 43,505 | 0.1% | 0.2% |

Limite : la charge dépend de la profondeur estimée (approximative hors du Grand Sud) ; un écart indique un passage possible de l'eau souterraine entre bassins, pas un flux mesuré.

