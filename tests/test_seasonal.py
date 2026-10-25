"""Teste la prévision saisonnière (calculs purs + écriture) avec de FAUSSES prévisions au format Open-Meteo (aucun accès réseau).

Usage : python tests/make_synthetic.py && python tests/test_seasonal.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import connector_seasonal as CS  # noqa: E402
from common import country_data_dir, country_docs_dir, read_units  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


def fake(n, rel):
    months = ["2026-10-01", "2026-11-01", "2026-12-01", "2027-01-01", "2027-02-01", "2027-03-01"]
    norm = [50.0, 120.0, 200.0, 220.0, 190.0, 130.0]
    anom = [5.0] + [rel * v for v in norm[1:]]
    return [{"monthly": {"time": months, "precipitation_mean": [round(a + b, 2) for a, b in zip(norm, anom)], "precipitation_anomaly": [round(a, 2) for a in anom]}} for _ in range(n)]


def main() -> None:
    r, used, rows = CS.season_anomaly(**{"months": ["2026-10-01", "2026-11-01", "2026-12-01"], "mean": [55, 108, 180], "anom": [5, -12, -20]})
    check("écart de la saison par rapport à la normale du modèle (octobre exclu)", abs(r - (-32 / (120 + 200))) < 1e-9 and used == [11, 12], f"{r:.4f}")
    check("moins de deux mois de saison : pas de prévision", CS.season_anomaly(["2026-09-01", "2026-10-01", "2026-11-01"], [1, 2, 3], [0, 0, 0.5])[0] is None)
    p0 = CS.tercile_probs(0.0, 800.0, 150.0)
    check("climatologie : trois classes à un tiers", all(abs(x - 1 / 3) < 0.01 for x in p0), str([round(x, 3) for x in p0]))
    pd_ = CS.tercile_probs(-0.15, 800.0, 150.0)
    check("signal sec : p_sec > p_normal > p_humide, somme 1", pd_[0] > pd_[1] > pd_[2] and abs(sum(pd_) - 1) < 1e-9, str([round(x, 3) for x in pd_]))
    pe = CS.tercile_probs(-0.9, 800.0, 100.0)
    check("garde-fou : probabilités entre 15 % et 50 %, somme 1", min(pe) >= 0.15 - 1e-6 and max(pe) <= 0.5 + 1e-6 and abs(sum(pe) - 1) < 1e-9, str([round(x, 3) for x in pe]))
    check("garde-fou sur un signal modéré aussi", max(CS.tercile_probs(-0.15, 800.0, 150.0)) <= 0.5 + 1e-6)
    check("normale nulle : pas de probabilité", CS.tercile_probs(0.1, 0.0, 10.0) is None)
    units = read_units("demo")
    d2 = units[units.level == 2]
    out = CS.run("demo", forecasts=fake(len(d2), -0.2))
    check("toutes les zones (districts et régions) renseignées", out is not None and set(d2.pcode) <= set(out["zones"]) and set(d2.parent) <= set(out["zones"]))
    z = out["zones"][d2.pcode.iloc[0]]
    check("saison sèche prévue : écart négatif, p_sec la plus forte", z["rs"] < 0 and z["p"][0] > z["p"][2], f"écart {z['rs']} % ; p {z['p']}")
    auto = pd.read_csv(country_data_dir("demo") / "seasonal_auto.csv")
    check("fichier de probabilités lisible par compute_metrics", {"pcode", "p_sec", "p_normal", "p_humide"} <= set(auto.columns) and (abs(auto[["p_sec", "p_normal", "p_humide"]].sum(axis=1) - 1) < 0.01).all())
    ext = pd.read_csv(country_data_dir("demo") / "external" / "seasonal.csv")
    defs = {i["id"]: i for i in __import__("common").load_yaml("indicators.yml")["indicators"]}
    check("indicateurs produits définis dans la configuration", set(ext.indicateur) <= set(defs), str(set(ext.indicateur) - set(defs)))
    check("JSON publié", (country_docs_dir("demo") / "seasonal.json").exists())
    # on retire les fichiers lus par le calcul des indicateurs (la démonstration ne doit pas dépendre de ce test) ; le JSON reste pour le test de l'interface
    (country_data_dir("demo") / "seasonal_auto.csv").unlink(missing_ok=True)
    (country_data_dir("demo") / "external" / "seasonal.csv").unlink(missing_ok=True)
    if FAILS:
        print(f"\n{FAILS} ÉCHEC(S)")
        sys.exit(1)
    print("\ntest_seasonal OK")


if __name__ == "__main__":
    main()
