# Digitales Tafelbild: Rom und China

Statische Unterseite (kein Build nötig, keine externen Dienste).

## Einbinden
1. Ordner `tafelbild/` in dein Repo `datenflix007.github.io` legen und pushen.
2. Erreichbar unter `https://datenflix007.github.io/tafelbild/`.
3. Verlinken: `<a href="tafelbild/">Digitales Tafelbild</a>`.
Lokal testen: `python3 -m http.server` im Ordner, dann http://localhost:8000 (nicht per Doppelklick öffnen).

## Bedienung
Ansicht Satellit/Schematisch, Reiche ein-/ausblenden, Zeitstrahl ziehen (Marker = Ausdehnungsstufen, ←/→ Jahr, Shift = 10 Jahre,
Leertaste = Abspielen). Auf Rom/China hineinzoomen (Mausrad/Pinch) oder „Karte entrollen" klicken -> Reichskarte; Esc schließt.

## Daten ändern
`data/reiche.json` (Stufen, Texte, Orte). Neu erzeugen mit `build_data.py` (Python, shapely).

## Wichtig
Die Reichsgrenzen sind schematische Handzeichnungen, in Stufen (kein Morphing). Vor Einsatz im Unterricht mit einem
Geschichtsatlas abgleichen; die Seite weist selbst darauf hin.
