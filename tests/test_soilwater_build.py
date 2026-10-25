"""Bout en bout du bilan hydrique sur le pays simulé, avec lecteurs de données simulés (pas de réseau)."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_soilwater as B  # noqa: E402
import soilwater_core as C  # noqa: E402
from common import country_data_dir, country_docs_dir, grid_dir, load_grid  # noqa: E402


def test_build():
    cl = load_grid(grid_dir("demo") / "clim_monthly.npz")
    clim = cl["clim"]
    rng = np.random.default_rng(3)

    def soil(var, layer, grid):
        h, w = grid["h"], grid["w"]
        lat = grid["lat0"] - (np.arange(h) + 0.5) * grid["res"]
        base = {"clay": 250 + 12 * (lat + 20), "sand": 450 - 10 * (lat + 20), "soc": 150 + 0 * lat}[var]
        return np.repeat(base[:, None], w, axis=1) + rng.normal(0, 5, (h, w))

    def landcover(grid):
        h, w = grid["h"], grid["w"]
        f = rng.dirichlet(np.ones(len(C.LC_CLASSES)), size=(h, w)).transpose(2, 0, 1).astype("float32")
        return f

    def et0(lons, lats, cache, max_batches):
        return {f"{lo:.2f},{la:.2f}": [90, 85, 80, 70, 60, 50, 55, 70, 85, 100, 110, 100] for lo, la in zip(lons, lats)}

    def chirps(y, m, cfg):
        return np.nan_to_num(clim[m - 1]) * rng.gamma(8.0, 1 / 8.0, size=clim.shape[1:]).astype("float32") + np.where(np.isnan(clim[m - 1]), np.nan, 0)

    out = B.main("demo", readers={"soil": soil, "landcover": landcover, "et0": et0, "chirps": chirps}, max_et0_batches=1)
    assert out is not None, json.dumps(B.STATUS, ensure_ascii=False)
    rel = out["rel"]
    assert np.nanmin(rel) >= -1e-9 and np.nanmax(rel) <= 1 + 1e-9, "stock relatif hors [0, 1]"
    sz = out["sm_z"]
    assert abs(np.nanmean(sz)) < 0.2 and 0.7 < np.nanstd(sz) < 1.2, (np.nanmean(sz), np.nanstd(sz))
    ext = out["ext"]
    assert {"sm_rel_pct", "sm_z", "recharge12_mm", "recharge12_z", "whc_mm", "cn2"} <= set(ext.indicateur)
    assert ext[ext.indicateur == "sm_rel_pct"].valeur.between(0, 100).all()
    assert ext[ext.indicateur == "cn2"].valeur.between(30, 100).all()
    d = country_docs_dir("demo") / "soilwater"
    S = json.loads((d / "series.json").read_text())
    assert len(S["months"]) == 36 and len(S["u"]) > 5
    u0 = next(iter(S["u"].values()))
    assert len(u0["sm"]) == 36 and len(u0["n"]) == 12
    st = json.loads((d / "status.json").read_text())
    assert all(v["ok"] for v in st["steps"].values()), st
    assert (country_data_dir("demo") / "external" / "soilwater.csv").exists()
    print("test_soilwater_build OK", st["summary"])


if __name__ == "__main__":
    test_build()
