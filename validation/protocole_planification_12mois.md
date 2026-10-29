# Protocole : scénarios de planification à 12 mois (saison 2027-2028) avec personnes exposées

*Rédigé le 29/10/2026, **avant** tout calcul. Modifications datées en section 7. Cahier des charges §9 (ne pas
prétendre prévoir précisément au-delà de la compétence), §10 (danger, exposition, vulnérabilité séparés), §12
(anticipation), §13.*

## 1. Question

Fin octobre de l'année Y, que peut-on dire de façon fiable de la pluie de la saison suivante (novembre Y+1 à avril
Y+2), région par région ? Et combien de personnes seraient exposées à la sécheresse ou à des pluies excessives,
selon les scénarios plausibles ?

## 2. Règle de fiabilité (non négociable)

- Un signal à 12 mois n'est **utilisé** pour une région que s'il passe **toutes** les épreuves suivantes sur les
  saisons passées :
  - MSSS en validation croisée (saison laissée de côté) > 0 ;
  - MSSS au test chronologique (ajusté jusqu'en 2005, testé après) > 0 ;
  - corrélation significative après contrôle des tests multiples (permutation unilatérale, Benjamini-Hochberg 10 %) ;
  - score de probabilité RPSS > 0 en validation croisée (les probabilités de terciles font mieux que 1/3, 1/3, 1/3).
- Sinon, l'outil affiche des **scénarios climatologiques** : toutes les saisons passées ont le même poids. Il le dit
  explicitement ; aucune prévision n'est suggérée.
- Le module est toujours présenté comme un outil de **planification** (plans de contingence, stocks), jamais comme une
  prévision opérationnelle. Il est remplacé automatiquement par la prévision C3S hybride le 16 octobre de l'année
  de la saison.

## 3. Données et prédicteurs

- Pluie CHIRPS par région (moyenne pondérée par la surface des fokontany), cumuls de novembre-janvier, janvier-mars et
  novembre-avril, saisons 1981-1982 à aujourd'hui.
- Prédicteurs connus à l'émission (fin octobre Y), pour la saison qui se termine en avril Y+2 : ONI de
  juillet-septembre Y et DMI de juillet-septembre Y (décalage d'un an de plus que le modèle saisonnier).
- Contexte physique, descriptif : phase ENSO de l'année Y+1 après chaque année Y de même type (ONI depuis 1950).

## 4. Modèle

- Régression linéaire de l'anomalie standardisée de pluie sur l'ONI seul, et sur l'ONI et le DMI, comme dans
  `build_teleconnections.py`.
- Probabilités de terciles : loi normale centrée sur la prévision, d'écart-type égal à celui des résidus en validation
  croisée, puis bornées à 15-50 % comme la prévision saisonnière du site.
- RPSS calculé avec ces probabilités bornées.

## 5. Personnes exposées

- Pour chaque saison passée j et chaque zone, l'outil calcule déjà :
  - les personnes en zone de sécheresse (niveau d'alerte saisonnier ≥ seuil d'exposition) ;
  - les cibles (pondérées par la vulnérabilité économique) ;
  - les personnes sous pluies excessives (≥ seuil humide) ;
  avec la **population actuelle**.
- Poids de la saison j pour une zone : probabilité du tercile de sa région cette année-là, divisée par le nombre de
  saisons de ce tercile. Ces poids sont uniformes si la région n'a pas de signal validé.
- Publiés : la valeur attendue, et une fourchette (10e et 90e centiles pondérés).
- Limites :
  - population actuelle, sans projection à 2027 ;
  - exposition dérivée de la pluie seule, sans cyclone ;
  - les cyclones de 2027-2028 ne sont pas prévisibles à 12 mois.

## 6. Hypothèse fixée à l'avance

- **H1** : au moins une région a un signal validé à 12 mois pour au moins une période. Si aucune, le résultat est
  publié tel quel : à 12 mois, seule la planification climatologique est défendable.

## 7. Journal des modifications

- 29/10/2026 : version initiale.
- 29/10/2026, avant tout calcul sur données réelles (défauts trouvés par les tests sur données simulées) :
  - sans signal validé, chaque saison passée a **exactement** le même poids (et non 1/3 par tercile, ce qui
    déséquilibrait les terciles de tailles inégales) ;
  - la valeur publiée est la **médiane** pondérée et non la valeur attendue, car une moyenne peut sortir de la
    fourchette 10e-90e centile quand la plupart des saisons n'exposent personne.
