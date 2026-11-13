# Coordination de MakyClimat

*Source unique de l'état du projet pour le porteur, Claude Code et Codex. **Lecture sobre :** (1) ce fichier ; (2) les [règles](coordination/regles.md), en début de session ; (3) la fiche du chantier de sa tâche (lien « Détail » de sa ligne). L'[archive](validation/coordination_archive.md) ne se lit que sur besoin précis. Une ligne tient en deux phrases ; le détail va dans la fiche ([règles de sobriété](coordination/regles.md#sobriété-en-jetons-décision-du-porteur-du-projet-11112026-2030--à-ajuster-à-lusage)).*

> **Pilotage permanent à distance (porteur, 13/11/2026).** Le porteur est absent des jours entiers, durablement. Claude coordonne (Codex quand le porteur le choisit), déroule le [fil des tâches](pilotage/fil.yml) (local) selon la [délégation](coordination/delegation.md), et rend compte par Telegram ; le porteur tranche par Telegram. Décisions : [proposition, § 11](coordination/proposition_systeme.md#11-décisions-du-13112026-après-midi).

> **Pause des calculs de recherche jusqu'au lundi 16/11** (porteur). D'ici là, seules les étapes du système avancent (bot Telegram, boucle, ménage). Rôles : le porteur collecte les données externes ; Claude, Codex et leurs sessions font le modèle, les hypothèses, les calculs et les vérifications.

**États** — À faire · En cours · En attente (dépendance ou run) · Bloqué (action nécessaire) · À relire · Prêt à publier · Fait · Clos. **Horaires** — Nairobi (UTC+3), `JJ/MM/AAAA HH:mm`.

## Tâches

| Tâche | Responsable | État | Preuve ou périmètre | Prochaine action ou condition de fin | Début | Fin |
|---|---|---|---|---|---|---|
| R-40 — Pluie IMERG et rafales des activations EMS [fil : T-H3.1] | Claude | En attente (pause jusqu'au 16/11) | [Protocole](validation/protocole_r02bis_echelle_alea.md), [workflow](.github/workflows/build-r02bis-sources.yml), [script](scripts/build_r02bis_sources.py), run `43250443721` (réussi) | Les 7 activations sont téléchargées. Bilan et contrôle des données (T-H3.1), puis analyse selon le protocole (T-H3.2). [Détail](coordination/chantiers/r40_e6.md#r-40) | 11/11/2026 18:34 | — |
| E6 — CMIP6, sonde puis collecte des 28 modèles [fil : T-E6.1] | Claude | En attente (R-40) | [Protocole CMIP6](validation/protocole_cmip6.md), [workflow](.github/workflows/build-cmip6-nexgddp.yml) | Après le bilan R-40 : sonde `ACCESS-CM2`, `historical`, `probe=true` sur un seul fichier, vérifier avant la collecte. [Détail](coordination/chantiers/r40_e6.md#e6) | 10/11/2026 19:06 | — |
| Démarches externes (ministère de l'Eau, chlorure de la pluie, BushProof, DGM, BNGRC, débits, Mines) | Porteur du projet | À faire | `courriers/` (local), démarches `X-…` du fil | Courriers MEAH, chlorure et BushProof prêts : relire, choisir le destinataire, envoyer. Les autres sont préparés par Claude. | — | — |
| Fil des tâches (tout le protocole doctoral et tout le site) [fil : S-PIL.3] | Claude | En attente du porteur (ce que lui seul sait) | `pilotage/fil.yml` (local, v2), [module](scripts/pilotage/fil.py), [tests](tests/test_fil.py) | Relu une fois par Codex (15 bloquants, 2 améliorations, intégrés) : 19 objectifs, 107 étapes, 44 données, 9 démarches. Reste : contacts, données déjà en main, priorités. | 13/11/2026 | — |
| Délégation écrite [fil : S-PIL.4] | Claude | À valider par le porteur | [délégation](coordination/delegation.md) | Trois niveaux, garde-fous (STOP, plafond de 8 lancements par jour, journal, canal unique). Validation : Telegram `/valider S-PIL.4`. | 13/11/2026 | — |
| Notifications (ntfy) et boucle de coordination [fil : S-PIL.6] | Claude | En cours | [boucle](scripts/pilotage/telegram_bot.py), [canal ntfy](scripts/pilotage/canal_ntfy.py), [tests](tests/test_canal_ntfy.py), [lanceur](pilotage_permanent.cmd), [installation au démarrage](scripts/pilotage/installer_demarrage.py) | ntfy choisi par le porteur (13/11 : Telegram facturait l'inscription) ; boutons signés, code personnel pour les actions ; essai réel de ntfy.sh réussi. Reste : initialisation et abonnement (porteur), installation au démarrage, essai de bout en bout. | 13/11/2026 | — |
| Ménage de l'état [fil : S-PIL.9] | Claude | Fait | ce fichier (35 → 8 Ko), [archive](validation/coordination_archive.md#archivé-le-13112026-ménage-du-fil-des-tâches-étape-s-pil9) | 24 lignes terminées, 14 exécutions, 1 message et 2 décisions archivés ; un seul point de reprise : `pilotage/etat/reprise_claude.md`. | 13/11/2026 | 13/11/2026 |

## Messages et décisions en attente

Format — `Date · auteur → destinataire · question précise · lien`. Réservé aux questions qui demandent une réponse ; une fois traité, consigner la décision dans la ligne ou la fiche et retirer le message (il part dans l'archive).

## Exécutions autorisées

Ajoutées par le tableau de bord après un clic du porteur du projet. Le surveillant les exécute une à une en mode écriture ; l'agent coche sa ligne à la fin.

## Décisions du porteur du projet

Réponses données depuis le tableau de bord. L'assistant concerné les lit à sa reprise et met sa ligne de tâche à jour.

- 13/11/2026 après-midi · Porteur du projet → Claude et Codex · **Pilotage permanent à distance** (discussion du 13/11, feu vert « fonce ») : (1) le porteur est absent plusieurs jours de suite, **durablement** : le système tourne seul et se pilote par Telegram (compte rendu quotidien, décisions groupées, STOP) ; (2) **délégation à trois niveaux** (seuls / par Telegram / interdit sans le porteur), à écrire ; (3) **relectures plafonnées à 3 tours**, points bloquants définis d'avance, désaccord restant → une décision Telegram ; (4) **score sous la cible** : on corrige les erreurs, on ne règle pas le modèle sur le test, une version 2 se teste sur des données neuves ; (5) **échelle de fiabilité** : aucune, provisoire, exploratoire, soutenue, confirmée ; (6) **fil des tâches** pour tout le protocole doctoral et tout le site : objectif → résultats → calculs → données (disponibles, manquantes, zones) → responsable et moyen, source unique `pilotage/fil.yml` (local, noms de personnes hors dépôt). **Gel de la règle 12 levé** pour le fil, Telegram et la boucle de coordination. Détail : [proposition, § 11](coordination/proposition_systeme.md#11-décisions-du-13112026-après-midi).

- 13/11/2026 09:00 · Porteur du projet → Claude et Codex · **Organisation à venir (décisions de principe, rien n'est codé avant validation de la proposition d'ensemble)** : un **coordinateur alterné**, Claude ou Codex, avec **les mêmes droits** (commit et push compris quand il coordonne), choisi par le porteur depuis le tableau de bord, et passant à l'autre avant les limites d'usage ; PC et tablette allumés en permanence ; notifications et autorisations par **Telegram** ; secours par **SMS** via la tablette (SIM dédiée) ; **pas d'automatisation WhatsApp** (brouillons envoyés par Telegram, copiés par le porteur) ; e-mails : niveau à décider. Proposition d'ensemble : `coordination/proposition_systeme.md`.
- 13/11/2026 08:00 · Porteur du projet → Claude et Codex · **Suite de R-21 bis : option 1, test EMS par sous-bassin**, avec dérogation au seuil de 25 % (section 8 du protocole), consignée comme une nouvelle question issue du diagnostic, sans modifier R-21 bis. Conditionnée à une **étape de faisabilité bloquante** (avis du relecteur attitré de Codex, 13/11) : audit des usages antérieurs d'EMS (R-02 bis, R-40, R-21, seuils) ; inventaire des activations sur les **seules métadonnées** ; puissance comptée en événements et saisons indépendants. Si l'indépendance n'est pas garantie ou si la puissance est inférieure à 80 % pour l'effet fixé : **option 3** (clôture, apport de méthode), sans prolongation exploratoire.

## Lancements ponctuels autorisés

Format d'une demande validée par le coordinateur — ``- [ ] `claude:identifiant-unique` Consigne de lecture seule.`` Les échanges ordinaires ne déclenchent aucun appel.
