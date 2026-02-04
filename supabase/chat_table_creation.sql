create extension if not exists "pgcrypto";
create table public.chat_messages (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null,
    topic_id uuid,

    role text not null
        check (role in ('system', 'user', 'assistant')),

    content text not null,

    created_at timestamptz not null default now()
);
alter table public.chat_messages
add constraint chat_messages_user_fk
foreign key (user_id)
references auth.users (id)
on delete cascade;

alter table public.chat_messages
add constraint chat_messages_topic_fk
foreign key (topic_id)
references public.documents (id)
on delete cascade;
create index chat_messages_user_topic_idx
on public.chat_messages (user_id, topic_id);

create index chat_messages_created_at_idx
on public.chat_messages (created_at);
alter table public.chat_messages
enable row level security;
create policy "Users can read own messages"
on public.chat_messages
for select
using (auth.uid() = user_id);

create policy "Users can insert own messages"
on public.chat_messages
for insert
with check (auth.uid() = user_id);

create policy "Users can delete own messages"
on public.chat_messages
for delete
using (auth.uid() = user_id);
