// Supabase-Client aus js/config.js (wie im Mindmap-Projekt). Wird nur in Session-Seiten nachgeladen (js/session.js).
(function () {
  var cfg = window.APP_CONFIG || {};
  var ok = cfg.SUPABASE_URL && cfg.SUPABASE_URL.indexOf('DEIN-PROJEKT') < 0 &&
    cfg.SUPABASE_PUBLISHABLE_KEY && cfg.SUPABASE_PUBLISHABLE_KEY.indexOf('DEIN_KEY') < 0;
  window.APP_CONFIGURED = !!ok;
  window.db = ok ? supabase.createClient(cfg.SUPABASE_URL, cfg.SUPABASE_PUBLISHABLE_KEY,
    { auth: { persistSession: false, autoRefreshToken: true, detectSessionInUrl: false } }) : null;
})();
