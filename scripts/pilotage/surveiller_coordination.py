"""Distribue les alertes locales et exécute les lancements Claude explicitement autorisés."""

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
LANCEMENT = re.compile(r"^- \[ \] `claude:([a-z0-9][a-z0-9-]{0,63})` (.{1,1200})$")


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


def demandes_claude(texte, relectures_auto=False):
    if any(ligne.startswith("> **Pilotage en pause") for ligne in texte.splitlines()):
        return
    section = ""
    for ligne in texte.splitlines():
        if ligne.startswith("## "):
            section = ligne[3:]
        if section == "Lancements ponctuels autorisés" and (match := LANCEMENT.fullmatch(ligne)):
            yield match.groups()
        if relectures_auto and section == "Tâches" and ligne.startswith("| "):
            yield from relecture_auto(ligne)


def relecture_auto(ligne):
    """Une ligne « À relire » dont Claude n'est pas responsable déclenche une relecture en lecture seule.
    L'identifiant dépend du contenu : une nouvelle version de la ligne redemande une relecture, une seule fois."""
    champs = [champ.strip() for champ in re.split(r"(?<!\\)\|", ligne)[1:-1]]
    if len(champs) < 5 or not champs[2].casefold().startswith("à relire") or "claude" in destinataires(champs[1]):
        return
    tache, responsable, _, preuve, suite = champs[:5]
    empreinte = hashlib.sha256(" ".join((tache, preuve, suite)).encode()).hexdigest()[:12]
    yield f"relecture-{empreinte}", (
        f"Relecture automatique de la tâche « {tache} » (responsable : {responsable}), "
        f"passée à « À relire » dans COORDINATION.md. Preuve ou périmètre : {preuve}. "
        f"Point à contrôler : {suite}. Lis les fichiers concernés. Signale chaque point bloquant avec "
        f"fichier:ligne, ou confirme la revue sans blocage. Termine par une ligne « Verdict : sans blocage » "
        f"ou « Verdict : corrections demandées »."
    )


def lancer_claude(db, dossier, demandes, executable):
    """Réserve une demande avant l'appel. Un échec ou un arrêt ne la rejoue pas."""
    for identifiant, consigne in demandes:
        debut = datetime.now(NAIROBI).strftime("%d/%m/%Y %H:%M")
        with db:
            reserve = db.execute(
                """INSERT OR IGNORE INTO lancements
                   SELECT ?, ?, NULL, 'En cours'
                   WHERE NOT EXISTS (SELECT 1 FROM lancements WHERE statut = 'En cours')""",
                (identifiant, debut),
            ).rowcount
        if reserve:
            break
    else:
        return 0

    prompt = (
        "Projet MakyClimat. Intervention en lecture seule, réponse en français et en 250 mots maximum. "
        "Utilise uniquement les fichiers utiles et respecte les règles de COORDINATION.md. "
        "Aucun changement de fichier, téléchargement, workflow, calcul de score ou appel d'un autre agent. "
        "Si une entrée manque, signale le blocage et termine.\n\n" + consigne
    )
    try:
        retour = subprocess.run(
            [str(executable), "-p", "--tools", "Read,Grep,Glob", "--allowedTools", "Read,Grep,Glob",
             "--max-turns", "5"],
            input=prompt, capture_output=True, encoding="utf-8", errors="replace",
            timeout=120, cwd=ROOT, check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        statut = "Réponse reçue" if retour.returncode == 0 and retour.stdout.strip() else "Échec"
        resultat = retour.stdout.strip() if statut == "Réponse reçue" else f"Code de sortie : {retour.returncode}."
    except subprocess.TimeoutExpired:
        statut, resultat = "Délai dépassé", "Claude a été arrêté après 120 secondes."
    except OSError as erreur:
        statut, resultat = "Échec", f"Lancement impossible ({type(erreur).__name__})."

    fin = datetime.now(NAIROBI).strftime("%d/%m/%Y %H:%M")
    ecrire_si_change(
        dossier / f"claude-{identifiant}.md",
        f"# Claude — {identifiant}\n\n{statut} · {debut} → {fin} (Nairobi)\n\n{resultat[:12000]}\n",
    )
    with db:
        db.execute("UPDATE lancements SET fin = ?, statut = ? WHERE id = ?", (fin, statut, identifiant))
        db.execute("INSERT INTO alertes VALUES (?, ?, ?, ?)",
                   (f"lancement:{identifiant}", fin, json.dumps(list(DESTINATAIRES)),
                    f"Claude · {identifiant} · {statut}. Résultat dans les lancements du tableau des alertes."))
    return 1


def verifier(source, dossier, executable=None, relectures_auto=False):
    texte = source.read_text(encoding="utf-8-sig")
    evenements = list(lire_coordination(texte))
    dossier.mkdir(parents=True, exist_ok=True)
    maintenant = datetime.now(NAIROBI).strftime("%d/%m/%Y %H:%M")
    with closing(sqlite3.connect(dossier / "coordination.sqlite3")) as db:
        with db:
            db.execute("CREATE TABLE IF NOT EXISTS etat (id TEXT PRIMARY KEY)")
            db.execute("""CREATE TABLE IF NOT EXISTS alertes (
                id TEXT PRIMARY KEY, date TEXT, cibles TEXT, message TEXT
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS lancements (
                id TEXT PRIMARY KEY, debut TEXT, fin TEXT, statut TEXT NOT NULL
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
        if executable:
            nouvelles += lancer_claude(db, dossier, demandes_claude(texte, relectures_auto), executable)
        alertes = db.execute(
            "SELECT date, cibles, message FROM alertes ORDER BY rowid DESC LIMIT 50"
        ).fetchall()
        lancements = []
        for identifiant, debut, fin, statut in db.execute(
            "SELECT id, debut, fin, statut FROM lancements ORDER BY rowid DESC LIMIT 10"
        ):
            libelle = f"{html.escape(identifiant)} · {html.escape(statut)} · {debut} → {fin or '—'}"
            if fin:
                libelle = f'<a href="claude-{identifiant}.md">{libelle}</a>'
            lancements.append(f"<li>{libelle}</li>")
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
            + "<h2>Lancements Claude</h2><ul>"
            + ("".join(lancements) or "<li>Aucun lancement</li>") + "</ul>"
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


def processus_actif(pid):
    """Vrai si le processus existe encore. Sous Windows, os.kill(pid, 0) le terminerait : on l'interroge sans le toucher."""
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    import ctypes
    noyau = ctypes.windll.kernel32
    poignee = noyau.OpenProcess(0x1000, False, int(pid))   # PROCESS_QUERY_LIMITED_INFORMATION
    if not poignee:
        return False
    code = ctypes.c_ulong()
    try:
        return bool(noyau.GetExitCodeProcess(poignee, ctypes.byref(code))) and code.value == 259   # STILL_ACTIVE
    finally:
        noyau.CloseHandle(poignee)


def lire_instance(dossier):
    """Instance en boucle déclarée dans surveillant.json, ou None si absente ou terminée."""
    try:
        instance = json.loads((dossier / "surveillant.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return None
    return instance if processus_actif(instance.get("pid", 0)) else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boucle", action="store_true")
    parser.add_argument("--duree-minutes", type=int, default=60, help="Durée maximale de la surveillance en boucle")
    parser.add_argument("--claude-exe", type=Path, help="Active les lancements autorisés via le binaire natif Claude")
    parser.add_argument("--relectures-auto", action="store_true",
                        help="Lance aussi une relecture Claude en lecture seule pour chaque ligne « À relire » d'un autre responsable")
    parser.add_argument("--windows", action="store_true", help="Afficher un avis Windows pour les nouvelles alertes")
    parser.add_argument("--source", type=Path, default=ROOT / "COORDINATION.md")
    parser.add_argument("--sortie", type=Path, default=ROOT / "pilotage" / "etat" / "coordination")
    args = parser.parse_args()
    if args.duree_minutes < 1:
        parser.error("--duree-minutes doit être positif")
    if args.claude_exe and (args.claude_exe.suffix.lower() != ".exe" or not args.claude_exe.is_file()):
        parser.error("--claude-exe doit désigner le binaire natif Windows, sans intermédiaire .cmd")
    if args.relectures_auto and not args.claude_exe:
        parser.error("--relectures-auto exige --claude-exe")
    fin = time.monotonic() + args.duree_minutes * 60
    instance = args.sortie / "surveillant.json"
    if args.boucle:
        # Une seule boucle à la fois (remarque de relecture du 09/11 : deux boucles = deux avis).
        args.sortie.mkdir(parents=True, exist_ok=True)
        if (autre := lire_instance(args.sortie)) and autre.get("pid") != os.getpid():
            parser.exit(1, f"Surveillant déjà actif (processus {autre['pid']}, depuis {autre.get('debut')}).\n")
        maintenant = datetime.now(NAIROBI)
        ecrire_si_change(instance, json.dumps({
            "pid": os.getpid(), "debut": maintenant.strftime("%d/%m/%Y %H:%M"),
            "fin_prevue": (maintenant + timedelta(minutes=args.duree_minutes)).strftime("%d/%m/%Y %H:%M"),
            "claude": bool(args.claude_exe), "relectures_auto": args.relectures_auto,
        }, ensure_ascii=False))
        # Un lancement resté « En cours » vient d'une boucle arrêtée de force : il bloquerait toutes les demandes suivantes.
        with closing(sqlite3.connect(args.sortie / "coordination.sqlite3")) as db, db:
            if db.execute("SELECT name FROM sqlite_master WHERE name = 'lancements'").fetchone():
                db.execute("UPDATE lancements SET statut = 'Interrompu', fin = ? WHERE statut = 'En cours'",
                           (maintenant.strftime("%d/%m/%Y %H:%M"),))
    try:
        boucle(args, fin)
    finally:
        if args.boucle:
            instance.unlink(missing_ok=True)


def boucle(args, fin):
    while True:
        try:
            nouvelles = verifier(args.source, args.sortie, args.claude_exe, args.relectures_auto)
            if nouvelles:
                print(f"{nouvelles} nouvelle(s) alerte(s).", flush=True)
                if args.windows and os.name == "nt":
                    notification_windows(nouvelles)
        except (OSError, UnicodeError, sqlite3.Error) as erreur:
            if not args.boucle:
                raise
            print(f"Surveillance : {erreur}", flush=True)
        if not args.boucle or time.monotonic() >= fin:
            return
        time.sleep(min(15, max(0, fin - time.monotonic())))
        if time.monotonic() >= fin:
            return


if __name__ == "__main__":
    main()
