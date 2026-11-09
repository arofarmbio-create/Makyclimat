# Instructions pour Codex (et tout agent de code)

Avant toute action, lis **`COORDINATION.md`** : règles communes, tâches et responsables, messages en attente. Il
remplace l'historique des conversations.

- Projet de thèse : MakyClimat, climat, eau et impacts humanitaires à Madagascar. Langue : **français**.
- **Le porteur du projet décide** des choix de fond ; proposer, ne pas trancher à sa place.
- Téléchargements : une tâche à la fois par fournisseur (NASA, Copernicus, CHIRPS), sans relances en rafale.
- **Où calculer** : sur GitHub Actions les mises à jour programmées, les téléchargements avec identifiants et les
  calculs longs sur données publiques (sorties lourdes en release, pas dans Git) ; sur le PC tout ce qui utilise des
  données non publiables (MGMERL brut, BushProof, GROSoM, carte PGRM) et les calculs courts.
- Cadre prioritaire : `protocole_doctoral_modelisation_climatique_Madagascar.txt`, puis `prompt_maitre.md` (section 0).
- Ne modifie pas un fichier lié à une tâche « en cours » d'un autre responsable (voir `COORDINATION.md`).
- Tout calcul nouveau : protocole écrit avant le calcul (`validation/protocole_*.md`), analyse de puissance, puis
  résultat consigné dans `validation/journal_recherche.md` et le registre, échecs compris.
- Dépôt public : garder les données brutes à diffusion restreinte hors de Git. Vérifier `.gitignore` avant d'ajouter des données, car une partie de `data/` est versionnée.
- Python : `.venv/Scripts/python.exe` sur le PC du porteur du projet ; tests dans `tests/` (lancés aussi sur GitHub).
- En fin de tâche : mets à jour ta ligne dans `COORDINATION.md` et laisse au besoin un message d'une ou deux lignes.
