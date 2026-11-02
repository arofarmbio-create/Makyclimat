"""H-C2 : validation par blocs du modèle hybride de profondeur (scripts/validate_nappes_hc2.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_nappes_hc2 as H  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


a = np.arange(12.0).reshape(3, 4)
check("lecture de grille : bonne maille (nord en haut)", H.grid_sample(a, 0.0, 3.0, 1.0, [2.5], [0.5])[0] == 10.0)
acc = np.zeros((5, 5))
acc[:, 2] = 5000
d = H.stream_distance_km(acc, 0.0, 5.0, 0.01, [0.005, 0.045], [4.995, 4.995])
check("distance au cours d'eau : 2 mailles de 0,01° = 2,2 km de part et d'autre", np.allclose(d, 2.22, atol=0.01), str(np.round(d, 2)))

rng = np.random.default_rng(4)
n = 300
df = pd.DataFrame({"lat": rng.uniform(-25, -18, n), "lon": rng.uniform(44, 48, n), "fan_m": rng.uniform(0, 40, n)})
df["hand"] = rng.uniform(0, 40, n)
df["mesure_m"] = 3 + 0.1 * df.hand + rng.normal(0, 0.5, n)


def perfect(tr, te):
    p = (3 + 0.1 * te.hand).to_numpy()
    return p, p - 1, p + 1


def mean_krige(tr, te):
    return np.full(len(te), tr.mesure_m.mean())


res = H.block_cv(df, hybrid=perfect, krige=mean_krige)
check("blocs de 1° avec au moins 5 forages, chacun prédit sans ses forages", len(res) > 10 and (res.forages >= 5).all())
text, ok = H.report(res, n)
check("hybride parfait : bat Fan et le krigeage, H-C2 confirmée", ok and (res.erreur_hybride < res.erreur_fan).all())
check("couverture de l'intervalle calculée", res.couverture_80.between(0, 1).all())

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
