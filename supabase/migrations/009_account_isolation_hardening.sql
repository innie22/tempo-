-- ============================================================================
-- TEMPO WELLBEING — ACCOUNT ISOLATION & RLS SECURITY HARDENING
-- File: migrations/009_account_isolation_hardening.sql
-- 
-- Objectives:
-- 1. Remove dangerous 'OR user_id IS NULL' from private user tables:
--    - recovery_notes
--    - self_check_notice_state
--    - weekly_reflections
--    - tool_notes
--    - ucheck_assessment_drafts
-- 2. Enforce cross-table ownership validation:
--    - plan_items: verify that task_id belongs to auth.uid()
--    - self_check_observations: verify that tracker_id belongs to auth.uid() or is a system template
-- 3. Enforce user_id immutability and ownership consistency
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. PLAN_ITEMS: Prevent attaching another user's task to a plan
-- ----------------------------------------------------------------------------
drop policy if exists "Users can insert their own plan items" on public.plan_items;
create policy "Users can insert their own plan items"
    on public.plan_items for insert
    with check (
        exists (
            select 1 from public.plans p
            where p.id = plan_id and p.user_id = auth.uid()
        )
        and exists (
            select 1 from public.tasks t
            where t.id = task_id and t.user_id = auth.uid()
        )
    );

drop policy if exists "Users can update their own plan items" on public.plan_items;
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
        and exists (
            select 1 from public.tasks t
            where t.id = task_id and t.user_id = auth.uid()
        )
    );

-- ----------------------------------------------------------------------------
-- 2. RECOVERY_NOTES: Remove 'OR user_id IS NULL'
-- ----------------------------------------------------------------------------
drop policy if exists "Users can view their own recovery note" on public.recovery_notes;
create policy "Users can view their own recovery note"
    on public.recovery_notes for select
    using (auth.uid() = user_id);

-- ----------------------------------------------------------------------------
-- 3. SELF_CHECK_NOTICE_STATE: Remove 'OR user_id IS NULL'
-- ----------------------------------------------------------------------------
drop policy if exists "Users can view their own notice states" on public.self_check_notice_state;
create policy "Users can view their own notice states"
    on public.self_check_notice_state for select
    using (auth.uid() = user_id);

-- ----------------------------------------------------------------------------
-- 4. WEEKLY_REFLECTIONS: Remove 'OR user_id IS NULL'
-- ----------------------------------------------------------------------------
drop policy if exists "Users can view their own weekly reflections" on public.weekly_reflections;
create policy "Users can view their own weekly reflections"
    on public.weekly_reflections for select
    using (auth.uid() = user_id);

-- ----------------------------------------------------------------------------
-- 5. TOOL_NOTES: Remove 'OR user_id IS NULL'
-- ----------------------------------------------------------------------------
drop policy if exists "Users can view their own tool notes" on public.tool_notes;
create policy "Users can view their own tool notes"
    on public.tool_notes for select
    using (auth.uid() = user_id);

-- ----------------------------------------------------------------------------
-- 6. UCHECK_ASSESSMENT_DRAFTS: Remove 'OR user_id IS NULL'
-- ----------------------------------------------------------------------------
drop policy if exists "Users can view their own ucheck drafts" on public.ucheck_assessment_drafts;
create policy "Users can view their own ucheck drafts"
    on public.ucheck_assessment_drafts for select
    using (auth.uid() = user_id);

-- ----------------------------------------------------------------------------
-- 7. SELF_CHECK_OBSERVATIONS: Prevent linking observations to another user's private tracker
-- ----------------------------------------------------------------------------
drop policy if exists "Users can insert their own observations" on public.self_check_observations;
create policy "Users can insert their own observations"
    on public.self_check_observations for insert
    with check (
        exists (
            select 1 from public.self_check_daily_checkins c
            where c.id = self_check_observations.checkin_id
              and c.user_id = auth.uid()
        )
        and exists (
            select 1 from public.self_check_trackers t
            where t.id = self_check_observations.tracker_id
              and (t.user_id = auth.uid() or t.user_id is null)
        )
    );

drop policy if exists "Users can update their own observations" on public.self_check_observations;
create policy "Users can update their own observations"
    on public.self_check_observations for update
    using (
        exists (
            select 1 from public.self_check_daily_checkins c
            where c.id = self_check_observations.checkin_id
              and c.user_id = auth.uid()
        )
    )
    with check (
        exists (
            select 1 from public.self_check_daily_checkins c
            where c.id = self_check_observations.checkin_id
              and c.user_id = auth.uid()
        )
        and exists (
            select 1 from public.self_check_trackers t
            where t.id = self_check_observations.tracker_id
              and (t.user_id = auth.uid() or t.user_id is null)
        )
    );
