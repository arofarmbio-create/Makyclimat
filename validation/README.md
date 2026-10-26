# Validation : événements réels 2016-2026

`evenements.csv` ne contient que des chiffres lus dans un document cité (colonne `source_url`). Une cellule vide signifie « non indiqué dans la source ».

À documenter (non encore sourcés, donc absents) : Ava (2018), Gombe (2022), Freddy (2023), Alvaro (2024), Honde (2025), Dikeledi, Grant et Gezani (2025-2026), sécheresse 2016-2017, crues non cycloniques, glissements de terrain.

Les dates de début et de fin des cyclones viennent des trajectoires IBTrACS déjà dans le site.
Exposé ≠ sinistré : la comparaison avec le modèle se fera sur le classement des zones et sur l'ordre de grandeur, pas sur l'égalité des chiffres.

## Résultats (octobre 2026)

**Niveau région, 9 cyclones (rapports OCHA/IFRC/presse)** : `cyclones_*.csv`, `modele_cyclone.json`. Classement vent + pluie : AUC 0,81 ; 92 % des régions citées sont dans les 8 premières sur 24. Probabilités non calibrées.

**Niveau fokontany et commune, 6 activations Copernicus EMS (satellite)** : `ems_*.csv`, `ems_resultats.json`, journal `_journal_ems.txt`.
- Vérité : zones inondées et bâtiments classés par satellite, uniquement dans les zones cartographiées (AOI). Touché = bâtiment détruit ou endommagé, ou au moins 5 % de la surface inondée.
- Parmi les fokontany cartographiés, le vent et la pluie seuls ne discriminent pas (AUC ≈ 0,5) : la zone entière est déjà touchée. Le terrain (HAND, altitude, pente, rivière, densité de population) discrimine : AUC 0,79 au fokontany et 0,81 à la commune, probabilités bien calibrées (Brier 0,176 contre 0,226 pour la fréquence moyenne).
- Les dégâts sur bâtiments seuls restent mal prédits (AUC 0,42-0,59) : il manque le type de construction.
- Enawo (EMSR197) : format ancien sans polygones d'inondation exploitables. Ava et Eliakim : zones inondées seulement, pas de bâtiments classés.
- Limites : les cartes EMS couvrent surtout des villes et des zones accessibles ; imagerie prise quelques jours après ; résultat conditionnel à « zone déjà touchée ».
