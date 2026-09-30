-- ============================================================================
-- TEMPO WELLBEING — ADDITIVE WEEKLY REFLECTIONS MIGRATION (PHASE 5)
-- File: migrations/006_weekly_reflections.sql
--
-- Architecture:
-- 1. Create weekly_reflections table for durable user self-reflections
-- 2. Enforce one reflection per user per week (UNIQUE user_id, week_start)
-- 3. Row Level Security (RLS) guaranteeing strict per-user privacy
-- ============================================================================

-- Ensure uuid extension is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. WEEKLY REFLECTIONS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.weekly_reflections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    comparison TEXT CHECK (comparison IN ('much_harder', 'little_harder', 'same', 'little_better', 'much_better', 'unsure')),
    difference_items JSONB DEFAULT '[]'::jsonb,
    custom_difference_items JSONB DEFAULT '[]'::jsonb,
    user_note TEXT,
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_user_week_reflection UNIQUE (user_id, week_start)
);

CREATE INDEX IF NOT EXISTS idx_weekly_reflections_user ON public.weekly_reflections(user_id);
CREATE INDEX IF NOT EXISTS idx_weekly_reflections_week ON public.weekly_reflections(week_start);

-- ----------------------------------------------------------------------------
-- 2. ROW LEVEL SECURITY (RLS) POLICIES
-- ----------------------------------------------------------------------------
ALTER TABLE public.weekly_reflections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own weekly reflections"
    ON public.weekly_reflections FOR SELECT
    USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can insert their own weekly reflections"
    ON public.weekly_reflections FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own weekly reflections"
    ON public.weekly_reflections FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own weekly reflections"
    ON public.weekly_reflections FOR DELETE
    USING (auth.uid() = user_id);
