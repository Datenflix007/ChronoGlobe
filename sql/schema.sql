-- ChronoGlobe · Live-Sessions · Supabase-Schema
-- Im Supabase SQL Editor vollständig ausführen. Mehrfaches Ausführen ist unschädlich (idempotent).
-- Anleitung: docs/SETUP.md · Ablauf und Sicherheitsmodell: docs/ARCHITEKTUR.md
--
-- Sicherheitsmodell (wie im Mindmap-Projekt):
--   * Im Browser steht nur der Publishable Key. Die Tabelle ist für anon/authenticated gesperrt.
--   * Zugriff nur über SECURITY-DEFINER-RPCs. Schreiben darf nur die Lehrkraft (Lehrer-Token, in der DB nur als Hash).
--   * Live-Updates: Die RPC der Lehrkraft speichert den Zustand und sendet ihn per realtime.send an den privaten
--     Kanal 'cg:<kanal>'. Schüler-Geräte dürfen diesen Kanal nur LESEN (Richtlinie unten). Eine Senderichtlinie für
--     Broadcast gibt es nicht: Weder Schüler noch der Browser der Lehrkraft können direkt in den Kanal schreiben.
--   * Anwesenheit (Teilnehmerzahl): Clients dürfen eine leere Presence-Meldung senden. Es werden keine Namen und
--     keine personenbezogenen Daten übertragen oder gespeichert.
--   * Keine Konten, keine Namen. Sessions werden beim Beenden sofort und sonst nach 30 Tagen gelöscht (sql/cron.sql).

create extension if not exists pgcrypto with schema extensions;

create table if not exists public.cg_sessions (
  id uuid primary key default extensions.gen_random_uuid(),
  code text not null unique,
  tafelbild_id text not null check (tafelbild_id ~ '^[a-z0-9][a-z0-9-]{0,59}$'),
  lehrer_token_hash text not null,
  kanal uuid not null default extensions.gen_random_uuid(),
  state jsonb not null default '{}'::jsonb,
  rechte jsonb not null default '{"zeit":"lehrer","globus":"lehrer","reiche":"lehrer","routen":"lehrer"}'::jsonb,
  fenster_mitsenden boolean not null default true,
  is_open boolean not null default true,
  seq bigint not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
-- Spalten nachrüsten, falls eine ältere Fassung der Tabelle existiert
alter table public.cg_sessions add column if not exists kanal uuid not null default extensions.gen_random_uuid();
alter table public.cg_sessions add column if not exists seq bigint not null default 0;
-- Schüleransicht (welche Bedienelemente die Schüler:innen sehen); null = Standard bzw. Voreinstellung des Tafelbilds
alter table public.cg_sessions add column if not exists schueler_ui jsonb;
create index if not exists cg_sessions_created_idx on public.cg_sessions(created_at);
create unique index if not exists cg_sessions_kanal_idx on public.cg_sessions(kanal);

alter table public.cg_sessions enable row level security;
revoke all on public.cg_sessions from anon, authenticated;

-- ---------- Hilfsfunktionen (nicht aus dem Browser aufrufbar) ----------
create or replace function public.cg_make_code()
returns text language plpgsql security definer set search_path = public, extensions as $$
declare
  alphabet constant text := 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';   -- ohne 0/O und 1/I
  c text; b bytea; i int;
begin
  loop
    b := extensions.gen_random_bytes(6); c := '';
    for i in 0..5 loop c := c || substr(alphabet, (get_byte(b, i) % 32) + 1, 1); end loop;
    exit when not exists (select 1 from public.cg_sessions where code = c);
  end loop;
  return c;
end $$;

create or replace function public.cg_hash(p_token text)
returns text language sql immutable set search_path = public, extensions as $$
  select encode(extensions.digest(coalesce(p_token, ''), 'sha256'), 'hex');
$$;

-- Sitzung der Lehrkraft holen (Code + Token geprüft), sonst Fehler
create or replace function public.cg_lehrer(p_code text, p_token text)
returns public.cg_sessions language plpgsql security definer set search_path = public, extensions as $$
declare s public.cg_sessions;
begin
  select * into s from public.cg_sessions where code = upper(btrim(p_code));
  if not found or s.lehrer_token_hash <> public.cg_hash(p_token) then
    raise exception 'Lehrer-Zugriff verweigert' using errcode = '42501';
  end if;
  return s;
end $$;

-- Zustand prüfen: Objekt, höchstens 64 KB
create or replace function public.cg_state_ok(p_state jsonb)
returns boolean language sql immutable as $$
  select p_state is not null and jsonb_typeof(p_state) = 'object' and pg_column_size(p_state) <= 65536;
$$;

-- Schülerrechte prüfen: genau die vier Schlüssel mit 'lehrer' oder 'selbst'
create or replace function public.cg_rechte_ok(p_rechte jsonb)
returns boolean language sql immutable as $$
  select jsonb_typeof(p_rechte) = 'object'
     and (select count(*) from jsonb_object_keys(p_rechte)) = 4
     and p_rechte ?& array['zeit', 'globus', 'reiche', 'routen']
     and not exists (select 1 from jsonb_each_text(p_rechte) where value not in ('lehrer', 'selbst'));
$$;

-- Schüleransicht prüfen: Objekt, nur bekannte Schlüssel, nur true/false
create or replace function public.cg_schueler_ui_ok(p_ui jsonb)
returns boolean language sql immutable as $$
  select jsonb_typeof(p_ui) = 'object'
     and not exists (select 1 from jsonb_each(p_ui)
                     where key not in ('reiche', 'ebenen', 'suche', 'spuren', 'infokarten') or jsonb_typeof(value) <> 'boolean');
$$;

-- Realtime-Richtlinie: Gehört ein Kanal zu einer bestehenden, offenen Session?
create or replace function public.cg_kanal_offen(p_topic text)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.cg_sessions s where 'cg:' || s.kanal::text = p_topic and s.is_open);
$$;

-- Nachricht an den Session-Kanal (privat)
create or replace function public.cg_senden(s public.cg_sessions, p_event text, p_payload jsonb)
returns void language plpgsql security definer set search_path = public, extensions as $$
begin
  perform realtime.send(p_payload, p_event, 'cg:' || s.kanal::text, true);
exception when others then
  -- Realtime nicht erreichbar (z. B. noch keine Tagespartition): Zustand ist gespeichert, Schüler holen ihn per Abfrage
  raise warning 'ChronoGlobe: realtime.send fehlgeschlagen: %', sqlerrm;
end $$;

-- ---------- RPCs für den Browser ----------
create or replace function public.create_session(p_tafelbild_id text)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare s public.cg_sessions; tok text;
begin
  if p_tafelbild_id is null or p_tafelbild_id !~ '^[a-z0-9][a-z0-9-]{0,59}$' then raise exception 'Ungültige Tafelbild-ID'; end if;
  tok := encode(extensions.gen_random_bytes(24), 'hex');
  insert into public.cg_sessions (code, tafelbild_id, lehrer_token_hash)
  values (public.cg_make_code(), p_tafelbild_id, public.cg_hash(tok))
  returning * into s;
  return jsonb_build_object('code', s.code, 'token', tok, 'kanal', s.kanal, 'tafelbild_id', s.tafelbild_id);
end $$;

-- Öffentlicher Stand für Schüler:innen und Nachzügler (ohne Token-Hash)
create or replace function public.get_session_public(p_code text)
returns jsonb language plpgsql stable security definer set search_path = public as $$
declare s public.cg_sessions;
begin
  select * into s from public.cg_sessions where code = upper(btrim(p_code));
  if not found then return null; end if;
  if not s.is_open then
    return jsonb_build_object('code', s.code, 'tafelbild_id', s.tafelbild_id, 'is_open', false);
  end if;
  return jsonb_build_object('code', s.code, 'tafelbild_id', s.tafelbild_id, 'kanal', s.kanal, 'state', s.state,
    'rechte', s.rechte, 'fenster_mitsenden', s.fenster_mitsenden, 'schueler_ui', s.schueler_ui, 'is_open', s.is_open, 'seq', s.seq);
end $$;

create or replace function public.teacher_snapshot(p_code text, p_token text)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare s public.cg_sessions;
begin
  s := public.cg_lehrer(p_code, p_token);
  return jsonb_build_object('code', s.code, 'tafelbild_id', s.tafelbild_id, 'kanal', s.kanal, 'state', s.state,
    'rechte', s.rechte, 'fenster_mitsenden', s.fenster_mitsenden, 'schueler_ui', s.schueler_ui, 'is_open', s.is_open, 'seq', s.seq,
    'created_at', s.created_at);
end $$;

-- Zustand der Lehrkraft speichern und an alle senden.
-- p_modus: 'state' (normal), 'fokus' (Kamera für alle erzwingen), 'zurueck' („Alle zurück zu meiner Ansicht“)
create or replace function public.teacher_update_state(p_code text, p_token text, p_state jsonb, p_modus text default 'state')
returns bigint language plpgsql security definer set search_path = public, extensions as $$
declare s public.cg_sessions;
begin
  s := public.cg_lehrer(p_code, p_token);
  if not public.cg_state_ok(p_state) then raise exception 'Ungültiger Zustand'; end if;
  if p_modus not in ('state', 'fokus', 'zurueck') then raise exception 'Ungültiger Modus'; end if;
  update public.cg_sessions set state = p_state, seq = seq + 1, updated_at = now() where id = s.id returning * into s;
  perform public.cg_senden(s, p_modus, jsonb_build_object('state', p_state, 'seq', s.seq));
  return s.seq;
end $$;

-- Rechte, „Fenster mitsenden“ und Schüleransicht. p_schueler_ui null = unverändert lassen.
-- Die ältere Fassung ohne p_schueler_ui wird entfernt, damit es keine zwei gleichnamigen Funktionen gibt.
drop function if exists public.teacher_update_rechte(text, text, jsonb, boolean);
create or replace function public.teacher_update_rechte(p_code text, p_token text, p_rechte jsonb, p_fenster_mitsenden boolean,
  p_schueler_ui jsonb default null)
returns void language plpgsql security definer set search_path = public, extensions as $$
declare s public.cg_sessions;
begin
  s := public.cg_lehrer(p_code, p_token);
  if not public.cg_rechte_ok(p_rechte) then raise exception 'Ungültige Rechte'; end if;
  if p_schueler_ui is not null and not public.cg_schueler_ui_ok(p_schueler_ui) then raise exception 'Ungültige Schüleransicht'; end if;
  update public.cg_sessions set rechte = p_rechte, fenster_mitsenden = coalesce(p_fenster_mitsenden, true),
    schueler_ui = coalesce(p_schueler_ui, schueler_ui), updated_at = now()
    where id = s.id returning * into s;
  perform public.cg_senden(s, 'rechte', jsonb_build_object('rechte', s.rechte, 'fenster_mitsenden', s.fenster_mitsenden,
    'schueler_ui', s.schueler_ui));
end $$;

-- Sperren: Niemand kann neu beitreten (Beitritt und Kanalanmeldung prüfen is_open); Verbundene bleiben verbunden.
create or replace function public.set_session_open(p_code text, p_token text, p_is_open boolean)
returns void language plpgsql security definer set search_path = public, extensions as $$
declare s public.cg_sessions;
begin
  s := public.cg_lehrer(p_code, p_token);
  update public.cg_sessions set is_open = coalesce(p_is_open, true), updated_at = now() where id = s.id returning * into s;
  perform public.cg_senden(s, 'offen', jsonb_build_object('is_open', s.is_open));
end $$;

-- Beenden: alle Geräte benachrichtigen, dann sofort löschen
create or replace function public.delete_session(p_code text, p_token text)
returns void language plpgsql security definer set search_path = public, extensions as $$
declare s public.cg_sessions;
begin
  s := public.cg_lehrer(p_code, p_token);
  perform public.cg_senden(s, 'beendet', '{}'::jsonb);
  delete from public.cg_sessions where id = s.id;
end $$;

-- Nur für Supabase Cron (sql/cron.sql), nie für Browserrollen
create or replace function public.cleanup_old_sessions()
returns integer language plpgsql security definer set search_path = public as $$
declare n integer;
begin
  delete from public.cg_sessions where created_at < now() - interval '30 days';
  get diagnostics n = row_count;
  return n;
end $$;

-- ---------- Realtime Authorization (private Kanäle) ----------
-- Voraussetzung im Dashboard: Realtime → Settings → „Allow public access“ AUS (docs/SETUP.md).
-- Lesen (Broadcast und Presence) für alle Geräte mit dem Kanalnamen einer offenen Session.
drop policy if exists "cg: Session-Kanal lesen" on realtime.messages;
create policy "cg: Session-Kanal lesen" on realtime.messages
  for select to anon, authenticated
  using (
    realtime.messages.extension in ('broadcast', 'presence')
    and (select realtime.topic()) like 'cg:%'
    and public.cg_kanal_offen((select realtime.topic()))
  );
-- Senden NUR für Presence (leere Anwesenheitsmeldung für die Teilnehmerzahl). Keine Richtlinie für Broadcast:
-- Broadcasts kommen ausschließlich aus der Datenbank (realtime.send in den RPCs oben).
drop policy if exists "cg: Anwesenheit melden" on realtime.messages;
create policy "cg: Anwesenheit melden" on realtime.messages
  for insert to anon, authenticated
  with check (
    realtime.messages.extension = 'presence'
    and (select realtime.topic()) like 'cg:%'
    and public.cg_kanal_offen((select realtime.topic()))
  );

-- ---------- Rechte ----------
revoke execute on function public.cg_make_code() from public, anon, authenticated;
revoke execute on function public.cg_hash(text) from public, anon, authenticated;
revoke execute on function public.cg_lehrer(text, text) from public, anon, authenticated;
revoke execute on function public.cg_state_ok(jsonb) from public, anon, authenticated;
revoke execute on function public.cg_rechte_ok(jsonb) from public, anon, authenticated;
revoke execute on function public.cg_schueler_ui_ok(jsonb) from public, anon, authenticated;
revoke execute on function public.cg_senden(public.cg_sessions, text, jsonb) from public, anon, authenticated;
revoke execute on function public.cleanup_old_sessions() from public, anon, authenticated;
-- cg_kanal_offen wird in der Realtime-Richtlinie mit der Rolle des Geräts ausgewertet
revoke execute on function public.cg_kanal_offen(text) from public;
grant execute on function public.cg_kanal_offen(text) to anon, authenticated;

grant execute on function public.create_session(text) to anon, authenticated;
grant execute on function public.get_session_public(text) to anon, authenticated;
grant execute on function public.teacher_snapshot(text, text) to anon, authenticated;
grant execute on function public.teacher_update_state(text, text, jsonb, text) to anon, authenticated;
grant execute on function public.teacher_update_rechte(text, text, jsonb, boolean, jsonb) to anon, authenticated;
grant execute on function public.set_session_open(text, text, boolean) to anon, authenticated;
grant execute on function public.delete_session(text, text) to anon, authenticated;

notify pgrst, 'reload schema';
