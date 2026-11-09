"""Atlas des nappes avec la fourchette de recharge T2 / T2c (décision fixée avant le calcul dans
validation/protocole_controle_recharge.md, section 5 : H-R2 non soutenue, donc T2 reste la valeur centrale et les
unités dont la classe de bilan change entre T2 et T2c sont marquées « incertaines »).

Entrées : data/<pays>/external/nappes_{bassins,sousbassins}.csv (T2) et nappes_{...}_t2c.csv
(atlas_bassins.py --recharge t2c). Sorties : validation/atlas_fourchette_recharge.md,
data/<pays>/external/nappes_{bassins,sousbassins}_fourchette.csv.
Usage : python scripts/atlas_fourchette_recharge.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt

import pandas as pd

from common import ROOT, country_data_dir

ORDER = ["faible", "modéré", "élevé"]


def compare(t2: pd.DataFrame, t2c: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par unité : bilan et classe sous T2 et T2c, statut « stable » ou « incertain »."""
    m = t2[["bassin", "nom", "population", "fiabilite", "recharge_mm", "bilan", "classe_bilan"]].merge(
        t2c[["bassin", "recharge_mm", "bilan", "classe_bilan"]], on="bassin", suffixes=("", "_t2c"))
    m["statut"] = (m.classe_bilan == m.classe_bilan_t2c).map({True: "stable", False: "incertain"})
    return m


def cross(m: pd.DataFrame) -> pd.DataFrame:
    return pd.crosstab(m.classe_bilan, m.classe_bilan_t2c).reindex(index=ORDER, columns=ORDER, fill_value=0)


def section(title: str, m: pd.DataFrame, top: int) -> list[str]:
    c = cross(m)
    L = [f"## {title}", "", f"{len(m)} unités ; **{int((m.statut == 'incertain').sum())} incertaines** (classe différente "
         "selon la recharge).", "", "| Classe avec T2 \\ avec T2c | " + " | ".join(ORDER) + " |", "|---|---|---|---|"]
    for k in ORDER:
        L.append(f"| {k} | " + " | ".join(str(int(c.loc[k, j])) for j in ORDER) + " |")
    hi = m[(m.classe_bilan == "élevé") | (m.classe_bilan_t2c == "élevé")].sort_values("bilan", ascending=False)
    if len(hi):
        L += ["", "Unités en bilan élevé avec au moins une des deux recharges :", "",
              "| Unité | Population | Recharge T2 → T2c (mm/an) | Bilan T2 → T2c | Classe T2 → T2c | Statut | Fiabilité |",
              "|---|---|---|---|---|---|---|"]
        for x in hi.head(top).itertuples():
            L.append(f"| {x.nom} | {x.population:,.0f} | {x.recharge_mm:.0f} → {x.recharge_mm_t2c:.0f} | {x.bilan:.3f} → "
                     f"{x.bilan_t2c:.3f} | {x.classe_bilan} → {x.classe_bilan_t2c} | {x.statut} | {x.fiabilite} |")
    return L + [""]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    ext = country_data_dir(args.country) / "external"
    L = ["# Atlas des nappes : fourchette de recharge T2 / T2c", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/atlas_fourchette_recharge.py`. Décision fixée avant le "
         "calcul (`validation/protocole_controle_recharge.md`, section 5) : H-R2 n'étant pas soutenue, T2 reste la valeur "
         "centrale ; une unité est **incertaine** si sa classe de bilan prélèvements / recharge change avec T2c.", ""]
    for lvl, title, top in (("bassins", "Grands bassins", 20), ("sousbassins", "Sous-bassins", 60)):
        m = compare(pd.read_csv(ext / f"nappes_{lvl}.csv"), pd.read_csv(ext / f"nappes_{lvl}_t2c.csv"))
        m.round(4).to_csv(ext / f"nappes_{lvl}_fourchette.csv", index=False)
        L += section(title, m, top)
    L += ["Limites : T2c ne corrige pas la surestimation du Grand Sud ni le karst de Toliara "
          "(`validation/controle_recharge.md`) ; une unité « stable » peut donc rester fausse dans ces zones.", ""]
    (ROOT / "validation" / "atlas_fourchette_recharge.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("Rapport : validation/atlas_fourchette_recharge.md")


if __name__ == "__main__":
    main()
