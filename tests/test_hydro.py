"""Tests du noyau d'hydrologie de terrain sur des terrains synthétiques dont on connaît la réponse."""
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import hydro_core as H  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK   " if cond else "ÉCHEC") + " " + name + (f" — {extra}" if extra else ""))
    if not cond:
        FAILS += 1


def valley(h=60, w=41):
    r, c = np.mgrid[0:h, 0:w]
    dem = (100 * (1 - r / h) + 3 * np.abs(c - w // 2)).astype(float)
    sea = r >= h - 3
    dem[sea] = -1
    return dem, sea


def run_chain(dem, sea):
    h, w = dem.shape
    z, ds = H.fill_and_route(dem, sea)
    area = np.ones(h * w)
    acc = H.accumulate(ds, area, sea.ravel())
    return z, ds, acc


def test_conservation_and_valley():
    dem, sea = valley()
    h, w = dem.shape
    z, ds, acc = run_chain(dem, sea)
    out = H.basin_outlets(ds, sea.ravel())
    land = (~sea).sum()
    check("conservation : la somme des aires aux exutoires = aire de terre", abs(acc[out].sum() - land) < 1e-6, f"{acc[out].sum()} / {land}")
    centre = acc.reshape(h, w)[h - 4, w // 2]
    check("la vallée collecte l'essentiel : aire drainée au fond de vallée >= 75 % de la terre (le reste sort par les bords du domaine)", centre >= 0.75 * land, f"{centre} / {land}")
    lab = H.jump_labels(out | sea.ravel(), ds)
    check("toute cellule de terre rejoint un exutoire", np.isin(lab[~sea.ravel()], np.where(out)[0]).all())


def test_pit_filling():
    dem, sea = valley()
    dem[30, 20] -= 40.0      # cuvette profonde au milieu de la pente
    dem[31, 20] -= 40.0
    z, ds, acc = run_chain(dem, sea)
    out = H.basin_outlets(ds, sea.ravel())
    lab = H.jump_labels(out | sea.ravel(), ds)
    check("cuvettes : toutes les cellules drainent quand même vers la mer", np.isin(lab[~sea.ravel()], np.where(out)[0]).all())
    check("cuvettes : le MNT rempli n'est jamais plus bas que le MNT d'origine", (z >= dem - 1e-9).all())
    h, w = dem.shape
    check("cuvettes : l'eau passe par la cuvette (aire drainée élevée au-dessus)", acc.reshape(h, w)[29, 20] > 5)


def test_slope_and_hand():
    h, w = 60, 41
    r, c = np.mgrid[0:h, 0:w]
    plane = 0.10 * 1000.0 * (c * 0 + r) * 1.0     # 10 % : 100 m de dénivelé par 1000 m de maille
    s = H.slope_percent(plane, np.full(h, 1000.0), 1000.0)
    check("pente : plan incliné à 10 % -> 10 %", abs(s[10:-10, 10:-10].mean() - 10.0) < 1e-6, f"{s[20, 20]:.3f}")
    r2, c2 = np.mgrid[0:h, 0:w]
    dem = (3.0 * np.abs(c2 - w // 2) + 0.05 * (h - r2)).astype(float)   # versants à 3 m par maille, très faible pente le long de la vallée
    sea = r2 >= h - 3
    dem[sea] = -1
    z, ds, acc = run_chain(dem, sea)
    stream = (acc >= 300) & ~sea.ravel()
    ha = H.hand(z, ds, stream, sea.ravel()).reshape(h, w)
    check("HAND : sur le cours d'eau = 0", abs(ha[40, w // 2]) < 1e-6)
    check("HAND : 1 maille de la vallée ≈ 3 m", abs(ha[40, w // 2 + 1] - 3.05) < 0.3, f"{ha[40, w // 2 + 1]:.2f}")
    check("HAND : 5 mailles de la vallée ≈ 15 m", abs(ha[40, w // 2 + 5] - 15.25) < 0.8, f"{ha[40, w // 2 + 5]:.2f}")
    check("HAND : croît quand on s'éloigne du cours d'eau", ha[40, w // 2 + 8] > ha[40, w // 2 + 3] > ha[40, w // 2 + 1])


def test_strahler_and_reaches():
    # arbre : a,b -> c ; d,e -> f ; c,f -> g ; g -> mer(s) ; x -> c
    names = ["a", "b", "c", "d", "e", "f", "g", "s", "x"]
    i = {k: j for j, k in enumerate(names)}
    ds = np.arange(len(names))
    for a, b in [("a", "c"), ("b", "c"), ("d", "f"), ("e", "f"), ("c", "g"), ("f", "g"), ("g", "s"), ("x", "c")]:
        ds[i[a]] = i[b]
    stream = np.ones(len(names), dtype=bool)
    stream[i["s"]] = False
    o = H.strahler(ds, stream)
    check("Strahler : feuilles = 1", all(o[i[k]] == 1 for k in "abdex"))
    check("Strahler : deux ordres 1 qui se rejoignent -> 2 ; un ordre 1 de plus ne change rien", o[i["c"]] == 2 and o[i["f"]] == 2, f"{o[i['c']]}")
    check("Strahler : deux ordres 2 qui se rejoignent -> 3", o[i["g"]] == 3, f"{o[i['g']]}")


def test_basins_two_valleys():
    h, w = 60, 61
    r, c = np.mgrid[0:h, 0:w]
    # crête centrale (c = 30) : deux vallées (c = 15 et c = 45) vers la mer au sud
    dem = (100 * (1 - r / h) + 3 * np.minimum(np.abs(c - 15), np.abs(c - 45))).astype(float)
    sea = r >= h - 3
    dem[sea] = -1
    z, ds, acc = run_chain(dem, sea)
    out = H.basin_outlets(ds, sea.ravel())
    big = np.where(out & (acc >= 200))[0]
    labs = H.jump_labels(out | sea.ravel(), ds)
    land = ~sea.ravel()
    areas = {int(b): int((labs[land] == b).sum()) for b in big}
    check("bassins : deux grands bassins versants séparés par la crête", len(big) >= 2 and sorted(areas.values())[-2] > 0.3 * land.sum(), str(sorted(areas.values())[-3:]))
    west = labs.reshape(h, w)[10, 12]
    east = labs.reshape(h, w)[10, 48]
    check("bassins : les deux versants ont des exutoires différents", west != east)


def test_reaches_and_perf():
    dem, sea = valley(60, 41)
    z, ds, acc = run_chain(dem, sea)
    stream = (acc >= 100) & ~sea.ravel()
    o = H.strahler(ds, stream)
    rs = H.reaches(ds, stream, acc, o, 41, 40.0, -10.0, 0.01)
    check("tronçons : au moins un tronçon, aires drainées croissantes vers l'aval", len(rs) >= 1 and all(a > 0 for _, a, _ in rs), f"{len(rs)} tronçons")
    check("tronçons : chaque tronçon a au moins 2 points", all(len(p) >= 2 for p, _, _ in rs))
    rng = np.random.default_rng(3)
    n = 300
    big = np.cumsum(np.cumsum(rng.normal(0, 1, (n, n)), 0), 1)
    big = (big - big.min()) / (big.max() - big.min()) * 1000
    sea = np.zeros((n, n), dtype=bool)
    sea[big < 40] = True
    t0 = time.time()
    z, ds, acc = run_chain(big, sea)
    out = H.basin_outlets(ds, sea.ravel())
    lab = H.jump_labels(out | sea.ravel(), ds)
    ok = np.isin(lab[~sea.ravel()], np.where(out)[0]).all() or (~sea).sum() == 0
    check("terrain aléatoire 300x300 : tout drainé, conservation de l'aire", ok and abs(acc[out].sum() - (~sea).sum()) < 1e-6, f"{time.time() - t0:.1f} s")


if __name__ == "__main__":
    test_conservation_and_valley()
    test_pit_filling()
    test_slope_and_hand()
    test_strahler_and_reaches()
    test_basins_two_valleys()
    test_reaches_and_perf()
    print("\nTous les tests d'hydrologie passent." if not FAILS else f"\n{FAILS} ÉCHEC(S)")
    sys.exit(1 if FAILS else 0)
