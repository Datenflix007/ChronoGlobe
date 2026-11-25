# -*- coding: utf-8 -*-
"""Browsertest für die Handels- und Verkehrsnetze (lädt die echte App ohne Webserver).

    python tests/test_netze_browser.py [ordner-für-bildschirmfotos]

Prüft: Mittelalter-Teil der Zeitleiste nur im freien Erkunden, Menü, Testjahre, keine fremden Server,
bestehende Ebenen unverändert, Zustand (getState/applyState), Infokarten, Tafelbilder unberührt.
Benötigt: playwright (pip install playwright) und Microsoft Edge oder Chromium.
"""
import mimetypes, os, sys, urllib.parse
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else None
U = 'http://localhost:8765/'
T = '__tafelbild'
ok, fehl = 0, 0
ALLE = ['petra_gaza', 'tang', 'viatariq', 'thurayya', 'mongolen']
ERWARTET = {-300: ['petra_gaza'], 100: ['petra_gaza'], 430: [], 700: ['tang', 'viatariq'], 850: ['tang', 'thurayya', 'viatariq'],
            1050: ['viatariq'], 1250: ['mongolen', 'viatariq'], 1350: ['mongolen', 'viatariq'], 1440: ['viatariq']}


def check(name, bed, info=''):
    global ok, fehl
    if bed: ok += 1; print('  ok   ' + name + (' – ' + info if info else ''))
    else: fehl += 1; print('  FEHL ' + name + (' – ' + info if info else ''))


def serve(route):
    u = urllib.parse.urlparse(route.request.url)
    fp = os.path.join(ROOT, urllib.parse.unquote(u.path.lstrip('/')))
    if os.path.isfile(fp): route.fulfill(path=fp, content_type=mimetypes.guess_type(fp)[0] or 'application/octet-stream')
    else: route.fulfill(status=404, body='nicht gefunden')


def netze_sichtbar(pg):
    return pg.evaluate("[...new Set(ChronoGlobe.globe.pathsData().filter(d => d.netzlinie).map(d => d.netzM.id))].sort()")


def andere(pg):
    return pg.evaluate("ChronoGlobe.globe.pathsData().filter(d => !d.netzlinie).map(d => d.id).sort().join(',') + '|' + "
                       "ChronoGlobe.globe.polygonsData().length + '|' + ChronoGlobe.globe.htmlElementsData().length + '|' + "
                       "ChronoGlobe.globe.pointsData().filter(d => !d.netzort).length")


with sync_playwright() as p:
    try: b = p.chromium.launch(channel='msedge', headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    except Exception: b = p.chromium.launch(headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    pg = b.new_page(viewport={'width': 1500, 'height': 950}, bypass_csp=True)
    fremd = []
    pg.route('**/*', lambda r: serve(r) if r.request.url.startswith(U) else (fremd.append(r.request.url), r.abort()))
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    print('Handels- und Verkehrsnetze – Browsertest')

    pg.goto(U + 'app.html'); pg.wait_for_function('window.ChronoGlobe'); pg.wait_for_timeout(1500)
    pg.evaluate("ChronoGlobe.setState({drehen:false}); 0")
    ep = pg.evaluate("[...document.querySelectorAll('#epbar .ep')].map(e => e.querySelector('b').textContent)")
    check('1. freies Erkunden: Zeitleiste mit Teil „Mittelalter“, kein Zeitsprung', 'Mittelalter' in ep and pg.evaluate("!document.querySelector('#epbar .epgap')"), ', '.join(ep))
    pg.evaluate(T + ".setYear(700); 0")
    check('2. Jahr 700 ist einstellbar (keine Lücke 480–1400)', pg.evaluate(T + '.state.year') == 700)
    chips = pg.evaluate("[...document.querySelectorAll('.chip.netz')].map(e => e.dataset.netz)")
    check('3. Menü: fünf Netze in Gruppen, aufklappbar', sorted(chips) == sorted(ALLE) and pg.evaluate("!!document.querySelector('#netzBox summary')"), ','.join(chips))
    check('3b. Reiseberichte in eigener Gruppe', pg.evaluate("!!document.querySelector('.netz-gruppe[data-gruppe=\"reise\"] .chip.netz[data-netz=\"mongolen\"]')"))

    pg.evaluate(T + ".setYear(100); " + T + ".applyState({handel:{on:true, strassen:true, schiff:true}, globus:{limes:true}}); 0"); pg.wait_for_timeout(500)
    vorher = andere(pg)
    pg.evaluate("document.querySelector('#netzBox').open = true; 0")
    for n in ALLE: pg.click('.chip.netz[data-netz="%s"]' % n); pg.wait_for_timeout(150)
    pg.evaluate(T + ".setYear(100); 0"); pg.wait_for_timeout(1500)
    check('4. alle Netze geladen', pg.evaluate("Object.keys(%s.netze.daten).sort().join(',')" % T) == ','.join(sorted(ALLE)))
    check('5. bestehende Ebenen unverändert (Straßen, ORBIS, Limes, Flächen, Beschriftungen)', andere(pg) == vorher)
    check('6. keine Anfragen an fremde Server', not fremd, ', '.join(fremd[:3]))

    for y, erw in ERWARTET.items():
        pg.evaluate(T + ".setYear(%d); 0" % y); pg.wait_for_timeout(200)
        da = netze_sichtbar(pg)
        check('7. Jahr %d: %s' % (y, ', '.join(erw) or 'keine neuen Netze'), da == erw, ','.join(da))
        if OUT and y in (850, 1250, 1440): pg.screenshot(path=os.path.join(OUT, 'netze_%d.png' % y))

    st = pg.evaluate("ChronoGlobe.getState().netze")
    check('8. getState enthält die Netze', st == {n: True for n in ALLE}, str(st))
    pg.evaluate("ChronoGlobe.applyState({netze:{tang:false, thurayya:false}, jahr:850}, {quelle:'lehrer'}); 0"); pg.wait_for_timeout(300)
    check('9. applyState schaltet Netze (Live-Session)', netze_sichtbar(pg) == ['viatariq'] and pg.evaluate("document.querySelector('.chip.netz[data-netz=\"tang\"]').getAttribute('aria-pressed')") == 'false')

    pg.evaluate("ChronoGlobe.setState({fenster:{info:{art:'netzlinie', netz:'viatariq', id:'vt-early_mamluk-1'}}}); 0"); pg.wait_for_timeout(500)
    txt = pg.evaluate("document.querySelector('#tinfoBody').innerText")
    check('10. Infokarte: Post-Route gekennzeichnet, Quelle und Lizenz', 'keine Handelsroute' in txt and 'CC BY 4.0' in txt and 'Pažout' in txt)
    pg.evaluate("ChronoGlobe.setState({fenster:{info:{art:'netzquellen'}}}); 0"); pg.wait_for_timeout(300)
    txt = pg.evaluate("document.querySelector('#tinfoBody').innerText")
    check('11. Quellenübersicht mit nicht übernommenen Quellen und Grund', 'Quellenübersicht' in txt and 'Ming-Zeit' in txt and 'Epochen mischen' in txt and 'OWTRAD' in txt)
    if OUT: pg.screenshot(path=os.path.join(OUT, 'netze_quellen.png'))
    pg.keyboard.press('Escape')

    # Tafelbilder: kein Mittelalter-Teil, Netze ausgeblendet, Zeitsprung wie bisher
    # 11b. Alles ein- und ausblenden (nur freier Modus)
    pg.goto(U + 'app.html?modus=frei'); pg.wait_for_function('window.ChronoGlobe'); pg.wait_for_timeout(1500)
    check('11b. Knöpfe „Alles einblenden/ausblenden“ im freien Modus', pg.is_visible('#allesAn') and pg.is_visible('#allesAus'))
    pg.click('#allesAn'); pg.wait_for_timeout(2500)
    st = pg.evaluate(T + '.getState()')
    alle = lambda d: bool(d) and all(d.values())
    check('11b. alles an: Reiche, Globus, Handel, Netze, Themen, Zheng He', alle(st['reiche']) and alle(st['globus']) and alle(st['handel']) and alle(st['netze']) and alle(st['themen']) and st['zh']['on'] and alle(st['zh']['fahrten']),
          str({k: st[k] for k in ('globus', 'handel')}))
    pg.evaluate(T + ".setYear(-480); 0"); pg.wait_for_timeout(1500)
    check('11b. 480 v. Chr.: Athen, Sparta und Perser sichtbar', set(pg.evaluate(T + ".globe.polygonsData().map(f => f.properties.reich)")) >= {'athen', 'sparta', 'perser'})
    pg.click('#allesAus'); pg.wait_for_timeout(1500)
    st = pg.evaluate(T + '.getState()')
    check('11b. alles aus: keine Reiche, keine Flächen, keine Pfade', not any(st['reiche'].values()) and not any(st['handel'].values()) and pg.evaluate(T + '.globe.polygonsData().length') == 0 and pg.evaluate(T + '.globe.pathsData().length') == 0)

    for tb, ep_erw in (('rom-zentrum-der-welt', ['Europäische Antike']), ('aufbruch-aus-europa', ['Europäisches Spätmittelalter'])):
        pg.goto(U + 'app.html?tafelbild=' + tb); pg.wait_for_function('window.ChronoGlobe'); pg.wait_for_timeout(1200)
        ep = pg.evaluate("[...document.querySelectorAll('#epbar .ep')].map(e => e.querySelector('b').textContent)")
        check('12. Tafelbild %s: Zeitleiste unverändert, Netze ausgeblendet' % tb, ep == ep_erw and pg.evaluate("document.querySelector('#netzSec').hidden"), ', '.join(ep))
        check('12. Tafelbild %s: kein „Alles einblenden“' % tb, not pg.is_visible('#allesAn'))
    pg.evaluate(T + ".setYear(700); 0")
    check('13. Tafelbild Aufbruch: Jahr bleibt im Zeitraum', pg.evaluate(T + '.state.year') == 1400, str(pg.evaluate(T + '.state.year')))

    check('14. keine Skriptfehler', not errs, '; '.join(errs[:3]))
    b.close()

print('\n%d ok, %d fehlgeschlagen' % (ok, fehl))
sys.exit(1 if fehl else 0)
