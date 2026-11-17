# -*- coding: utf-8 -*-
"""Erzeugt img/earth-schematic.png: Globus-Textur für die schematische Ansicht (Plattkarte, 4096 x 2048).

Quelle: world-atlas 2.0.2, land-50m.json (Natural Earth, gemeinfrei; world-atlas unter ISC-Lizenz).
world-atlas ist Kugelgeometrie (einige Ringe überqueren die Datumsgrenze). Deshalb wird mit d3-geo
(vendor/d3.min.js) in einem Headless-Browser gezeichnet, der die Datumsgrenze korrekt schneidet.

    python build_schema_textur.py PFAD/land-50m.json

Benötigt: playwright (pip install playwright) und Microsoft Edge oder Chromium.
"""
import asyncio, base64, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'land-50m.json')
OUT = os.path.join(HERE, 'img', 'earth-schematic.png')
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# TopoJSON -> GeoJSON (Delta-Kodierung der Bögen auflösen; Ringe behalten ihre Kugel-Orientierung)
topo = json.load(open(SRC, encoding='utf-8'))
sx, sy = topo['transform']['scale']; tx, ty = topo['transform']['translate']
arcs = []
for arc in topo['arcs']:
    x = y = 0; pts = []
    for dx, dy in arc:
        x += dx; y += dy; pts.append([round(x * sx + tx, 5), round(y * sy + ty, 5)])
    arcs.append(pts)
def ring(idx):
    pts = []
    for i in idx:
        a = arcs[i] if i >= 0 else arcs[~i][::-1]
        pts.extend(a if not pts else a[1:])
    return pts
polys = []
for g in topo['objects']['land']['geometries']:
    if g['type'] == 'Polygon': polys.append([ring(r) for r in g['arcs']])
    elif g['type'] == 'MultiPolygon': polys.extend([[ring(r) for r in p] for p in g['arcs']])
land = {'type': 'MultiPolygon', 'coordinates': polys}
coast = {'type': 'MultiLineString', 'coordinates': [r for p in polys for r in p]}

JS = """([land, coast]) => {
  const W = 4096, H = 2048, SS = 2, c = document.createElement('canvas');
  c.width = W * SS; c.height = H * SS;
  const x = c.getContext('2d'); x.scale(SS, SS);
  const proj = d3.geoEquirectangular().scale(W / (2 * Math.PI)).translate([W / 2, H / 2]).precision(0.05);
  const path = d3.geoPath(proj, x);
  x.fillStyle = '#8fb8d0'; x.fillRect(0, 0, W, H);
  x.beginPath(); path(d3.geoGraticule().step([15, 15]).extent([[-180, -90], [180, 90.001]])());
  x.strokeStyle = 'rgba(255,255,255,0.22)'; x.lineWidth = 1.2; x.stroke();
  x.beginPath(); path(land); x.fillStyle = '#e7dcc0'; x.fill();
  x.beginPath(); path(coast); x.lineJoin = 'round'; x.strokeStyle = 'rgba(110,98,70,0.75)'; x.lineWidth = 1.4; x.stroke();
  const o = document.createElement('canvas'); o.width = W; o.height = H;
  const ox = o.getContext('2d'); ox.imageSmoothingQuality = 'high'; ox.drawImage(c, 0, 0, W, H);
  return o.toDataURL('image/png');
}"""

async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = {'executable_path': EDGE} if os.path.exists(EDGE) else {}
        b = await p.chromium.launch(**kw)
        pg = await b.new_page()
        await pg.add_script_tag(path=os.path.join(HERE, 'vendor', 'd3.min.js'))
        url = await pg.evaluate(JS, [land, coast])
        await b.close()
    open(OUT, 'wb').write(base64.b64decode(url.split(',', 1)[1]))
    print('geschrieben:', OUT, os.path.getsize(OUT), 'Bytes')

asyncio.run(main())
