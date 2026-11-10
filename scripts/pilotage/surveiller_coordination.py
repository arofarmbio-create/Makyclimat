"""Distribue les alertes locales, exécute les lancements Claude autorisés et, en option, les relectures croisées Claude/Codex."""

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


AGENTS = {"claude": "Claude", "codex": "Codex"}
EXECUTION = re.compile(r"^- \[ \] `exec:(claude|codex):([a-z0-9][a-z0-9-]{0,63})` (.{1,4000})$")
SUIVI = ("COORDINATION.md", "pilotage/")          # textes de suivi : leur seule modification ne justifie pas une relecture
DIFF_MAX = 15000
CONSIGNE_LECTURE = (
    "Projet MakyClimat. Intervention en lecture seule, réponse en français et en 250 mots maximum. "
    "Respecte les règles de COORDINATION.md. Aucun changement de fichier, téléchargement, workflow, calcul de score "
    "ou appel d'un autre agent. Si une entrée manque, signale le blocage et termine.\n\n")
CONSIGNE_ECRITURE = (
    "Projet MakyClimat. Exécution autorisée par le porteur du projet depuis le tableau de bord. Réponds en français. "
    "Lis les règles de COORDINATION.md et la ligne de tâche concernée, puis respecte-les : une tâche = un responsable, "
    "protocole écrit et analyse de puissance avant tout calcul scientifique, dépôt public (rien de personnel), "
    "un téléchargement à la fois par fournisseur. Limite-toi strictement à la demande ci-dessous. "
    "Au début, passe la ligne de tâche concernée à « En cours » avec l'heure de Nairobi. À la fin, mets-la à jour "
    "(« À relire » si un livrable doit être relu), coche ta ligne `exec:` dans « Exécutions autorisées », lance les "
    "tests concernés, commite avec un message clair et pousse si la demande l'implique. Jamais de push forcé, de "
    "réécriture d'historique ni de suppression de données. S'il manque une décision de fond, arrête-toi et écris un "
    "message au porteur du projet dans « Messages et décisions en attente ». Termine par un résumé de 150 mots au "
    "plus : fait, vérifié, reste à faire.\n\n")


def nom_fichier(identifiant):
    """Résultat d'un lancement : <agent>-<id>.md. Identifiants : r21-x (Claude), codex/relecture-x, claude/exec-x."""
    agent, _, court = identifiant.partition("/") if "/" in identifiant else ("claude", "", identifiant)
    return f"{agent}-{court}.md"


def cle_message(ligne):
    """Clé stable d'un message en attente, partagée par le tableau de bord et le serveur."""
    return hashlib.sha256(" ".join(ligne.split()).encode()).hexdigest()[:12]


def git(*arguments):
    try:
        return subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace",
                              timeout=30, check=False,
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def chemins_cites(*textes):
    """Fichiers du dépôt cités dans une ligne de tâche (liens Markdown ou `code`), hors textes de suivi."""
    vus = []
    for texte in textes:
        for brut in re.findall(r"\]\(([^)#\s]+)|`([^`\s]+)`", texte):
            chemin = (brut[0] or brut[1]).strip()
            if chemin.startswith(("http", "#")) or chemin.startswith(SUIVI) or chemin in vus:
                continue
            if (ROOT / chemin).exists():
                vus.append(chemin)
    return vus


def commit_cite(*textes):
    """Premier commit cité entre accents graves (`00a687a`) : par convention, la version à relire."""
    for texte in textes:
        for candidat in re.findall(r"`([0-9a-f]{7,40})`", texte):
            if git("cat-file", "-t", candidat).strip() == "commit":
                return candidat
    return ""


def contexte_diff(chemins, commit=""):
    """Modifications à relire, complètes : le commit cité, sinon le travail non commité, sinon le dernier commit.
    La troncature se fait après le calcul de l'empreinte (relecture Codex du 10/11 : une correction au-delà de la
    limite ne relançait pas de relecture)."""
    if not chemins:
        return ""
    if commit:
        diff = git("show", "--format=commit %h · %s", commit, "--", *chemins)
        local = git("diff", "HEAD", "--", *chemins)
        return diff + ("\n# Modifications non commitées depuis :\n" + local if local.strip() else "")
    diff = git("diff", "HEAD", "--", *chemins)
    nouveaux = [f for f in git("ls-files", "--others", "--exclude-standard", "--", *chemins).splitlines() if f]
    for fichier in nouveaux:
        try:
            contenu = (ROOT / fichier).read_text(encoding="utf-8")
            diff += f"\n--- nouveau fichier : {fichier}\n" + "".join(f"+{l}\n" for l in contenu.splitlines())
        except (OSError, UnicodeError):
            pass
    if not diff.strip():
        commit = git("log", "-1", "--format=%H", "--", *chemins).strip()
        diff = git("show", "--format=commit %h · %s", commit, "--", *chemins) if commit else ""
    return diff


def tronquer(diff):
    return diff if len(diff) <= DIFF_MAX else diff[:DIFF_MAX] + (
        f"\n[… diff tronqué à {DIFF_MAX} caractères ; ouvrir les fichiers pour la suite]")


def demandes_claude(texte, relectures_auto=False, agents=("claude",)):
    """Demandes à exécuter : (agent, identifiant, consigne). Les exécutions autorisées passent en premier."""
    if any(ligne.startswith("> **Pilotage en pause") for ligne in texte.splitlines()):
        return
    lignes = texte.splitlines()
    section = ""
    for ligne in lignes:
        if ligne.startswith("## "):
            section = ligne[3:]
        if section == "Exécutions autorisées" and (match := EXECUTION.fullmatch(ligne)) and match[1] in agents:
            yield match[1], f"{match[1]}/exec-{match[2]}", match[3]
    section = ""
    for ligne in lignes:
        if ligne.startswith("## "):
            section = ligne[3:]
        if section == "Lancements ponctuels autorisés" and (match := LANCEMENT.fullmatch(ligne)) and "claude" in agents:
            yield ("claude", *match.groups())
        if relectures_auto and section == "Tâches" and ligne.startswith("| "):
            for agent in agents:
                yield from relecture_auto(ligne, agent)


def relecture_auto(ligne, relecteur="claude"):
    """Une ligne « À relire » de l'autre assistant déclenche une relecture en lecture seule par le relecteur.
    Le diff des fichiers cités est fourni d'emblée (économie de tokens) et l'identifiant dépend de ce diff :
    reformuler la ligne ne relance rien, une nouvelle modification du code relance une relecture."""
    champs = [champ.strip() for champ in re.split(r"(?<!\\)\|", ligne)[1:-1]]
    if len(champs) < 5 or not champs[2].casefold().startswith("à relire"):
        return
    responsables = destinataires(champs[1])
    autre = "codex" if relecteur == "claude" else "claude"
    if relecteur in responsables or autre not in responsables:
        return
    tache, responsable, _, preuve, suite = champs[:5]
    chemins = chemins_cites(preuve, suite)
    if not chemins:            # rien d'autre que du suivi : pas de relecture automatique
        return
    diff = contexte_diff(chemins, commit_cite(preuve, suite))
    # Empreinte sur les seules lignes ajoutées ou retirées : commiter un travail déjà relu ne relance pas de relecture.
    modifiees = "\n".join(l for l in diff.splitlines() if l[:1] in "+-" and not l.startswith(("+++", "---")))
    empreinte = hashlib.sha256(" ".join((tache, modifiees or "|".join(chemins))).encode()).hexdigest()[:12]
    identifiant = f"relecture-{empreinte}" if relecteur == "claude" else f"codex/relecture-{empreinte}"
    diff = tronquer(diff)
    yield relecteur, identifiant, (
        f"Relecture automatique de la tâche « {tache} » (responsable : {responsable}), passée à « À relire » dans "
        f"COORDINATION.md. Point à contrôler : {suite}\n\nFichiers concernés : {', '.join(chemins)}.\n"
        f"Base-toi d'abord sur les modifications ci-dessous ; n'ouvre un fichier que pour vérifier un point précis "
        f"(contexte, appelant, test). Signale chaque point bloquant avec fichier:ligne, ou confirme la revue. "
        f"Termine par « Verdict : sans blocage » ou « Verdict : corrections demandées ». Si un outil t'empêche de "
        f"lire et que le diff ci-dessous ne suffit pas pour juger, termine par « Verdict : relecture impossible » : "
        f"un problème d'environnement n'est jamais une demande de correction.\n\n"
        f"```diff\n{diff or '(aucune modification trouvée)'}\n```"
    )


def commande_agent(agent, executable, sortie, ecriture):
    """Commande et délai. Sorties JSON pour relever la consommation de tokens."""
    if agent == "codex":
        bac = ["-s", "workspace-write", "-c", "sandbox_workspace_write.network_access=true"] if ecriture else ["-s", "read-only"]
        return ([str(executable), "exec", *bac, "-C", str(ROOT), "--ephemeral", "--skip-git-repo-check", "--json",
                 "-o", str(sortie), "-"], 1800 if ecriture else 300)
    if ecriture:
        return ([str(executable), "-p", "--output-format", "json", "--permission-mode", "acceptEdits",
                 "--allowedTools", "Read,Grep,Glob,Edit,Write,Bash(git:*),Bash(gh:*),Bash(.venv/Scripts/python.exe:*)",
                 "--disallowedTools", "Bash(git push --force:*),Bash(git push -f:*),Bash(git reset --hard:*),"
                 "Bash(git clean:*),Bash(git rebase:*),Bash(gh repo delete:*),Bash(gh release delete:*)",
                 "--max-turns", "80"], 1800)
    return ([str(executable), "-p", "--output-format", "json", "--tools", "Read,Grep,Glob",
             "--allowedTools", "Read,Grep,Glob", "--max-turns", "5"], 120)


def milliers(n):
    return f"{int(n):,}".replace(",", " ")


def lire_sortie(agent, stdout, sortie):
    """(texte de la réponse, consommation lisible) à partir des sorties JSON de Claude ou de Codex."""
    if agent == "codex":
        entree = cache = sortie_t = 0
        for ligne in stdout.splitlines():
            try:
                evenement = json.loads(ligne)
            except ValueError:
                continue
            usage = evenement.get("usage") if isinstance(evenement, dict) else None
            if isinstance(usage, dict) and evenement.get("type", "").endswith("completed"):
                entree += usage.get("input_tokens", 0)
                cache += usage.get("cached_input_tokens", 0)
                sortie_t += usage.get("output_tokens", 0)
        texte = sortie.read_text(encoding="utf-8", errors="replace").strip() if sortie.exists() else ""
        conso = (f"entrée {milliers(entree)} (dont cache {milliers(cache)}) · sortie {milliers(sortie_t)}"
                 if entree or sortie_t else "non communiquée")
        return texte, conso
    try:
        donnees = json.loads(stdout)
    except ValueError:
        return stdout.strip(), "non communiquée"
    usage = donnees.get("usage") or {}
    entree = usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)
    cache = usage.get("cache_read_input_tokens", 0)
    conso = (f"entrée {milliers(entree + cache)} (dont cache {milliers(cache)}) · sortie "
             f"{milliers(usage.get('output_tokens', 0))}")
    if donnees.get("total_cost_usd") is not None:
        conso += f" · {donnees['total_cost_usd']:.2f} $"
    return str(donnees.get("result") or "").strip(), conso


def lancer_claude(db, dossier, demandes, executables):
    """Réserve une demande avant l'appel. Un échec ou un arrêt ne la rejoue pas. executables : {agent: binaire}."""
    if not isinstance(executables, dict):
        executables = {"claude": executables}
    for agent, identifiant, consigne in demandes:
        if not executables.get(agent):
            continue
        debut = datetime.now(NAIROBI).strftime("%d/%m/%Y %H:%M")
        with db:
            reserve = db.execute(
                """INSERT OR IGNORE INTO lancements (id, debut, fin, statut)
                   SELECT ?, ?, NULL, 'En cours'
                   WHERE NOT EXISTS (SELECT 1 FROM lancements WHERE statut = 'En cours')""",
                (identifiant, debut),
            ).rowcount
        if reserve:
            break
    else:
        return 0

    nom = AGENTS[agent]
    ecriture = "/exec-" in identifiant
    prompt = (CONSIGNE_ECRITURE if ecriture else CONSIGNE_LECTURE) + consigne
    consommation = "non communiquée"
    with tempfile.TemporaryDirectory() as temporaire:
        sortie = Path(temporaire) / "reponse.md"
        commande, delai = commande_agent(agent, executables[agent], sortie, ecriture)
        try:
            retour = subprocess.run(
                commande, input=prompt, capture_output=True, encoding="utf-8", errors="replace",
                timeout=delai, cwd=ROOT, check=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            texte, consommation = lire_sortie(agent, retour.stdout, sortie)
            statut = "Réponse reçue" if retour.returncode == 0 and texte else "Échec"
            if statut == "Réponse reçue" and "relecture impossible" in texte.casefold():
                statut = "Relecture impossible"
            resultat = texte if statut == "Réponse reçue" else f"Code de sortie : {retour.returncode}. {texte[:2000]}"
        except subprocess.TimeoutExpired:
            statut, resultat = "Délai dépassé", f"{nom} a été arrêté après {delai} secondes."
        except OSError as erreur:
            statut, resultat = "Échec", f"Lancement impossible ({type(erreur).__name__})."

    fin = datetime.now(NAIROBI).strftime("%d/%m/%Y %H:%M")
    court = identifiant.rpartition("/")[2]
    genre = "Exécution" if ecriture else "Relecture ou demande en lecture seule"
    ecrire_si_change(dossier / nom_fichier(identifiant),
                     f"# {nom} — {court}\n\n{genre} · {statut} · {debut} → {fin} (Nairobi) · tokens : {consommation}"
                     f"\n\n{resultat[:12000]}\n")
    with db:
        db.execute("UPDATE lancements SET fin = ?, statut = ?, consommation = ? WHERE id = ?",
                   (fin, statut, consommation, identifiant))
        db.execute("INSERT INTO alertes VALUES (?, ?, ?, ?)",
                   (f"lancement:{identifiant}", fin, json.dumps(list(DESTINATAIRES)),
                    f"{nom} · {court} · {statut} · tokens : {consommation}. Résultat dans les lancements du tableau des alertes."))
    return 1


def verifier(source, dossier, executable=None, relectures_auto=False, codex=None):
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
                id TEXT PRIMARY KEY, debut TEXT, fin TEXT, statut TEXT NOT NULL, consommation TEXT
            )""")
            if "consommation" not in {c[1] for c in db.execute("PRAGMA table_info(lancements)")}:
                db.execute("ALTER TABLE lancements ADD COLUMN consommation TEXT")
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
        if executable or codex:
            executables = {"claude": executable, "codex": codex}
            agents = tuple(agent for agent, binaire in executables.items() if binaire)
            nouvelles += lancer_claude(db, dossier, demandes_claude(texte, relectures_auto, agents), executables)
        alertes = db.execute(
            "SELECT date, cibles, message FROM alertes ORDER BY rowid DESC LIMIT 50"
        ).fetchall()
        lancements = []
        for identifiant, debut, fin, statut, consommation in db.execute(
            "SELECT id, debut, fin, statut, consommation FROM lancements ORDER BY rowid DESC LIMIT 20"
        ):
            libelle = (f"{html.escape(identifiant)} · {html.escape(statut)} · {debut} → {fin or '—'}"
                       + (f" · tokens : {html.escape(consommation)}" if consommation else ""))
            if fin:
                libelle = f'<a href="{nom_fichier(identifiant)}">{libelle}</a>'
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
            + "<h2>Lancements Claude et Codex</h2><ul>"
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
    parser.add_argument("--codex-exe", type=Path, help="Active les relectures automatiques par Codex (codex exec, lecture seule)")
    parser.add_argument("--relectures-auto", action="store_true",
                        help="Relectures croisées en lecture seule : Claude relit les lignes « À relire » de Codex, "
                             "Codex celles de Claude (si --codex-exe)")
    parser.add_argument("--windows", action="store_true", help="Afficher un avis Windows pour les nouvelles alertes")
    parser.add_argument("--source", type=Path, default=ROOT / "COORDINATION.md")
    parser.add_argument("--sortie", type=Path, default=ROOT / "pilotage" / "etat" / "coordination")
    args = parser.parse_args()
    if args.duree_minutes < 1:
        parser.error("--duree-minutes doit être positif")
    if args.claude_exe and (args.claude_exe.suffix.lower() != ".exe" or not args.claude_exe.is_file()):
        parser.error("--claude-exe doit désigner le binaire natif Windows, sans intermédiaire .cmd")
    if args.codex_exe and not args.codex_exe.is_file():
        parser.error("--codex-exe doit désigner le binaire codex.exe")
    if args.relectures_auto and not (args.claude_exe or args.codex_exe):
        parser.error("--relectures-auto exige --claude-exe ou --codex-exe")
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
            "claude": bool(args.claude_exe), "codex": bool(args.codex_exe), "relectures_auto": args.relectures_auto,
        }, ensure_ascii=False))
        # Un lancement resté « En cours » vient d'une boucle arrêtée de force : il bloquerait toutes les demandes suivantes.
        with closing(sqlite3.connect(args.sortie / "coordination.sqlite3")) as db, db:
            if db.execute("SELECT name FROM sqlite_master WHERE name = 'lancements'").fetchone():
                db.execute("UPDATE lancements SET statut = 'Interrompu', fin = ? WHERE statut = 'En cours'",
                           (maintenant.strftime("%d/%m/%Y %H:%M"),))
                # Une relecture empêchée par l'environnement est retentée une fois à chaque démarrage (pas en boucle).
                db.execute("""DELETE FROM lancements WHERE id LIKE '%relecture-%'
                              AND statut IN ('Relecture impossible', 'Échec', 'Délai dépassé', 'Interrompu')""")
    try:
        boucle(args, fin)
    finally:
        if args.boucle:
            instance.unlink(missing_ok=True)


def boucle(args, fin):
    while True:
        try:
            nouvelles = verifier(args.source, args.sortie, args.claude_exe, args.relectures_auto, args.codex_exe)
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
