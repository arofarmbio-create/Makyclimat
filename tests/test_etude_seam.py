"""Étude des données SEAM (scripts/etude_seam.py), sur données simulées."""
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import etude_seam as S  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


# Lecture : deux fichiers de région, un point en double, noms tirés du résumé
with tempfile.TemporaryDirectory() as d:
    raw = Path(d)
    (raw / "resume_pdo.json").write_text(json.dumps({"regions": ["R0", "R1"], "districts": ["D0"], "communes": ["C0", "C1"]}))
    (raw / "pdo_region_0.json").write_text(json.dumps({"points": [["a", -20.0, 46.0, 0, 0, 0, 0, "16", "1"],
                                                                  ["b", -20.0, 46.01, 0, 0, 1, 0, "10", "2"]]}))
    (raw / "pdo_region_1.json").write_text(json.dumps({"points": [["b", -20.0, 46.01, 0, 0, 1, 0, "10", "2"],
                                                                  ["c", -19.0, 47.0, 1, 0, 0, 0, "7", "4"]]}))
    (raw / "tableau_pdo.json").write_text(json.dumps({
        "regions": ["R0"], "districts": ["D0"], "communes": ["C0", "C1"],
        "evolution": {"lignes": [[0, 0, 0, 2025, 10, 1000], [0, 0, 0, 2026, 20, 1000], [0, 0, 1, 2025, 0, None]]},
        "lignes": [[0, 0, 0, "16", "1", 3, 0, 0, 0, 0, 0], [0, 0, 0, "10", "2", 2, 0, 0, 0, 0, 0], [0, 0, 0, "2", "1", 9, 0, 0, 0, 0, 0]]}))
    pts = S.load_points(raw)
    com = S.load_communes(raw)
check("lecture : doublon retiré, noms de région et de commune", len(pts) == 3 and list(pts.region) == ["R0", "R0", "R1"]
      and pts.commune.iloc[1] == "C1")
c0 = com[com.commune == "C0"].iloc[0]
check("communes : population 2025, bénéficiaires 2026, ouvrages souterrains sans les bornes-fontaines",
      c0.population == 1000 and c0.beneficiaires == 20 and c0.ouvrages_souterrains == 5 and c0.fonctionnels == 3)
q4 = S.pressure(com)
check("pression : part de communes avec population", q4["part_population_non_nulle"] == 0.5)
f = S.failures(pts)
check("pannes : FPMH abandonné compté en panne", f.set_index("region").en_panne.to_dict() == {"R0": 0.0, "R1": 1.0})

# Q2 : SEAM décalé d'un écart-type -> DMS proche de 1 ; étendue
rng = np.random.default_rng(0)
mg = pd.DataFrame({"altitude_m": rng.normal(0, 1, 2000)})
se = pd.DataFrame({"altitude_m": rng.normal(1, 1, 2000)})
q2 = S.representativeness(mg, se, ["altitude_m"])
check("DMS d'environ 1", abs(q2.dms.iloc[0] - 1) < 0.1, f"{q2.dms.iloc[0]:.2f}")
check("part hors étendue plus grande que 2 %", S.outside_share(mg, se, ["altitude_m"]).mean() > 0.05)
check("distance de classes : identiques 0, disjointes 1",
      S.class_distance(pd.DataFrame({"glim": [1, 2]}), pd.DataFrame({"glim": [1, 2]})) == 0.0
      and S.class_distance(pd.DataFrame({"glim": [1]}), pd.DataFrame({"glim": [2]})) == 1.0)

# Q3 : part de puits dans un rayon, anneau d'exclusion, minimum d'ouvrages
w_lat = np.r_[-20.0, np.full(4, -20.01), np.full(2, -20.02)]   # un ouvrage au point même, puis 6 à 1-2 km
w_lon = np.full(7, 46.0)
is_well = np.array([False, True, True, True, False, False, True])
share, n = S.well_share(np.array([-20.0]), np.array([46.0]), w_lat, w_lon, is_well, radius_km=5.0)
check("ouvrage à moins de 200 m exclu, 6 restants, 4 puits sur 6", n[0] == 6 and abs(share[0] - 4 / 6) < 1e-9)
share, n = S.well_share(np.array([-20.0]), np.array([46.0]), w_lat, w_lon, is_well, radius_km=5.0, min_works=7)
check("moins d'ouvrages que le minimum : valeur manquante", np.isnan(share[0]))

# H-S1 : nappe plus profonde là où il y a moins de puits, dans 8 régions
regs = np.repeat([f"R{i}" for i in range(8)], 30)
part = rng.uniform(0, 1, len(regs))
df = pd.DataFrame({"region": regs, "part_puits": part, "mesure_m": 30 - 20 * part + rng.normal(0, 2, len(regs))})
t = S.hs1_test(df)
check("H-S1 soutenue sur données où le lien existe", t["soutenue"] and t["regions_negatives"] == 8)
df["mesure_m"] = rng.normal(15, 5, len(regs))
check("H-S1 non soutenue sans lien", not S.hs1_test(df)["soutenue"])

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
