"""Connecteur prix PPN (WFP/VAM via HDX) : première source réelle de prix pour MadagASCAR trouvée par
MakyClimat, pour amorcer un futur volet « pouvoir d'achat » (absent aujourd'hui de l'indice de
vulnérabilité cumulative — voir validation/vuln_cumul_limites.md).

Source : jeu de données HDX « WFP Food Prices for Madagascar » (prix par marché, mensuel, depuis 2004).
On découvre l'URL exacte du CSV via l'API CKAN de HDX (package_show), pour ne jamais deviner un lien :
  https://data.humdata.org/api/3/action/package_show?id=wfp-food-prices-for-madagascar

Sortie : validation/wfp_prix_riz_candidat.csv (hors data/<pays>/external/, donc PAS lu automatiquement par
compute_metrics.py) : adm1_label, mois, prix_median_riz_local_kg, ecart_prix_pct (écart au prix médian des
3 années précédentes, même mois calendaire). Ce script prépare une donnée candidate à inspecter, pas un
indicateur affiché sur le site : il faudra d'abord vérifier la couverture (régions, continuité des mois) et
relier les noms de région WFP aux pcode MakyClimat avant toute intégration.
"""
from __future__ import annotations

import io
import sys

import pandas as pd
import requests

from common import ROOT

CKAN_PACKAGE = "https://data.humdata.org/api/3/action/package_show?id=wfp-food-prices-for-madagascar"


def find_csv_url() -> str | None:
    r = requests.get(CKAN_PACKAGE, timeout=60)
    r.raise_for_status()
    pkg = r.json()
    if not pkg.get("success"):
        return None
    resources = pkg["result"].get("resources", [])
    # on prend le CSV principal (le plus volumineux, en excluant les "QuickCharts")
    csvs = [res for res in resources if str(res.get("format", "")).lower() == "csv" and "quickchart" not in res.get("name", "").lower()]
    if not csvs:
        return None
    best = max(csvs, key=lambda res: res.get("size") or 0)
    return best.get("url")


def monthly_price_gap(rice: pd.DataFrame) -> pd.DataFrame:
    """Prix médian mensuel par région (admin1) et écart au prix médian des 3 années calendaires précédentes
    pour le même mois (saisonnalité du riz). Entrée : colonnes admin1, mois ("AAAA-MM"), price."""
    monthly = rice.groupby(["admin1", "mois"])["price"].median().reset_index().rename(columns={"price": "prix_median_riz_local"})
    monthly["mnum"] = pd.to_datetime(monthly["mois"]).dt.month
    monthly["y"] = pd.to_datetime(monthly["mois"]).dt.year
    out_rows = []
    for a1, g in monthly.groupby("admin1"):
        g = g.sort_values("mois")
        for r in g.itertuples():
            hist = g[(g.mnum == r.mnum) & (g.y < r.y) & (g.y >= r.y - 3)]
            ecart = None
            if len(hist) >= 2:
                base = hist["prix_median_riz_local"].median()
                if base > 0:
                    ecart = round((r.prix_median_riz_local - base) / base * 100, 1)
            out_rows.append({"adm1_label": a1, "mois": r.mois, "prix_median_riz_local_kg": round(r.prix_median_riz_local, 1),
                              "ecart_prix_pct": ecart})
    return pd.DataFrame(out_rows)


def main() -> None:
    try:
        url = find_csv_url()
    except Exception as e:  # noqa: BLE001
        print(f"Prix WFP : impossible d'interroger HDX ({e}) — indicateur non mis à jour.")
        sys.exit(1)
    if not url:
        print("Prix WFP : aucun fichier CSV trouvé sur HDX — indicateur non mis à jour.")
        sys.exit(1)

    try:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text), low_memory=False)
    except Exception as e:  # noqa: BLE001
        print(f"Prix WFP : téléchargement échoué ({e}) — indicateur non mis à jour.")
        sys.exit(1)

    # Schéma standard HDX/WFP : date, admin1, admin2, market, commodity, unit, price, usdprice (une ligne d'en-têtes HXL en plus, à écarter)
    cols = {c.lower(): c for c in df.columns}
    need = ["date", "admin1", "commodity", "price"]
    if not all(n in cols for n in need):
        print(f"Prix WFP : colonnes attendues absentes ({list(df.columns)[:8]}...) — format inattendu, indicateur non mis à jour.")
        sys.exit(1)
    df = df.rename(columns={cols[n]: n for n in need})
    df = df[pd.to_numeric(df["price"], errors="coerce").notna()]
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    rice = df[df["commodity"].astype(str).str.contains("Rice", case=False, na=False)]
    if rice.empty:
        print("Prix WFP : aucune ligne 'Rice' trouvée dans le jeu de données — indicateur non mis à jour.")
        sys.exit(1)

    rice = rice.copy()
    rice["mois"] = rice["date"].dt.to_period("M").astype(str)
    out = monthly_price_gap(rice)

    n_months = out["mois"].nunique()
    n_regions = out["adm1_label"].nunique()
    coverage_note = (f"Prix WFP (riz) : {len(out)} lignes, {n_regions} régions nommées (Admin1 WFP), {n_months} mois.")
    print(coverage_note)
    dest = ROOT / "validation" / "wfp_prix_riz_candidat.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dest, index=False)
    print(f"Écrit (archive complète, pour inspection) : {dest}")

    write_indicator(out)


# Correspondance nom de région WFP -> pcode région MakyClimat (units.csv, niveau 1).
# "Vatovavy Fitovinany" : les deux régions actuelles (séparées depuis 2009) étaient encore comptées
# ensemble par WFP à l'époque ; on duplique la même valeur sur les deux, en le disant dans la source.
ADM1_MAP = {
    "Alaotra Mangoro": ["MG33"], "Amoron I Mania": ["MG22"], "Analamanga": ["MG11"], "Analanjirofo": ["MG32"],
    "Androy": ["MG52"], "Anosy": ["MG53"], "Atsimo Andrefana": ["MG51"], "Atsimo Atsinanana": ["MG25"],
    "Atsinanana": ["MG31"], "Betsiboka": ["MG43"], "Boeny": ["MG41"], "Bongolava": ["MG14"], "Diana": ["MG71"],
    "Haute Matsiatra": ["MG21"], "Ihorombe": ["MG24"], "Itasy": ["MG13"], "Melaky": ["MG44"], "Menabe": ["MG54"],
    "Sava": ["MG72"], "Sofia": ["MG42"], "Vakinankaratra": ["MG12"], "Vatovavy Fitovinany": ["MG26", "MG27"],
}


MAX_STALENESS_DAYS = 185  # ~6 mois : au-delà, le dernier prix connu n'est plus un état "actuel", on ne l'affiche pas


def write_indicator(out: pd.DataFrame) -> None:
    """Écrit le DERNIER écart de prix connu par région dans data/mdg/external/ (format standard pcode,
    indicateur,valeur,date,source : lu automatiquement par compute_metrics.py, hérité vers les niveaux
    inférieurs via indicators.yml : inherit: down). Une région dont le dernier prix date de plus de
    MAX_STALENESS_DAYS est EXCLUE plutôt que d'afficher un chiffre périmé comme s'il était actuel : en
    pratique, la couverture récente du bulletin WFP ne porte que sur le Grand Sud et le Sud-Est (régions
    en crise alimentaire suivie de près), les autres régions n'ont plus de relevé depuis 2014-2019."""
    latest = (out.dropna(subset=["ecart_prix_pct"]).sort_values("mois").groupby("adm1_label").last().reset_index())
    today = pd.Timestamp.today()
    latest["age_days"] = (today - pd.to_datetime(latest["mois"])).dt.days
    stale = latest[latest["age_days"] > MAX_STALENESS_DAYS]["adm1_label"].tolist()
    latest = latest[latest["age_days"] <= MAX_STALENESS_DAYS]
    if stale:
        print(f"Prix WFP : {len(stale)} région(s) avec un dernier prix trop ancien (> {MAX_STALENESS_DAYS} j), exclues : {stale}")
    rows = []
    unmapped = []
    for r in latest.itertuples():
        pcodes = ADM1_MAP.get(r.adm1_label)
        if not pcodes:
            unmapped.append(r.adm1_label)
            continue
        src = "WFP/HDX (prix du riz, écart au prix médian des 3 années précédentes, même mois)"
        if len(pcodes) > 1:
            src += " ; région fusionnée Vatovavy-Fitovinany dans la source, valeur dupliquée sur les 2 régions actuelles"
        for pc in pcodes:
            rows.append({"pcode": pc, "indicateur": "prix_riz_ecart_pct", "valeur": r.ecart_prix_pct, "date": r.mois, "source": src})
    if unmapped:
        print(f"Prix WFP : régions non reliées à un pcode (ignorées) : {unmapped}")
    dest = ROOT / "data" / "mdg" / "external" / "prix_riz_ecart.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        print("Prix WFP : aucune région récente reliée à un pcode — indicateur non écrit.")
        if dest.exists():
            dest.unlink()
        return
    pd.DataFrame(rows).to_csv(dest, index=False)
    print(f"Prix WFP : indicateur écrit pour {len(rows)} régions (données récentes seulement) -> {dest}")


if __name__ == "__main__":
    main()
