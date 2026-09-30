-- ============================================================================
-- TEMPO WELLBEING — ADDITIVE SELF-CHECK HISTORY & PATTERNS MIGRATION
-- File: migrations/005_self_check_history_patterns.sql
--
-- Architecture:
-- 1. Add linked_note_item_ids to self_check_trackers
-- 2. Add self_check_notice_state table for dismiss / snooze tracking
-- 3. Row Level Security (RLS) guaranteeing user privacy
-- ============================================================================

-- Ensure uuid extension is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. EXTEND TRACKERS WITH RECOVERY NOTE LINKING
-- ----------------------------------------------------------------------------
ALTER TABLE public.self_check_trackers
ADD COLUMN IF NOT EXISTS linked_note_item_ids JSONB DEFAULT '[]'::jsonb;

-- ----------------------------------------------------------------------------
-- 2. NOTICE STATE (DISMISS / REMIND LATER)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.self_check_notice_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    tracker_id UUID REFERENCES public.self_check_trackers(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('active', 'dismissed', 'snoozed')),
    snoozed_until TIMESTAMPTZ,
    dismissed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_user_tracker_notice UNIQUE (user_id, tracker_id)
);

CREATE INDEX IF NOT EXISTS idx_self_check_notices_user ON public.self_check_notice_state(user_id);

-- ----------------------------------------------------------------------------
-- 3. ROW LEVEL SECURITY (RLS) POLICIES
-- ----------------------------------------------------------------------------
ALTER TABLE public.self_check_notice_state ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own notice states"
    ON public.self_check_notice_state FOR SELECT
    USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can insert their own notice states"
    ON public.self_check_notice_state FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own notice states"
    ON public.self_check_notice_state FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own notice states"
    ON public.self_check_notice_state FOR DELETE
    USING (auth.uid() = user_id);
