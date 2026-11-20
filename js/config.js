// ChronoGlobe · Supabase-Konfiguration für Live-Sessions (Einrichtung: docs/SETUP.md).
// Nur die Project URL und den PUBLISHABLE Key (sb_publishable_…) eintragen – NIEMALS einen Secret Key.
// Der Publishable Key darf im Browser stehen, weil alle Tabellen gesperrt sind und nur die RPCs aus sql/schema.sql
// erreichbar sind. Ohne Eintrag funktionieren freier Modus und Tafelbilder weiter; nur die Sessions sind aus.
window.APP_CONFIG = {
  SUPABASE_URL: "https://sgwqrfvsocuyiyhezosn.supabase.co",
  SUPABASE_PUBLISHABLE_KEY: "sb_publishable_Lzuvm8sD-R5C4yQlxXYuFg_La25UMdj",
  // Live-Updates je Sekunde für Zeitriegel und Kamera (Free-Plan: 100 Realtime-Nachrichten/s, gezählt je Empfänger;
  // 3/s reicht bei ~30 Geräten). Mit dem Pro-Plan kann der Wert erhöht werden.
  SYNC_RATE: 3
};
