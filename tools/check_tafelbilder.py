# -*- coding: utf-8 -*-
"""Prüft alle Tafelbilder: tafelbilder/index.json und jedes tafelbilder/<id>/tafelbild.json.

    python tools/check_tafelbilder.py

Geprüft werden Pflichtfelder und Typen, id = Ordnername, Startansicht, Zeitraum (ohne Jahr 0), Reiche (gegen
data/reiche.json), Ebenen, Fokuspunkte, Lehrerhinweise und alle referenzierten Dateien (Vorschaubild, Markdown,
Daten-Overlays, die gültiges JSON sein müssen). Ordner, die mit „_“ beginnen (z. B. _vorlage), werden als Vorlage
nur auf gültiges JSON geprüft. Rückgabewert 1 bei Fehlern – nach jeder Kernänderung ausführen (CLAUDE.md).
"""
import io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TB = os.path.join(ROOT, 'tafelbilder')
EBENEN = {'orte', 'schlachten', 'vw', 'limes', 'geo', 'handel', 'land', 'see', 'waren', 'gesandt', 'karawanen', 'strassen', 'schiff', 'hanseide', 'zh', 'bilder', 'netze'}
AKTIV_EXTRA = {'strassen_ehemals', 'strassen_animieren'}
DATEN = {'reiche', 'handel', 'zhenghe', 'texte', 'literatur', 'roemerstrassen', 'orbis_schiff', 'vignetten', 'fruehe_reiche', 'han_seidenstrasse', 'limes', 'netze'}
# Handels- und Verkehrsnetze (data/netze/index.json): Datenschlüssel netz_<id>, in ebenen.aktiv.netze als Liste von ids
try:
    NETZ_IDS = {n['id'] for n in json.load(io.open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'netze', 'index.json'), encoding='utf-8'))['netze'] if n.get('status') == 'verfuegbar'}
except (OSError, ValueError, KeyError):
    NETZ_IDS = set()
DATEN |= {'netz_' + i for i in NETZ_IDS}
fehler, warnungen = [], []


def F(tb, msg): fehler.append('%s: %s' % (tb, msg))
def W(tb, msg): warnungen.append('%s: %s' % (tb, msg))


def lade(p):
    with io.open(p, encoding='utf-8') as f: return json.load(f)


def jahr_ok(j): return isinstance(j, int) and j != 0 and -5000 < j < 3000


reiche = set(lade(os.path.join(ROOT, 'data', 'reiche.json'))['meta'].keys())
reiche |= {'ming'}

try: index = lade(os.path.join(TB, 'index.json'))
except Exception as e: print('FEHLER tafelbilder/index.json:', e); sys.exit(1)
ids = [e.get('id') for e in index.get('tafelbilder', [])]
if len(ids) != len(set(ids)): F('index.json', 'doppelte IDs')
for d in sorted(os.listdir(TB)):
    if os.path.isdir(os.path.join(TB, d)) and not d.startswith('_') and d not in ids: W('index.json', 'Ordner „%s“ ist nicht eingetragen' % d)

for d in sorted(os.listdir(TB)):
    if d.startswith('_') and os.path.isdir(os.path.join(TB, d)):
        try: lade(os.path.join(TB, d, 'tafelbild.json'))
        except Exception as e: F(d, 'Vorlage: tafelbild.json ungültig: %s' % e)

for tid in ids:
    ordner = os.path.join(TB, tid or '')
    if not tid or not re.match(r'^[a-z0-9][a-z0-9-]{0,59}$', tid): F(str(tid), 'ungültige ID (a–z, 0–9, Bindestrich, max. 60 Zeichen)'); continue
    p = os.path.join(ordner, 'tafelbild.json')
    if not os.path.isfile(p): F(tid, 'tafelbild.json fehlt'); continue
    try: t = lade(p)
    except Exception as e: F(tid, 'tafelbild.json ist kein gültiges JSON: %s' % e); continue
    for k, typ in (('id', str), ('titel', str), ('untertitel', str), ('beschreibung', str), ('vorschaubild', str),
                   ('zeitraum', dict), ('start', dict), ('reiche', dict), ('ebenen', dict), ('fokuspunkte', list)):
        if k not in t: F(tid, 'Pflichtfeld „%s“ fehlt' % k)
        elif not isinstance(t[k], typ): F(tid, '„%s“ hat den falschen Typ' % k)
    if t.get('id') != tid: F(tid, 'id „%s“ passt nicht zum Ordnernamen' % t.get('id'))
    if isinstance(t.get('vorschaubild'), str) and not os.path.isfile(os.path.join(ordner, t['vorschaubild'])): F(tid, 'Vorschaubild fehlt: %s' % t['vorschaubild'])
    z = t.get('zeitraum') or {}
    if not (jahr_ok(z.get('von')) and jahr_ok(z.get('bis')) and z['von'] < z['bis']): F(tid, 'zeitraum.von/bis ungültig (ganze Jahre, kein Jahr 0, von < bis)')
    st = t.get('start') or {}
    if 'jahr' in st and not jahr_ok(st['jahr']): F(tid, 'start.jahr ungültig')
    elif 'jahr' in st and z.get('von') is not None and not (z['von'] <= st['jahr'] <= z['bis']): F(tid, 'start.jahr liegt außerhalb des Zeitraums')
    if st.get('ansicht') not in (None, 'sat', 'schem'): F(tid, 'start.ansicht muss „sat“ oder „schem“ sein')
    fp_ids = []
    for i, f in enumerate(t.get('fokuspunkte') or []):
        n = 'fokuspunkte[%d]' % i
        if not isinstance(f, dict): F(tid, n + ' ist kein Objekt'); continue
        for k in ('id', 'name'):
            if not isinstance(f.get(k), str) or not f.get(k): F(tid, '%s.%s fehlt' % (n, k))
        if not isinstance(f.get('lat'), (int, float)) or not -90 <= f['lat'] <= 90: F(tid, n + '.lat ungültig')
        if not isinstance(f.get('lng'), (int, float)) or not -180 <= f['lng'] <= 180: F(tid, n + '.lng ungültig')
        a = f.get('alt', 'standard')
        if not (a == 'standard' or (isinstance(a, (int, float)) and 0.05 <= a <= 6)): F(tid, n + '.alt: Zahl 0,05–6 oder „standard“')
        if 'jahr' in f and not jahr_ok(f['jahr']): F(tid, n + '.jahr ungültig')
        if 'filter' in f and not isinstance(f['filter'], dict): F(tid, n + '.filter muss ein Teilzustand (Objekt) sein')
        fp_ids.append(f.get('id'))
    if len(fp_ids) != len(set(fp_ids)): F(tid, 'Fokuspunkte mit doppelter id')
    k = st.get('kamera')
    if isinstance(k, str) and k not in fp_ids: F(tid, 'start.kamera „%s“ ist kein Fokuspunkt' % k)
    r = t.get('reiche') or {}
    for feld in ('verfuegbar', 'aktiv'):
        v = r.get(feld)
        if v is None or v == 'alle': continue
        if not isinstance(v, list): F(tid, 'reiche.%s: Liste oder „alle“' % feld); continue
        for x in v:
            if x not in reiche: F(tid, 'reiche.%s: unbekanntes Reich „%s“' % (feld, x))
    if isinstance(r.get('verfuegbar'), list) and isinstance(r.get('aktiv'), list):
        for x in r['aktiv']:
            if x not in r['verfuegbar']: F(tid, 'reiche.aktiv „%s“ ist nicht verfügbar' % x)
    e = t.get('ebenen') or {}
    v = e.get('verfuegbar')
    if v not in (None, 'alle'):
        if not isinstance(v, list): F(tid, 'ebenen.verfuegbar: Liste oder „alle“')
        else:
            for x in v:
                if x not in EBENEN: F(tid, 'ebenen.verfuegbar: unbekannte Ebene „%s“' % x)
    for x, w in (e.get('aktiv') or {}).items():
        if x not in EBENEN | AKTIV_EXTRA: F(tid, 'ebenen.aktiv: unbekannte Ebene „%s“' % x)
        elif x == 'netze':
            if not isinstance(w, list) or any(i not in NETZ_IDS for i in w): F(tid, 'ebenen.aktiv.netze: Liste bekannter Netz-ids (%s)' % ', '.join(sorted(NETZ_IDS)))
        elif not isinstance(w, bool): F(tid, 'ebenen.aktiv.%s muss true/false sein' % x)
    lh = t.get('lehrerhinweise')
    if lh is not None:
        if not isinstance(lh, dict) or not isinstance(lh.get('reiter'), list): F(tid, 'lehrerhinweise: {ordner, reiter: [...]}')
        else:
            rids = []
            for i, re_ in enumerate(lh['reiter']):
                for kk in ('id', 'titel', 'datei'):
                    if not re_.get(kk): F(tid, 'lehrerhinweise.reiter[%d].%s fehlt' % (i, kk))
                if re_.get('datei') and not os.path.isfile(os.path.join(ordner, lh.get('ordner', ''), re_['datei'])):
                    F(tid, 'Lehrerhinweis-Datei fehlt: %s%s' % (lh.get('ordner', ''), re_['datei']))
                rids.append(re_.get('id'))
            if len(rids) != len(set(rids)): F(tid, 'Lehrerhinweis-Reiter mit doppelter id')
    for key, dd in (t.get('daten') or {}).items():
        if key not in DATEN: F(tid, 'daten: unbekannter Schlüssel „%s“ (erlaubt: %s)' % (key, ', '.join(sorted(DATEN)))); continue
        if not isinstance(dd, dict) or not dd.get('datei'): F(tid, 'daten.%s: {datei, art}' % key); continue
        if dd.get('art', 'ersetzen') not in ('ersetzen', 'ergaenzen'): F(tid, 'daten.%s.art: „ersetzen“ oder „ergaenzen“' % key)
        dp = os.path.join(ordner, dd['datei'])
        if not os.path.isfile(dp): F(tid, 'Datendatei fehlt: %s' % dd['datei']); continue
        try: lade(dp)
        except Exception as ex: F(tid, 'Datendatei %s ist kein gültiges JSON: %s' % (dd['datei'], ex))

for w in warnungen: print('WARNUNG ' + w)
for f in fehler: print('FEHLER  ' + f)
print('%d Tafelbild(er) geprüft, %d Fehler, %d Warnungen' % (len(ids), len(fehler), len(warnungen)))
sys.exit(1 if fehler else 0)
