"""Intensité infra-journalière (IMERG 1 h / 3 h / 6 h) contre cumul (24 h / 72 h) pour détecter les inondations pluviales
du périmètre pilote. Protocole fixé avant les calculs : validation/protocole_intensite_imerg.md.

Entrées : data/<pays>/imerg/imerg_<saison>.npz (scripts/build_imerg_pilot.py), validation/evenements.csv,
data/<pays>/external/desinventar.csv (scripts/connector_desinventar.py, non versionné), validation/evenements_gdacs.csv.
Sorties : validation/intensite_imerg.md, validation/intensite_imerg_scores.csv.
Usage : python scripts/validate_imerg_pluvial.py --country mdg [--boot 1000]
"""
from __future__ import annotations

import argparse
import datetime as dt
import re

import numpy as np
import pandas as pd

from common import country_data_dir, read_units
from validate_floods import SHARE, SHARES, VAL, episodes, ev_window, matches
from validate_reforecast_impact import auc

DURATIONS = (1, 3, 6, 24, 72)          # heures
MIN_VALID = 0.8                        # part minimale de pas de 30 min valides dans une fenêtre


def daily_max(P: np.ndarray, hours: int) -> np.ndarray:
    """P[pas de 30 min, maille] en mm/h -> maximum journalier du cumul glissant sur `hours` heures (mm), [jour, maille]."""
    n = hours * 2
    d = np.nan_to_num(P, nan=0.0) * 0.5
    v = np.isfinite(P).astype("float32")
    cs = np.vstack([np.zeros((1, P.shape[1])), np.cumsum(d, 0)])
    cv = np.vstack([np.zeros((1, P.shape[1])), np.cumsum(v, 0)])
    R = np.full(P.shape, np.nan, dtype="float32")
    R[n - 1:] = cs[n:] - cs[:-n]
    ok = np.zeros(P.shape, bool)
    ok[n - 1:] = (cv[n:] - cv[:-n]) >= MIN_VALID * n
    R[~ok] = np.nan
    with np.errstate(invalid="ignore"):
        return np.nanmax(R.reshape(-1, 48, P.shape[1]), axis=1)


def loso_levels(smax: np.ndarray, i: int):
    """Seuils (médiane, 80e centile) des maxima saisonniers par maille, sans la saison i."""
    X = np.delete(smax, i, axis=0)
    return np.nanmedian(X, 0), np.nanpercentile(X, 80, axis=0)


def load(country):
    files = sorted((country_data_dir(country) / "imerg").glob("imerg_*.npz"))
    if not files:
        raise SystemExit("Aucune saison IMERG : lancer le workflow 17.")
    th = pd.read_csv(country_data_dir(country) / "flood_thresholds.csv", dtype={"pcode": str})
    units = read_units(country)
    lv = units[(units.level == 4) & units.adm3.isin(set(th.pcode))]
    z0 = np.load(files[0])
    iy = np.abs(lv.lat.to_numpy()[:, None] - z0["lat"][None]).argmin(1)
    ix = np.abs(lv.lon.to_numpy()[:, None] - z0["lon"][None]).argmin(1)
    cells = sorted(set(zip(iy, ix)))
    seasons = []
    for f in files:
        z = np.load(f)
        P = z["pluie"].astype("float32")[:, [c[0] for c in cells], [c[1] for c in cells]]
        start = dt.date.fromisoformat(str(z["start"]))
        days = [start + dt.timedelta(days=k) for k in range(P.shape[0] // 48)]
        seasons.append({"season": start.year, "days": days, **{h: daily_max(P, h) for h in DURATIONS}})
    return seasons, cells, units, lv


def events(units, lv, country):
    names = dict(zip(units.pcode, units.name))
    regs = sorted(set(lv.adm1))
    reg_names = [names.get(r, r) for r in regs] + (["Antananarivo"] if "MG11" in regs else [])
    allev = pd.read_csv(VAL / "evenements.csv", dtype=str)
    ev = allev[allev.zones_citees.fillna("").str.contains("|".join(map(re.escape, reg_names)))].copy()
    win = [ev_window(a, b) for a, b in zip(ev.date_debut, ev.date_fin)]
    ev["w0"], ev["w1"] = [w[0] for w in win], [w[1] for w in win]
    di_path = country_data_dir(country) / "external" / "desinventar.csv"
    di = pd.DataFrame(columns=["id", "date_debut", "date_fin", "w0", "w1"])
    if di_path.exists():
        d = pd.read_csv(di_path, dtype=str)
        num = lambda c: pd.to_numeric(d[c], errors="coerce").fillna(0)
        keep = d.type.isin(["cyclone", "inondation"]) & d.date.notna() & (d.date_douteuse != "1") & \
            ((num("touches") > 0) | (num("maisons_endommagees") > 0) | (num("maisons_detruites") > 0)) & \
            d.adm2_actuel.fillna("").apply(lambda s: bool(set(s.split(";")) & set(lv.adm2)))
        d = d[keep]
        g = d.groupby("date").size().reset_index()
        di = pd.DataFrame({"id": [f"desinventar-{x}" for x in g.date], "date_debut": g.date, "date_fin": g.date})
        di["w0"] = [(pd.Timestamp(x) - pd.Timedelta(days=1)).date().isoformat() for x in g.date]
        di["w1"] = [(pd.Timestamp(x) + pd.Timedelta(days=1)).date().isoformat() for x in g.date]
    gd = pd.read_csv(VAL / "evenements_gdacs.csv", dtype=str) if (VAL / "evenements_gdacs.csv").exists() else None
    return ev, di, gd, allev[~allev.id.isin(ev.id) & (allev.type != "secheresse")]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--boot", type=int, default=1000)
    args = ap.parse_args()
    rng = np.random.default_rng(20261029)
    seasons, cells, units, lv = load(args.country)
    have = {s["season"] for s in seasons}
    gap = sorted(set(range(2014, max(have) + 1)) - have)
    if gap:                                        # jamais de scores publiés avec des saisons manquantes au milieu
        print(f"::warning::Saisons IMERG manquantes {gap} : rien n'est publié.")
        return
    ev, di, gd, other = events(units, lv, args.country)
    truth = pd.concat([ev[["id", "w0", "w1"]], di[["id", "w0", "w1"]]])
    smax = {h: np.stack([np.nanmax(s[h], 0) for s in seasons]) for h in DURATIONS}
    # part journalière des mailles au-dessus du seuil (vigilance / alerte), seuils sans la saison testée
    for i, s in enumerate(seasons):
        s["label"] = np.array([any(a <= d.isoformat() <= b for a, b in zip(truth.w0, truth.w1)) for d in s["days"]])
        for h in DURATIONS:
            l2, l5 = loso_levels(smax[h], i)
            with np.errstate(invalid="ignore"):
                s[f"f2_{h}"] = np.nanmean(s[h] >= l2, 1)
                s[f"f5_{h}"] = np.nanmean(s[h] >= l5, 1)
    pool = lambda key, ss: (np.concatenate([s[key] for s in ss]), np.concatenate([s["label"] for s in ss]))
    rows, sens, det = [], [], []
    for h in DURATIONS:
        x, y = pool(f"f2_{h}", seasons)
        boots = []
        for _ in range(args.boot):
            ss = [seasons[k] for k in rng.integers(0, len(seasons), len(seasons))]
            boots.append(auc(*pool(f"f2_{h}", ss)))
        rows.append({"duree_h": h, "jours": len(y), "jours_evenement": int(y.sum()), "auc": auc(x, y),
                     "auc_ic_bas": float(np.nanpercentile(boots, 2.5)), "auc_ic_haut": float(np.nanpercentile(boots, 97.5))})
        for _, e in truth.iterrows():
            m = [s[f"f2_{h}"][(np.array([d.isoformat() for d in s["days"]]) >= e.w0) & (np.array([d.isoformat() for d in s["days"]]) <= e.w1)]
                 for s in seasons]
            m = np.concatenate(m)
            if len(m):
                det.append({"duree_h": h, "evenement": e.id, "part_max": float(np.nanmax(m)), "detecte": bool(np.nanmax(m) >= SHARE)})
        for label, sh in SHARES:
            n_ep = n_none = n_true = 0
            for s in seasons:
                for a, b, _ in episodes([d.isoformat() for d in s["days"]], np.nan_to_num(s[f"f2_{h}"]), sh):
                    n_ep += 1
                    m_ev, m_di = matches(a, b, ev), matches(a, b, di)
                    n_true += bool(m_ev or m_di)
                    n_none += not (m_ev or m_di or matches(a, b, other) or matches(a, b, gd))
            sens.append({"duree_h": h, "seuil": label, "episodes": n_ep, "episodes_evenement_perimetre": n_true, "episodes_sans_correspondance": n_none})
    # H1 : différence appariée AUC(3 h) - AUC(72 h), bootstrap par saison
    diffs = []
    for _ in range(args.boot):
        ss = [seasons[k] for k in rng.integers(0, len(seasons), len(seasons))]
        diffs.append(auc(*pool("f2_3", ss)) - auc(*pool("f2_72", ss)))
    S, D, E = pd.DataFrame(rows), pd.DataFrame(det), pd.DataFrame(sens)
    out = pd.concat([S.assign(table="auc"), E.assign(table="episodes"), D.assign(table="detection")])
    out.to_csv(VAL / "intensite_imerg_scores.csv", index=False)
    write_md(VAL / "intensite_imerg.md", S, D, E, np.nanpercentile(diffs, [2.5, 97.5]), seasons, cells, ev, di)
    print(S.to_string())


def write_md(path, S, D, E, ci, seasons, cells, ev, di):
    f = lambda v, d=2: "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{d}f}".replace(".", ",")
    L = ["# Intensité infra-journalière (IMERG) contre cumul, pour les inondations pluviales du périmètre pilote", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/validate_imerg_pluvial.py`, selon "
         "`validation/protocole_intensite_imerg.md` (fixé avant les calculs).", "",
         f"- GPM IMERG V07 Final, pas de 30 min, 0,1° : {len(seasons)} saisons (novembre {seasons[0]['season']} à avril {seasons[-1]['season'] + 1}), "
         f"{len(cells)} mailles contenant au moins un fokontany du périmètre.",
         f"- Événements : {len(ev)} de `evenements.csv` (périmètre), {len(di)} dates DesInventar (districts du périmètre, avec impact).",
         "- Seuils par maille et par durée sans la saison testée ; score = part des mailles au-dessus du seuil de vigilance.", "",
         "## 1. Jours d'événement contre autres jours (aire sous la courbe ROC, IC à 95 % par bootstrap des saisons)", "",
         "| Durée | Jours | Jours d'événement | AUC | IC 95 % |", "|---|---|---|---|---|"]
    for _, r in S.iterrows():
        L.append(f"| {r.duree_h} h | {r.jours} | {r.jours_evenement} | {f(r.auc)} | [{f(r.auc_ic_bas)} ; {f(r.auc_ic_haut)}] |")
    L += ["", f"**H1** (AUC 3 h > AUC 72 h) : différence, IC 95 % [{f(ci[0])} ; {f(ci[1])}] -> "
          f"**{'soutenue' if ci[0] > 0 else ('contredite (le cumul l’emporte)' if ci[1] < 0 else 'non tranchée')}**.", "",
          "## 2. Détection des événements (part des mailles ≥ 10 %)", "", "| Durée | Événements couverts | Détectés |", "|---|---|---|"]
    for h, g in D.groupby("duree_h"):
        L.append(f"| {h} h | {len(g)} | {int(g.detecte.sum())} |")
    L += ["", "## 3. Épisodes et fausses alertes possibles (borne haute)", "",
          "| Durée | Seuil de part | Épisodes | Avec événement du périmètre | Sans aucune correspondance |", "|---|---|---|---|---|"]
    for _, r in E.iterrows():
        L.append(f"| {r.duree_h} h | {r.seuil} | {r.episodes} | {r.episodes_evenement_perimetre} | {r.episodes_sans_correspondance} |")
    L += ["", "## Limites", "", "- IMERG (0,1°, ~11 km) lisse les orages très locaux ; l'inondation urbaine dépend aussi du drainage.",
          "- Peu d'événements : les intervalles sont larges.",
          "- Les fiches DesInventar sont des déclarations ; leur absence n'est pas une absence d'impact."]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
