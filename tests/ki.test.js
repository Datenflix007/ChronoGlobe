/* KI-Assistent und Import (js/ki.js): Prompt, Einlesen von KI-Antworten, GeoJSON/CSV-Import.
       node tests/ki.test.js */
'use strict';
const KI = require('../js/ki.js'), Themen = require('../js/themen.js');
let ok = 0, fehler = 0;
function check(name, bed, info) { if (bed) { ok++; console.log('  ok   ' + name); } else { fehler++; console.log('  FEHL ' + name + (info !== undefined ? '  ' + JSON.stringify(info).slice(0, 300) : '')); } }

console.log('KI-Assistent und Import');

// 1. Prompt
const p = KI.prompt({ modus: 'neue-ebene', datensatz: 'name;lat;lng\nUr;30.96;46.10', dateiname: 'orte.csv', thema: 'Zikkurate' });
check('1. Prompt enthält Datensatz, Thema und Format', p.includes('Ur;30.96;46.10') && p.includes('Zikkurate') && p.includes('chronoglobe-beitrag/1'));
check('1. Prompt verlangt _editor-Anweisungen', p.includes('"_editor"') && p.includes('"pruefen"') && p.includes('"karte"'));
check('1. Prompt nennt Reihenfolge Länge/Breite und v. Chr. negativ', p.includes('[Länge, Breite]') && p.includes('-2560'));
check('1. Beispiel im Prompt ist selbst gültig', Themen.beitragPruefen(Object.assign({}, KI.BEISPIEL, { _editor: undefined })).length === 0, Themen.beitragPruefen(KI.BEISPIEL));
const pa = KI.prompt({ modus: 'aenderung', datensatz: 'Dakien 106' });
check('1. Änderungs-Prompt nennt die Bereiche', pa.includes('"reich-gebiet"') && pa.includes('"art": "aenderung"'));

// 2. Antwort lesen
const antwort = 'Hier ist das Ergebnis:\n```json\n' + JSON.stringify(KI.BEISPIEL, null, 2) + '\n```\nViel Erfolg!';
let r = KI.antwortLesen(antwort);
check('2. Codeblock mit Text drumherum', r.beitrag && r.fehler.length === 0, r.fehler);
check('2. _editor ausgelesen und aus dem Beitrag entfernt', r.editor.jahr === -2560 && r.editor.pruefen.length === 1 && !('_editor' in r.beitrag));
r = KI.antwortLesen('{ "format": "chronoglobe-beitrag/1", "art": "neue-ebene", // Kommentar\n "titel": "Test Ebene", "belege": ["Quelle 2000, Titel"], "ebene": { "name": "Städte am Euphrat", "farbe": "#4f86c6", "beschreibung": "Frühe Städte in Sumer.", "quellen": ["Van De Mieroop 2016"], "objekte": [ { "name": "Ur", "typ": "punkt", "von": "um 3800 v. Chr.", "koordinaten": ["30.963", "46.103"] }, { "name": "Ur", "typ": "punkt", "von": -2100, "koordinaten": [30.963, 46.103] }, ], }, }');
check('2. kaputtes JSON repariert', r.beitrag && r.hinweise.some(h => /repariert/.test(h)), r.fehler);
const o = r.beitrag && r.beitrag.ebene.objekte;
check('2. Jahr aus Text („um 3800 v. Chr.“)', o && o[0].von === -3800, o && o[0]);
check('2. Koordinaten aus Text zu Zahlen', o && o[0].koordinaten[0] === 30.963 && o[0].koordinaten[1] === 46.103, o && o[0].koordinaten);
const sw = KI.antwortLesen(JSON.stringify({ format: 'chronoglobe-ebene/1', name: 'Australien', objekte: [{ name: 'Sydney', von: 1788, koordinaten: [-33.87, 151.21] }] }));
check('2. eindeutig vertauschte Koordinaten getauscht (Breite > 90)', sw.beitrag.ebene.objekte[0].koordinaten[0] === 151.21 && sw.hinweise.some(h => /vertauscht/.test(h)), sw.beitrag.ebene.objekte[0]);
check('2. ids ergänzt und eindeutig', o && o[0].id === 'ur' && o[1].id === 'ur-2', o && o.map(x => x.id));
check('2. Ebenen-id aus dem Namen', r.beitrag.ebene.id === 'staedte-am-euphrat');
check('2. Quellen aus Text werden Objekte', r.beitrag.ebene.quellen[0].zitat === 'Van De Mieroop 2016');
r = KI.antwortLesen(JSON.stringify({ type: 'FeatureCollection', features: [{ type: 'Feature', properties: { name: 'Babylon', start: -1894 }, geometry: { type: 'Point', coordinates: [44.42, 32.54] } }] }));
check('2. GeoJSON als Antwort wird Ebene', r.beitrag && r.beitrag.art === 'neue-ebene' && r.beitrag.ebene.objekte[0].von === -1894);
check('2. kein JSON → verständlicher Fehler', KI.antwortLesen('Tut mir leid, das kann ich nicht.').fehler.length === 1);

// 3. Import
let im = KI.importieren('Name;Breite;Länge;von;bis;Beschreibung\nUr;30,963;46,103;-3800;-500;"Stadt; Zikkurat"\nUruk;31.322;45.636;-4000;\nohne Lage;;;-100;', 'orte.csv');
check('3. CSV mit Semikolon, Komma-Dezimalen, Anführungszeichen', im.objekte && im.objekte.length === 2 && im.objekte[0].koordinaten[0] === 46.103 && im.objekte[0].beschreibung === 'Stadt; Zikkurat', im);
check('3. Zeile ohne Koordinaten ausgelassen und gemeldet', im.hinweise.some(h => /ohne Koordinaten/.test(h)));
check('3. leeres bis entfällt', im.objekte[1].bis === undefined && im.objekte[1].von === -4000);
im = KI.importieren(JSON.stringify({ type: 'FeatureCollection', features: [
  { type: 'Feature', properties: { title: 'Mauer', year: '200 BC' }, geometry: { type: 'LineString', coordinates: [[1, 2], [3, 4]] } },
  { type: 'Feature', properties: { name: 'Gebiet' }, geometry: { type: 'Polygon', coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]] } }] }));
check('3. GeoJSON: Linie und Fläche, Ring ohne Schlusspunkt', im.objekte.length === 2 && im.objekte[0].typ === 'linie' && im.objekte[0].von === -200 && im.objekte[1].koordinaten.length === 3, im.objekte);
check('3. fehlendes Jahr gemeldet', im.hinweise.some(h => /ohne Jahr/.test(h)));
check('3. Datei ohne Koordinaten → Fehler', !!KI.importieren('a,b\n1,2').fehler);

console.log('\n' + ok + ' bestanden, ' + fehler + ' fehlgeschlagen');
process.exit(fehler ? 1 : 0);
