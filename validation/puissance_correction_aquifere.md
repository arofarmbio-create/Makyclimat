# Puissance de la correction de T2 par classe d'aquifère (étape T-H2.3)

Généré par `scripts/puissance_correction_aquifere.py` (500 tirages par case, 199 permutations par
tirage, graine 20261116), selon `validation/protocole_correction_par_aquifere.md`, **avant toute donnée du test**.
Table complète : `validation/puissance_correction_aquifere.csv`.

## 1. Vraisemblance de planification (données déjà vues, R-47)

Les 12 sites de R-47 forment 8 groupes (lien simple à 20 km). Classes déclarées après les avoir vus (GROSoM rangé en
calcaires). e = log10(mesurée / T2), médiane par groupe.

- Médiane de e par classe : calcaires +0.69 (1 groupe(s), 5 sites), sables -0.53 (1 groupe(s), 1 sites), socle -0.73 (6 groupe(s), 6 sites).
- Écart-type de e entre les 6 groupes de socle : **0.53** (log10) ; d'où la grille σ = [0.3, 0.5, 0.7]
  (dispersion entre groupes d'une même classe, erreur de mesure comprise).
- Scénarios de moyennes de classe (log10) : vu : socle -0.73, sables -0.53, calcaires +0.69; moitié : socle -0.63, sables -0.53, calcaires +0.08; quart : socle -0.58, sables -0.53, calcaires -0.23; nul : socle -0.53, sables -0.53, calcaires -0.53; calcaires seuls : socle -0.73, sables -0.73, calcaires +0.69.

**Critères appliqués aux données vues (descriptif, ne décide rien)** : une seule référence en sables et en calcaires,
donc M2c se replie sur M1 pour ces deux groupes. Critère de R-47 : p = 0.078, rapport des erreurs médianes
M2c / M1 = 0.89, échoue. Permutation : gain G = +0.062, p = 0.222.
C'est l'échec de R-47 : sans au moins 2 groupes par classe, la correction par classe n'apprend rien.

## 2. H-A1 retenu (permutation des classes), 3 classes de k groupes

| Scénario | σ | k = 3 | k = 4 | k = 5 | k = 6 | k = 8 |
|---|---|---|---|---|---|---|
| vu | 0.3 | 89 % | 97 % | 100 % | 100 % | 100 % |
| vu | 0.5 | 58 % | 67 % | 88 % | 86 % | 95 % |
| vu | 0.7 | 37 % | 39 % | 59 % | 61 % | 74 % |
| moitié | 0.3 | 42 % | 54 % | 73 % | 74 % | 85 % |
| moitié | 0.5 | 18 % | 22 % | 34 % | 32 % | 46 % |
| moitié | 0.7 | 12 % | 14 % | 18 % | 20 % | 25 % |
| quart | 0.3 | 14 % | 15 % | 22 % | 21 % | 35 % |
| quart | 0.5 | 6 % | 8 % | 12 % | 11 % | 15 % |
| quart | 0.7 | 7 % | 6 % | 6 % | 9 % | 9 % |
| nul | 0.3 | 4 % | 5 % | 4 % | 3 % | 5 % |
| nul | 0.5 | 5 % | 6 % | 5 % | 4 % | 4 % |
| nul | 0.7 | 3 % | 5 % | 4 % | 4 % | 5 % |
| calcaires seuls | 0.3 | 88 % | 99 % | 100 % | 100 % | 100 % |
| calcaires seuls | 0.5 | 65 % | 71 % | 92 % | 85 % | 95 % |
| calcaires seuls | 0.7 | 39 % | 42 % | 69 % | 63 % | 75 % |

Scénario « nul » = taux de faux positifs (aucune différence entre classes).

## 3. Critère de R-47 (Wilcoxon et réduction de 30 %), mêmes cas, pour comparaison

| Scénario | σ | k = 3 | k = 4 | k = 5 | k = 6 | k = 8 |
|---|---|---|---|---|---|---|
| vu | 0.3 | 44 % | 58 % | 73 % | 80 % | 88 % |
| vu | 0.5 | 22 % | 40 % | 43 % | 51 % | 57 % |
| vu | 0.7 | 13 % | 21 % | 23 % | 28 % | 34 % |
| moitié | 0.3 | 18 % | 26 % | 31 % | 35 % | 44 % |
| moitié | 0.5 | 7 % | 12 % | 9 % | 14 % | 16 % |
| moitié | 0.7 | 3 % | 7 % | 5 % | 10 % | 9 % |
| quart | 0.3 | 6 % | 8 % | 7 % | 8 % | 12 % |
| quart | 0.5 | 1 % | 6 % | 3 % | 6 % | 4 % |
| quart | 0.7 | 2 % | 3 % | 1 % | 4 % | 2 % |
| nul | 0.3 | 2 % | 5 % | 1 % | 2 % | 2 % |
| nul | 0.5 | 1 % | 3 % | 1 % | 3 % | 2 % |
| nul | 0.7 | 1 % | 2 % | 2 % | 2 % | 2 % |
| calcaires seuls | 0.3 | 39 % | 55 % | 75 % | 81 % | 86 % |
| calcaires seuls | 0.5 | 24 % | 36 % | 46 % | 50 % | 69 % |
| calcaires seuls | 0.7 | 14 % | 22 % | 22 % | 29 % | 35 % |

## 4. Plans inégaux (socle mieux couvert)

| Plan | Scénario | σ | H-A1 | critère R-47 |
|---|---|---|---|---|
| socle 6, sables 4, calcaires 4 | vu | 0.3 | 99 % | 42 % |
| socle 6, sables 5, calcaires 3 | vu | 0.3 | 98 % | 25 % |
| socle 6, sables 4, calcaires 4 | vu | 0.5 | 73 % | 29 % |
| socle 6, sables 5, calcaires 3 | vu | 0.5 | 69 % | 16 % |
| socle 6, sables 4, calcaires 4 | vu | 0.7 | 43 % | 17 % |
| socle 6, sables 5, calcaires 3 | vu | 0.7 | 43 % | 13 % |
| socle 6, sables 4, calcaires 4 | moitié | 0.3 | 63 % | 26 % |
| socle 6, sables 5, calcaires 3 | moitié | 0.3 | 51 % | 13 % |
| socle 6, sables 4, calcaires 4 | moitié | 0.5 | 27 % | 11 % |
| socle 6, sables 5, calcaires 3 | moitié | 0.5 | 25 % | 6 % |
| socle 6, sables 4, calcaires 4 | moitié | 0.7 | 16 % | 7 % |
| socle 6, sables 5, calcaires 3 | moitié | 0.7 | 15 % | 6 % |
| socle 6, sables 4, calcaires 4 | quart | 0.3 | 18 % | 10 % |
| socle 6, sables 5, calcaires 3 | quart | 0.3 | 15 % | 5 % |
| socle 6, sables 4, calcaires 4 | quart | 0.5 | 9 % | 3 % |
| socle 6, sables 5, calcaires 3 | quart | 0.5 | 9 % | 4 % |
| socle 6, sables 4, calcaires 4 | quart | 0.7 | 4 % | 2 % |
| socle 6, sables 5, calcaires 3 | quart | 0.7 | 5 % | 2 % |
| socle 6, sables 4, calcaires 4 | nul | 0.3 | 5 % | 3 % |
| socle 6, sables 5, calcaires 3 | nul | 0.3 | 6 % | 2 % |
| socle 6, sables 4, calcaires 4 | nul | 0.5 | 6 % | 3 % |
| socle 6, sables 5, calcaires 3 | nul | 0.5 | 4 % | 4 % |
| socle 6, sables 4, calcaires 4 | nul | 0.7 | 5 % | 4 % |
| socle 6, sables 5, calcaires 3 | nul | 0.7 | 4 % | 2 % |
| socle 6, sables 4, calcaires 4 | calcaires seuls | 0.3 | 99 % | 38 % |
| socle 6, sables 5, calcaires 3 | calcaires seuls | 0.3 | 99 % | 16 % |
| socle 6, sables 4, calcaires 4 | calcaires seuls | 0.5 | 78 % | 27 % |
| socle 6, sables 5, calcaires 3 | calcaires seuls | 0.5 | 72 % | 15 % |
| socle 6, sables 4, calcaires 4 | calcaires seuls | 0.7 | 48 % | 19 % |
| socle 6, sables 5, calcaires 3 | calcaires seuls | 0.7 | 48 % | 12 % |

## 5. H-A1, 2 classes seulement (socle, sables), si les calcaires ne sont pas couverts

| Scénario | σ | k = 3 | k = 4 | k = 5 | k = 6 | k = 8 |
|---|---|---|---|---|---|---|
| vu | 0.3 | 0 % | 7 % | 11 % | 10 % | 12 % |
| vu | 0.5 | 0 % | 3 % | 6 % | 6 % | 8 % |
| vu | 0.7 | 0 % | 4 % | 3 % | 6 % | 5 % |
| moitié | 0.3 | 0 % | 3 % | 4 % | 5 % | 6 % |
| moitié | 0.5 | 0 % | 3 % | 4 % | 5 % | 5 % |
| moitié | 0.7 | 0 % | 2 % | 3 % | 5 % | 5 % |
| nul | 0.3 | 0 % | 4 % | 3 % | 4 % | 4 % |
| nul | 0.5 | 0 % | 2 % | 3 % | 3 % | 3 % |
| nul | 0.7 | 0 % | 2 % | 5 % | 4 % | 5 % |

## 6. Comparaison à T2 (règle de R-47, abandonnée), 3 classes

| Scénario | σ | k = 3 | k = 4 | k = 5 | k = 6 | k = 8 |
|---|---|---|---|---|---|---|
| vu | 0.3 | 64 % | 73 % | 82 % | 83 % | 88 % |
| vu | 0.5 | 20 % | 28 % | 27 % | 32 % | 30 % |
| vu | 0.7 | 8 % | 13 % | 6 % | 9 % | 7 % |
| moitié | 0.3 | 39 % | 38 % | 47 % | 51 % | 55 % |
| moitié | 0.5 | 14 % | 15 % | 12 % | 14 % | 12 % |
| moitié | 0.7 | 6 % | 6 % | 3 % | 6 % | 2 % |
| quart | 0.3 | 39 % | 41 % | 49 % | 46 % | 57 % |
| quart | 0.5 | 11 % | 16 % | 13 % | 13 % | 12 % |
| quart | 0.7 | 5 % | 7 % | 3 % | 6 % | 3 % |
| nul | 0.3 | 52 % | 58 % | 62 % | 66 % | 73 % |
| nul | 0.5 | 18 % | 22 % | 16 % | 20 % | 19 % |
| nul | 0.7 | 7 % | 10 % | 4 % | 6 % | 3 % |
| calcaires seuls | 0.3 | 70 % | 81 % | 83 % | 89 % | 92 % |
| calcaires seuls | 0.5 | 25 % | 32 % | 28 % | 33 % | 41 % |
| calcaires seuls | 0.7 | 9 % | 14 % | 6 % | 11 % | 9 % |

Cette comparaison « passe » aussi dans le scénario nul quand σ est faible : il récompense le changement de niveau commun à
toutes les classes, pas la classe. Il reste descriptif.

## 7. Contrôle de la référence : classes tirées au hasard (scénario « vu », 3 classes)

H-A1 retenu :

| Scénario | σ | k = 3 | k = 4 | k = 5 | k = 6 | k = 8 |
|---|---|---|---|---|---|---|
| vu | 0.3 | 4 % | 4 % | 6 % | 6 % | 4 % |
| vu | 0.5 | 4 % | 5 % | 5 % | 4 % | 5 % |
| vu | 0.7 | 5 % | 5 % | 4 % | 6 % | 5 % |

Critère de R-47 :

| Scénario | σ | k = 3 | k = 4 | k = 5 | k = 6 | k = 8 |
|---|---|---|---|---|---|---|
| vu | 0.3 | 1 % | 2 % | 0 % | 3 % | 2 % |
| vu | 0.5 | 1 % | 2 % | 1 % | 2 % | 3 % |
| vu | 0.7 | 1 % | 5 % | 1 % | 4 % | 2 % |

Des classes sans rapport avec la roche (mêmes effectifs) doivent échouer : ce taux mesure ce que chaque critère
accorderait à un simple ajout de paramètres.
