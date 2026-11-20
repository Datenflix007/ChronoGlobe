# -*- coding: utf-8 -*-
"""check_zitate: prüft die Belege der Schülertexte (data/texte.json) gegen die abgelegten Quellenseiten.

Geprüft wird:
  1. Jede Fußnote verweist auf einen Titel aus data/literatur.json.
  2. Die Belegstelle („beleg“) steht wörtlich auf der angegebenen Seite (Vergleich nur über Buchstaben und
     Ziffern, damit Zeilenumbrüche, Silbentrennung und Anführungszeichen-Varianten nicht stören).
  3. Jedes Fußnotenzeichen [n] im Text hat eine Fußnote, und jede Fußnote wird benutzt.
  4. Wortzahlen je Niveau (A 80–100, B 130–160, C 180–220).
  5. Mindestens zwei unabhängige Fachtitel (keine antike Quelle) je Text.

Seitentexte: quellen/oeffentlich/<id>.json (im Repo, gemeinfrei) und quellen/lokal/<id>.json (nur lokal,
urheberrechtlich geschützt; siehe docs/GRUNDREGELN.md). Fehlt eine lokale Datei, wird der Beleg als
„nicht prüfbar“ gemeldet, nicht als Fehler.

Aufruf (im Projektordner):  python tools/check_zitate.py      Exitcode 1 bei Fehlern.
"""
import json, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
WORTE = {'A': (80, 100), 'B': (130, 160), 'C': (180, 220)}


def norm(s):
    s = unicodedata.normalize('NFKC', s).lower().replace('ß', 'ss')
    s = s.replace('­', '')
    return re.sub(r'[^0-9a-zäöü]', '', s)


def seiten(qid):
    for ordner in ('oeffentlich', 'lokal'):
        p = os.path.join(HERE, 'quellen', ordner, qid + '.json')
        if os.path.exists(p):
            return json.load(open(p, encoding='utf-8'))['seiten'], ordner
    return None, None


def worte(text):
    return len(re.sub(r'\[\d+\]', '', text).split())


def main():
    lit = {t['id']: t for t in json.load(open(os.path.join(HERE, 'data', 'literatur.json'), encoding='utf-8'))['titel']}
    texte = json.load(open(os.path.join(HERE, 'data', 'texte.json'), encoding='utf-8'))['texte']
    fehler, offen, ok = [], [], 0
    for t in texte:
        tid = t['id']
        fns = {f['n']: f for f in t['fussnoten']}
        benutzt = set()
        teile = list(t['niveaus'].items())
        if t.get('vignette'): teile.append(('Vignette', t['vignette']['text']))
        for niv, text in teile:
            for n in map(int, re.findall(r'\[(\d+)\]', text)):
                benutzt.add(n)
                if n not in fns: fehler.append('%s/%s: Fußnotenzeichen [%d] ohne Fußnote' % (tid, niv, n))
            if niv in WORTE:
                w, (lo, hi) = worte(text), WORTE[niv]
                if not lo <= w <= hi: fehler.append('%s/%s: %d Wörter (Soll %d–%d)' % (tid, niv, w, lo, hi))
                else: print('  %-14s Niveau %s: %d Wörter' % (tid, niv, w))
        for x in t.get('steckbrief', []) + t.get('glossar', []):
            if x.get('fn'): benutzt.add(x['fn'])
        for n in fns:
            if n not in benutzt: fehler.append('%s: Fußnote %d wird nirgends verwendet' % (tid, n))
        fach = {f['q'] for f in t['fussnoten'] if f['q'] in lit and not lit[f['q']].get('antik')}
        if len(fach) < 2: fehler.append('%s: nur %d Fachtitel (mind. 2)' % (tid, len(fach)))
        else: print('  %-14s Fachtitel: %s' % (tid, ', '.join(sorted(fach))))
        for f in t['fussnoten']:
            if f['q'] not in lit:
                fehler.append('%s Fn %d: Titel %s fehlt in literatur.json' % (tid, f['n'], f['q'])); continue
            s, ordner = seiten(f['q'])
            if s is None:
                offen.append('%s Fn %d: %s (Seitentext nicht abgelegt, ablage=%s)' % (tid, f['n'], f['q'], lit[f['q']]['ablage'])); continue
            if f['s'] not in s:
                fehler.append('%s Fn %d: Seite %s von %s nicht abgelegt' % (tid, f['n'], f['s'], f['q'])); continue
            if norm(f['beleg']) in norm(s[f['s']]): ok += 1
            else: fehler.append('%s Fn %d: Beleg nicht auf %s S. %s gefunden: „%s“' % (tid, f['n'], f['q'], f['s'], f['beleg']))
    print('\nBelege geprüft und gefunden: %d' % ok)
    for o in offen: print('NICHT PRÜFBAR:', o)
    for e in fehler: print('FEHLER:', e)
    print('Ergebnis:', 'OK' if not fehler else '%d Fehler' % len(fehler))
    return 1 if fehler else 0


if __name__ == '__main__':
    sys.exit(main())
