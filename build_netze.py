# -*- coding: utf-8 -*-
"""Historische Handels- und Verkehrsnetze aus Forschungsdaten (data/netze/*.json).

Einheitliches Datenmodell für alle Netze (siehe docs/HANDELSNETZE.md):

    { "id", "name", "gruppe": "land"|"wasser"|"reise", "art": "handelsweg"|"verkehrsnetz"|"reiseroute",
      "datierung": { "typ": "jahrgenau"|"zeitraum"|"reisedatum", "von", "bis", "text" },
      "quelle": { "zitat", "doi", "daten_doi", "url", "lizenz", "lizenz_url", "geaendert" },
      "linien": [ { "id", "name", "von", "bis", "teile": [[[lng, lat], …], …], … } ],
      "orte":   [ { "id", "name", "lng", "lat", "typ", "von", "bis", … } ] }

Jahre sind historische Jahre (negativ = v. Chr.). Nichts wird ergänzt, was nicht im Datensatz steht:
Liegt keine Datierung je Strecke vor, gilt der dokumentierte Zeitraum des ganzen Datensatzes (typ "zeitraum").

    python build_netze.py <rohdaten-ordner>

Erwartete Unterordner (Downloads, nicht im Repository):
    althurayya/routes.json, althurayya/places.geojson   github.com/althurayya/althurayya.github.io (Ordner master/)
    tang/交通线.shp …, tang/交通点.shp …                  Science Data Bank, DOI 10.57760/sciencedb.587 (RAR entpacken)
    mongolen/蒙元线shapefile/*.shp, mongolen/蒙元点shapefile/*.shp   Science Data Bank, DOI 10.57760/sciencedb.622
    viatariq/<periode>_roads.geojson, <periode>_sites.geojson   Zenodo, DOI 10.5281/zenodo.21981430 (Version 1.1)
    petra_gaza/compiled_insence_road.*, sites.*                Zenodo, DOI 10.5281/zenodo.3413625

Benötigt: pyshp, shapely, pypinyin (nur für die Umschrift der Tang-Straßennamen).
"""
import io, json, math, os, re, sys
import shapefile
from shapely.geometry import LineString
from pypinyin import lazy_pinyin

HERE = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HERE, 'data', 'netze')


def r3(x): return round(x, 3)


def vereinfachen(pts, tol):
    pts = [(p[0], p[1]) for p in pts]
    if len(pts) < 3: return [[r3(x), r3(y)] for x, y in pts]
    s = LineString(pts).simplify(tol, preserve_topology=False)
    out = []
    for x, y in s.coords:
        q = [r3(x), r3(y)]
        if not out or out[-1] != q: out.append(q)
    return out if len(out) >= 2 else [[r3(pts[0][0]), r3(pts[0][1])], [r3(pts[-1][0]), r3(pts[-1][1])]]


def teile_aus_shape(s, tol):
    grenzen = list(s.parts) + [len(s.points)]
    return [vereinfachen(s.points[grenzen[i]:grenzen[i + 1]], tol) for i in range(len(s.parts)) if grenzen[i + 1] - grenzen[i] >= 2]


def km(teile):
    d = 0
    for t in teile:
        for a, b in zip(t, t[1:]):
            la1, la2 = math.radians(a[1]), math.radians(b[1]); dl = math.radians(b[0] - a[0])
            d += 6371 * math.acos(min(1, math.sin(la1) * math.sin(la2) + math.cos(la1) * math.cos(la2) * math.cos(dl)))
    return round(d)


# Umrechnung projizierter Koordinaten nach WGS84 (Formeln nach Snyder 1987, Map Projections – A Working Manual)
WGS_A, WGS_F = 6378137.0, 1 / 298.257223563
WGS_E2 = WGS_F * (2 - WGS_F); WGS_E = math.sqrt(WGS_E2)


def mercator_inv(x, y):   # World Mercator, EPSG:3395 (ellipsoidisch)
    t = math.exp(-y / WGS_A); phi = math.pi / 2 - 2 * math.atan(t)
    for _ in range(12):
        es = WGS_E * math.sin(phi)
        phi = math.pi / 2 - 2 * math.atan(t * ((1 - es) / (1 + es)) ** (WGS_E / 2))
    return math.degrees(x / WGS_A), math.degrees(phi)


def utm_inv(x, y, zone, nord=True):   # Transverse Mercator (UTM), k0 = 0,9996
    k0, ep2 = 0.9996, WGS_E2 / (1 - WGS_E2)
    x -= 500000.0
    if not nord: y -= 10000000.0
    m = y / k0
    mu = m / (WGS_A * (1 - WGS_E2 / 4 - 3 * WGS_E2 ** 2 / 64 - 5 * WGS_E2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - WGS_E2)) / (1 + math.sqrt(1 - WGS_E2))
    p1 = mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu) + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu) \
        + (151 * e1 ** 3 / 96) * math.sin(6 * mu) + (1097 * e1 ** 4 / 512) * math.sin(8 * mu)
    c1 = ep2 * math.cos(p1) ** 2; t1 = math.tan(p1) ** 2
    n1 = WGS_A / math.sqrt(1 - WGS_E2 * math.sin(p1) ** 2)
    r1 = WGS_A * (1 - WGS_E2) / (1 - WGS_E2 * math.sin(p1) ** 2) ** 1.5
    d = x / (n1 * k0)
    lat = p1 - (n1 * math.tan(p1) / r1) * (d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * ep2) * d ** 4 / 24
                                          + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * ep2 - 3 * c1 ** 2) * d ** 6 / 720)
    lng = (d - (1 + 2 * t1 + c1) * d ** 3 / 6 + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ep2 + 24 * t1 ** 2) * d ** 5 / 120) / math.cos(p1)
    return (zone - 1) * 6 - 180 + 3 + math.degrees(lng), math.degrees(lat)


def schreiben(name, obj):
    os.makedirs(ZIEL, exist_ok=True)
    p = os.path.join(ZIEL, name)
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
    print(name, os.path.getsize(p) // 1024, 'KB')


# ---------------------------------------------------------------------------------------------------------------
# al-Ṯurayyā: Wegenetz der islamischen Welt im 9./10. Jahrhundert (nach G. Cornu, Atlas du monde arabo-islamique)
# ---------------------------------------------------------------------------------------------------------------
TH_TYP = {'metropoles': 'Metropole', 'capitals': 'Hauptort einer Provinz', 'towns': 'Stadt', 'waystations': 'Rast- und Poststation',
          'villages': 'Dorf', 'xroads': 'Wegkreuzung', 'sites': 'Ort', 'waters': 'Wasserstelle', 'regions': 'Bezirk', 'quarters': 'Stadtviertel'}
TH_ORTE = ('metropoles', 'capitals')   # nur die großen Orte als Punkte (übersichtlich); alle Orte dienen der Benennung der Abschnitte


def translit(c):
    t = c.get('toponym_translit') or c.get('toponym_search') or ''
    return t.replace('ŧ', 'a').replace('Ŧ', 'A')   # Projekt-Umschrift: ŧ = tāʾ marbūṭa


def thurayya(ordner):
    places = json.load(io.open(os.path.join(ordner, 'places.geojson'), encoding='utf-8'))['features']
    routes = json.load(io.open(os.path.join(ordner, 'routes.json'), encoding='utf-8'))['features']
    P = {}
    for f in places:
        c = f['properties']['cornuData']
        P[c['cornu_URI']] = {'name': translit(c), 'ar': c.get('toponym_arabic') or '', 'typ': c.get('top_type_hom'),
                             'region': c.get('region_spelled') or '', 'lng': float(c['coord_lon']), 'lat': float(c['coord_lat']),
                             'sicher': c.get('coord_certainty') == 'certain'}
    linien = []
    for f in routes:
        g = f['geometry']; pr = f['properties']
        if not g or g['type'] != 'LineString' or len(g['coordinates']) < 2: continue
        a, b = P.get(pr.get('sToponym')), P.get(pr.get('eToponym'))
        teile = [vereinfachen(g['coordinates'], 0.01)]
        linien.append({'id': pr['id'], 'name': (a['name'] if a else '?') + ' – ' + (b['name'] if b else '?'),
                       'von': 800, 'bis': 1000, 'km': round((pr.get('Meter') or 0) / 1000) or km(teile), 'teile': teile})
    orte = [{'id': k, 'name': v['name'], 'ar': v['ar'], 'typ': TH_TYP[v['typ']], 'region': v['region'], 'lng': r3(v['lng']), 'lat': r3(v['lat']),
             'von': 800, 'bis': 1000, 'gross': v['typ'] == 'metropoles'}
            for k, v in sorted(P.items()) if v['typ'] in TH_ORTE]
    schreiben('thurayya.json', {
        'id': 'thurayya', 'name': 'Wegenetz der islamischen Welt (9./10. Jh.)', 'gruppe': 'land', 'art': 'verkehrsnetz',
        'datierung': {'typ': 'zeitraum', 'von': 800, 'bis': 1000,
                      'text': 'Die Strecken stammen aus den Wegbeschreibungen arabischer Geografen des 9. und 10. Jahrhunderts, kartiert im Atlas von G. Cornu (1983). '
                              'Einzelne Strecken sind nicht datiert; gezeigt wird das Netz dieses Zeitraums (800–1000).'},
        'quelle': {'zitat': 'al-Ṯurayyā Gazetteer Project (M. Seydi, M. Romanov u. a.), github.com/althurayya/althurayya.github.io; '
                            'georeferenziert nach Georgette Cornu: Atlas du monde arabo-islamique à l’époque classique, IXe–Xe siècles. Leiden: Brill 1983.',
                   'url': 'https://althurayya.github.io/', 'lizenz': 'CC BY 4.0', 'lizenz_url': 'https://creativecommons.org/licenses/by/4.0/',
                   'geaendert': 'Linien vereinfacht (0,01°), nur Metropolen und Provinzhauptorte als Punkte, Umschrift ŧ → a.'},
        'linien': linien, 'orte': orte})


# ---------------------------------------------------------------------------------------------------------------
# Tang: Seidenstraße, Ost- und Mittelabschnitt (618–907), Strecken und Verkehrspunkte jahrgenau
# ---------------------------------------------------------------------------------------------------------------
TANG_TYP = {'县城': 'Kreisstadt', '县治': 'Kreissitz', '州城': 'Präfekturstadt', '府城': 'Sitz einer Generalpräfektur', '都城': 'Hauptstadt', '王城': 'Königsstadt',
            '驿站': 'Poststation', '驿馆': 'Poststation', '镇城': 'Garnisonsstadt', '军城': 'Militärstadt', '守捉城': 'Grenzgarnison', '堡寨': 'Festung', '城堡': 'Burg',
            '关隘': 'Pass mit Grenzposten', '古城': 'Alte Stadt', '桥梁': 'Brücke', '城门': 'Stadttor', '湖泊': 'See', '地名': 'Ort'}
TANG_SONDER = {'唐蕃古道': 'Tang–Tibet-Straße (Tang-Fan gudao)', '莫贺延碛道': 'Straße durch die Moheyan-Wüste', '回鹘道': 'Uigurenstraße (Huihu dao)',
               '吐谷浑道': 'Tuyuhun-Straße'}
RICHTUNG = {'南': 'Süd', '北': 'Nord', '中': 'Mitte', '东': 'Ost', '西': 'West'}


def py(s):
    # Pinyin-Regel: Silben, die mit a, e oder o beginnen, bekommen im Wortinneren einen Apostroph (Chang’an)
    sil = lazy_pinyin(s)
    t = ''.join(x if i == 0 or x[:1] not in 'aeo' else '’' + x for i, x in enumerate(sil))
    return t[:1].upper() + t[1:]


def tang_name(zh):
    if zh in TANG_SONDER: return TANG_SONDER[zh]
    k = zh[:-1] if zh.endswith('道') else zh
    richt = ''
    if len(k) > 4 and k[-1] in RICHTUNG: richt, k = RICHTUNG[k[-1]], k[:-1]
    teile = [k[i:i + 2] for i in range(0, len(k), 2)] if len(k) % 2 == 0 and len(k) >= 4 else [k]
    name = '–'.join(py(t) for t in teile)
    return ('Straße ' + name if len(teile) > 1 else name + '-Straße') + (' (' + richt + ')' if richt else '')


def tang(ordner):
    def lese(stamm): return shapefile.Reader(os.path.join(ordner, stamm), encoding='gbk')
    l = lese('交通线'); linien = []
    for rec, s in zip(l.records(), l.shapes()):
        teile = teile_aus_shape(s, 0.008)
        linien.append({'id': 'tang-' + str(rec['OBJECTID']), 'name': tang_name(rec['Name']), 'zh': rec['Name'],
                       'von': int(rec['Beg_year']), 'bis': int(rec['End_year']), 'km': km(teile), 'teile': teile})
    p = lese('交通点'); orte = []
    for rec, s in zip(p.records(), p.shapes()):
        x, y = s.points[0][:2]
        heute = ' · '.join(v for v in (rec['Province'], rec['PL_City'], rec['County']) if v)
        orte.append({'id': 'tangp-' + str(rec['OBJECTID']), 'name': (rec['Name_EN'] or '').strip() or py(rec['Name_CH']), 'zh': rec['Name_CH'],
                     'typ': TANG_TYP.get(rec['Type'], rec['Type']), 'lng': r3(x), 'lat': r3(y),
                     'von': max(618, int(rec['Beg_year'])), 'bis': int(rec['End_year']), 'heute_zh': heute})
    orte = [o for o in orte if o['von'] <= o['bis']]
    schreiben('tang.json', {
        'id': 'tang', 'name': 'Seidenstraße der Tang (Ost- und Mittelabschnitt)', 'gruppe': 'land', 'art': 'handelsweg',
        'datierung': {'typ': 'jahrgenau', 'von': 618, 'bis': 907,
                      'text': 'Jede Strecke und jeder Verkehrspunkt hat im Datensatz ein eigenes Anfangs- und Endjahr (aus Quellen und Grabungsbefunden). '
                              'Viele Strecken enden um 760–790, als Tibet und die Uiguren den Westen beherrschten; einige werden ab etwa 850 wieder genutzt.'},
        'quelle': {'zitat': 'Xu Xueqiang, Zhang Ping: A dataset of the east-central section of the Silk Road in Tang dynasty (618–907). '
                            'China Scientific Data 3 (2018), DOI 10.11922/csdata.2018.0015.zh.',
                   'doi': '10.11922/csdata.2018.0015.zh', 'daten_doi': '10.57760/sciencedb.587', 'url': 'https://doi.org/10.57760/sciencedb.587',
                   'lizenz': 'CC BY 4.0', 'lizenz_url': 'https://creativecommons.org/licenses/by/4.0/',
                   'geaendert': 'Linien vereinfacht (0,008°), Typen übersetzt, Straßennamen in Umschrift (pypinyin), Punkte vor 618 auf 618 gesetzt.'},
        'linien': linien, 'orte': orte})


# ---------------------------------------------------------------------------------------------------------------
# Mongolenzeit: Reisewege von 15 Reisenden (1218–1353). Reiseberichte, keine Handelsrouten.
# ---------------------------------------------------------------------------------------------------------------
REISENDE = {'耶律楚材': 'Yelü Chucai', '长春真人丘处机': 'Qiu Chuji (Changchun)', '柏朗嘉宾': 'Johannes de Plano Carpini',
            '安德烈': 'Andreas von Longjumeau', '鲁布鲁克的威廉': 'Wilhelm von Rubruk', '海屯': 'Hethum I. von Kleinarmenien', '常德': 'Chang De',
            '尼古拉·波罗': 'Niccolò und Maffeo Polo', '耶律希亮': 'Yelü Xiliang', '马可·波罗': 'Marco Polo', '拉班·扫马、马克': 'Rabban Bar Sauma und Markos',
            '鄂多利克': 'Odorich von Pordenone', '伊本·白图泰': 'Ibn Battuta', '巴斯喀尔': 'Paschalis von Vitoria', '马黎诺里': 'Johannes von Marignola'}
BERICHT = {'《湛然居士文集》': 'Zhanran jushi wenji (Gesammelte Werke)', '《长春真人西游记》': 'Changchun zhenren xiyou ji (Reise nach Westen)',
           '《柏朗嘉宾蒙古行纪》': 'Ystoria Mongalorum', '《蒙古与教廷》': 'Briefe und Berichte (nach „Die Mongolen und das Papsttum“)',
           '《鲁布鲁克东行纪》': 'Itinerarium', '《海屯行记》': 'Reisebericht des Hethum (überliefert bei Kirakos von Gandzak)',
           '《西使记》': 'Xishi ji (Bericht der Gesandtschaft nach Westen)', '《马可波罗行记》': 'Il Milione (Die Wunder der Welt)',
           '《中外史地考证》': 'Biografie in chinesischen Quellen (nach „Zhongwai shidi kaozheng“)', '《拉班·扫马和马克西行记》': 'Geschichte des Rabban Sauma und Mar Yahballaha',
           '《鄂多利克东游录》': 'Relatio', '《伊本·白图泰游记》': 'Rihla', '《巴斯喀尔之信》': 'Brief des Paschalis', '《马黎诺里游记》': 'Chronik (Reisebericht)'}


# Deutsche Namen bzw. berichtigte Schreibung für eindeutig bestimmte Orte (die englische Spalte des Datensatzes enthält
# Tippfehler wie „Emily“ für Emil oder „Keiv“ für Kiew). Die Zuordnung der Orte selbst bleibt die des Datensatzes.
ORT_DE = {'叶密里': 'Emil', '乞瓦': 'Kiew', '行在': 'Hoflager des Khans', '讹答剌': 'Otrar', '和林': 'Karakorum', '哈喇和林': 'Karakorum',
          '汗八里': 'Khanbaliq (Peking)', '马尔丁': 'Mardin', '阿勒颇': 'Aleppo', '麦加': 'Mekka', '萨雷城': 'Sarai', '别儿哥萨莱': 'Neu-Sarai',
          '甘州': 'Ganzhou', '君士坦丁堡': 'Konstantinopel', '康士坦丁堡': 'Konstantinopel', '威尼斯': 'Venedig', '开罗': 'Kairo', '忽里模子': 'Hormus',
          '安提俄克': 'Antiochia', '报达': 'Bagdad', '的黎波里': 'Tripolis', '吉达': 'Dschidda', '可失哈耳': 'Kaschgar', '不花剌': 'Buchara',
          '亦思法杭': 'Isfahan', '寻思干': 'Samarkand', '邪米思干': 'Samarkand', '燕京': 'Yanjing (Peking)', '伊州': 'Hami (Yizhou)', '格鲁吉亚': 'Georgien',
          '纳希阿': 'Nachitschewan', '拔里寺大城': 'Täbris', '阿维南城': 'Avignon', '不里阿耳': 'Bolgar', '北庭都护府': 'Beshbaliq', '别石把': 'Beshbaliq',
          '德里': 'Delhi', '息思城': 'Sis'}


def zeit(v):
    # Datensatz: Jahr.Monat als Zahl oder Text (1246.1 = Oktober 1246, 1271.01 = Januar 1271)
    t = ('%.2f' % float(v)) if not isinstance(v, str) else (v.strip() + '.00')[:7]
    j, m = t.split('.')[:2]
    return int(j), max(1, min(12, int((m + '0')[:2])))


def mongolen(ordner):
    lin = os.path.join(ordner, '蒙元线shapefile'); pun = os.path.join(ordner, '蒙元点shapefile')
    reisen, linien, orte = [], [], []
    for f in sorted(os.listdir(lin)):
        if not f.endswith('lines.shp'): continue
        stamm = f[:-len('lines.shp')]
        r = shapefile.Reader(os.path.join(lin, f), encoding='gbk')
        namen = {}
        pp = os.path.join(pun, stamm + 'points.shp')
        punkte = []
        if os.path.exists(pp):
            rp = shapefile.Reader(pp, encoding='gbk')
            for rec, s in zip(rp.records(), rp.shapes()):
                ne = ORT_DE.get(rec['Name']) or (rec['Name_E'] or '').strip()
                namen.setdefault(rec['Name'], ne)
                punkte.append({'name': ne or rec['Name'], 'zh': rec['Name'], 'jahr': int(float(rec['Year'] or 0)), 'lng': r3(s.points[0][0]), 'lat': r3(s.points[0][1])})
        recs = sorted(zip(r.records(), r.shapes()), key=lambda x: zeit(x[0]['Begin_Time']))
        if not recs: continue
        wer = recs[0][0]['Tourist'].strip(); rid = 'reise-' + stamm
        etappen = []
        for i, (rec, s) in enumerate(recs):
            (j1, m1), (j2, m2) = zeit(rec['Begin_Time']), zeit(rec['End_Time'])
            a, b = rec['Begin_Plac'].strip(), rec['End_Place'].strip()
            teile = teile_aus_shape(s, 0.02)
            nm = lambda z: ORT_DE.get(z) or namen.get(z) or py(z)
            etappen.append({'id': rid + '-' + str(i + 1), 'reise': rid, 'name': nm(a) + ' – ' + nm(b),
                            'zh': a + ' – ' + b, 'von': j1, 'vonMonat': m1, 'bis': j2, 'bisMonat': m2, 'km': km(teile), 'teile': teile})
        von, bis = etappen[0]['von'], max(e['bis'] for e in etappen)
        reisen.append({'id': rid, 'reisender': REISENDE.get(wer, wer), 'reisender_zh': wer, 'bericht': BERICHT.get(recs[0][0]['Reference'].strip(), recs[0][0]['Reference'].strip()),
                       'bericht_zh': recs[0][0]['Reference'].strip(), 'von': von, 'bis': bis})
        linien.extend(etappen)
        for k, p in enumerate(punkte):
            p.update({'id': rid + '-p' + str(k + 1), 'reise': rid, 'typ': 'Station', 'von': von, 'bis': bis})
            orte.append(p)
    schreiben('mongolen.json', {
        'id': 'mongolen', 'name': 'Reisende der Mongolenzeit (1218–1353)', 'gruppe': 'reise', 'art': 'reiseroute',
        'datierung': {'typ': 'reisedatum', 'von': 1218, 'bis': 1353,
                      'text': 'Jede Etappe ist im Datensatz mit Anfangs- und Endmonat datiert (nach den Reiseberichten). Gezeigt wird eine Reise, solange sie läuft; '
                              'danach bleibt sie drei Jahre blass sichtbar (Darstellungsregel).'},
        'hinweis': 'Reiseberichte einzelner Personen (Gesandte, Mönche, Kaufleute, Pilger). Sie zeigen, welche Wege benutzt wurden, '
                   'sind aber keine Handelsrouten und keine Belege für regelmäßigen Warenverkehr.',
        'quelle': {'zitat': 'Cheng Jun, Zhang Ping: A tourist routes GIS dataset of the Silk Road in the Mongol-Yuan dynasty. '
                            'China Scientific Data 3 (2018), DOI 10.11922/csdata.2018.0017.zh.',
                   'doi': '10.11922/csdata.2018.0017.zh', 'daten_doi': '10.57760/sciencedb.622', 'url': 'https://doi.org/10.57760/sciencedb.622',
                   'lizenz': 'CC BY 4.0', 'lizenz_url': 'https://creativecommons.org/licenses/by/4.0/',
                   'geaendert': 'Linien vereinfacht (0,02°), Namen der Reisenden und Berichte übersetzt, Ortsnamen aus der englischen Spalte des Datensatzes (sonst Umschrift).'},
        'reisen': reisen, 'linien': linien, 'orte': orte})


# ---------------------------------------------------------------------------------------------------------------
# VIA-TARIQ: mittelalterliches Straßennetz der Levante (Bilād al-Šām), vier Perioden 650–1517
# ---------------------------------------------------------------------------------------------------------------
VT_PERIODEN = [('early_islamic', 'Frühislamische Zeit', 'Umayyaden, Abbasiden', 650, 950),
               ('middle_islamic', 'Mittlere islamische Zeit', 'Fatimiden, Byzanz, Seldschuken, Kreuzfahrer, Ayyubiden', 950, 1250),
               ('early_mamluk', 'Frühe Mamlukenzeit', 'Mamluken', 1250, 1350),
               ('late_mamluk', 'Späte Mamlukenzeit', 'Mamluken', 1350, 1517)]
VT_TYP = {'city': 'Stadt', 'station': 'Station', 'fort': 'Festung', 'settlement': 'Siedlung', 'place': 'Ort', 'sanctuary': 'Heiligtum', 'bridge': 'Brücke'}
VT_ORTE = ('city', 'station')
VT_SICHER = {'Certain': 'sicher', 'Conjectured': 'erschlossen', 'Hypothetical': 'hypothetisch'}
VT_BELEG = {'High': 'hoch', 'Medium': 'mittel', 'Low': 'gering'}


def leer(v): return v is None or str(v).strip() in ('', '9999')


def viatariq(ordner):
    linien, orte, vergeben = [], [], set()
    for kurz, name, dyn, von, bis in VT_PERIODEN:
        r = json.load(io.open(os.path.join(ordner, kurz + '_roads.geojson'), encoding='utf-8'))
        assert 'EPSG:3395' in json.dumps(r.get('crs')), 'unerwartetes Koordinatensystem'
        for f in r['features']:
            g, p = f['geometry'], f['properties']
            if not g or g['type'] != 'LineString': continue
            pts = [mercator_inv(x, y) for x, y in (c[:2] for c in g['coordinates'])]
            teile = [vereinfachen(pts, 0.004)]
            it = (p.get('itinerary') or '').strip()
            lid = 'vt-' + kurz + '-' + str(p['Id'])
            while lid in vergeben: lid += 'b'   # eine Id kommt im Datensatz doppelt vor
            vergeben.add(lid)
            linien.append({'id': lid, 'name': (p.get('name') or '').strip(), 'periode': kurz, 'von': von, 'bis': bis,
                           'haupt': p.get('typeCode') == 2, 'itinerar': it, 'post': 'Barid' in it, 'hadsch': 'Hajj' in it,
                           'quelle_mittelalter': '' if leer(p.get('source')) else p['source'].strip(), 'literatur': '' if leer(p.get('biblio')) else p['biblio'].strip(),
                           'lage': VT_SICHER.get(p.get('segmentCer'), p.get('segmentCer')), 'beleg': VT_BELEG.get(p.get('roadCer'), p.get('roadCer')),
                           'km': round((p.get('geoLength') or p.get('lengthGeo') or 0) / 1000, 1), 'teile': teile})
        s = json.load(io.open(os.path.join(ordner, kurz + '_sites.geojson'), encoding='utf-8'))
        for f in s['features']:
            p = f['properties']
            if p.get('type') not in VT_ORTE or not f['geometry']: continue
            x, y = mercator_inv(*f['geometry']['coordinates'][:2])
            a = von if leer(p.get('minDate')) else max(von, int(p['minDate']))
            b = bis if leer(p.get('maxDate')) else min(bis, int(p['maxDate']))
            if a > b: continue
            orte.append({'id': 'vtp-' + kurz + '-' + str(p['Id']), 'name': (p.get('name') or '').strip(), 'heute': (p.get('modernName') or '').strip(),
                         'typ': VT_TYP.get(p['type'], p['type']), 'periode': kurz, 'lng': r3(x), 'lat': r3(y), 'von': a, 'bis': b,
                         'literatur': '' if leer(p.get('biblio')) else p['biblio'].strip()})
    schreiben('viatariq.json', {
        'id': 'viatariq', 'name': 'Straßen der Levante im Mittelalter (VIA-TARIQ)', 'gruppe': 'land', 'art': 'verkehrsnetz',
        'datierung': {'typ': 'zeitraum', 'von': 650, 'bis': 1517,
                      'text': 'Der Datensatz ordnet jede Strecke einer von vier Perioden zu: frühislamisch (650–950), mittlere islamische Zeit (950–1250), '
                              'frühe (1250–1350) und späte Mamlukenzeit (1350–1517). Gezeigt wird das Netz der Periode, in der das gewählte Jahr liegt.',
                      'perioden': [{'id': k, 'name': n, 'dynastien': d, 'von': a, 'bis': b} for k, n, d, a, b in VT_PERIODEN]},
        'hinweis': 'Ein Wegenetz, kein Nachweis von Handelsströmen. Strecken der staatlichen Post (barīd) und Pilgerwege (Hadsch) sind als solche gekennzeichnet.',
        'quelle': {'zitat': 'Adam Pažout: Geospatial data for the Medieval road system in the Levant (Bilād al-Šām). Version 1.1, Zenodo 2026, '
                            'DOI 10.5281/zenodo.21981430. Projekt VIA-TARIQ, Universitat Autònoma de Barcelona (EU Horizon Europe, MSCA Nr. 101151931).',
                   'daten_doi': '10.5281/zenodo.21981430', 'url': 'https://doi.org/10.5281/zenodo.21981430', 'lizenz': 'CC BY 4.0',
                   'lizenz_url': 'https://creativecommons.org/licenses/by/4.0/',
                   'geaendert': 'Von World Mercator (EPSG:3395) nach WGS84 umgerechnet, Linien vereinfacht (0,004°), nur Städte und Stationen als Punkte, Felder übersetzt.'},
        'linien': linien, 'orte': orte})


# ---------------------------------------------------------------------------------------------------------------
# Weihrauchstraße Petra – Gaza (Nabatäer), Verlauf nach Zohar & Erickson-Gini 2019
# ---------------------------------------------------------------------------------------------------------------
PG_ORTE = {'Petra': 'Petra', 'Avdat': 'Oboda (Avdat)', 'Eluza': 'Elusa (Haluza)', 'Gaza': 'Gaza', 'Mahmal': 'Mahmal'}


def petra(ordner):
    r = shapefile.Reader(os.path.join(ordner, 'compiled_insence_road'))
    assert 'UTM_Zone_36N' in open(os.path.join(ordner, 'compiled_insence_road.prj')).read()
    linien = []
    for rec, s in zip(r.records(), r.shapes()):
        grenzen = list(s.parts) + [len(s.points)]
        teile = [vereinfachen([utm_inv(x, y, 36) for x, y in (p[:2] for p in s.points[grenzen[i]:grenzen[i + 1]])], 0.002) for i in range(len(s.parts))]
        a, b = rec['Segment'].split('-')
        linien.append({'id': 'pg-' + str(rec['OBJECTID']), 'name': PG_ORTE.get(a, a) + ' – ' + PG_ORTE.get(b, b), 'von': -300, 'bis': 200,
                       'km': round(rec['Shape_Leng'] / 1000), 'teile': teile})
    rs = shapefile.Reader(os.path.join(ordner, 'sites'), encodingErrors='replace')
    orte = []
    for k, (rec, s) in enumerate(zip(rs.records(), rs.shapes())):
        x, y = utm_inv(s.points[0][0], s.points[0][1], 36)
        orte.append({'id': 'pgp-' + str(k + 1),   # OBJECTID ist im Datensatz nicht eindeutig
                     'name': (rec['ANCIENT_NA'] or rec['SITE_NAME']).strip(), 'heute': rec['SITE_NAME'].strip(),
                     'typ': 'Fundort am Weg', 'text': (rec['REMARKS'] or '').strip(), 'lng': r3(x), 'lat': r3(y), 'von': -300, 'bis': 200})
    schreiben('petra_gaza.json', {
        'id': 'petra_gaza', 'name': 'Weihrauchstraße Petra – Gaza', 'gruppe': 'land', 'art': 'handelsweg',
        'datierung': {'typ': 'zeitraum', 'von': -300, 'bis': 200,
                      'text': 'Der Datensatz selbst enthält keine Jahreszahlen. Zeitraum nach der UNESCO-Welterbeliste („Weihrauchstraße – Wüstenstädte im Negev“, Nr. 1107): '
                              'Der Handel mit Weihrauch und Myrrhe auf dieser Route blühte vom 3. Jahrhundert v. Chr. bis ins 2. Jahrhundert n. Chr.'},
        'quelle': {'zitat': 'Motti Zohar, Tali Erickson-Gini: The ‘Incense Road’ from Petra to Gaza: an analysis using GIS and cost functions. '
                            'International Journal of Geographical Information Science (2019); Daten: Zenodo, DOI 10.5281/zenodo.3413625.',
                   'daten_doi': '10.5281/zenodo.3413625', 'url': 'https://doi.org/10.5281/zenodo.3413625', 'lizenz': 'CC BY 4.0',
                   'lizenz_url': 'https://creativecommons.org/licenses/by/4.0/',
                   'zeit_beleg': 'UNESCO World Heritage Centre: Incense Route – Desert Cities in the Negev (Nr. 1107), whc.unesco.org/en/list/1107',
                   'geaendert': 'Von UTM Zone 36N nach WGS84 umgerechnet, Linien vereinfacht (0,002°); übernommen ist der zusammengesetzte Verlauf („compiled incense road“).'},
        'linien': linien, 'orte': orte})


if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    roh = sys.argv[1]
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if os.path.isdir(os.path.join(roh, 'althurayya')): thurayya(os.path.join(roh, 'althurayya'))
    if os.path.isdir(os.path.join(roh, 'tang')): tang(os.path.join(roh, 'tang'))
    if os.path.isdir(os.path.join(roh, 'mongolen')): mongolen(os.path.join(roh, 'mongolen'))
    if os.path.isdir(os.path.join(roh, 'viatariq')): viatariq(os.path.join(roh, 'viatariq'))
    if os.path.isdir(os.path.join(roh, 'petra_gaza')): petra(os.path.join(roh, 'petra_gaza'))
