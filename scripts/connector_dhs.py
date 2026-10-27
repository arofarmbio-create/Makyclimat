"""Connecteur DHS Program (ICF, USAID) : eau, assainissement, nutrition de l'enfant et santé maternelle et infantile, par région.

Source : API publique DHS (api.dhsprogram.com), enquête démographique et de santé la plus récente de Madagascar disposant de l'indicateur (en général EDS 2021).
Indicateurs (pourcentages, niveau région ; les districts, communes et fokontany reprennent la valeur de leur région) :
  dhs_eau_amelioree      population utilisant une source d'eau améliorée
  dhs_toilettes_amel     ménages ou population utilisant des toilettes améliorées
  dhs_sans_toilettes     ménages sans toilettes (défécation à l'air libre)
  dhs_lavage_mains       ménages avec un dispositif de lavage des mains avec eau et savon (basique)
  dhs_retard_croissance  enfants de moins de 5 ans avec retard de croissance (taille pour âge < -2 ET)
  dhs_emaciation         enfants de moins de 5 ans émaciés (poids pour taille < -2 ET)
  dhs_insuf_ponderale    enfants de moins de 5 ans en insuffisance pondérale
  dhs_diarrhee           enfants de moins de 5 ans ayant eu la diarrhée dans les 2 semaines précédentes
  dhs_vaccination_base   enfants de 12-23 mois avec tous les vaccins de base
  dhs_accouch_formation  naissances en établissement de santé
  dhs_cpn4               femmes avec 4 consultations prénatales ou plus
  dhs_electricite        ménages avec électricité
  dhs_femmes_enceintes_pct  % des femmes de 15-49 ans actuellement enceintes (sert aussi, combiné à la part
                            nationale de femmes de 15-49 ans dans la population -- voir compute_metrics.py et
                            femmes_15_49_pct dans config/countries/<pays>.yml -- à estimer un nombre de femmes
                            enceintes dans la population exposée ; approximation à deux hypothèses empilées,
                            jamais une mesure directe par fokontany)
Limites : enquête par sondage représentative au niveau région (pas district) ; les valeurs datent de l'année d'enquête (indiquée) ; la région Ambatosoa, créée après
l'enquête, n'a pas de valeur propre ; les identifiants DHS candidats sont testés dans l'ordre et la première série disponible est utilisée (journal du connecteur).
Sortie : data/<pays>/external/dhs.csv (pcode, indicateur, valeur, date, source). Usage : python scripts/connector_dhs.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import unicodedata

import pandas as pd
import requests

from common import country_data_dir, read_units

API = "https://api.dhsprogram.com/rest/dhs"
SPECS = {
    "dhs_eau_amelioree": ["WS_SRCE_P_IMP", "WS_SRCE_H_IMP"],
    "dhs_toilettes_amel": ["WS_TLET_P_IMP", "WS_TLET_H_IMP", "WS_TLET_P_BAS", "WS_TLET_H_BAS"],
    "dhs_sans_toilettes": ["WS_TLET_H_NFC", "WS_TLET_P_NFC"],
    "dhs_lavage_mains": ["WS_HNDW_H_BAS", "WS_HNDW_P_BAS", "WS_HNDW_H_SOP"],
    "dhs_retard_croissance": ["CN_NUTS_C_HA2"],
    "dhs_emaciation": ["CN_NUTS_C_WH2"],
    "dhs_insuf_ponderale": ["CN_NUTS_C_WA2"],
    "dhs_diarrhee": ["CH_DIAR_C_DIA"],
    "dhs_vaccination_base": ["CH_VACC_C_BAS"],
    "dhs_accouch_formation": ["RH_DELP_C_DHF"],
    "dhs_cpn4": ["RH_ANCN_W_N4P"],
    "dhs_electricite": ["HC_ELEC_H_ELC"],
    "dhs_femmes_enceintes_pct": ["FE_FRTY_W_PRG"],
}
SOURCE = "DHS Program (ICF), enquête auprès des ménages, représentative au niveau région"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)


def _get(path: str, params: dict) -> list[dict]:
    r = requests.get(f"{API}/{path}", params=dict(params, f="json"), timeout=120, headers={"User-Agent": "MakyClimat (recherche doctorale)"})
    r.raise_for_status()
    return r.json()["Data"]


def fetch(country_id: str = "MD") -> list[dict]:
    ids = ",".join(sorted({i for c in SPECS.values() for i in c}))
    return _get("data", {"countryIds": country_id, "indicatorIds": ids, "breakdown": "subnational", "perpage": 5000})


def build(data: list[dict], units: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Valeurs par région : pour chaque indicateur, le premier identifiant candidat disponible, enquête la plus récente. Retourne (lignes, journal)."""
    log = []
    reg = units[units.level == 1][["pcode", "name"]]
    by_name = {norm(n): p for p, n in zip(reg.pcode, reg.name)}
    # certaines régions ont été regroupées dans l'enquête : un libellé DHS peut couvrir plusieurs de nos régions
    # libellés regroupés ou mal orthographiés dans l'enquête (relevés dans les données DHS)
    alias = {"vatovavyfitovinany": ["vatovavy", "fitovinany"], "anamoroniimania": ["amoronimania"], "vakinankarata": ["vakinankaratra"]}
    df = pd.DataFrame(data)
    if df.empty:
        return pd.DataFrame(columns=["pcode", "indicateur", "valeur", "date", "source"]), ["aucune donnée DHS"]
    df = df[(df.CharacteristicCategory == "Region") & (df.Value.notna())]
    rows, unmatched = [], set()
    for ind, cands in SPECS.items():
        got = None
        for c in cands:
            d = df[df.IndicatorId == c]
            if "IsPreferred" in d.columns and len(d):      # plusieurs dénominateurs possibles : série « préférée » de la DHS (à défaut, toutes)
                pref = d[d.IsPreferred.fillna(1) == 1]
                d = pref if len(pref) else d
            if len(d):
                got = (c, d)
                break
        if got is None:
            log.append(f"{ind} : aucun identifiant DHS disponible parmi {cands}")
            continue
        c, d = got
        year = int(d.SurveyYear.max())
        d = d[d.SurveyYear == year].drop_duplicates(subset=["CharacteristicLabel"])
        n = 0
        for lab, v in zip(d.CharacteristicLabel, d.Value):
            keys = alias.get(norm(lab), [norm(lab)])
            hit = [by_name[k] for k in keys if k in by_name]
            if not hit:
                unmatched.add(lab)
            for pc in hit:
                rows.append((pc, ind, float(v), str(year), f"{SOURCE} ({c}, {year})"))
                n += 1
        log.append(f"{ind} : {c}, enquête {year}, {n} régions")
    if unmatched:
        log.append("régions DHS sans correspondance : " + ", ".join(sorted(unmatched)))
    return pd.DataFrame(rows, columns=["pcode", "indicateur", "valeur", "date", "source"]), log


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    if args.country != "mdg":
        print("Connecteur DHS : seul Madagascar est configuré.")
        return
    df, log = build(fetch("MD"), read_units(args.country))
    print("\n".join(log))
    out = country_data_dir(args.country) / "external"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "dhs.csv", index=False)
    print(f"DHS : {len(df)} valeurs pour {df.pcode.nunique()} régions ({dt.date.today().isoformat()})")


if __name__ == "__main__":
    main()
