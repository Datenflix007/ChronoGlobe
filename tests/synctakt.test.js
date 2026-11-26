/* Tests für den Sendetakt der Live-Session (js/synctakt.js).
   Aufruf:  node tests/synctakt.test.js   (keine Abhängigkeiten) */
'use strict';
var assert = require('assert');
var T = require('../js/synctakt.js');
var ok = 0, fehler = 0;
function test(name, fn) {
  try { fn(); ok++; console.log('  ok   ' + name); }
  catch (e) { fehler++; console.log('  FEHL ' + name + '\n       ' + e.message); }
}
var FREE = 100;   // Free-Plan: Realtime-Nachrichten/s, gezählt je Empfänger

console.log('Live-Session – Sendetakt');

test('1. kleine Gruppe: voller Takt (SYNC_RATE = 3)', function () {
  assert.strictEqual(T.rate(3, 5), 3);
  assert.strictEqual(T.rate(3, 0), 3);
});

test('2. Klasse mit 28 Tablets: unter dem Budget und unter dem Free-Plan', function () {
  var r = T.rate(3, 28);
  assert.ok(r < 3, 'Takt muss sinken: ' + r);
  assert.ok(T.last(r, 28) <= T.BUDGET + 1e-9, 'Last ' + T.last(r, 28));
  assert.ok(T.last(T.kameraRate(r), 28) <= T.BUDGET / 2 + 1e-9, 'Kamera halb so oft');
});

test('3. Reserve bleibt für Beitritte: Zustand + ein Beitritt (alle erhalten die Anwesenheit) < 100/s', function () {
  [10, 20, 28, 35, 45, 55].forEach(function (n) {
    var r = T.rate(3, n), beitritt = n + T.EXTRA;
    assert.ok(T.last(r, n) + beitritt < FREE, n + ' Geräte: ' + (T.last(r, n) + beitritt));
  });
});

test('3b. über 60 Geräte: Free-Plan reicht nicht mehr sicher (dokumentierte Grenze)', function () {
  var n = 80, r = T.rate(3, n);
  assert.strictEqual(r, T.MIN);
  assert.ok(T.last(r, n) + n + T.EXTRA >= FREE);
});

test('4. Takt fällt mit der Geräteanzahl, aber nie unter das Minimum', function () {
  var vorher = Infinity;
  for (var n = 0; n <= 200; n += 10) { var r = T.rate(3, n); assert.ok(r <= vorher); vorher = r; }
  assert.strictEqual(T.rate(3, 500), T.MIN);
});

test('5. SYNC_RATE bleibt Obergrenze (Pro-Plan: höherer Wert)', function () {
  assert.strictEqual(T.rate(1, 2), 1);
  assert.ok(T.rate(10, 2) <= 10);
});

test('6. nur Kamera bewegt: Art „kamera“; bei „Globus selbst bedienen“: „ruhe“', function () {
  var a = { v: 1, jahr: 117, kamera: { lat: 1, lng: 2, alt: 2 }, reiche: { rom: true } };
  var b = { v: 1, jahr: 117, kamera: { lat: 5, lng: 2, alt: 2 }, reiche: { rom: true } };
  var ja = JSON.stringify(a), ka = T.ohneKamera(a);
  assert.strictEqual(T.ohneKamera(a), T.ohneKamera(b));
  assert.strictEqual(T.art(JSON.stringify(b), T.ohneKamera(b), ja, ka, false), 'kamera');
  assert.strictEqual(T.art(JSON.stringify(b), T.ohneKamera(b), ja, ka, true), 'ruhe');
  assert.strictEqual(T.art(ja, ka, ja, ka, false), 'nichts');
});

test('7. Jahr, Ebenen oder Fenster geändert: Art „zustand“, auch bei „Globus selbst bedienen“', function () {
  var a = { v: 1, jahr: 117, kamera: { lat: 1 }, fenster: { rolle: null } };
  var ja = JSON.stringify(a), ka = T.ohneKamera(a);
  [{ jahr: 150 }, { fenster: { rolle: 'han' } }, { handel: { on: true } }].forEach(function (x) {
    var b = Object.assign({}, a, x);
    assert.strictEqual(T.art(JSON.stringify(b), T.ohneKamera(b), ja, ka, true), 'zustand', JSON.stringify(x));
  });
});

test('8. Abstand: Kamera doppelt so lang wie Zustand', function () {
  assert.strictEqual(T.abstand('zustand', 3, 0), 333);
  assert.strictEqual(T.abstand('kamera', 3, 0), 667);
  assert.ok(T.abstand('zustand', 3, 28) > 333);
});

test('9. Schüler:innen: Gleitdauer folgt dem gemessenen Takt, Pausen zählen nicht', function () {
  var t = 333;
  for (var i = 0; i < 10; i++) t = T.glaetten(t, 1000);
  assert.ok(Math.abs(t - 1000) < 20, 'geglättet: ' + t);
  assert.strictEqual(T.glaetten(t, 60000), t);
  assert.strictEqual(T.glaetten(t, 20), t);
  assert.strictEqual(T.gleitdauer(1000), 1150);
  assert.strictEqual(T.gleitdauer(50), 300);
  assert.strictEqual(T.gleitdauer(99999), 2500);
});

console.log('\n%d ok, %d Fehler', ok, fehler);
process.exit(fehler ? 1 : 0);
