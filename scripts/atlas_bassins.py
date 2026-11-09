"""Atlas des nappes par bassin versant (validation/protocole_atlas_bassins.md, fixé avant le calcul).

Pour chacun des 108 grands bassins (hydro.npz, noms dans docs/data/<pays>/hydro/basins.geojson) : taille, population,
niveau statique (carte v2), fiabilité, ressource, bilan prélèvements domestiques / recharge, relief et eau du sol.
Fokontany rattaché au bassin de la maille qui contient son point représentatif.
Sorties : validation/atlas_bassins.md, data/<pays>/external/nappes_bassins.csv.
Usage : python scripts/atlas_bassins.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import json

import numpy as np
import pandas as pd

import nappes_ressource as NR
import validate_nappes_hc1 as H1
import validate_nappes_hc2 as H2
from common import ROOT, country_data_dir, grid_dir, load_grid, read_units

MIN_WELLS, EXTRA_OK, EXTRA_PART = 10, 0.30, 0.60
SOURCE = "MakyClimat atlas des nappes par bassin v1 (validation/atlas_bassins.md)"


def reliability(n_wells: int, extra_share: float) -> str:
    if n_wells >= MIN_WELLS and extra_share < EXTRA_OK:
        return "mesurée"
    if n_wells >= 1 or extra_share < EXTRA_PART:
        return "partielle"
    return "non mesurée"


def basin_balance(prelev_mm, recharge_mm, area_km2) -> float:
    """Bilan du bassin : Σ prélèvements / Σ recharge, pondérés par la surface."""
    a = np.asarray(area_km2, float)
    p, r = np.asarray(prelev_mm, float), np.asarray(recharge_mm, float)
    ok = np.isfinite(p) & np.isfinite(r) & np.isfinite(a)
    den = np.sum(r[ok] * a[ok])
    return float(np.sum(p[ok] * a[ok]) / den) if den > 0 else float("nan")


def t2c_at(lon, lat) -> np.ndarray:
    """Recharge corrigée T2c de la maille la plus proche (même rattachement que nappes_ressource.py)."""
    from sklearn.neighbors import BallTree
    rt = pd.read_csv(ROOT / "inputs" / "hydrogeologie" / "recharge_t2c.csv")
    j = BallTree(np.radians(np.c_[rt.lat, rt.lon]), metric="haversine").query(
        np.radians(np.c_[np.asarray(lat), np.asarray(lon)]), k=1, return_distance=False)[:, 0]
    return rt.T2c_mmpa.to_numpy()[j]


def pivot(path, inds) -> pd.DataFrame:
    d = pd.read_csv(path, dtype={"pcode": str})
    d = d[d.indicateur.isin(inds)]
    d["valeur"] = pd.to_numeric(d.valeur, errors="coerce")
    return d.pivot_table(index="pcode", columns="indicateur", values="valeur")


def aggregate(fk: pd.DataFrame, wells_per_basin: pd.Series, names: dict) -> pd.DataFrame:
    rows = []
    for b, g in fk.groupby("basin"):
        if b <= 0:
            continue
        ex = float(g.extrapolation.mean())
        nw = int(wells_per_basin.get(b, 0))
        area = float(g.area_km2.sum())
        rows.append({"bassin": int(b), "nom": names.get(int(b), f"Bassin {b}"), "surface_km2": area, "fokontany": len(g),
                     "population": float(g.pop_ajustee.sum()),
                     "niveau_median_m": float(g.niveau_m.median()), "niveau_q1_m": float(g.niveau_m.quantile(0.25)),
                     "niveau_q3_m": float(g.niveau_m.quantile(0.75)), "erreur_attendue_m": float(g.erreur_m.median()),
                     "part_extrapolation": ex, "releves": nw, "densite_releves_1000km2": nw / area * 1000 if area else np.nan,
                     "recharge_mm": float(g.r_mm.median()), "stock_mm": float(g.v_mm.median()), "renouvellement_ans": float(g.tau_ans.median()),
                     "bilan": basin_balance(g.prelev_mm, g.r_mm, g.area_km2),
                     "bilan_sans_reseau": basin_balance(g.prelev_sans_reseau_mm, g.r_mm, g.area_km2),
                     "altitude_m": float(g.elev_mean_m.mean()), "pente_pct": float(g.slope_mean_pct.mean()),
                     "fond_vallee_pct": float(g.hand_lt5_pct.mean()), "reserve_utile_mm": float(g.whc_mm.median()),
                     "humidite_sol_pct": float(g.sm_rel_pct.median()), "fiabilite": reliability(nw, ex)})
    t = pd.DataFrame(rows)
    t["classe_bilan"] = NR.label(t.bilan, NR.CLASSES)
    return t


def report(t: pd.DataFrame) -> str:
    order = {"mesurée": 0, "partielle": 1, "non mesurée": 2}
    t = t.sort_values(["bilan"], ascending=False)
    L = ["# Atlas des nappes par bassin versant (version 1, carte du niveau statique v2)", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/atlas_bassins.py`, selon `validation/protocole_atlas_bassins.md` "
         "(fixé avant le calcul). Analyse descriptive. **Approximations** : recharge non validée, pression domestique seulement "
         "(15 L/j, norme Sphère), niveau statique approximatif hors du Grand Sud.", "",
         f"108 bassins ; fiabilité : {int((t.fiabilite == 'mesurée').sum())} mesurée, {int((t.fiabilite == 'partielle').sum())} partielle, "
         f"{int((t.fiabilite == 'non mesurée').sum())} non mesurée. Bilan prélèvements / recharge : {int((t.classe_bilan == 'élevé').sum())} "
         f"bassins élevés, {int((t.classe_bilan == 'modéré').sum())} modérés.", "",
         "## Les 25 bassins les plus peuplés", "",
         "| Bassin | Surface (km²) | Population | Niveau médian (m) | Recharge (mm/an) | Renouvellement (ans) | Bilan | Altitude (m) | Réserve utile du sol (mm) | Relevés | Fiabilité |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in t.sort_values("population", ascending=False).head(25).itertuples():
        L.append(f"| {r.nom} (n° {r.bassin}) | {r.surface_km2:,.0f} | {r.population:,.0f} | {r.niveau_median_m:.1f} | {r.recharge_mm:.0f} | {r.renouvellement_ans:.0f} | "
                 f"{r.bilan:.3f} | {r.altitude_m:.0f} | {r.reserve_utile_mm:.0f} | {r.releves} | {r.fiabilite} |")
    L += ["", "## Bassins à bilan le plus fort (10 premiers)", "",
          "| Bassin | Bilan (réseau 47 %) | Bilan (réseau coupé) | Recharge (mm/an) | Population | Fiabilité |", "|---|---|---|---|---|---|"]
    for r in t.head(10).itertuples():
        L.append(f"| {r.nom} (n° {r.bassin}) | {r.bilan:.3f} | {r.bilan_sans_reseau:.3f} | {r.recharge_mm:.0f} | {r.population:,.0f} | {r.fiabilite} |")
    L += ["", "Tableau complet : `data/mdg/external/nappes_bassins.csv`. Classement par fiabilité : " +
          " ; ".join(f"{k} {int((t.fiabilite == k).sum())}" for k in sorted(order, key=order.get)) + ".", ""]
    return "\n".join(L).replace(",", " ") + "\n"


def report_sub(t: pd.DataFrame) -> str:
    cls = t.classe_bilan.value_counts()
    L = ["# Atlas des nappes par sous-bassin (version 1, carte du niveau statique v2)", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/atlas_bassins.py --niveau sous-bassin`, selon "
         "`validation/protocole_atlas_bassins.md` (déclinaison du 04/11, fixée avant le calcul). Mêmes réserves que l'atlas par bassin.", "",
         f"{len(t)} sous-bassins avec au moins un fokontany ; fiabilité : {int((t.fiabilite == 'mesurée').sum())} mesurée, "
         f"{int((t.fiabilite == 'partielle').sum())} partielle, {int((t.fiabilite == 'non mesurée').sum())} non mesurée. "
         f"Classes de bilan : faible {int(cls.get('faible', 0))}, modéré {int(cls.get('modéré', 0))}, élevé {int(cls.get('élevé', 0))} "
         f"(réseau d'Antananarivo coupé : élevé {int((t.bilan_sans_reseau > 0.4).sum())}).", "",
         "## Les 30 sous-bassins au bilan le plus fort (au moins 1 000 habitants)", "",
         "| Sous-bassin | Population | Bilan (réseau 47 %) | Bilan (réseau coupé) | Recharge (mm/an) | Niveau médian (m) | Fiabilité |",
         "|---|---|---|---|---|---|---|"]
    for r in t[t.population >= 1000].sort_values("bilan_sans_reseau", ascending=False).head(30).itertuples():
        L.append(f"| {r.nom} | {r.population:,.0f} | {r.bilan:.3f} | {r.bilan_sans_reseau:.3f} | {r.recharge_mm:.0f} | {r.niveau_median_m:.1f} | {r.fiabilite} |")
    return "\n".join(L).replace(",", " ") + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--niveau", choices=["bassin", "sous-bassin"], default="bassin")
    ap.add_argument("--recharge", choices=["t2", "t2c"], default="t2",
                    help="t2c : recharge corrigée (validation/controle_recharge.md), pour la fourchette T2 / T2c")
    args = ap.parse_args()
    cdir = country_data_dir(args.country)
    key = "basin" if args.niveau == "bassin" else "subbasin"
    units = read_units(args.country)
    fk = units[units.level == 4][["pcode", "adm2", "adm3", "lon", "lat", "pop", "area_km2"]].reset_index(drop=True)
    h = load_grid(grid_dir(args.country) / "hydro.npz")
    g = (float(h["lon0"]), float(h["lat0"]), float(h["res"]))
    fk["main"] = H2.grid_sample(h["basin"], *g, fk.lon, fk.lat).astype(int)
    fk["basin"] = H2.grid_sample(h[key], *g, fk.lon, fk.lat).astype(int)
    carte = pivot(cdir / "external" / "nappes_carte.csv", ["niveau_statique_m", "niveau_statique_erreur_attendue_m", "niveau_statique_extrapolation"])
    res = pivot(cdir / "external" / "nappes_ressource.csv", ["recharge_mm_an", "stock_mm", "renouvellement_ans"])
    hyd = pivot(cdir / "external" / "hydro.csv", ["elev_mean_m", "slope_mean_pct", "hand_lt5_pct"])
    sw = pivot(cdir / "external" / "soilwater.csv", ["whc_mm", "sm_rel_pct"])
    fk = fk.join(carte, on="pcode").join(res, on="pcode").join(hyd, on="pcode").join(sw, on="pcode")
    fk = fk.rename(columns={"niveau_statique_m": "niveau_m", "niveau_statique_erreur_attendue_m": "erreur_m",
                            "niveau_statique_extrapolation": "extrapolation", "recharge_mm_an": "r_mm", "stock_mm": "v_mm",
                            "renouvellement_ans": "tau_ans"})
    if args.recharge == "t2c":
        fk["r_mm"] = t2c_at(fk.lon, fk.lat)
    import etude_seam as S
    fac, _ = NR.commune_factor(units, S.load_communes(cdir / "seam_raw"))
    pop_seam = fk["pop"] * fk.adm3.map(fac).fillna(1.0)
    fk["pop_ajustee"] = pop_seam * (1 - fk.adm2.map(NR.SURFACE_NETWORK).fillna(0.0))
    fk["prelev_mm"] = NR.withdrawals_mm(fk.pop_ajustee, fk.area_km2)
    fk["prelev_sans_reseau_mm"] = NR.withdrawals_mm(pop_seam, fk.area_km2)
    wells = H1.load_points(cdir / "mgmerl_raw" / "complet_2026-11-03" / "mgmerl_niveau_statique_complet.csv")
    wb = pd.Series(H2.grid_sample(h[key], *g, wells.lon, wells.lat).astype(int)).value_counts()
    gj = json.loads((ROOT / "docs" / "data" / args.country / "hydro" / "basins.geojson").read_text(encoding="utf-8"))
    names = {int(f["properties"]["id"]): f["properties"]["name"] for f in gj["features"]}
    if key == "subbasin":
        dn = dict(zip(units.pcode, units.name))
        dist = fk.groupby("basin").adm2.agg(lambda s: s.mode().iloc[0])
        names = {int(sb): f"sous-bassin n° {sb} ({dn.get(d, d)})" for sb, d in dist.items()}
    t = aggregate(fk, wb, names)
    if args.recharge == "t2c":
        sfx = "bassins" if key == "basin" else "sousbassins"
        t.round(3).to_csv(cdir / "external" / f"nappes_{sfx}_t2c.csv", index=False)
        print(f"Atlas T2c : {len(t)} unités ; bilan élevé {int((t.classe_bilan == 'élevé').sum())}")
        return
    if key == "basin":
        (ROOT / "validation" / "atlas_bassins.md").write_text(report(t), encoding="utf-8")
        t.round(3).to_csv(cdir / "external" / "nappes_bassins.csv", index=False)
    else:
        (ROOT / "validation" / "atlas_sousbassins.md").write_text(report_sub(t), encoding="utf-8")
        t.round(3).to_csv(cdir / "external" / "nappes_sousbassins.csv", index=False)
    print(f"Atlas : {len(t)} bassins ; fiabilité mesurée {int((t.fiabilite == 'mesurée').sum())}")


if __name__ == "__main__":
    main()
