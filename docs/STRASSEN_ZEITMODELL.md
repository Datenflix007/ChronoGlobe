# Römerstraßen im Zeitverlauf

Der Layer „Römerstraßen anzeigen“ (Menü → Handel & Austausch) zeigt die 819 vereinfachten Hauptstraßen aus `data/roemerstrassen.json`. Was zu sehen ist, hängt vom Jahr auf der Zeitleiste ab.

- Rechenlogik: `js/strassenzeit.js` (ohne Globus, testbar)
- Darstellung: `js/app.js`, Abschnitt „Layer Römische Straßen“
- Anreicherung der Daten: `build_strassen_zeit.py`

## Was belegt ist und was modelliert

| Angabe | Herkunft | Status |
|---|---|---|
| Verlauf (`p`), räumliche Sicherheit (`s`: S = gesichert/erschlossen, H = vermutet) | Itiner-e, vereinfacht und verkettet | **belegt** (Rekonstruktion des Datensatzes) |
| `beginn_min`, `beginn_max`, `beginn_modell`, `roemische_nutzung_bis_modell` | regionales Szenariomodell (`regionen_modell`) | **modelliert**, keine Bau- oder Aufgabejahre |
| `zeit.itinere.belege` (Lower_Date, Upper_Date, Bauphase `Cons_per_e`) | Itiner-e-Originalsegmente, räumlich zugeordnet | **belegt** für die zugeordneten Segmente |
| Wachstum des Netzes (`zeit.netz`: Anschluss, Zeichenfenster) | berechnet aus Lage und Modellzeiten (`build_strassen_zeit.py --netz`) | **didaktische Animation**, keine Baudaten |
| `historischer_fortbestand` | — | für alle Linien „unbekannt“ |

## Phasen (Funktion `StrassenZeit.zustand`)

| Phase | Bedingung (Jahr j) | Hauptmodus | Referenzmodus „Ehemalige Trassen“ |
|---|---|---|---|
| A vor | j < `beginn_min` | unsichtbar | unsichtbar |
| B Ausbau | `beginn_min` ≤ j < `beginn_max` | wächst als Netz: ab `netz.von` vom Anschlusspunkt aus gezeichnet, bis `netz.bis` ganz; ohne „Ausbau animieren“ ganz ab `beginn_modell` | wie Hauptmodus |
| C römisch | `beginn_max` ≤ j ≤ `roemische_nutzung_bis_modell` | voll sichtbar | voll sichtbar |
| D nachrömisch | danach | **unsichtbar** | blass, gestrichelt: „ehemalige römische Trasse – mittelalterliche Nutzung nicht allgemein belegt“ |
| undatiert | Ausbauzeitraum fehlt oder ist ungültig | unsichtbar | unsichtbar (im Datensatz derzeit keine solche Linie) |

- Fehlt das Nutzungsende, gilt die Linie höchstens bis 476 als römisch (Ende Westroms). Danach wird sie wie Phase D behandelt.
- Nach 1400 ist im Hauptmodus keine Straße aktiv. Der Datensatz enthält keine Belege für eine mittelalterliche Nutzung. Eine Straße darf erst dann als mittelalterlich genutzt erscheinen, wenn eigene Quellen- und Zeitangaben vorliegen. Dafür gibt es noch kein Datenfeld.

**Jahreszählung:** Daten und App verwenden historische Jahre (−44 = 44 v. Chr.). Ein Jahr 0 gibt es nicht.
- Für Dauern, Interpolation und die Sprünge der Zeitleiste (±10, Pfeiltasten, Abspielen) rechnet die App in astronomischen Jahren.
- Beispiel: 1 v. Chr. + 10 Jahre = 10 n. Chr.
- Das Jahr 0 ist auf der Zeitleiste nicht wählbar.

**Darstellung:**
- Gesichert oder erschlossen: kräftig. Vermutet: blass.
- **Zeichenfeder:** Eine Straße wird wie die Schiffsrouten gezeichnet (ca. 1,6 s je Schritt), und zwar vom Anschlusspunkt an das schon gezeichnete Netz aus in beide Richtungen; im Ausbau nur bis zum Anteil des Jahres. Die Geometrie bleibt fest, es wächst nur der sichtbare Strich (Shader-Werte `dashSize`/`dashOffset`). Übergangsanimationen von globe.gl sind abgeschaltet, damit keine Linie aus ihrem ersten Punkt heraus „fliegt“. Beim Zurückspulen gilt der neue Zustand sofort; bei „Bewegung reduzieren“ entfällt die Feder.
- **Eine Farbe für alle Straßen (Entscheidung, 20.11.2026):** Eine Einfärbung nach Datierungsqualität (grün = Itiner-e-belegt, gelb = teilweise, sonst Regionalmodell) war als Option „Datierung zeigen“ vorhanden. Sie wurde entfernt, weil die Farben im Unterricht eher verwirrten: Sie lassen sich leicht als Straßentypen oder Epochen missverstehen. Unterschieden wird nur noch die Deckkraft (kräftig = gesichert oder erschlossen, blass = vermutet). Die Datierungsqualität jeder Straße steht in ihrer Infokarte; die Daten (`zeit.datierung`) bleiben unverändert.
- Ein Klick auf eine Straße öffnet eine Infokarte. Sie zeigt räumliche Sicherheit, Modellzeiten, Quellenlage, Itiner-e-Belege und Zuordnung.
- Auf der flachen Rom-Karte gelten dieselben Zustände.

## Anreicherung mit Itiner-e (`build_strassen_zeit.py`)

    python build_strassen_zeit.py <pfad/zu/itinere_roads.geojson>

Quelle der Rohdaten: Zenodo, DOI 10.5281/zenodo.17122148, Datei `itinere_roads.geojson` (78 MB, CC BY 4.0).

**Was die Rohdaten hergeben** (Stand der Prüfung, Hauptstraßen „Main Road“: 5698 Segmente):
- `Lower_Date`/`Upper_Date` (mit Fehler `Low_Date_E`/`Up_Date_E`; 9999 = unbekannt) gibt es nur bei 356 Segmenten. Das sind etwa 6 % der Länge.
- `Cons_per_e` (Bauphase, z. B. „Claudius (46 CE)“) ist häufiger. Die Angabe stammt oft von Meilensteinen und kann auch eine spätere Erneuerung bezeichnen.
- Einzelne Werte sind offenkundig fehlerhaft, z. B. „Marcus Aemilius Lepidus (189–187 CE)“ statt v. Chr.

**Zuordnung:**
- Die vereinfachten Linien sind verkettet. Eine Linie entspricht deshalb oft mehreren Originalsegmenten.
- Ein Segment zählt zur Linie, wenn ≥ 80 % seiner Länge im Abstand von 0,04° (≈ 4 km) liegen.
- Die Linie gilt als zugeordnet, wenn die Segmente ≥ 60 % ihrer Länge abdecken.

**Übernahme (keine erfundenen Jahre):**
- `Lower_Date` + Fehler und das Ende einer Bauphase sind **Obergrenzen**: Die Straße bestand spätestens dann. Sie senken höchstens `beginn_max`.
- `beginn_min` wird nie früher gelegt als im Regionalmodell, denn der Layer zeigt das römische Netz. Fehlerhaft späte Angaben bleiben so ohne Wirkung.
- Eine verkettete Linie ist erst vollständig, wenn alle Teile bestehen: Es gilt das Maximum der Teilwerte; undatierte Teile behalten den Regionalwert.
- `Upper_Date` wird nur angezeigt (`zeit.itinere.spaeteste_belegte_nutzung`).
- Kennzeichnung in `zeit.datierung`:
  - `itinere_belegt`: ≥ 90 % der zugeordneten Länge datiert
  - `itinere_teilweise`: ein Teil datiert
  - `regionalmodell_nicht_einzelbelegt`: keine Belege

**Regionen korrigiert:**
- Das gelieferte Regionalmodell ordnete Linien nach Rechtecken zu. Dadurch lagen etwa Straßen in Tunesien in „italien“ (Ausbau ab 310 v. Chr. statt nach 146 v. Chr.) und Straßen in Dalmatien in „italien“.
- Das Skript bestimmt die Region nun aus der Provinzfläche (`data/reiche.json`, Stand 150 n. Chr.), in der der Großteil der Linie liegt. Die Werte übernimmt es dann aus `regionen_modell`.
- Betroffen sind 170 Linien. Vermerk in `zeit.region_korrektur`.

**Ergebnis (819 Linien):** 200 belegt, 181 teilweise belegt, 438 nur regional, 8 ohne Zuordnung. Die ursprünglichen Werte stehen in `zeit.regional`. Koordinaten, `s` und `id` bleiben unverändert. Das Skript lässt sich wiederholt ausführen und liefert dasselbe Ergebnis.

## Wachstumsnetz (`zeit.netz`)

    python build_strassen_zeit.py --netz      # ohne Itiner-e-Rohdaten; läuft auch am Ende der Anreicherung

Damit das Netz von den schon gezeichneten Straßen aus wächst und keine Linie losgelöst „in der Mitte“ beginnt:
- Linien mit gleichem `beginn_min` bilden eine Gruppe; die Gruppen werden zeitlich nacheinander verarbeitet.
- In einer Gruppe kommt als Nächstes immer die Linie, die dem schon gezeichneten Netz am nächsten liegt (frühere Gruppen eingeschlossen). Die erste Linie überhaupt ist die Rom am nächsten gelegene.
- `u`: Anschlusspunkt als Anteil der Linienlänge (0 = erster Punkt). Von dort wächst die Linie in beide Richtungen.
- `von`/`bis`: Zeichenfenster. Das Netz einer Gruppe wächst gleichmäßig entlang der Netzentfernung und ist zum spätesten `beginn_modell` der Gruppe fertig.
- Eine Linie beginnt erst, wenn ihr Anschlusspunkt auf der Elternlinie gezeichnet ist (Landanschluss ≤ 0,15°). Liegt ein Itiner-e-Beleg früher, wird die Elternlinie entsprechend früher gezeichnet.
- `ueber_see: true`: Anschluss über das Meer (Inseln, Überfahrten). Hier wird nicht auf die Elternlinie gewartet.
- `anschluss`: id der Elternlinie. 4 Linien ohne Ausbauzeitraum (`beginn_min` = `beginn_max`) erscheinen ohne Fenster.

**Andere Straßendaten geprüft:** ORBIS (Stanford) und die AWMC/DARMC-Straßen (Liste von Project MERCURY) haben keine Jahreszahlen und sind gröber als Itiner-e. Einzelheiten in `docs/DATENQUELLEN.md`.

## Genauere Datierungen ergänzen

- Direkt in `data/roemerstrassen.json` je Linie `zeit.beginn_min`/`beginn_max` setzen und `zeit.datierung` sowie `zeit.quelle_datierung` mit Beleg angeben. Achtung: `build_strassen_zeit.py` setzt diese Werte aus `zeit.regional` neu. Dauerhafte Einzelbelege gehören deshalb in eine eigene Liste im Skript.
- Mittelalterliche Nutzung: Ein künftiges Feld (z. B. `zeit.mittelalter: {von, bis, quelle}`) könnte einzelne Abschnitte als nachweislich genutzt markieren. Es ist noch nicht umgesetzt, weil keine belastbaren Daten vorliegen.

## Einschränkungen

- Alle Zeitwerte außer den Itiner-e-Belegen sind regionale Schätzungen; die Einblendung ist eine Animation, kein Baufortschritt.
- Die Zeitleiste hat eine Lücke zwischen 480 und 1400. Die Jahre 500–1399 lassen sich in der App nicht anwählen, die Rechenlogik deckt sie aber ab (siehe Tests).
- Für 1400–1453 ist keine Straße aktiv. Das heißt nicht, dass die Wege verschwunden waren, nur dass der Datensatz keine Belege enthält.
- Linien, die mehrere Regionen durchlaufen, erhalten die Region, in der der Großteil ihrer Länge liegt.

## Tests

    node tests/strassenzeit.test.js                    # Rechenlogik mit den echten Daten (11 Tests)
    python tests/test_strassen_browser.py [ordner]     # App im Browser (22 Prüfungen inkl. ORBIS-Schiffsverkehr, benötigt playwright + Edge/Chromium)
