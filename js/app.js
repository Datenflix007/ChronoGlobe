/* Digitales Tafelbild: Rom und China – Globus, Zeitleiste, Kartenrolle
   Abhängigkeiten (lokal in vendor/): globe.gl, d3. Daten: data/*.json (erzeugt mit build_reiche.py) */
(function () {
  'use strict';

  var YMIN = -300, YMAX = 480, TEILUNG = 395, OSTROM = '#7b3fa0', SCHLACHT_JAHRE = 25;
  // Epochen: eigene Zeitleiste je Epoche (die antike Achse wird nicht gestreckt)
  var EPOCHEN = {
    antike: { min: -300, max: 480, start: 117, tick: 50, major: 100, alt: 200, takt: 70, titel: 'Rom und China', side: 'Infos zu den Reichen' },
    ming: { min: 1400, max: 1440, start: 1405, tick: 5, major: 10, alt: 20, takt: 450, titel: 'Zheng He (Ming-Zeit)', side: 'Infos zu den Fahrten' }
  };
  var state = { mode: 'sat', on: {}, orte: false, rotate: true, schlachten: true, year: 117, epoche: 'antike', jahrJe: {} };
  var TRADE = { on: false, land: true, see: true, waren: true, gesandt: true, karawanen: true };
  var ZH = { on: true, waren: true, fahrt: {} }, ZHD = null;
  var DATA, LAND, LAND_FLAT = {}, EVENTS = {}, BYID = {}, globe, mapOpen = false, mapReich = null, playTimer = null, lastKey = '';
  var prevVis = null, mapPrev = null, flashTimer = null;

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
  function exists(r, y) { return y >= M(r).von && y < M(r).bis; }
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
  function schemTexture() { return SCHEM_URL; }

  function capColor(f) {
    var p = f.properties || {};
    if (p.kind === 'land') return '#e7dcc0';
    var c = regionColor(f, state.year), a = p.art === 'einfluss' ? 0.3 : (M(p.reich).haupt ? 0.62 : 0.55);
    if (f.__flash && Date.now() - f.__flash < 1300) return rgba(c, Math.min(0.9, a + 0.25));
    return rgba(c, a);
  }
  function visiblePolys() {
    var a = [];
    DATA.reihen.forEach(function (r) { if (state.on[r]) a.push.apply(a, regionsAt(r, state.year)); });
    return a;
  }
  function visibleCities() {
    if (!state.orte) return [];
    return DATA.orte.filter(function (o) {
      if (!state.on[o.reich] || !exists(o.reich, state.year)) return false;
      return state.year >= o.von && (o.bis === null || state.year <= o.bis);
    });
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
    globe.labelsData(visibleCities().concat(tv.places, karNodeLabels(tv)));
    globe.htmlElementsData(visibleBattles(state.year).concat(tv.kontakte, wareTags(tv), [STANDORT || JENA]));
    globe.pathsData(tradeGlobePaths(tv));
    karUpdate();
    setTimeout(scheduleTagSides, 50);
    clearTimeout(flashTimer);
    flashTimer = setTimeout(function () { globe.polygonCapColor(capColor); }, 1350);
  }
  function applyMode() {
    var sat = state.mode === 'sat';
    globe.globeImageUrl(sat ? 'img/earth-blue-marble.jpg' : schemTexture());
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
  function polyLabel(f) {
    var p = f.properties; if (p.kind === 'land') return '';
    var reich = (p.reich === 'rom' && state.year >= TEILUNG) ? (p.seite === 'o' ? 'Ostrom' : 'Westrom') : M(p.reich).name;
    var d = document.createElement('div');
    var b = document.createElement('b'); b.textContent = p.name; d.appendChild(b);
    d.appendChild(document.createElement('br'));
    d.appendChild(document.createTextNode(reich + (p.art === 'einfluss' ? ' (Einfluss)' : '') + ' · ' + fmtYear(p.von) + (p.bis < M(p.reich).bis ? ' bis ' + fmtYear(p.bis) : '')));
    return '<div class="gtip">' + d.innerHTML + '</div>';
  }
  function labelColor(d) {
    if (d.kind === 'handel') return tradeCol((routeById(d.an[0][0]) || { art: 'land' }).art);
    if (d.kind === 'zhhafen') return state.mode === 'schem' ? '#0d5a35' : '#9af5bd';
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
      .polygonAltitude(function (f) { var p = f.properties; return p.kind === 'land' ? 0.0012 : (M(p.reich).haupt ? 0.0045 : 0.0038); })
      .polygonCapCurvatureResolution(3)
      .polygonsTransitionDuration(900)
      .polygonLabel(polyLabel)
      .labelLat('lat').labelLng('lng').labelText(function (d) { return d.kind === 'handel' ? d.name.replace(/Ó/g, 'O') : d.name; })
      .labelSize(0.85).labelDotRadius(0.28).labelAltitude(0.006).labelResolution(2)
      .labelColor(labelColor)
      .labelSize(function (d) { return d.kind === 'karawane' ? 0.75 : labelIsTrade(d) ? 1.0 : 0.85; })
      .labelDotRadius(function (d) { return d.kind === 'karawane' ? 0.3 : labelIsTrade(d) ? 0.42 : 0.28; })
      .labelLabel(function (d) {
        if (!labelIsTrade(d)) return '';
        var t = el('div', 'gtip'); t.appendChild(el('b', null, d.name)); t.appendChild(el('br'));
        t.appendChild(document.createTextNode((d.kind === 'karawane' ? d.hinweis : d.vermittler) + ' · Klick für Infos')); return t.outerHTML;
      })
      .htmlLat('lat').htmlLng('lng').htmlAltitude(function (d) { return d.kind === 'waren' ? 0.009 : 0.01; }).htmlElement(htmlEl).htmlTransitionDuration(0);
    initTradeGlobe();
    globe.controls().addEventListener('change', scheduleTagSides);
    globe.controls().addEventListener('change', karDrawSoon);
    window.addEventListener('resize', scheduleTagSides);
    var c = globe.controls();
    c.autoRotate = state.rotate; c.autoRotateSpeed = 0.35;
    c.minDistance = 118; c.maxDistance = 520; c.zoomSpeed = 0.9; c.enablePan = false;
    globe.pointOfView({ lat: 36, lng: 62, altitude: homeAlt() }, 0);
    applyMode();
    function sizeGlobe() { var g = $('#globe'); globe.width(g.clientWidth || window.innerWidth).height(g.clientHeight || window.innerHeight); }
    window.addEventListener('resize', sizeGlobe);
    if (window.ResizeObserver) new ResizeObserver(sizeGlobe).observe($('#globe'));

    // Hineinzoomen => Karte entrollen
    var cvs = globe.renderer().domElement;
    cvs.addEventListener('wheel', function (e) {
      if (mapOpen || e.deltaY >= 0) return;
      if (globe.pointOfView().altitude <= 0.42) tryOpenMap();
    }, { passive: true });
    var pinchBase = null;
    cvs.addEventListener('touchstart', function () { pinchBase = globe.pointOfView().altitude; }, { passive: true });
    cvs.addEventListener('touchend', function () {
      var a = globe.pointOfView().altitude;
      if (!mapOpen && pinchBase !== null && a < pinchBase - 0.02 && a <= 0.42) tryOpenMap();
      pinchBase = null;
    }, { passive: true });
  }
  function fly(lat, lng, alt) { globe.pointOfView({ lat: lat, lng: lng, altitude: alt }, 1400); }

  /* Welches Reich (Rom/Han) liegt unter dem Blickpunkt? */
  function pickReich() {
    var pov = globe.pointOfView(), best = null, bestD = 1e9;
    ['rom', 'han'].forEach(function (r) {
      var regs = state.on[r] ? regionsAt(r, state.year) : [];
      if (!regs.length) return;
      var inside = regs.some(function (f) { return d3.geoContains(f, [pov.lng, pov.lat]); });
      var d = d3.geoDistance([pov.lng, pov.lat], M(r).zentrum) * 180 / Math.PI;
      if (inside) d = Math.min(d, 1);
      if (d < bestD) { bestD = d; best = r; }
    });
    return bestD <= 38 ? best : null;
  }
  function tryOpenMap(force) {
    if (state.epoche !== 'antike') return;   // Reichskarten gibt es nur für die Antike
    var r = force || pickReich();
    if (!r) {
      var any = ['rom', 'han'].some(function (k) { return state.on[k] && regionsAt(k, state.year).length; });
      toast(any ? 'Zum Entrollen auf Rom oder China hineinzoomen.' : 'Bitte ein Reich einblenden (und passendes Jahr wählen).');
      return;
    }
    openMap(r);
  }

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
        d.innerHTML = '<div class="k"></div><div class="t"></div><div class="y"></div><p></p><button type="button">Karte entrollen</button>';
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
    var box = $('#nbChips');
    DATA.reihen.forEach(function (r) {
      var m = M(r); if (m.haupt) return;
      var b = document.createElement('button'); b.type = 'button'; b.className = 'chip nb'; b.dataset.r = r;
      b.style.setProperty('--c', m.farbe); b.style.setProperty('--cbg', rgba(m.farbe, 0.28));
      b.setAttribute('aria-pressed', 'false');
      b.title = m.name + ' (' + fmtYear(m.von) + ' bis ' + fmtYear(m.bis) + '). ' + m.kurz;
      b.innerHTML = '<i></i><span></span>'; b.querySelector('span').textContent = m.name;
      b.addEventListener('click', function () { setOn(r, !state.on[r]); });
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
  function updateChips() {
    document.querySelectorAll('.chip.nb').forEach(function (b) { b.classList.toggle('absent', !exists(b.dataset.r, state.year)); });
  }

  /* ---------- Zeitleiste ---------- */
  function pct(y) { return ((y - YMIN) / (YMAX - YMIN) * 100); }
  function buildTicks() {
    var ticks = $('#ticks'), E = EPOCHEN[state.epoche], ming = state.epoche === 'ming';
    ticks.innerHTML = '';
    for (var y = YMIN; y <= YMAX; y += E.tick) {
      var t = document.createElement('div'); t.style.left = pct(y) + '%';
      if (y % E.major) { t.className = 'tick minor'; }
      else {
        t.className = 'tick' + (y % E.alt ? ' odd' : '');
        var l = el('span', 'tk-l', ming ? String(y) : y === 0 ? 'Chr. Geb.' : fmtYear(y)), sh = el('span', 'tk-s', ming ? String(y) : y === 0 ? '0' : shortYear(y));
        t.appendChild(l); t.appendChild(sh);
      }
      ticks.appendChild(t);
    }
  }
  function buildLanes() {
    if (state.epoche === 'ming') { buildLanesMing(); return; }
    var lanes = $('#lanes'); lanes.innerHTML = '';
    var zero = document.createElement('div'); zero.className = 'zero'; zero.style.left = pct(0) + '%'; lanes.appendChild(zero);
    var cur = document.createElement('div'); cur.className = 'cursor'; lanes.appendChild(cur);
    var shown = DATA.reihen.filter(function (r) { return M(r).haupt || state.on[r]; });
    shown.forEach(function (r) {
      var m = M(r), lane = document.createElement('div');
      lane.className = 'lane' + (m.haupt ? '' : ' thin'); lane.dataset.r = r;
      lane.style.setProperty('--c', m.farbe); lane.style.setProperty('--cs', rgba(m.farbe, 0.2));
      lane.style.setProperty('--cb', rgba(m.farbe, 0.6)); lane.style.setProperty('--ct', mix(m.farbe, '#ffffff', 0.55));
      var a = Math.max(YMIN, m.von), b = Math.min(YMAX, m.bis);
      var era = document.createElement('div'); era.className = 'era';
      era.style.left = pct(a) + '%'; era.style.width = (pct(b) - pct(a)) + '%';
      var nm = document.createElement('span'); nm.className = 'nm'; nm.textContent = m.name; era.appendChild(nm);
      era.title = m.name + ': ' + fmtYear(m.von) + ' bis ' + fmtYear(m.bis);
      lane.appendChild(era);
      if (r === 'rom') {   // ab 395: Ostrom
        var ost = document.createElement('div'); ost.className = 'era-ost';
        ost.style.left = pct(TEILUNG) + '%'; ost.style.width = (pct(YMAX) - pct(TEILUNG)) + '%';
        ost.style.setProperty('--co', rgba(OSTROM, 0.55)); ost.title = 'Ab 395 n. Chr.: Westrom (oben) und Ostrom (unten)';
        lane.appendChild(ost);
      }
      // Schlachten: in der ersten angezeigten Spur eines beteiligten Reichs
      DATA.schlachten.forEach(function (s) {
        var home = s.reiche.filter(function (x) { return shown.indexOf(x) >= 0; })[0];
        if (home !== r || s.jahr < YMIN || s.jahr > YMAX) return;
        var bt = document.createElement('button'); bt.type = 'button'; bt.className = 'bt'; bt.dataset.y = s.jahr;
        bt.style.left = pct(s.jahr) + '%'; bt.innerHTML = SWORDS;
        bt.title = 'Schlacht: ' + s.name + ' (' + fmtYear(s.jahr) + ')';
        bt.addEventListener('click', function () { setYear(s.jahr); toast('⚔ ' + s.name + ', ' + fmtYear(s.jahr) + ': ' + s.note); });
        lane.appendChild(bt);
      });
      (EVENTS[r] || []).forEach(function (e) {
        var k = document.createElement('button'); k.type = 'button'; k.className = 'mk'; k.dataset.y = e.jahr;
        k.style.left = pct(e.jahr) + '%'; k.textContent = shortYear(e.jahr);
        k.title = e.label + ': ' + e.titel;
        k.addEventListener('click', function () { setYear(e.jahr); });
        lane.appendChild(k);
      });
      lanes.appendChild(lane);
    });
    lanes.classList.toggle('noschl', !state.schlachten);
    var nThin = shown.length - shown.filter(function (r) { return M(r).haupt; }).length;
    var lt = $('#lanesToggle');
    lt.hidden = nThin === 0;
    lt.querySelector('span').textContent = 'Nachbarreiche (' + nThin + ')';
    updateMarkers();
  }
  function updateMarkers() {
    if (state.epoche === 'ming') { updateMarkersMing(); return; }
    document.querySelectorAll('.lane').forEach(function (lane) {
      var e = activeEvent(lane.dataset.r, state.year);
      lane.querySelectorAll('.mk').forEach(function (b) { b.classList.toggle('on', !!e && e.jahr === +b.dataset.y); });
    });
    document.querySelectorAll('.bt').forEach(function (b) {
      var d = state.year - b.dataset.y; b.classList.toggle('on', d >= 0 && d <= SCHLACHT_JAHRE);
    });
  }
  function stateKey(y) {
    if (state.epoche === 'ming') { stateKey.tv = EMPTY_TV; stateKey.zv = zhVisible(y); return 'ming|' + stateKey.zv.key; }
    var ids = [];
    DATA.reihen.forEach(function (r) { if (state.on[r]) regionsAt(r, y).forEach(function (f) { ids.push(f.properties.id); }); });
    var ev = DATA.reihen.map(function (r) { var e = activeEvent(r, y); return e ? e.jahr : 'x'; }).join(',');
    var bs = visibleBattles(y).map(function (b) { return b.name; }).join(',');
    var nb = DATA.reihen.map(function (r) { return exists(r, y) ? 1 : 0; }).join('');
    var tv = tradeVisible(y); stateKey.tv = tv;
    return ids.join(',') + '|' + ev + '|' + bs + '|' + nb + '|' + (y >= TEILUNG) + '|' + state.orte + '|' + state.schlachten + '|' + tv.key;
  }
  function setYear(y, fromSlider) {
    y = Math.max(YMIN, Math.min(YMAX, Math.round(y)));
    karYearJump(y);
    state.year = y;
    if (!fromSlider) $('#year').value = y;
    $('#yearOut').textContent = fmtYear(y);
    $('#track').style.setProperty('--pf', (y - YMIN) / (YMAX - YMIN));
    var key = stateKey(y);
    if (key !== lastKey) {
      lastKey = key; CUR_TV = stateKey.tv; CUR_ZV = stateKey.zv || null; refreshGlobe(); renderCards(); updateMarkers(); updateChips(); renderTradeList(CUR_TV);
      if (mapOpen) drawMap(mapReich, true);
    }
    visibleBattles(y).forEach(function (b) { if (b.__el) b.__el.classList.toggle('fresh', y - b.jahr <= 4); });
  }
  function togglePlay() {
    if (playTimer) { clearInterval(playTimer); playTimer = null; $('#play').textContent = '▶'; return; }
    if (state.year >= YMAX) setYear(YMIN);
    $('#play').textContent = '❚❚';
    playTimer = setInterval(function () {
      if (state.year >= YMAX) { togglePlay(); return; }
      setYear(state.year + 1);
    }, EPOCHEN[state.epoche].takt);
  }

  /* ---------- Flache Reichskarte ---------- */
  var W = 1200, H = 720;
  function makeProj(r) {
    var m = M(r), b = m.rahmen, w = b[0], s = b[1], e = b[2], n = b[3];
    var p = r === 'rom'
      ? d3.geoConicEquidistant().parallels([36, 46]).rotate([-17, 0]).center([0, 41])
      : d3.geoConicEquidistant().parallels([22, 40]).rotate([-105, 0]).center([0, 30]);
    p.fitExtent([[20, 20], [W - 20, H - 20]], { type: 'MultiPoint', coordinates: [[w, s], [e, s], [e, n], [w, n], [(w + e) / 2, s], [(w + e) / 2, n], [w, (s + n) / 2], [e, (s + n) / 2]] });
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
    mapOpen = false; mapReich = null; mapPrev = null;
    globe.controls().autoRotate = state.rotate;
    var pov = globe.pointOfView(); globe.pointOfView({ lat: pov.lat, lng: pov.lng, altitude: 0.9 }, 600);
  }
  function openMap(r) {
    if (closeTimer) finishClose();
    if (mapOpen) return;
    mapOpen = true; mapReich = r; mapPrev = null;
    globe.controls().autoRotate = false;
    var ov = $('#mapOverlay'); ov.classList.add('show'); ov.setAttribute('aria-hidden', 'false');
    drawMap(r, false);
    var sc = $('#scroll'); sc.classList.remove('open');
    void sc.offsetWidth;
    requestAnimationFrame(function () { requestAnimationFrame(function () { sc.classList.add('open'); }); });
    $('#mapClose').focus({ preventScroll: true });
  }
  function closeMap() {
    if (!mapOpen) return;
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
    svg.append('path').attr('d', path(LAND_FLAT[r])).attr('fill', '#efe3c2').attr('stroke', '#8d7b57').attr('stroke-width', 1.1).attr('stroke-linejoin', 'round');

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
    SEA_LABELS[r].forEach(function (l) { label(l[0], l[1], l[2], l[3] ? -l[3] / 4 : 0, 17, 'italic', '#3f6b78'); });
    NEIGH[r].forEach(function (n) { label(n[0], n[1], n[2], 0, 18, 'italic', '#6b5a3a'); });
    // Namen eingeblendeter Nachbarreiche
    DATA.reihen.forEach(function (k) {
      if (k === r || !inView[k]) return;
      var z = M(k).zentrum; label(M(k).name, z[0], z[1], 0, 18, 'italic', mix(M(k).farbe, '#000000', 0.5));
    });
    // Städte
    var cg = svg.append('g').attr('font-family', 'Georgia, serif');
    var seen = {}; mapCityNames = {}; mapCityBoxes = [];
    DATA.orte.forEach(function (o) {
      if (o.reich !== r && !state.on[o.reich]) return;
      if (!regionsAt(o.reich, y).length || seen[o.name]) return;
      if (y < o.von || (o.bis !== null && y > o.bis)) return;
      var xy = proj([o.lng, o.lat]); if (!xy || xy[0] < 0 || xy[0] > W || xy[1] < 0 || xy[1] > H) return;
      seen[o.name] = 1; mapCityNames[o.name] = 1;
      cg.append('circle').attr('cx', xy[0]).attr('cy', xy[1]).attr('r', 5).attr('fill', '#2b2110').attr('stroke', '#f5ecd2').attr('stroke-width', 1.5);
      var ctx = cg.append('text').attr('x', xy[0] + 9).attr('y', xy[1] + 5).attr('font-size', 17).attr('fill', '#2b2110').attr('stroke', 'rgba(239,227,194,.9)').attr('stroke-width', 3.5).attr('paint-order', 'stroke').attr('font-weight', 600).text(o.name);
      mapCityBoxes.push([xy[0] - 7, xy[1] - 13, 18 + ctx.node().getComputedTextLength(), 24]);
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
    t1.textContent = ev ? (r === 'rom' ? (y >= TEILUNG ? 'West- und Ostrom' : 'Das Römische Reich') : 'Das Reich der Han') : M(r).name;
    var t2 = document.createElement('div'); t2.className = 'cs'; t2.textContent = ev ? ev.titel + ' · ' + fmtYear(y) : fmtYear(y) + ': besteht nicht';
    ct.appendChild(t1); ct.appendChild(t2);
    if (ev) { var p = document.createElement('p'); p.textContent = ev.note; ct.appendChild(p); }
    // Legende
    var lg = $('#legend'); lg.innerHTML = '';
    function lgRow(bg, txt) {
      var d = document.createElement('div'), i = document.createElement('i'); i.style.background = bg;
      d.appendChild(i); d.appendChild(document.createTextNode(txt)); lg.appendChild(d);
    }
    if (r === 'rom' && y >= TEILUNG) { lgRow(rgba(M('rom').farbe, 0.74), 'Westrom'); lgRow(rgba(OSTROM, 0.74), 'Ostrom'); }
    else lgRow(rgba(M(r).farbe, 0.74), M(r).name + ' (vereinfacht)');
    if (own.some(function (x) { return x.properties.art === 'einfluss'; }))
      lgRow('repeating-linear-gradient(45deg,#e9c55f,#e9c55f 3px,#9a6b00 3px,#9a6b00 4px)', 'Einflussbereich (Westliche Regionen)');
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
    var res = { routes: [], parts: [], places: [], kontakte: [], kar: { list: [], key: 'aus' }, key: 'aus' };
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
    res.key = [TRADE.land, TRADE.see, TRADE.waren, TRADE.gesandt, TRADE.karawanen].join('') + '|' +
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
  function fmtRange(a, b) { return b >= YMAX ? 'ab ' + fmtYear(a) : fmtYear(a) + ' bis ' + fmtYear(b); }
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
        var q = globe.getScreenCoords(c[1], c[0], 0.008); scr.push([q.x, q.y]);
      });
    });
    var placed = [];
    ['#panel', '#side'].forEach(function (id) {   // offene Menüs wie belegte Flächen behandeln
      var e = $(id); if (!e || e.classList.contains('collapsed') || getComputedStyle(e).visibility === 'hidden') return;
      var r = e.getBoundingClientRect(); placed.push([r.left, r.top, r.width, r.height]);
    });
    tags.forEach(function (t) {
      var sc = globe.getScreenCoords(t.lat, t.lng, 0.009), box = t.__el.querySelector('.wtag'), w = box.offsetWidth, h = box.offsetHeight;
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
  function htmlEl(d) { return d.kind === 'standort' ? standortEl(d) : d.kind === 'zhflag' ? zhFlagEl(d) : d.kind === 'kontakt' ? kontaktEl(d) : d.kind === 'waren' ? warenEl(d) : battleEl(d); }

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
    tv.parts.forEach(function (p) { a.push(p, p.flowObj); });
    tv.kontakte.forEach(function (k) { if (k.pathObj) a.push(k.pathObj); });
    return a;
  }
  function pathColor(d) {
    if (d.zh) return d.flow ? 'rgba(255,255,255,0.9)' : zhCol(d.zh, zhAktiv(d.zh, state.year) ? 1 : 0.42);
    if (d.kontakt) return state.mode === 'schem' ? 'rgba(78,46,128,0.95)' : 'rgba(230,210,255,0.95)';
    if (d.flow) return d.teil === 'spaet' ? 'rgba(255,255,255,0.35)' : 'rgba(255,255,255,0.9)';
    if (d.teil === 'spaet') return rgba(tradeCol(d.route.art), 0.58);   // ab 220: schwächer
    return tradeCol(d.route.art);
  }
  function pathDash(d, i) {
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
    if (d.zh) return d.flow ? 1.1 : d.ab ? 1.5 : zhAktiv(d.zh, state.year) ? 3.2 : 1.9;
    if (d.teil === 'spaet') return d.flow ? 0.8 : 2.2;
    return d.flow ? 1.2 : d.kontakt ? 1.6 : 3.2;
  }
  function initTradeGlobe() {
    globe.pathsData([])
      .pathPoints('pts').pathPointLat(function (p) { return p[1]; }).pathPointLng(function (p) { return p[0]; })
      .pathPointAlt(0.008)
      .pathColor(pathColor)
      .pathStroke(pathStroke)
      .pathDashLength(function (d) { return pathDash(d, 0); })
      .pathDashGap(function (d) { return pathDash(d, 1); })
      .pathDashAnimateTime(function (d) { return d.flow ? (d.zh ? 9000 : d.teil === 'spaet' ? 40000 : 14000) : d.kontakt ? 30000 : 0; })
      .pathResolution(1)
      .pathTransitionDuration(600)
      .pathLabel(function (d) {
        var t = el('div', 'gtip');
        if (d.zh) {
          t.appendChild(el('b', null, d.ab ? d.zh.name + ': ' + d.ab.name : d.zh.name)); t.appendChild(el('br'));
          t.appendChild(document.createTextNode((d.ab ? BELEGT_TXT[d.ab.belegt] : d.zh.stationen) + ' · Klick für Infos'));
          return t.outerHTML;
        }
        if (d.kontakt) { t.appendChild(el('b', null, d.kontakt.name + ' (' + fmtYear(d.kontakt.jahr) + ')')); return t.outerHTML; }
        t.appendChild(el('b', null, d.route.name)); t.appendChild(el('br'));
        t.appendChild(document.createTextNode(TEIL_TXT[d.teil] + ': ' + BELEGT_TXT[PARTS[d.route.id][d.teil].belegt] + ' · Klick für Infos'));
        return t.outerHTML;
      })
      .onPathClick(function (d) { if (d.zh) openZhInfo(d.zh); else if (d.kontakt) openKontaktInfo(d.kontakt); else openTradeInfo(d.route); })
      .onLabelClick(function (d) {
        if (d.kind === 'handel') openPlaceInfo(d);
        else if (d.kind === 'zhhafen') openZhHafen(d);
        else if (d.kind === 'karawane') toast('🐪 ' + d.name + ': ' + d.hinweis);
      });
  }

  /* Liste im Menü (Zugang per Tastatur) */
  function renderTradeList(tv) {
    var box = $('#routeList'); box.innerHTML = '';
    if (!TRADE.on) return;
    if (!tv.routes.length && !tv.kontakte.length) {
      box.appendChild(el('p', 'rl-none', 'Keine Verbindung für die eingeblendeten Reiche in diesem Jahr.'));
      return;
    }
    tv.routes.forEach(function (rt) {
      var b = el('button', 'rl-item ' + rt.v.art); b.type = 'button';
      b.appendChild(el('i')); b.appendChild(el('span', null, rt.v.name));
      if (rt.v.seiten && !rt.teile.mitte) b.appendChild(el('small', null, rt.teile.rom ? 'nur römische Seite' : 'nur chinesische Seite'));
      b.addEventListener('click', function () { openTradeInfo(rt.v); });
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
    var body = $('#tinfoBody'); body.innerHTML = '';
    build(body);
    var t = $('#tinfo'); if (t.hidden) tinfoReturn = document.activeElement;
    t.hidden = false; t.querySelector('.tinfo-box').scrollTop = 0;
    $('#tinfoClose').focus({ preventScroll: true });
  }
  function closeInfo() {
    var t = $('#tinfo'); if (t.hidden) return false;
    t.hidden = true;
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
    showInfo(function (b) {
      b.appendChild(el('div', 'tk ' + v.art, v.art === 'see' ? 'Seeweg' : 'Landweg'));
      var h = el('h3', null, v.name); h.id = 'tinfoTitle'; b.appendChild(h);
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
      $('#wmodal').hidden = false; $('#wmodalClose').focus({ preventScroll: true });
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
    $('#wmodal').hidden = false; $('#wmodalClose').focus({ preventScroll: true });
  }

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
    tv.routes.forEach(function (rt) {
      var v = rt.v, col = TRADE_MAP[v.art];
      var grp = lines.append('g').attr('class', 'troute').attr('tabindex', 0).attr('role', 'button').attr('aria-label', v.name + ': Infokarte öffnen');
      keyAct(grp, function () { openTradeInfo(v); });
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
      info.push({ v: v, col: col, xy: xy, first: first, last: last, txt: exit ? '→ ' + v.rand[r] : (partial && last === xy.length - 1 ? '→ weiter nur über Vermittler' : null) });
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
  }
  /* Sichtbar: Fahrt eingeschaltet und Startjahr erreicht. Laufende Fahrt hell mit wanderndem Strich, frühere blass. */
  function zhVisible(y) {
    var res = { paths: [], places: [], tags: [], aktiv: [], key: 'aus' };
    if (!ZHD || !ZH.on) return res;
    var ids = [];
    ZHD.verbindungen.forEach(function (v) {
      if (!ZH.fahrt[v.nr] || y < v.von) return;
      var akt = zhAktiv(v, y);
      ids.push(v.id + (akt ? '*' : ''));
      res.paths.push(v.__p); res.paths.push.apply(res.paths, v.__ab);
      if (akt) { res.paths.push(v.__flow); res.aktiv.push(v); res.tags.push(v.__flag); if (ZH.waren) res.tags.push(v.__tag); }
    });
    ZHD.orte.forEach(function (o) {
      if (o.__fahrten.some(function (v) { return ZH.fahrt[v.nr] && y >= v.von; })) res.places.push(o);
    });
    res.key = ids.join(',') + '|' + ZH.waren + '|' + res.places.length;
    return res;
  }
  function refreshGlobeMing() {
    var zv = CUR_ZV || zhVisible(state.year);
    CUR_TV = { routes: [], parts: zv.aktiv.map(function (v) { return v.__p; }), places: [], kontakte: [], kar: { list: [] }, key: '' };
    globe.polygonsData([]);
    globe.labelsData(zv.places);
    globe.htmlElementsData(zv.tags.concat([STANDORT || JENA]));
    globe.pathColor(pathColor).pathStroke(pathStroke);
    globe.pathsData(zv.paths);
    zv.aktiv.forEach(function (v, i) { if (v.__flag.__el) v.__flag.__el.style.setProperty('--dy', (-14 - i * 28) + 'px'); });
    karUpdate();
    setTimeout(scheduleTagSides, 50);
  }
  function zhFlagEl(d) {
    if (d.__el) return d.__el;
    var e = el('div', 'zhflag', d.zh.nr + '. Fahrt'); e.style.setProperty('--c', ZH_COL[d.zh.nr - 1]);
    e.title = d.zh.name + ' (Klick für Infos)';
    e.addEventListener('click', function (ev) { ev.stopPropagation(); openZhInfo(d.zh); });
    d.__el = e; return e;
  }
  function openZhInfo(v) {
    showInfo(function (b) {
      b.appendChild(el('div', 'tk zh', 'Seeweg · Flotte der Ming'));
      var h = el('h3', null, 'Zheng He: ' + v.name); h.id = 'tinfoTitle'; b.appendChild(h);
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
    var akt = ZHD.verbindungen.filter(function (v) { return zhAktiv(v, y); });
    akt.forEach(function (v) {
      zhCard(box, ZH_COL[v.nr - 1], 'Gerade unterwegs', v.name, [v.stationen, v.hinweis], 'Infokarte zur Fahrt', function () { openZhInfo(v); });
    });
    if (!akt.length) {
      var next = ZHD.verbindungen.filter(function (v) { return v.von > y; })[0];
      var t = y < ZHD.verbindungen[0].von ? 'Die Fahrten beginnen 1405.' : next ? 'Zwischen den Fahrten. Nächste: ' + next.name + '.' : 'Nach 1433 gab es keine solchen Flottenfahrten mehr.';
      zhCard(box, '#566a80', 'Keine Fahrt in diesem Jahr', t, null, null, null, 'none');
    }
    var ev = null; ZHD.ereignisse.forEach(function (e) { if (e.jahr <= y) ev = e; });
    if (ev) zhCard(box, '#5fdc8a', 'Ereignis · ' + ev.jahr + (ev.belegt === 'umstritten' ? ' · teils umstritten' : ''), ev.titel, ev.text);
    zhCard(box, '#5fdc8a', 'Hintergrund', ZHD.info.titel, ZHD.info.absaetze.slice(0, 2), 'Weiterlesen', openZhBackground);
  }
  function buildLanesMing() {
    var lanes = $('#lanes'); lanes.innerHTML = '';
    lanes.appendChild(el('div', 'cursor'));
    var lane = el('div', 'lane zhlane'); lane.dataset.r = 'zhenghe';
    ZHD.verbindungen.forEach(function (v) {
      var b = el('button', 'zhbar', String(v.nr)); b.type = 'button'; b.dataset.nr = v.nr;
      b.style.left = pct(v.von) + '%'; b.style.width = 'calc(' + (pct(v.bis) - pct(v.von)) + '% - 2px)';
      b.style.setProperty('--c', ZH_COL[v.nr - 1]); b.style.setProperty('--cbg', rgba(ZH_COL[v.nr - 1], 0.22));
      b.title = v.name + ': ' + v.stationen;
      b.addEventListener('click', function () { setYear(v.von); });
      lane.appendChild(b);
    });
    lanes.appendChild(lane);
    var evl = el('div', 'lane zhev'); evl.dataset.r = 'zhev'; evl.style.setProperty('--c', '#5fdc8a');
    ZHD.ereignisse.forEach(function (e) {
      var k = el('button', 'mk', String(e.jahr)); k.type = 'button'; k.dataset.y = e.jahr; k.style.left = pct(e.jahr) + '%';
      k.title = e.jahr + ': ' + e.titel;
      k.addEventListener('click', function () { setYear(e.jahr); toast(e.jahr + ': ' + e.titel + '. ' + e.text); });
      evl.appendChild(k);
    });
    lanes.appendChild(evl);
    $('#lanesToggle').hidden = true;
    updateMarkersMing();
  }
  function updateMarkersMing() {
    var y = state.year, cur = null;
    document.querySelectorAll('.zhbar').forEach(function (b) {
      var v = zhById('zh' + b.dataset.nr);
      b.classList.toggle('on', zhAktiv(v, y)); b.classList.toggle('off', !ZH.on || !ZH.fahrt[v.nr]);
    });
    ZHD.ereignisse.forEach(function (e) { if (e.jahr <= y) cur = e; });
    document.querySelectorAll('.lane.zhev .mk').forEach(function (k) { k.classList.toggle('on', !!cur && +k.dataset.y === cur.jahr); });
  }
  function buildZhChips() {
    var box = $('#zhChips');
    ZHD.verbindungen.forEach(function (v) {
      var b = el('button', 'chip zc on'); b.type = 'button'; b.dataset.nr = v.nr; b.setAttribute('aria-pressed', 'true');
      b.style.setProperty('--c', ZH_COL[v.nr - 1]); b.style.setProperty('--cbg', rgba(ZH_COL[v.nr - 1], 0.25));
      b.appendChild(el('i')); b.appendChild(el('span', null, v.nr + '. Fahrt ' + v.von + '–' + String(v.bis).slice(2)));
      b.title = v.name + ': ' + v.stationen;
      b.addEventListener('click', function () {
        ZH.fahrt[v.nr] = !ZH.fahrt[v.nr]; b.classList.toggle('on', ZH.fahrt[v.nr]); b.setAttribute('aria-pressed', ZH.fahrt[v.nr]);
        lastKey = ''; setYear(state.year);
      });
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
        var c = this.__c; if (c) toast('🐪 Karawane zwischen ' + c.e.a.name + ' und ' + c.e.b.name + ': regionaler Zwischenhandel (Etappenhandel)');
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
      var sc = globe.getScreenCoords(p[1], p[0], 0.012), x = sc.x + gr.left, yy = sc.y + gr.top;
      if (d3.geoDistance([pov.lng, pov.lat], p) > 1.35 || x < -20 || yy < -20 || x > innerWidth + 20 || yy > innerHeight + 20) { e.classList.add('hide'); return; }
      e.classList.remove('hide');
      e.style.transform = 'translate(' + x.toFixed(1) + 'px,' + yy.toFixed(1) + 'px)';
      if (dir) {
        var q = karPoint(c.e, Math.max(0, Math.min(1, s + dir * 0.03))), sq = globe.getScreenCoords(q[1], q[0], 0.012);
        if (Math.abs(sq.x - sc.x) > 0.5) e.classList.toggle('flip', sq.x > sc.x);
      }
    });
  }

  /* ---------- Epoche umschalten ---------- */
  function setEpoche(ep) {
    if (state.epoche === ep || !EPOCHEN[ep]) return;
    if (playTimer) togglePlay();
    if (mapOpen) finishClose();
    closeInfo(); stopIntro();
    state.jahrJe[state.epoche] = state.year;
    state.epoche = ep;
    var E = EPOCHEN[ep]; YMIN = E.min; YMAX = E.max;
    document.documentElement.classList.toggle('ming', ep === 'ming');
    [['#epAntike', 'antike'], ['#epMing', 'ming']].forEach(function (x) { var on = x[1] === ep; $(x[0]).classList.toggle('on', on); $(x[0]).setAttribute('aria-pressed', on); });
    $('#h1sub').textContent = E.titel; $('#sideTitle').textContent = E.side;
    var yi = $('#year'); yi.min = YMIN; yi.max = YMAX;
    globe.pathTransitionDuration(ep === 'ming' ? 2600 : 600);   // Ming: neue Fahrten zeichnen sich sichtbar ein
    KAR.prevY = null;
    buildTicks(); buildLanes(); lastKey = '';
    setYear(state.jahrJe[ep] != null ? state.jahrJe[ep] : E.start);
    if (ep === 'ming') fly(8, 82, homeAlt()); else fly(36, 62, homeAlt());
  }

  /* ---------- Start: Linien von der Legende zum Reich ---------- */
  var intro = { on: false, raf: 0, timer: 0, els: {} };
  function startIntro() {
    var svg = $('#intro'), NS = 'http://www.w3.org/2000/svg';
    function mk(tag, attrs) { var e = document.createElementNS(NS, tag); for (var k in attrs) e.setAttribute(k, attrs[k]); svg.appendChild(e); return e; }
    ['rom', 'han'].forEach(function (r) {
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
      ['rom', 'han'].forEach(function (r) {
        var e = intro.els[r], chip = $(r === 'rom' ? '#tglRom' : '#tglHan');
        var z = M(r).zentrum, ang = d3.geoDistance([pov.lng, pov.lat], z);
        var rc0 = chip.getBoundingClientRect(), pb = $('#panelBody').getBoundingClientRect();
        var inPanel = rc0.top >= pb.top - 2 && rc0.bottom <= pb.bottom + 2;
        var vis = !collapsed && inPanel && !mapOpen && state.on[r] && regionsAt(r, state.year).length && ang < 1.35;
        var op = vis ? Math.min(1, (1.35 - ang) / 0.25) : 0;
        ['path', 'start', 'ring', 'dot'].forEach(function (k) { e[k].setAttribute('visibility', op ? 'visible' : 'hidden'); });
        if (!op) return;
        var rc = chip.getBoundingClientRect(), x1 = rc.right, y1 = rc.top + rc.height / 2;
        var p = globe.getScreenCoords(z[1], z[0], 0.01), x2 = p.x, y2 = p.y;
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
    if (globe && !mapOpen) setTimeout(function () { var pv = globe.pointOfView(); globe.pointOfView({ lat: pv.lat, lng: pv.lng, altitude: homeAlt() }, 600); }, 250);
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
    ['#goRom', '#goHan', '#goAll'].forEach(function (id) { $(id).addEventListener('click', function () { if (compact()) setPanel(true, true); }); });
    $('#modeSat').addEventListener('click', function () { state.mode = 'sat'; applyMode(); });
    $('#modeSchem').addEventListener('click', function () { state.mode = 'schem'; applyMode(); });
    function setAll(v) {
      DATA.reihen.forEach(function (r) { setOn(r, v, true); });
      buildLanes(); lastKey = ''; setYear(state.year);
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
    $('#tglRom').addEventListener('click', function () { setOn('rom', !state.on.rom); });
    $('#tglHan').addEventListener('click', function () { setOn('han', !state.on.han); });
    $('#tglOrte').addEventListener('click', function () {
      state.orte = !state.orte; this.classList.toggle('on', state.orte); this.setAttribute('aria-pressed', state.orte); lastKey = ''; setYear(state.year);
    });
    $('#tglSchl').addEventListener('click', function () {
      state.schlachten = !state.schlachten; this.classList.toggle('on', state.schlachten); this.setAttribute('aria-pressed', state.schlachten);
      $('#lanes').classList.toggle('noschl', !state.schlachten); lastKey = ''; setYear(state.year);
    });
    function setTrade(k, v) {
      TRADE[k] = v;
      var b = $({ on: '#tglHandel', land: '#tglLand', see: '#tglSee', waren: '#tglWaren', gesandt: '#tglGes', karawanen: '#tglKar' }[k]);
      b.classList.toggle('on', v); b.setAttribute('aria-pressed', v);
      if (k === 'on') {
        $('#handelSub').classList.toggle('off', !v);
        document.querySelectorAll('#handelSub button').forEach(function (x) { x.disabled = !v; });
        if (!v) closeInfo();
      }
      lastKey = ''; setYear(state.year);
    }
    $('#tglHandel').addEventListener('click', function () { setTrade('on', !TRADE.on); });
    $('#tglLand').addEventListener('click', function () { setTrade('land', !TRADE.land); });
    $('#tglSee').addEventListener('click', function () { setTrade('see', !TRADE.see); });
    $('#tglWaren').addEventListener('click', function () { setTrade('waren', !TRADE.waren); });
    $('#tglGes').addEventListener('click', function () { setTrade('gesandt', !TRADE.gesandt); });
    $('#tglKar').addEventListener('click', function () { setTrade('karawanen', !TRADE.karawanen); });
    // Epochen und Zheng He
    $('#epAntike').addEventListener('click', function () { setEpoche('antike'); });
    $('#epMing').addEventListener('click', function () { setEpoche('ming'); });
    $('#tglZh').addEventListener('click', function () {
      ZH.on = !ZH.on; this.classList.toggle('on', ZH.on); this.setAttribute('aria-pressed', ZH.on);
      document.querySelectorAll('#zhChips .chip, #tglZhWaren').forEach(function (x) { x.disabled = !ZH.on; });
      lastKey = ''; setYear(state.year);
    });
    $('#tglZhWaren').addEventListener('click', function () {
      ZH.waren = !ZH.waren; this.classList.toggle('on', ZH.waren); this.setAttribute('aria-pressed', ZH.waren); lastKey = ''; setYear(state.year);
    });
    $('#btnZhInfo').addEventListener('click', openZhBackground);
    $('#btnZhWaren').addEventListener('click', function () { openWaren(ZHD); });
    $('#goIndik').addEventListener('click', function () { fly(8, 82, homeAlt() * 0.85); });
    $('#btnWaren').addEventListener('click', openWaren);
    $('#tinfoClose').addEventListener('click', closeInfo);
    $('#tinfo').addEventListener('click', function (e) { if (e.target === this) closeInfo(); });
    $('#wmodalClose').addEventListener('click', function () { $('#wmodal').hidden = true; });
    $('#wmodal').addEventListener('click', function (e) { if (e.target === this) this.hidden = true; });
    $('#tglRot').addEventListener('click', function () {
      state.rotate = !state.rotate; this.classList.toggle('on', state.rotate); this.setAttribute('aria-pressed', state.rotate); globe.controls().autoRotate = state.rotate && !mapOpen;
    });
    $('#goRom').addEventListener('click', function () { fly(41.5, 14, 1.0); });
    $('#goHan').addEventListener('click', function () { fly(34, 108, 1.1); });
    $('#goAll').addEventListener('click', function () { fly(36, 62, homeAlt()); });
    $('#tglStandort').addEventListener('click', toggleStandort);
    $('#year').addEventListener('input', function (e) { setYear(+e.target.value, true); });
    $('#play').addEventListener('click', togglePlay);
    $('#yMinus').addEventListener('click', function () { setYear(state.year - 10); });
    $('#yPlus').addEventListener('click', function () { setYear(state.year + 10); });
    $('#mapClose').addEventListener('click', closeMap);
    $('#mapOverlay').addEventListener('click', function (e) { if (e.target === this) closeMap(); });
    $('#btnInfo').addEventListener('click', function () { $('#modal').hidden = false; });
    $('#modalClose').addEventListener('click', function () { $('#modal').hidden = true; });
    $('#modal').addEventListener('click', function (e) { if (e.target === this) this.hidden = true; });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        if (!$('#wmodal').hidden) { $('#wmodal').hidden = true; return; }
        if (!$('#modal').hidden) { $('#modal').hidden = true; return; }
        if (closeInfo()) return;
        closeMap(); return;
      }
      if (e.target && (e.target.tagName === 'INPUT' || (e.target.closest && e.target.closest('.troute,.tplace,.wchips-map')))) return;
      if (e.key === 'ArrowLeft') setYear(state.year - (e.shiftKey ? 10 : 1));
      if (e.key === 'ArrowRight') setYear(state.year + (e.shiftKey ? 10 : 1));
      if (e.key === ' ' && !mapOpen && e.target.tagName !== 'BUTTON') { e.preventDefault(); togglePlay(); }
    });
  }

  /* ---------- Start ---------- */
  function load(url) { return fetch(url).then(function (r) { if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); }); }
  Promise.all([load('data/reiche.json'), load('data/land.json'), load('data/land_rom.json'), load('data/land_han.json'), load('data/handel.json'), load('data/zhenghe.json')]).then(function (res) {
    DATA = res[0]; LAND = res[1]; LAND_FLAT.rom = res[2]; LAND_FLAT.han = res[3]; HANDEL = res[4]; ZHD = res[5];
    initTrade(); initZh(); buildZhChips();
    document.querySelectorAll('.camel-ico').forEach(function (x) { x.innerHTML = CAMEL; });
    DATA.reihen.forEach(function (r) { state.on[r] = !!M(r).haupt; EVENTS[r] = []; });
    DATA.ereignisse.forEach(function (e) { EVENTS[e.reich].push(e); });
    DATA.reihen.forEach(function (r) { EVENTS[r].sort(function (a, b) { return a.jahr - b.jahr; }); });
    DATA.regionen.forEach(function (f) { BYID[f.properties.id] = f; });
    var tl = $('#timeline'), setTlh = function () { document.documentElement.style.setProperty('--tlh', tl.offsetHeight + 'px'); };
    if (window.ResizeObserver) new ResizeObserver(setTlh).observe(tl);
    initGlobe(); buildChips(); buildTicks(); buildLanes(); bind(); lastKey = ''; setYear(state.year);
    setTimeout(startIntro, 600);
    window.__tafelbild = { state: state, trade: TRADE, zh: ZH, kar: KAR, openMap: openMap, closeMap: closeMap, setYear: setYear, setEpoche: setEpoche, globe: globe, tradeVisible: tradeVisible, zhVisible: zhVisible };
  }).catch(function (err) {
    var m = document.createElement('div'); m.className = 'toast show'; m.style.bottom = '50%';
    m.textContent = 'Daten konnten nicht geladen werden. Bitte die Seite über einen Webserver öffnen (nicht per Doppelklick). ' + err.message;
    document.body.appendChild(m);
  });
})();
