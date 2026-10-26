"""Indice de vulnérabilité cumulative par fokontany (expérimental).

Ce que c'est : un score 0-100 qui résume les chocs climatiques (cyclones, sécheresse) accumulés
par chaque fokontany sur les ~3 dernières années, le plus récent comptant davantage (demi-vie 18 mois).
Idée : une zone déjà frappée récemment a moins de réserve pour encaisser un nouveau choc, même si
la saison en cours est, prise isolément, normale.

Ce que ce n'est PAS : une mesure du pouvoir d'achat, de l'inflation locale ou de la résilience réelle
des ménages. Aucune de ces données n'est disponible par fokontany à ce jour (voir la fiche « Ce dont
nous avons besoin »). L'indice ne combine que des aléas physiques déjà calculés par MakyClimat.
Niveau de preuve : approximation (construction raisonnée, calibrage non testé sur des enquêtes de
vulnérabilité réelles ; voir validation/vuln_cumul_limites.md).

Entrées :
  validation/chocs_cyclones_fokontany.csv  (classe de vent + date de passage, par fokontany, historique complet)
  validation/spi_regions.csv               (SPI-3 mensuel par région, depuis 2014)
  data/<pays>/units.csv                    (hiérarchie des unités, pour relier fokontany <-> région)
Sortie :
  data/<pays>/external/vuln_cumul.csv : pcode, vuln_cumul_idx (0-100), vuln_cumul_cyc (0-100),
  vuln_cumul_sech (0-100), vuln_cumul_n_chocs (nombre de chocs comptés dans la fenêtre)
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd

from common import DATA_DIR, country_data_dir, read_units

HALF_LIFE_DAYS = 548.0          # ~18 mois : un choc vieux de 18 mois pèse moitié moins qu'un choc d'aujourd'hui
WINDOW_DAYS = 365.25 * 3.5      # on ne regarde pas au-delà de ~3,5 ans (au-delà, poids négligeable de toute façon)
WIND_SEVERITY = {34: 20, 50: 45, 64: 65, 83: 80, 96: 90, 113: 100, 137: 100}  # kt -> sévérité 0-100 (Saffir-Simpson-like)
SPI_SEVERITY = {-1.0: 25, -1.5: 55, -2.0: 85}  # seuil SPI (OMM) -> sévérité 0-100 ; interpolation linéaire en dessous


def recency_weight(days_ago: float) -> float:
    if days_ago < 0 or days_ago > WINDOW_DAYS:
        return 0.0
    return float(2 ** (-days_ago / HALF_LIFE_DAYS))


def wind_severity(kt) -> float:
    try:
        kt = float(kt)
    except (TypeError, ValueError):
        return 0.0
    best = 0.0
    for thr, sev in WIND_SEVERITY.items():
        if kt >= thr:
            best = max(best, sev)
    return best


def spi_severity(spi) -> float:
    try:
        spi = float(spi)
    except (TypeError, ValueError):
        return 0.0
    if not np.isfinite(spi) or spi > -1.0:
        return 0.0
    if spi <= -2.0:
        return 85.0 + min(15.0, (-spi - 2.0) * 10.0)  # au-delà de -2 (extrême), plafonne vers 100
    if spi <= -1.5:
        return 55.0 + (-spi - 1.5) / 0.5 * 30.0
    return 25.0 + (-spi - 1.0) / 0.5 * 30.0


def cumulative_score(weighted_sevs: list[float]) -> float:
    """Combine plusieurs chocs pondérés : pas une simple somme (saturerait vite), un max amorti par les suivants.
    Le choc le plus lourd compte plein ; chaque choc suivant ajoute un reliquat, pour refléter l'épuisement
    de la capacité de résistance sans dépasser 100."""
    if not weighted_sevs:
        return 0.0
    weighted_sevs = sorted(weighted_sevs, reverse=True)
    score, remaining = 0.0, 100.0
    for s in weighted_sevs:
        add = min(s, remaining) * 0.6 if score > 0 else s
        score = min(100.0, score + add)
        remaining = 100.0 - score
        if remaining <= 0.5:
            break
    return round(score, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--today", default=None, help="date de référence (AAAA-MM-JJ), défaut = aujourd'hui")
    args = ap.parse_args()
    slug = args.country
    today = pd.Timestamp(args.today) if args.today else pd.Timestamp(dt.date.today())

    units = read_units(slug)
    leaves = units[units.level == units.level.max()].copy()
    pc_to_adm1 = dict(zip(units.pcode, units.adm1))

    cyc_path = DATA_DIR.parent / "validation" / "chocs_cyclones_fokontany.csv"
    spi_path = DATA_DIR.parent / "validation" / "spi_regions.csv"

    by_pc: dict[str, list[float]] = {pc: [] for pc in leaves.pcode}
    n_cyc: dict[str, int] = {pc: 0 for pc in leaves.pcode}
    n_sech: dict[str, int] = {pc: 0 for pc in leaves.pcode}
    cyc_only: dict[str, list[float]] = {pc: [] for pc in leaves.pcode}
    sech_only: dict[str, list[float]] = {pc: [] for pc in leaves.pcode}

    if cyc_path.exists():
        cyc = pd.read_csv(cyc_path, dtype={"pcode": str})
        cyc["date_passage"] = pd.to_datetime(cyc["date_passage"], errors="coerce")
        cyc = cyc.dropna(subset=["date_passage"])
        cyc["days_ago"] = (today - cyc["date_passage"]).dt.days
        cyc = cyc[(cyc.days_ago >= 0) & (cyc.days_ago <= WINDOW_DAYS)]
        for r in cyc.itertuples():
            if r.pcode not in by_pc:
                continue
            w = recency_weight(r.days_ago) * wind_severity(r.vent_classe_kt)
            if w <= 0:
                continue
            by_pc[r.pcode].append(w)
            cyc_only[r.pcode].append(w)
            n_cyc[r.pcode] += 1
    else:
        print(f"  (pas de {cyc_path} : score cyclone = 0 pour tous)")

    if spi_path.exists():
        spi = pd.read_csv(spi_path, dtype={"adm1": str})
        spi["date"] = pd.to_datetime(spi["mois"] + "-15", errors="coerce")
        spi = spi.dropna(subset=["date"]).sort_values(["adm1", "date"])
        # Une sécheresse dure plusieurs mois d'affilée : on regroupe les mois consécutifs sous le seuil
        # en UN SEUL épisode (sévérité = son pic, date = celle du pic), pour ne pas compter plusieurs fois
        # la même sécheresse comme autant de chocs indépendants.
        by_adm1: dict[str, list[tuple[float, float]]] = {}
        for a1, g in spi.groupby("adm1"):
            g = g.reset_index(drop=True)
            dry = g["spi3"] <= -1.0
            ep_id = (dry != dry.shift(fill_value=False)).cumsum()
            for _, ep in g[dry].groupby(ep_id[dry]):
                peak = ep.loc[ep["spi3"].idxmin()]
                sev = spi_severity(peak["spi3"])
                days_ago = (today - peak["date"]).days
                if sev > 0 and 0 <= days_ago <= WINDOW_DAYS:
                    by_adm1.setdefault(a1, []).append((days_ago, sev))
        for pc in leaves.pcode:
            a1 = pc_to_adm1.get(pc)
            for days_ago, sev in by_adm1.get(a1, []):
                w = recency_weight(days_ago) * sev
                if w <= 0:
                    continue
                by_pc[pc].append(w)
                sech_only[pc].append(w)
                n_sech[pc] += 1
    else:
        print(f"  (pas de {spi_path} : score sécheresse = 0 pour tous)")

    rows = []
    for pc in leaves.pcode:
        idx = cumulative_score(by_pc[pc])
        rows.append({
            "pcode": pc,
            "vuln_cumul_idx": idx,
            "vuln_cumul_cyc": cumulative_score(cyc_only[pc]),
            "vuln_cumul_sech": cumulative_score(sech_only[pc]),
            "vuln_cumul_n_chocs": n_cyc[pc] + n_sech[pc],
        })
    out = pd.DataFrame(rows)
    out_path = country_data_dir(slug) / "external" / "vuln_cumul.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    nz = (out.vuln_cumul_idx > 0).sum()
    print(f"  vuln_cumul : {len(out)} fokontany, {nz} avec un score > 0, écrit dans {out_path}")


if __name__ == "__main__":
    main()
