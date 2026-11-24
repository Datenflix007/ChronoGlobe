/* ChronoGlobe · Landingpage: Galerie (tafelbilder/index.json), Session erstellen/fortsetzen, Session beitreten */
(function () {
  'use strict';
  var S = window.CGSession, lokal = S && S.lokal ? '&sync=lokal' : '';
  function $(s) { return document.querySelector(s); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function json(u) { var v = window.cgUrl ? cgUrl(u) : u; return fetch(v, v === u ? { cache: 'no-cache' } : {}).then(function (r) { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); }); }

  /* Galerie und Auswahl */
  var TB = [];
  json('tafelbilder/index.json').then(function (ix) {
    return Promise.all(ix.tafelbilder.map(function (e) {
      return json('tafelbilder/' + e.id + '/tafelbild.json').then(function (t) { t.ordner = 'tafelbilder/' + e.id + '/'; return t; }, function (err) { console.warn(err); return null; });
    }));
  }).then(function (liste) {
    TB = liste.filter(Boolean);
    var g = $('#galerie'); g.innerHTML = '';
    TB.forEach(function (t) {
      var a = el('a', 'karte'); a.href = 'app.html?tafelbild=' + encodeURIComponent(t.id);
      if (t.vorschaubild) { var img = el('img'); img.src = t.ordner + t.vorschaubild; img.alt = ''; img.loading = 'lazy'; a.appendChild(img); }
      var tx = el('div', 'ktext'); tx.appendChild(el('b', null, t.titel)); if (t.beschreibung) tx.appendChild(el('span', null, t.beschreibung));
      a.appendChild(tx); g.appendChild(a);
      var o = el('option', null, t.titel); o.value = t.id; $('#tbWahl').appendChild(o);
    });
    if (!TB.length) g.appendChild(el('p', 'klein', 'Noch keine Tafelbilder eingetragen (tafelbilder/index.json).'));
  }).catch(function (e) { $('#galerie').innerHTML = ''; $('#galerie').appendChild(el('p', 'klein', 'Tafelbilder konnten nicht geladen werden: ' + e.message)); });

  /* Sessions nur mit eingerichtetem Supabase (oder ?sync=lokal zum Testen) */
  (S ? S.konfiguriert() : Promise.resolve(false)).then(function (ok) {
    document.querySelectorAll('.nur-mit-db').forEach(function (x) { x.hidden = !ok; });
    document.querySelectorAll('.hinweis-db').forEach(function (x) { x.hidden = !!ok; });
    if (ok) alteZeigen();
  });

  function alteZeigen() {
    var l = S.gespeicherte().filter(function (e) { return !!e.lokal === !!S.lokal; }), ul = $('#alteListe'); ul.innerHTML = '';
    $('#alteSessions').hidden = !l.length;
    l.forEach(function (e) {
      var li = el('li'), a = el('a', 'knopf', e.code); a.href = S.lehrerLink(e.code);
      li.appendChild(a); li.appendChild(el('span', 'klein', e.titel + ' · ' + new Date(e.erstellt).toLocaleDateString('de-DE')));
      var x = el('button', 'knopf klein-knopf', 'Beenden'); x.type = 'button'; x.title = 'Session sofort löschen';
      x.addEventListener('click', function () {
        if (!confirm('Session ' + e.code + ' beenden? Sie wird sofort gelöscht.')) return;
        S.beenden(e.code).then(alteZeigen, function () { S.vergessen(e.code); alteZeigen(); });
      });
      li.appendChild(x); ul.appendChild(li);
    });
  }

  $('#btnStarten').addEventListener('click', function () {
    var id = $('#tbWahl').value, t = TB.filter(function (x) { return x.id === id; })[0], b = this;
    if (!id) return;
    b.disabled = true; b.textContent = 'Wird gestartet …';
    S.erstellen(id, t ? t.titel : id).then(function (e) {
      $('#neueSession').hidden = false;
      $('#nsCode').textContent = e.code; $('#nsToken').textContent = e.token;
      var link = S.schuelerLink(e.code); $('#nsLink').textContent = link; $('#nsLink').href = link;
      $('#nsOeffnen').href = S.lehrerLink(e.code);
      S.qr($('#nsQr'), link);
      alteZeigen();
    }, function (err) { alert('Session konnte nicht gestartet werden: ' + (err.message || err)); })
      .then(function () { b.disabled = false; b.textContent = 'Session starten'; });
  });

  $('#beitreten').addEventListener('submit', function (ev) {
    ev.preventDefault();
    var c = $('#codeFeld').value.toUpperCase().replace(/[^A-Z0-9]/g, '');
    if (c.length < 4) { $('#codeFeld').focus(); return; }
    location.href = 'app.html?session=' + c + '&rolle=schueler' + lokal;
  });
})();
