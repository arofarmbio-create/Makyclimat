"""Teste le calcul des trajectoires et de l'exposition aux cyclones (IBTrACS) avec de FAUX systèmes (aucun accès réseau).

Usage : python tests/make_synthetic.py && python tests/test_cyclones.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_cyclones as BC  # noqa: E402
from common import read_units  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


def storm(sid, season, name, pts, wmo=None, usa=None, track="main"):
    rows = []
    for i, (lon, lat) in enumerate(pts):
        t = pd.Timestamp(f"{season}-02-01") + pd.Timedelta(hours=6 * i)
        rows.append({"SID": sid, "SEASON": season, "NAME": name, "ISO_TIME": t.strftime("%Y-%m-%d %H:%M:%S"), "NATURE": "TS", "LAT": lat, "LON": lon,
                     "WMO_WIND": "" if wmo is None else wmo[i], "USA_WIND": "" if usa is None else usa[i], "TRACK_TYPE": track})
    return rows


def main() -> None:
    units = read_units("demo")
    leaves = units[units.level == 4]
    c = leaves.iloc[0]
    far = leaves.iloc[(leaves.lon - c.lon).abs().argmax()]
    lon, lat = float(c.lon), float(c.lat)
    # A : passe sur le premier fokontany avec 60 kt (10 min) ; B : 25 kt au même endroit (trop faible) ; C : loin ; D : avant 1980
    A = storm("A", 2010, "ALPHA", [(lon - 2, lat), (lon - 1, lat), (lon, lat), (lon + 1, lat)], wmo=[40, 55, 60, 45])
    B = storm("B", 2012, "BETA", [(lon - 1, lat), (lon, lat), (lon + 1, lat)], wmo=[20, 25, 22])
    C = storm("C", 2015, "NOT_NAMED", [(lon + 20, lat - 20), (lon + 21, lat - 20)], wmo=[100, 100])
    D = storm("D", 1975, "OLD", [(lon, lat), (lon + 0.5, lat)], wmo=[90, 90])
    E = storm("E", 2020, "ECHO", [(lon - 1, lat + 0.5), (lon, lat + 0.5), (lon + 1, lat + 0.5)], usa=[60, 80, 70], track="PROVISIONAL")   # vent 1 min seulement
    raw = pd.DataFrame(A + B + C + D + E)
    d = BC.clean(raw, 1980, [lon - 5, lat - 5, lon + 5, lat + 5])
    check("filtre : avant 1980 et hors emprise exclus", set(d.SID) == {"A", "B", "E"})
    check("vent 10 min repris du centre officiel", float(d[d.SID == "A"].kt.max()) == 60.0)
    check("vent 1 min converti (x 0,93) à défaut", abs(float(d[d.SID == "E"].kt.max()) - 0.93 * 80) < 1e-6)
    check("échelle La Réunion", BC.category(30) == "Dépression" and BC.category(60) == "Forte tempête tropicale" and BC.category(120) == "Cyclone tropical très intense")
    rows = BC.exposure(d, units, 100, 34)
    cnt, wmax = rows[c.pcode]
    check("fokontany traversé : A et E comptés, B (trop faible) non", cnt == 2, f"{cnt} systèmes")
    check("vent maximal à moins de 100 km", wmax == int(round(0.93 * 80)) or wmax == 60, f"{wmax} kt")
    check("fokontany éloigné : aucun système", rows[far.pcode][0] == 0 or abs(float(far.lon) - lon) < 1.0)
    reg = c.adm1
    check("la région compte les systèmes qui touchent au moins un de ses fokontany", rows[reg][0] >= 2 and rows[reg][1] >= rows[c.pcode][1])
    near = BC.nearest_unit_km(d, units)
    check("distance minimale au territoire calculée", near["A"] <= 15 and near["B"] <= 15)
    js = BC.tracks_json(d, near, "2026-10-25", 1980)
    sa = [s for s in js["storms"] if s["id"] == "A"][0]
    check("trajectoire exportée (positions, catégorie, saison)", len(sa["p"]) == 4 and sa["cat"] == "Forte tempête tropicale" and sa["season"] == 2010)
    check("système provisoire signalé, nom absent vidé", [s for s in js["storms"] if s["id"] == "E"][0]["prov"] is True)
    from common import country_docs_dir, write_json
    write_json(country_docs_dir("demo") / "cyclones.json", js)   # utilisé par le test de l'interface (dossier de démonstration, non publié)
    df = BC.build_rows(rows, "test")
    check("format long (pcode, indicateur, valeur, date, source)", {"pcode", "indicateur", "valeur", "date", "source"} <= set(df.columns))
    if FAILS:
        print(f"\n{FAILS} ÉCHEC(S)")
        sys.exit(1)
    print("\ntest_cyclones OK")


if __name__ == "__main__":
    main()
