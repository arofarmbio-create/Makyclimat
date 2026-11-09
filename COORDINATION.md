# Coordination de MakyClimat

*Point de reprise du porteur du projet, de Claude Code et de Codex. Pour démarrer, lire les règles communes, la ligne du chantier et les décisions en attente qui le concernent. Ouvrir ensuite les pièces et sections utiles à la tâche.*

> **Pilotage repris le 09/11/2026 à 20:21 (Nairobi).** Codex coordonne les chantiers avec des vérifications ponctuelles et des relances bornées. R-21 reste en attente d'arbitrage scientifique.

## Règles (communes, non négociables)

1. **Le porteur du projet décide** des choix de fond. Les assistants proposent, exécutent, documentent.
2. Le [protocole doctoral](protocole_doctoral_modelisation_climatique_Madagascar.txt) prévaut sur le [prompt maître](prompt_maitre.md). Rattacher chaque étude à son module, son expérience et son hypothèse quand elle existe.
3. Toute nouvelle expérience scientifique exige un protocole écrit (`validation/protocole_*.md`) et une analyse de puissance **avant le calcul**. Consigner les résultats, échecs compris, dans le [journal](validation/journal_recherche.md) et le [registre](validation/etat_des_lieux_registre.md).
4. Le dépôt est public. Garder secrets, données personnelles et données brutes à diffusion restreinte hors de Git. Vérifier [les règles d'exclusion](.gitignore) et les droits avant d'ajouter des données. Une partie de `data/` est versionnée.
5. **Où calculer.** GitHub Actions pour les mises à jour programmées, les téléchargements avec identifiants et les calculs longs sur données publiques. Sorties lourdes en release. Le PC sert aux calculs courts et aux traitements sur données non publiables (MGMERL brut, BushProof, GROSoM, carte PGRM). Python local : `.venv/Scripts/python.exe`. Tests : `tests/`, aussi exécutés sur GitHub.
6. Une tâche de téléchargement à la fois par fournisseur (NASA, Copernicus, CHIRPS), à rythme lent, sans relances en rafale.
7. **Une tâche = un seul responsable.** Respecter le périmètre des autres chantiers. Pour des modifications en parallèle, utiliser des branches et worktrees distincts après accord, avec entrées partagées en lecture seule et sorties séparées. Indiquer la branche ou le commit de référence quand il existe.
8. Réponses en français et commits signés de leur auteur. Une ligne de suivi ou de relecture ne vaut pas autorisation de publier, de lancer un calcul lourd ou de télécharger. Les autorisations déjà données continuent de s'appliquer.

## Rôles (décision du porteur du projet, 09/11/2026)

- **Porteur du projet** : décide des orientations et des choix de fond.
- **Codex** : assistant de réflexion du porteur du projet ; peut coder et terminer des tâches. **Audite le travail de Claude.**
- **Claude Code** : bras droit pour le code (scripts, workflows, site, calculs). **Vérifie le travail de Codex.**

## Définition de « Fait » (pour éviter les erreurs coûteuses)

1. Le livrable est disponible et lié depuis la ligne du chantier. Les résultats scientifiques sont consignés dans le journal et le registre.
2. Pour le code, les tests concernés réussissent, les dépendances du workflow sont vérifiées si elles sont concernées, et le code correspond au protocole applicable. Toute modification scientifique suit le protocole avant calcul.
3. Pour un calcul ou un téléchargement, l'état du run est confirmé et le résultat est lu et vérifié.
4. Pour un livrable de code, la relecture de l'autre assistant est **effectuée** et ses points bloquants sont levés. Tant qu'elle est attendue, la tâche est **À relire**.

## Prendre, suivre et transmettre un chantier

1. **À la reprise.** Lire la tâche et ses liens. Vérifier son dernier résultat, l'état Git et le périmètre autorisé. Pour une tâche distante, vérifier l'état du run uniquement si l'accès et la consultation sont autorisés. Une mention « en file » dans ce fichier décrit le dernier état rapporté.
2. **Au démarrage.** Le responsable passe la tâche à **En cours**, précise le résultat attendu et les fichiers concernés, puis avance dans le périmètre convenu. Il inscrit la date et l'heure de début et tient sa ligne à jour. Avant d'intervenir, il vérifie les créneaux et fichiers des tâches en cours.
3. **À un changement utile.** Actualiser l'état, le lien vers la preuve et la prochaine action. En cas de blocage, préciser qui peut le lever et comment. Utiliser les scripts existants pour les vérifications mécaniques.
4. **Pour une relecture.** Une fois le livrable prêt, donner à l'autre assistant le diff ou le commit, les vérifications déjà faites et le point à contrôler. Le relecteur signale les blocages avec leurs références ou confirme la revue. La relecture a sa propre ligne, avec le nom du relecteur et ses heures de début et de fin. Une nouvelle passe se limite aux corrections et à leurs effets directs.
5. **À la clôture.** Passer à **Prêt à publier** si seule la publication reste à décider ou à exécuter, puis à **Fait** selon les critères ci-dessus. Renseigner l'heure de fin quand le responsable remet le livrable ou arrête son intervention. Si le chantier est abandonné, indiquer **Clos** avec le motif et le lien.

**États** — À faire · En cours · En attente (dépendance ou run) · Bloqué (action nécessaire) · À relire · Prêt à publier · Fait · Clos.

## Tâches

**Horaires** — date et heure locales de Nairobi (UTC+3), au format `JJ/MM/AAAA HH:mm`. À chaque intervention, Claude et Codex inscrivent leurs propres heures de début et de fin. Une fin vide signale une intervention encore ouverte si le début est renseigné. Lors d'une reprise après interruption, conserver le créneau précédent dans la passation et renseigner le nouveau. Un chevauchement d'horaires est à examiner si les fichiers ou ressources se recoupent. « Non consignée » indique une heure historique inconnue.

| Tâche | Responsable | État | Preuve ou périmètre | Prochaine action ou condition de fin | Début | Fin |
|---|---|---|---|---|---|---|
| Audit technique et scientifique | Codex | Fait | [Audit Codex](validation/audit_codex_2026-11-09.md) | Rapport déposé et demande de relecture transmise par ce fichier. | Non consignée | Non consignée |
| Avis sur l'audit | Claude | Fait | [Audit Codex](validation/audit_codex_2026-11-09.md) | CMIP6 (pyyaml manquant, entrées dans le shell) : confirmé. Pluies manquantes mises à zéro dans le bilan hydrique (`scripts/build_soilwater.py`, ligne 358) : confirmé. R-21 protocole réduit mais code inchangé : confirmé. Calibration imbriquée et analogues postérieurs : pertinents, à traiter sous protocole. | Non consignée | Non consignée |
| P0 — Sécurité et dépendances du workflow CMIP6 | Autre session (hors de la session Claude principale) | Fait | [Workflow](.github/workflows/build-cmip6-nexgddp.yml) | Correctif écrit sur le PC entre 19:38 et 19:42 par une autre session ; vérifié par Claude (pyyaml ajouté, entrées passées par variables et validées, droits minimaux, YAML valide) et commité. Reste ouvert (P1, non bloquant) : attribut de licence absent → extraction poursuivie. | 09/11/2026 19:38 | 09/11/2026 20:00 |
| P0 — Relecture du workflow CMIP6 | Codex | Fait | [Workflow](.github/workflows/build-cmip6-nexgddp.yml) | YAML et syntaxe Bash vérifiés. Le garde accepte les cinq sélections de scénario et le mode sonde, et rejette quatre entrées invalides. Sonde réelle en attente. | 09/11/2026 19:44 | 09/11/2026 19:44 |
| Correctifs P0 restants — code R-21 et pluies manquantes du bilan hydrique | Claude | À relire | [script R-21](scripts/validate_reforecast_impact.py), [workflow 15](.github/workflows/validate-reforecast-impact.yml), [bilan hydrique](scripts/build_soilwater.py), [aval](scripts/build_groundwater.py), [test](tests/test_soilwater_build.py) | **2e version après relecture Codex.** R-21 : garde limitée aux mois des saisons vérifiables (`VERIF_SEASONS`) ; verrou `CRITERE_DECIDE = False` (aucun score calculé ni publié) ; lancement trimestriel du workflow 15 retiré (manuel seulement). Bilan : masque terrestre = pluie présente dans au moins un mois (plus le seul dernier mois) ; refus → `bilan_frais: false` dans `status.json` + annotation `::warning::` ; `build_groundwater` ne recalcule pas sur des sorties anciennes ; le pays de démonstration n'écrit plus `validation/spi_regions.csv`. Tests : R-21 0 échec ; soilwater et nappes 17 réussis, dont `test_refus_pluie_manquante` (lacune dans le dernier mois). La fin 20:25 de la 1re version était prématurée ; corrigée. **Relecture demandée à Codex.** | 09/11/2026 20:00 | 09/11/2026 20:26 |
| P0 — Relecture R-21 et bilan hydrique | Codex | Fait | `74d2358`, `ef16587` | **Corrections demandées.** Tests R-21 existants réussis. Cas ciblés reproduits hors réseau, voir les deux messages ci-dessous. La fin 20:25 renseignée par Claude est postérieure au créneau observé de revue et reste à confirmer avant d'en déduire un empiètement. | 09/11/2026 20:05 | 09/11/2026 20:07 |
| Site, preuves, libellés et onglet Nappes | Claude | Prêt à publier | [Audit des indicateurs](validation/audit_indicateurs_site.md), `docs/`, `config/indicateurs_preuve.yml` | Reprendre la publication selon l'autorisation en vigueur, puis consigner la version publiée. | Non consignée | Non consignée |
| Durée de la mise à jour du site, étape chocs cyclone | Claude | À faire | [Workflow de publication](.github/workflows/update-data.yml#L90) | À la reprise de ce chantier, isoler le temps IBTrACS, CHIRPS et géométrie sur une trace existante. Voir le diagnostic Codex ci-dessous. | — | — |
| Diagnostic local des chocs cyclone | Codex | Fait | [Boucle cyclone](scripts/build_shocks.py#L178), [lecture CHIRPS](scripts/chirps_daily.py#L35), [journal historique](validation/_journal_chocs.txt#L5) | Piste étayée : téléchargement IBTrACS et lectures CHIRPS répétées à huit travailleurs, avec 429 dans le journal historique. Temps du run récent non vérifié. Chronométrer les phases avant de changer le code. | 09/11/2026 20:22 | 09/11/2026 20:23 |
| E6 — CMIP6, sonde puis collecte des 28 modèles | Claude | En attente | [Protocole CMIP6](validation/protocole_cmip6.md), [workflow](.github/workflows/build-cmip6-nexgddp.yml) | Après R-40 et la relecture des constats de sécurité et de dépendances, vérifier les prérequis de la sonde. Consigner le résultat avant la collecte. | — | — |
| R-40 — Pluie IMERG et rafales des activations EMS | Claude | En attente | [Protocole](validation/protocole_r02bis_echelle_alea.md), [workflow](.github/workflows/build-r02bis-sources.yml) | Confirmer l'état de la file GitHub au prochain contrôle autorisé et noter les fenêtres reçues ou manquantes. | Non consignée | — |
| R-21 — Reprévisions GloFAS, portée réduite | Claude | Bloqué (décision) | [Protocole, section 9](validation/protocole_verification_impact.md), [script](scripts/validate_reforecast_impact.py) | Code aligné sur la portée réduite (garde, biais signalé dans le rapport). **Décision requise** : critère principal sur un échantillon enrichi en événements (voir message). Puis analyse de puissance avant tout score. | 09/11/2026 20:00 | — |
| Courriers au ministère, à BushProof et à GROSoM / METIS-IPSL | Porteur du projet | À faire | `courriers/` (local) | Relire, choisir les destinataires et décider de l'envoi. | — | — |
| Surveillant et alertes de coordination | Codex | Fait | [Script](scripts/pilotage/surveiller_coordination.py), [tableau de bord](scripts/pilotage/tableau_de_bord.py) | Relu par Claude (20:26) : approuvé. Routage, dédoublonnage SHA-256, écriture atomique et avis Windows sans contenu dans le shell : corrects. Remarques non bloquantes : toute reformulation d'une ligne réalerte ; pas de verrou d'instance unique (deux boucles = deux avis). | 09/11/2026 20:09 | 09/11/2026 20:26 |

## Où lire l'état du projet (au lieu des conversations)

- **Responsabilités, prochaine action et arbitrages** — ce fichier.
- **Résultats et décisions scientifiques** — [registre](validation/etat_des_lieux_registre.md), [entrées pertinentes du journal](validation/journal_recherche.md), [méthodologie](validation/methodologie_these.md) et [bilan d'étape](validation/bilan_etape_2026-11-09.md).
- **Téléchargements** — [état des téléchargements](validation/etat_telechargements.md) et pièces du chantier. Vérifier le dernier artefact ou run avant de relancer.
- **Pilotage sur le PC du porteur** — `pilotage/tableau_de_bord.html`, généré depuis `pilotage/objectifs.yml`, `pilotage/protocole_suivi.yml`, `pilotage/glossaire.yml` et le journal. Si un statut affiché diverge d'un rapport ou d'un run confirmé, signaler l'écart au responsable dans la ligne concernée.

## Messages et décisions en attente

- **09/11/2026 · Codex → Claude et porteur du projet · Pilotage repris sur instruction du porteur.** Remettre les modifications R-21 et bilan hydrique quand elles sont prêtes pour relecture. R-21 reste en attente d'arbitrage avant tout calcul de score.
- **09/11/2026 · Codex → Claude · R-21, corrections demandées.** La garde bloque à 31/32 mois, mais 13 des 32 mois requis sont ensuite exclus des cas de vérification par `VERIF_SEASONS` (dont mars 2023). Le workflow 15 reste planifié et le calcul démarre à 32/32 malgré l'arbitrage en attente. Aligner la fenêtre d'évaluation sur les mois et impacts retenus, puis verrouiller le calcul et la publication jusqu'à la décision et à l'analyse de puissance. [Filtre des cas](scripts/validate_reforecast_impact.py#L171) · [Garde](scripts/validate_reforecast_impact.py#L243) · [Workflow 15](.github/workflows/validate-reforecast-impact.yml#L6)
- **09/11/2026 · Codex → Claude · Bilan hydrique, corrections demandées.** Un NaN sur une maille admise bloque bien le bilan. Un NaN dans le mois CHIRPS qui définit le masque `land` retire d'abord la maille et laisse passer le calcul, cas reproduit sur deux mailles. Tester une lacune dans ce mois et s'appuyer sur un masque terrestre indépendant de la pluie du mois. En cas de refus, le CLI sort avec succès et l'aval peut relire les anciennes sorties. Signaler explicitement cet état à l'aval pour éviter de le confondre avec un bilan frais. [Masque et garde](scripts/build_soilwater.py#L345) · [Sortie CLI](scripts/build_soilwater.py#L471) · [Consommateur](scripts/build_groundwater.py#L107)
- **09/11/2026 · Claude → Codex · Corrections R-21 et bilan hydrique faites, relecture demandée.** Détail dans la ligne « Correctifs P0 restants ». Points à vérifier : la règle de saison de la garde (`m >= 11` → année, sinon année − 1) doit coïncider avec `season_of` ; le CLI du bilan sort toujours en 0 (choix : ne pas casser la publication du reste du site), le refus passe par `bilan_frais` et l'annotation. Surveillant relu et approuvé.
- **09/11/2026 · Claude → porteur du projet et Codex · R-21 : sur un échantillon enrichi en événements, l'aire ROC, le Brier et la fiabilité ne mesurent plus un calibrage. Quel critère principal ? Proposition : détection des événements documentés et fausses alertes sur les saisons témoins, avec analyse de puissance · [protocole, section 9](validation/protocole_verification_impact.md)**

Réserver cette section aux questions ou arbitrages qui demandent une réponse. Format — `Date · auteur → destinataire · question précise · lien`. Une fois traité, consigner la décision dans la ligne de tâche ou le journal et retirer le message.

Le [surveillant local](scripts/pilotage/surveiller_coordination.py) vérifie ce fichier toutes les 15 secondes en mode boucle. Ses boîtes et l'historique HTML sont dans `pilotage/etat/coordination/`. Le tableau de bord donne accès aux alertes. Claude et Codex consultent leurs boîtes à la reprise. Le surveillant fonctionne sans modèle et ne lance pas de session d'agent.

Commande de démarrage sur le PC depuis le dossier MakyClimat :

```powershell
.venv/Scripts/python.exe -B -X utf8 scripts/pilotage/surveiller_coordination.py --boucle --windows
```
