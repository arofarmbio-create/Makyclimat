"""Tests du suivi de charge des conversations et du changement de conversation (scripts/pilotage/conversations.py)."""
import json
import sys
import tempfile
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pilotage"))
import conversations as C  # noqa: E402


def avec_etat(fonction):
    def enveloppe():
        ancien = C.ETAT
        with tempfile.TemporaryDirectory() as d:
            C.ETAT = Path(d)
            try:
                with patch.dict("os.environ", {"CODEX_HOME": str(Path(d) / "codex")}):
                    fonction(Path(d))
            finally:
                C.ETAT = ancien
    enveloppe.__name__ = fonction.__name__
    return enveloppe


def test_jetons_du_dernier_usage():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "t.jsonl"
        lignes = [{"message": {"usage": {"input_tokens": 1, "cache_read_input_tokens": 10}}},
                  {"type": "user", "message": {"content": "x"}},
                  {"message": {"usage": {"input_tokens": 2, "cache_read_input_tokens": 100, "cache_creation_input_tokens": 30}}},
                  {"type": "user", "message": {"content": "\"usage\" dans un texte"}}]
        f.write_text("\n".join(json.dumps(l) for l in lignes), encoding="utf-8")
        assert C.jetons(str(f)) == 132
        assert C.jetons(str(Path(d) / "absent.jsonl")) is None


def test_session_automatique_reconnue():
    table = {10: (5, "python.exe"), 11: (10, "claude.exe"), 12: (11, "bash.exe"), 13: (12, "python.exe"),
             20: (1, "windowsterminal.exe"), 21: (20, "claude.exe"), 22: (21, "python.exe")}
    assert C.claude_parent(13, table) == (11, True)       # claude -p lancé par le surveillant
    assert C.claude_parent(22, table) == (21, False)      # conversation interactive du porteur
    assert C.claude_parent(99, table) == (None, False)


@avec_etat
def test_niveaux_de_charge(d):
    for n, niveau in ((50_000, "ok"), (130_000, "conseil"), (170_000, "alerte")):
        C.fichier("claude").write_text(json.dumps({"jetons": n, "pid": 1}), encoding="utf-8")
        assert C.charge("claude")["niveau"] == niveau
    assert C.charge("codex") == {"connue": False}


@avec_etat
def test_fenetre_reprise_d_une_autre_session(d):
    # Ouverture d'une conversation : la ligne d'état porte encore l'ancienne session (cas « 131 % » du 11/11).
    (d / "limites_claude.json").write_text(json.dumps({"session_id": "ancienne", "fenetre": 1_000_000}), encoding="utf-8")
    C.fichier("claude").write_text(json.dumps({"session_id": "neuve", "jetons": 262_000, "pid": 1}), encoding="utf-8")
    c = C.charge("claude")
    assert (c["limite"], c["pourcent"], c["niveau"], c["limite_estimee"]) == (1_000_000, 26, "ok", True)
    (d / "limites_claude.json").write_text(json.dumps({"session_id": "neuve", "fenetre": 1_000_000}), encoding="utf-8")
    assert C.charge("claude")["limite_estimee"] is False


@avec_etat
def test_refus_si_claude_travaille(d):
    C.fichier("claude").write_text(json.dumps({"au_travail": True, "pid": 1}), encoding="utf-8")
    r = C.nouvelle_conversation(Path("claude.exe"))
    assert "erreur" in r and not (d / "consigne_nouvelle_conversation.txt").exists()
    assert "erreur" in C.nouvelle_conversation(None, forcer=True)


class _Horloge:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def dormir(self, s):
        self.t += s


def test_attente_du_nouveau_claude():
    """Relecture Codex (11/11, 19:17 et 19:32) : le nouveau Claude doit tourner avant de fermer l'ancien."""
    h = _Horloge()
    tables = iter([{50: (1, "cmd.exe")}] * 2 + [{50: (1, "cmd.exe"), 51: (50, "claude.exe")}] * 20)
    with patch.object(C, "processus", lambda: next(tables)):
        assert C.attendre_claude(50, sommeil=h.dormir, horloge=h) == 51
    h = _Horloge()
    tables = iter([{50: (1, "cmd.exe"), 51: (50, "claude.exe")}] * 2 + [{50: (1, "cmd.exe")}] * 200)
    with patch.object(C, "processus", lambda: next(tables)):
        assert C.attendre_claude(50, sommeil=h.dormir, horloge=h) is None    # Claude apparu puis tombé
    h = _Horloge()
    with patch.object(C, "processus", lambda: {}):
        assert C.attendre_claude(50, sommeil=h.dormir, horloge=h) is None    # console fermée


@avec_etat
def test_ancien_claude_conserve_si_le_nouveau_ne_demarre_pas(d):
    C.fichier("claude").write_text(json.dumps({"pid": 77}), encoding="utf-8")
    tues = []

    class Console:
        pid = 50

    with patch.object(C, "processus", lambda: {77: (1, "claude.exe")}), \
            patch.object(C.subprocess, "Popen", lambda *a, **k: Console()), \
            patch.object(C, "attendre_claude", lambda pid: None), \
            patch.object(C.subprocess, "run", lambda commande, **k: tues.append(commande)):
        r = C.nouvelle_conversation(Path("claude.exe"))
        assert "erreur" in r and tues == []
        with patch.object(C, "attendre_claude", lambda pid: 51):
            r = C.nouvelle_conversation(Path("claude.exe"))
        assert "ok" in r and tues and tues[0][:3] == ["taskkill", "/PID", "77"]


@avec_etat
def test_etat_de_la_nouvelle_session_preserve(d):
    """Relecture Codex (11/11, 21:00) : l'état écrit par la nouvelle session pendant l'attente n'est pas écrasé ;
    celui de l'ancienne session est remis à zéro."""
    ancien = {"session_id": "ancienne", "pid": 77, "au_travail": False}
    nouveau = {"session_id": "nouvelle", "pid": 51, "au_travail": True, "transcript": "t.jsonl"}

    class Console:
        pid = 50

    def demarre(pid):
        C.fichier("claude").write_text(json.dumps(nouveau), encoding="utf-8")    # crochet de la nouvelle session
        return 51

    with patch.object(C, "processus", lambda: {77: (1, "claude.exe")}),             patch.object(C.subprocess, "Popen", lambda *a, **k: Console()),             patch.object(C.subprocess, "run", lambda commande, **k: None):
        C.fichier("claude").write_text(json.dumps(ancien), encoding="utf-8")
        with patch.object(C, "attendre_claude", demarre):
            assert "ok" in C.nouvelle_conversation(Path("claude.exe"))
        assert C.lire("claude") == nouveau
        C.fichier("claude").write_text(json.dumps(ancien), encoding="utf-8")
        with patch.object(C, "attendre_claude", lambda pid: 51):                # la nouvelle n'a rien écrit
            assert "ok" in C.nouvelle_conversation(Path("claude.exe"))
        assert set(C.lire("claude")) == {"maj"}


@avec_etat
def test_crochet_entrelace_avec_l_effacement(d):
    """Relecture Codex (12/11, 13:10) : le crochet de la nouvelle session qui écrit entre la lecture et l'effacement
    attend le verrou ; son état est écrit après l'effacement et n'est donc pas perdu."""
    import threading
    ancien = {"session_id": "ancienne", "pid": 77, "au_travail": False}
    C.fichier("claude").write_text(json.dumps(ancien), encoding="utf-8")
    lire_vrai, fil = C.lire, {}

    class Console:
        pid = 50

    def lire_entrelace(agent):
        etat = lire_vrai(agent)
        if threading.current_thread() is threading.main_thread():
            fil["lectures"] = fil.get("lectures", 0) + 1
        if fil.get("lectures") == 2 and "crochet" not in fil:     # 2e lecture : juste avant l'effacement
            fil["crochet"] = threading.Thread(target=C.noter, args=(
                {"session_id": "nouvelle", "hook_event_name": "UserPromptSubmit", "transcript_path": ""},))
            fil["crochet"].start()
            fil["crochet"].join(0.3)
            fil["bloque"] = fil["crochet"].is_alive()  # le crochet attend le verrou
        return etat

    with patch.object(C, "processus", lambda: {77: (1, "claude.exe")}),             patch.object(C.subprocess, "Popen", lambda *a, **k: Console()),             patch.object(C.subprocess, "run", lambda commande, **k: None),             patch.object(C, "attendre_claude", lambda pid: 51),             patch.object(C, "claude_parent", lambda pid: (51, False)),             patch.object(C, "jetons", lambda chemin: None),             patch.object(C, "lire", lire_entrelace):
        assert "ok" in C.nouvelle_conversation(Path("claude.exe"))
        fil["crochet"].join(5)
    etat = lire_vrai("claude")
    assert fil["bloque"] and etat["session_id"] == "nouvelle" and etat["pid"] == 51, (fil, etat)
    assert not (d / "session_claude.verrou").exists()


def test_verrou_perime_repris(tmp=None):
    """Un verrou laissé par un processus tué est repris après VERROU_PERIME secondes."""
    import os
    dossier = Path(tempfile.mkdtemp())
    with patch.object(C, "ETAT", dossier):
        v = dossier / "session_claude.verrou"
        v.write_text("")
        os.utime(v, (0, 0))
        with C.verrou_etat("claude") as verrou:
            assert verrou.tenu
        assert not v.exists()


def test_javascript_du_tableau_valide():
    """Une erreur de syntaxe JS bloque toute la page (11/11/2026 : apostrophe non protégée)."""
    import re, shutil, subprocess
    node = shutil.which("node")
    if not node:
        return
    f = Path(__file__).resolve().parents[1] / "pilotage" / "tableau_de_bord.html"   # page générée (locale)
    if not f.exists():
        return
    html = f.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as d:
        js = Path(d) / "page.js"
        js.write_text("\n;\n".join(re.findall(r"<script>(.*?)</script>", html, re.S)), encoding="utf-8")
        r = subprocess.run([node, "--check", str(js)], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[:500]


def test_scripts_de_pilotage_compilent():
    """Un crochet qui ne compile pas échoue en silence (11/11/2026 : chaîne coupée dans hook_alertes_claude.py)."""
    import py_compile
    dossier = Path(__file__).resolve().parents[1] / "scripts" / "pilotage"
    for script in sorted(dossier.glob("*.py")):
        py_compile.compile(str(script), doraise=True)


if __name__ == "__main__":
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f()
    print("OK : suivi des conversations")
