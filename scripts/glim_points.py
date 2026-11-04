"""Classe lithologique GLiM (version vectorielle v1.1, Hartmann et Moosdorf 2012 ; Moosdorf et Hartmann 2015, CCGM-CGMW)
aux points demandés, pour le typage du terrain du transfert par analogues (protocole_transfert_analogues.md, reprise du
04/11/2026). Lancé sur GitHub (workflow 27) : la base (1,14 Go) n'est jamais publiée, seules les classes aux points.
Entrée : inputs/analogues/points_glim.csv (id, lat, lon). Sortie : inputs/analogues/glim_points_classes.csv
(id, litho : code complet, xx : classe de niveau 1).
Usage : python scripts/glim_points.py --gdb "LiMW_GIS 2015.gdb"
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PAD_M = 1.0


def classify(gdb: str, points: pd.DataFrame) -> pd.DataFrame:
    import pyogrio
    from pyproj import Transformer
    from shapely.geometry import Point
    layer = pyogrio.list_layers(gdb)[0][0]
    crs = pyogrio.read_info(gdb, layer=layer)["crs"]
    tr = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    out = []
    for r in points.itertuples():
        x, y = tr.transform(r.lon, r.lat)
        df = pyogrio.read_dataframe(gdb, layer=layer, bbox=(x - PAD_M, y - PAD_M, x + PAD_M, y + PAD_M), columns=["Litho"])
        hit = df[df.geometry.contains(Point(x, y))] if len(df) else df
        litho = str(hit.Litho.iloc[0]) if len(hit) else ""
        out.append({"id": r.id, "litho": litho, "xx": litho[:2]})
    return pd.DataFrame(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gdb", required=True)
    args = ap.parse_args()
    pts = pd.read_csv(ROOT / "inputs" / "analogues" / "points_glim.csv")
    res = classify(args.gdb, pts)
    res.to_csv(ROOT / "inputs" / "analogues" / "glim_points_classes.csv", index=False)
    print(f"{len(res)} points ; sans classe : {int((res.xx == '').sum())}")


if __name__ == "__main__":
    main()
