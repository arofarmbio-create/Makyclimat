# Instructions pour Codex

Au démarrage, lis [COORDINATION.md](COORDINATION.md) (index court des tâches et décisions), puis les [règles](coordination/regles.md), puis la fiche de ton chantier (lien « Détail » de sa ligne). N'ouvre l'[archive](validation/coordination_archive.md) que sur besoin précis (règles de sobriété, 11/11/2026).
Suis les liens utiles à la tâche et mets à jour sa ligne (deux phrases) au prochain changement significatif ; le détail va dans la fiche.
Consulte `pilotage/etat/coordination/codex.md` si présent. Vérifie dans la coordination que l'alerte est encore d'actualité.
Avant d'ouvrir une nouvelle conversation, tiens ton point de reprise `pilotage/etat/reprise_codex.md` (local, non versionné) : fichiers non commités, travail en cours, prochaines étapes, sans copier COORDINATION.md. Lis-le au démarrage.

Tes sessions enfants n'écrivent pas dans `.git` : ne commite pas et ne pousse pas. Laisse les fichiers modifiés, liste-les dans ta ligne de tâche et passe-la à « À commiter par Claude » ; la session mère de Claude relit le diff puis commite (décision du porteur, 11/11/2026). Mets ton point de reprise à jour à la fin de chaque exécution.

Lire GitHub (runs, journaux, releases) est autorisé en permanence : ne demande pas la permission. Lis d'abord `pilotage/etat/github_direct.json`, tenu par le poste, et n'interroge GitHub que s'il manque ou date de plus de 15 min. Ne pose pas de question d'autorisation dans le chat : écris-la dans « Messages et décisions en attente » de COORDINATION.md, le porteur répond depuis le poste de pilotage (règle 10, 11/11/2026). Écris tes fichiers en UTF-8 : les accents doivent rester des accents, jamais « ? ».
