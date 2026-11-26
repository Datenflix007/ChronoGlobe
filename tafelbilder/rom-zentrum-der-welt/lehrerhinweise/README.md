# Lehrerhinweise

Die Dateien in diesem Ordner erscheinen im Tafelbild im Fenster **Lehrerhinweise** (Knopf oben rechts), je Datei ein Reiter:

| Reiter | Datei |
|---|---|
| Unterrichtsreihe | `01_unterrichtsreihe.md` |
| Kompetenzziele | `02_kompetenzziele.md` |
| Handlungsziele | `03_handlungsziele.md` |
| Sachanalyse | `04_sachanalyse.md` |
| Methodisch-didaktische Analyse | `05_methodisch_didaktische_analyse.md` |
| Verlaufsplan | `06_verlaufsplan.md` |
| Freigabe-Drehbuch | `07_freigabe_drehbuch.md` |

Reiter und Dateien sind in `../tafelbild.json` unter `lehrerhinweise` festgelegt (`ordner`, `reiter`: `id`, `titel`, `datei`).

Unterstütztes Markdown (eigener kleiner Leser, keine externe Bibliothek):
- Überschriften `#`, `##`, `###` (die erste `#`-Überschrift wird nicht angezeigt, der Reiter trägt den Titel)
- Absätze, **fett**, *kursiv*, `Code`, [Links](https://example.org)
- Listen mit `-` oder `1.`, Zitate mit `>`
- Tabellen im Format `| a | b |` mit Trennzeile `|---|---|`
- HTML-Kommentare `<!-- … -->` werden nicht angezeigt (z. B. für Gerüste und Notizen)

Die Seite muss über einen Webserver laufen (z. B. `python -m http.server`), damit die Dateien geladen werden können.
