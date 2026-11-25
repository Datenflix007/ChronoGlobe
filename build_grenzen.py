# -*- coding: utf-8 -*-
"""Bereinigt die Reichsflächen aller Epochen gemeinsam (data/reiche.json, data/fruehe_reiche.json, data/mittelalter_reiche.json).

Die Flächen sind von Hand gezeichnete Umrisse. Weil drei Skripte sie unabhängig erzeugen, überlappten sich gleichzeitige
Reiche, zwischen Nachbarn blieben schmale weiße Streifen, und Grenzen liefen schnurgerade quer zu Flüssen und Gebirgen.
Dieses Skript läuft NACH build_reiche.py, build_fruehe_kulturen.py und build_mittelalter.py und schreibt die drei Dateien
zurück:

1. Natürliche Grenzen: Liegt eine Grenze nahe (≤ BAND Grad) an einem großen Fluss oder Gebirgskamm (build_geographie.py:
   grenzlinien), wird sie an diese Linie gelegt. Dazu wird ein Saum beiderseits der Linie in kurze Stücke geteilt; jedes
   Stück gehört ganz zu dem Reich, das es schon überwiegend bedeckt. Nachbarn treffen sich so genau auf der Linie.
2. Lücken: Schmale Streifen Land (≤ LUECKE Grad) zwischen zwei gleichzeitigen Reichen werden zwischen beiden geteilt.
   Große unbesetzte Räume bleiben leer – dort ist kein Reich belegt (Grenzzonen, Steppen, Wüsten).
3. Überlappungen: Gleichzeitige Flächen dürfen sich nicht überdecken (sonst flimmern sie, und die Karte behauptet doppelte
   Herrschaft). Vorrang haben Rom und Han (Hauptreiche der Tafelbilder), sonst die kleinere, genauer gezeichnete Fläche.
   Die unterlegene Fläche verliert das Gebiet nur für die Jahre der Überschneidung (Zeitabschnitte werden geteilt).
   Oberhoheit (Tribut, Lehnshoheit) steht im Text, nicht als zweite Fläche. Flächen der Art „einfluss“ bleiben unberührt.
4. Küsten: alles exakt an data/land.json beschnitten (vorher teils 0,08° ins Meer gepuffert).

Immer auf frisch erzeugten Dateien ausführen (nach den drei build-Skripten); ein zweiter Lauf auf schon bereinigten
Daten ändert durch Rundung und Vereinfachung noch Kleinigkeiten.

    python build_grenzen.py            Flächen bereinigen und Bericht ausgeben
    python build_grenzen.py --pruefen  nur prüfen (Rückgabewert 1 bei Überlappungen; schmale Lücken werden nur gemeldet,
                                       denn manche sind historisch richtig: dort ist kein Reich belegt)
"""
import io, json, os, sys
from shapely import set_precision
from shapely.geometry import LineString, MultiPolygon, Polygon, mapping, shape
from shapely.geometry.polygon import orient
from shapely.ops import split, substring, unary_union
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
DATEIEN = ['reiche.json', 'fruehe_reiche.json', 'mittelalter_reiche.json']
HAUPT = ['rom', 'han']          # gewinnen immer (Tafelbilder sind um sie gebaut)
BAND = 0.35                      # Saum um natürliche Linien (Grad)
STUECK = 0.6                     # Länge der Saumstücke entlang der Linie (Grad)
LUECKE = 1.0                     # schmalere Lücken zwischen Nachbarn werden geschlossen (Grad)
MIN_FLAECHE = 0.004              # kleinere Splitter fallen weg (Grad²)
VEREINFACHEN = 0.015            # Toleranz beim Schreiben (Grad, ≈ 1,5 km)
RASTER = 0.01                    # Koordinatenraster beim Schreiben (Grad)
KLEINE_UEB = 0.15               # kleinere Überschneidungen werden ohne Zeitteilung abgezogen (Grad²)
KLEIN = 1.5                      # kleinere Flächen (Stadtstaaten, Inseln) werden nicht an Linien angelegt (Grad²)

if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')


def laden():
    daten = {d: json.load(io.open(os.path.join(HERE, 'data', d), encoding='utf-8')) for d in DATEIEN}
    land = shape(json.load(io.open(os.path.join(HERE, 'data', 'land.json'), encoding='utf-8'))['geometry']).buffer(0)
    return daten, land


def flaechen(daten):
    """Alle Kern-Flächen als Liste von dicts: datei, f (Feature), g (shapely), von, bis."""
    out = []
    for d, dat in daten.items():
        for f in dat['regionen']:
            p = f['properties']
            if p.get('art', 'kern') != 'kern': continue
            out.append(dict(datei=d, f=f, g=shape(f['geometry']).buffer(0), von=p['von'], bis=p['bis']))
    return out


def gleichzeitig(a, b): return a['von'] < b['bis'] and b['von'] < a['bis']


def ueberlappung_jahre(a, b): return max(0, min(a['bis'], b['bis']) - max(a['von'], b['von']))


def sauber(g):
    g = set_precision(g.buffer(0), 0.001)
    teile = [p for p in getattr(g, 'geoms', [g]) if p.geom_type == 'Polygon' and p.area >= MIN_FLAECHE]
    return unary_union(teile) if teile else Polygon()


# ---------- 1. natürliche Grenzen ----------
def _verlaengert(l, d):
    """Linie an beiden Enden in Fortsetzungsrichtung um d verlängern (damit sie den Saum ganz durchschneidet)."""
    p = list(l.coords)
    def weiter(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]; n = (dx * dx + dy * dy) ** 0.5 or 1
        return (b[0] + dx / n * d, b[1] + dy / n * d)
    return LineString([weiter(p[1], p[0])] + p + [weiter(p[-2], p[-1])])


def saumstuecke(linien, land):
    stuecke = []
    for art, l in linien:
        n = max(1, int(round(l.length / STUECK)))
        for i in range(n):
            s = substring(l, i / n, (i + 1) / n, normalized=True)
            if s.geom_type != 'LineString' or s.length < 0.05: continue
            saum = s.buffer(BAND, cap_style='flat')
            try: teile = split(saum, _verlaengert(s, BAND * 2)).geoms
            except Exception: continue
            for t in teile:
                t = t.intersection(land)
                if t.area > 0.002: stuecke.append(t)
    return stuecke


def anlegen(g, baum, stuecke):
    rand = g.boundary
    for i in baum.query(rand):
        st = stuecke[i]
        if not st.intersects(rand): continue
        anteil = g.intersection(st).area / st.area
        g = g.union(st) if anteil >= 0.5 else g.difference(st)
    return g


# ---------- 2. Lücken ----------
def nur_flaeche(g):
    """Nur Flächenanteile (Überschneidungen liefern sonst teils Linien und Punkte)."""
    teile = [p for p in getattr(g, 'geoms', [g]) if p.geom_type in ('Polygon', 'MultiPolygon') and not p.is_empty]
    return set_precision(unary_union(teile).buffer(0), 0.0005) if teile else Polygon()


def luecke_teilen(F, O, land):
    """Schmale Landstreifen zwischen F und O; Rückgabe (Anteil F, Anteil O). Bei Geometriefehlern: (None, None)."""
    try: return _luecke_teilen(nur_flaeche(F), nur_flaeche(O), land)
    except Exception as e:
        print('   Lücke übersprungen (Geometriefehler):', e); return None, None


def _luecke_teilen(F, O, land):
    zone = F.buffer(LUECKE).intersection(O.buffer(LUECKE))
    if zone.is_empty: return None, None
    G = unary_union([F, O]).buffer(LUECKE / 2, join_style='round').buffer(-LUECKE / 2).difference(F).difference(O)
    G = G.intersection(zone).intersection(land)
    if G.is_empty or G.area < 0.01: return None, None
    G = nur_flaeche(G)
    a, b, schritt = F, O, LUECKE / 8
    def wachsen(x, y): return nur_flaeche(x.union(nur_flaeche(x.buffer(schritt).intersection(G).difference(y))))
    for k in range(5):   # beide wachsen abwechselnd in kleinen Schritten → Teilung etwa auf der Mittellinie
        if k % 2 == 0: a = wachsen(a, b); b = wachsen(b, a)
        else: b = wachsen(b, a); a = wachsen(a, b)
    rest = nur_flaeche(G.difference(a).difference(b))
    for t in getattr(rest, 'geoms', [rest]):
        if t.is_empty: continue
        if t.distance(F) <= t.distance(O): a = nur_flaeche(a.union(t))
        else: b = nur_flaeche(b.union(t))
    return nur_flaeche(nur_flaeche(a.difference(F)).intersection(G)), nur_flaeche(nur_flaeche(b.difference(O)).intersection(G))


# ---------- 3. Überlappungen (zeitgenau) ----------
def vorrang(x):
    return (0 if x['f']['properties']['reich'] in HAUPT else 1, x['g'].area)


def ueberlappungen_aufloesen(fl):
    """Wie in build_reiche.py: Flächen in Vorrang-Reihenfolge; jede verliert, was gleichzeitige stärkere Flächen schon haben,
    und zwar nur für deren Jahre (der Zeitraum wird dafür geteilt). Rückgabe: Liste der Teile (dict wie fl, ggf. mehrfach)."""
    fertig = []
    for x in sorted(fl, key=vorrang):
        g0 = x['g']
        if g0.is_empty: continue
        stark = [p for p in fertig if gleichzeitig(p, x) and p['g'].intersects(g0) and p['g'].intersection(g0).area > 1e-4]
        # gleiches Reich (gleiche Farbe): der Vorrang ist gleichgültig. Liegt die Zeit der schon gesetzten Fläche ganz in der
        # von x, gibt sie das gemeinsame Gebiet ab – so entsteht weder eine Lücke noch eine Zeitteilung.
        rest = []
        for p in stark:
            if p['f']['properties']['reich'] == x['f']['properties']['reich'] and x['von'] <= p['von'] and p['bis'] <= x['bis']:
                p['g'] = sauber(p['g'].difference(g0))
            else: rest.append(p)
        stark = rest
        # kleine Überschneidungen: dauerhaft abziehen statt den Zeitraum zu teilen (jede Teilung verdoppelt die Fläche in der Datei)
        klein = [p for p in stark if p['g'].intersection(g0).area < KLEINE_UEB]
        if klein:
            g0 = sauber(g0.difference(unary_union([p['g'].intersection(g0) for p in klein])))
            stark = [p for p in stark if p not in klein]
            if g0.is_empty: continue
        schnitte = sorted({x['von'], x['bis']} | {j for p in stark for j in (p['von'], p['bis']) if x['von'] < j < x['bis']})
        abschnitte = []
        for a, b in zip(schnitte, schnitte[1:]):
            akt = tuple(i for i, p in enumerate(stark) if p['von'] <= a and p['bis'] >= b)
            if abschnitte and abschnitte[-1][2] == akt: abschnitte[-1][1] = b
            else: abschnitte.append([a, b, akt])
        for a, b, akt in abschnitte:
            g = g0.difference(unary_union([stark[i]['g'] for i in akt])) if akt else g0
            g = sauber(g)
            if g.is_empty or g.area < 0.01: continue
            fertig.append(dict(x, g=g, von=a, bis=b))
    return [p for p in fertig if not p['g'].is_empty and p['g'].area >= 0.01]


# ---------- Prüfung ----------
def pruefen(fl, land, jahre=None, ausgabe=True):
    """Überlappungen und schmale Lücken zwischen gleichzeitig sichtbaren Kern-Flächen (Stichjahre)."""
    if jahre is None:
        lo = min(x['von'] for x in fl); hi = max(x['bis'] for x in fl)
        jahre = list(range(lo - lo % 25 + 25, hi, 25))
    ueb, luk = [], []
    for y in jahre:
        akt = [x for x in fl if x['von'] <= y < x['bis']]
        for i, a in enumerate(akt):
            for b in akt[i + 1:]:
                if a['g'].intersects(b['g']):
                    fl_ = a['g'].intersection(b['g']).area
                    if fl_ > 0.05: ueb.append((y, fl_, a['f']['properties']['name'], b['f']['properties']['name']))
        if len(akt) > 1:
            U = unary_union([a['g'] for a in akt])
            G = U.buffer(LUECKE / 2).buffer(-LUECKE / 2).difference(U).intersection(land)
            for t in getattr(G, 'geoms', [G]):
                if t.area < 0.05: continue
                nah = sorted({a['f']['properties']['reich'] for a in akt if a['g'].distance(t) < 0.05})
                if len(nah) >= 2 or (len(nah) == 1 and sum(1 for a in akt if a['g'].distance(t) < 0.05) >= 2):
                    luk.append((y, t.area, ', '.join(nah), [round(c, 1) for c in t.centroid.coords[0]]))
    if ausgabe:
        print('Überlappungen (>0,05 Grad²):', len(ueb))
        for u in sorted(ueb, key=lambda u: -u[1])[:15]: print('   %5d  %.2f  %s  ×  %s' % u)
        print('Schmale Lücken zwischen Nachbarn (>0,05 Grad²):', len(luk))
        for u in sorted(luk, key=lambda u: -u[1])[:15]: print('   %5d  %.2f  %s  bei %s' % u)
    return ueb, luk


def geom_aus(g):
    # auf ein Raster von 0,01° (≈ 1 km) legen: gemeinsame Grenzpunkte von Nachbarn bleiben gemeinsam, die Dateien kleiner
    g = set_precision(g.simplify(VEREINFACHEN, preserve_topology=True).buffer(0), RASTER)
    teile = [orient(p, sign=-1.0) for p in getattr(g, 'geoms', [g]) if p.geom_type == 'Polygon' and p.area >= MIN_FLAECHE]
    g = teile[0] if len(teile) == 1 else MultiPolygon(teile)
    def rnd(o):
        if isinstance(o, (list, tuple)): return [rnd(v) for v in o]
        return round(o, 2) if isinstance(o, float) else o
    m = mapping(g)
    return {'type': m['type'], 'coordinates': rnd(m['coordinates'])}


def main():
    nur_pruefen = '--pruefen' in sys.argv
    daten, land = laden()
    fl = flaechen(daten)
    if nur_pruefen:
        ueb, luk = pruefen(fl, land)
        sys.exit(1 if ueb else 0)

    print('Vorher:'); pruefen(fl, land)
    import build_geographie
    stuecke = saumstuecke(build_geographie.grenzlinien(), land)
    baum = STRtree(stuecke)
    print('Saumstücke an Flüssen und Kämmen:', len(stuecke))

    # 0./4. Küste exakt; 1. an natürliche Linien anlegen
    for x in fl:
        g = sauber(x['g'].intersection(land))
        if g.area >= KLEIN:
            n = sauber(anlegen(g, baum, stuecke).intersection(land))
            if 0.75 * g.area <= n.area <= 1.3 * g.area: g = n   # Schutz: keine Fläche ändert sich dabei grundlegend
        x['g'] = g

    # 2. Lücken zwischen gleichzeitigen Nachbarn
    baum2 = STRtree([x['g'] for x in fl])
    zusatz = [[] for _ in fl]
    for i, F in enumerate(fl):
        for j in baum2.query(F['g'].buffer(LUECKE)):
            j = int(j)
            if j <= i: continue
            O = fl[j]
            if not gleichzeitig(F, O) or F['g'].is_empty or O['g'].is_empty or F['g'].distance(O['g']) > LUECKE: continue
            j_ = ueberlappung_jahre(F, O)
            f_ok, o_ok = j_ >= 0.5 * (F['bis'] - F['von']), j_ >= 0.5 * (O['bis'] - O['von'])
            if not (f_ok or o_ok): continue
            a, b = luecke_teilen(F['g'], O['g'], land)
            if a is None: continue
            if f_ok and o_ok: zusatz[i].append(a); zusatz[j].append(b)
            elif f_ok: zusatz[i].append(unary_union([a, b]))
            else: zusatz[j].append(unary_union([a, b]))
    # Füllungen nicht in Flächen hinein, die die meiste Zeit gleichzeitig bestehen (sonst neue Überlappungen und viele
    # Zeitteilungen). Kurzlebige Nachbarn regelt Schritt 3 zeitgenau.
    neu = []
    for i, x in enumerate(fl):
        if not zusatz[i]: neu.append(x['g']); continue
        z = nur_flaeche(unary_union(zusatz[i]))
        andere = [fl[int(j)]['g'] for j in baum2.query(z) if int(j) != i and gleichzeitig(fl[int(j)], x)
                  and (fl[int(j)]['f']['properties']['reich'] == x['f']['properties']['reich'] or ueberlappung_jahre(fl[int(j)], x) >= 0.5 * (x['bis'] - x['von']))]
        if andere: z = nur_flaeche(z.difference(unary_union(andere)))
        neu.append(sauber(unary_union([x['g'], z]).intersection(land)))
    for x, g in zip(fl, neu): x['g'] = g

    # 3. Überlappungen auflösen (mit Zeitteilung)
    teile = ueberlappungen_aufloesen(fl)

    # zurückschreiben: erster Teil behält die id, weitere Teile bekommen neue ids (ab 9001, fortlaufend)
    neue_id = 9000 + max([0] + [f['properties']['id'] - 9000 for d in daten.values() for f in d['regionen'] if f['properties']['id'] > 9000])
    je_feature = {}
    for t in teile: je_feature.setdefault(id(t['f']), []).append(t)
    for d, dat in daten.items():
        neu = []
        for f in dat['regionen']:
            p = f['properties']
            if p.get('art', 'kern') != 'kern': neu.append(f); continue
            ts = sorted(je_feature.get(id(f), []), key=lambda t: t['von'])
            for k, t in enumerate(ts):
                q = dict(p, von=t['von'], bis=t['bis'])
                if k > 0: neue_id += 1; q['id'] = neue_id
                neu.append({'type': 'Feature', 'properties': q, 'geometry': geom_aus(t['g'])})
        dat['regionen'] = neu
        dat['grenzen'] = 'bereinigt mit build_grenzen.py (natürliche Grenzen, Lücken, Überlappungen, Küste)'
        with io.open(os.path.join(HERE, 'data', d), 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(dat, fh, ensure_ascii=False, separators=(',', ':'))
        print(d, len(dat['regionen']), 'Flächen,', os.path.getsize(os.path.join(HERE, 'data', d)), 'Bytes')

    print('Nachher:'); pruefen(flaechen(daten), land)


if __name__ == '__main__':
    main()
