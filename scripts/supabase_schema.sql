-- ============================================================
-- meetAI Supabase Schema
-- Run this in Supabase SQL Editor
-- ============================================================

-- 1. profiles (auth.users 확장)
create table if not exists public.profiles (
  id         uuid primary key references auth.users(id) on delete cascade,
  username   text unique,
  created_at timestamptz default now()
);

alter table public.profiles enable row level security;

create policy "profiles_select_own" on public.profiles
  for select using (auth.uid() = id);

create policy "profiles_update_own" on public.profiles
  for update using (auth.uid() = id);

-- 회원가입 시 profiles 자동 생성 트리거
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, username)
  values (new.id, new.raw_user_meta_data ->> 'username');
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();


-- 2. analysis_history (분석 기록)
create table if not exists public.analysis_history (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references auth.users(id) on delete cascade,
  mode            text not null check (mode in ('interview', 'presentation')),
  transcript      text,
  overall_score   float,
  rubric_score    float,
  feedback        jsonb default '{}',
  improved_answer text,
  video_path      text,
  created_at      timestamptz default now()
);

alter table public.analysis_history enable row level security;

create policy "history_select_own" on public.analysis_history
  for select using (auth.uid() = user_id);

create policy "history_insert_own" on public.analysis_history
  for insert with check (auth.uid() = user_id);

create policy "history_update_own" on public.analysis_history
  for update using (auth.uid() = user_id);

create policy "history_delete_own" on public.analysis_history
  for delete using (auth.uid() = user_id);

create index if not exists analysis_history_user_created
  on public.analysis_history (user_id, created_at desc);


-- 3. Storage 버킷 (Supabase 대시보드 Storage 탭에서 직접 생성하거나 아래 SQL 실행)
insert into storage.buckets (id, name, public)
values ('meetai-videos', 'meetai-videos', false)
on conflict (id) do nothing;

-- 버킷 RLS: 자신의 파일만 접근
create policy "videos_select_own" on storage.objects
  for select using (bucket_id = 'meetai-videos' and auth.uid()::text = (storage.foldername(name))[1]);

create policy "videos_insert_own" on storage.objects
  for insert with check (bucket_id = 'meetai-videos' and auth.uid()::text = (storage.foldername(name))[1]);

create policy "videos_delete_own" on storage.objects
  for delete using (bucket_id = 'meetai-videos' and auth.uid()::text = (storage.foldername(name))[1]);
