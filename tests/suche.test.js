/* Tests für die Suche (js/suche.js) mit den echten Daten.
   Aufruf:  node tests/suche.test.js   (keine Abhängigkeiten) */
'use strict';
var assert = require('assert'), fs = require('fs'), path = require('path');
var S = require('../js/suche.js');
function J(f) { return JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', f), 'utf8')); }
var R = J('reiche.json'), F = J('fruehe_reiche.json'), H = J('handel.json'), G = J('geographie.json');
var ok = 0, fehler = 0;
function test(name, fn) {
  try { fn(); ok++; console.log('  ok   ' + name); }
  catch (e) { fehler++; console.log('  FEHL ' + name + '\n       ' + e.message); }
}
var meta = Object.assign({}, R.meta, F.meta);
var I = S.bauen({ meta: meta, ereignisse: R.ereignisse.concat(F.ereignisse), schlachten: R.schlachten.concat(F.schlachten),
  orte: R.orte.concat(F.orte), handelOrte: H.orte, geo: G });
function erster(q, opt) { var t = S.suchen(I, q, opt)[0]; return t ? t.e : null; }

console.log('Suche');

test('1. Faltung: Akzente, Apostrophe, Schreibvarianten', function () {
  [['Chang\'an', 'Changan'], ['Chang’an', 'changan'], ['Ktesiphon', 'Ctesiphon'], ['Kuschan', 'Kushan'],
   ['Seleukeia', 'Seleucia'], ['Cäsar', 'Caesar'], ['Pjöngjang', 'Pjoengjang'], ['Mérida', 'Merida']].forEach(function (p) {
    assert.strictEqual(S.falten(p[0]), S.falten(p[1]), p.join(' / '));
  });
});

test('2. Orte: Chang\'an, Changan, Ktesiphon, Ctesiphon', function () {
  ['Chang\'an', 'changan', 'CHANG AN'].forEach(function (q) { assert.strictEqual(erster(q).name, 'Chang\'an', q); });
  ['Ktesiphon', 'Ctesiphon', 'ktesifon'].forEach(function (q) { assert.strictEqual(erster(q).name, 'Ktesiphon', q); });
});

test('3. gleicher Ort in mehreren Reichen erscheint einmal mit allen Reichen', function () {
  var k = S.suchen(I, 'Ktesiphon').filter(function (t) { return t.e.name === 'Ktesiphon'; });
  assert.strictEqual(k.length, 1);
  assert.ok(k[0].e.reiche.indexOf('parth') >= 0 && k[0].e.reiche.indexOf('sasan') >= 0, k[0].e.reiche.join());
});

test('4. Reiche, auch mit Schreibvariante (Kushan, Parther)', function () {
  assert.strictEqual(erster('Kushan').id, 'kusch');
  assert.strictEqual(erster('Parther').id, 'parth');
  assert.strictEqual(erster('han-reich').id, 'han');
});

test('5. Geographie: antiker und heutiger Name', function () {
  assert.strictEqual(erster('Rhein').name, 'Rhenus');
  assert.strictEqual(erster('Rhenus').name, 'Rhenus');
  assert.strictEqual(erster('Mittelmeer').art, 'geo');
  var d = erster('Donau'); assert.strictEqual(d.art, 'geo'); assert.ok(d.lat && d.lng);
});

test('6. Schlachten und Ereignisse', function () {
  var c = erster('Carrhae'); assert.strictEqual(c.art, 'schlacht'); assert.strictEqual(c.jahr, -53);
  assert.ok(S.suchen(I, 'Carrhae').some(function (t) { return t.e.art === 'ereignis'; }));
  assert.strictEqual(erster('Varusschlacht').art, 'schlacht');
  assert.strictEqual(erster('Gelbe Turbane').name, 'Aufstand der Gelben Turbane', 'mehrere Wörter, gebeugt');
});

test('7. Tippfehler ab fünf Zeichen', function () {
  assert.strictEqual(erster('Luoyamg').name, 'Luoyang');
  assert.strictEqual(S.suchen(I, 'xq').length, 0);
});

test('8. Zeitraum des Tafelbilds: Treffer außerhalb stehen hinten und sind markiert', function () {
  var t = S.suchen(I, 'Ramses', { von: -300, bis: 480 });
  assert.ok(t.length && t.every(function (x) { return x.aussen; }), 'Ramses liegt vor 300 v. Chr.');
  var c = S.suchen(I, 'Carrhae', { von: -300, bis: 480 })[0]; assert.ok(!c.aussen);
  var a = S.suchen(I, 'Rom', { von: -300, bis: 480 }); var i = a.findIndex(function (x) { return x.aussen; });
  assert.ok(i < 0 || a.slice(i).every(function (x) { return x.aussen; }), 'ausgegraute Treffer am Ende');
});

test('9. Daten außerhalb des Tafelbilds (aussen) sind immer ausgegraut', function () {
  var X = S.bauen({ meta: { rom: R.meta.rom }, aussen: { meta: { ming: { name: 'Ming-Reich', von: 1368, bis: 1644, zentrum: [110, 32] } } } });
  var t = S.suchen(X, 'Ming');
  assert.strictEqual(t[0].e.name, 'Ming-Reich'); assert.ok(t[0].aussen);
});

test('10. Zieljahr: Ereignis/Schlacht setzt das Jahr, Ort nur außerhalb seiner Zeit', function () {
  assert.strictEqual(S.zieljahr({ jahr: -53 }, 117), -53);
  assert.strictEqual(S.zieljahr({ zeiten: [[-206, 220]] }, 117), null);
  assert.strictEqual(S.zieljahr({ zeiten: [[224, 651]] }, 117, -300, 480), 224);
  assert.strictEqual(S.zieljahr({ von: -247, bis: 224 }, 300, -300, 480), -247);
  assert.strictEqual(S.zieljahr({ von: -800, bis: 100 }, 300, -300, 480), -300, 'auf den Zeitraum begrenzt');
  assert.strictEqual(S.zieljahr({ art: 'geo' }, 117), null);
});

console.log('\n%d ok, %d Fehler', ok, fehler);
process.exit(fehler ? 1 : 0);
