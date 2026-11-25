# -*- coding: utf-8 -*-
"""Reiche und Übergänge 480–1453 für den freien Modus (data/mittelalter_reiche.json).

Ziel: Kein Reich „verschwindet“, nur weil die Daten enden. Nach 480 folgt Byzanz auf Ostrom, nach den Sasaniden das
Kalifat, nach der Han-Zeit die chinesischen Dynastien, nach den Franken Ost- und Westfranken usw.

Bewusst nur ANGEDEUTET wie build_fruehe_kulturen.py: grobe, von Hand gesetzte Umrisse (an die Küsten angepasst) und
gerundete Eckdaten der Handbuchliteratur. Grenzen im Mittelalter waren oft Zonen, keine Linien; Abhängigkeiten
(Tribut, Lehnshoheit) sind vereinfacht. Format wie data/reiche.json (meta, reihen, regionen, ereignisse, schlachten);
Byzanz ergänzt das Reich „rom“ (Ostrom, seite = 'o') ohne eigenes meta.

    python build_mittelalter.py
"""
import io, json, os
from shapely.geometry import MultiPolygon, Polygon, box, mapping, shape
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HERE, 'data', 'mittelalter_reiche.json')
P = lambda pts: Polygon(pts).buffer(0)   # buffer(0): gültige Fläche auch bei kleinen Zeichenfehlern

META = {
    'langob': dict(name='Langobardenreich', von=568, bis=774, farbe='#9c7b4e', kontext=True, kurz='Germanisches Königreich in Italien mit Hauptstadt Pavia; 774 von Karl dem Großen erobert.'),
    'kalifat': dict(name='Kalifat (Raschidun, Umayyaden, Abbasiden)', von=632, bis=1258, farbe='#2e8b57', kurz='Nach Mohammeds Tod 632 entsteht ein Reich vom Atlantik bis zum Indus; ab 750 regieren die Abbasiden von Bagdad aus, bis die Mongolen 1258 die Stadt zerstören.'),
    'andalus': dict(name='al-Andalus (muslimisches Spanien)', von=711, bis=1453, farbe='#3cb371', kurz='Muslimische Herrschaft auf der Iberischen Halbinsel: Emirat und Kalifat von Córdoba, Taifa-Reiche, Almoraviden, Almohaden, zuletzt Granada (bis 1492).'),
    'iberien': dict(name='Christliche Reiche Iberiens', von=718, bis=1453, farbe='#c0504d', kontext=True, kurz='Asturien, León, Kastilien, Navarra, Aragón und Portugal dehnen sich in der „Reconquista“ nach Süden aus.'),
    'china_ma': dict(name='China: Teilung, Sui, Tang, Song, Yuan', von=220, bis=1400, farbe='#e09e0c', kurz='Nach den Han: Drei Reiche, Jin, Nord- und Süddynastien; Wiedervereinigung unter Sui und Tang; Song; mongolische Yuan-Dynastie; ab 1368 Ming.'),
    'steppen': dict(name='Liao und Jin (Kitan und Jurchen)', von=907, bis=1234, farbe='#8b6fbf', kurz='Reiche von Steppen- und Waldvölkern im Norden Chinas; die Jin erobern 1127 Nordchina.'),
    'mongolen': dict(name='Mongolenreich und Khanate', von=1206, bis=1453, farbe='#7a5230', kurz='Dschingis Khan eint 1206 die Mongolen; sein Reich wird das größte zusammenhängende Landreich der Geschichte und zerfällt in Khanate.'),
    'seldsch': dict(name='Seldschuken', von=1037, bis=1308, farbe='#4f7cac', kurz='Türkische Dynastie: Große Seldschuken in Iran und Irak, Rum-Seldschuken in Anatolien nach dem Sieg bei Manzikert 1071.'),
    'aeg_ma': dict(name='Ägypten: Fatimiden, Ayyubiden, Mamluken', von=909, bis=1453, farbe='#d2a54a', kurz='Fatimiden-Kalifat (Kairo gegründet 969), Ayyubiden unter Saladin, ab 1250 Mamluken, die 1260 die Mongolen aufhalten.'),
    'hrr': dict(name='Ostfrankenreich und Heiliges Römisches Reich', von=843, bis=1453, farbe='#c9a227', kontext=True, kurz='Aus dem östlichen Teil des Frankenreichs entsteht das Reich der Ottonen, Salier und Staufer; 962 Kaiserkrönung Ottos I.'),
    'frankreich': dict(name='Westfrankenreich und Frankreich', von=843, bis=1453, farbe='#4169e1', kontext=True, kurz='Westlicher Teil des Frankenreichs; ab 987 Königtum der Kapetinger.'),
    'england': dict(name='Königreich England', von=927, bis=1453, farbe='#b22222', kontext=True, kurz='Aus den angelsächsischen Reichen entsteht England; 1066 erobern die Normannen das Land.'),
    'rus': dict(name='Kiewer Rus und russische Fürstentümer', von=882, bis=1453, farbe='#5f9ea0', kontext=True, kurz='Reich um Kiew und Nowgorod; 988 Taufe nach byzantinischem Ritus; ab 1240 unter der Oberhoheit der Goldenen Horde.'),
    'bulgarien': dict(name='Bulgarenreich', von=681, bis=1396, farbe='#6b8e23', kontext=True, kurz='Erstes Bulgarisches Reich bis 1018 (dann byzantinisch), Zweites Bulgarisches Reich 1185–1396.'),
    'ungarn': dict(name='Königreich Ungarn', von=1000, bis=1453, farbe='#8fbc8f', kontext=True, kurz='Um 1000 christliches Königreich unter Stephan I.'),
    'polen': dict(name='Polen', von=966, bis=1453, farbe='#dc6e6e', kontext=True, kurz='966 Taufe Mieszkos I.; ab 1386 in Union mit Litauen.'),
    'indien_ma': dict(name='Nordindien: Harsha und Sultanat Delhi', von=606, bis=1453, farbe='#b8860b', kurz='Reich des Harsha (606–647); ab 1206 Sultanat Delhi, unter den Tughluqs bis weit in den Süden.'),
}
REIHEN = ['china_ma', 'steppen', 'mongolen', 'kalifat', 'aeg_ma', 'seldsch', 'indien_ma', 'andalus', 'iberien', 'langob', 'frankreich', 'hrr', 'england', 'rus', 'bulgarien', 'ungarn', 'polen']

# ---------- Bausteine (grob) ----------
NIL = P([[29.6, 31.6], [32.3, 31.3], [31.5, 30.0], [31.3, 27.5], [33.0, 26.0], [33.0, 24.0], [32.6, 24.0], [32.2, 26.0], [30.6, 27.8], [30.4, 29.5], [29.6, 30.8]])
AFRIKA_N = P([[8.0, 37.3], [11.2, 37.2], [11.2, 32.8], [9.5, 33.0], [8.0, 34.8], [5.0, 36.0], [5.0, 36.9]])
MAGHREB = P([[-9.5, 35.8], [-1.0, 35.8], [11.0, 37.3], [20.0, 30.5], [25.0, 31.5], [29.5, 31.0], [29.0, 29.0], [25.0, 29.0], [-5.0, 29.0], [-9.8, 30.5]])
ITALIEN = P([[7.5, 46.0], [13.8, 46.6], [13.8, 45.5], [12.4, 44.2], [14.0, 42.0], [16.2, 41.7], [18.6, 40.1], [16.6, 38.4], [15.6, 37.9], [15.3, 40.0], [12.0, 41.8], [10.0, 44.0], [7.5, 43.8], [6.6, 45.0]])
SIZILIEN = P([[12.3, 38.2], [15.7, 38.3], [15.2, 36.6], [12.3, 37.5]])
ITALIEN_NORD = P([[6.6, 45.0], [7.5, 46.0], [13.8, 46.6], [13.5, 45.5], [12.4, 44.2], [13.5, 42.5], [11.5, 42.0], [10.0, 44.0], [7.5, 43.8]])
ITALIEN_REST = P([[12.0, 44.6], [12.6, 44.6], [13.5, 43.5], [14.5, 42.0], [16.0, 41.5], [18.6, 40.1], [16.6, 38.4], [15.6, 37.9], [15.3, 40.0], [13.8, 41.2], [12.3, 41.6], [12.0, 42.5]]).union(SIZILIEN)   # Ravenna, Rom, Süden, Sizilien
SUEDITALIEN = P([[15.0, 40.5], [16.6, 41.2], [18.6, 40.1], [16.6, 38.4], [15.6, 37.9]])
SPANIEN_SUED = P([[-6.5, 37.2], [-2.0, 38.0], [0.0, 38.5], [-0.5, 37.5], [-2.0, 36.7], [-5.6, 36.0]])
IBERIEN = P([[-9.6, 43.8], [3.4, 42.5], [3.4, 41.5], [0.5, 40.5], [0.0, 38.6], [-2.0, 36.6], [-5.6, 35.9], [-9.0, 37.0], [-9.6, 39.0]])
GRANADA = P([[-5.6, 36.0], [-1.6, 37.3], [-2.5, 37.8], [-4.5, 37.4], [-5.8, 36.6]])
ANATOLIEN = P([[26.0, 42.0], [29.0, 41.3], [36.0, 42.0], [41.5, 41.5], [41.0, 39.0], [38.5, 37.5], [36.2, 36.6], [30.0, 36.2], [27.2, 36.6], [26.0, 39.0]])
WEST_ANAT = P([[26.0, 42.0], [33.0, 41.8], [33.0, 37.0], [30.0, 36.2], [27.2, 36.6], [26.0, 39.0]])
NW_ANAT = P([[26.0, 42.0], [30.0, 41.3], [31.5, 40.6], [29.0, 39.9], [26.8, 40.2]])
BALKAN_KUESTE = P([[22.0, 40.2], [26.0, 42.0], [28.5, 41.5], [26.0, 40.0], [24.0, 38.0], [23.0, 36.4], [21.5, 36.7], [21.0, 38.5]])
BALKAN_SUED = P([[19.5, 41.5], [22.5, 42.3], [26.5, 42.2], [28.5, 41.5], [26.0, 40.0], [24.0, 38.0], [23.0, 36.4], [21.5, 36.7], [20.0, 39.0]])
BALKAN = P([[19.0, 42.0], [19.5, 44.8], [22.5, 44.6], [28.5, 45.2], [29.5, 44.8], [28.6, 42.5], [28.5, 41.5], [26.0, 40.0], [24.0, 38.0], [23.0, 36.4], [21.5, 36.7], [20.0, 39.0]])
BULGARIEN = P([[22.5, 44.2], [28.5, 44.2], [28.6, 42.5], [26.0, 41.6], [23.0, 41.5], [22.4, 42.5]])
ARMENIEN_W = P([[41.0, 41.5], [44.5, 41.3], [44.8, 39.0], [41.0, 38.5]])
ANTIOCHIA = P([[35.8, 37.0], [37.0, 37.0], [37.0, 35.6], [35.8, 35.6]])
TRAPEZUNT = P([[37.0, 41.3], [42.0, 41.7], [41.8, 40.5], [37.0, 40.6]])
EPIRUS = P([[19.3, 41.5], [21.5, 41.2], [22.4, 39.5], [21.0, 38.6], [20.0, 39.0]])
THRAKIEN = P([[23.0, 41.2], [28.8, 41.6], [29.2, 41.0], [26.3, 40.3], [23.5, 40.3]])
MOREA = P([[21.6, 37.9], [23.2, 37.9], [23.2, 36.4], [22.3, 36.4], [21.6, 36.9]])
ARABIEN = P([[35.0, 29.5], [39.0, 32.0], [47.5, 29.8], [56.0, 26.0], [59.8, 22.5], [52.0, 17.0], [43.0, 12.6], [38.5, 18.0], [34.8, 28.0]])
LEVANTE = P([[34.2, 31.3], [35.9, 36.8], [40.0, 37.0], [44.0, 37.3], [48.5, 30.0], [44.0, 31.0], [38.0, 30.0]])
IRAN = P([[44.0, 37.3], [48.0, 39.5], [54.0, 38.0], [61.0, 37.0], [62.5, 34.0], [61.5, 29.0], [57.5, 25.5], [52.0, 27.5], [48.5, 30.0]])
TRANSOX = P([[60.0, 40.5], [69.0, 42.5], [72.0, 40.0], [70.0, 37.0], [66.0, 36.0], [61.0, 35.0]])
SINDH = P([[66.5, 25.5], [71.5, 28.0], [71.5, 24.0], [68.0, 23.8]])
IRAK = P([[41.0, 37.0], [46.0, 35.5], [48.5, 30.0], [46.5, 29.5], [43.0, 31.0], [40.5, 34.0]])
CHINA = P([[98, 25], [100, 33], [104, 36], [110, 41], [118, 41.5], [122, 40], [122.5, 37], [121, 31.5], [122, 29], [119, 24], [117, 23.5], [113, 22], [109.5, 21.5], [106, 22], [101, 22]])
CHINA_N, CHINA_S = CHINA.intersection(box(90, 33, 130, 45)), CHINA.intersection(box(90, 15, 130, 33))
TARIM = P([[75, 40], [90, 44], [98, 42], [100, 36], [96, 36], [80, 36], [75, 38]])
MONGOLEI = P([[88, 49], [98, 52], [108, 52], [118, 50], [120, 46], [112, 42], [100, 42], [90, 44]])
OSTFRANKEN = P([[6.0, 53.5], [9.0, 55.0], [14.0, 54.0], [15.0, 51.0], [14.0, 48.5], [16.0, 48.0], [13.0, 46.6], [10.0, 47.3], [7.5, 47.5], [6.0, 49.5]])
BURGUND = P([[4.6, 46.5], [6.6, 47.5], [7.5, 46.3], [7.0, 44.0], [4.6, 43.4], [4.2, 45.0]])
BOEHMEN = P([[12.2, 50.3], [15.0, 51.0], [18.8, 49.5], [17.0, 48.6], [14.7, 48.6], [12.5, 49.3]])
WESTFRANKEN = P([[-4.8, 48.5], [-1.5, 49.7], [2.5, 51.1], [4.3, 49.5], [4.8, 47.0], [4.5, 45.0], [3.5, 43.3], [-1.8, 43.4], [-1.2, 46.2]])
ENGLAND = P([[-5.7, 50.0], [1.8, 51.3], [1.7, 52.8], [0.0, 53.5], [-1.5, 55.0], [-2.0, 55.8], [-3.5, 55.0], [-3.0, 53.3], [-4.7, 53.3], [-4.0, 51.5], [-5.5, 51.7]])
RUS = P([[24, 51], [28, 56], [30, 60], [38, 61], [44, 58], [42, 54], [36, 51], [32, 49.5], [27, 49]])
UNGARN = P([[16, 47.8], [17, 48.7], [19, 49.5], [22.5, 48.5], [26.5, 47.5], [25.5, 45.5], [22, 44.5], [19, 45], [16, 46.5]])
POLEN = P([[14.2, 53.9], [18.5, 54.8], [23, 54], [24, 52], [23, 50], [19, 49.4], [15, 50.8]])
GOLDENE_HORDE = P([[30, 52], [50, 56], [60, 55], [70, 52], [68, 45], [52, 41], [46, 43], [34, 45]])
ILCHANAT = P([[38.5, 38], [44, 41.5], [50, 40], [60, 39], [65, 37], [62, 30], [56, 26], [48.5, 30], [44, 31], [40, 35], [36.5, 37]])
TSCHAGATAI = P([[60, 45], [80, 45], [88, 43], [80, 36], [70, 35], [62, 37]])
NORDINDIEN = P([[68, 31], [77, 32], [85, 27], [88, 24], [82, 22], [74, 22], [68, 24]])

# Ostrom um 480 aus data/reiche.json (Reich „rom“, Seite Ost)
_r = json.load(open(os.path.join(HERE, 'data', 'reiche.json'), encoding='utf-8'))
OSTROM = unary_union([shape(f['geometry']).buffer(0) for f in _r['regionen'] if f['properties']['reich'] == 'rom' and f['properties'].get('seite') == 'o' and f['properties']['von'] <= 479 < f['properties']['bis']])

# (reich, name, von, bis, fläche)
REGIONEN = [
    # --- Byzanz (Reich „rom“, Ostrom) ---
    ('rom', 'Oströmisches Reich', 481, 533, OSTROM),
    ('rom', 'Byzanz: Rückeroberungen Justinians (Nordafrika, Italien)', 533, 554, OSTROM.union(AFRIKA_N).union(ITALIEN).union(SIZILIEN)),
    ('rom', 'Byzanz unter Justinian (größte Ausdehnung)', 554, 568, OSTROM.union(AFRIKA_N).union(ITALIEN).union(SIZILIEN).union(SPANIEN_SUED)),
    ('rom', 'Byzanz nach dem Einfall der Langobarden', 568, 636, OSTROM.union(AFRIKA_N).union(ITALIEN_REST).union(SPANIEN_SUED)),
    ('rom', 'Byzanz nach den arabischen Eroberungen', 636, 698, ANATOLIEN.union(BALKAN_KUESTE).union(AFRIKA_N).union(ITALIEN_REST)),
    ('rom', 'Byzanz: Kleinasien, Balkanküste, Süditalien', 698, 867, ANATOLIEN.union(BALKAN_KUESTE).union(ITALIEN_REST)),
    ('rom', 'Byzanz unter der Makedonischen Dynastie', 867, 1018, ANATOLIEN.union(BALKAN_SUED).union(SUEDITALIEN).union(ANTIOCHIA)),
    ('rom', 'Byzanz nach dem Sieg über Bulgarien (Basileios II.)', 1018, 1071, ANATOLIEN.union(BALKAN).union(SUEDITALIEN).union(ANTIOCHIA).union(ARMENIEN_W)),
    ('rom', 'Byzanz nach Manzikert (Kleinasien verloren)', 1071, 1097, BALKAN.union(NW_ANAT)),
    ('rom', 'Byzanz unter den Komnenen', 1097, 1185, BALKAN.union(WEST_ANAT)),
    ('rom', 'Byzanz nach dem Abfall Bulgariens', 1185, 1204, BALKAN_SUED.union(WEST_ANAT)),
    ('rom', 'Nachfolgestaaten: Kaiserreich Nikaia und Despotat Epirus', 1204, 1261, WEST_ANAT.difference(box(31, 30, 40, 45)).union(EPIRUS)),
    ('rom', 'Nachfolgestaat: Kaiserreich Trapezunt', 1204, 1400, TRAPEZUNT),
    ('rom', 'Byzanz nach der Rückeroberung Konstantinopels', 1261, 1300, THRAKIEN.union(BALKAN_SUED.intersection(box(21, 38, 30, 42.5))).union(NW_ANAT).union(MOREA)),
    ('rom', 'Byzanz: Thrakien, Thessaloniki, Morea', 1300, 1400, THRAKIEN.union(MOREA)),
    # --- Italien ---
    ('ostgot', 'Ostgotenreich in Italien', 493, 553, ITALIEN.union(SIZILIEN)),
    ('langob', 'Langobardenreich', 568, 774, ITALIEN_NORD.union(P([[12.3, 43.0], [14.5, 42.5], [15.5, 41.0], [14.8, 40.6], [13.2, 41.8]]))),
    # --- Kalifat ---
    ('kalifat', 'Arabien unter Mohammed und Abu Bakr', 632, 634, ARABIEN),
    ('kalifat', 'Kalifat der Raschidun: Syrien, Irak, Ägypten', 634, 651, ARABIEN.union(LEVANTE).union(NIL)),
    ('kalifat', 'Kalifat der Raschidun: bis Iran', 651, 661, ARABIEN.union(LEVANTE).union(NIL).union(IRAN)),
    ('kalifat', 'Kalifat der Umayyaden (Damaskus)', 661, 750, ARABIEN.union(LEVANTE).union(NIL).union(IRAN).union(MAGHREB).union(TRANSOX).union(SINDH)),
    ('kalifat', 'Kalifat der Abbasiden (Bagdad)', 750, 909, ARABIEN.union(LEVANTE).union(NIL).union(IRAN).union(MAGHREB.intersection(box(5, 20, 40, 40))).union(TRANSOX)),
    ('kalifat', 'Abbasiden: Macht bei Statthaltern und Emiren', 909, 1055, IRAK.union(IRAN).union(ARABIEN).union(LEVANTE.intersection(box(36, 30, 50, 40)))),
    ('kalifat', 'Abbasiden-Kalifat in Bagdad (unter seldschukischem Schutz)', 1055, 1258, IRAK),
    # --- Iberien ---
    ('andalus', 'al-Andalus (Provinz der Umayyaden)', 711, 756, IBERIEN.difference(P([[-9.6, 43.8], [-3.0, 43.6], [-3.5, 42.8], [-9.0, 42.5]]))),
    ('andalus', 'Emirat und Kalifat von Córdoba', 756, 1031, P([[-9.5, 41.2], [-2.0, 41.6], [0.5, 41.6], [0.3, 39.5], [-0.2, 38.0], [-2.0, 36.7], [-5.6, 36.0], [-9.0, 37.0]])),
    ('andalus', 'Taifa-Reiche, Almoraviden und Almohaden', 1031, 1212, P([[-9.5, 38.8], [-3.5, 39.8], [0.3, 39.5], [-0.2, 38.0], [-2.0, 36.7], [-5.6, 36.0], [-9.0, 37.0]])),
    ('andalus', 'Almohaden nach Las Navas de Tolosa', 1212, 1250, P([[-7.5, 38.0], [-3.0, 38.2], [-0.6, 37.6], [-2.0, 36.7], [-5.6, 36.0], [-7.5, 37.0]])),
    ('andalus', 'Emirat von Granada', 1250, 1453, GRANADA),
    ('iberien', 'Königreich Asturien', 718, 910, P([[-9.3, 43.2], [-4.5, 43.5], [-3.5, 43.0], [-6.5, 42.5], [-9.0, 42.5]])),
    ('iberien', 'León, Kastilien, Navarra, Grafschaft Barcelona', 910, 1085, P([[-9.3, 43.7], [3.3, 42.4], [2.0, 41.3], [0.0, 41.6], [-4.0, 41.4], [-8.7, 41.0]])),
    ('iberien', 'Christliche Reiche bis zum Tajo (Toledo 1085)', 1085, 1212, IBERIEN.difference(P([[-9.5, 38.8], [-3.5, 39.8], [0.3, 39.5], [-0.2, 38.0], [-2.0, 36.7], [-5.6, 36.0], [-9.0, 37.0]]))),
    ('iberien', 'Kastilien, Aragón und Portugal nach Las Navas de Tolosa', 1212, 1250, IBERIEN.difference(P([[-7.5, 38.0], [-3.0, 38.2], [-0.6, 37.6], [-2.0, 36.7], [-5.6, 36.0], [-7.5, 37.0]]))),
    ('iberien', 'Kastilien, Aragón, Navarra und Portugal', 1250, 1453, IBERIEN.difference(GRANADA)),
    # --- China ---
    ('china_ma', 'Drei Reiche: Wei', 220, 280, CHINA_N),
    ('china_ma', 'Drei Reiche: Shu', 221, 263, CHINA_S.intersection(box(90, 15, 108.5, 33))),
    ('china_ma', 'Drei Reiche: Wu', 222, 280, CHINA_S.intersection(box(108.5, 15, 130, 33))),
    ('china_ma', 'Westliche Jin (geeintes China)', 280, 317, CHINA),
    ('china_ma', 'Nördliche Dynastien (u. a. Nördliche Wei)', 317, 589, CHINA_N),
    ('china_ma', 'Südliche Dynastien (Östliche Jin, Song, Qi, Liang, Chen)', 317, 589, CHINA_S),
    ('china_ma', 'Sui-Dynastie', 589, 618, CHINA),
    ('china_ma', 'Tang-Dynastie (größte Ausdehnung bis Zentralasien)', 618, 755, CHINA.union(TARIM)),
    ('china_ma', 'Tang-Dynastie nach dem An-Lushan-Aufstand', 755, 907, CHINA),
    ('china_ma', 'Fünf Dynastien (Norden)', 907, 960, CHINA_N.difference(box(110, 39, 130, 45))),
    ('china_ma', 'Zehn Reiche (Süden)', 907, 960, CHINA_S),
    ('china_ma', 'Nördliche Song', 960, 1127, CHINA.difference(box(110, 39, 130, 45))),
    ('china_ma', 'Südliche Song', 1127, 1279, CHINA_S),
    ('china_ma', 'Yuan-Dynastie (Mongolen)', 1279, 1368, CHINA.union(TARIM.intersection(box(90, 30, 100, 45)))),
    ('china_ma', 'Ming-Dynastie', 1368, 1400, CHINA),
    ('steppen', 'Liao-Reich der Kitan', 907, 1125, P([[105, 40], [115, 48], [125, 50], [132, 48], [130, 42], [122, 39], [116, 39], [110, 41]])),
    ('steppen', 'Jin-Reich der Jurchen', 1125, 1234, P([[110, 41], [125, 50], [134, 47], [130, 42], [122, 39], [121, 33], [112, 32], [106, 34], [108, 38]])),
    # --- Mongolen ---
    ('mongolen', 'Reich Dschingis Khans', 1206, 1227, MONGOLEI.union(TARIM).union(TRANSOX)),
    ('mongolen', 'Mongolenreich (Großkhane)', 1227, 1259, MONGOLEI.union(TARIM).union(TRANSOX).union(IRAN).union(GOLDENE_HORDE).union(CHINA_N)),
    ('mongolen', 'Goldene Horde', 1259, 1453, GOLDENE_HORDE),
    ('mongolen', 'Ilchanat (Iran)', 1259, 1335, ILCHANAT),
    ('mongolen', 'Tschagatai-Khanat', 1259, 1453, TSCHAGATAI),
    ('mongolen', 'Mongolei (Großkhan, ab 1368 Nördliche Yuan)', 1259, 1453, MONGOLEI),
    # --- Seldschuken, Ägypten, Osmanen ---
    ('seldsch', 'Reich der Großseldschuken', 1037, 1071, IRAN.union(TRANSOX).union(IRAK)),
    ('seldsch', 'Großseldschuken und Rum-Seldschuken', 1071, 1194, IRAN.union(IRAK).union(LEVANTE.intersection(box(36, 33, 50, 40))).union(ANATOLIEN.difference(WEST_ANAT))),
    ('seldsch', 'Sultanat der Rum-Seldschuken (Anatolien)', 1194, 1308, ANATOLIEN.difference(WEST_ANAT).difference(TRAPEZUNT)),
    ('aeg_ma', 'Fatimiden in Nordafrika', 909, 969, AFRIKA_N.union(P([[11.2, 33.5], [20.0, 30.5], [20.0, 32.8], [11.2, 37.2]]))),
    ('aeg_ma', 'Fatimiden-Kalifat (Kairo)', 969, 1171, NIL.union(P([[34.2, 31.3], [35.6, 33.5], [36.5, 33.5], [35.3, 31.0]]))),
    ('aeg_ma', 'Ayyubiden (Saladin und Nachfolger)', 1171, 1250, NIL.union(P([[34.2, 31.3], [35.9, 36.5], [38.5, 36.0], [37.0, 32.0], [35.0, 29.5]]))),
    ('aeg_ma', 'Sultanat der Mamluken', 1250, 1453, NIL.union(P([[34.2, 31.3], [35.9, 36.8], [38.5, 36.5], [38.0, 32.0], [35.0, 28.0], [36.5, 25.0], [39.0, 21.5], [37.5, 21.0], [34.5, 27.5]]))),
    ('osman', 'Fürstentum Osmans (Bithynien)', 1299, 1326, P([[29.5, 40.6], [31.0, 40.5], [31.2, 39.7], [29.6, 39.6]])),
    ('osman', 'Osmanen: Bursa und Nordwest-Anatolien', 1326, 1362, P([[26.5, 40.6], [30.0, 41.2], [32.0, 40.5], [30.5, 39.3], [27.5, 39.5]])),
    ('osman', 'Osmanen auf dem Balkan und in Anatolien', 1362, 1400, P([[21.0, 42.5], [27.5, 43.5], [29.0, 41.3], [33.5, 41.5], [35.5, 39.0], [30.0, 37.5], [27.0, 38.5], [26.0, 40.2], [23.0, 40.0], [20.5, 41.0]]).difference(THRAKIEN.intersection(box(28, 40.5, 30, 42)))),
    # --- Europa ---
    ('frankreich', 'Westfrankenreich', 843, 987, WESTFRANKEN),
    ('frankreich', 'Königreich Frankreich (Kapetinger)', 987, 1453, WESTFRANKEN),
    ('hrr', 'Ostfrankenreich', 843, 962, OSTFRANKEN),
    ('hrr', 'Heiliges Römisches Reich (mit Reichsitalien und Burgund)', 962, 1250, OSTFRANKEN.union(ITALIEN_NORD).union(BOEHMEN).union(BURGUND)),
    ('hrr', 'Heiliges Römisches Reich', 1250, 1453, OSTFRANKEN.union(BOEHMEN)),
    ('england', 'Königreich England', 927, 1453, ENGLAND),
    ('rus', 'Kiewer Rus', 882, 1240, RUS),
    ('rus', 'Russische Fürstentümer unter der Goldenen Horde', 1240, 1453, RUS),
    ('bulgarien', 'Erstes Bulgarisches Reich', 681, 1018, BULGARIEN),
    ('bulgarien', 'Zweites Bulgarisches Reich', 1185, 1396, BULGARIEN),
    ('ungarn', 'Königreich Ungarn', 1000, 1453, UNGARN),
    ('polen', 'Polen', 966, 1453, POLEN),
    ('indien_ma', 'Reich des Harsha', 606, 647, P([[73, 31], [80, 30], [88, 26], [86, 23], [80, 23], [74, 25]])),
    ('indien_ma', 'Sultanat Delhi', 1206, 1320, NORDINDIEN),
    ('indien_ma', 'Sultanat Delhi unter den Tughluqs', 1320, 1398, NORDINDIEN.union(P([[74, 22], [84, 22], [84, 18], [80, 12], [77, 12], [73, 17], [72, 21]]))),
    ('indien_ma', 'Sultanat Delhi nach dem Einfall Timurs', 1398, 1453, NORDINDIEN.intersection(box(70, 25, 82, 32))),
]
EREIGNISSE = [
    ('rom', 527, '527', 'Justinian wird Kaiser', 'Justinian will das Römische Reich wiederherstellen und lässt das römische Recht sammeln (Corpus iuris civilis).'),
    ('rom', 533, '533–554', 'Rückeroberungen im Westen', 'Byzantinische Heere erobern Nordafrika von den Vandalen und Italien von den Ostgoten zurück.'),
    ('rom', 537, '537', 'Hagia Sophia', 'In Konstantinopel wird die riesige Kuppelkirche Hagia Sophia geweiht.'),
    ('rom', 568, '568', 'Langobarden in Italien', 'Die Langobarden erobern große Teile Italiens; Byzanz behält Ravenna, Rom und den Süden.'),
    ('rom', 636, '636', 'Niederlage am Jarmuk', 'Arabische Heere besiegen Byzanz; Syrien, Palästina und bald Ägypten gehen verloren.'),
    ('rom', 717, '717/18', 'Konstantinopel hält stand', 'Eine große arabische Belagerung scheitert – auch dank des „Griechischen Feuers“.'),
    ('rom', 726, '726–843', 'Bilderstreit', 'Kaiser und Kirche streiten, ob Bilder von Christus und Heiligen verehrt werden dürfen.'),
    ('rom', 867, '867', 'Makedonische Dynastie', 'Unter Basileios I. und seinen Nachfolgern erlebt Byzanz eine neue Blüte.'),
    ('rom', 1018, '1018', 'Bulgarien wird byzantinisch', 'Basileios II. („Bulgarentöter“) unterwirft das Bulgarenreich.'),
    ('rom', 1054, '1054', 'Morgenländisches Schisma', 'Die Kirchen von Rom und Konstantinopel trennen sich – katholisch und orthodox.'),
    ('rom', 1071, '1071', 'Manzikert', 'Die Seldschuken besiegen Byzanz; der größte Teil Kleinasiens geht verloren.'),
    ('rom', 1096, '1096', 'Erster Kreuzzug', 'Byzanz ruft um Hilfe; Kreuzfahrerheere ziehen über Konstantinopel nach Jerusalem.'),
    ('rom', 1204, '1204', 'Plünderung Konstantinopels', 'Der Vierte Kreuzzug erobert und plündert Konstantinopel. Griechische Nachfolgestaaten entstehen in Nikaia, Epirus und Trapezunt.'),
    ('rom', 1261, '1261', 'Rückeroberung Konstantinopels', 'Michael VIII. Palaiologos erobert die Hauptstadt zurück; das Reich bleibt aber klein.'),
    ('rom', 1354, '1354', 'Osmanen in Europa', 'Die Osmanen setzen bei Gallipoli nach Europa über; Byzanz schrumpft auf wenige Gebiete.'),
    ('ostgot', 493, '493', 'Theoderich in Italien', 'Der Ostgotenkönig Theoderich herrscht von Ravenna aus über Italien.'),
    ('ostgot', 535, '535–553', 'Gotenkrieg', 'Byzanz erobert Italien in einem langen, verheerenden Krieg zurück.'),
    ('langob', 568, '568', 'Langobarden ziehen nach Italien', 'Unter König Alboin erobern die Langobarden Norditalien.'),
    ('langob', 774, '774', 'Karl der Große erobert Pavia', 'Das Langobardenreich wird Teil des Frankenreichs.'),
    ('kalifat', 632, '632', 'Tod Mohammeds', 'Nach dem Tod des Propheten führen Kalifen („Nachfolger“) die Gemeinschaft der Muslime.'),
    ('kalifat', 636, '636–651', 'Arabische Eroberungen', 'Siege am Jarmuk und bei Kadesia: Syrien, Irak, Ägypten und das Sasanidenreich werden erobert.'),
    ('kalifat', 661, '661', 'Umayyaden in Damaskus', 'Die Umayyaden machen das Kalifat erblich; es reicht bald vom Atlantik bis zum Indus.'),
    ('kalifat', 750, '750', 'Abbasiden', 'Die Abbasiden stürzen die Umayyaden; 762 gründen sie Bagdad.'),
    ('kalifat', 830, 'um 830', 'Haus der Weisheit', 'In Bagdad werden griechische, persische und indische Schriften übersetzt und weiterentwickelt.'),
    ('kalifat', 1258, '1258', 'Mongolen zerstören Bagdad', 'Hülegü erobert Bagdad; der letzte Abbasiden-Kalif wird getötet.'),
    ('andalus', 711, '711', 'Eroberung Spaniens', 'Arabische und berberische Truppen besiegen das Westgotenreich.'),
    ('andalus', 929, '929', 'Kalifat von Córdoba', 'Abd ar-Rahman III. nennt sich Kalif; Córdoba ist eine der größten Städte Europas.'),
    ('andalus', 1031, '1031', 'Taifa-Reiche', 'Das Kalifat zerfällt in viele kleine Reiche.'),
    ('andalus', 1238, '1238', 'Emirat von Granada', 'Die Nasriden gründen das letzte muslimische Reich in Spanien; die Alhambra entsteht.'),
    ('iberien', 722, 'um 722', 'Covadonga', 'Ein kleines christliches Reich in Asturien behauptet sich.'),
    ('iberien', 1085, '1085', 'Toledo erobert', 'Alfons VI. von Kastilien erobert die alte Westgoten-Hauptstadt Toledo.'),
    ('iberien', 1212, '1212', 'Las Navas de Tolosa', 'Ein Bündnis christlicher Könige besiegt die Almohaden.'),
    ('china_ma', 220, '220', 'Ende der Han, Drei Reiche', 'Das Han-Reich zerfällt in die drei Reiche Wei, Shu und Wu.'),
    ('china_ma', 280, '280', 'Westliche Jin', 'Die Jin einen China für kurze Zeit wieder.'),
    ('china_ma', 317, '317–589', 'Nord- und Süddynastien', 'China ist geteilt; der Buddhismus breitet sich stark aus.'),
    ('china_ma', 589, '589', 'Sui eint China', 'Die Sui-Dynastie eint das Land und beginnt den Kaiserkanal.'),
    ('china_ma', 618, '618', 'Tang-Dynastie', 'Die Tang regieren ein weltoffenes Reich mit der Hauptstadt Chang’an.'),
    ('china_ma', 755, '755–763', 'Aufstand des An Lushan', 'Ein verheerender Aufstand schwächt das Tang-Reich dauerhaft.'),
    ('china_ma', 960, '960', 'Song-Dynastie', 'Unter den Song blühen Städte, Handel, Buchdruck und Papiergeld.'),
    ('china_ma', 1127, '1127', 'Südliche Song', 'Die Jurchen erobern Nordchina; die Song regieren nun von Hangzhou aus.'),
    ('china_ma', 1279, '1279', 'Yuan-Dynastie', 'Kublai Khan vollendet die Eroberung Chinas; Marco Polo berichtet später von seinem Hof.'),
    ('china_ma', 1368, '1368', 'Ming-Dynastie', 'Zhu Yuanzhang vertreibt die Mongolen und gründet die Ming-Dynastie.'),
    ('steppen', 907, '907/916', 'Liao-Reich', 'Die Kitan gründen im Norden ein Reich; vom Namen „Kitai“ leitet sich das russische Wort für China ab.'),
    ('steppen', 1125, '1125', 'Jin-Reich', 'Die Jurchen besiegen die Liao und erobern 1127 Nordchina.'),
    ('mongolen', 1206, '1206', 'Dschingis Khan', 'Temüdschin wird als Dschingis Khan zum Herrscher aller Mongolen ausgerufen.'),
    ('mongolen', 1241, '1241', 'Mongolen in Europa', 'Mongolische Heere siegen bei Liegnitz und Mohi; danach ziehen sie sich zurück.'),
    ('mongolen', 1260, '1260', 'Ain Dschalut', 'Die Mamluken stoppen den Vormarsch der Mongolen in Palästina.'),
    ('mongolen', 1370, '1370', 'Timur', 'Timur (Tamerlan) baut von Samarkand aus ein neues Reich auf.'),
    ('seldsch', 1037, '1037', 'Seldschuken', 'Türkische Krieger unter den Seldschuken erobern Iran; 1055 ziehen sie in Bagdad ein.'),
    ('seldsch', 1071, '1071', 'Sieg bei Manzikert', 'Sultan Alp Arslan besiegt Byzanz; türkische Gruppen besiedeln Anatolien.'),
    ('aeg_ma', 969, '969', 'Kairo gegründet', 'Die Fatimiden erobern Ägypten und gründen Kairo.'),
    ('aeg_ma', 1187, '1187', 'Saladin erobert Jerusalem', 'Nach dem Sieg bei Hattin nimmt Saladin Jerusalem ein.'),
    ('aeg_ma', 1250, '1250', 'Mamluken', 'Militärsklaven (Mamluken) übernehmen die Macht in Ägypten.'),
    ('osman', 1299, 'um 1299', 'Osman I.', 'Osman gründet in Bithynien ein kleines Fürstentum.'),
    ('osman', 1326, '1326', 'Bursa', 'Die Osmanen erobern Bursa und machen es zur Hauptstadt.'),
    ('osman', 1389, '1389', 'Schlacht auf dem Amselfeld', 'Die Osmanen siegen über ein serbisches Heer.'),
    ('frankreich', 843, '843', 'Vertrag von Verdun', 'Das Frankenreich wird unter den Enkeln Karls des Großen geteilt.'),
    ('frankreich', 987, '987', 'Kapetinger', 'Hugo Capet wird König; seine Familie regiert Frankreich jahrhundertelang.'),
    ('frankreich', 1337, '1337–1453', 'Hundertjähriger Krieg', 'England und Frankreich kämpfen um die französische Krone.'),
    ('hrr', 843, '843', 'Ostfrankenreich', 'Ludwig der Deutsche erhält den östlichen Teil des Frankenreichs.'),
    ('hrr', 955, '955', 'Lechfeld', 'Otto I. besiegt die Ungarn bei Augsburg.'),
    ('hrr', 962, '962', 'Kaiserkrönung Ottos I.', 'Otto I. wird in Rom zum Kaiser gekrönt.'),
    ('hrr', 1077, '1077', 'Gang nach Canossa', 'Im Investiturstreit beugt sich Heinrich IV. vor Papst Gregor VII.'),
    ('hrr', 1356, '1356', 'Goldene Bulle', 'Sieben Kurfürsten wählen künftig den König.'),
    ('england', 927, '927', 'Königreich England', 'Æthelstan herrscht über ganz England.'),
    ('england', 1066, '1066', 'Normannische Eroberung', 'Wilhelm der Eroberer siegt bei Hastings.'),
    ('england', 1215, '1215', 'Magna Carta', 'Der König muss die Rechte der Barone schriftlich anerkennen.'),
    ('rus', 882, '882', 'Kiewer Rus', 'Oleg macht Kiew zum Zentrum eines Reiches.'),
    ('rus', 988, '988', 'Taufe der Rus', 'Großfürst Wladimir lässt sich nach byzantinischem Ritus taufen.'),
    ('rus', 1240, '1240', 'Mongolen erobern Kiew', 'Die Rus-Fürstentümer werden von der Goldenen Horde abhängig.'),
    ('bulgarien', 681, '681', 'Bulgarenreich', 'Byzanz erkennt das Reich der Bulgaren an der unteren Donau an.'),
    ('bulgarien', 1185, '1185', 'Zweites Bulgarisches Reich', 'Ein Aufstand gegen Byzanz begründet ein neues Bulgarenreich.'),
    ('ungarn', 1000, '1000', 'Stephan I.', 'Stephan wird erster König Ungarns.'),
    ('polen', 966, '966', 'Taufe Mieszkos I.', 'Polen wird christlich.'),
    ('polen', 1386, '1386', 'Polen-Litauen', 'Durch die Heirat Jadwigas mit Jogaila entsteht eine Union mit Litauen.'),
    ('indien_ma', 606, '606', 'Harsha', 'König Harsha eint große Teile Nordindiens.'),
    ('indien_ma', 1206, '1206', 'Sultanat Delhi', 'Türkische Heerführer gründen das Sultanat Delhi.'),
    ('indien_ma', 1398, '1398', 'Timur plündert Delhi', 'Das Sultanat verliert danach viel von seiner Macht.'),
]
SCHLACHTEN = [
    dict(name='Jarmuk', jahr=636, lng=35.95, lat=32.80, reiche=['rom', 'kalifat'], note='Arabische Heere besiegen Byzanz.'),
    dict(name='Tours und Poitiers', jahr=732, lng=0.45, lat=46.80, reiche=['andalus'], note='Karl Martell schlägt ein Heer aus al-Andalus zurück.'),
    dict(name='Talas', jahr=751, lng=72.0, lat=42.5, reiche=['kalifat', 'china_ma'], note='Abbasiden besiegen ein Tang-Heer in Zentralasien.'),
    dict(name='Lechfeld', jahr=955, lng=10.90, lat=48.30, reiche=['hrr', 'ungarn'], note='Otto I. besiegt die Ungarn.'),
    dict(name='Hastings', jahr=1066, lng=0.49, lat=50.91, reiche=['england'], note='Wilhelm der Eroberer besiegt König Harald.'),
    dict(name='Manzikert', jahr=1071, lng=42.53, lat=39.14, reiche=['rom', 'seldsch'], note='Die Seldschuken besiegen Kaiser Romanos IV.'),
    dict(name='Hattin', jahr=1187, lng=35.45, lat=32.80, reiche=['aeg_ma'], note='Saladin besiegt das Heer des Königreichs Jerusalem.'),
    dict(name='Las Navas de Tolosa', jahr=1212, lng=-3.58, lat=38.28, reiche=['iberien', 'andalus'], note='Christliche Könige besiegen die Almohaden.'),
    dict(name='Ain Dschalut', jahr=1260, lng=35.35, lat=32.55, reiche=['aeg_ma', 'mongolen'], note='Die Mamluken besiegen die Mongolen.'),
    dict(name='Amselfeld (Kosovo)', jahr=1389, lng=21.10, lat=42.70, reiche=['osman'], note='Osmanischer Sieg über ein serbisches Heer.'),
]


def main():
    land = shape(json.load(open(os.path.join(HERE, 'data', 'land.json'), encoding='utf-8'))['geometry']).buffer(0)
    regionen = []
    for i, (r, name, von, bis, g) in enumerate(REGIONEN):
        g = g.buffer(0).intersection(land.buffer(0.08)).simplify(0.04, preserve_topology=True)
        if g.is_empty: raise SystemExit('leer: ' + name)
        teile = [orient(q, sign=-1.0) for q in (g.geoms if hasattr(g, 'geoms') else [g]) if q.geom_type == 'Polygon' and q.area > 0.01]
        g = teile[0] if len(teile) == 1 else MultiPolygon(teile)
        p = {'id': 3001 + i, 'reich': r, 'name': name, 'von': von, 'bis': bis, 'art': 'kern', 'angedeutet': True}
        if r == 'rom': p['seite'] = 'o'
        regionen.append({'type': 'Feature', 'properties': p, 'geometry': json.loads(json.dumps(mapping(g)))})

    def runden(o):
        if isinstance(o, float): return round(o, 3)
        if isinstance(o, (list, tuple)): return [runden(x) for x in o]
        if isinstance(o, dict): return {k: runden(v) for k, v in o.items()}
        return o
    daten = {
        '_hinweis': 'Reiche und Übergänge 480–1453, nur angedeutet (grobe Umrisse, gerundete Jahreszahlen). Erzeugt mit build_mittelalter.py. '
                    'Format wie data/reiche.json; nur im freien Modus (Tafelbilder blenden diese Reiche aus, außer sie nennen sie).',
        'abschnitt': 'mittelalter',
        'meta': META, 'reihen': REIHEN,
        'regionen': runden(regionen),
        'ereignisse': [dict(reich=r, jahr=j, label=l, titel=t, note=n) for r, j, l, t, n in EREIGNISSE],
        'schlachten': SCHLACHTEN, 'orte': [],
    }
    with io.open(ZIEL, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(daten, f, ensure_ascii=False, separators=(',', ':'))
    print('Mittelalter:', len(META), 'neue Reiche,', len(regionen), 'Flächen,', len(EREIGNISSE), 'Ereignisse ->', os.path.relpath(ZIEL, HERE), os.path.getsize(ZIEL), 'Bytes')


if __name__ == '__main__':
    main()
