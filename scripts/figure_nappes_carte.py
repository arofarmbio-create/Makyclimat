"""Figure de la carte nationale du niveau statique (version 1) : deux panneaux SVG sans dépendance graphique.

Gauche : profondeur estimée par fokontany (une teinte, du clair au foncé). Droite : fiabilité, selon la distance au
forage d'apprentissage le plus proche, et en gris foncé les fokontany en extrapolation (terrain jamais vu par les forages).
Contours des régions : docs/data/<pays>/geo/adm1.geojson. Entrée : data/<pays>/external/nappes_carte.csv.
Sortie : validation/figures/nappes_carte_v2.svg.
Usage : python scripts/figure_nappes_carte.py --country mdg
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from common import ROOT, country_data_dir, read_units

W, H, PAD, GAP = 420, 640, 30, 40
BOX = (43.0, -25.8, 50.7, -11.8)                      # lon min, lat min, lon max, lat max
DEPTH_BINS = [(0, 3, "< 3 m"), (3, 5, "3-5 m"), (5, 7, "5-7 m"), (7, 10, "7-10 m"), (10, 1e9, "> 10 m")]
BLUES = ["#d6e6f4", "#a6c8e4", "#6aa3cf", "#3274b0", "#0f4680"]
REL = [("0-25 km", "#fde0c5"), ("25-100 km", "#f4a259"), ("plus de 100 km", "#c0571b"), ("extrapolation", "#3a3a3a")]


def xy(lon, lat, x0):
    sx = (W - 2 * PAD) / (BOX[2] - BOX[0])
    sy = (H - 2 * PAD) / (BOX[3] - BOX[1])
    s = min(sx, sy)
    return x0 + PAD + (np.asarray(lon) - BOX[0]) * s, PAD + (BOX[3] - np.asarray(lat)) * s


def rings(geom):
    if geom["type"] == "Polygon":
        return geom["coordinates"]
    return [r for poly in geom["coordinates"] for r in poly]


def depth_color(v):
    for (lo, hi, _), c in zip(DEPTH_BINS, BLUES):
        if lo <= v < hi:
            return c
    return "#cccccc"


def rel_color(dist, extra):
    if extra >= 0.5:
        return REL[3][1]
    return REL[0][1] if dist < 25 else REL[1][1] if dist < 100 else REL[2][1]


def svg(fk: pd.DataFrame, regions: list) -> str:
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{2 * W + GAP}" height="{H + 150}" font-family="Arial, sans-serif">',
           '<rect width="100%" height="100%" fill="#ffffff"/>']
    for k, (title, colfn) in enumerate((("Profondeur estimée du niveau statique", lambda r: depth_color(r.niveau_statique_m)),
                                        ("Fiabilité : distance au forage connu le plus proche",
                                         lambda r: rel_color(r.distance_forage_km, r.niveau_statique_extrapolation)))):
        x0 = k * (W + GAP)
        out.append(f'<text x="{x0 + PAD}" y="18" font-size="14" fill="#1a1a1a" font-weight="bold">{title}</text>')
        X, Y = xy(fk.lon, fk.lat, x0)
        for x, y, r in zip(X, Y, fk.itertuples()):
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.3" fill="{colfn(r)}"/>')
        for g in regions:
            for ring in rings(g):
                a = np.array(ring)
                px, py = xy(a[:, 0], a[:, 1], x0)
                pts = " ".join(f"{u:.1f},{v:.1f}" for u, v in zip(px[::3], py[::3]))
                out.append(f'<polygon points="{pts}" fill="none" stroke="#555555" stroke-width="0.6"/>')
    ly = H + 10
    items = [(c, lab) for (_, _, lab), c in zip(DEPTH_BINS, BLUES)]
    for i, (c, lab) in enumerate(items):
        out.append(f'<rect x="{PAD + i * 75}" y="{ly}" width="12" height="12" fill="{c}"/><text x="{PAD + i * 75 + 16}" y="{ly + 10}" font-size="11" fill="#333">{lab}</text>')
    labs = ["moins de 25 km", "25 à 100 km", "plus de 100 km", "extrapolation : terrain jamais vu"]
    for i, ((_, c), lab) in enumerate(zip(REL, labs)):
        yy = ly + (i // 2) * 18
        xx = W + GAP + PAD + (i % 2) * 190
        out.append(f'<rect x="{xx}" y="{yy}" width="12" height="12" fill="{c}"/><text x="{xx + 16}" y="{yy + 10}" font-size="11" fill="#333">{lab}</text>')
    notes = ["Carte version 2 (03/11/2026, 1 385 forages MGMERL) : approximation. Modèle hybride (carte mondiale de Fan et al. 2017 corrigée sur 1 385 forages MGMERL).",
             "Erreur médiane mesurée hors des régions d'apprentissage : 2,1 m près des forages, 2,5 à 3,1 m au-delà de 25 km.",
             "En gris foncé, l'erreur n'est pas connue : le terrain (altitude, relief, pluie, socle) sort de ce que les forages ont vu.",
             "Sources : MGMERL, Fan et al. 2017, Copernicus GLO-90, CHIRPS, SoilGrids, GLiM, GLHYMPS. MakyClimat."]
    for i, n in enumerate(notes):
        out.append(f'<text x="{PAD}" y="{H + 60 + i * 16}" font-size="11" fill="#444">{n}</text>')
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    c = pd.read_csv(country_data_dir(args.country) / "external" / "nappes_carte.csv", dtype={"pcode": str})
    fk = c.pivot_table(index="pcode", columns="indicateur", values="valeur").reset_index()
    u = read_units(args.country)
    fk = fk.merge(u[u.level == 4][["pcode", "lon", "lat"]], on="pcode")
    gj = json.loads((ROOT / "docs" / "data" / args.country / "geo" / "adm1.geojson").read_text(encoding="utf-8"))
    out = ROOT / "validation" / "figures"
    out.mkdir(exist_ok=True)
    (out / "nappes_carte_v2.svg").write_text(svg(fk, [f["geometry"] for f in gj["features"]]), encoding="utf-8")
    print(f"figure : validation/figures/nappes_carte_v2.svg ({len(fk)} fokontany)")


if __name__ == "__main__":
    main()
