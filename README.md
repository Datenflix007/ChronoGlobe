# ChronoGlobe

Interaktiver Globus mit Zeitleiste für den Geschichtsunterricht (früher „Digitales Tafelbild: Rom und China“).
Veröffentlicht unter **https://datenflix007.github.io/ChronoGlobe/**.

<img width="946" height="631" alt="image" src="https://github.com/user-attachments/assets/62332721-ca48-4a0d-b88d-0c5059ea40fb" />

## Modi

Die Startseite (`index.html`) bietet vier Wege:

- **Freies Nutzen – Menschheitsgeschichte** (`app.html?modus=frei`): der ganze Globus mit allen Daten und vollem Menü, dazu links auf der Zeitleiste der Abschnitt **Frühe Hochkulturen** (3500–300 v. Chr.: Mesopotamien, Ägypten, Indus-Kultur, Hethiter, Shang/Zhou, Perserreich; nur angedeutet, `data/fruehe_reiche.json` aus `build_fruehe_kulturen.py`).
- **Session erstellen** (Lehrkraft): Tafelbild wählen und starten. Es erscheinen Code, Link, QR-Code und Lehrer-Schlüssel; „Session fortsetzen“ listet frühere Sessions dieses Browsers.
- **Session beitreten** (Schüler:innen): Code eingeben oder QR-Code scannen (`index.html?code=XXXXXX`). Ohne Menü; man folgt der Lehrkraft je nach Freigabe.
  - Auf Handy und Tablet ist die Schüleransicht reduziert:
    - keine Ereignisspuren in der Zeitleiste, Statusanzeige über der Zeitleiste;
    - im Querformat nur Jahr und Schieber;
    - bei gesperrtem Zeitriegel ohne Abspiel- und ±10-Knöpfe.
- **Tafelbilder ansehen**: Galerie aus `tafelbilder/index.json`, jedes Tafelbild einzeln (`app.html?tafelbild=<id>`).

Live-Sessions brauchen ein eigenes Supabase-Projekt (`docs/SETUP.md`). Ohne Einrichtung funktionieren freier Modus und Tafelbilder weiter; die Session-Kacheln zeigen dann „Supabase nicht eingerichtet“.

Aufbau, Zustand, Synchronisierung und Rechte: `docs/ARCHITEKTUR.md`. Neues Tafelbild: `docs/TAFELBILD_ERSTELLEN.md`. Regeln für Änderungen (Kern oder einzelnes Tafelbild): `CLAUDE.md`.

## Einbinden

- Das Repository über GitHub Pages veröffentlichen. Alle Pfade sind relativ; der Repo-Name spielt keine Rolle.
- Lokal testen: `python -m http.server` im Ordner, dann http://localhost:8000 öffnen (nicht per Doppelklick).

## Tests

- `python tests/test_regression.py "app.html?tafelbild=rom-zentrum-der-welt"`: Klickfolge gegen den gespeicherten Ausgangszustand. Ebenso `app.html?modus=frei`, dort ohne Lehrerhinweise.
- `python tests/test_session.py`: Live-Session mit zwei bzw. drei Fenstern über `?sync=lokal`, ohne Supabase.
- `node tests/synctakt.test.js`: Sendetakt der Live-Session (Geräteanzahl, Realtime-Grenze).
- `python tools/check_tafelbilder.py`: alle Tafelbilder (Schema, IDs, Dateien).
- `node tests/strassenzeit.test.js`, `python tests/test_strassen_browser.py`: Römerstraßen.
- `node tests/netze.test.js`, `python tests/test_netze_browser.py`: Handels- und Verkehrsnetze.
- `python tools/check_sources.py`: Quellenregister, lokale Dateiverweise, Literatur- und Fußnoten-IDs sowie Vollständigkeit (jede Datei unter `data/` und `img/` im Register).

## Wissenschaftliche Datengrundlage

Die Seite [Datensätze, Literatur und Quellen](quellen.html) dokumentiert die nachweislich eingebundenen Datensätze, eigene didaktische Rekonstruktionen, Literatur und nur recherchierte Projekte getrennt voneinander. Das zentrale Register liegt in `data/sources.json`.

- Einen neuen Registereintrag nur mit dem Status versehen, den die lokalen Import- oder Nutzungsdateien belegen (Verwendet, Teilweise verwendet, Wissenschaftliche Grundlage, Recherchiert). Daten oder Bilder ohne belegbare Herkunft werden nicht eingebunden; die Herkunft vorher klären.
- Nach jeder Änderung an Daten, Bildern oder Literatur das Register ergänzen und das Feld `stand` (JJJJ-MM-TT) in `data/sources.json` aktualisieren. Es erscheint oben auf der Quellenseite.
- Bei einer neuen Datenebene die tatsächlichen lokalen Dateien unter `local_files` und die sichtbare Ebene unter `used_by_layers` hinterlegen.
- `source_id` oder `source_ids` in Datenobjekten müssen auf eine ID im Register zeigen. Literatur-IDs aus `data/literatur.json` und Fußnoten-IDs aus `data/texte.json` werden ebenfalls geprüft.
- Nach Änderungen `python tools/check_sources.py` ausführen. Die Prüfung validiert Verweise und Dateien, nicht die historische Aussage selbst.

## Bedienung

- Oben rechts:

  - **Erste Schritte**: Kurzanleitung, Hinweise zu Daten und Darstellung, Lizenzen.
  - **Lehrerhinweise**: Reiter aus `tafelbild.json` → `lehrerhinweise`. Die Markdown-Dateien liegen im Tafelbild, z. B. `tafelbilder/rom-zentrum-der-welt/lehrerhinweise/` (derzeit Platzhalter). Im freien Modus gibt es keine Lehrerhinweise.
- Der Titel oben links führt zurück zur Startseite.
- Die Knöpfe „→ Rom“, „→ China“, „Eurasien“ kommen aus den Fokuspunkten des Tafelbilds.
- Ansicht Satellit/Schematisch, Rom, Han, 11 Nachbarreiche und 9 europäische Nachfolgestaaten (Gruppe „Europa (Kontext)“, ausgegraut, ohne Schriftrolle) ein-/ausblenden („Alle einblenden/ausblenden“), Menü einklappbar.

  - Bei vielen eingeblendeten Reichen werden die Spuren der Zeitleiste enger. Im Spätmittelalter sind die antiken Nachbarspuren ausgeblendet.
- Provinzen: Die römischen Flächen folgen den Provinzen um 117 n. Chr. Namen, Einrichtungsjahre und Hauptstädte stammen aus der Liste der Provinzen des Römischen Reichs (de.wikipedia).

  - Ab 395 ist das Reich in West- und Ostrom geteilt. Westrom verliert seine Gebiete an die Nachfolgestaaten: Britannien 410, Africa 429/439, Tripolitanien 455, Italien 476, Dalmatien 480/81.
  - Ostrom reicht als Byzantinisches Reich in den Abschnitt Spätmittelalter. Dieser endet jetzt 1453 (Fall Konstantinopels); dazu kommt das Osmanische Reich als Kontext.
- Völkerwanderung (Menü → Globus): Die Züge von Hunnen, Goten, Vandalen, Sueben, Burgundern, Alamannen, Angeln und Sachsen wachsen mit der Zeitleiste (255–456, schematisch). Daten: `wanderungen` in `data/reiche.json` (build_reiche.py).
- Weltbilder (Menü → Globus): „Die Welt nach Plinius“ (rund 160 Orte, Völker und Fabelwesen aus der Naturgeschichte mit Stelle und Wortlaut, Seeweg nach Indien, Unbekanntes abgedunkelt) und die Ebstorfer Weltkarte (hochaufgelöst als Schriftrolle mit rund 160 Datenpunkten, auch neben dem Globus; optional verzerrt auf den Globus gelegt). Eigene Tafelbilder: `welt-nach-plinius`, `ebstorfer-weltkarte`. Daten: `build_weltbilder.py`.
- Historische Geographie (Menü → Globus): Flüsse, Gebirgskämme, Gipfel, Meere und Landschaften mit antiken Namen nach dem Grundkurs-Skript (Kap. 8). Je näher man heranzoomt, desto mehr Namen erscheinen; ein Klick zeigt heutigen Namen und Beleg. Daten: `data/geographie.json` (build_geographie.py, Verläufe aus Natural Earth).
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
  - Inhalte stehen in `data/vignetten.json` (Kern) bzw. `tafelbilder/<id>/vignetten.json` (Tafelbild). Bisher sind es nur leere Platzhalter. Format: `docs/VIGNETTEN.md`. Vorschau aller Bausteine: `app.html?modus=frei&vignetten=demo` (alte Adresse `index.html?vignetten=demo` leitet weiter).
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
- **Seidenstraße der Han (Stationen)** (Schalter im Handelsmenü, standardmäßig aus):

  - 14 rekonstruierte Hauptlinien und 269 Verkehrspunkte der Han-Zeit (Poststationen, Pässe, Kommandanturen, Kreissitze …).
  - Quelle: Forschungsdaten von Hu, Yan und Zhang (2018, Science Data Bank, CC BY 4.0).
  - Sichtbar mit dem Han-Reich, 202 v. bis 220 n. Chr.; Klick auf eine Station zeigt ihre Rolle für Handel und Verkehr.
  - Daten: `data/han_seidenstrasse.json` aus `build_han_seidenstrasse.py`. Siehe `docs/DATENQUELLEN.md`.
- **Handels- und Verkehrsnetze** (Menü, aufklappbar; Gruppen Landwege, Wasserwege, Reiseberichte):

  - Fünf Netze aus offenen Forschungsdaten (CC BY 4.0):
    - Weihrauchstraße Petra – Gaza
    - Seidenstraße der Tang
    - Straßen der Levante (VIA-TARIQ, 650–1517)
    - Wegenetz der islamischen Welt (al-Ṯurayyā, 9./10. Jh.)
    - Reisende der Mongolenzeit
  - Jedes Netz ist nur in seinem Zeitraum sichtbar. Postwege, Pilgerwege und Reiseberichte sind als solche gekennzeichnet.
  - Klick auf eine Linie oder einen Ort öffnet eine Infokarte mit Datierung und Quelle; „Quellenübersicht“ listet alle Netze, auch die geprüften, aber nicht übernommenen.
  - Im freien Erkunden hat die Zeitleiste dafür einen Teil **Mittelalter** (480–1400); Tafelbilder bleiben unverändert.
  - Daten: `data/netze/`, erzeugt mit `build_netze.py`. Siehe `docs/HANDELSNETZE.md`.
- **Grenzanlagen (Limes)** (Menü → Globus, standardmäßig aus):

  - Hadrianswall, Antoninuswall, Obergermanisch-Raetischer Limes, Rhein- und Donaugrenze, Limes Arabicus, Fossatum Africae.
  - Je Bauart eine eigene Signatur über dunkler Kontur (Steinmauer, Rasenwall, Palisade, Flussgrenze, Grenzstraße, Graben), dazu Kastelle als Turm-Symbole mit Infokarte.
  - Sichtbar mit dem Römischen Reich, solange der Abschnitt in Gebrauch war.
  - Daten von Hand in `data/limes.json`; Verläufe schematisch über bekannte Kastellorte.
- **Völkerwanderung** (Menü → Globus): Jeder Zug ist ein leuchtender Strom mit Pfeilspitze und Namensschild. Am Ziel pulsiert einige Jahre ein Ankunftsring; abgeschlossene Züge bleiben 40 Jahre als blasse Spur.
- **Schiffsverkehr (ORBIS)** (Schalter im Handelsmenü, standardmäßig aus): 505 Küsten-, Hochsee-, Fähr- und Flussstrecken im Römischen Reich bis Britannien nach dem Verkehrsmodell ORBIS (Stanford, um 200 n. Chr.; Daten `emeeks/orbis_v2`, MIT), auf dem Globus und auf der Rom-Karte. ORBIS hat keine Jahreszahlen: Eine Strecke erscheint, solange beide Endhäfen römisch sind (z. B. Britannien 43–410). Einfarbig hellblau, Flüsse blasser; Klick öffnet eine Infokarte. Daten: `data/orbis_schiff.json`, erzeugt mit `python build_orbis.py <ordner mit den ORBIS-Dateien>`. Siehe `docs/DATENQUELLEN.md`.
- **Römerstraßen** (Schalter im Handelsmenü): 819 Hauptstraßen aus Itiner-e (CC BY 4.0) auf dem Globus und auf der Rom-Karte, sichtbar, wenn das Römische Reich eingeblendet ist. Das Netz verändert sich mit der Zeitleiste:

  - Straßen erscheinen in ihrer modellierten Ausbauphase (gezeichnet wie die Schiffsrouten; jede Straße setzt am schon gezeichneten Netz an und wächst von dort weiter, ausgehend von Rom; didaktische Animation) und sind in der römischen Nutzungsphase voll sichtbar.
  - Danach sind sie im Hauptmodus ausgeblendet. Ab 1400 ist keine Straße aktiv.
  - Optionen: „Ehemalige Trassen“ (blass gestrichelt, mittelalterliche Nutzung nicht allgemein belegt) und „Ausbau animieren“. Alle Straßen haben eine Farbe (kräftig = gesichert, blass = vermutet); die Datierungsqualität steht in der Infokarte jeder Straße.
  - Ein Klick auf eine Straße zeigt räumliche Sicherheit, Modellzeiten und Itiner-e-Belege.

## Daten ändern

- Reichsflächen immer in dieser Reihenfolge erzeugen: `build_reiche.py`, `build_fruehe_kulturen.py`, `build_mittelalter.py`, `build_geographie.py`, zuletzt `build_grenzen.py`. Unabhängig davon: `build_weltbilder.py`. Dieses gleicht die drei Reichsdateien aneinander an (keine Überlappungen gleichzeitiger Reiche, schmale Lücken geschlossen, Grenzen an Flüsse und Gebirgskämme gelegt). Prüfen: `python build_grenzen.py --pruefen`. Einzelheiten: `docs/DATENQUELLEN.md`.
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
  - Geprüfte weitere Quellen (ORBIS, Project MERCURY, Hanson-Städte, Pleiades) und Empfehlung: `docs/DATENQUELLEN.md`.
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
