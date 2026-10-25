"""Sondage de sources depuis GitHub Actions : le résultat est écrit dans data/_probe.txt (lisible dans le dépôt)."""
import collections
import io
import sys

import requests

out = []


def note(msg):
    print(msg)
    out.append(str(msg))


def pdf():
    import pdfplumber
    r = requests.get("https://www.meteomadagascar.mg/wp-content/uploads/Calendriers_culturaux-Riz-2025-2026.pdf", timeout=120, headers={"User-Agent": "Mozilla/5.0"})
    with pdfplumber.open(io.BytesIO(r.content)) as p:
        # titre de chaque page (grands caractères en haut) pour repérer région, culture, cycle
        for k, pg in enumerate(p.pages):
            if k < 7 or k > 20:
                continue
            ws = pg.extract_words(extra_attrs=["size"], keep_blank_chars=False)
            top = [w for w in ws if w["top"] < 60]
            note(f"-- page {k + 1} : " + " ".join(w["text"] for w in top)[:200])
        pg = p.pages[8]
        ws = pg.extract_words(extra_attrs=["size"])
        note("== mots page 9 (x0,top,taille,texte) colonne de gauche et titres")
        for w in ws:
            if w["x0"] < 120 or w["top"] < 70:
                note(f"{w['x0']:.0f},{w['top']:.0f},{w['size']:.0f},{w['text']}")
        note("== rectangles colorés page 9 (x0,top,w,h,couleur) hors fonds clairs")
        rc = [(round(r_["x0"]), round(r_["top"]), round(r_["width"]), round(r_["height"]), str(r_.get("non_stroking_color"))) for r_ in pg.rects
              if str(r_.get("non_stroking_color")) in ("(0.0, 0.69, 0.941)", "(0.753, 0.0, 0.0)", "(1.0, 0.851, 0.4)", "(1.0, 0.675, 0.561)", "(0.329, 0.51, 0.208)", "(0.184, 0.365, 0.541)")]
        note(f"{len(rc)} rectangles")
        for x in sorted(rc, key=lambda t: (t[1], t[0]))[:140]:
            note(",".join(map(str, x)))
        hdr = [w for w in ws if w["text"] in ("Octobre", "Novembre", "Décembre", "Janvier", "Février", "Mars", "Avril", "Mai")]
        note("== entêtes de mois : " + "; ".join(f"{w['text']}@{w['x0']:.0f},{w['top']:.0f}" for w in hdr))


try:
    pdf()
except Exception as e:
    note(f"== PDF ECHEC {type(e).__name__}: {str(e)[:500]}")
open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
sys.exit(0)
