"""Inspection de la géodatabase GLiM (lecture seule)."""
import sys
import pyogrio

src = sys.argv[1]
for name, gtype in pyogrio.list_layers(src):
    print("couche", name, gtype)
    info = pyogrio.read_info(src, layer=name)
    print("  crs", info["crs"])
    print("  n", info["features"], "champs", list(info["fields"]))
    print("  emprise", info.get("total_bounds"))
