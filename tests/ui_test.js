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
w.L = {
  map() { return { setView() { return this; }, fitBounds() {}, removeLayer() {}, invalidateSize() {} }; },
  tileLayer() { return { addTo() {} }; },
  geoJSON(fc, opts) {
    const layers = fc.features.map((f) => {
      const layer = { feature: f, on(ev, fn) { if (ev === "click") handlers[f.properties.c] = fn; },
                      bindTooltip(fn) { this._tip = fn; }, getBounds() { return {}; }, _style: opts.style(f) };
      opts.onEachFeature(f, layer);
      return layer;
    });
    currentLayers = layers;
    return { addTo() { return this; }, getBounds() { return {}; },
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
  check("badge de date", /Pluie jusqu'au/.test($("through").textContent), $("through").textContent);
  const metaJson = JSON.parse(fs.readFileSync(path.join(docs, "data", slug, "meta.json"), "utf8"));
  check("6 indicateurs de base + indicateurs externes affichables",
        $("layer").options.length === 6 + (metaJson.scenarios ? 3 : 0) + (metaJson.forecast ? 6 : 0) + metaJson.external.length, $("layer").options.length + " couches");
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
    $("layer").value = "l"; $("layer").dispatchEvent(new w.Event("change"));
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
  console.log(failures ? `\n${failures} ÉCHEC(S)` : "\nTous les tests de l'interface passent.");
  process.exit(failures ? 1 : 0);
})();
