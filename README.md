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
  Die Zeitleiste hat Epochen-Abschnitte („Europäische Antike“ −300 bis 480, „Europäisches Spätmittelalter“ 1400 bis 1440),
  getrennt durch einen schraffierten Zeitsprung (≈). Play, ±10 und Pfeiltasten springen über die Lücke; Klick auf ein
  Epochenfeld springt in den Abschnitt. Die Abschnitte haben verschiedene Maßstäbe; Reichsflächen gibt es nur in der Antike.
  Die Spuren der Nachbarreiche lassen sich über „Nachbarreiche (n)“ einklappen.
- **Schriftrolle:** Klick (oder Tipp) auf ein eingeblendetes Reich auf dem Globus, oder „Schriftrolle öffnen“ im Infoband, öffnet die Rolle dieses Reichs. Esc schließt sie.
  - Das geht bei Rom, Han und allen Nachbarreichen.
  - Reiter **Vignetten**: kindgerechte Inhaltspunkte. Beim Römischen Reich heißt der Reiter **Wiederholung** und enthält Aufgaben mit Rückmeldung.
  - Reiter **Karte**: die Reichskarte. Bei Nachbarreichen wird der Ausschnitt aus deren Gebieten berechnet.
  - Inhalte stehen in `data/vignetten.json`. Bisher sind es nur leere Platzhalter. Format: `docs/VIGNETTEN.md`. Vorschau aller Bausteine: `index.html?vignetten=demo`.
- Standardmäßig markiert ein Pin Jena. „Mein Standort“ (Menü → Globus) ersetzt ihn nach Freigabe im Browser durch den eigenen Standort (nur lokal, keine Übertragung; benötigt HTTPS oder localhost).
- **Handel & Austausch** (Menü, Standard aus): Land- und Seewege, Waren, Gesandtschaften.
  - Gezeigt werden Verbindungen aller Reiche, die eingeblendet sind **und** im gewählten Jahr existieren.
    Ist nur Rom oder nur Han aktiv, erscheint nur dessen Seite bis zu den Vermittlern; sind beide aktiv, die durchgehende Verbindung.
  - Linien: durchgezogen = belegt, gestrichelt = vermittelt, gepunktet = umstritten. Landweg gelb/braun, Seeweg blau.
  - Klick (oder Tab + Enter) auf Route, Ort, Waren-Chips oder Gesandtschaft öffnet eine Infokarte mit Zeitraum, Waren (mit Richtung),
    Vermittlern, Sicherheitsstufe, Quelle und Hinweisen. Die Liste im Menü bietet denselben Zugang per Tastatur.
  - „Warenübersicht“: Tabelle Ost→West / West→Ost, Anmerkung zum Handelsdefizit (Plinius) und umstrittene Thesen.
  - **Karawanenhandel** (Schalter im Handelsmenü): Kamel-Symbole ziehen auf kurzen Etappen zwischen Nachbarorten hin und her,
    keine Karawane läuft durch. Bis 220 n. Chr. auf den Etappen der Mittelroute, danach regional verteilt (alle 12 Jahre neu);
    die durchgehende Mittelroute wird ab 220 blass und gestrichelt. Pause: langsames Ziehen, Play: schneller, ±10/Schieber: Sprung.
  - **Entdeckungsfahrten des Zheng He** (im Handelsmenü, Schalter für alle und jede einzelne Fahrt; Waren über den
    gemeinsamen Schalter „Waren anzeigen“):
  - Sieben Flottenfahrten (1405–1433) in Grüntönen, zu sehen im Zeitleisten-Abschnitt „Europäisches Spätmittelalter“.
  - Eine Fahrt zeichnet sich ein, sobald ihr Startjahr erreicht ist; laufende Fahrt hell mit wanderndem Strich, frühere blass.
    Teilflotten dünn, Unsicheres gepunktet („umstritten“).
  - Häfen mit Infokarte (wann angelaufen, Funktion, Quelle), Waren-Labels mit Richtungspfeil, Ereignisse auf der Zeitleiste,
    Hintergrundtext und Warenübersicht.

- **Schülertexte:** Ein Klick auf eine Route (oder in der Routenliste) öffnet einen Text in den Niveaus A/B/C.
  - Mittelroute bis 220: „Die Seidenstraße als Landweg“, ab 220: „Nach der Han-Zeit“, Seeweg: „Der Seeweg nach Indien“,
    Fahrten: „Die Reisen des Zheng He“.
  - Jeder Text hat Glossar, Kartenskizze, Quellenauszug, „Woher wissen wir das?“, zwei Arbeitsaufträge und Anmerkungen.
  - „Daten zur Route“ führt zur bisherigen Infokarte. Alle Texte gesammelt: `lehrkraft.html` (Lehrkraft-Ansicht).
- **Römische Straßen** (Schalter im Handelsmenü): Hauptstraßen aus dem Datensatz Itiner-e (CC BY 4.0), auf dem Globus
  und auf der Rom-Karte; sichtbar, wenn das Römische Reich eingeblendet ist.

## Daten ändern
- `data/reiche.json` (Provinzen/Regionen, Ereignisse, Schlachten, Orte, Nachbarreiche): erzeugt mit `build_reiche.py` (Python, shapely).
- `data/handel.json` (von Hand gepflegt):
  - `verbindungen`: id, name, art (`land`|`see`), pfad (`[lng,lat]` von West nach Ost), von/bis, reiche, vermittler,
    richtung_waren (`{name, von_nach: "west->ost"|"ost->west"}`), belegt (`belegt`|`vermittelt`|`umstritten`), quelle, hinweis.
    Optional `seiten` (Teilung in römische Seite bis `bis_punkt`, Mittelstück, chinesische Seite ab `ab_punkt`, je mit eigenem `von`)
    und `rand` (Text des Randpfeils auf der Rom- bzw. Han-Karte).
  - `orte` (Vermittler-/Handelsorte, `an`: Liste `[route, teil]`), `kontakte` (Gesandtschaften), `waren`, `defizit`, `umstritten`.
  - `karawanen`: Wendepunkt `ab` (Standard 220, frei änderbar), `knoten` (Orte mit von/bis), `etappen` (`von`, `nach`, `pfad`,
    `haupt` = liegt auf der Mittelroute, optional `ab_jahr`), Höchstzahl `max_vorher`/`max_nachher`, Legenden- und Hinweistext.
  - Grundsatz: Nur Belegtes als „belegt“; alles Weitere nur mit Quelle und als „umstritten“.
- `data/zhenghe.json` (Ming-Zeit): erzeugt mit `build_zhenghe.py` (reines Python). Gleiches Format wie `handel.json`
  (`verbindungen` mit zusätzlich `nr`, `stationen`, `abzweige`; `orte` mit `funktion`), dazu `ereignisse` und `info`.
  Seewege werden aus Teilstrecken zusammengesetzt; die Amerika-These (Menzies, „1421“) ist widerlegt und wird nicht dargestellt.
- `data/vignetten.json` (von Hand gepflegt): Vignetten je Reich mit den Bausteinen Text, Merke, Erzählung, Quelle, Bild, Audio und Video. Dazu kommen die Quizarten einfach, mehrfach, wahrfalsch, luecke, zuordnen, reihenfolge und zahl, jeweils mit Rückmeldung. Siehe `docs/VIGNETTEN.md`.
- `data/texte.json` (Schülertexte) und `data/literatur.json` (Literatur, Lizenz, Ablage): Regeln in `docs/GRUNDREGELN.md`.
  Prüfen mit `python tools/check_zitate.py`. Es vergleicht jede Belegstelle mit den Seitentexten in `quellen/oeffentlich/`
  (gemeinfrei, im Repo) und `quellen/lokal/` (geschützt, nur lokal, per `.gitignore` ausgeschlossen).
- `data/roemerstrassen.json`: erzeugt mit `build_roemerstrassen.py` aus `itinere_roads.geojson` (Zenodo, CC BY 4.0).
- `build_data.py` nur noch für `land*.json` (der Teil für reiche.json ist veraltet).

## Wichtig
Reichsgrenzen und Handelsrouten sind schematische Handzeichnungen. Zwischen Rom und Han gab es keinen belegten direkten Handel,
sondern Zwischenhandel über Parther, Kuschana, Nabatäer, Palmyra und Indien. Vor Einsatz im Unterricht mit Atlas und Fachliteratur
abgleichen; die Seite weist selbst darauf hin.
