"""Sonde : vérifie le site publié (catalogue des indicateurs cultures et bâti)."""
import json, requests
BASE = "https://arofarmbio-create.github.io/Makyclimat/"
out = []
for rel in ["data/mdg/catalogue.json", "data/mdg/index.json"]:
    r = requests.get(BASE + rel, timeout=60)
    out.append(f"{rel} -> {r.status_code} {len(r.content)} octets")
    if rel.endswith("catalogue.json") and r.ok:
        ids = [i["id"] for i in r.json()["indicators"] if i["id"].startswith(("cult_", "bati_"))]
        out.append("indicateurs cultures/bâti publiés : " + ", ".join(ids))
    if rel.endswith("index.json") and r.ok:
        t = r.text
        out.append("cult_ présent dans index.json : %s" % ("cult_" in t))
open("data/_probe.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
