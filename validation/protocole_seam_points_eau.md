# Protocole : les données SEAM du ministère de l'Eau sont-elles utiles à MakyClimat ?

*Rédigé le 03/11/2026, **avant** tout calcul, à la demande du porteur du projet : étudier les données, sans chercher
d'abord à les relier à d'autres bases. Rattaché au protocole-cadre `protocole_cadre_eaux_souterraines.md` (niveau
statique, risque d'épuisement). Analyse exploratoire. Toute modification sera datée en section 7.*

## 1. Source

SEAM (Suivi de l'eau, de l'assainissement et de l'hygiène), ministère de l'Eau, de l'Assainissement et de l'Hygiène
(MEAH), https://seam.meah.gov.mg/v2/, données consolidées depuis DHIS2 et régénérées chaque jour. Lecture publique
sans connexion ; aucune licence affichée : citation « MEAH / SEAM », données brutes hors du dépôt
(`data/mdg/seam_raw/`), seuls des résultats agrégés sont publiés. Exploration du 03/11/2026 :

- 86 298 points d'eau (86 049 géolocalisés), dont 12 178 forages, 3 241 forages à pompe manuelle (FPMH), 8 050 puits
  protégés, 7 045 puits non protégés, 2 173 puits à pompe manuelle (PPMH), des sources et 46 523 bornes-fontaines ;
  état de fonctionnement ; région, district, commune, localité. **Ni profondeur, ni niveau statique, ni débit, ni
  date d'ouvrage.**
- Par commune : nombre de points par type et état ; population 2018 à 2026 ; bénéficiaires 2025 et 2026.
- Par région : taux d'accès à l'eau (2025, 2026). Les ventilations régionales sont des proportions fixes d'une
  région à l'autre (eau de surface entre 0,595 et 0,598 fois « non amélioré ») : seul le taux d'accès global est lu.
- 5 704 systèmes d'adduction (AEP), géolocalisés, avec leur état.

## 2. Questions et critères d'utilité (fixés avant calcul)

**Q1. Qualité.** Part des points avec coordonnées valides (à terre, à Madagascar), coordonnées en double, valeurs
arrondies ; cohérence de la population SEAM avec la projection nationale (environ 30 millions en 2025) ; part des
communes sans population. *Utile si* plus de 90 % des forages et puits ont une position valide.

**Q2. Représentativité des relevés MGMERL.** Les 1 000 forages mesurés représentent-ils les 15 419 forages (forages et
FPMH) du pays ? Comparaison des distributions de six variables de terrain déjà utilisées par l'hybride (altitude,
HAND, pente, pluie annuelle, profondeur du socle, classe GLiM) : différence moyenne standardisée (DMS) et part des
forages SEAM hors de l'étendue des relevés (au-delà des percentiles 1 et 99), par région. *Utile si* le résultat
permet de délimiter le domaine où la carte extrapole (forages SEAM hors étendue). Une DMS supérieure à 0,25 signale
un déséquilibre.

**Q3. Hypothèse H-S1 : les puits signalent une nappe peu profonde.** Un puits creusé à la main n'atteint en général
que les premiers mètres à la première dizaine de mètres ; là où les puits dominent parmi les ouvrages d'eau
souterraine, la nappe devrait être moins profonde.
- Indice, pour chaque forage MGMERL, dans un rayon de 5 km : part de puits = (puits protégés + non protégés + PPMH)
  / (ces puits + forages + FPMH). Les points SEAM à moins de 200 m du forage sont exclus (le forage mesuré y figure
  probablement lui-même). Au moins 5 ouvrages dans le rayon, sinon valeur manquante. Sensibilité : rayons de 2 et
  10 km.
- Test 1 (lien) : corrélation de Spearman entre la part de puits et le niveau mesuré, sur tous les forages, puis dans
  chaque région d'au moins 10 forages. **H-S1 soutenue** si ρ < 0 avec p < 0,01 sur l'ensemble, et ρ < 0 dans au moins
  6 régions sur 8.
- Test 2 (apport), seulement si le test 1 soutient H-S1 : ajout de la part de puits (et du nombre d'ouvrages dans le
  rayon) à l'hybride S0, avec les critères de la phase 0 ; gardée seulement si les deux critères principaux
  s'améliorent (même règle que la phase 1). Comme la variable existe sur tout le territoire où il y a des ouvrages,
  elle peut améliorer la carte dans les régions sans relevé.
- Limite connue : le choix entre puits et forage dépend aussi des projets, des bailleurs et des usages locaux, pas
  seulement de la profondeur de la nappe.

**Q4. Pression sur la ressource (risque d'épuisement).** Par commune : population, nombre d'ouvrages d'eau
souterraine fonctionnels, population par ouvrage fonctionnel. *Utile si* plus de 80 % des communes ont une
population non nulle et que la somme est cohérente avec la projection nationale (écart inférieur à 15 %) ; alors la
population communale SEAM et le nombre d'ouvrages remplacent l'hypothèse uniforme dans le calcul des prélèvements
(section 5 du protocole-cadre).

**Q5 (exploratoire, sans décision).** Part de forages non fonctionnels par district, comparée à la profondeur
estimée de la nappe et à la recharge : une panne peut venir d'une nappe trop basse comme d'une pompe cassée ;
l'analyse est descriptive.

## 3. Ce qui n'est pas fait

Pas de liaison avec d'autres bases (identifiants mWater ou autres) à ce stade ; pas de lecture des fiches point par
point ; pas de requête autre qu'une lecture.

## 4. Sorties

`validation/seam_utilite.md` (rapport, réussites et échecs) et CSV agrégés ; script `scripts/etude_seam.py` testé sur
données simulées ; journal et registre (R-42).

## 5. Mise à jour

Si l'étude conclut à l'utilité, un workflow programmé (lecture hebdomadaire, une requête à la fois) sera ajouté.

## 6. Références

MEAH, SEAM (2026). Fan et al. (2017) pour la carte mondiale de la nappe ; MacDonald et al. (2021) pour la recharge.

## 7. Journal des modifications

- 03/11/2026 : version initiale.
