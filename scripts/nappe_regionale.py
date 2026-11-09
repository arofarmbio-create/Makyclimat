"""Nappe régionale profonde : inverser le raisonnement depuis la base (validation/protocole_nappe_regionale.md, fixé
avant le calcul le 09/11/2026).

Forages BushProof (mêmes 538 qu'au bilan de chlorure) : charge h = NivPiezo_m (sinon Alt_m − SWL_m), profondeur captée
z = base de la crépine la plus profonde, pluie locale P (maille de la grille T2). Spearman au forage, intervalles à 95 %
par rééchantillonnage de blocs de 20 km (2 000 tirages, graine 20261109).
H-D1 : ρ(Cl, h) < 0 ; H-D2 : ρ(Cl, z) ≠ 0 ; H-D3 : |ρ(Cl, h)| > |ρ(Cl, P)| ; H-D4 : au bloc, corrélation partielle
T2 / recharge par chlorure (central) à charge fixée ≥ 0 alors que la brute est < 0 ; H-D5 : charge des puits à sec
(interpolée depuis les forages) différente de celle de la référence. Contrôle préalable : |ρ(Cl, P)| ≥ 0,3 avec
intervalle sans 0 → H-D3 sans objet.
Données brutes hors dépôt ; sortie agrégée : validation/nappe_regionale.md.
Usage : python scripts/nappe_regionale.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob

import numpy as np
import pandas as pd

from common import ROOT, country_data_dir

SEED, N_BOOT, MIN_TYPE, K_INTERP = 20261109, 2000, 30, 8


def rang(x) -> np.ndarray:
    return pd.Series(np.asarray(x, float)).rank().to_numpy()


def spearman(x, y) -> float:
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 5:
        return float("nan")
    return float(np.corrcoef(rang(x[ok]), rang(y[ok]))[0, 1])


def partielle(x, y, z) -> float:
    """Corrélation partielle de Spearman de x et y, z fixé (résidus des rangs)."""
    x, y, z = (np.asarray(v, float) for v in (x, y, z))
    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    if ok.sum() < 5:
        return float("nan")
    rx, ry, rz = rang(x[ok]), rang(y[ok]), rang(z[ok])
    A = np.c_[np.ones(len(rz)), rz]
    ex = rx - A @ np.linalg.lstsq(A, rx, rcond=None)[0]
    ey = ry - A @ np.linalg.lstsq(A, ry, rcond=None)[0]
    return float(np.corrcoef(ex, ey)[0, 1])


def boot(df: pd.DataFrame, stats: dict, n=N_BOOT, seed=SEED) -> dict:
    """Valeurs rééchantillonnées par blocs (colonne « bloc ») de chaque statistique (fonction de df)."""
    rng = np.random.default_rng(seed)
    groups = {k: g.index.to_numpy() for k, g in df.groupby("bloc")}
    keys = np.array(list(groups))
    out = {k: [] for k in stats}
    for _ in range(n):
        s = df.loc[np.concatenate([groups[k] for k in rng.choice(keys, len(keys), replace=True)])]
        for k, f in stats.items():
            out[k].append(f(s))
    return {k: np.array(v) for k, v in out.items()}


def ic(v) -> tuple[float, float]:
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    return (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) else (np.nan, np.nan)


def charge(f: pd.DataFrame) -> pd.Series:
    h = pd.to_numeric(f.get("NivPiezo_m"), errors="coerce")
    alt = pd.to_numeric(f.get("Alt_m"), errors="coerce") - pd.to_numeric(f.get("SWL_m"), errors="coerce")
    return h.where(h.notna(), alt)


def profondeur(f: pd.DataFrame) -> pd.Series:
    cols = [c for c in f.columns if c.startswith("BasCrep") and c.endswith("_m")]
    return f[cols].apply(pd.to_numeric, errors="coerce").max(axis=1) if cols else pd.Series(np.nan, index=f.index)


def interp_charge(lat, lon, plat, plon, ph, exclure_soi=False) -> np.ndarray:
    """Charge interpolée (moyenne des K forages les plus proches, pondérée par 1/d²)."""
    from sklearn.neighbors import BallTree
    ok = np.isfinite(ph)
    tree = BallTree(np.radians(np.c_[plat[ok], plon[ok]]), metric="haversine")
    k = min(K_INTERP + (1 if exclure_soi else 0), int(ok.sum()))
    d, j = tree.query(np.radians(np.c_[lat, lon]), k=k)
    if exclure_soi:
        d, j = d[:, 1:], j[:, 1:]
    w = 1.0 / np.maximum(d * 6371.0, 0.05) ** 2
    return (ph[ok][j] * w).sum(1) / w.sum(1)


def main() -> None:
    import puits_a_sec as PS
    import recharge_chlorure as RC
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    cdir = country_data_dir(args.country)
    fs = glob.glob(str(cdir / "bushproof_raw" / "recuperation" / "*Forages*.csv"))
    tout = pd.concat([pd.read_csv(x) for x in fs], ignore_index=True)
    tout["lat"], tout["lon"] = pd.to_numeric(tout.Lat_DD, errors="coerce"), pd.to_numeric(tout.Long_DD, errors="coerce")
    tout["cl"] = pd.to_numeric(tout["Cl-_mg/l"], errors="coerce")
    tout["h"], tout["z"] = charge(tout), profondeur(tout)
    coast_zip = glob.glob(str(cdir / "chlorure_pluie_raw" / "natural_earth" / "*.zip"))[0]
    f = tout[(tout.cl > 0) & tout.lat.notna() & tout.lon.notna()].copy()
    f = f.assign(_k=f.lat.round(5).astype(str) + f.lon.round(5).astype(str) + f.cl.astype(str)).drop_duplicates("_k").reset_index(drop=True)
    f["dist_km"] = RC.distance_cote(f.lat, f.lon, coast_zip)
    f, _ = RC.filtre(f)
    f = f.reset_index(drop=True).copy()
    t2k = pd.read_csv(ROOT / "inputs" / "hydrogeologie" / "recharge_t2k.csv")
    f["P"] = t2k.LTA_P_mmpa.to_numpy()[RC.nearest(f.lat, f.lon, t2k.lat, t2k.lon)]
    f["bloc"] = PS.blocs(f.lat, f.lon)
    ions = f[[c for c in RC.ION_COLS if c in f]].apply(pd.to_numeric, errors="coerce")
    f["mineral"] = ions.sum(axis=1, min_count=3)
    na = pd.to_numeric(f.get("Na+_mg/l"), errors="coerce")
    f["clna"] = (f.cl / na).where(na > 0)

    st = {"Cl_h": lambda s: spearman(s.cl, s.h), "Cl_z": lambda s: spearman(s.cl, s.z), "Cl_P": lambda s: spearman(s.cl, s.P),
          "diff": lambda s: abs(spearman(s.cl, s.h)) - abs(spearman(s.cl, s.P)),
          "Cl_h_cote": lambda s: partielle(s.cl, s.h, s.dist_km),
          "min_z": lambda s: spearman(s.mineral, s.z), "clna_z": lambda s: spearman(s.clna, s.z)}
    obs = {k: fn(f) for k, fn in st.items()}
    bs = boot(f, st)
    I = {k: ic(v) for k, v in bs.items()}
    pre = abs(obs["Cl_P"]) >= 0.3 and (I["Cl_P"][0] > 0 or I["Cl_P"][1] < 0)
    h1 = obs["Cl_h"] < 0 and I["Cl_h"][1] < 0
    h2 = I["Cl_z"][0] > 0 or I["Cl_z"][1] < 0
    h6 = obs["min_z"] > 0 and I["min_z"][0] > 0 and obs["clna_z"] < 0 and I["clna_z"][1] < 0
    h3 = (not pre) and obs["diff"] > 0 and I["diff"][0] > 0
    par_type = []
    for t, g in f.groupby(f.TypeAquif1.fillna("non renseigné")):
        if len(g) >= MIN_TYPE:
            par_type.append((t, len(g), spearman(g.cl, g.h), spearman(g.cl, g.z), spearman(g.mineral, g.z),
                             spearman(g.clna, g.z), float(g.clna.median())))

    # H-D4 : au bloc
    z = f.groupby("bloc").agg(n=("cl", "size"), cl=("cl", "median"), lat=("lat", "mean"), lon=("lon", "mean"), h=("h", "median")).reset_index()
    z = z[z.n >= RC.MIN_ZONE].reset_index(drop=True)
    z["dist_km"] = RC.distance_cote(z.lat, z.lon, coast_zip)
    t2l = pd.read_csv(ROOT / "inputs" / "hydrogeologie" / "recharge_t2l.csv")
    z["T2"] = t2l.T2_mmpa.to_numpy()[RC.nearest(z.lat, z.lon, t2l.lat, t2l.lon)]
    z["P"] = t2k.LTA_P_mmpa.to_numpy()[RC.nearest(z.lat, z.lon, t2k.lat, t2k.lon)]
    z["R"] = RC.depot(z.P, z.dist_km, RC.SCENARIOS["central"]) / z.cl
    brut, part = spearman(z.T2, z.R), partielle(z.T2, z.R, z.h)
    h4 = brut < 0 and part >= 0

    # H-D5 : puits à sec (charge interpolée depuis les forages ; référence en excluant le forage lui-même)
    ref_all = tout.dropna(subset=["lat", "lon"]).copy()
    ref_all = ref_all.assign(_k=ref_all.lat.round(5).astype(str) + ref_all.lon.round(5).astype(str)).drop_duplicates("_k").reset_index(drop=True)
    ph = ref_all.h.to_numpy(float)
    u = pd.read_csv(cdir / "unesco_puits_raw" / "madagascar_wells_full_english_converted.csv")
    box = u.latitude.between(ref_all.lat.min(), ref_all.lat.max()) & u.longitude.between(ref_all.lon.min(), ref_all.lon.max())
    pr, _ = PS.selection(u)
    cas = u.loc[pr & box, ["latitude", "longitude"]].rename(columns={"latitude": "lat", "longitude": "lon"}).reset_index(drop=True)
    cas["hh"] = interp_charge(cas.lat.to_numpy(), cas.lon.to_numpy(), ref_all.lat.to_numpy(), ref_all.lon.to_numpy(), ph)
    ok = np.isfinite(ph)
    ref = ref_all[ok].reset_index(drop=True)
    ref["hh"] = interp_charge(ref.lat.to_numpy(), ref.lon.to_numpy(), ref_all.lat.to_numpy(), ref_all.lon.to_numpy(), ph, exclure_soi=True)
    a5 = PS.auc(cas.hh, ref.hh)
    b5 = PS.bootstrap(cas.rename(columns={"hh": "H"}), ref.rename(columns={"hh": "H"}), ["H"])["H"]
    i5 = ic(b5)
    h5 = i5[0] > 0.5 or i5[1] < 0.5

    def fm(v):
        return f"{v:+.2f}"
    L = ["# Nappe régionale profonde : inverser le raisonnement", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/nappe_regionale.py`, selon `validation/protocole_nappe_regionale.md` "
         "(fixé avant le calcul). Forages : Al-Zoubaidy, Monteleone et Bünzli (2023), BushProof / DDC. Calcul local, données brutes hors dépôt.", "",
         f"{len(f)} forages avec chlorure ({int(f.h.notna().sum())} avec charge, {int(f.z.notna().sum())} avec profondeur de crépine) ; "
         f"{f.bloc.nunique()} blocs de 20 km. Spearman au forage ; intervalles à 95 % par blocs.", "",
         "## Contrôle préalable : le cadre local échoue-t-il ?", "",
         f"ρ(chlorure, pluie locale) = {fm(obs['Cl_P'])} [{fm(I['Cl_P'][0])} ; {fm(I['Cl_P'][1])}] → "
         f"**{'le cadre local tient (H-D3 sans objet)' if pre else 'le cadre local n échoue pas à expliquer : il n explique pas le chlorure'.replace('n échoue pas à expliquer : il n', 'n')}**.", "",
         "## Hypothèses", "", "| Hypothèse | Valeur | Intervalle à 95 % | Verdict |", "|---|---|---|---|",
         f"| H-D1 : ρ(chlorure, charge) < 0 | {fm(obs['Cl_h'])} | {fm(I['Cl_h'][0])} ; {fm(I['Cl_h'][1])} | **{'soutenue' if h1 else 'non soutenue'}** |",
         f"| H-D2 : ρ(chlorure, profondeur captée) ≠ 0 | {fm(obs['Cl_z'])} | {fm(I['Cl_z'][0])} ; {fm(I['Cl_z'][1])} | **{'soutenue' if h2 else 'non soutenue'}** |",
         f"| H-D3 : \\|ρ(Cl, charge)\\| − \\|ρ(Cl, pluie)\\| > 0 | {fm(obs['diff'])} | {fm(I['diff'][0])} ; {fm(I['diff'][1])} | **{'soutenue' if h3 else 'non soutenue'}** |",
         f"| H-D4 : T2 / recharge par chlorure au bloc ({len(z)} blocs), brute → à charge fixée | {fm(brut)} → {fm(part)} | — | **{'soutenue' if h4 else 'non soutenue'}** |",
         f"| H-D5 : charge des puits à sec ({len(cas)}) contre référence ({len(ref)}), AUC | {a5:.3f} | {i5[0]:.3f} ; {i5[1]:.3f} | **{'soutenue' if h5 else 'non soutenue'}** |",
         f"| H-D6 : avec la profondeur, minéralisation ↑ et Cl/Na ↓ | {fm(obs['min_z'])} et {fm(obs['clna_z'])} | "
         f"{fm(I['min_z'][0])} ; {fm(I['min_z'][1])} et {fm(I['clna_z'][0])} ; {fm(I['clna_z'][1])} | **{'soutenue' if h6 else 'non soutenue'}** |",
         "", f"Descriptif : ρ(chlorure, charge) à distance à la côte fixée = {fm(obs['Cl_h_cote'])} [{fm(I['Cl_h_cote'][0])} ; {fm(I['Cl_h_cote'][1])}] "
         "(contrôle de l'effet des embruns, plus forts en bas près de la côte).", "",
         "## Par type d'aquifère (au moins 30 forages)", "", "| Type | Forages | ρ(Cl, charge) | ρ(Cl, profondeur) | ρ(minéralisation, profondeur) | ρ(Cl/Na, profondeur) | Cl/Na médian (eau de mer : 1,80) |",
          "|---|---|---|---|---|---|---|"]
    for t, n, a, b, c, d, e in par_type:
        L.append(f"| {t} | {n} | {fm(a)} | {fm(b)} | {fm(c)} | {fm(d)} | {e:.2f} |")
    L += ["", f"Cl/Na médian, tous forages : {f.clna.median():.2f} (eau de mer et embruns : 1,80 en masse ; nettement plus bas : "
          "sodium venu des roches ou des sols ; nettement plus haut : autre source de chlorure)."]
    L += ["", "## Décision (fixée avant le calcul)", "",
          ("Le cadre « nappe régionale » devient le cadre de travail du module M3 pour le Grand Sud : bilan de chlorure le long "
           "des lignes d'écoulement, recharge rattachée aux zones d'alimentation, bassins hydrogéologiques refaits avec la charge mesurée."
           if (h1 and h3) else "Le cadre local reste ; les inversions restent inexpliquées par ce test et sont publiées comme telles."), "",
          "Limites : charges mesurées à des dates différentes ; zone ZH10 absente ; socle fracturé majoritaire ; charge des puits à sec "
          "interpolée (8 forages les plus proches, 1/d²).", ""]
    (ROOT / "validation" / "nappe_regionale.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print({"H6": h6, "pre": pre, "H1": h1, "H2": h2, "H3": h3, "H4": h4, "H5": h5, **{k: round(v, 3) for k, v in obs.items()}, "brut": round(brut, 3), "part": round(part, 3), "auc5": round(a5, 3)})


if __name__ == "__main__":
    main()
