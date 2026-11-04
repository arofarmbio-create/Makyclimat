# Protocole : atlas des nappes par bassin versant (carte v2)

*Rédigé le 04/11/2026, **avant** tout calcul. Demande du porteur du projet : travailler bassin par bassin, selon le
relief et le profil hydrique du sol. S'appuie sur la carte du niveau statique v2 (`nappes_carte_nationale.md`) et la
ressource v1 (`nappes_ressource.md`). Analyse descriptive : aucune hypothèse confirmatoire. Toute modification sera
datée en section 7.*

## 1. Objectif

Fournir, pour chacun des 108 grands bassins versants du système (`hydro.npz`, découpage par le relief GLO-90), une
fiche synthétique de la nappe : état, ressource, pression, relief, eau du sol, et **fiabilité**. C'est l'unité de
gestion de l'eau (agences de bassin, plans de gestion).

## 2. Rattachement

Chaque fokontany est rattaché au bassin de la maille de 0,005° qui contient son point représentatif.

## 3. Indicateurs par bassin

- Taille : surface (somme des fokontany), nombre de fokontany, population (WorldPop ramenée à SEAM).
- Nappe : niveau statique médian et intervalle interquartile des fokontany ; erreur attendue médiane ; part des
  fokontany en extrapolation ; nombre de relevés MGMERL dans le bassin et densité (pour 1 000 km²).
- Ressource : recharge médiane (T2) ; stock médian ; renouvellement médian.
- **Bilan du bassin** : prélèvements domestiques totaux / recharge totale (sommes pondérées par la surface), à la norme
  Sphère (15 L/j) ; Antananarivo en fourchette (réseau desservant 47 % ou coupé). Classes : faible (< 0,1), modéré
  (0,1 à 0,4), élevé (> 0,4).
- Relief : altitude moyenne, pente moyenne, part en fond de vallée (HAND < 5 m) (`hydro.csv`).
- Eau du sol : réserve utile (`whc_mm`), humidité relative du sol récente (`sm_rel_pct`) (`soilwater.csv`).

## 4. Fiabilité du bassin (règle fixée)

- **Mesurée** : au moins 10 relevés MGMERL dans le bassin et moins de 30 % des fokontany en extrapolation.
- **Partielle** : au moins un relevé, ou moins de 60 % en extrapolation.
- **Non mesurée** : aucun relevé et au moins 60 % en extrapolation.

## 5. Limites

Recharge non validée (H-C6, `recharge_fluctuation.md`) ; pression domestique seulement (bétail, irrigation et
industrie non comptés) ; niveau statique approximatif hors du Grand Sud. Le bilan du bassin est une borne basse de
la pression dans le Sud.

## 6. Sorties

`validation/atlas_bassins.md` (tableau des bassins, classés par pression puis par fiabilité) ;
`external/nappes_bassins.csv` (indicateurs par bassin) ; journal et registre (R-41).

## 7. Journal des modifications

- 04/11/2026 : version initiale.
- 04/11/2026, **avant calcul** : déclinaison par **sous-bassin** (16 177 sous-bassins de `hydro.npz`, seuil de 300 km²),
  mêmes indicateurs et même règle de fiabilité ; seuls les sous-bassins contenant au moins un fokontany sont décrits ;
  nom = « sous-bassin n° x du bassin de … » (bassin majoritaire de ses fokontany). Le rapport liste les 30 sous-bassins
  au bilan le plus fort parmi ceux d'au moins 1 000 habitants, et la répartition des classes de bilan.

