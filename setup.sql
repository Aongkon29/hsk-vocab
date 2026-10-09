-- Run this in Supabase SQL Editor (https://supabase.com/dashboard/project/_/sql/new)
-- 1) Progress table (per authenticated user)
create table if not exists public.progress (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  marks      jsonb not null default '{}'::jsonb,
  known      jsonb not null default '[]'::jsonb,
  unknown    jsonb not null default '[]'::jsonb,
  best       integer not null default 0,
  theme      text,
  recall     boolean,
  rev_list   jsonb not null default '[]'::jsonb,
  rev_idx    integer not null default 0,
  rev_known  jsonb not null default '[]'::jsonb,
  rev_unknown jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now()
);

-- 2) RLS: users can only touch their own row
alter table public.progress enable row level security;
drop policy if exists "own row" on public.progress;
create policy "own row" on public.progress
  for all
  to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- 3) IMPORTANT: In Supabase Dashboard → Authentication → Providers → Email,
--    turn OFF "Confirm email" so signup works without email verification.
--    (We use a fake email address derived from your username.)
