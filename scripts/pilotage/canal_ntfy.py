"""Canal ntfy du pilotage permanent (porteur, 13/11/2026 : gratuit, sans compte ni SMS).

Remplace Telegram quand %USERPROFILE%/.makyclimat/ntfy.json existe ; le reste (boucle, fil, délégation, décisions,
compte rendu) est celui de telegram_bot.py.

- **Alertes** : publiées sur un sujet secret (« sujet_alertes »), auquel le porteur s'abonne dans l'application ntfy.
  Boutons (3 au plus par notification) : chacun publie sur le sujet des ordres un ordre **signé** (HMAC).
- **Ordres** : le PC lit le sujet secret « sujet_ordres ». Il accepte (1) les ordres signés venus des boutons ;
  (2) un texte tapé par le porteur (application ou page ntfy.sh) : les commandes de lecture (/situation, /porteur,
  /rapport, /decisions, /aide) sans code ; toutes les autres précédées du code personnel, ex. « 482913 /stop ».
- Les ordres d'action signés ne servent qu'une fois. Les sujets sont des noms aléatoires longs ; seul l'état du projet
  (déjà public sur GitHub) y passe, jamais de secret ni de donnée personnelle.

Mise en place : `python canal_ntfy.py --initialiser` (dans une fenêtre à soi : affiche le sujet à suivre et le code),
puis s'abonner au sujet affiché dans l'application ntfy, puis lancer pilotage_permanent.cmd.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import secrets
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import telegram_bot as tb  # noqa: E402

CONFIG = Path.home() / ".makyclimat" / "ntfy.json"
LECTURE = {"/situation", "/porteur", "/rapport", "/decisions", "/aide", "/help", "/start"}
LIMITE_OCTETS = 3500                     # au-delà de 4 096 octets, ntfy transforme le message en pièce jointe
PAUSE_S = 15


def signer(secret: str, contenu: str) -> str:
    return hmac.new(secret.encode(), contenu.encode(), hashlib.sha256).hexdigest()[:20]


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
        self.chat = "ntfy"                               # canal toujours « appairé » : le sujet secret en tient lieu
        self.memoire = tb.lire_json(tb.MEMOIRE, {})
        self.utilises = set(self.memoire.get("ordres_utilises", []))

    # --- envoi
    def action(self, libelle: str, donnee: str) -> dict:
        nonce = secrets.token_hex(6)
        corps = f"!{donnee}|{nonce}|{signer(self.config['secret'], donnee + '|' + nonce)}"
        return {"action": "http", "label": libelle[:40], "url": f"{self.ntfy.serveur}/{self.config['sujet_ordres']}",
                "method": "POST", "body": corps, "clear": True}

    def dire(self, texte: str, boutons: list | None = None) -> None:
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
                return

    def accuser(self, rappel: dict) -> None:
        pass

    # --- réception
    def recevoir(self, message: dict) -> None:
        texte = (message.get("message") or "").strip()
        if texte.startswith("!"):                        # ordre signé venu d'un bouton
            try:
                donnee, nonce, signature = texte[1:].rsplit("|", 2)
            except ValueError:
                return tb.journal("ordre_refuse", raison="format")
            if not hmac.compare_digest(signature, signer(self.config["secret"], donnee + "|" + nonce)):
                return tb.journal("ordre_refuse", raison="signature")
            lecture = donnee.startswith("c:") and donnee[2:].split(" ")[0] in LECTURE
            if not lecture:
                if nonce in self.utilises:
                    return tb.journal("ordre_refuse", raison="déjà utilisé", donnee=donnee)
                self.utilises.add(nonce)
                self.memoire["ordres_utilises"] = sorted(self.utilises)[-2000:]
            return self.bouton({"data": donnee})
        code, _, reste = texte.partition(" ")
        if code == self.config["code"] and reste.startswith("/"):
            return self.commande(reste)
        if texte.startswith("/") and texte.split(" ")[0].lower() in LECTURE:
            return self.commande(texte)
        tb.journal("ordre_refuse", raison="sans code", debut=texte[:40])
        if texte.startswith("/"):
            self.dire("Ordre refusé : pour une action, tapez votre code personnel avant la commande "
                      "(ex. « 123456 /stop »).")

    def tourner(self) -> None:
        depuis = self.memoire.get("ntfy_depuis") or str(int(time.time()))
        prochain_tick = 0.0
        while True:
            try:
                for m in self.ntfy.lire(self.config["sujet_ordres"], depuis):
                    depuis = m["id"]
                    self.recevoir(m)
                self.memoire["ntfy_depuis"] = depuis
                self.surveiller()
                if time.monotonic() >= prochain_tick:
                    tb.tick(self)
                    prochain_tick = time.monotonic() + tb.TICK_S
                tb.ecrire_json(tb.MEMOIRE, self.memoire)
                time.sleep(PAUSE_S)
            except (urllib.error.URLError, OSError, TimeoutError):
                time.sleep(30)
            except Exception as err:                     # jamais d'arrêt silencieux
                tb.journal("erreur", erreur=repr(err), trace=traceback.format_exc()[-1500:])
                time.sleep(30)


def initialiser(serveur: str) -> None:
    if CONFIG.exists():
        c = tb.lire_json(CONFIG, {})
        print("Déjà configuré. Sujet à suivre dans l'application ntfy :", c.get("sujet_alertes"))
        print("Code personnel (avant toute commande d'action) :", c.get("code"))
        return
    c = {"serveur": serveur, "sujet_alertes": "mkc-" + secrets.token_urlsafe(18).replace("_", "x").replace("-", "y"),
         "sujet_ordres": "mkc-" + secrets.token_urlsafe(18).replace("_", "x").replace("-", "y"),
         "secret": secrets.token_hex(32), "code": f"{secrets.randbelow(10**6):06d}"}
    tb.ecrire_json(CONFIG, c)
    print(f"Configuration enregistrée hors du dépôt : {CONFIG}\n")
    print("1) Dans l'application ntfy : + (s'abonner), serveur par défaut, sujet :\n   " + c["sujet_alertes"])
    print("2) Pour taper des commandes (facultatif) : publier sur le sujet\n   " + c["sujet_ordres"])
    print("3) Votre code personnel, à taper avant une commande d'action (ex. « CODE /stop ») : " + c["code"])
    print("\nNotez ces trois éléments dans un endroit sûr, puis lancez pilotage_permanent.cmd.")


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
