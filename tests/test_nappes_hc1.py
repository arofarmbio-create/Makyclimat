"""H-C1 : profondeur de nappe de Fan et al. face aux forages (scripts/validate_nappes_hc1.py), sur données simulées."""
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_nappes_hc1 as H  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


csv = """Nom,ID unique,Type de point d'eau,Coordonnées GPS,Niveau statique d'eau,Date du rapport
A,1,Forage,"-22.8, 47.3",24.3,"Sep 8, 2026 10:32 AM"
A,1,Forage,"-22.8, 47.3",20.0,"Jan 2, 2026 10:00 AM"
B,2,Forage,"-21.6, 47.8",0,"Jul 29, 2026 10:28 AM"
C,3,Forage,"-21.6, 47.8",250,"Jul 29, 2026 10:28 AM"
D,4,Forage,"10.0, 10.0",5,"Jul 29, 2026 10:28 AM"
E,5,Puits,"-18.9, 47.5",3.2,"Jul 29, 2026 10:28 AM"
"""
with tempfile.TemporaryDirectory() as t:
    p = Path(t) / "m.csv"
    p.write_text(csv, encoding="utf-8")
    pts = H.load_points(p)
check("contrôle : 0 m, plus de 200 m et hors de Madagascar écartés ; doublon -> relevé le plus récent",
      sorted(pts.id) == [1, 5] and float(pts[pts.id == 1].mesure_m.iloc[0]) == 24.3)
check("Fan : valeur négative -> profondeur positive ; eau au-dessus du sol -> 0 m",
      np.allclose(H.fan_depth([-15.5, 2.0]), [15.5, 0.0]) and np.isnan(H.fan_depth([np.nan])[0]))
check("classes de relief", [H.hand_class(v) for v in (2, 10, 40)] ==
      ["fond de vallée (HAND < 5 m)", "bas de versant (5-15 m)", "versant ou plateau (> 15 m)"])

rng = np.random.default_rng(3)
n = 400
lat = rng.uniform(-25, -12, n)
lon = rng.uniform(44, 50, n)
obs = rng.gamma(2.0, 3.0, n)
base = pd.DataFrame({"lat": lat, "lon": lon, "mesure_m": obs, "classe_relief": np.where(obs > 6, "a", "b")})
r1 = H.analyse(base.assign(fan_m=obs + 10 + rng.normal(0, 1, n)))
check("biais réel de +10 m : H-C1 confirmée (Wilcoxon et blocs)", r1["H-C1"] and abs(r1["global"]["ecart_median_m"] - 10) < 0.5)
r0 = H.analyse(base.assign(fan_m=obs + rng.normal(0, 2, n)))
check("pas de biais : H-C1 non confirmée", not r0["H-C1"], f"p = {r0['global']['p_wilcoxon']:.3f}")
check("tableau par classe produit", set(r1["classes"].classe) == {"a", "b"})
bt = H.block_test(base.assign(ecart_m=5.0))
check("blocs de 1° : tous positifs, test du signe significatif", bt["blocs_fan_plus_profond"] == bt["blocs_non_nuls"] and bt["p_signe"] < 0.05)

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
