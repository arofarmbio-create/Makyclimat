"""Recharge du karst, T2K (validation/protocole_recharge_karst.md, fixé avant le calcul le 09/11/2026).

R/P du karst : mailles mesurées de Wan, Döll et Müller Schmied (2024) avec une part karstique f ≥ 0,3, hors Madagascar,
par climat (colonne arid1_humid0) : médiane r_k, quantiles 10 et 90 %. Recharge karstique K = r_k × P.
Mélange : T2K = (1 − f) × T2 + f × K, même mélange pour les bornes ; f = part karstique de la maille (grille de Wan et
al. à 0,5°, maille la plus proche). Sensibilité : seuil f ≥ 0,5.
H-K1 : T2K place au moins autant de références H-C6 que T2 (3 sur 8). H-K2 : intervalle de T2K contenant la valeur
centrale d'au moins 3 des 5 puits GROSoM (contrôle, un seul groupe de sites).
Entrées hors dépôt (grille T2, séries) : calcul local. Sorties : validation/recharge_karst.md,
inputs/hydrogeologie/recharge_t2k.csv.
Usage : python scripts/recharge_karst.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib

import numpy as np
import pandas as pd

from common import ROOT, country_data_dir

F_REF, F_SENS = 0.3, 0.5
ARID = 0.5
H_K2_MIN = 3
WAN = "Wan, Döll et Müller Schmied (2024), figshare 23592666, CC BY 4.0"


def karst_ratios(ref: pd.DataFrame, fmin: float = F_REF) -> pd.DataFrame:
    """Quantiles 10 %, 50 %, 90 % de R/P des mailles karstiques (f ≥ fmin) hors Madagascar, par climat."""
    d = ref.copy()
    d["r"] = pd.to_numeric(d["Obs_gwr/p"], errors="coerce")
    d = d[(d.fkarst >= fmin) & d.r.notna() & ~d.Country.astype(str).str.contains("Madagascar", case=False)]
    d["clim"] = np.where(d.arid1_humid0 == 1, "aride", "humide")
    return d.groupby("clim").r.agg(n="size", q10=lambda s: s.quantile(0.1), med="median",
                                   q90=lambda s: s.quantile(0.9)).reset_index()


def mix(t2, lo, hi, f, p, q10, med, q90) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """T2K et son intervalle : mélange de T2 et de la recharge karstique selon la part karstique f."""
    t2, lo, hi, f, p, q10, med, q90 = (np.asarray(x, float) for x in (t2, lo, hi, f, p, q10, med, q90))
    f = np.clip(np.nan_to_num(f), 0, 1)
    return (1 - f) * t2 + f * med * p, (1 - f) * lo + f * q10 * p, (1 - f) * hi + f * q90 * p


def apply(grid: pd.DataFrame, f: np.ndarray, kr: pd.DataFrame, prefix: str = "T2K") -> pd.DataFrame:
    g = grid.copy()
    g["f_karst"] = f
    g["clim"] = np.where(np.asarray(g.Aridity, float) < ARID, "aride", "humide")
    k = kr.set_index("clim")
    q = {c: k.reindex(g.clim)[c].to_numpy() for c in ("q10", "med", "q90")}
    g["K_mmpa"] = q["med"] * g.LTA_P_mmpa
    g[f"{prefix}_mmpa"], g[f"{prefix}_bas_mmpa"], g[f"{prefix}_haut_mmpa"] = mix(
        g.T2_mmpa, g.T2_bas_mmpa, g.T2_haut_mmpa, f, g.LTA_P_mmpa, q["q10"], q["med"], q["q90"])
    return g


def nearest(lat, lon, plat, plon) -> np.ndarray:
    from sklearn.neighbors import BallTree
    return BallTree(np.radians(np.c_[plat, plon]), metric="haversine").query(
        np.radians(np.c_[np.asarray(lat), np.asarray(lon)]), k=1, return_distance=False)[:, 0]


def main() -> None:
    import recharge_fluctuation as RF
    import validate_transfert_madagascar as V
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    cdir = country_data_dir(args.country)
    ref = pd.read_excel(cdir / "analogues" / "recharge_mondiale" / "figshare_23592666" / "1_Ground-based-estimates.xlsx",
                        sheet_name="Sheet1")
    kr, kr_s = karst_ratios(ref, F_REF), karst_ratios(ref, F_SENS)
    fk = pd.read_csv(cdir / "nappes_mondiales" / "fkarst_mdg.csv")
    grid = pd.read_csv(cdir / "nappes_mondiales" / "recharge_transferee.csv")
    f = fk.fkarst.to_numpy()[nearest(grid.lat, grid.lon, fk.lat, fk.lon)]
    g = apply(grid, f, kr)
    gs = apply(grid, f, kr_s, "T2Ks")

    refs = V.site_references(args.country, g)
    ev = {v: V.evaluate(g, v, refs) for v in ("T2", "T2K")}
    n_ok = {v: int(ev[v].dans_intervalle.dropna().sum()) for v in ev}
    n_ref = len(ev["T2"].dans_intervalle.dropna())
    h1 = n_ok["T2K"] >= n_ok["T2"]

    sites = RF.build_sites(cdir)
    gro = sites[(sites.source == "GROSoM") & sites.retenu.fillna(False).astype(bool)].reset_index(drop=True)
    j = nearest(gro.lat, gro.lon, g.lat, g.lon)
    gro["f_karst"] = g.f_karst.to_numpy()[j]
    for v in ("T2", "T2K"):
        gro[v], gro[f"{v}_bas"], gro[f"{v}_haut"] = (g[f"{v}{s}"].to_numpy()[j] for s in ("_mmpa", "_bas_mmpa", "_haut_mmpa"))
        gro[f"{v}_dedans"] = (gro[f"{v}_bas"] <= gro.r_mm) & (gro.r_mm <= gro[f"{v}_haut"])
    h2 = int(gro.T2K_dedans.sum()) >= H_K2_MIN

    out = g[["lon", "lat", "LTA_P_mmpa", "Aridity", "f_karst", "T2_mmpa", "K_mmpa", "T2K_mmpa", "T2K_bas_mmpa", "T2K_haut_mmpa"]]
    hd = ROOT / "inputs" / "hydrogeologie"
    hd.mkdir(parents=True, exist_ok=True)
    fp = hd / "recharge_t2k.csv"
    out.round(4).to_csv(fp, index=False, lineterminator="\n")
    sha = hashlib.sha256(fp.read_bytes()).hexdigest()

    kk = g.f_karst > 0
    L = ["# Recharge du karst (T2K)", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/recharge_karst.py`, selon `validation/protocole_recharge_karst.md` "
         f"(fixé avant le calcul). Part karstique et mesures de référence : {WAN}. Calcul local.", "",
         "## Part de la pluie qui recharge le karst (mailles mesurées, hors Madagascar)", "",
         "| Seuil de part karstique | Climat | Mailles | R/P 10 % | R/P médiane | R/P 90 % |", "|---|---|---|---|---|---|"]
    for lab, t in ((f"f ≥ {F_REF} (principal)", kr), (f"f ≥ {F_SENS} (sensibilité)", kr_s)):
        for x in t.itertuples():
            L.append(f"| {lab} | {x.clim} | {x.n} | {x.q10:.3f} | {x.med:.3f} | {x.q90:.3f} |")
    L += ["", "## Emprise du karst à Madagascar (grille à 0,5°)", "",
          f"{int(kk.sum())} mailles sur {len(g)} avec f > 0 ; {int((g.f_karst >= F_REF).sum())} avec f ≥ {F_REF}. "
          f"Recharge médiane des mailles avec f > 0 : T2 {g.T2_mmpa[kk].median():.0f} → T2K {g.T2K_mmpa[kk].median():.0f} mm/an "
          f"(sensibilité f ≥ {F_SENS} : {gs.T2Ks_mmpa[kk].median():.0f}).", "",
          "| Zone (maille la plus proche) | f | Pluie | T2 | T2K (intervalle) |", "|---|---|---|---|---|"]
    for name, lat, lon in (("Toliara", -23.35, 43.67), ("Plateau Mahafaly (Betioky)", -23.7, 44.4), ("Bemaraha", -18.8, 44.8),
                           ("Ankarana", -12.9, 49.1), ("Mahajanga", -15.72, 46.32)):
        i = int(np.argmin((g.lat - lat) ** 2 + (g.lon - lon) ** 2))
        r = g.iloc[i]
        L.append(f"| {name} | {r.f_karst:.2f} | {r.LTA_P_mmpa:.0f} | {r.T2_mmpa:.0f} | {r.T2K_mmpa:.0f} "
                 f"({r.T2K_bas_mmpa:.0f} à {r.T2K_haut_mmpa:.0f}) |")
    L += ["", "## H-K1 : non-régression sur les références de H-C6", "",
          f"T2 : {n_ok['T2']} sur {n_ref} ; T2K : {n_ok['T2K']} sur {n_ref}. **H-K1 {'soutenue' if h1 else 'non soutenue'}**.", "",
          "## H-K2 : puits GROSoM (contrôle, un seul groupe de sites)", "",
          "| Puits | f | Mesurée | T2 (intervalle) | T2K (intervalle) | Dans T2K |", "|---|---|---|---|---|---|"]
    for x in gro.itertuples():
        L.append(f"| {x.site} | {x.f_karst:.2f} | {x.r_mm:.0f} | {x.T2:.0f} ({x.T2_bas:.0f} à {x.T2_haut:.0f}) | "
                 f"{x.T2K:.0f} ({x.T2K_bas:.0f} à {x.T2K_haut:.0f}) | {'oui' if x.T2K_dedans else 'non'} |")
    L += ["", f"{int(gro.T2K_dedans.sum())} sur {len(gro)} (T2 : {int(gro.T2_dedans.sum())}). **H-K2 "
          f"{'soutenue' if h2 else 'non soutenue'}** (règle : au moins {H_K2_MIN}).", ""]
    if (gro.f_karst == 0).all():
        L += ["**Échec de résolution** : la maille des puits GROSoM a une part karstique nulle à 0,5° ; la méthode ne peut pas "
              "y corriger T2.", ""]
    L += ["## Validation prospective", "",
          f"Carte figée le {dt.date.today().isoformat()} : `inputs/hydrogeologie/recharge_t2k.csv`, SHA-256 `{sha}` (fin de "
          "ligne LF). Réussite future si au moins 60 % des nouveaux sites karstiques hors Toliara sont retrouvés.", "",
          "## Décision (fixée avant le calcul)", "",
          ("T2K remplace T2 dans les mailles avec f > 0 ; l'atlas par sous-bassin est refait." if h1 and h2 else
           "T2 reste la valeur centrale ; T2K est publiée comme sensibilité et figée pour le test prospectif."), ""]
    (ROOT / "validation" / "recharge_karst.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"H-K1 {h1} ({n_ok['T2']} -> {n_ok['T2K']}) ; H-K2 {h2} ({int(gro.T2K_dedans.sum())}/{len(gro)})")


if __name__ == "__main__":
    main()
