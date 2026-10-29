"""Pluie CHIRPS journalière (0,05°, CHC/UCSB) échantillonnée aux fokontany."""
from __future__ import annotations

import datetime as dt
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from chirps import fetch_array

URL = "https://data.chc.ucsb.edu/products/CHIRPS/v2.0/africa_daily/tifs/p05/{y}/chirps-v2.0.{y}.{m:02d}.{d:02d}.tif.gz"


class Sampler:
    """Indices (ligne, colonne) de chaque point ; les cellules sans donnée (mer) prennent la cellule valide la plus proche."""

    def __init__(self, arr, lon0, lat0, res, lons, lats):
        from scipy import ndimage
        h, w = arr.shape
        self.rows = np.clip(np.floor((lat0 - lats) / res).astype(int), 0, h - 1)
        self.cols = np.clip(np.floor((lons - lon0) / res).astype(int), 0, w - 1)
        bad = ~np.isfinite(arr)
        if bad.any():
            _, (ri, ci) = ndimage.distance_transform_edt(bad, return_indices=True)
            self.rows, self.cols = ri[self.rows, self.cols], ci[self.rows, self.cols]

    def __call__(self, arr):
        return arr[self.rows, self.cols].astype("float32")


def fetch_day(day: dt.date, bbox):
    return fetch_array(URL.format(y=day.year, m=day.month, d=day.day), bbox)


def leaf_series(days, bbox, lons, lats, sampler=None, workers=8):
    """Matrice (jours, points) de pluie journalière (mm) ; jour absent = NaN. Retourne (matrice, sampler)."""
    with ThreadPoolExecutor(workers) as ex:
        res = list(ex.map(lambda d: fetch_day(d, bbox), days))
    out = np.full((len(days), len(lons)), np.nan, dtype="float32")
    for i, r in enumerate(res):
        if r is None:
            continue
        arr, lon0, lat0, step = r
        if sampler is None:
            sampler = Sampler(arr, lon0, lat0, step, lons, lats)
        out[i] = sampler(arr)
    return out, sampler


def roll3_max(v: np.ndarray) -> np.ndarray:
    """Cumul maximal sur 3 jours consécutifs, par point (NaN comptés comme 0 ; au moins un jour valide)."""
    z = np.nan_to_num(v, nan=0.0)
    if len(z) < 3:
        return z.sum(axis=0)
    c = np.cumsum(np.vstack([np.zeros((1, z.shape[1])), z]), axis=0)
    return (c[3:] - c[:-3]).max(axis=0)


def days_between(a: dt.date, b: dt.date):
    return [a + dt.timedelta(days=i) for i in range((b - a).days + 1)]
