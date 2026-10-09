-- Run this in Supabase SQL Editor (https://supabase.com/dashboard/project/_/sql/new)
-- Creates the table that stores per-user progress synced across devices.

create table if not exists public.progress (
  user_key   text primary key,
  marks      jsonb not null default '{}'::jsonb,
  known      jsonb not null default '[]'::jsonb,
  unknown    jsonb not null default '[]'::jsonb,
  best       integer not null default 0,
  theme      text,
  recall     boolean,
  updated_at timestamptz not null default now()
);

-- Allow the anonymous key to read/write (personal app; protect by choosing an unguessable sync key)
alter table public.progress enable row level security;
drop policy if exists "allow all anon" on public.progress;
create policy "allow all anon" on public.progress
  for all
  to anon, authenticated
  using (true)
  with check (true);
