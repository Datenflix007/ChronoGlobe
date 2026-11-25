# -*- coding: utf-8 -*-
"""Versionsangaben gegen veraltete Browser-Caches setzen (kein Build-Schritt nötig).

GitHub Pages lässt Dateien 10 Minuten im Browser-Cache. Ohne Versionsangabe kann ein Browser nach einem Deploy
altes js/app.js mit neuen Daten mischen. Dieses Werkzeug
  1. hängt an jedes <script src="js|vendor/…"> und <link href="css/…"> in den HTML-Seiten ?v=<Inhalts-Hash>,
  2. schreibt js/version.js mit den Hashes aller Dateien, die per fetch geladen werden (data/, tafelbilder/, …).
     window.cgUrl('data/reiche.json') ergibt dann 'data/reiche.json?v=<hash>'. Der Service Worker (sw.js) nutzt
     dieselbe Liste zum Vorladen.

    python tools/version_setzen.py            # Angaben aktualisieren (vor jedem Commit)
    python tools/version_setzen.py --pruefen  # nur prüfen; Rückgabewert 1, wenn etwas veraltet ist (CI)
"""
import hashlib, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEITEN = ['index.html', 'app.html', 'quellen.html', 'lehrkraft.html', 'editor.html']
ZIEL = os.path.join(ROOT, 'js', 'version.js')
# Per fetch geladene Dateien (und Grundtexturen) – keine Kacheln, die sind zu zahlreich und ändern sich kaum
MANIFEST = [('data', ('.json',)), ('tafelbilder', ('.json', '.md', '.png', '.jpg', '.webp')), ('docs', ('.md',)),
            ('vendor', ('.js',)), ('js', ('.js',)), ('css', ('.css',)), ('img', ('.jpg', '.png', '.webp'))]
OHNE = ('img/tiles', 'img/tiles_schem', 'tafelbilder/_vorlage')
# version.js steht nicht in sich selbst, die HTML-Seiten nicht im Manifest (sie verweisen auf version.js: sonst ein Zirkel)
SELBST = 'js/version.js'
VERWEIS = re.compile(r'((?:src|href)=")((?:js|css|vendor)/[^"?#]+)(?:\?v=[0-9a-f]+)?(")')


def kurz(pfad):
    with open(pfad, 'rb') as f: return hashlib.sha1(f.read()).hexdigest()[:10]


def manifest():
    d = {}
    for ordner, endungen in MANIFEST:
        for wurzel, _, dateien in os.walk(os.path.join(ROOT, ordner)):
            rel_w = os.path.relpath(wurzel, ROOT).replace(os.sep, '/')
            if rel_w.startswith(OHNE): continue
            if ordner == 'img' and rel_w not in ('img', 'img/icons', 'img/weltbilder'): continue
            for n in sorted(dateien):
                if n.endswith(endungen) and rel_w + '/' + n != SELBST: d[rel_w + '/' + n] = kurz(os.path.join(wurzel, n))
    return dict(sorted(d.items()))


def version_js(m):
    stand = hashlib.sha1(json.dumps(m, sort_keys=True).encode()).hexdigest()[:10]
    zeilen = ',\n'.join('    %s: %s' % (json.dumps(k), json.dumps(v)) for k, v in m.items())
    return ('/* Automatisch erzeugt von tools/version_setzen.py – nicht von Hand ändern.\n'
            '   Inhalts-Hashes der per fetch geladenen Dateien: cgUrl(u) hängt ?v=<hash> an, damit nach einem Deploy\n'
            '   keine veralteten Dateien aus dem Browser-Cache kommen. sw.js nutzt dieselbe Liste. */\n'
            'self.CG_VERSION = {\n  stand: %s,\n  dateien: {\n%s\n  }\n};\n'
            'self.cgUrl = function (u) {\n'
            '  var v = self.CG_VERSION.dateien[u];\n'
            '  return v ? u + (u.indexOf(\'?\') < 0 ? \'?\' : \'&\') + \'v=\' + v : u;\n'
            '};\n') % (json.dumps(stand), zeilen)


def main():
    pruefen = '--pruefen' in sys.argv
    veraltet = []
    neu = version_js(manifest())
    alt = open(ZIEL, encoding='utf-8').read() if os.path.exists(ZIEL) else ''
    if neu != alt:
        veraltet.append('js/version.js')
        if not pruefen:
            with open(ZIEL, 'w', encoding='utf-8', newline='\n') as f: f.write(neu)
    for seite in SEITEN:
        p = os.path.join(ROOT, seite)
        if not os.path.exists(p): continue
        with open(p, encoding='utf-8', newline='') as f: html = f.read()
        def ersetzen(m):
            ziel = os.path.join(ROOT, m.group(2))
            return m.group(1) + m.group(2) + ('?v=' + kurz(ziel) if os.path.isfile(ziel) else '') + m.group(3)
        neu_html = VERWEIS.sub(ersetzen, html)
        if neu_html != html:
            veraltet.append(seite)
            if not pruefen:
                with open(p, 'w', encoding='utf-8', newline='') as f: f.write(neu_html)
    if pruefen:
        if veraltet:
            print('Versionsangaben veraltet: ' + ', '.join(veraltet) + '\n→ python tools/version_setzen.py ausführen')
            sys.exit(1)
        print('Versionsangaben aktuell')
    else:
        print(('Aktualisiert: ' + ', '.join(veraltet)) if veraltet else 'Versionsangaben waren aktuell')


if __name__ == '__main__':
    main()
