"""Sondage de sources depuis GitHub Actions : le résultat est écrit dans data/_probe.txt (lisible dans le dépôt)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
out = []


def note(msg):
    print(msg)
    out.append(str(msg))


def attempt(name, fn):
    try:
        fn()
    except Exception as e:
        note(f"== {name} ECHEC {type(e).__name__}: {str(e)[:600]}")


def dhs():
    import connector_dhs as CD
    from common import read_units
    data = CD.fetch("MD")
    note(f"== DHS : {len(data)} lignes brutes")
    df, log = CD.build(data, read_units("mdg"))
    note("\n".join(log))
    note(f"   {len(df)} valeurs, {df.pcode.nunique()} régions")
    if len(df):
        note(df.pivot_table(index="pcode", columns="indicateur", values="valeur").round(1).to_string()[:3500])


def heigit():
    import connector_heigit as CH
    df = CH.build_flood(CH.fetch("MDG_ADM2_flood_exposure.csv"))
    note(f"== HeiGIT crues : {len(df)} valeurs, {df.pcode.nunique()} districts, {df.indicateur.nunique()} indicateurs")
    note(df[df.indicateur.str.startswith("crue_rp100")].groupby("indicateur").valeur.describe().round(1).to_string())


attempt("DHS", dhs)
attempt("HeiGIT crues", heigit)
open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
sys.exit(0)
