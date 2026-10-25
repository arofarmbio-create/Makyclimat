"""Archive un instantané compact (régions et districts) à chaque nouvelle date de données.

Pourquoi : les fichiers détaillés sont recalculés à chaque mise à jour et ne sont pas conservés dans git (trop lourds).
Cet archivage garde l'historique des indicateurs par district, indispensable pour la validation rétrospective
de la thèse (comparer ce que l'outil signalait avec ce qui s'est réellement passé).
"""
from __future__ import annotations

import argparse
import json

from common import ROOT, country_docs_dir


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    base = country_docs_dir(args.country)
    meta = json.load(open(base / "meta.json", encoding="utf-8"))
    top = json.load(open(base / "metrics" / "top.json", encoding="utf-8"))
    slim = {lv: {pc: {k: v for k, v in m.items() if k not in ("se", "st")} for pc, m in d.items()}
            for lv, d in top.items()}
    out = ROOT / "archive" / args.country
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"{meta['data_through']}.json"
    if dest.exists():
        print("Instantané déjà archivé :", dest.name)
        return
    with open(dest, "w", encoding="utf-8") as f:
        json.dump({"data_through": meta["data_through"], "generated_at": meta["generated_at"],
                   "alert_levels": meta["alert_levels"], "default_vulnerable_share": meta["default_vulnerable_share"],
                   "metrics": slim}, f, ensure_ascii=False, separators=(",", ":"))
    print("Instantané archivé :", dest.name)


if __name__ == "__main__":
    main()
