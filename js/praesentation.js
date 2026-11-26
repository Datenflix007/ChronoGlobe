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
      letzt = j; bc.postMessage({ ev: 'zustand', st: st, alles: !!alles, t: Date.now() });   // t: Zeitstempel für die Kamera
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
    // Kamerabewegungen melden sich nicht von selbst: lokal und billig, deshalb zwanzigmal je Sekunde vergleichen
    timer = setInterval(function () { if (verbunden()) senden(false); anzeigen(); }, 50);
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
    /* Kamera: Die Stände des Steuerfensters kommen bis zu zwanzigmal je Sekunde, aber unregelmäßig. Ein eigener
       Kameraflug je Stand ließe den Globus ruckeln (jeder Flug bricht den vorigen ab). Deshalb werden die Stände mit
       Zeitstempel gepuffert und mit kleiner Verzögerung Bild für Bild gleichmäßig interpoliert. Die Verzögerung passt
       sich an: größter Abstand der letzten Stände + größte Übertragungszeit + Reserve, damit der Puffer nie leer läuft
       (sonst stünde die Kamera kurz still und spränge dann). Auf einem üblichen Laptop etwa 100 ms. */
    var VERZUG = 150, ZIEL_VERZUG = 150, letztesBild = 0, puffer = [], raf = 0, gezeigt = '', abstaende = [], laufzeiten = [];
    function verzugAnpassen(abstand, laufzeit) {
      if (abstand > 0 && abstand < 400) { abstaende.push(abstand); if (abstaende.length > 12) abstaende.shift(); }
      laufzeiten.push(Math.max(0, laufzeit)); if (laufzeiten.length > 12) laufzeiten.shift();
      var a = Math.max.apply(null, abstaende.concat([50])), l = Math.max.apply(null, laufzeiten);
      ZIEL_VERZUG = Math.max(100, Math.min(400, a + l + 30));
    }
    function kameraRein(k, t, sofort) {
      var p = { t: t, lat: k.lat, lng: k.lng, alt: k.alt }, v = puffer[puffer.length - 1];
      verzugAnpassen(v ? t - v.t : 0, Date.now() - t);
      if (sofort || !v) { puffer = [p]; setzeKamera(p); return; }
      while (p.lng - v.lng > 180) p.lng -= 360;   // kürzester Weg über die Datumsgrenze
      while (p.lng - v.lng < -180) p.lng += 360;
      if (p.t <= v.t) p.t = v.t + 1;
      // nach einer Pause: Bewegung erst kurz vor dem neuen Stand beginnen, nicht langsam über die ganze Pause
      if (p.t - v.t > 400) puffer.push({ t: p.t - 100, lat: v.lat, lng: v.lng, alt: v.alt });
      puffer.push(p);
      if (puffer.length > 40) puffer.splice(0, puffer.length - 40);
      if (!raf) raf = requestAnimationFrame(schritt);
    }
    function setzeKamera(p) {
      var lng = ((p.lng + 540) % 360) - 180, key = p.lat.toFixed(4) + ',' + lng.toFixed(4) + ',' + p.alt.toFixed(4);
      if (key === gezeigt) return;
      gezeigt = key; CGL.globe.pointOfView({ lat: p.lat, lng: lng, altitude: p.alt }, 0);
    }
    function schritt() {
      raf = 0;
      // Verzögerung nur langsam nachführen (höchstens 15 % der Bildzeit je Bild): die Anzeigezeit läuft nie rückwärts
      var jetzt = Date.now(), dt = letztesBild ? Math.min(100, jetzt - letztesBild) : 16; letztesBild = jetzt;
      VERZUG += Math.max(-0.15 * dt, Math.min(0.15 * dt, ZIEL_VERZUG - VERZUG));
      var rt = jetzt - VERZUG, n = puffer.length; if (!n) return;
      var p = puffer[n - 1];
      if (rt < puffer[0].t) p = puffer[0];
      else for (var i = 0; i < n - 1; i++) {
        var a = puffer[i], b = puffer[i + 1];
        if (rt >= a.t && rt <= b.t) { var f = (rt - a.t) / (b.t - a.t); p = { lat: a.lat + (b.lat - a.lat) * f, lng: a.lng + (b.lng - a.lng) * f, alt: a.alt + (b.alt - a.alt) * f }; break; }
      }
      setzeKamera(p);
      if (rt < puffer[n - 1].t + 50) raf = requestAnimationFrame(schritt);   // weiter, bis der letzte Stand erreicht ist
      else letztesBild = 0;
    }
    function anwenden(st, alles, zeit) {
      if (!st || !st.v) return;
      var t = Object.assign({}, st), k = st.kamera || {}, f = k.ref ? CGL.homeAlt() / k.ref : 1;
      delete t.tafelbild; delete t.v; delete t.kamera;
      if (t.fenster && t.fenster.modal === 'lehrer') t.fenster.modal = null;
      t.drehen = false;
      if (!alles && (zeichnet || Date.now() - eigeneZeichnung < 800)) delete t.zeichnung;
      if (isFinite(k.lat) && isFinite(k.lng)) kameraRein({ lat: k.lat, lng: k.lng, alt: Math.max(0.15, Math.min(6, (k.alt || CGL.homeAlt()) * f)) }, zeit || Date.now(), alles);
      wendet++;
      try { CGL.applyState(t, { quelle: 'lehrer', dauer: 0 }); } finally { wendet--; }
      if ('zeichnung' in t) gemeldet = JSON.stringify(CGL.getState().zeichnung);
      CGL.globe.controls().enabled = false;
    }
    bc.onmessage = function (e) {
      var m = e.data || {};
      if (m.ev === 'zustand') { zuletzt = Date.now(); verbindung(); anwenden(m.st, m.alles, m.t); }
      else if (m.ev === 'da') { var neu = Date.now() - zuletzt > 5000; zuletzt = Date.now(); verbindung(); if (neu) bc.postMessage({ ev: 'hallo' }); }
      else if (m.ev === 'weg') { zuletzt = 0; verbindung(); }
    };
    bc.postMessage({ ev: 'hallo' });
    setInterval(function () { bc.postMessage({ ev: 'da' }); verbindung(); }, 1500);
    window.addEventListener('pagehide', function () { bc.postMessage({ ev: 'tschuess' }); });
  }
})();
