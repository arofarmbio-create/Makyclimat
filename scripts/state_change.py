"""Détection de changement d'état à partir de l'archive des instantanés déjà collectés par le pipeline.

Pourquoi : l'utilisateur a demandé que MakyClimat "voie les changements d'état de situation, basé sur
des données réelles qu'on a intégrées et qui se mettent à jour systématiquement" -- pas en ajoutant une
nouvelle source, mais en réutilisant l'historique que `archive_snapshot.py` construit déjà à chaque
nouvelle dékade de pluie (archive/<pays>/<date>.json), gardé dans git depuis le début du projet.

Limite assumée : l'archive ne couvre que les niveaux région (adm1) et district (adm2) -- commune et
fokontany n'y figurent pas (fichiers détaillés trop volumineux pour être versionnés, voir
archive_snapshot.py). La durée/tendance n'est donc calculée qu'à ces deux niveaux. Avec un historique
encore court (projet récent), "depuis N dékades" peut simplement vouloir dire "depuis le début de
l'archivage", pas depuis un vrai changement -- ce cas est signalé explicitement (voir "depuis_origine").
"""
from __future__ import annotations

import json

from common import ROOT


def load_level_history(country: str) -> dict[str, list[tuple[str, int]]]:
    """Historique (date, niveau d'alerte saisonnier) par pcode région/district, depuis les instantanés archivés."""
    hist: dict[str, list[tuple[str, int]]] = {}
    adir = ROOT / "archive" / country
    if not adir.exists():
        return hist
    for f in sorted(adir.glob("*.json")):
        try:
            snap = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        date = snap.get("data_through", f.stem)
        for lvl_key in ("adm1", "adm2"):
            for pc, m in snap.get("metrics", {}).get(lvl_key, {}).items():
                if isinstance(m, dict) and "l" in m:
                    hist.setdefault(pc, []).append((date, int(m["l"])))
    for pc in hist:
        hist[pc].sort(key=lambda x: x[0])
    return hist


def state_for(pcode: str, today_date: str, today_level: int, hist: dict[str, list[tuple[str, int]]]) -> dict | None:
    """Durée au niveau actuel et tendance récente, pour une région ou un district (pcode présent dans l'archive)."""
    series = hist.get(pcode, [])
    series = [(d, lv) for d, lv in series if d < today_date] + [(today_date, today_level)]
    if len(series) < 2:   # aucun historique antérieur : rien de plus à dire que "aujourd'hui"
        return None
    n = 1
    depuis_origine = False
    for i in range(len(series) - 2, -1, -1):
        if series[i][1] == today_level:
            n += 1
        else:
            break
    else:
        depuis_origine = True   # le niveau actuel est le même depuis le tout premier instantané archivé
    since = series[len(series) - n][0]
    trend = 0
    if len(series) >= 4:
        trend = today_level - series[-4][1]
    return {"dekades": n, "since": since, "trend": int(trend), "depuis_origine": depuis_origine}
