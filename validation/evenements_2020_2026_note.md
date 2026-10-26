# Extension 2020-2026 : Diane, Ana, Fytia — note de prudence

3 événements récents ajoutés à `evenements.csv` (Diane 2020, Ana 2022, Fytia 2026), trouvés en
filtrant les activations Copernicus EMS sur Madagascar (`mapping.emergency.copernicus.eu/activations`,
filtre pays) : 4 activations liées à des tempêtes n'étaient pas encore dans le pipeline de validation
fokontany (`validate_fokontany.py`) — EMSR424 (Diane), EMSR559 (Ana), EMSR863 (Fytia), EMSR867 (Gezani,
déjà dans `evenements.csv` mais pas encore relié à son activation EMS). Les 4 codes sont désormais dans
`EVENTS` de `validate_fokontany.py` : la prochaine exécution du workflow 10 (validation fokontany) les
utilisera automatiquement comme vérité de terrain satellite (bâtiments gradés, zones inondées).

**Limites à garder en tête :**

1. **Ana 2022** : le bilan OCHA (34 morts, 62 000 touchés) couvre tout l'épisode pluvieux (zone de
   convergence intertropicale puis dépression tropicale Ana), pas la tempête seule — chiffre
   probablement un majorant de l'impact imputable à Ana elle-même.
2. **Diane 2020** : région (Boeny) déduite des zones cartographiées par l'activation EMS, pas d'un
   rapport d'impact par région ; bilan nombre de morts variable selon la source (30 à 49).
3. **Fytia 2026** : bilan très provisoire et évolutif au moment de la collecte (2 févr. 2026, quelques
   jours après l'atterrissage) ; écart entre le titre d'un article (3 morts) et son corps de texte
   (1 mort + 1 disparu) — signalé dans la colonne `remarque`, pas masqué.
4. **Gezani 2026** était déjà dans `evenements.csv` (40 morts, source Al Jazeera citant le BNGRC) ; un
   bilan UNICEF plus récent (flash update #2, 14 févr. 2026) cite 41 morts — chiffres cohérents entre
   eux, pas de correction nécessaire.

**Ce que ça change concrètement :** la base passe de 18 à 21 cyclones recensés dans `evenements.csv`,
et le pipeline de validation fokontany (satellite, le test le plus rigoureux car basé sur des dégâts
réellement observés et pas seulement une région citée dans un rapport) passe de 7 à 11 activations EMS
utilisables. À recalculer via le workflow « 10 - Validation au niveau fokontany (Copernicus EMS) ».
