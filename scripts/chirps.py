"""Lecture des fichiers CHIRPS (pluie satellitaire gratuite, CHC/UCSB) recadrés sur le pays."""
from __future__ import annotations

import calendar
import gzip
import shutil
import tempfile
from pathlib import Path

import numpy as np

from common import download


def read_crop(tif_path: Path, bbox: list[float]):
    """Lit un GeoTIFF CHIRPS et retourne (tableau mm [NaN = pas de donnée], lon0, lat0, res)."""
    import rasterio
    from rasterio.windows import from_bounds

    with rasterio.open(tif_path) as src:
        win = from_bounds(*bbox, transform=src.transform).round_offsets().round_lengths()
        arr = src.read(1, window=win).astype("float32")
        t = src.window_transform(win)
        nodata = src.nodata if src.nodata is not None else -9999.0
    arr[(arr == nodata) | (arr < 0)] = np.nan
    return arr, float(t.c), float(t.f), float(t.a)


def fetch_array(url: str, bbox: list[float]):
    """Télécharge un .tif.gz CHIRPS et le recadre. Retourne None si le fichier n'existe pas (404)."""
    with tempfile.TemporaryDirectory(prefix="chirps_") as tmp:
        gz = Path(tmp) / "f.tif.gz"
        if not download(url, gz):
            return None
        tif = Path(tmp) / "f.tif"
        with gzip.open(gz, "rb") as fi, open(tif, "wb") as fo:
            shutil.copyfileobj(fi, fo)
        return read_crop(tif, bbox)


def month_fraction_covered(year: int, month: int, dekads_done: int) -> float:
    days = calendar.monthrange(year, month)[1]
    elapsed = days if dekads_done >= 3 else 10 * dekads_done
    return elapsed / days


def season_months(today, start_month: int, end_month: int) -> list[tuple[int, int]]:
    """Liste (année, mois) de la saison en cours, du début jusqu'au mois courant (ou la fin de saison)."""
    if today.month >= start_month:
        y0 = today.year
    else:
        y0 = today.year - 1
    months, y, m = [], y0, start_month
    while True:
        months.append((y, m))
        if (y, m) == (today.year, today.month) or m == end_month:
            break
        m += 1
        if m == 13:
            m, y = 1, y + 1
    return months
