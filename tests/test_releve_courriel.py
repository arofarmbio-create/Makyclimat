"""Avis de panne de la relève des courriels (scripts/pilotage/telegram_bot.py) : cause distinguée, pas de fausse alerte."""
import imaplib
import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pilotage"))
import telegram_bot as tb  # noqa: E402


@pytest.fixture
def bot(tmp_path, monkeypatch):
    monkeypatch.setattr(tb, "JOURNAL", tmp_path / "journal.jsonl")
    b = tb.Bot.__new__(tb.Bot)
    b.memoire, b.dits = {}, []
    b.dire = lambda texte, boutons=None: b.dits.append(texte) or True
    return b


def test_causes():
    assert tb.cause_echec_releve(socket.gaierror(11001, "getaddrinfo failed")) == "dns"
    assert tb.cause_echec_releve(TimeoutError("lent")) == "reseau"
    assert tb.cause_echec_releve(imaplib.IMAP4.error(b"[AUTHENTICATIONFAILED] Invalid credentials")) == "mot_de_passe"
    assert tb.cause_echec_releve(imaplib.IMAP4.abort("socket error")) == "reseau"
    assert tb.cause_echec_releve(ValueError("x")) == "autre"


def test_panne_dns_courte_sans_avis_puis_avis_unique(bot, monkeypatch):
    horloge = [1_000_000.0]
    monkeypatch.setattr(tb.time, "time", lambda: horloge[0])
    panne = socket.gaierror(11001, "getaddrinfo failed")
    bot.echec_releve(panne)
    horloge[0] += 1800
    bot.echec_releve(panne)
    assert bot.dits == []                                   # moins d'une heure : silence
    horloge[0] += 1900
    bot.echec_releve(panne)
    bot.echec_releve(panne)
    assert len(bot.dits) == 1 and "DNS" in bot.dits[0] and "mot de passe n'est pas en cause" in bot.dits[0]


def test_mot_de_passe_signale_tout_de_suite(bot):
    bot.echec_releve(imaplib.IMAP4.error(b"[AUTHENTICATIONFAILED] Invalid credentials (Failure)"))
    assert len(bot.dits) == 1 and "refuse le mot de passe" in bot.dits[0]


def test_retablissement_annonce_apres_alerte(bot, monkeypatch, tmp_path):
    import courriel
    conf = tmp_path / "email.json"
    conf.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(courriel, "CONFIG", conf)
    monkeypatch.setattr(courriel, "vue", lambda *a, **k: [])
    monkeypatch.setattr(courriel, "relever", lambda: [])
    bot.memoire.update(releve_alerte=True, releve_echec_depuis=1.0)
    bot.courriels()
    assert bot.dits == ["Relève des courriels rétablie."] and "releve_echec_depuis" not in bot.memoire
