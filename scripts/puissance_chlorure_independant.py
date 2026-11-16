"""Analyse de puissance du test T2 contre T2L par bilan de chlorure, dépôt mesuré, blocs neufs (étape T-H2.1).

Fixée AVANT toute donnée du test (validation/protocole_chlorure_independant.md). Ne lit que des fichiers publics
déjà versionnés : les blocs de l'analyse après coup R-50 (validation/recharge_chlorure_blocs_zones.csv, données déjà
vues, servant ici de vraisemblance de planification) et la carte figée T2L (inputs/hydrogeologie/recharge_t2l.csv).
Aucune donnée du test (dépôt mesuré, forages neufs) n'existe encore : rien n'est testé ici.

Hypothèses (protocole, section 6) :
- H-I1 (niveau) : T2 surestime. Test du signe unilatéral sur log10(T2 / R), p < 0,05, avec le dépôt × 1,5 (le
  scénario le moins favorable à H-I1).
- H-I2 (structure) : T2L ordonne mieux les blocs que T2 une fois le biais de niveau de chaque modèle retiré.
  Écart centré c = |e − médiane(e)|, e = log10(modèle / R) ; Wilcoxon apparié unilatéral sur c(T2) − c(T2L),
  p < 0,05, et réduction de la médiane de c d'au moins 30 %. Invariant à une erreur uniforme du dépôt.

Sortie : validation/puissance_chlorure_independant.md (+ .csv).
"""
from __future__ import annotations

import argparse
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom

ROOT = Path(__file__).resolve().parents[1]
BLOCS = ROOT / "validation" / "recharge_chlorure_blocs_zones.csv"
T2L = ROOT / "inputs" / "hydrogeologie" / "recharge_t2l.csv"
OUT_MD = ROOT / "validation" / "puissance_chlorure_independant.md"
OUT_CSV = ROOT / "validation" / "puissance_chlorure_independant.csv"

ALPHA = 0.05
REDUC_MIN = 0.30
K_DEPOT = np.log10(1.5)
BLOC_KM, LAT_REF = 20.0, -23.0
SEED = 20261116
N_GRILLE = [6, 8, 10, 12, 15, 18, 24, 30]


# ---------- tests (exacts, vectorisables) ----------
@lru_cache(maxsize=None)
def _w_queue(n: int) -> np.ndarray:
    """P(W+ >= w) exacte sous H0 pour le Wilcoxon signé de taille n (sans ex aequo)."""
    m = n * (n + 1) // 2
    c = np.zeros(m + 1)
    c[0] = 1.0
    for k in range(1, n + 1):
        c[k:] = c[k:] + c[:-k].copy()
    p = c / 2.0 ** n
    return p[::-1].cumsum()[::-1]


def wilcoxon_sup(d: np.ndarray) -> float:
    """p unilatéral (d > 0) du Wilcoxon signé exact ; zéros retirés (méthode de Wilcoxon)."""
    d = d[np.abs(d) > 1e-12]
    n = len(d)
    if n == 0:
        return 1.0
    rangs = pd.Series(np.abs(d)).rank().to_numpy()
    w = rangs[d > 0].sum()
    return float(_w_queue(n)[min(int(np.ceil(w - 1e-9)), n * (n + 1) // 2)])


def signe_sup(e: np.ndarray) -> float:
    """p unilatéral du test du signe (médiane de e > 0)."""
    e = e[np.abs(e) > 1e-12]
    return float(binom.sf(int((e > 0).sum()) - 1, len(e), 0.5)) if len(e) else 1.0


def h_i1(t2, r) -> bool:
    return signe_sup(t2 - (r + K_DEPOT)) < ALPHA


def h_i2(ta, tb, r) -> tuple[bool, float, float]:
    """tb (candidat) contre ta (référence). Renvoie (soutenue, p, réduction)."""
    ea, eb = ta - r, tb - r
    ca, cb = np.abs(ea - np.median(ea)), np.abs(eb - np.median(eb))
    p = wilcoxon_sup(ca - cb)
    ma = np.median(ca)
    red = 1 - np.median(cb) / ma if ma > 0 else -np.inf
    return (p < ALPHA and red >= REDUC_MIN), p, red


# ---------- blocs ----------
def blocs(lat, lon) -> np.ndarray:
    dy = BLOC_KM / 111.0
    dx = BLOC_KM / (111.0 * np.cos(np.radians(LAT_REF)))
    return np.floor(np.asarray(lat) / dy).astype(int) * 100000 + np.floor(np.asarray(lon) / dx).astype(int)


def km(lat1, lon1, lat2, lon2) -> np.ndarray:
    la1, lo1, la2, lo2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def blocs_disponibles(z: pd.DataFrame) -> pd.DataFrame:
    """Plafond : blocs de la grille fixe couverts au moins à moitié par le domaine T2L (où T2L ≠ T2), dont le
    centre approché est à au moins 20 km du centre de tout bloc R-50."""
    g = pd.read_csv(T2L)
    g = g[(g.domaine != "hors domaine") & (np.abs(np.log10(g.T2L_mmpa / g.T2_mmpa)) > 1e-6)]
    pas = np.median(np.diff(np.sort(g.lat.unique())))
    off = (np.arange(8) + 0.5) / 8 - 0.5
    rows = [(c.lat + a * pas, c.lon + b * pas, c.groupe_t2l) for c in g.itertuples() for a in off for b in off]
    f = pd.DataFrame(rows, columns=["lat", "lon", "groupe"])
    f["bloc"] = blocs(f.lat, f.lon)
    f = f.groupby("bloc").agg(lat=("lat", "mean"), lon=("lon", "mean"), groupe=("groupe", lambda s: s.mode()[0]),
                              part=("lat", "size"))
    f = f[f.part >= 0.5 * f.part.max()]
    d = km(f.lat.to_numpy()[:, None], f.lon.to_numpy()[:, None], z.lat.to_numpy()[None, :], z.lon.to_numpy()[None, :])
    f["neuf"] = d.min(axis=1) >= BLOC_KM
    return f


# ---------- simulation ----------
def simuler(tri, n, sig_e, sig_u, rng, nsim, mode="boot", g=0.0) -> tuple[float, float]:
    """Puissance de H-I1 et de H-I2. tri = log10 (T2, T2L, R vraie) des blocs de planification."""
    k1 = k2 = 0
    for _ in range(nsim):
        s = tri[rng.integers(0, len(tri), n)]
        t2, t2l, r = s[:, 0].copy(), s[:, 1].copy(), s[:, 2].copy()
        if mode == "param":  # T2L = biais propre + (1 − g) × structure d'erreur de T2 + bruit propre
            e2 = t2 - r
            t2l = r + np.median(s[:, 1] - r) + (1 - g) * (e2 - np.median(e2)) + rng.normal(0, 0.15, n)
        r_obs = r + rng.normal(0, sig_u) + rng.normal(0, sig_e, n)
        k1 += h_i1(t2, r_obs)
        k2 += h_i2(t2, t2l, r_obs)[0]
    return k1 / nsim, k2 / nsim


def pct(x: float) -> str:
    return f"{x:.0%}".replace("%", " %")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--nsim", type=int, default=2000)
    args = ap.parse_args()
    rng = np.random.default_rng(SEED)

    z = pd.read_csv(BLOCS)
    zd = z[z.dom == "dans le domaine"].copy()
    lt2, ll = np.log10(zd.T2.to_numpy()), np.log10(zd.T2L.to_numpy())
    decal = np.median(ll - lt2)

    # 1. Contrôle sur les données déjà vues (sans bruit)
    ctrl = []
    for sc in ("bas", "central", "haut"):
        r = np.log10(zd[f"R_{sc}"].to_numpy())
        a = h_i2(lt2, ll, r)
        b = h_i2(lt2, lt2 + decal, r)
        ctrl.append((sc, h_i1(lt2, r), a, b))

    # 2. Plafond de blocs neufs
    dispo = blocs_disponibles(z)
    nb = dispo[dispo.neuf].groupby("groupe").size().to_dict()

    # 3. Puissance
    res = []
    cas = [(f"blocs R-50, {sc}", np.column_stack([lt2, ll, np.log10(zd[f'R_{sc}'].to_numpy())]), "boot", 0.0)
           for sc in ("bas", "central", "haut")]
    tri_c = cas[1][1]
    cas += [(f"paramétrique, structure {int(g * 100)} %", tri_c, "param", g) for g in (0.0, 0.3, 0.5)]
    for nom, tri, mode, g in cas:
        for sig_e in (0.1, 0.2, 0.3):
            for n in N_GRILLE:
                p1, p2 = simuler(tri, n, sig_e, 0.1, rng, args.nsim, mode, g)
                res.append(dict(verite=nom, sig_e=sig_e, sig_u=0.1, n=n, puissance_HI1=p1, puissance_HI2=p2))
    df = pd.DataFrame(res)
    df.to_csv(OUT_CSV, index=False, float_format="%.3f")

    L = ["# Analyse de puissance : T2 contre T2L, dépôt de chlorure mesuré, blocs neufs (T-H2.1)", "",
         f"Générée par `scripts/puissance_chlorure_independant.py` ({args.nsim} tirages par case, graine {SEED}), "
         "selon `validation/protocole_chlorure_independant.md`. **Planification seulement** : aucune donnée du test "
         "n'existe ; les 33 blocs de R-50 dans le domaine T2L (déjà vus, après coup) servent de vraisemblance.", "",
         "- **H-I1 (niveau)** : test du signe unilatéral sur log₁₀(T2 / R), p < 0,05, dépôt mesuré × 1,5.",
         "- **H-I2 (structure)** : écart centré c = |e − médiane(e)| ; Wilcoxon apparié unilatéral sur "
         "c(T2) − c(T2L), p < 0,05, **et** médiane de c réduite d'au moins 30 %. Invariant à une erreur uniforme "
         "du dépôt.", "- σ_e : bruit propre à chaque bloc (médiane d'au moins 3 forages, forme du dépôt) ; "
         "σ_u = 0,1 : erreur commune du dépôt mesuré (log₁₀).", "",
         "## 1. La référence échoue-t-elle sur les données déjà vues ?", "",
         f"« T2 décalé » = T2 × {10 ** decal:.2f} : même niveau médian que T2L, structure de T2. Avec le critère "
         "des écarts absolus (premier jet abandonné), T2 décalé battait T2 dans les scénarios bas et central : ce "
         "critère testait le niveau, pas la correction par roche. H-I2 retire le niveau.", "",
         "| Scénario R-50 | H-I1 : T2 surestime (dépôt × 1,5) | H-I2 : T2L contre T2 (p ; réduction) "
         "| H-I2 : T2 décalé contre T2 (p ; réduction) |", "|---|---|---|---|"]
    oui = lambda b: "oui" if b else "non"
    for sc, a1, a, b in ctrl:
        L.append(f"| {sc} | {oui(a1)} | {oui(a[0])} ({a[1]:.3f} ; {a[2]:+.0%}) | {oui(b[0])} ({b[1]:.3f} ; "
                 f"{b[2]:+.0%}) |".replace("%", " %"))
    L += ["", "## 2. Blocs neufs possibles (plafond)", "",
          f"Blocs de 20 km de la grille fixe couverts au moins à moitié par le domaine T2L (où T2L ≠ T2) : "
          f"{len(dispo)} ; à au moins 20 km de tout bloc R-50 : **{int(dispo.neuf.sum())}** "
          f"({', '.join(f'{k} : {v}' for k, v in sorted(nb.items()))}). Plafond géométrique : un bloc ne compte "
          "que s'il reçoit au moins 3 forages neufs valides.", ""]
    for col, titre in (("puissance_HI1", "## 3. Puissance de H-I1 (niveau)"),
                       ("puissance_HI2", "## 4. Puissance de H-I2 (structure)")):
        piv = df.pivot_table(index=["verite", "sig_e"], columns="n", values=col, sort=False)
        L += [titre, "", "| Vérité supposée | σ_e | " + " | ".join(f"n = {n}" for n in N_GRILLE) + " |",
              "|---|---|" + "---|" * len(N_GRILLE)]
        L += [f"| {v} | {se} | " + " | ".join(pct(x) for x in row) + " |" for (v, se), row in piv.iterrows()]
        L.append("")
    L.append("Lecture : pour H-I2, « structure 0 % » donne le taux de faux positifs (T2L n'apporte que son niveau) ; "
             "pour H-I1, la ligne « haut » est proche de l'absence d'effet.")
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
