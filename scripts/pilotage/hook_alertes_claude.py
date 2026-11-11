"""Crochet Claude Code (sans modèle, sans token) : porte à Claude les nouvelles alertes de coordination qui le concernent.

Le surveillant écrit pilotage/etat/coordination/claude.md, mais rien ne l'injectait dans la conversation : le porteur
devait rappeler les messages de Codex (10/11/2026). Ce crochet :
  - UserPromptSubmit / SessionStart : ajoute les alertes non encore vues au contexte de Claude ;
  - Stop : si une alerte est arrivée pendant le tour, empêche Claude de s'arrêter une fois, avec les alertes en motif.
Les alertes déjà portées sont mémorisées (empreintes) dans claude_vu.json. Ne bloque jamais Claude en cas d'erreur.
Usage manuel : --marquer-lues (tout marquer comme vu sans rien afficher).
"""
import hashlib
import json
import os
import sys
from pathlib import Path

DOSSIER = Path(os.environ.get("MAKYCLIMAT_COORD") or Path(__file__).resolve().parents[2] / "pilotage" / "etat" / "coordination")
BOITE, VU = DOSSIER / "claude.md", DOSSIER / "claude_vu.json"
MAX_ALERTES, MAX_CARACTERES = 10, 500


def cle(ligne: str) -> str:
    return hashlib.sha256(" ".join(ligne.split()).encode()).hexdigest()[:16]


def alertes() -> list[str]:
    if not BOITE.exists():
        return []
    return [l[2:].strip() for l in BOITE.read_text(encoding="utf-8").splitlines() if l.startswith("- ") and "Codex" in l]


def verdict(ligne: str) -> str:
    """Pour une relecture terminée, ajoute son verdict (lu dans le fichier de résultat)."""
    for mot in ligne.split(" · "):
        if mot.startswith("relecture-"):
            f = DOSSIER / f"codex-{mot.strip()}.md"
            if f.exists():
                for l in reversed(f.read_text(encoding="utf-8", errors="replace").splitlines()):
                    if l.strip().startswith("Verdict"):
                        return f" → {l.strip()} (avis : pilotage/etat/coordination/{f.name})"
    return ""


def nouvelles(marquer: bool = True) -> list[str]:
    vues = set(json.loads(VU.read_text(encoding="utf-8"))) if VU.exists() else set()
    liste = [a for a in alertes() if cle(a) not in vues]
    if marquer and liste:
        VU.write_text(json.dumps(sorted(vues | {cle(a) for a in liste})), encoding="utf-8")
    return liste


def texte(liste: list[str]) -> str:
    lignes = [f"- {(a + verdict(a))[:MAX_CARACTERES]}" for a in liste[:MAX_ALERTES]]
    reste = f"\n(+ {len(liste) - MAX_ALERTES} autres dans pilotage/etat/coordination/claude.md)" if len(liste) > MAX_ALERTES else ""
    return ("Nouvelles alertes de coordination pour Claude (surveillant, COORDINATION.md fait foi) :\n"
            + "\n".join(lignes) + reste)


def alerte_conversation(session: str) -> str:
    """Une seule fois par niveau et par conversation : contexte chargé, proposer une nouvelle conversation au porteur."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conversations
    c = conversations.charge("claude")
    if not c.get("connue") or c["niveau"] == "ok" or lire_session(session) != session:
        return ""
    vu = DOSSIER / "conversation_vu.json"
    cle_ = f"{session}:{c['niveau']}"
    try:
        deja = json.loads(vu.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        deja = []
    if cle_ in deja:
        return ""
    vu.write_text(json.dumps((deja + [cle_])[-20:]), encoding="utf-8")
    return (f"Conversation chargée à {c['pourcent']} % du contexte : propose au porteur, en une phrase, d'ouvrir une nouvelle "
            "conversation (bouton « Nouvelle conversation » du tableau de bord) à un point propre, après avoir mis à jour "
            "COORDINATION.md et, si utile, pilotage/etat/reprise_claude.md.")


def lire_session(session: str) -> str:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conversations
    return conversations.lire("claude").get("session_id", "")


def main() -> None:
    if "--marquer-lues" in sys.argv:
        nouvelles()
        return
    ev = json.loads(sys.stdin.buffer.read().decode("utf-8", errors="replace") or "{}")
    nom = ev.get("hook_event_name", "")
    if nom == "Stop":
        if ev.get("stop_hook_active"):          # déjà relancé une fois par ce crochet : ne pas boucler
            return
        liste = nouvelles()
        if liste:
            print(json.dumps({"decision": "block", "reason": texte(liste) + "\nTraite-les ou dis au porteur ce que tu en fais avant de t'arrêter."},
                             ensure_ascii=False))
        return
    if nom in ("UserPromptSubmit", "SessionStart"):
        liste = nouvelles()
        contexte = [texte(liste)] if liste else []
        conv = alerte_conversation(ev.get("session_id") or "")
        if conv:
            contexte.append(conv)
        if contexte:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": nom, "additionalContext": "\n".join(contexte)}}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        main()
    except Exception:
        pass
    sys.exit(0)
