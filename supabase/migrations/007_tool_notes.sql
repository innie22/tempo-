-- ============================================================================
-- TEMPO WELLBEING – ADDITIVE TOOL NOTES PERSISTENCE MIGRATION
-- File: supabase/migrations/007_tool_notes.sql
--
-- Architecture:
-- 1. tool_notes table supporting both Day Notes and Task Notes
-- 2. User isolation via user_id matching auth.uid()
-- 3. Strict Row Level Security (RLS) guaranteeing student privacy and ownership
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS public.tool_notes (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('day', 'task')),
    category TEXT NOT NULL DEFAULT 'day',
    date TEXT,
    task_id TEXT,
    task_name TEXT,
    title TEXT,
    content TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_tool_notes_user_type ON public.tool_notes(user_id, type);
CREATE INDEX IF NOT EXISTS idx_tool_notes_date ON public.tool_notes(user_id, date);
CREATE INDEX IF NOT EXISTS idx_tool_notes_task ON public.tool_notes(user_id, task_id);

ALTER TABLE public.tool_notes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own tool notes"
    ON public.tool_notes FOR SELECT
    USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can insert their own tool notes"
    ON public.tool_notes FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own tool notes"
    ON public.tool_notes FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own tool notes"
    ON public.tool_notes FOR DELETE
    USING (auth.uid() = user_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON public.tool_notes TO authenticated;
