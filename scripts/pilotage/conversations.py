"""Charge des conversations des assistants et changement de conversation en un clic (tableau de bord, 11/11/2026).

- Le crochet d'actions de Claude appelle noter() au début et à la fin de chaque tour : identifiant de session, processus
  claude.exe de la conversation interactive (les sessions lancées par le surveillant sont ignorées) et jetons du contexte,
  lus dans le dernier « usage » du journal de la conversation. Résultat : pilotage/etat/session_claude.json.
- Codex peut écrire pilotage/etat/session_codex.json au même format ({"jetons": ..., "maj": ...}) pour avoir sa jauge.
- nouvelle_conversation() ouvre une nouvelle fenêtre Claude Code avec une consigne de reprise, puis ferme l'ancienne
  conversation (son journal reste sur le disque). Refusé si Claude est en plein travail, sauf forcer=True.
Sans modèle, sans token, sans dépendance externe.
"""
import ctypes
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ETAT = ROOT / "pilotage" / "etat"
LIMITE = 200_000                 # fenêtre de contexte retenue (jetons)
CONSEIL, ALERTE = 0.60, 0.80     # part de la fenêtre : nouvelle conversation conseillée, puis urgente
REPRISE = ETAT / "reprise_claude.md"   # point de reprise tenu par Claude (facultatif)
CONSIGNE = ("Nouvelle conversation ouverte depuis le tableau de bord. Lis CLAUDE.md, le bandeau, les rôles et tes lignes "
            "en cours dans COORDINATION.md, et pilotage/etat/coordination/claude.md, puis reprends la tâche prioritaire.")


def fichier(agent: str) -> Path:
    return ETAT / f"session_{agent}.json"


# ------------------------------------------------------------------ processus Windows (ctypes, sans psutil)
def processus() -> dict[int, tuple[int, str]]:
    """{pid: (pid parent, nom de l'exécutable en minuscules)} ; vide hors Windows."""
    if os.name != "nt":
        return {}

    class P(ctypes.Structure):
        _fields_ = [("dwSize", ctypes.c_ulong), ("cntUsage", ctypes.c_ulong), ("th32ProcessID", ctypes.c_ulong),
                    ("th32DefaultHeapID", ctypes.c_void_p), ("th32ModuleID", ctypes.c_ulong), ("cntThreads", ctypes.c_ulong),
                    ("th32ParentProcessID", ctypes.c_ulong), ("pcPriClassBase", ctypes.c_long), ("dwFlags", ctypes.c_ulong),
                    ("szExeFile", ctypes.c_wchar * 260)]
    k = ctypes.windll.kernel32
    k.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    h = k.CreateToolhelp32Snapshot(2, 0)
    sortie, e = {}, P()
    e.dwSize = ctypes.sizeof(P)
    try:
        ok = k.Process32FirstW(ctypes.c_void_p(h), ctypes.byref(e))
        while ok:
            sortie[e.th32ProcessID] = (e.th32ParentProcessID, e.szExeFile.lower())
            ok = k.Process32NextW(ctypes.c_void_p(h), ctypes.byref(e))
    finally:
        k.CloseHandle(ctypes.c_void_p(h))
    return sortie


def claude_parent(pid: int, table: dict | None = None) -> tuple[int | None, bool]:
    """Premier ancêtre claude.exe de pid, et vrai s'il a été lancé par Python (session automatique du surveillant)."""
    table = processus() if table is None else table
    vus = set()
    while pid in table and pid not in vus:
        vus.add(pid)
        parent, nom = table[pid]
        if nom == "claude.exe":
            return pid, table.get(parent, (0, ""))[1].startswith("python")
        pid = parent
    return None, False


# ------------------------------------------------------------------ jetons du contexte
def jetons(transcript: str) -> int | None:
    """Taille du contexte au dernier appel du modèle : entrée + cache lu + cache créé (fin du journal seulement)."""
    try:
        with open(transcript, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 400_000))
            lignes = f.read().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for ligne in reversed(lignes):
        if '"usage"' not in ligne:
            continue
        try:
            u = (json.loads(ligne).get("message") or {}).get("usage") or {}
        except ValueError:
            continue
        if "input_tokens" in u:
            return int(u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0))
    return None


def lire(agent: str) -> dict:
    try:
        return json.loads(fichier(agent).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def noter(ev: dict) -> None:
    """Appelé par le crochet de Claude (UserPromptSubmit, SessionStart, Stop)."""
    sid = ev.get("session_id") or ""
    avant = lire("claude")
    if avant.get("session_id") == sid and avant.get("pid"):
        pid, auto = avant["pid"], False
    else:
        pid, auto = claude_parent(os.getppid())
        if auto:
            return                           # session du surveillant : ne remplace pas la conversation du porteur
    n = jetons(ev.get("transcript_path") or "")
    fichier("claude").write_text(json.dumps({
        "session_id": sid, "pid": pid, "transcript": ev.get("transcript_path") or "",
        "jetons": n if n is not None else avant.get("jetons") if avant.get("session_id") == sid else None,
        "au_travail": ev.get("hook_event_name") != "Stop",
        "maj": dt.datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False), encoding="utf-8")


def charge(agent: str) -> dict:
    d = lire(agent)
    n = d.get("jetons")
    if not n:
        return {"connue": False}
    part = n / LIMITE
    niveau = "alerte" if part >= ALERTE else "conseil" if part >= CONSEIL else "ok"
    return {"connue": True, "jetons": n, "pourcent": round(100 * part), "niveau": niveau, "maj": d.get("maj", ""),
            "au_travail": bool(d.get("au_travail")), "fermable": bool(d.get("pid"))}


# ------------------------------------------------------------------ changement de conversation (Claude)
def nouvelle_conversation(exe: Path | None, forcer: bool = False) -> dict:
    if exe is None:
        return {"erreur": "Claude Code introuvable sur ce PC."}
    d = lire("claude")
    if d.get("au_travail") and not forcer:
        return {"erreur": "Claude est en plein travail : attendre la fin de son tour (ou forcer)."}
    ancien = d.get("pid")
    table = processus()
    if ancien and table.get(ancien, (0, ""))[1] != "claude.exe":
        ancien = None                        # déjà fermée, ou identifiant réutilisé par un autre programme
    consigne = CONSIGNE
    if REPRISE.exists():
        consigne += " Point de reprise : pilotage/etat/reprise_claude.md."
    f = ETAT / "consigne_nouvelle_conversation.txt"
    f.write_text(consigne, encoding="utf-8")
    commande = f"& '{exe}' (Get-Content -Raw -Encoding UTF8 '{f}')"
    subprocess.Popen(["powershell.exe", "-NoExit", "-NoProfile", "-Command", commande], cwd=ROOT,
                     creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
    if ancien:
        subprocess.run(["taskkill", "/PID", str(ancien), "/T", "/F"], capture_output=True, check=False,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    fichier("claude").write_text(json.dumps({"maj": dt.datetime.now().isoformat(timespec="seconds")}), encoding="utf-8")
    return {"ok": "Nouvelle conversation Claude ouverte" + (" ; l'ancienne est fermée (son journal est conservé)." if ancien
                                                             else " ; aucune ancienne conversation ouverte à fermer.")}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({a: charge(a) for a in ("claude", "codex")}, ensure_ascii=False))
