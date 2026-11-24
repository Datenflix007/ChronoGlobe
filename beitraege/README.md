# Beiträge aus dem Editor

Hier landen Vorschläge aus dem Editor (`editor.html`) als Pull Request: Korrekturen an Gebieten, Routen, Orten, Texten und Schriftrollen sowie neue Themenebenen.

- Eine Datei pro Beitrag: `JJJJ-MM-TT-titel.json`, Format `chronoglobe-beitrag/1` (siehe `docs/EDITOR.md`).
- Die CI prüft jede Datei mit `node tools/check_beitraege.js` (Schema, Belege, Geometrie).
- Ein Beitrag ändert nichts am Globus, solange er nur hier liegt. Übernommen wird er von Hand nach fachlicher Prüfung (`docs/GRUNDREGELN.md`):
  - **Neue Ebene:** `ebene` nach `data/ebenen/<id>.json` kopieren und in `data/ebenen/index.json` eintragen. Danach `python tools/version_setzen.py` ausführen.
  - **Änderung:** in der genannten Datei (`ziel.datei`) umsetzen bzw. im passenden `build_*.py`, falls die Datei erzeugt wird.
  - Danach den Beitrag löschen oder nach `beitraege/erledigt/` verschieben.

`2026-11-24-beispiel-pyramiden-im-alten-aegypten.json` ist ein Beispiel für das Format. Die Pyramiden sind inzwischen Teil der übernommenen Ebene `data/ebenen/monumente-nil-zweistromland.json`.
