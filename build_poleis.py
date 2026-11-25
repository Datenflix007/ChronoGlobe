# -*- coding: utf-8 -*-
"""Griechische Poleis und Kolonisation aus dem „Inventory of Archaic and Classical Poleis“ (Hansen/Nielsen 2004).

Quellen (werden nach quellen/lokal/poleis/ geladen, dort per .gitignore ausgeschlossen):
  1. POLIS (Stanford University, Classics Department; M. Krishnan / J. Ober, Stand 2014):
     http://polis.stanford.edu/data/master_data_11_19_2013.csv
     Alle 1035 Poleis des Inventars mit Koordinaten, Region, Größenklasse, Bekanntheit, Mauern, Münzprägung,
     Mitgliedschaft im Delisch-Attischen Seebund. Keine Lizenz angegeben („frei zugänglich für akademische Nutzung“)
     → vor einer Veröffentlichung klären (docs/DATENQUELLEN.md).
  2. Appendix 27 „Colonisation and Hellenisation“, digitalisiert von D. Krasne (v1.0, 25.07.2026), CC BY 4.0:
     https://www.darcykrasne.com/digital_humanities/gis_data/polis_inv/hn_app27_with_pids.csv
     Kolonie → Mutterstadt mit Gründungsdatum in der Notation des Inventars und Polis-Nummern.

Ergebnis:
  data/ebenen/griechische-poleis.json         Themenebene: alle lokalisierten Poleis
  data/ebenen/delisch-attischer-seebund.json  Themenebene: Mitglieder des Seebunds (478/7–404 v. Chr.)
  data/kolonisation.json                      Züge Mutterstadt → Kolonie (von build_fruehe_kulturen.py übernommen)

Darstellungsregeln (im Hinweis der Ebenen genannt):
  - Eine Polis erscheint ab ihrem Gründungsdatum (Kolonien, Anhang 27), sonst ab 650 v. Chr. (Beginn des Zeitraums
    des Inventars), und bleibt bis 323 v. Chr. (Ende des Zeitraums) sichtbar.
  - Gründungsdaten: „C6m“ = Mitte 6. Jh. → 550, „C6f“ = erste Hälfte → 575, „C6s“ = zweite Hälfte → 525,
    „C6e“ = früh → 590, „C6l“ = spät → 510, „c.600“ → 600, „446/5“ → 446.

    python build_poleis.py          # lädt die Quellen bei Bedarf und schreibt die drei Dateien
"""
import csv, io, json, os, re, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LOKAL = os.path.join(HERE, 'quellen', 'lokal', 'poleis')
URL_STANFORD = 'http://polis.stanford.edu/data/master_data_11_19_2013.csv'
URL_APP27 = 'https://www.darcykrasne.com/digital_humanities/gis_data/polis_inv/hn_app27_with_pids.csv'
VON_STANDARD, BIS_STANDARD = -650, -323

QUELLE_HN = 'Hansen, Mogens Herman; Nielsen, Thomas Heine (Hg.): An Inventory of Archaic and Classical Poleis. Oxford: Oxford University Press 2004.'
QUELLE_STANFORD = {'zitat': 'POLIS – digitale Fassung des Inventars. Stanford University, Classics Department (M. Krishnan, J. Ober), Stand 2014.', 'url': 'http://polis.stanford.edu', 'lizenz': 'keine Lizenz angegeben, frei zugänglich für akademische Nutzung'}
QUELLE_APP27 = {'zitat': 'Krasne, Darcy: Augmented digitization of Appendix 27 („Colonisation and Hellenisation“) of Hansen/Nielsen 2004, v1.0, 2026.', 'url': 'https://www.darcykrasne.com/digital_humanities/gis_data/polis_inv/', 'lizenz': 'CC BY 4.0'}

REGION_DE = {
    'Achaia': 'Achaia', 'Adriatic': 'Adria', 'Aegean': 'Ägäische Inseln', 'Aiolis & SW Mysia': 'Aiolis und Mysien', 'Aitolia': 'Aitolien',
    'Akarnania & Ajacent': 'Akarnanien', 'Argolis': 'Argolis', 'Arkadia': 'Arkadien', 'Attika': 'Attika', 'Black Sea': 'Schwarzes Meer',
    'Boiotia': 'Böotien', 'Crete': 'Kreta', 'Cyprus': 'Zypern', 'Doris': 'Doris', 'East Locris': 'Ostlokris', 'Elis': 'Elis', 'Epeiros': 'Epirus',
    'Euboia': 'Euböa', 'Ionia': 'Ionien', 'Italia & Kampania': 'Italien und Kampanien', 'Karia': 'Karien', 'Lakedaimon': 'Lakonien',
    'Lesbos': 'Lesbos', 'Lykia': 'Lykien', 'Makedonia': 'Makedonien', 'Megaris, Korinthia, Sikyonia': 'Megaris, Korinthia, Sikyonia',
    'Messenia': 'Messenien', 'Pamphylia & Kilikia': 'Pamphylien und Kilikien', 'Phokis': 'Phokis', 'Propontic Asia Minor': 'Propontis (Kleinasien)',
    'Propontic Thrace': 'Propontis (Thrakien)', 'Rhodos': 'Rhodos', 'Saronic Gulf': 'Saronischer Golf', 'Sikelia': 'Sizilien',
    'Spain & France': 'Spanien und Gallien', 'Syria to Pillars of Herakles': 'Syrien bis zu den Säulen des Herakles', 'Thessaly & Adjacent': 'Thessalien',
    'Thrace: Axios - Strymon': 'Thrakien (Axios–Strymon)', 'Thrace: Inland': 'Thrakien (Binnenland)', 'Thrace: Nestos - Hebros': 'Thrakien (Nestos–Hebros)',
    'Thrace: Strymon - Nestos': 'Thrakien (Strymon–Nestos)', 'Thracian Chersonesos': 'Thrakische Chersones', 'Triphylia': 'Triphylien', 'Troas': 'Troas'}
GROESSE = {1: 'sehr kleines Gebiet (unter 25 km²)', 2: 'kleines Gebiet (25–100 km²)', 3: 'mittleres Gebiet (100–200 km²)', 4: 'großes Gebiet (200–500 km²)', 5: 'sehr großes Gebiet (über 500 km²)'}


def laden(url, name):
    os.makedirs(LOKAL, exist_ok=True)
    pfad = os.path.join(LOKAL, name)
    if not os.path.exists(pfad):
        req = urllib.request.Request(url, headers={'User-Agent': 'ChronoGlobe-Datenaufbereitung'})
        with urllib.request.urlopen(req, timeout=120) as r, open(pfad, 'wb') as f: f.write(r.read())
    return open(pfad, encoding='utf-8', errors='replace').read()


def jahr_aus(t):
    """Gründungsdatum in der Notation des Inventars → (Jahr v. Chr. negativ, unsicher) oder (None, None)."""
    t = (t or '').strip()
    if not t or t == '?': return None, None
    unsicher = '?' in t or t.startswith('c.') or t.startswith('C')
    m = re.match(r'^C(\d+)([efmsl]?)', t)
    if m:
        jh = int(m.group(1)); basis = -(jh * 100 - 50)   # Mitte des Jahrhunderts
        verschiebung = {'e': -40, 'f': -25, 'm': 0, 's': 25, 'l': 40, '': 0}[m.group(2)]
        return basis + verschiebung, True
    m = re.search(r'(\d{3,4})', t)
    if m: return -int(m.group(1)), unsicher
    return None, None


def slug(t):
    t = t.lower()
    for a, b in (('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss')): t = t.replace(a, b)
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')[:50] or 'polis'


def main():
    stanford = list(csv.DictReader(io.StringIO(laden(URL_STANFORD, 'stanford_master_data.csv'))))[1:]   # erste Zeile beschreibt Feldtypen
    app27 = list(csv.DictReader(io.StringIO(laden(URL_APP27, 'hn_app27_with_pids.csv'))))
    poleis = {}
    for z in stanford:
        if 'HansonNielson' not in z['Source']: continue
        try: lng, lat = float(z['xcoord']), float(z['ycoord'])
        except ValueError: continue
        if not lng and not lat: continue
        name = z['name'].split('-', 1)[1] if '-' in z['name'] else z['name']
        poleis[z['polis_id']] = dict(nr=z['polis_id'], name=name.strip(), lng=round(lng, 3), lat=round(lat, 3), region=z['Region name'].strip(),
                                     groesse=int(z['Size']) if z['Size'].isdigit() else 0, seebund=z['Delian_League'] == '1',
                                     mauern=z['Walls'] == '1', silber=z['Silver_1st'].strip(), bronze=z['Bronze_1st'].strip(),
                                     fame=float(z['Fame']) if re.match(r'^[\d.]+$', z['Fame'] or '') else 0)
    # Gründungen aus Anhang 27: erste (ursprüngliche) Gründung je Kolonie
    gruendung, zuege = {}, []
    for a in app27:
        k, m = a['colony_hnid'].strip(), a['founder_hnid'].strip()
        j, uns = jahr_aus(a['hn_foundation_date'])
        if a['initial_foundation'] != 'True' or j is None: continue
        if k in poleis and (k not in gruendung or j < gruendung[k][0]): gruendung[k] = (j, uns, a['founder_name'].strip(), a['hn_foundation_date'].strip())
        if k in poleis and m in poleis and VON_STANDARD - 200 <= j <= BIS_STANDARD:
            K, M = poleis[k], poleis[m]
            zuege.append({'volk': K['name'], 'gruppe': 'kolonisation', 'farbe': '#5fd3c4', 'von': j - 3, 'bis': j, 'spur': 9999,
                          'pfad': [[M['lng'], M['lat']], [round((M['lng'] + K['lng']) / 2, 3), round((M['lat'] + K['lat']) / 2, 3)], [K['lng'], K['lat']]],
                          'text': '%s gründet %s (%s, Inventar: „%s“%s)' % (M['name'], K['name'], ('um ' if uns else '') + str(-j) + ' v. Chr.', a['hn_foundation_date'].strip(), ', unsicher' if uns else '')})
    zuege.sort(key=lambda z: z['von'])

    objekte, mitglieder, ids = [], [], set()
    for p in sorted(poleis.values(), key=lambda x: (-x['fame'], x['name'])):
        g = gruendung.get(p['nr'])
        von = max(g[0], -1200) if g else VON_STANDARD
        teile = ['Polis Nr. %s im Inventar von Hansen/Nielsen; Region: %s.' % (p['nr'], REGION_DE.get(p['region'], p['region']))]
        if g: teile.append('Gegründet von %s, %s (Inventar: „%s“).' % (g[2], ('um ' if g[1] else '') + '%d v. Chr.' % -g[0], g[3]))
        if p['groesse'] in GROESSE: teile.append('Größe: ' + GROESSE[p['groesse']] + '.')
        extra = []
        if p['mauern']: extra.append('Stadtmauern belegt')
        if p['silber']: extra.append('eigene Silbermünzen')
        if p['seebund']: extra.append('Mitglied im Delisch-Attischen Seebund')
        if extra: teile.append('; '.join(extra) + '.')
        oid = slug(p['name']) + '-' + p['nr']
        if oid in ids: continue
        ids.add(oid)
        o = {'id': oid, 'typ': 'punkt', 'name': p['name'], 'von': von, 'bis': max(BIS_STANDARD, von), 'beschreibung': ' '.join(teile),
             'beleg': 'Hansen/Nielsen 2004, Nr. %s' % p['nr'], 'koordinaten': [p['lng'], p['lat']]}
        if g and g[1]: o['unsicher'] = True
        if p['groesse']: o['groesse'] = p['groesse']
        objekte.append(o)
        if p['seebund']:
            mitglieder.append({'id': oid, 'typ': 'punkt', 'name': p['name'], 'von': -478, 'bis': -404, 'beschreibung': 'In den athenischen Tributlisten als Mitglied belegt (Region: %s).' % REGION_DE.get(p['region'], p['region']),
                               'beleg': 'Hansen/Nielsen 2004, Nr. %s' % p['nr'], 'koordinaten': [p['lng'], p['lat']], **({'groesse': p['groesse']} if p['groesse'] else {})})

    ebene = {'format': 'chronoglobe-ebene/1', 'id': 'griechische-poleis', 'name': 'Griechische Poleis (alle Stadtstaaten)', 'farbe': '#7fd1ff',
             'beschreibung': 'Alle %d lokalisierten Poleis des Inventars von Hansen und Nielsen – vom Schwarzen Meer bis Spanien. Größere Punkte = größeres Stadtgebiet. Die Infokarte nennt Region, Gründung, Größe und Mitgliedschaft im Seebund.' % len(objekte),
             'hinweis': 'Darstellungsregel: Eine Polis erscheint ab ihrem Gründungsdatum (nur für Kolonien bekannt, sonst ab 650 v. Chr.) und bleibt bis 323 v. Chr. sichtbar – dem Zeitraum des Inventars. Viele Städte bestanden länger. Gründungsdaten sind oft nur auf ein Jahrhundert genau.',
             'quellen': [{'zitat': QUELLE_HN}, QUELLE_STANFORD, QUELLE_APP27], 'objekte': objekte}
    bund = {'format': 'chronoglobe-ebene/1', 'id': 'delisch-attischer-seebund', 'name': 'Mitglieder des Delisch-Attischen Seebunds', 'farbe': '#1fa2c8',
            'beschreibung': 'Die %d Poleis, die nach dem Inventar von Hansen und Nielsen zum Seebund unter Athens Führung gehörten (478/7–404 v. Chr.).' % len(mitglieder),
            'hinweis': 'Darstellungsregel: Alle Mitglieder erscheinen für die ganze Dauer des Bundes; tatsächlich traten viele später bei, fielen ab oder wurden gezwungen zu bleiben. Grundlage sind vor allem die athenischen Tributlisten.',
            'quellen': [{'zitat': QUELLE_HN}, QUELLE_STANFORD], 'objekte': mitglieder}
    for name, d in (('griechische-poleis.json', ebene), ('delisch-attischer-seebund.json', bund)):
        with io.open(os.path.join(HERE, 'data', 'ebenen', name), 'w', encoding='utf-8', newline='\n') as f: json.dump(d, f, ensure_ascii=False, separators=(',', ':'))
    with io.open(os.path.join(HERE, 'data', 'kolonisation.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'_hinweis': 'Erzeugt mit build_poleis.py aus Appendix 27 von Hansen/Nielsen 2004 (Digitalisierung D. Krasne, CC BY 4.0). Wege schematisch.', 'zuege': zuege}, f, ensure_ascii=False, separators=(',', ':'))
    print('Poleis: %d lokalisiert, %d mit Gründungsdatum, %d Seebund-Mitglieder, %d Kolonisationszüge' % (len(objekte), len(gruendung), len(mitglieder), len(zuege)))


if __name__ == '__main__':
    main()
