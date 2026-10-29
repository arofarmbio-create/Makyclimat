"""Vérification par l'impact des prévisions d'ensemble de crue GloFAS v4, district par district (protocole :
validation/protocole_verification_impact.md, fixé avant les calculs).

Entrées : reprévisions réduites (scripts/build_glofas_reforecast.py, data/<pays>/reforecast/*.npz) et fiches DesInventar
(scripts/connector_desinventar.py, data/<pays>/external/desinventar.csv, non versionnées).
Sorties (agrégées, sans fiche brute) : validation/verification_impact_glofas.md et validation/verification_impact_scores.csv.
Usage : python scripts/validate_reforecast_impact.py --country mdg [--boot 1000]
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
from pathlib import Path

import numpy as np
import pandas as pd

from common import country_data_dir, locate_points, read_units

ROOT = Path(__file__).resolve().parent.parent
EULER = 0.5772156649
SEASON_MONTHS = (11, 12, 1, 2, 3, 4)
THR_SEASONS = (2003, 2022)        # saisons complètes nov. Y - avr. Y+1 (reprévisions v4 sur EWDS : 2003-2023)
VERIF_SEASONS = (2003, 2018)      # saisons vérifiées (DesInventar jusqu'en 2019)
MIN_SEASONS = 15
RETURN_PERIODS = (2, 5)
Q_MIN = (5.0, 20.0, 50.0)         # référence puis sensibilité
PROB_LEVELS = np.round(np.arange(0.1, 1.0, 0.1), 1)
ALPHAS = np.round(np.arange(0.01, 1.0, 0.01), 2)


# ---------------------------------------------------------------- scores (fonctions pures, testées)

def season_of(d: dt.date) -> int | None:
    """Saison des pluies nov. Y - avr. Y+1 -> Y ; None hors saison."""
    if d.month >= 11:
        return d.year
    if d.month <= 4:
        return d.year - 1
    return None


def gumbel_q(mean, std, T):
    beta = std * math.sqrt(6) / math.pi
    return mean - EULER * beta - beta * math.log(-math.log(1 - 1 / T))


def brier(p, o):
    return float(np.mean((np.asarray(p, float) - np.asarray(o, float)) ** 2))


def auc(p, o):
    """Aire sous la courbe ROC (Mann-Whitney, ex aequo comptés 1/2) ; NaN si une seule classe."""
    p, o = np.asarray(p, float), np.asarray(o, bool)
    n1, n0 = o.sum(), (~o).sum()
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = pd.Series(p).rank().to_numpy()
    return float((r[o].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def contingency(p, o, thr):
    """Taux de détection (POD), taux de fausses alertes (FAR = FA / alertes) et de faux positifs (POFD)."""
    p, o = np.asarray(p, float), np.asarray(o, bool)
    a = p >= thr
    h, fa, mi, cn = (a & o).sum(), (a & ~o).sum(), (~a & o).sum(), (~a & ~o).sum()
    return {"pod": h / (h + mi) if h + mi else np.nan, "far": fa / (h + fa) if h + fa else np.nan,
            "pofd": fa / (fa + cn) if fa + cn else np.nan, "h": int(h), "fa": int(fa), "mi": int(mi), "cn": int(cn)}


def rev(p, o, alpha, thresholds):
    """Valeur économique relative (Richardson 2000) au rapport coût/perte alpha, meilleur seuil parmi thresholds.
    Dépense par cas (perte = 1) : alpha x alertes + ratés ; référence = min(alpha, fréquence) ; parfait = alpha x fréquence."""
    p, o = np.asarray(p, float), np.asarray(o, bool)
    s = o.mean()
    e_clim, e_perf = min(alpha, s), alpha * s
    if e_clim <= e_perf:
        return float("nan"), float("nan")
    best, best_t = -np.inf, np.nan
    for t in thresholds:
        a = p >= t
        e = alpha * a.mean() + (o & ~a).mean()
        v = (e_clim - e) / (e_clim - e_perf)
        if v > best:
            best, best_t = v, t
    return float(best), float(best_t)


def reliability(p, o, bins=(0, 0.05, 0.25, 0.45, 0.65, 0.85, 1.01)):
    p, o = np.asarray(p, float), np.asarray(o, float)
    k = np.digitize(p, bins) - 1
    return [(bins[i], bins[i + 1], int((k == i).sum()), float(p[k == i].mean()) if (k == i).any() else np.nan,
             float(o[k == i].mean()) if (k == i).any() else np.nan) for i in range(len(bins) - 1)]


# ---------------------------------------------------------------- données

def load_months(folder: Path):
    files = sorted(folder.glob("glofas_v4_*.npz"))
    if not files:
        raise SystemExit(f"Aucune reprévision dans {folder} : lancer le workflow 14.")
    return files


def cell_table(files, slug):
    """Union des mailles de rivière, district de chaque maille, maxima saisonniers du contrôle [saison, fenêtre, maille]."""
    keys = {}
    for f in files:
        z = np.load(f)
        for a, b in zip(z["lat"], z["lon"]):
            keys.setdefault((round(float(a), 3), round(float(b), 3)), len(keys))
    seasons = np.arange(THR_SEASONS[0], THR_SEASONS[1] + 1)
    windows = np.load(files[0])["windows"]
    M = np.full((len(seasons), len(windows), len(keys)), np.nan, dtype="float32")
    for f in files:
        z = np.load(f)
        ss = np.array([season_of(dt.date.fromisoformat(str(t))) or -1 for t in z["init"]])
        idx = np.array([keys[(round(float(a), 3), round(float(b), 3))] for a, b in zip(z["lat"], z["lon"])])
        for s in set(ss) & set(seasons):
            mx = z["q"][ss == s, 0].astype("float32").max(axis=0)    # contrôle : fenêtre x mailles du mois
            si = int(s - seasons[0])
            M[si][:, idx] = np.fmax(M[si][:, idx], mx)
    lat = np.array([k[0] for k in keys]); lon = np.array([k[1] for k in keys])
    units = read_units(slug).set_index("pcode")
    fk = locate_points(slug, lon, lat)
    dist = np.array([units.at[c, "adm2"] if c else "" for c in fk])
    return keys, dist, seasons, M, windows


def loso_thresholds(M, seasons, test_season, T):
    """Seuil Gumbel par fenêtre et maille, sans la saison testée ; NaN si moins de MIN_SEASONS saisons."""
    keep = seasons != test_season
    X = M[keep]
    n = np.isfinite(X).sum(0)
    with np.errstate(invalid="ignore"):
        m, s = np.nanmean(X, 0), np.nanstd(X, 0, ddof=1)
    beta = s * math.sqrt(6) / math.pi
    q = m - EULER * beta - beta * math.log(-math.log(1 - 1 / T))
    q[n < MIN_SEASONS] = np.nan
    return q


def impacts(slug, units):
    df = pd.read_csv(country_data_dir(slug) / "external" / "desinventar.csv", dtype=str)
    df = df[df.type.isin(["cyclone", "inondation"]) & df.date.notna() & df.adm2_actuel.notna() & (df.date_douteuse != "1")]
    num = lambda c: pd.to_numeric(df[c], errors="coerce").fillna(0)
    df = df[(num("touches") > 0) | (num("maisons_endommagees") > 0) | (num("maisons_detruites") > 0)]
    rows = [(dt.date.fromisoformat(d), a, t) for d, adm, t in zip(df.date, df.adm2_actuel, df.type) for a in adm.split(";")]
    return pd.DataFrame(rows, columns=["date", "adm2", "type"])


# ---------------------------------------------------------------- vérification

def build_cases(files, keys, dist, seasons, M, windows, obs, q_min):
    """Une ligne par (initialisation, district, fenêtre) : probabilités d'ensemble, contrôle, observation."""
    districts = sorted(set(dist) - {""})
    didx = {d: i for i, d in enumerate(districts)}
    cell_d = np.array([didx.get(d, -1) for d in dist])
    obs_by = {d: (np.array(g.date.tolist(), dtype="datetime64[D]"), g.type.to_numpy()) for d, g in obs.groupby("adm2")}
    none = (np.array([], dtype="datetime64[D]"), np.array([]))
    rows = []
    thr_cache = {}
    for f in files:
        z = np.load(f)
        idx = np.array([keys[(round(float(a), 3), round(float(b), 3))] for a, b in zip(z["lat"], z["lon"])])
        for i, init in enumerate(z["init"]):
            t0 = dt.date.fromisoformat(str(init))
            s = season_of(t0)
            if s is None or not VERIF_SEASONS[0] <= s <= VERIF_SEASONS[1]:
                continue
            if s not in thr_cache:
                thr_cache[s] = {T: loso_thresholds(M, seasons, s, T) for T in RETURN_PERIODS}
            q = z["q"][i].astype("float32")                           # membres x fenêtres x mailles (du mois)
            for wi, (lo, hi) in enumerate(windows):
                w0, w1 = np.datetime64(t0 + dt.timedelta(days=int(lo) - 1)), np.datetime64(t0 + dt.timedelta(days=int(hi) + 1))
                q2 = thr_cache[s][2][wi, idx]
                ok = np.isfinite(q2) & (q2 >= q_min) & (cell_d[idx] >= 0)
                dk = cell_d[idx][ok]
                has_river = np.zeros(len(districts), bool)
                has_river[dk] = True
                ex = {}
                for T in RETURN_PERIODS:
                    hit = q[:, wi, ok] >= thr_cache[s][T][wi, idx][ok]     # membres x mailles retenues
                    per_d = np.zeros((len(districts), q.shape[0]), bool)
                    np.logical_or.at(per_d, dk, hit.T)
                    ex[T] = per_d
                for k in np.flatnonzero(has_river):
                    dates, types = obs_by.get(districts[k], none)
                    sel = (dates >= w0) & (dates <= w1)
                    rows.append({"init": t0, "season": s, "adm2": districts[k], "window": f"{lo}-{hi}",
                                 **{f"p{T}": float(ex[T][k].mean()) for T in RETURN_PERIODS},
                                 **{f"c{T}": float(ex[T][k, 0]) for T in RETURN_PERIODS},
                                 "obs": int(sel.any()), "obs_cyclone": int((types[sel] == "cyclone").any()),
                                 "obs_inondation": int((types[sel] == "inondation").any())})
    return pd.DataFrame(rows)


def clim_reference(cases):
    """Fréquence d'impact du district par fenêtre, calculée sans la saison testée."""
    tot = cases.groupby(["adm2", "window"]).obs.agg(["sum", "count"])
    per = cases.groupby(["adm2", "window", "season"]).obs.agg(["sum", "count"])
    j = per.join(tot, rsuffix="_tot")
    j["clim"] = (j["sum_tot"] - j["sum"]) / (j["count_tot"] - j["count"]).clip(lower=1)
    return cases.join(j["clim"], on=["adm2", "window", "season"])["clim"].to_numpy()


def scores(c, T):
    p, ctl, o, cl = c[f"p{T}"].to_numpy(), c[f"c{T}"].to_numpy(), c.obs.to_numpy(), c.clim.to_numpy()
    bs, bsc, bsr = brier(p, o), brier(ctl, o), brier(cl, o)
    return {"n": len(c), "n_obs": int(o.sum()), "auc_ens": auc(p, o), "auc_ctl": auc(ctl, o),
            "bs_ens": bs, "bs_ctl": bsc, "bs_clim": bsr, "bss_ens": 1 - bs / bsr if bsr else np.nan,
            "bss_ctl": 1 - bsc / bsr if bsr else np.nan}


def bootstrap(c, T, n_boot, rng):
    ss = c.season.unique()
    groups = {s: g for s, g in c.groupby("season")}
    out = []
    for _ in range(n_boot):
        b = pd.concat([groups[s] for s in rng.choice(ss, len(ss))])
        r = scores(b, T)
        out.append((r["auc_ens"], r["auc_ctl"], r["bss_ens"], r["auc_ens"] - r["auc_ctl"]))
    a = np.array(out)
    return {k: (float(np.nanpercentile(a[:, i], 2.5)), float(np.nanpercentile(a[:, i], 97.5)))
            for i, k in enumerate(("auc_ens", "auc_ctl", "bss_ens", "auc_diff"))}


def fmt(x, nd=2):
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{nd}f}".replace(".", ",")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--boot", type=int, default=1000)
    args = ap.parse_args()
    rng = np.random.default_rng(20261029)
    files = load_months(country_data_dir(args.country) / "reforecast")
    units = read_units(args.country)
    keys, dist, seasons, M, windows = cell_table(files, args.country)
    obs = impacts(args.country, units)
    # biais de déclaration : seules les saisons où la base contient au moins une fiche cyclone/inondation
    reported = {season_of(d) for d in obs.date} - {None}
    res, rel, val, lines = [], [], [], []
    for q_min in Q_MIN:
        cases = build_cases(files, keys, dist, seasons, M, windows, obs, q_min)
        cases = cases[cases.season.isin(reported)].reset_index(drop=True)
        cases["clim"] = clim_reference(cases)
        for subset, mask in (("tous", np.ones(len(cases), bool)),
                             ("districts ayant déclaré", cases.adm2.isin(obs.adm2.unique()).to_numpy())):
            for w in cases.window.unique():
                c = cases[mask & (cases.window == w).to_numpy()]
                for T in RETURN_PERIODS:
                    r = {"q_min": q_min, "sous_ensemble": subset, "fenetre": w, "T": T, **scores(c, T)}
                    if q_min == Q_MIN[0] and subset == "tous":
                        r.update({f"ic_{k}": v for k, v in bootstrap(c, T, args.boot, rng).items()})
                        for pl in PROB_LEVELS:
                            val.append({"fenetre": w, "T": T, "seuil_proba": pl, **contingency(c[f"p{T}"], c.obs, pl)})
                        for a in ALPHAS:
                            ve, te = rev(c[f"p{T}"], c.obs, a, PROB_LEVELS)
                            vc, _ = rev(c[f"c{T}"], c.obs, a, [0.5])
                            val.append({"fenetre": w, "T": T, "alpha": a, "rev_ens": ve, "seuil_opt": te, "rev_ctl": vc})
                        for lo, hi, n, pm, om in reliability(c[f"p{T}"], c.obs):
                            rel.append({"fenetre": w, "T": T, "classe": f"{lo:.2f}-{min(hi, 1):.2f}", "n": n, "p_moy": pm, "freq_obs": om})
                        for kind in ("cyclone", "inondation"):
                            o = c[f"obs_{kind}"]
                            res.append({"q_min": q_min, "sous_ensemble": f"impacts {kind}", "fenetre": w, "T": T,
                                        "n": len(c), "n_obs": int(o.sum()), "auc_ens": auc(c[f"p{T}"], o), "auc_ctl": auc(c[f"c{T}"], o)})
                    res.append(r)
    out = ROOT / "validation"
    S = pd.DataFrame(res)
    S.to_csv(out / "verification_impact_scores.csv", index=False)
    V = pd.DataFrame(val)
    V.to_csv(out / "verification_impact_valeur.csv", index=False)
    pd.DataFrame(rel).to_csv(out / "verification_impact_fiabilite.csv", index=False)
    write_report(out / "verification_impact_glofas.md", S, V, pd.DataFrame(rel), len(files), len(keys), sorted(reported), obs)


def write_report(path, S, V, R, n_files, n_cells, reported, obs):
    ref = S[(S.q_min == Q_MIN[0]) & (S.sous_ensemble == "tous")]
    L = ["# Vérification par l'impact des prévisions d'ensemble de crue GloFAS v4 (Madagascar, par district)", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/validate_reforecast_impact.py`, selon "
         "`validation/protocole_verification_impact.md` (fixé avant les calculs).", "",
         "**Données**",
         f"- Reprévisions GloFAS v4 (Copernicus EWDS) : {n_files} mois, {n_cells} mailles de rivière, contrôle + 10 membres.",
         f"- Vérité terrain : DesInventar (UNDRR, fiches BNGRC), {len(obs)} fiches district x date (cyclone ou inondation, "
         "au moins une personne touchée ou une maison endommagée). Fiches brutes non republiées.",
         f"- Saisons vérifiées (avec au moins une fiche nationale) : {', '.join(str(s) for s in reported if VERIF_SEASONS[0] <= s <= VERIF_SEASONS[1])}.",
         "- Fausses alertes : borne haute (absence de fiche ≠ absence d'impact).", "",
         "## 1. Compétence (cellules de rivière : crue de 2 ans ≥ 5 m³/s ; IC à 95 % par bootstrap des saisons)", "",
         "| Fenêtre (jours) | Crue | Cas | Impacts | AUC ensemble [IC] | AUC contrôle [IC] | BSS ensemble [IC] |",
         "|---|---|---|---|---|---|---|"]
    for _, r in ref.iterrows():
        L.append(f"| {r.fenetre} | {r['T']} ans | {r.n} | {r.n_obs} | {fmt(r.auc_ens)} [{fmt(r.ic_auc_ens[0])} ; {fmt(r.ic_auc_ens[1])}] | "
                 f"{fmt(r.auc_ctl)} [{fmt(r.ic_auc_ctl[0])} ; {fmt(r.ic_auc_ctl[1])}] | {fmt(r.bss_ens)} [{fmt(r.ic_bss_ens[0])} ; {fmt(r.ic_bss_ens[1])}] |")
    L += ["", "## 2. Hypothèses fixées à l'avance", ""]
    r13 = ref[(ref.fenetre == ref.fenetre.iloc[0]) & (ref["T"] == 2)].iloc[0]
    L.append(f"- **H1** (AUC ensemble > 0,5 à 1-3 jours, crue de 2 ans) : IC [{fmt(r13.ic_auc_ens[0])} ; {fmt(r13.ic_auc_ens[1])}] -> "
             f"**{'soutenue' if r13.ic_auc_ens[0] > 0.5 else 'non soutenue'}**.")
    a2 = ref[ref["T"] == 2].auc_ens.to_numpy()
    L.append(f"- **H2** (compétence décroissante avec l'échéance) : AUC {' -> '.join(fmt(x) for x in a2)} -> "
             f"**{'soutenue' if np.all(np.diff(a2) <= 0) else 'non soutenue'}** (sans test formel).")
    v = V.dropna(subset=["alpha"])
    v13 = v[(v.fenetre == ref.fenetre.iloc[0]) & (v["T"] == 2)]
    better = v13[(v13.rev_ens > v13.rev_ctl.fillna(-np.inf)) & (v13.rev_ens > 0)]
    L.append(f"- **H3** (l'ensemble vaut plus que le contrôle pour une partie des rapports coût/perte, 1-3 jours) : "
             f"{len(better)} rapports sur {len(v13)} -> **{'soutenue' if len(better) else 'non soutenue'}**"
             + (f" (coût/perte de {fmt(better.alpha.min())} à {fmt(better.alpha.max())})." if len(better) else "."))
    cy = S[(S.sous_ensemble == "impacts cyclone") & (S["T"] == 2)]
    fl = S[(S.sous_ensemble == "impacts inondation") & (S["T"] == 2)]
    L.append(f"- **H4** (plus compétent pour les impacts cycloniques) : AUC cyclone {', '.join(fmt(x) for x in cy.auc_ens)} ; "
             f"inondation non cyclonique {', '.join(fmt(x) for x in fl.auc_ens)} (effectifs : {', '.join(str(x) for x in fl.n_obs)} impacts) -> "
             "à lire avec prudence si les effectifs sont faibles.")
    L += ["", "## 3. Sensibilité au critère de rivière", "", "| Crue de 2 ans ≥ | Fenêtre | AUC ensemble (2 ans) | BSS ensemble |", "|---|---|---|---|"]
    for _, r in S[(S.sous_ensemble == "tous") & (S["T"] == 2)].iterrows():
        L.append(f"| {r.q_min:g} m³/s | {r.fenetre} | {fmt(r.auc_ens)} | {fmt(r.bss_ens)} |")
    L += ["", "## 4. Fiabilité (crue de 2 ans)", "", "| Fenêtre | Classe de probabilité | Cas | Probabilité moyenne | Fréquence observée |", "|---|---|---|---|---|"]
    for _, r in R[R["T"] == 2].iterrows():
        L.append(f"| {r.fenetre} | {r.classe} | {r.n} | {fmt(r.p_moy)} | {fmt(r.freq_obs)} |")
    L += ["", "Détail : `validation/verification_impact_scores.csv`, `verification_impact_valeur.csv` (détection, fausses alertes, "
          "valeur économique relative par rapport coût/perte), `verification_impact_fiabilite.csv`."]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
