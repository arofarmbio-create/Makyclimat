"""Puits à sec et recharge : test secondaire des recharges figées T2, T2L et T2K
(validation/protocole_puits_a_sec.md, fixé avant le calcul le 09/11/2026).

Cas : points signalés à sec (UNESCO IHP-WINS 2025, CC BY-SA), cause « well is dry » ou « débit insuffisant », sans panne
mécanique, entretien, panne irréparable ni mauvaise gestion ; sensibilité : tous les points « Dry = Yes ».
Référence : forages BushProof (Al-Zoubaidy et al. 2023), sauf ceux à moins de 200 m d'un cas. Emprise : rectangle des
forages BushProof. Recharge : maille la plus proche des cartes figées (empreintes vérifiées). AUC de « recharge faible »,
intervalle à 95 % par rééchantillonnage de blocs de 20 km (2 000 tirages, graine 20261109).
H-P1 : T2L ou T2K a une AUC supérieure d'au moins 0,05 à celle de T2, intervalle de la différence sans 0.
Données brutes hors dépôt ; seules des valeurs agrégées sont publiées. Seules les coordonnées des forages BushProof sont
lues (le chlorure reste sous scellés, protocole du bilan de chlorure).
Sorties : validation/puits_a_sec.md. Usage : python scripts/puits_a_sec.py
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import re

import numpy as np
import pandas as pd

from common import ROOT

SEED, N_BOOT, BLOC_KM, EXCL_M, GAIN = 20261109, 2000, 20.0, 200.0, 0.05
OK_CAUSE = "dry|débit insuffisant"
EXCLU = "mechanical|maintenance|irr|gestion"


def auc(score_cas, score_ref) -> float:
    """AUC de Mann-Whitney : probabilité qu'un cas ait un score plus élevé qu'une référence (ex aequo = 1/2)."""
    a, b = np.asarray(score_cas, float), np.asarray(score_ref, float)
    if len(a) == 0 or len(b) == 0:
        return float("nan")
    r = pd.Series(np.r_[a, b]).rank().to_numpy()
    return float((r[:len(a)].sum() - len(a) * (len(a) + 1) / 2) / (len(a) * len(b)))


def selection(u: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    iss = u["Functionality issues"].fillna("").str.lower()
    dry = u["Dry"].astype(str).eq("Yes")
    principal = dry & iss.str.contains(OK_CAUSE) & ~iss.str.contains(EXCLU)
    return principal, dry


def blocs(lat, lon, km: float = BLOC_KM) -> np.ndarray:
    lat, lon = np.asarray(lat, float), np.asarray(lon, float)
    dy = km / 111.0
    dx = km / (111.0 * np.cos(np.radians(np.nanmean(lat))))
    return np.floor(lat / dy).astype(int) * 100000 + np.floor(lon / dx).astype(int)


def bootstrap(cas: pd.DataFrame, ref: pd.DataFrame, cols: list[str], n=N_BOOT, seed=SEED) -> dict:
    """AUC de chaque recharge (score = −recharge) et intervalles à 95 % par tirage de blocs avec remise."""
    rng = np.random.default_rng(seed)
    allp = pd.concat([cas.assign(y=1), ref.assign(y=0)], ignore_index=True)
    allp["bloc"] = blocs(allp.lat, allp.lon)
    groups = {k: g.index.to_numpy() for k, g in allp.groupby("bloc")}
    keys = np.array(list(groups))
    res = {c: [] for c in cols}
    for _ in range(n):
        idx = np.concatenate([groups[k] for k in rng.choice(keys, len(keys), replace=True)])
        s = allp.loc[idx]
        for c in cols:
            res[c].append(auc(-s.loc[s.y == 1, c], -s.loc[s.y == 0, c]))
    return {c: np.array(v) for c, v in res.items()}


def nearest(lat, lon, plat, plon) -> np.ndarray:
    from sklearn.neighbors import BallTree
    return BallTree(np.radians(np.c_[plat, plon]), metric="haversine").query(
        np.radians(np.c_[np.asarray(lat), np.asarray(lon)]), k=1, return_distance=False)[:, 0]


def empreinte_attendue(rapport: str) -> str:
    m = re.search(r"SHA-256 `([0-9a-f]{64})`", (ROOT / "validation" / rapport).read_text(encoding="utf-8"))
    return m.group(1) if m else ""


def main() -> None:
    from sklearn.neighbors import BallTree
    hd = ROOT / "inputs" / "hydrogeologie"
    cartes = {}
    for f, rap in (("recharge_t2l.csv", "recharge_locale.md"), ("recharge_t2k.csv", "recharge_karst.md")):
        sha = hashlib.sha256((hd / f).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        cartes[f] = (sha, empreinte_attendue(rap), sha == empreinte_attendue(rap))
    t2l, t2k = pd.read_csv(hd / "recharge_t2l.csv"), pd.read_csv(hd / "recharge_t2k.csv")

    fs = glob.glob(str(ROOT / "data" / "mdg" / "bushproof_raw" / "recuperation" / "*Forages*.csv"))
    ref = pd.concat([pd.read_csv(f, usecols=["Lat_DD", "Long_DD"]) for f in fs]).apply(pd.to_numeric, errors="coerce").dropna()
    ref = ref.round(5).drop_duplicates().rename(columns={"Lat_DD": "lat", "Long_DD": "lon"}).reset_index(drop=True)
    u = pd.read_csv(ROOT / "data" / "mdg" / "unesco_puits_raw" / "madagascar_wells_full_english_converted.csv")
    box = u.latitude.between(ref.lat.min(), ref.lat.max()) & u.longitude.between(ref.lon.min(), ref.lon.max())
    principal, dry = selection(u)

    out = {}
    for nom, sel in (("principal", principal & box), ("sensibilité (tous « Dry = Yes »)", dry & box)):
        cas = u.loc[sel, ["latitude", "longitude"]].rename(columns={"latitude": "lat", "longitude": "lon"}).reset_index(drop=True)
        d, _ = BallTree(np.radians(cas[["lat", "lon"]].to_numpy()), metric="haversine").query(np.radians(ref[["lat", "lon"]].to_numpy()), k=1)
        r = ref[d[:, 0] * 6371000 >= EXCL_M].reset_index(drop=True)
        for df in (cas, r):
            j = nearest(df.lat, df.lon, t2l.lat, t2l.lon)
            df["T2"], df["T2L"] = t2l.T2_mmpa.to_numpy()[j], t2l.T2L_mmpa.to_numpy()[j]
            df["T2K"] = t2k.T2K_mmpa.to_numpy()[nearest(df.lat, df.lon, t2k.lat, t2k.lon)]
            df["dom"] = t2l.domaine.to_numpy()[j]
        cols = ["T2", "T2L", "T2K"]
        a = {c: auc(-cas[c], -r[c]) for c in cols}
        bs = bootstrap(cas, r, cols)
        ci = {c: np.nanpercentile(bs[c], [2.5, 97.5]) for c in cols}
        dif = {c: (a[c] - a["T2"], np.nanpercentile(bs[c] - bs["T2"], [2.5, 97.5])) for c in ("T2L", "T2K")}
        h = {c: bool(dif[c][0] >= GAIN and dif[c][1][0] > 0) for c in dif}
        out[nom] = {"n_cas": len(cas), "n_ref": len(r), "auc": a, "ci": ci, "dif": dif, "h": h,
                    "dom_cas": float((cas.dom == "dans le domaine").mean()), "dom_ref": float((r.dom == "dans le domaine").mean()),
                    "med": {c: (float(cas[c].median()), float(r[c].median())) for c in cols},
                    "nblocs": int(len(np.unique(blocs(pd.concat([cas.lat, r.lat]), pd.concat([cas.lon, r.lon])))))}

    p = out["principal"]
    h_p1 = p["h"]["T2L"] or p["h"]["T2K"]
    L = ["# Puits à sec et recharge (test secondaire de T2, T2L et T2K)", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/puits_a_sec.py`, selon `validation/protocole_puits_a_sec.md` "
         "(fixé avant le calcul). Cas : Kaltsas, UNESCO IHP-WINS 2025 (doi:10.63253/r2yrjane, CC BY-SA). Référence : forages de "
         "Al-Zoubaidy, Monteleone et Bünzli 2023 (BushProof / DDC), coordonnées seulement. Calcul local, données brutes hors dépôt.", "",
         "## Cartes figées utilisées", "", "| Carte | Empreinte recalculée | Conforme à l'empreinte publiée |", "|---|---|---|"]
    for f, (sha, att, okk) in cartes.items():
        L.append(f"| `{f}` | `{sha[:12]}…` | {'oui' if okk else 'NON (attendu ' + att[:12] + '…)'} |")
    for nom, o in out.items():
        L += ["", f"## Sélection : {nom}", "",
              f"{o['n_cas']} puits à sec et {o['n_ref']} forages de référence dans l'emprise BushProof ({o['nblocs']} blocs de 20 km). "
              f"Part dans le domaine de T2L : cas {o['dom_cas']:.0%}, référence {o['dom_ref']:.0%}.", "",
              "| Recharge | Médiane cas (mm/an) | Médiane référence | AUC (recharge faible) | Intervalle à 95 % |", "|---|---|---|---|---|"]
        for c in ("T2", "T2L", "T2K"):
            L.append(f"| {c} | {o['med'][c][0]:.0f} | {o['med'][c][1]:.0f} | {o['auc'][c]:.3f} | {o['ci'][c][0]:.3f} à {o['ci'][c][1]:.3f} |")
        L += ["", "| Comparaison | Différence d'AUC | Intervalle à 95 % | Gain exigé (≥ 0,05, intervalle sans 0) |", "|---|---|---|---|"]
        for c in ("T2L", "T2K"):
            d0, ic = o["dif"][c]
            L.append(f"| {c} − T2 | {d0:+.3f} | {ic[0]:+.3f} à {ic[1]:+.3f} | {'atteint' if o['h'][c] else 'non atteint'} |")
    L += ["", f"**H-P1 {'soutenue' if h_p1 else 'non soutenue'}** (sélection principale ; règle fixée avant le calcul).", "",
          "Usage (protocole, section 6) : ce test appuie ou affaiblit le verdict du bilan de chlorure (en pause), sans décider seul.", "",
          "Limites : seuls les points signalés sont visibles ; un puits peut sécher pour d'autres raisons (profondeur, pompage, "
          "année sèche) ; 2024-2025 n'est pas une année moyenne ; zone ZH10 de BushProof absente ; recharge en mailles de 0,25 à "
          "0,5°, donc beaucoup d'ex aequo.", ""]
    (ROOT / "validation" / "puits_a_sec.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"H-P1 {h_p1} ; AUC T2 {p['auc']['T2']:.3f} T2L {p['auc']['T2L']:.3f} T2K {p['auc']['T2K']:.3f}")


if __name__ == "__main__":
    main()
