"""Alimente le panneau « En ce moment » avec des événements locaux Codex."""

import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
JOURNAL = ROOT / "pilotage" / "etat" / "actions_codex.jsonl"
ETAPES = {
    "UserPromptSubmit": ("demande", "Nouvelle demande reçue"),
    "Stop": ("repos", "Tour terminé"),
    "Interrupt": ("repos", "Tour interrompu"),
}
OUTILS = {
    "Bash": ("commande", "Commande locale lancée"),
    "apply_patch": ("modification", "Modification de fichiers demandée"),
    "Edit": ("modification", "Modification de fichiers demandée"),
    "Write": ("modification", "Écriture de fichiers demandée"),
}


def decrire(evenement):
    nom = evenement.get("hook_event_name")
    if nom == "PreToolUse":
        return OUTILS.get(evenement.get("tool_name"))
    return ETAPES.get(nom)


def main():
    try:
        evenement = json.load(sys.stdin.buffer)
        action = decrire(evenement)
        if action is None:
            return
        genre, texte = action
        ligne = {"quand": datetime.now().isoformat(timespec="seconds"),
                 "agent": "codex", "genre": genre, "texte": texte}
        JOURNAL.parent.mkdir(parents=True, exist_ok=True)
        with JOURNAL.open("ab", buffering=0) as journal:
            journal.write((json.dumps(ligne, ensure_ascii=False) + "\n").encode("utf-8"))
    except (OSError, ValueError, AttributeError, TypeError):
        # Le suivi est facultatif. Un événement invalide ou un journal indisponible
        # ne doit pas interrompre le travail de Codex.
        pass


if __name__ == "__main__":
    main()
