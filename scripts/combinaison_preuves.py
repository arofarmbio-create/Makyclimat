"""Combinaison des preuves sur la recharge du Grand Sud (validation/protocole_combinaison_preuves.md, fixé avant le calcul
le 09/11/2026). Synthèse rétrospective : toutes les lignes ont déjà été vues.

Q1 : T2 surestime-t-elle ? Q2 : T2L est-elle plus juste que T2 ? Lignes : L1 fluctuation de nappe (groupes de sites),
L2 puits à sec (blocs), L3 bilan de chlorure par blocs (trois scénarios de dépôt). Score z unilatéral par ligne
(Wilcoxon des rangs signés, ou différence d'AUC / erreur type), Z de Stouffer pondéré par √n.
Sortie : validation/combinaison_preuves.md. Usage : python scripts/combinaison_preuves.py
"""
from __future__ import annotations

import datetime as dt
import json
import re

import numpy as np
import pandas as pd
from scipy import stats

from common import ROOT

SCENARIOS = ("bas", "central", "haut")


def z_wilcoxon(d) -> tuple[float, int]:
    """z unilatéral (H1 : médiane de d > 0) du test des rangs signés ; renvoie (z, n)."""
    d = np.asarray(d, float)
    d = d[np.isfinite(d) & (d != 0)]
    if len(d) < 3:
        return float("nan"), len(d)
    p = stats.wilcoxon(d, alternative="greater", method="exact" if len(d) <= 25 else "approx").pvalue
    return float(stats.norm.ppf(1 - min(max(p, 1e-12), 1 - 1e-12))), len(d)


def stouffer(lignes: list[tuple[float, int]]) -> float:
    zs = [(z, n) for z, n in lignes if np.isfinite(z) and n > 0]
    if not zs:
        return float("nan")
    w = np.sqrt([n for _, n in zs])
    return float(np.sum(w * np.array([z for z, _ in zs])) / np.sqrt(np.sum(w ** 2)))


def verdict(Z: float, lignes: list[tuple[float, int]]) -> str:
    if not np.isfinite(Z):
        return "non calculable"
    contra = any(np.isfinite(z) and z <= -1.96 for z, _ in lignes)
    if Z >= 1.96 and not contra:
        return "établi"
    if Z >= 1.0 and not contra:
        return "indice"
    return "non établi" + (" (contradiction forte d'une ligne)" if contra else "")


KWALE_HUMIDE, INTERIEUR_TOTAL = 3334.0, 260.0      # mesures de référence (protocole, section 7)


def facteur_validation() -> float | None:
    """Facteur de correction de MERRA-2 (moyenne géométrique des rapports mesuré / MERRA-2), ou None s'il est crédible
    (à moins d'un facteur 2 des deux références) ou non validé."""
    p = ROOT / "data" / "mdg" / "depot_chlorure_merra2_validation.csv"
    if not p.exists():
        return None
    v = pd.read_csv(p)
    k = float(v[v.site.str.startswith("Kwale")].chlorure_humide_mg_m2_an.iloc[0])
    sa = float(v[v.site.str.contains("Afrique du Sud")].chlorure_total_mg_m2_an.median())
    r1, r2 = KWALE_HUMIDE / k, INTERIEUR_TOTAL / sa
    if 0.5 <= r1 <= 2 and 0.5 <= r2 <= 2:
        return 1.0
    return float(np.sqrt(r1 * r2))


def scenario_merra2(facteur: float = 1.0) -> str | None:
    """Scénario le plus proche du dépôt MERRA-2 (× facteur) sur les mailles terrestres (médiane de la classe de distance à
    la côte qui contient la distance médiane des blocs), si la synthèse MERRA-2 existe ; sinon None."""
    p = ROOT / "data" / "mdg" / "depot_chlorure.json"
    if not p.exists():
        return None
    cl = (json.loads(p.read_text(encoding="utf-8")).get("merra2") or {}).get("par_classe_distance_chlorure_mg_m2_an")
    if not cl:
        return None
    import recharge_chlorure as RC
    d_med = float(pd.read_csv(ROOT / "validation" / "recharge_chlorure_blocs_zones.csv").dist_km.median())
    classe = "moins de 30 km" if d_med < 30 else ("30 à 100 km" if d_med <= 100 else "plus de 100 km")
    cible = float(cl[classe]["mediane"]) * facteur
    ecarts = {s: abs(np.log10(RC.depot([500.0], [d_med], RC.SCENARIOS[s])[0] / cible)) for s in SCENARIOS}
    return min(ecarts, key=ecarts.get)


def main() -> None:
    s = pd.read_csv(ROOT / "validation" / "recharge_locale_sites.csv")
    soc = s.assign(q1=np.log10(s.t2_mm / s.mes),
                   q2=np.abs(np.log10(s.M0_groupes / s.mes)) - np.abs(np.log10(s.M2_groupes / s.mes)))
    g = soc.groupby("groupe_validation")[["q1", "q2"]].median()
    L1_q1, L1_q2 = z_wilcoxon(g.q1), z_wilcoxon(g.q2)

    txt = (ROOT / "validation" / "puits_a_sec.md").read_text(encoding="utf-8")
    m = re.search(r"\| T2L − T2 \| ([+-][\d.]+) \| ([+-]?[\d.]+) à ([+-][\d.]+) \|", txt)
    d, lo, hi = float(m.group(1)), float(m.group(2)), float(m.group(3))
    n_blocs = int(re.search(r"\((\d+) blocs de 20 km\)", txt).group(1))
    L2_q2 = (d / ((hi - lo) / 3.92), n_blocs)

    z = pd.read_csv(ROOT / "validation" / "recharge_chlorure_blocs_zones.csv")
    dom = z[z.dom == "dans le domaine"]
    L3 = {sc: (z_wilcoxon(np.log10(z.T2 / z[f"R_{sc}"])),
               z_wilcoxon(np.abs(np.log10(dom.T2 / dom[f"R_{sc}"])) - np.abs(np.log10(dom.T2L / dom[f"R_{sc}"]))))
          for sc in SCENARIOS}
    f_val = facteur_validation()
    sc_brut = scenario_merra2()
    sc_m = scenario_merra2(f_val) if f_val else sc_brut

    def fz(t):
        return "—" if not np.isfinite(t[0]) else f"{t[0]:+.2f} (n = {t[1]})"
    L = ["# Combinaison des preuves sur la recharge du Grand Sud", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/combinaison_preuves.py`, selon "
         "`validation/protocole_combinaison_preuves.md` (fixé avant le calcul). **Synthèse rétrospective** : toutes les lignes avaient "
         "déjà été vues ; elle résume, elle ne prouve pas à nouveau.", "",
         f"Scénario de dépôt de chlorure retenu : **{sc_m or 'aucun (MERRA-2 pas encore disponible)'}**"
         + (f" (MERRA-2 corrigé par le facteur {f_val:.2f} tiré de sa validation à Kwale et en Afrique du Sud ; MERRA-2 brut : {sc_brut})"
            if f_val and f_val != 1.0 else "") + ".", "",
         "## Scores par ligne (z unilatéral ; positif = dans le sens de la question)", "",
         "| Ligne | Q1 : T2 surestime | Q2 : T2L plus juste que T2 |", "|---|---|---|",
         f"| L1 fluctuation de nappe (groupes de sites) | {fz(L1_q1)} | {fz(L1_q2)} |",
         f"| L2 puits à sec (blocs) | sans objet | {fz(L2_q2)} |"]
    for sc in SCENARIOS:
        L.append(f"| L3 chlorure, scénario {sc} (blocs, après coup) | {fz(L3[sc][0])} | {fz(L3[sc][1])} |")
    L += ["", "## Combinaison (Z de Stouffer pondéré par √n)", "",
          "| Scénario de dépôt | Q1 : Z | Q1 : verdict | Q2 : Z | Q2 : verdict |", "|---|---|---|---|---|"]
    res = {}
    for sc in SCENARIOS:
        q1 = [L1_q1, L3[sc][0]]
        q2 = [L1_q2, L2_q2, L3[sc][1]]
        Z1, Z2 = stouffer(q1), stouffer(q2)
        res[sc] = (Z1, verdict(Z1, q1), Z2, verdict(Z2, q2))
        mark = " (retenu)" if sc == sc_m else ""
        L.append(f"| {sc}{mark} | {Z1:+.2f} | {res[sc][1]} | {Z2:+.2f} | {res[sc][3]} |")
    Z1s, Z2s = stouffer([L1_q1]), stouffer([L1_q2, L2_q2])
    L.append(f"| sans le chlorure | {Z1s:+.2f} | {verdict(Z1s, [L1_q1])} | {Z2s:+.2f} | {verdict(Z2s, [L1_q2, L2_q2])} |")
    L += ["", "Règle (fixée avant le calcul) : « établi » si Z ≥ 1,96 dans le scénario retenu et aucune ligne à z ≤ −1,96 ; « indice » si "
          "1,0 ≤ Z < 1,96 ; « non établi » sinon. Sans scénario retenu, aucun verdict global n'est prononcé.", "",
          "Dépendances : L2 et L3 couvrent la même région et les mêmes forages BushProof ; L3 est fragilisée par le chlorure venu des "
          "roches (Cl/Na médian 0,96), ce qui abaisse la recharge par chlorure et favorise Q1. L1 n'est pas indépendante de la "
          "construction de T2L (ses sites ont servi à T2L ; chacun est évalué en laissant son groupe de côté).", ""]
    (ROOT / "validation" / "combinaison_preuves.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(json.dumps({"retenu": sc_m, "L1": [L1_q1, L1_q2], "L2": L2_q2, **{k: v for k, v in res.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
