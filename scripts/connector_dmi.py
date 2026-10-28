"""Indice du dipôle de l'océan Indien (DMI) mensuel, calculé à partir d'ERSST v5 (NOAA), à jour au mois précédent.

Cahier des charges §4.A (sources sur l'océan Indien et le dipôle), §5 (conditions de l'océan Indien), §8 (prédicteur).
Pourquoi : la série DMI HadISST de NOAA PSL a plusieurs mois de retard (mai 2026 au 28/10/2026). ERSST v5 est publié vers
le 3 du mois suivant, en libre accès, sans compte, et lisible zone par zone par OPeNDAP (pas besoin du fichier de 160 Mo).
Méthode (Saji et al. 1999) : anomalie mensuelle de température de surface (référence 1991-2020, par mois du calendrier),
moyennée avec un poids cos(latitude) sur la zone ouest (50-70°E, 10°S-10°N) moins la zone est (90-110°E, 10°S-0°).
Limites : ERSST est une grille de 2° (plus grossière que HadISST 1° ou OISST 0,25°) ; valeurs proches des séries officielles
mais pas identiques ; pas de retrait de tendance.
Sortie : data/enso/dmi_ersst.csv (year, month, value). Le même fichier sert à l'apprentissage et à la prévision.
Usage : python scripts/connector_dmi.py
"""
from __future__ import annotations

import datetime as dt
import re

import numpy as np
import pandas as pd
import requests

from common import DATA_DIR

BASE = "https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.ersst.v5/sst.mnmean.nc"
START = (1854, 1)                      # premier mois du fichier ERSST v5
FIRST_YEAR = 1950
BASELINE = (1991, 2020)
# indices de grille ERSST (lat = 88 - 2 i, lon = 2 j)
WEST = (39, 49, 25, 35)                # 10°N..10°S, 50..70°E
EAST = (44, 49, 45, 55)                # 0..10°S, 90..110°E


def n_times() -> int:
    t = requests.get(BASE + ".dds", timeout=120).text
    return int(re.search(r"time\[time = (\d+)\]", t).group(1))


def parse_ascii(text: str, nt: int, nla: int, nlo: int) -> np.ndarray:
    """Réponse OPeNDAP .ascii d'une grille sst[t][lat][lon] -> tableau (nt, nla, nlo), NaN pour la terre."""
    arr = np.full((nt, nla, nlo), np.nan, dtype="float64")
    for ln in text.splitlines():
        m = re.match(r"\[(\d+)\]\[(\d+)\],\s*(.*)$", ln.strip())
        if not m:
            continue
        t, la = int(m.group(1)), int(m.group(2))
        vals = [float(v) for v in m.group(3).split(",")]
        arr[t, la, :len(vals)] = [np.nan if abs(v) > 1e30 else v for v in vals]
    return arr


def box(t0: int, t1: int, b) -> np.ndarray:
    i0, i1, j0, j1 = b
    url = f"{BASE}.ascii?sst[{t0}:1:{t1}][{i0}:1:{i1}][{j0}:1:{j1}]"
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    return parse_ascii(r.text.split("sst.sst")[1] if "sst.sst" in r.text else r.text, t1 - t0 + 1, i1 - i0 + 1, j1 - j0 + 1)


def box_mean(arr: np.ndarray, b) -> np.ndarray:
    i0, i1 = b[0], b[1]
    lat = 88.0 - 2.0 * np.arange(i0, i1 + 1)
    w = np.cos(np.deg2rad(lat))[None, :, None] * np.isfinite(arr)
    return np.nansum(np.nan_to_num(arr) * w, axis=(1, 2)) / np.maximum(w.sum(axis=(1, 2)), 1e-9)


def dmi_series(west: np.ndarray, east: np.ndarray, years: np.ndarray, months: np.ndarray) -> np.ndarray:
    """Différence ouest - est des anomalies mensuelles (référence BASELINE, par mois du calendrier)."""
    out = np.full(len(years), np.nan)
    ref = (years >= BASELINE[0]) & (years <= BASELINE[1])
    for m in range(1, 13):
        k = months == m
        aw = west[k] - west[k & ref].mean()
        ae = east[k] - east[k & ref].mean()
        out[k] = aw - ae
    return out


def main() -> pd.DataFrame:
    nt = n_times()
    t0 = (FIRST_YEAR - START[0]) * 12
    t1 = nt - 1
    w, e = box_mean(box(t0, t1, WEST), WEST), box_mean(box(t0, t1, EAST), EAST)
    k = np.arange(t0, t1 + 1)
    years, months = START[0] + k // 12, 1 + k % 12
    df = pd.DataFrame({"year": years, "month": months, "value": np.round(dmi_series(w, e, years, months), 3)})
    out = DATA_DIR / "enso" / "dmi_ersst.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    last = df.iloc[-1]
    print(f"DMI (ERSST v5) : {len(df)} mois, dernier {int(last.year)}-{int(last.month):02d} = {last.value:+.2f} °C ; "
          f"juillet-septembre {int(last.year)} = {df[(df.year == last.year) & df.month.isin([7, 8, 9])].value.mean():+.2f} °C")
    return df


if __name__ == "__main__":
    main()
