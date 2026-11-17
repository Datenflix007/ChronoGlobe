import json, warnings; warnings.filterwarnings("ignore")
from shapely.geometry import shape, Polygon, box, mapping, MultiPolygon
from shapely.ops import unary_union
from shapely import set_precision

land_raw = shape(json.load(open('land50.geojson'))['features'][0]['geometry']) if 'features' in json.load(open('land50.geojson')) else shape(json.load(open('land50.geojson'))['geometry'])
land = land_raw.buffer(0).simplify(0.03, preserve_topology=True).buffer(0)
land = set_precision(land, 0.001)
print("land verts", sum(len(p.exterior.coords) for p in (land.geoms if hasattr(land,'geoms') else [land])))

def P(*pts): return Polygon(pts).buffer(0)
def clip(g): 
    r = g.intersection(land)
    return set_precision(r, 0.001)

# ---------------- Rom ----------------
italia = P((9,42),(9,43.8),(12.4,44.4),(13.4,44),(19,41.5),(19,37.5),(9,37.5)).difference(box(8,38.8,9.8,43.1)).difference(box(12,36,15.7,38.35))
rom264 = italia

italy2 = P((6.5,36.5),(6.5,44.2),(7.2,44.1),(7.6,45.9),(10,46.4),(13.8,46.5),(13.8,45.5),(19,41.5),(19,36.5))
hisp   = P((-9.5,36),(-9.5,40.5),(-6.5,41),(-3,41.5),(-1,42.8),(3.3,42.5),(3.3,36))
africa = P((8.2,37.4),(11.5,37.4),(11.5,34.8),(8.2,34.8))
greece = P((19.3,42.2),(26,42),(26.5,40.4),(24.5,38.3),(23,36.2),(21.5,36.3),(19.3,39.5))
asia   = P((26.1,40.3),(30.7,40.2),(30.7,37.2),(27.3,36.4),(26,38))
narb   = P((3.3,42.4),(3.3,43.6),(4.5,45.2),(6.5,45.2),(7.2,43.7))
rom133 = unary_union([italy2,hisp,africa,greece,asia,narb])

rom117_main = P((-12,31.5),(-12,46),(-10,46),(-5,49),(2,51.3),(4.6,52.3),(6.9,51),(7.5,50.4),(8.5,50.2),(9,49.5),(9.6,48.9),(10.6,48.7),(11.6,48.9),(12.1,49.05),(13.6,48.4),(17,48.2),(19,47.7),(19.1,46),(19.2,45.3),(20.3,44.9),(21.5,45.2),(22.2,46.8),(23.5,47.6),(24.5,47.7),(25.8,47.5),(26.3,46.5),(26.8,45.3),(27.6,45.0),(28.2,45.4),(29.7,45.2),(31,44),(35,43),(40,43),(41.8,41.5),(42,40.5),(41,39.5),(39.5,39.5),(38.7,38.6),(38.2,37),(39,36.5),(40.2,35),(40.5,34.2),(38.5,33.4),(38,32),(37,30),(36.5,27),(36,24),(25,24),(24.9,28),(24,30.3),(20,30.3),(17,30.2),(14,30.8),(11,31.5),(9.5,32.5),(8.5,33.7),(7,34.5),(3,35),(-1,34),(-5,33.8),(-7.5,33),(-9.9,31.5))
brit = P((-6,49.8),(-6,53.5),(-3.3,55),(-1.5,55),(2,55),(2,49.8))
rom117 = unary_union([rom117_main, brit])

Q = P((6.9,51.2),(30.5,51.2),(30.5,41.25),(26.5,41.25),(24,41.5),(22.5,41.9),(20,42.3),(19.5,43.5),(17,45),(15.5,45),(14.5,45.9),(13.8,46.5),(10.5,46.5),(10.4,46.9),(9.5,47.6),(7.6,47.6),(7.8,48.6),(8.3,50.0))
rom44 = rom117.difference(brit).difference(Q).difference(box(24.9,22,36.5,31.3)).difference(box(34.2,27,40,33)).difference(box(-13,29,-2.5,35.95)).difference(P((33.5,40.5),(38.5,40.7),(38.8,37.5),(35,37),(33.5,38.5)))

D = P((21.4,45.5),(22.4,44.75),(23,43.95),(24.9,43.8),(26,43.95),(27.3,44.2),(28,44.35),(28.9,44.7),(29.9,45.2),(29.9,46.0),(26.5,48),(22.2,48),(21.4,47))
A = P((7.6,47.6),(7.8,48.6),(8.3,50.0),(8.5,50.2),(9,49.5),(9.6,48.9),(10.6,48.7),(11.6,48.9),(12.1,49.05),(12.1,48.9),(10.9,48.3),(10.0,48.4),(9.0,48.0),(8.5,47.9),(8.4,47.6))
rom395 = rom117.difference(D).difference(A)

# ---------------- Han ----------------
han_core = P((127,39.3),(124.5,41),(122,43.2),(118,42.7),(113,42),(108,41.7),(103,41.5),(98,41.2),(94,40.6),(93.5,38.8),(96,36.5),(98.8,34.8),(100.5,32.5),(100.2,28.5),(98.7,25),(100.8,21.8),(104,21.5),(104.5,18),(106.5,16.3),(108.3,15.8),(112,16),(116,20),(118.8,22),(119.8,25.6),(122.8,29.5),(122.8,31.5),(123,34),(122.9,37.5),(122.5,39),(124,39.5))
han_early = P((104,41),(109,41),(113,39.2),(118,38),(122.7,37.3),(122,34.5),(122,31),(122,29.5),(119.5,28.5),(116.5,26),(113,25.2),(110,24.8),(107,25.5),(105,25),(104,27),(102,28),(101,29),(102.5,32),(104,34.5),(102.5,36),(102,38.5))
tarim_full = P((74,40),(80,42.2),(85,42),(90,42.5),(93.7,40.8),(93.5,38.8),(91,37.5),(87,36.5),(80,35.5),(77,36.5),(74.5,38))
tarim_east = P((84,41.5),(90,42.4),(93.7,40.8),(93.5,38.8),(91,37.5),(87,36.8),(84,38.5))

stages = [
 # reich, jahr (Beginn der Gültigkeit), label, titel, geometrie-liste [(geom, art)], note
 ("rom",-264,"um 264 v. Chr.","Rom beherrscht Italien",[(rom264,"kern")],
  "Nach dem Sieg über Pyrrhos (275 v. Chr.) kontrolliert Rom die Halbinsel südlich der Poebene. 264 v. Chr. beginnt der Erste Punische Krieg."),
 ("rom",-133,"um 133 v. Chr.","Rom nach den Punischen Kriegen",[(rom133,"kern")],
  "Die Provinzen Sizilien, Sardinien/Korsika, Hispanien, Africa, Makedonien und Achaia sind erworben. 133 v. Chr. vererbt Attalos III. sein Reich Pergamon an Rom (Provinz Asia)."),
 ("rom",-44,"um 44 v. Chr.","Rom zur Zeit Caesars",[(rom44,"kern")],
  "Gallien ist durch Caesar erobert (58–50 v. Chr.). Ägypten wird erst 30 v. Chr. römisch. Kleinasien teils noch unter abhängigen Königen."),
 ("rom",117,"um 117 n. Chr.","Größte Ausdehnung unter Trajan",[(rom117,"kern")],
  "Dakien und Arabia sind Provinzen (106 n. Chr.). Mesopotamien wurde 116/117 nur kurz erobert und ist hier nicht eingezeichnet."),
 ("rom",395,"um 395 n. Chr.","Reichsteilung",[(rom395,"kern")],
  "Nach dem Tod Theodosius' I. wird das Reich in West und Ost geteilt. Dakien (um 271) und das Dekumatland (um 260) sind längst aufgegeben."),
 ("han",-206,"um 206 v. Chr.","Anfänge der Han-Dynastie",[(han_early,"kern")],
  "Liu Bang gründet die Dynastie (traditionell 206/202 v. Chr.). Im Osten bestehen Teilkönigreiche, der Norden gehört den Xiongnu."),
 ("han",-100,"um 100 v. Chr.","Expansion unter Kaiser Wu",[(han_core,"kern"),(tarim_east,"einfluss")],
  "Unter Wu Di (141–87 v. Chr.) dehnt sich das Reich nach Westen (Hexi-Korridor), Süden (Nanyue, 111 v. Chr.) und Nordkorea (Lelang, 108 v. Chr.) aus."),
 ("han",100,"um 100 n. Chr.","Östliche Han-Dynastie",[(han_core,"kern"),(tarim_full,"einfluss")],
  "Ban Chao stellt 91 n. Chr. den Einfluss in den Westlichen Regionen wieder her. 97 n. Chr. schickt er Gan Ying nach Westen."),
]
def rnd(o):
    if isinstance(o,(list,tuple)): return [rnd(x) for x in o]
    if isinstance(o,float): return round(o,3)
    return o
feats=[]
for reich,yr,label,title,geoms,note in stages:
    for g,art in geoms:
        c = clip(g)
        if c.is_empty: print("EMPTY",reich,yr); continue
        m = mapping(c); m={"type":m["type"],"coordinates":rnd(m["coordinates"])}
        feats.append({"type":"Feature","properties":{"reich":reich,"jahr":yr,"label":label,"titel":title,"note":note,"art":art},"geometry":m})
cities=[
 ("rom","Rom",12.50,41.90,-753,None),("rom","Karthago",10.32,36.85,-44,None),("rom","Athen",23.73,37.98,-146,None),
 ("rom","Alexandria",29.92,31.20,-30,None),("rom","Antiochia",36.16,36.20,-64,None),("rom","Lugdunum",4.83,45.76,-43,None),
 ("rom","Londinium",-0.09,51.51,43,None),("rom","Konstantinopel",28.98,41.01,330,None),
 ("han","Chang'an",108.95,34.27,-202,None),("han","Luoyang",112.45,34.62,25,220),("han","Dunhuang",94.66,40.14,-111,None),("han","Panyu",113.27,23.13,-111,None),
]
meta={"rom":{"name":"Römisches Reich","von":-264,"bis":476,"rahmen":[-13,27.5,46,56.5],"zentrum":[18,41]},
      "han":{"name":"Han-Reich","von":-206,"bis":220,"rahmen":[72,8,134,49],"zentrum":[108,34]}}
out={"stufen":feats,"orte":[{"reich":r,"name":n,"lng":x,"lat":y,"von":v,"bis":b} for r,n,x,y,v,b in cities],"meta":meta}
json.dump(out,open('tafelbild/data/reiche.json','w'),ensure_ascii=False,separators=(',',':'))
lm=mapping(land); lm={"type":lm["type"],"coordinates":rnd(lm["coordinates"])}
json.dump({"type":"Feature","properties":{},"geometry":lm},open('tafelbild/data/land.json','w'),separators=(',',':'))
import os
print({f:os.path.getsize('tafelbild/data/'+f) for f in os.listdir('tafelbild/data')})
for f in feats: print(f['properties']['reich'],f['properties']['jahr'],f['properties']['art'],f['geometry']['type'])
