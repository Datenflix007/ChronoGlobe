/* ChronoGlobe: KI-Assistent und Import für den Editor – reine Logik ohne Oberfläche (auch in Node nutzbar).

   Ablauf (docs/EDITOR.md, Abschnitt „KI-Assistent“):
     1. KI.prompt({ modus, datensatz, dateiname, thema, hinweise }) → Text, den man in eine KI der Wahl kopiert.
        Der Prompt enthält das Zielformat, die Grundregeln und verlangt einen Block "_editor" mit Anweisungen
        für den Editor (Kartenausschnitt, Startjahr, Prüfhinweise, ausgelassene Einträge).
     2. KI.antwortLesen(text) → { beitrag, editor, hinweise, fehler }: liest die Antwort der KI robust ein
        (Codeblöcke, Kommentare, Kommas am Ende, Zahlen als Text, fehlende ids, GeoJSON statt Ebene …).
     3. Ohne KI: KI.importieren(text, dateiname) → { objekte, hinweise, fehler } aus GeoJSON, CSV oder JSON-Liste.

   Datenschutz: Hier wird nichts gesendet. Den Prompt kopiert die Person selbst in eine KI ihrer Wahl. */
(function (wurzel) {
  'use strict';
  var Themen = wurzel.Themen || (typeof require === 'function' ? require('./themen.js') : null);

  /* ---------- Prompt ---------- */
  var BEISPIEL = {
    format: 'chronoglobe-beitrag/1', art: 'neue-ebene',
    titel: 'Neue Ebene: Pyramiden im Alten Ägypten',
    begruendung: 'Die Pyramiden zeigen, wie der Staat des Alten Reiches Arbeit und Vorräte bündeln konnte.',
    belege: [{ zitat: 'Lehner, Mark: The Complete Pyramids. London 1997.' }],
    ebene: {
      format: 'chronoglobe-ebene/1', id: 'pyramiden-im-alten-aegypten', name: 'Pyramiden im Alten Ägypten', farbe: '#e0b040',
      beschreibung: 'Große Königspyramiden des Alten Reiches.',
      hinweis: 'Baujahre nach der konventionellen Chronologie, Abweichungen von mehreren Jahrzehnten (umstritten).',
      quellen: [{ zitat: 'Lehner, Mark: The Complete Pyramids. London 1997.' }],
      objekte: [
        { id: 'cheops', typ: 'punkt', name: 'Cheops-Pyramide', von: -2560, unsicher: true, beschreibung: 'Größte Pyramide, ursprünglich rund 146 m hoch.', koordinaten: [31.134, 29.979] },
        { id: 'nil-memphis', typ: 'linie', name: 'Nil bei Memphis', von: -3000, koordinaten: [[31.25, 30.1], [31.26, 29.9], [31.24, 29.6]] }
      ]
    },
    _editor: { karte: { zentrum: [31.2, 29.9], zoom: 12 }, jahr: -2560,
      pruefen: ['Baujahr der Cheops-Pyramide: Forschung schwankt um mehrere Jahrzehnte.'], ausgelassen: [] }
  };
  var BEISPIEL_AENDERUNG = {
    format: 'chronoglobe-beitrag/1', art: 'aenderung', titel: 'Dakien: Jahr der Provinzgründung',
    begruendung: 'Die Provinz Dacia wurde nach dem zweiten Dakerkrieg 106 n. Chr. eingerichtet.',
    belege: [{ zitat: 'Der Neue Pauly, Art. Dacia.' }],
    ziel: { bereich: 'reich-gebiet', name: 'Dacia' },
    vorschlag: { text: 'Beginn der Provinz auf 106 n. Chr. setzen.', felder: { von: 106 } },
    _editor: { pruefen: ['Ist im Globus die Provinz oder das ganze Gebiet gemeint?'] }
  };

  function regeln(modus) {
    var r = [
      'Übernimm nur, was im Datensatz steht oder in der Fachliteratur gesichert ist. Erfinde keine Orte, Jahre, Koordinaten, Zitate oder Seitenzahlen. Fehlt eine Pflichtangabe, lass den Eintrag weg und nenne ihn in "_editor.ausgelassen" mit Grund.',
      'Jahre als ganze Zahlen, v. Chr. negativ: 2560 v. Chr. = -2560, 117 n. Chr. = 117. Bei „um“, „ca.“ oder Spannen das übliche Jahr nehmen und "unsicher": true setzen.',
      'Schreibe Umstrittenes als umstritten („Manche Forschende datieren …, andere …“) – in "hinweis" der Ebene oder in der "beschreibung" des Objekts.',
      'Sprache: Deutsch, verständlich für Schülerinnen und Schüler der Sekundarstufe I. "beschreibung" je Objekt höchstens zwei kurze Sätze.',
      '"belege" und "quellen" nennen echte bibliografische Angaben: den Datensatz selbst (Titel, Herausgeber, Jahr, Lizenz, Link) und Literatur, die im Datensatz genannt ist. Keine erfundenen Titel, keine Seitenzahlen aus dem Gedächtnis.',
      'Keine personenbezogenen Daten lebender Personen.'
    ];
    if (modus !== 'aenderung') r.splice(1, 0,
      'Koordinaten als [Länge, Breite] in Dezimalgrad mit höchstens 3 Nachkommastellen – zuerst Ost/West, dann Nord/Süd (Kairo: [31.236, 30.044]). Westliche Länge und südliche Breite negativ. Prüfe, dass jeder Ort in der richtigen Gegend liegt.',
      '"typ": "punkt" für Orte ("koordinaten": [lng, lat]), "linie" für Wege, Grenzen, Mauern, Flüsse ("koordinaten": [[lng, lat], …], mindestens 2 Punkte), "flaeche" für Gebiete ("koordinaten": [[lng, lat], …], mindestens 3 Eckpunkte, Ring nicht schließen).',
      '"id" (Ebene und Objekte): nur Kleinbuchstaben, Ziffern und Bindestriche, ä → ae, ö → oe, ü → ue, ß → ss; jede Objekt-id nur einmal.',
      '"von" ist das Jahr, ab dem das Objekt auf dem Globus erscheint (z. B. Bau, Gründung). "bis" weglassen, wenn es bis heute besteht oder sichtbar bleiben soll.',
      '"farbe": eine gut sichtbare Hex-Farbe wie #e0b040, passend zum Thema.');
    return r;
  }

  function prompt(o) {
    o = o || {};
    var modus = o.modus === 'aenderung' ? 'aenderung' : 'neue-ebene';
    var daten = String(o.datensatz || '').trim();
    var L = [];
    L.push('Du hilfst mir, Daten für **ChronoGlobe** aufzubereiten – einen interaktiven Geschichtsglobus mit Zeitleiste für den Schulunterricht.');
    L.push('');
    if (modus === 'neue-ebene') {
      L.push('## Aufgabe');
      L.push('Wandle den Datensatz unten in **eine neue Themenebene** um: genau ein JSON-Objekt im Format "chronoglobe-beitrag/1" mit "art": "neue-ebene".' +
        (o.thema ? ' Thema der Ebene: ' + o.thema + '.' : ''));
    } else {
      L.push('## Aufgabe');
      L.push('Formuliere aus dem Material unten **einen Änderungsvorschlag** an bestehenden Daten des Globus: genau ein JSON-Objekt im Format "chronoglobe-beitrag/1" mit "art": "aenderung".' +
        (o.thema ? ' Es geht um: ' + o.thema + '.' : ''));
      L.push('Erlaubte Werte für "ziel.bereich": ' + Object.keys(Themen.BEREICHE).map(function (k) { return '"' + k + '" (' + Themen.BEREICHE[k] + ')'; }).join(', ') + '.');
      L.push('"ziel.name" ist der Name des Objekts, wie er auf dem Globus heißt (z. B. ein Provinz-, Orts- oder Routenname). "vorschlag.felder" nur für neue Werte von name, von oder bis.');
    }
    L.push('');
    L.push('## Regeln');
    regeln(modus).forEach(function (r, i) { L.push((i + 1) + '. ' + r); });
    L.push('');
    L.push('## Anweisungen für den Editor');
    L.push('Füge dem JSON ein Feld "_editor" hinzu. Der Editor von ChronoGlobe liest es beim Einfügen:');
    if (modus === 'neue-ebene') {
      L.push('- "karte": { "zentrum": [lng, lat], "zoom": 1–40 } – Kartenausschnitt, in dem alle Objekte gut zu sehen sind (1 = ganze Welt, 10 ≈ ein Land, 30 ≈ eine Region).');
      L.push('- "jahr": ein Jahr, in dem möglichst viele Objekte sichtbar sind.');
    }
    L.push('- "pruefen": Liste kurzer Hinweise, was ein Mensch vor dem Einreichen nachprüfen soll (unsichere Lagen, umstrittene Jahre, Umrechnungen).');
    L.push('- "ausgelassen": Liste der Einträge aus dem Datensatz, die du weglassen musstest, jeweils mit Grund.');
    L.push('');
    L.push('## Beispiel für das Format');
    L.push('```json');
    L.push(JSON.stringify(modus === 'neue-ebene' ? BEISPIEL : BEISPIEL_AENDERUNG, null, 2));
    L.push('```');
    L.push('');
    if (o.hinweise && String(o.hinweise).trim()) { L.push('## Zusätzliche Wünsche'); L.push(String(o.hinweise).trim()); L.push(''); }
    L.push('## Datensatz' + (o.dateiname ? ' (' + o.dateiname + ')' : ''));
    L.push(daten ? '```\n' + daten + '\n```' : '(Hier den Datensatz einfügen.)');
    L.push('');
    L.push('## Antwort');
    L.push('Antworte ausschließlich mit dem fertigen JSON in einem einzigen ```json-Codeblock, ohne weiteren Text davor oder danach.');
    return L.join('\n');
  }

  /* ---------- Antwort der KI einlesen ---------- */
  // Zeilen- und Blockkommentare entfernen, aber nicht innerhalb von Zeichenketten (URLs!)
  function ohneKommentare(t) {
    var out = '', inStr = false;
    for (var i = 0; i < t.length; i++) {
      var c = t[i];
      if (inStr) { out += c; if (c === '\\') { out += t[++i] || ''; } else if (c === '"') inStr = false; continue; }
      if (c === '"') { inStr = true; out += c; continue; }
      if (c === '/' && t[i + 1] === '/') { while (i < t.length && t[i] !== '\n') i++; out += '\n'; continue; }
      if (c === '/' && t[i + 1] === '*') { var e = t.indexOf('*/', i + 2); i = e < 0 ? t.length : e + 1; continue; }
      out += c;
    }
    return out;
  }
  function jsonAusText(text) {
    var t = String(text || '').trim(), m = /```(?:json|JSON)?\s*\n([\s\S]*?)```/.exec(t);
    if (m) t = m[1].trim();
    else { var a = t.search(/[{[]/), b = Math.max(t.lastIndexOf('}'), t.lastIndexOf(']')); if (a >= 0 && b > a) t = t.slice(a, b + 1); }
    var hinweise = [];
    try { return { wert: JSON.parse(t), hinweise: hinweise }; } catch (e1) {
      // häufige Fehler von Sprachmodellen reparieren: Kommentare, Kommas vor } ], typografische Anführungszeichen
      var r = ohneKommentare(t.replace(/[“”„]/g, '"')).replace(/,\s*([}\]])/g, '$1');
      try { hinweise.push('JSON repariert (Kommentare, Kommas oder Anführungszeichen)'); return { wert: JSON.parse(r), hinweise: hinweise }; }
      catch (e2) { return { fehler: 'Kein gültiges JSON: ' + e1.message }; }
    }
  }
  function zahl(x) {
    if (typeof x === 'number') return isFinite(x) ? x : null;
    if (typeof x !== 'string') return null;
    var s = x.trim().replace(/\s/g, '').replace(/^(um|ca\.?|etwa|circa)/i, ''), m = /^(\d+)(v\.?Chr\.?|BC|BCE|v\.u\.Z\.?)$/i.exec(s);
    if (m) return -Number(m[1]);
    s = s.replace(/(n\.?Chr\.?|AD|CE|u\.Z\.?)$/i, '').replace(',', '.').replace('−', '-');
    var n = Number(s); return s !== '' && isFinite(n) ? n : null;
  }
  function eindeutigeIds(objekte, hinweise) {
    var vergeben = {}, n = 0;
    objekte.forEach(function (o) {
      var id = /^[a-z0-9][a-z0-9-]{1,59}$/.test(o.id || '') ? o.id : Themen.slug(o.name || o.id || 'objekt');
      if (id.length < 2) id = id + '-1';
      var x = id, k = 1; while (vergeben[x]) x = id.slice(0, 55) + '-' + (++k);
      if (x !== o.id) n++;
      o.id = x; vergeben[x] = 1;
    });
    if (n) hinweise.push(n + ' Objekt-ids ergänzt oder vereinheitlicht');
  }
  /* Objekt säubern: Zahlen aus Text, Geometrie prüfen; gibt null zurück, wenn nichts zu retten ist */
  function objektSaeubern(o, hinweise) {
    if (!o || typeof o !== 'object') return null;
    var x = Object.assign({}, o);
    ['von', 'bis'].forEach(function (k) { if (x[k] != null) { var z = zahl(x[k]); x[k] = z == null ? null : Math.round(z); } });
    if (x.bis == null) delete x.bis;
    if (!x.typ) x.typ = Array.isArray(x.koordinaten) && typeof x.koordinaten[0] === 'number' ? 'punkt' : 'linie';
    var p = function (q) { return Array.isArray(q) && q.length >= 2 ? [Math.round(zahl(q[0]) * 1000) / 1000, Math.round(zahl(q[1]) * 1000) / 1000] : null; };
    if (x.typ === 'punkt') x.koordinaten = p(x.koordinaten);
    else if (Array.isArray(x.koordinaten)) {
      var k = x.koordinaten.map(p).filter(Boolean);
      if (x.typ === 'flaeche' && k.length > 3 && k[0][0] === k[k.length - 1][0] && k[0][1] === k[k.length - 1][1]) k.pop();
      x.koordinaten = k;
    }
    return x;
  }
  /* Liegen (fast) alle Punkte so, als wären Länge und Breite vertauscht? (|Breite| > 90 nur bei vertauschten Werten möglich) */
  function vertauschtVerdacht(objekte) {
    var n = 0, alle = 0;
    objekte.forEach(function (o) { (o.typ === 'punkt' ? [o.koordinaten] : o.koordinaten || []).forEach(function (q) { if (!q) return; alle++; if (Math.abs(q[1]) > 90 && Math.abs(q[0]) <= 90) n++; }); });
    return alle && n / alle > 0.5;
  }
  function tauschen(objekte) {
    objekte.forEach(function (o) {
      if (o.typ === 'punkt') { if (o.koordinaten) o.koordinaten = [o.koordinaten[1], o.koordinaten[0]]; }
      else o.koordinaten = (o.koordinaten || []).map(function (q) { return [q[1], q[0]]; });
    });
  }
  function ebeneSaeubern(e, hinweise) {
    e = Object.assign({ format: 'chronoglobe-ebene/1' }, e);
    if (!e.format) e.format = 'chronoglobe-ebene/1';
    if (!e.id && e.name) e.id = Themen.slug(e.name);
    if (!Array.isArray(e.quellen)) e.quellen = e.quellen ? [e.quellen] : [];
    e.quellen = e.quellen.map(function (q) { return typeof q === 'string' ? { zitat: q } : q; });
    var vorher = (e.objekte || []).length;
    e.objekte = (e.objekte || []).map(function (o) { return objektSaeubern(o, hinweise); }).filter(Boolean);
    if (e.objekte.length < vorher) hinweise.push((vorher - e.objekte.length) + ' unbrauchbare Objekte entfernt');
    if (vertauschtVerdacht(e.objekte)) { tauschen(e.objekte); hinweise.push('Länge und Breite waren vertauscht und wurden getauscht – bitte auf der Karte prüfen'); }
    eindeutigeIds(e.objekte, hinweise);
    return e;
  }
  function antwortLesen(text) {
    var j = jsonAusText(text);
    if (j.fehler) return { fehler: [j.fehler] };
    var w = j.wert, hinweise = j.hinweise, b;
    if (Array.isArray(w)) { w = { format: 'chronoglobe-ebene/1', objekte: w }; hinweise.push('Liste von Objekten als Ebene übernommen'); }
    if (w && w.type === 'FeatureCollection') { var g = geojsonZuObjekte(w, hinweise); w = { format: 'chronoglobe-ebene/1', objekte: g }; hinweise.push('GeoJSON in eine Ebene umgewandelt'); }
    if (w && (w.format === 'chronoglobe-ebene/1' || (w.objekte && !w.art))) {
      b = { format: 'chronoglobe-beitrag/1', art: 'neue-ebene', titel: w.name ? 'Neue Ebene: ' + w.name : '', begruendung: '', belege: (w.quellen || []).slice(), ebene: w, _editor: w._editor };
      delete w._editor; hinweise.push('Nur eine Ebene erhalten – Beitrag drumherum ergänzt (Titel, Begründung, Belege bitte prüfen)');
    } else b = w;
    if (!b || typeof b !== 'object') return { fehler: ['Die Antwort enthält kein JSON-Objekt'] };
    var editor = b._editor && typeof b._editor === 'object' ? b._editor : {}; delete b._editor;
    b.format = 'chronoglobe-beitrag/1';
    if (!b.art) b.art = b.ebene ? 'neue-ebene' : 'aenderung';
    if (!Array.isArray(b.belege)) b.belege = b.belege ? [b.belege] : [];
    b.belege = b.belege.map(function (q) { return typeof q === 'string' ? { zitat: q } : q; });
    if (b.art === 'neue-ebene') b.ebene = ebeneSaeubern(b.ebene || {}, hinweise);
    if (b.art === 'aenderung') {
      b.ziel = b.ziel || {}; b.vorschlag = b.vorschlag || { text: '' };
      var f = b.vorschlag.felder || {}; ['von', 'bis'].forEach(function (k) { if (f[k] != null) f[k] = zahl(f[k]) == null ? null : Math.round(zahl(f[k])); });
      if (b.vorschlag.geometrie) { var go = objektSaeubern(b.vorschlag.geometrie, hinweise); b.vorschlag.geometrie = { typ: go.typ, koordinaten: go.koordinaten }; }
    }
    ['pruefen', 'ausgelassen'].forEach(function (k) { if (!Array.isArray(editor[k])) editor[k] = editor[k] ? [String(editor[k])] : []; });
    return { beitrag: b, editor: editor, hinweise: hinweise, fehler: Themen.beitragPruefen(b) };
  }

  /* ---------- Direkter Import: GeoJSON, CSV, JSON-Liste ---------- */
  var FELD = {
    name: /^(name|titel|title|label|bezeichnung|ort|site|place)$/i,
    lat: /^(lat|latitude|breite|breitengrad|y)$/i, lng: /^(lng|lon|long|longitude|laenge|länge|längengrad|x)$/i,
    von: /^(von|start|beginn|begin|from|jahr|year|date|datum|anfang)$/i, bis: /^(bis|ende|end|to|until)$/i,
    beschreibung: /^(beschreibung|description|desc|text|info|notiz|note)$/i, beleg: /^(beleg|quelle|source|reference|ref|literatur)$/i,
    typ: /^(typ|type|art|kategorie|category)$/i, unsicher: /^(unsicher|uncertain)$/i
  };
  function feldWert(obj, art) { for (var k in obj) if (FELD[art].test(k) && obj[k] != null && obj[k] !== '') return obj[k]; return null; }
  function ausEintrag(p, geo) {
    var o = { name: String(feldWert(p, 'name') || '').trim(), von: zahl(feldWert(p, 'von')), bis: zahl(feldWert(p, 'bis')) };
    var be = feldWert(p, 'beschreibung'), bl = feldWert(p, 'beleg'); if (be) o.beschreibung = String(be); if (bl) o.beleg = String(bl);
    var u = feldWert(p, 'unsicher'); if (u === true || /^(ja|yes|true|1|x)$/i.test(String(u || ''))) o.unsicher = true;
    if (geo) { o.typ = geo.typ; o.koordinaten = geo.koordinaten; }
    else { var la = zahl(feldWert(p, 'lat')), ln = zahl(feldWert(p, 'lng')); if (la != null && ln != null) { o.typ = 'punkt'; o.koordinaten = [ln, la]; } }
    if (o.von != null) o.von = Math.round(o.von); if (o.bis != null) o.bis = Math.round(o.bis); else delete o.bis;
    return o;
  }
  function geojsonZuObjekte(fc, hinweise) {
    var out = [], ohne = 0;
    (fc.features || []).forEach(function (f) {
      var g = f && f.geometry; if (!g) { ohne++; return; }
      var teile = [];
      if (g.type === 'Point') teile.push({ typ: 'punkt', koordinaten: g.coordinates });
      else if (g.type === 'MultiPoint') g.coordinates.forEach(function (c) { teile.push({ typ: 'punkt', koordinaten: c }); });
      else if (g.type === 'LineString') teile.push({ typ: 'linie', koordinaten: g.coordinates });
      else if (g.type === 'MultiLineString') g.coordinates.forEach(function (c) { teile.push({ typ: 'linie', koordinaten: c }); });
      else if (g.type === 'Polygon') teile.push({ typ: 'flaeche', koordinaten: g.coordinates[0].slice(0, -1) });
      else if (g.type === 'MultiPolygon') g.coordinates.forEach(function (c) { teile.push({ typ: 'flaeche', koordinaten: c[0].slice(0, -1) }); });
      else { ohne++; return; }
      teile.forEach(function (t, i) { var o = ausEintrag(f.properties || {}, t); if (teile.length > 1) o.name = (o.name || 'Teil') + ' (' + (i + 1) + ')'; out.push(o); });
    });
    if (ohne) hinweise.push(ohne + ' Features ohne verwendbare Geometrie ausgelassen');
    return out;
  }
  function csvZeilen(text) {
    var kopf = text.split(/\r?\n/)[0], trenner = [';', '\t', ','].sort(function (a, b) { return kopf.split(b).length - kopf.split(a).length; })[0];
    var zeilen = [], feld = '', zeile = [], q = false;
    for (var i = 0; i < text.length; i++) {
      var c = text[i];
      if (q) { if (c === '"' && text[i + 1] === '"') { feld += '"'; i++; } else if (c === '"') q = false; else feld += c; }
      else if (c === '"') q = true;
      else if (c === trenner) { zeile.push(feld); feld = ''; }
      else if (c === '\n' || c === '\r') { if (c === '\r' && text[i + 1] === '\n') i++; zeile.push(feld); zeilen.push(zeile); zeile = []; feld = ''; }
      else feld += c;
    }
    if (feld || zeile.length) { zeile.push(feld); zeilen.push(zeile); }
    zeilen = zeilen.filter(function (z) { return z.some(function (x) { return x.trim(); }); });
    var h = (zeilen.shift() || []).map(function (x) { return x.trim(); });
    return zeilen.map(function (z) { var o = {}; h.forEach(function (k, j) { o[k] = (z[j] || '').trim(); }); return o; });
  }
  function importieren(text, dateiname) {
    var hinweise = [], objekte = [], t = String(text || '').trim();
    if (!t) return { fehler: ['Die Datei ist leer'] };
    if (/^[{[]/.test(t)) {
      var j = jsonAusText(t); if (j.fehler) return { fehler: [j.fehler] };
      var w = j.wert;
      if (w && w.type === 'FeatureCollection') objekte = geojsonZuObjekte(w, hinweise);
      else if (w && w.type === 'Feature') objekte = geojsonZuObjekte({ features: [w] }, hinweise);
      else if (w && w.format === 'chronoglobe-beitrag/1' && w.ebene) objekte = w.ebene.objekte || [];
      else if (w && (w.format === 'chronoglobe-ebene/1' || Array.isArray(w.objekte))) objekte = w.objekte || [];
      else if (Array.isArray(w)) objekte = w.map(function (x) { return x && (x.koordinaten || x.typ) ? x : ausEintrag(x || {}); });
      else return { fehler: ['Unbekanntes JSON: erwartet GeoJSON, eine Ebene oder eine Liste von Einträgen'] };
    } else objekte = csvZeilen(t).map(function (z) { return ausEintrag(z); });
    var vorher = objekte.length;
    objekte = objekte.map(function (o) { return objektSaeubern(o, hinweise); }).filter(function (o) {
      return o && (o.typ === 'punkt' ? !!o.koordinaten : o.koordinaten && o.koordinaten.length >= (o.typ === 'flaeche' ? 3 : 2));
    });
    if (objekte.length < vorher) hinweise.push((vorher - objekte.length) + ' Einträge ohne Koordinaten ausgelassen');
    objekte.forEach(function (o, i) { if (!o.name) o.name = 'Eintrag ' + (i + 1); });
    if (vertauschtVerdacht(objekte)) { tauschen(objekte); hinweise.push('Länge und Breite waren vertauscht und wurden getauscht'); }
    var ohneJahr = objekte.filter(function (o) { return o.von == null; }).length;
    if (ohneJahr) hinweise.push(ohneJahr + ' Objekte ohne Jahr – bitte „von“ ergänzen');
    eindeutigeIds(objekte, hinweise);
    if (!objekte.length) return { fehler: ['Keine Einträge mit Koordinaten gefunden' + (dateiname ? ' in ' + dateiname : '') + '. CSV braucht Spalten wie name, lat, lng (oder breite, laenge).'] };
    return { objekte: objekte, hinweise: hinweise };
  }

  var KI = { prompt: prompt, antwortLesen: antwortLesen, importieren: importieren, tauschen: tauschen, zahl: zahl, BEISPIEL: BEISPIEL };
  if (typeof module !== 'undefined' && module.exports) module.exports = KI; else wurzel.KI = KI;
})(typeof self !== 'undefined' ? self : this);
