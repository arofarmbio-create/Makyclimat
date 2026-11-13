"""Accueil du tableau de bord (scripts/pilotage/accueil.py) : voyant, ce qui attend le porteur, thèmes, événements."""
import json
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pilotage"))
import accueil  # noqa: E402
import fil  # noqa: E402

FIL = """\
themes:
- {id: nappes, nom: "Nappes", dit: "eau souterraine"}
- {id: systeme, nom: "Système", dit: "coulisses", coulisses: true}
donnees:
- {id: D-NON, nom: "Chlorure de la pluie", etat: manquante}
demarches:
- id: X-A
  objet: "Ministère de l'Eau"
  etapes:
    - {id: X-A.1, quoi: "Envoyer", qui: porteur, etat: pret, prochaine_action: "compléter le destinataire"}
objectifs:
- id: T-A
  theme: nappes
  titre: "Recharge des nappes"
  priorite: 1
  resultats:
    - {ref: R-1, verdict: "dans le bon sens", fiabilite: exploratoire}
    - {ref: R-2, verdict: "échec", fiabilite: provisoire}
  etapes:
    - {id: T-A.1, quoi: "Protocole", qui: claude, autorisation: porteur, depend_de: [], etat: fait, preuve: c1}
    - {id: T-A.2, quoi: "Test", qui: claude, depend_de: [T-A.1, D-NON], etat: a_faire}
- id: S-P
  theme: systeme
  titre: "Pilotage"
  etapes:
    - {id: S-P.1, quoi: "Outil", qui: claude, depend_de: [], etat: pret}
"""


@pytest.fixture
def env(tmp_path, monkeypatch):
    (tmp_path / "fil.yml").write_text(FIL, encoding="utf-8")
    monkeypatch.setattr(fil, "FIL", tmp_path / "fil.yml")
    monkeypatch.setattr(fil, "EVENEMENTS", tmp_path / "ev.jsonl")
    monkeypatch.setattr(fil, "VERROUS", tmp_path / "verrous")
    monkeypatch.setattr(fil, "AGENTS", tmp_path / "agents.json")
    return tmp_path


def test_voyant(env):
    f = fil.charger()
    assert accueil.voyant(True, {"pid": 1}, {}, f)["couleur"] == "rouge"
    assert accueil.voyant(False, None, {}, f)["couleur"] == "orange"
    v = accueil.voyant(False, {"pid": 1}, {}, f, date(2026, 11, 14))
    assert v["couleur"] == "vert" and "Pause" in v["detail"]


def test_attend_en_clair(env):
    a = accueil.vous_attend(fil.charger(), [{"cle": "k1", "objet": "Choisir X", "detail": "d"}])
    assert [x["type"] for x in a] == ["valider", "decision", "faire"]
    assert a[2]["titre"] == "Ministère de l'Eau" and "compléter" in a[2]["detail"]
    assert all("T-A" not in x["titre"] for x in a)              # pas de code à l'écran


def test_themes_sans_coulisses(env):
    t = accueil.themes(fil.charger())
    assert [x["id"] for x in t] == ["nappes"]
    n = t[0]
    assert n["meilleure"] == "exploratoire" and n["rang"] == 2 and n["manque"] == ["Chlorure de la pluie"]
    assert n["resultats_par_fiabilite"] == {"exploratoire": 1, "provisoire": 1}


def test_evenements_en_clair(env):
    fil.changer("T-A.1", valide_le="13/11/2026 14:00", valide_preuve="c1")
    fil.changer("S-P.1", etat="en_cours")                      # système : non montré
    ev = accueil.evenements(fil.charger())
    assert len(ev) == 1 and ev[0]["texte"] == "Validé par vous : Protocole" and ev[0]["theme"] == "Nappes"
    json.dumps(accueil.construire(False, {"pid": 1}, {}, []))  # sérialisable
