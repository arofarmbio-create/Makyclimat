# Protocole R-02 bis : un aléa décrit finement redonne-t-il du poids au cyclone à l'intérieur des zones touchées ?

*Rédigé le 02/11/2026, **avant** tout calcul. Prolonge R-02 (`methodologie_these.md` §4.2,
`scripts/validate_fokontany.py`) et répond à la faiblesse identifiée dans `biblio_r02_nouveaute.md`. Protocole
doctoral : modules M4 et M5, expériences E3 (comparaison de modèles, ablation) et E4 (validation par événement), §11 et
§12. Toute modification sera datée en section 9, avant de voir les résultats concernés.*

## 1. Question

R-02 a établi qu'à l'intérieur des zones touchées par un cyclone, au niveau du fokontany, l'aléa tel que le système le
décrit ne sépare pas les fokontany endommagés ou inondés des autres (AUC 0,51 à 0,52), alors que le terrain les sépare
nettement (AUC 0,79 au fokontany, 0,82 à la commune).

Mais l'aléa de R-02 est grossier : couverture de l'empreinte de vent de la trajectoire IBTrACS et rareté de la pluie
journalière CHIRPS. R-02 bis tranche la question suivante : **l'absence de pouvoir de l'aléa vient-elle de sa
description trop grossière, ou d'un vrai effet d'échelle ?**

## 2. Recherche bibliographique systématique (pour établir la nouveauté)

La recherche du 02/11/2026 (`biblio_r02_nouveaute.md`) a trouvé les travaux voisins : Tang et al. 2023 (dépendance
d'échelle des fonctions de dommages, Chine) et Kooshki Forooshani et al. 2024 (modèle d'impact sur grille de 0,1°,
Philippines). Pour pouvoir affirmer la nouveauté devant le jury, elle est complétée, avant la publication des
résultats, par une recherche **systématique et traçable** :

- **Bases** : Google Scholar, Scopus ou Web of Science selon l'accès de l'Université d'Antananarivo, archives HAL et
  bibliothèque de l'IRD, ReliefWeb (littérature grise).
- **Requêtes** (en anglais et en français), combinant : *tropical cyclone OR typhoon OR hurricane* ; *damage OR impact
  OR flood extent* ; *scale OR spatial resolution OR aggregation* ; *terrain OR HAND OR topography* ; *village OR
  municipality OR fokontany* ; *Madagascar OR Africa*.
- **Critères d'inclusion** : étude empirique qui compare le pouvoir explicatif de l'intensité de l'aléa et celui du
  terrain sur des dégâts observés, à au moins une échelle infra-communale.
- **Traçabilité** : date, base, requête, nombre de résultats, nombre examinés, travaux retenus et motif de rejet,
  consignés dans `validation/biblio_r02_systematique.csv`.
- **Formulation de la conclusion** : elle sera tirée de ce tableau. Par exemple, « parmi les N travaux examinés selon
  ce protocole, aucun ne… », ou bien le travail antérieur sera cité s'il existe.

## 3. Données

| Donnée | Source | Rôle |
|---|---|---|
| Fokontany touchés et évalués | Copernicus EMS, 7 activations (comme R-02) | Vérité terrain |
| Terrain | HAND, pente, altitude, distance à la rivière, densité (comme R-02) | Modèle « terrain » |
| Aléa grossier | Empreinte de vent IBTrACS, rareté de la pluie CHIRPS journalière (comme R-02) | Référence |
| **Pluie fine** | GPM IMERG V07 Final, 30 min, 0,1° : maxima sur 1, 3 et 6 heures, et cumul de l'événement, à la maille du fokontany | Aléa fin |
| **Vent fin** | Modèle de vent paramétrique de Holland (1980) calculé à partir des trajectoires IBTrACS (rayon de vent maximal, pression centrale), à la position exacte de chaque fokontany ; rafales maximales ERA5 (0,25°, horaire) en contrôle | Aléa fin |

Fenêtre de chaque événement : du premier jour où le centre du cyclone est à moins de 500 km de Madagascar jusqu'à
2 jours après sa sortie, d'après IBTrACS.

Téléchargements (IMERG demi-horaire sur les zones EMS et les fenêtres des événements ; rafales ERA5) : confiés à
l'agent de téléchargement, au rythme contrôlé.

## 4. Modèles comparés (mêmes règles que R-02)

Régression logistique, variables standardisées, **un événement laissé de côté** à chaque fois, aux niveaux fokontany
et commune :

1. **Aléa grossier** (R-02, référence) ;
2. **Aléa fin** : pluie maximale sur 1, 3 et 6 heures, cumul de l'événement, vent de Holland maximal ;
3. **Terrain** (R-02) ;
4. **Terrain et aléa fin**.

Aucune sélection de variables à partir des résultats : les listes ci-dessus sont fixées maintenant.

## 5. Hypothèses fixées à l'avance

- **H-R1 (principale)** : au niveau du fokontany, l'écart AUC(terrain) − AUC(aléa fin) est positif. Intervalle de
  confiance à 95 % obtenu par bootstrap **par événement** (on rééchantillonne les 7 événements entiers, 2 000 tirages).
  Conclusion « effet d'échelle confirmé » si la borne basse dépasse 0.
- **H-R2** : l'aléa fin fait mieux que l'aléa grossier : AUC(aléa fin) − AUC(aléa grossier) > 0, même bootstrap.
- **H-R3** : ajouter l'aléa fin au terrain améliore la prévision. Score de Brier de (4) inférieur à celui de (3),
  même bootstrap.

**Lecture des issues possibles, fixée à l'avance :**
- H-R1 confirmée et H-R3 rejetée : à l'intérieur des zones touchées, le terrain décide **même avec un aléa fin**. R-02
  devient un résultat solide.
- H-R1 confirmée et H-R3 confirmée : le terrain domine, mais l'aléa fin apporte un complément mesurable. Le modèle
  opérationnel doit combiner les deux.
- H-R1 rejetée : l'aléa fin rattrape le terrain. La conclusion de R-02 venait de la résolution de l'aléa ; c'est un
  résultat méthodologique à publier (la résolution de l'aléa compte autant que l'échelle d'analyse).

Puissance : 7 événements seulement. Les intervalles par bootstrap d'événements seront larges ; un résultat non
concluant sera publié comme tel.

## 6. Fuite d'information

Les seuils et les variables sont fixés ici. Chaque modèle est réajusté sans l'événement testé. Le vent de Holland et
la pluie IMERG Final sont des reconstitutions après l'événement (type A du protocole doctoral E4) : R-02 bis teste ce
qui explique les dégâts, pas une capacité d'anticipation. Un test d'anticipation demanderait des prévisions d'archive
(type B) : ce sera un protocole distinct.

## 7. Limites connues

- Copernicus EMS cartographie surtout des zones accessibles ou urbaines, quelques jours après l'événement.
- IMERG sous-estime souvent les pics de pluie les plus courts, et sa maille (0,1°) reste plus grande que la plupart
  des fokontany.
- Le modèle de Holland ignore le freinage du vent par le relief.
- 7 événements, dominés par la côte est.

## 8. Mise en œuvre

- Script : `scripts/validate_r02bis.py`, qui réutilise les fonctions de `validate_fokontany.py` et `validate_events.py`
  (événement laissé de côté, AUC, Brier), avec des tests sur données simulées avant les données réelles.
- Résultats : `validation/r02bis_echelle_alea.md` et CSV, puis registre (R-40) et journal.

## 9. Journal des modifications

- 02/11/2026 : version initiale.
- 09/11/2026 (avant le calcul, règle « puissance avant hypothèse ») : l'unité indépendante est l'activation EMS ; avec
  7 activations, un test du signe entre événements exige 7 sur 7 (puissance 21 % si le modèle fin améliore 80 % des
  événements, `analyse_puissance_retro.md`). Les hypothèses sont **déclarées exploratoires dès maintenant**.
  Téléchargements ordonnés selon les règles de rythme : IMERG (NASA) après la validation MERRA-2 ; rafales ERA5
  (Copernicus) après les reprévisions GloFAS réduites.
