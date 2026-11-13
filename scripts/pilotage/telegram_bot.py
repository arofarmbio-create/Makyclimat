"""Boucle de coordination permanente et canal du porteur (décision du porteur du 13/11/2026).

Un seul processus (instance unique), lancé au démarrage du PC par pilotage_permanent.cmd :
- **Canal** : ntfy si %USERPROFILE%/.makyclimat/ntfy.json existe (choix du porteur, canal_ntfy.py), sinon Telegram
  (%USERPROFILE%/.makyclimat/telegram.json). Commandes : /situation, /porteur, /rapport, /decisions, /stop ; par
  boutons : Autoriser / Refuser, Valider, Reprise.
- **Boucle** (toutes les 10 min, même sans réseau) : relance le surveillant s'il s'est arrêté seul (jamais après un
  STOP), synchronise le fil avec COORDINATION.md, signale les étapes orphelines, puis confie au bon assistant la
  première étape prête du fil (pilotage/fil.yml), une à la fois, dans la limite de PLAFOND_JOUR par jour
  (coordination/delegation.md). Chaque lancement est réservé durablement avant d'être écrit.
- **Compte rendu** quotidien à 19:00 (Nairobi), avec le rappel des décisions et validations non résolues ; avis
  immédiat des nouvelles décisions, des validations à donner et des échecs de lancement.

Corrigé après la relecture unique de Codex (13/11/2026, pilotage/etat/coordination/codex-relecture-boucle-20261113.md).
"""
from __future__ import annotations

import argparse
import json
import secrets
import socket
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
BOUCLE = ETAT / "boucle.json"               # mémoire de la boucle (compteur du jour, réservation, tours, horodatages)
STOP = fil.STOP
PLAFOND_JOUR = 8
TICK_S = 600
HEURE_RAPPORT = 19
RELECTURE_LENTE_H = 6
TOURS_MAX = 3
ORPHELINE_H = 12
RESERVATION_MAX_S = 600
DUREE_SURVEILLANT = 480
PORT_INSTANCE = 8767                        # instance unique : ce port local est tenu tant que la boucle tourne
MENU = [[{"text": "Situation", "callback_data": "c:/situation"}, {"text": "Ce qui m'attend", "callback_data": "c:/porteur"},
         {"text": "STOP", "callback_data": "c:/stop"}]]
REPRISE = [[{"text": "Reprise", "callback_data": "c:/reprise"}, {"text": "Situation", "callback_data": "c:/situation"}]]


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
    fil.ecrire_atomique(chemin, json.dumps(donnees, ensure_ascii=False, indent=1))


def journal(quoi: str, **details) -> None:
    try:
        ETAT.mkdir(parents=True, exist_ok=True)
        with JOURNAL.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"quand": maintenant().isoformat(timespec="seconds"), "quoi": quoi, **details},
                               ensure_ascii=False) + "\n")
    except OSError:
        print(quoi, details, file=sys.stderr, flush=True)


def instance_unique() -> socket.socket | None:
    """Tient un port local : une deuxième boucle ne démarre pas (relecture Codex : deux instances = doublons)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
        s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    try:
        s.bind(("127.0.0.1", PORT_INSTANCE))
        s.listen(1)
        return s
    except OSError:
        s.close()
        return None


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
              f"Vous attendent : {len(p['faire'])} actions, {len(p['valider'])} validations"]
    return "\n".join(lignes)


def texte_porteur() -> str:
    p = fil.pour_porteur(fil.charger())
    blocs = []
    for titre, cle in (("À faire", "faire"), ("À valider (bouton Valider)", "valider"),
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
    decisions = decisions_porteur()
    return "\n\n".join([
        f"Compte rendu du {jour}",
        texte_situation(),
        "Commits des dernières 24 h :\n" + ("\n".join(log[:12]) if log else "aucun")
        + (f"\n… et {len(log) - 12} autres" if len(log) > 12 else ""),
        "Lancements du jour : " + (", ".join(f"{n} {s}" for s, n in lancements) or "aucun"),
        "Décisions en attente (rappel ; boutons dans les notifications /decisions) :\n"
        + ("\n".join(f"• {d['objet']}" for d in decisions) or "aucune"),
        texte_porteur()])


# ------------------------------------------------------------------ boucle de coordination
def ligne_tache_fil(etape_id: str) -> str | None:
    """État de la ligne de COORDINATION.md marquée « [fil : <id>] », s'il y en a une."""
    for ligne in sp.COORD.read_text(encoding="utf-8-sig").splitlines():
        if ligne.startswith("| ") and f"[fil : {etape_id}]" in ligne:
            cases = [c.strip() for c in ligne.split("|")[1:-1]]
            return cases[2] if len(cases) > 2 else None
    return None


def execution_du_fil(etape_id: str) -> str | None:
    """Identifiant d'une exécution (ouverte ou cochée) dont la consigne porte « [fil : <id>] »."""
    import re
    for ligne in sp.COORD.read_text(encoding="utf-8-sig").splitlines():
        m = re.match(r"^- \[[ x]\] `exec:(claude|codex):([^`]+)` (.*)", ligne)
        if m and f"[fil : {etape_id}]" in m.group(3):
            return f"exec:{m.group(1)}:{m.group(2)}"
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
            + ("Ce protocole devra être validé par le porteur avant le calcul qu'il fixe : il recevra un bouton Valider "
               "quand l'étape sera faite ; ne lance aucun calcul qu'il fixe. " if e.get("autorisation") == "porteur" else "")
            + "Si une donnée ou une décision manque, arrête-toi, écris-le dans la ligne et dans « Messages et décisions "
              "en attente » (Claude → Porteur du projet).")


def lancer_etape(agent: str, consigne: str) -> str:
    """Écrit l'exécution autorisée ; ne rend l'identifiant que si l'écriture est confirmée (relecture Codex)."""
    identifiant = {}

    def modifier(lignes):
        identifiant["id"] = sp.execution(lignes, agent, consigne)
        return {"ok": "lancé"}

    reponse = sp.ecrire_coordination(modifier)
    if "erreur" in reponse:
        journal("lancement_refuse", erreur=reponse["erreur"])
        return ""
    return identifiant.get("id", "")


def _dire(bot, texte: str) -> None:
    if bot:
        bot.dire(texte)


def tick(bot=None) -> None:
    if BOUCLE.exists() and lire_json(BOUCLE, None) is None:          # mémoire illisible : prudence, rien ne part
        journal("boucle_bloquee", raison="boucle.json illisible")
        return
    memoire = lire_json(BOUCLE, {})
    for c in synchroniser(memoire):
        journal("fil_synchronise", detail=c)
    depuis = memoire.setdefault("depuis", {})
    occupe = bool(sp.lancement_en_cours()) or executions_ouvertes()

    # étapes en cours depuis longtemps sans lancement vivant : au porteur (relecture Codex, point 8)
    if not occupe:
        for e in fil.etapes(fil.charger()):
            if e.get("etat") == "en_cours" and time.time() - depuis.get(e["id"], time.time()) > ORPHELINE_H * 3600:
                fil.changer(e["id"], etat="decision")
                journal("etape_orpheline", etape=e["id"])
                _dire(bot, f"Étape sans suite depuis {ORPHELINE_H} h, à examiner : {fil.ligne_etape(e)}")

    # réservation d'un tour précédent interrompu : on la solde avant tout
    res = memoire.get("reservation")
    if res:
        trouve = execution_du_fil(res["etape"])
        if trouve:
            e = next((x for x in fil.etapes(fil.charger()) if x["id"] == res["etape"]), {})
            if e.get("etat") not in ("en_cours", "a_relire"):
                fil.changer(res["etape"], etat="en_cours", preuve=trouve)
            memoire.pop("reservation")
        elif time.time() - res["quand"] > RESERVATION_MAX_S:
            memoire.pop("reservation")
        else:
            return ecrire_json(BOUCLE, memoire)

    if STOP.exists():
        return ecrire_json(BOUCLE, memoire)
    if not lire_instance(sp.ETAT):
        r = sp.demarrer(DUREE_SURVEILLANT, True)
        journal("surveillant_relance", ok=bool(r.get("actif")), detail=r.get("erreur", ""))
    if occupe:
        return ecrire_json(BOUCLE, memoire)
    jour = maintenant().strftime("%Y-%m-%d")
    compteur = memoire.setdefault("lancements", {})
    if compteur.get(jour, 0) >= PLAFOND_JOUR:
        return ecrire_json(BOUCLE, memoire)

    f = fil.charger()
    tours = memoire.setdefault("tours", {})
    cible = None
    for e in fil.etapes(f):                       # relecture qui traîne : tour suivant, 3 au plus
        if e.get("etat") == "a_relire" and time.time() - depuis.get(e["id"], time.time()) > RELECTURE_LENTE_H * 3600                 and fil.disponible(e.get("relu_par") or "claude"):        # relecteur mis de côté : on attend
            if tours.get(e["id"], 1) >= TOURS_MAX:
                fil.changer(e["id"], etat="decision")
                journal("relecture_au_plafond", etape=e["id"])
                _dire(bot, f"Relecture au 3e tour sans accord, à trancher : {fil.ligne_etape(e)}")
                continue
            cible = (e, fil.coordinateur(), f"[fil : {e['id']}] Étape en relecture depuis plus de {RELECTURE_LENTE_H} h "
                     f"(tour {tours.get(e['id'], 1) + 1} sur {TOURS_MAX}). Lis le dernier avis de relecture : corrige "
                     "les points bloquants et repasse la ligne à « À relire » avec le nouveau commit, ou, sans point "
                     "bloquant, passe-la à « Fait ».", True)
            break
    if not cible and (e := fil.prochaine(f)):
        cible = (e, fil.agent_de(e), consigne_etape(e), False)
    if not cible:
        return ecrire_json(BOUCLE, memoire)

    e, agent, consigne, relance = cible
    memoire["reservation"] = {"etape": e["id"], "agent": agent, "quand": time.time()}   # réservée AVANT d'écrire
    compteur[jour] = compteur.get(jour, 0) + 1
    if relance:
        tours[e["id"]] = tours.get(e["id"], 1) + 1
    ecrire_json(BOUCLE, memoire)
    identifiant = lancer_etape(agent, consigne)
    if identifiant:
        if not relance:
            fil.changer(e["id"], etat="en_cours", preuve=f"exec:{agent}:{identifiant}")
        depuis[e["id"]] = time.time()
        journal("etape_lancee", etape=e["id"], agent=agent, execution=identifiant)
        _dire(bot, f"Lancé : {fil.ligne_etape(e)} → {agent}")
    memoire.pop("reservation", None)
    ecrire_json(BOUCLE, memoire)


# ------------------------------------------------------------------ canal (Telegram ; ntfy en hérite)
class Bot:
    canal = "Telegram"

    def __init__(self, config: dict):
        self.config = config
        self.tg = Telegram(config["token"])
        self.chat = config.get("chat_id")
        self.memoire = lire_json(MEMOIRE, {})

    def dire(self, texte: str, boutons: list | None = None) -> bool:
        if not self.chat:
            return False
        try:
            self.tg.envoyer(self.chat, texte, boutons)
            return True
        except (OSError, RuntimeError) as err:
            journal("envoi_echoue", erreur=str(err))
            return False

    def sauver(self) -> None:
        ecrire_json(MEMOIRE, self.memoire)

    # --- appairage (Telegram)
    def code(self) -> str:
        code = self.memoire.get("code_appairage") or f"{secrets.randbelow(10**6):06d}"
        self.memoire["code_appairage"] = code
        self.sauver()
        (ETAT / "telegram_code.txt").write_text(code, encoding="utf-8")
        return code

    def appairer(self, message: dict) -> None:
        if (message.get("text") or "").strip() == f"/start {self.code()}":
            self.chat = message["chat"]["id"]
            self.config["chat_id"] = self.chat
            ecrire_json(CONFIG, self.config)
            self.memoire.pop("code_appairage", None)
            (ETAT / "telegram_code.txt").unlink(missing_ok=True)
            journal("appairage", chat=self.chat)
            self.dire("Appairage réussi. Ce bot n'obéit plus qu'à ce compte.", MENU)

    # --- commandes
    def commande(self, texte: str) -> None:
        mot, _, reste = texte.strip().partition(" ")
        mot = mot.split("@")[0].lower()
        journal("commande", texte=texte[:500], canal=self.canal)
        if mot in ("/aide", "/start", "/help"):
            self.dire("Commandes : /situation, /porteur, /rapport, /decisions, /stop. Les autres actions passent par "
                      "les boutons des notifications (Autoriser, Refuser, Valider, Reprise).", MENU)
        elif mot == "/situation":
            self.dire(texte_situation(), REPRISE if STOP.exists() else MENU)
        elif mot == "/porteur":
            self.dire(texte_porteur())
        elif mot == "/rapport":
            self.dire(texte_rapport(), REPRISE if STOP.exists() else MENU)
        elif mot == "/decisions":
            self.pousser_decisions(toutes=True)
        elif mot == "/valider":
            r = sp.valider_porteur(reste.strip(), self.canal)
            self.dire(r.get("ok") or r.get("erreur", ""))
        elif mot in ("/stop", "/stop_net"):
            r = sp.stop_porteur(immediat=(mot == "/stop_net"))
            self.dire(r.get("ok") or r.get("erreur", ""), REPRISE)
        elif mot == "/reprise":
            r = sp.reprise_porteur()
            self.dire(r.get("ok") or r.get("erreur", ""), MENU)
        elif mot == "/coordinateur" and reste.strip().lower() in ("claude", "codex"):
            fil.COORDINATEUR.write_text(reste.strip().lower(), encoding="utf-8")
            self.dire(f"Coordinateur : {reste.strip().lower()}.")
        elif mot == "/consigne":
            agent, _, consigne = reste.partition(" ")
            r = sp.consigne(agent.lower(), consigne)
            self.dire(r.get("ok") or r.get("erreur", ""))
        else:
            self.dire("Commande inconnue. /aide")

    # --- décisions et validations : marquées vues seulement si l'envoi a réussi
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
            if self.dire(f"Décision demandée par {d['auteur']} :\n{d['objet']}\n\n{d['detail'][:1500]}",
                         [[{"text": "Autoriser", "callback_data": f"a:{court}"},
                           {"text": "Refuser", "callback_data": f"r:{court}"}]]):
                vues.add(d["cle"])
        self.memoire["decisions_vues"] = list(vues)[-500:]
        self.sauver()

    def pousser_validations(self) -> None:
        if not isinstance(self.memoire.get("validations_vues"), dict):
            self.memoire["validations_vues"] = {}
        vues = self.memoire["validations_vues"]
        for e in fil.a_valider(fil.charger()):
            version = f"{e['id']}|{e.get('preuve', '')}"
            if version not in vues and self.dire(
                    f"À valider : {fil.ligne_etape(e)}" + (f"\nPreuve : {e['preuve']}" if e.get("preuve") else ""),
                    [[{"text": "Valider", "callback_data": f"v:{e['id']}"}]]):
                vues[version] = time.time()
        self.sauver()

    def accuser(self, rappel: dict) -> None:
        try:
            self.tg.appel("answerCallbackQuery", callback_query_id=rappel["id"])
        except (OSError, RuntimeError):
            pass

    def bouton(self, rappel: dict) -> None:
        action, _, court = (rappel.get("data") or "").partition(":")
        self.accuser(rappel)
        if action == "c" and court.startswith("/"):
            return self.commande(court)
        if action == "v":
            return self.commande(f"/valider {court}")
        cle = self.memoire.get("cles", {}).get(court)
        if not cle or action not in ("a", "r"):
            return self.dire("Décision introuvable.")
        if action == "a" and STOP.exists():
            return self.dire("STOP en cours : autorisation non transmise. Reprise d'abord.", REPRISE)
        r = sp.decision(cle, "autoriser" if action == "a" else "refuser", f"Réponse donnée par {self.canal}.")
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
            nouveaux = [(i, s) for i, s in nouveaux if self.dire(f"Lancement en échec : {s or i}")]
        self.memoire["echecs_vus"] = (depuis + [i for i, _ in nouveaux])[-200:]

    def rapport_du_jour(self) -> None:
        jour = maintenant().strftime("%Y-%m-%d")
        if maintenant().hour >= HEURE_RAPPORT and self.memoire.get("rapport") != jour:
            if self.dire(texte_rapport(), REPRISE if STOP.exists() else MENU):
                self.memoire["rapport"] = jour

    def surveiller(self) -> None:
        for etape in (self.pousser_decisions, self.pousser_validations, self.echecs, self.rapport_du_jour):
            try:
                etape()
            except Exception as err:                         # une étape en panne n'arrête pas les autres
                journal("erreur", ou=etape.__name__, erreur=repr(err), trace=traceback.format_exc()[-1200:])
        self.sauver()

    def recevoir_lot(self) -> None:
        """Lit et traite les messages du canal (Telegram : interrogation longue)."""
        decalage = self.memoire.get("decalage", 0)
        for maj in self.tg.appel("getUpdates", offset=decalage, timeout=50, allowed_updates=["message", "callback_query"]):
            message, rappel = maj.get("message"), maj.get("callback_query")
            if message and not self.chat:
                self.appairer(message)
            elif message and message["chat"]["id"] == self.chat and message.get("text", "").startswith("/"):
                self.commande(message["text"])
            elif rappel and rappel["from"]["id"] == self.chat:
                self.bouton(rappel)
            self.memoire["decalage"] = maj["update_id"] + 1          # avancé après traitement, puis sauvé
            self.sauver()

    # --- boucle principale : réception, surveillance et ordonnanceur séparés (le réseau ne bloque pas la boucle)
    def tourner(self) -> None:
        if not self.chat and self.canal == "Telegram":
            print(f"Appairage : envoyez au bot « /start {self.code()} » depuis votre téléphone.", flush=True)
        prochain_tick, reseau_signale = 0.0, False
        while True:
            try:
                self.recevoir_lot()
                reseau_signale = False
            except (urllib.error.URLError, OSError, TimeoutError) as err:
                if not reseau_signale:
                    journal("reseau_indisponible", erreur=str(err)[:300])
                    reseau_signale = True
                time.sleep(20)
            except Exception as err:
                journal("erreur", ou="reception", erreur=repr(err), trace=traceback.format_exc()[-1200:])
                time.sleep(20)
            if self.chat:
                self.surveiller()
            if time.monotonic() >= prochain_tick:
                try:
                    tick(self if self.chat else None)
                except Exception as err:                     # jamais d'arrêt silencieux de la boucle
                    journal("erreur", ou="tick", erreur=repr(err), trace=traceback.format_exc()[-1500:])
                prochain_tick = time.monotonic() + TICK_S


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jeton", help="Telegram : enregistre le jeton du bot (hors du dépôt) et s'arrête")
    ap.add_argument("--tick", action="store_true", help="un seul passage de la boucle, sans canal")
    a = ap.parse_args()
    if a.jeton:
        ecrire_json(CONFIG, {**lire_json(CONFIG, {}), "token": a.jeton.strip()})
        return print(f"Jeton enregistré dans {CONFIG}.")
    verrou = instance_unique()
    if verrou is None:
        sys.exit("Une boucle de coordination tourne déjà sur ce PC : rien à faire.")
    if a.tick:
        return tick(None)
    import canal_ntfy                                   # ntfy (gratuit, sans compte) prime s'il est configuré
    if canal_ntfy.CONFIG.exists():
        return canal_ntfy.NtfyBot(lire_json(canal_ntfy.CONFIG, {})).tourner()
    config = lire_json(CONFIG, {})
    if not config.get("token"):
        sys.exit(f"Aucun canal : lancer canal_ntfy.py --initialiser (ou configurer Telegram : {CONFIG}).")
    Bot(config).tourner()


if __name__ == "__main__":
    main()
