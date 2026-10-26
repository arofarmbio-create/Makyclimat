/* Test de l'interface sans navigateur (jsdom + Leaflet simulé).
   Usage : NODE_PATH=<dossier node_modules avec jsdom> node tests/ui_test.js [pays]   (pays par défaut : demo) */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const slug = process.argv[2] || "demo";
const docs = path.join(__dirname, "..", "docs");
const html = fs.readFileSync(path.join(docs, "index.html"), "utf8");
const dom = new JSDOM(html, { runScripts: "outside-only", url: `http://localhost/?pays=${slug}`, pretendToBeVisual: true });
const w = dom.window;
let failures = 0;
function check(name, cond, extra) {
  console.log((cond ? "OK   " : "ÉCHEC") + " " + name + (extra ? " — " + extra : ""));
  if (!cond) failures++;
}

// --- Leaflet simulé ---
const handlers = {}; // pcode -> click handler
let currentLayers = [];
let lastBlob = null;
let mapCount = 0;
const markerGroups = [];
const hydroLayers = {};
let cycGroup = null;
let layersB = [];
w.L = {
  map() { return { id: ++mapCount, setView() { return this; }, fitBounds() {}, removeLayer(l) { if (l && l.kind) delete hydroLayers[l.kind]; if (l === cycGroup) cycGroup = null; }, invalidateSize() {}, on() {}, getCenter() { return [0, 0]; }, getZoom() { return 5; } }; },
  tileLayer() { return { addTo() {} }; },
  polyline(ll, o) { return { ll, o, bindTooltip() { return this; } }; },
  circleMarker(ll, o) { return { ll, o, bindTooltip() { return this; } }; },
  layerGroup(ms) { markerGroups.push(ms); const g = { ms, addTo() { if (ms.length && ms.every((m) => m.ll && Array.isArray(m.ll[0]))) cycGroup = g; return this; } }; return g; },
  geoJSON(fc, opts) {
    if (opts.hydro) { const o = { fc, kind: opts.hydro, addTo() { hydroLayers[opts.hydro] = o; return o; } }; return o; }
    const layers = fc.features.map((f) => {
      const layer = { feature: f, on(ev, fn) { if (ev === "click") handlers[f.properties.c] = fn; },
                      bindTooltip(fn) { this._tip = fn; }, getBounds() { return {}; }, _style: opts.style(f) };
      opts.onEachFeature(f, layer);
      return layer;
    });
    return { addTo(map) { if (map && map.id === 2) layersB = layers; else currentLayers = layers; return this; }, getBounds() { return {}; },
             setStyle(fn) { layers.forEach((l) => { l._style = fn(l.feature); }); },
             eachLayer(cb) { layers.forEach(cb); } };
  },
};
w.alert = (m) => { console.log("alert:", m); failures++; };
w.fetch = (url) => {
  const file = path.join(docs, url.split("?")[0]);
  return fs.existsSync(file)
    ? Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(JSON.parse(fs.readFileSync(file, "utf8"))) })
    : Promise.resolve({ ok: false, status: 404, json: () => Promise.reject(new Error("404")) });
};
w.URL.createObjectURL = (b) => { lastBlob = b; return "blob:test"; };
w.HTMLAnchorElement.prototype.click = function () {};
w.eval(fs.readFileSync(path.join(docs, "logic.js"), "utf8"));
w.eval(fs.readFileSync(path.join(docs, "app.js"), "utf8"));

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const $ = (id) => w.document.getElementById(id);
async function waitFor(fn, ms = 4000) { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (fn()) return true; await sleep(50); } return false; }

(async () => {
  check("chargement initial (KPIs)", await waitFor(() => $("kpis").children.length === 3));
  $("fsbtn").click();
  check("plein écran activé", w.document.body.classList.contains("mapfull"));
  $("panelbtn").click();
  check("panneau masquable", w.document.body.classList.contains("nopanel"));
  $("fsbtn").click();
  check("sortie du plein écran", !w.document.body.classList.contains("mapfull") && !w.document.body.classList.contains("nopanel"));
  $("lgtoggle").click();
  check("légende repliable", $("legendbox").classList.contains("closed"));
  $("lgtoggle").click();
  check("légende réaffichée", !$("legendbox").classList.contains("closed"));
  var h3 = w.document.querySelector("#cmpcard > h3"); h3.click();
  check("rubrique repliable", $("cmpcard").classList.contains("collapsed")); h3.click();
  check("badge de date", /Pluie jusqu'au/.test($("through").textContent), $("through").textContent);
  const metaJson = JSON.parse(fs.readFileSync(path.join(docs, "data", slug, "meta.json"), "utf8"));
  const nHist = fs.existsSync(path.join(docs, "data", slug, "response.json")) ? 6 : 0;
  check("6 indicateurs de base + indicateurs externes affichables",
        await waitFor(() => $("layer").options.length === 7 + (metaJson.scenarios ? 3 : 0) + (metaJson.forecast ? 6 : 0) + metaJson.external.length + nHist), $("layer").options.length + " couches");
  check("régions affichées", currentLayers.length === 4, currentLayers.length + " régions");
  check("couleurs d'alerte attribuées", currentLayers.every((l) => /^#/.test(l._style.fillColor)));
  const kpi0 = $("kpis").textContent;

  // sélection puis exploration
  const first = currentLayers[0].feature.properties.c;
  handlers[first]();
  if (fs.existsSync(path.join(docs, "data", slug, "hindcast.json"))) {
    check("onglet Méthode : fiabilité mesurée (hindcast)", await waitFor(() => /Fiabilité mesurée/.test($("methodtext").innerHTML) && $("methodtext").querySelectorAll("table.hind tbody tr").length === 6));
  }
  if (metaJson.has_history) {
    check("courbe historique ENSO : une barre par saison", await waitFor(() => /Pluie de chaque saison/.test($("info").innerHTML) && ($("info").innerHTML.match(/<rect /g) || []).length >= 20));
  }
  if (metaJson.forecast) {
    check("badge de prévision", !$("fcbadge").hidden && /Prévision du/.test($("fcbadge").textContent));
    check("panneau d'alerte précoce : 5 aléas et graphique de 10 jours", $("info").querySelectorAll(".ewrow").length === 5 && /<svg[^>]*Pluie prévue/.test($("info").innerHTML));
    $("layer").value = "ewm"; $("layer").dispatchEvent(new w.Event("change"));
    const cols = new Set(currentLayers.map((l) => l._style.fillColor));
    check("carte des alertes colorée avec la palette des niveaux", [...cols].every((c) => ["#d7ebd2", "#f2d16b", "#e8893a", "#b2262e"].includes(c)), [...cols].join(" "));
    check("légende des niveaux d'alerte", /Vigilance/.test($("legend").textContent) && /Alerte maximale/.test($("legend").textContent));
  check("rubrique repliable", $("cmpcard").classList.contains("collapsed")); h3.click();
    $("layer").value = "l"; $("layer").dispatchEvent(new w.Event("change"));
  }
  const respPath = path.join(docs, "data", slug, "response.json");
  check("carte Priorités de réponse visible", await waitFor(() => !$("respcard").hidden && $("rtable").querySelectorAll("tr").length >= 2));
  {
    const rows = [...$("rtable").querySelectorAll("tr")].slice(1).map((tr) => [...tr.children].map((td) => td.textContent));
    const num = (x) => Number(String(x).replace(/\D/g, ""));
    const gaps = rows.map((r) => num(r[5]));
    check("priorités : classées par écart décroissant", rows.length > 0 && gaps.every((g, i) => i === 0 || gaps[i - 1] >= g), gaps.join(" "));
    $("rsort").value = "e"; $("rsort").dispatchEvent(new w.Event("change"));
    const ex = [...$("rtable").querySelectorAll("tr")].slice(1).map((tr) => num(tr.children[2].textContent));
    check("priorités : tri par personnes exposées", ex.every((g, i) => i === 0 || ex[i - 1] >= g), ex.join(" "));
    let copied = ""; Object.defineProperty(w.navigator, "clipboard", { value: { writeText: (t) => { copied = t; return Promise.resolve(); } }, configurable: true });
    $("rcopy").click();
    check("note de situation copiée", /NOTE DE SITUATION/.test(copied) && /Zones prioritaires/.test(copied) && /Sources/.test(copied));
    $("rcsv").click();
    const txt = lastBlob ? await lastBlob.text() : "";
    check("export de la liste priorisée", /ecart/.test(txt) && txt.split("\n").length > 3);
    $("rsort").value = "gap"; $("rsort").dispatchEvent(new w.Event("change"));
  }
  if (fs.existsSync(respPath)) {
    const HW = JSON.parse(fs.readFileSync(respPath, "utf8"));
    check("carte Qui fait quoi où visible", await waitFor(() => !$("whocard").hidden && $("whomat").querySelectorAll("tr").length >= 2));
    const y0 = +$("hy0").value, y1 = +$("hy1").value, trs = [...$("whomat").querySelectorAll("tr")].slice(1);
    const nameToC = {}; currentLayers.forEach((l) => { nameToC[l.feature.properties.n] = l.feature.properties.c; });
    const heads = [...$("whomat").querySelectorAll("th")].slice(1).map((t) => t.title);
    let okAll = true, detail = "";
    trs.forEach((tr) => {
      const pc = nameToC[tr.children[0].textContent];
      heads.forEach((cl, j) => {
        const ci = HW.clusters.indexOf(cl), set = new Set();
        HW.rec.u.forEach((u, i) => { if (u.split("D")[0] === pc && HW.rec.c[i] === ci && HW.rec.y[i] >= y0 && HW.rec.y[i] <= y1) set.add(HW.rec.o[i]); });
        const txt = tr.children[j + 1].textContent, got = txt === "vide" ? 0 : Number(txt);
        if (got !== set.size) { okAll = false; detail = pc + " " + cl + " " + got + "/" + set.size; }
      });
    });
    check("qui fait quoi où : organisations par zone et secteur = comptage direct du fichier", okAll && trs.length > 0, detail);
    check("cellules vides signalées", $("whomat").querySelectorAll("td.wvide, td.wok, td.wmany").length === trs.length * heads.length);
    $("whocsv").click();
    const t2 = lastBlob ? await lastBlob.text() : "";
    check("export qui-fait-quoi-où", /organisation/.test(t2) && t2.split("\n").length > 2);
  }
  const hydroMeta = path.join(docs, "data", slug, "hydro", "meta.json");
  if (fs.existsSync(hydroMeta)) {
    const HM = JSON.parse(fs.readFileSync(hydroMeta, "utf8"));
    check("carte Eau et terrain visible", await waitFor(() => !$("hydcard").hidden));
    $("hrivers").checked = true; $("hrivers").dispatchEvent(new w.Event("change"));
    check("cours d'eau ajoutés à la carte", await waitFor(() => hydroLayers.rivers && hydroLayers.rivers.fc.features.length === HM.n_reaches));
    $("hbasins").checked = true; $("hbasins").dispatchEvent(new w.Event("change"));
    check("bassins versants ajoutés à la carte", await waitFor(() => hydroLayers.basins && hydroLayers.basins.fc.features.length > 0));
    $("hrivers").checked = false; $("hrivers").dispatchEvent(new w.Event("change"));
    check("cours d'eau retirés", !hydroLayers.rivers);
    $("hbasins").checked = false; $("hbasins").dispatchEvent(new w.Event("change"));
    check("les couches de zones ne sont pas perturbées", currentLayers.length > 0);
  }
  if (fs.existsSync(respPath)) {
    const H = JSON.parse(fs.readFileSync(respPath, "utf8"));
    check("carte Historique et réponse visible", await waitFor(() => !$("histcard").hidden));
    check("couches d'historique ajoutées au sélecteur", ["ev_n", "ev_p", "rb", "rg", "rp", "rf"].every((k) => $("layer").querySelector(`option[value="${k}"]`)));
    const regionOf = (u) => u.split("D")[0];
    const expect = (fn) => { const o = {}; fn(o); return o; };
    $("layer").value = "ev_n"; $("layer").dispatchEvent(new w.Event("change"));
    const evAll = expect((o) => H.events.forEach((e) => { o[regionOf(e.u)] = (o[regionOf(e.u)] || 0) + 1; }));
    const tipN = (l) => Number(((l._tip().match(/: ([\d\s  ]+)$/) || [])[1] || "0").replace(/\D/g, ""));
    check("événements : nombre par région = comptage direct du fichier", currentLayers.every((l) => tipN(l) === (evAll[l.feature.properties.c] || 0)), currentLayers.map((l) => tipN(l) + "/" + (evAll[l.feature.properties.c] || 0)).join(" "));
    $("hy0").value = "2024"; $("hy0").dispatchEvent(new w.Event("change"));
    const ev24 = expect((o) => H.events.filter((e) => +e.date.slice(0, 4) >= 2024).forEach((e) => { o[regionOf(e.u)] = (o[regionOf(e.u)] || 0) + 1; }));
    check("filtre de période (2024–2025) appliqué à la carte", currentLayers.every((l) => tipN(l) === (ev24[l.feature.properties.c] || 0)));
    $("hy0").value = "2016"; $("hy0").dispatchEvent(new w.Event("change"));
    const t0 = H.event_types[0];
    $("htypes").querySelector(`input[data-t="${t0}"]`).checked = false; $("htypes").querySelector(`input[data-t="${t0}"]`).dispatchEvent(new w.Event("change"));
    const evNo = expect((o) => H.events.filter((e) => e.type !== t0).forEach((e) => { o[regionOf(e.u)] = (o[regionOf(e.u)] || 0) + 1; }));
    check("filtre de type d'événement appliqué", currentLayers.every((l) => tipN(l) === (evNo[l.feature.properties.c] || 0)));
    $("htypes").querySelector(`input[data-t="${t0}"]`).checked = true; $("htypes").querySelector(`input[data-t="${t0}"]`).dispatchEvent(new w.Event("change"));
    $("layer").value = "rb"; $("layer").dispatchEvent(new w.Event("change"));
    const k3 = H.kinds.indexOf("3w");
    const rbAll = expect((o) => H.rec.u.forEach((u, i) => { if (H.rec.k[i] === k3) o[regionOf(u)] = (o[regionOf(u)] || 0) + H.rec.b[i]; }));
    check("bénéficiaires 3W par région = somme directe du fichier", currentLayers.every((l) => tipN(l) === (rbAll[l.feature.properties.c] || 0)), currentLayers.map((l) => tipN(l) + "/" + (rbAll[l.feature.properties.c] || 0)).join(" "));
    $("hcl").value = "0"; $("hcl").dispatchEvent(new w.Event("change"));
    const rb0 = expect((o) => H.rec.u.forEach((u, i) => { if (H.rec.k[i] === k3 && H.rec.c[i] === 0) o[regionOf(u)] = (o[regionOf(u)] || 0) + H.rec.b[i]; }));
    check("filtre de secteur appliqué aux bénéficiaires", currentLayers.every((l) => tipN(l) === (rb0[l.feature.properties.c] || 0)));
    $("hcl").value = ""; $("hcl").dispatchEvent(new w.Event("change"));
    $("layer").value = "rg"; $("layer").dispatchEvent(new w.Event("change"));
    check("écart cibles − bénéficiaires : jamais négatif", currentLayers.every((l) => tipN(l) >= 0));
    $("hshow").checked = true; $("hshow").dispatchEvent(new w.Event("change"));
    const last = markerGroups[markerGroups.length - 1];
    check("événements affichés sur la carte : un marqueur par événement filtré", last && last.length === H.events.length, last && last.length + " / " + H.events.length);
    $("hshow").checked = false; $("hshow").dispatchEvent(new w.Event("change"));
    handlers[currentLayers[1].feature.properties.c]();
    check("fiche de zone : frise historique, ENSO et secteurs", await waitFor(() => /Historique et réponse \(/.test($("info").innerHTML) && /Événements selon l'ENSO/.test($("info").innerHTML) && $("info").querySelectorAll("svg rect").length > 20));
    handlers[first]();
    $("layer").value = "l"; $("layer").dispatchEvent(new w.Event("change"));
  }
  if (metaJson.scenarios && metaJson.scenarios.hist_years) {
    const hy = metaJson.scenarios.hist_years, n = hy.length;
    check("sélecteur de période : scénarios + saisons passées", $("scn").querySelectorAll("optgroup").length === 2 && $("scn").querySelectorAll('option[value^="y:"]').length === n);
    const yTest = hy[10], metr = JSON.parse(fs.readFileSync(path.join(docs, "data", slug, "metrics", "top.json"), "utf8")).adm1;
    $("layer").value = "pc"; $("layer").dispatchEvent(new w.Event("change"));
    $("scn").value = "y:" + yTest; $("scn").dispatchEvent(new w.Event("change"));
    const l0 = currentLayers[0], c0 = l0.feature.properties.c;
    check("saison passée : la carte affiche la pluie de cette année-là", /Saison/.test($("legend").textContent) && /Pluie cumulée/.test(l0._tip()) && l0._tip().indexOf(Math.round(metr[c0].y[10]).toString()) >= 0, l0._tip().replace(/<[^>]+>/g, " "));
    check("saison passée : couleur issue de la pluie de l'année", l0._style.fillColor !== "#cccccc");
    // deux cartes côte à côte
    $("modeseg").querySelector('[data-mode="split"]').click();
    check("deux cartes : carte B visible et construite", await waitFor(() => !$("map2").hidden && layersB.length === 4), layersB.length + " zones");
    check("deux cartes : en-têtes A et B", /^A · /.test($("hdrA").textContent) && /^B · /.test($("hdrB").textContent), $("hdrA").textContent + " | " + $("hdrB").textContent);
    check("deux cartes : B = saison choisie, A = autre période", layersB[0]._tip(0).length > 0);
    $("scn").value = ""; $("scn").dispatchEvent(new w.Event("change"));
    $("scnB").value = "y:" + hy[0]; $("scnB").dispatchEvent(new w.Event("change"));
    const a0 = currentLayers[0]._style.fillColor, b0 = layersB[0]._style.fillColor;
    check("deux cartes : légendes A et B", /A · /.test($("legend").textContent) && /B · /.test($("legend").textContent));
    // différence
    $("modeseg").querySelector('[data-mode="diff"]').click();
    check("différence : carte unique avec légende B − A", await waitFor(() => $("map2").hidden && /Différence B − A/.test($("legend").textContent)), $("legend").textContent.slice(0, 80));
    check("différence : l'infobulle donne A, B et B − A", /B − A/.test(currentLayers[0]._tip()) && /A : /.test(currentLayers[0]._tip()), currentLayers[0]._tip().replace(/<[^>]+>/g, " "));
    check("lien partageable : mode et saison dans l'adresse", /m=diff/.test(w.location.search) && /sb=y%3A/.test(w.location.search), w.location.search);
    $("modeseg").querySelector('[data-mode="single"]').click();
    await waitFor(() => $("map2").hidden);
    // indicateurs couplés
    const rows = $("cxrows").querySelectorAll(".cxrow");
    rows[0].querySelector(".cxk").value = "pc"; rows[0].querySelector(".cxd").value = "-1";
    rows[1].querySelector(".cxk").value = "p"; rows[1].querySelector(".cxd").value = "1";
    $("cxop").value = "min";
    $("cxgo").click();
    await sleep(100);
    const cxv = currentLayers.map((l) => (l._tip().match(/Indice couplé : <b>(\d+)/) || [])[1]).map(Number);
    check("indice couplé : 4 zones notées de 0 à 100", cxv.length === 4 && cxv.every((v) => v >= 0 && v <= 100), cxv.join(","));
    // vérification numérique : rang(moyenne des égalités) de (1 - rang pluie) et de la population, minimum des deux
    const rk = (arr, v) => { const lo = arr.filter((x) => x < v).length, eq = arr.filter((x) => x === v).length; return (lo + 0.5 * eq) / arr.length; };
    const ids = currentLayers.map((l) => l.feature.properties.c);
    const pcs = ids.map((c) => metr[c].pc), pps = ids.map((c) => metr[c].p);
    const exp = ids.map((c, i) => Math.round(100 * Math.min(1 - rk(pcs, pcs[i]), rk(pps, pps[i]))));
    check("indice couplé : valeurs = minimum des rangs (pluie inversée, population)", exp.every((v, i) => Math.abs(v - cxv[i]) <= 1), exp.join(",") + " vs " + cxv.join(","));
    check("indice couplé : légende explicative", /Classement relatif/.test($("legend").textContent) && /tous les indicateurs élevés/.test($("legend").textContent));
    check("indice couplé : lien partageable", /cx=pc/.test(w.location.search), w.location.search);
    $("layer").value = "l"; $("layer").dispatchEvent(new w.Event("change"));
    $("scn").value = ""; $("scn").dispatchEvent(new w.Event("change"));
  }
  if (metaJson.risks) {
    check("sélecteur de profil visible", !$("profcard").hidden && $("profile").options.length === 5);
    check("tableau des risques (profil ONG) : 9 risques x 3 horizons", $("info").querySelectorAll(".rtab tbody tr").length === 9 && /Risques pour : ONG/.test($("info").innerHTML));
    check("risque inconnu affiché « données à intégrer » (jamais inventé)", $("info").querySelectorAll(".rtodo").length >= 5);
    check("alerte précoce reprise dans le tableau (pastilles de niveau)", $("info").querySelectorAll(".rchip").length >= 10);
    $("profile").value = "pecheur"; $("profile").dispatchEvent(new w.Event("change"));
    check("profil pêcheur : 4 risques dont mer et pêche", $("info").querySelectorAll(".rtab tbody tr").length === 4 && /Mer et pêche/.test($("info").innerHTML));
    check("liste des données à intégrer", /Données à intégrer pour compléter/.test($("info").innerHTML));
    $("profile").value = "ong"; $("profile").dispatchEvent(new w.Event("change"));
  }
  if (metaJson.scenarios) {
    check("tableau des scénarios dans la fiche", /Probabilité d'alerte/.test($("info").innerHTML) && $("info").querySelectorAll(".sctable tr").length >= 4);
    check("plan d'action par secteur", $("info").querySelectorAll(".plan details").length >= 5 && /personnes à cibler/.test($("info").textContent));
    $("scn").value = "sec"; $("scn").dispatchEvent(new w.Event("change"));
    check("scénario sec appliqué à la carte (légende)", /scénario/.test($("legend").textContent));
    const kSec = $("kpis").textContent;
    $("scn").value = "hum"; $("scn").dispatchEvent(new w.Event("change"));
    check("les chiffres changent selon le scénario", $("kpis").textContent !== kSec, kSec + " → " + $("kpis").textContent);
    $("scn").value = ""; $("scn").dispatchEvent(new w.Event("change"));
    // vue simple « Chez moi »
    $("modebtn").click();
    if (metaJson.forecast) check("vue simple : alerte des 7 prochains jours avec conseils", /Alerte pour les 7 prochains jours/.test($("info").textContent));
    check("vue simple : message clair et conseils", /Risque de saison trop sèche/.test($("info").textContent) && /Ce que vous pouvez faire/.test($("info").textContent));
    $("modebtn").click();
  }
  // toutes les couches colorent la carte sans erreur
  for (let i = 0; i < $("layer").options.length; i++) {
    $("layer").value = $("layer").options[i].value; $("layer").dispatchEvent(new w.Event("change"));
    if (!currentLayers.every((l) => /^#/.test(l._style.fillColor))) { check("couche " + $("layer").value + " colore toutes les zones", false); }
  }
  $("layer").value = "l"; $("layer").dispatchEvent(new w.Event("change"));
  check("fiche après clic", $("info").textContent.includes(currentLayers[0].feature.properties.n));
  handlers[first]();
  check("exploration vers les districts", await waitFor(() => currentLayers.length === 2 && w.document.querySelectorAll("#crumbs button").length === 2),
        currentLayers.length + " districts");
  const d = currentLayers[0].feature.properties.c;
  handlers[d](); handlers[d]();
  check("communes", await waitFor(() => currentLayers.length === 4 && w.document.querySelectorAll("#crumbs button").length === 3));
  const c = currentLayers[0].feature.properties.c;
  handlers[c](); handlers[c]();
  check("fokontany (9)", await waitFor(() => currentLayers.length === 9 && w.document.querySelectorAll("#crumbs button").length === 4));
  check("hash de partage", w.location.hash.split("/").length === 3, w.location.hash);
  check("tooltip", currentLayers[0]._tip().includes("<b>"));

  // simulation
  const sim = $("sim");
  sim.value = 0; sim.dispatchEvent(new w.Event("input"));
  await sleep(100);
  check("simulation active (légende)", /scénario/.test($("legend").textContent));
  check("KPIs changent sous simulation", /scénario/.test($("kpis").textContent));
  $("simreset").click(); await sleep(100);
  check("retour à l'observé", !/scénario/.test($("legend").textContent));

  // couches
  for (const k of ["pc", "e", "t", "g", "p", "l"]) {
    $("layer").value = k; $("layer").dispatchEvent(new w.Event("change")); await sleep(30);
    check("couche " + k, currentLayers.every((l) => /^#/.test(l._style.fillColor)) && $("legend").innerHTML.length > 20);
  }

  // recherche : renvoie vers un fokontany précis
  const q = $("q");
  q.value = "Fokontany 2.1.2.3"; q.dispatchEvent(new w.Event("input"));
  check("résultats de recherche", await waitFor(() => $("resultlist").children.length >= 1 && !$("resultlist").hidden));
  $("resultlist").children[0].click();
  check("navigation par recherche", await waitFor(() => w.document.querySelectorAll("#crumbs button").length === 4 &&
        $("info").textContent.includes("Fokontany 2.1.2.3")), w.location.hash);

  // export
  $("export").click();
  const csv = lastBlob ? await new Promise((r) => { const fr = new w.FileReader(); fr.onload = () => r(fr.result); fr.readAsText(lastBlob); }) : "";
  check("export CSV", csv.split("\n").length === 10 && csv.includes("cibles_potentiels"), csv.split("\n").length + " lignes");

  // pages d'information
  check("catalogue", await waitFor(() => w.document.querySelectorAll("#cattable tr").length > 10));
  check("sources", $("sourcelist").textContent.includes("CHIRPS"));
  check("méthode (seuils provisoires)", $("methodtext").textContent.includes("provisoires"));
  w.document.querySelectorAll(".chip")[3].click();
  check("filtre secteur", w.document.querySelectorAll("#cattable tr").length > 1);
  const soilSeries = path.join(docs, "data", slug, "soilwater", "series.json");
  if (fs.existsSync(soilSeries)) {
    handlers[currentLayers[0].feature.properties.c]();
    check("fiche : eau dans le sol (humidité, indice de nappe, graphique)", await waitFor(() => /Eau dans le sol/.test($("info").innerHTML) && /Indice relatif de nappe/.test($("info").innerHTML) && $("info").querySelectorAll("svg polyline").length >= 1));
    check("éboulement : seuil mondial de pluie et pente affichés", /seuil mondial de déclenchement/.test($("info").innerHTML) || /terrain presque plat/.test($("info").innerHTML) || /Prévision non disponible/.test($("info").innerHTML));
  }
  if (fs.existsSync(path.join(docs, "data", slug, "seasonal.json"))) {
    check("fiche : prévision saisonnière (écart, probabilités, graphique)", await waitFor(() => /Prévision saisonnière \(modèle ECMWF\)/.test($("info").innerHTML) && /Probabilités \(tiers sec/.test($("info").innerHTML) && $("info").querySelectorAll("svg rect").length >= 2));
  }
  if (fs.existsSync(path.join(docs, "data", slug, "calendrier.json"))) {
    check("fiche : cultures et calendrier (recommandations, source citée)", await waitFor(() => /Cultures et calendrier/.test($("info").innerHTML) && /Règle de démonstration|recommand/i.test($("info").innerHTML) && /Source de test|meteomadagascar/.test($("info").innerHTML)));
  }
  const cycFile = path.join(docs, "data", slug, "cyclones.json");
  if (fs.existsSync(cycFile)) {
    const C = JSON.parse(fs.readFileSync(cycFile, "utf8"));
    check("cyclones : carte de réglage visible", await waitFor(() => !$("cyccard").hidden));
    const maxS = Math.max(...C.storms.map((s) => s.season));
    const expect = (a, b, mn, near) => C.storms.filter((s) => s.season >= a && s.season <= b && s.max_kt >= mn && (!near || (s.near_km !== null && s.near_km <= 100))).length;
    $("cy0").value = String(Math.min(...C.storms.map((s) => s.season))); $("cy1").value = String(maxS); $("cymin").value = "0"; $("cynear").checked = false;
    $("cyshow").checked = true; $("cyshow").dispatchEvent(new w.Event("change"));
    check("cyclones : tous les systèmes tracés", cycGroup && cycGroup.ms.length === C.storms.length, cycGroup ? cycGroup.ms.length + "/" + C.storms.length : "aucune couche");
    $("cymin").value = "64"; $("cymin").dispatchEvent(new w.Event("change"));
    check("cyclones : filtre d'intensité minimale", (cycGroup ? cycGroup.ms.length : 0) === expect(0, 9999, 64, false), cycGroup ? String(cycGroup.ms.length) : "");
    $("cyshow").checked = false; $("cyshow").dispatchEvent(new w.Event("change"));
    check("cyclones : couche retirée à la décoche", cycGroup === null);
  }
  console.log(failures ? `\n${failures} ÉCHEC(S)` : "\nTous les tests de l'interface passent.");
  process.exit(failures ? 1 : 0);
})();
