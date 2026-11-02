"""Carte nationale des nappes (validation/protocole_carte_nappes.md) : couches mondiales recadrées sur Madagascar.

Chaque partie télécharge une couche publiée, la recadre sur l'emprise du pays (résolution native conservée) et note
sa source, sa licence et ses unités dans <partie>.json. Aucun calcul de modèle ici.

  fan       : profondeur de nappe, Fan et al. 2017 (mise à jour de Fan et al. 2013), 30″, m (OPeNDAP)
              licence : usage de recherche libre avec citation -> jamais republié
  fluor     : probabilité de fluor > 1,5 mg/L, Podgorski et Berg 2022, 250 m (zip Eawag de 2 Go)
              licence non précisée -> jamais republié
  socle     : profondeur absolue du socle, SoilGrids 2017 (Shangguan et al. 2017), 250 m, cm (lecture distante) - ODbL
  glhymps   : perméabilité et porosité, GLHYMPS 2.0 (Huscroft et al. 2018), polygones (zip de 2,6 Go) - CC BY 4.0
  glim      : lithologie, GLiM (Hartmann et Moosdorf 2012), grille 0,5° - CC BY 3.0
  salinite  : conductivité des eaux souterraines, Thorslund et van Vliet 2020, points - CC BY 4.0
Sortie : data/<pays>/nappes_mondiales/<partie>.(tif|gpkg|csv) et <partie>.json.
Usage : python scripts/build_nappes_mondiales.py --country mdg --part fan
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import requests

from common import country_data_dir, download, load_config

SOURCES = {
    "fan": {
        "url": "http://thredds-gfnl.usc.es/thredds/dodsC/GLOBALWTDFTP/annualmeans/AFRICA_WTD_annualmean.nc",
        "citation": "Fan Y., Miguez-Macho G., Jobbágy E. G., Jackson R. B., Otero-Casal C. (2017). Hydrologic regulation "
                    "of plant rooting depth. PNAS 114(40), 10572-10577. doi:10.1073/pnas.1712381114 (mise à jour de Fan "
                    "et al. 2013, Science 339, 940-943)",
        "licence": "usage de recherche libre, citation obligatoire ; redistribution non prévue (ne pas republier)",
        "republication": False, "unite": "m, niveau de la nappe par rapport au sol (négatif = sous la surface), moyenne annuelle", "resolution": "30 secondes d'arc (~1 km)"},
    "fluor": {
        "url": "https://opendata.eawag.ch/dataset/2012f6f6-afb5-4c30-b032-89f28d0acd93/resource/840629ab-1899-4754-a2aa-827fe479a5ef/download/maps.zip",
        "citation": "Podgorski J., Berg M. (2022). Global analysis and prediction of fluoride in groundwater. Nature "
                    "Communications 13, 4232. Données : doi:10.25678/0006GQ",
        "licence": "open data Eawag, licence non précisée (ne pas republier sans accord des auteurs)",
        "republication": False, "unite": "probabilité en % (0-100) que le fluor dépasse 1,5 mg/L (médiane de 21 sur Madagascar au 02/11/2026)", "resolution": "250 m"},
    "socle": {
        "url": "https://files.isric.org/soilgrids/former/2017-03-10/data/BDTICM_M_250m_ll.tif",
        "citation": "Shangguan W., Hengl T. et al. (2017). Mapping the global depth to bedrock for land surface modeling. "
                    "JAMES 9, 65-88. SoilGrids250m 2017 (ISRIC), couche BDTICM_M",
        "licence": "Open Database License (ODbL) : attribution et partage à l'identique",
        "republication": True, "unite": "cm (profondeur absolue du socle)", "resolution": "250 m (7,5 secondes d'arc)"},
    "glhymps": {
        "url": "https://borealisdata.ca/api/access/datafile/71909",
        "citation": "Huscroft J., Gleeson T., Hartmann J., Börker J. (2018). Compiling and mapping global permeability of "
                    "the unconsolidated and consolidated Earth: GLobal HYdrogeology MaPS 2.0 (GLHYMPS 2.0). GRL 45, "
                    "1897-1904. Données : doi:10.5683/SP2/TTJNIU",
        "licence": "CC BY 4.0", "republication": True,
        "unite": "logK_Ferr_x100_INT : log10 de la perméabilité (m²) x 100 ; Porosity_x100 : porosité x 100",
        "resolution": "polygones (lithologie GLiM)"},
    "glim": {
        "url": "https://hdl.handle.net/10013/epic.39939.d001",
        "citation": "Hartmann J., Moosdorf N. (2012). Global Lithological Map Database v1.0 (gridded to 0.5°). PANGAEA, "
                    "doi:10.1594/PANGAEA.788537",
        "licence": "CC BY 3.0", "republication": True, "unite": "classe lithologique (code GLiM de premier niveau)",
        "resolution": "0,5°"},
    "salinite": {
        "url": "https://hs.pangaea.de/bio/Salinity_database/Thorslund-vanVliet_2020/Groundwaters_summary.csv",
        "citation": "Thorslund J., van Vliet M. T. H. (2020). A global dataset of surface water and groundwater salinity "
                    "measurements from 1980-2019. Scientific Data 7, 231. Données : doi:10.1594/PANGAEA.913939",
        "licence": "CC BY 4.0", "republication": True, "unite": "µS/cm (conductivité électrique)", "resolution": "points"},
}
GLIM_CLASSES = {1: "su", 2: "vb", 3: "ss", 4: "pb", 5: "sm", 6: "sc", 7: "va", 8: "mt", 9: "pa", 10: "vi", 11: "wb",
                12: "py", 13: "pi", 14: "ev", 15: "nd", 16: "ig"}   # Hartmann et Moosdorf 2012 (Classnames.txt)


def bbox_of(cfg):
    lon0, lat0, lon1, lat1 = cfg["map"]["bbox"]
    return lon0, lat0, lon1, lat1


def crop_ascii_grid(text: str, bbox):
    """Grille ESRI ASCII (ncols, nrows, xllcorner, yllcorner, cellsize, NODATA_value) -> (tableau recadré nord en haut,
    ouest, nord, pas). Les mailles dont le centre est dans l'emprise sont gardées ; NODATA -> NaN."""
    lines = text.splitlines()
    head = {}
    k = 0
    while len(head) < 6:
        key, val = lines[k].split()[:2]
        head[key.lower()] = float(val)
        k += 1
    nc, nr, x0, y0, cs = int(head["ncols"]), int(head["nrows"]), head["xllcorner"], head["yllcorner"], head["cellsize"]
    a = np.array(" ".join(lines[k:]).split(), dtype="float64").reshape(nr, nc)
    a[a == head["nodata_value"]] = np.nan
    lon0, lat0, lon1, lat1 = bbox
    xc = x0 + cs * (np.arange(nc) + 0.5)
    yc = y0 + cs * (nr - np.arange(nr) - 0.5)                        # ligne 0 = nord
    cols = np.where((xc >= lon0) & (xc <= lon1))[0]
    rows = np.where((yc >= lat0) & (yc <= lat1))[0]
    sub = a[rows.min():rows.max() + 1, cols.min():cols.max() + 1]
    return sub, x0 + cs * cols.min(), y0 + cs * (nr - rows.min()), cs


def filter_points(df, bbox, lat="Lat", lon="Lon"):
    lon0, lat0, lon1, lat1 = bbox
    return df[(df[lat] >= lat0) & (df[lat] <= lat1) & (df[lon] >= lon0) & (df[lon] <= lon1)].copy()


def write_tif(path: Path, arr, west, north, res, dtype="float32", nodata=np.nan):
    import rasterio
    from rasterio.transform import from_origin
    with rasterio.open(path, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1, dtype=dtype,
                       crs="EPSG:4326", transform=from_origin(west, north, res, res), compress="deflate",
                       nodata=nodata) as dst:
        dst.write(arr.astype(dtype), 1)


def read_window(path: str, bbox):
    import rasterio
    from rasterio.windows import from_bounds
    with rasterio.open(path) as src:
        win = from_bounds(*bbox, transform=src.transform).round_offsets().round_lengths()
        arr = src.read(1, window=win).astype("float32")
        t = src.window_transform(win)
        if src.nodata is not None:
            arr[arr == src.nodata] = np.nan
        return arr, t.c, t.f, t.a


def part_fan(bbox, out):
    import xarray as xr
    ds = xr.open_dataset(SOURCES["fan"]["url"])                     # OPeNDAP : seul le recadrage est transféré
    lat = ds["lat"].values
    lat_slice = slice(bbox[1], bbox[3]) if lat[0] < lat[-1] else slice(bbox[3], bbox[1])
    w = ds["WTD"].isel(time=0).sel(lat=lat_slice, lon=slice(bbox[0], bbox[2]))
    m = ds["mask"].sel(lat=lat_slice, lon=slice(bbox[0], bbox[2]))
    a = np.where(m.values == 1, w.values, np.nan).astype("float32")
    la, lo = w["lat"].values, w["lon"].values
    if la[0] < la[-1]:
        a, la = a[::-1], la[::-1]
    res = float(abs(lo[1] - lo[0]))
    write_tif(out / "fan.tif", a, float(lo[0]) - res / 2, float(la[0]) + res / 2, res)
    return {"mailles": int(np.isfinite(a).sum()), "mediane_m": round(float(np.nanmedian(a)), 2)}


def part_fluor(bbox, out):
    tmp = Path(tempfile.mkdtemp()) / "maps.zip"
    if not download(SOURCES["fluor"]["url"], tmp, retries=3, timeout=1800):
        raise SystemExit("archive du fluor introuvable")
    name = next(n for n in zipfile.ZipFile(tmp).namelist() if n.endswith("global_F_hazard_model.tif"))
    a, west, north, res = read_window(f"/vsizip/{tmp}/{name}", bbox)
    write_tif(out / "fluor.tif", a, west, north, res)
    tmp.unlink()
    return {"mailles": int(np.isfinite(a).sum()), "probabilite_mediane": round(float(np.nanmedian(a)), 3)}


def part_socle(bbox, out):
    a, west, north, res = read_window("/vsicurl/" + SOURCES["socle"]["url"], bbox)   # lecture distante, ligne par ligne
    write_tif(out / "socle.tif", a, west, north, res)
    return {"mailles": int(np.isfinite(a).sum()), "mediane_cm": round(float(np.nanmedian(a)), 0)}


def part_glhymps(bbox, out):
    import pyogrio
    tmp = Path(tempfile.mkdtemp()) / "glhymps.zip"
    if not download(SOURCES["glhymps"]["url"], tmp, retries=3, timeout=3600):
        raise SystemExit("archive GLHYMPS introuvable")
    names = zipfile.ZipFile(tmp).namelist()
    shp = next((n for n in names if n.lower().endswith(".shp")), None)
    gdb = next((n.split(".gdb")[0] + ".gdb" for n in names if ".gdb/" in n), None)
    src = f"/vsizip/{tmp}/{shp}" if shp else f"/vsizip/{tmp}/{gdb}"
    info = pyogrio.read_info(src)
    from pyproj import Transformer
    crs = info.get("crs") or "EPSG:4326"
    tr = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    xs, ys = tr.transform([bbox[0], bbox[2], bbox[0], bbox[2]], [bbox[1], bbox[1], bbox[3], bbox[3]])
    g = pyogrio.read_dataframe(src, bbox=(min(xs), min(ys), max(xs), max(ys)))
    g = g.to_crs("EPSG:4326")
    keep = [c for c in g.columns if c in ("logK_Ferr_x100_INT", "logK_Ferr_", "Porosity_x100", "Porosity_x", "K_stdev_x100",
                                           "K_stdev_x1", "XX", "YY", "ZZ", "AA", "MEAN", "geometry")]
    g[keep].to_file(out / "glhymps.gpkg", driver="GPKG")
    tmp.unlink()
    return {"polygones": int(len(g)), "colonnes": [c for c in keep if c != "geometry"], "crs_source": str(crs)}


def part_glim(bbox, out):
    r = requests.get(SOURCES["glim"]["url"], timeout=300)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    asc = z.read(next(n for n in z.namelist() if n.endswith(".asc"))).decode("latin-1")
    a, west, north, res = crop_ascii_grid(asc, bbox)
    write_tif(out / "glim.tif", a, west, north, res)
    vals, cnt = np.unique(a[np.isfinite(a)], return_counts=True)
    return {"mailles": int(np.isfinite(a).sum()), "classes": {GLIM_CLASSES.get(int(v), str(int(v))): int(c) for v, c in zip(vals, cnt)}}


def part_salinite(bbox, out):
    import pandas as pd
    tmp = Path(tempfile.mkdtemp()) / "gw.csv"
    if not download(SOURCES["salinite"]["url"], tmp, retries=3, timeout=600):
        raise SystemExit("base de salinité introuvable")
    df = filter_points(pd.read_csv(tmp, low_memory=False), bbox)
    df.to_csv(out / "salinite.csv", index=False)
    return {"points": int(len(df)), "pays": sorted(df["Country"].dropna().unique().tolist()) if len(df) else []}


PARTS = {"fan": part_fan, "fluor": part_fluor, "socle": part_socle, "glhymps": part_glhymps, "glim": part_glim,
         "salinite": part_salinite}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--part", required=True, choices=sorted(PARTS))
    args = ap.parse_args()
    cfg = load_config(args.country)
    out = country_data_dir(args.country) / "nappes_mondiales"
    out.mkdir(exist_ok=True)
    resume = PARTS[args.part](bbox_of(cfg), out)
    meta = {**SOURCES[args.part], "partie": args.part, "emprise": list(bbox_of(cfg)),
            "telecharge_le": dt.date.today().isoformat(), "resume": resume}
    (out / f"{args.part}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{args.part} : {resume}")


if __name__ == "__main__":
    main()
