"""Tests du module historique et réponses (événements, HRP, IATI, import 3W) sans réseau."""
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_history as BH  # noqa: E402
import common  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK   " if cond else "ÉCHEC") + " " + name + (f" — {extra}" if extra else ""))
    if not cond:
        FAILS += 1


def test_parsers_and_merge():
    glide = pd.DataFrame([
        {"glidenumber": "TC-2022-1", "event": "TC", "event_name": "tropical cyclone", "year": 2022, "month": 1, "day": 22, "latitude": -17.0, "longitude": 49.0,
         "affected": 120000, "killed": 10, "homeless": 500, "comments": "Batsirai"},
        {"glidenumber": "DR-2021-1", "event": "DR", "event_name": "drought", "year": 2021, "month": 6, "day": 1, "latitude": -24.5, "longitude": 45.5,
         "affected": 1000000, "killed": 0, "homeless": 0, "comments": "Grand Sud"},
        {"glidenumber": "XX", "event": "OT", "event_name": "x", "year": "bad", "month": 1, "day": 1, "latitude": 0, "longitude": 0}])
    idmc = pd.DataFrame([
        {"displacement_type": "Disaster", "event_start_date": "2022-01-25", "type": "Storm", "subtype": "Tropical cyclone", "event_name": "Cyclone Batsirai",
         "latitude": -17.1, "longitude": 49.1, "figure": 130000, "event_id": 5},
        {"displacement_type": "Conflict", "event_start_date": "2022-02-01", "type": "x", "subtype": "", "event_name": "c", "latitude": -17, "longitude": 49, "figure": 5, "event_id": 6},
        {"displacement_type": "Disaster", "event_start_date": "2023-03-10", "type": "Flood", "subtype": "", "event_name": "Floods", "latitude": -18.9, "longitude": 47.5,
         "figure": 8000, "event_id": 7}])
    g, i = BH.parse_glide(glide), BH.parse_idmc(idmc)
    check("GLIDE : lignes illisibles ignorées, types normalisés", len(g) == 2 and g[0]["type"] == "cyclone" and g[1]["type"] == "sécheresse")
    check("IDMC : seuls les déplacements dus aux catastrophes", len(i) == 2 and i[0]["type"] == "cyclone" and i[1]["type"] == "inondation")
    m = BH.merge_events(g, i)
    check("fusion : le même cyclone vu par GLIDE et IDMC n'est compté qu'une fois", len(m) == 3 and sum(e["type"] == "cyclone" for e in m) == 1)
    cyc = next(e for e in m if e["type"] == "cyclone")
    check("fusion : on garde les deux sources et les deux chiffres", cyc["src"] == "GLIDE+IDMC" and cyc["affected"] == 120000 and cyc["displaced"] == 130000, str(cyc))
    check("événements triés par date", [e["date"] for e in m] == sorted(e["date"] for e in m))


def test_clusters():
    check("grappes : alias anglais et français", BH.cluster_of("Food Security") == "Sécurité alimentaire" and BH.cluster_of("WASH") == "Eau, assainissement et hygiène"
          and BH.cluster_of("Shelter/NFI") == "Abris et biens non alimentaires" and BH.cluster_of("Santé") == "Santé" and BH.cluster_of("???") == "Autre")


def test_iati_hrp_3w():
    units = common.read_units("demo")
    iati = pd.DataFrame([
        {"aid": "A1", "reporting": "Org A", "title": "Water supply project", "sector_group": "WASH", "day_start": "2019-05-01", "day_end": "2021-03-01",
         "commitment_eur": 3000000, "latitude": -20.0, "longitude": 47.0},
        {"aid": "A1", "reporting": "Org A", "title": "Water supply project", "sector_group": "WASH", "day_start": "2019-05-01", "day_end": "2021-03-01",
         "commitment_eur": 3000000, "latitude": -20.0, "longitude": 47.0},   # doublon
        {"aid": "B2", "reporting": "Org B", "title": "x", "sector_group": "", "day_start": "bad", "day_end": "2021-01-01", "commitment_eur": 1, "latitude": -20.0, "longitude": 47.0}])
    t = BH.parse_iati(iati)
    check("IATI : doublon retiré, une ligne par année d'activité, budget réparti", len(t) == 3 and abs(t.funds.sum() - 3000000) < 1 and set(t.y) == {2019, 2020, 2021}, str(len(t)))
    check("IATI : grappe déduite du titre et du secteur", set(t.cluster) == {"Eau, assainissement et hygiène"})
    hrp = pd.DataFrame([
        {"startDate": "2024-01-01", "locations": "Région 1; District 2.1", "globalClusters": "Education", "organizations": "UNICEF", "currentRequestedFunds": 1000},
        {"startDate": "2024-01-01", "locations": "MDG", "globalClusters": "Health", "organizations": "WHO", "currentRequestedFunds": 500}])
    h = BH.parse_hrp(hrp, units)
    check("HRP : lieux reconnus (région, district) et fonds répartis ; sinon national", len(h) == 3 and (h.pcode == "").sum() == 1 and abs(h[h.pcode != ""].funds.sum() - 1000) < 1e-6, str(h.pcode.tolist()))
    f = units[units.level == 4].iloc[0]
    csv = ("date_debut;pcode;cluster;organisation;beneficiaires;evenement\n"
           f"2023-02-01;{f.pcode};WASH;ONG X;1 200;Cyclone\n2023-03-01;ZZZ;WASH;ONG X;50;\n2023-04-01;{f.pcode};Santé;ONG Y;abc;\n2023-05-01;{f.pcode};Santé;ONG Y;-5;\n")
    d3 = pd.read_csv(io.StringIO(csv), sep=None, engine="python")
    r3, warn = BH.parse_3w(d3, units)
    check("3W : lignes valides gardées, erreurs signalées avec leur numéro de ligne", len(r3) == 1 and r3.ben.iloc[0] == 1200 and len(warn) == 3 and "ligne 3" in warn[0], "; ".join(warn))
    try:
        BH.parse_3w(pd.DataFrame({"pcode": []}), units)
        check("3W : colonnes obligatoires vérifiées", False)
    except ValueError as e:
        check("3W : colonnes obligatoires vérifiées", "date_debut" in str(e))


def test_locate_and_pack():
    units = common.read_units("demo")
    leaf = units[units.level == 4].iloc[5]
    got = common.locate_points("demo", [leaf.lon, 0.0], [leaf.lat, 0.0])
    check("localisation : un point au centre d'un fokontany retrouve son code, un point hors pays reste vide", got[0] == leaf.pcode and got[1] == "", str(got))
    d1 = pd.DataFrame([{"y": 2022, "pcode": leaf.pcode, "org": "A", "cluster": "Santé", "ben": 100.4, "n": 1}])
    d2 = pd.DataFrame([{"y": 2023, "pcode": leaf.pcode, "org": "B", "cluster": "Nutrition", "funds": 5000.0, "n": 2}])
    p = BH.pack([("3w", d1), ("hrp", d2)])
    r = p["rec"]
    check("colonnes compactes cohérentes", all(len(v) == 2 for v in r.values()) and r["b"] == [100, 0] and r["f"] == [0, 5000] and p["orgs"] == ["A", "B"] and p["kinds"][r["k"][1]] == "hrp")


def test_main_with_mocks():
    import shutil
    units = common.read_units("demo")
    leaf = units[units.level == 4].iloc[3]
    inputs = ROOT / "inputs" / "reponses_humanitaires.csv"
    had = inputs.exists()
    if had:
        shutil.copy(inputs, inputs.with_suffix(".bak"))
    inputs.parent.mkdir(exist_ok=True)
    inputs.write_text(f"date_debut,pcode,cluster,organisation,beneficiaires\n2022-02-01,{leaf.pcode},WASH,ONG X,300\n", encoding="utf-8")
    glide = pd.DataFrame([{"glidenumber": "FL-2022-1", "event": "FL", "event_name": "flood", "year": 2022, "month": 2, "day": 3, "latitude": leaf.lat, "longitude": leaf.lon,
                           "affected": 5000, "killed": 1, "homeless": 0, "comments": "Inondations"}])
    orig_fetch = BH.fetch_csv
    orig_hdx = BH.hdx_resources
    BH.fetch_csv = lambda ds, pick, label: glide if label == "GLIDE" else None
    BH.hdx_resources = lambda ds: []
    sys.argv = ["build_history.py", "--country", "demo"]
    try:
        BH.main()
    finally:
        BH.fetch_csv, BH.hdx_resources = orig_fetch, orig_hdx
        inputs.unlink()
        if had:
            shutil.move(str(inputs.with_suffix(".bak")), inputs)
    out = json.loads((common.country_docs_dir("demo") / "response.json").read_text(encoding="utf-8"))
    check("sortie : événement placé dans le bon fokontany", len(out["events"]) == 1 and out["events"][0]["u"] == leaf.pcode and out["events"][0]["affected"] == 5000)
    check("sortie : import 3W présent avec sa source", out["rec"]["b"] == [300] and out["sources"][-1]["id"] == "3w")
    check("sortie : notes de prudence sur les sources", any("bénéficiaires" in n for n in out["notes"]))


if __name__ == "__main__":
    test_parsers_and_merge()
    test_clusters()
    test_iati_hrp_3w()
    test_locate_and_pack()
    test_main_with_mocks()
    print("\nTous les tests d'historique passent." if not FAILS else f"\n{FAILS} ÉCHEC(S)")
    sys.exit(1 if FAILS else 0)
