# Extension de la base d'événements (1994-2013) — note de prudence

8 cyclones antérieurs à 2017 ont été ajoutés à `evenements.csv` (Geralda 1994, Eline 2000, Hudah 2000,
Gafilo 2004, Elita 2004, Hubert 2010, Giovanna 2012, Haruna 2013), portant la base de 10 à 18 cyclones.
Chaque ligne cite sa source et, quand les chiffres divergent d'une source à l'autre (c'est le cas de
Gafilo : 172 à 363 morts selon la source), l'écart est écrit dans la colonne `remarque` plutôt que
masqué derrière un seul chiffre.

**Avant d'utiliser ces événements dans le calcul de fiabilité (AUC, leave-one-out) :**

1. **La plupart n'ont pas de liste de régions complète**, contrairement aux événements récents (Enawo,
   Batsirai...) qui citent toutes les régions touchées. Seuls Hudah, Gafilo et Geralda ont une ou deux
   régions identifiées avec confiance (voir `zones_touchees.csv`), via des noms de ville (Antalaha,
   Mahajanga, Toamasina) traduits en région actuelle. Les autres (Eline, Elita, Hubert, Giovanna, Haruna)
   n'ont que des chiffres nationaux : utilisables pour une analyse nationale (fréquence, ampleur), pas
   pour tester le classement région par région.
2. **Deux sources (Geralda, Gafilo pour la partie région) sont secondaires** (encyclopédie, blog
   scientifique), pas des rapports humanitaires d'époque. Une recherche plus poussée dans les archives
   OCHA/ReliefWeb ou IFRC pourrait trouver des rapports primaires pour ces événements et resterait utile.
3. **Le désaccord Gafilo (172 à 363 morts)** doit être signalé s'il est cité, pas arrondi à un seul chiffre.

**Ce que ça change concrètement :** la base passe de 10 à 18 cyclones avec au moins un chiffre d'impact
réel, ce qui resserre l'incertitude statistique de toute validation nationale (fréquence, ampleur
moyenne). Le test de classement par région (AUC) reste basé sur les événements qui ont une liste de
régions utilisable — à recalculer en incluant Hudah, Gafilo et Geralda une fois leurs listes vérifiées.
