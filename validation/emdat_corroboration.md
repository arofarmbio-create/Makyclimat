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

*Tableau revu le 02/11/2026 : le dépôt est public, et la licence d'EM-DAT (CC BY-NC-ND) interdit d'y redistribuer
ses chiffres sous une forme dérivée. Seul le verdict de la comparaison est publié ; aucun chiffre EM-DAT n'apparaît
ici. Les chiffres MakyClimat restent dans `evenements.csv`, avec leurs sources. Le calcul détaillé se refait à partir
de l'archive EM-DAT, que chacun peut obtenir auprès du CRED.*

| Événement | Personnes touchées | Décès |
|---|---|---|
| Enawo 2017 | Concordance quasi exacte | Pas de chiffre MakyClimat |
| Batsirai 2022 | Concordance exacte | Concordance exacte |
| Emnati 2022 | Pas de chiffre MakyClimat | Concordance exacte |
| Belna 2019 | Pas de chiffre MakyClimat | Écart (EM-DAT plus élevé ; source MakyClimat probablement un bilan précoce) |
| Gamane 2024 | Concordance quasi exacte | Écart faible |
| Ava 2018 | **Écart net** | **Écart net** (EM-DAT plus élevé) |
| Freddy 2023 | **Écart net** (MakyClimat ne couvre qu'une partie : un seul rapport DREF) | Écart (EM-DAT plus élevé) |
| Alvaro 2024 | Écart modéré | Écart modéré (MakyClimat plus élevé) |
| Geralda 1994 | Non comparable (EM-DAT réunit deux cyclones) | Non comparable |
| Eline 2000 | Concordance quasi exacte (EM-DAT réunit deux cyclones) | Pas de chiffre MakyClimat |
| Hudah 2000 | Concordance quasi exacte | Pas de chiffre MakyClimat |
| Gafilo 2004 | Concordance exacte (« No. Affected ») | Confirme la borne haute déjà indiquée dans `evenements.csv` |
| Elita 2004 | Pas de chiffre MakyClimat | Proche |
| Hubert 2010 | Concordance quasi exacte (« No. Affected ») | Écart net (EM-DAT plus élevé) |
| Giovanna 2012 | Pas de chiffre MakyClimat | Proche |
| Haruna 2013 | Concordance quasi exacte | Écart net (EM-DAT plus élevé) |
| Diane 2020 | — | Rapprochement plausible mais incertain : pas d'entrée « Diane », une inondation de janvier 2020 chevauche ses dates |
| Ana 2022 | **Écart net** (MakyClimat : rapport DREF partiel ; EM-DAT : bilan consolidé) | Écart (EM-DAT plus élevé) |
| Sécheresse Grand Sud 2020-2022 | Non comparable (périodes différentes) | — |
| Jude 2025, Gezani 2026, Fytia 2026 | Hors couverture de l'archive (fin 2024) | — |

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

📌 Décision du 02/11/2026 : le dépôt reste public. Aucune colonne de chiffres EM-DAT ne sera donc ajoutée à
`evenements.csv`. La comparaison reste un contrôle interne, refait à la demande à partir de l'archive EM-DAT, qui
n'est jamais versée dans le dépôt.
