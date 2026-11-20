"""Satelliten-Kacheln für den Globus (Web-Mercator, 256 px, Schema img/tiles/{z}/{x}/{y}.jpg).

Quelle: NASA Earth Observatory, Blue Marble Next Generation w/ Topography and Bathymetry, Juli 2004 (gemeinfrei).
  - Stufe 6 (weltweit) aus world.topo.bathy.200407.3x21600x10800.jpg (ca. 2 km/Pixel)
  - Stufen 7 und 8 (nur REGION) aus den 500-m-Teilbildern world.topo.bathy.200407.3x21600x21600.{B1,B2,C1,C2,D1,D2}.jpg
Download: https://visibleearth.nasa.gov/ (Dateiserver assets.science.nasa.gov, .../bmng-topography-bathymetry/july/)

Aufruf:  python build_kacheln.py <ordner-mit-quellbildern> [stufen, z. B. 6,7,8]
Die Region muss mit KACHELN in js/app.js übereinstimmen.
Benötigt: numpy, Pillow. Die 500-m-Teilbilder werden einmalig als .npy (je 1,4 GB) neben die Quellen entpackt.
"""
import math, os, sys
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
REGION = (-20.0, -15.0, 150.0, 62.0)          # lng_min, lat_min, lng_max, lat_max
STUFEN_REGION = (7, 8)
ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img', 'tiles')
QUALI = 80
T = 256


def tile_range(z, box):
    n = 2 ** z
    def tx(lng): return min(n - 1, max(0, int(math.floor((lng + 180) / 360 * n))))
    def ty(lat):
        r = math.radians(lat)
        return min(n - 1, max(0, int(math.floor((1 - math.asinh(math.tan(r)) / math.pi) / 2 * n))))
    return tx(box[0]), tx(box[2]), ty(box[3]), ty(box[1])   # x0, x1, y0, y1


class Global2k:
    """21600×10800, komplett im Speicher"""
    def __init__(self, pfad):
        self.a = np.asarray(Image.open(pfad).convert('RGB'))
        self.H, self.W = self.a.shape[:2]

    def patch(self, x0, y0, x1, y1):
        x0, x1 = max(0, x0), min(self.W, x1); y0, y1 = max(0, y0), min(self.H, y1)
        return self.a[y0:y1, x0:x1], x0, y0


class Mosaik500:
    """86400×43200 aus Teilbildern (Spalten A..D = 180°W..90°E, Zeilen 1/2 = Nord/Süd), per Memmap"""
    S = 21600

    def __init__(self, ordner):
        self.W, self.H = 4 * self.S, 2 * self.S
        self.m = {}
        for c, col in enumerate('ABCD'):
            for r in (1, 2):
                jpg = os.path.join(ordner, '%s%d.jpg' % (col, r))
                npy = jpg[:-4] + '.npy'
                if not os.path.exists(jpg) and not os.path.exists(npy):
                    continue
                if not os.path.exists(npy):
                    print('entpacke', jpg, flush=True)
                    a = np.asarray(Image.open(jpg).convert('RGB'))
                    mm = np.lib.format.open_memmap(npy, mode='w+', dtype=np.uint8, shape=a.shape)
                    mm[:] = a; mm.flush(); del mm, a
                self.m[(c, r - 1)] = np.load(npy, mmap_mode='r')

    def patch(self, x0, y0, x1, y1):
        x0, x1 = max(0, x0), min(self.W, x1); y0, y1 = max(0, y0), min(self.H, y1)
        out = np.zeros((y1 - y0, x1 - x0, 3), np.uint8)
        for (c, r), a in self.m.items():
            ax0, ay0 = c * self.S, r * self.S
            ix0, ix1 = max(x0, ax0), min(x1, ax0 + self.S)
            iy0, iy1 = max(y0, ay0), min(y1, ay0 + self.S)
            if ix0 < ix1 and iy0 < iy1:
                out[iy0 - y0:iy1 - y0, ix0 - x0:ix1 - x0] = a[iy0 - ay0:iy1 - ay0, ix0 - ax0:ix1 - ax0]
        return out, x0, y0


def kachel(src, z, x, y, ss):
    """Eine Kachel: je Ausgabepixel ss×ss Unterabtastungen, bilinear, gemittelt"""
    n = 2 ** z
    k = (np.arange(T * ss) + 0.5) / ss
    X = (x * T + k) / (T * n)
    Y = (y * T + k) / (T * n)
    lng = X * 360 - 180
    lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * Y))))
    sx = (lng + 180) / 360 * src.W - 0.5
    sy = (90 - lat) / 180 * src.H - 0.5
    px0, px1 = int(math.floor(sx.min())) - 1, int(math.ceil(sx.max())) + 2
    py0, py1 = int(math.floor(sy.min())) - 1, int(math.ceil(sy.max())) + 2
    p, ox, oy = src.patch(px0, py0, px1, py1)
    p = p.astype(np.float32)
    fx = np.clip(sx - ox, 0, p.shape[1] - 1.001); fy = np.clip(sy - oy, 0, p.shape[0] - 1.001)
    ix, iy = np.floor(fx).astype(int), np.floor(fy).astype(int)
    wx, wy = (fx - ix)[None, :, None], (fy - iy)[:, None, None]
    a = p[iy][:, ix]; b = p[iy][:, ix + 1]; c = p[iy + 1][:, ix]; d = p[iy + 1][:, ix + 1]
    v = (a * (1 - wx) + b * wx) * (1 - wy) + (c * (1 - wx) + d * wx) * wy
    v = v.reshape(T, ss, T, ss, 3).mean(axis=(1, 3))
    return Image.fromarray(np.clip(v + 0.5, 0, 255).astype(np.uint8))


def baue(src, z, box, ss):
    x0, x1, y0, y1 = tile_range(z, box)
    gesamt, i = (x1 - x0 + 1) * (y1 - y0 + 1), 0
    print('Stufe %d: x %d–%d, y %d–%d, %d Kacheln' % (z, x0, x1, y0, y1, gesamt), flush=True)
    for x in range(x0, x1 + 1):
        os.makedirs(os.path.join(ZIEL, str(z), str(x)), exist_ok=True)
        for y in range(y0, y1 + 1):
            kachel(src, z, x, y, ss).save(os.path.join(ZIEL, str(z), str(x), '%d.jpg' % y), 'JPEG', quality=QUALI, optimize=True)
            i += 1
        if x % 8 == 0:
            print('  %d/%d' % (i, gesamt), flush=True)


if __name__ == '__main__':
    ordner = sys.argv[1]
    stufen = [int(s) for s in (sys.argv[2] if len(sys.argv) > 2 else '6,7,8').split(',')]
    if 6 in stufen:
        baue(Global2k(os.path.join(ordner, 'world.topo.bathy.200407.jpg')), 6, (-180, -85.05, 180, 85.05), 2)
    if any(z in STUFEN_REGION for z in stufen):
        m = Mosaik500(ordner)
        for z in STUFEN_REGION:
            if z in stufen:
                baue(m, z, REGION, 3 if z == 7 else 2)
