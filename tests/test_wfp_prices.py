"""Tests du calcul d'écart de prix (pas de test réseau : la collecte HDX tourne uniquement sur GitHub Actions,
le bac à sable n'a pas accès à data.humdata.org)."""
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from connector_wfp_prices import ADM1_MAP, MAX_STALENESS_DAYS, monthly_price_gap, write_indicator


def _rows(region, prices_by_month):
    return [{"admin1": region, "mois": m, "price": p} for m, p in prices_by_month.items()]


def test_no_history_gives_no_gap():
    rice = pd.DataFrame(_rows("Androy", {"2021-06": 1000}))
    out = monthly_price_gap(rice)
    assert len(out) == 1
    assert out.iloc[0]["ecart_prix_pct"] is None


def test_gap_computed_against_same_calendar_month_only():
    # juin à 1000 trois années de suite, puis juin à 1300 : +30 % attendu, pas influencé par un autre mois
    months = {"2019-06": 1000, "2019-11": 2000, "2020-06": 1000, "2021-06": 1000, "2022-06": 1300}
    rice = pd.DataFrame(_rows("Androy", months))
    out = monthly_price_gap(rice).set_index("mois")
    assert abs(out.loc["2022-06", "ecart_prix_pct"] - 30.0) < 0.5


def test_regions_are_independent():
    rice = pd.DataFrame(_rows("Androy", {"2021-06": 1000, "2022-06": 1200}) + _rows("Anosy", {"2021-06": 500, "2022-06": 500}))
    out = monthly_price_gap(rice)
    androy = out[(out.adm1_label == "Androy") & (out.mois == "2022-06")].iloc[0]
    anosy = out[(out.adm1_label == "Anosy") & (out.mois == "2022-06")].iloc[0]
    assert androy["ecart_prix_pct"] is None or androy["ecart_prix_pct"] != anosy.get("ecart_prix_pct")


def _with_tmp_root(fn):
    """Exécute fn(tmp_root) avec connector_wfp_prices.ROOT redirigé vers un dossier temporaire, remis en place après."""
    import connector_wfp_prices as c
    with tempfile.TemporaryDirectory() as d:
        tmp_root = Path(d)
        old_root = c.ROOT
        c.ROOT = tmp_root
        try:
            fn(tmp_root)
        finally:
            c.ROOT = old_root


def test_write_indicator_excludes_stale_regions():
    def run(tmp_root):
        recent = (pd.Timestamp.today() - pd.Timedelta(days=30)).strftime("%Y-%m")
        stale = "2015-01"
        out = pd.DataFrame([
            {"adm1_label": "Androy", "mois": recent, "ecart_prix_pct": -10.0},
            {"adm1_label": "Sofia", "mois": stale, "ecart_prix_pct": 5.0},
        ])
        write_indicator(out)
        dest = tmp_root / "data" / "mdg" / "external" / "prix_riz_ecart.csv"
        written = pd.read_csv(dest)
        assert set(written.pcode) == {"MG52"}  # Androy seulement : Sofia est trop ancien, donc exclu
        assert written.iloc[0]["valeur"] == -10.0
    _with_tmp_root(run)


def test_merged_region_duplicated_on_both_pcodes():
    def run(tmp_root):
        recent = (pd.Timestamp.today() - pd.Timedelta(days=10)).strftime("%Y-%m")
        out = pd.DataFrame([{"adm1_label": "Vatovavy Fitovinany", "mois": recent, "ecart_prix_pct": 7.5}])
        write_indicator(out)
        written = pd.read_csv(tmp_root / "data" / "mdg" / "external" / "prix_riz_ecart.csv")
        assert set(written.pcode) == {"MG26", "MG27"}
        assert (written.valeur == 7.5).all()
    _with_tmp_root(run)


def test_no_recent_region_removes_stale_file():
    def run(tmp_root):
        dest = tmp_root / "data" / "mdg" / "external" / "prix_riz_ecart.csv"
        dest.parent.mkdir(parents=True)
        dest.write_text("pcode,indicateur,valeur,date,source\nMG11,prix_riz_ecart_pct,1,2015-01,x\n")
        out = pd.DataFrame([{"adm1_label": "Sofia", "mois": "2015-01", "ecart_prix_pct": 5.0}])
        write_indicator(out)
        assert not dest.exists()  # un ancien fichier périmé ne doit pas rester affiché comme si c'était à jour
    _with_tmp_root(run)


def test_all_adm1_map_pcodes_look_like_region_codes():
    for name, pcodes in ADM1_MAP.items():
        for pc in pcodes:
            assert pc.startswith("MG") and len(pc) == 4, (name, pc)


if __name__ == "__main__":
    import inspect
    mod = sys.modules[__name__]
    fails = 0
    for name, fn in inspect.getmembers(mod, inspect.isfunction):
        if name.startswith("test_"):
            try:
                fn()
                print(f"OK    {name}")
            except AssertionError as e:
                fails += 1
                print(f"ÉCHEC {name} : {e}")
    if fails:
        raise SystemExit(f"{fails} test(s) en échec")
    print("Tous les tests du connecteur de prix passent.")
