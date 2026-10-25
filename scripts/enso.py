"""ENSO (El Niño / La Niña) : indice ONI de la NOAA et classement des saisons.

ONI = anomalie de température de surface de la mer (région Niño 3.4), moyenne glissante sur 3 mois.
Le trimestre est repéré par son mois central (DJF = janvier, ..., NDJ = décembre) et par l'année de ce mois.
Classement simple d'une saison (moyenne de l'ONI sur ses mois) : El Niño si >= +0,5, La Niña si <= -0,5, sinon neutre.
La définition officielle exige 5 trimestres consécutifs : cette version simplifiée est à raffiner pour la thèse.
"""
from __future__ import annotations

import re

import pandas as pd

SEAS = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
CENTER = {s: i + 1 for i, s in enumerate(SEAS)}
THRESHOLD = 0.5
PHASE_LABEL = {"E": "El Niño", "L": "La Niña", "N": "neutre"}


def parse_cpc(text: str) -> pd.DataFrame:
    """Format CPC : lignes « SEAS YR TOTAL ANOM »."""
    rows = []
    for line in text.splitlines():
        p = line.split()
        if len(p) >= 4 and p[0] in CENTER and re.fullmatch(r"\d{4}", p[1]):
            rows.append((int(p[1]), CENTER[p[0]], p[0], float(p[3])))
    return pd.DataFrame(rows, columns=["year", "center_month", "season", "oni"])


def parse_psl(text: str) -> pd.DataFrame:
    """Format PSL : une ligne par année, 12 trimestres (DJF à NDJ), -99.9 = manquant."""
    rows = []
    for line in text.splitlines():
        p = line.split()
        if len(p) == 13 and re.fullmatch(r"\d{4}", p[0]):
            for i, v in enumerate(p[1:]):
                x = float(v)
                if x > -90:
                    rows.append((int(p[0]), i + 1, SEAS[i], x))
    return pd.DataFrame(rows, columns=["year", "center_month", "season", "oni"])


def season_months(end_year: int, start_m: int, end_m: int) -> list[tuple[int, int]]:
    """Mois (année, mois) de la saison qui se termine en `end_year`."""
    y = end_year - 1 if start_m > end_m else end_year
    out, m = [], start_m
    while True:
        out.append((y, m))
        if m == end_m:
            return out
        m += 1
        if m == 13:
            m, y = 1, y + 1


def season_oni(oni: pd.DataFrame, end_year: int, start_m: int, end_m: int, partial: bool = False) -> float:
    """Moyenne de l'ONI centré sur les mois de la saison (NaN si des mois manquent, sauf partial)."""
    idx = {(r.year, r.center_month): r.oni for r in oni.itertuples()}
    vals = [idx.get(ym) for ym in season_months(end_year, start_m, end_m)]
    got = [v for v in vals if v is not None]
    if not got or (len(got) < len(vals) and not partial):
        return float("nan")
    return sum(got) / len(got)


def phase_of(value: float) -> str:
    if value != value:
        return "?"
    return "E" if value >= THRESHOLD else "L" if value <= -THRESHOLD else "N"


def latest(oni: pd.DataFrame) -> dict | None:
    if oni.empty:
        return None
    r = oni.sort_values(["year", "center_month"]).iloc[-1]
    return {"oni": round(float(r.oni), 2), "season": f"{r.season} {int(r.year)}", "phase": phase_of(float(r.oni)),
            "phase_label": PHASE_LABEL.get(phase_of(float(r.oni)), "?")}
