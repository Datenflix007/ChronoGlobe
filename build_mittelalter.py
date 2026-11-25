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
    'langob': dict(name='Langobardenreich (ab 774 Fürstentum Benevent)', von=568, bis=1077, farbe='#9c7b4e', kontext=True, kurz='Germanisches Königreich in Italien mit Hauptstadt Pavia; 774 von Karl dem Großen erobert. Im Süden besteht das langobardische Fürstentum Benevent bis 1077.'),
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
    'lothar': dict(name='Lotharingien, Burgund und Arelat', von=843, bis=1032, farbe='#9a7fb5', kontext=True, kurz='Mittelreich Lothars I. nach dem Vertrag von Verdun 843: Lotharingien fällt 870/880 an das Ostfrankenreich, Burgund und die Provence bilden ab 933 das Königreich Arelat, das 1032/33 an das Reich kommt.'),
    'italien_ma': dict(name='Regnum Italiae (Königreich Italien)', von=843, bis=962, farbe='#7fa36b', kontext=True, kurz='Ober- und Mittelitalien nach dem Vertrag von Verdun; ab 888 eigene Könige, 951/962 an Otto I. (Reichsitalien).'),
    'kirchenstaat': dict(name='Kirchenstaat', von=756, bis=1453, farbe='#a05a7a', kontext=True, kurz='Herrschaft der Päpste in Mittelitalien seit der Pippinschen Schenkung (754/756); die Rechte über Romagna und Marken waren lange nur nominell.'),
    'sizilien_ma': dict(name='Sizilien und Süditalien', von=902, bis=1453, farbe='#5f8f8a', kontext=True, kurz='Emirat Sizilien, ab 1061 normannische Eroberung, 1130 Königreich Sizilien (Normannen, Staufer, Anjou); nach der Sizilianischen Vesper 1282 getrennt in Neapel und Sizilien.'),
    'serbien': dict(name='Serbien', von=1166, bis=1453, farbe='#a0522d', kontext=True, kurz='Unter den Nemanjiden vom Fürstentum Raška zum Königreich (1217) und unter Stefan Dušan zum Zarenreich (1346); nach 1371 Despotat, 1459 osmanisch.'),
    'litauen': dict(name='Großfürstentum Litauen', von=1240, bis=1453, farbe='#c78c3c', kontext=True, kurz='Um 1240 geeint (Mindaugas, 1253 gekrönt); unter Gediminas und Algirdas Ausdehnung über weite Teile der früheren Rus; seit 1386 in Union mit Polen.'),
    'orden': dict(name='Deutscher Orden (Preußen und Livland)', von=1230, bis=1453, farbe='#5d6470', kontext=True, kurz='Geistlicher Ritterorden; ab 1230 Eroberung Preußens, 1237 Vereinigung mit dem Schwertbrüderorden in Livland; 1410 Niederlage bei Tannenberg.'),
    'awaren': dict(name='Awaren', von=568, bis=796, farbe='#a98c5a', kontext=True, kurz='Reiternomaden; ihr Khaganat beherrscht ab 568 das Karpatenbecken und bedroht Byzanz (626 Belagerung Konstantinopels); 791–796 von Karl dem Großen zerschlagen.'),
    'indien_ma': dict(name='Nordindien: Harsha und Sultanat Delhi', von=606, bis=1453, farbe='#b8860b', kurz='Reich des Harsha (606–647); ab 1206 Sultanat Delhi, unter den Tughluqs bis weit in den Süden.'),
}
REIHEN = ['china_ma', 'steppen', 'mongolen', 'kalifat', 'aeg_ma', 'seldsch', 'indien_ma', 'andalus', 'iberien', 'langob', 'awaren', 'frankreich', 'hrr', 'lothar', 'italien_ma', 'kirchenstaat', 'sizilien_ma', 'england', 'rus', 'litauen', 'orden', 'bulgarien', 'serbien', 'ungarn', 'polen']

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
ENGLAND = P([[-5.7, 50.0], [1.8, 51.3], [1.7, 52.8], [0.0, 53.5], [-1.5, 55.0], [-2.0, 55.8], [-3.5, 55.0], [-3.0, 53.3], [-4.7, 53.3], [-4.0, 51.5], [-5.5, 51.7]])
# ---------- Mitteleuropa: Umrisse entlang Flüssen und Gebirgen ----------
# Küstenseiten dürfen grob ins Meer reichen (es wird an data/land.json beschnitten); Binnengrenzen folgen den Linien,
# die die Handbücher nennen: Vertrag von Verdun 843 (Schelde, Maas, Saône, Rhône), Elbe und Saale, Enns, Alpenhauptkamm,
# Pyrenäen, Karpatenbogen, Erzgebirge, Sudeten und Böhmerwald. build_grenzen.py legt grenznahe Abschnitte zusätzlich genau
# auf Flüsse und Gebirgskämme.
VERDUN = [(3.4, 51.45), (3.7, 51.05), (3.45, 50.6), (3.25, 50.2), (4.0, 49.95), (4.8, 49.75), (5.0, 49.3), (5.1, 48.8), (5.3, 48.3), (5.4, 47.9),
          (5.5, 47.5), (5.1, 47.1), (4.85, 46.78), (4.83, 46.31), (4.82, 45.9), (4.85, 45.5), (4.85, 44.95), (4.75, 44.4), (4.65, 43.95), (4.62, 43.68), (4.75, 43.3)]
PYRENAEEN = [(3.15, 42.45), (2.0, 42.45), (0.7, 42.7), (-0.6, 42.8), (-1.5, 43.1), (-1.85, 43.4)]
WESTFRANKEN = P([(-5.5, 48.6), (-4.5, 49.2), (-1.9, 49.8), (0.2, 49.95), (1.4, 50.4), (1.6, 51.2), (2.6, 51.3)] + VERDUN + [(3.6, 43.1)] + PYRENAEEN
                + [(-2.2, 43.6), (-1.6, 45.5), (-2.0, 46.8), (-3.0, 47.3), (-5.0, 47.6)])
MARCA = P([(3.2, 42.45), (3.4, 41.9), (2.2, 41.3), (1.6, 41.2), (1.0, 41.6), (0.7, 42.3), (1.5, 42.5), (2.0, 42.45)])   # Spanische Mark (Barcelona 801)
LYONNAIS = P([(4.82, 45.9), (5.2, 45.95), (5.3, 45.6), (4.85, 45.5)])
OSTFRANKEN_843 = P([(6.9, 53.35), (8.5, 54.4), (9.6, 54.4), (10.2, 54.3), (10.7, 53.9), (10.8, 53.4), (11.3, 53.1), (11.8, 52.7), (11.9, 52.1),
                    (11.95, 51.5), (11.7, 50.9), (11.9, 50.3), (12.1, 50.3), (12.6, 49.7), (13.4, 49.1), (13.8, 48.75), (14.5, 48.6), (15.2, 48.5),
                    (16.1, 48.3), (15.8, 47.7), (15.6, 47.0), (15.8, 46.6), (14.6, 46.45), (13.7, 46.5), (12.9, 46.6), (12.2, 47.05), (11.5, 47.0),
                    (10.5, 46.85), (9.9, 46.4), (9.5, 46.5), (8.5, 46.5), (7.9, 46.7), (7.4, 47.2), (7.6, 47.55), (7.55, 48.1), (7.8, 48.6),
                    (8.1, 49.0), (7.9, 49.3), (8.1, 49.6), (7.8, 49.95), (7.6, 50.35), (6.96, 50.94), (6.7, 51.5), (6.2, 51.85), (6.9, 52.3), (7.1, 52.8)])
LOTHARINGIEN = P([(3.4, 51.45), (4.1, 52.0), (5.0, 52.9), (6.9, 53.35), (7.1, 52.8), (6.9, 52.3), (6.2, 51.85), (6.7, 51.5), (6.96, 50.94), (7.6, 50.35),
                  (7.8, 49.95), (8.1, 49.6), (7.9, 49.3), (8.1, 49.0), (7.8, 48.6), (7.55, 48.1), (7.6, 47.55), (6.9, 47.45), (6.0, 47.75)]
                 + list(reversed(VERDUN[:10])))
ARELAT = P([(5.4, 47.9), (6.0, 47.75), (6.9, 47.45), (7.6, 47.55), (7.4, 47.2), (7.9, 46.7), (7.9, 46.0), (6.85, 45.85), (7.1, 45.2), (6.9, 44.6),
            (6.9, 44.4), (7.7, 44.1), (7.55, 43.75), (6.0, 42.9)] + list(reversed(VERDUN[9:])))   # Hoch- und Niederburgund (ab 933 Königreich Arelat)
REGNUM_ITALIAE = P([(7.55, 43.78), (7.7, 44.1), (6.9, 44.4), (7.0, 45.0), (7.1, 45.25), (6.85, 45.85), (7.9, 46.0), (8.4, 46.45), (9.3, 46.5), (10.2, 46.6),
                    (10.5, 46.85), (11.5, 47.0), (12.2, 47.05), (12.9, 46.6), (13.7, 46.5), (13.8, 45.75), (13.1, 45.6), (12.4, 45.2), (12.4, 44.9),
                    (11.7, 44.75), (11.3, 44.45), (11.6, 44.1), (11.9, 43.85), (12.1, 43.5), (12.15, 43.15), (12.6, 43.0), (13.0, 42.7), (13.9, 42.9),
                    (14.3, 42.4), (13.9, 41.95), (13.35, 42.0), (13.2, 42.35), (12.75, 42.55), (12.2, 42.75), (11.9, 42.55), (11.55, 42.3),
                    (10.5, 42.9), (10.0, 43.9), (8.5, 44.4)])   # Ober- und Mittelitalien mit Tuszien und Spoleto, ohne Kirchenstaat
KIRCHENSTAAT = P([(11.55, 42.3), (11.9, 42.55), (12.2, 42.75), (12.15, 43.15), (12.1, 43.5), (11.9, 43.85), (11.6, 44.1), (11.3, 44.45), (11.7, 44.75),
                  (12.4, 44.9), (12.7, 44.2), (13.2, 43.9), (13.7, 43.6), (13.0, 43.3), (12.6, 43.0), (12.75, 42.55), (13.2, 42.35), (13.35, 42.0),
                  (13.4, 41.65), (13.25, 41.3), (12.6, 41.3), (11.9, 41.8)])   # Patrimonium Petri, Perugia, Exarchat Ravenna und Pentapolis
SUED_KGR = P([(13.25, 41.3), (13.4, 41.65), (13.35, 42.0), (13.2, 42.35), (13.3, 42.65), (13.85, 42.95), (15.0, 42.2), (16.2, 41.95), (18.7, 40.1),
              (16.6, 38.3), (15.6, 37.85), (15.6, 40.0), (14.3, 40.4)])   # festländischer Süden (Königreich Sizilien, ab 1282 Neapel)
BENEVENT = P([(13.4, 41.65), (13.9, 41.95), (14.5, 42.1), (15.3, 41.95), (16.0, 41.5), (15.6, 41.1), (15.9, 40.6), (15.7, 40.0), (15.0, 40.1),
              (14.3, 40.4), (13.25, 41.3)])   # langobardisches Fürstentum Benevent (mit Salerno und Capua)
FR_487 = P([(-1.55, 48.65), (-1.9, 49.7), (0.2, 49.95), (1.6, 50.6), (1.6, 51.2), (3.4, 51.5), (4.3, 51.9), (5.9, 51.85), (6.96, 50.94), (7.6, 50.35),
            (6.6, 49.6), (6.3, 49.0), (5.6, 48.3), (4.6, 47.9), (3.6, 47.5), (2.9, 47.6), (1.9, 47.9), (0.7, 47.4), (-0.6, 47.4), (-1.2, 47.8)])
AQUIT_507 = P([(-0.6, 47.4), (0.7, 47.4), (1.9, 47.9), (2.9, 47.6), (3.6, 47.5), (4.0, 46.9), (4.3, 46.0), (4.2, 45.1), (4.0, 44.3), (3.3, 43.7),
               (2.2, 43.2), (2.0, 42.45), (0.7, 42.7), (-0.6, 42.8), (-1.5, 43.1), (-1.85, 43.4), (-2.2, 43.6), (-1.6, 45.5), (-2.3, 47.2)])
RHEIN_ALAM = P([(6.96, 50.94), (8.0, 50.6), (9.5, 50.3), (10.5, 49.5), (10.9, 48.4), (10.9, 47.6), (9.6, 47.55), (8.6, 47.65), (7.6, 47.55),
                (6.9, 47.45), (6.3, 48.0), (6.3, 49.0), (6.6, 49.6), (7.6, 50.35)])
BURG_534 = P([(4.6, 47.9), (5.4, 47.9), (6.0, 47.75), (6.9, 47.45), (7.6, 47.55), (8.3, 47.2), (7.9, 46.6), (7.9, 46.0), (6.85, 45.85), (7.1, 45.2),
              (6.9, 44.6), (6.0, 44.2), (5.0, 43.9), (4.65, 43.95), (4.0, 44.3), (4.2, 45.1), (4.3, 46.0), (4.0, 46.9), (3.6, 47.5)])
PROVENCE = P([(4.65, 43.95), (5.0, 43.9), (6.0, 44.2), (6.9, 44.4), (7.7, 44.1), (7.55, 43.75), (6.0, 42.9), (4.75, 43.3), (4.62, 43.68)])
THUERINGEN = P([(9.6, 51.0), (9.9, 51.5), (10.8, 51.9), (11.9, 51.5), (11.95, 50.9), (11.9, 50.3), (10.9, 50.2), (10.0, 50.5)])
BAYERN = P([(10.9, 48.4), (10.9, 47.5), (11.5, 47.0), (12.2, 47.05), (12.9, 46.6), (14.3, 47.5), (14.45, 48.25), (13.8, 48.75), (13.4, 49.1),
            (12.6, 49.7), (12.1, 50.3), (11.6, 49.9), (11.0, 49.3), (10.9, 48.7)])
OSTMARK_KAR = P([(14.45, 48.25), (14.5, 48.6), (15.2, 48.5), (16.1, 48.4), (16.9, 48.15), (16.4, 47.7), (16.1, 46.85), (16.3, 46.5), (15.8, 46.6),
                 (14.6, 46.45), (13.7, 46.5), (12.9, 46.6), (14.3, 47.5)])   # Ostmark (Österreich) und Karantanien
KRAIN = P([(13.7, 46.5), (14.6, 46.45), (15.8, 46.6), (15.7, 45.85), (15.3, 45.45), (14.6, 45.5), (13.9, 45.6), (13.6, 45.75)])   # Mark Krain (973)
NEUMARK = P([(14.6, 53.4), (15.9, 53.7), (16.0, 53.1), (15.7, 52.8), (15.5, 52.3), (14.6, 52.4)])   # brandenburgische Neumark östlich der Oder
THRAKIEN_OBER = P([(23.0, 41.5), (23.7, 42.8), (25.0, 42.7), (26.3, 42.8), (27.8, 42.9), (27.9, 42.3), (26.0, 42.0), (24.0, 41.6)])   # Oberthrakien (Philippopel)
SEPTIMANIEN = P([(2.0, 42.45), (2.2, 43.2), (3.3, 43.7), (4.4, 43.95), (4.62, 43.68), (4.75, 43.3), (3.6, 43.1), (3.15, 42.45)])
FRIESLAND = P([(4.3, 51.95), (5.9, 51.85), (6.1, 52.3), (7.2, 52.9), (8.6, 53.15), (8.9, 53.9), (6.9, 53.6), (5.0, 53.4), (4.4, 52.6)])
SACHSEN = P([(6.6, 51.85), (7.2, 52.9), (8.6, 53.15), (8.9, 53.9), (8.5, 54.4), (9.6, 54.4), (10.2, 54.3), (10.7, 53.9), (10.8, 53.4), (11.3, 53.1),
             (11.8, 52.7), (11.9, 52.1), (10.8, 51.9), (9.9, 51.5), (9.0, 51.3), (8.0, 51.3), (7.0, 51.5)])
FR_507 = unary_union([FR_487, AQUIT_507, RHEIN_ALAM])
FR_534 = unary_union([FR_507, BURG_534, PROVENCE, THUERINGEN, BAYERN])
FR_734 = FR_534.union(FRIESLAND)
FR_759 = FR_734.union(SEPTIMANIEN)
FR_774 = FR_759.union(REGNUM_ITALIAE)
FR_796 = unary_union([FR_774, OSTMARK_KAR, MARCA])
FR_804 = FR_796.union(SACHSEN)
AWAREN = P([(16.1, 48.3), (17.0, 48.6), (18.5, 48.4), (20.0, 48.5), (21.5, 48.4), (22.5, 48.0), (23.0, 47.0), (22.5, 45.6), (22.0, 44.8), (20.5, 44.8),
            (19.0, 44.9), (17.0, 45.2), (15.7, 45.9), (15.5, 46.8), (16.0, 47.6)])
BOEHMEN = P([(12.1, 50.3), (12.9, 50.45), (13.6, 50.7), (14.3, 50.9), (14.8, 50.9), (15.3, 50.85), (16.0, 50.65), (16.3, 50.6), (16.9, 50.3), (17.6, 50.2),
             (17.8, 49.95), (18.5, 49.6), (18.3, 49.2), (17.6, 48.8), (17.1, 48.65), (16.9, 48.6), (16.0, 48.75), (15.0, 48.95), (14.6, 48.6),
             (13.8, 48.75), (13.4, 49.1), (12.6, 49.7)])   # Böhmen und Mähren
MEISSEN = P([(11.95, 51.5), (13.2, 51.7), (14.2, 51.3), (14.3, 50.9), (13.6, 50.7), (12.9, 50.45), (12.1, 50.3), (11.9, 50.3), (11.7, 50.9)])
OSTSIEDLUNG = P([(10.7, 53.9), (11.5, 54.2), (13.0, 54.7), (14.3, 54.2), (15.6, 54.3), (15.9, 53.7), (14.6, 53.4), (14.6, 52.4), (14.75, 51.6),
                 (15.0, 51.25), (14.3, 50.9), (14.2, 51.3), (13.2, 51.7), (11.95, 51.5), (11.9, 52.1), (11.8, 52.7), (11.3, 53.1), (10.8, 53.4)])
SCHLESIEN = P([(15.0, 51.25), (15.6, 51.8), (16.6, 51.75), (17.6, 51.4), (18.4, 51.0), (18.9, 50.4), (18.5, 49.6), (17.8, 49.95), (16.9, 50.3),
               (16.3, 50.6), (15.3, 50.85)])
HRR_880 = OSTFRANKEN_843.union(LOTHARINGIEN)
HRR_962 = unary_union([HRR_880, REGNUM_ITALIAE, BOEHMEN, MEISSEN, OSTMARK_KAR, KRAIN])
HRR_1032 = HRR_962.union(ARELAT)
HRR_1150 = HRR_1032.union(OSTSIEDLUNG)
HRR_1250 = HRR_1150.union(NEUMARK)
HRR_1335 = HRR_1250.union(SCHLESIEN)
POLEN_PIAST = P([(14.6, 53.4), (14.5, 54.0), (16.0, 54.4), (18.0, 54.9), (19.0, 54.4), (19.0, 54.0), (19.5, 53.4), (21.0, 53.5), (22.5, 53.1), (23.5, 52.3),
                 (24.0, 51.6), (23.6, 50.6), (22.8, 49.6), (22.0, 49.3), (20.5, 49.4), (19.8, 49.2), (18.9, 49.5), (18.5, 49.6), (17.8, 49.95),
                 (16.9, 50.3), (16.3, 50.6), (15.3, 50.85), (15.0, 51.25), (14.75, 51.6), (14.6, 52.4)])
POLEN_1320 = P([(15.5, 52.3), (15.7, 52.8), (16.0, 53.1), (17.0, 53.2), (18.0, 53.1), (18.7, 53.2), (19.5, 53.3), (21.0, 53.5), (22.5, 53.1), (23.5, 52.3),
                (24.0, 51.6), (23.6, 50.6), (22.8, 49.6), (22.0, 49.3), (20.5, 49.4), (19.8, 49.2), (18.9, 49.5), (18.9, 50.4), (18.4, 51.0),
                (17.6, 51.4), (16.6, 51.75), (15.6, 51.8)])   # Groß- und Kleinpolen, Masowien (ohne Schlesien und Pommerellen)
ROTREUSSEN = P([(23.6, 50.6), (24.5, 50.7), (25.6, 50.2), (26.2, 49.2), (25.8, 48.6), (25.0, 48.6), (23.5, 48.9), (22.8, 49.3), (22.8, 49.6)])
POMMERELLEN = P([(16.9, 54.7), (18.9, 54.6), (19.0, 54.0), (18.7, 53.2), (17.6, 53.2), (16.7, 53.6), (16.5, 54.2)])
UNGARN_1000 = P([(16.95, 48.15), (17.05, 48.6), (17.6, 48.8), (18.3, 49.2), (18.8, 49.5), (19.8, 49.2), (20.5, 49.4), (21.5, 49.4), (22.6, 49.05),
                 (23.5, 48.1), (24.5, 47.9), (25.2, 47.6), (25.8, 46.8), (26.2, 46.0), (25.9, 45.55), (25.2, 45.45), (24.2, 45.45), (23.0, 45.35),
                 (22.5, 44.75), (21.4, 44.8), (20.5, 44.8), (19.4, 44.9), (18.8, 45.8), (17.5, 45.9), (16.9, 46.3), (16.3, 46.5), (16.1, 46.85),
                 (16.4, 47.7)])   # Karpatenbecken mit Siebenbürgen
KROATIEN = P([(15.6, 46.45), (16.3, 46.5), (16.9, 46.3), (17.5, 45.9), (18.8, 45.8), (19.4, 44.9), (18.0, 45.1), (17.2, 45.15), (16.3, 44.8), (15.9, 44.3),
              (16.5, 43.9), (17.4, 43.1), (16.0, 43.2), (14.6, 44.8), (13.6, 45.3), (14.6, 45.6), (15.3, 46.0)])   # Kroatien und Slawonien (mit Ungarn ab 1102)
BULG_681 = P([(22.9, 43.9), (24.9, 43.7), (27.3, 44.15), (28.2, 45.4), (29.7, 45.3), (28.6, 44.4), (27.9, 43.1), (27.8, 42.9), (26.3, 42.8), (25.0, 42.7),
              (23.7, 42.8), (22.9, 43.0)])   # zwischen Donau und Balkangebirge, mit dem Donaudelta
BULG_850 = P([(22.5, 44.7), (24.0, 44.6), (26.0, 45.0), (28.2, 45.4), (29.7, 45.3), (28.6, 44.4), (28.0, 43.0), (27.6, 42.4), (26.5, 42.3), (25.5, 42.1),
              (24.7, 42.15), (23.5, 41.5), (22.5, 41.1), (20.8, 41.1), (20.6, 41.8), (21.3, 42.5), (22.0, 43.5), (22.3, 44.2)])
BULG_SIMEON = P([(20.5, 44.8), (22.5, 44.7), (24.0, 44.6), (26.0, 45.0), (28.2, 45.4), (29.7, 45.3), (28.6, 44.4), (28.0, 43.0), (27.7, 42.4), (27.9, 41.9),
                 (26.5, 41.4), (25.5, 41.0), (23.8, 40.9), (22.6, 40.5), (21.5, 39.6), (20.0, 40.0), (19.4, 41.4), (19.5, 42.4), (19.5, 44.0)])
BULG_SAMUEL = P([(21.5, 44.6), (22.5, 44.6), (22.9, 44.1), (22.9, 43.0), (23.5, 42.0), (23.0, 41.0), (22.4, 40.3), (21.0, 39.9), (19.8, 40.4), (19.4, 41.4), (19.5, 42.4), (20.3, 43.2),
                 (21.5, 44.0)])   # Reich Samuels (Westbulgarien, Ohrid)
BULG_2 = P([(22.6, 44.2), (24.9, 43.75), (27.3, 44.15), (28.6, 44.4), (28.0, 43.0), (27.8, 42.4), (26.5, 42.2), (25.0, 42.1), (23.5, 42.3), (22.4, 42.5),
            (22.3, 43.4)])
BULG_ASEN = P([(22.6, 44.2), (24.9, 43.75), (27.3, 44.15), (28.6, 44.4), (28.0, 43.0), (27.7, 42.4), (26.5, 41.4), (25.5, 41.0), (23.8, 40.9),
               (22.6, 40.6), (21.5, 40.4), (19.6, 40.9), (19.5, 41.8), (20.6, 42.3), (21.5, 43.0), (22.3, 43.4)])   # Iwan Assen II. (1230–1241)
RASKA = P([(19.0, 43.5), (19.3, 43.6), (20.5, 43.9), (21.5, 43.3), (21.6, 42.6), (20.9, 42.2), (20.0, 42.0), (19.3, 41.9), (18.6, 42.4), (18.5, 43.0)])
SERBIEN_1282 = P([(19.3, 43.9), (20.5, 44.3), (21.6, 44.0), (22.5, 43.2), (22.6, 42.2), (22.4, 41.5), (21.2, 41.2), (20.5, 41.6), (19.5, 41.8), (18.5, 42.4),
                  (18.5, 43.0)])
SERBIEN_DUSAN = P([(19.3, 43.9), (20.5, 44.6), (21.6, 44.0), (22.5, 43.2), (22.8, 42.2), (24.0, 41.5), (24.4, 40.9), (23.8, 40.7), (22.7, 40.6), (22.4, 40.0),
                   (22.9, 39.4), (22.8, 39.0), (21.8, 38.8), (21.0, 38.8), (20.1, 39.4), (19.4, 40.4), (19.4, 41.8), (18.5, 42.4), (18.5, 43.0)])
SERBIEN_MORAVA = P([(19.3, 43.9), (20.3, 44.8), (21.5, 44.8), (22.5, 44.2), (22.4, 43.3), (21.9, 42.4), (21.1, 42.4), (20.3, 42.8), (19.5, 43.2)])
LIT_KERN = P([(21.0, 55.7), (22.5, 56.3), (24.0, 56.3), (26.0, 55.8), (26.5, 55.3), (26.0, 54.3), (25.8, 53.6), (25.0, 53.3), (23.8, 53.6), (23.5, 54.2),
              (22.8, 54.6), (22.0, 55.1), (21.2, 55.3)])
LIT_GED = LIT_KERN.union(P([(26.5, 55.3), (28.0, 56.0), (28.8, 55.6), (30.5, 55.3), (31.0, 54.0), (30.5, 52.5), (29.0, 52.0), (27.0, 51.8), (24.5, 51.9),
                            (23.7, 52.1), (23.8, 53.6), (25.0, 53.3)]))
LIT_GROSS = LIT_GED.union(P([(23.7, 52.1), (24.0, 51.6), (24.1, 50.6), (25.6, 50.2), (26.4, 49.0), (28.0, 48.3), (29.5, 47.6), (30.3, 46.3), (31.5, 46.6),
                             (32.0, 47.5), (33.0, 48.5), (34.5, 49.6), (35.0, 50.6), (34.5, 51.6), (33.0, 52.5), (33.0, 54.0), (32.05, 54.8), (33.5, 55.4),
                             (31.5, 56.0), (30.5, 55.3), (31.0, 54.0), (30.5, 52.5)]))
PREUSSEN = P([(18.7, 53.2), (19.0, 54.0), (19.5, 54.4), (20.5, 54.9), (21.2, 55.75), (21.9, 55.1), (22.9, 54.4), (22.8, 53.9), (22.4, 53.5), (21.0, 53.3),
              (20.7, 53.2), (19.8, 53.3), (19.2, 53.1), (18.6, 53.0)])
LIVLAND = P([(21.0, 56.1), (21.0, 57.5), (22.5, 57.8), (23.5, 59.3), (24.0, 59.5), (28.0, 59.5), (28.2, 59.3), (27.5, 58.8), (27.4, 58.0), (27.8, 57.4),
             (28.0, 56.7), (26.8, 55.9), (25.0, 56.2), (23.0, 56.4), (22.0, 56.4)])
RUS_KIEW = P([(23.7, 52.1), (24.0, 51.6), (23.6, 50.6), (22.8, 49.6), (22.6, 49.05), (23.5, 48.1), (24.5, 47.9), (25.6, 48.0), (26.5, 48.3), (28.0, 48.6), (30.5, 48.8), (32.0, 49.2),
              (34.5, 49.6), (36.0, 50.8), (37.5, 52.2), (40.0, 53.5), (41.5, 54.8), (42.5, 55.8), (44.0, 56.3), (43.0, 57.5), (40.0, 58.8), (38.0, 60.0),
              (36.0, 61.5), (33.0, 62.0), (31.0, 61.5), (30.5, 60.0), (28.0, 59.6), (28.2, 59.3), (27.5, 58.8), (27.4, 58.0), (27.8, 57.4),
              (28.0, 56.7), (27.0, 55.6), (26.0, 54.5), (25.0, 53.8), (24.0, 53.4)])
RUS_NO = P([(27.8, 57.4), (27.4, 58.0), (27.5, 58.8), (28.2, 59.3), (28.0, 59.6), (30.0, 60.0), (31.0, 61.5), (33.0, 62.5), (36.0, 63.0), (40.0, 62.0),
            (44.0, 61.0), (46.0, 59.5), (47.0, 57.5), (45.5, 56.0), (44.0, 55.6), (41.0, 53.8), (39.5, 53.2), (38.0, 53.6), (36.5, 54.5), (35.0, 55.3),
            (33.5, 55.4), (31.5, 56.0), (30.0, 56.5), (28.5, 56.6)])   # Wladimir-Susdal, Moskau, Twer, Rjasan, Nowgorod, Pskow
GALIZIEN = P([(23.7, 52.1), (24.5, 51.9), (26.0, 51.6), (26.5, 50.5), (27.0, 49.2), (26.4, 48.4), (25.2, 47.9), (24.5, 47.9), (23.5, 48.1), (22.6, 49.05),
              (22.8, 49.6), (23.6, 50.6), (24.0, 51.6)])   # Galizien-Wolhynien
GOLDENE_HORDE = P([(28.2, 45.4), (28.9, 46.8), (30.0, 48.5), (32.5, 49.4), (34.5, 49.6), (36.0, 50.8), (37.5, 52.2), (39.5, 53.2), (41.0, 53.8),
                   (44.0, 54.5), (47.0, 55.5), (49.1, 55.8), (52.0, 56.5), (56.0, 56.5), (58.0, 55.0), (61.0, 55.5), (68.0, 54.0), (72.0, 52.0),
                   (70.0, 47.0), (66.0, 45.5), (61.5, 44.5), (60.5, 42.0), (57.0, 41.5), (54.0, 41.0), (52.0, 42.0), (48.3, 42.05), (46.0, 43.0),
                   (44.0, 43.0), (41.0, 43.5), (38.0, 44.5), (37.0, 45.0), (33.5, 44.4), (32.5, 45.5), (30.5, 46.4), (29.7, 45.3)])
ILCHANAT = P([(38.3, 38.3), (40.0, 40.5), (41.5, 41.3), (43.0, 41.5), (44.5, 42.6), (46.0, 42.2), (48.3, 42.05), (49.8, 40.4), (49.0, 38.5), (50.0, 37.0),
              (54.0, 37.4), (56.5, 38.2), (59.0, 37.5), (61.5, 36.5), (62.5, 35.5), (62.0, 31.0), (61.5, 29.5), (62.0, 26.0), (61.6, 25.2), (57.0, 25.0),
              (56.3, 27.0), (53.0, 26.5), (50.5, 28.5), (48.5, 30.0), (47.5, 29.5), (44.5, 30.5), (42.0, 32.0), (40.8, 34.4), (39.0, 35.8), (38.3, 36.8),
              (37.8, 37.3)])
TSCHAGATAI = P([(60.0, 40.5), (61.5, 44.0), (66.0, 45.5), (70.0, 46.5), (75.0, 46.5), (79.0, 46.0), (83.0, 46.5), (88.0, 44.5), (90.0, 42.5), (88.0, 40.0),
                (85.0, 38.0), (80.0, 36.5), (75.0, 36.5), (71.0, 36.8), (68.0, 37.0), (65.0, 37.5), (62.0, 37.5), (61.0, 38.5)])
WALES = P([(-5.6, 51.6), (-3.0, 51.45), (-2.65, 51.9), (-3.1, 52.5), (-2.95, 53.3), (-4.7, 53.5), (-5.6, 52.0)])
ANGEVIN = P([(-1.55, 48.62), (-1.9, 49.75), (0.2, 49.9), (1.4, 50.05), (1.7, 49.6), (1.6, 49.1), (1.0, 48.4), (1.2, 47.7), (1.2, 47.2), (1.5, 46.6),
             (2.3, 46.3), (2.6, 45.5), (2.5, 44.6), (1.9, 44.0), (1.3, 43.5), (0.5, 43.1), (-0.6, 42.8), (-1.5, 43.1), (-1.85, 43.4), (-2.2, 43.6),
             (-1.6, 45.5), (-2.5, 46.8), (-2.2, 47.2), (-1.4, 47.6), (-1.1, 48.0)])   # Normandie, Maine, Anjou, Touraine, Poitou, Aquitanien
GUYENNE = P([(-1.6, 45.9), (-1.3, 45.8), (0.0, 45.2), (0.5, 44.6), (0.3, 43.9), (-0.3, 43.4), (-1.0, 43.3), (-1.6, 43.35), (-2.0, 44.5)])
BRETIGNY = P([(-1.6, 47.0), (0.2, 46.9), (1.0, 46.4), (2.3, 46.0), (2.6, 44.9), (2.9, 44.2), (1.9, 43.9), (1.0, 43.4), (0.3, 43.0), (-0.6, 42.8), (-1.5, 43.1),
              (-1.85, 43.4), (-2.2, 43.6), (-1.6, 45.5), (-2.3, 46.6)])
CALAIS = P([(1.55, 51.1), (2.1, 51.05), (2.05, 50.8), (1.6, 50.8)])
LANCASTER = P([(-1.9, 49.75), (1.4, 50.05), (2.2, 50.35), (3.2, 49.9), (3.6, 49.2), (3.3, 48.4), (2.2, 48.3), (1.0, 48.0), (0.2, 47.6), (-1.0, 48.0),
               (-1.55, 48.62)])   # Normandie, Maine, Île-de-France (Vertrag von Troyes 1420)
NORMANDIE = P([(-1.9, 49.75), (1.4, 50.05), (1.7, 49.6), (1.6, 49.1), (0.8, 48.6), (-0.6, 48.5), (-1.55, 48.62)])
NORDINDIEN = P([[68, 31], [77, 32], [85, 27], [88, 24], [82, 22], [74, 22], [68, 24]])

# Ostrom um 480 aus data/reiche.json (Reich „rom“, Seite Ost)
_r = json.load(open(os.path.join(HERE, 'data', 'reiche.json'), encoding='utf-8'))
OSTROM = unary_union([shape(f['geometry']).buffer(0) for f in _r['regionen'] if f['properties']['reich'] == 'rom' and f['properties'].get('seite') == 'o' and f['properties']['von'] <= 479 < f['properties']['bis']])

# (reich, name, von, bis, fläche)
REGIONEN = [
    # --- Byzanz (Reich „rom“, Ostrom) ---
    ('rom', 'Oströmisches Reich', 481, 533, OSTROM),
    ('rom', 'Byzanz: Rückeroberung Nordafrikas (Vandalenkrieg)', 533, 535, OSTROM.union(AFRIKA_N)),
    ('rom', 'Byzanz unter Justinian (größte Ausdehnung)', 554, 568, OSTROM.union(AFRIKA_N).union(ITALIEN).union(SIZILIEN).union(SPANIEN_SUED)),
    ('rom', 'Byzanz nach dem Einfall der Langobarden', 568, 636, OSTROM.union(AFRIKA_N).union(ITALIEN_REST).union(SPANIEN_SUED)),
    ('rom', 'Byzanz nach den arabischen Eroberungen', 636, 698, ANATOLIEN.union(BALKAN_KUESTE).union(AFRIKA_N).union(ITALIEN_REST)),
    ('rom', 'Byzanz: Kleinasien, Balkanküste, Ravenna, Rom und Süditalien', 698, 751, ANATOLIEN.union(BALKAN_KUESTE).union(ITALIEN_REST)),
    ('rom', 'Byzanz unter der Makedonischen Dynastie', 867, 971, ANATOLIEN.union(BALKAN_SUED.difference(BULG_850)).union(SUEDITALIEN).union(ANTIOCHIA)),
    ('rom', 'Byzanz nach dem Sieg über Bulgarien (Basileios II.)', 1018, 1071, ANATOLIEN.union(BALKAN).union(SUEDITALIEN).union(ANTIOCHIA).union(ARMENIEN_W)),
    ('rom', 'Byzanz nach Manzikert (Kleinasien verloren)', 1071, 1097, BALKAN.union(NW_ANAT)),
    ('rom', 'Byzanz unter den Komnenen', 1097, 1185, BALKAN.union(WEST_ANAT)),
    ('rom', 'Byzanz nach dem Abfall Bulgariens', 1185, 1204, BALKAN_SUED.union(WEST_ANAT)),
    ('rom', 'Nachfolgestaaten: Kaiserreich Nikaia und Despotat Epirus', 1204, 1261, WEST_ANAT.difference(box(31, 30, 40, 45)).union(EPIRUS)),
    ('rom', 'Nachfolgestaat: Kaiserreich Trapezunt', 1204, 1400, TRAPEZUNT),
    ('rom', 'Byzanz nach der Rückeroberung Konstantinopels', 1261, 1300, THRAKIEN.union(BALKAN_SUED.intersection(box(21, 38, 30, 42.5))).union(NW_ANAT).union(MOREA)),
    ('rom', 'Byzanz: Thrakien, Thessaloniki, Morea', 1300, 1354, THRAKIEN.union(MOREA)),
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
    ('seldsch', 'Reich der Großseldschuken', 1037, 1055, IRAN.union(TRANSOX)),
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
    ('frankreich', 'Westfrankenreich (mit der Spanischen Mark)', 843, 987, WESTFRANKEN.union(MARCA)),
    ('frankreich', 'Königreich Frankreich (Kapetinger)', 987, 1312, WESTFRANKEN),
    ('hrr', 'Ostfrankenreich', 843, 880, OSTFRANKEN_843),
    ('hrr', 'Heiliges Römisches Reich (mit Reichsitalien und Böhmen)', 962, 1032, HRR_962),
    ('hrr', 'Heiliges Römisches Reich (Reichsitalien und Burgund nur noch locker gebunden)', 1250, 1335, HRR_1250),
    ('england', 'Königreich England (ohne Wales)', 927, 1283, ENGLAND.difference(WALES)),
    ('rus', 'Kiewer Rus', 882, 1240, RUS_KIEW),
    ('rus', 'Russische Fürstentümer (Wladimir-Susdal, Moskau, Twer, Rjasan, Nowgorod) unter der Goldenen Horde', 1240, 1453, RUS_NO),
    ('bulgarien', 'Erstes Bulgarisches Reich', 681, 800, BULG_681),
    ('bulgarien', 'Zweites Bulgarisches Reich', 1185, 1230, BULG_2),
    ('ungarn', 'Königreich Ungarn', 1000, 1102, UNGARN_1000),
    ('polen', 'Polen der Piasten', 966, 1138, POLEN_PIAST),
    ('indien_ma', 'Reich des Harsha', 606, 647, P([[73, 31], [80, 30], [88, 26], [86, 23], [80, 23], [74, 25]])),
    ('indien_ma', 'Sultanat Delhi', 1206, 1320, NORDINDIEN),
    ('indien_ma', 'Sultanat Delhi unter den Tughluqs', 1320, 1398, NORDINDIEN.union(P([[74, 22], [84, 22], [84, 18], [80, 12], [77, 12], [73, 17], [72, 21]]))),
    ('indien_ma', 'Sultanat Delhi nach dem Einfall Timurs', 1398, 1453, NORDINDIEN.intersection(box(70, 25, 82, 32))),
    # --- Lücken geschlossen (am Ende, damit die ids der Regionen davor gleich bleiben) ---
    # Ägypten zwischen Abbasiden und Fatimiden: 905–935 direkt abbasidisch, 935–969 Ichschididen unter nomineller Oberhoheit Bagdads
    ('kalifat', 'Ägypten unter abbasidischen Statthaltern, ab 935 Ichschididen (nominell abbasidisch)', 909, 969, NIL),
    # Thessaloniki bleibt bis zur osmanischen Eroberung 1387 byzantinisch (1403–1423 erneut, siehe data/reiche.json)
    ('rom', 'Byzanz: Thessaloniki und Chalkidike', 1300, 1387, P([[22.4, 40.95], [23.6, 40.95], [24.0, 40.3], [23.9, 39.9], [22.9, 40.0], [22.5, 40.4]]).difference(THRAKIEN)),
    # --- Mitteleuropa entlang Flüssen und Gebirgen (ergänzt; am Ende, damit die ids davor gleich bleiben) ---
    ('frankreich', 'Königreich Frankreich (mit Lyon seit 1312)', 1312, 1453, WESTFRANKEN.union(LYONNAIS)),
    ('hrr', 'Ostfrankenreich mit Lotharingien (seit 880)', 880, 962, HRR_880),
    ('hrr', 'Heiliges Römisches Reich (mit Burgund seit 1032/33)', 1032, 1150, HRR_1032),
    ('hrr', 'Heiliges Römisches Reich (Ostsiedlung bis zur Oder)', 1150, 1250, HRR_1150),
    ('hrr', 'Heiliges Römisches Reich (Schlesien mit Böhmen ab 1335)', 1335, 1453, HRR_1335),
    ('lothar', 'Lotharingien (Mittelreich Lothars I., ab 855 Lothars II.)', 843, 880, LOTHARINGIEN),
    ('lothar', 'Burgund und Provence (ab 933 Königreich Arelat)', 843, 1032, ARELAT),
    ('italien_ma', 'Regnum Italiae (Ober- und Mittelitalien)', 843, 962, REGNUM_ITALIAE),
    ('kirchenstaat', 'Kirchenstaat (Patrimonium Petri, Exarchat Ravenna, Pentapolis)', 756, 1453, KIRCHENSTAAT),
    ('langob', 'Fürstentum Benevent (langobardisch, mit Salerno und Capua)', 774, 1077, BENEVENT),
    ('sizilien_ma', 'Emirat Sizilien (Aghlabiden, Fatimiden, Kalbiten)', 902, 1061, SIZILIEN),
    ('sizilien_ma', 'Normannen in Süditalien und Sizilien', 1061, 1130, SUED_KGR.union(SIZILIEN)),
    ('sizilien_ma', 'Königreich Sizilien (Normannen, ab 1194 Staufer, ab 1266 Anjou)', 1130, 1282, SUED_KGR.union(SIZILIEN)),
    ('sizilien_ma', 'Königreiche Neapel (Anjou) und Sizilien (Aragón) nach der Sizilianischen Vesper', 1282, 1453, SUED_KGR.union(SIZILIEN)),
    ('franken', 'Reich Chlodwigs nach dem Sieg über Syagrius', 487, 507, FR_487),
    ('franken', 'Frankenreich nach Vouillé (mit Aquitanien, Alamannen und Rheinfranken)', 507, 534, FR_507),
    ('franken', 'Frankenreich der Merowinger (mit Burgund, Provence, Thüringen; Bayern abhängig)', 534, 734, FR_534),
    ('franken', 'Frankenreich mit Friesland', 734, 759, FR_734),
    ('franken', 'Frankenreich der Karolinger (mit Septimanien seit 759)', 759, 774, FR_759),
    ('franken', 'Frankenreich Karls des Großen mit dem Langobardenreich', 774, 796, FR_774),
    ('franken', 'Frankenreich nach den Awarenkriegen (Ostmark, Karantanien, Spanische Mark)', 796, 804, FR_796),
    ('franken', 'Reich Karls des Großen (Kaiser seit 800; Sachsen unterworfen)', 804, 843, FR_804),
    ('andalus', 'Septimanien (Narbonne, arabisch besetzt)', 720, 759, SEPTIMANIEN),
    ('awaren', 'Awarenreich (Khaganat im Karpatenbecken)', 568, 796, AWAREN),
    ('ostgot', 'Provence (ostgotisch, 508–537)', 508, 537, PROVENCE),
    ('polen', 'Polen in Teilfürstentümern (Seniorat der Piasten)', 1138, 1320, POLEN_PIAST),
    ('polen', 'Königreich Polen (Krönung Władysławs I. 1320)', 1320, 1349, POLEN_1320),
    ('polen', 'Königreich Polen mit Rotreußen (seit 1349)', 1349, 1453, POLEN_1320.union(ROTREUSSEN)),
    ('ungarn', 'Königreich Ungarn mit Kroatien und Slawonien (Personalunion seit 1102)', 1102, 1453, UNGARN_1000.union(KROATIEN)),
    ('bulgarien', 'Erstes Bulgarisches Reich unter Krum, Omurtag und Boris I.', 800, 893, BULG_850),
    ('bulgarien', 'Bulgarenreich unter Zar Simeon (größte Ausdehnung)', 893, 927, BULG_SIMEON),
    ('bulgarien', 'Bulgarenreich nach Simeon', 927, 971, BULG_850),
    ('bulgarien', 'Westbulgarisches Reich Samuels (Ohrid)', 971, 1018, BULG_SAMUEL),
    ('bulgarien', 'Zweites Bulgarisches Reich unter Iwan Assen II.', 1230, 1246, BULG_ASEN),
    ('bulgarien', 'Zweites Bulgarisches Reich (Tarnowo)', 1246, 1396, BULG_2),
    ('serbien', 'Serbien der Nemanjiden (Raška und Zeta)', 1180, 1282, RASKA),
    ('serbien', 'Königreich Serbien (Milutin)', 1282, 1346, SERBIEN_1282),
    ('serbien', 'Zarenreich Stefan Dušans', 1346, 1371, SERBIEN_DUSAN),
    ('serbien', 'Serbien nach der Schlacht an der Mariza (Moravia-Serbien, Despotat)', 1371, 1453, SERBIEN_MORAVA),
    ('litauen', 'Großfürstentum Litauen', 1240, 1316, LIT_KERN),
    ('litauen', 'Großfürstentum Litauen unter Gediminas', 1316, 1345, LIT_GED),
    ('litauen', 'Großfürstentum Litauen bis zum Schwarzen Meer (Algirdas, Vytautas)', 1345, 1453, LIT_GROSS),
    ('orden', 'Deutscher Orden: Kulmerland und Preußen (Eroberung 1230–1283)', 1230, 1283, PREUSSEN.intersection(box(18, 52, 21, 55))),
    ('orden', 'Deutschordensstaat Preußen', 1283, 1308, PREUSSEN),
    ('orden', 'Deutschordensstaat Preußen mit Pommerellen (Danzig 1308)', 1308, 1453, PREUSSEN.union(POMMERELLEN)),
    ('orden', 'Livland (Orden, Bistümer, Riga; Nordestland dänisch)', 1237, 1346, LIVLAND.difference(box(23, 58.7, 28.5, 60))),
    ('orden', 'Livland (mit Estland seit 1346)', 1346, 1453, LIVLAND),
    ('rus', 'Fürstentum Galizien-Wolhynien', 1240, 1349, GALIZIEN),
    ('england', 'Angevinisches Reich in Frankreich (Normandie, Anjou, Aquitanien)', 1154, 1204, ANGEVIN),
    ('england', 'Englische Gascogne (Guyenne)', 1204, 1360, GUYENNE),
    ('england', 'Aquitanien nach dem Frieden von Brétigny, Calais', 1360, 1372, BRETIGNY.union(CALAIS)),
    ('england', 'Guyenne und Calais', 1372, 1420, GUYENNE.union(CALAIS)),
    ('england', 'Lancaster-Frankreich nach dem Vertrag von Troyes, Guyenne, Calais', 1420, 1429, unary_union([LANCASTER, GUYENNE, CALAIS])),
    ('england', 'Normandie, Guyenne und Calais', 1429, 1450, unary_union([NORMANDIE, GUYENNE, CALAIS])),
    ('england', 'Guyenne und Calais (Bordeaux fällt 1453)', 1450, 1453, GUYENNE.union(CALAIS)),
    ('england', 'Königreich England mit Wales (seit 1283)', 1283, 1453, ENGLAND),
    ('rom', 'Byzanz: Kleinasien, Thrakien, Balkanküste, Süditalien und Sizilien', 751, 867, unary_union([ANATOLIEN, BALKAN_KUESTE, THRAKIEN_OBER.difference(BULG_850), SUEDITALIEN, SIZILIEN])),
    ('rom', 'Byzanz im Gotenkrieg: Sizilien, Süditalien, Ravenna', 535, 552, unary_union([OSTROM, AFRIKA_N, SIZILIEN, SUEDITALIEN, P([(12.0, 44.6), (12.6, 44.6), (13.6, 43.6), (13.2, 43.4), (12.2, 44.1)])])),
    ('rom', 'Byzanz: Italien zurückerobert (552 Busta Gallorum)', 552, 554, unary_union([OSTROM, AFRIKA_N, ITALIEN, SIZILIEN])),
    ('rom', 'Byzanz nach der Eroberung Ostbulgariens (971)', 971, 1018, unary_union([ANATOLIEN, BALKAN_SUED.difference(BULG_SAMUEL), BULG_681, SUEDITALIEN, ANTIOCHIA])),
    ('rom', 'Byzanz: Konstantinopel und Umland, Morea (Adrianopel 1369 osmanisch)', 1354, 1400, P([(28.0, 41.0), (28.3, 41.6), (29.2, 41.3), (29.1, 40.95)]).union(MOREA)),
    ('seldsch', 'Großseldschuken mit Bagdad (seit 1055)', 1055, 1071, IRAN.union(TRANSOX).union(IRAK)),
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
    ('franken', 486, '486/87', 'Chlodwig besiegt Syagrius', 'Der Merowinger Chlodwig erobert das gallorömische Gebiet um Soissons.'),
    ('franken', 498, 'um 500', 'Taufe Chlodwigs', 'Chlodwig lässt sich katholisch taufen (das Jahr ist umstritten, 496–508).'),
    ('franken', 507, '507', 'Sieg bei Vouillé', 'Chlodwig besiegt die Westgoten; Aquitanien wird fränkisch.'),
    ('franken', 534, '534/37', 'Burgund und Provence', 'Die Söhne Chlodwigs erobern das Burgunderreich; die Ostgoten treten die Provence ab.'),
    ('franken', 732, '732', 'Tours und Poitiers', 'Der Hausmeier Karl Martell schlägt ein Heer aus al-Andalus zurück.'),
    ('franken', 751, '751', 'Karolinger', 'Pippin der Jüngere setzt den letzten Merowinger ab und wird König.'),
    ('franken', 774, '774', 'Langobardenreich erobert', 'Karl der Große nimmt Pavia ein und wird König der Langobarden.'),
    ('franken', 800, '800', 'Kaiserkrönung Karls des Großen', 'Papst Leo III. krönt Karl in Rom zum Kaiser.'),
    ('franken', 814, '814', 'Tod Karls des Großen', 'Sein Sohn Ludwig der Fromme folgt ihm; unter dessen Söhnen zerfällt die Einheit.'),
    ('awaren', 568, '568', 'Awaren im Karpatenbecken', 'Die Awaren übernehmen Pannonien, als die Langobarden nach Italien ziehen.'),
    ('awaren', 626, '626', 'Belagerung Konstantinopels', 'Awaren, Slawen und Perser belagern Konstantinopel vergeblich.'),
    ('awaren', 791, '791–796', 'Awarenkriege', 'Fränkische Heere erobern den „Ring“, das Zentrum des Khaganats.'),
    ('lothar', 843, '843', 'Mittelreich Lothars I.', 'Im Vertrag von Verdun erhält Lothar I. das Mittelreich von Friesland bis Italien.'),
    ('lothar', 870, '870/880', 'Lotharingien geteilt', 'In den Verträgen von Meerssen und Ribemont fällt Lotharingien an das Ostfrankenreich.'),
    ('lothar', 933, '933', 'Königreich Arelat', 'Hoch- und Niederburgund werden zum Königreich Burgund (Arelat) vereinigt.'),
    ('lothar', 1032, '1032/33', 'Burgund an das Reich', 'Nach dem Tod Rudolfs III. fällt Burgund an Kaiser Konrad II.'),
    ('italien_ma', 843, '843', 'Regnum Italiae', 'Italien gehört zum Mittelreich Lothars I.; ab 888 regieren eigene Könige.'),
    ('italien_ma', 951, '951', 'Otto I. in Italien', 'Otto I. wird König der Langobarden; 962 Kaiserkrönung in Rom.'),
    ('kirchenstaat', 756, '754/56', 'Pippinsche Schenkung', 'Pippin überlässt dem Papst die von den Langobarden eroberten Gebiete um Ravenna und Rom.'),
    ('kirchenstaat', 1077, '1077', 'Canossa', 'Im Investiturstreit erreicht Heinrich IV. in Canossa die Lösung vom Bann.'),
    ('kirchenstaat', 1309, '1309–1377', 'Päpste in Avignon', 'Die Päpste residieren in Avignon; 1378–1417 folgt das Große Schisma.'),
    ('sizilien_ma', 902, '827–902', 'Emirat Sizilien', 'Arabische Heere erobern Sizilien von Byzanz (902 fällt Taormina).'),
    ('sizilien_ma', 1061, '1061–1091', 'Normannen', 'Normannen unter Robert Guiskard und Roger I. erobern Süditalien und Sizilien.'),
    ('sizilien_ma', 1130, '1130', 'Königreich Sizilien', 'Roger II. wird König; Palermo ist ein Zentrum arabischer, griechischer und lateinischer Kultur.'),
    ('sizilien_ma', 1282, '1282', 'Sizilianische Vesper', 'Aufstand gegen Karl von Anjou: Sizilien fällt an Aragón, das Festland bleibt bei Anjou (Neapel).'),
    ('serbien', 1166, '1166', 'Stefan Nemanja', 'Nemanja eint die serbischen Gebiete; 1217 wird Serbien Königreich.'),
    ('serbien', 1346, '1346', 'Zar Stefan Dušan', 'Dušan lässt sich zum Zaren krönen; sein Reich reicht bis Thessalien.'),
    ('serbien', 1389, '1389', 'Amselfeld', 'Ein serbisches Heer unterliegt den Osmanen; Serbien wird tributpflichtig.'),
    ('litauen', 1253, '1253', 'König Mindaugas', 'Mindaugas wird zum König gekrönt; Litauen bleibt bis 1387 überwiegend heidnisch.'),
    ('litauen', 1362, '1362', 'Kiew litauisch', 'Großfürst Algirdas dehnt Litauen über weite Teile der früheren Rus aus.'),
    ('litauen', 1386, '1386', 'Union mit Polen', 'Großfürst Jogaila heiratet Jadwiga, wird König von Polen und lässt Litauen taufen.'),
    ('orden', 1230, '1230', 'Deutscher Orden in Preußen', 'Der Orden beginnt, die heidnischen Prußen zu unterwerfen.'),
    ('orden', 1309, '1309', 'Marienburg', 'Der Hochmeister verlegt seinen Sitz von Venedig auf die Marienburg.'),
    ('orden', 1410, '1410', 'Tannenberg', 'Polen und Litauen besiegen den Orden bei Tannenberg (Grunwald).'),
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
    dict(name='Amselfeld (Kosovo)', jahr=1389, lng=21.10, lat=42.70, reiche=['osman', 'serbien'], note='Osmanischer Sieg über ein serbisches Heer.'),
    dict(name='Liegnitz', jahr=1241, lng=16.16, lat=51.21, reiche=['mongolen', 'polen'], note='Ein mongolisches Heer besiegt schlesische und polnische Ritter.'),
    dict(name='Mohi', jahr=1241, lng=20.97, lat=47.97, reiche=['mongolen', 'ungarn'], note='Die Mongolen vernichten das ungarische Heer König Belas IV.'),
    dict(name='Mariza (Tschernomen)', jahr=1371, lng=26.10, lat=41.85, reiche=['osman', 'serbien'], note='Die Osmanen besiegen ein serbisches Heer; Makedonien fällt an sie.'),
    dict(name='Tannenberg (Grunwald)', jahr=1410, lng=20.09, lat=53.49, reiche=['orden', 'polen', 'litauen'], note='Polen und Litauen besiegen den Deutschen Orden.'),
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
