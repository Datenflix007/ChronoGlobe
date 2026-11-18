/* Schülertexte: Darstellung für Infokarte (index.html) und Lehrkraft-Ansicht (lehrkraft.html).
   Fußnoten nach dem Merkblatt „Zitation“ (FSU Jena, VfZ): erste Nennung Vollbeleg, danach Kurztitel,
   „Vgl.“ bei sinngemäßer Übernahme, „Ebd.“ bei gleichem Titel wie in der vorigen Anmerkung.
   Abhängigkeit: d3 (Kartenskizzen). */
(function () {
  'use strict';

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

  /* Fußnoten einer Textfassung: Zeichen [n] in Reihenfolge des ersten Auftretens neu nummerieren */
  function nummerieren(teile) {
    var order = [], map = {};
    teile.forEach(function (s) {
      (s || '').replace(/\[(\d+)\]/g, function (_, n) { n = +n; if (!map[n]) { order.push(n); map[n] = order.length; } return ''; });
    });
    return { order: order, map: map };
  }
  function istDeutsch(s) { return /\b(der|die|das|und|nahm|zu)\b/.test(s); }

  /* Anmerkungstext nach Merkblatt */
  function anmerkungen(fussnoten, order, lit) {
    var byN = {}; fussnoten.forEach(function (f) { byN[f.n] = f; });
    var genannt = {}, vorher = null;
    return order.map(function (n) {
      var f = byN[n], L = lit[f.q], ort, titel, t;
      if (!f || !L) return '[Fußnote ' + n + ' fehlt]';
      if (L.antik) { ort = f.s; vorher = f.q; return L.kurz + ' ' + ort + '.'; }
      ort = f.s === 'online' ? 'Abschn. „' + (f.abschnitt || '') + '“' : 'S. ' + f.s;
      var url = '';
      if (vorher === f.q) titel = 'ebd.';
      else if (genannt[f.q]) titel = L.kurz;
      else {   // Vollbeleg: Seitenangabe vor die URL setzen
        var i = L.voll.indexOf(' (URL:');
        titel = i < 0 ? L.voll : L.voll.slice(0, i); url = i < 0 ? '' : L.voll.slice(i);
      }
      ort += url;
      genannt[f.q] = 1; vorher = f.q;
      if (f.art === 'vgl') {
        t = 'Vgl. ' + titel + ', ' + ort + (f.zusatz ? ' (' + f.zusatz + ')' : '') + '.';
      } else if (f.art === 'zitat' && f.zusatz && /zit\. nach/.test(f.zusatz)) {
        t = f.zusatz + ' ' + titel + ', ' + ort + '.';
      } else {
        t = titel.charAt(0).toUpperCase() + titel.slice(1) + ', ' + ort + (f.art === 'zitat' && !istDeutsch(f.beleg) ? ' [Übers. d. Verf.]' : '') + '.';
      }
      return t.replace(/^ebd\./, 'Ebd.').replace(/^Vgl\. ebd\./, 'Vgl. ebd.');
    });
  }

  /* Fließtext mit hochgestellten Fußnotenzeichen */
  function absatz(text, map, cls) {
    var p = el('p', cls || null);
    var re = /\[(\d+)\]/g, last = 0, m;
    while ((m = re.exec(text))) {
      p.appendChild(document.createTextNode(text.slice(last, m.index)));
      var s = el('sup', 'fnz', String(map[+m[1]] || '?')); s.title = 'Anmerkung ' + (map[+m[1]] || '?'); p.appendChild(s);
      last = re.lastIndex;
    }
    p.appendChild(document.createTextNode(text.slice(last)));
    return p;
  }

  /* ---------- Kartenskizzen (eigene Darstellung, Küstenlinien Natural Earth) ---------- */
  function skizze(typ, D) {
    var W = 520, H = 300, NS = 'http://www.w3.org/2000/svg';
    var svg = d3.select(document.createElementNS(NS, 'svg')).attr('viewBox', '0 0 ' + W + ' ' + H).attr('class', 'skizze').attr('role', 'img');
    var ext = { netz: [[28, 18], [118, 48]], etappen: [[30, 26], [100, 46]], monsun: [[28, 2], [82, 30]], zhenghe: [[36, -10], [124, 34]] }[typ];
    var proj = d3.geoEquirectangular().fitExtent([[6, 6], [W - 6, H - 6]], { type: 'MultiPoint', coordinates: [ext[0], [ext[1][0], ext[0][1]], ext[1], [ext[0][0], ext[1][1]]] });
    var path = d3.geoPath(proj);
    svg.append('rect').attr('width', W).attr('height', H).attr('fill', '#cfe3ea');
    svg.append('path').attr('d', path(D.land)).attr('fill', '#efe3c2').attr('stroke', '#a99363').attr('stroke-width', 0.6);
    function linie(pts, col, w, dash, op) {
      svg.append('path').attr('d', path({ type: 'LineString', coordinates: pts })).attr('fill', 'none').attr('stroke', col)
        .attr('stroke-width', w).attr('stroke-dasharray', dash || null).attr('stroke-opacity', op == null ? 1 : op).attr('stroke-linecap', 'round');
    }
    function ort(lng, lat, name, dx, dy) {
      var p = proj([lng, lat]); if (!p) return;
      svg.append('circle').attr('cx', p[0]).attr('cy', p[1]).attr('r', 3).attr('fill', '#2b2110');
      svg.append('text').attr('x', p[0] + (dx || 5)).attr('y', p[1] + (dy || -5)).attr('font-size', 11).attr('font-family', 'Georgia, serif')
        .attr('fill', '#2b2110').attr('stroke', '#f5ecd2').attr('stroke-width', 3).attr('paint-order', 'stroke').text(name);
    }
    function pfeil(a, b, col, txt) {
      var p = proj(a), q = proj(b), id = 'pf' + Math.random().toString(36).slice(2);
      svg.append('defs').append('marker').attr('id', id).attr('viewBox', '0 0 10 10').attr('refX', 8).attr('refY', 5).attr('markerWidth', 6).attr('markerHeight', 6)
        .attr('orient', 'auto').append('path').attr('d', 'M0,0 L10,5 L0,10 z').attr('fill', col);
      svg.append('path').attr('d', 'M' + p + ' Q' + ((p[0] + q[0]) / 2) + ',' + ((p[1] + q[1]) / 2 - 18) + ' ' + q).attr('fill', 'none').attr('stroke', col).attr('stroke-width', 2.5).attr('marker-end', 'url(#' + id + ')');
      svg.append('text').attr('x', (p[0] + q[0]) / 2).attr('y', (p[1] + q[1]) / 2 - 22).attr('text-anchor', 'middle').attr('font-size', 11).attr('font-weight', 700)
        .attr('fill', col).attr('stroke', '#f5ecd2').attr('stroke-width', 3).attr('paint-order', 'stroke').text(txt);
    }
    var H_ = D.handel, K = H_ && H_.karawanen;
    if (typ === 'netz' || typ === 'etappen') {
      H_.verbindungen.filter(function (v) { return v.art === 'land'; }).forEach(function (v) {
        linie(v.pfad, '#8a4b12', typ === 'netz' ? 3 : 2, v.belegt === 'umstritten' ? '2 5' : null, typ === 'netz' ? 1 : 0.35);
      });
      K.etappen.forEach(function (e) { linie(e.pfad, typ === 'netz' ? '#c58b2a' : '#8a4b12', typ === 'netz' ? 1.5 : 3, typ === 'netz' ? '4 3' : null); });
      var lage = { palmyra: [-46, -6], ktesiphon: [4, 14], merw: [-36, 14], samarkand: [-24, -8], kaschgar: [4, 14], turfan: [4, -6], dunhuang: [4, 14] };
      K.knoten.forEach(function (n) { var l = lage[n.id]; if (l) ort(n.lng, n.lat, n.name.replace(/ \(.*\)/, ''), l[0], l[1]); else { var p = proj([n.lng, n.lat]); if (p) svg.append('circle').attr('cx', p[0]).attr('cy', p[1]).attr('r', 2.5).attr('fill', '#2b2110'); } });
    } else if (typ === 'monsun') {
      H_.verbindungen.filter(function (v) { return v.art === 'see'; }).forEach(function (v) { linie(v.pfad, '#155f86', 2.5, '6 4', 0.8); });
      pfeil([52, 13], [72, 14], '#b0401f', 'Sommer: Hinfahrt');
      pfeil([70, 7], [52, 7.5], '#2d6aa0', 'Winter: Rückfahrt');
      ort(35.47, 23.91, 'Berenike'); ort(32.82, 26.0, 'Koptos', -48, -4); ort(76.2, 10.15, 'Muziris', 5, 12);
    } else if (typ === 'zhenghe') {
      D.zhenghe.verbindungen.forEach(function (v, i) { linie(v.pfad, ['#7cb342', '#43a047', '#2e7d32', '#00897b', '#26a69a', '#558b2f', '#1b5e20'][i % 7], 1.6, null, 0.85); });
      [['nanjing', 4, -5], ['malakka', 5, 12], ['calicut', -48, 12], ['hormuz', 5, -5], ['mogadischu', 5, 4], ['malindi', 5, 4]].forEach(function (x) {
        var o = D.zhenghe.orte.filter(function (y) { return y.id === x[0]; })[0]; if (o) ort(o.lng, o.lat, o.name.replace(/ \(.*\)/, ''), x[1], x[2]);
      });
    }
    return svg.node();
  }

  /* ---------- Gesamtdarstellung eines Textes ---------- */
  function render(box, T, lit, D, opt) {
    opt = opt || {};
    var niv = opt.niveau || 'B';
    var teile = [T.niveaus[niv]];
    (T.steckbrief || []).forEach(function (x) { if (x.fn) teile.push('[' + x.fn + ']'); });
    if (T.vignette) teile.push(T.vignette.text);
    var nm = nummerieren(teile);

    if (T.steckbrief) {
      var sb = el('div', 'tx-steckbrief'); sb.appendChild(el('div', 'tx-h', 'Steckbrief'));
      var dl = el('dl');
      T.steckbrief.forEach(function (x) { dl.appendChild(el('dt', null, x.k)); var dd = absatz(x.v + (x.fn ? '[' + x.fn + ']' : ''), nm.map); var d2 = el('dd'); while (dd.firstChild) d2.appendChild(dd.firstChild); dl.appendChild(d2); });
      sb.appendChild(dl); box.appendChild(sb);
    }
    box.appendChild(absatz(T.niveaus[niv], nm.map, 'tx-text'));
    if (T.vignette) {
      var vg = el('div', 'tx-vignette'); vg.appendChild(el('div', 'tx-h', 'Erzählung aus Sicht eines Seemanns'));
      vg.appendChild(el('p', 'tx-fiktion', T.vignette.hinweis));
      vg.appendChild(absatz(T.vignette.text, nm.map)); box.appendChild(vg);
    }
    if (T.leitfrage) box.appendChild(el('p', 'tx-leitfrage', T.leitfrage));

    var fig = el('figure', 'tx-fig'); fig.appendChild(skizze(T.abbildung.skizze, D));
    var cap = el('figcaption'); cap.appendChild(el('b', null, T.abbildung.titel + '. ')); cap.appendChild(document.createTextNode(T.abbildung.text + ' Lizenz: ' + T.abbildung.lizenz + '.'));
    fig.appendChild(cap); box.appendChild(fig);

    var gl = el('div', 'tx-glossar'); gl.appendChild(el('div', 'tx-h', 'Glossar'));
    var gdl = el('dl'); T.glossar.forEach(function (g) { gdl.appendChild(el('dt', null, g.wort)); gdl.appendChild(el('dd', null, g.erklaerung)); });
    gl.appendChild(gdl); box.appendChild(gl);

    T.quellenauszug.forEach(function (q) {
      var qa = el('div', 'tx-quelle'); qa.appendChild(el('div', 'tx-h', 'Quelle: ' + q.titel));
      qa.appendChild(el('blockquote', null, q.text)); qa.appendChild(el('p', 'tx-nachweis', q.nachweis));
      if (q.hinweis) qa.appendChild(el('p', 'tx-qhinweis', q.hinweis)); box.appendChild(qa);
    });

    var wb = el('div', 'tx-woher'); wb.appendChild(el('div', 'tx-h', 'Woher wissen wir das?'));
    var p1 = el('p'); p1.appendChild(el('b', null, 'Quellen: ')); p1.appendChild(document.createTextNode(T.woher.quellen)); wb.appendChild(p1);
    var p2 = el('p'); p2.appendChild(el('b', null, 'Was wir nicht wissen: ')); p2.appendChild(document.createTextNode(T.woher.nichtwissen)); wb.appendChild(p2);
    box.appendChild(wb);

    var au = el('div', 'tx-auftraege'); au.appendChild(el('div', 'tx-h', 'Arbeitsaufträge'));
    var ol = el('ol'); T.auftraege.forEach(function (a) { ol.appendChild(el('li', null, a)); }); au.appendChild(ol); box.appendChild(au);

    var an = el('div', 'tx-anm'); an.appendChild(el('div', 'tx-h', 'Anmerkungen'));
    var aol = el('ol'); anmerkungen(T.fussnoten, nm.order, lit).forEach(function (t) { aol.appendChild(el('li', null, t)); });
    an.appendChild(aol); box.appendChild(an);
  }

  window.Texte = { render: render, anmerkungen: anmerkungen, nummerieren: nummerieren, skizze: skizze };
})();
