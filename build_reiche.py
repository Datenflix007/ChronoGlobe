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
 'rom':   dict(name='Römisches Reich', von=-753, bis=1453, farbe='#c4342c', zentrum=[18, 41], rahmen=[-13, 27.5, 46, 56.5], haupt=True,
              kurz='Vom Stadtstaat zum Weltreich rund um das Mittelmeer: Königszeit (753–510 v. Chr., Gründungsdatum legendär), Republik (510–27 v. Chr.), Kaiserzeit (27 v. Chr.–284 n. Chr.), Spätantike (284–565); Ostrom/Byzanz bis 1453.'),
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
 'franken': dict(name='Franken (Merowinger und Karolinger)', von=257, bis=843, farbe='#7d8a5a', zentrum=[5.5, 50.9], kontext=True,
              kurz='Germanischer Verband am Niederrhein; Salfranken ab 358 in Toxandrien, ab etwa 457 Kleinkönigreich um Tournai (Childerich I.). Chlodwig (481/82–511) begründet das Frankenreich der Merowinger; ab 751 Karolinger, unter Karl dem Großen (768–814, Kaiser 800) von der Elbe bis Mittelitalien. 843 im Vertrag von Verdun geteilt.'),
 'alaman': dict(name='Alamannen', von=260, bis=506, farbe='#8f7a5c', zentrum=[8.6, 48.5], kontext=True,
              kurz='Germanischer Verband; besetzt nach 260 das aufgegebene Dekumatland, nach 455 auch Elsass und Nordschweiz.'),
 'westgot': dict(name='Westgotenreich', von=418, bis=711, farbe='#8a6f8f', zentrum=[0.5, 43.5], kontext=True,
              kurz='418 als Föderaten in Aquitanien angesiedelt (Hauptstadt Toulouse); unter Eurich (466–484) größtes Reich im Westen.'),
 'sueben': dict(name='Suebenreich', von=411, bis=585, farbe='#6f8a8a', zentrum=[-8, 42.5], kontext=True,
              kurz='Germanisches Königreich in Gallaecia (Nordwesten Hispaniens), Hauptort Bracara.'),
 'vandal': dict(name='Vandalen', von=406, bis=534, farbe='#5f7a99', zentrum=[9.5, 35.5], kontext=True,
              kurz='Überschreiten 406 den Rhein, ziehen 409 nach Hispanien (Baetica), setzen 429 nach Afrika über und erobern 439 Karthago; 455 plündern sie Rom.'),
 'burgund': dict(name='Burgunderreich', von=413, bis=534, farbe='#a07a6a', zentrum=[5.6, 46.2], kontext=True,
              kurz='413–436 Reich um Worms (Zerstörung durch hunnische Truppen), ab 443 in der Sapaudia um Genf neu angesiedelt.'),
 'odoaker': dict(name='Reich des Odoaker', von=476, bis=493, farbe='#7a7a92', zentrum=[12, 43], kontext=True,
              kurz='Odoaker setzt 476 den letzten weströmischen Kaiser ab und herrscht als König in Italien.'),
 'ostgot': dict(name='Ostgoten', von=456, bis=553, farbe='#6d7f6d', zentrum=[18, 46.5], kontext=True,
              kurz='Nach dem Zerfall des Hunnenreichs 456–473 als Föderaten in Pannonien; ab 493 Reich in Italien.'),
 'syagrius': dict(name='Reich von Soissons', von=461, bis=487, farbe='#9a8a7a', zentrum=[2.5, 48.8], kontext=True,
              kurz='Gallorömischer Reststaat in Nordgallien unter Aegidius und seinem Sohn Syagrius; 486/87 von Chlodwig I. erobert. Ausdehnung unsicher.'),
 'osman': dict(name='Osmanisches Reich', von=1299, bis=1922, farbe='#8e6f50', zentrum=[30, 40.5], kontext=True,
              kurz='Beherrscht um 1400 den Balkan und den Westen Kleinasiens; erobert 1453 Konstantinopel.'),
 'angels': dict(name='Angelsachsen', von=449, bis=927, farbe='#8c7f6a', zentrum=[0.3, 52.3], kontext=True,
              kurz='Nach dem Abzug Roms (410) siedeln Angeln, Sachsen und Jüten im Osten Britanniens; Kleinkönigreiche entstehen.'),
}
ORDER = list(META.keys())
# Bei Überlappung gewinnt das frühere Reich. Die Nachfolgestaaten stehen VOR Rom: Sie nehmen Westrom die Gebiete ab,
# auch wenn das formale Ende einer weströmischen Provinz später datiert ist.
KONTEXT = ['osman', 'syagrius', 'sueben', 'vandal', 'burgund', 'odoaker', 'ostgot', 'angels', 'franken', 'alaman', 'westgot']   # Westgoten zuletzt: ihre großen Flächen füllen nur, was frei ist
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

# ---- Rom: Provinzen (Stand um 117 n. Chr., Namen und Einrichtungsjahre nach der Liste der Provinzen des Römischen
#      Reichs, de.wikipedia). Flächen grob von Hand gezeichnet. von = Erwerb des Gebiets, Provinzjahr im Namen.
#      seite: w = Westrom, o = Ostrom ab 395 (Teilung nach dem Tod Theodosius' I.).
#      bis Westrom: Verlustjahr; Nachfolgestaaten (Europa, Kontext) haben bei Überlappung Vorrang.
#      Ostrom: Gebiete reichen bis zum Ende der dargestellten Antike (481); Byzanz um 1400–1453 steht gesondert unten.
OST_ENDE = 481
baetica    = P((-7.5,37.2),(-7.4,38.2),(-5.5,38.6),(-4.3,38.4),(-3.0,38.0),(-2.3,37.4),(-1.7,37.0),(-2.2,36.6),(-5.6,35.9),(-6.5,36.8))
lusitania  = P((-9.9,36.95),(-9.9,41.15),(-6.8,41.0),(-6.2,41.2),(-4.6,40.9),(-4.4,40.2),(-5.0,39.3),(-5.5,38.6),(-7.4,38.2),(-7.5,37.2))
narbonensis= P((3.25,42.45),(1.75,42.45),(1.3,43.3),(2.1,43.7),(2.9,44.2),(3.9,44.9),(4.5,45.7),(5.2,46.2),(6.1,46.35),(6.8,46.05),(6.9,45.6),(6.6,45.1),(6.6,44.5),(7.0,44.1),(7.0,43.55))
aquitania  = P((-1.8,43.35),(-1.3,44.6),(-1.2,46.2),(-2.2,47.25),(0.0,47.4),(1.5,47.4),(2.9,47.3),(3.4,46.4),(3.9,45.5),(3.9,44.9),(2.9,44.2),(2.1,43.7),(1.3,43.3),(1.75,42.45),(0.0,42.7))
lugdunensis= P((-5.0,47.5),(-5.2,48.7),(-1.9,49.7),(0.2,49.5),(1.8,49.0),(3.0,48.6),(4.4,47.9),(5.0,47.2),(5.0,46.2),(5.3,46.25),(4.8,45.7),(4.5,45.7),(3.95,44.95),(3.9,45.5),(3.4,46.4),(2.9,47.3),(1.5,47.4),(0.0,47.4),(-2.2,47.25))
belgica    = P((0.2,49.5),(1.6,50.9),(3.5,51.4),(4.3,51.3),(5.2,50.7),(6.0,50.0),(6.3,49.95),(7.1,50.25),(7.0,49.8),(6.3,49.4),(7.0,48.8),(6.7,47.9),(6.0,47.0),(5.2,46.4),(5.0,46.2),(5.0,47.2),(4.4,47.9),(3.0,48.6),(1.8,49.0))
germ_sup   = P((6.3,49.4),(7.0,49.8),(7.1,50.25),(7.3,50.5),(7.7,50.5),(8.3,50.05),(7.8,48.6),(7.6,47.6),(9.5,47.6),(9.4,47.2),(8.4,46.6),(7.0,46.4),(6.1,46.35),(5.2,46.4),(6.0,47.0),(6.7,47.9),(7.0,48.8))
germ_inf   = P((4.3,51.3),(4.5,51.9),(6.0,52.0),(6.7,51.9),(6.9,51.0),(7.3,50.5),(6.3,49.9),(6.0,50.0),(5.2,50.7))
raetia_p   = raetia.intersection(box(5,40,12.95,50))
noricum    = U(raetia.intersection(box(12.95,40,20,50)), box(12.95,46.35,16.0,47.0))
pann_nord  = pannonia.intersection(box(14,45.05,21,49))
pann_sup   = pann_nord.intersection(box(14,40,18.1,50))
pann_inf   = pann_nord.difference(box(14,40,18.1,50))
dalm_hint  = pannonia.difference(box(14,45.05,21,49))
moes_sup   = moesia.intersection(box(18,40,23.0,46))
moes_inf   = moesia.difference(box(18,40,23.0,46))
epirus     = greece.intersection(P((19.2,38.8),(19.2,40.5),(20.6,40.6),(21.4,39.9),(21.4,38.8)))
achaia     = greece.difference(epirus).intersection(box(19,35,27,39.05))
macedonia  = greece.difference(epirus).difference(box(19,35,27,39.05))
sic_ost    = sicilia.intersection(box(14.6,36.4,15.8,37.7))
numidia    = africa_ext.intersection(box(5,30,8.3,38))
tripolis   = africa_ext.intersection(box(11.2,28,26,38)).difference(africa)
africa_nova= africa_ext.difference(numidia).difference(tripolis)
maur_ting  = mauretania.intersection(box(-11,30,-1.8,37))
maur_caes  = mauretania.difference(box(-11,30,-1.8,37))
alpen_prov = alpen_w
soissons   = P((1.5,50.1),(4.3,49.9),(4.6,49.0),(4.0,48.0),(2.5,47.3),(0.0,47.4),(-1.0,48.3),(0.2,49.5))

reg('rom','Italia (Mittelitalien)',italia_c,-300,476,seite='w')
reg('rom','Italia (Süditalien, nach dem Krieg gegen Pyrrhos)',italia_s,-272,476,seite='w')
reg('rom','Sicilia (Syrakus, ganz römisch ab 210 v. Chr.)',sic_ost,-212,476,seite='w')
reg('rom','Sicilia (erste Provinz, 241 v. Chr.)',sicilia,-241,476,seite='w')
reg('rom','Sardinia et Corsica (237 v. Chr. annektiert, Provinz 227 v. Chr.)',sardinia,-237,476,seite='w')
reg('rom','Gallia cisalpina (Norditalien, ab 42 v. Chr. Teil Italiens)',cisalpina,-222,476,seite='w')
reg('rom','Hispania Baetica (Hauptstadt Corduba)',baetica,-206,476,seite='w')
reg('rom','Hispania Tarraconensis (Küste; Hauptstadt Tarraco)',hisp_early,-206,476,seite='w')
reg('rom','Illyricum / Dalmatia (Küste)',illyria,-167,OST_ENDE,seite='w')
reg('rom','Macedonia (Provinz 148 v. Chr.)',macedonia,-148,OST_ENDE,seite='o')
reg('rom','Achaia (Hauptstadt Korinth, Provinz 27 v. Chr.)',achaia,-146,OST_ENDE,seite='o')
reg('rom','Epirus (Hauptstadt Nikopolis, eigene Provinz vor 117)',epirus,-146,OST_ENDE,seite='o')
reg('rom','Africa proconsularis (Africa vetus, Hauptstadt Karthago)',africa,-146,439,seite='w')
reg('rom','Lusitania (Süden)',lusitania.intersection(hisp_mid),-138,476,seite='w')
reg('rom','Hispania Tarraconensis (Inneres)',hisp_mid.difference(lusitania),-133,476,seite='w')
reg('rom','Asia (Erbe von Pergamon, Provinz 129 v. Chr.; Hauptstadt Ephesos)',asia,-133,OST_ENDE,seite='o')
reg('rom','Gallia Narbonensis',narbonensis,-121,476,seite='w')
reg('rom','Creta et Cyrenaica (Kyrenaika)',cyrenaica,-74,OST_ENDE,seite='o')
reg('rom','Bithynia et Pontus (Hauptstadt Nikomedia)',bithynia,-74,OST_ENDE,seite='o')
reg('rom','Creta et Cyrenaica (Kreta; Hauptstadt Gortyn)',creta,-67,OST_ENDE,seite='o')
reg('rom','Bithynia et Pontus (Pontus)',pontus,-64,OST_ENDE,seite='o')
reg('rom','Cilicia (Hauptort Tarsos)',cilicia,-64,OST_ENDE,seite='o')
reg('rom','Syria (Hauptstadt Antiochia, Provinz 63 v. Chr.)',syria,-64,OST_ENDE,seite='o')
reg('rom','Lusitania (Norden)',lusitania,-61,476,seite='w')
reg('rom','Cyprus',cyprus,-58,OST_ENDE,seite='o')
reg('rom','Gallia Aquitania (Hauptstadt Burdigala, Provinz 16 v. Chr.)',aquitania,-50,476,seite='w')
reg('rom','Gallia Lugdunensis (Hauptstadt Lugdunum)',lugdunensis,-50,476,seite='w')
reg('rom','Gallia Belgica (Hauptstadt Durocortorum/Reims)',belgica,-50,476,seite='w')
reg('rom','Germania inferior (eigene Provinz ab 90)',germ_inf,-50,476,seite='w')
reg('rom','Germania superior (eigene Provinz ab 90; mit Helvetiern)',germ_sup,-50,476,seite='w')
reg('rom','Numidia (Africa nova)',numidia,-46,439,seite='w')
reg('rom','Africa proconsularis (Africa nova, Byzacena)',africa_nova,-46,439,seite='w')
reg('rom','Tripolitanien (zu Africa proconsularis)',tripolis,-46,455,seite='w')
reg('rom','Aegyptus (Hauptstadt Alexandria)',aegyptus,-30,OST_ENDE,seite='o')
reg('rom','Galatia',galatia,-25,OST_ENDE,seite='o')
reg('rom','Hispania Tarraconensis (Nordwesten: Gallaecia, Asturien, Kantabrien)',hisp_all,-19,476,seite='w')
reg('rom','Raetia',raetia_p,-15,476,seite='w')
reg('rom','Noricum',noricum,-15,476,seite='w')
reg('rom','Alpenprovinzen (Alpes Maritimae, Cottiae, Graiae et Poeninae)',alpen_prov,-15,476,seite='w')
reg('rom','Noricum und Ostalpen',alpen_o,-15,476,seite='w')
reg('rom','Iudaea',judaea,6,OST_ENDE,seite='o')
reg('rom','Moesia superior (Provinz Moesia, Teilung 86)',moes_sup,6,OST_ENDE,seite='o')
reg('rom','Moesia inferior (Provinz Moesia, Teilung 86)',moes_inf,6,OST_ENDE,seite='o')
reg('rom','Pannonia superior',pann_sup,9,433,seite='w')
reg('rom','Pannonia inferior',pann_inf,9,433,seite='w')
reg('rom','Dalmatia (Hinterland)',dalm_hint,9,OST_ENDE,seite='w')
reg('rom','Cappadocia (Hauptstadt Caesarea)',cappadocia,18,OST_ENDE,seite='o')
reg('rom','Palmyrene (zu Syria)',palmyrene,17,OST_ENDE,seite='o')
reg('rom','Mauretania Tingitana',maur_ting,42,429,seite='w')
reg('rom','Mauretania Caesariensis',maur_caes,42,429,seite='w')
reg('rom','Britannia (Süden)',brit_s,43,410,seite='w')
reg('rom','Lycia et Pamphylia',lycia,43,OST_ENDE,seite='o')
reg('rom','Thracia',thracia,46,OST_ENDE,seite='o')
reg('rom','Pontus Polemoniacus',pontus_o,64,OST_ENDE,seite='o')
reg('rom','Commagene (zu Syria)',commagene,72,OST_ENDE,seite='o')
reg('rom','Agri decumates (zu Germania superior und Raetia)',agri_dec,74,260,seite='w')
reg('rom','Britannia (Norden und Wales)',brit_n,78,410,seite='w')
reg('rom','Dacia',dacia_mm,106,271,seite='o')
reg('rom','Arabia Petraea (Hauptstadt Bostra)',arabia,106,OST_ENDE,seite='o')

# ---- Byzanz (Ostrom) im Spätmittelalter, Abschnitt 1400–1453 der Zeitleiste ----
byz_konst  = P((27.9,40.95),(27.9,41.55),(29.1,41.25),(29.05,40.98))
byz_thess  = P((22.6,40.5),(23.3,40.8),(24.0,40.4),(23.9,39.9),(22.9,40.1))
byz_morea  = P((22.0,36.4),(21.9,37.3),(22.4,37.6),(23.2,37.6),(23.2,36.4))
byz_achaia = P((21.1,37.4),(21.1,38.4),(22.9,38.3),(22.4,37.6),(21.9,37.3))
reg('rom','Konstantinopel und Umland',byz_konst,1400,1453,seite='o')
reg('rom','Thessalonike (1403 zurückgewonnen, 1423 an Venedig)',byz_thess,1403,1423,seite='o')
reg('rom','Despotat Morea (Peloponnes)',byz_morea,1400,1460,seite='o')
reg('rom','Nordwest-Peloponnes (ab 1430 byzantinisch)',byz_achaia,1430,1460,seite='o')

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
reg('karth','Sardinien und Korsika',sardinia,-300,-237)   # 237 v. Chr. von Rom annektiert (Grundkurs-Skript S. 68)
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
# Arabische Eroberung: Ktesiphon 637, Nahavand 642, Tod Yazdegerds III. 651
for nm, g, bis in [('Mesopotamien',mesopot,637),('Medien',media,642),('Persis (Stammland)',persis,None),('Parthyene',parthyene,None),('Ost-Iran',ostiran,None)]:
    reg('sasan', nm, g, 224, bis)
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
reg('westgot','Aquitanien (Föderatenvertrag)',wg_aquit,418,507)   # 507 Vouillé: Aquitanien fränkisch
reg('westgot','Septimanien (Narbonne)',wg_sept,462)
reg('westgot','Gallien bis zur Loire',wg_gall,470,507)
nord_pyr = P((-2.2,43.55),(-1.85,43.4),(-1.5,43.1),(-0.6,42.8),(0.7,42.7),(2.0,42.45),(3.15,42.45),(3.4,42.5),(3.4,44.3),(-2.2,44.3))   # nördlich der Pyrenäen
reg('westgot','Hispanien (Eroberung unter Eurich)',hisp_all.difference(nord_pyr),472)
reg('westgot','Provence (Arles, Marseille)',wg_prov,474,508)   # 508 an die Ostgoten, 537 fränkisch
reg('sueben','Gallaecia',sueb_core,411)
reg('sueben','Lusitanien und Baetica',sueb_ext,439,456)
reg('vandal','Baetica (Silingen und Hasdingen)',baetica,411,429)
reg('vandal','Mauretanien',mauretania,429)
reg('vandal','Africa und Numidien (Karthago)',U(africa,africa_nova,numidia),439)
reg('vandal','Tripolitanien',tripolis,455)
reg('vandal','Sardinien, Korsika, Balearen',U(sardinia,balearen),455)
reg('burgund','Reich um Worms',burg_worms,413,436)
reg('burgund','Sapaudia (Genf)',burg_sap,443)
reg('burgund','Rhônetal und Lyon',burg_rhone,470)
reg('odoaker','Italien',U(italia_c,italia_s,cisalpina,sicilia),476)
reg('odoaker','Dalmatien (nach dem Tod des Julius Nepos 480)',U(illyria,dalm_hint),481)
reg('syagrius','Nordgallien zwischen Somme und Loire (Ausdehnung unsicher)',soissons,461,487)
osm_balkan = P((19.8,41.8),(20.5,43.2),(22.4,44.6),(26,44.0),(28.6,43.8),(29.2,41.2),(28.0,40.9),(26.4,40.4),(24.0,40.7),(23.0,40.3),(22.4,39.5),(21.0,39.6),(20.0,40.0))
osm_anatol = P((26.2,40.0),(28.0,40.6),(31.0,41.2),(34.0,41.8),(36.0,41.5),(36.5,38.5),(32.0,37.0),(29.0,36.6),(27.0,37.5))
reg('osman','Balkan (Thrakien, Bulgarien, Makedonien, Thessalien)',osm_balkan.difference(byz_konst).difference(byz_thess),1400,1454)
reg('osman','Westliches Kleinasien',osm_anatol,1400,1454)
reg('osman','Thessalonike (1430 erobert)',byz_thess,1430,1454)
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
 # Rom bis 476, Karthago, Hellenistische Reiche, Parther, Sasaniden nach dem Grundkurs „Alte Geschichte“ (Skript FSU Jena,
 # WS 2022/23; Seite im 6. Feld). Ein Ereignis beschreibt den Zustand bis zum nächsten (Infokarte, Marker auf der Zeitleiste).
 # 5. Feld: Anzeige des Jahres. Die Gebiete Roms vor 300 v. Chr. stehen in build_fruehe_kulturen.py.
 ('rom',-753,'Gründung Roms (Sage)','Nach der späteren Überlieferung (Varro) wird Rom am 21. April 753 v. Chr. gegründet; das Datum ist legendär. Zuerst herrschen latinische Könige (Romulus, Numa Pompilius, Tullus Hostilius, Ancus Marcius).','753 v. Chr. (Sage)','66'),
 ('rom',-650,'Etruskische Könige','Unter Tarquinius Priscus, Servius Tullius und Tarquinius Superbus wächst Rom zur Stadt. Von den Etruskern übernehmen die Römer u. a. Alphabet, Vorzeichenschau und Amtsinsignien.','um 650 v. Chr.','66'),
 ('rom',-510,'Beginn der Republik','Der letzte König wird vertrieben; jährlich gewählte Beamte (später zwei Konsuln) führen den Staat. Es beginnen die Ständekämpfe zwischen Patriziern und Plebejern.','um 510 v. Chr.','66'),
 ('rom',-494,'Auszug der Plebs','Mit der ersten secessio plebis erzwingen die Plebejer das Volkstribunat. Nach dem Latinerkrieg (498–493 v. Chr.) besteht der Latinische Bund.','494 v. Chr.','66'),
 ('rom',-450,'Zwölftafelgesetz','Ein Zehnmännerkollegium (decemviri) schreibt das Recht auf zwölf Tafeln nieder.','450 v. Chr.','66'),
 ('rom',-396,'Veji erobert','Nach zehnjährigem Krieg (406–396 v. Chr.) erobert Rom die etruskische Nachbarstadt Veji.','396 v. Chr.','66'),
 ('rom',-387,'Gallierkatastrophe','Kelten besiegen die Römer und plündern die Stadt (nach anderer Zählung 390 v. Chr.). Danach entsteht die Servianische Mauer (380 v. Chr.).','387 v. Chr.','66'),
 ('rom',-367,'Licinisch-sextische Gesetze','Plebejer werden zum Konsulat zugelassen; es folgen der erste plebejische Zensor (351) und Prätor (337 v. Chr.).','367 v. Chr.','66'),
 ('rom',-338,'Ende des Latinischen Bundes','Nach dem Latinerkrieg (340–338 v. Chr.) löst Rom den Bund auf und schließt Einzelverträge mit den Städten.','338 v. Chr.','66'),
 ('rom',-326,'Zweiter Samnitenkrieg','Im Krieg gegen die Samniten (326–304 v. Chr.) wird Kampanien römisch; Rom legt planmäßig Militärkolonien an.','326 v. Chr.','66'),
 ('rom',-298,'Dritter Samnitenkrieg','Der Dritte Samnitenkrieg (298–290 v. Chr.) macht Rom zur Vormacht Mittelitaliens.','298 v. Chr.','66'),
 ('rom',-287,'Ende der Ständekämpfe','Die lex Hortensia gibt den Beschlüssen der Plebs Gesetzeskraft. Patrizier und reiche Plebejer bilden die neue Führungsschicht (Nobilität).','287 v. Chr.','66–67'),
 ('rom',-280,'Krieg gegen Pyrrhos','Tarent ruft König Pyrrhos von Epirus zu Hilfe; Rom kämpft gegen ihn, die Samniten und Lukaner (280–272 v. Chr.).','280 v. Chr.','67'),
 ('rom',-272,'Hegemonie in Italien','Rom beherrscht Italien südlich der Poebene; die Bundesgenossen stellen Truppen (italische Wehrgemeinschaft).','272 v. Chr.','67'),
 ('rom',-264,'Erster Punischer Krieg','Rom und Karthago kämpfen um Sizilien (264–241 v. Chr.); 260 v. Chr. siegt Rom erstmals zur See (Mylae).','264 v. Chr.','68'),
 ('rom',-241,'Sizilien römisch','Nach dem Seesieg bei den Ägatischen Inseln räumt Karthago Sizilien. 237 v. Chr. annektiert Rom Sardinien und Korsika.','241 v. Chr.','68'),
 ('rom',-227,'Erste Provinzen','Sizilien sowie Sardinien und Korsika werden Provinzen unter Prätoren.','227 v. Chr.','68'),
 ('rom',-218,'Zweiter Punischer Krieg','Hannibal zieht über die Alpen und siegt am Trasimenischen See (217) und bei Cannae (216 v. Chr.); erst 202 v. Chr. besiegt ihn Scipio bei Zama.','218 v. Chr.','68'),
 ('rom',-201,'Frieden mit Karthago','Karthago muss Hispanien räumen; 198 v. Chr. richtet Rom dort zwei Provinzen ein (Hispania citerior und ulterior).','201 v. Chr.','68'),
 ('rom',-196,'Freiheitserklärung','Nach dem Sieg bei Kynoskephalai (197 v. Chr.) erklärt T. Quinctius Flamininus die Griechen für frei.','196 v. Chr.','68'),
 ('rom',-188,'Friede von Apameia','Antiochos III. muss nach Magnesia (189 v. Chr.) Kleinasien diesseits des Tauros räumen.','188 v. Chr.','65, 68'),
 ('rom',-168,'Pydna','Rom beendet die makedonische Monarchie; im selben Jahr zwingt eine Senatsgesandtschaft Antiochos IV. zum Rückzug aus Ägypten („Tag von Eleusis“).','168 v. Chr.','68'),
 ('rom',-146,'Karthago und Korinth zerstört','Africa (146) und Macedonia (148 v. Chr.) werden Provinzen, ebenso Achaea. Rom ist Vormacht im Mittelmeer.','146 v. Chr.','68'),
 ('rom',-133,'Erbe von Pergamon','Attalos III. vermacht Rom sein Reich (Provinz Asia ab 129 v. Chr.). Numantia fällt. Tiberius Gracchus will als Volkstribun Land an arme Bürger verteilen und wird erschlagen.','133 v. Chr.','68–69'),
 ('rom',-123,'Gaius Gracchus','Gaius Gracchus setzt als Volkstribun (123–122 v. Chr.) die Reformen seines Bruders fort und wird ebenfalls getötet. 121 v. Chr. wird Gallia Narbonensis Provinz.','123 v. Chr.','68–69'),
 ('rom',-107,'Marius','Kimbern und Teutonen fallen ein (113–101 v. Chr.). Marius, mehrfach Konsul, reformiert das Heer und besiegt sie bei Aquae Sextiae (102) und Vercellae (101 v. Chr.).','107 v. Chr.','69'),
 ('rom',-91,'Bundesgenossenkrieg','Die italischen Bundesgenossen kämpfen gegen Rom (91–89 v. Chr.).','91 v. Chr.','69'),
 ('rom',-88,'Sulla marschiert auf Rom','Sulla führt erstmals ein Heer gegen die eigene Stadt und kämpft danach gegen Mithridates VI. von Pontos (87–84 v. Chr.).','88 v. Chr.','69'),
 ('rom',-82,'Diktatur Sullas','Nach seinem zweiten Marsch auf Rom lässt Sulla Gegner ächten (Proskriptionen); Diktatur 82–79 v. Chr.','82 v. Chr.','69'),
 ('rom',-73,'Spartacus','Sklavenaufstand in Italien unter Spartacus (73–71 v. Chr.).','73 v. Chr.','69'),
 ('rom',-64,'Pompeius ordnet den Osten','Pompeius besiegt Mithridates und ordnet die römische Herrschaft im Osten neu (64/63 v. Chr.); das Seleukidenreich wird Provinz Syria.','64/63 v. Chr.','65, 69'),
 ('rom',-60,'Erstes Triumvirat','Pompeius, Caesar und Crassus verbünden sich; 59 v. Chr. ist Caesar Konsul.','60 v. Chr.','70'),
 ('rom',-58,'Caesar erobert Gallien','Im Gallischen Krieg (58–51 v. Chr.) unterwirft Caesar Gallien bis an den Rhein. 53 v. Chr. fällt Crassus gegen die Parther bei Carrhae.','58 v. Chr.','70'),
 ('rom',-49,'Bürgerkrieg','Caesar überschreitet den Rubikon. Pompeius unterliegt bei Pharsalos (48) und wird in Ägypten ermordet; Caesar siegt auch bei Thapsus (46) und Munda (45 v. Chr.).','49 v. Chr.','70'),
 ('rom',-44,'Ermordung Caesars','Caesar, Diktator auf Lebenszeit, wird am 15. März 44 v. Chr. ermordet.','44 v. Chr.','70'),
 ('rom',-43,'Zweites Triumvirat','Antonius, Octavian und Lepidus herrschen gemeinsam (lex Titia); Proskriptionen, Tod Ciceros. 42 v. Chr. siegen sie bei Philippi über die Caesarmörder.','43 v. Chr.','70'),
 ('rom',-31,'Actium','Octavian besiegt Antonius und Kleopatra VII.; 30 v. Chr. wird Ägypten römische Provinz.','31 v. Chr.','70'),
 ('rom',-27,'Augustus: Beginn der Kaiserzeit','Octavian erhält den Namen Augustus und begründet den Prinzipat; die Provinzen werden in kaiserliche und senatorische geteilt.','27 v. Chr.','70–71'),
 ('rom',9,'Varusschlacht','Der Versuch, Germanien bis zur Elbe zur Provinz zu machen (12 v.–9 n. Chr.), scheitert; der Rhein bleibt die Grenze.','9 n. Chr.','71'),
 ('rom',14,'Julisch-claudische Dynastie','Auf Augustus folgen Tiberius (14–37), Caligula (37–41), Claudius (41–54) und Nero (54–68).','14 n. Chr.','71'),
 ('rom',43,'Eroberung Britanniens','Unter Claudius beginnt die Eroberung Britanniens.','43 n. Chr.','71'),
 ('rom',64,'Brand Roms','Nach dem Brand Roms lässt Nero Christen verfolgen. 67–70 n. Chr. kämpft Rom gegen den Jüdischen Aufstand.','64 n. Chr.','71'),
 ('rom',69,'Vierkaiserjahr','Galba, Otho, Vitellius und Vespasian kämpfen um die Herrschaft; Vespasian begründet die flavische Dynastie (69–96).','69 n. Chr.','71'),
 ('rom',98,'Trajan','Unter den Adoptivkaisern (96–180) erreicht das Reich seine größte Ausdehnung; Trajan erobert Dakien (101–106 n. Chr.).','98 n. Chr.','71'),
 ('rom',117,'Größte Ausdehnung','Dakien und Arabia sind Provinzen. Mesopotamien wurde im Partherkrieg (114–117) nur kurz erobert und ist nicht eingezeichnet. Hadrian (117–138) sichert die Grenzen.','117 n. Chr.','71'),
 ('rom',166,'Pest und Markomannenkriege','Unter Mark Aurel (161–180) wütet eine Seuche; an der Donau kämpft Rom gegen Markomannen (169–175, 178–180 n. Chr.).','166 n. Chr.','72'),
 ('rom',193,'Severer','Nach Bürgerkriegen setzt sich Septimius Severus durch (193–211). Caracalla gibt 212 n. Chr. fast allen freien Reichsbewohnern das Bürgerrecht (Constitutio Antoniniana).','193 n. Chr.','72'),
 ('rom',235,'Soldatenkaiser','Mit Maximinus Thrax beginnt die Zeit der Soldatenkaiser (235–284): rasch wechselnde Kaiser, Einfälle an Rhein, Donau und Euphrat.','235 n. Chr.','72'),
 ('rom',260,'Reichskrise','Šābuhr I. nimmt Kaiser Valerian gefangen. Das Gallische Sonderreich (260–274) und das Palmyrenische Teilreich (bis 272) lösen sich ab; der Limes fällt (259/60).','260 n. Chr.','72'),
 ('rom',274,'Aurelian','Aurelian (270–275) besiegt die Sonderreiche und stellt die Einheit des Reiches wieder her.','274 n. Chr.','72'),
 ('rom',284,'Diocletian: Beginn der Spätantike','Diocletian (284–305) ordnet Heer, Verwaltung und Steuern neu; 293 n. Chr. teilen sich vier Herrscher die Macht (Tetrarchie). 303 beginnt eine Christenverfolgung.','284 n. Chr.','76'),
 ('rom',312,'Konstantin','Konstantin siegt an der Milvischen Brücke; 313 n. Chr. wird das Christentum erlaubte Religion (Mailänder Übereinkunft).','312 n. Chr.','76'),
 ('rom',324,'Konstantin Alleinherrscher','Nach dem Sieg über Licinius regiert Konstantin allein; 325 Konzil von Nicaea, 330 n. Chr. Einweihung Konstantinopels.','324 n. Chr.','76'),
 ('rom',376,'Goten an der Donau','Von den Hunnen bedrängt, überqueren Goten die Donau; 378 n. Chr. fällt Kaiser Valens bei Adrianopel. 382 werden sie als Föderaten angesiedelt.','376 n. Chr.','77'),
 ('rom',380,'Christentum als Reichsreligion','Theodosius I. verlangt im Edikt Cunctos populos das nicaenische Bekenntnis; 391/92 n. Chr. verbieten Gesetze die heidnischen Kulte.','380 n. Chr.','77'),
 ('rom',395,'Reichsteilung in West- und Ostrom','Nach dem Tod Theodosius’ I. erben seine Söhne das Reich: Honorius den Westen, Arcadius den Osten (Hauptstadt Konstantinopel).','395 n. Chr.','77'),
 ('rom',406,'Germanen über den Rhein','Vandalen, Alanen und Sueben überschreiten den Rhein (406/07) und ziehen 409 n. Chr. nach Spanien.','406 n. Chr.','78'),
 ('rom',410,'Plünderung Roms','Westgoten unter Alarich plündern Rom. Britannien wird aufgegeben; 418 n. Chr. werden die Westgoten in Aquitanien angesiedelt.','410 n. Chr.','78'),
 ('rom',429,'Vandalen in Africa','Die Vandalen unter Geiserich setzen nach Nordafrika über.','429 n. Chr.','78'),
 ('rom',439,'Vandalen erobern Karthago','Westrom verliert Nordafrika, seine reichste Provinz. 451 n. Chr. stellen sich Aëtius und die Westgoten Attila auf den Katalaunischen Feldern entgegen.','439 n. Chr.','78'),
 ('rom',455,'Vandalen plündern Rom','Nach dem Tod Valentinians III. verfällt das westliche Kaisertum; Heermeister wie Rikimer bestimmen die Politik.','455 n. Chr.','78'),
 ('rom',476,'Ende Westroms','Odoaker setzt den letzten weströmischen Kaiser Romulus Augustulus ab. Julius Nepos hält sich bis 480 in Dalmatien. Ostrom besteht weiter.','476 n. Chr.','78'),
 # --- Karthago (GK S. 68) ---
 ('karth',-300,'Seemacht im westlichen Mittelmeer','Karthago beherrscht Nordafrika, West-Sizilien, Sardinien und Küsten Hispaniens.','um 300 v. Chr.'),
 ('karth',-264,'Erster Punischer Krieg','Krieg gegen Rom um Sizilien (264–241 v. Chr.); 241 muss Karthago die Insel räumen, 237 v. Chr. verliert es Sardinien und Korsika.','264 v. Chr.','68'),
 ('karth',-237,'Die Barkiden in Hispanien','Hamilkar Barkas, Hasdrubal (seit 229) und Hannibal (seit 221 v. Chr.) besetzen Spanien; 226 v. Chr. wird der Ebro als Grenze festgelegt.','237 v. Chr.','68'),
 ('karth',-218,'Hannibal gegen Rom','Hannibal greift Italien an und siegt bei Cannae (216 v. Chr.), muss Italien aber schließlich räumen.','218 v. Chr.','68'),
 ('karth',-201,'Niederlage','Nach Zama (202 v. Chr.) verliert Karthago Hispanien.','201 v. Chr.','68'),
 ('karth',-149,'Dritter Punischer Krieg','Rom belagert Karthago (149–146 v. Chr.) und zerstört die Stadt.','149 v. Chr.','68'),
 # --- Hellenistische Reiche (GK S. 64–65) ---
 ('ptol',-300,'Ptolemaios I.','Ptolemaios I. Soter herrscht seit 305 v. Chr. als König über Ägypten (Hauptstadt Alexandria).','um 300 v. Chr.','64'),
 ('ptol',-285,'Ptolemaios II.','Unter Ptolemaios II. Philadelphos (285–246 v. Chr.) blüht Alexandria; im 1. und 2. Syrischen Krieg (274–271, 260–253) kämpft er mit den Seleukiden um Syrien.','285 v. Chr.','64–65'),
 ('ptol',-246,'Dritter Syrischer Krieg','Nach dem Tod Ptolemaios’ II. und Antiochos’ II. beginnt der Laodikekrieg (246–241 v. Chr.).','246 v. Chr.','65'),
 ('ptol',-217,'Raphia','Ptolemaios IV. besiegt Antiochos III. (4. Syrischer Krieg, 219–217 v. Chr.).','217 v. Chr.','65'),
 ('ptol',-202,'Fünfter Syrischer Krieg','Antiochos III. kämpft mit Erfolg um Koilesyrien (202–195 v. Chr.).','202 v. Chr.','65'),
 ('ptol',-168,'Tag von Eleusis','Eine römische Gesandtschaft zwingt Antiochos IV. zum Abzug aus Ägypten.','168 v. Chr.','65'),
 ('ptol',-31,'Actium','Kleopatra VII. und Antonius unterliegen Octavian; 30 v. Chr. endet das Ptolemäerreich mit dem Selbstmord Kleopatras.','31 v. Chr.','65'),
 ('seleu',-300,'Seleukos I.','Seleukos I. Nikator (König seit 305, gest. 281 v. Chr.) herrscht von Syrien bis Baktrien; ab 312/11 v. Chr. wird nach der seleukidischen Ära gezählt.','um 300 v. Chr.','46, 64'),
 ('seleu',-281,'Kurupedion','Seleukos besiegt Lysimachos, wird aber im selben Jahr von Ptolemaios Keraunos ermordet. Antiochos I. (281–261) folgt.','281 v. Chr.','64'),
 ('seleu',-240,'Abfall im Osten','Im „Bruderkrieg“ zwischen Seleukos II. und Antiochos Hierax (240–238?) lösen sich Parthien und Baktrien.','um 240 v. Chr.','65'),
 ('seleu',-212,'Anabasis Antiochos’ III.','Antiochos III. zieht nach Osten gegen die Parther (212–205 v. Chr.).','212 v. Chr.','65'),
 ('seleu',-192,'Antiochoskrieg','Krieg gegen Rom (192–188 v. Chr.); Niederlage bei Magnesia (189).','192 v. Chr.','65'),
 ('seleu',-188,'Friede von Apameia','Das Reich verliert Kleinasien diesseits des Tauros.','188 v. Chr.','65'),
 ('seleu',-141,'Mesopotamien an die Parther','Der Partherkönig Mithradates I. (171–139/38 v. Chr.) erobert Westiran und Mesopotamien.','141 v. Chr.','65'),
 ('seleu',-64,'Ende','Der Rest des Reiches wird 64/63 v. Chr. römische Provinz Syria.','64/63 v. Chr.','65'),
 ('parth',-247,'Arsakes I.','Arsakes I. (247–217 v. Chr.) begründet das Reich der Arsakiden; ab 247 v. Chr. wird nach ihnen gezählt.','247 v. Chr.','46, 65'),
 ('parth',-171,'Mithradates I.','Mithradates I. (171–139/38 v. Chr.) erobert Westiran und Mesopotamien.','171 v. Chr.','65'),
 ('parth',-53,'Carrhae','Die Parther vernichten das Heer des Crassus. 20 v. Chr. geben sie die erbeuteten Feldzeichen an Augustus zurück.','53 v. Chr.','70–71'),
 ('parth',114,'Partherkrieg Trajans','Trajan erobert Mesopotamien (114–117 n. Chr.); Hadrian gibt die Eroberungen auf.','114 n. Chr.','71'),
 ('parth',161,'Kriege mit Rom','Partherkriege des Lucius Verus (161–166) und des Septimius Severus (195, 197/98 n. Chr.).','161 n. Chr.','72'),
 # --- Sasaniden (GK S. 72, 76–77, 80) ---
 ('sasan',224,'Ardašīr I.','Ardašīr I. (224–240) stürzt die Arsakiden und begründet das Sasanidenreich.','224 n. Chr.','72'),
 ('sasan',240,'Šābuhr I.','Šābuhr I. (240–272) dringt bis Antiochia vor (253) und nimmt 260 n. Chr. Kaiser Valerian gefangen.','240 n. Chr.','72'),
 ('sasan',298,'Friede von Nisibis','Nach dem Perserzug des Galerius (297/98 n. Chr.) schließt Persien Frieden mit Rom.','298 n. Chr.','76'),
 ('sasan',363,'Perserfeldzug Julians','Kaiser Julian zieht gegen Persien und fällt auf dem Feldzug.','363 n. Chr.','77'),
 ('sasan',531,'Xusrō I.','Xusrō I. Anōširvān (531–579) schließt 532 den „Ewigen Frieden“ mit Justinian und fällt 540 n. Chr. in Syrien ein.','531 n. Chr.','80'),
 ('sasan',604,'Xusrō II.','Xusrō II. erobert große Teile Ostroms (604–627), wird aber von Herakleios zurückgeschlagen.','604 n. Chr.','80'),
 ('sasan',642,'Nihavand','Die Araber besiegen die Perser; das Sasanidenreich endet 651 n. Chr.','642 n. Chr.','80'),
 ('rom',1400,'Byzanz um 1400','Vom Oströmischen Reich sind nur Konstantinopel, Teile der Peloponnes (Morea) und einige Inseln übrig. Die Osmanen beherrschen den Balkan und den Westen Kleinasiens.'),
 ('rom',1403,'Thessalonike wieder byzantinisch','Nach der Niederlage der Osmanen gegen Timur bei Ankara (1402) erhält Byzanz Thessalonike zurück.'),
 ('rom',1423,'Thessalonike an Venedig','Byzanz übergibt die von den Osmanen belagerte Stadt an Venedig. 1430 erobern die Osmanen sie.'),
 ('rom',1430,'Osmanen erobern Thessalonike','Byzanz gewinnt im selben Jahr den Nordwesten der Peloponnes; die Morea ist fast ganz byzantinisch.'),
 ('rom',1439,'Kirchenunion von Florenz','Kaiser Johannes VIII. sucht Hilfe im Westen gegen die Osmanen. Die Union von Ost- und Westkirche bleibt ohne Wirkung.'),
 ('rom',1453,'Fall Konstantinopels','Sultan Mehmed II. erobert Konstantinopel am 29. Mai 1453. Das Byzantinische Reich, der Rest des Oströmischen Reichs, endet.'),
 ('han',-206,'Anfänge der Han-Dynastie','Liu Bang gründet die Dynastie (traditionell 206/202 v. Chr.). Im Norden sind die Xiongnu überlegen; 200 v. Chr. wird der Kaiser bei Baideng eingeschlossen.'),
 ('han',-127,'Gegenangriff auf die Xiongnu','Kaiser Wu (141–87 v. Chr.) lässt die Xiongnu angreifen. Das Ordos-Gebiet und 121 v. Chr. der Hexi-Korridor werden erobert.'),
 ('han',-111,'Expansion unter Kaiser Wu','Nanyue im Süden (111 v. Chr.), Dian (109 v. Chr.) und Nordkorea (Lelang, 108 v. Chr.) werden eingegliedert.'),
 ('han',-60,'Protektorat der Westlichen Regionen','Die Han kontrollieren die Oasenstädte im Tarimbecken – den Weg der Seidenstraße nach Westen.'),
 ('han',9,'Xin-Dynastie des Wang Mang','Wang Mang reißt die Macht an sich (9–23 n. Chr.). Die Westlichen Regionen gehen verloren. 25 n. Chr. stellt Guangwu die Han wieder her (Östliche Han, Hauptstadt Luoyang).'),
 ('han',91,'Östliche Han-Dynastie','Ban Chao stellt 91 n. Chr. den Einfluss in den Westlichen Regionen wieder her. 97 n. Chr. schickt er Gan Ying nach Westen.'),
 ('han',107,'Rückzug aus dem Westen','Aufstände führen zum Abzug aus dem Tarimbecken; Ban Yong stellt den Einfluss ab 123 n. Chr. teilweise wieder her.'),
 ('han',184,'Aufstand der Gelben Turbane','Bauernaufstände und Machtkämpfe der Generäle zerrütten das Reich. 220 n. Chr. endet die Han-Dynastie; es folgen die Drei Reiche.'),
]
def _label(j): return f'{-j} v. Chr.' if j < 0 else f'{j} n. Chr.'
GK = 'Grundkurs „Alte Geschichte“, Skript Institut für Altertumswissenschaften, FSU Jena, WS 2022/23'
# 4 Felder: Jahr exakt anzeigen; 5. Feld: eigene Anzeige (z. B. „um 650 v. Chr.“, „64/63 v. Chr.“); 6. Feld: Seite im Grundkurs-Skript
events = [{'reich': e[0], 'jahr': e[1], 'label': e[4] if len(e) > 4 else ('um ' + _label(e[1]) if e[1] == 1400 else _label(e[1])), 'titel': e[2], 'note': e[3],
           **({'quelle': GK + ', S. ' + e[5]} if len(e) > 5 else {})} for e in E]

# ======================================================================
#  Schlachten
# ======================================================================
S = [
 ('Cannae',-216,16.13,41.31,['rom','karth'],'Hannibal vernichtet ein großes römisches Heer.'),
 ('Raphia',-217,34.25,31.29,['ptol','seleu'],'Ptolemaios IV. besiegt Antiochos III.'),
 ('Zama',-202,9.30,36.15,['rom','karth'],'Scipio besiegt Hannibal; Ende des Zweiten Punischen Krieges.'),
 ('Baideng',-200,113.3,40.1,['han','xiong'],'Die Xiongnu kesseln Kaiser Gaozu ein; die Han zahlen danach Tribut.'),
 ('Kynoskephalai',-197,22.55,39.40,['rom'],'Rom besiegt Makedonien.'),
 ('Magnesia',-189,27.53,38.62,['rom','seleu'],'Rom besiegt Antiochos III. bei Magnesia am Sipylos (Winter 190/189 v. Chr.); die Seleukiden verlieren Kleinasien.'),
 ('Mylae',-260,15.24,38.22,['rom','karth'],'Erster Seesieg Roms über Karthago.'),
 ('Ägatische Inseln',-241,12.20,37.95,['rom','karth'],'Seesieg Roms; Karthago räumt Sizilien.'),
 ('Trasimenischer See',-217,12.10,43.18,['rom','karth'],'Hannibal vernichtet ein römisches Heer aus dem Hinterhalt.'),
 ('Kurupedion',-281,27.90,38.60,['seleu'],'Seleukos I. besiegt Lysimachos, der fällt.'),
 ('Arausio',-105,4.81,44.14,['rom'],'Kimbern und Teutonen besiegen zwei römische Heere.'),
 ('Vercellae',-101,8.42,45.32,['rom'],'Marius und Catulus vernichten die Kimbern.'),
 ('Thapsus',-46,11.05,35.62,['rom'],'Caesar besiegt die Anhänger des Senats in Africa.'),
 ('Munda',-45,-4.90,37.40,['rom'],'Letzter Sieg Caesars im Bürgerkrieg (Lage des Schlachtfelds umstritten).'),
 ('Philippi',-42,24.29,41.01,['rom'],'Antonius und Octavian besiegen die Caesarmörder Cassius und Brutus.'),
 ('Abrittus',251,26.56,43.52,['rom'],'Die Goten unter Cniva besiegen Kaiser Decius, der fällt.'),
 ('Naïssus',268,21.90,43.32,['rom'],'Claudius II. Gothicus besiegt die Goten.'),
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
 ('Vouillé',507,0.17,46.64,['franken','westgot'],'Chlodwig besiegt den Westgotenkönig Alarich II., der fällt.'),
 ('Soissons',486,3.32,49.38,['franken','syagrius'],'Chlodwig besiegt Syagrius.'),
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

# ======================================================================
#  Völkerwanderung: Züge als Linien [lng, lat], von/bis = Jahre, in denen der Zug gezeichnet wird (schematisch!)
# ======================================================================
WANDERUNGEN = [
 dict(volk='Hunnen', farbe='#c08a5b', von=370, bis=376, pfad=[[50,47.5],[45,47.8],[40,47.5],[35,47.0],[31,46.6]], text='um 375: Hunnen überqueren den Don und besiegen Alanen und Ostgoten – nach verbreiteter Datierung Beginn der Völkerwanderung (das Jahr ist in den Quellen nicht belegt)'),
 dict(volk='Hunnen', farbe='#c08a5b', von=395, bis=410, pfad=[[31,46.6],[27,46.5],[23,46.8],[20,47.0]], text='um 400: Hunnen in der Ungarischen Tiefebene'),
 dict(volk='Hunnen', farbe='#c08a5b', von=450, bis=451, pfad=[[20,47.0],[16,48.0],[12,48.6],[8.3,49.6],[4.4,48.9]], text='451: Attila zieht nach Gallien (Katalaunische Felder)'),
 dict(volk='Hunnen', farbe='#c08a5b', von=452, bis=453, pfad=[[20,47.0],[16,46.3],[13.37,45.77],[11.5,45.4],[10.8,45.2]], text='452: Attila in Italien (Aquileia zerstört)'),
 dict(volk='Westgoten', farbe='#8a6f8f', von=376, bis=378, pfad=[[28.5,45.4],[27.4,44.1],[26.6,42.9],[26.56,41.68]], text='376: Goten überqueren die Donau; 378 Sieg bei Adrianopel, 382 als Föderaten angesiedelt'),
 dict(volk='Westgoten', farbe='#8a6f8f', von=395, bis=401, pfad=[[26.56,41.68],[23.5,40.8],[22.4,39.5],[22.9,37.9],[21.6,38.6],[20.4,40.4],[19.6,42.0],[17.2,44.2],[14.5,45.7],[13.37,45.77]], text='395–401: Westgoten unter Alarich in Griechenland und Illyricum; 401 erster Einfall in Italien'),
 dict(volk='Westgoten', farbe='#8a6f8f', von=401, bis=410, pfad=[[13.37,45.77],[11.3,44.5],[12.5,43.1],[12.5,41.9]], text='410: Alarich plündert Rom'),
 dict(volk='Westgoten', farbe='#8a6f8f', von=410, bis=418, pfad=[[12.5,41.9],[11.5,43.6],[8.5,44.3],[5.5,43.5],[3.0,43.2],[2.17,41.39],[1.44,43.6]], text='412–418: über Südgallien nach Hispanien; 418 Ansiedlung in Aquitanien (Toulouse)'),
 dict(volk='Vandalen', farbe='#5f7a99', von=401, bis=406, pfad=[[17,50.5],[13,50.5],[10,50.2],[8.27,50.0]], text='406/07: Vandalen, Alanen und Sueben überqueren den Rhein (Tag und Ort umstritten)'),
 dict(volk='Vandalen', farbe='#5f7a99', von=406, bis=409, pfad=[[8.27,50.0],[5.5,49.3],[3.0,48.0],[1.2,46.0],[-0.5,44.5],[-1.5,43.2]], text='406–409: Zug durch Gallien bis zu den Pyrenäen'),
 dict(volk='Vandalen', farbe='#5f7a99', von=409, bis=422, pfad=[[-1.5,43.2],[-3.0,41.5],[-4.5,39.5],[-5.5,37.6]], text='409: Vandalen, Alanen und Sueben in Hispanien; Vandalen in der Baetica'),
 dict(volk='Vandalen', farbe='#5f7a99', von=429, bis=439, pfad=[[-5.5,37.6],[-5.6,36.0],[-5.3,35.6],[-2.0,35.2],[2.0,36.4],[6.0,36.8],[8.5,36.8],[10.32,36.85]], text='429: Vandalen unter Geiserich setzen nach Africa über; 430 Hippo Regius, 439 Eroberung Karthagos'),
 dict(volk='Vandalen', farbe='#5f7a99', von=455, bis=456, pfad=[[10.32,36.85],[11.0,38.5],[12.0,40.5],[12.3,41.7]], text='455: Vandalen plündern Rom (über das Meer)'),
 dict(volk='Sueben', farbe='#6f8a8a', von=409, bis=411, pfad=[[-1.5,43.2],[-4.5,42.6],[-7.0,42.2],[-8.43,41.55]], text='411: Sueben in Gallaecia (Hauptort Bracara)'),
 dict(volk='Burgunder', farbe='#a07a6a', von=406, bis=413, pfad=[[11,50.3],[9.5,50.0],[8.36,49.63]], text='413: Burgunderreich um Worms'),
 dict(volk='Burgunder', farbe='#a07a6a', von=436, bis=443, pfad=[[8.36,49.63],[7.6,48.3],[7.0,47.3],[6.14,46.2]], text='443: nach der Niederlage 436 Ansiedlung in der Sapaudia (Genf)'),
 dict(volk='Angeln, Sachsen, Jüten', farbe='#8c7f6a', von=440, bis=455, pfad=[[9.5,54.8],[7.5,54.2],[4.5,53.3],[2.0,52.5],[1.2,51.4]], text='um 450: Angeln, Sachsen und Jüten setzen nach Britannien über'),
 dict(volk='Alamannen', farbe='#8f7a5c', von=255, bis=260, pfad=[[10.8,50.2],[10.0,49.3],[9.0,48.6]], text='um 260: Alamannen besetzen das Dekumatland'),
 dict(volk='Ostgoten', farbe='#6d7f6d', von=454, bis=456, pfad=[[31,46.6],[27,46.0],[22,46.2],[19,46.5]], text='456: Ostgoten als Föderaten in Pannonien'),
 # ergänzt nach dem Grundkurs-Skript (FSU Jena, WS 2022/23), S. 3 und 79
 dict(volk='Ostgoten', farbe='#6d7f6d', von=489, bis=493, pfad=[[25.4,43.6],[22.0,44.0],[20.5,44.8],[19.6,45.0],[16.5,45.6],[14.5,46.05],[13.5,45.9],[11.0,45.44],[12.2,44.42]], text='489–493: Theoderich zieht im Auftrag Kaiser Zenos nach Italien, belagert ab 490 Ravenna und herrscht ab 493 über Italien'),
 dict(volk='Westgoten', farbe='#8a6f8f', von=507, bis=511, pfad=[[1.44,43.6],[3.0,43.18],[2.17,41.39],[-0.9,41.65],[-4.02,39.86]], text='507: Nach der Niederlage bei Vouillé gegen Chlodwig ziehen sich die Westgoten nach Spanien zurück (Westgotenreich 507–711/25)'),
 dict(volk='Langobarden', farbe='#9c7b4e', von=568, bis=572, pfad=[[18.5,46.3],[16.0,46.2],[13.5,46.1],[12.0,45.5],[10.5,45.3],[9.16,45.19]], text='568: Die Langobarden fallen in Italien ein – die letzte germanische Staatsgründung auf Reichsboden'),
]

# Auslöser und Stationen unterwegs (Überfälle, Plünderungen, Belagerungen) je Zug, Schlüssel (Volk, von).
# Station: (Jahr, lng, lat, Kurztext, Beleg). Die App blendet eine Station ab ihrem Jahr ein; liegt sie am Weg,
# zusätzlich erst, wenn die Feder die Stelle passiert hat. Umstrittenes ist als umstritten gekennzeichnet.
VW_KONTEXT = {
 ('Hunnen', 370): ('Gründe der Westwanderung unklar (Klima, Druck in Zentralasien – umstritten)', [
    (371, 42.0, 47.6, 'Alanen am Don besiegt und eingegliedert', 'Ammianus 31,3,1'),
    (375, 33.5, 47.2, 'Reich der Greutungen zerbricht; Ermanarich tot', 'Ammianus 31,3,1–2')]),
 ('Hunnen', 395): ('Hunnen rücken den Goten nach; Weideland an der Donau', [
    (408, 22.6, 43.9, '408: Uldin über die Donau, Castra Martis genommen', 'Sozomenos 9,5')]),
 ('Hunnen', 450): ('Honoria-Brief (450) und Streit um Tribute; Attila fordert Teile des Westreichs (Motive umstritten)', [
    (451, 6.18, 49.12, '7. April 451: Metz geplündert', 'Hydatius 150'),
    (451, 1.9, 47.9, '451: Orléans belagert, von Aëtius entsetzt', 'Jordanes, Getica 194–195')]),
 ('Hunnen', 452): ('Nach dem Rückschlag in Gallien erneuter Druck auf Westrom', [
    (452, 13.37, 45.77, 'Aquileia nach langer Belagerung zerstört', 'Jordanes, Getica 219–221'),
    (452, 11.0, 45.44, 'Padua, Verona, Mailand geplündert', 'Jordanes, Getica 222'),
    (453, 10.7, 45.15, 'Gesandtschaft Papst Leos I. am Mincio; Abzug (Gründe umstritten: Seuche, Hunger)', 'Prosper Tiro 1367')]),
 ('Westgoten', 376): ('Hunnenvorstoß um 375: Terwingen unter Fritigern bitten um Aufnahme ins Reich', [
    (377, 27.6, 43.2, 'Aufstand bei Marcianopolis nach Hunger und Übergriffen römischer Beamter', 'Ammianus 31,4–5'),
    (377, 26.5, 42.6, 'Plünderungen in Thrakien', 'Ammianus 31,6')]),
 ('Westgoten', 395): ('Tod Theodosius’ I. (395): Alarich fordert Jahrgelder und ein Kommando', [
    (396, 22.9, 37.9, 'Korinth, Argos und Sparta geplündert; Athen verschont', 'Zosimos 5,5–6'),
    (397, 21.8, 37.7, 'Von Stilicho in der Pholoe eingeschlossen, Alarich entkommt', 'Zosimos 5,7'),
    (399, 20.4, 40.4, 'Ostrom macht Alarich zum Heermeister in Illyricum', 'Claudian, In Eutropium 2,214–218')]),
 ('Westgoten', 401): ('Ostrom entzieht Alarich um 400 den Rückhalt; in Italien sucht er Jahrgelder und Land (Motive umstritten)', [
    (402, 10.99, 45.44, '402/03: Niederlagen gegen Stilicho bei Pollentia und Verona', 'Claudian, De bello Gothico'),
    (408, 12.2, 44.42, '408: Stilicho in Ravenna hingerichtet; Föderaten laufen zu Alarich über', 'Zosimos 5,34–35'),
    (409, 12.6, 42.2, '408/09: Rom belagert, hohes Lösegeld', 'Zosimos 5,41'),
    (410, 12.5, 41.9, '24. Aug. 410: Rom drei Tage geplündert', 'Orosius 7,39')]),
 ('Westgoten', 410): ('Alarich stirbt 410 in Kalabrien; Ataulf führt die Goten aus dem ausgezehrten Italien nach Gallien', [
    (413, 3.0, 43.18, '413: Narbonne besetzt; 414 Hochzeit Ataulfs mit Galla Placidia', 'Olympiodor fr. 24'),
    (415, 2.17, 41.39, 'Römische Seeblockade, Hunger; Ataulf in Barcelona ermordet', 'Orosius 7,43')]),
 ('Vandalen', 401): ('Druck in Mitteleuropa (Hunnen? umstritten); Rheingrenze für Italien von Truppen entblößt', [
    (406, 8.6, 50.1, 'Kampf gegen Franken am Rhein; König Godegisel fällt', 'Renatus Frigeridus bei Gregor von Tours 2,9')]),
 ('Vandalen', 406): ('Rheinübergang am 31.12.406 (Datum umstritten); Usurpation Konstantins III. lähmt die Abwehr', [
    (407, 8.27, 50.0, 'Mainz zerstört, Worms nach langer Belagerung genommen', 'Hieronymus, Brief 123,15'),
    (407, 4.03, 49.26, 'Reims, Amiens, Arras, Tournai verwüstet', 'Hieronymus, Brief 123,15'),
    (408, 1.44, 43.6, 'Toulouse hält stand (Bischof Exuperius)', 'Hieronymus, Brief 123,15')]),
 ('Vandalen', 409): ('Pyrenäenpässe im römischen Bürgerkrieg ungesichert (Herbst 409)', [
    (410, -3.7, 40.4, 'Plünderung und Hungersnot in Hispanien', 'Hydatius 46–48'),
    (418, -4.8, 38.3, '416–418: Westgoten im römischen Auftrag gegen Silingen und Alanen', 'Hydatius 63–68'),
    (422, -5.5, 37.6, 'Sieg über das römisch-gotische Heer des Castinus', 'Hydatius 77')]),
 ('Vandalen', 429): ('Druck der Westgoten in Hispanien; reiches, schwach verteidigtes Africa (Ruf durch Bonifatius umstritten)', [
    (430, 7.77, 36.88, 'Hippo Regius belagert; Augustinus stirbt während der Belagerung', 'Possidius, Vita Augustini 28–31'),
    (439, 10.32, 36.85, '19. Okt. 439: Karthago ohne Kampf genommen', 'Prosper Tiro 1339')]),
 ('Vandalen', 455): ('Ermordung Valentinians III. (455): Geiserich sieht den Vertrag als erloschen', [
    (455, 12.5, 41.9, 'Juni 455: Rom 14 Tage geplündert, Kaiserin Eudoxia verschleppt', 'Prokop, Vandalenkrieg 1,5')]),
 ('Sueben', 409): ('Mit Vandalen und Alanen über den Rhein und die Pyrenäen', [
    (411, -7.0, 42.2, '411: Gallaecia bei der Verteilung der Provinzen (durch Los)', 'Hydatius 49')]),
 ('Burgunder', 406): ('Rheinübergang 406/07 und römischer Bürgerkrieg: Die Rheingrenze ist offen', [
    (411, 8.27, 50.0, '411: Jovinus in Mainz zum Kaiser erhoben, Burgunder und Alanen dabei', 'Olympiodor fr. 17')]),
 ('Burgunder', 436): ('Einfall in die Belgica (435); Aëtius lässt sie durch hunnische Hilfstruppen schlagen', [
    (436, 8.0, 49.4, '436: Niederlage gegen Hunnen im römischen Dienst; König Gundahar fällt (Kern der Nibelungensage)', 'Prosper Tiro 1322')]),
 ('Angeln, Sachsen, Jüten', 440): ('Römische Truppen um 407–410 abgezogen; britannische Herrscher werben Söldner an (Gildas; Vortigern umstritten)', [
    (442, 0.5, 52.3, 'um 441/42: Britannien unter sächsischer Herrschaft', 'Gallische Chronik von 452'),
    (450, 1.3, 51.35, 'Hengist und Horsa in Kent (legendär)', 'Beda, Kirchengeschichte 1,15'),
    (455, -0.6, 51.8, 'Aufstand der Söldner: Plünderungen bis an das westliche Meer', 'Gildas, De excidio 23–24')]),
 ('Alamannen', 255): ('Krise des 3. Jh.: Grenztruppen gegen Perser und Usurpatoren abgezogen', [
    (259, 9.19, 45.46, '259/60: Einfall bis Italien, Niederlage bei Mediolanum', 'Zonaras 12,24'),
    (260, 10.9, 48.37, '260: Juthungen auf dem Rückweg aus Italien bei Augsburg geschlagen', 'Augsburger Siegesaltar')]),
 ('Ostgoten', 454): ('Tod Attilas (453) und Schlacht am Nedao: Das Hunnenreich zerfällt', [
    (455, 20.0, 46.4, 'Am Nedao siegen die Gepiden über Attilas Söhne', 'Jordanes, Getica 260–264')]),
 ('Ostgoten', 489): ('Kaiser Zeno schickt Theoderich gegen Odoaker – und hat die Goten so vom Balkan fort', [
    (489, 19.0, 45.3, '488/89: Kämpfe mit den Gepiden an der Ulca (Vuka)', 'Ennodius, Panegyricus 28–35'),
    (489, 13.6, 45.85, '489: Sieg über Odoaker am Isonzo, dann bei Verona', 'Anonymus Valesianus 50'),
    (493, 12.2, 44.42, '490–493: Ravenna belagert; Theoderich tötet Odoaker beim Gastmahl', 'Anonymus Valesianus 53–56')]),
 ('Westgoten', 507): ('Niederlage bei Vouillé (507) gegen Chlodwig; König Alarich II. fällt', [
    (508, 1.44, 43.6, '508: Franken nehmen Toulouse', 'Gregor von Tours 2,37'),
    (508, 3.0, 43.18, 'Theoderich sichert den Westgoten Septimanien', 'Jordanes, Getica 302')]),
 ('Langobarden', 568): ('Druck der Awaren an der Donau; Byzanz nach Gotenkrieg und Pest geschwächt', [
    (568, 13.43, 46.09, '568: Forum Iulii (Cividale) erstes Herzogtum', 'Paulus Diaconus 2,9'),
    (569, 9.19, 45.46, '569: Mailand eingenommen', 'Paulus Diaconus 2,25'),
    (572, 9.16, 45.19, '569–572: Pavia drei Jahre belagert, dann Königssitz', 'Paulus Diaconus 2,26–27')]),
}
for w in WANDERUNGEN:
    k = VW_KONTEXT.get((w['volk'], w['von']))
    if not k: continue
    w['ausloeser'] = k[0]
    w['stationen'] = [dict(jahr=j, lng=x, lat=y, text=t, quelle=q) for j, x, y, t, q in k[1]]
fehlt = [(w['volk'], w['von']) for w in WANDERUNGEN if 'ausloeser' not in w]
if fehlt: print('Zug ohne Auslöser:', fehlt)

out = {'meta': META, 'reihen': ORDER, 'regionen': feats, 'ereignisse': events, 'schlachten': battles, 'orte': orte, 'wanderungen': WANDERUNGEN}
path = os.path.join(HERE, 'data/reiche.json')
json.dump(out, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('Regionen:', len(feats), ' Datei:', os.path.getsize(path), 'Bytes')
from collections import Counter
print(Counter(f['properties']['reich'] for f in feats))
