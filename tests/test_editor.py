# -*- coding: utf-8 -*-
"""Editor (editor.html): neue Themenebene anlegen, auf dem Globus ansehen, Änderung vorschlagen.

    python tests/test_editor.py

Benötigt playwright und Microsoft Edge oder Chromium (wie die übrigen Browsertests).
"""
import json, mimetypes, os, sys, urllib.parse
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'http://localhost:8765/'
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


def fehlerliste(pg): return pg.eval_on_selector_all('#pFehler li', 'l => l.map(x => x.textContent)')


print('Editor')
with sync_playwright() as p:
    try: b = p.chromium.launch(channel='msedge', headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    except Exception: b = p.chromium.launch(headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    ctx = b.new_context(viewport={'width': 1400, 'height': 1000}, bypass_csp=True); ctx.route(URL + '**', serve)
    errs = []
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('dialog', lambda d: d.accept())
    pg.goto(URL + 'editor.html'); pg.wait_for_selector('[data-start]'); pg.wait_for_timeout(800)
    pg.evaluate("localStorage.removeItem('cg.editor.entwurf')"); pg.reload(); pg.wait_for_timeout(1000)

    # --- 1. neue Themenebene ---
    check('0. Startseite mit vier Kacheln', pg.locator('[data-start]').count() == 4 and pg.is_visible('#start'))
    pg.click('[data-start="neue-ebene"]')
    check('1. Ebenen-Teil sichtbar', pg.is_visible('#teilEbene') and pg.is_visible('#karte'))
    check('1. leerer Beitrag hat Fehler', len(fehlerliste(pg)) >= 4, fehlerliste(pg))
    check('1. GitHub-Knopf gesperrt', pg.get_attribute('#aGithub', 'aria-disabled') == 'true')
    pg.fill('#eName', 'Pyramiden im Alten Ägypten')
    pg.fill('#eBeschreibung', 'Große Königspyramiden des Alten Reiches im Raum Memphis.')
    pg.fill('#eQuellen input.breit', 'Lehner, Mark: The Complete Pyramids. London 1997.')
    pg.click('[data-neu="punkt"]')
    pg.fill('#oName', 'Cheops-Pyramide'); pg.fill('#oVon', '-2560')
    # Klick auf die Karte bei 31,13° O / 29,98° N (Plattkarte 960×480: x = (lng+180)/360·960, y = (90−lat)/180·480)
    box = pg.locator('#karte').bounding_box()
    x = box['x'] + (31.13 + 180) / 360 * box['width']; y = box['y'] + (90 - 29.98) / 180 * box['height']
    pg.mouse.click(x, y); pg.wait_for_timeout(300)
    k = json.loads(pg.text_content('#pJson'))['ebene']['objekte'][0]['koordinaten']
    check('1. Kartenklick setzt den Ort', k and abs(k[0] - 31.13) < 0.6 and abs(k[1] - 29.98) < 0.6, k)
    pg.fill('#oLat', '29.979'); pg.fill('#oLng', '31.134'); pg.press('#oLng', 'Tab')
    pg.click('[data-neu="linie"]'); pg.fill('#oName', 'Nil bei Memphis'); pg.fill('#oVon', '-2700')
    box = pg.locator('#karte').bounding_box()
    for lng, lat in ((31.25, 31.0), (32.5, 28.5), (31.0, 25.5)):
        pg.mouse.click(box['x'] + (lng + 180) / 360 * box['width'], box['y'] + (90 - lat) / 180 * box['height'])
    pg.fill('#bTitel', 'Neue Ebene: Pyramiden im Alten Ägypten')
    pg.fill('#bBegruendung', 'Die Pyramiden zeigen Staatlichkeit und Arbeitsorganisation im Alten Reich.')
    pg.fill('#bBelege input.breit', 'Lehner, Mark: The Complete Pyramids. London 1997, S. 108–119.')
    pg.wait_for_timeout(300)
    check('1. vollständiger Beitrag ohne Fehler', fehlerliste(pg) == [], fehlerliste(pg))
    beitrag = json.loads(pg.text_content('#pJson'))
    e = beitrag['ebene']
    check('1. Ebene: id aus dem Namen', e['id'] == 'pyramiden-im-alten-aegypten', e['id'])
    check('1. Objekte: Punkt und Linie', [o['typ'] for o in e['objekte']] == ['punkt', 'linie'] and len(e['objekte'][1]['koordinaten']) == 3, e['objekte'])
    check('1. Punkt aus Breite/Länge', e['objekte'][0]['koordinaten'] == [31.134, 29.979], e['objekte'][0]['koordinaten'])
    href = pg.get_attribute('#aGithub', 'href') or ''
    q = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
    check('1. GitHub-Link: neue Datei in beitraege/', href.startswith('https://github.com/') and '/new/main' in href and q.get('filename', [''])[0].startswith('beitraege/'), href[:120])
    check('1. GitHub-Link enthält den Beitrag', json.loads(q.get('value', ['{}'])[0]) == beitrag)
    check('1. Entwurf bleibt nach Neuladen', (pg.reload(), pg.wait_for_timeout(1200), pg.input_value('#eName'))[2] == 'Pyramiden im Alten Ägypten')

    # --- 2. Vorschau auf dem Globus ---
    with ctx.expect_page() as neu:
        pg.click('#aVorschau')
    g = neu.value; g.on('pageerror', lambda e: errs.append('Globus: ' + str(e)))
    g.wait_for_function('window.__tafelbild', timeout=30000); g.wait_for_timeout(2500)
    check('2. Vorschau-Ebene im Menü und an', g.get_attribute('.chip.thema[data-thema="vorschau"]', 'aria-pressed') == 'true')
    check('2. Zeitleiste bleibt (Ebene ohne Ende ist im Startjahr sichtbar)', g.evaluate('__tafelbild.state.year') == 117, g.evaluate('__tafelbild.state.year'))
    pts = g.evaluate("__tafelbild.globe.pointsData().filter(d => d.themaort).map(d => d.o.name)")
    pfade = g.evaluate("__tafelbild.globe.pathsData().filter(d => d.themalinie).map(d => d.themalinie.name)")
    check('2. Ort und Linie auf dem Globus', pts == ['Cheops-Pyramide'] and pfade == ['Nil bei Memphis'], (pts, pfade))
    check('2. Vorschau steht nicht im geteilten Zustand', 'vorschau' not in g.evaluate('__tafelbild.getState().themen'))
    g.evaluate("__tafelbild.setState({jahr: -2650}); 0"); g.wait_for_timeout(500)
    check('2. vor dem Bau nicht sichtbar', g.evaluate("__tafelbild.globe.pointsData().filter(d => d.themaort).length") == 0)
    g.close()
    # Ebene, die im Startjahr nicht sichtbar ist: die Zeitleiste springt an ihren Anfang
    for i in (0, 1):   # beiden Objekten ein Ende geben
        pg.click('#oListe .objekt >> nth=%d' % i); pg.fill('#oBis', '-1500'); pg.press('#oBis', 'Tab')
    pg.wait_for_timeout(300)
    with ctx.expect_page() as neu:
        pg.click('#aVorschau')
    g = neu.value; g.wait_for_function('window.__tafelbild', timeout=30000); g.wait_for_timeout(2500)
    check('2. Zeitleiste springt an den Anfang der Ebene', g.evaluate('__tafelbild.state.year') == -2700, g.evaluate('__tafelbild.state.year'))
    g.close()

    # --- 3. Änderung an einem Reichsgebiet ---
    pg.click('#aNeu'); pg.wait_for_timeout(300)
    check('3. „Neu beginnen“ führt zur Startseite', pg.is_visible('#start'))
    pg.click('[data-start="aenderung"]')
    pg.select_option('#zBereich', 'reich-gebiet')
    wert = pg.evaluate("[...document.querySelectorAll('#zObjekt option')].find(o => /Dakien|Dacia/.test(o.textContent))?.value")
    check('3. Gebiet Dakien in der Auswahl', bool(wert), wert)
    if wert: pg.select_option('#zObjekt', wert)
    pg.wait_for_timeout(600)
    check('3. bisherige Werte angezeigt', pg.is_visible('#zAktuell') and 'von' in pg.text_content('#zAktuell'))
    check('3. bisherige Fläche grau auf der Karte', pg.evaluate("document.querySelectorAll('#karte .ref').length") >= 1)
    pg.fill('#vText', 'Provinzgründung 106 n. Chr. statt des bisherigen Jahres.'); pg.fill('#vVon', '106')
    pg.fill('#bTitel', 'Dakien: Jahr der Provinzgründung'); pg.fill('#bBegruendung', 'Die Provinz wurde nach dem zweiten Dakerkrieg 106 n. Chr. eingerichtet.')
    pg.fill('#bBelege input.breit', 'Der Neue Pauly, Art. Dacia.'); pg.wait_for_timeout(300)
    check('3. Änderung ohne Fehler', fehlerliste(pg) == [], fehlerliste(pg))
    a = json.loads(pg.text_content('#pJson'))
    check('3. Ziel und Vorschlag im Beitrag', a['ziel']['bereich'] == 'reich-gebiet' and a['ziel']['datei'] == 'data/reiche.json' and a['vorschlag']['felder'] == {'von': 106}, a.get('ziel'))
    check('3. keine Vorschau für Änderungen', not pg.is_visible('#aVorschau'))

    # --- 4. Rückgängig und Wiederholen ---
    pg.click('#aNeu'); pg.wait_for_timeout(300); pg.click('[data-start="neue-ebene"]')
    pg.click('[data-neu="punkt"]'); pg.fill('#oName', 'Ur'); pg.wait_for_timeout(500)
    pg.click('[data-neu="punkt"]'); pg.wait_for_timeout(500)
    check('4. zwei Objekte', pg.locator('#oListe .objekt').count() == 2)
    pg.click('#btnUndo'); pg.wait_for_timeout(300)
    check('4. Rückgängig entfernt das zweite Objekt', pg.locator('#oListe .objekt').count() == 1)
    pg.click('#btnRedo'); pg.wait_for_timeout(300)
    check('4. Wiederholen stellt es wieder her', pg.locator('#oListe .objekt').count() == 2)

    # --- 5. Punkt auf der Karte ziehen ---
    pg.click('#oListe .objekt >> nth=0'); pg.fill('#oLat', '30.0'); pg.fill('#oLng', '45.0'); pg.press('#oLng', 'Tab'); pg.wait_for_timeout(300)
    pg.click('#kWelt'); pg.wait_for_timeout(700)
    box = pg.locator('#karte').bounding_box()
    sx, sy = box['x'] + (45 + 180) / 360 * box['width'], box['y'] + (90 - 30) / 180 * box['height']
    pg.mouse.move(sx, sy); pg.mouse.down(); pg.mouse.move(sx + 20, sy + 10, steps=6); pg.mouse.up(); pg.wait_for_timeout(400)
    k = json.loads(pg.text_content('#pJson'))['ebene']['objekte'][0]['koordinaten']
    check('5. gezogener Punkt hat neue Koordinaten', k and k[0] > 45.5 and k[1] < 29.8, k)
    check('5. Ziehen setzt keinen zusätzlichen Punkt', json.loads(pg.text_content('#pJson'))['ebene']['objekte'][1]['koordinaten'] is None)

    # --- 6. KI-Assistent ---
    pg.click('#btnKi'); pg.wait_for_timeout(300)
    check('6. Dialog offen', pg.evaluate("document.getElementById('kiDialog').open"))
    pg.fill('#kiThema', 'Städte in Sumer'); pg.fill('#kiDaten', 'name;lat;lng;von\nUr;30.963;46.103;-3800')
    prompt = pg.input_value('#kiPrompt')
    check('6. Prompt enthält Datensatz, Thema und _editor', 'Ur;30.963;46.103;-3800' in prompt and 'Städte in Sumer' in prompt and '"_editor"' in prompt)
    pg.click('#kiTab2')
    antwort = {"format": "chronoglobe-beitrag/1", "art": "neue-ebene", "titel": "Neue Ebene: Städte in Sumer",
               "begruendung": "Die ersten Städte entstanden in Südmesopotamien.", "belege": [{"zitat": "Van De Mieroop, Marc: A History of the Ancient Near East. 3. Aufl. 2016."}],
               "ebene": {"format": "chronoglobe-ebene/1", "id": "staedte-in-sumer", "name": "Städte in Sumer", "farbe": "#4f86c6", "beschreibung": "Frühe Städte im Süden Mesopotamiens.",
                         "quellen": ["Van De Mieroop 2016"], "objekte": [{"name": "Ur", "typ": "punkt", "von": "um 3800 v. Chr.", "koordinaten": [46.103, 30.963]},
                                                                        {"name": "Uruk", "typ": "punkt", "von": -4000, "koordinaten": [45.636, 31.322]}]},
               "_editor": {"karte": {"zentrum": [45.9, 31.1], "zoom": 20}, "jahr": -3000, "pruefen": ["Gründungsjahr von Ur ist eine Schätzung."], "ausgelassen": ["Eridu: keine Koordinaten"]}}
    pg.fill('#kiAntwort', 'Gern! Hier ist die Datei:\n```json\n' + json.dumps(antwort, ensure_ascii=False, indent=1) + '\n```')
    pg.wait_for_timeout(600)
    check('6. Antwort erkannt', pg.is_visible('#kiErgebnis') and '2 Objekte' in pg.text_content('#kiErgebnis'), pg.text_content('#kiErgebnis'))
    pg.click('#kiErsetzen'); pg.wait_for_timeout(1200)
    b2 = json.loads(pg.text_content('#pJson'))
    check('6. übernommen: Ebene mit 2 Objekten', b2['ebene']['name'] == 'Städte in Sumer' and len(b2['ebene']['objekte']) == 2, b2.get('ebene', {}).get('name'))
    check('6. Jahr aus „um 3800 v. Chr.“', b2['ebene']['objekte'][0]['von'] == -3800)
    check('6. _editor nicht im Beitrag', '_editor' not in b2 and '_ki' not in b2)
    check('6. Prüfhinweis als Checkliste', pg.locator('#kiListe li').count() == 1 and pg.is_visible('#kiPruefen'))
    check('6. Zeitfilter auf das Jahr der KI', pg.is_checked('#zeitAn') and pg.input_value('#zeitJahr') == '-3000')
    check('6. Karte herangezoomt', pg.evaluate("d3.zoomTransform(document.getElementById('karte')).k") > 10)
    check('6. Status zeigt offenen Prüfhinweis', 'prüfen' in pg.text_content('#status'))
    pg.click('#kiListe input'); pg.wait_for_timeout(200)
    check('6. abgehakt → bereit', 'bereit' in pg.text_content('#status'), pg.text_content('#status'))

    # --- 7. Import einer CSV-Datei ---
    with pg.expect_file_chooser() as fc:
        pg.click('#oImport')
    fc.value.set_files(files=[{'name': 'zikkurate.csv', 'mimeType': 'text/csv', 'buffer': 'Name;Breite;Länge;von\nZikkurat von Ur;30,962;46,103;-2100\nEtemenanki;32,536;44,421;-600\n'.encode('utf-8')}])
    pg.wait_for_timeout(800)
    b3 = json.loads(pg.text_content('#pJson'))
    check('7. CSV-Objekte angehängt', [o['name'] for o in b3['ebene']['objekte']][-2:] == ['Zikkurat von Ur', 'Etemenanki'], [o['name'] for o in b3['ebene']['objekte']])
    check('7. Komma-Dezimalen gelesen', b3['ebene']['objekte'][-1]['koordinaten'] == [44.421, 32.536])
    check('keine Skriptfehler', not errs, errs[:3])
    b.close()

print('\n%d bestanden, %d fehlgeschlagen' % (ok, fehl))
sys.exit(1 if fehl else 0)
