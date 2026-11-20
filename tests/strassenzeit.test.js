/* Tests für das Zeitmodell der Römerstraßen (js/strassenzeit.js) mit den echten Daten.
   Aufruf:  node tests/strassenzeit.test.js   (keine Abhängigkeiten) */
'use strict';
var assert = require('assert'), fs = require('fs'), path = require('path');
var SZ = require('../js/strassenzeit.js');
var roh = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', 'roemerstrassen.json'), 'utf8'));
var D = SZ.vorbereiten(roh), L = D.linien;
var STD = { ehemals: false, animieren: true, unsicherheit: false };
var REF = { ehemals: true, animieren: true, unsicherheit: false };
var KONTROLL = [-300, -200, -100, 1, 100, 200, 300, 400, 500, 800, 1000, 1200, 1440];
var ok = 0, fehler = 0;
function test(name, fn) {
  try { fn(); ok++; console.log('  ok   ' + name); }
  catch (e) { fehler++; console.log('  FEHL ' + name + '\n       ' + e.message); }
}

console.log('Römerstraßen – Zeitmodell');

test('1. alle 819 Linien werden geladen, Geometrie und Sicherheit unverändert', function () {
  assert.strictEqual(roh.linien.length, 819);
  assert.strictEqual(L.length, 819);
  roh.linien.forEach(function (r, i) {
    assert.strictEqual(L[i].id, r.id); assert.strictEqual(L[i].s, r.s); assert.deepStrictEqual(L[i].p, r.p);
  });
  assert.ok(L.every(function (l) { return l.datierbar; }), 'alle Linien des Datensatzes sind datierbar');
});

test('2. vor der modellierten Entstehung unsichtbar', function () {
  L.forEach(function (l) {
    var vorher = SZ.historisch(SZ.astro(l.bmin) - 1);
    var z = SZ.zustand(l, vorher, REF);
    assert.strictEqual(z.phase, 'vor'); assert.strictEqual(z.stil, null);
  });
  assert.ok(SZ.zaehlen(L, -300, STD).sichtbar <= L.filter(function (l) { return SZ.astro(l.bmin) <= SZ.astro(-300); }).length);
});

test('3. Wachstumsnetz: Linie wird im Zeichenfenster vom Anschlusspunkt aus gezeichnet (Anteil 0 → 1)', function () {
  var mitNetz = L.filter(function (x) { return x.netz; });
  assert.ok(mitNetz.length > 780, 'fast alle Linien haben ein Zeichenfenster (' + mitNetz.length + ')');
  mitNetz.forEach(function (l) {
    assert.ok(l.netz.von >= SZ.astro(l.bmin) && l.netz.bis <= SZ.astro(l.bmax), l.id + ': Fenster im Ausbauzeitraum');
    assert.ok(l.netz.u >= 0 && l.netz.u <= 1);
  });
  var l = mitNetz.filter(function (x) { return x.netz.bis - x.netz.von > 20 && x.netz.von > SZ.astro(x.bmin); })[0];
  var v = SZ.zustand(l, SZ.historisch(l.netz.von - 1), STD), a = SZ.zustand(l, SZ.historisch(l.netz.von), STD),
      m = SZ.zustand(l, SZ.historisch(Math.round((l.netz.von + l.netz.bis) / 2)), STD), e = SZ.zustand(l, SZ.historisch(l.netz.bis), STD);
  assert.strictEqual(v.phase, 'ausbau'); assert.strictEqual(v.stil, null, 'vor dem Anschluss noch nicht gezeichnet');
  [a, m].forEach(function (z) { assert.strictEqual(z.stil, 'ausbau'); assert.ok(z.anteil > 0 && z.anteil < 1); });
  assert.ok(a.anteil < m.anteil && m.anteil <= e.anteil && e.anteil === 1, 'Anteil steigt bis 1');
  // jede Linie (außer der ersten) hängt an einer Linie, die zu ihrem Start schon begonnen hat (über Land; Inseln/Überfahrten ausgenommen)
  var byId = {}; L.forEach(function (x) { byId[x.id] = x; });
  var ohne = mitNetz.filter(function (x) { return !x.netz.anschluss; });
  assert.strictEqual(ohne.length, 1, 'genau ein Startpunkt (bei Rom)');
  mitNetz.forEach(function (x) {
    var p = x.netz.anschluss && byId[x.netz.anschluss];
    if (p && p.netz && !x.zeit.netz.ueber_see) assert.ok(p.netz.von <= x.netz.von, x.id + ' beginnt nicht vor ' + p.id);
  });
  // ohne Animation: ganz sichtbar ab beginn_modell
  assert.strictEqual(SZ.zustand(l, l.modell, { animieren: false }).stil, 'aktiv');
});

test('4. römische Nutzungsphase: voll sichtbar', function () {
  L.forEach(function (l) {
    var z = SZ.zustand(l, l.bmax, STD); assert.strictEqual(z.phase, 'roemisch'); assert.strictEqual(z.anteil, 1);
    z = SZ.zustand(l, l.ende, STD); assert.strictEqual(z.phase, 'roemisch');
  });
  assert.strictEqual(SZ.zaehlen(L, 200, STD).sichtbar, 819, 'um 200 alle sichtbar (teils noch im modellierten Ausbau bis 250)');
  assert.strictEqual(SZ.zaehlen(L, 300, STD).roemisch, 819, 'um 300 alle in voller römischer Nutzung');
});

test('5. nachrömisch: Hauptmodus unsichtbar, Referenzmodus „ehemals“', function () {
  L.forEach(function (l) {
    var j = SZ.historisch(SZ.astro(l.ende) + 1);
    assert.strictEqual(SZ.zustand(l, j, STD).stil, null);
    assert.strictEqual(SZ.zustand(l, j, REF).stil, 'ehemals');
    assert.strictEqual(SZ.zustand(l, j, REF).phase, 'nachroemisch');
  });
});

test('6. Jahre 800 und 1440: keine Linie aktiv; Referenzmodus zeigt nur ehemalige Trassen', function () {
  [800, 1440].forEach(function (j) {
    var c = SZ.zaehlen(L, j, STD);
    assert.strictEqual(c.sichtbar, 0, j + ': Hauptmodus');
    var r = SZ.zaehlen(L, j, REF);
    assert.strictEqual(r.nachroemisch, 819); assert.strictEqual(r.sichtbar, 819);
    L.forEach(function (l) { assert.strictEqual(SZ.zustand(l, j, REF).stil, 'ehemals'); });
  });
  // 500: nur Regionen mit längerer Nutzung (Osten) noch aktiv
  var c5 = SZ.zaehlen(L, 500, STD);
  assert.ok(c5.roemisch > 0 && c5.roemisch < 819, '500: teils noch in Nutzung (' + c5.roemisch + ')');
});

test('8. Zurückspulen und erneutes Vorwärtslaufen ergeben dieselben Zustände', function () {
  var hin = KONTROLL.map(function (j) { return SZ.schluessel(L, j, STD); });
  var rueck = KONTROLL.slice().reverse().map(function (j) { return SZ.schluessel(L, j, STD); }).reverse();
  var nochmal = KONTROLL.map(function (j) { return SZ.schluessel(L, j, STD); });
  assert.deepStrictEqual(rueck, hin); assert.deepStrictEqual(nochmal, hin);
});

test('8b. Kontrolljahre: Zahl sichtbarer Linien steigt bis ins 2. Jh. und fällt danach', function () {
  var n = KONTROLL.map(function (j) { return SZ.zaehlen(L, j, STD).sichtbar; });
  console.log('       sichtbar je Kontrolljahr: ' + KONTROLL.map(function (j, i) { return SZ.jahrText(j) + ' ' + n[i]; }).join(', '));
  assert.ok(n[0] < n[3] && n[3] < n[5], 'Anstieg');
  assert.ok(n[8] < n[6] && n[9] === 0, 'Rückgang nach dem Ende der Nutzung');
});

test('9. ungültige oder fehlende Datierungen werden robust behandelt', function () {
  var t = SZ.vorbereiten({ linien: [
    { id: 'a', s: 'S', p: [[10, 45], [11, 45]] },                                                     // keine zeit
    { id: 'b', s: 'X', p: [[10, 45], [11, 45]], zeit: { beginn_min: 'x', beginn_max: null } },          // ungültig
    { id: 'c', s: 'S', p: [[10, 45], [11, 45]], zeit: { beginn_min: 100, beginn_max: 50, roemische_nutzung_bis_modell: 400 } },   // vertauscht
    { id: 'd', s: 'S', p: [[10, 45], [11, 45]], zeit: { beginn_min: 0, beginn_max: 50 } },              // Jahr 0 ungültig
    { id: 'e', s: 'S', p: [[10, 45]], zeit: { beginn_min: 10, beginn_max: 50 } },                       // Geometrie ungültig
    { id: 'f', s: 'S', p: [[10, 45], [11, 45]], zeit: { beginn_min: 10, beginn_max: 50 } }              // Ende unbekannt
  ] });
  assert.strictEqual(t.linien.length, 5, 'Linie mit ungültiger Geometrie wird verworfen');
  assert.ok(t.fehler.length >= 5);
  var by = {}; t.linien.forEach(function (l) { by[l.id] = l; });
  assert.strictEqual(SZ.zustand(by.a, 200, STD).stil, null); assert.strictEqual(SZ.zustand(by.a, 200, { unsicherheit: true }).stil, 'undatiert');
  assert.strictEqual(by.b.s, 'H'); assert.strictEqual(by.b.datierbar, false);
  assert.strictEqual(by.c.bmin, 50); assert.strictEqual(by.c.bmax, 100);
  assert.strictEqual(by.d.datierbar, false);
  assert.strictEqual(SZ.zustand(by.f, 300, STD).phase, 'roemisch');
  assert.strictEqual(SZ.zustand(by.f, 800, STD).stil, null, 'unbekanntes Ende: nicht bis ins Mittelalter aktiv');
  assert.deepStrictEqual(SZ.vorbereiten(null).linien, []);
});

test('Jahr 0: historische und astronomische Zählung', function () {
  assert.strictEqual(SZ.astro(-1), 0); assert.strictEqual(SZ.astro(1), 1); assert.strictEqual(SZ.historisch(0), -1);
  assert.strictEqual(SZ.historisch(SZ.astro(-44)), -44);
  assert.strictEqual(SZ.jahrText(-1), '1 v. Chr.'); assert.strictEqual(SZ.jahrText(1), '1 n. Chr.');
  var l = { datierbar: true, bmin: -1, bmax: 1, modell: -1, ende: 400, endeUnbekannt: false };   // Ausbau 1 v. bis 1 n. Chr.: 1 Jahr
  assert.strictEqual(SZ.zustand(l, -1, STD).phase, 'ausbau'); assert.strictEqual(SZ.zustand(l, 1, STD).phase, 'roemisch');
});

test('Anreicherung: belegte Datierungen nie vor das Regionalmodell, Kennzeichnung vorhanden', function () {
  roh.linien.forEach(function (r) {
    var z = r.zeit, g = z.regional;
    assert.ok(g, 'regionale Ausgangswerte gespeichert');
    assert.ok(['itinere_belegt', 'itinere_teilweise', 'regionalmodell_nicht_einzelbelegt'].indexOf(z.datierung) >= 0, z.datierung);
    assert.ok(SZ.astro(z.beginn_min) <= SZ.astro(z.beginn_max));
    if (z.datierung !== 'regionalmodell_nicht_einzelbelegt') assert.ok(z.itinere && z.itinere.belege.length > 0);
  });
});

console.log('\n' + ok + ' bestanden, ' + fehler + ' fehlgeschlagen');
process.exit(fehler ? 1 : 0);
