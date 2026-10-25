"""Sondage de sources depuis GitHub Actions : le résultat est écrit dans data/_probe.txt (lisible dans le dépôt)."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
out = []


def note(msg):
    print(msg)
    out.append(str(msg))


try:
    import connector_osm_services as CO
    t = time.time()
    els = CO.fetch()
    pts = CO.classify(els)
    note(f"== OSM Overpass OK : {len(els)} éléments en {time.time() - t:.0f} s ; {(pts.kind == 'edu').sum()} écoles, {(pts.kind == 'sante').sum()} formations sanitaires, dont {int(pts.hopital.sum())} hôpitaux")
    import json
    from shapely.geometry import shape
    from common import country_docs_dir
    geoms = {}
    for f in sorted((country_docs_dir("mdg") / "geo" / "adm4").glob("*.geojson")):
        for ft in json.loads(f.read_text(encoding="utf-8"))["features"]:
            geoms[ft["properties"]["c"]] = shape(ft["geometry"])
    c = CO.count_by_unit(pts, geoms)
    note(f"   fokontany : {len(geoms)} ; avec école {(c.osm_ecoles > 0).sum()} ; avec formation sanitaire {(c.osm_sante > 0).sum()} ; total écoles rattachées {int(c.osm_ecoles.sum())}, formations {int(c.osm_sante.sum())}")
except Exception as e:
    note(f"== OSM ECHEC {type(e).__name__}: {str(e)[:400]}")
open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
sys.exit(0)
