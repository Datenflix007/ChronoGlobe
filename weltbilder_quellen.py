# -*- coding: utf-8 -*-
"""Belege für die Weltbilder aus den Volltexten (für build_weltbilder.py).

- Lateinischer Text: Plinius, Naturalis historia, ed. Mayhoff, bei LacusCurtius (Bill Thayer), je Buch eine Seite.
  Abschnittsnummern (§) aus den Ankern der Seite.
- Deutsche Übersetzung: G. C. Wittstein, Die Naturgeschichte des Cajus Plinius Secundus, Bd. 1 (Bücher 1–6) und
  Anfang Bd. 2, Leipzig 1881, gemeinfrei; OCR-Text von archive.org (dienatugeschicht03plin).
Beide werden beim ersten Lauf nach quellen/lokal/weltbilder/plinius/ geladen.
"""
import html, os, re, urllib.request

LAT_URL = 'https://penelope.uchicago.edu/Thayer/L/Roman/Texts/Pliny_the_Elder/%d*.html'
DE_URL = 'https://archive.org/download/dienatugeschicht03plin/dienatugeschicht03plin_djvu.txt'
BUCHNAME = {2: 'Zweites', 3: 'Drittes', 4: 'Viertes', 5: 'Fünftes', 6: 'Sechstes', 7: 'Siebentes'}


def _laden(url, ziel):
    if not os.path.exists(ziel):
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        print('lade', url)
        req = urllib.request.Request(url, headers={'User-Agent': 'ChronoGlobe-Build/1.0'})
        with urllib.request.urlopen(req, timeout=180) as r, open(ziel, 'wb') as f: f.write(r.read())
    return open(ziel, encoding='utf-8', errors='replace').read()


class Latein:
    def __init__(self, ordner):
        self.ordner = ordner; self.buecher = {}

    def abschnitte(self, b):
        if b not in self.buecher:
            s = _laden(LAT_URL % b, os.path.join(self.ordner, 'mayhoff_%d.html' % b))
            teile = re.split(r'<A [^>]*?NAME="(\d+)"[^>]*>', s)
            A = {}
            for i in range(1, len(teile) - 1, 2):
                t = re.sub(r'<[^>]+>', ' ', teile[i + 1]); t = re.sub(r'\s+', ' ', html.unescape(t))
                A[int(teile[i])] = A.get(int(teile[i]), '') + ' ' + t
            self.buecher[b] = A
        return self.buecher[b]

    def finde(self, b, muster, ab=None):
        A = self.abschnitte(b)
        for n in sorted(A):
            if ab and n < ab: continue
            if re.search(muster, A[n]): return n
        return None

    def anteil(self, b, n):
        """relative Lage des Abschnitts im Buch (0..1), um die Stelle in der Übersetzung zu finden"""
        k = sorted(self.abschnitte(b)); return k.index(n) / max(1, len(k) - 1)


class Deutsch:
    """Wittstein: Text je Buch bereinigt (Seitenköpfe → Seitenmarken, Fußnoten und Silbentrennung entfernt)."""
    def __init__(self, ordner):
        self.roh = _laden(DE_URL, os.path.join(ordner, 'wittstein_djvu.txt')); self.buecher = {}

    def buch(self, b):
        if b in self.buecher: return self.buecher[b]
        if b not in BUCHNAME: return None
        t, name = self.roh, BUCHNAME[b]
        kopf = re.compile(r'(?:(\d{1,3})\s+%s\s+Buch\.|%s\s+Buch\.\s+(\d{1,3}))' % (name, name))
        treffer = list(kopf.finditer(t))
        if not treffer: return None
        start = treffer[0].start() - 3000
        naechstes = BUCHNAME.get(b + 1)
        ende = len(t)
        if naechstes:
            m = re.search(r'(?:\d{1,3}\s+%s\s+Buch\.|%s\s+Buch\.\s+\d{1,3})' % (naechstes, naechstes), t[treffer[-1].end():])
            if m: ende = treffer[-1].end() + m.start()
        s = t[max(0, start):ende]
        # Seitenköpfe → Seitenmarken. OCR verliest Seitenzahlen gelegentlich; gültig ist nur, was zu einer robusten
        # Geraden „Textstelle → Seite“ passt (Median der Steigungen benachbarter Köpfe).
        kk = [(m.start(), int(m.group(1) or m.group(2))) for m in kopf.finditer(s)]
        st = sorted((b2 - b1) / (a2 - a1) for (a1, b1), (a2, b2) in zip(kk, kk[1:]) if a2 > a1 and 0 < b2 - b1 <= 3)
        k = st[len(st) // 2] if st else 0
        d0 = sorted(n - k * p for p, n in kk)[len(kk) // 2] if kk else 0
        gut = {p for p, n in kk if abs(n - (d0 + k * p)) <= 2.5}
        s = kopf.sub(lambda m: ' ⟦S.%s⟧ ' % (m.group(1) or m.group(2)) if m.start() in gut else ' ', s)
        if kk: s = ' ⟦S.%d⟧ ' % max(1, min(n for p, n in kk if p in gut) - 1) + s if gut else s
        zeilen = [z for z in s.split('\n') if not re.match(r'^\s*[\d>»*l]{1,3}\)\s', z)]   # Fußnoten (OCR liest „1)“ oft als „>)“)
        s = '\n'.join(zeilen)
        s = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', s)            # Silbentrennung
        s = re.sub(r'(?<=[a-zäöüß,;])\s?\d{1,2}\)', '', s)         # Fußnotenzeichen im Text
        s = re.sub(r'\s+', ' ', s)
        self.buecher[b] = s
        return s

    def finde(self, b, muster, anteil=None):
        """Treffer, der der relativen Lage `anteil` des lateinischen Abschnitts am nächsten liegt"""
        s = self.buch(b)
        if not s: return None
        alle = list(re.finditer(muster, s, re.I))
        if not alle: return None
        m = alle[0] if anteil is None else min(alle, key=lambda x: abs(x.start() / len(s) - anteil))
        seiten = re.findall(r'⟦S\.(\d+)⟧', s[:m.start()])
        # Satz um den Treffer
        # Satzgrenzen: „. “ – aber nicht nach Abkürzungen wie „d. h.“, „u.“, „v. Chr.“ oder Zahlen
        ende = [x.start() for x in re.finditer(r'(?<![ (][a-zäöüA-Z])(?<![ (][a-zäöü][a-zäöü])(?<!\d)\. (?=[A-ZÄÖÜ„])', s)]
        import bisect
        k = bisect.bisect_left(ende, m.start())
        a = ende[k - 1] + 2 if k > 0 and m.start() - ende[k - 1] < 320 else max(0, m.start() - 160)
        e = ende[k] + 1 if k < len(ende) and ende[k] - m.end() < 260 else m.end() + 160
        if e - a > 330:   # zu lang: Ausschnitt um den Treffer
            a2 = max(a, m.start() - 150); e2 = min(e, m.end() + 170)
            if a2 > a: a2 = s.find(' ', a2) + 1          # nicht mitten im Wort
            if e2 < e: e2 = s.rfind(' ', a2, e2)
            roh = ('… ' if a2 > a else '') + s[a2:e2] + (' …' if e2 < e else '')
        else: roh = s[a:e]
        satz = re.sub(r'\s*⟦S\.\d+⟧\s*', ' ', roh).strip()
        satz = re.sub(r'^(?:… )?[\W\dlIv]{1,3}\)\s*', '', satz)                  # Rest einer Fußnote am Satzanfang
        satz = re.sub(r"\s*[’'`\"]\)\s[A-ZÄÖÜ][^.()]{0,40}\.", '', satz)   # eingestreute Fußnotentexte
        satz = re.sub(r'\s\d{1,2}\)|\s[*x•]\)|\s[*•]', '', satz)          # Fußnotenzeichen
        satz = re.sub(r'\s+([,;.])', r'\1', satz)
        return {'seite': int(seiten[-1]) if seiten else None, 'zitat': satz}
