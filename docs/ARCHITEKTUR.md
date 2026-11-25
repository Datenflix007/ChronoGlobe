# Architektur von ChronoGlobe

## Seiten und Modi

| Adresse | Inhalt |
|---|---|
| `index.html` | Startseite: Freies Nutzen · Session erstellen · Session beitreten · Galerie |
| `index.html?code=XXXXXX` | Link aus dem QR-Code; leitet sofort zum Beitritt weiter |
| `app.html?modus=frei` | Freies Nutzen „Menschheitsgeschichte“: Kern mit vollem Menü, ohne Lehrerhinweise und Tafelbild-Vignetten |
| `app.html?tafelbild=<id>` | ein Tafelbild aus `tafelbilder/<id>/` |
| `app.html?session=<CODE>&rolle=lehrer` | Live-Session, Lehreransicht mit Lehrermenü |
| `app.html?session=<CODE>&rolle=schueler` | Live-Session, Schüleransicht ohne Menü |
| `…&sync=lokal` | Session über den lokalen Übertragungsweg (BroadcastChannel); nur für Tests |
| `…&vignetten=demo` | Vorschau aller Vignetten-Bausteine (`data/vignetten_demo.json`) |

Ladereihenfolge in `app.html`:

```
vendor (globe.gl, d3) → texte.js → vignetten.js → strassenzeit.js → netze.js
→ session.js   stellt CGSession bereit; lädt Supabase nur in Session-Seiten nach
→ tafelbild.js bestimmt Modus und Tafelbild; CG.bereit, CG.daten
→ app.js       Engine: wartet auf CG.bereit, lädt Kern- und Tafelbild-Daten, startet
```

Wenn alles steht, löst `app.js` das Ereignis `chronoglobe:bereit` aus. Darauf startet `session.js` die Lehrer- bzw. Schüleransicht.

## Kern und Tafelbild

- **Kern:** Engine und alle Daten in `data/`.
- **Tafelbild:** `tafelbilder/<id>/tafelbild.json` legt Folgendes fest (Format: `docs/TAFELBILD_ERSTELLEN.md`):
  - Titel, Zeitraum und Startansicht,
  - verfügbare und anfangs aktive Reiche und Ebenen,
  - Fokuspunkte und Lehrerhinweise,
  - Daten-Overlays.
- **Daten-Overlays:** `CG.daten(schluessel, kernUrl)` lädt die Kerndatei. Ist für den Schlüssel eine Tafelbild-Datei angegeben, gilt:
  - `"art": "ersetzen"`: die Tafelbild-Datei statt der Kerndatei.
  - `"art": "ergaenzen"`: Objekte werden rekursiv gemischt, Listen angehängt; ein Eintrag mit gleicher `id` ersetzt den Kerneintrag.
- **Freier Modus:** ein eingebautes Tafelbild ohne `id` (`FREI` in `js/tafelbild.js`).
- **Relevanter Ausschnitt:** Ein Tafelbild lädt nur Reiche, deren Lebenszeit in seinen `zeitraum` fällt (`reicheFiltern` in `js/app.js`).
  - Frühe Hochkulturen (`data/fruehe_reiche.json`, `meta.frueh`) kommen nur dazu, wenn der Zeitraum vor 300 v. Chr. beginnt oder das Tafelbild sie in `reiche.verfuegbar` ausdrücklich nennt.
  - Der freie Modus lädt alles.
- **Zeitleiste:** Abschnitte stehen in `SEGS`. Ein Abschnitt kann mehrere lineare Teile mit eigenem Maßstab haben (`teile`).
  - Beispiel: Die frühen Hochkulturen sind ein Vorlauf des ersten Abschnitts; `zeitleisteEinrichten` legt ihn nur an, wenn solche Reiche geladen sind.
  - `pct`/`yearAt` rechnen über alle Teile; zwischen nicht anschließenden Teilen liegt ein Zeitsprung.
  - Freies Erkunden ohne Tafelbild-Zeitraum: `mittelalterEinrichten` füllt die Lücke 480–1400 mit dem Teil „Mittelalter“
    (für die Handels- und Verkehrsnetze, `docs/HANDELSNETZE.md`). Tafelbilder mit `zeitraum` behalten den Zeitsprung.

## Zentraler Zustand (`js/app.js`)

Der gesamte sichtbare Zustand ist ein serialisierbares Objekt:

```js
{ v: 1, tafelbild: 'rom-zentrum-der-welt',
  jahr: 117, ansicht: 'sat' | 'schem',
  kamera: { lat, lng, alt }, drehen: true,
  reiche: { rom: true, han: true, parth: false, … },
  globus: { orte, schlachten, vw },
  handel: { on, land, see, waren, gesandt, karawanen, strassen, schiff },
  strassen: { ehemals, animieren },
  zh: { on, fahrten: { 1: true, … 7: true }, bilder },
  netze: { petra_gaza, tang, viatariq, thurayya, mongolen },   // Handels- und Verkehrsnetze (data/netze/index.json)
  niveau: 'A' | 'B' | 'C',
  fenster: {
    rolle: null | { reich, reiter: 'vig' | 'karte', vignette: 'liste' | <Nummer> },
    info:  null | { art: 'route'|'ort'|'kontakt'|'zh'|'zhhafen'|'zhhintergrund'|'orbis'|'strasse'|'strassen', id }
                | { art: 'netzlinie'|'netzort', netz, id } | { art: 'netzquellen' }
                | { art: 'text', id, zurueck: { art, id } | null },
    waren: null | 'handel' | 'zh',
    modal: null | 'hilfe' | 'lehrer'
  },
  zeichnung: [ { id, art: 'stift' | 'marker', fest, a, p: [lng, lat, lng, lat, …] }, … ]   // Leuchtstift der Lehrkraft
}
```

**Schnittstelle** (`window.ChronoGlobe`):

| Funktion | Zweck |
|---|---|
| `getState()` | aktueller Zustand (Kopie) |
| `setState(teil, opt)` | eigene Bedienung: ruft `applyState(teil, { quelle: 'lokal', … })` auf |
| `applyState(teil, opt)` | Teilzustand anwenden; `opt.quelle` ist `'lokal'`, `'lehrer'` oder `'tafelbild'`, `opt.dauer` die Dauer des Kameraflugs in ms |
| `abonnieren(fn)` | `fn(quelle)` nach jeder Änderung |
| `setzeRechte(fn)` | `fn(recht)` → `true`, wenn diese Bedienung gerade erlaubt ist (Schülerrechte) |

**Regeln:**
- Alle Menü-Handler, Tastenkürzel, der Zeitregler und die Fokus-Knöpfe laufen über `setState`.
- Interne Funktionen melden Änderungen selbst an die Abonnenten (`zustandGemeldet`): `setYear`, Fenster öffnen/schließen, Reiterwechsel, Vignettenwechsel.
- Kamerabewegungen durch Ziehen oder Zoomen melden sich nicht. Die Lehreransicht fragt `getState().kamera` deshalb im Takt der Senderate ab.
- Nicht Teil des Zustands, weil gerätebezogen:
  - Standort-Pin, eingeklapptes Menü, Infoband und Zeitleiste,
  - Antworten in Quizfragen.
- Regressionstest: `tests/test_regression.py`.
  - Spielt eine feste Klickfolge ab und vergleicht nach jedem Schritt Ebenen, Fenster, Schalter und Jahr mit `tests/regression_baseline.json`.
  - Der Ausgangszustand wurde vor dem Umbau mit dem alten Code aufgenommen.

## Live-Sessions (`js/session.js`, `sql/schema.sql`)

### Ablauf

1. **Session starten** (Startseite):
   - `create_session(tafelbild_id)` liefert Code, Lehrer-Token und Kanal.
   - Das Token speichert nur dieser Browser (`localStorage: chronoglobe.sessions`); in der Datenbank steht nur sein SHA-256-Hash.
   - Angezeigt werden Code, Link, QR-Code und Lehrer-Schlüssel.
2. **Lehreransicht** (`rolle=lehrer`):
   - `teacher_snapshot` prüft das Token. Fehlt es, wird der Lehrer-Schlüssel abgefragt.
   - Ein gespeicherter Zustand wird übernommen (Fortsetzen nach Reload).
   - Jede Änderung sendet die Lehreransicht gedrosselt (Standard 3 Updates/s, `SYNC_RATE` in `js/config.js`) per `teacher_update_state`. Die Datenbank speichert den Zustand und verteilt ihn über `realtime.send`.
3. **Schüleransicht** (`rolle=schueler`):
   - `get_session_public` liefert Zustand, Rechte und Kanal; Nachzügler und Reload bekommen so sofort den aktuellen Stand.
   - Danach Abo des privaten Kanals `cg:<kanal-uuid>` und eine leere Presence-Meldung für die Teilnehmerzahl.
4. **Rückfall:** Ohne Realtime-Verbindung fragt die Schüleransicht alle 3 s `get_session_public` ab. Neu verbunden wird automatisch. Eine Statusanzeige zeigt „live“, „verbinde …“ bzw. „Abfrage“.
5. **Ende:**
   - „Session sperren“: neue Beitritte werden abgewiesen (`is_open`); wer schon verbunden ist, bleibt.
   - „Session beenden“ sendet `beendet` und löscht sofort.
   - Vergessene Sessions löscht `cleanup_old_sessions` nach 30 Tagen (`sql/cron.sql`).

### Nachrichten im Kanal

| Ereignis | Inhalt | Wirkung bei Schüler:innen |
|---|---|---|
| `state` | Zustand, seq | folgen, soweit nicht selbst abgewichen |
| `fokus` | Zustand, seq | Kamera für alle, auch bei „selbst bedienen“ |
| `zurueck` | Zustand, seq | „Alle zurück zu meiner Ansicht“: alles wie bei der Lehrkraft |
| `rechte` | Rechte, `fenster_mitsenden` | Rechte sofort anwenden |
| `offen` | `is_open` | nur Information |
| `beendet` | – | Hinweis „Session beendet“, Kanal schließen |

### Leuchtstift der Lehrkraft

- Nur in der Lehreransicht: `session.js` ruft `ChronoGlobe.stift()` auf; die Leiste erscheint oben in der Mitte.
- Werkzeuge: dünner Stift, breiter durchscheinender Marker, Radierer (einzelne Striche). Ziehen zeichnet, das Mausrad zoomt weiter.
- Gezeichnetes ist zunächst **vorläufig**:
  - „Stehen lassen“ macht es zur festen Beschriftung (`fest: true`).
  - „Wegwischen“, Esc oder das Schließen des Stifts entfernen das Vorläufige.
  - „Alles löschen“ entfernt auch Feststehendes (mit Rückfrage).
- Die Striche liegen in Längen- und Breitengraden (2 Nachkommastellen) und drehen mit dem Globus; die Rückseite wird ausgeblendet. `a` ist der Kameraabstand beim Zeichnen; die Strichbreite wächst beim Heranzoomen mit.
- Die Zeichnung gehört zum Zustand (`zeichnung`) und gilt wie die Filter immer für alle, auch bei „selbst bedienen“. Höchstens 3000 Punkte, damit der Zustand unter der Grenze von 64 KB in `teacher_update_state` bleibt.
- Gezeichnet wird auf einer eigenen Fläche über dem Globus (`.stift-flaeche`, `STIFT` in `js/app.js`); solange der Stift an ist, nehmen Beschriftungen keine Klicks an.

### Schülerrechte

| Recht | „Lehreransicht“ | „selbst bedienen“ |
|---|---|---|
| `zeit` (Zeitriegel) | Jahr folgt der Lehrkraft; Schieber, Abspielen, ±10 und Pfeiltasten gesperrt | eigenes Jahr; nach dem ersten Abweichen folgt das Jahr nicht mehr |
| `globus` (drehen/zoomen) | Kamera folgt, Steuerung aus | eigene Kamera nach dem ersten Ziehen; Fokus-Knöpfe gelten trotzdem |
| `reiche` (Schriftrolle) | nur die Schriftrolle der Lehrkraft | eigene Schriftrollen, nur lokal |
| `routen` (Routen, Orte, Gesandtschaften, Texte, Warenübersicht) | nur Fenster der Lehrkraft | eigene Fenster, nur lokal |

- Filter wirken immer für alle: Ansicht, Reiche, Ebenen, Handel, Straßen, Zheng He, Niveau, Leuchtstift-Zeichnung.
- Öffnet oder schließt die Lehrkraft ein Fenster und ist „Fenster mitsenden“ an, passiert das bei allen, auch bei „selbst bedienen“.
- Die Lehrerhinweise werden nie mitgesendet.
- Sobald Schüler:innen abweichen, erscheint „Zur Lehreransicht zurück“.

**Umsetzung der Sperren:**
- `DARF(recht)` in `js/app.js` sperrt eigene Eingaben in `setYear`, `togglePlay`, `openMap`, allen Infokarten und der Warenübersicht.
- Zustände, die von der Lehrkraft kommen (`quelle: 'lehrer'`), sind davon ausgenommen.

### Sicherheitsmodell

- Im Browser steht nur der Publishable Key. `cg_sessions` ist für `anon` und `authenticated` gesperrt. Lesen und Schreiben laufen ausschließlich über `SECURITY DEFINER`-RPCs.
- Schreiben darf nur, wer das Lehrer-Token kennt (`cg_lehrer` vergleicht den Hash).
- **Realtime:**
  - Kanäle sind privat (`private: true`; im Dashboard „Allow public access“ aus).
  - Die RLS-Richtlinie auf `realtime.messages` erlaubt `select` (Broadcast und Presence) für Topics `cg:<kanal>` offener Sessions.
  - `insert` ist nur für Presence erlaubt. Eine Broadcast-Senderichtlinie gibt es nicht; Broadcasts entstehen nur in der Datenbank (`realtime.send` in den RPCs).
  - Damit kann kein Gerät, auch kein manipuliertes, falsche Zustände an die Klasse senden.
- **Kanalname:** `cg:` plus eine zufällige UUID. Er wird erst nach Eingabe des Codes bekannt.
- **Rückfall B:** Darf die Rolle `anon` einen privaten Kanal in einem Projekt nicht abonnieren, meldet sich das Gerät einmalig anonym an (Supabase „Anonymous Sign-ins“, ohne Name und E-Mail) und versucht es erneut. Klappt auch das nicht, bleibt die Abfrage per RPC. Siehe `docs/SETUP.md`.
- **Keine personenbezogenen Daten:** Schüler-Geräte schreiben nichts in die Datenbank. Die Presence-Meldung ist ein leeres Objekt unter einem zufälligen Schlüssel; die Lehrkraft sieht nur die Zahl.
- **Mengen:** Der Free-Plan erlaubt 100 Realtime-Nachrichten/s, gezählt je Empfänger. 3 Updates/s reichen deshalb für etwa 30 Geräte. Die Kamera wird bei Schüler:innen zwischen den Updates geglättet.

## Laden, Geräteprofil und Offline-Betrieb

### Geräteprofil (`GERAET` in `js/app.js`)

Beim Start wird eine Detailstufe bestimmt. Sie gehört zum Gerät, nicht zum Unterrichtszustand, und steht deshalb nicht in `getState`.

| Stufe | Wann | Wirkung |
|---|---|---|
| `niedrig` | Smartphone (grober Zeiger, kurze Seite < 600 px), Datensparmodus, 2G/3G, ≤ 2 GB Arbeitsspeicher | 4k-Texturen, Kacheln bis Stufe 7, kein Sternenhimmel, kein Relief, Pixeldichte ≤ 1,5 |
| `mittel` | Tablet, ≤ 4 GB Arbeitsspeicher | 8k-Texturen (wenn die Grafik sie kann), Pixeldichte ≤ 2 |
| `hoch` | Laptop/PC | alles; ausgeschaltete Ebenen werden nach dem Start im Hintergrund vorgeladen |

Erzwingen mit `app.html?detail=niedrig|mittel|hoch`; das Gerät merkt sich die Wahl (`localStorage` `cg.detail`), `?detail=auto` setzt zurück. Das CSS kann über `html[data-detail]` darauf reagieren.

„Bewegung reduzieren“ (Systemeinstellung) schaltet die automatische Drehung und die Kameraflüge ab. `state.rotate` bleibt dabei unverändert. Ein Klick auf „Drehen“ geht vor.

### Ebenen bei Bedarf (`NACHLADEN` in `js/app.js`)

Römerstraßen, ORBIS, Han-Seidenstraße und Limes werden nicht mehr beim Start geladen. Sie kommen, sobald die Ebene eingeschaltet oder ein zugehöriges Infofenster geöffnet wird (auch über `applyState` in Live-Sessions). Bis dahin sind `STRASSEN`, `ORBIS`, `HANSEIDE` und `LIMES` `null`; alle Zeichenfunktionen kommen damit zurecht. Nach dem Laden zeichnet `setYear(state.year)` mit geleerten Schlüsseln neu. Die Netze (`data/netze/`) liefen schon vorher so.

Eine neue große Ebene gehört in `NACHLADEN` (Schlüssel, Datei, `noetig()`, `fertig(d)`) und in die Zuordnung am Anfang von `infoOeffnen`.

### Versionsangaben (`tools/version_setzen.py`, `js/version.js`)

GitHub Pages lässt Dateien 10 Minuten im Browser-Cache. Damit nach einem Deploy kein Browser alte Skripte mit neuen Daten mischt:

- Skripte und Stylesheets in den HTML-Seiten tragen `?v=<Inhalts-Hash>`.
- `js/version.js` enthält die Hashes aller per `fetch` geladenen Dateien. `cgUrl('data/reiche.json')` hängt den passenden Hash an.
- **Vor jedem Commit:** `python tools/version_setzen.py`. Die CI prüft das mit `--pruefen`. Optionaler Hook: `git config core.hooksPath tools/hooks`.

### Service Worker (`sw.js`, `js/offline.js`)

- Angemeldet nur über https (GitHub Pages). Lokal und in Tests nur mit `?sw=an`; `?sw=aus` meldet ab und leert die Caches.
- HTML: zuerst Netz, sonst Cache. Kacheln: zuerst Cache. Alles andere: sofort aus dem Cache, im Hintergrund erneuern.
- Beim Installieren wird nur geladen, was der Start braucht. „Für den Unterricht offline speichern“ (Fußzeile der Startseite) lädt alle Dateien aus `js/version.js` (ohne Kacheln).
- Fremde Server (Supabase) laufen nie über den Service Worker.

### Content-Security-Policy (`js/csp.js`)

Erstes Skript im `<head>` jeder Seite. Es setzt die Richtlinie als Meta-Element (GitHub Pages kann keine eigenen Kopfzeilen senden):

- Verbindungen nur zur eigenen Adresse. Supabase (`*.supabase.co`) nur auf Session-Seiten (`?session=`) und der Startseite.
- Keine Inline-Skripte und kein `eval`. Neue Skripte gehören in eigene Dateien unter `js/`.
- `style`-Attribute bleiben erlaubt.

`tests/test_csp.py` prüft jede Seite. Die übrigen Browsertests laufen mit `bypass_csp=True`, weil Playwrights `wait_for_function` intern `eval` nutzt.

## Mittelalter, Züge und ehemalige Wege

- **Durchgehendes Mittelalter:** Im freien Modus hat die Zeitleiste keinen Sprung 480–1400 (`MA_DURCHGEHEND`). Dann gilt ein Reich, solange es Gebiete hat (`MITTEL[r]`, wenn ein Gebiet nach 481 endet). Tafelbilder mit eigenem Zeitraum behalten die alte Regel (nur Gebiete ab 1400). Byzanz ist das Reich „rom“ mit `seite: 'o'` nach 480; Karte und Zeitleiste heißen dann „Byzantinisches Reich“.
- **Zusätzliche Reichsdateien:** `data/fruehe_reiche.json` und `data/mittelalter_reiche.json` werden mit `reicheErgaenzen` zusammengeführt (meta, reihen, regionen, ereignisse, schlachten, orte, wanderungen). Ihre Reiche gelten als `frueh` (Tafelbilder blenden sie aus, außer `reiche.verfuegbar` nennt sie); `abschnitt: 'mittelalter'` legt sie im Menü unter „Mittelalter“ ab.
- **Züge:** `DATA.wanderungen` mit `gruppe` (`vw` = Völkerwanderung, `alexander`, `kolonisation`) und optional `spur` (Jahre sichtbar nach der Ankunft). Jede Gruppe hat einen Schalter und steht in `getState().globus`. Die Schalter für Alexander und Kolonisation entstehen nur, wo erlaubt (freier Modus oder Tafelbild nennt sie).
- **Griechische Kolonisation (`KOL` in `js/app.js`, `data/kolonisation.json`):** eigenes Modul, wird erst beim Einschalten geladen. Erreicht die Zeitleiste ein Gründungsjahr, zeichnet ein Schiff die Route live (Feder wie bei Zheng He); bei Sprüngen mit mehr als zwölf neuen Gründungen erscheint alles sofort. Routen bleiben bis 323 v. Chr. sichtbar, frische Gründungen (30 Jahre) kräftiger. Je Mutterstadt-Gruppe schaltbar (`getState().kolonien`). Beim Abspielen wartet die Zeitleiste, bis laufende Fahrten gezeichnet sind. Die Seewege berechnet `build_poleis.py` über Wegpunkte auf See (Dijkstra, Prüfung gegen die Küstenlinie, feste Verbindungen durch Meerengen).
- **Ehemalige Wege:** `STR_OPT.ehemals` („Ehemalige Trassen und Wege“) zeigt neben Römerstraßen auch Handelsrouten, Gesandtschaften, Han-Seidenstraße, Limes, Netze und Themenlinien nach dem Ende ihres Zeitraums gestrichelt (`ehemaligePaths`), jeweils nur für eingeschaltete Ebenen.
- **Spuren der Zeitleiste:** Im freien Modus mit mehr als zwölf Nachbarreichen zunächst eingeklappt; die eigene Wahl (localStorage `tafelbild.lanes`) geht vor.
