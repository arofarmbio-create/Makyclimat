"""Tests de cohérence de la chaîne de données (hors réseau, données simulées « demo »).

Usage : python tests/make_synthetic.py && python tests/test_pipeline.py
"""
from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import chirps  # noqa: E402
import compute_metrics  # noqa: E402
import update_rainfall  # noqa: E402
from common import INPUTS_DIR, country_docs_dir, grid_dir, load_config, load_grid  # noqa: E402

FAILS = 0


def check(name: str, cond: bool, extra: str = "") -> None:
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


def run_compute() -> None:
    sys.argv = ["compute_metrics.py", "--country", "demo"]
    compute_metrics.main()


def load(rel: str):
    return json.load(open(country_docs_dir("demo") / rel, encoding="utf-8"))


# ---------- 1. Mise à jour de la pluie avec un faux téléchargement ----------
def test_update_rainfall() -> None:
    cfg = load_config("demo")
    clim = load_grid(grid_dir("demo") / "clim_monthly.npz")
    shape = clim["clim"][0].shape
    calls = []

    def fake_fetch(url, bbox):
        calls.append(url)
        # le mois de février 2026 n'a pas encore de dékade 2 ni 3 ; novembre 2026 n'existe pas du tout
        if "2026.11" in url or ("2026.02.2" in url) or ("2026.02.3" in url):
            return None
        return np.full(shape, 50.0, dtype="float32"), 43.0, -11.5, 0.05

    update_rainfall.fetch_array = fake_fetch
    r = update_rainfall.accumulate(cfg, clim, dt.date(2026, 2, 15))
    check("cumul de saison (nov, déc, janv complets + dékade de février)", r is not None and r[2] == dt.date(2026, 2, 10),
          f"jusqu'au {r[2] if r else None}")
    act, norm = r[0], r[1]
    check("pluie cumulée = 4 x 50 mm (3 mois + 1 dékade)", np.allclose(act, 50 * 3 + 50) or np.allclose(act, 200),
          f"{float(np.nanmean(act)):.0f} mm")
    frac_feb = chirps.month_fraction_covered(2026, 2, 1)
    expected_norm = clim["clim"][10] + clim["clim"][11] + clim["clim"][0] + clim["clim"][1] * frac_feb
    check("normale proportionnelle à la couverture du dernier mois", np.allclose(norm, expected_norm, equal_nan=True))
    # début de saison sans donnée : repli sur la saison précédente
    calls.clear()
    r2 = update_rainfall.accumulate(cfg, clim, dt.date(2026, 11, 3))
    check("début de saison sans donnée -> aucun cumul", r2 is None)
    fb = update_rainfall.previous_season_end(cfg, dt.date(2026, 11, 3))
    check("repli = fin de la saison précédente (30 avril 2026)", fb == dt.date(2026, 4, 30), str(fb))
    r3 = update_rainfall.accumulate(cfg, clim, fb + dt.timedelta(days=1))
    check("saison précédente complète disponible", r3 is not None and r3[2] == dt.date(2026, 4, 30) and len(r3[4]) == 6,
          f"{len(r3[4]) if r3 else 0} mois")


# ---------- 2. Cohérence Python / JavaScript des niveaux d'alerte ----------
def test_js_parity() -> None:
    if not shutil.which("node"):
        print("SKIP  parité JS (node absent)")
        return
    cfg = load_config("demo")
    vals = [0, 10, 49.9, 50, 62, 74.99, 75, 89, 90, 99, 100, 140, 400, 999, 2000]
    py = compute_metrics.level_from_pct(np.array(vals, dtype=float), cfg["alert_levels"]).tolist()
    code = ("const MC=require('./docs/logic.js');const v=%s;const a=%s;"
            "console.log(JSON.stringify(v.map(x=>MC.levelFromPct(x,a))))") % (json.dumps(vals), json.dumps(cfg["alert_levels"]))
    out = subprocess.run(["node", "-e", code], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    check("niveaux d'alerte identiques en Python et JavaScript", json.loads(out) == py, f"{py}")


# ---------- 3. Invariants des indicateurs ----------
def test_invariants() -> None:
    meta, top = load("meta.json"), load("metrics/top.json")
    neutral = meta["rain_factors"].index(1.0)
    ok_neutral = ok_monotone = ok_sum = True
    for lv in ("adm1", "adm2"):
        for pc, m in top[lv].items():
            ok_neutral &= m["se"][neutral] == m["e"] and m["st"][neutral] == m["t"]
            ok_monotone &= all(m["se"][i] >= m["se"][i + 1] for i in range(len(m["se"]) - 1))
            ok_monotone &= all(m["st"][i] >= m["st"][i + 1] for i in range(len(m["st"]) - 1))
    check("scénario neutre (x1,00) = valeurs observées", ok_neutral)
    check("exposés et cibles décroissent quand la pluie augmente", ok_monotone)
    # somme des fokontany d'un district = valeur du district
    for adm2, m2 in top["adm2"].items():
        d = load(f"metrics/d/{adm2}.json")
        s_e = sum(v["e"] for v in d["adm4"].values())
        s_t = sum(v["t"] for v in d["adm4"].values())
        s_p = sum(v["p"] for v in d["adm4"].values())
        ok_sum &= abs(s_e - m2["e"]) <= len(d["adm4"]) and abs(s_t - m2["t"]) <= len(d["adm4"]) and s_p == m2["p"]
    check("districts = somme de leurs fokontany (population, exposés, cibles)", ok_sum)
    nat = meta["national"]
    check("total national = somme des régions", nat["pop"] == sum(m["p"] for m in top["adm1"].values()))
    check("cibles <= exposés <= population", nat["targets"] <= nat["exposed"] <= nat["pop"],
          f"{nat['targets']} <= {nat['exposed']} <= {nat['pop']}")
    r1 = next(iter(top["adm1"].values()))
    check("cellules côtières sans donnée remplies (aucune région sans niveau)", all(m["l"] > 0 for m in top["adm1"].values()))


# ---------- 4. Fichiers d'entrée : vulnérabilité et interventions ----------
def with_inputs(files: dict[str, str], fn) -> None:
    backups = {}
    try:
        for name, content in files.items():
            p = INPUTS_DIR / name
            backups[name] = p.read_text(encoding="utf-8") if p.exists() else None
            p.write_text(content, encoding="utf-8")
        run_compute()
        fn()
    finally:
        for name, content in backups.items():
            p = INPUTS_DIR / name
            if content is None:
                p.unlink(missing_ok=True)
            else:
                p.write_text(content, encoding="utf-8")


def test_inputs() -> None:
    def after():
        d = load("metrics/d/R1D1.json")
        top = load("metrics/top.json")
        f = next(v for v in d["adm4"].values() if v["e"] > 0)
        check("part vulnérable fournie au niveau district appliquée aux fokontany",
              f["vs"] == 0.5 and f["vi"] == 1 and abs(f["t"] - f["e"] * 0.5) <= 1, f"vs={f['vs']}, vi={f['vi']}")
        other = next(v for v in load("metrics/d/R2D1.json")["adm4"].values())
        check("autres districts : valeur par défaut signalée", other["vi"] == 0 and other["vs"] == 0.8)
        c = d["adm3"]["R1D1C1"]
        check("bénéficiaires comptés une seule fois au niveau commune", c.get("b") == 1000, str(c.get("b")))
        check("… et cumulés au district et à la région", d.get("adm3") is not None and top["adm2"]["R1D1"].get("b") == 1000
              and top["adm1"]["R1"].get("b") == 1000)
        check("pas de bénéficiaires ailleurs", "b" not in top["adm2"]["R2D1"])

    with_inputs({"vulnerabilite.csv": "pcode,part_vulnerable,source,date\nR1D1,0.5,test,2026-01-01\n",
                 "interventions.csv": "partenaire,secteur,activite,pcode,beneficiaires,statut,debut,fin,source\n"
                                      "ONG-test,food_security,cash,R1D1C1,1000,en cours,2026-01-01,2026-03-01,test\n"},
                after)
    run_compute()  # remet les sorties en état par défaut


def test_external() -> None:
    run_compute()
    top = load("metrics/top.json")
    meta = load("meta.json")
    ids = {x["id"] for x in meta["external"]}
    check("indicateurs externes déclarés détectés, inconnus ignorés",
          ids == {"poverty_headcount", "ipc_phase3plus_pct", "ipc_phase3plus_pop"}, str(ids))
    check("valeur directe région", top["adm1"]["R1"]["x"]["poverty_headcount"] == 70)
    check("date la plus récente retenue (somme R1D2 = 700)", top["adm2"]["R1D2"]["x"]["ipc_phase3plus_pop"] == 700)
    check("agrégation somme vers la région (R1 = 700)", top["adm1"]["R1"]["x"].get("ipc_phase3plus_pop") == 700,
          str(top["adm1"]["R1"].get("x")))
    d3 = load("metrics/d/R3D1.json")
    f = next(v for v in d3["adm4"].values())
    check("IPC phase 3+ devient la part vulnérable (0,30, vi=2) héritée par les fokontany",
          abs(f["vs"] - 0.3) < 1e-9 and f["vi"] == 2, f"vs={f['vs']} vi={f['vi']}")
    d1 = load("metrics/d/R1D1.json")
    check("sans IPC : valeur par défaut", next(iter(d1["adm4"].values()))["vi"] == 0)

    def after():
        g = load("metrics/d/R3D1.json")
        ff = next(v for v in g["adm4"].values())
        check("vulnerabilite.csv prioritaire sur l'IPC", ff["vs"] == 0.6 and ff["vi"] == 1, f"vs={ff['vs']} vi={ff['vi']}")
    with_inputs({"vulnerabilite.csv": "pcode,part_vulnerable,source,date\nR3D1,0.6,test,2026-01-01\n"}, after)
    run_compute()


if __name__ == "__main__":
    run_compute()
    test_update_rainfall()
    test_js_parity()
    test_invariants()
    test_inputs()
    test_external()
    print("\nTous les tests de données passent." if not FAILS else f"\n{FAILS} ÉCHEC(S)")
    sys.exit(1 if FAILS else 0)
