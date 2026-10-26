"""Validation sur événements réels : nos indicateurs désignent-ils les régions que les rapports disent touchées ?

Pour chaque cyclone documenté (validation/evenements.csv, validation/zones_touchees.csv, chaque ligne avec sa source), par région :
  - EMPREINTE DU VENT : part de la population dont le fokontany est dans les rayons de vent 34, 50 et 64 nœuds publiés par le JTWC
    (IBTrACS, quatre quadrants, interpolés toutes les heures entre deux positions) ;
  - PLUIE : cumul maximal sur 3 jours (CHIRPS journalier), puis son caractère exceptionnel LOCAL : période de retour empirique
    (N+1)/(1+nombre de saisons 2006-2020 au moins aussi fortes) et rapport à la médiane des maxima annuels, au 90e centile des fokontany.
Un modèle logistique simple (3 variantes : vent seul, pluie seule, les deux) estime la probabilité qu'une région soit citée touchée.
Il est évalué en « laisser un événement de côté » : l'événement testé n'est jamais vu pendant l'apprentissage.
Limites : listes de régions des rapports partielles (région non citée ≠ épargnée) : l'AUC est prudente, la part de fausses alertes est
majorée ; peu d'événements ; l'exposition n'est pas l'impact (pas de vulnérabilité ici). Résultats indicatifs.
Usage : python scripts/validate_events.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import io

import numpy as np
import pandas as pd

from common import DATA_DIR, country_docs_dir, grid_dir, load_config, read_units, write_json

VAL_DIR = DATA_DIR.parent / "validation"
KM_LAT, KM_LON0 = 110.57, 111.32
NM = 1.852
QUADS = ("NE", "SE", "SW", "NW")                 # bearing 0-90, 90-180, 180-270, 270-360
RADCOLS = [f"USA_R{k}_{q}" for k in (34, 50, 64) for q in QUADS]
USECOLS = ["SID", "SEASON", "NAME", "ISO_TIME", "NATURE", "LAT", "LON", "WMO_WIND", "USA_WIND", "TRACK_TYPE"] + RADCOLS
VARIANTS = {"vent seul": ["cov34", "cov64"], "pluie seule": ["lrp", "lratio"], "vent et pluie": ["cov34", "cov64", "lrp", "lratio"]}


# ------------------------------------------------------------------ outils statistiques
def auc(score, pos) -> float:
    s, p = np.asarray(score, float), np.asarray(pos, bool)
    if p.sum() == 0 or (~p).sum() == 0:
        return float("nan")
    from scipy.stats import rankdata
    r = rankdata(s)
    return float((r[p].sum() - p.sum() * (p.sum() + 1) / 2) / (p.sum() * (~p).sum()))


def fit_logit(X, y, lam=1.0):
    """Régression logistique L2, classes équilibrées ; X déjà standardisé. Retourne (intercept, coefficients)."""
    from scipy.optimize import minimize
    X = np.asarray(X, float); y = np.asarray(y, float)
    n, k = X.shape
    w = np.where(y == 1, 0.5 / max(y.sum(), 1), 0.5 / max((1 - y).sum(), 1)) * n

    def f(b):
        z = b[0] + X @ b[1:]
        p = 1 / (1 + np.exp(-z))
        eps = 1e-12
        ll = -(w * (y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps))).sum() / n + lam * (b[1:] ** 2).sum() / n
        g = (w * (p - y))
        return ll, np.r_[g.sum() / n, X.T @ g / n + 2 * lam * b[1:] / n]

    r = minimize(f, np.zeros(k + 1), jac=True, method="L-BFGS-B")
    return float(r.x[0]), r.x[1:]


def predict(model, X):
    mu, sd, b0, b = model
    z = b0 + ((np.asarray(X, float) - mu) / sd) @ b
    return 1 / (1 + np.exp(-z))


def train(X, y, lam=1.0):
    X = np.asarray(X, float)
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd[sd < 1e-9] = 1.0
    b0, b = fit_logit((X - mu) / sd, y, lam)
    return mu, sd, b0, b


def confusion(flag, pos):
    flag, pos = np.asarray(flag, bool), np.asarray(pos, bool)
    tp, fp, fn = int((flag & pos).sum()), int((flag & ~pos).sum()), int((~flag & pos).sum())
    pod = tp / (tp + fn) if tp + fn else float("nan")
    far = fp / (tp + fp) if tp + fp else float("nan")
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    return tp, fp, fn, pod, far, f1


def best_threshold(p, y):
    cand = np.unique(np.round(p, 3))
    best, bf = 0.5, -1.0
    for t in cand:
        f1 = confusion(p >= t, y)[5]
        if f1 > bf:
            best, bf = float(t), f1
    return best


def loeo(feat: pd.DataFrame, cols: list[str], lam=1.0) -> dict:
    """Évaluation en laissant chaque événement de côté."""
    evs = sorted(feat.evenement.unique())
    oof = np.full(len(feat), np.nan)
    per = []
    for held in evs:
        tr, te = (feat.evenement != held).values, (feat.evenement == held).values
        if feat.loc[tr, "pos"].sum() == 0:
            continue
        m = train(feat.loc[tr, cols].values, feat.loc[tr, "pos"].values, lam)
        oof[te] = predict(m, feat.loc[te, cols].values)
        t = best_threshold(predict(m, feat.loc[tr, cols].values), feat.loc[tr, "pos"].values)
        tp, fp, fn, pod, far, f1 = confusion(oof[te] >= t, feat.loc[te, "pos"].values)
        per.append({"evenement": held, "auc": auc(oof[te], feat.loc[te, "pos"].values), "seuil": t, "tp": tp, "fp": fp, "fn": fn,
                    "pod": pod, "far": far, "f1": f1})
    ok = np.isfinite(oof)
    y = feat["pos"].values.astype(float)
    pooled = {"auc": auc(oof[ok], y[ok]), "brier": float(np.mean((oof[ok] - y[ok]) ** 2)),
              "brier_climato": float(np.mean((y[ok].mean() - y[ok]) ** 2))}
    tp = sum(p["tp"] for p in per); fp = sum(p["fp"] for p in per); fn = sum(p["fn"] for p in per)
    pooled.update({"pod": tp / (tp + fn) if tp + fn else float("nan"), "far": fp / (tp + fp) if tp + fp else float("nan"), "tp": tp, "fp": fp, "fn": fn})
    bins = []
    for lo, hi in [(0, .2), (.2, .4), (.4, .6), (.6, .8), (.8, 1.0001)]:
        m = ok & (oof >= lo) & (oof < hi)
        if m.sum():
            bins.append({"de": lo, "a": min(hi, 1.0), "n": int(m.sum()), "annoncee": float(oof[m].mean()), "observee": float(y[m].mean())})
    return {"par_evenement": per, "global": pooled, "fiabilite": bins}


def evaluate(feat: pd.DataFrame) -> dict:
    out = {"variantes": {}, "evenements": []}
    for name, cols in VARIANTS.items():
        use = [c for c in cols if c in feat and feat[c].std() > 0]
        if use:
            out["variantes"][name] = {"colonnes": use, **loeo(feat, use)}
    for ev, g in feat.groupby("evenement"):
        row = {"evenement": ev, "n_regions": int(len(g)), "n_documentees": int(g.pos.sum())}
        for c in ["cov34", "cov64", "lrp", "lratio", "rx3"]:
            if c in g:
                row[f"auc_{c}"] = auc(g[c].values, g.pos.values)
        out["evenements"].append(row)
    return out


# ------------------------------------------------------------------ vent : empreinte par quadrants
def project(lon, lat):
    return (np.asarray(lon) - 47.0) * KM_LON0 * np.cos(np.deg2rad(-19.0)), np.asarray(lat) * KM_LAT


def footprint(g: pd.DataFrame, lons, lats, substeps=6):
    """Booléens (par point) : dans le rayon de vent 34, 50, 64 nœuds d'au moins une position du système (interpolée)."""
    X, Y = project(lons, lats)
    xc, yc = project(g.LON.values, g.LAT.values)
    rad = {k: np.column_stack([pd.to_numeric(g[f"USA_R{k}_{q}"], errors="coerce").values for q in QUADS]) * NM for k in (34, 50, 64)}
    kt = g.kt.values
    # positions à vent >= 34 kt sans rayon : rayon médian du système (ou 110 km à défaut)
    r34 = rad[34]
    fallback = np.nanmedian(r34) if np.isfinite(r34).any() else 110.0
    miss = np.isfinite(kt) & (kt >= 34) & ~np.isfinite(r34).any(axis=1)
    r34[miss] = fallback
    for k in (50, 64):                                       # sans rayon publié = pas de vent de ce niveau connu
        rad[k] = np.nan_to_num(rad[k], nan=0.0)
    rad[34] = np.nan_to_num(rad[34], nan=0.0)
    cov = {k: np.zeros(len(X), bool) for k in (34, 50, 64)}
    n = len(g)
    for i in range(n):
        last = i == n - 1
        for f in ([0.0] if last else np.linspace(0, 1, substeps, endpoint=False)):
            j = i if last else i + 1
            x0, y0 = xc[i] * (1 - f) + xc[j] * f, yc[i] * (1 - f) + yc[j] * f
            dx, dy = X - x0, Y - y0
            d = np.hypot(dx, dy)
            q = ((np.degrees(np.arctan2(dx, dy)) % 360) // 90).astype(int)
            for k in (34, 50, 64):
                r = rad[k][i] * (1 - f) + rad[k][j] * f
                cov[k] |= d <= r[q]
    return cov, int(miss.sum()), int((np.isfinite(kt) & (kt >= 34)).sum())


def region_shares(cov, leaves: pd.DataFrame):
    pop = leaves["pop"].fillna(0).values
    out = {}
    for pc, idx in leaves.groupby("adm1").indices.items():
        tot = max(pop[idx].sum(), 1e-9)
        out[pc] = {f"cov{k}": float(pop[idx][cov[k][idx]].sum() / tot) for k in (34, 50, 64)}
    return out


# ------------------------------------------------------------------ pluie
def rain_features(v: np.ndarray, leaves: pd.DataFrame, annual: np.ndarray | None):
    from chirps_daily import roll3_max
    rx3 = roll3_max(v)
    res = {}
    if annual is not None:
        N = annual.shape[0]
        rp = (N + 1) / (1 + (annual >= rx3[None, :]).sum(axis=0))
        ratio = rx3 / np.maximum(np.median(annual, axis=0), 1.0)
    for pc, idx in leaves.groupby("adm1").indices.items():
        r = {"rx3": float(np.nanpercentile(rx3[idx], 90))}
        if annual is not None:
            r["rp90"] = float(np.nanpercentile(np.clip(rp[idx], 1, N + 1), 90))
            r["ratio90"] = float(np.nanpercentile(ratio[idx], 90))
            r["lrp"] = float(np.log(r["rp90"]))
            r["lratio"] = float(np.log(max(r["ratio90"], 0.05)))
        res[pc] = r
    return res


def fetch_ibtracs(since=2000):
    import requests
    from build_cyclones import URL, clean
    r = requests.get(URL, timeout=600, headers={"User-Agent": "MakyClimat (recherche doctorale)"})
    r.raise_for_status()
    raw = pd.read_csv(io.BytesIO(r.content), skiprows=[1], usecols=USECOLS, low_memory=False)
    d = clean(raw, since, [38.0, -30.0, 58.0, -6.0])
    d["nom"] = d.NAME.astype(str).str.title()
    return d


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    from build_cyclones import KM_LAT as _k, KM_LON0 as _k0  # noqa: F401
    from chirps_daily import days_between, leaf_series
    from scipy.spatial import cKDTree
    full = load_config(args.country)
    bbox = full["map"]["bbox"]
    units = read_units(args.country)
    leaves = units[units.level == 4].reset_index(drop=True)
    ev = pd.read_csv(VAL_DIR / "evenements.csv")
    truth = pd.read_csv(VAL_DIR / "zones_touchees.csv")
    reg = units[units.level == 1]
    names = dict(zip(reg.name, reg.pcode))
    annual = None
    p = grid_dir(args.country) / "rx3_annual.npz"
    if p.exists():
        z = np.load(p)
        if (z["codes"] == leaves.pcode.values).all():
            annual = z["rx3"]
            print(f"climatologie locale des pluies extrêmes : {annual.shape[0]} saisons")
    d_all = fetch_ibtracs()
    LX, LY = project(leaves.lon.values, leaves.lat.values)
    tree = cKDTree(np.c_[LX, LY])
    sampler, rows, notes = None, [], []
    for _, e in ev[ev.type == "cyclone"].iterrows():
        t = truth[truth.evenement == e.id]
        if t.empty:
            continue
        yr = int(str(e.date_debut)[:4])
        g = d_all[(d_all.nom == e.nom) & (d_all.time.dt.year.isin([yr, yr + 1]))]
        if g.empty:
            print("trajectoire introuvable", e.id)
            continue
        g = g[g.SID == g.SID.iloc[0]].reset_index(drop=True)
        x, y = project(g.LON.values, g.LAT.values)
        dist, _ = tree.query(np.c_[x, y])
        near = g[dist <= 400]
        if near.empty:
            continue
        cov, miss, n34 = footprint(g[(g.time >= near.time.min() - pd.Timedelta(hours=12)) & (g.time <= near.time.max() + pd.Timedelta(hours=12))].reset_index(drop=True), leaves.lon.values, leaves.lat.values)
        wind = region_shares(cov, leaves)
        days = days_between(near.time.min().date() - dt.timedelta(days=1), near.time.max().date() + dt.timedelta(days=1))
        try:
            v, sampler = leaf_series(days, bbox, leaves.lon.values, leaves.lat.values, sampler)
            if np.isnan(v).all(axis=1).any():
                raise RuntimeError("jour de pluie absent")
            rainf = rain_features(v, leaves, annual)
        except Exception as ex:  # noqa: BLE001
            print("pluie indisponible", e.id, ex)
            rainf = {}
        pos = {names[r] for r in t.region if r in names}
        for pc in wind:
            rows.append({"evenement": e.id, "region": pc, "pos": pc in pos, **wind[pc], **rainf.get(pc, {})})
        print(f"{e.id}: {days[0]}..{days[-1]}, rayons de vent manquants {miss}/{n34} positions >= 34 kt, pluie={'oui' if rainf else 'non'}")
    feat = pd.DataFrame(rows)
    need = [c for c in ("lrp", "lratio", "rx3") if c in feat]
    feat = feat.dropna(subset=need).reset_index(drop=True)
    res = evaluate(feat)
    nm = dict(zip(reg.pcode, reg.name))
    feat["nom_region"] = feat.region.map(nm)
    VAL_DIR.mkdir(exist_ok=True)
    feat.to_csv(VAL_DIR / "cyclones_indicateurs_par_region.csv", index=False)
    pd.DataFrame(res["evenements"]).to_csv(VAL_DIR / "cyclones_auc_par_evenement.csv", index=False)
    summ = [{"variante": n, **v["global"]} for n, v in res["variantes"].items()]
    pd.DataFrame(summ).to_csv(VAL_DIR / "cyclones_modeles.csv", index=False)
    rows2 = []
    for n, v in res["variantes"].items():
        for r in v["par_evenement"]:
            rows2.append({"variante": n, **r})
    pd.DataFrame(rows2).to_csv(VAL_DIR / "cyclones_laisser_un_de_cote.csv", index=False)
    # modèle final (tous les événements) : coefficients publiés
    final = {}
    for n, v in res["variantes"].items():
        mu, sd, b0, b = train(feat[v["colonnes"]].values, feat["pos"].values)
        final[n] = {"colonnes": v["colonnes"], "moyenne": mu.tolist(), "ecart_type": sd.tolist(), "intercept": b0, "coefficients": b.tolist()}
    write_json(VAL_DIR / "modele_cyclone.json", final)
    write_json(country_docs_dir(args.country) / "validation.json", {"generated": dt.date.today().isoformat(), "cyclones": res, "modele": final,
               "annee_climato": None if annual is None else int(annual.shape[0]),
               "notes": ["Listes de régions touchées partielles (rapports OCHA/IFRC/presse) : AUC prudente, fausses alertes majorées.",
                         "Évaluation en laissant chaque événement de côté ; peu d'événements : résultats indicatifs."]})
    print(pd.DataFrame(summ).round(2).to_string())
    print(pd.DataFrame(res["evenements"]).round(2).to_string())


if __name__ == "__main__":
    main()
