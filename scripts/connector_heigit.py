"""Connecteur HeiGIT / HDX : accessibilité aux services (santé, écoles) et aux routes, au niveau district.

Source : « Madagascar - Risk Assessment Indicators » (HeiGIT, Université de Heidelberg ; HDX), produit par le pipeline GAIA à partir de
WorldPop, OpenStreetMap et Google Earth Engine, sur les limites COD-AB. Données ouvertes. Temps de trajet calculés sur le réseau routier d'OpenStreetMap.
Indicateurs (district ; les régions sont déduites par moyenne pondérée par la population, les sous-zones héritent de la valeur du district) :
  acc_hosp_1h_pct   part de la population à moins d'1 h d'un hôpital
  acc_phc_1h_pct    part de la population à moins d'1 h d'un centre de santé de base
  acc_edu_5km_pct   part de la population à moins de 5 km d'une école
  rai_pct           indice d'accès rural (part de la population rurale à moins de 2 km d'une route praticable toute l'année), calcul HeiGIT
  pop_no_hosp_2h    personnes à plus de 2 h d'un hôpital (nombre, non hérité par les sous-zones)
Limites : un réseau OpenStreetMap incomplet sous-estime l'accès ; temps théoriques (hors saison des pluies, état réel des routes, pannes de bac).
Sortie : data/<pays>/external/heigit.csv (pcode, indicateur, valeur, date, source). Usage : python scripts/connector_heigit.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import io

import pandas as pd
import requests

from common import country_data_dir

BASE = "https://hot.storage.heigit.org/heigit-hdx-public/risk_assessment_inputs/mdg/"
SOURCE = "HeiGIT GAIA (WorldPop, OpenStreetMap) via HDX : Madagascar Risk Assessment Indicators"


def fetch(name: str) -> pd.DataFrame:
    r = requests.get(BASE + name, timeout=180, headers={"User-Agent": "MakyClimat"})
    r.raise_for_status()
    return pd.read_csv(io.BytesIO(r.content))


def build(access: pd.DataFrame, demo: pd.DataFrame, coping: pd.DataFrame | None = None) -> pd.DataFrame:
    """Indicateurs par district à partir des tableaux HeiGIT."""
    a = access.set_index("ADM2_PCODE")
    tot = demo.set_index("ADM2_PCODE")["total_pop"]
    rows = []

    def pct(col, ind):
        if col not in a.columns:
            return
        for pc, v in a[col].items():
            t = tot.get(pc)
            if t and t > 0 and pd.notna(v):
                rows.append((pc, ind, round(min(100.0, 100.0 * float(v) / float(t)), 1)))
    pct("access_pop_hospitals_1h", "acc_hosp_1h_pct")
    pct("access_pop_primary_healthcare_1h", "acc_phc_1h_pct")
    pct("access_pop_education_5km", "acc_edu_5km_pct")
    if "access_pop_hospitals_2h" in a.columns:
        for pc, v in a["access_pop_hospitals_2h"].items():
            t = tot.get(pc)
            if t and pd.notna(v):
                rows.append((pc, "pop_no_hosp_2h", int(round(max(0.0, float(t) - float(v))))))
    if coping is not None and "RAI_total_pop" in coping.columns:
        for pc, v in coping.set_index("ADM2_PCODE")["RAI_total_pop"].items():
            if pd.notna(v):
                rows.append((pc, "rai_pct", round(float(v), 1)))
    df = pd.DataFrame(rows, columns=["pcode", "indicateur", "valeur"])
    df["date"] = dt.date.today().isoformat()
    df["source"] = SOURCE
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    if args.country != "mdg":
        print("Connecteur HeiGIT : seul Madagascar est configuré.")
        return
    df = build(fetch("MDG_ADM2_access.csv"), fetch("MDG_ADM2_demographics.csv"), fetch("MDG_ADM2_coping.csv"))
    out = country_data_dir(args.country) / "external"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "heigit.csv", index=False)
    print(f"HeiGIT : {len(df)} valeurs pour {df.pcode.nunique()} districts")


if __name__ == "__main__":
    main()
