"""H-N7, maillon A : état de l'océan avant la saison → pluies extrêmes du Grand Sud
(validation/protocole_climat_extremes_nappes.md ; test principal fixé le 09/11/2026 avant tout calcul).

Principal : Spearman entre l'ONI de juillet-septembre (année Y − 1) et la pluie du mois le plus fort de la saison
novembre-avril (fin en Y), Atsimo-Andrefana ; p bilatéral par permutation (5 000), seuil 5 %. Descriptif : validation
croisée (régression linéaire, une saison laissée de côté, MSSS) et test chronologique (≤ 2005 / > 2005).
Exploratoire : 9 combinaisons (3 régions × ONI, DMI, SIOD) et canal de Mozambique, résultat continu et binaire (au moins
un mois au-dessus du 95e centile des mois de novembre à avril), Benjamini-Hochberg 10 %.
Saisons incomplètes exclues. Sortie : validation/hn7_maillon_a.md. Usage : python scripts/hn7_maillon_a.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd
from scipy import stats

from build_teleconnections import bh, region_series
from common import DATA_DIR, ROOT, grid_dir, load_grid, read_units

SEED, NPERM, SPLIT = 20261109, 5000, 2005
REGIONS = {"MG51": "Atsimo-Andrefana", "MG52": "Androy", "MG53": "Anosy"}


def indice_jas(df: pd.DataFrame, years, col="value") -> np.ndarray:
    """Moyenne juillet-septembre de l'année Y − 1 pour chaque saison se terminant en Y."""
    if "center_month" in df:
        s = df[df.center_month == 8].set_index("year").oni
    else:
        g = df[df.month.isin([7, 8, 9])].groupby("year")[col].agg(["mean", "count"])
        s = g[g["count"] == 3]["mean"]
    return np.array([s.get(y - 1, np.nan) for y in years], float)


def perm_p(x, y, n=NPERM, seed=SEED) -> tuple[float, float]:
    """Spearman et p bilatéral par permutation."""
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    r = stats.spearmanr(x, y).statistic
    rng = np.random.default_rng(seed)
    null = np.array([stats.spearmanr(x, rng.permutation(y)).statistic for _ in range(n)])
    return float(r), float((np.sum(np.abs(null) >= abs(r)) + 1) / (n + 1))


def msss_loo(x, y) -> float:
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    pred, clim = np.empty(len(y)), np.empty(len(y))
    for i in range(len(y)):
        m = np.ones(len(y), bool)
        m[i] = False
        b = np.polyfit(x[m], y[m], 1)
        pred[i], clim[i] = np.polyval(b, x[i]), y[m].mean()
    return float(1 - np.mean((pred - y) ** 2) / np.mean((clim - y) ** 2))


def msss_chrono(x, y, years) -> float:
    ok = np.isfinite(x) & np.isfinite(y)
    x, y, years = x[ok], y[ok], years[ok]
    tr, te = years <= SPLIT, years > SPLIT
    b = np.polyfit(x[tr], y[tr], 1)
    return float(1 - np.mean((np.polyval(b, x[te]) - y[te]) ** 2) / np.mean((y[tr].mean() - y[te]) ** 2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    a = ap.parse_args()
    ms = load_grid(grid_dir(a.country) / "monthly_series.npz")
    years = np.array([int(y) for y in ms["years"]])
    reg = region_series(ms, read_units(a.country))
    oni = pd.read_csv(DATA_DIR / "enso" / "oni.csv")
    ind = {"ONI": indice_jas(oni, years), "DMI": indice_jas(pd.read_csv(DATA_DIR / "enso" / "dmi_ersst.csv"), years),
           "SIOD": indice_jas(pd.read_csv(DATA_DIR / "enso" / "siod_ersst.csv"), years),
           "canal de Mozambique": indice_jas(pd.read_csv(DATA_DIR / "enso" / "moz_ersst.csv"), years)}
    series = {}
    for pc, nom in REGIONS.items():
        v = np.asarray(reg[pc], float)                       # (saisons, 6 mois)
        complete = np.isfinite(v).all(axis=1)
        seuil = np.nanpercentile(v[complete], 95)
        series[nom] = {"max": np.where(complete, np.nanmax(v, axis=1), np.nan),
                       "binaire": np.where(complete, (v > seuil).any(axis=1).astype(float), np.nan), "seuil": seuil}

    y = series["Atsimo-Andrefana"]["max"]
    r0, p0 = perm_p(ind["ONI"], y)
    n0 = int((np.isfinite(y) & np.isfinite(ind["ONI"])).sum())
    m_loo, m_chr = msss_loo(ind["ONI"], y), msss_chrono(ind["ONI"], y, years)
    principal = p0 < 0.05

    rows = []
    for nom in REGIONS.values():
        for k, x in ind.items():
            for res in ("max", "binaire"):
                r, p = perm_p(x, series[nom][res], n=2000)
                rows.append({"region": nom, "indice": k, "resultat": "pluie maximale" if res == "max" else "au moins un mois extrême", "r": r, "p": p})
    ex = pd.DataFrame(rows)
    ex["retenu_BH"] = False
    for res in ex.resultat.unique():
        m = ex.resultat == res
        ex.loc[m, "retenu_BH"] = bh(ex.loc[m, "p"].to_numpy())

    L = ["# H-N7, maillon A : océan avant la saison → pluies extrêmes du Grand Sud", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/hn7_maillon_a.py`, selon `validation/protocole_climat_extremes_nappes.md` "
         "(test principal fixé le 09/11/2026 avant tout calcul, après `puissance_hn7.md`). Pluie : CHIRPS v2.0 par région ; ONI : NOAA CPC ; "
         "DMI, SIOD et canal de Mozambique : ERSST v5.", "",
         "## Test principal", "",
         f"ONI de juillet-septembre contre pluie du mois le plus fort de la saison, Atsimo-Andrefana, {n0} saisons complètes : "
         f"**ρ = {r0:+.2f}, p = {p0:.3f}** (bilatéral, permutation). **{'Lien retenu' if principal else 'Lien non retenu'}** (seuil 5 %). "
         "Statut : exploratoire de justesse (puissance 47 % pour ρ = 0,3).", "",
         f"Descriptif : MSSS en validation croisée {m_loo:+.2f} ; MSSS chronologique (apprentissage jusqu'en {SPLIT}) {m_chr:+.2f} "
         "(positif = meilleur que la moyenne historique).", "",
         "## Exploratoire (Benjamini-Hochberg 10 % par type de résultat)", "",
         "| Région | Indice | Résultat | ρ | p | Retenu après correction |", "|---|---|---|---|---|---|"]
    for x in ex.itertuples():
        L.append(f"| {x.region} | {x.indice} | {x.resultat} | {x.r:+.2f} | {x.p:.3f} | {'oui' if x.retenu_BH else 'non'} |")
    L += ["", "Seuils du 95e centile mensuel (mm/mois) : " + " ; ".join(f"{n} {s['seuil']:.0f}" for n, s in series.items()) + ".", "",
          "Limites : 45 saisons au plus ; CHIRPS sous-estime souvent les extrêmes ; ce maillon ne dit rien des nappes (maillon B).", ""]
    (ROOT / "validation" / "hn7_maillon_a.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"principal rho {r0:+.3f} p {p0:.4f} n {n0} ; MSSS loo {m_loo:+.2f} chrono {m_chr:+.2f} ; retenus BH {int(ex.retenu_BH.sum())}")


if __name__ == "__main__":
    main()
