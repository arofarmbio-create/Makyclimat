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
    for name in ("Calendriers_culturaux-Riz-2025-2026.pdf",):
        r = requests.get("https://www.meteomadagascar.mg/wp-content/uploads/" + name, timeout=120, headers={"User-Agent": "Mozilla/5.0"})
        note(f"== {name} HTTP {r.status_code} {len(r.content)/1e6:.1f} Mo")
        with pdfplumber.open(io.BytesIO(r.content)) as p:
            note(f"pages {len(p.pages)}")
            for k in (4, 5, 8):
                if k >= len(p.pages):
                    continue
                pg = p.pages[k]
                cols = collections.Counter(str(r_.get("non_stroking_color")) for r_ in pg.rects)
                note(f"-- page {k + 1} : {pg.width:.0f}x{pg.height:.0f}, {len(pg.rects)} rectangles, couleurs {dict(cols.most_common(8))}, {len(pg.lines)} lignes, {len(pg.images)} images")
                note((pg.extract_text() or "")[:1800])


try:
    pdf()
except Exception as e:
    note(f"== PDF ECHEC {type(e).__name__}: {str(e)[:500]}")
open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
sys.exit(0)
