# -*- coding: utf-8 -*-
"""Weltbilder (data/weltbilder/, build_weltbilder.py) in den Tafelbildern „Die Welt nach Plinius“ und
„Die Ebstorfer Weltkarte“: Einträge, Hülle auf dem Globus, Schriftrolle, Umschalten im freien Modus.

    python tests/test_weltbilder.py
"""
import json, mimetypes, os, sys, urllib.parse
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'http://localhost:8765/'
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


# Hülle: Kugelausschnitt mit eigener Textur, etwas über dem Globus
HUELLE = """(() => { let h = null; ChronoGlobe.globe.scene().traverse(o => { const p = o.geometry && o.geometry.parameters;
  if (o.isMesh && p && Math.abs(p.radius - 100.16) < 0.01) h = { phiLen: p.phiLength, sichtbar: o.visible, textur: !!o.material.map,
    eigeneTextur: !!o.material.map && o.material.map.source !== ChronoGlobe.globe.globeMaterial().map.source, deck: o.material.opacity }; }); return h; })()"""
ST = 'ChronoGlobe.getState()'

daten = {w['id']: json.load(open(os.path.join(ROOT, 'data', 'weltbilder', w['id'] + '.json'), encoding='utf-8'))
         for w in json.load(open(os.path.join(ROOT, 'data', 'weltbilder', 'index.json'), encoding='utf-8'))['weltbilder']}
print('ChronoGlobe – Weltbilder')
for wid, d in daten.items():
    check('Daten %s: Einträge mit Beleg' % wid, all(e.get('beleg') for e in d['eintraege']) and len(d['eintraege']) >= 100, len(d['eintraege']))
    check('Daten %s: Projektion vorhanden' % wid, os.path.isfile(os.path.join(ROOT, d['projektion']['datei'])))
check('Ebstorf: Kachelpyramide und viele Datenpunkte', os.path.isfile(os.path.join(ROOT, daten['ebstorf']['bild']['kacheln'], '0', '0_0.jpg')) and len(daten['ebstorf']['eintraege']) >= 100)
check('Plinius: jeder Eintrag mit Stelle, Bücher 3–6 mit Wortlaut und Seite bei Wittstein', all(e['beleg'].startswith('Plinius, Naturgeschichte') for e in daten['plinius']['eintraege'])
      and all(e.get('zitat') and 'S. ' in e.get('zitat_beleg', '') for e in daten['plinius']['eintraege'] if int(e['beleg'].split()[-1].split(',')[0]) <= 6))

with sync_playwright() as p:
    try: b = p.chromium.launch(channel='msedge', headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    except Exception: b = p.chromium.launch(headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    errs = []

    def seite(adresse):
        pg = b.new_page(viewport={'width': 1400, 'height': 900}, bypass_csp=True); pg.route(URL + '**', serve)
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(URL + adresse); pg.wait_for_function('window.ChronoGlobe', timeout=30000); pg.wait_for_timeout(5000)
        return pg

    # --- Plinius ---
    pg = seite('app.html?tafelbild=welt-nach-plinius')
    st = pg.evaluate(ST)
    check('Plinius: Start mit Weltbild und Hülle', st['weltbild']['id'] == 'plinius' and st['weltbild']['projektion'] is True and st['jahr'] == 77, st['weltbild'])
    n = len(daten['plinius']['eintraege']) + len(daten['plinius']['route']['stationen'])
    check('Plinius: alle Einträge und Stationen der Indienfahrt auf dem Globus', pg.evaluate("document.querySelectorAll('.wb-schild').length") == n)
    check('Plinius: Seeweg nach Indien als Linie', pg.evaluate("ChronoGlobe.globe.pathsData().filter(d => d.wbRoute).length") == 1)
    check('Plinius: keine Reichsflächen', pg.evaluate("ChronoGlobe.globe.polygonsData().length") == 0)
    h = pg.evaluate(HUELLE)
    check('Plinius: Hülle über die ganze Erde, eigene Textur', h and abs(h['phiLen'] - 6.2832) < 0.01 and h['sichtbar'] and h['eigeneTextur'], h)
    pg.click('.wb-schild:has-text("Taprobane")', force=True); pg.wait_for_timeout(300)
    check('Plinius: Infokarte mit Stelle und Wortlaut', 'Plinius, Naturgeschichte 6,81' in pg.inner_text('#tinfo') and 'Wittstein' in pg.inner_text('#tinfo') and pg.evaluate(ST + '.fenster.info.art') == 'weltbild')
    check('Plinius: keine Schriftrolle (keine Karte)', pg.is_hidden('#btnWbRolle'))
    pg.evaluate("ChronoGlobe.setState({ weltbild: { projektion: false } })"); pg.wait_for_timeout(300)
    check('Hülle abschaltbar', pg.evaluate(HUELLE) is None)
    pg.close()

    # --- Ebstorf ---
    pg = seite('app.html?tafelbild=ebstorfer-weltkarte')
    st = pg.evaluate(ST)
    check('Ebstorf: Jahr 1300 erreichbar (Mittelalter in der Zeitleiste)', st['jahr'] == 1300, st['jahr'])
    ort = [e for e in daten['ebstorf']['eintraege'] if 'lng' in e]
    check('Ebstorf: Datenpunkte an wirklicher Lage, ohne verzerrte Karte, keine Reiche', pg.evaluate(HUELLE) is None and pg.evaluate("document.querySelectorAll('.wb-schild').length") == len(ort)
          and pg.evaluate("document.querySelectorAll('.wb-schild.auf-karte').length") == 0 and pg.evaluate("ChronoGlobe.globe.polygonsData().length") == 0)
    check('Ebstorf: Jerusalem hervorgehoben', pg.evaluate("!!document.querySelector('.wb-schild.mitte') && document.querySelector('.wb-schild.mitte').textContent.includes('Jerusalem')"))
    pg.evaluate("ChronoGlobe.setState({ weltbild: { projektion: true } })"); pg.wait_for_timeout(2500)
    h = pg.evaluate(HUELLE)
    check('Ebstorf: Karte auf Wunsch verzerrt aufgelegt', h and abs(h['phiLen'] - 3.1416) < 0.01 and h['eigeneTextur'], h)
    check('Ebstorf: dann Einträge auf der Karte, Verzerrungslinien', pg.evaluate("document.querySelectorAll('.wb-schild.auf-karte').length") == len(ort)
          and pg.evaluate("ChronoGlobe.globe.pathsData().filter(d => d.wbLinie).length") >= 100)
    pg.evaluate("ChronoGlobe.setState({ weltbild: { deckkraft: 0.4 } })"); pg.wait_for_timeout(200)
    check('Deckkraft wirkt', abs(pg.evaluate(HUELLE)['deck'] - 0.4) < 0.01)
    pg.click('#btnWbRolle'); pg.wait_for_timeout(1800)
    check('Schriftrolle öffnet mit Originalkarte und Datenpunkten', pg.is_visible('#wbBild') and pg.evaluate(ST + '.fenster.weltkarte.id') == 'ebstorf'
          and pg.evaluate("document.querySelectorAll('.wb-punkt').length") == len(daten['ebstorf']['eintraege']))
    pg.click('.wb-punkt[data-id="jerusalem"]', force=True); pg.wait_for_timeout(300)
    check('Raute zeigt Erläuterung', 'Jerusalem' in pg.inner_text('#wbAside'))
    z0 = pg.evaluate("getComputedStyle(document.querySelector('#wbFlaeche')).transform")
    for i in range(6): pg.click('#wbZoomIn'); pg.wait_for_timeout(120)
    pg.wait_for_timeout(1500)
    check('Zoomen lädt schärfere Kacheln', pg.evaluate("getComputedStyle(document.querySelector('#wbFlaeche')).transform") != z0
          and pg.evaluate("Math.max(...[...document.querySelectorAll('#wbKacheln .wb-ebene:not([hidden])')].map(e => +e.dataset.z))") >= 3)
    pg.click('#wbAside >> text=Auf dem Globus zeigen'); pg.wait_for_timeout(2000)
    st = pg.evaluate(ST)
    check('„Auf dem Globus zeigen“: Vergleichsansicht, Kamera bei Jerusalem', st['fenster']['weltkarte'] == {'id': 'ebstorf', 'neben': True} and abs(st['kamera']['lng'] - 35.2) < 2
          and pg.evaluate("document.documentElement.classList.contains('wb-neben')"), st['kamera'])
    pg.evaluate("document.querySelector('.wb-punkt[data-id=koeln]').click()"); pg.wait_for_timeout(1800)
    check('Vergleichsansicht: Klick auf der Karte zeigt den Ort auf dem Globus', abs(pg.evaluate(ST + '.kamera.lng') - 6.96) < 1.5)
    pg.evaluate("ChronoGlobe.setState({ fenster: { weltkarte: null } })"); pg.wait_for_timeout(900)
    pg.evaluate("ChronoGlobe.setState({ fenster: { weltkarte: { id: 'ebstorf', neben: false } } })"); pg.wait_for_timeout(1500)
    check('Rolle über den Zustand öffnen (Live-Session)', pg.is_visible('#wbBild') and not pg.evaluate("document.documentElement.classList.contains('wb-neben')"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(700)
    check('Esc schließt die Rolle', pg.evaluate(ST + '.fenster.weltkarte') is None)
    pg.close()

    # --- freier Modus: Umschalten ---
    pg = seite('app.html?modus=frei')
    check('Frei: Menü mit beiden Weltbildern', pg.evaluate("document.querySelectorAll('#wbChips .chip').length") == 2)
    pg.click('#wbChips .chip[data-wb="ebstorf"]'); pg.wait_for_timeout(2500)
    check('Frei: Ebstorf eingeschaltet (ohne verzerrte Karte)', pg.evaluate(ST + '.weltbild.id') == 'ebstorf' and pg.evaluate(HUELLE) is None and pg.evaluate("document.querySelectorAll('.wb-schild').length") > 100)
    pg.click('#wbChips .chip[data-wb="plinius"]'); pg.wait_for_timeout(2500)
    h = pg.evaluate(HUELLE)
    check('Frei: Wechsel zu Plinius ersetzt die Hülle', pg.evaluate(ST + '.weltbild.id') == 'plinius' and h and abs(h['phiLen'] - 6.2832) < 0.01)
    pg.click('#wbChips .chip[data-wb="plinius"]'); pg.wait_for_timeout(500)
    check('Frei: ausschalten', pg.evaluate(ST + '.weltbild.id') is None and pg.evaluate(HUELLE) is None and pg.evaluate("document.querySelectorAll('.wb-schild').length") == 0)
    check('Grundtextur des Globus unverändert', pg.evaluate("ChronoGlobe.globe.globeMaterial().map.image.src.indexOf('weltbilder') < 0"))
    pg.close()
    check('keine Skriptfehler', not errs, '; '.join(errs[:3]))
    b.close()

print('\n%d bestanden, %d fehlgeschlagen' % (ok, fehl))
sys.exit(1 if fehl else 0)
