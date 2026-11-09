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
| Température du canal de Mozambique | ERSST v5, anomalie moyenne sur 35-45°E, 25-15°S ; à calculer (ajout du 02/11, section 9) | 1950 à aujourd'hui |
| Creux du canal de Mozambique | ERA5, tourbillon à 850 hPa (attribution seulement ; à télécharger) | 1981-2025 |
| Relief, géologie | GLO-90 et carte BGS (déjà dans le système) | — |
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
- 02/11/2026, **avant tout calcul**, à la demande du porteur du projet (« pour le sud-ouest, regarde la topographie,
  le canal de Mozambique et la géologie ») :
  - **Relief.** Le sud-ouest est sous le vent des Hautes Terres : les alizés y apportent peu de pluie liée au relief,
    et ses épisodes extrêmes viennent plutôt de systèmes du canal de Mozambique. Le relief de Madagascar crée
    lui-même le creux du canal de Mozambique (Barimalala et al. 2018, *Geophysical Research Letters* 45, 11380-11389) ;
    un creux plus marqué donne plus de pluie sur Madagascar. Analyse descriptive ajoutée : les districts du Grand Sud
    sont classés, avant tout calcul, en « versant au vent » ou « sous le vent » selon l'orientation de la pente
    principale (relief GLO-90) par rapport aux alizés d'est. Les résultats du maillon A sont présentés pour chacun des
    deux groupes.
  - **Canal de Mozambique.**
    - Nouveau prédicteur connu avant la saison : l'anomalie de température de surface du canal (35-45°E, 25-15°S),
      moyenne de juillet à septembre, calculée à partir d'ERSST v5 comme le DMI. Le contrôle des tests multiples porte
      désormais sur 3 régions × 4 indices.
    - Analyse d'attribution (secondaire, jamais utilisée pour la prévision) : intensité du creux du canal en
      décembre-février, mesurée par le tourbillon à 850 hPa d'ERA5 au-dessus du canal (données à demander à l'agent de
      téléchargement, après ERA5-Land).
    - Dans l'analyse des cyclones : les mois extrêmes sont séparés selon que le cyclone est né ou est passé dans le
      canal de Mozambique, ou est venu de l'est.
  - **Géologie.** Pour le maillon B, chaque site de nappe est classé avant tout calcul selon la carte géologique et
    hydrogéologique (BGS) : sédimentaire ou karst (plateau Mahafaly, Isalo, dépôts côtiers) ou socle cristallin. Les
    réponses aux mois extrêmes sont décrites séparément par classe. On s'attend à une réponse plus rapide dans le
    karst, où l'eau s'infiltre vite, que dans le socle, où elle passe par les fractures. Cette attente reste
    descriptive : avec 7 sites, pas de test.
  - H-A, H-B et H-B2 gardent le même énoncé. Les ajouts sont des prédicteurs et des stratifications fixés avant tout
    calcul.
- 09/11/2026 (avant tout calcul du maillon A) : **analyse de puissance** (`validation/puissance_hn7.md`, simulation
  seule). Avec 45 saisons, un résultat binaire et 9 tests corrigés (Benjamini-Hochberg 10 %), la puissance de
  l'épreuve 3 est de 11 à 17 % pour un lien r = 0,3 s'il n'y en a qu'un seul vrai, et de 33 à 45 % s'il y en a trois.
  Elle n'atteint 50 % qu'avec r ≈ 0,5 (un lien) ou r ≈ 0,4 (trois liens). Selon la règle adoptée le 09/11/2026, le
  maillon A est **déclaré exploratoire dès maintenant** : un résultat négatif ne réfutera pas le lien océan → pluies
  extrêmes. Pistes pour gagner en puissance, non adoptées à ce stade : nombre de mois extrêmes ou pluie maximale
  mensuelle (variable continue) au lieu du résultat binaire ; moins de tests (région et indice choisis par la
  littérature).
- 09/11/2026 (avant tout calcul, décision du porteur du projet, après `puissance_hn7.md`) : **test principal unique du
  maillon A** : corrélation de Spearman entre l'**ONI de juillet-septembre** (année Y − 1) et la **pluie du mois le plus
  fort** de la saison novembre-avril (fin en Y) dans la région **Atsimo-Andrefana** (Sud-Ouest), 45 saisons
  1981-2025, p bilatéral par permutation (5 000 tirages), seuil 5 %. Choix de la littérature : lien El Niño - pluies
  d'été du Sud-Ouest (*Theoretical and Applied Climatology*, 2016). Puissance simulée : 47 % pour r = 0,3, 74 % pour
  r = 0,4 ; le test reste **exploratoire de justesse** pour un lien modéré. Publiés à titre descriptif : validation
  croisée (régression, une saison laissée de côté, MSSS) et test chronologique (jusqu'en 2005 / après). Les 8 autres
  combinaisons (Androy, Anosy ; DMI, SIOD, canal de Mozambique) et la définition binaire d'origine (au moins un mois au
  95e centile) sont calculées **à titre exploratoire** (Benjamini-Hochberg 10 %).
