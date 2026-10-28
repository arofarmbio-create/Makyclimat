"""Modèle de prévision saisonnière par région à partir d'El Niño (ONI) et du dipôle de l'océan Indien (DMI).

Cahier des charges §8 (approche 1 : modèle statistique), §5 (« ne déduis jamais un risque local d'une anomalie océanique
globale sans démontrer le lien »), §9 (horizon saisonnier 1-6 mois), §13 (validation sans fuite de données).

Prédicteurs connus AVANT la saison (date d'émission fin octobre) : ONI de juillet-septembre (NOAA CPC) et DMI moyen de
juillet-septembre (NOAA PSL, HadISST). Cible : pluie CHIRPS par région, en anomalie standardisée, pour novembre-janvier,
janvier-mars et la saison novembre-avril. Modèle : régression linéaire (moindres carrés), une par région et par cible.
Validation :
  - validation croisée « une saison laissée de côté » (LOO) : corrélation et score de compétence MSSS par rapport à la
    climatologie (MSSS > 0 = meilleur que la moyenne historique) ;
  - test chronologique : ajusté sur les saisons jusqu'en 2005, évalué sur 2006 et après ;
  - significativité unilatérale de la corrélation entre prévision croisée et observation, par permutation (500 tirages,
    modèle réajusté à chaque tirage), et contrôle des tests multiples (Benjamini-Hochberg).
Une région n'est déclarée « prévisible » que si MSSS LOO > 0, MSSS chronologique > 0 et corrélation significative (FDR 10 %).
Sinon la prévision affichée est la climatologie : le lien n'est pas démontré.
Sorties : validation/teleconnexions_regions.csv, validation/teleconnexions.md, docs/data/<pays>/teleconnections.json
Usage : python scripts/build_teleconnections.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd

from common import DATA_DIR, country_docs_dir, grid_dir, load_grid, read_units, sample_grid, write_json

DMI_URL = "https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data"
TARGETS = {"ndj": (11, 12, 1), "jfm": (1, 2, 3), "nov_avr": (11, 12, 1, 2, 3, 4)}
TARGET_LABELS = {"ndj": "novembre-janvier", "jfm": "janvier-mars", "nov_avr": "novembre-avril"}
SPLIT_YEAR = 2005                     # test chronologique : ajustement <= 2005, évaluation > 2005
RNG = np.random.default_rng(0)


def parse_psl(text: str) -> pd.DataFrame:
    """Format PSL : 1re ligne « an_début an_fin », puis « année v1 ... v12 », valeurs manquantes -9999 ou -99.99."""
    rows = []
    lines = text.strip().splitlines()
    for ln in lines[1:]:
        p = ln.split()
        if len(p) != 13 or not p[0].isdigit():
            continue
        for m, v in enumerate(p[1:], 1):
            v = float(v)
            if v > -99:
                rows.append((int(p[0]), m, v))
    return pd.DataFrame(rows, columns=["year", "month", "value"])


def read_dmi() -> pd.DataFrame:
    import requests
    return parse_psl(requests.get(DMI_URL, timeout=120).text)


def predictors(oni: pd.DataFrame, dmi: pd.DataFrame, season_end_years):
    """Pour la saison qui se termine en avril de l'année Y : ONI JAS et DMI moyen juillet-septembre de l'année Y-1."""
    o = oni[oni.center_month == 8].set_index("year").oni
    d = dmi[dmi.month.isin([7, 8, 9])].groupby("year").value.agg(["mean", "count"])
    d = d[d["count"] == 3]["mean"]
    X = pd.DataFrame({"oni": [o.get(y - 1, np.nan) for y in season_end_years],
                      "dmi": [d.get(y - 1, np.nan) for y in season_end_years]}, index=list(season_end_years))
    return X


def fit_predict(Xtr, ytr, Xte):
    A = np.column_stack([np.ones(len(Xtr)), Xtr])
    coef, *_ = np.linalg.lstsq(A, ytr, rcond=None)
    return np.column_stack([np.ones(len(Xte)), Xte]) @ coef, coef


def loo(X, y):
    pred = np.full(len(y), np.nan)
    for i in range(len(y)):
        tr = np.arange(len(y)) != i
        # standardisation de la cible recalculée sans la saison testée (pas de fuite)
        mu, sd = y[tr].mean(), y[tr].std(ddof=1)
        p, _ = fit_predict(X[tr], (y[tr] - mu) / sd, X[i:i + 1])
        pred[i] = p[0] * sd + mu
    return pred


def msss(y, pred, ref):
    """Score de compétence : 1 - EQM(prévision) / EQM(référence climatologique)."""
    return float(1 - np.mean((y - pred) ** 2) / np.mean((y - ref) ** 2))


def loo_climatology(y):
    return np.array([np.delete(y, i).mean() for i in range(len(y))])


def perm_pvalue(a, b, n=2000):
    """Corrélation simple (bilatérale) entre un prédicteur et la cible, par permutation."""
    r = abs(np.corrcoef(a, b)[0, 1])
    c = np.array([abs(np.corrcoef(RNG.permutation(a), b)[0, 1]) for _ in range(n)])
    return float((1 + np.sum(c >= r)) / (n + 1))


def perm_pvalue_loo(X, y, n=500):
    """Compétence de la prévision croisée, unilatérale : seule une corrélation POSITIVE entre prévision LOO et observation
    compte. À chaque permutation de la cible, le modèle est réajusté en entier (LOO), pour que le test reproduise toute la
    procédure. Une corrélation LOO négative (fréquente sans aucun signal) n'est jamais une compétence."""
    r0 = np.corrcoef(loo(X, y), y)[0, 1]
    c = np.empty(n)
    for i in range(n):
        yp = RNG.permutation(y)
        c[i] = np.corrcoef(loo(X, yp), yp)[0, 1]
    return float((1 + np.sum(c >= r0)) / (n + 1))


def bh(p, q=0.10):
    """Benjamini-Hochberg : True pour les tests retenus au taux de fausses découvertes q."""
    p = np.asarray(p)
    order = np.argsort(p)
    k = np.where(p[order] <= q * np.arange(1, len(p) + 1) / len(p))[0]
    keep = np.zeros(len(p), bool)
    if len(k):
        keep[order[:k.max() + 1]] = True
    return keep


def evaluate(X: np.ndarray, y: np.ndarray, years: np.ndarray):
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
    X, y, years = X[ok], y[ok], years[ok]
    pred = loo(X, y)
    out = {"n": int(len(y)), "r_loo": float(np.corrcoef(pred, y)[0, 1]), "msss_loo": msss(y, pred, loo_climatology(y))}
    tr, te = years <= SPLIT_YEAR, years > SPLIT_YEAR
    if tr.sum() >= 15 and te.sum() >= 8:
        p, _ = fit_predict(X[tr], y[tr], X[te])
        out["msss_chrono"] = msss(y[te], p, np.full(te.sum(), y[tr].mean()))
    else:
        out["msss_chrono"] = np.nan
    # tercile sec : prévision « sous la normale » quand la valeur prévue (LOO) est dans le tiers inférieur des prévisions
    lo_obs = y <= np.quantile(y, 1 / 3)
    lo_pred = pred <= np.quantile(pred, 1 / 3)
    out["pod_sec"] = float((lo_obs & lo_pred).sum() / max(lo_obs.sum(), 1))
    out["far_sec"] = float((lo_pred & ~lo_obs).sum() / max(lo_pred.sum(), 1))
    return out


def region_series(ms: dict, units: pd.DataFrame):
    """Pluie par région, saison et mois : moyenne pondérée par la surface des fokontany -> {adm1: (Y, M)}."""
    leaves = units[units.level == 4].reset_index(drop=True)
    lon, lat = leaves.lon.to_numpy(), leaves.lat.to_numpy()
    arr = ms["arr"].astype("float32")
    Y, M = arr.shape[:2]
    vals = np.stack([np.stack([sample_grid(arr[y, m], float(ms["lon0"]), float(ms["lat0"]), float(ms["res"]), lon, lat)
                               for m in range(M)]) for y in range(Y)])            # (Y, M, N)
    w = leaves.area_km2.fillna(1.0).to_numpy()
    out = {}
    for pc, ix in leaves.groupby("adm1").indices.items():
        v = vals[:, :, ix]
        ok = np.isfinite(v)
        out[pc] = np.where(ok, v, 0).dot(w[ix]) / np.maximum(ok.astype(float).dot(w[ix]), 1e-9)
    return out


def main(country="mdg", dmi=None, oni=None):
    ms = load_grid(grid_dir(country) / "monthly_series.npz")
    months = [int(m) for m in ms["months"]]
    years = np.array([int(y) for y in ms["years"]])
    oni = oni if oni is not None else pd.read_csv(DATA_DIR / "enso" / "oni.csv")
    dmi = dmi if dmi is not None else read_dmi()
    Xdf = predictors(oni, dmi, years)
    units = read_units(country)
    names = dict(zip(units.pcode, units.name))
    reg = region_series(ms, units)
    rows = []
    for pc, s in sorted(reg.items()):
        for tk, tm in TARGETS.items():
            idx = [months.index(m) for m in tm if m in months]
            tot = s[:, idx].sum(axis=1)
            y = (tot - tot.mean()) / tot.std(ddof=1)
            for model, cols in (("oni", ["oni"]), ("oni_dmi", ["oni", "dmi"])):
                X = Xdf[cols].to_numpy()
                ev = evaluate(X, y, years)
                ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
                ev["p_perm"] = perm_pvalue_loo(X[ok], y[ok])
                # coefficients sur toutes les saisons, pour la prévision de la saison à venir
                _, coef = fit_predict(X[ok], y[ok], X[ok][:1])
                rows.append({"adm1": pc, "region": names.get(pc, pc), "cible": tk, "modele": model, **ev,
                             "coef_oni": float(coef[1]), "coef_dmi": float(coef[2]) if model == "oni_dmi" else np.nan,
                             "mm_moyen": float(tot.mean()), "mm_ecart_type": float(tot.std(ddof=1))})
    df = pd.DataFrame(rows)
    df["signif_fdr10"] = False
    for (tk, model), g in df.groupby(["cible", "modele"]):
        df.loc[g.index, "signif_fdr10"] = bh(g.p_perm.to_numpy())
    df["previsible"] = (df.msss_loo > 0) & (df.msss_chrono.fillna(-1) > 0) & df.signif_fdr10
    # prévision 2026-27 (ou saison à venir) : modèle ONI seul si le DMI de juillet-septembre manque
    season_next = int(years[-1]) + 1
    Xn = predictors(oni, dmi, [season_next]).iloc[0]
    fc = []
    for _, r in df.iterrows():
        if r.modele == "oni_dmi" and not np.isfinite(Xn.dmi):
            continue
        z = r.coef_oni * Xn.oni + (r.coef_dmi * Xn.dmi if r.modele == "oni_dmi" else 0.0)
        fc.append({"adm1": r.adm1, "region": r.region, "cible": r.cible, "modele": r.modele, "previsible": bool(r.previsible),
                   "anomalie_std": round(float(z), 2) if r.previsible else None,
                   "pct_normale": round(100 + 100 * z * r.mm_ecart_type / r.mm_moyen) if r.previsible else None})
    vd = DATA_DIR.parent / "validation"
    if country != "demo":
        df.round(3).to_csv(vd / "teleconnexions_regions.csv", index=False)
        write_md(vd / "teleconnexions.md", df, fc, Xn, season_next, years)
    write_json(country_docs_dir(country) / "teleconnections.json",
               {"generated": dt.date.today().isoformat(), "season": f"{season_next - 1}-{season_next}",
                "predictors": {"oni_jas": None if not np.isfinite(Xn.oni) else round(float(Xn.oni), 2),
                               "dmi_jas": None if not np.isfinite(Xn.dmi) else round(float(Xn.dmi), 2)},
                "n_seasons": int(len(years)), "forecast": fc})
    n_prev = df[df.previsible].groupby(["cible", "modele"]).size().to_dict()
    print(f"Téléconnexions : {df.adm1.nunique()} régions, {len(years)} saisons ; régions prévisibles : {n_prev}")
    return df, fc


def write_md(path, df, fc, Xn, season_next, years):
    def f(v, d=2):
        return "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{d}f}".replace(".", ",")
    L = [f"# Modèle de prévision saisonnière El Niño / dipôle de l'océan Indien, par région",
         "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/build_teleconnections.py`. Cahier des charges §5, §8 (approche 1), §9, §13.",
         f"Saisons {int(years[0]) - 1}-{int(years[0])} à {int(years[-1]) - 1}-{int(years[-1])} ({len(years)} saisons). Pluie CHIRPS par région.",
         "Prédicteurs connus avant la saison : ONI de juillet-septembre (NOAA CPC) et DMI de juillet-septembre (NOAA PSL, HadISST).",
         "",
         "Une région est dite **prévisible** seulement si les trois conditions suivantes sont réunies :",
         "- score de compétence en validation croisée (MSSS, saison laissée de côté) > 0 ;",
         f"- score de compétence au test chronologique (ajusté jusqu'en {SPLIT_YEAR}, testé après) > 0 ;",
         "- corrélation POSITIVE et significative entre prévision croisée et observation (permutation unilatérale, modèle réajusté à chaque tirage), après contrôle des tests multiples (Benjamini-Hochberg, 10 %).",
         "",
         "Sinon, la meilleure prévision est la climatologie.",
         "",
         "## Combien de régions sont prévisibles ?",
         "",
         "| Cible | Modèle | Régions prévisibles | MSSS médian (LOO) |",
         "|---|---|---|---|"]
    for (tk, model), g in df.groupby(["cible", "modele"], sort=False):
        L.append(f"| {TARGET_LABELS[tk]} | {'ONI seul' if model == 'oni' else 'ONI + DMI'} | {int(g.previsible.sum())} / {len(g)} | {f(g.msss_loo.median())} |")
    L += ["", "## Détail par région (novembre-avril)", "",
          "| Région | Modèle | r (LOO) | MSSS LOO | MSSS chrono | p permutation | Coef. ONI | Coef. DMI | Prévisible |",
          "|---|---|---|---|---|---|---|---|---|"]
    for _, r in df[df.cible == "nov_avr"].sort_values(["region", "modele"]).iterrows():
        L.append(f"| {r.region} | {'ONI' if r.modele == 'oni' else 'ONI+DMI'} | {f(r.r_loo)} | {f(r.msss_loo)} | {f(r.msss_chrono)} | "
                 f"{f(r.p_perm, 3)} | {f(r.coef_oni)} | {f(r.coef_dmi)} | {'**oui**' if r.previsible else 'non'} |")
    L += ["", f"## Prévision {season_next - 1}-{season_next}", "",
          f"ONI de juillet-septembre {season_next - 1} : **{f(Xn.oni)}**. DMI de juillet-septembre {season_next - 1} : "
          + (f"**{f(Xn.dmi)}**." if np.isfinite(Xn.dmi) else "**indisponible** (la série HadISST de NOAA PSL a plusieurs mois de retard) : seul le modèle ONI est appliqué."),
          ""]
    prev = [x for x in fc if x["previsible"]]
    if prev:
        L += ["| Région | Période | Modèle | Anomalie (écart-type) | % de la normale |", "|---|---|---|---|---|"]
        for x in sorted(prev, key=lambda x: (x["region"], x["cible"])):
            L.append(f"| {x['region']} | {TARGET_LABELS[x['cible']]} | {'ONI' if x['modele'] == 'oni' else 'ONI+DMI'} | {f(x['anomalie_std'])} | {x['pct_normale']} % |")
    else:
        L.append("Aucune région ne passe les trois critères : **pas de prévision autre que la climatologie**.")
    L += ["", "## Limites", "",
          "- Le modèle est linéaire : un El Niño très fort (ONI > 2, très rare dans l'échantillon) est extrapolé, et son effet réel peut différer.",
          "- La pluie est estimée par CHIRPS, sans stations au sol. La moyenne régionale lisse les contrastes internes (relief, façade est et ouest).",
          "- Aucune autre source de prévisibilité n'est prise en compte : autres modes de l'océan Indien (SIOD), cyclones, MJO.",
          "- Les seuils de décision (MSSS > 0, FDR 10 %) sont des conventions, à discuter avec Météo Madagascar.",
          "- Cette prévision complète celle des modèles dynamiques (ECMWF SEAS5, Météo Madagascar, SARCOF). Elle ne la remplace pas."]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    main(ap.parse_args().country)
