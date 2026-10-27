"""Connecteur qualité de l'eau souterraine (conductivité électrique) : mesures réelles MGMERL.

Même source et même méthode que `connector_watertable.py` (voir son docstring pour le détail complet :
extraction manuelle faute d'API MGMERL accessible, échantillon des relevés les plus récents, assignation
par plus proche voisin avec un rayon maximal, aucune valeur inventée au-delà). Ce connecteur traite un
indicateur différent : la **conductivité électrique** (µS/cm), un indicateur indirect de salinité/minéralisation
de l'eau — répond directement au point 3 de "Pour l'améliorer encore" dans validation/groundwater_limites.md
(absence de couche qualité/salinité, notamment pour les zones côtières à risque d'intrusion saline).

Important — ce que ce n'est PAS : la conductivité seule ne donne pas une classification potable/non potable
(cela dépend aussi de la composition ionique, pas seulement de la conductivité globale, et des normes
retenues). MakyClimat n'étiquette donc PAS les valeurs "bonnes" ou "mauvaises" : il publie la mesure brute,
avec sa source et sa date, et laisse l'utilisateur l'interpréter. Pour cette raison, cet indicateur n'entre
PAS dans le score composite `potentiel_eau_pct` (voir build_groundwater.py) : une conductivité élevée est un
signal de risque qui peut coexister avec un site par ailleurs favorable (nappe peu profonde, bonne géologie)
— le mélanger dans une note positive unique masquerait ce risque plutôt que de le signaler. Conformément au
principe du projet (exposition ≠ dommage ≠ besoin), ce signal de risque reste un indicateur séparé, affiché
à côté du score, jamais fondu dedans.

Fichier source : inputs/mgmerl/mgmerl_conductivite.csv (extrait le 27/10/2026, même lot que le niveau
statique). Les valeurs sont formatées avec virgule comme séparateur de milliers (ex. "3,999") ; nettoyées
avant conversion en nombre.
Sortie : data/<pays>/external/water_quality.csv (pcode, indicateur=conductivity_uscm, valeur en µS/cm, date, source)
Usage : python scripts/connector_mgmerl_quality.py --country mdg
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from common import ROOT, country_data_dir, read_units
from connector_watertable import WATERTABLE_MAX_DIST_KM, assign_nearest

MGMERL_CONDUCTIVITE_CSV = ROOT / "inputs" / "mgmerl" / "mgmerl_conductivite.csv"
MGMERL_EXTRACTION_DATE = "2026-10-27"
SOURCE = (f"MGMERL (mgmerl.org, plateforme publique de suivi des ressources en eau de Madagascar, mWater) — "
          f"conductivité électrique mesurée sur forages/puits, extraite manuellement le {MGMERL_EXTRACTION_DATE} "
          f"(export programmatique indisponible pour un compte non membre) ; assignée par plus proche voisin, "
          f"{WATERTABLE_MAX_DIST_KM:.0f} km max ; indicateur indirect de salinité, PAS une classification "
          f"potable/non potable — voir validation/groundwater_limites.md")


def load_conductivity(path: Path = MGMERL_CONDUCTIVITE_CSV) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"Conductivité électrique (uS/cm)": str})
    coords = df["Coordonnées GPS"].str.split(",", expand=True).astype(float)
    df["lat"], df["lon"] = coords[0], coords[1]
    df["valeur"] = pd.to_numeric(
        df["Conductivité électrique (uS/cm)"].str.replace(",", "", regex=False), errors="coerce")
    df = df.dropna(subset=["lat", "lon", "valeur"])
    df = df.drop_duplicates("ID unique", keep="last")
    return df.reset_index(drop=True)


def compute(leaves: pd.DataFrame, path: Path = MGMERL_CONDUCTIVITE_CSV) -> pd.DataFrame:
    points = load_conductivity(path)
    out = assign_nearest(points, leaves)
    out["indicateur"] = "conductivity_uscm"
    out["valeur"] = out["valeur"].round(0)
    out["source"] = SOURCE
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    units = read_units(args.country)
    leaves = units[units.level == units.level.max()]
    out = compute(leaves)
    ext = country_data_dir(args.country) / "external"
    ext.mkdir(parents=True, exist_ok=True)
    out.to_csv(ext / "water_quality.csv", index=False)
    if len(out):
        print(f"Conductivité électrique (MGMERL, mesures réelles) : {len(out)}/{len(leaves)} fokontany "
              f"({100*len(out)/len(leaves):.0f} %), médiane {out.valeur.median():.0f} µS/cm, "
              f"dans un rayon de {WATERTABLE_MAX_DIST_KM:.0f} km d'un forage mesuré.")
    else:
        print("Conductivité électrique : aucune valeur exploitable (fichier MGMERL vide ou illisible).")


if __name__ == "__main__":
    main()
