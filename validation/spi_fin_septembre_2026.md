# SPI à fin septembre 2026 — état de sécheresse avant la saison 2026-2027

Cahier des charges : §5 (anomalies depuis le début de l'année hydrologique), §6.A (SPI-1/3/6/12), §13 (validation).
Calcul du 28/10/2026 (`build_soilwater.py`, workflow « 6 - Eau dans le sol », exécution 40634464352).

**Données et méthode**
- Pluie CHIRPS v2.0 mensuelle définitive, jusqu'au 30/09/2026. Loi gamma ajustée par mois du calendrier sur 1981-2026.
- SPI vide quand la normale du cumul est inférieure à 25 mm.
- Valeur régionale : moyenne simple des fokontany, sans pondération par la surface ni par la population.

Type de donnée : **estimation satellitaire** (CHIRPS), pas une observation de station.

## Résultats par région (septembre 2026)

Lecture OMM : ≤ −1 modérément sec, ≤ −1,5 sévèrement sec, ≤ −2 extrêmement sec ; symétrique côté humide.
« vide » = normale trop faible pour calculer le SPI.

| Région | SPI-1 | SPI-3 | SPI-6 | SPI-12 |
|---|---|---|---|---|
| Anosy | −0,08 | −0,57 | −0,98 | **−1,63** |
| Atsimo Atsinanana | 0,54 | −0,08 | −0,97 | **−1,33** |
| Fitovinany | 1,57 | 0,92 | −0,30 | **−1,18** |
| Atsimo Andrefana | vide | 0,04 | 0,06 | **−1,14** |
| Androy | 0,21 | −0,12 | −0,80 | **−1,12** |
| Haute Matsiatra | 2,84 | 2,68 | 0,92 | **−1,09** |
| Ihorombe | 1,60 | 1,67 | 0,16 | −0,96 |
| Vatovavy | 2,67 | 2,00 | 0,06 | −0,72 |
| Ambatosoa | 0,93 | 0,93 | −0,14 | −0,67 |
| Sava | −0,59 | 1,19 | 0,43 | −0,57 |
| Diana | 0,38 | 1,02 | 0,61 | −0,51 |
| Amoron'i Mania | 3,09 | 3,09 | 1,20 | −0,49 |
| Sofia | 0,55 | 0,72 | −0,29 | −0,44 |
| Vakinankaratra | 3,09 | 3,09 | 0,82 | −0,42 |
| Menabe | vide | 2,82 | 0,07 | −0,38 |
| Itasy | vide | 3,09 | 0,65 | −0,22 |
| Boeny | vide | 1,72 | −0,51 | −0,21 |
| Melaky | vide | 2,12 | −0,21 | −0,18 |
| Analanjirofo | 1,18 | 1,02 | −0,20 | −0,06 |
| Betsiboka | vide | 1,25 | −0,20 | −0,05 |
| Bongolava | vide | 3,09 | 0,03 | 0,17 |
| Analamanga | 2,87 | 2,70 | 0,72 | 0,18 |
| Atsinanana | 1,45 | 1,30 | 0,17 | 0,37 |
| Alaotra Mangoro | 1,68 | 0,91 | 0,42 | 0,51 |

Source : `validation/spi_regions.csv`, lignes `2026-09`.

## Lecture

1. **Déficit sur 12 mois dans le Sud et le Sud-Est.**
   - SPI-12 ≤ −1 dans 6 régions : Anosy (sévèrement sec, −1,63), Atsimo Atsinanana, Fitovinany, Atsimo Andrefana, Androy et Haute Matsiatra.
   - C'est l'héritage de la saison 2025-2026, cohérent avec FEWS NET (saison principale 2025-2026 sous la moyenne, crise IPC 3 à Toliara II et Amboasary Atsimo).
   - La saison 2026-2027 démarre donc avec un déficit dans ces régions, **avant même** l'effet éventuel d'El Niño.
2. **Saison sèche anormalement humide sur les Hautes Terres, l'Ouest et le Sud-Est.**
   - SPI-3 de +2 à +3,09 (borne).
   - **Vérifié de façon indépendante avec ERA5** (Open-Meteo), sur 4 points tests :

     | Ville | Juillet-septembre 2026 | Normale 1991-2020 | Rang sur 36 ans |
     |---|---|---|---|
     | Antananarivo | 52 mm | 14 mm | 1er |
     | Fianarantsoa | 112 mm | 38 mm | 1er |
     | Antsirabe | 73 mm | 23 mm | 2e |
     | Ambovombe | 132 mm | 44 mm | 2e |

   - Le signal est donc **réel**, mais faible en millimètres. Il ne compense pas le déficit sur 12 mois. Dans l'Androy, ces pluies précoces ont déclenché des semis de manioc prématurés (FEWS NET), exposés si la saison est sèche.
3. **Le déficit sur 12 mois n'est pas une pénurie d'eau** (règle §6.E). Aucune donnée de niveau de nappe ni de débit observé ne permet de le vérifier ici.

## Point non résolu

L'humidité du sol standardisée (`sm_z`) est fortement négative là où le SPI est fortement positif : −2,2 à Bongolava, −2,15 à Itasy, −2,04 à Vakinankaratra. C'est contradictoire.

- **Hypothèse :** en saison sèche, le stock simulé est proche de zéro. Sa variance est alors minuscule et le score standardisé devient instable. De plus, l'évapotranspiration est une climatologie fixe (2016-2020).
- **À vérifier avant d'utiliser `sm_z` en saison sèche :** cet indicateur n'est **pas interprété** ici.

## Limites et suite

- Octobre 2026 n'est pas inclus. CHIRPS provisoire est disponible jusqu'au 20/10 mais n'est pas encore lu par le pipeline (prochaine étape).
- Les moyennes régionales sont non pondérées, et la vérification ERA5 porte sur 4 points seulement.
- Il manque une validation par stations au sol (Météo Madagascar) : **validation partielle**.
