# Audit de notre organisation — 13 novembre 2026

Codex · À relire par Claude · Sources locales arrêtées au 13/11, vers 08:15 Nairobi, avant cet audit.

## Synthèse — une page

**Nous avançons, mais le suivi prend trop de place et ne permet pas de voir simplement ce qui rapproche la thèse de son objectif.** Les relectures ont corrigé de vraies erreurs ; leur multiplication, les alertes périmées et les décisions tardives ont aussi consommé du travail sans livrable nouveau.

- **Coût observé :** 164 lancements terminés du 10 au 13/11, dont 154 avec consommation connue : **43,00 millions de jetons d’entrée**, dont 37,70 millions en cache, et 0,306 million en sortie. Ce ne sont ni des jetons uniques ni une facture ; les sessions mères ne sont pas mesurées séparément par cette base.
- **Répartition récente :** sur les 58 lancements dont le sujet est renseigné (11/11 à 18:43–13/11 à 08:13), **56,7 % des entrées vont à la thèse**, 27,5 % au pilotage, 6,3 % à la sûreté commune de MakyClimat et 9,5 % à des consignes mixtes. Les relectures représentent 24,3 % de ces entrées, déjà incluses dans ces domaines.
- **Temps :** sur cette même fenêtre, 158 minutes cumulées entre début et fin : thèse 50,6 %, pilotage 33,5 %, sûreté 7,0 %, mixte 8,9 %. Il s’agit de durées des lancements, pas du temps humain, des calculs distants ou d’un temps de raisonnement mesuré.
- **Résultats :** R-21 a abouti à une conclusion négative exploratoire ; R-21 bis à un diagnostic utile et à une clôture justifiée. Le suivi « Situation » affiche **quatre correctifs techniques confirmés**, mais aucun élément de thèse ou du site au niveau « confirmé » ; cela n’annule pas les hypothèses ponctuelles soutenues dans les rapports.
- **Freins concrets :** six passes retrouvées pour le protocole R-21 bis ; deux départs d’exécution arrêtés pour décision ou donnée manquante ; un branchement repris trois fois, dont un échec de limite d’usage. Plusieurs informations restent contradictoires : H1 encore « verrouillée » en bandeau alors que les scores sont faits, message licence CMIP6 encore ouvert après correction.

**Priorité proposée : appliquer les règles existantes avant d’ajouter du pilotage.** Claude tient un état court et actuel ; Codex reçoit des lots prêts à exécuter et relit les changements ; le porteur choisit les résultats prioritaires et les données à obtenir. Les dix propositions ci-dessous sont des recommandations, aucune règle n’a été changée.

## 1. Ce que les chiffres permettent de dire

Lecture SQLite en mode lecture seule : `lancements`, `retentes`, `remises_plafond` ; instantané de 165 lignes, dont l’audit en cours exclu. Les champs `agent`, `genre`, `sujet`, `consigne` manquent sur les 106 premières lignes : agent et genre sont récupérés du préfixe de l’identifiant quand il est explicite, sinon laissés non attribués. Aucune absence de consommation n’est traitée comme un coût nul.

| Agent des lancements | Nombre | Avec jetons | Entrée (millions) | Sortie (milliers) |
|---|---:|---:|---:|---:|
| Codex | 140 | 133 | 30,775 | 201,5 |
| Claude | 15 | 15 | 11,201 | 93,4 |
| Non attribué | 9 | 6 | 1,022 | 11,3 |
| **Total** | **164** | **154** | **42,998** | **306,3** |

| Jour de lancement, Nairobi | Nombre | Entrée (millions) | Durée cumulée (min) |
|---|---:|---:|---:|
| 10/11 | 61 | 11,163 | 105 |
| 11/11 | 68 | 15,133 | 379 |
| 12/11 | 30 | 11,575 | 84 |
| 13/11, avant l’audit | 5 | 5,127 | 32 |

Les 600 minutes totales comprennent **203 minutes d’un réveil interrompu**, sans jetons renseignés : l’exclure ramène le cumul à 397 minutes, sans prouver que le reste est du travail actif. Horodatages à la minute, chevauchements possibles, heures déclarées parfois incohérentes avec les commits : ne pas en déduire une productivité horaire.

| Genre, toutes dates | Nombre | Entrée (millions) | Part des entrées connues |
|---|---:|---:|---:|
| Exécution | 32 | 24,194 | 56,3 % |
| Relecture | 105 | 15,703 | 36,5 % |
| Réveil | 22 | 2,935 | 6,8 % |
| Non attribué | 5 | 0,166 | 0,4 % |

**Domaines : fenêtre renseignée seulement**, 58 lancements, 56 consommations connues, 22 098 464 entrées. Classement manuel du sujet et de la consigne : recherche, collecte et licence CMIP6 dans « thèse » ; interface, suivi et diagnostics de CI annulée dans « pilotage » ; audit P1 transversal dans « MakyClimat/sûreté » ; trois consignes groupées de plusieurs domaines laissées mixtes.

| Domaine | Lancements | Entrée (millions) | Part | Minutes | Part du temps |
|---|---:|---:|---:|---:|---:|
| Thèse | 27 | 12,524 | 56,7 % | 80 | 50,6 % |
| Pilotage | 27 | 6,083 | 27,5 % | 53 | 33,5 % |
| MakyClimat/sûreté commune | 1 | 1,391 | 6,3 % | 11 | 7,0 % |
| Mixte | 3 | 2,101 | 9,5 % | 14 | 8,9 % |

Les **32 relectures** de cette fenêtre coûtent 5,366 millions d’entrées et 41 minutes (24,3 % et 25,9 %) : ce sont des parts transversales, à ne pas additionner aux domaines. Hors cache, les entrées sont respectivement 1 088 316, 765 659, 63 866 et 192 331 : la thèse représente alors **51,6 %**, le pilotage **36,3 %** ; le choix de mesure change donc le bilan. Le cache représente 87,7 % de toutes les entrées connues ; son coût monétaire n’est pas assimilable à celui d’une entrée non cachée.

Le constat du 12/11 (« environ 10 % thèse, 60 % coordination ») est conservé dans la [règle 12](regles.md), introduite par `0798753`, et complété par les incidents de la [fiche pilotage](chantiers/pilotage.md). Aucun rapport autonome donnant son échantillon et son calcul exact n’a été retrouvé dans les emplacements examinés, y compris la recherche ciblée dans l’archive : **ce chiffre historique n’est pas une mesure reproduite ici**. La fenêtre récente couvre notamment les grosses exécutions de recherche après cette décision ; elle ne mesure pas à elle seule l’effet causal du gel.

## 2. Pourquoi du travail se perd

**Les sessions mères doivent décider et transmettre ; elles entretiennent aussi l’outil qui les coordonne.** Les 353 commits sur dix jours incluent 120 commits touchant COORDINATION.md (34 %, chevauchement possible avec du code) : c’est un indice d’entretien, pas une part du temps. À l’instantané `a167895`, cet index fait 33 644 octets, plus de deux fois l’objectif de 15 Ko ; les longues consignes cochées restent relues à chaque démarrage.

**Des enfants sont réveillés pour relire un état, sans décision nouvelle.** La fiche pilotage rapporte 14 lancements en 24 minutes le 11/11, environ 1,5 million d’entrées pour deux avis nouveaux ; les lignes actuellement conservées ne suffisent pas à reproduire exactement ce décompte historique. Elle documente aussi une revue groupée suivie de six relectures par ligne, dont le même commit deux fois ; deux diagnostics de CI annulée coûtent dans la base **829 037 entrées et cinq minutes** (`exec-20261111-203336-dd76`, `exec-20261111-204934-8e9e`). Les correctifs de dédoublonnage existent : ce gaspillage passé ne prouve pas qu’ils échouent aujourd’hui.

**Les arrêts utiles sont mélangés aux réussites et aux pannes.** La base porte 160 « Réponse reçue », deux « Échec », un « Interrompu », un « Arrêté par le porteur » ; quatre réponses du 10/11 annoncent pourtant l’impossibilité de lire les fichiers. La table `retentes` conserve cinq identifiants, pour six retentes comptées : ce n’est pas l’historique complet des tentatives, certaines lignes ayant été remplacées ; la dernière remise de plafond est au 12/11 à 18:11.

**Le gel du pilotage reçoit rapidement des exceptions.** Relecteur attitré (`78e79b9`), Situation (`ebe2ff3`), maçon (`566b166`) répondent à de vrais besoins, mais continuent d’absorber conception, tests et suivi ; leur rendement doit être observé avant extension. Le point de reprise de Claude mentionne aussi un gardien hors dépôt qui relance le surveillant et remet les plafonds à zéro : une autre voie d’action, à réconcilier avec la file, sans conclure ici à une violation d’autorisation.

**Les passations ne sont pas synchronisées.** La reprise Claude conserve des tâches déjà terminées sous « En cours » ; la reprise Codex décrit encore EMS à relire, alors que la coordination le dit relu. L’organigramme est annulé dans son autorisation et arrêté dans la base, mais encore « En cours » dans sa ligne, et « Échec » dans `macons.json` ; des paragraphes des fiches R-40/R-21 ont aussi des accents remplacés par « ? ».

## 3. Tours, blocages et résultats

| Livrable | Parcours observé | Enseignement |
|---|---|---|
| Méthode R-21 | Validation à la 4e version, fiche R-21 | Version ne signifie pas nombre exact de sessions ; population et portée ont changé pendant la revue. |
| Protocole R-21 bis | 6 relectures retrouvées, 1 074 824 entrées ; 7e version finale | Quatre sessions neuves (661 806 entrées), puis deux tours attitrés (413 018) ; le registre attitré seul masque le début du parcours. |
| Rapport R-21 bis | 2 tours attitrés, 557 455 entrées | Corrections puis avis sans blocage ; deux minutes de sessions, mais 4 h 37 entre les fins d’avis. |
| Code du diagnostic | 2 exécutions, 924 549 entrées, 12 min | Premier arrêt sur cinq groupes d’ambiguïtés ; livraison après décision. |
| Branchement du diagnostic | 3 exécutions, ≥ 1 793 005 entrées, 11 min | Horodatages IBTrACS manquants, puis limite d’usage à 18:22, puis livraison ; coût de l’échec inconnu. |

Le relecteur attitré converge sur **deux documents, deux tours chacun** : signe encourageant, échantillon insuffisant pour promettre une économie. Le maçon n’a qu’une tâche arrêtée et aucune reprise observée : son bénéfice reste non mesuré ; un contexte conservé peut aussi grossir. Les tours ci-dessus sont des lancements ou des versions, pas les appels internes du modèle, absents de la base.

**Blocages comptables, sans les additionner :** deux exécutions R-21 bis explicitement arrêtées pour une décision/donnée manquante (866 475 entrées, sept minutes), puis reprises ; trois éléments encore marqués bloqués dans Situation (R-22 fermé pour puissance insuffisante, E6 attendant R-40, analyses secondaires R-21 attendant décision). Deux branches sont explicitement closes faute de faisabilité : R-22 et le test EMS (indépendance non garantie, puissance insuffisante) ; l’organigramme est un arrêt de périmètre du porteur, pas une panne scientifique. R-40 attend des données fournisseur et les courriers externes restent au porteur ; ces dépendances ne se résolvent pas par davantage de sessions.

**Ce qui avance :** 59 fichiers mensuels de reprévision et 14 saisons de réanalyse sont consignés dans la coordination ; R-21 et R-21 bis ont une méthode, des tests, des rapports et une conclusion relue. Les contrôles ont évité de transformer un résultat négatif ou une référence peu détectante en conclusion excessive sur la compétence de GloFAS ; les correctifs P1 protègent licences, fichiers NPZ, dépendances et publication.

**L’atteinte des objectifs reste partielle.** Situation compte 93 éléments thèse (65 faits, 24 en cours, trois bloqués, un à faire), 129 MakyClimat (122 faits, un en cours, six à faire), 17 audit ; ces éléments mélangent modules, résultats et indicateurs, donc ne constituent pas 239 résultats indépendants. Les quatre passages à « confirmé » documentés le 13/11 sont techniques ; la thèse compte 85 provisoires, trois exploratoires et cinq sans fiabilité, MakyClimat 123 provisoires et six sans fiabilité.

Sur dix jours, les pièces attestent **au moins quatre hypothèses distinctes soutenues avec réserves** : H-T1 du transfert par analogues (04/11, `80e2422`, reprise `7332c50`) et H-D1/H-D2/H-D4 de la nappe régionale (09/11, `898df04`). Deux autres, H-K1/H-K2 de T2K (`24559d1`), sont formellement soutenues mais non discriminantes selon le propre rapport : ne pas les vendre comme progrès probant ; H1 SPEI–NDVI est aussi déclarée soutenue au 03/11 dans le registre, sans transition précisément isolée ici. **Ce n’est pas un décompte exhaustif des transitions**, et aucun de ces libellés ne suffit à certifier une validation indépendante, puissante et relue ; H-C5 confirmé le 02/11 est hors fenêtre.

## 4. Dix améliorations, par gain attendu sur effort

Classement qualitatif, sans économie promise ni mise en application dans cet audit.

1. **Claude — gain très fort, effort faible : fermer les états périmés à chaque remise.** Réconcilier la ligne, le message en attente et la reprise évite les réveils inutiles et rend la prochaine action visible.
2. **Claude — gain très fort, effort faible : appliquer l’archivage prévu et ramener l’index sous 15 Ko.** Les fiches gardent les preuves, tandis que chaque démarrage relit moins de texte ancien.
3. **Claude — gain fort, effort faible : vérifier les données et les décisions nécessaires avant de confier un lot à Codex.** Les deux arrêts R-21 bis montrent qu’une fiche prête aurait épargné au moins deux démarrages sans code livré.
4. **Porteur — gain fort, effort faible : choisir trois résultats prioritaires pour la reprise du 16/11, avec leur condition de fin.** Une liste courte limite les changements de direction et distingue résultat scientifique, donnée attendue et amélioration du site.
5. **Codex — gain fort, effort faible : relire une version groupée et rendre un avis limité aux blocages et aux changements.** Cela conserve la vérification indépendante tout en évitant de rouvrir les points déjà acceptés.
6. **Claude — gain fort, effort faible : traiter les décisions manquantes en un seul lot, puis relancer au premier pas utile.** Cela réduit les reprises partielles et distingue une correction technique déjà autorisée d’un arbitrage scientifique du porteur.
7. **Porteur — gain fort, effort moyen : prioriser les démarches de données externes avec une réponse attendue et une date.** La puissance et l’indépendance manquantes exigent des observations adaptées, pas une multiplication d’analyses exploratoires.
8. **Claude — gain moyen à fort, effort faible : observer les dispositifs attitrés et le maçon avant toute nouvelle fonction de pilotage.** Deux documents et une tâche interrompue ne suffisent pas encore à démontrer leur rendement.
9. **Codex — gain moyen, effort faible : remettre une passation courte avec livrable, vérifications, réserve restante et fichiers modifiés.** Claude peut alors décider et commiter sans reconstituer toute la conversation, en préservant l’UTF-8.
10. **Claude — gain moyen, effort moyen : établir avec les sources existantes un bilan hebdomadaire séparant résultats, relectures et incidents.** Montrer entrées avec et sans cache, consommations inconnues et temps d’attente évite de prendre l’activité affichée pour un progrès de la thèse.

## Sources et vérification

Sources publiques : [coordination](../COORDINATION.md), [règles](regles.md), fiches [pilotage](chantiers/pilotage.md), [R-21](chantiers/r21.md), [R-40/E6](chantiers/r40_e6.md), [audit P1](chantiers/audit_p1.md), [organigramme](chantiers/organigramme.md), [registre](../validation/etat_des_lieux_registre.md), [nappe régionale](../validation/nappe_regionale.md), [karst](../validation/recharge_karst.md). Historique lu avec `git log --since=10.days` et `git log -p --since=10.days -- COORDINATION.md`, état de référence `a167895`.

Sources locales non destinées au dépôt public : base SQLite, `relecteurs.json`, `macons.json`, `situation.yml`, les deux reprises et les comptes rendus de lancements ; seuls des agrégats et identifiants de tâches sont repris ici. Les instantanés de travail `pilotage/etat/audit_organisation_snapshot.json`, `audit_organisation_mesures.json` et `audit_organisation_git.txt` permettent la relecture locale ; ne pas les publier.

Reproduction : extraire les lignes par `SELECT * FROM lancements ORDER BY debut`, exclure `codex/exec-20261113-0900-audit-organisation`, sommer séparément entrée/cache/sortie, et calculer fin moins début à la minute. Le classement détaillé des 58 sujets est conservé dans l’instantané de mesures ; ne pas extrapoler cette ventilation aux 106 lignes sans sujet ni aux sessions mères.

Vérifications de cette livraison : rapprochement des sommes et des effectifs, encodage UTF-8, liens locaux, périmètre du diff et `git diff --check`. Aucun calcul scientifique, téléchargement, lancement de workflow, modification de code ou de règle ; les propositions restent à relire et à décider.
