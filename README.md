# Digitales Tafelbild: Rom und China

<img width="946" height="631" alt="image" src="https://github.com/user-attachments/assets/62332721-ca48-4a0d-b88d-0c5059ea40fb" />


## Einbinden
1. Ordner `tafelbild/` in dein Repo `datenflix007.github.io` legen und pushen.
2. Erreichbar unter `https://datenflix007.github.io/tafelbild/`.
3. Verlinken: `<a href="tafelbild/">Digitales Tafelbild</a>`.
Lokal testen: `python3 -m http.server` im Ordner, dann http://localhost:8000 (nicht per Doppelklick öffnen).

## Bedienung
- Oben rechts: **Erste Schritte** (Kurzanleitung, Hinweise zu Daten und Darstellung, Lizenzen) und **Lehrerhinweise** (Entwurf mit Reitern: Unterrichtsreihe, Kompetenzziele, Handlungsziele, Sachanalyse, Methodisch-didaktische Analyse, Verlaufsplan). „Erste Schritte“ steht in `index.html` (`#modal`). Die Lehrerhinweise werden aus `lehrerhinweise/*.md` geladen (je Datei ein Reiter, derzeit Platzhalter; siehe `lehrerhinweise/README.md`).
- Ansicht Satellit/Schematisch, Rom, Han, 11 Nachbarreiche und 9 europäische Nachfolgestaaten (Gruppe „Europa (Kontext)“, ausgegraut, ohne Schriftrolle) ein-/ausblenden („Alle einblenden/ausblenden“), Menü einklappbar.
  - Bei vielen eingeblendeten Reichen werden die Spuren der Zeitleiste enger. Im Spätmittelalter sind die antiken Nachbarspuren ausgeblendet.
- Provinzen: Die römischen Flächen folgen den Provinzen um 117 n. Chr. Namen, Einrichtungsjahre und Hauptstädte stammen aus der Liste der Provinzen des Römischen Reichs (de.wikipedia).
  - Ab 395 ist das Reich in West- und Ostrom geteilt. Westrom verliert seine Gebiete an die Nachfolgestaaten: Britannien 410, Africa 429/439, Tripolitanien 455, Italien 476, Dalmatien 480/81.
  - Ostrom reicht als Byzantinisches Reich in den Abschnitt Spätmittelalter. Dieser endet jetzt 1453 (Fall Konstantinopels); dazu kommt das Osmanische Reich als Kontext.
- Völkerwanderung (Menü → Globus): Die Züge von Hunnen, Goten, Vandalen, Sueben, Burgundern, Alamannen, Angeln und Sachsen wachsen mit der Zeitleiste (255–456, schematisch). Daten: `wanderungen` in `data/reiche.json` (build_reiche.py).
- Orte („Orte anzeigen“): Die Namen sind HTML-Beschriftungen mit dunklem Rand, damit sie auch über den Straßen lesbar bleiben.
- Orte („Orte anzeigen“): Je näher man heranzoomt, desto mehr Orte erscheinen (ganz weit weg keine → Weltstädte → große Provinzzentren → weitere Hauptstädte und Wirtschaftszentren → erst ganz nah alle Orte). Die Schrift bleibt auf dem Bildschirm etwa gleich groß.
- Zeitstrahl ziehen (Punkte = Ereignisse, Schwerter = Schlachten), ←/→ Jahr, Shift = 10 Jahre, Leertaste = Abspielen.
  Die Zeitleiste hat Epochen-Abschnitte („Europäische Antike“ −300 bis 480, „Europäisches Spätmittelalter“ 1400 bis 1440),
  getrennt durch einen schraffierten Zeitsprung (≈). Play, ±10 und Pfeiltasten springen über die Lücke; Klick auf ein
  Epochenfeld springt in den Abschnitt. Die Abschnitte haben verschiedene Maßstäbe; Reichsflächen gibt es nur in der Antike.
  Die Spuren der Nachbarreiche lassen sich über „Nachbarreiche (n)“ einklappen.
  Der Pfeil rechts oben in der Zeitleiste verkleinert sie: Dann bleiben nur noch Jahr, Abspielen und Schieber. Der Globus nutzt den frei werdenden Platz und steht immer mittig im Bereich über der Zeitleiste.
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
  - **Karawanenhandel** (Schalter im Handelsmenü, standardmäßig aus): Kamel-Symbole ziehen auf kurzen Etappen zwischen Nachbarorten hin und her,
    keine Karawane läuft durch. Bis 220 n. Chr. auf den Etappen der Mittelroute, danach regional verteilt (alle 12 Jahre neu);
    die durchgehende Mittelroute wird ab 220 blass und gestrichelt. Pause: langsames Ziehen, Play: schneller, ±10/Schieber: Sprung.
  - **Entdeckungsfahrten des Zheng He** (im Handelsmenü, Schalter für alle und jede einzelne Fahrt; Waren über den
    gemeinsamen Schalter „Waren anzeigen“):
  - Sieben Flottenfahrten (1405–1433) in Grüntönen, zu sehen im Zeitleisten-Abschnitt „Europäisches Spätmittelalter“.
  - Eine Fahrt zeichnet sich ein, sobald ihr Startjahr erreicht ist (ca. 7 s). Das Schiff zeichnet die Linie wie eine Feder, Häfen erscheinen beim Erreichen. Die wandernden Striche anderer Linien laufen dabei weiter, denn nur die Strichlänge im Material wächst. Ebenso zeichnen portugiesische Karavellen ihre Fahrten nach Ceuta, Madeira, zu den Azoren und nach Kap Bojador. Beim Abspielen wartet die Zeitleiste, bis die Fahrt gezeichnet ist.
  - **Abbildungen statt Symbole** (Schalter bei Zheng He): Wo eine Abbildung vorliegt (bisher Zheng Hes Schatzschiff, `img/icons/zhenghe_schiff_*.png`, je eine Fassung für Satellit und Schematisch), ersetzt sie das Symbol; das Schiff zeigt mit dem Bug in Fahrtrichtung. Symbol bzw. Abbildung stehen mit dem Kiel genau auf der Spitze der gezeichneten Linie.
  - Danach ist die laufende Fahrt hell mit wanderndem Strich, frühere sind blass.
  - Infoband: erzählende Karte zur laufenden Fahrt (Häfen in Reihenfolge, erreichte abgehakt), Karte „China · Ming-Dynastie“ (Hauptstadt Nanjing, ab 1421 Peking; Jiaozhi 1407–1427) und „Zur gleichen Zeit in Europa“ (Ceuta 1415, Madeira 1419, Azoren 1427, Kap Bojador 1434; auch als Marker auf Globus und Zeitleiste).
  - Das Ming-Reich (vereinfacht) erscheint, wenn das Han-Reich (China) eingeblendet ist.
    Teilflotten dünn, Unsicheres gepunktet („umstritten“).
  - Häfen mit Infokarte (wann angelaufen, Funktion, Quelle), Waren-Labels mit Richtungspfeil, Ereignisse auf der Zeitleiste,
    Hintergrundtext und Warenübersicht.

- **Schülertexte:** Ein Klick auf eine Route (oder in der Routenliste) öffnet einen Text in den Niveaus A/B/C.
  - Mittelroute bis 220: „Die Seidenstraße als Landweg“, ab 220: „Nach der Han-Zeit“, Seeweg: „Der Seeweg nach Indien“,
    Fahrten: „Die Reisen des Zheng He“.
  - Jeder Text hat Glossar, Kartenskizze, Quellenauszug, „Woher wissen wir das?“, zwei Arbeitsaufträge und Anmerkungen.
  - „Daten zur Route“ führt zur bisherigen Infokarte. Alle Texte gesammelt: `lehrkraft.html` (Lehrkraft-Ansicht).
- **Römerstraßen** (Schalter im Handelsmenü): 819 Hauptstraßen aus Itiner-e (CC BY 4.0) auf dem Globus und auf der Rom-Karte, sichtbar, wenn das Römische Reich eingeblendet ist. Das Netz verändert sich mit der Zeitleiste:
  - Straßen erscheinen in ihrer modellierten Ausbauphase (gezeichnet wie die Schiffsrouten; jede Straße setzt am schon gezeichneten Netz an und wächst von dort weiter, ausgehend von Rom; didaktische Animation) und sind in der römischen Nutzungsphase voll sichtbar.
  - Danach sind sie im Hauptmodus ausgeblendet. Ab 1400 ist keine Straße aktiv.
  - Optionen: „Ehemalige Trassen“ (blass gestrichelt, mittelalterliche Nutzung nicht allgemein belegt), „Ausbau animieren“ und „Datierung zeigen“ (grün belegt, gelb teilweise, sonst Regionalmodell).
  - Ein Klick auf eine Straße zeigt räumliche Sicherheit, Modellzeiten und Itiner-e-Belege.

## Daten ändern
- `data/reiche.json` (Provinzen/Regionen, Ereignisse, Schlachten, Orte, Nachbarreiche): erzeugt mit `build_reiche.py` (Python, shapely).
  - Orte haben eine `stufe` (1 Weltstadt, 2 großes Provinzzentrum, 3 weitere Hauptstadt/Wirtschaftszentrum, 4 kleinerer Ort; Zuordnung in `STUFE_ROM_HAN`) und `zeiten`. Die Zeiten berechnet das Skript: In diesen Jahren gehört das Gebiet des Ortes zum Reich.
  - Europa (Kontext): Franken, Alamannen, West- und Ostgoten, Sueben, Vandalen, Burgunder, das Reich Odoakers und die Angelsachsen (`kontext: true`). Sie stehen in einer eigenen Menügruppe, sind ausgegraut und haben keine Schriftrolle.
  - Bei Überlappung gewinnen die Kontext-Reiche gegen Westrom (Reihenfolge `PRIO`).
  - `luecken`-Prüfung: Innerhalb des Reichsgebiets sollten keine Flächen frei bleiben. Ausgenommen sind historisch freie Gebiete wie die Westalpen vor 15 v. Chr.
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
- `data/roemerstrassen.json`: Geometrie aus `build_roemerstrassen.py` (Itiner-e, Zenodo, CC BY 4.0). Dazu kommt ein Zeitmodell je Linie (`zeit`), angereichert mit `build_strassen_zeit.py` (Itiner-e-Belege, Regionskorrektur).
  - Anzeige je Jahr: Ausbau, römische Nutzung, danach optional „ehemalige Trassen“.
  - Einzelheiten und was belegt bzw. modelliert ist: `docs/STRASSEN_ZEITMODELL.md`.
  - Tests: `node tests/strassenzeit.test.js`, `python tests/test_strassen_browser.py`.
- Schematische Ansicht: `img/earth-schematic-8k.png` und Kacheln `img/tiles_schem/` aus Natural Earth 1:10 Mio. Die Abdeckung ist dieselbe wie bei den Satelliten-Kacheln. Neu erzeugen mit `python build_schema_kacheln.py <land-10m.json>` (world-atlas 2.0.2).
- Satellitenbild:
  - `img/earth-blue-marble-8k.jpg` (8192×4096) ist die Grundkugel.
  - Beim Hineinzoomen legen sich Kacheln aus `img/tiles/` darüber (NASA Blue Marble Next Generation, Juli 2004, gemeinfrei).
  - Stufe 6 gilt weltweit (ca. 2 km/Pixel). Die Stufen 7–8 (bis 500 m/Pixel) gibt es nur für Europa bis China, Nordafrika und den Indischen Ozean (20° W–150° O, 15° S–62° N). Außerhalb davon bleibt das 8k-Bild sichtbar.
  - Neu erzeugen mit `python build_kacheln.py <ordner mit NASA-Bildern>`. Die Region steht im Skript und in `KACHELN` in `js/app.js`; beide müssen übereinstimmen.
- `build_data.py` nur noch für `land*.json` (der Teil für reiche.json ist veraltet).

## Wichtig
Reichsgrenzen und Handelsrouten sind schematische Handzeichnungen. Zwischen Rom und Han gab es keinen belegten direkten Handel,
sondern Zwischenhandel über Parther, Kuschana, Nabatäer, Palmyra und Indien. Vor Einsatz im Unterricht mit Atlas und Fachliteratur
abgleichen; die Seite weist selbst darauf hin.
