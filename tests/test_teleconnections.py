"""Teste le modèle saisonnier ONI/DMI (build_teleconnections.py) : détecte un lien réel, refuse un faux lien, pas de réseau.

Usage : python tests/make_synthetic.py && python tests/test_teleconnections.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_teleconnections as T  # noqa: E402
from common import country_docs_dir, grid_dir, load_grid  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


rng = np.random.default_rng(5)
years = np.arange(1982, 2027)
oni = rng.normal(0, 1, len(years))
X = oni[:, None]
y_lien = -0.8 * oni + rng.normal(0, 0.5, len(years))        # lien fort : El Niño -> moins de pluie
e1 = T.evaluate(X, y_lien, years)
check("lien réel : MSSS en validation croisée > 0,3", e1["msss_loo"] > 0.3, f"{e1['msss_loo']:.2f}")
check("lien réel : MSSS chronologique > 0", e1["msss_chrono"] > 0, f"{e1['msss_chrono']:.2f}")
check("lien réel : permutation significative", T.perm_pvalue_loo(X, y_lien, n=200) < 0.01)
# bruit pur : un tirage isolé peut dépasser 0 par hasard ; en moyenne sur 200 tirages, pas mieux que la climatologie,
# et les trois critères réunis (MSSS LOO > 0, chrono > 0, p < 0,05) ne passent que rarement
ms_b, faux = [], 0
for _ in range(200):
    yb = rng.normal(0, 1, len(years))
    eb = T.evaluate(X, yb, years)
    ms_b.append(eb["msss_loo"])
    faux += eb["msss_loo"] > 0 and eb["msss_chrono"] > 0 and T.perm_pvalue_loo(X, yb, n=50) < 0.05
check("bruit : MSSS moyen en validation croisée <= 0", np.mean(ms_b) <= 0, f"{np.mean(ms_b):.3f}")
check("bruit : faux « prévisible » dans moins de 10 % des tirages", faux / 200 < 0.10, f"{faux}/200")
check("Benjamini-Hochberg : garde la petite p-valeur, rejette les autres", list(T.bh([0.001, 0.4, 0.8, 0.5])) == [True, False, False, False])
txt = "1870 2026\n2025 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 1.1 1.2\n2026 0.1 0.2 0.3 0.4 0.5 -9999.000 -9999.000 -9999.000 -9999.000 -9999.000 -9999.000 -9999.000\n  -9999\n"
d = T.parse_psl(txt)
check("lecture du format NOAA PSL (valeurs manquantes ignorées)", len(d) == 17 and d[(d.year == 2025) & (d.month == 8)].value.iloc[0] == 0.8)

# chaîne complète sur le pays simulé : DMI de juillet-septembre absent pour l'année en cours -> modèle ONI seul en prévision
ms = load_grid(grid_dir("demo") / "monthly_series.npz")
yrs = [int(v) for v in ms["years"]]
oni_df = pd.DataFrame({"year": range(yrs[0] - 1, yrs[-1] + 1), "center_month": 8,
                       "oni": rng.normal(0, 1, yrs[-1] - yrs[0] + 2)})
dmi_df = pd.DataFrame([(y, m, rng.normal()) for y in range(yrs[0] - 1, yrs[-1]) for m in range(1, 13)], columns=["year", "month", "value"])
df, fc = T.main("demo", dmi=dmi_df, oni=oni_df)
check("une ligne par région, cible et modèle", len(df) == df.adm1.nunique() * 3 * 2, str(len(df)))
check("prévisible seulement si MSSS LOO > 0, MSSS chrono > 0 et significatif",
      ((~df.previsible) | ((df.msss_loo > 0) & (df.msss_chrono > 0) & df.signif_fdr10)).all())
check("DMI de l'année en cours absent : aucune prévision ONI+DMI", all(x["modele"] == "oni" for x in fc))
check("région non prévisible : pas de chiffre de prévision (climatologie)", all(x["anomalie_std"] is None for x in fc if not x["previsible"]))
j = json.load(open(country_docs_dir("demo") / "teleconnections.json", encoding="utf-8"))
check("JSON publié avec prédicteurs et prévision", j["predictors"]["dmi_jas"] is None and len(j["forecast"]) == len(fc))

print(f"\n{FAILS} ÉCHEC(S)" if FAILS else "\nTous les tests passent")
sys.exit(1 if FAILS else 0)
