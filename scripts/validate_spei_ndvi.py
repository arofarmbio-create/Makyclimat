"""SPI ou SPEI pour suivre le stress de la végétation (NDVI MODIS), par district. Protocole fixé avant les calculs :
validation/protocole_spei_ndvi.md.

Entrées : data/<pays>/drought/{pluie,et0,ndvi}_districts.csv (scripts/build_drought_series.py).
Sorties : validation/spei_ndvi.md, validation/spei_ndvi_districts.csv, validation/spei_controle_et0.csv.
Usage : python scripts/validate_spei_ndvi.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from math import comb

import numpy as np
import pandas as pd

import soilwater_core as C
from common import DATA_DIR, country_data_dir, grid_dir, read_units

SCALES = (1, 3, 6)
LAGS = (0, 1, 2)
MAIN = (3, 1)
GROW = (12, 1, 2, 3, 4, 5)
DRY_REGIONS = ("Androy", "Anosy", "Atsimo-Andrefana", "Menabe", "Melaky", "Boeny", "Ihorombe")
NDVI_YEARS = (2001, 2025)
GRAND_SUD = ("Androy", "Anosy", "Atsimo-Andrefana")


def wide(path):
    d = pd.read_csv(path, dtype={"adm2": str})
    return d.pivot(index="mois", columns="adm2", values="valeur").sort_index()


def sign_p(w, n):
    return float(sum(comb(n, k) for k in range(w, n + 1)) / 2 ** n) if n else float("nan")


def corr_at(idx_s, ndvi_z, months, n, lag):
    """Corrélation indice(t - lag) / NDVI(t) sur les mois de végétation active."""
    ix = idx_s.shift(lag)
    sel = [m for m in ndvi_z.index if int(m[5:7]) in GROW and NDVI_YEARS[0] <= int(m[:4]) <= NDVI_YEARS[1]]
    a, b = ix.loc[sel], ndvi_z.loc[sel]
    ok = a.notna() & b.notna()
    return float(np.corrcoef(a[ok], b[ok])[0, 1]) if ok.sum() >= 30 else np.nan


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    dd = country_data_dir(args.country) / "drought"
    P, E, N = wide(dd / "pluie_districts.csv"), wide(dd / "et0_districts.csv"), wide(dd / "ndvi_districts.csv")
    months = sorted(set(P.index) & set(E.index))
    cols = sorted(set(P.columns) & set(E.columns) & set(N.columns))
    P, E = P.loc[months, cols], E.loc[months, cols]
    m0 = int(months[0][5:7])
    spi = {n: pd.DataFrame(C.spi(P.to_numpy(), n, m0), index=months, columns=cols) for n in SCALES}
    spe = {n: pd.DataFrame(C.spei(P.to_numpy(), E.to_numpy(), n, m0), index=months, columns=cols) for n in SCALES}
    Nn = N.loc[[m for m in N.index if NDVI_YEARS[0] <= int(m[:4]) <= NDVI_YEARS[1]], cols]
    nz = pd.DataFrame(C.monthly_standardized(Nn.to_numpy(), int(Nn.index[0][5:7])), index=Nn.index, columns=cols)
    nz = nz.reindex(months)
    units = read_units(args.country)
    names = dict(zip(units.pcode, units.name))
    adm1 = dict(zip(units.pcode, units.adm1))
    norm = lambda x: "".join(ch for ch in str(x).lower() if ch.isalnum())
    dry_codes = {p for p, nm in names.items() if norm(nm) in {norm(r) for r in DRY_REGIONS} and len(p) == 4}
    if len(dry_codes) != len(DRY_REGIONS):
        print(f"::warning::régions sèches trouvées : {len(dry_codes)} / {len(DRY_REGIONS)}")
    rows = []
    for d in cols:
        r = {"adm2": d, "district": names.get(d, d), "region": names.get(adm1.get(d), ""), "sec": adm1.get(d) in dry_codes}
        for kind, I in (("spi", spi), ("spei", spe)):
            grid = {(n, L): corr_at(I[n][d], nz[d], months, n, L) for n in SCALES for L in LAGS}
            r[f"r_{kind}_principal"] = grid[MAIN]
            best = max(grid, key=lambda k: -np.inf if not np.isfinite(grid[k]) else grid[k])
            r[f"r_{kind}_meilleur"], r[f"{kind}_meilleur_n_L"] = grid[best], f"{best[0]}-{best[1]}"
        rows.append(r)
    D = pd.DataFrame(rows)
    D.round(4).to_csv(DATA_DIR.parent / "validation" / "spei_ndvi_districts.csv", index=False)
    # contrôle de l'ET0 : climatologie 2016-2020 contre celle d'Open-Meteo déjà utilisée par le site (et0_cache.json)
    ctrl = control_et0(E, units, args.country)
    H = {}
    for grp, g in (("secs", D[D.sec]), ("humides", D[~D.sec])):
        for k in ("principal", "meilleur"):
            v = g[[f"r_spei_{k}", f"r_spi_{k}"]].dropna()
            w = int((v[f"r_spei_{k}"] > v[f"r_spi_{k}"]).sum())
            H[(grp, k)] = (w, len(v), sign_p(w, len(v)), float(v[f"r_spi_{k}"].median()) if len(v) else np.nan,
                           float(v[f"r_spei_{k}"].median()) if len(v) else np.nan)
    gs = grand_sud(spi[6], spe[6], names, adm1)
    write_md(DATA_DIR.parent / "validation" / "spei_ndvi.md", D, H, ctrl, gs, months)
    print(pd.DataFrame(H, index=["gagne", "n", "p", "r_spi_med", "r_spei_med"]).T.to_string())


def control_et0(E, units, country):
    p = grid_dir(country) / "et0_cache.json"
    if not p.exists():
        return None
    cache = json.loads(p.read_text())
    sel = [m for m in E.index if 2016 <= int(m[:4]) <= 2020]
    ours = E.loc[sel].groupby([int(m[5:7]) for m in sel]).mean().mean(axis=1)
    om = np.nanmean(np.array([v for v in cache.values() if v]), axis=0)
    df = pd.DataFrame({"mois": range(1, 13), "et0_era5land_pm_mm": ours.reindex(range(1, 13)).to_numpy(), "et0_openmeteo_mm": om})
    df.round(1).to_csv(DATA_DIR.parent / "validation" / "spei_controle_et0.csv", index=False)
    return df


def grand_sud(s6, e6, names, adm1):
    norm = lambda x: "".join(ch for ch in str(x).lower() if ch.isalnum())
    ds = [d for d in s6.columns if norm(names.get(adm1.get(d))) in {norm(r) for r in GRAND_SUD}]
    out = {}
    for kind, I in (("SPI-6", s6), ("SPEI-6", e6)):
        v = I.loc[[m for m in I.index if "2019-07" <= m <= "2023-06"], ds].mean(axis=1)
        dry = v[v <= -1]
        out[kind] = (dry.index[0] if len(dry) else None, int(len(dry)), float(v.min()))
    return out


def write_md(path, D, H, ctrl, gs, months):
    f = lambda v, d=2: "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{d}f}".replace(".", ",")
    L = ["# SPI ou SPEI pour suivre le stress de la végétation (NDVI MODIS), par district", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/validate_spei_ndvi.py`, selon `validation/protocole_spei_ndvi.md` "
         "(fixé avant les calculs).", "",
         f"- {len(D)} districts ({int(D.sec.sum())} secs, {int((~D.sec).sum())} humides) ; indices calculés sur {months[0]} - {months[-1]} ; "
         f"NDVI {NDVI_YEARS[0]}-{NDVI_YEARS[1]}, mois de décembre à mai.",
         "- Pluie CHIRPS, ET0 Penman-Monteith FAO-56 depuis ERA5-Land (moyennes mensuelles), NDVI MOD13C2 (pixels fiables).", "",
         "## 1. Hypothèses fixées à l'avance (test du signe unilatéral entre districts)", "",
         "| Districts | Combinaison | SPEI meilleur que SPI | p | r médian SPI | r médian SPEI |", "|---|---|---|---|---|---|"]
    for (grp, k), (w, n, p, a, b) in H.items():
        L.append(f"| {grp} | {'principale (3 mois, décalage 1)' if k == 'principal' else 'meilleure de chaque indice'} | {w} / {n} | {f(p, 3)} | {f(a)} | {f(b)} |")
    hs, hh = H[("secs", "principal")], H[("humides", "principal")]
    L += ["", f"- **H1** (gain du SPEI dans les districts secs) : **{'soutenue' if hs[2] < 0.05 else 'non soutenue'}**.",
          f"- **H2** (pas de gain systématique dans les districts humides) : **{'soutenue' if hh[2] >= 0.05 else 'non soutenue'}**.", "",
          "## 2. Sécheresse du Grand Sud 2020-2022 (moyenne des districts d'Androy, Anosy, Atsimo-Andrefana ; juillet 2019 - juin 2023)", "",
          "| Indice | Premier mois ≤ −1 | Mois ≤ −1 | Minimum |", "|---|---|---|---|"]
    for k, (first, nmo, mn) in gs.items():
        L.append(f"| {k} | {first or '—'} | {nmo} | {f(mn)} |")
    if ctrl is not None:
        L += ["", "## 3. Contrôle de l'ET0 (moyenne nationale des districts, 2016-2020, mm/mois)", "",
              "| Mois | ERA5-Land Penman-Monteith (ce travail) | Open-Meteo (site) |", "|---|---|---|"]
        L += [f"| {int(r.mois)} | {f(r.et0_era5land_pm_mm, 0)} | {f(r.et0_openmeteo_mm, 0)} |" for _, r in ctrl.iterrows()]
    L += ["", "Détail par district : `validation/spei_ndvi_districts.csv`.", "", "## Limites", "",
          "- ET0 à partir de moyennes mensuelles (pas de Tmax/Tmin journaliers) : légère sous-estimation possible du déficit de vapeur.",
          "- Le NDVI réagit aussi aux feux, à l'irrigation et aux cyclones ; il sature en forêt dense (est humide).",
          "- Autocorrélation des séries : seules les comparaisons entre districts (test du signe) servent à conclure."]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
