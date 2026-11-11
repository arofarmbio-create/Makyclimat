"""Poste de pilotage : une seule page pour voir et piloter Claude, Codex et leurs sessions enfants (porteur, 11/11/2026).

Ce module rassemble, sans modèle ni appel réseau, ce que la page `pilotage/poste.html` affiche toutes les 10 s :
  - l'état du serveur et du surveillant, les décisions attendues du porteur et les exécutions en file ;
  - pour Claude et Codex (sessions mères) : charge du contexte, dernières actions, tâches ouvertes ;
  - les sessions enfants (relectures, exécutions, réveils lancés par le surveillant ; sous-agents de Claude) avec leur
    sujet en clair, leur durée, leurs jetons et leur résultat ;
  - la consommation du jour, les plafonds des lancements automatiques et les runs GitHub ;
  - la messagerie porteur ↔ sessions mères (pilotage/etat/messages_porteur.jsonl, local, ignoré par Git).

Une session mère ouverte dans sa fenêtre ne peut pas recevoir de texte de l'extérieur : un message du porteur lui est
remis par son crochet à sa prochaine action (Claude : hook_alertes_claude.py ; Codex : hook_actions_codex.py).
Elle répond avec :  .venv/Scripts/python.exe -B -X utf8 scripts/pilotage/poste.py repondre <claude|codex> <id> "texte"
"""
from __future__ import annotations

import argparse
import json
import re
import secrets
import sqlite3
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conversations  # noqa: E402
from surveiller_coordination import (ARRETE, NAIROBI, PLAFOND_JOUR, cle_message, genre_lancement,  # noqa: E402
                                     lire_instance, nom_fichier)

ROOT = Path(__file__).resolve().parents[2]
ETAT = ROOT / "pilotage" / "etat"
COORD_DIR = ETAT / "coordination"
BASE = COORD_DIR / "coordination.sqlite3"
MESSAGES = ETAT / "messages_porteur.jsonl"
AGENTS_JSONL = ETAT / "agents.jsonl"
COORD = ROOT / "COORDINATION.md"
_verrou = threading.Lock()
AGENTS = ("claude", "codex")
NOMS = {"claude": "Claude", "codex": "Codex"}


# ------------------------------------------------------------------ messagerie porteur ↔ sessions mères
def _messages() -> list[dict]:
    try:
        lignes = MESSAGES.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    sortie = []
    for ligne in lignes:
        try:
            sortie.append(json.loads(ligne))
        except ValueError:
            pass
    return sortie


def _ajouter(entree: dict) -> None:
    MESSAGES.parent.mkdir(parents=True, exist_ok=True)
    with _verrou, MESSAGES.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entree, ensure_ascii=False) + "\n")


def maintenant() -> str:
    return datetime.now(NAIROBI).strftime("%d/%m/%Y %H:%M")


def envoyer(agent: str, texte: str) -> dict:
    """Message du porteur à une session mère ; remis par son crochet à sa prochaine action."""
    texte = " ".join(str(texte or "").split())[:3000]
    if agent not in AGENTS or not texte:
        return {"erreur": "Choisir Claude ou Codex et écrire un message."}
    ident = datetime.now(NAIROBI).strftime("%H%M%S-") + secrets.token_hex(2)
    _ajouter({"id": ident, "quand": maintenant(), "de": "porteur", "a": agent, "texte": texte})
    return {"ok": f"Message déposé pour {NOMS[agent]} : il lui sera remis à sa prochaine action.", "id": ident}


def repondre(agent: str, ident: str, texte: str) -> dict:
    texte = " ".join(str(texte or "").split())[:3000]
    if agent not in AGENTS or not texte:
        return {"erreur": "Agent inconnu ou réponse vide."}
    _ajouter({"id": ident, "quand": maintenant(), "de": agent, "a": "porteur", "texte": texte})
    return {"ok": "Réponse inscrite dans le poste de pilotage."}


def marquer_remis(agent: str, idents: list[str]) -> None:
    for ident in idents:
        _ajouter({"id": ident, "quand": maintenant(), "de": agent, "a": "porteur", "remis": True})


def a_remettre(agent: str) -> list[dict]:
    """Messages du porteur pour cet agent, pas encore remis à sa session mère."""
    remis = {m["id"] for m in _messages() if m.get("de") == agent and (m.get("remis") or m.get("texte"))}
    return [m for m in _messages() if m.get("de") == "porteur" and m.get("a") == agent and m["id"] not in remis]


def texte_remise(agent: str, liste: list[dict]) -> str:
    lignes = "\n".join(f"- [{m['id']}] {m['quand']} : {m['texte']}" for m in liste)
    return (f"Message(s) du porteur du projet depuis le poste de pilotage, pour {NOMS[agent]} (session mère) :\n{lignes}\n"
            f"Traite-les, puis réponds-lui dans le poste avec : .venv/Scripts/python.exe -B -X utf8 "
            f"scripts/pilotage/poste.py repondre {agent} <id> \"ta réponse en une à trois phrases\"")


def fil(n: int = 40) -> list[dict]:
    """Fil porteur ↔ sessions mères, du plus récent au plus ancien, avec l'état de remise de chaque message."""
    tous = _messages()
    remis = {(m["de"], m["id"]) for m in tous if m.get("remis")}
    reponses = {(m["de"], m["id"]) for m in tous if m.get("a") == "porteur" and m.get("texte")}
    sortie = []
    for m in tous:
        if not m.get("texte"):
            continue
        e = dict(m)
        if m["de"] == "porteur":
            e["etat"] = ("répondu" if (m["a"], m["id"]) in reponses else
                         "remis" if (m["a"], m["id"]) in remis else "en attente de remise")
        sortie.append(e)
    return sortie[-n:][::-1]


# ------------------------------------------------------------------ sessions enfants
JETONS = re.compile(r"entrée ([\d\s  ]+)\(dont cache ([\d\s  ]+)\) · sortie ([\d\s  ]+)(?:· ([\d.]+) \$)?")


def _nombre(t: str) -> int:
    return int(re.sub(r"\D", "", t) or 0)


def lire_jetons(conso: str | None) -> dict:
    m = JETONS.search(conso or "")
    if not m:
        return {}
    return {"entree": _nombre(m[1]), "cache": _nombre(m[2]), "sortie": _nombre(m[3]),
            "cout": float(m[4]) if m[4] else None}


def _date(texte: str | None) -> datetime | None:
    try:
        return datetime.strptime(texte or "", "%d/%m/%Y %H:%M").replace(tzinfo=NAIROBI)
    except ValueError:
        return None


def _agent_de(identifiant: str, agent: str | None) -> str:
    return agent or ("codex" if identifiant.startswith("codex/") else "claude")


def enfants(jour: str | None = None, minimum: int = 25) -> list[dict]:
    """Lancements du surveillant : ceux du jour, et au moins les `minimum` derniers."""
    if not BASE.exists():
        return []
    jour = jour or maintenant()[:10]
    try:
        db = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
        try:
            colonnes = {c[1] for c in db.execute("PRAGMA table_info(lancements)")}
            champs = ", ".join(c if c in colonnes else f"NULL AS {c}"
                               for c in ("id", "debut", "fin", "statut", "consommation", "agent", "genre", "sujet"))
            rangs = db.execute(f"SELECT {champs} FROM lancements ORDER BY rowid DESC LIMIT 400").fetchall()
        finally:
            db.close()
    except sqlite3.Error:
        return []
    sortie = []
    for i, (ident, debut, fin, statut, conso, agent, genre, sujet) in enumerate(rangs):
        if i >= minimum and not (debut or "").startswith(jour):
            break
        d, f = _date(debut), _date(fin)
        duree = None
        if d:
            duree = int(((f or datetime.now(NAIROBI)) - d).total_seconds() // 60)
        sortie.append({"id": ident, "agent": _agent_de(ident, agent), "genre": genre or genre_lancement(ident),
                       "sujet": sujet or "", "debut": debut or "", "fin": fin or "", "statut": statut,
                       "duree_min": duree, "jetons": lire_jetons(conso), "fichier": nom_fichier(ident),
                       "du_jour": (debut or "").startswith(jour)})
    return sortie


def sous_agents(jour_iso: str | None = None) -> list[dict]:
    """Sous-agents de Claude (outil Agent) du jour, d'après le crochet hook_agents.py. Les débuts (PreToolUse, avec la
    description) et les fins (SubagentStop) sont appariés dans l'ordre, par session : approximation suffisante pour
    savoir combien tournent et sur quoi. Jetons non mesurés par le crochet."""
    jour_iso = jour_iso or datetime.now().strftime("%Y-%m-%d")
    try:
        lignes = AGENTS_JSONL.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    debuts, fins = {}, {}
    for ligne in lignes:
        try:
            r = json.loads(ligne)
        except ValueError:
            continue
        if not str(r.get("quand", "")).startswith(jour_iso):
            continue
        if r.get("evenement") == "PreToolUse":
            debuts.setdefault(r.get("session", ""), []).append(r)
        elif r.get("evenement") == "SubagentStop":
            fins.setdefault(r.get("session", ""), []).append(r)
    sortie = []
    for session, liste in debuts.items():
        arrets = fins.get(session, [])
        for k, r in enumerate(liste):
            fin = arrets[k]["quand"] if k < len(arrets) else ""
            sortie.append({"agent": "claude", "genre": "sous-agent", "sujet": r.get("description") or "(sans description)",
                           "type": r.get("type") or "", "debut": r["quand"][11:16], "fin": fin[11:16],
                           "statut": "Terminé" if fin else "En cours", "session": session[:8],
                           "arriere_plan": bool(r.get("arriere_plan"))})
    return sorted(sortie, key=lambda s: s["debut"], reverse=True)


def detail(ident: str) -> dict:
    """Consigne et résultat d'une session enfant (le fichier de résultat écrit par le surveillant)."""
    if not re.fullmatch(r"[a-z]+(/[a-z]+-[A-Za-z0-9-]{1,80}|-[A-Za-z0-9-]{1,80})", ident or ""):
        return {"erreur": "Identifiant invalide."}
    consigne = ""
    try:
        db = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
        try:
            if "consigne" in {c[1] for c in db.execute("PRAGMA table_info(lancements)")}:
                consigne = (db.execute("SELECT consigne FROM lancements WHERE id = ?", (ident,)).fetchone() or ("",))[0] or ""
        finally:
            db.close()
    except sqlite3.Error:
        pass
    try:
        resultat = (COORD_DIR / nom_fichier(ident)).read_text(encoding="utf-8", errors="replace")
    except OSError:
        resultat = ""
    return {"id": ident, "consigne": consigne[:6000], "resultat": resultat[:15000]}


def arreter_enfant(ident: str) -> dict:
    """Arrête la session enfant en cours : marque le lancement, puis arrête les processus Claude ou Codex enfants du
    surveillant. Le surveillant conserve le statut « Arrêté par le porteur » et passe à la suite."""
    import subprocess
    instance = lire_instance(COORD_DIR)
    if not instance:
        return {"erreur": "Le surveillant ne tourne pas : aucune session enfant à arrêter."}
    db = sqlite3.connect(BASE)          # fermé explicitement : « with » laisserait le fichier verrouillé sous Windows
    try:
        with db:
            n = db.execute("UPDATE lancements SET statut = ? WHERE id = ? AND statut = 'En cours'", (ARRETE, ident)).rowcount
    finally:
        db.close()
    if not n:
        return {"erreur": "Cette session n'est plus en cours."}
    table = conversations.processus()
    pere = int(instance["pid"])
    cibles = [pid for pid, (ppid, nom) in table.items() if ppid == pere and nom in ("claude.exe", "codex.exe", "node.exe")]
    for pid in cibles:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return {"ok": f"Session arrêtée ({len(cibles)} processus)." if cibles else
            "Lancement marqué arrêté ; aucun processus enfant trouvé (déjà terminé ?)."}


# ------------------------------------------------------------------ coordination
COULEUR = (("fait", "ok"), ("à relire", "info"), ("en cours", "info"), ("bloqué", "ko"), ("en attente", "warn"),
           ("prêt", "ok"), ("à faire", "neutre"))


def _nettoyer(t: str, n: int = 260) -> str:
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t).replace("**", "").replace("`", "")
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + " …"


def coordination() -> dict:
    try:
        texte = COORD.read_text(encoding="utf-8-sig")
    except OSError:
        return {"taches": [], "decisions": [], "executions": [], "pause": False}
    taches, decisions, executions, section = [], [], [], ""
    for ligne in texte.splitlines():
        if ligne.startswith("## "):
            section = ligne[3:].strip()
        elif section == "Tâches" and ligne.startswith("| ") and not re.match(r"^\|[\s\-:|]+\|$", ligne):
            c = [x.strip() for x in re.split(r"(?<!\\)\|", ligne)[1:-1]]
            if len(c) >= 5 and c[0] != "Tâche" and not c[2].casefold().startswith(("fait", "clos")):
                etat = c[2]
                taches.append({"tache": _nettoyer(c[0], 140), "responsable": c[1], "etat": _nettoyer(etat, 60),
                               "couleur": next((k for e, k in COULEUR if etat.casefold().startswith(e)), "neutre"),
                               "suite": _nettoyer(c[4]), "debut": c[5] if len(c) > 5 else ""})
        elif section.startswith("Messages") and (m := re.match(r"^- \*\*(.+?)\*\*(.*)", ligne)):
            parties = [p.strip() for p in m.group(1).split("·")]
            if len(parties) >= 3 and "→" in parties[1]:
                auteur, dest = (p.strip() for p in parties[1].split("→", 1))
                decisions.append({"cle": cle_message(ligne), "date": parties[0], "auteur": auteur, "destinataire": dest,
                                  "pour_porteur": "porteur" in dest.casefold(),
                                  "objet": _nettoyer(" · ".join(parties[2:]).rstrip("."), 200),
                                  "detail": _nettoyer(m.group(2).strip(), 700)})
        elif section == "Exécutions autorisées" and (m := re.match(r"^- \[ \] `exec:(claude|codex):([^`]+)` (.*)", ligne)):
            executions.append({"agent": m.group(1), "id": m.group(2), "demande": _nettoyer(m.group(3), 300)})
    return {"taches": taches, "decisions": decisions, "executions": executions,
            "pause": any(l.startswith("> **Pilotage en pause") for l in texte.splitlines())}


# ------------------------------------------------------------------ synthèse
def consommation(liste: list[dict]) -> dict:
    sortie = {a: {"sessions": 0, "entree": 0, "cache": 0, "sortie": 0, "cout": 0.0, "par_genre": {}} for a in AGENTS}
    for e in liste:
        if not e["du_jour"]:
            continue
        s = sortie[e["agent"]]
        s["sessions"] += 1
        s["par_genre"][e["genre"]] = s["par_genre"].get(e["genre"], 0) + 1
        for k in ("entree", "cache", "sortie"):
            s[k] += e["jetons"].get(k, 0)
        s["cout"] += e["jetons"].get("cout") or 0.0
    for s in sortie.values():
        s["cout"] = round(s["cout"], 2)
    return sortie


def plafonds(conso: dict) -> dict:
    return {a: {g: {"utilise": conso[a]["par_genre"].get(g, 0), "max": m} for g, m in PLAFOND_JOUR.items()}
            for a in AGENTS}


def github_instantane() -> dict:
    """Dernier relevé GitHub enregistré (pilotage/etat/github_direct.json) : affiché dès l'ouverture, avant le premier
    relevé du serveur qui vient de démarrer."""
    try:
        return json.loads((ETAT / "github_direct.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def instantane(actions: dict | None = None, github: dict | None = None) -> dict:
    liste = enfants()
    conso = consommation(liste)
    coord = coordination()
    surveillant = lire_instance(COORD_DIR)
    if not surveillant:          # une session « En cours » sans surveillant vient d'une boucle arrêtée : elle ne tourne plus
        for e in liste:
            if e["statut"] == "En cours":
                e["statut"], e["duree_min"] = "Interrompu (surveillant arrêté)", None
    meres = {}
    for agent in AGENTS:
        a = (actions or {}).get(agent) or {}
        meres[agent] = {"etat": a.get("etat", "inconnu"), "actions": (a.get("actions") or [])[:8],
                        "charge": a.get("charge") or conversations.charge(agent),
                        "nouvelle_conversation": a.get("nouvelle_conversation", ""),
                        "taches": [t for t in coord["taches"] if NOMS[agent].casefold() in t["responsable"].casefold()],
                        "messages_en_attente": len(a_remettre(agent))}
    return {"heure": datetime.now(NAIROBI).strftime("%H:%M:%S"), "date": maintenant()[:10],
            "surveillant": {"actif": bool(surveillant), **({k: surveillant[k] for k in ("fin", "debut") if k in surveillant}
                                                           if surveillant else {})},
            "pause": coord["pause"],
            "decisions": [d for d in coord["decisions"] if d["pour_porteur"]],
            "messages_assistants": [d for d in coord["decisions"] if not d["pour_porteur"]][:8],
            "executions": coord["executions"], "meres": meres, "enfants": liste[:60], "sous_agents": sous_agents()[:30],
            "en_cours": [e for e in liste if e["statut"] == "En cours"], "consommation": conso,
            "plafonds": plafonds(conso), "fil": fil(), "github": github if github and github.get("runs") else github_instantane(),
            "porteur_taches": [t for t in coord["taches"] if "porteur" in t["responsable"].casefold()]}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Messagerie du poste de pilotage")
    sous = ap.add_subparsers(dest="action", required=True)
    r = sous.add_parser("repondre", help="répondre au porteur depuis une session mère")
    r.add_argument("agent", choices=AGENTS)
    r.add_argument("id")
    r.add_argument("texte")
    e = sous.add_parser("ecrire", help="écrire au porteur sans répondre à un message précis")
    e.add_argument("agent", choices=AGENTS)
    e.add_argument("texte")
    sous.add_parser("instantane", help="afficher la synthèse JSON")
    a = ap.parse_args()
    if a.action == "repondre":
        print(json.dumps(repondre(a.agent, a.id, a.texte), ensure_ascii=False))
    elif a.action == "ecrire":
        print(json.dumps(repondre(a.agent, "spontane-" + secrets.token_hex(2), a.texte), ensure_ascii=False))
    else:
        print(json.dumps(instantane(), ensure_ascii=False, indent=1)[:6000])


if __name__ == "__main__":
    main()
