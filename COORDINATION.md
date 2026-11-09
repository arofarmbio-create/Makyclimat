# Coordination de MakyClimat

*Point de reprise du porteur du projet, de Claude Code et de Codex. Lire d'abord la ligne du chantier, puis les pièces liées. Les résultats détaillés vont dans `validation/`.*

## Règles (communes, non négociables)

1. **Le porteur du projet décide** des choix de fond. Les assistants proposent, exécutent, documentent.
2. Le [protocole doctoral](protocole_doctoral_modelisation_climatique_Madagascar.txt) prévaut sur le [prompt maître](prompt_maitre.md). Rattacher chaque étude à son module, son expérience et son hypothèse quand elle existe.
3. Toute nouvelle expérience scientifique exige un protocole écrit et une analyse de puissance **avant le calcul**. Consigner les résultats, échecs compris, dans le [journal](validation/journal_recherche.md) et le [registre](validation/etat_des_lieux_registre.md).
4. Le dépôt est public. Garder secrets, données personnelles et données brutes à diffusion restreinte hors de Git. Vérifier [les règles d'exclusion](.gitignore) et les droits avant d'ajouter des données. Une partie de `data/` est versionnée.
5. Téléchargements : une tâche à la fois par fournisseur (NASA, Copernicus, CHIRPS), rythme lent.
6. **Une tâche = un seul responsable.** Respecter le périmètre des autres chantiers. Pour des modifications en parallèle, utiliser des branches et worktrees distincts après accord, avec entrées partagées en lecture seule et sorties séparées. Indiquer la branche ou le commit de référence quand il existe.
7. Réponses en français et commits signés de leur auteur. Une ligne de suivi ou de relecture ne vaut pas autorisation de publier, de lancer un calcul lourd ou de télécharger. Les autorisations déjà données continuent de s'appliquer.

## Rôles (décision du porteur du projet, 09/11/2026)

- **Porteur du projet** : décide des orientations et des choix de fond.
- **Codex** : assistant de réflexion du porteur du projet ; peut coder et terminer des tâches. **Audite le travail de Claude.**
- **Claude Code** : bras droit pour le code (scripts, workflows, site, calculs). **Vérifie le travail de Codex.**
- Tout livrable de code passe par la relecture de l'autre assistant avant d'être déclaré **Fait**.

## Définition de « Fait » (pour éviter les erreurs coûteuses)

1. Tests concernés lancés et réussis (sur le PC ou sur GitHub), dépendances du workflow vérifiées.
2. Pour un calcul ou un téléchargement : **résultat lu et vérifié**, pas seulement « lancé » ; état du run confirmé.
3. Protocole et code alignés : toute modification de protocole est répercutée dans le code (et inversement).
4. Journal, registre et ligne de ce fichier à jour ; relecture de l'autre assistant demandée.

## Prendre, suivre et transmettre un chantier

1. **À la reprise.** Lire la tâche et ses liens. Vérifier son dernier résultat, l'état Git et le périmètre autorisé. Pour une tâche distante, vérifier l'état du run uniquement si l'accès et la consultation sont autorisés. Une mention « en file » dans ce fichier décrit le dernier état rapporté.
2. **Au démarrage.** Le responsable passe la tâche à **En cours**, précise le résultat attendu et les fichiers concernés, puis avance dans le périmètre convenu. Un seul agent actualise la ligne. Un second agent reçoit une question de relecture ciblée dans sa propre ligne si nécessaire.
3. **À un changement utile.** Mettre à jour la ligne si un résultat est disponible, si une dépendance bloque la suite ou si une décision est requise. En cas de blocage, préciser qui peut le lever et par quelle action. Les vérifications mécaniques se font avec les scripts existants quand ils suffisent. Une passation contient l'état, une preuve et la prochaine action.
4. **À la clôture.** Lier le résultat et indiquer les vérifications faites. Passer à **À relire** si un avis est attendu, à **Prêt à publier** si la publication reste à décider ou à exécuter, puis à **Fait** lorsque le résultat attendu est livré. Si le chantier est abandonné, indiquer **Clos** avec le motif et le lien.

**États** — À faire · En cours · En attente (dépendance ou run) · Bloqué (action nécessaire) · À relire · Prêt à publier · Fait · Clos.

## Tâches

| Tâche | Responsable | État | Preuve ou périmètre | Prochaine action ou condition de fin |
|---|---|---|---|---|
| Audit technique et scientifique | Codex | Fait | [Audit Codex](validation/audit_codex_2026-11-09.md) | Rapport déposé et demande de relecture transmise par ce fichier. |
| Avis sur l'audit | Claude | Fait | [Audit Codex](validation/audit_codex_2026-11-09.md) | CMIP6 (pyyaml manquant, entrées dans le shell) : confirmé. Pluies manquantes mises à zéro dans le bilan hydrique (`scripts/build_soilwater.py`, ligne 358) : confirmé. R-21 protocole réduit mais code inchangé : confirmé. Calibration imbriquée et analogues postérieurs : pertinents, à traiter sous protocole. |
| Correctifs P0 : workflow CMIP6, code R-21, pluies manquantes du bilan hydrique | Claude | À faire | `.github/workflows/build-cmip6-nexgddp.yml`, `scripts/validate_reforecast_impact.py`, `scripts/build_soilwater.py` | Bilan hydrique sous protocole (comparaison avant et après sur les indicateurs publiés). Relecture par Codex avant « Fait ». |
| Site, preuves, libellés et onglet Nappes | Claude | Prêt à publier | [Audit des indicateurs](validation/audit_indicateurs_site.md), `docs/`, `config/indicateurs_preuve.yml` | Reprendre la publication selon l'autorisation en vigueur, puis consigner la version publiée. |
| Durée de la mise à jour du site, étape chocs cyclone | Claude | À faire | [Workflow de publication](.github/workflows/update-data.yml#L90) | Après l'audit, confirmer le goulot d'étranglement et proposer un correctif mesurable par rapport à la limite de 45 minutes. |
| E6 — CMIP6, sonde puis collecte des 28 modèles | Claude | En attente | [Protocole CMIP6](validation/protocole_cmip6.md), [workflow](.github/workflows/build-cmip6-nexgddp.yml) | Après R-40 et la relecture des constats de sécurité et de dépendances, vérifier les prérequis de la sonde. Consigner le résultat avant la collecte. |
| R-40 — Pluie IMERG et rafales des activations EMS | Claude | En attente | [Protocole](validation/protocole_r02bis_echelle_alea.md), [workflow](.github/workflows/build-r02bis-sources.yml) | Confirmer l'état de la file GitHub au prochain contrôle autorisé et noter les fenêtres reçues ou manquantes. |
| R-21 — Reprévisions GloFAS, portée réduite | Claude | En attente | [Protocole de vérification](validation/protocole_verification_impact.md), [script](scripts/validate_reforecast_impact.py) | Vérifier l'état du run signalé et statuer sur l'écart entre périmètre réduit et garde de complétude avant de calculer les scores. |
| Courriers au ministère, à BushProof et à GROSoM / METIS-IPSL | Porteur du projet | À faire | `courriers/` (local) | Relire, choisir les destinataires et décider de l'envoi. |

## Où lire l'état du projet (au lieu des conversations)

- **Responsabilités, prochaine action et arbitrages** — ce fichier.
- **Résultats et décisions scientifiques** — [registre](validation/etat_des_lieux_registre.md), [entrées pertinentes du journal](validation/journal_recherche.md), [méthodologie](validation/methodologie_these.md) et [bilan d'étape](validation/bilan_etape_2026-11-09.md).
- **Téléchargements** — [état des téléchargements](validation/etat_telechargements.md) et pièces du chantier. Vérifier le dernier artefact ou run avant de relancer.
- **Pilotage sur le PC du porteur** — `pilotage/tableau_de_bord.html`, généré depuis `pilotage/objectifs.yml`, `pilotage/protocole_suivi.yml`, `pilotage/glossaire.yml` et le journal. Si un statut affiché diverge d'un rapport ou d'un run confirmé, signaler l'écart au responsable dans la ligne concernée.

## Messages et décisions en attente

- **09/11/2026 · Claude → Codex.** Constats CMIP6, R-21 et bilan hydrique confirmés (voir ligne « Avis sur l'audit ») ; je prends les correctifs P0 et te les soumets en relecture. Rôles et définition de « Fait » ajoutés ci-dessus.

Format d'un nouveau message — `Date · auteur → destinataire · décision ou question précise · lien`. Une fois traité, reporter la décision dans la ligne de tâche ou le journal, puis retirer le message de cette section.
