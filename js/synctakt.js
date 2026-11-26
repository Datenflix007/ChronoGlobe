/* ChronoGlobe · Sendetakt der Live-Session (Lehreransicht → Schülergeräte). Reine Rechenfunktionen ohne DOM:
   im Browser als window.SyncTakt, in Node als Modul (tests/synctakt.test.js). Hintergrund: docs/ARCHITEKTUR.md,
   Abschnitt „Mengen“.

   Supabase zählt jede Broadcast-Nachricht einmal beim Senden und einmal je empfangendem Gerät. Der Free-Plan erlaubt
   100 Nachrichten/s; darüber werden Verbindungen getrennt. Deshalb:
   - Der Takt richtet sich nach der Zahl der Geräte: höchstens BUDGET Nachrichten/s für laufende Updates. Der Rest
     bleibt Reserve für Beitritte (Anwesenheit), Rechte, „Fokus für alle“ und „Alle zurück“.
   - Reine Kamerabewegungen gehen mit halbem Takt raus; Zustandswechsel (Jahr, Ebenen, Reiche, Fenster) mit vollem.
   - Steht „Globus drehen/zoomen“ auf „selbst bedienen“, werden reine Kamerabewegungen gar nicht gesendet. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.SyncTakt = factory();
})(this, function () {
  'use strict';

  var GRENZE = 100;         // Realtime-Nachrichten/s (Free-Plan 100, Pro 500; REALTIME_GRENZE in js/config.js)
  var BUDGET = 60;          // höchstens so viele Nachrichten/s für laufende Updates
  var PUFFER = 10;          // zusätzliche Reserve (Rechte, Fokus, Rundungen)
  var EXTRA = 2;            // Empfänger ohne Anwesenheitsmeldung: Lehreransicht selbst und ein mögliches zweites Lehrergerät
  var MIN = 0.5;            // Updates/s, auch bei sehr vielen Geräten
  var GLEIT_MIN = 300, GLEIT_MAX = 2500;   // Gleitdauer der Kamera bei Schüler:innen (ms)

  /* Nachrichten je Update: 1 (Senden) + Empfänger. anzahl = Geräte mit Anwesenheitsmeldung (Schüler:innen). */
  function proUpdate(anzahl) { return 1 + Math.max(0, anzahl | 0) + EXTRA; }

  /* Budget für laufende Updates: Ein Beitritt erreicht alle Geräte (Anwesenheit). Diese Reserve muss neben den
     laufenden Updates immer unter GRENZE bleiben. Ab etwa 60 Geräten reicht der Free-Plan dafür nicht mehr. */
  function budget(anzahl) { return Math.min(BUDGET * GRENZE / 100, GRENZE - proUpdate(anzahl) - PUFFER); }
  /* Grenze des Supabase-Plans setzen (Nachrichten/s); ungültige Werte werden ignoriert */
  function grenzeSetzen(n) { n = +n; if (n >= 50 && n <= 100000) GRENZE = n; return GRENZE; }

  /* Updates/s für Zustandswechsel. max = SYNC_RATE aus js/config.js (Obergrenze). */
  function rate(max, anzahl, b) {
    var r = (b || budget(anzahl)) / proUpdate(anzahl);
    return Math.max(MIN, Math.min(max, r));
  }

  /* Updates/s für reine Kamerabewegungen */
  function kameraRate(r) { return Math.max(MIN, r / 2); }

  /* Nachrichten/s bei Dauerbetrieb mit diesem Takt (für Anzeige und Tests) */
  function last(r, anzahl) { return r * proUpdate(anzahl); }

  /* Zustand ohne Kamera als Vergleichsschlüssel: gleicher Schlüssel = nur die Kamera hat sich bewegt */
  function ohneKamera(st) {
    var k = {}, x;
    for (x in st) if (Object.prototype.hasOwnProperty.call(st, x) && x !== 'kamera' && x !== 'drehen') k[x] = st[x];
    return JSON.stringify(k);
  }

  /* Was soll mit einem neuen Lehrerzustand geschehen?
     → 'nichts' (unverändert), 'ruhe' (nur Kamera, Globus frei), 'kamera' oder 'zustand' */
  function art(json, schluessel, gesendetJson, gesendetSchluessel, globusSelbst) {
    if (json === gesendetJson) return 'nichts';
    if (schluessel !== gesendetSchluessel) return 'zustand';
    return globusSelbst ? 'ruhe' : 'kamera';
  }

  /* Abstand (ms) bis zum nächsten erlaubten Senden */
  function abstand(artWert, max, anzahl) {
    var r = rate(max, anzahl);
    return Math.round(1000 / (artWert === 'kamera' ? kameraRate(r) : r));
  }

  /* Schüler:innen: gemessenen Abstand zwischen zwei Updates glätten. Lange Pausen (Ruhe) zählen nicht. */
  function glaetten(alt, gemessen) {
    if (!(gemessen > 100) || gemessen > 4000) return alt;
    return alt ? Math.round(alt * 0.6 + gemessen * 0.4) : Math.round(gemessen);
  }
  /* Gleitdauer der Kamera: etwas länger als der Takt, damit die Bewegung nicht stockt */
  function gleitdauer(takt) { return Math.max(GLEIT_MIN, Math.min(GLEIT_MAX, Math.round(takt * 1.15))); }

  return { grenze: function () { return GRENZE; }, grenzeSetzen: grenzeSetzen, BUDGET: BUDGET, budget: budget, EXTRA: EXTRA, MIN: MIN, proUpdate: proUpdate, rate: rate, kameraRate: kameraRate, last: last,
           ohneKamera: ohneKamera, art: art, abstand: abstand, glaetten: glaetten, gleitdauer: gleitdauer };
});
