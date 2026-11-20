# -*- coding: utf-8 -*-
"""Schiffsverkehr im Römischen Reich aus ORBIS (data/orbis_schiff.json).

Quelle: ORBIS – The Stanford Geospatial Network Model of the Roman World (W. Scheidel, E. Meeks), Daten aus dem
GitHub-Repository emeeks/orbis_v2 (Lizenz MIT): base_routes.geojson (Strecken), sites_extended.csv (Orte).

Übernommen werden nur die Schiffsstrecken (t = coastal, overseas, ferry, upstream, downstream), nicht die Straßen
(die liefert Itiner-e, siehe docs/STRASSEN_ZEITMODELL.md). Stromauf- und Stromab-Strecken zwischen denselben Orten
werden zu einer Flussstrecke zusammengefasst.

ORBIS bildet das Netz um 200 n. Chr. ab und enthält KEINE Jahreszahlen. Damit die Ebene zur Zeitleiste passt, wird
jede Strecke an das römische Gebiet gekoppelt: Sie gilt in den Jahren als sichtbar, in denen BEIDE Endpunkte in einer
römischen Fläche aus data/reiche.json liegen (Puffer PUFFER Grad, weil Häfen an der Küste oft knapp außerhalb der
vereinfachten Flächen liegen). Das ist eine Darstellungsregel, kein Beleg für den Beginn des Verkehrs.

    python build_orbis.py <ordner mit base_routes.geojson und sites_extended.csv>
"""
import csv, io, json, math, os, sys
from shapely.geometry import LineString, Point, shape
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HERE, 'data', 'orbis_schiff.json')
PUFFER = 0.3          # Grad: Hafen gilt als römisch, wenn er so nah an einer römischen Fläche liegt
VEREINFACHUNG = 0.01  # Grad
ART = {'coastal': 'kueste', 'overseas': 'hochsee', 'ferry': 'faehre', 'upstream': 'fluss', 'downstream': 'fluss'}
ANTIKE_BIS = 480


def lade_orte(ordner):
    t = io.open(os.path.join(ordner, 'sites_extended.csv'), encoding='utf-8', errors='replace').read().replace('\r', '\n')
    return {int(r['id']): r for r in csv.DictReader(io.StringIO(t))}


def roemische_flaechen():
    d = json.load(open(os.path.join(HERE, 'data', 'reiche.json'), encoding='utf-8'))
    out = []
    for f in d['regionen']:
        p = f['properties']
        if p['reich'] == 'rom' and p['von'] < ANTIKE_BIS:
            out.append((shape(f['geometry']).buffer(PUFFER), p['von'], min(p['bis'], ANTIKE_BIS + 1)))
    return out


def vereinigen(iv):
    iv = sorted(iv); out = []
    for a, b in iv:
        if out and a <= out[-1][1]: out[-1][1] = max(out[-1][1], b)
        else: out.append([a, b])
    return out


def schneiden(x, y):
    out = []
    for a, b in x:
        for c, d in y:
            lo, hi = max(a, c), min(b, d)
            if lo < hi: out.append([lo, hi])
    return vereinigen(out)


def main(ordner):
    orte = lade_orte(ordner)
    routen = json.load(open(os.path.join(ordner, 'base_routes.geojson'), encoding='utf-8'))['features']
    fl = roemische_flaechen()
    baum = STRtree([g for g, _, _ in fl])
    ort_pts = [(float(r['x']), float(r['y']), r['label']) for r in orte.values()]

    def zeiten(pt):
        p = Point(pt)
        return vereinigen([[fl[int(i)][1], fl[int(i)][2]] for i in baum.query(p) if fl[int(i)][0].contains(p)])

    def name(oid, pt):
        r = orte.get(oid % 100000)
        if r: return r['label']
        return min(ort_pts, key=lambda q: math.hypot(q[0] - pt[0], q[1] - pt[1]))[2]

    gesehen, out, stat = set(), [], {}
    for f in routen:
        p = f['properties']
        art = ART.get(p['t'])
        if not art: continue
        a, b = p['sid'] % 100000, p['tid'] % 100000
        schl = (min(a, b), max(a, b), art)
        if schl in gesehen: continue
        gesehen.add(schl)
        g = f['geometry']
        teile = [g['coordinates']] if g['type'] == 'LineString' else g['coordinates']
        pts = [c for t in teile for c in t]
        if len(pts) < 2: continue
        lin = LineString(pts).simplify(VEREINFACHUNG)
        z = schneiden(zeiten(pts[0]), zeiten(pts[-1]))
        if not z: continue   # nie in römischer Hand (z. B. außerhalb des Reichs)
        out.append({'id': 'orbis-%d' % p['gid'], 'art': art, 'von_ort': name(p['sid'], pts[0]), 'nach_ort': name(p['tid'], pts[-1]),
                    'zeiten': z, 'p': [[round(x, 3), round(y, 3)] for x, y in lin.coords]})
        stat[art] = stat.get(art, 0) + 1
    daten = {
        '_quelle': 'ORBIS – The Stanford Geospatial Network Model of the Roman World (Walter Scheidel, Elijah Meeks); '
                   'Daten: github.com/emeeks/orbis_v2 (base_routes.geojson, sites_extended.csv)',
        'lizenz': 'MIT (Repository emeeks/orbis_v2)',
        'stand': 'ORBIS-Netz um 200 n. Chr., ohne Jahreszahlen',
        'zeitregel': 'zeiten = Jahre [von, bis), in denen beide Endpunkte in einer römischen Fläche aus data/reiche.json liegen '
                     '(Puffer %.2f°); Darstellungsregel, kein Beleg' % PUFFER,
        'arten': {'kueste': 'Küstenschifffahrt', 'hochsee': 'Hochseeroute', 'faehre': 'Fähre', 'fluss': 'Flussschifffahrt'},
        'routen': out,
    }
    with io.open(ZIEL, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(daten, f, ensure_ascii=False, separators=(',', ':'))
    print('Schiffsstrecken:', len(out), stat, 'Punkte:', sum(len(r['p']) for r in out), 'Bytes:', os.path.getsize(ZIEL))


if __name__ == '__main__':
    main(sys.argv[1])
