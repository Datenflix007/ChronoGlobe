# -*- coding: utf-8 -*-
"""Frühe Hochkulturen für den freien Modus (data/fruehe_reiche.json).

Bewusst nur ANGEDEUTET: grobe, von Hand gesetzte Umrisse (an die Küstenlinie aus data/land.json angepasst) und
wenige, in der Fachliteratur übliche Eckdaten. Viele Jahreszahlen der frühen Zeit sind Näherungen („um“). Die Datei
hat dasselbe Format wie data/reiche.json (meta, reihen, regionen, ereignisse, schlachten, orte) und wird in js/app.js
zu den Kerndaten hinzugefügt. Tafelbilder laden nur Reiche, die in ihren Zeitraum fallen.

    python build_fruehe_kulturen.py
"""
import io, json, os
from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HERE, 'data', 'fruehe_reiche.json')

META = {
    'aegypten': dict(name='Altes Ägypten', von=-3100, bis=-332, farbe='#c8a23a', zentrum=[31.2, 27.0],
                     kurz='Pharaonenreich am Nil: Altes, Mittleres und Neues Reich; Pyramiden, Hieroglyphen, Bewässerung.'),
    'mesopotamien': dict(name='Mesopotamien', von=-3500, bis=-539, farbe='#4f86c6', zentrum=[44.5, 33.0],
                         kurz='Zwischen Euphrat und Tigris: Sumer, Akkad, Babylon und Assyrien; frühe Städte und Keilschrift.'),
    'indus': dict(name='Indus-Kultur', von=-2600, bis=-1900, farbe='#2a9d8f', zentrum=[70.5, 28.0],
                  kurz='Planmäßig angelegte Städte wie Harappa und Mohenjo-Daro; ihre Schrift ist bis heute nicht entziffert.'),
    'hethiter': dict(name='Hethiterreich', von=-1650, bis=-1180, farbe='#8a5cc7', zentrum=[34.5, 39.0],
                     kurz='Großreich in Anatolien mit der Hauptstadt Hattuša; Rivale Ägyptens um Syrien.'),
    'shang': dict(name='China: Shang und Zhou', von=-1600, bis=-221, farbe='#d9822b', zentrum=[113.0, 35.0],
                  kurz='Erste belegte Dynastien Chinas am Gelben Fluss; Orakelknochen mit früher chinesischer Schrift.'),
    'perser': dict(name='Perserreich (Achämeniden)', von=-550, bis=-330, farbe='#b5477a', zentrum=[53.0, 32.0],
                   kurz='Von Kyros II. gegründetes Großreich vom Mittelmeer bis zum Indus; endet mit Alexander dem Großen.'),
}
REIHEN = ['mesopotamien', 'aegypten', 'indus', 'hethiter', 'shang', 'perser']

NIL = [[29.6, 31.6], [32.3, 31.3], [31.5, 30.0], [31.3, 27.5], [33.0, 26.0], [33.0, 24.0], [32.6, 24.0], [32.2, 26.0], [30.6, 27.8], [30.4, 29.5], [29.6, 30.8]]
# (reich, name, von, bis, umriss [lng, lat])
REGIONEN = [
    ('aegypten', 'Unter- und Oberägypten (Niltal)', -3100, -332, NIL),
    ('aegypten', 'Nubien (Neues Reich)', -1550, -1070, [[31.0, 24.0], [33.6, 24.0], [34.0, 21.0], [33.6, 18.5], [31.5, 18.5], [30.5, 21.0]]),
    ('aegypten', 'Levante (Neues Reich)', -1479, -1180, [[34.2, 31.3], [35.6, 31.2], [36.9, 34.5], [36.7, 35.9], [35.9, 36.0], [35.5, 33.5], [34.3, 31.6]]),
    ('mesopotamien', 'Sumer (Stadtstaaten)', -3500, -2334, [[44.0, 32.6], [46.2, 32.2], [47.8, 30.6], [48.0, 29.9], [46.6, 30.0], [45.0, 31.0], [44.0, 32.0]]),
    ('mesopotamien', 'Reich von Akkad', -2334, -2154, [[38.0, 36.8], [42.5, 37.2], [45.5, 35.5], [48.3, 30.0], [46.5, 29.8], [43.0, 32.0], [40.0, 34.5], [38.0, 35.5]]),
    ('mesopotamien', 'Babylonisches Reich (Hammurabi)', -1792, -1595, [[42.5, 36.5], [45.5, 35.8], [48.0, 30.5], [46.6, 29.9], [44.0, 31.0], [42.0, 33.5]]),
    ('mesopotamien', 'Neuassyrisches Reich', -911, -609, [[35.8, 37.5], [44.5, 38.0], [47.5, 34.0], [48.3, 30.2], [46.5, 29.8], [39.0, 32.5], [35.8, 30.0], [34.2, 31.3], [35.8, 35.8]]),
    ('mesopotamien', 'Neubabylonisches Reich', -626, -539, [[38.5, 36.5], [44.0, 36.3], [47.8, 31.0], [48.0, 29.8], [46.0, 29.0], [39.0, 31.0], [35.5, 29.8], [34.2, 31.3], [35.8, 35.5]]),
    ('indus', 'Kerngebiet der Indus-Kultur', -2600, -1900, [[66.5, 30.5], [70.0, 32.5], [74.5, 32.5], [76.5, 30.0], [74.0, 27.0], [72.0, 24.0], [70.5, 22.0], [68.5, 23.2], [67.0, 25.0], [66.5, 28.0]]),
    ('hethiter', 'Hethiterreich (Anatolien)', -1650, -1180, [[27.5, 40.5], [36.0, 41.5], [40.5, 40.3], [40.0, 37.5], [36.5, 36.0], [34.0, 36.5], [30.0, 37.0], [27.5, 38.0]]),
    ('hethiter', 'Nordsyrien (hethitisch)', -1350, -1180, [[36.0, 37.0], [39.5, 37.0], [38.5, 35.0], [36.0, 35.0]]),
    ('shang', 'Shang-Reich', -1600, -1046, [[111.0, 37.0], [117.0, 37.5], [118.0, 34.0], [116.0, 32.5], [112.0, 33.0], [110.5, 35.0]]),
    ('shang', 'Westliche Zhou', -1046, -771, [[105.0, 36.5], [112.0, 38.5], [118.0, 37.5], [120.0, 35.0], [118.0, 32.0], [111.0, 31.5], [106.0, 33.0]]),
    ('shang', 'Östliche Zhou und Streitende Reiche', -770, -221, [[103.0, 36.0], [110.0, 40.0], [119.0, 40.5], [122.0, 37.0], [121.0, 31.0], [118.0, 28.5], [112.0, 28.0], [106.0, 29.0], [103.0, 31.0]]),
    ('perser', 'Perserreich (Achämeniden)', -550, -330, [[26.0, 41.0], [30.0, 42.0], [40.0, 42.0], [48.0, 42.0], [54.0, 40.0], [60.0, 40.0], [67.0, 38.0], [71.0, 37.0], [72.0, 33.0], [70.0, 26.0], [63.0, 25.0], [57.0, 25.5], [52.0, 28.0], [48.5, 30.0], [44.0, 31.0], [38.0, 30.0], [34.2, 31.3], [32.5, 31.0], [26.0, 36.5]]),
    ('perser', 'Ägypten (persisch)', -525, -404, NIL),
]
EREIGNISSE = [
    ('mesopotamien', -3200, 'um 3200 v. Chr.', 'Keilschrift in Uruk', 'In Uruk entstehen die ältesten bekannten Schrifttafeln; zuerst für Verwaltung und Abrechnung.'),
    ('mesopotamien', -2334, 'um 2334 v. Chr.', 'Sargon von Akkad', 'Sargon vereint die Stadtstaaten Mesopotamiens zum ersten großen Reich.'),
    ('mesopotamien', -1754, 'um 1754 v. Chr.', 'Codex Hammurabi', 'König Hammurabi von Babylon lässt eine Gesetzessammlung auf einer Stele aufschreiben.'),
    ('mesopotamien', -612, '612 v. Chr.', 'Fall Ninives', 'Babylonier und Meder zerstören die assyrische Hauptstadt Ninive.'),
    ('aegypten', -3100, 'um 3100 v. Chr.', 'Einigung Ägyptens', 'Ober- und Unterägypten werden zu einem Reich vereint; Beginn der Pharaonenzeit.'),
    ('aegypten', -2560, 'um 2560 v. Chr.', 'Cheops-Pyramide', 'In Giza entsteht die größte Pyramide (Altes Reich).'),
    ('aegypten', -1479, 'um 1479 v. Chr.', 'Neues Reich auf dem Höhepunkt', 'Thutmosis III. dehnt die ägyptische Herrschaft bis nach Syrien und Nubien aus.'),
    ('aegypten', -332, '332 v. Chr.', 'Alexander in Ägypten', 'Alexander der Große erobert Ägypten; danach herrschen die Ptolemäer.'),
    ('indus', -2600, 'um 2600 v. Chr.', 'Städte am Indus', 'Harappa und Mohenjo-Daro wachsen zu großen, planmäßig angelegten Städten.'),
    ('indus', -1900, 'um 1900 v. Chr.', 'Niedergang', 'Die großen Städte werden nach und nach aufgegeben; die Gründe sind umstritten.'),
    ('hethiter', -1650, 'um 1650 v. Chr.', 'Hattuša wird Hauptstadt', 'Das Hethiterreich in Anatolien entsteht.'),
    ('hethiter', -1259, 'um 1259 v. Chr.', 'Friedensvertrag mit Ägypten', 'Nach der Schlacht bei Kadesch schließen Hethiter und Ägypter einen der ältesten erhaltenen Friedensverträge.'),
    ('shang', -1600, 'um 1600 v. Chr.', 'Shang-Dynastie', 'Erste durch Funde belegte Dynastie Chinas; Orakelknochen tragen frühe Schriftzeichen.'),
    ('shang', -1046, 'um 1046 v. Chr.', 'Die Zhou stürzen die Shang', 'Die Zhou-Dynastie übernimmt die Herrschaft am Gelben Fluss.'),
    ('shang', -551, 'um 551 v. Chr.', 'Konfuzius', 'Nach der Überlieferung wird Konfuzius geboren; seine Lehre prägt China bis heute.'),
    ('shang', -221, '221 v. Chr.', 'Qin eint China', 'Qin Shihuangdi beendet die Zeit der Streitenden Reiche; 206 v. Chr. folgt die Han-Dynastie.'),
    ('perser', -550, 'um 550 v. Chr.', 'Kyros II.', 'Kyros begründet das Perserreich; 539 v. Chr. erobert er Babylon.'),
    ('perser', -330, '330 v. Chr.', 'Ende durch Alexander', 'Alexander der Große besiegt Dareios III.; das Perserreich endet.'),
]
SCHLACHTEN = [
    dict(name='Kadesch', jahr=-1274, lng=36.51, lat=34.56, reiche=['aegypten', 'hethiter'], note='Ramses II. gegen die Hethiter unter Muwattalli II.; keiner siegt eindeutig.'),
]
ORTE = [
    ('mesopotamien', 'Uruk', 45.64, 31.32, 1, [[-3500, -539]]),
    ('mesopotamien', 'Ur', 46.10, 30.96, 2, [[-3500, -539]]),
    ('mesopotamien', 'Babylon', 44.42, 32.54, 1, [[-2300, -539]]),
    ('mesopotamien', 'Assur', 43.26, 35.46, 2, [[-2000, -614]]),
    ('mesopotamien', 'Ninive', 43.15, 36.36, 1, [[-911, -612]]),
    ('aegypten', 'Memphis', 31.25, 29.85, 1, [[-3100, -332]]),
    ('aegypten', 'Giza (Pyramiden)', 31.13, 29.98, 2, [[-2600, -332]]),
    ('aegypten', 'Theben', 32.65, 25.70, 1, [[-2100, -332]]),
    ('indus', 'Mohenjo-Daro', 68.14, 27.33, 1, [[-2600, -1900]]),
    ('indus', 'Harappa', 72.86, 30.63, 1, [[-2600, -1900]]),
    ('hethiter', 'Hattuša', 34.61, 40.02, 1, [[-1650, -1180]]),
    ('shang', 'Anyang (Yin)', 114.30, 36.10, 1, [[-1300, -1046]]),
    ('shang', 'Haojing (bei Xi’an)', 108.80, 34.20, 1, [[-1046, -771]]),
    ('shang', 'Luoyang', 112.45, 34.62, 1, [[-770, -221]]),
    ('perser', 'Persepolis', 52.89, 29.93, 1, [[-518, -330]]),
    ('perser', 'Susa', 48.25, 32.19, 1, [[-550, -330]]),
    ('perser', 'Pasargadai', 53.17, 30.20, 2, [[-546, -330]]),
]


def main():
    land = shape(json.load(open(os.path.join(HERE, 'data', 'land.json'), encoding='utf-8'))['geometry']).buffer(0)
    regionen = []
    for i, (r, name, von, bis, umriss) in enumerate(REGIONEN):
        g = Polygon(umriss).buffer(0)
        g = g.intersection(land.buffer(0.08))   # an die Küste anpassen (leicht gepuffert, damit Flussmündungen nicht abreißen)
        g = g.simplify(0.04, preserve_topology=True)
        if g.is_empty: raise SystemExit('leer: ' + name)
        # Umlaufsinn wie in build_reiche.py (im Uhrzeigersinn), sonst deutet d3/globe.gl die Fläche als „Rest der Welt“
        teile = [orient(q, sign=-1.0) for q in (g.geoms if hasattr(g, 'geoms') else [g]) if q.geom_type == 'Polygon']
        g = teile[0] if len(teile) == 1 else MultiPolygon(teile)
        regionen.append({'type': 'Feature', 'properties': {'id': 1001 + i, 'reich': r, 'name': name, 'von': von, 'bis': bis, 'art': 'kern', 'angedeutet': True},
                         'geometry': json.loads(json.dumps(mapping(g)))})
    def runden(o):
        if isinstance(o, float): return round(o, 3)
        if isinstance(o, list): return [runden(x) for x in o]
        if isinstance(o, tuple): return [runden(x) for x in o]
        if isinstance(o, dict): return {k: runden(v) for k, v in o.items()}
        return o
    daten = {
        '_hinweis': 'Frühe Hochkulturen, nur angedeutet (grobe Umrisse, gerundete Jahreszahlen). Erzeugt mit build_fruehe_kulturen.py. '
                    'Format wie data/reiche.json; nur im freien Modus bzw. in Tafelbildern, deren Zeitraum diese Jahre umfasst.',
        'meta': META, 'reihen': REIHEN,
        'regionen': runden(regionen),
        'ereignisse': [dict(reich=r, jahr=j, label=l, titel=t, note=n) for r, j, l, t, n in EREIGNISSE],
        'schlachten': SCHLACHTEN,
        'orte': [dict(reich=r, name=n, lng=x, lat=y, stufe=s, zeiten=z) for r, n, x, y, s, z in ORTE],
    }
    with io.open(ZIEL, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(daten, f, ensure_ascii=False, separators=(',', ':'))
    print('Frühe Hochkulturen:', len(REIHEN), 'Reiche,', len(regionen), 'Flächen,', len(ORTE), 'Orte ->', os.path.relpath(ZIEL, HERE), os.path.getsize(ZIEL), 'Bytes')


if __name__ == '__main__':
    main()
