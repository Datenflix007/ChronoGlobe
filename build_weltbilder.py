# -*- coding: utf-8 -*-
"""Weltbilder: die Welt, wie ein antiker Autor oder eine mittelalterliche Karte sie zeigt.

Erzeugt:
  data/weltbilder/index.json                  Liste der Weltbilder
  data/weltbilder/<id>.json                   Einträge mit Lage auf dem Globus (und auf der Karte), Beleg, Text
  img/weltbilder/<id>_projektion.webp         Bild für den Globus (gleichabständige Zylinderprojektion, Ausschnitt „bbox“)
  img/weltbilder/ebstorf/<z>/<x>_<y>.jpg      Kachelpyramide der Ebstorfer Karte für die Schriftrolle (512 px)

Plinius (weltbilder_plinius.py): Er hinterließ keine Karte. Gezeigt werden Orte, Völker, Flüsse, Gebirge, Meere und
Vorstellungen aus der Naturalis historia (Bücher 3–7, 12) an ihrer heutigen Lage, dazu der Seeweg nach Indien (6,101–106)
und – abgedunkelt – was jenseits der ihm bekannten Welt lag. Jeder Eintrag wird beim Build am lateinischen Text
(Mayhoff) und an Wittsteins Übersetzung (1881) belegt (weltbilder_quellen.py); fehlt ein Beleg, bricht der Build ab.

Ebstorfer Weltkarte (weltbilder_ebstorf.py): Vorlage „Ebstorfer Weltkarte 2.jpg“ (7849 × 7798, Wikimedia Commons,
gemeinfrei; digitale Ausgabe der Leuphana Universität Lüneburg). Lage der Beschriftungen auf der Karte nach der
Leuphana-Ausgabe (HyperImage, 2008), wirkliche Lage und Erläuterungen eigene Angaben.
Optional wird die Karte über alle verortbaren Einträge als Passpunkte auf den Globus gelegt (Ähnlichkeitsabbildung plus
geglättete Thin-Plate-Spline, Glättung automatisch so gewählt, dass sich die Karte nicht faltet).

    python build_weltbilder.py
"""
import io, json, math, os, re, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from weltbilder_plinius import P as PL_EINTRAEGE, INDIENFAHRT, INDIENFAHRT_WEG
from weltbilder_ebstorf import E as EB_E, BILDFELDER as EB_BF, KLEIN_ZU_GROSS
from weltbilder_quellen import Latein, Deutsch

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
LOKAL = os.path.join(HERE, 'quellen', 'lokal', 'weltbilder')
DATA = os.path.join(HERE, 'data', 'weltbilder')
IMG = os.path.join(HERE, 'img', 'weltbilder')

EB_URL = 'https://upload.wikimedia.org/wikipedia/commons/c/c4/Ebstorfer_Weltkarte_2.jpg'
EB_LEUPHANA = 'https://warnke.web.leuphana.de/hyperimage/EbsKart/postPetal/V1010.xml'
EB_KREIS = (0.4961, 0.4965, 0.4990)   # Mittelpunkt (x, y) und Halbmesser der Kartenscheibe, Anteile der Bildbreite
KACHEL = 512


def laden(url, ziel):
    if not os.path.exists(ziel):
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        print('lade', url)
        req = urllib.request.Request(url, headers={'User-Agent': 'ChronoGlobe-Build/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r, open(ziel, 'wb') as f: f.write(r.read())
    return ziel


def schreiben(pfad, d):
    with io.open(pfad, 'w', encoding='utf-8', newline='\n') as f: json.dump(d, f, ensure_ascii=False, separators=(',', ':'))


# ---------------------------------------------------------------------------------------------------------------
#  Plinius
# ---------------------------------------------------------------------------------------------------------------
PL_HORIZONT = [(-19, 27), (-14, 33), (-12, 37), (-11, 44), (-12, 52), (-14, 58), (-18, 64), (-10, 67), (5, 66), (20, 64), (32, 61), (45, 59),
               (60, 56), (75, 52), (90, 47), (104, 42), (108, 35), (103, 27), (95, 21), (88, 17), (82, 5), (78, 6), (73, 13), (66, 21),
               (58, 16), (52, 12), (45, 10), (38, 11), (33, 13), (25, 17), (15, 19), (5, 21), (-6, 23), (-14, 24), (-19, 27)]
PL_META = {
    'id': 'plinius', 'titel': 'Die Welt nach Plinius', 'zeit': '77 n. Chr.', 'jahr': 77,
    'kurz': 'Plinius der Ältere (23/24–79 n. Chr.) beschreibt in seiner Naturgeschichte (Bücher 3–6) die bewohnte Erde '
            'Küste für Küste: von der Meerenge bei Gades über Europa, Afrika und Asien bis zu den Serern, in Buch 7 die '
            'Wundervölker an ihren Rändern. Eine Karte hinterließ er nicht. Gezeigt sind Orte, Völker und Vorstellungen aus '
            'seinem Text an ihrer heutigen Lage, jeweils mit Stelle und dem Wortlaut der Übersetzung.',
    'umgang': 'Der dunkle Bereich zeigt schematisch, was jenseits der Welt lag, die Plinius kannte. Am Rand mischt sich gesichertes '
              'Wissen (Meroe, Taprobane, der Seeweg nach Indien) mit Hörensagen und Fabelwesen. Plinius gibt solche Berichte oft '
              'mit „man sagt“ oder unter Nennung seiner Gewährsleute weiter. Rot markiert sind Irrtümer, violett Fabelwesen.',
    'erdmass': 'Länge der bewohnten Erde von Indien bis zu den Säulen des Hercules: nach Artemidor rund 8 570, nach Isidor rund 9 820 '
               'römische Meilen (Plinius, Naturgeschichte 2,242) – etwa 12 700 bzw. 14 500 km. Tatsächlich sind es auf dem Breitenkreis '
               'gut 10 000 km.',
    'literatur': 'C. Plinius Secundus, Naturalis historia, hg. von Karl Mayhoff, Leipzig 1892–1909 (lateinischer Text bei LacusCurtius); '
                 'Die Naturgeschichte des Cajus Plinius Secundus, übers. von G. C. Wittstein, Bd. 1, Leipzig 1881 (gemeinfrei, archive.org).',
}


def plinius():
    q = os.path.join(LOKAL, 'plinius'); L = Latein(q); D = Deutsch(q)
    eintraege, fehlt = [], []
    for i, name, heute, lng, lat, art, stufe, b, la, de, ab, notiz in PL_EINTRAEGE:
        n = L.finde(b, la, ab)
        w = D.finde(b, de, None if b == 7 else L.anteil(b, n)) if n is not None and b <= 7 else None
        if n is None or (b <= 6 and w is None): fehlt.append(i); continue
        e = {'id': i, 'name': name, 'heute': heute, 'lng': lng, 'lat': lat, 'typ': art, 'stufe': stufe,
             'beleg': 'Plinius, Naturgeschichte %d,%d' % (b, n)}
        if notiz: e['text'] = notiz
        if w:
            e['zitat'] = w['zitat']
            e['zitat_beleg'] = 'Übers. G. C. Wittstein, Bd. %d, Leipzig 1881%s' % (2 if b >= 7 else 1, ', S. %d' % w['seite'] if w['seite'] else '')
        eintraege.append(e)
    if fehlt: raise SystemExit('Plinius: kein Beleg für ' + ', '.join(fehlt))
    # Seeweg nach Indien
    for s in INDIENFAHRT:
        if not L.finde(6, re.escape(s[0][:5])): raise SystemExit('Indienfahrt: %s nicht in Buch 6' % s[0])
    fahrt = {'name': 'Der Seeweg nach Indien', 'beleg': 'Plinius, Naturgeschichte 6,101–106', 'weg': INDIENFAHRT_WEG,
             'stationen': [{'name': n, 'lng': x, 'lat': y, 'text': t} for n, x, y, t in INDIENFAHRT],
             'text': 'Plinius beschreibt die Reise von Alexandria nach Indien Etappe für Etappe: auf dem Nil, durch die Wüste zum Roten '
                     'Meer und mit dem Monsunwind (Hippalus) über den Ozean. Er klagt, Indien nehme dem Reich jährlich mindestens '
                     '50 Millionen Sesterzen ab. Die Linie ist schematisch.'}
    # Abdunkeln jenseits der bekannten Welt (ganze Erde, weicher Rand)
    B, H = 2048, 1024
    def px(p): return ((p[0] + 180) / 360 * B, (90 - p[1]) / 180 * H)
    maske = Image.new('L', (B, H), 0)
    ImageDraw.Draw(maske).polygon([px(p) for p in PL_HORIZONT], fill=255)
    maske = maske.filter(ImageFilter.GaussianBlur(9))
    a = 255 - np.asarray(maske).astype(np.float32)
    rgba = np.zeros((H, B, 4), np.uint8); rgba[..., 0] = 10; rgba[..., 1] = 14; rgba[..., 2] = 24
    rgba[..., 3] = (a * 0.72).astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(os.path.join(IMG, 'plinius_projektion.webp'), quality=80, method=6)
    d = dict(PL_META)
    d.update({'art': 'text', 'projektion': {'datei': 'img/weltbilder/plinius_projektion.webp', 'bbox': [-180, -90, 180, 90], 'deckkraft': 1},
              'horizont': [list(p) for p in PL_HORIZONT], 'route': fahrt, 'eintraege': eintraege})
    print('Plinius: %d Einträge, alle belegt' % len(eintraege))
    return d


# ---------------------------------------------------------------------------------------------------------------
#  Ebstorfer Weltkarte
# ---------------------------------------------------------------------------------------------------------------
EB_META = {
    'id': 'ebstorf', 'titel': 'Ebstorfer Weltkarte', 'zeit': 'um 1300', 'jahr': 1300,
    'mitte': 'jerusalem',
    'kurz': 'Größte bekannte mittelalterliche Weltkarte: eine Radkarte von rund 3,6 m Durchmesser auf 30 Pergamentblättern, entstanden '
            'vermutlich im Kloster Ebstorf (Lüneburger Heide). Osten oben, Jerusalem in der Mitte, die Erde als Leib Christi. '
            'Die Datierung ist umstritten (früher um 1235, heute meist um 1300). Das Original verbrannte 1943 in Hannover; '
            'erhalten sind Fotografien von 1891 und Nachbildungen.',
    'umgang': 'Die Karte ist eine Heilskarte: Sie ordnet die Welt nach Bibel, Legende und antiker Überlieferung, nicht nach '
              'Entfernungen. Jeder Punkt auf dem Globus ist eine Beschriftung der Karte an ihrer wirklichen Lage; ein Klick zeigt, '
              'wo sie auf der Karte steht. Die Karte lässt sich zusätzlich verzerrt auf den Globus legen – das zeigt, wie anders '
              'sie die Welt ordnet, ist aber nur eine Annäherung.',
    'bild_herkunft': 'Abbildung: digitale Ausgabe der Ebstorfer Weltkarte, Leuphana Universität Lüneburg (Wikimedia Commons, '
                     '„Ebstorfer Weltkarte 2.jpg“, gemeinfrei; laut Projektleitung kein Urheberrecht beansprucht).',
    'leuphana': 'Lage der Beschriftungen nach der interaktiven Ausgabe „HyperEbsKart“ der Leuphana Universität Lüneburg (2008; '
                'Transkription und Übersetzung: Hartmut Kugler). Dort sind alle rund 1 400 Bildfelder mit Übersetzung zu lesen.',
    'leuphana_url': 'https://warnke.web.leuphana.de/hyperimage/EbsKart/index.html',
    'literatur': 'Hartmut Kugler (Hg.), Die Ebstorfer Weltkarte. Kommentierte Neuausgabe in zwei Bänden, Berlin 2007.',
}
ART_TEXT = {'stadt': 'Stadt', 'kloster': 'Kloster oder Kirche', 'bibel': 'biblische Stätte', 'legende': 'Legende', 'region': 'Land', 'natur': 'Fluss, Berg, Meer oder Insel'}


def leuphana_lagen():
    s = open(laden(EB_LEUPHANA, os.path.join(LOKAL, 'ebstorf', 'leuphana_V1010.xml')), encoding='utf-8').read()
    lagen = {}
    for blk in re.findall(r'<layer .*?</layer>', s, re.S):
        pm = re.search(r'points="([^"]+)"', blk); la = re.search(r'<content[^>]*>(.*?)</content>', blk, re.S)
        if not pm or not la: continue
        pts = [tuple(map(float, p.split(','))) for p in pm.group(1).split()]
        lagen.setdefault(la.group(1).strip(), []).append((sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)))
    return lagen


def tps_anpassen(quelle, ziel, glatt=0.0):
    """Thin-Plate-Spline von quelle (n×2) nach ziel (n×2); gibt f(P: m×2) → m×2 zurück."""
    n = len(quelle)
    def U(r2): return np.where(r2 == 0, 0.0, r2 * np.log(r2 + 1e-12))
    d2 = ((quelle[:, None, :] - quelle[None, :, :]) ** 2).sum(-1)
    A = np.zeros((n + 3, n + 3)); A[:n, :n] = U(d2) + glatt * np.eye(n)
    Pm = np.hstack([np.ones((n, 1)), quelle]); A[:n, n:] = Pm; A[n:, :n] = Pm.T
    b = np.zeros((n + 3, 2)); b[:n] = ziel
    w = np.linalg.solve(A, b)
    def f(X):
        r2 = ((X[:, None, :] - quelle[None, :, :]) ** 2).sum(-1)
        return U(r2) @ w[:n] + w[n] + X @ w[n + 1:]
    return f


def kacheln(im, ordner):
    """Kachelpyramide: Stufe z hat die Breite W / 2^(zmax - z); Kacheln 512 px, Dateien <z>/<x>_<y>.jpg"""
    W, H = im.size; zmax = math.ceil(math.log2(max(W, H) / KACHEL)); stufen = []
    for z in range(zmax + 1):
        f = 2 ** (zmax - z); w, h = math.ceil(W / f), math.ceil(H / f)
        st = im if f == 1 else im.resize((w, h), Image.LANCZOS)
        os.makedirs(os.path.join(ordner, str(z)), exist_ok=True)
        for x in range(math.ceil(w / KACHEL)):
            for y in range(math.ceil(h / KACHEL)):
                st.crop((x * KACHEL, y * KACHEL, min(w, (x + 1) * KACHEL), min(h, (y + 1) * KACHEL))).save(
                    os.path.join(ordner, str(z), '%d_%d.jpg' % (x, y)), quality=76, optimize=True, progressive=True)
        stufen.append([w, h])
    return stufen


def ebstorf():
    src = laden(EB_URL, os.path.join(LOKAL, 'Ebstorfer_Weltkarte_2.jpg'))
    im = Image.open(src).convert('RGB'); W, H = im.size
    # Einträge: Lage auf der Karte (Anteile der Bildbreite/-höhe)
    lagen = leuphana_lagen(); eintraege = []
    for la, i, name, lng, lat, art, stufe, text in EB_E:
        h = lagen.get(la)
        if not h or len(h) != 1: raise SystemExit('Ebstorf: Beschriftung „%s“ nicht eindeutig in der Leuphana-Ausgabe' % la)
        e = {'id': i, 'name': name, 'inschrift': la.rstrip('.').replace(' (= Kreta)', ''), 'bild': [round(h[0][0], 4), round(h[0][1], 4)],
             'typ': art, 'stufe': stufe, 'beleg': 'Ebstorfer Weltkarte (um 1300), Beschriftung „%s“' % la.rstrip('.').replace(' (= Kreta)', '')}
        if text: e['text'] = text
        if lng is not None: e.update(lng=lng, lat=lat)
        eintraege.append(e)
    s, dx, dy = KLEIN_ZU_GROSS
    for i, name, bx, by, lng, lat, art, stufe, text in EB_BF:
        e = {'id': i, 'name': name, 'bild': [round((s * bx + dx) / W, 4), round((s * by + dy) / H, 4)], 'typ': art, 'stufe': stufe,
             'text': text, 'beleg': 'Ebstorfer Weltkarte (um 1300), Bildfeld'}
        if lng is not None: e.update(lng=lng, lat=lat)
        eintraege.append(e)
    # Schriftrolle: Kachelpyramide + Übersicht
    stufen = kacheln(im, os.path.join(IMG, 'ebstorf'))
    # Projektion: Passpunkte = alle verortbaren Einträge
    pp = [e for e in eintraege if 'lng' in e]
    geo = np.array([[e['lng'], e['lat']] for e in pp], float); bild = np.array([[e['bild'][0] * W, e['bild'][1] * H] for e in pp], float)
    gm, gs = geo.mean(0), geo.std(0).mean(); bm, bs = bild.mean(0), bild.std(0).mean()
    G, Bn = (geo - gm) / gs, (bild - bm) / bs
    U_, S_, Vt = np.linalg.svd(Bn.T @ G); Rm = U_ @ Vt; sk = S_.sum() / (Bn ** 2).sum()
    cx, cy, R = EB_KREIS[0] * W, EB_KREIS[1] * H, EB_KREIS[2] * W
    xs, ys = np.meshgrid(np.linspace(cx - R, cx + R, 140), np.linspace(cy - R, cy + R, 140)); m = (xs - cx) ** 2 + (ys - cy) ** 2 < R ** 2
    Pk = (np.vstack([xs[m], ys[m]]).T - bm) / bs
    for glatt in (0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4):   # kleinste Glättung ohne Faltung
        spline = tps_anpassen(Bn, G, glatt)
        vor = lambda x, sp=spline: 0.2 * (sk * x @ Rm) + 0.8 * sp(x)
        a = vor(Pk); bx_ = vor(Pk + [1e-3, 0]); by_ = vor(Pk + [0, 1e-3])
        det = (bx_[:, 0] - a[:, 0]) * (by_[:, 1] - a[:, 1]) - (bx_[:, 1] - a[:, 1]) * (by_[:, 0] - a[:, 0])
        if min((det < 0).mean(), (det > 0).mean()) < 0.001: break
    rueck = tps_anpassen(G, Bn, glatt)
    bbox = [-40.0, -20.0, 140.0, 80.0]
    bw = 2600; bh = int(round(bw * (bbox[3] - bbox[1]) / (bbox[2] - bbox[0])))
    LNG, LAT = np.meshgrid(bbox[0] + (np.arange(bw) + 0.5) / bw * (bbox[2] - bbox[0]), bbox[3] - (np.arange(bh) + 0.5) / bh * (bbox[3] - bbox[1]))
    Z = (np.vstack([LNG.ravel(), LAT.ravel()]).T - gm) / gs
    out = np.zeros_like(Z); ok = np.zeros(len(Z), bool); h = 1e-4
    for i in range(0, len(Z), 150000):
        z = Z[i:i + 150000]; x = rueck(z)
        for _ in range(12):
            a = vor(x); r = a - z
            jx = (vor(x + [h, 0]) - a) / h; jy = (vor(x + [0, h]) - a) / h
            det = jx[:, 0] * jy[:, 1] - jy[:, 0] * jx[:, 1]; det = np.where(np.abs(det) < 1e-9, 1e-9, det)
            st = np.stack([(jy[:, 1] * r[:, 0] - jy[:, 0] * r[:, 1]) / det, (-jx[:, 1] * r[:, 0] + jx[:, 0] * r[:, 1]) / det], 1)
            x = x - st * np.minimum(1, 0.5 / np.maximum(np.linalg.norm(st, axis=1, keepdims=True), 1e-12))
        out[i:i + 150000] = x; ok[i:i + 150000] = np.linalg.norm(vor(x) - z, axis=1) * gs < 0.05
    X, Y = out[:, 0] * bs + bm[0], out[:, 1] * bs + bm[1]
    rd = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2); drin = (rd < R) & ok
    arr = np.asarray(im.resize((W // 2, H // 2), Image.LANCZOS))
    rgb = arr[np.clip((Y / 2).astype(int), 0, H // 2 - 1), np.clip((X / 2).astype(int), 0, W // 2 - 1)].reshape(bh, bw, 3)
    alpha = (np.where(drin, np.clip((R - rd) / 40.0, 0, 1), 0) * 255).astype(np.uint8).reshape(bh, bw)
    Image.fromarray(np.dstack([rgb, alpha]), 'RGBA').save(os.path.join(IMG, 'ebstorf_projektion.webp'), quality=78, method=6)
    rest = np.linalg.norm(vor(Bn) * gs + gm - geo, axis=1)
    for e, r_, k in zip(pp, rest, vor(Bn) * gs + gm):
        e['karte'] = [round(float(k[0]), 2), round(float(k[1]), 2)]
    d = dict(EB_META)
    d.update({'art': 'karte', 'bild': {'kacheln': 'img/weltbilder/ebstorf/', 'kachel': KACHEL, 'stufen': stufen, 'osten_oben': True},
              'projektion': {'datei': 'img/weltbilder/ebstorf_projektion.webp', 'bbox': bbox, 'deckkraft': 0.8, 'standard': False,
                             'passpunkte': len(pp), 'abweichung_mittel': round(float(rest.mean()), 1), 'abweichung_max': round(float(rest.max()), 1)},
              'eintraege': eintraege})
    print('Ebstorf: %d Einträge (%d verortbar), %d Kachelstufen, Glättung %.2f, Abweichung im Mittel %.1f°, höchstens %.1f°'
          % (len(eintraege), len(pp), len(stufen), glatt, rest.mean(), rest.max()))
    return d


def main():
    os.makedirs(DATA, exist_ok=True); os.makedirs(IMG, exist_ok=True)
    for alt in ('ebstorf_karte.jpg',):
        p = os.path.join(IMG, alt)
        if os.path.exists(p): os.remove(p)
    alle = [plinius(), ebstorf()]
    for d in alle: schreiben(os.path.join(DATA, d['id'] + '.json'), d)
    schreiben(os.path.join(DATA, 'index.json'), {'_hinweis': 'Erzeugt von build_weltbilder.py', 'weltbilder': [
        {'id': d['id'], 'titel': d['titel'], 'zeit': d['zeit'], 'art': d['art'], 'datei': 'data/weltbilder/%s.json' % d['id']} for d in alle]})


if __name__ == '__main__':
    main()
