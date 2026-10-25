/* MakyClimat — application web (aucune dépendance sauf Leaflet). */
(function () {
  "use strict";
  var MC = window.MC;
  var params = new URLSearchParams(location.search);
  var SLUG = params.get("pays") || "mdg";
  var BASE = "data/" + SLUG + "/";
  var cache = {};

  var ALERT_COLORS = ["#bdbdbd", "#8fc08a", "#f2d16b", "#e8893a", "#b2262e"];
  var PCT_BINS = [
    { max: 50, color: "#b2262e", label: "moins de 50 %" }, { max: 75, color: "#e8893a", label: "50 à 75 %" },
    { max: 90, color: "#f2d16b", label: "75 à 90 %" }, { max: 110, color: "#b9d7a8", label: "90 à 110 %" },
    { max: 150, color: "#7fb3d5", label: "110 à 150 %" }, { max: Infinity, color: "#3b7dbf", label: "plus de 150 %" }];
  var SEQ = { p: ["#eff3ff", "#bdd7e7", "#6baed6", "#3182bd", "#08519c"],
              e: ["#fff5eb", "#fdd0a2", "#fd8d3c", "#d94801", "#7f2704"],
              t: ["#fff5eb", "#fdd0a2", "#fd8d3c", "#d94801", "#7f2704"],
              g: ["#fff5eb", "#fdd0a2", "#fd8d3c", "#d94801", "#7f2704"],
              x: ["#f7f4f9", "#d4b9da", "#c994c7", "#dd3497", "#7a0177"] };
  var SIGNED_COLORS = ["#b2182b", "#ef8a62", "#f1f1f1", "#67a9cf", "#2166ac"];
  function styleOfLayer(k) {
    if (k === "l") return "alert";
    if (k === "pc") return "pct";
    var d = layerDef(k);
    return d && d.ext && d.ext.style === "rainpct" ? "pct" : d && d.ext && d.ext.style === "signed" ? "signed" : "seq";
  }
  function layerDef(k) { return LAYERS.filter(function (l) { return l.id === k; })[0]; }
  function fmtLayer(k, v) {
    var d = layerDef(k);
    if (v === null || v === undefined) return "n/d";
    if (d && d.ext && d.ext.format === "pct") return MC.fmtPct(v);
    if (d && d.ext && d.ext.format === "float") return (d.ext.style === "signed" && v > 0 ? "+" : "") + String(Math.round(v * 100) / 100).replace(".", ",");
    return MC.fmtInt(v);
  }
  var LAYERS = [
    { id: "l", label: "Niveau d'alerte sécheresse" }, { id: "pc", label: "Pluie cumulée (% de la normale)" },
    { id: "e", label: "Population exposée" }, { id: "t", label: "Cibles potentiels (estimation)" },
    { id: "g", label: "Écart : cibles moins bénéficiaires déclarés" }, { id: "p", label: "Population" }];

  var S = { meta: null, top: null, index: null, nameOf: {}, path: [], layer: "l", simIdx: null,
            view: null, selected: null, geo: null, breaks: [], map: null, cat: null, sector: "all" };

  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function getJSON(p) {
    if (!cache[p]) cache[p] = fetch(BASE + p).then(function (r) { if (!r.ok) throw new Error(p + " : " + r.status); return r.json(); });
    return cache[p];
  }
  function levelName(l) {
    if (l === 0) return "Pas de donnée";
    var r = S.meta.alert_levels.filter(function (x) { return x.level === l; })[0];
    return r ? r.name : String(l);
  }
  function val(m, key) { return MC.valueFor(m, key, S.simIdx, S.meta); }
  function fmtDate(iso) { try { return new Date(iso + (iso.length === 10 ? "T00:00:00" : "")).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" }); } catch (e) { return iso; } }

  /* ---------- Onglets ---------- */
  function setupTabs() {
    document.querySelectorAll("nav.tabs button").forEach(function (b) {
      b.addEventListener("click", function () {
        document.querySelectorAll("nav.tabs button").forEach(function (x) { x.setAttribute("aria-selected", x === b ? "true" : "false"); });
        document.querySelectorAll(".tab").forEach(function (t) { t.classList.toggle("active", t.id === "tab-" + b.dataset.tab); });
        if (b.dataset.tab === "map" && S.map) setTimeout(function () { S.map.invalidateSize(); }, 50);
      });
    });
  }

  /* ---------- Carte ---------- */
  function setupMap() {
    var c = S.meta.map;
    S.map = L.map("map", { zoomSnap: 0.25 }).setView(c.center, c.zoom);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18, attribution: "© contributeurs OpenStreetMap" }).addTo(S.map);
  }

  function loadView() {
    var path = S.path, lvl = path.length + 1;
    if (lvl === 1) return getJSON("geo/adm1.geojson").then(function (g) { return { lvl: lvl, feats: g.features, metrics: S.top.adm1 }; });
    if (lvl === 2) return getJSON("geo/adm2.geojson").then(function (g) {
      return { lvl: lvl, feats: g.features.filter(function (f) { return f.properties.p === path[0].pcode; }), metrics: S.top.adm2 }; });
    var d = path[1].pcode;
    return Promise.all([getJSON("geo/adm" + lvl + "/" + d + ".geojson"), getJSON("metrics/d/" + d + ".json")]).then(function (r) {
      return { lvl: lvl, metrics: r[1]["adm" + lvl],
               feats: r[0].features.filter(function (f) { return f.properties.p === path[lvl - 2].pcode; }) };
    });
  }

  function computeBreaks() {
    var k = S.layer;
    var st = styleOfLayer(k);
    if (st === "alert" || st === "pct") { S.breaks = []; return; }
    var vals = S.view.feats.map(function (f) { return val(S.view.metrics[f.properties.c], k); });
    if (st === "signed") {
      var ab = vals.filter(function (x) { return x !== null && x !== undefined && isFinite(x); }).map(Math.abs).sort(function (a, b) { return a - b; });
      S.breaks = ab.length ? [ab[Math.floor(ab.length * 0.4)], ab[Math.min(ab.length - 1, Math.floor(ab.length * 0.8))]] : [0, 0];
      return;
    }
    S.breaks = MC.classBreaks(vals, 5);
  }

  function colorOf(f) {
    var m = S.view.metrics[f.properties.c], k = S.layer, v = val(m, k);
    if (v === null || v === undefined) return "#cccccc";
    if (k === "l") return ALERT_COLORS[v] || "#cccccc";
    var st = styleOfLayer(k);
    if (st === "pct") { for (var i = 0; i < PCT_BINS.length; i++) if (v < PCT_BINS[i].max) return PCT_BINS[i].color; }
    if (st === "signed") {
      var b = S.breaks || [0, 0];
      return v <= -b[1] ? SIGNED_COLORS[0] : v <= -b[0] ? SIGNED_COLORS[1] : v < b[0] ? SIGNED_COLORS[2] : v < b[1] ? SIGNED_COLORS[3] : SIGNED_COLORS[4];
    }
    if (v <= 0) return "#f2f2f2";
    var ci = MC.classIndex(v, S.breaks);
    return ci < 1 ? "#cccccc" : (SEQ[k] || SEQ.x)[Math.min(ci - 1, 4)];
  }

  function styleOf(f) {
    var sel = S.selected && S.selected.properties.c === f.properties.c;
    return { fillColor: colorOf(f), fillOpacity: 0.78, color: sel ? "#000" : "#ffffff", weight: sel ? 3 : (S.view.lvl === 4 ? 0.6 : 1.2) };
  }

  function render(fit) {
    loadView().then(function (v) {
      if (!v.feats.length) { S.path.pop(); alert("Aucune sous-zone disponible pour cette unité."); return; }
      S.view = v;
      if (S.selected && !v.feats.some(function (f) { return f.properties.c === S.selected.properties.c; })) S.selected = null;
      computeBreaks();
      if (S.geo) S.map.removeLayer(S.geo);
      S.geo = L.geoJSON({ type: "FeatureCollection", features: v.feats }, {
        style: styleOf,
        onEachFeature: function (f, layer) {
          layer.on("click", function () { onFeatureClick(f); });
          layer.bindTooltip(function () { return tipText(f); }, { sticky: true });
        } }).addTo(S.map);
      if (fit !== false) S.map.fitBounds(S.geo.getBounds(), { padding: [20, 20] });
      refresh();
      location.hash = S.path.map(function (p) { return p.pcode; }).join("/");
    }).catch(function (e) { console.error(e); alert("Erreur de chargement : " + e.message); });
  }

  function restyle() { if (!S.view) return; if (S.geo) { computeBreaks(); S.geo.setStyle(styleOf); } refresh(); }

  function tipText(f) {
    var m = S.view.metrics[f.properties.c], k = S.layer, v = val(m, k);
    var txt = k === "l" ? levelName(v) : k === "pc" ? MC.fmtPct(v) : fmtLayer(k, v);
    return "<b>" + esc(f.properties.n) + "</b><br>" + esc(layerDef(k).label) + " : " + txt;
  }

  function onFeatureClick(f) {
    var same = S.selected && S.selected.properties.c === f.properties.c;
    if (same && S.view.lvl < 4) return drill(f);
    S.selected = f;
    if (S.geo) S.geo.setStyle(styleOf);
    renderInfo();
  }

  function drill(f) {
    S.path.push({ pcode: f.properties.c, name: f.properties.n });
    S.selected = null;
    render(true);
  }

  /* ---------- Panneau ---------- */
  function refresh() { renderCrumbs(); renderLegend(); renderKPIs(); renderInfo(); renderRank(); }

  function renderCrumbs() {
    var box = $("crumbs");
    box.innerHTML = "";
    var items = [{ name: S.meta.country, upto: 0 }].concat(S.path.map(function (p, i) { return { name: p.name, upto: i + 1 }; }));
    items.forEach(function (it, i) {
      var b = document.createElement("button");
      b.textContent = it.name;
      if (i === items.length - 1) b.className = "cur";
      b.addEventListener("click", function () { S.path = S.path.slice(0, it.upto); S.selected = null; render(true); });
      box.appendChild(b);
    });
  }

  function renderLegend() {
    var k = S.layer, h = "<b>" + esc(layerDef(k).label) + "</b>";
    if (S.simIdx !== null) h += '<div><i style="background:#fff"></i> <em>scénario : pluie × ' + S.meta.rain_factors[S.simIdx].toFixed(2).replace(".", ",") + "</em></div>";
    if (k === "l") {
      [1, 2, 3, 4, 0].forEach(function (l) { h += '<div><i style="background:' + ALERT_COLORS[l] + '"></i>' + esc(levelName(l)) + "</div>"; });
    } else if (styleOfLayer(k) === "signed") {
      var sb = S.breaks || [0, 0];
      var dry = layerDef(k).ext.id.indexOf("corr") >= 0 ? "corrélation négative (moins de pluie quand l'ONI monte)" : "baisse";
      var wet = layerDef(k).ext.id.indexOf("corr") >= 0 ? "corrélation positive" : "hausse";
      h += '<div><i style="background:' + SIGNED_COLORS[0] + '"></i>' + dry + " forte (au-delà de " + fmtLayer(k, -sb[1]) + ")</div>" +
        '<div><i style="background:' + SIGNED_COLORS[1] + '"></i>' + dry + " modérée</div>" +
        '<div><i style="background:' + SIGNED_COLORS[2] + '"></i>proche de zéro (±' + fmtLayer(k, sb[0]).replace("+", "") + ')</div>' +
        '<div><i style="background:' + SIGNED_COLORS[3] + '"></i>' + wet + " modérée</div>" +
        '<div><i style="background:' + SIGNED_COLORS[4] + '"></i>' + wet + " forte (au-delà de +" + fmtLayer(k, sb[1]).replace("+", "") + ")</div>";
    } else if (styleOfLayer(k) === "pct") {
      PCT_BINS.forEach(function (b) { h += '<div><i style="background:' + b.color + '"></i>' + b.label + "</div>"; });
    } else {
      var br = S.breaks, pal = SEQ[k] || SEQ.x;
      h += '<div><i style="background:#f2f2f2"></i>zéro</div>';
      var edges = [0].concat(br);
      edges.forEach(function (e, i) {
        var next = br[i];
        var lab = i === 0 ? "moins de " + fmtLayer(k, br[0] || 0) : fmtLayer(k, e) + (next ? " à " + fmtLayer(k, next) : " et plus");
        if (br.length) h += '<div><i style="background:' + pal[Math.min(i, 4)] + '"></i>' + lab + "</div>";
      });
    }
    $("legend").innerHTML = h;
  }

  function sumView(key, sim) {
    var s = 0, any = false;
    S.view.feats.forEach(function (f) {
      var v = MC.valueFor(S.view.metrics[f.properties.c], key, sim, S.meta);
      if (v !== null && isFinite(v)) { s += v; any = true; }
    });
    return any ? s : null;
  }

  function renderKPIs() {
    var parent = S.path.length ? S.path[S.path.length - 1].name : S.meta.country;
    $("viewtitle").textContent = "Vue : " + parent + " (" + S.meta.levels[S.view.lvl].plural.toLowerCase() + ")";
    var h = "";
    [["p", "Population"], ["e", "Exposés"], ["t", "Cibles potentiels"]].forEach(function (x) {
      var obs = sumView(x[0], null), sim = S.simIdx === null ? null : sumView(x[0], S.simIdx);
      h += '<div class="kpi' + (sim !== null && x[0] !== "p" ? " sim" : "") + '"><b>' + MC.fmtInt(sim !== null && x[0] !== "p" ? sim : obs) +
           "</b><span>" + x[1] + (sim !== null && x[0] !== "p" ? " (scénario)" : "") + "</span></div>";
    });
    $("kpis").innerHTML = h;
  }

  function row(a, b) { return '<div class="row"><span>' + a + "</span><span>" + b + "</span></div>"; }

  function renderInfo() {
    var f = S.selected, box = $("info");
    if (!f) { box.innerHTML = '<div class="note">Cliquez sur une zone de la carte pour voir ses indicateurs. Cliquez une seconde fois pour explorer ses sous-zones.</div>'; return; }
    var m = S.view.metrics[f.properties.c] || {};
    var lvlLabel = S.meta.levels[S.view.lvl].label;
    var h = "<h3>" + esc(lvlLabel) + "</h3><div style='font-size:17px;font-weight:700;margin-bottom:6px'>" + esc(f.properties.n) + "</div>";
    h += row("Population (estimation)", MC.fmtInt(m.p));
    if (m.pc !== undefined) {
      h += row("Pluie de la saison", MC.fmtInt(m.a) + " mm sur " + MC.fmtInt(m.n) + " mm normaux");
      h += row("% de la normale", MC.fmtPct(m.pc) + (S.simIdx !== null ? " → <b>" + MC.fmtPct(val(m, "pc")) + "</b>" : ""));
    } else h += row("Pluie de la saison", "pas assez de données (début de saison ou hors couverture)");
    h += row("Niveau d'alerte", esc(levelName(m.l)) + (S.simIdx !== null ? " → <b>" + esc(levelName(val(m, "l"))) + "</b>" : ""));
    h += row("Population exposée", MC.fmtInt(m.e) + (S.simIdx !== null ? " → <b>" + MC.fmtInt(val(m, "e")) + "</b>" : ""));
    h += row("Cibles potentiels", MC.fmtInt(m.t) + (S.simIdx !== null ? " → <b>" + MC.fmtInt(val(m, "t")) + "</b>" : ""));
    if (m.vs !== undefined) h += row("Part vulnérable retenue", Math.round(m.vs * 100) + " % " +
      (m.vi === 1 ? "(donnée fournie)" : m.vi === 2 ? "(IPC phase 3 ou plus)" : "(valeur par défaut provisoire)"));
    (S.meta.external || []).forEach(function (x) {
      var xv = m.x ? m.x[x.id] : undefined;
      if (xv !== undefined) h += row(x.label, fmtLayer("x:" + x.id, xv));
    });
    if (S.meta.has_history) h += '<div id="histbox" class="hist"></div>';
    if (m.b) h += row("Bénéficiaires déclarés", MC.fmtInt(m.b)) + row("Écart restant", MC.fmtInt(val(m, "g")));
    if (S.view.lvl === 4) h += '<div class="note warn" style="margin-top:6px">Au niveau fokontany, les limites et la population sont des estimations anciennes : à utiliser comme indication à confirmer sur le terrain.</div>';
    if (S.view.lvl < 4) h += '<div style="margin-top:8px"><button class="btn primary" id="drillbtn">Explorer les sous-zones ▸</button></div>';
    box.innerHTML = h;
    var db = $("drillbtn");
    if (db) db.addEventListener("click", function () { drill(f); });
    if (S.meta.has_history) drawHistory(f);
  }

  function renderRank() {
    var rows = S.view.feats.map(function (f) {
      return { f: f, v: val(S.view.metrics[f.properties.c], "t") };
    }).filter(function (r) { return r.v !== null && r.v > 0; })
      .sort(function (a, b) { return b.v - a.v; }).slice(0, 10);
    var h = "<tr><th>Zone</th><th>Cibles potentiels" + (S.simIdx !== null ? " (scénario)" : "") + "</th></tr>";
    if (!rows.length) h += '<tr><td colspan="2" class="note">Aucune zone exposée dans cette vue.</td></tr>';
    rows.forEach(function (r, i) {
      h += '<tr class="link" data-i="' + i + '"><td>' + esc(r.f.properties.n) + "</td><td>" + MC.fmtInt(r.v) + "</td></tr>";
    });
    $("rank").innerHTML = h;
    $("rank").querySelectorAll("tr.link").forEach(function (tr) {
      tr.addEventListener("click", function () {
        var f = rows[+tr.dataset.i].f;
        S.selected = f; S.geo.setStyle(styleOf); renderInfo();
        S.geo.eachLayer(function (l) { if (l.feature.properties.c === f.properties.c) S.map.fitBounds(l.getBounds(), { padding: [40, 40], maxZoom: 11 }); });
      });
    });
  }

  /* ---------- Historique climat et ENSO ---------- */
  var PHASE_COLORS = { E: "#d95f02", L: "#1b6ca8", N: "#9e9e9e", "?": "#cccccc" };
  var PHASE_NAMES = { E: "El Niño", L: "La Niña", N: "neutre" };
  function drawHistory(f) {
    var box = $("histbox");
    if (!box) return;
    var pc = S.view.lvl <= 2 ? f.properties.c : S.path[1].pcode;
    var viaDistrict = S.view.lvl > 2;
    getJSON("history.json").then(function (H) {
      var box2 = $("histbox");
      var ser = H.series[pc];
      if (!box2 || !ser) return;
      var n = H.years.length, W = 300, Ht = 120, padL = 26, padB = 16, bw = (W - padL) / n;
      var mx = Math.max(150, Math.max.apply(null, ser.filter(function (v) { return v !== null; }).concat([100]))), sy = (Ht - padB - 6) / mx;
      var svg = '<svg viewBox="0 0 ' + W + " " + Ht + '" width="100%" role="img" aria-label="Pluie de chaque saison en pourcentage de la normale, colorée selon la phase ENSO">';
      svg += '<line x1="' + padL + '" x2="' + W + '" y1="' + (Ht - padB - 100 * sy) + '" y2="' + (Ht - padB - 100 * sy) + '" stroke="#555" stroke-dasharray="3 2"/>';
      svg += '<text x="1" y="' + (Ht - padB - 100 * sy + 3) + '" font-size="8" fill="#555">100 %</text>';
      ser.forEach(function (v, i) {
        if (v === null) return;
        svg += '<rect x="' + (padL + i * bw + 0.5) + '" y="' + (Ht - padB - v * sy) + '" width="' + Math.max(1, bw - 1) + '" height="' + (v * sy) +
          '" fill="' + PHASE_COLORS[H.phases[i]] + '"><title>' + H.years[i] + " : " + v + " % de la normale (" + PHASE_NAMES[H.phases[i]] + ", ONI " + String(H.oni[i]).replace(".", ",") + ")</title></rect>";
      });
      [0, Math.floor(n / 2), n - 1].forEach(function (i) {
        svg += '<text x="' + (padL + i * bw) + '" y="' + (Ht - 3) + '" font-size="8" fill="#555">' + H.years[i] + "</text>";
      });
      svg += "</svg>";
      var lg = ["E", "L", "N"].map(function (c) { return '<span><i style="background:' + PHASE_COLORS[c] + '"></i>' + PHASE_NAMES[c] + " (" + H.counts[c] + ")</span>"; }).join(" ");
      box2.innerHTML = "<b>Pluie de chaque saison depuis " + H.years[0] + (viaDistrict ? " (district " + esc(S.path[1].name) + ")" : "") + "</b>" + svg +
        '<div class="note hlegend">' + lg + "<br>Chaque barre = une saison des pluies, en % de la normale " + H.baseline[0] + "–" + H.baseline[1] + ", colorée selon la phase ENSO de cette saison.</div>";
    }).catch(function () { var b = $("histbox"); if (b) b.remove(); });
  }

  function renderEnso() {
    var e = S.meta.enso, b = $("enso");
    if (!e || !b) return;
    var col = PHASE_COLORS[e.phase] || "#999";
    b.hidden = false;
    b.innerHTML = '<i style="background:' + col + '"></i>ENSO : ' + esc(e.phase_label) + " (ONI " + (e.oni > 0 ? "+" : "") + String(e.oni).replace(".", ",") + ", " + esc(e.season) + ")";
  }

  /* ---------- Contrôles ---------- */
  function setupControls() {
    var sel = $("layer");
    (S.meta.external || []).forEach(function (x) {
      if (!LAYERS.some(function (l) { return l.id === "x:" + x.id; })) LAYERS.push({ id: "x:" + x.id, label: x.label, ext: x });
    });
    LAYERS.forEach(function (l) {
      var o = document.createElement("option"); o.value = l.id; o.textContent = l.label; sel.appendChild(o);
    });
    sel.addEventListener("change", function () { S.layer = sel.value; restyle(); });
    var sim = $("sim"), nf = S.meta.rain_factors.length, neutral = S.meta.rain_factors.indexOf(1);
    sim.max = nf - 1; sim.value = neutral;
    function apply() {
      var i = +sim.value;
      S.simIdx = i === neutral ? null : i;
      $("simlabel").textContent = S.simIdx === null ? "observée" : "× " + S.meta.rain_factors[i].toFixed(2).replace(".", ",") +
        " (" + Math.round(S.meta.rain_factors[i] * 100) + " % de l'observé)";
      restyle();
    }
    sim.addEventListener("input", apply);
    $("simreset").addEventListener("click", function () { sim.value = neutral; apply(); });
    $("print").addEventListener("click", function () { window.print(); });
    $("export").addEventListener("click", exportCSV);
    setupSearch();
  }

  function exportCSV() {
    var cols = [
      { label: "code", get: function (r) { return r.f.properties.c; } },
      { label: "nom", get: function (r) { return r.f.properties.n; } },
      { label: "niveau", get: function () { return S.meta.levels[S.view.lvl].label; } },
      { label: "population", get: function (r) { return r.m.p; } },
      { label: "pluie_mm", get: function (r) { return r.m.a; } },
      { label: "normale_mm", get: function (r) { return r.m.n; } },
      { label: "pct_normale", get: function (r) { var v = MC.valueFor(r.m, "pc", null, S.meta); return v === null ? "" : v.toFixed(1); } },
      { label: "niveau_alerte", get: function (r) { return levelName(r.m.l); } },
      { label: "exposes", get: function (r) { return r.m.e; } },
      { label: "cibles_potentiels", get: function (r) { return r.m.t; } },
      { label: "beneficiaires_declares", get: function (r) { return r.m.b || 0; } },
      { label: "part_vulnerable", get: function (r) { return r.m.vs === undefined ? "" : r.m.vs; } },
      { label: "scenario_facteur_pluie", get: function () { return S.simIdx === null ? 1 : S.meta.rain_factors[S.simIdx]; } },
      { label: "exposes_scenario", get: function (r) { return val(r.m, "e"); } },
      { label: "cibles_scenario", get: function (r) { return val(r.m, "t"); } }];
    (S.meta.external || []).forEach(function (x) {
      cols.push({ label: x.id, get: function (r) { var v = r.m.x ? r.m.x[x.id] : undefined; return v === undefined ? "" : v; } });
    });
    var rows = S.view.feats.map(function (f) { return { f: f, m: S.view.metrics[f.properties.c] || {} }; });
    var blob = new Blob([MC.toCSV(rows, cols)], { type: "text/csv;charset=utf-8" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "makyclimat_" + SLUG + "_vue_" + (S.path.map(function (p) { return p.pcode; }).join("_") || "pays") + ".csv";
    document.body.appendChild(a); a.click(); a.remove();
  }

  /* ---------- Recherche ---------- */
  function ensureIndex() {
    if (S.index) return Promise.resolve();
    return getJSON("index.json").then(function (idx) {
      S.index = idx.map(function (r) { return { c: r[0], n: r[1], l: r[2], a1: r[3], a2: r[4], a3: r[5], k: MC.normalize(r[1]) }; });
      S.index.forEach(function (r) { S.nameOf[r.c] = r.n; });
    });
  }

  function goTo(entry) {
    var chain = [entry.a1, entry.a2, entry.a3].filter(Boolean);
    var path = chain.slice(0, Math.max(0, entry.l - 1)).map(function (c) { return { pcode: c, name: S.nameOf[c] || c }; });
    S.path = path;
    S.selected = null;
    render(true);
    // sélectionne l'unité une fois la vue chargée
    var tries = 0, t = setInterval(function () {
      tries++;
      if (S.view && S.view.lvl === entry.l) {
        var f = S.view.feats.filter(function (x) { return x.properties.c === entry.c; })[0];
        if (f) { S.selected = f; S.geo.setStyle(styleOf); renderInfo();
          S.geo.eachLayer(function (l) { if (l.feature.properties.c === entry.c) S.map.fitBounds(l.getBounds(), { padding: [40, 40], maxZoom: 12 }); }); }
        clearInterval(t);
      }
      if (tries > 60) clearInterval(t);
    }, 150);
  }

  function setupSearch() {
    var q = $("q"), list = $("resultlist");
    q.addEventListener("focus", function () { ensureIndex(); });
    q.addEventListener("input", function () {
      var term = MC.normalize(q.value.trim());
      if (term.length < 2) { list.hidden = true; return; }
      ensureIndex().then(function () {
        var hits = S.index.filter(function (r) { return r.k.indexOf(term) !== -1; })
          .sort(function (a, b) { return (a.k.indexOf(term) === 0 ? 0 : 1) - (b.k.indexOf(term) === 0 ? 0 : 1) || a.l - b.l; }).slice(0, 8);
        list.innerHTML = "";
        hits.forEach(function (h) {
          var li = document.createElement("li");
          li.innerHTML = esc(h.n) + " <small>" + esc(S.meta.levels[h.l].label) + (h.a2 && h.l > 2 ? " — " + esc(S.nameOf[h.a2] || "") : "") + "</small>";
          li.addEventListener("click", function () { list.hidden = true; q.value = h.n; goTo(h); });
          list.appendChild(li);
        });
        list.hidden = !hits.length;
      });
    });
    document.addEventListener("click", function (e) { if (!$("results").contains(e.target)) list.hidden = true; });
  }

  /* ---------- Pages d'information ---------- */
  function renderCatalogue() {
    return getJSON("catalogue.json").then(function (cat) {
      S.cat = cat;
      var sectorLabel = {}, natLabel = {}, goalLabel = {};
      cat.sectors.forEach(function (s) { sectorLabel[s.id] = s.label; });
      cat.national.pge_r.axes.forEach(function (a) { natLabel[a.id] = "PGE-R · " + a.label; });
      cat.national.priorites_budgetaires_2026.forEach(function (p) { natLabel[p.id] = "Priorité 2026 · " + p.label; });
      cat.sdg.goals.forEach(function (g) { goalLabel[g.id] = g.label; });
      var chips = $("sectorchips");
      function draw() {
        chips.innerHTML = "";
        [{ id: "all", label: "Tous les secteurs" }].concat(cat.sectors).forEach(function (s) {
          var b = document.createElement("button"); b.className = "chip"; b.textContent = s.label;
          b.setAttribute("aria-pressed", S.sector === s.id ? "true" : "false");
          b.addEventListener("click", function () { S.sector = s.id; draw(); }); chips.appendChild(b);
        });
        var rows = cat.indicators.filter(function (i) { return S.sector === "all" || i.sectors.indexOf(S.sector) !== -1; });
        var h = "<tr><th>Indicateur</th><th>Secteurs</th><th>ODD</th><th>Cadre national (à valider)</th><th>Source et fréquence</th><th>Statut</th></tr>";
        rows.forEach(function (i) {
          h += "<tr><td><b>" + esc(i.label) + "</b></td><td>" + i.sectors.map(function (s) { return esc(sectorLabel[s]); }).join(", ") + "</td><td>" +
            i.sdg.map(function (t) { return '<span title="' + esc(goalLabel[t.split(".")[0]] || "") + '">ODD ' + esc(t) + "</span>"; }).join(", ") + "</td><td>" +
            (i.national || []).map(function (n) { return esc(natLabel[n] || n); }).join("<br>") + "</td><td>" + esc(i.source) + "<br><span class='note'>" + esc(i.frequency) + "</span></td><td><span class='status " + i.status + "'>" +
            (i.status === "active" ? "Actif" : "Prévu") + "</span></td></tr>";
        });
        $("cattable").innerHTML = h;
      }
      draw();
    });
  }

  function renderSources() {
    var m = S.meta, h = "<p class='note'>Dernière mise à jour automatique : " + esc(fmtDate(m.generated_at.slice(0, 10))) +
      ". Les données de pluie vont jusqu'au " + esc(fmtDate(m.data_through)) + ".</p>";
    m.sources.forEach(function (s) {
      h += '<div class="card" style="margin-bottom:10px"><b>' + esc(s.label) + "</b>";
      h += row("Fréquence de mise à jour", esc(s.frequency || ""));
      if (s.data_through) h += row("Données jusqu'au", esc(fmtDate(s.data_through)));
      if (s.baseline) h += row("Période de référence (normale)", s.baseline[0] + "–" + s.baseline[1]);
      if (s.reference_year) h += row("Année de référence", esc(s.reference_year));
      if (s.given_for !== undefined) h += row("Zones avec valeur fournie", s.given_for);
      if (s.n_indicators !== undefined) h += row("Indicateurs externes chargés", s.n_indicators);
      if (s.ipc_units !== undefined) h += row("Zones avec donnée IPC", s.ipc_units);
      if (s.units_with_beneficiaries !== undefined) h += row("Zones avec bénéficiaires déclarés", s.units_with_beneficiaries);
      h += "</div>";
    });
    h += "<p class='note'>Ajouter une base de données : voir le fichier README du dépôt (section « Ajouter une source »).</p>";
    $("sourcelist").innerHTML = h;
  }

  function renderMethod() {
    var m = S.meta, al = m.alert_levels.slice().sort(function (a, b) { return b.level - a.level; });
    var seuils = al.filter(function (a) { return a.below_pct < 1000; }).map(function (a) { return esc(a.name) + " : moins de " + a.below_pct + " %"; }).join(" ; ");
    $("methodtext").innerHTML =
      "<h2>Méthode (version pilote)</h2>" +
      "<h3>1. Pluie et alerte</h3><p>Pour chaque zone, on compare la pluie cumulée depuis le début de la saison (données satellites CHIRPS) à la normale calculée sur " +
      m.sources[0].baseline[0] + "–" + m.sources[0].baseline[1] + " pour la même période. Les niveaux d'alerte actuels sont : " + seuils +
      ". <b>Ces seuils sont provisoires</b> et doivent être calibrés avec la Météo, le BNGRC et le groupe IPC sur des crises passées.</p>" +
      "<h3>2. Population exposée</h3><p>Population des fokontany dont le niveau d'alerte atteint « " + esc(levelName(m.exposure_min_level)) + " » ou plus, puis cumul vers les communes, districts et régions.</p>" +
      "<h3>3. Cibles potentiels</h3><p>Population exposée × part vulnérable. Par défaut, la part vulnérable est de " + Math.round(m.default_vulnerable_share * 100) +
      " % (valeur provisoire, approximation fondée sur la pauvreté nationale). Par ordre de priorité, elle est remplacée (1) par les valeurs du fichier <code>inputs/vulnerabilite.csv</code>, puis (2) par la part de population en IPC phase 3 ou plus (OCHA/HAPI) là où une analyse existe, héritée par les sous-zones.</p>" +
      (m.has_history ? "<h3>Changement climatique et ENSO</h3><p>Pour chaque saison des pluies depuis 1982, la pluie CHIRPS est comparée à la normale " + m.sources[0].baseline[0] + "–" + m.sources[0].baseline[1] +
        ". La saison est classée <b>El Niño</b> (indice ONI de la NOAA moyen ≥ +0,5), <b>La Niña</b> (≤ −0,5) ou neutre. Pour chaque zone, l'outil calcule : la <b>tendance</b> de la pluie saisonnière (régression linéaire, points de % de la normale par décennie) et sa significativité ; la <b>pluie moyenne lors des El Niño et des La Niña passés</b> ; la <b>corrélation</b> avec l'ONI. " +
        "Limites : 40 à 45 saisons seulement (peu de saisons de chaque phase), classement ENSO simplifié, pluie satellitaire (CHIRPS) et non pluviomètres, et aucune projection climatique future à ce stade (modèles CMIP6 prévus). Ces résultats décrivent le passé : ils ne prédisent pas la prochaine saison.</p>" : "") +
      "<h3>4. Simulation « et si ? »</h3><p>La pluie cumulée observée est multipliée par un facteur (de ×" + m.rain_factors[0].toFixed(2).replace(".", ",") + " à ×" +
      m.rain_factors[m.rain_factors.length - 1].toFixed(2).replace(".", ",") + ") puis tous les calculs sont refaits. C'est une analyse de sensibilité : elle ne prédit pas la pluie à venir. La température, l'évaporation et le sol sont prévus aux phases suivantes.</p>" +
      "<h3>5. Limites connues</h3><ul><li>Population et limites des fokontany : estimations anciennes (référence " + esc(m.sources[2].reference_year) + ").</li>" +
      "<li>La pluie satellitaire est moins fiable dans les zones montagneuses et côtières ; à valider avec les stations.</li>" +
      "<li>Aucun chiffre ne remplace l'analyse officielle IPC ; l'outil prépare et met à jour entre deux cycles.</li></ul>" +
      "<p class='note'>Tout est reproductible : le code, les seuils et les fichiers de configuration sont publics dans le dépôt.</p>";
  }

  /* ---------- Démarrage ---------- */
  function showEmpty(msg) {
    $("through").textContent = "Données non disponibles";
    $("info").innerHTML = '<div class="note warn">' + esc(msg) + "</div>";
    $("map").innerHTML = '<div style="padding:30px"><h3>Première mise à jour en attente</h3><p>Les données de ce pays ne sont pas encore générées. ' +
      "Lancez le workflow « Mise à jour des données » dans l'onglet Actions du dépôt GitHub, puis rechargez cette page.</p></div>";
  }

  function init() {
    setupTabs();
    getJSON("meta.json").then(function (meta) {
      S.meta = meta;
      return getJSON("metrics/top.json");
    }).then(function (top) {
      S.top = top;
      $("country").textContent = S.meta.country;
      $("through").textContent = "Pluie jusqu'au " + fmtDate(S.meta.data_through);
      document.title = "MakyClimat — " + S.meta.country;
      renderEnso();
      setupMap(); setupControls();
      var hash = location.hash.replace("#", "").split("/").filter(Boolean).slice(0, 3);
      var p = hash.length ? ensureIndex().then(function () {
        S.path = hash.map(function (c) { return { pcode: c, name: S.nameOf[c] || c }; });
      }) : Promise.resolve();
      p.then(function () { render(true); });
      renderCatalogue().catch(function (e) { console.warn(e); });
      renderSources(); renderMethod();
    }).catch(function (e) { console.error(e); showEmpty("Chargement impossible : " + e.message); });
  }
  init();
})();
