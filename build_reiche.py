# -*- coding: utf-8 -*-
"""Erzeugt data/reiche.json: Provinzen/Regionen mit Erwerbs- und Verlustjahr,
Ereignisse (Texte für Karten), Schlachten, Orte und Nachbarreiche.

Alle Flächen sind grob von Hand gezeichnete Polygone (lon, lat), die an die
Küstenlinie aus data/land.json angepasst werden. Grenzen nur ungefähr!

Aufruf (im Ordner tafelbild):  python build_reiche.py
Benötigt: shapely (pip install shapely)
"""
import json, os, warnings
warnings.filterwarnings("ignore")
from shapely.geometry import shape, Polygon, box, mapping
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import set_precision

HERE = os.path.dirname(os.path.abspath(__file__))
LAND = shape(json.load(open(os.path.join(HERE, 'data/land.json')))['geometry']).buffer(0)

def P(*pts): return Polygon(pts).buffer(0)
def U(*gs): return unary_union(gs)

# ======================================================================
#  Reiche (Reihenfolge = Priorität bei Überlappung; Rom und Han zuerst)
# ======================================================================
META = {
 'rom':   dict(name='Römisches Reich', von=-300, bis=1453, farbe='#c4342c', zentrum=[18, 41], rahmen=[-13, 27.5, 46, 56.5], haupt=True,
              kurz='Vom Stadtstaat zum Weltreich rund um das Mittelmeer.'),
 'han':   dict(name='Han-Reich', von=-206, bis=220, farbe='#e09e0c', zentrum=[108, 34], rahmen=[72, 8, 134, 49], haupt=True,
              kurz='Chinesisches Kaiserreich, Gegenstück zu Rom im Osten Eurasiens.'),
 'karth': dict(name='Karthago', von=-300, bis=-146, farbe='#8e44ad', zentrum=[10, 36],
              kurz='Phönizische Seemacht in Nordafrika; Hauptgegner Roms in den Punischen Kriegen. 146 v. Chr. zerstört.'),
 'ptol':  dict(name='Ptolemäerreich', von=-300, bis=-30, farbe='#00a6c7', zentrum=[31, 28],
              kurz='Makedonische Könige in Ägypten (Hauptstadt Alexandria). Mit Kleopatra VII. endet es 30 v. Chr.'),
 'seleu': dict(name='Seleukidenreich', von=-300, bis=-63, farbe='#3f51b5', zentrum=[44, 34],
              kurz='Nachfolgereich Alexanders von Syrien bis Iran. Verliert den Osten an die Parther, der Rest wird 64/63 v. Chr. römisch.'),
 'parth': dict(name='Partherreich', von=-247, bis=224, farbe='#2e9d5b', zentrum=[52, 34],
              kurz='Iranisches Reich der Arsakiden; Roms großer Rivale im Osten und Zwischenhändler der Seidenstraße.'),
 'sasan': dict(name='Sasanidenreich', von=224, bis=651, farbe='#00897b', zentrum=[52, 33],
              kurz='Neupersisches Reich, löst 224 n. Chr. die Parther ab. Dauerkonflikt mit Rom bzw. Ostrom.'),
 'maurya':dict(name='Maurya-Reich', von=-300, bis=-185, farbe='#ef6c00', zentrum=[80, 24],
              kurz='Erstes indisches Großreich; unter Ashoka (um 268–232 v. Chr.) größte Ausdehnung.'),
 'kusch': dict(name='Kuschanreich', von=30, bis=375, farbe='#9e9d24', zentrum=[70, 34],
              kurz='Reich in Baktrien und Nordindien; Drehscheibe der Seidenstraße zwischen Rom, Parthern und Han.'),
 'gupta': dict(name='Gupta-Reich', von=320, bis=550, farbe='#d81b60', zentrum=[82, 25],
              kurz='Nordindisches Reich, „klassisches Zeitalter“ Indiens.'),
 'xiong': dict(name='Xiongnu', von=-209, bis=93, farbe='#78909c', zentrum=[104, 46],
              kurz='Reiterverband der Steppe nördlich von China; lange überlegen, ab 133 v. Chr. von den Han bekämpft.'),
 'xianb': dict(name='Xianbei', von=93, bis=235, farbe='#5c7cba', zentrum=[112, 46],
              kurz='Steppenvolk, das nach den Xiongnu die Mongolei beherrscht.'),
 'hunnen':dict(name='Hunnen', von=370, bis=469, farbe='#c08a5b', zentrum=[34, 47],
              kurz='Steppenvolk, das ab 375 n. Chr. die Völkerwanderung auslöst; unter Attila (434–453) auf dem Höhepunkt.'),
 # --- Europa (Kontext): Nachfolgestaaten Westroms. kontext=True: grau im Menü, keine Schriftrolle ---
 'franken': dict(name='Franken', von=257, bis=843, farbe='#7d8a5a', zentrum=[5.5, 50.9], kontext=True,
              kurz='Germanischer Verband am Niederrhein; Salfranken ab 358 in Toxandrien, ab etwa 457 Kleinkönigreich um Tournai (Childerich I.). Grundlage des späteren Frankenreichs.'),
 'alaman': dict(name='Alamannen', von=260, bis=506, farbe='#8f7a5c', zentrum=[8.6, 48.5], kontext=True,
              kurz='Germanischer Verband; besetzt nach 260 das aufgegebene Dekumatland, nach 455 auch Elsass und Nordschweiz.'),
 'westgot': dict(name='Westgotenreich', von=418, bis=711, farbe='#8a6f8f', zentrum=[0.5, 43.5], kontext=True,
              kurz='418 als Föderaten in Aquitanien angesiedelt (Hauptstadt Toulouse); unter Eurich (466–484) größtes Reich im Westen.'),
 'sueben': dict(name='Suebenreich', von=411, bis=585, farbe='#6f8a8a', zentrum=[-8, 42.5], kontext=True,
              kurz='Germanisches Königreich in Gallaecia (Nordwesten Hispaniens), Hauptort Bracara.'),
 'vandal': dict(name='Vandalenreich', von=429, bis=534, farbe='#5f7a99', zentrum=[9.5, 35.5], kontext=True,
              kurz='Die Vandalen setzen 429 nach Afrika über und erobern 439 Karthago; 455 plündern sie Rom.'),
 'burgund': dict(name='Burgunderreich', von=413, bis=534, farbe='#a07a6a', zentrum=[5.6, 46.2], kontext=True,
              kurz='413–436 Reich um Worms (Zerstörung durch hunnische Truppen), ab 443 in der Sapaudia um Genf neu angesiedelt.'),
 'odoaker': dict(name='Reich des Odoaker', von=476, bis=493, farbe='#7a7a92', zentrum=[12, 43], kontext=True,
              kurz='Odoaker setzt 476 den letzten weströmischen Kaiser ab und herrscht als König in Italien.'),
 'ostgot': dict(name='Ostgoten', von=456, bis=553, farbe='#6d7f6d', zentrum=[18, 46.5], kontext=True,
              kurz='Nach dem Zerfall des Hunnenreichs 456–473 als Föderaten in Pannonien; ab 493 Reich in Italien.'),
 'angels': dict(name='Angelsachsen', von=449, bis=927, farbe='#8c7f6a', zentrum=[0.3, 52.3], kontext=True,
              kurz='Nach dem Abzug Roms (410) siedeln Angeln, Sachsen und Jüten im Osten Britanniens; Kleinkönigreiche entstehen.'),
}
ORDER = list(META.keys())
# Bei Überlappung gewinnt das frühere Reich. Die Nachfolgestaaten stehen VOR Rom: Sie nehmen Westrom die Gebiete ab,
# auch wenn das formale Ende einer weströmischen Provinz später datiert ist.
KONTEXT = ['sueben', 'vandal', 'burgund', 'odoaker', 'ostgot', 'angels', 'franken', 'alaman', 'westgot']   # Westgoten zuletzt: ihre großen Flächen füllen nur, was frei ist
PRIO = KONTEXT + [k for k in ORDER if k not in KONTEXT]

# ======================================================================
#  Geometrien
# ======================================================================
# --- Italien / Rom ---
italia_all = P((9,42),(9,43.8),(12.4,44.4),(13.4,44),(19,41.5),(19,37.5),(9,37.5)).difference(box(8,38.8,9.8,43.1)).difference(box(12,36,15.7,38.35))
italia_c   = italia_all.intersection(P((8,45),(19,45),(19,42.2),(15.6,41.4),(13.9,40.9),(8,40.9)))
italia_s   = italia_all.difference(italia_c)
sicilia    = box(12,36.5,15.7,38.35)
sicilia_w  = box(12,36.5,13.75,38.35)
sardinia   = box(8,38.8,9.8,43.1)
cisalpina  = P((6.5,44.2),(7.2,44.1),(7.6,45.9),(10,46.4),(13.8,46.5),(13.8,45.5),(12.4,44.4),(9,43.8),(8.5,44.3))
hisp_early = P((-7.5,36),(-7.5,38.5),(-4,39),(-2,41),(0,42.2),(3.3,42.5),(3.3,36))
hisp_mid   = P((-9.8,36),(-9.8,40.5),(-6.5,41.2),(-3,41.6),(-1,42.8),(3.3,42.5),(3.3,36))
hisp_all   = box(-10,35.9,3.4,44.2)
karth_hisp = P((-7.5,36),(-7.5,38.5),(-4,39),(-1.5,40.0),(0.9,40.8),(0.9,38.5),(-2,36.6))
africa     = P((8.2,37.4),(11.5,37.4),(11.5,34.8),(8.2,34.8))
karth_core = P((8.2,37.4),(11.5,37.4),(11.2,35.2),(10.5,34),(8.2,34.8))
africa_ext = P((5.5,37.1),(11.5,37.4),(11.5,33.5),(15,32.3),(19.9,31),(19.9,30.2),(14,30.8),(11,31.5),(9.5,32.5),(8.5,33.7),(5.5,34.3))
karth_lib  = P((11.2,35.2),(11.5,33.5),(15,32.3),(19.9,30.6),(19.9,30.2),(14,30.8),(11,31.5),(10.5,34))
karth_maur = P((-6,35.9),(-1,35.6),(3,36.9),(8.2,37.4),(8.2,36.3),(3,36.2),(-1,35.1),(-6,35.4))
mauretania = P((-10,31.5),(-10,36),(-5.5,36),(-1,35.6),(3,36.9),(5.5,37.1),(5.5,34.3),(3,35),(-1,34),(-5,33.8),(-7.5,33))
illyria    = P((14.5,45.3),(16,45),(19.6,42.4),(19.8,40.4),(19.2,40.4),(18.5,42.3),(15.5,44),(13.8,45.6))
greece     = P((19.3,42.2),(23.5,42.2),(23.5,40.6),(26,40.6),(24.5,38.3),(23,36.2),(21.5,36.3),(19.3,39.5))
asia       = U(P((26.1,40.3),(30.7,40.2),(30.7,37.2),(27.3,36.4),(26,38)), box(27.0,40.2,29.1,40.75))   # mit Marmara-Südküste
narb       = P((3.3,42.4),(3.3,43.6),(4.5,45.2),(6.5,45.2),(7.2,43.7))
cyrenaica  = P((19.9,30.3),(19.9,32.9),(23,33),(25,32),(25,30.3))
creta      = box(23.4,34.8,26.4,35.7)
cyprus     = box(32.2,34.5,34.7,35.8)
bithynia   = P((28.9,41.3),(32,41.9),(32,40.2),(30.7,40.2),(29,40.3))
pontus     = P((32,41.9),(36,41.8),(37.5,41.2),(37.5,40.3),(33,40.2),(32,40.2))
cilicia    = P((32.5,36.1),(36.2,36.6),(36.0,37.3),(33.5,37.3),(32.5,36.6))
syria      = P((35.7,36.9),(36.7,37.0),(37.9,36.9),(38.3,35.8),(37.2,34.5),(36.6,33.2),(35.0,33.0),(35.6,35.0))
koile      = P((34.2,31.3),(35.0,33.0),(36.6,33.2),(36.3,31.5),(35.4,29.6),(34.9,29.5))
gallia     = P((-5,47.5),(-5,49),(2,51.3),(4.6,52.3),(6.9,51),(7.5,50.4),(8.3,50),(7.8,48.6),(7.6,47.6),(6.9,46.4),(6.5,45.2),(4.5,45.2),(3.3,43.6),(-1.8,43.4),(-1.2,46))
aegyptus   = P((24.9,31.8),(34.3,31.4),(34.95,29.5),(34.75,28.6),(34.3,27.8),(35.7,23.9),(25,23.9))   # mit Süd-Sinai
galatia    = P((30.7,40.2),(33,40.2),(35.5,40.3),(35.5,38.5),(33.5,37.3),(32.5,36.6),(30.7,37.2))   # mit Pisidien/Lykaonien
lycia      = P((27.3,36.4),(30.7,37.2),(32.5,36.6),(32.5,36.1),(28,36.2))
cappadocia = P((35.5,40.3),(37.5,40.3),(39.5,39.5),(38.7,38.6),(38.2,37),(36.0,37.3),(33.5,37.3),(35.5,38.5))
pontus_o   = P((37.5,41.2),(40,41),(41.8,41.5),(42,40.5),(41,39.5),(39.5,39.5),(37.5,40.3))
raetia     = P((7.6,47.6),(8.4,47.6),(9,48.0),(10,48.4),(10.9,48.3),(12.1,48.9),(13.6,48.4),(16,48.3),(16,46.7),(14.5,45.9),(13.8,46.5),(10.4,46.9),(9.5,47.6))
pannonia   = P((16,46.7),(16,48.3),(17,48.2),(19,47.7),(19.1,46),(19.2,45.3),(20.3,44.9),(19.5,43.5),(20,42.3),(19.6,42.4),(16,45),(14.5,45.9))
moesia     = P((20.3,44.9),(22.4,44.75),(23,43.95),(24.9,43.8),(26,43.95),(27.3,44.2),(28,44.35),(28.9,44.7),(29.7,45.2),(29.6,42.8),(23.5,42.8),(23.5,42.0),(19.6,42.0),(19.5,43.5))   # mit Dardanien
thracia    = P((23.5,42.8),(29.6,42.8),(29.6,41.0),(26.5,40.3),(23.5,40.6))
judaea     = P((34.2,31.3),(35.0,33.0),(35.9,33.0),(35.6,31.2),(35.4,29.8),(34.9,29.5))
arabia     = P((34.9,29.4),(35.6,31.2),(35.9,33.0),(36.6,33.2),(37.2,33.3),(38.5,33.4),(38,32),(37,30),(36.5,27),(35.5,27.6),(34.8,28.2))   # mit Küste Midians
dacia      = P((21.4,45.5),(22.4,44.75),(23,43.95),(24.9,43.8),(26,43.95),(26.8,45.3),(26.5,48),(22.2,48),(21.4,47))
dacia_mm   = P((21.4,45.5),(21.1,44.9),(21.6,44.65),(22.4,44.75),(23,43.95),(24.9,43.8),(26.8,45.3),(26.3,46.5),(25.8,47.5),(24.5,47.7),(23.5,47.6),(22.2,46.8),(21.5,45.2))
agri_dec   = P((7.6,47.6),(7.8,48.6),(8.3,50.0),(8.5,50.2),(9,49.5),(9.6,48.9),(10.6,48.7),(11.6,48.9),(12.1,49.05),(12.1,48.9),(10.9,48.3),(10.0,48.4),(9.0,48.0),(8.5,47.9),(8.4,47.6))
brit_s     = P((-6,49.8),(-4.5,51.5),(-3.2,52.2),(-3.0,53.4),(0.5,53.6),(2,53),(2,49.8))
# Alpen: Lückenfüller (frühere Regionen haben Vorrang, hier bleibt nur, was sonst frei wäre)
helvetia   = box(6.0,46.15,9.5,47.55)                                   # Schweizer Mittelland (Helvetier)
alpen_w    = box(5.5,43.6,11.0,47.55)                                   # West- und Zentralalpen
alpen_o    = U(box(11.0,45.6,14.6,47.3), box(13.5,45.2,16.0,46.8))       # Ostalpen, Julische Alpen
commagene  = P((36.3,36.9),(37.9,36.9),(39.0,37.0),(39.2,38.0),(39.0,38.6),(38.2,38.4),(37.0,37.6),(36.3,37.4))   # mit Melitene
palmyrene  = P((36.6,33.2),(37.2,34.5),(38.3,35.8),(38.6,35.0),(38.6,34.0),(38.5,33.4),(37.2,33.3))
brit_n     = P((-6,49.8),(-6,53.5),(-3.3,55),(-1.5,55),(2,55),(2,53),(0.5,53.6),(-3.0,53.4),(-3.2,52.2),(-4.5,51.5))

# --- Osten / Iran ---
mesopot    = P((38.3,35.8),(40.2,35.4),(38.7,37.5),(40,37.6),(43,37.4),(45.5,35.2),(47.8,31.5),(48.6,30.0),(47.5,29.5),(46.5,30.0),(44,31.2),(41.5,32.8),(40.2,34.3),(38.6,35))
media      = P((45.5,35.2),(43,37.4),(44.3,39.4),(48,39.5),(50,37.3),(53,37),(53,35.5),(51,33.5),(48.5,33.5),(46.5,34))
persis     = P((47.8,31.5),(46.5,34),(48.5,33.5),(51,33.5),(53,35.5),(56,34.5),(58,30),(57.5,27),(54,26.5),(51,27.8),(48.6,30.0))
parthyene  = P((53,37),(53.5,38.5),(56,38.3),(58,37.8),(61,36.6),(61,34.5),(56,34.5),(53,35.5))
ostiran    = P((61,36.6),(61.3,37.9),(62.3,38.1),(62.5,37.8),   # mit Merw
                 (64.5,37.4),(64.5,34),(63,30),(61.5,29),(58,30),(56,34.5),(61,34.5))
baktria    = P((64.5,37.4),(66,38.4),(68.5,38.6),(70.5,38.3),(71.5,36.8),(70.2,35.5),(67,35),(64.5,34))
armenia    = P((41.8,41.5),(43.5,41.2),(46.5,41.5),(48,39.5),(44.3,39.4),(43,37.4),(40,37.6),(39.5,39.5),(41,39.5),(42,40.5))
anatol_in  = P((30.7,40.2),(33,40.2),(35.5,40.3),(35.5,38.5),(33.5,37.3),(32.5,36.6),(30.7,37.2),(28.5,37.6),(28,39.5))

# --- Indien / Zentralasien ---
maurya_n   = P((67,24),(68,30),(71,33.5),(74,35),(77,33),(80,30),(84,27.5),(88,26.6),(92,25.5),(89,22),(86,20.5),(82,21.5),(78,21),(73,21.5),(70,22.5))
maurya_s   = P((73,21.5),(78,21),(82,21.5),(81,17.5),(80,15.5),(77.5,13.5),(75,13.5),(73.5,16))
kalinga    = P((81,17.5),(82,21.5),(86,20.5),(87.5,21.5),(85,22.5),(84,18))
arachosia  = P((62,30),(62,33),(65,35.5),(70.2,35.5),(71,33.5),(68,30),(66,28))
gandhara   = P((67,35),(70.2,35.5),(71.5,36.8),(74,35.8),(75,33.5),(74,32),(71,31.5),(69.5,31),(68,33))
kusch_ind  = P((71,31.5),(74,32),(77,31.5),(80,29),(83.5,26.5),(82,24.5),(78,25),(74,26),(71,28))
gupta_core = P((77,30),(80,30),(84,27.5),(88,26.6),(89,24),(88,22),(84,23),(80,23),(77,25),(75,26.5))
gupta_w    = P((69,22.5),(70,24),(72,26.5),(75,26.5),(77,25),(80,23),(78,21.5),(74,21),(72,20.5))

# --- China / Steppe ---
han_early  = P((104,41),(109,41),(113,39.2),(118,38),(122.7,37.3),(122,34.5),(122,31),(122,29.5),(119.5,28.5),(116.5,26),(113,25.2),(110,24.8),(107,25.5),(105,25),(104,27),(102,28),(101,29),(102.5,32),(104,34.5),(102.5,36),(102,38.5))
han_core   = P((127,39.3),(124.5,41),(122,43.2),(118,42.7),(113,42),(108,41.7),(103,41.5),(98,41.2),(94,40.6),(93.5,38.8),(96,36.5),(98.8,34.8),(100.5,32.5),(100.2,28.5),(98.7,25),(100.8,21.8),(104,21.5),(104.5,18),(106.5,16.3),(108.3,15.8),(112,16),(116,20),(118.8,22),(119.8,25.6),(122.8,29.5),(122.8,31.5),(123,34),(122.9,37.5),(122.5,39),(124,39.5),(125.0,38.5),(126.9,38.6))   # mit Lelang (Pjöngjang)
han_rest   = han_core.difference(han_early)
han_yan    = han_rest.intersection(box(109,37,121.5,44))
han_korea  = han_rest.intersection(box(121.5,37,131,44))
han_ordos  = han_rest.intersection(box(103.9,37,109,43))
han_hexi   = U(han_rest.intersection(box(90,34,103.9,43)), box(92.8,39.3,94.6,40.8))   # mit Dunhuang
han_longxi = han_rest.intersection(box(96,30,104.2,34))                 # Longxi und Westgrenze
han_minyue = han_rest.intersection(P((116.3,25.0),(116.5,26),(119.5,28.5),(121.6,29.3),(121.2,27.5),(120,25),(117.3,23.5),(116.8,24.4)))
han_dian   = han_rest.intersection(box(96,20,104.2,30))
han_nanyue = han_rest.intersection(box(104.2,14,125,27))
tarim_full = P((74,40),(80,42.2),(85,42),(90,42.5),(93.7,40.8),(93.5,38.8),(91,37.5),(87,36.5),(80,35.5),(77,36.5),(74.5,38))
tarim_east = P((84,41.5),(90,42.4),(93.7,40.8),(93.5,38.8),(91,37.5),(87,36.8),(84,38.5))
mongolia   = P((88,47),(90,50.5),(98,52),(108,52),(118,50),(122,47),(119,43.5),(113,42),(108,41.7),(103,41.5),(98,41.2),(94,42.5),(90,44))
mong_ost   = P((112,42),(119,43.5),(122,47),(126,47.5),(127,44),(124.5,41),(122,43.2),(118,42.7))
steppe_w   = P((28,46.5),(30,48.5),(40,50.5),(48,50),(50,47),(47,44.5),(40,45.5),(36,45.3),(33,46),(30,45.8))
# --- Europa (Kontext) ---
wg_aquit   = P((-1.8,43.4),(-1.4,44.5),(-1.2,46.2),(0.3,46.6),(1.5,45.9),(2.2,44.6),(2.3,43.5),(1.5,42.8),(-0.5,42.9))
wg_sept    = P((1.5,42.8),(2.3,43.5),(3.3,43.6),(4.5,43.7),(3.3,42.4))
wg_gall    = P((-1.2,46.2),(-2.2,47.3),(0.5,47.5),(2.9,47.4),(3.5,46.3),(3.9,45.2),(4.2,44.3),(3.3,43.6),(2.3,43.5),(2.2,44.6),(1.5,45.9),(0.3,46.6))
wg_prov    = P((4.5,43.7),(4.2,44.3),(5.5,44.5),(6.9,43.9),(6.3,43.1),(4.8,43.3))
sueb_core  = P((-9.8,40.5),(-9.8,43.8),(-7,43.8),(-4.5,43.4),(-5.5,42),(-6.5,41.2))
sueb_ext   = P((-9.8,36),(-9.8,40.5),(-6.5,41.2),(-5,39.5),(-4,37.5),(-5,36))
balearen   = box(1.2,38.6,4.4,40.1)
burg_worms = box(7.8,49.2,8.6,50.0)
burg_sap   = P((5.6,45.3),(5.8,46.6),(6.9,46.6),(7.1,45.8),(6.6,45.2))
burg_rhone = P((4.2,44.3),(4.0,45.8),(4.5,47.0),(5.5,47.6),(6.9,47.5),(7.1,46.5),(6.6,45.2),(5.5,44.5))
fr_rechts  = P((6.0,51.4),(5.9,51.8),(6.5,52.5),(8.5,52.3),(8.8,51.0),(7.6,50.4),(7.2,51.4))
fr_toxand  = P((4.2,51.0),(4.2,51.7),(5.9,51.8),(6.0,51.0))
fr_tournai = P((2.5,50.0),(2.5,51.0),(4.2,51.0),(4.6,50.3),(3.8,49.9))
fr_koeln   = P((6.0,50.3),(6.0,51.4),(7.2,51.4),(7.6,50.4),(7.0,49.9))
al_elsass  = P((7.0,47.4),(7.2,48.9),(8.2,48.9),(7.8,48.6),(7.6,47.6),(9.5,47.6),(9.5,47.3),(7.6,47.3))
angl_ost   = P((-0.5,50.8),(-1.0,52.0),(-0.6,53.7),(0.3,53.6),(2,52.9),(1.9,51.1),(1.4,50.9))
hung_plain = P((19,47.7),(19,48.6),(22,48.5),(24.5,47.7),(26,46.5),(26.8,45.3),(24,44.5),(22.4,44.75),(21.4,45.5),(20.3,44.9),(19.2,45.3),(19.1,46))

# ======================================================================
#  Regionen: (reich, name, geom, von, bis, art, seite[nur Rom: w/o])
#  bis = Jahr des Verlusts (exklusiv), None = bis Reichsende
# ======================================================================
R = []
def reg(reich, name, g, von, bis=None, art='kern', seite=None):
    R.append(dict(reich=reich, name=name, g=g, von=von, bis=bis, art=art, seite=seite))

# ---- Rom (W = Westrom, O = Ostrom ab 395) ----
reg('rom','Mittelitalien',italia_c,-300,476,seite='w')
reg('rom','Süditalien (nach dem Krieg gegen Pyrrhos)',italia_s,-272,476,seite='w')
reg('rom','Sicilia',sicilia,-241,476,seite='w')
reg('rom','Sardinia et Corsica',sardinia,-238,476,seite='w')
reg('rom','Gallia Cisalpina (Poebene)',cisalpina,-222,476,seite='w')
reg('rom','Hispania (Küste)',hisp_early,-206,456,seite='w')
reg('rom','Illyricum (Küste)',illyria,-167,476,seite='w')
reg('rom','Macedonia und Achaia',greece,-146,seite='o')
reg('rom','Africa',africa,-146,439,seite='w')
reg('rom','Hispania (Inneres)',hisp_mid,-133,456,seite='w')
reg('rom','Asia (Erbe von Pergamon)',asia,-133,seite='o')
reg('rom','Gallia Narbonensis',narb,-121,462,seite='w')
reg('rom','Cyrenaica',cyrenaica,-74,seite='o')
reg('rom','Bithynia',bithynia,-74,seite='o')
reg('rom','Creta',creta,-67,seite='o')
reg('rom','Pontus',pontus,-64,seite='o')
reg('rom','Cilicia',cilicia,-64,seite='o')
reg('rom','Syria',syria,-64,seite='o')
reg('rom','Cyprus',cyprus,-58,seite='o')
reg('rom','Gallia (Eroberung durch Caesar)',gallia,-50,460,seite='w')
reg('rom','Africa Nova und Tripolitanien',africa_ext,-46,439,seite='w')
reg('rom','Aegyptus',aegyptus,-30,seite='o')
reg('rom','Galatia',galatia,-25,seite='o')
reg('rom','Hispania (Nordwesten)',hisp_all,-19,456,seite='w')
reg('rom','Raetia und Noricum',raetia,-15,476,seite='w')
reg('rom','Helvetien (Schweizer Mittelland)',helvetia,-50,455,seite='w')
reg('rom','Alpenprovinzen (Westalpen)',alpen_w,-15,476,seite='w')
reg('rom','Ostalpen und Julische Alpen',alpen_o,-15,476,seite='w')
reg('rom','Iudaea',judaea,6,seite='o')
reg('rom','Moesia',moesia,6,seite='o')
reg('rom','Pannonia und Dalmatia',pannonia,9,433,seite='w')
reg('rom','Cappadocia',cappadocia,17,seite='o')
reg('rom','Palmyrene (zu Syria)',palmyrene,17,seite='o')
reg('rom','Mauretania',mauretania,42,429,seite='w')
reg('rom','Britannia (Süden)',brit_s,43,410,seite='w')
reg('rom','Lycia et Pamphylia',lycia,43,seite='o')
reg('rom','Thracia',thracia,46,seite='o')
reg('rom','Pontus Polemoniacus',pontus_o,64,seite='o')
reg('rom','Commagene (zu Syria)',commagene,72,seite='o')
reg('rom','Agri decumates',agri_dec,74,260,seite='w')
reg('rom','Britannia (Norden und Wales)',brit_n,78,410,seite='w')
reg('rom','Dacia',dacia_mm,106,271,seite='o')
reg('rom','Arabia Petraea',arabia,106,seite='o')

# ---- Han ----
reg('han','Kernland der Han',han_early,-206)
reg('han','Yan und Liaodong',han_yan,-202)
reg('han','Ordos (von den Xiongnu zurückerobert)',han_ordos,-127)
reg('han','Longxi und Westgrenze',han_longxi,-206)
reg('han','Hexi-Korridor',han_hexi,-121)
reg('han','Minyue (Fujian)',han_minyue,-110)
reg('han','Nanyue (Süden)',han_nanyue,-111)
reg('han','Dian (Yunnan)',han_dian,-109)
reg('han','Lelang-Kommandanturen (Korea)',han_korea,-108)
reg('han','Westliche Regionen (Osten)',tarim_east,-101,16,art='einfluss')
reg('han','Westliche Regionen (Westen)',tarim_full.difference(tarim_east),-60,16,art='einfluss')
reg('han','Westliche Regionen (Osten)',tarim_east,73,107,art='einfluss')
reg('han','Westliche Regionen (Westen)',tarim_full.difference(tarim_east),91,107,art='einfluss')
reg('han','Westliche Regionen (Osten)',tarim_east,123,150,art='einfluss')

# ---- Karthago ----
reg('karth','Kernland um Karthago',karth_core,-300)
reg('karth','West-Sizilien',sicilia_w,-300,-241)
reg('karth','Sardinien und Korsika',sardinia,-300,-238)
reg('karth','Libysche Küste',karth_lib,-300,-201)
reg('karth','Küste Mauretaniens',karth_maur,-300,-201)
reg('karth','Hispanien (Barkiden)',karth_hisp,-237,-206)

# ---- Ptolemäer ----
reg('ptol','Ägypten',aegyptus,-300)
reg('ptol','Kyrenaika',cyrenaica,-300,-96)
reg('ptol','Koilesyrien',koile,-300,-200)
reg('ptol','Zypern',cyprus,-300,-58)

# ---- Seleukiden ----
reg('seleu','Syrien und Kilikien',U(syria,cilicia),-300)
reg('seleu','Koilesyrien',koile,-200,-140)
reg('seleu','Mesopotamien',mesopot,-300,-141)
reg('seleu','Medien',media,-300,-148)
reg('seleu','Persis',persis,-300,-141)
reg('seleu','Inneres Kleinasien',anatol_in,-281,-188)
reg('seleu','Parthyene und Hyrkanien',parthyene,-300,-247)
reg('seleu','Ost-Iran',ostiran,-300,-210)
reg('seleu','Baktrien',baktria,-300,-250)

# ---- Parther ----
reg('parth','Parthyene (Stammland)',parthyene,-247)
reg('parth','Ost-Iran',ostiran,-210)
reg('parth','Medien',media,-148)
reg('parth','Mesopotamien',mesopot,-141)
reg('parth','Persis',persis,-141)
reg('parth','Armenien (Einfluss)',armenia,-66,art='einfluss')

# ---- Sasaniden ----
for nm, g in [('Mesopotamien',mesopot),('Medien',media),('Persis (Stammland)',persis),('Parthyene',parthyene),('Ost-Iran',ostiran)]:
    reg('sasan', nm, g, 224)
reg('sasan','Armenien (Einfluss)',armenia,252,art='einfluss')
reg('sasan','Kuschanschahr (Baktrien)',baktria,240)

# ---- Maurya ----
reg('maurya','Nordindien (Ganges)',maurya_n,-300)
reg('maurya','Dekkan',maurya_s,-300)
reg('maurya','Arachosien und Gandhara',arachosia,-300,-190)
reg('maurya','Kalinga (Eroberung durch Ashoka)',kalinga,-261)

# ---- Kuschan ----
reg('kusch','Baktrien',baktria,30,240)
reg('kusch','Gandhara',gandhara,30)
reg('kusch','Nordindien (Mathura)',kusch_ind,80,240)

# ---- Gupta ----
reg('gupta','Gangesebene',gupta_core,320)
reg('gupta','Malwa und Gujarat',gupta_w,395)

# ---- Xiongnu / Xianbei ----
reg('xiong','Mongolische Steppe',mongolia,-209)
reg('xiong','Ordos',han_ordos,-209,-127)
reg('xiong','Hexi-Korridor',han_hexi,-177,-121)
reg('xiong','Tarimbecken (Tributvölker)',tarim_full,-177,-60,art='einfluss')
reg('xianb','Östliche Steppe',mong_ost,93)
reg('xianb','Mongolische Steppe',mongolia,93)

# ---- Hunnen ----
reg('hunnen','Pontische Steppe',steppe_w,370)
reg('hunnen','Ungarische Tiefebene',hung_plain,400,455)
reg('hunnen','Pannonien (von Westrom abgetreten)',pannonia.intersection(box(16,44,20.5,48.5)),433,455)

# ---- Europa (Kontext): Nachfolgestaaten ----
reg('franken','Siedlungsgebiet rechts des Rheins',fr_rechts,257)
reg('franken','Toxandrien (Salfranken als Föderaten)',fr_toxand,358)
reg('franken','Rheinfranken um Köln',fr_koeln,457)
reg('franken','Tournai und Cambrai (Childerich I.)',fr_tournai,457)
reg('alaman','Dekumatland',agri_dec,260)
reg('alaman','Elsass und Nordschweiz',al_elsass,455)
reg('westgot','Aquitanien (Föderatenvertrag)',wg_aquit,418)
reg('westgot','Septimanien (Narbonne)',wg_sept,462)
reg('westgot','Gallien bis zur Loire',wg_gall,470)
reg('westgot','Hispanien (Eroberung unter Eurich)',hisp_all,472)
reg('westgot','Provence (Arles, Marseille)',wg_prov,476)
reg('sueben','Gallaecia',sueb_core,411)
reg('sueben','Lusitanien und Baetica',sueb_ext,439,456)
reg('vandal','Mauretanien',mauretania,429)
reg('vandal','Africa (Karthago)',U(africa,africa_ext),439)
reg('vandal','Sardinien, Korsika, Balearen',U(sardinia,balearen),455)
reg('burgund','Reich um Worms',burg_worms,413,436)
reg('burgund','Sapaudia (Genf)',burg_sap,443)
reg('burgund','Rhônetal und Lyon',burg_rhone,470)
reg('odoaker','Italien',U(italia_c,italia_s,cisalpina,sicilia),476)
reg('odoaker','Dalmatien',illyria,480)
reg('ostgot','Pannonien (Föderaten)',pannonia.intersection(box(16,44,20.5,48.5)),456,473)
reg('angels','Ostengland (Siedlungsgebiet)',angl_ost,449)

# ======================================================================
#  Überlappungen zeitabhängig auflösen
# ======================================================================
def clipland(g):
    return set_precision(g.intersection(LAND).buffer(0), 0.001)

def endyear(r): return r['bis'] if r['bis'] is not None else META[r['reich']]['bis']

pieces = []   # dicts mit g, von, bis
for r in sorted(R, key=lambda r: PRIO.index(r['reich'])):  # stabile Sortierung: Reihenfolge innerhalb eines Reichs bleibt
    g0 = clipland(r['g'])
    if g0.is_empty: print('LEER', r['reich'], r['name']); continue
    a0, b0 = max(r['von'], META[r['reich']]['von']), endyear(r)
    if a0 >= b0: continue
    over = [p for p in pieces if p['von'] < b0 and p['bis'] > a0 and p['g'].intersects(g0) and p['g'].intersection(g0).area > 1e-4]
    cuts = sorted({a0, b0} | {y for p in over for y in (p['von'], p['bis']) if a0 < y < b0})
    segs = []
    for a, b in zip(cuts, cuts[1:]):
        act = tuple(i for i, p in enumerate(over) if p['von'] <= a and p['bis'] >= b)
        if segs and segs[-1][2] == act: segs[-1][1] = b
        else: segs.append([a, b, act])
    for a, b, act in segs:
        g = g0
        if act: g = g0.difference(unary_union([over[i]['g'] for i in act])).buffer(0)
        g = set_precision(g, 0.001)
        if g.is_empty or g.area < 0.02: continue
        pieces.append(dict(r, g=g, von=a, bis=b))

def rnd(o):
    if isinstance(o, (list, tuple)): return [rnd(x) for x in o]
    if isinstance(o, float): return round(o, 3)
    return o

def outgeom(g):
    polys = [orient(p, sign=-1.0) for p in (g.geoms if hasattr(g, 'geoms') else [g]) if p.geom_type == 'Polygon' and p.area > 0.004]
    if not polys: return None
    m = mapping(polys[0] if len(polys) == 1 else unary_union(polys))
    if m['type'] == 'MultiPolygon':
        m = {'type': 'MultiPolygon', 'coordinates': [mapping(orient(Polygon(c[0], c[1:]), sign=-1.0))['coordinates'] for c in m['coordinates']]}
    elif m['type'] == 'Polygon':
        m = mapping(orient(Polygon(m['coordinates'][0], m['coordinates'][1:]), sign=-1.0))
    return {'type': m['type'], 'coordinates': rnd(m['coordinates'])}

feats = []
for i, p in enumerate(pieces):
    gm = outgeom(p['g'])
    if not gm: continue
    pr = {'id': i, 'reich': p['reich'], 'name': p['name'], 'von': p['von'], 'bis': p['bis'], 'art': p['art']}
    if p['seite']: pr['seite'] = p['seite']
    feats.append({'type': 'Feature', 'properties': pr, 'geometry': gm})

# ======================================================================
#  Ereignisse (Texte für Infokarten + Marker auf der Zeitleiste)
# ======================================================================
E = [
 ('rom',-300,'Rom erobert Mittelitalien','Nach den Samnitenkriegen beherrscht Rom große Teile Mittelitaliens. Bündnisse mit unterworfenen Städten sichern die Macht.'),
 ('rom',-272,'Rom beherrscht Italien','Nach dem Sieg über Pyrrhos (275 v. Chr.) fällt 272 v. Chr. Tarent. Rom kontrolliert die Halbinsel südlich der Poebene.'),
 ('rom',-241,'Erster Punischer Krieg gewonnen','Sizilien wird erste römische Provinz (241 v. Chr.), kurz darauf Sardinien und Korsika (238 v. Chr.).'),
 ('rom',-218,'Zweiter Punischer Krieg','Hannibal zieht mit Elefanten über die Alpen und besiegt Rom bei Cannae (216 v. Chr.). Erst 202 v. Chr. siegt Scipio bei Zama.'),
 ('rom',-146,'Karthago und Korinth zerstört','Africa, Makedonien und Achaia werden römisch. Rom ist Vormacht im Mittelmeer.'),
 ('rom',-133,'Erbe von Pergamon','Attalos III. vererbt sein Reich an Rom (Provinz Asia). Numantia in Hispanien fällt. In Rom beginnen die Reformen der Gracchen.'),
 ('rom',-64,'Pompeius ordnet den Osten','Syrien, Pontus und Kilikien werden Provinzen. Das Seleukidenreich ist erloschen.'),
 ('rom',-50,'Caesar erobert Gallien','Nach dem Gallischen Krieg (58–50 v. Chr.) reicht Rom bis an den Rhein. 44 v. Chr. wird Caesar ermordet.'),
 ('rom',-30,'Ägypten wird römisch','Nach dem Sieg bei Actium (31 v. Chr.) und dem Tod Kleopatras fällt Ägypten an Rom. 27 v. Chr. wird Octavian zu Augustus.'),
 ('rom',9,'Augustus sichert die Grenzen','Donauprovinzen entstehen. Nach der Varusschlacht (9 n. Chr.) bleibt der Rhein die Grenze in Germanien.'),
 ('rom',43,'Eroberung Britanniens','Unter Kaiser Claudius beginnt 43 n. Chr. die Eroberung Britanniens. Thrakien und Mauretanien werden Provinzen.'),
 ('rom',117,'Größte Ausdehnung unter Trajan','Dakien und Arabia sind Provinzen (106 n. Chr.). Mesopotamien wurde 116/117 nur kurz erobert und ist nicht eingezeichnet.'),
 ('rom',260,'Reichskrise im 3. Jahrhundert','Kaiser Valerian gerät in persische Gefangenschaft. Das Dekumatland wird aufgegeben, um 271 auch Dakien.'),
 ('rom',395,'Reichsteilung in West- und Ostrom','Nach dem Tod Theodosius’ I. erben seine Söhne das Reich: Honorius den Westen (Westrom), Arcadius den Osten (Ostrom, Hauptstadt Konstantinopel).'),
 ('rom',410,'Plünderung Roms','Westgoten unter Alarich plündern Rom. Britannien wird aufgegeben.'),
 ('rom',439,'Vandalen erobern Karthago','Westrom verliert Nordafrika, seine reichste Provinz. Hispanien und Gallien gehen in den folgenden Jahrzehnten an germanische Reiche.'),
 ('rom',476,'Ende Westroms','Odoaker setzt den letzten weströmischen Kaiser Romulus Augustulus ab. Ostrom (Byzanz) besteht bis 1453 weiter.'),
 ('han',-206,'Anfänge der Han-Dynastie','Liu Bang gründet die Dynastie (traditionell 206/202 v. Chr.). Im Norden sind die Xiongnu überlegen; 200 v. Chr. wird der Kaiser bei Baideng eingeschlossen.'),
 ('han',-127,'Gegenangriff auf die Xiongnu','Kaiser Wu (141–87 v. Chr.) lässt die Xiongnu angreifen. Das Ordos-Gebiet und 121 v. Chr. der Hexi-Korridor werden erobert.'),
 ('han',-111,'Expansion unter Kaiser Wu','Nanyue im Süden (111 v. Chr.), Dian (109 v. Chr.) und Nordkorea (Lelang, 108 v. Chr.) werden eingegliedert.'),
 ('han',-60,'Protektorat der Westlichen Regionen','Die Han kontrollieren die Oasenstädte im Tarimbecken – den Weg der Seidenstraße nach Westen.'),
 ('han',9,'Xin-Dynastie des Wang Mang','Wang Mang reißt die Macht an sich (9–23 n. Chr.). Die Westlichen Regionen gehen verloren. 25 n. Chr. stellt Guangwu die Han wieder her (Östliche Han, Hauptstadt Luoyang).'),
 ('han',91,'Östliche Han-Dynastie','Ban Chao stellt 91 n. Chr. den Einfluss in den Westlichen Regionen wieder her. 97 n. Chr. schickt er Gan Ying nach Westen.'),
 ('han',107,'Rückzug aus dem Westen','Aufstände führen zum Abzug aus dem Tarimbecken; Ban Yong stellt den Einfluss ab 123 n. Chr. teilweise wieder her.'),
 ('han',184,'Aufstand der Gelben Turbane','Bauernaufstände und Machtkämpfe der Generäle zerrütten das Reich. 220 n. Chr. endet die Han-Dynastie; es folgen die Drei Reiche.'),
]
events = [{'reich': r, 'jahr': j, 'label': ('um ' if True else '') + (f'{-j} v. Chr.' if j < 0 else f'{j} n. Chr.'), 'titel': t, 'note': n} for r, j, t, n in E]

# ======================================================================
#  Schlachten
# ======================================================================
S = [
 ('Cannae',-216,16.13,41.31,['rom','karth'],'Hannibal vernichtet ein großes römisches Heer.'),
 ('Raphia',-217,34.25,31.29,['ptol','seleu'],'Ptolemaios IV. besiegt Antiochos III.'),
 ('Zama',-202,9.30,36.15,['rom','karth'],'Scipio besiegt Hannibal; Ende des Zweiten Punischen Krieges.'),
 ('Baideng',-200,113.3,40.1,['han','xiong'],'Die Xiongnu kesseln Kaiser Gaozu ein; die Han zahlen danach Tribut.'),
 ('Kynoskephalai',-197,22.55,39.40,['rom'],'Rom besiegt Makedonien.'),
 ('Magnesia',-190,27.53,38.62,['rom','seleu'],'Rom besiegt Antiochos III.; die Seleukiden verlieren Kleinasien.'),
 ('Pydna',-168,22.60,40.40,['rom'],'Ende des makedonischen Königtums.'),
 ('Karthago',-146,10.32,36.85,['rom','karth'],'Rom zerstört Karthago nach dreijähriger Belagerung.'),
 ('Numantia',-133,-2.44,41.81,['rom'],'Die keltiberische Stadt fällt nach langer Belagerung.'),
 ('Mobei',-119,106.0,46.5,['han','xiong'],'Wei Qing und Huo Qubing schlagen die Xiongnu nördlich der Gobi.'),
 ('Aquae Sextiae',-102,5.45,43.53,['rom'],'Marius besiegt die Teutonen.'),
 ('Zhizhi',-36,71.4,42.9,['han'],'Han-Truppen besiegen den Xiongnu-Herrscher Zhizhi am Talas.'),
 ('Carrhae',-53,39.03,36.87,['rom','parth'],'Die Parther vernichten das Heer des Crassus.'),
 ('Alesia',-52,4.50,47.54,['rom'],'Caesar besiegt Vercingetorix; Gallien ist erobert.'),
 ('Pharsalos',-48,22.38,39.30,['rom'],'Caesar siegt im Bürgerkrieg über Pompeius.'),
 ('Actium',-31,20.73,38.95,['rom','ptol'],'Octavian besiegt Antonius und Kleopatra in einer Seeschlacht.'),
 ('Varusschlacht',9,8.12,52.41,['rom'],'Arminius vernichtet drei römische Legionen in Germanien.'),
 ('Kunyang',23,113.1,33.6,['han'],'Liu Xiu (Guangwu) besiegt das Heer Wang Mangs.'),
 ('Ikh Bayan',89,99.0,45.0,['han','xiong'],'Dou Xian schlägt die Nördlichen Xiongnu entscheidend.'),
 ('Edessa',260,38.79,37.16,['rom','sasan'],'Schapur I. nimmt Kaiser Valerian gefangen.'),
 ('Guandu',200,114.2,34.8,['han'],'Cao Cao besiegt Yuan Shao im Kampf um Nordchina.'),
 ('Rote Klippen',208,113.9,29.9,['han'],'Sun Quan und Liu Bei stoppen Cao Cao am Jangtse.'),
 ('Kalinga-Krieg',-261,85.8,20.3,['maurya'],'Ashoka erobert Kalinga; danach wendet er sich dem Buddhismus zu.'),
 ('Milvische Brücke',312,12.47,41.94,['rom'],'Konstantin siegt über Maxentius.'),
 ('Adrianopel',378,26.56,41.68,['rom'],'Goten vernichten das oströmische Heer; Kaiser Valens fällt.'),
 ('Katalaunische Felder',451,4.37,48.95,['rom','hunnen'],'Aëtius und die Westgoten halten Attila auf.'),
]
battles = [{'name': n, 'jahr': j, 'lng': x, 'lat': y, 'reiche': rs, 'note': t} for n, j, x, y, rs, t in S]

# ======================================================================
#  Orte: (reich, name, lng, lat, von, bis, stufe)
#  stufe: Vorgabe hier, endgültig gesetzt durch neue_stufe() unten (1–4).
#  von/bis = Stadtgeschichte; sichtbar ist ein Ort nur, solange sein Gebiet zum Reich gehört (wird unten berechnet).
# ======================================================================
cities = [
 # --- Rom ---
 ('rom','Rom',12.50,41.90,-753,None,1),('rom','Konstantinopel',28.98,41.01,330,None,1),('rom','Alexandria',29.92,31.20,-331,None,1),
 ('rom','Antiochia',36.16,36.20,-300,None,1),('rom','Karthago',10.32,36.85,-44,None,1),('rom','Athen',23.73,37.98,-1000,None,1),
 ('rom','Lugdunum',4.83,45.76,-43,None,1),('rom','Londinium',-0.09,51.51,47,None,1),('rom','Ravenna',12.20,44.42,-200,None,2),
 ('rom','Mediolanum',9.19,45.46,-400,None,2),('rom','Aquileia',13.37,45.77,-181,None,2),('rom','Capua',14.25,41.08,-600,None,2),
 ('rom','Neapolis',14.25,40.85,-470,None,2),('rom','Tarentum',17.24,40.47,-706,None,2),('rom','Syracusae',15.29,37.07,-734,None,2),
 ('rom','Carthago Nova',-0.98,37.60,-228,None,2),('rom','Tarraco',1.25,41.12,-218,None,2),('rom','Gades',-6.29,36.53,-1100,None,2),
 ('rom','Emerita Augusta',-6.34,38.92,-25,None,2),('rom','Corduba',-4.78,37.88,-169,None,2),('rom','Massilia',5.37,43.30,-600,None,2),
 ('rom','Narbo',3.00,43.18,-118,None,2),('rom','Burdigala',-0.58,44.84,-300,None,2),('rom','Lutetia',2.35,48.85,-250,None,2),
 ('rom','Augusta Treverorum',6.64,49.75,-16,None,2),('rom','Colonia Agrippina',6.96,50.94,-38,None,2),('rom','Mogontiacum',8.27,50.00,-13,None,2),
 ('rom','Augusta Vindelicum',10.90,48.37,-15,None,2),('rom','Carnuntum',16.92,48.11,6,None,2),('rom','Sirmium',19.61,44.97,9,None,2),
 ('rom','Thessalonike',22.94,40.64,-315,None,2),('rom','Korinth',22.88,37.91,-44,None,2),('rom','Ephesos',27.34,37.94,-1000,None,2),
 ('rom','Pergamon',27.18,39.13,-300,None,2),('rom','Nikomedia',29.92,40.77,-264,None,2),('rom','Ankyra',32.86,39.93,-300,None,2),
 ('rom','Tarsos',34.90,36.92,-1000,None,2),('rom','Caesarea Maritima',34.89,32.50,-22,None,2),('rom','Jerusalem',35.23,31.78,-1000,None,2),
 ('rom','Damaskus',36.30,33.51,-1000,None,2),('rom','Palmyra',38.27,34.55,-100,None,2),('rom','Petra',35.44,30.33,-300,None,2),
 ('rom','Kyrene',21.86,32.82,-630,None,2),('rom','Leptis Magna',14.29,32.64,-600,None,2),('rom','Caesarea (Mauretania)',2.19,36.61,-25,None,2),
 ('rom','Tingis',-5.80,35.77,-400,None,2),('rom','Eboracum',-1.08,53.96,71,None,2),('rom','Ulpia Traiana Sarmizegetusa',22.79,45.52,106,None,2),
 ('rom','Byzantion',28.98,41.01,-667,329,2),('rom','Augusta Raurica',7.72,47.53,-44,None,3),('rom','Aventicum',7.04,46.88,-15,None,3),
 ('rom','Pompeji',14.49,40.75,-600,79,3),('rom','Ostia',12.29,41.75,-620,None,3),('rom','Brundisium',17.94,40.63,-244,None,3),
 ('rom','Verona',10.99,45.44,-89,None,3),('rom','Arelate',4.63,43.68,-46,None,3),('rom','Nemausus',4.36,43.84,-121,None,3),
 ('rom','Vienna (Vienne)',4.87,45.52,-121,None,3),('rom','Argentoratum',7.75,48.58,-12,None,3),('rom','Castra Regina',12.10,49.02,179,None,3),
 ('rom','Vindobona',16.37,48.21,97,None,3),('rom','Aquincum',19.05,47.56,41,None,3),('rom','Singidunum',20.46,44.82,86,None,3),
 ('rom','Naissus',21.90,43.32,6,None,3),('rom','Serdica',23.32,42.70,46,None,3),('rom','Philippopolis',24.75,42.15,-342,None,3),
 ('rom','Dyrrachium',19.45,41.32,-627,None,3),('rom','Salona',16.48,43.54,-200,None,3),('rom','Sparta',22.43,37.07,-900,None,3),
 ('rom','Smyrna',27.14,38.42,-1000,None,3),('rom','Milet',27.28,37.53,-1000,None,3),('rom','Sardes',28.04,38.49,-1000,None,3),
 ('rom','Sinope',35.15,42.03,-630,None,3),('rom','Trapezus',39.72,41.00,-756,None,3),('rom','Berytus',35.50,33.89,-1000,None,3),
 ('rom','Tyros',35.20,33.27,-1000,None,3),('rom','Apameia',36.40,35.42,-300,None,3),('rom','Gaza',34.46,31.50,-1000,None,3),
 ('rom','Bostra',36.48,32.52,-100,None,3),('rom','Memphis',31.25,29.85,-3000,None,3),('rom','Theben',32.65,25.70,-3000,None,3),
 ('rom','Utica',10.06,37.06,-1100,None,3),('rom','Sabratha',12.48,32.80,-500,None,3),('rom','Hippo Regius',7.77,36.88,-1100,None,3),
 ('rom','Hispalis',-5.99,37.39,-800,None,3),('rom','Toletum',-4.03,39.86,-190,None,3),('rom','Caesaraugusta',-0.88,41.65,-14,None,3),
 ('rom','Olisipo',-9.14,38.71,-1000,None,3),('rom','Bracara Augusta',-8.43,41.55,-16,None,3),('rom','Camulodunum',0.90,51.89,43,None,3),
 ('rom','Lindum',-0.54,53.23,60,None,3),('rom','Tomis',28.65,44.17,-600,None,3),
 # --- Han ---
 ('han',"Chang'an",108.95,34.27,-202,None,1),('han','Luoyang',112.45,34.62,-206,None,1),('han','Dunhuang',94.66,40.14,-111,None,2),
 ('han','Panyu',113.27,23.13,-214,None,2),('han','Linzi',118.30,36.80,-859,None,2),('han','Handan',114.48,36.60,-386,None,2),
 ('han','Chengdu',104.07,30.67,-316,None,2),('han','Wuwei',102.64,37.93,-121,None,2),('han','Ji (Peking)',116.40,39.90,-1045,None,2),
 ('han','Jiangling',112.20,30.35,-689,None,2),('han','Changsha',112.98,28.20,-206,None,2),('han','Wu (Suzhou)',120.62,31.30,-514,None,2),
 ('han','Lelang (Pjöngjang)',125.75,39.02,-108,None,2),('han','Jiaozhi (Hanoi)',105.85,21.03,-111,None,2),('han','Dian (Kunming)',102.70,24.90,-279,None,2),
 ('han','Zhangye',100.45,38.93,-111,None,3),('han','Jiuquan',98.50,39.73,-111,None,3),('han','Yumen-Pass',93.86,40.35,-111,None,3),
 ('han','Hepu',109.20,21.66,-111,None,3),('han','Shouchun',116.78,32.58,-241,None,3),('han','Pengcheng',117.19,34.26,-575,None,3),
 ('han','Wan (Nanyang)',112.53,33.00,-688,None,3),('han','Jinyang (Taiyuan)',112.55,37.87,-497,None,3),
 # --- Nachbarreiche ---
 ('karth','Karthago',10.32,36.85,-814,-146,1),('karth','Carthago Nova',-0.98,37.60,-228,-209,2),('karth','Utica',10.06,37.06,-1100,None,3),
 ('ptol','Alexandria',29.92,31.20,-331,None,1),('ptol','Memphis',31.25,29.85,-3000,None,2),('ptol','Kyrene',21.86,32.82,-630,None,2),('ptol','Theben',32.65,25.70,-3000,None,3),
 ('seleu','Antiochia',36.16,36.20,-300,None,1),('seleu','Seleukeia',44.52,33.10,-305,None,1),('seleu','Sardes',28.04,38.49,-1000,None,2),
 ('seleu','Ekbatana',48.52,34.80,-700,None,2),('seleu','Susa',48.26,32.19,-4000,None,3),
 ('parth','Ktesiphon',44.58,33.09,-120,None,1),('parth','Hekatompylos',54.40,36.10,-300,None,2),('parth','Ekbatana',48.52,34.80,-700,None,2),
 ('parth','Merw',61.83,37.66,-500,None,2),('parth','Seleukeia',44.52,33.10,-305,None,3),('parth','Nisa',58.20,37.95,-250,None,3),('parth','Susa',48.26,32.19,-4000,None,3),
 ('sasan','Ktesiphon',44.58,33.09,224,None,1),('sasan','Istachr',52.92,29.98,-500,None,2),('sasan','Merw',61.83,37.66,-500,None,2),
 ('sasan','Gundischapur',48.52,32.28,260,None,3),('sasan','Bischapur',51.57,29.78,266,None,3),
 ('maurya','Pataliputra',85.14,25.61,-490,None,1),('maurya','Taxila',72.82,33.74,-500,None,2),('maurya','Ujjain',75.78,23.18,-600,None,2),
 ('kusch','Purushapura',71.57,34.01,-200,None,1),('kusch','Mathura',77.67,27.49,-600,None,2),('kusch','Taxila',72.82,33.74,-500,None,2),('kusch','Kapisa (Begram)',69.27,34.99,-300,None,3),
 ('gupta','Pataliputra',85.14,25.61,-490,None,1),('gupta','Ujjain',75.78,23.18,-600,None,2),('gupta','Prayaga',81.85,25.43,-600,None,3),
 # --- Europa (Kontext) ---
 ('westgot','Tolosa (Toulouse)',1.44,43.60,-100,None,1),('westgot','Burdigala',-0.58,44.84,-300,None,2),('westgot','Narbo',3.00,43.18,-118,None,2),('westgot','Arelate',4.63,43.68,-46,None,3),
 ('sueben','Bracara',-8.43,41.55,-16,None,1),('vandal','Karthago',10.32,36.85,-44,None,1),('vandal','Hippo Regius',7.77,36.88,-1100,None,3),
 ('burgund','Genava (Genf)',6.14,46.20,-120,None,1),('burgund','Lugdunum',4.83,45.76,-43,None,2),('burgund','Borbetomagus (Worms)',8.36,49.63,-14,None,2),
 ('franken','Tornacum (Tournai)',3.39,50.61,-50,None,1),('franken','Köln',6.96,50.94,-38,None,2),
 ('odoaker','Ravenna',12.20,44.42,-200,None,1),('odoaker','Rom',12.50,41.90,-753,None,2),('angels','Cantiacorum (Canterbury)',1.08,51.28,-50,None,2),
]

cities += [('rom','Gortyna',24.95,35.06,-600,None,2),('rom','Puteoli',14.12,40.82,-194,None,3)]

# Stufen (Anzeige nach Zoom): 1 Weltstädte, 2 große Provinzzentren (über das Reich verteilt), 3 weitere Provinzhauptstädte
# und wirtschaftlich bedeutende Städte, 4 kleinere Orte
STUFE_ROM_HAN = {
 1: {'Rom','Konstantinopel','Alexandria','Antiochia','Karthago',"Chang'an",'Luoyang'},
 2: {'Londinium','Lugdunum','Augusta Treverorum','Tarraco','Corduba','Mediolanum','Carnuntum','Sirmium','Thessalonike',
     'Athen','Ephesos','Ankyra','Caesarea Maritima','Leptis Magna',
     'Chengdu','Ji (Peking)','Panyu','Dunhuang','Lelang (Pjöngjang)','Linzi'},
 3: {'Ravenna','Emerita Augusta','Narbo','Burdigala','Colonia Agrippina','Mogontiacum','Augusta Vindelicum','Aquincum','Salona','Korinth','Nikomedia','Tarsos','Bostra','Kyrene','Gortyna','Caesarea (Mauretania)','Tingis','Eboracum','Ulpia Traiana Sarmizegetusa','Tomis','Handan','Wuwei','Jiaozhi (Hanoi)','Dian (Kunming)','Jiangling','Changsha','Wu (Suzhou)',
     'Massilia','Gades','Carthago Nova','Aquileia','Capua','Neapolis','Puteoli','Ostia','Syracusae','Tarentum','Leptis Magna',
     'Palmyra','Damaskus','Petra','Pergamon','Smyrna','Tyros','Berytus','Jerusalem','Memphis','Byzantion','Lutetia','Hispalis',
     'Arelate','Brundisium','Milet','Sardes','Sinope','Trapezus','Apameia','Gaza','Dyrrachium','Utica','Hippo Regius','Olisipo',
     'Camulodunum','Verona','Zhangye','Jiuquan','Hepu','Shouchun','Pengcheng','Wan (Nanyang)','Jinyang (Taiyuan)'},
}
def neue_stufe(r, n, st):
    if r in ('rom', 'han'):
        return next((k for k in (1, 2, 3) if n in STUFE_ROM_HAN[k]), 4)
    if META[r].get('kontext'): return 2 if st == 1 else 4   # Europa (Kontext): Hauptorte erst beim Hineinzoomen
    return st if st < 3 else 4                              # Nachbarreiche: Hauptstadt 1, wichtige Städte 2, sonst 4
cities = [(r, n, x, y, v, b, neue_stufe(r, n, st)) for r, n, x, y, v, b, st in cities]

def zeiten(reich, lng, lat, von, bis):
    """Jahre, in denen ein Gebiet des Reichs den Ort (±0,3°) abdeckt, geschnitten mit der Stadtgeschichte"""
    from shapely.geometry import Point
    pt = Point(lng, lat).buffer(0.3)
    ende = bis + 1 if bis is not None else META[reich]['bis']
    iv = sorted((max(p['von'], von), min(p['bis'], ende)) for p in pieces if p['reich'] == reich and p['g'].intersects(pt))
    iv = [x for x in iv if x[0] < x[1]]
    out = []
    for a, b in iv:
        if out and a <= out[-1][1]: out[-1][1] = max(out[-1][1], b)
        else: out.append([a, b])
    return out

orte = []
for r, n, x, y, v, b, st in cities:
    z = zeiten(r, x, y, v, b)
    if not z: print('Ort ohne Gebiet:', r, n); continue
    orte.append({'reich': r, 'name': n, 'lng': x, 'lat': y, 'stufe': st, 'zeiten': z})

out = {'meta': META, 'reihen': ORDER, 'regionen': feats, 'ereignisse': events, 'schlachten': battles, 'orte': orte}
path = os.path.join(HERE, 'data/reiche.json')
json.dump(out, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('Regionen:', len(feats), ' Datei:', os.path.getsize(path), 'Bytes')
from collections import Counter
print(Counter(f['properties']['reich'] for f in feats))
