"""Pilotage local : décisions du porteur, exécutions autorisées, relectures croisées et lecture des tokens (sans réseau,
sans lancer Claude ni Codex). Travaille sur une copie de COORDINATION.md."""
import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "scripts" / "pilotage"))
import serveur_pilotage as S  # noqa: E402
import surveiller_coordination as C  # noqa: E402

DEMARRER = S.demarrer        # vraie fonction, remplacée par un leurre dans _copie()

COPIE = """# Coordination

## Tâches

| Tâche | Responsable | État | Preuve ou périmètre | Prochaine action ou condition de fin | Début | Fin |
|---|---|---|---|---|---|---|
| Outil A | Claude | À relire | [Parcours](scripts/pilotage/parcours.py) | Vérifier le rendu. | — | — |
| Outil B | Codex | À relire | `COORDINATION.md` | Suivi seulement. | — | — |

## Messages et décisions en attente

- **10/11/2026 · Claude → porteur du projet · R-21, autoriser la collecte ?** Lots proposés : 2010 mois 2 et 3.
- **10/11/2026 · Codex → porteur du projet · Choisir un seuil.** Deux options.

Réserver cette section aux questions.

## Lancements ponctuels autorisés

- [x] `claude:ancien` Déjà fait.
"""


def _copie():
    dossier = Path(tempfile.mkdtemp())
    chemin = dossier / "COORDINATION.md"
    chemin.write_text(COPIE, encoding="utf-8")
    S.COORD = chemin
    S.tableau_de_bord.generer = lambda: None        # ne pas régénérer le vrai tableau pendant le test
    S.lire_instance = lambda dossier: None
    S.demarrer = lambda duree, relectures: {"actif": False}   # jamais de vrai surveillant pendant les tests
    S.ETAT = dossier / "etat"
    return chemin


def test_autoriser_cree_decision_et_execution():
    chemin = _copie()
    ligne = next(l for l in COPIE.splitlines() if "autoriser la collecte" in l)
    r = S.decision(C.cle_message(ligne), "autoriser", "D'abord 2010.")
    assert "erreur" not in r and r["surveillant_actif"] is False, r
    texte = chemin.read_text(encoding="utf-8")
    assert "autoriser la collecte ?** Lots" not in texte                     # message retiré
    assert "## Décisions du porteur du projet" in texte and "**Autorisé**" in texte and "D'abord 2010." in texte
    assert texte.index("## Exécutions autorisées") < texte.index("## Lancements ponctuels autorisés")
    demandes = list(C.demandes_claude(texte, False, ("claude", "codex")))
    assert len(demandes) == 1 and demandes[0][0] == "claude" and demandes[0][1].startswith("claude/exec-"), demandes
    assert "D'abord 2010." in demandes[0][2]
    # un second clic sur le même message ne fait rien
    assert "erreur" in S.decision(C.cle_message(ligne), "autoriser", "")


def test_refuser_et_repondre_n_executent_rien():
    chemin = _copie()
    ligne = next(l for l in COPIE.splitlines() if "Choisir un seuil" in l)
    assert "erreur" in S.decision(C.cle_message(ligne), "repondre", "  ")   # réponse vide refusée
    assert "erreur" not in S.decision(C.cle_message(ligne), "repondre", "Prendre l'option 2.")
    texte = chemin.read_text(encoding="utf-8")
    assert "Porteur du projet → Codex · **Réponse** · Choisir un seuil" in texte
    assert "## Exécutions autorisées" not in texte


def test_consigne_codex():
    chemin = _copie()
    assert "erreur" not in S.consigne("codex", "Relire le `workflow` 14\net répondre.")
    texte = chemin.read_text(encoding="utf-8")
    demandes = [d for d in C.demandes_claude(texte, False, ("codex",))]
    assert demandes and demandes[0][0] == "codex" and "`" not in demandes[0][2] and "\n" not in demandes[0][2]
    assert "erreur" in S.consigne("autre", "x")


def test_codex_ne_commite_pas():
    """Session enfant Codex : pas d'écriture dans .git ; Claude commite (porteur, 11/11/2026)."""
    assert "ne commite pas" in C.CONSIGNE_ECRITURE_CODEX and "reprise_codex.md" in C.CONSIGNE_ECRITURE_CODEX
    assert "commite avec un message clair" not in C.CONSIGNE_ECRITURE_CODEX
    assert "commite avec un message clair" in C.CONSIGNE_ECRITURE


def test_relecture_croisee_et_economie():
    lignes = COPIE.splitlines()
    a = next(l for l in lignes if l.startswith("| Outil A"))
    b = next(l for l in lignes if l.startswith("| Outil B"))
    assert list(C.relecture_auto(a, "claude")) == []          # Claude ne se relit pas
    (agent, ident, consigne), = C.relecture_auto(a, "codex")
    assert agent == "codex" and ident.startswith("codex/relecture-") and "```diff" in consigne
    assert list(C.relecture_auto(b, "claude")) == []          # suivi seul : pas de relecture
    reformulee = a.replace("Vérifier le rendu.", "Vérifier le rendu, autrement dit.")
    (_, ident2, _), = C.relecture_auto(reformulee, "codex")
    assert ident2 == ident                                     # reformuler la ligne ne relance pas la relecture


def test_reveil_codex_sur_nouveau_message_ou_alerte():
    with tempfile.TemporaryDirectory() as temporaire:
        dossier = Path(temporaire)
        chemin = dossier / "COORDINATION.md"
        chemin.write_text(COPIE, encoding="utf-8")
        etat = dossier / "etat"
        C.verifier(chemin, etat)
        texte = COPIE.replace("| Outil A |", "| Outil C | Codex | Bloqué | Entrée | Vérifier la source. | — | — |\n| Outil A |")
        texte = texte.replace("Réserver cette section", "- **10/11/2026 · Claude → Codex · Fiche à examiner.** Annexe locale.\n"
                             "- **10/11/2026 · Codex → Codex · Message interne.**\n\nRéserver cette section")
        chemin.write_text("> **Pilotage en pause**\n\n" + texte, encoding="utf-8")
        appels = []

        def codex(commande, *, input, **options):
            assert commande[commande.index("-s") + 1] == "read-only"
            assert "ne vaut pas autorisation" in input
            appels.append(input)
            Path(commande[commande.index("-o") + 1]).write_text("Avis de test", encoding="utf-8")
            return C.subprocess.CompletedProcess(commande, 0, stdout="", stderr="")

        with patch.object(C.subprocess, "run", side_effect=codex), patch.object(C, "reseau_ok", return_value=True),                 patch.object(C, "limite_atteinte", return_value=False):
            C.verifier(chemin, etat, codex="codex-test")
            assert appels == []
            chemin.write_text(texte, encoding="utf-8")
            for _ in range(3):
                C.verifier(chemin, etat, codex="codex-test")

        assert len(appels) == 2 and "Vérifier la source" in appels[0] and "Fiche à examiner" in appels[1]
        assert len(list(etat.glob("codex-reveil-*.md"))) == 2
        assert "Réponse reçue" in (etat / "claude.md").read_text(encoding="utf-8")


def test_lecture_des_tokens_et_fichiers():
    texte, conso = C.lire_sortie("claude", json.dumps({"result": "Verdict : sans blocage", "total_cost_usd": 0.1234,
        "usage": {"input_tokens": 10, "cache_creation_input_tokens": 1000, "cache_read_input_tokens": 20000, "output_tokens": 300}}),
        Path("absent"))
    assert texte == "Verdict : sans blocage" and conso == "entrée 21 010 (dont cache 20 000) · sortie 300 · 0.12 $", conso
    dossier = Path(tempfile.mkdtemp())
    (dossier / "r.md").write_text("Avis Codex", encoding="utf-8")
    flux = "\n".join([json.dumps({"type": "thread.started"}),
                      json.dumps({"type": "turn.completed", "usage": {"input_tokens": 5000, "cached_input_tokens": 4000, "output_tokens": 200}})])
    assert C.lire_sortie("codex", flux, dossier / "r.md") == ("Avis Codex", "entrée 5 000 (dont cache 4 000) · sortie 200")
    assert C.nom_fichier("r21-x") == "claude-r21-x.md" and C.nom_fichier("codex/relecture-a") == "codex-relecture-a.md"
    assert C.nom_fichier("claude/exec-1") == "claude-exec-1.md"
    shutil.rmtree(dossier, ignore_errors=True)


def test_empreinte_sur_diff_complet():
    """Relecture Codex : une correction au-delà de la troncature doit changer l'identifiant de relecture."""
    a = next(l for l in COPIE.splitlines() if l.startswith("| Outil A"))
    original = C.contexte_diff
    try:
        base = "+x\n" * (C.DIFF_MAX // 3 + 100)
        C.contexte_diff = lambda chemins, commit="": base + "+fin 1\n"
        (_, id1, consigne), = C.relecture_auto(a, "codex")
        C.contexte_diff = lambda chemins, commit="": base + "+fin 2\n"
        (_, id2, _), = C.relecture_auto(a, "codex")
    finally:
        C.contexte_diff = original
    assert id1 != id2 and "diff tronqué" in consigne


def test_ecriture_concurrente_non_ecrasee():
    """Relecture Codex : si un assistant écrit COORDINATION.md pendant une décision, son ajout est conservé."""
    chemin = _copie()
    appels = []

    def modifier(lignes):
        if not appels:                     # simule l'écriture d'un autre processus entre lecture et remplacement
            chemin.write_text(chemin.read_text(encoding="utf-8") + "\nAjout d'un assistant.\n", encoding="utf-8")
        appels.append(1)
        lignes.append("Ajout du serveur.")
        return {"ok": "x"}

    assert "erreur" not in S.ecrire_coordination(modifier)
    texte = chemin.read_text(encoding="utf-8")
    assert "Ajout d'un assistant." in texte and "Ajout du serveur." in texte and len(appels) == 2


def test_echec_run_confie_au_responsable_puis_au_porteur():
    """Règle du porteur (10/11/2026) : diagnostic par le responsable de la tâche, au plus 2 par workflow et par jour,
    sinon message au porteur ; un run sans tâche liée va directement au porteur."""
    chemin = _copie()
    base = {"workflow": "Outil", "conclusion": "cancelled", "url": "https://exemple/run", "chemin": ".github/workflows/x.yml"}
    texte = chemin.read_text(encoding="utf-8").replace("Vérifier le rendu.", "Vérifier le rendu (run 4242).")
    chemin.write_text(texte, encoding="utf-8")
    S.echec_run({**base, "id": 4242})
    demandes = list(C.demandes_claude(chemin.read_text(encoding="utf-8"), False, ("claude", "codex")))
    assert len(demandes) == 1 and demandes[0][0] == "claude" and "run 4242" in demandes[0][2]
    S.echec_run({**base, "id": 4242})                             # même run : rien de plus
    assert len(list(C.demandes_claude(chemin.read_text(encoding="utf-8"), False, ("claude",)))) == 1
    S.echec_run({**base, "id": 5555, "chemin": "", "workflow": "Autre"})   # aucune tâche ne le cite : message au porteur
    texte = chemin.read_text(encoding="utf-8")
    assert "Surveillant → porteur du projet · Échec GitHub à examiner.** run 5555" in texte
    texte = texte.replace("(run 4242)", "(run 4242, 6666, 7777)")
    chemin.write_text(texte, encoding="utf-8")
    S.echec_run({**base, "id": 6666})                             # 2e échec du workflow en 24 h : encore un diagnostic
    S.echec_run({**base, "id": 7777})                             # 3e : plafond atteint, message au porteur
    texte = chemin.read_text(encoding="utf-8")
    assert len(list(C.demandes_claude(texte, False, ("claude",)))) == 2 and "run 7777" in texte and "échecs de ce workflow" in texte


def test_fin_d_un_run_ancien_et_reessai():
    """Relectures Codex (10:53, 10:57) : la fin d'un run sorti des listes est vue, et un échec non transmis est retenté."""
    import github_direct as G
    etat_run = {"statut": "in_progress"}

    def faux_gh(*args, **kw):
        if args[:2] == ("run", "list"):
            if "-s" in args:      # listes des runs actifs
                return [run()] if etat_run["statut"] != "completed" and args[args.index("-s") + 1] == "in_progress" else []
            return []             # le run ancien n'est pas parmi les 12 derniers
        if args[:2] == ("run", "view"):
            return {"jobs": []} if args[-1] == "jobs" else run()
        if args[:2] == ("workflow", "list"):
            return [{"id": 9, "path": ".github/workflows/build-glofas-reforecast.yml"}]
        raise AssertionError(args)

    def run():
        return {"databaseId": 42, "workflowName": "14", "workflowDatabaseId": 9, "displayTitle": "R-21",
                "status": etat_run["statut"], "conclusion": "failure" if etat_run["statut"] == "completed" else "",
                "createdAt": "2026-11-09T11:03:00Z", "startedAt": "2026-11-09T11:03:00Z",
                "updatedAt": "2026-11-10T11:00:00Z", "event": "workflow_dispatch", "url": "u"}

    vus, reponses = [], [False, True]
    original = G.gh
    try:
        G.gh = faux_gh
        G._vus.clear()
        G.actualiser(avec_release=False, echec=lambda r: vus.append(r) or reponses.pop(0))
        etat_run["statut"] = "completed"
        G.actualiser(avec_release=False, echec=lambda r: vus.append(r) or reponses.pop(0))   # écriture refusée
        G.actualiser(avec_release=False, echec=lambda r: vus.append(r) or reponses.pop(0))   # nouvel essai réussi
        G.actualiser(avec_release=False, echec=lambda r: vus.append(r) or reponses.pop(0))   # plus rien
    finally:
        G.gh = original
        G._vus.clear()
    assert [r["id"] for r in vus] == [42, 42] and vus[0]["chemin"].endswith("build-glofas-reforecast.yml")


def test_echec_non_memorise_si_ecriture_refusee():
    _copie()
    original = S.ecrire_coordination
    try:
        S.ecrire_coordination = lambda modifier: {"erreur": "COORDINATION.md change en continu"}
        assert S.echec_run({"id": 8888, "workflow": "W", "conclusion": "failure", "url": "u", "chemin": ""}) is False
    finally:
        S.ecrire_coordination = original
    assert not (S.ETAT / "echecs_github.json").exists()
    assert S.echec_run({"id": 8888, "workflow": "W", "conclusion": "failure", "url": "u", "chemin": ""}) is True


def test_codex_transmis_sans_relectures():
    """Relecture Codex : décocher les relectures ne doit pas empêcher les exécutions confiées à Codex."""
    vus = []

    class Arret(Exception):
        pass

    def popen(commande, **kw):
        vus.append(commande)
        raise Arret

    originaux = (S.subprocess.Popen, S.binaire_codex, S.binaire_claude, S.lire_instance, S.ETAT)
    try:
        S.subprocess.Popen, S.lire_instance = popen, (lambda d: None)
        S.binaire_codex = lambda: Path("codex.exe")
        S.binaire_claude = lambda: Path("claude.exe")
        S.ETAT = Path(tempfile.mkdtemp())
        try:
            DEMARRER(60, False)
        except Arret:
            pass
    finally:
        S.subprocess.Popen, S.binaire_codex, S.binaire_claude, S.lire_instance, S.ETAT = originaux
    assert "--codex-exe" in vus[0] and "--relectures-auto" not in vus[0], vus



def test_un_seul_serveur_par_port():
    """Sous Windows, un 2e serveur se liait au même port (SO_REUSEADDR) : un onglet et des avis en double par lancement."""
    from http.server import SimpleHTTPRequestHandler
    premier = S.ServeurExclusif(("127.0.0.1", 0), SimpleHTTPRequestHandler)
    try:
        try:
            S.ServeurExclusif(("127.0.0.1", premier.server_address[1]), SimpleHTTPRequestHandler).server_close()
            assert False, "un 2e serveur a pu se lier au même port"
        except OSError:
            pass
    finally:
        premier.server_close()
    assert S.onglet_deja_ouvert(1) is False      # aucun serveur joignable → on ouvre (réponse prudente)


def test_crochet_actions_sans_texte_de_commande():
    """Le crochet ne note que la description ou le chemin relatif, jamais le texte d'une commande ou d'une demande."""
    sys.path.insert(0, str(RACINE / "scripts" / "pilotage"))
    import hook_actions as H
    g, t = H.decrire({"hook_event_name": "PostToolUse", "tool_name": "Bash",
                      "tool_input": {"command": "echo SECRET", "description": "Lister les fichiers"}})
    assert (g, t) == ("commande", "Lister les fichiers") and "SECRET" not in t
    g, t = H.decrire({"hook_event_name": "UserPromptSubmit", "prompt": "texte privé"})
    assert g == "demande" and "privé" not in t
    g, t = H.decrire({"hook_event_name": "PostToolUse", "tool_name": "Edit",
                      "tool_input": {"file_path": str(RACINE / "scripts" / "common.py")}})
    assert t == "Modifié scripts/common.py"
    g, t = H.decrire({"hook_event_name": "PostToolUse", "tool_name": "Grep", "tool_input": {"pattern": "mot de passe 1234"}})
    assert g == "recherche" and "1234" not in t and "passe" not in t


def test_carte_relire_rapprochee_du_verdict():
    """Une carte « Relire » suit le dernier verdict du diff actuel : avis rendu → carte chez le responsable."""
    import sqlite3
    import tableau_de_bord as T
    originaux = T.PIL, T.relecture_auto
    with tempfile.TemporaryDirectory() as d:
        dossier = Path(d) / "etat" / "coordination"
        dossier.mkdir(parents=True)
        from contextlib import closing
        with closing(sqlite3.connect(dossier / "coordination.sqlite3")) as db, db:
            db.execute("CREATE TABLE lancements (id TEXT PRIMARY KEY, debut TEXT, fin TEXT, statut TEXT)")
            db.executemany("INSERT INTO lancements VALUES (?, '', '10/11/2026 10:07', ?)",
                           [("codex/relecture-aaa", "Réponse reçue"), ("codex/relecture-bbb", "Délai dépassé")])
        (dossier / "codex-relecture-aaa.md").write_text("Rien à signaler.\n\nVerdict : sans blocage\n", encoding="utf-8")
        ids = {"Tâche A": "codex/relecture-aaa", "Tâche B": "codex/relecture-bbb", "Tâche C": "codex/relecture-ccc"}
        try:
            T.PIL = Path(d)
            T.relecture_auto = lambda ligne, relecteur: iter([(relecteur, ids[ligne.split("|")[1].strip()], "")])
            texte = "## Tâches\n\n" + "".join(f"| {t} | Claude | À relire | x | y |\n" for t in ids)
            col = {}
            T.colonnes_coordination(col, texte)
        finally:
            T.PIL, T.relecture_auto = originaux
    codex, claude = " ".join(col.get("codex", [])), " ".join(col.get("claude", []))
    assert "Tâche A" not in codex and "Relu sans blocage" in claude
    assert "Relecture échouée" in codex and "Tâche B" in codex
    assert "Relire : Tâche C" in codex and "À relire" in codex


def test_etat_github_fourni_a_codex_en_lecture_seule():
    """Porteur du projet, 11/11/2026 : Codex relit sans réseau ; le serveur lui fournit l'état GitHub."""
    import github_direct
    from datetime import datetime, timedelta, timezone
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "github_direct.json"
        t0 = datetime(2026, 11, 11, 8, 0, tzinfo=timezone.utc)
        github_direct.ecrire_instantane({"horodatage": t0.isoformat(), "alertes": [],
            "runs": [{"id": 1, "workflow": "14 - Reprévisions", "statut": "in_progress", "duree": "12 min",
                      "actifs": [{"nom": "build (2007-3)", "etape": "Télécharger", "depuis": "10 min"}]},
                     {"id": 2, "workflow": "Tests", "statut": "completed", "conclusion": "success", "cree": "x"}],
            "release": {"nom": "reprevisions-glofas-v4", "mois": 2, "annees": {"2010": [2, 3]}}}, f)
        texte = C.contexte_github(f, t0 + timedelta(minutes=5))
        assert "build (2007-3)" in texte and "run 2" in texte and "2010 : 2, 3" in texte
        assert C.contexte_github(f, t0 + timedelta(minutes=30)) == ""          # instantané trop ancien
        assert C.contexte_github(Path(d) / "absent.json") == ""


def test_relecture_empechee_retentee_deux_fois():
    import sqlite3
    from datetime import datetime, timedelta
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE lancements (id TEXT PRIMARY KEY, debut TEXT, fin TEXT, statut TEXT NOT NULL, consommation TEXT)")
    t0 = datetime(2026, 11, 11, 12, 0, tzinfo=C.NAIROBI)
    ident = "codex/relecture-abc"
    for essai in range(3):
        db.execute("INSERT INTO lancements VALUES (?, '', ?, 'Relecture impossible', NULL)",
                   (ident, (t0 + timedelta(hours=essai)).strftime("%d/%m/%Y %H:%M")))
        C.retenter_relectures(db, t0 + timedelta(hours=essai, minutes=5))       # trop tôt : conservée
        assert db.execute("SELECT COUNT(*) FROM lancements").fetchone()[0] == 1
        C.retenter_relectures(db, t0 + timedelta(hours=essai, minutes=25))
        restant = db.execute("SELECT COUNT(*) FROM lancements").fetchone()[0]
        assert restant == (0 if essai < 2 else 1)                               # deux nouvelles tentatives, pas plus
        if restant:
            break


def test_redemarrage_sans_tentative_supplementaire():
    """Relecture Codex 23a8531d3f17 : un redémarrage du surveillant ne contourne ni le délai ni le plafond."""
    import sqlite3
    from datetime import datetime, timedelta
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE lancements (id TEXT PRIMARY KEY, debut TEXT, fin TEXT, statut TEXT NOT NULL, consommation TEXT)")
    db.execute("CREATE TABLE retentes (id TEXT PRIMARY KEY, nombre INTEGER NOT NULL)")
    t0 = datetime(2026, 11, 11, 12, 0, tzinfo=C.NAIROBI)
    fin = t0.strftime("%d/%m/%Y %H:%M")
    db.execute("INSERT INTO lancements VALUES ('codex/relecture-epuisee', '', ?, 'Échec', NULL)", (fin,))
    db.execute("INSERT INTO retentes VALUES ('codex/relecture-epuisee', ?)", (C.RETENTES_MAX,))
    db.execute("INSERT INTO lancements VALUES ('codex/relecture-recente', '', ?, 'Échec', NULL)", (fin,))
    db.execute("INSERT INTO lancements VALUES ('claude/relecture-coupee', ?, NULL, 'En cours', NULL)", (fin,))
    C.reprendre_au_demarrage(db, t0 + timedelta(minutes=5))
    statuts = dict(db.execute("SELECT id, statut FROM lancements"))
    assert statuts == {"codex/relecture-epuisee": "Échec", "codex/relecture-recente": "Échec",
                       "claude/relecture-coupee": "Interrompu"}                  # rien n'est relancé immédiatement
    C.reprendre_au_demarrage(db, t0 + timedelta(hours=2))                        # délai écoulé
    restants = {r[0] for r in db.execute("SELECT id FROM lancements")}
    assert restants == {"codex/relecture-epuisee"}                               # plafond atteint : conservée


if __name__ == "__main__":
    for nom, fonction in list(globals().items()):
        if nom.startswith("test_"):
            fonction()
    print("OK : tests pilotage")
