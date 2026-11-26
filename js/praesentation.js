/* ChronoGlobe · Präsentationsfenster für einen zweiten Bildschirm (Fernseher, Smartboard über die Bildschirmerweiterung).

   Steuerfenster (freier Modus, Tafelbild oder Lehreransicht einer Session): Knopf „Präsentation“ öffnet
     app.html?tafelbild=<id>|modus=frei&praesentation=<kanal>. Danach sendet es seinen Zustand über einen
     BroadcastChannel „cg.praes.<kanal>“ an das Präsentationsfenster (nur im selben Browser, nichts verlässt das Gerät).
   Präsentationsfenster: ohne Menü und ohne Lehrerhinweise, große Schrift, Vollbild-Knopf, Leuchtstift für das
     Smartboard. Es folgt dem Steuerfenster und meldet nur die Zeichnung des Leuchtstifts zurück. Das Steuerfenster
     übernimmt sie wie eine eigene Änderung; in einer Session erreicht sie so wie gewohnt die Klasse.
   Das Präsentationsfenster verbindet sich nie mit Supabase und zählt nicht als Gerät der Session.
   Ablauf und Gründe: docs/ARCHITEKTUR.md, Abschnitt „Präsentationsfenster“. */
(function () {
  'use strict';
  var q = new URLSearchParams(location.search);
  var KANAL_PRAES = q.get('praesentation');
  var P = window.CGPraesentation = { aktiv: !!KANAL_PRAES, kanal: KANAL_PRAES, verbunden: false };
  if (P.aktiv) document.documentElement.classList.add('cg-praes');
  if (typeof BroadcastChannel === 'undefined') return;

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function zufall() { var a = new Uint8Array(8); crypto.getRandomValues(a); return Array.prototype.map.call(a, function (x) { return ('0' + x.toString(16)).slice(-2); }).join(''); }
  function gleich(a, b) { return JSON.stringify(a == null ? null : a) === JSON.stringify(b == null ? null : b); }

  document.addEventListener('chronoglobe:bereit', function () {
    if (P.aktiv) praesentation(); else steuerung();
  });

  /* ---------- Steuerfenster ---------- */
  function steuerung() {
    if (document.documentElement.classList.contains('cg-schueler')) return;   // Schülergeräte: kein Präsentationsfenster
    var CGL = window.ChronoGlobe, box = document.querySelector('.top-btns'); if (!box || !CGL) return;
    // gleicher Kanal nach einem Neuladen dieses Tabs: ein offenes Präsentationsfenster findet wieder Anschluss
    var kanal = null; try { kanal = sessionStorage.getItem('cg.praesKanal'); } catch (e) {}
    if (!kanal) { kanal = zufall(); try { sessionStorage.setItem('cg.praesKanal', kanal); } catch (e) {} }
    var bc = new BroadcastChannel('cg.praes.' + kanal), letzt = '', zuletztDa = 0, timer = null;
    var b = el('button', 'ghost', 'Präsentation'); b.id = 'btnPraes'; b.type = 'button';
    b.title = 'Zweites Fenster ohne Menü öffnen, z. B. für den Fernseher oder das Smartboard (Bildschirm erweitern, Fenster hinüberziehen)';
    box.insertBefore(b, box.firstChild);
    function zustand() {
      var st = CGL.getState();
      if (st.fenster && st.fenster.modal === 'lehrer') st.fenster.modal = null;   // Lehrerhinweise nie im Präsentationsfenster
      st.kamera.ref = CGL.homeAlt();
      return st;
    }
    function senden(alles) {
      var st = zustand(), j = JSON.stringify(st);
      if (!alles && j === letzt) return;
      letzt = j; bc.postMessage({ ev: 'zustand', st: st, alles: !!alles });
    }
    function verbunden() { return Date.now() - zuletztDa < 5000; }
    function anzeigen() { var v = verbunden(); P.verbunden = v; b.classList.toggle('on', v); b.setAttribute('aria-pressed', String(v)); }
    bc.onmessage = function (e) {
      var m = e.data || {};
      if (m.ev === 'hallo' || m.ev === 'da') {
        var neu = !verbunden(); zuletztDa = Date.now(); anzeigen();
        if (m.ev === 'hallo' || neu) senden(true);
      } else if (m.ev === 'zeichnung' && Array.isArray(m.z)) {
        // Leuchtstift am Smartboard: wie eine eigene Änderung übernehmen (Session: geht dann an die Klasse)
        if (!gleich(m.z, CGL.getState().zeichnung)) CGL.setState({ zeichnung: m.z });
      } else if (m.ev === 'tschuess') { zuletztDa = 0; anzeigen(); }
    };
    CGL.abonnieren(function () { if (verbunden()) senden(false); });
    // Kamerabewegungen melden sich nicht von selbst: lokal und billig, deshalb zehnmal je Sekunde vergleichen
    timer = setInterval(function () { if (verbunden()) senden(false); anzeigen(); }, 100);
    setInterval(function () { bc.postMessage({ ev: 'da' }); }, 1500);
    b.addEventListener('click', function () {
      var tb = window.CG && CG.tafelbild && CG.tafelbild.id;
      var url = 'app.html?' + (tb ? 'tafelbild=' + encodeURIComponent(tb) : 'modus=frei') + '&praesentation=' + kanal;
      var w = window.open(url, 'chronoglobe-praesentation-' + kanal, 'popup,width=1280,height=760');
      if (!w) { window.alert('Das Präsentationsfenster wurde vom Browser blockiert. Bitte Pop-ups für diese Seite erlauben.'); return; }
      try { w.focus(); } catch (e) {}
    });
    window.addEventListener('pagehide', function () { bc.postMessage({ ev: 'weg' }); });
    P.steuerung = { kanal: kanal, senden: senden };
  }

  /* ---------- Präsentationsfenster ---------- */
  function praesentation() {
    var CGL = window.ChronoGlobe, bc = new BroadcastChannel('cg.praes.' + KANAL_PRAES);
    var zuletzt = 0, eigeneZeichnung = 0, zeichnet = false, wendet = 0;
    document.title = 'Präsentation · ' + document.title;
    // keine eigene Bedienung außer dem Leuchtstift: alles kommt vom Steuerfenster
    CGL.setzeRechte(function () { return false; });
    CGL.globe.controls().enabled = false; CGL.globe.controls().autoRotate = false;
    if (CGL.stift) CGL.stift();
    // Kopfzeile: Vollbild und Hinweis auf die Verbindung
    var box = document.querySelector('.top-btns');
    var vb = el('button', 'ghost praes-vollbild', '⛶ Vollbild'); vb.type = 'button'; vb.id = 'btnVollbild';
    vb.title = 'Vollbild ein/aus (F11)';
    vb.addEventListener('click', function () {
      var d = document;
      if (d.fullscreenElement) { if (d.exitFullscreen) d.exitFullscreen(); }
      else if (d.documentElement.requestFullscreen) d.documentElement.requestFullscreen().catch(function () {});
    });
    document.addEventListener('fullscreenchange', function () { vb.textContent = document.fullscreenElement ? '⛶ Vollbild beenden' : '⛶ Vollbild'; });
    if (box) box.appendChild(vb);
    var hinweis = el('div', 'praes-hinweis', 'Warte auf das Steuerfenster …'); hinweis.setAttribute('role', 'status'); document.body.appendChild(hinweis);
    function verbindung() { var v = Date.now() - zuletzt < 5000; P.verbunden = v; hinweis.hidden = v; }
    // Zeichnen am Smartboard erkennen: während eines Strichs keine fremde Zeichnung übernehmen (würde ihn abbrechen)
    document.addEventListener('pointerdown', function (e) { if (e.target.closest && e.target.closest('.stift-flaeche')) zeichnet = true; }, true);
    document.addEventListener('pointerup', function () { if (zeichnet) { zeichnet = false; eigeneZeichnung = Date.now(); } }, true);
    document.addEventListener('pointercancel', function () { zeichnet = false; }, true);
    var gemeldet = '';
    CGL.abonnieren(function (quelle) {
      if (wendet || quelle !== 'lokal') return;
      var z = CGL.getState().zeichnung, j = JSON.stringify(z);
      if (j === gemeldet) return;
      gemeldet = j; eigeneZeichnung = Date.now();
      bc.postMessage({ ev: 'zeichnung', z: z });
    });
    function anwenden(st, alles) {
      if (!st || !st.v) return;
      var t = Object.assign({}, st), k = st.kamera || {}, f = k.ref ? CGL.homeAlt() / k.ref : 1;
      delete t.tafelbild; delete t.v;
      if (t.fenster && t.fenster.modal === 'lehrer') t.fenster.modal = null;
      t.kamera = { lat: k.lat, lng: k.lng, alt: Math.max(0.15, Math.min(6, (k.alt || CGL.homeAlt()) * f)) }; t.drehen = false;
      if (!alles && (zeichnet || Date.now() - eigeneZeichnung < 800)) delete t.zeichnung;
      wendet++;
      try { CGL.applyState(t, { quelle: 'lehrer', dauer: alles ? 0 : 160 }); } finally { wendet--; }
      if ('zeichnung' in t) gemeldet = JSON.stringify(CGL.getState().zeichnung);
      CGL.globe.controls().enabled = false;
    }
    bc.onmessage = function (e) {
      var m = e.data || {};
      if (m.ev === 'zustand') { zuletzt = Date.now(); verbindung(); anwenden(m.st, m.alles); }
      else if (m.ev === 'da') { var neu = Date.now() - zuletzt > 5000; zuletzt = Date.now(); verbindung(); if (neu) bc.postMessage({ ev: 'hallo' }); }
      else if (m.ev === 'weg') { zuletzt = 0; verbindung(); }
    };
    bc.postMessage({ ev: 'hallo' });
    setInterval(function () { bc.postMessage({ ev: 'da' }); verbindung(); }, 1500);
    window.addEventListener('pagehide', function () { bc.postMessage({ ev: 'tschuess' }); });
  }
})();
