"""Poste de pilotage (11/11/2026) : sessions enfants visibles et plafonnées, arrêt, messagerie porteur ↔ sessions mères,
remise des messages par les crochets et JavaScript de la page. Sans réseau, sans lancer Claude ni Codex."""
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "scripts" / "pilotage"))
import hook_alertes_claude as H  # noqa: E402
import poste as P  # noqa: E402
import surveiller_coordination as C  # noqa: E402

TABLE = "CREATE TABLE lancements (id TEXT PRIMARY KEY, debut TEXT, fin TEXT, statut TEXT NOT NULL, consommation TEXT)"


class Sujet(unittest.TestCase):
    def test_sujet_lisible_par_genre(self):
        self.assertEqual(C.sujet_lancement("codex/relecture-ab", "Relecture automatique de la tâche « R-21 — Méthode » (x)"),
                         "R-21 — Méthode")
        self.assertEqual(C.sujet_lancement("claude/exec-1", "Consigne du porteur du projet : faire **X**"), "faire X")
        self.assertEqual(C.sujet_lancement("codex/reveil-1", "Réponds." + C.SAUT + "**Claude → Codex · Sujet.** détail"),
                         "Claude → Codex · Sujet. détail")
        self.assertEqual(C.genre_lancement("relecture-x"), "relecture")
        self.assertEqual(C.genre_lancement("r21-x"), "ponctuel")


class Plafond(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute(TABLE)
        C.colonnes_lancements(self.db)

    def ajouter(self, ident, sujet="S", jour="11/11/2026"):
        self.db.execute("INSERT INTO lancements (id, debut, statut, sujet) VALUES (?, ?, 'Réponse reçue', ?)",
                        (ident, f"{jour} 10:00", sujet))

    def test_plafond_journalier_par_agent(self):
        for i in range(C.PLAFOND_JOUR["reveil"]):
            self.ajouter(f"codex/reveil-{i}", f"s{i}")
        self.assertTrue(C.au_plafond(self.db, "codex", "codex/reveil-z", "autre", "11/11/2026"))
        self.assertFalse(C.au_plafond(self.db, "codex", "codex/reveil-z", "autre", "12/11/2026"))   # nouveau jour
        self.assertFalse(C.au_plafond(self.db, "claude", "relecture-z", "autre", "11/11/2026"))     # autre agent

    def test_relectures_d_une_meme_tache(self):
        for i in range(C.RELECTURES_TACHE_JOUR):
            self.ajouter(f"relecture-{i}", "Tâche A")
        self.assertTrue(C.au_plafond(self.db, "claude", "relecture-n", "Tâche A", "11/11/2026"))
        self.assertFalse(C.au_plafond(self.db, "claude", "relecture-n", "Tâche B", "11/11/2026"))
        self.assertFalse(C.au_plafond(self.db, "codex", "codex/relecture-n", "Tâche A", "11/11/2026"))

    def test_remise_a_zero_par_le_porteur(self):
        """Porteur, 11/11/2026 : effacer les plafonds pour travailler même plafond atteint, Claude ou Codex."""
        for i in range(C.PLAFOND_JOUR["reveil"]):
            self.ajouter(f"codex/reveil-{i}", f"s{i}")
        for i in range(C.RELECTURES_TACHE_JOUR):
            self.ajouter(f"relecture-{i}", "Tâche A")
        self.assertTrue(C.au_plafond(self.db, "codex", "codex/reveil-z", "autre", "11/11/2026"))
        C.effacer_plafonds(self.db, "codex", "11/11/2026 11:00")
        self.assertFalse(C.au_plafond(self.db, "codex", "codex/reveil-z", "autre", "11/11/2026"))
        self.assertTrue(C.au_plafond(self.db, "claude", "relecture-n", "Tâche A", "11/11/2026"))  # Claude non touché
        C.effacer_plafonds(self.db, "claude", "11/11/2026 11:00")
        self.assertFalse(C.au_plafond(self.db, "claude", "relecture-n", "Tâche A", "11/11/2026"))
        for i in range(C.PLAFOND_JOUR["reveil"]):                    # le décompte repart après la remise
            self.ajouter(f"codex/reveil-apres-{i}", f"t{i}")
            self.db.execute("UPDATE lancements SET debut = '11/11/2026 12:00' WHERE id = ?", (f"codex/reveil-apres-{i}",))
        self.assertTrue(C.au_plafond(self.db, "codex", "codex/reveil-z", "autre", "11/11/2026"))
        C.effacer_plafonds(self.db, "codex", "10/11/2026 23:00")    # une remise de la veille ne vaut pas aujourd'hui
        self.assertTrue(C.au_plafond(self.db, "codex", "codex/reveil-z", "autre", "11/11/2026"))

    def test_remise_dans_la_minute_des_lancements(self):
        """Avis Codex (11/11, 19:17) : des lancements de la minute de la remise, juste avant, ne comptent plus."""
        for i in range(C.PLAFOND_JOUR["reveil"]):
            self.ajouter(f"codex/reveil-{i}", f"s{i}")               # tous à 10:00
        C.effacer_plafonds(self.db, "codex", "11/11/2026 10:00:30")
        self.assertFalse(C.au_plafond(self.db, "codex", "codex/reveil-z", "autre", "11/11/2026"))
        self.assertEqual(C.lancements_comptes(self.db, "codex", "reveil", "11/11/2026"), 0)
        self.assertEqual(C.lancements_comptes(self.db, "codex", "reveil", "12/11/2026"), 0)
        self.ajouter("codex/reveil-apres", "x")                          # après la remise, même minute (10:00)
        self.assertEqual(C.lancements_comptes(self.db, "codex", "reveil", "11/11/2026"), 1)   # avis Codex 19:36

    def test_ancienne_table_de_remise_sans_seuil(self):
        """Une table créée par la version précédente (sans colonne seuil) est complétée à la remise suivante."""
        self.db.execute("CREATE TABLE remises_plafond (agent TEXT PRIMARY KEY, depuis TEXT NOT NULL)")
        self.db.execute("INSERT INTO remises_plafond VALUES ('codex', '11/11/2026 19:12')")
        self.ajouter("codex/reveil-0")
        self.assertEqual(C.lancements_comptes(self.db, "codex", "reveil", "11/11/2026"), 1)
        C.effacer_plafonds(self.db, "codex", "11/11/2026 19:40:00")
        self.assertEqual(C.lancements_comptes(self.db, "codex", "reveil", "11/11/2026"), 0)

    def test_execution_autorisee_jamais_plafonnee(self):
        for i in range(50):
            self.ajouter(f"claude/exec-{i}")
        self.assertFalse(C.au_plafond(self.db, "claude", "claude/exec-x", "S", "11/11/2026"))


class Lancement(unittest.TestCase):
    def test_sujet_consigne_enregistres_et_arret_conserve(self):
        with tempfile.TemporaryDirectory() as t:
            dossier = Path(t)
            db = sqlite3.connect(dossier / "c.sqlite3")
            db.execute(TABLE)
            db.execute("CREATE TABLE alertes (id TEXT PRIMARY KEY, date TEXT, cibles TEXT, message TEXT)")

            def faux(commande, *, input, **options):
                # Pendant la session, le porteur l'arrête depuis le poste.
                autre = sqlite3.connect(dossier / "c.sqlite3")      # « with » ne ferme pas : fichier verrouillé sous Windows
                with autre:
                    autre.execute("UPDATE lancements SET statut = ? WHERE statut = 'En cours'", (C.ARRETE,))
                autre.close()
                return subprocess.CompletedProcess(commande, 1, stdout="", stderr="tué")

            with patch.object(C.subprocess, "run", side_effect=faux):
                C.lancer_claude(db, dossier, [("claude", "claude/exec-1", "Consigne du porteur du projet : tester")],
                                {"claude": "claude.exe"})
            ligne = db.execute("SELECT statut, agent, genre, sujet, consigne FROM lancements").fetchone()
            self.assertEqual(ligne[:4], (C.ARRETE, "claude", "exec", "tester"))
            self.assertIn("tester", ligne[4])
            self.assertIn("arrêtée depuis le poste", (dossier / "claude-exec-1.md").read_text(encoding="utf-8"))
            db.close()


class Messagerie(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = patch.object(P, "MESSAGES", self.t / "m.jsonl")
        self.p.start()

    def tearDown(self):
        self.p.stop()
        shutil.rmtree(self.t, ignore_errors=True)

    def test_envoi_remise_reponse(self):
        self.assertIn("erreur", P.envoyer("autre", "x"))
        self.assertIn("erreur", P.envoyer("claude", "   "))
        ident = P.envoyer("claude", "Bonjour  Claude")["id"]
        self.assertEqual([m["texte"] for m in P.a_remettre("claude")], ["Bonjour Claude"])
        self.assertEqual(P.a_remettre("codex"), [])
        self.assertEqual(P.fil()[0]["etat"], "en attente de remise")
        P.marquer_remis("claude", [ident])
        self.assertEqual(P.a_remettre("claude"), [])
        self.assertEqual(P.fil()[0]["etat"], "remis")
        P.repondre("claude", ident, "Bien reçu")
        f = P.fil()
        self.assertEqual((f[0]["de"], f[0]["texte"]), ("claude", "Bien reçu"))
        self.assertEqual(f[1]["etat"], "répondu")

    def test_crochet_remet_seulement_a_la_session_mere(self):
        P.envoyer("claude", "Pour la mère")
        with patch.object(H, "lire_session", return_value="mere"):
            self.assertEqual(H.messages_porteur("enfant"), "")          # session enfant : rien, rien de marqué
            self.assertEqual(len(P.a_remettre("claude")), 1)
            texte = H.messages_porteur("mere")
            self.assertIn("Pour la mère", texte)
            self.assertIn("poste.py repondre claude", texte)
            self.assertEqual(H.messages_porteur("mere"), "")            # une seule remise


class Instantane(unittest.TestCase):
    def test_enfants_et_consommation(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t) / "c.sqlite3"
            with sqlite3.connect(base) as db:
                db.execute(TABLE)
                C.colonnes_lancements(db)
                db.execute("INSERT INTO lancements VALUES ('codex/relecture-a', '11/11/2026 10:00', '11/11/2026 10:03', "
                           "'Réponse reçue', 'entrée 1 000 (dont cache 800) · sortie 50', 'codex', 'relecture', 'T', 'c')")
                db.execute("INSERT INTO lancements (id, debut, statut, consommation) VALUES ('claude/exec-b', "
                           "'11/11/2026 11:00', 'En cours', 'entrée 2 000 (dont cache 0) · sortie 10 · 0.50 $')")
            db.close()
            with patch.object(P, "BASE", base):
                liste = P.enfants(jour="11/11/2026")
                conso = P.consommation(liste)
                plafonds = P.plafonds(conso, jour="11/11/2026")
                self.assertIn("ok", P.effacer_plafonds("codex"))       # remise du jour réel : sans effet le 11/11
                self.assertIn("erreur", P.effacer_plafonds("autre"))
            self.assertEqual([e["agent"] for e in liste], ["claude", "codex"])
            self.assertEqual(liste[1]["duree_min"], 3)
            self.assertEqual(liste[1]["jetons"], {"entree": 1000, "cache": 800, "sortie": 50, "cout": None})
            self.assertEqual((conso["codex"]["sessions"], conso["claude"]["cout"]), (1, 0.5))
            self.assertEqual(plafonds["codex"]["relecture"]["utilise"], 1)

    def test_detail_refuse_un_chemin(self):
        self.assertIn("erreur", P.detail("../../secret"))
        self.assertIn("erreur", P.detail("codex/../x"))


class Page(unittest.TestCase):
    def test_javascript_valide(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node est nécessaire pour vérifier le JavaScript de la page.")
        html = (RACINE / "scripts" / "pilotage" / "poste.html").read_text(encoding="utf-8")
        script = html.split("<script>", 1)[1].split("</script>", 1)[0]
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "poste.js"
            f.write_text(script, encoding="utf-8")
            r = subprocess.run([node, "--check", str(f)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)




import conversations as V  # noqa: E402
import ligne_etat_claude as L  # noqa: E402


class Limites(unittest.TestCase):
    """Limites d'usage (11/11/2026) : ligne d'état de Claude, journal de Codex, garde du surveillant."""

    def test_ligne_etat_lit_le_json_reel(self):
        ev = {"session_id": "s", "model": {"display_name": "Opus"},
              "context_window": {"context_window_size": 1_000_000, "used_percentage": 9},
              "rate_limits": {"five_hour": {"used_percentage": 19, "resets_at": 1794423000},
                              "seven_day": {"used_percentage": 61, "resets_at": 1794682800}}}
        d = L.extraire(ev)
        self.assertEqual((d["fenetre"], d["cinq_heures"]["pourcent"], d["semaine"]["pourcent"]), (1_000_000, 19, 61))
        self.assertTrue(d["cinq_heures"]["remise"].startswith("2026-11-"))
        self.assertIn("5 h 19 %", L.ligne(d))
        vide = L.extraire({})                       # champs absents : rien ne casse
        self.assertIsNone(vide["fenetre"])
        self.assertEqual(L.ligne(vide), "MakyClimat")

    def test_codex_dernier_token_count_et_fenetre_ecoulee(self):
        futur = int(__import__("time").time()) + 3600
        with tempfile.TemporaryDirectory() as t:
            j = Path(t) / "rollout.jsonl"
            evs = [{"timestamp": "T", "type": "event_msg", "payload": {"type": "token_count", "rate_limits": {
                "primary": {"used_percent": 95.0, "window_minutes": 300, "resets_at": futur},
                "secondary": {"used_percent": 29.0, "window_minutes": 10080, "resets_at": futur - 7 * 86400}}}}]
            j.write_text("\n".join(json.dumps(e) for e in evs), encoding="utf-8")
            brut = V.limites_codex([j])
            self.assertEqual(brut["cinq_heures"]["pourcent"], 95.0)
            with patch.object(V, "limites_codex", return_value=brut):
                d = V.limites("codex")
        self.assertTrue(d["cinq_heures"]["alerte"])
        self.assertEqual(d["semaine"]["pourcent"], 0)       # remise à zéro passée depuis la mesure
        self.assertTrue(d["semaine"]["perimee"])

    def test_jauge_claude_prend_la_fenetre_reelle(self):
        with tempfile.TemporaryDirectory() as t:
            etat = Path(t)
            (etat / "session_claude.json").write_text(json.dumps({"session_id": "s", "jetons": 100_000}), encoding="utf-8")
            (etat / "limites_claude.json").write_text(json.dumps({"session_id": "s", "fenetre": 1_000_000}), encoding="utf-8")
            with patch.object(V, "ETAT", etat):
                self.assertEqual((V.charge("claude")["limite"], V.charge("claude")["pourcent"]), (1_000_000, 10))
                (etat / "limites_claude.json").write_text(json.dumps({"session_id": "autre", "fenetre": 1_000_000}),
                                                          encoding="utf-8")
                self.assertEqual(V.charge("claude")["limite"], V.LIMITE)

    def lancer(self, ident, atteinte=True):
        with tempfile.TemporaryDirectory() as t:
            db = sqlite3.connect(":memory:")
            db.execute(TABLE)
            db.execute("CREATE TABLE alertes (id TEXT PRIMARY KEY, date TEXT, cibles TEXT, message TEXT)")
            fini = subprocess.CompletedProcess([], 0, stdout="", stderr="")
            with patch.object(C, "limite_atteinte", return_value=atteinte), \
                    patch.object(C.subprocess, "run", return_value=fini) as run:
                C.lancer_claude(db, Path(t), [("codex", ident, "Relecture automatique « X »")], {"codex": "codex.exe"})
            return run.called

    def test_suspension_a_90_pour_cent(self):
        self.assertFalse(self.lancer("codex/relecture-1"))          # automatique : suspendu
        self.assertTrue(self.lancer("codex/exec-1"))                # exécution autorisée par le porteur : maintenue
        self.assertTrue(self.lancer("codex/relecture-2", atteinte=False))

    def test_reseau_coupe_aucun_lancement(self):
        with tempfile.TemporaryDirectory() as t:
            dossier = Path(t)
            source = dossier / "COORDINATION.md"
            source.write_text("# Coordination\n", encoding="utf-8")
            with patch.object(C.socket, "create_connection", side_effect=OSError), \
                    patch.object(C, "lancer_claude") as lancer:
                C.verifier(source, dossier / "etat", codex="codex.exe")
            self.assertFalse(lancer.called)
            self.assertTrue(json.loads((dossier / "etat" / "reseau.json").read_text(encoding="utf-8"))["coupe"])


    def test_point_de_reprise_a_jour_ou_ancien(self):
        with tempfile.TemporaryDirectory() as t, patch.object(V, "ETAT", Path(t)):
            self.assertFalse(V.reprise("codex")["present"])
            f = Path(t) / "reprise_codex.md"
            f.write_text("# Reprise", encoding="utf-8")
            self.assertFalse(V.reprise("codex")["ancien"])
            self.assertTrue(V.reprise("codex", maintenant=f.stat().st_mtime + 25 * 3600)["ancien"])
        self.assertIn("reprise_codex.md", V.lien_codex().replace("%2F", "/"))


class CrochetSobre(unittest.TestCase):
    def test_seules_les_alertes_a_traiter_relancent_claude(self):
        """11/11/2026 : en fin de tour, seules les alertes qui demandent une action relancent Claude."""
        self.assertFalse(H.a_traiter("11/11/2026 19:17 · Codex · exec-x · Réponse reçue · tokens : entrée 1"))
        self.assertFalse(H.a_traiter("11/11/2026 19:18 · Fait · Relecture · Codex · sans blocage"))
        self.assertTrue(H.a_traiter("11/11/2026 · Codex → Claude · Corrections après avis."))
        self.assertTrue(H.a_traiter("11/11/2026 · Bloqué (commit seulement) · Tâche · Codex · x"))
        self.assertTrue(H.a_traiter("11/11/2026 · Codex · relecture-x · Échec · tokens"))


if __name__ == "__main__":
    unittest.main()
