"""Canal ntfy du pilotage permanent (porteur, 13/11/2026 : gratuit, sans compte ni SMS).

Remplace Telegram quand %USERPROFILE%/.makyclimat/ntfy.json existe ; le reste (boucle, fil, délégation, décisions,
compte rendu) est celui de telegram_bot.py.

- **Alertes** : publiées sur un sujet secret (« sujet_alertes »), auquel le porteur s'abonne dans l'application ntfy.
- **Ordres** : uniquement par les **boutons** des notifications (3 au plus) ; chacun publie sur le sujet secret des
  ordres un ordre signé (HMAC, secret resté sur le PC), daté (valable 7 jours), à usage unique pour les actions, et
  réservé durablement avant d'être exécuté. Un texte tapé n'est accepté que pour la lecture (/situation, /porteur,
  /rapport, /decisions, /aide) et pour /stop, qui ne fait qu'arrêter : aucun code ne circule en clair.
- Les sujets sont des noms aléatoires longs ; seul l'état du projet (déjà public sur GitHub) y passe, jamais de secret
  ni de donnée personnelle.

Corrigé après la relecture unique de Codex (13/11/2026, pilotage/etat/coordination/codex-relecture-boucle-20261113.md).
Mise en place : `python canal_ntfy.py --initialiser` (dans une fenêtre à soi : affiche le sujet à suivre), s'abonner
au sujet affiché dans l'application ntfy, puis lancer pilotage_permanent.cmd.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import telegram_bot as tb  # noqa: E402

CONFIG = Path.home() / ".makyclimat" / "ntfy.json"
LECTURE = {"/situation", "/porteur", "/rapport", "/decisions", "/aide", "/help", "/start"}
TEXTE_PERMIS = LECTURE | {"/stop"}           # arrêter est toujours sans risque ; tout le reste passe par un bouton signé
LIMITE_OCTETS = 3500                         # au-delà de 4 096 octets, ntfy transforme le message en pièce jointe
VALIDITE_S = 7 * 86400
PAUSE_S = 15


def signer(secret: str, contenu: str) -> str:
    return hmac.new(secret.encode(), contenu.encode(), hashlib.sha256).hexdigest()[:24]


def morceaux(texte: str, limite: int = LIMITE_OCTETS) -> list[str]:
    """Coupe un texte en morceaux de moins de `limite` octets UTF-8, de préférence aux fins de ligne."""
    sortie, courant = [], ""
    for ligne in texte.split("\n"):
        while len(ligne.encode()) > limite:              # ligne trop longue : coupe franche
            coupe = limite // 4
            sortie.append(ligne[:coupe])
            ligne = ligne[coupe:]
        essai = f"{courant}\n{ligne}" if courant else ligne
        if len(essai.encode()) > limite:
            sortie.append(courant)
            courant = ligne
        else:
            courant = essai
    return sortie + ([courant] if courant else [])


class Ntfy:
    def __init__(self, serveur: str):
        self.serveur = serveur.rstrip("/")

    def publier(self, sujet: str, texte: str, titre: str = "", actions: list | None = None, priorite: int = 3):
        corps = {"topic": sujet, "message": texte, "priority": priorite}
        if titre:
            corps["title"] = titre
        if actions:
            corps["actions"] = actions
        req = urllib.request.Request(self.serveur + "/", data=json.dumps(corps).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            r.read()

    def lire(self, sujet: str, depuis: str) -> list[dict]:
        url = f"{self.serveur}/{urllib.parse.quote(sujet)}/json?poll=1&since={urllib.parse.quote(depuis)}"
        with urllib.request.urlopen(url, timeout=40) as r:
            lignes = r.read().decode("utf-8", errors="replace").splitlines()
        return [m for m in (json.loads(l) for l in lignes if l.strip()) if m.get("event") == "message"]


class NtfyBot(tb.Bot):
    canal = "ntfy"

    def __init__(self, config: dict):                   # pas d'appel au constructeur Telegram
        self.config = config
        self.ntfy = Ntfy(config.get("serveur", "https://ntfy.sh"))
        self.chat = "ntfy"                               # toujours « appairé » : le sujet secret en tient lieu
        self.memoire = tb.lire_json(tb.MEMOIRE, {})

    # --- envoi
    def action(self, libelle: str, donnee: str, quand: int | None = None) -> dict:
        nonce, ts = secrets.token_hex(8), str(quand or int(time.time()))
        corps = f"!{donnee}|{nonce}|{ts}|{signer(self.config['secret'], '|'.join((donnee, nonce, ts)))}"
        return {"action": "http", "label": libelle[:40], "url": f"{self.ntfy.serveur}/{self.config['sujet_ordres']}",
                "method": "POST", "body": corps, "clear": True}

    def dire(self, texte: str, boutons: list | None = None) -> bool:
        actions = [self.action(b["text"], b["callback_data"]) for ligne in (boutons or []) for b in ligne][:3]
        parties = morceaux(texte)
        for i, partie in enumerate(parties):
            dernier = i == len(parties) - 1
            try:
                self.ntfy.publier(self.config["sujet_alertes"], partie, titre="MakyClimat" if i == 0 else "",
                                  actions=actions if dernier else None,
                                  priorite=4 if actions and dernier else 3)
            except (OSError, urllib.error.URLError) as err:
                tb.journal("envoi_echoue", erreur=str(err))
                return False
        return True

    def accuser(self, rappel: dict) -> None:
        pass

    # --- réception
    def ordre_signe(self, texte: str) -> str | None:
        """Donnée d'un ordre signé valable, réservé durablement s'il est à usage unique ; sinon None (journalisé)."""
        try:
            donnee, nonce, ts, signature = texte[1:].rsplit("|", 3)
            age = time.time() - int(ts)
        except ValueError:
            tb.journal("ordre_refuse", raison="format")
            return None
        if not hmac.compare_digest(signature, signer(self.config["secret"], "|".join((donnee, nonce, ts)))):
            tb.journal("ordre_refuse", raison="signature")
            return None
        if not -300 < age < VALIDITE_S:
            tb.journal("ordre_refuse", raison="expiré", donnee=donnee)
            self.dire("Bouton expiré (plus de 7 jours) : utilisez une notification récente.")
            return None
        if donnee.startswith("c:") and donnee[2:].split(" ")[0] in LECTURE:
            return donnee                                # lecture : réutilisable
        if not isinstance(self.memoire.get("ordres_utilises"), dict):
            self.memoire["ordres_utilises"] = {}
        utilises = self.memoire["ordres_utilises"]
        if nonce in utilises:
            tb.journal("ordre_refuse", raison="déjà utilisé", donnee=donnee)
            return None
        utilises[nonce] = time.time()                    # réservé et sauvé AVANT l'exécution (pas de rejeu au redémarrage)
        for n in [n for n, t in utilises.items() if time.time() - t > VALIDITE_S + 86400]:
            del utilises[n]
        self.sauver()
        return donnee

    def recevoir(self, message: dict) -> None:
        texte = (message.get("message") or "").strip()
        if texte.startswith("!"):
            donnee = self.ordre_signe(texte)
            return self.bouton({"data": donnee}) if donnee else None
        if texte.startswith("/") and texte.split(" ")[0].lower() in TEXTE_PERMIS:
            return self.commande(texte.split(" ")[0].lower())
        tb.journal("ordre_refuse", raison="texte non permis", debut=texte[:40])
        if texte.startswith("/"):
            self.dire("Commande tapée refusée : seules la lecture et /stop se tapent. Les autres actions passent par "
                      "les boutons des notifications.")

    def recevoir_lot(self) -> None:
        depuis = self.memoire.get("ntfy_depuis") or str(int(time.time()))
        self.memoire["ntfy_depuis"] = depuis
        for m in self.ntfy.lire(self.config["sujet_ordres"], depuis):
            self.recevoir(m)
            self.memoire["ntfy_depuis"] = m["id"]            # curseur avancé après traitement, puis sauvé
            self.sauver()
        time.sleep(PAUSE_S)


def initialiser(serveur: str) -> None:
    if CONFIG.exists():
        c = tb.lire_json(CONFIG, {})
        print("Déjà configuré. Sujet à suivre dans l'application ntfy :", c.get("sujet_alertes"))
        return
    c = {"serveur": serveur, "sujet_alertes": "mkc-" + secrets.token_urlsafe(18).replace("_", "x").replace("-", "y"),
         "sujet_ordres": "mkc-" + secrets.token_urlsafe(18).replace("_", "x").replace("-", "y"),
         "secret": secrets.token_hex(32)}
    tb.ecrire_json(CONFIG, c)
    print(f"Configuration enregistrée hors du dépôt : {CONFIG}\n")
    print("Dans l'application ntfy : + (s'abonner), serveur par défaut, sujet :\n   " + c["sujet_alertes"])
    print("\nNotez ce sujet dans un endroit sûr, puis lancez pilotage_permanent.cmd.")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--initialiser", action="store_true")
    ap.add_argument("--serveur", default="https://ntfy.sh")
    ap.add_argument("--essai", action="store_true", help="envoie une notification d'essai avec le menu")
    a = ap.parse_args()
    if a.initialiser:
        return initialiser(a.serveur)
    if not CONFIG.exists():
        sys.exit("Pas de configuration : lancer d'abord --initialiser.")
    bot = NtfyBot(tb.lire_json(CONFIG, {}))
    if a.essai:
        return bot.dire("Essai : le PC du projet vous parle. Touchez « Situation ».", tb.MENU)
    bot.tourner()


if __name__ == "__main__":
    main()
