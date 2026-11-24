/* ChronoGlobe: Themenebenen und Beiträge – reine Logik ohne Oberfläche.
   Genutzt von js/app.js (Anzeige auf dem Globus), js/editor.js (Editor) und tools/check_beitraege.js (CI).
   Format und Ablauf: docs/EDITOR.md.

   Themenebene (data/ebenen/<id>.json oder im Beitrag unter "ebene"):
     { format: 'chronoglobe-ebene/1', id, name, farbe: '#rrggbb', beschreibung, hinweis?,
       quellen: [{ zitat, url?, lizenz? }],                        // mindestens eine (docs/GRUNDREGELN.md)
       objekte: [{ id, typ: 'punkt'|'linie'|'flaeche', name, von, bis?, beschreibung?, beleg?, unsicher?,
                   koordinaten }] }                                 // punkt [lng, lat] · linie [[lng, lat], …] · flaeche [[lng, lat], …] (Ring)
     von/bis: Jahre (negativ = v. Chr.). Ohne bis bleibt ein Objekt bis zum Ende der Zeitleiste sichtbar.

   Beitrag (beitraege/<name>.json), entsteht im Editor und kommt als Pull Request ins Projekt:
     { format: 'chronoglobe-beitrag/1', art: 'neue-ebene'|'aenderung', titel, begruendung,
       belege: [{ zitat, url? }],                                   // mindestens einer
       ebene?: Themenebene,                                         // art 'neue-ebene'
       ziel?: { bereich, datei, id, name },                         // art 'aenderung': was geändert werden soll
       vorschlag?: { text, felder?: { name?, von?, bis? }, geometrie?: { typ, koordinaten } } } */
(function (wurzel) {
  'use strict';

  var TYPEN = { punkt: 'Ort (Punkt)', linie: 'Linie (Weg, Grenze, Mauer)', flaeche: 'Fläche (Gebiet)' };
  var BEREICHE = {
    'reich-gebiet': 'Gebiet eines Reiches (Fläche)', 'reich-ort': 'Stadt bzw. Ort eines Reiches', 'reich-ereignis': 'Ereignis eines Reiches (Infoband)',
    'handelsroute': 'Handelsroute', 'handelsort': 'Handelsort', 'kontakt': 'Gesandtschaft bzw. Kontakt',
    'text': 'Schülertext', 'vignette': 'Schriftrolle (Vignetten eines Reiches)', 'ebene': 'Themenebene', 'sonstiges': 'Sonstiges'
  };
  var ID = /^[a-z0-9][a-z0-9-]{1,59}$/;

  function zahl(x) { return typeof x === 'number' && isFinite(x); }
  function jahrOk(x) { return zahl(x) && Math.round(x) === x && x >= -10000 && x <= 2100; }
  function lngLat(p) { return Array.isArray(p) && p.length >= 2 && zahl(p[0]) && zahl(p[1]) && Math.abs(p[0]) <= 180 && Math.abs(p[1]) <= 90; }
  function text(x, min) { return typeof x === 'string' && x.trim().length >= (min || 1); }
  function belegeOk(L) { return Array.isArray(L) && L.some(function (q) { return q && text(q.zitat, 5); }); }

  function geometriePruefen(typ, k, wo, f) {
    if (typ === 'punkt') { if (!lngLat(k)) f.push(wo + ': Koordinaten [Länge, Breite] fehlen oder sind ungültig'); return; }
    if (!Array.isArray(k) || !k.every(lngLat)) { f.push(wo + ': Koordinaten ungültig'); return; }
    if (typ === 'linie' && k.length < 2) f.push(wo + ': eine Linie braucht mindestens 2 Punkte');
    if (typ === 'flaeche' && k.length < 3) f.push(wo + ': eine Fläche braucht mindestens 3 Punkte');
  }

  /* Themenebene prüfen → Liste von Fehlern (leer = in Ordnung) */
  function ebenePruefen(d) {
    var f = [];
    if (!d || typeof d !== 'object') return ['keine Ebene'];
    if (d.format !== 'chronoglobe-ebene/1') f.push('format muss "chronoglobe-ebene/1" sein');
    if (!ID.test(d.id || '')) f.push('id: nur Kleinbuchstaben, Ziffern und Bindestriche (2–60 Zeichen)');
    if (!text(d.name, 3)) f.push('name fehlt');
    if (!/^#[0-9a-fA-F]{6}$/.test(d.farbe || '')) f.push('farbe: Hex-Farbe wie #c08a2e');
    if (!text(d.beschreibung, 10)) f.push('beschreibung fehlt (mindestens ein Satz)');
    if (!belegeOk(d.quellen)) f.push('quellen: mindestens eine Quelle mit Zitat (docs/GRUNDREGELN.md)');
    if (!Array.isArray(d.objekte) || !d.objekte.length) { f.push('objekte: mindestens ein Objekt'); return f; }
    var ids = {};
    d.objekte.forEach(function (o, i) {
      var wo = 'Objekt ' + (i + 1) + (o && o.name ? ' „' + o.name + '“' : '');
      if (!o || typeof o !== 'object') { f.push(wo + ': ungültig'); return; }
      if (!ID.test(o.id || '')) f.push(wo + ': id ungültig');
      else if (ids[o.id]) f.push(wo + ': id „' + o.id + '“ doppelt'); else ids[o.id] = 1;
      if (!TYPEN[o.typ]) f.push(wo + ': typ muss punkt, linie oder flaeche sein');
      if (!text(o.name, 2)) f.push(wo + ': name fehlt');
      if (!jahrOk(o.von)) f.push(wo + ': von muss eine ganze Jahreszahl sein (v. Chr. negativ)');
      if (o.bis != null && (!jahrOk(o.bis) || o.bis < o.von)) f.push(wo + ': bis muss eine Jahreszahl ≥ von sein');
      if (TYPEN[o.typ]) geometriePruefen(o.typ, o.koordinaten, wo, f);
    });
    return f;
  }

  /* Beitrag prüfen → Liste von Fehlern */
  function beitragPruefen(b) {
    var f = [];
    if (!b || typeof b !== 'object') return ['kein Beitrag'];
    if (b.format !== 'chronoglobe-beitrag/1') f.push('format muss "chronoglobe-beitrag/1" sein');
    if (!text(b.titel, 5)) f.push('titel fehlt');
    if (!text(b.begruendung, 20)) f.push('begruendung: bitte in ein, zwei Sätzen erklären, warum (mindestens 20 Zeichen)');
    if (!belegeOk(b.belege)) f.push('belege: mindestens ein Beleg mit Zitat (Literatur, Quelle oder Datensatz)');
    if (b.art === 'neue-ebene') {
      ebenePruefen(b.ebene).forEach(function (x) { f.push('Ebene: ' + x); });
    } else if (b.art === 'aenderung') {
      var z = b.ziel || {};
      if (!BEREICHE[z.bereich]) f.push('ziel.bereich unbekannt');
      if (z.bereich !== 'sonstiges' && !text(z.name)) f.push('ziel: bitte das Objekt auswählen, das geändert werden soll');
      var v = b.vorschlag || {};
      if (!text(v.text, 10)) f.push('vorschlag.text: beschreiben, was geändert werden soll');
      var fe = v.felder || {};
      if (fe.von != null && !jahrOk(fe.von)) f.push('vorschlag.felder.von: ganze Jahreszahl');
      if (fe.bis != null && !jahrOk(fe.bis)) f.push('vorschlag.felder.bis: ganze Jahreszahl');
      if (v.geometrie) geometriePruefen(v.geometrie.typ, v.geometrie.koordinaten, 'vorschlag.geometrie', f);
    } else f.push('art muss "neue-ebene" oder "aenderung" sein');
    return f;
  }

  /* Anzeige */
  function sichtbar(o, y) { return o.von <= y && (o.bis == null || y <= o.bis); }
  function imJahr(d, y) { return d && Array.isArray(d.objekte) ? d.objekte.filter(function (o) { return sichtbar(o, y); }) : []; }
  function spanne(d) {
    var von = Infinity, bis = -Infinity, offen = false;
    (d.objekte || []).forEach(function (o) { von = Math.min(von, o.von); if (o.bis == null) offen = true; else bis = Math.max(bis, o.bis); });
    return { von: von, bis: offen ? null : bis };
  }
  function jahrText(y) { return y < 0 ? (-y) + ' v. Chr.' : y + ' n. Chr.'; }
  function zeitText(o) { return o.bis == null ? 'ab ' + jahrText(o.von) : o.von === o.bis ? jahrText(o.von) : jahrText(o.von) + ' bis ' + jahrText(o.bis); }
  function schluessel(d, y) { return imJahr(d, y).map(function (o) { return o.id; }).join('.'); }
  /* Flächen als geschlossener Umriss (für die Linienebene des Globus) */
  function umriss(o) { var k = o.koordinaten.slice(); if (k.length && (k[0][0] !== k[k.length - 1][0] || k[0][1] !== k[k.length - 1][1])) k.push(k[0]); return k; }

  /* Dateiname und GitHub-Adresse für einen Pull Request (ohne Server: GitHubs „Neue Datei“-Seite mit Inhalt).
     Wer keine Schreibrechte hat, bekommt von GitHub automatisch eine Kopie (Fork) und einen Pull Request angeboten. */
  function slug(t) {
    return String(t || 'beitrag').toLowerCase().replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss')
      .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 50) || 'beitrag';
  }
  function dateiname(b, heute) { return 'beitraege/' + (heute || new Date().toISOString().slice(0, 10)) + '-' + slug(b.titel) + '.json'; }
  var URL_GRENZE = 7500;   // längere Adressen schneiden Browser bzw. GitHub ab → dann Datei hochladen
  function githubAdresse(repo, zweig, b, heute) {
    var u = 'https://github.com/' + repo + '/new/' + zweig + '?filename=' + encodeURIComponent(dateiname(b, heute)) +
      '&value=' + encodeURIComponent(JSON.stringify(b, null, 2) + '\n');
    return u.length <= URL_GRENZE ? u : null;
  }
  function githubHochladen(repo, zweig) { return 'https://github.com/' + repo + '/upload/' + zweig + '/beitraege'; }

  var Themen = {
    TYPEN: TYPEN, BEREICHE: BEREICHE,
    ebenePruefen: ebenePruefen, beitragPruefen: beitragPruefen,
    imJahr: imJahr, sichtbar: sichtbar, spanne: spanne, zeitText: zeitText, jahrText: jahrText, schluessel: schluessel, umriss: umriss,
    slug: slug, dateiname: dateiname, githubAdresse: githubAdresse, githubHochladen: githubHochladen
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = Themen; else wurzel.Themen = Themen;
})(typeof self !== 'undefined' ? self : this);
