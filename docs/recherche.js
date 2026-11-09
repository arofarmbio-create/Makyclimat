/* Pages « Nappes » et « Preuves par module » (données : data/<pays>/recherche.json, scripts/build_site_recherche.py).
   Rend visibles les résultats de recherche avec leur incertitude et leurs tests (protocole doctoral : M3, H6, E4, M7). */
(function () {
  "use strict";
  var DEPOT = "https://github.com/arofarmbio-create/Makyclimat/blob/main/validation/";

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function liens(s) {
    // noms de fichiers du dossier validation → liens vers le dépôt
    return esc(s).replace(/([a-z0-9_]+\.(?:md|csv))/gi, function (f) {
      return '<a href="' + DEPOT + f + '" target="_blank" rel="noopener">' + f + "</a>";
    });
  }
  function badge(classe, texte) {
    var c = { ok: "rok", ko: "rko", partiel: "rpart", attente: "ratt" }[classe] || "ratt";
    return '<span class="rbadge ' + c + '">' + esc(texte) + "</span>";
  }
  function n(v, suf) { return v == null ? "—" : String(v).replace(".", ",") + (suf || ""); }

  function pageNappes(d) {
    var el = document.getElementById("nappestext");
    if (!el) return;
    var np = d.nappes, cb = np.combinaison || {}, sc = cb.scenario, v = (cb.par_scenario || {})[sc] || {};
    var h = "<h2>Nappes : ce que l'on sait, avec son incertitude</h2>";
    h += '<p class="note">Résultats de recherche, mis à jour le ' + esc(d.genere) + ". Chaque valeur est donnée avec sa fourchette "
      + "ou son niveau de preuve. La recharge n'est <b>pas validée</b> : trois cartes sont montrées côte à côte, et les tests qui les "
      + "jugent sont listés plus bas.</p>";
    h += '<div class="rbox"><b>Où en est la question de la recharge ?</b><ul>'
      + "<li>T2 (recharge transférée de 134 sites africains) surestime-t-elle dans le Grand Sud ? " + badge(/établi/.test(v.q1 || "") && !/non/.test(v.q1 || "") ? "ok" : "partiel", v.q1 || "—") + "</li>"
      + "<li>T2L (corrigée par les mesures malgaches) est-elle plus juste ? " + badge(/^établi/.test(v.q2 || "") ? "ok" : "ko", v.q2 || "—") + "</li>"
      + "</ul><p class=\"note\">Verdicts pour le dépôt de chlorure de la pluie retenu (« " + esc(sc || "—") + " », d'après le modèle MERRA-2 "
      + "corrigé par sa validation). Ils changent si le dépôt est plus faible : seule une mesure du chlorure de la pluie dans le Sud "
      + "tranchera (" + liens("combinaison_preuves.md") + ", " + liens("plan_mesures.md") + ").</p></div>";

    h += "<h3>Par région</h3>";
    h += '<p class="note">Niveau statique : médiane des fokontany et fourchette à 80 % (médianes des bornes). « Extrapolé » : part des '
      + "fokontany loin de tout forage mesuré, où la précision n'est pas connue. Recharge en mm/an : T2 = transfert africain ; "
      + "T2L = corrigée par les mesures malgaches (seulement dans son domaine, le Sud) ; T2K = avec le karst. Aucune n'est validée.</p>";
    h += '<div class="tablewrap"><table><thead><tr><th>Région</th><th>Fokontany</th><th>Niveau statique (m)</th><th>Fourchette à 80 %</th>'
      + "<th>Extrapolé</th><th>Forage le plus proche (km, médiane)</th><th>Recharge T2</th><th>T2L</th><th>T2K</th></tr></thead><tbody>";
    np.regions.forEach(function (r) {
      h += "<tr><td>" + esc(r.region) + "</td><td>" + r.fokontany + "</td><td>" + n(r.niveau_m) + "</td><td>" + n(r.niveau_bas80_m) + " à "
        + n(r.niveau_haut80_m) + "</td><td>" + Math.round(100 * r.part_extrapolee) + " %</td><td>" + n(r.distance_forage_km) + "</td><td>"
        + n(r.recharge_T2) + "</td><td>" + n(r.recharge_T2L) + "</td><td>" + n(r.recharge_T2K) + "</td></tr>";
    });
    h += "</tbody></table></div>";

    h += "<h3>Grands bassins versants les plus peuplés</h3>";
    h += '<p class="note">Bilan = prélèvements domestiques / recharge T2 (classe « faible » sous 0,1). Fiabilité selon le nombre de '
      + "relevés et la part extrapolée (" + liens("atlas_bassins.md") + ").</p>";
    h += '<div class="tablewrap"><table><thead><tr><th>Bassin</th><th>Population</th><th>Niveau (m)</th><th>Recharge T2 (mm/an)</th>'
      + "<th>Bilan</th><th>Classe</th><th>Fiabilité</th></tr></thead><tbody>";
    np.atlas.forEach(function (b) {
      h += "<tr><td>" + esc(b.nom) + "</td><td>" + b.population.toLocaleString("fr-FR") + "</td><td>" + n(b.niveau_m) + "</td><td>"
        + n(b.recharge_mm) + "</td><td>" + n(b.bilan) + "</td><td>" + esc(b.classe) + "</td><td>" + esc(b.fiabilite) + "</td></tr>";
    });
    h += "</tbody></table></div>";

    h += "<h3>Tests de la recharge (hypothèses fixées avant le calcul, échecs compris)</h3>";
    h += '<div class="tablewrap"><table><thead><tr><th>N°</th><th>Question</th><th>Résultat</th><th>Statut</th></tr></thead><tbody>';
    np.tests.forEach(function (t) {
      h += "<tr><td>" + esc(t.id) + "</td><td>" + esc(t.question) + "</td><td>" + liens(t.resultat) + "</td><td>" + badge(t.classe, t.statut) + "</td></tr>";
    });
    h += "</tbody></table></div>";
    el.innerHTML = h;
  }

  function pagePreuves(d) {
    var el = document.getElementById("preuvestext");
    if (!el) return;
    var h = "<h3>Preuves par module (registre des méthodes)</h3>";
    h += '<p class="note">Pour chaque module : le <b>type de résultat</b> (reconstitution d\'un événement passé, anticipation avant '
      + "l'événement, ou suivi pendant l'événement), les tests qui le jugent et leur statut, relus dans le registre "
      + "(" + liens("etat_des_lieux_registre.md") + "). « Puissance insuffisante » signifie que le test ne pouvait pas conclure avec les "
      + "données disponibles (" + liens("analyse_puissance_retro.md") + ").</p>";
    d.preuves.forEach(function (m) {
      h += '<details class="rmod"><summary><b>' + esc(m.module) + "</b> · <span class=\"note\">" + esc(m.type) + "</span> "
        + m.tests.map(function (t) { return badge(t.classe, t.id); }).join(" ") + "</summary>";
      if (m.remarque) h += '<p class="note">⚠ ' + esc(m.remarque) + "</p>";
      h += "<ul>" + m.tests.map(function (t) {
        return "<li>" + badge(t.classe, t.id) + " " + esc(t.question) + (t.resultat ? "<br><span class=\"note\">" + liens(t.resultat) + "</span>" : "")
          + "<br><span class=\"note\">Statut : " + esc(t.statut) + "</span></li>";
      }).join("") + "</ul></details>";
    });
    h += "<h3>Incertitudes affichées et manques</h3><ul><li>" + esc(d.calibrage_saisonnier) + "</li>"
      + d.manques.map(function (x) { return "<li>" + liens(x) + "</li>"; }).join("") + "</ul>";
    el.innerHTML = h;
  }

  fetch("data/mdg/recherche.json", { cache: "no-cache" })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (d) { pageNappes(d); pagePreuves(d); })
    .catch(function () {
      var el = document.getElementById("nappestext");
      if (el) el.innerHTML = '<p class="note">Données de recherche indisponibles pour le moment.</p>';
    });
})();
