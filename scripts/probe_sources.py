import requests, re
BASE = "https://arofarmbio-create.github.io/Makyclimat/"
t = requests.get(BASE + "data/mdg/meta.json", timeout=60).text
out = [f"{k}: {len(re.findall(k, t))}" for k in ["route_km", "route_basse5_km", "route_basse5_pct", "route_dist_km", "choc_crue_retour_ans", "spi3"]]
out.append("Fiabilité routes en ligne : " + str("Routes principales en zone basse" in requests.get(BASE, timeout=60).text))
open("data/_probe.txt", "w").write("\n".join(out) + "\n"); print("\n".join(out))
