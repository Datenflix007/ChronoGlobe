# Ein neues Tafelbild erstellen

Ein Tafelbild ist ein Ordner `tafelbilder/<id>/`. Er legt fest, was vom Kern (Globus, Daten, Menü) zu sehen ist, wie das Tafelbild startet, und bringt eigene Inhalte mit. Den Kern ändert man dafür nicht.

## Schritt für Schritt

1. **Ordner anlegen:** `tafelbilder/_vorlage/` nach `tafelbilder/<id>/` kopieren.
   - Die ID besteht aus Kleinbuchstaben, Ziffern und Bindestrichen, höchstens 60 Zeichen, z. B. `seidenstrasse-han`.
2. **`tafelbild.json` ausfüllen** (Felder siehe unten).
3. **Startansicht ausprobieren:**
   - `python -m http.server` starten und `http://localhost:8000/app.html?tafelbild=<id>` öffnen.
   - Jahr, Kamera und Ebenen einstellen und die Werte in `start`, `ebenen.aktiv` und `fokuspunkte` übernehmen.
   - Die aktuelle Kamera liefert in der Browser-Konsole `ChronoGlobe.getState().kamera`.
4. **Vorschaubild:** `vorschau.jpg`, etwa 640 × 400 Pixel, z. B. ein zugeschnittenes Bildschirmfoto der Startansicht.
5. **Optional:**
   - Lehrerhinweise (Markdown) in `lehrerhinweise/`.
   - Eigene Vignetten (`vignetten.json`, Format `docs/VIGNETTEN.md`).
   - Weitere Daten-Overlays.
6. **Eintragen** in `tafelbilder/index.json`: `{ "id": "<id>" }`. Die Reihenfolge der Einträge ist die Reihenfolge in der Galerie.
7. **Prüfen:** `python tools/check_tafelbilder.py` muss ohne Fehler durchlaufen.
8. **Testen:**
   - Galerie auf `index.html` öffnen.
   - Tafelbild öffnen.
   - Optional mit einer Live-Session (`?sync=lokal` ohne Supabase, siehe `tests/test_session.py`).

## Felder von `tafelbild.json`

| Feld | Pflicht | Bedeutung |
|---|---|---|
| `id` | ja | gleich dem Ordnernamen |
| `titel` | ja | Name in Galerie und Session-Auswahl |
| `kopf`, `untertitel` | `untertitel` ja | Kopfzeile im Globus, z. B. „Digitales Tafelbild“ und die Leitfrage |
| `beschreibung` | ja | ein bis zwei Sätze für die Galerie |
| `vorschaubild` | ja | Dateiname im Ordner |
| `zeitraum` | ja | `{ von, bis, epochen }` in historischen Jahren ohne Jahr 0 (−44 = 44 v. Chr.). Die Zeitleiste lässt nur diesen Bereich zu, und es werden nur Reiche geladen, die in diesen Zeitraum fallen. Beginnt er vor 300 v. Chr., erscheint links der Abschnitt „Frühe Hochkulturen“. |
| `start` | ja | `{ jahr, ansicht: "sat" \| "schem", kamera: <Fokuspunkt-id> \| {lat, lng, alt}, drehen }` |
| `reiche` | ja | `{ verfuegbar: "alle" \| [ids], aktiv: [ids] }`; IDs aus `data/reiche.json` → `meta` |
| `ebenen` | ja | `{ verfuegbar: "alle" \| [ebenen], aktiv: { ebene: true/false } }`, siehe unten |
| `fokuspunkte` | ja | Liste `{ id, name, knopf, lat, lng, alt, jahr?, filter? }` |
| `lehrerhinweise` | nein | `{ ordner, reiter: [{ id, titel, datei }] }`; fehlt das Feld, gibt es keinen Knopf „Lehrerhinweise“ |
| `schueler_ui` | nein | Voreinstellung „Schüleransicht anpassen“ für Live-Sessions, z. B. `{ "ebenen": true, "infokarten": false }`. Schlüssel: `reiche`, `ebenen`, `suche` (Standard `false`), `spuren`, `infokarten` (Standard `true`); siehe `docs/ARCHITEKTUR.md` |
| `daten` | nein | Daten-Overlays, siehe unten |

**Ebenen**

- `orte`, `schlachten`, `vw` (Völkerwanderung), `limes` (Grenzanlagen), `geo` (Historische Geographie: Flüsse, Gebirge, Meere, Landschaften)
- `handel`; darunter `land`, `see`, `waren`, `gesandt`, `karawanen`, `strassen`, `schiff`
- `zh` (Zheng He), `bilder` (Abbildungen statt Symbole)
- `netze` (Menü „Handels- und Verkehrsnetze“); in `aktiv` als Liste von Netz-ids, z. B. `"netze": ["tang"]` (ids in `data/netze/index.json`, siehe `docs/HANDELSNETZE.md`)
- `weltbild` (Menü „Weltbilder“): in `aktiv` die id eines Weltbilds aus `data/weltbilder/index.json` (`plinius`, `ebstorf`) oder `null`
  - Das Weltbild zeigt seine Einträge auf dem Globus; bei Karten gibt es zusätzlich die Schriftrolle mit dem Original.
  - `weltbild_projektion` (nur in `aktiv`, Standard `true`): Karte bzw. Rand der bekannten Welt auf den Globus legen.
  - Neue Weltbilder entstehen in `build_weltbilder.py` (Kern), nicht im Tafelbild-Ordner.
- Nur in `aktiv`: `strassen_ehemals`, `strassen_animieren`, `weltbild_projektion`

**Fokuspunkte**
- Erscheinen im Menü als Knöpfe.
- In Live-Sessions sind sie die Fokus-Knöpfe der Lehrkraft. Sie setzen die Kamera bei allen, auch bei Schüler:innen mit „Globus selbst bedienen“.
- `alt` ist der Kameraabstand: etwa 1 = Region, 2,7 = halbe Erdkugel; `"standard"` passt sich dem Bildschirm an.
- Optional:
  - `jahr`: das Jahr springt mit.
  - `filter`: Teilzustand im Format von `getState`, z. B. `{ "handel": { "on": true, "strassen": true } }`.

**Daten-Overlays**

```json
"daten": {
  "vignetten": { "datei": "vignetten.json", "art": "ersetzen" },
  "handel":    { "datei": "handel_extra.json", "art": "ergaenzen" }
}
```

- Erlaubte Schlüssel: `reiche`, `handel`, `zhenghe`, `texte`, `literatur`, `roemerstrassen`, `orbis_schiff`, `vignetten`.
- `ersetzen`: Die Tafelbild-Datei wird statt der Kerndatei geladen.
- `ergaenzen`:
  - Objekte werden rekursiv gemischt, Listen angehängt.
  - Ein Eintrag mit gleicher `id` ersetzt den Kerneintrag, z. B. eine Route aus `handel.json` mit anderer Beschreibung.

Neue Texte und Belege folgen den Grundregeln in `docs/GRUNDREGELN.md`.

## Was ein Tafelbild nicht kann

- **Eigenes JavaScript:** Neue Funktionen gehören in den Kern und müssen dann für alle Tafelbilder funktionieren (`CLAUDE.md`).
- **Andere Abschnitte der Zeitleiste:** Die Abschnitte stehen im Kern (`SEGS` in `js/app.js`). `zeitraum` begrenzt nur die wählbaren Jahre.
