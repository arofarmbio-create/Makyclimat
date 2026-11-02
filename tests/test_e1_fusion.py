"""E1 : pentades, triple collocation, fusion et stations (scripts/validate_e1.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_e1 as V  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


# Pentades
d = pd.to_datetime(["2020-01-01", "2020-01-05", "2020-01-06", "2020-12-31"])
check("pentades : 1er janvier = 0, 6 janvier = 1, 31 décembre (année bissextile) = 72",
      list(V.pentad_index(pd.DatetimeIndex(d))) == [0, 0, 1, 72])
days = pd.date_range("2021-01-01", "2021-01-10", freq="D")
x = np.ones((10, 2))
x[7, 1] = np.nan
keys, month, s = V.to_pentads(days, x)
check("cumul par pentade ; pentade manquante si un jour manque",
      list(keys) == [202100, 202101] and s[0, 0] == 5 and s[1, 0] == 5 and np.isnan(s[1, 1]))

# Triple collocation : erreurs indépendantes d'écarts-types 1, 2 et 3
rng = np.random.default_rng(0)
t = rng.gamma(2.0, 10.0, size=(4000, 3))
xs = [t + rng.normal(0, sd, t.shape) for sd in (1.0, 2.0, 3.0)]
ev, r2 = V.triple_collocation(*xs)
check("triple collocation : variances d'erreur retrouvées (1, 4, 9 à 15 % près)",
      np.allclose(ev.mean(1), [1, 4, 9], rtol=0.15), str(np.round(ev.mean(1), 2)))
check("triple collocation : la source la moins bruitée est la mieux corrélée à la vérité", r2[0].mean() > r2[1].mean() > r2[2].mean())
ev2, _ = V.triple_collocation(*(a[:10] for a in xs))
check("moins de 30 valeurs communes : pas d'estimation", np.isnan(ev2).all())

# Poids et fusion
w, n_eq = V.tc_weights(np.array([[1.0, -1.0], [4.0, 2.0], [9.0, 3.0]]))
check("poids : 1 / variance d'erreur, normalisés", np.allclose(w[:, 0], np.array([1, 1 / 4, 1 / 9]) / (1 + 1 / 4 + 1 / 9)))
check("variance négative : poids égaux sur la maille", np.allclose(w[:, 1], 1 / 3) and n_eq == 1)
m = V.merge([np.array([[1.0]]), np.array([[np.nan]]), np.array([[4.0]])], np.array([[0.5], [0.25], [0.25]]))
check("fusion : source manquante, poids renormalisés", np.isclose(m[0, 0], (0.5 * 1 + 0.25 * 4) / 0.75))

# Mise à l'échelle sur la référence
mon = np.tile(np.arange(1, 13), 20)
ref = rng.gamma(2.0, 10.0, size=(240, 2))
src = 2 * ref + 5
out = V.rescale_to_ref(src, ref, mon, np.ones(240, bool))
check("mise à l'échelle : source affine de la référence ramenée sur elle", np.allclose(out, ref, atol=1e-6))

# Stations : drapeau I écarté (pentade incomplète)
g = pd.DataFrame({"date": pd.date_range("2016-01-01", periods=10).strftime("%Y-%m-%d"), "pluie_mm": [1.0] * 10,
                  "drapeau": ["G"] * 7 + ["I"] + ["G"] * 2})
sp = V.station_pentads(g)
check("station : pentade avec un drapeau I = manquante", sp.loc[201600] == 5 and np.isnan(sp.loc[201601]))
o = np.array([1.0, 2.0, 3.0, 4.0] * 5)
check("KGE parfait = 1", np.isclose(V.kge(o, o), 1.0))

# Chaîne complète sur 4 mailles, 2001-2025 : la fusion bat la meilleure source seule
dates = pd.date_range("2001-01-01", "2025-12-31", freq="D")
truth = rng.gamma(0.6, 8.0, size=(len(dates), 4))
daily = {"chirps": (dates, truth + rng.normal(0, 3, truth.shape)),
         "imerg": (dates, 1.3 * truth + rng.normal(0, 4, truth.shape)),
         "era5": (dates, 0.8 * truth + rng.normal(0, 5, truth.shape))}
res = V.analyse(daily, None)
check("chaîne : meilleure source seule = CHIRPS (erreur la plus faible)", res["best"] == "chirps", res["best"])
kt, _, tp = V.to_pentads(dates, truth)
te = res["test"]
rm = lambda a: float(np.sqrt(np.nanmean((a[te] - tp[te]) ** 2)))
check("chaîne : la fusion C est plus proche de la vérité que CHIRPS seule en période de test",
      rm(res["products"]["C"]) < rm(res["products"]["chirps"]),
      f"C {rm(res['products']['C']):.2f} contre CHIRPS {rm(res['products']['chirps']):.2f}")

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
