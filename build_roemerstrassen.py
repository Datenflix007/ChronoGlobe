# -*- coding: utf-8 -*-
"""Erzeugt data/roemerstrassen.json (Layer „Römische Straßen“) aus dem Datensatz Itiner-e.

Quelle: Pau de Soto, Adam Pažout, Tom Brughmans u. a., Itiner-e. A high-resolution dataset of roads
of the Roman Empire, in: Scientific Data 12 (2025), Nr. 1731, DOI 10.1038/s41597-025-06140-z.
Daten: Itiner-e static version 2024, Zenodo, DOI 10.5281/zenodo.17122148, Lizenz CC BY 4.0.

Download (78 MB, nicht im Repo):
  https://zenodo.org/records/17122148/files/itinere_roads.geojson?download=1
Aufruf:  python build_roemerstrassen.py <pfad/zu/itinere_roads.geojson>

Verarbeitung: nur „Main Road“ (Hauptstraßen), ohne Wasserwege; Rückrechnung aus World Mercator
(EPSG:3395, WGS84-Ellipsoid) in Grad; Vereinfachung (Douglas-Peucker, ca. 3 km); aneinander
anschließende Abschnitte werden zu längeren Linien verkettet (weniger Objekte auf dem Globus).
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
A = 6378137.0
E = 0.0818191908426215          # Exzentrizität WGS84
TOL = 0.03                       # Grad (~3 km)


def inv_merc(x, y):
    lng = math.degrees(x / A)
    t = math.exp(-y / A)
    phi = math.pi / 2 - 2 * math.atan(t)
    for _ in range(8):
        es = E * math.sin(phi)
        phi = math.pi / 2 - 2 * math.atan(t * ((1 - es) / (1 + es)) ** (E / 2))
    return [round(lng, 3), round(math.degrees(phi), 3)]


def dp(pts, tol):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1e-12
    imax, dmax = 0, -1
    for i in range(1, len(pts) - 1):
        d = abs(dy * pts[i][0] - dx * pts[i][1] + b[0] * a[1] - b[1] * a[0]) / n
        if d > dmax: imax, dmax = i, d
    if dmax <= tol: return [a, b]
    return dp(pts[:imax + 1], tol)[:-1] + dp(pts[imax:], tol)


def key(p): return (round(p[0], 2), round(p[1], 2))


def main(src):
    g = json.load(open(src, encoding='utf-8'))
    segs, skipped = [], 0
    for f in g['features']:
        p = f['properties']
        if p.get('Type') != 'Main Road':
            continue
        if 'Waterway' in (p.get('Citation') or '') or 'river' in (p.get('Name') or '').lower():
            skipped += 1; continue
        for line in f['geometry']['coordinates']:
            pts = dp([inv_merc(c[0], c[1]) for c in line], TOL)
            if len(pts) >= 2:
                # zwei Klassen: H = vermutet (Hypothetical), S = gesichert oder erschlossen
                segs.append({'n': p.get('Name') or '', 's': 'H' if p.get('Segment_s') == 'Hypothetical' else 'S', 'p': pts})
    # Verkettung: an jedem Knoten mit irgendeinem freien Abschnitt derselben Klasse weiter (jeder Abschnitt nur einmal)
    ends = {}
    for i, s in enumerate(segs):
        for e in (key(s['p'][0]), key(s['p'][-1])):
            ends.setdefault(e, []).append(i)
    used, lines = [False] * len(segs), []
    def grow(line, cert):
        while True:
            k = key(line[-1]); cand = [j for j in ends.get(k, []) if not used[j] and segs[j]['s'] == cert]
            if not cand: return line
            j = cand[0]; used[j] = True; q = segs[j]['p']
            line += (q if key(q[0]) == k else q[::-1])[1:]
    for i, s in enumerate(segs):
        if used[i]: continue
        used[i] = True
        fwd = grow(list(s['p']), s['s'])
        back = grow(list(reversed(fwd)), s['s'])
        lines.append({'s': s['s'], 'p': dp(back, TOL)})
    out = {
        '_quelle': 'Itiner-e static version 2024 (de Soto/Pažout/Brughmans u. a., Scientific Data 12, 2025), Zenodo DOI 10.5281/zenodo.17122148, CC BY 4.0. Nur Hauptstraßen, vereinfacht und verkettet.',
        'lizenz': 'CC BY 4.0',
        'stand': 'Straßennetz zur Zeit der größten Ausdehnung (um 150 n. Chr.)',
        'sicherheit': {'S': 'Certain/Conjectured (gesichert oder erschlossen)', 'H': 'Hypothetical (vermutet)'},
        'linien': [{'s': l['s'], 'p': l['p']} for l in lines],
    }
    dst = os.path.join(HERE, 'data', 'roemerstrassen.json')
    with open(dst, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(',', ':'))
    npts = sum(len(l['p']) for l in lines)
    print('Abschnitte: %d (Wasserwege übersprungen: %d) -> Linien: %d, Punkte: %d, Datei: %.0f KB'
          % (len(segs), skipped, len(lines), npts, os.path.getsize(dst) / 1024))


if __name__ == '__main__':
    main(sys.argv[1])
