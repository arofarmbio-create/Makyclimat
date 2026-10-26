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

rng = np.random.default_rng(1)
rows = []
for ev in ["a", "b", "c", "d"]:
    for i in range(24):
        pos = i < 4
        w = 60 if pos else 0
        rows.append({"evenement": ev, "region": f"R{i}", "pos": pos, "wind50": w, "wind100": w, "wind150": w, "wind200": w + (30 if i == 10 else 0),
                     "rx3": (150 if pos else 20) + rng.normal(0, 5), "frac3": 0.5 if pos else 0.05})
res = V.evaluate(pd.DataFrame(rows))
assert all(abs(e["auc_rx3"] - 1.0) < 1e-9 for e in res["events"])
best = max(res["rules"], key=lambda r: r["f1"])
assert best["pod"] == 1.0 and best["f1"] > 0.9, best
assert all(r["pod"] == 1.0 for r in res["loeo"]), res["loeo"]
# une règle qui ne détecte rien : POD 0
z = [r for r in res["rules"] if r["regle"] == "pluie 3 j >= 200 mm"][0]
assert z["pod"] == 0.0
print("test_validate_events OK")
