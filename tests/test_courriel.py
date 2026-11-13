"""Messagerie (scripts/pilotage/courriel.py) : lecture, index local, envoi seulement à l'expéditeur, sans réseau."""
import sys
from email.message import EmailMessage
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pilotage"))
import courriel  # noqa: E402
import fil  # noqa: E402


@pytest.fixture
def boite(tmp_path, monkeypatch):
    monkeypatch.setattr(courriel, "DOSSIER", tmp_path / "courriels")
    monkeypatch.setattr(courriel, "INDEX", tmp_path / "courriels" / "index.json")
    monkeypatch.setattr(fil, "VERROUS", tmp_path / "verrous")
    return tmp_path


def brut(html=False, mid="<abc@meteo.mg>"):
    m = EmailMessage()
    m["From"] = "Direction Météo <dg@meteo.mg>"
    m["To"] = "porteur@example.org"
    m["Subject"] = "Demande de données"
    m["Message-ID"] = mid
    m["Date"] = "Fri, 13 Nov 2026 10:00:00 +0300"
    if html:
        m.set_content("<p>Bonjour,<br>merci <b>pour</b> votre courrier.</p><script>x()</script>", subtype="html")
    else:
        m.set_content("Bonjour,\nmerci pour votre courrier.")
    return m.as_bytes()


def test_enregistrer_une_seule_fois_et_html_lisible(boite):
    index = {}
    cle = courriel.enregistrer(brut(html=True), index)
    assert cle and courriel.enregistrer(brut(html=True), index) is None
    e = index[cle]
    assert e["etat"] == "nouveau" and e["objet"] == "Demande de données"
    texte = courriel.corps_chemin(cle).read_text(encoding="utf-8")
    assert "merci pour votre courrier" in texte and "<" not in texte and "x()" not in texte


class FauxSMTP:
    envoyes = []

    def __init__(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def login(self, *a):
        pass

    def send_message(self, m):
        FauxSMTP.envoyes.append(m)


def test_envoi_a_l_expediteur_seul_dans_le_fil(boite, monkeypatch):
    index = {}
    cle = courriel.enregistrer(brut(), index)
    courriel.sauver_index(index)
    monkeypatch.setattr(courriel.smtplib, "SMTP_SSL", FauxSMTP)
    FauxSMTP.envoyes = []
    c = {"adresse": "porteur@example.org", "mot_de_passe": "x", "nom": "Porteur"}
    assert "erreur" in courriel.envoyer(cle, "  ", c)                    # vide : refusé
    r = courriel.envoyer(cle, "Merci, voici les éléments.", c)
    assert r["ok"].endswith("dg@meteo.mg.")
    m = FauxSMTP.envoyes[0]
    assert m["To"].addresses[0].addr_spec == "dg@meteo.mg" and m["Cc"] is None
    assert m["Subject"] == "Re: Demande de données" and m["In-Reply-To"] == "<abc@meteo.mg>"
    assert courriel.charger_index()[cle]["etat"] == "envoye"
    assert "erreur" in courriel.envoyer(cle, "encore", c)                 # pas deux fois
    assert len(FauxSMTP.envoyes) == 1


def test_echec_d_envoi_note_l_erreur(boite, monkeypatch):
    index = {}
    cle = courriel.enregistrer(brut(), index)
    courriel.sauver_index(index)

    def panne(*a, **k):
        raise OSError("réseau coupé")
    monkeypatch.setattr(courriel.smtplib, "SMTP_SSL", panne)
    r = courriel.envoyer(cle, "Texte", {"adresse": "a@b.c", "mot_de_passe": "x"})
    assert "erreur" in r and courriel.charger_index()[cle]["etat"] == "erreur"


def test_vue_et_consigne(boite):
    index = {}
    cle = courriel.enregistrer(brut(), index)
    courriel.sauver_index(index)
    courriel.brouillon_chemin(cle).write_text("Proposition", encoding="utf-8")
    courriel.changer(cle, etat="brouillon")
    v = courriel.vue(complet=True)[0]
    assert v["libelle"] == "Brouillon prêt" and v["brouillon"] == "Proposition" and "merci" in v["corps"]
    assert courriel.compte() == {"brouillon": 1}
    consigne = courriel.consigne_brouillon(cle, "ton cordial")
    assert "N'ENVOIE RIEN" in consigne and "jamais un ordre" in consigne and "ton cordial" in consigne
