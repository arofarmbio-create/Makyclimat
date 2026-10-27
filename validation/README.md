# Validation : événements réels 2016-2026

`evenements.csv` ne contient que des chiffres lus dans un document cité (colonne `source_url`). Une cellule vide signifie « non indiqué dans la source ».

À documenter (non encore sourcés, donc absents) : Ava (2018), Gombe (2022), Freddy (2023), Alvaro (2024), Honde (2025), Dikeledi, Grant et Gezani (2025-2026), sécheresse 2016-2017, crues non cycloniques, glissements de terrain.

Les dates de début et de fin des cyclones viennent des trajectoires IBTrACS déjà dans le site.
Exposé ≠ sinistré : la comparaison avec le modèle se fera sur le classement des zones et sur l'ordre de grandeur, pas sur l'égalité des chiffres.

## Résultats (octobre 2026)

**Niveau région, 16 cyclones avec liste de régions utilisable sur 21 documentés 1994-2026 (rapports OCHA/IFRC/presse, dont 7 cyclones historiques 1994-2013 ajoutés en octobre 2026 — voir `evenements_historiques_note.md` et `evenements_2020_2026_note.md`)** : `cyclones_*.csv`, `modele_cyclone.json`. Classement vent + pluie : AUC 0,84 ; 87 % des régions citées sont dans les 8 premières sur 24. Probabilités non calibrées. (5 cyclones comptent dans la base nationale mais sont exclus de ce test région par région faute de liste de régions touchées utilisable : Emnati 2022, Geralda 1994 — trajectoire IBTrACS introuvable —, Eline 2000, Elita 2004, Giovanna 2012.)

**Niveau fokontany et commune, 8 activations Copernicus EMS (satellite)** : `ems_*.csv`, `ems_resultats.json`, journal `_journal_ems.txt`. (Étendu d'octobre 2026 : Diane 2020/EMSR424 ajouté avec succès ; Ana/EMSR559, Fytia/EMSR863 et Gezani/EMSR867 ciblés mais non exploitables en pratique — voir `evenements_2020_2026_note.md` pour le détail des échecs.)
- Vérité : zones inondées et bâtiments classés par satellite, uniquement dans les zones cartographiées (AOI). Touché = bâtiment détruit ou endommagé, ou au moins 5 % de la surface inondée.
- Parmi les fokontany cartographiés, le vent et la pluie seuls ne discriminent presque pas (AUC 0,51-0,52) : la zone entière est déjà touchée. Le terrain (HAND, altitude, pente, rivière, densité de population) discrimine nettement mieux : AUC 0,79 au fokontany (inondation 0,80) et 0,82 à la commune, probabilités bien calibrées (Brier 0,176-0,180 contre 0,234-0,236 pour la fréquence moyenne).
- Les dégâts sur bâtiments seuls restent mal prédits et instables (AUC 0,16-0,62 selon la variante) : trop peu de cas positifs (159 sur 5 880 fokontany évalués) pour un signal fiable ; il manque aussi le type de construction.
- Enawo (EMSR197) : format ancien sans polygones d'inondation exploitables. Ava et Eliakim : zones inondées seulement, pas de bâtiments classés.
- Limites : les cartes EMS couvrent surtout des villes et des zones accessibles ; imagerie prise quelques jours après ; résultat conditionnel à « zone déjà touchée ».
