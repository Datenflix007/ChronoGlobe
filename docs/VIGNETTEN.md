# Vignetten in der Schriftrolle

Ein Klick auf ein eingeblendetes Reich (Globus oder „Schriftrolle öffnen“ im Infoband) öffnet dessen Schriftrolle.
Sie hat zwei Reiter: **Vignetten** (beim Römischen Reich **Wiederholung**) und **Karte**.

Die Inhalte stehen in `data/vignetten.json`. Die Engine liegt in `js/vignetten.js`.
Vorschau aller Bausteine mit Beispielinhalt: `app.html?modus=frei&vignetten=demo` (Datei `data/vignetten_demo.json`). Ein Tafelbild bringt seine Vignetten als Daten-Overlay mit (`tafelbilder/<id>/vignetten.json`, siehe `docs/TAFELBILD_ERSTELLEN.md`).

Für die Sachinhalte gelten die Regeln in `docs/GRUNDREGELN.md`. Erfundene Erzählungen stehen immer im Baustein `erzaehlung`, der sie automatisch als erfunden kennzeichnet.

## Aufbau der Datei

```json
{
  "platzhalter": 5,
  "reiche": {
    "rom": {
      "modus": "wiederholung",
      "titel": "",
      "einleitung": "",
      "vignetten": [
        { "id": "rom-1", "titel": "Die Gründung Roms", "bloecke": [ … ], "quellen": [ "…" ] }
      ]
    },
    "han": { "modus": "vignetten", "vignetten": [ … ] }
  }
}
```

- Schlüssel unter `reiche` sind die Kürzel aus `data/reiche.json` (`rom`, `han`, `karth`, `ptol`, `seleu`, `parth`, `sasan`, `maurya`, `kusch`, `gupta`, `xiong`, `xianb`, `hunnen`).
- Ein Eintrag `"*"` gilt für alle Reiche ohne eigenen Eintrag.
- `modus`:
  - `"vignetten"`: Reiter „Vignetten“, Kacheln heißen „Vignette 1, 2, …“.
  - `"wiederholung"`: Reiter „Wiederholung“, Kacheln heißen „Aufgabe 1, 2, …“.
- `titel` ersetzt die Überschrift (sonst der Reichsname). `einleitung` ersetzt den Satz unter der Überschrift.
- Eine Vignette mit leerer Liste `bloecke` erscheint als gestrichelte Kachel „Inhalt folgt“.
- Hat ein Reich gar keine Vignetten, zeigt die Rolle `platzhalter` leere Kacheln (Standard 5; fünf Vignetten je Rolle sind das vorgesehene Maß).
- `schriftrolle`: `false` heißt, das Reich hat keine Schriftrolle. Es lässt sich dann nicht anklicken, und im Infoband fehlt der Knopf. So legt die Lehrkraft fest, welche Kulturen die Klasse erarbeitet.
- Die europäischen Nachfolgestaaten (Kontext) haben grundsätzlich keine Schriftrolle. Nur ein ausdrückliches `"schriftrolle": true` gibt ihnen eine.
- `quellen` (optional) erscheinen am Ende der Vignette als Liste (Kurzbeleg, z. B. „Vgl. Lewis, Early Chinese Empires.“).
- `source_ids` (optional) verknüpft die Vignette mit Einträgen im Quellenregister `data/sources.json`. Die Liste wird nicht angezeigt. `python tools/check_sources.py` prüft, dass jede ID registriert ist, auch in Tafelbild-Dateien.

## Bausteine (`bloecke`)

Die Bausteine einer Vignette stehen untereinander, in der Reihenfolge der Liste.

In allen Textfeldern gilt: `**fett**`, `*kursiv*`, eine Leerzeile beginnt einen neuen Absatz.

### Inhalt

| `typ` | Felder | Darstellung |
|---|---|---|
| `text` | `text` | Fließtext |
| `merke` | `text`, `titel` (Standard „Merke“) | gelber Merkkasten |
| `erzaehlung` | `text`, `titel`, `hinweis` | Erzählung mit Hinweis „Diese Geschichte ist erfunden …“ |
| `quelle` | `text`, `titel`, `nachweis` | Quellenauszug als Zitat |
| `bild` | `src`, `alt`, `titel`, `unterschrift`, `lizenz` | Bild mit Bildunterschrift |
| `audio` | `src`, `titel`, `unterschrift`, `lizenz` | Abspielleiste, z. B. für Musik oder Hörtext |
| `video` | `src`, `poster`, `untertitel` (.vtt), `titel`, `unterschrift`, `lizenz` | Videoplayer |

Für Medien gilt:

- Dateien liegen im Repository, z. B. unter `media/<reich>/…`. Es werden keine externen Dienste eingebunden (Datenschutz).
- Formate: Bilder `.jpg`, `.png`, `.webp` oder `.svg`; Ton `.mp3`; Video `.mp4` (H.264), möglichst kurz und klein.
- Fehlt eine Datei, steht an ihrer Stelle ein Hinweis.

### Quiz

Jedes Quiz hat die Knöpfe **Prüfen**, **Tipp** (nur wenn `tipp` gesetzt ist), **Lösung zeigen** (ab dem 2. Fehlversuch) und **Nochmal**.

Diese Felder gibt es bei allen Quizarten:

- `frage`
- `titel`: ersetzt die Arbeitsanweisung, z. B. „Wähle die richtige Antwort“.
- `tipp`
- `feedback`: `{ "richtig": "…", "falsch": "…" }`
- `erklaerung`: erscheint nach richtiger Lösung und bei „Lösung zeigen“.

| `typ` | eigene Felder | Beispiel |
|---|---|---|
| `einfach` | `antworten: [{text, richtig, feedback}]`, `mischen` (Standard an) | eine richtige Antwort |
| `mehrfach` | wie `einfach`, mehrere mit `"richtig": true` | mehrere richtige Antworten |
| `wahrfalsch` | `aussagen: [{text, richtig: true/false, feedback}]`, `mischen` (Standard aus) | „stimmt / stimmt nicht“ je Aussage |
| `luecke` | `text` mit `{{Lösung}}` oder `{{Lösung\|andere Schreibweise}}`, `woerter` (Wörterkasten, optional) | Lückentext; Groß-/Kleinschreibung egal |
| `zuordnen` | `paare: [{links, rechts}]`, `mischen` | Auswahlliste je Begriff |
| `reihenfolge` | `elemente: [ … ]` in **richtiger** Reihenfolge (angezeigt wird gemischt) | Sortieren mit ↑/↓ |
| `zahl` | `antwort`, `toleranz` (± erlaubt), `einheit` | Schätzfrage, z. B. Jahreszahl; Hinweis „zu groß/zu klein“ |

Ein `feedback` an einer einzelnen Antwort (bei `einfach`, `mehrfach` und `wahrfalsch`) erscheint, wenn genau diese Antwort falsch gewählt wurde. Damit lässt sich gezielt auf typische Fehler eingehen.

Beispiel:

```json
{ "typ": "einfach", "frage": "…?",
  "antworten": [
    { "text": "…", "richtig": true },
    { "text": "…", "feedback": "Das verwechselt man leicht mit …" }
  ],
  "tipp": "…",
  "feedback": { "richtig": "Genau!", "falsch": "Lies noch einmal nach." },
  "erklaerung": "…" }
```

Die Kachel in der Übersicht zeigt, wie viele Quizfragen der Vignette schon richtig gelöst sind (z. B. „2/3“). Dieser Stand bleibt nur, solange die Seite geöffnet ist. Er wird nicht gespeichert und nicht übertragen.

## Neue Bausteine ergänzen

In `js/vignetten.js` gibt es zwei Tabellen:

- `BLOCK` für Inhaltsbausteine: Funktion `b → DOM-Element`.
- `QUIZ` für Quizarten: Funktion `b → { body, pruefen, loesen, reset, inputs }`.

Ein neuer Eintrag dort ist sofort als `typ` nutzbar. Unbekannte Typen erscheinen in der Rolle als roter Hinweis.
