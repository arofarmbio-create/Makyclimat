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


def remettre_messages(evenement):
    """Messages du porteur (poste de pilotage) remis à la session mère Codex à sa prochaine demande, une seule fois.
    Une session enfant (codex exec) n'est pas la session suivie : elle ne les reçoit pas."""
    if evenement.get("hook_event_name") != "UserPromptSubmit":
        return
    import conversations
    import poste
    sid = evenement.get("session_id") or evenement.get("thread_id") or ""
    if not sid or conversations.lire("codex").get("session_id") != sid:
        return
    liste = poste.a_remettre("codex")
    if not liste:
        return
    poste.marquer_remis("codex", [m["id"] for m in liste])
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                             "additionalContext": poste.texte_remise("codex", liste)}},
                     ensure_ascii=False))


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
        try:
            import conversations
            conversations.noter_codex(evenement)
        except (OSError, ValueError, AttributeError, TypeError):
            pass
        with JOURNAL.open("ab", buffering=0) as journal:
            journal.write((json.dumps(ligne, ensure_ascii=False) + "\n").encode("utf-8"))
        remettre_messages(evenement)
    except (OSError, ValueError, AttributeError, TypeError, ImportError):
        # Le suivi est facultatif. Un événement invalide ou un journal indisponible
        # ne doit pas interrompre le travail de Codex.
        pass


if __name__ == "__main__":
    main()
