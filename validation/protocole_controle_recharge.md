# Protocole : contrôle de vraisemblance de la recharge transférée (T2c)

*Rédigé le 09/11/2026, **avant** tout calcul. Suite de l'atlas par sous-bassin (`validation/atlas_sousbassins.md`) et de
H-C6 (`validation/transfert_recharge_hc6.md`). Toute modification sera datée en section 8.*

## 1. Question

La recharge transférée T2 (5 analogues africains, distance de Gower) se trompe dans les deux sens. Elle **surestime**
aux sites suivis du Grand Sud : 77 à 262 mm/an transférés, contre 6 à 48 mm/an mesurés par fluctuation de nappe. Elle
**sous-estime** sur la côte Ouest : 6,8 mm/an à Mahajanga pour 1 472 mm de pluie, alors que la carte BGS donne 124 mm,
et 20 mm/an à Toliara, alors que les puits karstiques voisins mesurent 80 à 195 mm/an. Ces erreurs faussent le bilan
prélèvements / recharge des 36 sous-bassins à bilan élevé.

Un contrôle physique simple, qui borne la **part de la pluie qui recharge la nappe** (R/P) selon le type d'aquifère et
le climat, corrige-t-il ces erreurs sans être réglé sur les sites malgaches ?

## 2. Données

- Grille T2 : `data/mdg/nappes_mondiales/recharge_transferee.csv` (T2 et intervalle de 80 %, pluie moyenne
  `LTA_P_mmpa`, aridité, groupe d'aquifère BGS).
- Bornes : les sites africains de recharge mesurée au sol (MacDonald et al. 2021, figshare 23592666, déjà utilisés
  pour T2), avec leur recharge, leur pluie, leur aridité et leur groupe d'aquifère BGS.
- **Aucune donnée malgache ne sert à fixer les bornes.** Les 8 références malgaches de H-C6 servent uniquement à
  vérifier le résultat (section 4).

## 3. Méthode (fixée avant calcul)

1. Pour chaque site africain : rapport r = R / P.
2. Classes : groupe d'aquifère BGS (socle, sédimentaire consolidé, non consolidé, autre) × climat (aride ou semi-aride
   si l'indice d'aridité P/ETP est inférieur à 0,5, humide ou sub-humide sinon). Pour chaque classe : bornes basse et
   haute = quantiles à 10 % et à 90 % de r. Si une classe a moins de 10 sites, on prend le groupe d'aquifère seul,
   tous climats confondus ; s'il a encore moins de 10 sites, on prend tous les sites.
3. Pour chaque maille de Madagascar : r_T2 = T2 / P. La maille est **signalée** si r_T2 sort des bornes de sa classe.
4. Recharge corrigée **T2c** : T2 ramenée dans l'intervalle [q10 × P ; q90 × P] de sa classe. Son intervalle de 80 %
   est la partie commune entre l'intervalle de T2 et cet intervalle ; s'ils ne se recouvrent pas, on prend
   [q10 × P ; q90 × P].
5. Le reste de la chaîne est inchangé : mêmes fokontany, même rattachement à la maille la plus proche, même calcul du
   bilan.

## 4. Hypothèses (fixées avant calcul)

- **H-R1** (descriptive) : on s'attend à ce que la plupart des mailles signalées soient au-dessus de la borne haute
  dans le Grand Sud (au sud de 23° S), et sous la borne basse sur la côte Ouest. Résultat publié avec la part de
  mailles signalées, par région et par groupe d'aquifère.
- **H-R2** (vérification indépendante) : T2c place **au moins 5 des 8 références malgaches** de H-C6 dans son
  intervalle de 80 %, contre 3 sur 8 pour T2. Même liste et même mode d'évaluation que H-C6. La référence du plateau
  Mahafaly, non évaluée dans H-C6, reste non évaluée, pour ne pas changer la règle après coup.
- **Contrôles nommés** (descriptifs, ce sont eux qui ont révélé le problème, ils ne valent donc pas preuve) : T2c à
  Mahajanga comparé à la carte BGS (124 mm/an) ; T2c près de Toliara comparé à la fourchette des puits karstiques
  (80 à 195 mm/an).

## 5. Décision

- Si H-R2 est soutenue : T2c remplace T2 dans `nappes_ressource.py`, puis on refait l'atlas par bassin et par
  sous-bassin. On publie les 36 sous-bassins avant et après correction.
- Si H-R2 n'est pas soutenue : T2 reste la valeur centrale ; le bilan est publié avec la fourchette T2 / T2c, et les
  sous-bassins dont la classe de bilan change entre les deux sont marqués « incertains ».
- Dans les deux cas : on croise ensuite avec les bassins hydrogéologiques (petits bassins côtiers où la nappe peut
  passer d'un bassin à l'autre).

## 6. Sorties

`validation/controle_recharge.md` (bornes par classe, part de mailles signalées, H-R1, H-R2, contrôles nommés) et
`inputs/hydrogeologie/recharge_t2c.csv` (maille : T2, T2c, intervalle, classe, signalée ou non). Calcul sur GitHub
(nouveau workflow), comme les autres calculs de nappes.

## 7. Limites

- Le karst n'est pas un groupe BGS distinct : il est classé dans le sédimentaire consolidé, où la recharge est
  souvent bien plus forte. Les bornes de ce groupe peuvent donc être trop basses autour de Toliara ; on le signalera.
- Les bornes viennent de sites africains : elles supposent que le rapport R/P se transfère mieux que la recharge
  elle-même ; c'est précisément ce que H-R2 vérifie.
- La pluie moyenne `LTA_P_mmpa` est celle de la grille du BGS ; son erreur se reporte sur les bornes.
- La fluctuation de nappe des sites du Sud peut elle-même sous-estimer la recharge (voir H-C6).

## 8. Journal des modifications

- 09/11/2026 : version initiale.
