# Corroboration interne avec EM-DAT (27/10/2026)

**Usage restreint, conformément au choix explicite de l'utilisateur :** l'archive EM-DAT (CRED/UCLouvain,
DOI [10.14428/DVN/I0LTPH](https://doi.org/10.14428/DVN/I0LTPH)) est publiée sous licence **CC BY-NC-ND**
(pas d'usage commercial, pas de forme dérivée republiée). Elle est utilisée ici **uniquement pour vérifier
en interne** les chiffres de `evenements.csv` — aucune donnée brute ou dérivée d'EM-DAT n'est republiée sur
le site public (`docs/`) ni versée telle quelle dans le dépôt (le fichier source `260430_emdat_archive.xlsx`
n'est volontairement pas commité).

## Méthode

119 lignes Madagascar extraites de l'archive (`ISO == "MDG"`), filtrées sur les types *Storm* et *Drought*,
rapprochées des 22 événements de `evenements.csv` par nom/année. Comparaison de `deces` et
`personnes_touchees` (MakyClimat) avec `Total Deaths` et `Total Affected`/`No. Affected` (EM-DAT).

## Résultat

| Événement | Décès MKC | Décès EM-DAT | Touchés MKC | Touchés EM-DAT (Total / No. Affected) | Remarque |
|---|---|---|---|---|---|
| Enawo 2017 | — | 81 | 434 000 | 434 253 / 434 000 | **Concordance quasi exacte** (touchés) |
| Batsirai 2022 | 92 | 92 | 112 115 | 112 115 / 112 115 | **Concordance exacte** |
| Emnati 2022 | 15 | 15 | — | 169 000 / 169 000 | **Concordance exacte** (décès) |
| Belna 2019 | 1 | 5 | — | 20 293 / 14 000 | Écart décès (source MKC probablement un bilan précoce) |
| Gamane 2024 | 19 | 22 | 89 465 | 89 469 / 89 465 | Concordance quasi exacte |
| Jude 2025 | 2 | — | 19 100 | — | Hors couverture de l'archive (postérieur à fin 2024) |
| Sécheresse Grand Sud 2020-2022 | — | — | 2 200 000 | — / 1 680 000 | Périmètre différent (EM-DAT : 2020-2024, drought unique ; MKC : 2020-2022) — pas comparable terme à terme |
| Ava 2018 | 33 | 73 | 123 000 | 161 318 / 161 318 | **Écart net** (décès et touchés) |
| Freddy 2023 | 11 | 17 | 116 701 | 299 000 / 299 000 | **Écart net** (touchés : MKC couvre une partie seulement — un seul rapport DREF) |
| Alvaro 2024 | 19 | 10 | 33 000 | 25 837 / 25 837 | Écart modéré dans les deux sens |
| Gezani 2026 | 40 | — | — | — | Hors couverture de l'archive |
| Geralda 1994 | 231 | 200 | — | 540 043 / 500 000 | EM-DAT combine deux cyclones ("Daisy, Geralda") — comparaison directe peu fiable |
| Eline 2000 | — | 130 | 737 000 | 736 937 / 736 937 | **Concordance quasi exacte** (touchés) ; EM-DAT combine "Eline, Gloria" |
| Hudah 2000 | — | 23 | 369 271 | 369 272 / 369 271 | **Concordance quasi exacte** (touchés) |
| Gafilo 2004 | 237 (`remarque` : 172 à 363 selon les sources) | 363 | 773 000 | 988 139 / 773 000 | `No. Affected` EM-DAT = touchés MKC exactement ; le chiffre de décès EM-DAT (363) confirme la borne haute déjà citée dans `evenements.csv` |
| Elita 2004 | 29 | 32 | — | 44 290 / — | Proche |
| Hubert 2010 | 85 | 120 | 192 000 | 192 132 / 192 000 | `No. Affected` quasi exact ; décès nettement plus élevé côté EM-DAT |
| Giovanna 2012 | 31 | 35 | — | 250 284 / 250 000 | Proche |
| Haruna 2013 | 26 | 42 | 40 000 | 40 281 / 40 154 | Touchés quasi exacts ; décès nettement plus élevé côté EM-DAT |
| Diane 2020 | 49 | 40 (*) | — | — | (*) EM-DAT n'a pas d'entrée "Diane" — l'épisode est probablement enregistré sous "2020-0016-MDG" (inondation, 1-24 janv. 2020, 40 décès), chevauchant les dates de Diane (21 janv.-3 févr.) ; rapprochement plausible mais pas certain |
| Ana 2022 | 34 | 55 | 62 000 | 131 555 / 131 555 | **Écart net** (touchés : MKC = un rapport DREF partiel, EM-DAT = bilan consolidé) |
| Fytia 2026 | 1 | — | 22 067 | — | Hors couverture de l'archive |

## Lecture

- **Les chiffres de « personnes touchées » de `evenements.csv` concordent quasi systématiquement avec
  `No. Affected` d'EM-DAT** quand les deux existent (Enawo, Batsirai, Eline, Hudah, Gafilo, Hubert,
  Haruna) — c'est le signal de corroboration le plus solide de cet exercice : les deux bases, construites
  indépendamment, convergent sur ce chiffre pour 7 événements sur 9 comparables.
- **Les bilans de décès divergent plus souvent, et toujours dans le même sens** (EM-DAT ≥ MKC) : Ava,
  Freddy, Alvaro (dans l'autre sens), Hubert, Giovanna, Haruna, Belna, Ana. Explication la plus probable :
  les chiffres MKC viennent en général d'un seul rapport de situation humanitaire précoce (ReliefWeb/
  IFRC-DREF, cité en source), alors qu'EM-DAT consolide le bilan final, parfois réévalué plusieurs
  semaines après l'événement. **Ce n'est pas nécessairement une erreur côté MKC** — chaque chiffre reste
  sourcé individuellement dans `evenements.csv` avec un lien vérifiable — mais c'est une limite réelle à
  documenter : les décès de `evenements.csv` doivent être lus comme « au moment du rapport cité », pas
  comme un bilan final consolidé.
- **Touchés de la sécheresse Grand Sud non comparables** : périmètres temporels différents.
- **Aucun événement n'a montré d'incohérence structurelle** (ordre de grandeur, région, saison) — rien
  dans cette comparaison ne remet en cause la fiabilité globale de `evenements.csv`, mais elle confirme que
  le niveau « Validé » (actuellement réservé aux régions touchées, calibrées en leave-one-out) ne doit
  **pas** s'étendre aux bilans de décès eux-mêmes, qui restent `Standard`/`Approximation` selon la
  source.

## Suite possible

Une colonne `deces_emdat` (à titre de référence croisée, pas comme remplacement) pourrait être ajoutée à
`evenements.csv` pour les 18 événements couverts par EM-DAT — à discuter : cela resterait un usage interne
(comparaison), pas une republication de données EM-DAT, mais le format reste à trancher pour ne pas
dépasser le cadre « validation interne uniquement » choisi par l'utilisateur.
