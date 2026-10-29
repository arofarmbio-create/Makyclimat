"""Prévision saisonnière hybride (multi-modèles C3S + ENSO/IOD) par région : validation et prévision de la saison à venir.

Protocole fixé avant les calculs : validation/protocole_saisonnier_multimodele.md.
Entrées : data/<pays>/c3s/*.npz (scripts/build_c3s_seasonal.py), monthly_series.npz (CHIRPS), ONI et DMI.
Sorties : validation/saisonnier_multimodele.md, validation/saisonnier_multimodele_regions.csv,
docs/data/<pays>/seasonal_mme.json (prévision des seules régions prévisibles par l'approche principale).
Usage : python scripts/validate_c3s_hybrid.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
from math import comb

import numpy as np
import pandas as pd

import build_teleconnections as TC
from common import DATA_DIR, country_data_dir, country_docs_dir, grid_dir, load_grid, read_units, write_json

TARGETS = {"ndj": (2, 3, 4), "jfm": (4, 5, 6)}           # échéances (mois) depuis une émission le 1er octobre
TARGET_MONTHS = {"ndj": (11, 12, 1), "jfm": (1, 2, 3)}
LABELS = {"ndj": "novembre-janvier", "jfm": "janvier-mars"}
SPLIT = 2008                                              # saisons terminées jusqu'en 2008 : ajustement chronologique
MAIN = "hybride"
N_PERM = 300
RNG = np.random.default_rng(20261029)


def system_series(path, units):
    """Cumul régional de la moyenne d'ensemble par cible -> {cible: DataFrame(index = année de fin de saison, colonnes = adm1)}."""
    z = np.load(path)
    ens = np.nanmean(z["pluie"].astype("float32"), axis=1)                      # année, échéance, lat, lon
    lat, lon = z["lat"], z["lon"]
    leaves = units[units.level == 4].reset_index(drop=True)
    iy = np.abs(leaves.lat.to_numpy()[:, None] - lat[None]).argmin(1)
    ix = np.abs(leaves.lon.to_numpy()[:, None] - lon[None]).argmin(1)
    w = leaves.area_km2.fillna(1.0).to_numpy()
    leads = list(z["leads"])
    out = {}
    for tk, ld in TARGETS.items():
        tot = sum(ens[:, leads.index(k)] for k in ld)[:, iy, ix]                  # année, fokontany
        reg = {pc: tot[:, ix_].dot(w[ix_]) / w[ix_].sum() for pc, ix_ in leaves.groupby("adm1").indices.items()}
        out[tk] = pd.DataFrame(reg, index=[int(y) + 1 for y in z["years"]])
    return out


def build(kind, sys_x, Xidx, tr, te):
    """Prédicteurs (entraînement, test) d'une approche ; standardisation des systèmes sur l'entraînement seulement."""
    cols = []
    if kind.startswith("sys:"):
        x = sys_x[kind[4:]]
        return x[tr, None], x[te, None]
    if kind in ("mme", "hybride", "hybride_complet"):
        zs_tr, zs_te = [], []
        for x in sys_x.values():
            m, s = x[tr].mean(), x[tr].std(ddof=1)
            zs_tr.append((x[tr] - m) / s); zs_te.append((x[te] - m) / s)
        cols.append((np.mean(zs_tr, 0), np.mean(zs_te, 0)))
    if kind in ("stat_oni", "stat_oni_dmi", "hybride_complet"):
        cols.append((Xidx["oni"][tr], Xidx["oni"][te]))
    if kind in ("stat_oni_dmi", "hybride", "hybride_complet"):
        cols.append((Xidx["dmi"][tr], Xidx["dmi"][te]))
    return np.column_stack([c[0] for c in cols]), np.column_stack([c[1] for c in cols])


def loo_pred(kind, sys_x, Xidx, y):
    n = len(y)
    pred = np.empty(n)
    for i in range(n):
        tr = np.arange(n) != i
        Xtr, Xte = build(kind, sys_x, Xidx, tr, ~tr)
        mu, sd = y[tr].mean(), y[tr].std(ddof=1)
        p, _ = TC.fit_predict(Xtr, (y[tr] - mu) / sd, Xte)
        pred[i] = p[0] * sd + mu
    return pred


def evaluate(kind, sys_x, Xidx, y, years):
    pred = loo_pred(kind, sys_x, Xidx, y)
    r0 = np.corrcoef(pred, y)[0, 1]
    out = {"r_loo": float(r0), "msss_loo": TC.msss(y, pred, TC.loo_climatology(y))}
    tr = years <= SPLIT
    Xtr, Xte = build(kind, sys_x, Xidx, tr, ~tr)
    p, _ = TC.fit_predict(Xtr, y[tr], Xte)
    out["msss_chrono"] = TC.msss(y[~tr], p, np.full((~tr).sum(), y[tr].mean()))
    c = np.empty(N_PERM)
    for k in range(N_PERM):
        yp = RNG.permutation(y)
        c[k] = np.corrcoef(loo_pred(kind, sys_x, Xidx, yp), yp)[0, 1]
    out["p_perm"] = float((1 + np.sum(c >= r0)) / (N_PERM + 1))
    return out


def sign_test(wins: int, n: int) -> float:
    """p unilatéral (gagner plus d'une fois sur deux)."""
    return float(sum(comb(n, k) for k in range(wins, n + 1)) / 2 ** n) if n else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    units = read_units(args.country)
    names = dict(zip(units.pcode, units.name))
    files = sorted((country_data_dir(args.country) / "c3s").glob("*.npz"))
    if not files:
        raise SystemExit("Aucune prévision C3S : lancer scripts/build_c3s_seasonal.py.")
    systems = {f.stem: system_series(f, units) for f in files}
    incomplete = [s for s, v in systems.items() if v["ndj"].loc[1994:2017].isna().any().any()]
    for s in incomplete:                                   # un système sans toutes ses rétroprévisions est écarté
        print(f"::warning::{s} écarté : rétroprévisions incomplètes")
        systems.pop(s)
    ms = load_grid(grid_dir(args.country) / "monthly_series.npz")
    months = [int(m) for m in ms["months"]]
    obs_years = np.array([int(y) for y in ms["years"]])
    reg = TC.region_series(ms, units)
    hind = [y for y in range(1994, 2018) if y in obs_years]                         # saisons terminées 1994-2017
    fc_year = max(int(y) for s in systems.values() for y in s["ndj"].index)       # saison de la prévision opérationnelle
    oni = pd.read_csv(DATA_DIR / "enso" / "oni.csv")
    dmi = TC.read_dmi()
    Xall = TC.predictors(oni, dmi, hind + [fc_year])
    Xidx = {k: Xall.loc[hind, k].to_numpy() for k in ("oni", "dmi")}
    kinds = ["stat_oni", "stat_oni_dmi"] + [f"sys:{s}" for s in systems] + ["mme", "hybride", "hybride_complet"]
    rows, fc = [], []
    for tk, tm in TARGET_MONTHS.items():
        idx = [months.index(m) for m in tm]
        for pc in sorted(reg):
            tot = reg[pc][:, idx].sum(axis=1)
            y = np.array([tot[list(obs_years).index(yy)] for yy in hind])
            sys_x = {s: v[tk].loc[hind, pc].to_numpy() for s, v in systems.items()}
            for kind in kinds:
                rows.append({"adm1": pc, "region": names.get(pc, pc), "cible": tk, "approche": kind,
                             **evaluate(kind, sys_x, Xidx, y, np.array(hind)), "mm_moyen": float(y.mean()), "mm_ecart_type": float(y.std(ddof=1))})
            # prévision opérationnelle par l'approche principale, ajustée sur toutes les rétroprévisions
            sys_all = {s: np.append(sys_x[s], v[tk].loc[fc_year, pc]) for s, v in systems.items()}
            Xi = {k: np.append(Xidx[k], Xall.loc[fc_year, k]) for k in Xidx}
            tr = np.arange(len(hind) + 1) < len(hind)
            Xtr, Xte = build(MAIN, sys_all, Xi, tr, ~tr)
            mu, sd = y.mean(), y.std(ddof=1)
            p, _ = TC.fit_predict(Xtr, (y - mu) / sd, Xte)
            fc.append({"adm1": pc, "region": names.get(pc, pc), "cible": tk, "anomalie_std": float(p[0]),
                       "pct_normale": float(100 + 100 * p[0] * sd / mu), "dmi_disponible": bool(np.isfinite(Xall.loc[fc_year, "dmi"]))})
    df = pd.DataFrame(rows)
    df["signif_fdr10"] = False
    for _, g in df.groupby(["cible", "approche"]):
        df.loc[g.index, "signif_fdr10"] = TC.bh(g.p_perm.to_numpy())
    df["previsible"] = (df.msss_loo > 0) & (df.msss_chrono > 0) & df.signif_fdr10
    prev = df[df.approche == MAIN].set_index(["adm1", "cible"]).previsible
    for x in fc:
        x["previsible"] = bool(prev.get((x["adm1"], x["cible"]), False)) and x["dmi_disponible"]
    vd = DATA_DIR.parent / "validation"
    df.round(4).to_csv(vd / "saisonnier_multimodele_regions.csv", index=False)
    write_md(vd / "saisonnier_multimodele.md", df, fc, systems, hind, fc_year, Xall)
    write_json(country_docs_dir(args.country) / "seasonal_mme.json",
               {"generated": dt.date.today().isoformat(), "season": f"{fc_year - 1}-{fc_year}", "approach": MAIN,
                "systems": sorted(systems), "hindcast": [hind[0], hind[-1]],
                "forecast": [{k: (round(v, 2) if isinstance(v, float) else v) for k, v in x.items()} for x in fc if x["previsible"]]})
    print(df[df.previsible].groupby(["cible", "approche"]).size().to_string())


def write_md(path, df, fc, systems, hind, fc_year, Xall):
    f = lambda v, d=2: "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{d}f}".replace(".", ",")
    L = ["# Prévision saisonnière hybride : multi-modèles C3S + ENSO/IOD, par région", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/validate_c3s_hybrid.py`, selon "
         "`validation/protocole_saisonnier_multimodele.md` (fixé avant les calculs).", "",
         f"- Systèmes C3S ({len(systems)}) : {', '.join(sorted(systems))}. Émission le 1er octobre.",
         f"- Saisons de rétroprévision : {hind[0] - 1}-{hind[0]} à {hind[-1] - 1}-{hind[-1]} ({len(hind)}). Pluie observée : CHIRPS par région.",
         "- Prévisible = MSSS (saison laissée de côté) > 0, MSSS chronologique (ajusté jusqu'en 2008) > 0 et corrélation "
         "significative après contrôle des tests multiples (Benjamini-Hochberg, 10 %).", "",
         "## 1. Comparaison des approches", "",
         "| Cible | Approche | Régions prévisibles | MSSS médian (LOO) | r médian (LOO) |", "|---|---|---|---|---|"]
    for (tk, k), g in df.groupby(["cible", "approche"], sort=False):
        L.append(f"| {LABELS[tk]} | {'**' + k + '**' if k == MAIN else k} | {int(g.previsible.sum())} / {len(g)} | {f(g.msss_loo.median())} | {f(g.r_loo.median())} |")
    L += ["", "## 2. Hypothèses fixées à l'avance", ""]
    for tk in TARGETS:
        g = df[df.cible == tk].pivot(index="adm1", columns="approche", values="msss_loo")
        sys_cols = [c for c in g.columns if c.startswith("sys:")]
        nprev = df[df.cible == tk].groupby("approche").previsible.sum()
        h1 = nprev["mme"] >= nprev[sys_cols].max() and g["mme"].median() >= g[sys_cols].median().max()
        w2, w3 = int((g[MAIN] > g["mme"]).sum()), int((g[MAIN] > g["stat_oni_dmi"]).sum())
        n = len(g)
        L += [f"**{LABELS[tk]}**",
              f"- H1 (MME meilleure que chaque système seul) : régions prévisibles MME {int(nprev['mme'])} contre {int(nprev[sys_cols].max())} "
              f"au mieux pour un système ; MSSS médian {f(g['mme'].median())} contre {f(g[sys_cols].median().max())} -> **{'soutenue' if h1 else 'non soutenue'}**.",
              f"- H2 (hybride > MME) : {w2} régions sur {n}, test du signe p = {f(sign_test(w2, n), 3)} -> **{'soutenue' if sign_test(w2, n) < 0.05 else 'non soutenue'}**.",
              f"- H3 (hybride > statistique ONI + DMI) : {w3} régions sur {n}, p = {f(sign_test(w3, n), 3)} -> **{'soutenue' if sign_test(w3, n) < 0.05 else 'non soutenue'}**.", ""]
    L += ["## 3. Détail par région (approche principale et références)", "",
          "| Région | Cible | MSSS stat. ONI+DMI | MSSS MME | MSSS hybride | p perm. hybride | Prévisible (hybride) |", "|---|---|---|---|---|---|---|"]
    piv = df.pivot_table(index=["region", "cible"], columns="approche", values=["msss_loo", "p_perm", "previsible"], aggfunc="first")
    for (reg, tk), r in piv.iterrows():
        L.append(f"| {reg} | {LABELS[tk]} | {f(r[('msss_loo', 'stat_oni_dmi')])} | {f(r[('msss_loo', 'mme')])} | {f(r[('msss_loo', MAIN)])} | "
                 f"{f(r[('p_perm', MAIN)], 3)} | {'**oui**' if r[('previsible', MAIN)] else 'non'} |")
    L += ["", f"## 4. Prévision {fc_year - 1}-{fc_year} (approche principale, régions prévisibles seulement)", "",
          f"ONI de juillet-septembre {fc_year - 1} : {f(Xall.loc[fc_year, 'oni'])} ; DMI : {f(Xall.loc[fc_year, 'dmi'])}.", ""]
    p = [x for x in fc if x["previsible"]]
    if p:
        L += ["| Région | Période | Anomalie (écart-type) | % de la normale |", "|---|---|---|---|"]
        L += [f"| {x['region']} | {LABELS[x['cible']]} | {f(x['anomalie_std'])} | {round(x['pct_normale'])} % |" for x in sorted(p, key=lambda x: (x["region"], x["cible"]))]
    else:
        L.append("Aucune région prévisible par l'approche principale : la meilleure prévision reste la climatologie.")
    L += ["", "## Limites", "", "- 24 saisons seulement : les intervalles d'incertitude des scores sont larges.",
          "- La prévision opérationnelle compte plus de membres que les rétroprévisions : sa moyenne d'ensemble est un peu moins dispersée.",
          "- Pluie CHIRPS (satellite et stations) comme vérité, elle-même incertaine là où les stations sont rares."]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
