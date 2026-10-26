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
              ev_n: ["#f7f4f9", "#d9c6e6", "#b08fd0", "#7e4fb0", "#4a1f80"], ev_p: ["#f7f4f9", "#d9c6e6", "#b08fd0", "#7e4fb0", "#4a1f80"],
              rb: ["#edf8e9", "#bae4b3", "#74c476", "#31a354", "#006d2c"], rp: ["#edf8e9", "#bae4b3", "#74c476", "#31a354", "#006d2c"], rf: ["#edf8e9", "#bae4b3", "#74c476", "#31a354", "#006d2c"],
              x: ["#f7f4f9", "#d4b9da", "#c994c7", "#dd3497", "#7a0177"] };
  var SIGNED_COLORS = ["#b2182b", "#ef8a62", "#f1f1f1", "#67a9cf", "#2166ac"];
  function styleOfLayer(k) {
    if (/^ew/.test(k)) return "ew";
    if (k === "cx") return "cx";
    if (k === "l") return "alert";
    if (k === "pc") return "pct";
    var d = layerDef(k);
    return d && d.ext && d.ext.style === "rainpct" ? "pct" : d && d.ext && d.ext.style === "signed" ? "signed" : "seq";
  }
  function layerDef(k) { return LAYERS.filter(function (l) { return l.id === k; })[0]; }
  function fmtLayer(k, v) {
    var d = layerDef(k);
    if (v === null || v === undefined) return "n/d";
    if (k === "cx") return Math.round(v) + " / 100";
    if (k === "rf") return MC.fmtInt(v) + " €";
    if (d && (d.fmt === "pct" || (d.ext && d.ext.format === "pct"))) return MC.fmtPct(v);
    if (d && d.ext && d.ext.format === "float") return (d.ext.style === "signed" && v > 0 ? "+" : "") + String(Math.round(v * 100) / 100).replace(".", ",");
    return MC.fmtInt(v);
  }
  var LAYERS = [
    { id: "l", label: "Niveau d'alerte sécheresse" }, { id: "pc", label: "Pluie cumulée (% de la normale)" },
    { id: "e", label: "Population exposée" }, { id: "t", label: "Cibles potentiels (estimation)" },
    { id: "g", label: "Écart : cibles moins bénéficiaires déclarés" }, { id: "p", label: "Population" },
    { id: "pa", label: "Probabilité d'alerte sécheresse en fin de saison", fmt: "pct" },
    { id: "ex", label: "Population exposée attendue (moyenne des saisons possibles)" },
    { id: "w", label: "Population exposée à l'excès de pluie (scénario humide ou choisi)" },
    { id: "ewm", label: "Alerte précoce : niveau maximal (7 prochains jours)", ew: true },
    { id: "ew0", label: "Alerte précoce : pluies fortes", ew: true }, { id: "ew4", label: "Alerte précoce : crue de rivière", ew: true },
    { id: "ew1", label: "Alerte précoce : vent fort", ew: true }, { id: "ew2", label: "Alerte précoce : forte chaleur", ew: true },
    { id: "ew3", label: "Alerte précoce : période sèche prolongée", ew: true }];
  var EW_COLORS = ["#d7ebd2", "#f2d16b", "#e8893a", "#b2262e"];
  var EW_ICON = { rain: "🌧", wind: "💨", heat: "🌡", dry: "☀", flood: "🌊" };
  var HAZ = ["rain", "wind", "heat", "dry", "flood"];

  var S = { meta: null, top: null, index: null, nameOf: {}, path: [], layer: "l", simIdx: null, scn: "", simple: false,
            view: null, selected: null, geo: null, breaks: [], map: null, cat: null, sector: "all", profile: "ong",
            mode: "single", layerB: "pc", scnB: "", sp: [], br: [], map2: null, geo2: null, hist: null, anc: null, hf: null, hagg: {}, evLayer: null,
            cx: { items: [{ k: "pc", w: 1, dir: -1 }, { k: "e", w: 1, dir: 1 }, { k: "", w: 1, dir: 1 }], op: "mean" } };

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
  function val(m, key) { return MC.valueFor(m, key, S.simIdx, S.meta, S.scn); }
  function isSim() { return S.simIdx !== null || !!S.scn; }
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

  /* ---------- Ergonomie : plein écran, panneau, légende, cartes repliables ---------- */
  function resizeMaps() {
    setTimeout(function () { if (S.map && S.map.invalidateSize) S.map.invalidateSize(); if (S.map2 && S.map2.invalidateSize) S.map2.invalidateSize(); }, 60);
  }
  function setupErgonomics() {
    var body = document.body, fs = $("fsbtn"), pb = $("panelbtn"), lg = $("lgtoggle"), box = $("legendbox");
    var small = false;
    try { small = window.matchMedia && window.matchMedia("(max-width: 860px)").matches; } catch (e) {}
    function sync() {
      fs.setAttribute("aria-pressed", body.classList.contains("mapfull") ? "true" : "false");
      fs.textContent = body.classList.contains("mapfull") ? "✕ Quitter le plein écran" : "⛶ Plein écran";
      pb.setAttribute("aria-pressed", body.classList.contains("nopanel") ? "false" : "true");
      lg.setAttribute("aria-expanded", box.classList.contains("closed") ? "false" : "true");
      lg.textContent = box.classList.contains("closed") ? "Légende ▸" : "Légende ▾";
      resizeMaps();
    }
    fs.addEventListener("click", function () {
      var on = !body.classList.contains("mapfull");
      body.classList.toggle("mapfull", on);
      if (on && small) body.classList.add("nopanel");   // sur téléphone : carte seule d'abord
      if (!on) body.classList.remove("nopanel");
      sync();
    });
    pb.addEventListener("click", function () { body.classList.toggle("nopanel"); sync(); });
    lg.addEventListener("click", function () { box.classList.toggle("closed"); sync(); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && body.classList.contains("mapfull")) { body.classList.remove("mapfull", "nopanel"); sync(); } });
    // rubriques du panneau repliables (clic sur le titre)
    document.querySelectorAll("#panel .card > h3, #panel > div > h3").forEach(function (h) {
      h.setAttribute("role", "button"); h.tabIndex = 0;
      function tog() { h.parentNode.classList.toggle("collapsed"); }
      h.addEventListener("click", tog);
      h.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); tog(); } });
    });
    if (small) box.classList.add("closed");            // téléphone : légende repliée au départ
    sync();
  }

  /* ---------- Bulles d'aide ---------- */
  var TIPS = {
    "#modebtn": "Version courte avec grands caractères : niveau d'alerte et conseils pour votre zone.",
    "#through": "Date jusqu'à laquelle les pluies observées sont à jour.",
    "#fcbadge": "Date de la dernière prévision météo utilisée.",
    "#enso": "Phase d'ENSO (El Niño / La Niña) : influence la pluie de la saison.",
    "label[for=q]": "Tapez un nom pour aller directement à la zone.",
    "label[for=layer]": "Choisissez ce que la carte colorie : pluie, sécheresse, inondation, cultures exposées…",
    "label[for=profile]": "Le tableau des risques s'adapte à votre métier ou situation.",
    "#scncard > h3": "Comparer une saison sèche, normale ou pluvieuse. Clic pour replier.",
    "#profcard > h3": "Choisissez votre profil pour des conseils adaptés. Clic pour replier.",
    "#hydcard > h3": "Humidité du sol, zones basses inondables et rivières. Clic pour replier.",
    "#cyccard > h3": "Trajectoires et zones de vent des cyclones passés. Clic pour replier.",
    "#histcard > h3": "Comparer la saison actuelle aux saisons passées. Clic pour replier.",
    "#respcard > h3": "Où agir en priorité selon le risque et la population. Clic pour replier.",
    "#whocard > h3": "Organisations présentes par zone et par secteur. Clic pour replier.",
    "#cmpcard > h3": "Deux cartes côte à côte, ou la différence entre deux périodes. Clic pour replier.",
    "#cxcard > h3": "Combiner jusqu'à 3 indicateurs en un indice de 0 à 100. Clic pour replier.",
    "#modeseg [data-mode=single]": "Une seule carte.",
    "#modeseg [data-mode=split]": "Deux cartes côte à côte, qui se déplacent ensemble.",
    "#modeseg [data-mode=diff]": "Carte de la différence : rouge = plus de risque en B, bleu = moins.",
    "#cxgo": "Calcule l'indice combiné et l'affiche sur la carte.",
    "#cxcopy": "Copie un lien qui rouvre exactement cette carte.",
    "#sim": "Multiplie la pluie observée pour tester une saison plus sèche ou plus humide. Pas une prévision.",
    "#simreset": "Revient aux données réellement observées.",
    "#export": "Télécharge les zones de cette vue au format CSV (Excel).",
    "#print": "Imprime la vue ou l'enregistre en PDF.",
    "#viewtitle": "Chiffres clés de la zone actuellement affichée.",
    "#fsbtn": "Agrandit la carte sur tout l'écran (Échap pour quitter).",
    "#panelbtn": "Masque ou affiche le panneau de détails.",
    "#lgtoggle": "Réduit ou affiche la légende des couleurs.",
    "#helpbtn": "Explication du site et de son fonctionnement.",
    "#crumbs": "Fil d'Ariane : cliquez pour remonter à une zone plus large."
  };
  function setupTips() {
    Object.keys(TIPS).forEach(function (sel) {
      document.querySelectorAll(sel).forEach(function (el) {
        el.setAttribute("data-tip", TIPS[sel]);
        if (!/^(button|select|input|a)$/i.test(el.tagName) && !el.hasAttribute("tabindex")) el.tabIndex = 0;
      });
    });
    var bub = document.createElement("div"); bub.id = "tipbubble"; bub.setAttribute("role", "tooltip"); document.body.appendChild(bub);
    var timer = null;
    function hide() { bub.classList.remove("on"); clearTimeout(timer); }
    function show(el) {
      var t = el.getAttribute("data-tip"); if (!t) return;
      bub.textContent = t; bub.classList.add("on");
      var r = el.getBoundingClientRect(), bw = bub.offsetWidth, bh = bub.offsetHeight;
      var x = Math.max(8, Math.min(r.left, window.innerWidth - bw - 8));
      var y = r.bottom + 8; if (y + bh > window.innerHeight - 8) y = Math.max(8, r.top - bh - 8);
      bub.style.left = x + "px"; bub.style.top = y + "px";
    }
    function target(e) { return e.target && e.target.closest ? e.target.closest("[data-tip]") : null; }
    document.addEventListener("mouseover", function (e) { var el = target(e); if (el) show(el); else hide(); });
    document.addEventListener("mouseout", function (e) { if (target(e)) hide(); });
    document.addEventListener("focusin", function (e) { var el = target(e); if (el) show(el); });
    document.addEventListener("focusout", hide);
    document.addEventListener("click", function () { hide(); });
    document.addEventListener("touchstart", function (e) {
      var el = target(e); if (!el) { hide(); return; }
      clearTimeout(timer); timer = setTimeout(function () { show(el); timer = setTimeout(hide, 3500); }, 450);
    }, { passive: true });
    document.addEventListener("touchend", function () { clearTimeout(timer); }, { passive: true });
    document.addEventListener("scroll", hide, true);
    $("helpbtn").addEventListener("click", function () {
      document.body.classList.remove("mapfull", "nopanel"); $("helptab").click(); window.scrollTo(0, 0);
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

  /* ---------- Cartes : une, deux côte à côte, ou différence ---------- */
  var HIGHER_WORSE = ["e", "t", "w", "g", "ex", "pa", "l", "ev_n", "ev_p", "rg"];
  var HIST_LAYERS = ["ev_n", "ev_p", "rb", "rg", "rp", "rf"];
  var CX_STEPS = [20, 40, 60, 80];

  function specA() { return { layer: S.layer, scn: S.scn, sim: S.simIdx }; }
  function specB() { return { layer: S.mode === "split" ? S.layerB : S.layer, scn: S.scnB, sim: null }; }
  function panes() {
    if (S.mode === "split") return [{ spec: specA(), tag: "A" }, { spec: specB(), tag: "B" }];
    if (S.mode === "diff") return [{ spec: { layer: S.layer, diff: [specA(), specB()], scn: S.scn, sim: null }, tag: "Δ" }];
    return [{ spec: specA(), tag: "A" }];
  }

  function plainVal(c, layer, scn, sim) {
    if (HIST_LAYERS.indexOf(layer) >= 0) {
      if (layer === "rg") {
        var t = MC.valueFor(S.view.metrics[c], "t", sim, S.meta, scn);
        return t === null || t === undefined ? null : Math.max(0, t - ((S.hagg.rb || {})[c] || 0));
      }
      return (S.hagg[layer] || {})[c] || 0;
    }
    return MC.valueFor(S.view.metrics[c], layer, sim, S.meta, scn);
  }

  function rankOf(sorted, v) {
    var lo = 0, hi = sorted.length;
    while (lo < hi) { var mid = (lo + hi) >> 1; if (sorted[mid] < v) lo = mid + 1; else hi = mid; }
    var a = lo; hi = sorted.length;
    while (lo < hi) { var m2 = (lo + hi) >> 1; if (sorted[m2] <= v) lo = m2 + 1; else hi = m2; }
    return (a + 0.5 * (lo - a)) / sorted.length;
  }

  // Indice composite : classement relatif (0 à 100) dans la vue de chaque indicateur, puis combinaison.
  function cxCompute(spec) {
    var items = S.cx.items.filter(function (it) { return it.k; }), op = S.cx.op;
    var cs = S.view.feats.map(function (f) { return f.properties.c; });
    var cols = items.map(function (it) { return cs.map(function (c) { return plainVal(c, it.k, spec.scn, spec.sim); }); });
    var sorted = cols.map(function (col) { return col.filter(function (v) { return v !== null && v !== undefined && isFinite(v); }).sort(function (a, b) { return a - b; }); });
    var out = { score: {}, parts: {} };
    cs.forEach(function (c, i) {
      var rs = [], ws = [], parts = [], ok = items.length > 0;
      items.forEach(function (it, j) {
        var v = cols[j][i];
        if (v === null || v === undefined || !isFinite(v) || !sorted[j].length) { ok = false; return; }
        var r = rankOf(sorted[j], v); if (it.dir < 0) r = 1 - r;
        rs.push(r); ws.push(it.w);
        parts.push({ k: it.k, v: v, r: Math.round(r * 100) });
      });
      if (!ok) { out.score[c] = null; return; }
      var sc = op === "max" ? Math.max.apply(null, rs) : op === "min" ? Math.min.apply(null, rs) :
        rs.reduce(function (a, r, j) { return a + r * ws[j]; }, 0) / ws.reduce(function (a, w) { return a + w; }, 0);
      out.score[c] = Math.round(sc * 1000) / 10;
      out.parts[c] = parts;
    });
    return out;
  }

  function specValue(c, spec) {
    if (spec.diff) {
      var a = specValue(c, spec.diff[0]), b = specValue(c, spec.diff[1]);
      return a !== null && b !== null && isFinite(a) && isFinite(b) ? b - a : null;
    }
    if (spec.layer === "cx") { if (!spec.cx) spec.cx = cxCompute(spec); var v = spec.cx.score[c]; return v === undefined ? null : v; }
    return plainVal(c, spec.layer, spec.scn, spec.sim);
  }
  function specStyle(spec) { return spec.diff ? "signed" : spec.layer === "cx" ? "cx" : styleOfLayer(spec.layer); }

  function breaksFor(spec) {
    var st = specStyle(spec);
    if (st === "alert" || st === "pct" || st === "ew" || st === "cx") return [];
    var vals = S.view.feats.map(function (f) { return specValue(f.properties.c, spec); });
    if (st === "signed") {
      var ab = vals.filter(function (x) { return x !== null && x !== undefined && isFinite(x); }).map(Math.abs).sort(function (a, b) { return a - b; });
      return ab.length ? [ab[Math.floor(ab.length * 0.4)], ab[Math.min(ab.length - 1, Math.floor(ab.length * 0.8))]] : [0, 0];
    }
    return MC.classBreaks(vals, 5);
  }

  function colorFor(f, spec, br) {
    var k = spec.layer, v = specValue(f.properties.c, spec), st = specStyle(spec);
    if (v === null || v === undefined) return "#cccccc";
    if (st === "cx") { var ci = 0; while (ci < CX_STEPS.length && v >= CX_STEPS[ci]) ci++; return SEQ.e[ci]; }
    if (st === "alert") return ALERT_COLORS[v] || "#cccccc";
    if (st === "ew") return EW_COLORS[v] || "#cccccc";
    if (st === "pct") { for (var i = 0; i < PCT_BINS.length; i++) if (v < PCT_BINS[i].max) return PCT_BINS[i].color; }
    if (st === "signed") {
      var b = br || [0, 0], pal = SIGNED_COLORS;
      if (spec.diff && (HIGHER_WORSE.indexOf(k) >= 0 || /^ew/.test(k))) pal = SIGNED_COLORS.slice().reverse();
      return v <= -b[1] ? pal[0] : v <= -b[0] ? pal[1] : v < b[0] ? pal[2] : v < b[1] ? pal[3] : pal[4];
    }
    if (v <= 0) return "#f2f2f2";
    var cj = MC.classIndex(v, br);
    return cj < 1 ? "#cccccc" : (SEQ[k] || SEQ.x)[Math.min(cj - 1, 4)];
  }

  function computeBreaks() {
    histAggregate();
    S.sp = panes().map(function (p) { p.spec.cx = null; return p.spec; });
    S.br = S.sp.map(breaksFor);
    S.breaks = S.br[0];
  }

  function styleFor(f, i) {
    var sel = S.selected && S.selected.properties.c === f.properties.c;
    return { fillColor: colorFor(f, S.sp[i], S.br[i]), fillOpacity: 0.78, color: sel ? "#000" : "#ffffff", weight: sel ? 3 : (S.view.lvl === 4 ? 0.6 : 1.2) };
  }
  function styleOf(f) { return styleFor(f, 0); }
  function styleOf2(f) { return styleFor(f, 1); }
  function restyleGeo() {
    if (S.geo) S.geo.setStyle(styleOf);
    if (S.geo2 && S.sp.length > 1) S.geo2.setStyle(styleOf2);
  }

  function buildGeo(map, i, old) {
    if (old) map.removeLayer(old);
    return L.geoJSON({ type: "FeatureCollection", features: S.view.feats }, {
      style: function (f) { return styleFor(f, i); },
      onEachFeature: function (f, layer) {
        layer.on("click", function () { onFeatureClick(f); });
        layer.bindTooltip(function () { return tipText(f, i); }, { sticky: true });
      } }).addTo(map);
  }

  function ensureMap2() {
    if (S.map2) return;
    var c = S.meta.map;
    S.map2 = L.map("map2", { zoomSnap: 0.25 }).setView(c.center, c.zoom);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: "© contributeurs OpenStreetMap" }).addTo(S.map2);
    var syncing = false;
    function link(from, to) {
      if (!from.on) return;
      from.on("move", function () {
        if (syncing || S.mode !== "split") return;
        syncing = true; to.setView(from.getCenter(), from.getZoom(), { animate: false }); syncing = false;
      });
    }
    link(S.map, S.map2); link(S.map2, S.map);
  }

  function applyMode() {
    var split = S.mode === "split";
    $("mapwrap").classList.toggle("split", split);
    $("map2").hidden = !split;
    $("cmpB").hidden = S.mode === "single";
    $("layerBrow").hidden = !split;
    $("cmpnote").textContent = S.mode === "split" ? "Les deux cartes se déplacent ensemble. Un clic sur l'une sélectionne la même zone sur l'autre."
      : S.mode === "diff" ? "Différence B moins A pour l'indicateur choisi ci-dessus (période A = « Scénario ou saison » du haut ; période B = ci-dessous). Rouge : plus de risque en B ; bleu : moins." : "";
    if (S.mode === "split") ensureMap2();
    document.querySelectorAll("#modeseg button").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.mode === S.mode ? "true" : "false"); });
    setTimeout(function () { if (S.map.invalidateSize) S.map.invalidateSize(); if (S.map2 && S.map2.invalidateSize) S.map2.invalidateSize(); }, 30);
    if (S.view) { render(false); }
    syncURL();
  }

  function render(fit) {
    loadView().then(function (v) {
      if (!v.feats.length) { S.path.pop(); alert("Aucune sous-zone disponible pour cette unité."); return; }
      S.view = v;
      if (S.selected && !v.feats.some(function (f) { return f.properties.c === S.selected.properties.c; })) S.selected = null;
      computeBreaks();
      S.geo = buildGeo(S.map, 0, S.geo);
      if (S.mode === "split") { ensureMap2(); S.geo2 = buildGeo(S.map2, 1, S.geo2); }
      else if (S.geo2) { S.map2.removeLayer(S.geo2); S.geo2 = null; }
      if (fit !== false) { S.map.fitBounds(S.geo.getBounds(), { padding: [20, 20] }); if (S.map2) S.map2.fitBounds(S.geo.getBounds(), { padding: [20, 20] }); }
      refresh();
      location.hash = S.path.map(function (p) { return p.pcode; }).join("/");
    }).catch(function (e) { console.error(e); alert("Erreur de chargement : " + e.message); });
  }

  function restyle() { if (!S.view) return; computeBreaks(); restyleGeo(); refresh(); syncURL(); }

  function specTitle(spec) {
    if (spec.diff) return "Différence B − A : " + layerDef(spec.layer).label + " (" + periodName(spec.diff[1].scn) + " moins " + periodName(spec.diff[0].scn) + ")";
    return layerDef(spec.layer).label + " — " + periodName(spec.scn, spec.sim);
  }
  function periodName(scn, sim) {
    if (scn) return scnShort(scn);
    if (sim !== null && sim !== undefined) return "pluie × " + S.meta.rain_factors[sim].toFixed(2).replace(".", ",");
    return S.meta.scenarios && S.meta.scenarios.observed_share > 0 ? "observé à ce jour" : "situation de référence";
  }

  function tipText(f, i) {
    i = i || 0;
    var spec = S.sp[i], c = f.properties.c, v = specValue(c, spec), k = spec.layer;
    var head = "<b>" + esc(f.properties.n) + "</b><br>";
    if (spec.diff) {
      var a = specValue(c, spec.diff[0]), b = specValue(c, spec.diff[1]);
      return head + esc(layerDef(k).label) + "<br>A : " + fmtLayer(k, a) + " · B : " + fmtLayer(k, b) + "<br><b>B − A : " + (v === null ? "n/d" : (v > 0 ? "+" : "") + fmtLayer(k, v)) + "</b>";
    }
    if (k === "cx") {
      var parts = (spec.cx && spec.cx.parts[c]) || [];
      return head + "Indice couplé : <b>" + (v === null ? "n/d" : Math.round(v) + " / 100") + "</b>" +
        parts.map(function (p) { return "<br>" + esc(layerDef(p.k).label) + " : " + fmtLayer(p.k, p.v) + " (rang " + p.r + ")"; }).join("");
    }
    var txt = k === "l" ? levelName(v) : k === "pc" ? MC.fmtPct(v) : /^ew/.test(k) ? S.meta.forecast.level_names[v] : fmtLayer(k, v);
    return head + esc(layerDef(k).label) + (S.mode === "split" ? " (" + (i ? "B" : "A") + ")" : "") + " : " + txt;
  }

  function onFeatureClick(f) {
    var same = S.selected && S.selected.properties.c === f.properties.c;
    if (same && S.view.lvl < 4) return drill(f);
    S.selected = f;
    restyleGeo();
    renderInfo();
  }

  function drill(f) {
    S.path.push({ pcode: f.properties.c, name: f.properties.n });
    S.selected = null;
    render(true);
  }

  /* ---------- Panneau ---------- */
  function refresh() { renderCrumbs(); renderLegend(); renderKPIs(); renderInfo(); renderRank(); renderResponse(); renderWho(); }

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

  function legendFor(spec, br, tag) {
    var k = spec.layer, h = "<b>" + (tag ? tag + " · " : "") + esc(spec.diff ? "Différence B − A" : layerDef(k).label) + "</b>";
    var st = specStyle(spec);
    if (spec.diff) h += '<div><i style="background:#fff"></i> <em>' + esc(layerDef(k).label) + " : " + esc(periodName(spec.diff[1].scn)) + " moins " + esc(periodName(spec.diff[0].scn)) + "</em></div>";
    else if (spec.scn) h += '<div><i style="background:#fff"></i> <em>' + (isHist(spec.scn) ? "saison passée : " : "scénario : ") + esc(scnLabel(spec.scn)) + "</em></div>";
    else if (spec.sim !== null && spec.sim !== undefined) h += '<div><i style="background:#fff"></i> <em>scénario : pluie × ' + S.meta.rain_factors[spec.sim].toFixed(2).replace(".", ",") + "</em></div>";
    if (st === "cx") {
      var lab = ["0 à 20 : faible", "20 à 40", "40 à 60", "60 à 80", "80 à 100 : très élevé"];
      lab.forEach(function (t, i) { h += '<div><i style="background:' + SEQ.e[i] + '"></i>' + t + "</div>"; });
      var opn = { mean: "moyenne pondérée", max: "au moins un indicateur élevé", min: "tous les indicateurs élevés à la fois" }[S.cx.op];
      h += '<div class="note">Classement relatif dans cette vue (' + opn + ") de : " + S.cx.items.filter(function (it) { return it.k; }).map(function (it) { return esc(layerDef(it.k).label) + (it.dir < 0 ? " (inversé)" : "") + (S.cx.op === "mean" ? " ×" + it.w : ""); }).join(" ; ") + ".</div>";
    } else if (st === "alert") {
      [1, 2, 3, 4, 0].forEach(function (l) { h += '<div><i style="background:' + ALERT_COLORS[l] + '"></i>' + esc(levelName(l)) + "</div>"; });
    } else if (st === "ew") {
      S.meta.forecast.level_names.forEach(function (nm, i) { h += '<div><i style="background:' + EW_COLORS[i] + '"></i>' + esc(nm) + "</div>"; });
      h += '<div class="note">Prévision météo, 7 prochains jours. Seuils provisoires ; alertes officielles : Météo Madagascar et BNGRC.</div>';
    } else if (st === "signed") {
      var sb = br || [0, 0], pal = SIGNED_COLORS;
      var dry, wet;
      if (spec.diff) {
        var rev = HIGHER_WORSE.indexOf(k) >= 0;
        pal = rev ? SIGNED_COLORS.slice().reverse() : SIGNED_COLORS;
        h += '<div><i style="background:' + pal[0] + '"></i>' + "baisse forte (au-delà de " + fmtLayer(k, -sb[1]) + ")</div>" +
          '<div><i style="background:' + pal[1] + '"></i>baisse modérée</div>' +
          '<div><i style="background:' + pal[2] + '"></i>proche de zéro (±' + fmtLayer(k, sb[0]).replace("+", "") + ")</div>" +
          '<div><i style="background:' + pal[3] + '"></i>hausse modérée</div>' +
          '<div><i style="background:' + pal[4] + '"></i>hausse forte (au-delà de +' + fmtLayer(k, sb[1]).replace("+", "") + ")</div>" +
          '<div class="note">' + (rev ? "Rouge = plus de risque ou de personnes en B." : "Rouge = plus sec en B ; bleu = plus humide en B.") + "</div>";
      } else {
        dry = layerDef(k).ext.id.indexOf("corr") >= 0 ? "corrélation négative (moins de pluie quand l'ONI monte)" : "baisse";
        wet = layerDef(k).ext.id.indexOf("corr") >= 0 ? "corrélation positive" : "hausse";
        h += '<div><i style="background:' + pal[0] + '"></i>' + dry + " forte (au-delà de " + fmtLayer(k, -sb[1]) + ")</div>" +
          '<div><i style="background:' + pal[1] + '"></i>' + dry + " modérée</div>" +
          '<div><i style="background:' + pal[2] + '"></i>proche de zéro (±' + fmtLayer(k, sb[0]).replace("+", "") + ')</div>' +
          '<div><i style="background:' + pal[3] + '"></i>' + wet + " modérée</div>" +
          '<div><i style="background:' + pal[4] + '"></i>' + wet + " forte (au-delà de +" + fmtLayer(k, sb[1]).replace("+", "") + ")</div>";
      }
    } else if (st === "pct") {
      PCT_BINS.forEach(function (b) { h += '<div><i style="background:' + b.color + '"></i>' + b.label + "</div>"; });
    } else {
      var pal2 = SEQ[k] || SEQ.x;
      h += '<div><i style="background:#f2f2f2"></i>zéro</div>';
      var edges = [0].concat(br);
      edges.forEach(function (e, i) {
        var next = br[i];
        var lab = i === 0 ? "moins de " + fmtLayer(k, br[0] || 0) : fmtLayer(k, e) + (next ? " à " + fmtLayer(k, next) : " et plus");
        if (br.length) h += '<div><i style="background:' + pal2[Math.min(i, 4)] + '"></i>' + lab + "</div>";
      });
    }
    return h;
  }

  function renderLegend() {
    var multi = S.sp.length > 1;
    $("legend").innerHTML = S.sp.map(function (sp, i) { return legendFor(sp, S.br[i], multi ? (i ? "B" : "A") : ""); }).join('<hr class="lgsep">');
    var ha = $("hdrA"), hb = $("hdrB");
    ha.hidden = S.mode === "single"; hb.hidden = S.mode !== "split";
    if (S.mode !== "single") ha.textContent = (S.mode === "diff" ? "" : "A · ") + specTitle(S.sp[0]);
    if (S.mode === "split") hb.textContent = "B · " + specTitle(S.sp[1]);
  }

  function sumView(key, sim, scn) {
    var s = 0, any = false;
    S.view.feats.forEach(function (f) {
      var v = MC.valueFor(S.view.metrics[f.properties.c], key, sim, S.meta, scn);
      if (v !== null && isFinite(v)) { s += v; any = true; }
    });
    return any ? s : null;
  }

  function renderKPIs() {
    var parent = S.path.length ? S.path[S.path.length - 1].name : S.meta.country;
    $("viewtitle").textContent = "Vue : " + parent + " (" + S.meta.levels[S.view.lvl].plural.toLowerCase() + ")";
    var h = "";
    [["p", "Population"], ["e", "Exposés"], ["t", "Cibles potentiels"]].forEach(function (x) {
      var obs = sumView(x[0], null, ""), sim = !isSim() ? null : sumView(x[0], S.simIdx, S.scn);
      h += '<div class="kpi' + (sim !== null && x[0] !== "p" ? " sim" : "") + '"><b>' + MC.fmtInt(sim !== null && x[0] !== "p" ? sim : obs) +
           "</b><span>" + x[1] + (sim !== null && x[0] !== "p" ? " (scénario)" : "") + "</span></div>";
    });
    $("kpis").innerHTML = h;
  }

  function row(a, b) { return '<div class="row"><span>' + a + "</span><span>" + b + "</span></div>"; }

  function renderInfo() {
    var f = S.selected, box = $("info");
    if (!f && S.simple) { box.innerHTML = "<h3>Chez moi</h3><p class='bigprompt'>Tapez le nom de votre fokontany, de votre commune ou de votre district dans la recherche, ou touchez votre zone sur la carte.</p>"; return; }
    if (!f) { box.innerHTML = '<div class="note">Cliquez sur une zone de la carte pour voir ses indicateurs. Cliquez une seconde fois pour explorer ses sous-zones.</div>'; return; }
    var m = S.view.metrics[f.properties.c] || {};
    if (S.simple) { box.innerHTML = simpleCard(f, m); return; }
    var lvlLabel = S.meta.levels[S.view.lvl].label;
    var h = "<h3>" + esc(lvlLabel) + "</h3><div style='font-size:17px;font-weight:700;margin-bottom:6px'>" + esc(f.properties.n) + "</div>";
    h += row("Population (estimation)", MC.fmtInt(m.p));
    if (m.pc !== undefined) {
      h += row("Pluie de la saison", MC.fmtInt(m.a) + " mm sur " + MC.fmtInt(m.n) + " mm normaux");
      h += row("% de la normale", MC.fmtPct(m.pc) + (isSim() ? " → <b>" + MC.fmtPct(val(m, "pc")) + "</b>" : ""));
    } else h += row("Pluie de la saison", "pas assez de données (début de saison ou hors couverture)");
    h += row("Niveau d'alerte", esc(levelName(m.l)) + (isSim() ? " → <b>" + esc(levelName(val(m, "l"))) + "</b>" : ""));
    h += row("Population exposée", MC.fmtInt(m.e) + (isSim() ? " → <b>" + MC.fmtInt(val(m, "e")) + "</b>" : ""));
    h += row("Cibles potentiels", MC.fmtInt(m.t) + (isSim() ? " → <b>" + MC.fmtInt(val(m, "t")) + "</b>" : ""));
    if (m.vs !== undefined) h += row("Part vulnérable retenue", Math.round(m.vs * 100) + " % " +
      (m.vi === 1 ? "(donnée fournie)" : m.vi === 2 ? "(IPC phase 3 ou plus)" : "(valeur par défaut provisoire)"));
    (S.meta.external || []).forEach(function (x) {
      var xv = m.x ? m.x[x.id] : undefined;
      if (xv !== undefined) h += row(x.label, fmtLayer("x:" + x.id, xv));
    });
    h += forecastSection(m) + risksSection(m, false) + alertsSection(m) + shockSection(m) + scenarioTable(m) + seasonSection(f) + calendarSection(f) + hydroSection(f) + soilSection(f) + histSection(f);
    if (S.meta.has_history) h += '<div id="histbox" class="hist"></div>';
    h += planSection(m);
    if (m.b) h += row("Bénéficiaires déclarés", MC.fmtInt(m.b)) + row("Écart restant", MC.fmtInt(val(m, "g")));
    if (S.view.lvl === 4) h += '<div class="note warn" style="margin-top:6px">Au niveau fokontany, les limites et la population sont des estimations anciennes : à utiliser comme indication à confirmer sur le terrain.</div>';
    if (S.view.lvl < 4) h += '<div style="margin-top:8px"><button class="btn primary" id="drillbtn">Explorer les sous-zones ▸</button></div>';
    box.innerHTML = h;
    var db = $("drillbtn");
    if (db) db.addEventListener("click", function () { drill(f); });
    if (S.meta.has_history && !S.simple) drawHistory(f);
  }

  function renderRank() {
    var rows = S.view.feats.map(function (f) {
      return { f: f, v: val(S.view.metrics[f.properties.c], "t") };
    }).filter(function (r) { return r.v !== null && r.v > 0; })
      .sort(function (a, b) { return b.v - a.v; }).slice(0, 10);
    var h = "<tr><th>Zone</th><th>Cibles potentiels" + (isSim() ? " (scénario)" : "") + "</th></tr>";
    if (!rows.length) h += '<tr><td colspan="2" class="note">Aucune zone exposée dans cette vue.</td></tr>';
    rows.forEach(function (r, i) {
      h += '<tr class="link" data-i="' + i + '"><td>' + esc(r.f.properties.n) + "</td><td>" + MC.fmtInt(r.v) + "</td></tr>";
    });
    $("rank").innerHTML = h;
    $("rank").querySelectorAll("tr.link").forEach(function (tr) {
      tr.addEventListener("click", function () {
        var f = rows[+tr.dataset.i].f;
        S.selected = f; restyleGeo(); renderInfo();
        S.geo.eachLayer(function (l) { if (l.feature.properties.c === f.properties.c) S.map.fitBounds(l.getBounds(), { padding: [40, 40], maxZoom: 11 }); });
      });
    });
  }


  /* ---------- Scénarios de fin de saison ---------- */
  function isHist(id) { return typeof id === "string" && id.indexOf("y:") === 0; }
  function seasonLabel(y) {
    var sc = S.meta.scenarios, i = sc.hist_years.indexOf(+y), ph = sc.hist_phases ? sc.hist_phases[i] : "";
    return "Saison " + (y - 1) + "–" + y + (ph && PHASE_NAMES[ph] && ph !== "N" ? " · " + PHASE_NAMES[ph] : "");
  }
  function scnLabel(id) {
    if (isHist(id)) return seasonLabel(id.slice(2)) + " (observée)";
    var l = ((S.meta.scenarios || {}).list || []).filter(function (x) { return x.id === id; })[0];
    return l ? l.label : id;
  }
  function scnShort(id) {
    if (isHist(id)) return seasonLabel(id.slice(2));
    var l = ((S.meta.scenarios || {}).list || []).filter(function (x) { return x.id === id; })[0];
    return l ? l.short : id;
  }
  function setupScenarios() {
    var sc = S.meta.scenarios;
    if (!sc) return;
    $("scncard").hidden = false;
    $("scnseason").textContent = sc.season.replace("-", "–");
    var sel = $("scn");
    sel.innerHTML = "";
    var o0 = document.createElement("option"); o0.value = ""; o0.textContent = sc.observed_share > 0 ? "Observé à ce jour (sans scénario)" : "Aucun (situation de référence)";
    sel.appendChild(o0);
    var g1 = document.createElement("optgroup"); g1.label = "Scénarios de la saison à venir";
    sc.list.forEach(function (l) { var o = document.createElement("option"); o.value = l.id; o.textContent = l.label; g1.appendChild(o); });
    sel.appendChild(g1);
    if (sc.hist_years) {
      var g2 = document.createElement("optgroup"); g2.label = "Saisons passées (pluie réellement observée)";
      sc.hist_years.slice().reverse().forEach(function (y) { var o = document.createElement("option"); o.value = "y:" + y; o.textContent = seasonLabel(y); g2.appendChild(o); });
      sel.appendChild(g2);
    }
    var obs = sc.observed_share > 0 ? "Les pluies déjà tombées (" + Math.round(sc.observed_share * 100) + " % de la saison écoulée) sont conservées ; " : "La saison n'a pas encore commencé : ";
    $("scnnote").innerHTML = esc(obs) + "la pluie restante est celle de chacune des " + sc.n_years + " saisons passées (" + sc.years[0] + "–" + sc.years[1] + "). " +
      "Ce n'est pas une prévision météo : ce sont des situations qui se sont déjà produites. Une « saison passée » montre la pluie réellement tombée cette année-là, avec les seuils d'alerte et la population d'aujourd'hui." +
      (sc.weighted_by_forecast ? " Les années sont pondérées par la prévision saisonnière fournie." : "") +
      (sc.cascade && sc.cascade.used ? " La prévision météo est intégrée jusqu'au " + fmtDate(sc.cascade.known_through) + " (elle remplace le climat sur cette période)." : "");
    sel.addEventListener("change", function () {
      S.scn = sel.value;
      if (S.scn) { $("sim").value = S.meta.rain_factors.indexOf(1); S.simIdx = null; $("simlabel").textContent = "observée"; }
      restyle();
    });
  }

  function planSection(m) {
    var pb = S.meta.playbook, sc = m.sc;
    if (!pb || !sc) return "";
    var hist = isHist(S.scn);
    var basis = hist ? S.scn : S.scn && sc[S.scn] ? S.scn : "sec";
    var e = hist ? (val(m, "e") || 0) : sc[basis][2], w = hist ? (val(m, "w") || 0) : sc[basis][4], h = '<div class="plan"><h3>Plan d\'action recommandé</h3>' +
      '<div class="note">Planification sur le scénario : <b>' + esc(scnLabel(basis)) + "</b>. Pistes génériques à valider avec les clusters : elles complètent les outils et alertes de chaque secteur, sans les remplacer.</div>";
    var names = {};
    (S.meta.sector_names || []).forEach(function (x) { names[x.id] = x.label; });
    Object.keys(pb.sectors).forEach(function (id) {
      var sec = pb.sectors[id], n = Math.round(e * sec.share);
      var li = function (arr) { return arr.map(function (t) { return "<li>" + esc(t) + "</li>"; }).join(""); };
      h += "<details><summary><b>" + esc(names[id] || id) + "</b> : " + (n > 0 ? "≈ " + MC.fmtInt(n) + " personnes à cibler" : "pas de population en alerte dans ce scénario") + "</summary>" +
        '<div class="note">' + esc(sec.share_note) + "</div>" +
        (n > 0 ? "<b>Anticiper</b><ul>" + li(sec.anticipation) + "</ul><b>Limiter l'impact</b><ul>" + li(sec.mitigation) + "</ul><b>Répondre</b><ul>" + li(sec.response) + "</ul><b>Renforcer la résilience</b><ul>" + li(sec.resilience) + "</ul>" : "<ul>" + li(sec.resilience) + "</ul>") +
        "</details>";
    });
    if (w > 0) h += "<details><summary><b>Excès de pluie</b> : ≈ " + MC.fmtInt(w) + " personnes en zone très pluvieuse</summary><ul>" + pb.wet.map(function (t) { return "<li>" + esc(t) + "</li>"; }).join("") +
      '</ul><div class="note">Indicateur pluviométrique simple (pluie finale ≥ ' + S.meta.scenarios.wet_threshold_pct + " % de la normale), pas une prévision de crue.</div></details>";
    return h + "</div>";
  }

  function scenarioTable(m) {
    var sc = m.sc;
    if (!sc) return "";
    var ids = S.meta.scenarios.list.map(function (x) { return x.id; }).filter(function (id) { return sc[id]; });
    var h = '<div class="sctable"><h3>Scénarios de la saison ' + esc(S.meta.scenarios.season.replace("-", "–")) + "</h3>";
    if (m.pa !== undefined && m.pa !== null) h += row("Probabilité d'alerte ou pire", Math.round(m.pa * 100) + " % des saisons possibles") + row("Exposés attendus (moyenne)", MC.fmtInt(m.ex));
    h += "<table><tr><th>Scénario</th><th>Pluie</th><th>Niveau</th><th>Exposés</th><th>Cibles</th></tr>";
    ids.forEach(function (id) {
      var r = sc[id];
      h += "<tr" + (S.scn === id ? ' class="cur"' : "") + "><td>" + esc(scnShort(id)) + "</td><td>" + (r[0] === null ? "n/d" : Math.round(r[0]) + " %") + "</td><td>" + esc(levelName(r[1])) +
        "</td><td>" + MC.fmtInt(r[2]) + "</td><td>" + MC.fmtInt(r[3]) + "</td></tr>";
    });
    return h + "</table></div>";
  }

  function alertsSection(m) {
    if (!m.al) return "";
    var h = '<div class="sectoralerts"><h3>Alertes déjà émises par les secteurs</h3><div class="note">Affichées telles que fournies : MakyClimat ne les remplace pas.</div>';
    var names = {};
    (S.meta.sector_names || []).forEach(function (x) { names[x.id] = x.label; });
    m.al.forEach(function (a) {
      h += '<div class="row"><span><b>' + esc(names[a[0]] || a[0]) + "</b> : " + esc(a[2]) + " <em>(" + esc(a[3]) + (a[4] ? ", " + esc(a[4]) : "") + ")</em></span><span>niveau " + a[1] + "</span></div>";
    });
    return h + "</div>";
  }


  /* ---------- Risques par profil et par horizon ---------- */
  var SIGNAL = ["Aucun signal", "Signal faible", "Signal net", "Signal fort"];
  var LONG_TODO = "Données à intégrer";

  function lvlToChip(l) { return l >= 4 ? 3 : l === 3 ? 2 : l === 2 ? 1 : 0; }

  function slideThreshold(hours) { var T = S.meta.risks.landslide_threshold; return T.a * Math.pow(hours, 1 + T.b); }
  function steepShare(m) { var v = m.x ? m.x.slope_ge15_pct : undefined; return v === undefined ? null : v; }
  function riskSlide(m) {
    var T = S.meta.risks.landslide_threshold, F = S.meta.forecast, sl = steepShare(m);
    if (!F || !m.ev) return { none: "Prévision non disponible" };
    if (sl === null) return { none: "Pente non calculée (lancer le workflow « 5 - Hydrologie »)" };
    var t24 = slideThreshold(24), t72 = slideThreshold(72), r = Math.max(m.ev[0] / t24, m.ev[1] / t72);
    var steep = Math.round(sl * 10) / 10, txt = "pluie prévue " + String(m.ev[0]).replace(".", ",") + " mm/jour et " + String(m.ev[1]).replace(".", ",") + " mm/3 jours = " +
      String(Math.round(r * 10) / 10).replace(".", ",") + " × le seuil mondial de déclenchement (" + Math.round(t24) + " mm/jour, " + Math.round(t72) + " mm/3 jours) ; " + String(steep).replace(".", ",") + " % du territoire en pente ≥ 15 %";
    if (sl < T.min_share_pct) return { chip: 0, label: "Aucun signal", text: "terrain presque plat (" + String(steep).replace(".", ",") + " % en pente ≥ 15 %)" };
    var c = r >= 3 ? 3 : r >= 2 ? 2 : r >= 1 ? 1 : 0;
    return { chip: c, label: ["Aucun signal", "Vigilance", "Alerte", "Alerte maximale"][c], text: txt, pop: S.view.lvl < 4 && m.ewp ? m.ewp[0] : 0, proxy: true };
  }

  function riskCourt(spec, m) {
    var F = S.meta.forecast;
    if (spec.rule === "landslide") return riskSlide(m);
    if (spec.status === "todo") return { todo: true };
    if (!F || !m.ew) return { none: "Prévision non disponible" };
    var best = 0, bh = null, pop = 0;
    spec.from.forEach(function (hz) {
      var i = HAZ.indexOf(hz);
      if (i >= 0 && m.ew[i] > best) { best = m.ew[i]; bh = hz; }
      if (i >= 0 && m.ewp && m.ewp[i] > pop) pop = m.ewp[i];
    });
    return { chip: best, label: best ? F.level_names[best] : "Aucun signal", text: bh ? ewMessage(bh, m) : "", pop: S.view.lvl < 4 ? pop : 0, proxy: spec.status === "proxy" };
  }

  function riskMoyen(spec, m) {
    var sc = S.meta.scenarios;
    if (spec.status === "todo") return { todo: true };
    if (!sc || !m.sc) return { none: "Scénarios non disponibles" };
    var wetThr = sc.wet_threshold_pct || 130;
    function one(id) {
      var v = m.sc[id];
      if (!v || v[0] === null || v[0] === undefined) return null;
      if (id === "sec") return { chip: lvlToChip(v[1]), text: "saison sèche : " + Math.round(v[0]) + " % de la normale", pop: v[2] };
      var c = v[0] >= wetThr + 20 ? 3 : v[0] >= wetThr ? 2 : v[0] >= wetThr - 15 ? 1 : 0;
      return { chip: c, text: "saison humide : " + Math.round(v[0]) + " % de la normale", pop: v[4] };
    }
    var a = one(spec.scenario), b = spec.scenario_alt ? one(spec.scenario_alt) : null;
    var r = !a ? b : (!b || a.chip >= b.chip ? a : b);
    if (!r) return { none: "Pas assez de données" };
    if (spec.gate === "slope") {
      var sl = steepShare(m), T = S.meta.risks.landslide_threshold;
      if (sl === null) return { none: "Pente non calculée (lancer le workflow « 5 - Hydrologie »)" };
      if (sl < T.min_share_pct) return { chip: 0, label: "Aucun signal", text: "terrain presque plat" };
      r.text += " ; " + String(Math.round(sl * 10) / 10).replace(".", ",") + " % du territoire en pente ≥ 15 %";
    }
    var names = ["Aucun signal", "Vigilance", "Alerte", "Alerte maximale"];
    return { chip: r.chip, label: names[r.chip], text: r.text, pop: S.view.lvl < 4 ? r.pop : 0, proxy: spec.status === "proxy" };
  }

  function riskLong(spec, m) {
    if (spec.status === "todo") return { todo: true };
    var x = m.x || {};
    var tr = x.rain_trend_pct_decade, el = x.enso_el_pct, la = x.enso_la_pct;
    if (tr === undefined && el === undefined && la === undefined) return { none: "Pas assez de données" };
    var c = 0, parts = [];
    var dry = (tr !== undefined && tr <= -2 ? 1 : 0) + (tr !== undefined && tr <= -5 ? 1 : 0) + (el !== undefined && el <= 85 ? 1 : 0);
    var wet = (tr !== undefined && tr >= 2 ? 1 : 0) + (tr !== undefined && tr >= 5 ? 1 : 0) + (la !== undefined && la >= 120 ? 1 : 0);
    c = spec.kind === "dry" ? dry : spec.kind === "wet" ? wet : Math.max(dry, wet);
    if (tr !== undefined) parts.push("tendance " + (tr > 0 ? "+" : "") + String(Math.round(tr * 10) / 10).replace(".", ",") + " % de pluie par décennie");
    if (spec.kind !== "wet" && el !== undefined) parts.push("El Niño passés : " + Math.round(el) + " % de la normale");
    if (spec.kind !== "dry" && la !== undefined) parts.push("La Niña passées : " + Math.round(la) + " % de la normale");
    return { chip: Math.min(3, c), label: SIGNAL[Math.min(3, c)], text: parts.join(" ; "), proxy: spec.status === "proxy" };
  }

  function riskCell(c, longTerm) {
    if (c.todo) return '<td class="rtodo">' + LONG_TODO + "</td>";
    if (c.none) return '<td class="rnone">' + esc(c.none) + "</td>";
    return '<td><span class="rchip" style="background:' + EW_COLORS[c.chip] + (c.chip === 3 ? ";color:#fff" : "") + '">' + esc(c.label) + "</span>" +
      (c.proxy ? ' <span class="rproxy" title="Indicateur indirect : voir « données à intégrer »">indicatif</span>' : "") +
      (c.text ? '<div class="rtxt">' + esc(c.text) + "</div>" : "") +
      (c.pop > 0 ? '<div class="rpop">≈ ' + MC.fmtInt(c.pop) + " pers.</div>" : "") + "</td>";
  }

  function risksSection(m, forSimple) {
    var R = S.meta.risks;
    if (!R) return "";
    var prof = R.profiles.filter(function (p) { return p.id === S.profile; })[0] || R.profiles[0];
    var h = '<div class="risks"><h3>Risques pour : ' + esc(prof.label) + "</h3>" +
      '<div class="tablewrap"><table class="rtab"><thead><tr><th>Risque</th><th>7 jours</th><th>Saison</th><th>Climat (long terme)</th></tr></thead><tbody>';
    var dmg = "", needs = "";
    prof.hazards.forEach(function (id) {
      var hz = R.hazards[id];
      if (!hz) return;
      h += "<tr><th scope='row'>" + hz.icon + " " + esc(hz.label) + "</th>" + riskCell(riskCourt(hz.court, m)) + riskCell(riskMoyen(hz.moyen, m)) + riskCell(riskLong(hz.long, m)) + "</tr>";
      var any = ["court", "moyen", "long"].some(function (k) { return hz.damages[k] && hz.damages[k].length; });
      if (any && !forSimple) {
        dmg += "<div class='dmg'><b>" + hz.icon + " " + esc(hz.label) + "</b>";
        [["court", "Court terme (jours)"], ["moyen", "Moyen terme (saison)"], ["long", "Long terme (années)"]].forEach(function (k) {
          if (hz.damages[k[0]] && hz.damages[k[0]].length) dmg += "<div><i>" + k[1] + " :</i> " + hz.damages[k[0]].map(esc).join(" ; ") + "</div>";
        });
        dmg += "</div>";
      }
      if (hz.needs && [hz.court, hz.moyen, hz.long].some(function (s) { return s.status !== "live"; })) needs += "<li><b>" + esc(hz.label) + " :</b> " + esc(hz.needs) + "</li>";
    });
    h += "</tbody></table></div>";
    if (!forSimple && dmg) h += "<details><summary>Dégâts possibles (indicatif)</summary>" + dmg + "<div class='note'>Liste qualitative provisoire, à valider avec les clusters et les services techniques ; elle ne chiffre pas les dommages.</div></details>";
    if (needs) h += "<details><summary>Données à intégrer pour compléter ce tableau</summary><ul class='advice'>" + needs + "</ul></details>";
    h += "<div class='note'>« Indicatif » = indicateur indirect (par exemple la pluie comme déclencheur d'éboulement). Les alertes officielles du BNGRC et de Météo Madagascar priment.</div></div>";
    return h;
  }

  function setupProfiles() {
    var R = S.meta.risks;
    if (!R) return;
    $("profcard").hidden = false;
    var sel = $("profile");
    R.profiles.forEach(function (p) { var o = document.createElement("option"); o.value = p.id; o.textContent = p.label; sel.appendChild(o); });
    sel.value = S.profile;
    sel.addEventListener("change", function () { S.profile = sel.value; renderInfo(); });
  }

  function simpleCard(f, m) {
    var sc = S.meta.scenarios, pb = S.meta.playbook;
    var name = esc(f.properties.n);
    if (!sc || !m.sc || m.pa === undefined || m.pa === null) {
      return "<h3>Chez moi</h3><div class='bigname'>" + name + "</div><p>Pas assez de données pour cette zone.</p>";
    }
    var pa = m.pa, tier = pa >= 0.5 ? ["élevé", "#b2262e"] : pa >= 0.25 ? ["moyen", "#e8893a"] : ["faible", "#3b8a3e"];
    var tenth = Math.round(pa * 10);
    var wet = m.sc.hum && m.p && m.sc.hum[4] > 0.2 * m.p;
    var h = "<h3>Chez moi</h3><div class='bigname'>" + name + "</div>" + simpleAlerts(m) + "<h3>La saison à venir</h3>" +
      "<div class='risk' style='border-color:" + tier[1] + "'><b style='color:" + tier[1] + "'>Risque de saison trop sèche : " + tier[0] + "</b>" +
      "<div>Saison " + esc(sc.season.replace("-", "–")) + " : sur 10 saisons comparables aux années passées, environ <b>" + tenth + "</b> ont été trop sèches pour cette zone.</div></div>";
    if (sc.observed_share > 0 && m.pc !== undefined) h += "<p>Pluie tombée jusqu'ici : <b>" + Math.round(m.pc) + " %</b> de la normale.</p>";
    else h += "<p>La saison des pluies n'a pas encore commencé.</p>";
    var e = S.meta.enso;
    if (e) h += "<p>Le Pacifique est actuellement en phase <b>" + esc(e.phase_label) + "</b>." +
      (m.x && m.x.enso_el_pct !== undefined && e.phase === "E" ? " Lors des El Niño passés, cette zone a reçu en moyenne <b>" + Math.round(m.x.enso_el_pct) + " %</b> de la pluie normale." : "") +
      (m.x && m.x.enso_la_pct !== undefined && e.phase === "L" ? " Lors des La Niña passées, cette zone a reçu en moyenne <b>" + Math.round(m.x.enso_la_pct) + " %</b> de la pluie normale." : "") + "</p>";
    if (pb && pb.household) {
      var list = pa >= 0.25 ? pb.household.dry : pb.household.normal;
      h += "<h3>Ce que vous pouvez faire</h3><ul class='advice'>" + list.map(function (t) { return "<li>" + esc(t) + "</li>"; }).join("") + "</ul>";
      if (wet) h += "<h3>Si les pluies sont très fortes</h3><ul class='advice'>" + pb.household.wet.map(function (t) { return "<li>" + esc(t) + "</li>"; }).join("") + "</ul>";
    }
    h += risksSection(m, true);
    return h + "<div class='note'>Information indicative, calculée à partir des saisons passées : ce n'est pas une prévision de la météo. Écoutez la météo et les consignes du fokontany, de la commune et du BNGRC.</div>";
  }


  /* ---------- Alerte précoce (prévision) ---------- */
  function ewMessage(h, m) {
    var ev = m.ev || [];
    if (h === "rain") return "pluie jusqu'à " + Math.round(ev[0]) + " mm en un jour (" + Math.round(ev[1]) + " mm sur 3 jours)";
    if (h === "wind") return "rafales jusqu'à " + Math.round(ev[3]) + " km/h";
    if (h === "heat") return "jusqu'à " + Math.round(ev[2]) + " °C";
    if (h === "dry") return ev[4] + " jours secs de suite prévus";
    if (h === "flood") return ev[5] ? "débit prévu = " + String(ev[5]).replace(".", ",") + " × la crue de 2 ans (" + Math.round(ev[6]) + " m³/s)" : "";
    return "";
  }

  function forecastSection(m) {
    var F = S.meta.forecast;
    if (!F || !m.ew) return "";
    var lvlNames = F.level_names, mx = Math.max.apply(null, m.ew);
    var h = '<div class="ew"><h3>Alerte précoce, 7 prochains jours</h3>';
    HAZ.forEach(function (hz, i) {
      var lv = m.ew[i];
      h += '<div class="row ewrow"><span><i class="ewdot" style="background:' + EW_COLORS[lv] + '"></i>' + EW_ICON[hz] + " <b>" + esc(F.hazard_labels[hz]) + "</b>" +
        (lv > 0 ? " : " + esc(ewMessage(hz, m)) : "") + "</span><span>" + esc(lvlNames[lv]) +
        (S.view.lvl < 4 && m.ewp && m.ewp[i] > 0 ? " · " + MC.fmtInt(m.ewp[i]) + " pers." : "") + "</span></div>";
    });
    if (!F.in_rain_season) h += '<div class="note">Hors saison des pluies : l\'alerte « période sèche » est désactivée.</div>';
    if (mx === 0) h += '<div class="note">Aucune alerte prévue pour cette zone dans les 7 prochains jours.</div>';
    if (m.fr && m.fr.length) {
      var n = m.fr.length, W = 300, Ht = 96, padL = 4, padB = 14, bw = (W - padL) / n, mxp = Math.max(20, Math.max.apply(null, m.fr.filter(function (v) { return v !== null; }))), sy = (Ht - padB - 12) / mxp;
      var d0 = new Date(F.today + "T00:00:00");
      var svg = '<svg viewBox="0 0 ' + W + " " + Ht + '" width="100%" role="img" aria-label="Pluie prévue (barres) et température maximale (points) pour les 10 prochains jours">';
      m.fr.forEach(function (v, i) {
        var d = new Date(d0.getTime() + i * 86400000), lab = d.getDate() + "/" + (d.getMonth() + 1);
        if (v !== null) svg += '<rect x="' + (padL + i * bw + 2) + '" y="' + (Ht - padB - v * sy) + '" width="' + (bw - 4) + '" height="' + Math.max(0.5, v * sy) + '" fill="#3b7dbf"><title>' + lab + " : " + v + " mm</title></rect>" +
          (v >= 1 ? '<text x="' + (padL + i * bw + bw / 2) + '" y="' + (Ht - padB - v * sy - 2) + '" font-size="8" text-anchor="middle" fill="#245">' + v + "</text>" : "");
        if (m.ft && m.ft[i] !== null) svg += '<circle cx="' + (padL + i * bw + bw / 2) + '" cy="' + (8 + (Math.max(0, 45 - m.ft[i])) * 0.5) + '" r="2.5" fill="#d95f02"><title>' + lab + " : " + m.ft[i] + " °C max</title></circle>";
        svg += '<text x="' + (padL + i * bw + bw / 2) + '" y="' + (Ht - 3) + '" font-size="8" text-anchor="middle" fill="#555">' + lab + "</text>";
      });
      h += svg + '</svg><div class="note">Barres : pluie (mm/jour). Points orange : température maximale (plus haut = plus chaud).' + (S.view.lvl > 3 ? "" : " Moyenne de la zone.") + "</div>";
    }
    h += '<div class="note">Prévision du modèle météo, mise à jour ' + esc(fmtDateTime(F.fetched_at)) + ". Maille d'environ 28 km : à lire comme une indication par zone ; les bulletins officiels de Météo Madagascar et du BNGRC priment.</div></div>";
    return h;
  }

  function fmtDateTime(iso) {
    try { var d = new Date(iso); return d.toLocaleString("fr-FR", { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" }); } catch (e) { return iso; }
  }

  function simpleAlerts(m) {
    var F = S.meta.forecast, pb = S.meta.playbook;
    if (!F || !m.ew) return "";
    var h = "<h3>Alerte pour les 7 prochains jours</h3>", any = false;
    HAZ.forEach(function (hz, i) {
      if (m.ew[i] > 0) {
        any = true;
        h += "<div class='risk' style='border-color:" + EW_COLORS[m.ew[i]] + "'><b>" + EW_ICON[hz] + " " + esc(F.hazard_labels[hz]) + " : " + esc(F.level_names[m.ew[i]]) + "</b><div>" + esc(ewMessage(hz, m)) + "</div>" +
          (pb && pb.household_alert && pb.household_alert[hz] ? "<ul class='advice'>" + pb.household_alert[hz].map(function (t) { return "<li>" + esc(t) + "</li>"; }).join("") + "</ul>" : "") + "</div>";
      }
    });
    if (!any) h += "<p>Aucune alerte prévue chez vous dans les 7 prochains jours.</p>";
    return h + "<div class='note'>Mise à jour : " + esc(fmtDateTime(F.fetched_at)) + ". Écoutez aussi la radio, la Météo et le BNGRC.</div>";
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

  function renderForecastBadge() {
    var F = S.meta.forecast, b = $("fcbadge");
    if (!b) return;
    if (!F) { b.hidden = true; return; }
    b.hidden = false;
    b.textContent = "Prévision du " + fmtDateTime(F.fetched_at);
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
    LAYERS = LAYERS.filter(function (l) { return (S.meta.scenarios || ["pa", "ex", "w"].indexOf(l.id) < 0) && (S.meta.forecast || !l.ew); });
    LAYERS.push({ id: "cx", label: "Indice couplé (voir « Indicateurs couplés »)" });
    LAYERS.forEach(function (l) {
      var o = document.createElement("option"); o.value = l.id; o.textContent = l.label; sel.appendChild(o);
    });
    sel.addEventListener("change", function () { S.layer = sel.value; restyle(); });
    setupScenarios(); setupProfiles(); setupCompare(); setupResponse(); setupWho(); readURL();
    $("modebtn").addEventListener("click", function () {
      S.simple = !S.simple;
      $("modebtn").setAttribute("aria-pressed", S.simple ? "true" : "false");
      $("modebtn").textContent = S.simple ? "Vue experte" : "Vue simple « Chez moi »";
      document.body.classList.toggle("simple", S.simple);
      renderInfo();
    });
    var sim = $("sim"), nf = S.meta.rain_factors.length, neutral = S.meta.rain_factors.indexOf(1);
    sim.max = nf - 1; sim.value = neutral;
    function apply() {
      var i = +sim.value;
      if (i !== neutral && S.scn) { S.scn = ""; $("scn").value = ""; }
      if (i !== neutral && S.mode === "diff") S.mode = "single";
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
      { label: "scenario_choisi", get: function () { return S.scn || ""; } },
      { label: "proba_alerte_fin_saison", get: function (r) { return r.m.pa === undefined || r.m.pa === null ? "" : r.m.pa; } },
      { label: "exposes_attendus", get: function (r) { return r.m.ex === undefined ? "" : r.m.ex; } },
      { label: "scenario_facteur_pluie", get: function () { return S.simIdx === null ? 1 : S.meta.rain_factors[S.simIdx]; } },
      { label: "exposes_scenario", get: function (r) { return val(r.m, "e"); } },
      { label: "cibles_scenario", get: function (r) { return val(r.m, "t"); } }];
    ((S.meta.scenarios || {}).list || []).forEach(function (l) {
      ["pct_fin_saison", "niveau", "exposes", "cibles", "exposes_exces_pluie"].forEach(function (nm, k) {
        cols.push({ label: "sc_" + l.id + "_" + nm, get: function (r) { var v = r.m.sc && r.m.sc[l.id]; return v ? (k === 1 ? levelName(v[1]) : (v[k === 0 ? 0 : k] === null ? "" : v[k])) : ""; } });
      });
    });
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



  /* ---------- Historique des événements et de la réponse ---------- */
  var EV_COLORS = { cyclone: "#6a3d9a", "inondation": "#1f78b4", "sécheresse": "#e08214", "épidémie": "#33a02c", autre: "#666666" };
  var KIND_LABELS = { "3w": "Bénéficiaires atteints (import 3W)", hrp: "Projets des plans de réponse (HRP)", iati: "Activités des partenaires (IATI)" };

  function ancestors(pc) { return S.anc && S.anc[pc] ? S.anc[pc] : null; }

  function setupHistory() {
    return getJSON("response.json").then(function (H) {
      S.hist = H;
      return ensureIndex();
    }).then(function () {
      S.anc = {};
      S.index.forEach(function (r) { S.anc[r.c] = [r.a1, r.a2, r.a3].filter(Boolean).slice(0, Math.max(0, r.l - 1)).concat([r.c]); });
      var H = S.hist, years = {};
      H.events.forEach(function (e) { years[+e.date.slice(0, 4)] = 1; });
      H.rec.y.forEach(function (y) { years[y] = 1; });
      var ys = Object.keys(years).map(Number).sort();
      if (!ys.length) return;
      var last = ys[ys.length - 1];
      S.hf = { y0: Math.max(ys[0], last - 9), y1: last, types: {}, kinds: {}, cl: "", org: "", show: false };
      H.event_types.forEach(function (t) { S.hf.types[t] = true; });
      H.kinds.forEach(function (k) { S.hf.kinds[k] = true; });
      $("histcard").hidden = false;
      ["hy0", "hy1"].forEach(function (id, j) {
        var sel = $(id); sel.innerHTML = "";
        ys.forEach(function (y) { var o = document.createElement("option"); o.value = y; o.textContent = y; sel.appendChild(o); });
        sel.value = j ? S.hf.y1 : S.hf.y0;
        sel.addEventListener("change", function () { S.hf.y0 = Math.min(+$("hy0").value, +$("hy1").value); S.hf.y1 = Math.max(+$("hy0").value, +$("hy1").value); histChanged(); });
      });
      $("htypes").innerHTML = H.event_types.map(function (t) {
        return '<label class="check"><input type="checkbox" data-t="' + esc(t) + '" checked><i class="evdot" style="background:' + EV_COLORS[t] + '"></i> ' + esc(t) + "</label>";
      }).join("");
      $("htypes").querySelectorAll("input").forEach(function (cb) { cb.addEventListener("change", function () { S.hf.types[cb.dataset.t] = cb.checked; histChanged(); }); });
      $("hshow").addEventListener("change", function () { S.hf.show = $("hshow").checked; drawEvents(); });
      var cl = $("hcl"); cl.innerHTML = '<option value="">Tous les secteurs</option>' + H.clusters.map(function (c, i) { return '<option value="' + i + '">' + esc(c) + "</option>"; }).join("");
      cl.addEventListener("change", function () { S.hf.cl = cl.value; histChanged(); });
      var og = $("hor"); og.innerHTML = '<option value="">Toutes les organisations</option>' + H.orgs.map(function (o, i) { return '<option value="' + i + '">' + esc(o) + "</option>"; }).join("");
      og.addEventListener("change", function () { S.hf.org = og.value; histChanged(); });
      $("hkinds").innerHTML = H.kinds.map(function (k) {
        var has = H.rec.k.indexOf(H.kinds.indexOf(k)) >= 0;
        return has ? '<label class="check"><input type="checkbox" data-k="' + k + '" checked> ' + esc(KIND_LABELS[k] || k) + "</label>" : "";
      }).join("");
      $("hkinds").querySelectorAll("input").forEach(function (cb) { cb.addEventListener("change", function () { S.hf.kinds[cb.dataset.k] = cb.checked; histChanged(); }); });
      $("histsrc").innerHTML = "Sources : " + H.sources.map(function (x) { return esc(x.label) + " (" + x.n + ")"; }).join(" ; ") + ". " + H.notes.map(esc).join(" ");
      // couches
      var defs = [["ev_n", "Événements : nombre (période choisie)"], ["ev_p", "Événements : personnes affectées ou déplacées"]];
      if (H.rec.u.length) {
        if (H.rec.k.indexOf(H.kinds.indexOf("3w")) >= 0) defs.push(["rb", "Réponse : bénéficiaires atteints (3W)"], ["rg", "Réponse : cibles potentiels moins bénéficiaires atteints"]);
        defs.push(["rp", "Réponse : nombre de projets ou d'activités (HRP, IATI)"], ["rf", "Réponse : budget (€, HRP et IATI)"]);
      }
      defs.forEach(function (d) { LAYERS.push({ id: d[0], label: d[1] }); });
      [$("layer"), $("layerB")].forEach(function (sel) {
        if (!sel) return;
        defs.forEach(function (d) { var o = document.createElement("option"); o.value = d[0]; o.textContent = d[1]; sel.appendChild(o); });
      });
      readURL();
      if (S.view) restyle();
    }).catch(function () { /* pas d'historique disponible */ });
  }

  function histRecs() {
    var H = S.hist, f = S.hf, R = H.rec, out = [];
    for (var i = 0; i < R.u.length; i++) {
      var kind = H.kinds[R.k[i]];
      if (R.y[i] < f.y0 || R.y[i] > f.y1 || !f.kinds[kind]) continue;
      if (f.cl !== "" && R.c[i] !== +f.cl) continue;
      if (f.org !== "" && R.o[i] !== +f.org) continue;
      out.push(i);
    }
    return out;
  }
  function histEvents() {
    var f = S.hf;
    return S.hist.events.filter(function (e) { var y = +e.date.slice(0, 4); return y >= f.y0 && y <= f.y1 && f.types[e.type]; });
  }

  function histAggregate() {
    S.hagg = {};
    if (!S.hist || !S.hf || !S.view || !S.anc) return;
    var L = S.view.lvl, keys = {};
    S.view.feats.forEach(function (f) { keys[f.properties.c] = 1; });
    var agg = { ev_n: {}, ev_p: {}, rb: {}, rp: {}, rf: {} };
    function add(layer, u, v) {
      var a = ancestors(u);
      if (!a || a.length < L) return;
      var key = a[L - 1];
      if (keys[key]) agg[layer][key] = (agg[layer][key] || 0) + v;
    }
    histEvents().forEach(function (e) { add("ev_n", e.u, 1); add("ev_p", e.u, (e.affected || 0) + (e.displaced || 0)); });
    var R = S.hist.rec;
    histRecs().forEach(function (i) {
      if (S.hist.kinds[R.k[i]] === "3w") add("rb", R.u[i], R.b[i]);
      else { add("rp", R.u[i], R.n[i]); add("rf", R.u[i], R.f[i]); }
    });
    S.hagg = agg;
  }

  function histChanged() {
    var ev = histEvents(), recs = histRecs(), R = S.hist.rec, ben = 0, funds = 0, aff = 0;
    ev.forEach(function (e) { aff += (e.affected || 0) + (e.displaced || 0); });
    recs.forEach(function (i) { if (S.hist.kinds[R.k[i]] === "3w") ben += R.b[i]; else funds += R.f[i]; });
    $("hsum").innerHTML = "<b>" + ev.length + "</b> événement(s), " + MC.fmtInt(aff) + " personnes affectées ou déplacées" +
      (ben ? " ; <b>" + MC.fmtInt(ben) + "</b> bénéficiaires atteints (3W)" : "") + (funds ? " ; budget " + MC.fmtInt(funds) + " €" : "") + " sur " + S.hf.y0 + "–" + S.hf.y1 + ".";
    drawEvents();
    if (S.view) restyle();
  }

  function drawEvents() {
    if (!S.map || !S.hist) return;
    if (S.evLayer) { S.map.removeLayer(S.evLayer); S.evLayer = null; }
    if (!S.hf || !S.hf.show || !L.circleMarker) return;
    var layers = histEvents().map(function (e) {
      var r = Math.max(5, Math.min(26, Math.sqrt(((e.affected || 0) + (e.displaced || 0)) / 400)));
      var m = L.circleMarker([e.lat, e.lon], { radius: r, color: "#fff", weight: 1, fillColor: EV_COLORS[e.type] || "#666", fillOpacity: 0.75 });
      m.bindTooltip("<b>" + esc(e.type) + " · " + esc(e.date) + "</b><br>" + esc(e.name) + "<br>Affectés : " + MC.fmtInt(e.affected) + " · Déplacés : " + MC.fmtInt(e.displaced) + "<br><i>Source : " + esc(e.src) + "</i>");
      return m;
    });
    S.evLayer = L.layerGroup(layers).addTo(S.map);
  }



  /* ---------- Eau dans le sol : humidité, recharge, indice de nappe ---------- */
  function setupSoil() {
    return getJSON("soilwater/series.json").then(function (D) { S.soil = D; }).catch(function () { S.soil = null; });
  }
  function soilSection(f) {
    var D = S.soil;
    if (!D) return "";
    var c = f.properties.c, own = D.u[c], u = own || D.u[f.properties.p];
    if (!u) return "";
    var n = D.months.length, last = n - 1, sm = u.sm[last], rz = u.rz[last];
    if (sm === null || sm === undefined) return "";
    var W = 300, Ht = 90, padB = 14, bw = W / n, sy = (Ht - padB - 6) / 100;
    var svg = '<svg viewBox="0 0 ' + W + " " + Ht + '" width="100%" role="img" aria-label="Humidité du sol des 36 derniers mois (barres) et normale du mois (trait)">';
    var line = [];
    D.months.forEach(function (lab, i) {
      var v = u.sm[i], nm = u.n[D.month_numbers[i] - 1];
      if (v !== null && v !== undefined) svg += '<rect x="' + (i * bw + 0.5) + '" y="' + (Ht - padB - v * sy) + '" width="' + (bw - 1) + '" height="' + Math.max(0.5, v * sy) + '" fill="' + (nm !== null && v < nm - 10 ? "#c97b2b" : "#3b7dbf") + '"><title>' + lab + " : " + v + " % de la réserve utile (normale " + nm + " %)</title></rect>";
      if (nm !== null && nm !== undefined) line.push((i * bw + bw / 2) + "," + (Ht - padB - nm * sy));
      if (i % 6 === 0) svg += '<text x="' + (i * bw) + '" y="' + (Ht - 3) + '" font-size="8" fill="#555">' + lab.slice(2) + "</text>";
    });
    svg += '<polyline points="' + line.join(" ") + '" fill="none" stroke="#222" stroke-width="1.2"/></svg>';
    var desc = function (z) { return z === null || z === undefined ? "" : z <= -1.5 ? "très inférieur à la normale" : z <= -0.5 ? "inférieur à la normale" : z < 0.5 ? "proche de la normale" : z < 1.5 ? "supérieur à la normale" : "très supérieur à la normale"; };
    var h = "<h4>Eau dans le sol (modèle)</h4>";
    h += '<div class="row"><span>Humidité du sol, ' + esc(D.months[last]) + '</span><span><b>' + sm + " %</b> de la réserve utile</span></div>";
    if (rz !== null && rz !== undefined) h += '<div class="row"><span>Indice relatif de nappe (recharge sur 12 mois)</span><span><b>' + (rz > 0 ? "+" : "") + String(rz).replace(".", ",") + "</b> : " + desc(rz) + "</span></div>";
    h += svg + '<div class="note">Barres : humidité du sol chaque mois (orange = nettement plus sec que la normale du mois) ; trait : normale du mois. ' +
      (own ? "" : "Valeur de la commune. ") + "Modèle de bilan hydrique mensuel (Thornthwaite-Mather) avec pluie CHIRPS, évapotranspiration ERA5-Land, sols SoilGrids et occupation du sol WorldCover. L'indice de nappe est relatif : ce n'est pas un niveau mesuré.</div>";
    return h;
  }


  /* ---------- Prévision saisonnière (ECMWF SEAS5 via Open-Meteo) ---------- */
  var MONTHS_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
  function setupSeasonal() {
    return getJSON("seasonal.json").then(function (D) { S.seas = D; }).catch(function () { S.seas = null; });
  }
  /* Chocs au format JIAF 2 : intensité et proximité des dangers naturels et des chocs agroécologiques */
  function shockSection(m) {
    var x = m.x || {}, rows = "";
    function g(k) { return x[k]; }
    function spiWord(v) { return v <= -2 ? "extrêmement sec" : v <= -1.5 ? "sévèrement sec" : v <= -1 ? "modérément sec" : v < 1 ? "proche de la normale" : v < 1.5 ? "modérément humide" : v < 2 ? "très humide" : "extrêmement humide"; }
    var wind = g("choc_cyc_vent_kt");
    if (wind !== undefined && g("choc_cyc_nb") > 0) {
      var wl = wind >= 64 ? "force cyclone (≥ 64 kt)" : wind >= 50 ? "vent fort (≥ 50 kt)" : wind >= 34 ? "tempête tropicale (≥ 34 kt)" : "pas de vent de tempête";
      rows += row("Aléa naturel · intensité (cyclone)", "<b>" + esc(wl) + "</b>");
      if (g("choc_cyc_dist_km") !== undefined) rows += row("Aléa naturel · proximité", Math.round(g("choc_cyc_dist_km")) + " km de la trajectoire" + (g("choc_cyc_dernier_jours") !== undefined ? ", passage il y a " + Math.round(g("choc_cyc_dernier_jours")) + " jours" : ""));
      if (g("choc_cyc_retour_ans") !== undefined) rows += row("Pluie du passage (3 jours)", g("choc_cyc_retour_ans") >= 15 ? "au moins aussi forte que toutes les saisons de référence" : "retour d'environ " + String(Math.round(g("choc_cyc_retour_ans") * 10) / 10).replace(".", ",") + " ans");
    }
    [["spi3", "SPI-3"], ["spi6", "SPI-6"], ["spi12", "SPI-12"]].forEach(function (k) {
      var v = g(k[0]);
      if (v !== undefined && v !== null) rows += row("Choc agroécologique · " + k[1], "<b>" + (v > 0 ? "+" : "") + String(Math.round(v * 100) / 100).replace(".", ",") + "</b> : " + spiWord(v));
    });
    var sm = g("sm_z");
    if (sm !== undefined && sm !== null) rows += row("Humidité du sol vs normale du mois", (sm > 0 ? "+" : "") + String(Math.round(sm * 100) / 100).replace(".", ",") + " écart-type");
    if (!rows) return "";
    return "<h4>Chocs (format JIAF)</h4>" + rows +
      '<div class="note" data-tip="Le JIAF est le cadre d\'analyse des besoins humanitaires de l\'ONU (OCHA/IASC). Il demande l\'intensité et la proximité de chaque choc.">Intensité et proximité des chocs, selon le cadre JIAF 2 (OCHA/IASC). SPI : indice standardisé de précipitation de l\'OMM (1981 à aujourd\'hui). Exposition au danger, pas dégât ni besoin humanitaire.</div>';
  }

  function seasonSection(f) {
    var D = S.seas;
    if (!D) return "";
    var c = f.properties.c, chain = (S.anc && S.anc[c]) ? S.anc[c].slice().reverse() : [c, f.properties.p], z = null;
    for (var i = 0; i < chain.length && !z; i++) z = D.z[chain[i]];
    if (!z) return "";
    var own = !!D.z[c], n = D.months.length, W = 300, Ht = 92, base = 46, bw = W / n, sc = 36 / 40;
    var svg = '<svg viewBox="0 0 ' + W + " " + Ht + '" width="100%" role="img" aria-label="Écart prévu de la pluie mensuelle à la normale du modèle">' +
      '<line x1="0" x2="' + W + '" y1="' + base + '" y2="' + base + '" stroke="#999" stroke-width="0.8"/>';
    D.months.forEach(function (m, i) {
      var v = z.r[i], mo = +m.slice(5, 7), inSeason = D.season_months.indexOf(mo) >= 0;
      if (v === null || v === undefined) return;
      var h = Math.max(0.5, Math.min(40, Math.abs(v)) * sc), y = v >= 0 ? base - h : base;
      svg += '<rect x="' + (i * bw + 4) + '" y="' + y + '" width="' + (bw - 8) + '" height="' + h + '" fill="' + (v >= 0 ? "#3b7dbf" : "#c97b2b") + '" opacity="' + (inSeason ? 1 : 0.35) + '"><title>' +
        MONTHS_FR[mo - 1] + " " + m.slice(0, 4) + " : " + (v > 0 ? "+" : "") + String(v).replace(".", ",") + " % (" + (z.a[i] > 0 ? "+" : "") + String(z.a[i]).replace(".", ",") + " mm)" + (inSeason ? "" : " ; hors saison de pluie") + "</title></rect>" +
        '<text x="' + (i * bw + bw / 2) + '" y="' + (Ht - 4) + '" font-size="8" fill="#555" text-anchor="middle">' + MONTHS_FR[mo - 1] + "</text>";
    });
    svg += "</svg>";
    var rs = z.rs, word = rs <= -15 ? "nettement plus sèche que la normale" : rs <= -5 ? "plutôt plus sèche que la normale" : rs < 5 ? "proche de la normale" : rs < 15 ? "plutôt plus humide que la normale" : "nettement plus humide que la normale";
    var h = "<h4>Prévision saisonnière (modèle ECMWF)</h4>";
    h += '<div class="row"><span>Pluie de la saison (mois prévus de novembre à avril)</span><span><b>' + (rs > 0 ? "+" : "") + String(rs).replace(".", ",") + " %</b> : " + word + "</span></div>";
    h += '<div class="row"><span>Probabilités (tiers sec / normal / humide)</span><span><b>' + z.p[0] + " % / " + z.p[1] + " % / " + z.p[2] + " %</b></span></div>" + svg;
    h += '<div class="note">Prévision émise le ' + esc(D.issued) + ". Barres : écart prévu de chaque mois à la normale du modèle (pâle = hors saison de pluie). " + (own ? "" : "Valeur du district. ") +
      "Moyenne d'ensemble ECMWF SEAS5 via Open-Meteo ; la compétence est modérée à Madagascar (surtout liée à El Niño dans le Sud) et les probabilités sont volontairement bornées entre 15 et 50 %. Ce n'est pas une prévision de Météo Madagascar.</div>";
    return h;
  }

  /* ---------- Calendrier cultural (recommandations officielles par région, fenêtres saisies) ---------- */
  function setupCalendar() {
    return getJSON("calendrier.json").then(function (D) { S.cal = D; }).catch(function () { S.cal = null; });
  }
  function calendarSection(f) {
    var D = S.cal;
    if (!D) return "";
    var c = f.properties.c, chain = (S.anc && S.anc[c]) ? S.anc[c] : [c], reg = chain[0], recs = D.regions[reg] || [], wins = [];
    chain.concat(["ALL"]).forEach(function (code) { (D.windows[code] || []).forEach(function (w) { wins.push(w); }); });
    if (!recs.length && !wins.length) return "";
    var now = new Date(), cm = now.getMonth() + 1, cd = Math.min(3, Math.ceil(now.getDate() / 10)), DEC = ["1-10", "11-20", "21-fin"];
    function key(m, d) { return ((m + 1) % 12) * 3 + (d - 1); }      // l'année agricole commence en novembre (mois 11 -> 0)
    var h = "<h4>Cultures et calendrier</h4>";
    if (recs.length) h += "<ul>" + recs.map(function (t) { return "<li>" + esc(t) + "</li>"; }).join("") + "</ul>";
    if (wins.length) {
      h += "<ul>" + wins.slice(0, 12).map(function (w) {
        var a = key(w.d0[0], w.d0[1]), b = key(w.d1[0], w.d1[1]), k = key(cm, cd), live = a <= b ? (k >= a && k <= b) : (k >= a || k <= b);
        return "<li" + (live ? ' style="font-weight:600"' : "") + ">" + esc(w.c) + " : " + esc(w.o) + " du " + DEC[w.d0[1] - 1] + "/" + w.d0[0] + " au " + DEC[w.d1[1] - 1] + "/" + w.d1[0] + (live ? " (en cours)" : "") + (w.src ? ' <span class="note">' + esc(w.src) + "</span>" : "") + "</li>";
      }).join("") + "</ul>";
    }
    h += '<div class="note">Recommandations pour la saison ' + esc(D.season) + " ; elles dépendent des perspectives de pluie de cette saison. Source : " +
      (D.source && D.source.url ? '<a href="' + esc(D.source.url) + '" target="_blank" rel="noopener">' + esc(D.source.title) + "</a>" : "document officiel") +
      ". Les tableaux par décade et par variété sont dans le document officiel.</div>";
    return h;
  }

  /* ---------- Priorités de réponse (vue d'un gestionnaire d'information) ---------- */
  function respRows() {
    if (!S.view) return [];
    var rb = (S.hagg && S.hagg.rb) || {};
    return S.view.feats.map(function (f) {
      var c = f.properties.c, m = S.view.metrics[c] || {}, e = val(m, "e") || 0, t = val(m, "t") || 0, got = rb[c] || 0;
      var ew = m.ew ? Math.max.apply(null, m.ew) : 0;
      return { c: c, n: f.properties.n, l: val(m, "l") || 0, e: e, t: t, got: got, gap: Math.max(0, t - got), cov: t > 0 ? Math.min(100, 100 * got / t) : null, ew: ew, m: m };
    });
  }
  function respSorted(rows) {
    var k = $("rsort").value, key = { gap: "gap", e: "e", t: "t", l: "l" }[k];
    var r = rows.filter(function (x) { return k === "cov" ? x.t > 0 : true; });
    r.sort(function (a, b) { return k === "cov" ? a.cov - b.cov || b.t - a.t : b[key] - a[key] || b.e - a.e; });
    return r;
  }
  function renderResponse() {
    var card = $("respcard");
    if (!card || !S.view) return;
    card.hidden = false;
    var rows = respRows(), top = respSorted(rows).slice(0, +$("rn").value), lv = S.meta.levels[S.view.lvl].label.toLowerCase();
    var tot = rows.reduce(function (a, x) { a.e += x.e; a.t += x.t; a.got += x.got; a.gap += x.gap; return a; }, { e: 0, t: 0, got: 0, gap: 0 });
    var hasResp = !!S.hist;
    var h = '<div class="row"><span>Total de la vue</span><span><b>' + MC.fmtInt(tot.e) + "</b> exposés · <b>" + MC.fmtInt(tot.t) + "</b> cibles" + (hasResp ? " · <b>" + MC.fmtInt(tot.got) + "</b> atteints (3W) · écart <b>" + MC.fmtInt(tot.gap) + "</b>" : "") + "</span></div>";
    h += '<table class="rtab"><tr><th>Zone</th><th>Alerte</th><th>Exposés</th><th>Cibles</th>' + (hasResp ? "<th>Atteints</th><th>Écart</th><th>Couv.</th>" : "") + "</tr>";
    top.forEach(function (x) {
      h += "<tr><td>" + esc(x.n) + "</td><td>" + esc(levelName(x.l)) + "</td><td>" + MC.fmtInt(x.e) + "</td><td>" + MC.fmtInt(x.t) + "</td>" +
        (hasResp ? "<td>" + MC.fmtInt(x.got) + "</td><td>" + MC.fmtInt(x.gap) + "</td><td>" + (x.cov === null ? "n/d" : Math.round(x.cov) + " %") + "</td>" : "") + "</tr>";
    });
    $("rtable").innerHTML = h + "</table>";
    var ant = rows.filter(function (x) { return x.ew >= 2; }).sort(function (a, b) { return b.ew - a.ew || b.e - a.e; });
    var F = S.meta.forecast, ah = "";
    if (F && rows.some(function (x) { return x.m.ew; })) {
      ah = "<h4>Action anticipée : alertes prévues dans les 7 jours</h4>";
      if (!ant.length) ah += '<div class="note">Aucune zone de la vue n\'a une alerte de niveau « Alerte » ou plus prévue dans les 7 prochains jours.</div>';
      else ah += "<ul>" + ant.slice(0, 8).map(function (x) {
        var hz = HAZ.filter(function (z, i) { return x.m.ew[i] >= 2; }).map(function (z) { return F.hazard_labels[z].toLowerCase(); });
        var pop = Math.max.apply(null, (x.m.ewp || []).filter(function (v, i) { return x.m.ew[i] >= 2; }).concat([0]));
        var share = pop > 0 && x.m.p > 0 ? " (" + (100 * pop / x.m.p < 1 ? "moins de 1" : Math.round(100 * pop / x.m.p)) + " % de la population de la zone)" : "";
        return "<li><b>" + esc(x.n) + "</b> : " + esc(F.level_names[x.ew]) + " (" + esc(hz.join(", ")) + ")" + (pop > 0 ? " · ≈ " + MC.fmtInt(pop) + " pers." + share : "") + "</li>";
      }).join("") + "</ul>";
    }
    $("rant").innerHTML = ah;
    $("rnote").innerHTML = "Écart = cibles potentielles − bénéficiaires déclarés par les partenaires (3W/4W importés, filtres actuels). La réponse non déclarée n'est pas visible : un écart élevé peut aussi venir d'un manque de rapportage. Le 3W importé n'est pas additionnable d'un secteur à l'autre sans filtre de secteur. Les cibles et exposés utilisent des parts provisoires (voir Méthode).";
  }
  function respNote() {
    var rows = respRows(), top = respSorted(rows).slice(0, 5), tot = rows.reduce(function (a, x) { a.e += x.e; a.t += x.t; a.got += x.got; a.gap += x.gap; return a; }, { e: 0, t: 0, got: 0, gap: 0 });
    var where = S.path.length ? S.path[S.path.length - 1].name : S.meta.country, lv = S.meta.levels[S.view.lvl].plural.toLowerCase();
    var lines = ["NOTE DE SITUATION — MakyClimat — " + where + " (" + lv + ")", "Situation : " + periodName(S.scn, S.simIdx) + (S.meta.data_through ? " ; pluie jusqu'au " + fmtDate(S.meta.data_through) : ""),
      "Exposés : " + MC.fmtInt(tot.e) + " ; cibles potentielles : " + MC.fmtInt(tot.t) + (S.hist ? " ; bénéficiaires déclarés (3W) : " + MC.fmtInt(tot.got) + " ; écart : " + MC.fmtInt(tot.gap) : ""), "", "Zones prioritaires (classées par « " + $("rsort").selectedOptions[0].textContent.toLowerCase() + " ») :"];
    top.forEach(function (x, i) { lines.push((i + 1) + ". " + x.n + " — " + levelName(x.l) + " ; exposés " + MC.fmtInt(x.e) + " ; cibles " + MC.fmtInt(x.t) + (S.hist ? " ; atteints " + MC.fmtInt(x.got) + " ; écart " + MC.fmtInt(x.gap) : "")); });
    var ant = rows.filter(function (x) { return x.ew >= 2; });
    if (ant.length) lines.push("", "Alertes prévues sous 7 jours : " + ant.length + " zone(s) (" + ant.slice(0, 5).map(function (x) { return x.n; }).join(", ") + ").");
    lines.push("", "Sources : CHIRPS, prévision Open-Meteo, population OCHA COD-PS" + (S.hist ? ", réponse déclarée (3W/4W importés, HRP, IATI)" : "") + ". Estimations à valider avec les clusters ; les alertes officielles (BNGRC, Météo Madagascar) priment.");
    return lines.join("\n");
  }
  function setupResponse() {
    ["rsort", "rn"].forEach(function (id) { $(id).addEventListener("change", renderResponse); });
    $("rcopy").addEventListener("click", function () {
      var t = respNote();
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(function () { $("rcopy").textContent = "Note copiée"; setTimeout(function () { $("rcopy").textContent = "Copier la note de situation"; }, 2000); });
      else { var ta = document.createElement("textarea"); ta.value = t; document.body.appendChild(ta); ta.select(); document.execCommand("copy"); document.body.removeChild(ta); }
    });
    $("rcsv").addEventListener("click", function () {
      var rows = respSorted(respRows()), cols = [
        { label: "code", get: function (r) { return r.c; } }, { label: "zone", get: function (r) { return r.n; } }, { label: "niveau_alerte", get: function (r) { return levelName(r.l); } },
        { label: "exposes", get: function (r) { return r.e; } }, { label: "cibles", get: function (r) { return r.t; } }, { label: "beneficiaires_declares_3w", get: function (r) { return r.got; } },
        { label: "ecart", get: function (r) { return r.gap; } }, { label: "couverture_pct", get: function (r) { return r.cov === null ? "" : Math.round(r.cov); } },
        { label: "alerte_prevue_7j", get: function (r) { return S.meta.forecast ? S.meta.forecast.level_names[r.ew] : ""; } }];
      var a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([MC.toCSV(rows, cols)], { type: "text/csv;charset=utf-8" }));
      a.download = "makyclimat_" + SLUG + "_priorites_" + (S.path.map(function (p) { return p.pcode; }).join("_") || "pays") + ".csv";
      a.click();
    });
  }


  /* ---------- Qui fait quoi où (4W) ---------- */
  var WHO_CLUSTERS = [["food_security", "Sécurité alimentaire"], ["nutrition", "Nutrition"], ["health", "Santé"], ["wash", "Eau, assainissement et hygiène"],
                      ["education", "Éducation"], ["protection", "Protection"], ["shelter", "Abris et biens non alimentaires"]];
  var WHO_MANY = 3;
  function whoData() {
    // enregistrements filtrés -> par zone de la vue : secteur -> organisations ; organisation -> secteurs, zones, bénéficiaires
    var H = S.hist, R = H.rec, L = S.view.lvl, keys = {}, zone = {}, orgs = {}, lines = [];
    S.view.feats.forEach(function (f) { keys[f.properties.c] = f.properties.n; });
    histRecs().forEach(function (i) {
      var a = ancestors(R.u[i]);
      if (!a || a.length < L || !keys[a[L - 1]]) return;
      var z = a[L - 1], cl = H.clusters[R.c[i]], org = H.orgs[R.o[i]] || "Organisation non précisée";
      var zz = zone[z] = zone[z] || {};
      (zz[cl] = zz[cl] || {})[org] = 1;
      var o = orgs[org] = orgs[org] || { cl: {}, z: {}, b: 0 };
      o.cl[cl] = 1; o.z[z] = 1; if (H.kinds[R.k[i]] === "3w") o.b += R.b[i];
      lines.push({ z: z, zn: keys[z], cl: cl, org: org, b: H.kinds[R.k[i]] === "3w" ? R.b[i] : 0, y: R.y[i], kind: H.kinds[R.k[i]] });
    });
    return { zone: zone, orgs: orgs, lines: lines, keys: keys };
  }
  function renderWho() {
    var card = $("whocard");
    if (!card) return;
    if (!S.hist || !S.view || !S.anc || !S.hf) { card.hidden = true; return; }
    card.hidden = false;
    var D = whoData(), rows = respSorted(respRows()).slice(0, +$("rn").value);
    var h = '<table class="rtab who"><tr><th>Zone</th>' + WHO_CLUSTERS.map(function (c) { return '<th title="' + esc(c[1]) + '">' + esc(c[1].split(",")[0].split(" ")[0]) + "</th>"; }).join("") + "</tr>";
    rows.forEach(function (x) {
      h += "<tr><td>" + esc(x.n) + "</td>" + WHO_CLUSTERS.map(function (c) {
        var n = Object.keys(((D.zone[x.c] || {})[c[1]]) || {}).length, cls = n === 0 ? "wvide" : n >= WHO_MANY ? "wmany" : "wok";
        return '<td class="' + cls + '">' + (n === 0 ? "vide" : n) + "</td>";
      }).join("") + "</tr>";
    });
    $("whomat").innerHTML = h + "</table>";
    var ol = Object.keys(D.orgs).map(function (k) { var o = D.orgs[k]; return { n: k, cl: Object.keys(o.cl), z: Object.keys(o.z).length, b: o.b }; }).sort(function (a, b) { return b.z - a.z || b.b - a.b; }).slice(0, 8);
    $("whoorg").innerHTML = ol.length ? '<h4>Principaux partenaires de la vue</h4><table class="rtab"><tr><th>Organisation</th><th>Secteurs</th><th>Zones</th><th>Bénéf.</th></tr>' +
      ol.map(function (o) { return "<tr><td>" + esc(o.n) + "</td><td>" + esc(o.cl.slice(0, 3).join(", ")) + (o.cl.length > 3 ? "…" : "") + "</td><td>" + o.z + "</td><td>" + (o.b ? MC.fmtInt(o.b) : "–") + "</td></tr>"; }).join("") + "</table>" : "";
    $("whonote").innerHTML = "Cellule = nombre d'organisations qui déclarent une activité dans la zone et le secteur. « vide » : aucune déclaration (réponse absente ou non rapportée). Orange : " + WHO_MANY + " organisations ou plus, à vérifier (chevauchement ou complémentarité) : seuil de lecture choisi par MakyClimat, sans valeur normative. Seuls les secteurs humanitaires principaux sont affichés.";
  }
  function setupWho() {
    $("whocsv").addEventListener("click", function () {
      var D = whoData();
      var cols = [{ label: "code_zone", get: function (r) { return r.z; } }, { label: "zone", get: function (r) { return r.zn; } }, { label: "secteur", get: function (r) { return r.cl; } },
                  { label: "organisation", get: function (r) { return r.org; } }, { label: "annee", get: function (r) { return r.y; } }, { label: "beneficiaires", get: function (r) { return r.b; } },
                  { label: "source", get: function (r) { return r.kind; } }];
      var a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([MC.toCSV(D.lines, cols)], { type: "text/csv;charset=utf-8" }));
      a.download = "makyclimat_" + SLUG + "_qui_fait_quoi_ou_" + (S.path.map(function (p) { return p.pcode; }).join("_") || "pays") + ".csv";
      a.click();
    });
  }

  /* ---------- Hydrologie : cours d'eau, bassins versants ---------- */
  var RIVER_W = [0, 1, 1.4, 2, 2.8, 3.8, 5];
  function setupHydro() {
    return getJSON("hydro/meta.json").then(function (M) {
      S.hydro = { meta: M, layers: {}, units: null };
      $("hydcard").hidden = false;
      $("hydnote").innerHTML = "<b>" + M.n_basins + "</b> grands bassins et <b>" + M.n_reaches + "</b> tronçons de cours d'eau calculés le " + esc(M.generated) + ".";
      var defs = { hrivers: ["rivers", riverStyle], hbasins: ["basins", basinStyle], hsubs: ["subbasins", subStyle] };
      Object.keys(defs).forEach(function (id) {
        $(id).addEventListener("change", function () { toggleHydro(defs[id][0], defs[id][1], $(id).checked); });
      });
      return getJSON("hydro/units.json").then(function (U) { S.hydro.units = U.u; }).catch(function () {});
    }).catch(function () { /* pas d'hydrologie calculée pour ce pays */ });
  }
  function riverStyle(f) { return { color: "#1f6fb2", weight: RIVER_W[Math.min(6, f.properties.o)] || 1, opacity: 0.85, interactive: false }; }
  function basinStyle() { return { color: "#6b3fa0", weight: 1.6, fill: false, opacity: 0.9, interactive: false }; }
  function subStyle() { return { color: "#8a8f98", weight: 0.8, fill: false, opacity: 0.8, dashArray: "3 3", interactive: false }; }
  function toggleHydro(kind, style, on) {
    var H = S.hydro;
    if (H.layers[kind]) { S.map.removeLayer(H.layers[kind]); H.layers[kind] = null; }
    if (!on) return;
    getJSON("hydro/" + kind + ".geojson").then(function (fc) {
      if (!$({ rivers: "hrivers", basins: "hbasins", subbasins: "hsubs" }[kind]).checked || H.layers[kind]) return;
      H.layers[kind] = L.geoJSON(fc, { style: style, hydro: kind, interactive: false }).addTo(S.map);
    }).catch(function (e) { console.warn(e); });
  }
  function hydroSection(f) {
    var H = S.hydro;
    if (!H || !H.units || !H.units[f.properties.c]) return "";
    var b = H.meta.basins.filter(function (x) { return x.id === H.units[f.properties.c]; })[0];
    if (!b) return "";
    return '<h4>Bassin versant</h4><p class="note">Cette zone se draine vers le bassin <b>' + esc(b.name) + "</b> (" + MC.fmtInt(b.area_km2) + " km², " + MC.fmtInt(b.pop) +
      " habitants). Un cyclone ou une crue en amont peut toucher les zones en aval ; le nom du bassin est celui de la commune de son embouchure.</p>";
  }

  /* ---------- Cyclones passés (IBTrACS) ---------- */
  var CYC_MIN = [[0, "Tous les systèmes"], [34, "Tempête tropicale modérée et plus (34 kt)"], [48, "Forte tempête tropicale et plus (48 kt)"], [64, "Cyclone tropical et plus (64 kt)"], [90, "Cyclone intense et plus (90 kt)"]];
  function cycColor(kt) { return kt < 34 ? "#8b95a1" : kt < 48 ? "#d4ac0d" : kt < 64 ? "#f39c12" : kt < 90 ? "#e67e22" : kt < 116 ? "#c0392b" : "#7b1c12"; }
  function setupCyclones() {
    return getJSON("cyclones.json").then(function (C) {
      var seasons = C.storms.map(function (s) { return s.season; }), y0 = Math.min.apply(null, seasons), y1 = Math.max.apply(null, seasons);
      S.cyc = { data: C, layer: null };
      $("cyccard").hidden = false;
      var opts = "";
      for (var y = y1; y >= y0; y--) opts += '<option value="' + y + '">' + y + "</option>";
      $("cy0").innerHTML = opts; $("cy1").innerHTML = opts;
      $("cy0").value = String(Math.max(y0, y1 - 9)); $("cy1").value = String(y1);
      $("cymin").innerHTML = CYC_MIN.map(function (m) { return '<option value="' + m[0] + '">' + m[1] + "</option>"; }).join("");
      $("cymin").value = "34";
      $("cycsrc").innerHTML = "IBTrACS (NOAA) : <b>" + C.storms.length + "</b> systèmes depuis " + C.since + ", mis à jour le " + esc(C.generated) + ". Les saisons récentes sont provisoires.";
      ["cyshow", "cy0", "cy1", "cymin", "cynear"].forEach(function (id) { $(id).addEventListener("change", drawCyclones); });
    }).catch(function () { /* pas de cyclones pour ce pays */ });
  }
  function drawCyclones() {
    var Y = S.cyc;
    if (!Y) return;
    if (Y.layer) { S.map.removeLayer(Y.layer); Y.layer = null; }
    if (!$("cyshow").checked) { $("cycnote").textContent = ""; return; }
    var a = +$("cy0").value, b = +$("cy1").value, mn = +$("cymin").value, near = $("cynear").checked;
    if (a > b) { var t = a; a = b; b = t; }
    var sel = Y.data.storms.filter(function (s) { return s.season >= a && s.season <= b && s.max_kt >= mn && (!near || (s.near_km !== null && s.near_km <= 100)); });
    var lines = sel.map(function (s) {
      var ln = L.polyline(s.p.map(function (q) { return [q[1], q[0]]; }), { color: cycColor(s.max_kt), weight: s.max_kt >= 64 ? 2.6 : 1.6, opacity: 0.85 });
      ln.bindTooltip((s.name || "Sans nom") + " " + s.season + " : " + s.cat + ", vent max " + s.max_kt + " kt (" + s.start + " au " + s.end + ")" + (s.prov ? " ; provisoire" : ""));
      return ln;
    });
    Y.layer = L.layerGroup(lines).addTo(S.map);
    $("cycnote").innerHTML = "<b>" + sel.length + "</b> systèmes affichés (saisons " + a + " à " + b + "). Couleur = intensité maximale (échelle du RSMC La Réunion) ; trait épais = cyclone tropical (64 kt ou plus).";
  }

  function seasonPhaseOf(date) {
    var sc = S.meta.scenarios;
    if (!sc || !sc.hist_phases) return null;
    var y = +date.slice(0, 4), m = +date.slice(5, 7), end = m >= 11 ? y + 1 : m <= 4 ? y : null;
    if (end === null) return "hors";
    var i = sc.hist_years.indexOf(end);
    return i >= 0 ? sc.hist_phases[i] : null;
  }

  function histSection(f) {
    if (!S.hist || !S.hf || !S.anc) return "";
    var c = f.properties.c, H = S.hist, R = H.rec, hf = S.hf;
    function inZone(u) { var a = ancestors(u); return a && a.indexOf(c) >= 0; }
    var ev = histEvents().filter(function (e) { return inZone(e.u); });
    var recs = histRecs().filter(function (i) { return inZone(R.u[i]); });
    var h = '<div class="hist2"><h3>Historique et réponse (' + hf.y0 + "–" + hf.y1 + ")</h3>";
    // frise par année
    var byY = {};
    for (var y = hf.y0; y <= hf.y1; y++) byY[y] = { e: 0, p: 0, b: 0, f: 0 };
    ev.forEach(function (e) { var o = byY[+e.date.slice(0, 4)]; o.e += 1; o.p += (e.affected || 0) + (e.displaced || 0); });
    recs.forEach(function (i) { var o = byY[R.y[i]]; if (H.kinds[R.k[i]] === "3w") o.b += R.b[i]; else o.f += R.f[i]; });
    var ys = Object.keys(byY).map(Number), mxe = Math.max(1, Math.max.apply(null, ys.map(function (k) { return byY[k].e; }))),
        mxb = Math.max(1, Math.max.apply(null, ys.map(function (k) { return byY[k].b + byY[k].f / 100; })));
    var W = 300, Ht = 90, bw = (W - 8) / ys.length, svg = '<svg viewBox="0 0 ' + W + " " + Ht + '" width="100%" role="img" aria-label="Événements (violet) et réponse (vert) par année">';
    ys.forEach(function (k, j) {
      var o = byY[k], x = 4 + j * bw, he = 28 * o.e / mxe, hb = 40 * (o.b + o.f / 100) / mxb;
      svg += '<rect x="' + (x + 1) + '" y="' + (46 - he) + '" width="' + (bw - 2) + '" height="' + he + '" fill="#7e4fb0"><title>' + k + " : " + o.e + " événement(s), " + MC.fmtInt(o.p) + " personnes</title></rect>" +
        '<rect x="' + (x + 1) + '" y="48" width="' + (bw - 2) + '" height="' + Math.max(0, hb) + '" fill="#31a354"><title>' + k + " : " + MC.fmtInt(o.b) + " bénéficiaires (3W), " + MC.fmtInt(o.f) + " € (HRP/IATI)</title></rect>" +
        '<text x="' + (x + bw / 2) + '" y="' + (Ht - 1) + '" font-size="7" text-anchor="middle" fill="#555">' + String(k).slice(2) + "</text>";
    });
    h += svg + '</svg><div class="note">Violet (haut) : événements. Vert (bas) : réponse (bénéficiaires 3W, sinon budget).</div>';
    // lien avec l'ENSO
    var cnt = { E: 0, L: 0, N: 0, hors: 0 };
    ev.forEach(function (e) { var p = seasonPhaseOf(e.date); if (p && cnt[p] !== undefined) cnt[p] += 1; });
    if (ev.length && S.meta.scenarios && S.meta.scenarios.hist_phases)
      h += row("Événements selon l'ENSO de la saison", "El Niño : " + cnt.E + " · La Niña : " + cnt.L + " · neutre : " + cnt.N + " · hors saison des pluies : " + cnt.hors);
    // par type
    var types = {};
    ev.forEach(function (e) { types[e.type] = (types[e.type] || 0) + 1; });
    Object.keys(types).forEach(function (t) { h += row('<i class="evdot" style="background:' + EV_COLORS[t] + '"></i> ' + esc(t), types[t]); });
    // par secteur
    var cl = {};
    recs.forEach(function (i) { var k = H.clusters[R.c[i]]; cl[k] = cl[k] || { b: 0, f: 0, n: 0 }; if (H.kinds[R.k[i]] === "3w") cl[k].b += R.b[i]; else cl[k].f += R.f[i]; cl[k].n += R.n[i]; });
    var ck = Object.keys(cl);
    if (ck.length) {
      h += '<table class="hind2"><tr><th>Secteur</th><th>Bénéficiaires (3W)</th><th>Budget (€)</th></tr>' + ck.sort(function (a, b) { return cl[b].b + cl[b].f - cl[a].b - cl[a].f; }).slice(0, 8).map(function (k) {
        return "<tr><td>" + esc(k) + "</td><td>" + (cl[k].b ? MC.fmtInt(cl[k].b) : "–") + "</td><td>" + (cl[k].f ? MC.fmtInt(cl[k].f) : "–") + "</td></tr>"; }).join("") + "</table>";
    }
    if (!ev.length && !recs.length) h += '<div class="note">Aucun événement ni donnée de réponse dans cette zone pour ces filtres' + (S.view.lvl > 1 ? " (certaines données ne sont localisées qu'à un niveau plus large)" : "") + ".</div>";
    var last = ev.slice(-5).reverse();
    if (last.length) h += "<details><summary>Derniers événements</summary><ul class='advice'>" + last.map(function (e) {
      return "<li><b>" + esc(e.date) + "</b> " + esc(e.type) + " : " + esc(e.name) + " (" + MC.fmtInt((e.affected || 0) + (e.displaced || 0)) + " pers., " + esc(e.src) + ")</li>"; }).join("") + "</ul></details>";
    return h + "</div>";
  }

  /* ---------- Comparer, indicateurs couplés, lien partageable ---------- */
  function fillSelect(sel, withCx, noEw) {
    sel.innerHTML = "";
    LAYERS.forEach(function (l) {
      if (!withCx && l.id === "cx") return;
      if (noEw && l.ew) return;
      var o = document.createElement("option"); o.value = l.id; o.textContent = l.label; sel.appendChild(o);
    });
  }

  function setupCompare() {
    fillSelect($("layerB"), true, false);
    $("layerB").value = S.layerB;
    $("layerB").addEventListener("change", function () { S.layerB = $("layerB").value; restyle(); });
    var sB = $("scnB");
    sB.innerHTML = $("scn").innerHTML;
    if (S.meta.scenarios) {
      // par défaut : la saison passée la plus récente pour comparer avec la situation actuelle
      var yrs = S.meta.scenarios.hist_years || [];
      if (yrs.length) { S.scnB = "y:" + yrs[yrs.length - 1]; }
    }
    sB.value = S.scnB;
    sB.addEventListener("change", function () { S.scnB = sB.value; restyle(); });
    document.querySelectorAll("#modeseg button").forEach(function (b) {
      b.addEventListener("click", function () { S.mode = b.dataset.mode; applyMode(); });
    });
    // indicateurs couplés
    var box = $("cxrows");
    S.cx.items.forEach(function (it, i) {
      var row = document.createElement("div"); row.className = "cxrow";
      row.innerHTML = '<select class="cxk" aria-label="Indicateur ' + (i + 1) + '"></select>' +
        '<select class="cxw" aria-label="Poids">' + [1, 2, 3, 4, 5].map(function (n) { return "<option value='" + n + "'>poids " + n + "</option>"; }).join("") + "</select>" +
        '<select class="cxd" aria-label="Sens"><option value="1">plus = plus de risque</option><option value="-1">moins = plus de risque</option></select>';
      box.appendChild(row);
      var k = row.querySelector(".cxk");
      var o0 = document.createElement("option"); o0.value = ""; o0.textContent = i < 2 ? "— choisir —" : "— (facultatif) —"; k.appendChild(o0);
      LAYERS.forEach(function (l) { if (l.id === "cx") return; var o = document.createElement("option"); o.value = l.id; o.textContent = l.label; k.appendChild(o); });
      k.value = it.k; row.querySelector(".cxw").value = it.w; row.querySelector(".cxd").value = it.dir;
    });
    $("cxgo").addEventListener("click", function () { readCx(); $("layer").value = "cx"; S.layer = "cx"; restyle(); });
    $("cxop").addEventListener("change", function () { if (S.layer === "cx" || S.layerB === "cx") { readCx(); restyle(); } });
    box.addEventListener("change", function () { if (S.layer === "cx" || S.layerB === "cx") { readCx(); restyle(); } });
    $("cxcopy").addEventListener("click", function () {
      syncURL();
      var url = location.href, ok = function () { $("cxcopy").textContent = "Lien copié"; setTimeout(function () { $("cxcopy").textContent = "Copier le lien de cette carte"; }, 1800); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(ok, function () { window.prompt("Copiez ce lien :", url); });
      else window.prompt("Copiez ce lien :", url);
    });
    applyModeUI();
  }

  function readCx() {
    var rows = document.querySelectorAll("#cxrows .cxrow");
    S.cx.items = Array.prototype.map.call(rows, function (r) {
      return { k: r.querySelector(".cxk").value, w: +r.querySelector(".cxw").value, dir: +r.querySelector(".cxd").value };
    });
    S.cx.op = $("cxop").value;
  }

  function applyModeUI() {
    document.querySelectorAll("#modeseg button").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.mode === S.mode ? "true" : "false"); });
    $("cmpB").hidden = S.mode === "single";
    $("layerBrow").hidden = S.mode !== "split";
  }

  function syncURL() {
    try {
      var q = new URLSearchParams();
      if (SLUG !== "mdg") q.set("pays", SLUG);
      if (S.layer !== "l") q.set("l", S.layer);
      if (S.scn) q.set("s", S.scn);
      if (S.mode !== "single") { q.set("m", S.mode); q.set("sb", S.scnB); if (S.mode === "split") q.set("lb", S.layerB); }
      if (S.layer === "cx" || S.layerB === "cx") q.set("cx", S.cx.items.filter(function (it) { return it.k; }).map(function (it) { return [it.k, it.w, it.dir].join("|"); }).join("~") + "~op=" + S.cx.op);
      var qs = q.toString();
      history.replaceState(null, "", location.pathname + (qs ? "?" + qs : "") + location.hash);
    } catch (e) { /* aperçu sans historique */ }
  }

  function readURL() {
    var l = params.get("l"), s = params.get("s"), m = params.get("m"), cx = params.get("cx");
    if (cx) {
      var parts = cx.split("~"), items = [];
      parts.forEach(function (p) {
        if (p.indexOf("op=") === 0) S.cx.op = p.slice(3);
        else { var a = p.split("|"); if (a[0]) items.push({ k: a[0], w: +a[1] || 1, dir: +a[2] || 1 }); }
      });
      while (items.length < 3) items.push({ k: "", w: 1, dir: 1 });
      S.cx.items = items.slice(0, 3);
      var rows = document.querySelectorAll("#cxrows .cxrow");
      S.cx.items.forEach(function (it, i) { rows[i].querySelector(".cxk").value = it.k; rows[i].querySelector(".cxw").value = it.w; rows[i].querySelector(".cxd").value = it.dir; });
      $("cxop").value = S.cx.op;
    }
    if (l && layerDef(l)) { S.layer = l; $("layer").value = l; }
    if (s && ($("scn").querySelector('option[value="' + s + '"]'))) { S.scn = s; $("scn").value = s; }
    if (params.get("sb") !== null && $("scnB").querySelector('option[value="' + params.get("sb") + '"]')) { S.scnB = params.get("sb"); $("scnB").value = S.scnB; }
    if (params.get("lb") && layerDef(params.get("lb"))) { S.layerB = params.get("lb"); $("layerB").value = S.layerB; }
    if (m === "split" || m === "diff") { S.mode = m; $("mapwrap").classList.toggle("split", m === "split"); $("map2").hidden = m !== "split"; applyModeUI(); }
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
        if (f) { S.selected = f; restyleGeo(); renderInfo();
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
      (m.scenarios ? "<h3>Scénarios de fin de saison</h3><p>La pluie finale de la saison " + esc(m.scenarios.season.replace("-", "–")) + " est la pluie déjà observée plus la pluie restante prise dans chacune des " + m.scenarios.n_years +
        " saisons passées (" + m.scenarios.years[0] + "–" + m.scenarios.years[1] + "), comparée à la normale complète. Les scénarios sont : saison sèche (le 10<sup>e</sup> centile), médiane, humide (90<sup>e</sup> centile), et la médiane des saisons El Niño et La Niña passées. " +
        "Les niveaux d'alerte, la population exposée et les cibles sont recalculés pour chaque scénario avec les <b>mêmes seuils provisoires</b> ; la probabilité d'alerte est la part des saisons possibles qui atteignent le niveau d'alerte ou pire. Si une prévision saisonnière officielle est fournie (fichier <code>inputs/prevision_saisonniere.csv</code>), les années sont pondérées selon ses probabilités par tercile. " +
        "<b>Ce n'est pas une prévision météo</b> : cela décrit ce que des situations comparables ont produit dans le passé. La couche « excès de pluie » est un indicateur pluviométrique simple, pas une prévision de crue. Les nombres de personnes par secteur appliquent des parts provisoires (voir le plan d'action) à valider avec les clusters.</p>" : "") +
      '<div id="hindbox"></div>' +
      "<h3>Un outil qui complète les outils existants</h3><p>Chaque secteur et chaque cluster coordonné par l'OCHA dispose déjà de ses propres outils et alertes. MakyClimat ne les remplace pas : il les rassemble sur une même carte jusqu'au fokontany, ajoute le climat, les scénarios et les personnes concernées, et reste utilisable par tous, des ménages aux agences des Nations Unies. " +
      "Les alertes sectorielles peuvent être importées telles quelles (fichier <code>inputs/alertes_secteurs.csv</code>) et sont affichées avec leur source. Pour approfondir : " +
      '<a href="https://fews.net" target="_blank" rel="noopener">FEWS NET</a>, <a href="https://www.ipcinfo.org" target="_blank" rel="noopener">IPC</a>, <a href="https://hungermap.wfp.org" target="_blank" rel="noopener">HungerMap (PAM)</a>, <a href="https://data.humdata.org" target="_blank" rel="noopener">HDX</a> et <a href="https://www.unocha.org/madagascar" target="_blank" rel="noopener">OCHA Madagascar</a>.</p>' +
      "<h3>4. Simulation « et si ? »</h3><p>La pluie cumulée observée est multipliée par un facteur (de ×" + m.rain_factors[0].toFixed(2).replace(".", ",") + " à ×" +
      m.rain_factors[m.rain_factors.length - 1].toFixed(2).replace(".", ",") + ") puis tous les calculs sont refaits. C'est une analyse de sensibilité : elle ne prédit pas la pluie à venir. La température, l'évaporation et le sol sont prévus aux phases suivantes.</p>" +
      "<h3>5. Limites connues</h3><ul><li>Population et limites des fokontany : estimations anciennes (référence " + esc(m.sources[2].reference_year) + ").</li>" +
      "<li>La pluie satellitaire est moins fiable dans les zones montagneuses et côtières ; à valider avec les stations.</li>" +
      "<li>Aucun chiffre ne remplace l'analyse officielle IPC ; l'outil prépare et met à jour entre deux cycles.</li></ul>" +
      "<p class='note'>Tout est reproductible : le code, les seuils et les fichiers de configuration sont publics dans le dépôt.</p>";
  }

  function renderHindcast() {
    getJSON("hindcast.json").then(function (H) {
      var box = $("hindbox");
      if (!box) return;
      var pc = function (x) { return x === null || x === undefined ? "–" : Math.round(x * 100) + " %"; };
      var f1 = function (x) { return String(x).replace(".", ","); };
      var rows = H.origins.map(function (o) {
        return "<tr><td>" + o.months_observed + "</td><td>" + f1(o.mae) + "</td><td>" + f1(o.mae_climatology) + "</td><td>" + pc(o.skill) +
          "</td><td>" + pc(o.coverage_p10_p90) + "</td><td>" + pc(o.brier_skill) + "</td></tr>";
      }).join("");
      var mid = H.origins[Math.min(2, H.origins.length - 1)];
      var ph = mid.by_phase || {}, phTxt = ["el", "la", "ne"].filter(function (k) { return ph[k]; }).map(function (k) {
        return { el: "El Niño", la: "La Niña", ne: "neutres" }[k] + " : erreur " + f1(ph[k].mae) + " pts (biais " + (ph[k].bias > 0 ? "+" : "") + f1(ph[k].bias) + ")";
      }).join(" ; ");
      box.innerHTML = "<h3>Fiabilité mesurée des scénarios</h3><p>Le moteur de scénarios est testé sur les " + H.n_seasons + " saisons passées (" + H.first_season + "–" + H.last_season +
        ") : pour chaque saison, on la « cache », on prévoit sa fin à partir des autres saisons et de la pluie déjà tombée, puis on compare à ce qui s'est réellement passé (validation croisée, " + H.n_points + " points de grille). " +
        "L'erreur est exprimée en points de % de la normale ; la <b>référence</b> est la simple climatologie (ignorer la pluie déjà tombée).</p>" +
        '<div class="tablewrap"><table class="tbl hind"><thead><tr><th>Mois déjà observés</th><th>Erreur du scénario médian</th><th>Erreur climatologie</th><th>Gain</th><th>Couverture P10–P90 (idéal 80 %)</th><th>Gain du score de Brier (alerte &lt; " + H.alert_below_pct + " %)</th></tr></thead><tbody>' +
        rows + "</tbody></table></div>" +
        (phTxt ? "<p>Après " + mid.months_observed + " mois observés, selon la phase ENSO de la saison : " + phTxt + ".</p>" : "") +
        "<p>Lecture : plus la saison avance, plus le scénario médian est précis ; un gain positif signifie que l'outil fait mieux que la climatologie. Avec 0 mois observé il n'y a aucun gain, c'est normal. " +
        "Limites : le test porte sur la pluie satellitaire, pas sur les dégâts ; il ne mesure pas la prévision météo à 16 jours (à valider séparément) ; un échantillon de ~" + H.n_seasons + " saisons reste modeste.</p>";
    }).catch(function () { /* hindcast non encore calculé */ });
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
      renderEnso(); renderForecastBadge();
      setupMap(); setupControls(); setupErgonomics(); setupTips();
      var hash = location.hash.replace("#", "").split("/").filter(Boolean).slice(0, 3);
      var p = hash.length ? ensureIndex().then(function () {
        S.path = hash.map(function (c) { return { pcode: c, name: S.nameOf[c] || c }; });
      }) : Promise.resolve();
      p.then(function () { render(true); });
      renderCatalogue().catch(function (e) { console.warn(e); });
      renderSources(); renderMethod(); renderHindcast();
      setupHistory();
      setupHydro();
      setupSoil();
      setupSeasonal();
      setupCalendar();
      setupCyclones();
    }).catch(function (e) { console.error(e); showEmpty("Chargement impossible : " + e.message); });
  }
  init();
})();
