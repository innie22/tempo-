-- ============================================================================
-- TEMPO WELLBEING — PRODUCTION-HARDENED SUPABASE DATABASE SCHEMA
-- Features:
-- 1. Strict Least-Privilege PostgreSQL Role Grants (anon vs authenticated)
-- 2. Row Level Security (RLS) on all tables with zero data leaks
-- 3. Search-path hardened SECURITY DEFINER functions (prevents path hijacking)
-- 4. Anti-Self-Promotion triggers (database enforces role & status immutability)
-- 5. Hard Gating: Unapproved volunteers cannot access student inquiries or profiles
-- ============================================================================

-- 1. Enable UUID Extension
create extension if not exists "uuid-ossp";

-- 2. Custom ENUM Types
do $$ begin
    create type user_role as enum ('student', 'volunteer', 'admin');
exception
    when duplicate_object then null;
end $$;

do $$ begin
    create type application_status as enum ('PENDING', 'APPROVED', 'REJECTED', 'SUSPENDED');
exception
    when duplicate_object then null;
end $$;

do $$ begin
    create type ticket_status as enum ('OPEN', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED');
exception
    when duplicate_object then null;
end $$;

-- 3. Public Profiles Table (Tied 1:1 to auth.users)
create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text not null,
    full_name text not null,
    role user_role not null default 'student',
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 4. Student Profiles Table
create table if not exists public.student_profiles (
    user_id uuid primary key references public.profiles(id) on delete cascade,
    university text,
    year_of_study text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 5. Volunteer Profiles & Application Table
create table if not exists public.volunteer_profiles (
    user_id uuid primary key references public.profiles(id) on delete cascade,
    university_or_organization text not null,
    background text not null,
    study_year_or_qualification text not null,
    experience text not null,
    motivation text not null,
    availability text not null,
    ethical_acknowledged boolean not null default false,
    application_status application_status not null default 'PENDING',
    is_online boolean not null default false,
    reviewed_at timestamp with time zone,
    reviewed_by uuid references public.profiles(id),
    review_notes text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 6. Support Requests Table
create table if not exists public.support_requests (
    id uuid primary key default uuid_generate_v4(),
    student_id uuid not null references public.profiles(id) on delete cascade,
    assigned_volunteer_id uuid references public.profiles(id) on delete set null,
    subject text not null,
    category text not null,
    urgency text not null default 'Medium',
    status ticket_status not null default 'OPEN',
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 7. Support Messages Table
create table if not exists public.support_messages (
    id uuid primary key default uuid_generate_v4(),
    request_id uuid not null references public.support_requests(id) on delete cascade,
    sender_id uuid not null references public.profiles(id) on delete cascade,
    content text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- ============================================================================
-- SECURITY DEFINER HELPER FUNCTIONS (HARDENED SEARCH_PATH)
-- ============================================================================

-- Check if current authenticated user has 'admin' role
create or replace function public.is_admin()
returns boolean as $$
begin
    return exists (
        select 1 from public.profiles
        where id = auth.uid() and role = 'admin'
    );
end;
$$ language plpgsql security definer stable set search_path = public, pg_temp;

-- Check if current authenticated user is an APPROVED volunteer
create or replace function public.is_approved_volunteer()
returns boolean as $$
begin
    return exists (
        select 1 from public.profiles p
        join public.volunteer_profiles v on v.user_id = p.id
        where p.id = auth.uid() 
          and p.role = 'volunteer' 
          and v.application_status = 'APPROVED'
    );
end;
$$ language plpgsql security definer stable set search_path = public, pg_temp;

-- ============================================================================
-- ANTI-PRIVILEGE-ESCALATION TRIGGERS
-- ============================================================================

-- Trigger 1: Handle new user creation upon signup in auth.users
create or replace function public.handle_new_user()
returns trigger as $$
declare
    assigned_role user_role := 'student';
    user_full_name text;
begin
    -- Strictly reject self-promotion to admin in metadata!
    if (new.raw_user_meta_data->>'role') = 'volunteer' then
        assigned_role := 'volunteer';
    else
        assigned_role := 'student';
    end if;

    user_full_name := coalesce(new.raw_user_meta_data->>'full_name', 'Tempo User');

    -- Insert into public profiles
    insert into public.profiles (id, email, full_name, role)
    values (new.id, new.email, user_full_name, assigned_role);

    -- Insert role-specific profile record
    if assigned_role = 'student' then
        insert into public.student_profiles (user_id, university, year_of_study)
        values (
            new.id,
            new.raw_user_meta_data->>'university',
            new.raw_user_meta_data->>'year_of_study'
        );
    elsif assigned_role = 'volunteer' then
        insert into public.volunteer_profiles (
            user_id,
            university_or_organization,
            background,
            study_year_or_qualification,
            experience,
            motivation,
            availability,
            ethical_acknowledged,
            application_status
        )
        values (
            new.id,
            coalesce(new.raw_user_meta_data->>'university_or_organization', 'Not specified'),
            coalesce(new.raw_user_meta_data->>'background', 'Other'),
            coalesce(new.raw_user_meta_data->>'study_year_or_qualification', 'Not specified'),
            coalesce(new.raw_user_meta_data->>'experience', ''),
            coalesce(new.raw_user_meta_data->>'motivation', ''),
            coalesce(new.raw_user_meta_data->>'availability', 'Flexible'),
            coalesce((new.raw_user_meta_data->>'ethical_acknowledged')::boolean, true),
            'PENDING' -- Always hardcode initial status to PENDING
        );
    end if;

    return new;
end;
$$ language plpgsql security definer set search_path = public, pg_temp;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();

-- Trigger 2: Prevent users from updating their own role or ID on profiles
create or replace function public.protect_profile_fields()
returns trigger as $$
begin
    -- Non-admins cannot alter their role
    if (OLD.role is distinct from NEW.role) and not public.is_admin() then
        raise exception 'Security violation: User role cannot be modified by non-administrators.';
    end if;

    -- User ID cannot be modified
    if (OLD.id is distinct from NEW.id) then
        raise exception 'Security violation: Profile ID is immutable.';
    end if;

    NEW.updated_at := timezone('utc'::text, now());
    return NEW;
end;
$$ language plpgsql security definer set search_path = public, pg_temp;

drop trigger if exists trg_protect_profile_fields on public.profiles;
create trigger trg_protect_profile_fields
    before update on public.profiles
    for each row execute function public.protect_profile_fields();

-- Trigger 3: Prevent volunteers from self-approving or modifying review metadata
create or replace function public.protect_volunteer_status()
returns trigger as $$
begin
    -- Non-admins cannot alter application status
    if (OLD.application_status is distinct from NEW.application_status) and not public.is_admin() then
        raise exception 'Security violation: Volunteer application status can only be modified by administrators.';
    end if;

    -- Non-admins cannot alter review metadata (reviewed_at, reviewed_by, review_notes)
    if ((OLD.reviewed_at is distinct from NEW.reviewed_at) 
        or (OLD.reviewed_by is distinct from NEW.reviewed_by)
        or (OLD.review_notes is distinct from NEW.review_notes)) and not public.is_admin() then
        raise exception 'Security violation: Application review metadata can only be set by administrators.';
    end if;

    -- Non-approved volunteers cannot set is_online to true
    if (NEW.is_online = true) and (OLD.application_status != 'APPROVED') then
        raise exception 'Security violation: Only approved volunteers can broadcast online availability.';
    end if;

    NEW.updated_at := timezone('utc'::text, now());
    return NEW;
end;
$$ language plpgsql security definer set search_path = public, pg_temp;

drop trigger if exists trg_protect_volunteer_status on public.volunteer_profiles;
create trigger trg_protect_volunteer_status
    before update on public.volunteer_profiles
    for each row execute function public.protect_volunteer_status();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

alter table public.profiles enable row level security;
alter table public.student_profiles enable row level security;
alter table public.volunteer_profiles enable row level security;
alter table public.support_requests enable row level security;
alter table public.support_messages enable row level security;

-- PROFILES POLICIES
create policy "Users can view their own profile" 
    on public.profiles for select 
    using (auth.uid() = id);

create policy "Admins can view all profiles"
    on public.profiles for select
    using (public.is_admin());

create policy "Approved volunteers can view profiles of assigned students"
    on public.profiles for select
    using (
        public.is_approved_volunteer()
        and exists (
            select 1 from public.support_requests r
            where r.assigned_volunteer_id = auth.uid()
              and r.student_id = public.profiles.id
        )
    );

create policy "Users can update their own profile details" 
    on public.profiles for update 
    using (auth.uid() = id)
    with check (auth.uid() = id);

create policy "Admins can update any profile"
    on public.profiles for update
    using (public.is_admin())
    with check (public.is_admin());

-- STUDENT PROFILES POLICIES
create policy "Students can view their own student profile" 
    on public.student_profiles for select 
    using (auth.uid() = user_id);

create policy "Admins can view all student profiles"
    on public.student_profiles for select
    using (public.is_admin());

create policy "Approved volunteers can view assigned student profile"
    on public.student_profiles for select
    using (
        public.is_approved_volunteer()
        and exists (
            select 1 from public.support_requests r
            where r.assigned_volunteer_id = auth.uid()
              and r.student_id = public.student_profiles.user_id
        )
    );

create policy "Students can update their own student profile" 
    on public.student_profiles for update 
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

create policy "Admins can update any student profile"
    on public.student_profiles for update
    using (public.is_admin())
    with check (public.is_admin());

-- VOLUNTEER PROFILES POLICIES
create policy "Volunteers can view their own application" 
    on public.volunteer_profiles for select 
    using (auth.uid() = user_id);

create policy "Admins can view all volunteer applications" 
    on public.volunteer_profiles for select 
    using (public.is_admin());

create policy "Approved volunteers can toggle online availability" 
    on public.volunteer_profiles for update 
    using (auth.uid() = user_id and public.is_approved_volunteer())
    with check (auth.uid() = user_id and public.is_approved_volunteer());

create policy "Admins can manage any volunteer profile" 
    on public.volunteer_profiles for update 
    using (public.is_admin())
    with check (public.is_admin());

-- SUPPORT REQUESTS POLICIES
create policy "Students can view their own support requests" 
    on public.support_requests for select 
    using (auth.uid() = student_id);

create policy "Approved volunteers can view open and assigned requests" 
    on public.support_requests for select 
    using (
        public.is_approved_volunteer() 
        and (status = 'OPEN' or assigned_volunteer_id = auth.uid())
    );

create policy "Admins can view all support requests" 
    on public.support_requests for select 
    using (public.is_admin());

create policy "Students can create their own support requests" 
    on public.support_requests for insert 
    with check (auth.uid() = student_id);

create policy "Students can update their own support requests (e.g. resolve)" 
    on public.support_requests for update 
    using (auth.uid() = student_id)
    with check (auth.uid() = student_id);

create policy "Approved volunteers can claim or update assigned requests" 
    on public.support_requests for update 
    using (
        public.is_approved_volunteer() 
        and (status = 'OPEN' or assigned_volunteer_id = auth.uid())
    )
    with check (
        public.is_approved_volunteer()
        and (assigned_volunteer_id = auth.uid() or assigned_volunteer_id is null)
    );

create policy "Admins can manage any support request" 
    on public.support_requests for update 
    using (public.is_admin())
    with check (public.is_admin());

-- SUPPORT MESSAGES POLICIES
create policy "Conversation participants can view messages" 
    on public.support_messages for select 
    using (
        exists (
            select 1 from public.support_requests r
            where r.id = request_id
              and (
                  r.student_id = auth.uid() 
                  or (public.is_approved_volunteer() and r.assigned_volunteer_id = auth.uid())
                  or public.is_admin()
              )
        )
    );

create policy "Conversation participants can send messages" 
    on public.support_messages for insert 
    with check (
        auth.uid() = sender_id
        and exists (
            select 1 from public.support_requests r
            where r.id = request_id
              and (
                  r.student_id = auth.uid() 
                  or (public.is_approved_volunteer() and r.assigned_volunteer_id = auth.uid())
                  or public.is_admin()
              )
        )
    );

-- ============================================================================
-- LEAST-PRIVILEGE POSTGRESQL GRANTS
-- Do not rely on RLS alone. Revoke broad defaults and grant strictly what each
-- role requires.
-- ============================================================================

-- Step 1: Revoke all default public privileges on all tables, sequences, functions
revoke all on all tables in schema public from public, anon, authenticated;
revoke all on all sequences in schema public from public, anon, authenticated;
revoke all on all functions in schema public from public, anon, authenticated;

-- Step 2: Grant schema usage
grant usage on schema public to anon, authenticated;

-- Step 3: 'anon' role grants:
-- Zero table access! Anonymous clients register through auth.signUp()
-- and cannot query or mutate any public tables directly.

-- Step 4: 'authenticated' role grants:
-- Specific table privileges subject to Row Level Security:
grant select, update on public.profiles to authenticated;
grant select, update on public.student_profiles to authenticated;
grant select, update on public.volunteer_profiles to authenticated;
grant select, insert, update on public.support_requests to authenticated;
grant select, insert on public.support_messages to authenticated;

-- Grant sequence usage if any sequences exist
grant usage, select on all sequences in schema public to authenticated;

-- Step 5: Function execution grants:
grant execute on function public.is_admin() to authenticated;
grant execute on function public.is_approved_volunteer() to authenticated;

-- Explicitly revoke execute on internal triggers from client roles:
revoke execute on function public.handle_new_user() from public, anon, authenticated;
revoke execute on function public.protect_profile_fields() from public, anon, authenticated;
revoke execute on function public.protect_volunteer_status() from public, anon, authenticated;

-- ============================================================================
-- INITIAL ADMIN CREATION INSTRUCTION:
-- To elevate a user to admin, run from Supabase SQL Editor:
-- update public.profiles set role = 'admin' where email = 'your-admin@email.com';
-- ============================================================================
