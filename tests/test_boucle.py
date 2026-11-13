"""Boucle de coordination (telegram_bot.tick) : STOP, plafond, réservation, échec d'écriture, tours de relecture,
et STOP respecté par le démarrage du surveillant (relecture Codex du 13/11/2026). Aucun lancement réel."""
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pilotage"))
import fil  # noqa: E402
import serveur_pilotage as sp  # noqa: E402
import telegram_bot as tb  # noqa: E402

DEMARRER = sp.demarrer          # la vraie fonction (un autre fichier de tests la remplace sans la rétablir)

FIL = """\
donnees: []
objectifs:
- id: S-X
  domaine: systeme
  priorite: 0
  etapes:
    - {id: S-X.1, quoi: "Un", qui: claude, depend_de: [], etat: pret}
    - {id: S-X.2, quoi: "Deux", qui: codex, depend_de: [], etat: pret}
"""


@pytest.fixture
def env(tmp_path, monkeypatch):
    (tmp_path / "fil.yml").write_text(FIL, encoding="utf-8")
    monkeypatch.setattr(fil, "FIL", tmp_path / "fil.yml")
    monkeypatch.setattr(fil, "VERROUS", tmp_path / "verrous")
    monkeypatch.setattr(fil, "COORDINATEUR", tmp_path / "coordinateur.txt")
    monkeypatch.setattr(fil, "EVENEMENTS", tmp_path / "evenements.jsonl")
    monkeypatch.setattr(fil, "VERROUS", tmp_path / "verrous")
    monkeypatch.setattr(tb, "BOUCLE", tmp_path / "boucle.json")
    monkeypatch.setattr(tb, "JOURNAL", tmp_path / "journal.jsonl")
    monkeypatch.setattr(tb, "STOP", tmp_path / "stop.txt")
    monkeypatch.setattr(tb, "synchroniser", lambda memoire: [])
    monkeypatch.setattr(tb, "execution_du_fil", lambda etape: None)
    monkeypatch.setattr(tb, "executions_ouvertes", lambda: False)
    monkeypatch.setattr(tb, "lire_instance", lambda dossier: {"pid": 1})
    monkeypatch.setattr(sp, "lancement_en_cours", lambda: {})
    lances = []
    monkeypatch.setattr(tb, "lancer_etape", lambda agent, consigne: lances.append((agent, consigne)) or f"id{len(lances)}")
    return lances


def etat(i):
    return next(e for e in fil.etapes(fil.charger()) if e["id"] == i)


def test_un_lancement_par_passage_puis_attente(env, monkeypatch):
    tb.tick()
    assert len(env) == 1 and etat("S-X.1")["etat"] == "en_cours" and etat("S-X.1")["preuve"] == "exec:claude:id1"
    monkeypatch.setattr(sp, "lancement_en_cours", lambda: {"id": "x"})
    tb.tick()
    assert len(env) == 1                                   # un lancement vivant : rien de plus


def test_stop_bloque_tout(env):
    tb.STOP.write_text("x", encoding="utf-8")
    tb.tick()
    assert env == []


def test_plafond_du_jour(env, monkeypatch):
    monkeypatch.setattr(tb, "PLAFOND_JOUR", 1)
    tb.tick()
    fil.changer("S-X.1", etat="fait")
    tb.tick()
    assert len(env) == 1


def test_echec_d_ecriture_ne_marque_rien(env, monkeypatch):
    monkeypatch.setattr(tb, "lancer_etape", lambda agent, consigne: "")
    tb.tick()
    m = tb.lire_json(tb.BOUCLE, {})
    assert etat("S-X.1")["etat"] == "pret" and "reservation" not in m and sum(m["lancements"].values()) == 1


def test_reservation_interrompue_soldee_sans_doublon(env, monkeypatch):
    tb.ecrire_json(tb.BOUCLE, {"reservation": {"etape": "S-X.1", "agent": "claude", "quand": time.time()}})
    monkeypatch.setattr(tb, "execution_du_fil", lambda etape: "exec:claude:ancien" if etape == "S-X.1" else None)
    tb.tick()
    assert etat("S-X.1")["etat"] == "en_cours" and etat("S-X.1")["preuve"] == "exec:claude:ancien"
    assert [c for _, c in env if "S-X.1" in c] == []        # pas relancée


def test_reservation_recente_sans_trace_attend(env):
    tb.ecrire_json(tb.BOUCLE, {"reservation": {"etape": "S-X.1", "agent": "claude", "quand": time.time()}})
    tb.tick()
    assert env == []


def test_memoire_illisible_rien_ne_part(env):
    tb.BOUCLE.write_text("{pas du json", encoding="utf-8")
    tb.tick()
    assert env == []


def test_relecture_plafonnee_a_trois_tours(env, monkeypatch):
    fil.changer("S-X.1", etat="a_relire")
    fil.changer("S-X.2", etat="fait")
    vieux = time.time() - 7 * 3600
    tb.ecrire_json(tb.BOUCLE, {"depuis": {"S-X.1": vieux}, "tours": {"S-X.1": 1}})
    tb.tick()
    assert len(env) == 1 and "tour 2" in env[0][1]
    m = tb.lire_json(tb.BOUCLE, {})
    m["depuis"]["S-X.1"] = vieux
    m["tours"]["S-X.1"] = 3
    tb.ecrire_json(tb.BOUCLE, m)
    tb.tick()
    assert len(env) == 1 and etat("S-X.1")["etat"] == "decision"


def test_demarrage_refuse_apres_stop(tmp_path, monkeypatch):
    monkeypatch.setattr(fil, "STOP", tmp_path / "stop.txt")
    fil.STOP.write_text("x", encoding="utf-8")
    assert "erreur" in DEMARRER(60, True)


def test_hotes_supplementaires(tmp_path, monkeypatch):
    f = tmp_path / "hotes.txt"
    monkeypatch.setattr(sp, "HOTES", f)
    assert sp.hotes_supplementaires() == set()
    f.write_text("# commentaire\nPC.tail1234.ts.net\n\n", encoding="utf-8")
    assert sp.hotes_supplementaires() == {"pc.tail1234.ts.net"}


def test_codex_mis_de_cote(env, monkeypatch, tmp_path):
    from datetime import datetime
    monkeypatch.setattr(fil, "AGENTS", tmp_path / "agents.json")
    (tmp_path / "agents.json").write_text('{"codex": {"indisponible_jusqu_au": "2026-11-17T00:00:00+03:00"}}',
                                          encoding="utf-8")
    assert not fil.disponible("codex", datetime.fromisoformat("2026-11-16T23:59:00+03:00"))
    assert fil.disponible("codex", datetime.fromisoformat("2026-11-17T00:00:00+03:00"))
    assert fil.disponible("claude")
    fil.changer("S-X.1", etat="fait")                       # ne reste que l'étape de Codex
    tb.tick()
    assert env == []                                         # Codex mis de côté : rien ne part


def test_urgent_en_tete_de_file():
    lignes = ["## Exécutions autorisées", "", "Texte.", "", "- [ ] `exec:claude:a` tâche A", "- [ ] `exec:codex:b` tâche B",
              "", "## Décisions du porteur du projet"]
    sp.execution(lignes, "claude", "urgent X", en_tete=True)
    execs = [l for l in lignes if l.startswith("- [ ]")]
    assert "urgent X" in execs[0] and "tâche A" in execs[1]
    sp.execution(lignes, "claude", "normale Y")
    assert "normale Y" in [l for l in lignes if l.startswith("- [ ]")][-1]


def test_message_urgent_attend_la_tache_en_cours(monkeypatch, tmp_path):
    import poste
    monkeypatch.setattr(poste, "MESSAGES", tmp_path / "messages.jsonl")
    monkeypatch.setattr(fil, "STOP", tmp_path / "stop.txt")
    ecrit = {}

    def ecrire(modifier):
        lignes = ["## Exécutions autorisées", "", "- [ ] `exec:codex:b` tâche B", ""]
        r = modifier(lignes)
        ecrit["lignes"] = lignes
        return r
    monkeypatch.setattr(sp, "ecrire_coordination", ecrire)
    monkeypatch.setattr(sp, "lancer_si_besoin", lambda r, cree: r)
    monkeypatch.setattr(sp, "lancement_en_cours", lambda: {"id": "x", "sujet": "Bilan R-40"})
    r = sp.message_urgent("Réponds au mail de la DGM")
    assert "termine d'abord" in r["ok"] and "Bilan R-40" in r["ok"]
    premiere = next(l for l in ecrit["lignes"] if l.startswith("- [ ]"))
    assert "[urgent]" in premiere and "DGM" in premiere
    assert poste.a_remettre("claude") == []                   # pas remis une seconde fois à la session mère
