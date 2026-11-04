-- ============================================================================
-- TEMPO WELLBEING – UCHECK ASSESSMENT DRAFTS & PROGRESS AUTO-SAVE MIGRATION
-- File: migrations/008_ucheck_assessment_drafts.sql
--
-- Architecture:
-- 1. ucheck_assessment_drafts table supporting full draft persistence across Steps 1-4
-- 2. User isolation via user_id matching auth.uid()
-- 3. Strict Row Level Security (RLS) guaranteeing student privacy and ownership
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS public.ucheck_assessment_drafts (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    parent_version_id TEXT,
    status TEXT NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed')),
    current_stage INTEGER NOT NULL DEFAULT 1 CHECK (current_stage BETWEEN 1 AND 5),
    concerns JSONB NOT NULL DEFAULT '[]'::jsonb,
    custom_concerns JSONB NOT NULL DEFAULT '[]'::jsonb,
    top_concerns JSONB NOT NULL DEFAULT '[]'::jsonb,
    feelings_by_concern JSONB NOT NULL DEFAULT '{}'::jsonb,
    custom_feelings_by_concern JSONB NOT NULL DEFAULT '{}'::jsonb,
    noticed_changes JSONB NOT NULL DEFAULT '[]'::jsonb,
    custom_changes JSONB NOT NULL DEFAULT '[]'::jsonb,
    impact_level TEXT NOT NULL DEFAULT '',
    needs JSONB NOT NULL DEFAULT '[]'::jsonb,
    need_details JSONB NOT NULL DEFAULT '{}'::jsonb,
    custom_need TEXT NOT NULL DEFAULT '',
    primary_need TEXT NOT NULL DEFAULT '',
    chosen_direction TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_ucheck_drafts_user_status ON public.ucheck_assessment_drafts(user_id, status);
CREATE INDEX IF NOT EXISTS idx_ucheck_drafts_user_updated ON public.ucheck_assessment_drafts(user_id, updated_at DESC);

ALTER TABLE public.ucheck_assessment_drafts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own ucheck drafts"
    ON public.ucheck_assessment_drafts FOR SELECT
    USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can insert their own ucheck drafts"
    ON public.ucheck_assessment_drafts FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own ucheck drafts"
    ON public.ucheck_assessment_drafts FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own ucheck drafts"
    ON public.ucheck_assessment_drafts FOR DELETE
    USING (auth.uid() = user_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON public.ucheck_assessment_drafts TO authenticated;
