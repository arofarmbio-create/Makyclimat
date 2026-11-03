"""Les données SEAM du ministère de l'Eau sont-elles utiles à MakyClimat ? (validation/protocole_seam_points_eau.md)

Q1 qualité des positions et de la population ; Q2 représentativité des relevés MGMERL parmi les forages du pays ;
Q3 hypothèse H-S1 (la part de puits autour d'un forage signale une nappe peu profonde), puis apport à l'hybride S0 si
H-S1 est soutenue ; Q4 pression par commune ; Q5 pannes de forages par district (exploratoire).
Entrée : JSON bruts de data/<pays>/seam_raw/ (lecture publique, hors dépôt). Sorties : validation/seam_utilite.md et
CSV agrégés (aucune valeur point par point de Fan).
Usage : python scripts/etude_seam.py --country mdg [--couches DOSSIER]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import audit_nappes_phase0 as A
import nappes_phase1 as P1
import validate_nappes_hc2 as H2
from common import ROOT, country_data_dir

WELLS = {"10", "11", "6"}        # puits protégé, puits non protégé, puits à pompe manuelle (PPMH)
BORES = {"16", "7"}              # forage, forage à pompe manuelle (FPMH)
SPRINGS = {"12", "14"}
RADII_KM, MAIN_RADIUS, EXCL_KM, MIN_WORKS = (2.0, 5.0, 10.0), 5.0, 0.2, 5
TERRAIN = ["altitude_m", "hand", "pente", "pluie_mm", "socle_m"]
NATIONAL_POP_2025 = 30.3e6       # projection nationale (Nations unies, WPP 2024), ordre de grandeur pour Q4
BBOX = (43.0, -26.0, 51.0, -11.5)


# ---------------- lecture ----------------
def load_points(raw: Path) -> pd.DataFrame:
    res = json.loads((raw / "resume_pdo.json").read_text(encoding="utf-8"))
    rows = []
    for f in sorted(raw.glob("pdo_region_*.json")):
        rows += json.loads(f.read_text(encoding="utf-8"))["points"]
    d = pd.DataFrame(rows, columns=["id", "lat", "lon", "r", "d", "c", "l", "type", "etat"]).drop_duplicates("id")
    d["region"] = [res["regions"][i] for i in d.r]
    d["district"] = [res["districts"][i] for i in d.d]
    d["commune"] = [res["communes"][i] for i in d.c]
    d["type"], d["etat"] = d["type"].astype(str), d["etat"].astype(str)
    return d.drop(columns=["r", "d", "c", "l"])


def load_communes(raw: Path) -> pd.DataFrame:
    """Par commune : population 2025, bénéficiaires 2026, ouvrages d'eau souterraine (tous, fonctionnels)."""
    t = json.loads((raw / "tableau_pdo.json").read_text(encoding="utf-8"))
    ev = pd.DataFrame(t["evolution"]["lignes"], columns=["r", "d", "c", "annee", "beneficiaires", "population"])
    pop = ev[ev.annee == 2025].groupby(["r", "d", "c"]).population.max()
    ben = ev[ev.annee == 2026].groupby(["r", "d", "c"]).beneficiaires.max()
    li = pd.DataFrame(t["lignes"], columns=["r", "d", "c", "type", "etat", "n", "x", "la0", "la1", "lo0", "lo1"])
    li["type"], li["etat"] = li["type"].astype(str), li["etat"].astype(str)
    gw = li[li["type"].isin(WELLS | BORES | SPRINGS)]
    works = gw.groupby(["r", "d", "c"]).n.sum()
    ok = gw[gw.etat == "1"].groupby(["r", "d", "c"]).n.sum()
    out = pd.concat({"population": pop, "beneficiaires": ben, "ouvrages_souterrains": works, "fonctionnels": ok}, axis=1)
    out = out.reset_index()
    out["region"] = [t["regions"][i] for i in out.r]
    out["district"] = [t["districts"][i] for i in out.d]
    out["commune"] = [t["communes"][i] for i in out.c]
    return out.drop(columns=["r", "d", "c"])


# ---------------- Q1 ----------------
def quality(pts: pd.DataFrame) -> dict:
    gw = pts[pts["type"].isin(WELLS | BORES)]
    valid = gw.lat.between(BBOX[1], BBOX[3]) & gw.lon.between(BBOX[0], BBOX[2])
    dup = gw.duplicated(["lat", "lon"], keep=False)
    rounded = (np.round(gw.lat, 3) == gw.lat) & (np.round(gw.lon, 3) == gw.lon)
    return {"ouvrages": len(gw), "positions_valides": float(valid.mean()), "doublons": float(dup.mean()),
            "arrondis_1e-3": float(rounded.mean())}


# ---------------- Q2 ----------------
def representativeness(mg: pd.DataFrame, seam: pd.DataFrame, cols=TERRAIN) -> pd.DataFrame:
    """Différence moyenne standardisée et part des forages SEAM hors de l'étendue (P1-P99) des relevés."""
    rows = []
    for c in cols:
        a, b = mg[c].dropna().to_numpy(float), seam[c].dropna().to_numpy(float)
        sd = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
        lo, hi = np.percentile(a, [1, 99])
        rows.append({"variable": c, "moyenne_mgmerl": a.mean(), "moyenne_seam": b.mean(),
                     "dms": (b.mean() - a.mean()) / sd if sd > 0 else 0.0, "hors_etendue": float(((b < lo) | (b > hi)).mean())})
    return pd.DataFrame(rows)


def outside_share(mg: pd.DataFrame, seam: pd.DataFrame, cols=TERRAIN) -> np.ndarray:
    """Forage SEAM hors de l'étendue des relevés pour au moins une variable."""
    out = np.zeros(len(seam), bool)
    for c in cols:
        lo, hi = np.nanpercentile(mg[c], [1, 99])
        v = seam[c].to_numpy(float)
        out |= np.isfinite(v) & ((v < lo) | (v > hi))
    return out


def class_distance(mg: pd.DataFrame, seam: pd.DataFrame, col="glim") -> float:
    """Distance de variation totale entre les répartitions par classe (0 : identiques ; 1 : disjointes)."""
    a = mg[col].dropna().value_counts(normalize=True)
    b = seam[col].dropna().value_counts(normalize=True)
    return float(0.5 * a.sub(b, fill_value=0).abs().sum())


# ---------------- Q3 ----------------
def well_share(lat, lon, w_lat, w_lon, w_is_well, radius_km, excl_km=EXCL_KM, min_works=MIN_WORKS):
    """Part de puits parmi les ouvrages d'eau souterraine dans le rayon (anneau excl_km à radius_km) et leur nombre."""
    from sklearn.neighbors import BallTree
    tree = BallTree(np.radians(np.c_[w_lat, w_lon]), metric="haversine")
    q = np.radians(np.c_[lat, lon])
    idx, dist = tree.query_radius(q, r=radius_km / 6371.0, return_distance=True)
    share, n = np.full(len(lat), np.nan), np.zeros(len(lat), int)
    for i, (j, d) in enumerate(zip(idx, dist)):
        j = j[d * 6371.0 >= excl_km]
        n[i] = len(j)
        if len(j) >= min_works:
            share[i] = w_is_well[j].mean()
    return share, n


def hs1_test(df: pd.DataFrame, col="part_puits") -> dict:
    ok = df[col].notna()
    rho, p = stats.spearmanr(df.loc[ok, col], df.loc[ok, "mesure_m"])
    reg = {}
    for r, g in df[ok].groupby("region"):
        if len(g) >= 10 and g[col].nunique() > 1:
            reg[r] = float(stats.spearmanr(g[col], g.mesure_m)[0])
    neg = sum(v < 0 for v in reg.values())
    return {"rho": float(rho), "p": float(p), "n": int(ok.sum()), "regions": reg, "regions_negatives": neg,
            "soutenue": bool(rho < 0 and p < 0.01 and neg >= 6)}


# ---------------- Q4 ----------------
def pressure(com: pd.DataFrame) -> dict:
    pop = com.population.fillna(0)
    return {"communes": len(com), "part_population_non_nulle": float((pop > 0).mean()), "population_totale": float(pop.sum()),
            "ecart_projection": float(pop.sum() / NATIONAL_POP_2025 - 1),
            "habitants_par_ouvrage_fonctionnel_median": float((pop / com.fonctionnels).replace(np.inf, np.nan).median())}


# ---------------- Q5 ----------------
def failures(pts: pd.DataFrame) -> pd.DataFrame:
    b = pts[pts["type"].isin(BORES) & pts.etat.isin(["1", "2", "3", "4"])]
    g = b.groupby(["region", "district"]).agg(forages=("etat", "size"), en_panne=("etat", lambda s: float(s.isin(["2", "4"]).mean())))
    return g.reset_index()


def report(q1, q2, tvd, out_share, q3, q3_sens, q3b, q4, q5_rho, n_seam_bores) -> str:
    L = ["# Les données SEAM du ministère de l'Eau sont-elles utiles à MakyClimat ?", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/etude_seam.py`, selon `validation/protocole_seam_points_eau.md` "
         "(fixé avant le calcul). Source : MEAH / SEAM, lecture publique. Analyse exploratoire.", "",
         "## Q1. Qualité des positions (forages et puits)", "",
         f"{q1['ouvrages']} ouvrages ; positions valides {q1['positions_valides']:.1%} ; coordonnées partagées par plusieurs "
         f"ouvrages {q1['doublons']:.1%} ; coordonnées arrondies au millième de degré {q1['arrondis_1e-3']:.1%}. "
         f"Critère (plus de 90 % valides) : **{'atteint' if q1['positions_valides'] > 0.9 else 'non atteint'}**.", "",
         "## Q2. Représentativité des 1 000 relevés MGMERL parmi les forages du pays", "",
         f"Forages SEAM (forages et FPMH) : {n_seam_bores}.", "",
         "| Variable | Moyenne MGMERL | Moyenne SEAM | DMS | Forages SEAM hors étendue (P1-P99) |", "|---|---|---|---|---|"]
    for r in q2.itertuples():
        L.append(f"| {r.variable} | {r.moyenne_mgmerl:.1f} | {r.moyenne_seam:.1f} | {r.dms:+.2f} | {r.hors_etendue:.1%} |")
    L += ["", f"Forages SEAM hors de l'étendue des relevés pour au moins une variable : **{out_share:.1%}** (la carte y "
          "extrapole). Une DMS au-delà de 0,25 en valeur absolue signale un déséquilibre. Classes lithologiques GLiM : distance "
          f"de variation totale entre les deux répartitions {tvd:.2f} (0 : identiques, 1 : disjointes).", "",
          "## Q3. H-S1 : la part de puits autour d'un forage signale-t-elle une nappe peu profonde ?", "",
          f"Rayon {MAIN_RADIUS:g} km (ouvrages à moins de {EXCL_KM * 1000:.0f} m exclus, au moins {MIN_WORKS} ouvrages) : "
          f"ρ de Spearman = {q3['rho']:+.2f} (p = {q3['p']:.1g}, {q3['n']} forages) ; ρ négatif dans "
          f"{q3['regions_negatives']} régions sur {len(q3['regions'])}. **H-S1 {'soutenue' if q3['soutenue'] else 'non soutenue'}**.", "",
          "| Région | ρ |", "|---|---|"]
    L += [f"| {r} | {v:+.2f} |" for r, v in sorted(q3["regions"].items())]
    L += ["", "Sensibilité au rayon : " + " ; ".join(f"{k:g} km : ρ = {v['rho']:+.2f} (n = {v['n']})" for k, v in q3_sens.items()) + ".", ""]
    if q3b is not None:
        res, keep, shown = q3b
        L += ["Apport à l'hybride S0 (critères de la phase 0) :", "",
              "| Critère | S0 (m) | S0 + part de puits (m) | Écart [IC 95 %] |", "|---|---|---|---|"]
        for c, lab in (("c1", "1 : erreur moyennée par région"), ("c2", "2 : erreur à plus de 50 km")):
            r = res[c]
            L.append(f"| {lab} | {r['s0']:.2f} | {r['s1']:.2f} | {r['s1'] - r['s0']:+.2f} [{r['ecart_ic'][0]:+.2f} ; {r['ecart_ic'][1]:+.2f}] |")
        L += ["", f"Décision : variable **{'gardée' if keep else 'rejetée'}**" + (" (amélioration démontrée)." if shown else
              " (amélioration non démontrée)." if keep else "."), ""]
    else:
        L += ["Test d'apport à l'hybride non fait : H-S1 n'est pas soutenue (règle du protocole).", ""]
    L += ["## Q4. Pression sur la ressource par commune", "",
          f"{q4['communes']} communes ; population non nulle dans {q4['part_population_non_nulle']:.1%} ; total "
          f"{q4['population_totale'] / 1e6:.1f} millions (écart à la projection nationale {q4['ecart_projection']:+.1%}) ; médiane "
          f"{q4['habitants_par_ouvrage_fonctionnel_median']:.0f} habitants par ouvrage d'eau souterraine fonctionnel. "
          f"Critère (plus de 80 % non nulles, écart sous 15 %) : **"
          f"{'atteint' if q4['part_population_non_nulle'] > 0.8 and abs(q4['ecart_projection']) < 0.15 else 'non atteint'}**.", "",
          "## Q5. Pannes de forages par district (exploratoire)", "",
          f"Corrélation de Spearman, par district (au moins 20 forages), entre la part de forages en panne ou abandonnés et "
          f"la profondeur médiane mesurée des relevés MGMERL du district : {q5_rho}.", ""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--couches", default=None)
    args = ap.parse_args()
    raw = country_data_dir(args.country) / "seam_raw"
    couches = Path(args.couches) if args.couches else country_data_dir(args.country) / "nappes_mondiales"
    pts = load_points(raw)
    q1 = quality(pts)
    gw = pts[pts["type"].isin(WELLS | BORES) & pts.lat.between(BBOX[1], BBOX[3]) & pts.lon.between(BBOX[0], BBOX[2])]
    gw = gw.reset_index(drop=True)
    mg, *_ = A.load_sites(args.country, couches)
    bores = gw[gw["type"].isin(BORES)].reset_index(drop=True)
    seam_f = H2.point_features(args.country, bores[["lon", "lat"]].copy(), couches)
    q2 = representativeness(mg, seam_f)
    out_share = float(outside_share(mg, seam_f).mean())
    is_well = gw["type"].isin(WELLS).to_numpy()
    sens = {}
    for rad in RADII_KM:
        s, n = well_share(mg.lat.to_numpy(), mg.lon.to_numpy(), gw.lat.to_numpy(), gw.lon.to_numpy(), is_well, rad)
        if rad == MAIN_RADIUS:
            mg["part_puits"], mg["n_ouvrages"] = s, n
        sens[rad] = hs1_test(mg.assign(part_puits=s))
    q3 = sens[MAIN_RADIUS]
    q3b = None
    if q3["soutenue"]:
        p0 = A.s0_predictions(mg)
        p1 = A.s0_predictions(mg, hybrid=partial(H2.hybrid_predict, features=H2.FEATURES + ["part_puits", "n_ouvrages"]))
        res = P1.compare(p0, p1)
        q3b = (res, *P1.decide(res))
    q4 = pressure(load_communes(raw))
    f = failures(pts)
    mg_d = pd.DataFrame({"district": [None] * len(mg)})  # districts MGMERL : rattachés par le plus proche forage SEAM
    from sklearn.neighbors import BallTree
    tree = BallTree(np.radians(np.c_[bores.lat, bores.lon]), metric="haversine")
    j = tree.query(np.radians(np.c_[mg.lat, mg.lon]), k=1, return_distance=False)[:, 0]
    mg_d["district"] = bores.district.to_numpy()[j]
    med = mg.assign(district=mg_d.district).groupby("district").mesure_m.median()
    f = f[f.forages >= 20].merge(med.rename("niveau_median_m"), left_on="district", right_index=True)
    q5 = (f"ρ = {stats.spearmanr(f.en_panne, f.niveau_median_m)[0]:+.2f} sur {len(f)} districts" if len(f) >= 8
          else f"non calculé ({len(f)} districts seulement avec relevés et au moins 20 forages)")
    vd = ROOT / "validation"
    (vd / "seam_utilite.md").write_text(report(q1, q2, class_distance(mg, seam_f), out_share, q3, sens, q3b, q4, q5, len(bores)), encoding="utf-8")
    q2.round(3).to_csv(vd / "seam_representativite.csv", index=False)
    print("SEAM : rapport écrit dans validation/seam_utilite.md")


if __name__ == "__main__":
    main()
