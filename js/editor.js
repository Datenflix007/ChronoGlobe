/* ChronoGlobe-Editor (editor.html): Änderungen und neue Themenebenen vorschlagen.
   Ergebnis ist ein Beitrag im Format von js/themen.js (docs/EDITOR.md). Er wird
     – im Browser als Entwurf gemerkt (localStorage 'cg.editor.entwurf'; nur dieses Gerät),
     – als Vorschau auf dem Globus gezeigt (app.html?vorschau=editor liest localStorage 'cg.editor.vorschau'),
     – als Pull Request vorgeschlagen: Link auf GitHubs „Neue Datei“-Seite mit fertigem Inhalt (kein Server, kein Token).
   KI-Assistent (js/ki.js): erzeugt einen Prompt für eine KI der Wahl und liest deren Antwort ein. Der Editor sendet
   nichts an eine KI und lädt nur Dateien dieses Projekts. */
(function () {
  'use strict';
  var REPO = 'Datenflix007/ChronoGlobe', ZWEIG = 'main';   // Ziel der Pull Requests
  var SPEICHER = 'cg.editor.entwurf', W = 960, H = 480;
  var DATEI = {
    'reich-gebiet': 'data/reiche.json', 'reich-ort': 'data/reiche.json', 'reich-ereignis': 'data/reiche.json',
    'handelsroute': 'data/handel.json', 'handelsort': 'data/handel.json', 'kontakt': 'data/handel.json',
    'text': 'data/texte.json', 'vignette': 'data/vignetten.json', 'ebene': 'data/ebenen/', 'sonstiges': ''
  };
  var SYMBOL = { punkt: '●', linie: '╱', flaeche: '▰' };
  var D = {}, E = null, AKT = -1, REF = null;
  var UI = { zeichnen: true, jahr: null, suche: '', sort: 'liste', zSuche: '', dateiZweck: null, kiErgebnis: null };
  var HIST = { stapel: [], pos: -1, timer: null, still: false };

  function $(s) { return document.querySelector(s); }
  function $$(s) { return Array.prototype.slice.call(document.querySelectorAll(s)); }
  function el(t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
  function json(u) { return fetch(window.cgUrl ? cgUrl(u) : u).then(function (r) { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); }); }
  function jahr(y) { return y == null ? '…' : Themen.jahrText(y); }
  function zahlOderNull(v) { if (v === '' || v == null) return null; var n = Number(v); return isFinite(n) ? Math.round(n) : null; }
  function r3(x) { return Math.round(x * 1000) / 1000; }
  function toast(t, lang) {
    var x = $('#toast'); x.textContent = t; x.classList.add('zeigen');
    clearTimeout(toast.t); toast.t = setTimeout(function () { x.classList.remove('zeigen'); }, lang ? 6500 : 3200);
  }
  function herunterladen(name, inhalt, typ) {
    var a = el('a'); a.href = URL.createObjectURL(new Blob([inhalt], { type: typ })); a.download = name;
    document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }
  function kopieren(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (ok, nein) {   // Rückfall für http:// im Schulnetz
      var t = el('textarea'); t.value = text; t.style.position = 'fixed'; t.style.opacity = '0'; document.body.appendChild(t); t.select();
      try { document.execCommand('copy') ? ok() : nein(); } catch (e) { nein(e); } t.remove();
    });
  }

  /* ---------- Entwurf ---------- */
  function leer() {
    return { format: 'chronoglobe-beitrag/1', art: null, titel: '', begruendung: '', belege: [{ zitat: '', url: '' }],
      ebene: { format: 'chronoglobe-ebene/1', id: '', name: '', farbe: '#e0b040', beschreibung: '', hinweis: '', quellen: [{ zitat: '', url: '', lizenz: '' }], objekte: [] },
      ziel: { bereich: 'reich-gebiet', datei: DATEI['reich-gebiet'], id: '', name: '' },
      vorschlag: { text: '', felder: {}, geometrie: null }, _ki: null };
  }
  function objektNormal(o) {
    return { id: o.id || '', typ: SYMBOL[o.typ] ? o.typ : 'punkt', name: o.name || '', von: o.von == null ? null : o.von, bis: o.bis == null ? null : o.bis,
      beschreibung: o.beschreibung || '', beleg: o.beleg || '', unsicher: !!o.unsicher,
      koordinaten: o.typ === 'punkt' ? (Array.isArray(o.koordinaten) && typeof o.koordinaten[0] === 'number' ? [o.koordinaten] : (o.koordinaten || []).slice(0, 1)) : (o.koordinaten || []) };
  }
  function normalisieren(x) {   // alte oder fremde Entwürfe auf die aktuelle Form bringen
    var l = leer();
    x = Object.assign(l, x || {});
    x.ebene = Object.assign(leer().ebene, x.ebene || {});
    x.ebene.objekte = (x.ebene.objekte || []).map(objektNormal);
    if (!x.ebene.quellen || !x.ebene.quellen.length) x.ebene.quellen = [{ zitat: '', url: '', lizenz: '' }];
    x.ebene.quellen = x.ebene.quellen.map(function (q) { return { zitat: q.zitat || '', url: q.url || '', lizenz: q.lizenz || '' }; });
    if (!x.belege || !x.belege.length) x.belege = [{ zitat: '', url: '' }];
    x.belege = x.belege.map(function (q) { return { zitat: q.zitat || '', url: q.url || '' }; });
    x.ziel = Object.assign(leer().ziel, x.ziel || {});
    x.vorschlag = Object.assign({ text: '', felder: {}, geometrie: null }, x.vorschlag || {});
    if (!x.vorschlag.felder) x.vorschlag.felder = {};
    var g = x.vorschlag.geometrie;
    if (g && g.typ === 'punkt' && Array.isArray(g.koordinaten) && typeof g.koordinaten[0] === 'number') g.koordinaten = [g.koordinaten];
    return x;
  }
  function laden() { try { var x = JSON.parse(localStorage.getItem(SPEICHER) || 'null'); if (x && x.format === 'chronoglobe-beitrag/1') return normalisieren(x); } catch (e) {} return leer(); }
  function speichern() { try { localStorage.setItem(SPEICHER, JSON.stringify(E)); } catch (e) {} }

  /* Der Beitrag, wie er eingereicht wird: leere Felder und der jeweils andere Teil fallen weg */
  function beitrag() {
    var b = { format: E.format, art: E.art, titel: E.titel.trim(), begruendung: E.begruendung.trim(),
      belege: E.belege.filter(function (q) { return q.zitat.trim(); }).map(function (q) { var o = { zitat: q.zitat.trim() }; if (q.url.trim()) o.url = q.url.trim(); return o; }) };
    if (E.art === 'neue-ebene') {
      var e = E.ebene, x = { format: e.format, id: e.id, name: e.name.trim(), farbe: e.farbe, beschreibung: e.beschreibung.trim() };
      if (e.hinweis.trim()) x.hinweis = e.hinweis.trim();
      x.quellen = e.quellen.filter(function (q) { return q.zitat.trim(); }).map(function (q) {
        var o = { zitat: q.zitat.trim() }; if (q.url.trim()) o.url = q.url.trim(); if (q.lizenz.trim()) o.lizenz = q.lizenz.trim(); return o; });
      x.objekte = e.objekte.map(function (o) {
        var y = { id: o.id, typ: o.typ, name: o.name.trim(), von: o.von };
        if (o.bis != null) y.bis = o.bis;
        if (o.beschreibung && o.beschreibung.trim()) y.beschreibung = o.beschreibung.trim();
        if (o.beleg && o.beleg.trim()) y.beleg = o.beleg.trim();
        if (o.unsicher) y.unsicher = true;
        y.koordinaten = o.typ === 'punkt' ? (o.koordinaten[0] || null) : o.koordinaten;
        return y;
      });
      b.ebene = x;
    } else if (E.art === 'aenderung') {
      b.ziel = E.ziel;
      var v = { text: E.vorschlag.text.trim() }, f = {};
      ['name', 'von', 'bis'].forEach(function (k) { var w = E.vorschlag.felder[k]; if (w != null && w !== '') f[k] = w; });
      if (Object.keys(f).length) v.felder = f;
      var g = E.vorschlag.geometrie;
      if (g && g.typ && g.koordinaten.length) v.geometrie = { typ: g.typ, koordinaten: g.typ === 'punkt' ? g.koordinaten[0] : g.koordinaten };
      b.vorschlag = v;
    }
    return b;
  }

  /* ---------- Verlauf (Rückgängig / Wiederholen) ---------- */
  function schnappschuss() { return JSON.stringify({ E: E, AKT: AKT }); }
  function verlaufJetzt() {
    clearTimeout(HIST.timer); HIST.timer = null;
    var s = schnappschuss(); if (HIST.stapel[HIST.pos] === s) return;
    HIST.stapel = HIST.stapel.slice(0, HIST.pos + 1); HIST.stapel.push(s);
    if (HIST.stapel.length > 150) HIST.stapel.shift();
    HIST.pos = HIST.stapel.length - 1; undoKnoepfe();
  }
  function verlaufMerken() { if (HIST.still) return; clearTimeout(HIST.timer); HIST.timer = setTimeout(verlaufJetzt, 350); }
  function verlaufGehe(d) {
    if (HIST.timer) verlaufJetzt();
    var p = HIST.pos + d; if (p < 0 || p >= HIST.stapel.length) return;
    HIST.pos = p; var s = JSON.parse(HIST.stapel[p]);
    HIST.still = true; E = s.E; AKT = s.AKT; speichern(); formularFuellen(true); artSetzen(E.art); HIST.still = false;
    undoKnoepfe(); toast(d < 0 ? 'Rückgängig' : 'Wiederholt');
  }
  function undoKnoepfe() { $('#btnUndo').disabled = HIST.pos <= 0; $('#btnRedo').disabled = HIST.pos >= HIST.stapel.length - 1; }

  /* ---------- Objekte der Kerndaten für „Änderung“ ---------- */
  function meta(r) { return (D.reiche.meta[r] || (D.frueh && D.frueh.meta[r]) || {}); }
  function reichName(r) { return meta(r).name || r; }
  function auswahl(bereich) {   // → [{ wert, text, gruppe?, roh, geo, datei? }]
    var R = D.reiche, F = D.frueh || { regionen: [], orte: [], ereignisse: [] }, H = D.handel, FD = 'data/fruehe_reiche.json';
    switch (bereich) {
      case 'reich-gebiet': return R.regionen.map(function (f) { var p = f.properties;
          return { wert: String(p.id), gruppe: reichName(p.reich), text: p.name + ' (' + jahr(p.von) + ' – ' + jahr(p.bis) + ')', roh: p, geo: { flaeche: f.geometry } }; })
        .concat(F.regionen.map(function (f) { var p = f.properties;
          return { wert: 'frueh-' + p.id, gruppe: reichName(p.reich) + ' (frühe Hochkulturen)', text: p.name + ' (' + jahr(p.von) + ' – ' + jahr(p.bis) + ')', roh: p, geo: { flaeche: f.geometry }, datei: FD }; }));
      case 'reich-ort': return R.orte.map(function (o, i) { return { wert: 'ort-' + i, gruppe: reichName(o.reich), text: o.name, roh: o, geo: { punkt: [o.lng, o.lat] } }; })
        .concat(F.orte.map(function (o, i) { return { wert: 'frueh-ort-' + i, gruppe: reichName(o.reich) + ' (frühe Hochkulturen)', text: o.name, roh: o, geo: { punkt: [o.lng, o.lat] }, datei: FD }; }));
      case 'reich-ereignis': return R.ereignisse.map(function (e, i) { return { wert: 'ereignis-' + i, gruppe: reichName(e.reich), text: e.label + ': ' + e.titel, roh: e }; })
        .concat(F.ereignisse.map(function (e, i) { return { wert: 'frueh-ereignis-' + i, gruppe: reichName(e.reich) + ' (frühe Hochkulturen)', text: e.label + ': ' + e.titel, roh: e, datei: FD }; }));
      case 'handelsroute': return H.verbindungen.map(function (v) { return { wert: v.id, text: v.name, roh: v, geo: { linie: v.pfad } }; });
      case 'handelsort': return H.orte.map(function (o) { return { wert: o.id, text: o.name, roh: o, geo: { punkt: [o.lng, o.lat] } }; });
      case 'kontakt': return H.kontakte.map(function (k) { return { wert: k.id, text: k.name + ' (' + jahr(k.jahr) + ')', roh: k, geo: k.pfad ? { linie: k.pfad } : { punkt: [k.lng, k.lat] } }; });
      case 'text': return D.texte.texte.map(function (t) { return { wert: t.id, text: t.titel, roh: { id: t.id, titel: t.titel, kurz: t.kurz } }; });
      case 'vignette': return Object.keys(D.vignetten.reiche || {}).map(function (r) { var v = D.vignetten.reiche[r];
        return { wert: r, text: v.name || reichName(r), roh: { reich: r, name: v.name, titel: v.titel, vignetten: (v.vignetten || []).map(function (x) { return x.id + (x.titel ? ': ' + x.titel : ''); }) } }; });
      case 'ebene': var L = [];
        Object.keys(D.ebenen).forEach(function (id) { var e = D.ebenen[id]; (e.objekte || []).forEach(function (o) {
          var g = {}; g[o.typ] = o.koordinaten; L.push({ wert: id + ':' + o.id, gruppe: e.name, text: o.name + ' (' + Themen.zeitText(o) + ')', roh: o, geo: g, datei: 'data/ebenen/' + id + '.json' }); }); });
        return L;
      default: return [];
    }
  }
  function zielAnzeigen(fokus) {
    var b = E.ziel.bereich, sel = $('#zObjekt'), L = auswahl(b), such = UI.zSuche.toLowerCase();
    $('#zObjektFeld').hidden = b === 'sonstiges';
    sel.innerHTML = '';
    var gefiltert = L.filter(function (x) { return !such || (x.text + ' ' + (x.gruppe || '')).toLowerCase().indexOf(such) >= 0 || x.wert === E.ziel.id; });
    if (!L.length) sel.appendChild(el('option', null, b === 'ebene' ? 'noch keine Themenebenen übernommen' : '–')).value = '';
    var gruppen = {};
    gefiltert.forEach(function (x) {
      var o = el('option', null, x.text); o.value = x.wert;
      if (x.gruppe) { if (!gruppen[x.gruppe]) { gruppen[x.gruppe] = el('optgroup'); gruppen[x.gruppe].label = x.gruppe; sel.appendChild(gruppen[x.gruppe]); } gruppen[x.gruppe].appendChild(o); }
      else sel.appendChild(o);
    });
    sel.value = E.ziel.id || '';
    var akt = L.filter(function (x) { return x.wert === E.ziel.id; })[0];
    REF = akt && akt.geo ? akt.geo : null;
    var box = $('#zAktuell'); box.innerHTML = ''; box.hidden = !akt;
    if (akt) {
      box.appendChild(el('h3', null, 'Bisher: ' + akt.text));
      var dl = el('dl');
      ['name', 'titel', 'label', 'von', 'bis', 'jahr', 'note', 'hinweis', 'beschreibung', 'quelle', 'belegt', 'kurz'].forEach(function (k) {
        var w = akt.roh[k]; if (w == null || w === '') return;
        dl.appendChild(el('dt', null, k)); dl.appendChild(el('dd', null, typeof w === 'number' && /von|bis|jahr/.test(k) ? jahr(w) + ' (' + w + ')' : String(w)));
      });
      box.appendChild(dl);
      var det = el('details'); det.appendChild(el('summary', null, 'Alle Felder'));
      det.appendChild(el('pre', null, JSON.stringify(akt.roh, function (k, v) { return k === 'pfad' || k === 'rand' ? '[' + (v.length || 0) + ' Punkte]' : v; }, 2)));
      box.appendChild(det);
      $('#vName').placeholder = akt.roh.name || akt.roh.titel || '';
    }
    karteZeichnen(fokus);
  }

  /* ---------- Neue Ebene: Objekte ---------- */
  function eindeutig(basis, ausser) {
    var id = Themen.slug(basis).slice(0, 50) || 'objekt', n = 1, x = id;
    while (E.ebene.objekte.some(function (o, i) { return i !== ausser && o.id === x; })) x = id + '-' + (++n);
    return x.length < 2 ? x + '-1' : x;
  }
  function objektNeu(typ) {
    E.ebene.objekte.push(objektNormal({ id: eindeutig('objekt-' + (E.ebene.objekte.length + 1)), typ: typ }));
    AKT = E.ebene.objekte.length - 1; UI.suche = ''; $('#oSuche').value = '';
    zeichnenSetzen(true); objekteAnzeigen(); $('#oName').focus(); aenderung();
  }
  function objekteAnhaengen(liste) {
    var erster = E.ebene.objekte.length;
    liste.forEach(function (o) { var x = objektNormal(o); E.ebene.objekte.push(x); x.id = eindeutig(x.id || x.name || 'objekt', E.ebene.objekte.length - 1); });
    AKT = liste.length ? erster : AKT;
    objekteAnzeigen(); aenderung(); fitAlle();
  }
  var GEO_HINWEIS = { punkt: 'Klick auf die Karte setzt den Ort – oder Breite/Länge eingeben. Den Punkt kannst du danach ziehen.',
    linie: 'Nacheinander die Punkte der Linie anklicken. Punkte ziehen verschiebt sie, Rechtsklick löscht einen Punkt.',
    flaeche: 'Die Eckpunkte der Fläche anklicken; sie wird automatisch geschlossen. Punkte ziehen verschiebt sie.' };
  function objektProbleme(o) {
    var p = [];
    if (!o.name.trim()) p.push('Name');
    if (o.von == null) p.push('Jahr');
    if (o.typ === 'punkt' ? !o.koordinaten.length : o.koordinaten.length < (o.typ === 'flaeche' ? 3 : 2)) p.push('Geometrie');
    return p;
  }
  function reihenfolge() {
    var idx = E.ebene.objekte.map(function (_, i) { return i; }), s = UI.suche.toLowerCase();
    if (s) idx = idx.filter(function (i) { var o = E.ebene.objekte[i]; return (o.name + ' ' + o.beschreibung).toLowerCase().indexOf(s) >= 0; });
    if (UI.sort === 'zeit') idx.sort(function (a, b) { var x = E.ebene.objekte[a].von, y = E.ebene.objekte[b].von; return (x == null ? 1e9 : x) - (y == null ? 1e9 : y); });
    if (UI.sort === 'name') idx.sort(function (a, b) { return E.ebene.objekte[a].name.localeCompare(E.ebene.objekte[b].name, 'de'); });
    return idx;
  }
  function objekteAnzeigen() { objektListe(); objektFormular(); }
  function objektListe() {
    var box = $('#oListe'); box.innerHTML = '';
    var n = E.ebene.objekte.length, idx = reihenfolge();
    $('#oAnzahl').textContent = n ? '(' + (idx.length < n ? idx.length + ' von ' : '') + n + ')' : '';
    $('#oFilter').hidden = n < 6;
    if (!n) box.appendChild(el('p', 'leer', 'Noch keine Objekte. Lege einen Ort, eine Linie oder eine Fläche an – oder importiere eine Datei.'));
    idx.forEach(function (i) {
      var o = E.ebene.objekte[i], prob = objektProbleme(o);
      var b = el('button', 'objekt' + (i === AKT ? ' aktiv' : '') + (prob.length ? ' unfertig' : '')); b.type = 'button';
      b.style.setProperty('--c', E.ebene.farbe);
      b.appendChild(el('i', 'sym', SYMBOL[o.typ]));
      var t = el('span', 'text'); t.appendChild(el('b', null, o.name || '(ohne Namen)'));
      t.appendChild(el('small', null, (o.von != null ? Themen.zeitText(o) : 'Jahr fehlt') + ' · ' + o.koordinaten.length + ' Pkt.' + (o.unsicher ? ' · unsicher' : '')));
      b.appendChild(t);
      if (prob.length) { var w = el('em', 'fehlt', prob.join(', ') + ' fehlt'); b.appendChild(w); }
      b.addEventListener('click', function () { AKT = i; objekteAnzeigen(); karteZeichnen(); verlaufMerken(); });
      box.appendChild(b);
    });
    var o = E.ebene.objekte[AKT];
    $('#kTitel').textContent = o ? (SYMBOL[o.typ] + ' ' + (o.name || 'Objekt')) : 'Karte';
  }
  function objektFormular() {
    var o = E.ebene.objekte[AKT];
    $('#oForm').hidden = !o;
    if (!o) return;
    $('#oName').value = o.name; $('#oTyp').value = o.typ; $('#oVon').value = o.von == null ? '' : o.von; $('#oBis').value = o.bis == null ? '' : o.bis;
    $('#oBeschreibung').value = o.beschreibung || ''; $('#oBeleg').value = o.beleg || ''; $('#oUnsicher').checked = !!o.unsicher;
    $('#oPunkt').hidden = o.typ !== 'punkt';
    var p = o.koordinaten[0]; $('#oLat').value = o.typ === 'punkt' && p ? p[1] : ''; $('#oLng').value = o.typ === 'punkt' && p ? p[0] : '';
    $('#oGeoHinweis').textContent = GEO_HINWEIS[o.typ];
    jahrTexte();
  }
  function jahrTexte() {
    [['#oVon', '#oVonTxt'], ['#oBis', '#oBisTxt'], ['#vVon', '#vVonTxt'], ['#vBis', '#vBisTxt']].forEach(function (p) {
      var v = zahlOderNull($(p[0]).value); $(p[1]).textContent = v == null ? '' : '= ' + jahr(v);
    });
  }

  /* Listen mit Zitat/URL(/Lizenz) – Quellen der Ebene und Belege des Beitrags */
  function listeAnzeigen(box, L, felder) {
    box.innerHTML = '';
    L.forEach(function (q, i) {
      var z = el('div', 'listenzeile');
      felder.forEach(function (f) {
        var inp = el('input'); inp.type = 'text'; inp.placeholder = f[1]; inp.value = q[f[0]] || ''; inp.setAttribute('aria-label', f[1]);
        if (f[0] === 'zitat') inp.className = 'breit';
        inp.addEventListener('input', function () { q[f[0]] = inp.value; aenderung(); });
        z.appendChild(inp);
      });
      var x = el('button', 'weg', '×'); x.type = 'button'; x.title = 'Entfernen'; x.setAttribute('aria-label', 'Eintrag entfernen');
      x.addEventListener('click', function () { L.splice(i, 1); if (!L.length) L.push(felder.reduce(function (o, f) { o[f[0]] = ''; return o; }, {})); listeAnzeigen(box, L, felder); aenderung(); });
      z.appendChild(x); box.appendChild(z);
    });
  }
  var QF = [['zitat', 'Zitat, z. B. Lehner, Mark: The Complete Pyramids. London 1997'], ['url', 'Link (optional)'], ['lizenz', 'Lizenz bei Datensätzen (optional)']];
  var BF = [['zitat', 'Beleg: Autor, Titel, Jahr, Seite'], ['url', 'Link (optional)']];

  /* ---------- Karte (d3, Plattkarte mit Zoom, Zeichnen, Ziehen) ---------- */
  var K = { svg: null, g: null, proj: null, pfad: null, k: 1 };
  function karteEinrichten() {
    var svg = d3.select('#karte');
    svg.attr('viewBox', '0 0 ' + W + ' ' + H);
    K.proj = d3.geoEquirectangular().fitSize([W, H], { type: 'Sphere' });
    K.pfad = d3.geoPath(K.proj);
    K.svg = svg; K.g = svg.append('g');
    K.g.append('path').attr('class', 'meer').attr('d', K.pfad({ type: 'Sphere' }));
    K.g.append('path').attr('class', 'netz').attr('d', K.pfad(d3.geoGraticule10()));
    K.g.append('path').attr('class', 'land').attr('d', K.pfad(D.land.type === 'Feature' ? D.land : { type: 'Feature', geometry: D.land.geometry || D.land }));
    K.reiche = K.g.append('g').attr('class', 'reiche'); K.ref = K.g.append('g'); K.obj = K.g.append('g'); K.lbl = K.g.append('g').attr('class', 'beschriftung');
    K.zoom = d3.zoom().scaleExtent([1, 80]).translateExtent([[0, 0], [W, H]]).clickDistance(5)
      .on('zoom', function (ev) { K.k = ev.transform.k; K.g.attr('transform', ev.transform); massstab(); });
    svg.call(K.zoom).on('dblclick.zoom', null);
    svg.on('click', function (ev) {
      if (!UI.zeichnen) return;
      var ll = lngLat(ev); if (ll) punktSetzen(ll);
    });
    svg.on('mousemove', function (ev) { var ll = lngLat(ev); $('#kKoord').textContent = ll ? ll[1].toFixed(2) + '° ' + (ll[1] >= 0 ? 'N' : 'S') + ' · ' + Math.abs(ll[0]).toFixed(2) + '° ' + (ll[0] >= 0 ? 'O' : 'W') : ''; });
    svg.on('mouseleave', function () { $('#kKoord').textContent = ''; });
  }
  function lngLat(ev) {
    var t = d3.zoomTransform(K.svg.node()), p = d3.pointer(ev, K.svg.node()), ll = K.proj.invert(t.invert(p));
    return ll && isFinite(ll[0]) ? [r3(ll[0]), r3(ll[1])] : null;
  }
  function massstab() {
    var k = K.k;
    K.svg.selectAll('circle[data-r]').attr('r', function () { return this.getAttribute('data-r') / k; });
    K.lbl.selectAll('text').attr('font-size', 11 / k).attr('dx', 7 / k).attr('dy', 3.5 / k).attr('stroke-width', 3 / k);
    K.lbl.classed('aus', k < 2.5 && E.ebene.objekte.length > 25);
  }
  function aktiveGeometrie() {
    if (E.art === 'neue-ebene') return E.ebene.objekte[AKT] || null;
    if (E.art === 'aenderung' && E.vorschlag.geometrie && E.vorschlag.geometrie.typ) return E.vorschlag.geometrie;
    return null;
  }
  function punktSetzen(ll) {
    var g = aktiveGeometrie();
    if (!g) { toast(E.art === 'aenderung' ? 'Zum Zeichnen zuerst den Typ der neuen Geometrie wählen.' : 'Zuerst ein Objekt anlegen: + Ort, + Linie oder + Fläche.'); return; }
    if (g.typ === 'punkt') g.koordinaten = [ll]; else g.koordinaten.push(ll);
    if (E.art === 'neue-ebene') objekteAnzeigen();
    aenderung();
  }
  function geoFeature(typ, k) {
    if (typ === 'punkt') return { type: 'Point', coordinates: k[0] || k };
    if (typ === 'linie') return { type: 'LineString', coordinates: k };
    // d3 rechnet auf der Kugel: ein Ring in der „falschen“ Richtung meint alles außer dem Gebiet. Dann umdrehen.
    var r = k.concat([k[0]]), poly = { type: 'Polygon', coordinates: [r] };
    if (d3.geoArea(poly) > 2 * Math.PI) poly.coordinates = [r.slice().reverse()];
    return poly;
  }
  function reicheZeichnen() {
    K.reiche.selectAll('*').remove();
    if (UI.jahr == null || !D.reiche) return;
    var y = UI.jahr, alle = D.reiche.regionen.concat(D.frueh ? D.frueh.regionen : []);
    alle.filter(function (f) { return f.properties.von <= y && y < f.properties.bis; }).forEach(function (f) {
      K.reiche.append('path').attr('d', K.pfad(f)).style('--c', meta(f.properties.reich).farbe || '#888')
        .append('title').text(reichName(f.properties.reich) + ': ' + f.properties.name);
    });
  }
  var ZIEHEN = d3.drag()
    .on('start', function () { d3.select(this).classed('zieht', true); })
    .on('drag', function (ev) {
      var ll = K.proj.invert([ev.x, ev.y]); if (!ll) return;
      var i = +this.getAttribute('data-i'), g = aktiveGeometrie(); if (!g) return;
      g.koordinaten[i] = [r3(ll[0]), r3(ll[1])];
      d3.select(this).attr('cx', ev.x).attr('cy', ev.y);
      var grp = d3.select(this.parentNode);
      grp.select('path.linie').attr('d', g.typ === 'linie' || g.koordinaten.length === 2 ? K.pfad(geoFeature('linie', g.koordinaten)) : null);
      grp.select('path.flaeche').attr('d', g.koordinaten.length > 2 ? K.pfad(geoFeature('flaeche', g.koordinaten)) : null);
      $('#kKoord').textContent = r3(ll[1]) + '° / ' + r3(ll[0]) + '°';
    })
    .on('end', function () { d3.select(this).classed('zieht', false); if (E.art === 'neue-ebene') objekteAnzeigen(); aenderung(); });
  function karteZeichnen(fokus) {
    if (!K.g) return;
    K.ref.selectAll('*').remove(); K.obj.selectAll('*').remove(); K.lbl.selectAll('*').remove();
    K.svg.classed('zeichnen', UI.zeichnen);
    if (E.art === 'aenderung' && REF) {
      if (REF.flaeche) K.ref.append('path').attr('class', 'ref').attr('d', K.pfad(REF.flaeche));
      if (REF.linie) K.ref.append('path').attr('class', 'ref offen').attr('d', K.pfad({ type: 'LineString', coordinates: REF.linie }));
      if (REF.punkt) K.ref.append('circle').attr('class', 'ref').attr('data-r', 6).attr('cx', K.proj(REF.punkt)[0]).attr('cy', K.proj(REF.punkt)[1]);
      if (fokus) zuGeometrie(REF.flaeche || (REF.linie ? { type: 'LineString', coordinates: REF.linie } : { type: 'Point', coordinates: REF.punkt }));
    }
    var liste = E.art === 'neue-ebene' ? E.ebene.objekte.map(function (o, i) { return { g: o, i: i, aktiv: i === AKT }; })
      : (E.vorschlag.geometrie && E.vorschlag.geometrie.typ ? [{ g: E.vorschlag.geometrie, i: -1, aktiv: true }] : []);
    var farbe = E.art === 'neue-ebene' ? E.ebene.farbe : '#5cc2ff';
    liste.sort(function (a, b) { return a.aktiv - b.aktiv; });   // aktives Objekt oben
    liste.forEach(function (x) {
      var g = x.g, k = g.koordinaten || []; if (!k.length) return;
      var blass = UI.jahr != null && E.art === 'neue-ebene' && g.von != null && !Themen.sichtbar(g, UI.jahr);
      var grp = K.obj.append('g').attr('class', 'obj' + (x.aktiv ? ' aktiv' : '') + (blass ? ' blass' : '')).style('--c', farbe);
      if (!x.aktiv) grp.on('click', function (ev) { if (UI.zeichnen) return; ev.stopPropagation(); AKT = x.i; objekteAnzeigen(); karteZeichnen(); verlaufMerken(); });
      grp.append('path').attr('class', 'flaeche').attr('d', g.typ === 'flaeche' && k.length > 2 ? K.pfad(geoFeature('flaeche', k)) : null);
      grp.append('path').attr('class', 'linie').attr('d', (g.typ === 'linie' && k.length > 1) || (g.typ === 'flaeche' && k.length === 2) ? K.pfad(geoFeature('linie', k)) : null);
      k.forEach(function (p, j) {
        var xy = K.proj(p), c = grp.append('circle').attr('class', g.typ === 'punkt' ? 'ort' : 'ecke')
          .attr('data-r', g.typ === 'punkt' ? (x.aktiv ? 7 : 5) : x.aktiv ? 4.5 : 2.2).attr('data-i', j).attr('cx', xy[0]).attr('cy', xy[1]);
        c.append('title').text((g.name ? g.name + ' · ' : '') + (g.typ === 'punkt' ? '' : 'Punkt ' + (j + 1) + ': ') + p[1] + '° N, ' + p[0] + '° O');
        if (x.aktiv) {
          c.call(ZIEHEN).on('click', function (ev) { ev.stopPropagation(); })
            .on('contextmenu', function (ev) { ev.preventDefault(); ev.stopPropagation(); g.koordinaten.splice(j, 1); if (E.art === 'neue-ebene') objekteAnzeigen(); aenderung(); toast('Punkt gelöscht'); });
        }
      });
      if (g.typ === 'punkt' && g.name) {
        var xy = K.proj(k[0]);
        K.lbl.append('text').attr('x', xy[0]).attr('y', xy[1]).attr('class', blass ? 'blass' : null).text(g.name);
      }
    });
    massstab();
  }
  function zuGeometrie(geo) {
    if (!geo || !K.zoom) return;
    var b = K.pfad.bounds(geo), dx = b[1][0] - b[0][0], dy = b[1][1] - b[0][1];
    if (!isFinite(dx)) return;
    var k = Math.max(1, Math.min(40, 0.8 / Math.max(dx / W, dy / H, 0.01)));
    var t = d3.zoomIdentity.translate(W / 2 - k * (b[0][0] + b[1][0]) / 2, H / 2 - k * (b[0][1] + b[1][1]) / 2).scale(k);
    K.svg.transition().duration(550).call(K.zoom.transform, t);
  }
  function fitAlle() {
    var f = E.ebene.objekte.filter(function (o) { return o.koordinaten.length; }).map(function (o) {
      return { type: 'Feature', geometry: o.typ === 'punkt' ? { type: 'Point', coordinates: o.koordinaten[0] } : { type: 'LineString', coordinates: o.koordinaten.length > 1 ? o.koordinaten : [o.koordinaten[0], o.koordinaten[0]] } };
    });
    if (E.art === 'aenderung' && REF) return karteZeichnen(true);
    if (f.length) zuGeometrie({ type: 'FeatureCollection', features: f });
  }
  function karteAuf(zentrum, zoom) {
    if (!K.zoom || !Array.isArray(zentrum)) return;
    var k = Math.max(1, Math.min(80, Number(zoom) || 4)), p = K.proj(zentrum);
    K.svg.transition().duration(650).call(K.zoom.transform, d3.zoomIdentity.translate(W / 2 - k * p[0], H / 2 - k * p[1]).scale(k));
  }
  function zeichnenSetzen(v) {
    UI.zeichnen = v; var b = $('#kZeichnen'); b.classList.toggle('an', v); b.setAttribute('aria-pressed', String(v));
    $('#kHilfe').textContent = v ? 'Klicken setzt Punkte · Punkte ziehen verschiebt sie · Rechtsklick auf einen Punkt löscht ihn'
      : 'Auswählen: Objekt anklicken, um es zu bearbeiten · ✎ oder Esc schaltet das Zeichnen wieder ein';
    if (K.svg) K.svg.classed('zeichnen', v);
  }
  function zeitSetzen(an, wert) {
    UI.jahr = an ? Number(wert) : null;
    $('#zeitAn').checked = an; $('#zeitJahr').disabled = !an; if (wert != null) $('#zeitJahr').value = wert;
    $('#zeitTxt').textContent = an ? jahr(UI.jahr) : 'alle Jahre';
    reicheZeichnen(); karteZeichnen();
  }

  /* ---------- Ausgabe, Status, Schritte ---------- */
  function ausgabe() {
    var b = beitrag(), fehler = Themen.beitragPruefen(b);
    var ul = $('#pFehler'); ul.innerHTML = '';
    fehler.forEach(function (f) { ul.appendChild(el('li', null, f)); });
    $('#pOk').hidden = !!fehler.length;
    $('#pJson').textContent = JSON.stringify(b, null, 2);
    var a = $('#aGithub'), url = fehler.length ? null : Themen.githubAdresse(REPO, ZWEIG, b);
    a.classList.toggle('aus', !url); a.setAttribute('aria-disabled', String(!url));
    if (url) a.href = url; else a.removeAttribute('href');
    $('#aGithubHinweis').textContent = fehler.length ? 'Der Pull Request ist möglich, sobald die Punkte oben erledigt sind.'
      : url ? 'GitHub öffnet sich mit der fertigen Datei ' + Themen.dateiname(b) + '. Unten auf „Propose new file“ bzw. „Commit changes“ klicken, dann „Create pull request“.'
      : 'Der Beitrag ist zu groß für einen Link. Bitte „Als Datei“ herunterladen und hier hochladen: ' + Themen.githubHochladen(REPO, ZWEIG);
    $('#aVorschau').hidden = E.art !== 'neue-ebene';
    var offenKi = E._ki ? E._ki.pruefen.filter(function (_, i) { return !(E._ki.erledigt || [])[i]; }).length : 0;
    var st = $('#status');
    st.textContent = fehler.length ? fehler.length + ' offen' + (offenKi ? ' · ' + offenKi + ' prüfen' : '') : offenKi ? '✓ vollständig · ' + offenKi + ' prüfen' : '✓ bereit';
    st.className = 'status ' + (fehler.length ? 'offen' : offenKi ? 'pruefen' : 'bereit');
    kiPruefenAnzeigen();
    schritte(fehler);
  }
  function schritte(fehler) {
    var inhalt = fehler.filter(function (f) { return /^(Ebene|ziel|vorschlag)/.test(f); }).length === 0 &&
      (E.art === 'neue-ebene' ? E.ebene.objekte.length > 0 : !!E.vorschlag.text.trim());
    var belege = fehler.filter(function (f) { return /^(titel|begruendung|belege)/.test(f); }).length === 0;
    var zustand = { art: !!E.art, inhalt: inhalt, belege: belege, einreichen: !fehler.length };
    $$('[data-schritt]').forEach(function (b) { b.classList.toggle('fertig', !!zustand[b.getAttribute('data-schritt')]); });
  }
  function kiPruefenAnzeigen() {
    var k = E._ki, box = $('#kiPruefen');
    box.hidden = !(k && (k.pruefen.length || k.ausgelassen.length));
    if (box.hidden) return;
    var ul = $('#kiListe'); ul.innerHTML = '';
    k.erledigt = k.erledigt || [];
    k.pruefen.forEach(function (t, i) {
      var li = el('li'), lab = el('label'), cb = el('input'); cb.type = 'checkbox'; cb.checked = !!k.erledigt[i];
      cb.addEventListener('change', function () { k.erledigt[i] = cb.checked; aenderung(); });
      lab.appendChild(cb); lab.appendChild(el('span', null, t)); li.appendChild(lab); ul.appendChild(li);
    });
    if (!k.pruefen.length) ul.appendChild(el('li', 'hint', 'Keine Prüfhinweise.'));
    $('#kiAusgelassenBox').hidden = !k.ausgelassen.length;
    var ua = $('#kiAusgelassen'); ua.innerHTML = ''; k.ausgelassen.forEach(function (t) { ua.appendChild(el('li', null, t)); });
  }
  function aenderung() { speichern(); karteZeichnen(); ausgabe(); verlaufMerken(); }

  /* ---------- Ansicht wechseln ---------- */
  function startZeigen() { $('#start').hidden = false; $('#arbeit').hidden = true; $('#schritte').hidden = true; }
  function artSetzen(art) {
    E.art = art || null;
    $('#start').hidden = !!art; $('#arbeit').hidden = !art; $('#schritte').hidden = !art;
    $$('input[name=art]').forEach(function (r) { r.checked = r.value === art; });
    $('#teilAenderung').hidden = art !== 'aenderung';
    $('#teilEbene').hidden = $('#teilObjekte').hidden = art !== 'neue-ebene';
    $('#teilGemeinsam').hidden = !art;
    if (!art) return;
    if (art === 'aenderung') zielAnzeigen();
    if (art === 'neue-ebene') { ebeneKopf(); objekteAnzeigen(); karteZeichnen(); }
    aenderung();
  }
  function ebeneKopf() {
    $('#eFarbpunkt').style.background = E.ebene.farbe;
    $('#eZusammen').textContent = E.ebene.name ? E.ebene.name : '';
  }

  /* ---------- KI-Assistent ---------- */
  function kiSeite(n) {
    $('#kiSeite1').hidden = n !== 1; $('#kiSeite2').hidden = n !== 2;
    $('#kiTab1').setAttribute('aria-selected', String(n === 1)); $('#kiTab2').setAttribute('aria-selected', String(n === 2));
    if (n === 2) $('#kiAntwort').focus();
  }
  function kiModus() { var r = $('input[name=kiModus]:checked'); return r ? r.value : 'neue-ebene'; }
  function kiPromptAktualisieren() {
    var p = KI.prompt({ modus: kiModus(), datensatz: $('#kiDaten').value, dateiname: UI.kiDateiname || '', thema: $('#kiThema').value, hinweise: $('#kiWuensche').value });
    $('#kiPrompt').value = p;
    var n = p.length, tok = Math.round(n / 3.5);
    $('#kiGroesse').textContent = n.toLocaleString('de-DE') + ' Zeichen, etwa ' + tok.toLocaleString('de-DE') + ' Tokens.' +
      (n > 120000 ? ' Sehr groß: viele KIs schneiden das ab – Datensatz besser in Teilen verarbeiten und die Objekte jeweils anhängen.' : '') +
      (!$('#kiDaten').value.trim() ? ' Noch kein Datensatz eingefügt.' : '');
    $('#kiGroesse').classList.toggle('warn', n > 120000);
  }
  function kiAntwortPruefen() {
    var t = $('#kiAntwort').value, box = $('#kiErgebnis');
    UI.kiErgebnis = null; $('#kiErsetzen').disabled = $('#kiAnhaengen').disabled = true;
    if (!t.trim()) { box.hidden = true; return; }
    var r = KI.antwortLesen(t); box.hidden = false; box.innerHTML = '';
    if (!r.beitrag) { box.className = 'ki-ergebnis schlecht'; box.appendChild(el('b', null, 'Kein brauchbares JSON gefunden')); r.fehler.forEach(function (f) { box.appendChild(el('p', null, f)); }); return; }
    UI.kiErgebnis = r;
    var b = r.beitrag, o = b.ebene ? b.ebene.objekte : [];
    box.className = 'ki-ergebnis ' + (r.fehler.length ? 'mittel' : 'gut');
    box.appendChild(el('b', null, b.art === 'neue-ebene' ? '◈ Themenebene „' + (b.ebene.name || '?') + '“' : '✎ Änderung: ' + (b.titel || '?')));
    if (b.art === 'neue-ebene') {
      var z = { punkt: 0, linie: 0, flaeche: 0 }; o.forEach(function (x) { z[x.typ] = (z[x.typ] || 0) + 1; });
      var sp = o.length ? Themen.spanne(b.ebene) : null;
      box.appendChild(el('p', null, o.length + ' Objekte (' + z.punkt + ' Orte, ' + z.linie + ' Linien, ' + z.flaeche + ' Flächen)' + (sp && isFinite(sp.von) ? ' · ab ' + jahr(sp.von) : '')));
    }
    var ed = r.editor;
    if (ed.pruefen.length || ed.ausgelassen.length) box.appendChild(el('p', null, '✦ ' + ed.pruefen.length + ' Prüfhinweise, ' + ed.ausgelassen.length + ' ausgelassene Einträge – sie erscheinen im Editor als Checkliste.'));
    if (r.hinweise.length) { var h = el('ul', 'hinweise'); r.hinweise.forEach(function (x) { h.appendChild(el('li', null, x)); }); box.appendChild(h); }
    if (r.fehler.length) { box.appendChild(el('p', 'warn', 'Noch offen (kannst du im Editor ergänzen):')); var f = el('ul'); r.fehler.slice(0, 8).forEach(function (x) { f.appendChild(el('li', null, x)); }); if (r.fehler.length > 8) f.appendChild(el('li', null, '… und ' + (r.fehler.length - 8) + ' weitere')); box.appendChild(f); }
    $('#kiErsetzen').disabled = false;
    $('#kiAnhaengen').disabled = b.art !== 'neue-ebene' || E.art !== 'neue-ebene' || !o.length;
  }
  function kiUebernehmen(nurObjekte) {
    var r = UI.kiErgebnis; if (!r) return;
    var b = r.beitrag, ed = r.editor;
    if (nurObjekte) objekteAnhaengen(b.ebene.objekte);
    else {
      E = normalisieren(b); AKT = E.ebene.objekte.length ? 0 : -1;
      if (E.art === 'aenderung') zielZuordnen();
      formularFuellen(true); artSetzen(E.art);
    }
    var alt = E._ki || { pruefen: [], ausgelassen: [], erledigt: [] };
    E._ki = nurObjekte ? { pruefen: alt.pruefen.concat(ed.pruefen), ausgelassen: alt.ausgelassen.concat(ed.ausgelassen), erledigt: alt.erledigt }
      : { pruefen: ed.pruefen, ausgelassen: ed.ausgelassen, erledigt: [] };
    $('#kiDialog').close();
    if (ed.jahr != null && KI.zahl(ed.jahr) != null) zeitSetzen(true, Math.max(-3500, Math.min(2000, Math.round(KI.zahl(ed.jahr)))));
    if (ed.karte && Array.isArray(ed.karte.zentrum)) setTimeout(function () { karteAuf(ed.karte.zentrum, ed.karte.zoom); }, 50);
    else setTimeout(fitAlle, 50);
    aenderung(); verlaufJetzt();
    toast('✦ Übernommen' + (r.fehler.length ? ' – ' + r.fehler.length + ' Punkte noch offen' : '') + (ed.pruefen.length ? ', ' + ed.pruefen.length + ' Prüfhinweise' : ''), true);
  }
  function zielZuordnen() {   // die KI kennt nur Namen: passendes Objekt in den Kerndaten suchen
    var z = E.ziel; if (!Themen.BEREICHE[z.bereich]) z.bereich = 'sonstiges';
    z.datei = DATEI[z.bereich];
    if (z.id || !z.name) return;
    var n = z.name.toLowerCase(), L = auswahl(z.bereich);
    var x = L.filter(function (a) { return a.text.toLowerCase() === n; })[0] || L.filter(function (a) { return a.text.toLowerCase().indexOf(n) >= 0; })[0];
    if (x) { z.id = x.wert; z.name = x.text; z.datei = x.datei || DATEI[z.bereich]; }
  }

  /* ---------- Dateien (Import, KI-Datensatz, KI-Antwort) ---------- */
  function dateiWaehlen(zweck) { UI.dateiZweck = zweck; var f = $('#datei'); f.value = ''; f.click(); }
  function dateiGelesen(name, text) {
    if (UI.dateiZweck === 'kiDaten') {
      UI.kiDateiname = name; $('#kiDaten').value = text; $('#kiDateiInfo').textContent = name + ' · ' + text.length.toLocaleString('de-DE') + ' Zeichen';
      kiPromptAktualisieren(); return;
    }
    if (UI.dateiZweck === 'kiAntwort') { $('#kiAntwort').value = text; kiAntwortPruefen(); return; }
    var r = KI.importieren(text, name);
    if (r.fehler) { toast(r.fehler.join(' '), true); return; }
    if (E.art !== 'neue-ebene') artSetzen('neue-ebene');
    if (!E.ebene.name) { E.ebene.name = name.replace(/\.[a-z]+$/i, '').replace(/[_-]+/g, ' '); E.ebene.id = Themen.slug(E.ebene.name); $('#eName').value = E.ebene.name; ebeneKopf(); }
    objekteAnhaengen(r.objekte);
    toast('⇪ ' + r.objekte.length + ' Objekte aus ' + name + ' übernommen' + (r.hinweise.length ? ' · ' + r.hinweise.join(' · ') : ''), true);
  }

  /* ---------- Oberfläche verdrahten ---------- */
  function binde(sel, fn, ev) { var x = $(sel); x.addEventListener(ev || 'input', function () { fn(x); aenderung(); }); }
  function verdrahten() {
    $$('[data-start]').forEach(function (b) { b.addEventListener('click', function () {
      var s = b.getAttribute('data-start');
      if (s === 'ki') { $('#kiDialog').showModal(); kiSeite(1); kiPromptAktualisieren(); return; }
      if (s === 'import') { dateiWaehlen('import'); return; }
      artSetzen(s); verlaufJetzt();
    }); });
    $('#btnStart').addEventListener('click', startZeigen);
    $$('input[name=art]').forEach(function (r) { r.addEventListener('change', function () { artSetzen(r.value); }); });
    $$('[data-schritt]').forEach(function (b) { b.addEventListener('click', function () {
      var z = { art: '#teilArt', inhalt: E.art === 'aenderung' ? '#teilAenderung' : '#teilObjekte', belege: '#teilGemeinsam', einreichen: '#ausgabe' }[b.getAttribute('data-schritt')];
      var x = $(z); if (x) x.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }); });
    $('#btnUndo').addEventListener('click', function () { verlaufGehe(-1); });
    $('#btnRedo').addEventListener('click', function () { verlaufGehe(1); });
    // Änderung
    var bs = $('#zBereich'); Object.keys(Themen.BEREICHE).forEach(function (k) { var o = el('option', null, Themen.BEREICHE[k]); o.value = k; bs.appendChild(o); });
    bs.addEventListener('change', function () { E.ziel = { bereich: bs.value, datei: DATEI[bs.value], id: '', name: '' }; UI.zSuche = ''; $('#zSuche').value = ''; zielAnzeigen(); aenderung(); });
    $('#zSuche').addEventListener('input', function () { UI.zSuche = this.value; zielAnzeigen(); });
    $('#zObjekt').addEventListener('change', function () {
      var s = $('#zObjekt'), x = auswahl(E.ziel.bereich).filter(function (a) { return a.wert === s.value; })[0];
      E.ziel.id = s.value; E.ziel.name = x ? x.text : ''; E.ziel.datei = (x && x.datei) || DATEI[E.ziel.bereich];
      zielAnzeigen(true); aenderung();
    });
    binde('#vText', function (x) { E.vorschlag.text = x.value; });
    binde('#vName', function (x) { E.vorschlag.felder.name = x.value.trim() || null; });
    binde('#vVon', function (x) { E.vorschlag.felder.von = zahlOderNull(x.value); jahrTexte(); });
    binde('#vBis', function (x) { E.vorschlag.felder.bis = zahlOderNull(x.value); jahrTexte(); });
    binde('#vGeoTyp', function (x) { E.vorschlag.geometrie = x.value ? { typ: x.value, koordinaten: [] } : null; if (x.value) zeichnenSetzen(true); }, 'change');
    // Neue Ebene
    binde('#eName', function (x) { E.ebene.name = x.value; E.ebene.id = Themen.slug(x.value); ebeneKopf(); });
    binde('#eFarbe', function (x) { E.ebene.farbe = x.value; ebeneKopf(); objektListe(); });
    binde('#eBeschreibung', function (x) { E.ebene.beschreibung = x.value; });
    binde('#eHinweis', function (x) { E.ebene.hinweis = x.value; });
    $('#eQuelleNeu').addEventListener('click', function () { E.ebene.quellen.push({ zitat: '', url: '', lizenz: '' }); listeAnzeigen($('#eQuellen'), E.ebene.quellen, QF); });
    $$('[data-neu]').forEach(function (b) { b.addEventListener('click', function () { objektNeu(b.getAttribute('data-neu')); }); });
    $('#oImport').addEventListener('click', function () { dateiWaehlen('import'); });
    $('#oSuche').addEventListener('input', function () { UI.suche = this.value; objektListe(); });
    $('#oSort').addEventListener('change', function () { UI.sort = this.value; objektListe(); });
    function obj(fn) { return function (x) { var o = E.ebene.objekte[AKT]; if (o) { fn(o, x); objektListe(); } }; }
    binde('#oName', obj(function (o, x) { o.name = x.value; o.id = eindeutig(x.value || 'objekt', AKT); }));
    binde('#oTyp', obj(function (o, x) { o.typ = x.value; if (o.typ === 'punkt') o.koordinaten = o.koordinaten.slice(0, 1); objektFormular(); }), 'change');
    binde('#oVon', obj(function (o, x) { o.von = zahlOderNull(x.value); jahrTexte(); }));
    binde('#oBis', obj(function (o, x) { o.bis = zahlOderNull(x.value); jahrTexte(); }));
    binde('#oBeschreibung', obj(function (o, x) { o.beschreibung = x.value; }));
    binde('#oBeleg', obj(function (o, x) { o.beleg = x.value; }));
    binde('#oUnsicher', obj(function (o, x) { o.unsicher = x.checked; }), 'change');
    function latLng() { var o = E.ebene.objekte[AKT], la = Number($('#oLat').value), ln = Number($('#oLng').value);
      if (o && $('#oLat').value !== '' && $('#oLng').value !== '' && Math.abs(la) <= 90 && Math.abs(ln) <= 180) { o.koordinaten = [[r3(ln), r3(la)]]; objektListe(); aenderung(); } }
    $('#oLat').addEventListener('change', latLng); $('#oLng').addEventListener('change', latLng);
    $('#oZeigen').addEventListener('click', function () { var o = E.ebene.objekte[AKT]; if (o && o.koordinaten.length) zuGeometrie(geoFeature(o.typ === 'flaeche' && o.koordinaten.length < 3 ? 'linie' : o.typ, o.koordinaten)); });
    $('#oKopie').addEventListener('click', function () {
      var o = E.ebene.objekte[AKT]; if (!o) return;
      var k = JSON.parse(JSON.stringify(o)); k.name = o.name + ' (Kopie)'; E.ebene.objekte.splice(AKT + 1, 0, k); AKT++; k.id = eindeutig(k.name, AKT);
      objekteAnzeigen(); aenderung(); toast('Objekt dupliziert');
    });
    $('#oLoeschen').addEventListener('click', function () {
      if (AKT < 0) return; var n = E.ebene.objekte[AKT].name || 'ohne Namen';
      E.ebene.objekte.splice(AKT, 1); AKT = Math.min(AKT, E.ebene.objekte.length - 1); objekteAnzeigen(); aenderung();
      toast('„' + n + '“ gelöscht – Strg+Z holt es zurück');
    });
    $('#oTauschen').addEventListener('click', function () { KI.tauschen(E.ebene.objekte); objekteAnzeigen(); aenderung(); fitAlle(); toast('Länge und Breite getauscht'); });
    $('#oAlleLoeschen').addEventListener('click', function () {
      if (!E.ebene.objekte.length || !confirm('Alle ' + E.ebene.objekte.length + ' Objekte löschen?')) return;
      E.ebene.objekte = []; AKT = -1; objekteAnzeigen(); aenderung();
    });
    $$('[data-geo]').forEach(function (b) { b.addEventListener('click', function () {
      var g = aktiveGeometrie(); if (!g) return;
      if (b.getAttribute('data-geo') === 'zurueck') g.koordinaten.pop(); else g.koordinaten = [];
      if (E.art === 'neue-ebene') objekteAnzeigen(); aenderung();
    }); });
    // Karte
    $('#kZeichnen').addEventListener('click', function () { zeichnenSetzen(!UI.zeichnen); karteZeichnen(); });
    $('#kPlus').addEventListener('click', function () { K.svg.transition().duration(250).call(K.zoom.scaleBy, 1.8); });
    $('#kMinus').addEventListener('click', function () { K.svg.transition().duration(250).call(K.zoom.scaleBy, 1 / 1.8); });
    $('#kFit').addEventListener('click', fitAlle);
    $('#kWelt').addEventListener('click', function () { K.svg.transition().duration(450).call(K.zoom.transform, d3.zoomIdentity); });
    $('#zeitAn').addEventListener('change', function () {
      var start = $('#zeitJahr').value;
      if (this.checked && E.art === 'neue-ebene') { var sp = Themen.spanne({ objekte: E.ebene.objekte.filter(function (o) { return o.von != null; }) }); if (isFinite(sp.von)) start = Math.max(-3500, sp.von); }
      zeitSetzen(this.checked, start);
    });
    $('#zeitJahr').addEventListener('input', function () { zeitSetzen(true, this.value); });
    // gemeinsam
    binde('#bTitel', function (x) { E.titel = x.value; });
    binde('#bBegruendung', function (x) { E.begruendung = x.value; });
    $('#bBelegNeu').addEventListener('click', function () { E.belege.push({ zitat: '', url: '' }); listeAnzeigen($('#bBelege'), E.belege, BF); });
    // Ausgabe
    $('#aVorschau').addEventListener('click', function () {
      try { localStorage.setItem('cg.editor.vorschau', JSON.stringify(beitrag().ebene)); } catch (e) { toast('Vorschau nicht möglich: Der Browser erlaubt keinen lokalen Speicher.'); return; }
      window.open('app.html?modus=frei&vorschau=editor', '_blank', 'noopener');
    });
    $('#aGithub').addEventListener('click', function (ev) { if (this.classList.contains('aus')) { ev.preventDefault(); toast('Erst die offenen Punkte erledigen.'); } });
    $('#aLaden').addEventListener('click', function () { var b = beitrag(); herunterladen(Themen.dateiname(b).split('/').pop(), JSON.stringify(b, null, 2) + '\n', 'application/json'); });
    $('#aKopieren').addEventListener('click', function () { kopieren(JSON.stringify(beitrag(), null, 2)).then(function () { toast('JSON kopiert'); }, function () { toast('Kopieren nicht möglich'); }); });
    $('#aNeu').addEventListener('click', function () {
      if (!confirm('Den ganzen Entwurf verwerfen?')) return;
      E = leer(); AKT = -1; speichern(); formularFuellen(); zeitSetzen(false); startZeigen(); verlaufJetzt();
    });
    // KI-Assistent
    $('#btnKi').addEventListener('click', function () { $('#kiDialog').showModal(); kiSeite(1); kiPromptAktualisieren(); });
    $('#kiZu').addEventListener('click', function () { $('#kiDialog').close(); });
    $$('[data-ki]').forEach(function (b) { b.addEventListener('click', function () { kiSeite(+b.getAttribute('data-ki')); }); });
    ['#kiThema', '#kiDaten', '#kiWuensche'].forEach(function (s) { $(s).addEventListener('input', kiPromptAktualisieren); });
    $$('input[name=kiModus]').forEach(function (r) { r.addEventListener('change', kiPromptAktualisieren); });
    $('#kiDatei').addEventListener('click', function () { dateiWaehlen('kiDaten'); });
    $('#kiAntwortDatei').addEventListener('click', function () { dateiWaehlen('kiAntwort'); });
    $('#kiKopieren').addEventListener('click', function () {
      kopieren($('#kiPrompt').value).then(function () { toast('✦ Prompt kopiert – jetzt in die KI deiner Wahl einfügen'); $('#kiKopieren').textContent = '✓ Kopiert'; setTimeout(function () { $('#kiKopieren').textContent = 'Prompt kopieren'; }, 2000); },
        function () { $('#kiPrompt').select(); toast('Bitte mit Strg+C kopieren'); });
    });
    $('#kiSpeichern').addEventListener('click', function () { herunterladen('chronoglobe-prompt.txt', $('#kiPrompt').value, 'text/plain'); });
    $('#kiWeiter').addEventListener('click', function () { kiSeite(2); });
    var kiT = null; $('#kiAntwort').addEventListener('input', function () { clearTimeout(kiT); kiT = setTimeout(kiAntwortPruefen, 250); });
    $('#kiErsetzen').addEventListener('click', function () {
      if (E.art && (E.ebene.objekte.length || E.vorschlag.text) && !confirm('Den aktuellen Entwurf durch die Antwort der KI ersetzen? (Strg+Z macht es rückgängig)')) return;
      kiUebernehmen(false);
    });
    $('#kiAnhaengen').addEventListener('click', function () { kiUebernehmen(true); });
    // Datei-Auswahl
    $('#datei').addEventListener('change', function () {
      var f = this.files && this.files[0]; if (!f) return;
      if (f.size > 25e6) { toast('Die Datei ist größer als 25 MB.'); return; }
      var r = new FileReader(); r.onload = function () { dateiGelesen(f.name, String(r.result)); }; r.readAsText(f);
    });
    // Tastatur
    document.addEventListener('keydown', function (ev) {
      var feld = /^(INPUT|TEXTAREA|SELECT)$/.test(ev.target.tagName) || $('#kiDialog').open;
      if ((ev.ctrlKey || ev.metaKey) && !feld && (ev.key === 'z' || ev.key === 'Z')) { ev.preventDefault(); verlaufGehe(ev.shiftKey ? 1 : -1); }
      else if ((ev.ctrlKey || ev.metaKey) && !feld && ev.key === 'y') { ev.preventDefault(); verlaufGehe(1); }
      else if (ev.key === 'Escape' && !$('#kiDialog').open && !feld) { zeichnenSetzen(!UI.zeichnen); karteZeichnen(); }
    });
  }
  function formularFuellen(behalteAkt) {
    $('#zBereich').value = E.ziel.bereich;
    $('#vText').value = E.vorschlag.text; $('#vName').value = E.vorschlag.felder.name || '';
    $('#vVon').value = E.vorschlag.felder.von == null ? '' : E.vorschlag.felder.von; $('#vBis').value = E.vorschlag.felder.bis == null ? '' : E.vorschlag.felder.bis;
    $('#vGeoTyp').value = E.vorschlag.geometrie ? E.vorschlag.geometrie.typ : '';
    $('#eName').value = E.ebene.name; $('#eFarbe').value = E.ebene.farbe; $('#eBeschreibung').value = E.ebene.beschreibung; $('#eHinweis').value = E.ebene.hinweis;
    $('#bTitel').value = E.titel; $('#bBegruendung').value = E.begruendung;
    listeAnzeigen($('#eQuellen'), E.ebene.quellen, QF); listeAnzeigen($('#bBelege'), E.belege, BF);
    if (!behalteAkt || AKT >= E.ebene.objekte.length) AKT = E.ebene.objekte.length ? 0 : -1;
    $('#eMeta').open = !E.ebene.name || !E.ebene.beschreibung;
    ebeneKopf(); jahrTexte();
  }

  /* ---------- Start ---------- */
  Promise.all([json('data/reiche.json'), json('data/handel.json'), json('data/texte.json'), json('data/vignetten.json'), json('data/land.json'),
    json('data/ebenen/index.json').catch(function () { return { ebenen: [] }; }), json('data/fruehe_reiche.json').catch(function () { return null; })]).then(function (r) {
    D.reiche = r[0]; D.handel = r[1]; D.texte = r[2]; D.vignetten = r[3]; D.land = r[4]; D.ebenen = {}; D.frueh = r[6];
    return Promise.all((r[5].ebenen || []).map(function (e) { return json(e.datei).then(function (d) { D.ebenen[e.id] = d; }, function () {}); }));
  }).then(function () {
    E = laden();
    verdrahten(); karteEinrichten(); formularFuellen(); zeichnenSetzen(true);
    // Aufruf aus einem Infofenster des Globus: editor.html?ziel=<bereich>:<id>
    var z = new URLSearchParams(location.search).get('ziel');
    if (z) {
      var t = z.split(':'), bereich = t[0];
      if (Themen.BEREICHE[bereich]) {
        E.art = 'aenderung'; E.ziel = { bereich: bereich, datei: DATEI[bereich], id: t.slice(1).join(':'), name: '' };
        var x = auswahl(bereich).filter(function (a) { return a.wert === E.ziel.id; })[0];
        if (x) { E.ziel.name = x.text; E.ziel.datei = x.datei || DATEI[bereich]; }
        formularFuellen();
      }
    }
    if (E.art) artSetzen(E.art); else { startZeigen(); ausgabe(); }
    verlaufJetzt();
    if (E.art === 'aenderung' && REF) karteZeichnen(true); else if (E.art === 'neue-ebene') setTimeout(fitAlle, 100);
  }).catch(function (e) {
    console.error(e);
    document.body.insertBefore(el('p', 'ladefehler', 'Daten konnten nicht geladen werden (Seite über einen Webserver öffnen): ' + e.message), document.body.children[1]);
  });
})();
