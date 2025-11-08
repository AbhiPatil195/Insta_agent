-- Enable pgvector and create core tables
create extension if not exists vector;
create extension if not exists pgcrypto;

create table if not exists users (
  id bigint primary key,
  ig_username text,
  language text,
  attributes jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create table if not exists threads (
  id uuid default gen_random_uuid() primary key,
  user_id bigint references users(id),
  last_intent text,
  status text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists messages (
  id uuid default gen_random_uuid() primary key,
  thread_id uuid references threads(id),
  role text check (role in ('user','assistant','system')),
  text text,
  meta jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create table if not exists memory_embeddings (
  id uuid default gen_random_uuid() primary key,
  user_id bigint references users(id),
  content text,
  embedding vector(384),
  kind text,
  created_at timestamptz default now()
);

create table if not exists analytics (
  id uuid default gen_random_uuid() primary key,
  thread_id uuid references threads(id),
  latency_ms int,
  model text,
  confidence float,
  feedback jsonb,
  created_at timestamptz default now()
);
