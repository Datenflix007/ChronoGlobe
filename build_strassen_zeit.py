# -*- coding: utf-8 -*-
"""Reichert das Zeitmodell der Römerstraßen (data/roemerstrassen.json) mit belegten Datierungen aus Itiner-e an.

Ausgangslage: data/roemerstrassen.json enthält 819 vereinfachte, verkettete Hauptstraßen-Linien mit einem
regionalen Zeitmodell (zeit.beginn_min/beginn_max/beginn_modell/roemische_nutzung_bis_modell). Diese Werte sind
regionale Schätzungen, keine Baujahre.

Itiner-e (static version 2024, Zenodo DOI 10.5281/zenodo.17122148, CC BY 4.0) enthält je Segment u. a.:
  Lower_Date / Low_Date_E   frühestes Datum der Straße und Unsicherheit in Jahren (9999 = unbekannt)
  Upper_Date / Up_Date_E    spätestes Datum und Unsicherheit (9999 = unbekannt)
  Cons_per_e                Bau- bzw. Ausbauphase laut Beleg, z. B. "Claudius (46 CE)" (oft Meilensteine; kann
                            auch eine spätere Erneuerung sein)

Zuordnung (räumlich, dokumentierte Toleranzen):
  - Originalsegmente vom Typ "Main Road" werden aus EPSG:3395 in Grad umgerechnet.
  - Ein Segment gehört zu einer vereinfachten Linie, wenn mindestens MIN_SEG_ANTEIL seiner Länge innerhalb von
    TOL Grad (≈ 4 km) um die Linie liegt.
  - Eine Linie gilt als zugeordnet, wenn die zugeordneten Segmente mindestens MIN_ABDECKUNG ihrer Länge abdecken.
Übernahme (keine erfundenen Jahre):
  - Lower_Date: Die Straße bestand spätestens um Lower_Date + Fehler → beginn_max wird höchstens darauf gesenkt.
  - Cons_per_e: Die Straße bestand spätestens am Ende der genannten Phase → ebenso nur Obergrenze für beginn_max.
  - beginn_min wird nie früher gelegt als im Regionalmodell (das Netz zeigt römische Straßen, keine vorrömischen).
  - Upper_Date: als belegte späteste Nutzung gespeichert (Anzeige in der Infokarte), ändert das Modell nicht.
  - Eine Linie, die aus mehreren Segmenten besteht, ist erst vollständig, wenn alle Teile bestehen: beginn_max der
    Linie = Maximum der Teilwerte; undatierte Teile behalten den regionalen Wert.
  - datierung: "itinere_belegt" (≥ 90 % der zugeordneten Länge datiert), "itinere_teilweise" (> 0 %),
    sonst bleibt "regionalmodell_nicht_einzelbelegt".
Die ursprünglichen Regionalwerte bleiben in zeit.regional erhalten. Koordinaten (p), s und id bleiben unverändert.

    python build_strassen_zeit.py <pfad/zu/itinere_roads.geojson>
"""
import io, json, math, os, re, sys
from shapely.geometry import LineString, MultiLineString
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HERE, 'data', 'roemerstrassen.json')
TOL = 0.04            # Grad, ≈ 4 km (Vereinfachung der Linien: ≈ 3 km)
MIN_SEG_ANTEIL = 0.8  # Anteil eines Segments innerhalb der Toleranz
MIN_ABDECKUNG = 0.6   # Anteil der Linienlänge, der durch zugeordnete Segmente abgedeckt sein muss
A, E = 6378137.0, 0.0818191908426215


def inv_merc(x, y):
    lng = math.degrees(x / A)
    t = math.exp(-y / A)
    phi = math.pi / 2 - 2 * math.atan(t)
    for _ in range(8):
        es = E * math.sin(phi)
        phi = math.pi / 2 - 2 * math.atan(t * ((1 - es) / (1 + es)) ** (E / 2))
    return lng, math.degrees(phi)


def jahr(v):
    return None if v is None or v >= 9000 else int(round(v))


def bauphase(txt):
    """'Claudius (44-45 CE)' -> (44, 45); 'Manius Aquilius (129-126 BCE)' -> (-129, -126); ohne Jahre/Ära -> None"""
    if not txt: return None
    m = re.search(r'\(([^)]*)\)', txt)
    if not m: return None
    tok = re.findall(r'(\d{1,4})\s*(BCE|BC|CE|AD)?', m.group(1))
    if not tok: return None
    jahre, offen = [], []
    for zahl, aera in tok:
        offen.append(int(zahl))
        if aera:
            sign = -1 if aera.startswith('B') else 1
            jahre += [sign * z for z in offen]; offen = []
    if offen or not jahre: return None   # Ära fehlt: nicht verwendbar
    return min(jahre), max(jahre)


def lade_segmente(pfad):
    d = json.load(open(pfad, encoding='utf-8'))
    segs = []
    for f in d['features']:
        p = f['properties']
        if p.get('Type') != 'Main Road' or not f.get('geometry'): continue
        g = f['geometry']
        teile = g['coordinates'] if g['type'] == 'MultiLineString' else [g['coordinates']]
        linien = [[inv_merc(c[0], c[1]) for c in t] for t in teile if len(t) >= 2]
        if not linien: continue
        geo = MultiLineString(linien).simplify(0.005)
        lo, lo_e, up, up_e = jahr(p.get('Lower_Date')), jahr(p.get('Low_Date_E')), jahr(p.get('Upper_Date')), jahr(p.get('Up_Date_E'))
        segs.append(dict(g=geo, name=p.get('Name'), lower=lo, lower_e=lo_e or 0, upper=up, upper_e=up_e or 0,
                         phase_txt=p.get('Cons_per_e'), phase=bauphase(p.get('Cons_per_e')), sicher=p.get('Segment_s')))
    return segs


def obergrenze(s):
    """spätestes Jahr, zu dem das Segment laut Beleg bestand (oder None)"""
    w = []
    if s['lower'] is not None: w.append(s['lower'] + s['lower_e'])
    if s['phase']: w.append(s['phase'][1])
    return min(w) if w else None


# Region einer Linie aus den Provinzflächen (data/reiche.json, Stand 150 n. Chr.): Name der Provinz -> Modellregion
REGION_NACH_PROVINZ = [
    ('mauretanien', ('Mauretania',)),
    ('nordafrika', ('Africa', 'Numidia', 'Tripolitanien', 'Cyrenaica (Kyrenaika)')),
    ('aegypten', ('Aegyptus',)),
    ('levant', ('Syria', 'Iudaea', 'Arabia', 'Palmyrene', 'Cyprus')),
    ('pontus_kaukasus', ('Pontus Polemoniacus',)),
    ('kleinasien', ('Asia', 'Bithynia', 'Pontus', 'Galatia', 'Cappadocia', 'Lycia', 'Cilicia', 'Commagene')),
    ('griechenland', ('Macedonia', 'Achaia', 'Epirus', 'Kreta')),
    ('balkan', ('Pannonia', 'Dalmatia', 'Illyricum', 'Moesia', 'Dacia', 'Thracia')),
    ('britannien', ('Britannia',)),
    ('germanien_raetien', ('Germania', 'Raetia', 'Noricum', 'Agri decumates', 'Alpenprovinzen', 'Ostalpen')),
    ('gallien', ('Gallia Narbonensis', 'Gallia Aquitania', 'Gallia Lugdunensis', 'Gallia Belgica')),
    ('hispanien', ('Hispania', 'Lusitania')),
    ('italien', ('Italia', 'Sicilia', 'Sardinia', 'Gallia cisalpina')),
]


def provinzen():
    from shapely.geometry import shape
    d = json.load(open(os.path.join(HERE, 'data', 'reiche.json'), encoding='utf-8'))
    out = []
    for f in d['regionen']:
        p = f['properties']
        if p['reich'] == 'rom' and p['von'] <= 150 < p['bis']:
            reg = next((r for r, keys in REGION_NACH_PROVINZ if any(k in p['name'] for k in keys)), None)
            if reg: out.append((shape(f['geometry']).buffer(0.05), reg, p['name']))
    return out


def region_aus_lage(prov, linie):
    """Modellregion, in der der größte Teil der Linie liegt (oder None)"""
    best, bl = None, 0
    for g, reg, name in prov:
        lg = g.intersection(linie).length
        if lg > bl: best, bl = (reg, name), lg
    return best if best and bl >= 0.5 * linie.length else None


def main(pfad):
    daten = json.load(open(ZIEL, encoding='utf-8'))
    segs = lade_segmente(pfad)
    prov = provinzen()
    RM = daten['regionen_modell']
    modell = {}
    for l in daten['linien']:
        r = (l['zeit'].get('regional') or l['zeit']).get('region', l['zeit']['region'])
        modell.setdefault(r, []).append((l['zeit'].get('regional') or l['zeit'])['beginn_modell'])
    modell = {r: sorted(v)[len(v) // 2] for r, v in modell.items()}
    korr = 0
    baum = STRtree([s['g'] for s in segs])
    stat = {'itinere_belegt': 0, 'itinere_teilweise': 0, 'regionalmodell_nicht_einzelbelegt': 0, 'nicht_zugeordnet': 0}
    for l in daten['linien']:
        z = l['zeit']
        reg = z.get('regional') or {k: z[k] for k in ('beginn_min', 'beginn_max', 'beginn_modell', 'roemische_nutzung_bis_modell', 'region', 'datierung', 'quelle_datierung')}
        z['regional'] = reg
        for k in reg: z[k] = reg[k]
        z.pop('itinere', None); z.pop('region_korrektur', None)
        linie = LineString(l['p'])
        # Region nach Lage korrigieren (Regionalmodell ordnete nach Rechtecken zu, z. B. Tunesien zu Italien)
        lage = region_aus_lage(prov, linie)
        if lage and lage[0] != reg['region'] and lage[0] in RM:
            r = lage[0]; korr += 1
            z['region_korrektur'] = 'Region nach Lage in der Provinz „%s“ korrigiert (vorher %s)' % (lage[1], reg['region'])
            z['region'] = r
            z['beginn_min'], z['beginn_max'] = RM[r]['beginn_min'], RM[r]['beginn_max']
            z['roemische_nutzung_bis_modell'] = RM[r]['roemisch_bis']
            z['beginn_modell'] = max(RM[r]['beginn_min'], min(RM[r]['beginn_max'], modell.get(r, (RM[r]['beginn_min'] + RM[r]['beginn_max']) // 2)))
        reg = dict(reg, **{k: z[k] for k in ('beginn_min', 'beginn_max', 'beginn_modell')})
        puffer = linie.buffer(TOL)
        treffer = []
        for i in baum.query(puffer):
            s = segs[int(i)]
            if s['g'].length == 0: continue
            if s['g'].intersection(puffer).length / s['g'].length >= MIN_SEG_ANTEIL: treffer.append(s)
        abdeckung = min(1.0, sum(s['g'].length for s in treffer) / max(linie.length, 1e-9))
        if not treffer or abdeckung < MIN_ABDECKUNG:
            stat['nicht_zugeordnet'] += 1; stat[reg['datierung']] += 1
            continue
        ges = sum(s['g'].length for s in treffer)
        datiert = [s for s in treffer if obergrenze(s) is not None]
        anteil = sum(s['g'].length for s in datiert) / ges
        namen = []
        for s in sorted(treffer, key=lambda s: -s['g'].length):
            if s['name'] and s['name'] not in namen: namen.append(s['name'])
        belege = []
        for s in sorted(datiert, key=lambda s: -s['g'].length)[:6]:
            belege.append({k: v for k, v in dict(name=s['name'], lower_date=s['lower'], lower_fehler=s['lower_e'] if s['lower'] is not None else None,
                                                 upper_date=s['upper'], upper_fehler=s['upper_e'] if s['upper'] is not None else None,
                                                 bauphase=s['phase_txt'], segment_sicherheit=s['sicher']).items() if v is not None})
        z['itinere'] = {'segmente': len(treffer), 'abdeckung': round(abdeckung, 2), 'datierter_anteil': round(anteil, 2),
                        'namen': namen[:5], 'belege': belege,
                        'zuordnung': 'räumlich, Toleranz %.2f°, Segmentanteil ≥ %d %%, Abdeckung ≥ %d %%' % (TOL, MIN_SEG_ANTEIL * 100, MIN_ABDECKUNG * 100)}
        if not datiert:
            stat[reg['datierung']] += 1
            continue
        # Linie vollständig, wenn alle Teile bestehen: Maximum über die Teile; undatierte Teile behalten den Regionalwert
        teile_max = [max(reg['beginn_min'], min(reg['beginn_max'], obergrenze(s))) if obergrenze(s) is not None else reg['beginn_max'] for s in treffer]
        neu_max = max(teile_max)
        z['beginn_max'] = max(reg['beginn_min'], min(reg['beginn_max'], neu_max))
        z['beginn_modell'] = min(reg['beginn_modell'], z['beginn_max']) if reg['beginn_modell'] > z['beginn_max'] else max(reg['beginn_min'], min(reg['beginn_modell'], z['beginn_max']))
        spaet = [s['upper'] + s['upper_e'] for s in datiert if s['upper'] is not None]
        if spaet: z['itinere']['spaeteste_belegte_nutzung'] = max(spaet)
        z['datierung'] = 'itinere_belegt' if anteil >= 0.9 else 'itinere_teilweise'
        z['quelle_datierung'] = ('Itiner-e (Lower_Date bzw. Cons_per_e) als Obergrenze für den Ausbau; Beginn weiter regional modelliert'
                                 if z['datierung'] == 'itinere_belegt' else
                                 'teilweise Itiner-e-Belege (%d %% der zugeordneten Länge); übrige Teile regional modelliert' % round(anteil * 100))
        stat[z['datierung']] += 1
    daten['_zeitmodell_version'] = '1.1'
    daten['zeitliche_einordnung']['anreicherung'] = (
        'build_strassen_zeit.py: räumliche Zuordnung zu Itiner-e-Hauptstraßensegmenten (Toleranz %.2f°, Segmentanteil ≥ %d %%, '
        'Abdeckung ≥ %d %%). Belegte Daten (Lower_Date, Cons_per_e) senken beginn_max höchstens; beginn_min bleibt regional. '
        'Ursprüngliche Regionalwerte in zeit.regional.' % (TOL, MIN_SEG_ANTEIL * 100, MIN_ABDECKUNG * 100))
    with io.open(ZIEL, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(daten, f, ensure_ascii=False, separators=(',', ':'))
    print('Linien:', len(daten['linien']), stat, 'Region korrigiert:', korr)


if __name__ == '__main__':
    main(sys.argv[1])
