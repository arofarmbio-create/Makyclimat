"""Test H-C5 du protocole de la carte des nappes (section 10) : un modèle de recharge appris sur des pays africains
prédit-il la recharge d'un pays qu'il n'a jamais vu mieux qu'une valeur naïve ?

Données : base des 134 sites de recharge mesurée du BGS (MacDonald et al. 2021), fichier gardé hors git
(data/<pays>/bgs_recharge_raw/Recharge_data_Africa_BGS.xlsx). Versions comparées (précisions du 02/11/2026) :
  T1 : régression ridge (λ = 1) de log10(R + 1) sur pluie, jours de pluie, ETP, aridité, NDVI, groupe d'aquifère,
       occupation des terres ;
  T2 : 5 plus proches voisins, distance de Gower (avec le type de sol), poids 1 / (d + 0,01) ;
  naïf : médiane des pays d'apprentissage.
Validation : un pays laissé de côté à chaque fois ; erreur du pays = médiane des |erreur| de ses sites (log10) ;
test du signe entre pays, p < 0,025 par version (Bonferroni).
Sorties : validation/transfert_recharge_hc5.md, validation/transfert_recharge_hc5_pays.csv (résultats par pays).
Usage : python scripts/validate_transfert_recharge.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd

from common import ROOT, country_data_dir

NUM = ["LTA_P_mmpa", "LTA_WD_days", "LTA_PET_mm", "Aridity", "NDVI"]
CAT_T1 = ["Aquifer_group", "Landcover"]
CAT_T2 = ["Aquifer_group", "Soil_group", "Landcover"]
LAMBDA, K, EPS = 1.0, 5, 0.01


def target(r) -> np.ndarray:
    return np.log10(np.asarray(r, dtype=float) + 1.0)


def design(train: pd.DataFrame, test: pd.DataFrame):
    """Matrices de T1 : variables numériques standardisées sur l'apprentissage, indicatrices des catégories vues."""
    mu, sd = train[NUM].mean(), train[NUM].std().replace(0, 1)
    def mk(d):
        x = ((d[NUM] - mu) / sd).to_numpy(float)
        cats = []
        for c in CAT_T1:
            levels = sorted(train[c].astype(str).unique())[1:]          # première modalité = référence
            cats.append(np.column_stack([(d[c].astype(str) == lv).to_numpy(float) for lv in levels]) if levels else np.zeros((len(d), 0)))
        return np.column_stack([x] + cats)
    return mk(train), mk(test)


def ridge_predict(xtr, ytr, xte, lam=LAMBDA):
    xm, ym = xtr.mean(0), ytr.mean()
    a, b = xtr - xm, ytr - ym
    w = np.linalg.solve(a.T @ a + lam * np.eye(a.shape[1]), a.T @ b)
    return ym + (xte - xm) @ w


def gower(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Distance de Gower (test x apprentissage) : numériques divisées par l'étendue de l'apprentissage, qualitatives 0/1."""
    parts = []
    for c in NUM:
        rng = float(train[c].max() - train[c].min()) or 1.0
        parts.append(np.abs(test[c].to_numpy(float)[:, None] - train[c].to_numpy(float)[None, :]) / rng)
    for c in CAT_T2:
        parts.append((test[c].astype(str).to_numpy()[:, None] != train[c].astype(str).to_numpy()[None, :]).astype(float))
    return np.mean(parts, axis=0)


def knn_predict(train, ytr, test, k=K):
    d = gower(train, test)
    idx = np.argsort(d, axis=1)[:, :k]
    w = 1.0 / (np.take_along_axis(d, idx, axis=1) + EPS)
    return (w * ytr[idx]).sum(1) / w.sum(1)


def leave_one_country_out(df: pd.DataFrame) -> pd.DataFrame:
    y = target(df.Recharge_mmpa)
    rows = []
    for c in sorted(df.Country.unique()):
        te = (df.Country == c).to_numpy()
        tr = ~te
        dtr, dte = df[tr], df[te]
        xtr, xte = design(dtr, dte)
        p1 = ridge_predict(xtr, y[tr], xte)
        p2 = knn_predict(dtr, y[tr], dte)
        p0 = np.full(te.sum(), np.median(y[tr]))
        rows.append({"pays": c, "sites": int(te.sum()),
                     "erreur_naif": float(np.median(np.abs(p0 - y[te]))),
                     "erreur_T1": float(np.median(np.abs(p1 - y[te]))),
                     "erreur_T2": float(np.median(np.abs(p2 - y[te])))})
    return pd.DataFrame(rows)


def sign_test(model_err, naive_err) -> tuple[int, int, float]:
    from scipy import stats
    d = np.asarray(model_err) - np.asarray(naive_err)
    wins, n = int((d < 0).sum()), int((d != 0).sum())
    return wins, n, float(stats.binomtest(wins, n, 0.5, alternative="greater").pvalue) if n else float("nan")


def report(res: pd.DataFrame, n_sites: int) -> str:
    L = ["# H-C5 : transfert de la recharge entre pays africains (base BGS)", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/validate_transfert_recharge.py`, selon "
         "`validation/protocole_carte_nappes.md` (section 10 et précisions du 02/11/2026, fixées avant le calcul). "
         f"Données : MacDonald et al. (2021), {n_sites} sites dans {len(res)} pays ; aucun à Madagascar.", "",
         "Erreur d'un pays laissé de côté : médiane des erreurs absolues de ses sites sur log10(R + 1). Une erreur de "
         "0,3 correspond à un facteur 2 environ sur la recharge, 1,0 à un facteur 10.", "",
         "| Version | Erreur médiane entre pays | Pays où elle bat la référence naïve | p (signe) | H-C5 (p < 0,025) |",
         "|---|---|---|---|---|",
         f"| Référence naïve | {res.erreur_naif.median():.2f} | — | — | — |"]
    out = {}
    for v in ("T1", "T2"):
        w, n, p = sign_test(res[f"erreur_{v}"], res.erreur_naif)
        out[v] = p < 0.025
        L.append(f"| {v} | {res[f'erreur_{v}'].median():.2f} | {w} sur {n} | {p:.3f} | {'passe' if out[v] else 'échoue'} |")
    passed = [v for v, ok in out.items() if ok]
    L += ["", f"**Conclusion : {'H-C5 confirmée pour ' + ' et '.join(passed) + ' ; le transfert vers Madagascar peut être tenté (H-C6).' if passed else 'H-C5 non confirmée : aucune recharge transférée ne sera publiée comme estimation (règle du protocole).'}**",
          "", "Résultats par pays : `validation/transfert_recharge_hc5_pays.csv`."]
    return "\n".join(L) + "\n", passed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    f = country_data_dir(args.country) / "bgs_recharge_raw" / "Recharge_data_Africa_BGS.xlsx"
    df = pd.read_excel(f, sheet_name="data").dropna(subset=["Recharge_mmpa"] + NUM + CAT_T2)
    res = leave_one_country_out(df)
    text, passed = report(res, len(df))
    vd = ROOT / "validation"
    (vd / "transfert_recharge_hc5.md").write_text(text, encoding="utf-8")
    res.round(3).to_csv(vd / "transfert_recharge_hc5_pays.csv", index=False)
    print(text)


if __name__ == "__main__":
    main()
