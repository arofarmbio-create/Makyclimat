"""Tableau de bord LOCAL de la thèse et de MakyClimat — aucun modèle, aucun token.

Lit (fichiers locaux, hors dépôt) : pilotage/objectifs.yml, pilotage/protocole_suivi.yml, pilotage/glossaire.yml,
pilotage/etat/agents.jsonl (écrit par les hooks de Claude Code) ; et validation/journal_recherche.md (verdicts des
hypothèses), git, GitHub (gh). Écrit : pilotage/tableau_de_bord.html (rafraîchi toutes les 30 s).
Usage : python scripts/pilotage/tableau_de_bord.py            (une fois)
        python scripts/pilotage/tableau_de_bord.py --boucle   (régénère toutes les 30 s ; Ctrl+C pour arrêter)
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import subprocess
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PIL = ROOT / "pilotage"
OUT = PIL / "tableau_de_bord.html"
PERIODE_S, GH_PERIODE_S, ARRET_MIN = 30, 300, 15
_gh_cache: dict = {"t": 0.0, "runs": []}

VERDICT = re.compile(r"\*\*(H-[A-Za-z0-9-]+)[^*]*?(non soutenue|soutenue|robuste|non confirmée|non vérifiée)")
SECTION = re.compile(r"^###\s+(.*)")
FAMILLE = {"H-R": "contrôle de T2 par des bornes africaines (T2c)", "H-L": "T2 corrigée par les mesures malgaches (T2L)",
           "H-K": "karst", "H-Cl": "bilan de chlorure", "H-P": "puits à sec", "H-C": "carte des nappes",
           "H-B": "bassins hydrogéologiques", "H-M": "mémoire du sous-sol (THMS)", "H-N": "océan et nappes"}


def run(cmd: list[str], timeout: int = 20) -> str:
    try:
        return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=timeout).stdout
    except Exception:
        return ""


def lire(nom: str) -> dict:
    try:
        return yaml.safe_load((PIL / nom).read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        return {"erreur": f"{nom} illisible : {e}"}


def agents():
    """Agents en cours (SubagentStart sans SubagentStop), derniers lancements, dernières fins."""
    p = PIL / "etat" / "agents.jsonl"
    rows = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    started, stopped = {}, {}
    for r in rows:
        if r.get("agent_id") and r.get("evenement") == "SubagentStart":
            started[r["agent_id"]] = r
        elif r.get("agent_id") and r.get("evenement") == "SubagentStop":
            stopped[r["agent_id"]] = r
    en_cours = [r for a, r in started.items() if a not in stopped]
    lancements = [r for r in rows if r.get("evenement") == "PreToolUse"][-6:][::-1]
    return en_cours, lancements, list(stopped.values())[-4:][::-1]


def hypotheses() -> list[tuple[str, str, str]]:
    """(section du journal, hypothèse, verdict) ; dernier verdict par couple section-hypothèse."""
    p = ROOT / "validation" / "journal_recherche.md"
    out, sec = {}, ""
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            m = SECTION.match(line)
            if m:
                sec = re.sub(r"\s*\(`.*?`\)", "", m.group(1)).strip()
            for h, v in VERDICT.findall(line):
                out[(sec, h)] = (sec, h, v)
    return list(out.values())


def famille(h: str) -> str:
    for k in sorted(FAMILLE, key=len, reverse=True):
        if h.startswith(k):
            return FAMILLE[k]
    return ""


def github() -> list[dict]:
    if time.time() - _gh_cache["t"] > GH_PERIODE_S:
        txt = run(["gh", "run", "list", "-L", "6", "--json", "displayTitle,workflowName,status,conclusion,createdAt"])
        try:
            _gh_cache["runs"] = json.loads(txt) if txt else []
        except Exception:
            _gh_cache["runs"] = []
        _gh_cache["t"] = time.time()
    return _gh_cache["runs"]


def telechargements(obj: dict) -> list[dict]:
    out = []
    for d in obj.get("telechargements") or []:
        p = ROOT / d.get("chemin", "")
        if p.is_dir():
            fs = [f for f in p.rglob("*") if f.is_file()]
            taille, mtime = sum(f.stat().st_size for f in fs), max((f.stat().st_mtime for f in fs), default=0)
        elif p.exists():
            taille, mtime = p.stat().st_size, p.stat().st_mtime
        else:
            taille, mtime = 0, 0
        att = d.get("taille_attendue")
        age = (time.time() - mtime) / 60 if mtime else None
        if att and taille >= att:
            etat = "fini"
        elif age is None:
            etat = "absent"
        elif age > ARRET_MIN:
            etat = "arrêté" if att else "fini"
        else:
            etat = "en_cours"
        out.append({"nom": d.get("nom", ""), "taille": taille, "attendue": att, "etat": etat,
                    "maj": dt.datetime.fromtimestamp(mtime).strftime("%d/%m %H:%M") if mtime else "-"})
    return out


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


CLS = {"fini": "ok", "soutenue": "ok", "robuste": "ok", "success": "ok",
       "en_cours": "run", "in_progress": "run", "partiel": "warn", "non vérifiée": "warn", "queued": "todo",
       "bloque": "ko", "arrêté": "ko", "non soutenue": "ko", "non confirmée": "ko", "failure": "ko",
       "a_faire": "todo", "absent": "todo"}
LIB = {"fini": "fini", "en_cours": "en cours", "bloque": "bloqué", "a_faire": "à faire", "partiel": "partiel",
       "success": "réussi", "failure": "échec", "in_progress": "en cours", "queued": "en file"}


def badge(etat: str) -> str:
    return f'<span class="b {CLS.get(etat, "todo")}">{esc(LIB.get(etat, etat))}</span>' if etat else ""


def carte(titre: str, sous: str = "", etat: str = "") -> str:
    return f'<div class="card {CLS.get(etat, "todo")}"><div class="t">{esc(titre)} {badge(etat)}</div><div class="s">{esc(sous)}</div></div>'


def table_suivi(rows: list[dict], avec_manque: bool = True) -> str:
    tr = "".join(f'<tr><td class="code">{esc(r.get("code"))}</td><td>{esc(r.get("nom"))}</td><td>{badge(r.get("statut", ""))}</td>'
                 f'<td>{esc(r.get("ou"))}</td>' + (f'<td class="mut">{esc(r.get("manque"))}</td>' if avec_manque else "") + "</tr>"
                 for r in rows)
    head = "<tr><th></th><th>Élément</th><th>État</th><th>Où on en est</th>" + ("<th>Ce qui manque</th>" if avec_manque else "") + "</tr>"
    return f"<table>{head}{tr}</table>"


def jauge(rows: list[dict]) -> str:
    poids = {"fini": 1.0, "en_cours": 0.6, "partiel": 0.4, "a_faire": 0.0, "bloque": 0.0}
    if not rows:
        return ""
    v = 100 * sum(poids.get(r.get("statut"), 0) for r in rows) / len(rows)
    return f'<div class="bar"><i style="width:{v:.0f}%"></i></div><div class="mut small">{v:.0f} % (fini = 1, en cours = 0,6, partiel = 0,4)</div>'


def page() -> str:
    obj, suivi, glo = lire("objectifs.yml"), lire("protocole_suivi.yml"), lire("glossaire.yml")
    now = dt.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    th = obj.get("these") or {}
    en_cours, lancements, fins = agents()
    col = {"toi": [], "claude": [], "agent": [], "github": []}
    for t in obj.get("taches") or []:
        if t.get("statut") != "fini":
            col.setdefault(t.get("qui", "claude"), []).append(carte(t.get("nom", ""), "", t.get("statut", "")))
    for o in obj.get("objectifs") or []:
        for e in o.get("etapes") or []:
            if e.get("statut") != "fini" and e.get("qui"):
                col.setdefault(e["qui"], []).append(carte(e.get("nom", ""), o.get("nom", ""), e.get("statut", "")))
    for r in en_cours:
        col["agent"].insert(0, carte(f"Agent actif ({r.get('type') or 'agent'})", f"depuis {r.get('quand', '')[11:16]}", "en_cours"))
    for r in lancements:
        q = r.get("quand", "")
        col["agent"].append(carte(r.get("description") or "Agent", f"lancé le {q[8:10]}/{q[5:7]} à {q[11:16]}", ""))
    for r in fins:
        col["agent"].append(carte(f"Agent terminé ({r.get('type') or 'agent'})", f"à {r.get('quand', '')[11:16]}", "fini"))
    for d in telechargements(obj):
        pct = f" · {100 * d['taille'] / d['attendue']:.0f} %" if d["attendue"] else ""
        col["agent"].append(carte(f"Téléchargement : {d['nom']}", f"{d['taille'] / 1e6:.0f} Mo{pct} · écrit le {d['maj']}", d["etat"]))
    for r in github():
        col["github"].append(carte(r.get("workflowName", ""), f"{r.get('displayTitle', '')[:60]} · {r.get('createdAt', '')[5:16].replace('T', ' ')}",
                                   r.get("conclusion") or r.get("status") or ""))
    attente = [l for l in run(["git", "log", "origin/main..HEAD", "--format=%s"]).splitlines() if l]
    if attente:
        col["github"].insert(0, carte(f"{len(attente)} commit(s) à envoyer", attente[0][:70], "bloque"))
    colonnes = "".join(f'<section><h2>{t}</h2>{"".join(col.get(k, [])) or "<p class=mut>rien</p>"}</section>'
                       for k, t in (("toi", "Toi"), ("claude", "Claude"), ("agent", "Agents · téléchargements"), ("github", "GitHub")))

    objs = ""
    for o in obj.get("objectifs") or []:
        av = int(o.get("avancement", 0))
        et = "".join(f'<li>{esc(e.get("nom"))} {badge(e.get("statut", ""))}</li>' for e in o.get("etapes") or [])
        objs += f'<div class="obj"><div class="t">{esc(o.get("nom"))} <span class="num">{av} %</span></div><div class="bar"><i style="width:{av}%"></i></div><ul>{et}</ul></div>'
    bloc = "".join(f'<tr><td>{esc(b.get("quoi"))}</td><td>{esc(b.get("effet"))}</td><td class="mut">{esc(b.get("qui_peut_debloquer"))}</td></tr>'
                   for b in obj.get("blocages") or [])
    hyp = "".join(f'<tr><td class="code">{esc(h)}</td><td>{badge(v)}</td><td>{esc(s)}</td><td class="mut">{esc(famille(h))}</td></tr>'
                  for s, h, v in hypotheses()[::-1])
    gl = "".join(f'<tr><td class="code">{esc(g.get("terme"))}</td><td>{esc(g.get("sens"))}</td></tr>' for g in glo.get("termes") or [])
    commits = "".join(f"<li>{esc(l)}</li>" for l in run(["git", "log", "-8", "--format=%ad · %s", "--date=format:%d/%m %H:%M"]).splitlines())
    errs = "".join(f'<p class="kot">{esc(x["erreur"])}</p>' for x in (obj, suivi, glo) if x.get("erreur"))

    proto = ""
    for cle, titre in (("modules", "Modules M0 à M7 (protocole §6)"), ("experiences", "Expériences E1 à E7 (protocole §10)"),
                       ("hypotheses", "Hypothèses H1 à H6 (protocole §5)"), ("livrables", "Livrables L1 à L6 (prompt maître §15)")):
        rows = suivi.get(cle) or []
        proto += f'<details open><summary>{titre}</summary>{jauge(rows)}{table_suivi(rows, cle in ("modules", "experiences"))}</details>'

    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta http-equiv="refresh" content="{PERIODE_S}">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Pilotage MakyClimat</title><style>
:root{{--bg:#05080f;--panel:#0a1220;--line:#14324a;--fg:#d6f4ff;--mut:#6f93a8;--acc:#29d3ff;--ok:#3ef0a6;--ko:#ff5a6e;--run:#29d3ff;--warn:#ffc857;--todo:#6f93a8}}
*{{box-sizing:border-box}} body{{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:14px/1.45 "Segoe UI",system-ui,sans-serif;
background-image:linear-gradient(rgba(41,211,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(41,211,255,.04) 1px,transparent 1px);background-size:32px 32px}}
h1{{font:600 20px/1.2 Consolas,"Cascadia Mono",monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--acc);margin:0}}
h2,summary{{font:600 12px/1.2 Consolas,"Cascadia Mono",monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--acc);margin:0 0 10px}}
summary{{cursor:pointer;margin:6px 0}} .mut{{color:var(--mut)}} .small{{font-size:12px}} .kot{{color:var(--ko)}}
.head{{border:1px solid var(--line);background:var(--panel);padding:12px 14px;margin-bottom:14px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-bottom:14px}}
section,.box{{border:1px solid var(--line);background:var(--panel);padding:12px}}
.card{{border:1px solid var(--line);background:#0c1728;padding:8px 10px;margin-bottom:8px}}
.card.ok{{border-color:rgba(62,240,166,.45)}} .card.ko{{border-color:rgba(255,90,110,.6)}} .card.run{{border-color:rgba(41,211,255,.6)}} .card.warn{{border-color:rgba(255,200,87,.5)}}
.t{{font-weight:600}} .s{{color:var(--mut);font-size:12px}}
.b{{font:11px Consolas,monospace;padding:1px 6px;border:1px solid currentColor;white-space:nowrap;text-transform:uppercase;letter-spacing:.05em}}
.b.ok{{color:var(--ok)}} .b.ko{{color:var(--ko)}} .b.run{{color:var(--run)}} .b.warn{{color:var(--warn)}} .b.todo{{color:var(--todo)}}
.bar{{height:6px;border:1px solid var(--line);margin:4px 0}} .bar i{{display:block;height:100%;background:var(--acc)}}
.num{{font-family:Consolas,monospace;color:var(--acc)}} .obj{{margin-bottom:12px}} ul{{margin:4px 0 0 18px;padding:0}}
table{{width:100%;border-collapse:collapse;font-size:13px}} th{{text-align:left;color:var(--mut);font-weight:500;font-size:12px}}
td,th{{padding:5px 6px;border-top:1px solid var(--line);vertical-align:top}} td.code{{font-family:Consolas,monospace;color:var(--acc);white-space:nowrap}}
.two{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:12px;margin-bottom:14px}}
.wide{{margin-bottom:14px}} details{{margin-bottom:8px}}
</style></head><body>
<div class="head"><h1>MakyClimat · pilotage de la thèse</h1>
<div class="mut">{esc(th.get("titre", ""))}</div>
<div><span class="mut">Question en cours :</span> {esc(th.get("question_en_cours", ""))}</div>
<div class="mut small">Mis à jour le {now} · rafraîchi toutes les {PERIODE_S} s · aucun token · suivi du protocole au {esc(suivi.get("mis_a_jour", "?"))}</div>{errs}</div>
<div class="grid">{colonnes}</div>
<div class="box wide"><h2>Où on en est : protocole doctoral et prompt maître</h2>{proto}</div>
<div class="two"><div class="box"><h2>Objectifs et avancement</h2>{objs}</div>
<div class="box"><h2>Blocages</h2><table><tr><th>Quoi</th><th>Effet</th><th>Qui peut débloquer</th></tr>{bloc}</table></div></div>
<div class="two"><div class="box"><h2>Hypothèses testées (plus récentes en haut)</h2><table><tr><th></th><th>Verdict</th><th>Étude</th><th>Famille</th></tr>{hyp}</table></div>
<div class="box"><h2>Glossaire : T2, T2L, T2K…</h2><table>{gl}</table></div></div>
<div class="box wide"><h2>Dernières actions (git)</h2><ul>{commits}</ul></div>
</body></html>"""


def generer() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(page(), encoding="utf-8")
    tmp.replace(OUT)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boucle", action="store_true")
    a = ap.parse_args()
    generer()
    while a.boucle:
        time.sleep(PERIODE_S)
        try:
            generer()
        except Exception as e:
            print("erreur :", e)


if __name__ == "__main__":
    main()
