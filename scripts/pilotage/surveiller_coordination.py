"""Distribue les changements de COORDINATION.md dans les boîtes locales, sans modèle."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sqlite3
import subprocess
import tempfile
import time
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESTINATAIRES = {"porteur": "Porteur du projet", "claude": "Claude", "codex": "Codex"}
ETATS = ("à relire", "bloqué", "prêt à publier", "fait", "clos")
NAIROBI = timezone(timedelta(hours=3))


def destinataires(texte):
    texte = texte.casefold()
    return {cle for cle, nom in DESTINATAIRES.items() if nom.casefold() in texte}


def lire_coordination(texte):
    """Les messages explicites et les états actionnables sont les seuls signaux."""
    section = ""
    for ligne in texte.splitlines():
        if ligne.startswith("## "):
            section = ligne[3:]
        if section == "Tâches" and ligne.startswith("| "):
            champs = re.split(r"(?<!\\)\|", ligne)[1:-1]
            if len(champs) < 5:
                continue
            tache, responsable, etat, preuve, suite = (champ.strip() for champ in champs[:5])
            if not etat.casefold().startswith(ETATS):
                continue
            cibles = {"porteur"}
            if etat.casefold().startswith("à relire"):
                cibles.update({"claude", "codex"} - destinataires(responsable))
            elif etat.casefold().startswith(("fait", "clos")):
                cibles.update(("claude", "codex"))
            else:
                cibles.update(destinataires(responsable))
            yield "tâche", cibles, f"{etat} · {tache} · {responsable} · {preuve} · {suite}"
        if section == "Messages et décisions en attente" and ligne.startswith("- "):
            message = ligne[2:].replace("**", "")
            adresse = re.search(r"→\s*([^·.]+)", message)
            if adresse and (cibles := destinataires(adresse[1])):
                yield "message", cibles | {"porteur"}, message


def ecrire_si_change(chemin, contenu):
    try:
        if chemin.read_text(encoding="utf-8") == contenu:
            return
    except FileNotFoundError:
        pass
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                     dir=chemin.parent, delete=False) as fichier:
        temporaire = Path(fichier.name)
        fichier.write(contenu)
    try:
        temporaire.replace(chemin)
    finally:
        temporaire.unlink(missing_ok=True)


def verifier(source, dossier):
    evenements = list(lire_coordination(source.read_text(encoding="utf-8-sig")))
    dossier.mkdir(parents=True, exist_ok=True)
    maintenant = datetime.now(NAIROBI).strftime("%d/%m/%Y %H:%M")
    with closing(sqlite3.connect(dossier / "coordination.sqlite3")) as db:
        with db:
            db.execute("CREATE TABLE IF NOT EXISTS etat (id TEXT PRIMARY KEY)")
            db.execute("""CREATE TABLE IF NOT EXISTS alertes (
                id TEXT PRIMARY KEY, date TEXT, cibles TEXT, message TEXT
            )""")
            # Verrouille l'écriture avant de déterminer si une base existe déjà.
            premier = db.execute("INSERT OR IGNORE INTO etat VALUES ('initialisé')").rowcount
            nouvelles = 0
            for genre, cibles, message in evenements:
                cle = hashlib.sha256(" ".join(message.split()).encode()).hexdigest()
                ajoute = db.execute("INSERT OR IGNORE INTO etat VALUES (?)", (cle,)).rowcount
                if ajoute and (not premier or genre == "message"):
                    db.execute("INSERT INTO alertes VALUES (?, ?, ?, ?)",
                               (cle, maintenant, json.dumps(sorted(cibles)), message))
                    nouvelles += int("porteur" in cibles)
            alertes = db.execute(
                "SELECT date, cibles, message FROM alertes ORDER BY rowid DESC LIMIT 50"
            ).fetchall()
        boites = {cle: [] for cle in DESTINATAIRES}
        for date, cibles, message in alertes:
            for cle in json.loads(cibles):
                boites[cle].append((date, message))
        for cle, items in boites.items():
            lignes = [f"# Alertes de coordination — {DESTINATAIRES[cle]}", ""]
            lignes.extend(f"- {date} · {message}" for date, message in items[:10])
            ecrire_si_change(dossier / f"{cle}.md", "\n".join(lignes) + "\n")
        sections = []
        for cle, items in boites.items():
            contenu = "".join(f"<li><time>{date}</time> · {html.escape(message)}</li>"
                              for date, message in items[:10])
            sections.append(f"<section><h2>{DESTINATAIRES[cle]}</h2>"
                            f"<ul>{contenu or '<li>Aucune alerte</li>'}</ul></section>")
        ecrire_si_change(
            dossier / "notifications.html",
            '<!doctype html><html lang="fr"><meta charset="utf-8">'
            '<meta http-equiv="refresh" content="15"><title>Alertes MakyClimat</title>'
            '<style>body{font:16px system-ui;margin:2rem;max-width:70rem}'
            'li{margin:.8rem 0;overflow-wrap:anywhere}time{color:#515966}</style>'
            '<h1>Alertes de coordination</h1><p>Heure de Nairobi. '
            'Historique des notifications. Voir COORDINATION.md pour l’état courant.</p>'
            + "".join(sections) + "</html>",
        )
    return nouvelles


def notification_windows(nombre):
    """Affiche un avis générique, sans transmettre le contenu des messages au shell."""
    commande = """
    Add-Type -AssemblyName System.Windows.Forms,System.Drawing
    $icone = New-Object System.Windows.Forms.NotifyIcon
    $icone.Icon = [System.Drawing.SystemIcons]::Information
    $icone.Visible = $true
    $icone.ShowBalloonTip(8000, 'MakyClimat', $env:MAKYCLIMAT_AVIS, 'Info')
    Start-Sleep -Seconds 9
    $icone.Dispose()
    """
    subprocess.Popen(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", commande],
        env=dict(os.environ, MAKYCLIMAT_AVIS=f"{nombre} nouvelle(s) alerte(s). Voir le tableau de bord."),
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boucle", action="store_true")
    parser.add_argument("--windows", action="store_true", help="Afficher un avis Windows pour les nouvelles alertes")
    parser.add_argument("--source", type=Path, default=ROOT / "COORDINATION.md")
    parser.add_argument("--sortie", type=Path, default=ROOT / "pilotage" / "etat" / "coordination")
    args = parser.parse_args()
    while True:
        try:
            nouvelles = verifier(args.source, args.sortie)
            if nouvelles:
                print(f"{nouvelles} nouvelle(s) alerte(s).", flush=True)
                if args.windows and os.name == "nt":
                    notification_windows(nouvelles)
        except (OSError, UnicodeError, sqlite3.Error) as erreur:
            if not args.boucle:
                raise
            print(f"Surveillance : {erreur}", flush=True)
        if not args.boucle:
            return
        time.sleep(15)


if __name__ == "__main__":
    main()
