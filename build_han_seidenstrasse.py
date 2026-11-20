# -*- coding: utf-8 -*-
"""Seidenstraße der Han-Zeit aus Forschungsdaten (data/han_seidenstrasse.json).

Quelle: Hu Yumeng, Yan Bo, Zhang Ping: 两汉丝绸之路交通数据集 / Traffic data of the Silk Road in the Han dynasty.
China Scientific Data 3 (2018), Nr. 3, DOI 10.11922/csdata.2018.0016.zh; Daten: Science Data Bank,
DOI 10.57760/sciencedb.611 (früher 10.11922/sciencedb.611), Lizenz CC BY 4.0.

Der Datensatz enthält 14 rekonstruierte Hauptlinien (Chang’an bis ans Mittelmeer) und die Verkehrspunkte der
Westlichen Han (202 v. Chr. – 8 n. Chr.) und der Östlichen Han (25–220 n. Chr.): Hauptstädte, Sitze der Kommandanturen
und Kreise, Poststationen, Pässe, Fährstellen, Brücken u. a. Übernommen werden Lage, Typ, Zeitraum und Namen
(chinesisch und Umschrift aus dem Datensatz); die Linien werden vereinfacht.

    python build_han_seidenstrasse.py <ordner mit dh.*, xh.*, linie.* (Shapefiles) und dh.xlsx, xh.xlsx>

Benötigt: pyshp, openpyxl, shapely. Das Archiv der Science Data Bank enthält die Dateien unter chinesischen Namen:
东汉交通点 → dh, 西汉交通点 → xh, 汉代丝绸之路 → linie.
"""
import io, json, os, sys
import openpyxl, shapefile
from shapely.geometry import LineString

HERE = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HERE, 'data', 'han_seidenstrasse.json')
TYP = {'都城': 'Hauptstadt', '城市': 'Stadt', '郡级驻所': 'Sitz einer Kommandantur', '县级驻所': 'Kreissitz', '都尉治所': 'Sitz eines Militärkommandanten',
       '聚邑': 'Siedlung', '驿站': 'Poststation', '关隘': 'Pass mit Grenzposten', '渡口': 'Fährstelle', '桥梁': 'Brücke', '城门': 'Stadttor',
       '湖泊': 'See', '沙漠': 'Wüste'}
LINIE_DE = {'长安萧关道': 'Chang’an – Xiao-Pass', '长安汧县道': 'Chang’an – Qianxian', '凤翔灵台道': 'Fengxiang – Lingtai',
            '西域南道': 'Südroute durch die Westgebiete', '丝路中段新北道': 'Neue Nordroute (Mittelabschnitt)', '西域北道': 'Nordroute durch die Westgebiete',
            '婼羌道': 'Ruoqiang-Straße', '陇关道': 'Long-Pass-Straße', '河西走廊道': 'Hexi-Korridor', '丝路西段': 'Westabschnitt (Iran bis Mittelmeer)',
            '略阳道': 'Lüeyang-Straße', '回中道': 'Huizhong-Straße', '萧关道': 'Xiao-Pass-Straße', '河湟道': 'Hehuang-Straße'}
LAND = {'中华人民共和国': 'China', '伊朗伊斯兰共和国': 'Iran', '阿富汗伊斯兰共和国': 'Afghanistan', '伊拉克共和国': 'Irak', '阿拉伯叙利亚共和国': 'Syrien',
        '土耳其共和国': 'Türkei', '吉尔吉斯斯坦共和国': 'Kirgisistan', '哈萨克斯坦共和国': 'Kasachstan', '印度共和国': 'Indien', '蒙古国': 'Mongolei',
        '土库曼斯坦共和国': 'Turkmenistan', '乌兹别克斯坦共和国': 'Usbekistan', '克什米尔地区': 'Kaschmir', '阿拉伯埃及共和国': 'Ägypten'}


def punkte(ordner, kurz):
    # Lage aus dem Shapefile, über den chinesischen Namen zugeordnet (Reihenfolge von Tabelle und Shapefile weicht ab).
    # Kommt ein Name mehrfach vor, werden die Vorkommen der Reihe nach zugeordnet.
    r = shapefile.Reader(os.path.join(ordner, kurz), encoding='utf-8', encodingErrors='replace')
    geo = {}
    for rec, shp in zip(r.records(), r.shapes()):
        geo.setdefault((rec[0] or '').strip(), []).append(shp.points[0])
    wb = openpyxl.load_workbook(os.path.join(ordner, kurz + '.xlsx'), read_only=True)
    zeilen = list(wb.active.iter_rows(values_only=True))
    kopf, zeilen = zeilen[0], [z for z in zeilen[1:] if z and z[0] is not None]
    k = {n: i for i, n in reversed(list(enumerate(kopf)))}   # erste Spalte gleichen Namens
    out = []
    for z in zeilen:
        name = (z[k['Name_Chine']] or '').strip()
        if not geo.get(name): print('ohne Lage:', name); continue
        lng, lat = geo[name].pop(0)
        out.append(dict(zh=(z[k['Name_Chine']] or '').strip(), py=(z[k['Name_Engli']] or '').strip(), typ=TYP.get(z[k['type']], z[k['type']] or ''),
                        land=LAND.get(z[k['Country']], z[k['Country']] or ''), provinz=(z[k['Province']] or '').strip() if isinstance(z[k['Province']], str) else '',
                        von=int(z[k['beg_year']]), bis=int(z[k['end_year']]), lng=round(lng, 4), lat=round(lat, 4)))
    return out


def main(ordner):
    st = {}
    for kurz in ('xh', 'dh'):
        for p in punkte(ordner, kurz):
            if not p['zh']: continue
            schl = (p['zh'], round(p['lng'], 2), round(p['lat'], 2))
            e = st.setdefault(schl, dict(p, zeiten=[]))
            if [p['von'], p['bis']] not in e['zeiten']: e['zeiten'].append([p['von'], p['bis']])
    stationen = []
    for i, e in enumerate(sorted(st.values(), key=lambda x: (x['lng'], x['lat']))):
        stationen.append({'id': 'hs%03d' % i, 'zh': e['zh'], 'py': e['py'], 'typ': e['typ'], 'land': e['land'], 'provinz': e['provinz'],
                          'lng': e['lng'], 'lat': e['lat'], 'zeiten': sorted(e['zeiten'])})
    r = shapefile.Reader(os.path.join(ordner, 'linie'), encoding='utf-8', encodingErrors='replace')
    linien = []
    for i, (rec, shp) in enumerate(zip(r.records(), r.shapes())):
        teile = list(shp.parts) + [len(shp.points)]
        pts = []
        for a, b in zip(teile[:-1], teile[1:]):
            g = LineString(shp.points[a:b]).simplify(0.015)
            pts.append([[round(x, 3), round(y, 3)] for x, y in g.coords])
        name = (rec[0] or '').strip()
        linien.append({'id': 'hl%02d' % i, 'zh': name, 'de': LINIE_DE.get(name, name), 'teile': pts})
    daten = {
        '_quelle': 'Hu Yumeng, Yan Bo, Zhang Ping: Traffic data of the Silk Road in the Han dynasty (两汉丝绸之路交通数据集). '
                   'China Scientific Data 3 (2018) 3, DOI 10.11922/csdata.2018.0016.zh; Science Data Bank, DOI 10.57760/sciencedb.611',
        'lizenz': 'CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); vereinfacht und übersetzt mit build_han_seidenstrasse.py',
        'zeitraum': {'westliche_han': [-202, 8], 'oestliche_han': [25, 220]},
        'linien': linien, 'stationen': stationen,
    }
    with io.open(ZIEL, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(daten, f, ensure_ascii=False, separators=(',', ':'))
    from collections import Counter
    print('Linien:', len(linien), 'Punkte:', sum(len(t) for l in linien for t in l['teile']), '| Stationen:', len(stationen),
          dict(Counter(s['typ'] for s in stationen)), '| Bytes:', os.path.getsize(ZIEL))


if __name__ == '__main__':
    main(sys.argv[1])
