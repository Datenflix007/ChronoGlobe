/* Digitales Tafelbild: Rom und China – Globus, Zeitleiste, Kartenrolle
   Abhängigkeiten (lokal in vendor/): globe.gl, d3. Daten: data/*.json */
(function () {
  'use strict';

  var COL = {
    rom: { cap: 'rgba(196,52,44,0.62)', line: '#7d1f1a', map: 'rgba(181,54,47,0.74)', mapLine: '#6e1d18', solid: '#c4342c', name: 'Römisches Reich' },
    han: { cap: 'rgba(224,158,12,0.66)', line: '#8a5d00', map: 'rgba(212,154,10,0.80)', mapLine: '#7a5200', solid: '#e09e0c', name: 'Han-Reich' }
  };
  var YMIN = -300, YMAX = 480;
  var state = { mode: 'sat', on: { rom: true, han: true }, orte: false, rotate: true, year: 117 };
  var DATA, LAND, LAND_FLAT = {}, STAGES = {}, globe, mapOpen = false, mapReich = null, playTimer = null, lastKey = '';

  function $(s) { return document.querySelector(s); }
  function fmtYear(y) { return y < 0 ? (-y) + ' v. Chr.' : y + ' n. Chr.'; }
  function toast(msg) {
    var t = $('#toast'); t.textContent = msg; t.classList.add('show');
    clearTimeout(toast._t); toast._t = setTimeout(function () { t.classList.remove('show'); }, 3200);
  }

  /* ---------- Daten ---------- */
  function buildStages() {
    ['rom', 'han'].forEach(function (r) {
      var m = {};
      DATA.stufen.filter(function (f) { return f.properties.reich === r; }).forEach(function (f) {
        var j = f.properties.jahr;
        if (!m[j]) m[j] = { reich: r, jahr: j, label: f.properties.label, titel: f.properties.titel, note: f.properties.note, features: [] };
        m[j].features.push(f);
      });
      STAGES[r] = Object.keys(m).map(function (k) { return m[k]; }).sort(function (a, b) { return a.jahr - b.jahr; });
    });
  }
  function activeStage(r, y) {
    var meta = DATA.meta[r];
    if (y < meta.von || y > meta.bis) return null;
    var cur = STAGES[r][0];
    STAGES[r].forEach(function (s) { if (s.jahr <= y) cur = s; });
    return cur;
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
    var c = COL[p.reich];
    return p.art === 'einfluss' ? c.cap.replace(/0\.\d+\)/, '0.30)') : c.cap;
  }
  function visiblePolys() {
    var a = [];
    if (state.mode === 'schem') a.push(LANDF);
    ['rom', 'han'].forEach(function (r) {
      if (!state.on[r]) return;
      var s = activeStage(r, state.year);
      if (s) a.push.apply(a, s.features);
    });
    return a;
  }
  function visibleCities() {
    if (!state.orte) return [];
    return DATA.orte.filter(function (o) {
      if (!state.on[o.reich]) return false;
      if (!activeStage(o.reich, state.year)) return false;
      return state.year >= o.von && (o.bis === null || state.year <= o.bis);
    });
  }
  function refreshGlobe() {
    globe.polygonsData(visiblePolys());
    globe.labelsData(visibleCities());
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
  function initGlobe() {
    LANDF = { type: 'Feature', properties: { kind: 'land' }, geometry: LAND.geometry };
    globe = Globe()($('#globe'))
      .width(window.innerWidth).height(window.innerHeight)
      .polygonGeoJsonGeometry(function (f) { return f.geometry; })
      .polygonCapColor(capColor)
      .polygonSideColor(function (f) { return f.properties.kind === 'land' ? 'rgba(0,0,0,0)' : 'rgba(0,0,0,0.15)'; })
      .polygonStrokeColor(function (f) {
        var p = f.properties; return p.kind === 'land' ? 'rgba(90,80,55,0.55)' : COL[p.reich].line;
      })
      .polygonAltitude(function (f) { return f.properties.kind === 'land' ? 0.0012 : 0.0045; })
      .polygonCapCurvatureResolution(3)
      .polygonsTransitionDuration(250)
      .labelLat('lat').labelLng('lng').labelText('name')
      .labelSize(0.85).labelDotRadius(0.28).labelAltitude(0.006).labelResolution(2)
      .labelColor(function (d) { return d.reich === 'rom' ? '#ffd9d6' : '#ffe9a8'; });
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
      var pov = globe.pointOfView();
      if (pov.altitude <= 0.42) tryOpenMap();
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

  /* Welches Reich liegt unter dem Blickpunkt? */
  function pickReich() {
    var pov = globe.pointOfView(), best = null, bestD = 1e9;
    ['rom', 'han'].forEach(function (r) {
      if (!state.on[r] || !activeStage(r, state.year)) return;
      var s = activeStage(r, state.year), inside = false;
      s.features.forEach(function (f) { if (d3.geoContains(f, [pov.lng, pov.lat])) inside = true; });
      var z = DATA.meta[r].zentrum;
      var d = d3.geoDistance([pov.lng, pov.lat], z) * 180 / Math.PI;
      if (inside) d = Math.min(d, 1);
      if (d < bestD) { bestD = d; best = r; }
    });
    return bestD <= 38 ? best : null;
  }
  function tryOpenMap(force) {
    var r = force || pickReich();
    if (!r) {
      var any = ['rom', 'han'].some(function (k) { return state.on[k] && activeStage(k, state.year); });
      toast(any ? 'Zum Entrollen auf Rom oder China hineinzoomen.' : 'Bitte ein Reich einblenden (und passendes Jahr wählen).');
      return;
    }
    openMap(r);
  }

  /* ---------- Karten-Infokarten ---------- */
  function renderCards() {
    var box = $('#cards'); box.innerHTML = '';
    var shown = 0;
    ['rom', 'han'].forEach(function (r) {
      if (!state.on[r]) return;
      var s = activeStage(r, state.year);
      var d = document.createElement('div'); d.className = 'card'; d.style.setProperty('--c', COL[r].solid);
      if (!s) {
        d.classList.add('none');
        d.innerHTML = '<div class="k"></div><div class="t"></div>';
        d.querySelector('.k').textContent = COL[r].name;
        d.querySelector('.t').textContent = state.year < DATA.meta[r].von ? 'Besteht in diesem Jahr noch nicht.' : 'Besteht in diesem Jahr nicht mehr.';
      } else {
        d.innerHTML = '<div class="k"></div><div class="t"></div><div class="y"></div><p></p><button type="button">Karte entrollen</button>';
        d.querySelector('.k').textContent = COL[r].name;
        d.querySelector('.t').textContent = s.titel;
        d.querySelector('.y').textContent = 'Stand: ' + s.label;
        d.querySelector('p').textContent = s.note;
        d.querySelector('button').addEventListener('click', function () { openMap(r); });
        shown++;
      }
      box.appendChild(d);
    });
  }

  /* ---------- Zeitleiste ---------- */
  function buildTimeline() {
    var span = YMAX - YMIN;
    function pct(y) { return ((y - YMIN) / span * 100); }
    var ticks = $('#ticks');
    for (var y = -300; y <= 480; y += 50) {
      var t = document.createElement('div'); t.style.left = pct(y) + '%';
      if (y % 100) { t.className = 'tick minor'; }
      else { t.className = 'tick'; t.textContent = y === 0 ? 'Chr. Geb.' : (y < 0 ? (-y) + ' v. Chr.' : y + ' n. Chr.'); }
      ticks.appendChild(t);
    }
    var lanes = $('#lanes');
    var zero = document.createElement('div'); zero.className = 'zero'; zero.style.left = pct(0) + '%'; lanes.appendChild(zero);
    var cur = document.createElement('div'); cur.className = 'cursor'; lanes.appendChild(cur);
    [['rom', '#rowRom'], ['han', '#rowHan']].forEach(function (p) {
      var row = $(p[1]), m = DATA.meta[p[0]];
      var era = document.createElement('div'); era.className = 'era';
      era.style.left = pct(Math.max(YMIN, m.von)) + '%'; era.style.width = (pct(Math.min(YMAX, m.bis)) - pct(Math.max(YMIN, m.von))) + '%';
      var nm = document.createElement('span'); nm.className = 'nm'; nm.textContent = COL[p[0]].name; era.appendChild(nm);
      era.title = COL[p[0]].name + ': ' + fmtYear(m.von) + ' bis ' + fmtYear(m.bis);
      row.appendChild(era);
      STAGES[p[0]].forEach(function (s) {
        var b = document.createElement('button'); b.type = 'button'; b.className = 'mk'; b.dataset.y = s.jahr;
        b.style.left = pct(s.jahr) + '%'; b.textContent = fmtYear(s.jahr).replace(' Chr.', '');
        b.title = s.label + ': ' + s.titel;
        b.addEventListener('click', function () { setYear(s.jahr); });
        row.appendChild(b);
      });
    });
  }
  function updateMarkers() {
    document.querySelectorAll('.mk').forEach(function (b) {
      var r = b.parentNode.id === 'rowRom' ? 'rom' : 'han';
      var s = activeStage(r, state.year);
      b.classList.toggle('on', !!s && s.jahr === +b.dataset.y);
    });
  }
  function setYear(y, fromSlider) {
    y = Math.max(YMIN, Math.min(YMAX, Math.round(y)));
    state.year = y;
    if (!fromSlider) $('#year').value = y;
    $('#yearOut').textContent = fmtYear(y);
    $('#track').style.setProperty('--pf', (y - YMIN) / (YMAX - YMIN));
    var key = ['rom', 'han'].map(function (r) { var s = activeStage(r, y); return s ? s.jahr : 'x'; }).join('|') + '|' + state.orte;
    if (key !== lastKey) { lastKey = key; refreshGlobe(); renderCards(); updateMarkers(); }
    if (mapOpen) drawMap(mapReich, true);
  }
  function togglePlay() {
    if (playTimer) { clearInterval(playTimer); playTimer = null; $('#play').textContent = '▶'; return; }
    if (state.year >= YMAX) setYear(YMIN);
    $('#play').textContent = '❚❚';
    playTimer = setInterval(function () {
      if (state.year >= YMAX) { togglePlay(); return; }
      setYear(state.year + 2);
    }, 45);
  }

  /* ---------- Flache Reichskarte ---------- */
  var W = 1200, H = 720;
  function makeProj(r) {
    var m = DATA.meta[r], b = m.rahmen, w = b[0], s = b[1], e = b[2], n = b[3];
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
    rom: [['Germanen', 11, 53.6, -113, null], ['Parther', 50.5, 34, -247, 224]],
    han: [['Xiongnu', 104, 47.5, -209, 93], ['Xianbei', 112, 47.5, 93, null], ['Kuschana', 76, 33, 30, null]]
  };

  var closeTimer = null;
  function finishClose() {
    clearTimeout(closeTimer); closeTimer = null;
    $('#mapOverlay').classList.remove('show'); $('#mapOverlay').setAttribute('aria-hidden', 'true');
    mapOpen = false; mapReich = null;
    globe.controls().autoRotate = state.rotate;
    var pov = globe.pointOfView(); globe.pointOfView({ lat: pov.lat, lng: pov.lng, altitude: 0.9 }, 600);
  }
  function openMap(r) {
    if (closeTimer) finishClose();
    if (mapOpen) return;
    mapOpen = true; mapReich = r;
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
    var svg = d3.select('#flat');
    var s = activeStage(r, state.year);
    var proj = makeProj(r), path = d3.geoPath(proj);
    var land = LAND_FLAT[r];
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
    svg.append('path').attr('d', path(land)).attr('fill', '#efe3c2').attr('stroke', '#8d7b57').attr('stroke-width', 1.1).attr('stroke-linejoin', 'round');

    var layer = svg.append('g');
    if (s) {
      s.features.forEach(function (ft) {
        var einfl = ft.properties.art === 'einfluss';
        layer.append('path').attr('d', path(ft)).attr('fill', einfl ? 'url(#hatch)' : COL[r].map)
          .attr('stroke', einfl ? '#9a6b00' : COL[r].mapLine).attr('stroke-width', einfl ? 1.2 : 2.2).attr('stroke-linejoin', 'round');
      });
      if (soft) layer.attr('opacity', 0.15).transition().duration(350).attr('opacity', 1);
    }
    // Meere/Regionen und Nachbarn
    var tg = svg.append('g').attr('font-family', 'Georgia, serif').attr('text-anchor', 'middle');
    function label(txt, lon, lat, rot, size, style, col) {
      var xy = proj([lon, lat]); if (!xy) return;
      tg.append('text').attr('x', xy[0]).attr('y', xy[1]).attr('transform', rot ? 'rotate(' + rot + ' ' + xy[0] + ' ' + xy[1] + ')' : null)
        .attr('font-size', size).attr('font-style', style).attr('fill', col).attr('stroke', 'rgba(239,227,194,.85)').attr('stroke-width', 3).attr('paint-order', 'stroke')
        .attr('letter-spacing', style === 'italic' ? 2 : 0).text(txt);
    }
    SEA_LABELS[r].forEach(function (l) { label(l[0], l[1], l[2], l[3] ? -l[3] / 4 : 0, 17, 'italic', '#3f6b78'); });
    NEIGH[r].forEach(function (n) {
      if (state.year >= n[3] && (n[4] === null || state.year <= n[4])) label(n[0], n[1], n[2], 0, 18, 'italic', '#6b5a3a');
    });
    // Städte
    var cg = svg.append('g').attr('font-family', 'Georgia, serif');
    DATA.orte.forEach(function (o) {
      if (o.reich !== r || !s) return;
      if (state.year < o.von || (o.bis !== null && state.year > o.bis)) return;
      var xy = proj([o.lng, o.lat]); if (!xy) return;
      cg.append('circle').attr('cx', xy[0]).attr('cy', xy[1]).attr('r', 5).attr('fill', '#2b2110').attr('stroke', '#f5ecd2').attr('stroke-width', 1.5);
      cg.append('text').attr('x', xy[0] + 9).attr('y', xy[1] + 5).attr('font-size', 17).attr('fill', '#2b2110').attr('stroke', 'rgba(239,227,194,.9)').attr('stroke-width', 3.5).attr('paint-order', 'stroke').attr('font-weight', 600).text(o.name);
    });
    // Nordpfeil
    var na = svg.append('g').attr('transform', 'translate(' + (W - 78) + ',150)');
    na.append('path').attr('d', 'M0,-34 L11,10 L0,2 L-11,10 Z').attr('fill', '#3b2d14');
    na.append('text').attr('y', 30).attr('text-anchor', 'middle').attr('font-family', 'Georgia, serif').attr('font-size', 17).attr('fill', '#3b2d14').text('N');
    // Papierkörnung
    svg.append('rect').attr('width', W).attr('height', H).attr('filter', 'url(#paper)').attr('opacity', 0.22).attr('pointer-events', 'none');

    // Kopf, Legende, Stufen
    var ct = $('#cartouche'); ct.innerHTML = '';
    var t1 = document.createElement('div'); t1.className = 'ct'; t1.textContent = s ? (r === 'rom' ? 'Das Römische Reich' : 'Das Reich der Han') : COL[r].name;
    var t2 = document.createElement('div'); t2.className = 'cs'; t2.textContent = s ? s.titel + ' · ' + s.label : fmtYear(state.year) + ': besteht nicht';
    ct.appendChild(t1); ct.appendChild(t2);
    if (s) { var p = document.createElement('p'); p.textContent = s.note; ct.appendChild(p); }
    var lg = $('#legend'); lg.innerHTML = '';
    var hasInfl = s && s.features.some(function (x) { return x.properties.art === 'einfluss'; });
    var l1 = document.createElement('div'); var i1 = document.createElement('i'); i1.style.background = COL[r].map;
    l1.appendChild(i1); l1.appendChild(document.createTextNode(COL[r].name + ' (vereinfacht)')); lg.appendChild(l1);
    if (hasInfl) {
      var l2 = document.createElement('div'); var i2 = document.createElement('i'); i2.style.background = 'repeating-linear-gradient(45deg,#e9c55f,#e9c55f 3px,#9a6b00 3px,#9a6b00 4px)';
      l2.appendChild(i2); l2.appendChild(document.createTextNode('Einflussbereich (Westliche Regionen)')); lg.appendChild(l2);
    }
    var sb = $('#stagebar'); sb.innerHTML = '';
    STAGES[r].forEach(function (st) {
      var b = document.createElement('button'); b.type = 'button'; b.textContent = st.label.replace('um ', '');
      if (s && s.jahr === st.jahr) b.className = 'on';
      b.addEventListener('click', function () { setYear(st.jahr); });
      sb.appendChild(b);
    });
  }

  /* ---------- Bedienung ---------- */
  function bind() {
    $('#modeSat').addEventListener('click', function () { state.mode = 'sat'; applyMode(); });
    $('#modeSchem').addEventListener('click', function () { state.mode = 'schem'; applyMode(); });
    function tg(id, key) {
      var b = $(id);
      b.addEventListener('click', function () {
        state.on[key] = !state.on[key]; b.classList.toggle('on', state.on[key]); b.setAttribute('aria-pressed', state.on[key]);
        lastKey = ''; setYear(state.year);
      });
    }
    tg('#tglRom', 'rom'); tg('#tglHan', 'han');
    $('#tglOrte').addEventListener('click', function () {
      state.orte = !state.orte; this.classList.toggle('on', state.orte); this.setAttribute('aria-pressed', state.orte); lastKey = ''; setYear(state.year);
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
    buildStages(); initGlobe(); buildTimeline(); bind(); lastKey = ''; setYear(state.year);
    window.__tafelbild = { state: state, openMap: openMap, closeMap: closeMap, setYear: setYear, globe: globe };
  }).catch(function (err) {
    var m = document.createElement('div'); m.className = 'toast show'; m.style.bottom = '50%';
    m.textContent = 'Daten konnten nicht geladen werden. Bitte die Seite über einen Webserver öffnen (nicht per Doppelklick). ' + err.message;
    document.body.appendChild(m);
  });
})();
