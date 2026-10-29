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


def run_balance(precip, pet_clim, whc, month0, cn2=None, spinup_years=3):
    """Série mensuelle. precip : (T, N) mm ; pet_clim : (12, N) mm/mois ; month0 : mois (1-12) du premier pas ; whc : (N,).
    cn2 : CN (condition II) par cellule (N,), optionnel. S'il est fourni, le ruissellement SCS-CN (Hawkins et al. 1985 ;
    condition antécédente déduite du stock relatif du pas précédent) est retiré de la pluie AVANT le bilan du sol — X
    (l'excédent retourné) ne représente alors que l'eau infiltrée au-delà de la réserve utile (la recharge nette de
    ruissellement), et Q (ruissellement) est retourné séparément. Sans cn2 (par défaut), le comportement est inchangé :
    toute la pluie entre dans le bilan du sol et Q = 0 partout (X = tout le surplus, ruissellement et recharge confondus,
    comme avant la séparation du ruissellement).
    Limite connue : SCS-CN est conçu pour un événement de pluie isolé, pas un cumul mensuel ; appliqué ici au pas mensuel
    comme approximation documentée (pas de données journalières disponibles à l'échelle du pays).
    Retourne stock (T, N), évapotranspiration réelle (T, N), excédent/recharge (T, N), ruissellement (T, N). Le stock
    initial vient d'une mise en route sur les premiers mois."""
    T, N = precip.shape
    w = whc * 0.5
    months = [((month0 - 1 + t) % 12) for t in range(T)]

    def split(w_state, p):
        if cn2 is None:
            return p, np.zeros_like(p)
        rel = np.divide(w_state, whc, out=np.zeros_like(w_state), where=whc > 0)
        cn = cn_for_moisture(cn2, rel)
        q = np.minimum(scs_runoff(p, cn), p)
        return p - q, q

    for _ in range(spinup_years):                       # mise en route : on rejoue la 1re année
        for t in range(min(12, T)):
            p_eff, _ = split(w, precip[t])
            w, _, _ = tm_step(w, p_eff, pet_clim[months[t]], whc)
    W = np.zeros((T, N))
    A = np.zeros((T, N))
    X = np.zeros((T, N))
    Q = np.zeros((T, N))
    for t in range(T):
        p_eff, q = split(w, precip[t])
        w, a, x = tm_step(w, p_eff, pet_clim[months[t]], whc)
        W[t], A[t], X[t], Q[t] = w, a, x, q
    return W, A, X, Q


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


def spi(P, n, month0, min_mean_mm=None):
    """Indice de précipitation standardisé SPI-n (McKee et al. 1993 ; Guide de l'utilisateur du SPI, OMM-N° 1090, 2012).
    P (T, N) : pluie mensuelle (mm), le pas 0 étant le mois `month0` (1-12). Le cumul glissant sur n mois est ajusté, séparément pour chaque
    mois du calendrier, par une loi gamma (ajustement de Thom 1958) avec probabilité de zéro q ; SPI = Phi^-1(q + (1-q) G(x)), borné à +-3,09.
    Retourne (T, N) avec NaN pour les n-1 premiers pas et si moins de 20 cumuls valides.
    min_mean_mm : si donné, NaN là où la moyenne du cumul sur n mois (pour ce mois du calendrier) est inférieure au seuil. En saison
    sèche, quelques millimètres d'écart suffisent à donner un SPI extrême sans signification ; le Guide OMM-N° 1090 déconseille de
    l'interpréter dans les périodes climatologiquement très sèches."""
    from scipy import special, stats
    T = P.shape[0]
    S = rolling_sum(np.asarray(P, float), n)
    out = np.full(S.shape, np.nan)
    cal = np.array([(month0 - 1 + t) % 12 for t in range(T)])
    for m in range(12):
        idx = np.where((cal == m) & np.isfinite(S[:, 0] if S.ndim > 1 else S))[0]
        if len(idx) < 20:
            continue
        x = S[idx]
        ok = np.isfinite(x)
        pos = ok & (x > 0)
        npos, nok = pos.sum(axis=0), ok.sum(axis=0)
        q = 1.0 - npos / np.maximum(nok, 1)
        xm = np.where(pos, x, 0).sum(axis=0) / np.maximum(npos, 1)
        lm = np.where(pos, np.log(np.where(pos, x, 1.0)), 0).sum(axis=0) / np.maximum(npos, 1)
        A = np.log(np.maximum(xm, 1e-9)) - lm
        A = np.maximum(A, 1e-6)
        alpha = (1 + np.sqrt(1 + 4 * A / 3)) / (4 * A)
        beta = xm / alpha
        G = special.gammainc(alpha[None, :], np.maximum(x, 0) / np.maximum(beta[None, :], 1e-9))
        H = q[None, :] + (1 - q[None, :]) * G
        z = np.clip(stats.norm.ppf(np.clip(H, 1e-6, 1 - 1e-6)), -3.09, 3.09)
        z = np.where(ok & (npos >= 15)[None, :], z, np.nan)
        if min_mean_mm is not None:
            mean_cum = np.where(ok, x, 0).sum(axis=0) / np.maximum(nok, 1)
            z = np.where((mean_cum >= min_mean_mm)[None, :], z, np.nan)
        out[idx] = z
    return out


def glo_lmoments(x):
    """Loi logistique généralisée (Hosking 1986), forme à 3 paramètres de la log-logistique utilisée par le paquet SPEI
    (Beguería et al. 2014) : accepte une asymétrie des deux signes. Paramètres (xi, alpha, k) par L-moments (estimateurs
    non biaisés des moments pondérés). x : échantillon 1-D sans NaN ; NaN si moins de 10 valeurs ou dispersion nulle."""
    x = np.sort(np.asarray(x, float))
    N = len(x)
    if N < 10:
        return np.nan, np.nan, np.nan
    i = np.arange(1, N + 1)
    b0 = x.mean()
    b1 = np.sum((i - 1) / (N - 1) * x) / N
    b2 = np.sum((i - 1) * (i - 2) / ((N - 1) * (N - 2)) * x) / N
    l1, l2, l3 = b0, 2 * b1 - b0, 6 * b2 - 6 * b1 + b0
    if l2 <= 0:
        return np.nan, np.nan, np.nan
    k = -l3 / l2
    if abs(k) < 1e-6:
        return l1, l2, 0.0
    alpha = l2 * np.sin(k * np.pi) / (k * np.pi)
    return l1 - alpha * (1 / k - np.pi / np.sin(k * np.pi)), alpha, k


def glo_cdf(x, xi, alpha, k):
    if k == 0:
        y = (x - xi) / alpha
    else:
        arg = 1 - k * (x - xi) / alpha
        with np.errstate(divide="ignore", invalid="ignore"):
            y = np.where(arg > 0, -np.log(np.maximum(arg, 1e-300)) / k, np.inf if k > 0 else -np.inf)
    return 1.0 / (1.0 + np.exp(-np.clip(y, -700, 700)))


def spei(P, PET, n, month0):
    """Indice standardisé de précipitation-évapotranspiration SPEI-n (Vicente-Serrano et al. 2010). P, PET (T, N) en mm/mois,
    le pas 0 étant le mois `month0`. Bilan P - PET cumulé sur n mois, loi log-logistique (forme logistique généralisée de
    Hosking, comme le paquet SPEI) par mois du calendrier (L-moments),
    SPEI = Phi^-1(F), borné à +-3,09. NaN pour les n-1 premiers pas et si moins de 20 cumuls valides."""
    from scipy import stats
    D = rolling_sum(np.asarray(P, float) - np.asarray(PET, float), n)
    D[: n - 1] = np.nan
    bad = ~(np.isfinite(P) & np.isfinite(PET))
    if n > 1:
        bad = rolling_sum(bad.astype(float), n) > 0
    D[bad] = np.nan
    T = D.shape[0]
    out = np.full(D.shape, np.nan)
    cal = np.array([(month0 - 1 + t) % 12 for t in range(T)])
    for m in range(12):
        idx = np.where(cal == m)[0]
        for j in range(D.shape[1]):
            x = D[idx, j]
            ok = np.isfinite(x)
            if ok.sum() < 20:
                continue
            xi, al, k = glo_lmoments(x[ok])
            if not np.isfinite(xi):
                continue
            F = glo_cdf(x[ok], xi, al, k)
            z = np.full(len(x), np.nan)
            z[ok] = np.clip(stats.norm.ppf(np.clip(F, 1e-6, 1 - 1e-6)), -3.09, 3.09)
            out[idx, j] = z
    return out


def et0_pm_monthly(t2m_k, d2m_k, u10, v10, ssrd_j_day, sp_pa, lat_deg, year, month):
    """ET0 de référence (mm/mois), Penman-Monteith FAO-56 (Allen et al. 1998) à partir de moyennes mensuelles ERA5-Land.
    Simplifications documentées : température moyenne (Tmax/Tmin journaliers absents), flux de chaleur du sol nul,
    Rso = 0,75 Ra (altitude non utilisée), vent à 2 m = 0,748 x vent à 10 m (FAO-56 éq. 47)."""
    import calendar
    T = t2m_k - 273.15
    es = 0.6108 * np.exp(17.27 * T / (T + 237.3))
    Td = d2m_k - 273.15
    ea = np.minimum(0.6108 * np.exp(17.27 * Td / (Td + 237.3)), es)
    delta = 4098 * es / (T + 237.3) ** 2
    gam = 0.000665 * sp_pa / 1000.0
    u2 = np.hypot(u10, v10) * 0.748
    Rs = ssrd_j_day / 1e6
    J = (np.datetime64(f"{year}-{month:02d}-15") - np.datetime64(f"{year}-01-01")).astype(int) + 1
    phi = np.deg2rad(lat_deg)
    dr = 1 + 0.033 * np.cos(2 * np.pi * J / 365)
    dec = 0.409 * np.sin(2 * np.pi * J / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(dec), -1, 1))
    Ra = 24 * 60 / np.pi * 0.0820 * dr * (ws * np.sin(phi) * np.sin(dec) + np.cos(phi) * np.cos(dec) * np.sin(ws))
    Rso = 0.75 * Ra
    Rnl = 4.903e-9 * (T + 273.16) ** 4 * (0.34 - 0.14 * np.sqrt(ea)) * (1.35 * np.clip(Rs / np.maximum(Rso, 1e-6), 0.3, 1.0) - 0.35)
    Rn = 0.77 * Rs - Rnl
    et0 = (0.408 * delta * Rn + gam * 900 / (T + 273) * u2 * (es - ea)) / (delta + gam * (1 + 0.34 * u2))
    return np.maximum(et0, 0) * calendar.monthrange(year, month)[1]
