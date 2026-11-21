/* Tests für die Handels- und Verkehrsnetze (js/netze.js, data/netze/*.json) mit den echten Daten.
   Aufruf:  node tests/netze.test.js   (keine Abhängigkeiten) */
'use strict';
var assert = require('assert'), fs = require('fs'), path = require('path');
var N = require('../js/netze.js');
var DIR = path.join(__dirname, '..', 'data', 'netze');
var lies = function (f) { return JSON.parse(fs.readFileSync(path.join(DIR, f), 'utf8')); };
var IX = lies('index.json');
var TESTJAHRE = [-300, 100, 430, 700, 850, 1050, 1250, 1350, 1440];
var ok = 0, fehler = 0;
function test(name, fn) {
  try { fn(); ok++; console.log('  ok   ' + name); }
  catch (e) { fehler++; console.log('  FEHL ' + name + '\n       ' + e.message); }
}
var verf = IX.netze.filter(function (n) { return n.status === 'verfuegbar'; });
var D = {};
verf.forEach(function (n) { D[n.id] = N.vorbereiten(lies(path.basename(n.datei))); });
function linien(id, y) { return N.linienImJahr(D[id], y); }

console.log('Handels- und Verkehrsnetze');

test('1. Register: Status gültig, Gruppen bekannt, Gründe bei nicht übernommenen Quellen', function () {
  var gruppen = IX.gruppen.map(function (g) { return g.id; }), ids = {};
  IX.netze.forEach(function (n) {
    assert.ok(!ids[n.id], 'doppelte id ' + n.id); ids[n.id] = 1;
    assert.ok(['verfuegbar', 'bestehend', 'nicht_verfuegbar', 'nicht_lizenziert', 'zurueckgestellt'].indexOf(n.status) >= 0, n.id + ': status');
    assert.ok(gruppen.indexOf(n.gruppe) >= 0, n.id + ': gruppe');
    assert.ok(n.quelle, n.id + ': quelle fehlt');
    if (/^(nicht_|zurueck)/.test(n.status)) assert.ok(n.grund, n.id + ': Grund fehlt');
    if (n.status === 'verfuegbar' || n.status === 'bestehend') assert.ok(n.lizenz, n.id + ': lizenz fehlt');
  });
});

test('2. Register: nur lokale Netzdateien (keine fremden Server zur Laufzeit)', function () {
  verf.forEach(function (n) {
    assert.ok(/^data\/netze\/[a-z_]+\.json$/.test(n.datei), n.id + ': ' + n.datei);
    assert.ok(fs.existsSync(path.join(__dirname, '..', n.datei)), n.datei + ' fehlt');
  });
});

test('3. jede Netzdatei entspricht dem Datenmodell (Netze.pruefen)', function () {
  verf.forEach(function (n) {
    var f = N.pruefen(lies(path.basename(n.datei)));
    assert.deepStrictEqual(f, [], n.id + ': ' + f.slice(0, 5).join('; '));
  });
});

test('4. Register und Datei stimmen überein (Gruppe, Zeitraum, Lizenz)', function () {
  verf.forEach(function (n) {
    var d = D[n.id];
    assert.strictEqual(d.id, n.id); assert.strictEqual(d.gruppe, n.gruppe);
    assert.strictEqual(d.datierung.von, n.von, n.id + ': von'); assert.strictEqual(d.datierung.bis, n.bis, n.id + ': bis');
    assert.strictEqual(d.datierung.typ, n.datierung, n.id + ': datierung');
    assert.strictEqual(d.quelle.lizenz, n.lizenz, n.id + ': lizenz');
  });
});

test('5. nur offene Lizenzen eingebunden', function () {
  verf.forEach(function (n) { assert.ok(/^(CC BY 4\.0|CC0|MIT|ODbL)/.test(D[n.id].quelle.lizenz), n.id + ': ' + D[n.id].quelle.lizenz); });
});

test('6. keine Epochenmischung: außerhalb der Datierung ist nichts sichtbar', function () {
  verf.forEach(function (n) {
    var d = D[n.id], nach = d.datierung.typ === 'reisedatum' ? N.NACHLEUCHTEN : 0;
    [d.datierung.von - 1, d.datierung.bis + nach + 1].forEach(function (y) {
      assert.strictEqual(linien(n.id, y).length, 0, n.id + ' im Jahr ' + y);
      assert.strictEqual(N.orteImJahr(d, y).length, 0, n.id + ' Orte im Jahr ' + y);
    });
  });
});

test('7. Testjahre: erwartete Netze sichtbar', function () {
  var erwartet = { '-300': ['petra_gaza'], '100': ['petra_gaza'], '430': [], '700': ['tang', 'viatariq'], '850': ['tang', 'viatariq', 'thurayya'],
    '1050': ['viatariq'], '1250': ['viatariq', 'mongolen'], '1350': ['viatariq', 'mongolen'], '1440': ['viatariq'] };
  TESTJAHRE.forEach(function (y) {
    var da = verf.map(function (n) { return n.id; }).filter(function (id) { return linien(id, y).length > 0; }).sort();
    assert.deepStrictEqual(da, erwartet[y].slice().sort(), 'Jahr ' + y);
  });
});

test('8. Tang: Strecken jahrgenau (z. B. Uigurenstraße 751–790 und 791–840 getrennt)', function () {
  var ui = D.tang.linien.filter(function (l) { return l.zh === '回鹘道'; });
  assert.strictEqual(ui.length, 2);
  assert.ok(linien('tang', 790).some(function (x) { return x.linie === ui[0]; }) && !linien('tang', 790).some(function (x) { return x.linie === ui[1]; }));
  assert.ok(linien('tang', 800).some(function (x) { return x.linie === ui[1]; }) && !linien('tang', 800).some(function (x) { return x.linie === ui[0]; }));
  assert.ok(linien('tang', 700).length > linien('tang', 850).length, 'nach 790 weniger Strecken (Verlust des Westens)');
});

test('9. VIA-TARIQ: genau eine Periode je Jahr, Grenzjahr gehört zur jüngeren Periode', function () {
  [700, 950, 1050, 1250, 1350, 1440].forEach(function (y) {
    var per = {}; linien('viatariq', y).forEach(function (x) { per[x.linie.periode] = 1; });
    assert.strictEqual(Object.keys(per).length, 1, 'Jahr ' + y + ': ' + Object.keys(per));
  });
  assert.strictEqual(N.periode(D.viatariq, 950).id, 'middle_islamic');
  assert.strictEqual(N.periode(D.viatariq, 1250).id, 'early_mamluk');
  assert.strictEqual(N.periode(D.viatariq, 1517).id, 'late_mamluk');
});

test('10. VIA-TARIQ: Post- und Pilgerwege als solche gekennzeichnet, nicht als Handelsweg', function () {
  assert.strictEqual(D.viatariq.art, 'verkehrsnetz');
  var post = D.viatariq.linien.filter(function (l) { return l.post; }), hadsch = D.viatariq.linien.filter(function (l) { return l.hadsch; });
  assert.ok(post.length > 100 && hadsch.length > 20, post.length + ' / ' + hadsch.length);
  post.forEach(function (l) { assert.ok(/Barid/.test(l.itinerar)); });
});

test('11. Reiseberichte: eigene Gruppe, Art „reiseroute“, Etappen erscheinen erst nach Reisebeginn', function () {
  var d = D.mongolen;
  assert.strictEqual(d.gruppe, 'reise'); assert.strictEqual(d.art, 'reiseroute'); assert.ok(d.hinweis && /keine Handelsrouten/.test(d.hinweis));
  var polo = d.reisen.filter(function (r) { return r.reisender === 'Marco Polo'; })[0];
  assert.ok(polo);
  var vor = linien('mongolen', 1272).filter(function (x) { return x.linie.reise === polo.id; });
  assert.ok(vor.length && vor.every(function (x) { return x.linie.von <= 1272; }));
  assert.ok(vor.some(function (x) { return x.stil === 'aktiv'; }));
  var spaet = linien('mongolen', polo.bis + 1).filter(function (x) { return x.linie.reise === polo.id; });
  assert.ok(spaet.length && spaet.every(function (x) { return x.stil === 'blass'; }), 'nach Reiseende blass');
});

test('12. al-Ṯurayyā: Zeitraum des Datensatzes (800–1000), alle Strecken gleich datiert', function () {
  assert.ok(D.thurayya.linien.every(function (l) { return l.von === 800 && l.bis === 1000; }));
  assert.strictEqual(linien('thurayya', 850).length, D.thurayya.linien.length);
});

test('13. Schlüssel ändert sich nur mit dem sichtbaren Zustand', function () {
  assert.strictEqual(N.schluessel(D.thurayya, 850), N.schluessel(D.thurayya, 900));
  assert.notStrictEqual(N.schluessel(D.viatariq, 949), N.schluessel(D.viatariq, 950));
});

test('14. Zeittexte ohne Jahr 0 und mit Monaten', function () {
  assert.strictEqual(N.spanne(-300, 200), '300 v. Chr. bis 200 n. Chr.');
  assert.strictEqual(N.zeitText({ von: 1246, vonMonat: 10, bis: 1246, bisMonat: 12 }), 'Okt. 1246 bis Dez. 1246');
});

console.log('\n' + ok + ' ok, ' + fehler + ' fehlgeschlagen');
process.exit(fehler ? 1 : 0);
