"""Fil des tâches (scripts/pilotage/fil.py) et boucle de coordination (telegram_bot.tick), sur un fil fictif."""
import sys
from datetime import date
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pilotage"))
import fil  # noqa: E402

FIL = """\
# commentaire conservé
donnees:
- {id: D-OK, nom: "dispo", etat: disponible}
- {id: D-PART, nom: "partielle", etat: partielle, suffit_pour: "T-A.3"}
- {id: D-NON, nom: "manquante", etat: manquante}
demarches:
- id: X-A
  etapes:
    - {id: X-A.1, quoi: "Envoyer", qui: porteur, etat: pret}
    - {id: X-A.2, quoi: "Réponse", qui: partenaire, depend_de: [X-A.1], etat: en_attente}
objectifs:
- id: T-A
  domaine: these
  priorite: 2
  etapes:
    - {id: T-A.1, quoi: "Protocole", qui: claude, autorisation: porteur, depend_de: [D-OK], etat: pret}
    - {id: T-A.2, quoi: "Calcul", qui: claude, depend_de: [T-A.1], etat: a_faire}
    - {id: T-A.3, quoi: "Audit", qui: codex, depend_de: [D-PART], etat: pret}
    - {id: T-A.4, quoi: "Bloqué", qui: claude, depend_de: [D-NON], etat: a_faire}
- id: S-B
  domaine: systeme
  priorite: 0
  etapes:
    - {id: S-B.1, quoi: "Outil", qui: claude, depend_de: [], etat: pret}
"""


@pytest.fixture
def fichier(tmp_path, monkeypatch):
    chemin = tmp_path / "fil.yml"
    chemin.write_text(FIL, encoding="utf-8")
    monkeypatch.setattr(fil, "FIL", chemin)
    monkeypatch.setattr(fil, "COORDINATEUR", tmp_path / "coordinateur.txt")
    monkeypatch.setattr(fil, "EVENEMENTS", tmp_path / "evenements.jsonl")
    monkeypatch.setattr(fil, "VERROUS", tmp_path / "verrous")
    return chemin


def ids(liste):
    return [e["id"] for e in liste]


def test_pretes_respecte_donnees_partielles_et_manquantes(fichier):
    f = fil.charger(fichier)
    pretes = ids(fil.pretes(f))
    assert "T-A.3" in pretes and "T-A.1" in pretes      # partielle suffisante pour T-A.3
    assert "T-A.4" not in pretes and "T-A.2" not in pretes


def test_protocole_relu_n_autorise_pas_le_calcul(fichier):
    assert fil.changer("T-A.1", etat="fait")
    f = fil.charger(fichier)
    assert "T-A.2" not in ids(fil.pretes(f))
    assert ids(fil.a_valider(f)) == ["T-A.1"]
    assert fil.valider("T-A.1", "13/11/2026 20:00")
    f = fil.charger(fichier)
    assert "T-A.2" in ids(fil.pretes(f)) and fil.a_valider(f) == []


def test_validation_seulement_apres_livraison_et_liee_a_la_version(fichier):
    assert not fil.valider("T-A.1", "13/11/2026 20:00")             # pas encore livrée
    fil.changer("T-A.1", etat="fait", preuve="commit-1")
    assert fil.valider("T-A.1", "13/11/2026 20:05")
    assert not fil.valider("T-A.1", "13/11/2026 20:06")             # déjà validée
    fil.changer("T-A.1", preuve="commit-2")                         # protocole modifié après validation
    f = fil.charger(fichier)
    assert "T-A.2" not in ids(fil.pretes(f)) and ids(fil.a_valider(f)) == ["T-A.1"]


def test_pause_des_calculs_et_priorite(fichier):
    f = fil.charger(fichier)
    assert fil.prochaine(f, date(2026, 11, 14))["id"] == "S-B.1"     # pendant la pause : système seulement
    fil.changer("S-B.1", etat="fait")
    f = fil.charger(fichier)
    assert fil.prochaine(f, date(2026, 11, 14)) is None
    assert fil.prochaine(f, date(2026, 11, 16))["id"] == "T-A.1"


def test_boucle_ignore_porteur_et_partenaire(fichier):
    f = fil.charger(fichier)
    p = fil.pour_porteur(f)
    assert ids(p["faire"]) == ["X-A.1"]
    choisies = []
    while (e := fil.prochaine(fil.charger(fichier), date(2027, 1, 1))):
        choisies.append(e)
        fil.changer(e["id"], etat="en_cours")
    assert choisies and all(e["qui"] not in ("porteur", "partenaire") for e in choisies)
    assert "X-A.1" not in [e["id"] for e in choisies]


def test_changer_garde_commentaires_et_lisibilite(fichier):
    assert fil.changer("T-A.3", etat="en_cours", preuve="exec:codex:20261113-1")
    texte = fichier.read_text(encoding="utf-8")
    assert texte.startswith("# commentaire conservé")
    e = next(e for e in fil.etapes(yaml.safe_load(texte)) if e["id"] == "T-A.3")
    assert e["etat"] == "en_cours" and e["preuve"] == "exec:codex:20261113-1"
    assert not fil.changer("T-Z.9", etat="fait")


def test_agent_selon_coordinateur(fichier):
    assert fil.agent_de({"qui": "codex"}) == "codex"
    assert fil.agent_de({"qui": "agent"}) == "claude"
    fil.COORDINATEUR.write_text("codex", encoding="utf-8")
    assert fil.agent_de({"qui": "coordinateur"}) == "codex" and fil.agent_de({"qui": "claude"}) == "claude"


def test_vrai_fil_coherent():
    """Le fil réel, s'il est présent sur ce poste : références toutes définies."""
    if not fil.FIL.exists():
        pytest.skip("fil local absent (pilotage/ hors dépôt)")
    f = fil.charger()
    connus = {e["id"] for e in fil.etapes(f)} | {d["id"] for d in f["donnees"]} | {o["id"] for o in f["objectifs"]}
    assert all(r in connus for e in fil.etapes(f) for r in e.get("depend_de", []))


def test_onglet_du_poste_lit_le_fil(fichier):
    import poste
    o = poste.organigramme(fichier)
    assert [r["id"] for r in o["resultats"]][:2] == ["S-B", "X-A"]           # priorité 0 d'abord
    t_a4 = next(t for r in o["resultats"] for t in r["taches"] if t["id"] == "T-A.4")
    assert "manquante" in t_a4["bloquant"] and t_a4["depend_de"] == []      # donnée affichée comme bloquante


def test_changer_valeur_avec_virgule_et_liste(fichier):
    assert fil.changer("T-A.3", prochaine_action="relire, compléter, envoyer", etat="a_relire")
    assert fil.changer("T-A.3", prochaine_action="autre, texte")
    e = next(e for e in fil.etapes(fil.charger(fichier)) if e["id"] == "T-A.3")
    assert e["prochaine_action"] == "autre, texte" and e["etat"] == "a_relire" and e["depend_de"] == ["D-PART"]
