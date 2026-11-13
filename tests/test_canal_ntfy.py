"""Canal ntfy : signature, expiration, usage unique réservé avant exécution, texte limité (sans réseau)."""
import sys
import time
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
                            "secret": "s" * 64})
    b.envoyes, b.commandes = [], []
    b.ntfy.publier = lambda sujet, texte, titre="", actions=None, priorite=3: b.envoyes.append((texte, actions))
    b.commande = lambda texte: b.commandes.append(texte)
    return b


def corps(b, donnee, quand=None):
    return b.action("X", donnee, quand)["body"]


def test_bouton_d_action_une_seule_fois_et_reserve_avant(bot):
    c = corps(bot, "c:/reprise")
    vu = []
    bot.commande = lambda texte: vu.append((texte, dict(tb.lire_json(tb.MEMOIRE, {})).get("ordres_utilises")))
    bot.recevoir({"message": c})
    bot.recevoir({"message": c})                           # rejeu : refusé
    assert [t for t, _ in vu] == ["/reprise"] and vu[0][1]  # l'ordre était déjà réservé sur disque


def test_rejeu_refuse_apres_redemarrage(bot):
    c = corps(bot, "c:/reprise")
    bot.recevoir({"message": c})
    autre = canal_ntfy.NtfyBot(bot.config)                 # nouveau processus : relit la mémoire
    autre.commandes = []
    autre.commande = lambda texte: autre.commandes.append(texte)
    autre.ntfy.publier = lambda *a, **k: None
    autre.recevoir({"message": c})
    assert bot.commandes == ["/reprise"] and autre.commandes == []


def test_bouton_de_lecture_reutilisable(bot):
    c = corps(bot, "c:/situation")
    bot.recevoir({"message": c})
    bot.recevoir({"message": c})
    assert bot.commandes == ["/situation", "/situation"]


def test_signature_fausse_ou_ancien_format_refuses(bot):
    c = corps(bot, "c:/situation")
    bot.recevoir({"message": c.replace("c:/situation", "c:/reprise")})
    bot.recevoir({"message": "!c:/stop|abc|0000"})
    assert bot.commandes == []


def test_bouton_expire(bot):
    bot.recevoir({"message": corps(bot, "c:/reprise", int(time.time()) - 8 * 86400)})
    assert bot.commandes == [] and any("expiré" in t for t, _ in bot.envoyes)


def test_texte_tape_lecture_et_stop_seulement(bot):
    for t in ("/situation", "/stop", "/reprise", "123456 /reprise", "/consigne claude x"):
        bot.recevoir({"message": t})
    assert bot.commandes == ["/situation", "/stop"]


def test_validation_par_bouton(bot):
    bot.recevoir({"message": corps(bot, "v:T-H2.1")})
    assert bot.commandes == ["/valider T-H2.1"]


def test_dire_coupe_et_place_les_boutons_a_la_fin(bot):
    assert bot.dire("ligne\n" * 2000, [[{"text": "A", "callback_data": "c:/situation"}]])
    assert len(bot.envoyes) > 1
    assert all(len(t.encode()) <= canal_ntfy.LIMITE_OCTETS for t, _ in bot.envoyes)
    assert bot.envoyes[-1][1] and all(a is None for _, a in bot.envoyes[:-1])
    assert bot.envoyes[-1][1][0]["url"].endswith("/o") and bot.envoyes[-1][1][0]["method"] == "POST"


def test_dire_signale_l_echec(bot):
    def panne(*a, **k):
        raise OSError("réseau")
    bot.ntfy.publier = panne
    assert bot.dire("x") is False


def test_morceaux_ligne_tres_longue():
    parties = canal_ntfy.morceaux("é" * 5000)
    assert "".join(parties) == "é" * 5000 and all(len(p.encode()) <= canal_ntfy.LIMITE_OCTETS for p in parties)
