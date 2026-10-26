"""Éboulements documentés (NASA COOLR, rapports pour Madagascar) : la pluie du jour était-elle exceptionnelle au fokontany le plus proche ?

Pour chaque rapport : cumul de pluie CHIRPS sur 3 jours (jour de l'événement et 2 jours avant) au fokontany le plus proche, comparé aux maxima annuels
sur 3 jours de 2006-2020 (période de retour locale), et pente moyenne du fokontany. Test descriptif : 8 rapports seulement, localisation à 1-50 km près.
Usage : python scripts/validate_landslides.py --country mdg
"""
import argparse
import datetime as dt

import numpy as np
import pandas as pd

from common import DATA_DIR, grid_dir, load_config, read_units

VAL = DATA_DIR.parent / "validation"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    a = ap.parse_args()
    from chirps_daily import leaf_series, roll3_max
    from scipy.spatial import cKDTree
    d = pd.read_csv(VAL / "coolr_rapports_madagascar.csv")
    d["date"] = pd.to_datetime(d.event_date, unit="ms").dt.date
    # rapport de 2009 « Mananjary, côte sud-est » : coordonnées du catalogue (-18,53 ; 47,32) incompatibles avec la côte sud-est ; un fokontany
    # « Manajary » existe aussi à Antananarivo (près de Mahamasina) : lieu incertain, écarté du test.
    d = d[~((d.event_date == d.event_date.iloc[0]) & d.location_description.str.contains("southeastern coast"))] if d.location_description.str.contains("southeastern coast").any() else d
    units = read_units(a.country)
    leaves = units[units.level == 4].reset_index(drop=True)
    bbox = load_config(a.country)["map"]["bbox"]
    z = np.load(grid_dir(a.country) / "rx3_annual.npz", allow_pickle=True)
    annual = z["rx3"]
    assert (z["codes"].astype(str) == leaves.pcode.values).all()
    hy = pd.read_csv(DATA_DIR / a.country / "external" / "hydro.csv")
    slope = hy[hy.indicateur == "slope_mean_pct"].set_index("pcode")["valeur"] if "indicateur" in hy else None
    tree = cKDTree(np.c_[leaves.lon.values, leaves.lat.values])
    rows, sampler = [], None
    for _, r in d.iterrows():
        _, i = tree.query([r.longitude, r.latitude])
        days = [r.date - dt.timedelta(days=k) for k in (2, 1, 0)]
        try:
            v, sampler = leaf_series(days, bbox, leaves.lon.values[[i]], leaves.lat.values[[i]], None)
            rx = float(roll3_max(v)[0])
        except Exception as ex:  # noqa: BLE001
            print("pluie indisponible", r.date, ex)
            rx = np.nan
        N = annual.shape[0]
        rp = (N + 1) / (1 + (annual[:, i] >= rx).sum()) if np.isfinite(rx) else np.nan
        pc = leaves.pcode[i]
        rows.append({"date": r.date, "lieu": r.location_description, "declencheur": r.landslide_trigger, "morts": r.fatality_count,
                     "precision": r.location_accuracy, "fokontany": pc, "pluie_3j_mm": round(rx, 0), "mediane_maxima_annuels_mm": round(float(np.median(annual[:, i])), 0),
                     "periode_retour_ans": round(float(rp), 1) if np.isfinite(rp) else None,
                     "pente_moy_pct": float(slope.get(pc, np.nan)) if slope is not None else None})
    out = pd.DataFrame(rows)
    out.to_csv(VAL / "eboulements_pluie.csv", index=False)
    print(out.to_string())


if __name__ == "__main__":
    main()
