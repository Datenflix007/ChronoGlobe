/* ChronoGlobe · Live-Sessions (Lehrkraft steuert, Schüler:innen folgen). Ablauf und Sicherheit: docs/ARCHITEKTUR.md.

   Übertragung
   - Supabase (Standard): Die Lehrkraft schreibt nur über RPCs (Token geprüft, sql/schema.sql). Die Datenbank speichert
     den Zustand und verteilt ihn per realtime.send an den privaten Kanal „cg:<kanal-uuid>“. Schüler-Geräte dürfen dort
     nur lesen (RLS auf realtime.messages) und senden nichts außer einer leeren Anwesenheitsmeldung (Teilnehmerzahl).
     Fällt Realtime aus, wird der Zustand per RPC abgefragt (alle 3 s), bis die Verbindung wieder steht.
   - Lokal (?sync=lokal): BroadcastChannel + localStorage im selben Browser. Nur für Tests ohne Supabase.

   Schülerrechte (je „lehrer“ = nur Lehreransicht oder „selbst“ = selbst bedienen):
     zeit (Zeitriegel) · globus (drehen/zoomen) · reiche (Schriftrolle) · routen (Routen, Orte, Gesandtschaften, Texte)
   Von Schüler-Geräten wird nichts gespeichert und nichts Personenbezogenes übertragen. */
(function () {
  'use strict';
  var LS_KEY = 'chronoglobe.sessions';
  var LOKAL = /[?&]sync=lokal\b/.test(location.search);
  var S = window.CGSession = { lokal: LOKAL, status: 'aus', anzahl: 0 };
  var RECHTE_STANDARD = { zeit: 'lehrer', globus: 'lehrer', reiche: 'lehrer', routen: 'lehrer' };
  var RECHTE_TXT = { zeit: 'Zeitriegel', globus: 'Globus drehen/zoomen', reiche: 'Reiche anklicken (Schriftrolle)', routen: 'Routen, Orte, Gesandtschaften, Schülertexte' };

  /* ---------- Hilfen ---------- */
  var skripte = {};
  function skript(src) {
    if (skripte[src]) return skripte[src];
    return (skripte[src] = new Promise(function (ok, fehler) {
      var s = document.createElement('script'); s.src = src; s.onload = ok;
      s.onerror = function () { fehler(new Error(src + ' konnte nicht geladen werden')); };
      document.head.appendChild(s);
    }));
  }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function zufall(n) { var a = new Uint8Array(n); crypto.getRandomValues(a); return Array.prototype.map.call(a, function (x) { return ('0' + x.toString(16)).slice(-2); }).join(''); }
  function gleich(a, b) { return JSON.stringify(a == null ? null : a) === JSON.stringify(b == null ? null : b); }
  function codeNorm(c) { return String(c || '').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 12); }
  function basisUrl() { return location.href.replace(/[?#].*$/, '').replace(/[^/]*$/, ''); }
  S.schuelerLink = function (code) { return basisUrl() + 'index.html?code=' + encodeURIComponent(code) + (LOKAL ? '&sync=lokal' : ''); };
  S.lehrerLink = function (code) { return basisUrl() + 'app.html?session=' + encodeURIComponent(code) + '&rolle=lehrer' + (LOKAL ? '&sync=lokal' : ''); };
  function rate() { var r = +((window.APP_CONFIG || {}).SYNC_RATE); return r > 0 && r <= 20 ? r : 3; }

  /* ---------- gemerkte Sessions der Lehrkraft (nur in diesem Browser) ---------- */
  S.gespeicherte = function () { try { return JSON.parse(localStorage.getItem(LS_KEY) || '[]'); } catch (e) { return []; } };
  function merken(e) {
    var l = S.gespeicherte().filter(function (x) { return x.code !== e.code; }); l.unshift(e);
    try { localStorage.setItem(LS_KEY, JSON.stringify(l.slice(0, 20))); } catch (x) {}
  }
  S.vergessen = function (code) { try { localStorage.setItem(LS_KEY, JSON.stringify(S.gespeicherte().filter(function (x) { return x.code !== code; }))); } catch (x) {} };
  function tokenVon(code) { var e = S.gespeicherte().filter(function (x) { return x.code === code; })[0]; return e ? e.token : null; }

  /* ---------- Konfiguration ---------- */
  S.konfiguriert = function () {
    if (LOKAL) return Promise.resolve(true);
    return skript('js/config.js').then(function () {
      var c = window.APP_CONFIG || {};
      return !!(c.SUPABASE_URL && c.SUPABASE_URL.indexOf('DEIN-PROJEKT') < 0 && c.SUPABASE_PUBLISHABLE_KEY && c.SUPABASE_PUBLISHABLE_KEY.indexOf('DEIN_KEY') < 0);
    }, function () { return false; });
  };

  /* ---------- Übertragung: Supabase ---------- */
  function supabaseWeg() {
    var dbp = null;
    function db() {
      if (!dbp) dbp = S.konfiguriert().then(function (ok) {
        if (!ok) throw new Error('nicht-eingerichtet');
        return skript('vendor/supabase.min.js').then(function () { return skript('js/supabase-client.js'); }).then(function () { return window.db; });
      });
      return dbp;
    }
    function rpc(name, args) {
      return db().then(function (d) { return d.rpc(name, args); }).then(function (r) { if (r.error) throw r.error; return r.data; });
    }
    return {
      erstellen: function (tb) { return rpc('create_session', { p_tafelbild_id: tb }); },
      oeffentlich: function (code) { return rpc('get_session_public', { p_code: code }); },
      lehrerStand: function (code, tok) { return rpc('teacher_snapshot', { p_code: code, p_token: tok }); },
      senden: function (code, tok, st, modus) { return rpc('teacher_update_state', { p_code: code, p_token: tok, p_state: st, p_modus: modus || 'state' }); },
      rechteSetzen: function (code, tok, r, mit) { return rpc('teacher_update_rechte', { p_code: code, p_token: tok, p_rechte: r, p_fenster_mitsenden: mit }); },
      offenSetzen: function (code, tok, offen) { return rpc('set_session_open', { p_code: code, p_token: tok, p_is_open: offen }); },
      beenden: function (code, tok) { return rpc('delete_session', { p_code: code, p_token: tok }); },
      /* privater Kanal: nur lesen + Anwesenheit. Schlägt das mit dem Publishable Key fehl, einmal anonym anmelden
         (Supabase „Anonymous Sign-ins“, ohne Namen/E-Mail) und erneut versuchen (Rückfall B, docs/SETUP.md). */
      abonnieren: function (kanal, h, anwesend) {
        var ch = null, aus = false, anonymVersucht = false;
        function verbinden(d) {
          if (aus) return;
          ch = d.channel('cg:' + kanal, { config: { private: true, presence: { key: zufall(8) } } });
          ch.on('broadcast', { event: '*' }, function (m) { h.nachricht(m.event, m.payload || {}); });
          ch.on('presence', { event: 'sync' }, function () { h.anzahl(Object.keys(ch.presenceState()).length); });
          ch.subscribe(function (status, err) {
            if (status === 'SUBSCRIBED') { if (anwesend) ch.track({}); h.status('live'); }
            else if (status === 'CHANNEL_ERROR' && !anonymVersucht && d.auth && d.auth.signInAnonymously) {
              anonymVersucht = true; h.status('verbinde');
              d.removeChannel(ch);
              d.auth.signInAnonymously().then(function (r) {
                if (r.error) throw r.error;
                return d.realtime.setAuth(r.data.session.access_token);
              }).then(function () { verbinden(d); }, function () { h.status('abfrage', err); });
            }
            else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT' || status === 'CLOSED') h.status(aus ? 'aus' : 'abfrage', err);
          });
        }
        db().then(verbinden);
        return { stop: function () { aus = true; db().then(function (d) { if (ch) d.removeChannel(ch); }); } };
      }
    };
  }

  /* ---------- Übertragung: lokal (Tests, ?sync=lokal) ---------- */
  function lokalWeg() {
    function lesen(code) { try { return JSON.parse(localStorage.getItem('cg.lokal.' + code)); } catch (e) { return null; } }
    function schreiben(code, s) { localStorage.setItem('cg.lokal.' + code, JSON.stringify(s)); }
    function bc(code) { return new BroadcastChannel('cg.lokal.' + code); }
    function senden(code, ev, p) { var b = bc(code); b.postMessage({ ev: ev, p: p }); b.close(); }
    function lehrer(code, tok) { var s = lesen(code); if (!s || s.token !== tok) throw new Error('Lehrer-Zugriff verweigert'); return s; }
    function oeff(s) { return s ? { code: s.code, tafelbild_id: s.tafelbild_id, kanal: s.code, state: s.state, rechte: s.rechte, fenster_mitsenden: s.fenster_mitsenden, is_open: s.is_open, seq: s.seq } : null; }
    var P = Promise.resolve.bind(Promise);
    return {
      erstellen: function (tb) {
        var code = zufall(3).toUpperCase(), tok = zufall(24);
        schreiben(code, { code: code, tafelbild_id: tb, token: tok, state: {}, rechte: RECHTE_STANDARD, fenster_mitsenden: true, is_open: true, seq: 0 });
        return P({ code: code, token: tok, kanal: code });
      },
      oeffentlich: function (code) { return P(oeff(lesen(code))); },
      lehrerStand: function (code, tok) { return new Promise(function (ok) { ok(oeff(lehrer(code, tok))); }); },
      senden: function (code, tok, st, modus) {
        return new Promise(function (ok) {
          var s = lehrer(code, tok); s.state = st; s.seq++; schreiben(code, s);
          senden(code, modus || 'state', { state: st, seq: s.seq }); ok(s.seq);
        });
      },
      rechteSetzen: function (code, tok, r, mit) {
        return new Promise(function (ok) {
          var s = lehrer(code, tok); s.rechte = r; s.fenster_mitsenden = mit; s.seq++; schreiben(code, s);
          senden(code, 'rechte', { rechte: r, fenster_mitsenden: mit, seq: s.seq }); ok();
        });
      },
      offenSetzen: function (code, tok, offen) { return new Promise(function (ok) { var s = lehrer(code, tok); s.is_open = offen; schreiben(code, s); senden(code, 'offen', { is_open: offen }); ok(); }); },
      beenden: function (code, tok) { return new Promise(function (ok) { lehrer(code, tok); localStorage.removeItem('cg.lokal.' + code); senden(code, 'beendet', {}); ok(); }); },
      abonnieren: function (kanal, h, anwesend) {
        var b = bc(kanal), ich = zufall(6), gesehen = {}, t1, t2;
        b.onmessage = function (e) {
          var m = e.data || {};
          if (m.ev === '_da') { gesehen[m.p.id] = Date.now(); return; }
          h.nachricht(m.ev, m.p || {});
        };
        function da() { var x = bc(kanal); x.postMessage({ ev: '_da', p: { id: ich } }); x.close(); }
        if (anwesend) { da(); t1 = setInterval(da, 1500); }
        t2 = setInterval(function () {
          var j = Date.now(); Object.keys(gesehen).forEach(function (k) { if (j - gesehen[k] > 4000) delete gesehen[k]; });
          h.anzahl(Object.keys(gesehen).length);
        }, 1000);
        setTimeout(function () { h.status('live'); }, 50);
        return { stop: function () { clearInterval(t1); clearInterval(t2); b.close(); } };
      }
    };
  }
  var WEG = LOKAL ? lokalWeg() : supabaseWeg();

  /* ---------- Landingpage: Session anlegen ---------- */
  S.erstellen = function (tafelbildId, titel) {
    return WEG.erstellen(tafelbildId).then(function (r) {
      var e = { code: r.code, token: r.token, tafelbild: tafelbildId, titel: titel || tafelbildId, erstellt: new Date().toISOString(), lokal: LOKAL };
      merken(e); return e;
    });
  };
  S.beenden = function (code) {
    var tok = tokenVon(code);
    return (tok ? WEG.beenden(code, tok) : Promise.resolve()).then(function () { S.vergessen(code); });
  };
  S.qr = function (box, text) {
    return skript('vendor/qrcode.min.js').then(function () {
      box.innerHTML = '';
      new QRCode(box, { text: text, width: 220, height: 220, colorDark: '#0b1320', colorLight: '#ffffff', correctLevel: QRCode.CorrectLevel.M });
    });
  };

  /* ---------- App: Sperrfenster (Fehler, gesperrt, beendet, Lehrer-Schlüssel) ---------- */
  function sperre(titel, text, opts) {
    opts = opts || {};
    var alt = document.querySelector('.cg-sperre'); if (alt) alt.remove();
    var o = el('div', 'cg-sperre'), b = el('div', 'cg-sperre-box'); o.setAttribute('role', 'dialog'); o.setAttribute('aria-modal', 'true');
    b.appendChild(el('h2', null, titel)); if (text) b.appendChild(el('p', null, text));
    var feld = null;
    if (opts.eingabe) { feld = el('input', 'cg-eingabe'); feld.type = 'text'; feld.placeholder = opts.eingabe; feld.autocomplete = 'off'; b.appendChild(feld); }
    var row = el('div', 'cg-sperre-row');
    (opts.knoepfe || []).forEach(function (k) {
      var x = el(k.href ? 'a' : 'button', 'cg-knopf' + (k.prim ? ' prim' : ''), k.text);
      if (k.href) x.href = k.href; else { x.type = 'button'; x.addEventListener('click', function () { k.fn(feld ? feld.value : null, o); }); }
      row.appendChild(x);
    });
    if (!opts.knoepfe) { var a = el('a', 'cg-knopf prim', 'Zur Startseite'); a.href = 'index.html'; row.appendChild(a); }
    b.appendChild(row); o.appendChild(b); document.body.appendChild(o);
    if (feld) feld.focus();
    return o;
  }
  S.sperre = sperre;

  /* ---------- App: vor dem Laden der Daten (js/tafelbild.js) ---------- */
  var SITZ = null;   // { code, rolle, token, oeff, kanal }
  S.vorbereiten = function (code, rolle) {
    code = codeNorm(code);
    SITZ = { code: code, rolle: rolle, token: null };
    document.documentElement.classList.add('cg-session', rolle === 'lehrer' ? 'cg-lehrkraft' : 'cg-schueler');
    return S.konfiguriert().then(function (ok) {
      if (!ok) throw Object.assign(new Error('Supabase ist nicht eingerichtet (js/config.js, docs/SETUP.md).'), { art: 'nicht-eingerichtet' });
      return WEG.oeffentlich(code);
    }).then(function (o) {
      if (!o) throw Object.assign(new Error('Zu diesem Code gibt es keine Session. Bitte den Code prüfen.'), { art: 'unbekannt' });
      SITZ.oeff = o; SITZ.kanal = o.kanal;
      if (rolle !== 'lehrer') {
        if (!o.is_open) throw Object.assign(new Error('Die Lehrkraft hat die Session gerade gesperrt. Bitte später erneut versuchen.'), { art: 'gesperrt' });
        return o;
      }
      return lehrerZugang(code).then(function (stand) { SITZ.oeff = stand; return stand; });
    }).catch(function (e) { SITZ.fehler = e; throw e; });
  };
  function lehrerZugang(code) {
    var tok = tokenVon(code);
    function pruefen(t) { return WEG.lehrerStand(code, t).then(function (st) { if (!st) throw new Error('verweigert'); SITZ.token = t; return st; }); }
    var erst = tok ? pruefen(tok) : Promise.reject(new Error('kein Schlüssel'));
    return erst.catch(function () {
      return new Promise(function (ok) {
        sperre('Lehrer-Schlüssel', 'Für die Lehreransicht der Session ' + code + ' wird der Lehrer-Schlüssel benötigt. Er wurde beim Starten der Session angezeigt.', {
          eingabe: 'Lehrer-Schlüssel',
          knoepfe: [{ text: 'Öffnen', prim: true, fn: function (wert, o) {
            pruefen((wert || '').trim()).then(function (st) {
              merken({ code: code, token: SITZ.token, tafelbild: st.tafelbild_id, titel: st.tafelbild_id, erstellt: new Date().toISOString(), lokal: LOKAL });
              o.remove(); ok(st);
            }, function () { o.querySelector('p').textContent = 'Der Schlüssel passt nicht. Bitte erneut eingeben.'; });
          } }, { text: 'Zur Startseite', href: 'index.html' }]
        });
      });
    });
  }

  /* ---------- App: nach dem Start (Ereignis aus js/app.js) ---------- */
  document.addEventListener('chronoglobe:bereit', function () {
    if (!SITZ) return;
    if (SITZ.fehler) {
      sperre(SITZ.fehler.art === 'gesperrt' ? 'Session gesperrt' : 'Session nicht verfügbar', SITZ.fehler.message, SITZ.fehler.art === 'gesperrt'
        ? { knoepfe: [{ text: 'Erneut versuchen', prim: true, fn: function () { location.reload(); } }, { text: 'Zur Startseite', href: 'index.html' }] } : null);
      return;
    }
    if (SITZ.rolle === 'lehrer') lehrerStarten(); else schuelerStarten();
  });

  function statusBadge() {
    var b = document.querySelector('.cg-badge');
    if (b) return b;
    b = el('div', 'cg-badge'); b.setAttribute('role', 'status'); b.setAttribute('aria-live', 'polite');
    b.appendChild(el('span', 'cg-punkt')); b.appendChild(el('span', 'cg-btext'));
    document.body.appendChild(b); return b;
  }
  var STATUS_TXT = { live: 'live', verbinde: 'verbinde …', abfrage: 'Verbindung unterbrochen · Abfrage alle 3 s', aus: 'getrennt' };
  function statusSetzen(s, text) {
    S.status = s;
    var b = statusBadge(); b.dataset.s = s;
    b.querySelector('.cg-btext').textContent = text || ('Session ' + SITZ.code + ' · ' + (STATUS_TXT[s] || s));
  }

  /* Kanal + Rückfall-Abfrage. h.nachricht(ev, p) */
  function verbinden(h, anwesend) {
    var abfrage = null, seq = 0;
    function nachricht(ev, p) { if (p && p.seq) seq = Math.max(seq, p.seq); h.nachricht(ev, p); }
    function pollen() {
      WEG.oeffentlich(SITZ.code).then(function (o) {
        if (!o) { nachricht('beendet', {}); return; }
        if (!gleich(o.rechte, h.rechte && h.rechte()) || o.fenster_mitsenden !== (h.mitsenden && h.mitsenden())) nachricht('rechte', { rechte: o.rechte, fenster_mitsenden: o.fenster_mitsenden });
        if (o.seq > seq) nachricht('state', { state: o.state, seq: o.seq });
      }).catch(function () {});
    }
    var abo = WEG.abonnieren(SITZ.kanal, {
      nachricht: nachricht,
      anzahl: function (n) { S.anzahl = n; if (h.anzahl) h.anzahl(n); },
      status: function (s) {
        statusSetzen(s);
        if (s === 'live') { if (abfrage) { clearInterval(abfrage); abfrage = null; pollen(); } }
        else if (s === 'abfrage' && !abfrage) { abfrage = setInterval(pollen, 3000); pollen(); }
      }
    }, anwesend);
    statusSetzen('verbinde');
    // keine Verbindung nach 8 s: Abfrage starten (Verbindung wird weiter versucht)
    setTimeout(function () { if (S.status !== 'live' && !abfrage) { statusSetzen('abfrage'); abfrage = setInterval(pollen, 3000); pollen(); } }, 8000);
    return abo;
  }

  /* ---------- Lehrkraft ---------- */
  function lehrerStarten() {
    var CGL = window.ChronoGlobe, o = SITZ.oeff;
    var L = { rechte: Object.assign({}, RECHTE_STANDARD, o.rechte || {}), mitsenden: o.fenster_mitsenden !== false, offen: o.is_open !== false };
    S.lehrer = L;
    // Fortsetzen nach Reload: gespeicherten Lehrerzustand übernehmen
    if (o.state && o.state.v) CGL.applyState(o.state, { quelle: 'tafelbild' });
    lehrerMenu(L);
    var letzt = 0, timer = null, gesendet = '', laufend = Promise.resolve();
    function zustand() {
      var st = CGL.getState();
      if (st.fenster && st.fenster.modal === 'lehrer') st.fenster.modal = null;   // Lehrerhinweise nie mitsenden
      if (!L.mitsenden) delete st.fenster;
      st.kamera.ref = CGL.homeAlt();   // Bezug für Geräte mit anderem Bildformat (Handy, Tablet)
      return st;
    }
    function senden(modus) {
      var st = zustand(), j = JSON.stringify(st);
      if (!modus && j === gesendet) return;
      gesendet = j; letzt = Date.now();
      laufend = laufend.then(function () { return WEG.senden(SITZ.code, SITZ.token, st, modus || 'state'); })
        .catch(function (e) { console.error(e); statusSetzen('abfrage', 'Senden fehlgeschlagen: ' + (e.message || e)); });
    }
    function planen() {
      var abstand = 1000 / rate(), j = Date.now();
      if (j - letzt >= abstand) senden();
      else if (!timer) timer = setTimeout(function () { timer = null; senden(); }, abstand - (j - letzt));
    }
    S.senden = senden;
    CGL.abonnieren(function (q) { if (q !== 'tafelbild') planen(); });
    setInterval(planen, 1000 / rate());   // Kamerabewegungen (Ziehen, Zoomen, Flüge) melden sich nicht von selbst
    senden('zurueck');                   // Nachzügler und Reload: aktueller Stand sofort
    verbinden({ nachricht: function () {}, anzahl: function (n) { var a = document.querySelector('#cgAnzahl'); if (a) a.textContent = n === 1 ? '1 Gerät verbunden' : n + ' Geräte verbunden'; } }, false);
  }

  function lehrerMenu(L) {
    var CGL = window.ChronoGlobe, tb = (window.CG && CG.tafelbild) || {};
    var sec = el('section', 'cg-lehrer'); sec.setAttribute('aria-label', 'Lehrermenü');
    sec.appendChild(el('h2', null, 'Live-Session'));
    var kopf = el('div', 'cg-kopf');
    kopf.appendChild(el('div', 'cg-code', SITZ.code));
    var anz = el('div', 'cg-anzahl', '0 Geräte verbunden'); anz.id = 'cgAnzahl'; kopf.appendChild(anz);
    sec.appendChild(kopf);
    function knopf(text, fn, cls) { var b = el('button', 'small' + (cls ? ' ' + cls : ''), text); b.type = 'button'; b.addEventListener('click', fn); return b; }
    var r1 = el('div', 'row');
    r1.appendChild(knopf('Link kopieren', function () {
      var t = S.schuelerLink(SITZ.code);
      (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(function () { this.textContent = 'Kopiert ✓'; }.bind(this), function () { window.prompt('Link für Schüler:innen', t); });
    }));
    r1.appendChild(knopf('QR-Code', function () { qrFenster(); }));
    sec.appendChild(r1);
    var r2 = el('div', 'row'), bOffen = knopf(L.offen ? 'Session sperren' : 'Session öffnen', function () {
      var neu = !L.offen;
      WEG.offenSetzen(SITZ.code, SITZ.token, neu).then(function () { L.offen = neu; bOffen.textContent = neu ? 'Session sperren' : 'Session öffnen'; bOffen.classList.toggle('on', !neu); });
    });
    bOffen.title = 'Gesperrt: Niemand kann neu beitreten; wer schon dabei ist, bleibt verbunden.';
    r2.appendChild(bOffen);
    r2.appendChild(knopf('Session beenden', function () {
      if (!window.confirm('Session ' + SITZ.code + ' beenden? Sie wird sofort gelöscht; alle Geräte werden getrennt.')) return;
      WEG.beenden(SITZ.code, SITZ.token).then(function () { S.vergessen(SITZ.code); location.href = 'index.html'; });
    }, 'warn'));
    sec.appendChild(r2);

    sec.appendChild(el('h3', 'cg-h3', 'Fokus für alle'));
    var fr = el('div', 'row cg-wrap');
    (tb.fokuspunkte || []).forEach(function (f) {
      fr.appendChild(knopf(f.name, function () {
        var t = Object.assign({}, f.filter || {}); t.kamera = { lat: f.lat, lng: f.lng, alt: f.alt === 'standard' || f.alt == null ? CGL.homeAlt() : f.alt };
        if (f.jahr != null) t.jahr = f.jahr;
        CGL.setState(t, { dauer: 1400 });
        setTimeout(function () { S.senden('fokus'); }, 1450);
      }));
    });
    fr.appendChild(knopf('Aktuelle Ansicht für alle', function () { S.senden('fokus'); }, 'prim'));
    sec.appendChild(fr);
    sec.appendChild(knopf('Alle zurück zu meiner Ansicht', function () { S.senden('zurueck'); }, 'voll'));

    sec.appendChild(el('h3', 'cg-h3', 'Schülerrechte'));
    var tab = el('div', 'cg-rechte');
    Object.keys(RECHTE_TXT).forEach(function (k) {
      var z = el('div', 'cg-recht'); z.appendChild(el('span', 'cg-rname', RECHTE_TXT[k]));
      var seg = el('div', 'seg cg-seg');
      [['lehrer', 'Lehreransicht'], ['selbst', 'selbst bedienen']].forEach(function (w) {
        var b = el('button', L.rechte[k] === w[0] ? 'on' : '', w[1]); b.type = 'button'; b.dataset.recht = k; b.dataset.wert = w[0];
        b.setAttribute('aria-pressed', L.rechte[k] === w[0]);
        b.addEventListener('click', function () {
          L.rechte[k] = w[0];
          seg.querySelectorAll('button').forEach(function (x) { x.classList.toggle('on', x === b); x.setAttribute('aria-pressed', x === b); });
          WEG.rechteSetzen(SITZ.code, SITZ.token, L.rechte, L.mitsenden);
        });
        seg.appendChild(b);
      });
      z.appendChild(seg); tab.appendChild(z);
    });
    sec.appendChild(tab);
    var lab = el('label', 'cg-check'), cb = el('input'); cb.type = 'checkbox'; cb.checked = L.mitsenden; cb.id = 'cgFenster';
    cb.addEventListener('change', function () { L.mitsenden = cb.checked; WEG.rechteSetzen(SITZ.code, SITZ.token, L.rechte, L.mitsenden); S.senden(); });
    lab.appendChild(cb); lab.appendChild(document.createTextNode(' Geöffnete Fenster mitsenden')); sec.appendChild(lab);
    var pb = document.querySelector('#panelBody'); pb.insertBefore(sec, pb.firstChild);
  }
  function qrFenster() {
    var o = el('div', 'cg-sperre'), b = el('div', 'cg-sperre-box cg-qr-box');
    b.appendChild(el('h2', null, 'Beitreten: ' + SITZ.code));
    var q = el('div', 'cg-qr'); b.appendChild(q);
    var l = el('p', 'cg-link', S.schuelerLink(SITZ.code)); b.appendChild(l);
    var x = el('button', 'cg-knopf prim', 'Schließen'); x.type = 'button'; x.addEventListener('click', function () { o.remove(); });
    b.appendChild(x); o.appendChild(b); document.body.appendChild(o);
    o.addEventListener('click', function (e) { if (e.target === o) o.remove(); });
    S.qr(q, S.schuelerLink(SITZ.code));
  }

  /* ---------- Schüler:innen ---------- */
  function schuelerStarten() {
    var CGL = window.ChronoGlobe, o = SITZ.oeff, g = CGL.globe;
    var R = Object.assign({}, RECHTE_STANDARD, o.rechte || {}), mitsenden = o.fenster_mitsenden !== false;
    var T = null, abw = { zeit: false, globus: false, fenster: false }, wendet = 0;
    S.schueler = { rechte: function () { return R; }, abweichung: function () { return abw; } };
    var badge = statusBadge(), zur = el('button', 'cg-zurueck', 'Zur Lehreransicht zurück'); zur.type = 'button'; zur.hidden = true;
    badge.appendChild(zur);
    zur.addEventListener('click', function () { abw = { zeit: false, globus: false, fenster: false }; hinweis(); if (T) anwenden(T, null, true); });
    function hinweis() { zur.hidden = !(abw.zeit || abw.globus || abw.fenster); }

    function rechteAnwenden() {
      CGL.setzeRechte(function (k) { return R[k] === 'selbst'; });
      g.controls().enabled = R.globus === 'selbst';
      var h = document.documentElement;
      h.classList.toggle('cg-zeit-aus', R.zeit !== 'selbst');
      h.classList.toggle('cg-globus-aus', R.globus !== 'selbst');
      ['zeit', 'globus'].forEach(function (k) { if (R[k] !== 'selbst') abw[k] = false; });
      if (R.reiche !== 'selbst' && R.routen !== 'selbst') abw.fenster = false;
      hinweis();
      if (T) anwenden(T, null, false);
    }
    function anwenden(st, alt, alles) {
      if (!st || !st.v) return;
      var t = {};
      ['ansicht', 'reiche', 'globus', 'handel', 'strassen', 'zh', 'niveau'].forEach(function (k) { if (k in st) t[k] = st[k]; });
      if (alles || R.zeit !== 'selbst' || !abw.zeit) t.jahr = st.jahr;
      if (alles || R.globus !== 'selbst' || !abw.globus) {
        // gleicher Bildausschnitt auf anderem Format: Abstand im Verhältnis der Standardabstände umrechnen
        var k = st.kamera || {}, f = k.ref ? CGL.homeAlt() / k.ref : 1;
        t.kamera = { lat: k.lat, lng: k.lng, alt: Math.max(0.15, Math.min(6, (k.alt || CGL.homeAlt()) * f)) }; t.drehen = false;
      }
      if (st.fenster && (mitsenden || alles)) {
        var jetzt = CGL.getState().fenster, af = (alt && alt.fenster) || {}, f = {};
        [['rolle', 'reiche'], ['info', 'routen'], ['waren', 'routen'], ['modal', null]].forEach(function (x) {
          var slot = x[0], recht = x[1], soll = st.fenster[slot] || null;
          if (slot === 'modal' && soll === 'lehrer') soll = null;
          var folgen = alles || (recht && R[recht] !== 'selbst') || !gleich(af[slot], st.fenster[slot]);
          f[slot] = folgen ? soll : jetzt[slot];
        });
        t.fenster = f;
      }
      wendet++;
      try { CGL.applyState(t, { quelle: 'lehrer', dauer: alles ? 900 : Math.round(1150 / rate()) }); } finally { wendet--; }
    }
    function nachricht(ev, p) {
      if (ev === 'state' || ev === 'fokus' || ev === 'zurueck') {
        if (!p.state) return;
        var alt = T; T = p.state;
        if (ev === 'zurueck') { abw = { zeit: false, globus: false, fenster: false }; hinweis(); anwenden(T, alt, true); }
        else if (ev === 'fokus') { abw.globus = false; hinweis(); anwenden(T, alt, false); }
        else anwenden(T, alt, false);
      } else if (ev === 'rechte') {
        R = Object.assign({}, RECHTE_STANDARD, p.rechte || {}); mitsenden = p.fenster_mitsenden !== false; rechteAnwenden();
      } else if (ev === 'beendet') {
        sperre('Session beendet', 'Die Lehrkraft hat die Session beendet. Vielen Dank fürs Mitmachen!');
        if (S.abo) S.abo.stop();
      }
    }
    // eigene Abweichungen erkennen (nur bei „selbst bedienen“)
    CGL.abonnieren(function (q) {
      if (q !== 'lokal' || wendet || !T) return;
      var st = CGL.getState();
      if (R.zeit === 'selbst' && st.jahr !== T.jahr) abw.zeit = true;
      if ((R.reiche === 'selbst' || R.routen === 'selbst') && T.fenster && !gleich(st.fenster, Object.assign({}, T.fenster, { modal: T.fenster.modal === 'lehrer' ? null : T.fenster.modal }))) abw.fenster = true;
      hinweis();
    });
    g.controls().addEventListener('start', function () { if (R.globus === 'selbst') { abw.globus = true; hinweis(); } });
    if (o.state && o.state.v) { T = o.state; }
    rechteAnwenden();
    if (T) anwenden(T, null, true);
    S.abo = verbinden({ nachricht: nachricht, rechte: function () { return R; }, mitsenden: function () { return mitsenden; } }, true);
  }
})();
