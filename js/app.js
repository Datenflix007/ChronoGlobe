/* Digitales Tafelbild: Rom und China – Globus, Zeitleiste, Kartenrolle
   Abhängigkeiten (lokal in vendor/): globe.gl, d3. Daten: data/*.json (erzeugt mit build_reiche.py) */
(function () {
  'use strict';

  var YMIN = -300, YMAX = 480, TEILUNG = 395, OSTROM = '#7b3fa0', SCHLACHT_JAHRE = 25;
  var state = { mode: 'sat', on: {}, orte: false, rotate: true, schlachten: true, year: 117 };
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
  var SEA_URL = (function () {
    var c = document.createElement('canvas'); c.width = c.height = 4;
    var x = c.getContext('2d'); x.fillStyle = '#8fb8d0'; x.fillRect(0, 0, 4, 4); return c.toDataURL();
  })();
  var LANDF = null;

  function capColor(f) {
    var p = f.properties || {};
    if (p.kind === 'land') return '#e7dcc0';
    var c = regionColor(f, state.year), a = p.art === 'einfluss' ? 0.3 : (M(p.reich).haupt ? 0.62 : 0.55);
    if (f.__flash && Date.now() - f.__flash < 1300) return rgba(c, Math.min(0.9, a + 0.25));
    return rgba(c, a);
  }
  function visiblePolys() {
    var a = [];
    if (state.mode === 'schem') a.push(LANDF);
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
    var el = document.createElement('div'); el.className = 'battle';
    el.innerHTML = SWORDS + '<span></span>';
    el.querySelector('span').textContent = d.name + ' ' + shortYear(d.jahr);
    el.title = d.name + ' (' + fmtYear(d.jahr) + '): ' + d.note;
    el.addEventListener('click', function (e) { e.stopPropagation(); toast('⚔ ' + d.name + ', ' + fmtYear(d.jahr) + ': ' + d.note); });
    d.__el = el; return el;
  }
  function refreshGlobe() {
    var polys = visiblePolys(), now = Date.now();
    if (prevVis) polys.forEach(function (f) { if (f.properties.id !== undefined && !prevVis.has(f)) f.__flash = now; });
    prevVis = new Set(polys);
    globe.polygonsData(polys);
    globe.labelsData(visibleCities());
    globe.htmlElementsData(visibleBattles(state.year));
    clearTimeout(flashTimer);
    flashTimer = setTimeout(function () { globe.polygonCapColor(capColor); }, 1350);
  }
  function applyMode() {
    var sat = state.mode === 'sat';
    globe.globeImageUrl(sat ? 'img/earth-blue-marble.jpg' : SEA_URL);
    globe.bumpImageUrl(sat ? 'img/earth-topology.png' : '');
    globe.backgroundImageUrl(sat ? 'img/night-sky.png' : '');
    globe.backgroundColor(sat ? '#000010' : '#14202e');
    globe.showAtmosphere(true);
    globe.atmosphereColor(sat ? '#6fb1ff' : '#9fd0ee');
    globe.atmosphereAltitude(sat ? 0.17 : 0.09);
    $('#modeSat').classList.toggle('on', sat); $('#modeSat').setAttribute('aria-pressed', sat);
    $('#modeSchem').classList.toggle('on', !sat); $('#modeSchem').setAttribute('aria-pressed', !sat);
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
      .labelLat('lat').labelLng('lng').labelText('name')
      .labelSize(0.85).labelDotRadius(0.28).labelAltitude(0.006).labelResolution(2)
      .labelColor(function (d) { return mix(M(d.reich).farbe, '#ffffff', 0.7); })
      .htmlLat('lat').htmlLng('lng').htmlAltitude(0.01).htmlElement(battleEl).htmlTransitionDuration(0);
    var c = globe.controls();
    c.autoRotate = state.rotate; c.autoRotateSpeed = 0.35;
    c.minDistance = 118; c.maxDistance = 520; c.zoomSpeed = 0.9; c.enablePan = false;
    globe.pointOfView({ lat: 36, lng: 62, altitude: 2.7 }, 0);
    applyMode();
    window.addEventListener('resize', function () { globe.width(window.innerWidth).height(window.innerHeight); });

    // Hineinzoomen => Karte entrollen
    var el = globe.renderer().domElement;
    el.addEventListener('wheel', function (e) {
      if (mapOpen || e.deltaY >= 0) return;
      if (globe.pointOfView().altitude <= 0.42) tryOpenMap();
    }, { passive: true });
    var pinchBase = null;
    el.addEventListener('touchstart', function () { pinchBase = globe.pointOfView().altitude; }, { passive: true });
    el.addEventListener('touchend', function () {
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
    var ticks = $('#ticks');
    for (var y = -300; y <= 480; y += 50) {
      var t = document.createElement('div'); t.style.left = pct(y) + '%';
      if (y % 100) { t.className = 'tick minor'; }
      else { t.className = 'tick'; t.textContent = y === 0 ? 'Chr. Geb.' : fmtYear(y); }
      ticks.appendChild(t);
    }
  }
  function buildLanes() {
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
    document.querySelectorAll('.lane').forEach(function (lane) {
      var e = activeEvent(lane.dataset.r, state.year);
      lane.querySelectorAll('.mk').forEach(function (b) { b.classList.toggle('on', !!e && e.jahr === +b.dataset.y); });
    });
    document.querySelectorAll('.bt').forEach(function (b) {
      var d = state.year - b.dataset.y; b.classList.toggle('on', d >= 0 && d <= SCHLACHT_JAHRE);
    });
  }
  function stateKey(y) {
    var ids = [];
    DATA.reihen.forEach(function (r) { if (state.on[r]) regionsAt(r, y).forEach(function (f) { ids.push(f.properties.id); }); });
    var ev = DATA.reihen.map(function (r) { var e = activeEvent(r, y); return e ? e.jahr : 'x'; }).join(',');
    var bs = visibleBattles(y).map(function (b) { return b.name; }).join(',');
    var nb = DATA.reihen.map(function (r) { return exists(r, y) ? 1 : 0; }).join('');
    return ids.join(',') + '|' + ev + '|' + bs + '|' + nb + '|' + (y >= TEILUNG) + '|' + state.orte + '|' + state.schlachten;
  }
  function setYear(y, fromSlider) {
    y = Math.max(YMIN, Math.min(YMAX, Math.round(y)));
    state.year = y;
    if (!fromSlider) $('#year').value = y;
    $('#yearOut').textContent = fmtYear(y);
    $('#track').style.setProperty('--pf', (y - YMIN) / (YMAX - YMIN));
    var key = stateKey(y);
    if (key !== lastKey) {
      lastKey = key; refreshGlobe(); renderCards(); updateMarkers(); updateChips();
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
    }, 70);
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
      var el = layer.append('path').attr('d', path(ft)).attr('fill', fillOf(ft))
        .attr('stroke', mix(c, '#000000', 0.45)).attr('stroke-width', mine ? 1.3 : 0.9)
        .attr('stroke-dasharray', p.art === 'einfluss' || !mine ? '4 3' : null);
      el.append('title').text(p.name + ' (' + (M(p.reich).name) + ', seit ' + fmtYear(p.von) + ')');
      if (soft && mapPrev && !mapPrev[p.id]) {
        el.attr('opacity', 0).attr('stroke', '#fff').attr('stroke-width', 3)
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
    var seen = {};
    DATA.orte.forEach(function (o) {
      if (o.reich !== r && !state.on[o.reich]) return;
      if (!regionsAt(o.reich, y).length || seen[o.name]) return;
      if (y < o.von || (o.bis !== null && y > o.bis)) return;
      var xy = proj([o.lng, o.lat]); if (!xy || xy[0] < 0 || xy[0] > W || xy[1] < 0 || xy[1] > H) return;
      seen[o.name] = 1;
      cg.append('circle').attr('cx', xy[0]).attr('cy', xy[1]).attr('r', 5).attr('fill', '#2b2110').attr('stroke', '#f5ecd2').attr('stroke-width', 1.5);
      cg.append('text').attr('x', xy[0] + 9).attr('y', xy[1] + 5).attr('font-size', 17).attr('fill', '#2b2110').attr('stroke', 'rgba(239,227,194,.9)').attr('stroke-width', 3.5).attr('paint-order', 'stroke').attr('font-weight', 600).text(o.name);
    });
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
        var vis = !collapsed && !mapOpen && state.on[r] && regionsAt(r, state.year).length && ang < 1.35;
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
    var el = globe.renderer().domElement;
    function first() { el.removeEventListener('pointerdown', first); el.removeEventListener('wheel', first); setTimeout(stopIntro, 1200); }
    el.addEventListener('pointerdown', first); el.addEventListener('wheel', first, { passive: true });
  }
  function stopIntro() {
    if (!intro.on) return;
    clearTimeout(intro.timer);
    var svg = $('#intro'); svg.classList.add('off');
    setTimeout(function () { intro.on = false; cancelAnimationFrame(intro.raf); svg.innerHTML = ''; }, 900);
  }

  /* ---------- Menü einklappen ---------- */
  function setPanel(collapsed) {
    var p = $('#panel'), b = $('#panelToggle');
    p.classList.toggle('collapsed', collapsed);
    b.setAttribute('aria-expanded', !collapsed);
    b.title = collapsed ? 'Menü ausklappen' : 'Menü einklappen';
    try { localStorage.setItem('tafelbild.panel', collapsed ? '0' : '1'); } catch (e) {}
  }

  /* ---------- Bedienung ---------- */
  function bind() {
    $('#panelToggle').addEventListener('click', function () { setPanel(!$('#panel').classList.contains('collapsed')); });
    try { if (localStorage.getItem('tafelbild.panel') === '0') setPanel(true); } catch (e) {}
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
    $('#tglRot').addEventListener('click', function () {
      state.rotate = !state.rotate; this.classList.toggle('on', state.rotate); this.setAttribute('aria-pressed', state.rotate); globe.controls().autoRotate = state.rotate && !mapOpen;
    });
    $('#goRom').addEventListener('click', function () { fly(41.5, 14, 1.0); });
    $('#goHan').addEventListener('click', function () { fly(34, 108, 1.1); });
    $('#goAll').addEventListener('click', function () { fly(36, 62, 2.7); });
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
      if (e.key === 'Escape') { if (!$('#modal').hidden) $('#modal').hidden = true; else closeMap(); return; }
      if (e.target && e.target.tagName === 'INPUT') return;
      if (e.key === 'ArrowLeft') setYear(state.year - (e.shiftKey ? 10 : 1));
      if (e.key === 'ArrowRight') setYear(state.year + (e.shiftKey ? 10 : 1));
      if (e.key === ' ' && !mapOpen && e.target.tagName !== 'BUTTON') { e.preventDefault(); togglePlay(); }
    });
  }

  /* ---------- Start ---------- */
  function load(url) { return fetch(url).then(function (r) { if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); }); }
  Promise.all([load('data/reiche.json'), load('data/land.json'), load('data/land_rom.json'), load('data/land_han.json')]).then(function (res) {
    DATA = res[0]; LAND = res[1]; LAND_FLAT.rom = res[2]; LAND_FLAT.han = res[3];
    DATA.reihen.forEach(function (r) { state.on[r] = !!M(r).haupt; EVENTS[r] = []; });
    DATA.ereignisse.forEach(function (e) { EVENTS[e.reich].push(e); });
    DATA.reihen.forEach(function (r) { EVENTS[r].sort(function (a, b) { return a.jahr - b.jahr; }); });
    DATA.regionen.forEach(function (f) { BYID[f.properties.id] = f; });
    var tl = $('#timeline'), setTlh = function () { document.documentElement.style.setProperty('--tlh', tl.offsetHeight + 'px'); };
    if (window.ResizeObserver) new ResizeObserver(setTlh).observe(tl);
    initGlobe(); buildChips(); buildTicks(); buildLanes(); bind(); lastKey = ''; setYear(state.year);
    setTimeout(startIntro, 600);
    window.__tafelbild = { state: state, openMap: openMap, closeMap: closeMap, setYear: setYear, globe: globe };
  }).catch(function (err) {
    var m = document.createElement('div'); m.className = 'toast show'; m.style.bottom = '50%';
    m.textContent = 'Daten konnten nicht geladen werden. Bitte die Seite über einen Webserver öffnen (nicht per Doppelklick). ' + err.message;
    document.body.appendChild(m);
  });
})();
