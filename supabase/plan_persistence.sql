-- ============================================================================
-- TEMPO WELLBEING — ADDITIVE PLAN & SHARED TASK PERSISTENCE MIGRATION
-- File: supabase/plan_persistence.sql
-- 
-- Architecture:
-- 1. Shared Plans table (supports Emergency, Recovery, Unclear plans)
-- 2. Shared Tasks table (tasks exist independently of plans, single identity)
-- 3. Plan Items table (relationship layer: plan-specific ordering & scheduling)
-- 4. Subtasks table (belong directly to shared tasks, used across plans & Focus Zone)
-- 5. Strict Row Level Security (RLS) ensuring students access ONLY their own data
-- ============================================================================

-- Ensure uuid-ossp extension is enabled
create extension if not exists "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. PLANS TABLE
-- Represents a structured action plan created by a student.
-- ----------------------------------------------------------------------------
create table if not exists public.plans (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    plan_type text not null default 'emergency',
    status text not null default 'draft',
    title text not null default 'Emergency Plan',
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
    constraint chk_plan_type check (plan_type in ('emergency', 'recovery', 'unclear', 'general')),
    constraint chk_plan_status check (status in ('draft', 'active', 'completed', 'archived'))
);

-- ----------------------------------------------------------------------------
-- 2. TASKS TABLE
-- Represents a student's shared tasks. A task has one durable identity and
-- can be referenced across multiple plans, modes, and Focus Zone.
-- ----------------------------------------------------------------------------
create table if not exists public.tasks (
    id text primary key,
    user_id uuid not null references public.profiles(id) on delete cascade,
    name text not null,
    description text default '',
    has_deadline boolean not null default false,
    deadline_date text,
    deadline_time text,
    importance text default 'High',
    consequence text default 'Big consequences',
    flexibility jsonb not null default '[]'::jsonb,
    duration_minutes integer not null default 60,
    duration_label text default '1h',
    is_unknown_duration boolean not null default false,
    is_long_term boolean not null default false,
    priority_category text not null default 'DO_FIRST',
    execution_status text not null default 'not_started',
    completed boolean not null default false,
    is_in_progress boolean not null default false,
    is_broken_down boolean not null default false,
    already_know_what_to_do boolean not null default false,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
    constraint chk_execution_status check (execution_status in ('not_started', 'in_progress', 'completed'))
);

-- ----------------------------------------------------------------------------
-- 3. PLAN ITEMS TABLE
-- Normalizes the relationship between a plan and a shared task.
-- Stores plan-specific sequence, scheduling, and presentation badges.
-- ----------------------------------------------------------------------------
create table if not exists public.plan_items (
    id uuid primary key default uuid_generate_v4(),
    plan_id uuid not null references public.plans(id) on delete cascade,
    task_id text not null references public.tasks(id) on delete cascade,
    position integer not null default 0,
    scheduled_date text,
    scheduled_day_label text,
    scheduled_start text,
    scheduled_end text,
    start_minutes integer,
    end_minutes integer,
    execution_badge text default 'UP NEXT',
    is_over_capacity boolean not null default false,
    has_deadline_conflict boolean not null default false,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
    constraint uq_plan_task unique (plan_id, task_id)
);

-- ----------------------------------------------------------------------------
-- 4. SUBTASKS TABLE
-- Micro-action steps belonging directly to a shared task.
-- Focus Zone, Step Breakdown, and future Plan Workspace share these records.
-- ----------------------------------------------------------------------------
create table if not exists public.subtasks (
    id text primary key,
    task_id text not null references public.tasks(id) on delete cascade,
    title text not null,
    duration_minutes integer,
    position integer not null default 0,
    completed boolean not null default false,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- ----------------------------------------------------------------------------
-- 5. PERFORMANCE INDEXES
-- ----------------------------------------------------------------------------
create index if not exists idx_plans_user_status on public.plans(user_id, plan_type, status);
create index if not exists idx_tasks_user on public.tasks(user_id);
create index if not exists idx_plan_items_plan_pos on public.plan_items(plan_id, position);
create index if not exists idx_subtasks_task_pos on public.subtasks(task_id, position);

-- ----------------------------------------------------------------------------
-- 6. ROW LEVEL SECURITY (RLS) POLICIES
-- Strict user isolation: students can access ONLY their own data.
-- ----------------------------------------------------------------------------
alter table public.plans enable row level security;
alter table public.tasks enable row level security;
alter table public.plan_items enable row level security;
alter table public.subtasks enable row level security;

-- PLANS Policies
create policy "Users can view their own plans"
    on public.plans for select
    using (auth.uid() = user_id);

create policy "Users can insert their own plans"
    on public.plans for insert
    with check (auth.uid() = user_id);

create policy "Users can update their own plans"
    on public.plans for update
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

create policy "Users can delete their own plans"
    on public.plans for delete
    using (auth.uid() = user_id);

-- TASKS Policies
create policy "Users can view their own tasks"
    on public.tasks for select
    using (auth.uid() = user_id);

create policy "Users can insert their own tasks"
    on public.tasks for insert
    with check (auth.uid() = user_id);

create policy "Users can update their own tasks"
    on public.tasks for update
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

create policy "Users can delete their own tasks"
    on public.tasks for delete
    using (auth.uid() = user_id);

-- PLAN ITEMS Policies (derived ownership through parent plan)
create policy "Users can view their own plan items"
    on public.plan_items for select
    using (
        exists (
            select 1 from public.plans p
            where p.id = plan_id and p.user_id = auth.uid()
        )
    );

create policy "Users can insert their own plan items"
    on public.plan_items for insert
    with check (
        exists (
            select 1 from public.plans p
            where p.id = plan_id and p.user_id = auth.uid()
        )
    );

create policy "Users can update their own plan items"
    on public.plan_items for update
    using (
        exists (
            select 1 from public.plans p
            where p.id = plan_id and p.user_id = auth.uid()
        )
    )
    with check (
        exists (
            select 1 from public.plans p
            where p.id = plan_id and p.user_id = auth.uid()
        )
    );

create policy "Users can delete their own plan items"
    on public.plan_items for delete
    using (
        exists (
            select 1 from public.plans p
            where p.id = plan_id and p.user_id = auth.uid()
        )
    );

-- SUBTASKS Policies (derived ownership through parent task)
create policy "Users can view their own subtasks"
    on public.subtasks for select
    using (
        exists (
            select 1 from public.tasks t
            where t.id = task_id and t.user_id = auth.uid()
        )
    );

create policy "Users can insert their own subtasks"
    on public.subtasks for insert
    with check (
        exists (
            select 1 from public.tasks t
            where t.id = task_id and t.user_id = auth.uid()
        )
    );

create policy "Users can update their own subtasks"
    on public.subtasks for update
    using (
        exists (
            select 1 from public.tasks t
            where t.id = task_id and t.user_id = auth.uid()
        )
    )
    with check (
        exists (
            select 1 from public.tasks t
            where t.id = task_id and t.user_id = auth.uid()
        )
    );

create policy "Users can delete their own subtasks"
    on public.subtasks for delete
    using (
        exists (
            select 1 from public.tasks t
            where t.id = task_id and t.user_id = auth.uid()
        )
    );

-- ----------------------------------------------------------------------------
-- 7. LEAST-PRIVILEGE ROLE GRANTS
-- Grants table privileges to authenticated clients subject to RLS.
-- Anonymous users are not granted table access.
-- ----------------------------------------------------------------------------
grant select, insert, update, delete on public.plans to authenticated;
grant select, insert, update, delete on public.tasks to authenticated;
grant select, insert, update, delete on public.plan_items to authenticated;
grant select, insert, update, delete on public.subtasks to authenticated;
