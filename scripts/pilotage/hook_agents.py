"""Hook Claude Code (sans modèle, sans token) : ajoute une ligne JSON dans pilotage/etat/agents.jsonl à chaque
lancement d'agent (PreToolUse sur l'outil Agent, SubagentStart) et à chaque fin (SubagentStop).
Lit l'événement sur l'entrée standard. Ne doit jamais bloquer Claude Code : toute erreur est ignorée.
"""
import datetime as dt
import json
import sys
from pathlib import Path

ETAT = Path(__file__).resolve().parents[2] / "pilotage" / "etat" / "agents.jsonl"


def main() -> None:
    try:
        ev = json.loads(sys.stdin.read() or "{}")
    except Exception:
        ev = {}
    ti = ev.get("tool_input") or {}
    row = {
        "quand": dt.datetime.now().isoformat(timespec="seconds"),
        "evenement": ev.get("hook_event_name", ""),
        "session": ev.get("session_id", ""),
        "agent_id": ev.get("agent_id", ""),
        "type": ev.get("agent_type", "") or ti.get("subagent_type", ""),
        "description": ti.get("description", ""),
        "arriere_plan": bool(ti.get("run_in_background", False)),
    }
    ETAT.parent.mkdir(parents=True, exist_ok=True)
    with open(ETAT, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
