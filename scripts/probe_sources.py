"""Sonde : indicateurs de choc et SPI sur le site publié."""
import requests, re
BASE = "https://arofarmbio-create.github.io/Makyclimat/data/mdg/"
t = requests.get(BASE + "meta.json", timeout=60).text
out = [f"meta.json {len(t)} car."]
for k in ["spi3", "spi6", "spi12", "choc_cyc_vent_kt", "choc_cyc_dist_km", "choc_cyc_retour_ans", "choc_cyc_nb", "choc_cyc_dernier_jours", "susc_inond_pct", "cult_basse5_pct", "choc_crue_retour_ans", "choc_crue_ratio_q2"]:
    out.append(f"{k}: {len(re.findall(k, t))}")
r = requests.get("https://arofarmbio-create.github.io/Makyclimat/", timeout=60).text
out.append("page Fiabilité en ligne : " + str("tab-trust" in r))
out.append("page : rubrique JIAF dans app.js : " + str("Chocs (format JIAF)" in requests.get("https://arofarmbio-create.github.io/Makyclimat/app.js", timeout=60).text))
open("data/_probe.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
