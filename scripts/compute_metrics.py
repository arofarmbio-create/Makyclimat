"""Calcul des indicateurs MakyClimat pour toutes les unités (région -> fokontany) et écriture des fichiers du site.

Entrées : data/<pays>/units.csv (limites + population), data/<pays>/grids/season.npz (pluie),
          inputs/vulnerabilite.csv et inputs/interventions.csv (facultatifs).
Sorties : docs/data/<pays>/metrics/top.json, metrics/d/<district>.json, meta.json

Méthode (version 1, à calibrer et valider scientifiquement) :
  1. pct = pluie cumulée de la saison / normale à la même date x 100 (cellule CHIRPS au centroïde ; moyenne
     pondérée par la surface pour les unités qui ont des sous-unités).
  2. niveau d'alerte selon les seuils de la configuration (4 urgence, 3 alerte, 2 veille, 1 normal, 0 sans donnée).
  3. population exposée = population des fokontany dont le niveau >= exposure_min_level, puis cumul vers le haut.
  4. cibles potentiels = population exposée x part vulnérable (par priorité : fichier fourni, IPC phase 3+, valeur par défaut).
  5. sensibilité : mêmes calculs avec la pluie multipliée par chaque facteur de simulation.
"""
from __future__ import annotations

import argparse
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
    return allv


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
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
    ext_all = aggregate_external(units, ext_direct, ext_defs) if ext_direct else {}

    # --- Feuilles (fokontany) : exposition, cibles, sensibilité ---
    leaf = units.level == 4
    anc = {}
    for r in units.itertuples():
        anc[r.pcode] = [r.pcode, r.adm3, r.adm2, r.adm1]

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

    through = str(season["data_through"])
    season_start = str(season["season_start"])

    def pack(i: int) -> dict:
        r = units.iloc[i]
        d = {"p": int(r["pop"]) if pd.notna(r["pop"]) else None}
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
            {"id": "vulnerability", "label": "Part vulnérable (fichier inputs/vulnerabilite.csv)",
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
