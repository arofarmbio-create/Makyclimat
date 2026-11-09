"""Recharge corrigée par les mesures malgaches (scripts/recharge_locale.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import recharge_locale as R  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


check("groupes : socle et autres", list(R.group2(["Basement", "Unconsolidated", "Sedimentary"])) == ["socle", "autres", "autres"])
d = R.dist_km([0.0], [0.0], [0.0], [1.0])[0, 0]
check("distance : 1° de longitude à l'équateur ≈ 111 km", abs(d - 111.2) < 0.5, f"{d:.1f}")
lat, lon = np.array([0.0, 0.0, 0.0, 5.0]), np.array([0.0, 0.1, 0.2, 5.0])   # 3 sites en chaîne (11 km), 1 isolé
lab = R.clusters(lat, lon)
check("groupes de sites par lien simple", lab[0] == lab[1] == lab[2] and lab[3] != lab[0], str(lab))

tab = pd.DataFrame({"site": list("abcd"), "lat": [0.0, 0.0, 10.0, 10.0], "lon": [0.0, 1.0, 0.0, 1.0], "t2": [100.0] * 4,
                    "mes": [10.0, 10.0, 300.0, 300.0], "g2": ["socle", "socle", "autres", "autres"]})
m = R.fit(tab)
check("facteur par groupe", abs(np.exp(m["grp"]["socle"]) - 0.1) < 1e-9 and abs(np.exp(m["grp"]["autres"]) - 3.0) < 1e-9)
p2 = R.predict(m, [100.0, 100.0], ["socle", "autres"], [0.0, 10.0], [0.5, 0.5], "M2")
check("M2 applique le facteur du groupe", np.allclose(p2, [10.0, 300.0]))
p3 = R.predict(m, [100.0], ["socle"], [0.0], [0.5], "M3")
check("M3 = M2 quand les résidus après M2 sont nuls", np.allclose(p3, [10.0]))
m1 = R.fit(tab.iloc[[0, 2]])
check("repli sur le facteur unique si moins de 2 sites dans le groupe", m1["grp"] == {}
      and np.allclose(R.predict(m1, [100.0], ["socle"], [0.0], [0.0], "M2"), 100.0 * np.exp(m1["glob"])))
tab2 = tab.assign(mes=[5.0, 20.0, 300.0, 300.0])
m2 = R.fit(tab2)
far = R.predict(m2, [100.0], ["socle"], [50.0], [50.0], "M3")
near = R.predict(m2, [100.0], ["socle"], [0.0], [0.0], "M3")
check("M3 : correction locale près d'un site, effacée loin", abs(far[0] - 10.0) < 1e-6 and near[0] < 10.0, f"{near[0]:.2f}")
cv = R.cross_validate(tab, np.array([0, 1, 2, 3]))
# sans le site a, le socle n'a plus qu'un site : repli sur le facteur unique (médiane de 0,1 ; 3 ; 3 = 3)
check("validation croisée : site prédit sans lui-même (repli)", np.isclose(cv.M2.iloc[0], 300.0) and cv.M0.iloc[0] == 100.0)
hits, err = R.score([10.0, 50.0], [12.0, 10.0], [5.0, 5.0], [20.0, 20.0])
check("score : retrouvés et erreur médiane", hits == 1 and abs(err - np.median([abs(np.log10(10 / 12)), np.log10(5)])) < 1e-12)

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
