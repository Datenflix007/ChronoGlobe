-- ChronoGlobe · einmal zusätzlich zu sql/schema.sql im Supabase SQL Editor ausführen.
-- Aktiviert die tägliche Bereinigung vergessener Sessions um 03:40 UTC.
-- Der Job löscht ausschließlich Sessions, die älter als 30 Tage sind.
create extension if not exists pg_cron;

do $$
declare existing_job bigint;
begin
  select jobid into existing_job from cron.job where jobname = 'chronoglobe-cleanup' limit 1;
  if existing_job is not null then perform cron.unschedule(existing_job); end if;
  perform cron.schedule('chronoglobe-cleanup', '40 3 * * *', $cron$select public.cleanup_old_sessions();$cron$);
end $$;

-- Nur falls der Rückfall „Anonymous Sign-ins“ eingeschaltet ist (docs/SETUP.md, Abschnitt Rückfall B):
-- anonyme Auth-Einträge ohne Daten nach einem Tag entfernen. Sonst diesen Block weglassen.
-- do $$
-- declare existing_job bigint;
-- begin
--   select jobid into existing_job from cron.job where jobname = 'chronoglobe-anon-cleanup' limit 1;
--   if existing_job is not null then perform cron.unschedule(existing_job); end if;
--   perform cron.schedule('chronoglobe-anon-cleanup', '50 3 * * *',
--     $cron$delete from auth.users where is_anonymous and created_at < now() - interval '1 day';$cron$);
-- end $$;
