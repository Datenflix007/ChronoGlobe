/* ChronoGlobe · Landingpage: lebender Globus im Kopfbereich (rein dekorativ).
   Zeigt das Römische Reich und das Han-Reich um 117 n. Chr. sowie die Handelswege mit fließenden Lichtpunkten.
   Lädt nur Dateien dieses Servers. Bei „Bewegung reduzieren“ dreht der Globus nicht. */
(function () {
  'use strict';
  var box = document.getElementById('heldGlobus');
  if (!box || !window.Globe) return;
  var ruhig = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  function json(u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(u); return r.json(); }); }
  function groesse() { var w = box.clientWidth || 600; g.width(w).height(w); }

  var g = Globe({ animateIn: true })(box)
    .backgroundColor('rgba(0,0,0,0)')
    .globeImageUrl('img/earth-blue-marble.jpg')
    .bumpImageUrl('img/earth-topology.png')
    .showAtmosphere(true).atmosphereColor('#6fb1ff').atmosphereAltitude(0.2);
  groesse();
  window.addEventListener('resize', groesse);
  var c = g.controls();
  c.enableZoom = false; c.enablePan = false; c.autoRotate = !ruhig; c.autoRotateSpeed = 0.55;
  g.pointOfView({ lat: 30, lng: 60, altitude: 2.25 }, 0);

  Promise.all([json('data/reiche.json'), json('data/handel.json')]).then(function (x) {
    var D = x[0], H = x[1], J = 117;
    var flaechen = D.regionen.filter(function (f) {
      var p = f.properties; return (p.reich === 'rom' || p.reich === 'han') && p.von <= J && J < p.bis;
    });
    g.polygonsData(flaechen)
      .polygonGeoJsonGeometry(function (f) { return f.geometry; })
      .polygonCapColor(function (f) { return f.properties.reich === 'rom' ? 'rgba(196,52,44,0.62)' : 'rgba(224,158,12,0.62)'; })
      .polygonSideColor(function () { return 'rgba(0,0,0,0.12)'; })
      .polygonStrokeColor(function () { return 'rgba(30,10,5,0.4)'; })
      .polygonAltitude(0.006).polygonsTransitionDuration(1800);
    var wege = [];
    H.verbindungen.forEach(function (v) {
      var farbe = v.art === 'see' ? '#5fd8ff' : '#ffcf6b';
      wege.push({ pts: v.pfad, c: farbe, w: 2.4, dash: [1, 0], t: 0 });
      wege.push({ pts: v.pfad, c: 'rgba(255,255,255,0.95)', w: 1.4, dash: [0.02, 0.07], t: v.art === 'see' ? 9000 : 7000 });
    });
    g.pathsData(wege).pathPoints('pts').pathPointLat(function (p) { return p[1]; }).pathPointLng(function (p) { return p[0]; })
      .pathPointAlt(0.008).pathColor('c').pathStroke('w')
      .pathDashLength(function (d) { return d.dash[0]; }).pathDashGap(function (d) { return d.dash[1]; })
      .pathDashAnimateTime(function (d) { return ruhig ? 0 : d.t; }).pathTransitionDuration(0);
    var orte = [{ n: 'Rom', lat: 41.9, lng: 12.5 }, { n: 'Chang’an', lat: 34.27, lng: 108.9 }, { n: 'Ktesiphon', lat: 33.09, lng: 44.58 },
      { n: 'Alexandria', lat: 31.2, lng: 29.9 }, { n: 'Samarkand', lat: 39.65, lng: 66.96 }];
    g.ringsData(ruhig ? [] : orte).ringLat('lat').ringLng('lng').ringColor(function () { return function (t) { return 'rgba(255,220,140,' + (1 - t) + ')'; }; })
      .ringMaxRadius(3.2).ringPropagationSpeed(1.6).ringRepeatPeriod(1600);
    g.labelsData(orte).labelLat('lat').labelLng('lng').labelText('n').labelSize(1.1).labelDotRadius(0.45)
      .labelColor(function () { return 'rgba(255,240,210,0.95)'; }).labelResolution(2).labelAltitude(0.01);
  }).catch(function (e) { console.warn(e); });
  setTimeout(function () { box.classList.add('da'); }, 150);
})();
