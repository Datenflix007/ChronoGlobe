# Live-Sessions einrichten (Supabase)

Freies Nutzen und Tafelbilder brauchen nichts davon. Supabase ist nur für Live-Sessions nötig. Für ChronoGlobe wird ein **eigenes, neues Supabase-Projekt** verwendet, nicht das der Mindmap.

## 1. Projekt anlegen

1. Auf https://supabase.com ein neues Projekt erstellen, z. B. `chronoglobe`. Der kostenlose Plan reicht für eine Klasse (siehe Abschnitt 6).
2. Ein starkes Datenbankpasswort vergeben und sicher aufbewahren.
3. Warten, bis das Projekt bereit ist.

## 2. Datenbank einrichten

1. Im Dashboard **SQL Editor** öffnen.
2. Den gesamten Inhalt von `sql/schema.sql` einfügen und **Run** ausführen. Das Skript darf mehrfach laufen.
   - **Nach einem Update von ChronoGlobe** das Skript erneut ausführen. Es ergänzt fehlende Spalten und Funktionen, z. B. `schueler_ui` für „Schüleransicht anpassen“. Bestehende Sessions bleiben erhalten.
   - Es legt die Tabelle `cg_sessions` an.
   - Es legt die RPCs an: `create_session`, `get_session_public`, `teacher_snapshot`, `teacher_update_state`, `teacher_update_rechte`, `set_session_open`, `delete_session`, `cleanup_old_sessions`.
   - Es legt die Realtime-Richtlinien an.
3. Danach `sql/cron.sql` ausführen. Das richtet die tägliche Löschung von Sessions ein, die älter als 30 Tage sind.

## 3. Realtime auf private Kanäle stellen

Dashboard → **Realtime** → **Settings** → **Allow public access** ausschalten.

Erst dann gelten die Richtlinien aus `sql/schema.sql`:
- Geräte dürfen den Kanal einer Session nur lesen.
- Senden kann nur die Datenbank, auf Anweisung der Lehrkraft per RPC.

## 4. Schlüssel eintragen

1. Dashboard → **Connect** bzw. **Project Settings → API Keys**.
2. Die **Project URL** (`https://xxxx.supabase.co`) und den **Publishable Key** (`sb_publishable_…`) kopieren.
3. In `js/config.js` eintragen:

   ```js
   window.APP_CONFIG = {
     SUPABASE_URL: "https://xxxx.supabase.co",
     SUPABASE_PUBLISHABLE_KEY: "sb_publishable_…",
     SYNC_RATE: 3,
     REALTIME_GRENZE: 100
   };
   ```

**Niemals einen Secret Key (`sb_secret_…`) oder den `service_role`-Key eintragen.** Der Publishable Key darf öffentlich sein, weil die Tabelle gesperrt ist und nur die RPCs erreichbar sind.

## 5. Prüfen

Die automatischen Tests (`tests/test_session.py`) laufen über den lokalen Übertragungsweg und prüfen Supabase nicht. Nach der Einrichtung deshalb einmal von Hand prüfen:

1. `index.html` öffnen. Die Bereiche „Session erstellen“ und „Session beitreten“ zeigen kein „Supabase nicht eingerichtet“ mehr.
2. Eine Session starten und „Als Lehrkraft öffnen“.
3. In einem zweiten Browser bzw. am Handy den QR-Code scannen. Die Statusanzeige oben muss **„live“** zeigen, nicht „Abfrage alle 3 s“.
4. Bei der Lehrkraft:
   - die Zeitleiste ziehen; bei Schüler:innen läuft sie mit;
   - die Teilnehmerzahl steigt.
5. **Gegenprobe Sicherheit:** In der Browser-Konsole des Schülergeräts versuchen, selbst zu senden. Das darf nichts bewirken:

   ```js
   const ch = db.channel('cg:' + '<kanal-uuid aus get_session_public>', { config: { private: true } });
   ch.subscribe(s => s === 'SUBSCRIBED' && ch.send({ type: 'broadcast', event: 'state', payload: { state: { jahr: 1 } } }));
   ```

6. Session beenden. Die Schüleransicht zeigt „Session beendet“.

**Rückfall B (Anonymous Sign-ins):**
- Zeigt die Statusanzeige dauerhaft „Abfrage alle 3 s“, darf die Rolle `anon` in diesem Projekt keinen privaten Kanal abonnieren. Die Sessions funktionieren dann trotzdem, nur mit Verzögerung.
- Für Live-Betrieb: Dashboard → **Authentication → Sign In / Providers → Anonymous Sign-ins** einschalten.
  - Jedes Gerät meldet sich dann ohne Name und E-Mail anonym an und abonniert erneut.
  - Die anonymen Einträge räumt der auskommentierte Block in `sql/cron.sql` nach einem Tag auf. Diesen Block dann ausführen.
- Eine Captcha-Pflicht für anonyme Anmeldungen ist sinnvoll (Supabase-Empfehlung gegen Missbrauch).

## 6. Grenzen des kostenlosen Plans

- **Realtime:** 100 Nachrichten pro Sekunde (jede Zustellung zählt einzeln) und 200 gleichzeitige Verbindungen.
  - Der Sendetakt passt sich der Zahl der Geräte an (`docs/ARCHITEKTUR.md`, Abschnitt „Mengen“). Eine Klasse mit 28 Tablets bleibt so bei etwa 60 Nachrichten/s.
  - Ab etwa 60 Geräten reicht der Free-Plan nicht mehr sicher.
  - Mit dem Pro-Plan (500 Nachrichten/s) `REALTIME_GRENZE: 500` und bei Bedarf eine höhere `SYNC_RATE` eintragen.
- **Monatskontingent:** 2 Mio. Realtime-Nachrichten. Eine Doppelstunde mit 28 Geräten braucht grob 30 000–50 000.
- **Pausieren:** Projekte ohne Nutzung werden nach einiger Zeit pausiert. Vor dem Unterricht kurz im Dashboard prüfen.

## 7. Datenschutz

- Gespeichert werden je Session nur:
  - Code und Kanal-ID,
  - Tafelbild-ID,
  - Zustand der Lehreransicht und Schülerrechte,
  - der Hash des Lehrer-Tokens,
  - Zeitstempel.
- Keine Namen, keine Konten, keine IP-Adressen in eigenen Tabellen.
- Schüler-Geräte schreiben nichts in die Datenbank. Die Anwesenheit ist eine leere Meldung; die Lehrkraft sieht nur die Zahl.
- „Session beenden“ löscht sofort, sonst löscht die Bereinigung nach 30 Tagen.
- Supabase verarbeitet technisch Verbindungsdaten. Die Region des Projekts (z. B. Frankfurt, `eu-central-1`) beim Anlegen wählen und im Datenschutzhinweis der Schule erwähnen.
