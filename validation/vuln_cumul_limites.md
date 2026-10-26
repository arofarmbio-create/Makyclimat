# Indice de vulnérabilité cumulative — ce qu'il montre et ce qu'il ne montre pas

**Niveau de preuve : approximation (non validé).** Construction raisonnée, jamais comparée à une
enquête de vulnérabilité ou de résilience réelle.

## Ce qu'il calcule

Pour chaque fokontany, un score de 0 à 100 qui résume les chocs climatiques (vent de cyclone,
sécheresse mesurée par le SPI-3) survenus sur les ~3,5 dernières années, le choc le plus récent
pesant le plus (sa valeur est réduite de moitié tous les 18 mois). L'idée : une zone déjà frappée
récemment a moins de marge pour encaisser un nouveau choc, même si la saison en cours, prise seule,
est normale.

Les sécheresses de plusieurs mois consécutifs comptent comme un seul épisode (la sévérité de son pic),
pour ne pas gonfler artificiellement le score d'une région simplement parce que sa sécheresse a duré
longtemps.

## Ce qu'il NE calcule PAS

- **Aucune donnée de prix, d'inflation locale ou de pouvoir d'achat.** Nous n'avons identifié aucune
  source fiable de prix ou d'inflation au niveau du fokontany à Madagascar (le PAM/VAM et l'INSTAT
  publient au mieux au niveau district ou région, par marché). Tant qu'une telle source n'est pas
  disponible et citée, l'indice reste un indice d'aléas physiques, pas un indice économique.
- **Aucune mesure de la résilience réelle des ménages** (épargne, diversification des revenus, accès
  au crédit, soutien communautaire). Ces informations relèvent d'enquêtes de terrain (EFSA, enquêtes
  IPC, études socio-économiques), pas d'un calcul satellite.
- **Pas une estimation de dégâts ni de besoins.** Comme les autres modules de MakyClimat, l'indice
  mesure une exposition cumulée aux aléas, pas un impact constaté ni un besoin humanitaire.

## Comment l'interpréter

Un score élevé signifie : « cette zone a subi plusieurs chocs physiques rapprochés ces dernières
années ». Cela justifie d'y regarder de plus près, pas de conclure automatiquement à une vulnérabilité
plus grande : une zone peut avoir subi plusieurs chocs et rester bien dotée (routes, marchés,
diversité agricole), une autre subir un seul choc sur un terrain déjà fragile.

## Pour l'améliorer

1. Une source de prix ou d'inflation par district, même trimestrielle (PAM/VAM, INSTAT, FEWS NET).
   **Une première source a été trouvée et branchée en collecte silencieuse** : le jeu de données ouvert
   « WFP Food Prices for Madagascar » (HDX), prix du riz par marché, mensuel, depuis 2004. Le script
   `scripts/connector_wfp_prices.py` le télécharge à chaque mise à jour et écrit
   `validation/wfp_prix_riz_candidat.csv` (écart du prix du riz au prix médian des 3 années précédentes,
   par région). **Ce fichier n'est pas encore affiché sur le site** : il faut d'abord vérifier, une fois
   collecté, la couverture réelle (quelles régions, quelle continuité des mois) et relier les noms de
   région WFP aux codes pcode de MakyClimat avant toute intégration à l'indice.
2. Des données de dégâts réels (voir la demande adressée au BNGRC) pour calibrer la sévérité attribuée
   à chaque classe de vent et à chaque seuil de SPI, au lieu des poids actuels choisis de façon
   raisonnée.
3. Un indicateur de diversité des moyens de subsistance, si une source existe au niveau local.

Tant que ces données manquent, l'indice reste affiché avec l'étiquette « approximation » et jamais
utilisé seul pour classer des priorités de réponse.
