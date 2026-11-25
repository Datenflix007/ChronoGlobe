# -*- coding: utf-8 -*-
"""Griechische Poleis und Kolonisation aus dem „Inventory of Archaic and Classical Poleis“ (Hansen/Nielsen 2004).

Quellen (werden nach quellen/lokal/poleis/ geladen, dort per .gitignore ausgeschlossen):
  1. POLIS (Stanford University, Classics Department; M. Krishnan / J. Ober, Stand 2014):
     http://polis.stanford.edu/data/master_data_11_19_2013.csv
     Alle 1035 Poleis des Inventars mit Koordinaten, Region, Größenklasse, Bekanntheit, Mauern, Münzprägung,
     Mitgliedschaft im Delisch-Attischen Seebund. Keine Lizenz angegeben („frei zugänglich für akademische Nutzung“)
     → vor einer Veröffentlichung klären (docs/DATENQUELLEN.md).
  2. Appendix 27 „Colonisation and Hellenisation“, digitalisiert von D. Krasne (v1.0, 25.07.2026), CC BY 4.0:
     https://www.darcykrasne.com/digital_humanities/gis_data/polis_inv/hn_app27_with_pids.csv
     Kolonie → Mutterstadt mit Gründungsdatum in der Notation des Inventars und Polis-Nummern.

Ergebnis:
  data/ebenen/griechische-poleis.json         Themenebene: alle lokalisierten Poleis
  data/ebenen/delisch-attischer-seebund.json  Themenebene: Mitglieder des Seebunds (478/7–404 v. Chr.)
  data/kolonisation.json                      Züge Mutterstadt → Kolonie (von build_fruehe_kulturen.py übernommen)

Darstellungsregeln (im Hinweis der Ebenen genannt):
  - Eine Polis erscheint ab ihrem Gründungsdatum (Kolonien, Anhang 27), sonst ab 650 v. Chr. (Beginn des Zeitraums
    des Inventars), und bleibt bis 323 v. Chr. (Ende des Zeitraums) sichtbar.
  - Gründungsdaten: „C6m“ = Mitte 6. Jh. → 550, „C6f“ = erste Hälfte → 575, „C6s“ = zweite Hälfte → 525,
    „C6e“ = früh → 590, „C6l“ = spät → 510, „c.600“ → 600, „446/5“ → 446.

    python build_poleis.py          # lädt die Quellen bei Bedarf und schreibt die drei Dateien
"""
import csv, heapq, io, json, math, os, re, urllib.request
from shapely.geometry import LineString, shape

HERE = os.path.dirname(os.path.abspath(__file__))
LOKAL = os.path.join(HERE, 'quellen', 'lokal', 'poleis')
URL_STANFORD = 'http://polis.stanford.edu/data/master_data_11_19_2013.csv'
URL_APP27 = 'https://www.darcykrasne.com/digital_humanities/gis_data/polis_inv/hn_app27_with_pids.csv'
VON_STANDARD, BIS_STANDARD = -650, -323

QUELLE_HN = 'Hansen, Mogens Herman; Nielsen, Thomas Heine (Hg.): An Inventory of Archaic and Classical Poleis. Oxford: Oxford University Press 2004.'
QUELLE_STANFORD = {'zitat': 'POLIS – digitale Fassung des Inventars. Stanford University, Classics Department (M. Krishnan, J. Ober), Stand 2014.', 'url': 'http://polis.stanford.edu', 'lizenz': 'keine Lizenz angegeben, frei zugänglich für akademische Nutzung'}
QUELLE_APP27 = {'zitat': 'Krasne, Darcy: Augmented digitization of Appendix 27 („Colonisation and Hellenisation“) of Hansen/Nielsen 2004, v1.0, 2026.', 'url': 'https://www.darcykrasne.com/digital_humanities/gis_data/polis_inv/', 'lizenz': 'CC BY 4.0'}

REGION_DE = {
    'Achaia': 'Achaia', 'Adriatic': 'Adria', 'Aegean': 'Ägäische Inseln', 'Aiolis & SW Mysia': 'Aiolis und Mysien', 'Aitolia': 'Aitolien',
    'Akarnania & Ajacent': 'Akarnanien', 'Argolis': 'Argolis', 'Arkadia': 'Arkadien', 'Attika': 'Attika', 'Black Sea': 'Schwarzes Meer',
    'Boiotia': 'Böotien', 'Crete': 'Kreta', 'Cyprus': 'Zypern', 'Doris': 'Doris', 'East Locris': 'Ostlokris', 'Elis': 'Elis', 'Epeiros': 'Epirus',
    'Euboia': 'Euböa', 'Ionia': 'Ionien', 'Italia & Kampania': 'Italien und Kampanien', 'Karia': 'Karien', 'Lakedaimon': 'Lakonien',
    'Lesbos': 'Lesbos', 'Lykia': 'Lykien', 'Makedonia': 'Makedonien', 'Megaris, Korinthia, Sikyonia': 'Megaris, Korinthia, Sikyonia',
    'Messenia': 'Messenien', 'Pamphylia & Kilikia': 'Pamphylien und Kilikien', 'Phokis': 'Phokis', 'Propontic Asia Minor': 'Propontis (Kleinasien)',
    'Propontic Thrace': 'Propontis (Thrakien)', 'Rhodos': 'Rhodos', 'Saronic Gulf': 'Saronischer Golf', 'Sikelia': 'Sizilien',
    'Spain & France': 'Spanien und Gallien', 'Syria to Pillars of Herakles': 'Syrien bis zu den Säulen des Herakles', 'Thessaly & Adjacent': 'Thessalien',
    'Thrace: Axios - Strymon': 'Thrakien (Axios–Strymon)', 'Thrace: Inland': 'Thrakien (Binnenland)', 'Thrace: Nestos - Hebros': 'Thrakien (Nestos–Hebros)',
    'Thrace: Strymon - Nestos': 'Thrakien (Strymon–Nestos)', 'Thracian Chersonesos': 'Thrakische Chersones', 'Triphylia': 'Triphylien', 'Troas': 'Troas'}
GROESSE = {1: 'sehr kleines Gebiet (unter 25 km²)', 2: 'kleines Gebiet (25–100 km²)', 3: 'mittleres Gebiet (100–200 km²)', 4: 'großes Gebiet (200–500 km²)', 5: 'sehr großes Gebiet (über 500 km²)'}


def laden(url, name):
    os.makedirs(LOKAL, exist_ok=True)
    pfad = os.path.join(LOKAL, name)
    if not os.path.exists(pfad):
        req = urllib.request.Request(url, headers={'User-Agent': 'ChronoGlobe-Datenaufbereitung'})
        with urllib.request.urlopen(req, timeout=120) as r, open(pfad, 'wb') as f: f.write(r.read())
    return open(pfad, encoding='utf-8', errors='replace').read()


# ---------- Seewege für die Kolonisation ----------
# Wegpunkte auf See (Länge, Breite). Kanten entstehen automatisch zwischen Punkten, deren Verbindung kein Land kreuzt.
SEE = {
    'saron': (23.55, 37.7), 'kykladen': (25.0, 37.2), 'nordaegaeis': (24.6, 39.8), 'thermaisch': (23.0, 40.1), 'thrakien': (25.0, 40.6),
    'chalkidike': (24.2, 39.9), 'hellespont_w': (26.15, 40.05), 'hellespont_o': (26.8, 40.45), 'marmara': (28.0, 40.7), 'bosporus_s': (28.98, 40.98), 'bosporus_n': (29.12, 41.3),
    'pontos_sw': (29.0, 42.5), 'pontos_w': (29.3, 44.0), 'pontos_nw': (30.8, 45.8), 'olbia': (31.6, 46.4), 'krim_s': (33.5, 44.2), 'kertsch': (36.4, 45.0),
    'pontos_mitte': (34.0, 43.2), 'sinope': (35.2, 42.3), 'pontos_o': (39.0, 41.6), 'phasis': (41.3, 42.1),
    'chios': (26.3, 38.5), 'samos': (27.0, 37.6), 'rhodos': (27.45, 36.2), 'kos': (27.0, 36.7), 'kreta_n': (25.0, 35.7), 'kythera': (23.0, 36.0),
    'kreta_s': (24.5, 34.6), 'kyrene': (21.8, 33.2), 'syrte': (16.5, 32.8), 'nil': (30.3, 31.7), 'zypern_w': (32.0, 34.8), 'kilikien': (34.5, 36.3),
    'pamphylien': (31.0, 36.4), 'lykien': (29.5, 36.0), 'levante': (35.0, 34.0),
    'korinth_golf': (22.7, 38.1), 'patras': (21.6, 38.3), 'zakynthos': (20.5, 37.6), 'kerkyra': (19.8, 39.4), 'otranto': (19.0, 40.4),
    'adria_s': (18.0, 41.8), 'adria_m': (15.6, 43.2), 'adria_n': (13.4, 44.6),
    'tarent': (17.1, 39.9), 'kalabrien': (16.8, 38.6), 'messina_s': (15.5, 37.9), 'messina_n': (15.7, 38.35), 'syrakus': (15.45, 37.0),
    'sizilien_s': (14.0, 36.8), 'sizilien_w': (12.1, 37.7), 'tyrrhen_s': (14.0, 39.2), 'neapel': (14.1, 40.55), 'tyrrhen_n': (11.0, 42.0),
    'korsika_o': (10.0, 42.8), 'ligurien': (8.5, 43.8), 'lion': (5.3, 42.9), 'katalonien': (3.6, 42.0), 'valencia': (1.0, 40.5), 'cartagena': (-0.5, 37.6),
    'sardinien_s': (8.9, 38.7), 'karthago': (10.5, 37.5), 'libyen_w': (13.0, 33.6),
}
_land = None
# Meerengen, die in der groben Küstenlinie geschlossen sind: Golf von Korinth, Hellespont, Bosporus, Straße von Messina
FEST = [('korinth_golf', 'patras'), ('patras', 'zakynthos'), ('hellespont_w', 'hellespont_o'), ('hellespont_o', 'marmara'),
        ('marmara', 'bosporus_s'), ('bosporus_s', 'bosporus_n'), ('bosporus_n', 'pontos_sw'), ('messina_s', 'messina_n')]


def land():
    global _land
    if _land is None:
        _land = shape(json.load(open(os.path.join(HERE, 'data', 'land.json'), encoding='utf-8'))['geometry']).buffer(0).buffer(-0.03)
    return _land


def frei(a, b): return not LineString([a, b]).intersects(land())


def km(a, b):
    la1, la2, d = math.radians(a[1]), math.radians(b[1]), math.radians(b[0] - a[0])
    return 6371 * math.acos(min(1, math.sin(la1) * math.sin(la2) + math.cos(la1) * math.cos(la2) * math.cos(d)))


_kanten = None


def seegraph():
    global _kanten
    if _kanten is None:
        _kanten = {k: [] for k in SEE}
        ks = list(SEE)
        for i, a in enumerate(ks):
            for b in ks[i + 1:]:
                if km(SEE[a], SEE[b]) < 700 and frei(SEE[a], SEE[b]):
                    d = km(SEE[a], SEE[b]); _kanten[a].append((b, d)); _kanten[b].append((a, d))
        for a, b in FEST:
            if not any(n == b for n, _ in _kanten[a]): d = km(SEE[a], SEE[b]); _kanten[a].append((b, d)); _kanten[b].append((a, d))
    return _kanten


def anschluss(pt):
    """Seepunkte, die von einem Hafen aus erreichbar sind (ohne Land zu kreuzen); sonst der nächste."""
    nah = sorted(SEE, key=lambda k: km(pt, SEE[k]))
    frei_ = [k for k in nah[:6] if frei(pt, SEE[k])]
    return frei_[:2] or nah[:1]


def seeweg(a, b):
    """Route von Hafen a nach Hafen b über die Seepunkte (Dijkstra); direkt, wenn die Luftlinie kein Land kreuzt."""
    if frei(a, b) or km(a, b) < 60: return [a, b]
    G = seegraph(); start, ziel = anschluss(a), set(anschluss(b))
    dist, vor, q = {}, {}, []
    for k in start: dist[k] = km(a, SEE[k]); heapq.heappush(q, (dist[k], k))
    while q:
        d, k = heapq.heappop(q)
        if d > dist.get(k, 1e18): continue
        if k in ziel:
            weg = [k]
            while weg[-1] in vor: weg.append(vor[weg[-1]])
            return [a] + [list(SEE[x]) for x in reversed(weg)] + [b]
        for n, w in G[k]:
            if d + w < dist.get(n, 1e18): dist[n] = d + w; vor[n] = k; heapq.heappush(q, (d + w, n))
    return [a, b]


# Gruppen der Mutterstädte (Schalter im Menü, Farben)
GRUPPEN = [
    ('milet', 'Milet', '#4fc3f7', ['Miletos']),
    ('korinth', 'Korinth', '#ff8a65', ['Korinthos', 'Korkyra']),
    ('euboia', 'Chalkis und Eretria (Euböa)', '#ffd54f', ['Chalkis', 'Eretria']),
    ('megara', 'Megara', '#81c784', ['Megara']),
    ('phokaia', 'Phokaia und Massalia', '#ba68c8', ['Phokaia', 'Massalia']),
    ('sparta', 'Sparta', '#e57373', ['Sparta/Lakedaimon']),
    ('athen', 'Athen', '#64b5f6', ['Athenai']),
    ('inseln', 'Inseln der Ägäis und Ionien', '#4db6ac', ['Samos', 'Paros', 'Thasos', 'Naxos', 'Andros', 'Chios', 'Rhodos', 'Lindos', 'Knidos', 'Mytilene', 'Klazomenai', 'Teos', 'Kolophon', 'Erythrai', 'Thera']),
    ('westen', 'Tochterstädte im Westen', '#f0a35e', ['Syrakousai', 'Zankle/Messana', 'Sybaris', 'Kroton', 'Lokroi', 'Kyme', 'Gela', 'Akragas', 'Taras', 'Rhegion', 'Megara Hyblaia', 'Selinous']),
]
GRUPPE_VON = {n: g[0] for g in GRUPPEN for n in g[3]}


def jahr_aus(t):
    """Gründungsdatum in der Notation des Inventars → (Jahr v. Chr. negativ, unsicher) oder (None, None)."""
    t = (t or '').strip()
    if not t or t == '?': return None, None
    unsicher = '?' in t or t.startswith('c.') or t.startswith('C')
    m = re.match(r'^C(\d+)([efmsl]?)', t)
    if m:
        jh = int(m.group(1)); basis = -(jh * 100 - 50)   # Mitte des Jahrhunderts
        verschiebung = {'e': -40, 'f': -25, 'm': 0, 's': 25, 'l': 40, '': 0}[m.group(2)]
        return basis + verschiebung, True
    m = re.search(r'(\d{3,4})', t)
    if m: return -int(m.group(1)), unsicher
    return None, None


def slug(t):
    t = t.lower()
    for a, b in (('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss')): t = t.replace(a, b)
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')[:50] or 'polis'


def main():
    stanford = list(csv.DictReader(io.StringIO(laden(URL_STANFORD, 'stanford_master_data.csv'))))[1:]   # erste Zeile beschreibt Feldtypen
    app27 = list(csv.DictReader(io.StringIO(laden(URL_APP27, 'hn_app27_with_pids.csv'))))
    poleis = {}
    for z in stanford:
        if 'HansonNielson' not in z['Source']: continue
        try: lng, lat = float(z['xcoord']), float(z['ycoord'])
        except ValueError: continue
        if not lng and not lat: continue
        name = z['name'].split('-', 1)[1] if '-' in z['name'] else z['name']
        poleis[z['polis_id']] = dict(nr=z['polis_id'], name=name.strip(), lng=round(lng, 3), lat=round(lat, 3), region=z['Region name'].strip(),
                                     groesse=int(z['Size']) if z['Size'].isdigit() else 0, seebund=z['Delian_League'] == '1',
                                     mauern=z['Walls'] == '1', silber=z['Silver_1st'].strip(), bronze=z['Bronze_1st'].strip(),
                                     fame=float(z['Fame']) if re.match(r'^[\d.]+$', z['Fame'] or '') else 0)
    # Gründungen aus Anhang 27: erste (ursprüngliche) Gründung je Kolonie
    gruendung, zuege, gesehen = {}, [], set()
    for a in app27:
        k, m = a['colony_hnid'].strip(), a['founder_hnid'].strip()
        j, uns = jahr_aus(a['hn_foundation_date'])
        if a['initial_foundation'] != 'True' or j is None: continue
        if k in poleis and (k not in gruendung or j < gruendung[k][0]): gruendung[k] = (j, uns, a['founder_name'].strip(), a['hn_foundation_date'].strip())
        if k in poleis and m in poleis and VON_STANDARD - 200 <= j <= BIS_STANDARD and (k, m) not in gesehen:
            gesehen.add((k, m))
            K, M = poleis[k], poleis[m]
            pfad = [[round(x, 3), round(y, 3)] for x, y in seeweg([M['lng'], M['lat']], [K['lng'], K['lat']])]
            zuege.append({'id': 'k%s-%s' % (k, m), 'kolonie': K['name'], 'mutter': M['name'], 'gruppe': GRUPPE_VON.get(M['name'], 'weitere'),
                          'jahr': j, 'unsicher': bool(uns), 'inventar': a['hn_foundation_date'].strip(), 'pfad': pfad})
    zuege.sort(key=lambda z: (z['jahr'], z['kolonie']))

    objekte, mitglieder, ids = [], [], set()
    for p in sorted(poleis.values(), key=lambda x: (-x['fame'], x['name'])):
        g = gruendung.get(p['nr'])
        von = max(g[0], -1200) if g else VON_STANDARD
        teile = ['Polis Nr. %s im Inventar von Hansen/Nielsen; Region: %s.' % (p['nr'], REGION_DE.get(p['region'], p['region']))]
        if g: teile.append('Gegründet von %s, %s (Inventar: „%s“).' % (g[2], ('um ' if g[1] else '') + '%d v. Chr.' % -g[0], g[3]))
        if p['groesse'] in GROESSE: teile.append('Größe: ' + GROESSE[p['groesse']] + '.')
        extra = []
        if p['mauern']: extra.append('Stadtmauern belegt')
        if p['silber']: extra.append('eigene Silbermünzen')
        if p['seebund']: extra.append('Mitglied im Delisch-Attischen Seebund')
        if extra: teile.append('; '.join(extra) + '.')
        oid = slug(p['name']) + '-' + p['nr']
        if oid in ids: continue
        ids.add(oid)
        o = {'id': oid, 'typ': 'punkt', 'name': p['name'], 'von': von, 'bis': max(BIS_STANDARD, von), 'beschreibung': ' '.join(teile),
             'beleg': 'Hansen/Nielsen 2004, Nr. %s' % p['nr'], 'koordinaten': [p['lng'], p['lat']]}
        if g and g[1]: o['unsicher'] = True
        if p['groesse']: o['groesse'] = p['groesse']
        objekte.append(o)
        if p['seebund']:
            mitglieder.append({'id': oid, 'typ': 'punkt', 'name': p['name'], 'von': -478, 'bis': -404, 'beschreibung': 'In den athenischen Tributlisten als Mitglied belegt (Region: %s).' % REGION_DE.get(p['region'], p['region']),
                               'beleg': 'Hansen/Nielsen 2004, Nr. %s' % p['nr'], 'koordinaten': [p['lng'], p['lat']], **({'groesse': p['groesse']} if p['groesse'] else {})})

    ebene = {'format': 'chronoglobe-ebene/1', 'id': 'griechische-poleis', 'name': 'Griechische Poleis (alle Stadtstaaten)', 'farbe': '#7fd1ff',
             'beschreibung': 'Alle %d lokalisierten Poleis des Inventars von Hansen und Nielsen – vom Schwarzen Meer bis Spanien. Größere Punkte = größeres Stadtgebiet. Die Infokarte nennt Region, Gründung, Größe und Mitgliedschaft im Seebund.' % len(objekte),
             'hinweis': 'Darstellungsregel: Eine Polis erscheint ab ihrem Gründungsdatum (nur für Kolonien bekannt, sonst ab 650 v. Chr.) und bleibt bis 323 v. Chr. sichtbar – dem Zeitraum des Inventars. Viele Städte bestanden länger. Gründungsdaten sind oft nur auf ein Jahrhundert genau.',
             'quellen': [{'zitat': QUELLE_HN}, QUELLE_STANFORD, QUELLE_APP27], 'objekte': objekte}
    bund = {'format': 'chronoglobe-ebene/1', 'id': 'delisch-attischer-seebund', 'name': 'Mitglieder des Delisch-Attischen Seebunds', 'farbe': '#1fa2c8',
            'beschreibung': 'Die %d Poleis, die nach dem Inventar von Hansen und Nielsen zum Seebund unter Athens Führung gehörten (478/7–404 v. Chr.).' % len(mitglieder),
            'hinweis': 'Darstellungsregel: Alle Mitglieder erscheinen für die ganze Dauer des Bundes; tatsächlich traten viele später bei, fielen ab oder wurden gezwungen zu bleiben. Grundlage sind vor allem die athenischen Tributlisten.',
            'quellen': [{'zitat': QUELLE_HN}, QUELLE_STANFORD], 'objekte': mitglieder}
    for name, d in (('griechische-poleis.json', ebene), ('delisch-attischer-seebund.json', bund)):
        with io.open(os.path.join(HERE, 'data', 'ebenen', name), 'w', encoding='utf-8', newline='\n') as f: json.dump(d, f, ensure_ascii=False, separators=(',', ':'))
    with io.open(os.path.join(HERE, 'data', 'kolonisation.json'), 'w', encoding='utf-8', newline='\n') as f:
        gruppen = [dict(id=g[0], name=g[1], farbe=g[2], anzahl=sum(1 for z in zuege if z['gruppe'] == g[0])) for g in GRUPPEN]
        gruppen.append(dict(id='weitere', name='Weitere Mutterstädte', farbe='#b0bec5', anzahl=sum(1 for z in zuege if z['gruppe'] == 'weitere')))
        json.dump({'_hinweis': 'Erzeugt mit build_poleis.py aus Appendix 27 von Hansen/Nielsen 2004 (Digitalisierung D. Krasne, CC BY 4.0). '
                               'Seewege berechnet über Wegpunkte auf See (schematisch, keine überlieferten Routen).',
                   'quelle': QUELLE_APP27, 'bis': BIS_STANDARD, 'gruppen': gruppen, 'zuege': zuege}, f, ensure_ascii=False, separators=(',', ':'))
    print('Poleis: %d lokalisiert, %d mit Gründungsdatum, %d Seebund-Mitglieder, %d Kolonisationszüge' % (len(objekte), len(gruendung), len(mitglieder), len(zuege)))


if __name__ == '__main__':
    main()
