"""Tests du suivi de charge des conversations et du changement de conversation (scripts/pilotage/conversations.py)."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pilotage"))
import conversations as C  # noqa: E402


def avec_etat(fonction):
    def enveloppe():
        ancien = C.ETAT
        with tempfile.TemporaryDirectory() as d:
            C.ETAT = Path(d)
            try:
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
def test_refus_si_claude_travaille(d):
    C.fichier("claude").write_text(json.dumps({"au_travail": True, "pid": 1}), encoding="utf-8")
    r = C.nouvelle_conversation(Path("claude.exe"))
    assert "erreur" in r and not (d / "consigne_nouvelle_conversation.txt").exists()
    assert "erreur" in C.nouvelle_conversation(None, forcer=True)


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
