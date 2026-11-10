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
import tableau_de_bord  # noqa: E402
from surveiller_coordination import lire_instance  # noqa: E402

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
    """Ligne de commande Codex : sur le PATH, sinon celle installée par l'application Codex."""
    trouve = shutil.which("codex.exe") or shutil.which("codex")
    if trouve and Path(trouve).suffix.lower() == ".exe":
        return Path(trouve)
    natif = Path.home() / ".codex" / ".sandbox-bin" / "codex.exe"
    return natif if natif.is_file() else None


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
        if codex and relectures:
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
        super().do_GET()

    def do_POST(self):
        if not self._local():
            return
        origine = self.headers.get("Origin")
        if self.headers.get("X-Pilotage") != JETON or (origine and origine.split("//", 1)[-1] not in self.hotes):
            return self._json({"erreur": "Jeton absent ou origine refusée."}, 403)
        try:
            longueur = min(int(self.headers.get("Content-Length") or 0), 1000)
            corps = json.loads(self.rfile.read(longueur) or b"{}")
        except ValueError:
            return self._json({"erreur": "Requête illisible."}, 400)
        if self.path == "/api/surveillant/demarrer":
            reponse = demarrer(int(corps.get("duree", 60)), bool(corps.get("relectures", True)))
        elif self.path == "/api/surveillant/arreter":
            reponse = arreter()
        else:
            return self._json({"erreur": "Commande inconnue."}, 404)
        self._json(reponse, 409 if "erreur" in reponse else 200)


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
