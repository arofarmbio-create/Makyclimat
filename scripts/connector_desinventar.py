"""Base nationale des pertes et dommages DesInventar (UNDRR ; fiches BNGRC pour Madagascar), par district et par événement.

Cahier des charges §4.D (historique des inondations, cyclones, pertes), §13 (vérité terrain d'impact indépendante des
modèles). Sert de vérité terrain à la vérification des prévisions d'ensemble de crue par l'impact (thèse) : là où il
n'existe pas de station hydrométrique publique, on vérifie la prévision contre les dégâts déclarés.
Source : export XML public https://www.desinventar.net (sans compte). Aucune licence de données explicite n'est publiée
(seul le logiciel est sous Apache-2) : comme pour EM-DAT, les fiches brutes ne sont PAS versionnées ni republiées
(data/<pays>/external/desinventar.csv est ignoré par git) ; seuls des décomptes agrégés le sont.
Limites : base de déclarations (pas d'enregistrement = pas de déclaration, pas forcément pas d'impact) ; couverture
inégale selon les années ; codes de district de 2011 (OCHA/BNGRC), rapprochés des limites actuelles par leur code.
Méthode transférable : changer desinventar.country (code DesInventar à 3 lettres, environ 90 pays) dans config/countries.
Usage : python scripts/connector_desinventar.py --country mdg
"""
from __future__ import annotations

import argparse
import collections
import csv
import io
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

from common import country_data_dir, load_config, read_units

URL = "https://www.desinventar.net/DesInventar/download/DI_export_{code}.zip"
# fragments sans accent : les accents sont parfois illisibles dans l'export
TYPES = {"CYCLON": "cyclone", "INOND": "inondation", "GLISSEMENT": "glissement", "CHERESSE": "secheresse"}
NUM = {"afectados": "touches", "damnificados": "sinistres", "muertos": "deces", "desaparece": "disparus",
       "vivdest": "maisons_detruites", "vivafec": "maisons_endommagees", "reubicados": "deplaces", "nhectareas": "cultures_ha"}
COLS = ["serial", "type", "evenement", "date", "annee", "adm1", "adm2", "adm2_actuel", "glide", *NUM.values(), "source"]


def download(code: str) -> bytes:
    req = urllib.request.Request(URL.format(code=code), headers={"User-Agent": "MakyClimat"})
    with urllib.request.urlopen(req, timeout=600) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    name = next(n for n in z.namelist() if n.lower().endswith(".xml"))
    return z.read(name)


def number(s: str | None) -> float | str:
    try:
        v = float(s)
    except (TypeError, ValueError):
        return ""
    return v if v >= 0 else ""                                       # -1 = « non renseigné » dans DesInventar


def current_districts(code: str, known: set[str], split: dict) -> str:
    """District(s) actuel(s) d'un code DesInventar : identique, découpé (config desinventar.split), ou même numéro de
    district dans une région renommée (ex. Vatovavy-Fitovinany 23209 -> Vatovavy 26209) s'il est unique. « ; » entre plusieurs."""
    if code in known:
        return code
    if code in split:
        return ";".join(split[code])
    same = [k for k in known if k[-3:] == code[-3:]]
    return same[0] if len(same) == 1 else ""


def parse(raw: bytes, prefix: str, known: set[str], split: dict | None = None) -> list[dict]:
    # l'export mélange UTF-8 et Latin-1 : les octets invalides sont remplacés (seuls des noms d'événements sont touchés)
    root = ET.fromstring(raw.decode("utf-8", errors="replace").encode("utf-8"))
    out = []
    for tr in root.find("fichas"):
        g = {c.tag: (c.text or "").strip() for c in tr}
        ev = g.get("evento", "").upper()
        typ = next((v for k, v in TYPES.items() if k in ev), "autre")
        y, m, d = g.get("fechano", ""), g.get("fechames", ""), g.get("fechadia", "")
        if not y.isdigit():
            continue
        date = f"{int(y):04d}-{int(m):02d}-{int(d):02d}" if m.isdigit() and d.isdigit() and int(m) and int(d) else ""
        adm1 = prefix + g["level0"] if g.get("level0") else ""
        adm2 = prefix + g["level1"] if g.get("level1") and g["level1"] != "00" else ""
        out.append({"serial": g.get("serial", ""), "type": typ, "evenement": g.get("evento", ""), "date": date, "annee": int(y),
                    "adm1": adm1, "adm2": adm2, "adm2_actuel": current_districts(adm2, known, split or {}) if adm2 else "", "glide": g.get("glide", ""),
                    **{v: number(g.get(k)) for k, v in NUM.items()}, "source": g.get("fuentes", "")})
    return sorted(out, key=lambda r: (r["annee"], r["date"], r["serial"]))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    cfg = load_config(args.country).get("desinventar")
    if not cfg:
        raise SystemExit("desinventar absent de la configuration du pays : rien à faire.")
    units = read_units(args.country)
    recs = parse(download(cfg["country"]), cfg.get("pcode_prefix", ""), set(units.pcode[units.level == 2]), cfg.get("split"))
    out = country_data_dir(args.country) / "external" / "desinventar.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(recs)
    n = collections.Counter(r["type"] for r in recs)
    d = [r for r in recs if r["adm2"]]
    print(f"DesInventar {cfg['country']} : {len(recs)} fiches {dict(n)} ; {len(d)} au niveau district, dont "
          f"{sum(bool(r['adm2_actuel']) for r in d)} rapprochées des limites actuelles ; années {recs[0]['annee']}-{recs[-1]['annee']}")


if __name__ == "__main__":
    main()
