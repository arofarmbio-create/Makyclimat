"""Transfert de connaissances depuis des régions analogues (validation/protocole_transfert_analogues.md, fixé avant le
calcul) : la recharge mesurée dans le monde, sur des roches et climats semblables, prédit-elle la recharge mesurée à
Madagascar ?

Source : compilation de Wan, Döll et Müller Schmied 2024 (821 estimations, CC BY 4.0). Type d'aquifère attribué à tous
les sites par la GLiM à 0,5° (Hartmann et Moosdorf 2012, CC BY 3.0). Analogues : distance de Gower sur pluie, ETP,
aridité, type d'aquifère ; k = 5 ; prédiction = médiane des log-recharges.
Tests : niveau 1 (pays laissé de côté contre référence naïve), H-R1 (biais du modèle africain selon le type
d'aquifère, Fisher), H-T1 et H-T2 (12 sites malgaches mesurés par fluctuation de nappe).
Sorties : validation/transfert_analogues.md et transfert_analogues_madagascar.csv.
Usage : python scripts/transfert_analogues.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd
from scipy import stats

from common import ROOT, country_data_dir

K = 5
NUM = ["P", "PET", "Aridity"]
GLIM_AQUIFER = {"mt": "Basement", "pa": "Basement", "pb": "Basement", "pi": "Basement",
                "ss": "Sedimentary", "sc": "Sedimentary", "sm": "Sedimentary", "su": "Unconsolidated",
                "va": "Volcanic", "vb": "Volcanic", "vi": "Volcanic", "py": "Volcanic"}
GLIM_CODES = {1: "su", 2: "vb", 3: "ss", 4: "pb", 5: "sm", 6: "sc", 7: "va", 8: "mt", 9: "pa", 10: "vi", 11: "wb",
              12: "py", 13: "pi", 14: "ev", 15: "nd", 16: "ig"}
AFRICA_BOX = (-20.0, -36.0, 52.0, 38.0)          # lon min, lat min, lon max, lat max (Madagascar exclue : aucun site)


# ---------------- GLiM ----------------
def read_ascii_grid(path):
    head = {}
    with open(path) as f:
        for _ in range(6):
            k, v = f.readline().split()
            head[k.lower()] = float(v)
    a = np.loadtxt(path, skiprows=6)
    return a, head


def glim_class(lat, lon, grid, head) -> list[str]:
    """Classe dominante GLiM (lettres) ; maille vide -> maille renseignée la plus proche."""
    a = grid
    res, x0 = head["cellsize"], head["xllcorner"]
    y_top = head["yllcorner"] + res * a.shape[0]
    valid = np.argwhere(a != head.get("nodata_value", -9999))
    out = []
    for la, lo in zip(np.asarray(lat, float), np.asarray(lon, float)):
        r, c = int((y_top - la) // res), int((lo - x0) // res)
        r, c = min(max(r, 0), a.shape[0] - 1), min(max(c, 0), a.shape[1] - 1)
        v = a[r, c]
        if v == head.get("nodata_value", -9999):
            j = np.argmin((valid[:, 0] - r) ** 2 + (valid[:, 1] - c) ** 2)
            v = a[tuple(valid[j])]
        out.append(GLIM_CODES.get(int(v), "nd"))
    return out


def aquifer(classes) -> np.ndarray:
    return np.array([GLIM_AQUIFER.get(c, "Unknown") for c in classes], dtype=object)


# ---------------- analogues ----------------
def gower(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Distance de Gower (tests × sources) sur NUM (écart rapporté à l'étendue des sources) et le type d'aquifère."""
    parts = []
    for c in NUM:
        rng = float(np.nanmax(train[c]) - np.nanmin(train[c])) or 1.0
        parts.append(np.abs(test[c].to_numpy(float)[:, None] - train[c].to_numpy(float)[None, :]) / rng)
    parts.append((test.aquifer.to_numpy()[:, None] != train.aquifer.to_numpy()[None, :]).astype(float))
    return np.nanmean(np.stack(parts), axis=0)


def knn_log(train: pd.DataFrame, test: pd.DataFrame, k=K) -> np.ndarray:
    d = gower(train, test)
    idx = np.argsort(d, axis=1)[:, :k]
    y = np.log10(np.maximum(train.R.to_numpy(float), 0.1))
    return np.median(y[idx], axis=1)


def loco(df: pd.DataFrame, min_sites=3) -> pd.DataFrame:
    """Niveau 1 : chaque pays laissé de côté ; erreur absolue log du modèle et de la référence naïve (médiane du type)."""
    rows = []
    for ctry, g in df.groupby("country"):
        if len(g) < min_sites:
            continue
        tr = df[df.country != ctry]
        pred = knn_log(tr, g)
        ytr = np.log10(np.maximum(tr.R, 0.1))
        naive = np.array([ytr[tr.aquifer == a].median() if (tr.aquifer == a).any() else ytr.median() for a in g.aquifer])
        y = np.log10(np.maximum(g.R, 0.1)).to_numpy()
        rows.append({"pays": ctry, "sites": len(g), "erreur_modele": float(np.median(np.abs(pred - y))),
                     "erreur_naive": float(np.median(np.abs(naive - y)))})
    return pd.DataFrame(rows)


def sign_test(wins: int, n: int) -> float:
    return float(stats.binomtest(wins, n, 0.5, alternative="greater").pvalue) if n else float("nan")


def hr1(df: pd.DataFrame) -> dict:
    """Modèle africain appliqué hors d'Afrique : surestimation selon le type d'aquifère (Fisher unilatéral)."""
    lo0, la0, lo1, la1 = AFRICA_BOX
    afr = df.lon.between(lo0, lo1) & df.lat.between(la0, la1)
    tr, te = df[afr], df[~afr & df.aquifer.isin(["Basement", "Sedimentary", "Unconsolidated"])]
    if len(tr) < K or len(te) == 0:
        return {"n": 0}
    over = knn_log(tr, te) > np.log10(np.maximum(te.R, 0.1)).to_numpy()
    base = (te.aquifer == "Basement").to_numpy()
    table = [[int((over & base).sum()), int((~over & base).sum())], [int((over & ~base).sum()), int((~over & ~base).sum())]]
    p = float(stats.fisher_exact(table, alternative="greater")[1])
    return {"n": len(te), "table": table, "p": p, "soutenue": bool(p < 0.05),
            "part_socle": table[0][0] / max(sum(table[0]), 1), "part_sedi": table[1][0] / max(sum(table[1]), 1)}


def load_sources(path_xlsx, grid, head, vect: dict | None = None) -> pd.DataFrame:
    """vect : classes GLiM vectorielles par identifiant « wan_<ligne> » (reprise du 04/11) ; sinon grille à 0,5°."""
    w = pd.read_excel(path_xlsx)
    df = pd.DataFrame({"wid": [f"wan_{i}" for i in range(len(w))], "lat": w.lat, "lon": w.lon, "R": pd.to_numeric(w.Recharge_mmpa, errors="coerce"),
                       "P": pd.to_numeric(w.Prep_mmpa, errors="coerce"), "PET": pd.to_numeric(w.PET_mm, errors="coerce"),
                       "Aridity": pd.to_numeric(w.Aridity, errors="coerce"),
                       "country": w.Country_Name.fillna(w.Country).astype(str), "bgs": w.Aquifer_group})
    df = df.dropna(subset=["lat", "lon", "R", "P", "PET", "Aridity"]).reset_index(drop=True)
    df["glim"] = [vect.get(i.lower(), "") for i in df.wid] if vect is not None else glim_class(df.lat, df.lon, grid, head)
    df["aquifer"] = aquifer(df.glim)
    return df[df.aquifer != "Unknown"].reset_index(drop=True)


def report(n_src, accord, lo, t_lo, h, mdg, t1, t2) -> str:
    L = ["# Transfert de connaissances depuis des régions analogues : recharge", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/transfert_analogues.py`, selon "
         "`validation/protocole_transfert_analogues.md` (fixé avant le calcul). Sources : Wan, Döll et Müller Schmied 2024 "
         "(CC BY 4.0) ; GLiM 0,5° (Hartmann et Moosdorf 2012, CC BY 3.0) ; Madagascar : MGMERL (HT) et Carrière et al. 2021 (GROSoM).", "",
         f"{n_src} sites sources avec type d'aquifère. Accord de la règle GLiM avec le type du BGS sur les sites africains : {accord}.", "",
         "## Niveau 1 : dans les sources (pays laissé de côté)", "",
         f"Le modèle par analogues bat la référence naïve dans {t_lo[0]} pays sur {t_lo[1]} (test du signe, p = {t_lo[2]:.3f}). "
         f"Erreur médiane : modèle {lo.erreur_modele.median():.2f}, naïve {lo.erreur_naive.median():.2f} (log10 de la recharge).", "",
         "## H-R1 : le modèle africain hors d'Afrique, selon le type d'aquifère", ""]
    if h.get("n"):
        L.append(f"{h['n']} sites hors d'Afrique. Surestimation : socle {h['part_socle']:.0%}, sédimentaire et non consolidé "
                 f"{h['part_sedi']:.0%} ; Fisher unilatéral p = {h['p']:.3f}. **H-R1 {'soutenue' if h['soutenue'] else 'non soutenue'}**.")
    else:
        L.append("Test impossible (sites insuffisants).")
    L += ["", "## H-T1 et H-T2 : les sites malgaches mesurés (fluctuation de nappe)", "",
          "| Site | Type d'aquifère (GLiM) | Mesurée (mm/an) | Transfert mondial (mm/an) | T2 africain (mm/an) | Plus proche : |",
          "|---|---|---|---|---|---|"]
    for r in mdg.itertuples():
        L.append(f"| {r.site} | {r.aquifer} | {r.r_mm:.0f} | {r.mondial_mm:.0f} | {r.t2_mm:.0f} | {'mondial' if r.mondial_gagne else 'T2'} |")
    L += ["", f"**H-T1** : transfert mondial plus proche sur {t1[0]} sites sur {t1[1]} (règle : au moins 10 sur 12 ; test du signe "
          f"p = {t1[2]:.3f}). **{'Soutenue' if t1[0] >= 10 and t1[2] < 0.05 else 'Non soutenue'}**.",
          f"**H-T2** : Spearman entre transfert mondial et mesure ρ = {t2['rho']:+.2f} (p = {t2['p']:.3f}) ; ordre socle / sédimentaire "
          f"{'respecté' if t2['ordre'] else 'non respecté'}. **{'Soutenue' if t2['soutenue'] else 'Non soutenue'}**.", ""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--typage", choices=["grille", "vectoriel"], default="grille")
    args = ap.parse_args()
    adir = country_data_dir(args.country) / "analogues"
    vect = None
    if args.typage == "vectoriel":
        g = pd.read_csv(ROOT / "inputs" / "analogues" / "glim_points_classes.csv", keep_default_na=False)
        vect = {i.lower(): x for i, x in zip(g.id, g.xx)}       # appariement insensible à la casse (AnKaranabO)
    grid, head = read_ascii_grid(adir / "glim" / "ex" / "glim_wgs84_0point5deg.txt.asc")
    src = load_sources(adir / "recharge_mondiale" / "figshare_23592666" / "1_Ground-based-estimates.xlsx", grid, head, vect)
    b = src.dropna(subset=["bgs"])
    accord = f"{float((b.bgs == b.aquifer).mean()):.0%} sur {len(b)} sites" if len(b) else "non mesurable"
    lo = loco(src)
    wins = int((lo.erreur_modele < lo.erreur_naive).sum())
    t_lo = (wins, len(lo), sign_test(wins, len(lo)))
    h = hr1(src)
    sites = pd.read_csv(ROOT / "validation" / "recharge_fluctuation_sites.csv")
    sites = sites[sites.retenu.astype(str) == "True"].reset_index(drop=True)
    coords = pd.read_csv(ROOT / "inputs" / "mgmerl" / "mgmerl_dataloggers_ht_analytics_sites.csv")
    gro = pd.read_csv(country_data_dir(args.country) / "nappes_mondiales" / "grosom" / "puits_grosom.csv")
    ll = {**{r.site: (r.lat, r.lon) for r in coords.itertuples()}, **{r.nom: (r.lat, r.lon) for r in gro.itertuples()}}
    ll = {k.lower(): v for k, v in ll.items()}
    sites["lat"] = [ll.get(s.lower(), (np.nan, np.nan))[0] for s in sites.site]
    sites["lon"] = [ll.get(s.lower(), (np.nan, np.nan))[1] for s in sites.site]
    cov = pd.read_csv(country_data_dir(args.country) / "nappes_mondiales" / "covariables_hc6.csv")
    j = [int(np.argmin((cov.lat - la) ** 2 + (cov.lon - lo_) ** 2)) for la, lo_ in zip(sites.lat, sites.lon)]
    sites["P"], sites["PET"], sites["Aridity"] = cov.LTA_P_mmpa.to_numpy()[j], cov.LTA_PET_mm.to_numpy()[j], cov.Aridity.to_numpy()[j]
    sites["aquifer"] = (aquifer([vect.get(f"mdg_{s}".lower(), "") for s in sites.site]) if vect is not None
                        else aquifer(glim_class(sites.lat, sites.lon, grid, head)))
    sites["mondial_mm"] = 10 ** knn_log(src, sites)
    y = np.log10(sites.r_mm)
    sites["mondial_gagne"] = np.abs(np.log10(sites.mondial_mm) - y) < np.abs(np.log10(sites.t2_mm) - y)
    w1 = int(sites.mondial_gagne.sum())
    t1 = (w1, len(sites), sign_test(w1, len(sites)))
    rho, p = stats.spearmanr(sites.mondial_mm, sites.r_mm)
    sed = sites.aquifer.isin(["Sedimentary", "Unconsolidated"])
    ordre = bool(sed.any() and (~sed).any() and sites.mondial_mm[sed].median() > sites.mondial_mm[~sed].median())
    t2 = {"rho": float(rho), "p": float(p), "ordre": ordre, "soutenue": bool(rho > 0 and p < 0.05 and ordre)}
    vd = ROOT / "validation"
    suf = "" if vect is None else "_vectoriel"
    txt = report(len(src), accord, lo, t_lo, h, sites, t1, t2)
    if vect is not None:
        acc = float((b.bgs == b.aquifer).mean()) if len(b) else 0.0
        ok = t1[0] >= 10 and t1[2] < 0.05 and t2["soutenue"] and acc > 0.7
        txt = txt.replace("# Transfert de connaissances depuis des régions analogues : recharge", "# Transfert par analogues : recharge, typage par la GLiM vectorielle (reprise annoncée)")
        verdict = "transfert démontré" if ok else "inchangée (plausible, non démontré)"
        txt += ("\nRègle de la reprise (fixée avant calcul) : conclusion relevée à « démontré » seulement si H-T1 et H-T2 "
                f"réussissent et si l'accord avec le BGS dépasse 70 % (ici {acc:.0%}). **Conclusion : {verdict}**.\n")
    (vd / f"transfert_analogues{suf}.md").write_text(txt, encoding="utf-8")
    sites[["site", "source", "aquifer", "r_mm", "mondial_mm", "t2_mm", "mondial_gagne"]].round(1).to_csv(vd / f"transfert_analogues_madagascar{suf}.csv", index=False)
    print(f"Analogues : niveau 1 {t_lo[0]}/{t_lo[1]} ; H-R1 p = {h.get('p')} ; H-T1 {t1[0]}/{t1[1]} ; H-T2 rho = {rho:+.2f}")


if __name__ == "__main__":
    main()
