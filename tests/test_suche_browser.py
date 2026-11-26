# -*- coding: utf-8 -*-
"""Suche im Browser (js/suche.js, sucheEinrichten in js/app.js): freier Modus, Tafelbild und Live-Session.
Prüft: Tastenkürzel „/“ und Strg+K, Pfeiltasten und Enter, Schreibvarianten, Flug zum Ort, Jahr, Infokarte und
Schriftrolle, ausgegraute Treffer außerhalb des Tafelbild-Zeitraums, Wirkung der Lehrkraft-Suche auf ein Schülergerät
(über den normalen Zustand, ?sync=lokal) und dass Schüler:innen kein Suchfeld haben.

    python tests/test_suche_browser.py

Benötigt: playwright und Microsoft Edge oder Chromium.
"""
import mimetypes, os, sys, urllib.parse
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'http://localhost:8765/'
ST = 'ChronoGlobe.getState()'
ok, fehl = 0, 0


def check(name, bed, info=''):
    global ok, fehl
    if bed: ok += 1; print('  ok   ' + name + (' – ' + str(info) if info else ''))
    else: fehl += 1; print('  FEHL ' + name + (' – ' + str(info) if info else ''))


def serve(route):
    u = urllib.parse.urlparse(route.request.url)
    fp = os.path.join(ROOT, urllib.parse.unquote(u.path.lstrip('/')))
    if os.path.isfile(fp): route.fulfill(path=fp, content_type=mimetypes.guess_type(fp)[0] or 'application/octet-stream')
    else: route.fulfill(status=404, body='nicht gefunden')


def warte(pg, js, ms=6000):
    try: pg.wait_for_function(js, timeout=ms); return True
    except Exception: return False


def treffer(pg):
    return pg.evaluate("[...document.querySelectorAll('#sucheListe .such-treffer')].map(li => ({ name: li.querySelector('b').textContent, art: li.dataset.art, aussen: li.classList.contains('aussen'), aktiv: li.classList.contains('aktiv') }))")


def tippen(pg, text):
    pg.fill('#sucheFeld', ''); pg.type('#sucheFeld', text); pg.wait_for_timeout(250)


with sync_playwright() as p:
    try: b = p.chromium.launch(channel='msedge', headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    except Exception: b = p.chromium.launch(headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    ctx = b.new_context(viewport={'width': 1400, 'height': 900}, bypass_csp=True); ctx.route(URL + '**', serve)
    errs = []
    def neu():
        pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('dialog', lambda d: d.accept()); return pg
    print('ChronoGlobe – Suche')

    # --- freier Modus ---
    F = neu(); F.goto(URL + 'app.html?modus=frei'); warte(F, 'window.ChronoGlobe', 20000); F.wait_for_timeout(1500)
    F.evaluate("ChronoGlobe.setState({ drehen: false })")
    check('Frei: Suchfeld sichtbar', F.is_visible('#sucheFeld'))
    F.keyboard.press('/'); check('Kürzel „/“ setzt den Fokus', F.evaluate('document.activeElement.id') == 'sucheFeld')
    F.keyboard.press('Escape'); F.evaluate('document.activeElement.blur()')
    F.keyboard.press('Control+k'); check('Kürzel Strg+K setzt den Fokus', F.evaluate('document.activeElement.id') == 'sucheFeld')
    for q in ("Chang'an", 'Changan'):
        tippen(F, q); t = treffer(F)
        check('Variante „%s“ → Chang\'an' % q, t and t[0]['name'] == "Chang'an", t[:2])
    tippen(F, 'Ctesiphon'); t = treffer(F)
    check('Variante „Ctesiphon“ → Ktesiphon', t and t[0]['name'] == 'Ktesiphon', t[:2])
    tippen(F, 'Rhein'); t = treffer(F)
    check('Geographie: heutiger Name „Rhein“ → Rhenus', t and t[0]['name'] == 'Rhenus' and t[0]['art'] == 'geo', t[:2])
    F.keyboard.press('Enter')
    check('Geographie: Flug zum Rhein, Ebene an', warte(F, 'Math.abs(%s.kamera.lng - 7) < 6 && %s.globus.geo === true' % (ST, ST), 5000), F.evaluate(ST + '.kamera'))

    # Pfeiltasten und Enter: Schlacht setzt Jahr und Kamera
    F.keyboard.press('Control+k'); tippen(F, 'Carrhae'); t = treffer(F)
    check('Pfeiltasten: erster Treffer aktiv', t and t[0]['aktiv'])
    F.keyboard.press('ArrowDown'); t2 = treffer(F)
    check('Pfeil runter wählt den nächsten Treffer', len(t2) > 1 and t2[1]['aktiv'] and not t2[0]['aktiv'])
    F.keyboard.press('ArrowUp'); F.keyboard.press('Enter')
    check('Schlacht: Jahr 53 v. Chr. und Flug nach Carrhae', warte(F, '%s.jahr === -53 && Math.abs(%s.kamera.lng - 39) < 3' % (ST, ST), 5000),
          F.evaluate('[%s.jahr, %s.kamera]' % (ST, ST)))
    check('Liste nach Auswahl geschlossen', F.is_hidden('#sucheListe'))

    # Ereignis: Jahr, Reich eingeblendet, Infokarte hervorgehoben
    F.keyboard.press('Control+k'); tippen(F, 'Gelbe Turbane'); t = treffer(F)
    check('Ereignis gefunden', t and t[0]['art'] == 'ereignis', t[:1])
    F.keyboard.press('Enter')
    check('Ereignis: Jahr gesetzt, Han-Reich an', warte(F, '%s.jahr === 184 && %s.reiche.han === true' % (ST, ST), 5000), F.evaluate(ST + '.jahr'))
    check('Ereignis: Infokarte des Reichs hervorgehoben', warte(F, "!!document.querySelector('#cards .card.such-hl[data-r=\"han\"]')", 3000))

    # Reich mit Schriftrolle (Umschalt+Enter)
    F.keyboard.press('Control+k'); tippen(F, 'Partherreich'); F.keyboard.press('Shift+Enter')
    check('Reich: Umschalt+Enter öffnet die Schriftrolle', warte(F, "%s.fenster.rolle && %s.fenster.rolle.reich === 'parth'" % (ST, ST), 5000))
    F.keyboard.press('Control+k'); tippen(F, 'Luoyang'); F.keyboard.press('Enter')
    check('Neuer Treffer schließt die Schriftrolle (Globus sichtbar)', warte(F, '%s.fenster.rolle === null && Math.abs(%s.kamera.lng - 112) < 3' % (ST, ST), 5000))

    # Handelsort: Infokarte
    F.keyboard.press('Control+k'); tippen(F, 'Palmyra'); t = treffer(F)
    F.keyboard.press('Enter')
    check('Handelsort: Infokarte „Handelsort“ geöffnet', warte(F, "%s.fenster.info && %s.fenster.info.art === 'ort'" % (ST, ST), 5000), t[:1])
    F.keyboard.press('Escape'); F.wait_for_timeout(200)
    F.keyboard.press('Control+k'); tippen(F, 'qqqxxyy')
    check('Keine Treffer: Hinweis', F.is_visible('.such-leer'))
    F.keyboard.press('Escape'); check('Escape leert das Feld', F.input_value('#sucheFeld') == '')

    # --- Tafelbild: Treffer außerhalb des Zeitraums ausgegraut ---
    T = neu(); T.goto(URL + 'app.html?tafelbild=rom-zentrum-der-welt'); warte(T, 'window.ChronoGlobe', 20000); T.wait_for_timeout(1500)
    T.keyboard.press('/'); tippen(T, 'Ming'); t = treffer(T)
    m = [x for x in t if x['name'] == 'Ming-Reich']
    check('Tafelbild: Ming-Reich ausgegraut', m and m[0]['aussen'], t)
    check('Tafelbild: ausgegraute Treffer stehen hinten', all(x['aussen'] for x in t[[i for i, x in enumerate(t) if x['aussen']][0]:]) if any(x['aussen'] for x in t) else False)
    jahr = T.evaluate(ST + '.jahr')
    T.click('#sucheListe .such-treffer.aussen >> nth=0', force=True); T.wait_for_timeout(500)
    check('Tafelbild: Klick auf ausgegrauten Treffer ändert nichts', T.evaluate(ST + '.jahr') == jahr and 'außerhalb des Zeitraums' in T.inner_text('#toast'), T.inner_text('#toast'))
    T.keyboard.press('/'); tippen(T, 'Ktesiphon'); T.keyboard.press('Enter')
    check('Tafelbild: Ktesiphon anfliegen', warte(T, 'Math.abs(%s.kamera.lng - 44.5) < 2' % ST, 5000))

    # --- Live-Session: Suche der Lehrkraft wirkt über den Zustand auf alle ---
    L = neu(); L.goto(URL + 'index.html?sync=lokal'); L.wait_for_timeout(800)
    L.click('#btnStarten'); warte(L, "document.querySelector('#nsCode').textContent.length >= 4")
    code = L.inner_text('#nsCode'); lehrer = L.get_attribute('#nsOeffnen', 'href')
    LK = neu(); LK.goto(lehrer); warte(LK, 'window.ChronoGlobe', 20000); LK.wait_for_timeout(1500); LK.evaluate("ChronoGlobe.setState({ drehen: false })")
    S = neu(); S.goto(URL + 'index.html?code=' + code + '&sync=lokal'); warte(S, 'window.ChronoGlobe', 20000); S.wait_for_timeout(1500)
    check('Session: Lehrkraft hat ein Suchfeld', LK.is_visible('#sucheFeld'))
    check('Session: Schüler:innen haben kein Suchfeld', not S.is_visible('#sucheFeld'))
    S.keyboard.press('/'); check('Session: „/“ bei Schüler:innen ohne Wirkung', S.evaluate('document.activeElement.id') != 'sucheFeld')
    LK.keyboard.press('Control+k'); tippen(LK, 'Carrhae'); LK.keyboard.press('Enter')
    check('Session: Schülergerät folgt der Suche (Jahr und Kamera)', warte(S, '%s.jahr === -53 && Math.abs(%s.kamera.lng - 39) < 4' % (ST, ST), 8000),
          S.evaluate('[%s.jahr, %s.kamera]' % (ST, ST)))
    LK.keyboard.press('Control+k'); tippen(LK, 'Sasanidenreich'); LK.keyboard.press('Shift+Enter')
    check('Session: Schriftrolle aus der Suche erscheint bei allen', warte(S, "%s.fenster.rolle && %s.fenster.rolle.reich === 'sasan'" % (ST, ST), 8000))

    check('keine Skriptfehler', not errs, errs[:3])
    b.close()

print('\n%d bestanden, %d fehlgeschlagen' % (ok, fehl))
sys.exit(1 if fehl else 0)
