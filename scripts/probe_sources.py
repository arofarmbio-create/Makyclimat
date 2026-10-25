"""Sondage de sources depuis GitHub Actions : le résultat est écrit dans data/_probe.txt (lisible dans le dépôt)."""
import io
import json
import sys

import pandas as pd
import requests

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
out = []


def note(msg):
    print(msg)
    out.append(str(msg))


def attempt(name, fn):
    try:
        fn()
    except Exception as e:
        note(f"== {name} ECHEC {type(e).__name__}: {str(e)[:500]}")


def heigit():
    base = "https://hot.storage.heigit.org/heigit-hdx-public/risk_assessment_inputs/mdg/"
    for f in ["MDG_ADM2_flood_exposure.csv"]:
        df = pd.read_csv(io.BytesIO(requests.get(base + f, headers=UA, timeout=120).content))
        note(f"== {f} {df.shape}\ncolonnes: {list(df.columns)}")
        note(df.head(3).T.to_string(max_colwidth=40)[:4000])


def ibtracs():
    u = "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.SI.list.v04r01.csv"
    r = requests.get(u, headers=UA, timeout=300)
    note(f"== IBTrACS SI HTTP {r.status_code}, {len(r.content)/1e6:.1f} Mo")
    df = pd.read_csv(io.BytesIO(r.content), skiprows=[1], low_memory=False)
    note(f"colonnes ({df.shape}): {list(df.columns)[:60]}")
    note(f"saisons {df.SEASON.min()}–{df.SEASON.max()} ; tempêtes {df.SID.nunique()} ; dernières dates {df.ISO_TIME.max()}")
    note(df[["SID", "NAME", "ISO_TIME", "LAT", "LON", "USA_WIND", "WMO_WIND", "USA_R34_NE", "REUNION_WIND", "TRACK_TYPE"]].tail(3).to_string())


def seasonal():
    base = "https://seasonal-api.open-meteo.com/v1/seasonal"
    for params in [
        {"monthly": "precipitation_mean,precipitation_anomaly"},
        {"monthly": "precipitation_sum"},
        {"six_hourly": "precipitation", "forecast_days": 3},
        {"daily": "precipitation_sum", "forecast_days": 3},
    ]:
        r = requests.get(base, params=dict({"latitude": -18.9, "longitude": 47.5, "timezone": "auto"}, **params), headers=UA, timeout=120)
        note(f"== seasonal {params} -> HTTP {r.status_code} {r.text[:700]}")


def dhs():
    r = requests.get("https://api.dhsprogram.com/rest/dhs/surveys", params={"countryIds": "MD", "f": "json"}, headers=UA, timeout=60)
    note("== DHS surveys MD: " + json.dumps([(s["SurveyId"], s["SurveyYear"], s.get("SurveyType")) for s in r.json()["Data"]]))
    r = requests.get("https://api.dhsprogram.com/rest/dhs/indicators", params={"f": "json", "perpage": 3000}, headers=UA, timeout=60)
    ind = r.json()["Data"]
    keys = ("water", "sanitation", "stunt", "wast", "underweight", "diarr", "vaccin", "fever", "skilled", "antenatal", "electric")
    sel = [(i["IndicatorId"], i["Label"]) for i in ind if any(k in i["Label"].lower() for k in keys) and i.get("MeasurementType") == "Percent"]
    note(f"== DHS indicateurs ({len(ind)}), sélection {len(sel)}: " + json.dumps(sel[:60], ensure_ascii=False))
    r = requests.get("https://api.dhsprogram.com/rest/dhs/data", params={"countryIds": "MD", "indicatorIds": "WS_SRCE_P_IMP", "breakdown": "subnational", "f": "json", "perpage": 100}, headers=UA, timeout=60)
    d = r.json()["Data"]
    note(f"== DHS data WS_SRCE_P_IMP {len(d)} lignes ; exemple : " + json.dumps(d[:3], ensure_ascii=False)[:900])


attempt("HeiGIT crues", heigit)
attempt("IBTrACS", ibtracs)
attempt("Saisonnier", seasonal)
attempt("DHS", dhs)
open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
sys.exit(0)
