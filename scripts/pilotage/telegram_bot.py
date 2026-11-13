"""Bot Telegram privé du porteur et boucle de coordination permanente (décision du porteur du 13/11/2026).

Un seul processus, lancé au démarrage du PC (pilotage_permanent.cmd) :
- **Telegram** (interrogation longue, aucun port ouvert) : n'obéit qu'au compte appairé du porteur. Commandes /aide,
  /situation, /porteur, /decisions, /valider <étape>, /stop, /stop_net, /reprise, /coordinateur claude|codex,
  /consigne claude|codex <texte>, /rapport. Boutons Autoriser / Refuser sur les décisions en attente.
- **Boucle** (toutes les 10 min) : relance le surveillant s'il s'est arrêté seul (jamais après un STOP), synchronise le
  fil avec COORDINATION.md, puis confie au bon assistant la première étape prête du fil (pilotage/fil.yml), une à la
  fois, dans la limite de PLAFOND_JOUR lancements par jour (coordination/delegation.md).
- **Compte rendu** quotidien à 19:00 (Nairobi) ; avis immédiat des nouvelles décisions et des échecs de lancement.

Secrets hors du dépôt : %USERPROFILE%/.makyclimat/telegram.json ({"token": …, "chat_id": …}).
Mise en place : 1) créer le bot avec @BotFather ; 2) `python telegram_bot.py --jeton <TOKEN>` ;
3) lancer le bot, lire le code d'appairage affiché (et écrit dans pilotage/etat/telegram_code.txt) ;
4) envoyer au bot « /start <code> » depuis son téléphone.
"""
from __future__ import annotations

import argparse
import json
import secrets
import sqlite3
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fil  # noqa: E402
import poste  # noqa: E402
import serveur_pilotage as sp  # noqa: E402
from surveiller_coordination import NAIROBI, lire_instance  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ETAT = ROOT / "pilotage" / "etat"
CONFIG = Path.home() / ".makyclimat" / "telegram.json"
JOURNAL = ETAT / "telegram.jsonl"
MEMOIRE = ETAT / "telegram_etat.json"
BOUCLE = ETAT / "boucle.json"               # mémoire de la boucle (compteur du jour, horodatages)
STOP = ETAT / "stop_porteur.txt"            # STOP du porteur : la boucle ne relance plus rien jusqu'à /reprise
PLAFOND_JOUR = 8
TICK_S = 600
HEURE_RAPPORT = 19
RELECTURE_LENTE_H = 6
DUREE_SURVEILLANT = 480


# ------------------------------------------------------------------ petits outils
def maintenant() -> datetime:
    return datetime.now(NAIROBI)


def lire_json(chemin: Path, defaut):
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaut


def ecrire_json(chemin: Path, donnees) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    tmp = chemin.with_suffix(".tmp")
    tmp.write_text(json.dumps(donnees, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(chemin)


def journal(quoi: str, **details) -> None:
    ETAT.mkdir(parents=True, exist_ok=True)
    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"quand": maintenant().isoformat(timespec="seconds"), "quoi": quoi, **details},
                           ensure_ascii=False) + "\n")


class Telegram:
    def __init__(self, token: str):
        self.base = f"https://api.telegram.org/bot{token}/"

    def appel(self, methode: str, **params):
        corps = json.dumps(params).encode("utf-8")
        req = urllib.request.Request(self.base + methode, data=corps, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=params.get("timeout", 0) + 20) as r:
            reponse = json.loads(r.read())
        if not reponse.get("ok"):
            raise RuntimeError(reponse.get("description", "erreur Telegram"))
        return reponse["result"]

    def envoyer(self, chat_id: int, texte: str, boutons: list | None = None) -> None:
        for i in range(0, len(texte), 3900):                     # limite de 4 096 caractères par message
            params = {"chat_id": chat_id, "text": texte[i:i + 3900], "disable_web_page_preview": True}
            if boutons and i + 3900 >= len(texte):
                params["reply_markup"] = {"inline_keyboard": boutons}
            self.appel("sendMessage", **params)


# ------------------------------------------------------------------ textes
def texte_situation() -> str:
    f = fil.charger()
    r = fil.resume(f)
    inst = lire_instance(sp.ETAT)
    en_cours = sp.lancement_en_cours()
    p = fil.pour_porteur(f)
    prochaine = fil.prochaine(f)
    lignes = [f"Situation — {maintenant():%d/%m %H:%M}",
              f"Surveillant : {'actif' if inst else 'arrêté'}" + (" · STOP du porteur" if STOP.exists() else ""),
              f"Coordinateur : {fil.coordinateur()}",
              f"Lancement en cours : {en_cours.get('sujet') or en_cours.get('id')}" if en_cours else "Aucun lancement en cours",
              f"Fil : {r['etapes']} étapes, {r['pretes']} prêtes, {r['par_etat'].get('fait', 0)} faites",
              "En cours dans le fil : " + (", ".join(e["id"] for e in r["en_cours"]) or "rien"),
              f"Prochaine étape : {fil.ligne_etape(prochaine)}" if prochaine else "Prochaine étape : rien de prêt",
              f"Vous attendent : {len(p['faire'])} actions, {len(p['valider'])} validations (/porteur)"]
    return "\n".join(lignes)


def texte_porteur() -> str:
    p = fil.pour_porteur(fil.charger())
    blocs = []
    for titre, cle in (("À faire", "faire"), ("À valider (/valider <id>)", "valider"),
                       ("Chez un partenaire", "chez_partenaire")):
        if p[cle]:
            blocs.append(titre + " :\n" + "\n".join("• " + fil.ligne_etape(e) for e in p[cle]))
    return "\n\n".join(blocs) or "Rien ne vous attend."


def decisions_porteur() -> list[dict]:
    return [d for d in poste.coordination()["decisions"] if d["pour_porteur"]]


def texte_rapport() -> str:
    hier = (maintenant() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    log = subprocess.run(["git", "log", f"--since={hier}", "--format=• %s"], cwd=ROOT, capture_output=True,
                         encoding="utf-8", errors="replace", check=False).stdout.strip().splitlines()
    jour = maintenant().strftime("%d/%m/%Y")
    with closing(sqlite3.connect(sp.ETAT / "coordination.sqlite3")) as db:
        lancements = db.execute("SELECT statut, COUNT(*) FROM lancements WHERE debut LIKE ? GROUP BY statut",
                                (jour + "%",)).fetchall()
    return "\n\n".join([
        f"Compte rendu du {jour}",
        texte_situation(),
        "Commits des dernières 24 h :\n" + ("\n".join(log[:12]) if log else "aucun")
        + (f"\n… et {len(log) - 12} autres" if len(log) > 12 else ""),
        "Lancements du jour : " + (", ".join(f"{n} {s}" for s, n in lancements) or "aucun"),
        "Décisions en attente : " + str(len(decisions_porteur())) + " (/decisions)",
        texte_porteur()])


# ------------------------------------------------------------------ boucle de coordination
def ligne_tache_fil(etape_id: str) -> str | None:
    """État de la ligne de COORDINATION.md marquée « [fil : <id>] », s'il y en a une."""
    for ligne in sp.COORD.read_text(encoding="utf-8-sig").splitlines():
        if ligne.startswith("| ") and f"[fil : {etape_id}]" in ligne:
            cases = [c.strip() for c in ligne.split("|")[1:-1]]
            return cases[2] if len(cases) > 2 else None
    return None


def synchroniser(memoire: dict) -> list[str]:
    """Reporte dans le fil l'état des lignes de COORDINATION.md liées à une étape (« [fil : id] »)."""
    changes = []
    for e in fil.etapes(fil.charger()):
        if e.get("etat") not in ("en_cours", "a_relire"):
            continue
        etat = (ligne_tache_fil(e["id"]) or "").casefold()
        nouveau = "fait" if etat.startswith("fait") else "clos" if etat.startswith("clos") else \
            "a_relire" if etat.startswith("à relire") else None
        if nouveau and nouveau != e["etat"]:
            fil.changer(e["id"], etat=nouveau)
            memoire.setdefault("depuis", {})[e["id"]] = time.time()
            changes.append(f"{e['id']} → {nouveau}")
    return changes


def executions_ouvertes() -> bool:
    return bool(poste.coordination()["executions"])


def consigne_etape(e: dict) -> str:
    relu = e.get("relu_par")
    return (f"[fil : {e['id']}] Boucle de coordination (délégation du porteur, coordination/delegation.md). Étape du fil "
            f"des tâches pilotage/fil.yml (local) : « {e.get('quoi', '')} » (objectif {e['_groupe']}). Lis l'objectif, "
            f"ses dépendances et la légende du fil, puis fais seulement cette étape. Crée ou mets à jour dans "
            f"COORDINATION.md une ligne de tâche dont la colonne Tâche contient « [fil : {e['id']}] ». "
            + (f"Le livrable est relu par {relu} : à la fin, passe la ligne à « À relire » en citant le commit entre "
               f"accents graves (relecture automatique, 3 tours au plus). " if relu else
               "À la fin, passe la ligne à « Fait » avec sa preuve. ")
            + (f"Ce protocole devra être validé par le porteur avant le calcul : écris aussi dans « Messages et "
               f"décisions en attente » une question « Claude → Porteur du projet · Valider {e['id']} ? » avec le lien. "
               if e.get("autorisation") == "porteur" else "")
            + "Si une donnée ou une décision manque, arrête-toi, écris-le dans la ligne et dans le message au porteur.")


def lancer_etape(e: dict, agent: str, consigne: str) -> str:
    identifiant = {}

    def modifier(lignes):
        identifiant["id"] = sp.execution(lignes, agent, consigne)
        return {"ok": "lancé"}

    sp.ecrire_coordination(modifier)
    return identifiant.get("id", "")


def tick(bot: "Bot | None") -> None:
    memoire = lire_json(BOUCLE, {})
    for c in synchroniser(memoire):
        journal("fil_synchronise", detail=c)
    if STOP.exists():
        return ecrire_json(BOUCLE, memoire)
    if not lire_instance(sp.ETAT):
        r = sp.demarrer(DUREE_SURVEILLANT, True)
        journal("surveillant_relance", ok=bool(r.get("actif")), detail=r.get("erreur", ""))
    if sp.lancement_en_cours() or executions_ouvertes():
        return ecrire_json(BOUCLE, memoire)
    jour = maintenant().strftime("%Y-%m-%d")
    compteur = memoire.setdefault("lancements", {})
    if compteur.get(jour, 0) >= PLAFOND_JOUR:
        return ecrire_json(BOUCLE, memoire)
    f = fil.charger()
    cible = None
    for e in fil.etapes(f):                       # relecture qui traîne : on la fait avancer (tour suivant)
        if e.get("etat") == "a_relire" and time.time() - memoire.get("depuis", {}).get(e["id"], time.time()) \
                > RELECTURE_LENTE_H * 3600:
            cible = (e, fil.coordinateur(), f"[fil : {e['id']}] Étape en relecture depuis plus de {RELECTURE_LENTE_H} h. "
                     "Lis le dernier avis de relecture : corrige les points bloquants (tour suivant, 3 au plus) ou, sans "
                     "point bloquant, passe la ligne à « Fait » ; au 3e tour en désaccord, écris une décision au porteur.")
            break
    if not cible and (e := fil.prochaine(f)):
        cible = (e, fil.agent_de(e), consigne_etape(e))
    if not cible:
        return ecrire_json(BOUCLE, memoire)
    e, agent, consigne = cible
    identifiant = lancer_etape(e, agent, consigne)
    if identifiant:
        if e.get("etat") != "a_relire":
            fil.changer(e["id"], etat="en_cours", preuve=f"exec:{agent}:{identifiant}")
        memoire.setdefault("depuis", {})[e["id"]] = time.time()
        compteur[jour] = compteur.get(jour, 0) + 1
        journal("etape_lancee", etape=e["id"], agent=agent, execution=identifiant)
        if bot:
            bot.dire(f"Lancé : {fil.ligne_etape(e)} → {agent}")
    ecrire_json(BOUCLE, memoire)


# ------------------------------------------------------------------ bot
class Bot:
    def __init__(self, config: dict):
        self.config = config
        self.tg = Telegram(config["token"])
        self.chat = config.get("chat_id")
        self.memoire = lire_json(MEMOIRE, {})

    def dire(self, texte: str, boutons: list | None = None) -> None:
        if self.chat:
            try:
                self.tg.envoyer(self.chat, texte, boutons)
            except (OSError, RuntimeError) as err:
                journal("envoi_echoue", erreur=str(err))

    # --- appairage
    def code(self) -> str:
        code = self.memoire.get("code_appairage") or f"{secrets.randbelow(10**6):06d}"
        self.memoire["code_appairage"] = code
        ecrire_json(MEMOIRE, self.memoire)
        (ETAT / "telegram_code.txt").write_text(code, encoding="utf-8")
        return code

    def appairer(self, message: dict) -> None:
        texte = (message.get("text") or "").strip()
        if texte == f"/start {self.code()}":
            self.chat = message["chat"]["id"]
            self.config["chat_id"] = self.chat
            ecrire_json(CONFIG, self.config)
            self.memoire.pop("code_appairage", None)
            (ETAT / "telegram_code.txt").unlink(missing_ok=True)
            journal("appairage", chat=self.chat)
            self.dire("Appairage réussi. Ce bot n'obéit plus qu'à ce compte. /aide pour les commandes.")

    # --- commandes
    def commande(self, texte: str) -> None:
        mot, _, reste = texte.strip().partition(" ")
        mot = mot.split("@")[0].lower()
        journal("commande", texte=texte[:500])
        if mot in ("/aide", "/start", "/help"):
            self.dire(__doc__.split("\n\n")[1])
        elif mot == "/situation":
            self.dire(texte_situation())
        elif mot == "/porteur":
            self.dire(texte_porteur())
        elif mot == "/rapport":
            self.dire(texte_rapport())
        elif mot == "/decisions":
            self.pousser_decisions(toutes=True)
        elif mot == "/valider":
            etape = reste.strip()
            if etape and fil.changer(etape, valide_le=maintenant().strftime("%d/%m/%Y %H:%M")):
                def noter(lignes):
                    sp.inserer(lignes, "Décisions du porteur du projet",
                               f"- {maintenant():%d/%m/%Y %H:%M} · Porteur du projet → Claude et Codex · "
                               f"**Validé (Telegram)** · étape {etape} du fil des tâches")
                    return {"ok": "noté"}
                sp.ecrire_coordination(noter)
                self.dire(f"{etape} validée : les étapes qui en dépendent deviennent prêtes.")
            else:
                self.dire("Étape introuvable. Exemple : /valider T-H2.1")
        elif mot == "/stop" or mot == "/stop_net":
            STOP.write_text(maintenant().strftime("%d/%m/%Y %H:%M"), encoding="utf-8")
            r = sp.arreter(immediat=(mot == "/stop_net"))
            self.dire("STOP enregistré. " + r.get("ok", r.get("erreur", "")) + " /reprise pour relancer.")
        elif mot == "/reprise":
            STOP.unlink(missing_ok=True)
            r = sp.demarrer(DUREE_SURVEILLANT, True) if not lire_instance(sp.ETAT) else {"actif": True}
            self.dire("Reprise : surveillant " + ("actif." if r.get("actif") else "non démarré : " + r.get("erreur", "")))
        elif mot == "/coordinateur" and reste.strip().lower() in ("claude", "codex"):
            fil.COORDINATEUR.write_text(reste.strip().lower(), encoding="utf-8")
            self.dire(f"Coordinateur : {reste.strip().lower()}.")
        elif mot == "/consigne":
            agent, _, consigne = reste.partition(" ")
            r = sp.consigne(agent.lower(), consigne)
            self.dire(r.get("ok") or r.get("erreur", ""))
        else:
            self.dire("Commande inconnue. /aide")

    # --- décisions
    def pousser_decisions(self, toutes: bool = False) -> None:
        vues = set(self.memoire.get("decisions_vues", []))
        cles = self.memoire.setdefault("cles", {})
        decisions = decisions_porteur()
        if toutes and not decisions:
            self.dire("Aucune décision en attente.")
        for d in decisions:
            if d["cle"] in vues and not toutes:
                continue
            court = d["cle"][:8]
            cles[court] = d["cle"]
            self.dire(f"Décision demandée par {d['auteur']} :\n{d['objet']}\n\n{d['detail'][:1500]}",
                      [[{"text": "Autoriser", "callback_data": f"a:{court}"},
                        {"text": "Refuser", "callback_data": f"r:{court}"}]])
            vues.add(d["cle"])
        self.memoire["decisions_vues"] = sorted(vues)[-500:]
        ecrire_json(MEMOIRE, self.memoire)

    def bouton(self, rappel: dict) -> None:
        action, _, court = (rappel.get("data") or "").partition(":")
        cle = self.memoire.get("cles", {}).get(court)
        try:
            self.tg.appel("answerCallbackQuery", callback_query_id=rappel["id"])
        except (OSError, RuntimeError):
            pass
        if not cle or action not in ("a", "r"):
            return self.dire("Décision introuvable.")
        r = sp.decision(cle, "autoriser" if action == "a" else "refuser", "Réponse donnée par Telegram.")
        journal("decision", cle=cle, action=action, resultat=r.get("ok") or r.get("erreur"))
        self.dire(r.get("ok") or r.get("erreur", ""))

    # --- surveillance
    def echecs(self) -> None:
        depuis = self.memoire.get("echecs_vus", [])
        with closing(sqlite3.connect(sp.ETAT / "coordination.sqlite3")) as db:
            lignes = db.execute("SELECT id, sujet FROM lancements WHERE statut IN ('Échec', 'Interrompu') "
                                "ORDER BY rowid DESC LIMIT 20").fetchall()
        nouveaux = [(i, s) for i, s in lignes if i not in depuis]
        if "echecs_vus" in self.memoire:                     # au premier démarrage, l'historique n'est pas renvoyé
            for i, s in nouveaux:
                self.dire(f"Lancement en échec : {s or i}")
        self.memoire["echecs_vus"] = (depuis + [i for i, _ in nouveaux])[-200:]

    def rapport_du_jour(self) -> None:
        jour = maintenant().strftime("%Y-%m-%d")
        if maintenant().hour >= HEURE_RAPPORT and self.memoire.get("rapport") != jour:
            self.dire(texte_rapport())
            self.memoire["rapport"] = jour

    # --- boucle principale
    def tourner(self) -> None:
        if not self.chat:
            print(f"Appairage : envoyez au bot « /start {self.code()} » depuis votre téléphone.", flush=True)
        decalage, prochain_tick = self.memoire.get("decalage", 0), 0.0
        while True:
            try:
                for maj in self.tg.appel("getUpdates", offset=decalage, timeout=50,
                                         allowed_updates=["message", "callback_query"]):
                    decalage = maj["update_id"] + 1
                    message, rappel = maj.get("message"), maj.get("callback_query")
                    if message and not self.chat:
                        self.appairer(message)
                    elif message and message["chat"]["id"] == self.chat and message.get("text", "").startswith("/"):
                        self.commande(message["text"])
                    elif rappel and rappel["from"]["id"] == self.chat:
                        self.bouton(rappel)
                    # tout autre expéditeur est ignoré (canal unique)
                self.memoire["decalage"] = decalage
                if self.chat:
                    self.pousser_decisions()
                    self.echecs()
                    self.rapport_du_jour()
                if time.monotonic() >= prochain_tick:
                    tick(self if self.chat else None)
                    prochain_tick = time.monotonic() + TICK_S
                ecrire_json(MEMOIRE, self.memoire)
            except (urllib.error.URLError, OSError, TimeoutError):
                time.sleep(30)                                    # réseau coupé : on attend et on reprend
            except Exception as err:                              # jamais d'arrêt silencieux
                journal("erreur", erreur=repr(err), trace=traceback.format_exc()[-1500:])
                time.sleep(30)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jeton", help="enregistre le jeton du bot (hors du dépôt) et s'arrête")
    ap.add_argument("--tick", action="store_true", help="un seul passage de la boucle, sans Telegram")
    a = ap.parse_args()
    if a.jeton:
        ecrire_json(CONFIG, {**lire_json(CONFIG, {}), "token": a.jeton.strip()})
        return print(f"Jeton enregistré dans {CONFIG}.")
    if a.tick:
        return tick(None)
    config = lire_json(CONFIG, {})
    if not config.get("token"):
        sys.exit(f"Pas de jeton : créer le bot avec @BotFather puis lancer ce script avec --jeton <TOKEN> ({CONFIG}).")
    Bot(config).tourner()


if __name__ == "__main__":
    main()
