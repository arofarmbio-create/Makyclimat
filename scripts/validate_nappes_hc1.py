"""Test H-C1 du protocole de la carte des nappes (validation/protocole_carte_nappes.md, section 6 et modification du
02/11/2026) : la profondeur de nappe de Fan et al. (2017) a-t-elle un biais face aux forages malgaches (MGMERL) ?

Test principal : Wilcoxon bilatéral sur les écarts (Fan − mesure), 5 %. Contrôle de robustesse : écart médian par
bloc de 1°, test du signe entre blocs. Analyses descriptives : position dans le relief (HAND au point), productivité
de l'aquifère (BGS, fokontany du point), corrélation de Spearman.
Seules des statistiques par classe et par bloc sont publiées (licence de Fan et al. : pas de republication).
Entrées : data/<pays>/nappes_mondiales/fan.tif (cache des Actions), inputs/mgmerl/mgmerl_niveau_statique.csv,
data/<pays>/grids/hydro.npz, data/<pays>/external/geology.csv.
Sorties : validation/nappes_hc1.md, validation/nappes_hc1_classes.csv.
Usage : python scripts/validate_nappes_hc1.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd

from common import ROOT, country_data_dir, grid_dir, load_grid

MGMERL = ROOT / "inputs" / "mgmerl" / "mgmerl_niveau_statique.csv"
BBOX = (43.0, -26.0, 51.0, -11.5)
HAND_CLASSES = [(-np.inf, 5, "fond de vallée (HAND < 5 m)"), (5, 15, "bas de versant (5-15 m)"), (15, np.inf, "versant ou plateau (> 15 m)")]


def load_points(path=MGMERL) -> pd.DataFrame:
    """Relevés MGMERL contrôlés (modification du 02/11/2026) : 0 < profondeur ≤ 200 m, à Madagascar, doublons -> plus récent."""
    d = pd.read_csv(path)
    xy = d["Coordonnées GPS"].astype(str).str.split(",", expand=True)
    out = pd.DataFrame({"id": d["ID unique"], "type": d["Type de point d'eau"],
                        "lat": pd.to_numeric(xy[0], errors="coerce"), "lon": pd.to_numeric(xy[1], errors="coerce"),
                        "mesure_m": pd.to_numeric(d["Niveau statique d'eau"], errors="coerce"),
                        "date": pd.to_datetime(d["Date du rapport"], errors="coerce", format="mixed")})
    ok = (out.mesure_m > 0) & (out.mesure_m <= 200) & out.lon.between(BBOX[0], BBOX[2]) & out.lat.between(BBOX[1], BBOX[3])
    out = out[ok].sort_values("date").drop_duplicates("id", keep="last")
    return out.reset_index(drop=True)


def fan_depth(values) -> np.ndarray:
    """Valeur du fichier Fan (négative sous la surface) -> profondeur positive ; eau au-dessus du sol -> 0 m."""
    v = np.asarray(values, dtype=float)
    return np.where(np.isfinite(v), np.maximum(-v, 0.0), np.nan)


def sample_raster(path, lons, lats) -> np.ndarray:
    import rasterio
    with rasterio.open(path) as src:
        vals = np.array([v[0] for v in src.sample(zip(lons, lats))], dtype=float)
        if src.nodata is not None:
            vals[vals == src.nodata] = np.nan
    return vals


def hand_at(country, lons, lats) -> np.ndarray:
    h = load_grid(grid_dir(country) / "hydro.npz")
    lon0, lat0, res = float(h["lon0"]), float(h["lat0"]), float(h["res"])
    hand = np.asarray(h["hand"], dtype=float)
    r = np.clip(np.floor((lat0 - np.asarray(lats)) / res).astype(int), 0, hand.shape[0] - 1)
    c = np.clip(np.floor((np.asarray(lons) - lon0) / res).astype(int), 0, hand.shape[1] - 1)
    return hand[r, c]


def hand_class(v):
    for lo, hi, name in HAND_CLASSES:
        if lo <= v < hi:
            return name
    return "inconnu"


def stats(diff: np.ndarray) -> dict:
    from scipy import stats as st
    d = diff[np.isfinite(diff)]
    if len(d) < 5:
        return {"n": len(d)}
    w = st.wilcoxon(d) if np.any(d != 0) else None
    return {"n": len(d), "ecart_median_m": float(np.median(d)), "biais_moyen_m": float(np.mean(d)),
            "erreur_absolue_mediane_m": float(np.median(np.abs(d))), "p_wilcoxon": float(w.pvalue) if w else 1.0}


def block_test(df: pd.DataFrame) -> dict:
    """Écart médian par bloc de 1° ; test du signe (bilatéral) entre blocs."""
    from scipy import stats as st
    b = df.assign(bloc=np.floor(df.lat).astype(int).astype(str) + "/" + np.floor(df.lon).astype(int).astype(str))
    med = b.groupby("bloc").ecart_m.median()
    pos, n = int((med > 0).sum()), int((med != 0).sum())
    p = float(st.binomtest(pos, n, 0.5).pvalue) if n else float("nan")
    return {"blocs": int(len(med)), "blocs_fan_plus_profond": pos, "blocs_non_nuls": n, "p_signe": p, "medianes": med}


def analyse(df: pd.DataFrame) -> dict:
    from scipy import stats as st
    df = df.assign(ecart_m=df.fan_m - df.mesure_m)
    ok = df[np.isfinite(df.ecart_m)]
    res = {"global": stats(ok.ecart_m.to_numpy()), "blocs": block_test(ok),
           "spearman": float(st.spearmanr(ok.fan_m, ok.mesure_m).correlation) if len(ok) > 5 else np.nan,
           "mediane_mesure": float(ok.mesure_m.median()), "mediane_fan": float(ok.fan_m.median())}
    rows = []
    for col in ("classe_relief", "productivite"):
        if col not in ok:
            continue
        for k, g in ok.groupby(col):
            s = stats(g.ecart_m.to_numpy())
            rows.append({"variable": col, "classe": k, "mediane_mesure_m": float(g.mesure_m.median()),
                         "mediane_fan_m": float(g.fan_m.median()), **s})
    res["classes"] = pd.DataFrame(rows)
    g, b = res["global"], res["blocs"]
    res["H-C1"] = bool(g.get("p_wilcoxon", 1) < 0.05 and b["p_signe"] < 0.05
                       and np.sign(g.get("ecart_median_m", 0)) == np.sign(b["blocs_fan_plus_profond"] - (b["blocs_non_nuls"] - b["blocs_fan_plus_profond"])))
    return res


def report(res, n_in) -> str:
    f = lambda x: "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else (f"{x:.2f}" if isinstance(x, float) else str(x))
    g, b = res["global"], res["blocs"]
    L = ["# H-C1 : la profondeur de nappe de Fan et al. face aux forages malgaches", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/validate_nappes_hc1.py`, selon `validation/protocole_carte_nappes.md` "
         "(section 6 et modification du 02/11/2026, fixées avant le calcul). Données de forage : MGMERL ; carte mondiale : "
         "Fan et al. (2017), valeurs non republiées.", "",
         f"Relevés lus : {n_in} ; gardés après contrôle et avec une valeur de Fan : {g.get('n')}.", "",
         "## Résultat", "",
         f"- Profondeur médiane mesurée : **{f(res['mediane_mesure'])} m** ; profondeur médiane de Fan aux mêmes points : "
         f"**{f(res['mediane_fan'])} m**.",
         f"- Écart médian (Fan − mesure) : {f(g.get('ecart_median_m'))} m ; biais moyen : {f(g.get('biais_moyen_m'))} m ; "
         f"erreur absolue médiane : {f(g.get('erreur_absolue_mediane_m'))} m.",
         f"- Test de Wilcoxon (principal) : p = {f(g.get('p_wilcoxon'))}.",
         f"- Contrôle par blocs de 1° : {b['blocs']} blocs ; Fan plus profond dans {b['blocs_fan_plus_profond']} sur "
         f"{b['blocs_non_nuls']} ; test du signe p = {f(b['p_signe'])}.",
         f"- Corrélation de Spearman entre Fan et la mesure : {f(res['spearman'])} (Fan classe-t-il les sites dans le bon ordre ?).",
         f"- **H-C1 (biais significatif, solide aux deux tests) : {'confirmée' if res['H-C1'] else 'non confirmée'}.**", "",
         "## Par classe (descriptif)", "",
         "| Variable | Classe | Points | Mesure médiane (m) | Fan médiane (m) | Écart médian (m) | Erreur absolue médiane (m) |",
         "|---|---|---|---|---|---|---|"]
    for r in res["classes"].itertuples():
        L.append(f"| {r.variable} | {r.classe} | {r.n} | {f(r.mediane_mesure_m)} | {f(r.mediane_fan_m)} | "
                 f"{f(getattr(r, 'ecart_median_m', np.nan))} | {f(getattr(r, 'erreur_absolue_mediane_m', np.nan))} |")
    L += ["", "Limites (protocole §7) : relevés regroupés autour des projets WASH, surtout dans le Sud ; niveau statique "
          "ponctuel (saison, pompage) ; niveau d'un forage captif possiblement au-dessus du toit de la nappe ; maille de "
          "1 km de Fan qui mélange vallée et versant."]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    pts = load_points()
    n_in = len(pd.read_csv(MGMERL))
    fan_tif = country_data_dir(args.country) / "nappes_mondiales" / "fan.tif"
    pts["fan_m"] = fan_depth(sample_raster(fan_tif, pts.lon, pts.lat))
    pts["classe_relief"] = [hand_class(v) for v in hand_at(args.country, pts.lon, pts.lat)]
    try:
        from common import locate_points
        geo = pd.read_csv(country_data_dir(args.country) / "external" / "geology.csv")
        prod = geo[geo.indicateur == "aquifer_productivity_pct"].set_index("pcode").valeur
        pc = locate_points(args.country, pts.lon.tolist(), pts.lat.tolist())
        pts["productivite"] = [f"productivité BGS {int(prod[c])} %" if c in prod.index else "inconnue" for c in pc]
    except Exception as e:  # noqa: BLE001
        print(f"productivité BGS indisponible : {e}")
    res = analyse(pts)
    vd = ROOT / "validation"
    (vd / "nappes_hc1.md").write_text(report(res, n_in), encoding="utf-8")
    res["classes"].round(3).to_csv(vd / "nappes_hc1_classes.csv", index=False)
    print(f"H-C1 : {'confirmée' if res['H-C1'] else 'non confirmée'} ; {res['global']}")


if __name__ == "__main__":
    main()
