"""Contrôle qualité AVANT publication. Si un contrôle échoue, le workflow s'arrête et les anciennes données restent en ligne.

Contrôles : fichiers présents, population totale plausible, pas trop d'unités sans donnée de pluie,
valeurs de pluie dans des bornes physiques, données pas trop anciennes ; fraîcheur,
disponibilité et bornes des alertes et des couches à forte conséquence, à tous les niveaux.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys

from common import country_docs_dir, load_config


def rain_age_days(through: dt.date, today: dt.date, start_month: int) -> int:
    """Âge des données de pluie. En début de saison, update_rainfall.py se replie sur la saison précédente tant
    qu'aucune donnée de la nouvelle n'est publiée : ce repli n'est pas « ancien », l'âge court depuis le début
    de la saison en cours."""
    season_start = dt.date(today.year if today.month >= start_month else today.year - 1, start_month, 1)
    return (today - max(through, season_start)).days


def consequential_errors(base, meta, top, cfg, today, skip_age=False):
    """Contrat des couches publiées, sans conclure à leur validité scientifique.

    Une source facultative peut être absente, mais pas présenter des valeurs
    actives sans métadonnées cohérentes. La fraîcheur utilise le seuil météo
    déjà configuré, également pour les prévisions de crue et de ruissellement.
    """
    errors = []
    max_age = cfg.get('forecast', {}).get('max_age_days', 3)

    def reject(message):
        errors.append(message)

    def number(value, low=0, high=math.inf):
        return (type(value) in (int, float) and math.isfinite(value)
                and low <= value <= high)

    def fresh(value, label):
        try:
            date = dt.datetime.fromisoformat(value.replace('Z', '+00:00')).date()
            if not skip_age and not 0 <= (today - date).days <= max_age:
                reject(f'{label} : date future ou périmée ({value})')
        except (TypeError, ValueError, AttributeError):
            reject(f'{label} : date absente ou illisible')

    forecast = meta.get('forecast')
    flood = {}
    ensemble = {}
    if forecast is not None:
        if not isinstance(forecast, dict):
            reject('prévision : métadonnées invalides')
            forecast = None
        else:
            fresh(forecast.get('fetched_at'), 'prévision météo')
            try:
                first, last = (dt.date.fromisoformat(forecast[k]) for k in ('first', 'last'))
                if first > last or (not skip_age and not first <= today <= last):
                    reject('prévision : période incohérente ou hors date courante')
            except (KeyError, TypeError, ValueError):
                reject('prévision : période absente ou illisible')
            if forecast.get('hazards') != ['rain', 'wind', 'heat', 'dry', 'flood']:
                reject('prévision : ordre des aléas invalide')
            flood = forecast.get('flood') or {}
            if not isinstance(flood, dict):
                reject('crue : métadonnées invalides')
                flood = {}
            if flood.get('available'):
                fresh(flood.get('fetched_at'), 'prévision crue')
            ensemble = flood.get('ensemble') or {}
            if not isinstance(ensemble, dict):
                reject('ensemble crue : métadonnées invalides')
                ensemble = {}
            elif ensemble.get('available'):
                fresh(ensemble.get('fetched_at'), 'ensemble crue')
                if not flood.get('available') or not number(ensemble.get('members'), 1):
                    reject('ensemble crue : source ou effectif incohérent')

    pluvial = None
    path = base / 'pluvial_forecast.json'
    if path.exists():
        try:
            pluvial = json.loads(path.read_text(encoding='utf-8'))
            if type(pluvial.get('available')) is not bool:
                raise ValueError('available absent')
            if pluvial['available']:
                fresh(pluvial.get('generated'), 'ruissellement produit')
                fresh(pluvial.get('forecast_fetched_at'), 'ruissellement source')
                if pluvial.get('experimental') is not True or not pluvial.get('warning'):
                    reject('ruissellement : statut expérimental ou avertissement absent')
                days = [dt.date.fromisoformat(d) for d in pluvial['days']]
                if not days or days != sorted(set(days)) or (not skip_age and today not in days):
                    reject('ruissellement : période incohérente')
                regions = pluvial['regions']
                if not isinstance(regions, list) or not regions:
                    raise ValueError('régions absentes')
                for row in regions:
                    if not number(row.get('niveau_max'), 0, 2) or not number(row.get('part_fokontany_vigilance_pct'), 0, 100):
                        reject('ruissellement : niveau ou pourcentage régional invalide')
        except (ValueError, TypeError, KeyError, AttributeError):
            reject('ruissellement : JSON ou schéma invalide')
            pluvial = None

    layers = [('metrics/top.json', top)]
    for district in top.get('adm2', {}):
        path = base / 'metrics' / 'd' / f'{district}.json'
        try:
            layers.append((str(path.relative_to(base)), json.loads(path.read_text(encoding='utf-8'))))
        except (OSError, ValueError):
            reject(f'{path.name} : détail territorial absent ou illisible')
    bounds = {'susc_inond_pct': (0, 100), 'potentiel_eau_pct': (0, 100),
              'ruiss_prevu_mm': (0, math.inf), 'ruiss_prevu_niveau': (0, 2),
              'ruiss_prevu_part_pct': (0, 100), 'water_table_depth_m': (0, math.inf),
              'aquifer_yield_lsec_mid': (0, math.inf), 'recharge12_mm': (0, math.inf)}
    for filename, layer in layers:
        try:
            for units in layer.values():
                for code, row in units.items():
                    label = f'{filename}/{code}'
                    if forecast is None and any(k in row for k in ('ew', 'ew2', 'ewp', 'ewt', 'ewe5', 'ev', 'fp2', 'fp3')):
                        reject(f'{label} : alerte sans prévision disponible')
                    if forecast is not None and 'ew' not in row:
                        reject(f'{label} : niveaux des alertes absents')
                    for key in ('ew', 'ew2'):
                        if key in row and (not isinstance(row[key], list) or len(row[key]) != 5
                                or any(type(v) is not int or not 0 <= v <= 3 for v in row[key])):
                            reject(f'{label} : {key} invalide')
                    for key in ('ewp', 'ewt', 'ewe5'):
                        if 'ew' in row:
                            values = row.get(key)
                            if not isinstance(values, list) or len(values) != 5 or any(not number(v, 0, row['p'] + 1) for v in values):
                                reject(f'{label} : {key} ou population invalide')
                    if 'ewp' in row and 'ewt' in row and any(t > e + 1 for t, e in zip(row['ewt'], row['ewp'])):
                        reject(f'{label} : cibles d’alerte supérieures aux exposés')
                    for key in ('fp2', 'fp3'):
                        if key in row:
                            if not ensemble.get('available'):
                                reject(f'{label} : probabilité sans ensemble disponible')
                            if not isinstance(row[key], list) or len(row[key]) != 3 or any(v is not None and not number(v, 0, 100) for v in row[key]):
                                reject(f'{label} : probabilité de crue invalide')
                    if 'ew' in row and 'ev' not in row:
                        reject(f'{label} : valeurs météo/crue absentes')
                    if 'ev' in row:
                        ev = row['ev']
                        if not isinstance(ev, list) or len(ev) != 10:
                            reject(f'{label} : valeurs météo/crue invalides')
                        else:
                            for i, value in enumerate(ev):
                                if value is not None and not number(value, -math.inf if i == 2 else 0, 100 if i >= 7 else math.inf):
                                    reject(f'{label} : valeur météo/crue hors bornes')
                            if not flood.get('available') and (any(v is not None for v in ev[5:]) or row.get('ew', [0]*5)[4] != 0):
                                reject(f'{label} : crue active sans source disponible')
                            if not ensemble.get('available') and any(v is not None for v in ev[7:]):
                                reject(f'{label} : probabilités sans ensemble disponible')
                    for key, value in row.get('x', {}).items():
                        if key in bounds and not number(value, *bounds[key]):
                            reject(f'{label} : {key} hors bornes')
                        if key.startswith('ruiss_prevu_') and not (pluvial and pluvial.get('available')):
                            reject(f'{label} : ruissellement actif sans source disponible')
        except (TypeError, KeyError, AttributeError, IndexError):
            reject(f'{filename} : schéma des couches à forte conséquence invalide')
    return errors


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--max-age-days", type=int, default=75)
    ap.add_argument("--skip-age", action="store_true", help="Pour les tests avec des données simulées")
    args = ap.parse_args()
    cfg = load_config(args.country)
    base = country_docs_dir(args.country)
    errors = []

    for f in ("meta.json", "index.json", "catalogue.json", "metrics/top.json", "geo/adm1.geojson", "geo/adm2.geojson"):
        if not (base / f).exists():
            errors.append(f"fichier manquant : {f}")
    if errors:
        print("\n".join(errors)); sys.exit(1)

    meta = json.loads((base / "meta.json").read_text(encoding="utf-8"))
    top = json.loads((base / "metrics" / "top.json").read_text(encoding="utf-8"))
    errors.extend(consequential_errors(base, meta, top, cfg, dt.date.today(), args.skip_age))
    if meta["national"]["pop"] <= 0:
        errors.append("population nationale nulle")
    n_districts = len(top["adm2"])
    nodata = sum(1 for v in top["adm2"].values() if v["l"] == 0)
    if n_districts == 0 or nodata / n_districts > 0.2:
        errors.append(f"{nodata}/{n_districts} districts sans donnée de pluie (> 20 %)")
    for k, v in top["adm2"].items():
        if "pc" in v and not (0 <= v["pc"] <= 1000):
            errors.append(f"% de la normale hors bornes ({k}: {v['pc']})")
        if v["e"] > (v["p"] or 0) + 1:
            errors.append(f"exposés > population ({k})")
        if v["t"] > v["e"] + 1:
            errors.append(f"cibles > exposés ({k})")
    sm, em = cfg["rainfall"]["season_start_month"], cfg["rainfall"]["season_end_month"]
    month = dt.date.today().month
    in_season = (month >= sm or month <= em) if sm > em else (sm <= month <= em)
    if not args.skip_age and in_season:
        age = rain_age_days(dt.date.fromisoformat(meta["data_through"]), dt.date.today(), sm)
        if age > args.max_age_days:
            errors.append(f"données de pluie trop anciennes ({age} jours)")
    if errors:
        print("VALIDATION ÉCHOUÉE :\n- " + "\n- ".join(errors))
        sys.exit(1)
    print(f"Validation OK — {cfg['name']}, pluie jusqu'au {meta['data_through']}, {n_districts} districts.")


if __name__ == "__main__":
    main()
