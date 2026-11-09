"""Récupération partielle des lignes d'une base SQLite (GeoPackage) tronquée.

Les copies Wayback Machine des geopackages BushProof sont coupées à 1 Mio : SQLite refuse de les ouvrir
(« database disk image is malformed »). Ce script parcourt toutes les pages présentes, décode les feuilles de
table (type 13) et rattache chaque enregistrement à sa table par le nombre de colonnes déclaré dans sqlite_master.
Les débordements (overflow) absents du fichier rendent l'enregistrement incomplet : il est alors écarté et compté.

Usage : python -I -X utf8 scripts/sqlite_tronque.py <fichier.gpkg> <dossier_sortie>
Écrit un CSV par table récupérée et un résumé JSON dans le dossier de sortie (à garder hors git).
"""
import csv
import json
import re
import struct
import sys
from pathlib import Path


def varint(b, i):
    v = 0
    for k in range(9):
        c = b[i + k]
        if k == 8:
            return (v << 8) | c, i + 9
        v = (v << 7) | (c & 0x7F)
        if c < 0x80:
            return v, i + k + 1
    raise ValueError


class DB:
    def __init__(self, data):
        self.d = data
        ps = struct.unpack(">H", data[16:18])[0]
        self.ps = 65536 if ps == 1 else ps
        self.usable = self.ps - data[20]
        self.npages_header = struct.unpack(">I", data[28:32])[0]
        self.npages_file = len(data) // self.ps

    def page(self, n):
        o = (n - 1) * self.ps
        if n < 1 or o + self.ps > len(self.d):
            return None
        return self.d[o:o + self.ps]

    def payload(self, pg, i, P):
        U = self.usable
        X = U - 35
        if P <= X:
            return pg[i:i + P], True
        M = ((U - 12) * 32 // 255) - 23
        K = M + ((P - M) % (U - 4))
        loc = K if K <= X else M
        out = bytearray(pg[i:i + loc])
        nxt = struct.unpack(">I", pg[i + loc:i + loc + 4])[0]
        while len(out) < P and nxt:
            op = self.page(nxt)
            if op is None:
                return bytes(out), False
            nxt = struct.unpack(">I", op[0:4])[0]
            out += op[4:U]
        return bytes(out[:P]), len(out) >= P

    def leaf_records(self, n):
        pg = self.page(n)
        if pg is None:
            return
        h = 100 if n == 1 else 0
        if pg[h] != 13:
            return
        ncell = struct.unpack(">H", pg[h + 3:h + 5])[0]
        for k in range(ncell):
            ptr = struct.unpack(">H", pg[h + 8 + 2 * k:h + 10 + 2 * k])[0]
            try:
                P, i = varint(pg, ptr)
                rowid, i = varint(pg, i)
                pay, ok = self.payload(pg, i, P)
                yield rowid, (decode(pay) if ok else None)
            except (IndexError, ValueError, struct.error):
                yield None, None


def decode(rec):
    hs, i = varint(rec, 0)
    types = []
    while i < hs:
        t, i = varint(rec, i)
        types.append(t)
    vals, j = [], hs
    for t in types:
        if t == 0:
            vals.append(None)
        elif 1 <= t <= 6:
            ln = [0, 1, 2, 3, 4, 6, 8][t]
            vals.append(int.from_bytes(rec[j:j + ln], "big", signed=True)); j += ln
        elif t == 7:
            vals.append(struct.unpack(">d", rec[j:j + 8])[0]); j += 8
        elif t in (8, 9):
            vals.append(t - 8)
        elif t >= 12 and t % 2 == 0:
            ln = (t - 12) // 2
            vals.append(bytes(rec[j:j + ln])); j += ln
        elif t >= 13:
            ln = (t - 13) // 2
            vals.append(rec[j:j + ln].decode("utf-8", "replace")); j += ln
        else:
            raise ValueError(t)
    return vals


def columns_of(sql):
    body = sql[sql.index("(") + 1:sql.rindex(")")]
    cols, depth, cur = [], 0, ""
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            cols.append(cur); cur = ""
        else:
            cur += ch
    cols.append(cur)
    names = []
    for c in cols:
        c = c.strip()
        if re.match(r"(?i)(constraint|primary\s+key|unique|check|foreign\s+key)\b", c):
            continue
        m = re.match(r'"([^"]+)"|`([^`]+)`|\[([^\]]+)\]|(\S+)', c)
        names.append(next(g for g in m.groups() if g))
    return names


def recover(src):
    """Renvoie (résumé, colonnes par table, lignes par table {rowid: valeurs})."""
    src = Path(src)
    db = DB(src.read_bytes())
    # schéma : enregistrements de sqlite_master (5 colonnes, premier champ 'table')
    tables, roots = {}, {}
    for n in range(1, db.npages_file + 1):
        for _, v in db.leaf_records(n):
            if v and len(v) == 5 and v[0] == "table" and isinstance(v[4], str) and v[4].upper().startswith("CREATE"):
                tables[v[1]] = columns_of(v[4])
                roots[v[1]] = v[3]
    # pages feuilles atteignables depuis la racine de chaque table (pages intérieures présentes seulement)
    owner, unreachable = {}, {}
    for t, r in roots.items():
        stack, miss = [r], 0
        while stack:
            n = stack.pop()
            pg = db.page(n)
            if pg is None:
                miss += 1
                continue
            h = 100 if n == 1 else 0
            if pg[h] == 13:
                owner[n] = t
            elif pg[h] == 5:
                nc = struct.unpack(">H", pg[h + 3:h + 5])[0]
                stack.append(struct.unpack(">I", pg[h + 8:h + 12])[0])
                for k in range(nc):
                    ptr = struct.unpack(">H", pg[h + 12 + 2 * k:h + 14 + 2 * k])[0]
                    stack.append(struct.unpack(">I", pg[ptr:ptr + 4])[0])
        unreachable[t] = miss
    by_ncol = {}
    for t, cols in tables.items():
        by_ncol.setdefault(len(cols), []).append(t)
    rows = {t: {} for t in tables}
    incomplete = 0
    ambiguous = 0
    for n in range(1, db.npages_file + 1):
        for rowid, v in db.leaf_records(n):
            if v is None:
                incomplete += rowid is not None
                continue
            if n in owner and len(tables[owner[n]]) == len(v):
                rows[owner[n]][rowid] = v
                continue
            cands = by_ncol.get(len(v), [])
            if len(cands) == 1 and not (len(v) == 5 and v[0] in ("table", "index", "trigger", "view")):
                rows[cands[0]][rowid] = v
            elif len(cands) > 1:
                ambiguous += 1
    summary = {"fichier": src.name, "octets": len(db.d), "pages_annoncees": db.npages_header,
               "pages_presentes": db.npages_file, "taille_page": db.ps,
               "enregistrements_incomplets_ecartes": incomplete, "enregistrements_ambigus": ambiguous,
               "tables": {t: {"colonnes": len(tables[t]), "lignes_recuperees": len(rows[t]),
                              "pages_absentes_sous_la_racine": unreachable.get(t)} for t in tables
                          if not t.startswith(("rtree_", "gpkg_", "sqlite_"))}}
    return summary, tables, rows


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    summary, tables, rows = recover(src)
    for t, rr in rows.items():
        if not rr or t.startswith(("gpkg_", "rtree_", "sqlite_")):
            continue
        safe = re.sub(r"[^\w.-]+", "_", t)
        with open(out / f"{src.stem}__{safe}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["_rowid"] + tables[t])
            for rid in sorted(rr):
                w.writerow([rid] + [("<geom %d o>" % len(x)) if isinstance(x, bytes) else x for x in rr[rid]])
    (out / f"{src.stem}__recuperation.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1),
                                                        encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
