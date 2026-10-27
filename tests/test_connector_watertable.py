"""Tests du connecteur profondeur de nappe (mock complet : un GeoTIFF fabriqué en mémoire, aucun appel réseau)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from connector_watertable import compute, sample


def make_fake_geotiff(bytes_out=True):
    import rasterio
    from affine import Affine
    # grille 10x10, résolution 1°, coin nord-ouest à (40, -10) ; valeur = colonne (profondeur croissante vers l'est)
    arr = np.tile(np.arange(10, dtype="float64"), (10, 1))
    transform = Affine(1.0, 0, 40.0, 0, -1.0, -10.0)
    mem = rasterio.io.MemoryFile()
    with mem.open(driver="GTiff", height=10, width=10, count=1, dtype="float64", crs="EPSG:4326", transform=transform, nodata=-9999.0) as dst:
        dst.write(arr, 1)
    return mem.read() if bytes_out else mem


def test_sample_reads_expected_values():
    tiff = make_fake_geotiff()
    # point proche de la colonne 2 (lon ~42.5) et de la colonne 8 (lon ~48.5)
    vals = sample(tiff, lons=[42.5, 48.5], lats=[-15.0, -15.0])
    assert vals[0] < vals[1]   # profondeur croissante vers l'est, cohérent avec la grille fabriquée


def test_compute_drops_nan_rows():
    import rasterio
    from affine import Affine
    arr = np.full((5, 5), -9999.0)
    arr[2, 2] = 7.5
    transform = Affine(1.0, 0, 40.0, 0, -1.0, -10.0)
    mem = rasterio.io.MemoryFile()
    with mem.open(driver="GTiff", height=5, width=5, count=1, dtype="float64", crs="EPSG:4326", transform=transform, nodata=-9999.0) as dst:
        dst.write(arr, 1)
    tiff = mem.read()
    leaves = pd.DataFrame({"pcode": ["A", "B"], "lon": [42.5, 43.5], "lat": [-12.5, -11.5]})
    out = compute(tiff, leaves)
    assert set(out.pcode) <= {"A", "B"}
    assert (out.valeur >= 0).all()


if __name__ == "__main__":
    test_sample_reads_expected_values()
    test_compute_drops_nan_rows()
    print("OK : tests connector_watertable")
