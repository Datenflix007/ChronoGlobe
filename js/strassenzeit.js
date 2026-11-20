/* Zeitmodell der Römerstraßen (data/roemerstrassen.json, Format: docs/STRASSEN_ZEITMODELL.md).
   Reine Rechenfunktionen ohne Globus: im Browser als window.StrassenZeit, in Node als Modul (für Tests).

   Jahreszählung: Die App und die Daten verwenden historische Jahre (−44 = 44 v. Chr.). Ein Jahr 0 gibt es nicht.
   Für Dauern und Interpolation wird in astronomische Jahre umgerechnet (1 v. Chr. = 0, 2 v. Chr. = −1 …).

   Phasen einer Linie im Jahr j:
     A „vor“         j < beginn_min                       → nicht sichtbar
     B „ausbau“      beginn_min ≤ j < beginn_max          → schrittweise gezeichnet (didaktische Interpolation); mit
                                                            zeit.netz erst ab netz.von, vom Anschlusspunkt aus wachsend
     C „roemisch“    beginn_max ≤ j ≤ roemische_nutzung_bis_modell → voll sichtbar
     D „nachroemisch“ danach                              → Hauptmodus unsichtbar; Referenzmodus blass gestrichelt
   Ohne gültigen Ausbauzeitraum: „undatiert“ (nur mit Option „Unsicherheit“ sichtbar).
   Ohne gültiges Nutzungsende: römisch höchstens bis ENDE_UNBEKANNT (476, Ende Westroms), danach wie D. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.StrassenZeit = factory();
})(this, function () {
  'use strict';

  var ENDE_UNBEKANNT = 476;
  var STUFEN = 4;   // Einblendung in Viertelschritten: weniger Neuzeichnen beim Abspielen

  function astro(j) { return j < 0 ? j + 1 : j; }
  function historisch(a) { return a <= 0 ? a - 1 : a; }
  function zahl(v) { return typeof v === 'number' && isFinite(v) ? v : null; }
  function jahrOk(v) { v = zahl(v); return v !== null && v !== 0 && Math.abs(v) < 5000 ? Math.round(v) : null; }   // 0 gibt es nicht

  function gradLaenge(p) {
    var s = 0;
    for (var i = 1; i < p.length; i++) {
      var dx = (p[i][0] - p[i - 1][0]) * Math.cos((p[i][1] + p[i - 1][1]) / 2 * Math.PI / 180), dy = p[i][1] - p[i - 1][1];
      s += Math.sqrt(dx * dx + dy * dy);
    }
    return s;
  }

  /* Einmal beim Laden: prüfen, vereinheitlichen, Fehler sammeln. Ungültige Geometrie wird verworfen,
     ungültige Zeitangaben machen eine Linie „undatiert“ bzw. „Ende unbekannt“. */
  function vorbereiten(daten) {
    var fehler = [], linien = [];
    var roh = daten && Array.isArray(daten.linien) ? daten.linien : [];
    if (!roh.length) fehler.push('keine Linien gefunden');
    roh.forEach(function (l, i) {
      var id = l && l.id ? String(l.id) : 'linie-' + (i + 1);
      var p = l && Array.isArray(l.p) ? l.p.filter(function (c) { return Array.isArray(c) && zahl(c[0]) !== null && zahl(c[1]) !== null && Math.abs(c[0]) <= 180 && Math.abs(c[1]) <= 90; }) : [];
      if (p.length < 2) { fehler.push(id + ': Geometrie ungültig, Linie ausgelassen'); return; }
      var s = l.s === 'S' || l.s === 'H' ? l.s : 'H';
      if (s !== l.s) fehler.push(id + ': räumliche Sicherheit unbekannt, als „vermutet“ behandelt');
      var z = l.zeit && typeof l.zeit === 'object' ? l.zeit : {};
      var bmin = jahrOk(z.beginn_min), bmax = jahrOk(z.beginn_max), ende = jahrOk(z.roemische_nutzung_bis_modell), mod = jahrOk(z.beginn_modell);
      var datierbar = bmin !== null && bmax !== null;
      if (!l.zeit) fehler.push(id + ': keine Zeitangaben');
      else if (!datierbar) fehler.push(id + ': Ausbauzeitraum fehlt oder ungültig');
      if (datierbar && astro(bmin) > astro(bmax)) { fehler.push(id + ': beginn_min > beginn_max, vertauscht'); var t = bmin; bmin = bmax; bmax = t; }
      if (datierbar && (mod === null || astro(mod) < astro(bmin) || astro(mod) > astro(bmax))) mod = historisch(Math.round((astro(bmin) + astro(bmax)) / 2));
      if (l.zeit && ende === null) fehler.push(id + ': Ende der römischen Nutzung unbekannt');
      // Wachstumsnetz (build_strassen_zeit.py → zeit.netz): Anschlusspunkt u und Zeichenfenster von … bis
      var n = z.netz && typeof z.netz === 'object' ? z.netz : null, netz = null;
      if (datierbar && n && zahl(n.u) !== null && jahrOk(n.von) !== null && jahrOk(n.bis) !== null) {
        var nv = Math.max(astro(bmin), astro(jahrOk(n.von))), nb = Math.min(astro(bmax), astro(jahrOk(n.bis)));
        if (nb > nv) netz = { u: Math.max(0, Math.min(1, n.u)), von: nv, bis: nb, anschluss: n.anschluss || null };
      }
      linien.push({
        id: id, s: s, p: p, laenge: gradLaenge(p), datierbar: datierbar,
        bmin: bmin, bmax: bmax, modell: mod, ende: ende, endeUnbekannt: ende === null, netz: netz,
        datierung: z.datierung || 'unbekannt', region: z.region || null, zeit: z
      });
    });
    return { linien: linien, fehler: fehler, meta: daten || {} };
  }

  /* Zustand einer Linie im Jahr j. opt: { ehemals, animieren, unsicherheit } */
  function zustand(L, j, opt) {
    opt = opt || {};
    if (!L.datierbar) return { phase: 'undatiert', stil: opt.unsicherheit ? 'undatiert' : null, anteil: opt.unsicherheit ? 1 : 0 };
    var a = astro(j), amin = astro(L.bmin), amax = astro(L.bmax);
    var ende = L.endeUnbekannt ? ENDE_UNBEKANNT : L.ende;
    if (a < amin) return { phase: 'vor', stil: null, anteil: 0 };
    if (a < amax) {
      if (opt.animieren === false) {
        var da = a >= astro(L.modell);
        return { phase: 'ausbau', stil: da ? 'aktiv' : null, anteil: da ? 1 : 0 };
      }
      if (L.netz) {   // Netz wächst: erst wenn der Anschlusspunkt gezeichnet ist, dann gleichmäßig bis netz.bis
        if (a < L.netz.von) return { phase: 'ausbau', stil: null, anteil: 0 };
        return { phase: 'ausbau', stil: 'ausbau', anteil: Math.min(1, (a - L.netz.von + 1) / (L.netz.bis - L.netz.von + 1)) };
      }
      var f = (a - amin + 1) / (amax - amin + 1);
      var q = Math.max(1, Math.ceil(f * STUFEN)) / STUFEN;
      return { phase: 'ausbau', stil: 'ausbau', anteil: q };
    }
    if (a <= astro(ende)) return { phase: 'roemisch', stil: 'aktiv', anteil: 1 };
    return { phase: 'nachroemisch', stil: opt.ehemals ? 'ehemals' : null, anteil: opt.ehemals ? 1 : 0 };
  }

  /* Kurzschlüssel aller sichtbaren Zustände: ändert sich nur, wenn neu gezeichnet werden muss */
  function schluessel(linien, j, opt, nurStil) {
    var out = '';
    for (var i = 0; i < linien.length; i++) {
      var z = zustand(linien[i], j, opt);
      out += z.stil ? z.stil.charAt(0) + (nurStil ? '' : Math.round(z.anteil * STUFEN)) : '-';
    }
    return out;
  }

  function zaehlen(linien, j, opt) {
    var c = { vor: 0, ausbau: 0, roemisch: 0, nachroemisch: 0, undatiert: 0, sichtbar: 0 };
    linien.forEach(function (L) { var z = zustand(L, j, opt); c[z.phase]++; if (z.stil) c.sichtbar++; });
    return c;
  }

  /* Anzeige eines historischen Jahres (ohne Jahr 0) */
  function jahrText(j) { return j < 0 ? (-j) + ' v. Chr.' : j + ' n. Chr.'; }

  return { vorbereiten: vorbereiten, zustand: zustand, schluessel: schluessel, zaehlen: zaehlen,
           astro: astro, historisch: historisch, jahrText: jahrText, ENDE_UNBEKANNT: ENDE_UNBEKANNT, STUFEN: STUFEN };
});
