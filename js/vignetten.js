/* Vignetten-Engine: Inhalte der Schriftrolle je Reich (Text, Bild, Musik, Video, Quiz mit Rückmeldung).
   Daten: data/vignetten.json (Format: docs/VIGNETTEN.md). Keine Abhängigkeiten.
   Aufruf: Vignetten.render(box, cfg, ctx)  ctx = { reich, name, farbe }
   Fortschritt (Quiz) wird nur im Speicher der geöffneten Seite gehalten, nichts wird übertragen oder gespeichert. */
(function () {
  'use strict';

  var PLATZHALTER = 5;                 // so viele leere Vignetten, wenn für ein Reich nichts eingetragen ist
  var FORTSCHRITT = {};                // reich -> vignetten-index -> block-index -> true/false
  var ANSICHT = {};                    // reich -> 'liste' | index der geöffneten Vignette
  var uid = 0;

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function add(p, c) { p.appendChild(c); return c; }
  function mischen(a) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
  function norm(s) { return String(s == null ? '' : s).trim().toLowerCase().replace(/\s+/g, ' ').replace(/[.,;:!?]+$/, ''); }
  function istLeer(v) { return !v || !(v.bloecke && v.bloecke.length); }
  function istQuiz(b) { return !!QUIZ[b.typ]; }

  /* Einfache Auszeichnung im Text: **fett**, *kursiv*, Absätze durch Leerzeile */
  function inline(p, text) {
    var re = /(\*\*([^*]+)\*\*|\*([^*]+)\*)/g, last = 0, m;
    text = String(text || '');
    while ((m = re.exec(text))) {
      p.appendChild(document.createTextNode(text.slice(last, m.index)));
      p.appendChild(el(m[2] != null ? 'b' : 'i', null, m[2] != null ? m[2] : m[3]));
      last = re.lastIndex;
    }
    p.appendChild(document.createTextNode(text.slice(last)));
    return p;
  }
  function absaetze(box, text) {
    String(text || '').split(/\n\s*\n/).forEach(function (t) { if (t.trim()) add(box, inline(el('p'), t.trim())); });
    return box;
  }
  function lizenz(fig, b) {
    if (!b.unterschrift && !b.lizenz && !b.titel) return;
    var cap = add(fig, el('figcaption'));
    if (b.titel) add(cap, el('b', null, b.titel + (b.unterschrift ? '. ' : '')));
    if (b.unterschrift) inline(cap, b.unterschrift);
    if (b.lizenz) add(cap, el('span', 'vg-liz', ' ' + b.lizenz));
  }
  function fehlt(box, art, src) {
    box.innerHTML = '';
    add(box, el('div', 'vg-fehlt', art + ' fehlt noch' + (src ? ': ' + src : '') + '.'));
  }

  /* ---------- Inhaltsblöcke ---------- */
  var BLOCK = {
    text: function (b) { return absaetze(el('div', 'vg-text'), b.text); },
    merke: function (b) {
      var d = el('div', 'vg-merke'); add(d, el('div', 'vg-h', b.titel || 'Merke')); return absaetze(d, b.text);
    },
    erzaehlung: function (b) {   // GRUNDREGELN 9: Erfundenes kennzeichnen
      var d = el('div', 'vg-erz'); add(d, el('div', 'vg-h', b.titel || 'Erzählung'));
      add(d, el('p', 'vg-fiktion', b.hinweis || 'Diese Geschichte ist erfunden. Was darin über die Zeit erzählt wird, ist aber belegt.'));
      return absaetze(d, b.text);
    },
    quelle: function (b) {
      var d = el('div', 'vg-quelle'); add(d, el('div', 'vg-h', 'Quelle' + (b.titel ? ': ' + b.titel : '')));
      add(d, el('blockquote', null, b.text)); if (b.nachweis) add(d, el('p', 'vg-nachweis', b.nachweis)); return d;
    },
    bild: function (b) {
      var fig = el('figure', 'vg-bild');
      if (!b.src) { fehlt(fig, 'Bild'); return fig; }
      var img = add(fig, el('img')); img.loading = 'lazy'; img.alt = b.alt || ''; img.src = b.src;
      img.addEventListener('error', function () { fehlt(fig, 'Bild', b.src); });
      lizenz(fig, b); return fig;
    },
    audio: function (b) {
      var fig = el('figure', 'vg-audio');
      if (!b.src) { fehlt(fig, 'Tonaufnahme'); return fig; }
      var a = add(fig, el('audio')); a.controls = true; a.preload = 'none'; a.src = b.src;
      a.addEventListener('error', function () { fehlt(fig, 'Tonaufnahme', b.src); });
      lizenz(fig, b); return fig;
    },
    video: function (b) {
      var fig = el('figure', 'vg-video');
      if (!b.src) { fehlt(fig, 'Video'); return fig; }
      var v = add(fig, el('video')); v.controls = true; v.preload = 'metadata'; v.playsInline = true;
      if (b.poster) v.poster = b.poster;
      var s = add(v, el('source')); s.src = b.src;
      if (b.untertitel) { var t = add(v, el('track')); t.kind = 'subtitles'; t.srclang = 'de'; t.label = 'Deutsch'; t.src = b.untertitel; t.default = true; }
      s.addEventListener('error', function () { fehlt(fig, 'Video', b.src); });
      lizenz(fig, b); return fig;
    }
  };

  /* ---------- Quiz ----------
     Jeder Typ liefert { body, pruefen() -> {ok, leer}, loesen(), reset() }.
     Gemeinsame Felder: frage, tipp, feedback {richtig, falsch}, erklaerung, punkte (unbenutzt, vorbereitet). */
  function opt(name, type, text, wert) {
    var l = el('label', 'vg-opt'), i = add(l, el('input')); i.type = type; i.name = name; i.value = wert;
    add(l, inline(el('span'), text)); return { label: l, input: i };
  }
  function markieren(node, cls) { node.classList.remove('ok', 'bad', 'miss'); if (cls) node.classList.add(cls); }
  var QUIZ = {
    /* Eine richtige Antwort: antworten [{text, richtig, feedback}] */
    einfach: function (b) {
      var name = 'vgq' + (++uid), body = el('div', 'vg-opts'), los = b.mischen === false ? b.antworten : mischen(b.antworten);
      var items = los.map(function (a, i) { var o = opt(name, 'radio', a.text, i); o.a = a; add(body, o.label); return o; });
      return {
        body: body,
        pruefen: function () {
          var sel = items.filter(function (o) { return o.input.checked; })[0];
          if (!sel) return { leer: true };
          items.forEach(function (o) { markieren(o.label, o === sel ? (o.a.richtig ? 'ok' : 'bad') : null); });
          return { ok: !!sel.a.richtig, einzel: sel.a.feedback };
        },
        loesen: function () { items.forEach(function (o) { o.input.checked = !!o.a.richtig; markieren(o.label, o.a.richtig ? 'ok' : null); }); },
        reset: function () { items.forEach(function (o) { o.input.checked = false; markieren(o.label); }); },
        inputs: items.map(function (o) { return o.input; })
      };
    },
    /* Mehrere richtige Antworten: wie einfach, mehrere mit richtig: true */
    mehrfach: function (b) {
      var name = 'vgq' + (++uid), body = el('div', 'vg-opts'), los = b.mischen === false ? b.antworten : mischen(b.antworten);
      add(body, el('p', 'vg-anw', 'Mehrere Antworten können richtig sein.'));
      var items = los.map(function (a, i) { var o = opt(name, 'checkbox', a.text, i); o.a = a; add(body, o.label); return o; });
      return {
        body: body,
        pruefen: function () {
          if (!items.some(function (o) { return o.input.checked; })) return { leer: true };
          var ok = true, fb = [];
          items.forEach(function (o) {
            var c = o.input.checked, r = !!o.a.richtig;
            if (c && r) markieren(o.label, 'ok'); else if (c) { markieren(o.label, 'bad'); ok = false; if (o.a.feedback) fb.push(o.a.feedback); }
            else if (r) { markieren(o.label, null); ok = false; } else markieren(o.label, null);
          });
          var fehlen = items.filter(function (o) { return o.a.richtig && !o.input.checked; }).length;
          return { ok: ok, einzel: fb.join(' '), zusatz: fehlen && !fb.length ? 'Es fehlt noch mindestens eine richtige Antwort.' : '' };
        },
        loesen: function () { items.forEach(function (o) { o.input.checked = !!o.a.richtig; markieren(o.label, o.a.richtig ? 'ok' : null); }); },
        reset: function () { items.forEach(function (o) { o.input.checked = false; markieren(o.label); }); },
        inputs: items.map(function (o) { return o.input; })
      };
    },
    /* Richtig oder falsch: aussagen [{text, richtig: true|false, feedback}] */
    wahrfalsch: function (b) {
      var body = el('div', 'vg-wf'), rows = (b.mischen ? mischen(b.aussagen) : b.aussagen).map(function (a) {
        var name = 'vgq' + (++uid), row = add(body, el('div', 'vg-wfrow'));
        add(row, inline(el('span', 'vg-wft'), a.text));
        var w = opt(name, 'radio', 'stimmt', 'w'), f = opt(name, 'radio', 'stimmt nicht', 'f');
        w.label.classList.add('vg-pill'); f.label.classList.add('vg-pill'); add(row, w.label); add(row, f.label);
        return { a: a, row: row, w: w.input, f: f.input };
      });
      return {
        body: body,
        pruefen: function () {
          if (rows.some(function (r) { return !r.w.checked && !r.f.checked; })) return { leer: true, text: 'Entscheide bei jeder Aussage: stimmt oder stimmt nicht?' };
          var ok = true, fb = [];
          rows.forEach(function (r) { var g = r.w.checked === !!r.a.richtig; markieren(r.row, g ? 'ok' : 'bad'); if (!g) { ok = false; if (r.a.feedback) fb.push(r.a.feedback); } });
          return { ok: ok, einzel: fb.join(' ') };
        },
        loesen: function () { rows.forEach(function (r) { r.w.checked = !!r.a.richtig; r.f.checked = !r.a.richtig; markieren(r.row, 'ok'); }); },
        reset: function () { rows.forEach(function (r) { r.w.checked = r.f.checked = false; markieren(r.row); }); },
        inputs: rows.reduce(function (a, r) { return a.concat([r.w, r.f]); }, [])
      };
    },
    /* Lückentext: text mit {{Lösung}} oder {{Lösung|andere Schreibweise}}; optional woerter (Wörterkasten) */
    luecke: function (b) {
      var body = el('div', 'vg-luecke'), p = add(body, el('p')), gaps = [], re = /\{\{([^}]+)\}\}/g, last = 0, m, t = String(b.text || '');
      while ((m = re.exec(t))) {
        inline(p, t.slice(last, m.index));
        var alts = m[1].split('|').map(function (s) { return s.trim(); }), inp = add(p, el('input', 'vg-gap'));
        inp.type = 'text'; inp.autocomplete = 'off'; inp.spellcheck = false; inp.size = Math.max(6, alts[0].length + 2);
        inp.setAttribute('aria-label', 'Lücke ' + (gaps.length + 1));
        gaps.push({ inp: inp, alts: alts }); last = re.lastIndex;
      }
      inline(p, t.slice(last));
      if (b.woerter && b.woerter.length) {
        var wk = add(body, el('div', 'vg-wk')); add(wk, el('span', 'vg-wkh', 'Wörterkasten:'));
        mischen(b.woerter).forEach(function (w) { add(wk, el('span', 'vg-wort', w)); });
      }
      return {
        body: body,
        pruefen: function () {
          if (gaps.some(function (g) { return !g.inp.value.trim(); })) return { leer: true, text: 'Fülle zuerst alle Lücken aus.' };
          var ok = true;
          gaps.forEach(function (g) { var r = g.alts.some(function (a) { return norm(a) === norm(g.inp.value); }); markieren(g.inp, r ? 'ok' : 'bad'); if (!r) ok = false; });
          return { ok: ok };
        },
        loesen: function () { gaps.forEach(function (g) { g.inp.value = g.alts[0]; markieren(g.inp, 'ok'); }); },
        reset: function () { gaps.forEach(function (g) { g.inp.value = ''; markieren(g.inp); }); },
        inputs: gaps.map(function (g) { return g.inp; })
      };
    },
    /* Zuordnen: paare [{links, rechts}] – zu jedem linken Begriff den passenden rechten auswählen */
    zuordnen: function (b) {
      var body = el('div', 'vg-zu'), rechts = mischen(b.paare.map(function (x) { return x.rechts; }));
      var rows = (b.mischen ? mischen(b.paare) : b.paare).map(function (x) {
        var row = add(body, el('div', 'vg-zurow')); add(row, inline(el('span', 'vg-zul'), x.links));
        add(row, el('span', 'vg-zupf', '→'));
        var s = add(row, el('select')); s.setAttribute('aria-label', 'Passendes zu „' + x.links + '“');
        add(s, el('option', null, 'bitte wählen …')).value = '';
        rechts.forEach(function (r) { add(s, el('option', null, r)).value = r; });
        return { x: x, row: row, s: s };
      });
      return {
        body: body,
        pruefen: function () {
          if (rows.some(function (r) { return !r.s.value; })) return { leer: true, text: 'Ordne zuerst jedem Begriff etwas zu.' };
          var ok = true;
          rows.forEach(function (r) { var g = r.s.value === r.x.rechts; markieren(r.row, g ? 'ok' : 'bad'); if (!g) ok = false; });
          return { ok: ok };
        },
        loesen: function () { rows.forEach(function (r) { r.s.value = r.x.rechts; markieren(r.row, 'ok'); }); },
        reset: function () { rows.forEach(function (r) { r.s.value = ''; markieren(r.row); }); },
        inputs: rows.map(function (r) { return r.s; })
      };
    },
    /* Reihenfolge: elemente in richtiger Reihenfolge eintragen, angezeigt wird gemischt */
    reihenfolge: function (b) {
      var body = el('div', 'vg-rf'), ol = add(body, el('ol')), richtig = b.elemente.slice(), cur = mischen(richtig), btns = [];
      if (cur.join('\u0001') === richtig.join('\u0001') && cur.length > 1) cur.push(cur.shift());
      function zeichnen() {
        ol.innerHTML = ''; btns = [];
        cur.forEach(function (t, i) {
          var li = add(ol, el('li')); add(li, inline(el('span', 'vg-rft'), t));
          [['↑', -1, 'nach oben'], ['↓', 1, 'nach unten']].forEach(function (d) {
            var bt = add(li, el('button', 'vg-rfb', d[0])); bt.type = 'button'; bt.title = '„' + t + '“ ' + d[2];
            bt.disabled = (i + d[1] < 0 || i + d[1] >= cur.length); btns.push(bt);
            bt.addEventListener('click', function () {
              var j = i + d[1], x = cur[i]; cur[i] = cur[j]; cur[j] = x; zeichnen();
              var nb = ol.children[j] && ol.children[j].querySelectorAll('button')[d[1] < 0 ? 0 : 1]; if (nb && !nb.disabled) nb.focus();
            });
          });
        });
      }
      zeichnen();
      return {
        body: body,
        pruefen: function () {
          var ok = true;
          Array.prototype.forEach.call(ol.children, function (li, i) { var g = cur[i] === richtig[i]; markieren(li, g ? 'ok' : 'bad'); if (!g) ok = false; });
          return { ok: ok };
        },
        loesen: function () { cur = richtig.slice(); zeichnen(); Array.prototype.forEach.call(ol.children, function (li) { markieren(li, 'ok'); }); },
        reset: function () { cur = mischen(richtig); zeichnen(); },
        inputs: function () { return btns; }
      };
    },
    /* Zahl / Jahr schätzen: antwort (Zahl), toleranz (± erlaubt), einheit (z. B. "n. Chr.") */
    zahl: function (b) {
      var body = el('div', 'vg-zahl'), inp = add(body, el('input', 'vg-gap'));
      inp.type = 'number'; inp.step = 'any'; inp.inputMode = 'numeric'; inp.setAttribute('aria-label', 'Deine Antwort');
      if (b.einheit) add(body, el('span', 'vg-einh', b.einheit));
      var tol = +b.toleranz || 0;
      return {
        body: body,
        pruefen: function () {
          if (inp.value === '') return { leer: true, text: 'Gib zuerst eine Zahl ein.' };
          var v = +inp.value, d = v - (+b.antwort), ok = Math.abs(d) <= tol;
          markieren(inp, ok ? 'ok' : 'bad');
          return { ok: ok, zusatz: ok ? '' : (d < 0 ? 'Deine Zahl ist zu klein.' : 'Deine Zahl ist zu groß.') };
        },
        loesen: function () { inp.value = b.antwort; markieren(inp, 'ok'); },
        reset: function () { inp.value = ''; markieren(inp); },
        inputs: [inp]
      };
    }
  };
  var QUIZ_NAME = { einfach: 'Wähle die richtige Antwort', mehrfach: 'Kreuze alle richtigen Antworten an', wahrfalsch: 'Stimmt das?', luecke: 'Fülle die Lücken', zuordnen: 'Ordne richtig zu', reihenfolge: 'Bringe in die richtige Reihenfolge', zahl: 'Schätze' };

  function quizBlock(b, melden) {
    var box = el('div', 'vg-quiz'), q;
    add(box, el('div', 'vg-h', b.titel || QUIZ_NAME[b.typ]));
    if (b.frage) add(box, inline(el('p', 'vg-frage'), b.frage));
    try { q = QUIZ[b.typ](b); } catch (e) { add(box, el('div', 'vg-fehlt', 'Quiz „' + b.typ + '“ ist unvollständig eingetragen: ' + e.message)); return box; }
    add(box, q.body);
    var bar = add(box, el('div', 'vg-qbar'));
    var bP = add(bar, el('button', 'vg-btn prim', 'Prüfen')), bN = add(bar, el('button', 'vg-btn', 'Nochmal')), bL = add(bar, el('button', 'vg-btn', 'Lösung zeigen'));
    var bT = b.tipp ? add(bar, el('button', 'vg-btn', 'Tipp')) : null;
    [bP, bN, bL, bT].forEach(function (x) { if (x) x.type = 'button'; });
    bN.hidden = bL.hidden = true;
    var fb = add(box, el('div', 'vg-fb')); fb.setAttribute('role', 'status'); fb.setAttribute('aria-live', 'polite');
    var versuche = 0;
    function inputs() { return typeof q.inputs === 'function' ? q.inputs() : (q.inputs || []); }
    function sperren(v) { inputs().forEach(function (i) { i.disabled = v; }); }
    function zeigen(cls, kopf, texte) {
      fb.className = 'vg-fb ' + cls; fb.innerHTML = '';
      add(fb, el('b', null, kopf));
      texte.filter(Boolean).forEach(function (t) { add(fb, inline(el('p'), t)); });
    }
    bP.addEventListener('click', function () {
      var r = q.pruefen();
      if (r.leer) { zeigen('info', 'Noch nicht fertig.', [r.text || 'Wähle zuerst eine Antwort aus.']); return; }
      versuche++;
      var fbk = b.feedback || {};
      if (r.ok) {
        zeigen('ok', 'Richtig!', [r.einzel, fbk.richtig, b.erklaerung]);
        sperren(true); bP.hidden = true; bL.hidden = true; bN.hidden = false;
      } else {
        zeigen('bad', versuche > 1 ? 'Leider noch nicht richtig.' : 'Noch nicht ganz.', [r.einzel, r.zusatz, fbk.falsch || 'Schau dir die markierten Stellen noch einmal an und versuche es erneut.']);
        bL.hidden = versuche < 2; bN.hidden = true;
      }
      melden(!!r.ok);
    });
    bN.addEventListener('click', function () {
      q.reset(); sperren(false); fb.className = 'vg-fb'; fb.innerHTML = ''; versuche = 0; bP.hidden = false; bN.hidden = true; bL.hidden = true;
    });
    bL.addEventListener('click', function () {
      q.loesen(); sperren(true); zeigen('info', 'So ist es richtig:', [b.erklaerung || 'Die richtigen Antworten sind jetzt markiert.']);
      bP.hidden = true; bL.hidden = true; bN.hidden = false;
    });
    if (bT) bT.addEventListener('click', function () { zeigen('tipp', 'Tipp:', [b.tipp]); });
    return box;
  }

  /* ---------- Rolle eines Reichs ---------- */
  function config(daten, reich) {
    var R = (daten && daten.reiche) || {}, c = R[reich] || R['*'] || {};
    var n = (daten && daten.platzhalter) || PLATZHALTER, v = c.vignetten && c.vignetten.length ? c.vignetten : [];
    if (!v.length) for (var i = 0; i < n; i++) v.push({ titel: '', bloecke: [] });
    return { modus: c.modus === 'wiederholung' ? 'wiederholung' : 'vignetten', titel: c.titel, einleitung: c.einleitung, vignetten: v };
  }
  function etikett(cfg) { return cfg.modus === 'wiederholung' ? 'Aufgabe' : 'Vignette'; }
  function stand(reich, vi, v) {
    var qs = (v.bloecke || []).map(function (b, i) { return istQuiz(b) ? i : -1; }).filter(function (i) { return i >= 0; });
    var f = (FORTSCHRITT[reich] || {})[vi] || {};
    return { gesamt: qs.length, richtig: qs.filter(function (i) { return f[i] === true; }).length };
  }

  function render(box, daten, ctx) {
    var cfg = config(daten, ctx.reich), wo = ANSICHT[ctx.reich];
    box.innerHTML = '';
    box.style.setProperty('--vc', ctx.farbe || '#6b5530');
    if (typeof wo === 'number' && cfg.vignetten[wo]) detail(box, daten, cfg, ctx, wo); else liste(box, daten, cfg, ctx);
  }

  function kopf(box, cfg, ctx) {
    var k = add(box, el('header', 'vg-kopf'));
    add(k, el('div', 'vg-art', cfg.modus === 'wiederholung' ? 'Wiederholung' : 'Das Wichtigste in Kürze'));
    add(k, el('h2', null, cfg.titel || ctx.name));
    if (cfg.einleitung) absaetze(k, cfg.einleitung);
    else add(k, el('p', 'vg-sub', cfg.modus === 'wiederholung'
      ? 'Was weißt du noch? Löse die Aufgaben. Du bekommst sofort eine Rückmeldung.'
      : 'Wähle eine Vignette aus.'));
  }

  function liste(box, daten, cfg, ctx) {
    ANSICHT[ctx.reich] = 'liste';
    kopf(box, cfg, ctx);
    var ul = add(box, el('ol', 'vg-liste'));
    cfg.vignetten.forEach(function (v, i) {
      var li = add(ul, el('li')), b = add(li, el('button', 'vg-karte' + (istLeer(v) ? ' leer' : ''))); b.type = 'button';
      add(b, el('span', 'vg-nr', String(i + 1)));
      var t = add(b, el('span', 'vg-kt'));
      add(t, el('b', null, v.titel || (etikett(cfg) + ' ' + (i + 1))));
      if (istLeer(v)) add(t, el('small', null, 'Inhalt folgt'));
      else {
        var s = stand(ctx.reich, i, v), arten = {};
        v.bloecke.forEach(function (x) { arten[istQuiz(x) ? 'quiz' : x.typ] = 1; });
        var sym = { text: 'Text', erzaehlung: 'Geschichte', bild: 'Bild', audio: 'Musik', video: 'Video', quiz: 'Quiz', quelle: 'Quelle' };
        add(t, el('small', null, Object.keys(arten).map(function (a) { return sym[a]; }).filter(Boolean).join(' · ')));
        if (s.gesamt) add(b, el('span', 'vg-stand' + (s.richtig === s.gesamt ? ' fertig' : ''), (s.richtig === s.gesamt ? '✓ ' : '') + s.richtig + '/' + s.gesamt));
      }
      b.addEventListener('click', function () { ANSICHT[ctx.reich] = i; render(box, daten, ctx); box.scrollTop = 0; fokus(box); });
    });
  }
  function fokus(box) { var h = box.querySelector('h2,h3'); if (h) { h.tabIndex = -1; h.focus({ preventScroll: true }); } }

  function detail(box, daten, cfg, ctx, i) {
    var v = cfg.vignetten[i], n = cfg.vignetten.length;
    var nav = add(box, el('nav', 'vg-nav'));
    var zur = add(nav, el('button', 'vg-btn', '← Übersicht')); zur.type = 'button';
    zur.addEventListener('click', function () { ANSICHT[ctx.reich] = 'liste'; render(box, daten, ctx); box.scrollTop = 0; fokus(box); });
    add(nav, el('span', 'vg-pos', etikett(cfg) + ' ' + (i + 1) + ' von ' + n));
    function geh(j) { ANSICHT[ctx.reich] = j; render(box, daten, ctx); box.scrollTop = 0; fokus(box); }
    var vor = add(nav, el('button', 'vg-btn', '‹')), nach = add(nav, el('button', 'vg-btn', '›'));
    vor.type = nach.type = 'button'; vor.title = 'Vorherige'; nach.title = 'Nächste';
    vor.disabled = i === 0; nach.disabled = i === n - 1;
    vor.addEventListener('click', function () { geh(i - 1); }); nach.addEventListener('click', function () { geh(i + 1); });

    var art = add(box, el('article', 'vg-art-body'));
    add(art, el('h3', null, v.titel || (etikett(cfg) + ' ' + (i + 1))));
    if (istLeer(v)) {
      var p = add(art, el('div', 'vg-leer'));
      add(p, el('b', null, 'Dieser Bereich ist vorbereitet.'));
      add(p, el('p', null, cfg.modus === 'wiederholung'
        ? 'Hier kommen später Aufgaben zur Wiederholung hin, jeweils mit Rückmeldung.'
        : 'Hier kommen später Texte, Bilder, Musik, kurze Videos und Quizfragen hin.'));
      return;
    }
    v.bloecke.forEach(function (b, bi) {
      var node;
      if (istQuiz(b)) node = quizBlock(b, function (ok) {
        var F = FORTSCHRITT[ctx.reich] = FORTSCHRITT[ctx.reich] || {}; F[i] = F[i] || {};
        if (F[i][bi] !== true) F[i][bi] = ok;
      });
      else if (BLOCK[b.typ]) node = BLOCK[b.typ](b);
      else node = el('div', 'vg-fehlt', 'Unbekannter Baustein „' + b.typ + '“ (siehe docs/VIGNETTEN.md).');
      add(art, node);
    });
    if (v.quellen && v.quellen.length) {
      var q = add(art, el('div', 'vg-quellen')); add(q, el('div', 'vg-h', 'Quellen'));
      var ol = add(q, el('ol')); v.quellen.forEach(function (t) { add(ol, el('li', null, t)); });
    }
    if (i < n - 1) {
      var w = add(art, el('button', 'vg-btn prim vg-weiter', 'Weiter zu ' + etikett(cfg) + ' ' + (i + 2) + ' →')); w.type = 'button';
      w.addEventListener('click', function () { geh(i + 1); });
    }
  }

  function modus(daten, reich) { return config(daten, reich).modus; }
  function zuruecksetzen(reich) { if (reich) ANSICHT[reich] = 'liste'; }

  window.Vignetten = { render: render, modus: modus, zuruecksetzen: zuruecksetzen, typen: { bloecke: Object.keys(BLOCK), quiz: Object.keys(QUIZ) } };
})();
