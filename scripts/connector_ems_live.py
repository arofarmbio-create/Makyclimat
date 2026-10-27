"""Cartographie de crise Copernicus EMS « quasi temps réel » (vue satellite des zones inondées actives).

Différence avec validate_fokontany.py : ce module-ci ne valide rien, il AFFICHE sur la carte les zones déjà
cartographiées par une activation Copernicus EMS en cours ou récente pour Madagascar, dès qu'une nouvelle
activation apparaît — sans attendre qu'elle soit ajoutée manuellement à la base de validation.

Découverte des activations : API officielle et publique de Copernicus EMS Rapid Mapping (pas de scraping
HTML fragile) : https://rapidmapping.emergency.copernicus.eu/backend/dashboard-api/public-activations-info/
documentée ici : https://mapping.emergency.copernicus.eu/about/how-to-harvest-cems-mapping-data/emergency-response-data/
Filtre pays fait côté client (l'API ne documente pas de paramètre pays) sur le tableau countries (liste de
chaînes à ce point de terminaison, ex. ["Madagascar"]).

« Quasi temps réel » signifie : vérifié à chaque exécution du pipeline de mise à jour (toutes les 6 h),
pas un flux continu. L'imagerie Copernicus EMS elle-même n'est généralement disponible que 1 à 3 jours
après l'événement, et ne couvre que les zones cartographiées (villes et zones accessibles).

Sortie : docs/data/<pays>/ems_live.geojson (zones inondées, WGS84, simplifiées) et
docs/data/<pays>/ems_live_meta.json (liste des activations actives/récentes, même sans géométrie
exploitable, pour que l'interface affiche au moins le fait qu'une activation est en cours).
Usage : python scripts/connector_ems_live.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

import requests

from common import country_docs_dir

API = "https://rapidmapping.emergency.copernicus.eu/backend/dashboard-api/public-activations-info/"
RECENT_DAYS = 45  # une activation plus ancienne et fermée n'est plus "quasi temps réel", elle appartient à l'historique validé
SIMPLIFY_DEG = 0.0005  # ~50 m : assez pour l'affichage, garde le fichier léger


def list_madagascar_activations(session: requests.Session) -> list[dict]:
    """Liste les activations Copernicus EMS taguées Madagascar, actives ou closes depuis moins de RECENT_DAYS jours."""
    out, url = [], API + "?limit=50"
    today = dt.datetime.now(dt.timezone.utc)
    seen_urls = set()
    while url and url not in seen_urls:
        seen_urls.add(url)
        r = session.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        for act in data.get("results", []):
            countries = act.get("countries", [])  # liste de chaînes à ce point de terminaison, ex. ["Madagascar"]
            if "Madagascar" not in countries:
                continue
            closed = act.get("closed")
            act_time = act.get("activationTime")
            try:
                age_days = (today - dt.datetime.fromisoformat(str(act_time).replace("Z", "+00:00"))).days
            except (TypeError, ValueError):
                age_days = None
            if closed and (age_days is None or age_days > RECENT_DAYS):
                continue
            out.append(act)
        url = data.get("next")
        if url and len(seen_urls) > 40:  # garde-fou : jamais plus de 40 pages (l'API ne devrait jamais en avoir tant)
            break
    return out


def features_for(code: str, tmp: Path) -> list[dict]:
    """Zones inondées d'une activation, en GeoJSON (liste de Feature). Vide si rien d'exploitable."""
    from validate_fokontany import read_layers  # import tardif : dépend de geopandas, inutile si aucune activation
    try:
        _, floods, _ = read_layers(code, tmp)
    except Exception as exc:  # noqa: BLE001
        print(f"  {code} : lecture impossible ({type(exc).__name__}: {exc})")
        return []
    if floods.empty:
        return []
    floods = floods.copy()
    floods["geometry"] = floods.geometry.buffer(0).simplify(SIMPLIFY_DEG, preserve_topology=True)
    floods = floods[~floods.geometry.is_empty]
    return json.loads(floods.to_json())["features"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    if args.country != "mdg":
        print("Cartographie EMS en direct : seul mdg est pris en charge pour le moment.")
        return
    out_dir = country_docs_dir(args.country)
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 MakyClimat (recherche doctorale)"

    try:
        acts = list_madagascar_activations(session)
    except Exception as exc:  # noqa: BLE001
        print(f"Cartographie EMS en direct : API Copernicus EMS indisponible ({type(exc).__name__}) — étape ignorée.")
        sys.exit(0)

    meta = {"checked_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "events": []}
    all_features = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for act in acts:
            code = act.get("code") or ""
            if not code:
                continue
            feats = features_for(code, tmp)
            for f in feats:
                f["properties"] = {
                    "event_code": code, "event_title": act.get("name", ""),
                    "activation_time": act.get("activationTime"), "closed": bool(act.get("closed")),
                }
            all_features.extend(feats)
            meta["events"].append({
                "code": code, "title": act.get("name", ""),
                "activation_time": act.get("activationTime"),
                "closed": bool(act.get("closed")), "n_zones_inondees": len(feats),
                "lien": f"https://rapidmapping.emergency.copernicus.eu/{code}/",
            })
            print(f"  {code} ({act.get('name', '')}) : {len(feats)} zones inondées exploitables")

    (out_dir / "ems_live_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    fc = {"type": "FeatureCollection", "features": all_features}
    (out_dir / "ems_live.geojson").write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    print(f"Cartographie EMS en direct : {len(acts)} activation(s) Madagascar récente(s)/active(s), "
          f"{len(all_features)} zone(s) inondée(s) exploitable(s) au total.")


if __name__ == "__main__":
    main()
