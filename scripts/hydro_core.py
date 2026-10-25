"""Hydrologie de terrain à partir d'un modèle numérique de terrain (MNT) : fonctions pures, testées sur terrains synthétiques.

Chaîne (algorithmes classiques, publiés) :
  1. remplissage des cuvettes par « Priority-Flood + epsilon » (Barnes, Lehman & Mulla 2014) : chaque cellule reçoit le sens d'écoulement
     vers la cellule par laquelle elle a été atteinte ; la mer est l'exutoire ;
  2. accumulation d'écoulement (aire drainée) par épluchage des cellules sans amont ;
  3. réseau hydrographique (aire drainée >= seuil), ordre de Strahler, tronçons ;
  4. bassins versants par « saut de pointeurs » depuis les exutoires ;
  5. HAND (Height Above Nearest Drainage, Rennó et al. 2008) : hauteur d'une cellule au-dessus du cours d'eau où elle se déverse ;
  6. pente (différences finies).
Les cellules sont indexées à plat (ligne * largeur + colonne). La mer (ou toute cellule hors terre) est donnée par un masque booléen.
"""
from __future__ import annotations

import heapq

import numpy as np

NEIGH = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def fill_and_route(dem: np.ndarray, sea: np.ndarray):
    """Retourne (dem_rempli, ds) : ds[i] = indice de la cellule aval (la mer et les cellules de bord pointent sur elles-mêmes)."""
    h, w = dem.shape
    z = dem.astype("float64").copy()
    n = h * w
    ds = np.arange(n, dtype=np.int64)
    seen = np.zeros(n, dtype=bool)
    flat_sea = sea.ravel()
    zf = z.ravel()
    heap = []
    for i in np.where(flat_sea)[0]:
        seen[i] = True
        heap.append((zf[i], int(i)))
    # les bords du domaine qui ne sont pas de la mer sont aussi des exutoires
    edge = np.zeros((h, w), dtype=bool)
    edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
    for i in np.where((edge & ~sea).ravel())[0]:
        seen[i] = True
        heap.append((zf[i], int(i)))
    heapq.heapify(heap)
    while heap:
        zc, c = heapq.heappop(heap)
        r, col = divmod(c, w)
        for dr, dc in NEIGH:
            rr, cc = r + dr, col + dc
            if rr < 0 or rr >= h or cc < 0 or cc >= w:
                continue
            nb = rr * w + cc
            if seen[nb]:
                continue
            seen[nb] = True
            if zf[nb] <= zc:
                zf[nb] = zc + 1e-5   # petite pente artificielle dans les cuvettes et les zones plates (1e-5 m)
            ds[nb] = c
            heapq.heappush(heap, (zf[nb], nb))
    return zf.reshape(h, w), ds


def cell_area_km2(lats: np.ndarray, res_deg: float) -> np.ndarray:
    """Aire d'une maille régulière en degrés (km²) pour chaque latitude (vecteur)."""
    km = 111.32
    return (res_deg * km) ** 2 * np.cos(np.deg2rad(lats))


def accumulate(ds: np.ndarray, area: np.ndarray, sea_flat: np.ndarray) -> np.ndarray:
    """Aire drainée (km²) en chaque cellule de terre, y compris la sienne. area : aire de chaque cellule (n,)."""
    n = len(ds)
    idx = np.arange(n)
    land = ~sea_flat
    acc = np.where(land, area, 0.0).astype("float64")
    has_down = land & (ds != idx) & land[ds]
    indeg = np.bincount(ds[has_down], minlength=n)
    frontier = np.where(land & (indeg == 0))[0]
    while frontier.size:
        mv = frontier[has_down[frontier]]
        tgt = ds[mv]
        np.add.at(acc, tgt, acc[mv])
        np.subtract.at(indeg, tgt, 1)
        cand = np.unique(tgt)
        frontier = cand[indeg[cand] == 0]
    return acc


def strahler(ds: np.ndarray, stream: np.ndarray) -> np.ndarray:
    """Ordre de Strahler sur les cellules du réseau (stream : masque booléen à plat). 0 hors réseau."""
    n = len(ds)
    idx = np.arange(n)
    has_down = stream & (ds != idx) & stream[ds]
    indeg = np.bincount(ds[has_down], minlength=n)
    order = np.where(stream, 1, 0).astype(int)
    maxin = np.zeros(n, dtype=int)
    cntmax = np.zeros(n, dtype=int)
    frontier = np.where(stream & (indeg == 0))[0]
    while frontier.size:
        # l'ordre d'une cellule se fixe quand tous ses amonts sont traités
        mv = frontier[has_down[frontier]]
        for c in mv:                      # tronçons : boucle sur la frontière (petite)
            t = ds[c]
            o = order[c]
            if o > maxin[t]:
                maxin[t], cntmax[t] = o, 1
            elif o == maxin[t]:
                cntmax[t] += 1
        tgt = ds[mv]
        np.subtract.at(indeg, tgt, 1)
        cand = np.unique(tgt)
        ready = cand[indeg[cand] == 0]
        for t in ready:
            order[t] = maxin[t] + 1 if cntmax[t] >= 2 else max(1, maxin[t])
        frontier = ready
    return order


def jump_labels(term: np.ndarray, ds: np.ndarray) -> np.ndarray:
    """Pour chaque cellule, la première cellule « terminale » (term True) rencontrée en descendant (saut de pointeurs)."""
    nxt = np.where(term, np.arange(len(ds)), ds).astype(np.int64)
    while True:
        nn = nxt[nxt]
        if np.array_equal(nn, nxt):
            return nn
        nxt = nn


def basin_outlets(ds: np.ndarray, sea_flat: np.ndarray) -> np.ndarray:
    """Cellules de terre qui se jettent dans la mer (ou hors domaine) : exutoires des grands bassins."""
    idx = np.arange(len(ds))
    return (~sea_flat) & ((ds == idx) | sea_flat[ds])


def slope_percent(dem: np.ndarray, dx_m: np.ndarray, dy_m: float) -> np.ndarray:
    """Pente en % (différences centrales). dx_m : largeur de maille en m pour chaque ligne (h,)."""
    gy, gx = np.gradient(dem.astype("float64"))
    return 100.0 * np.hypot(gx / dx_m[:, None], gy / dy_m)


def hand(dem_filled: np.ndarray, ds: np.ndarray, stream_flat: np.ndarray, sea_flat: np.ndarray) -> np.ndarray:
    """Hauteur (m) au-dessus du cours d'eau où l'eau de la cellule se déverse ; NaN si elle ne rejoint aucun cours d'eau avant la mer."""
    term = stream_flat | sea_flat | (ds == np.arange(len(ds)))
    lab = jump_labels(term, ds)
    z = dem_filled.ravel()
    out = z - z[lab]
    out[~stream_flat[lab]] = np.nan
    out[sea_flat] = np.nan
    return out.reshape(dem_filled.shape)


def reaches(ds: np.ndarray, stream: np.ndarray, acc: np.ndarray, order: np.ndarray, w: int, lon0: float, lat0: float, res: float):
    """Tronçons du réseau : liste de (liste de (lon, lat), aire drainée à l'aval en km², ordre de Strahler à l'aval)."""
    n = len(ds)
    idx = np.arange(n)
    has_down = stream & (ds != idx) & stream[ds]
    indeg = np.bincount(ds[has_down], minlength=n)
    starts = np.where(stream & (indeg != 1))[0]
    out = []

    def xy(i):
        r, c = divmod(int(i), w)
        return (lon0 + (c + 0.5) * res, lat0 - (r + 0.5) * res)

    for s in starts:
        path = [int(s)]
        cur = int(s)
        while has_down[cur]:
            cur = int(ds[cur])
            path.append(cur)
            if indeg[cur] != 1:
                break
        if len(path) >= 2:
            out.append(([xy(i) for i in path], float(acc[path[-1]]), int(order[path[0]])))
    return out
