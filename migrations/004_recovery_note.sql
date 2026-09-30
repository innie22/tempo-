-- ============================================================================
-- TEMPO WELLBEING — ADDITIVE RECOVERY NOTE PERSISTENCE MIGRATION
-- File: migrations/004_recovery_note.sql
--
-- Architecture:
-- 1. recovery_notes: One personal recovery note per user
-- 2. recovery_note_items: Structured items (warning_sign, helper, reminder, support_person)
-- 3. Row Level Security (RLS) guaranteeing student privacy and ownership
-- ============================================================================

-- Ensure uuid extension is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. RECOVERY_NOTES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.recovery_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_user_recovery_note UNIQUE (user_id)
);

CREATE INDEX IF NOT EXISTS idx_recovery_notes_user ON public.recovery_notes(user_id);

-- ----------------------------------------------------------------------------
-- 2. RECOVERY_NOTE_ITEMS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.recovery_note_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recovery_note_id UUID NOT NULL REFERENCES public.recovery_notes(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('warning_sign', 'helper', 'reminder', 'support_person')),
    text TEXT NOT NULL,
    source TEXT DEFAULT 'custom',
    source_ref TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    order_index INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_recovery_note_items_note ON public.recovery_note_items(recovery_note_id, type);

-- ----------------------------------------------------------------------------
-- 3. ROW LEVEL SECURITY (RLS) POLICIES
-- ----------------------------------------------------------------------------
ALTER TABLE public.recovery_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recovery_note_items ENABLE ROW LEVEL SECURITY;

-- recovery_notes policies
CREATE POLICY "Users can view their own recovery note"
    ON public.recovery_notes FOR SELECT
    USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can insert their own recovery note"
    ON public.recovery_notes FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own recovery note"
    ON public.recovery_notes FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own recovery note"
    ON public.recovery_notes FOR DELETE
    USING (auth.uid() = user_id);

-- recovery_note_items policies
CREATE POLICY "Users can view their own recovery note items"
    ON public.recovery_note_items FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.recovery_notes n
            WHERE n.id = recovery_note_items.recovery_note_id
            AND n.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert their own recovery note items"
    ON public.recovery_note_items FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.recovery_notes n
            WHERE n.id = recovery_note_items.recovery_note_id
            AND n.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update their own recovery note items"
    ON public.recovery_note_items FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.recovery_notes n
            WHERE n.id = recovery_note_items.recovery_note_id
            AND n.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.recovery_notes n
            WHERE n.id = recovery_note_items.recovery_note_id
            AND n.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete their own recovery note items"
    ON public.recovery_note_items FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.recovery_notes n
            WHERE n.id = recovery_note_items.recovery_note_id
            AND n.user_id = auth.uid()
        )
    );
