# Protocole H-N7 : El Niño et l'océan Indien, pluies extrêmes et recharge des nappes du Grand Sud

*Rédigé le 02/11/2026, **avant** tout calcul. Protocole doctoral : modules M1, M3, M7 ; expériences E4 (anticipation
sans fuite) et E6 ; hypothèses H3, H4, H6. Prolonge `protocole_nappes_mgmerl.md` et
`biblio_hydrogeologie_grand_sud.md`. Toute modification sera datée en section 9, avant de voir les résultats
concernés.*

## 1. Question

Dans le Grand Sud, un bilan mensuel ne voit presque aucune recharge (registre R-37, M3) : la littérature dit qu'elle
vient d'épisodes brutaux. Peut-on relier, en une chaîne vérifiable :

- **maillon A** : l'état de l'océan avant la saison (El Niño, dipôle de l'océan Indien, dipôle subtropical) → le
  nombre de mois de pluie extrême de la saison ;
- **maillon B** : les mois de pluie extrême → les remontées des nappes mesurées ;
- **maillon C** : donc, dès octobre, une probabilité qu'une saison recharge ou non les nappes ?

Si la chaîne tient, elle annonce plusieurs mois à l'avance les années de recharge ou de pénurie d'eau souterraine
dans une région où la sécheresse est meurtrière.

## 2. Positionnement (recherche du 02/11/2026)

- Taylor et al. (2013, *Nature Climate Change* 3, 374-378), Tanzanie centrale : la recharge dépend des mois de pluie
  au-delà du 95e centile, souvent renforcés par El Niño et le dipôle de l'océan Indien.
- Kolusu et al. (2019, *HESS* 23, 1751-1762) : El Niño 2015-2016, dipôle nord-sud. Sécheresse record en Afrique
  australe et baisse des stocks d'eau souterraine du Limpopo ; hausse en Tanzanie.
- Cuthbert et al. (2019, *Nature*) : dans les zones sèches d'Afrique subsaharienne, la recharge vient surtout des
  fuites des rivières et des mares lors des fortes pluies et des crues, liées à El Niño et La Niña.
- **Sud-ouest de Madagascar** (*Theoretical and Applied Climatology*, 2016) : la plupart des étés El Niño sont plus
  secs et les étés La Niña plus humides, mais le lien avec les fortes pluies est « moins clair ».
- **Madagascar** (*Theoretical and Applied Climatology*, 2022) : une phase positive du dipôle de l'océan Indien ou du
  dipôle subtropical augmente la pluie du sud en saison des pluies.
- Notre propre résultat (`teleconnexions.md`) : signal El Niño → plus sec dans le Sud et le Sud-Ouest, mais non retenu
  après le contrôle des tests multiples.
- **Ce que ce chapitre ajoute :** aucune étude trouvée ne relie, pour le Grand Sud de Madagascar, l'état de l'océan,
  les pluies extrêmes et des niveaux de nappe mesurés. Le sens de l'effet de l'océan n'est pas connu d'avance : les
  tests sont donc bilatéraux.

## 3. Données

| Donnée | Source | Période |
|---|---|---|
| Pluie mensuelle par région | CHIRPS v2.0 (déjà dans le système) | 1981-2025 (45 saisons) |
| Pluie journalière | CHIRPS et IMERG Late de l'expérience E1 (en cours de téléchargement) | 2001-2025 |
| ONI | NOAA CPC (déjà dans le système) | 1950 à aujourd'hui |
| DMI | ERSST v5, `connector_dmi.py` (déjà dans le système) | 1950 à aujourd'hui |
| SIOD (dipôle subtropical) | ERSST v5, même méthode : (55-65°E, 37-27°S) moins (90-100°E, 28-18°S), Behera et Yamagata (2001) ; à calculer | 1950 à aujourd'hui |
| Cyclones | IBTrACS (déjà dans le système) | 1981-2025 |
| Niveaux de nappe | MGMERL HT Analytics (16 sites, 7 retenus en M3) ; puis Water Missions, Lorentz, relevés ACF, GROSoM, à obtenir | 2019-2025 pour l'instant |

Régions du Grand Sud : Androy, Anosy, Atsimo-Andrefana.

## 4. Définitions fixées à l'avance

- **Mois extrême** : pluie régionale du mois au-dessus du **95e centile** de tous les mois de novembre à avril sur
  1981-2025 (seuil de Taylor et al. 2013, choisi avant tout calcul).
- **E** : nombre de mois extrêmes de la saison (novembre à avril).
- **Prédicteurs connus avant la saison** (anticipation, protocole E4-B) : moyennes de juillet à septembre de l'ONI, du
  DMI et du SIOD, disponibles début octobre. Les moyennes de décembre à février servent seulement à l'attribution
  (analyse secondaire), jamais à la prévision.
- **Remontée de nappe** : variation mensuelle du niveau ΔL(t) = L(t) − L(t − 1), sur les séries contrôlées comme en M3
  (mêmes règles de la section 4 de `protocole_nappes_mgmerl.md`).

## 5. Méthodes et hypothèses

### Maillon A : océan → pluies extrêmes (45 saisons)

- **H-A (principale)** : pour au moins une région du Grand Sud, un modèle de probabilité qu'une saison compte au moins
  un mois extrême, établi avec les prédicteurs de juillet-septembre, bat la climatologie. Il doit passer les mêmes
  quatre épreuves que la planification à 12 mois (`protocole_planification_12mois.md`) :
  1. score de Brier ramené à la climatologie (BSS) en validation croisée > 0 ;
  2. BSS chronologique > 0 ;
  3. corrélation de Spearman significative (permutation, bilatérale), après contrôle des tests multiples
     (Benjamini-Hochberg, 10 %) sur 3 régions × 3 indices ;
  4. modèle logistique à un seul prédicteur par région (pas de sélection de variables).
- Si aucune région ne passe, le maillon A est rejeté et publié comme tel. On décrit alors seulement la répartition des
  mois extrêmes selon les phases.
- **Descriptif** : part des mois extrêmes avec le passage d'un cyclone à moins de 500 km (IBTrACS). Si les extrêmes du
  Sud sont surtout cycloniques, l'état de l'océan agit à travers les trajectoires des cyclones.
- **Contrôle avec les pluies journalières** (2001-2025, quand E1 sera complète) : même analyse avec le nombre de jours
  au-dessus du 99e centile journalier, pour CHIRPS et IMERG séparément. Si les deux sources ne donnent pas le même
  signe, le résultat est déclaré dépendant de la source.

### Maillon B : pluies extrêmes → remontées des nappes

- **H-B** : aux sites de nappe, ΔL est plus grand pendant les mois extrêmes (95e centile de la pluie à la maille du
  site) que pendant les autres mois de saison des pluies. Test de Mann-Whitney par site, puis test du signe entre
  sites (unilatéral, 5 %).
- **H-B2** : l'indicateur « mois extrême » est plus corrélé à ΔL que le SPI-1 (Spearman, comparaison site par site,
  test du signe).
- **Statut honnête des données** : les 7 sites MGMERL ont déjà servi au protocole M3. Les tester ici est donc
  **exploratoire**. Le test **confirmatoire** se fera sur des sites indépendants : Water Missions, Lorentz, relevés
  ACF, observatoire GROSoM, ou années de mesure postérieures à juin 2025. Les deux statuts seront publiés séparément.

### Maillon C : la chaîne (seulement si A et B passent)

- Probabilité de saison « rechargeante » annoncée en octobre, comparée aux remontées observées. Avec les séries
  actuelles (2019-2025), ce sera une vérification descriptive, saison par saison, pas un score.

## 6. Fuite d'information

- Le maillon A n'utilise que des prédicteurs connus avant le 1er novembre de chaque saison.
- Les seuils (95e centile) sont fixés par la littérature et calculés sur la période d'apprentissage seulement dans la
  validation chronologique.
- Aucun réglage sur les sites de confirmation.

## 7. Limites connues

- Séries de nappe courtes (2 à 6 ans) : le maillon B reste de faible puissance tant que d'autres sites manquent.
- CHIRPS sous-estime souvent les pluies extrêmes ; c'est pourquoi IMERG est utilisé comme contrôle.
- Pompage, nappes profondes alimentées ailleurs, failles (`biblio_hydrogeologie_grand_sud.md`) : un site peut
  légitimement ne pas répondre à la pluie locale.
- Un mois extrême (cumul mensuel) n'est pas une averse : les jours extrêmes (E1) précisent ce point.
- Recharge par les crues des rivières (Cuthbert et al. 2019) : la pluie du bassin amont, ou le débit GloFAS, pourrait
  mieux convenir pour les nappes alluviales (hypothèse H-N4 du futur protocole M3 bis).

## 8. Mise en œuvre

- Calculs légers, faits sur le PC (règle du porteur du projet) ; les données à télécharger (SIOD depuis ERSST, pluies
  journalières E1, nouveaux sites) passent par l'agent de téléchargement.
- Script : `scripts/validate_climat_extremes_nappes.py`, testé sur des données simulées avant les données réelles.
- Résultats : `validation/climat_extremes_nappes.md` et CSV, puis registre (R-39) et journal, que les résultats soient
  positifs ou négatifs.

## 9. Journal des modifications

- 02/11/2026 : version initiale.
