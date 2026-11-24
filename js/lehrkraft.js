/* Lehrkraft-Ansicht der Schülertexte (aus lehrkraft.html ausgelagert, damit die CSP keine Inline-Skripte braucht) */
(function () {
  function load(u) { return fetch(window.cgUrl ? cgUrl(u) : u).then(function (r) { if (!r.ok) throw new Error(u); return r.json(); }); }
  function el(t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
  Promise.all(['data/texte.json', 'data/literatur.json', 'data/land.json', 'data/handel.json', 'data/zhenghe.json'].map(load)).then(function (r) {
    var T = r[0].texte, LIT = {}; r[1].titel.forEach(function (t) { LIT[t.id] = t; });
    var land = r[2].type === 'Feature' ? r[2] : { type: 'Feature', geometry: r[2].geometry || r[2] };
    var D = { land: land, handel: r[3], zhenghe: r[4] }, box = document.getElementById('texte'), nav = document.getElementById('nav');
    T.forEach(function (t) {
      var a = el('a', null, t.titel); a.href = '#' + t.id; nav.appendChild(a);
      var s = el('section', 'text'); s.id = t.id; s.style.setProperty('--c', t.farbe);
      s.appendChild(el('h2', null, t.titel));
      var niv = el('div', 'niv');
      ['A', 'B', 'C'].forEach(function (n) {
        var d = el('div'); d.appendChild(el('h3', null, 'Niveau ' + n));
        var txt = t.niveaus[n], nm = Texte.nummerieren([txt]);
        d.appendChild(el('div', 'wz', txt.replace(/\[\d+\]/g, '').split(/\s+/).filter(Boolean).length + ' Wörter'));
        var p = el('p'); txt.split(/(\[\d+\])/).forEach(function (x) { var m = /^\[(\d+)\]$/.exec(x); if (m) p.appendChild(el('sup', 'fnz', String(nm.map[+m[1]]))); else p.appendChild(document.createTextNode(x)); });
        d.appendChild(p);
        var ol = el('ol'); Texte.anmerkungen(t.fussnoten, nm.order, LIT).forEach(function (x) { ol.appendChild(el('li', null, x)); }); d.appendChild(ol);
        niv.appendChild(d);
      });
      s.appendChild(niv);
      // Gemeinsame Teile (Steckbrief, Erzählung, Abbildung, Glossar …): einmal mit Niveau B darstellen
      var g = el('div');
      Texte.render(g, t, LIT, D, { niveau: 'B' });
      var txtB = g.querySelector('.tx-text'); if (txtB) txtB.remove();
      s.appendChild(el('div', 'tx-h', 'Gemeinsame Bausteine (Anmerkungen hier zur Fassung B)'));
      s.appendChild(g);
      box.appendChild(s);
    });
    var a2 = el('a', null, 'Literatur'); a2.href = '#literatur'; nav.appendChild(a2);
    var tb = document.getElementById('litbody');
    r[1].titel.slice().sort(function (a, b) { return a.verz.localeCompare(b.verz, 'de'); }).forEach(function (t) {
      var tr = el('tr'); tr.appendChild(el('td', null, t.verz)); tr.appendChild(el('td', null, t.typ)); tr.appendChild(el('td', null, t.lizenz));
      var ab = el('td', t.ablage === 'lokal' ? 'lok' : 'ok', t.ablage === 'lokal' ? 'lokal' : 'öffentlich'); tr.appendChild(ab); tb.appendChild(tr);
    });
  }).catch(function (e) { document.getElementById('texte').textContent = 'Daten konnten nicht geladen werden (bitte über einen Webserver öffnen): ' + e.message; });
})();
