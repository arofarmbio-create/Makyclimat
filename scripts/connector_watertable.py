"""Connecteur profondeur de la nappe (niveau statique) : mesures réelles de forages malgaches (MGMERL).

Historique : ce connecteur visait initialement la carte continentale de MacDonald et al. (2012)/BGS
("Quantitative maps of groundwater resources in Africa"), republiée par l'UNESCO-IHP. Son service WCS
répond 404 depuis le 27/10/2026, mais surtout le fichier source obtenu directement auprès du BGS a été
inspecté point par point : **son emprise s'arrête à 40,8°E et ne couvre PAS Madagascar** (l'île, à
43°E-51°E, n'a jamais été incluse dans cette étude continentale). Cette source a donc été abandonnée
définitivement pour Madagascar — voir l'historique git de ce fichier pour le détail de cette vérification.

Source actuelle : **MGMERL** (mgmerl.org), plateforme publique de suivi des ressources en eau de
Madagascar (mWater), initiée avec l'appui de l'UNICEF. Données réelles de terrain : niveau statique
d'eau mesuré sur des forages/puits malgaches, avec coordonnées GPS et date du relevé — PAS une grille
interpolée ni une modélisation.

Méthode d'obtention — **IMPORTANT, à relire avant de "corriger" ce connecteur** : MGMERL n'expose aucune
API publique ni export CSV accessible sans être membre de l'organisation mWater propriétaire du projet
(le bouton "Export Data" du tableau de bord renvoie "client not found" pour tout compte non membre,
y compris un compte mWater fraîchement créé — vérifié le 27/10/2026). Les données ont donc été extraites
manuellement : lecture des tableaux déjà rendus dans le DOM du tableau de bord public (accessible sans
connexion), export en CSV côté navigateur, puis copiées ici. Le tableau de bord limite l'affichage aux
~1000 relevés les plus récents (sur 25 271 forages enregistrés au total dans MGMERL au 27/10/2026) : ce
n'est donc PAS un échantillon aléatoire ni exhaustif, mais les relevés les plus récents disponibles.
**Rafraîchissement** : pas automatisé (pas d'accès programmatique) ; à refaire manuellement
périodiquement en répétant cette extraction et en remplaçant inputs/mgmerl/mgmerl_niveau_statique.csv.
Fichier source : inputs/mgmerl/mgmerl_niveau_statique.csv (extrait le 27/10/2026).

Méthode d'assignation : plus proche voisin. Pour chaque fokontany, on cherche le point de mesure MGMERL
le plus proche ; au-delà de WATERTABLE_MAX_DIST_KM (15 km), on ne produit PAS de valeur plutôt que
d'inventer une mesure à une distance déraisonnable. Si plusieurs relevés existent pour le même point
(même "ID unique"), seul le plus récent est conservé.

Limites essentielles :
  - Couverture partielle et non uniforme : seuls les fokontany à moins de 15 km d'un forage mesuré
    reçoivent une valeur (environ 29 % du pays au moment de l'extraction — densité réelle du réseau
    MGMERL, pas un artefact du seuil).
  - Biais de sélection : MGMERL échantillonne les forages SUIVIS (souvent desservis par un partenaire
    WASH), pas un maillage systématique du territoire.
  - "Niveau statique" ponctuel, pas une moyenne saisonnière : varie avec la saison et l'année du relevé
    (relevés mélangés 2023-2026 dans l'extrait actuel).
Voir validation/groundwater_limites.md pour le détail et les pistes d'amélioration.
Sortie : data/<pays>/external/watertable.csv (pcode, indicateur=water_table_depth_m, valeur en mètres, date, source)
Usage : python scripts/connector_watertable.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

from common import ROOT, country_data_dir, read_units

MGMERL_CSV = ROOT / "inputs" / "mgmerl" / "mgmerl_niveau_statique.csv"
MGMERL_EXTRACTION_DATE = "2026-10-27"
WATERTABLE_MAX_DIST_KM = 15.0
KM_PER_DEG_LAT = 111.0
SOURCE = (f"MGMERL (mgmerl.org, plateforme publique de suivi des ressources en eau de Madagascar, mWater) — "
          f"relevés réels de niveau statique d'eau sur forages/puits, extraits manuellement le {MGMERL_EXTRACTION_DATE} "
          f"(export programmatique indisponible pour un compte non membre) ; assignés par plus proche voisin, "
          f"{WATERTABLE_MAX_DIST_KM:.0f} km max — voir validation/groundwater_limites.md")


def load_mgmerl(path: Path = MGMERL_CSV) -> pd.DataFrame:
    df = pd.read_csv(path)
    coords = df["Coordonnées GPS"].str.split(",", expand=True).astype(float)
    df["lat"], df["lon"] = coords[0], coords[1]
    df["valeur"] = pd.to_numeric(df["Niveau statique d'eau"], errors="coerce")
    df["date_releve"] = pd.to_datetime(df["Date du rapport"], errors="coerce")
    df = df.dropna(subset=["lat", "lon", "valeur"])
    # un même forage peut être relevé plusieurs fois (même "ID unique") : ne garder que le plus récent
    df = df.sort_values("date_releve").drop_duplicates("ID unique", keep="last")
    return df.reset_index(drop=True)


def assign_nearest(points: pd.DataFrame, leaves: pd.DataFrame, max_dist_km: float = WATERTABLE_MAX_DIST_KM) -> pd.DataFrame:
    """Assigne à chaque fokontany la valeur du point MGMERL le plus proche, dans la limite de max_dist_km.
    Distance approximée en degrés->km (correction cos(latitude) pour la longitude) : suffisant à l'échelle
    du seuil utilisé (quelques dizaines de km), pas une projection géodésique précise."""
    from scipy.spatial import cKDTree
    lat0 = np.radians(leaves.lat.to_numpy().mean())
    lon_scale = np.cos(lat0)  # corrige l'aplatissement des degrés de longitude à cette latitude
    pts_xy = np.column_stack([points.lon.to_numpy() * lon_scale, points.lat.to_numpy()])
    leaves_xy = np.column_stack([leaves.lon.to_numpy() * lon_scale, leaves.lat.to_numpy()])
    tree = cKDTree(pts_xy)
    dist_deg, idx = tree.query(leaves_xy)
    dist_km = dist_deg * KM_PER_DEG_LAT
    within = dist_km <= max_dist_km
    date = dt.date.today().isoformat()
    out = pd.DataFrame({
        "pcode": leaves.pcode.to_numpy()[within],
        "indicateur": "water_table_depth_m",
        "valeur": np.round(points.valeur.to_numpy()[idx[within]], 2),
        "date": date,
    })
    out["source"] = SOURCE
    return out


def compute(leaves: pd.DataFrame, mgmerl_path: Path = MGMERL_CSV) -> pd.DataFrame:
    points = load_mgmerl(mgmerl_path)
    return assign_nearest(points, leaves)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    units = read_units(args.country)
    leaves = units[units.level == units.level.max()]
    out = compute(leaves)
    ext = country_data_dir(args.country) / "external"
    ext.mkdir(parents=True, exist_ok=True)
    out.to_csv(ext / "watertable.csv", index=False)
    if len(out):
        print(f"Profondeur de nappe (MGMERL, mesures réelles) : {len(out)}/{len(leaves)} fokontany "
              f"({100*len(out)/len(leaves):.0f} %), médiane {out.valeur.median():.1f} m, "
              f"dans un rayon de {WATERTABLE_MAX_DIST_KM:.0f} km d'un forage mesuré.")
    else:
        print("Profondeur de nappe : aucune valeur exploitable (fichier MGMERL vide ou illisible).")


if __name__ == "__main__":
    main()
