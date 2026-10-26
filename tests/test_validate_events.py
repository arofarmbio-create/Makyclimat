"""Test de la logique de validation sur des données synthétiques (pas de réseau)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_events as V  # noqa: E402

assert abs(V.auc(np.array([3, 2, 1, 0.]), np.array([1, 1, 0, 0], bool)) - 1.0) < 1e-9
assert abs(V.auc(np.array([0, 1, 2, 3.]), np.array([1, 1, 0, 0], bool)) - 0.0) < 1e-9
assert abs(V.auc(np.array([1, 1, 1, 1.]), np.array([1, 0, 1, 0], bool)) - 0.5) < 1e-9
assert np.isnan(V.auc(np.array([1, 2.]), np.array([1, 1], bool)))

# régression logistique : sépare deux classes
rng = np.random.default_rng(0)
X = np.r_[rng.normal(2, .5, (40, 2)), rng.normal(-2, .5, (160, 2))]
y = np.r_[np.ones(40), np.zeros(160)]
m = V.train(X, y)
p = V.predict(m, X)
assert V.auc(p, y) > 0.99 and p[:40].mean() > 0.8 and p[40:].mean() < 0.2

# empreinte du vent : un système fixe avec R34 = 100 nm au NE seulement
lon0, lat0 = 47.0, -19.0
g = pd.DataFrame({"LON": [lon0, lon0], "LAT": [lat0, lat0], "kt": [70.0, 70.0]})
for k in (34, 50, 64):
    for q in V.QUADS:
        g[f"USA_R{k}_{q}"] = np.nan
g["USA_R34_NE"] = 100.0     # nœuds marins -> 185 km
g["USA_R64_NE"] = 30.0      # 55,6 km
km = 1 / 111.0
lons = np.array([lon0 + 100 * km / np.cos(np.deg2rad(19)) * 0.7, lon0 - 100 * km, lon0 + 40 * km * 0.7, lon0 + 100 * km * 0.7])
lats = np.array([lat0 + 100 * km * 0.7, lat0 - 100 * km, lat0 + 40 * km * 0.7, lat0 + 100 * km * 0.7 + 200 * km])
cov, miss, n34 = V.footprint(g, lons, lats)
assert cov[34][0] and not cov[34][1], cov[34]         # point au NE dans le rayon, point au SW hors rayon (rayon 0 de ce quadrant)
assert cov[64][2] and not cov[64][0], cov[64]         # R64 : 55 km seulement
assert miss == 0 and n34 == 2

# modèle complet sur événements synthétiques
rows = []
for ev in ["a", "b", "c", "d", "e"]:
    for i in range(24):
        pos = i < 4
        rows.append({"evenement": ev, "region": f"R{i}", "pos": pos, "cov34": 0.8 if pos else 0.0, "cov64": 0.3 if pos else 0.0,
                     "lrp": 2.0 + rng.normal(0, .3) if pos else 0.2 + rng.normal(0, .3), "lratio": 0.5 + rng.normal(0, .1) if pos else -0.5 + rng.normal(0, .1),
                     "rx3": 120.0 if pos else 30.0})
res = V.evaluate(pd.DataFrame(rows))
g_ = res["variantes"]["vent et pluie"]["global"]
assert g_["auc"] > 0.99 and g_["pod"] == 1.0 and g_["brier"] < g_["brier_climato"], g_
assert all(e["auc_cov34"] == 1.0 for e in res["evenements"])
print("test_validate_events OK")
