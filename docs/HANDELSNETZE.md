# Handels- und Verkehrsnetze aus Forschungsdaten

Stand: 21.11.2026. Menü „Handels- und Verkehrsnetze“ (aufklappbar), Gruppen **Landwege**, **Wasserwege** und **Reiseberichte**.

## Überblick

| Netz | Gruppe | Zeitraum | Datierung | Umfang | Lizenz |
|---|---|---|---|---|---|
| Weihrauchstraße Petra – Gaza | Landwege | 300 v.–200 n. Chr. | Zeitraum (UNESCO 1107) | 4 Abschnitte, 17 Fundorte | CC BY 4.0 |
| Seidenstraße der Tang | Landwege | 618–907 | jahrgenau | 47 Strecken, 316 Verkehrspunkte | CC BY 4.0 |
| Straßen der Levante (VIA-TARIQ) | Landwege | 650–1517 | vier Perioden | 2372 Abschnitte, 288 Städte/Stationen | CC BY 4.0 |
| Wegenetz der islamischen Welt (al-Ṯurayyā) | Landwege | 800–1000 | Zeitraum des Atlas | 2053 Abschnitte, 126 große Orte | CC BY 4.0 |
| Reisende der Mongolenzeit | Reiseberichte | 1218–1353 | Reisedaten (Monat) | 20 Reisen von 15 Reisenden | CC BY 4.0 |

Daneben bestehen weiterhin (unter „Handel & Austausch“): Seidenstraße der Han, Römerstraßen (Itiner-e), Schiffsverkehr (ORBIS), Fahrten des Zheng He. Die Quellenübersicht im Menü listet alle Netze, auch die geprüften, aber nicht übernommenen.

## Grundsätze

- **Keine erfundenen Strecken oder Jahre.**
  - Verläufe und Jahre stammen aus dem Datensatz.
  - Wo ein Datensatz keine Jahre hat, gilt ein dokumentierter Zeitraum für den ganzen Datensatz:
    - Petra – Gaza: UNESCO-Welterbe Nr. 1107.
    - al-Ṯurayyā: Darstellungszeitraum des Atlas von G. Cornu.
- **Keine Epochenmischung.** Ein Netz ist nur in seinem Zeitraum sichtbar (Test 6 in `tests/netze.test.js`).
  - VIA-TARIQ zeigt je Jahr genau eine Periode.
  - Das Grenzjahr gehört zur jüngeren Periode.
- **Wege sind keine Handelsströme.**
  - `art` unterscheidet `handelsweg`, `verkehrsnetz` und `reiseroute`.
  - Postwege (barīd) und Pilgerwege (Hadsch) in VIA-TARIQ sind eigens eingefärbt und in der Infokarte erklärt.
  - Reiseberichte stehen in einer eigenen Gruppe mit dem Hinweis „keine Handelsrouten“.
- **Lizenz vor Import.** Übernommen werden nur offene Lizenzen; Test 5 lässt nur CC BY 4.0, CC0, MIT und ODbL zu.
- **Keine fremden Server zur Laufzeit.**
  - Alle Netze liegen unter `data/netze/`.
  - Eine Netzdatei wird erst geladen, wenn das Netz eingeschaltet wird.
- **Bestehendes bleibt unverändert.** Der Browsertest vergleicht Straßen, ORBIS, Limes, Flächen und Beschriftungen mit und ohne Netze.

## Zeitleiste

- **Freies Erkunden** (ohne Tafelbild-Zeitraum):
  - Die frühere Lücke 480–1400 wird zum Teil **„Mittelalter“** mit eigenem Maßstab (`mittelalterEinrichten` in `js/app.js`).
  - Der antike Teil wird dafür etwas schmaler.
  - Es gibt keinen Zeitsprung mehr.
- **Tafelbilder** behalten ihren Zuschnitt (`zeitraum`). Rom und Aufbruch sind unverändert (Regressionstests).
- **Ein Netz einschalten:**
  - Liegt das Jahr außerhalb des Netzzeitraums, springt die Zeitleiste an den Anfang des Netzes.
  - Das gilt nur, wenn der Zeitriegel frei ist; ein Hinweis erklärt den Sprung.

## Datenmodell (`data/netze/<id>.json`)

```js
{ id, name,
  gruppe: 'land' | 'wasser' | 'reise',
  art: 'handelsweg' | 'verkehrsnetz' | 'reiseroute',
  datierung: { typ: 'jahrgenau' | 'zeitraum' | 'reisedatum', von, bis, text, perioden?: [{ id, name, dynastien, von, bis }] },
  hinweis?,                                  // z. B. „keine Handelsrouten“
  quelle: { zitat, doi?, daten_doi?, url, lizenz, lizenz_url, geaendert, zeit_beleg? },
  reisen?: [{ id, reisender, reisender_zh, bericht, bericht_zh, von, bis }],
  linien: [{ id, name, von, bis, teile: [[[lng, lat], …], …], km?,
             // je nach Netz: zh, periode, haupt, itinerar, post, hadsch, quelle_mittelalter, literatur, lage, beleg,
             //               reise, vonMonat, bisMonat
           }],
  orte:   [{ id, name, lng, lat, typ, von, bis, … }] }
```

### Zeitfilter (`js/netze.js`)

| `datierung.typ` | Linie bzw. Ort sichtbar |
|---|---|
| `jahrgenau` | `von ≤ Jahr ≤ bis` (eigene Jahre je Eintrag) |
| `zeitraum` | wie oben. Bei Perioden gilt `[von, bis)`; nur die letzte Periode schließt `bis` ein. |
| `reisedatum` | Eine Reise ist sichtbar von ihrem Beginn bis drei Jahre nach dem Ende (`NACHLEUCHTEN`, Darstellungsregel). |

Bei `reisedatum` gilt für die Etappen:

- Sie erscheinen ab ihrem Anfangsjahr.
- Stil `aktiv`: die laufende Etappe.
- Stil `gereist`: Etappen, die während der Reise schon zurückgelegt sind.
- Stil `blass`: nach Reiseende.
- Stationen sind nur sichtbar, solange die Reise läuft.

`Netze.pruefen(netz)` prüft das Modell. Fehler erscheinen beim Laden als Warnung in der Konsole und im Test als Fehler.

### Register (`data/netze/index.json`)

- Pro Netz ein Eintrag mit `id`, `status`, `gruppe`, `name`, `von`/`bis`, `datierung`, `farbe`, `kurz`, `lizenz`, `quelle` sowie `datei` (verfügbar), `ort` (bestehend) oder `grund` (nicht übernommen).
- Mögliche Werte für `status`:

| `status` | Bedeutung |
|---|---|
| `verfuegbar` | Schalter in diesem Menü |
| `bestehend` | Ebene an anderer Stelle im Menü; hier nur in der Quellenübersicht |
| `nicht_verfuegbar` | geprüft, nicht übernommen |
| `nicht_lizenziert` | geprüft, nicht übernommen |
| `zurueckgestellt` | geprüft, nicht übernommen |

## Zustand, Sessions, Tafelbilder

- **Zustand:** `getState().netze = { petra_gaza: false, tang: true, … }`.
  - `applyState({ netze: { tang: true } })` schaltet Netze und lädt sie bei Bedarf.
  - Damit funktionieren die Netze in Live-Sessions.
- **Infokarten** gehören zum Zustand (`fenster.info`):
  - `{ art: 'netzlinie', netz, id }`
  - `{ art: 'netzort', netz, id }`
  - `{ art: 'netzquellen' }`
- **Tafelbild:**
  - Die Netze erscheinen nur, wenn `ebenen.verfuegbar` den Eintrag `"netze"` enthält.
  - Vorab einschalten: `ebenen.aktiv.netze: ["tang", …]`.
  - Overlays sind möglich: Schlüssel `netze` für das Register, `netz_<id>` für eine Netzdatei.
  - Die bestehenden Tafelbilder nutzen die Netze (noch) nicht.

## Daten neu erzeugen

```
python build_netze.py <rohdaten-ordner>
```

Benötigt `pyshp`, `shapely` und `pypinyin`. Der Rohdaten-Ordner liegt nicht im Repository. Er enthält:

| Unterordner | Herkunft | Abruf |
|---|---|---|
| `althurayya/` (`routes.json`, `places.geojson`) | github.com/althurayya/althurayya.github.io, Ordner `master/` | raw.githubusercontent.com |
| `tang/` (`交通线.*`, `交通点.*`) | Science Data Bank, DOI 10.57760/sciencedb.587 | `scidb.cn/api/gin-sdb-filetree/getAllUrl?dataSetId=633694461053894658&version=V1` liefert den Download. Das RAR enthält GBK-Dateinamen; Windows-`tar` entpackt erst nach Umbenennen der Kopfeinträge. |
| `mongolen/` (`蒙元线shapefile/`, `蒙元点shapefile/`) | Science Data Bank, DOI 10.57760/sciencedb.622 | wie oben, `dataSetId=633694461087449088`. Das ZIP hat GBK-Namen (`cp437 → gbk`). |
| `viatariq/` (`<periode>_roads.geojson`, `<periode>_sites.geojson`) | Zenodo, Version 1.1, DOI 10.5281/zenodo.21981430 | `zenodo.org/records/21981430/files/<name>?download=1`. Zenodo sperrt automatische Abrufe zeitweise (403). |
| `petra_gaza/` (`compiled_insence_road.*`, `sites.*`) | Zenodo, DOI 10.5281/zenodo.3413625 | wie oben |

Umrechnungen in `build_netze.py`:

- World Mercator (EPSG:3395) bei VIA-TARIQ.
- UTM Zone 36N bei Petra – Gaza.
- Formeln nach Snyder (1987). Geprüft an den Lon/Lat-Spalten der Petra-Fundorte: Abweichung unter 15 m.

## Geprüfte, nicht übernommene Quellen

| Quelle | Ergebnis |
|---|---|
| Weihrauchstraßen der Arabischen Halbinsel (ArcGIS 394b5ddec04c44208b28838d3daf3d9d, Staedtler) | Keine offene Lizenz: Laut Lizenzfeld unveröffentlichte eigene Forschung („Staedtler forthcoming“), nur Zitieren erlaubt. |
| Postnetz der Ming-Zeit (Berman/Zhang/Douai 2016, Harvard Dataverse DOI 10.7910/DVN/SB8ZTM; GitHub ruoranc/Mingroutes) | Dataverse-Fassung CC0, GitHub-Fassung ohne Lizenz. Der Datensatz zeigt die **späte** Ming-Zeit (nach Yang Zhengtai) und liegt damit nach 1453. **Zurückgestellt**, bis die Zeitleiste bis 1644 reicht; dann als Postnetz. |
| Südliche Seidenstraße (Dili Yanjiu 2022, DOI 10.11821/dlyj020210210) | Aufsatz mit Karten, keine freien Geodaten gefunden. |
| China Historical GIS | Verwaltungseinheiten, keine Verkehrswege; automatische Abrufe blockiert. |
| Kaiserkanal / Kanäle Chinas (GeoDOI 4028) | Seite lieferte nur die Portalübersicht (vorher Fehler 500); Lizenz und Download nicht prüfbar. |
| OWTRAD (Ciolek; Library of Congress) | Abruf blockiert (403); Lizenz unklar. |

Für die **Wasserwege** gibt es damit keine neue frei lizenzierte Quelle. Die Gruppe verweist auf ORBIS und Zheng He.

## Tests

- `node tests/netze.test.js` (14 Prüfungen):
  - Register, Datenmodell, Lizenzen.
  - Keine Epochenmischung.
  - Testjahre −300, 100, 430, 700, 850, 1050, 1250, 1350, 1440.
  - Perioden, Post- und Pilgerwege, Reiseberichte.
- `python tests/test_netze_browser.py [ordner]` (24 Prüfungen):
  - Mittelalter-Teil nur im freien Erkunden; Menü.
  - Keine fremden Server; bestehende Ebenen unverändert.
  - Testjahre, Zustand, Infokarten, Quellenübersicht.
  - Tafelbilder Rom und Aufbruch unverändert.

Im Jahr 430 zeigt kein neues Netz etwas: Für die Zeit zwischen dem Ende der Han (220) bzw. der Weihrauchstraße (200) und dem Beginn der Tang (618) fehlt ein offener Datensatz. Die Römerstraßen und ORBIS decken diese Zeit weiterhin ab.
