# -*- coding: utf-8 -*-
"""Präsentationsfenster (js/praesentation.js) mit zwei bzw. drei Fenstern im selben Browser.
Prüft: Knopf „Präsentation“ öffnet das zweite Fenster; es zeigt kein Menü, keine Lehrerhinweise, hat Vollbild-Knopf
und Leuchtstift; Jahr, Reiche, Kamera und Schriftrolle folgen dem Steuerfenster; der Leuchtstift im
Präsentationsfenster kommt im Steuerfenster an (und in einer Session bei den Schüler:innen); das Präsentationsfenster
lädt kein Supabase und zählt nicht als Gerät. Funktioniert im freien Modus, im Tafelbild und in der Session.

    python tests/test_praesentation.py

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


def sichtbar(pg, sel):
    return pg.evaluate("(() => { const e = document.querySelector('%s'); return !!e && e.getClientRects().length > 0 && getComputedStyle(e).display !== 'none'; })()" % sel)


def strich(pg):
    """Einen Strich mit dem Leuchtstift in der Mitte des Globus ziehen."""
    pg.evaluate("ChronoGlobe.setState({ kamera: { lat: 40, lng: 20, alt: 1.8 } })"); pg.wait_for_timeout(500)
    m = pg.evaluate("(() => { const r = document.querySelector('#globe').getBoundingClientRect(), q = ChronoGlobe.globe.getScreenCoords(40, 20, 0); return [r.left + q.x, r.top + q.y]; })()")
    pg.mouse.move(m[0] - 80, m[1]); pg.mouse.down(); pg.mouse.move(m[0] + 80, m[1] + 20, steps=14); pg.mouse.up(); pg.wait_for_timeout(300)


with sync_playwright() as p:
    try: b = p.chromium.launch(channel='msedge', headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    except Exception: b = p.chromium.launch(headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    errs = []
    print('ChronoGlobe – Präsentationsfenster')

    def kontext():
        c = b.new_context(viewport={'width': 1400, 'height': 900}, bypass_csp=True); c.route(URL + '**', serve)
        c.on('page', lambda pg: (pg.on('pageerror', lambda e: errs.append(str(e))), pg.on('dialog', lambda d: d.accept())))
        return c

    def oeffnen(c, steuer):
        with c.expect_page() as neu: steuer.click('#btnPraes')
        pr = neu.value; warte(pr, 'window.ChronoGlobe', 20000); pr.wait_for_timeout(1200)
        return pr

    # --- freier Modus ---
    c = kontext(); F = c.new_page(); F.goto(URL + 'app.html?modus=frei'); warte(F, 'window.ChronoGlobe', 20000); F.wait_for_timeout(1200)
    F.evaluate("ChronoGlobe.setState({ drehen: false, jahr: 117 })")
    check('Frei: Knopf „Präsentation“', sichtbar(F, '#btnPraes'))
    PR = oeffnen(c, F)
    check('Präsentationsfenster: eigene Adresse mit Kanal', 'praesentation=' in PR.url and 'modus=frei' in PR.url, PR.url)
    check('Präsentationsfenster: kein Menü, keine Suche, kein „Präsentation“-Knopf', not sichtbar(PR, '#panel') and not sichtbar(PR, '#sucheFeld') and not sichtbar(PR, '#btnPraes'))
    check('Präsentationsfenster: Vollbild-Knopf und Leuchtstift', sichtbar(PR, '#btnVollbild') and sichtbar(PR, '.stift-leiste .stift-an'))
    check('Präsentationsfenster: große Schrift (Jahr)', PR.evaluate("parseFloat(getComputedStyle(document.querySelector('.year')).fontSize)") >= 40)
    check('Verbindung steht (Steuerknopf markiert, kein Warnhinweis)', warte(F, "document.querySelector('#btnPraes').classList.contains('on')", 4000) and not sichtbar(PR, '.praes-hinweis'))
    F.evaluate("ChronoGlobe.setState({ jahr: -53, reiche: { parth: true } })")
    check('Jahr und Reiche folgen dem Steuerfenster', warte(PR, '%s.jahr === -53 && %s.reiche.parth === true' % (ST, ST), 4000))
    F.evaluate("ChronoGlobe.setState({ kamera: { lat: 35, lng: 105, alt: 1.4 } })")
    check('Kamera folgt (ohne Supabase, lokal)', warte(PR, 'Math.abs(%s.kamera.lng - 105) < 3' % ST, 4000), PR.evaluate(ST + '.kamera'))
    PR.evaluate("ChronoGlobe.setState({ jahr: 300 })"); PR.wait_for_timeout(300)
    check('Präsentationsfenster: Zeitleiste nicht selbst bedienbar', PR.evaluate(ST + '.jahr') == -53)
    F.click('#cards .card button');
    check('Schriftrolle folgt', warte(PR, '%s.fenster.rolle !== null' % ST, 4000))
    F.click('#mapClose'); warte(PR, '%s.fenster.rolle === null' % ST, 4000); F.wait_for_timeout(1500)
    PR.click('.stift-an'); strich(PR)
    check('Leuchtstift im Präsentationsfenster kommt im Steuerfenster an', warte(F, '%s.zeichnung.length === 1' % ST, 4000), F.evaluate(ST + '.zeichnung.length'))
    PR.click('.stift-fest'); check('„Stehen lassen“ kommt an', warte(F, '%s.zeichnung.length === 1 && %s.zeichnung[0].fest' % (ST, ST), 4000))
    F.evaluate("ChronoGlobe.setState({ jahr: 100 })"); PR.wait_for_timeout(600)
    check('Zeichnung bleibt bei Änderungen des Steuerfensters erhalten', PR.evaluate(ST + '.zeichnung.length') == 1 and PR.evaluate(ST + '.jahr') == 100)
    PR.keyboard.press('Escape')
    F.reload(); warte(F, 'window.ChronoGlobe', 20000); F.wait_for_timeout(1500)
    F.evaluate("ChronoGlobe.setState({ jahr: 222 })")
    check('Steuerfenster neu geladen: Präsentationsfenster findet wieder Anschluss', warte(PR, '%s.jahr === 222' % ST, 6000))
    F.close(); PR.wait_for_timeout(300)
    check('Steuerfenster geschlossen: Hinweis im Präsentationsfenster', warte(PR, "!document.querySelector('.praes-hinweis').hidden", 7000))
    c.close()

    # --- Tafelbild: Lehrerhinweise nie im Präsentationsfenster ---
    c = kontext(); T = c.new_page(); T.goto(URL + 'app.html?tafelbild=rom-zentrum-der-welt'); warte(T, 'window.ChronoGlobe', 20000); T.wait_for_timeout(1200)
    PR = oeffnen(c, T)
    check('Tafelbild: Präsentationsfenster lädt dasselbe Tafelbild', 'tafelbild=rom-zentrum-der-welt' in PR.url and PR.evaluate('CG.tafelbild.id') == 'rom-zentrum-der-welt')
    T.click('#btnLehrer'); T.wait_for_timeout(800)
    check('Tafelbild: Lehrerhinweise erscheinen nicht', PR.evaluate(ST + '.fenster.modal') is None and not sichtbar(PR, '#lmodal') and not sichtbar(PR, '#btnLehrer'))
    T.keyboard.press('Escape'); c.close()

    # --- Session: Präsentationsfenster belastet weder Supabase noch die Gerätezahl ---
    c = kontext(); L = c.new_page(); L.goto(URL + 'index.html?sync=lokal'); L.wait_for_timeout(800)
    L.click('#btnStarten'); warte(L, "document.querySelector('#nsCode').textContent.length >= 4")
    code = L.inner_text('#nsCode')
    LK = c.new_page(); LK.goto(L.get_attribute('#nsOeffnen', 'href')); warte(LK, 'window.ChronoGlobe', 20000); LK.wait_for_timeout(1200)
    S = c.new_page(); S.goto(URL + 'app.html?session=' + code + '&rolle=schueler&sync=lokal'); warte(S, 'window.ChronoGlobe', 20000); S.wait_for_timeout(1200)
    check('Session: Schüler:innen haben keinen Knopf „Präsentation“', not sichtbar(S, '#btnPraes'))
    PR = oeffnen(c, LK)
    check('Session: Präsentationsfenster ohne Session und ohne Supabase', 'session=' not in PR.url and PR.evaluate("!document.querySelector('script[src*=\"supabase\"]') && !document.documentElement.classList.contains('cg-session')"))
    LK.wait_for_timeout(2500)
    check('Session: Präsentationsfenster zählt nicht als Gerät', LK.inner_text('#cgAnzahl').startswith('1 '), LK.inner_text('#cgAnzahl'))
    LK.evaluate("ChronoGlobe.setState({ jahr: 150 })")
    check('Session: Präsentationsfenster folgt der Lehrkraft', warte(PR, '%s.jahr === 150' % ST, 4000) and warte(S, '%s.jahr === 150' % ST, 6000))
    PR.click('.stift-an'); strich(PR); PR.click('.stift-fest')
    check('Session: Leuchtstift am Smartboard erreicht die Klasse', warte(S, '%s.zeichnung.length === 1 && %s.zeichnung[0].fest' % (ST, ST), 8000), S.evaluate(ST + '.zeichnung.length'))
    check('Session: … und das Steuerfenster', LK.evaluate(ST + '.zeichnung.length') == 1)
    c.close()

    check('keine Skriptfehler', not errs, errs[:3])
    b.close()

print('\n%d bestanden, %d fehlgeschlagen' % (ok, fehl))
sys.exit(1 if fehl else 0)
