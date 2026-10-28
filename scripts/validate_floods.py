"""Validation du modèle de crue (GloFAS + seuils de Gumbel) sur le périmètre pilote, contre les inondations documentées.

Cahier des charges §7 (modèle hydrologique, calibration/validation sur observations), §13 (taux de détection, fausses
alertes, événements manqués, validation partielle déclarée). Périmètre : communes ayant un seuil de crue
(data/<pays>/flood_thresholds.csv ; pour Madagascar, bassin de l'Ikopa et de la Sisaony : Analamanga, Vakinankaratra).

Ce qui est validé : la chaîne « débit simulé GloFAS (réanalyse journalière, Open-Meteo) -> dépassement de la crue de
2 ans (vigilance) ou de 5 ans (alerte) ». Ce n'est PAS la prévision elle-même : les prévisions GloFAS archivées
(délai d'anticipation réel) demandent un compte Copernicus CDS ; la validation du délai reste à faire.
Vérité terrain, dans le dépôt :
  A. validation/evenements.csv : événements dont les zones citées nomment une région du périmètre ;
  B. validation/ems_communes_oof.csv : communes cartographiées inondées / non inondées par Copernicus EMS (satellite).
Mesures :
  1. détection par événement, sur toutes les mailles : part des communes au-dessus de q2 / q5 dans [début - 2 j, fin + 10 j] ;
  2. épisodes de dépassement, saisons de pluie 2015-2016 à aujourd'hui, sur les N_MAIN mailles de plus fort débit moyen
     (cours d'eau principaux) : un épisode = au moins 10 % de ces mailles au-dessus de q2. Ceux sans événement documenté
     sont des fausses alertes POSSIBLES (la liste ne contient presque que des cyclones) : taux = borne haute ;
  3. pour chaque activation EMS dont les dates sont sourcées : le débit simulé sépare-t-il les communes inondées des autres (AUC) ?
Quota : l'API gratuite compte une requête de N jours comme environ N/14 appels ; d'où des fenêtres courtes plutôt que
27 ans continus pour 136 mailles. Chaque fenêtre lue est mise en cache (data/<pays>/grids/glofas_windows.json) et un refus
de quota (HTTP 429) arrête proprement : relancer reprend là où on s'était arrêté.
Sorties : validation/crues_validation.md, validation/crues_episodes.csv.
Usage : python scripts/validate_floods.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import time

import numpy as np
import pandas as pd

import openmeteo as om
from common import DATA_DIR, country_data_dir, grid_dir, read_units

VAL = DATA_DIR.parent / "validation"
SHARE = 0.10                # épisode / détection : au moins 10 % des communes (ou mailles) au-dessus du seuil
GAP_DAYS = 5                # deux dépassements séparés de plus de 5 jours = deux épisodes
N_MAIN = 20                 # mailles des cours d'eau principaux pour les épisodes
FIRST_SEASON = 2015         # saisons de pluie de novembre 2015 à avril de l'année en cours


class QuotaError(RuntimeError):
    pass


def om_fetch(lat, lon, start, end):
    p = {"latitude": f"{lat:.4f}", "longitude": f"{lon:.4f}", "daily": "river_discharge", "start_date": start, "end_date": end}
    try:
        item = om.as_list(om.get_json(om.FLOOD_URL, p, retries=3, pause=10.0))[0]
    except (RuntimeError, ValueError) as e:
        raise QuotaError(str(e)) from e
    return item["daily"]["time"], [np.nan if v is None else float(v) for v in item["daily"]["river_discharge"]]


class Cache:
    """Débits par (maille, fenêtre), sauvegardés après chaque lecture."""

    def __init__(self, path, fetch, pause, budget_s=45 * 60):
        self.path, self.fetch, self.pause = path, fetch, pause
        self.d = json.loads(path.read_text(encoding="utf-8")) if path is not None and path.exists() else {}
        self.stopped = None
        self.deadline = time.time() + budget_s

    def get(self, cell, lat, lon, start, end):
        k = f"{cell}|{start}|{end}"
        if k not in self.d:
            if self.stopped:
                return None
            if time.time() > self.deadline:                        # arrêt propre avant la limite du job GitHub
                self.stopped = "durée maximale atteinte"
                print(f"::warning::Durée maximale atteinte ({len(self.d)} fenêtres en cache). Relancer pour reprendre.", flush=True)
                return None
            try:
                t, v = self.fetch(lat, lon, start, end)
            except QuotaError as e:
                self.stopped = str(e)
                print(f"::warning::Lecture des débits interrompue ({len(self.d)} fenêtres en cache) : {e}. Relancer pour reprendre.", flush=True)
                return None
            self.d[k] = {"t": t, "v": v}
            if self.path is not None:
                self.path.write_text(json.dumps(self.d), encoding="utf-8")
            time.sleep(self.pause)
        return self.d[k]


def cells_of(th: pd.DataFrame):
    """Mailles GloFAS dédoublonnées ; chacune est interrogée aux coordonnées de sa 1re commune (même sélection de maille que
    pour le calcul des seuils, update_floods.thresholds interrogeant le centroïde de la commune)."""
    t = th.assign(ck=[f"{a:.4f},{b:.4f}" for a, b in zip(th.cell_lat, th.cell_lon)])
    cells = t.drop_duplicates("ck").reset_index(drop=True)
    key = {k: i for i, k in enumerate(cells.ck)}
    return cells, np.array([key[k] for k in t.ck])


def window(cache, cells, start, end):
    """Débit (T, mailles) sur une fenêtre ; None si une maille manque (quota)."""
    cols, dates = [], None
    for _, c in cells.iterrows():
        r = cache.get(c.ck, c.lat, c.lon, start, end)
        if r is None:
            return None, None
        dates = dates or r["t"]
        cols.append(np.array(r["v"], dtype="float64"))
    return np.array(dates), np.stack(cols, axis=1)


def auc(pos, neg):
    """Aire sous la courbe ROC (Mann-Whitney) ; 0,5 = hasard."""
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    gt = (pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum()
    return float(gt / (len(pos) * len(neg)))


def episodes(dates, frac, share=SHARE, months=(11, 12, 1, 2, 3, 4)):
    """Regroupe les jours où frac >= share en épisodes ; retourne [(début, fin, part max), ...]."""
    d = pd.to_datetime(dates)
    on = (frac >= share) & np.isin(d.month, months)
    out, cur = [], None
    for t in np.where(on)[0]:
        if cur and (d[t] - d[cur[1]]).days <= GAP_DAYS:
            cur = (cur[0], t, max(cur[2], frac[t]))
        else:
            if cur:
                out.append(cur)
            cur = (t, t, frac[t])
    if cur:
        out.append(cur)
    return [(d[a].date(), d[b].date(), float(m)) for a, b, m in out]


def ev_window(a, b):
    return (pd.Timestamp(a) - pd.Timedelta(days=2)).date().isoformat(), (pd.Timestamp(b) + pd.Timedelta(days=10)).date().isoformat()


def matches(s, e, df):
    """Identifiants des événements de df dont la fenêtre [début - 2 j, fin + 10 j] recoupe l'épisode [s, e]."""
    if df is None or len(df) == 0:
        return []
    ok = (pd.Timestamp(s) <= pd.to_datetime(df.date_fin) + pd.Timedelta(days=10)) & \
         (pd.Timestamp(e) >= pd.to_datetime(df.date_debut) - pd.Timedelta(days=2))
    return df.id[ok].tolist()


# analyse de sensibilité au seuil de part des communes / mailles (arbitrage détection - fausses alertes, §13)
SHARES = [("au moins 1", 1e-9), ("5 %", 0.05), ("10 %", 0.10), ("25 %", 0.25)]


def main(country="mdg", fetch=om_fetch, today=None, events=None, pause=1.0, cache_path=None, first_season=FIRST_SEASON, gdacs=None):
    today = today or dt.date.today()
    th = pd.read_csv(country_data_dir(country) / "flood_thresholds.csv", dtype={"pcode": str})
    th = th[np.isfinite(th.q2) & np.isfinite(th.q5)].reset_index(drop=True)
    if "cell_lat" not in th:
        th["cell_lat"], th["cell_lon"] = th.lat, th.lon
    cells, idx = cells_of(th)
    q2, q5 = th.q2.to_numpy(), th.q5.to_numpy()
    cache = Cache(cache_path if cache_path is not None else grid_dir(country) / "glofas_windows.json", fetch, pause)
    units = read_units(country)
    names, adm1 = dict(zip(units.pcode, units.name)), dict(zip(units.pcode, units.adm1))
    regions = sorted({adm1[p] for p in th.pcode if adm1.get(p)})
    reg_names = [names.get(r, r) for r in regions] + (["Antananarivo"] if "MG11" in regions else [])
    all_ev = events if events is not None else pd.read_csv(VAL / "evenements.csv", dtype=str)
    ev = all_ev[all_ev.zones_citees.fillna("").str.contains("|".join(map(re.escape, reg_names)))]
    if gdacs is None and events is None and (VAL / "evenements_gdacs.csv").exists():
        gdacs = pd.read_csv(VAL / "evenements_gdacs.csv", dtype=str)       # événements indépendants de GloFAS (connector_gdacs_events.py)
    other = all_ev[(all_ev.type != "secheresse") & ~all_ev.id.isin(ev.id)]
    # 1. détection par événement documenté (toutes les mailles, fenêtre courte)
    det = []
    for _, e in ev.iterrows():
        a, b = ev_window(e.date_debut, e.date_fin)
        dates, Q = window(cache, cells, a, b)
        if Q is None:
            break
        q = Q[:, idx]
        f2, f5 = np.nanmean(q / q2 >= 1, axis=1), np.nanmean(q / q5 >= 1, axis=1)
        det.append({"evenement": e.id, "debut": e.date_debut, "fin": e.date_fin,
                    "part_communes_q2": round(float(f2.max()), 3), "part_communes_q5": round(float(f5.max()), 3),
                    "rapport_max_q2": round(float(np.nanmax(q / q2)), 2),
                    "detecte_vigilance": bool(f2.max() >= SHARE), "detecte_alerte": bool(f5.max() >= SHARE)})
    det = pd.DataFrame(det, columns=["evenement", "debut", "fin", "part_communes_q2", "part_communes_q5", "rapport_max_q2",
                                     "detecte_vigilance", "detecte_alerte"])
    # 2. épisodes sur les cours d'eau principaux, saisons de pluie FIRST_SEASON -> aujourd'hui
    main_cells = cells.assign(qm=cells.q_mean).sort_values("qm", ascending=False).head(N_MAIN).reset_index(drop=True)
    mq2 = main_cells.q2.to_numpy()
    seasons = []
    last = today.year if today.month >= 5 else today.year - 1
    for y in range(first_season, last):
        dates, Q = window(cache, main_cells, f"{y}-11-01", f"{y + 1}-04-30")
        if Q is None:
            break
        seasons.append((dates, np.nanmean(Q / mq2 >= 1, axis=1)))
    seasons_done = len(seasons)

    def episode_table(share):
        rows = []
        for dates, frac in seasons:
            for s, t_end, m in episodes(dates, frac, share):
                rows.append({"debut": s, "fin": t_end, "part_max_mailles_q2": round(m, 3),
                             "evenement_perimetre": ";".join(matches(s, t_end, ev)),
                             "evenement_ailleurs": ";".join(matches(s, t_end, other)),
                             "evenement_gdacs": ";".join(matches(s, t_end, gdacs))})
        return pd.DataFrame(rows, columns=["debut", "fin", "part_max_mailles_q2", "evenement_perimetre", "evenement_ailleurs", "evenement_gdacs"])
    epi = episode_table(SHARE)
    sens = []
    for label, sh in SHARES:
        e = episode_table(sh)
        none = ((e.evenement_perimetre == "") & (e.evenement_ailleurs == "") & (e.evenement_gdacs == "")).sum() if len(e) else 0
        sens.append({"seuil": label, "detectes": int((det.part_communes_q2 >= sh).sum()) if len(det) else 0, "evenements": len(det),
                     "episodes": len(e), "episodes_perimetre": int((e.evenement_perimetre != "").sum()) if len(e) else 0,
                     "episodes_sans_correspondance": int(none)})
    sens = pd.DataFrame(sens)
    # 3. activations EMS : communes inondées contre non inondées
    ems_rows = []
    oof = VAL / "ems_communes_oof.csv"
    if oof.exists() and not cache.stopped:
        from validate_fokontany import EVENTS                          # EMSRxxx -> (nom, année)
        o = pd.read_csv(oof, dtype={"adm3": str})
        ref = all_ev.set_index("id")
        col = {pc: i for i, pc in enumerate(th.pcode)}
        for ev_id, (nm, yr) in EVENTS.items():
            eid = f"{nm.lower()}-{yr}"
            sub = o[(o.evenement == ev_id) & o.adm3.isin(th.pcode)]
            if eid not in ref.index or len(sub) < 5:                   # dates seulement si elles sont sourcées dans le dépôt
                continue
            a, b = ev_window(ref.loc[eid, "date_debut"], ref.loc[eid, "date_fin"])
            dates, Q = window(cache, cells, a, b)
            if Q is None:
                break
            r2 = Q[:, idx] / q2
            rmax = {pc: float(np.nanmax(r2[:, col[pc]])) for pc in sub.adm3}
            pos = [rmax[p] for p, v in zip(sub.adm3, sub.pos) if str(v) == "True"]
            neg = [rmax[p] for p, v in zip(sub.adm3, sub.pos) if str(v) != "True"]
            ems_rows.append({"evenement": ev_id, "nom": nm, "communes": len(sub), "inondees": len(pos), "non_inondees": len(neg),
                             "auc_debit": round(auc(pos, neg), 3) if neg and pos else None,
                             "pod_q2": round(float(np.mean(np.array(pos) >= 1)), 3) if pos else None,
                             "fausses_q2": round(float(np.mean(np.array(neg) >= 1)), 3) if neg else None})
    ems = pd.DataFrame(ems_rows)
    complete = cache.stopped is None
    res = {"n_communes": len(th), "n_cells": len(cells), "detection": det, "episodes": epi, "seasons": seasons_done, "first_season": first_season,
           "ems": ems, "regions": reg_names, "complete": complete, "n_events": len(ev), "sensitivity": sens,
           "n_gdacs": 0 if gdacs is None else len(gdacs)}
    if country != "demo":
        epi.to_csv(VAL / "crues_episodes.csv", index=False)
        write_md(VAL / "crues_validation.md", res)
    print(f"Crues : {len(th)} communes, {len(cells)} mailles ; événements {len(det)}/{len(ev)} évalués "
          f"({int(det.detecte_vigilance.sum()) if len(det) else 0} détectés en vigilance) ; {seasons_done} saisons, {len(epi)} épisodes ; "
          f"{len(ems)} activations EMS ; {'complet' if complete else 'INCOMPLET (quota) : relancer'}", flush=True)
    return res


def write_md(path, res):
    def f(v, n=2):
        return "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{n}f}".replace(".", ",")
    det, epi, ems = res["detection"], res["episodes"], res["ems"]
    n_loc = int((epi.evenement_perimetre != "").sum()) if len(epi) else 0
    n_else = int(((epi.evenement_perimetre == "") & (epi.evenement_ailleurs != "")).sum()) if len(epi) else 0
    n_gd = int(((epi.evenement_perimetre == "") & (epi.evenement_ailleurs == "") & (epi.evenement_gdacs != "")).sum()) if len(epi) else 0
    L = ["# Validation du modèle de crue sur le périmètre pilote", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/validate_floods.py`. Cahier des charges §7 et §13.", ""]
    if not res["complete"]:
        L += ["> **Résultat incomplet** : le quota gratuit d'Open-Meteo a été atteint. Relancer le workflow « 10 » pour compléter.", ""]
    L += ["**Données**",
          f"- Périmètre : {res['n_communes']} communes ({res['n_cells']} mailles GloFAS) avec un seuil de crue ({', '.join(res['regions'])}).",
          "- Débit simulé : GloFAS, réanalyse journalière via Open-Meteo.",
          "- Seuils : crue de 2 ans = vigilance, crue de 5 ans = alerte (loi de Gumbel sur les maxima annuels simulés 1984-2025).",
          "",
          "**Ce qui n'est pas validé ici**",
          "- La prévision et son délai d'anticipation : les archives de prévision GloFAS demandent un compte Copernicus CDS.",
          "- Les débits réels : aucune station hydrométrique publique n'est disponible.",
          "",
          "La validation est donc **partielle** (règle §13).",
          "",
          "## 1. Les inondations documentées sont-elles détectées ?", "",
          f"{res['n_events']} événements documentés citent le périmètre. Un événement est détecté si au moins {int(SHARE * 100)} % des communes "
          "dépassent le seuil dans la fenêtre [début − 2 j, fin + 10 j].", "",
          "| Événement | Dates | Communes ≥ crue de 2 ans | Communes ≥ crue de 5 ans | Débit max / crue de 2 ans | Détecté (vigilance) | Détecté (alerte) |",
          "|---|---|---|---|---|---|---|"]
    for _, r in det.iterrows():
        L.append(f"| {r.evenement} | {r.debut} → {r.fin} | {round(100 * r.part_communes_q2)} % | {round(100 * r.part_communes_q5)} % | "
                 f"{f(r.rapport_max_q2)} | {'oui' if r.detecte_vigilance else '**non**'} | {'oui' if r.detecte_alerte else 'non'} |")
    if len(det):
        L += ["", f"**Taux de détection : {int(det.detecte_vigilance.sum())} / {len(det)} en vigilance, {int(det.detecte_alerte.sum())} / {len(det)} en alerte.**"]
    L += ["", f"## 2. Épisodes de dépassement sur les cours d'eau principaux ({N_MAIN} mailles de plus fort débit)", "",
          f"Saisons de pluie de novembre {res['first_season']} à avril {res['first_season'] + res['seasons']} ({res['seasons']} saisons). "
          f"Un épisode = au moins {int(SHARE * 100)} % des mailles au-dessus de la crue de 2 ans ; des jours séparés de plus de {GAP_DAYS} jours forment des épisodes distincts.", "",
          f"- **{len(epi)} épisodes**, soit environ {f(len(epi) / max(res['seasons'], 1), 1)} par saison.",
          f"- {n_loc} correspondent à un événement documenté dans le périmètre.",
          f"- {n_else} correspondent à un événement documenté ailleurs à Madagascar, sans mention du périmètre.",
          f"- {n_gd} correspondent seulement à un cyclone ou une inondation GDACS ({res['n_gdacs']} événements indépendants de GloFAS, "
          "`validation/evenements_gdacs.csv`) : explication possible, région non précisée.",
          f"- **{len(epi) - n_loc - n_else - n_gd} sans aucune correspondance.** Ce sont des fausses alertes possibles, à comparer avec la liste BNGRC des inondations non cycloniques.",
          "", "| Début | Fin | Part max des mailles | Événement (périmètre) | Événement (ailleurs) | GDACS |", "|---|---|---|---|---|---|"]
    for _, r in epi.iterrows():
        L.append(f"| {r.debut} | {r.fin} | {round(100 * r.part_max_mailles_q2)} % | {r.evenement_perimetre or '—'} | {r.evenement_ailleurs or '—'} | {r.evenement_gdacs or '—'} |")
    sens = res["sensitivity"]
    if len(sens):
        L += ["", "## 2 bis. Sensibilité au seuil : arbitrage entre détection et fausses alertes", "",
              "Le seuil s'applique à la part des communes pour la détection des événements du périmètre, et à la part des mailles principales pour les épisodes.", "",
              "| Seuil | Événements du périmètre détectés | Épisodes simulés | Dont événement du périmètre | Sans aucune correspondance |",
              "|---|---|---|---|---|"]
        for _, s in sens.iterrows():
            L.append(f"| {s.seuil} | {s.detectes} / {s.evenements} | {s.episodes} | {s.episodes_perimetre} | {s.episodes_sans_correspondance} |")
        L += ["", "Abaisser le seuil fait détecter plus d'événements, mais crée plus d'épisodes sans correspondance. "
              "Le choix du seuil opérationnel revient aux services (BNGRC, DGRE) : il n'est pas fixé ici."]
    L += ["", "## 3. Communes inondées selon le satellite (Copernicus EMS)", ""]
    if len(ems):
        L += ["| Activation | Communes comparées | Inondées | Non inondées | AUC du débit simulé | Inondées en vigilance (≥ crue de 2 ans) | Non inondées en vigilance |",
              "|---|---|---|---|---|---|---|"]
        for _, r in ems.iterrows():
            L.append(f"| {r.evenement} ({r.nom}) | {r.communes} | {r.inondees} | {r.non_inondees} | {f(r.auc_debit)} | "
                     f"{'—' if r.pod_q2 is None else str(round(100 * r.pod_q2)) + ' %'} | {'—' if r.fausses_q2 is None else str(round(100 * r.fausses_q2)) + ' %'} |")
        L += ["", "AUC : 0,5 = pas mieux que le hasard, 1 = séparation parfaite. Avec si peu d'activations, le résultat est indicatif."]
    else:
        L.append("Aucune activation EMS sourcée avec au moins 5 communes du périmètre.")
    L += ["", "## Limites", "",
          "- Les seuils sont calculés sur le même débit simulé : on teste la cohérence du modèle avec les inondations, pas sa justesse en m³/s.",
          "- Les mailles GloFAS (~5 km) sont plus grossières que l'inondation urbaine d'Antananarivo, qui dépend du drainage, des digues et du pompage. "
          "L'inondation pluviale (§7.A) n'est pas représentée.",
          "- Avec si peu d'événements, les taux sont très incertains.",
          "",
          "**Données qui rendraient la validation complète :** débits observés (DGRE), archive des prévisions GloFAS (compte CDS), "
          "liste BNGRC des inondations non cycloniques, cartes Sentinel-1 des zones inondées (GFM)."]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    main(ap.parse_args().country)
