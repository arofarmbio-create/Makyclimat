/* MakyClimat — fonctions pures (testables sans navigateur). */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.MC = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // Même règle que scripts/compute_metrics.py : 0 = pas de donnée, sinon niveau du premier seuil dépassé.
  function levelFromPct(pct, alertLevels) {
    if (pct === null || pct === undefined || !isFinite(pct)) return 0;
    var rules = alertLevels.slice().sort(function (a, b) { return b.level - a.level; });
    for (var i = 0; i < rules.length; i++) if (pct < rules[i].below_pct) return rules[i].level;
    return 0;
  }

  // Valeur d'un indicateur pour une unité, sous scénario de pluie (simIdx = index du facteur, null = observé).
  var SC_IDX = { pc: 0, l: 1, e: 2, t: 3, w: 4 };
  function valueFor(m, key, simIdx, meta, scn) {
    if (!m) return null;
    if (scn && m.sc && m.sc[scn] && SC_IDX[key] !== undefined) {
      var v = m.sc[scn][SC_IDX[key]];
      return v === undefined ? null : v;
    }
    if (scn && m.sc && m.sc[scn] && key === "g") return Math.max(0, m.sc[scn][3] - (m.b || 0));
    if (key === "ewm") return m.ew ? Math.max.apply(null, m.ew) : null;
    if (/^ew[0-4]$/.test(key)) return m.ew ? m.ew[+key.charAt(2)] : null;
    if (key === "pa") return m.pa === undefined || m.pa === null ? null : m.pa * 100;
    if (key === "ex") return m.ex === undefined ? null : m.ex;
    if (key === "w") { var hs = m.sc && (m.sc[scn] || m.sc.hum); return hs ? hs[4] : null; }
    var f = simIdx === null || simIdx === undefined ? 1 : meta.rain_factors[simIdx];
    switch (key) {
      case "l": return simIdx === null || f === 1 ? m.l : levelFromPct(m.pc === undefined ? null : m.pc * f, meta.alert_levels);
      case "pc": return m.pc === undefined ? null : m.pc * f;
      case "e": return simIdx === null || simIdx === undefined ? m.e : m.se[simIdx];
      case "t": return simIdx === null || simIdx === undefined ? m.t : m.st[simIdx];
      case "p": return m.p === undefined ? null : m.p;
      case "g": {
        var t = valueFor(m, "t", simIdx, meta);
        return t === null ? null : Math.max(0, t - (m.b || 0));
      }
      default:
        if (typeof key === "string" && key.indexOf("x:") === 0) {
          var xv = m.x ? m.x[key.slice(2)] : undefined;
          return xv === undefined ? null : xv;
        }
        return null;
    }
  }

  // Bornes par quantiles sur les valeurs strictement positives (n classes).
  function classBreaks(values, n) {
    var v = values.filter(function (x) { return x !== null && isFinite(x) && x > 0; }).sort(function (a, b) { return a - b; });
    if (!v.length) return [];
    var out = [];
    for (var i = 1; i < n; i++) {
      var q = v[Math.min(v.length - 1, Math.floor((i * v.length) / n))];
      if (!out.length || q > out[out.length - 1]) out.push(q);
    }
    return out;
  }

  function classIndex(value, breaks) {
    if (value === null || value === undefined || !isFinite(value)) return -1;
    if (value <= 0) return 0;
    var i = 0;
    while (i < breaks.length && value >= breaks[i]) i++;
    return Math.min(i + 1, breaks.length + 1);
  }

  function fmtInt(n) {
    if (n === null || n === undefined || !isFinite(n)) return "n/d";
    return Math.round(n).toLocaleString("fr-FR");
  }

  function fmtPct(n) {
    if (n === null || n === undefined || !isFinite(n)) return "n/d";
    return n.toLocaleString("fr-FR", { maximumFractionDigits: 0 }) + " %";
  }

  function normalize(s) {
    return String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }

  function csvEscape(v) {
    if (v === null || v === undefined) return "";
    var s = String(v);
    return /[",;\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  function toCSV(rows, cols) {
    var head = cols.map(function (c) { return csvEscape(c.label); }).join(";");
    var body = rows.map(function (r) { return cols.map(function (c) { return csvEscape(c.get(r)); }).join(";"); });
    return "﻿" + [head].concat(body).join("\n"); // BOM pour Excel
  }

  return { levelFromPct: levelFromPct, valueFor: valueFor, classBreaks: classBreaks, classIndex: classIndex,
           fmtInt: fmtInt, fmtPct: fmtPct, normalize: normalize, toCSV: toCSV };
});
