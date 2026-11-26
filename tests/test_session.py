# -*- coding: utf-8 -*-
"""Live-Session mit zwei (bzw. drei) Browserfenstern über den lokalen Übertragungsweg (?sync=lokal, ohne Supabase).
Prüft: Landingpage, Session starten, Beitritt per QR-Link, alle vier Schülerrechte in beiden Stellungen, Fokus,
Filter, „Fenster mitsenden“, „Alle zurück“, Nachzügler, Reload beider Seiten, Leuchtstift der Lehrkraft, Sperren, Beenden.

    python tests/test_session.py

Benötigt: playwright und Microsoft Edge oder Chromium. Die Supabase-Anbindung selbst (RPCs, private Kanäle) kann
dieser Test NICHT prüfen; dafür docs/SETUP.md, Abschnitt „Prüfen“.
"""
import json, mimetypes, os, sys, tempfile, urllib.parse
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


def warte(pg, js, ms=6000):
    try: pg.wait_for_function(js, timeout=ms); return True
    except Exception: return False


ST = 'ChronoGlobe.getState()'
with sync_playwright() as p:
    try: b = p.chromium.launch(channel='msedge', headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    except Exception: b = p.chromium.launch(headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    ctx = b.new_context(viewport={'width': 1400, 'height': 900}, bypass_csp=True); ctx.route(URL + '**', serve)
    errs = []
    def neu():
        pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('dialog', lambda d: d.accept()); return pg
    print('ChronoGlobe – Live-Session (lokal)')

    # --- Landingpage und Session starten ---
    L = neu(); L.goto(URL + 'index.html?sync=lokal'); L.wait_for_timeout(800)
    check('Landing: vier Bereiche', L.locator('.kachel').count() == 4)
    check('Landing: Galerie zeigt das Tafelbild', warte(L, "document.querySelectorAll('#galerie .karte').length >= 1"))
    check('Landing: Session-Bereich aktiv (lokal)', L.is_visible('#btnStarten'))
    L.click('#btnStarten'); warte(L, "document.querySelector('#nsCode').textContent.length >= 4")
    code = L.inner_text('#nsCode')
    check('Session gestartet: Code, Link, QR', len(code) >= 4 and 'code=' + code in L.get_attribute('#nsLink', 'href') and warte(L, "document.querySelector('#nsQr canvas, #nsQr img')"), code)
    lehrer_url = L.get_attribute('#nsOeffnen', 'href')

    T = neu(); T.goto(lehrer_url); warte(T, 'window.ChronoGlobe', 15000); T.wait_for_timeout(1500)
    T.evaluate("ChronoGlobe.setState({ drehen: false })")
    check('Lehrkraft: Lehrermenü mit Code', T.is_visible('.cg-lehrer') and T.inner_text('.cg-code') == code)

    S = neu(); S.goto(URL + 'index.html?code=' + code + '&sync=lokal'); warte(S, 'window.ChronoGlobe', 15000); S.wait_for_timeout(1500)
    check('Schüler: Beitritt über QR-Link (index.html?code=…)', 'session=' + code in S.url and 'rolle=schueler' in S.url)
    check('Schüler: kein Menü, kein Lehrermenü, Statusanzeige', not S.is_visible('#panel') and not S.is_visible('.cg-lehrer') and S.is_visible('.cg-badge'))
    check('Lehrkraft sieht anonyme Teilnehmerzahl', warte(T, "/^1 /.test(document.querySelector('#cgAnzahl').textContent)", 8000), T.inner_text('#cgAnzahl'))

    # --- Standard: alle Rechte „nur Lehreransicht“ ---
    T.evaluate("ChronoGlobe.setState({ jahr: -50 })")
    check('1a Zeitriegel folgt der Lehrkraft', warte(S, ST + '.jahr === -50'), S.evaluate(ST + '.jahr'))
    S.evaluate("ChronoGlobe.setState({ jahr: 300 })"); S.wait_for_timeout(300)
    check('1a eigene Zeit-Eingabe gesperrt', S.evaluate(ST + '.jahr') == -50 and S.evaluate("getComputedStyle(document.querySelector('#play')).pointerEvents") == 'none')
    T.click('#fokus-china');
    check('2a Fokus „China“ bei allen', warte(S, 'Math.abs(' + ST + '.kamera.lng - 108) < 3', 6000), S.evaluate(ST + '.kamera'))
    check('2a Globus drehen/zoomen gesperrt', S.evaluate('ChronoGlobe.globe.controls().enabled') is False)
    T.evaluate("ChronoGlobe.setState({ kamera: { lat: 10, lng: 20, alt: 1.5 } })")
    check('2a Kamera folgt laufend', warte(S, 'Math.abs(' + ST + '.kamera.lng - 20) < 2', 5000))
    S.evaluate("document.querySelector('#cards .card button') && document.querySelector('#cards .card button').click()"); S.wait_for_timeout(400)
    check('3a eigene Schriftrolle gesperrt', S.evaluate(ST + '.fenster.rolle') is None)
    T.click('#cards .card button');
    check('3a Schriftrolle der Lehrkraft erscheint', warte(S, ST + ".fenster.rolle && " + ST + ".fenster.rolle.reich === 'rom'"))
    T.click('#tabKarte'); check('3a Reiter folgt', warte(S, ST + ".fenster.rolle && " + ST + ".fenster.rolle.reiter === 'karte'"))
    T.click('#mapClose'); check('3a Schließen folgt', warte(S, ST + '.fenster.rolle === null'))
    T.wait_for_timeout(1700)
    T.click('#tglHandel'); check('Filter: Handel an bei allen', warte(S, ST + '.handel.on === true'))
    T.click('#tglStr'); check('Filter: Römerstraßen bei allen', warte(S, ST + '.handel.strassen === true'))
    T.evaluate("ChronoGlobe.setState({ jahr: 117 })"); warte(S, ST + '.jahr === 117')
    rid = T.evaluate("(document.querySelector('#routeList .rl-item:not(.str):not(.orbis)') || {}).textContent || ''")
    T.click('#routeList .rl-item:not(.str):not(.orbis) >> nth=0')
    check('4a Schülertext der Lehrkraft erscheint', warte(S, ST + ".fenster.info && " + ST + ".fenster.info.art === 'text'"), rid.strip())
    S.evaluate("ChronoGlobe.setState({ fenster: { info: { art: 'strassen' } } })"); S.wait_for_timeout(300)
    check('4a eigene Infokarte gesperrt', S.evaluate(ST + ".fenster.info.art") == 'text')
    T.keyboard.press('Escape'); check('4a Schließen folgt', warte(S, ST + '.fenster.info === null'))

    # --- Rechte auf „selbst bedienen“ ---
    for k in ('zeit', 'globus', 'reiche', 'routen'): T.click('.cg-seg button[data-recht="%s"][data-wert="selbst"]' % k)
    check('Rechte übertragen', warte(S, "CGSession.schueler.rechte().routen === 'selbst' && CGSession.schueler.rechte().zeit === 'selbst'"))
    S.evaluate("ChronoGlobe.setState({ jahr: 200 })")
    check('1b eigene Zeit möglich', S.evaluate(ST + '.jahr') == 200)
    check('1b Hinweis „Zur Lehreransicht zurück“', warte(S, "!document.querySelector('.cg-zurueck').hidden", 2000))
    T.evaluate("ChronoGlobe.setState({ jahr: 100 })"); T.wait_for_timeout(900)
    check('1b nach Abweichung bleibt die eigene Zeit', S.evaluate(ST + '.jahr') == 200)
    S.click('.cg-zurueck'); check('1b „Zur Lehreransicht zurück“ holt die Lehrerzeit', warte(S, ST + '.jahr === 100'))
    check('2b Globus bedienbar', S.evaluate('ChronoGlobe.globe.controls().enabled') is True)
    S.mouse.move(700, 350); S.mouse.down(); S.mouse.move(760, 360, steps=5); S.mouse.up(); S.wait_for_timeout(200)   # echtes Ziehen
    S.evaluate("ChronoGlobe.globe.pointOfView({ lat: -20, lng: -60, altitude: 2 }, 0); 0")
    T.evaluate("ChronoGlobe.setState({ kamera: { lat: 45, lng: 10, alt: 1.2 } })"); T.wait_for_timeout(900)
    check('2b eigene Kamera bleibt nach Abweichung', abs(S.evaluate(ST + '.kamera.lng') + 60) < 3, S.evaluate(ST + '.kamera'))
    T.click('.cg-lehrer >> text=Aktuelle Ansicht für alle')
    check('2b „Aktuelle Ansicht für alle“ setzt den Fokus trotzdem', warte(S, 'Math.abs(' + ST + '.kamera.lng - 10) < 3', 5000))
    # Sendetakt (js/synctakt.js): bei „Globus selbst bedienen“ keine Nachricht für reine Kamerabewegungen
    S.evaluate("window.__n = 0; window.__bc = new BroadcastChannel('cg.lokal." + code + "'); __bc.onmessage = e => { if (e.data.ev === 'state') __n++; }; 0")
    T.wait_for_timeout(600); S.evaluate('window.__n = 0')
    for i in range(4): T.evaluate("ChronoGlobe.setState({ kamera: { lat: 30, lng: %d, alt: 1.4 } })" % (20 + 5 * i)); T.wait_for_timeout(250)
    T.wait_for_timeout(1200)
    check('Takt: Globus frei → reine Kamerabewegung sendet nichts', S.evaluate('window.__n') == 0, S.evaluate('window.__n'))
    T.evaluate("ChronoGlobe.setState({ jahr: 120 })")
    check('Takt: Jahreswechsel wird trotzdem gesendet', warte(S, 'window.__n >= 1', 3000))
    check('Takt: Anzeige im Lehrermenü', 'Updates/s' in (T.get_attribute('#cgAnzahl', 'title') or ''), T.get_attribute('#cgAnzahl', 'title'))
    T.evaluate("ChronoGlobe.setState({ jahr: 100 })"); T.wait_for_timeout(800)   # Ausgangsjahr für die folgenden Schritte
    S.evaluate('__bc.close(); 0')
    S.click('#cards .card button')
    check('3b eigene Schriftrolle möglich', warte(S, ST + '.fenster.rolle !== null', 3000))
    T.wait_for_timeout(600); check('3b bleibt lokal (Lehrkraft unverändert)', T.evaluate(ST + '.fenster.rolle') is None)
    S.click('#mapClose'); S.wait_for_timeout(1700)
    S.evaluate("ChronoGlobe.setState({ fenster: { info: { art: 'strassen' } } })")
    check('4b eigene Infokarte möglich', warte(S, ST + ".fenster.info && " + ST + ".fenster.info.art === 'strassen'", 2000))
    T.wait_for_timeout(600); check('4b bleibt lokal', T.evaluate(ST + '.fenster.info') is None)
    T.click('#btnWaren'); check('4b Lehrkraft öffnet Fenster → erscheint trotzdem bei allen', warte(S, ST + ".fenster.waren === 'handel'"))
    T.click('#wmodalClose'); warte(S, ST + '.fenster.waren === null')

    # --- Fenster mitsenden aus ---
    T.click('#cgFenster'); T.wait_for_timeout(500)
    T.click('#btnWaren'); T.wait_for_timeout(1200)
    check('Fenster mitsenden aus: Warenübersicht nicht bei Schüler:innen', S.evaluate(ST + '.fenster.waren') is None)
    T.click('#wmodalClose'); T.click('#cgFenster'); T.wait_for_timeout(400)

    # --- Alle zurück ---
    S.evaluate("ChronoGlobe.setState({ jahr: 300 })")
    T.click('.cg-lehrer >> text=Alle zurück zu meiner Ansicht')
    check('„Alle zurück“: Zeit und Fenster wie Lehrkraft', warte(S, ST + '.jahr === 100 && ' + ST + '.fenster.info === null'))
    check('„Alle zurück“: Hinweis verschwindet', warte(S, "document.querySelector('.cg-zurueck').hidden", 2000))

    # --- Nachzügler, Reload ---
    T.evaluate("ChronoGlobe.setState({ jahr: 250, reiche: { parth: true } })"); T.wait_for_timeout(800)
    N = neu(); N.goto(URL + 'app.html?session=' + code + '&rolle=schueler&sync=lokal'); warte(N, 'window.ChronoGlobe', 15000)
    check('Nachzügler bekommt den aktuellen Stand', warte(N, ST + '.jahr === 250 && ' + ST + '.reiche.parth === true', 8000))
    S.reload(); warte(S, 'window.ChronoGlobe', 15000)
    check('Reload Schüler: aktueller Stand', warte(S, ST + '.jahr === 250', 8000))
    T.reload(); warte(T, 'window.ChronoGlobe', 15000); T.wait_for_timeout(1200)
    check('Reload Lehrkraft: Lehrermenü und Zustand bleiben', T.is_visible('.cg-lehrer') and T.evaluate(ST + '.jahr') == 250 and T.evaluate(ST + '.reiche.parth') is True)
    check('Reload Lehrkraft: Rechte bleiben', T.get_attribute('.cg-seg button[data-recht="zeit"][data-wert="selbst"]', 'aria-pressed') == 'true')

    # --- Weltbilder ---
    T.evaluate("ChronoGlobe.setState({ weltbild: { id: 'ebstorf', projektion: true } })")
    check('Weltbild der Lehrkraft erscheint bei Schüler:innen', warte(S, ST + ".weltbild.id === 'ebstorf'", 8000))
    T.evaluate("ChronoGlobe.setState({ fenster: { weltkarte: { id: 'ebstorf' } } })")
    check('Schriftrolle mit der Karte öffnet sich bei allen', warte(S, ST + ".fenster.weltkarte && " + ST + ".fenster.weltkarte.id === 'ebstorf'", 6000))
    T.keyboard.press('Escape')
    check('… und schließt sich wieder', warte(S, ST + '.fenster.weltkarte === null', 6000))
    T.evaluate("ChronoGlobe.setState({ weltbild: { id: null } })"); warte(S, ST + '.weltbild.id === null', 6000)

    # --- Leuchtstift der Lehrkraft ---
    Z = ST + '.zeichnung'
    check('Stift: Leiste nur bei der Lehrkraft', T.is_visible('.stift-leiste .stift-an') and not S.is_visible('.stift-leiste'))
    T.evaluate("ChronoGlobe.setState({ kamera: { lat: 45, lng: 10, alt: 1.6 }, drehen: false })"); T.wait_for_timeout(1200)
    mitte = T.evaluate("(() => { const r = document.querySelector('#globe').getBoundingClientRect(), q = ChronoGlobe.globe.getScreenCoords(45, 10, 0); return [r.left + q.x, r.top + q.y]; })()")

    def strich(dx0, dy0, dx1, dy1):
        T.mouse.move(mitte[0] + dx0, mitte[1] + dy0); T.mouse.down()
        T.mouse.move(mitte[0] + dx1, mitte[1] + dy1, steps=14); T.mouse.up(); T.wait_for_timeout(200)
    T.click('.stift-an')
    check('Stift an: Werkzeuge sichtbar, Globus nicht mehr drehbar per Ziehen', T.is_visible('.stift-w[data-w="marker"]') and T.evaluate("document.documentElement.classList.contains('stift-an')"))
    strich(-90, 0, 90, 30)
    check('Stift: Strich bei der Lehrkraft (vorläufig)', T.evaluate(Z + '.length === 1 && !' + Z + '[0].fest && ' + Z + '[0].p.length >= 8'), T.evaluate(Z + '.map(s => s.p.length)'))
    check('Stift: Strich erscheint bei Schüler:innen', warte(S, Z + '.length === 1', 5000))
    T.click('.stift-fest')
    check('„Stehen lassen“ kommt an', warte(S, Z + '.length === 1 && ' + Z + '[0].fest', 5000))
    T.click('.stift-w[data-w="marker"]'); strich(-60, -70, 60, -70)
    check('Marker: zweiter Strich bei allen', warte(S, Z + ".length === 2 && " + Z + "[1].art === 'marker'", 5000))
    T.keyboard.press('Escape')
    check('Stift schließen (Esc): Vorläufiges weg, Stehengelassenes bleibt', warte(S, Z + '.length === 1 && ' + Z + '[0].fest', 5000) and not T.evaluate("document.documentElement.classList.contains('stift-an')"))
    S.wait_for_timeout(300); S.screenshot(path=os.path.join(tempfile.gettempdir(), 'chronoglobe_stift_schueler.png'))   # zum Ansehen
    T.click('.stift-an'); T.click('.stift-w[data-w="radierer"]'); strich(0, -40, 0, 50)
    check('Radierer entfernt den Strich bei allen', warte(S, Z + '.length === 0', 5000), S.evaluate(Z + '.length'))
    T.click('.stift-w[data-w="stift"]'); strich(-40, 20, 40, 20); T.click('.stift-fest'); T.keyboard.press('Escape')
    warte(S, Z + '.length === 1 && ' + Z + '[0].fest', 5000)
    T.reload(); warte(T, 'window.ChronoGlobe', 15000); T.wait_for_timeout(1200)
    check('Reload Lehrkraft: stehen gelassene Beschriftung bleibt', T.evaluate(Z + '.length === 1 && ' + Z + '[0].fest'))
    T.click('.stift-alle'); check('„Alles löschen“ bei allen', warte(S, Z + '.length === 0', 5000))

    # --- Schüleransicht anpassen (schueler_ui) ---
    S.reload(); warte(S, 'window.ChronoGlobe', 15000); S.wait_for_timeout(1200)
    sichtbar = lambda pg, sel: pg.evaluate("(() => { const e = document.querySelector('%s'); return !!e && e.getClientRects().length > 0 && getComputedStyle(e).display !== 'none'; })()" % sel)
    check('UI Standard: kein Menü, keine Suche, Infokarten und Spuren sichtbar',
          not sichtbar(S, '#panel') and not sichtbar(S, '#sucheFeld') and sichtbar(S, '#side') and sichtbar(S, '#lanes'))
    check('UI: Lehrermenü „Schüleransicht anpassen“ mit fünf Schaltern', T.locator('#cgUi input[data-ui]').count() == 5)
    T.click('#cgUi summary')
    for k in ('reiche', 'ebenen', 'suche'): T.check('#cgUi input[data-ui="%s"]' % k)
    for k in ('infokarten', 'spuren'): T.uncheck('#cgUi input[data-ui="%s"]' % k)
    check('UI: Schülergerät zeigt Reiche-Liste und Ebenen-Schalter', warte(S, "document.documentElement.classList.contains('cg-ui-ebenen')", 6000)
          and sichtbar(S, '#panel') and sichtbar(S, '.ps-reiche') and sichtbar(S, '#handelSec') and not sichtbar(S, '.ps-ansicht') and not sichtbar(S, '.cg-lehrer'))
    check('UI: Suche freigeschaltet, Infokarten und Spuren ausgeblendet', sichtbar(S, '#sucheFeld') and not sichtbar(S, '#side') and not sichtbar(S, '#lanes'))
    lokal = lambda: json.loads(S.evaluate("localStorage.getItem('cg.lokal." + code + "')"))
    vorher = lokal()
    S.click('.chip.nb[data-r="kusch"]'); S.wait_for_timeout(300)
    check('Filter lokal: eigenes Reich nur auf dem Schülergerät', S.evaluate(ST + '.reiche.kusch') is True and T.evaluate(ST + '.reiche.kusch') is False)
    check('Filter lokal: Hinweis „Zur Lehreransicht zurück“', warte(S, "!document.querySelector('.cg-zurueck').hidden", 2000))
    T.evaluate("ChronoGlobe.setState({ jahr: 150 })"); warte(S, ST + '.jahr === 150 || true', 3000); T.wait_for_timeout(900)
    check('Filter lokal bleibt, wenn die Lehrkraft anderes ändert', S.evaluate(ST + '.reiche.kusch') is True)
    T.evaluate("ChronoGlobe.setState({ handel: { on: true } })")
    check('Filter der Lehrkraft gilt weiter für alle', warte(S, ST + '.handel.on === true', 5000))
    S.click('#tglHandel'); S.wait_for_timeout(300); T.evaluate("ChronoGlobe.setState({ jahr: 160 })"); T.wait_for_timeout(900)
    check('Eigene Ebene (Handel aus) bleibt lokal', S.evaluate(ST + '.handel.on') is False and T.evaluate(ST + '.handel.on') is True)
    T.evaluate("ChronoGlobe.setState({ handel: { on: false } })"); T.wait_for_timeout(700); T.evaluate("ChronoGlobe.setState({ handel: { on: true } })")
    check('Neue Einstellung der Lehrkraft für denselben Filter gilt wieder', warte(S, ST + '.handel.on === true', 5000))
    nachher = lokal()
    check('Datenschutz: Schülergerät schreibt nichts (gespeicherter Zustand ohne Schülerfilter)',
          nachher['state']['reiche'].get('kusch') is False and nachher['schueler_ui']['suche'] is True and nachher['seq'] >= vorher['seq'])
    T.click('.cg-lehrer >> text=Alle zurück zu meiner Ansicht')
    check('„Alle zurück“ setzt lokale Filter zurück', warte(S, ST + '.reiche.kusch === false', 5000))
    for k in ('zeit', 'globus'): T.click('.cg-seg button[data-recht="%s"][data-wert="selbst"]' % k)
    warte(S, "CGSession.schueler.rechte().globus === 'selbst'", 4000)
    tj = T.evaluate(ST + '.jahr')
    S.keyboard.press('/'); S.type('#sucheFeld', 'Carrhae'); S.wait_for_timeout(300); S.keyboard.press('Enter')
    check('Suche auf dem Schülergerät wirkt nur lokal', warte(S, ST + '.jahr === -53', 5000) and T.evaluate(ST + '.jahr') == tj, [S.evaluate(ST + '.jahr'), T.evaluate(ST + '.jahr')])
    S.reload(); warte(S, 'window.ChronoGlobe', 15000); S.wait_for_timeout(1200)
    check('Reload Schüler: Schüleransicht bleibt', sichtbar(S, '#panel') and sichtbar(S, '#sucheFeld') and not sichtbar(S, '#side'))
    S.click('.chip.nb[data-r="kusch"]'); S.wait_for_timeout(300)
    T.click('#cgUi >> text=Standard (kein Menü)')
    check('„Standard“: Menü und Suche wieder weg, Infokarten zurück', warte(S, "!document.documentElement.classList.contains('cg-ui-reiche')", 6000)
          and not sichtbar(S, '#panel') and not sichtbar(S, '#sucheFeld') and sichtbar(S, '#side'))
    check('„Standard“: Filter folgen wieder der Lehrkraft', warte(S, ST + '.reiche.kusch === false', 5000))
    T.reload(); warte(T, 'window.ChronoGlobe', 15000); T.wait_for_timeout(1000)
    check('Reload Lehrkraft: Schüleransicht bleibt gespeichert', T.is_checked('#cgUi input[data-ui="infokarten"]') and not T.is_checked('#cgUi input[data-ui="suche"]'))

    # --- Sperren, Beenden ---
    T.click('.cg-lehrer >> text=Session sperren'); T.wait_for_timeout(400)
    G = neu(); G.goto(URL + 'app.html?session=' + code + '&rolle=schueler&sync=lokal')
    check('Gesperrt: neuer Beitritt abgewiesen', warte(G, "document.querySelector('.cg-sperre') && /gesperrt/i.test(document.querySelector('.cg-sperre').textContent)", 15000))
    check('Gesperrt: Verbundene bleiben', S.evaluate("!document.querySelector('.cg-sperre')"))
    T.click('.cg-lehrer >> text=Session öffnen'); T.wait_for_timeout(300)
    T.click('.cg-lehrer >> text=Session beenden')
    check('Beenden: Schüler:innen sehen „Session beendet“', warte(S, "document.querySelector('.cg-sperre') && /beendet/.test(document.querySelector('.cg-sperre').textContent)", 6000))
    check('Beenden: Daten gelöscht', S.evaluate("localStorage.getItem('cg.lokal." + code + "')") is None)
    U = neu(); U.goto(URL + 'app.html?session=' + code + '&rolle=schueler&sync=lokal')
    check('Beendete Session: Code ungültig', warte(U, "document.querySelector('.cg-sperre') && /keine Session/.test(document.querySelector('.cg-sperre').textContent)", 15000))
    # --- Voreinstellung der Schüleransicht aus tafelbild.json (schueler_ui) ---
    ctx2 = b.new_context(viewport={'width': 1400, 'height': 900}, bypass_csp=True); ctx2.route(URL + '**', serve)
    def mit_ui(route):
        u = urllib.parse.urlparse(route.request.url); fp = os.path.join(ROOT, urllib.parse.unquote(u.path.lstrip('/')))
        d = json.load(open(fp, encoding='utf-8')); d['schueler_ui'] = {'ebenen': True, 'infokarten': False}
        route.fulfill(status=200, content_type='application/json', body=json.dumps(d))
    ctx2.route('**/tafelbilder/*/tafelbild.json*', mit_ui)
    L2 = ctx2.new_page(); L2.on('pageerror', lambda e: errs.append(str(e))); L2.goto(URL + 'index.html?sync=lokal'); L2.wait_for_timeout(800)
    L2.click('#btnStarten'); warte(L2, "document.querySelector('#nsCode').textContent.length >= 4")
    code2 = L2.inner_text('#nsCode')
    T2 = ctx2.new_page(); T2.goto(L2.get_attribute('#nsOeffnen', 'href')); warte(T2, 'window.ChronoGlobe', 15000); T2.wait_for_timeout(1200)
    S2 = ctx2.new_page(); S2.goto(URL + 'app.html?session=' + code2 + '&rolle=schueler&sync=lokal'); warte(S2, 'window.ChronoGlobe', 15000); S2.wait_for_timeout(1200)
    check('Voreinstellung aus tafelbild.json: Lehrermenü übernimmt sie', T2.is_checked('#cgUi input[data-ui="ebenen"]') and not T2.is_checked('#cgUi input[data-ui="infokarten"]'))
    check('Voreinstellung aus tafelbild.json: Schülergerät zeigt Ebenen, keine Infokarten',
          warte(S2, "document.documentElement.classList.contains('cg-ui-ebenen') && document.documentElement.classList.contains('cg-ui-ohne-infokarten')", 6000))

    check('keine Skriptfehler', not errs, '; '.join(errs[:3]))
    b.close()

print('\n%d bestanden, %d fehlgeschlagen' % (ok, fehl))
sys.exit(1 if fehl else 0)
