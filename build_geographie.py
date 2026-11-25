# -*- coding: utf-8 -*-
"""Historische Geographie (data/geographie.json): Flüsse, Gebirge, Gipfel, Meere und Landschaften mit antiken Namen.

Auswahl und Namen nach dem Grundkurs „Alte Geschichte“ (Skript FSU Jena, WS 2022/23), Kap. 8 „Historische Geographie“
(S. 41–42) und den Karten S. 43–45 (Griechenland, Kleinasien, Römisches Reich im 2. Jh., Untere Donau und Balkan,
Italien, Persien–Parthien); Hydaspes und Hyphasis nach der Zeittafel S. 63. Einträge ohne Seitenangabe sind ergänzt
(Feld „gk“ fehlt) und in der Infokarte als Ergänzung gekennzeichnet.

Verläufe: Natural Earth 1:10 Mio. (gemeinfrei, https://www.naturalearthdata.com): Flussmittellinien und Umrisse der
Gebirge. Die Kammlinie eines Gebirges ist die Mittelachse seines Umrisses (vereinfacht) – sie zeigt die Lage, nicht den
genauen Grat. Heutige Flussläufe; antike Läufe wichen besonders in Deltas und Schwemmebenen ab (Nil, Euphrat/Tigris,
Po, Mäander), siehe Skript S. 41 („Verlauf der Küstenlinie“).

Die Linien dienen auch build_grenzen.py als natürliche Grenzlinien (Flüsse, Gebirgskämme).

    python build_geographie.py      (lädt die Natural-Earth-Daten einmalig nach quellen/lokal/naturalearth/)
"""
import io, json, os, urllib.request, zipfile
import shapefile
from shapely import segmentize
from shapely.ops import voronoi_diagram
from shapely.geometry import LineString, MultiLineString, MultiPoint, Polygon, box, shape
from shapely.ops import linemerge, unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HERE, 'data', 'geographie.json')
LOKAL = os.path.join(HERE, 'quellen', 'lokal', 'naturalearth')
NE_URL = 'https://naciscdn.org/naturalearth/10m/physical/%s.zip'
GK = 'Grundkurs „Alte Geschichte“, Skript FSU Jena, WS 2022/23, S. %s'


def ne(name):
    """Natural-Earth-Datensatz (Shapefile) laden; beim ersten Mal herunterladen und entpacken."""
    ordner = os.path.join(LOKAL, name)
    if not os.path.exists(os.path.join(ordner, name + '.shp')):
        os.makedirs(ordner, exist_ok=True)
        req = urllib.request.Request(NE_URL % name, headers={'User-Agent': 'ChronoGlobe-Datenaufbereitung'})
        with urllib.request.urlopen(req, timeout=120) as r:
            zipfile.ZipFile(io.BytesIO(r.read())).extractall(ordner)
    return shapefile.Reader(os.path.join(ordner, name), encoding='utf-8', encodingErrors='replace')


def _felder(rec):
    return {k.lower(): v for k, v in rec.as_dict().items()}


_FLUSS_CACHE = {}


def flusslinien(namen, rahmen=None):
    """Alle Abschnitte eines Flusses (Natural-Earth-Namen) als Linien, optional auf ein Rechteck (lon/lat) beschränkt."""
    teile = []
    # zuerst der weltweite Datensatz; fehlt der Fluss dort, der ausführlichere europäische (sonst doppelte Linien)
    for ds in ['ne_10m_rivers_lake_centerlines', 'ne_10m_rivers_europe']:
        if teile: break
        if ds not in _FLUSS_CACHE:
            r = ne(ds)
            _FLUSS_CACHE[ds] = [(_felder(rec), shape(shp.__geo_interface__)) for rec, shp in zip(r.records(), r.shapes())]
        for f, g in _FLUSS_CACHE[ds]:
            if f.get('name') not in namen: continue
            if rahmen and not g.intersects(box(*rahmen)): continue
            if rahmen: g = g.intersection(box(*rahmen))
            teile += list(g.geoms) if hasattr(g, 'geoms') else [g]
    teile = [t for t in teile if t.geom_type == 'LineString' and t.length > 0]
    if not teile: raise SystemExit('Fluss nicht gefunden: %s' % namen)
    m = linemerge(teile)
    return list(m.geoms) if hasattr(m, 'geoms') else [m]


_GEB = None


def gebirgsflaeche(namen):
    global _GEB
    if _GEB is None:
        r = ne('ne_10m_geography_regions_polys')
        _GEB = [(_felder(rec), shape(shp.__geo_interface__).buffer(0)) for rec, shp in zip(r.records(), r.shapes())]
    gs = [g for f, g in _GEB if f.get('featurecla') == 'Range/mtn' and f.get('name') in namen]
    if not gs: raise SystemExit('Gebirge nicht gefunden: %s' % namen)
    return gs


def kammlinie(poly):
    """Mittelachse eines Gebirgsumrisses: längster Weg im Voronoi-Gerüst der Randpunkte (≈ Lage des Hauptkamms)."""
    if poly.geom_type == 'MultiPolygon': poly = max(poly.geoms, key=lambda p: p.area)
    poly = poly.simplify(0.03, preserve_topology=True).buffer(0)
    rand = segmentize(poly.exterior, 0.08)
    kanten = voronoi_diagram(MultiPoint(list(rand.coords)), edges=True)
    innen = poly.buffer(-1e-6)
    nb = {}
    alle = []
    for g in getattr(kanten, 'geoms', [kanten]):
        alle += list(g.geoms) if hasattr(g, 'geoms') else [g]
    for e in alle:
        if e.geom_type != 'LineString' or not innen.contains(e): continue
        a, b = [(round(x, 5), round(y, 5)) for x, y in e.coords[:2]]
        d = e.length
        nb.setdefault(a, []).append((b, d)); nb.setdefault(b, []).append((a, d))
    if not nb: return LineString(list(poly.exterior.coords)[:2])

    def weiteste(start):
        import heapq
        dist, vor, q = {start: 0.0}, {start: None}, [(0.0, start)]
        while q:
            d, u = heapq.heappop(q)
            if d > dist[u]: continue
            for v, w in nb[u]:
                if d + w < dist.get(v, 1e18): dist[v] = d + w; vor[v] = u; heapq.heappush(q, (d + w, v))
        ziel = max(dist, key=dist.get)
        return ziel, vor
    a, _ = weiteste(next(iter(nb)))
    b, vor = weiteste(a)
    weg = [b]
    while vor[weg[-1]] is not None: weg.append(vor[weg[-1]])
    linie = LineString(weg).simplify(0.06)
    # leicht glätten (Chaikin), damit die Linie nicht eckig wirkt
    p = list(linie.coords)
    for _ in range(2):
        q = [p[0]]
        for (x1, y1), (x2, y2) in zip(p, p[1:]):
            q += [(0.75 * x1 + 0.25 * x2, 0.75 * y1 + 0.25 * y2), (0.25 * x1 + 0.75 * x2, 0.25 * y1 + 0.75 * y2)]
        q.append(p[-1]); p = q
    return LineString(p)


# ---------- Flüsse ----------
# (id, antiker Name, heutiger Name, Natural-Earth-Namen, Rahmen [lon0, lat0, lon1, lat1] oder None, Skript-Seite oder None, Hinweis)
FLUESSE = [
    ('rhenus', 'Rhenus', 'Rhein', ['Rhine', 'Rhein', 'Rhin', 'Nederrijn', 'Waal'], [3, 46, 11, 53], '44', 'Grenze des Römischen Reichs (Germania inferior und superior); 406/07 Rheinübergang der Vandalen, Alanen und Sueben.'),
    ('danuvius', 'Danuvius (Istros)', 'Donau', ['Danube', 'Donau'], None, '44', 'Grenzfluss des Römischen Reichs von Raetia bis zum Schwarzen Meer; 376 Donauübergang der Goten.'),
    ('albis', 'Albis', 'Elbe', ['Elbe'], None, '44', '12 v.–9 n. Chr.: Versuch, Germanien bis zur Elbe zu provinzialisieren (Skript S. 71).'),
    ('liger', 'Liger', 'Loire', ['Loire'], None, '44', None),
    ('rhodanus', 'Rhodanus', 'Rhone', ['Rhône'], [3, 43, 9, 47], '44', None),
    ('garumna', 'Garumna', 'Garonne', ['Garonne'], None, '44', None),
    ('iberus', 'Iberus', 'Ebro', ['Ebro'], None, '44', '226 v. Chr.: Ebro-Grenze zwischen Rom und Karthago (Skript S. 68).'),
    ('tagus', 'Tagus', 'Tajo', ['Tajo', 'Tejo'], None, '44', None),
    ('baetis', 'Baetis', 'Guadalquivir', ['Guadalquivir'], None, '44', None),
    ('padus', 'Padus', 'Po', ['Po'], [6, 44, 13, 46], '44 f.', None),
    ('tiberis', 'Tiberis', 'Tiber', ['Tevere'], None, '44', None),
    ('dravus', 'Dravus', 'Drau', ['Drau'], None, '44', None),
    ('savus', 'Savus', 'Save', ['Sava'], None, '44', None),
    ('tisia', 'Tisia', 'Theiß', ['Tisa', 'Tisza'], None, '44', None),
    ('marisus', 'Marisus', 'Mureș (Marosch)', ['Mureș'], None, '44', None),
    ('alutus', 'Alutus', 'Olt', ['Olt'], None, '44', None),
    ('margus', 'Margus', 'Morava', ['Morava'], [19, 42, 23, 45], '44', None),
    ('hebrus', 'Hebros', 'Mariza (Evros)', ['Evros'], None, '44', None),
    ('nestus', 'Nestos', 'Mesta', ['Mesta'], None, '44', None),
    ('tyras', 'Tyras', 'Dnister', ['Dniester'], None, '44', None),
    ('borysthenes', 'Borysthenes', 'Dnepr', ['Dnipro', 'Dnepre'], None, '44', None),
    ('tamesis', 'Tamesis', 'Themse', ['Thames'], None, '44', None),
    ('halys', 'Halys', 'Kızılırmak', ['Kızılırmak'], None, '43', 'Grenze zwischen Lydern und Medern; nach dem Orakel bei Herodot (1,53) zerstörte Kroisos, als er den Halys überschritt, ein großes Reich – sein eigenes.'),
    ('sangarius', 'Sangarios', 'Sakarya', ['Sakarya'], None, '43', None),
    ('nilus', 'Nilus', 'Nil', ['Nile', 'Rosetta Branch', 'Damietta Branch'], [24, 15, 36, 32], '41, 44', 'Lebensader Ägyptens; Eratosthenes legte seinen Längenkreis bis Syene am Nil (Skript S. 41).'),
    ('euphrates', 'Euphrates', 'Euphrat', ['Euphrates', 'Al Furat', 'Firat'], None, '43, 45', 'Lange Grenze zwischen Rom und den Parthern bzw. Sasaniden.'),
    ('tigris', 'Tigris', 'Tigris', ['Tigris', 'Dicle'], None, '45', None),
    ('araxes', 'Araxes', 'Aras', ['Aras'], None, '45', None),
    ('kyros', 'Kyros', 'Kura', ['Kura'], None, '45', None),
    ('oxos', 'Oxos', 'Amudarja', ['Amu Darya', 'Panj'], None, '42, 45', None),
    ('iaxartes', 'Iaxartes', 'Syrdarja', ['Syr Darya'], None, '45', 'Am Iaxartes gründete Alexander „Alexandria Eschate“.'),
    ('indus', 'Indus', 'Indus', ['Indus'], None, '42, 45', None),
    ('hydaspes', 'Hydaspes', 'Jhelam', ['Jhelum'], None, '63', '326 v. Chr.: Schlacht am Hydaspes gegen Poros (Skript S. 63).'),
    ('hyphasis', 'Hyphasis', 'Beas', ['Beas'], None, '63', '326 v. Chr.: Umkehr am Hyphasis (Skript S. 63).'),
    ('etymandros', 'Etymandros', 'Hilmend', ['Helmand'], None, '45', None),
    # ergänzt: die großen Flüsse Chinas (Han-Reich)
    ('huanghe', 'Huang He', 'Gelber Fluss', ['Huang'], None, None, 'Kernland der chinesischen Reiche.'),
    ('jangtse', 'Chang Jiang', 'Jangtsekiang', ['Chang Jiang', 'Yangtze', 'Jinsha'], None, None, None),
]

# ---------- Gebirge ----------
# (id, antiker Name, heutiger Name, Natural-Earth-Namen, Skript-Seite oder None)
GEBIRGE = [
    ('alpes', 'Alpes', 'Alpen', ['ALPS'], '44'),
    ('apenninus', 'Apenninus', 'Apennin', ['APPENNINI'], '44'),
    ('pyrenaei', 'Pyrenaei montes', 'Pyrenäen', ['PYRENEES'], '44'),
    ('carpates', 'Carpates', 'Karpaten', ['CARPATHIAN MOUNTAINS'], '44'),
    ('carpates_s', 'Carpates', 'Südkarpaten', ['Transylvanian Alps'], '44'),
    ('taurus', 'Tauros', 'Taurus', ['Taurus Mts.'], '43 f.'),
    ('atlas', 'Atlas', 'Atlas', ['ATLAS MOUNTAINS'], '44'),
    ('paropamisos', 'Paropamisos', 'Hindukusch', ['HINDU KUSH'], '45'),
    ('imaos', 'Imaos (Emodos)', 'Himalaya', ['HIMALAYAS'], '41'),
    # ergänzt
    ('haemus', 'Haimos', 'Balkangebirge', ['Balkan Mts.'], None),
    ('caucasus', 'Kaukasos', 'Kaukasus', ['CAUCASUS MTS.'], None),
    ('zagros', 'Zagros', 'Zagros', ['ZAGROS MOUNTAINS'], None),
    ('pindos', 'Pindos', 'Pindos', ['Pindus Mts.'], None),
    ('libanos', 'Libanos', 'Libanon', ['Lebanon Mts.'], None),
]
# Gipfel: (id, antiker Name, heutiger Name, lon, lat, Skript-Seite oder None, Hinweis)
GIPFEL = [
    ('olympos', 'Olympos', 'Olymp', 22.35, 40.08, '44', 'Sitz der Götter.'),
    ('argaios', 'Argaios', 'Erciyes Dağı', 35.45, 38.53, '43', None),
    ('parnassos', 'Parnassos', 'Parnass', 22.61, 38.53, None, 'Über Delphi.'),
    ('vesuvius', 'Vesuvius', 'Vesuv', 14.43, 40.82, None, '79 n. Chr. Ausbruch, Pompeji und Herculaneum verschüttet.'),
    ('aetna', 'Aetna', 'Ätna', 14.99, 37.75, None, None),
]
# Meere und Meerengen: (id, antiker Name, heutiger Name, lon, lat, Stufe 1 = weit sichtbar, Skript-Seite oder None)
MEERE = [
    ('internum', 'Mare Internum („mare nostrum“)', 'Mittelmeer', 18.0, 34.2, 1, '45'),
    ('pontus', 'Pontos Euxeinos (Pontus Euxinus)', 'Schwarzes Meer', 34.0, 43.4, 1, '44'),
    ('caspium', 'Mare Caspium', 'Kaspisches Meer', 50.8, 42.2, 1, '45'),
    ('erythraeum', 'Erythräisches Meer', 'Indischer Ozean', 63.0, 15.5, 1, '42, 45'),
    ('oceanus', 'Okeanos (Oceanus)', 'Atlantischer Ozean', -15.0, 41.5, 1, '41'),
    ('aegaeum', 'Aigaion pelagos (Aegaeum mare)', 'Ägäis', 25.2, 38.9, 2, '43 f.'),
    ('adriaticum', 'Mare Adriaticum', 'Adria', 15.4, 43.1, 2, '45'),
    ('tuscum', 'Mare Tuscum (Tyrrhenum)', 'Tyrrhenisches Meer', 11.8, 40.0, 2, '45'),
    ('arabicus', 'Sinus Arabicus', 'Rotes Meer', 38.3, 20.8, 2, '44 f.'),
    ('persicus', 'Sinus Persicus', 'Persischer Golf', 51.2, 27.0, 2, '45'),
    ('ionium', 'Mare Ionium', 'Ionisches Meer', 18.6, 37.6, 2, None),
    ('propontis', 'Propontis', 'Marmarameer', 28.0, 40.72, 3, '43'),
    ('bosporus', 'Bosporos', 'Bosporus', 29.06, 41.12, 3, '42 f.'),
    ('hellespontos', 'Hellespontos', 'Dardanellen', 26.45, 40.2, 3, None),
    ('saeulen', 'Säulen des Herakles', 'Straße von Gibraltar', -5.6, 35.95, 2, '41'),
]
# Landschaften (Skript S. 42; Karten S. 43–45): (Name, lon, lat, Stufe 2 = mittlerer Zoom, 4 = ganz nah)
LANDSCHAFTEN = [
    # Westen und Norden (S. 42, Karte S. 44)
    ('Britannia', -1.8, 52.6, 2), ('Gallia', 2.4, 46.6, 2), ('Germania', 10.0, 51.6, 2), ('Hispania', -4.0, 40.0, 2),
    ('Italia', 12.6, 42.9, 2), ('Raetia', 10.4, 47.6, 4), ('Noricum', 14.2, 47.3, 4), ('Pannonia', 18.0, 46.7, 2),
    ('Dacia', 24.2, 46.2, 2), ('Moesia', 23.6, 43.5, 2), ('Thracia', 25.6, 42.1, 2), ('Dalmatia', 17.2, 44.0, 2),
    ('Macedonia', 22.2, 40.9, 2), ('Mauretania', -4.5, 33.5, 2), ('Numidia', 6.6, 35.6, 2), ('Africa', 9.6, 35.2, 2),
    ('Cyrenaica', 21.8, 32.1, 2), ('Aegyptus', 30.6, 27.0, 2),
    # Vorderasien und Osten (S. 42, Karten S. 43, 45)
    ('Syria', 37.6, 35.2, 2), ('Palaestina', 35.1, 31.4, 4), ('Arabia', 36.3, 30.3, 4), ('Mesopotamia', 40.8, 36.2, 2),
    ('Armenia', 42.6, 39.6, 2), ('Media', 48.8, 35.4, 2), ('Persis', 53.0, 29.6, 2), ('Parthia', 57.5, 37.0, 2),
    ('Hyrkania', 55.0, 37.2, 4), ('Baktria', 67.8, 36.9, 2), ('Sogdiana', 66.8, 39.6, 2), ('Choresmia', 60.2, 42.0, 4),
    ('Areia', 62.4, 34.6, 4), ('Margiana', 62.0, 37.6, 4), ('Arachosia', 65.8, 31.6, 4), ('Drangiana', 62.0, 31.2, 4),
    ('Gedrosia', 63.0, 26.6, 2), ('Karmania', 57.2, 28.2, 4), ('Gandhara', 72.0, 34.2, 4), ('Elymais', 49.0, 31.8, 4),
    ('Atropatene', 47.0, 37.9, 4), ('Adiabene', 43.6, 36.3, 4),
    # Kleinasien (S. 42, Karte S. 43)
    ('Troas', 26.4, 39.7, 4), ('Mysia', 27.9, 39.8, 4), ('Lydia', 28.3, 38.6, 4), ('Ionia', 27.25, 38.15, 4),
    ('Karia', 28.2, 37.3, 4), ('Lykia', 29.7, 36.6, 4), ('Pamphylia', 31.0, 37.0, 4), ('Phrygia', 30.9, 39.0, 4),
    ('Bithynia', 30.4, 40.6, 4), ('Paphlagonia', 33.6, 41.3, 4), ('Pontos', 36.9, 40.6, 4), ('Galatia', 33.0, 39.7, 4),
    ('Kappadokia', 35.6, 38.6, 4), ('Kilikia', 34.8, 36.95, 4), ('Kommagene', 38.0, 37.7, 4),
    # Griechenland (S. 42, Karte S. 43)
    ('Elis', 21.5, 37.75, 4), ('Messenien', 21.9, 37.15, 4), ('Lakonien', 22.6, 36.95, 4), ('Argolis', 22.85, 37.6, 4),
    ('Arkadien', 22.2, 37.55, 4), ('Achaia', 22.0, 38.12, 4), ('Attika', 23.85, 38.1, 4), ('Boiotien', 23.1, 38.4, 4),
    ('Phokis', 22.5, 38.62, 4), ('Aitolien', 21.5, 38.62, 4), ('Thessalien', 22.2, 39.5, 4), ('Epirus', 20.6, 39.6, 4),
    ('Euboia', 23.85, 38.62, 4),
    # Italien (S. 42, Karte S. 45)
    ('Gallia cisalpina', 10.0, 45.3, 4), ('Etruria', 11.3, 43.2, 4), ('Latium', 12.8, 41.75, 4), ('Samnium', 14.5, 41.45, 4),
    ('Campania', 14.4, 40.95, 4), ('Großgriechenland', 16.6, 39.6, 4), ('Sicilia', 14.2, 37.5, 4),
]


def rnd(pts, n=3): return [[round(x, n), round(y, n)] for x, y in pts]


def flussdaten():
    out = []
    for fid, name, heute, nen, rahmen, gk, hinweis in FLUESSE:
        linien = flusslinien(nen, rahmen)
        linien = [l.simplify(0.02) for l in linien if l.length > 0.15]
        d = dict(id=fid, name=name, heute=heute, pfade=[rnd(l.coords) for l in linien])
        if gk: d['gk'] = GK % gk
        if hinweis: d['hinweis'] = hinweis
        out.append(d)
    return out


def gebirgsdaten():
    out = []
    for gid, name, heute, nen, gk in GEBIRGE:
        flaechen = gebirgsflaeche(nen)
        kaemme = [kammlinie(f) for f in flaechen]
        haupt = max(kaemme, key=lambda k: k.length)
        mitte = haupt.interpolate(0.5, normalized=True)
        d = dict(id=gid, name=name, heute=heute, kaemme=[rnd(k.coords) for k in kaemme], lng=round(mitte.x, 2), lat=round(mitte.y, 2),
                 umriss=[rnd(list(f.simplify(0.05).exterior.coords) if f.geom_type == 'Polygon' else list(max(f.geoms, key=lambda p: p.area).simplify(0.05).exterior.coords), 2) for f in flaechen])
        if gk: d['gk'] = GK % gk
        out.append(d)
    return out


# ---------- natürliche Grenzlinien für build_grenzen.py ----------
# Flüsse, an denen Reichsgrenzen oft verliefen (auch solche ohne eigene Beschriftung), und Gebirgskämme.
GRENZFLUESSE = [
    (['Rhine', 'Rhein', 'Rhin'], [3, 46, 11, 53]), (['Danube', 'Donau'], None), (['Elbe'], None), (['Oder'], None), (['Vistula'], None),
    (['Euphrates', 'Al Furat', 'Firat'], None), (['Tigris', 'Dicle'], [38, 30, 48, 39]), (['Ebro'], None), (['Duero'], None), (['Tajo', 'Tejo'], None),
    (['Loire'], None), (['Rhône'], [3, 43, 9, 47]), (['Saône'], None), (['Maas'], None), (['Schelde'], None),
    (['Dnipro', 'Dnepre'], None), (['Don'], [36, 46, 45, 54]), (['Dniester'], None), (['Volga'], [40, 45, 52, 58]),
    (['Amu Darya', 'Panj'], None), (['Syr Darya'], None), (['Indus'], None), (['Kızılırmak'], None),
    (['Sava'], None), (['Drau'], None), (['Tisa', 'Tisza'], None), (['Morava'], [19, 42, 23, 45]), (['Prut'], None),
    (['Aras'], None), (['Kura'], None), (['Nile'], [29, 15, 34, 30]), (['Huang'], None), (['Chang Jiang', 'Yangtze'], None),
]
GRENZGEBIRGE = [['ALPS'], ['PYRENEES'], ['CARPATHIAN MOUNTAINS'], ['Transylvanian Alps'], ['CAUCASUS MTS.'], ['ZAGROS MOUNTAINS'],
                ['Taurus Mts.'], ['Balkan Mts.'], ['HINDU KUSH'], ['HIMALAYAS'], ['Sudetes Mts.'], ['Erzgebirge'], ['Böhmerwald'],
                ['Dinaric Alps'], ['ELBURZ MTS.'], ['Qinling Mountains'], ['Lesser Caucasus'], ['Kopet Dag Mts .'], ['PAMIRS'], ['TIAN SHAN']]


def grenzlinien():
    """Liste (art, LineString): natürliche Linien, an die build_grenzen.py Reichsgrenzen in ihrer Nähe anlegt."""
    out = []
    for nen, rahmen in GRENZFLUESSE:
        for l in flusslinien(nen, rahmen):
            l = l.simplify(0.02)
            if l.length > 0.3: out.append(('fluss', l))
    for nen in GRENZGEBIRGE:
        for f in gebirgsflaeche(nen):
            k = kammlinie(f)
            if k.length > 0.3: out.append(('kamm', k))
    return out


def main():
    daten = {
        '_hinweis': 'Historische Geographie. Erzeugt mit build_geographie.py. Verläufe: Natural Earth 1:10 Mio. (gemeinfrei); '
                    'Namen und Auswahl nach dem Grundkurs „Alte Geschichte“ (Skript FSU Jena, WS 2022/23), S. 41–45 und 63. '
                    'Heutige Flussläufe; Kammlinien = Mittelachse der Gebirgsumrisse (schematisch).',
        'quelle': 'Natural Earth (naturalearthdata.com, gemeinfrei); Namen: ' + GK % '41–45',
        'fluesse': flussdaten(),
        'gebirge': gebirgsdaten(),
        'gipfel': [dict(dict(id=i, name=n, heute=h, lng=x, lat=y), **({'gk': GK % s} if s else {}), **({'hinweis': t} if t else {})) for i, n, h, x, y, s, t in GIPFEL],
        'meere': [dict(dict(id=i, name=n, heute=h, lng=x, lat=y, stufe=st), **({'gk': GK % s} if s else {})) for i, n, h, x, y, st, s in MEERE],
        'landschaften': [dict(name=n, lng=x, lat=y, stufe=st) for n, x, y, st in LANDSCHAFTEN],
        'landschaften_quelle': GK % '42–45',
    }
    with io.open(ZIEL, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(daten, f, ensure_ascii=False, separators=(',', ':'))
    n = sum(len(p) for fl in daten['fluesse'] for p in fl['pfade'])
    print('Geographie:', len(daten['fluesse']), 'Flüsse (', n, 'Punkte),', len(daten['gebirge']), 'Gebirge,', len(daten['meere']), 'Meere,',
          len(daten['landschaften']), 'Landschaften ->', os.path.relpath(ZIEL, HERE), os.path.getsize(ZIEL), 'Bytes')


if __name__ == '__main__':
    main()
