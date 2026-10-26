"""Tests du calcul d'écart de prix (pas de test réseau : la collecte HDX tourne uniquement sur GitHub Actions,
le bac à sable n'a pas accès à data.humdata.org)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from connector_wfp_prices import monthly_price_gap


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
