"""Fil des tâches (pilotage/fil.yml, local) : lecture, étapes prêtes, prochaine étape de la boucle, liste du porteur.

Décision du porteur du 13/11/2026 (coordination/proposition_systeme.md, § 11, point 6 ; délégation :
coordination/delegation.md). Le fil est la source unique ; ce module ne fait que le lire et changer l'état d'une étape.

Usage : .venv/Scripts/python.exe -B -X utf8 scripts/pilotage/fil.py [--porteur | --prochaine | --resume]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
FIL = ROOT / "pilotage" / "fil.yml"
COORDINATEUR = ROOT / "pilotage" / "etat" / "coordinateur.txt"
FIN_PAUSE = date(2026, 11, 16)        # pause des calculs de recherche décidée par le porteur (13/11/2026)
AUTONOMES = {"claude", "codex", "coordinateur", "agent", "github"}
FINIS = {"fait", "clos"}
ACTIFS = {"en_cours", "a_relire", "decision"}


def charger(chemin: Path = FIL) -> dict:
    return yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}


def etapes(fil: dict) -> list[dict]:
    """Toutes les étapes, dans l'ordre du fichier, avec leur objectif ou démarche et sa priorité."""
    sortie = []
    for groupe in fil.get("demarches", []):
        for e in groupe.get("etapes", []):
            sortie.append({**e, "_groupe": groupe["id"], "_priorite": 0, "_domaine": "demarche"})
    for o in fil.get("objectifs", []):
        for e in o.get("etapes", []):
            sortie.append({**e, "_groupe": o["id"], "_priorite": o.get("priorite", 5), "_domaine": o.get("domaine", "")})
    return sortie


def _termine(ref: str, par_id: dict, donnees: dict, etape_id: str) -> bool:
    if ref in donnees:
        d = donnees[ref]
        return d.get("etat") == "disponible" or (d.get("etat") == "partielle" and etape_id in str(d.get("suffit_pour", "")))
    e = par_id.get(ref)
    if e is None:
        return False
    if e.get("etat") not in FINIS:
        return False
    return e.get("autorisation") != "porteur" or bool(e.get("valide_le"))     # protocole relu ≠ calcul autorisé


def pretes(fil: dict) -> list[dict]:
    """Étapes dont tout l'amont est fait ou disponible (autorisations du porteur comprises), non commencées."""
    tout = etapes(fil)
    par_id = {e["id"]: e for e in tout}
    donnees = {d["id"]: d for d in fil.get("donnees", [])}
    return [e for e in tout if e.get("etat") not in FINIS | ACTIFS
            and all(_termine(r, par_id, donnees, e["id"]) for r in e.get("depend_de", []))]


def a_valider(fil: dict) -> list[dict]:
    """Étapes faites qui exigent la validation du porteur et ne l'ont pas encore."""
    return [e for e in etapes(fil) if e.get("autorisation") == "porteur" and e.get("etat") in FINIS
            and not e.get("valide_le")]


def coordinateur() -> str:
    try:
        nom = COORDINATEUR.read_text(encoding="utf-8").strip().lower()
    except OSError:
        return "claude"
    return nom if nom in ("claude", "codex") else "claude"


def agent_de(etape: dict) -> str:
    """Qui exécute : Codex pour ses étapes, sinon le coordinateur (il lance aussi workflows et téléchargements)."""
    return "codex" if etape.get("qui") == "codex" else coordinateur() if etape.get("qui") != "claude" else "claude"


def prochaine(fil: dict, aujourd_hui: date | None = None) -> dict | None:
    """Première étape prête qu'un assistant peut faire seul, par priorité. Pendant la pause des calculs, seules les
    étapes du système avancent."""
    jour = aujourd_hui or date.today()
    candidates = [e for e in pretes(fil) if e.get("qui") in AUTONOMES
                  and (jour >= FIN_PAUSE or e["_domaine"] == "systeme")]
    candidates.sort(key=lambda e: e["_priorite"])            # tri stable : l'ordre du fichier départage
    return candidates[0] if candidates else None


def pour_porteur(fil: dict) -> dict:
    """Ce qui n'attend que le porteur : ses étapes prêtes, les validations, les démarches chez un partenaire."""
    pret = pretes(fil)
    return {"faire": [e for e in pret if e.get("qui") == "porteur"],
            "valider": a_valider(fil),
            "chez_partenaire": [e for e in etapes(fil) if e.get("qui") == "partenaire" and e.get("etat") == "en_attente"
                                and e["id"] in {p["id"] for p in pret}]}


def resume(fil: dict) -> dict:
    tout = etapes(fil)
    compte: dict[str, int] = {}
    for e in tout:
        compte[e.get("etat", "?")] = compte.get(e.get("etat", "?"), 0) + 1
    return {"etapes": len(tout), "par_etat": compte, "pretes": len(pretes(fil)),
            "en_cours": [e for e in tout if e.get("etat") in ACTIFS]}


def changer(etape_id: str, **champs) -> bool:
    """Change des champs simples (etat, preuve, valide_le…) sur la ligne de l'étape, sans réécrire le reste du fichier
    (commentaires et mise en forme conservés). Chaque étape tient sur une ligne « - {id: …} »."""
    texte = FIL.read_text(encoding="utf-8")
    motif = re.compile(r"^(\s*- \{id: " + re.escape(etape_id) + r",.*)\}\s*$", re.M)
    m = motif.search(texte)
    if not m:
        return False
    ligne = m.group(1)
    for cle, valeur in champs.items():
        rendu = json.dumps(valeur, ensure_ascii=False)       # JSON = YAML valide dans un mapping en ligne
        champ = re.compile(r"(, " + cle + r": )(\"(?:[^\"\\]|\\.)*\"|\[[^\]]*\]|[^,{}]*)")
        ligne = champ.sub(lambda x: x.group(1) + rendu, ligne, count=1) if champ.search(ligne) else f"{ligne}, {cle}: {rendu}"
    nouveau = texte[:m.start(1)] + ligne + texte[m.end(1):]
    relu = next((e for e in etapes(yaml.safe_load(nouveau)) if e["id"] == etape_id), {})
    if any(relu.get(cle) != valeur for cle, valeur in champs.items()):   # relecture : valeur écrite exacte, sinon rien
        raise ValueError(f"Écriture refusée pour {etape_id} : {champs}")
    FIL.write_text(nouveau, encoding="utf-8")
    return True


def ligne_etape(e: dict) -> str:
    return f"{e['id']} — {e.get('quoi', '')}" + (f" ({e['prochaine_action']})" if e.get("prochaine_action") else "")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--porteur", action="store_true")
    ap.add_argument("--prochaine", action="store_true")
    a = ap.parse_args()
    fil = charger()
    if a.porteur:
        p = pour_porteur(fil)
        for titre, cle in (("À faire", "faire"), ("À valider", "valider"), ("Chez un partenaire", "chez_partenaire")):
            print(f"## {titre}")
            for e in p[cle]:
                print(" -", ligne_etape(e))
    elif a.prochaine:
        e = prochaine(fil)
        print(ligne_etape(e) + f" → {agent_de(e)}" if e else "Rien de prêt pour la boucle.")
    else:
        r = resume(fil)
        print(f"{r['etapes']} étapes, {r['pretes']} prêtes ; {r['par_etat']}")


if __name__ == "__main__":
    main()
