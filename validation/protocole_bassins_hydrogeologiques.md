# Protocole : bassins hydrogéologiques (lignes de partage de la nappe) et bassins de surface

*Rédigé le 04/11/2026, **avant** tout calcul. Demande du porteur du projet. Complète `protocole_atlas_bassins.md`.
Toute modification sera datée en section 7.*

## 1. Question

Les lignes de partage de la nappe (bassins hydrogéologiques) coïncident-elles avec celles de la surface ? Où s'en
écartent-elles, c'est-à-dire où l'eau souterraine peut-elle passer d'un bassin versant à l'autre ?

## 2. Méthode

- Modèle de terrain : Copernicus GLO-90 à 0,005°, même lecture et même chaîne que le système (`build_hydro.py` :
  remplissage des dépressions, écoulement D8, bassins).
- **Charge hydraulique** h = altitude du sol − profondeur du niveau statique (carte v2, valeur du fokontany le plus
  proche pour chaque maille de 0,005°).
- Bassins hydrogéologiques : même calcul que les bassins de surface, mais l'écoulement suit la surface de la nappe h
  (la mer et les pentes sont celles du terrain).
- Comparaison : chaque bassin hydrogéologique est apparié au bassin de surface avec lequel il se recouvre le plus ;
  une maille est « divergente » si elle n'appartient pas au même bassin dans les deux découpages.

## 3. Hypothèse (fixée avant calcul)

Avec une nappe peu profonde (4 à 7 m en médiane) et un relief marqué, la nappe suit la topographie (Tóth 1963 ;
Haitjema et Mitchell-Bruker 2005).
- **H-B1** : au moins 95 % des mailles terrestres sont dans le même bassin dans les deux découpages.
- **H-B2** : les mailles divergentes sont au moins deux fois plus fréquentes là où la pente est inférieure à 2 % que
  là où elle est d'au moins 2 % (plaines côtières et grandes plaines de l'Ouest et du Sud).
Résultat à lire avec la fiabilité de la carte v2 : là où la profondeur est extrapolée, le tracé l'est aussi.

## 4. Sorties

`validation/bassins_hydrogeologiques.md` (taux de divergence, par région et par classe de pente, bassins les plus
concernés) et `inputs/hydrogeologie/divergence_bassins.csv` (part de mailles divergentes par bassin de surface).
Calcul lancé sur GitHub (workflow 28, modèle de terrain téléchargé là-bas).

## 5. Limites

Charge calculée à partir d'une profondeur approximative ; pompages et échanges avec les rivières ignorés ; un écart
entre les deux découpages est une indication, pas une mesure de flux.

## 7. Journal des modifications

- 04/11/2026 : version initiale.
