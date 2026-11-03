"""E1, section 6.3 : versions de la pluie face aux impacts (scripts/validate_e1_impacts.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_e1_impacts as I  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


# Maximum saisonnier sur 3 jours : 10 mm pendant 3 jours en janvier 2003 (saison 2002) ; rien ailleurs
dates = pd.date_range("2001-01-01", "2004-12-31", freq="D")
P = np.zeros((len(dates), 2))
k = (dates >= "2003-01-10") & (dates <= "2003-01-12")
P[k, 0] = 10.0
rx = I.rx3_seasons(dates, P, 2001, 2003)
check("rx3 : 30 mm en saison 2002, 0 ailleurs", rx.shape == (3, 2) and rx[1, 0] == 30 and rx[0, 0] == 0 and rx[1, 1] == 0)
P[dates == "2003-12-25", 0] = 40.0
check("rx3 : décembre compté dans la saison commencée en novembre", I.rx3_seasons(dates, P, 2003, 2003)[0, 0] >= 40)

# Pluie mensuelle par région : moyenne des mailles ; mois incomplet -> manquant
P2 = np.ones((len(dates), 3))
P2[:, 2] = 3.0
P2[5, 0] = np.nan                                # 6 janvier 2001 manquant pour la maille 0
M = I.monthly_by_region(dates, P2, np.array(["A", "A", "B"], dtype=object))
check("mois complet : 31 mm en mars 2001 (A)", M.loc["2001-03", "A"] == 31.0)
check("janvier 2001 de A : moyenne des seules mailles complètes", M.loc["2001-01", "A"] == 31.0)
check("région B : 93 mm en janvier", M.loc["2001-01", "B"] == 93.0)

# SPI : la région asséchée de 2019 à 2023 est la plus sèche
rng = np.random.default_rng(0)
idx = pd.period_range("1990-01", "2025-12", freq="M").strftime("%Y-%m")
M = pd.DataFrame(rng.gamma(2.0, 50.0, (len(idx), 4)), index=idx, columns=["Androy", "Anosy", "Atsimo Andrefana", "Diana"])
M.loc["2019-07":"2023-06", "Androy"] *= 0.1
r = I.drought_ranks(M, 12)
check("Androy : rang 1 et SPI-12 très négatif", r["Androy"][1] == 1 and r["Androy"][0] < -2)

# Versions : B moyenne simple ; C = CHIRPS si tout le poids est sur CHIRPS
d = pd.date_range("2001-01-01", "2016-12-31", freq="D")
raw = {s: rng.gamma(1.0, 5.0, (len(d), 2)) for s in ("chirps", "imerg", "era5")}
w = np.array([[1.0, 1.0], [0.0, 0.0], [0.0, 0.0]])
V = I.daily_versions(d, raw, w)
check("B = moyenne simple", np.allclose(V["B"], (raw["chirps"] + raw["imerg"] + raw["era5"]) / 3))
check("C = CHIRPS quand son poids vaut 1", np.allclose(V["C"], raw["chirps"]))

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
