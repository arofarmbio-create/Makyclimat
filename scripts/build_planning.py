"""Scénarios de planification à 12 mois par région (validation/protocole_planification_12mois.md, fixé avant les calculs).

Émission fin octobre Y, saison novembre Y+1 - avril Y+2. Prédicteurs : ONI et DMI de juillet-septembre Y. Même cadre
de validation que build_teleconnections.py (saison laissée de côté, test chronologique, permutation, Benjamini-Hochberg),
plus un score de probabilité (RPSS) des terciles. Un signal n'est utilisé que s'il passe toutes les épreuves ; sinon
les probabilités restent climatologiques (1/3 chacune) et l'outil le dit.
Sorties : docs/data/<pays>/planning.json (lu par compute_metrics.py pour les personnes exposées attendues),
validation/planification_12mois.md, validation/planification_12mois_regions.csv.
Usage : python scripts/build_planning.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import math

import numpy as np
import pandas as pd

import build_teleconnections as TC
from common import DATA_DIR, country_docs_dir, grid_dir, load_grid, read_units, write_json

LABELS = TC.TARGET_LABELS
P_MIN, P_MAX = 0.15, 0.50
Z3 = 0.4307


def lagged_predictors(oni, dmi, season_end_years):
    """Saison terminée en avril Y : ONI et DMI de juillet-septembre Y-2 (connus fin octobre Y-2, 12 mois avant)."""
    return TC.predictors(oni, dmi, [y - 1 for y in season_end_years]).set_axis(list(season_end_years))


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def bound(p):
    """Borne chaque probabilité à [P_MIN, P_MAX] en gardant la somme à 1 (bissection sur un mélange avec 1/3)."""
    p = np.asarray(p, float)
    lo, hi = 0.0, 1.0
    for _ in range(50):
        a = (lo + hi) / 2
        q = (1 - a) * p + a / 3
        if q.min() >= P_MIN - 1e-9 and q.max() <= P_MAX + 1e-9:
            hi = a
        else:
            lo = a
    return (1 - hi) * p + hi / 3


def tercile_probs(z_pred, sd):
    """Probabilités (sec, normal, humide) pour une anomalie standardisée prévue z_pred, écart-type sd des résidus."""
    p_dry = phi((-Z3 - z_pred) / sd)
    p_wet = 1 - phi((Z3 - z_pred) / sd)
    return bound([p_dry, 1 - p_dry - p_wet, p_wet])


def rps(p, k):
    """Score de probabilité ordonné (3 classes) ; k = classe observée 0, 1 ou 2."""
    c, o = np.cumsum(p), np.cumsum(np.eye(3)[k])
    return float(np.sum((c - o) ** 2))


def rpss_loo(X, y):
    """RPSS en validation croisée : probabilités de terciles du modèle contre 1/3 chacune ; classes observées selon les
    terciles des AUTRES saisons."""
    n = len(y)
    s_m, s_c = 0.0, 0.0
    pred = TC.loo(X, y)
    for i in range(n):
        tr = np.arange(n) != i
        res = y[tr] - TC.loo(X[tr], y[tr])
        mu, sd = y[tr].mean(), y[tr].std(ddof=1)
        t1, t2 = np.quantile(y[tr], [1 / 3, 2 / 3])
        k = 0 if y[i] <= t1 else (2 if y[i] > t2 else 1)
        p = tercile_probs((pred[i] - mu) / sd, max(res.std(ddof=1) / sd, 0.2))
        s_m += rps(p, k)
        s_c += rps(np.full(3, 1 / 3), k)
    return float(1 - s_m / s_c)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    ms = load_grid(grid_dir(args.country) / "monthly_series.npz")
    months = [int(m) for m in ms["months"]]
    years = np.array([int(y) for y in ms["years"]])
    oni = pd.read_csv(DATA_DIR / "enso" / "oni.csv")
    dmi = TC.read_dmi()
    X_all = lagged_predictors(oni, dmi, years)
    units = read_units(args.country)
    names = dict(zip(units.pcode, units.name))
    reg = TC.region_series(ms, units)
    target_year = int(years[-1]) + 2                       # saison terminée en avril Y+2 (Y = année de la dernière saison + 1)
    issue_year = target_year - 2
    Xn = lagged_predictors(oni, dmi, [target_year]).iloc[0]
    rows = []
    for pc, s in sorted(reg.items()):
        for tk, tm in TC.TARGETS.items():
            idx = [months.index(m) for m in tm if m in months]
            tot = s[:, idx].sum(axis=1)
            y = (tot - tot.mean()) / tot.std(ddof=1)
            for model, cols in (("oni", ["oni"]), ("oni_dmi", ["oni", "dmi"])):
                X = X_all[cols].to_numpy()
                ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
                ev = TC.evaluate(X[ok], y[ok], years[ok])
                ev["p_perm"] = TC.perm_pvalue_loo(X[ok], y[ok])
                ev["rpss_loo"] = rpss_loo(X[ok], y[ok])
                _, coef = TC.fit_predict(X[ok], y[ok], X[ok][:1])
                res = y[ok] - TC.loo(X[ok], y[ok])
                xn = np.array([Xn[c] for c in cols])
                z = float(coef[0] + coef[1:] @ xn) if np.isfinite(xn).all() else np.nan
                rows.append({"adm1": pc, "region": names.get(pc, pc), "cible": tk, "modele": model, **ev, "z_prevu": z,
                             "sd_residu": float(res.std(ddof=1)), "mm_moyen": float(tot.mean()), "mm_ecart_type": float(tot.std(ddof=1))})
    df = pd.DataFrame(rows)
    df["signif_fdr10"] = False
    for _, g in df.groupby(["cible", "modele"]):
        df.loc[g.index, "signif_fdr10"] = TC.bh(g.p_perm.to_numpy())
    df["valide"] = (df.msss_loo > 0) & (df.msss_chrono.fillna(-1) > 0) & df.signif_fdr10 & (df.rpss_loo > 0) & df.z_prevu.notna()
    out = {}
    for (pc, tk), g in df.groupby(["adm1", "cible"]):
        v = g[g.valide]
        if len(v):                                          # ONI seul s'il passe (plus simple), sinon ONI + DMI
            r = v.sort_values("modele").iloc[0]
            p = tercile_probs(r.z_prevu, max(r.sd_residu, 0.2))
            out.setdefault(pc, {})[tk] = {"valide": True, "modele": r.modele, "p": [round(float(x), 3) for x in p],
                                          "pct_normale": round(100 + 100 * r.z_prevu * r.mm_ecart_type / r.mm_moyen),
                                          "rpss": round(float(r.rpss_loo), 3), "msss": round(float(r.msss_loo), 3)}
        else:
            out.setdefault(pc, {})[tk] = {"valide": False, "p": [1 / 3, 1 / 3, 1 / 3]}
    trans = enso_transition(oni, issue_year)
    write_json(country_docs_dir(args.country) / "planning.json", {
        "generated": dt.date.today().isoformat(), "issued_for": f"{target_year - 1}-{target_year}", "issue_year": issue_year,
        "predictors": {"oni_jas": None if not np.isfinite(Xn.oni) else round(float(Xn.oni), 2),
                       "dmi_jas": None if not np.isfinite(Xn.dmi) else round(float(Xn.dmi), 2)},
        "n_seasons": int(len(years)), "regions": out, "enso_transition": trans,
        "replaced_on": f"{target_year - 1}-10-16"})
    vd = DATA_DIR.parent / "validation"
    df.round(4).to_csv(vd / "planification_12mois_regions.csv", index=False)
    write_md(vd / "planification_12mois.md", df, out, trans, target_year, Xn, names, years)
    print(f"Planification {target_year - 1}-{target_year} : {int(df.valide.sum())} combinaisons région x période x modèle validées")


def enso_transition(oni, year):
    """Phase ENSO de l'année suivante après chaque année de même type que `year` (ONI de juillet-septembre)."""
    jas = oni[oni.center_month == 8].set_index("year").oni
    v = jas.get(year, np.nan)
    if not np.isfinite(v):
        return None
    ph = lambda x: "la_nina" if x <= -0.5 else ("el_nino" if x >= 0.5 else "neutre")
    same = [y for y in jas.index if y != year and y + 1 in jas.index and ph(jas[y]) == ph(v) and abs(jas[y]) >= min(abs(v), 1.0)]
    nxt = [ph(jas[y + 1]) for y in same]
    return {"oni_jas": round(float(v), 2), "phase": ph(v), "cases": [int(y) for y in same],
            "next": {k: nxt.count(k) for k in ("la_nina", "neutre", "el_nino")}}


def write_md(path, df, out, trans, target_year, Xn, names, years):
    f = lambda v, d=2: "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{d}f}".replace(".", ",")
    L = [f"# Scénarios de planification à 12 mois : saison {target_year - 1}-{target_year}", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/build_planning.py`, selon `validation/protocole_planification_12mois.md` "
         "(fixé avant les calculs).", "",
         f"- {len(years)} saisons de pluie CHIRPS par région. Prédicteurs connus un an avant : ONI et DMI de juillet-septembre "
         f"{target_year - 2} (ONI {f(Xn.oni)}, DMI {f(Xn.dmi)}).",
         "- Un signal n'est utilisé que s'il passe les quatre épreuves (MSSS croisé > 0, MSSS chronologique > 0, corrélation "
         "significative après contrôle des tests multiples, RPSS croisé > 0). Sinon : scénarios climatologiques.", "",
         "## 1. Résultat", "", "| Période | Modèle | Régions validées | MSSS médian | RPSS médian |", "|---|---|---|---|---|"]
    for (tk, m), g in df.groupby(["cible", "modele"], sort=False):
        L.append(f"| {LABELS[tk]} | {'ONI' if m == 'oni' else 'ONI + DMI'} | {int(g.valide.sum())} / {len(g)} | {f(g.msss_loo.median())} | {f(g.rpss_loo.median())} |")
    ok = [(pc, tk, v) for pc, d in out.items() for tk, v in d.items() if v["valide"]]
    L += ["", f"**H1** (au moins un signal validé à 12 mois) : **{'soutenue' if ok else 'non soutenue'}**.", ""]
    if ok:
        L += ["| Région | Période | Probabilités sec / normal / humide | Pluie attendue | RPSS |", "|---|---|---|---|---|"]
        for pc, tk, v in sorted(ok, key=lambda x: (names.get(x[0], ""), x[1])):
            L.append(f"| {names.get(pc, pc)} | {LABELS[tk]} | {' / '.join(str(round(100 * x)) + ' %' for x in v['p'])} | {v['pct_normale']} % | {f(v['rpss'])} |")
    else:
        L.append("À 12 mois, aucune région ne passe les épreuves : seule une planification climatologique (toutes les saisons passées à poids égal) est défendable.")
    if trans:
        n = trans["next"]
        L += ["", "## 2. Contexte : phase El Niño / La Niña de l'année suivante", "",
              f"Après les {len(trans['cases'])} années de même type que {target_year - 2} (ONI de juillet-septembre {f(trans['oni_jas'])}) : "
              f"{n['la_nina']} fois La Niña, {n['neutre']} fois neutre, {n['el_nino']} fois El Niño ({', '.join(map(str, trans['cases']))}).",
              "C'est un contexte physique, pas une prévision régionale : son effet sur la pluie de chaque région n'est retenu que s'il passe les épreuves ci-dessus."]
    L += ["", "## Limites", "", "- Population actuelle, non projetée.", "- Exposition déduite de la pluie seule : les cyclones ne sont pas prévisibles à 12 mois.",
          "- Remplacé automatiquement par la prévision hybride C3S le 16 octobre de l'année de la saison."]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
