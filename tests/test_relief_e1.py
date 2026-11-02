"""Relief sur la grille E1 (scripts/build_relief_e1.py) : moyenne, rugosité, versant au vent ou sous le vent."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_e1_sources as E  # noqa: E402
import build_relief_e1 as R  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


k = 10
h, w = E.NY * k, E.NX * k
cols = np.arange(w)[None, :].repeat(h, 0).astype("float32")
west_high = 2000.0 - cols                    # le terrain monte vers l'ouest : versant tourné vers l'est (au vent)
mean, std = R.block_stats(west_high, E.LON0, E.LAT1)
check("forme 145 x 80, sud en bas", mean.shape == (E.NY, E.NX))
check("altitude moyenne d'une maille = moyenne de ses 10 x 10 pixels", np.isclose(mean[0, 0], 2000.0 - 4.5))
check("rugosité = écart-type des 100 pixels de la maille", np.isclose(std[0, 0], np.std(np.tile(np.arange(10.0), 10), ddof=1), rtol=1e-4))
check("terrain qui monte vers l'ouest : exposition positive (au vent)", np.nanmedian(R.exposure_east(mean)) > 0)
check("terrain qui monte vers l'est : exposition négative (sous le vent)",
      np.nanmedian(R.exposure_east(R.block_stats(cols.copy(), E.LON0, E.LAT1)[0])) < 0)
north = np.zeros((h, w), "float32")
north[:k, :k] = np.nan                       # coin nord-ouest en mer
m2, _ = R.block_stats(north, E.LON0, E.LAT1)
check("maille entièrement en mer : manquante, au nord (dernière ligne)", np.isnan(m2[-1, 0]) and not np.isnan(m2[0, 0]))

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
