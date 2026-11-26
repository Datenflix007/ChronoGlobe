# ChronoGlobe – Regeln für Änderungen

ChronoGlobe ist eine statische Seite ohne Build-Schritt: globe.gl, d3 und reines Browser-JavaScript. Veröffentlicht wird sie unter https://datenflix007.github.io/ChronoGlobe/. Alle Pfade sind relativ.

## Kern und Tafelbilder

| Bereich | Dateien | Gilt für |
|---|---|---|
| **Kern** („Menschheitsgeschichte“) | `app.html`, `js/`, `css/`, `vendor/`, `img/`, `data/`, `build_*.py`, `sql/` | alle Modi und alle Tafelbilder |
| **Tafelbild** | `tafelbilder/<id>/` (`tafelbild.json`, Vorschaubild, Lehrerhinweise, eigene Daten-Overlays) | nur dieses Tafelbild |
| Register | `tafelbilder/index.json` | Galerie und Session-Erstellung |
| Startseite | `index.html`, `js/landing.js`, `css/landing.css` | Moduswahl |
| Editor | `editor.html`, `js/editor.js`, `js/themen.js`, `js/ki.js`, `css/editor.css`, `beitraege/` | Vorschläge als Pull Request |

## Regeln

1. **Auftrag „nur Tafelbild X“:** ausschließlich Dateien unter `tafelbilder/X/` ändern.
   - Fehlt dafür etwas im Kern, das melden und nicht stillschweigend den Kern ändern.
2. **Kernänderungen dürfen kein Tafelbild brechen.** Nach jeder Kernänderung ausführen:
   - `python tools/check_tafelbilder.py`: Schema, IDs, referenzierte Dateien.
   - `python tests/test_regression.py "app.html?tafelbild=rom-zentrum-der-welt"`: Klickfolge gegen den gespeicherten Ausgangszustand.
     - Gewollte Verhaltensänderungen: Ausgangszustand vorher mit `--aufnehmen` neu speichern und die Änderung im Commit begründen.
   - `python tools/version_setzen.py`: Versionsangaben (`?v=`, `js/version.js`) nach jeder Änderung an `js/`, `css/`, `data/`, `vendor/` oder Tafelbild-Dateien aktualisieren.
   - Je nach Bereich zusätzlich:
     - `node tests/strassenzeit.test.js`
     - `python tests/test_strassen_browser.py`
     - `python tests/test_session.py`
     - `node tests/netze.test.js`
     - `python tests/test_netze_browser.py`
     - `node tests/suche.test.js` und `python tests/test_suche_browser.py` (Suche)
     - `python tests/test_csp.py` (bei neuen Skripten, Seiten oder externen Verbindungen)
     - `python tests/test_weltbilder.py` (Weltbilder, Schriftrolle, Hülle auf dem Globus)
     - `python tests/test_editor.py`, `node tests/ki.test.js` und `node tools/check_beitraege.js` (Editor, KI-Assistent, Themenebenen, Beiträge)
3. **Neue Tafelbilder:**
   - Aus `tafelbilder/_vorlage/` anlegen und in `tafelbilder/index.json` eintragen.
   - Anleitung: `docs/TAFELBILD_ERSTELLEN.md`.
4. **Zustand:**
   - Sichtbarer Zustand ändert sich nur über `setState`/`applyState` in `js/app.js`.
   - Ein neuer Schalter oder ein neues Fenster gehört in `getState`/`applyState`. Sonst funktioniert er in Live-Sessions nicht (siehe `docs/ARCHITEKTUR.md`).
5. **Grundregeln für Inhalte** gelten weiter: `docs/GRUNDREGELN.md` (Belege, Zitierweise, Niveaus, Zitatrecht).
   - Erfundene Rahmenerzählungen kennzeichnen.
   - Umstrittenes als umstritten darstellen.
6. **Datenschutz:**
   - Freier Modus und Tafelbilder laden nichts von fremden Servern.
   - Supabase (`vendor/supabase.min.js`, `js/config.js`) wird nur in Session-Seiten nachgeladen.
   - Im Frontend steht nur der Publishable Key, nie ein Secret Key.
   - Die Content-Security-Policy (`js/csp.js`) erzwingt das. Keine Inline-Skripte, keine fremden Server.
   - Keine Namen, Konten oder personenbezogenen Daten.
7. **Sprache:** Oberfläche, Kommentare und Dokumentation auf Deutsch.
8. **Git:**
   - Nicht pushen und nicht nach `main` mergen ohne Rückfrage.
   - Commit-Nachrichten ohne „Co-Authored-By“-Zeile.

## Wichtige Dokumente

- `docs/ARCHITEKTUR.md`: Kern, Zustand, Modi, Synchronisierung, Rechte
- `docs/TAFELBILD_ERSTELLEN.md`: neues Tafelbild Schritt für Schritt
- `docs/SETUP.md`: Supabase für Live-Sessions einrichten
- `docs/EDITOR.md`: Editor, Beiträge als Pull Request, Themenebenen (`data/ebenen/`)
- `docs/HANDELSNETZE.md`: Handels- und Verkehrsnetze (Datenmodell, Zeitfilter, Quellen, Download)
- `docs/VIGNETTEN.md`, `docs/STRASSEN_ZEITMODELL.md`, `docs/DATENQUELLEN.md`, `docs/GRUNDREGELN.md`
