"""Canal ntfy : signature des boutons, usage unique, code personnel, découpage des messages (sans réseau)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pilotage"))
import canal_ntfy  # noqa: E402
import telegram_bot as tb  # noqa: E402


@pytest.fixture
def bot(tmp_path, monkeypatch):
    monkeypatch.setattr(tb, "MEMOIRE", tmp_path / "memoire.json")
    monkeypatch.setattr(tb, "JOURNAL", tmp_path / "journal.jsonl")
    monkeypatch.setattr(tb, "ETAT", tmp_path)
    b = canal_ntfy.NtfyBot({"serveur": "https://ntfy.invalid", "sujet_alertes": "a", "sujet_ordres": "o",
                            "secret": "s" * 64, "code": "123456"})
    b.envoyes, b.commandes = [], []
    b.ntfy.publier = lambda sujet, texte, titre="", actions=None, priorite=3: b.envoyes.append((texte, actions))
    b.commande = lambda texte: b.commandes.append(texte)
    return b


def bouton(b, donnee):
    return b.action("X", donnee)["body"]


def test_bouton_signe_accepte_une_seule_fois(bot):
    corps = bouton(bot, "c:/stop")
    bot.recevoir({"message": corps})
    bot.recevoir({"message": corps})                      # rejeu : refusé
    assert bot.commandes == ["/stop"]


def test_bouton_de_lecture_reutilisable(bot):
    corps = bouton(bot, "c:/situation")
    bot.recevoir({"message": corps})
    bot.recevoir({"message": corps})
    assert bot.commandes == ["/situation", "/situation"]


def test_signature_fausse_refusee(bot):
    corps = bouton(bot, "c:/situation")
    bot.recevoir({"message": corps.replace("c:/situation", "c:/reprise")})
    bot.recevoir({"message": "!c:/stop|abc|0000"})
    assert bot.commandes == []


def test_texte_libre_code_exige_pour_les_actions(bot):
    bot.recevoir({"message": "/situation"})
    bot.recevoir({"message": "/stop"})                     # sans code : refusé, message d'aide envoyé
    bot.recevoir({"message": "999999 /stop"})              # mauvais code
    bot.recevoir({"message": "123456 /stop"})
    assert bot.commandes == ["/situation", "/stop"]
    assert any("code personnel" in t for t, _ in bot.envoyes)


def test_validation_par_bouton(bot):
    bot.recevoir({"message": bouton(bot, "v:T-H2.1")})
    assert bot.commandes == ["/valider T-H2.1"]


def test_dire_coupe_et_place_les_boutons_a_la_fin(bot):
    bot.dire("ligne\n" * 2000, [[{"text": "A", "callback_data": "c:/situation"}]])
    assert len(bot.envoyes) > 1
    assert all(len(t.encode()) <= canal_ntfy.LIMITE_OCTETS for t, _ in bot.envoyes)
    assert bot.envoyes[-1][1] and all(a is None for _, a in bot.envoyes[:-1])
    assert bot.envoyes[-1][1][0]["url"].endswith("/o") and bot.envoyes[-1][1][0]["method"] == "POST"


def test_morceaux_ligne_tres_longue():
    parties = canal_ntfy.morceaux("é" * 5000)
    assert "".join(parties) == "é" * 5000 and all(len(p.encode()) <= canal_ntfy.LIMITE_OCTETS for p in parties)
