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
    'nubien': dict(name='Nubien: Kerma und Kusch', von=-2400, bis=-300, farbe='#6b8e23', zentrum=[31.5, 19.5],
                   kurz='Reiche am oberen Nil: Kerma (bis um 1450 v. Chr.), später Kusch mit Napata; die Könige von Kusch beherrschen um 728–664 v. Chr. Ägypten.'),
    'minoer': dict(name='Minoisches Kreta', von=-1900, bis=-1300, farbe='#e07a5f', zentrum=[24.9, 35.2],
                   kurz='Palastkultur auf Kreta (Knossos, Phaistos, Malia); nach 1450 v. Chr. herrschen in Knossos Griechisch sprechende Eliten (Linear B).'),
    'mykener': dict(name='Mykenisches Griechenland', von=-1600, bis=-1100, farbe='#8d6e63', zentrum=[22.6, 37.7],
                    kurz='Burgen und Paläste wie Mykene, Tiryns, Pylos und Theben; Verwaltung mit Linear-B-Tafeln; um 1200 v. Chr. brechen die Paläste zusammen.'),
    'athen': dict(name='Athen und die Attischen Seebünde', von=-508, bis=-338, farbe='#1fa2c8', zentrum=[24.5, 38.0],
                  kurz='Athen nach den Reformen des Kleisthenes, Vormacht des Delisch-Attischen Seebunds (478/7–404 v. Chr.) und des Zweiten Seebunds (378/7 v. Chr.).'),
    'sparta': dict(name='Sparta und der Peloponnesische Bund', von=-700, bis=-338, farbe='#9b2335', zentrum=[22.4, 37.2],
                   kurz='Militärstaat auf der Peloponnes; führt seit dem 6. Jh. v. Chr. den Peloponnesischen Bund, besiegt Athen 404 v. Chr., verliert 371 v. Chr. bei Leuktra.'),
    'makedonien': dict(name='Makedonien und das Reich Alexanders', von=-359, bis=-168, farbe='#d4a017', zentrum=[40.0, 35.0],
                       kurz='Philipp II. macht Makedonien zur Vormacht Griechenlands; sein Sohn Alexander erobert das Perserreich bis zum Indus. Nach 323 v. Chr. teilen die Diadochen das Reich.'),
    'perser': dict(name='Perserreich (Achämeniden)', von=-550, bis=-330, farbe='#b5477a', zentrum=[53.0, 32.0],
                   kurz='Von Kyros II. gegründetes Großreich vom Mittelmeer bis zum Indus; endet mit Alexander dem Großen.'),
}
REIHEN = ['mesopotamien', 'aegypten', 'nubien', 'indus', 'minoer', 'mykener', 'hethiter', 'athen', 'sparta', 'makedonien', 'shang', 'perser']

NIL = [[29.6, 31.6], [32.3, 31.3], [31.5, 30.0], [31.3, 27.5], [33.0, 26.0], [33.0, 24.0], [32.6, 24.0], [32.2, 26.0], [30.6, 27.8], [30.4, 29.5], [29.6, 30.8]]


def nil(sued, nord):
    """Teil des Niltals zwischen zwei Breitengraden (für die Zwischenzeiten, in denen das Land geteilt war)."""
    return Polygon(NIL).intersection(box(20, sued, 40, nord))


# Ägäis (Inseln und Küsten), Attika, Peloponnes – grob, wird an die Küstenlinie angepasst
AEGAEIS = Polygon([[22.9, 40.9], [24.0, 41.0], [26.0, 40.9], [26.6, 40.6], [27.8, 40.6], [29.0, 41.2], [29.3, 40.8], [27.6, 40.2], [27.2, 39.4],
                   [27.6, 38.4], [27.6, 37.4], [28.3, 36.8], [28.0, 36.3], [27.0, 35.8], [25.5, 36.2], [24.0, 36.6], [23.2, 37.3], [23.3, 37.9],
                   [23.9, 38.4], [23.0, 39.0], [23.2, 39.6], [22.8, 40.2]])
MITTELGRIECHENLAND = Polygon([[22.0, 39.4], [23.62, 38.8], [23.58, 38.25], [22.8, 38.0], [22.0, 38.3]])
ATTIKA = Polygon([[23.35, 38.3], [24.1, 38.3], [24.1, 37.6], [23.6, 37.6], [23.35, 37.95]])
KLEINASIEN = Polygon([[26.9, 41.5], [30, 41.5], [30, 35], [26.9, 35]])
PELOPONNES = Polygon([[21.1, 38.3], [22.9, 38.2], [23.2, 37.9], [23.4, 37.3], [23.2, 36.4], [22.5, 36.4], [21.6, 36.7], [21.1, 37.6]])
ARGOLIS = Polygon([[22.55, 37.8], [23.0, 37.8], [23.3, 37.45], [22.75, 37.35], [22.55, 37.55]])
LAKONIEN_MESSENIEN = [[21.6, 37.4], [22.6, 37.4], [23.2, 36.8], [22.9, 36.4], [22.4, 36.4], [21.6, 36.7]]
SEEBUND_1 = AEGAEIS.union(ATTIKA).difference(MITTELGRIECHENLAND).difference(PELOPONNES)
SEEBUND_2 = SEEBUND_1.difference(KLEINASIEN)   # Königsfrieden 387/6 v. Chr.: Ionien persisch
PERSIEN = Polygon([[26.0, 41.0], [30.0, 42.0], [40.0, 42.0], [48.0, 42.0], [54.0, 40.0], [60.0, 40.0], [67.0, 38.0], [71.0, 37.0], [72.0, 33.0], [70.0, 26.0], [63.0, 25.0], [57.0, 25.5], [52.0, 28.0], [48.5, 30.0], [44.0, 31.0], [38.0, 30.0], [34.2, 31.3], [32.5, 31.0], [26.0, 36.5]])
MAKEDONIEN = Polygon([[20.5, 41.8], [24.5, 41.9], [26.6, 41.2], [26.0, 40.6], [23.5, 39.9], [22.5, 39.0], [21.5, 39.3], [20.5, 40.5]])
GRIECHENLAND = MAKEDONIEN.union(PELOPONNES).union(MITTELGRIECHENLAND).union(ATTIKA).union(Polygon([[21.0, 39.6], [23.3, 39.9], [23.0, 38.7], [21.2, 38.6]]))
INDUS = Polygon([[66.0, 36.5], [72.0, 35.5], [75.5, 32.5], [74.5, 30.0], [70.0, 25.5], [67.0, 24.2], [64.5, 26.0]])
NILTAL = Polygon(NIL)
ALEX_1 = GRIECHENLAND.union(PERSIEN.intersection(box(20, 30, 33, 43)))                                   # 334: Kleinasien
ALEX_2 = GRIECHENLAND.union(PERSIEN.intersection(box(20, 28, 39, 43))).union(NILTAL)                    # 333–331: Levante, Ägypten
ALEX_3 = GRIECHENLAND.union(PERSIEN.intersection(box(20, 24, 55, 43))).union(NILTAL)                    # 331–329: Mesopotamien, Persis
ALEX_4 = GRIECHENLAND.union(PERSIEN).union(NILTAL).union(INDUS)                                         # 329–323: bis zum Indus
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
    ('aegypten', 'Unternubien (frühes Neues Reich)', -1550, -1450,
     [[32.4, 24.1], [33.2, 24.0], [32.4, 22.6], [31.4, 21.4], [30.8, 21.5], [31.6, 22.6], [32.3, 23.4]]),
    # UEE (Kuckertz 2021): zu Beginn der 18. Dynastie Eroberung Nubiens bis Kurgus zwischen 4. und 5. Katarakt
    ('aegypten', 'Nubien bis Kurgus (Neues Reich)', -1450, -1070, [[31.0, 24.0], [33.6, 24.0], [34.0, 21.0], [33.9, 19.2], [32.6, 18.2], [31.2, 18.0], [30.2, 19.5], [30.5, 21.0]]),
    ('aegypten', 'Levante (Neues Reich)', -1457, -1180, [[34.2, 31.3], [35.6, 31.2], [36.9, 34.5], [36.7, 35.9], [35.9, 36.0], [35.5, 33.5], [34.3, 31.6]]),
    ('aegypten', 'Dritte Zwischenzeit (Tanis und Theben)', -1069, -728, NIL),
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
    # --- Nubien ---
    ('nubien', 'Königreich Kerma', -2400, -1450, [[29.8, 21.3], [31.0, 21.3], [32.2, 19.6], [32.0, 18.3], [30.6, 18.6], [29.8, 19.8]]),
    ('nubien', 'Königreich Kusch (Napata)', -800, -300, [[30.4, 20.8], [31.6, 20.8], [33.8, 19.4], [34.2, 16.5], [32.6, 16.0], [31.4, 18.0], [30.2, 19.5]]),
    ('nubien', 'Kusch beherrscht Ägypten (25. Dynastie)', -728, -664, NIL),
    # --- Ägäis: Minoer und Mykener (Kreta-Daten nach JAR 2023; Kollaps um 1200 nach Middleton 2008) ---
    ('minoer', 'Kreta: Ältere Paläste (Knossos, Phaistos, Malia)', -1900, -1700, [[23.5, 35.7], [26.4, 35.4], [26.4, 34.9], [23.5, 35.1]]),
    ('minoer', 'Kreta: Jüngere Paläste und Seehandel', -1700, -1450, [[23.5, 35.7], [26.4, 35.4], [26.4, 34.9], [23.5, 35.1]]),
    ('minoer', 'Knossos unter mykenischer Herrschaft (Linear B)', -1450, -1300, [[23.5, 35.7], [26.4, 35.4], [26.4, 34.9], [23.5, 35.1]]),
    ('mykener', 'Argolis: Schachtgräberzeit (Mykene)', -1600, -1400, [[22.4, 37.95], [23.1, 37.95], [23.2, 37.45], [22.6, 37.4]]),
    ('mykener', 'Palastzeit: Mykene, Tiryns, Pylos, Theben', -1400, -1200, PELOPONNES.union(MITTELGRIECHENLAND).union(ATTIKA)),
    ('mykener', 'Nachpalastzeit (Kleinreiche)', -1200, -1100, PELOPONNES),
    # --- Athen und Sparta (Daten nach Kagan, Yale CLCV 205; Thukydides; Xenophon; Marshall 1905) ---
    ('athen', 'Athen (Attika)', -508, -478, ATTIKA),
    ('athen', 'Delisch-Attischer Seebund', -478, -404, SEEBUND_1),
    ('athen', 'Athen nach der Niederlage', -404, -378, ATTIKA),
    ('athen', 'Zweiter Attischer Seebund', -378, -355, SEEBUND_2),
    ('athen', 'Athen nach dem Bundesgenossenkrieg', -355, -338, ATTIKA),
    ('sparta', 'Sparta (Lakonien und Messenien)', -700, -550, LAKONIEN_MESSENIEN),
    ('sparta', 'Peloponnesischer Bund', -550, -371, PELOPONNES.difference(ARGOLIS)),
    ('sparta', 'Sparta nach Leuktra (ohne Messenien)', -371, -338, [[22.2, 37.4], [22.6, 37.4], [23.2, 36.8], [22.9, 36.4], [22.4, 36.4], [22.2, 36.8]]),
    # --- Makedonien und Alexander (Arrian, Anabasis; Gebiete angedeutet) ---
    ('makedonien', 'Makedonien unter Philipp II.', -359, -338, MAKEDONIEN),
    ('makedonien', 'Makedonische Vorherrschaft (Korinthischer Bund)', -338, -334, GRIECHENLAND),
    ('makedonien', 'Reich Alexanders: Kleinasien erobert', -334, -333, ALEX_1),
    ('makedonien', 'Reich Alexanders: bis Syrien und Ägypten', -333, -331, ALEX_2),
    ('makedonien', 'Reich Alexanders: Mesopotamien und Persis', -331, -329, ALEX_3),
    ('makedonien', 'Reich Alexanders: bis zum Indus', -329, -323, ALEX_4),
    ('makedonien', 'Alexanderreich unter den Diadochen (Nachfolgekämpfe)', -323, -301, ALEX_4),
    ('makedonien', 'Makedonien der Antigoniden', -301, -168, MAKEDONIEN.union(Polygon([[21.0, 39.6], [23.3, 39.9], [23.0, 38.7], [21.2, 38.6]]))),
    # --- weitere frühe Reiche ---
    ('indus', 'Kerngebiet der Indus-Kultur', -2600, -1900, [[66.5, 30.5], [70.0, 32.5], [74.5, 32.5], [76.5, 30.0], [74.0, 27.0], [72.0, 24.0], [70.5, 22.0], [68.5, 23.2], [67.0, 25.0], [66.5, 28.0]]),
    ('hethiter', 'Hethiterreich (Anatolien)', -1650, -1180, [[27.5, 40.5], [36.0, 41.5], [40.5, 40.3], [40.0, 37.5], [36.5, 36.0], [34.0, 36.5], [30.0, 37.0], [27.5, 38.0]]),
    ('hethiter', 'Nordsyrien (hethitisch)', -1350, -1180, [[36.0, 37.0], [39.5, 37.0], [38.5, 35.0], [36.0, 35.0]]),
    ('shang', 'Shang-Reich', -1600, -1046, [[111.0, 37.0], [117.0, 37.5], [118.0, 34.0], [116.0, 32.5], [112.0, 33.0], [110.5, 35.0]]),
    ('shang', 'Westliche Zhou', -1046, -771, [[105.0, 36.5], [112.0, 38.5], [118.0, 37.5], [120.0, 35.0], [118.0, 32.0], [111.0, 31.5], [106.0, 33.0]]),
    ('shang', 'Östliche Zhou und Streitende Reiche', -770, -221, [[103.0, 36.0], [110.0, 40.0], [119.0, 40.5], [122.0, 37.0], [121.0, 31.0], [118.0, 28.5], [112.0, 28.0], [106.0, 29.0], [103.0, 31.0]]),
    # Ionien und die Inseln gehören 478/7–387/6 v. Chr. zum Seebund bzw. sind umkämpft (Kalliasfrieden 449, Königsfrieden 387/6)
    ('perser', 'Perserreich (Achämeniden)', -550, -478, PERSIEN),
    ('perser', 'Perserreich (ohne Ionien und die Inseln)', -478, -387, PERSIEN.difference(SEEBUND_1.buffer(0.15))),
    ('perser', 'Perserreich (Achämeniden)', -387, -334, PERSIEN),
    ('perser', 'Perserreich (ohne Kleinasien)', -334, -333, PERSIEN.difference(box(20, 30, 33, 43))),
    ('perser', 'Perserreich (ohne Kleinasien, Levante, Ägypten)', -333, -331, PERSIEN.difference(box(20, 28, 39, 43))),
    ('perser', 'Perserreich (Rest im Osten)', -331, -330, PERSIEN.difference(box(20, 24, 55, 43))),
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
    ('aegypten', -1555, 'um 1555 v. Chr.', 'Kamose gegen die Hyksos', 'Der thebanische König Kamose zieht gegen die Hyksos nach Norden; sein Nachfolger Ahmose setzt den Kampf fort.'),
    ('aegypten', -1550, 'um 1550 v. Chr.', 'Beginn des Neuen Reiches', 'Ahmose erobert Auaris, vertreibt die Hyksos und eint Ägypten wieder.', 'Breasted, History of Egypt (1905), Buch IV (Biografie des Ahmose, Sohn der Ebana)'),
    ('aegypten', -1500, 'um 1500 v. Chr.', 'Feldzüge nach Nubien', 'Zu Beginn der 18. Dynastie erobert Ägypten Nubien bis Kurgus zwischen dem 4. und 5. Katarakt; das Reich von Kerma geht unter.', 'Kuckertz, Meroe and Egypt, UEE 2021, PDF-S. 4'),
    ('aegypten', -1473, 'um 1473 v. Chr.', 'Hatschepsut', 'Hatschepsut regiert als Pharaonin. Berühmt sind ihr Totentempel in Deir el-Bahari und eine Handelsfahrt in das Land Punt.'),
    ('aegypten', -1457, 'um 1457 v. Chr.', 'Feldzüge Thutmosis’ III.', 'Im Jahr 23 seiner Regierung siegt Thutmosis III. bei Megiddo und dehnt die Herrschaft bis nach Syrien aus. Nach anderer Chronologie war die Schlacht 1482 v. Chr.', 'Nelson, The Battle of Megiddo (1913), S. 5 (Annalen von Karnak)'),
    ('aegypten', -1353, 'um 1353 v. Chr.', 'Echnaton und Amarna', 'Echnaton verehrt fast nur noch den Sonnengott Aton und gründet die neue Hauptstadt Achet-Aton (Amarna). Nach seinem Tod wird die Reform rückgängig gemacht.'),
    ('aegypten', -1332, 'um 1332 v. Chr.', 'Tutanchamun', 'Der junge König kehrt zu den alten Göttern zurück. Berühmt wurde er durch sein fast unberührtes Grab, entdeckt 1922.'),
    ('aegypten', -1290, 'um 1290 v. Chr.', 'Sethos I.', 'Sethos I. führt Feldzüge nach Palästina und Syrien, gegen die Libyer und gegen die Hethiter. Die Reihenfolge der Kriege ist unsicher.', 'Breasted, Ancient Records of Egypt III (1906): Reliefs von Karnak'),
    ('aegypten', -1279, 'um 1279 v. Chr.', 'Ramses II.', 'Ramses II. regiert 66 Jahre, lässt Abu Simbel bauen und verlegt die Residenz nach Pi-Ramesse im Delta.'),
    ('aegypten', -1208, 'um 1208 v. Chr.', 'Merenptah gegen Libyer und „Nordvölker“', 'Merenptah besiegt Libyer und ihre Verbündeten – Ekwesch, Teresch, Lukka, Scherden und Schekelesch. Seine Siegesstele nennt zum ersten Mal den Namen „Israel“.', 'Breasted, Ancient Records III, § 574; Breasted, History of Egypt, S. 465'),
    ('aegypten', -1177, 'um 1177 v. Chr.', 'Abwehr der Seevölker', 'Ramses III. wehrt Angriffe der „Seevölker“ ab, darunter die Peleset (Philister); Reliefs in Medinet Habu zeigen die Seeschlacht. In dieser Zeit brechen viele Reiche im östlichen Mittelmeer zusammen – die Ursachen sind umstritten.', 'Breasted, History of Egypt, S. 464–480; Knapp/Manning, AJA 120 (2016)'),
    ('aegypten', -1069, 'um 1069 v. Chr.', 'Dritte Zwischenzeit', 'Nach dem Ende des Neuen Reiches teilen sich Könige in Tanis und Hohepriester in Theben die Macht.'),

    ('aegypten', -664, '664 v. Chr.', 'Spätzeit', 'Psammetich I. aus Saïs eint das Land wieder. Griechische Händler lassen sich in Naukratis nieder.'),
    ('aegypten', -404, '404 v. Chr.', 'Wieder unabhängig', 'Ägypten befreit sich von den Persern; es regieren die letzten einheimischen Pharaonen bis 343 v. Chr.'),
    ('aegypten', -332, '332 v. Chr.', 'Alexander in Ägypten', 'Alexander der Große erobert Ägypten; danach herrschen die Ptolemäer.'),
    # --- Nubien ---
    ('nubien', -2400, 'um 2400 v. Chr.', 'Königreich Kerma', 'Am oberen Nil entsteht das Reich von Kerma – für Ägypten Handelspartner und gefährlicher Nachbar zugleich.', 'Kuckertz, Meroe and Egypt, UEE 2021, PDF-S. 4'),
    ('nubien', -800, 'um 800 v. Chr.', 'Königreich Kusch', 'Bei Napata am Gebel Barkal entsteht das Königreich Kusch; seine Könige verehren den ägyptischen Gott Amun.'),
    ('nubien', -728, 'um 728 v. Chr.', 'Pharaonen aus Kusch', 'König Pije aus Kusch erobert Ägypten; seine Nachfolger regieren als 25. Dynastie, bis die Assyrer sie vertreiben.'),
    ('nubien', -664, '664 v. Chr.', 'Rückzug nach Napata', 'Die Könige von Kusch verlieren Ägypten und regieren weiter in Nubien; später wird Meroë ihr Zentrum.'),
    # --- Minoer und Mykener ---
    ('minoer', -1900, 'um 1900 v. Chr.', 'Erste Paläste auf Kreta', 'In Knossos, Phaistos und Malia entstehen große Palastanlagen als Zentren von Kult, Vorratshaltung und Verwaltung.'),
    ('minoer', -1700, 'um 1700 v. Chr.', 'Neubau der Paläste', 'Nach Zerstörungen werden die Paläste größer wieder aufgebaut; kretische Waren gelangen bis nach Ägypten.'),
    ('minoer', -1600, 'um 1600 oder um 1550 v. Chr.', 'Ausbruch des Thera-Vulkans', 'Der Vulkan auf Santorin begräbt die Stadt Akrotiri. Das Jahr ist umstritten: manche datieren ins späte 17. Jh. v. Chr., andere in die Mitte des 16. Jh.; die Forschung neigt derzeit eher zur späteren Datierung.', 'JAR 2023 (Bronzezeitliches Kreta), S. 13; Knapp/Manning, AJA 120 (2016)'),
    ('minoer', -1450, 'um 1500–1450 v. Chr.', 'Zerstörungen auf Kreta', 'Viele Paläste werden zerstört; nur Knossos bleibt. Dort herrscht nun eine Griechisch sprechende Elite, die mit Linear-B-Tafeln verwaltet.', 'JAR 2023 (Bronzezeitliches Kreta), S. 13'),
    ('minoer', -1350, 'spätes 14. Jh. v. Chr.', 'Ende des Palastes von Knossos', 'Der Palast von Knossos wird zerstört; Chania im Westen Kretas besteht wohl noch etwas länger.', 'JAR 2023 (Bronzezeitliches Kreta), S. 13'),
    ('mykener', -1600, 'um 1600 v. Chr.', 'Schachtgräber von Mykene', 'Reiche Fürstengräber mit Goldmasken zeigen den Aufstieg einer Kriegerelite auf dem griechischen Festland.'),
    ('mykener', -1400, 'um 1400 v. Chr.', 'Palastzeit', 'Paläste wie Mykene, Tiryns, Pylos und Theben verwalten ihr Umland mit Linear-B-Tafeln; Pylos teilt sein Reich in zwei Provinzen.', 'Bennet, Palaces and their Regions, PDF-S. 9'),
    ('mykener', -1250, 'um 1250 v. Chr.', 'Löwentor und Zyklopenmauern', 'Mykene und Tiryns werden mit gewaltigen Mauern befestigt.'),
    ('mykener', -1200, 'um 1200 v. Chr.', 'Zusammenbruch der Paläste', 'Die Paläste werden zerstört und nicht wieder aufgebaut. Als Ursachen werden Erdbeben, Dürre, innere Krisen und Angriffe diskutiert – meist im Zusammenspiel; umstritten.', 'Middleton, Durham-Diss. 2008, Bd. I, Abstract; Knapp/Manning, AJA 120 (2016)'),
    ('mykener', -1150, 'um 1150 v. Chr.', 'Nachpalastzeit', 'Kleinere Herrschaften bestehen weiter. Ob man die folgende Zeit „Dunkle Jahrhunderte“ oder „Frühe Eisenzeit“ nennt, ist in der Forschung umstritten.', 'Kotsonas, AJA 120 (2016)'),
    # --- Athen ---
    ('athen', -508, 'um 508 v. Chr.', 'Reformen des Kleisthenes', 'Kleisthenes ordnet die Bürgerschaft neu; Athen wird zur Demokratie.'),
    ('athen', -499, '499 v. Chr.', 'Ionischer Aufstand', 'Die Griechen Ioniens erheben sich gegen Persien. Athen schickt 20 Schiffe, Eretria fünf; 498 brennt Sardes.', 'Kagan, Yale CLCV 205, Handout „The Persian Wars“, S. 4'),
    ('athen', -490, '490 v. Chr.', 'Marathon', 'Die Athener und Plataier besiegen das persische Heer bei Marathon.', 'Kagan, Yale CLCV 205, Handout „The Persian Wars“'),
    ('athen', -480, '480 v. Chr.', 'Salamis', 'Die griechische Flotte siegt bei Salamis über die Flotte des Xerxes; Athen hat seine Flotte zuvor stark ausgebaut.', 'Kagan, Yale CLCV 205, Handout „The Athenian Empire“, S. 3'),
    ('athen', -478, '478/7 v. Chr.', 'Delisch-Attischer Seebund', 'Athen gründet mit Inselstädten und Küstenorten einen Bund gegen Persien. Die Kasse liegt im Apollon-Heiligtum auf Delos; der erste Tribut beträgt 460 Talente.', 'Kagan, Yale CLCV 205, Handout „The Athenian Empire“, S. 3'),
    ('athen', -470, 'um 470 v. Chr.', 'Naxos muss im Bund bleiben', 'Naxos will austreten und wird gezwungen zu bleiben – aus dem Bund wird nach und nach eine Herrschaft Athens.', 'Kagan, Yale CLCV 205, Handout „The Athenian Empire“, S. 4'),
    ('athen', -454, '454/3 v. Chr.', 'Bundeskasse nach Athen', 'Die Kasse des Seebunds wird von Delos nach Athen gebracht; mit Bundesgeldern baut Perikles später die Akropolis aus.', 'Kagan, Yale CLCV 205, Handout „The Athenian Empire“'),
    ('athen', -449, '449 v. Chr.', 'Kalliasfrieden', 'Nach antiken Berichten schließen Athen und Persien Frieden. Ob dieser Vertrag wirklich so geschlossen wurde, ist in der Forschung umstritten.', 'Kagan, Yale CLCV 205, Handout „The Athenian Empire“'),
    ('athen', -445, '445 v. Chr.', 'Dreißigjähriger Frieden', 'Athen und der Peloponnesische Bund erkennen ihre Machtbereiche gegenseitig an.', 'Kagan, Yale CLCV 205, Handout „The Athenian Empire“'),
    ('athen', -431, '431 v. Chr.', 'Peloponnesischer Krieg', 'Der Krieg zwischen Athen und Sparta mit ihren Bündnissen beginnt; Thukydides beschreibt ihn als Zeitzeuge.', 'Thukydides, Buch I–II'),
    ('athen', -415, '415–413 v. Chr.', 'Sizilische Expedition', 'Athens großer Feldzug gegen Syrakus endet mit der Vernichtung von Heer und Flotte.', 'Thukydides, Buch VI–VII'),
    ('athen', -404, '404 v. Chr.', 'Kapitulation Athens', 'Nach der Niederlage bei Aigospotamoi muss Athen kapitulieren; der Seebund ist aufgelöst.', 'Xenophon, Hellenika II'),
    ('athen', -378, '378/7 v. Chr.', 'Zweiter Attischer Seebund', 'Athen gründet einen neuen Bund. Das Dekret des Aristoteles verspricht den Mitgliedern Freiheit und Selbstverwaltung; ein Bundesrat (Synhedrion) tagt in Athen.', 'Marshall, The Second Athenian Confederacy (1905)'),
    ('athen', -357, '357–355 v. Chr.', 'Bundesgenossenkrieg', 'Wichtige Mitglieder fallen von Athen ab; nach dem Krieg ist der Bund nur noch klein.', 'Marshall, The Second Athenian Confederacy (1905), PDF-S. 131'),
    # --- Sparta ---
    ('sparta', -700, 'um 700 v. Chr.', 'Sparta beherrscht Messenien', 'Sparta unterwirft Messenien; die Bevölkerung muss als Heloten für die Spartaner arbeiten.'),
    ('sparta', -550, 'Mitte 6. Jh. v. Chr.', 'Peloponnesischer Bund', 'Sparta schließt Bündnisse mit den meisten Städten der Peloponnes; Argos bleibt außen vor. Erstmals erwähnt wird der Bund für 501 v. Chr.', 'Kagan, Yale CLCV 205, Handout „The Persian Wars“, S. 3'),
    ('sparta', -494, '494 v. Chr.', 'Sieg über Argos', 'Kleomenes besiegt Argos bei Sepeia; Spartas Führung im Bund wird gefestigt.', 'Kagan, Yale CLCV 205, Handout „The Persian Wars“, S. 5'),
    ('sparta', -480, '480 v. Chr.', 'Thermopylen', 'König Leonidas hält mit einem kleinen Heer den Engpass, bis die Perser ihn umgehen.', 'Kagan, Yale CLCV 205, Handout „The Athenian Empire“, S. 3'),
    ('sparta', -479, '479 v. Chr.', 'Plataiai', 'Unter Pausanias besiegen Spartaner, Athener und Verbündete das persische Landheer; die Perserkriege in Griechenland sind beendet.', 'Kagan, Yale CLCV 205, Handout „The Persian Wars“'),
    ('sparta', -464, '465/4 v. Chr.', 'Erdbeben und Helotenaufstand', 'Ein schweres Erdbeben trifft Sparta; danach erheben sich die Heloten in Messenien.', 'Kagan, Yale CLCV 205, Handout „The Athenian Empire“, S. 4'),
    ('sparta', -425, '425 v. Chr.', 'Niederlage auf Sphakteria', 'Athener schließen Spartaner auf der Insel Sphakteria bei Pylos ein; die Gefangennahme spartanischer Bürger ist ein Schock.', 'Thukydides, Buch IV'),
    ('sparta', -405, '405 v. Chr.', 'Sieg bei Aigospotamoi', 'Lysander vernichtet die athenische Flotte am Hellespont; Sparta wird Vormacht Griechenlands.', 'Xenophon, Hellenika II 1'),
    ('sparta', -387, '387/6 v. Chr.', 'Königsfrieden', 'Persien und Sparta setzen einen Frieden durch: Ionien wird persisch, Spartas Vormacht in Griechenland bestätigt.', 'Xenophon, Hellenika V'),
    ('sparta', -371, '371 v. Chr.', 'Niederlage bei Leuktra', 'Theben unter Epameinondas besiegt Sparta; bald darauf wird Messenien frei. Spartas Vormacht ist zu Ende.', 'Xenophon, Hellenika VI'),
    # --- Makedonien und Alexander ---
    ('makedonien', -359, '359 v. Chr.', 'Philipp II. wird König', 'Philipp II. baut ein schlagkräftiges Heer mit der langen Lanze (Sarissa) auf und macht Makedonien zur Großmacht.'),
    ('makedonien', -338, '338/7 v. Chr.', 'Chaironeia und Korinthischer Bund', 'Philipp besiegt Athen und Theben bei Chaironeia und vereint die griechischen Staaten (ohne Sparta) unter seiner Führung.'),
    ('makedonien', -336, '336 v. Chr.', 'Alexander wird König', 'Philipp wird ermordet; sein zwanzigjähriger Sohn Alexander folgt ihm.'),
    ('makedonien', -334, '334 v. Chr.', 'Aufbruch nach Asien, Sieg am Granikos', 'Alexander setzt über den Hellespont und schlägt die Perser am Fluss Granikos.', 'Arrian, Anabasis I'),
    ('makedonien', -333, '333 v. Chr.', 'Issos', 'Alexander besiegt den Perserkönig Dareios III. bei Issos; Dareios flieht.', 'Arrian, Anabasis II'),
    ('makedonien', -332, '332/1 v. Chr.', 'Tyros, Ägypten, Alexandria', 'Nach monatelanger Belagerung fällt Tyros; Ägypten ergibt sich. Alexander gründet Alexandria und besucht das Orakel des Amun in Siwa.', 'Arrian, Anabasis II–III'),
    ('makedonien', -331, '331 v. Chr.', 'Gaugamela', 'Entscheidender Sieg über Dareios III.; Babylon und Susa öffnen Alexander die Tore.', 'Arrian, Anabasis III'),
    ('makedonien', -330, '330 v. Chr.', 'Persepolis brennt, Ende der Achämeniden', 'Der Palast von Persepolis geht in Flammen auf; Dareios III. wird von eigenen Leuten getötet.', 'Arrian, Anabasis III'),
    ('makedonien', -327, '329–327 v. Chr.', 'Kämpfe in Baktrien und Sogdien', 'Jahre harter Kämpfe in Zentralasien; Alexander heiratet die baktrische Fürstentochter Roxane.', 'Arrian, Anabasis IV'),
    ('makedonien', -326, '326 v. Chr.', 'Hydaspes und Umkehr', 'Sieg über König Poros am Hydaspes. Am Hyphasis weigern sich die Soldaten weiterzuziehen.', 'Arrian, Anabasis V'),
    ('makedonien', -325, '325 v. Chr.', 'Marsch durch die Gedrosische Wüste', 'Auf dem Rückweg durch die Wüste sterben viele Soldaten; die Flotte unter Nearchos fährt an der Küste entlang.', 'Arrian, Anabasis VI'),
    ('makedonien', -323, '323 v. Chr.', 'Tod Alexanders in Babylon', 'Alexander stirbt mit 32 Jahren; seine Generäle (Diadochen) kämpfen um das Erbe.', 'Arrian, Anabasis VII'),
    ('makedonien', -301, '301 v. Chr.', 'Ipsos: Das Reich zerfällt endgültig', 'Nach der Schlacht bei Ipsos entstehen die großen hellenistischen Reiche: Ptolemäer in Ägypten, Seleukiden in Asien, Antigoniden in Makedonien.'),
    ('makedonien', -168, '168 v. Chr.', 'Pydna: Ende Makedoniens', 'Rom besiegt König Perseus; 148/146 v. Chr. wird Makedonien römische Provinz.'),
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
    dict(name='Megiddo', jahr=-1457, lng=35.18, lat=32.59, reiche=['aegypten'], note='Thutmosis III. besiegt eine Koalition kanaanäischer Fürsten (Jahr 23 seiner Regierung; nach anderer Chronologie 1482 v. Chr.). Die Annalen von Karnak beschreiben den Ablauf ausführlich (Nelson 1913).'),
    dict(name='Granikos', jahr=-334, lng=27.25, lat=40.20, reiche=['makedonien', 'perser'], note='Erster Sieg Alexanders über ein persisches Heer (Arrian, Anabasis I).'),
    dict(name='Issos', jahr=-333, lng=36.20, lat=36.84, reiche=['makedonien', 'perser'], note='Alexander besiegt Dareios III. (Arrian, Anabasis II).'),
    dict(name='Gaugamela', jahr=-331, lng=43.50, lat=36.57, reiche=['makedonien', 'perser'], note='Entscheidungsschlacht gegen Dareios III. (Arrian, Anabasis III).'),
    dict(name='Hydaspes', jahr=-326, lng=73.60, lat=32.95, reiche=['makedonien'], note='Sieg über den indischen König Poros mit Kriegselefanten (Arrian, Anabasis V).'),
    dict(name='Ipsos', jahr=-301, lng=31.05, lat=38.62, reiche=['makedonien'], note='Diadochen gegen Antigonos Monophthalmos; danach zerfällt das Alexanderreich endgültig.'),
    dict(name='Pydna', jahr=-168, lng=22.58, lat=40.37, reiche=['makedonien'], note='Rom besiegt Perseus von Makedonien.'),
    dict(name='Lade', jahr=-494, lng=27.27, lat=37.52, reiche=['perser'], note='Die persische Flotte besiegt die Ionier vor Milet; der Ionische Aufstand bricht zusammen (Kagan, Yale CLCV 205).'),
    dict(name='Marathon', jahr=-490, lng=23.97, lat=38.12, reiche=['athen', 'perser'], note='Athener und Plataier unter Miltiades besiegen das persische Landungsheer.'),
    dict(name='Thermopylen', jahr=-480, lng=22.54, lat=38.80, reiche=['sparta', 'perser'], note='Leonidas und seine Truppen werden nach drei Tagen umgangen und fallen.'),
    dict(name='Salamis', jahr=-480, lng=23.53, lat=37.95, reiche=['athen', 'sparta', 'perser'], note='Die griechische Flotte besiegt die persische in der Meerenge vor Salamis.'),
    dict(name='Plataiai', jahr=-479, lng=23.27, lat=38.21, reiche=['sparta', 'athen', 'perser'], note='Sieg der Griechen unter Pausanias über das Heer des Mardonios.'),
    dict(name='Mykale', jahr=-479, lng=27.15, lat=37.65, reiche=['sparta', 'athen', 'perser'], note='Griechischer Sieg an der kleinasiatischen Küste; Samos, Chios und Lesbos schließen sich den Griechen an.'),
    dict(name='Eurymedon', jahr=-469, lng=31.33, lat=36.83, reiche=['athen', 'perser'], note='Kimon besiegt mit der Flotte des Seebunds Perser zu Wasser und zu Land (Jahr unsicher, 469–466 v. Chr.).'),
    dict(name='Sphakteria', jahr=-425, lng=21.67, lat=36.93, reiche=['athen', 'sparta'], note='Athener nehmen spartanische Hopliten auf der Insel vor Pylos gefangen (Thukydides IV).'),
    dict(name='Syrakus', jahr=-413, lng=15.27, lat=37.07, reiche=['athen'], note='Untergang der athenischen Sizilien-Expedition (Thukydides VII).'),
    dict(name='Aigospotamoi', jahr=-405, lng=26.55, lat=40.33, reiche=['athen', 'sparta'], note='Lysander überrascht die athenische Flotte am Hellespont (Xenophon, Hellenika II 1).'),
    dict(name='Leuktra', jahr=-371, lng=23.18, lat=38.24, reiche=['sparta'], note='Theben unter Epameinondas besiegt Sparta.'),
    dict(name='Chaironeia', jahr=-338, lng=22.84, lat=38.50, reiche=['athen'], note='Philipp II. von Makedonien besiegt Athen und Theben; die Unabhängigkeit der Poleis endet.'),
    dict(name='Kadesch', jahr=-1274, lng=36.51, lat=34.56, reiche=['aegypten', 'hethiter'], note='Ramses II. gegen die Hethiter unter Muwattalli II.; keiner siegt eindeutig.'),
]
# Züge (wie die Völkerwanderung in data/reiche.json; gruppe = eigener Schalter im Menü). Wege schematisch.
ALEX = '#ffcc33'
ALEXANDERZUG = [
    (-334, -333, 'Pella – Hellespont – Granikos – Sardes – Gordion – Issos', [[22.52, 40.76], [23.85, 40.82], [26.40, 40.23], [27.25, 40.20], [28.04, 38.49], [27.28, 37.53], [27.42, 37.04], [30.5, 37.3], [31.99, 39.65], [33.5, 38.5], [34.90, 36.92], [36.20, 36.84]]),
    (-332, -331, 'Issos – Tyros – Gaza – Memphis – Alexandria – Siwa', [[36.20, 36.84], [35.80, 34.9], [35.20, 33.27], [34.45, 31.50], [32.57, 31.04], [31.25, 29.85], [29.92, 31.20], [27.25, 31.35], [25.54, 29.20]]),
    (-331, -330, 'Ägypten – Tyros – Gaugamela – Babylon – Susa – Persepolis', [[25.54, 29.20], [31.25, 29.85], [35.20, 33.27], [37.2, 35.5], [38.40, 35.95], [41.5, 36.6], [43.50, 36.57], [44.01, 36.19], [44.42, 32.54], [48.25, 32.19], [52.89, 29.93]]),
    (-330, -329, 'Persepolis – Ekbatana – Hekatompylos – Areia – Arachosien – Hindukusch', [[52.89, 29.93], [48.52, 34.80], [51.43, 35.59], [54.40, 36.10], [62.20, 34.35], [62.10, 32.37], [65.70, 31.60], [69.15, 35.00]]),
    (-329, -327, 'Baktra – Marakanda – Alexandria Eschate – Baktra', [[69.15, 35.00], [66.90, 36.76], [66.97, 39.65], [69.60, 40.28], [66.97, 39.65], [66.90, 36.76]]),
    (-327, -325, 'Baktra – Taxila – Hydaspes – Hyphasis – Indus abwärts bis Patala', [[66.90, 36.76], [69.15, 35.00], [72.83, 33.75], [73.60, 32.95], [75.00, 31.50], [73.60, 32.95], [71.47, 30.20], [68.40, 25.40]]),
    (-325, -324, 'Gedrosische Wüste – Karmanien – Persepolis – Susa', [[68.40, 25.40], [64.0, 25.6], [61.00, 27.20], [57.10, 29.10], [52.89, 29.93], [48.25, 32.19]]),
    (-324, -323, 'Susa – Opis – Ekbatana – Babylon (Tod im Juni 323)', [[48.25, 32.19], [44.50, 33.30], [48.52, 34.80], [44.42, 32.54]]),
]
WANDERUNGEN = [dict(volk='Alexander der Große', gruppe='alexander', farbe=ALEX, von=v, bis=b, pfad=pf, text='%s–%s v. Chr.: %s' % (-v, -b, t)) for v, b, t, pf in ALEXANDERZUG]
_kol = os.path.join(HERE, 'data', 'kolonisation.json')   # erzeugt von build_poleis.py
if os.path.exists(_kol): WANDERUNGEN += json.load(open(_kol, encoding='utf-8'))['zuege']

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
    ('aegypten', 'Kurgus (Grenzinschrift)', 33.50, 19.20, 3, [[-1500, -1070]]),
    # --- Nubien ---
    ('nubien', 'Kerma', 30.40, 19.60, 1, [[-2400, -1450]]),
    ('nubien', 'Napata (Gebel Barkal)', 31.83, 18.53, 1, [[-800, -300]]),
    ('nubien', 'Meroë', 33.75, 16.93, 2, [[-600, -300]]),
    # --- Minoer und Mykener ---
    ('minoer', 'Knossos', 25.16, 35.30, 1, [[-1900, -1300]]),
    ('minoer', 'Phaistos', 24.81, 35.05, 2, [[-1900, -1450]]),
    ('minoer', 'Malia', 25.49, 35.29, 2, [[-1900, -1450]]),
    ('minoer', 'Zakros', 26.26, 35.10, 3, [[-1600, -1450]]),
    ('minoer', 'Chania (Kydonia)', 24.02, 35.52, 3, [[-1700, -1300]]),
    ('minoer', 'Akrotiri (Thera)', 25.40, 36.35, 2, [[-1700, -1600]]),
    ('mykener', 'Mykene', 22.76, 37.73, 1, [[-1600, -1100]]),
    ('mykener', 'Tiryns', 22.80, 37.60, 2, [[-1400, -1100]]),
    ('mykener', 'Pylos (Palast des Nestor)', 21.70, 37.03, 2, [[-1400, -1200]]),
    ('mykener', 'Theben (Böotien)', 23.32, 38.32, 2, [[-1400, -1200]]),
    # --- Athen und Sparta ---
    ('athen', 'Athen', 23.73, 37.97, 1, [[-508, -338]]),
    ('makedonien', 'Pella', 22.52, 40.76, 1, [[-400, -168]]),
    ('makedonien', 'Alexandria (Ägypten)', 29.92, 31.20, 2, [[-331, -301]]),
    ('makedonien', 'Babylon (Residenz Alexanders)', 44.42, 32.54, 2, [[-331, -311]]),
    ('athen', 'Piräus', 23.64, 37.94, 3, [[-493, -338]]),
    ('athen', 'Delos (Bundeskasse)', 25.27, 37.40, 2, [[-478, -454]]),
    ('sparta', 'Sparta', 22.43, 37.08, 1, [[-700, -338]]),
    ('sparta', 'Korinth', 22.88, 37.91, 2, [[-550, -338]]),
    ('sparta', 'Tegea', 22.42, 37.45, 3, [[-550, -371]]),
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
        'ereignisse': [dict(reich=e[0], jahr=e[1], label=e[2], titel=e[3], note=e[4], **({'quelle': e[5]} if len(e) > 5 else {})) for e in EREIGNISSE],
        'schlachten': SCHLACHTEN,
        'orte': [dict(reich=r, name=n, lng=x, lat=y, stufe=s, zeiten=z) for r, n, x, y, s, z in ORTE],
        'wanderungen': WANDERUNGEN,
    }
    with io.open(ZIEL, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(daten, f, ensure_ascii=False, separators=(',', ':'))
    print('Frühe Hochkulturen:', len(REIHEN), 'Reiche,', len(regionen), 'Flächen,', len(ORTE), 'Orte ->', os.path.relpath(ZIEL, HERE), os.path.getsize(ZIEL), 'Bytes')


if __name__ == '__main__':
    main()
