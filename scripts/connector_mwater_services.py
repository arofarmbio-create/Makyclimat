"""Connecteur mWater Portal : formations sanitaires et écoles recensées par fokontany — comptage réel,
pas une estimation.

Contexte : le module eau souterraine utilise déjà MGMERL (mgmerl.org), qui est un tableau de bord public
construit sur la plateforme mWater (mwater.co). MGMERL lui-même n'expose pas de module établissements
(écoles, CSB), mais **ces données existent en accès public directement sur le portail mWater**
(portal.mwater.co/#/entity_views), car mWater est un entrepôt de données communautaire plus large que le
seul projet MGMERL : de nombreuses organisations (dont les partenaires WASH/santé/éducation de Madagascar)
y publient leurs propres relevés de sites.

Ce connecteur traite deux types de sites (Site/Asset Type dans mWater) :
  - "Health facility" -> mwater_sante  (CSB/CHRD/CHU et assimilés)
  - "School"           -> mwater_ecoles (EPP, écoles privées, etc.)

Contrairement aux formations OSM (connector_osm_services.py, qui reste un comptage minimal de ce qui a
été cartographié par des bénévoles), mWater est alimenté par des organisations de terrain (ONG WASH,
ministères, MGMERL/UNICEF) qui relèvent les établissements avec GPS dans le cadre de leur travail — la
couverture est donc nettement plus complète (3 837 formations sanitaires et 27 981 écoles avec
coordonnées GPS au 27/10/2026, contre des sous-ensembles bien plus restreints sur OSM).

Important — ce que ce n'est PAS : ce ne sont toujours pas des registres officiels exhaustifs (Ministère de
la Santé Publique pour les CSB — environ 3 000-3 300 officiellement recensés selon les sources ; Ministère
de l'Éducation pour les écoles). Les deux comptages mWater peuvent inclure des doublons, des
établissements fermés non retirés, ou des catégories plus larges que le seul secteur public (écoles/
dispensaires privés ou confessionnels, etc.). C'est la source la plus complète et la plus récente qu'on
ait trouvée à ce jour, pas un recensement officiel validé.

Méthode d'obtention — **IMPORTANT, à relire avant de "corriger" ce connecteur** : le portail mWater
(portal.mwater.co) permet, une fois connecté avec un compte mWater (gratuit), de filtrer les sites publics
par pays et par type puis de les exporter en CSV directement depuis l'interface ("Export... > All
Columns") — contrairement à MGMERL, cet export fonctionne sans statut de membre d'une organisation
particulière. Il n'existe pas d'API publique automatisable identifiée à ce jour pour ce même filtre ;
l'extraction a donc été faite manuellement via le navigateur le 27/10/2026.
**Rafraîchissement** : pas automatisé ; à refaire manuellement périodiquement en répétant cette extraction
et en remplaçant inputs/mwater/mwater_sante.csv / inputs/mwater/mwater_ecoles.csv.
Fichiers source :
  inputs/mwater/mwater_sante.csv  (3 837 lignes, 100 % avec coordonnées GPS, relevés majoritairement
                                    2023-2026)
  inputs/mwater/mwater_ecoles.csv (27 981 lignes, 100 % avec coordonnées GPS)

Méthode d'assignation : **point dans polygone** (pas plus proche voisin) — chaque établissement a ses
propres coordonnées GPS précises, donc on utilise directement les limites de fokontany publiées
(common.locate_points), comme pour les services OSM. Pas de rayon de recherche, pas de valeur
approximative : chaque établissement est compté dans le fokontany qui le contient géométriquement.

Indicateurs produits (nombre, par fokontany ; communes/districts/régions en font la somme) :
  mwater_sante    nombre de formations sanitaires recensées sur mWater
  mwater_ecoles   nombre d'écoles recensées sur mWater

Sortie : data/<pays>/external/mwater_services.csv (pcode, indicateur, valeur, date, source)
Usage : python scripts/connector_mwater_services.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import pandas as pd

from common import ROOT, country_data_dir, locate_points, read_units

MWATER_SANTE_CSV = ROOT / "inputs" / "mwater" / "mwater_sante.csv"
MWATER_ECOLES_CSV = ROOT / "inputs" / "mwater" / "mwater_ecoles.csv"
EXTRACTION_DATE = "2026-10-27"


def _source(kind: str) -> str:
    return (f"mWater Portal (portal.mwater.co, entrepôt communautaire de sites WASH/santé/éducation — "
            f"alimenté par des ONG, ministères et projets dont MGMERL/UNICEF à Madagascar) — {kind} "
            f"publiques avec coordonnées GPS, extraites manuellement le {EXTRACTION_DATE} (export filtré "
            f"par pays, pas d'API publique automatisable identifiée) ; assignées par point dans polygone "
            f"(pas une approximation de distance) ; PAS un registre officiel exhaustif — voir "
            f"validation/groundwater_limites.md ou methodologie_these.md pour le détail")


def load_sites(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = df.rename(columns={"GPS Location (latitude)": "lat", "GPS Location (longitude)": "lon"})
    df = df.dropna(subset=["lat", "lon"])
    return df.reset_index(drop=True)


# alias conservé pour compatibilité (tests, usages existants)
load_sante = load_sites


def _compute_one(leaves: pd.DataFrame, slug: str, path: Path, indicateur: str, source_kind: str) -> pd.DataFrame:
    pts = load_sites(path)
    pts["pcode"] = locate_points(slug, pts["lon"].tolist(), pts["lat"].tolist())
    pts = pts[pts["pcode"] != ""]
    counts = pts.groupby("pcode").size().rename("valeur").reset_index()
    out = leaves[["pcode"]].merge(counts, on="pcode", how="left")
    out["valeur"] = out["valeur"].fillna(0).astype(int)
    out = out[out["valeur"] > 0].copy()  # comme osm_services : zéro = rien à afficher, pas une valeur
    out["indicateur"] = indicateur
    out["date"] = dt.date.today().isoformat()
    out["source"] = _source(source_kind)
    return out[["pcode", "indicateur", "valeur", "date", "source"]]


def compute(leaves: pd.DataFrame, slug: str, path: Path = MWATER_SANTE_CSV) -> pd.DataFrame:
    """Rétro-compatible : calcule uniquement l'indicateur formations sanitaires (mwater_sante)."""
    return _compute_one(leaves, slug, path, "mwater_sante", "formations sanitaires")


def compute_ecoles(leaves: pd.DataFrame, slug: str, path: Path = MWATER_ECOLES_CSV) -> pd.DataFrame:
    return _compute_one(leaves, slug, path, "mwater_ecoles", "écoles")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    units = read_units(args.country)
    leaves = units[units.level == units.level.max()]

    out_sante = compute(leaves, args.country)
    pts_sante = load_sites(MWATER_SANTE_CSV)
    print(f"mWater — formations sanitaires : {len(pts_sante)} établissements avec GPS, "
          f"{len(out_sante)}/{len(leaves)} fokontany ({100*len(out_sante)/len(leaves):.0f} %) avec au "
          f"moins une formation sanitaire.")

    frames = [out_sante]
    if MWATER_ECOLES_CSV.exists():
        out_ecoles = compute_ecoles(leaves, args.country)
        pts_ecoles = load_sites(MWATER_ECOLES_CSV)
        print(f"mWater — écoles : {len(pts_ecoles)} établissements avec GPS, "
              f"{len(out_ecoles)}/{len(leaves)} fokontany ({100*len(out_ecoles)/len(leaves):.0f} %) avec "
              f"au moins une école.")
        frames.append(out_ecoles)
    else:
        print("mWater — écoles : fichier inputs/mwater/mwater_ecoles.csv absent, indicateur ignoré.")

    out = pd.concat(frames, ignore_index=True)
    ext = country_data_dir(args.country) / "external"
    ext.mkdir(parents=True, exist_ok=True)
    out.to_csv(ext / "mwater_services.csv", index=False)


if __name__ == "__main__":
    main()
