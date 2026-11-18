# Digitales Tafelbild: Rom und China

<img width="946" height="631" alt="image" src="https://github.com/user-attachments/assets/62332721-ca48-4a0d-b88d-0c5059ea40fb" />


## Einbinden
1. Ordner `tafelbild/` in dein Repo `datenflix007.github.io` legen und pushen.
2. Erreichbar unter `https://datenflix007.github.io/tafelbild/`.
3. Verlinken: `<a href="tafelbild/">Digitales Tafelbild</a>`.
Lokal testen: `python3 -m http.server` im Ordner, dann http://localhost:8000 (nicht per Doppelklick öffnen).

## Bedienung
- Ansicht Satellit/Schematisch, Rom, Han und 11 Nachbarreiche ein-/ausblenden („Alle einblenden/ausblenden“), Menü einklappbar.
- Zeitstrahl ziehen (Punkte = Ereignisse, Schwerter = Schlachten), ←/→ Jahr, Shift = 10 Jahre, Leertaste = Abspielen.
  Die Spuren der Nachbarreiche lassen sich über „Nachbarreiche (n)“ einklappen.
- Auf Rom/China hineinzoomen (Mausrad/Pinch) oder „Karte entrollen“ → Reichskarte; Esc schließt.
- Standardmäßig markiert ein Pin Jena. „Mein Standort“ (Menü → Globus) ersetzt ihn nach Freigabe im Browser durch den eigenen Standort (nur lokal, keine Übertragung; benötigt HTTPS oder localhost).
- **Handel & Austausch** (Menü, Standard aus): Land- und Seewege, Waren, Gesandtschaften.
  - Gezeigt werden Verbindungen aller Reiche, die eingeblendet sind **und** im gewählten Jahr existieren.
    Ist nur Rom oder nur Han aktiv, erscheint nur dessen Seite bis zu den Vermittlern; sind beide aktiv, die durchgehende Verbindung.
  - Linien: durchgezogen = belegt, gestrichelt = vermittelt, gepunktet = umstritten. Landweg gelb/braun, Seeweg blau.
  - Klick (oder Tab + Enter) auf Route, Ort, Waren-Chips oder Gesandtschaft öffnet eine Infokarte mit Zeitraum, Waren (mit Richtung),
    Vermittlern, Sicherheitsstufe, Quelle und Hinweisen. Die Liste im Menü bietet denselben Zugang per Tastatur.
  - „Warenübersicht“: Tabelle Ost→West / West→Ost, Anmerkung zum Handelsdefizit (Plinius) und umstrittene Thesen.

## Daten ändern
- `data/reiche.json` (Provinzen/Regionen, Ereignisse, Schlachten, Orte, Nachbarreiche): erzeugt mit `build_reiche.py` (Python, shapely).
- `data/handel.json` (von Hand gepflegt):
  - `verbindungen`: id, name, art (`land`|`see`), pfad (`[lng,lat]` von West nach Ost), von/bis, reiche, vermittler,
    richtung_waren (`{name, von_nach: "west->ost"|"ost->west"}`), belegt (`belegt`|`vermittelt`|`umstritten`), quelle, hinweis.
    Optional `seiten` (Teilung in römische Seite bis `bis_punkt`, Mittelstück, chinesische Seite ab `ab_punkt`, je mit eigenem `von`)
    und `rand` (Text des Randpfeils auf der Rom- bzw. Han-Karte).
  - `orte` (Vermittler-/Handelsorte, `an`: Liste `[route, teil]`), `kontakte` (Gesandtschaften), `waren`, `defizit`, `umstritten`.
  - Grundsatz: Nur Belegtes als „belegt“; alles Weitere nur mit Quelle und als „umstritten“.
- `build_data.py` nur noch für `land*.json` (der Teil für reiche.json ist veraltet).

## Wichtig
Reichsgrenzen und Handelsrouten sind schematische Handzeichnungen. Zwischen Rom und Han gab es keinen belegten direkten Handel,
sondern Zwischenhandel über Parther, Kuschana, Nabatäer, Palmyra und Indien. Vor Einsatz im Unterricht mit Atlas und Fachliteratur
abgleichen; die Seite weist selbst darauf hin.
