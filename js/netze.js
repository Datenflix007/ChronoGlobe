/* Handels- und Verkehrsnetze aus Forschungsdaten (data/netze/*.json, Format: docs/HANDELSNETZE.md).
   Reine Rechenfunktionen ohne Globus: im Browser als window.Netze, in Node als Modul (für Tests).

   Zeitfilter je Datierungsart (netz.datierung.typ):
     jahrgenau   Strecke/Ort sichtbar, wenn von ≤ Jahr ≤ bis (eigene Jahre je Eintrag aus dem Datensatz)
     zeitraum    wie jahrgenau; die Jahre gelten für den ganzen Datensatz bzw. eine Periode. Hat der Datensatz
                 Perioden (datierung.perioden), gilt [von, bis) – das Grenzjahr gehört zur jüngeren Periode,
                 damit nicht zwei Fassungen derselben Straße übereinanderliegen. Die letzte Periode schließt bis ein.
     reisedatum  Reisen (netz.reisen): sichtbar von Reisebeginn bis Reiseende; gezeigt werden die Etappen, die schon
                 begonnen haben. Danach bleibt die Reise NACHLEUCHTEN Jahre blass sichtbar (Darstellungsregel).
   Jahre sind historische Jahre (−300 = 300 v. Chr.). */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.Netze = factory();
})(this, function () {
  'use strict';

  var NACHLEUCHTEN = 3;
  var GRUPPEN = ['land', 'wasser', 'reise'];
  var ARTEN = ['handelsweg', 'verkehrsnetz', 'reiseroute'];
  var TYPEN = ['jahrgenau', 'zeitraum', 'reisedatum'];
  var MONAT = ['Jan.', 'Feb.', 'März', 'Apr.', 'Mai', 'Juni', 'Juli', 'Aug.', 'Sept.', 'Okt.', 'Nov.', 'Dez.'];

  function zahl(x) { return typeof x === 'number' && isFinite(x); }
  function punktOk(p) { return Array.isArray(p) && zahl(p[0]) && zahl(p[1]) && p[0] >= -180 && p[0] <= 180 && p[1] >= -90 && p[1] <= 90; }

  /* Prüft eine Netzdatei gegen das Datenmodell. Ergebnis: Liste von Fehlertexten (leer = in Ordnung). */
  function pruefen(n) {
    var f = [];
    if (!n || typeof n !== 'object') return ['keine Netzdatei'];
    if (!n.id) f.push('id fehlt');
    if (GRUPPEN.indexOf(n.gruppe) < 0) f.push('gruppe ungültig: ' + n.gruppe);
    if (ARTEN.indexOf(n.art) < 0) f.push('art ungültig: ' + n.art);
    var d = n.datierung || {};
    if (TYPEN.indexOf(d.typ) < 0) f.push('datierung.typ ungültig: ' + d.typ);
    if (!zahl(d.von) || !zahl(d.bis) || d.von > d.bis) f.push('datierung von/bis ungültig');
    if (!d.text) f.push('datierung.text fehlt');
    var q = n.quelle || {};
    if (!q.zitat) f.push('quelle.zitat fehlt');
    if (!q.lizenz) f.push('quelle.lizenz fehlt');
    if (n.art === 'reiseroute' && n.gruppe !== 'reise') f.push('Reiserouten gehören in die Gruppe „reise“');
    var ids = {}, reisen = {};
    (n.reisen || []).forEach(function (r) { reisen[r.id] = r; });
    if (d.typ === 'reisedatum' && !(n.reisen || []).length) f.push('reisedatum ohne reisen');
    (n.linien || []).forEach(function (l, i) {
      var w = 'linien[' + i + '] ' + (l.id || '');
      if (!l.id) f.push(w + ': id fehlt'); else if (ids[l.id]) f.push(w + ': id doppelt'); else ids[l.id] = 1;
      if (!zahl(l.von) || !zahl(l.bis) || l.von > l.bis) f.push(w + ': von/bis ungültig');
      else if (l.von < d.von || l.bis > d.bis) f.push(w + ': Jahre außerhalb der Datierung des Datensatzes');
      if (!Array.isArray(l.teile) || !l.teile.length) f.push(w + ': keine Geometrie');
      else l.teile.forEach(function (t) { if (!Array.isArray(t) || t.length < 2 || !t.every(punktOk)) f.push(w + ': ungültige Koordinaten'); });
      if (d.typ === 'reisedatum' && !reisen[l.reise]) f.push(w + ': unbekannte Reise ' + l.reise);
    });
    (n.orte || []).forEach(function (o, i) {
      var w = 'orte[' + i + '] ' + (o.id || '');
      if (!o.id) f.push(w + ': id fehlt'); else if (ids[o.id]) f.push(w + ': id doppelt'); else ids[o.id] = 1;
      if (!punktOk([o.lng, o.lat])) f.push(w + ': ungültige Lage');
      if (!zahl(o.von) || !zahl(o.bis) || o.von > o.bis) f.push(w + ': von/bis ungültig');
    });
    return f;
  }

  /* Bereitet eine geladene Netzdatei vor (Verweise auf Reisen, Periodengrenzen). Gibt das Netz zurück. */
  function vorbereiten(n) {
    var R = {};
    (n.reisen || []).forEach(function (r) { R[r.id] = r; });
    var per = (n.datierung && n.datierung.perioden) || null, letzte = per ? Math.max.apply(null, per.map(function (p) { return p.bis; })) : null;
    (n.linien || []).concat(n.orte || []).forEach(function (x) {
      if (x.reise) x.__reise = R[x.reise] || null;
      x.__offen = !!per && x.bis !== letzte;   // halb offenes Intervall [von, bis)
    });
    n.__R = R;
    return n;
  }
  function imZeitraum(x, y) { return y >= x.von && (x.__offen ? y < x.bis : y <= x.bis); }

  /* Sichtbare Linien im Jahr y: Liste von { linie, stil } mit stil 'aktiv' | 'gereist' | 'blass' */
  function linienImJahr(n, y) {
    var out = [];
    if (!n || !n.linien) return out;
    if (n.datierung.typ === 'reisedatum') {
      n.linien.forEach(function (l) {
        var r = l.__reise; if (!r || y < r.von || y > r.bis + NACHLEUCHTEN || l.von > y) return;
        out.push({ linie: l, stil: y > r.bis ? 'blass' : l.bis >= y ? 'aktiv' : 'gereist' });
      });
      return out;
    }
    n.linien.forEach(function (l) { if (imZeitraum(l, y)) out.push({ linie: l, stil: 'aktiv' }); });
    return out;
  }
  /* Sichtbare Orte im Jahr y. Reisen: Stationen nur, solange die Reise läuft und die Station erreicht ist. */
  function orteImJahr(n, y) {
    if (!n || !n.orte) return [];
    if (n.datierung.typ === 'reisedatum') return n.orte.filter(function (o) { var r = o.__reise; return r && y >= r.von && y <= r.bis && (o.jahr == null || o.jahr <= y); });
    return n.orte.filter(function (o) { return imZeitraum(o, y); });
  }
  /* Periode eines Datensatzes im Jahr y (oder null) */
  function periode(n, y) {
    var per = n && n.datierung && n.datierung.perioden; if (!per) return null;
    var letzte = per[per.length - 1];
    return per.filter(function (p) { return y >= p.von && (p === letzte ? y <= p.bis : y < p.bis); })[0] || null;
  }
  /* Kurzer Schlüssel des sichtbaren Zustands (ändert sich nur, wenn sich Linien, Stile oder Orte ändern) */
  function schluessel(n, y) {
    var L = linienImJahr(n, y), h = 0;
    L.forEach(function (x, i) { var s = x.linie.id + x.stil; for (var k = 0; k < s.length; k++) h = (h * 31 + s.charCodeAt(k) + i) | 0; });
    return L.length + ':' + h + ':' + orteImJahr(n, y).length;
  }

  function jahrText(j) { return j < 0 ? (-j) + ' v. Chr.' : j + ' n. Chr.'; }
  function spanne(a, b) { return a === b ? jahrText(a) : (a < 0 && b > 0) ? jahrText(a) + ' bis ' + jahrText(b) : (a < 0 ? (-a) + ' bis ' + (-b) + ' v. Chr.' : a + ' bis ' + b + ' n. Chr.'); }
  /* Zeitangabe einer Linie in Worten (mit Monaten bei Reisedaten) */
  function zeitText(l) {
    if (l.vonMonat) {
      var a = MONAT[l.vonMonat - 1] + ' ' + l.von, b = MONAT[l.bisMonat - 1] + ' ' + l.bis;
      return a === b ? a : a + ' bis ' + b;
    }
    return spanne(l.von, l.bis);
  }

  return { pruefen: pruefen, vorbereiten: vorbereiten, linienImJahr: linienImJahr, orteImJahr: orteImJahr, periode: periode,
           schluessel: schluessel, zeitText: zeitText, spanne: spanne, jahrText: jahrText, NACHLEUCHTEN: NACHLEUCHTEN };
});
