"""Teste l'analyse climat/ENSO avec une pluie synthétique dont la tendance et l'effet ENSO sont connus.

Usage : python tests/make_synthetic.py && python tests/test_climate.py
"""
from __future__ import annotations

import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_climate_change as bcc  # noqa: E402
import common  # noqa: E402
import enso  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


def oni_val(y, m):
    return 1.5 * math.sin(2 * math.pi * (y + m / 12) / 4.0)


def test_parsers() -> None:
    cpc = "SEAS  YR   TOTAL  ANOM\n DJF 1950 24.55 -1.53\n JFM 1950 25.06 -1.34\n NDJ 1950 23.9 -0.8\n"
    df = enso.parse_cpc(cpc)
    check("ONI CPC : lignes lues, mois central", len(df) == 3 and df.center_month.tolist() == [1, 2, 12] and df.oni[0] == -1.53)
    psl = "1950 2025\n1950 -1.53 -1.34 -1.16 -1.18 -1.07 -0.85 -0.54 -0.42 -0.39 -0.44 -0.60 -0.80\n2025 -0.5 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90\n"
    d2 = enso.parse_psl(psl)
    check("ONI PSL : valeurs manquantes ignorées", len(d2) == 13 and d2.oni.iloc[0] == -1.53)
    rows = [(y, m, enso.SEAS[m - 1], 0.0) for y in range(2000, 2003) for m in range(1, 13)]
    o = pd.DataFrame(rows, columns=["year", "center_month", "season", "oni"])
    o.loc[(o.year == 2001) & (o.center_month.isin([11, 12])), "oni"] = 1.2
    o.loc[(o.year == 2002) & (o.center_month.isin([1, 2, 3, 4])), "oni"] = 1.2
    check("ONI de saison : mois centraux nov(y-1) à avr(y)", abs(enso.season_oni(o, 2002, 11, 4) - 1.2 * 6 / 6) < 1e-9)
    check("classement des phases", enso.phase_of(0.6) == "E" and enso.phase_of(-0.5) == "L" and enso.phase_of(0.2) == "N")
    check("saison incomplète -> NaN, sauf partiel", math.isnan(enso.season_oni(o, 2003, 11, 4)) and enso.season_oni(o, 2003, 11, 4, partial=True) == 0.0)


def test_analysis() -> None:
    cfg = common.load_config("demo")
    clim = common.load_grid(common.grid_dir("demo") / "clim_monthly.npz")
    h, w = clim["clim"].shape[1:]
    lon0, lat0, step = float(clim["lon0"]), float(clim["lat0"]), float(clim["res"])
    east = np.zeros((h, w), dtype=bool)
    east[:, w // 2:] = True

    def fake_fetch(url, bbox):
        import re
        y, m = map(int, re.search(r"\.(\d{4})\.(\d{2})\.tif", url).groups())
        base = 100.0 * (1 + 0.01 * (y - 2000))
        sign = np.where(east, -0.3, 0.3)
        arr = (base * (1 + sign * oni_val(y, m))).astype("float32")
        return arr, lon0, lat0, step

    rows = [(y, m, enso.SEAS[m - 1], oni_val(y, m)) for y in range(1950, 2026) for m in range(1, 13)]
    tmp = Path(tempfile.mkdtemp(prefix="fake_enso_"))
    (tmp / "enso").mkdir()
    pd.DataFrame(rows, columns=["year", "center_month", "season", "oni"]).to_csv(tmp / "enso" / "oni.csv", index=False)
    bcc.fetch_array = fake_fetch
    bcc.DATA_DIR = tmp
    sys.argv = ["build_climate_change.py", "--country", "demo"]
    bcc.main()
    g = common.load_grid(common.grid_dir("demo") / "climate_change.npz")
    e, wst = g["trend"][:, w // 2 + 2:], g["trend"][:, : w // 2 - 2]
    check("tendance positive de ~9,5 points par décennie retrouvée", 7 < np.nanmean(e) < 12, f"{np.nanmean(e):.1f}")
    check("tendance significative (p < 0,10)", np.nanmean(g["trend_p"] < 0.1) > 0.9)
    check("corrélation ENSO négative à l'est, positive à l'ouest",
          np.nanmean(g["corr"][:, w // 2 + 2:]) < -0.5 and np.nanmean(g["corr"][:, : w // 2 - 2]) > 0.5)
    check("El Niño plus sec que La Niña à l'est", np.nanmean(g["el"][:, w // 2 + 2:]) < np.nanmean(g["la"][:, w // 2 + 2:]) - 10)
    hist = json.loads((common.country_docs_dir("demo") / "history.json").read_text(encoding="utf-8"))
    check("historique : années, ONI et phases alignés", len(hist["years"]) == len(hist["oni"]) == len(hist["phases"]) >= 25)
    check("historique : phases El Niño et La Niña présentes", hist["counts"]["E"] >= 3 and hist["counts"]["L"] >= 3, str(hist["counts"]))
    units = common.read_units("demo")
    check("historique : toutes les régions et tous les districts",
          set(units[units.level.isin([1, 2])].pcode) <= set(hist["series"]))
    ext = pd.read_csv(common.country_data_dir("demo") / "external" / "climate.csv")
    check("indicateurs climat écrits pour les fokontany", set(ext.indicateur) == {
        "rain_trend_pct_decade", "rain_trend_signif_share", "enso_el_pct", "enso_la_pct", "enso_corr"} and ext.pcode.nunique() == (units.level == 4).sum())


def test_hindcast() -> None:
    import build_hindcast as bh
    rng = np.random.default_rng(5)
    Y, M, N = 40, 6, 200
    clim = np.full((M, N), 100.0)
    arr = clim[None] * (1 + rng.normal(0, 0.5, (Y, M, N)))      # mois indépendants : plus on observe, mieux on sait
    ph = np.array(["N"] * Y)
    ph[:6], ph[6:12] = "E", "L"
    r = bh.run(arr, clim, ph, np.arange(1982, 1982 + Y), 95, 100)
    o = r["origins"]
    check("hindcast : 6 points de départ", len(o) == 6 and r["n_seasons"] == Y)
    check("hindcast : sans pluie observée, aucun gain sur la climatologie", abs(o[0]["mae"] - o[0]["mae_climatology"]) < 1e-9 and abs(o[0]["brier_skill"]) < 1e-9)
    check("hindcast : l'erreur diminue quand la saison avance", all(o[i]["mae"] > o[i + 1]["mae"] for i in range(5)), str([x["mae"] for x in o]))
    check("hindcast : gain de Brier fort en fin de saison", o[5]["brier_skill"] > 0.4, str(o[5]["brier_skill"]))
    check("hindcast : couverture P10-P90 proche de 80 %", all(0.70 <= x["coverage_p10_p90"] <= 0.88 for x in o), str([x["coverage_p10_p90"] for x in o]))
    rel = o[3]["reliability"]
    check("hindcast : courbe de fiabilité cohérente (probabilité annoncée ~ fréquence observée)", len(rel) >= 2 and all(abs(b["p"] - b["freq"]) < 0.15 for b in rel), str(rel))
    same = np.repeat(arr[:1], Y, axis=0)
    r2 = bh.run(same, clim, ph, np.arange(Y), 75, 100)
    check("hindcast : saisons identiques -> erreur nulle", all(x["mae"] < 1e-9 for x in r2["origins"]))


if __name__ == "__main__":
    test_hindcast()
    test_parsers()
    test_analysis()
    print("\nTous les tests climat passent." if not FAILS else f"\n{FAILS} ÉCHEC(S)")
    sys.exit(1 if FAILS else 0)
