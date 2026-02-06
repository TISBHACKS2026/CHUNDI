create table if not exists public.allowed_sources (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    domain text not null,

    created_at timestamp with time zone
        default now(),
    constraint allowed_sources_domain_format
        check (
            domain ~ '^[a-z0-9.-]+\.[a-z]{2,}$'
        ),
    constraint allowed_sources_unique_user_domain
        unique (user_id, domain)
);

create index if not exists idx_allowed_sources_user_id
    on public.allowed_sources(user_id);

alter table public.allowed_sources
enable row level security;

create policy "read own allowed sources"
on public.allowed_sources
for select
using (auth.uid() = user_id);
create policy "insert own allowed sources"
on public.allowed_sources
for insert
with check (auth.uid() = user_id);
create policy "delete own allowed sources"
on public.allowed_sources
for delete
using (auth.uid() = user_id);
