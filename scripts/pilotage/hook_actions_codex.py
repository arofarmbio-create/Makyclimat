"""Alimente le panneau « En ce moment » avec des événements locaux Codex."""

import json
import re
import shlex
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


ENVELOPPES = {"bash", "sh", "powershell", "pwsh", "cmd"}       # « bash -lc "…" » : on lit la commande intérieure
# Sous-commandes affichables, par programme (relecture Codex du 11/11, 20:55) : seuls ces mots, placés juste après le
# programme, sont montrés. Une option (« git -C chemin status », « gh --hostname serveur run ») arrête la lecture, si
# bien qu'aucune valeur d'option ni aucun argument libre n'apparaît.
SOUS_COMMANDES = {
    "git": [{"status", "diff", "log", "show", "add", "commit", "push", "pull", "fetch", "branch", "checkout",
             "switch", "restore", "rev-parse", "ls-files", "stash", "merge", "rebase", "remote", "blame", "grep",
             "reset", "tag", "cat-file", "mv", "rm"}],
    "gh": [{"run", "api", "release", "workflow", "pr", "issue", "repo", "auth", "cache"},
           {"view", "list", "download", "rerun", "watch", "create", "cancel", "run", "delete", "upload", "status",
            "edit", "merge", "checks", "diff", "enable", "disable"}],
    "npm": [{"install", "run", "test", "ci"}],
    "pip": [{"install", "list", "show", "freeze"}],
    "uv": [{"run", "pip", "sync"}],
    "codex": [{"exec"}],
}
NOM_SUR = re.compile(r"^[\w.+-]{1,40}$")
SCRIPT_SUR = re.compile(r"^[\w./\-]{1,120}\.(py|ps1|cmd|bat|sh)$", re.I)
OPTION_COMMANDE = {"powershell": {"-command", "-c"}, "pwsh": {"-command", "-c"}, "cmd": {"/c", "/k"}}


def interieur(enveloppe, mots):
    """Commande portée par une enveloppe : argument de -Command (PowerShell), de /c (cmd) ou de -c, -lc… (bash, sh).
    None si la forme n'est pas reconnue : le panneau garde alors le libellé générique."""
    for i, mot in enumerate(mots[1:], 1):
        bas = mot.lower()
        if bas in OPTION_COMMANDE.get(enveloppe, set()) or (
                enveloppe in {"bash", "sh"} and re.fullmatch(r"-[a-z]*c", bas)):
            reste = mots[i + 1:]
            return " ".join(reste) if reste else None
    return None


def programme(commande):
    """Programme lancé, sans ses arguments : « git status », « gh run view », « python scripts/x.py ».
    Rien d'autre de la commande n'est retenu (confidentialité). None si on ne sait pas le dire sûrement."""
    try:
        if isinstance(commande, list):
            mots = [str(m) for m in commande]
        else:
            mots = shlex.split(str(commande).replace("\\", "/"), posix=True)  # chemins Windows
    except ValueError:
        mots = str(commande).split()
    for _ in range(2):  # au plus deux enveloppes (powershell -Command "bash -lc …" est improbable)
        if not mots:
            break
        enveloppe = Path(mots[0].replace("\\", "/")).stem.lower()
        if enveloppe not in ENVELOPPES:
            break
        texte = interieur(enveloppe, mots)
        if texte is None:
            return None
        try:
            mots = shlex.split(texte.replace("\\", "/"), posix=True)
        except ValueError:
            mots = texte.split()
    mots = [m for m in mots if "=" not in m or m.startswith("-")]    # variables d'environnement en tête
    if not mots:
        return None
    nom = Path(mots[0].replace("\\", "/")).stem.lower()
    if not NOM_SUR.match(nom):
        return None
    if nom.startswith("python") or nom == "py":
        if "-m" in mots[:-1]:
            module = mots[mots.index("-m") + 1]
            return f"python -m {module}" if NOM_SUR.match(module) else "python"
        if "-c" in mots:
            return "python"
        script = next((m for m in mots[1:] if SCRIPT_SUR.match(m)), None)
        return f"python {script}" if script else "python"
    suite = []
    for autorises, mot in zip(SOUS_COMMANDES.get(nom, []), mots[1:]):
        if mot not in autorises:
            break
        suite.append(mot)
    return " ".join([nom, *suite])


def decrire(evenement):
    nom = evenement.get("hook_event_name")
    if nom == "PreToolUse":
        action = OUTILS.get(evenement.get("tool_name"))
        if action and action[0] == "commande":
            prog = programme((evenement.get("tool_input") or {}).get("command") or "")
            if prog:
                return "commande", f"Lance {prog}"
        return action
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
