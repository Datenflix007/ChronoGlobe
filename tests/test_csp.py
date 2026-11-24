# -*- coding: utf-8 -*-
"""Content-Security-Policy (js/csp.js): Datenschutzregel technisch erzwungen.

Prüft je Seite: Richtlinie gesetzt, Anfrage an einen fremden Server blockiert (außer Supabase auf Session-Seiten),
und im normalen Betrieb (Ebenen an, Nahansicht mit Kacheln) keine CSP-Verstöße und keine Skriptfehler.

    python tests/test_csp.py

Hinweis: Die übrigen Browsertests laufen mit bypass_csp=True, weil Playwrights wait_for_function intern eval nutzt
(das die Richtlinie zu Recht verbietet). Dieser Test wartet deshalb ohne wait_for_function.
"""
import mimetypes, os, sys, time, urllib.parse
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INIT = ("window.__csp = []; document.addEventListener('securitypolicyviolation',"
        " e => window.__csp.push(e.violatedDirective + ' ' + e.blockedURI));")
ok, fehl = 0, 0


def serve(route):
    u = urllib.parse.urlparse(route.request.url)
    fp = os.path.join(ROOT, urllib.parse.unquote(u.path.lstrip('/')))
    if os.path.isfile(fp): route.fulfill(path=fp, content_type=mimetypes.guess_type(fp)[0] or 'application/octet-stream')
    else: route.fulfill(status=404, body='nicht gefunden')


def check(name, bed, info=''):
    global ok, fehl
    if bed: ok += 1; print('  ok   ' + name)
    else: fehl += 1; print('  FEHL ' + name + ('  ' + str(info) if info else ''))


def warte(pg, ausdruck, sek=30):
    ende = time.time() + sek
    while time.time() < ende:
        if pg.evaluate('!!(' + ausdruck + ')'): return True
        pg.wait_for_timeout(200)
    return False


SEITEN = [  # Seite, warten auf, Supabase erlaubt?
    ('app.html?modus=frei', 'window.__tafelbild', False),
    ('app.html?tafelbild=rom-zentrum-der-welt', 'window.__tafelbild', False),
    ('app.html?session=TEST01&rolle=schueler&sync=lokal', None, True),
    ('index.html', None, True),
    ('quellen.html', None, False),
    ('lehrkraft.html', None, False),
    ('editor.html', None, False),
]

print('Content-Security-Policy')
with sync_playwright() as p:
    try: b = p.chromium.launch(channel='msedge', headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    except Exception: b = p.chromium.launch(headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    for seite, bereit, supa in SEITEN:
        pg = b.new_page(viewport={'width': 1300, 'height': 900}); pg.route('http://localhost:8765/**', serve); pg.add_init_script(INIT)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto('http://localhost:8765/' + seite)
        if bereit: check(seite + ': geladen', warte(pg, bereit))
        pg.wait_for_timeout(2500)
        if bereit:   # alle großen Ebenen an, nah heran (Kacheln)
            pg.evaluate("window.__tafelbild.setState({handel:{on:true, strassen:true, schiff:true, hanseide:true}, globus:{limes:true, orte:true}});"
                        " window.__tafelbild.globe.pointOfView({lat:41.9, lng:12.5, altitude:0.1}, 0); 0")
            pg.wait_for_timeout(3000)
        csp = pg.evaluate("(document.querySelector('meta[http-equiv=Content-Security-Policy]') || {}).content || ''")
        check(seite + ': Richtlinie gesetzt', "connect-src 'self'" in csp, csp)
        check(seite + ': Supabase ' + ('erlaubt' if supa else 'gesperrt'), ('supabase.co' in csp) == supa, csp)
        extern = pg.evaluate("fetch('https://example.org/x').then(() => 'erlaubt', () => 'blockiert')")
        check(seite + ': fremder Server blockiert', extern == 'blockiert', extern)
        verstoesse = [v for v in pg.evaluate('window.__csp') if 'example.org' not in v]
        check(seite + ': keine Verstöße im Betrieb', not verstoesse, verstoesse[:5])
        check(seite + ': keine Skriptfehler', not errs, errs[:3])
        pg.close()
    b.close()

print('\n%d bestanden, %d fehlgeschlagen' % (ok, fehl))
sys.exit(1 if fehl else 0)
