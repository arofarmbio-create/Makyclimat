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


class _SansVerrou:
    """Variante témoin : verrou toujours accordé, sans exclusion."""
    def __init__(self, *a, **k):
        self.tenu = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _entrelacement(d, classe_verrou):
    """Le crochet de la nouvelle session est lancé juste avant l'effacement (2e lecture du changement de conversation).
    Synchronisation explicite : on ne reprend l'effacement qu'après une tentative refusée du crochet sur le verrou,
    ou après la fin du crochet s'il n'a pas eu à attendre (variante sans verrou)."""
    import threading
    C.fichier("claude").write_text(json.dumps({"session_id": "ancienne", "pid": 77}), encoding="utf-8")
    lire_vrai, prendre_vrai, fil = C.lire, C.verrou_etat._prendre, {"lectures": 0}
    refuse = threading.Event()

    def prendre(fd):
        ok = prendre_vrai(fd)
        if not ok and threading.current_thread() is not threading.main_thread():
            refuse.set()
        return ok

    def lire_entrelace(agent):
        etat = lire_vrai(agent)
        if threading.current_thread() is threading.main_thread():
            fil["lectures"] += 1
            if fil["lectures"] == 2:
                fil["crochet"] = threading.Thread(target=C.noter, args=(
                    {"session_id": "nouvelle", "hook_event_name": "UserPromptSubmit", "transcript_path": ""},))
                fil["crochet"].start()
                while not refuse.is_set() and fil["crochet"].is_alive():
                    refuse.wait(0.01)
                fil["refuse"] = refuse.is_set()
        return etat

    class Console:
        pid = 50

    with patch.object(C, "processus", lambda: {77: (1, "claude.exe")}),             patch.object(C.subprocess, "Popen", lambda *a, **k: Console()),             patch.object(C.subprocess, "run", lambda commande, **k: None),             patch.object(C, "attendre_claude", lambda pid: 51),             patch.object(C, "claude_parent", lambda pid: (51, False)),             patch.object(C, "jetons", lambda chemin: None),             patch.object(C.verrou_etat, "_prendre", staticmethod(prendre)),             patch.object(C, "verrou_etat", classe_verrou),             patch.object(C, "lire", lire_entrelace):
        assert "ok" in C.nouvelle_conversation(Path("claude.exe"))
        fil["crochet"].join(10)
    return fil, lire_vrai("claude")


@avec_etat
def test_crochet_entrelace_avec_l_effacement(d):
    """Relectures Codex (12/11, 13:10 et 14:29) : le crochet qui écrit entre la lecture et l'effacement attend le
    verrou ; son état est écrit après l'effacement et n'est pas perdu. Sans verrou, il est perdu (témoin)."""
    fil, etat = _entrelacement(d, C.verrou_etat)
    assert fil["refuse"] and etat.get("session_id") == "nouvelle" and etat.get("pid") == 51, (fil, etat)
    fil, etat = _entrelacement(d, _SansVerrou)
    assert not fil["refuse"] and "session_id" not in etat, (fil, etat)       # la course existe bien sans verrou


@avec_etat
def test_sans_verrou_l_operation_est_abandonnee(d):
    """Relecture Codex (12/11, 14:29) : verrou non obtenu dans le délai → ni le crochet ni l'effacement n'écrivent."""
    ancien = {"session_id": "ancienne", "pid": 77}
    C.fichier("claude").write_text(json.dumps(ancien), encoding="utf-8")
    with C.verrou_etat("claude") as tenu:
        assert tenu.tenu
        with patch.object(C, "VERROU_DELAI", 0.1), patch.object(C, "claude_parent", lambda pid: (51, False)):
            with C.verrou_etat("claude") as second:
                assert not second.tenu
            C.noter({"session_id": "nouvelle", "hook_event_name": "UserPromptSubmit", "transcript_path": ""})
    assert C.lire("claude") == ancien


@avec_etat
def test_verrou_libere_a_la_mort_du_proprietaire(d):
    """Relecture Codex (12/11, 14:29) : pas de reprise à l'ancienneté ; le système libère le verrou d'un processus tué,
    et seulement à ce moment."""
    import subprocess
    code = ("import sys, time; sys.path.insert(0, sys.argv[1]); import conversations as C; from pathlib import Path; "
            "C.ETAT = Path(sys.argv[2]); v = C.verrou_etat('claude').__enter__(); print(v.tenu, flush=True); "
            "time.sleep(60)")
    p = subprocess.Popen([sys.executable, "-c", code, str(Path(C.__file__).parent), str(d)], stdout=subprocess.PIPE,
                         text=True)
    try:
        assert p.stdout.readline().strip() == "True"
        with C.verrou_etat("claude", delai=0.2) as v:
            assert not v.tenu                    # propriétaire vivant : jamais retiré
    finally:
        p.kill()
        p.wait()
    with C.verrou_etat("claude", delai=2) as v:
        assert v.tenu                            # propriétaire tué : libéré par le système


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
