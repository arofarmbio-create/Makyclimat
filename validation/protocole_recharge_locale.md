# Protocole : recharge transférée corrigée par les mesures malgaches (T2L)

*Rédigé le 09/11/2026, **avant** tout calcul. Suite de l'échec de H-R2 (`validation/controle_recharge.md`) : des
bornes tirées des sites africains ne corrigent pas les erreurs malgaches. Toute modification sera datée en section 9.*

## 1. Question de recherche

Quand une recharge a été transférée depuis une base continentale (134 sites africains du BGS ; MacDonald et al. 2021)
vers un pays presque sans mesures, **une poignée de mesures locales suffit-elle à corriger ce transfert ?** Et peut-on
dire **jusqu'où** la correction reste valable ? La question vaut pour tout pays pauvre en données ; Madagascar est le
cas d'étude.

## 2. Ce qui est déjà connu (à déclarer honnêtement)

Les 12 sites retenus de `validation/recharge_fluctuation.md` (au moins 24 mois de mesures) ont déjà été regardés :
- socle (6 sites MGMERL du Grand Sud) : rapport mesuré / T2 de 0,04 à 1,07 (médiane 0,19 environ) ;
- non consolidé (Sihanamaro, MGMERL ; 5 puits GROSoM près de Toliara) : 0,30 pour Sihanamaro, 2,1 à 5,2 pour GROSoM.

L'effet du groupe d'aquifère est donc **déjà vu**. La validation croisée ci-dessous dit si une correction apprise sur
une partie des sites prédit les autres ; elle n'est pas un test à l'aveugle. Le test vraiment indépendant est
prospectif (section 6).

## 3. Données

- Sites : les 12 sites retenus, recharge par fluctuation de nappe, méthode mensuelle (méthode principale du protocole
  `protocole_recharge_fluctuation.md`), avec leur fourchette selon le rendement spécifique (Sy bas ; Sy haut).
- Groupe d'aquifère et T2 : maille la plus proche de `recharge_transferee.csv` (comme dans `recharge_fluctuation.py`).
- Coordonnées : séries hors dépôt (MGMERL, GROSoM) ; calcul local, seules des valeurs agrégées sont publiées.

## 4. Modèles comparés (fixés avant calcul)

Résidu d'un site : e = ln(mesurée / T2).
- **M0** : T2, sans correction.
- **M1** : facteur unique, T2 × exp(médiane des e des sites d'apprentissage).
- **M2** : facteur par groupe d'aquifère (socle ; autres), médiane des e des sites d'apprentissage du même groupe ;
  repli sur M1 si le groupe a moins de 2 sites d'apprentissage.
- **M3** : M2 + correction locale du résidu restant, pondérée par la distance et ramenée vers zéro loin des sites :
  c(x) = Σ wᵢ uᵢ / (1 + Σ wᵢ), wᵢ = exp(−dᵢ / L), uᵢ = résidu du site i après M2, sites du même groupe seulement,
  **L = 25 km** (rayon fixé maintenant ; 10 et 50 km publiés à titre descriptif).

## 5. Validation et hypothèses (fixées avant calcul)

- **Validation par groupe de sites laissé de côté** : les sites à moins de 20 km les uns des autres forment un
  groupe (lien simple) ; chaque groupe est retiré à son tour, le modèle est appris sur les autres et prédit les sites
  retirés. C'est le critère principal : il empêche un voisin immédiat de « souffler » la réponse. La validation site
  par site est publiée en complément.
- Un site est **retrouvé** si la valeur prédite tombe dans sa fourchette mesurée [Sy bas ; Sy haut].
- Erreur : médiane de |log₁₀(prédite / mesurée)|.
- **H-L1** : M2 retrouve **au moins 6 sites sur 12** et divise par au moins deux l'erreur médiane de M0.
- **H-L2** : M3 fait mieux que M2 : au moins un site retrouvé de plus **et** une erreur médiane plus faible.
- M1 est publié pour savoir si le groupe d'aquifère apporte quelque chose au-delà d'un facteur unique.

## 6. Validation prospective (le test indépendant)

Avant l'arrivée de nouvelles mesures (ministère de l'Eau, autres puits suivis), la carte T2L et son domaine de
validité sont **figés et publiés** avec la date et l'empreinte du fichier. Toute nouvelle mesure de recharge sera
comparée à ces prédictions figées, sans recalcul. Règle de réussite fixée maintenant : au moins 60 % des nouveaux
sites situés dans le domaine sont retrouvés.

## 7. Carte T2L et décision

- Carte : M2, plus M3 si H-L2 est soutenue, appris sur les 12 sites, appliqué aux mailles **dans le domaine de
  validité** : même groupe d'aquifère qu'au moins 2 sites, et à moins de 100 km d'un site de ce groupe. Hors du
  domaine : T2 inchangée, maille marquée « hors domaine ».
- Si H-L1 est soutenue : T2L devient la valeur centrale dans son domaine ; l'atlas par sous-bassin est refait et
  comparé à l'atlas T2. Sinon : T2 reste la valeur centrale, T2L est publiée comme sensibilité.

## 8. Limites

- 12 sites, tous dans le Sud et le Sud-Ouest : le domaine couvre le Sud, pas le reste de l'île.
- La fourchette de Sy rend chaque mesure incertaine d'un facteur 3 à 5 ; un site « retrouvé » l'est dans cette
  fourchette.
- La méthode journalière donne des recharges bien plus fortes que la méthode mensuelle ; on garde la méthode
  mensuelle fixée auparavant ; la journalière est publiée à titre de sensibilité.
- Le groupe GROSoM est en partie karstique alors que la grille le classe en non consolidé.

## 9. Journal des modifications

- 09/11/2026 : version initiale.
- 09/11/2026 (résultat) : H-L1 et H-L2 non soutenues (`validation/recharge_locale.md`). T2 reste la valeur centrale ;
  T2L publiée comme sensibilité et figée pour la validation prospective (empreinte dans le rapport).
