"""Inondation pluviale / crue éclair : deux indicateurs fondés sur la pluie, validés sur le périmètre pilote.

Cahier des charges §7.A (cumuls de pluie, seuils locaux, pluies susceptibles de saturer les sols), §7.B (sol, couverture,
humidité antérieure), §8 (approche 1), §13 (détection, fausses alertes, sensibilité, validation partielle).
Pourquoi : le modèle de rivière (GloFAS, ~5 km) manque l'inondation urbaine d'Antananarivo (Ana 2022 : validate_floods.py).

Indicateur « pluie » : cumul CHIRPS sur 3 jours glissants, par fokontany, comparé au maximum saisonnier sur 3 jours de retour
2 ans (médiane, vigilance) et 5 ans (80e centile, alerte) de CE fokontany sur 2006-2020 (rx3_annual.npz, build_rx3_clim.py).
Indicateur « ruissellement » (proposé par le porteur du projet : en ville l'infiltration est faible mais pas nulle) :
  lame ruisselée SCS-CN (NRCS NEH-4) de la pluie sur 3 jours, avec le CN du fokontany (occupation du sol WorldCover et groupe
  hydrologique du sol, build_soilwater.py : ~92 en ville, 79-88 autour) ajusté selon la pluie des 5 jours précédents
  (règle NRCS, saison de croissance : < 36 mm sol sec, CN I ; > 53 mm sol humide, CN III ; sinon CN II).
  Seuil UNIQUE pour tout le périmètre : ruissellement de retour 2 ans / 5 ans de la zone (médiane / 80e centile du ruissellement
  des maxima saisonniers de tous les fokontany, en condition II). Un seuil local annulerait l'effet du CN (à CN fixe, le
  ruissellement croît avec la pluie : mêmes dépassements que l'indicateur « pluie ») ; un seuil commun fait dépasser plus
  souvent les zones peu perméables, pour une même pluie.
Validation, pour les deux indicateurs : mêmes événements, épisodes, critères et sensibilité que validate_floods.py ; communes
inondées selon Copernicus EMS (AUC).
Limites : CHIRPS (~5 km, journalier) ne voit ni l'intensité horaire ni le drainage, les digues ou le pompage ; seuils sur
15 saisons, dont 2015-2020 servent aussi au test ; CN tabulés (non calés localement).
Cache : data/<pays>/grids/chirps_daily_pilot.npz. Sorties : validation/crues_pluviales_validation.md, validation/crues_pluviales_episodes.csv.
Usage : python scripts/validate_pluvial.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import re

import numpy as np
import pandas as pd

import soilwater_core as C
from common import country_data_dir, grid_dir, load_config, read_units
from validate_floods import FIRST_SEASON, SHARE, SHARES, VAL, auc, episodes, ev_window, matches

AMC_DRY, AMC_WET = 35.6, 53.3          # pluie des 5 jours précédents (mm), saison de croissance (NRCS NEH-4, tableau 4-2)
INDICATORS = {"pluie": "Pluie sur 3 jours (seuil local)", "ruissellement": "Ruissellement SCS-CN (seuil commun au périmètre)"}


def chirps_days(days, lons, lats, bbox):
    from chirps_daily import leaf_series
    v, _ = leaf_series(days, bbox, lons, lats, workers=10)
    return v


def local_levels(rx3: np.ndarray):
    """rx3 (saisons, fokontany) -> (niveau 2 ans = médiane, niveau 5 ans = 80e centile) des maxima saisonniers sur 3 jours."""
    return np.nanmedian(rx3, axis=0), np.nanpercentile(rx3, 80, axis=0)


def runoff_levels(rx3: np.ndarray, cn2: np.ndarray):
    """Seuils communs : médiane et 80e centile du ruissellement (condition II) des maxima saisonniers de tous les fokontany."""
    q = C.scs_runoff(rx3, cn2[None, :])
    return float(np.nanmedian(q)), float(np.nanpercentile(q, 80))


def amc_cn(cn2: np.ndarray, p5: np.ndarray) -> np.ndarray:
    """CN ajusté selon la pluie des 5 jours précédents (NRCS) ; p5 (T, N)."""
    return np.where(p5 < AMC_DRY, C.cn_dry(cn2)[None, :], np.where(p5 > AMC_WET, C.cn_wet(cn2)[None, :], cn2[None, :]))


def roll(D: np.ndarray, days: list[dt.date], lags) -> np.ndarray:
    """Somme de la pluie des jours décalés de `lags` (0 = le jour même) ; NaN si l'un manque."""
    pos = {d: i for i, d in enumerate(days)}
    out = np.full(D.shape, np.nan, dtype="float64")
    for i, d in enumerate(days):
        idx = [pos.get(d - dt.timedelta(days=k)) for k in lags]
        if all(j is not None for j in idx):
            out[i] = D[idx].sum(axis=0)
    return out


class DailyCache:
    """Pluie journalière (jours, fokontany du périmètre) ; ne télécharge que les jours manquants, sauvegarde par paquets."""

    def __init__(self, path, codes, fetch, lons, lats, bbox):
        self.path, self.codes, self.fetch, self.lons, self.lats, self.bbox = path, list(codes), fetch, lons, lats, bbox
        self.d = {}
        if path is not None and path.exists():
            z = np.load(path, allow_pickle=False)
            if list(z["codes"]) == self.codes:
                self.d = {dt.date.fromisoformat(s): row for s, row in zip(z["days"], z["rain"].astype("float32"))}

    def save(self):
        if self.path is None or not self.d:
            return
        ks = sorted(self.d)
        np.savez_compressed(self.path, days=np.array([k.isoformat() for k in ks]), codes=np.array(self.codes),
                            rain=np.stack([self.d[k] for k in ks]).astype("float16"))

    def get(self, days: list[dt.date], chunk=60):
        todo = [d for d in days if d not in self.d]
        for i in range(0, len(todo), chunk):
            part = todo[i:i + chunk]
            v = self.fetch(part, self.lons, self.lats, self.bbox)
            for d, row in zip(part, v):
                if np.isfinite(row).any():                         # jour absent du serveur : non mis en cache, réessayé plus tard
                    self.d[d] = row
            self.save()
            print(f"  pluie journalière : {len(self.d)} jours en cache", flush=True)
        ok = [d for d in days if d in self.d]
        return ok, (np.stack([self.d[d] for d in ok]).astype("float64") if ok else np.zeros((0, len(self.codes))))


def span(a: str, b: str):
    a, b = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
    return [a + dt.timedelta(days=i) for i in range((b - a).days + 1)]


def main(country="mdg", fetch=chirps_days, rx3=None, cn2=None, today=None, events=None, gdacs=None, cache_path=None,
         first_season=FIRST_SEASON):
    today = today or dt.date.today()
    cfg = load_config(country)
    units = read_units(country)
    th = pd.read_csv(country_data_dir(country) / "flood_thresholds.csv", dtype={"pcode": str})
    th = th[np.isfinite(th.q2)].reset_index(drop=True)
    leaves_all = units[units.level == 4].reset_index(drop=True)
    sel = leaves_all.adm3.isin(set(th.pcode)).to_numpy()
    leaves = leaves_all[sel].reset_index(drop=True)
    if rx3 is None:
        z = np.load(grid_dir(country) / "rx3_annual.npz", allow_pickle=True)
        if list(z["codes"]) != list(leaves_all.pcode):
            raise SystemExit("rx3_annual.npz ne correspond pas aux fokontany actuels : relancer build_rx3_clim.py")
        rx3 = z["rx3"][:, sel]
    if cn2 is None:
        sw = pd.read_csv(country_data_dir(country) / "external" / "soilwater.csv", dtype={"pcode": str})
        cn_map = sw[sw.indicateur == "cn2"].set_index("pcode").valeur
        cn2 = leaves.pcode.map(cn_map).to_numpy(dtype="float64")
    cn2 = np.asarray(cn2, dtype="float64")
    n_cn_missing = int((~np.isfinite(cn2)).sum())
    cn2 = np.where(np.isfinite(cn2), cn2, np.nanmedian(cn2))         # fokontany sans CN : médiane du périmètre (signalé)
    L2, L5 = local_levels(rx3)
    Q2, Q5 = runoff_levels(rx3, cn2)
    names, adm1 = dict(zip(units.pcode, units.name)), dict(zip(units.pcode, units.adm1))
    regions = sorted({adm1[p] for p in th.pcode if adm1.get(p)})
    reg_names = [names.get(r, r) for r in regions] + (["Antananarivo"] if "MG11" in regions else [])
    all_ev = events if events is not None else pd.read_csv(VAL / "evenements.csv", dtype=str)
    ev = all_ev[all_ev.zones_citees.fillna("").str.contains("|".join(map(re.escape, reg_names)))]
    other = all_ev[(all_ev.type != "secheresse") & ~all_ev.id.isin(ev.id)]
    if gdacs is None and events is None and (VAL / "evenements_gdacs.csv").exists():
        gdacs = pd.read_csv(VAL / "evenements_gdacs.csv", dtype=str)
    cache = DailyCache(cache_path if cache_path is not None else grid_dir(country) / "chirps_daily_pilot.npz", leaves.pcode,
                       fetch, leaves.lon.to_numpy(), leaves.lat.to_numpy(), cfg["map"]["bbox"])

    def window(a, b):
        """Pour chaque jour de [a, b] : rapport aux seuils (vigilance, alerte) des deux indicateurs, par fokontany.
        7 jours de plus avant a : 2 pour le cumul sur 3 jours, 5 pour l'humidité antérieure."""
        a7 = (dt.date.fromisoformat(a) - dt.timedelta(days=7)).isoformat()
        days, D = cache.get(span(a7, b))
        if len(days) == 0:
            return None
        P3, P5 = roll(D, days, (0, 1, 2)), roll(D, days, (3, 4, 5, 6, 7))
        Q = C.scs_runoff(P3, amc_cn(cn2, np.nan_to_num(P5, nan=0.0)))
        Q = np.where(np.isfinite(P3), Q, np.nan)
        keep = [i for i, d in enumerate(days) if d >= dt.date.fromisoformat(a)]
        days = [days[i] for i in keep]
        return {"days": days, "pluie": (P3[keep] / L2, P3[keep] / L5, P3[keep]), "ruissellement": (Q[keep] / Q2, Q[keep] / Q5, Q[keep])}

    def share(r):
        ok = np.isfinite(r)
        return np.where(ok.any(axis=1), np.nansum(r >= 1, axis=1) / np.maximum(ok.sum(axis=1), 1), np.nan)

    ev_w = []
    for _, e in ev.iterrows():
        w = window(*ev_window(e.date_debut, e.date_fin))
        if w is not None:
            ev_w.append((e, w))
    last = today.year if today.month >= 5 else today.year - 1
    seasons = [w for w in (window(f"{y}-11-01", f"{y + 1}-04-30") for y in range(first_season, last)) if w is not None]
    ems_w = []
    oof = VAL / "ems_communes_oof.csv"
    if oof.exists() and events is None:
        from validate_fokontany import EVENTS
        o = pd.read_csv(oof, dtype={"adm3": str})
        ref = all_ev.set_index("id")
        for ev_id, (nm, yr) in EVENTS.items():
            eid = f"{nm.lower()}-{yr}"
            sub = o[(o.evenement == ev_id) & o.adm3.isin(set(leaves.adm3))]
            if eid in ref.index and len(sub) >= 5:
                w = window(*ev_window(ref.loc[eid, "date_debut"], ref.loc[eid, "date_fin"]))
                if w is not None:
                    ems_w.append((ev_id, nm, sub, w))

    out = {}
    for ind in INDICATORS:
        det = []
        for e, w in ev_w:
            r2, r5, v = w[ind]
            f2, f5 = share(r2), share(r5)
            det.append({"evenement": e.id, "debut": e.date_debut, "fin": e.date_fin, "part_2ans": round(float(np.nanmax(f2)), 3),
                        "part_5ans": round(float(np.nanmax(f5)), 3), "valeur_max_mm": round(float(np.nanmax(v)), 1),
                        "rapport_max_2ans": round(float(np.nanmax(r2)), 2),
                        "detecte_vigilance": bool(np.nanmax(f2) >= SHARE), "detecte_alerte": bool(np.nanmax(f5) >= SHARE)})
        det = pd.DataFrame(det, columns=["evenement", "debut", "fin", "part_2ans", "part_5ans", "valeur_max_mm", "rapport_max_2ans",
                                         "detecte_vigilance", "detecte_alerte"])

        def episode_table(sh):
            rows = []
            for w in seasons:
                for s, t_end, m in episodes([d.isoformat() for d in w["days"]], np.nan_to_num(share(w[ind][0])), sh):
                    rows.append({"debut": s, "fin": t_end, "part_max": round(m, 3), "evenement_perimetre": ";".join(matches(s, t_end, ev)),
                                 "evenement_ailleurs": ";".join(matches(s, t_end, other)), "evenement_gdacs": ";".join(matches(s, t_end, gdacs))})
            return pd.DataFrame(rows, columns=["debut", "fin", "part_max", "evenement_perimetre", "evenement_ailleurs", "evenement_gdacs"])
        epi = episode_table(SHARE)
        sens = []
        for label, sh in SHARES:
            e = episode_table(sh)
            none = int(((e.evenement_perimetre == "") & (e.evenement_ailleurs == "") & (e.evenement_gdacs == "")).sum()) if len(e) else 0
            sens.append({"seuil": label, "detectes": int((det.part_2ans >= sh).sum()) if len(det) else 0, "evenements": len(det), "episodes": len(e),
                         "episodes_perimetre": int((e.evenement_perimetre != "").sum()) if len(e) else 0, "episodes_sans_correspondance": none})
        ems = []
        for ev_id, nm, sub, w in ems_w:
            ratio = pd.Series(np.nanmax(w[ind][0], axis=0), index=leaves.adm3).groupby(level=0).max()
            pos = [ratio[p] for p, v in zip(sub.adm3, sub.pos) if str(v) == "True"]
            neg = [ratio[p] for p, v in zip(sub.adm3, sub.pos) if str(v) != "True"]
            ems.append({"evenement": ev_id, "nom": nm, "communes": len(sub), "inondees": len(pos), "non_inondees": len(neg),
                        "auc": round(auc(pos, neg), 3) if pos and neg else None,
                        "pod_2ans": round(float(np.mean(np.array(pos) >= 1)), 3) if pos else None,
                        "fausses_2ans": round(float(np.mean(np.array(neg) >= 1)), 3) if neg else None})
        out[ind] = {"detection": det, "episodes": epi.assign(indicateur=ind), "sensitivity": pd.DataFrame(sens), "ems": pd.DataFrame(ems)}
    res = {"n_fokontany": len(leaves), "n_communes": int(leaves.adm3.nunique()), "n_seasons_clim": rx3.shape[0], "seasons": len(seasons),
           "first_season": first_season, "regions": reg_names, "n_events": len(ev), "ind": out, "Q2": Q2, "Q5": Q5,
           "cn_median": float(np.median(cn2)), "cn_range": (float(np.min(cn2)), float(np.max(cn2))), "n_cn_missing": n_cn_missing}
    if country != "demo":
        pd.concat([out[k]["episodes"] for k in out]).to_csv(VAL / "crues_pluviales_episodes.csv", index=False)
        write_md(VAL / "crues_pluviales_validation.md", res)
    for k, o in out.items():
        print(f"Pluvial [{k}] : {len(leaves)} fokontany ; événements {int(o['detection'].detecte_vigilance.sum()) if len(o['detection']) else 0}"
              f"/{len(o['detection'])} détectés ; {len(seasons)} saisons, {len(o['episodes'])} épisodes ; AUC EMS "
              f"{o['ems'].auc.tolist() if len(o['ems']) else '—'}", flush=True)
    return res


def write_md(path, res):
    def f(v, n=2):
        return "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{n}f}".replace(".", ",")
    L = ["# Inondation pluviale : deux indicateurs fondés sur la pluie, validés sur le périmètre pilote", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/validate_pluvial.py`. Cahier des charges §7.A, §7.B, §8, §13. "
         "À comparer avec le modèle de rivière : `crues_validation.md`.", "",
         f"**Périmètre** : {res['n_fokontany']} fokontany de {res['n_communes']} communes ({', '.join(res['regions'])}). "
         f"Pluie CHIRPS journalière, {res['seasons']} saisons de test (novembre {res['first_season']} à avril {res['first_season'] + res['seasons']}).", "",
         "**Indicateurs**",
         f"- **Pluie** : cumul sur 3 jours, comparé au maximum saisonnier de retour 2 ans (vigilance) et 5 ans (alerte) du fokontany ({res['n_seasons_clim']} saisons, 2006-2020).",
         "- **Ruissellement** (idée du porteur du projet : infiltration urbaine faible mais non nulle) : lame ruisselée SCS-CN du cumul sur 3 jours.",
         f"  - CN de l'occupation du sol et du sol : médiane {f(res['cn_median'], 1)}, de {f(res['cn_range'][0], 1)} à {f(res['cn_range'][1], 1)}. En ville, il vaut environ 92, soit une infiltration faible mais non nulle.",
         "  - CN ajusté selon la pluie des 5 jours précédents (sol sec ou humide, règle NRCS).",
         f"  - Fokontany sans CN calculé : {res['n_cn_missing']} (médiane du périmètre utilisée à la place).",
         f"  - Seuils communs au périmètre : {f(res['Q2'], 1)} mm (retour 2 ans), {f(res['Q5'], 1)} mm (retour 5 ans).",
         "",
         "**Limites** : pas d'intensité horaire ; drainage, digues et pompage non représentés ; CN tabulés, non calés ; "
         "les saisons 2015-2020 servent aussi aux seuils. La validation est **partielle**.", "",
         "## Comparaison des deux indicateurs (seuil : 10 % des fokontany)", "",
         "| Indicateur | Inondations documentées détectées | Épisodes simulés | Dont événement du périmètre | Sans aucune correspondance | AUC communes inondées (EMS) |",
         "|---|---|---|---|---|---|"]
    for k, lab in INDICATORS.items():
        o = res["ind"][k]
        s = o["sensitivity"][o["sensitivity"].seuil == "10 %"].iloc[0] if len(o["sensitivity"]) else None
        a = o["ems"].auc.tolist() if len(o["ems"]) else []
        L.append(f"| {lab} | {s.detectes if s is not None else 0} / {s.evenements if s is not None else 0} | {s.episodes if s is not None else 0} | "
                 f"{s.episodes_perimetre if s is not None else 0} | {s.episodes_sans_correspondance if s is not None else 0} | {', '.join(f(x) for x in a) or '—'} |")
    L += ["", "Pour le modèle de rivière (GloFAS) au même seuil : voir `crues_validation.md`."]
    for k, lab in INDICATORS.items():
        o = res["ind"][k]
        det, epi, sens, ems = o["detection"], o["episodes"], o["sensitivity"], o["ems"]
        L += ["", f"## {lab}", "", "### Inondations documentées", "",
              "| Événement | Dates | Fokontany ≥ 2 ans | Fokontany ≥ 5 ans | Valeur max (mm) | Max / seuil 2 ans | Vigilance | Alerte |",
              "|---|---|---|---|---|---|---|---|"]
        for _, r in det.iterrows():
            L.append(f"| {r.evenement} | {r.debut} → {r.fin} | {round(100 * r.part_2ans)} % | {round(100 * r.part_5ans)} % | {f(r.valeur_max_mm, 0)} | "
                     f"{f(r.rapport_max_2ans)} | {'oui' if r.detecte_vigilance else '**non**'} | {'oui' if r.detecte_alerte else 'non'} |")
        L += ["", "### Sensibilité au seuil", "",
              "| Seuil (part des fokontany) | Événements détectés | Épisodes | Dont événement du périmètre | Sans aucune correspondance |", "|---|---|---|---|---|"]
        for _, s in sens.iterrows():
            L.append(f"| {s.seuil} | {s.detectes} / {s.evenements} | {s.episodes} | {s.episodes_perimetre} | {s.episodes_sans_correspondance} |")
        L += ["", "### Épisodes (seuil de 10 %)", "", "| Début | Fin | Part max | Événement (périmètre) | Événement (ailleurs) | GDACS |", "|---|---|---|---|---|---|"]
        for _, r in epi.iterrows():
            L.append(f"| {r.debut} | {r.fin} | {round(100 * r.part_max)} % | {r.evenement_perimetre or '—'} | {r.evenement_ailleurs or '—'} | {r.evenement_gdacs or '—'} |")
        if len(ems):
            L += ["", "### Communes inondées selon le satellite (Copernicus EMS)", "",
                  "| Activation | Communes | Inondées | Non inondées | AUC | Inondées ≥ seuil 2 ans | Non inondées ≥ seuil 2 ans |", "|---|---|---|---|---|---|---|"]
            for _, r in ems.iterrows():
                L.append(f"| {r.evenement} ({r.nom}) | {r.communes} | {r.inondees} | {r.non_inondees} | {f(r.auc)} | "
                         f"{'—' if r.pod_2ans is None else str(round(100 * r.pod_2ans)) + ' %'} | {'—' if r.fausses_2ans is None else str(round(100 * r.fausses_2ans)) + ' %'} |")
    L += ["", "**Données qui amélioreraient les indicateurs :** pluie horaire (GPM IMERG, compte NASA Earthdata ; pluviographes de Météo Madagascar), "
          "inventaire BNGRC des inondations urbaines, réseau de drainage et zones de pompage d'Antananarivo, CN calés sur des mesures."]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    main(ap.parse_args().country)
