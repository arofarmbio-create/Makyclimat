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
from common import INPUTS_DIR, country_docs_dir, grid_dir, load_config, load_grid, read_units  # noqa: E402

FAILS = 0


def check(name: str, cond: bool, extra: str = "") -> None:
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


def run_compute(today: str = "2026-02-21") -> None:
    sys.argv = ["compute_metrics.py", "--country", "demo", "--today", today]
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


def test_scenarios() -> None:
    import datetime as dt
    import numpy as np
    import scenarios as SC
    from compute_metrics import level_from_pct

    # fonctions pures
    months = [(2025, 11), (2025, 12), (2026, 1), (2026, 2), (2026, 3), (2026, 4)]
    cov = SC.covered_fractions(months, "2025-11", dt.date(2026, 2, 20), (2025, 11))
    check("fraction observée par mois (nov, déc, jan = 1 ; fév = 20/28 ; mars, avril = 0)",
          cov[:3] == [1.0, 1.0, 1.0] and abs(cov[3] - 20 / 28) < 1e-9 and cov[4:] == [0.0, 0.0])
    check("saison non couverte par les données -> rien d'observé",
          SC.covered_fractions(months, "2024-11", dt.date(2025, 4, 30), (2025, 11)) == [0.0] * 6)
    check("saison cible hors saison = prochaine saison", SC.target_season(dt.date(2026, 10, 25), 11, 4) == (2026, 2027)
          and SC.target_season(dt.date(2026, 2, 1), 11, 4) == (2025, 2026))
    lv = [{"level": 4, "below_pct": 50}, {"level": 3, "below_pct": 75}, {"level": 2, "below_pct": 90}, {"level": 1, "below_pct": 1e6}]
    xs = np.array([10, 49.9, 50, 74, 80, 95, np.nan, 300])
    check("niveaux vectorisés identiques à la version de référence", (SC.level_array(xs, lv) == level_from_pct(xs, lv)).all())
    w = SC.tercile_weights(np.arange(30.0), (0.6, 0.3, 0.1))
    check("poids de prévision : somme = 1 et plus de poids sur le tercile sec", abs(w.sum() - 1) < 1e-9 and w[:10].sum() > 0.59)
    check("quantile pondéré", abs(SC.weighted_quantile(np.array([1.0, 2, 3]), np.array([1.0, 1, 1]), 0.5) - 2) < 1e-9)

    # chaîne complète sur la démo (en pleine saison)
    run_compute()
    top, meta = load("metrics/top.json"), load("meta.json")
    sc = meta["scenarios"]
    check("saison cible en cours et part observée", sc["season"] == "2025-2026" and 0.5 < sc["observed_share"] < 0.7, str(sc["season"]))
    nat = lambda sid, k: sum(v["sc"][sid][k] for v in top["adm1"].values())
    check("plus la saison est sèche, plus il y a d'exposés (sèche >= médiane >= humide)",
          nat("sec", 2) >= nat("med", 2) >= nat("hum", 2), f"{nat('sec', 2)} {nat('med', 2)} {nat('hum', 2)}")
    check("El Niño simulé plus exposé que La Niña", nat("el", 2) > nat("la", 2))
    check("excès de pluie : plus de personnes en saison humide", nat("hum", 4) >= nat("sec", 4))
    check("cibles <= exposés dans chaque scénario", all(v["sc"][s][3] <= v["sc"][s][2] for v in top["adm1"].values() for s in v["sc"]))
    d = load("metrics/d/R1D1.json")
    d3 = d["adm3"]
    check("districts = somme des communes (exposés, scénario sec)",
          abs(top["adm2"]["R1D1"]["sc"]["sec"][2] - sum(v["sc"]["sec"][2] for v in d3.values())) <= len(d3))
    check("probabilité d'alerte entre 0 et 1 et exposés attendus", all(0 <= v["pa"] <= 1 and v["ex"] >= 0 for v in top["adm1"].values()))

    # hors saison : on regarde la prochaine saison, rien n'est encore observé
    run_compute("2026-10-25")
    sc2 = load("meta.json")["scenarios"]
    check("hors saison : prochaine saison, aucune pluie observée", sc2["season"] == "2026-2027" and sc2["observed_share"] == 0)
    run_compute()

    # prévision saisonnière fournie : pondération des années, tout le pays très sec
    def after_forecast():
        m2 = load("meta.json")
        t2 = load("metrics/top.json")
        n2 = sum(v["sc"]["prev"][2] for v in t2["adm1"].values())
        check("prévision saisonnière : scénario « prévision » ajouté et pondération signalée",
              m2["scenarios"]["weighted_by_forecast"] and any(x["id"] == "prev" for x in m2["scenarios"]["list"]))
        check("prévision très sèche : plus d'exposés que le scénario médian", n2 > nat("med", 2), f"{n2} > {nat('med', 2)}")
        check("probabilité d'alerte plus forte avec une prévision sèche",
              sum(v["pa"] for v in t2["adm1"].values()) > sum(v["pa"] for v in top["adm1"].values()))
    with_inputs({"prevision_saisonniere.csv": "pcode,p_sec,p_normal,p_humide,source,date\nALL,0.8,0.15,0.05,test,2026-10-01\n"},
                after_forecast)

    # alertes des secteurs : affichées et héritées
    def after_alerts():
        t2 = load("metrics/top.json")
        al = t2["adm2"]["R1D1"].get("al", [])
        d4 = next(iter(load("metrics/d/R1D1.json")["adm4"].values()))
        check("alerte sectorielle fournie affichée au niveau du district", al and al[0][0] == "wash" and al[0][1] == 3)
        check("… héritée par les fokontany du district avec sa source", d4.get("al") and d4["al"][0][3] == "Cluster WASH")
        check("… pas dans un autre district", "al" not in t2["adm2"]["R2D1"])
    with_inputs({"alertes_secteurs.csv": "pcode,secteur,niveau,message,source,date\nR1D1,wash,3,Points d'eau en baisse,Cluster WASH,2026-02-10\n"},
                after_alerts)
    run_compute()


def test_history_years() -> None:
    meta, top = load("meta.json"), load("metrics/top.json")
    yrs = meta["scenarios"]["hist_years"]
    d = load("metrics/d/R1D1.json")
    check("pluie par saison passée : une valeur par année pour chaque unité", len(yrs) == 44 and all(len(v["y"]) == 44 for v in list(d["adm4"].values()) + list(d["adm3"].values()) + list(top["adm1"].values())))
    el = [i for i, y in enumerate(yrs) if y % 4 == 0]
    la = [i for i, y in enumerate(yrs) if y % 4 == 2]
    r = top["adm1"]["R1"]["y"]
    check("saisons El Niño simulées plus sèches que La Niña dans l'historique", np.mean([r[i] for i in el]) < np.mean([r[i] for i in la]) - 20, f"{np.mean([r[i] for i in el]):.0f} vs {np.mean([r[i] for i in la]):.0f}")
    comm = [v["y"][0] for v in d["adm3"].values() if v["y"][0] is not None]
    dist = top["adm2"]["R1D1"]["y"][0]
    check("la valeur d'un district est comprise entre celles de ses communes", min(comm) - 1 <= dist <= max(comm) + 1, f"{min(comm)} {dist} {max(comm)}")


def test_history_js_consistency() -> None:
    """Pour une saison passée, la somme des exposés des fokontany (calcul JS) = exposés du district (calcul Python)."""
    if not shutil.which("node"):
        return
    meta, top = load("meta.json"), load("metrics/top.json")
    d = load("metrics/d/R1D1.json")
    code = ("const MC=require('./docs/logic.js');const meta=%s;const top=%s;const d=%s;const out=[];"
            "meta.scenarios.hist_years.forEach((y,i)=>{const id='y:'+y;"
            "const dist=top.adm2.R1D1;const lv=Object.values(d.adm4);"
            "for(const k of ['e','t','w']){const s=lv.reduce((a,m)=>a+MC.valueFor(m,k,null,meta,id),0);"
            "const t=MC.valueFor(dist,k,null,meta,id);out.push(Math.abs(s-t)<=Math.max(2,0.002*t));}"
            "out.push(MC.valueFor(dist,'pc',null,meta,id)===dist.y[i]);});console.log(JSON.stringify(out.every(Boolean)))") % (json.dumps(meta), json.dumps(top), json.dumps(d))
    out = subprocess.run(["node", "-e", code], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    check("saisons passées : exposés, cibles et excès des fokontany (JS) = district (Python), 44 saisons", json.loads(out) is True)


def test_forecast_alerts() -> None:
    run_compute()
    meta, top = load("meta.json"), load("metrics/top.json")
    fc = meta["forecast"]
    check("prévision utilisée : dates, horizon et aléas déclarés", fc and fc["horizon_days"] == 7 and fc["today"] == "2026-02-21"
          and "flood" in fc["hazards"] and fc["flood"]["available"], str(fc and fc["flood"]))
    casc = meta["scenarios"]["cascade"]
    check("cascade climat -> prévision : observations jusqu'au 20/02, prévision jusqu'au 08/03",
          casc["used"] and casc["observed_through"] == "2026-02-20" and casc["known_through"] == "2026-03-08" and casc["days"] == 16, str(casc))
    # niveaux par fokontany
    d = {}
    for f in (country_docs_dir("demo") / "metrics" / "d").glob("*.json"):
        j = json.load(open(f, encoding="utf-8"))
        d.update(j["adm4"])
    units = read_units("demo")
    leaves = units[units.level == 4]
    north = [pc for pc, la in zip(leaves.pcode, leaves.lat) if la > -16.5 + 0.13]
    south = [pc for pc, la in zip(leaves.pcode, leaves.lat) if la < -24.0 - 0.13]
    west = [pc for pc, lo in zip(leaves.pcode, leaves.lon) if lo < 45.0 - 0.13]
    H = ["rain", "wind", "heat", "dry", "flood"]
    check("pluie très forte au nord -> alerte (niveau 2) ou plus", north and all(d[pc]["ew"][0] >= 2 for pc in north), f"{len(north)} fokontany")
    check("rafales de 95 km/h au nord -> alerte vent", all(d[pc]["ew"][1] == 2 for pc in north))
    check("39 °C à l'ouest -> alerte chaleur", west and all(d[pc]["ew"][2] == 2 for pc in west))
    check("plus de 15 jours secs au sud -> alerte période sèche", south and all(d[pc]["ew"][3] >= 2 for pc in south))
    quiet = [pc for pc in leaves.pcode if pc not in set(north) | set(south) | set(west)]
    check("zone calme sans alerte pluie/vent/chaleur", all(sum(d[pc]["ew"][:3]) == 0 for pc in quiet[:50]))
    check("alerte précoce à 7 jours : cible pondérée par la vulnérabilité économique (jamais seulement l'exposé brut)",
          north and all(d[pc]["ewt"][0] <= d[pc]["ewp"][0] and abs(d[pc]["ewt"][0] - round(d[pc]["ewp"][0] * d[pc]["vs"])) <= 1 for pc in north))
    com = units[units.level == 3].reset_index(drop=True)
    kids0 = leaves[leaves.adm3 == com.pcode[0]].pcode
    kids1 = leaves[leaves.adm3 == com.pcode[1]].pcode
    check("crue : débit prévu 2,5 × la crue de 2 ans -> niveau 2 (alerte) hérité par les fokontany de la commune",
          all(d[pc]["ew"][4] == 2 for pc in kids0) and d[next(iter(kids0))]["ev"][5] == 2.5)
    check("crue : 1,2 × la crue de 2 ans -> vigilance", all(d[pc]["ew"][4] == 1 for pc in kids1))
    r = top["adm1"]
    check("région : niveau maximal des fokontany et personnes en alerte",
          all(len(v["ew"]) == 5 and len(v["ewp"]) == 5 and len(v["ewt"]) == 5 for v in r.values()) and max(v["ew"][0] for v in r.values()) >= 2)
    check("région : cible pondérée <= exposé brut pour chaque aléa météo à 7 jours",
          all(all(v["ewt"][k] <= v["ewp"][k] for k in range(5)) for v in r.values()))
    nd = [len(v["fr"]) for v in r.values()]
    check("série quotidienne de 10 jours de pluie et de température", all(n == 10 for n in nd))
    # la prévision change les scénarios (ceinture sèche : zéro pluie pendant 17 jours)
    sc_with = {k: sum(v["sc"][k][2] for v in r.values()) for k in ("sec", "med", "hum")}
    p = grid_dir("demo") / "forecast.npz"
    backup = p.with_suffix(".bak")
    shutil.move(p, backup)
    try:
        run_compute()
        r0 = load("metrics/top.json")["adm1"]
        sc_wo = {k: sum(v["sc"][k][2] for v in r0.values()) for k in ("sec", "med", "hum")}
        check("sans prévision : pas d'alerte précoce ni de cascade", load("meta.json")["forecast"] is None
              and not load("meta.json")["scenarios"]["cascade"]["used"])
        check("la prévision (ceinture sèche) augmente les exposés du scénario médian", sc_with["med"] > sc_wo["med"], f"{sc_with['med']} > {sc_wo['med']}")
    finally:
        shutil.move(backup, p)
    run_compute()


def test_external() -> None:
    run_compute()
    top = load("metrics/top.json")
    meta = load("meta.json")
    ids = {x["id"] for x in meta["external"]}
    check("indicateurs externes déclarés détectés, inconnus ignorés",
          {"poverty_headcount", "ipc_phase3plus_pct", "ipc_phase3plus_pop"} <= ids and "inconnu_xyz" not in ids, str(ids))
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

    f1 = next(v for v in d1["adm4"].values() if v["e"] > 0)
    femmes_1549 = load_config("demo")["femmes_15_49_pct"]   # hérité de mdg.yml par make_synthetic.py
    attendu = f1["e"] * femmes_1549 * 10 / 100   # femmes_15_49_pct x dhs_femmes_enceintes_pct (R1)
    check("femmes enceintes estimées pour un fokontany exposé sous R1 (deux hypothèses empilées)",
          abs(f1["x"].get("femmes_enceintes_estimees", -1) - attendu) < 0.5, f"{f1['x'].get('femmes_enceintes_estimees')} vs {attendu}")
    d2 = load("metrics/d/R2D1.json")
    check("pas de femmes enceintes estimées hors R1 (R2 sans dhs_femmes_enceintes_pct)",
          all("femmes_enceintes_estimees" not in v.get("x", {}) for v in d2["adm4"].values()))

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
    test_scenarios()
    test_history_years()
    test_history_js_consistency()
    test_forecast_alerts()
    print("\nTous les tests de données passent." if not FAILS else f"\n{FAILS} ÉCHEC(S)")
    sys.exit(1 if FAILS else 0)
