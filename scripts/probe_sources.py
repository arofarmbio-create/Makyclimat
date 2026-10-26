"""Sonde : vérifie les valeurs cultures/bâti sur le site publié."""
import requests, re
BASE = "https://arofarmbio-create.github.io/Makyclimat/data/mdg/"
out = []
for rel in ["index.json", "meta.json", "geo/meta.json"]:
    r = requests.get(BASE + rel, timeout=60)
    t = r.text
    out.append(f"{rel} -> {r.status_code} {len(t)} car.; cult_ : {len(re.findall('cult_', t))}; susc_inond_pct : {len(re.findall('susc_inond_pct', t))}; cult_basse5_pct : {len(re.findall('cult_basse5_pct', t))}")
    out.append("   début : " + t[:300].replace("\n", " "))
open("data/_probe.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
