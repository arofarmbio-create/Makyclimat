"""Contrôle de vraisemblance de la recharge transférée T2 et recharge corrigée T2c
(validation/protocole_controle_recharge.md, fixé avant le calcul le 09/11/2026).

Bornes de la part de la pluie qui recharge la nappe (r = R / P) : quantiles 10 % et 90 % des 134 sites africains du BGS
(MacDonald et al. 2021), par groupe d'aquifère × climat (aride ou semi-aride si P/ETP < 0,5), avec repli sur le groupe
seul puis sur tous les sites si moins de 10 sites. T2c = T2 ramenée dans [q10 × P ; q90 × P] ; intervalle de 80 % =
partie commune avec celui de T2, sinon [q10 × P ; q90 × P]. Aucune donnée malgache ne fixe les bornes ; les 8
références de H-C6 servent seulement à vérifier (H-R2).
Entrées (hors git, comme H-C6) : base BGS, grille T2 (recharge_transferee.csv), séries MGMERL.
Sorties : validation/controle_recharge.md, inputs/hydrogeologie/recharge_t2c.csv.
Usage : python scripts/controle_recharge.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd

from common import ROOT, country_data_dir, read_units

MIN_SITES = 10
ARID = 0.5                         # indice d'aridité P/ETP
SOUTH_LAT = -23.0
H_R2_MIN = 5
NAMED = [("Mahajanga", -15.72, 46.32, "carte BGS : 124 mm/an"), ("Toliara", -23.35, 43.67, "puits karstiques voisins : 80 à 195 mm/an")]


def climate(aridity) -> np.ndarray:
    return np.where(np.asarray(aridity, float) < ARID, "aride", "humide")


def bounds_table(af: pd.DataFrame) -> pd.DataFrame:
    """Quantiles 10 % et 90 % de r = R / P par groupe × climat, groupe seul et tous sites."""
    d = af[(af.P > 0) & af.R.notna()].assign(r=lambda x: x.R / x.P, clim=lambda x: climate(x.Aridity))
    rows = []
    for (g, c), s in d.groupby(["groupe", "clim"]):
        rows.append({"groupe": g, "clim": c, "n": len(s), "q10": s.r.quantile(0.1), "q90": s.r.quantile(0.9)})
    for g, s in d.groupby("groupe"):
        rows.append({"groupe": g, "clim": "tous", "n": len(s), "q10": s.r.quantile(0.1), "q90": s.r.quantile(0.9)})
    rows.append({"groupe": "tous", "clim": "tous", "n": len(d), "q10": d.r.quantile(0.1), "q90": d.r.quantile(0.9)})
    return pd.DataFrame(rows)


def lookup(tab: pd.DataFrame, groupe: str, clim: str) -> tuple[float, float, str]:
    """Bornes de la classe, avec repli si moins de MIN_SITES sites."""
    for g, c in ((groupe, clim), (groupe, "tous"), ("tous", "tous")):
        s = tab[(tab.groupe == g) & (tab.clim == c)]
        if len(s) and s.n.iloc[0] >= MIN_SITES:
            return float(s.q10.iloc[0]), float(s.q90.iloc[0]), f"{g} / {c}"
    raise ValueError("table de bornes vide")


def correct(t2, lo, hi, p, q10, q90) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """T2c, intervalle de 80 % corrigé et signal (-1 sous la borne basse, +1 au-dessus de la haute, 0 sinon)."""
    t2, lo, hi, p, q10, q90 = (np.asarray(x, float) for x in (t2, lo, hi, p, q10, q90))
    bmin, bmax = q10 * p, q90 * p
    flag = np.where(t2 < bmin, -1, np.where(t2 > bmax, 1, 0))
    t2c = np.clip(t2, bmin, bmax)
    clo, chi = np.maximum(lo, bmin), np.minimum(hi, bmax)
    empty = clo > chi
    clo, chi = np.where(empty, bmin, clo), np.where(empty, bmax, chi)
    return t2c, clo, chi, flag


def apply(grid: pd.DataFrame, tab: pd.DataFrame) -> pd.DataFrame:
    g = grid.copy()
    g["clim"] = climate(g.Aridity)
    b = [lookup(tab, gr if isinstance(gr, str) and gr else "tous", c) for gr, c in zip(g.Aquifer_group, g.clim)]
    g["q10"], g["q90"], g["classe_bornes"] = [x[0] for x in b], [x[1] for x in b], [x[2] for x in b]
    g["T2c_mmpa"], g["T2c_bas_mmpa"], g["T2c_haut_mmpa"], g["signal"] = correct(
        g.T2_mmpa, g.T2_bas_mmpa, g.T2_haut_mmpa, g.LTA_P_mmpa, g.q10, g.q90)
    return g


def share_table(keys, flag) -> pd.DataFrame:
    d = pd.DataFrame({"g": np.asarray(keys), "f": np.asarray(flag)})
    return d.groupby("g").agg(mailles=("f", "size"), sous_borne=("f", lambda x: (x < 0).mean()),
                              au_dessus=("f", lambda x: (x > 0).mean())).reset_index()


def main() -> None:
    import validate_transfert_madagascar as V
    from sklearn.neighbors import BallTree
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    base = country_data_dir(args.country)
    w = pd.read_excel(base / "bgs_recharge_raw" / "Recharge_data_Africa_BGS.xlsx", sheet_name="data")
    af = pd.DataFrame({"R": pd.to_numeric(w.Recharge_mmpa, errors="coerce"), "P": pd.to_numeric(w.LTA_P_mmpa, errors="coerce"),
                       "Aridity": pd.to_numeric(w.Aridity, errors="coerce"), "groupe": w.Aquifer_group})
    tab = bounds_table(af.dropna())
    grid = pd.read_csv(base / "nappes_mondiales" / "recharge_transferee.csv")
    g = apply(grid, tab)

    # Région de chaque maille : fokontany le plus proche
    units = read_units(args.country)
    fk = units[units.level == 4]
    reg_name = dict(zip(units[units.level == 1].pcode, units[units.level == 1].name))
    j = BallTree(np.radians(np.c_[fk.lat, fk.lon]), metric="haversine").query(np.radians(np.c_[g.lat, g.lon]), k=1,
                                                                                return_distance=False)[:, 0]
    g["region"] = [reg_name.get(a, a) for a in fk.adm1.to_numpy()[j]]

    # H-R2 : mêmes références et même évaluation que H-C6
    refs = V.site_references(args.country, g)
    ev = {v: V.evaluate(g, v, refs) for v in ("T2", "T2c")}
    ok = {v: ev[v].dans_intervalle.dropna() for v in ev}
    n_ok = {v: int(ok[v].sum()) for v in ok}
    h_r2 = n_ok["T2c"] >= H_R2_MIN

    out = ROOT / "inputs" / "hydrogeologie"
    out.mkdir(parents=True, exist_ok=True)
    cols = ["lon", "lat", "region", "LTA_P_mmpa", "Aridity", "Aquifer_group", "classe_bornes", "q10", "q90", "T2_mmpa",
            "T2_bas_mmpa", "T2_haut_mmpa", "T2c_mmpa", "T2c_bas_mmpa", "T2c_haut_mmpa", "signal"]
    g[cols].round(4).to_csv(out / "recharge_t2c.csv", index=False)

    south = np.where(g.lat < SOUTH_LAT, "Grand Sud (au sud de 23° S)", "reste de l'île")
    L = ["# Contrôle de vraisemblance de la recharge transférée (T2c)", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/controle_recharge.py`, selon "
         "`validation/protocole_controle_recharge.md` (fixé avant le calcul). Calcul local : la base BGS, la grille T2 et "
         "les séries MGMERL sont hors du dépôt, comme pour H-C6.", "",
         "## Bornes de la part de la pluie qui recharge la nappe (sites africains du BGS)", "",
         "| Groupe d'aquifère | Climat | Sites | R/P à 10 % | R/P à 90 % |", "|---|---|---|---|---|"]
    for x in tab.itertuples():
        L.append(f"| {x.groupe} | {x.clim} | {x.n} | {x.q10:.3f} | {x.q90:.3f} |")
    L += ["", f"Classes de moins de {MIN_SITES} sites : repli sur le groupe seul, puis sur tous les sites.", "",
          "## H-R1 : mailles hors bornes", "",
          f"Sur {len(g)} mailles : {(g.signal < 0).mean():.0%} sous la borne basse, {(g.signal > 0).mean():.0%} au-dessus de la "
          f"borne haute. Recharge médiane : T2 {g.T2_mmpa.median():.0f} mm/an, T2c {g.T2c_mmpa.median():.0f} mm/an.", "",
          "| Zone | Mailles | Sous la borne basse | Au-dessus de la borne haute |", "|---|---|---|---|"]
    for x in share_table(south, g.signal).itertuples():
        L.append(f"| {x.g} | {x.mailles} | {x.sous_borne:.0%} | {x.au_dessus:.0%} |")
    L += ["", "| Région | Mailles | Sous la borne basse | Au-dessus de la borne haute |", "|---|---|---|---|"]
    for x in share_table(g.region, g.signal).sort_values("g").itertuples():
        L.append(f"| {x.g} | {x.mailles} | {x.sous_borne:.0%} | {x.au_dessus:.0%} |")
    L += ["", "| Groupe d'aquifère | Mailles | Sous la borne basse | Au-dessus de la borne haute |", "|---|---|---|---|"]
    for x in share_table(g.Aquifer_group.fillna("inconnu"), g.signal).itertuples():
        L.append(f"| {x.g} | {x.mailles} | {x.sous_borne:.0%} | {x.au_dessus:.0%} |")
    L += ["", "## H-R2 : références malgaches (vérification indépendante, même évaluation que H-C6)", "",
          "| Référence | Valeur centrale | T2 (intervalle) | T2c (intervalle) | T2 | T2c |", "|---|---|---|---|---|---|"]
    a, b = ev["T2"].set_index("reference"), ev["T2c"].set_index("reference")

    def f(v):
        return "—" if pd.isna(v) else f"{v:.0f}"

    def yn(v):
        return "—" if pd.isna(v) else ("oui" if v else "non")
    for name in a.index:
        ra, rb = a.loc[name], b.loc[name]
        L.append(f"| {name} | {f(ra.valeur_centrale_mmpa)} | {f(ra.get('prediction_mediane'))} ({f(ra.get('intervalle_bas'))} à "
                 f"{f(ra.get('intervalle_haut'))}) | {f(rb.get('prediction_mediane'))} ({f(rb.get('intervalle_bas'))} à "
                 f"{f(rb.get('intervalle_haut'))}) | {yn(ra.dans_intervalle)} | {yn(rb.dans_intervalle)} |")
    L += ["", f"T2 : {n_ok['T2']} sur {len(ok['T2'])} ; T2c : {n_ok['T2c']} sur {len(ok['T2c'])}. **H-R2 "
          f"{'soutenue' if h_r2 else 'non soutenue'}** (règle : au moins {H_R2_MIN} sur 8).", "",
          "## Contrôles nommés (descriptifs : ce sont eux qui ont révélé le problème)", "",
          "| Lieu | Pluie (mm/an) | Groupe | Bornes R/P | T2 | T2c (intervalle) | Comparaison |", "|---|---|---|---|---|---|---|"]
    for name, lat, lon, cmp_ in NAMED:
        i = int(np.argmin((g.lat - lat) ** 2 + (g.lon - lon) ** 2))
        r = g.iloc[i]
        L.append(f"| {name} | {r.LTA_P_mmpa:.0f} | {r.Aquifer_group} | {r.q10:.3f} à {r.q90:.3f} ({r.classe_bornes}) | "
                 f"{r.T2_mmpa:.0f} | {r.T2c_mmpa:.0f} ({r.T2c_bas_mmpa:.0f} à {r.T2c_haut_mmpa:.0f}) | {cmp_} |")
    L += ["", "## Décision (fixée avant le calcul)", "",
          ("T2c remplace T2 dans `nappes_ressource.py` ; l'atlas par bassin et par sous-bassin est refait, avec les 36 "
           "sous-bassins avant et après correction." if h_r2 else
           "T2 reste la valeur centrale ; le bilan est publié avec la fourchette T2 / T2c, et les sous-bassins dont la classe "
           "de bilan change sont marqués « incertains »."), "",
          "Limites : le karst n'est pas un groupe BGS distinct (classé « Sedimentary ») ; bornes tirées de sites africains ; "
          "pluie de la grille BGS ; la fluctuation de nappe des sites du Sud peut elle-même sous-estimer la recharge.", ""]
    (ROOT / "validation" / "controle_recharge.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"T2 {n_ok['T2']}/{len(ok['T2'])} ; T2c {n_ok['T2c']}/{len(ok['T2c'])} ; H-R2 {'soutenue' if h_r2 else 'non soutenue'}")


if __name__ == "__main__":
    main()
