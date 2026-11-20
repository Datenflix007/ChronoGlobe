# Datenquellen für Straßen und Städte

Stand der Prüfung: 20.11.2026. Geprüft wurden ORBIS und die Datensatzliste von Project MERCURY. Ziel war, Straßen und Städte des Tafelbilds aus offenen Forschungsdaten zu speisen.

## Kurzfassung

| Bereich | Derzeit im Tafelbild | Geprüfte Alternative | Entscheidung |
|---|---|---|---|
| Straßenverlauf | Itiner-e (2025), 819 vereinfachte Hauptstraßen | ORBIS-Straßennetz (2012/2014) | **Itiner-e bleibt**: genauer, neuer, teils datiert |
| Zeitangaben der Straßen | regionales Modell + Itiner-e-Belege | ORBIS: keine Jahreszahlen | ORBIS hilft hier nicht |
| Reisezeiten, Seewege | – | ORBIS: Geschwindigkeit und Kosten je Strecke, See- und Flussrouten | möglicher **neuer Baustein** |
| Römische Städte | 94 Orte, von Hand gesetzt (`data/reiche.json` → `orte`) | Hanson, Cities Database (1388 Städte, mit Anfangsjahr) | möglicher **Ersatz/Ergänzung**, Lizenz vorher klären |
| Ortsnamen, Koordinaten | von Hand | Pleiades (Ortsverzeichnis), ORBIS-Orte | zum Abgleich geeignet |

## ORBIS – The Stanford Geospatial Network Model of the Roman World

- Website: https://orbis.stanford.edu/ (Walter Scheidel, Elijah Meeks, Stanford University Libraries)
- Daten: GitHub `emeeks/orbis_v2`, Lizenz des Repositorys **MIT**. Kartenkacheln der Website: AWMC, CC BY-NC 3.0 (werden hier nicht verwendet).
  - `sites_extended.csv`: 670 Orte mit Name, Rang (60–100), Koordinaten, Provinz, heutigem Land
  - `base_routes.geojson`: 1215 Strecken zwischen diesen Orten, Feld `t`:

    | `t` | road | coastal | overseas | upstream | downstream | ferry |
    |---|---|---|---|---|---|---|
    | Anzahl | 627 | 411 | 69 | 54 | 49 | 5 |

    Dazu kommen je Strecke `e` (Kosten) und `s` (Geschwindigkeit) des Verkehrsmodells.
- **Zeitbezug:** keiner. ORBIS bildet das Netz als Momentaufnahme um 200 n. Chr. ab. Es gibt keine Bau- oder Nutzungsjahre.
- **Straßen:** Die 627 Straßenstrecken ergeben gemessen rund 60 000 km. Sie verbinden nur die ORBIS-Orte und beruhen auf dem Barrington Atlas (2000). Itiner-e ist neuer, deutlich dichter (laut Projektangaben knapp 300 000 km) und für einen Teil der Abschnitte datiert. Ein Wechsel brächte deshalb weniger Genauigkeit und keine Zeitangaben.
- **Was ORBIS zusätzlich bietet:**
  - Reisezeiten und Kosten, z. B. „Wie lange dauerte eine Reise von Rom nach Londinium?“
  - See- und Flussrouten (Küstenschifffahrt, Hochsee, Flüsse)

  Für ein Tafelbild zur Leitfrage „Zentrum der Welt?“ wäre das didaktisch reizvoll, etwa als Entfernungskarte ab Rom.

## Project MERCURY – Datensatzliste

- https://projectmercury.eu/datasets/ (Computational Modelling in Roman Studies). Eine Sammlung von Links zu offenen Datensätzen, ohne eigene Daten.
- Für Straßen und Städte relevant:
  - **Transport system (Orbis)** → siehe oben.
  - **Roads:** AWMC/DARMC-Straßenshapefiles (Barrington Atlas). Ebenfalls ohne Datierung und älter als Itiner-e.
  - **Urban areas / Cities: Hanson (2016), Cities Database (OXREP)**
    - Download: http://oxrep.classics.ox.ac.uk/oxrep/docs/Hanson2016/Hanson2016_Cities_OxREP.csv
    - Inhalt: 1388 Orte mit städtischen Merkmalen (100 v. Chr. – 300 n. Chr.). Zu jedem Ort gibt es antiken und heutigen Namen, Provinz, Rang im Barrington Atlas (1–5), Koordinaten, Bibliografie, **Anfangsjahr** (`Start Date`, bei allen gefüllt) und Endjahr (`End Date`, nur bei 38 gefüllt).
    - Abgleich: 92 der 94 römischen Orte des Tafelbilds liegen höchstens 0,2° von einem Hanson-Ort entfernt.
    - **Lizenz:** „Terms and Conditions of Use for Oxford University Research Archive“, keine freie Lizenz wie CC BY. Gefordert ist die Zitierung von Datenbank und Monografie. Vor einer Übernahme in dieses öffentliche Repository ist zu klären, ob Weitergabe und Veröffentlichung erlaubt sind.
    - Zitierung: Hanson, J. W. (2016): Cities Database (OXREP databases), Version 1.0, DOI 10.5287/bodleian:eqapevAn8; Hanson, J. W. (2016): An Urban Geography of the Roman World, 100 B.C. to A.D. 300, Oxford.
  - **Places (Pleiades):** https://pleiades.stoa.org/downloads – Ortsverzeichnis der antiken Welt (alle Orte des Barrington Atlas), Lizenz CC BY 3.0. Geeignet zum Abgleich von Namen und Koordinaten.

## Was eine Übernahme bedeuten würde

1. **Städte aus Hanson** (nach Klärung der Lizenz):
   - Ein Ort erscheint ab seinem Anfangsjahr, aber nur, solange sein Gebiet zum Römischen Reich gehört (wie bisher).
   - Die Zoomstufen ergeben sich aus dem Barrington-Rang (1 → Weltstadt … 4/5 → nur ganz nah).
   - Die Liste ist rund 15-mal so lang wie die bisherige. Die Ausdünnung nach Zoomstufe bleibt daher wichtig.
   - Grenze: Hanson deckt nur das Römische Reich ab. Han-China und die Nachbarreiche bleiben von Hand gepflegt.
2. **Reisezeiten aus ORBIS** (MIT):
   - neuer Schalter, z. B. „Reisezeit ab Rom“, mit Einfärbung der Orte nach Tagen
   - einfaches Wegenetzmodell aus `base_routes.geojson`, nicht das vollständige ORBIS-Modell mit Jahreszeiten und Verkehrsmitteln
3. **Straßen bleiben Itiner-e.** ORBIS und AWMC/DARMC wären ungenauer und haben keine Zeitangaben (siehe `docs/STRASSEN_ZEITMODELL.md`).
