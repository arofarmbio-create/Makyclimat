"""Inventaire de la base BushProof / DDC « Contribution à l'hydrogéologie du Sud de Madagascar » (2023).

Lit les geopackages rangés hors git dans data/mdg/bushproof_raw/. Un geopackage intact est lu par sqlite3 ; un
geopackage tronqué (copies Wayback Machine coupées à 1 Mio) est lu partiellement par scripts/sqlite_tronque.py, et
chaque couche porte alors un indicateur « complete ».

Écrit :
- <sortie_json> (data/mdg/bushproof_inventaire.json) : fichiers, couches, colonnes, effectifs ; aucune donnée brute ;
- <sortie_scellee> (data/mdg/bushproof_inventaire_cl_scelle.json, hors git) : quantiles du chlorure de la nappe, NON
  affichés : validation/protocole_recharge_chlorure.md (section 4) impose de fixer le dépôt de chlorure avant toute
  lecture des chlorures de la nappe.

Usage : python -I -X utf8 scripts/bushproof_inventaire.py <dossier_brut> <sortie_json> <sortie_scellee>
"""
import importlib.util
import json
import re
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

_spec = importlib.util.spec_from_file_location("sqlite_tronque", Path(__file__).with_name("sqlite_tronque.py"))
st = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(st)

# effectifs annoncés sur https://hydro-madagascar.weebly.com/hydrogeacuteologie.html (lu le 09/11/2026)
ANNONCES = {"Zones hydrogéologiques": 4, "Forages": 2880, "piézométrie générale": 1832, "Econd générale": 2048,
            "piézométrie basses eaux": 734, "Econd basses eaux": 1039, "piézométrie hautes eaux": 215,
            "Econd hautes eaux": 338}


def num(v):
    if v is None or isinstance(v, bytes):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", ".")
    if not s or s[0] in "<>":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def filled(v):
    return v is not None and not isinstance(v, bytes) and str(v).strip() not in ("", "-", "NULL", "nan", "None")


def censored(v):
    return isinstance(v, str) and v.strip()[:1] in "<>"


def quantiles(vals):
    vals = sorted(v for v in vals if v is not None)
    if len(vals) < 3:
        return {"n": len(vals)}
    q = statistics.quantiles(vals, n=10, method="inclusive")
    return {"n": len(vals), "q10": round(q[0], 2), "q50": round(statistics.median(vals), 2), "q90": round(q[8], 2)}


def load(raw):
    """{fichier: {"etat": ..., "couches": {nom: {"colonnes", "lignes" (liste de dict), "complete"}}}}"""
    out = {}
    for f in sorted(raw.glob("*.gpkg")):
        info = {"octets": f.stat().st_size, "couches": {}}
        try:
            con = sqlite3.connect(f"file:{f}?mode=ro", uri=True)
            con.execute("pragma integrity_check").fetchall()
            names = [r[0] for r in con.execute("select table_name from gpkg_contents")]
            for n in names:
                cols = [r[1] for r in con.execute(f'pragma table_info("{n}")')]
                rows = [dict(zip(cols, r)) for r in con.execute(f'select * from "{n}"')]
                info["couches"][n] = {"colonnes": cols, "lignes": rows, "complete": True}
            info["etat"] = "intact"
            con.close()
        except sqlite3.DatabaseError as e:
            summ, tables, rows = st.recover(f)
            info["etat"] = f"tronqué ({e}) : {summ['pages_presentes']} pages sur {summ['pages_annoncees']}"
            for n, t in summ["tables"].items():
                if n == "layer_styles":
                    continue
                cols = tables[n]
                info["couches"][n] = {"colonnes": cols,
                                      "lignes": [dict(zip(cols, v)) for v in rows[n].values()],
                                      "complete": t["pages_absentes_sous_la_racine"] == 0}
        out[f.name] = info
    return out


def col(cols, *pats):
    for p in pats:
        for c in cols:
            if re.fullmatch(p, c, flags=re.I):
                return c
    return None


def forage_stats(rows, cols):
    c = {k: col(cols, *p) for k, p in {
        "id": [r"ID"], "region": [r"R[ée]gion"], "cl": [r"Cl-?_mg/l"], "datechim": [r"DateChimie"],
        "no3": [r"NO3-*_mg/l"], "swl": [r"SWL_m"], "dateswl": [r"DateSWL"], "ec": [r"EC_.*"],
        "q1": [r"QPal1_m3/h"], "r1": [r"Rabat1_m"], "qexpl": [r"Qexpl_m3/h"], "lat": [r"Lat_DD"],
        "lon": [r"Long?_DD"], "ta1": [r"TypeAquif1"], "na": [r"Na\+?_mg/l"], "ca": [r"Ca\+*_mg/l"],
        "mg": [r"Mg\+*_mg/l"], "k": [r"K\+?_mg/l"], "hco3": [r"HCO3-?_mg/l"], "so4": [r"SO4-*_mg/l"],
        "co3": [r"CO3-*_mg/l"]}.items()}
    r = {"colonnes_cles": c, "n_lignes": len(rows)}
    xs = [num(x.get(c["lon"])) for x in rows]
    ys = [num(x.get(c["lat"])) for x in rows]
    pts = [(a, b) for a, b in zip(xs, ys) if a and b]
    if pts:
        r["emprise"] = {"lon_min": min(p[0] for p in pts), "lon_max": max(p[0] for p in pts),
                        "lat_min": min(p[1] for p in pts), "lat_max": max(p[1] for p in pts), "n": len(pts)}
    clpos = [x for x in rows if (num(x.get(c["cl"])) or 0) > 0]
    r["cl_renseigne"] = sum(filled(x.get(c["cl"])) for x in rows)
    r["cl_mesure_positif"] = len(clpos)
    r["cl_censure"] = sum(censored(x.get(c["cl"])) for x in rows)
    r["cl_positif_avec_date_chimie"] = sum(filled(x.get(c["datechim"])) for x in clpos)
    r["date_chimie"] = sum(filled(x.get(c["datechim"])) for x in rows)
    r["nitrate_mesure"] = sum(num(x.get(c["no3"])) is not None for x in rows)
    r["cl_positif_avec_nitrate"] = sum(num(x.get(c["no3"])) is not None for x in clpos)
    r["ec_mesuree"] = sum(num(x.get(c["ec"])) is not None for x in rows)

    def typ(x):
        v = x.get(c["ta1"])
        return str(v).strip().lower() if filled(v) else "non renseigné"
    r["type_aquifere_1"] = dict(Counter(typ(x) for x in rows).most_common())
    r["type_aquifere_1_cl_positif"] = dict(Counter(typ(x) for x in clpos).most_common())
    r["region_cl_positif"] = dict(Counter(str(x.get(c["region"])).strip() for x in clpos).most_common())
    r["niveau_statique"] = sum(num(x.get(c["swl"])) is not None for x in rows)
    r["niveau_statique_avec_date"] = sum(num(x.get(c["swl"])) is not None and filled(x.get(c["dateswl"]))
                                         for x in rows)
    r["essai_pompage_debit_et_rabattement_palier1"] = sum(
        num(x.get(c["q1"])) is not None and num(x.get(c["r1"])) is not None for x in rows)
    r["debit_exploitation"] = sum(num(x.get(c["qexpl"])) is not None for x in rows)
    # contrôle d'unité du chlorure : balance ionique calculée en supposant des mg/L
    eqw = {"ca": 20.04, "mg": 12.15, "na": 22.99, "k": 39.10, "hco3": 61.02, "so4": 48.03, "co3": 30.00,
           "cl": 35.45}
    errs = []
    for x in rows:
        v = {k: num(x.get(c[k])) if c[k] else None for k in eqw}
        if all(v[k] is not None for k in ("ca", "mg", "na", "cl", "hco3")) and v["cl"] > 0:
            cat = sum((v[k] or 0) / eqw[k] for k in ("ca", "mg", "na", "k"))
            an = sum((v[k] or 0) / eqw[k] for k in ("hco3", "so4", "co3", "cl"))
            if cat + an > 0:
                errs.append(100 * (cat - an) / (cat + an))
    if errs:
        r["balance_ionique_en_supposant_mg_l"] = {
            "n": len(errs), "erreur_mediane_pct": round(statistics.median(errs), 1),
            "part_erreur_abs_moins_10pct": round(sum(abs(e) < 10 for e in errs) / len(errs), 2)}
    sealed = {"tous": quantiles(num(x.get(c["cl"])) for x in clpos)}
    bt, br = defaultdict(list), defaultdict(list)
    for x in clpos:
        bt[typ(x)].append(num(x.get(c["cl"])))
        br[str(x.get(c["region"])).strip()].append(num(x.get(c["cl"])))
    sealed["par_type_aquifere"] = {k: quantiles(v) for k, v in bt.items()}
    sealed["par_region"] = {k: quantiles(v) for k, v in br.items()}
    return r, sealed


def ids(layer):
    cid = col(layer["colonnes"], r"ID")
    return {x.get(cid) for x in layer["lignes"] if filled(x.get(cid))} if cid else set()


def main():
    raw, out_json, out_sealed = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    data = load(raw)
    inv = {"date": "2026-11-09",
           "source": "Al-Zoubaidy M., Monteleone M., Bünzli M.-A. (2023). Contribution à l'hydrogéologie du Sud de "
                     "Madagascar, base de données géoréférencées et site interactif, "
                     "https://hydro-madagascar.weebly.com/ ; éditeurs DDC (Berne) et BushProof Sàrl (Antananarivo)",
           "conditions": "Toutes les données sur ce site sont libres d'accès et peuvent être librement utilisées. Il "
                         "est par contre interdit de les vendre ou de s'en approprier la propriété intellectuelle.",
           "provenance": "Wayback Machine (captures de mars 2024) ; qgis.bushproof.com ne résout plus (NXDOMAIN)",
           "fichiers": {}}
    all_layers = {}
    for fn, info in data.items():
        inv["fichiers"][fn] = {"octets": info["octets"], "etat": info["etat"], "couches": {
            n: {"colonnes": L["colonnes"], "lignes_lues": len(L["lignes"]), "complete": L["complete"],
                "annonce_site": ANNONCES.get(n)} for n, L in info["couches"].items()}}
        for n, L in info["couches"].items():
            all_layers.setdefault(n, []).append((fn, L))
    fl = [(fn, dict(L, couche=n)) for n, v in all_layers.items() if n.lower().startswith("forage") for fn, L in v]
    sealed = {"avertissement": "Ne pas lire avant d'avoir fixé le dépôt de chlorure "
                               "(validation/protocole_recharge_chlorure.md, section 4).",
              "unite": "mg/L (nom de colonne Cl-_mg/l et page Hydrogéologie du site)"}
    if fl:
        # réunion de toutes les couches de forages (couche générale tronquée + couches par zone), sans doublon d'ID
        merged, origin = {}, Counter()
        cols = fl[0][1]["colonnes"]
        for fn, L in fl:
            cid = col(L["colonnes"], r"ID")
            for x in L["lignes"]:
                k = x.get(cid) if cid and filled(x.get(cid)) else (fn, id(x))
                if k not in merged:
                    merged[k] = x
                    origin[fn] += 1
        st_, sl = forage_stats(list(merged.values()), cols)
        st_.update({"couches_reunies": {f"{fn}:{L['couche']}": [len(L["lignes"]), "complète" if L["complete"] else "partielle"]
                                        for fn, L in fl},
                    "forages_distincts_par_fichier": dict(origin), "annonce_site": ANNONCES["Forages"]})
        st_["zones_hydro"] = dict(Counter(str(x.get("ZH_code")) for x in merged.values()))
        inv["forages"] = st_
        sealed.update({"couverture": "forages distincts réunis, voir bushproof_inventaire.json", **sl})
    # deux saisons : identifiants présents dans les couches basses eaux et hautes eaux
    two = {}
    for kind in ("piézométrie", "Econd"):
        be = [L for n, v in all_layers.items() for _, L in v if n.lower() == f"{kind} basses eaux".lower()]
        he = [L for n, v in all_layers.items() for _, L in v if n.lower() == f"{kind} hautes eaux".lower()]
        if be and he:
            a, b = set().union(*map(ids, be)), set().union(*map(ids, he))
            two[kind] = {"basses_eaux": len(a), "hautes_eaux": len(b), "les_deux": len(a & b),
                         "couches_completes": all(L["complete"] for L in be + he)}
        else:
            two[kind] = "couches absentes ou illisibles"
    inv["deux_saisons"] = two
    out_json.write_text(json.dumps(inv, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    out_sealed.write_text(json.dumps(sealed, ensure_ascii=False, indent=1), encoding="utf-8")
    # affichage sans les quantiles de chlorure
    print(json.dumps({k: v for k, v in inv.items() if k != "fichiers"}, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
