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
  1. détection par événement : part des communes au-dessus de q2 / q5 dans la fenêtre [début - 2 j, fin + 10 j] ;
  2. épisodes de dépassement (au moins 10 % des communes au-dessus de q2, novembre-avril) : combien correspondent à un
     événement documenté. Les autres sont des fausses alertes POSSIBLES : la liste d'événements ne contient presque que
     des cyclones, une inondation non cyclonique non listée n'est pas une fausse alerte. Taux = borne haute ;
  3. pour chaque activation EMS : le débit simulé sépare-t-il les communes inondées des autres (AUC) ?
Sorties : validation/crues_validation.md, validation/crues_episodes.csv ; cache data/<pays>/grids/glofas_hist.npz.
Usage : python scripts/validate_floods.py --country mdg
"""
from __future__ import annotations

import argparse
import re
import datetime as dt
import time

import numpy as np
import pandas as pd

import openmeteo as om
from common import DATA_DIR, country_data_dir, grid_dir, load_config, load_grid, read_units, save_grid

VAL = DATA_DIR.parent / "validation"
SHARE = 0.10                # épisode : au moins 10 % des communes au-dessus du seuil
GAP_DAYS = 5                # deux dépassements séparés de plus de 5 jours = deux épisodes


def fetch_history(th: pd.DataFrame, start: str, end: str, batch: int = 10):
    """Débit journalier GloFAS par maille de rivière (dédoublonnée) -> (dates, Q (T, n_mailles), index commune -> maille)."""
    # une requête par maille, avec les coordonnées de la 1re commune de cette maille : même sélection de maille que pour
    # le calcul des seuils (update_floods.thresholds interroge le centroïde de la commune)
    t = th.assign(ck=list(zip(th.cell_lat.round(4), th.cell_lon.round(4))))
    cells = t.drop_duplicates("ck").reset_index(drop=True)
    key = {k: i for i, k in enumerate(cells.ck)}
    idx = np.array([key[k] for k in t.ck])
    series, dates = [None] * len(cells), None
    for i in range(0, len(cells), batch):
        sub = cells.iloc[i:i + batch]
        p = {"latitude": ",".join(f"{x:.4f}" for x in sub.lat), "longitude": ",".join(f"{x:.4f}" for x in sub.lon),
             "daily": "river_discharge", "start_date": start, "end_date": end}
        for j, item in enumerate(om.as_list(om.get_json(om.FLOOD_URL, p, retries=4, pause=5.0))):
            d = item["daily"]
            dates = dates or d["time"]
            series[i + j] = np.array([np.nan if v is None else v for v in d["river_discharge"]], dtype="float32")
        time.sleep(1.0)
    return np.array(dates), np.stack(series, axis=1), idx


def load_or_fetch(country, th, start, end):
    path = grid_dir(country) / "glofas_hist.npz"
    if path.exists():
        g = load_grid(path)
        if str(g["start"]) == start and str(g["end"]) == end and len(g["idx"]) == len(th):
            return g["dates"], g["Q"], g["idx"]
    dates, Q, idx = fetch_history(th, start, end)
    save_grid(path, dates=dates, Q=Q, idx=idx, start=np.array(start), end=np.array(end))
    return dates, Q, idx


def auc(pos, neg):
    """Aire sous la courbe ROC (Mann-Whitney) ; 0,5 = hasard."""
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    gt = (pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum()
    return float(gt / (len(pos) * len(neg)))


def episodes(dates, frac, months=(11, 12, 1, 2, 3, 4)):
    """Regroupe les jours où frac >= SHARE en épisodes ; retourne [(début, fin, part max), ...]."""
    d = pd.to_datetime(dates)
    on = (frac >= SHARE) & np.isin(d.month, months)
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


def main(country="mdg", history=None, today=None, events=None):
    cfg = load_config(country)
    today = today or dt.date.today()
    th = pd.read_csv(country_data_dir(country) / "flood_thresholds.csv", dtype={"pcode": str})
    th = th[np.isfinite(th.q2) & np.isfinite(th.q5)].reset_index(drop=True)
    start = f"{cfg['flood'].get('history_start', 1984)}-01-01"
    end = (today - dt.timedelta(days=10)).isoformat()
    dates, Q, idx = history if history is not None else load_or_fetch(country, th, start, end)
    q = Q[:, idx]                                                       # (T, communes)
    r2, r5 = q / th.q2.to_numpy()[None], q / th.q5.to_numpy()[None]
    f2, f5 = np.nanmean(r2 >= 1, axis=1), np.nanmean(r5 >= 1, axis=1)
    d = pd.to_datetime(dates)
    units = read_units(country)
    names = dict(zip(units.pcode, units.name))
    regions = sorted({p[:4] for p in th.pcode})
    reg_names = [names.get(r, r) for r in regions] + (["Antananarivo"] if "MG11" in regions else [])
    # 1. détection par événement documenté
    ev = events if events is not None else pd.read_csv(VAL / "evenements.csv", dtype=str)
    ev = ev[ev.zones_citees.fillna("").str.contains("|".join(map(re.escape, reg_names)))]
    det = []
    for _, e in ev.iterrows():
        w = (d >= pd.Timestamp(e.date_debut) - pd.Timedelta(days=2)) & (d <= pd.Timestamp(e.date_fin) + pd.Timedelta(days=10))
        if not w.any():
            continue
        det.append({"evenement": e.id, "debut": e.date_debut, "fin": e.date_fin,
                    "part_communes_q2": round(float(np.nanmax(f2[w])), 3), "part_communes_q5": round(float(np.nanmax(f5[w])), 3),
                    "rapport_max_q2": round(float(np.nanmax(r2[w])), 2),
                    "detecte_vigilance": bool(np.nanmax(f2[w]) >= SHARE), "detecte_alerte": bool(np.nanmax(f5[w]) >= SHARE)})
    det = pd.DataFrame(det)
    # 2. épisodes de dépassement et correspondance avec les événements documentés
    eps = episodes(dates, f2)
    rows = []
    for a, b, m in eps:
        hit = [e.id for _, e in ev.iterrows()
               if pd.Timestamp(a) <= pd.Timestamp(e.date_fin) + pd.Timedelta(days=10) and pd.Timestamp(b) >= pd.Timestamp(e.date_debut) - pd.Timedelta(days=2)]
        rows.append({"debut": a, "fin": b, "part_max_communes_q2": round(m, 3), "evenement_documente": ";".join(hit)})
    epi = pd.DataFrame(rows, columns=["debut", "fin", "part_max_communes_q2", "evenement_documente"])
    first_doc = pd.to_datetime(ev.date_debut).min() if len(ev) else None
    epi_doc = epi[pd.to_datetime(epi.debut) >= first_doc] if first_doc is not None and len(epi) else epi
    # 3. activations EMS : débit simulé, communes inondées contre non inondées
    ems_rows = []
    oof = VAL / "ems_communes_oof.csv"
    if oof.exists():
        from validate_fokontany import EVENTS                          # EMSRxxx -> (nom, année)
        o = pd.read_csv(oof, dtype={"adm3": str})
        all_ev = pd.read_csv(VAL / "evenements.csv", dtype=str).set_index("id")
        for ev_id, (nm, yr) in EVENTS.items():
            eid = f"{nm.lower()}-{yr}"
            if eid not in all_ev.index:                                # dates seulement si elles sont sourcées dans le dépôt
                continue
            a, b = all_ev.loc[eid, "date_debut"], all_ev.loc[eid, "date_fin"]
            sub = o[(o.evenement == ev_id) & o.adm3.isin(th.pcode)]
            w = (d >= pd.Timestamp(a) - pd.Timedelta(days=2)) & (d <= pd.Timestamp(b) + pd.Timedelta(days=10))
            if len(sub) < 5 or not w.any():
                continue
            col = {pc: i for i, pc in enumerate(th.pcode)}
            rmax = {pc: float(np.nanmax(r2[w, col[pc]])) for pc in sub.adm3}
            pos = [rmax[p] for p, v in zip(sub.adm3, sub.pos) if str(v) == "True"]
            neg = [rmax[p] for p, v in zip(sub.adm3, sub.pos) if str(v) != "True"]
            ems_rows.append({"evenement": ev_id, "communes": len(sub), "inondees": len(pos), "non_inondees": len(neg),
                             "auc_debit": round(auc(pos, neg), 3) if neg else None,
                             "pod_q2": round(float(np.mean(np.array(pos) >= 1)), 3) if pos else None,
                             "fausses_q2": round(float(np.mean(np.array(neg) >= 1)), 3) if neg else None})
    ems = pd.DataFrame(ems_rows)
    res = {"n_communes": len(th), "periode": (str(d[0].date()), str(d[-1].date())), "detection": det, "episodes": epi,
           "episodes_periode_doc": epi_doc, "ems": ems, "regions": reg_names}
    if country != "demo":
        epi.to_csv(VAL / "crues_episodes.csv", index=False)
        write_md(VAL / "crues_validation.md", res)
    n_hit = int(det.detecte_vigilance.sum()) if len(det) else 0
    print(f"Crues : {len(th)} communes, {len(det)} événements documentés ({n_hit} détectés en vigilance), "
          f"{len(epi_doc)} épisodes depuis le 1er événement documenté, {len(ems)} activations EMS comparées")
    return res


def write_md(path, res):
    def f(v, n=2):
        return "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{n}f}".replace(".", ",")
    det, epi, ed, ems = res["detection"], res["episodes"], res["episodes_periode_doc"], res["ems"]
    n_doc = int((ed.evenement_documente != "").sum()) if len(ed) else 0
    L = ["# Validation du modèle de crue sur le périmètre pilote",
         "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/validate_floods.py`. Cahier des charges §7 et §13.",
         "",
         "**Données**",
         f"- Périmètre : {res['n_communes']} communes avec un seuil de crue ({', '.join(res['regions'])}).",
         f"- Débit simulé : GloFAS, réanalyse journalière via Open-Meteo, du {res['periode'][0]} au {res['periode'][1]}.",
         "- Seuils : crue de 2 ans = vigilance, crue de 5 ans = alerte (loi de Gumbel sur les maxima annuels simulés).",
         "",
         "**Ce qui n'est pas validé ici**",
         "- La prévision et son délai d'anticipation : les archives de prévision GloFAS demandent un compte Copernicus CDS.",
         "- Les débits réels : aucune station hydrométrique publique n'est disponible.",
         "",
         "La validation est donc **partielle** (règle §13).",
         "",
         "## 1. Les inondations documentées sont-elles détectées ?",
         "",
         f"Un événement est détecté si au moins {int(SHARE * 100)} % des communes dépassent le seuil dans la fenêtre [début − 2 j, fin + 10 j].",
         "",
         "| Événement | Dates | Communes ≥ crue de 2 ans | Communes ≥ crue de 5 ans | Débit max / crue de 2 ans | Détecté (vigilance) | Détecté (alerte) |",
         "|---|---|---|---|---|---|---|"]
    for _, r in det.iterrows():
        L.append(f"| {r.evenement} | {r.debut} → {r.fin} | {round(100 * r.part_communes_q2)} % | {round(100 * r.part_communes_q5)} % | "
                 f"{f(r.rapport_max_q2)} | {'oui' if r.detecte_vigilance else '**non**'} | {'oui' if r.detecte_alerte else 'non'} |")
    if len(det):
        L += ["", f"**Taux de détection (vigilance) : {int(det.detecte_vigilance.sum())} / {len(det)}** ; en alerte : {int(det.detecte_alerte.sum())} / {len(det)}."]
    L += ["", "## 2. Épisodes de dépassement sans événement documenté (fausses alertes possibles)", "",
          f"Épisode : au moins {int(SHARE * 100)} % des communes au-dessus de la crue de 2 ans, de novembre à avril. "
          f"Jours séparés de plus de {GAP_DAYS} jours = épisodes distincts.",
          "",
          f"- Sur toute la période : {len(epi)} épisodes.",
          f"- Depuis le premier événement documenté : {len(ed)} épisodes, dont {n_doc} correspondent à un événement documenté."]
    if len(ed):
        L.append(f"- **Part d'épisodes sans correspondance : {round(100 * (1 - n_doc / len(ed)))} %**. C'est une borne haute des fausses alertes : "
                 "la liste d'événements du dépôt ne contient presque que des cyclones.")
    L += ["", "Épisodes depuis 2015 :", "", "| Début | Fin | Part max des communes | Événement documenté |", "|---|---|---|---|"]
    for _, r in epi[pd.to_datetime(epi.debut) >= "2015-01-01"].iterrows():
        L.append(f"| {r.debut} | {r.fin} | {round(100 * r.part_max_communes_q2)} % | {r.evenement_documente or '—'} |")
    L += ["", "## 3. Communes inondées selon le satellite (Copernicus EMS)", ""]
    if len(ems):
        L += ["| Activation | Communes comparées | Inondées | Non inondées | AUC du débit simulé | Inondées détectées (≥ crue de 2 ans) | Non inondées en vigilance |",
              "|---|---|---|---|---|---|---|"]
        for _, r in ems.iterrows():
            L.append(f"| {r.evenement} | {r.communes} | {r.inondees} | {r.non_inondees} | {f(r.auc_debit)} | "
                     f"{'—' if r.pod_q2 is None else str(round(100 * r.pod_q2)) + ' %'} | {'—' if r.fausses_q2 is None else str(round(100 * r.fausses_q2)) + ' %'} |")
        L += ["", "AUC : 0,5 = pas mieux que le hasard, 1 = séparation parfaite. Une seule activation dans le périmètre : résultat indicatif."]
    else:
        L.append("Aucune activation EMS avec au moins 5 communes du périmètre.")
    L += ["", "## Limites", "",
          "- Les seuils de crue sont calculés sur le même débit simulé : on teste la cohérence du modèle avec les inondations, pas sa justesse en m³/s.",
          "- Les mailles GloFAS (~5 km) sont plus grossières que l'inondation urbaine d'Antananarivo, qui dépend du drainage, des digues et des stations de pompage. "
          "L'inondation pluviale (§7.A) n'est pas représentée.",
          "- Avec si peu d'événements, aucun taux n'a d'intervalle de confiance étroit.",
          "",
          "**Données qui rendraient la validation complète :** débits observés (DGRE), archive des prévisions GloFAS (compte CDS), "
          "liste BNGRC des inondations non cycloniques, cartes Sentinel-1 des zones inondées (GFM)."]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    main(ap.parse_args().country)
