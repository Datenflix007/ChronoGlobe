# Vorlage für ein neues Tafelbild

1. Diesen Ordner kopieren: `tafelbilder/_vorlage/` → `tafelbilder/<neue-id>/`.
   Die ID besteht aus Kleinbuchstaben, Ziffern und Bindestrichen, z. B. `seidenstrasse-han`.
2. `tafelbild.json` ausfüllen. Jedes Feld ist dort mit einem `_hinweis_…` erklärt.
3. Ein Vorschaubild `vorschau.jpg` ablegen (etwa 640 × 400 Pixel, Bildschirmfoto der Startansicht).
4. Optional:
   - Lehrerhinweise als Markdown-Dateien in `lehrerhinweise/`.
   - Eigene Vignetten (`vignetten.json`, Format: `docs/VIGNETTEN.md`).
   - Weitere Daten-Overlays (siehe `daten` in `tafelbild.json`).
5. Das Tafelbild in `tafelbilder/index.json` eintragen.
6. `python tools/check_tafelbilder.py` ausführen, bis keine Fehler mehr gemeldet werden.
7. Testen: `python -m http.server` starten und `http://localhost:8000/app.html?tafelbild=<neue-id>` öffnen.

Ausführliche Anleitung: `docs/TAFELBILD_ERSTELLEN.md`. Grundregeln für Texte und Belege: `docs/GRUNDREGELN.md`.
