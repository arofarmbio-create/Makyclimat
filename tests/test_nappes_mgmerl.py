"""Protocole M3 : contrôle qualité et indices des niveaux de nappe (scripts/validate_nappes_mgmerl.py, build_nappes_sites.py)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_nappes_mgmerl as V  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


# Série simulée : 3 ans, une mesure toutes les 4 heures, cycle saisonnier autour de -5 m
t = pd.date_range("2020-01-01", "2022-12-31 20:00", freq="4h")
doy = t.day_of_year.to_numpy()
days = (t - t[0]).days.to_numpy()
lev = -5 + 0.8 * np.sin(2 * np.pi * doy / 365) + 0.6 * np.sin(2 * np.pi * days / 500)   # cycle + variation pluriannuelle
raw = pd.DataFrame({"t": t, "level": lev.copy(), "ec": np.full(len(t), 0.7)})
raw.loc[100, "level"] = 3.0                  # règle 1 : niveau positif
raw.loc[200, "level"] = -40.0                # règle 2 : pic isolé (dans les bornes)
raw.loc[300, "ec"] = 0.0                     # règle 4
d, n = V.qc(raw)
check("règle 1 : niveau positif retiré", np.isnan(d.level[100]) and n["hors_bornes"] == 1)
check("règle 2 : pic isolé retiré", np.isnan(d.level[200]) and n["pics"] >= 1)
check("règle 4 : conductivité nulle retirée", np.isnan(d.ec[300]) and n["conductivite_rejetee"] == 1)
check("aucune coupure sur une série continue", n["coupures"] == 0 and n["hors_segment"] == 0)

# Règle 3 : capteur déplacé de 10 m pendant les 4 derniers mois -> le plus long segment (avant) est gardé
raw2 = raw.copy()
moved = raw2.t >= "2022-09-01"
raw2.loc[moved, "level"] = raw2.loc[moved, "level"] - 10
d2, n2 = V.qc(raw2)
check("règle 3 : saut durable coupé, plus long segment gardé",
      n2["coupures"] == 1 and d2.loc[moved, "level"].isna().all() and d2.loc[~moved, "level"].notna().mean() > 0.99)

# Règle 5 : mois avec moins de 10 jours de mesures écarté
raw3 = raw.copy()
raw3.loc[(raw3.t >= "2021-03-06"), "level"] = raw3.loc[(raw3.t >= "2021-03-06"), "level"]
raw3 = raw3[~((raw3.t >= "2021-03-06") & (raw3.t < "2021-04-01"))]          # mars 2021 : 5 jours seulement
m = V.monthly(V.qc(raw3)[0])
check("règle 5 : mois de moins de 10 jours écarté", pd.Period("2021-03", "M") not in m.index and len(m) == 35)

# Anomalies : le cycle saisonnier disparaît
an = V.anomalies(V.monthly(d))
check("anomalie : cycle saisonnier retiré (moyenne nulle par mois du calendrier)",
      np.allclose(an.groupby(an.index.month).mean(), 0, atol=1e-9))

# Corrélation et site : un indice qui suit l'anomalie donne r > 0 ; trop peu de paires -> NaN
ind = pd.DataFrame({"mois": [str(p) for p in an.index]})
for k in range(1, V.NMAX + 1):
    ind[f"spi{k}"] = an.to_numpy() * (1 if k == 6 else 0.2) + np.random.default_rng(k).normal(0, 0.05, len(an))
ind["recharge12_z"] = -an.to_numpy()
res = V.analyse_site("simulé", raw, ind)
check("site retenu (36 mois valides)", res["retenu"] and res["mois_valides"] == 36)
check("corrélation positive avec l'indice qui suit le niveau", res["r_spi12"] > 0.5)
check("n* retrouve la durée de cumul la mieux corrélée", res["n_etoile"] == 6)
check("indice opposé : corrélation négative", res["r_recharge12_z"] < -0.9)
r, k = V.spearman(np.arange(5.0), np.arange(5.0))
check("moins de 12 paires : pas de corrélation", np.isnan(r) and k == 5)

# Tests du signe
df = pd.DataFrame({"retenu": [True] * 10, "r_spi12": [0.5] * 9 + [-0.1], "r_recharge12_z": [0.1] * 10})
t = V.tests(df)
check("H-N1 : 9 sur 10 favorables, p < 0,05", t["H-N1"][:2] == (9, 10) and t["H-N1"][2] < 0.05)
check("H-N2 : 1 sur 10 favorable, non soutenue", t["H-N2"][:2] == (1, 10) and t["H-N2"][2] > 0.5)

# Maille du site (build_nappes_sites) : maille en mer -> maille valide la plus proche
import build_nappes_sites as B  # noqa: E402
grid = {"lon0": 43.0, "lat0": -11.5, "res": 0.05, "h": 4, "w": 4}
valid = np.zeros((4, 4), bool)
valid[2, 2] = True
valid[0, 2] = True
cells = B.site_cells([-11.52, -11.62], [43.12, 43.02], grid, valid)
check("site sur une maille valide : sa maille", cells[0] == (0, 2, 0.0))
check("site en mer : maille valide la plus proche, décalage noté", cells[1][:2] == (2, 2) and cells[1][2] > 0)

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
