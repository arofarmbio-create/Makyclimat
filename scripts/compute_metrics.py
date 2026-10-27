"""Calcul des indicateurs MakyClimat pour toutes les unités (région -> fokontany) et écriture des fichiers du site.

Entrées : data/<pays>/units.csv (limites + population), data/<pays>/grids/season.npz (pluie),
          inputs/vulnerabilite.csv et inputs/interventions.csv (facultatifs).
Sorties : docs/data/<pays>/metrics/top.json, metrics/d/<district>.json, meta.json

Méthode (version 1, à calibrer et valider scientifiquement) :
  1. pct = pluie cumulée de la saison / normale à la même date x 100 (cellule CHIRPS au centroïde ; moyenne
     pondérée par la surface pour les unités qui ont des sous-unités).
  2. niveau d'alerte selon les seuils de la configuration (4 urgence, 3 alerte, 2 veille, 1 normal, 0 sans donnée).
  3. population exposée = population des fokontany dont le niveau >= exposure_min_level, puis cumul vers le haut.
  4. cibles potentiels = population exposée x vulnérabilité économique (part de la population la moins capable de faire face à l'aléa,
     p. ex. les ménages pauvres plus que les ménages aisés -- distinct de l'exposition géographique du point 3, qui est la même pour
     tous dans la zone ; par priorité : fichier fourni, IPC phase 3+, valeur par défaut).
  5. sensibilité : mêmes calculs avec la pluie multipliée par chaque facteur de simulation.
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt

import numpy as np
import pandas as pd

from common import (DATA_DIR, INPUTS_DIR, country_data_dir, country_docs_dir, grid_dir, load_config, load_grid, load_yaml,
                    read_units, sample_grid, write_json)


def level_from_pct(pct: np.ndarray, levels: list[dict]) -> np.ndarray:
    """0 = pas de donnée ; sinon niveau du premier seuil dépassé (du plus sévère au moins sévère)."""
    out = np.zeros(len(pct), dtype=int)
    for i, p in enumerate(pct):
        if not np.isfinite(p):
            continue
        for rule in sorted(levels, key=lambda r: -r["level"]):
            if p < rule["below_pct"]:
                out[i] = rule["level"]
                break
    return out


def read_inputs(units: pd.DataFrame, default_share: float):
    # Part vulnérable : par pcode (n'importe quel niveau)
    vs = {}
    f = INPUTS_DIR / "vulnerabilite.csv"
    if f.exists() and f.stat().st_size > 0:
        v = pd.read_csv(f, dtype={"pcode": str})
        for r in v.itertuples():
            if pd.notna(r.part_vulnerable) and 0 <= float(r.part_vulnerable) <= 1:
                vs[str(r.pcode)] = float(r.part_vulnerable)
    ben = {}
    g = INPUTS_DIR / "interventions.csv"
    if g.exists() and g.stat().st_size > 0:
        iv = pd.read_csv(g, dtype={"pcode": str})
        iv["beneficiaires"] = pd.to_numeric(iv["beneficiaires"], errors="coerce").fillna(0)
        by = iv.groupby("pcode")["beneficiaires"].sum().to_dict()
        row = units.set_index("pcode")
        for pc, b in by.items():
            if pc not in row.index:
                print(f"  intervention ignorée (pcode inconnu) : {pc}")
                continue
            r = row.loc[pc]
            # l'intervention compte pour l'unité visée et pour tous ses parents (codes distincts, sans doublon)
            codes = {pc} | {c for c in (r["adm3"], r["adm2"], r["adm1"]) if isinstance(c, str) and c}
            for code in codes:
                ben[code] = ben.get(code, 0.0) + float(b)
    return vs, ben


def read_external(slug: str, units: pd.DataFrame):
    """Indicateurs externes au format standard : colonnes pcode, indicateur, valeur, date, source.
    Lus dans inputs/indicateurs/*.csv (déposés à la main) et data/<pays>/external/*.csv (écrits par les connecteurs).
    Seuls les indicateurs déclarés dans config/indicators.yml sont retenus ; la valeur la plus récente gagne."""
    defs = {i["id"]: i for i in load_yaml("indicators.yml")["indicators"]}
    folders = [INPUTS_DIR / "indicateurs", country_data_dir(slug) / "external"]
    frames = []
    for folder in folders:
        for f in sorted(folder.glob("*.csv")) if folder.exists() else []:
            if f.stat().st_size == 0:
                continue
            df = pd.read_csv(f, dtype=str)
            if not {"pcode", "indicateur", "valeur"} <= set(df.columns):
                print(f"  fichier ignoré (colonnes pcode, indicateur, valeur requises) : {f.name}")
                continue
            df["date"] = df["date"] if "date" in df.columns else ""
            df["source"] = df["source"] if "source" in df.columns else f.name
            frames.append(df[["pcode", "indicateur", "valeur", "date", "source"]])
    if not frames:
        return {}, {}, []
    df = pd.concat(frames, ignore_index=True)
    df["valeur"] = pd.to_numeric(df["valeur"].str.replace(",", ".", regex=False), errors="coerce")
    df = df.dropna(subset=["valeur"])
    unknown = sorted(set(df.indicateur) - set(defs))
    if unknown:
        print(f"  indicateurs non déclarés dans config/indicators.yml (ignorés) : {unknown}")
    df = df[df.indicateur.isin(defs)]
    codes = set(units.pcode)
    bad = ~df.pcode.isin(codes)
    if bad.any():
        print(f"  {int(bad.sum())} lignes ignorées (pcode inconnu), par exemple : {list(df[bad].pcode.unique()[:3])}")
    df = df[~bad].copy()
    df["date"] = df["date"].fillna("").astype(str)
    df = df.sort_values("date").groupby(["pcode", "indicateur"], as_index=False).last()
    direct: dict[str, dict[str, float]] = {}
    for r in df.itertuples():
        direct.setdefault(r.pcode, {})[r.indicateur] = float(r.valeur)
    latest = {i: g["date"].max() for i, g in df.groupby("indicateur")}
    return direct, defs, latest


def aggregate_external(units: pd.DataFrame, direct: dict, defs: dict) -> dict:
    """Complète les niveaux supérieurs quand un indicateur n'est fourni qu'à un niveau plus fin
    (règle de l'indicateur : sum, mean ou popmean ; none = pas d'agrégation)."""
    allv = {pc: dict(v) for pc, v in direct.items()}
    ids = {i for v in direct.values() for i in v}
    popmap = dict(zip(units.pcode, units["pop"].fillna(0)))
    for ind in ids:
        rule = defs[ind].get("aggregate", "none")
        if rule == "none":
            continue
        for lv in (3, 2, 1):
            kids = units[units.level == lv + 1]
            for parent, grp in kids.groupby("parent"):
                if ind in allv.get(parent, {}):
                    continue
                vals = [(allv[c][ind], popmap.get(c, 0)) for c in grp.pcode if ind in allv.get(c, {})]
                if not vals:
                    continue
                if rule == "sum":
                    v = sum(x for x, _ in vals)
                elif rule == "popmean" and sum(w for _, w in vals) > 0:
                    v = sum(x * w for x, w in vals) / sum(w for _, w in vals)
                else:
                    v = sum(x for x, _ in vals) / len(vals)
                allv.setdefault(parent, {})[ind] = v
    # héritage vers le bas : les indicateurs « inherit: down » (valeur connue à un niveau large) sont attribués aux sous-zones sans valeur propre
    for ind in ids:
        if defs[ind].get("inherit") != "down":
            continue
        for lv in (1, 2, 3):
            for _, r in units[units.level == lv + 1].iterrows():
                par = r["parent"]
                if ind not in allv.get(r["pcode"], {}) and ind in allv.get(par, {}):
                    allv.setdefault(r["pcode"], {})[ind] = allv[par][ind]
    return allv


def _load_playbook():
    try:
        return load_yaml("playbook.yml")
    except FileNotFoundError:
        return None


def _load_risks():
    try:
        return load_yaml("risks.yml")
    except FileNotFoundError:
        return None


SCENARIO_LIST = [
    {"id": "sec", "label": "Saison sèche (1 saison sur 10 est aussi sèche)", "short": "Sèche"},
    {"id": "med", "label": "Saison médiane (la plus probable)", "short": "Médiane"},
    {"id": "hum", "label": "Saison humide (1 saison sur 10 est aussi humide)", "short": "Humide"},
    {"id": "el", "label": "Comme lors des El Niño passés", "short": "Type El Niño"},
    {"id": "la", "label": "Comme lors des La Niña passées", "short": "Type La Niña"},
    {"id": "prev", "label": "Selon la prévision saisonnière (ECMWF SEAS5, ou fichier fourni)", "short": "Prévision"},
]


def read_forecast(units, LI, anc, pct_y, path=None):
    """Prévision saisonnière officielle optionnelle (inputs/prevision_saisonniere.csv : pcode, p_sec, p_normal, p_humide,
    source, date ; pcode = zone ou ALL). Retourne (probabilités par fokontany (N,3), poids par saison (Y,N)) ou (None, None)."""
    path = path or INPUTS_DIR / "prevision_saisonniere.csv"
    if not path.exists():
        return None, None
    import scenarios as SC
    df = pd.read_csv(path, dtype={"pcode": str})
    table = {}
    for r in df.itertuples():
        try:
            p = np.array([float(r.p_sec), float(r.p_normal), float(r.p_humide)])
        except (TypeError, ValueError):
            continue
        if not np.isfinite(p).all() or p.min() < 0 or p.sum() <= 0:
            print(f"  prévision ignorée (probabilités invalides) : {r.pcode}")
            continue
        table[str(r.pcode)] = p / p.sum()
    if not table:
        return None, None
    probs = np.full((len(LI), 3), 1 / 3)
    for k, i in enumerate(LI):
        for code in anc[units.at[i, "pcode"]] + ["ALL"]:
            if code in table:
                probs[k] = table[code]
                break
    W = np.zeros(pct_y.shape)
    for k in range(len(LI)):
        W[:, k] = SC.tercile_weights(pct_y[:, k], probs[k])
    print(f"Prévision saisonnière appliquée ({len(table)} zones fournies).")
    return probs, W


def read_sector_alerts(units, anc):
    """Alertes déjà produites par les secteurs/clusters (inputs/alertes_secteurs.csv : pcode, secteur, niveau 1-4, message,
    source, date). Elles sont AFFICHÉES, jamais remplacées : une zone hérite des alertes de ses zones parentes."""
    path = INPUTS_DIR / "alertes_secteurs.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path, dtype={"pcode": str}).fillna("")
    by = {}
    for r in df.itertuples():
        try:
            lvl = int(r.niveau)
        except (TypeError, ValueError):
            continue
        if 1 <= lvl <= 4:
            by.setdefault(str(r.pcode), []).append([str(r.secteur), lvl, str(r.message), str(r.source), str(r.date), str(r.pcode)])
    out = {}
    for pc, chain in anc.items():
        items = [e for code in chain for e in by.get(code, [])]
        if items:
            out[pc] = items
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--today", help="date de référence AAAA-MM-JJ (tests) ; par défaut aujourd'hui")
    args = ap.parse_args()
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    cfg = load_config(args.country)
    units = read_units(args.country)
    season = load_grid(grid_dir(args.country) / "season.npz")
    levels = cfg["alert_levels"]
    min_lvl = cfg["exposure_min_level"]
    factors = cfg["simulation"]["rain_factors"]
    default_share = cfg["default_vulnerable_share"]
    min_norm = cfg["rainfall"]["min_normal_mm"]
    urg_pct = min(r["below_pct"] for r in levels)

    lon0, lat0, res = float(season["lon0"]), float(season["lat0"]), float(season["res"])
    units = units.copy()
    units["act"] = sample_grid(season["act"], lon0, lat0, res, units.lon.values, units.lat.values)
    units["norm"] = sample_grid(season["norm"], lon0, lat0, res, units.lon.values, units.lat.values)

    # Moyennes pondérées par la surface vers le haut (adm4 -> adm3 -> adm2 -> adm1)
    for lv, key in ((3, "adm3"), (2, "adm2"), (1, "adm1")):
        kids = units[(units.level == lv + 1) & units.act.notna() & units.norm.notna() & (units.area_km2 > 0)]
        if kids.empty:
            continue
        w = kids.assign(wa=kids.act * kids.area_km2, wn=kids.norm * kids.area_km2)
        grp = w.groupby(kids[{3: "adm3", 2: "adm2", 1: "adm1"}[lv]]).agg(wa=("wa", "sum"), wn=("wn", "sum"),
                                                                    a=("area_km2", "sum"))
        m = units.level == lv
        a = units.loc[m, "pcode"].map(grp.wa / grp.a)
        n = units.loc[m, "pcode"].map(grp.wn / grp.a)
        units.loc[m & a.notna(), "act"] = a[a.notna()]
        units.loc[m & n.notna(), "norm"] = n[n.notna()]

    ok = units.norm >= min_norm
    units["pct"] = np.where(ok, 100 * units.act / units.norm.where(units.norm > 0), np.nan)
    units["lvl"] = level_from_pct(units.pct.values, levels)
    units["haz"] = np.clip((100 - units.pct) / (100 - urg_pct), 0, 1)

    vs_in, ben = read_inputs(units, default_share)
    ext_direct, ext_defs, ext_latest = read_external(args.country, units)
    # IPC phase 3+ fournie directement (jamais agrégée) : sert de part vulnérable là où elle existe
    vs_ipc = {pc: v["ipc_phase3plus_pct"] / 100 for pc, v in ext_direct.items()
              if "ipc_phase3plus_pct" in v and 0 <= v["ipc_phase3plus_pct"] <= 100}

    # Formations sanitaires / écoles mWater situées dans un fokontany actuellement en zone d'alerte (niveau
    # courant >= seuil d'exposition) : un COMPTAGE de structures, jamais pondéré par la vulnérabilité
    # économique (une structure n'est pas "plus vulnérable" selon le revenu des ménages autour d'elle -- cette
    # dimension reste affichée séparément, voir "vs" / "Vulnérabilité économique retenue" sur la fiche de zone).
    leaf_mask0 = (units.level == 4).values
    exposed_leaf0 = leaf_mask0 & (units.lvl.values >= min_lvl)
    pop0 = units["pop"].fillna(0).values
    for i in np.where(exposed_leaf0)[0]:
        pc = units.at[i, "pcode"]
        vals = ext_direct.get(pc, {})
        for src_id, new_id in (("mwater_sante", "mwater_sante_expose"), ("mwater_ecoles", "mwater_ecoles_expose")):
            if src_id in vals:
                ext_direct.setdefault(pc, {})[new_id] = vals[src_id]

    # Estimation du nombre de femmes enceintes dans la population exposée -- approximation à DEUX hypothèses
    # empilées, documentées séparément (jamais fondue avec la vulnérabilité économique ni avec l'exposition
    # brute) : (1) % de femmes de 15-49 ans actuellement enceintes, mesuré par région (EDS/DHS, voir
    # dhs_femmes_enceintes_pct) ; (2) part nationale de femmes de 15-49 ans dans la population totale
    # (Nations Unies, World Population Prospects 2024 -- Madagascar : ~24,9 %, non mesurée par fokontany,
    # voir femmes_15_49_pct dans config/countries/<pays>.yml). Si l'EDS ne couvre pas la région (donnée
    # manquante), aucune valeur n'est produite pour cette zone -- pas de valeur par défaut inventée.
    # dhs_femmes_enceintes_pct n'est écrit qu'au niveau région (level 1) par le connecteur DHS -- l'héritage
    # vers le bas ("inherit: down") ne se produit que plus tard, dans aggregate_external(). On remonte donc
    # ici explicitement au pcode de la région (colonne adm1) plutôt que de chercher au niveau fokontany.
    femmes_1549_share = cfg.get("femmes_15_49_pct")
    if femmes_1549_share:
        for i in np.where(exposed_leaf0)[0]:
            pc = units.at[i, "pcode"]
            reg_pc = units.at[i, "adm1"]
            pct_enceintes = ext_direct.get(reg_pc, {}).get("dhs_femmes_enceintes_pct")
            if pct_enceintes is not None and 0 <= pct_enceintes <= 100 and pop0[i] > 0:
                est = pop0[i] * femmes_1549_share * pct_enceintes / 100
                ext_direct.setdefault(pc, {})["femmes_enceintes_estimees"] = round(float(est), 1)

    ext_all = aggregate_external(units, ext_direct, ext_defs) if ext_direct else {}

    # --- Feuilles (fokontany) : exposition, cibles, sensibilité ---
    leaf = units.level == 4
    anc = {}
    for r in units.itertuples():
        anc[r.pcode] = [r.pcode, r.adm3, r.adm2, r.adm1]

    sector_alerts = read_sector_alerts(units, anc)

    def share_for(pcode: str) -> tuple[float, int]:
        """Part vulnérable et sa provenance : 1 = fichier fourni, 2 = IPC phase 3+, 0 = valeur par défaut."""
        for code in anc[pcode]:
            if code in vs_in:
                return vs_in[code], 1
        for code in anc[pcode]:
            if code in vs_ipc:
                return vs_ipc[code], 2
        return default_share, 0

    units["vs"] = np.nan
    units["vs_in"] = 0
    for i in units.index[leaf]:
        s, given = share_for(units.at[i, "pcode"])
        units.at[i, "vs"], units.at[i, "vs_in"] = s, given
    pop = units["pop"].fillna(0).values
    # Enfants de moins de 5 ans (grille WorldPop âge/sexe, voir build_population_grid_under5.py) : comptage
    # démographique, jamais pondéré par la vulnérabilité économique (même principe que les structures mWater/
    # HeiGIT -- un enfant n'est pas "plus exposé" selon le revenu du quartier, voir plus haut). Colonne absente
    # tant que le script n'a pas été lancé pour ce pays : vaut alors 0 partout, enfants5 non calculé.
    pop5 = units["pop_under5"].fillna(0).values if "pop_under5" in units.columns else np.zeros(len(units))
    leafmask = leaf.values
    lvl_leaf = units.lvl.values
    exp_leaf = np.where(leafmask & (lvl_leaf >= min_lvl), pop, 0.0)
    tgt_leaf = exp_leaf * units.vs.fillna(default_share).values
    units["e"], units["t"] = exp_leaf, tgt_leaf

    sens_e, sens_t = [], []
    pct_arr = units.pct.values
    for f in factors:
        lv_f = level_from_pct(pct_arr * f, levels)
        e_f = np.where(leafmask & (lv_f >= min_lvl), pop, 0.0)
        sens_e.append(e_f)
        sens_t.append(e_f * units.vs.fillna(default_share).values)
    sens_e = np.array(sens_e)  # (n_facteurs, n_unités)
    sens_t = np.array(sens_t)

    # --- Cumul vers le haut ---
    idx = {pc: i for i, pc in enumerate(units.pcode)}
    E = units.e.values.copy()
    T = units.t.values.copy()
    SE, ST = sens_e.copy(), sens_t.copy()
    leaves = np.where(leafmask)[0]
    for li in leaves:
        for code in anc[units.at[li, "pcode"]][1:]:
            if code in idx:
                j = idx[code]
                E[j] += units.at[li, "e"]
                T[j] += units.at[li, "t"]
                SE[:, j] += sens_e[:, li]
                ST[:, j] += sens_t[:, li]
    units["E"], units["T"] = E, T



    # --- Prévision météo et alertes précoces (cascade : climat -> prévision -> observations) ---
    import early_warning as EW
    from openmeteo import cell_key
    fcst = None
    fc_path = grid_dir(args.country) / "forecast.npz"
    LI0 = np.where(leafmask)[0]
    if fc_path.exists():
        z = load_grid(fc_path)
        dts = [str(x) for x in z["dates"]]
        fetched = dt.datetime.fromisoformat(str(z["fetched_at"]))
        age = (dt.datetime.now(dt.timezone.utc) - fetched).total_seconds() / 86400 if not args.today else 0
        if age <= cfg.get("forecast", {}).get("max_age_days", 3) and today.isoformat() in dts:
            res_f = float(z["res"])
            kx, ky = cell_key(units.lon.values[LI0], units.lat.values[LI0], res_f)
            cell_of = {(int(round(a / res_f)), int(round(b / res_f))): i for i, (a, b) in enumerate(zip(z["lon"], z["lat"]))}
            idxs = np.array([cell_of.get((int(a), int(b)), -1) for a, b in zip(kx, ky)])
            if (idxs >= 0).all():
                t0 = dts.index(today.isoformat())
                fcst = {"dates": dts, "t0": t0, "idx": idxs, "fetched_at": str(z["fetched_at"]),
                        "precip": z["precipitation_sum"][idxs], "tmax": z["temperature_2m_max"][idxs],
                        "tmin": z["temperature_2m_min"][idxs], "gust": z["wind_gusts_10m_max"][idxs]}
            else:
                print("Prévision ignorée : des fokontany n'ont pas de maille de prévision (relancer update_forecast.py).")
        else:
            print("Prévision ignorée : périmée ou ne contient pas la date du jour.")
    s_m0, e_m0 = cfg["rainfall"]["season_start_month"], cfg["rainfall"]["season_end_month"]
    in_rain = (today.month >= s_m0 or today.month <= e_m0) if s_m0 > e_m0 else (s_m0 <= today.month <= e_m0)
    EWL = None   # niveaux d'alerte par fokontany (0-7 jours)
    EWL2 = None  # tendance indicative 8-16 jours (mêmes données déjà récupérées par update_forecast.py/update_floods.py --
                 # forecast_days=16 -- mais jusqu'ici seuls les 7 premiers jours étaient exploités ; fiabilité
                 # météorologique nettement plus faible au-delà d'une semaine, donc jamais utilisée pour les
                 # populations exposées/cibles, seulement un niveau de tendance affiché à part -- audit du 27/10/2026)
    th_path = country_data_dir(args.country) / "flood_thresholds.csv"
    ff_path = grid_dir(args.country) / "flood_forecast.npz"
    flood_src_ok = False
    if fcst is not None and th_path.exists() and ff_path.exists():
        th = pd.read_csv(th_path, dtype={"pcode": str}).set_index("pcode")
        zf = load_grid(ff_path)
        fdates = [str(x) for x in zf["dates"]]
        if today.isoformat() in fdates:
            f0 = fdates.index(today.isoformat())
            rl = cfg["flood"]["return_levels"]
            flood_src_ok = True

    def flood_levels_for(day_lo: int, day_hi: int):
        """Niveau de crue (0-3) pour la fenêtre [day_lo, day_hi) de jours de prévision, même méthode que l'alerte à 7 jours."""
        flood_lv = np.zeros(len(LI0), dtype=int)
        flood_ratio = np.full(len(LI0), np.nan)
        flood_q = np.full(len(LI0), np.nan)
        if not flood_src_ok:
            return flood_lv, flood_ratio, flood_q
        lo, hi = f0 + day_lo, min(f0 + day_hi, zf["q"].shape[1])
        if hi <= lo:
            return flood_lv, flood_ratio, flood_q
        qmax = {pc: float(np.nanmax(zf["q"][i, lo:hi])) if np.isfinite(zf["q"][i, lo:hi]).any() else np.nan
                for i, pc in enumerate(zf["pcode"].astype(str))}
        for k, i in enumerate(LI0):
            c = units.at[i, "adm3"]
            if c in th.index and c in qmax and np.isfinite(qmax[c]):
                row = th.loc[c]
                q2 = row.get("q2", np.nan)
                if np.isfinite(q2) and q2 >= cfg["flood"]["min_q2_m3s"]:
                    flood_q[k], flood_ratio[k] = qmax[c], qmax[c] / q2
                    flood_lv[k] = 3 if qmax[c] >= row.get(f"q{rl[2]}", np.inf) else 2 if qmax[c] >= row.get(f"q{rl[1]}", np.inf) \
                        else 1 if qmax[c] >= q2 else 0
        return flood_lv, flood_ratio, flood_q

    if fcst is not None:
        horizon = cfg["forecast"].get("horizon_days", 7)
        fut = slice(fcst["t0"], None)
        lv, nums = EW.compute(fcst["precip"][:, fut], fcst["tmax"][:, fut], fcst["gust"][:, fut], cfg["alerts"], in_rain, horizon)
        flood_lv, flood_ratio, flood_q = flood_levels_for(0, horizon)
        flood_info = {"available": flood_src_ok, "fetched_at": str(zf["fetched_at"]) if flood_src_ok else None,
                      "n_communes": int(len(th)) if flood_src_ok else 0, "n_valid_thresholds": int(th.q2.notna().sum()) if flood_src_ok else 0}
        lv["flood"] = flood_lv
        nums["flood_ratio"], nums["flood_q"] = flood_ratio, flood_q
        EWL = {"lv": lv, "nums": nums, "horizon": horizon, "flood": flood_info}

        # Tendance 8-16 jours : même calcul de niveaux (pluie/vent/chaleur/sécheresse/crue), sur la fenêtre
        # suivante déjà présente dans forecast.npz (forecast_days=16) mais jamais lue jusqu'ici au-delà du jour 7.
        total_days = fcst["precip"].shape[1] - fcst["t0"]
        if total_days > horizon:
            d0, d1 = horizon, total_days
            fut2 = slice(fcst["t0"] + d0, fcst["t0"] + d1)
            lv2, nums2 = EW.compute(fcst["precip"][:, fut2], fcst["tmax"][:, fut2], fcst["gust"][:, fut2], cfg["alerts"], in_rain, d1 - d0)
            flood_lv2, flood_ratio2, flood_q2 = flood_levels_for(d0, d1)
            lv2["flood"] = flood_lv2
            nums2["flood_ratio"], nums2["flood_q"] = flood_ratio2, flood_q2
            EWL2 = {"lv": lv2, "nums": nums2, "day_from": d0 + 1, "day_to": d1}

    # --- Scénarios de fin de saison (ensemble d'analogues, voir scripts/scenarios.py) ---
    import scenarios as SC
    from enso import season_months as _season_months
    scn = None
    ms_path, cl_path = grid_dir(args.country) / "monthly_series.npz", grid_dir(args.country) / "clim_monthly.npz"
    season_start = str(season["season_start"])
    through = str(season["data_through"])
    sc_cfg = cfg.get("scenarios", {})
    wet_thr = float(sc_cfg.get("wet_threshold_pct", 130))
    if ms_path.exists() and cl_path.exists():
        ms, cl = load_grid(ms_path), load_grid(cl_path)
        s_m, e_m = cfg["rainfall"]["season_start_month"], cfg["rainfall"]["season_end_month"]
        y0s, y1s = SC.target_season(today, s_m, e_m)
        months = _season_months(y1s, s_m, e_m)
        through_d = dt.date.fromisoformat(through)
        cov = SC.covered_fractions(months, season_start, through_d, months[0])
        LI = np.where(leafmask)[0]
        cov_obs = list(cov)
        cascade = {"used": False}
        known_mm = np.zeros(len(LI))
        lon, lat = units.lon.values[LI], units.lat.values[LI]
        g0, g1, gr = float(ms["lon0"]), float(ms["lat0"]), float(ms["res"])
        arr = ms["arr"]
        series = np.stack([np.stack([sample_grid(arr[yi, mi].astype("float32"), g0, g1, gr, lon, lat)
                                     for mi in range(arr.shape[1])]) for yi in range(arr.shape[0])])
        clim_m = np.stack([sample_grid(cl["clim"][mo - 1], float(cl["lon0"]), float(cl["lat0"]), float(cl["res"]), lon, lat)
                           for _, mo in months])
        act = units.act.values[LI] if any(c > 0 for c in cov) else np.zeros(len(LI))
        if fcst is not None:
            # étape 2 de la cascade : jours récents (analyse du modèle) puis prévision remplacent le climat jusqu'à l'horizon
            s_first = dt.date(months[0][0], months[0][1], 1)
            s_last = dt.date(months[-1][0], months[-1][1], calendar.monthrange(*months[-1])[1])
            obs_through = through_d if season_start == f"{months[0][0]}-{months[0][1]:02d}" else None
            k_start = obs_through + dt.timedelta(days=1) if obs_through else s_first
            fdates = [dt.date.fromisoformat(x) for x in fcst["dates"]]
            h_end = min(s_last, fdates[-1])
            if fdates[0] <= k_start <= h_end:
                sel = [j for j, d in enumerate(fdates) if k_start <= d <= h_end]
                known_mm = np.nansum(fcst["precip"][:, sel], axis=1)
                act = act + known_mm
                cov = SC.covered_fractions(months, season_start, h_end, months[0], ignore_season_check=True)
                cascade = {"used": True, "known_through": h_end.isoformat(), "days": len(sel), "fetched_at": fcst["fetched_at"],
                           "observed_through": through if obs_through else None}
            else:
                print("Cascade prévision non appliquée : la prévision ne couvre pas le jour qui suit les dernières observations.")
        pct_y, norm_full = SC.final_pct(act, clim_m, series, cov, min_norm)
        seas_path = INPUTS_DIR / "prevision_saisonniere.csv"          # prévision officielle fournie à la main : prioritaire
        if not seas_path.exists():
            seas_path = country_data_dir(args.country) / "seasonal_auto.csv"   # sinon prévision ECMWF SEAS5 (connector_seasonal.py)
        fprobs, fweights = read_forecast(units, LI, anc, pct_y, seas_path)
        sc_pct, nph = SC.scenario_values(pct_y, ms["phases"], fprobs)
        lvl_y = SC.level_array(pct_y, levels)
        ok_y = np.isfinite(pct_y)
        W = fweights if fweights is not None else ok_y.astype(float)
        W = np.where(ok_y, W, 0.0)
        with np.errstate(invalid="ignore", divide="ignore"):
            p_leaf = np.where(W.sum(axis=0) > 0, (W * (lvl_y >= min_lvl)).sum(axis=0) / W.sum(axis=0), np.nan)
        popL = pop[LI]
        vsL = units.vs.fillna(default_share).values[LI]
        area = units.area_km2.fillna(0).values
        nU = len(units)

        def lift(v):
            a = np.zeros(nU)
            a[LI] = np.nan_to_num(v)
            return a

        SCN = {}
        normU = np.zeros(nU)
        normU[LI] = np.nan_to_num(norm_full)
        for sid, pc_leaf in sc_pct.items():
            lv_leaf = SC.level_array(pc_leaf, levels)
            e_l = np.where(lv_leaf >= min_lvl, popL, 0.0)
            t_l = e_l * vsL
            w_l = np.where(np.isfinite(pc_leaf) & (pc_leaf >= wet_thr), popL, 0.0)
            tot = SC.rollup_sum(units, leafmask, lift(np.where(np.isfinite(pc_leaf), pc_leaf / 100 * norm_full, 0.0)) * area)
            den = SC.rollup_sum(units, leafmask, lift(np.where(np.isfinite(pc_leaf), norm_full, 0.0)) * area)
            with np.errstate(invalid="ignore", divide="ignore"):
                pct_u = np.where(den > 0, tot / den * 100, np.nan)
            pct_u[LI] = pc_leaf
            lv_u = SC.level_array(pct_u, levels)
            SCN[sid] = {"pct": pct_u, "lvl": lv_u, "e": SC.rollup_sum(units, leafmask, lift(e_l)),
                        "t": SC.rollup_sum(units, leafmask, lift(t_l)), "w": SC.rollup_sum(units, leafmask, lift(w_l))}
        # pluie de chaque saison passée complète (% de la normale) par unité : cartes « une année contre une autre »
        season_sum = np.nansum(series, axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            hy_leaf = np.where(norm_full[None, :] > min_norm, season_sum / norm_full[None, :] * 100.0, np.nan)
        hy_leaf[np.isnan(series).all(axis=1)] = np.nan
        HY = np.full((nU, hy_leaf.shape[0]), np.nan)
        HYE, HYT, HYW = (np.zeros((nU, hy_leaf.shape[0])) for _ in range(3))
        for j in range(hy_leaf.shape[0]):
            pj = hy_leaf[j]
            e_j = np.where(SC.level_array(pj, levels) >= min_lvl, popL, 0.0)
            HYE[:, j] = SC.rollup_sum(units, leafmask, lift(e_j))
            HYT[:, j] = SC.rollup_sum(units, leafmask, lift(e_j * vsL))
            HYW[:, j] = SC.rollup_sum(units, leafmask, lift(np.where(np.isfinite(pj) & (pj >= wet_thr), popL, 0.0)))
            tot_j = SC.rollup_sum(units, leafmask, lift(np.where(np.isfinite(pj), pj / 100 * norm_full, 0.0)) * area)
            den_j = SC.rollup_sum(units, leafmask, lift(np.where(np.isfinite(pj), norm_full, 0.0)) * area)
            with np.errstate(invalid="ignore", divide="ignore"):
                col = np.where(den_j > 0, tot_j / den_j * 100, np.nan)
            col[LI] = pj
            HY[:, j] = col
        num = SC.rollup_sum(units, leafmask, lift(popL * np.nan_to_num(p_leaf)))
        popU = SC.rollup_sum(units, leafmask, lift(popL))
        with np.errstate(invalid="ignore", divide="ignore"):
            pa_u = np.where(popU > 0, num / popU, np.nan)
        scn = {"S": SCN, "pa": pa_u, "ex": num, "cov": cov, "cov_obs": cov_obs, "cascade": cascade, "season": f"{y0s}-{y1s}", "n": nph,
               "years": [int(ms["years"][0]), int(ms["years"][-1])], "hist_years": [int(y) for y in ms["years"]], "hist_phases": [str(x) for x in ms["phases"]], "HY": HY, "HYE": HYE, "HYT": HYT, "HYW": HYW, "weighted": fweights is not None, "n_years": int(len(ms["years"]))}


    # --- Alertes précoces : cumul vers les zones supérieures ---
    EWU = None
    if EWL is not None:
        import scenarios as SC2
        nU2 = len(units)
        popL0 = pop[LI0]
        pop5L0 = pop5[LI0]
        area2 = units.area_km2.fillna(0).values

        def lift2(v, fill=0.0):
            a = np.full(nU2, fill, dtype=float)
            a[LI0] = np.nan_to_num(v, nan=fill)
            return a

        vsL0 = units.vs.fillna(default_share).values[LI0]
        lv_u = {h: SC2.rollup_max(units, leafmask, lift2(EWL["lv"][h])).astype(int) for h in EW.HAZARDS}
        ppl_u = {h: SC2.rollup_sum(units, leafmask, lift2(np.where(EWL["lv"][h] >= 2, popL0, 0.0))) for h in EW.HAZARDS}
        # cible (vulnérabilité économique) des alertes précoces météo à 7 jours -- même principe que "t" pour
        # l'exposition saisonnière : ne jamais afficher seulement un comptage brut là où un comptage pondéré
        # par la vulnérabilité économique existe partout ailleurs dans le pipeline (voir audit du 27/10/2026).
        tgt_u = {h: SC2.rollup_sum(units, leafmask, lift2(np.where(EWL["lv"][h] >= 2, popL0 * vsL0, 0.0))) for h in EW.HAZARDS}
        # Enfants -5 ans en zone d'alerte précoce (tous aléas météo à 7 jours : pluie, vent, chaleur, sécheresse,
        # crue) -- grille WorldPop âge/sexe (voir build_population_grid_under5.py), même logique que ppl_u/tgt_u
        # mais pour la population -5 ans ; jamais pondéré par vs (voir note sur pop5 ci-dessus). Tâche n°45.
        enf5_u = {h: SC2.rollup_sum(units, leafmask, lift2(np.where(EWL["lv"][h] >= 2, pop5L0, 0.0))) for h in EW.HAZARDS}
        nums_u = {k: SC2.rollup_max(units, leafmask, lift2(v, fill=0.0)) for k, v in EWL["nums"].items()}
        nd = min(10, fcst["precip"].shape[1] - fcst["t0"])
        denA = SC2.rollup_sum(units, leafmask, lift2(np.ones(len(LI0))) * area2)
        daily_p, daily_t = [], []
        for j in range(nd):
            for arr_, store in ((fcst["precip"], daily_p), (fcst["tmax"], daily_t)):
                v = lift2(arr_[:, fcst["t0"] + j])
                tot = SC2.rollup_sum(units, leafmask, v * area2)
                with np.errstate(invalid="ignore", divide="ignore"):
                    u = np.where(denA > 0, tot / denA, np.nan)
                u[LI0] = arr_[:, fcst["t0"] + j]
                store.append(u)
        EWU = {"lv": lv_u, "ppl": ppl_u, "tgt": tgt_u, "e5": enf5_u, "nums": nums_u,
               "p": np.array(daily_p), "t": np.array(daily_t)}

    # Tendance 8-16 jours : seul le niveau de tendance par zone est remonté (aucune population exposée/cible
    # calculée dessus -- fiabilité météo trop faible au-delà d'une semaine pour en faire un chiffre d'action,
    # voir validation/methodologie_these.md). Affichée à part de l'alerte précoce à 7 jours, jamais fondue avec elle.
    EWU2 = None
    if EWL2 is not None:
        import scenarios as SC2b
        lv_u2 = {h: SC2b.rollup_max(units, leafmask, lift2(EWL2["lv"][h])).astype(int) for h in EW.HAZARDS}
        EWU2 = {"lv": lv_u2, "day_from": EWL2["day_from"], "day_to": EWL2["day_to"]}

    def pack(i: int) -> dict:
        r = units.iloc[i]
        d = {"p": int(r["pop"]) if pd.notna(r["pop"]) else None}
        # Enfants -5 ans (estimation, grille WorldPop âge/sexe) : affiché en permanence dans la fiche de zone,
        # pas seulement nichés dans le détail de l'alerte précoce à 7 jours (ewe5) -- sinon cet indicateur reste
        # invisible dès qu'aucune alerte météo n'est active, ce qui était le cas pour la quasi-totalité des zones
        # la plupart du temps. Absent si pop_under5 n'a jamais été calculée pour ce pays (pas d'invention de 0).
        if "pop_under5" in r.index and pd.notna(r["pop_under5"]):
            d["p5"] = int(round(float(r["pop_under5"])))
        if pd.notna(r["pct"]):
            d.update({"a": round(float(r["act"]), 1), "n": round(float(r["norm"]), 1),
                      "pc": round(float(r["pct"]), 1), "h": round(float(r["haz"]), 2)})
        d["l"] = int(r["lvl"])
        d["e"] = int(round(E[i]))
        d["t"] = int(round(T[i]))
        d["se"] = [int(round(x)) for x in SE[:, i]]
        d["st"] = [int(round(x)) for x in ST[:, i]]
        if r["level"] == 4:
            d["vs"] = round(float(r["vs"]), 3)
            d["vi"] = int(r["vs_in"])
        b = ben.get(r["pcode"])
        if b:
            d["b"] = int(round(b))
        if scn is not None:
            d["sc"] = {sid: [None if not np.isfinite(v["pct"][i]) else round(float(v["pct"][i]), 1), int(v["lvl"][i]),
                             int(round(v["e"][i])), int(round(v["t"][i])), int(round(v["w"][i]))] for sid, v in scn["S"].items()}
            d["pa"] = None if not np.isfinite(scn["pa"][i]) else round(float(scn["pa"][i]), 3)
            d["y"] = [None if not np.isfinite(x) else round(float(x), 1) for x in scn["HY"][i]]
            if r["level"] < 4:   # pour les fokontany, ces valeurs se déduisent de y, de la population et de la part vulnérable
                d["ye"] = [int(round(x)) for x in scn["HYE"][i]]
                d["yt"] = [int(round(x)) for x in scn["HYT"][i]]
                d["yw"] = [int(round(x)) for x in scn["HYW"][i]]
            d["ex"] = int(round(scn["ex"][i]))
        if EWU is not None:
            d["ew"] = [int(EWU["lv"][h][i]) for h in EW.HAZARDS]
            d["ewp"] = [int(round(EWU["ppl"][h][i])) for h in EW.HAZARDS]
            d["ewt"] = [int(round(EWU["tgt"][h][i])) for h in EW.HAZARDS]
            d["ewe5"] = [int(round(EWU["e5"][h][i])) for h in EW.HAZARDS]
            nm = EWU["nums"]
            fr = nm["flood_ratio"][i]
            d["ev"] = [round(float(nm["rain_max"][i]), 1), round(float(nm["rain_3d"][i]), 1), round(float(nm["tmax_max"][i]), 1),
                       round(float(nm["gust_max"][i]), 1), int(nm["dry_run"][i]),
                       round(float(fr), 2) if fr > 0 else None, round(float(nm["flood_q"][i]), 1) if nm["flood_q"][i] > 0 else None]
            d["fr"] = [None if not np.isfinite(x) else int(round(float(x))) for x in EWU["p"][:, i]]
            d["ft"] = [None if not np.isfinite(x) else int(round(float(x))) for x in EWU["t"][:, i]]
        if EWU2 is not None:
            # Tendance 8-16 jours : niveau par aléa uniquement (pas de population), fiabilité plus faible,
            # jamais mélangée avec "ew" (alerte précoce 0-7 jours).
            d["ew2"] = [int(EWU2["lv"][h][i]) for h in EW.HAZARDS]
        al = sector_alerts.get(r["pcode"])
        if al:
            d["al"] = al
        xv = ext_all.get(r["pcode"])
        if xv:
            d["x"] = {k: round(v, 3) for k, v in xv.items()}
        return d

    out = country_docs_dir(args.country) / "metrics"
    top = {"adm1": {}, "adm2": {}}
    for i in units.index[units.level <= 2]:
        top[f"adm{int(units.at[i, 'level'])}"][units.at[i, "pcode"]] = pack(i)
    write_json(out / "top.json", top)
    for adm2, sub in units[units.level >= 3].groupby("adm2"):
        part = {"adm3": {}, "adm4": {}}
        for i in sub.index:
            part[f"adm{int(units.at[i, 'level'])}"][units.at[i, "pcode"]] = pack(i)
        write_json(out / "d" / f"{adm2}.json", part)

    enso_state, enso_p = None, DATA_DIR / "enso" / "oni.csv"
    if enso_p.exists():
        import enso as _enso
        enso_state = _enso.latest(pd.read_csv(enso_p))
    hist_ok = (country_docs_dir(args.country) / "history.json").exists()
    nat = units[units.level == 1]
    meta = {
        "enso": enso_state, "has_history": hist_ok,
        "scenarios": None if scn is None else {
            "season": scn["season"], "observed_share": round(float(np.mean(scn["cov_obs"])), 2), "years": scn["years"], "hist_years": scn["hist_years"], "hist_phases": scn["hist_phases"],
            "cascade": scn["cascade"], "n_years": scn["n_years"], "weighted_by_forecast": scn["weighted"], "n_phase": scn["n"], "wet_threshold_pct": wet_thr,
            "list": [x for x in SCENARIO_LIST if x["id"] in scn["S"]]},
        "playbook": _load_playbook(),
        "risks": _load_risks(),
        "sector_alerts": len(sector_alerts),
        "forecast": None if EWL is None else {
            "fetched_at": fcst["fetched_at"], "first": fcst["dates"][0], "last": fcst["dates"][-1], "today": today.isoformat(),
            "horizon_days": EWL["horizon"], "hazards": EW.HAZARDS, "hazard_labels": EW.HAZARD_LABEL, "level_names": EW.LEVEL_NAME,
            "thresholds": cfg["alerts"], "flood": EWL["flood"], "in_rain_season": bool(in_rain),
            "n_days_series": int(EWU["p"].shape[0]),
            "trend": None if EWU2 is None else {"day_from": EWU2["day_from"], "day_to": EWU2["day_to"]}},
        "sector_names": [{"id": x["id"], "label": x["label"]} for x in load_yaml("sectors.yml")["sectors"]],
        "country": cfg["name"], "slug": cfg["slug"], "iso3": cfg["iso3"],
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "data_through": through, "season_start": season_start,
        "map": cfg["map"], "levels": cfg["levels"],
        "alert_levels": levels, "exposure_min_level": min_lvl,
        "default_vulnerable_share": default_share,
        "rain_factors": factors,
        "external": [{"id": i, "label": ext_defs[i]["label"], "unit": ext_defs[i].get("unit", ""),
                      "format": ext_defs[i].get("format", "float"), "style": ext_defs[i].get("style", ""), "latest": ext_latest.get(i, ""),
                      "n_units": sum(1 for v in ext_all.values() if i in v)}
                     for i in sorted({k for v in ext_all.values() for k in v})],
        "national": {"pop": int(nat["pop"].sum()), "exposed": int(round(nat["E"].sum())),
                     "targets": int(round(nat["T"].sum()))},
        "sources": [
            {"id": "chirps", "label": "Pluie CHIRPS v2.0 (CHC/UCSB)", "frequency": "10 jours",
             "data_through": through, "baseline": cfg["rainfall"]["baseline_years"]},
            {"id": "cod_ab", "label": "Limites administratives OCHA COD-AB (BNGRC)", "frequency": "ponctuelle"},
            {"id": "cod_ps", "label": "Population OCHA COD-PS", "frequency": "ponctuelle",
             "reference_year": cfg["population"].get("reference_year")},
            {"id": "vulnerability", "label": "Vulnérabilité économique (fichier inputs/vulnerabilite.csv)",
             "given_for": len(vs_in)},
            {"id": "interventions", "label": "Interventions des partenaires (inputs/interventions.csv)",
             "units_with_beneficiaries": len(ben)},
            {"id": "external", "label": "Indicateurs externes (inputs/indicateurs et connecteurs : IPC, pauvreté…)",
             "n_indicators": len({k for v in ext_all.values() for k in v}),
             "ipc_units": len(vs_ipc)},
        ],
    }
    write_json(country_docs_dir(args.country) / "meta.json", meta)
    print(f"Indicateurs écrits : données de pluie jusqu'au {through} ; "
          f"exposés au niveau national : {meta['national']['exposed']:,} ; cibles : {meta['national']['targets']:,}")


if __name__ == "__main__":
    main()
