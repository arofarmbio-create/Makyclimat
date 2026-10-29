# Scénarios de planification à 12 mois : saison 2027-2028

Généré le 2026-10-29 par `scripts/build_planning.py`, selon `validation/protocole_planification_12mois.md` (fixé avant les calculs).

- 45 saisons de pluie CHIRPS par région. Prédicteurs connus un an avant : ONI et DMI de juillet-septembre 2026 (ONI 2,16, DMI 0,23).
- Un signal n'est utilisé que s'il passe les quatre épreuves (MSSS croisé > 0, MSSS chronologique > 0, corrélation significative après contrôle des tests multiples, RPSS croisé > 0). Sinon : scénarios climatologiques.

## 1. Résultat

| Période | Modèle | Régions validées | MSSS médian | RPSS médian |
|---|---|---|---|---|
| novembre-janvier | ONI | 0 / 24 | -0,04 | -0,03 |
| novembre-janvier | ONI + DMI | 0 / 24 | -0,08 | -0,05 |
| janvier-mars | ONI | 0 / 24 | -0,04 | -0,02 |
| janvier-mars | ONI + DMI | 0 / 24 | -0,03 | -0,01 |
| novembre-avril | ONI | 0 / 24 | -0,04 | -0,02 |
| novembre-avril | ONI + DMI | 0 / 24 | -0,06 | -0,03 |

**H1** (au moins un signal validé à 12 mois) : **non soutenue**.

À 12 mois, aucune région ne passe les épreuves : seule une planification climatologique (toutes les saisons passées à poids égal) est défendable.

## 2. Contexte : phase El Niño / La Niña de l'année suivante

Après les 8 années de même type que 2026 (ONI de juillet-septembre 2,16) : 4 fois La Niña, 4 fois neutre, 0 fois El Niño (1957, 1963, 1965, 1972, 1987, 1997, 2015, 2023).
C'est un contexte physique, pas une prévision régionale : son effet sur la pluie de chaque région n'est retenu que s'il passe les épreuves ci-dessus.

## Limites

- Population actuelle, non projetée.
- Exposition déduite de la pluie seule : les cyclones ne sont pas prévisibles à 12 mois.
- Remplacé automatiquement par la prévision hybride C3S le 16 octobre de l'année de la saison.
