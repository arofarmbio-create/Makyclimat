"""Jauge Codex, isolation des conversations et ouverture du projet depuis le tableau."""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pilotage"))
import conversations as C
import serveur_pilotage as S
import tableau_de_bord as T

SID = "00000000-0000-0000-0000-000000000001"
AUTRE = "00000000-0000-0000-0000-000000000002"


class ConversationsCodex(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.etat = self.root / "pilotage" / "etat"
        self.etat.mkdir(parents=True)
        self.home = self.root / "codex"
        self.sessions = self.home / "sessions"
        self.sessions.mkdir(parents=True)
        for target, value in (("ROOT", self.root), ("ETAT", self.etat)):
            mock = patch.object(C, target, value)
            mock.start()
            self.addCleanup(mock.stop)
        mock = patch.dict("os.environ", {"CODEX_HOME": str(self.home), "CODEX_THREAD_ID": SID})
        mock.start()
        self.addCleanup(mock.stop)

    def journal(self, sid=SID, source="vscode", tokens=120_000, limite=400_000):
        path = self.sessions / f"rollout-{sid}.jsonl"
        meta = {"type": "session_meta", "payload": {
            "id": sid, "originator": "Codex Desktop", "source": source, "cwd": str(self.root)}}
        event = {"type": "event_msg", "timestamp": "2026-11-11T08:00:00Z", "payload": {
            "type": "token_count", "info": {"model_context_window": limite,
                "last_token_usage": {"total_tokens": tokens}, "total_token_usage": {"total_tokens": 9_000_000}}}}
        path.write_text(json.dumps(meta) + "\n" + json.dumps(event) + "\n", encoding="utf-8")
        return path

    def test_mesure_du_dernier_appel_et_limite_reelle(self):
        path = self.journal()
        C.noter_codex({"hook_event_name": "UserPromptSubmit"})
        charge = C.charge("codex")
        self.assertEqual((charge["jetons"], charge["limite"], charge["pourcent"]), (120_000, 400_000, 30))
        self.assertFalse(charge["limite_estimee"])
        self.journal(tokens=320_000)
        self.assertEqual(C.charge("codex")["niveau"], "alerte")
        self.journal(tokens=0, limite=800_000)
        with path.open("a", encoding="utf-8") as f:
            f.write('{"type":"event_msg","payload":{"type":"token_count","info":null}}\n')
        self.assertEqual(C.charge("codex")["pourcent"], 0)

    def test_sessions_automatiques_et_anciens_tours_ecartes(self):
        self.journal()
        C.noter_codex({"hook_event_name": "UserPromptSubmit", "session_id": SID})
        for source in ("exec", {"subagent": "review"}):
            self.journal(AUTRE, source=source)
            C.noter_codex({"hook_event_name": "UserPromptSubmit", "session_id": AUTRE})
            self.assertEqual(C.lire("codex")["session_id"], SID)
        path = self.journal(AUTRE)
        lignes = path.read_text(encoding="utf-8").splitlines()
        meta = json.loads(lignes[0])
        del meta["payload"]["cwd"]
        path.write_text(json.dumps(meta) + "\n" + "\n".join(lignes[1:]) + "\n", encoding="utf-8")
        with patch("os.getcwd", return_value=str(self.root)):
            C.noter_codex({"hook_event_name": "UserPromptSubmit", "session_id": AUTRE})
        self.assertEqual(C.lire("codex")["session_id"], SID)
        self.journal(AUTRE)
        C.noter_codex({"hook_event_name": "Stop", "session_id": AUTRE})
        self.assertEqual(C.lire("codex")["session_id"], SID)
        C.noter_codex({"hook_event_name": "UserPromptSubmit", "session_id": AUTRE})
        self.assertEqual(C.lire("codex")["session_id"], AUTRE)
        C.noter_codex({"hook_event_name": "Stop", "session_id": SID})
        self.assertTrue(C.lire("codex")["au_travail"])

    def test_lien_et_entree_api_meme_sans_mesure(self):
        with patch.object(S, "PIL", self.root / "pilotage"):
            d = S.actions()["codex"]
        self.assertEqual(d["charge"], {"connue": False})
        lien = urlparse(d["nouvelle_conversation"])
        self.assertEqual((lien.scheme, lien.netloc, lien.path), ("codex", "threads", "/new"))
        query = parse_qs(lien.query)
        self.assertEqual(query["path"], [str(self.root)])
        self.assertIn("COORDINATION.md", query["prompt"][0])
        self.assertIn("règles de coordination", query["prompt"][0])
        self.assertNotIn("Attends l'accord", query["prompt"][0])

    def test_nouvelle_session_retrouvee_sans_crochet(self):
        ancien = self.journal(tokens=300_000)
        C.noter_codex({"hook_event_name": "UserPromptSubmit"})
        nouveau = self.journal(AUTRE, tokens=20_000)
        for path, date in ((ancien, "2026-11-10T08:00:00Z"), (nouveau, "2026-11-11T08:00:00Z")):
            lignes = path.read_text(encoding="utf-8").splitlines()
            meta = json.loads(lignes[0])
            meta["payload"]["timestamp"] = date
            lignes[0] = json.dumps(meta)
            path.write_text("\n".join(lignes) + "\n", encoding="utf-8")
        self.assertEqual(C.charge("codex")["jetons"], 20_000)
        # Une session automatique plus récente ne remplace pas la conversation.
        lignes = nouveau.read_text(encoding="utf-8").splitlines()
        meta = json.loads(lignes[0])
        meta["payload"]["source"] = "exec"
        lignes[0] = json.dumps(meta)
        nouveau.write_text("\n".join(lignes) + "\n", encoding="utf-8")
        self.assertEqual(C.charge("codex")["jetons"], 300_000)

    def test_claude_mesure_relue_et_journal_manquant(self):
        journal = self.root / "claude.jsonl"
        C.fichier("claude").write_text(json.dumps({
            "transcript": str(journal), "jetons": 190_000, "au_travail": True}), encoding="utf-8")
        charge = C.charge("claude")
        self.assertFalse(charge["connue"])
        self.assertTrue(charge["au_travail"])
        journal.write_text(json.dumps({"message": {"usage": {"input_tokens": 12_000}}}), encoding="utf-8")
        self.assertEqual(C.charge("claude")["jetons"], 12_000)

    def test_nouvelle_fenetre_claude_sans_environnement_enfant(self):
        with patch.object(C, "processus", return_value={}), patch.object(C.subprocess, "Popen") as ouvrir, \
                patch.dict("os.environ", {"CLAUDECODE": "1", "CLAUDE_CODE_CHILD_SESSION": "1", "MAKY_TEST": "ok"}):
            C.nouvelle_conversation(Path("claude.exe"))
        env = ouvrir.call_args.kwargs["env"]
        self.assertNotIn("CLAUDECODE", env)
        self.assertNotIn("CLAUDE_CODE_CHILD_SESSION", env)
        self.assertEqual(env["MAKY_TEST"], "ok")

    def test_javascript_genere_et_bouton_avec_ou_sans_mesure(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node est nécessaire pour vérifier le JavaScript généré.")
        (self.root / "config").mkdir()
        (self.root / "config" / "parcours_pilotage.yml").write_text("parcours: []\n", encoding="utf-8")
        (self.root / "COORDINATION.md").write_text("# Coordination\n", encoding="utf-8")
        with patch.multiple(T, ROOT=self.root, PIL=self.root / "pilotage", lire=lambda _: {},
                            agents=lambda: ([], [], []), github=lambda: [], etudes=lambda: [],
                            run=lambda *args, **kwargs: "", lancements_recents=lambda: ""):
            page = T.page()
        scripts = "\n;\n".join(re.findall(r"<script>(.*?)</script>", page, re.S))
        js = self.root / "page.js"
        js.write_text(scripts, encoding="utf-8")
        check = subprocess.run([node, "--check", str(js)], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)
        fonction = re.search(r"  function afficherActions\(e\).*?(?=  function lireActions)", scripts, re.S).group()
        with patch.object(S, "PIL", self.root / "pilotage"):
            inconnu = S.actions()
            self.journal()
            C.noter_codex({"hook_event_name": "UserPromptSubmit"})
            connu = S.actions()
        js.write_text(
            'const z={innerHTML:"",querySelector:()=>null}; function $(){return z;}\n'
            'function echap(x){return String(x).replaceAll("&","&amp;").replaceAll("\\\"","&quot;");}\n'
            + fonction + "\n" + "\n".join(
                f"afficherActions({json.dumps(e)}); console.log(JSON.stringify(z.innerHTML));" for e in (inconnu, connu)),
            encoding="utf-8")
        check = subprocess.run([node, str(js)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(check.returncode, 0, check.stderr)
        inconnu_html, connu_html = map(json.loads, check.stdout.splitlines())
        self.assertIn("Contexte pas encore mesuré", inconnu_html)
        self.assertIn("Nouvelle conversation (ferme", inconnu_html)
        self.assertIn("30 % du contexte", connu_html)
        self.assertIn("120 k / 400 k", connu_html)
        for resultat in (inconnu_html, connu_html):
            self.assertIn("Nouvelle conversation Codex", resultat)
            self.assertIn("codex://threads/new?", resultat)


if __name__ == "__main__":
    unittest.main()
