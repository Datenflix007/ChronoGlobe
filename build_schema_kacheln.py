# -*- coding: utf-8 -*-
"""Schematische Ansicht in hoher Auflösung:
  - img/earth-schematic-8k.png   Grundkugel (Plattkarte 8192 × 4096)
  - img/tiles_schem/{z}/{x}/{y}.png   Kacheln für die Nahansicht (Web-Mercator, 256 px), gleiche Abdeckung wie die
    Satelliten-Kacheln (build_kacheln.py): Stufe 6 weltweit bis ±72°, Stufen 7–8 in der REGION.

Quelle: world-atlas 2.0.2, land-10m.json (Natural Earth 1:10 Mio., gemeinfrei; world-atlas unter ISC-Lizenz).
Download: https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/land-10m.json

    python build_schema_kacheln.py PFAD/land-10m.json [basis|kacheln|alles]

Benötigt: numpy, Pillow. Farben wie build_schema_textur.py (4096er-Fassung, bleibt als Rückfall).
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
REGION = (-20.0, -15.0, 150.0, 62.0)      # wie build_kacheln.py und KACHELN in js/app.js
STUFEN_REGION = (7, 8)
POLAR = 72.0
MEER, LAND, KUESTE, NETZ = (143, 184, 208), (231, 220, 192), (110, 98, 70, 190), (255, 255, 255, 56)
T, SS = 256, 3

# ---------- TopoJSON -> Ringe (lon/lat), über die Datumsgrenze „abgewickelt“ ----------
def lade(pfad):
    topo = json.load(open(pfad, encoding='utf-8'))
    sx, sy = topo['transform']['scale']; tx, ty = topo['transform']['translate']
    arcs = []
    for arc in topo['arcs']:
        a = np.cumsum(np.array(arc, dtype=np.float64), axis=0)
        arcs.append(np.column_stack([a[:, 0] * sx + tx, a[:, 1] * sy + ty]))
    def ring(idx):
        teile = []
        for i in idx:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            teile.append(a if not teile else a[1:])
        return np.vstack(teile)
    polys = []
    for g in topo['objects']['land']['geometries']:
        ps = [g['arcs']] if g['type'] == 'Polygon' else g['arcs']
        for p in ps:
            polys.append([abwickeln(ring(r)) for r in p])
    return polys

def abwickeln(r):
    lng = r[:, 0].copy()
    d = np.diff(lng)
    off = np.concatenate([[0], np.cumsum(np.where(d > 180, -360, np.where(d < -180, 360, 0)))])
    lng = lng + off
    r = np.column_stack([lng, r[:, 1]])
    spann = lng[-1] - lng[0]
    if abs(spann) > 180:   # Ring um einen Pol (Antarktis): über den Pol schließen
        pol = -90.0 if r[:, 1].mean() < 0 else 90.0
        r = np.vstack([r, [[lng[-1], pol], [lng[0], pol]]])
    return r

def bbox(r): return (r[:, 0].min(), r[:, 0].max(), r[:, 1].min(), r[:, 1].max())

# ---------- Zeichnen ----------
def merc_y(lat):
    lat = np.clip(lat, -85.0511, 85.0511)
    return (1 - np.arcsinh(np.tan(np.radians(lat))) / np.pi) / 2

def male(img_size, proj, polys, box_lnglat, netz_px, kueste_px, netz_proj):
    """proj(lng, lat) -> (x, y) Pixel im Überabtastungsbild; box_lnglat = (l0, l1, b0, b1) Sichtbereich"""
    W, H = img_size
    im = Image.new('RGB', (W, H), MEER)
    dr = ImageDraw.Draw(im, 'RGBA')
    for (gx, gy) in netz_proj():
        dr.line(list(zip(gx, gy)), fill=NETZ, width=netz_px)
    l0, l1, b0, b1 = box_lnglat
    linien = []
    for poly in polys:
        for k, r in enumerate(poly):
            bb = poly_bb[id(r)]
            for o in (-360.0, 0.0, 360.0):
                if bb[1] + o < l0 or bb[0] + o > l1 or bb[3] < b0 or bb[2] > b1:
                    continue
                x, y = proj(r[:, 0] + o, r[:, 1])
                pts = list(zip(x.tolist(), y.tolist()))
                if len(pts) < 3: continue
                dr.polygon(pts, fill=LAND if k == 0 else MEER)
                linien.append(pts)
    for pts in linien:
        dr.line(pts + pts[:1], fill=KUESTE, width=kueste_px, joint='curve')
    return im

poly_bb = {}

def basis(polys, ziel):
    W, H, ss = 8192, 4096, 2
    def proj(lng, lat): return (lng + 180) / 360 * W * ss, (90 - lat) / 180 * H * ss
    def netz():
        for lng in range(-180, 181, 15):
            yield [((lng + 180) / 360 * W * ss)] * 2, [0, H * ss]
        for lat in range(-75, 76, 15):
            yield [0, W * ss], [((90 - lat) / 180 * H * ss)] * 2
    im = male((W * ss, H * ss), proj, polys, (-540, 540, -90, 90), 3, 3, netz)
    im = im.resize((W, H), Image.LANCZOS)
    im.quantize(colors=64, method=Image.Quantize.MEDIANCUT).save(ziel, optimize=True)
    print('Basis:', ziel, round(os.path.getsize(ziel) / 1e6, 2), 'MB')

def tile_range(z, box):
    n = 2 ** z
    def tx(lng): return min(n - 1, max(0, int(math.floor((lng + 180) / 360 * n))))
    def ty(lat): return min(n - 1, max(0, int(math.floor((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n))))
    return tx(box[0]), tx(box[2]), ty(box[3]), ty(box[1])

def kachel(polys, z, x, y):
    n = 2 ** z
    S = T * SS
    def proj(lng, lat): return ((lng + 180) / 360 * n - x) * S, (merc_y(lat) * n - y) * S
    l0, l1 = x / n * 360 - 180, (x + 1) / n * 360 - 180
    def lat_of(yy): return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * yy / n))))
    b1, b0 = lat_of(y), lat_of(y + 1)
    pad = (l1 - l0) * 0.05
    def netz():
        for lng in range(-180, 181, 15):
            if l0 - pad <= lng <= l1 + pad:
                px = ((lng + 180) / 360 * n - x) * S
                yield [px, px], [0, S]
        for lat in range(-75, 76, 15):
            if b0 - pad <= lat <= b1 + pad:
                py = (merc_y(np.array(lat)) * n - y) * S
                yield [0, S], [float(py)] * 2
    im = male((S, S), proj, polys, (l0 - pad, l1 + pad, b0 - pad, b1 + pad), 3, 4, netz)
    return im.resize((T, T), Image.LANCZOS)

_POLYS = None
def _init(pfad):
    global _POLYS
    _POLYS = lade(pfad)
    for p in _POLYS:
        for r in p: poly_bb[id(r)] = bbox(r)

def _spalte(args):
    z, x, y0, y1, ziel = args
    os.makedirs(os.path.join(ziel, str(z), str(x)), exist_ok=True)
    for y in range(y0, y1 + 1):
        kachel(_POLYS, z, x, y).quantize(colors=32, method=Image.Quantize.MEDIANCUT).save(
            os.path.join(ziel, str(z), str(x), '%d.png' % y), optimize=True)
    return y1 - y0 + 1

def baue_stufe(pfad, z, box, ziel):
    """parallel: eine Aufgabe je Kachelspalte"""
    from multiprocessing import Pool
    x0, x1, y0, y1 = tile_range(z, box)
    ges = (x1 - x0 + 1) * (y1 - y0 + 1); i = 0
    print('Stufe %d: %d Kacheln' % (z, ges), flush=True)
    with Pool(os.cpu_count(), initializer=_init, initargs=(pfad,)) as pool:
        for k in pool.imap_unordered(_spalte, [(z, x, y0, y1, ziel) for x in range(x0, x1 + 1)]):
            i += k
            if i % 500 < k: print('  %d/%d' % (i, ges), flush=True)

if __name__ == '__main__':
    polys = lade(sys.argv[1])
    for p in polys:
        for r in p: poly_bb[id(r)] = bbox(r)
    was = sys.argv[2] if len(sys.argv) > 2 else 'alles'
    if was in ('basis', 'alles'):
        basis(polys, os.path.join(HERE, 'img', 'earth-schematic-8k.png'))
    if was in ('kacheln', 'alles') or was.isdigit():
        ziel = os.path.join(HERE, 'img', 'tiles_schem')
        stufen = [int(was)] if was.isdigit() else [6] + list(STUFEN_REGION)
        for z in stufen:
            baue_stufe(sys.argv[1], z, REGION if z in STUFEN_REGION else (-180, -POLAR, 180, POLAR), ziel)
