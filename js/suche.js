/* ChronoGlobe · Suche (Reiche, Orte, Ereignisse, Schlachten, Geographie). Reine Rechenfunktionen ohne DOM:
   im Browser als window.Suche, in Node als Modul (tests/suche.test.js). Die Bedienung steht in js/app.js
   (sucheEinrichten); ein Treffer wirkt nur über setState, in Live-Sessions also wie jede andere Bedienung der Lehrkraft.

   Tolerant gegenüber Akzenten, Apostrophen und Schreibvarianten: Beide Seiten werden „gefaltet“
   (Chang'an = Changan, Ktesiphon = Ctesiphon, Kuschan = Kushan, Seleukeia = Seleucia). */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.Suche = factory();
})(this, function () {
  'use strict';

  var ARTEN = {   // Reihenfolge bei gleicher Güte
    reich: { rang: 0, name: 'Reich' }, ort: { rang: 1, name: 'Ort' }, geo: { rang: 2, name: 'Geographie' },
    schlacht: { rang: 3, name: 'Schlacht' }, ereignis: { rang: 4, name: 'Ereignis' }
  };

  /* Text → Suchschlüssel: Kleinbuchstaben, ohne Akzente und Satzzeichen, Schreibvarianten vereinheitlicht */
  function falten(s) {
    s = String(s == null ? '' : s).toLowerCase();
    if (s.normalize) s = s.normalize('NFD').replace(/[̀-ͯ]/g, '');
    s = s.replace(/ß/g, 'ss').replace(/[ʼ’‘`´'"„“”«»]/g, '')
      .replace(/[^a-z0-9]+/g, ' ').trim();
    return s
      .replace(/ae/g, 'a').replace(/oe/g, 'o').replace(/ue/g, 'u')   // Caesar/Cäsar, Böhmen/Boehmen
      .replace(/sch/g, 'sh')                                          // Kuschan/Kushan
      .replace(/ph/g, 'f').replace(/th/g, 't').replace(/rh/g, 'r')
      .replace(/c(?!h)/g, 'k').replace(/q/g, 'k')                    // Ctesiphon/Ktesiphon
      .replace(/y/g, 'i').replace(/ei/g, 'i').replace(/z/g, 's')      // Seleukeia/Seleucia/Seleukia
      .replace(/(.)\1+/g, '$1');                                      // Doppelbuchstaben
  }

  /* Levenshtein-Abstand, abgebrochen ab max+1 (für Tippfehler bei längeren Suchwörtern) */
  function abstand(a, b, max) {
    if (Math.abs(a.length - b.length) > max) return max + 1;
    var v = []; for (var j = 0; j <= b.length; j++) v[j] = j;
    for (var i = 1; i <= a.length; i++) {
      var prev = v[0], min = v[0] = i;
      for (j = 1; j <= b.length; j++) {
        var t = v[j]; v[j] = Math.min(v[j] + 1, v[j - 1] + 1, prev + (a[i - 1] === b[j - 1] ? 0 : 1)); prev = t;
        if (v[j] < min) min = v[j];
      }
      if (min > max) return max + 1;
    }
    return v[b.length];
  }

  function mitte(pfade) {   // Punkt in der Mitte des längsten Teilstücks (Flüsse, Gebirge)
    var best = null; (pfade || []).forEach(function (p) { if (p && (!best || p.length > best.length)) best = p; });
    if (!best || !best.length) return null;
    var q = best[Math.floor(best.length / 2)]; return { lng: q[0], lat: q[1] };
  }

  /* Index aus den Daten bauen.
     d = { meta: {id: {name, von, bis, zentrum}}, ereignisse, schlachten, orte, handelOrte, geo,
           aussen: { meta, ereignisse, schlachten, orte } (Daten außerhalb des Tafelbild-Zeitraums) } */
  function bauen(d) {
    var L = [];
    function rein(e) { e.schluessel = [e.name].concat(e.varianten || []).map(falten).filter(Boolean); L.push(e); }
    function reiche(meta, aussen) {
      Object.keys(meta || {}).forEach(function (id) {
        var m = meta[id]; if (!m || !m.name) return;
        rein({ art: 'reich', id: id, name: m.name, varianten: m.varianten || [], reich: id, von: m.von, bis: m.bis,
               lng: m.zentrum ? m.zentrum[0] : null, lat: m.zentrum ? m.zentrum[1] : null, aussen: !!aussen });
      });
    }
    function ereignisse(l, aussen, meta) {
      (l || []).forEach(function (e, i) {
        var m = meta && meta[e.reich];
        rein({ art: 'ereignis', id: e.reich + ':' + e.jahr + ':' + i, name: e.titel, reich: e.reich, jahr: e.jahr, label: e.label,
               lng: m && m.zentrum ? m.zentrum[0] : null, lat: m && m.zentrum ? m.zentrum[1] : null, aussen: !!aussen });
      });
    }
    function schlachten(l, aussen) {
      (l || []).forEach(function (s) {
        rein({ art: 'schlacht', id: s.name + ':' + s.jahr, name: s.name, varianten: ['Schlacht bei ' + s.name, 'Schlacht von ' + s.name],
               reiche: s.reiche, reich: (s.reiche || [])[0], jahr: s.jahr, lng: s.lng, lat: s.lat, note: s.note, aussen: !!aussen });
      });
    }
    var orte = {};
    function ortRein(o, aussen, handel) {
      var k = falten(o.name) + '@' + Math.round(o.lng * 2) + ',' + Math.round(o.lat * 2);   // gleicher Ort in mehreren Reichen
      var z = o.zeiten || (o.von != null ? [[o.von, o.bis]] : null);
      if (orte[k]) {
        var x = orte[k];
        if (o.reich && x.reiche.indexOf(o.reich) < 0) x.reiche.push(o.reich);
        if (z) x.zeiten = (x.zeiten || []).concat(z);
        if (handel) x.handel = o.id;
        if (!aussen) x.aussen = false;
        return;
      }
      orte[k] = { art: 'ort', id: k, name: o.name, reich: o.reich || null, reiche: o.reich ? [o.reich] : [], zeiten: z,
                  lng: o.lng, lat: o.lat, handel: handel ? o.id : null, aussen: !!aussen };
    }
    reiche(d.meta, false); if (d.aussen) reiche(d.aussen.meta, true);
    (d.orte || []).forEach(function (o) { ortRein(o, false, false); });
    if (d.aussen) (d.aussen.orte || []).forEach(function (o) { ortRein(o, true, false); });
    (d.handelOrte || []).forEach(function (o) { ortRein(o, false, true); });
    Object.keys(orte).forEach(function (k) { rein(orte[k]); });
    schlachten(d.schlachten, false); if (d.aussen) schlachten(d.aussen.schlachten, true);
    ereignisse(d.ereignisse, false, d.meta); if (d.aussen) ereignisse(d.aussen.ereignisse, true, d.aussen.meta);
    var g = d.geo;
    if (g) {
      var geo = function (x, artGeo, p) {
        if (!x || !p) return;
        rein({ art: 'geo', id: artGeo + ':' + (x.id || x.name), name: x.name, varianten: x.heute ? [x.heute] : [], heute: x.heute || null,
               geoArt: artGeo, lng: p.lng, lat: p.lat, hinweis: x.hinweis || null, aussen: false });
      };
      (g.fluesse || []).forEach(function (x) { geo(x, 'fluss', mitte(x.pfade)); });
      (g.gebirge || []).forEach(function (x) { geo(x, 'gebirge', mitte(x.kaemme)); });
      (g.gipfel || []).forEach(function (x) { geo(x, 'gipfel', x); });
      (g.meere || []).forEach(function (x) { geo(x, 'meer', x); });
      (g.landschaften || []).forEach(function (x) { geo(x, 'landschaft', x); });
    }
    return L;
  }

  /* Liegt ein Eintrag im Zeitraum [von, bis]? (Tafelbild; ohne Zeitraum immer ja) */
  function imZeitraum(e, von, bis) {
    if (e.aussen) return false;
    if (von == null || bis == null) return true;
    if (e.jahr != null) return e.jahr >= von && e.jahr <= bis;
    if (e.zeiten && e.zeiten.length) return e.zeiten.some(function (z) { return z[1] >= von && z[0] <= bis; });
    if (e.von != null && e.bis != null) return e.bis >= von && e.von <= bis;
    return true;
  }

  /* Güte eines Schlüssels für die Anfrage q (beide gefaltet); 0 = kein Treffer */
  function guete(k, q) {
    if (k === q) return 100;
    if (k.indexOf(q) === 0) return 80;
    if ((' ' + k).indexOf(' ' + q) >= 0) return 65;
    if (q.length >= 5 && k.indexOf(q) >= 0) return 45;   // mitten im Wort erst ab fünf Zeichen (sonst „Parth“ → „Sparta“)
    var qw = q.split(' ');
    if (qw.length > 1 && qw.every(function (w) { return (' ' + k).indexOf(' ' + w) >= 0; })) return 55;   // „gelbe turbane“ → „… gelben turbane“
    if (q.length >= 5) {   // Tippfehler: ein Zeichen Abstand zum Wortanfang gleicher Länge
      var w = k.split(' ');
      for (var i = 0; i < w.length; i++) if (abstand(w[i].slice(0, q.length), q, 1) <= 1) return 25;
    }
    return 0;
  }

  /* Suchen. opt: { von, bis (Zeitraum des Tafelbilds), max (Standard 12) } → [{ e, guete, aussen }] */
  function suchen(index, anfrage, opt) {
    opt = opt || {};
    var q = falten(anfrage); if (!q) return [];
    var out = [];
    index.forEach(function (e) {
      var g = 0; e.schluessel.forEach(function (k) { g = Math.max(g, guete(k, q)); });
      if (!g) return;
      out.push({ e: e, guete: g, aussen: !imZeitraum(e, opt.von, opt.bis) });
    });
    out.sort(function (a, b) {
      return (a.aussen - b.aussen) || (b.guete - a.guete) || (ARTEN[a.e.art].rang - ARTEN[b.e.art].rang) ||
        (a.e.name.length - b.e.name.length) || (a.e.name < b.e.name ? -1 : 1);
    });
    return out.slice(0, opt.max || 12);
  }

  /* Jahr, auf das ein Treffer die Zeitleiste stellt (null = Jahr bleibt). jetzt = aktuelles Jahr. */
  function zieljahr(e, jetzt, von, bis) {
    var lo = von == null ? -Infinity : von, hi = bis == null ? Infinity : bis;
    function klemm(y) { return Math.max(lo, Math.min(hi, y)); }
    if (e.jahr != null) return e.jahr;
    var z = e.zeiten && e.zeiten.length ? e.zeiten : (e.von != null ? [[e.von, e.bis]] : null);
    if (!z) return null;
    if (z.some(function (t) { return jetzt >= t[0] && jetzt <= t[1]; })) return null;   // passt schon
    var t = z.filter(function (t) { return t[1] >= lo && t[0] <= hi; })[0] || z[0];
    var y = klemm(t[0]); return y === 0 ? 1 : y;
  }

  return { ARTEN: ARTEN, falten: falten, abstand: abstand, bauen: bauen, suchen: suchen, imZeitraum: imZeitraum, zieljahr: zieljahr };
});
