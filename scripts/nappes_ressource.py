"""Recharge, volume, renouvellement et risque d'épuisement de la nappe par fokontany
(validation/protocole_cadre_eaux_souterraines.md, section 5 et mise en œuvre du 03/11/2026, fixées avant le calcul).

- Recharge R : transfert T2 depuis 134 sites africains (maille la plus proche, intervalle de 80 %) ; non validée
  (H-C6), le Grand Sud est signalé.
- Épaisseur saturée b = profondeur du socle (SoilGrids) − niveau statique (carte nationale), bornée à 0.
- Volume V = 10⁶ × b × Sy (m³/km²), Sy selon le groupe d'aquifère BGS.
- Renouvellement τ = V / (10³ × R) (années).
- Prélèvements : population (WorldPop 2015 ramenée au total communal SEAM 2025) × 20 L/j ; indice d'exploitation =
  prélèvements / R, aggravé d'une classe si la conductivité voisine (moins de 5 km) dépasse 3 000 µS/cm.
Toutes les grandeurs sont des approximations publiées en fourchette.
Sorties : data/<pays>/external/nappes_ressource.csv, validation/nappes_ressource.md.
Usage : python scripts/nappes_ressource.py --country mdg [--couches DOSSIER] [--conductivite CSV] [--sortie-test]
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

import validate_nappes_hc2b as H2b
from common import ROOT, country_data_dir, read_units

SY = {"Basement": (0.02, 0.08), "Sedimentary": (0.05, 0.15), "Unconsolidated": (0.05, 0.15)}
SY_OTHER = (0.02, 0.15)
LITRES, LITRES_SENS = 20.0, (15.0, 50.0)
CLASSES = [(0.1, "faible"), (0.4, "modéré"), (np.inf, "élevé")]
TAU_CLASSES = [(10, "renouvelable (moins de 10 ans)"), (100, "lent (10 à 100 ans)"), (np.inf, "peu renouvelable (plus de 100 ans)")]
EC_LIMIT, EC_RADIUS_KM = 3000.0, 5.0
SOUTH_LAT = -23.0
SOURCE = "MakyClimat ressource en eau souterraine v1 (validation/nappes_ressource.md)"


def sy_range(groups) -> tuple[np.ndarray, np.ndarray]:
    lo = np.array([SY.get(g, SY_OTHER)[0] for g in groups])
    hi = np.array([SY.get(g, SY_OTHER)[1] for g in groups])
    return lo, hi


def saturated(socle_m, level_lo, level_hi) -> tuple[np.ndarray, np.ndarray]:
    """Épaisseur saturée basse (niveau profond) et haute (niveau proche de la surface), bornées à 0."""
    s = np.asarray(socle_m, float)
    return np.maximum(s - np.asarray(level_hi, float), 0), np.maximum(s - np.asarray(level_lo, float), 0)


def volume_mm(b, sy) -> np.ndarray:
    """Lame d'eau stockée (mm) = 10³ × b × Sy ; × 1 000 donne des m³/km²."""
    return 1e3 * np.asarray(b, float) * np.asarray(sy, float)


def renewal_years(v_mm, r_mm) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(np.asarray(r_mm, float) > 0, np.asarray(v_mm, float) / np.asarray(r_mm, float), np.nan)


def withdrawals_mm(pop, area_km2, litres=LITRES) -> np.ndarray:
    """Prélèvements en mm/an : pop × L/j × 365 / (surface en m²) × 1 000."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.asarray(pop, float) * litres * 365 / 1000 / (np.asarray(area_km2, float) * 1e6) * 1000


def label(v, classes) -> np.ndarray:
    out = np.full(len(v), "", dtype=object)
    for i, x in enumerate(np.asarray(v, float)):
        if np.isfinite(x):
            out[i] = next(lab for lim, lab in classes if x < lim)
    return out


def worsen(cls: np.ndarray, salty: np.ndarray) -> np.ndarray:
    order = [lab for _, lab in CLASSES]
    return np.array([order[min(order.index(c) + 1, len(order) - 1)] if c and s else c for c, s in zip(cls, salty)], dtype=object)


def norm(x) -> str:
    x = unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]", "", x)


def commune_factor(units: pd.DataFrame, seam: pd.DataFrame) -> tuple[pd.Series, float]:
    """Rapport population SEAM 2025 / WorldPop 2015 par commune (pcode adm3), appariement par noms région-district-commune.
    Retourne (facteur par pcode de commune, part des communes appariées)."""
    names = dict(zip(units.pcode, units.name))
    fk = units[units.level == 4]
    wp = fk.groupby("adm3")["pop"].sum()
    com = units[units.level == 3].set_index("pcode")
    key = {p: (norm(names.get(r.adm1)), norm(names.get(r.adm2)), norm(r["name"])) for p, r in com.iterrows()}
    s = seam.assign(k=[(norm(a), norm(b), norm(c)) for a, b, c in zip(seam.region, seam.district, seam.commune)])
    s = s[s.population > 0].groupby("k").population.sum()
    fac = pd.Series({p: (s[k] / wp[p]) if k in s.index and wp.get(p, 0) > 0 else 1.0 for p, k in key.items()})
    matched = float(np.mean([k in s.index for k in key.values()])) if key else 0.0
    return fac, matched


def nearest_values(lat, lon, plat, plon, values, radius_km) -> np.ndarray:
    d = H2b.nearest_km(np.asarray(lat), np.asarray(lon), np.asarray(plat), np.asarray(plon))
    from sklearn.neighbors import BallTree
    j = BallTree(np.radians(np.c_[plat, plon]), metric="haversine").query(np.radians(np.c_[lat, lon]), k=1, return_distance=False)[:, 0]
    return np.where(d <= radius_km, np.asarray(values, float)[j], np.nan)


def socle_at(path, lons, lats) -> np.ndarray:
    import rasterio
    with rasterio.open(path) as s:
        v = np.array([x[0] for x in s.sample(zip(lons, lats))], dtype=float)
        if s.nodata is not None:
            v[v == s.nodata] = np.nan
    return v / 100.0


def compute(fk: pd.DataFrame) -> pd.DataFrame:
    """fk : niveau (médiane, bas, haut), socle_m, groupe, R (central, bas, haut), pop, surface, conductivité voisine."""
    sylo, syhi = sy_range(fk.groupe)
    blo, bhi = saturated(fk.socle_m, fk.bas80_m, fk.haut80_m)
    bmid = np.maximum(fk.socle_m - fk.niveau_m, 0)
    out = fk.copy()
    out["b_m"], out["b_bas_m"], out["b_haut_m"] = bmid, blo, bhi
    out["v_mm"] = volume_mm(bmid, (sylo + syhi) / 2)
    out["v_bas_mm"], out["v_haut_mm"] = volume_mm(blo, sylo), volume_mm(bhi, syhi)
    out["tau_ans"] = renewal_years(out.v_mm, fk.r_mm)
    out["tau_bas_ans"], out["tau_haut_ans"] = renewal_years(out.v_bas_mm, fk.r_haut_mm), renewal_years(out.v_haut_mm, fk.r_bas_mm)
    out["tau_classe"] = label(out.tau_ans, TAU_CLASSES)
    out["prelev_mm"] = withdrawals_mm(fk.pop_ajustee, fk.area_km2)
    with np.errstate(divide="ignore", invalid="ignore"):
        out["exploitation"] = out.prelev_mm / fk.r_mm
        out["exploitation_15L"] = withdrawals_mm(fk.pop_ajustee, fk.area_km2, LITRES_SENS[0]) / fk.r_mm
        out["exploitation_50L"] = withdrawals_mm(fk.pop_ajustee, fk.area_km2, LITRES_SENS[1]) / fk.r_mm
    out["risque_base"] = label(out.exploitation, CLASSES)
    out["risque"] = worsen(out.risque_base, (fk.conductivite_us > EC_LIMIT).to_numpy())
    out["grand_sud"] = fk.lat < SOUTH_LAT
    return out


def report(r: pd.DataFrame, reg: pd.DataFrame, matched: float, wtf: pd.DataFrame | None, test: bool) -> str:
    share = lambda col, lab: float((r[col] == lab).mean())
    L = ["# Ressource en eau souterraine par fokontany : recharge, volume, renouvellement, risque (version 1)", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/nappes_ressource.py`, selon "
         "`validation/protocole_cadre_eaux_souterraines.md` (section 5, mise en œuvre du 03/11/2026 fixée avant le calcul). "
         "**Toutes ces grandeurs sont des approximations** : aucune mesure de volume ni d'âge ne les valide ; la recharge "
         "(transfert T2) n'est pas confirmée à Madagascar (H-C6) et surestime aux sites suivis du Sud.", ""]
    if test:
        L += ["**Essai de code sur la carte v1 (extrait de 1 000 relevés) : résultats non publiables.**", ""]
    L += [f"Population : WorldPop 2015 ramenée aux totaux communaux SEAM 2025 ({matched:.0%} des communes appariées par leur nom ; "
          "facteur 1 ailleurs). Prélèvements : 20 L par personne et par jour (sensibilité 15 et 50 L).", "",
          f"- Renouvellement : {share('tau_classe', TAU_CLASSES[0][1]):.0%} renouvelable, {share('tau_classe', TAU_CLASSES[1][1]):.0%} lent, "
          f"{share('tau_classe', TAU_CLASSES[2][1]):.0%} peu renouvelable (valeurs centrales).",
          f"- Risque d'épuisement : {share('risque', 'faible'):.0%} faible, {share('risque', 'modéré'):.0%} modéré, {share('risque', 'élevé'):.0%} élevé "
          f"(sensibilité : élevé {float((r.exploitation_15L > 0.4).mean()):.0%} à 15 L, {float((r.exploitation_50L > 0.4).mean()):.0%} à 50 L).", "",
          "| Région | Recharge médiane (mm/an) | Stock médian (mm d'eau) | Renouvellement médian (ans) | Indice d'exploitation médian | Part en risque élevé |",
          "|---|---|---|---|---|---|"]
    for x in reg.sort_values("region").itertuples():
        L.append(f"| {x.region} | {x.r_mm:.0f} | {x.v_mm:.0f} | {x.tau_ans:.0f} | {x.exploitation:.3f} | {x.eleve:.0%} |")
    if wtf is not None and len(wtf):
        L += ["", "Contrôle local (sites MGMERL suivis, recharge par fluctuation de nappe, H-C6) :", "",
              "| Site | Fluctuation de nappe (mm/an) | Transfert T2 (mm/an) |", "|---|---|---|"]
        for x in wtf.itertuples():
            L.append(f"| {x.reference} | {x.valeur_centrale_mmpa:.0f} | {x.prediction_mediane:.0f} |")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--couches", default=None)
    ap.add_argument("--conductivite", default=None, help="CSV MGMERL de conductivité (complet)")
    ap.add_argument("--sortie-test", action="store_true", help="essai sur la carte v1 : rapport marqué non publiable, pas de CSV système")
    args = ap.parse_args()
    cdir = country_data_dir(args.country)
    couches = Path(args.couches) if args.couches else cdir / "nappes_mondiales"
    units = read_units(args.country)
    names = dict(zip(units.pcode, units.name))
    c = pd.read_csv(cdir / "external" / "nappes_carte.csv", dtype={"pcode": str})
    m = c.pivot_table(index="pcode", columns="indicateur", values="valeur")
    fk = units[units.level == 4][["pcode", "adm1", "adm3", "lon", "lat", "pop", "area_km2"]].merge(m, left_on="pcode", right_index=True)
    fk = fk.rename(columns={"niveau_statique_m": "niveau_m", "niveau_statique_bas80_m": "bas80_m", "niveau_statique_haut80_m": "haut80_m"})
    fk["socle_m"] = socle_at(couches / "socle.tif", fk.lon, fk.lat)
    rt = pd.read_csv(cdir / "nappes_mondiales" / "recharge_transferee.csv")
    from sklearn.neighbors import BallTree
    j = BallTree(np.radians(np.c_[rt.lat, rt.lon]), metric="haversine").query(np.radians(np.c_[fk.lat, fk.lon]), k=1, return_distance=False)[:, 0]
    fk["r_mm"], fk["r_bas_mm"], fk["r_haut_mm"] = rt.T2_mmpa.to_numpy()[j], rt.T2_bas_mmpa.to_numpy()[j], rt.T2_haut_mmpa.to_numpy()[j]
    fk["groupe"] = rt.Aquifer_group.fillna("").to_numpy()[j]
    import etude_seam as S
    fac, matched = commune_factor(units, S.load_communes(cdir / "seam_raw"))
    fk["pop_ajustee"] = fk["pop"] * fk.adm3.map(fac).fillna(1.0)
    fk["conductivite_us"] = np.nan
    if args.conductivite:
        ec = pd.read_csv(args.conductivite)
        xy = ec["Coordonnées GPS"].astype(str).str.split(",", expand=True)
        ec = pd.DataFrame({"lat": pd.to_numeric(xy[0], errors="coerce"), "lon": pd.to_numeric(xy[1], errors="coerce"),
                           "ec": pd.to_numeric(ec["Conductivité électrique (uS/cm)"], errors="coerce")}).dropna()
        fk["conductivite_us"] = nearest_values(fk.lat, fk.lon, ec.lat, ec.lon, ec.ec, EC_RADIUS_KM)
    r = compute(fk)
    r["region"] = r.adm1.map(names)
    reg = r.groupby("region").agg(r_mm=("r_mm", "median"), v_mm=("v_mm", "median"), tau_ans=("tau_ans", "median"),
                                  exploitation=("exploitation", "median"), eleve=("risque", lambda s: float((s == "élevé").mean()))).reset_index()
    ref = ROOT / "validation" / "transfert_recharge_hc6_references.csv"
    wtf = pd.read_csv(ref) if ref.exists() else None
    if wtf is not None:
        wtf = wtf[wtf.reference.str.startswith("Site MGMERL")]
    (ROOT / "validation" / ("nappes_ressource_essai_v1.md" if args.sortie_test else "nappes_ressource.md")).write_text(
        report(r, reg, matched, wtf, args.sortie_test), encoding="utf-8")
    if not args.sortie_test:
        cols = {"r_mm": "recharge_mm_an", "r_bas_mm": "recharge_bas80_mm_an", "r_haut_mm": "recharge_haut80_mm_an",
                "v_mm": "stock_mm", "v_bas_mm": "stock_bas_mm", "v_haut_mm": "stock_haut_mm", "tau_ans": "renouvellement_ans",
                "exploitation": "indice_exploitation"}
        rows = [pd.DataFrame({"pcode": r.pcode, "indicateur": ind, "valeur": r[col].astype(float).round(3)}) for col, ind in cols.items()]
        rows.append(pd.DataFrame({"pcode": r.pcode, "indicateur": "risque_epuisement", "valeur": r.risque}))
        out = pd.concat(rows, ignore_index=True)
        out = out[out.valeur.astype(str).ne("") & out.valeur.astype(str).ne("nan")]
        out.assign(date=dt.date.today().isoformat(), source=SOURCE).to_csv(cdir / "external" / "nappes_ressource.csv", index=False)
    print(f"Ressource : {len(r)} fokontany ; rapport dans validation/{'nappes_ressource_essai_v1.md' if args.sortie_test else 'nappes_ressource.md'}")


if __name__ == "__main__":
    main()
