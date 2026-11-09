"""Chlorure de la pluie à Kwale (Kenya) : agrégats par station.

Source : Ferrer N., Folch A., Thomas M. (2019). Gro for GooD project Chloride rainwater results,
Kwale County, Kenya [Data set]. British Geological Survey. doi:10.5285/e5c1dd99-f97b-4670-9d78-c2ae6133a722.
Licence : Open Government Licence (« Contains data supplied by UKRI » / « by permission of NERC »).

Entrées (hors dépôt, data/*/chlorure_pluie_raw/ ignoré par git) :
  argv[1] : GroforGooD_Rainwater_Chloride_ARCH.xlsx (BGS, accession 125757)
  argv[2] : ne_10m_coastline.zip (Natural Earth 10 m, domaine public)
Sortie : JSON des agrégats sur stdout (valeurs agrégées seulement).

Méthode :
- coordonnées UTM Arc 1960 zone 37S (EPSG:21037) converties en WGS84 ;
- distance à la côte : distance euclidienne en UTM 37S WGS84 (EPSG:32737) au trait de côte Natural Earth 10 m
  (précision de l'ordre de 0,5 à 1 km : trait généralisé, criques et mangroves simplifiées) ;
- chlorure moyen pondéré par la pluie : somme(P_i * C_i) / somme(P_i) sur les mois où P et C sont tous deux connus ;
- variante « robuste » : on écarte les mois de moins de 10 mm (échantillons concentrés par évaporation ou poussière) ;
- pluie annuelle : décembre 2016 à novembre 2017 (12 mois) ; dépôt humide = Cl pondéré x pluie annuelle.
  Les cellules « - », vides ou non numériques sont des manques.
"""
import json
import sys
import zipfile
import tempfile
import os

import openpyxl
import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import Point, box

MOIS = ["2016-04", "2016-05", "2016-06", "2016-07", "2016-08", "2016-09", "2016-10", "2016-11", "2016-12",
        "2017-01", "2017-02", "2017-03", "2017-04", "2017-05", "2017-06", "2017-07", "2017-08", "2017-09",
        "2017-10", "2017-11"]
ANNEE = MOIS[8:]  # 2016-12 à 2017-11
SEUIL_MM = 10.0


def num(v):
    return float(v) if isinstance(v, (int, float)) else None


def main(xlsx, coast_zip):
    wb = openpyxl.load_workbook(xlsx, data_only=True)
    ws = wb["Results Rainfall and Cl"]
    rows = [r for r in ws.iter_rows(values_only=True)]
    stations = []
    for i, r in enumerate(rows):
        if r[0] and r[4] == "rain mm":
            cl = rows[i + 1]
            assert cl[4] == "Cl mg/l"
            stations.append(dict(code=r[0], nom=r[1].strip(), x=r[2], y=r[3],
                                 P=[num(v) for v in r[5:25]], C=[num(v) for v in cl[5:25]]))

    to_wgs = Transformer.from_crs("EPSG:21037", "EPSG:4326", always_xy=True)
    to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32737", always_xy=True)
    with tempfile.TemporaryDirectory() as td:
        zipfile.ZipFile(coast_zip).extractall(td)
        shp = [f for f in os.listdir(td) if f.endswith(".shp")][0]
        coast = gpd.read_file(os.path.join(td, shp), bbox=(38.5, -5.5, 40.5, -3.5))
    coast_utm = coast.to_crs("EPSG:32737").geometry.union_all()

    out = []
    for s in stations:
        lon, lat = to_wgs.transform(s["x"], s["y"])
        ex, ny = to_utm.transform(lon, lat)
        dist = Point(ex, ny).distance(coast_utm) / 1000.0
        paires = [(m, p, c) for m, p, c in zip(MOIS, s["P"], s["C"]) if p is not None and c is not None]
        n_cl = sum(c is not None for c in s["C"])

        def wmean(pp):
            sp = sum(p for _, p, _ in pp)
            return (sum(p * c for _, p, c in pp) / sp if sp > 0 else None), sp

        cw, p_couv = wmean(paires)
        rob = [t for t in paires if t[1] >= SEUIL_MM]
        cw_rob, _ = wmean(rob)
        p_tot = sum(p for p in s["P"] if p is not None)
        n_p_manq = sum(p is None for p in s["P"])
        p_an_vals = [p for m, p in zip(MOIS, s["P"]) if m in ANNEE]
        p_an = sum(v for v in p_an_vals if v is not None)
        an_complet = all(v is not None for v in p_an_vals)
        douteux = []
        for m, p, c in zip(MOIS, s["P"], s["C"]):
            if c is not None and p is not None and p < SEUIL_MM:
                douteux.append(f"{m} : Cl {c:.1f} mg/L pour {p:g} mm de pluie")
            elif c is not None and c > 15:
                douteux.append(f"{m} : Cl {c:.1f} mg/L (valeur forte)")
            elif c is not None and p is None:
                douteux.append(f"{m} : Cl {c:.1f} mg/L sans pluie mesurée (non utilisé)")
        out.append(dict(
            code=s["code"], nom=s["nom"], lon=round(lon, 4), lat=round(lat, 4),
            distance_cote_km=round(dist, 1),
            n_echantillons_cl=n_cl, n_mois_pluie_et_cl=len(paires),
            cl_pondere_mg_L=round(cw, 2) if cw else None,
            cl_pondere_sans_mois_lt10mm_mg_L=round(cw_rob, 2) if cw_rob else None,
            part_pluie_couverte_par_cl=round(p_couv / p_tot, 2) if p_tot else None,
            pluie_periode_mm=round(p_tot, 1), mois_pluie_manquants=n_p_manq,
            pluie_dec2016_nov2017_mm=round(p_an, 1), annee_complete=an_complet,
            depot_humide_mg_m2_an=round(cw * p_an, 0) if cw else None,
            depot_humide_sans_mois_lt10mm_mg_m2_an=round(cw_rob * p_an, 0) if cw_rob else None,
            echantillons_douteux=douteux,
        ))
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
