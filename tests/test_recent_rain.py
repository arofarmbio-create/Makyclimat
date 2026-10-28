"""Teste la pluie récente par dékade (update_recent_rain.py) avec de FAUX fichiers CHIRPS (aucun accès réseau).

Usage : python tests/make_synthetic.py && python tests/test_recent_rain.py
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import update_recent_rain as R  # noqa: E402
from common import country_data_dir, grid_dir, load_config  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


cfg = load_config("demo")
x0, y0, x1, y1 = cfg["map"]["bbox"]
res = 0.05
h, w = int(round((y1 - y0) / res)), int(round((x1 - x0) / res))
lat = y1 - (np.arange(h) + 0.5) * res
lon = x0 + (np.arange(w) + 0.5) * res
south = lat < (y0 + y1) / 2                      # moitié sud : aucune pluie récente
east = lon > x1 - 1.0                            # bande est : normale quasi nulle (saison sèche)
reads = {"final": 0}


def exists(url):
    if "monthly" in url:
        return ".2026.09." in url                 # dernier mois définitif : septembre 2026
    if "prelim" in url:
        return url.endswith("2026.10.1.tif") or url.endswith("2026.10.2.tif")
    return ".2026." not in url                    # dékades définitives : seulement les années passées


def read_final(url, bbox):
    reads["final"] += 1
    y = int(url.split("chirps-v2.0.")[1][:4])
    a = np.full((h, w), 10.0 + (y - 1991), dtype="float32")      # 10 à 39 mm selon l'année
    a[:, east] = 1.0
    return a, x0, y1, res


def read_prov(url, bbox):
    a = np.full((h, w), 25.0, dtype="float32")
    a[south, :] = 0.0
    a[:, east] = 1.0
    return a, x0, y1, res


for f in grid_dir("demo").glob("dekad_ref_*.npz"):
    f.unlink()
out = R.main("demo", today=dt.date(2026, 10, 28), exists=exists, read_final=read_final, read_prov=read_prov)
check("fenêtre : octobre 1re et 2e dékades, provisoires", [(m, d, k) for _, m, d, k in out["dekads"]] == [(10, 1, "provisoire"), (10, 2, "provisoire")], str(out["dekads"]))
check("période du 1er au 20 octobre", out["period"] == {"from": "2026-10-01", "to": "2026-10-20"}, str(out["period"]))
n = (~south)[:, None] & (~east)[None, :]
# cumul 50 mm contre 2 x (10..39) = 20..78 mm, normale 49 : 15 années plus sèches sur 30 -> rang 50
check("nord : % de la normale ~102", np.allclose(out["pct"][n], 100 * 50 / 49, atol=0.5), str(np.nanmean(out["pct"][n])))
check("nord : rang centile 50", np.allclose(out["rank"][n], 50.0), str(np.nanmean(out["rank"][n])))
s = south[:, None] & (~east)[None, :]
check("sud sans pluie : 0 % et rang 0", np.allclose(out["pct"][s], 0) and np.allclose(out["rank"][s], 0))
check("bande est (normale 2 mm < seuil) : % non calculé, rang conservé",
      np.isnan(out["pct"][:, east]).all() and np.isfinite(out["rank"][:, east]).all())
ext = pd.read_csv(country_data_dir("demo") / "external" / "recent_rain.csv")
check("indicateurs écrits par fokontany et par zone", set(ext.indicateur) >= {"pluie_recente_mm", "pluie_recente_pct", "pluie_recente_rang"} and ext.pcode.nunique() > 10)
check("régions résumées", len(out["regions"]) > 0 and all(0 <= r["rang_centile"] <= 100 for r in out["regions"]))
n_first = reads["final"]
R.main("demo", today=dt.date(2026, 10, 28), exists=exists, read_final=read_final, read_prov=read_prov)
check("référence mise en cache : aucune relecture au 2e passage", reads["final"] == n_first, f"{n_first} puis {reads['final']}")
none = R.main("demo", today=dt.date(2026, 10, 28), exists=lambda u: False, read_final=read_final, read_prov=read_prov)
check("aucun mois définitif trouvé : rien de calculé, pas d'erreur", none is None)

print(f"\n{FAILS} ÉCHEC(S)" if FAILS else "\nTous les tests passent")
sys.exit(1 if FAILS else 0)
