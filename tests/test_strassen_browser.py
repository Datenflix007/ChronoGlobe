# -*- coding: utf-8 -*-
"""Browsertest für den zeitabhängigen Römerstraßen-Layer (lädt die echte App ohne Webserver).

    python tests/test_strassen_browser.py [ordner-für-bildschirmfotos]

Benötigt: playwright (pip install playwright) und Microsoft Edge oder Chromium.
"""
import mimetypes, os, sys, urllib.parse
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else None
T = '__tafelbild'
ok, fehl = 0, 0


def check(name, bed, info=''):
    global ok, fehl
    if bed: ok += 1; print('  ok   ' + name + (' – ' + info if info else ''))
    else: fehl += 1; print('  FEHL ' + name + (' – ' + info if info else ''))


def serve(route):
    u = urllib.parse.urlparse(route.request.url)
    fp = os.path.join(ROOT, urllib.parse.unquote(u.path.lstrip('/')))
    if os.path.isfile(fp): route.fulfill(path=fp, content_type=mimetypes.guess_type(fp)[0] or 'application/octet-stream')
    else: route.fulfill(status=404, body='nicht gefunden')


with sync_playwright() as p:
    try: b = p.chromium.launch(channel='msedge', headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    except Exception: b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={'width': 1500, 'height': 950}); pg.route('http://localhost:8765/**', serve)
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_function('window.' + T); pg.wait_for_timeout(2500)
    pg.evaluate(T + '.globe.controls().autoRotate=false; ' + T + '.globe.pointOfView({lat:44,lng:12,altitude:1.1},0); 0')
    st = lambda: pg.evaluate(T + '.strassen()')
    jahr = lambda y: (pg.evaluate(T + '.setYear(%d)' % y), pg.wait_for_timeout(250))
    def ebenen():
        return pg.evaluate("(() => { const g = %s.globe; return { poly: g.polygonsData().length, labels: g.labelsData().length, html: g.htmlElementsData().length,"
                           " andere: g.pathsData().filter(d => !d.strasse).map(d => d.id).sort().join(',') }; })()" % T)
    print('Römerstraßen – Browsertest')
    check('1. alle Linien geladen', st()['geladen'] == 819, str(st()))

    jahr(117); vorher = ebenen()
    pg.click('#tglHandel'); pg.wait_for_timeout(200); ohne = ebenen()
    pg.click('#tglStr'); pg.wait_for_timeout(400); s117 = st(); mit = ebenen()
    check('7a. Layer an: Straßen auf dem Globus', s117['aufGlobus'] > 700, str(s117))
    check('10. übrige Ebenen unverändert', ohne['poly'] == mit['poly'] and ohne['labels'] == mit['labels'] and ohne['html'] == mit['html'] and ohne['andere'] == mit['andere'],
          'Flächen %d, Beschriftungen %d, HTML %d, andere Linien gleich' % (mit['poly'], mit['labels'], mit['html']))
    check('10b. ohne Handel ebenfalls gleich (Flächen/Beschriftungen)', vorher['poly'] == mit['poly'])
    if OUT: pg.screenshot(path=os.path.join(OUT, 'str_117.png'))

    jahr(-250); a = st()['aufGlobus']; jahr(-100); b1 = st()['aufGlobus']; jahr(100); c = st()['aufGlobus']
    check('2./3. Ausbau: wenige Linien 250 v. Chr., mehr 100 v. Chr., alle 100 n. Chr.', a < b1 < c == 819, '%d < %d < %d' % (a, b1, c))
    jahr(-100); check('3b. Ausbauphase zeigt teils eingeblendete Linien', 'ausbau' in st()['stile'], str(st()['stile']))
    if OUT: pg.screenshot(path=os.path.join(OUT, 'str_-100.png'))

    zust = []
    for y in (-200, -50, 50, 150, 300, 450): jahr(y); zust.append(st()['aufGlobus'])
    rueck = []
    for y in (450, 300, 150, 50, -50, -200): jahr(y); rueck.append(st()['aufGlobus'])
    check('8. Zurückspulen setzt die Zustände zurück', rueck[::-1] == zust, str(zust))
    for _ in range(3): pg.click('#yMinus'); pg.wait_for_timeout(120)
    for _ in range(3): pg.click('#yPlus'); pg.wait_for_timeout(120)
    check('8b. ±10 hin und zurück: gleicher Zustand', st()['aufGlobus'] == rueck[-1], str(st()))

    jahr(-1); pg.click('#yPlus'); pg.wait_for_timeout(200)
    check('Jahr 0: −1 + 10 = 10 n. Chr. (kein Jahr 0)', pg.inner_text('#yearOut') == '10 n. Chr.', pg.inner_text('#yearOut'))
    jahr(0); check('Jahr 0 wird übersprungen', pg.inner_text('#yearOut') in ('1 n. Chr.', '1 v. Chr.'), pg.inner_text('#yearOut'))

    jahr(470); s470 = st()
    check('5. Hauptmodus 470: Linien mit kürzerer Nutzung (Britannien bis 410) fehlen', s470['aufGlobus'] < 819, str(s470))
    pg.click('#panelToggle') if not pg.is_visible('#tglStrEhem') else None
    pg.click('#tglStrEhem'); pg.wait_for_timeout(300); r470 = st()
    check('5b. Referenzmodus 470: ehemalige Trassen gestrichelt sichtbar', r470['stile'].get('ehemals', 0) > 0 and r470['aufGlobus'] == 819, str(r470))
    pg.click('#tglStrEhem'); pg.wait_for_timeout(200)

    jahr(1440); pg.wait_for_timeout(1500); s1440 = st()
    check('6. 1440 Hauptmodus: keine aktive Straße', s1440['aufGlobus'] == 0, str(s1440))
    pg.click('#tglStrEhem'); pg.wait_for_timeout(500); r1440 = st()
    check('6b. 1440 Referenzmodus: nur ehemalige Trassen', r1440['aufGlobus'] == 819 and list(r1440['stile'].keys()) == ['ehemals'], str(r1440))
    if OUT:
        pg.evaluate(T + '.globe.pointOfView({lat:44,lng:12,altitude:1.1},0); 0'); pg.wait_for_timeout(1500)
        pg.screenshot(path=os.path.join(OUT, 'str_1440_ref.png'))

    jahr(117); pg.wait_for_timeout(800); pg.click('#tglStr'); pg.wait_for_timeout(400)
    check('7b. Layer aus: keine Straßen, unabhängig vom Jahr', st()['aufGlobus'] == 0, str(st()))
    pg.click('#tglStr'); pg.wait_for_timeout(300); pg.click('#tglRom'); pg.wait_for_timeout(300)
    check('7c. Römisches Reich ausgeblendet: keine Straßen', st()['aufGlobus'] == 0, str(st()))
    pg.click('#tglRom'); pg.wait_for_timeout(300)

    pg.click('#tglStrUns'); pg.wait_for_timeout(300)
    farben = pg.evaluate("[...new Set(%s.globe.pathsData().filter(d => d.strasse).map(d => d.L.datierung))]" % T)
    check('Datierung zeigen: drei Qualitätsstufen vorhanden', len(farben) == 3, str(farben))
    check('keine Skriptfehler', not errs, '; '.join(errs[:3]))
    b.close()

print('\n%d bestanden, %d fehlgeschlagen' % (ok, fehl))
sys.exit(1 if fehl else 0)
