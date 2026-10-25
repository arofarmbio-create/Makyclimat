"""Test de bout en bout du pipeline d'hydrologie sur un terrain simulé (pays demo), sans réseau."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_hydro as B  # noqa: E402
from common import country_data_dir, country_docs_dir  # noqa: E402


def fake_reader(lat0, lon0, res):
    """Île simulée : une crête centrale nord-sud (~1500 m) qui s'abaisse vers les côtes, avec du relief ondulé."""
    n = int(round(1 / res))
    lat = lat0 + 1 - (np.arange(n) + 0.5) * res
    lon = lon0 + (np.arange(n) + 0.5) * res
    LO, LA = np.meshgrid(lon, lat)
    if LA.max() < -25.2 or LA.min() > -12.3:
        return None
    ridge = 1500 * np.exp(-((LO - 47.0) / 1.2) ** 2) * np.clip(1 - np.abs((LA + 18.7) / 6.8) ** 3, 0, 1)
    wav = 40 * np.sin(LO * 9) * np.cos(LA * 11)
    z = ridge + wav * (ridge > 20)
    z[ridge < 15] = 0.0
    return z.astype("float32")


def test_build():
    res = 0.02
    out = B.run("demo", reader=fake_reader, res=res, hcfg={"stream_min_km2": 100, "basin_min_km2": 300, "subbasin_min_km2": 200}, bbox=[43.0, -26.0, 51.0, -11.5])
    P = out["P"]
    assert (~P["sea"]).sum() > 1000, "pas de terre"
    ext, lk = out["ext"], out["lk"]
    assert set(ext.indicateur) >= {"hand_lt5_pct", "slope_mean_pct", "elev_mean_m", "river_max_km2"}
    assert ext.valeur.notna().all()
    h = ext[ext.indicateur == "hand_lt5_pct"].valeur
    assert h.between(0, 100).all()
    assert len(out["minfo"]) >= 1
    d = country_docs_dir("demo") / "hydro"
    for f in ("rivers.geojson", "basins.geojson", "subbasins.geojson", "meta.json"):
        assert (d / f).exists() and (d / f).stat().st_size > 50, f
    assert (country_data_dir("demo") / "external" / "hydro.csv").exists()
    assert (lk.basin > 0).any()
    print("test_hydro_build OK", len(out["minfo"]), "bassins")


if __name__ == "__main__":
    test_build()
