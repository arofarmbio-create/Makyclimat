# Protocole : test de la mémoire hydrique du sous-sol (THMS) dans le Grand Sud

*Rédigé le 04/11/2026, **avant** tout calcul. Idée du porteur du projet (note de travail personnelle, gardée hors du
dépôt public). Lien avec le transfert de connaissances (`protocole_transfert_analogues.md`) : si les paramètres de
mémoire suivent la géologie (dont le karst, H-K1), ils pourront être estimés là où il n'y a pas de mesure. Toute
modification sera datée en section 9.*

## 1. Question

Représenter la recharge comme la somme de plusieurs « mémoires » (transferts rapides, intermédiaires, lents) prédit-il
mieux l'évolution du niveau des nappes du Grand Sud qu'une mémoire unique ?

## 2. Positionnement (à compléter par la recherche bibliographique systématique)

Le noyau mathématique (somme de réponses exponentielles, réservoirs linéaires en parallèle) existe : modèles à
fonction de transfert (Von Asmuth et al. 2002 ; Pastas, Collenteur et al. 2019), modèles globaux à réservoirs
(Gardenia, BRGM), Peterson et Western 2014. La contribution visée n'est pas ce noyau, mais : (1) des paramètres de
mémoire liés à la lithologie, au karst et aux structures ; (2) leur transfert vers les zones sans mesure ; (3) une
méthode adaptée aux données malgaches incomplètes.

## 3. Données

- Niveaux : 7 capteurs MGMERL (HT Analytics) retenus par `recharge_fluctuation.md` (au moins 24 mois valides, 2019 à
  2025), 5 puits GROSoM de la région de Toliara retenus (2014 à 2020). Contrôle qualité de `protocole_nappes_mgmerl.md`.
  Moyenne journalière.
- Pluie : CHIRPS journalier à 0,1° (données E1, source du système), maille du site ; jours manquants : le site est
  ignoré ces jours-là.
- Évapotranspiration de référence : climatologie mensuelle Open-Meteo (ERA5-Land, cache du système), point le plus
  proche, répartie uniformément sur les jours du mois.
- Période : intersection des séries de niveau et de pluie (pluie disponible jusqu'au 31/12/2025).

## 4. Modèle (pas journalier)

1. **Sol** (eau disponible pour l'infiltration) : réservoir de capacité Smax ; évapotranspiration réelle =
   ET0 × stock / Smax ; le surplus au-delà de Smax est I(t). Ruissellement non séparé (limite, section 8).
2. **Recharge à M mémoires** : R(t) = Σ w_j × (I convolué avec exp(−τ/T_j)/T_j), j = 1…M, réalisé par M réservoirs
   linéaires ; w_j ≥ 0, Σ w_j ≤ 1 ; T_1 < T_2 < T_3 (ordre imposé pour l'identifiabilité), bornes de 1 à 3 000 jours.
3. **Nappe** : dh/dt = R(t)/Sy − (h − h0)/τd (drainage linéaire vers un niveau de base h0, à la place des pertes
   latérales et pompages inconnus) ; Sy dans la fourchette du type d'aquifère (socle 0,01 à 0,05 ; sédimentaire 0,05 à
   0,15) ; niveau simulé comparé au niveau mesuré (profondeur sous repère).
4. Paramètres : Smax, w_j, T_j, Sy, τd, h0 ; M = 1 : 6 paramètres ; M = 2 : 8 ; M = 3 : 10.
5. Calage : par site, sur les **60 % premiers** de la série, en maximisant le KGE des niveaux journaliers
   (évolution différentielle, graine fixée, 1 an d'échauffement). Validation : **40 % suivants**, jamais vus.

## 5. Hypothèses (fixées avant calcul)

- **H-M1** : le nombre de mémoires choisi sur le calage (M qui minimise l'AIC) prédit mieux sur la validation qu'une
  mémoire unique (KGE de validation plus élevé) sur au moins 9 des 12 sites (test du signe unilatéral, p < 0,05).
- **H-M2 (exploratoire)** : la part des mémoires rapides (w_1) est plus grande dans le sédimentaire de Toliara
  (en partie calcaire) que sur le socle ; avec ~12 sites, aucune conclusion confirmatoire.
- **H-M3 (exploratoire, lien avec le karst H-K1)** : les sites karstiques (WOKAM) ont un temps de mémoire rapide T_1
  plus court et une part w_1 plus forte.

## 6. Référence de comparaison

M = 1 (réservoir unique), qui correspond à l'approche courante. Aucun autre modèle n'est ajouté à ce stade
(pas de multiplication des modèles).

## 7. Règle de suite (fixée avant calcul)

- H-M1 soutenue : protocole d'extension à tout Madagascar par bassin versant (relief, profil hydrique du sol),
  avec transfert des paramètres par analogues géologiques, écrit avant calcul.
- H-M1 non soutenue : publié tel quel ; pas d'extension ; examen des causes (données, identifiabilité).

## 8. Limites connues

Pluie de maille (0,1°) et non au forage ; ruissellement non séparé ; pompages et échanges latéraux réduits à un
drainage linéaire ; séries courtes (quelques années) ; équifinalité possible (rapportée par la dispersion des
paramètres sur plusieurs graines, à titre descriptif).

## 9. Journal des modifications

- 04/11/2026 : version initiale.
