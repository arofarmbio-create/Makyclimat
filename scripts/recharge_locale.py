"""Recharge transférée corrigée par les mesures malgaches, T2L (validation/protocole_recharge_locale.md, fixé avant le
calcul le 09/11/2026).

Résidu d'un site : e = ln(mesurée / T2), recharge mensuelle par fluctuation de nappe (12 sites retenus, MGMERL et GROSoM).
M0 : T2 ; M1 : facteur unique ; M2 : facteur par groupe d'aquifère (socle / autres), repli sur M1 si moins de 2 sites ;
M3 : M2 + résidu restant pondéré par exp(−d/L), ramené vers zéro (c = Σwu / (1 + Σw)), même groupe, L = 25 km.
Validation : groupes de sites à moins de 20 km laissés de côté (principal) et site par site. Site retrouvé si la
prédiction tombe dans [Sy bas ; Sy haut]. H-L1 : M2 retrouve au moins 6 sites sur 12 et divise par 2 l'erreur médiane
de M0. H-L2 : M3 retrouve au moins un site de plus que M2 avec une erreur médiane plus faible.
Carte : domaine = groupe représenté par au moins 2 sites et site de ce groupe à moins de 100 km ; hors domaine, T2.
Entrées hors dépôt (séries MGMERL et GROSoM, grille T2) : calcul local. Sorties : validation/recharge_locale.md,
validation/recharge_locale_sites.csv (sans coordonnées), inputs/hydrogeologie/recharge_t2l.csv.
Usage : python scripts/recharge_locale.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib

import numpy as np
import pandas as pd

from common import ROOT, country_data_dir

L_KM, L_SENS = 25.0, (10.0, 50.0)
CLUSTER_KM, DOMAIN_KM, MIN_GROUP = 20.0, 100.0, 2
H_L1_HITS = 6
MODELS = ["M0", "M1", "M2", "M3"]


def group2(g) -> np.ndarray:
    return np.where(np.asarray(g).astype(str) == "Basement", "socle", "autres")


def dist_km(lat1, lon1, lat2, lon2) -> np.ndarray:
    """Distances orthodromiques (km), matrice len(1) × len(2)."""
    p1, p2 = np.radians(np.asarray(lat1, float))[:, None], np.radians(np.asarray(lat2, float))[None, :]
    dl = np.radians(np.asarray(lon2, float))[None, :] - np.radians(np.asarray(lon1, float))[:, None]
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def clusters(lat, lon, km: float = CLUSTER_KM) -> np.ndarray:
    """Groupes de sites par lien simple : deux sites à moins de km sont dans le même groupe."""
    d = dist_km(lat, lon, lat, lon)
    n = len(d)
    lab = np.arange(n)
    changed = True
    while changed:
        changed = False
        for i in range(n):
            for j in range(n):
                if d[i, j] < km and lab[i] != lab[j]:
                    m = min(lab[i], lab[j])
                    lab[lab == lab[i]], lab[lab == lab[j]] = m, m
                    changed = True
    return np.unique(lab, return_inverse=True)[1]


def fit(tr: pd.DataFrame) -> dict:
    """Facteur unique, facteurs par groupe, résidus après M2 (pour M3)."""
    e = np.log(tr.mes / tr.t2)
    glob = float(np.median(e))
    grp = {g: float(np.median(e[tr.g2 == g])) for g in tr.g2.unique() if (tr.g2 == g).sum() >= MIN_GROUP}
    u = e - np.array([grp.get(g, glob) for g in tr.g2])
    return {"glob": glob, "grp": grp, "lat": tr.lat.to_numpy(), "lon": tr.lon.to_numpy(), "g2": tr.g2.to_numpy(), "u": np.asarray(u)}


def predict(m: dict, t2, g2, lat, lon, model: str, L: float = L_KM) -> np.ndarray:
    t2, g2 = np.asarray(t2, float), np.asarray(g2)
    if model == "M0":
        return t2
    if model == "M1":
        return t2 * np.exp(m["glob"])
    f = np.array([m["grp"].get(g, m["glob"]) for g in g2])
    if model == "M2":
        return t2 * np.exp(f)
    d = dist_km(lat, lon, m["lat"], m["lon"])
    w = np.exp(-d / L) * (g2[:, None] == m["g2"][None, :])
    c = (w * m["u"][None, :]).sum(1) / (1.0 + w.sum(1))
    return t2 * np.exp(f + c)


def cross_validate(tab: pd.DataFrame, folds: np.ndarray, L: float = L_KM) -> pd.DataFrame:
    out = tab[["site"]].copy()
    for k in MODELS:
        out[k] = np.nan
    for f in np.unique(folds):
        te, tr = folds == f, folds != f
        m = fit(tab[tr])
        for k in MODELS:
            out.loc[te, k] = predict(m, tab.t2[te], tab.g2[te], tab.lat[te], tab.lon[te], k, L)
    return out


def score(pred, mes, lo, hi) -> tuple[int, float]:
    pred, mes, lo, hi = (np.asarray(x, float) for x in (pred, mes, lo, hi))
    return int(((pred >= lo) & (pred <= hi)).sum()), float(np.median(np.abs(np.log10(pred / mes))))


def main() -> None:
    import recharge_fluctuation as RF
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    cdir = country_data_dir(args.country)
    tab = RF.build_sites(cdir)
    tab = tab[tab.retenu.fillna(False).astype(bool)].reset_index(drop=True)
    tab = tab.assign(mes=tab.r_mm, t2=tab.t2_mm, g2=group2(tab.groupe))
    folds_c = clusters(tab.lat, tab.lon)
    folds_s = np.arange(len(tab))

    def table(cv):
        return {k: score(cv[k], tab.mes, tab.r_bas, tab.r_haut) for k in MODELS}
    cv_c, cv_s = cross_validate(tab, folds_c), cross_validate(tab, folds_s)
    S_c, S_s = table(cv_c), table(cv_s)
    sens = {L: table(cross_validate(tab, folds_c, L))["M3"] for L in L_SENS}
    h1 = S_c["M2"][0] >= H_L1_HITS and S_c["M2"][1] <= S_c["M0"][1] / 2
    h2 = S_c["M3"][0] >= S_c["M2"][0] + 1 and S_c["M3"][1] < S_c["M2"][1]

    # Carte T2L (apprise sur les 12 sites), domaine de validité
    grid = pd.read_csv(cdir / "nappes_mondiales" / "recharge_transferee.csv")
    m = fit(tab)
    g2 = group2(grid.Aquifer_group.fillna(""))
    best = "M3" if h2 else "M2"
    t2l = predict(m, grid.T2_mmpa, g2, grid.lat, grid.lon, best)
    d = dist_km(grid.lat, grid.lon, tab.lat, tab.lon)
    same = g2[:, None] == tab.g2.to_numpy()[None, :]
    near = np.where(same, d, np.inf).min(1)
    represented = np.isin(g2, [g for g in m["grp"]])
    dom = represented & (near <= DOMAIN_KM)
    out = grid[["lon", "lat", "Aquifer_group", "T2_mmpa"]].copy()
    out["groupe_t2l"] = g2
    out["T2L_mmpa"] = np.where(dom, t2l, grid.T2_mmpa)
    out["domaine"] = np.where(dom, "dans le domaine", "hors domaine")
    out["distance_site_km"] = np.where(np.isfinite(near), near, np.nan)
    hd = ROOT / "inputs" / "hydrogeologie"
    hd.mkdir(parents=True, exist_ok=True)
    fp = hd / "recharge_t2l.csv"
    out.round(4).to_csv(fp, index=False, lineterminator="\n")
    sha = hashlib.sha256(fp.read_bytes()).hexdigest()

    sites = tab[["site", "source", "groupe", "t2_mm", "mes", "r_bas", "r_haut"]].copy()
    sites["groupe_validation"] = folds_c
    for k in MODELS:
        sites[f"{k}_groupes"] = cv_c[k].to_numpy()
    sites.round(2).to_csv(ROOT / "validation" / "recharge_locale_sites.csv", index=False)

    L = ["# Recharge corrigée par les mesures malgaches (T2L)", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/recharge_locale.py`, selon `validation/protocole_recharge_locale.md` "
         "(fixé avant le calcul). Calcul local (séries MGMERL et GROSoM hors dépôt).", "",
         f"Facteurs appris sur les 12 sites : unique ×{np.exp(m['glob']):.2f} ; " +
         " ; ".join(f"{g} ×{np.exp(v):.2f}" for g, v in m["grp"].items()) + ".", "",
         f"## Validation ({len(np.unique(folds_c))} groupes de sites à moins de {CLUSTER_KM:.0f} km laissés de côté : critère principal)", "",
         "| Modèle | Sites retrouvés (groupes) | Erreur médiane log₁₀ (groupes) | Sites retrouvés (site par site) | Erreur (site par site) |",
         "|---|---|---|---|---|"]
    names = {"M0": "M0 : T2 sans correction", "M1": "M1 : facteur unique", "M2": "M2 : facteur par groupe d'aquifère",
             "M3": f"M3 : M2 + correction locale (L = {L_KM:.0f} km)"}
    for k in MODELS:
        L.append(f"| {names[k]} | {S_c[k][0]} sur {len(tab)} | {S_c[k][1]:.2f} (facteur {10 ** S_c[k][1]:.1f}) | "
                 f"{S_s[k][0]} sur {len(tab)} | {S_s[k][1]:.2f} |")
    L += ["", "Sensibilité de M3 au rayon (groupes) : " + " ; ".join(f"L = {k:.0f} km : {v[0]} retrouvés, erreur {v[1]:.2f}" for k, v in sens.items()) + ".", "",
          f"**H-L1 {'soutenue' if h1 else 'non soutenue'}** (M2 : au moins {H_L1_HITS} sites sur 12 et erreur au plus la moitié de M0).",
          f"**H-L2 {'soutenue' if h2 else 'non soutenue'}** (M3 : au moins un site de plus que M2 et erreur plus faible).", "",
          "## Sites (prédictions des groupes laissés de côté, mm/an)", "",
          "| Site | Source | Groupe | Mesurée [Sy bas ; haut] | M0 | M1 | M2 | M3 |", "|---|---|---|---|---|---|---|---|"]
    for i, x in sites.iterrows():
        L.append(f"| {x.site} | {x.source} | {x.groupe} | {x.mes:.0f} [{x.r_bas:.0f} ; {x.r_haut:.0f}] | " +
                 " | ".join(f"{x[f'{k}_groupes']:.0f}" for k in MODELS) + " |")
    din = out.domaine == "dans le domaine"
    L += ["", f"## Carte T2L (modèle {best})", "",
          f"{int(din.sum())} mailles sur {len(out)} dans le domaine de validité ({din.mean():.0%}). Recharge médiane dans le "
          f"domaine : T2 {out.T2_mmpa[din].median():.0f} → T2L {out.T2L_mmpa[din].median():.0f} mm/an.", "",
          "| Groupe | Mailles dans le domaine | T2 médiane | T2L médiane |", "|---|---|---|---|"]
    for g, s in out[din].groupby("groupe_t2l"):
        L.append(f"| {g} | {len(s)} | {s.T2_mmpa.median():.0f} | {s.T2L_mmpa.median():.0f} |")
    L += ["", "## Validation prospective (section 6 du protocole)", "",
          f"Carte figée le {dt.date.today().isoformat()} : `inputs/hydrogeologie/recharge_t2l.csv`, empreinte SHA-256 "
          f"`{sha}`. Toute nouvelle mesure de recharge sera comparée à ces valeurs, sans recalcul ; réussite si au moins 60 % "
          "des nouveaux sites du domaine sont retrouvés.", "",
          "## Décision (fixée avant le calcul)", "",
          ("T2L devient la valeur centrale dans son domaine ; l'atlas par sous-bassin est refait et comparé à l'atlas T2."
           if h1 else "T2 reste la valeur centrale ; T2L est publiée comme sensibilité."), "",
          "Limites : 12 sites, tous dans le Sud et le Sud-Ouest ; fourchette de Sy d'un facteur 3 à 5 ; méthode mensuelle "
          "(la journalière donne des recharges plus fortes) ; puits GROSoM en partie karstiques, classés non consolidés.", ""]
    (ROOT / "validation" / "recharge_locale.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"H-L1 {h1} ; H-L2 {h2} ; groupes {len(np.unique(folds_c))}")


if __name__ == "__main__":
    main()
