/* Digitales Tafelbild: Rom und China – Globus, Zeitleiste, Kartenrolle
   Abhängigkeiten (lokal in vendor/): globe.gl, d3. Daten: data/*.json (erzeugt mit build_reiche.py) */
(function () {
  'use strict';

  var YMIN = -300, YMAX = 1453, ANTIKE_ENDE = 480, TEILUNG = 395, OSTROM = '#7b3fa0', SCHLACHT_JAHRE = 25;
  /* Zeitleiste in Epochen-Abschnitten, getrennt durch einen Zeitsprung (die Achse wird nicht gestreckt).
     a/b = Anteil der Leistenbreite; takt = ms pro Jahr beim Abspielen. */
  var SEGS = [
    { ep: 'antike', von: -300, bis: 480, a: 0, b: 0.76, takt: 70, tick: 50, major: 100, alt: 200, start: 117,
      name: 'Europäische Antike', sub: 'China: Qin, Han und Zeit der Teilung' },
    { ep: 'ming', von: 1400, bis: 1453, a: 0.79, b: 1, takt: 450, tick: 10, major: 20, alt: 40, start: 1405,
      name: 'Europäisches Spätmittelalter', sub: 'China: Ming-Dynastie (Zheng He) · Byzanz bis 1453' }
  ];
  var state = { mode: 'sat', on: {}, orte: false, rotate: true, schlachten: true, vw: false, limes: false, year: 117, epoche: 'antike' };
  var TRADE = { on: false, land: true, see: true, waren: true, gesandt: true, karawanen: false, strassen: false, schiff: false, hanseide: false };
  var STR_OPT = { ehemals: false, animieren: true, unsicherheit: false };   // Römerstraßen: Referenzmodus, Ausbau; unsicherheit bleibt aus (einfarbige Darstellung)
  var ZH = { on: true, fahrt: {} }, ZHD = null;
  var BILDER = { an: false };   // Abbildungen statt Symbole (nur wo eine Abbildung vorliegt, z. B. Zheng Hes Schatzschiff)
  var DATA, LAND, LAND_FLAT = {}, EVENTS = {}, BYID = {}, globe, mapOpen = false, mapReich = null, playTimer = null, lastKey = '', lastStrKey = '';
  var prevVis = null, mapPrev = null, flashTimer = null, VIG = null, rollView = 'vig';
  /* Geöffnete Fenster (Teil des Zustands, siehe getState): Schriftrolle, Infokarte/Schülertext, Warenübersicht, Hilfe */
  var FENSTER = { rolle: null, info: null, waren: null, modal: null }, INFO_NEU = null;
  var KAMERA_GESETZT = 0;   // Zeitpunkt der letzten über applyState gesetzten Kamera
  var ZUSTAND = { hoerer: [], still: 0, fern: 0 };
  var DARF = function () { return true; };   // Schülerrechte in Live-Sessions (js/session.js setzt das)
  function darfLokal(recht) { return ZUSTAND.fern > 0 || DARF(recht); }

  var SWORDS = '<svg viewBox="0 0 24 24" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">' +
    '<path d="M5 4l11 11M19 4L8 15"/><path d="M13 17l5-5M6 12l5 5"/><path d="M16.5 15.5L20 19M7.5 15.5L4 19"/></g></svg>';
  var SWORD_PATHS = ['M5 4l11 11M19 4L8 15', 'M13 17l5-5M6 12l5 5', 'M16.5 15.5L20 19M7.5 15.5L4 19'];

  function $(s) { return document.querySelector(s); }
  function fmtYear(y) { return y < 0 ? (-y) + ' v. Chr.' : y + ' n. Chr.'; }
  function shortYear(y) { return y < 0 ? (-y) + ' v.' : y + ' n.'; }
  function toast(msg) {
    var t = $('#toast'); t.textContent = msg; t.classList.add('show');
    clearTimeout(toast._t); toast._t = setTimeout(function () { t.classList.remove('show'); }, 4200);
  }
  function rgb(h) { var n = parseInt(h.slice(1), 16); return [n >> 16 & 255, n >> 8 & 255, n & 255]; }
  function rgba(h, a) { var c = rgb(h); return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + a + ')'; }
  function mix(h, w, t) { var a = rgb(h), b = rgb(w); return 'rgb(' + a.map(function (v, i) { return Math.round(v + (b[i] - v) * t); }).join(',') + ')'; }

  /* ---------- Daten ---------- */
  function M(r) { return DATA.meta[r]; }
  // Reichsdaten gelten nur für den antiken Abschnitt (Rom hat in den Daten bis 1453, gezeichnet ist aber nur bis 480)
  var MITTEL = {};   // Reiche mit Gebieten im Spätmittelalter (Byzanz, Osmanen); gefüllt beim Laden
  function exists(r, y) { return y >= M(r).von && y < M(r).bis && (y <= ANTIKE_ENDE || !!MITTEL[r]); }
  function regionsAt(r, y) {
    return DATA.regionen.filter(function (f) { var p = f.properties; return p.reich === r && p.von <= y && y < p.bis; });
  }
  function activeEvent(r, y) {
    if (!exists(r, y) || !regionsAt(r, y).length) return null;
    var cur = null;
    (EVENTS[r] || []).forEach(function (e) { if (e.jahr <= y) cur = e; });
    return cur;
  }
  function regionColor(f, y) {
    var p = f.properties;
    return (p.reich === 'rom' && p.seite === 'o' && y >= TEILUNG) ? OSTROM : M(p.reich).farbe;
  }
  function visibleBattles(y) {
    if (!state.schlachten) return [];
    return DATA.schlachten.filter(function (b) {
      return y >= b.jahr && y <= b.jahr + SCHLACHT_JAHRE && b.reiche.some(function (r) { return state.on[r]; });
    });
  }

  /* ---------- Globus ---------- */
  /* Schematische Ansicht: fertige Textur (img/earth-schematic.png, erzeugt mit build_schema_textur.py aus Natural Earth).
     Früher wurde das ganze Festland als ein riesiges 3D-Polygon gezeichnet; das ergab Risse und Flackern. */
  var SCHEM_URL = 'img/earth-schematic.png', LANDF = null;
  function schemTexture() {   // 8192er-Fassung aus Natural Earth 1:10 Mio. (build_schema_kacheln.py), sonst die alte 4096er
    var max = 0; try { max = globe.renderer().capabilities.maxTextureSize; } catch (e) {}
    return max >= 8192 ? 'img/earth-schematic-8k.png' : SCHEM_URL;
  }
  /* Satellitenbild: NASA Blue Marble Next Generation (Juli 2004) in 8192×4096. Geräte, deren Grafikkarte
     so große Texturen nicht kann (manche ältere Tablets), bekommen die alte 4096er-Fassung. */
  function satTexture() {
    var max = 0; try { max = globe.renderer().capabilities.maxTextureSize; } catch (e) {}
    return max >= 8192 ? 'img/earth-blue-marble-8k.jpg' : 'img/earth-blue-marble.jpg';
  }
  /* Kacheln für die Nahansicht, Stufe 6 weltweit bis ±72°, Stufen 7–8 nur in der Region Europa–China:
     Satellit: img/tiles (build_kacheln.py, NASA Blue Marble Next Generation, bis 500 m/Pixel),
     schematisch: img/tiles_schem (build_schema_kacheln.py, Natural Earth 1:10 Mio.).
     Unter den Kacheln bleibt eine Kopie der Grundkugel mit dem 8k-Bild sichtbar: Fehlende Kacheln (außerhalb
     der Region), gröbere Stufen und die Polargebiete zeigen dann das 8k-Bild statt Schwarz.
     'data:,' als Adresse heißt „keine Kachel“: Es wird nichts geladen, die Grundkugel bleibt sichtbar. */
  var KACHELN = { region: [-20, -15, 150, 62], stufenRegion: [7, 8], min: 6, max: 8, polar: 72, an: null, basis: null, te: null, bereich: {} };
  function kachelBereich(z, box) {
    var n = Math.pow(2, z);
    function tx(lng) { return Math.min(n - 1, Math.max(0, Math.floor((lng + 180) / 360 * n))); }
    function ty(lat) { var r = lat * Math.PI / 180; return Math.min(n - 1, Math.max(0, Math.floor((1 - Math.asinh(Math.tan(r)) / Math.PI) / 2 * n))); }
    return [tx(box[0]), tx(box[2]), ty(box[3]), ty(box[1])];
  }
  function kachelUrl(x, y, z) {
    if (z < KACHELN.min) return 'data:,';
    var b = KACHELN.bereich[z] || (KACHELN.bereich[z] = KACHELN.stufenRegion.indexOf(z) >= 0
      ? kachelBereich(z, KACHELN.region)
      : kachelBereich(z, [-180, -KACHELN.polar, 180, KACHELN.polar]));   // Stufe 6: Polargebiete aus, dort wären die Kacheln winzig und zahlreich
    if (x < b[0] || x > b[1] || y < b[2] || y > b[3]) return 'data:,';
    return state.mode === 'schem' ? 'img/tiles_schem/' + z + '/' + x + '/' + y + '.png' : 'img/tiles/' + z + '/' + x + '/' + y + '.jpg';
  }
  function kachelnVorbereiten() {
    if (KACHELN.te) return true;
    var mesh = null, te = null, mat = globe.globeMaterial();
    globe.scene().traverse(function (o) {
      if (!mesh && o.isMesh && o.material === mat) mesh = o;
      if (!te && o.thresholds && 'minLevel' in o && 'tileUrl' in o) te = o;
    });
    if (!mesh || !te) return false;
    var basis = mesh.clone(); basis.scale.setScalar(0.997); basis.visible = false;
    mesh.parent.add(basis);
    te.thresholds = te.thresholds.map(function (_, t) { return 16 / Math.pow(2, t); });   // eine Stufe früher schärfer als Standard
    globe.globeTileEngineMaxLevel(KACHELN.max);
    KACHELN.basis = basis; KACHELN.te = te;
    return true;
  }
  function kachelnPruefen() {
    if (!globe) return;
    if (!kachelnVorbereiten()) { clearTimeout(kachelnPruefen.t); kachelnPruefen.t = setTimeout(kachelnPruefen, 300); return; }   // Szene noch nicht fertig
    var an = state.mode;   // Kacheln in beiden Ansichten (Satellit: img/tiles, schematisch: img/tiles_schem); Stufe nach Abstand
    if (an === KACHELN.an) return;
    KACHELN.an = an;
    KACHELN.basis.visible = true;
    globe.globeTileEngineUrl(null); globe.globeTileEngineClearCache();
    globe.globeTileEngineUrl(function (x, y, z) { return kachelUrl(x, y, z); });   // neue Funktion = Engine lädt neu
  }
  /* Anisotrope Filterung: Gebiete am schräg gesehenen Globusrand bleiben scharf. Die Textur lädt asynchron. */
  function scharfStellen(url) {
    var n = 0;
    (function warte() {
      var m = globe.globeMaterial && globe.globeMaterial(), map = m && m.map;
      if (map && map.image && String(map.image.src || '').indexOf(url) >= 0) {
        var a = globe.renderer().capabilities.getMaxAnisotropy();
        if (map.anisotropy !== a) { map.anisotropy = a; map.needsUpdate = true; }
        return;
      }
      if (++n < 100) setTimeout(warte, 200);
    })();
  }

  function capColor(f) {
    var p = f.properties || {};
    if (p.kind === 'land') return '#e7dcc0';
    var c = regionColor(f, state.year), a = p.art === 'einfluss' ? 0.3 : M(p.reich).haupt ? 0.62 : M(p.reich).kontext ? 0.4 : 0.55;
    if (f.__flash && Date.now() - f.__flash < 1300) return rgba(c, Math.min(0.9, a + 0.25));
    return rgba(c, a);
  }
  function visiblePolys() {
    var a = [];
    DATA.reihen.forEach(function (r) { if (state.on[r]) a.push.apply(a, regionsAt(r, state.year)); });
    return a;
  }
  /* Ort sichtbar, solange sein Gebiet zum Reich gehört (zeiten aus build_reiche.py) */
  function ortAktiv(o, y) { return o.zeiten.some(function (z) { return y >= z[0] && y < z[1]; }); }
  function visibleCities() {
    if (!state.orte) return [];
    return DATA.orte.filter(function (o) {
      if (o.stufe > LBL.stufe || !state.on[o.reich] || !exists(o.reich, state.year)) return false;
      return ortAktiv(o, state.year);
    });
  }
  /* Beschriftung je Zoom: weiter weg nur Hauptstädte, näher auch kleinere Orte. Schrift wächst nicht mit, sondern
     bleibt auf dem Bildschirm etwa gleich groß (Größe in Grad ∝ Höhe der Kamera). */
  var LBL = { stufe: 1, s: 1, key: '' };
  function zoomPruefen() {
    if (!globe) return;
    var alt = globe.pointOfView().altitude;
    // Abstand relativ zur Standard-Zoomstufe des Geräts (homeAlt, am Desktop 2.7): ganz weit weg keine Orte,
    // Standard nur Weltstädte, mittel große Provinzzentren, nah weitere Hauptstädte und Wirtschaftszentren, ganz nah alle Orte
    var rel = alt * 2.7 / homeAlt();
    var stufe = rel > 3.3 ? 0 : rel > 1.3 ? 1 : rel > 0.55 ? 2 : rel > 0.28 ? 3 : 4;
    var s = Math.max(0.11, Math.min(1.7, alt / 1.7));   // weit weg größer, damit die Weltstädte lesbar sind
    s = Math.pow(2, Math.round(Math.log(s) / Math.LN2 * 3) / 3);   // in Stufen, damit nicht bei jeder Bewegung neu gezeichnet wird
    var key = stufe + '|' + s;
    if (key === LBL.key) return;
    LBL.stufe = stufe; LBL.s = s; LBL.key = key;
    globe.labelSize(labelSize).labelDotRadius(labelDot);
    refreshLabels(); refreshHtml();
  }
  function labelSize(d) {
    var b = d.kind === 'karawane' ? 0.75 : labelIsTrade(d) ? 1.0 : d.stufe ? [0, 1.45, 0.84, 0.72, 0.62][d.stufe] : 0.9;
    return b * LBL.s;
  }
  function labelDot(d) {
    var b = d.kind === 'karawane' ? 0.3 : labelIsTrade(d) ? 0.42 : d.stufe ? [0, 0.4, 0.25, 0.2, 0.17][d.stufe] : 0.3;
    return b * LBL.s;
  }
  function refreshLabels() {
    if (state.epoche === 'ming') { var zv = CUR_ZV || zhVisible(state.year); globe.labelsData(zhLabels(zv)); return; }
    var tv = CUR_TV || tradeVisible(state.year);
    globe.labelsData(tv.places.concat(karNodeLabels(tv)));
  }
  /* HTML-Ebene: Ortsnamen (mit dunklem Rand, gut lesbar über Straßen), Schlachten, Gesandtschaften, Waren, Standort */
  function refreshHtml() {
    if (state.epoche === 'ming') { globe.htmlElementsData(zhHtml(CUR_ZV || zhVisible(state.year))); return; }
    var tv = CUR_TV || tradeVisible(state.year);
    globe.htmlElementsData(visibleCities().concat(visibleBattles(state.year), tv.kontakte, wareTags(tv), vwTags(), limesKastelle(), [STANDORT || JENA]));
  }
  function battleEl(d) {
    if (d.__el) return d.__el;
    var bel = document.createElement('div'); bel.className = 'battle';
    bel.innerHTML = SWORDS + '<span></span>';
    bel.querySelector('span').textContent = d.name + ' ' + shortYear(d.jahr);
    bel.title = d.name + ' (' + fmtYear(d.jahr) + '): ' + d.note;
    bel.addEventListener('click', function (e) { e.stopPropagation(); toast('⚔ ' + d.name + ', ' + fmtYear(d.jahr) + ': ' + d.note); });
    d.__el = bel; return bel;
  }
  function refreshGlobe() {
    if (state.epoche === 'ming') { refreshGlobeMing(); return; }
    var polys = visiblePolys(), now = Date.now();
    if (prevVis) polys.forEach(function (f) { if (f.properties.id !== undefined && !prevVis.has(f)) f.__flash = now; });
    prevVis = new Set(polys);
    globe.polygonsData(polys);
    var tv = CUR_TV || tradeVisible(state.year);
    refreshLabels();
    pfadeSetzen(limesPaths().concat(tradeGlobePaths(tv), vwPaths(), netzePaths()));
    globe.pointsData(hanStationen(state.year).concat(netzeOrte()));
    refreshHtml(); vwDrehenBald();
    karUpdate();
    setTimeout(scheduleTagSides, 50);
    clearTimeout(flashTimer);
    flashTimer = setTimeout(function () { globe.polygonCapColor(capColor); }, 1350);
  }
  function applyMode() {
    var sat = state.mode === 'sat';
    var tex = sat ? satTexture() : schemTexture();
    globe.globeImageUrl(tex);
    scharfStellen(tex);
    KACHELN.an = null; kachelnPruefen();
    globe.bumpImageUrl(sat ? 'img/earth-topology.png' : '');
    globe.backgroundImageUrl(sat ? 'img/night-sky.png' : '');
    globe.backgroundColor(sat ? '#000010' : '#14202e');
    globe.showAtmosphere(true);
    globe.atmosphereColor(sat ? '#6fb1ff' : '#9fd0ee');
    globe.atmosphereAltitude(sat ? 0.17 : 0.09);
    $('#modeSat').classList.toggle('on', sat); $('#modeSat').setAttribute('aria-pressed', sat);
    $('#modeSchem').classList.toggle('on', !sat); $('#modeSchem').setAttribute('aria-pressed', !sat);
    globe.pathColor(pathColor).labelColor(labelColor);   // Handelsfarben an Hintergrund anpassen
    refreshGlobe();
  }
  /* Schriftrolle nur für Reiche, die die Schülerinnen und Schüler untersuchen sollen.
     Kontext-Reiche (europäische Nachfolgestaaten) nie; sonst abschaltbar mit "schriftrolle": false in data/vignetten.json. */
  function hatRolle(r) {
    var m = DATA.meta[r]; if (!m || m.ohneRolle) return false;
    var c = VIG && VIG.reiche && VIG.reiche[r];
    if (m.kontext) return !!(c && c.schriftrolle === true);
    return !(c && c.schriftrolle === false);
  }
  function polyLabel(f) {
    var p = f.properties; if (p.kind === 'land') return '';
    var reich = (p.reich === 'rom' && state.year > ANTIKE_ENDE) ? 'Byzantinisches Reich (Ostrom)'
      : (p.reich === 'rom' && state.year >= TEILUNG) ? (p.seite === 'o' ? 'Ostrom' : 'Westrom') : M(p.reich).name;
    var d = document.createElement('div');
    var b = document.createElement('b'); b.textContent = p.name; d.appendChild(b);
    d.appendChild(document.createElement('br'));
    d.appendChild(document.createTextNode(p.reich === 'ming' ? 'Ming-Dynastie (1368–1644) · Fläche vereinfacht'
      : reich + (p.art === 'einfluss' ? ' (Einfluss)' : '') + ' · ' + fmtYear(p.von) + (p.bis < M(p.reich).bis ? ' bis ' + fmtYear(p.bis) : '')));
    d.appendChild(document.createElement('br'));
    var k = document.createElement('small'); k.textContent = hatRolle(p.reich) ? 'Klick: Schriftrolle öffnen' : 'Europa (Kontext) · keine Schriftrolle'; d.appendChild(k);
    return '<div class="gtip">' + d.innerHTML + '</div>';
  }
  function labelColor(d) {
    if (d.kind === 'handel') return tradeCol((routeById(d.an[0][0]) || { art: 'land' }).art);
    if (d.kind === 'zhhafen') return state.mode === 'schem' ? '#0d5a35' : '#9af5bd';
    if (d.kind === 'mingstadt') return state.mode === 'schem' ? '#7a3c0a' : '#ffd29a';
    if (d.kind === 'karawane') return state.mode === 'schem' ? '#5a2c06' : '#ffe2a8';
    return mix(M(d.reich).farbe, '#ffffff', 0.7);
  }
  function labelIsTrade(d) { return d.kind === 'handel' || d.kind === 'zhhafen' || d.kind === 'karawane'; }
  function initGlobe() {
    LANDF = { type: 'Feature', properties: { kind: 'land' }, geometry: LAND.geometry };
    globe = Globe()($('#globe'))
      .width(window.innerWidth).height(window.innerHeight)
      .polygonGeoJsonGeometry(function (f) { return f.geometry; })
      .polygonCapColor(capColor)
      .polygonSideColor(function (f) { return f.properties.kind === 'land' ? 'rgba(0,0,0,0)' : 'rgba(0,0,0,0.15)'; })
      .polygonStrokeColor(function (f) { return f.properties.kind === 'land' ? 'rgba(90,80,55,0.55)' : 'rgba(35,15,5,0.45)'; })
      .polygonAltitude(function (f) { var p = f.properties; return p.kind === 'land' ? 0.0003 : (M(p.reich).haupt ? 0.0007 : 0.0005); })
      .polygonCapCurvatureResolution(1)   // fein unterteilt, damit die flach liegenden Flächen nicht in die Kugel einsinken
      .polygonsTransitionDuration(900)
      .polygonLabel(polyLabel)
      .labelLat('lat').labelLng('lng').labelText(function (d) { return d.kind === 'handel' ? d.name.replace(/Ó/g, 'O') : d.name; })
      .labelAltitude(0.0014).labelResolution(2)
      .labelColor(labelColor)
      .labelSize(labelSize).labelDotRadius(labelDot)
      .labelLabel(function (d) {
        if (!labelIsTrade(d)) return '';
        var t = el('div', 'gtip'); t.appendChild(el('b', null, d.name)); t.appendChild(el('br'));
        t.appendChild(document.createTextNode((d.kind === 'karawane' ? d.hinweis : d.vermittler) + ' · Klick für Infos')); return t.outerHTML;
      })
      .htmlLat('lat').htmlLng('lng').htmlAltitude(function (d) { return d.zeiten ? 0.0013 : d.kind === 'waren' ? 0.0015 : 0.0016; }).htmlElement(htmlEl).htmlTransitionDuration(0);
    initTradeGlobe();
    globe.pointLat('lat').pointLng('lng').pointAltitude(0.0025).pointResolution(10).pointsTransitionDuration(0)
      .pointRadius(function (s) { if (s.netzort) return s.gross ? 0.14 : 0.08; return /Hauptstadt|Kommandantur|Poststation|Pass/.test(s.typ) ? 0.16 : 0.09; })
      .pointColor(function (s) { return s.netzort ? netzOrtFarbe(s) : HS_FARBE[s.typ] || '#d8c7a8'; })
      .pointLabel(function (s) { var t = el('div', 'gtip');
        if (s.netzort) { t.appendChild(el('b', null, netzOrtTitel(s))); t.appendChild(el('br')); t.appendChild(document.createTextNode(s.typ + ' · ' + s.netzM.name + ' · Klick für Infos')); return t.outerHTML; }
        t.appendChild(el('b', null, s.py + ' (' + s.zh + ')')); t.appendChild(el('br'));
        t.appendChild(document.createTextNode(s.typ + ' · Seidenstraße der Han · Klick für Infos')); return t.outerHTML; })
      .onPointClick(function (s) { if (s && s.hanstation) openHanStation(s); else if (s && s.netzort) openNetzOrt(s); });
    globe.controls().addEventListener('change', scheduleTagSides);
    globe.controls().addEventListener('change', karDrawSoon);
    globe.controls().addEventListener('change', zoomPruefen);
    globe.controls().addEventListener('change', vwDrehenBald);
    setInterval(zoomPruefen, 500);   // Kameraflüge (pointOfView) melden kein 'change'
    window.addEventListener('resize', scheduleTagSides);
    var c = globe.controls();
    c.autoRotate = state.rotate; c.autoRotateSpeed = 0.35;
    c.minDistance = 106; c.maxDistance = 520;   // nah heran: dort greifen die 500-m-Kacheln
    c.zoomSpeed = 0.9; c.enablePan = false;
    globe.pointOfView({ lat: 36, lng: 62, altitude: homeAlt() }, 0);
    applyMode();
    function sizeGlobe() { var g = $('#globe'); globe.width(g.clientWidth || window.innerWidth).height(g.clientHeight || window.innerHeight); }
    window.addEventListener('resize', sizeGlobe);
    if (window.ResizeObserver) new ResizeObserver(sizeGlobe).observe($('#globe'));

    // Klick auf eine Reichsfläche => Schriftrolle dieses Reichs entrollen
    globe.onPolygonClick(function (f) { var p = f && f.properties; if (p && p.reich && hatRolle(p.reich)) openMap(p.reich); });
    globe.onPolygonHover(function (f) { $('#globe').style.cursor = f && f.properties && hatRolle(f.properties.reich) ? 'pointer' : ''; });
    /* Touch: bei sehr kurzem Tippen kennt globe.gl das Objekt unter dem Finger evtl. noch nicht (Hover wird gedrosselt
       berechnet). Dann über die Geokoordinate das Reich suchen – nur wenn nichts anderes (Route, Ort) geöffnet wurde. */
    var cvs = globe.renderer().domElement, tap = null;
    cvs.addEventListener('pointerdown', function (e) { tap = e.pointerType === 'touch' ? { x: e.clientX, y: e.clientY, t: Date.now() } : null; });
    cvs.addEventListener('pointerup', function (e) {
      if (!tap || e.pointerType !== 'touch') return;
      var ok = Math.hypot(e.clientX - tap.x, e.clientY - tap.y) < 10 && Date.now() - tap.t < 600; tap = null;
      if (!ok) return;
      var r = cvs.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
      setTimeout(function () {
        if (mapOpen || !$('#tinfo').hidden) return;
        var c = globe.toGlobeCoords(x, y); if (!c) return;
        var hit = visiblePolys().filter(function (f) { return hatRolle(f.properties.reich) && d3.geoContains(f, [c.lng, c.lat]); });
        hit.sort(function (a, b) { return (a.properties.art === 'einfluss') - (b.properties.art === 'einfluss'); });
        if (hit[0]) openMap(hit[0].properties.reich);
      }, 160);
    });
  }
  function fly(lat, lng, alt) { globe.pointOfView({ lat: lat, lng: lng, altitude: alt }, 1400); }

  /* ---------- Infokarten ---------- */
  function renderCards() {
    if (state.epoche === 'ming') { renderCardsMing(); return; }
    var box = $('#cards'); box.innerHTML = '';
    DATA.reihen.forEach(function (r) {
      if (!state.on[r]) return;
      var m = M(r), d = document.createElement('div');
      d.className = 'card'; d.style.setProperty('--c', m.farbe);
      if (!m.haupt) {
        if (!regionsAt(r, state.year).length) return;
        d.classList.add('mini');
        d.innerHTML = '<div class="k"></div><p></p>';
        d.querySelector('.k').textContent = m.name + ' · ' + shortYear(m.von) + '–' + shortYear(m.bis);
        d.querySelector('p').textContent = m.kurz;
        if (m.kontext) d.classList.add('kx');
        if (hatRolle(r)) {
          var mb = document.createElement('button'); mb.type = 'button'; mb.textContent = 'Schriftrolle öffnen';
          mb.addEventListener('click', function () { openMap(r); }); d.appendChild(mb);
        }
        box.appendChild(d); return;
      }
      var e = activeEvent(r, state.year);
      if (!e) {
        d.classList.add('none');
        d.innerHTML = '<div class="k"></div><div class="t"></div>';
        d.querySelector('.k').textContent = m.name;
        d.querySelector('.t').textContent = state.year < m.von ? 'Besteht in diesem Jahr noch nicht.' : 'Besteht in diesem Jahr nicht mehr.';
      } else {
        if (r === 'rom' && state.year >= TEILUNG) d.style.setProperty('--c2', OSTROM);
        d.innerHTML = '<div class="k"></div><div class="t"></div><div class="y"></div><p></p><button type="button">Schriftrolle öffnen</button>';
        d.querySelector('.k').textContent = (r === 'rom' && state.year >= TEILUNG) ? 'Weströmisches und Oströmisches Reich' : m.name;
        d.querySelector('.t').textContent = e.titel;
        d.querySelector('.y').textContent = 'Stand: ' + e.label;
        d.querySelector('p').textContent = e.note;
        d.querySelector('button').addEventListener('click', function () { openMap(r); });
      }
      box.appendChild(d);
    });
  }

  /* ---------- Reiche-Auswahl ---------- */
  function buildChips() {
    DATA.reihen.forEach(function (r) {
      var m = M(r); if (m.haupt) return;
      var box = m.frueh ? $('#fruehChips') : m.kontext ? $('#kxChips') : $('#nbChips');
      var b = document.createElement('button'); b.type = 'button'; b.className = 'chip nb' + (m.kontext ? ' kx' : ''); b.dataset.r = r;
      b.style.setProperty('--c', m.farbe); b.style.setProperty('--cbg', rgba(m.farbe, 0.28));
      b.setAttribute('aria-pressed', 'false');
      b.title = m.name + ' (' + fmtYear(m.von) + ' bis ' + fmtYear(m.bis) + '). ' + m.kurz + (m.kontext ? ' Nur zur Orientierung, keine Schriftrolle.' : '');
      b.innerHTML = '<i></i><span></span>'; b.querySelector('span').textContent = m.name;
      b.addEventListener('click', function () { var o = {}; o[r] = !state.on[r]; setState({ reiche: o }); reichHinweis(r); });
      box.appendChild(b);
    });
  }
  function setOn(r, v, batch) {
    state.on[r] = v;
    var b = r === 'rom' ? $('#tglRom') : r === 'han' ? $('#tglHan') : $('.chip.nb[data-r="' + r + '"]');
    b.classList.toggle('on', v); b.setAttribute('aria-pressed', v);
    if (batch) return;
    if (!M(r).haupt) buildLanes();
    lastKey = ''; setYear(state.year);
    if (v && !M(r).haupt && !regionsAt(r, state.year).length) toast(M(r).name + ' besteht von ' + fmtYear(M(r).von) + ' bis ' + fmtYear(M(r).bis));
  }
  function reichHinweis(r) { if (state.on[r] && !M(r).haupt && !regionsAt(r, state.year).length) toast(M(r).name + ' besteht von ' + fmtYear(M(r).von) + ' bis ' + fmtYear(M(r).bis)); }
  function updateChips() {
    document.querySelectorAll('.chip.nb').forEach(function (b) { b.classList.toggle('absent', !exists(b.dataset.r, state.year)); });
  }

  /* ---------- Zeitleiste (Abschnitte je Epoche, dazwischen Zeitsprung) ---------- */
  function segOf(y) { return y >= SEGS[1].von ? SEGS[1] : SEGS[0]; }
  /* Lineare Teile der Leiste: ein Abschnitt kann mehrere Teile mit eigenem Maßstab haben (frühe Hochkulturen) */
  function teile() { var T = []; SEGS.forEach(function (S) { if (!S.aus) (S.teile || [S]).forEach(function (t) { T.push(t); }); }); return T; }
  function teilVon(y) { return teile().filter(function (t) { return y >= t.von && y <= t.bis; })[0] || segOf(y); }
  function pct(y) {
    var T = teile();
    if (y <= T[0].von) return T[0].a * 100;
    for (var i = 0; i < T.length; i++) {
      var t = T[i];
      if (y > t.bis) continue;
      if (y >= t.von) return (t.a + (y - t.von) / (t.bis - t.von) * (t.b - t.a)) * 100;
      var p = T[i - 1]; return (p.b + (y - p.bis) / (t.von - p.bis) * (t.a - p.b)) * 100;   // im Zeitsprung
    }
    return T[T.length - 1].b * 100;
  }
  /* Anteil 0..1 auf der Leiste -> Jahr; im Zeitsprung rastet es am näheren Rand ein */
  function yearAt(f) {
    var T = teile();
    if (f <= T[0].a) return T[0].von;
    for (var i = 0; i < T.length; i++) {
      var t = T[i];
      if (f > t.b) continue;
      if (f >= t.a) return Math.round(t.von + (f - t.a) / (t.b - t.a) * (t.bis - t.von));
      var p = T[i - 1]; return f - p.b < t.a - f ? p.bis : t.von;
    }
    return T[T.length - 1].bis;
  }
  /* Jahre im Zeitsprung gibt es nicht: vorwärts -> Anfang des nächsten Abschnitts, rückwärts -> Ende des vorigen */
  /* Jahre addieren ohne Jahr 0: 1 v. Chr. + 10 Jahre = 10 n. Chr. (Rechnung in astronomischen Jahren) */
  function plusJahre(y, d) { var a = (y < 0 ? y + 1 : y) + d; return a <= 0 ? a - 1 : a; }
  function normYear(y, prev) {
    y = Math.max(YMIN, Math.min(YMAX, Math.round(y)));
    if (y === 0) y = prev != null && prev > 0 ? -1 : 1;   // historische Zählung: auf 1 v. Chr. folgt 1 n. Chr.
    var ende = SEGS[0].bis;   // ohne Mittelalter-Teil: 480, sonst 1400 (kein Zeitsprung)
    if (y > ende && y < SEGS[1].von) {
      if (prev != null && y !== prev) y = y > prev ? SEGS[1].von : ende;
      else y = y - ende < SEGS[1].von - y ? ende : SEGS[1].von;
    }
    return y;
  }
  function buildTicks() {
    var ticks = $('#ticks'); ticks.innerHTML = '';
    SEGS.forEach(function (S0, si) { if (S0.aus) return; (S0.teile || [S0]).forEach(function (S, ti, alle) {
      for (var y = Math.ceil(S.von / S.tick) * S.tick; ti < alle.length - 1 || S.mittel ? y < S.bis : y <= S.bis; y += S.tick) {
        var t = document.createElement('div'); t.style.left = pct(y) + '%';
        if (y % S.major) { t.className = 'tick minor'; }
        else {
          t.className = 'tick' + (y % S.alt ? ' odd' : '');
          var l = el('span', 'tk-l', si ? String(y) : y === 0 ? 'Chr. Geb.' : S.kurz ? shortYear(y) : fmtYear(y)), sh = el('span', 'tk-s', si ? String(y) : y === 0 ? '0' : shortYear(y));
          t.appendChild(l); t.appendChild(sh);
        }
        ticks.appendChild(t);
      }
    }); });
    buildEpochs();
  }
  /* Epochen-Übersicht über der Zeitleiste: Name je Abschnitt, Zeitsprung dazwischen. Klick springt in den Abschnitt. */
  function buildEpochs() {
    var bar = $('#epbar'); bar.innerHTML = '';
    SEGS.forEach(function (S0) { if (S0.aus) return; (S0.teile || [S0]).forEach(function (S) {
      var d = el('button', 'ep'); d.type = 'button'; d.dataset.ep = S0.ep; d.dataset.von = S.von; d.dataset.bis = S.bis;
      d.style.left = S.a * 100 + '%'; d.style.width = (S.b - S.a) * 100 + '%';
      d.appendChild(el('b', null, S.name)); d.appendChild(el('span', null, S.sub));
      d.title = S.name + ' (' + fmtYear(S.von) + ' bis ' + fmtYear(S.bis) + '), ' + S.sub;
      d.addEventListener('click', function () { if (!(state.year >= S.von && state.year <= S.bis)) setYear(S.start); });
      bar.appendChild(d);
    }); });
    if (SEGS[0].aus || SEGS[1].aus || SEGS[1].a <= SEGS[0].b) return;   // nur ein Abschnitt oder lückenlos: kein Zeitsprung
    var g = el('div', 'epgap', '≈'); g.style.left = SEGS[0].b * 100 + '%'; g.style.width = (SEGS[1].a - SEGS[0].b) * 100 + '%';
    g.title = 'Zeitsprung: ' + fmtYear(SEGS[0].bis) + ' bis ' + fmtYear(SEGS[1].von) + ' ist nicht dargestellt';
    bar.appendChild(g);
  }
  function buildLanes() {
    var lanes = $('#lanes'); lanes.innerHTML = '';
    var zero = document.createElement('div'); zero.className = 'zero'; zero.style.left = pct(0) + '%'; lanes.appendChild(zero);
    if (!SEGS[0].aus && !SEGS[1].aus && SEGS[1].a > SEGS[0].b) { var gap = el('div', 'lgap'); gap.style.left = SEGS[0].b * 100 + '%'; gap.style.width = (SEGS[1].a - SEGS[0].b) * 100 + '%'; lanes.appendChild(gap); }
    var cur = document.createElement('div'); cur.className = 'cursor'; lanes.appendChild(cur);
    var shown = DATA.reihen.filter(function (r) { return M(r).haupt || state.on[r]; });
    shown.forEach(function (r) {
      var m = M(r), lane = document.createElement('div');
      lane.className = 'lane' + (m.haupt ? '' : ' thin') + (m.kontext ? ' kx' : ''); lane.dataset.r = r;
      lane.style.setProperty('--c', m.farbe); lane.style.setProperty('--cs', rgba(m.farbe, 0.2));
      lane.style.setProperty('--cb', rgba(m.farbe, 0.6)); lane.style.setProperty('--ct', mix(m.farbe, '#ffffff', 0.55));
      if (MITTEL[r]) lane.classList.add('mittel');
      [[Math.max(YMIN, m.von), Math.min(ANTIKE_ENDE, m.bis)], MITTEL[r] ? [Math.max(SEGS[1].von, m.von), Math.min(YMAX, m.bis)] : null].forEach(function (ab, k) {
        if (!ab || ab[1] <= ab[0]) return;
        var era = document.createElement('div'); era.className = 'era' + (k ? ' era-mittel' : '');
        era.style.left = pct(ab[0]) + '%'; era.style.width = (pct(ab[1]) - pct(ab[0])) + '%';
        var nm = document.createElement('span'); nm.className = 'nm'; nm.textContent = k && r === 'rom' ? 'Byzanz' : m.name; era.appendChild(nm);
        era.title = (k && r === 'rom' ? 'Byzantinisches Reich (Ostrom)' : m.name) + ': ' + fmtYear(m.von) + ' bis ' + fmtYear(m.bis);
        lane.appendChild(era);
      });
      if (r === 'rom') {   // ab 395: Ostrom
        var ost = document.createElement('div'); ost.className = 'era-ost';
        ost.style.left = pct(TEILUNG) + '%'; ost.style.width = (pct(ANTIKE_ENDE) - pct(TEILUNG)) + '%';
        ost.style.setProperty('--co', rgba(OSTROM, 0.55)); ost.title = 'Ab 395 n. Chr.: Westrom (oben) und Ostrom (unten)';
        lane.appendChild(ost);
      }
      // Schlachten: in der ersten angezeigten Spur eines beteiligten Reichs
      DATA.schlachten.forEach(function (s) {
        var home = s.reiche.filter(function (x) { return shown.indexOf(x) >= 0; })[0];
        if (home !== r || s.jahr < YMIN || s.jahr > ANTIKE_ENDE) return;
        var bt = document.createElement('button'); bt.type = 'button'; bt.className = 'bt'; bt.dataset.y = s.jahr;
        bt.style.left = pct(s.jahr) + '%'; bt.innerHTML = SWORDS;
        bt.title = 'Schlacht: ' + s.name + ' (' + fmtYear(s.jahr) + ')';
        bt.addEventListener('click', function () { setYear(s.jahr); toast('⚔ ' + s.name + ', ' + fmtYear(s.jahr) + ': ' + s.note); });
        lane.appendChild(bt);
      });
      (EVENTS[r] || []).forEach(function (e) {
        if (e.jahr < YMIN || e.jahr > YMAX) return;   // außerhalb des Tafelbild-Zeitraums
        var k = document.createElement('button'); k.type = 'button'; k.className = 'mk'; k.dataset.y = e.jahr;
        k.style.left = pct(e.jahr) + '%'; k.textContent = shortYear(e.jahr);
        k.title = e.label + ': ' + e.titel;
        k.addEventListener('click', function () { setYear(e.jahr); });
        lane.appendChild(k);
      });
      lanes.appendChild(lane);
    });
    addMingLanes(lanes);
    lanes.classList.toggle('noschl', !state.schlachten);
    var nThin = shown.length - shown.filter(function (r) { return M(r).haupt; }).length;
    lanes.classList.toggle('dicht', nThin > 7);   // viele Nachbarreiche: Spuren enger, damit der Globus Platz behält
    var lt = $('#lanesToggle');
    lt.hidden = nThin === 0;
    lt.querySelector('span').textContent = 'Nachbarreiche (' + nThin + ')';
    updateMarkers();
  }
  function updateMarkers() {
    document.querySelectorAll('.lane').forEach(function (lane) {
      if (!DATA.meta[lane.dataset.r]) return;
      var e = activeEvent(lane.dataset.r, state.year);
      lane.querySelectorAll('.mk:not(.zhmk)').forEach(function (b) { b.classList.toggle('on', !!e && e.jahr === +b.dataset.y); });
    });
    document.querySelectorAll('.bt').forEach(function (b) {
      var d = state.year - b.dataset.y; b.classList.toggle('on', d >= 0 && d <= SCHLACHT_JAHRE);
    });
    updateMarkersMing();
    document.querySelectorAll('#epbar .ep').forEach(function (b) { b.classList.toggle('on', state.year >= +b.dataset.von && state.year <= +b.dataset.bis); });
    $('#lanes').classList.toggle('ming', state.epoche === 'ming');   // Spätmittelalter: antike Nachbarspuren ausblenden
  }
  function stateKey(y) {
    if (state.epoche === 'ming') {
      // auch bei ausgeblendeten Fahrten ändern sich Infokarten und Zeitleisten-Marker mit dem Jahr
      var akt = ZHD.verbindungen.filter(function (v) { return zhAktiv(v, y); }).map(function (v) { return v.nr; }).join(',');
      var zev = ZHD.ereignisse.filter(function (e) { return e.jahr <= y; }).length;
      stateKey.tv = EMPTY_TV; stateKey.zv = zhVisible(y);
      return 'ming|' + TRADE.on + ZH.on + '|' + akt + '|' + zev + '|' + stateKey.zv.key + '|' + netzeSchluessel(y);
    }
    stateKey.zv = null;
    var ids = [];
    DATA.reihen.forEach(function (r) { if (state.on[r]) regionsAt(r, y).forEach(function (f) { ids.push(f.properties.id); }); });
    var ev = DATA.reihen.map(function (r) { var e = activeEvent(r, y); return e ? e.jahr : 'x'; }).join(',');
    var bs = visibleBattles(y).map(function (b) { return b.name; }).join(',');
    var nb = DATA.reihen.map(function (r) { return exists(r, y) ? 1 : 0; }).join('');
    var tv = tradeVisible(y); stateKey.tv = tv;
    return ids.join(',') + '|' + ev + '|' + bs + '|' + nb + '|' + (y >= TEILUNG) + '|' + state.orte + '|' + state.schlachten + '|' + tv.key + '|' + state.vw + '|' + limesSchluessel(y) + '|' + netzeSchluessel(y);
  }
  function sliderPos(y) { return Math.round(pct(y) * 10); }   // Schieber 0..1000
  function setYear(y, fromSlider) {
    y = normYear(y, state.year);
    if (y !== state.year && !darfLokal('zeit')) { $('#year').value = sliderPos(state.year); return; }   // Zeitriegel gesperrt (Session)
    var ep = segOf(y).ep;
    if (ep !== state.epoche) epochWechsel(ep);
    karYearJump(y);
    state.year = y;
    if (!fromSlider) $('#year').value = sliderPos(y);
    $('#yearOut').textContent = fmtYear(y);
    $('#track').style.setProperty('--pf', pct(y) / 100);
    var key = stateKey(y), strKey = strassenSchluessel(y) + '#' + vwSchluessel(y);
    if (key !== lastKey) {
      lastKey = key; lastStrKey = strKey; CUR_TV = stateKey.tv; CUR_ZV = stateKey.zv || null; refreshGlobe(); renderCards(); updateMarkers(); updateChips(); renderTradeList(CUR_TV);
      if (mapOpen) drawMap(mapReich, true);
    } else if (strKey !== lastStrKey) {
      // nur das Straßennetz hat sich geändert: allein die Linien neu übergeben. Flächen, Beschriftungen und Karten
      // bleiben unberührt – sonst begänne die Aufspann-Animation der Provinzen bei jedem Jahresschritt neu (Flackern).
      lastStrKey = strKey;
      pfadeSetzen((state.epoche === 'ming' ? zhPaths(CUR_ZV || zhVisible(y)) : limesPaths().concat(tradeGlobePaths(CUR_TV), vwPaths())).concat(netzePaths()));
      if (state.vw) { refreshHtml(); vwDrehenBald(); }
      if (mapOpen) drawMap(mapReich, true);
    }
    else strassenAnteile(y);   // gleicher Stil, aber Netz wächst weiter
    visibleBattles(y).forEach(function (b) { if (b.__el) b.__el.classList.toggle('fresh', y - b.jahr <= 4); });
    zustandGemeldet();
  }
  /* Wechsel zwischen den Abschnitten (über Zeitleiste, Play, ±10, Tastatur) */
  function epochWechsel(ep) {
    state.epoche = ep;
    $('#sideTitle').textContent = ep === 'ming' ? 'Infos zu den Fahrten' : 'Infos zu den Reichen';
    globe.pathTransitionDuration(ep === 'ming' ? 0 : 600);   // Ming: keine Verformung; neue Fahrten zeichnen sich selbst ein (zhAnim)
    penStopAlle(); PEN.prevAkt = {}; PEN.prevEu = {};
    if (mapOpen) finishClose();
    KAR.prevY = null;
    if (ZUSTAND.kameraFolgt) return;   // applyState setzt gleich eine eigene Kamera
    if (ep === 'ming') fly(8, 82, homeAlt()); else fly(36, 62, homeAlt());
  }
  function togglePlay() {
    if (!playTimer && !darfLokal('zeit')) return;
    if (playTimer) { clearTimeout(playTimer); playTimer = null; $('#play').textContent = '▶'; return; }
    if (state.year >= YMAX) setYear(YMIN);
    $('#play').textContent = '❚❚';
    (function step() {
      // am Ende der Antike kurz anhalten, dann über den Zeitsprung
      var t = state.year === ANTIKE_ENDE ? 1500 : teilVon(state.year).takt || segOf(state.year).takt;
      playTimer = setTimeout(function () {
        if (state.year >= YMAX) { togglePlay(); return; }
        if (PENS.length) { step(); return; }   // erst weiter, wenn die laufenden Fahrten fertig gezeichnet sind
        setYear(plusJahre(state.year, 1)); step();
      }, t);
    })();
  }

  /* ---------- Flache Reichskarte ---------- */
  var W = 1200, H = 720;
  var RAHMEN = {};
  /* Kartenausschnitt: Rom/Han fest (meta.rahmen), Nachbarreiche aus allen ihren Gebieten (über alle Jahre) mit Rand */
  function rahmen(r) {
    if (M(r).rahmen) return M(r).rahmen;
    if (RAHMEN[r]) return RAHMEN[r];
    var z = M(r).zentrum, feats = DATA.regionen.filter(function (f) { return f.properties.reich === r; });
    var bb = feats.length ? d3.geoBounds({ type: 'FeatureCollection', features: feats }) : [[z[0] - 10, z[1] - 8], [z[0] + 10, z[1] + 8]];
    var w = bb[0][0], s = bb[0][1], e = bb[1][0], n = bb[1][1];
    var dx = Math.max(6, (e - w) * 0.22), dy = Math.max(5, (n - s) * 0.22);
    return (RAHMEN[r] = [w - dx, Math.max(-60, s - dy), e + dx, Math.min(75, n + dy)]);
  }
  function makeProj(r) {
    var b = rahmen(r), w = b[0], s = b[1], e = b[2], n = b[3], p;
    if (r === 'rom') p = d3.geoConicEquidistant().parallels([36, 46]).rotate([-17, 0]).center([0, 41]);
    else if (r === 'han') p = d3.geoConicEquidistant().parallels([22, 40]).rotate([-105, 0]).center([0, 30]);
    else { var cy = (s + n) / 2; p = d3.geoConicEquidistant().parallels([cy - 6, cy + 6]).rotate([-(w + e) / 2, 0]).center([0, cy]); }
    p.fitExtent([[20, 20], [W - 20, H - 20]], { type: 'MultiPoint', coordinates: [[w, s], [e, s], [e, n], [w, n], [(w + e) / 2, s], [(w + e) / 2, n], [w, (s + n) / 2], [e, (s + n) / 2]] });
    if (!LAND_FLAT[r]) p.clipExtent([[-10, -10], [W + 10, H + 10]]);   // Weltküsten auf den Ausschnitt begrenzen
    return p;
  }
  var SEA_LABELS = {
    rom: [['Atlantischer Ozean', -9.5, 46.8, -35], ['Mittelmeer („Mare Nostrum“)', 17, 34.2, 0], ['Schwarzes Meer', 34.2, 43.2, 0], ['Nordsee', 3.5, 55, 0]],
    han: [['Gelbes Meer', 123.3, 35.3, 80], ['Südchinesisches Meer', 114.5, 15.2, 0], ['Gobi', 104, 44.4, 0], ['Taklamakan', 82.5, 38.6, 0], ['Tibet', 90, 31, 0]]
  };
  var NEIGH = {
    rom: [['Germanen', 11, 53.6, -113, null, null]],
    han: []
  };

  var closeTimer = null;
  function finishClose() {
    clearTimeout(closeTimer); closeTimer = null;
    $('#mapOverlay').classList.remove('show'); $('#mapOverlay').setAttribute('aria-hidden', 'true');
    mapOpen = false; mapReich = null; mapPrev = null; FENSTER.rolle = null;
    globe.controls().autoRotate = state.rotate;
    var pov = globe.pointOfView(); globe.pointOfView({ lat: pov.lat, lng: pov.lng, altitude: 0.9 }, 600);
  }
  /* Schriftrolle eines Reichs: Reiter „Vignetten“ (Rom: „Wiederholung“) und „Karte“ */
  function setRollView(v) {
    rollView = v;
    if (FENSTER.rolle && FENSTER.rolle.reiter !== v) { FENSTER.rolle.reiter = v; zustandGemeldet(); }
    var vig = v === 'vig';
    $('#vigView').classList.toggle('on', vig); $('#mapView').classList.toggle('on', !vig);
    $('#vigView').setAttribute('aria-hidden', !vig); $('#mapView').setAttribute('aria-hidden', vig);
    $('#tabVig').setAttribute('aria-selected', vig); $('#tabKarte').setAttribute('aria-selected', !vig);
    $('#tabVig').classList.toggle('on', vig); $('#tabKarte').classList.toggle('on', !vig);
    $('#scroll').classList.toggle('vigmode', vig);
    if (!vig && mapOpen) drawMap(mapReich, false);
  }
  function renderVignetten(r) {
    var m = M(r);
    $('#tabVig').textContent = Vignetten.modus(VIG, r) === 'wiederholung' ? 'Wiederholung' : 'Vignetten';
    Vignetten.render($('#vigView'), VIG, { reich: r, name: m.name, farbe: m.farbe });
  }
  function openMap(r, view) {
    if (!darfLokal('reiche')) return;
    if (closeTimer) finishClose();
    if (mapOpen) return;
    if (!hatRolle(r)) return;
    mapOpen = true; mapReich = r; mapPrev = null;
    FENSTER.rolle = { reich: r, reiter: view || 'vig', vignette: 'liste' };
    globe.controls().autoRotate = false;
    var ov = $('#mapOverlay'); ov.classList.add('show'); ov.setAttribute('aria-hidden', 'false');
    Vignetten.zuruecksetzen(r); renderVignetten(r); $('#vigView').scrollTop = 0;
    setRollView(view || 'vig');
    drawMap(r, false);
    var sc = $('#scroll'); sc.classList.remove('open');
    void sc.offsetWidth;
    requestAnimationFrame(function () { requestAnimationFrame(function () { sc.classList.add('open'); }); });
    $('#mapClose').focus({ preventScroll: true });
    zustandGemeldet();
  }
  function closeMap() {
    if (!mapOpen) return;
    FENSTER.rolle = null; zustandGemeldet();
    var sc = $('#scroll'); sc.classList.remove('open');
    closeTimer = setTimeout(finishClose, 1550);
  }

  function drawMap(r, soft) {
    var svg = d3.select('#flat'), y = state.year;
    var ev = activeEvent(r, y), own = regionsAt(r, y);
    var proj = makeProj(r), path = d3.geoPath(proj);
    svg.selectAll('*').remove();
    var defs = svg.append('defs');
    var pat = defs.append('pattern').attr('id', 'hatch').attr('patternUnits', 'userSpaceOnUse').attr('width', 8).attr('height', 8).attr('patternTransform', 'rotate(45)');
    pat.append('rect').attr('width', 8).attr('height', 8).attr('fill', 'rgba(240,205,110,0.38)');
    pat.append('line').attr('x1', 0).attr('y1', 0).attr('x2', 0).attr('y2', 8).attr('stroke', '#9a6b00').attr('stroke-width', 2);
    var g = defs.append('radialGradient').attr('id', 'sea').attr('cx', '50%').attr('cy', '50%').attr('r', '75%');
    g.append('stop').attr('offset', '0%').attr('stop-color', '#d6e3e1'); g.append('stop').attr('offset', '100%').attr('stop-color', '#b9cfd3');
    var f = defs.append('filter').attr('id', 'paper').attr('x', '0').attr('y', '0').attr('width', '100%').attr('height', '100%');
    f.append('feTurbulence').attr('type', 'fractalNoise').attr('baseFrequency', '0.9').attr('numOctaves', '2').attr('seed', '4').attr('result', 'n');
    f.append('feColorMatrix').attr('in', 'n').attr('type', 'matrix').attr('values', '0 0 0 0 0.35  0 0 0 0 0.27  0 0 0 0 0.12  0 0 0 0.55 0');

    svg.append('rect').attr('width', W).attr('height', H).attr('fill', 'url(#sea)');
    svg.append('path').attr('d', path(d3.geoGraticule().step([10, 10])())).attr('fill', 'none').attr('stroke', 'rgba(70,90,95,.28)').attr('stroke-width', 0.7);
    svg.append('path').attr('d', path(LAND_FLAT[r] || LAND)).attr('fill', '#efe3c2').attr('stroke', '#8d7b57').attr('stroke-width', 1.1).attr('stroke-linejoin', 'round');

    // Regionen: eigene + eingeblendete Nachbarn
    var feats = [];
    DATA.reihen.forEach(function (k) { if (k === r || state.on[k]) feats.push.apply(feats, regionsAt(k, y)); });
    var nowIds = {}, inView = {};
    feats.forEach(function (ft) {
      nowIds[ft.properties.id] = ft;
      var bb = path.bounds(ft);
      if (bb[1][0] > 0 && bb[0][0] < W && bb[1][1] > 0 && bb[0][1] < H) inView[ft.properties.reich] = 1;
    });
    function fillOf(ft) {
      var p = ft.properties, c = regionColor(ft, y);
      if (p.art === 'einfluss') return p.reich === 'han' ? 'url(#hatch)' : rgba(c, 0.25);
      return rgba(c, p.reich === r ? 0.74 : 0.5);
    }
    var layer = svg.append('g').attr('stroke-linejoin', 'round');
    feats.forEach(function (ft) {
      var p = ft.properties, c = regionColor(ft, y), mine = p.reich === r;
      var rp = layer.append('path').attr('d', path(ft)).attr('fill', fillOf(ft))
        .attr('stroke', mix(c, '#000000', 0.45)).attr('stroke-width', mine ? 1.3 : 0.9)
        .attr('stroke-dasharray', p.art === 'einfluss' || !mine ? '4 3' : null);
      rp.append('title').text(p.name + ' (' + (M(p.reich).name) + ', seit ' + fmtYear(p.von) + ')');
      if (soft && mapPrev && !mapPrev[p.id]) {
        rp.attr('opacity', 0).attr('stroke', '#fff').attr('stroke-width', 3)
          .transition().duration(900).attr('opacity', 1)
          .transition().duration(700).attr('stroke', mix(c, '#000000', 0.45)).attr('stroke-width', mine ? 1.3 : 0.9);
      }
    });
    // Verlorene Gebiete ausblenden
    if (soft && mapPrev) Object.keys(mapPrev).forEach(function (id) {
      if (nowIds[id]) return;
      var ft = mapPrev[id];
      layer.append('path').attr('d', path(ft)).attr('fill', fillOf(ft)).attr('stroke', '#3b2d14').attr('stroke-dasharray', '3 3')
        .attr('opacity', 1).transition().duration(1100).attr('opacity', 0).remove();
    });
    mapPrev = nowIds;

    // Teilungslinie 395
    var tg = svg.append('g').attr('font-family', 'Georgia, serif').attr('text-anchor', 'middle');
    function label(txt, lon, lat, rot, size, style, col) {
      var xy = proj([lon, lat]); if (!xy) return;
      tg.append('text').attr('x', xy[0]).attr('y', xy[1]).attr('transform', rot ? 'rotate(' + rot + ' ' + xy[0] + ' ' + xy[1] + ')' : null)
        .attr('font-size', size).attr('font-style', style).attr('fill', col).attr('stroke', 'rgba(239,227,194,.85)').attr('stroke-width', 3).attr('paint-order', 'stroke')
        .attr('letter-spacing', style === 'italic' ? 2 : 0).text(txt);
    }
    if (r === 'rom' && y >= TEILUNG && own.length) {
      label('WESTROM', 2, 45.5, 0, 22, 'normal', '#5e1612');
      label('OSTROM', 34, 39, 0, 22, 'normal', '#4a1f63');
    }
    (SEA_LABELS[r] || []).forEach(function (l) { label(l[0], l[1], l[2], l[3] ? -l[3] / 4 : 0, 17, 'italic', '#3f6b78'); });
    (NEIGH[r] || []).forEach(function (n) { label(n[0], n[1], n[2], 0, 18, 'italic', '#6b5a3a'); });
    // Namen eingeblendeter Nachbarreiche
    DATA.reihen.forEach(function (k) {
      if (k === r || !inView[k]) return;
      var z = M(k).zentrum; label(M(k).name, z[0], z[1], 0, 18, 'italic', mix(M(k).farbe, '#000000', 0.5));
    });
    // Städte
    var cg = svg.append('g').attr('font-family', 'Georgia, serif');
    var seen = {}; mapCityNames = {}; mapCityBoxes = [];
    DATA.orte.slice().sort(function (a, b) { return a.stufe - b.stufe; }).forEach(function (o) {   // größere Orte zuerst
      if (o.reich !== r && !state.on[o.reich]) return;
      if (!regionsAt(o.reich, y).length || seen[o.name] || !ortAktiv(o, y)) return;
      if (o.stufe >= 3 && o.reich !== r) return;   // Nachbarn: nur größere Orte
      var xy = proj([o.lng, o.lat]); if (!xy || xy[0] < 0 || xy[0] > W || xy[1] < 0 || xy[1] > H) return;
      var fs = [0, 18, 15, 13, 12][o.stufe], ctx = cg.append('text').attr('x', xy[0] + 9).attr('y', xy[1] + 5).attr('font-size', fs).attr('fill', '#2b2110')
        .attr('stroke', 'rgba(239,227,194,.9)').attr('stroke-width', 3.5).attr('paint-order', 'stroke').attr('font-weight', o.stufe >= 3 ? 400 : o.stufe === 1 ? 700 : 600).text(o.name);
      var bx = [xy[0] - 7, xy[1] - fs + 4, 18 + ctx.node().getComputedTextLength(), fs + 7];
      var stoss = mapCityBoxes.some(function (q) { return bx[0] < q[0] + q[2] && bx[0] + bx[2] > q[0] && bx[1] < q[1] + q[3] && bx[1] + bx[3] > q[1]; });
      if (stoss && o.stufe > 1) { ctx.remove(); return; }   // kein Platz: kleineren Ort weglassen
      seen[o.name] = 1; mapCityNames[o.name] = 1;
      cg.insert('circle', 'text').attr('cx', xy[0]).attr('cy', xy[1]).attr('r', [0, 5.5, 4, 3, 2.5][o.stufe]).attr('fill', '#2b2110').attr('stroke', '#f5ecd2').attr('stroke-width', 1.5);
      mapCityBoxes.push(bx);
    });
    // Handelswege
    var tradeOnMap = drawTrade(svg, proj, path, r);
    // Schlachten
    var bg = svg.append('g').attr('font-family', 'Georgia, serif');
    var bats = visibleBattles(y);
    bats.forEach(function (b) {
      var xy = proj([b.lng, b.lat]); if (!xy || xy[0] < 0 || xy[0] > W || xy[1] < 0 || xy[1] > H) return;
      var gg = bg.append('g').attr('transform', 'translate(' + xy[0] + ',' + xy[1] + ')').attr('class', 'mbattle');
      gg.append('circle').attr('r', 15).attr('fill', '#7a1d12').attr('stroke', '#f5ecd2').attr('stroke-width', 2);
      var sw = gg.append('g').attr('transform', 'translate(-10,-10) scale(0.84)').attr('fill', 'none').attr('stroke', '#fff').attr('stroke-width', 2.4).attr('stroke-linecap', 'round');
      SWORD_PATHS.forEach(function (d) { sw.append('path').attr('d', d); });
      gg.append('text').attr('x', 20).attr('y', 5).attr('font-size', 15).attr('font-style', 'italic').attr('font-weight', 700).attr('fill', '#5a140c')
        .attr('stroke', 'rgba(239,227,194,.92)').attr('stroke-width', 3.5).attr('paint-order', 'stroke').text(b.name + ' ' + shortYear(b.jahr));
      gg.append('title').text(b.name + ' (' + fmtYear(b.jahr) + '): ' + b.note);
      if (y - b.jahr <= 4) gg.select('circle').attr('r', 4).transition().duration(600).attr('r', 15);
    });
    // Nordpfeil
    var na = svg.append('g').attr('transform', 'translate(' + (W - 78) + ',150)');
    na.append('path').attr('d', 'M0,-34 L11,10 L0,2 L-11,10 Z').attr('fill', '#3b2d14');
    na.append('text').attr('y', 30).attr('text-anchor', 'middle').attr('font-family', 'Georgia, serif').attr('font-size', 17).attr('fill', '#3b2d14').text('N');
    // Papierkörnung
    svg.append('rect').attr('width', W).attr('height', H).attr('filter', 'url(#paper)').attr('opacity', 0.22).attr('pointer-events', 'none');

    // Kopf
    var ct = $('#cartouche'); ct.innerHTML = '';
    var t1 = document.createElement('div'); t1.className = 'ct';
    var haupt = r === 'rom' || r === 'han';
    t1.textContent = ev && haupt ? (r === 'rom' ? (y >= TEILUNG ? 'West- und Ostrom' : 'Das Römische Reich') : 'Das Reich der Han') : M(r).name;
    var t2 = document.createElement('div'); t2.className = 'cs';
    t2.textContent = ev ? ev.titel + ' · ' + fmtYear(y) : own.length ? fmtYear(y) : fmtYear(y) + ': besteht nicht (' + shortYear(M(r).von) + '–' + shortYear(M(r).bis) + ')';
    ct.appendChild(t1); ct.appendChild(t2);
    var note = ev ? ev.note : (!haupt ? M(r).kurz : '');
    if (note) { var p = document.createElement('p'); p.textContent = note; ct.appendChild(p); }
    // Legende
    var lg = $('#legend'); lg.innerHTML = '';
    function lgRow(bg, txt) {
      var d = document.createElement('div'), i = document.createElement('i'); i.style.background = bg;
      d.appendChild(i); d.appendChild(document.createTextNode(txt)); lg.appendChild(d);
    }
    if (r === 'rom' && y >= TEILUNG) { lgRow(rgba(M('rom').farbe, 0.74), 'Westrom'); lgRow(rgba(OSTROM, 0.74), 'Ostrom'); }
    else lgRow(rgba(M(r).farbe, 0.74), M(r).name + ' (vereinfacht)');
    if (own.some(function (x) { return x.properties.art === 'einfluss'; })) {
      if (r === 'han') lgRow('repeating-linear-gradient(45deg,#e9c55f,#e9c55f 3px,#9a6b00 3px,#9a6b00 4px)', 'Einflussbereich (Westliche Regionen)');
      else lgRow(rgba(M(r).farbe, 0.25), 'Einflussbereich');
    }
    DATA.reihen.forEach(function (k) { if (k !== r && inView[k]) lgRow(rgba(M(k).farbe, 0.5), M(k).name); });
    if (tradeOnMap) {
      var tl = document.createElement('div'); tl.className = 'lg-trade';
      tl.innerHTML = '<span><svg viewBox="0 0 40 8"><line x1="2" y1="4" x2="38" y2="4" stroke="#8a4b12"/></svg>Landweg</span>' +
        '<span><svg viewBox="0 0 40 8"><line x1="2" y1="4" x2="38" y2="4" stroke="#155f86"/></svg>Seeweg</span><br>' +
        '<span><svg viewBox="0 0 40 8"><line x1="2" y1="4" x2="38" y2="4"/></svg>belegt</span>' +
        '<span><svg viewBox="0 0 40 8"><line x1="2" y1="4" x2="38" y2="4" stroke-dasharray="8 5"/></svg>vermittelt</span>' +
        '<span><svg viewBox="0 0 40 8"><line x1="3" y1="4" x2="38" y2="4" stroke-dasharray="0.1 6" stroke-linecap="round" stroke-width="3.4"/></svg>umstritten</span>';
      lg.appendChild(tl);
    }
    if (bats.length) {
      var d = document.createElement('div'); d.innerHTML = '<span class="lsw">' + SWORDS + '</span>'; d.appendChild(document.createTextNode('Schlacht')); lg.appendChild(d);
    }
    // Ereignis-Leiste
    var sb = $('#stagebar'); sb.innerHTML = '';
    (EVENTS[r] || []).forEach(function (st) {
      var b = document.createElement('button'); b.type = 'button'; b.textContent = shortYear(st.jahr);
      b.title = st.titel;
      if (ev && ev.jahr === st.jahr) b.className = 'on';
      b.addEventListener('click', function () { setYear(st.jahr); });
      sb.appendChild(b);
    });
  }

  /* ---------- Handel & Austausch ---------- */
  var TRADE_COL = { land: '#ffcf6b', see: '#5fd8ff' };           // Globus Satellit (dunkler Hintergrund)
  var TRADE_SCHEM = { land: '#6b3206', see: '#0a3f66' };         // Globus schematisch (helle Textur)
  function tradeCol(art) { return (state.mode === 'schem' ? TRADE_SCHEM : TRADE_COL)[art]; }
  var TRADE_MAP = { land: '#8a4b12', see: '#155f86' };           // Pergament (heller Hintergrund)
  var DASH_GLOBE = { belegt: [1, 0], vermittelt: [0.035, 0.018], umstritten: [0.006, 0.012] };
  var DASH_MAP = { belegt: null, vermittelt: '12 7', umstritten: '1 7' };
  var BELEGT_TXT = { belegt: 'belegt', vermittelt: 'vermittelt (Zwischenhandel)', umstritten: 'umstritten' };
  var TEIL_TXT = { rom: 'Römische Seite', mitte: 'Mittelstück (Vermittler)', han: 'Chinesische Seite', ganz: 'Gesamte Strecke', spaet: 'Gesamte Strecke, schwächer (Etappenhandel)' };
  var EMPTY_TV = { routes: [], parts: [], places: [], kontakte: [], kar: { list: [], key: '' }, key: '' }, CUR_ZV = null;
  var KONTAKT_JAHRE = 20;
  var ENVOY = '<svg viewBox="0 0 24 24" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
    '<path d="M6 4h10a2 2 0 0 1 2 2v13a2 2 0 0 0 2-2V8"/><path d="M6 4a2 2 0 0 0-2 2v1h4V6a2 2 0 0 0-2-2z"/><path d="M8 7v12a2 2 0 0 0 2 2h10"/><path d="M11 10h4M11 14h4"/></g></svg>';
  var HANDEL = null, PARTS = {}, WTAGS = {}, CUR_TV = null, mapCityNames = {}, mapCityBoxes = [];

  function initTrade() {
    HANDEL.verbindungen.forEach(function (v) {
      var n = v.pfad.length, s = v.seiten;
      function mk(teil, a, b, belegt, quelle) {
        var p = { id: v.id + ':' + teil, route: v, teil: teil, pts: v.pfad.slice(a, b + 1), belegt: belegt || v.belegt, quelle: quelle || v.quelle };
        p.flowObj = { id: p.id + ':flow', route: v, teil: teil, pts: p.pts, flow: true };
        return p;
      }
      PARTS[v.id] = s
        ? { rom: mk('rom', 0, s.rom.bis_punkt, s.rom.belegt, s.rom.quelle), mitte: mk('mitte', s.rom.bis_punkt, s.han.ab_punkt), han: mk('han', s.han.ab_punkt, n - 1, s.han.belegt, s.han.quelle) }
        : { ganz: mk('ganz', 0, n - 1) };
      // Ab dem Wendepunkt: durchgehende Strecke, aber schwächer (vermittelt)
      if (HANDEL.karawanen && HANDEL.karawanen.route === v.id) PARTS[v.id].spaet = mk('spaet', 0, n - 1, 'vermittelt', HANDEL.karawanen.quelle);
    });
    if (HANDEL.karawanen) initKarawanen();
    HANDEL.orte.forEach(function (o) { o.kind = 'handel'; });
    HANDEL.kontakte.forEach(function (k) {
      k.kind = 'kontakt';
      if (k.pfad) k.pathObj = { id: 'k:' + k.id, kontakt: k, pts: k.pfad };
    });
  }
  function routeById(id) { return HANDEL.verbindungen.filter(function (x) { return x.id === id; })[0]; }
  function reichAktiv(r, y) { return !!DATA.meta[r] && !!state.on[r] && exists(r, y); }
  function seiteAktiv(v, side, y) {
    var s = v.seiten[side];
    return reichAktiv(side, y) && y >= (s.von != null ? s.von : v.von) && y <= (s.bis != null ? s.bis : v.bis);
  }
  /* Sichtbare Teilstrecken, Orte, Gesandtschaften. Regel: Reich eingeblendet UND existiert im Jahr.
     Nur ein Reich aktiv -> nur dessen Seite (bis zu den Vermittlern); beide aktiv -> durchgehende Verbindung. */
  function tradeVisible(y) {
    var res = { routes: [], parts: [], places: [], kontakte: [], kar: { list: [], key: 'aus' }, schiff: [], key: 'aus' };
    if (!TRADE.on) return res;
    var K = HANDEL.karawanen;
    HANDEL.verbindungen.forEach(function (v) {
      if (y < v.von || y > v.bis) return;
      if (v.art === 'land' ? !TRADE.land : !TRADE.see) return;
      var P = PARTS[v.id], t = {};
      if (P.ganz) { if (v.reiche.some(function (r) { return reichAktiv(r, y); })) t.ganz = 1; }
      else if (P.spaet && y >= K.ab) { if (v.reiche.some(function (r) { return reichAktiv(r, y); })) t.spaet = 1; }
      else {
        var a = seiteAktiv(v, 'rom', y), b = seiteAktiv(v, 'han', y);
        if (a) t.rom = 1; if (b) t.han = 1; if (a && b) t.mitte = 1;
      }
      var teile = ['rom', 'mitte', 'han', 'ganz', 'spaet'].filter(function (k) { return t[k]; });
      if (!teile.length) return;
      var parts = teile.map(function (k) { return P[k]; });
      res.routes.push({ v: v, teile: t, parts: parts });
      res.parts.push.apply(res.parts, parts);
    });
    var seen = {};
    HANDEL.orte.forEach(function (o) {
      if (y < o.von || y > o.bis || seen[o.id]) return;
      var ok = o.an.some(function (a) { return res.routes.some(function (rt) { return rt.v.id === a[0] && (rt.teile[a[1]] || rt.teile.spaet); }); });
      if (ok) { seen[o.id] = 1; res.places.push(o); }
    });
    if (TRADE.gesandt) HANDEL.kontakte.forEach(function (k) {
      if (y >= k.jahr && y <= k.jahr + KONTAKT_JAHRE && k.reiche.some(function (r) { return reichAktiv(r, y); })) res.kontakte.push(k);
    });
    res.kar = karPlan(y, res);
    res.strassen = strassenSichtbar(y);
    res.schiff = orbisSichtbar(y);
    res.hanseide = hanSeideAn(y) ? (y <= 8 ? 'w' : y >= 25 ? 'o' : 'x') + hanStationen(y).length : '';
    res.strKey = strassenSchluessel(y);
    res.key = [TRADE.land, TRADE.see, TRADE.waren, TRADE.gesandt, TRADE.karawanen, res.strassen].join('') + '|' + res.hanseide + '|' + res.schiff.map(function (d) { return d.n; }).join('.') + '|' +
      res.parts.map(function (p) { return p.id; }).join(',') + '|' + res.places.map(function (o) { return o.id; }).join(',') + '|' +
      res.kontakte.map(function (k) { return k.id; }).join(',') + '|' + res.kar.key;
    return res;
  }
  function joinPts(parts) { return parts.reduce(function (a, p) { return a.concat(a.length ? p.pts.slice(1) : p.pts); }, []); }
  function wareTags(tv) {
    if (!TRADE.waren) return [];
    return tv.routes.map(function (rt) {
      var key = rt.v.id + ':' + Object.keys(rt.teile).join('');
      if (!WTAGS[key]) {
        // Ankerpunkt auf der Mitte der sichtbaren Strecke; die Box hängt per Stiel darüber (Landweg) bzw. darunter (Seeweg)
        var pts = dense(joinPts(rt.parts)), mid = pts[Math.floor(pts.length / 2)];
        WTAGS[key] = { kind: 'waren', route: rt.v, lng: mid[0], lat: mid[1], seite: rt.v.art === 'land' ? 'oben' : 'unten', pts: pts.filter(function (x, j) { return j % 2 === 0; }) };
      }
      return WTAGS[key];
    });
  }
  function dense(coords) {
    var out = [coords[0]];
    for (var i = 1; i < coords.length; i++) {
      var a = coords[i - 1], b = coords[i], n = Math.max(1, Math.ceil(d3.geoDistance(a, b) * 180 / Math.PI / 0.75)), ip = d3.geoInterpolate(a, b);
      for (var j = 1; j <= n; j++) out.push(ip(j / n));
    }
    return out;
  }
  function fmtRange(a, b) { return b >= ANTIKE_ENDE && a < ANTIKE_ENDE ? 'ab ' + fmtYear(a) : fmtYear(a) + ' bis ' + fmtYear(b); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function wareChip(w) {
    var ow = w.von_nach === 'ost->west', c = el('span', 'wchip ' + (ow ? 'ow' : 'wo'), ow ? '← ' + w.name : w.name + ' →');
    c.title = w.name + ': ' + (ow ? 'von Osten nach Westen' : 'von Westen nach Osten');
    return c;
  }
  function badge(b) { return el('span', 'tbadge ' + b, BELEGT_TXT[b] || b); }

  /* Globus-Elemente */
  function kontaktEl(k) {
    if (k.__el) return k.__el;
    var e = el('div', 'envoy'); e.innerHTML = ENVOY; e.appendChild(el('span', null, k.name + ' ' + shortYear(k.jahr)));
    e.title = k.name + ' (' + fmtYear(k.jahr) + ')';
    e.addEventListener('click', function (ev) { ev.stopPropagation(); openKontaktInfo(k); });
    k.__el = e; return e;
  }
  function warenEl(t) {
    if (t.__el) return t.__el;
    // Nullgroßer Anker; die Box sitzt darüber (Landweg) bzw. darunter (Seeweg), damit die Route frei bleibt
    var anchor = el('div', 'wanchor ' + t.seite);
    var e = el('div', 'wtag');
    t.route.richtung_waren.forEach(function (w) { e.appendChild(wareChip(w)); });
    e.title = 'Waren: ' + t.route.name + ' (Klick für Infos)';
    e.addEventListener('click', function (ev) { ev.stopPropagation(); if (t.route.nr) openZhInfo(t.route); else openTradeInfo(t.route); });
    anchor.appendChild(el('i', 'wstem')); anchor.appendChild(e);
    t.__el = anchor; return anchor;
  }
  /* Waren-Boxen: nach oben oder unten klappen, je nachdem wo auf dem Bildschirm Platz ist */
  var tagSideRaf = 0;
  function updateTagSides() {
    tagSideRaf = 0;
    var tags = Object.keys(WTAGS).map(function (k) { return WTAGS[k]; }).filter(function (t) { return t.__el && t.__el.isConnected; });
    if (!tags.length) return;
    var top = 70, bottom = window.innerHeight - (document.getElementById('timeline').offsetHeight || 180) - 24, Wd = window.innerWidth, STEM = 64;
    var pov = globe.pointOfView();
    // Bildschirmpunkte aller sichtbaren Routen (nur Vorderseite des Globus)
    var scr = [];
    (CUR_TV ? CUR_TV.parts : []).forEach(function (p) {
      dense(p.pts).forEach(function (c, j) {
        if (j % 2 || d3.geoDistance([pov.lng, pov.lat], c) > 1.45) return;
        var q = globe.getScreenCoords(c[1], c[0], 0.0012); scr.push([q.x, q.y]);
      });
    });
    var placed = [];
    ['#panel', '#side'].forEach(function (id) {   // offene Menüs wie belegte Flächen behandeln
      var e = $(id); if (!e || e.classList.contains('collapsed') || getComputedStyle(e).visibility === 'hidden') return;
      var r = e.getBoundingClientRect(); placed.push([r.left, r.top, r.width, r.height]);
    });
    tags.forEach(function (t) {
      var sc = globe.getScreenCoords(t.lat, t.lng, 0.0015), box = t.__el.querySelector('.wtag'), w = box.offsetWidth, h = box.offsetHeight;
      var cand = {
        oben: [sc.x - w / 2, sc.y - STEM - h, w, h], unten: [sc.x - w / 2, sc.y + STEM, w, h],
        links: [sc.x - STEM - w, sc.y - h / 2, w, h], rechts: [sc.x + STEM, sc.y - h / 2, w, h]
      };
      var best = null, bestScore = 1e9;
      ['oben', 'unten', 'links', 'rechts'].forEach(function (k, i) {
        var r = cand[k], score = (k === t.seite ? 0 : 0.5) + i * 0.01;
        if (r[0] < 8 || r[0] + r[2] > Wd - 8 || r[1] < top || r[1] + r[3] > bottom) score += 1000;
        scr.forEach(function (q) { if (q[0] > r[0] - 6 && q[0] < r[0] + r[2] + 6 && q[1] > r[1] - 6 && q[1] < r[1] + r[3] + 6) score += 3; });
        placed.forEach(function (o) {
          var ow = Math.min(r[0] + r[2], o[0] + o[2]) - Math.max(r[0], o[0]), oh = Math.min(r[1] + r[3], o[1] + o[3]) - Math.max(r[1], o[1]);
          if (ow > 0 && oh > 0) score += 200;
        });
        if (score < bestScore) { bestScore = score; best = k; }
      });
      placed.push(cand[best]);
      ['oben', 'unten', 'links', 'rechts'].forEach(function (k) { t.__el.classList.toggle(k, k === best); });
    });
  }
  function scheduleTagSides() { if (!tagSideRaf) tagSideRaf = requestAnimationFrame(updateTagSides); }
  function ortEl(d) {
    if (d.__el) return d.__el;
    var e = el('div', 'ort st' + d.stufe); e.style.setProperty('--c', mix(M(d.reich).farbe, '#ffffff', 0.78));
    e.appendChild(el('i')); e.appendChild(el('span', null, d.name));
    d.__el = e; return e;
  }
  /* Völkerwanderung: Züge wachsen mit der Zeitleiste (von/bis), Schild am Zugende solange der Zug läuft */
  /* ---------- Völkerwanderung (data/reiche.json → wanderungen) ----------
     Jeder Zug ist ein leuchtender Strom: breites Glühband, kräftige Kernlinie und fließende Partikel. An der Front sitzt
     eine Pfeilspitze, die auf dem Bildschirm in Zugrichtung zeigt, mit dem Namen des Volkes. Am Ziel pulsiert einige
     Jahre ein Ankunfts-Ring; abgeschlossene Züge bleiben eine Weile als blasse Spur. Wege sind schematisch. */
  var VW_FARBE = { 'Hunnen': '#ff5a36', 'Westgoten': '#b06bff', 'Ostgoten': '#7fe35a', 'Vandalen': '#3aa0ff', 'Sueben': '#21d4c4',
    'Burgunder': '#ff4fa3', 'Alamannen': '#ffc233', 'Angeln, Sachsen, Jüten': '#3ee08a' };
  var VW_SPUR = 40, VW_ANKUNFT = 6;   // Jahre: Spur nach dem Ende; Ankunfts-Ring
  function vwFarbe(w) { return VW_FARBE[w.volk] || w.farbe; }
  function vwAnteil(w, y) { return y < w.von ? -1 : Math.min(1, (y - w.von + 1) / (w.bis - w.von + 1)); }
  function vwSichtbar(w, y) { return vwAnteil(w, y) > 0 && y <= w.bis + VW_SPUR; }
  function vwVorbereiten(w, i) {
    w.__p = { id: 'vw' + i, vw: w, pts: w.pfad };
    w.__band = { id: 'vwb' + i, vw: w, vwArt: 'band', pts: w.pfad };
    w.__fluss = { id: 'vwf' + i, vw: w, vwArt: 'fluss', pts: w.pfad };
    w.__schatten = { id: 'vws' + i, vw: w, vwArt: 'schatten', pts: w.pfad };   // dunkle Kontur: hebt den Strom von den Reichsflächen ab
    w.__tag = { kind: 'vw', w: w };
  }
  function vwPaths() {
    if (!state.vw || state.epoche !== 'antike') return [];
    var y = state.year, out = [];
    (DATA.wanderungen || []).forEach(function (w) {
      if (!vwSichtbar(w, y)) return;
      var pts = schnitt(w.__lauf, vwAnteil(w, y)), laeuft = y <= w.bis;
      w.__band.pts = w.__schatten.pts = w.__p.pts = w.__fluss.pts = pts;
      w.__laeuft = laeuft;
      out.push(w.__band, w.__schatten, w.__p);
      if (laeuft) out.push(w.__fluss);
    });
    return out;
  }
  /* Schlüssel des sichtbaren Zustands: ändert sich, wenn ein Zug wächst, ankommt oder verblasst */
  function vwSchluessel(y) {
    if (!state.vw || state.epoche !== 'antike') return 'aus';
    return (DATA.wanderungen || []).map(function (w) {
      return vwSichtbar(w, y) ? Math.round(vwAnteil(w, y) * 100) + (y <= w.bis ? 'l' : y <= w.bis + VW_ANKUNFT ? 'a' : 's') : '-';
    }).join(',');
  }
  function vwTags() {
    if (!state.vw || state.epoche !== 'antike') return [];
    var y = state.year;
    var je = {};   // je Volk ein Kopf: am jüngsten Zug, solange er läuft und bis zum Ende des Ankunfts-Rings
    (DATA.wanderungen || []).forEach(function (w) { if (y >= w.von && y <= w.bis + VW_ANKUNFT && (!je[w.volk] || w.von > je[w.volk].von)) je[w.volk] = w; });
    return Object.keys(je).map(function (k) {
      var w = je[k], f = vwAnteil(w, y), t = punktBei(w.__lauf, f);
      w.__tag.lng = t[0]; w.__tag.lat = t[1]; w.__tag.f = f; w.__tag.angekommen = y > w.bis;
      if (w.__tag.__el) w.__tag.__el.classList.toggle('da', y > w.bis);
      return w.__tag;
    });
  }
  function vwEl(d) {
    if (d.__el) return d.__el;
    var w = d.w, c = vwFarbe(w), e = el('div', 'vwkopf'); e.style.setProperty('--c', c);
    e.appendChild(el('span', 'vw-ring'));
    var pf = el('span', 'vw-pfeil'); pf.innerHTML = '<svg viewBox="0 0 40 40" aria-hidden="true"><path d="M6 20 L34 20 M22 8 L34 20 L22 32" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    e.appendChild(pf);
    var b = el('button', 'vw-schild'); b.type = 'button';
    b.appendChild(el('b', null, w.volk)); b.appendChild(el('span', null, shortYear(w.von) + '–' + shortYear(w.bis)));
    b.title = w.text + ' (Weg schematisch)';
    b.addEventListener('click', function (ev) { ev.stopPropagation(); toast(w.volk + ' (' + fmtYear(w.von) + ' bis ' + fmtYear(w.bis) + '): ' + w.text + ' · Weg schematisch'); });
    e.appendChild(b);
    d.__el = e; e.classList.toggle('da', !!d.angekommen); return e;
  }
  /* Pfeilspitzen in Zugrichtung drehen (Bildschirmrichtung hängt von der Kamera ab) */
  var VW_DREH = 0;
  function vwDrehen() {
    VW_DREH = 0;
    if (!state.vw || state.epoche !== 'antike' || !globe) return;
    vwTags().forEach(function (d) {
      if (!d.__el) return;
      var w = d.w, f = Math.max(0.02, d.f), a = punktBei(w.__lauf, Math.max(0, f - 0.03)), b = punktBei(w.__lauf, f);
      var pa = globe.getScreenCoords(a[1], a[0], 0.002), pb = globe.getScreenCoords(b[1], b[0], 0.002);
      if (!pa || !pb || (Math.abs(pb.x - pa.x) + Math.abs(pb.y - pa.y)) < 0.5) return;
      d.__el.style.setProperty('--rot', Math.atan2(pb.y - pa.y, pb.x - pa.x) + 'rad');
    });
  }
  function vwDrehenBald() { if (!VW_DREH) VW_DREH = requestAnimationFrame(vwDrehen); }
  function htmlEl(d) { return d.zeiten ? ortEl(d) : d.kind === 'vw' ? vwEl(d) : d.kind === 'kastell' ? kastellEl(d) : d.kind === 'zhschiff' ? zhSchiffEl(d) : d.kind === 'europa' ? europaEl(d) : d.kind === 'standort' ? standortEl(d) : d.kind === 'zhflag' ? zhFlagEl(d) : d.kind === 'kontakt' ? kontaktEl(d) : d.kind === 'waren' ? warenEl(d) : battleEl(d); }

  /* ---------- Eigener Standort (Pin) ---------- */
  // Standard-Pin: Jena; wird durch den eigenen Standort ersetzt, sobald dieser aktiviert ist
  var JENA = { kind: 'standort', name: 'Jena', lat: 50.9271, lng: 11.5892 };
  var STANDORT = null;
  function standortEl(d) {
    if (d.__el) return d.__el;
    var e = document.createElement('div'); e.className = 'standort';
    e.innerHTML = '<svg viewBox="0 0 24 32" aria-hidden="true"><path d="M12 31C12 31 2 18.5 2 11.5a10 10 0 0 1 20 0C22 18.5 12 31 12 31z" fill="#e0262f" stroke="#fff" stroke-width="2"/><circle cx="12" cy="11.5" r="4" fill="#fff"/></svg><span></span>';
    e.querySelector('span').textContent = d.name;
    e.title = d === JENA ? 'Jena (Standard-Standort)' : 'Eigener Standort (wird nur im Browser verwendet)';
    e.addEventListener('click', function (ev) {
      ev.stopPropagation();
      toast('📍 ' + (d === JENA ? 'Jena' : 'Hier bist du') + ' (' + d.lat.toFixed(1) + '°, ' + d.lng.toFixed(1) + '°)');
    });
    d.__el = e; return e;
  }
  function setStandortBtn(on, busy) {
    var b = $('#tglStandort'); b.classList.toggle('on', on); b.setAttribute('aria-pressed', on); b.disabled = !!busy;
  }
  function toggleStandort() {
    if (STANDORT) { STANDORT = null; setStandortBtn(false); refreshGlobe(); return; }
    if (!navigator.geolocation) { toast('Standortbestimmung wird von diesem Browser nicht unterstützt.'); return; }
    setStandortBtn(false, true);
    navigator.geolocation.getCurrentPosition(function (pos) {
      STANDORT = { kind: 'standort', name: 'Mein Standort', lat: pos.coords.latitude, lng: pos.coords.longitude };
      setStandortBtn(true); refreshGlobe();
      if (!mapOpen) fly(STANDORT.lat, STANDORT.lng, Math.max(1.2, globe.pointOfView().altitude * 0.8));
    }, function (err) {
      setStandortBtn(false);
      toast(err.code === 1 ? 'Standortfreigabe wurde abgelehnt.' : 'Standort konnte nicht ermittelt werden.');
    }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 });
  }
  function tradeGlobePaths(tv) {
    var a = [];
    if (tv.strassen) a.push.apply(a, strassenPaths(state.year));
    if (tv.schiff) a.push.apply(a, tv.schiff);
    if (tv.hanseide) a.push.apply(a, HANSEIDE_LINIEN);
    tv.parts.forEach(function (p) { a.push(p, p.flowObj); });
    tv.kontakte.forEach(function (k) { if (k.pathObj) a.push(k.pathObj); });
    return a;
  }

  /* ---------- Layer „Schiffsverkehr (ORBIS)“: Küste, Hochsee, Fähren, Flüsse (data/orbis_schiff.json, build_orbis.py) ----------
     ORBIS hat keine Jahreszahlen. Eine Strecke erscheint in den Jahren, in denen beide Endhäfen römisch sind (Darstellungsregel). */
  var ORBIS = null, ORBIS_OBJ = [];
  var ORBIS_ART = { kueste: 'Küstenschifffahrt', hochsee: 'Hochseeroute', faehre: 'Fähre', fluss: 'Flussschifffahrt' };
  function initOrbis(d) {
    ORBIS = d && Array.isArray(d.routen) ? d : null;
    ORBIS_OBJ = ORBIS ? ORBIS.routen.map(function (r, i) { return { id: r.id, n: i, orbis: r, pts: r.p }; }) : [];
  }
  function orbisSichtbar(y) {
    if (!ORBIS || !TRADE.on || !TRADE.schiff || !state.on.rom || state.epoche !== 'antike') return [];
    return ORBIS_OBJ.filter(function (d) { return d.orbis.zeiten.some(function (z) { return y >= z[0] && y < z[1]; }); });
  }
  function orbisFarbe(d) {
    var a = d.orbis.art === 'fluss' ? 0.5 : 0.75;
    return state.mode === 'schem' ? 'rgba(10,63,102,' + a + ')' : 'rgba(150,215,255,' + a + ')';
  }
  function openOrbisInfo(d) {
    if (!darfLokal('routen')) return; INFO_NEU = { art: 'orbis', id: d ? d.id : null };
    showInfo(function (b) {
      b.appendChild(el('div', 'tk see', 'Schiffsverkehr (ORBIS)'));
      var h = el('h3', null, d ? d.orbis.von_ort + ' – ' + d.orbis.nach_ort : 'Schiffsverkehr im Römischen Reich'); h.id = 'tinfoTitle'; b.appendChild(h);
      if (d) row(b, 'Art', ORBIS_ART[d.orbis.art] || d.orbis.art);
      else row(b, 'Im Jahr ' + fmtYear(state.year), orbisSichtbar(state.year).length + ' von ' + ORBIS_OBJ.length + ' Strecken (Küste, Hochsee, Fähren, Flüsse)');
      row(b, 'Was gezeigt wird', 'Das Verkehrsnetz des ORBIS-Modells um 200 n. Chr.: Strecken, auf denen Schiffe Waren und Menschen transportierten, im Mittelmeer, am Atlantik bis Britannien und auf den großen Flüssen. Die Linien sind Modellstrecken, keine belegten einzelnen Fahrten.');
      row(b, 'Zeit', 'ORBIS enthält keine Jahreszahlen. Eine Strecke erscheint, solange beide Endhäfen im Tafelbild römisch sind. Das ist eine Darstellungsregel, kein Beleg für den Beginn des Verkehrs.').classList.add('twarn');
      row(b, 'Daten', 'ORBIS – The Stanford Geospatial Network Model of the Roman World (W. Scheidel, E. Meeks), orbis.stanford.edu; Daten aus github.com/emeeks/orbis_v2, vereinfacht mit build_orbis.py.');
      row(b, 'Lizenz', 'MIT (Repository emeeks/orbis_v2)');
    });
  }

  /* ---------- Grenzanlagen (Limes, Hadrianswall …; data/limes.json) ----------
     Eigene Signatur je Bauart über einer dunklen Kontur; Kastelle als Turm-Symbole. Sichtbar mit dem Römischen Reich,
     solange der Abschnitt in Gebrauch war. Verläufe schematisch. */
  var LIMES = null, LIMES_OBJ = [];
  var LIMES_ART = {
    mauer: { name: 'Steinmauer', farbe: '#f4e3b5', block: 5, luecke: 1.2 },
    wall: { name: 'Rasen- bzw. Erdwall', farbe: '#a8e07a', block: 4, luecke: 1.5 },
    palisade: { name: 'Palisade, Wall und Graben', farbe: '#ffb35c', block: 6, luecke: 2.2 },
    fluss: { name: 'Flussgrenze mit Kastellkette', farbe: '#7fd8ff', block: 18, luecke: 12 },
    strasse: { name: 'Grenzstraße mit Kastellen', farbe: '#ffd27a', block: 22, luecke: 9 },
    graben: { name: 'Graben und Wall', farbe: '#ff8f6b', block: 10, luecke: 5 }
  };
  function initLimes(d) {
    LIMES = d && Array.isArray(d.abschnitte) ? d : null; LIMES_OBJ = [];
    if (!LIMES) return;
    LIMES.abschnitte.forEach(function (a) {
      var km = Math.max(1, lauf(a.pfad).len * 6371);
      a.__dash = [Math.min(1, LIMES_ART[a.art].block / km), LIMES_ART[a.art].luecke / km];   // Muster in km, unabhängig von der Länge
      // Kernlinie etwas höher als die Kontur, damit sie sicher darüber liegt (dritter Wert = Höhe)
      LIMES_OBJ.push({ id: 'lim-' + a.id + '-r', limes: a, limTeil: 'rand', pts: a.pfad },
        { id: 'lim-' + a.id + '-k', limes: a, limTeil: 'kern', pts: a.pfad.map(function (q) { return [q[0], q[1], 0.0019]; }) });
    });
    LIMES.kastelle.forEach(function (k) { k.kind = 'kastell'; k.__a = LIMES.abschnitte.filter(function (a) { return a.id === k.abschnitt; })[0]; });
  }
  function limesAn(a, y) { return !!state.limes && !!state.on.rom && state.epoche === 'antike' && y >= a.von && y <= a.bis; }
  function limesPaths() { var y = state.year; return LIMES_OBJ.filter(function (o) { return limesAn(o.limes, y); }); }
  function limesKastelle() { var y = state.year; return LIMES ? LIMES.kastelle.filter(function (k) { return k.__a && limesAn(k.__a, y); }) : []; }
  function limesSchluessel(y) { return !state.limes ? '' : (LIMES ? LIMES.abschnitte.filter(function (a) { return limesAn(a, y); }).map(function (a) { return a.id; }).join('.') : ''); }
  var TURM = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 21V9h2V6h2v3h2V6h2v3h2V6h2v3h2v12h-5v-5a2 2 0 0 0-4 0v5z" fill="currentColor" stroke="#2a1608" stroke-width="1.4" stroke-linejoin="round"/></svg>';
  function kastellEl(d) {
    if (d.__el) return d.__el;
    var e = el('button', 'kastell'); e.type = 'button'; e.innerHTML = TURM; e.style.setProperty('--c', LIMES_ART[d.__a.art].farbe);
    e.title = d.name + ' · ' + d.__a.name + ' (Klick für Infos)';
    e.setAttribute('aria-label', d.name + ': Infokarte öffnen');
    e.addEventListener('click', function (ev) { ev.stopPropagation(); openLimes(d.__a, d); });
    d.__el = e; return e;
  }
  function openLimes(a, k) {
    if (!darfLokal('routen')) return; INFO_NEU = { art: 'limes', id: a.id, kastell: k ? k.name : null };
    showInfo(function (b) {
      b.appendChild(el('div', 'tk limes', 'Römische Grenzanlage · ' + LIMES_ART[a.art].name));
      var h = el('h3', null, k ? k.name : a.name); h.id = 'tinfoTitle'; b.appendChild(h);
      if (k) { row(b, 'Kastell', k.text); row(b, 'Teil von', a.name); }
      row(b, 'Bauart', LIMES_ART[a.art].name);
      row(b, 'Zeitraum', 'etwa ' + fmtYear(a.von) + ' bis ' + fmtYear(a.bis));
      row(b, 'Länge', 'rund ' + a.laenge_km.toLocaleString('de-DE') + ' km');
      row(b, 'Bedeutung', a.text);
      row(b, 'Hinweis', 'Verlauf schematisch über bekannte Kastellorte gelegt; Jahreszahlen gerundet. Eine Grenze war keine dichte Abschottung, sondern kontrollierte Übergänge für Händler, Reisende und Herden.').classList.add('twarn');
      if (k) { var x = el('button', 'small tmore', 'Ganzer Abschnitt: ' + a.name); x.type = 'button'; x.addEventListener('click', function () { openLimes(a); }); b.appendChild(x); }
    });
  }

  /* ---------- Layer „Seidenstraße der Han (Forschungsdaten)“ (data/han_seidenstrasse.json, build_han_seidenstrasse.py) ----------
     Rekonstruierte Hauptlinien und Verkehrspunkte der Westlichen (202 v.–8 n. Chr.) und Östlichen Han (25–220 n. Chr.):
     Hauptstädte, Kommandanturen, Kreissitze, Poststationen, Pässe, Fährstellen. Quelle: Hu/Yan/Zhang 2018, CC BY 4.0. */
  var HANSEIDE = null, HANSEIDE_LINIEN = [];
  var HS_FARBE = { 'Poststation': '#5fd8ff', 'Pass mit Grenzposten': '#ff7a59', 'Hauptstadt': '#ffd166', 'Sitz einer Kommandantur': '#ffd166',
    'Sitz eines Militärkommandanten': '#ff9e66', 'Kreissitz': '#f1e6c8', 'Fährstelle': '#8be08b', 'Brücke': '#8be08b', 'Siedlung': '#c9b49b' };
  var HS_ROLLE = {
    'Poststation': 'Poststationen versorgten Boten, Beamte und Gesandte mit Pferden, Unterkunft und Verpflegung und hielten fest, wer durchreiste.',
    'Pass mit Grenzposten': 'An Pässen und Grenzposten wurden Reisende und Waren kontrolliert; ohne Passierschein ging es nicht weiter.',
    'Sitz einer Kommandantur': 'Verwaltungssitz einer Kommandantur (Bezirk): Steuern, Getreidelager, Militär – wichtige Versorgungspunkte am Weg.',
    'Sitz eines Militärkommandanten': 'Sitz eines Militärkommandanten, der den Abschnitt der Straße sicherte.',
    'Hauptstadt': 'Hauptstadt eines Reiches oder Staates: Ziel von Gesandtschaften und Mittelpunkt von Handel und Verwaltung.',
    'Kreissitz': 'Verwaltungssitz eines Kreises mit Markt; Rast- und Versorgungspunkt.',
    'Fährstelle': 'Übergang über einen Fluss.', 'Brücke': 'Übergang über einen Fluss.'
  };
  function initHanSeide(d) {
    HANSEIDE = d && Array.isArray(d.stationen) ? d : null; HANSEIDE_LINIEN = [];
    if (!HANSEIDE) return;
    HANSEIDE.linien.forEach(function (L) { L.teile.forEach(function (t, i) { HANSEIDE_LINIEN.push({ id: L.id + '-' + i, hanlinie: L, pts: t }); }); });
    HANSEIDE.stationen.forEach(function (s) { s.hanstation = true; });
  }
  function hanSeideAn(y) { return !!HANSEIDE && TRADE.on && TRADE.hanseide && !!state.on.han && state.epoche === 'antike' && y >= -202 && y <= 220; }
  function hanStationen(y) {
    if (!hanSeideAn(y)) return [];
    return HANSEIDE.stationen.filter(function (s) { return s.zeiten.some(function (z) { return y >= z[0] && y <= z[1]; }); });
  }
  function hanZeitText(s) {
    return s.zeiten.map(function (z) { return z[1] <= 8 ? 'Westliche Han (' + fmtYear(z[0]) + ' bis ' + fmtYear(z[1]) + ')' : 'Östliche Han (' + fmtYear(z[0]) + ' bis ' + fmtYear(z[1]) + ')'; }).join(' · ');
  }
  var HS_QUELLE = 'Hu Yumeng, Yan Bo, Zhang Ping: Traffic data of the Silk Road in the Han dynasty (两汉丝绸之路交通数据集), China Scientific Data 3 (2018); Science Data Bank, DOI 10.57760/sciencedb.611, Lizenz CC BY 4.0.';
  function openHanStation(s) {
    if (!darfLokal('routen')) return; INFO_NEU = { art: 'hanstation', id: s.id };
    showInfo(function (b) {
      b.appendChild(el('div', 'tk land', 'Seidenstraße der Han · ' + s.typ));
      var h = el('h3', null, s.py + ' (' + s.zh + ')'); h.id = 'tinfoTitle'; b.appendChild(h);
      row(b, 'Art', s.typ);
      if (HS_ROLLE[s.typ]) row(b, 'Rolle für Handel und Verkehr', HS_ROLLE[s.typ]);
      row(b, 'Belegt für', hanZeitText(s));
      if (s.land) row(b, 'Heute', s.land);
      row(b, 'Daten', HS_QUELLE + ' Lage nach dem Datensatz; Namen in der dort verwendeten Umschrift.');
      row(b, 'Hinweis', 'Rekonstruktion aus Quellen, Funden und Satellitenbildern. Viele Lagen ausländischer Orte sind unsicher.').classList.add('twarn');
    });
  }
  function openHanLinie(L) {
    if (!darfLokal('routen')) return; INFO_NEU = { art: 'hanlinie', id: L.id };
    showInfo(function (b) {
      b.appendChild(el('div', 'tk land', 'Seidenstraße der Han · Hauptlinie'));
      var h = el('h3', null, L.de + ' (' + L.zh + ')'); h.id = 'tinfoTitle'; b.appendChild(h);
      var n = HANSEIDE.stationen.length, typen = {};
      HANSEIDE.stationen.forEach(function (s) { typen[s.typ] = (typen[s.typ] || 0) + 1; });
      row(b, 'Was gezeigt wird', 'Eine von 14 rekonstruierten Hauptlinien der Seidenstraße zur Han-Zeit, von Chang’an bis ans Mittelmeer, dazu ' + n +
        ' Verkehrspunkte: ' + Object.keys(typen).sort(function (a, c) { return typen[c] - typen[a]; }).slice(0, 6).map(function (t) { return typen[t] + ' × ' + t; }).join(', ') + ' …');
      row(b, 'Bedeutung', 'Die Han sicherten den Weg nach Westen mit Kommandanturen, Garnisonen, Poststationen und Grenzpässen. Über diese Kette liefen Gesandtschaften und der Handel mit Seide, Pferden und anderen Waren – meist von Station zu Station, nicht in einem Zug bis nach Rom.');
      row(b, 'Daten', HS_QUELLE);
    });
  }

  /* ---------- Handels- und Verkehrsnetze aus Forschungsdaten (data/netze/, build_netze.py, js/netze.js) ----------
     Register data/netze/index.json; die Netzdateien werden erst geladen, wenn ein Netz eingeschaltet wird (lokal, keine
     fremden Server). Sichtbar nach Jahr – unabhängig davon, welche Reiche eingeblendet sind. Format: docs/HANDELSNETZE.md. */
  var NETZE = { index: null, an: {}, daten: {}, laden: {}, obj: {} };
  var DATIERUNG_TXT = { jahrgenau: 'jahrgenau (eigene Jahre je Strecke)', zeitraum: 'Zeitraum des Datensatzes (Strecken nicht einzeln datiert)',
    reisedatum: 'Reisedaten aus Reiseberichten (Monat)', modell: 'modelliert' };
  var NETZ_GRUPPE_TK = { land: 'land', wasser: 'see', reise: 'reise' };
  function initNetze(ix) {
    NETZE.index = ix && Array.isArray(ix.netze) ? ix : null;
    if (!NETZE.index) { $('#netzSec').hidden = true; return; }
    netzMenuBauen();
  }
  function netzMeta(id) { return NETZE.index ? NETZE.index.netze.filter(function (n) { return n.id === id; })[0] : null; }
  function netzeVerfuegbar() { return NETZE.index ? NETZE.index.netze.filter(function (n) { return n.status === 'verfuegbar'; }) : []; }
  function netzLaden(id) {
    var m = netzMeta(id); if (!m || !m.datei) return Promise.resolve(null);
    if (NETZE.daten[id]) return Promise.resolve(NETZE.daten[id]);
    if (!NETZE.laden[id]) {
      var chip = $('.chip.netz[data-netz="' + id + '"]'); if (chip) chip.classList.add('laedt');
      NETZE.laden[id] = daten('netz_' + id, m.datei).then(function (d) {
        var fehler = Netze.pruefen(d); if (fehler.length) console.warn('Netz ' + id + ': ' + fehler.length + ' Hinweise', fehler.slice(0, 10));
        NETZE.daten[id] = Netze.vorbereiten(d);
        var obj = {};   // Pfadobjekte je Linie (bleiben dieselben, nur der Stil ändert sich)
        d.linien.forEach(function (l) { obj[l.id] = l.teile.map(function (t, i) { return { id: 'n-' + l.id + '-' + i, netzlinie: l, netzM: m, pts: t, stil: 'aktiv' }; }); });
        (d.orte || []).forEach(function (o) { o.netzort = true; o.netzM = m; });
        NETZE.obj[id] = obj;
        if (chip) chip.classList.remove('laedt');
        lastKey = ''; setYear(state.year);
        return NETZE.daten[id];
      }).catch(function (e) { console.warn(e); if (chip) chip.classList.remove('laedt'); toast('Netz „' + m.name + '“ konnte nicht geladen werden.'); delete NETZE.laden[id]; return null; });
    }
    return NETZE.laden[id];
  }
  function netzSetzen(id, v) {
    NETZE.an[id] = v; chipSetzen('.chip.netz[data-netz="' + id + '"]', v);
    if (v) netzLaden(id);
  }
  function netzeSchluessel(y) {
    return Object.keys(NETZE.an).filter(function (id) { return NETZE.an[id] && NETZE.daten[id]; }).sort()
      .map(function (id) { return id + Netze.schluessel(NETZE.daten[id], y); }).join(',') + state.mode;
  }
  function netzePaths() {
    var y = state.year, out = [];
    Object.keys(NETZE.an).forEach(function (id) {
      if (!NETZE.an[id] || !NETZE.daten[id]) return;
      Netze.linienImJahr(NETZE.daten[id], y).forEach(function (x) { NETZE.obj[id][x.linie.id].forEach(function (o) { o.stil = x.stil; out.push(o); }); });
    });
    return out;
  }
  function netzeOrte() {
    var y = state.year, out = [];
    Object.keys(NETZE.an).forEach(function (id) { if (NETZE.an[id] && NETZE.daten[id]) out.push.apply(out, Netze.orteImJahr(NETZE.daten[id], y)); });
    return out;
  }
  function netzRgba(hex, a) { var c = rgb(hex); if (state.mode === 'schem') c = c.map(function (v) { return Math.round(v * 0.45); }); return 'rgba(' + c.join(',') + ',' + a + ')'; }
  function netzLinienFarbe(d) {
    var l = d.netzlinie, m = d.netzM, hex = m.farbe;
    if (m.id === 'viatariq') hex = l.post ? '#8fc7ff' : l.hadsch ? '#9be89b' : hex;   // Post und Pilgerweg eigens gekennzeichnet
    var a = d.stil === 'blass' ? 0.45 : d.stil === 'gereist' ? 0.6 : (m.id === 'viatariq' && !l.haupt) || m.id === 'thurayya' ? 0.62 : 0.92;
    return netzRgba(hex, a);
  }
  function netzUnsicher(l) { return l.lage === 'hypothetisch' || l.beleg === 'gering'; }
  function netzStrich(d) {
    var m = d.netzM.id;
    if (m === 'thurayya' || m === 'viatariq') return null;   // viele kurze Abschnitte: dünne Linie
    if (m === 'mongolen') return d.stil === 'aktiv' ? 2 : d.stil === 'gereist' ? 1.3 : 0.9;
    return m === 'petra_gaza' ? 2.2 : 1.4;
  }
  function netzOrtFarbe(o) { return netzRgba(o.netzM.farbe, 0.95); }
  function netzOrtTitel(o) { return o.name + (o.zh ? ' (' + o.zh + ')' : o.ar ? ' (' + o.ar + ')' : ''); }
  function netzZeile(b, m, d) {
    row(b, 'Datierung', DATIERUNG_TXT[d.datierung.typ] + '. ' + d.datierung.text);
    if (d.hinweis) row(b, 'Hinweis', d.hinweis).classList.add('twarn');
    row(b, 'Daten', d.quelle.zitat);
    row(b, 'Lizenz', d.quelle.lizenz + (d.quelle.geaendert ? ' · verändert: ' + d.quelle.geaendert : ''));
    var x = el('button', 'small tmore', 'Alle Quellen der Netze'); x.type = 'button'; x.addEventListener('click', function () { openNetzQuellen(); }); b.appendChild(x);
  }
  function openNetzLinie(l, m) {
    if (!darfLokal('routen')) return; INFO_NEU = { art: 'netzlinie', netz: m.id, id: l.id };
    var d = NETZE.daten[m.id];
    showInfo(function (b) {
      b.appendChild(el('div', 'tk ' + NETZ_GRUPPE_TK[m.gruppe], m.name));
      var h = el('h3', null, l.name || m.name); h.id = 'tinfoTitle'; b.appendChild(h);
      if (l.zh) row(b, 'Originalname', l.zh);
      if (m.id === 'mongolen' && l.__reise) {
        row(b, 'Reisende', l.__reise.reisender + ' (' + l.__reise.reisender_zh + ')');
        row(b, 'Bericht', l.__reise.bericht);
        row(b, 'Ganze Reise', Netze.spanne(l.__reise.von, l.__reise.bis));
      }
      row(b, m.id === 'mongolen' ? 'Etappe' : 'Zeitraum', Netze.zeitText(l));
      var p = Netze.periode(d, l.von); if (p) row(b, 'Periode', p.name + ' (' + p.dynastien + ')');
      if (l.km) row(b, 'Länge', 'rund ' + l.km.toLocaleString('de-DE') + ' km');
      if (m.id === 'viatariq') {
        row(b, 'Art', l.haupt ? 'Hauptstraße' : 'Nebenstraße');
        if (l.post) row(b, 'Staatliche Post', 'Teil des barīd, der staatlichen Post: Kuriere, Nachrichten und Beamte reisten von Station zu Station. Eine Postroute ist keine Handelsroute.');
        if (l.hadsch) row(b, 'Pilgerweg', 'Teil eines Hadsch-Weges nach Mekka. Pilgerkarawanen nahmen oft Waren mit, der Weg ist aber zuerst ein Pilgerweg.');
        if (l.itinerar && !l.post && !l.hadsch) row(b, 'Bekannte Route', l.itinerar);
        if (l.quelle_mittelalter) row(b, 'Quelle', l.quelle_mittelalter + ' (mittelalterlicher Text)');
        if (l.literatur) row(b, 'Forschung', l.literatur);
        row(b, 'Sicherheit', 'Existenz: ' + l.beleg + ' · Lage: ' + l.lage);
      }
      if (m.id === 'tang') row(b, 'Bedeutung', 'Über diese Straßen liefen Gesandtschaften, Truppen, Mönche und der Handel mit Seide, Pferden und Tee. Poststationen und Garnisonen sicherten den Weg.');
      if (m.id === 'thurayya') row(b, 'Was gezeigt wird', 'Ein Abschnitt des Wegenetzes, wie es arabische Geografen beschrieben: von Ort zu Ort mit Entfernungen in Tagesreisen bzw. Meilen. Gezeigt ist ein Weg, nicht der Umfang des Handels darauf.');
      if (m.id === 'petra_gaza') row(b, 'Bedeutung', 'Auf diesem Weg brachten nabatäische Karawanen Weihrauch und Myrrhe aus Südarabien über Petra an den Mittelmeerhafen Gaza. Festungen, Rastplätze und Zisternen sicherten die Wüstenstrecke.');
      netzZeile(b, m, d);
    });
  }
  function openNetzOrt(o) {
    if (!darfLokal('routen')) return; var m = o.netzM; INFO_NEU = { art: 'netzort', netz: m.id, id: o.id };
    var d = NETZE.daten[m.id];
    showInfo(function (b) {
      b.appendChild(el('div', 'tk ' + NETZ_GRUPPE_TK[m.gruppe], m.name + ' · ' + o.typ));
      var h = el('h3', null, netzOrtTitel(o)); h.id = 'tinfoTitle'; b.appendChild(h);
      row(b, 'Art', o.typ);
      if (o.heute && o.heute !== o.name) row(b, 'Heute', o.heute);
      if (o.region) row(b, 'Region', o.region);
      if (o.__reise) row(b, 'Station der Reise', o.__reise.reisender + ' (' + Netze.spanne(o.__reise.von, o.__reise.bis) + ')' + (o.jahr ? ', erreicht ' + o.jahr : ''));
      else row(b, 'Belegt für', Netze.spanne(o.von, o.bis));
      if (o.text) row(b, 'Beschreibung (aus dem Datensatz, englisch)', o.text);
      if (o.literatur) row(b, 'Forschung', o.literatur);
      netzZeile(b, m, d);
    });
  }
  var NETZ_STATUS = { verfuegbar: 'eingebunden (dieses Menü)', bestehend: 'eingebunden (andere Stelle im Menü)', nicht_verfuegbar: 'geprüft – nicht verfügbar', nicht_lizenziert: 'geprüft – keine passende Lizenz', zurueckgestellt: 'geprüft – zurückgestellt (Zeitraum)' };
  function openNetzQuellen() {
    if (!NETZE.index) return; INFO_NEU = { art: 'netzquellen' };
    showInfo(function (b) {
      b.appendChild(el('div', 'tk land', 'Handels- und Verkehrsnetze'));
      var h = el('h3', null, 'Quellenübersicht'); h.id = 'tinfoTitle'; b.appendChild(h);
      b.appendChild(el('p', 'nq-intro', 'Alle Netze stammen aus veröffentlichten Forschungsdaten. Sie liegen im Projekt und werden ohne fremde Server geladen. Geprüfte, aber nicht übernommene Quellen stehen mit Grund dabei.'));
      ['verfuegbar', 'bestehend', 'zurueckgestellt', 'nicht_verfuegbar', 'nicht_lizenziert'].forEach(function (st) {
        var L = NETZE.index.netze.filter(function (n) { return n.status === st; }); if (!L.length) return;
        b.appendChild(el('h4', 'nq-h', NETZ_STATUS[st]));
        L.forEach(function (n) {
          var g = (NETZE.index.gruppen.filter(function (x) { return x.id === n.gruppe; })[0] || {}).name || n.gruppe;
          var box = el('div', 'nq'); var t = el('b', null, n.name); if (n.farbe) t.style.setProperty('--c', n.farbe); box.appendChild(t);
          box.appendChild(el('span', 'nq-m', g + (n.von != null ? ' · ' + Netze.spanne(n.von, n.bis) : '') + (n.datierung ? ' · ' + (DATIERUNG_TXT[n.datierung] || n.datierung) : '') + (n.lizenz ? ' · ' + n.lizenz : '')));
          box.appendChild(el('span', 'nq-q', n.quelle || ''));
          if (n.ort) box.appendChild(el('span', 'nq-q', 'Im Menü: ' + n.ort));
          if (n.grund) box.appendChild(el('span', 'nq-g', n.grund));
          b.appendChild(box);
        });
      });
      b.appendChild(el('p', 'nq-intro', 'Ausführlich: docs/HANDELSNETZE.md und docs/DATENQUELLEN.md im Projekt.'));
    });
  }
  function netzMenuBauen() {
    var box = $('#netzGruppen'); box.innerHTML = '';
    NETZE.index.gruppen.forEach(function (g) {
      var alle = NETZE.index.netze.filter(function (n) { return n.gruppe === g.id; }), da = alle.filter(function (n) { return n.status === 'verfuegbar'; });
      var sec = el('div', 'netz-gruppe'); sec.dataset.gruppe = g.id;
      sec.appendChild(el('h3', 'hsub-h', g.name));
      if (g.hinweis) sec.appendChild(el('p', 'hint netz-hint', g.hinweis));
      da.forEach(function (n) {
        var b = el('button', 'chip plain netz'); b.type = 'button'; b.dataset.netz = n.id; b.setAttribute('aria-pressed', 'false');
        b.style.setProperty('--c', n.farbe); b.title = n.kurz + ' · Quelle: ' + n.quelle + ' · ' + n.lizenz;
        b.appendChild(el('i')); b.appendChild(el('span', null, n.name)); b.appendChild(el('small', null, Netze.spanne(n.von, n.bis)));
        b.addEventListener('click', function () {
          var v = !NETZE.an[n.id], o = {}; o[n.id] = v; setState({ netze: o });
          if (v && (state.year < n.von || state.year > n.bis)) {
            var ziel = Math.max(YMIN, Math.min(YMAX, n.von));
            if (n.von >= YMIN && n.von <= YMAX && darfLokal('zeit')) { setYear(ziel); toast(n.name + ': ' + Netze.spanne(n.von, n.bis) + ' – Zeitleiste auf ' + fmtYear(state.year) + ' gestellt.'); }
            else toast(n.name + ': ' + Netze.spanne(n.von, n.bis) + '. Dieser Zeitraum liegt außerhalb der Zeitleiste dieses Tafelbilds.');
          }
        });
        sec.appendChild(b);
      });
      var weitere = alle.filter(function (n) { return n.status === 'bestehend'; });
      if (weitere.length) sec.appendChild(el('p', 'hint netz-hint', 'Außerdem unter „Handel & Austausch“: ' + weitere.map(function (n) { return n.name; }).join(', ') + '.'));
      var fehlt = alle.filter(function (n) { return /^(nicht_|zurueck)/.test(n.status); });
      if (fehlt.length) sec.appendChild(el('p', 'hint netz-hint netz-fehlt', 'Geprüft, nicht übernommen: ' + fehlt.map(function (n) { return n.name.replace(/ \(.*\)$/, ''); }).join(', ') + '.'));
      box.appendChild(sec);
    });
  }

  /* ---------- Layer „Römische Straßen“ (Itiner-e, CC BY 4.0) ---------- */
  /* Zeitmodell (js/strassenzeit.js): Linien erscheinen in der modellierten Ausbauphase, sind in der römischen
     Nutzungsphase voll sichtbar und danach nur im Referenzmodus als blasse, gestrichelte „ehemalige Trassen“.
     Pfad-Objekte bleiben je Linie dieselben (kein Neuaufbau, keine Speicherlecks); neu gezeichnet wird nur,
     wenn sich der Zustandsschlüssel ändert. */
  var STRASSEN = null, STR_OBJ = null, STR_CACHE = { key: null, list: [] };
  function strassenSichtbar(y) { return !!STRASSEN && TRADE.on && TRADE.strassen && !!state.on.rom; }
  function strassenSchluessel(y) {
    if (!strassenSichtbar(y)) return 'aus';
    // nur Sichtbarkeit und Stil: der gezeichnete Anteil ändert sich über die Feder, ohne die Linien neu zu übergeben
    return [STR_OPT.ehemals, STR_OPT.animieren, STR_OPT.unsicherheit, state.mode].join('') + StrassenZeit.schluessel(STRASSEN.linien, y, STR_OPT, true);
  }
  /* Linie gleichmäßig unterteilen (≈ 0,03°): Der Shader misst die Strichlänge in Punkten, nicht in Kilometern –
     bei gleichen Abständen entspricht der gezeichnete Anteil der Länge. */
  function gleichmaessig(p, schritt) {
    var out = [p[0]];
    for (var i = 1; i < p.length; i++) {
      var a = p[i - 1], b = p[i], d = Math.hypot((b[0] - a[0]) * Math.cos(a[1] * Math.PI / 180), b[1] - a[1]), n = Math.max(1, Math.round(d / schritt));
      for (var k = 1; k <= n; k++) out.push([a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n]);
    }
    return out;
  }
  var ROM_MITTE = [12.48, 41.89];
  function strassenPaths(y) {
    if (!strassenSichtbar(y)) {
      if (STR_OBJ && STR_CACHE.key !== 'aus') { STR_OBJ.forEach(function (o) { o.gez = 0; o.ziel = 0; }); STR_PEN.list = []; STR_CACHE = { key: 'aus', list: [] }; }
      return [];
    }
    if (!STR_OBJ) STR_OBJ = STRASSEN.linien.map(function (L, i) {
      // Anschlusspunkt u (Anteil der Länge ab dem ersten Punkt): dort setzt die Linie am schon gezeichneten Netz an
      var u = L.netz ? L.netz.u : d3.geoDistance(L.p[L.p.length - 1], ROM_MITTE) < d3.geoDistance(L.p[0], ROM_MITTE) ? 1 : 0;
      return { id: 'str' + i, strasse: true, s: L.s, L: L, pts: gleichmaessig(L.p, 0.03), gez: 0, ziel: 0, u: u };
    });
    var key = strassenSchluessel(y);
    if (key === STR_CACHE.key) { strassenAnteile(y); return STR_CACHE.list; }
    var list = [];
    STR_OBJ.forEach(function (o) { strassenZiel(o, y); if (o.stil) list.push(o); });
    STR_CACHE = { key: key, list: list };
    return list;
  }
  /* Zustand und Ziel-Anteil einer Linie; vorwärts zeichnet die Feder, rückwärts gilt der neue Stand sofort */
  function strassenZiel(o, y) {
    var z = StrassenZeit.zustand(o.L, y, STR_OPT);
    o.stil = z.stil; o.anteil = z.anteil; o.phase = z.phase;
    var ziel = !z.stil ? 0 : z.stil === 'ausbau' ? z.anteil : 1;
    if (z.stil === 'ehemals' || z.stil === 'undatiert') o.gez = ziel;   // ehemalige/undatierte Trassen ohne Feder
    else if (ziel < o.gez || (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches)) { o.gez = ziel; strassenUniform(o); }
    else if (ziel > o.gez && ziel !== o.ziel) strassenFeder(o, ziel);
    o.ziel = ziel;
  }
  /* bei jedem Jahreswechsel: gezeichnete Anteile nachführen (auch wenn sich kein Stil ändert) */
  function strassenAnteile(y) {
    if (!STR_OBJ || !strassenSichtbar(y)) return;
    STR_CACHE.list.forEach(function (o) { strassenZiel(o, y); });
  }
  /* Zeichenfeder für Straßen: wie bei den Schiffsrouten wächst nur der sichtbare Abschnitt der Linie (Shader-Werte),
     die Geometrie bleibt fest. Vom Anschlusspunkt u aus wächst die Linie in beide Richtungen gleich schnell. */
  var STR_PEN = { list: [], raf: 0, dauer: 1600 };
  function strassenFeder(o, ziel) {
    var q = STR_PEN.list.filter(function (x) { return x.o === o; })[0];
    if (q) { q.von = o.gez; q.nach = ziel; q.t0 = performance.now(); }
    else STR_PEN.list.push({ o: o, von: o.gez, nach: ziel, t0: performance.now() });
    if (!STR_PEN.raf) STR_PEN.raf = requestAnimationFrame(strassenFederLauf);
  }
  /* sichtbarer Abschnitt als Shader-Werte [dashOffset, dashSize, gapSize]. Im Shader trägt Punkt i (von n) den Wert
     (n − i) / n: 1 am ersten Punkt, fallend zum letzten. Sichtbar ist dashOffset … dashOffset + dashSize. */
  function strassenFenster(o) {
    if (o.gez >= 1) return [0, 1, 0];
    var f = Math.max(o.gez, 0), u = o.u, m = Math.max(u, 1 - u);
    var lo = Math.max(0, u - f * m), hi = Math.min(1, u + f * m), n = o.pts.length;
    var r = function (s) { return (n - s * (n - 1)) / n; }, e = 0.5 / n;
    if (f <= 0) return [2, 0.00001, 3];   // noch nichts gezeichnet
    return [r(hi) - e, r(lo) - r(hi) + 2 * e, 3];
  }
  function strassenGap(o) { return strassenFenster(o)[0]; }
  function strassenUniform(o) {
    var g = o.__threeObjPath, m = g && g.children[0] && g.children[0].material, u = m && m.uniforms;
    if (!u || !u.dashSize || o.stil === 'ehemals' || o.stil === 'undatiert') return;
    var w = strassenFenster(o);
    u.dashOffset.value = w[0]; u.dashSize.value = w[1]; u.gapSize.value = w[2];
  }
  function strassenFederLauf(now) {
    STR_PEN.raf = STR_PEN.list.length ? requestAnimationFrame(strassenFederLauf) : 0;
    STR_PEN.list = STR_PEN.list.filter(function (q) {
      if (q.o.ziel !== q.nach) return false;   // inzwischen zurückgespult oder neues Ziel
      var t = Math.min(1, (now - q.t0) / STR_PEN.dauer), f = 1 - Math.pow(1 - t, 2);
      q.o.gez = q.von + (q.nach - q.von) * f;
      strassenUniform(q.o);
      return t < 1;
    });
  }
  /* Pfade an den Globus geben. globe.gl übernimmt sie erst beim nächsten Durchlauf; die Strichwerte kommen dann aus
     pathDash/pathDashInitialGap (strassenFenster), laufende Federn setzen sie danach direkt. */
  function pfadeSetzen(list) {
    globe.pathsData(list);
    list.forEach(function (d) { if (d.strasse) strassenUniform(d); });
  }
  function strassenFarbe(d) {
    var schem = state.mode === 'schem';
    if (d.stil === 'ehemals') return schem ? 'rgba(122,40,20,0.32)' : 'rgba(255,215,195,0.3)';
    if (d.stil === 'undatiert') return schem ? 'rgba(70,70,70,0.6)' : 'rgba(210,210,210,0.6)';
    // einfarbig (Entscheidung, siehe docs/STRASSEN_ZEITMODELL.md): die Datierungsqualität steht in der Infokarte
    var a = d.s === 'H' ? 0.4 : 0.85, rgb = schem ? '122,40,20' : '255,205,185';
    return 'rgba(' + rgb + ',' + a.toFixed(2) + ')';
  }
  function strassenDash(d, i) {
    if (d.stil === 'ehemals') { var f = Math.min(0.45, 0.12 / Math.max(d.L.laenge, 0.01)); return [f, f][i]; }   // ≈ 0,12° Strich/Lücke
    if (d.stil === 'undatiert') { var g = Math.min(0.3, 0.04 / Math.max(d.L.laenge, 0.01)); return [g, g * 2][i]; }
    if (d.gez < 1) return strassenFenster(d).slice(1)[i];   // Feder: gezeichneter Abschnitt
    return [1, 0][i];
  }
  var STR_TXT = { itinere_belegt: 'mit Itiner-e-Belegen eingegrenzt', itinere_teilweise: 'teilweise mit Itiner-e-Belegen', regionalmodell_nicht_einzelbelegt: 'nur regional modelliert (keine Einzelbelege)' };
  var PHASE_TXT = { vor: 'noch nicht angelegt (Modell)', ausbau: 'in der modellierten Ausbauphase', roemisch: 'in römischer Nutzung (Modell)', nachroemisch: 'nach dem Ende der modellierten römischen Nutzung', undatiert: 'nicht datierbar' };
  function openStrassenLinie(d) {
    if (!darfLokal('routen')) return; INFO_NEU = { art: 'strasse', id: d.id };
    var L = d.L, z = L.zeit || {}, it = z.itinere;
    showInfo(function (b) {
      b.appendChild(el('div', 'tk str', 'Römische Straße · ' + L.id));
      var h = el('h3', null, it && it.namen && it.namen.length ? it.namen.slice(0, 2).join(' · ') : 'Römische Straße'); h.id = 'tinfoTitle'; b.appendChild(h);
      row(b, 'Im Jahr ' + fmtYear(state.year), PHASE_TXT[d.phase] || '–');
      row(b, 'Räumliche Sicherheit', L.s === 'S' ? 'gesichert oder erschlossen (Itiner-e: Certain/Conjectured)' : 'vermutet (Itiner-e: Hypothetical)');
      if (L.datierbar) {
        row(b, 'Ausbau (Modell)', fmtYear(L.bmin) + ' bis ' + fmtYear(L.bmax) + (z.region ? ' · Region ' + z.region : ''));
        row(b, 'Römische Nutzung (Modell)', L.endeUnbekannt ? 'Ende unbekannt' : 'bis ' + fmtYear(L.ende));
      } else row(b, 'Datierung', 'keine gültigen Zeitangaben').classList.add('twarn');
      row(b, 'Quellenlage', STR_TXT[L.datierung] || L.datierung);
      if (it && it.belege && it.belege.length) {
        var ul = el('ul', 'tparts');
        it.belege.forEach(function (e) {
          var t = (e.name || 'Abschnitt') + ': ' + [e.bauphase ? 'Bauphase ' + e.bauphase : null,
            e.lower_date != null ? 'frühestens belegt ' + fmtYear(e.lower_date) + (e.lower_fehler ? ' (±' + e.lower_fehler + ')' : '') : null,
            e.upper_date != null ? 'spätestens belegt ' + fmtYear(e.upper_date) + (e.upper_fehler ? ' (±' + e.upper_fehler + ')' : '') : null].filter(Boolean).join(', ');
          ul.appendChild(el('li', null, t));
        });
        row(b, 'Belege (Itiner-e)', ul);
        row(b, 'Zuordnung', it.zuordnung + '; ' + it.segmente + ' Segmente, ' + Math.round(it.datierter_anteil * 100) + ' % der Länge datiert');
      }
      if (z.region_korrektur) row(b, 'Region', z.region_korrektur);
      row(b, 'Nachrömisch', 'Fortbestand ' + (z.historischer_fortbestand || 'unbekannt') + '. ' + (z.modellgrenze_hinweis || ''));
      row(b, 'Hinweis', 'Die Jahreszahlen sind Modellwerte für die Darstellung, keine nachgewiesenen Bau- oder Aufgabejahre. Die schrittweise Einblendung ist eine didaktische Animation.').classList.add('twarn');
      var mb = el('button', 'small tmore', 'Über den Straßen-Layer'); mb.type = 'button'; mb.addEventListener('click', openStrassenInfo); b.appendChild(mb);
    });
  }
  function openStrassenInfo() {
    if (!darfLokal('routen')) return; INFO_NEU = { art: 'strassen' };
    var L = LIT.itinere2025;
    showInfo(function (b) {
      b.appendChild(el('div', 'tk str', 'Kartenlayer'));
      var h = el('h3', null, 'Römische Straßen'); h.id = 'tinfoTitle'; b.appendChild(h);
      var M = STRASSEN.meta, c = StrassenZeit.zaehlen(STRASSEN.linien, state.year, STR_OPT);
      row(b, 'Im Jahr ' + fmtYear(state.year), c.ausbau + ' Linien im Ausbau, ' + c.roemisch + ' in römischer Nutzung, ' + c.nachroemisch + ' nachrömisch' + (c.undatiert ? ', ' + c.undatiert + ' undatiert' : '') + ' (von ' + STRASSEN.linien.length + ')');
      row(b, 'Belegt', 'Verlauf und räumliche Sicherheit der Hauptstraßen (Itiner-e). Für einen Teil der Linien grenzen Itiner-e-Belege (frühestes Datum, Bauphasen meist nach Meilensteinen) den Ausbau ein.');
      row(b, 'Modelliert', 'Ausbauzeitraum und Ende der römischen Nutzung je Region (regionales Szenariomodell). Die schrittweise Einblendung ist eine didaktische Animation, kein belegter Baufortschritt.');
      row(b, 'Darstellung', 'Kräftig: gesicherter oder erschlossener Verlauf; blass: vermutet. Option „Ehemalige Trassen“: nach dem Ende der römischen Nutzung blass gestrichelt (mittelalterliche Nutzung nicht allgemein belegt).');
      row(b, 'Nach 1400', 'Keine Linie gilt als aktiv: Für eine mittelalterliche Nutzung enthält der Datensatz keine Belege. Im Referenzmodus erscheinen die ehemaligen Trassen.').classList.add('twarn');
      row(b, 'Daten', (L ? L.voll + '.' : M._quelle) + ' Zeitmodell ' + (M._zeitmodell_version || '') + ', angereichert mit build_strassen_zeit.py.');
      row(b, 'Lizenz', 'CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/), Daten vereinfacht und auf Hauptstraßen reduziert');
    });
  }

  /* ---------- Schülertexte (data/texte.json, Darstellung in js/texte.js) ---------- */
  var TEXTE = null, LIT = {};
  var TX_NIV = (function () { try { return localStorage.getItem('tafelbild.niveau') || 'B'; } catch (e) { return 'B'; } })();
  function textById(id) { return TEXTE ? TEXTE.texte.filter(function (t) { return t.id === id; })[0] : null; }
  function routeText(v) {
    if (v.art === 'see') return 'seeweg';
    if (v.id === (HANDEL.karawanen && HANDEL.karawanen.route) && state.year >= HANDEL.karawanen.ab) return 'rueckgang';
    return 'seidenstrasse';
  }
  function openText(id, zurueck) {
    var T = textById(id); if (!T) return;
    if (!darfLokal('routen')) return; INFO_NEU = { art: 'text', id: id, zurueck: zurueck && zurueck.art ? zurueck : null };
    showInfo(function (b) {
      b.appendChild(el('div', 'tk tx-tk', 'Schülertext · ' + T.kurz));
      var h = el('h3', null, T.titel); h.id = 'tinfoTitle'; b.appendChild(h);
      var bar = el('div', 'tx-niv'); bar.setAttribute('role', 'group'); bar.setAttribute('aria-label', 'Niveau wählen');
      var inhalt = el('div', 'tx-inhalt');
      ['A', 'B', 'C'].forEach(function (n) {
        var x = el('button', n === TX_NIV ? 'on' : null, 'Niveau ' + n); x.type = 'button'; x.setAttribute('aria-pressed', n === TX_NIV);
        x.title = { A: 'einfach (ca. 90 Wörter)', B: 'mittel (ca. 145 Wörter)', C: 'anspruchsvoll (ca. 200 Wörter)' }[n];
        x.addEventListener('click', function () {
          TX_NIV = n; try { localStorage.setItem('tafelbild.niveau', n); } catch (e) {}
          zustandGemeldet();
          bar.querySelectorAll('button[aria-pressed]').forEach(function (y) { y.classList.toggle('on', y === x); y.setAttribute('aria-pressed', y === x); });
          zeichne();
        });
        bar.appendChild(x);
      });
      if (zurueck && zurueck.art) {   // Rücksprung zur Infokarte der Route bzw. Fahrt
        var zv = zurueck.art === 'zh' ? zhById(zurueck.id) : null;
        var db = el('button', 'tx-daten', zurueck.art === 'zh' ? 'Daten zur ' + (zv ? zv.nr : '') + '. Fahrt' : 'Daten zur Route'); db.type = 'button';
        db.addEventListener('click', function () { infoOeffnen(zurueck); }); bar.appendChild(db);
      }
      b.appendChild(bar); b.appendChild(inhalt);
      function zeichne() { inhalt.innerHTML = ''; Texte.render(inhalt, T, LIT, { land: LANDF, handel: HANDEL, zhenghe: ZHD }, { niveau: TX_NIV }); }
      zeichne();
    });
  }
  function textBtn(b, id) {
    var x = el('button', 'small tmore tx-open', '📖 Schülertext lesen'); x.type = 'button';
    x.addEventListener('click', function () { openText(id); }); b.appendChild(x);
  }
  function pathColor(d) {
    if (d.netzlinie) return netzLinienFarbe(d);
    if (d.strasse) return strassenFarbe(d);
    if (d.orbis) return orbisFarbe(d);
    if (d.limes) return d.limTeil === 'rand' ? (state.mode === 'schem' ? '#fffaf0' : '#1a0c04') : (state.mode === 'schem' ? mix(LIMES_ART[d.limes.art].farbe, '#000000', 0.45) : LIMES_ART[d.limes.art].farbe);
    if (d.hanlinie) return state.mode === 'schem' ? 'rgba(122,74,10,0.9)' : 'rgba(255,224,138,0.92)';
    if (d.vw) {
      var vc = state.mode === 'schem' ? mix(vwFarbe(d.vw), '#000000', 0.25) : vwFarbe(d.vw), l = d.vw.__laeuft;
      var hx = vwFarbe(d.vw);
      if (d.vwArt === 'band') return rgba(hx, l ? 0.4 : 0.14);
      if (d.vwArt === 'schatten') return l ? 'rgba(8,4,16,0.6)' : 'rgba(8,4,16,0.25)';
      if (d.vwArt === 'fluss') return state.mode === 'schem' ? 'rgba(255,255,255,0.95)' : 'rgba(255,255,255,0.9)';
      return l ? vc : rgba(hx, 0.5);
    }
    if (d.eu) return state.mode === 'schem' ? '#1d4f8a' : '#8fc3ff';
    if (d.zh) return d.flow ? 'rgba(255,255,255,0.9)' : zhCol(d.zh, zhAktiv(d.zh, state.year) ? 1 : 0.42);
    if (d.kontakt) return state.mode === 'schem' ? 'rgba(78,46,128,0.95)' : 'rgba(230,210,255,0.95)';
    if (d.flow) return d.teil === 'spaet' ? 'rgba(255,255,255,0.35)' : 'rgba(255,255,255,0.9)';
    if (d.teil === 'spaet') return rgba(tradeCol(d.route.art), 0.58);   // ab 220: schwächer
    return tradeCol(d.route.art);
  }
  function pathDash(d, i) {
    if (d.__pen != null) return [d.__pen, 3][i];
    if (d.netzlinie) return netzUnsicher(d.netzlinie) ? [0.07, 0.06][i] : [1, 0][i];
    if (d.vw) return d.vwArt === 'fluss' ? [0.02, 0.045][i] : [1, 0][i];   // fließende Partikel auf dem Strom
    if (d.eu) return [1, 0][i];
    if (d.strasse) return strassenDash(d, i);
    if (d.orbis) return [1, 0][i];
    if (d.hanlinie) return [1, 0][i];
    if (d.limes) return d.limTeil === 'rand' ? [1, 0][i] : d.limes.__dash[i];
    if (d.zh) {
      if (d.flow) return [0.008, 0.05][i];
      if (d.ab) return d.ab.belegt === 'umstritten' ? DASH_GLOBE.umstritten[i] : [1, 0][i];
      return [1, 0][i];
    }
    if (d.kontakt) return [0.01, 0.02][i];
    if (d.flow) return [0.012, 0.09][i];
    return DASH_GLOBE[d.belegt][i];
  }
  function pathStroke(d) {
    if (d.netzlinie) return netzStrich(d);
    if (d.vw) return d.vwArt === 'band' ? (d.vw.__laeuft ? 22 : 9) : d.vwArt === 'schatten' ? (d.vw.__laeuft ? 9 : 4) : d.vwArt === 'fluss' ? 2.6 : (d.vw.__laeuft ? 5.5 : 2.2);
    if (d.eu) return 2;
    if (d.strasse) return null;   // dünne Linie (günstig bei vielen Straßen)
    if (d.orbis) return null;
    if (d.hanlinie) return 1.6;
    if (d.limes) return d.limTeil === 'rand' ? 11 : 6;
    if (d.zh) return d.flow ? 1.1 : d.ab ? 1.5 : zhAktiv(d.zh, state.year) ? 3.2 : 1.9;
    if (d.teil === 'spaet') return d.flow ? 0.8 : 2.2;
    return d.flow ? 1.2 : d.kontakt ? 1.6 : 3.2;
  }
  function initTradeGlobe() {
    globe.pathsData([])
      .pathPoints('pts').pathPointLat(function (p) { return p[1]; }).pathPointLng(function (p) { return p[0]; })
      .pathPointAlt(function (p) { return p[2] || 0.0012; })
      .pathColor(pathColor)
      .pathStroke(pathStroke)
      .pathDashLength(function (d) { return pathDash(d, 0); })
      .pathDashGap(function (d) { return pathDash(d, 1); })
      .pathDashInitialGap(function (d) { return d.strasse && d.stil !== 'ehemals' && d.stil !== 'undatiert' ? strassenGap(d) : 0; })
      .pathDashAnimateTime(function (d) { return d.vw ? (d.vwArt === 'fluss' ? 2000 : 0) : d.flow ? (d.zh ? 9000 : d.teil === 'spaet' ? 40000 : 14000) : d.kontakt ? 30000 : 0; })
      .pathResolution(1)
      .pathTransitionDuration(0)   // keine Übergänge: neue Linien würden sonst aus ihrem ersten Punkt heraus „fliegen“; gezeichnet wird mit der Feder
      .pathLabel(function (d) {
        var t = el('div', 'gtip');
        if (d.netzlinie) {
          var nl = d.netzlinie, rz = nl.__reise;
          t.appendChild(el('b', null, (rz ? rz.reisender + ': ' : '') + (nl.name || d.netzM.name))); t.appendChild(el('br'));
          t.appendChild(document.createTextNode(d.netzM.name + ' · ' + Netze.zeitText(nl) + (nl.post ? ' · staatliche Post' : nl.hadsch ? ' · Pilgerweg' : '') + (netzUnsicher(nl) ? ' · unsicher' : '') + ' · Klick für Infos'));
          return t.outerHTML;
        }
        if (d.strasse) {
          var nm = d.L.zeit && d.L.zeit.itinere && d.L.zeit.itinere.namen;
          t.appendChild(el('b', null, d.stil === 'ehemals' ? 'Ehemalige römische Trasse' : 'Römische Straße' + (nm && nm.length ? ': ' + nm[0] : ''))); t.appendChild(el('br'));
          t.appendChild(document.createTextNode(d.stil === 'ehemals' ? 'mittelalterliche Nutzung nicht allgemein belegt · Klick für Infos'
            : (PHASE_TXT[d.phase] || '') + (d.s === 'H' ? ' · Verlauf vermutet' : '') + ' · Klick für Infos'));
          return t.outerHTML;
        }
        if (d.limes) {
          t.appendChild(el('b', null, d.limes.name + ' · ' + LIMES_ART[d.limes.art].name)); t.appendChild(el('br'));
          t.appendChild(document.createTextNode('etwa ' + fmtYear(d.limes.von) + ' bis ' + fmtYear(d.limes.bis) + ' · Verlauf schematisch · Klick für Infos'));
          return t.outerHTML;
        }
        if (d.hanlinie) {
          t.appendChild(el('b', null, 'Seidenstraße der Han: ' + d.hanlinie.de)); t.appendChild(el('br'));
          t.appendChild(document.createTextNode(d.hanlinie.zh + ' · Rekonstruktion (Hu/Yan/Zhang 2018) · Klick für Infos'));
          return t.outerHTML;
        }
        if (d.orbis) {
          t.appendChild(el('b', null, (ORBIS_ART[d.orbis.art] || '') + ': ' + d.orbis.von_ort + ' – ' + d.orbis.nach_ort)); t.appendChild(el('br'));
          t.appendChild(document.createTextNode('ORBIS-Modell um 200 n. Chr. · Klick für Infos'));
          return t.outerHTML;
        }
        if (d.zh) {
          t.appendChild(el('b', null, d.ab ? d.zh.name + ': ' + d.ab.name : d.zh.name)); t.appendChild(el('br'));
          t.appendChild(document.createTextNode((d.ab ? BELEGT_TXT[d.ab.belegt] : d.zh.stationen) + ' · Klick für Infos'));
          return t.outerHTML;
        }
        if (d.kontakt) { t.appendChild(el('b', null, d.kontakt.name + ' (' + fmtYear(d.kontakt.jahr) + ')')); return t.outerHTML; }
        if (d.vw) { t.appendChild(el('b', null, d.vw.volk + ' (' + d.vw.von + '–' + d.vw.bis + ')')); t.appendChild(el('br')); t.appendChild(document.createTextNode(d.vw.text + ' · Weg schematisch')); return t.outerHTML; }
        if (d.eu) { t.appendChild(el('b', null, d.eu.jahr + ': ' + d.eu.titel)); t.appendChild(el('br')); t.appendChild(document.createTextNode('Portugal · Weg schematisch')); return t.outerHTML; }
        t.appendChild(el('b', null, d.route.name)); t.appendChild(el('br'));
        t.appendChild(document.createTextNode(TEIL_TXT[d.teil] + ': ' + BELEGT_TXT[PARTS[d.route.id][d.teil].belegt] + ' · Klick für Infos'));
        return t.outerHTML;
      })
      .onPathClick(function (d) {
        if (d.netzlinie) openNetzLinie(d.netzlinie, d.netzM);
        else if (d.strasse) openStrassenLinie(d);
        else if (d.orbis) openOrbisInfo(d);
        else if (d.hanlinie) openHanLinie(d.hanlinie);
        else if (d.limes) openLimes(d.limes);
        else if (d.zh) openText('zhenghe', { art: 'zh', id: d.zh.id });
        else if (d.kontakt) openKontaktInfo(d.kontakt);
        else openText(routeText(d.route), { art: 'route', id: d.route.id });
      })
      .onLabelClick(function (d) {
        if (d.kind === 'handel') openPlaceInfo(d);
        else if (d.kind === 'zhhafen') openZhHafen(d);
        else if (d.kind === 'karawane') openText('rueckgang');
      });
  }

  /* Liste im Menü (Zugang per Tastatur) */
  function renderTradeList(tv) {
    var box = $('#routeList'); box.innerHTML = '';
    if (!TRADE.on) return;
    var zl = CUR_ZV ? CUR_ZV.sichtbar : [];
    if (!tv.routes.length && !tv.kontakte.length && !zl.length) {
      box.appendChild(el('p', 'rl-none', state.epoche === 'ming' ? 'Keine Fahrt des Zheng He in diesem Jahr (oder ausgeblendet).' : 'Keine Verbindung für die eingeblendeten Reiche in diesem Jahr.'));
      return;
    }
    zl.forEach(function (v) {
      var b = el('button', 'rl-item zh'); b.type = 'button'; b.style.setProperty('--zh', ZH_COL[v.nr - 1]);
      b.appendChild(el('i')); b.appendChild(el('span', null, 'Zheng He: ' + v.name));
      if (zhAktiv(v, state.year)) b.appendChild(el('small', null, 'gerade unterwegs'));
      b.addEventListener('click', function () { openText('zhenghe', { art: 'zh', id: v.id }); });
      box.appendChild(b);
    });
    if (tv.strassen) {
      var sb = el('button', 'rl-item str'); sb.type = 'button';
      sb.appendChild(el('i')); sb.appendChild(el('span', null, 'Römische Straßen (Kartenlayer)'));
      sb.addEventListener('click', openStrassenInfo); box.appendChild(sb);
    }
    if (tv.schiff && tv.schiff.length) {
      var ob = el('button', 'rl-item orbis'); ob.type = 'button';
      ob.appendChild(el('i')); ob.appendChild(el('span', null, 'Schiffsverkehr im Reich (ORBIS)'));
      ob.addEventListener('click', function () { openOrbisInfo(null); }); box.appendChild(ob);
    }
    tv.routes.forEach(function (rt) {
      var b = el('button', 'rl-item ' + rt.v.art); b.type = 'button';
      b.appendChild(el('i')); b.appendChild(el('span', null, rt.v.name));
      if (rt.v.seiten && !rt.teile.mitte) b.appendChild(el('small', null, rt.teile.rom ? 'nur römische Seite' : 'nur chinesische Seite'));
      b.addEventListener('click', function () { openText(routeText(rt.v), { art: 'route', id: rt.v.id }); });
      box.appendChild(b);
    });
    tv.kontakte.forEach(function (k) {
      var b = el('button', 'rl-item kontakt'); b.type = 'button';
      b.innerHTML = ENVOY; b.appendChild(el('span', null, 'Gesandtschaft ' + fmtYear(k.jahr) + ': ' + k.name));
      b.addEventListener('click', function () { openKontaktInfo(k); });
      box.appendChild(b);
    });
  }

  /* Infokarten */
  var tinfoReturn = null;
  function showInfo(build) {
    FENSTER.info = INFO_NEU; INFO_NEU = null;
    var body = $('#tinfoBody'); body.innerHTML = '';
    build(body);
    var t = $('#tinfo'); if (t.hidden) tinfoReturn = document.activeElement;
    t.hidden = false; t.querySelector('.tinfo-box').scrollTop = 0;
    $('#tinfoClose').focus({ preventScroll: true });
    zustandGemeldet();
  }
  function closeInfo() {
    var t = $('#tinfo'); if (t.hidden) return false;
    t.hidden = true; FENSTER.info = null; zustandGemeldet();
    if (tinfoReturn && document.body.contains(tinfoReturn) && tinfoReturn.focus) tinfoReturn.focus({ preventScroll: true });
    return true;
  }
  function row(box, label, val) {
    var d = el('div', 'trow'); d.appendChild(el('div', 'tl', label));
    var v = el('div', 'tv'); if (typeof val === 'string') v.textContent = val; else v.appendChild(val);
    d.appendChild(v); box.appendChild(d); return v;
  }
  function linkBtn(txt, fn) { var x = el('button', 'tlink', txt); x.type = 'button'; x.addEventListener('click', fn); return x; }
  function openTradeInfo(v) {
    if (!darfLokal('routen')) return; INFO_NEU = { art: 'route', id: v.id };
    showInfo(function (b) {
      b.appendChild(el('div', 'tk ' + v.art, v.art === 'see' ? 'Seeweg' : 'Landweg'));
      var h = el('h3', null, v.name); h.id = 'tinfoTitle'; b.appendChild(h);
      textBtn(b, routeText(v));
      row(b, 'Zeitraum', fmtRange(v.von, v.bis));
      row(b, 'Sicherheit', badge(v.belegt));
      if (v.seiten) {
        var ul = el('ul', 'tparts');
        [['rom', v.seiten.rom], ['mitte', null], ['han', v.seiten.han]].forEach(function (x) {
          var p = PARTS[v.id][x[0]], li = el('li');
          li.appendChild(el('b', null, TEIL_TXT[x[0]] + ': ')); li.appendChild(badge(p.belegt));
          if (x[1]) li.appendChild(el('div', 'tsrc', 'ab ' + fmtYear(x[1].von) + ' · Quelle: ' + x[1].quelle));
          ul.appendChild(li);
        });
        var K = HANDEL.karawanen;
        if (PARTS[v.id].spaet) {
          var li2 = el('li'); li2.appendChild(el('b', null, 'Ab ' + fmtYear(K.ab) + ': ')); li2.appendChild(badge('vermittelt'));
          li2.appendChild(el('div', 'tsrc', 'Ganze Strecke blass dargestellt; Kamel-Karawanen zeigen den Etappenhandel.'));
          ul.appendChild(li2);
        }
        row(b, 'Abschnitte', ul);
        if (PARTS[v.id].spaet) {
          row(b, K.titel, K.hinweis);
          row(b, 'Quelle (Etappenhandel)', K.quelle);
        }
      }
      var wc = el('div', 'wchips'); v.richtung_waren.forEach(function (w) { wc.appendChild(wareChip(w)); });
      row(b, 'Waren', wc);
      row(b, 'Vermittler', v.vermittler.join(', '));
      var orte = HANDEL.orte.filter(function (o) { return o.an.some(function (a) { return a[0] === v.id; }); });
      if (orte.length) {
        var ob = el('div', 'tlinks');
        orte.forEach(function (o) { ob.appendChild(linkBtn(o.name, function () { openPlaceInfo(o); })); });
        row(b, 'Orte', ob);
      }
      row(b, 'Quelle', v.quelle);
      row(b, 'Hinweis', v.hinweis).classList.add('twarn');
      var wb = el('button', 'small tmore', 'Warenübersicht öffnen'); wb.type = 'button'; wb.addEventListener('click', openWaren); b.appendChild(wb);
    });
  }
  function openPlaceInfo(o) {
    if (!darfLokal('routen')) return; INFO_NEU = { art: 'ort', id: o.id };
    showInfo(function (b) {
      b.appendChild(el('div', 'tk', 'Handelsort'));
      var h = el('h3', null, o.name); h.id = 'tinfoTitle'; b.appendChild(h);
      row(b, 'Vermittler', o.vermittler);
      row(b, 'Zeitraum', fmtRange(o.von, o.bis));
      row(b, 'Sicherheit', badge(o.belegt));
      row(b, 'Quelle', o.quelle);
      var hw = row(b, 'Hinweis', o.hinweis); if (o.belegt === 'umstritten') hw.classList.add('twarn');
      var lb = el('div', 'tlinks');
      o.an.forEach(function (a) { var v = routeById(a[0]); if (v) lb.appendChild(linkBtn(v.name, function () { openTradeInfo(v); })); });
      row(b, 'Route', lb);
    });
  }
  function openKontaktInfo(k) {
    if (!darfLokal('routen')) return; INFO_NEU = { art: 'kontakt', id: k.id };
    showInfo(function (b) {
      b.appendChild(el('div', 'tk kontakt', 'Gesandtschaft · ' + fmtYear(k.jahr)));
      var h = el('h3', null, k.name); h.id = 'tinfoTitle'; b.appendChild(h);
      row(b, 'Ort', k.ort);
      row(b, 'Sicherheit', k.sicherheit);
      row(b, 'Bericht', k.text);
      row(b, 'Quelle', k.quelle);
    });
  }
  function openWaren(src) {
    if (!darfLokal('routen')) return;
    var D = src && src.waren ? src : HANDEL, ming = D === ZHD;
    var body = $('#wbody'); body.innerHTML = '';
    $('#wmt').textContent = ming ? 'Warenübersicht: Fahrten des Zheng He' : 'Warenübersicht';
    var wrap = el('div', 'wtable-wrap'), tb = el('table', 'wtable'), thead = el('thead'), tr = el('tr');
    tr.appendChild(el('th', null, ming ? '← Ausfuhr Chinas (nach Westen)' : '← Von Osten nach Westen'));
    tr.appendChild(el('th', null, ming ? 'Einfuhr nach China (nach Osten) →' : 'Von Westen nach Osten →'));
    thead.appendChild(tr); tb.appendChild(thead);
    var ow = D.waren.filter(function (w) { return w.von_nach === 'ost->west'; }), wo = D.waren.filter(function (w) { return w.von_nach === 'west->ost'; });
    var tbody = el('tbody');
    for (var i = 0; i < Math.max(ow.length, wo.length); i++) {
      var r = el('tr');
      [ow[i], wo[i]].forEach(function (w) {
        var td = el('td');
        if (w) { td.appendChild(el('b', null, w.name)); td.appendChild(el('div', 'wmeta', w.weg + ' · ' + w.quelle)); }
        r.appendChild(td);
      });
      tbody.appendChild(r);
    }
    tb.appendChild(tbody); wrap.appendChild(tb); body.appendChild(wrap);
    if (ming) {
      body.appendChild(el('p', 'wnote', 'Vieles waren Geschenke im Rahmen der Tributdiplomatie: China gab Seide und Porzellan, fremde Herrscher schickten Gesandte mit Gaben. Daneben wurde an den Häfen auch gehandelt.'));
      warenZeigen(true);
      return;
    }
    var d = el('p', 'wnote'); d.appendChild(el('b', null, 'Handelsdefizit? '));
    d.appendChild(document.createTextNode(HANDEL.defizit.text + ' (' + HANDEL.defizit.quelle + ')'));
    body.appendChild(d);
    body.appendChild(el('p', 'wnote', 'Routenverläufe sind schematisch. Zwischen Rom und Han gab es keinen belegten direkten Handel, sondern Zwischenhandel über Parther, Kuschana, Nabatäer, Palmyra und Indien.'));
    body.appendChild(el('h3', 'wsub', 'Umstrittene Thesen (keine gesicherten Tatsachen)'));
    var ul = el('ul', 'wum');
    HANDEL.umstritten.forEach(function (u) {
      var li = el('li'); li.appendChild(badge('umstritten')); li.appendChild(el('b', null, ' ' + u.titel));
      li.appendChild(el('div', null, u.text)); li.appendChild(el('div', 'wmeta', 'Quelle: ' + u.quelle)); ul.appendChild(li);
    });
    body.appendChild(ul);
    warenZeigen(false);
  }
  function warenZeigen(ming) { FENSTER.waren = ming ? 'zh' : 'handel'; $('#wmodal').hidden = false; $('#wmodalClose').focus({ preventScroll: true }); zustandGemeldet(); }
  function warenSchliessen() { if ($('#wmodal').hidden) return false; $('#wmodal').hidden = true; FENSTER.waren = null; zustandGemeldet(); return true; }

  /* Pergamentkarte: Routen, Orte, Waren, Gesandtschaften */
  function keyAct(sel, fn) {
    sel.on('click', fn).on('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); fn(); } });
  }
  function drawTrade(svg, proj, path, r) {
    var tv = CUR_TV; if (!TRADE.on || !tv) return false;
    var g = svg.append('g').attr('class', 'trade').attr('font-family', 'Georgia, serif');
    function inside(xy) { return xy && xy[0] > 12 && xy[0] < W - 12 && xy[1] > 12 && xy[1] < H - 12; }
    var any = false, info = [], labels = g.append('g');
    var lines = g.insert('g', ':first-child');
    if (tv.strassen && r === 'rom') {   // Römische Straßen (Itiner-e, CC BY 4.0) unter den Handelsrouten
      var gruppen = { aktiv: [], ausbau: [], ehemals: [], undatiert: [] };
      strassenPaths(state.year).forEach(function (o) { gruppen[o.stil].push(o.L.p); });
      [['ehemals', 0.3, '5 4'], ['undatiert', 0.45, '1 3'], ['ausbau', 0.32, null], ['aktiv', 0.6, null]].forEach(function (st) {
        if (!gruppen[st[0]].length) return;
        var sd = path({ type: 'MultiLineString', coordinates: gruppen[st[0]] });
        if (sd) { g.insert('path', ':first-child').attr('d', sd).attr('fill', 'none').attr('stroke', st[0] === 'undatiert' ? '#555' : '#7a2e1c').attr('stroke-width', 1.1)
          .attr('stroke-opacity', st[1]).attr('stroke-dasharray', st[2]).attr('pointer-events', 'none'); any = true; }
      });
    }
    if (tv.schiff && tv.schiff.length && r === 'rom') {   // Schiffsverkehr (ORBIS) unter den Handelsrouten
      var sd2 = path({ type: 'MultiLineString', coordinates: tv.schiff.map(function (d) { return d.pts; }) });
      if (sd2) { g.insert('path', ':first-child').attr('d', sd2).attr('fill', 'none').attr('stroke', '#155f86').attr('stroke-width', 1.1)
        .attr('stroke-opacity', 0.55).attr('pointer-events', 'none'); any = true; }
    }
    tv.routes.forEach(function (rt) {
      var v = rt.v, col = TRADE_MAP[v.art];
      var grp = lines.append('g').attr('class', 'troute').attr('tabindex', 0).attr('role', 'button').attr('aria-label', v.name + ': Infokarte öffnen');
      keyAct(grp, function () { openText(routeText(v), { art: 'route', id: v.id }); });
      rt.parts.forEach(function (p) {
        var d = path({ type: 'LineString', coordinates: p.pts }); if (!d) return;
        grp.append('path').attr('d', d).attr('fill', 'none').attr('stroke', 'rgba(245,236,210,.9)').attr('stroke-width', 8).attr('stroke-linecap', 'round').attr('stroke-linejoin', 'round');
        grp.append('path').attr('d', d).attr('fill', 'none').attr('stroke', col).attr('stroke-width', p.belegt === 'umstritten' ? 4.5 : p.teil === 'spaet' ? 2.6 : 3.6)
          .attr('stroke-linecap', 'round').attr('stroke-linejoin', 'round').attr('stroke-dasharray', DASH_MAP[p.belegt])
          .attr('stroke-opacity', p.teil === 'spaet' ? 0.5 : 1);
        grp.append('path').attr('d', d).attr('class', 'thit');
      });
      grp.append('title').text(v.name + ' – ' + BELEGT_TXT[v.belegt] + ' (Klick für Infos)');
      // Vom eigenen Reich aus abtasten: wo verlässt die Route die Karte?
      var pts = dense(joinPts(rt.parts)); if (r === 'han') pts.reverse();
      var xy = pts.map(function (c) { return proj(c); }), first = -1, last = -1, exit = false;
      for (var i = 0; i < xy.length; i++) {
        if (inside(xy[i])) { if (first < 0) first = i; last = i; } else if (first >= 0) { exit = true; break; }
      }
      if (first < 0) return;
      any = true;
      var partial = v.seiten && !rt.teile.mitte && !rt.teile.spaet;
      info.push({ v: v, col: col, xy: xy, first: first, last: last, txt: exit ? '→ ' + ((v.rand && v.rand[r]) || 'weiter über Vermittler') : (partial && last === xy.length - 1 ? '→ weiter nur über Vermittler' : null) });
    });
    // Belegte Flächen (Kopf, Legende, Leiste unten) – dort keine Beschriftungen
    var busy = [[40, 15, 600, 200], [40, H - 150, 380, 150], [0, H - 70, W, 70], [W - 260, 10, 260, 110]].concat(mapCityBoxes);
    function hits(bx) { return busy.some(function (o) { return bx[0] < o[0] + o[2] && bx[0] + bx[2] > o[0] && bx[1] < o[1] + o[3] && bx[1] + bx[3] > o[1]; }); }
    function overlap(bx) {
      var sum = 0;
      busy.forEach(function (o) {
        var w = Math.min(bx[0] + bx[2], o[0] + o[2]) - Math.max(bx[0], o[0]), h = Math.min(bx[1] + bx[3], o[1] + o[3]) - Math.max(bx[1], o[1]);
        if (w > 0 && h > 0) sum += w * h;
      });
      return sum;
    }
    function best(cand) {
      var f = cand.filter(fits); if (f.length) return f[0];
      return cand.slice().sort(function (a, b) { return overlap(a) - overlap(b); })[0];
    }
    function fits(bx) { return bx[0] >= MX && bx[1] >= 8 && bx[0] + bx[2] <= W - MX && bx[1] + bx[3] <= H - 8 && !hits(bx); }
    var MX = 44;
    // Handelsorte
    tv.places.forEach(function (o) {
      var p = proj([o.lng, o.lat]); if (!inside(p)) return;
      var col = TRADE_MAP[(routeById(o.an[0][0]) || {}).art] || '#3b2d14';
      var og = labels.append('g').attr('class', 'tplace').attr('tabindex', 0).attr('role', 'button').attr('aria-label', o.name + ': Infokarte öffnen')
        .attr('transform', 'translate(' + p[0] + ',' + p[1] + ')');
      keyAct(og, function () { openPlaceInfo(o); });
      og.append('rect').attr('x', -7).attr('y', -7).attr('width', 14).attr('height', 14).attr('transform', 'rotate(45)').attr('fill', col).attr('stroke', '#f5ecd2').attr('stroke-width', 2);
      og.append('text').attr('x', 12).attr('y', -9).attr('font-size', 17).attr('font-weight', 700).attr('font-style', 'italic').attr('fill', col)
        .attr('stroke', 'rgba(245,236,210,.95)').attr('stroke-width', 4.5).attr('paint-order', 'stroke').text(mapCityNames[o.name] ? '' : o.name);
      busy.push([p[0] - 10, p[1] - 28, 24 + og.select('text').node().getComputedTextLength(), 38]);
      og.append('title').text(o.name + ' – ' + o.vermittler);
    });
    // Gesandtschaften
    tv.kontakte.forEach(function (k) {
      if (k.pfad) {
        var d = path({ type: 'LineString', coordinates: k.pfad });
        if (d) lines.append('path').attr('d', d).attr('fill', 'none').attr('stroke', '#5a3d8a').attr('stroke-width', 3).attr('stroke-dasharray', '2 7').attr('stroke-linecap', 'round').attr('pointer-events', 'none');
      }
      var p = proj([k.lng, k.lat]); if (!inside(p)) return;
      var kg = labels.append('g').attr('class', 'tplace').attr('tabindex', 0).attr('role', 'button').attr('aria-label', 'Gesandtschaft ' + k.name + ': Infokarte öffnen')
        .attr('transform', 'translate(' + p[0] + ',' + p[1] + ')');
      keyAct(kg, function () { openKontaktInfo(k); });
      kg.append('circle').attr('r', 15).attr('fill', '#5a3d8a').attr('stroke', '#f5ecd2').attr('stroke-width', 2);
      kg.append('g').attr('transform', 'translate(-10,-10) scale(0.84)').attr('color', '#fff').html(ENVOY.replace(/<svg[^>]*>|<\/svg>/g, ''));
      kg.append('text').attr('x', 20).attr('y', 5).attr('font-size', 17).attr('font-weight', 700).attr('font-style', 'italic').attr('fill', '#3d2463')
        .attr('stroke', 'rgba(245,236,210,.95)').attr('stroke-width', 4.5).attr('paint-order', 'stroke').text(k.name + ' ' + shortYear(k.jahr));
      busy.push([p[0] - 17, p[1] - 17, 40 + kg.select('text').node().getComputedTextLength(), 34]);
    });
    // Randpfeile mit Textfeld
    info.forEach(function (o) {
      if (!o.txt) return;
      var A = o.xy[o.last], B = o.xy[Math.max(o.first, o.last - 4)], ang = Math.atan2(A[1] - B[1], A[0] - B[0]) * 180 / Math.PI;
      var ag = labels.append('g').attr('class', 'tarrow').attr('pointer-events', 'none');
      ag.append('path').attr('d', 'M-2,-11 L20,0 L-2,11 Z').attr('fill', o.col).attr('stroke', '#f5ecd2').attr('stroke-width', 2)
        .attr('transform', 'translate(' + A[0] + ',' + A[1] + ') rotate(' + ang + ')');
      var rect = ag.append('rect').attr('rx', 8).attr('fill', 'rgba(245,236,210,.95)').attr('stroke', o.col).attr('stroke-width', 2);
      var te = ag.append('text').attr('font-size', 18).attr('font-weight', 700).attr('font-style', 'italic').attr('fill', o.col).text(o.txt);
      var tw = te.node().getComputedTextLength() + 20, th = 30;
      // Kandidaten: innen neben der Pfeilspitze
      var dx = Math.cos(ang * Math.PI / 180), cand = [];
      var inward = dx > 0 ? [[-tw - 16, 14], [-tw - 16, -th - 14]] : [[16, 14], [16, -th - 14]];
      inward.concat([[-tw / 2, 22], [-tw / 2, -th - 22], [-tw / 2, 60], [-tw / 2, -th - 60]]).forEach(function (c) {
        cand.push([Math.max(MX, Math.min(W - tw - MX, A[0] + c[0])), Math.max(8, Math.min(H - th - 78, A[1] + c[1])), tw, th]);
      });
      var bx = best(cand);
      rect.attr('x', bx[0]).attr('y', bx[1]).attr('width', tw).attr('height', th);
      te.attr('x', bx[0] + 10).attr('y', bx[1] + 21);
      busy.push(bx);
    });
    // Waren-Chips: kompakt in Zeilen, ohne Überlappung
    if (TRADE.waren) info.forEach(function (o) {
      var cg = labels.append('g').attr('class', 'wchips-map').attr('tabindex', 0).attr('role', 'button').attr('aria-label', 'Waren: ' + o.v.name);
      keyAct(cg, function () { openTradeInfo(o.v); });
      var maxW = 340, x = 0, yy = 0, rowH = 26, wmax = 0, all = o.v.richtung_waren, MAXC = 5;
      var list = all.length > MAXC + 1 ? all.slice(0, MAXC).concat([{ name: '+' + (all.length - MAXC) + ' weitere', mehr: true }]) : all;
      list.forEach(function (w) {
        var ow = w.von_nach === 'ost->west', t = w.mehr ? w.name : ow ? '← ' + w.name : w.name + ' →';
        var cgi = cg.append('g');
        var rect = cgi.append('rect').attr('rx', 10).attr('height', 22).attr('fill', w.mehr ? o.col : ow ? '#3b2d14' : '#f5ecd2').attr('stroke', o.col).attr('stroke-width', 1.6);
        var te = cgi.append('text').attr('x', 9).attr('y', 16).attr('font-size', 15).attr('font-weight', 600).attr('fill', w.mehr || ow ? '#f5ecd2' : '#3b2d14').text(t);
        var cw = te.node().getComputedTextLength() + 18; rect.attr('width', cw);
        if (x > 0 && x + cw > maxW) { x = 0; yy += rowH; }
        cgi.attr('transform', 'translate(' + x + ',' + yy + ')');
        cgi.append('title').text(w.mehr ? 'Alle Waren in der Infokarte (Klick)' : w.name + ': ' + (ow ? 'von Osten nach Westen' : 'von Westen nach Osten'));
        x += cw + 5; wmax = Math.max(wmax, x);
      });
      var bw = wmax, bh = yy + 22, cand = [];
      [0.35, 0.55, 0.2, 0.75, 0.1, 0.9].forEach(function (f) {
        var P = o.xy[o.first + Math.floor((o.last - o.first) * f)];
        [[16, 16], [16, -bh - 16], [-bw - 16, 16], [-bw - 16, -bh - 16], [-bw / 2, 40], [-bw / 2, -bh - 40], [40, -bh / 2], [-bw - 40, -bh / 2]].forEach(function (c) {
          cand.push([Math.max(MX, Math.min(W - bw - MX, P[0] + c[0])), Math.max(8, Math.min(H - bh - 78, P[1] + c[1])), bw, bh]);
        });
      });
      var bx = best(cand);
      cg.attr('transform', 'translate(' + bx[0] + ',' + bx[1] + ')');
      busy.push(bx);
    });
    return any;
  }

  /* ---------- Ming-Zeit: Flottenfahrten des Zheng He (data/zhenghe.json) ---------- */
  var ZH_COL = ['#c3f27a', '#93e86f', '#62dc73', '#3dcf86', '#25c497', '#6fe0a8', '#a6efc0'];          // Satellit (dunkler Hintergrund)
  var ZH_COL_SCHEM = ['#3d6b00', '#2f6a12', '#1d6b2a', '#0f6a3e', '#0b6650', '#1f7a52', '#2e5f3c'];  // schematisch (helle Textur)
  function zhBase(v) { return (state.mode === 'schem' ? ZH_COL_SCHEM : ZH_COL)[(v.nr - 1) % 7]; }
  function zhCol(v, a) { return a >= 1 ? zhBase(v) : rgba(zhBase(v), a); }
  function zhAktiv(v, y) { return y >= v.von && y <= v.bis; }
  function zhById(id) { return ZHD.verbindungen.filter(function (v) { return v.id === id; })[0]; }
  function initZh() {
    ZHD.verbindungen.forEach(function (v) {
      ZH.fahrt[v.nr] = true;
      v.__p = { id: v.id, zh: v, pts: v.pfad };
      v.__flow = { id: v.id + ':flow', zh: v, flow: true, pts: v.pfad };
      v.__ab = (v.abzweige || []).map(function (a, i) { return { id: v.id + ':ab' + i, zh: v, ab: a, pts: a.pfad }; });
      var dp = dense(v.pfad), mid = dp[Math.floor(dp.length * 0.62)], end = v.pfad[v.pfad.length - 1];
      v.__tag = { kind: 'waren', route: v, lng: mid[0], lat: mid[1], seite: 'unten', pts: dp.filter(function (x, j) { return j % 2 === 0; }) };
      WTAGS['zh:' + v.id] = v.__tag;
      v.__flag = { kind: 'zhflag', zh: v, lng: end[0], lat: end[1] };
    });
    ZHD.orte.forEach(function (o) { o.kind = 'zhhafen'; o.__fahrten = o.an.map(function (a) { return zhById(a[0]); }).filter(Boolean); });
    // Zeichnen: Pfade verdichten und nach Länge parametrisieren; Häfen bekommen ihren Anteil (0..1) an der Fahrt
    ZHD.verbindungen.forEach(function (v) {
      v.__lauf = lauf(v.pfad);
      v.__ab.forEach(function (a) {
        a.__lauf = lauf(a.ab.pfad);
        a.__f0 = naechster(v.__lauf, a.ab.pfad[0]).f;
      });
      v.__hafen = {};
      ZHD.orte.forEach(function (o) {
        if (o.__fahrten.indexOf(v) < 0) return;
        var best = naechster(v.__lauf, [o.lng, o.lat]);
        v.__ab.forEach(function (a) {
          var n = naechster(a.__lauf, [o.lng, o.lat]);
          if (n.d < best.d) best = { d: n.d, f: a.__f0 + (1 - a.__f0) * n.f };
        });
        v.__hafen[o.id] = best.f;
      });
      v.__reihe = ZHD.orte.filter(function (o) { return v.__hafen[o.id] != null; }).sort(function (a, b) { return v.__hafen[a.id] - v.__hafen[b.id]; });
    });
    DATA.meta.ming = { name: ZHD.ming.name, farbe: ZHD.ming.farbe, von: 1368, bis: 1644, ohneRolle: true, kurz: ZHD.ming.hinweis };
    ZHD.ming.hauptstaedte.forEach(function (h) { h.kind = 'mingstadt'; });
    ZHD.europa.forEach(function (e) { e.kind = 'europa'; e.__p = { id: 'eu' + e.jahr, eu: e, pts: e.route }; e.__lauf = lauf(e.route); });
  }
  /* Pfad mit Längenparameter: pts (verdichtet), cum (kumulierte Länge), len */
  function lauf(pfad) {
    var pts = dense(pfad), cum = [0];
    for (var i = 1; i < pts.length; i++) cum.push(cum[i - 1] + d3.geoDistance(pts[i - 1], pts[i]));
    return { pts: pts, cum: cum, len: cum[cum.length - 1] || 1 };
  }
  function naechster(L, p) {
    var bi = 0, bd = 9;
    L.pts.forEach(function (q, i) { var d = d3.geoDistance(q, p); if (d < bd) { bd = d; bi = i; } });
    return { d: bd, f: L.cum[bi] / L.len };
  }
  /* Anfangsstück eines Pfads bis zum Anteil f (0..1), am Ende interpoliert */
  function schnitt(L, f) {
    f = Math.max(0, Math.min(1, f));
    if (f >= 1) return L.pts;
    var ziel = f * L.len, i = 1;
    while (i < L.cum.length - 1 && L.cum[i] < ziel) i++;
    var a = L.pts[i - 1], b = L.pts[i], t = (ziel - L.cum[i - 1]) / ((L.cum[i] - L.cum[i - 1]) || 1);
    var spitze = d3.geoInterpolate(a, b)(Math.max(0.001, t));
    return L.pts.slice(0, i).concat([spitze]);
  }

  /* ---------- Zeichenfeder: Schiffe zeichnen ihre Route live (Zheng He, portugiesische Fahrten) ----------
     Die Linie wird nur EINMAL an globe.gl übergeben. Danach wächst allein die Strichlänge im Material dieser einen Linie
     (dashSize = gezeichneter Anteil, Lücke dahinter). globe.gl setzt bei jeder neuen Datenübergabe die wandernden Striche
     aller Linien zurück – so laufen die Animationen der übrigen Fahrten ungestört weiter. */
  var PENS = [], PEN = { raf: 0, last: 0, prevAkt: {}, prevEu: {} };
  function penVon(ziel) { return PENS.filter(function (q) { return q.ziel === ziel; })[0]; }
  function penMat(d) { var g = d && d.__threeObjPath, m = g && g.children[0] && g.children[0].material; return m && 'dashSize' in m ? m : null; }
  function setPen(d, f) { d.__pen = Math.max(0.00001, f); var m = penMat(d); if (m) m.dashSize = d.__pen; }
  function penEnde(q) { q.haupt.__pen = null; q.teile.forEach(function (a) { a.obj.__pen = null; }); }
  function penStopAlle() { PENS.forEach(penEnde); PENS = []; cancelAnimationFrame(PEN.raf); PEN.raf = 0; }
  function punktBei(L, f) { var x = schnitt(L, f); return x[x.length - 1]; }
  function penStart(q) {
    q.t0 = performance.now(); q.f = 0; q.erreicht = -1;
    q.haupt.__pen = 0.00001; q.teile.forEach(function (a) { a.obj.__pen = 0.00001; });
    var st = q.lauf.pts[0]; q.schiff = { kind: 'zhschiff', farbe: q.farbe, titel: q.titel, bild: q.bild || null, lng: st[0], lat: st[1] };
    PENS.push(q);
    if (!PEN.raf) PEN.raf = requestAnimationFrame(penFrame);
  }
  function penFrame(now) {
    if (!PENS.length) { PEN.raf = 0; return; }
    PEN.raf = requestAnimationFrame(penFrame);
    if (now - PEN.last < 40) return;
    PEN.last = now;
    var fertig = [];
    PENS.forEach(function (q) {
      var t = Math.min(1, (now - q.t0) / q.dur), f = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;   // sanft an- und auslaufen
      q.f = f;
      setPen(q.haupt, f);
      q.teile.forEach(function (a) { setPen(a.obj, f <= a.f0 ? 0 : (f - a.f0) / (1 - a.f0)); });
      var tip = punktBei(q.lauf, f), vor = punktBei(q.lauf, Math.min(1, f + 0.004)); q.schiff.lng = tip[0]; q.schiff.lat = tip[1];
      if (Math.abs(vor[0] - tip[0]) > 1e-4) q.schiff.ost = vor[0] > tip[0];   // Fahrtrichtung: Bug voraus
      zhSchiffStil(q.schiff);
      if (q.schritt) q.schritt(q, f);
      if (t >= 1) fertig.push(q);
    });
    var zv = CUR_ZV || zhVisible(state.year);
    globe.htmlElementsData(zhHtml(zv));   // nur die HTML-Ebene (Schiffe) – die Linien bleiben unberührt
    if (fertig.length) {
      fertig.forEach(penEnde);
      PENS = PENS.filter(function (q) { return fertig.indexOf(q) < 0; });
      pfadeSetzen(zhPaths(zv)); globe.htmlElementsData(zhHtml(zv)); refreshLabels(); zhErzUpdate();
    }
  }
  /* neue Fahrten (Zheng He: Startjahr erreicht; Europa: Ereignisjahr erreicht) bekommen eine Feder */
  function zhAnimPruefen(zv) {
    PENS = PENS.filter(function (q) { var ok = q.sichtbar(zv); if (!ok) penEnde(q); return ok; });
    var akt = {}, eu = {};
    zv.aktiv.forEach(function (v) { akt[v.id] = 1; });
    (zv.europa || []).forEach(function (e) { eu[e.jahr] = 1; });
    var neu = zv.aktiv.filter(function (v) { return !PEN.prevAkt[v.id]; });
    var euNeu = (zv.europa || []).filter(function (e) { return !PEN.prevEu[e.jahr]; });
    PEN.prevAkt = akt; PEN.prevEu = eu;
    if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    neu.forEach(function (v) {
      penStart({ ziel: v, haupt: v.__p, lauf: v.__lauf, dur: 7000, farbe: ZH_COL[v.nr - 1], titel: v.name + ': Flotte unterwegs', bild: 'zhenghe',
        teile: v.__ab.map(function (a) { return { obj: a, f0: a.__f0 }; }),
        sichtbar: function (z) { return z.sichtbar.indexOf(v) >= 0; },
        schritt: function (q, f) {
          var n = v.__reihe.filter(function (o) { return v.__hafen[o.id] <= f + 0.002; }).length;
          if (n !== q.erreicht) { q.erreicht = n; refreshLabels(); zhErzUpdate(); }
        } });
    });
    euNeu.forEach(function (e) {
      penStart({ ziel: e, haupt: e.__p, lauf: e.__lauf, dur: 5000, farbe: '#8fc3ff', titel: 'Portugiesische Karavelle: ' + e.titel, teile: [],
        sichtbar: function (z) { return (z.europa || []).indexOf(e) >= 0; } });
    });
  }
  /* Pfade für den Globus: während des Zeichnens ohne wandernden Strich */
  function zhPaths(zv) {
    var p = zv.paths.filter(function (d) { return !(d.flow && d.zh && penVon(d.zh)); });
    return strassenPaths(state.year).concat(p, (zv.europa || []).map(function (e) { return e.__p; }));
  }
  function zhHtml(zv) {
    var t = zv.tags.filter(function (d) { return !penVon(d.route); });   // Waren-Etikett erst nach dem Zeichnen
    PENS.forEach(function (q) { t.push(q.schiff); });
    return visibleCities().concat(t, (zv.europa || []).filter(function (e) { return !penVon(e); }), [STANDORT || JENA]);   // Europa-Marker erst bei Ankunft
  }
  function zhLabels(zv) {
    var y = state.year;
    var orte = zv.places.filter(function (o) {
      return o.__fahrten.some(function (v) {
        var q = penVon(v);
        return ZH.fahrt[v.nr] && y >= v.von && (!q || v.__hafen[o.id] <= q.f + 0.002);
      });
    });
    var haupt = mingAn() ? ZHD.ming.hauptstaedte.filter(function (h) { return y >= h.von && y <= h.bis; }) : [];
    return orte.concat(haupt);
  }
  var JUNKE = '<svg viewBox="0 0 32 28" aria-hidden="true"><path d="M3 18h26l-3.5 6.5H7.5z" fill="currentColor"/><path d="M15 3v14M15 4l-8 12h8zM16 6l7 10h-7z" fill="currentColor" stroke="currentColor" stroke-width="1" stroke-linejoin="round"/><path d="M2 26.5c3 1.3 5 1.3 8 0s5-1.3 8 0 5 1.3 8 0" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>';
  /* Abbildungen (Option „Abbildungen statt Symbole“): nur wo eine vorliegt; je Darstellung eine Fassung */
  var ABB = { zhenghe: { sat: 'img/icons/zhenghe_schiff_detail.png', schem: 'img/icons/zhenghe_schiff_schema.png', bugLinks: true } };
  /* Schiff: Das Element hat die Größe 0 und sitzt genau auf der Spitze der gezeichneten Linie;
     das Symbol bzw. die Abbildung steht mit dem Kiel darauf. */
  function zhSchiffEl(d) {
    if (d.__el) return d.__el;
    var e = el('div', 'zhschiff'), s = el('span', 'zhs-sym'); s.innerHTML = JUNKE; e.appendChild(s);
    var img = document.createElement('img'); img.className = 'zhs-bild'; img.alt = ''; img.decoding = 'async'; e.appendChild(img);
    e.style.setProperty('--c', d.farbe); e.title = d.titel;
    d.__el = e; zhSchiffStil(d); return e;
  }
  function zhSchiffStil(d) {
    var e = d.__el; if (!e) return;
    var a = BILDER.an && d.bild && ABB[d.bild], src = a ? a[state.mode === 'schem' ? 'schem' : 'sat'] : '';
    e.classList.toggle('bild', !!a);
    if (a && e.lastChild.getAttribute('src') !== src) e.lastChild.setAttribute('src', src);
    e.classList.toggle('flip', !!a && !!d.ost === !!a.bugLinks);   // Bug in Fahrtrichtung
  }
  function europaEl(d) {
    if (d.__el) return d.__el;
    var e = el('button', 'eumark'); e.type = 'button';
    e.appendChild(el('b', null, String(d.jahr))); e.appendChild(el('span', null, d.ort));
    e.title = 'Europa, ' + d.jahr + ': ' + d.titel + (d.belegt === 'umstritten' ? ' (Datierung umstritten)' : '');
    e.addEventListener('click', function (ev) { ev.stopPropagation(); toast(d.jahr + ' · ' + d.titel + ': ' + d.text); });
    d.__el = e; return e;
  }
  /* Sichtbar: Fahrt eingeschaltet und Startjahr erreicht. Laufende Fahrt hell mit wanderndem Strich, frühere blass. */
  function zhVisible(y) {
    var res = { paths: [], places: [], tags: [], aktiv: [], sichtbar: [], europa: [], key: 'aus' };
    if (!ZHD || !TRADE.on || !ZH.on) return res;   // Teil von „Handel & Austausch“
    var ids = [];
    ZHD.verbindungen.forEach(function (v) {
      if (!ZH.fahrt[v.nr] || y < v.von) return;
      var akt = zhAktiv(v, y);
      ids.push(v.id + (akt ? '*' : ''));
      res.sichtbar.push(v);
      res.paths.push(v.__p); res.paths.push.apply(res.paths, v.__ab);
      if (akt) { res.paths.push(v.__flow); res.aktiv.push(v); res.tags.push(v.__flag); if (TRADE.waren) res.tags.push(v.__tag); }
    });
    ZHD.orte.forEach(function (o) {
      if (o.__fahrten.some(function (v) { return ZH.fahrt[v.nr] && y >= v.von; })) res.places.push(o);
    });
    res.europa = (ZHD.europa || []).filter(function (e) { return y >= e.jahr; });
    res.key = ids.join(',') + '|' + TRADE.waren + '|' + res.places.length + '|' + res.europa.length;
    return res;
  }
  function refreshGlobeMing() {
    globe.pointsData(netzeOrte());
    var zv = CUR_ZV || zhVisible(state.year);
    CUR_TV = { routes: [], parts: zv.aktiv.map(function (v) { return v.__p; }), places: [], kontakte: [], kar: { list: [] }, key: '' };
    globe.polygonsData(visiblePolys().concat(mingAn() ? ZHD.ming.regionen.filter(function (f) { return f.properties.von <= state.year && state.year < f.properties.bis; }) : []));
    zhAnimPruefen(zv);
    refreshLabels();
    globe.htmlElementsData(zhHtml(zv));
    globe.pathColor(pathColor).pathStroke(pathStroke);
    pfadeSetzen(zhPaths(zv).concat(netzePaths()));
    zv.aktiv.forEach(function (v, i) { if (v.__flag.__el) v.__flag.__el.style.setProperty('--dy', (-14 - i * 28) + 'px'); });
    karUpdate();
    setTimeout(scheduleTagSides, 50);
  }
  function zhFlagEl(d) {
    if (d.__el) return d.__el;
    var e = el('div', 'zhflag', d.zh.nr + '. Fahrt'); e.style.setProperty('--c', ZH_COL[d.zh.nr - 1]);
    e.title = d.zh.name + ' (Klick für Infos)';
    e.addEventListener('click', function (ev) { ev.stopPropagation(); openText('zhenghe', { art: 'zh', id: d.zh.id }); });
    d.__el = e; return e;
  }
  function openZhInfo(v) {
    if (!darfLokal('routen')) return; INFO_NEU = { art: 'zh', id: v.id };
    showInfo(function (b) {
      b.appendChild(el('div', 'tk zh', 'Seeweg · Flotte der Ming'));
      var h = el('h3', null, 'Zheng He: ' + v.name); h.id = 'tinfoTitle'; b.appendChild(h);
      textBtn(b, 'zhenghe');
      row(b, 'Zeitraum', v.von + ' bis ' + v.bis);
      row(b, 'Sicherheit', badge(v.belegt));
      row(b, 'Stationen', v.stationen);
      if (v.abzweige && v.abzweige.length) {
        var ul = el('ul', 'tparts');
        v.abzweige.forEach(function (a) { var li = el('li'); li.appendChild(el('b', null, a.name + ': ')); li.appendChild(badge(a.belegt)); ul.appendChild(li); });
        row(b, 'Teilflotten', ul);
      }
      var wc = el('div', 'wchips'); v.richtung_waren.forEach(function (w) { wc.appendChild(wareChip(w)); });
      row(b, 'Waren', wc);
      var hb = el('div', 'tlinks');
      ZHD.orte.filter(function (o) { return o.__fahrten.indexOf(v) >= 0; }).forEach(function (o) { hb.appendChild(linkBtn(o.name, function () { openZhHafen(o); })); });
      row(b, 'Häfen', hb);
      row(b, 'Quelle', v.quelle);
      row(b, 'Hinweis', v.hinweis).classList.add('twarn');
      var wb = el('button', 'small tmore', 'Warenübersicht öffnen'); wb.type = 'button'; wb.addEventListener('click', function () { openWaren(ZHD); }); b.appendChild(wb);
    });
  }
  function openZhHafen(o) {
    if (!darfLokal('routen')) return; INFO_NEU = { art: 'zhhafen', id: o.id };
    showInfo(function (b) {
      b.appendChild(el('div', 'tk zh', 'Hafen · Fahrten des Zheng He'));
      var h = el('h3', null, o.name); h.id = 'tinfoTitle'; b.appendChild(h);
      row(b, 'Funktion', o.funktion);
      var lb = el('div', 'tlinks');
      o.__fahrten.forEach(function (v) { lb.appendChild(linkBtn(v.name, function () { openZhInfo(v); })); });
      row(b, 'Angelaufen', lb);
      row(b, 'Sicherheit', badge(o.belegt));
      row(b, 'Quelle', o.quelle);
      if (o.hinweis) { var hw = row(b, 'Hinweis', o.hinweis); if (o.belegt === 'umstritten') hw.classList.add('twarn'); }
    });
  }
  function openZhBackground() {
    if (!darfLokal('routen')) return; INFO_NEU = { art: 'zhhintergrund' };
    var I = ZHD.info;
    showInfo(function (b) {
      b.appendChild(el('div', 'tk zh', 'Hintergrund'));
      var h = el('h3', null, I.titel); h.id = 'tinfoTitle'; b.appendChild(h);
      I.absaetze.forEach(function (t) { b.appendChild(el('p', 'tpara', t)); });
      row(b, 'Quelle', I.quelle);
    });
  }
  function zhCard(box, c, k, t, p, btn, fn, cls) {
    var d = el('div', 'card' + (cls ? ' ' + cls : '')); d.style.setProperty('--c', c);
    d.appendChild(el('div', 'k', k)); d.appendChild(el('div', 't', t));
    (Array.isArray(p) ? p : [p]).forEach(function (x) { if (x) d.appendChild(el('p', null, x)); });
    if (btn) { var b = el('button', null, btn); b.type = 'button'; b.addEventListener('click', fn); d.appendChild(b); }
    box.appendChild(d);
  }
  function renderCardsMing() {
    var box = $('#cards'), y = state.year; box.innerHTML = '';
    if (!TRADE.on || !ZH.on) {
      zhCard(box, '#5fdc8a', 'Fahrten ausgeblendet', 'Die Fahrten des Zheng He stehen unter „Handel & Austausch“.', null,
        'Fahrten einblenden', function () { if (!TRADE.on) $('#tglHandel').click(); if (!ZH.on) $('#tglZh').click(); });
    }
    var akt = ZHD.verbindungen.filter(function (v) { return zhAktiv(v, y); });
    akt.forEach(function (v) { zhErzKarte(box, v); });
    if (!akt.length) {
      var next = ZHD.verbindungen.filter(function (v) { return v.von > y; })[0];
      var t = y < ZHD.verbindungen[0].von ? 'Die Fahrten beginnen 1405.' : next ? 'Zwischen den Fahrten. Nächste: ' + next.name + '.' : 'Nach 1433 gab es keine solchen Flottenfahrten mehr.';
      zhCard(box, '#566a80', 'Keine Fahrt in diesem Jahr', t, null, null, null, 'none');
    }
    var ev = null; ZHD.ereignisse.forEach(function (e) { if (e.jahr <= y) ev = e; });
    if (ev) zhCard(box, '#5fdc8a', 'Ereignis · ' + ev.jahr + (ev.belegt === 'umstritten' ? ' · teils umstritten' : ''), ev.titel, ev.text);
    var byz = state.on.rom ? activeEvent('rom', y) : null;
    if (byz) zhCard(box, OSTROM, 'Byzantinisches Reich (Ostrom) · ' + byz.label, byz.titel, byz.note, null, null);
    var hs = ZHD.ming.hauptstaedte.filter(function (h) { return y >= h.von && y <= h.bis; })[0];
    zhCard(box, ZHD.ming.farbe, 'China · Ming-Dynastie', hs ? 'Hauptstadt: ' + hs.name.replace(/ \(.*\)/, '') : 'Ming-Reich',
      [y < 1421 ? 'Kaiser Yongle verlegt die Hauptstadt 1421 von Nanjing nach Peking.' : 'Seit 1421 ist Peking die Hauptstadt; Nanjing bleibt Nebenhauptstadt.',
       y >= 1407 && y <= 1427 ? 'Nordvietnam (Jiaozhi) ist 1407–1427 von den Ming besetzt.' : null, ZHD.ming.hinweis].filter(Boolean),
      mingAn() ? null : 'Ming-Reich einblenden', function () { setOn('han', true); });
    var eu = null; (ZHD.europa || []).forEach(function (e) { if (e.jahr <= y) eu = e; });
    if (eu) zhCard(box, '#6aa8e8', 'Zur gleichen Zeit in Europa · ' + eu.jahr + (eu.belegt === 'umstritten' ? ' · Datierung umstritten' : ''), eu.titel,
      [eu.text, 'Quelle: ' + eu.quelle], 'Auf dem Globus zeigen', function () { fly(eu.lat, eu.lng, 1.3); });
    else zhCard(box, '#6aa8e8', 'Zur gleichen Zeit in Europa', 'Portugal beginnt erst 1415 mit Fahrten an der Küste Afrikas.', null, null, null, 'none');
    zhCard(box, '#5fdc8a', 'Hintergrund', ZHD.info.titel, ZHD.info.absaetze.slice(0, 2), 'Weiterlesen', openZhBackground);
  }
  /* Erzählende Karte zur laufenden Fahrt: Häfen in Reihenfolge, erreichte abgehakt, aktuelles Ziel hervorgehoben */
  function zhErzKarte(box, v) {
    var d = el('div', 'card zherz'); d.style.setProperty('--c', ZH_COL[v.nr - 1]); d.dataset.nr = v.nr;
    d.appendChild(el('div', 'k', 'Gerade unterwegs · Fahrt ' + v.nr + ' von 7'));
    d.appendChild(el('div', 't', v.name));
    var ol = el('ol', 'zhstat');
    v.__reihe.forEach(function (o) { var li = el('li', null, o.name.replace(/ \(.*\)/, '')); li.dataset.id = o.id; ol.appendChild(li); });
    d.appendChild(ol);
    d.appendChild(el('p', null, v.hinweis));
    var b = el('button', null, 'Infokarte zur Fahrt'); b.type = 'button'; b.addEventListener('click', function () { openZhInfo(v); }); d.appendChild(b);
    box.appendChild(d);
    zhErzUpdate();
  }
  function zhErzUpdate() {
    document.querySelectorAll('.card.zherz').forEach(function (d) {
      var v = zhById('zh' + d.dataset.nr), q = penVon(v), f = q ? q.f : 1, ziel = false;
      d.querySelectorAll('.zhstat li').forEach(function (li) {
        var da = v.__hafen[li.dataset.id] <= f + 0.002;
        li.classList.toggle('da', da);
        li.classList.toggle('ziel', !da && !ziel && (ziel = true));
      });
    });
  }
  /* Spätmittelalter-Abschnitt der Zeitleiste: Fahrt-Balken in eigener Spur, Ereignisse in der China-Spur (Han) */
  /* Ming-Reich: folgt dem Schalter des Han-Reichs (China); fehlt das Han-Reich im Tafelbild, immer sichtbar */
  function mingAn() { return DATA.meta.han ? !!state.on.han : true; }
  function addMingLanes(lanes) {
    if (SEGS[1].aus) return;
    var lane = el('div', 'lane zhlane'); lane.dataset.r = 'zhenghe';
    ZHD.verbindungen.forEach(function (v) {
      var b = el('button', 'zhbar', String(v.nr)); b.type = 'button'; b.dataset.nr = v.nr;
      b.style.left = pct(v.von) + '%'; b.style.width = 'calc(' + (pct(v.bis) - pct(v.von)) + '% - 2px)';
      b.style.setProperty('--c', ZH_COL[v.nr - 1]); b.style.setProperty('--cbg', rgba(ZH_COL[v.nr - 1], 0.22));
      b.title = v.name + ': ' + v.stationen;
      b.addEventListener('click', function () { setYear(v.von); });
      lane.appendChild(b);
    });
    var nm = el('span', 'zhnm', 'Zheng He'); nm.style.left = SEGS[0].aus ? '0' : 'calc(' + SEGS[1].a * 100 + '% - 6px)'; lane.appendChild(nm);
    var china = lanes.querySelector('.lane[data-r="han"]');
    var evl = china || lane;
    ZHD.ereignisse.forEach(function (e) {
      var k = el('button', 'mk zhmk', String(e.jahr)); k.type = 'button'; k.dataset.y = e.jahr; k.style.left = pct(e.jahr) + '%';
      k.style.setProperty('--c', '#5fdc8a');
      k.title = 'China (Ming), ' + e.jahr + ': ' + e.titel;
      k.addEventListener('click', function () { setYear(e.jahr); toast(e.jahr + ': ' + e.titel + '. ' + e.text); });
      evl.appendChild(k);
    });
    var rom = lanes.querySelector('.lane[data-r="rom"]');
    (ZHD.europa || []).forEach(function (e) {
      if (!rom) return;
      var k = el('button', 'mk eumk', String(e.jahr)); k.type = 'button'; k.dataset.y = e.jahr; k.style.left = pct(e.jahr) + '%';
      k.style.setProperty('--c', '#6aa8e8');
      k.title = 'Europa (Portugal), ' + e.jahr + ': ' + e.titel;
      k.addEventListener('click', function () { setYear(e.jahr); toast(e.jahr + ': ' + e.titel + '. ' + e.text); });
      rom.appendChild(k);
    });
    lanes.insertBefore(lane, rom && rom.nextSibling && rom.nextSibling.nextSibling ? rom.nextSibling.nextSibling : null);
  }
  function updateMarkersMing() {
    var y = state.year, cur = null;
    document.querySelectorAll('.zhbar').forEach(function (b) {
      var v = zhById('zh' + b.dataset.nr);
      b.classList.toggle('on', zhAktiv(v, y)); b.classList.toggle('off', !ZH.on || !ZH.fahrt[v.nr]);
    });
    ZHD.ereignisse.forEach(function (e) { if (e.jahr <= y) cur = e; });
    document.querySelectorAll('.mk.zhmk').forEach(function (k) { k.classList.toggle('on', !!cur && +k.dataset.y === cur.jahr); });
    var eu = null; (ZHD.europa || []).forEach(function (e) { if (e.jahr <= y) eu = e; });
    document.querySelectorAll('.mk.eumk').forEach(function (k) { k.classList.toggle('on', state.epoche === 'ming' && !!eu && +k.dataset.y === eu.jahr); });
  }
  function buildZhChips() {
    var box = $('#zhChips');
    ZHD.verbindungen.forEach(function (v) {
      var b = el('button', 'chip zc on'); b.type = 'button'; b.dataset.nr = v.nr; b.setAttribute('aria-pressed', 'true'); b.disabled = !TRADE.on;
      b.style.setProperty('--c', ZH_COL[v.nr - 1]); b.style.setProperty('--cbg', rgba(ZH_COL[v.nr - 1], 0.25));
      b.appendChild(el('i')); b.appendChild(el('span', null, v.nr + '. Fahrt ' + v.von + '–' + String(v.bis).slice(2)));
      b.title = v.name + ': ' + v.stationen;
      b.addEventListener('click', function () { var f = {}; f[v.nr] = !ZH.fahrt[v.nr]; setState({ zh: { fahrten: f } }); });
      box.appendChild(b);
    });
  }

  /* ---------- Karawanenhandel: Kamel-Karawanen auf kurzen Etappen (handel.json → karawanen) ----------
     Vor dem Wendepunkt (Standard 220) ziehen sie auf den Etappen der Mittelroute, danach regional verteilt über Eurasien.
     Pause: langsames Ziehen. Play: schneller. Sprung (±10, Schieber): Karawanen rücken entsprechend weiter. */
  var CAMEL = '<svg viewBox="0 0 32 24" aria-hidden="true"><path fill="currentColor" d="M2 6.5L4.2 4h2.6l.8 1.6.8 4.9 2.1.7C11.5 6.8 13.4 5 15 5c1.8 0 2.6 2 3.2 3.6.6-2 2-3.2 3.6-3.2 2.8 0 4.4 3.2 5.2 6.2l2.5 1.8-.5 1-1.8-1c-.2 1.8-.8 3-1.6 3.6l.2 5.5h-1.6l-.4-4.9h-1.4l-.4 4.9h-1.6v-5.1h-5.8l-.4 5.1h-1.6l-.2-5.3-1.2-.2-.4 5.5H9.2l.2-6.5c-1-1-2-2.4-2.6-4L5.6 7.4l-2 .2z"/></svg>';
  var KAR = { nodes: {}, etappen: [], els: [], clock: 0, last: 0, raf: 0, plan: null, prevY: null };
  var KAR_SPRUNG = 0.035, KAR_PLAY = 0.25, KAR_RUHE = 0.025;   // Zyklen je Jahr bzw. je Sekunde
  function initKarawanen() {
    var K = HANDEL.karawanen;
    K.knoten.forEach(function (n) { n.kind = 'karawane'; KAR.nodes[n.id] = n; });
    KAR.etappen = K.etappen.map(function (e, i) {
      var a = KAR.nodes[e.von], b = KAR.nodes[e.nach], pts = dense(e.pfad), cum = [0];
      for (var j = 1; j < pts.length; j++) cum.push(cum[j - 1] + d3.geoDistance(pts[j - 1], pts[j]));
      return { i: i, a: a, b: b, haupt: !!e.haupt, von: Math.max(a.von, b.von, e.ab_jahr != null ? e.ab_jahr : -9999), bis: Math.min(a.bis, b.bis), pts: pts, cum: cum, len: cum[cum.length - 1] };
    });
  }
  function karPlan(y, tv) {
    var K = HANDEL.karawanen, res = { list: [], key: 'aus' };
    if (!K || state.epoche !== 'antike' || !TRADE.on || !TRADE.land || !TRADE.karawanen || y < K.von || y > K.bis) return res;
    var mrt = tv.routes.filter(function (rt) { return rt.v.id === K.route; })[0];
    if (!mrt) return res;                                   // nur wenn die Mittelroute zu sehen ist
    var nach = y >= K.ab, vis = [];
    mrt.parts.forEach(function (p) { vis.push.apply(vis, dense(p.pts)); });
    function near(n) { return vis.some(function (c) { return d3.geoDistance(c, [n.lng, n.lat]) < 0.055; }); }
    var avail = KAR.etappen.filter(function (e) { return y >= e.von && y <= e.bis && (nach || (e.haupt && near(e.a) && near(e.b))); });
    if (!avail.length) return res;
    var n = Math.min(nach ? K.max_nachher : K.max_vorher, 15);
    var bucket = nach ? Math.floor((y - K.ab) / 12) : 0;   // danach alle 12 Jahre neu verteilt: „ziehen durch Eurasien“
    for (var i = 0; i < n; i++) {
      var e = avail[(i * 5 + bucket * 3) % avail.length];
      res.list.push({ e: e, rev: (i + bucket) % 2 === 1, phase: (i * 0.618 + bucket * 0.27) % 1 });
    }
    res.key = (nach ? 'n' : 'v') + bucket + ':' + avail.map(function (e) { return e.i; }).join('.');
    return res;
  }
  function karNodeLabels(tv) {
    if (!tv.kar || !tv.kar.list.length) return [];
    var seen = {}, out = [];
    tv.kar.list.forEach(function (c) {
      [c.e.a, c.e.b].forEach(function (n) {
        if (seen[n.id]) return; seen[n.id] = 1;
        if (tv.places.some(function (o) { return d3.geoDistance([o.lng, o.lat], [n.lng, n.lat]) < 0.02; })) return;
        out.push(n);
      });
    });
    return out;
  }
  function karUpdate() {
    var plan = state.epoche === 'antike' && CUR_TV && CUR_TV.kar ? CUR_TV.kar : { list: [] }, L = $('#karLayer');
    KAR.plan = plan;
    while (KAR.els.length < plan.list.length) {
      var e = el('div', 'camel'); e.innerHTML = CAMEL;
      e.addEventListener('click', function () {
        var c = this.__c; if (c) { toast('🐪 Karawane zwischen ' + c.e.a.name + ' und ' + c.e.b.name + ': regionaler Zwischenhandel (Etappenhandel)'); openText(state.year >= HANDEL.karawanen.ab ? 'rueckgang' : 'seidenstrasse'); }
      });
      L.appendChild(e); KAR.els.push(e);
    }
    KAR.els.forEach(function (e, i) { e.__c = plan.list[i] || null; e.classList.toggle('off', !e.__c); });
    if (plan.list.length && !KAR.raf) { KAR.last = performance.now(); KAR.raf = requestAnimationFrame(karFrame); }
    if (!plan.list.length && KAR.raf) { cancelAnimationFrame(KAR.raf); KAR.raf = 0; }
  }
  function karYearJump(y) {
    if (KAR.prevY != null && !playTimer) KAR.clock += (y - KAR.prevY) * KAR_SPRUNG;
    KAR.prevY = y;
  }
  function karFrame(now) {
    KAR.raf = requestAnimationFrame(karFrame);
    var dt = Math.min(0.1, Math.max(0, (now - KAR.last) / 1000)); KAR.last = now;
    KAR.clock += dt * (playTimer ? KAR_PLAY : KAR_RUHE);
    karDraw();
  }
  function karDrawSoon() { if (KAR.plan && KAR.plan.list.length && !KAR.raf) karDraw(); }
  function karPoint(e, s) {
    var d = s * e.len, c = e.cum, j = 1;
    while (j < c.length - 1 && c[j] < d) j++;
    var seg = c[j] - c[j - 1], t = seg ? (d - c[j - 1]) / seg : 0;
    return d3.geoInterpolate(e.pts[j - 1], e.pts[j])(Math.max(0, Math.min(1, t)));
  }
  function karDraw() {
    var plan = KAR.plan, L = $('#karLayer'); if (!plan) return;
    L.hidden = mapOpen || state.epoche !== 'antike';
    if (L.hidden) return;
    var pov = globe.pointOfView(), gr = $('#globe').getBoundingClientRect();
    plan.list.forEach(function (c, i) {
      var e = KAR.els[i]; if (!e) return;
      var rate = 1 / Math.max(0.6, Math.min(2.2, c.e.len * 180 / Math.PI / 10));
      var u = ((KAR.clock * rate + c.phase) % 1 + 1) % 1, s, dir;
      if (u < 0.44) { s = u / 0.44; dir = 1; } else if (u < 0.5) { s = 1; dir = 0; } else if (u < 0.94) { s = 1 - (u - 0.5) / 0.44; dir = -1; } else { s = 0; dir = 0; }
      if (c.rev) { s = 1 - s; dir = -dir; }
      var p = karPoint(c.e, s);
      var sc = globe.getScreenCoords(p[1], p[0], 0.0016), x = sc.x + gr.left, yy = sc.y + gr.top;
      if (d3.geoDistance([pov.lng, pov.lat], p) > 1.35 || x < -20 || yy < -20 || x > innerWidth + 20 || yy > innerHeight + 20) { e.classList.add('hide'); return; }
      e.classList.remove('hide');
      e.style.transform = 'translate(' + x.toFixed(1) + 'px,' + yy.toFixed(1) + 'px)';
      if (dir) {
        var q = karPoint(c.e, Math.max(0, Math.min(1, s + dir * 0.03))), sq = globe.getScreenCoords(q[1], q[0], 0.0016);
        if (Math.abs(sq.x - sc.x) > 0.5) e.classList.toggle('flip', sq.x > sc.x);
      }
    });
  }

  /* ---------- Start: Linien von der Legende zum Reich ---------- */
  var intro = { on: false, raf: 0, timer: 0, els: {} };
  function startIntro() {
    var svg = $('#intro'), NS = 'http://www.w3.org/2000/svg';
    function mk(tag, attrs) { var e = document.createElementNS(NS, tag); for (var k in attrs) e.setAttribute(k, attrs[k]); svg.appendChild(e); return e; }
    ['rom', 'han'].filter(function (r) { return !!DATA.meta[r]; }).forEach(function (r) {
      intro.els[r] = {
        path: mk('path', { pathLength: 1 }),
        start: mk('circle', { r: 3.5, 'class': 'start' }),
        ring: mk('circle', { r: 5, 'class': 'ring' }),
        dot: mk('circle', { r: 5, 'class': 'dot' })
      };
    });
    intro.on = true;
    (function frame() {
      if (!intro.on) return;
      var pov = globe.pointOfView(), collapsed = $('#panel').classList.contains('collapsed');
      Object.keys(intro.els).forEach(function (r) {
        var e = intro.els[r], chip = $(r === 'rom' ? '#tglRom' : '#tglHan');
        var z = M(r).zentrum, ang = d3.geoDistance([pov.lng, pov.lat], z);
        var rc0 = chip.getBoundingClientRect(), pb = $('#panelBody').getBoundingClientRect();
        var inPanel = rc0.width > 0 && rc0.top >= pb.top - 2 && rc0.bottom <= pb.bottom + 2;   // Menü ausgeblendet (Schüleransicht): keine Linie
        var vis = !collapsed && inPanel && !mapOpen && state.on[r] && regionsAt(r, state.year).length && ang < 1.35;
        var op = vis ? Math.min(1, (1.35 - ang) / 0.25) : 0;
        ['path', 'start', 'ring', 'dot'].forEach(function (k) { e[k].setAttribute('visibility', op ? 'visible' : 'hidden'); });
        if (!op) return;
        var rc = chip.getBoundingClientRect(), x1 = rc.right, y1 = rc.top + rc.height / 2;
        var p = globe.getScreenCoords(z[1], z[0], 0.0016), x2 = p.x, y2 = p.y;
        var dx = Math.max(60, (x2 - x1) * 0.5);
        e.path.setAttribute('d', 'M' + x1 + ',' + y1 + ' C' + (x1 + dx) + ',' + y1 + ' ' + (x2 - dx * 0.4) + ',' + y2 + ' ' + x2 + ',' + y2);
        e.path.setAttribute('stroke-opacity', op);
        e.start.setAttribute('cx', x1); e.start.setAttribute('cy', y1);
        [e.ring, e.dot].forEach(function (c) { c.setAttribute('cx', x2); c.setAttribute('cy', y2); });
      });
      intro.raf = requestAnimationFrame(frame);
    })();
    intro.timer = setTimeout(stopIntro, 14000);
    var cvs = globe.renderer().domElement;
    function first() { cvs.removeEventListener('pointerdown', first); cvs.removeEventListener('wheel', first); setTimeout(stopIntro, 1200); }
    cvs.addEventListener('pointerdown', first); cvs.addEventListener('wheel', first, { passive: true });
  }
  function stopIntro() {
    if (!intro.on) return;
    clearTimeout(intro.timer);
    var svg = $('#intro'); svg.classList.add('off');
    setTimeout(function () { intro.on = false; cancelAnimationFrame(intro.raf); svg.innerHTML = ''; }, 900);
  }

  /* ---------- Kompakte Ansicht (Smartphone, Tablet hochkant) ----------
     Menü und Infoband werden zu Schubladen: anfangs zu, immer nur eine offen, Tipp auf den Globus schließt sie. */
  var COMPACT_MQ = window.matchMedia('(max-width: 760px), (max-height: 560px), (max-width: 1024px) and (orientation: portrait)');
  function compact() { return COMPACT_MQ.matches; }
  function homeAlt() {
    var g = $('#globe'), asp = (g.clientWidth || innerWidth) / (g.clientHeight || innerHeight);
    var h = g.clientHeight || innerHeight;
    if (asp < 1) return Math.min(4.2, 2.7 * 0.72 / asp);
    return h < 420 ? 1.75 : h < 600 ? 2.2 : 2.7;     // flache Querformate: näher heran
  }

  /* ---------- Menü einklappen ---------- */
  function setPanel(collapsed, nosave) {
    var p = $('#panel'), b = $('#panelToggle');
    p.classList.toggle('collapsed', collapsed);
    b.setAttribute('aria-expanded', !collapsed);
    b.title = collapsed ? 'Menü ausklappen' : 'Menü einklappen';
    if (globe) setTimeout(scheduleTagSides, 30);
    if (!collapsed && compact() && !$('#side').classList.contains('collapsed')) setSide(true, true);
    if (!nosave && !compact()) try { localStorage.setItem('tafelbild.panel', collapsed ? '0' : '1'); } catch (e) {}
  }

  /* ---------- Infoband rechts einklappen ---------- */
  function setSide(collapsed, nosave) {
    var p = $('#side'), b = $('#sideToggle');
    p.classList.toggle('collapsed', collapsed);
    b.setAttribute('aria-expanded', !collapsed);
    b.title = collapsed ? 'Infoband ausklappen' : 'Infoband einklappen';
    if (globe) setTimeout(scheduleTagSides, 30);
    if (!collapsed && compact() && !$('#panel').classList.contains('collapsed')) setPanel(true, true);
    if (!nosave && !compact()) try { localStorage.setItem('tafelbild.side', collapsed ? '0' : '1'); } catch (e) {}
  }
  function applyCompact() {
    document.documentElement.classList.toggle('compact', compact());
    if (compact()) { setPanel(true, true); setSide(true, true); }
    // Abstand an das neue Format anpassen – aber nicht, wenn inzwischen eine Kamera gesetzt wurde (Fokus, Lehreransicht)
    var geplant = Date.now();
    if (globe && !mapOpen) setTimeout(function () {
      if (KAMERA_GESETZT > geplant) return;
      var pv = globe.pointOfView(); globe.pointOfView({ lat: pv.lat, lng: pv.lng, altitude: homeAlt() }, 600);
    }, 250);
    else {
      var lp = null, ls = null;
      try { lp = localStorage.getItem('tafelbild.panel'); ls = localStorage.getItem('tafelbild.side'); } catch (e) {}
      setPanel(lp === '0', true); setSide(ls === '0', true);
    }
  }

  /* ---------- Bedienung ---------- */
  function bind() {
    $('#sideToggle').addEventListener('click', function () { setSide(!$('#side').classList.contains('collapsed')); });
    $('#panelToggle').addEventListener('click', function () { setPanel(!$('#panel').classList.contains('collapsed')); });
    applyCompact();
    if (COMPACT_MQ.addEventListener) COMPACT_MQ.addEventListener('change', applyCompact); else COMPACT_MQ.addListener(applyCompact);
    // Kompakt: Tipp auf den Globus schließt offene Schubladen
    globe.renderer().domElement.addEventListener('pointerdown', function () {
      if (!compact()) return;
      setPanel(true, true); setSide(true, true);
    });
    // Kompakt: nach Auswahl einer Route/Karte die Schublade schließen, damit man das Ergebnis sieht
    $('#routeList').addEventListener('click', function () { if (compact()) setPanel(true, true); });
    $('#cards').addEventListener('click', function (e) { if (compact() && e.target.closest('button')) setSide(true, true); });
    $('#fokusBtns').addEventListener('click', function (e) { if (compact() && e.target.closest('button')) setPanel(true, true); });
    $('#modeSat').addEventListener('click', function () { setState({ ansicht: 'sat' }); });
    $('#modeSchem').addEventListener('click', function () { setState({ ansicht: 'schem' }); });
    function setAll(v) {
      var o = {}; DATA.reihen.forEach(function (r) { o[r] = v; }); setState({ reiche: o });
    }
    $('#allOn').addEventListener('click', function () { setAll(true); });
    $('#allOff').addEventListener('click', function () { setAll(false); });
    function setLanes(collapsed) {
      $('#lanes').classList.toggle('collapsed', collapsed);
      $('#lanesToggle').setAttribute('aria-expanded', !collapsed);
      $('#lanesToggle').classList.toggle('closed', collapsed);
      try { localStorage.setItem('tafelbild.lanes', collapsed ? '0' : '1'); } catch (e) {}
    }
    $('#lanesToggle').addEventListener('click', function () { setLanes(!$('#lanes').classList.contains('collapsed')); });
    try { if (localStorage.getItem('tafelbild.lanes') === '0') setLanes(true); } catch (e) {}
    // Zeitleiste verkleinern: der Globus wächst in den frei werdenden Platz (über --tlh) und bleibt mittig
    function setTlMini(mini, nosave) {
      $('#timeline').classList.toggle('mini', mini);
      var b = $('#tlToggle'); b.setAttribute('aria-expanded', !mini);
      b.title = mini ? 'Zeitleiste vergrößern' : 'Zeitleiste verkleinern';
      if (!nosave) try { localStorage.setItem('tafelbild.tl', mini ? '0' : '1'); } catch (e) {}
      setTimeout(scheduleTagSides, 60);
    }
    $('#tlToggle').addEventListener('click', function () { setTlMini(!$('#timeline').classList.contains('mini')); });
    try { if (localStorage.getItem('tafelbild.tl') === '0') setTlMini(true, true); } catch (e) {}
    $('#tglRom').addEventListener('click', function () { setState({ reiche: { rom: !state.on.rom } }); });
    $('#tglHan').addEventListener('click', function () { setState({ reiche: { han: !state.on.han } }); });
    $('#tglOrte').addEventListener('click', function () { setState({ globus: { orte: !state.orte } }); });
    $('#tglVw').addEventListener('click', function () {
      setState({ globus: { vw: !state.vw } });
      if (state.vw && state.epoche === 'antike' && (state.year < 370 || state.year > 480)) toast('Völkerwanderung: Die Züge laufen vor allem 375–456 n. Chr. Spiel die Zeitleiste ab 370 ab.');
    });
    $('#tglSchl').addEventListener('click', function () { setState({ globus: { schlachten: !state.schlachten } }); });
    $('#tglLimes').addEventListener('click', function () {
      setState({ globus: { limes: !state.limes } });
      if (state.limes && !state.on.rom) toast('Grenzanlagen erscheinen mit dem Römischen Reich – bitte „Römisches Reich“ einblenden.');
      else if (state.limes && state.epoche === 'antike' && !limesSchluessel(state.year)) toast('Grenzanlagen: Hadrianswall ab 122, Limes in Germanien etwa 100–260 n. Chr.');
    });
    function setTrade(k, v) { var o = {}; o[k] = v; setState({ handel: o }); }
    $('#tglHandel').addEventListener('click', function () { setTrade('on', !TRADE.on); });
    $('#tglLand').addEventListener('click', function () { setTrade('land', !TRADE.land); });
    $('#tglSee').addEventListener('click', function () { setTrade('see', !TRADE.see); });
    $('#tglWaren').addEventListener('click', function () { setTrade('waren', !TRADE.waren); });
    $('#tglGes').addEventListener('click', function () { setTrade('gesandt', !TRADE.gesandt); });
    $('#tglKar').addEventListener('click', function () { setTrade('karawanen', !TRADE.karawanen); });
    $('#tglSchiff').addEventListener('click', function () { setTrade('schiff', !TRADE.schiff); });
    $('#tglHanSeide').addEventListener('click', function () { setTrade('hanseide', !TRADE.hanseide); });
    $('#btnNetzQuellen').addEventListener('click', function () { openNetzQuellen(); });
    // Entdeckungsfahrten des Zheng He (unter Handel & Austausch)
    $('#tglZh').addEventListener('click', function () { setState({ zh: { on: !ZH.on } }); });
    $('#btnZhInfo').addEventListener('click', function () { openText('zhenghe'); });
    $('#tglBilder').addEventListener('click', function () { setState({ zh: { bilder: !BILDER.an } }); });
    $('#tglStr').addEventListener('click', function () { setTrade('strassen', !TRADE.strassen); });
    [['#tglStrEhem', 'ehemals'], ['#tglStrAnim', 'animieren']].forEach(function (x) {
      $(x[0]).addEventListener('click', function () { var o = {}; o[x[1]] = !STR_OPT[x[1]]; setState({ strassen: o }); });
    });
    $('#btnZhWaren').addEventListener('click', function () { openWaren(ZHD); });
    $('#btnZhGo').addEventListener('click', function () { if (state.epoche !== 'ming') setYear(SEGS[1].start); else fly(8, 82, homeAlt()); });
    $('#year').addEventListener('change', function () { this.value = sliderPos(state.year); });   // Schieber im Zeitsprung einrasten
    $('#btnWaren').addEventListener('click', openWaren);
    $('#tinfoClose').addEventListener('click', closeInfo);
    $('#tinfo').addEventListener('click', function (e) { if (e.target === this) closeInfo(); });
    $('#wmodalClose').addEventListener('click', warenSchliessen);
    $('#wmodal').addEventListener('click', function (e) { if (e.target === this) warenSchliessen(); });
    $('#tglRot').addEventListener('click', function () { setState({ drehen: !state.rotate }); });
    $('#tglStandort').addEventListener('click', toggleStandort);
    $('#year').addEventListener('input', function (e) { setState({ jahr: yearAt(+e.target.value / 1000) }, { schieber: true }); });
    $('#play').addEventListener('click', togglePlay);
    $('#yMinus').addEventListener('click', function () { setState({ jahr: plusJahre(state.year, -10) }); });
    $('#yPlus').addEventListener('click', function () { setState({ jahr: plusJahre(state.year, 10) }); });
    $('#mapClose').addEventListener('click', closeMap);
    $('#tabVig').addEventListener('click', function () { setRollView('vig'); });
    $('#tabKarte').addEventListener('click', function () { setRollView('karte'); });
    $('.roll-tabs').addEventListener('keydown', function (e) {   // Pfeiltasten wechseln zwischen den Reitern
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      e.preventDefault();
      setRollView(rollView === 'vig' ? 'karte' : 'vig'); $(rollView === 'vig' ? '#tabVig' : '#tabKarte').focus();
    });
    $('#mapOverlay').addEventListener('click', function (e) { if (e.target === this) closeMap(); });
    $('#btnInfo').addEventListener('click', function () { modalOeffnen('hilfe'); });
    $('#modalClose').addEventListener('click', modalSchliessen);
    $('#modal').addEventListener('click', function (e) { if (e.target === this) modalSchliessen(); });
    // Lehrerhinweise: Fenster mit Reitern (Pfeiltasten wechseln den Reiter)
    $('#btnLehrer').addEventListener('click', function () { modalOeffnen('lehrer'); });
    $('#lmodalClose').addEventListener('click', modalSchliessen);
    $('#lmodal').addEventListener('click', function (e) { if (e.target === this) modalSchliessen(); });
    bindRest();
  }
  /* Lehrerhinweise: je Reiter eine Markdown-Datei aus dem Tafelbild-Ordner (tafelbild.json → lehrerhinweise) */
  function lehrerReiterBauen(lh, ordner) {
    var tabs = $('#ltabs'), panels = $('#lpanels'); tabs.innerHTML = ''; panels.innerHTML = '';
    $('#lquelle').textContent = ordner + lh.ordner + '*.md';
    lh.reiter.forEach(function (r, i) {
      var t = el('button', null, r.titel); t.type = 'button'; t.setAttribute('role', 'tab'); t.id = 'lt-' + r.id;
      t.setAttribute('aria-controls', 'lp-' + r.id); t.setAttribute('aria-selected', i === 0); t.tabIndex = i === 0 ? 0 : -1; tabs.appendChild(t);
      var p = el('section', 'lpanel'); p.setAttribute('role', 'tabpanel'); p.id = 'lp-' + r.id; p.setAttribute('aria-labelledby', t.id);
      p.setAttribute('data-md', ordner + lh.ordner + r.datei); p.hidden = i > 0; p.appendChild(el('p', 'hint', 'Wird geladen …')); panels.appendChild(p);
    });
    LEHRER_GELADEN = false;
    var ltabs = Array.prototype.slice.call(document.querySelectorAll('.ltabs [role="tab"]'));
    function lehrerReiter(t) {
      ltabs.forEach(function (x) {
        var an = x === t; x.setAttribute('aria-selected', an); x.tabIndex = an ? 0 : -1;
        document.getElementById(x.getAttribute('aria-controls')).hidden = !an;
      });
      t.focus({ preventScroll: true });
    }
    ltabs.forEach(function (t, i) {
      t.addEventListener('click', function () { lehrerReiter(t); });
      t.addEventListener('keydown', function (e) {
        var n = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
        if (n) { e.preventDefault(); e.stopPropagation(); lehrerReiter(ltabs[(i + n + ltabs.length) % ltabs.length]); }
      });
    });
  }
  function bindRest() {
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        if (warenSchliessen()) return;
        if (modalSchliessen()) return;
        if (closeInfo()) return;
        closeMap(); return;
      }
      if (e.target && (/^(INPUT|SELECT|TEXTAREA)$/.test(e.target.tagName) || (e.target.closest && e.target.closest('.troute,.tplace,.wchips-map,.roll-tabs')))) return;
      if (mapOpen && rollView === 'vig') return;   // in den Vignetten verstellen Pfeiltasten nicht das Jahr
      if (e.key === 'ArrowLeft') setState({ jahr: plusJahre(state.year, e.shiftKey ? -10 : -1) });
      if (e.key === 'ArrowRight') setState({ jahr: plusJahre(state.year, e.shiftKey ? 10 : 1) });
      if (e.key === ' ' && !mapOpen && e.target.tagName !== 'BUTTON') { e.preventDefault(); togglePlay(); }
    });
  }


  /* ---------- Zentraler Zustand ----------
     Der gesamte sichtbare Zustand steht in einem serialisierbaren Objekt (getState). Änderungen laufen über
     setState(teil) → applyState(teil, {quelle}). Interne Funktionen (setYear, Fenster öffnen/schließen) melden
     Änderungen an die Abonnenten (abonnieren). Format: docs/ARCHITEKTUR.md. */
  function handelSetzen(k, v) {
    TRADE[k] = v;
    var b = $({ on: '#tglHandel', land: '#tglLand', see: '#tglSee', waren: '#tglWaren', gesandt: '#tglGes', karawanen: '#tglKar', strassen: '#tglStr', schiff: '#tglSchiff', hanseide: '#tglHanSeide' }[k]);
    if (b) { b.classList.toggle('on', v); b.setAttribute('aria-pressed', v); }
    if (k === 'on') {
      $('#handelSub').classList.toggle('off', !v);
      document.querySelectorAll('#handelSub button').forEach(function (x) { x.disabled = !v; });
      if (v && !ZH.on) document.querySelectorAll('#zhChips .chip').forEach(function (x) { x.disabled = true; });
      if (!v) closeInfo();
    }
    if (k === 'strassen') $('#strOpt').classList.toggle('off', !v);
  }
  function chipSetzen(sel, v) { var b = $(sel); if (b) { b.classList.toggle('on', v); b.setAttribute('aria-pressed', v); } }
  function kopie(o) { return o == null ? o : JSON.parse(JSON.stringify(o)); }
  function gleich(a, b) { return JSON.stringify(a == null ? null : a) === JSON.stringify(b == null ? null : b); }
  function netzeZustand() { var o = {}; netzeVerfuegbar().forEach(function (n) { o[n.id] = !!NETZE.an[n.id]; }); return o; }
  function getState() {
    var pov = globe ? globe.pointOfView() : { lat: 36, lng: 62, altitude: 2.7 };
    var reiche = {}; DATA.reihen.forEach(function (r) { reiche[r] = !!state.on[r]; });
    var fahrten = {}; (ZHD ? ZHD.verbindungen : []).forEach(function (v) { fahrten[v.nr] = !!ZH.fahrt[v.nr]; });
    return {
      v: 1, tafelbild: window.CG_TAFELBILD ? window.CG_TAFELBILD.id : null,
      jahr: state.year, ansicht: state.mode,
      kamera: { lat: Math.round(pov.lat * 1000) / 1000, lng: Math.round(pov.lng * 1000) / 1000, alt: Math.round(pov.altitude * 1000) / 1000 },
      drehen: state.rotate,
      reiche: reiche,
      globus: { orte: state.orte, schlachten: state.schlachten, vw: state.vw, limes: state.limes },
      handel: { on: TRADE.on, land: TRADE.land, see: TRADE.see, waren: TRADE.waren, gesandt: TRADE.gesandt, karawanen: TRADE.karawanen, strassen: TRADE.strassen, schiff: TRADE.schiff, hanseide: TRADE.hanseide },
      strassen: { ehemals: STR_OPT.ehemals, animieren: STR_OPT.animieren },
      zh: { on: ZH.on, fahrten: fahrten, bilder: BILDER.an },
      netze: netzeZustand(),
      niveau: TX_NIV,
      fenster: kopie(FENSTER)
    };
  }
  /* Teilzustand anwenden. opt.quelle: 'lokal' (eigene Bedienung), 'lehrer' (Live-Session), 'tafelbild' (Start);
     opt.dauer: Kameraflug in ms; opt.schieber: Jahr kommt vom Schieber (Schieberwert nicht zurücksetzen). */
  function applyState(t, opt) {
    opt = opt || {}; if (!t) return;
    var fern = opt.quelle === 'lehrer' || opt.quelle === 'tafelbild';
    if (fern) ZUSTAND.fern++;
    ZUSTAND.still++;
    try {
      var neu = false, lanes = false;
      if (t.ansicht && t.ansicht !== state.mode) { state.mode = t.ansicht; applyMode(); }
      if (t.reiche) Object.keys(t.reiche).forEach(function (r) {
        if (!DATA.meta[r] || !!t.reiche[r] === !!state.on[r]) return;
        setOn(r, !!t.reiche[r], true); neu = true; if (!M(r).haupt) lanes = true;
      });
      if (t.globus) {
        if ('orte' in t.globus && !!t.globus.orte !== state.orte) { state.orte = !!t.globus.orte; chipSetzen('#tglOrte', state.orte); neu = true; }
        if ('vw' in t.globus && !!t.globus.vw !== state.vw) { state.vw = !!t.globus.vw; chipSetzen('#tglVw', state.vw); neu = true; }
        if ('limes' in t.globus && !!t.globus.limes !== state.limes) { state.limes = !!t.globus.limes; chipSetzen('#tglLimes', state.limes); neu = true; }
        if ('schlachten' in t.globus && !!t.globus.schlachten !== state.schlachten) {
          state.schlachten = !!t.globus.schlachten; chipSetzen('#tglSchl', state.schlachten); $('#lanes').classList.toggle('noschl', !state.schlachten); neu = true;
        }
      }
      if ('drehen' in t && !!t.drehen !== state.rotate) { state.rotate = !!t.drehen; chipSetzen('#tglRot', state.rotate); globe.controls().autoRotate = state.rotate && !mapOpen; }
      if (t.handel) ['on', 'land', 'see', 'waren', 'gesandt', 'karawanen', 'strassen', 'schiff', 'hanseide'].forEach(function (k) {
        if (k in t.handel && !!t.handel[k] !== !!TRADE[k]) { handelSetzen(k, !!t.handel[k]); neu = true; }
      });
      if (t.strassen) ['ehemals', 'animieren'].forEach(function (k) {
        if (k in t.strassen && !!t.strassen[k] !== !!STR_OPT[k]) { STR_OPT[k] = !!t.strassen[k]; chipSetzen(k === 'ehemals' ? '#tglStrEhem' : '#tglStrAnim', STR_OPT[k]); neu = true; }
      });
      if (t.zh) {
        if ('on' in t.zh && !!t.zh.on !== ZH.on) {
          ZH.on = !!t.zh.on; chipSetzen('#tglZh', ZH.on);
          document.querySelectorAll('#zhChips .chip').forEach(function (x) { x.disabled = !ZH.on || !TRADE.on; }); neu = true;
        }
        if (t.zh.fahrten) Object.keys(t.zh.fahrten).forEach(function (nr) {
          if (!!t.zh.fahrten[nr] === !!ZH.fahrt[nr]) return;
          ZH.fahrt[nr] = !!t.zh.fahrten[nr]; chipSetzen('#zhChips .chip[data-nr="' + nr + '"]', ZH.fahrt[nr]); neu = true;
        });
        if ('bilder' in t.zh && !!t.zh.bilder !== BILDER.an) { BILDER.an = !!t.zh.bilder; chipSetzen('#tglBilder', BILDER.an); PENS.forEach(function (q) { zhSchiffStil(q.schiff); }); }
      }
      if (t.netze) Object.keys(t.netze).forEach(function (id) {
        var m = netzMeta(id); if (!m || m.status !== 'verfuegbar' || !!t.netze[id] === !!NETZE.an[id]) return;
        netzSetzen(id, !!t.netze[id]); neu = true;
      });
      if (t.niveau && t.niveau !== TX_NIV && /^[ABC]$/.test(t.niveau)) {
        TX_NIV = t.niveau; try { localStorage.setItem('tafelbild.niveau', TX_NIV); } catch (e) {}
        if (FENSTER.info && FENSTER.info.art === 'text' && !('fenster' in t)) infoOeffnen(FENSTER.info);
      }
      if (lanes) buildLanes();
      ZUSTAND.kameraFolgt = !!(t.kamera && isFinite(t.kamera.lat));
      if (t.jahr != null && t.jahr !== state.year) { if (neu) lastKey = ''; setYear(t.jahr, !!opt.schieber); }
      else if (neu) { lastKey = ''; setYear(state.year); }
      if (t.kamera && isFinite(t.kamera.lat) && isFinite(t.kamera.lng)) {
        KAMERA_GESETZT = Date.now();
        globe.pointOfView({ lat: t.kamera.lat, lng: t.kamera.lng, altitude: t.kamera.alt || homeAlt() }, opt.dauer != null ? opt.dauer : 0);
      }
      if ('fenster' in t) fensterAnwenden(t.fenster || {});
    } finally {
      ZUSTAND.kameraFolgt = false;
      ZUSTAND.still--;
      if (fern) ZUSTAND.fern--;
    }
    zustandGemeldet(opt.quelle);
  }
  function setState(t, opt) { applyState(t, Object.assign({ quelle: 'lokal' }, opt || {})); }
  function abonnieren(fn) { ZUSTAND.hoerer.push(fn); return function () { ZUSTAND.hoerer = ZUSTAND.hoerer.filter(function (x) { return x !== fn; }); }; }
  function zustandGemeldet(quelle) {
    if (ZUSTAND.still || !ZUSTAND.hoerer.length) return;
    var q = quelle || (ZUSTAND.fern ? 'lehrer' : 'lokal');
    ZUSTAND.hoerer.forEach(function (fn) { try { fn(q); } catch (e) { console.error(e); } });
  }
  /* Fenster aus einer Beschreibung öffnen bzw. schließen */
  function infoOeffnen(d) {
    if (!d) return;
    var finde = function (L, id) { return (L || []).filter(function (x) { return x.id === id; })[0]; };
    if (d.art === 'route') { var v = routeById(d.id); if (v) openTradeInfo(v); }
    else if (d.art === 'ort') { var o = finde(HANDEL.orte, d.id); if (o) openPlaceInfo(o); }
    else if (d.art === 'kontakt') { var k = finde(HANDEL.kontakte, d.id); if (k) openKontaktInfo(k); }
    else if (d.art === 'zh') { var z = zhById(d.id); if (z) openZhInfo(z); }
    else if (d.art === 'zhhafen') { var h = finde(ZHD.orte, d.id); if (h) openZhHafen(h); }
    else if (d.art === 'zhhintergrund') openZhBackground();
    else if (d.art === 'orbis') openOrbisInfo(d.id ? finde(ORBIS_OBJ, d.id) || null : null);
    else if (d.art === 'strasse') { var sx = finde(STR_OBJ, d.id); if (sx) openStrassenLinie(sx); }
    else if (d.art === 'strassen') openStrassenInfo();
    else if (d.art === 'hanstation') { var hs = HANSEIDE && finde(HANSEIDE.stationen, d.id); if (hs) openHanStation(hs); }
    else if (d.art === 'limes') { var la = LIMES && finde(LIMES.abschnitte, d.id); if (la) openLimes(la, d.kastell ? LIMES.kastelle.filter(function (k) { return k.name === d.kastell; })[0] : null); }
    else if (d.art === 'hanlinie') { var hl = HANSEIDE && finde(HANSEIDE.linien, d.id); if (hl) openHanLinie(hl); }
    else if (d.art === 'netzquellen') openNetzQuellen();
    else if (d.art === 'netzlinie' || d.art === 'netzort') netzLaden(d.netz).then(function (nd) {
      if (!nd) return;
      if (d.art === 'netzort') { var no = finde(nd.orte, d.id); if (no) openNetzOrt(no); }
      else { var nl = finde(nd.linien, d.id); if (nl) openNetzLinie(nl, netzMeta(d.netz)); }
    });
    else if (d.art === 'text') openText(d.id, d.zurueck);
  }
  function modalOeffnen(id) {
    FENSTER.modal = id;
    $('#modal').hidden = id !== 'hilfe'; $('#lmodal').hidden = id !== 'lehrer';
    if (id === 'lehrer') { lehrerLaden(); $('.ltabs [aria-selected="true"]').focus({ preventScroll: true }); }
    zustandGemeldet();
  }
  function modalSchliessen() {
    if ($('#modal').hidden && $('#lmodal').hidden) return false;
    $('#modal').hidden = true; $('#lmodal').hidden = true; FENSTER.modal = null; zustandGemeldet(); return true;
  }
  function fensterAnwenden(f) {
    var r = f.rolle || null, a = FENSTER.rolle;
    if (!r && a) closeMap();
    else if (r && (!a || a.reich !== r.reich)) { if (mapOpen || closeTimer) finishClose(); openMap(r.reich, r.reiter); }
    if (r && FENSTER.rolle) {
      if (r.vignette != null && r.vignette !== FENSTER.rolle.vignette) { Vignetten.setzen(r.reich, r.vignette); FENSTER.rolle.vignette = r.vignette; renderVignetten(r.reich); }
      if (r.reiter && r.reiter !== FENSTER.rolle.reiter) setRollView(r.reiter);
    }
    if (!gleich(f.info, FENSTER.info)) { if (f.info) infoOeffnen(f.info); else closeInfo(); }
    if ((f.waren || null) !== FENSTER.waren) { if (f.waren) openWaren(f.waren === 'zh' ? ZHD : HANDEL); else warenSchliessen(); }
    if ((f.modal || null) !== FENSTER.modal) { if (f.modal) modalOeffnen(f.modal); else modalSchliessen(); }
  }



  /* ---------- Frühe Hochkulturen und Zeitraum ----------
     data/fruehe_reiche.json (build_fruehe_kulturen.py) wird zu den Kerndaten hinzugefügt. Ein Tafelbild lädt nur Reiche,
     deren Lebenszeit in seinen Zeitraum fällt („relevanter Ausschnitt“); der freie Modus zeigt alles. */
  function reicheErgaenzen(f) {
    if (!f || !f.meta) return;
    Object.keys(f.meta).forEach(function (r) { DATA.meta[r] = Object.assign({ frueh: true }, f.meta[r]); });
    DATA.reihen = DATA.reihen.concat(f.reihen || Object.keys(f.meta));
    ['regionen', 'ereignisse', 'schlachten', 'orte'].forEach(function (k) { DATA[k] = (DATA[k] || []).concat(f[k] || []); });
  }
  function reicheFiltern(tb) {
    var z = tb && tb.zeitraum; if (!z) return;
    var weg = {}, liste = tb.reiche && Array.isArray(tb.reiche.verfuegbar) ? tb.reiche.verfuegbar : null;
    DATA.reihen.forEach(function (r) {
      var m = DATA.meta[r];
      if (m.bis <= z.von || m.von >= z.bis) weg[r] = 1;
      // frühe Hochkulturen nur, wenn das Tafelbild in diese Zeit reicht oder sie ausdrücklich nennt
      else if (m.frueh && z.von >= SEGS[0].von && !(liste && liste.indexOf(r) >= 0)) weg[r] = 1;
    });
    if (!Object.keys(weg).length) return;
    DATA.reihen = DATA.reihen.filter(function (r) { return !weg[r]; });
    Object.keys(weg).forEach(function (r) { delete DATA.meta[r]; });
    DATA.regionen = DATA.regionen.filter(function (f) { return !weg[f.properties.reich]; });
    DATA.ereignisse = DATA.ereignisse.filter(function (e) { return !weg[e.reich]; });
    DATA.orte = DATA.orte.filter(function (o) { return !weg[o.reich]; });
    DATA.schlachten = DATA.schlachten.filter(function (s) { return s.reiche.some(function (r) { return !weg[r]; }); });
  }
  /* Reichen geladene Reiche vor 300 v. Chr. zurück, bekommt der erste Abschnitt einen Vorlauf mit eigenem Maßstab */
  function zeitleisteEinrichten() {
    var frueh = Math.min.apply(null, DATA.reihen.map(function (r) { return DATA.meta[r].von; }));
    var tb = window.CG && CG.tafelbild;
    if (tb && tb.zeitraum) frueh = Math.max(frueh, tb.zeitraum.von);
    $('#fruehSec').hidden = !DATA.reihen.some(function (r) { return DATA.meta[r].frueh; });
    if (frueh >= SEGS[0].von) return;
    var von = Math.floor(frueh / 500) * 500, S = SEGS[0];
    S.teile = [
      { von: von, bis: S.von, a: 0, b: 0.2, takt: 12, tick: 500, major: 1000, alt: 1000, start: -2560, kurz: true,
        name: 'Frühe Hochkulturen', sub: 'Ägypten, Mesopotamien, Indus, China' },
      { von: S.von, bis: S.bis, a: 0.2, b: S.b, takt: S.takt, tick: S.tick, major: S.major, alt: S.alt, start: S.start, name: S.name, sub: S.sub }
    ];
    S.von = von; YMIN = Math.min(YMIN, von);
  }
  /* Freies Erkunden (ohne Tafelbild-Zeitraum): Die Lücke 480–1400 wird zum Teil „Mittelalter“ mit eigenem Maßstab,
     damit die mittelalterlichen Netze (Tang, Levante, Mongolenzeit …) erreichbar sind. Tafelbilder behalten ihren Zuschnitt. */
  function mittelalterEinrichten() {
    var tb = window.CG && CG.tafelbild; if (tb && tb.zeitraum) return;
    var S = SEGS[0], T = SEGS[1], ende = 0.64, f = function (x) { return x * ende / S.b; };
    var basis = S.teile || [{ von: S.von, bis: S.bis, a: S.a, b: S.b, takt: S.takt, tick: S.tick, major: S.major, alt: S.alt, start: S.start, name: S.name, sub: S.sub }];
    basis.forEach(function (t) { t.a = f(t.a); t.b = f(t.b); });
    basis.push({ von: S.bis, bis: T.von, a: ende, b: T.a, takt: 30, tick: 100, major: 200, alt: 400, start: 700, kurz: true, mittel: true,
      name: 'Mittelalter', sub: 'Tang, Kalifate, Mongolenzeit' });
    S.teile = basis; S.b = T.a; S.bis = T.von;
  }
  /* Abschnitte außerhalb des Tafelbild-Zeitraums ausblenden; bleibt einer übrig, nimmt er die ganze Breite ein */
  function abschnitteZuschneiden() {
    var tb = window.CG && CG.tafelbild, z = tb && tb.zeitraum; if (!z) return;
    YMIN = Math.max(YMIN, z.von); YMAX = Math.min(YMAX, z.bis);
    SEGS.forEach(function (S) { S.aus = S.bis < z.von || S.von > z.bis; });
    var sichtbar = SEGS.filter(function (S) { return !S.aus; });
    if (sichtbar.length !== 1) return;
    var S = sichtbar[0], a0 = S.a, b0 = S.b, f = function (x) { return (x - a0) / (b0 - a0); };
    (S.teile || []).forEach(function (t) { t.a = f(t.a); t.b = f(t.b); });
    S.a = 0; S.b = 1;
    SEGS.forEach(function (T) { if (T.aus) { T.a = T.b = T === SEGS[0] ? 0 : 1; } });
    if (state.year < YMIN || state.year > YMAX) { state.year = S.start; if (S.ep !== state.epoche) ZUSTAND.kameraFolgt = true; }   // Startansicht kommt vom Tafelbild
  }

  /* ---------- Tafelbild anwenden (js/tafelbild.js → window.CG.tafelbild) ----------
     Titel, verfügbare Reiche/Ebenen, Fokuspunkte, Lehrerhinweise, Zeitraum und Startzustand. */
  var EBENEN_SEL = { orte: '#tglOrte', schlachten: '#tglSchl', vw: '#tglVw', limes: '#tglLimes', handel: '#tglHandel', land: '#tglLand', see: '#tglSee', waren: '#tglWaren',
    gesandt: '#tglGes', karawanen: '#tglKar', strassen: '#tglStr', schiff: '#tglSchiff', hanseide: '#tglHanSeide', zh: '#tglZh', bilder: '#tglBilder', netze: '#netzSec' };
  function fokusKamera(f) { return { lat: f.lat, lng: f.lng, alt: f.alt === 'standard' || f.alt == null ? homeAlt() : f.alt }; }
  /* Teilzustand eines Fokuspunkts: Kamera, optional Jahr und Filter (Teilzustand wie getState) */
  function fokusZustand(f) {
    var t = Object.assign({}, f.filter || {}); t.kamera = fokusKamera(f);
    if (f.jahr != null) t.jahr = f.jahr;
    return t;
  }
  function tafelbildStart(tb) {
    var st = tb.start || {}, a = (tb.ebenen && tb.ebenen.aktiv) || {}, t = {};
    if (st.jahr != null) t.jahr = st.jahr;
    if (st.ansicht) t.ansicht = st.ansicht;
    if ('drehen' in st) t.drehen = !!st.drehen;
    var k = st.kamera, fp = (tb.fokuspunkte || []).filter(function (f) { return f.id === k; })[0];
    if (fp) t.kamera = fokusKamera(fp); else if (k && typeof k === 'object') t.kamera = fokusKamera(k);
    if (tb.reiche && tb.reiche.aktiv) { t.reiche = {}; DATA.reihen.forEach(function (r) { t.reiche[r] = tb.reiche.aktiv.indexOf(r) >= 0; }); }
    t.globus = {}; ['orte', 'schlachten', 'vw', 'limes'].forEach(function (x) { if (x in a) t.globus[x] = !!a[x]; });
    t.handel = {}; ['land', 'see', 'waren', 'gesandt', 'karawanen', 'strassen', 'schiff', 'hanseide'].forEach(function (x) { if (x in a) t.handel[x] = !!a[x]; });
    if ('handel' in a) t.handel.on = !!a.handel;
    t.strassen = {}; if ('strassen_ehemals' in a) t.strassen.ehemals = !!a.strassen_ehemals; if ('strassen_animieren' in a) t.strassen.animieren = !!a.strassen_animieren;
    t.zh = {}; if ('zh' in a) t.zh.on = !!a.zh; if ('bilder' in a) t.zh.bilder = !!a.bilder;
    if (Array.isArray(a.netze)) { t.netze = {}; a.netze.forEach(function (id) { t.netze[id] = true; }); }
    return t;
  }
  function tafelbildAnwenden(tb) {
    if (!tb) return;
    document.title = tb.id ? tb.titel + ' · ChronoGlobe' : 'ChronoGlobe · ' + tb.titel;
    $('#h1kopf').textContent = tb.kopf || 'ChronoGlobe'; $('#h1sub').textContent = tb.untertitel || tb.titel || '';
    if (tb.zeitraum) { YMIN = Math.max(YMIN, tb.zeitraum.von); YMAX = Math.min(YMAX, tb.zeitraum.bis); }
    // verfügbare Reiche und Ebenen
    var rv = tb.reiche && tb.reiche.verfuegbar;
    ['rom', 'han'].forEach(function (r) { if (!DATA.meta[r]) $(r === 'rom' ? '#tglRom' : '#tglHan').hidden = true; });   // außerhalb des Zeitraums
    if (Array.isArray(rv)) DATA.reihen.forEach(function (r) {
      if (rv.indexOf(r) >= 0) return;
      var b = r === 'rom' ? $('#tglRom') : r === 'han' ? $('#tglHan') : $('.chip.nb[data-r="' + r + '"]'); if (b) b.hidden = true;
    });
    var ev = tb.ebenen && tb.ebenen.verfuegbar;
    if (Array.isArray(ev)) Object.keys(EBENEN_SEL).forEach(function (k) { if (ev.indexOf(k) < 0) { var b = $(EBENEN_SEL[k]); if (b) b.hidden = true; } });
    if (Array.isArray(ev) && ev.indexOf('zh') < 0) $('.zh-block').hidden = true;
    if (Array.isArray(ev) && ev.indexOf('limes') < 0) $('#limesLeg').hidden = true;
    // Fokuspunkte → Knöpfe im Menü
    var box = $('#fokusBtns'); box.innerHTML = '';
    (tb.fokuspunkte || []).forEach(function (f) {
      var b = el('button', 'small', f.knopf || f.name); b.type = 'button'; b.id = 'fokus-' + f.id; b.title = f.name;
      b.addEventListener('click', function () { setState(fokusZustand(f), { dauer: 1400 }); });
      box.appendChild(b);
    });
    // Lehrerhinweise nur mit Tafelbild
    if (tb.lehrerhinweise && tb.lehrerhinweise.reiter && tb.lehrerhinweise.reiter.length) lehrerReiterBauen(tb.lehrerhinweise, tb.ordner || '');
    else $('#btnLehrer').hidden = true;
    applyState(tafelbildStart(tb), { quelle: 'tafelbild' });
  }

  /* ---------- Start ---------- */
  /* ---------- Lehrerhinweise: Inhalte aus lehrerhinweise/*.md (Reiter in index.html, data-md = Datei) ---------- */
  var LEHRER_GELADEN = false;
  function lehrerLaden() {
    if (LEHRER_GELADEN) return;
    LEHRER_GELADEN = true;
    document.querySelectorAll('.lpanel[data-md]').forEach(function (sec) {
      fetch(sec.getAttribute('data-md'), { cache: 'no-cache' })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
        .then(function (t) { sec.innerHTML = markdown(t); })
        .catch(function () { sec.innerHTML = '<p class="hint">Datei <code>' + esc(sec.getAttribute('data-md')) + '</code> konnte nicht geladen werden (Seite über einen Webserver öffnen).</p>'; LEHRER_GELADEN = false; });
    });
  }
  function esc(t) { return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  /* kleiner Markdown-Leser: Überschriften, Absätze, Listen, Zitate, Tabellen, fett/kursiv/Code/Links; HTML wird maskiert */
  function markdown(src) {
    var zeilen = src.replace(/\r/g, '').replace(/<!--[\s\S]*?-->/g, '').split('\n'), out = [], i = 0, ersteH1 = true;
    function inl(t) {
      return esc(t).replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>').replace(/(^|[^*])\*([^*\s][^*]*)\*/g, '$1<i>$2</i>')
        .replace(/\[([^\]]+)\]\(((?:https?:\/\/|\.{0,2}\/|[\w-]+\.html)[^)\s]*)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    }
    function zellen(z) { return z.trim().replace(/^\||\|$/g, '').split('|').map(function (c) { return c.trim(); }); }
    while (i < zeilen.length) {
      var z = zeilen[i], m;
      if (!z.trim()) { i++; continue; }
      if ((m = /^(#{1,4})\s+(.*)$/.exec(z))) {
        if (m[1].length === 1 && ersteH1) { ersteH1 = false; i++; continue; }   // Titel trägt der Reiter
        var h = Math.min(4, m[1].length + 1); out.push('<h' + h + '>' + inl(m[2]) + '</h' + h + '>'); i++; continue;
      }
      if (/^\s*\|/.test(z) && i + 1 < zeilen.length && /^\s*\|?\s*:?-{2,}/.test(zeilen[i + 1])) {
        var kopf = zellen(z), t = '<table class="ltab"><thead><tr>' + kopf.map(function (c) { return '<th>' + inl(c) + '</th>'; }).join('') + '</tr></thead><tbody>';
        i += 2;
        while (i < zeilen.length && /^\s*\|/.test(zeilen[i])) { t += '<tr>' + zellen(zeilen[i]).map(function (c) { return '<td>' + inl(c) + '</td>'; }).join('') + '</tr>'; i++; }
        out.push(t + '</tbody></table>'); continue;
      }
      if (/^\s*([-*]|\d+\.)\s+/.test(z)) {
        var ol = /^\s*\d+\./.test(z), li = [];
        while (i < zeilen.length && /^\s*([-*]|\d+\.)\s+/.test(zeilen[i])) { li.push('<li>' + inl(zeilen[i].replace(/^\s*([-*]|\d+\.)\s+/, '')) + '</li>'); i++; }
        out.push((ol ? '<ol>' : '<ul>') + li.join('') + (ol ? '</ol>' : '</ul>')); continue;
      }
      if (/^>\s?/.test(z)) {
        var q = [];
        while (i < zeilen.length && /^>\s?/.test(zeilen[i])) { q.push(zeilen[i].replace(/^>\s?/, '')); i++; }
        out.push('<blockquote>' + inl(q.join(' ')) + '</blockquote>'); continue;
      }
      var abs = [];
      while (i < zeilen.length && zeilen[i].trim() && !/^(#{1,4}\s|>|\s*\||\s*([-*]|\d+\.)\s)/.test(zeilen[i])) { abs.push(zeilen[i]); i++; }
      out.push('<p>' + inl(abs.join(' ')) + '</p>');
    }
    return out.join('\n');
  }
  function load(url) { return fetch(url).then(function (r) { if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); }); }
  function daten(k, url) { return window.CG && CG.daten ? CG.daten(k, url) : load(url); }
  (window.CG && CG.bereit ? CG.bereit : Promise.resolve(null)).then(function () { return Promise.all([daten('reiche', 'data/reiche.json'), load('data/land.json'), load('data/land_rom.json'), load('data/land_han.json'), daten('handel', 'data/handel.json'), daten('zhenghe', 'data/zhenghe.json'),
    daten('texte', 'data/texte.json'), daten('literatur', 'data/literatur.json'), daten('roemerstrassen', 'data/roemerstrassen.json'),
    daten('orbis_schiff', 'data/orbis_schiff.json').catch(function (e) { console.warn(e); return null; }),
    daten('fruehe_reiche', 'data/fruehe_reiche.json').catch(function (e) { console.warn(e); return null; }),
    daten('han_seidenstrasse', 'data/han_seidenstrasse.json').catch(function (e) { console.warn(e); return null; }),
    daten('limes', 'data/limes.json').catch(function (e) { console.warn(e); return null; }),
    daten('netze', 'data/netze/index.json').catch(function (e) { console.warn(e); return null; }),
    // Vignetten: fehlt die Datei, bleibt die Rolle mit leeren Platzhaltern nutzbar. ?vignetten=demo zeigt alle Bausteine.
    daten('vignetten', /[?&]vignetten=demo\b/.test(location.search) ? 'data/vignetten_demo.json' : 'data/vignetten.json').catch(function (e) { console.warn(e); return {}; })]); }).then(function (res) {
    DATA = res[0]; LAND = res[1]; LAND_FLAT.rom = res[2]; LAND_FLAT.han = res[3]; HANDEL = res[4]; ZHD = res[5];
    TEXTE = res[6]; res[7].titel.forEach(function (t) { LIT[t.id] = t; }); STRASSEN = StrassenZeit.vorbereiten(res[8]); initOrbis(res[9]); initHanSeide(res[11]); initLimes(res[12]); VIG = res[14];
    reicheErgaenzen(res[10]); reicheFiltern(window.CG && CG.tafelbild); zeitleisteEinrichten(); mittelalterEinrichten(); abschnitteZuschneiden();
    if (STRASSEN.fehler.length) console.warn('Römerstraßen: ' + STRASSEN.fehler.length + ' Hinweise beim Einlesen', STRASSEN.fehler.slice(0, 20));
    initTrade(); initZh(); buildZhChips(); initNetze(res[13]);
    Vignetten.beiWechsel(function (r, wo) { if (FENSTER.rolle && FENSTER.rolle.reich === r && FENSTER.rolle.vignette !== wo) { FENSTER.rolle.vignette = wo; zustandGemeldet(); } });
    document.querySelectorAll('.camel-ico').forEach(function (x) { x.innerHTML = CAMEL; });
    DATA.reihen.forEach(function (r) { state.on[r] = !!M(r).haupt; EVENTS[r] = []; });
    DATA.ereignisse.forEach(function (e) { EVENTS[e.reich].push(e); });
    DATA.reihen.forEach(function (r) { EVENTS[r].sort(function (a, b) { return a.jahr - b.jahr; }); });
    DATA.regionen.forEach(function (f) { BYID[f.properties.id] = f; if (f.properties.von >= SEGS[1].von) MITTEL[f.properties.reich] = 1; });
    (DATA.wanderungen || []).forEach(function (w, i) { w.__lauf = lauf(w.pfad); vwVorbereiten(w, i); });
    var tl = $('#timeline'), setTlh = function () { document.documentElement.style.setProperty('--tlh', tl.offsetHeight + 'px'); };
    if (window.ResizeObserver) new ResizeObserver(setTlh).observe(tl);
    initGlobe(); buildChips(); buildTicks(); buildLanes(); bind(); lastKey = ''; setYear(state.year);
    tafelbildAnwenden(window.CG ? CG.tafelbild : null);
    if (location.hash === '#hilfe') modalOeffnen('hilfe');
    setTimeout(startIntro, 600);
    window.__tafelbild = { strOpt: STR_OPT, strassen: function () { return { geladen: STRASSEN.linien.length, fehler: STRASSEN.fehler.length,
        sichtbar: strassenPaths(state.year).length, aufGlobus: globe.pathsData().filter(function (d) { return d.strasse; }).length,
        stile: globe.pathsData().filter(function (d) { return d.strasse; }).reduce(function (a, d) { a[d.stil] = (a[d.stil] || 0) + 1; return a; }, {}) }; },
      state: state, trade: TRADE, zh: ZH, kar: KAR, openMap: openMap, closeMap: closeMap, setYear: setYear, globe: globe, tradeVisible: tradeVisible, zhVisible: zhVisible,
      getState: getState, applyState: applyState, setState: setState, netze: NETZE, netzePaths: netzePaths, netzeOrte: netzeOrte, segs: SEGS };
    window.ChronoGlobe = { getState: getState, applyState: applyState, setState: setState, abonnieren: abonnieren,
      setzeRechte: function (fn) { DARF = typeof fn === 'function' ? fn : function () { return true; }; }, globe: globe, homeAlt: homeAlt };
    document.dispatchEvent(new CustomEvent('chronoglobe:bereit'));
  }).catch(function (err) {
    var m = document.createElement('div'); m.className = 'toast show'; m.style.bottom = '50%';
    m.textContent = 'Daten konnten nicht geladen werden. Bitte die Seite über einen Webserver öffnen (nicht per Doppelklick). ' + err.message;
    document.body.appendChild(m);
  });
})();
