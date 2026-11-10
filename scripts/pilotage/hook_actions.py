"""Crochet Claude Code (sans modèle, sans token) : note chaque action de Claude dans pilotage/etat/actions_claude.jsonl
pour le panneau « En ce moment » du tableau de bord.

Format d'une ligne, commun à tous les assistants (Codex peut écrire actions_codex.jsonl au même format) :
    {"quand": "2026-11-10T09:12:03", "agent": "claude", "genre": "commande|modification|lecture|recherche|demande|repos|autre",
     "texte": "Lancer les tests du bilan hydrique"}

Confidentialité : on n'enregistre jamais le texte d'une commande ni d'une demande, seulement la description donnée par
l'assistant ou le chemin relatif du fichier. Ne doit jamais bloquer Claude Code : toute erreur est ignorée.
"""
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ETAT = ROOT / "pilotage" / "etat" / "actions_claude.jsonl"
GARDER, MAX = 300, 600          # au-delà de MAX lignes, on ne garde que les GARDER dernières


def relatif(chemin: str) -> str:
    try:
        return Path(chemin).resolve().relative_to(ROOT).as_posix()
    except (ValueError, OSError):
        return Path(chemin).name or "fichier hors du dépôt"


def decrire(ev: dict) -> tuple[str, str]:
    nom = ev.get("hook_event_name", "")
    if nom == "UserPromptSubmit":
        return "demande", "Nouvelle demande du porteur reçue"
    if nom == "Stop":
        return "repos", "Tour terminé : en attente du porteur"
    outil = ev.get("tool_name", "")
    ti = ev.get("tool_input") or {}
    if outil in ("Bash", "PowerShell"):
        return "commande", ti.get("description") or "Commande sans description"
    if outil in ("Edit", "Write", "NotebookEdit"):
        return "modification", ("Écrit " if outil == "Write" else "Modifié ") + relatif(ti.get("file_path") or ti.get("notebook_path") or "")
    if outil == "Read":
        return "lecture", "Lu " + relatif(ti.get("file_path") or "")
    if outil in ("Grep", "Glob"):
        return "recherche", f"Recherche « {str(ti.get('pattern', ''))[:60]} »"
    if outil == "Agent":
        return "commande", "Agent lancé : " + (ti.get("description") or "sans description")
    if outil in ("WebSearch", "WebFetch") or outil.startswith("mcp__"):
        return "recherche", "Recherche en ligne (" + outil.split("__")[-1] + ")"
    return "autre", outil or nom or "action"


def main() -> None:
    ev = json.loads(sys.stdin.buffer.read().decode("utf-8", errors="replace") or "{}")
    genre, texte = decrire(ev)
    row = {"quand": dt.datetime.now().isoformat(timespec="seconds"), "agent": "claude", "genre": genre, "texte": texte[:160]}
    ETAT.parent.mkdir(parents=True, exist_ok=True)
    with open(ETAT, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    lignes = ETAT.read_text(encoding="utf-8").splitlines()
    if len(lignes) > MAX:
        ETAT.write_text("\n".join(lignes[-GARDER:]) + "\n", encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
