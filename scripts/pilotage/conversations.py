"""Charge des conversations des assistants et changement de conversation en un clic (tableau de bord, 11/11/2026).

- Le crochet d'actions de Claude appelle noter() au début et à la fin de chaque tour : identifiant de session, processus
  claude.exe de la conversation interactive (les sessions lancées par le surveillant sont ignorées) et jetons du contexte,
  lus dans le dernier « usage » du journal de la conversation. Résultat : pilotage/etat/session_claude.json.
- Le crochet Codex mémorise la conversation Desktop du projet. Sa jauge lit le dernier token_count du journal local.
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
import tempfile
from pathlib import Path
from urllib.parse import urlencode
from uuid import UUID

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
def fin_journal(transcript: str) -> list[str]:
    try:
        with open(transcript, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 400_000))
            lignes = f.read().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return lignes[::-1]


def jetons(transcript: str) -> int | None:
    """Taille du contexte au dernier appel du modèle : entrée + cache lu + cache créé."""
    for ligne in fin_journal(transcript):
        if '"usage"' not in ligne:
            continue
        try:
            u = (json.loads(ligne).get("message") or {}).get("usage") or {}
        except ValueError:
            continue
        if "input_tokens" in u:
            return int(u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0))
    return None


def mesure_codex(transcript: str) -> dict:
    """Dernier contexte mesuré et fenêtre du modèle, distincts du cumul de consommation."""
    for ligne in fin_journal(transcript):
        try:
            evenement = json.loads(ligne)
        except ValueError:
            continue
        contenu = evenement.get("payload") or {}
        if evenement.get("type") != "event_msg" or contenu.get("type") != "token_count":
            continue
        info = contenu.get("info") or {}
        n = (info.get("last_token_usage") or {}).get("total_tokens")
        limite = info.get("model_context_window")
        if isinstance(n, int) and n >= 0:
            # Ne pas reprendre une ancienne mesure quand la fenêtre est omise.
            # None déclenche le repli LIMITE et son indicateur « estimée » dans charge().
            limite = limite if isinstance(limite, int) and limite > 0 else None
            return {"jetons": n, "limite": limite, "maj": evenement.get("timestamp", "")}
    return {}


def noter_codex(ev: dict) -> None:
    sid = ev.get("session_id") or ev.get("thread_id") or os.environ.get("CODEX_THREAD_ID", "")
    try:
        sid = str(UUID(sid))
    except (ValueError, TypeError, AttributeError):
        return
    avant = lire("codex")
    meme = avant.get("session_id") == sid
    if avant.get("session_id") and not meme and ev.get("hook_event_name") != "UserPromptSubmit":
        return
    sessions = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
    transcript = ev.get("transcript_path") or (avant.get("transcript") if meme else None)
    chemin = Path(transcript) if transcript else next(sessions.rglob(f"*{sid}.jsonl"), None)
    if chemin is None or not chemin.resolve().is_relative_to(sessions.resolve()):
        return
    try:
        with chemin.open(encoding="utf-8") as journal:
            meta = json.loads(journal.readline()).get("payload") or {}
    except (OSError, ValueError):
        return
    if (meta.get("id") != sid or meta.get("originator") != "Codex Desktop"
            or meta.get("source") == "exec" or isinstance(meta.get("source"), dict)
            or not meta.get("cwd") or Path(meta["cwd"]).resolve() != ROOT.resolve()):
        return
    d = {"session_id": sid, "transcript": str(chemin),
         "au_travail": ev.get("hook_event_name") not in ("Stop", "Interrupt")}
    ETAT.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=ETAT, delete=False) as f:
        temporaire = Path(f.name)
        json.dump(d, f, ensure_ascii=False)
    try:
        temporaire.replace(fichier("codex"))
    finally:
        temporaire.unlink(missing_ok=True)


def lien_codex() -> str:
    consigne = ("Reprise MakyClimat. Lis AGENTS.md, les règles, le bandeau et les rôles de COORDINATION.md, "
                "puis pilotage/etat/coordination/codex.md et ton point de reprise pilotage/etat/reprise_codex.md. "
                "Claude pilote, Codex vérifie et améliore. "
                "Vérifie l'état actuel avant de reprendre et suis les règles de coordination.")
    return "codex://threads/new?" + urlencode({"path": str(ROOT), "prompt": consigne})


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
    if agent == "codex":
        d = session_codex_recente(d)
    if agent == "codex" and d.get("transcript"):
        d.update(mesure_codex(d["transcript"]))
    if agent == "claude" and d.get("transcript"):
        # Le journal continue à évoluer entre deux appels du crochet.
        d["jetons"] = jetons(d["transcript"])
    n = d.get("jetons")
    if n is None:
        return {"connue": False, **({"au_travail": bool(d.get("au_travail"))} if d else {})}
    if agent == "claude" and not d.get("limite"):
        # Fenêtre réelle du modèle, écrite par la ligne d'état de la même conversation.
        lc = _lire_json(ETAT / "limites_claude.json")
        if lc.get("fenetre") and lc.get("session_id") == d.get("session_id"):
            d["limite"] = lc["fenetre"]
    limite = d.get("limite") or LIMITE
    part = n / limite
    niveau = "alerte" if part >= ALERTE else "conseil" if part >= CONSEIL else "ok"
    return {"connue": True, "jetons": n, "limite": limite, "limite_estimee": agent == "codex" and not d.get("limite"),
            "pourcent": round(100 * part), "niveau": niveau, "maj": d.get("maj", ""),
            "au_travail": bool(d.get("au_travail")), "fermable": bool(d.get("pid"))}


def _lire_json(chemin: Path) -> dict:
    try:
        d = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def _remise(secondes) -> str:
    if not isinstance(secondes, (int, float)) or isinstance(secondes, bool) or secondes <= 0:
        return ""
    try:
        return dt.datetime.fromtimestamp(secondes).astimezone().isoformat(timespec="minutes")
    except (OSError, OverflowError, ValueError):
        return ""


def limites_codex(transcripts: list[Path] | None = None) -> dict:
    """Limites d'usage de Codex (5 h et semaine) : dernier token_count portant rate_limits.

    Les limites valent pour tout le compte : on prend le journal Codex modifié le plus récemment (aujourd'hui ou hier)."""
    if transcripts is None:
        sessions = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
        transcripts = []
        for jour in (dt.date.today(), dt.date.today() - dt.timedelta(days=1)):
            transcripts.extend((sessions / jour.strftime("%Y/%m/%d")).glob("*.jsonl"))

    def date_modif(p: Path) -> float:
        try:
            return p.stat().st_mtime
        except OSError:
            return 0.0
    for chemin in sorted(transcripts, key=date_modif, reverse=True)[:5]:
        for ligne in fin_journal(str(chemin)):
            if '"rate_limits"' not in ligne:
                continue
            try:
                ev = json.loads(ligne)
            except ValueError:
                continue
            rl = (ev.get("payload") or {}).get("rate_limits") or {}
            sortie = {}
            for cle, nom in (("primary", "cinq_heures"), ("secondary", "semaine")):
                b = rl.get(cle) or {}
                p = b.get("used_percent")
                if isinstance(p, (int, float)) and not isinstance(p, bool):
                    sortie[nom] = {"pourcent": round(p, 1), "remise": _remise(b.get("resets_at")),
                                   "fenetre_min": b.get("window_minutes")}
            if sortie:
                return {**sortie, "maj": ev.get("timestamp", "")}
    return {}


def reprise(agent: str, maintenant: float | None = None) -> dict:
    """Date du point de reprise de l'agent ; « ancien » au-delà de 24 h (à réécrire avant une nouvelle conversation)."""
    chemin = ETAT / f"reprise_{agent}.md"
    try:
        t = chemin.stat().st_mtime
    except OSError:
        return {"present": False}
    age = ((maintenant or dt.datetime.now().timestamp()) - t) / 3600
    return {"present": True, "maj": dt.datetime.fromtimestamp(t).strftime("%d/%m %H:%M"), "ancien": age > 24}


SEUIL_LIMITE = 80          # % d'une limite d'usage : alerte sur le poste


def limites(agent: str) -> dict:
    """Limites d'usage de 5 h et de la semaine, avec niveau d'alerte, pour le poste de pilotage."""
    if agent == "claude":
        d = _lire_json(ETAT / "limites_claude.json")
        d = {k: d[k] for k in ("cinq_heures", "semaine") if isinstance(d.get(k), dict)
             and d[k].get("pourcent") is not None} | ({"maj": d.get("maj", "")} if d else {})
    else:
        d = limites_codex()
    maintenant = dt.datetime.now().astimezone()
    for k in ("cinq_heures", "semaine"):
        if k not in d:
            continue
        try:
            passee = bool(d[k].get("remise")) and dt.datetime.fromisoformat(d[k]["remise"]) <= maintenant
        except ValueError:
            passee = False
        if passee:                     # fenêtre écoulée depuis la mesure : compteur remis à zéro
            d[k].update(pourcent=0, remise="", perimee=True)
        d[k]["alerte"] = d[k]["pourcent"] >= SEUIL_LIMITE
    return d


def session_codex_recente(avant: dict) -> dict:
    """Retrouve une nouvelle conversation Desktop même si son crochet n'a pas tourné.

    Ne lit que les métadonnées des journaux récents : aucune session automatique
    ni conversation d'un autre projet ne peut alimenter cette jauge.
    """
    sessions = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
    candidats = list(sessions.glob("*.jsonl"))
    for jour in (dt.date.today(), dt.date.today() - dt.timedelta(days=1)):
        candidats.extend((sessions / jour.strftime("%Y/%m/%d")).glob("*.jsonl"))
    if avant.get("transcript"):
        candidats.append(Path(avant["transcript"]))
    meilleur, ordre = avant, ""
    for chemin in set(candidats):
        try:
            if not chemin.resolve().is_relative_to(sessions.resolve()):
                continue
            with chemin.open(encoding="utf-8") as f:
                meta = json.loads(f.readline()).get("payload") or {}
            if (meta.get("originator") != "Codex Desktop" or meta.get("source") != "vscode"
                    or meta.get("thread_source", "user") != "user"
                    or not meta.get("cwd") or Path(meta["cwd"]).resolve() != ROOT.resolve()):
                continue
            sid = str(UUID(meta.get("id", "")))
            date = meta.get("timestamp") or dt.datetime.fromtimestamp(
                chemin.stat().st_mtime, dt.timezone.utc).isoformat()
        except (OSError, ValueError, TypeError, AttributeError):
            continue
        if date > ordre:
            ordre = date
            meilleur = avant if sid == avant.get("session_id") else {
                "session_id": sid, "transcript": str(chemin)}
    return meilleur


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
    # cmd plutôt que PowerShell : la fenêtre PowerShell de la session mère s'est figée le 11/11/2026 (porteur).
    # La consigne (une ligne, sans guillemet droit) est lue par « set /p » depuis son fichier, jamais dans la commande.
    lanceur = ETAT / "lancer_nouvelle_conversation.cmd"
    lanceur.write_text("@echo off\r\nchcp 65001 >nul\r\n"
                       f"set /p CONSIGNE=<\"{f}\"\r\n\"{exe}\" \"%CONSIGNE%\"\r\n", encoding="utf-8")
    subprocess.Popen(["cmd.exe", "/k", str(lanceur)], cwd=ROOT,
                     env={k: v for k, v in os.environ.items()
                          if k.upper() != "CLAUDECODE" and not k.upper().startswith("CLAUDE_CODE_")},
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
