# -*- coding: utf-8 -*-
"""Frühe Hochkulturen für den freien Modus (data/fruehe_reiche.json).

Bewusst nur ANGEDEUTET: grobe, von Hand gesetzte Umrisse (an die Küstenlinie aus data/land.json angepasst) und
in der Fachliteratur übliche Eckdaten. Viele Jahreszahlen der frühen Zeit sind Näherungen („um“).
Ägypten und Mesopotamien sind nach Epochen gegliedert (Zwischenzeiten, Ur III, Kassiten, Mittel- und Neuassyrien …).
Jahreszahlen nach der konventionellen Chronologie, gerundet: Ägypten nach Shaw, Ian (Hg.): The Oxford History of
Ancient Egypt, Oxford 2000; Mesopotamien nach Van De Mieroop, Marc: A History of the Ancient Near East, ca. 3000–323 BC,
3. Aufl., Chichester 2016 (mittlere Chronologie). Abweichende Datierungen der Forschung sind im Text als umstritten benannt. Die Datei
hat dasselbe Format wie data/reiche.json (meta, reihen, regionen, ereignisse, schlachten, orte) und wird in js/app.js
zu den Kerndaten hinzugefügt. Tafelbilder laden nur Reiche, die in ihren Zeitraum fallen.

    python build_fruehe_kulturen.py
"""
import io, json, os
from shapely.geometry import MultiPolygon, Polygon, box, mapping, shape
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HERE, 'data', 'fruehe_reiche.json')

META = {
    'aegypten': dict(name='Altes Ägypten', von=-3500, bis=-332, farbe='#c8a23a', zentrum=[31.2, 27.0],
                     kurz='Pharaonenreich am Nil: Altes, Mittleres und Neues Reich mit Zwischenzeiten; Pyramiden, Hieroglyphen, Bewässerung.'),
    'mesopotamien': dict(name='Mesopotamien', von=-3500, bis=-539, farbe='#4f86c6', zentrum=[44.5, 33.0],
                         kurz='Zwischen Euphrat und Tigris: Uruk und die sumerischen Stadtstaaten, Akkad, Ur III, Babylon und Assyrien; frühe Städte und Keilschrift.'),
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


def nil(sued, nord):
    """Teil des Niltals zwischen zwei Breitengraden (für die Zwischenzeiten, in denen das Land geteilt war)."""
    return Polygon(NIL).intersection(box(20, sued, 40, nord))


SUMER = [[44.0, 32.6], [46.2, 32.2], [47.8, 30.6], [48.0, 29.9], [46.6, 30.0], [45.0, 31.0], [44.0, 32.0]]
# (reich, name, von, bis, umriss [lng, lat] oder shapely-Fläche)
# Ägypten und Mesopotamien nach Epochen; Jahreszahlen gerundet nach der konventionellen Chronologie
# (Ägypten: Shaw 2000; Mesopotamien: Van De Mieroop 2016, mittlere Chronologie). Grenzen nur angedeutet.
REGIONEN = [
    # --- Ägypten ---
    ('aegypten', 'Niltal in vorgeschichtlicher Zeit (Naqada-Kultur)', -3500, -3100, NIL),
    ('aegypten', 'Frühzeit: geeintes Ägypten (1.–2. Dynastie)', -3100, -2686, NIL),
    ('aegypten', 'Altes Reich (Pyramidenzeit)', -2686, -2160, NIL),
    ('aegypten', 'Erste Zwischenzeit: Herrscher von Herakleopolis (Norden)', -2160, -2055, nil(26.6, 32)),
    ('aegypten', 'Erste Zwischenzeit: Herrscher von Theben (Süden)', -2160, -2055, nil(23, 26.6)),
    ('aegypten', 'Mittleres Reich', -2055, -1650, NIL),
    ('aegypten', 'Unternubien (Mittleres Reich, Festungen bis zum 2. Katarakt)', -1950, -1650,
     [[32.4, 24.1], [33.2, 24.0], [32.4, 22.6], [31.4, 21.4], [30.8, 21.5], [31.6, 22.6], [32.3, 23.4]]),
    ('aegypten', 'Zweite Zwischenzeit: Hyksos (Delta und Mittelägypten)', -1650, -1550, nil(27.4, 32)),
    ('aegypten', 'Zweite Zwischenzeit: Thebanisches Königtum (Oberägypten)', -1650, -1550, nil(23, 27.4)),
    ('aegypten', 'Neues Reich', -1550, -1069, NIL),
    ('aegypten', 'Nubien (Neues Reich)', -1550, -1070, [[31.0, 24.0], [33.6, 24.0], [34.0, 21.0], [33.6, 18.5], [31.5, 18.5], [30.5, 21.0]]),
    ('aegypten', 'Levante (Neues Reich)', -1457, -1180, [[34.2, 31.3], [35.6, 31.2], [36.9, 34.5], [36.7, 35.9], [35.9, 36.0], [35.5, 33.5], [34.3, 31.6]]),
    ('aegypten', 'Dritte Zwischenzeit (Tanis und Theben)', -1069, -664, NIL),
    ('aegypten', 'Spätzeit (Saïs)', -664, -525, NIL),
    ('aegypten', 'Spätzeit: letzte einheimische Pharaonen', -404, -343, NIL),
    # --- Mesopotamien ---
    ('mesopotamien', 'Uruk-Zeit: erste Städte in Südmesopotamien', -3500, -2900, SUMER),
    ('mesopotamien', 'Sumerische Stadtstaaten (Frühdynastische Zeit)', -2900, -2334, SUMER),
    ('mesopotamien', 'Reich von Akkad', -2334, -2154, [[38.0, 36.8], [42.5, 37.2], [45.5, 35.5], [48.3, 30.0], [46.5, 29.8], [43.0, 32.0], [40.0, 34.5], [38.0, 35.5]]),
    ('mesopotamien', 'Sumer nach dem Fall Akkads (Gutäer, Lagasch)', -2154, -2112, SUMER),
    ('mesopotamien', 'Reich der III. Dynastie von Ur', -2112, -2004, [[43.0, 35.6], [45.5, 35.0], [48.6, 32.0], [48.3, 30.0], [46.6, 29.9], [44.0, 31.0], [42.5, 33.5]]),
    ('mesopotamien', 'Isin-Larsa-Zeit (konkurrierende Stadtstaaten)', -2004, -1792, [[43.8, 33.2], [46.2, 32.6], [47.8, 30.6], [48.0, 29.9], [46.6, 30.0], [45.0, 31.0], [43.8, 32.5]]),
    ('mesopotamien', 'Altassyrischer Stadtstaat Assur (Fernhandel)', -2000, -1750, [[42.8, 36.0], [43.8, 36.0], [43.8, 35.0], [42.8, 35.0]]),
    ('mesopotamien', 'Babylonisches Reich (Hammurabi)', -1792, -1595, [[42.5, 36.5], [45.5, 35.8], [48.0, 30.5], [46.6, 29.9], [44.0, 31.0], [42.0, 33.5]]),
    ('mesopotamien', 'Babylonien unter den Kassiten', -1595, -1155, [[43.0, 34.3], [45.5, 34.0], [48.0, 30.5], [46.6, 29.9], [44.0, 31.0], [42.6, 33.0]]),
    ('mesopotamien', 'Mittelassyrisches Reich', -1365, -1050, [[38.0, 37.0], [42.0, 37.6], [44.8, 37.2], [45.5, 35.0], [43.6, 34.2], [40.5, 34.4], [38.0, 35.6]]),
    ('mesopotamien', 'Neuassyrisches Reich', -911, -609, [[35.8, 37.5], [44.5, 38.0], [47.5, 34.0], [48.3, 30.2], [46.5, 29.8], [39.0, 32.5], [35.8, 30.0], [34.2, 31.3], [35.8, 35.8]]),
    ('mesopotamien', 'Neubabylonisches Reich', -626, -539, [[38.5, 36.5], [44.0, 36.3], [47.8, 31.0], [48.0, 29.8], [46.0, 29.0], [39.0, 31.0], [35.5, 29.8], [34.2, 31.3], [35.8, 35.5]]),
    # --- weitere frühe Reiche ---
    ('indus', 'Kerngebiet der Indus-Kultur', -2600, -1900, [[66.5, 30.5], [70.0, 32.5], [74.5, 32.5], [76.5, 30.0], [74.0, 27.0], [72.0, 24.0], [70.5, 22.0], [68.5, 23.2], [67.0, 25.0], [66.5, 28.0]]),
    ('hethiter', 'Hethiterreich (Anatolien)', -1650, -1180, [[27.5, 40.5], [36.0, 41.5], [40.5, 40.3], [40.0, 37.5], [36.5, 36.0], [34.0, 36.5], [30.0, 37.0], [27.5, 38.0]]),
    ('hethiter', 'Nordsyrien (hethitisch)', -1350, -1180, [[36.0, 37.0], [39.5, 37.0], [38.5, 35.0], [36.0, 35.0]]),
    ('shang', 'Shang-Reich', -1600, -1046, [[111.0, 37.0], [117.0, 37.5], [118.0, 34.0], [116.0, 32.5], [112.0, 33.0], [110.5, 35.0]]),
    ('shang', 'Westliche Zhou', -1046, -771, [[105.0, 36.5], [112.0, 38.5], [118.0, 37.5], [120.0, 35.0], [118.0, 32.0], [111.0, 31.5], [106.0, 33.0]]),
    ('shang', 'Östliche Zhou und Streitende Reiche', -770, -221, [[103.0, 36.0], [110.0, 40.0], [119.0, 40.5], [122.0, 37.0], [121.0, 31.0], [118.0, 28.5], [112.0, 28.0], [106.0, 29.0], [103.0, 31.0]]),
    ('perser', 'Perserreich (Achämeniden)', -550, -330, [[26.0, 41.0], [30.0, 42.0], [40.0, 42.0], [48.0, 42.0], [54.0, 40.0], [60.0, 40.0], [67.0, 38.0], [71.0, 37.0], [72.0, 33.0], [70.0, 26.0], [63.0, 25.0], [57.0, 25.5], [52.0, 28.0], [48.5, 30.0], [44.0, 31.0], [38.0, 30.0], [34.2, 31.3], [32.5, 31.0], [26.0, 36.5]]),
    ('perser', 'Ägypten (erste persische Herrschaft)', -525, -404, NIL),
    ('perser', 'Ägypten (zweite persische Herrschaft)', -343, -332, NIL),
]
EREIGNISSE = [
    # --- Mesopotamien ---
    ('mesopotamien', -3500, 'um 3500 v. Chr.', 'Uruk wird zur ersten Großstadt', 'Uruk wächst zur größten Stadt ihrer Zeit. Große Tempel, Verwaltung und Arbeitsteilung entstehen.'),
    ('mesopotamien', -3200, 'um 3200 v. Chr.', 'Keilschrift in Uruk', 'In Uruk entstehen die ältesten bekannten Schrifttafeln; zuerst für Verwaltung und Abrechnung.'),
    ('mesopotamien', -2900, 'um 2900 v. Chr.', 'Sumerische Stadtstaaten', 'Sumer ist in rivalisierende Stadtstaaten wie Ur, Uruk, Lagasch und Kisch geteilt. Jede Stadt verehrt ihren eigenen Stadtgott.'),
    ('mesopotamien', -2600, 'um 2600 v. Chr.', 'Königsgräber von Ur', 'In Ur werden reiche Gräber mit Goldschmuck und Musikinstrumenten angelegt; mit den Toten wurden auch Gefolgsleute bestattet (Ablauf im Einzelnen umstritten).'),
    ('mesopotamien', -2334, 'um 2334 v. Chr.', 'Sargon von Akkad', 'Sargon vereint die Stadtstaaten Mesopotamiens zum ersten großen Reich.'),
    ('mesopotamien', -2154, 'um 2154 v. Chr.', 'Ende des Reiches von Akkad', 'Das Reich zerfällt; die Gutäer aus dem Zagros-Gebirge gewinnen Einfluss. Ob auch eine Dürre beitrug, ist umstritten.'),
    ('mesopotamien', -2112, 'um 2112 v. Chr.', 'Ur-Nammu und die III. Dynastie von Ur', 'Ur-Nammu begründet ein straff verwaltetes Reich und lässt die große Zikkurat von Ur bauen. Aus dieser Zeit stammt eine der ältesten Gesetzessammlungen.'),
    ('mesopotamien', -2004, 'um 2004 v. Chr.', 'Fall von Ur', 'Elamiter erobern Ur. Danach ringen die Städte Isin und Larsa um die Vorherrschaft.'),
    ('mesopotamien', -1950, 'um 1950 v. Chr.', 'Kaufleute aus Assur in Anatolien', 'Händler aus Assur bringen Zinn und Stoffe bis nach Kaneš in Anatolien. Tausende ihrer Briefe auf Tontafeln sind erhalten.'),
    ('mesopotamien', -1792, 'um 1792 v. Chr.', 'Hammurabi wird König von Babylon', 'Hammurabi besteigt den Thron und vereint später fast ganz Mesopotamien unter Babylon.'),
    ('mesopotamien', -1754, 'um 1754 v. Chr.', 'Codex Hammurabi', 'König Hammurabi von Babylon lässt eine Gesetzessammlung auf einer Stele aufschreiben.'),
    ('mesopotamien', -1595, 'um 1595 v. Chr.', 'Hethiter plündern Babylon', 'Der Hethiterkönig Muršili I. erobert Babylon. Danach herrschen die Kassiten über Babylonien – über 400 Jahre lang.'),
    ('mesopotamien', -1365, 'um 1365 v. Chr.', 'Assyrien wird Großmacht', 'Unter Aššur-uballiṭ I. steigt Assyrien zur Großmacht auf und schreibt Briefe an den Pharao (Amarna-Briefe).'),
    ('mesopotamien', -911, 'um 911 v. Chr.', 'Neuassyrisches Reich', 'Mit jährlichen Feldzügen beginnen die assyrischen Könige, ein Großreich aufzubauen.'),
    ('mesopotamien', -745, 'um 745 v. Chr.', 'Tiglat-Pileser III.', 'Er schafft ein stehendes Heer und siedelt unterworfene Völker um. Assyrien wird zum größten Reich seiner Zeit.'),
    ('mesopotamien', -705, 'um 705 v. Chr.', 'Sanherib baut Ninive aus', 'Ninive wird prächtige Hauptstadt mit Palästen und Wasserleitungen. 701 v. Chr. belagert Sanherib Jerusalem.'),
    ('mesopotamien', -668, 'um 668 v. Chr.', 'Assurbanipal und seine Bibliothek', 'In Ninive lässt Assurbanipal Tausende Keilschrifttafeln sammeln – darunter das Gilgamesch-Epos.'),
    ('mesopotamien', -612, '612 v. Chr.', 'Fall Ninives', 'Babylonier und Meder zerstören die assyrische Hauptstadt Ninive.'),
    ('mesopotamien', -605, 'um 605 v. Chr.', 'Nebukadnezar II.', 'Babylon wird prächtig ausgebaut: Ischtar-Tor, Prozessionsstraße und der Tempelturm Etemenanki.'),
    ('mesopotamien', -587, 'um 587 v. Chr.', 'Zerstörung Jerusalems', 'Nebukadnezar erobert Jerusalem; ein Teil der Bevölkerung wird nach Babylon verschleppt (Babylonisches Exil). Das genaue Jahr – 587 oder 586 – ist umstritten.'),
    # --- Ägypten ---
    ('aegypten', -3500, 'um 3500 v. Chr.', 'Naqada-Kultur am Nil', 'Bauern am Nil leben in wachsenden Dörfern; Häuptlinge und erste Zentren wie Hierakonpolis entstehen.'),
    ('aegypten', -3300, 'um 3300 v. Chr.', 'Frühe Schriftzeichen in Abydos', 'In einem Grab in Abydos fanden sich beschriftete Täfelchen – mit die ältesten Schriftzeugnisse Ägyptens. Die genaue Datierung ist umstritten.'),
    ('aegypten', -3100, 'um 3100 v. Chr.', 'Einigung Ägyptens', 'Ober- und Unterägypten werden zu einem Reich vereint; die Narmer-Palette zeigt einen König mit beiden Kronen. Beginn der Pharaonenzeit.'),
    ('aegypten', -2686, 'um 2686 v. Chr.', 'Beginn des Alten Reiches', 'Mit der 3. Dynastie beginnt das Alte Reich; Hauptstadt ist Memphis.'),
    ('aegypten', -2650, 'um 2650 v. Chr.', 'Stufenpyramide des Djoser', 'In Sakkara entsteht der erste große Steinbau Ägyptens; als Baumeister gilt Imhotep.'),
    ('aegypten', -2600, 'um 2600 v. Chr.', 'Snofru baut die ersten echten Pyramiden', 'In Meidum und Dahschur entstehen die Knickpyramide und die Rote Pyramide.'),
    ('aegypten', -2560, 'um 2560 v. Chr.', 'Cheops-Pyramide', 'In Giza entsteht die größte Pyramide (Altes Reich).'),
    ('aegypten', -2160, 'um 2160 v. Chr.', 'Erste Zwischenzeit', 'Das Königtum zerfällt: Herrscher in Herakleopolis und in Theben ringen um die Macht. Ob schwache Nilfluten dazu beitrugen, ist umstritten.'),
    ('aegypten', -2055, 'um 2055 v. Chr.', 'Beginn des Mittleren Reiches', 'Mentuhotep II. aus Theben eint Ägypten erneut.'),
    ('aegypten', -1950, 'um 1950 v. Chr.', 'Festungen in Nubien', 'Die Könige der 12. Dynastie sichern Unternubien bis zum zweiten Nilkatarakt mit großen Festungen wie Buhen.'),
    ('aegypten', -1650, 'um 1650 v. Chr.', 'Hyksos im Nildelta', 'Herrscher vorderasiatischer Herkunft, die Hyksos, regieren von Auaris aus den Norden. Sie gelten als Vermittler von Pferd und Streitwagen.'),
    ('aegypten', -1550, 'um 1550 v. Chr.', 'Beginn des Neuen Reiches', 'Ahmose vertreibt die Hyksos und eint Ägypten wieder.'),
    ('aegypten', -1473, 'um 1473 v. Chr.', 'Hatschepsut', 'Hatschepsut regiert als Pharaonin. Berühmt sind ihr Totentempel in Deir el-Bahari und eine Handelsfahrt in das Land Punt.'),
    ('aegypten', -1457, 'um 1457 v. Chr.', 'Feldzüge Thutmosis’ III.', 'Nach dem Sieg bei Megiddo dehnt Thutmosis III. die ägyptische Herrschaft bis nach Syrien aus; das Neue Reich ist auf dem Höhepunkt.'),
    ('aegypten', -1353, 'um 1353 v. Chr.', 'Echnaton und Amarna', 'Echnaton verehrt fast nur noch den Sonnengott Aton und gründet die neue Hauptstadt Achet-Aton (Amarna). Nach seinem Tod wird die Reform rückgängig gemacht.'),
    ('aegypten', -1332, 'um 1332 v. Chr.', 'Tutanchamun', 'Der junge König kehrt zu den alten Göttern zurück. Berühmt wurde er durch sein fast unberührtes Grab, entdeckt 1922.'),
    ('aegypten', -1279, 'um 1279 v. Chr.', 'Ramses II.', 'Ramses II. regiert 66 Jahre, lässt Abu Simbel bauen und verlegt die Residenz nach Pi-Ramesse im Delta.'),
    ('aegypten', -1177, 'um 1177 v. Chr.', 'Abwehr der Seevölker', 'Ramses III. wehrt Angriffe der „Seevölker“ ab (Reliefs in Medinet Habu). In dieser Zeit brechen viele Reiche im östlichen Mittelmeer zusammen.'),
    ('aegypten', -1069, 'um 1069 v. Chr.', 'Dritte Zwischenzeit', 'Nach dem Ende des Neuen Reiches teilen sich Könige in Tanis und Hohepriester in Theben die Macht.'),
    ('aegypten', -728, 'um 728 v. Chr.', 'Pharaonen aus Kusch', 'König Pije aus Kusch (Nubien) erobert Ägypten; seine Nachfolger regieren als 25. Dynastie.'),
    ('aegypten', -664, '664 v. Chr.', 'Spätzeit', 'Psammetich I. aus Saïs eint das Land wieder. Griechische Händler lassen sich in Naukratis nieder.'),
    ('aegypten', -404, '404 v. Chr.', 'Wieder unabhängig', 'Ägypten befreit sich von den Persern; es regieren die letzten einheimischen Pharaonen bis 343 v. Chr.'),
    ('aegypten', -332, '332 v. Chr.', 'Alexander in Ägypten', 'Alexander der Große erobert Ägypten; danach herrschen die Ptolemäer.'),
    # --- weitere frühe Reiche ---
    ('indus', -2600, 'um 2600 v. Chr.', 'Städte am Indus', 'Harappa und Mohenjo-Daro wachsen zu großen, planmäßig angelegten Städten.'),
    ('indus', -1900, 'um 1900 v. Chr.', 'Niedergang', 'Die großen Städte werden nach und nach aufgegeben; die Gründe sind umstritten.'),
    ('hethiter', -1650, 'um 1650 v. Chr.', 'Hattuša wird Hauptstadt', 'Das Hethiterreich in Anatolien entsteht.'),
    ('hethiter', -1259, 'um 1259 v. Chr.', 'Friedensvertrag mit Ägypten', 'Nach der Schlacht bei Kadesch schließen Hethiter und Ägypter einen der ältesten erhaltenen Friedensverträge.'),
    ('shang', -1600, 'um 1600 v. Chr.', 'Shang-Dynastie', 'Erste durch Funde belegte Dynastie Chinas; Orakelknochen tragen frühe Schriftzeichen.'),
    ('shang', -1046, 'um 1046 v. Chr.', 'Die Zhou stürzen die Shang', 'Die Zhou-Dynastie übernimmt die Herrschaft am Gelben Fluss.'),
    ('shang', -551, 'um 551 v. Chr.', 'Konfuzius', 'Nach der Überlieferung wird Konfuzius geboren; seine Lehre prägt China bis heute.'),
    ('shang', -221, '221 v. Chr.', 'Qin eint China', 'Qin Shihuangdi beendet die Zeit der Streitenden Reiche; 206 v. Chr. folgt die Han-Dynastie.'),
    ('perser', -550, 'um 550 v. Chr.', 'Kyros II.', 'Kyros begründet das Perserreich; 539 v. Chr. erobert er Babylon.'),
    ('perser', -525, '525 v. Chr.', 'Kambyses erobert Ägypten', 'Der Perserkönig Kambyses II. besiegt den Pharao Psammetich III.; Ägypten wird persische Provinz.'),
    ('perser', -330, '330 v. Chr.', 'Ende durch Alexander', 'Alexander der Große besiegt Dareios III.; das Perserreich endet.'),
]
SCHLACHTEN = [
    dict(name='Megiddo', jahr=-1457, lng=35.18, lat=32.59, reiche=['aegypten'], note='Thutmosis III. besiegt eine Koalition kanaanäischer Fürsten; die erste Schlacht, deren Ablauf ausführlich überliefert ist.'),
    dict(name='Kadesch', jahr=-1274, lng=36.51, lat=34.56, reiche=['aegypten', 'hethiter'], note='Ramses II. gegen die Hethiter unter Muwattalli II.; keiner siegt eindeutig.'),
]
ORTE = [
    # --- Mesopotamien ---
    ('mesopotamien', 'Uruk', 45.64, 31.32, 1, [[-3500, -539]]),
    ('mesopotamien', 'Ur', 46.10, 30.96, 2, [[-3500, -539]]),
    ('mesopotamien', 'Eridu', 46.00, 30.82, 3, [[-3500, -2000]]),
    ('mesopotamien', 'Nippur', 45.23, 32.13, 2, [[-3000, -539]]),
    ('mesopotamien', 'Kisch', 44.58, 32.54, 2, [[-2900, -1600]]),
    ('mesopotamien', 'Girsu (Lagasch)', 46.18, 31.55, 3, [[-2600, -2000]]),
    ('mesopotamien', 'Mari', 40.89, 34.55, 2, [[-2900, -1759]]),
    ('mesopotamien', 'Isin', 45.27, 31.88, 3, [[-2000, -1700]]),
    ('mesopotamien', 'Larsa', 45.85, 31.29, 3, [[-2000, -1750]]),
    ('mesopotamien', 'Babylon', 44.42, 32.54, 1, [[-2300, -539]]),
    ('mesopotamien', 'Assur', 43.26, 35.46, 2, [[-2000, -614]]),
    ('mesopotamien', 'Kaneš (assyrische Handelsniederlassung)', 35.63, 38.85, 3, [[-1950, -1750]]),
    ('mesopotamien', 'Kalḫu (Nimrud)', 43.33, 36.10, 2, [[-879, -612]]),
    ('mesopotamien', 'Dur-Šarrukin (Chorsabad)', 43.23, 36.51, 3, [[-717, -705]]),
    ('mesopotamien', 'Ninive', 43.15, 36.36, 1, [[-911, -612]]),
    # --- Ägypten ---
    ('aegypten', 'Hierakonpolis (Nechen)', 32.78, 25.10, 3, [[-3500, -2600]]),
    ('aegypten', 'Abydos', 31.92, 26.18, 2, [[-3500, -332]]),
    ('aegypten', 'Elephantine (Assuan)', 32.89, 24.08, 3, [[-3000, -332]]),
    ('aegypten', 'Memphis', 31.25, 29.85, 1, [[-3100, -332]]),
    ('aegypten', 'Sakkara (Stufenpyramide)', 31.22, 29.87, 3, [[-2650, -332]]),
    ('aegypten', 'Dahschur (Pyramiden)', 31.21, 29.80, 3, [[-2600, -332]]),
    ('aegypten', 'Giza (Pyramiden)', 31.13, 29.98, 2, [[-2600, -332]]),
    ('aegypten', 'Herakleopolis', 30.94, 29.09, 3, [[-2160, -2025]]),
    ('aegypten', 'Theben', 32.65, 25.70, 1, [[-2100, -332]]),
    ('aegypten', 'Itj-taui (bei el-Lischt)', 31.22, 29.57, 3, [[-1985, -1650]]),
    ('aegypten', 'Buhen (Festung)', 31.33, 21.87, 3, [[-1950, -1070]]),
    ('aegypten', 'Auaris (Hyksos-Hauptstadt)', 31.82, 30.79, 2, [[-1700, -1530]]),
    ('aegypten', 'Achet-Aton (Amarna)', 30.90, 27.65, 2, [[-1346, -1332]]),
    ('aegypten', 'Pi-Ramesse', 31.83, 30.80, 2, [[-1270, -1070]]),
    ('aegypten', 'Abu Simbel', 31.63, 22.34, 3, [[-1264, -332]]),
    ('aegypten', 'Napata (Gebel Barkal)', 31.83, 18.53, 3, [[-1450, -1070]]),
    ('aegypten', 'Tanis', 31.88, 30.97, 2, [[-1069, -664]]),
    ('aegypten', 'Saïs', 30.77, 30.96, 2, [[-664, -525]]),
    # --- weitere frühe Reiche ---
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
        g = (umriss if hasattr(umriss, 'geom_type') else Polygon(umriss)).buffer(0)
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
        'meta': {k: dict(v, frueh=True) for k, v in META.items()}, 'reihen': REIHEN,   # frueh: Infokarte zeigt Epoche und Ereignis
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
