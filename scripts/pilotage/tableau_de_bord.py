"""Tableau de bord local de la thèse et de MakyClimat (aucun modèle de langage, aucun appel réseau sauf `gh`).

Lit : pilotage/objectifs.yml, pilotage/protocole_suivi.yml, pilotage/glossaire.yml, pilotage/etat/agents.jsonl (hooks
de Claude Code), validation/journal_recherche.md, git et GitHub (gh). Écrit : pilotage/tableau_de_bord.html.
Usage : python scripts/pilotage/tableau_de_bord.py [--boucle]   (--boucle : régénère toutes les 30 s)
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
PERIODE_S, PAGE_S, GH_PERIODE_S, ARRET_MIN = 60, 300, 300, 15
_gh_cache: dict = {"t": 0.0, "runs": []}

VERDICT = re.compile(r"\*\*(H-[A-Za-z0-9-]+)[^*]*?(non soutenue|soutenue|robuste|non confirmée|non vérifiée)")
SECTION = re.compile(r"^###\s+(.*)")
FAMILLE = {"H-R": "Contrôle de T2 par des bornes africaines (T2c)", "H-L": "T2 corrigée par les mesures malgaches (T2L)",
           "H-K": "Karst", "H-Cl": "Bilan de chlorure", "H-P": "Puits à sec", "H-C": "Carte des nappes",
           "H-B": "Bassins hydrogéologiques", "H-M": "Mémoire du sous-sol (THMS)", "H-N": "Océan et nappes"}
MARQUES = {"✅": ("ok", "Réussi"), "❌": ("ko", "Échec"), "📊": ("info", "Résultat"), "📌": ("neutre", "Suite"),
           "🔧": ("warn", "Correction"), "⚠️": ("warn", "Attention"), "🟡": ("warn", "Piste")}
ETAT = {"fini": ("ok", "Terminé"), "soutenue": ("ok", "Soutenue"), "robuste": ("ok", "Robuste"), "success": ("ok", "Réussi"),
        "en_cours": ("info", "En cours"), "in_progress": ("info", "En cours"), "partiel": ("warn", "Partiel"),
        "non vérifiée": ("warn", "Non vérifiée"), "queued": ("neutre", "En file"), "bloque": ("ko", "Bloqué"),
        "arrêté": ("ko", "Arrêté"), "non soutenue": ("ko", "Non soutenue"), "non confirmée": ("ko", "Non confirmée"),
        "failure": ("ko", "Échec"), "a_faire": ("neutre", "À faire"), "absent": ("neutre", "Absent")}


# ----------------------------------------------------------------------------------------------- lecture des sources
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


def etudes() -> list[dict]:
    """Études du journal de recherche : titre, date, puces, verdicts d'hypothèses."""
    p = ROOT / "validation" / "journal_recherche.md"
    out, date, cur = [], "", None
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            date, cur = line[3:].strip(), None
            continue
        m = SECTION.match(line)
        if m:
            cur = {"titre": m.group(1).strip(), "court": re.sub(r"\s*\(`.*?`\)", "", m.group(1)).strip(),
                   "date": date, "puces": [], "verdicts": []}
            out.append(cur)
            continue
        if cur is None:
            continue
        if line.startswith("- "):
            cur["puces"].append(line[2:].strip())
        elif line.startswith("  ") and cur["puces"]:
            cur["puces"][-1] += " " + line.strip()
        cur["verdicts"] += VERDICT.findall(line)
    for e in out:
        e["verdicts"] = list(dict(e["verdicts"]).items())
    return out


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
                    "maj": dt.datetime.fromtimestamp(mtime).strftime("%d/%m %H:%M") if mtime else "—"})
    return out


# ----------------------------------------------------------------------------------------------- rendu
def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


def inline(t: str) -> str:
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", t)


def statut(etat: str) -> str:
    if not etat:
        return ""
    c, lib = ETAT.get(etat, ("neutre", etat))
    return f'<span class="st {c}"><i></i>{esc(lib)}</span>'


def famille(h: str) -> str:
    for k in sorted(FAMILLE, key=len, reverse=True):
        if h.startswith(k):
            return FAMILLE[k]
    return ""


def puce(p: str) -> str:
    for m, (c, lib) in MARQUES.items():
        if p.startswith(m):
            return f'<li><span class="tag {c}">{lib}</span><span>{inline(p[len(m):].strip())}</span></li>'
    return f'<li><span class="tag neutre">Note</span><span>{inline(p)}</span></li>'


def md_html(texte: str) -> str:
    out, table = [], []

    def flush():
        if table:
            rows = [r for r in table if not re.match(r"^\|[\s\-:|]+\|$", r)]
            out.append('<table class="t">' + "".join("<tr>" + "".join(f"<td>{inline(c.strip())}</td>" for c in r.strip("|").split("|"))
                                                     + "</tr>" for r in rows) + "</table>")
            table.clear()
    for line in texte.splitlines():
        if line.startswith("|"):
            table.append(line.strip())
            continue
        flush()
        if line.startswith("#"):
            out.append(f"<h4>{inline(line.lstrip('#').strip())}</h4>")
        elif line.lstrip().startswith(("- ", "* ")) or re.match(r"^\s*\d+\.\s", line):
            out.append(f"<p class='md-li'>{inline(re.sub(r'^\s*([-*]|\d+\.)\s', '', line))}</p>")
        elif line.strip():
            out.append(f"<p>{inline(line.strip())}</p>")
    flush()
    return "".join(out)


def jauge(rows: list[dict]) -> str:
    poids = {"fini": 1.0, "en_cours": 0.6, "partiel": 0.4}
    if not rows:
        return ""
    v = 100 * sum(poids.get(r.get("statut"), 0) for r in rows) / len(rows)
    return f'<span class="gauge" title="Terminé = 1 ; en cours = 0,6 ; partiel = 0,4"><span style="width:{v:.0f}%"></span></span><span class="num">{v:.0f} %</span>'


def bloc(r: dict, liste: list[dict], regles: list[dict], details: dict) -> str:
    code = r.get("code", "")
    mine = [e for e in liste if any(code in g.get("codes", []) and re.search(g.get("motif", "^$"), e["titre"]) for g in regles)]
    ok = sum(p.startswith("✅") for e in mine for p in e["puces"])
    ko = sum(p.startswith("❌") for e in mine for p in e["puces"])
    verd = [v for e in mine for _, v in e["verdicts"]]
    sout, rob = sum(v in ("soutenue", "robuste") for v in verd), sum(v == "robuste" for v in verd)
    nons = sum(v in ("non soutenue", "non confirmée") for v in verd)
    meta = (f'<span class="meta"><b>{len(mine)}</b> études</span><span class="meta"><b>{ok}</b> réussites</span>'
            f'<span class="meta"><b>{ko}</b> échecs</span><span class="meta"><b>{sout}</b> hyp. soutenues'
            f'{f" ({rob} robustes)" if rob else ""}</span><span class="meta"><b>{nons}</b> non soutenues</span>')
    corps = '<dl class="kv">'
    corps += f'<dt>Où on en est</dt><dd>{inline(r.get("ou", "—"))}</dd>'
    if r.get("manque"):
        corps += f'<dt>Ce qui manque</dt><dd>{inline(r["manque"])}</dd>'
    corps += "</dl>"
    d = details.get(code) or {}
    if d.get("ameliorer"):
        corps += '<h4>Pistes d\'amélioration</h4><table class="t"><tr><th>Quoi</th><th>Avec quoi</th></tr>' + "".join(
            f"<tr><td>{inline(a.get('quoi', ''))}</td><td>{inline(a.get('avec', ''))}</td></tr>" for a in d["ameliorer"]) + "</table>"
    if d.get("comparaison"):
        corps += '<h4>Positionnement par rapport aux travaux existants</h4><table class="t"><tr><th>Ce projet</th><th>Travaux existants</th><th>Référence</th></tr>' + "".join(
            f"<tr><td>{inline(a.get('nous', ''))}</td><td>{inline(a.get('autres', ''))}</td><td class='muted'>{inline(a.get('ref', ''))}</td></tr>"
            for a in d["comparaison"]) + "</table>"
    if mine:
        corps += "<h4>Études rattachées</h4>"
        for e in mine[::-1]:
            vb = "".join(f'<span class="hyp"><code>{esc(h)}</code>{statut(v)}</span>' for h, v in e["verdicts"])
            corps += (f'<details class="study"><summary><span class="s-title">{esc(e["court"])}</span>'
                      f'<span class="s-date">{esc(e["date"])}</span>{vb}</summary><ul class="log">'
                      + "".join(puce(p) for p in e["puces"]) + "</ul></details>")
    return (f'<details class="row"><summary><code class="id">{esc(code)}</code><span class="r-title">{esc(r.get("nom"))}</span>'
            f'{statut(r.get("statut", ""))}<span class="metas">{meta}</span></summary><div class="body">{corps}</div></details>')


def carte(titre: str, sous: str = "", etat: str = "") -> str:
    return f'<div class="item"><div class="i-top"><span class="i-title">{esc(titre)}</span>{statut(etat)}</div>{f"<div class=i-sub>{esc(sous)}</div>" if sous else ""}</div>'


def page() -> str:
    obj, suivi, glo = lire("objectifs.yml"), lire("protocole_suivi.yml"), lire("glossaire.yml")
    now = dt.datetime.now()
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
        col["agent"].insert(0, carte(f"Agent actif · {r.get('type') or 'agent'}", f"depuis {r.get('quand', '')[11:16]}", "en_cours"))
    for r in lancements:
        q = r.get("quand", "")
        col["agent"].append(carte(r.get("description") or "Agent", f"lancé le {q[8:10]}/{q[5:7]} à {q[11:16]}"))
    for r in fins:
        col["agent"].append(carte(f"Agent terminé · {r.get('type') or 'agent'}", f"à {r.get('quand', '')[11:16]}", "fini"))
    for d in telechargements(obj):
        pct = f" · {100 * d['taille'] / d['attendue']:.0f} %" if d["attendue"] else ""
        col["agent"].append(carte(d["nom"], f"{d['taille'] / 1e6:,.0f} Mo{pct} · dernière écriture {d['maj']}".replace(",", " "), d["etat"]))
    for r in github():
        col["github"].append(carte(r.get("workflowName", ""), f"{r.get('displayTitle', '')[:60]} · {r.get('createdAt', '')[5:16].replace('T', ' ')}",
                                   r.get("conclusion") or r.get("status") or ""))
    attente = [l for l in run(["git", "log", "origin/main..HEAD", "--format=%s"]).splitlines() if l]
    if attente:
        col["github"].insert(0, carte(f"{len(attente)} commit(s) non envoyé(s)", attente[0][:70], "bloque"))
    noms = (("toi", "Porteur du projet"), ("claude", "Claude"), ("agent", "Agents et téléchargements"), ("github", "Intégration (GitHub)"))
    equipe = "".join(f'<div class="lane"><div class="lane-h">{t}<span class="count">{len(col.get(k, []))}</span></div>'
                     f'{"".join(col.get(k, [])) or "<div class=empty>Rien en attente</div>"}</div>' for k, t in noms)

    liste = etudes()
    regles, details = suivi.get("regles") or [], suivi.get("details") or {}
    proto = ""
    for cle, titre in (("modules", "Modules M0 à M7"), ("experiences", "Expériences E1 à E7"),
                       ("hypotheses", "Hypothèses générales H1 à H6"), ("livrables", "Livrables L1 à L6 (prompt maître)")):
        rows = suivi.get(cle) or []
        proto += (f'<div class="group"><div class="group-h"><h3>{titre}</h3>{jauge(rows)}</div>'
                  + "".join(bloc(r, liste, regles, details) for r in rows) + "</div>")

    objs = ""
    for o in obj.get("objectifs") or []:
        av = int(o.get("avancement", 0))
        et = "".join(f'<li><span>{esc(e.get("nom"))}</span>{statut(e.get("statut", ""))}</li>' for e in o.get("etapes") or [])
        objs += (f'<div class="goal"><div class="goal-h"><span>{esc(o.get("nom"))}</span><span class="gauge"><span style="width:{av}%"></span></span>'
                 f'<span class="num">{av} %</span></div><ul class="steps">{et}</ul></div>')
    bloc_ = "".join(f'<tr><td>{esc(b.get("quoi"))}</td><td>{esc(b.get("effet"))}</td><td class="muted">{esc(b.get("qui_peut_debloquer"))}</td></tr>'
                    for b in obj.get("blocages") or [])
    hyp_rows = []
    for e in liste:
        for h, v in e["verdicts"]:
            hyp_rows.append((e["court"], e["date"], h, v))
    hyp = "".join(f'<tr><td><code>{esc(h)}</code></td><td>{statut(v)}</td><td>{esc(s)}</td><td class="muted">{esc(famille(h))}</td><td class="muted nowrap">{esc(d)}</td></tr>'
                  for s, d, h, v in hyp_rows[::-1])
    gl = "".join(f'<tr><td class="nowrap"><strong>{esc(g.get("terme"))}</strong></td><td>{esc(g.get("sens"))}</td></tr>' for g in glo.get("termes") or [])
    biblio = ""
    for b in suivi.get("bibliographie") or []:
        p = ROOT / b.get("fichier", "")
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        if b.get("section"):
            i = t.find(b["section"])
            j = t.find("\n## ", i + 3)
            t = t[i:j if j > 0 else None] if i >= 0 else ""
        biblio += f'<details class="row"><summary><span class="r-title">{esc(b.get("titre"))}</span><span class="muted small">{esc(b.get("fichier"))}</span></summary><div class="body md">{md_html(t)}</div></details>'
    commits = "".join(f'<tr><td class="muted nowrap">{esc(l.split(" | ", 1)[0])}</td><td>{esc(l.split(" | ", 1)[-1])}</td></tr>'
                      for l in run(["git", "log", "-10", "--format=%ad | %s", "--date=format:%d/%m %H:%M"]).splitlines())
    errs = "".join(f'<div class="alert">{esc(x["erreur"])}</div>' for x in (obj, suivi, glo) if x.get("erreur"))
    nav = "".join(f'<a href="#{i}">{t}</a>' for i, t in (("equipe", "Équipe"), ("protocole", "Protocole"), ("objectifs", "Objectifs"),
                                                        ("hypotheses", "Hypothèses"), ("biblio", "Bibliographie"), ("glossaire", "Glossaire"),
                                                        ("activite", "Activité")))

    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MakyClimat · Pilotage</title><style>
:root{{--bg:#f7f8fa;--surface:#fff;--sub:#f2f4f7;--border:#e4e7ec;--text:#101828;--muted:#667085;--accent:#2e5aac;
--ok:#16794c;--ok-bg:#e7f6ee;--ko:#b42318;--ko-bg:#fdecea;--warn:#a15c07;--warn-bg:#fef4e2;--info:#2e5aac;--info-bg:#eaf0fb;--neutre:#667085;--neutre-bg:#f2f4f7}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0f1115;--surface:#161a20;--sub:#1c2129;--border:#2a303b;--text:#e7eaf0;--muted:#98a1b2;--accent:#8fb0ec;
--ok:#5fcf98;--ok-bg:#16301f;--ko:#f28b82;--ko-bg:#3a1c1a;--warn:#f0b45b;--warn-bg:#36290f;--info:#8fb0ec;--info-bg:#1b2840;--neutre:#98a1b2;--neutre-bg:#222833}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 -apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;-webkit-font-smoothing:antialiased}}
header{{position:sticky;top:0;z-index:5;background:var(--surface);border-bottom:1px solid var(--border)}}
.hwrap{{max-width:1320px;margin:0 auto;padding:12px 24px 0}} .brand{{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}}
.brand h1{{font-size:16px;font-weight:600;margin:0}} .brand .sub{{color:var(--muted);font-size:13px}} .brand .upd{{margin-left:auto;color:var(--muted);font-size:12px}}
#actualiser{{font:inherit;font-size:12px;padding:4px 10px;border:1px solid var(--border);border-radius:6px;background:var(--surface);color:var(--text);cursor:pointer}} #actualiser:hover{{background:var(--sub)}}
nav{{display:flex;gap:4px;overflow-x:auto;margin-top:8px}} nav a{{color:var(--muted);text-decoration:none;font-size:13px;padding:8px 10px;border-bottom:2px solid transparent;white-space:nowrap}}
nav a:hover{{color:var(--text);border-bottom-color:var(--border)}}
main{{max-width:1320px;margin:0 auto;padding:20px 24px 48px}} section{{margin-bottom:28px;scroll-margin-top:96px}}
h2{{font-size:15px;font-weight:600;margin:0 0 10px}} h3{{font-size:14px;font-weight:600;margin:0}} h4{{font-size:12px;font-weight:600;color:var(--muted);margin:16px 0 6px;text-transform:none}}
.lead{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px 16px;margin-bottom:20px}}
.lead .q{{font-size:15px}} .lead .t{{color:var(--muted);font-size:13px;margin-top:2px}}
.lanes{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}}
.lane{{background:var(--sub);border:1px solid var(--border);border-radius:8px;padding:10px}}
.lane-h{{display:flex;justify-content:space-between;font-size:12px;font-weight:600;color:var(--muted);margin:2px 2px 8px}}
.count{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:0 7px;font-weight:500}}
.item{{background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:8px 10px;margin-bottom:6px}}
.i-top{{display:flex;gap:8px;justify-content:space-between;align-items:flex-start}} .i-title{{font-size:13px;font-weight:500}} .i-sub{{color:var(--muted);font-size:12px;margin-top:2px}}
.empty{{color:var(--muted);font-size:12px;padding:6px 2px}}
.st{{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:500;white-space:nowrap;color:var(--neutre)}} .st i{{width:7px;height:7px;border-radius:50%;background:currentColor}}
.st.ok{{color:var(--ok)}} .st.ko{{color:var(--ko)}} .st.warn{{color:var(--warn)}} .st.info{{color:var(--info)}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:8px}}
.group{{background:var(--surface);border:1px solid var(--border);border-radius:8px;margin-bottom:14px;overflow:hidden}}
.group-h{{display:flex;align-items:center;gap:12px;padding:12px 16px;border-bottom:1px solid var(--border)}}
.gauge{{display:inline-block;width:120px;height:6px;background:var(--sub);border-radius:3px;overflow:hidden}} .gauge span{{display:block;height:100%;background:var(--accent)}}
.num{{font-variant-numeric:tabular-nums;color:var(--muted);font-size:12px}}
details.row{{border-bottom:1px solid var(--border)}} details.row:last-child{{border-bottom:0}}
details>summary{{list-style:none;cursor:pointer}} details>summary::-webkit-details-marker{{display:none}}
details.row>summary{{display:flex;align-items:center;gap:12px;padding:10px 16px;flex-wrap:wrap}}
details.row>summary:hover{{background:var(--sub)}}
details.row>summary::before,details.study>summary::before{{content:"";width:6px;height:6px;border-right:1.5px solid var(--muted);border-bottom:1.5px solid var(--muted);transform:rotate(-45deg);transition:transform .15s;flex:none}}
details[open]>summary::before{{transform:rotate(45deg)}}
code{{font:12px ui-monospace,SFMono-Regular,Consolas,monospace}} code.id{{color:var(--muted);min-width:24px}}
.r-title{{font-weight:500}} .metas{{margin-left:auto;display:flex;gap:14px;color:var(--muted);font-size:12px;flex-wrap:wrap}} .meta b{{color:var(--text);font-weight:600}}
.body{{padding:4px 16px 16px 46px}}
dl.kv{{display:grid;grid-template-columns:140px 1fr;gap:4px 16px;margin:8px 0}} dt{{color:var(--muted);font-size:13px}} dd{{margin:0}}
table.t{{width:100%;border-collapse:collapse;font-size:13px}} .t th{{text-align:left;font-weight:500;color:var(--muted);font-size:12px;border-bottom:1px solid var(--border);padding:6px 8px}}
.t td{{border-bottom:1px solid var(--border);padding:7px 8px;vertical-align:top}} .t tr:last-child td{{border-bottom:0}}
details.study{{border:1px solid var(--border);border-radius:6px;margin:6px 0;background:var(--surface)}}
details.study>summary{{display:flex;align-items:center;gap:10px;padding:8px 10px;flex-wrap:wrap}} .s-title{{font-size:13px;font-weight:500}} .s-date{{color:var(--muted);font-size:12px}}
.hyp{{display:inline-flex;gap:6px;align-items:center;margin-left:4px}}
ul.log{{list-style:none;margin:0;padding:4px 12px 10px}} ul.log li{{display:grid;grid-template-columns:86px 1fr;gap:10px;padding:5px 0;border-top:1px solid var(--border);font-size:13px}}
.tag{{font-size:11px;font-weight:600;border-radius:4px;padding:1px 6px;height:fit-content;text-align:center}}
.tag.ok{{color:var(--ok);background:var(--ok-bg)}} .tag.ko{{color:var(--ko);background:var(--ko-bg)}} .tag.warn{{color:var(--warn);background:var(--warn-bg)}}
.tag.info{{color:var(--info);background:var(--info-bg)}} .tag.neutre{{color:var(--neutre);background:var(--neutre-bg)}}
.cols{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:16px}} .pad{{padding:14px 16px}}
.goal{{padding:12px 16px;border-bottom:1px solid var(--border)}} .goal:last-child{{border-bottom:0}}
.goal-h{{display:flex;align-items:center;gap:12px;font-weight:500}} .goal-h>span:first-child{{flex:1}}
ul.steps{{list-style:none;margin:8px 0 0;padding:0}} ul.steps li{{display:flex;justify-content:space-between;gap:12px;padding:4px 0;font-size:13px;color:var(--muted)}}
.muted{{color:var(--muted)}} .small{{font-size:12px}} .nowrap{{white-space:nowrap}}
.md p{{margin:4px 0;font-size:13px}} .md .md-li{{padding-left:12px;position:relative}} .md .md-li::before{{content:"–";position:absolute;left:0;color:var(--muted)}}
.scroll{{max-height:520px;overflow:auto}} .alert{{background:var(--ko-bg);color:var(--ko);border-radius:6px;padding:8px 12px;margin-bottom:12px}}
@media (max-width:640px){{.hwrap,main{{padding-left:16px;padding-right:16px}} .body{{padding-left:16px}} dl.kv{{grid-template-columns:1fr}} .cols{{grid-template-columns:1fr}}}}
</style></head><body>
<header><div class="hwrap"><div class="brand"><h1>MakyClimat</h1><span class="sub">Pilotage de la thèse</span>
<span class="upd">Données du {now:%H:%M} · mise à jour automatique toutes les 5 min · protocole au {esc(suivi.get("mis_a_jour", "—"))}</span><button id="actualiser" type="button" title="Recharger la page sans perdre la position">Actualiser</button></div>
<nav>{nav}</nav></div></header>
<main>{errs}
<div class="lead"><div class="q">{esc(th.get("question_en_cours", ""))}</div><div class="t">{esc(th.get("titre", ""))}</div></div>
<section id="equipe"><h2>Répartition du travail</h2><p><a href="etat/coordination/notifications.html">Alertes de coordination</a></p><div class="lanes">{equipe}</div></section>
<section id="protocole"><h2>Avancement par rapport au protocole doctoral et au prompt maître</h2>{proto}</section>
<section id="objectifs" class="cols"><div><h2>Objectifs</h2><div class="card">{objs}</div></div>
<div><h2>Blocages</h2><div class="card pad"><table class="t"><tr><th>Blocage</th><th>Effet</th><th>Qui peut débloquer</th></tr>{bloc_}</table></div></div></section>
<section id="hypotheses"><h2>Hypothèses testées</h2><div class="card pad scroll"><table class="t"><tr><th>Code</th><th>Verdict</th><th>Étude</th><th>Famille</th><th>Date</th></tr>{hyp}</table></div></section>
<section id="biblio"><h2>Bibliographie et sources</h2><div class="group">{biblio or '<div class="pad muted">Aucun fichier</div>'}</div></section>
<section id="glossaire"><h2>Glossaire</h2><div class="card pad"><table class="t">{gl}</table></div></section>
<section id="activite"><h2>Activité récente</h2><div class="card pad"><table class="t">{commits}</table></div></section>
</main>
<script>
(function(){{
  var K="pilotage_ouverts",Y="pilotage_defilement",o={{}};
  if("scrollRestoration" in history) history.scrollRestoration="manual";
  function lire(k,d){{try{{var v=localStorage.getItem(k);return v===null?d:v;}}catch(e){{return d;}}}}
  function ecrire(k,v){{try{{localStorage.setItem(k,v);}}catch(e){{}}}}
  function cle(d){{var s=d.querySelector("summary");return s?s.textContent.trim().slice(0,90):"";}}
  try{{o=JSON.parse(lire(K,"{{}}"));}}catch(e){{o={{}};}}
  document.querySelectorAll("details").forEach(function(d){{var k=cle(d);if(k in o)d.open=o[k];
    d.addEventListener("toggle",function(){{o[k]=d.open;ecrire(K,JSON.stringify(o));}});}});
  function restaurer(){{var y=+lire(Y,"0");if(y>0)window.scrollTo({{top:y,left:0,behavior:"instant"}});}}
  restaurer(); window.addEventListener("load",restaurer);
  var t=null; window.addEventListener("scroll",function(){{clearTimeout(t);t=setTimeout(function(){{ecrire(Y,String(window.scrollY));}},150);}});
  function recharger(){{ecrire(Y,String(window.scrollY));location.reload();}}
  document.getElementById("actualiser").addEventListener("click",recharger);
  setTimeout(recharger,{PAGE_S}*1000);
}})();
</script></body></html>"""


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
