"""Relief sur la grille commune de l'expérience E1 (0,1°, 145 x 80 mailles), pour les zones de l'hypothèse H3-E1
(protocole E1, modification du 02/11/2026) : Hautes Terres, rugosité, versant au vent ou sous le vent.

Source : Copernicus GLO-90 (ESA/Copernicus, libre, Amazon S3), lu avec le lecteur de build_hydro.py et ré-échantillonné
en moyenne à 0,01° (~1 km), soit 10 x 10 pixels par maille de 0,1°. La mer (0 m reliée au bord) est exclue.
Pour chaque maille :
  altitude_m : altitude moyenne ;
  rugosite_m : écart-type de l'altitude des pixels de 1 km ;
  exposition_est : composante est-ouest de la pente de grande échelle, en m/km, positive quand le terrain monte vers
    l'ouest (versant tourné vers l'est, AU VENT des alizés), négative quand il monte vers l'est (SOUS LE VENT). Calculée
    sur l'altitude moyenne de 0,1° lissée sur 3 x 3 mailles (~30 km), pour retenir les grands versants et non les
    vallées.
Sortie : data/<pays>/e1/relief_01deg.npz (petit, versionné).
Usage : python scripts/build_relief_e1.py --country mdg
"""
from __future__ import annotations

import argparse

import numpy as np

import build_e1_sources as E
from common import country_data_dir

DEM_RES = 0.01


def block_stats(dem: np.ndarray, lon0: float, lat_top: float, res: float = DEM_RES):
    """MNT (nord en haut, mer = NaN) -> (moyenne, écart-type) par maille de la grille commune (sud en bas)."""
    k = round(0.1 / res)
    r0, c0 = round((lat_top - E.LAT1) / res), round((E.LON0 - lon0) / res)
    a = dem[r0:r0 + E.NY * k, c0:c0 + E.NX * k]
    if a.shape != (E.NY * k, E.NX * k):
        raise ValueError(f"emprise du MNT insuffisante : {a.shape}")
    b = a.reshape(E.NY, k, E.NX, k)
    n = np.isfinite(b).sum(axis=(1, 3))
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = np.where(n > 0, np.nansum(b, axis=(1, 3)) / np.maximum(n, 1), np.nan)
        var = np.where(n > 1, np.nansum((b - mean[:, None, :, None]) ** 2, axis=(1, 3)) / np.maximum(n - 1, 1), np.nan)
    return mean[::-1].astype("float32"), np.sqrt(var)[::-1].astype("float32")


def exposure_east(mean: np.ndarray) -> np.ndarray:
    """Pente est-ouest (m/km) de l'altitude moyenne lissée 3 x 3, signe + quand le terrain monte vers l'ouest."""
    from scipy import ndimage
    land = np.isfinite(mean)
    z = np.where(land, mean, 0.0)
    w = ndimage.uniform_filter(land.astype(float), 3, mode="nearest")
    zs = np.where(w > 0, ndimage.uniform_filter(z, 3, mode="nearest") / np.maximum(w, 1e-9), np.nan)
    dx_km = 0.1 * 111.32 * np.cos(np.deg2rad(E.LATS))[:, None]
    dzdx = np.gradient(zs, axis=1) / dx_km                    # m/km, positif si l'altitude augmente vers l'est
    return np.where(land, -dzdx, np.nan).astype("float32")


def main() -> None:
    import build_hydro as H
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    dem, lon0, lat_top = H.read_dem([E.LON0, E.LAT0, E.LON1, E.LAT1], res=DEM_RES, workers=3)
    sea = H.sea_mask(dem)
    dem = np.where(sea, np.nan, dem)
    mean, std = block_stats(dem, lon0, lat_top)
    expo = exposure_east(mean)
    out = country_data_dir(args.country) / "e1"
    out.mkdir(exist_ok=True)
    path = out / "relief_01deg.npz"
    np.savez_compressed(path, altitude_m=mean, rugosite_m=std, exposition_est=expo, lat=E.LATS, lon=E.LONS,
                        source=np.array("Copernicus GLO-90, moyenne à 0,01° puis statistiques par maille de 0,1°"))
    land = np.isfinite(mean)
    print(f"{path.name} : {int(land.sum())} mailles terrestres ; altitude médiane {np.nanmedian(mean):.0f} m ; "
          f"{int((mean > 1000).sum())} mailles au-dessus de 1 000 m ; au vent {int((expo > 0).sum())}, "
          f"sous le vent {int((expo < 0).sum())}")


if __name__ == "__main__":
    main()
