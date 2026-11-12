"""Teste scripts/build_cmip6_nexgddp.py sur données SIMULÉES, sans réseau : conversion d'unités, agrégation mensuelle
selon le calendrier, moyenne régionale pondérée par la surface, lecture d'une réponse netCDF-3, URL NCSS, essais.

Usage : python tests/test_build_cmip6_nexgddp.py
"""
from __future__ import annotations

import io
import sys
import tempfile
from unittest.mock import patch
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_cmip6_nexgddp as C  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


# --- calendriers
m = C.month_of_day(365, "noleap", 2001)
check("365 jours : 31 jours en janvier, 28 en février, 31 en décembre",
      (m == 1).sum() == 31 and (m == 2).sum() == 28 and (m == 12).sum() == 31)
m = C.month_of_day(366, "proleptic_gregorian", 2000)
check("année bissextile grégorienne : 29 jours en février", (m == 2).sum() == 29 and len(m) == 366)
m = C.month_of_day(360, "360_day", 2050)
check("360 jours : 30 jours par mois", all((m == k).sum() == 30 for k in range(1, 13)))
try:
    C.month_of_day(365, "standard", 2000)
    check("fichier incomplet refusé (365 jours pour une année bissextile)", False)
except ValueError:
    check("fichier incomplet refusé (365 jours pour une année bissextile)", True)

# --- conversions et agrégation mensuelle
months = C.month_of_day(365, "noleap", 2001)
pr = np.full((365, 2, 2), 1.0 / 86400)                    # 1 mm/jour partout
pr[:, 1, 1] = np.nan                                       # maille de mer
mo = C.daily_to_monthly(pr, months, "pr", "kg m-2 s-1")
check("pr : 1 mm/jour -> 31 mm en janvier, 28 en février", np.isclose(mo[0, 0, 0], 31) and np.isclose(mo[1, 0, 0], 28))
check("pr : maille vide -> NaN", np.isnan(mo[0, 1, 1]))
tas = np.zeros((365, 1, 1)) + 300.0
tas[months == 7] = 290.0
mt = C.daily_to_monthly(tas, months, "tas", "K")
check("tas : K -> °C (300 K = 26,85 °C ; juillet 16,85 °C)", np.isclose(mt[0, 0, 0], 26.85) and np.isclose(mt[6, 0, 0], 16.85))
try:
    C.daily_to_monthly(pr, months, "pr", "mm/day")
    check("unité de pr inattendue refusée", False)
except ValueError:
    check("unité de pr inattendue refusée", True)

# --- moyenne régionale pondérée par la surface (grille 0,25°, deux régions)
lat = np.array([-20.125, -19.875])                         # sud -> nord, comme NCSS
lon = np.array([45.125, 45.375])
monthly = np.zeros((12, 2, 2))
monthly[:, 0, 0], monthly[:, 0, 1] = 10.0, 30.0            # rangée sud
monthly[:, 1, 0], monthly[:, 1, 1] = 100.0, 200.0          # rangée nord
units = pd.DataFrame({
    "level": [4, 4, 4], "pcode": ["A1", "A2", "B1"], "adm1": ["A", "A", "B"],
    "lon": [45.1, 45.3, 45.2], "lat": [-20.1, -20.1, -19.9], "area_km2": [1.0, 3.0, 2.0]})
reg = C.regional_means(monthly, lat, lon, units)
check("région A : (1 x 10 + 3 x 30) / 4 = 25", np.allclose(reg["A"], 25.0), f"{reg['A'][0]:.2f}")
check("région B : maille nord-ouest = 100", np.allclose(reg["B"], 100.0), f"{reg['B'][0]:.2f}")
reg_ns = C.regional_means(monthly[:, ::-1], lat[::-1], lon, units)
check("ordre des latitudes indifférent (nord -> sud ou sud -> nord)",
      np.allclose(reg_ns["A"], reg["A"]) and np.allclose(reg_ns["B"], reg["B"]))


# --- lecture d'une réponse netCDF-3 simulée (comme NCSS accept=netcdf3) et chaîne complète
def fake_nc3(var="pr", n=365, cal="noleap", units_v="kg m-2 s-1", value=2.0 / 86400, lic="CC-BY-SA 4.0"):
    from scipy.io import netcdf_file
    buf = io.BytesIO()
    f = netcdf_file(buf, "w", version=1)
    if lic is not None:
        f.cmip6_license = lic
    f.version = "2.0"
    f.createDimension("time", n)
    f.createDimension("lat", 2)
    f.createDimension("lon", 2)
    t = f.createVariable("time", "d", ("time",))
    t[:] = np.arange(n) + 0.5
    t.calendar = cal
    t.units = "days since 2001-01-01"
    la = f.createVariable("lat", "d", ("lat",))
    la[:] = lat
    lo = f.createVariable("lon", "d", ("lon",))
    lo[:] = lon
    v = f.createVariable(var, "f", ("time", "lat", "lon"))
    d = np.full((n, 2, 2), value, dtype="float32")
    d[:, 1, 1] = 1e20
    v[:] = d
    v.units = units_v
    v._FillValue = np.float32(1e20)
    f.flush()
    out = buf.getvalue()
    f.close()
    return out


nc = C.read_nc3(fake_nc3(), "pr")
check("lecture netCDF-3 : forme, calendrier, licence, valeur de remplissage -> NaN",
      nc["data"].shape == (365, 2, 2) and nc["calendar"] == "noleap" and nc["attrs"]["cmip6_license"] == "CC-BY-SA 4.0"
      and np.isnan(nc["data"][0, 1, 1]))


class FakeResp:
    def __init__(self, status, content):
        self.status_code, self.content = status, content


class FakeSession:
    def __init__(self, responses):
        self.responses, self.urls = list(responses), []

    def get(self, url, timeout):
        self.urls.append(url)
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


s = FakeSession([FakeResp(200, fake_nc3())])
rows, info = C.process_file("ACCESS-CM2", "ssp245", "r1i1p1f1", "gn", "pr", 2050, units, s)
df = pd.DataFrame(rows)
check("chaîne complète : 2 régions x 12 mois, colonnes du CSV long",
      len(df) == 24 and list(df.columns) == C.COLUMNS, f"{len(df)} lignes")
check("chaîne complète : 2 mm/jour -> 62 mm en janvier, 56 en février (région A)",
      np.isclose(df[(df.region == "A") & (df.mois == 1)].valeur.iloc[0], 62)
      and np.isclose(df[(df.region == "A") & (df.mois == 2)].valeur.iloc[0], 56))
check("licence consignée", info["licence"] == "CC-BY-SA 4.0" and info["calendrier"] == "noleap")
check("une seule requête", len(s.urls) == 1)
try:
    C.process_file("X", "ssp245", "r1i1p1f1", "gn", "pr", 2050, units,
                   FakeSession([FakeResp(200, fake_nc3(lic="Non-commercial only"))]))
    check("licence non admise : arrêt", False)
except SystemExit:
    check("licence non admise : arrêt", True)

# --- URL NCSS
for scenario in ("historical", "ssp245"):
    for lic in (None, "", "   ", "Non-commercial only"):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            with patch.object(C, "read_units", return_value=units), \
                 patch.object(C, "fetch", return_value=fake_nc3(lic=lic)), \
                 patch.object(C, "daily_to_monthly") as aggregate:
                try:
                    C.run("ACCESS-CM2", scenario, 2001, 2001, ["pr"], out)
                    check(f"{scenario}, licence {lic!r} : arrêt", False)
                except SystemExit:
                    check(f"{scenario}, licence {lic!r} : arrêt avant agrégation et écriture",
                          not aggregate.called and not list(out.iterdir()))

for lic in ("CC0 1.0", "CC BY 4.0", "CC-BY-SA 4.0"):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        with patch.object(C, "read_units", return_value=units), \
             patch.object(C, "fetch", return_value=fake_nc3(lic=lic)), \
             patch.object(C.time, "sleep"):
            C.run("ACCESS-CM2", "historical", 2001, 2001, ["pr"], out)
        import json
        saved = json.loads((out / "ACCESS-CM2_historical_meta.json").read_text(encoding="utf-8"))
        check(f"licence {lic} admise : CSV et provenance consignés",
              len(pd.read_csv(out / "ACCESS-CM2_historical.csv")) == 24
              and saved["fichiers"]["pr/2001"]["licence"] == lic
              and "cmip6_license" in saved["fichiers"]["pr/2001"]["source_licence"])

# Une erreur tardive reste un échec : les années valides locales ne sont pas publiées.
with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp)
    with patch.object(C, "read_units", return_value=units), \
         patch.object(C, "fetch", side_effect=[fake_nc3(), fake_nc3(lic=None)]), \
         patch.object(C.time, "sleep"):
        try:
            C.run("ACCESS-CM2", "ssp245", 2001, 2002, ["pr"], out)
            check("échec tardif propagé", False)
        except SystemExit:
            check("échec tardif : aucune ligne de l'année refusée",
                  set(pd.read_csv(out / "ACCESS-CM2_ssp245.csv").annee) == {2001})
    metaf = out / "ACCESS-CM2_ssp245_meta.json"
    metaf.write_text('{"fichiers": {"pr/2001": {"licence": "absente de la réponse NCSS"}}}', encoding="utf-8")
    before = (out / "ACCESS-CM2_ssp245.csv").read_bytes()
    with patch.object(C, "read_units", return_value=units), patch.object(C, "fetch") as fetch:
        try:
            C.run("ACCESS-CM2", "ssp245", 2001, 2001, ["pr"], out)
            check("ancienne reprise sans licence refusée", False)
        except SystemExit:
            check("ancienne reprise sans licence refusée sans requête ni écriture",
                  not fetch.called and (out / "ACCESS-CM2_ssp245.csv").read_bytes() == before)

import yaml
workflow = yaml.safe_load((Path(__file__).resolve().parents[1] /
                          ".github/workflows/build-cmip6-nexgddp.yml").read_text(encoding="utf-8"))
steps = workflow["jobs"]["nexgddp"]["steps"]
publish = [step for step in steps if "gh release upload" in step.get("run", "")]
check("publication uniquement après succès, aucune création de release avant extraction",
      len(publish) == 1 and publish[0]["if"] == "success() && github.event.inputs.probe != 'true'"
      and all("gh release create" not in step.get("run", "") for step in steps if step is not publish[0])
      and not any(step.get("continue-on-error", False) for step in steps))

# --- URL NCSS
u = C.ncss_url("ACCESS-CM2", "historical", "r1i1p1f1", "gn", "pr", 2014)
check("URL NCSS : chemin et nom de fichier v2.0, emprise, netCDF-3",
      u.startswith("https://ds.nccs.nasa.gov/thredds/ncss/grid/AMES/NEX/GDDP-CMIP6/ACCESS-CM2/historical/r1i1p1f1/pr/"
                   "pr_day_ACCESS-CM2_historical_r1i1p1f1_gn_2014_v2.0.nc?")
      and "north=-11.5" in u and "south=-26.0" in u and "west=43.0" in u and "east=51.0" in u
      and "accept=netcdf3" in u and "temporal=all" in u)

# --- essais : 3 au plus, 30 s entre deux
pauses = []
s = FakeSession([FakeResp(503, b"busy"), ConnectionError("coupure"), FakeResp(200, b"<html>")])
try:
    C.fetch("u", s, sleep=pauses.append)
    check("fetch : 3 échecs -> erreur", False)
except RuntimeError:
    check("fetch : 3 essais, 2 pauses de 30 s, puis erreur", len(s.urls) == 3 and pauses == [30, 30])
pauses = []
s = FakeSession([FakeResp(500, b""), FakeResp(200, b"CDF\x01...")])
check("fetch : réussite au 2e essai", C.fetch("u", s, sleep=pauses.append).startswith(b"CDF") and pauses == [30])

# --- liste des modèles (data/mdg/cmip6_modeles.json)
import json  # noqa: E402
meta = json.loads(C.MODELS_JSON.read_text(encoding="utf-8"))
keep = [x for x in meta["modeles"] if x["statut"] == "à garder"]
check("liste des modèles : 28 complets sur 35, tous avec membre et grille",
      len(keep) == meta["n_complets"] == 28 and all(x["membre"] and x["grille_source"] for x in keep))

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
