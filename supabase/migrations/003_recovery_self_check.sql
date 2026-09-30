-- ============================================================================
-- TEMPO WELLBEING — ADDITIVE RECOVERY SELF-CHECK PERSISTENCE MIGRATION
-- File: supabase/migrations/003_recovery_self_check.sql
--
-- Architecture:
-- 1. self_check_trackers: User-defined trackers with categories & check methods
-- 2. self_check_daily_checkins: At most one check-in per user per calendar day
-- 3. self_check_observations: Nuanced observations (unanswered, skipped, answered)
-- 4. Row Level Security (RLS) guaranteeing user data privacy and ownership
-- ============================================================================

-- Ensure uuid extension is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. SELF_CHECK_TRACKERS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.self_check_trackers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('stress_sign', 'supportive', 'neutral')),
    check_method TEXT NOT NULL CHECK (check_method IN ('yes_no', 'scale', 'percentage', 'quantity')),
    scale_min INT DEFAULT 1,
    scale_max INT DEFAULT 5,
    scale_min_label TEXT DEFAULT 'Very low',
    scale_max_label TEXT DEFAULT 'Very high',
    quantity_unit TEXT DEFAULT '',
    direction TEXT CHECK (direction IN ('higher_concerning', 'higher_better', 'neutral')),
    pattern_notices_enabled BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_self_check_trackers_user ON public.self_check_trackers(user_id, is_archived);

-- ----------------------------------------------------------------------------
-- 2. SELF_CHECK_DAILY_CHECKINS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.self_check_daily_checkins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    checkin_date DATE NOT NULL,
    overall_note TEXT,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_user_checkin_date UNIQUE (user_id, checkin_date)
);

CREATE INDEX IF NOT EXISTS idx_self_check_checkins_user_date ON public.self_check_daily_checkins(user_id, checkin_date DESC);

-- ----------------------------------------------------------------------------
-- 3. SELF_CHECK_OBSERVATIONS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.self_check_observations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    checkin_id UUID NOT NULL REFERENCES public.self_check_daily_checkins(id) ON DELETE CASCADE,
    tracker_id UUID NOT NULL REFERENCES public.self_check_trackers(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('unanswered', 'skipped', 'answered')),
    value JSONB,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_checkin_tracker UNIQUE (checkin_id, tracker_id)
);

CREATE INDEX IF NOT EXISTS idx_self_check_obs_checkin ON public.self_check_observations(checkin_id);

-- ----------------------------------------------------------------------------
-- 4. ROW LEVEL SECURITY (RLS) POLICIES
-- ----------------------------------------------------------------------------
ALTER TABLE public.self_check_trackers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.self_check_daily_checkins ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.self_check_observations ENABLE ROW LEVEL SECURITY;

-- self_check_trackers policies
CREATE POLICY "Users can view their own trackers"
    ON public.self_check_trackers FOR SELECT
    USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can insert their own trackers"
    ON public.self_check_trackers FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own trackers"
    ON public.self_check_trackers FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own trackers"
    ON public.self_check_trackers FOR DELETE
    USING (auth.uid() = user_id);

-- self_check_daily_checkins policies
CREATE POLICY "Users can view their own daily checkins"
    ON public.self_check_daily_checkins FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own daily checkins"
    ON public.self_check_daily_checkins FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own daily checkins"
    ON public.self_check_daily_checkins FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own daily checkins"
    ON public.self_check_daily_checkins FOR DELETE
    USING (auth.uid() = user_id);

-- self_check_observations policies
CREATE POLICY "Users can view their own observations"
    ON public.self_check_observations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.self_check_daily_checkins c
            WHERE c.id = self_check_observations.checkin_id
            AND c.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert their own observations"
    ON public.self_check_observations FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.self_check_daily_checkins c
            WHERE c.id = self_check_observations.checkin_id
            AND c.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update their own observations"
    ON public.self_check_observations FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.self_check_daily_checkins c
            WHERE c.id = self_check_observations.checkin_id
            AND c.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.self_check_daily_checkins c
            WHERE c.id = self_check_observations.checkin_id
            AND c.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete their own observations"
    ON public.self_check_observations FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.self_check_daily_checkins c
            WHERE c.id = self_check_observations.checkin_id
            AND c.user_id = auth.uid()
        )
    );
