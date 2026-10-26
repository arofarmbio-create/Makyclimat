"""Sondage ad hoc : vérifier l'humidité du sol et l'IPC sur le site publié."""
import requests

B = "https://arofarmbio-create.github.io/Makyclimat/"
out = []
for p in ["data/mdg/soilwater/status.json", "data/mdg/soilwater/series.json", "data/mdg/catalogue.json"]:
    r = requests.get(B + p, timeout=60)
    out.append(f"{p} -> {r.status_code} {len(r.content)} octets")
    if p.endswith("catalogue.json") and r.ok:
        t = r.text
        for k in ["soil", "sol_", "recharge", "nappe", "humidite", "ipc", "hapi"]:
            out.append(f"   '{k}' present: {k in t}")
    if p.endswith("status.json") and r.ok:
        out.append("   " + r.text[:200].replace("\n", " "))
open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
