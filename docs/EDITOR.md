# Editor und Themenebenen

Stand: 24.11.2026.

## Ziel

Nutzer:innen schlagen Änderungen und neue Ebenen vor, ohne Programmierkenntnisse und ohne eigenen Server:

1. **Editor** (`editor.html`, `js/editor.js`): Formular und Zeichenkarte.
2. **Beitrag** als JSON-Datei. Er wird im Browser als Entwurf gemerkt (`localStorage`).
3. **Pull Request** über GitHubs Seite „Neue Datei“ mit fertigem Inhalt. Wer keine Schreibrechte hat, bekommt von GitHub automatisch eine Kopie (Fork) und einen Pull Request angeboten. Zu große Beiträge lädt man als Datei herunter und unter `beitraege/` hoch.
4. **Prüfung:** Die CI prüft das Format (`node tools/check_beitraege.js`). Das Projektteam prüft den Inhalt nach `docs/GRUNDREGELN.md`.
5. **Übernahme** von Hand (siehe `beitraege/README.md`).

Datenschutz: Der Editor lädt nur Dateien dieses Projekts und fragt keine Namen ab. GitHub öffnet sich erst auf Knopfdruck, mit dem eigenen Konto der Person. Die Content-Security-Policy gilt auch für `editor.html`.

## Bedienung

- **Start:** vier Wege – Änderung vorschlagen, neue Themenebene zeichnen, mit KI aus einem Datensatz, Datei importieren.
- **Schrittanzeige** im Kopf (Art · Inhalt · Belege · Einreichen) und ein Status („3 offen“, „✓ bereit“).
- **Karte:**
  - Klick setzt Punkte (✎, Esc schaltet zwischen Zeichnen und Auswählen um).
  - Punkte des aktiven Objekts lassen sich ziehen; ein Rechtsklick löscht einen Punkt.
  - Im Auswahlmodus wählt ein Klick auf ein Objekt es aus.
  - Zoom, Einpassen, ganze Welt; Koordinaten unter dem Mauszeiger.
- **Zeitfilter:** zeigt die Reiche eines Jahres zur Orientierung und macht Objekte außerhalb ihres Zeitraums blass.
- **Objektliste:** Suche, Sortierung nach Zeit oder Name, Hinweis auf fehlende Angaben, Duplizieren, „Auf der Karte zeigen“, Länge/Breite für alle tauschen.
- **Rückgängig/Wiederholen:** Strg+Z, Strg+Y (bis zu 150 Schritte).
- **Import:** GeoJSON (Punkte, Linien, Flächen, auch Multi-Geometrien), CSV (Trenner `;` `,` Tab, Dezimalkomma, Spalten wie `name`, `lat`/`breite`, `lng`/`laenge`, `von`, `bis`, `beschreibung`, `beleg`) oder JSON-Listen.

## KI-Assistent (`js/ki.js`)

Für Datensätze, die man nicht von Hand zeichnen will (Fundortlisten, Tabellen aus Büchern, GeoJSON aus Forschungsprojekten):

1. **Prompt erstellen:** Datensatz einfügen oder laden, Ziel wählen (neue Ebene oder Änderung), optional Thema und Wünsche. Der Editor erzeugt einen Prompt mit Zielformat, Beispiel, den Grundregeln (nichts erfinden, Länge vor Breite, v. Chr. negativ, Umstrittenes kennzeichnen, echte Belege) und dem Datensatz.
2. **In eine KI der Wahl kopieren.** Der Editor sendet selbst nichts (Datenschutz, keine fremden Server).
3. **Antwort einfügen:** Der Editor findet das JSON auch zwischen Text oder in Codeblöcken, repariert Kommentare, Kommas und Anführungszeichen, wandelt Jahresangaben wie „um 3800 v. Chr.“ um, ergänzt ids, erkennt eindeutig vertauschte Koordinaten und nimmt auch reines GeoJSON oder eine bloße Ebene an.
4. **Anweisungen für den Editor** stehen im Feld `_editor` der Antwort und werden nicht eingereicht:

   ```js
   _editor: { karte: { zentrum: [lng, lat], zoom }, jahr, pruefen: ['…'], ausgelassen: ['…'] }
   ```

   Der Editor zoomt dorthin, stellt den Zeitfilter auf `jahr` und zeigt `pruefen` als Checkliste. Offene Prüfpunkte erscheinen im Status.
5. „In den Editor übernehmen“ ersetzt den Entwurf (Strg+Z macht es rückgängig); „Nur Objekte anhängen“ ergänzt die aktuelle Ebene, etwa wenn ein großer Datensatz in Teilen verarbeitet wird.

Die KI-Antwort ist ein Vorschlag wie jeder andere: Belege, Lagen und Jahre müssen von Menschen geprüft werden, bevor der Beitrag eingereicht wird.

## Was man vorschlagen kann

| Art | Bereiche | Ergebnis |
|---|---|---|
| Änderung | Gebiet, Ort oder Ereignis eines Reiches · Handelsroute, Handelsort, Gesandtschaft · Schülertext · Schriftrolle · Objekt einer Themenebene · Sonstiges | Beschreibung, optional neue Werte (Name, von, bis) und neue Geometrie. Die bisherige Geometrie ist grau gestrichelt. |
| Neue Themenebene | beliebiges Thema (Pyramiden, Klöster, Fundorte …) | Orte, Linien und Flächen mit Jahreszahlen, Beschreibung und Beleg |

Neue Ebenen lassen sich vor dem Einreichen auf dem Globus ansehen: „Auf dem Globus ansehen“ öffnet `app.html?modus=frei&vorschau=editor`. Die Vorschau kommt aus dem `localStorage` dieses Browsers, erscheint als „(Vorschau)“ und steht nicht im geteilten Zustand (Live-Sessions).

Aus dem Infofenster eines Themenobjekts führt „Korrektur vorschlagen“ direkt in den Editor (`editor.html?ziel=ebene:<ebene>:<objekt>`).

## Formate (`js/themen.js`)

Prüfregeln, Zeitfilter und PR-Link stehen in einem Modul, das Globus, Editor und CI gemeinsam nutzen.

### Themenebene (`data/ebenen/<id>.json`)

```js
{ format: 'chronoglobe-ebene/1', id, name, farbe: '#rrggbb', beschreibung, hinweis?,
  quellen: [{ zitat, url?, lizenz? }],                     // mindestens eine
  objekte: [{ id, typ: 'punkt' | 'linie' | 'flaeche', name, von, bis?, beschreibung?, beleg?, unsicher?,
              koordinaten }] }                              // punkt [lng, lat] · linie/flaeche [[lng, lat], …]
```

- Jahre als ganze Zahlen, v. Chr. negativ. Ohne `bis` bleibt ein Objekt bis zum Ende der Zeitleiste sichtbar (z. B. Bauwerke).
- `unsicher: true` zeichnet Linien gestrichelt und zeigt einen Hinweis.
- Flächen erscheinen auf dem Globus als Umriss. Gefüllte Flächen wären ein nächster Schritt; sie bräuchten eine eigene Polygon-Ebene neben den Reichen.

Register `data/ebenen/index.json`:

```js
{ ebenen: [{ id, name, farbe, datei: 'data/ebenen/<id>.json', von, bis, kurz }] }
```

`von`/`bis` müssen zur Datei passen; die CI prüft das. Im Menü erscheint der Bereich „Themenebenen“. Tafelbilder zeigen ihn nur, wenn ihre `ebenen.verfuegbar` `themen` enthält (oder `alle` ist). Der Zustand steht in `getState().themen` (Regel 4).

### Beitrag (`beitraege/JJJJ-MM-TT-titel.json`)

```js
{ format: 'chronoglobe-beitrag/1', art: 'neue-ebene' | 'aenderung', titel, begruendung,
  belege: [{ zitat, url? }],                                // mindestens einer
  ebene?: Themenebene,                                      // bei 'neue-ebene'
  ziel?: { bereich, datei, id, name },                      // bei 'aenderung'
  vorschlag?: { text, felder?: { name?, von?, bis? }, geometrie?: { typ, koordinaten } } }
```

## Einstellungen

- Ziel-Repository und Zweig: `REPO`, `ZWEIG` oben in `js/editor.js` (derzeit `Datenflix007/ChronoGlobe`, `main`).
- Längengrenze für den PR-Link: `URL_GRENZE` in `js/themen.js`.

## Tests

- `python tests/test_editor.py`: Startseite, Ebene anlegen, Kartenklick, Punkte ziehen, Rückgängig, KI-Assistent (Prompt, Antwort, `_editor`), CSV-Import, Prüfung, PR-Link, Vorschau auf dem Globus, Änderung an einem Reichsgebiet.
- `node tests/ki.test.js`: Prompt, Einlesen fehlerhafter KI-Antworten, GeoJSON- und CSV-Import.
- `node tools/check_beitraege.js`: alle Beiträge und übernommenen Ebenen.

## Nächste Schritte

- **Übernahme automatisieren:** ein Skript, das eine geprüfte neue Ebene nach `data/ebenen/` kopiert und das Register schreibt.
- **Änderungen als Diff:** `vorschlag` direkt als Patch auf die Zieldatei, bei erzeugten Dateien auf die Eingabe des `build_*.py`.
- **„Korrektur vorschlagen“** auch in den Infofenstern von Reichen, Routen und Orten (bisher nur bei Themenobjekten).
- **Schriftrollen-Bausteine** im Editor bearbeiten (Format `docs/VIGNETTEN.md`), statt sie nur zu beschreiben.
- **Geometrie bearbeiten:** Punkte verschieben, Flächen aus vorhandenen Reichsgebieten übernehmen.
- **Gefüllte Flächen** auf dem Globus.
