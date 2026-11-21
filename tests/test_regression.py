# -*- coding: utf-8 -*-
"""Regressionstest für den freien Modus: feste Klickfolge, nach jedem Schritt ein Fingerabdruck
(Ebenen auf dem Globus, Fenster, Schalter, Jahr). Vergleicht mit tests/regression_baseline.json.

    python tests/test_regression.py --aufnehmen [seite]   # Ausgangszustand speichern (vor einem Umbau)
    python tests/test_regression.py [seite]               # vergleichen (Standard: app.html, sonst index.html)

Benötigt: playwright (pip install playwright) und Microsoft Edge oder Chromium. Lädt die App ohne Webserver
(Dateien werden direkt ausgeliefert).
"""
import hashlib, json, mimetypes, os, sys, urllib.parse
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASIS = os.path.join(ROOT, 'tests', 'regression_baseline.json')   # Ausgangszustand vor dem Umbau (freier Modus)
args = [a for a in sys.argv[1:] if not a.startswith('--')]
AUFNEHMEN = '--aufnehmen' in sys.argv
SEITE = args[0] if args else ('app.html?modus=frei' if os.path.exists(os.path.join(ROOT, 'app.html')) else 'index.html')
# Tafelbilder haben einen eigenen Ausgangszustand (sie zeigen bewusst nur einen Ausschnitt)
if 'tafelbild=' in SEITE:
    BASIS = os.path.join(ROOT, 'tests', 'regression_baseline_%s.json' % SEITE.split('tafelbild=')[1].split('&')[0])
T = '__tafelbild'


def serve(route):
    u = urllib.parse.urlparse(route.request.url)
    fp = os.path.join(ROOT, urllib.parse.unquote(u.path.lstrip('/')))
    if os.path.isfile(fp): route.fulfill(path=fp, content_type=mimetypes.guess_type(fp)[0] or 'application/octet-stream')
    else: route.fulfill(status=404, body='nicht gefunden')


FP_JS = """(() => {
  const T = window.%s, g = T.globe, q = s => document.querySelector(s);
  const h = a => a.slice().sort().join(',');
  const pressed = [...document.querySelectorAll('#panel button[aria-pressed]')].map(b => (b.dataset.netz ? 'netz:' + b.dataset.netz : b.id || b.dataset.r || b.dataset.nr || b.textContent.trim()) + '=' + b.getAttribute('aria-pressed'));
  return {
    jahr: q('#yearOut').textContent,
    state: { mode: T.state.mode, on: T.state.on, orte: T.state.orte, schlachten: T.state.schlachten, vw: T.state.vw, year: T.state.year, epoche: T.state.epoche, rotate: T.state.rotate },
    trade: T.trade, zh: { on: T.zh.on, fahrt: T.zh.fahrt },
    polys: h(g.polygonsData().map(f => String(f.properties.id !== undefined ? f.properties.id : f.properties.kind))),
    paths: h(g.pathsData().map(d => String(d.id))),
    labels: h(g.labelsData().map(d => String(d.name || d.id))),
    html: g.htmlElementsData().length,
    tinfo: q('#tinfo').hidden ? null : (q('#tinfoTitle') || {}).textContent,
    rolle: q('#mapOverlay').classList.contains('show') ? { tab: q('#tabVig').getAttribute('aria-selected'), kopf: (q('#vigView h2, #vigView h3') || {}).textContent } : null,
    waren: q('#wmodal').hidden ? null : q('#wmt').textContent,
    modal: !q('#modal').hidden, lmodal: !q('#lmodal').hidden,
    gedrueckt: pressed,
    karten: [...document.querySelectorAll('#cards .card')].map(c => (c.querySelector('.k') || {}).textContent)
  };
})()""" % T

ok, fehl, schritte = 0, 0, []
with sync_playwright() as p:
    try: b = p.chromium.launch(channel='msedge', headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    except Exception: b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={'width': 1500, 'height': 950}); pg.route('http://localhost:8765/**', serve)
    pg.add_init_script("try { localStorage.clear(); } catch (e) {}")
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://localhost:8765/' + SEITE); pg.wait_for_function('window.' + T); pg.wait_for_timeout(2500)

    def fp(name):
        pg.wait_for_timeout(350)
        schritte.append((name, pg.evaluate(FP_JS)))

    def klick(sel, warte=150):
        pg.click(sel); pg.wait_for_timeout(warte)

    klick('#tglRot'); fp('start')
    klick('#modeSchem'); fp('schematisch'); klick('#modeSat')
    klick('.chip.nb[data-r="parth"]'); fp('parther an')
    klick('#allOff'); fp('alle aus'); klick('#allOn'); fp('alle an'); klick('#allOff'); klick('#tglRom'); klick('#tglHan'); fp('nur rom han')
    klick('#tglOrte'); fp('orte'); klick('#tglVw'); fp('vw'); klick('#tglSchl'); fp('schlachten aus'); klick('#tglSchl'); klick('#tglVw')
    pg.evaluate(T + '.setYear(-100)'); fp('jahr -100')
    klick('#yPlus'); fp('+10'); klick('#yMinus'); klick('#yMinus'); fp('-10 -10')
    pg.keyboard.press('ArrowRight'); fp('pfeil rechts'); pg.keyboard.press('Shift+ArrowLeft'); fp('shift pfeil links')
    pg.evaluate(T + '.setYear(117)'); fp('jahr 117')
    klick('#tglHandel'); fp('handel an')
    for s in ('#tglLand', '#tglSee', '#tglWaren', '#tglGes', '#tglKar', '#tglSchiff', '#tglStr'):
        klick(s); fp('klick ' + s)
    klick('#tglLand'); klick('#tglSee'); fp('land see wieder an')
    klick('#tglStrEhem'); fp('ehemalige trassen'); klick('#tglStrAnim'); fp('animieren aus')
    pg.click('#routeList .rl-item.str'); pg.wait_for_timeout(300); fp('routenliste straßen'); pg.keyboard.press('Escape')
    pg.click('#routeList .rl-item:not(.str):not(.orbis) >> nth=0'); pg.wait_for_timeout(300); fp('routenliste 1')
    if pg.is_visible('.tx-daten'): klick('.tx-daten'); fp('daten zur route')
    if pg.is_visible('#tinfo .tmore >> text=Warenübersicht'): klick('#tinfo .tmore >> text=Warenübersicht'); fp('warenübersicht aus infokarte')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150); fp('esc 1'); pg.keyboard.press('Escape'); pg.wait_for_timeout(150); fp('esc 2')
    klick('#btnWaren'); fp('btn waren'); klick('#wmodalClose')
    klick('#cards .card button'); pg.wait_for_timeout(600); fp('schriftrolle')
    klick('#tabKarte'); fp('reiter karte'); klick('#tabVig')
    klick('#vigView .vg-karte >> nth=0'); fp('vignette 1')
    klick('#mapClose', 1800); fp('rolle zu')
    pg.evaluate("document.querySelector('#routeList .rl-item.orbis') && document.querySelector('#routeList .rl-item.orbis').click()"); fp('orbis info'); pg.keyboard.press('Escape')
    if pg.is_visible('#btnZhGo'):
        klick('#btnZhGo', 2500); fp('ming 1405')
        klick('#zhChips .chip >> nth=1'); fp('fahrt 2 aus'); klick('#tglBilder'); fp('bilder'); klick('#tglZh'); fp('zh aus'); klick('#tglZh')
    else:   # Tafelbild ohne Spätmittelalter
        for n in ('ming 1405', 'fahrt 2 aus', 'bilder', 'zh aus'): schritte.append((n, None))
    klick('#btnInfo'); fp('erste schritte'); pg.keyboard.press('Escape')
    if pg.is_visible('#btnLehrer'): klick('#btnLehrer'); fp('lehrerhinweise'); pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    else: schritte.append(('lehrerhinweise', None))   # Freier Modus: keine Lehrerhinweise (gewollt)
    pg.evaluate(T + '.setYear(117)'); pg.wait_for_timeout(1500)
    klick('#fokus-rom', 1800)
    pov = pg.evaluate(T + '.globe.pointOfView()')
    schritte.append(('kamera rom', {'pov': [round(pov['lat'], 1), round(pov['lng'], 1), round(pov['altitude'], 2)]}))
    fp('ende')
    schritte.append(('skriptfehler', {'fehler': errs}))
    b.close()

if AUFNEHMEN:
    json.dump(schritte, open(BASIS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Ausgangszustand gespeichert:', len(schritte), 'Schritte →', os.path.relpath(BASIS, ROOT))
    sys.exit(0)

basis = json.load(open(BASIS, encoding='utf-8'))
# Frühe Hochkulturen (data/fruehe_reiche.json) kamen nach dem Ausgangszustand hinzu: im Vergleich herausrechnen
try: NEU = set(json.load(open(os.path.join(ROOT, 'data', 'fruehe_reiche.json'), encoding='utf-8'))['meta'])
except Exception: NEU = set()
# Häfen des Zheng He erscheinen, sobald die Zeichenanimation sie erreicht – zeitabhängig, daher nicht verglichen
try: HAEFEN = {o['name'] for o in json.load(open(os.path.join(ROOT, 'data', 'zhenghe.json'), encoding='utf-8'))['orte']}
except Exception: HAEFEN = set()
def ohne_haefen(e):
    if isinstance(e, dict) and isinstance(e.get('labels'), str):
        t = e['labels']
        for n in sorted(HAEFEN, key=len, reverse=True): t = t.replace(n, '')   # Namen können Kommas enthalten
        e['labels'] = ','.join(x for x in t.split(',') if x)
    return e
def ohne_neue(e):
    if not isinstance(e, dict): return e
    # neue Schalter nach dem Ausgangszustand (Seidenstraße der Han, Limes, Handels- und Verkehrsnetze; standardmäßig aus)
    if 'gedrueckt' in e: e['gedrueckt'] = [x for x in e['gedrueckt'] if x.split('=')[0] not in NEU and x.split('=')[0] not in ('tglHanSeide', 'tglLimes') and not x.startswith('netz:')]
    if isinstance(e.get('trade'), dict) and e['trade'].get('hanseide') is False: del e['trade']['hanseide']
    if 'state' in e and isinstance(e['state'].get('on'), dict): e['state']['on'] = {k: v for k, v in e['state']['on'].items() if k not in NEU}
    return e
for (n1, a), (n2, e) in zip(basis, schritte):
    e = ohne_haefen(ohne_neue(json.loads(json.dumps(e)))); a = ohne_haefen(ohne_neue(json.loads(json.dumps(a))))
    if e is None: print('  --   ' + n1 + ' (in diesem Modus nicht vorhanden)'); continue
    if a == e: ok += 1; print('  ok   ' + n1)
    else:
        fehl += 1; print('  FEHL ' + n1)
        for k in sorted(set(a) | set(e)):
            if a.get(k) != e.get(k): print('       %s: vorher %s\n       %s  nachher %s' % (k, str(a.get(k))[:300], ' ' * len(k), str(e.get(k))[:300]))
if len(basis) != len(schritte): fehl += 1; print('  FEHL Zahl der Schritte: %d statt %d' % (len(schritte), len(basis)))
print('\n%d gleich, %d abweichend (%s)' % (ok, fehl, SEITE))
sys.exit(1 if fehl else 0)
