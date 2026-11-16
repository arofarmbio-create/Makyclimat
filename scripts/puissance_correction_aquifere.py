"""Analyse de puissance de la correction de T2 par classe d'aquifère (étape T-H2.3).

Fixée AVANT toute donnée du test (validation/protocole_correction_par_aquifere.md). Ne lit qu'un fichier public déjà
versionné : validation/recharge_locale_sites.csv (les 12 sites de R-47, données déjà vues, servant ici de
vraisemblance de planification). Aucune donnée du test (références de recharge neuves, coupes de forage) n'existe
encore : rien n'est testé ici.

Unité : le groupe de sites (lien simple à 20 km). e = log10(recharge mesurée / T2) du groupe (médiane de ses sites).
Validation : chaque groupe neuf est retiré à son tour ; les facteurs sont appris sur les autres groupes neufs.
- M0 : T2 ; M1 : facteur unique (médiane des e d'apprentissage) ; M2c : facteur de la classe du groupe (médiane des e
  d'apprentissage de la même classe), repli sur M1 si la classe a moins de 2 groupes d'apprentissage.
- H-A1 (critère retenu) : gain G = moyenne |err M1| − moyenne |err M2c| ; p de permutation des classes entre groupes
  (effectifs conservés), p < 0,05. Le contrôle de la référence (classes sans rapport avec la roche) est la loi nulle
  même du test.
- Critère abandonné (section 2 du protocole) : Wilcoxon apparié sur |err M1| − |err M2c|, p < 0,05, et médiane de
  |err M2c| au plus 70 % de celle de M1 (règle de R-47) ; calculé pour comparaison.
- Comparaison à T2 (abandonnée, descriptive ; colonne HA2 de la table) : M2c retrouve au moins la moitié des groupes (prédiction dans [mesurée / 3 ; mesurée × 5/3]) et
  divise par au moins deux l'erreur médiane de M0 ; montré ici comme sensible au seul niveau.

Sortie : validation/puissance_correction_aquifere.md (+ .csv).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from puissance_chlorure_independant import wilcoxon_sup  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SITES = ROOT / "validation" / "recharge_locale_sites.csv"
OUT_MD = ROOT / "validation" / "puissance_correction_aquifere.md"
OUT_CSV = ROOT / "validation" / "puissance_correction_aquifere.csv"

ALPHA = 0.05
REDUC_MIN = 0.30
BAS, HAUT = 1 / 3, 5 / 3          # fourchette « retrouvé » de R-47 (Sy bas ; Sy haut), en rapport prédite / mesurée
SEED = 20261116
NPERM_SIM = 199                   # permutations par tirage simulé (999 dans le test réel)
K_GRILLE = [3, 4, 5, 6, 8]
SIGMAS = [0.3, 0.5, 0.7]
CLASSES = ["socle", "sables", "calcaires"]


def classe_site(row) -> str:
    """Classe des sites déjà vus, déclarée APRÈS les avoir vus (GROSoM : puits de Toliara en partie karstiques).
    Sert seulement à la vraisemblance de planification, jamais au test."""
    if row["source"] == "GROSoM":
        return "calcaires"
    if row["site"] == "Sihanamaro":
        return "sables"
    return "socle"


def groupes_vus() -> pd.DataFrame:
    s = pd.read_csv(SITES)
    s["classe"] = s.apply(classe_site, axis=1)
    s["e"] = np.log10(s["mes"] / s["t2_mm"])
    return (s.groupby("groupe_validation")
             .agg(classe=("classe", "first"), e=("e", "median"), n_sites=("site", "size"))
             .reset_index())


# ---------- validation par groupe laissé de côté (vectorisée sur les jeux d'étiquettes) ----------
def logo(e: np.ndarray, lab: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Erreurs log10(prédite / mesurée) de M1 (n,) et de M2c (P, n) pour P jeux d'étiquettes lab (P, n)."""
    lab = np.atleast_2d(lab)
    n = len(e)
    idx = np.arange(n)
    err1 = np.array([np.median(e[idx != i]) for i in range(n)]) - e
    err2 = np.empty(lab.shape)
    rows = np.arange(lab.shape[0])
    for i in range(n):
        m = (lab == lab[:, [i]]) & (idx != i)
        c = m.sum(axis=1)
        s = np.sort(np.where(m, e, np.inf), axis=1)            # médiane masquée : valeurs hors masque en fin
        lo, hi = np.maximum(c - 1, 0) // 2, np.maximum(c, 1) // 2
        f2 = (s[rows, lo] + s[rows, hi]) / 2
        f2 = np.where(c >= 2, f2, err1[i] + e[i])
        err2[:, i] = f2 - e[i]
    return err1, err2


def test_permutation(e, cl, rng, nperm) -> tuple[float, float]:
    """H-A1 : gain G (classes vraies) et p de permutation des classes (effectifs conservés)."""
    lab = np.vstack([cl, rng.permuted(np.tile(cl, (nperm, 1)), axis=1)])
    err1, err2 = logo(e, lab)
    g = np.abs(err1).mean() - np.abs(err2).mean(axis=1)
    return float(g[0]), float((1 + (g[1:] >= g[0] - 1e-12).sum()) / (nperm + 1))


def critere_r47(err1, err2) -> tuple[bool, float, float]:
    a1, a2 = np.abs(err1), np.abs(err2)
    p = wilcoxon_sup(a1 - a2)
    m1, m2 = np.median(a1), np.median(a2)
    return bool(p < ALPHA and m2 <= (1 - REDUC_MIN) * m1), p, (m2 / m1 if m1 > 0 else np.nan)


def h_a2(e, err2) -> bool:
    r = 10 ** err2                                  # prédite / mesurée
    retrouves = np.mean((r >= BAS) & (r <= HAUT))
    return bool(retrouves >= 0.5 and np.median(np.abs(err2)) <= 0.5 * np.median(np.abs(e)))


# ---------- simulation ----------
def moyennes(g: pd.DataFrame) -> dict[str, dict[str, float]]:
    vu = g.groupby("classe")["e"].median().to_dict()
    ctr = float(np.median(list(vu.values())))
    sc = {}
    for nom, f in [("vu", 1.0), ("moitié", 0.5), ("quart", 0.25), ("nul", 0.0)]:
        sc[nom] = {c: ctr + f * (vu[c] - ctr) for c in CLASSES}
    # Seuls les calcaires se distinguent (socle et sables confondus) : cas plausible.
    sc["calcaires seuls"] = {"socle": vu["socle"], "sables": vu["socle"], "calcaires": vu["calcaires"]}
    return sc


def simuler(mu: dict, k: dict, sigma: float, rng, nsim: int, hasard: bool = False) -> dict[str, float]:
    cl = np.repeat(list(k.keys()), list(k.values()))
    base = np.array([mu[c] for c in cl])
    ok = dict(HA1=0, R47=0, HA2=0)
    for _ in range(nsim):
        e = base + rng.normal(0, sigma, len(cl))
        lab = rng.permutation(cl) if hasard else cl
        _, p = test_permutation(e, lab, rng, NPERM_SIM)
        err1, err2 = logo(e, lab)
        ok["HA1"] += p < ALPHA
        ok["R47"] += critere_r47(err1, err2[0])[0]
        ok["HA2"] += h_a2(e, err2[0])
    return {c: v / nsim for c, v in ok.items()}


def pct(x: float) -> str:
    return "—" if pd.isna(x) else f"{100 * x:.0f} %"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--nsim", type=int, default=500)
    a = ap.parse_args()
    rng = np.random.default_rng(SEED)

    g = groupes_vus()
    soc = g.loc[g["classe"] == "socle", "e"].to_numpy()
    sd_socle = float(np.std(soc, ddof=1))
    par_classe = g.groupby("classe").agg(e=("e", "median"), groupes=("e", "size"), sites=("n_sites", "sum"))
    sc = moyennes(g)

    # Données déjà vues : application descriptive des critères (ne décide rien).
    ev, cv = g["e"].to_numpy(), g["classe"].to_numpy()
    err1, err2 = logo(ev, cv)
    vu_ok, vu_p, vu_rap = critere_r47(err1, err2[0])
    vu_g, vu_pp = test_permutation(ev, cv, np.random.default_rng(SEED), 999)

    plans = [(f"3 classes × {kk}", "3 classes", kk, {c: kk for c in CLASSES}) for kk in K_GRILLE]
    plans += [(f"2 classes × {kk}", "2 classes", kk, {"socle": kk, "sables": kk}) for kk in K_GRILLE]
    plans += [("socle 6, sables 4, calcaires 4", "inégal", 6, {"socle": 6, "sables": 4, "calcaires": 4}),
              ("socle 6, sables 5, calcaires 3", "inégal", 6, {"socle": 6, "sables": 5, "calcaires": 3})]
    lignes = []
    for nom, mu in sc.items():
        for sigma in SIGMAS:
            for lib, fam, kk, k in plans:
                if fam == "2 classes" and nom not in ("vu", "moitié", "nul"):
                    continue
                r = simuler(mu, k, sigma, rng, a.nsim)
                rh = (simuler(mu, k, sigma, rng, a.nsim, hasard=True)
                      if nom == "vu" and fam == "3 classes" else {})
                lignes.append(dict(scenario=nom, famille=fam, plan=lib, sigma=sigma, k_par_classe=kk,
                                   n_groupes=sum(k.values()), puissance_HA1=r["HA1"], critere_R47=r["R47"],
                                   HA2=r["HA2"], HA1_classes_au_hasard=rh.get("HA1", np.nan),
                                   R47_classes_au_hasard=rh.get("R47", np.nan)))
    t = pd.DataFrame(lignes)
    t.to_csv(OUT_CSV, index=False, float_format="%.4f")

    def tab(fam, col, scen):
        sub = t[t.famille == fam]
        ks = sorted(sub.k_par_classe.unique())
        out = ["| Scénario | σ | " + " | ".join(f"k = {k}" for k in ks) + " |", "|---|---|" + "---|" * len(ks)]
        for nom in scen:
            for sigma in SIGMAS:
                r = sub[(sub.scenario == nom) & (sub.sigma == sigma)].sort_values("k_par_classe")
                out.append(f"| {nom} | {sigma} | " + " | ".join(pct(v) for v in r[col]) + " |")
        return "\n".join(out)

    def tab_inegal():
        sub = t[t.famille == "inégal"]
        out = ["| Plan | Scénario | σ | H-A1 | critère R-47 |", "|---|---|---|---|---|"]
        for r in sub.itertuples():
            out.append(f"| {r.plan} | {r.scenario} | {r.sigma} | {pct(r.puissance_HA1)} | {pct(r.critere_R47)} |")
        return "\n".join(out)

    mu_txt = "; ".join(f"{n} : " + ", ".join(f"{c} {v:+.2f}" for c, v in m.items()) for n, m in sc.items())
    cl_txt = ", ".join(f"{c} {r.e:+.2f} ({int(r.groupes)} groupe(s), {int(r.sites)} sites)" for c, r in par_classe.iterrows())
    md = f"""# Puissance de la correction de T2 par classe d'aquifère (étape T-H2.3)

Généré par `scripts/puissance_correction_aquifere.py` ({a.nsim} tirages par case, {NPERM_SIM} permutations par
tirage, graine {SEED}), selon `validation/protocole_correction_par_aquifere.md`, **avant toute donnée du test**.
Table complète : `validation/puissance_correction_aquifere.csv`.

## 1. Vraisemblance de planification (données déjà vues, R-47)

Les 12 sites de R-47 forment 8 groupes (lien simple à 20 km). Classes déclarées après les avoir vus (GROSoM rangé en
calcaires). e = log10(mesurée / T2), médiane par groupe.

- Médiane de e par classe : {cl_txt}.
- Écart-type de e entre les 6 groupes de socle : **{sd_socle:.2f}** (log10) ; d'où la grille σ = {SIGMAS}
  (dispersion entre groupes d'une même classe, erreur de mesure comprise).
- Scénarios de moyennes de classe (log10) : {mu_txt}.

**Critères appliqués aux données vues (descriptif, ne décide rien)** : une seule référence en sables et en calcaires,
donc M2c se replie sur M1 pour ces deux groupes. Critère de R-47 : p = {vu_p:.3f}, rapport des erreurs médianes
M2c / M1 = {vu_rap:.2f}, {"passerait" if vu_ok else "échoue"}. Permutation : gain G = {vu_g:+.3f}, p = {vu_pp:.3f}.
C'est l'échec de R-47 : sans au moins 2 groupes par classe, la correction par classe n'apprend rien.

## 2. H-A1 retenu (permutation des classes), 3 classes de k groupes

{tab("3 classes", "puissance_HA1", list(sc.keys()))}

Scénario « nul » = taux de faux positifs (aucune différence entre classes).

## 3. Critère de R-47 (Wilcoxon et réduction de 30 %), mêmes cas, pour comparaison

{tab("3 classes", "critere_R47", list(sc.keys()))}

## 4. Plans inégaux (socle mieux couvert)

{tab_inegal()}

## 5. H-A1, 2 classes seulement (socle, sables), si les calcaires ne sont pas couverts

{tab("2 classes", "puissance_HA1", ["vu", "moitié", "nul"])}

## 6. Comparaison à T2 (règle de R-47, abandonnée), 3 classes

{tab("3 classes", "HA2", list(sc.keys()))}

Cette comparaison « passe » aussi dans le scénario nul quand σ est faible : il récompense le changement de niveau commun à
toutes les classes, pas la classe. Il reste descriptif.

## 7. Contrôle de la référence : classes tirées au hasard (scénario « vu », 3 classes)

H-A1 retenu :

{tab("3 classes", "HA1_classes_au_hasard", ["vu"])}

Critère de R-47 :

{tab("3 classes", "R47_classes_au_hasard", ["vu"])}

Des classes sans rapport avec la roche (mêmes effectifs) doivent échouer : ce taux mesure ce que chaque critère
accorderait à un simple ajout de paramètres.
"""
    OUT_MD.write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
