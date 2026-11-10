"""Serveur local du tableau de bord : sert pilotage/, régénère la page et démarre ou arrête le surveillant.

Usage : double-cliquer sur pilotage.cmd à la racine du dépôt, ou
        .venv/Scripts/python.exe -B -X utf8 scripts/pilotage/serveur_pilotage.py [--port 8765] [--sans-navigateur]
Le serveur n'écoute que sur 127.0.0.1. Les commandes exigent un jeton tiré au démarrage et l'en-tête Host local,
ce qui empêche une autre page web ouverte dans le navigateur de démarrer ou d'arrêter le surveillant.
Fermer la fenêtre arrête le serveur ; un surveillant déjà lancé continue jusqu'à sa durée maximale.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import github_direct  # noqa: E402
import tableau_de_bord  # noqa: E402
from surveiller_coordination import NAIROBI, cle_message, ecrire_si_change, lire_instance  # noqa: E402
from datetime import datetime  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PIL = ROOT / "pilotage"
ETAT = PIL / "etat" / "coordination"
SURVEILLANT = Path(__file__).resolve().parent / "surveiller_coordination.py"
DUREES = (30, 60, 120, 240, 480)
JETON = secrets.token_urlsafe(24)
_verrou = threading.Lock()


def binaire_claude() -> Path | None:
    """Binaire natif Windows de Claude Code : le surveillant refuse les intermédiaires .cmd et .ps1."""
    for nom in ("claude.exe", "claude.cmd", "claude"):
        trouve = shutil.which(nom)
        if not trouve:
            continue
        chemin = Path(trouve)
        if chemin.suffix.lower() == ".exe":
            return chemin
        natif = chemin.parent / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
        if natif.is_file():
            return natif
    natif = Path.home() / ".local" / "bin" / "claude.exe"
    return natif if natif.is_file() else None


def binaire_codex() -> Path | None:
    """Ligne de commande Codex : sur le PATH, sinon celle de l'application Codex. La copie de .sandbox-bin ne trouve
    pas son outil de lecture (codex-code-mode-host.exe) : relectures bloquées le 10/11/2026. Celle de
    .plugin-appserver l'a à côté d'elle et fonctionne."""
    trouve = shutil.which("codex.exe") or shutil.which("codex")
    if trouve and Path(trouve).suffix.lower() == ".exe":
        return Path(trouve)
    natif = Path.home() / ".codex" / "plugins" / ".plugin-appserver" / "codex.exe"
    return natif if natif.is_file() and (natif.parent / "codex-code-mode-host.exe").is_file() else None


def etat() -> dict:
    instance = lire_instance(ETAT)
    return {"actif": bool(instance), **(instance or {}), "claude_disponible": bool(binaire_claude()),
            "codex_disponible": bool(binaire_codex()), "jeton": JETON, "durees": DUREES}


def demarrer(duree: int, relectures: bool) -> dict:
    with _verrou:
        if lire_instance(ETAT):
            return {"erreur": "Le surveillant est déjà actif."}
        if duree not in DUREES:
            return {"erreur": "Durée non autorisée."}
        exe = binaire_claude()
        commande = [sys.executable, "-B", "-X", "utf8", str(SURVEILLANT), "--boucle",
                    "--duree-minutes", str(duree), "--windows"]
        codex = binaire_codex()
        if exe:
            commande += ["--claude-exe", str(exe)]
        if codex:            # toujours : les consignes et autorisations confiées à Codex en dépendent (relecture Codex)
            commande += ["--codex-exe", str(codex)]
        if relectures and (exe or codex):
            commande.append("--relectures-auto")
        ETAT.mkdir(parents=True, exist_ok=True)
        journal = open(ETAT / "surveillant.log", "a", encoding="utf-8")
        subprocess.Popen(commande, cwd=ROOT, stdout=journal, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        journal.close()
        for _ in range(40):                       # attendre que la boucle se déclare (surveillant.json)
            if lire_instance(ETAT):
                break
            time.sleep(0.25)
        return etat() if lire_instance(ETAT) else {"erreur": "Démarrage non confirmé : voir pilotage/etat/coordination/surveillant.log."}


def arreter() -> dict:
    with _verrou:
        instance = lire_instance(ETAT)
        if not instance:
            return etat()
        pid = int(instance["pid"])
        if os.name == "nt":                      # /T : arrête aussi une session Claude en cours
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        else:
            os.kill(pid, 15)
        for _ in range(20):
            if not lire_instance(ETAT):
                break
            time.sleep(0.25)
        (ETAT / "surveillant.json").unlink(missing_ok=True)   # un arrêt forcé n'exécute pas le nettoyage du surveillant
        return etat()


# ------------------------------------------------------------------ décisions et consignes du porteur (option C)
COORD = ROOT / "COORDINATION.md"
SECTIONS = {
    "Décisions du porteur du projet": "Réponses données depuis le tableau de bord. L'assistant concerné les lit à sa "
                                      "reprise et met sa ligne de tâche à jour.",
    "Exécutions autorisées": "Ajoutées par le tableau de bord après un clic du porteur du projet. Le surveillant les "
                             "exécute une à une en mode écriture ; l'agent coche sa ligne à la fin.",
}
LIBELLES = {"autoriser": "Autorisé", "refuser": "Refusé", "repondre": "Réponse"}


def propre(texte: str, n: int = 1500) -> str:
    """Une seule ligne Markdown, sans accent grave (réservé aux identifiants d'exécution)."""
    return " ".join(str(texte or "").split()).replace("`", "'")[:n]


def inserer(lignes: list[str], titre: str, nouvelle: str) -> None:
    """Ajoute une puce à la fin d'une section, créée au besoin avant « Lancements ponctuels autorisés »."""
    entete = f"## {titre}"
    if entete not in lignes:
        position = next((i for i, l in enumerate(lignes) if l.startswith("## Lancements ponctuels")), len(lignes))
        lignes[position:position] = [entete, "", SECTIONS[titre], ""]
    i = lignes.index(entete) + 1
    j = next((k for k in range(i, len(lignes)) if lignes[k].startswith("## ")), len(lignes))
    while j > i and not lignes[j - 1].strip():      # remonter au-dessus des lignes vides de fin de section
        j -= 1
    if lignes[j - 1].strip() and not lignes[j - 1].startswith("- "):   # une liste après un paragraphe : ligne vide
        lignes.insert(j, "")
        j += 1
    lignes.insert(j, nouvelle)
    if j + 1 < len(lignes) and lignes[j + 1].strip():
        lignes.insert(j + 1, "")


def ecrire_coordination(modifier) -> dict:
    """Lecture, modification puis remplacement atomique. Relecture Codex du 10/11 : un assistant peut écrire le fichier
    entre la lecture et le remplacement. On relit juste avant d'écrire ; si le contenu a changé, la modification est
    rejouée sur la nouvelle version (trois essais), au lieu d'écraser l'écriture de l'autre."""
    with _verrou:
        for _ in range(3):
            brut = COORD.read_text(encoding="utf-8-sig")
            fin_ligne = "\r\n" if "\r\n" in brut else "\n"
            lignes = brut.splitlines()
            reponse = modifier(lignes)
            if "erreur" in reponse:
                break
            if COORD.read_text(encoding="utf-8-sig") == brut:
                ecrire_si_change(COORD, fin_ligne.join(lignes) + fin_ligne)
                break
            time.sleep(0.5)
        else:
            reponse = {"erreur": "COORDINATION.md change en continu : réessayer dans un instant."}
    try:
        tableau_de_bord.generer()
    except Exception:
        pass
    reponse["surveillant_actif"] = bool(lire_instance(ETAT))
    return reponse


def execution(lignes, agent: str, demande: str) -> str:
    identifiant = datetime.now(NAIROBI).strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(2)
    inserer(lignes, "Exécutions autorisées", f"- [ ] `exec:{agent}:{identifiant}` {propre(demande, 3900)}")
    return identifiant


def decision(cle: str, action: str, texte: str) -> dict:
    if action not in LIBELLES or (action == "repondre" and not texte.strip()):
        return {"erreur": "Action inconnue, ou réponse vide."}

    def modifier(lignes):
        section = ""
        for i, ligne in enumerate(lignes):
            if ligne.startswith("## "):
                section = ligne[3:]
            if section.startswith("Messages") and ligne.startswith("- **") and cle_message(ligne) == cle:
                break
        else:
            return {"erreur": "Message introuvable : il a peut-être déjà été traité."}
        message = lignes.pop(i)
        tete = message[4:].split("**", 1)[0]
        parties = [p.strip() for p in tete.split("·")]
        auteur = parties[1].split("→")[0].strip() if len(parties) > 1 else "Claude"
        objet = " · ".join(parties[2:]).rstrip(".") or tete
        maintenant = datetime.now(NAIROBI).strftime("%d/%m/%Y %H:%M")
        ligne = f"- {maintenant} · Porteur du projet → {auteur} · **{LIBELLES[action]}** · {propre(objet, 300)}"
        if texte.strip():
            ligne += f" · Précision : {propre(texte)}"
        reponse = {"ok": f"{LIBELLES[action]} : décision inscrite dans COORDINATION.md."}
        if action == "autoriser":
            agent = "codex" if "codex" in auteur.casefold() else "claude"
            demande = (f"Le porteur du projet autorise : {objet}. Message d'origine : {message[2:].replace('**', '')}"
                       + (f" Précision du porteur : {texte}" if texte.strip() else ""))
            identifiant = execution(lignes, agent, demande)
            ligne += f" · Exécution `exec:{agent}:{identifiant}`"
            reponse["ok"] = f"Autorisé : exécution confiée à {agent.capitalize()}."
        inserer(lignes, "Décisions du porteur du projet", ligne)
        return reponse

    return lancer_si_besoin(ecrire_coordination(modifier), action == "autoriser")


def lancer_si_besoin(reponse: dict, execution_creee: bool) -> dict:
    """Une exécution autorisée ne part que si le surveillant tourne : on le démarre (2 h, relectures actives)."""
    if execution_creee and "erreur" not in reponse and not reponse.get("surveillant_actif"):
        demarre = demarrer(120, True)
        reponse["surveillant_actif"] = bool(demarre.get("actif"))
        if reponse["surveillant_actif"]:
            reponse["ok"] += " Surveillant démarré pour 2 h."
    return reponse


def consigne(agent: str, texte: str) -> dict:
    if agent not in ("claude", "codex") or not texte.strip():
        return {"erreur": "Choisir Claude ou Codex et écrire une consigne."}

    def modifier(lignes):
        identifiant = execution(lignes, agent, f"Consigne du porteur du projet : {texte}")
        maintenant = datetime.now(NAIROBI).strftime("%d/%m/%Y %H:%M")
        inserer(lignes, "Décisions du porteur du projet",
                f"- {maintenant} · Porteur du projet → {agent.capitalize()} · **Consigne** · {propre(texte, 600)}"
                f" · Exécution `exec:{agent}:{identifiant}`")
        return {"ok": f"Consigne confiée à {agent.capitalize()}."}

    return lancer_si_besoin(ecrire_coordination(modifier), True)


# ------------------------------------------------------------------ échec d'un run GitHub (règle du porteur, 10/11/2026)
# Le responsable de la tâche liée au run diagnostique la cause ; s'il peut corriger, il corrige et relance une fois ;
# sinon il écrit au porteur la cause et ses suggestions, et attend sa validation.
ECHECS_MAX_JOUR = 2              # au-delà, pour un même workflow, plus de diagnostic automatique : avis du porteur


def tache_du_run(lignes, run) -> tuple[str, str] | None:
    """(tâche, responsable) de la première tâche ouverte qui cite le run ou le fichier de son workflow."""
    cles = [str(run["id"])] + ([Path(run["chemin"]).name] if run.get("chemin") else [])
    section = ""
    for ligne in lignes:
        if ligne.startswith("## "):
            section = ligne[3:]
        if section == "Tâches" and ligne.startswith("| ") and any(c in ligne for c in cles):
            champs = [c.strip() for c in ligne.split("|")[1:-1]]
            if len(champs) >= 5 and champs[0] != "Tâche" and not champs[2].casefold().startswith(("fait", "clos")):
                return champs[0], champs[1]
    return None


def echec_run(run: dict) -> None:
    journal = ETAT / "echecs_github.json"
    try:
        historique = json.loads(journal.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        historique = []
    limite = time.time() - 86400
    historique = [h for h in historique if h["t"] > limite]
    if any(h["run"] == run["id"] for h in historique):
        return                                       # déjà traité
    recents = sum(h["workflow"] == run["workflow"] for h in historique)
    historique.append({"t": time.time(), "run": run["id"], "workflow": run["workflow"]})
    ETAT.mkdir(parents=True, exist_ok=True)
    ecrire_si_change(journal, json.dumps(historique, ensure_ascii=False))
    resume = f"run {run['id']} ({run['workflow']}, {run['conclusion']}) {run['url']}"

    def modifier(lignes):
        maintenant = datetime.now(NAIROBI).strftime("%d/%m/%Y")
        trouve = tache_du_run(lignes, run)
        agent = None
        if trouve:
            responsable = trouve[1].casefold()
            agent = "codex" if "codex" in responsable else "claude" if "claude" in responsable else None
        if agent and recents < ECHECS_MAX_JOUR:
            execution(lignes, agent,
                      f"Diagnostic d'échec automatique · {resume} · tâche « {trouve[0]} ». Lis le journal "
                      f"(gh run view {run['id']} --log-failed ; si GitHub le refuse, gh run view {run['id']} --json jobs) "
                      f"et identifie la cause. Si elle est corrigeable dans le périmètre de ta tâche : corrige, teste, "
                      f"commite, pousse, puis relance une seule fois (gh run rerun {run['id']} --failed, ou gh workflow run "
                      f"avec les mêmes paramètres) en respectant la règle 6 (aucun autre téléchargement du même fournisseur "
                      f"en cours) ; consigne cause, correction et relance dans ta ligne de tâche. Si ce n'est pas "
                      f"corrigeable, ou si la même cause a déjà fait échouer une relance : ne relance pas, écris au porteur "
                      f"du projet dans « Messages et décisions en attente » la cause et tes suggestions, et attends sa "
                      f"validation.")
            return {"ok": f"diagnostic confié à {agent}"}
        motif = ("aucune tâche ouverte de Claude ou Codex ne cite ce workflow" if not agent
                 else f"{recents} échecs de ce workflow en 24 h : pas de nouveau diagnostic automatique")
        i = next((k for k, l in enumerate(lignes) if l.startswith("## Messages")), None)
        if i is None:
            return {"erreur": "section des messages introuvable"}
        lignes.insert(i + 2, f"- **{maintenant} · Surveillant → porteur du projet · Échec GitHub à examiner.** "
                             f"{propre(resume, 400)} ; {motif}. Répondre ou autoriser une relance.")
        return {"ok": "message au porteur"}

    reponse = ecrire_coordination(modifier)               # le diagnostic ne part que si le surveillant tourne
    lancer_si_besoin(reponse, reponse.get("ok", "").startswith("diagnostic"))


class Gestionnaire(SimpleHTTPRequestHandler):
    hotes: set[str] = set()

    def log_message(self, *args):
        pass

    def _local(self) -> bool:
        if self.headers.get("Host", "") not in self.hotes:   # protège contre le DNS rebinding
            self.send_error(403)
            return False
        return True

    def _json(self, donnees: dict, code: int = 200):
        corps = json.dumps(donnees, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if not self._local():
            return
        if self.path in ("/", "/index.html"):
            self.send_response(302)
            self.send_header("Location", "/tableau_de_bord.html")
            self.end_headers()
            return
        if self.path == "/api/surveillant":
            return self._json(etat())
        if self.path == "/api/github":
            return self._json(github_direct.etat())
        super().do_GET()

    def do_POST(self):
        if not self._local():
            return
        origine = self.headers.get("Origin")
        if self.headers.get("X-Pilotage") != JETON or (origine and origine.split("//", 1)[-1] not in self.hotes):
            return self._json({"erreur": "Jeton absent ou origine refusée."}, 403)
        try:
            longueur = min(int(self.headers.get("Content-Length") or 0), 20000)
            corps = json.loads(self.rfile.read(longueur) or b"{}")
        except ValueError:
            return self._json({"erreur": "Requête illisible."}, 400)
        if self.path == "/api/surveillant/demarrer":
            reponse = demarrer(int(corps.get("duree", 60)), bool(corps.get("relectures", True)))
        elif self.path == "/api/surveillant/arreter":
            reponse = arreter()
        elif self.path == "/api/decision":
            reponse = decision(str(corps.get("cle", "")), str(corps.get("action", "")), str(corps.get("texte", "")))
        elif self.path == "/api/consigne":
            reponse = consigne(str(corps.get("agent", "")), str(corps.get("texte", "")))
        else:
            return self._json({"erreur": "Commande inconnue."}, 404)
        self._json(reponse, 409 if "erreur" in reponse else 200)


def avis_windows(texte: str) -> None:
    """Avis Windows ; le texte (titre GitHub) passe par une variable d'environnement, jamais dans la commande."""
    if os.name != "nt":
        return
    commande = ("Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
                "$i = New-Object System.Windows.Forms.NotifyIcon; $i.Icon = [System.Drawing.SystemIcons]::Information; "
                "$i.Visible = $true; $i.ShowBalloonTip(10000, 'MakyClimat', $env:MAKYCLIMAT_AVIS, 'Info'); "
                "Start-Sleep -Seconds 11; $i.Dispose()")
    subprocess.Popen(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", commande],
                     env=dict(os.environ, MAKYCLIMAT_AVIS=texte[:200]), creationflags=subprocess.CREATE_NO_WINDOW)


def suivre_github():
    """Toutes les 20 s : runs et jobs ; toutes les 2 min : mois de la release R-21."""
    cycle = 0
    while True:
        github_direct.actualiser(avis=avis_windows, avec_release=cycle % 6 == 0, echec=echec_run)
        cycle += 1
        time.sleep(20)


def regenerer():
    while True:
        try:
            tableau_de_bord.generer()
        except Exception as erreur:                 # une source illisible ne doit pas arrêter le serveur
            print("Tableau de bord :", erreur, flush=True)
        time.sleep(tableau_de_bord.PERIODE_S)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--sans-navigateur", action="store_true")
    a = ap.parse_args()
    adresse = f"http://127.0.0.1:{a.port}/tableau_de_bord.html"
    try:
        serveur = ThreadingHTTPServer(("127.0.0.1", a.port), partial(Gestionnaire, directory=str(PIL)))
    except OSError:
        print(f"Port {a.port} occupé : le serveur tourne sans doute déjà. Ouverture de {adresse}")
        if not a.sans_navigateur:
            webbrowser.open(adresse)
        return
    Gestionnaire.hotes = {f"127.0.0.1:{a.port}", f"localhost:{a.port}"}
    tableau_de_bord.generer()
    threading.Thread(target=regenerer, daemon=True).start()
    threading.Thread(target=suivre_github, daemon=True).start()
    print(f"Tableau de bord : {adresse}\nFermer cette fenêtre arrête le serveur (le surveillant continue jusqu'à sa durée maximale).",
          flush=True)
    if not a.sans_navigateur:
        webbrowser.open(adresse)
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
