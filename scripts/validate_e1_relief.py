"""E1, hypothèse descriptive H3-E1 (validation/protocole_e1_fusion_pluie.md, section 6.2 et seuils du 03/11/2026) :
l'erreur de chaque source de pluie dépend-elle du relief ?

Lit la triple collocation (e1_tc.npz, release « e1-pluie », workflow 25) et le relief GLO-90 sur la même grille de
0,1° (data/<pays>/e1/relief_01deg.npz). Classes : Hautes Terres (altitude ≥ 1 000 m), tiers de rugosité, exposition
aux alizés (au vent, sous le vent, sans grand versant), côte (moins de 20 km de la mer). Mesure principale : r de la
triple collocation ; secondaire : variance d'erreur.
Sortie : validation/e1_relief.md et e1_relief.csv.
Usage : python scripts/validate_e1_relief.py --country mdg [--tc CHEMIN/e1_tc.npz]
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import ndimage, stats

from common import ROOT, country_data_dir

HIGHLANDS_M, EXPO_MKM, COAST_KM, CELL_KM = 1000.0, 2.0, 20.0, 11.1


def classes(alt, rug, expo, land) -> dict:
    """Une étiquette de classe par maille terrestre, pour chaque découpage."""
    t1, t2 = np.nanpercentile(rug[land], [100 / 3, 200 / 3])
    dist = ndimage.distance_transform_edt(land) * CELL_KM      # distance (km) à la maille de mer la plus proche
    lab = lambda cond_list, names: np.select(cond_list, names, default="")
    return {
        "altitude": lab([alt >= HIGHLANDS_M, alt < HIGHLANDS_M], ["Hautes Terres (≥ 1 000 m)", "moins de 1 000 m"]),
        "rugosité": lab([rug < t1, rug < t2, rug >= t2], ["plat", "moyen", "accidenté"]),
        "exposition": lab([expo > EXPO_MKM, expo < -EXPO_MKM, np.isfinite(expo)], ["au vent (est)", "sous le vent (ouest)", "sans grand versant"]),
        "côte": lab([dist <= COAST_KM, dist > COAST_KM], ["côte (moins de 20 km)", "intérieur"]),
    }


def zone_table(r2, ev, sources, cls: dict, land) -> pd.DataFrame:
    rows = []
    for split, lab in cls.items():
        for name in [x for x in dict.fromkeys(lab[land]) if x]:
            m = land & (lab == name)
            row = {"decoupage": split, "classe": name, "mailles": int(m.sum())}
            for i, s in enumerate(sources):
                row[f"r_{s}"] = float(np.nanmedian(np.sqrt(np.clip(r2[i][m], 0, 1))))
                row[f"var_{s}"] = float(np.nanmedian(ev[i][m]))
            rows.append(row)
    return pd.DataFrame(rows)


def rank_corr(r2, rug, sources, land) -> dict:
    out = {}
    for i, s in enumerate(sources):
        r = np.sqrt(np.clip(r2[i], 0, 1))
        ok = land & np.isfinite(r) & np.isfinite(rug)
        out[s] = float(stats.spearmanr(r[ok], rug[ok])[0])
    return out


def report(tab: pd.DataFrame, rho: dict, sources) -> str:
    L = ["# E1, H3-E1 : l'erreur des sources de pluie selon le relief", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/validate_e1_relief.py`, selon "
         "`validation/protocole_e1_fusion_pluie.md` (section 6.2, seuils fixés le 03/11/2026 avant ce calcul). Triple "
         "collocation sur l'apprentissage 2001-2015, pentades de novembre à avril ; relief Copernicus GLO-90. Analyse descriptive.", "",
         "r : corrélation médiane avec la pluie vraie (1 = parfaite). Variance d'erreur médiane en mm² par pentade "
         "(croît avec la quantité de pluie).", ""]
    head = "| Découpage | Classe | Mailles | " + " | ".join(f"r {s}" for s in sources) + " | " + " | ".join(f"variance {s}" for s in sources) + " |"
    L += [head, "|" + "---|" * (3 + 2 * len(sources))]
    for r in tab.itertuples(index=False):
        d = r._asdict()
        L.append(f"| {d['decoupage']} | {d['classe']} | {d['mailles']} | " + " | ".join(f"{d[f'r_{s}']:.2f}" for s in sources)
                 + " | " + " | ".join(f"{d[f'var_{s}']:.0f}" for s in sources) + " |")
    L += ["", "Corrélation de Spearman, sur les mailles, entre r et la rugosité (négative : la source se dégrade en relief "
          "accidenté) : " + " ; ".join(f"{s} {v:+.2f}" for s, v in rho.items()) + ".", ""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--tc", default=None)
    args = ap.parse_args()
    e1 = country_data_dir(args.country) / "e1"
    tc = np.load(Path(args.tc) if args.tc else e1 / "e1_tc.npz", allow_pickle=True)
    rel = np.load(e1 / "relief_01deg.npz")
    if not (np.allclose(tc["lat"], rel["lat"]) and np.allclose(tc["lon"], rel["lon"])):
        raise SystemExit("grilles différentes entre la triple collocation et le relief")
    sources = [str(s) for s in tc["sources"]]
    ev, r2 = tc["variance_erreur"].astype(float), tc["r2"].astype(float)
    land = np.isfinite(ev).any(axis=0)
    alt, rug, expo = (rel[k].astype(float) for k in ("altitude_m", "rugosite_m", "exposition_est"))
    tab = zone_table(r2, ev, sources, classes(alt, rug, expo, land), land)
    rho = rank_corr(r2, rug, sources, land)
    vd = ROOT / "validation"
    (vd / "e1_relief.md").write_text(report(tab, rho, sources), encoding="utf-8")
    tab.round(3).to_csv(vd / "e1_relief.csv", index=False)
    print("H3-E1 : rapport écrit dans validation/e1_relief.md")


if __name__ == "__main__":
    main()
