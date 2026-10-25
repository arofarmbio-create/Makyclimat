"""Historique des événements et de la réponse : GLIDE, IDMC (événements), HRP/FTS (projets du plan de réponse), IATI (activités géolocalisées)
et import 3W/4W fourni par les gestionnaires d'information (inputs/reponses_humanitaires.csv).

Sortie : docs/data/<pays>/response.json (colonnes compactes, lu par la carte). Chaque donnée garde sa source et son type :
  - « 3w »   : bénéficiaires atteints (import) ;
  - « hrp »  : projets des plans de réponse (OCHA/FTS), fonds demandés ;
  - « iati » : activités des partenaires (budget engagé réparti également sur les années d'activité) : indique une PRÉSENCE, pas des bénéficiaires.
Aucune de ces sources publiques ne fournit de bénéficiaires par zone : seul l'import 3W le permet.

Usage : python scripts/build_history.py --country mdg   (les sources publiques sont facultatives : une indisponibilité n'arrête rien)
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import re
import unicodedata

import numpy as np
import pandas as pd
import requests

from common import country_docs_dir, hdx_resources, load_config, locate_points, read_units, write_json

UA = {"User-Agent": "makyclimat/1.0 (+https://github.com/arofarmbio-create/Makyclimat)"}
TYPES = ["cyclone", "inondation", "sécheresse", "épidémie", "autre"]
TYPE_MAP = {"tc": "cyclone", "st": "cyclone", "vw": "cyclone", "fl": "inondation", "ff": "inondation", "ls": "inondation",
            "dr": "sécheresse", "ep": "épidémie"}
CLUSTERS = ["Sécurité alimentaire", "Santé", "Nutrition", "Eau, assainissement et hygiène", "Éducation", "Protection", "Abris et biens non alimentaires",
            "Logistique", "Relèvement précoce", "Coordination", "Multisectoriel", "Autre"]
CLUSTER_ALIASES = {
    "food security": "Sécurité alimentaire", "securite alimentaire": "Sécurité alimentaire", "fsl": "Sécurité alimentaire", "agriculture": "Sécurité alimentaire",
    "health": "Santé", "sante": "Santé", "nutrition": "Nutrition",
    "wash": "Eau, assainissement et hygiène", "water sanitation hygiene": "Eau, assainissement et hygiène", "eau": "Eau, assainissement et hygiène",
    "education": "Éducation", "protection": "Protection", "child protection": "Protection", "gbv": "Protection",
    "shelter": "Abris et biens non alimentaires", "shelter/nfi": "Abris et biens non alimentaires", "abris": "Abris et biens non alimentaires", "nfi": "Abris et biens non alimentaires",
    "logistics": "Logistique", "logistique": "Logistique", "early recovery": "Relèvement précoce", "relevement precoce": "Relèvement précoce",
    "coordination": "Coordination", "multi-sector": "Multisectoriel", "multisector": "Multisectoriel", "multisectoriel": "Multisectoriel",
}


def norm(s) -> str:
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9/ ]", " ", s)).strip()


def cluster_of(s) -> str:
    n = norm(s)
    for key, val in CLUSTER_ALIASES.items():
        if key in n:
            return val
    for c in CLUSTERS:
        if norm(c) == n:
            return c
    return "Autre"


def event_type(code=None, text=None) -> str:
    if code and str(code).lower() in TYPE_MAP:
        return TYPE_MAP[str(code).lower()]
    t = norm(text or "")
    for k, v in (("cyclon", "cyclone"), ("storm", "cyclone"), ("tempete", "cyclone"), ("wind", "cyclone"), ("flood", "inondation"), ("inond", "inondation"),
                 ("landslide", "inondation"), ("drought", "sécheresse"), ("secheresse", "sécheresse"), ("epidemic", "épidémie"), ("cholera", "épidémie"), ("mpox", "épidémie")):
        if k in t:
            return v
    return "autre"


def parse_glide(df: pd.DataFrame) -> list[dict]:
    out = []
    for _, r in df.iterrows():
        try:
            date = dt.date(int(r["year"]), int(r["month"] or 1), int(r["day"] or 1))
        except (ValueError, TypeError):
            continue
        out.append({"date": date.isoformat(), "type": event_type(r.get("event"), r.get("event_name")), "name": str(r.get("comments") or r.get("event_name") or "")[:120],
                    "lat": float(r["latitude"]), "lon": float(r["longitude"]), "affected": int(r.get("affected") or 0), "displaced": 0,
                    "killed": int(r.get("killed") or 0), "homeless": int(r.get("homeless") or 0), "src": "GLIDE", "id": str(r.get("glidenumber"))})
    return out


def parse_idmc(df: pd.DataFrame) -> list[dict]:
    out = []
    for _, r in df.iterrows():
        if str(r.get("displacement_type", "")).lower() != "disaster":
            continue
        date = str(r.get("event_start_date") or r.get("displacement_start_date") or "")[:10]
        if len(date) < 10 or pd.isna(r.get("latitude")):
            continue
        out.append({"date": date, "type": event_type(None, f"{r.get('type')} {r.get('subtype')} {r.get('event_name')}"), "name": str(r.get("event_name") or "")[:120],
                    "lat": float(r["latitude"]), "lon": float(r["longitude"]), "affected": 0, "displaced": int(r.get("figure") or 0),
                    "killed": 0, "homeless": 0, "src": "IDMC", "id": str(r.get("event_id"))})
    return out


def merge_events(a: list[dict], b: list[dict], days: int = 10) -> list[dict]:
    """Fusionne les événements de même type dont les dates sont voisines (évite de compter deux fois le même événement)."""
    out = [dict(e) for e in a]
    for e in b:
        d = dt.date.fromisoformat(e["date"])
        hit = next((x for x in out if x["type"] == e["type"] and abs((dt.date.fromisoformat(x["date"]) - d).days) <= days), None)
        if hit:
            hit["displaced"] = max(hit["displaced"], e["displaced"])
            hit["affected"] = max(hit["affected"], e["affected"])
            if e["src"] not in hit["src"]:
                hit["src"] += "+" + e["src"]
        else:
            out.append(dict(e))
    return sorted(out, key=lambda x: x["date"])


def parse_iati(df: pd.DataFrame) -> pd.DataFrame:
    """Activités géolocalisées : une ligne par (activité, lieu), budget engagé réparti également sur les années d'activité."""
    d = df.copy()
    for c in ("latitude", "longitude"):
        if c not in d.columns:
            cand = [x for x in d.columns if x.startswith(c[:3]) and "location" in x] or [x for x in d.columns if c in x]
            if cand:
                d[c] = d[cand[0]]
    d = d.dropna(subset=["latitude", "longitude"]).drop_duplicates(subset=["aid", "latitude", "longitude"])
    rows = []
    for _, r in d.iterrows():
        try:
            y0, y1 = int(str(r["day_start"])[:4]), int(str(r["day_end"])[:4])
        except ValueError:
            continue
        y1 = min(max(y1, y0), dt.date.today().year)
        ny = y1 - y0 + 1
        funds = float(r.get("commitment_eur") or 0) / ny
        for y in range(y0, y1 + 1):
            rows.append({"y": y, "lat": float(r["latitude"]), "lon": float(r["longitude"]), "org": str(r.get("reporting"))[:60],
                         "cluster": cluster_of(f"{r.get('title')} {r.get('sector_group', '')}"), "funds": funds, "n": 1, "aid": r["aid"]})
    return pd.DataFrame(rows)


def parse_hrp(df: pd.DataFrame, units: pd.DataFrame) -> pd.DataFrame:
    """Projets du plan de réponse : lieu = région ou district nommé s'il est reconnu, sinon national (pcode vide)."""
    names = {}
    for _, u in units[units.level.isin([1, 2])].iterrows():
        names[norm(u["name"])] = u["pcode"]
    rows = []
    for _, r in df.iterrows():
        try:
            y = int(str(r["startDate"])[:4])
        except ValueError:
            continue
        locs = [norm(x) for x in re.split(r"[;,|]", str(r.get("locations") or ""))]
        pcs = sorted({names[x] for x in locs if x in names})
        cl = str(r.get("globalClusters") or "")
        for pc in pcs or [""]:
            rows.append({"y": y, "pcode": pc, "org": str(r.get("organizations") or "")[:60], "cluster": cluster_of(cl),
                         "funds": float(r.get("currentRequestedFunds") or 0) / max(1, len(pcs)), "n": 1})
    return pd.DataFrame(rows)


def parse_3w(df: pd.DataFrame, units: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Import 3W/4W : colonnes date_debut, pcode, cluster, organisation, beneficiaires (+ activite, evenement, source). Retourne (lignes, avertissements)."""
    df = df.rename(columns={c: norm(c).replace(" ", "_") for c in df.columns})
    # mêmes noms de colonnes que inputs/interventions.csv (partenaire, secteur, debut) acceptés
    df = df.rename(columns={"partenaire": "organisation", "secteur": "cluster", "debut": "date_debut", "activite": "activite"})
    miss = [c for c in ("date_debut", "pcode", "cluster", "organisation", "beneficiaires") if c not in df.columns]
    if miss:
        raise ValueError("colonnes manquantes : " + ", ".join(miss))
    known = set(units.pcode)
    warn, rows = [], []
    for i, r in df.iterrows():
        pc = str(r["pcode"]).strip()
        if pc not in known:
            warn.append(f"ligne {i + 2} : pcode inconnu « {pc} » ignoré")
            continue
        try:
            y = int(str(r["date_debut"])[:4])
            b = float(str(r["beneficiaires"]).replace(" ", "").replace(",", "."))
        except ValueError:
            warn.append(f"ligne {i + 2} : date ou bénéficiaires illisibles, ignorée")
            continue
        if b < 0:
            warn.append(f"ligne {i + 2} : bénéficiaires négatifs, ignorée")
            continue
        rows.append({"y": y, "pcode": pc, "org": str(r["organisation"])[:60], "cluster": cluster_of(r["cluster"]), "ben": b, "n": 1,
                     "event": str(r.get("evenement") or "")[:60]})
    return pd.DataFrame(rows), warn


def pack(parts: list[tuple[str, pd.DataFrame]]) -> dict:
    """Colonnes compactes : u (pcode), y, c (cluster), o (organisation), k (type de donnée), b (bénéficiaires), f (fonds en euros), n (activités)."""
    orgs, kinds = [], ["3w", "hrp", "iati"]
    cols = {k: [] for k in "uycokbfn"}
    for kind, d in parts:
        for _, r in d.iterrows():
            org = r["org"]
            if org not in orgs:
                orgs.append(org)
            cols["u"].append(r["pcode"] if "pcode" in d.columns else "")
            cols["y"].append(int(r["y"]))
            cols["c"].append(CLUSTERS.index(r["cluster"]))
            cols["o"].append(orgs.index(org))
            cols["k"].append(kinds.index(kind))
            cols["b"].append(int(round(r["ben"])) if "ben" in d.columns else 0)
            cols["f"].append(int(round(r["funds"])) if "funds" in d.columns else 0)
            cols["n"].append(int(r["n"]))
    return {"clusters": CLUSTERS, "orgs": orgs, "kinds": kinds, "rec": cols}


def fetch_csv(dataset: str, pick, label: str):
    try:
        res = hdx_resources(dataset)
        url = next(x["url"] for x in res if pick(x))
        r = requests.get(url, headers=UA, timeout=240)
        r.raise_for_status()
        return pd.read_csv(io.BytesIO(r.content), low_memory=False)
    except Exception as e:  # source facultative
        print(f"  {label} indisponible : {e}")
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    cfg = load_config(args.country)
    units = read_units(args.country)
    h = cfg.get("history", {})
    events, parts, sources = [], [], []

    g = fetch_csv(h.get("glide_dataset", "mdg-glide-events"), lambda x: x["format"].upper() == "CSV", "GLIDE")
    i = fetch_csv(h.get("idmc_dataset", "mdg-idmc-idu-events"), lambda x: x["format"].upper() == "CSV", "IDMC")
    ev_g = parse_glide(g.iloc[1:] if g is not None and str(g.iloc[0].get("year")).startswith("#") else g) if g is not None else []
    ev_i = parse_idmc(i.iloc[1:] if i is not None and str(i.iloc[0].get("year")).startswith("#") else i) if i is not None else []
    events = merge_events(ev_g, ev_i)
    if events:
        if ev_g:
            sources.append({"id": "glide", "label": "GLIDE (catastrophes)", "n": len(ev_g)})
        if ev_i:
            sources.append({"id": "idmc", "label": "IDMC (déplacements dus aux catastrophes)", "n": len(ev_i)})
        lat = np.array([e["lat"] for e in events]); lon = np.array([e["lon"] for e in events])
        for e, pc in zip(events, locate_points(args.country, lon, lat)):
            e["u"] = pc

    # le jeu HRP contient un CSV par année : on les lit tous
    hrp_frames = []
    try:
        for x in hdx_resources(h.get("hrp_dataset", "hrp-projects-mdg")):
            if x["format"].upper() == "CSV" and x["name"].lower().startswith("fmdg"):
                r = requests.get(x["url"], headers=UA, timeout=240)
                d = pd.read_csv(io.BytesIO(r.content), low_memory=False)
                if len(d) and str(d.iloc[0].get("startDate", "")).startswith("#"):
                    d = d.iloc[1:]
                hrp_frames.append(d)
    except Exception as e:
        print(f"  HRP indisponible : {e}")
    if hrp_frames:
        hrp = parse_hrp(pd.concat(hrp_frames), units)
        parts.append(("hrp", hrp))
        sources.append({"id": "hrp", "label": "Projets des plans de réponse (OCHA/FTS)", "n": int(len(hrp))})

    ia = fetch_csv(h.get("iati_dataset", "iati-mdg"), lambda x: "locations" in x["name"].lower(), "IATI")
    if ia is not None:
        iat = parse_iati(ia)
        if len(iat):
            iat["pcode"] = ""
            keys = iat[["lat", "lon"]].drop_duplicates()
            loc = dict(zip(zip(keys.lat, keys.lon), locate_points(args.country, keys.lon.to_numpy(), keys.lat.to_numpy())))
            iat["pcode"] = [loc[(a, b)] for a, b in zip(iat.lat, iat.lon)]
            iat = iat[iat.pcode != ""]
            parts.append(("iati", iat))
            sources.append({"id": "iati", "label": "Activités des partenaires (IATI, géolocalisées)", "n": int(len(iat))})

    inputs_dir = __import__("pathlib").Path(__file__).resolve().parent.parent / "inputs"
    warnings, frames3 = [], []
    for name in ("reponses_humanitaires.csv", "interventions.csv"):
        path = inputs_dir / name
        if not path.exists():
            continue
        d3 = pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")
        if not len(d3):
            continue
        try:
            r3, w3 = parse_3w(d3, units)
        except ValueError as e:
            warnings.append(f"{name} : {e}")
            continue
        warnings += [f"{name} : {x}" for x in w3]
        frames3.append(r3)
    if frames3:
        r3 = pd.concat(frames3, ignore_index=True)
        parts.append(("3w", r3))
        sources.append({"id": "3w", "label": "Import 3W/4W (gestionnaires d'information)", "n": int(len(r3))})
    for w in warnings[:20]:
        print("  3W :", w)

    out = pack(parts)
    out.update({"events": events, "event_types": TYPES, "sources": sources, "warnings": warnings[:50],
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "notes": ["Les sources publiques ne donnent pas de bénéficiaires par zone : seule la couche « 3W » en contient.",
                          "IATI : budget engagé réparti également sur les années d'activité (présence, pas résultat).",
                          "HRP : les projets sans lieu précis sont rattachés au niveau national (non cartographiés)."]})
    write_json(country_docs_dir(args.country) / "response.json", out)
    print(f"Historique : {len(events)} événements, {len(out['rec']['u'])} lignes de réponse/présence ; sources : {[s['id'] for s in sources]}")


if __name__ == "__main__":
    main()
