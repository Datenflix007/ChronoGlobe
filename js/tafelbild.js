/* ChronoGlobe: Modus und Tafelbild für app.html bestimmen, Tafelbild-Daten mit den Kerndaten zusammenführen.

   app.html?modus=frei                      Freies Nutzen („Menschheitsgeschichte“): Kern ohne Tafelbild-Extras
   app.html?tafelbild=<id>                  Tafelbild aus tafelbilder/<id>/tafelbild.json
   app.html?session=<CODE>&rolle=lehrer|schueler   Live-Session (js/session.js); das Tafelbild kommt aus der Session

   Stellt window.CG bereit:
     CG.modus, CG.rolle, CG.code       aus der Adresse
     CG.bereit                         Promise → Tafelbild-Konfiguration (Freimodus: CG_FREI)
     CG.daten(schluessel, kernUrl)     Kerndatei laden und ggf. mit der Tafelbild-Datei ersetzen/ergänzen
   Format von tafelbild.json: docs/TAFELBILD_ERSTELLEN.md */
(function () {
  'use strict';
  var q = new URLSearchParams(location.search);
  var code = (q.get('session') || '').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 12);
  var CG = window.CG = {
    modus: code ? 'session' : q.get('tafelbild') ? 'tafelbild' : 'frei',
    rolle: q.get('rolle') === 'lehrer' ? 'lehrer' : 'schueler',
    code: code || null,
    tafelbild: null
  };

  /* Freies Nutzen: alle Kerndaten, volles Menü, keine Lehrerhinweise und keine Tafelbild-Vignetten */
  var FREI = {
    id: null, titel: 'Menschheitsgeschichte', kopf: 'ChronoGlobe', untertitel: 'Menschheitsgeschichte',
    beschreibung: 'Der ganze Globus mit allen Daten, frei durchklickbar.', ordner: '',
    start: { jahr: 117, ansicht: 'sat', kamera: 'eurasien', drehen: true },
    reiche: { verfuegbar: 'alle', aktiv: ['rom', 'han', 'mesopotamien', 'aegypten', 'nubien', 'indus', 'minoer', 'mykener', 'hethiter', 'athen', 'sparta', 'makedonien', 'shang', 'perser',
      // Mittelalter (data/mittelalter_reiche.json) und Reiche, die nach 480 weiterbestehen: keine leere Zeit nach Westrom
      'sasan', 'franken', 'westgot', 'ostgot', 'angels', 'osman', 'langob', 'kalifat', 'andalus', 'iberien', 'china_ma', 'steppen', 'mongolen',
      'seldsch', 'aeg_ma', 'hrr', 'frankreich', 'england', 'rus', 'bulgarien', 'ungarn', 'polen', 'indien_ma'] },
    ebenen: { verfuegbar: 'alle' },
    fokuspunkte: [
      { id: 'rom', name: 'Rom', knopf: '→ Rom', lat: 41.5, lng: 14, alt: 1.0 },
      { id: 'china', name: 'China/Han', knopf: '→ China', lat: 34, lng: 108, alt: 1.1 },
      { id: 'eurasien', name: 'Eurasien', knopf: 'Eurasien', lat: 36, lng: 62, alt: 'standard' }
    ],
    lehrerhinweise: null, daten: {}
  };

  function json(url) {
    var v = window.cgUrl ? cgUrl(url) : url;   // mit Versionsangabe (js/version.js) darf der Cache greifen
    return fetch(v, v === url ? { cache: 'no-cache' } : {}).then(function (r) { if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); });
  }
  function istObj(o) { return o && typeof o === 'object' && !Array.isArray(o); }
  /* Ergänzen: Objekte rekursiv, Listen werden angehängt (Einträge mit gleicher id ersetzen den Kerneintrag) */
  function mischen(a, b) {
    if (Array.isArray(a) && Array.isArray(b)) {
      var out = a.slice();
      b.forEach(function (x) {
        var i = x && x.id != null ? out.findIndex(function (y) { return y && y.id === x.id; }) : -1;
        if (i >= 0) out[i] = mischen(out[i], x); else out.push(x);
      });
      return out;
    }
    if (istObj(a) && istObj(b)) {
      var o = Object.assign({}, a);
      Object.keys(b).forEach(function (k) { o[k] = k in a ? mischen(a[k], b[k]) : b[k]; });
      return o;
    }
    return b;
  }
  CG.mischen = mischen;

  CG.daten = function (schluessel, kernUrl) {
    var tb = CG.tafelbild, d = tb && tb.daten && tb.daten[schluessel];
    if (schluessel === 'vignetten' && /[?&]vignetten=demo\b/.test(location.search)) d = null;   // Bausteinvorschau
    if (!d) return json(kernUrl);
    var eigen = json(tb.ordner + d.datei);
    if (d.art === 'ersetzen') return eigen;
    return Promise.all([json(kernUrl), eigen]).then(function (x) { return mischen(x[0], x[1]); });
  };

  function tafelbildLaden(id) {
    if (!/^[a-z0-9][a-z0-9-]{0,59}$/.test(id || '')) return Promise.reject(new Error('Ungültige Tafelbild-ID: ' + id));
    return json('tafelbilder/' + id + '/tafelbild.json').then(function (tb) {
      if (tb.id !== id) throw new Error('tafelbild.json: id „' + tb.id + '“ passt nicht zum Ordner „' + id + '“');
      tb.ordner = 'tafelbilder/' + id + '/';
      return tb;
    });
  }

  var weg;
  if (CG.modus === 'tafelbild') weg = tafelbildLaden(q.get('tafelbild'));
  else if (CG.modus === 'session') {
    weg = (window.CGSession ? window.CGSession.vorbereiten(CG.code, CG.rolle) : Promise.reject(new Error('js/session.js fehlt')))
      .then(function (s) { return s && s.tafelbild_id ? tafelbildLaden(s.tafelbild_id) : FREI; });
  } else weg = Promise.resolve(FREI);

  CG.bereit = weg.then(function (tb) { CG.tafelbild = tb; return tb; }, function (err) {
    console.error(err);
    CG.fehler = err;
    CG.tafelbild = FREI;
    return FREI;
  });
})();
