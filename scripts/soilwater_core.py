"""Noyau du bilan hydrique du sol : formules publiées, sans paramètre ajusté à la main.

Références :
  - Saxton K.E., Rawls W.J. (2006) Soil water characteristic estimates by texture and organic matter for hydrologic solutions.
    Soil Sci. Soc. Am. J. 70:1569-1578. -> capacité au champ (33 kPa), point de flétrissement (1500 kPa).
  - USDA-NRCS National Engineering Handbook, partie 630, chap. 7 et 9 (1986, 2004) : groupes hydrologiques de sol, courbe-numéro (CN),
    ruissellement SCS : Q = (P - 0,2 S)^2 / (P + 0,8 S), S = 25400/CN - 254 (mm). Conditions antécédentes : Hawkins et al. (1985).
  - Allen R.G. et al. (1998) FAO Irrigation and Drainage Paper 56, tableau 22 : profondeur racinaire maximale des cultures.
  - Thornthwaite C.W., Mather J.R. (1957) bilan hydrique mensuel du sol ; forme exponentielle : Steenhuis T.S., Van der Molen W.H. (1986).
  - Indices standardisés par scores normaux (SPI/SGI) : McKee et al. (1993) ; Bloomfield J.P., Marchant B.P. (2013) HESS 17:4769-4787.
Limites connues : bilan mensuel (le ruissellement dépend de l'intensité journalière), CN de table pour des occupations du sol « moyennes »,
texture du sol de SoilGrids (250 m) : les sols ferrallitiques argileux de Madagascar sont plus perméables que leur texture ne l'indique.
"""
from __future__ import annotations

import numpy as np

# ---------------- Propriétés hydriques du sol (Saxton & Rawls 2006) ----------------


def saxton_rawls(sand, clay, om_pct):
    """sand, clay : fractions (0-1) ; om_pct : matière organique en %. Retourne (point de flétrissement, capacité au champ), en m3/m3."""
    S, C, OM = np.asarray(sand, float), np.asarray(clay, float), np.asarray(om_pct, float)
    t1500 = -0.024 * S + 0.487 * C + 0.006 * OM + 0.005 * S * OM - 0.013 * C * OM + 0.068 * S * C + 0.031
    wp = t1500 + (0.14 * t1500 - 0.02)
    t33 = -0.251 * S + 0.195 * C + 0.011 * OM + 0.006 * S * OM - 0.027 * C * OM + 0.452 * S * C + 0.299
    fc = t33 + (1.283 * t33 ** 2 - 0.374 * t33 - 0.015)
    return wp, fc


def usda_texture(sand_pct, clay_pct):
    """Indice (dans TEXTURES) de la classe de texture USDA (triangle des textures, définitions standard NRCS) ; -1 si non classé."""
    sa, cl = np.asarray(sand_pct, float), np.asarray(clay_pct, float)
    si = 100.0 - sa - cl
    cls = np.full(sa.shape, -1, dtype=int)
    T = {n: i for i, n in enumerate(TEXTURES)}
    cls[(si + 1.5 * cl < 15)] = T["sable"]
    cls[(si + 1.5 * cl >= 15) & (si + 2 * cl < 30)] = T["sable limoneux"]
    c = ((cl >= 7) & (cl < 20) & (sa > 52) & (si + 2 * cl >= 30)) | ((cl < 7) & (si < 50) & (si + 2 * cl >= 30))
    cls[c] = T["limon sableux"]
    cls[(cl >= 7) & (cl < 27) & (si >= 28) & (si < 50) & (sa <= 52)] = T["limon"]
    cls[((si >= 50) & (cl >= 12) & (cl < 27)) | ((si >= 50) & (si < 80) & (cl < 12))] = T["limon silteux"]
    cls[(si >= 80) & (cl < 12)] = T["silt"]
    cls[(cl >= 20) & (cl < 35) & (si < 28) & (sa > 45)] = T["limon argilo-sableux"]
    cls[(cl >= 27) & (cl < 40) & (sa > 20) & (sa <= 45)] = T["limon argileux"]
    cls[(cl >= 27) & (cl < 40) & (sa <= 20)] = T["limon argilo-silteux"]
    cls[(cl >= 35) & (sa > 45)] = T["argile sableuse"]
    cls[(cl >= 40) & (si >= 40)] = T["argile silteuse"]
    cls[(cl >= 40) & (sa <= 45) & (si < 40)] = T["argile"]
    return cls


TEXTURES = ["sable", "sable limoneux", "limon sableux", "limon", "limon silteux", "silt", "limon argilo-sableux", "limon argileux",
            "limon argilo-silteux", "argile sableuse", "argile silteuse", "argile"]
# Groupe hydrologique de sol (A faible ruissellement ... D fort) selon la texture : pratique standard NRCS (Musgrave 1955 ; NEH-4 chap. 7)
HSG_OF_TEXTURE = {"sable": "A", "sable limoneux": "A", "limon sableux": "A", "limon": "B", "limon silteux": "B", "silt": "B",
                  "limon argilo-sableux": "C", "limon argileux": "D", "limon argilo-silteux": "D", "argile sableuse": "D", "argile silteuse": "D", "argile": "D"}
HSG_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3}
HSG_ARRAY = np.array([HSG_INDEX[HSG_OF_TEXTURE[t]] for t in TEXTURES])

# ---------------- Occupation du sol (ESA WorldCover) -> CN et profondeur racinaire ----------------
# CN (condition II) par groupe A, B, C, D : NEH-4 tableaux 9-1 (terres agricoles, pâturages, forêts) et 2-2a (zones bâties).
# Correspondance WorldCover -> catégorie NEH-4 (choix documentés, à affiner avec des données locales) :
#   10 arbres      -> « Woods, good »            30 55 70 77
#   20 arbustes    -> « Brush, good »            30 48 65 73
#   30 herbacées   -> « Pasture, fair »          49 69 79 84
#   40 cultures    -> « Row crops, straight row, good » 67 78 85 89 (les rizières inondées ne sont pas distinguées)
#   50 bâti        -> « Residential 1/8 acre, 65 % imperméable » 77 85 90 92
#   60 sol nu      -> « Fallow, bare soil »      77 86 91 94
#   80 eau         -> 100          90 zones humides herbacées -> « Meadow, good » 30 58 71 78          95 mangrove -> comme les arbres
# Profondeur racinaire maximale (m) : FAO-56 tableau 22 (forêt tropicale ~ 1,5-2 m ; arbustes ~ 1,0-1,5 m ; pâturage 0,5-1,5 m ; cultures annuelles 0,5-1,2 m).
# Valeurs retenues = milieu de fourchette FAO-56 (tableau 22) : arbres 1,75 ; arbustes 1,25 ; herbacées 1,0 ; cultures 0,85 ; bâti 0,2 ; sol nu 0,3 ; zones humides 1,0.
LANDCOVER = {
    10: {"cn": (30, 55, 70, 77), "root_m": 1.75},
    20: {"cn": (30, 48, 65, 73), "root_m": 1.25},
    30: {"cn": (49, 69, 79, 84), "root_m": 1.0},
    40: {"cn": (67, 78, 85, 89), "root_m": 0.85},
    50: {"cn": (77, 85, 90, 92), "root_m": 0.2},
    60: {"cn": (77, 86, 91, 94), "root_m": 0.3},
    80: {"cn": (100, 100, 100, 100), "root_m": 0.0},
    90: {"cn": (30, 58, 71, 78), "root_m": 1.0},
    95: {"cn": (30, 55, 70, 77), "root_m": 1.75},
}
LC_CLASSES = sorted(LANDCOVER)


def cn_lookup(lc, hsg):
    """CN (condition II) pour des tableaux d'occupation du sol (codes WorldCover) et de groupe hydrologique (0..3). NaN si hors table."""
    lc, hsg = np.asarray(lc), np.asarray(hsg)
    out = np.full(lc.shape, np.nan)
    for k, v in LANDCOVER.items():
        m = lc == k
        if m.any():
            tab = np.array(v["cn"], float)
            out[m] = tab[np.clip(hsg[m], 0, 3)]
    return out


def root_depth(lc):
    lc = np.asarray(lc)
    out = np.full(lc.shape, np.nan)
    for k, v in LANDCOVER.items():
        out[lc == k] = v["root_m"]
    return out


def whc_mm(fc, wp, root_m):
    """Réserve utile maximale du sol (mm) = (capacité au champ - point de flétrissement) x profondeur racinaire (m) x 1000."""
    return np.maximum(fc - wp, 0.0) * root_m * 1000.0


# ---------------- Ruissellement SCS-CN ----------------


def cn_dry(cn2):
    return 4.2 * cn2 / (10.0 - 0.058 * cn2)


def cn_wet(cn2):
    return 23.0 * cn2 / (10.0 + 0.13 * cn2)


def cn_for_moisture(cn2, rel):
    """CN selon l'humidité relative antécédente rel (0 = sol sec, 0,5 = condition II moyenne, 1 = saturé) : interpolation entre CN I, II et III (Hawkins et al. 1985)."""
    cn2 = np.asarray(cn2, float)
    rel = np.clip(np.asarray(rel, float), 0.0, 1.0)
    lo = cn_dry(cn2) + (cn2 - cn_dry(cn2)) * (rel / 0.5)
    hi = cn2 + (cn_wet(cn2) - cn2) * ((rel - 0.5) / 0.5)
    return np.where(rel <= 0.5, lo, hi)


def scs_runoff(p_mm, cn, ia_ratio=0.2):
    """Lame ruisselée (mm) d'une pluie P (mm) tombée en un événement : Q = (P - Ia)^2 / (P - Ia + S), Ia = 0,2 S, S = 25400/CN - 254."""
    p = np.asarray(p_mm, float)
    cn = np.asarray(cn, float)
    S = 25400.0 / np.clip(cn, 1.0, 100.0) - 254.0
    ia = ia_ratio * S
    ex = p - ia
    with np.errstate(invalid="ignore", divide="ignore"):
        q = np.where(ex > 0, ex ** 2 / (ex + S), 0.0)
    return np.where(np.isfinite(p) & np.isfinite(cn), q, np.nan)


# ---------------- Bilan hydrique mensuel de Thornthwaite-Mather ----------------


def tm_step(w_prev, p, pet, whc):
    """Un mois. w_prev : stock d'eau du sol (mm). Retourne (stock, évapotranspiration réelle, excédent)."""
    w_prev, p, pet, whc = (np.asarray(a, float) for a in (w_prev, p, pet, whc))
    wet = p >= pet
    gain = w_prev + (p - pet)
    w_wet = np.minimum(whc, gain)
    surplus = np.where(wet, np.maximum(gain - whc, 0.0), 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        w_dry = np.where(whc > 0, w_prev * np.exp(-(pet - p) / np.where(whc > 0, whc, 1.0)), 0.0)
    w = np.where(wet, w_wet, w_dry)
    aet = np.where(wet, pet, p + (w_prev - w_dry))
    return w, aet, surplus


def run_balance(precip, pet_clim, whc, month0, spinup_years=3):
    """Série mensuelle. precip : (T, N) mm ; pet_clim : (12, N) mm/mois ; month0 : mois (1-12) du premier pas ; whc : (N,).
    Retourne stock (T, N), évapotranspiration réelle (T, N), excédent (T, N). Le stock initial vient d'une mise en route sur les premiers mois."""
    T, N = precip.shape
    w = whc * 0.5
    months = [((month0 - 1 + t) % 12) for t in range(T)]
    for _ in range(spinup_years):                       # mise en route : on rejoue la 1re année
        for t in range(min(12, T)):
            w, _, _ = tm_step(w, precip[t], pet_clim[months[t]], whc)
    W = np.zeros((T, N))
    A = np.zeros((T, N))
    X = np.zeros((T, N))
    for t in range(T):
        w, a, x = tm_step(w, precip[t], pet_clim[months[t]], whc)
        W[t], A[t], X[t] = w, a, x
    return W, A, X


# ---------------- Indices standardisés (scores normaux) ----------------


def normal_scores(x, axis=0):
    """Transformation en scores normaux par rang (position de tracé de Gringorten) le long de `axis` ; NaN conservés ; égalités -> rang moyen."""
    from scipy import stats
    x = np.moveaxis(np.asarray(x, float), axis, 0)
    ok = np.isfinite(x)
    k = ok.sum(axis=0)
    r = stats.rankdata(np.where(ok, x, np.inf), axis=0)       # les NaN passent en dernier et n'altèrent pas le rang des valeurs valides
    z = stats.norm.ppf((r - 0.44) / (k + 0.12))
    z = np.where(ok & (k >= 10), z, np.nan)
    return np.moveaxis(z, 0, axis)


def rolling_sum(x, n):
    """Somme glissante sur n pas (T, ...) ; NaN pour les n-1 premiers pas."""
    c = np.cumsum(np.nan_to_num(x, nan=0.0), axis=0)
    out = np.full(x.shape, np.nan)
    out[n - 1:] = c[n - 1:] - np.concatenate([np.zeros((1,) + x.shape[1:]), c[:-n]], axis=0)[: len(x) - n + 1]
    return out


def monthly_standardized(series, month0, axis=0):
    """Standardise chaque mois de l'année séparément (comparaison avec le même mois des autres années). series (T, N)."""
    T = series.shape[0]
    out = np.full(series.shape, np.nan)
    for m in range(12):
        idx = np.array([t for t in range(T) if (month0 - 1 + t) % 12 == m])
        if len(idx) >= 10:
            out[idx] = normal_scores(series[idx], axis=0)
    return out
