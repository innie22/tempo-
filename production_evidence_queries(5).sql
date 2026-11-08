-- ============================================================================
-- TEMPO WELLBEING — PRODUCTION EVIDENCE COLLECTION QUERIES (STRICTLY READ-ONLY)
-- File: production_evidence_queries(5).sql
-- Target Migrations: 008_ucheck_assessment_drafts.sql & 009_account_isolation_hardening.sql
-- Execution Mode: STRICTLY READ-ONLY (No DDL, no DML, no DO blocks, no temporary tables)
--
-- STATUS: NOT READY FOR EXECUTION — AWAITING ACTUAL PRODUCTION EVIDENCE AND HUMAN APPROVAL.
--
-- INSTRUCTIONS FOR DATABASE ADMINISTRATOR:
-- 1. Open Supabase Dashboard -> SQL Editor.
-- 2. Execute each Block below sequentially.
-- 3. Precondition for Block 3: Always run Block 1 first. Only run a table-specific
--    NULL count query in Block 3 if Block 1 confirms that the table and its required
--    user_id column physically exist on remote.
-- 4. Copy the raw result sets (table grid, CSV, or JSON) back to the engineering team.
-- 5. No SQL in this file modifies database state, rows, tables, schemas, or policies.
--
-- METADATA VISIBILITY & ROLE PERMISSION NOTICE:
--   Information schema and catalog visibility depends on the database role executing
--   the query. Standard SQL information_schema views restrict rows to objects the active
--   role has permissions to view. Missing visible metadata (e.g. referencing auth.users)
--   requires review and verification against pg_catalog, NOT automatic conclusions of absence.
-- ============================================================================


-- ============================================================================
-- BLOCK 1: TABLE AND COLUMN EXISTENCE AUDIT
-- Purpose: Verify physical presence of all 11 core tables and check all columns
--          directly referenced in Migration 008 and Migration 009 subqueries.
-- Catalogs: information_schema.tables, information_schema.columns
--
-- Technical Evaluation Rules:
--   - Missing Required Table: HARD STOP. Migrations cannot proceed.
--   - Missing Required Column: HARD STOP. Subqueries or policies will fail.
--   - Complete Schema Compatibility: Do not assume checking only user_id or a subset
--     of columns proves full schema compatibility. All expected columns must be verified.
--   - Column Nullability Note on ucheck_assessment_drafts:
--     Migration 008 explicitly defines user_id as nullable:
--     `user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE`
--     Therefore, user_id_is_nullable = 'YES' is EXPECTED for ucheck_assessment_drafts
--     and must NOT be classified as a schema mismatch.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- BLOCK 1A: 11-Core Table Existence Inventory
-- Expected: 11 rows showing table presence.
-- ----------------------------------------------------------------------------
SELECT 
    target.table_name,
    CASE 
        WHEN t.table_name IS NOT NULL THEN 'EXISTS' 
        ELSE 'MISSING (HARD STOP if referenced by migration)' 
    END AS table_status
FROM (
    VALUES 
        ('plans'),
        ('tasks'),
        ('plan_items'),
        ('recovery_notes'),
        ('self_check_notice_state'),
        ('weekly_reflections'),
        ('tool_notes'),
        ('self_check_trackers'),
        ('self_check_daily_checkins'),
        ('self_check_observations'),
        ('ucheck_assessment_drafts')
) AS target(table_name)
LEFT JOIN information_schema.tables t 
    ON t.table_schema = 'public' AND t.table_name = target.table_name
ORDER BY target.table_name;


-- ----------------------------------------------------------------------------
-- BLOCK 1B: Migration 008 & 009 Referenced Column Audit
-- Inspects every column directly referenced by Migration 009 subqueries, as well
-- as ALL 22 columns required by Migration 008 in ucheck_assessment_drafts.
-- ----------------------------------------------------------------------------
SELECT 
    target.table_name,
    CASE 
        WHEN t.table_name IS NOT NULL THEN 'EXISTS' 
        ELSE 'MISSING TABLE' 
    END AS table_status,
    target.column_name,
    CASE 
        WHEN c.column_name IS NOT NULL THEN 'PRESENT' 
        ELSE 'MISSING COLUMN (HARD STOP)' 
    END AS column_status,
    COALESCE(c.data_type, 'N/A') AS data_type,
    COALESCE(c.is_nullable, 'N/A') AS is_nullable,
    COALESCE(c.column_default, 'NONE') AS column_default,
    target.purpose_in_migrations
FROM (
    VALUES 
        -- plans: referenced by plan_items RLS subquery
        ('plans', 'id', 'Referenced by plan_items RLS subquery (p.id = plan_id)'),
        ('plans', 'user_id', 'Referenced by plan_items RLS subquery (p.user_id = auth.uid())'),

        -- tasks: referenced by plan_items RLS subquery
        ('tasks', 'id', 'Referenced by plan_items RLS subquery (t.id = task_id)'),
        ('tasks', 'user_id', 'Referenced by plan_items RLS subquery (t.user_id = auth.uid())'),

        -- plan_items: affected table in migration 009
        ('plan_items', 'plan_id', 'Foreign key linked to plans.id in RLS check'),
        ('plan_items', 'task_id', 'Foreign key linked to tasks.id in RLS check'),

        -- Private single-user tables affected by removal of OR user_id IS NULL
        ('recovery_notes', 'id', 'Primary key'),
        ('recovery_notes', 'user_id', 'Owner column; migration 009 enforces auth.uid() = user_id'),
        ('self_check_notice_state', 'id', 'Primary key'),
        ('self_check_notice_state', 'user_id', 'Owner column; migration 009 enforces auth.uid() = user_id'),
        ('weekly_reflections', 'id', 'Primary key'),
        ('weekly_reflections', 'user_id', 'Owner column; migration 009 enforces auth.uid() = user_id'),
        ('tool_notes', 'id', 'Primary key'),
        ('tool_notes', 'user_id', 'Owner column; migration 009 enforces auth.uid() = user_id'),

        -- self_check_daily_checkins: referenced by self_check_observations subquery
        ('self_check_daily_checkins', 'id', 'Referenced by observations RLS (c.id = checkin_id)'),
        ('self_check_daily_checkins', 'user_id', 'Referenced by observations RLS (c.user_id = auth.uid())'),

        -- self_check_trackers: referenced by self_check_observations subquery
        ('self_check_trackers', 'id', 'Referenced by observations RLS (t.id = tracker_id)'),
        ('self_check_trackers', 'user_id', 'Referenced by observations RLS (t.user_id = auth.uid() OR t.user_id IS NULL)'),

        -- self_check_observations: affected table in migration 009
        ('self_check_observations', 'id', 'Primary key'),
        ('self_check_observations', 'checkin_id', 'Foreign key linked to checkins in RLS check'),
        ('self_check_observations', 'tracker_id', 'Foreign key linked to trackers in RLS check'),

        -- ucheck_assessment_drafts: Complete 22-column verification per Migration 008
        ('ucheck_assessment_drafts', 'id', 'Primary key (TEXT per migration 008)'),
        ('ucheck_assessment_drafts', 'user_id', 'Owner column (UUID, nullable per 008; hardened in 009)'),
        ('ucheck_assessment_drafts', 'version', 'Draft version (INTEGER NOT NULL DEFAULT 1 per 008)'),
        ('ucheck_assessment_drafts', 'parent_version_id', 'Lineage reference (TEXT, nullable per 008)'),
        ('ucheck_assessment_drafts', 'status', 'Lifecycle state (TEXT NOT NULL DEFAULT in_progress per 008)'),
        ('ucheck_assessment_drafts', 'current_stage', 'Stage tracker (INTEGER NOT NULL DEFAULT 1 per 008)'),
        ('ucheck_assessment_drafts', 'concerns', 'Step 1 concerns payload (JSONB NOT NULL DEFAULT [] per 008)'),
        ('ucheck_assessment_drafts', 'custom_concerns', 'Step 1 custom concerns (JSONB NOT NULL DEFAULT [] per 008)'),
        ('ucheck_assessment_drafts', 'top_concerns', 'Step 1 top concerns (JSONB NOT NULL DEFAULT [] per 008)'),
        ('ucheck_assessment_drafts', 'feelings_by_concern', 'Step 2 feelings map (JSONB NOT NULL DEFAULT {} per 008)'),
        ('ucheck_assessment_drafts', 'custom_feelings_by_concern', 'Step 2 custom feelings (JSONB NOT NULL DEFAULT {} per 008)'),
        ('ucheck_assessment_drafts', 'noticed_changes', 'Step 2 noticed changes (JSONB NOT NULL DEFAULT [] per 008)'),
        ('ucheck_assessment_drafts', 'custom_changes', 'Step 2 custom changes (JSONB NOT NULL DEFAULT [] per 008)'),
        ('ucheck_assessment_drafts', 'impact_level', 'Step 2 impact level (TEXT NOT NULL DEFAULT empty string per 008)'),
        ('ucheck_assessment_drafts', 'needs', 'Step 3 identified needs (JSONB NOT NULL DEFAULT [] per 008)'),
        ('ucheck_assessment_drafts', 'need_details', 'Step 3 need details (JSONB NOT NULL DEFAULT {} per 008)'),
        ('ucheck_assessment_drafts', 'custom_need', 'Step 3 custom need (TEXT NOT NULL DEFAULT empty string per 008)'),
        ('ucheck_assessment_drafts', 'primary_need', 'Step 3 primary need (TEXT NOT NULL DEFAULT empty string per 008)'),
        ('ucheck_assessment_drafts', 'chosen_direction', 'Step 4 chosen direction (TEXT NOT NULL DEFAULT empty string per 008)'),
        ('ucheck_assessment_drafts', 'created_at', 'Creation timestamp (TIMESTAMPTZ NOT NULL DEFAULT timezone(utc, now()) per 008)'),
        ('ucheck_assessment_drafts', 'updated_at', 'Indexed update timestamp (TIMESTAMPTZ NOT NULL DEFAULT timezone(utc, now()) per 008)'),
        ('ucheck_assessment_drafts', 'completed_at', 'Completion timestamp (TIMESTAMPTZ, nullable per 008)')
) AS target(table_name, column_name, purpose_in_migrations)
LEFT JOIN information_schema.tables t 
    ON t.table_schema = 'public' AND t.table_name = target.table_name
LEFT JOIN information_schema.columns c 
    ON c.table_schema = 'public' AND c.table_name = target.table_name AND c.column_name = target.column_name
ORDER BY target.table_name, target.column_name;


-- ============================================================================
-- BLOCK 2: RLS STATUS AND POLICY INVENTORY
-- Purpose: Inspect whether RLS is active on the seven affected tables and review
--          all existing defined policies, commands, roles, and expressions.
-- Catalogs: pg_tables, pg_policies
--
-- Technical Evaluation Guidance for Reviewers:
--   - RLS Activation Independence:
--     `pg_policies` lists DEFINED policies, while `pg_tables.rowsecurity` independently
--     determines whether RLS is actually ENABLED on the table.
--     Do NOT infer that RLS is active merely because policies exist in `pg_policies`.
--     If `rowsecurity` is false, PostgreSQL completely ignores defined policies for standard
--     operations and falls back to normal table grants. Both `rls_enabled = true` and
--     proper policy definitions are required for account isolation.
--
--   - PostgreSQL Policy Attributes that are NORMAL (NOT automatic violations):
--     1. `qual IS NULL`: Completely normal for INSERT policies (PostgreSQL does
--        not evaluate USING on INSERT, only WITH CHECK).
--     2. `with_check IS NULL`: Completely normal for SELECT and DELETE policies
--        (PostgreSQL does not evaluate WITH CHECK on read or delete operations).
--     3. Multiple policies for the same command: Legitimate if separating roles
--        (e.g., authenticated vs service_role) or combining RESTRICTIVE policies.
--
--   - Policy Interaction & Broadening Access:
--     PostgreSQL combines PERMISSIVE policies for the same command with boolean OR:
--     (Policy_A OR Policy_B). Therefore, an unexpected permissive policy with a wide
--     clause (e.g., USING (true) or OR user_id IS NULL) broadens access and bypasses
--     Migration 009's intent.
--
--   - Review Rule:
--     Flag unexpected policies for human review based on actual roles, commands,
--     expressions, and interaction with the intended policies. Do NOT classify every
--     additional policy as an automatic hard stop.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- BLOCK 2A: RLS Table Status & Policy Count
-- Expected: 7 rows with rls_enabled = true.
-- ----------------------------------------------------------------------------
SELECT 
    target.table_name,
    CASE 
        WHEN t.tablename IS NOT NULL THEN 'EXISTS' 
        ELSE 'MISSING' 
    END AS table_status,
    COALESCE(t.rowsecurity, false) AS rls_enabled,
    count(p.policyname) AS policy_count
FROM (
    VALUES 
        ('plan_items'),
        ('recovery_notes'),
        ('self_check_notice_state'),
        ('weekly_reflections'),
        ('tool_notes'),
        ('self_check_observations'),
        ('ucheck_assessment_drafts')
) AS target(table_name)
LEFT JOIN pg_tables t 
    ON t.schemaname = 'public' AND t.tablename = target.table_name
LEFT JOIN pg_policies p 
    ON p.schemaname = 'public' AND p.tablename = target.table_name
GROUP BY target.table_name, t.tablename, t.rowsecurity
ORDER BY target.table_name;


-- ----------------------------------------------------------------------------
-- BLOCK 2B: Complete RLS Policy Inventory
-- Expected: List of all defined policies on the 7 affected tables.
-- ----------------------------------------------------------------------------
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual AS using_expression,
    with_check AS with_check_expression
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN (
    'plan_items',
    'recovery_notes',
    'self_check_notice_state',
    'weekly_reflections',
    'tool_notes',
    'self_check_observations',
    'ucheck_assessment_drafts'
  )
ORDER BY tablename, cmd, policyname;


-- ============================================================================
-- BLOCK 3: NULL user_id RECORD COUNT AUDIT (SEPARATE SELECT QUERIES)
-- Purpose: Inspect rows with user_id IS NULL in private user tables.
--
-- CRITICAL SAFETY INSTRUCTIONS:
--   - Do NOT run these queries as a single batch without checking Block 1.
--   - First run Block 1 to verify that the table and its user_id column exist.
--   - Only execute a table-specific query below if Block 1 confirms table existence.
--   - Run Query 3.5 (ucheck_assessment_drafts) ONLY if Block 1 confirms BOTH:
--     1. public.ucheck_assessment_drafts physically exists.
--     2. Its user_id column physically exists.
--     If either the table or user_id column is missing, DO NOT EXECUTE Query 3.5.
--
-- Technical Interpretation:
--   - NULL count = 0: CLEAN. No affected NULL-owner rows detected.
--   - NULL count > 0: OWNERSHIP INVESTIGATION REQUIRED.
--   - Missing Table: Migration dependency (e.g. Migration 008 unapplied).
--   - Missing Required Column: HARD STOP. Schema incompatibility.
--
-- Access Impact vs Physical Data Safety:
--   - Migration 009 DOES NOT DELETE OR TRUNCATE NULL-owner rows.
--   - Removing 'OR user_id IS NULL' means authenticated PostgREST API queries
--     (which evaluate auth.uid() = user_id) will no longer return these rows.
--   - The rows remain stored on disk and accessible to administrators via service_role.
--   - NEVER recommend automatic deletion or reassignment without engineering review.
-- ============================================================================

-- Query 3.1: recovery_notes
-- PRECONDITION: Run only if Block 1 confirms public.recovery_notes and user_id exist.
SELECT 
    'recovery_notes' AS table_name,
    count(*) AS total_rows,
    count(*) FILTER (WHERE user_id IS NULL) AS null_user_id_rows
FROM public.recovery_notes;

-- Query 3.2: self_check_notice_state
-- PRECONDITION: Run only if Block 1 confirms public.self_check_notice_state and user_id exist.
SELECT 
    'self_check_notice_state' AS table_name,
    count(*) AS total_rows,
    count(*) FILTER (WHERE user_id IS NULL) AS null_user_id_rows
FROM public.self_check_notice_state;

-- Query 3.3: weekly_reflections
-- PRECONDITION: Run only if Block 1 confirms public.weekly_reflections and user_id exist.
SELECT 
    'weekly_reflections' AS table_name,
    count(*) AS total_rows,
    count(*) FILTER (WHERE user_id IS NULL) AS null_user_id_rows
FROM public.weekly_reflections;

-- Query 3.4: tool_notes
-- PRECONDITION: Run only if Block 1 confirms public.tool_notes and user_id exist.
SELECT 
    'tool_notes' AS table_name,
    count(*) AS total_rows,
    count(*) FILTER (WHERE user_id IS NULL) AS null_user_id_rows
FROM public.tool_notes;

-- Query 3.5: ucheck_assessment_drafts
-- PRECONDITION: Run ONLY if Block 1 confirms BOTH that public.ucheck_assessment_drafts
--               physically exists AND that its user_id column physically exists.
SELECT 
    'ucheck_assessment_drafts' AS table_name,
    count(*) AS total_rows,
    count(*) FILTER (WHERE user_id IS NULL) AS null_user_id_rows
FROM public.ucheck_assessment_drafts;


-- ============================================================================
-- BLOCK 4: PRODUCTION INDEX INVENTORY
-- Purpose: Inspect all existing indexes across all 11 core tables using PostgreSQL
--          catalog inspection.
-- Catalog: pg_indexes
--
-- Technical Note:
--   - This query reports ACTUAL physical indexes present in the remote database.
--   - Do NOT assume that an index exists merely because it appears in a local
--     migration file. Verify presence from the actual query output.
-- ============================================================================
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN (
    'plan_items',
    'recovery_notes',
    'self_check_notice_state',
    'weekly_reflections',
    'tool_notes',
    'self_check_observations',
    'ucheck_assessment_drafts',
    'plans',
    'tasks',
    'self_check_trackers',
    'self_check_daily_checkins'
  )
ORDER BY tablename, indexname;


-- ============================================================================
-- BLOCK 5: MIGRATION 008 PREREQUISITE & EXTENSION CHECK
-- Purpose: Verify Migration 008 schema and security prerequisites before applying 009.
-- Catalogs: information_schema.tables, information_schema.columns, pg_extension
--
-- Technical Clarification on uuid-ossp Extension:
--   - Migration 008 declares `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`.
--   - However, ucheck_assessment_drafts uses `id TEXT PRIMARY KEY` and does not
--     visibly invoke functions from uuid-ossp (such as uuid_generate_v4()) in its
--     column defaults or index statements.
--   - Therefore, missing uuid-ossp alone is NOT classified as a hard stop unless
--     evidence shows deployed schema expressions actually depend on it.
--   - Extension presence is reported separately as INFORMATIONAL.
--
-- Verification Scope Distinction:
--   - Table existence alone does NOT prove Migration 008 was fully applied.
--   - Do not assume that a table containing only a subset of columns is fully compatible.
--     All 22 columns defined in Migration 008 must be verified.
--   - Semantic Default Comparison:
--     Raw catalog string representations of defaults can vary (e.g. whitespace, explicit casts).
--     Block 5B compares semantic equivalence where safely possible and returns 'MANUAL REVIEW'
--     whenever safe equivalence cannot be determined in read-only SQL. It NEVER returns a false MATCH.
--   - Supabase migration-history tables (e.g. supabase_migrations.schema_migrations)
--     are not assumed to be readable. If migration history cannot be directly verified
--     through available catalog queries, that limitation must be noted.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- BLOCK 5A: Table Existence and Extension Presence
-- ----------------------------------------------------------------------------
SELECT 
    'public.ucheck_assessment_drafts' AS object_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'ucheck_assessment_drafts'
        ) 
        THEN 'TABLE EXISTS (Verify columns, constraints, and policies below)' 
        ELSE 'TABLE MISSING (HARD STOP: Migration 008 must precede Migration 009)' 
    END AS status,
    'SCHEMA PREREQUISITE' AS check_category
UNION ALL
SELECT 
    'extension: uuid-ossp' AS object_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM pg_extension 
            WHERE extname = 'uuid-ossp'
        ) 
        THEN 'INSTALLED' 
        ELSE 'NOT INSTALLED (Informational: migration 008 declares this, but table does not visibly invoke it)' 
    END AS status,
    'INFORMATIONAL' AS check_category;


-- ----------------------------------------------------------------------------
-- BLOCK 5B: ucheck_assessment_drafts Complete 22-Column Schema & Semantic Default Verification
-- (Verifies all 22 columns defined in Migration 008 against expected specifications)
-- ----------------------------------------------------------------------------
SELECT 
    expected.column_name,
    CASE 
        WHEN c.column_name IS NOT NULL THEN 'PRESENT' 
        ELSE 'MISSING (HARD STOP: Schema incomplete)' 
    END AS column_presence,

    -- Data Type Verification
    expected.expected_data_type,
    COALESCE(c.data_type, 'N/A') AS actual_data_type,
    CASE 
        WHEN c.column_name IS NULL THEN 'MISSING (HARD STOP)'
        WHEN c.data_type = expected.expected_data_type THEN 'MATCH'
        ELSE 'MISMATCH (HARD STOP)'
    END AS data_type_status,

    -- Nullability Verification
    expected.expected_nullability,
    COALESCE(c.is_nullable, 'N/A') AS actual_nullability,
    CASE 
        WHEN c.column_name IS NULL THEN 'MISSING (HARD STOP)'
        WHEN c.is_nullable = expected.expected_nullability THEN 'MATCH'
        ELSE 'MISMATCH (HARD STOP)'
    END AS nullability_status,

    -- Default Specification & Semantic Equivalence Verification
    expected.expected_default,
    COALESCE(c.column_default, 'NONE') AS actual_default,
    CASE 
        WHEN c.column_name IS NULL THEN 'MISSING (HARD STOP)'
        
        -- Columns with NO default expected (id, user_id, parent_version_id, completed_at)
        WHEN expected.expected_default = 'NONE' THEN 
            CASE 
                WHEN c.column_default IS NULL THEN 'MATCH (No default expected)'
                ELSE 'MISMATCH (Unexpected default present)'
            END

        -- Columns where default is unexpectedly NULL in actual database
        WHEN c.column_default IS NULL THEN 'MISMATCH (Default missing)'

        -- Integer defaults (version = 1, current_stage = 1)
        WHEN expected.expected_data_type = 'integer' THEN
            CASE 
                WHEN trim(c.column_default) IN ('1', '1::integer', '1::smallint', '1::bigint') 
                  OR replace(trim(c.column_default), ' ', '') IN ('1', '1::integer') THEN 'MATCH'
                WHEN c.column_default ~ '^\d+$' AND c.column_default <> '1' THEN 'MISMATCH'
                ELSE 'MANUAL REVIEW'
            END

        -- JSONB empty array defaults (concerns, custom_concerns, top_concerns, noticed_changes, custom_changes, needs)
        WHEN expected.expected_default = '''[]''::jsonb' THEN
            CASE 
                WHEN replace(trim(c.column_default), ' ', '') IN ('''[]''::jsonb', 'jsonb_build_array()') THEN 'MATCH'
                WHEN c.column_default ~* '\[\s*\]' THEN 'MANUAL REVIEW (Formatting variation)'
                ELSE 'MANUAL REVIEW'
            END

        -- JSONB empty object defaults (feelings_by_concern, custom_feelings_by_concern, need_details)
        WHEN expected.expected_default = '''{}''::jsonb' THEN
            CASE 
                WHEN replace(trim(c.column_default), ' ', '') IN ('''{}''::jsonb', 'jsonb_build_object()') THEN 'MATCH'
                WHEN c.column_default ~* '\{\s*\}' THEN 'MANUAL REVIEW (Formatting variation)'
                ELSE 'MANUAL REVIEW'
            END

        -- Text empty string defaults (impact_level, custom_need, primary_need, chosen_direction)
        WHEN expected.expected_default = '''''::text' THEN
            CASE 
                WHEN trim(c.column_default) IN ('''''::text', '''''', '''''::character varying') 
                  OR replace(trim(c.column_default), ' ', '') IN ('''''::text', '''''', '''''::charactervarying') THEN 'MATCH'
                WHEN c.column_default ~* '^\s*''''::' THEN 'MANUAL REVIEW (Text cast variation)'
                ELSE 'MANUAL REVIEW'
            END

        -- Text status default ('in_progress'::text)
        WHEN expected.expected_default = '''in_progress''::text' THEN
            CASE 
                WHEN trim(c.column_default) IN ('''in_progress''::text', '''in_progress''', '''in_progress''::character varying') 
                  OR replace(trim(c.column_default), ' ', '') IN ('''in_progress''::text', '''in_progress''', '''in_progress''::charactervarying') THEN 'MATCH'
                ELSE 'MANUAL REVIEW'
            END

        -- TIMESTAMPTZ UTC now defaults (created_at, updated_at)
        -- TECHNICAL NOTE ON TIMESTAMP WITHOUT TIME ZONE CONVERSION:
        -- Migration 008 declares: created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
        -- In PostgreSQL, timezone('utc', now()) returns a TIMESTAMP WITHOUT TIME ZONE (wall-clock UTC).
        -- When inserted into a TIMESTAMPTZ column, PostgreSQL implicitly casts it to TIMESTAMPTZ
        -- by assuming the naked timestamp is in the active session's TimeZone setting!
        -- If the session TimeZone is not UTC, this implicit conversion can cause unexpected offsets.
        -- Therefore, matching this expression confirms that the catalog default matches Migration 008,
        -- but does NOT prove UTC storage behavior across arbitrary client session configurations.
        WHEN expected.expected_data_type = 'timestamp with time zone' AND expected.expected_default LIKE '%timezone%' THEN
            CASE 
                WHEN replace(lower(trim(c.column_default)), ' ', '') IN (
                    'timezone(''utc''::text,now())',
                    'timezone(''utc''::text,current_timestamp)',
                    'now()attimezone''utc''::text',
                    'now()attimezone''utc'''
                ) THEN 'MATCH (Equivalent Expression)'
                WHEN replace(lower(trim(c.column_default)), ' ', '') LIKE '%timezone(%''utc''%now()%)%' 
                  OR replace(lower(trim(c.column_default)), ' ', '') LIKE '%timezone(%''utc''%current_timestamp%)%'
                  OR replace(lower(trim(c.column_default)), ' ', '') LIKE '%now()attimezone%''utc''%' THEN 'MATCH (Equivalent Expression)'
                ELSE 'MANUAL REVIEW (Inspect custom timestamp expression)'
            END

        ELSE 'MANUAL REVIEW'
    END AS default_status
FROM (
    VALUES 
        ('id', 'text', 'NO', 'NONE'),
        ('user_id', 'uuid', 'YES', 'NONE'),
        ('version', 'integer', 'NO', '1'),
        ('parent_version_id', 'text', 'YES', 'NONE'),
        ('status', 'text', 'NO', '''in_progress''::text'),
        ('current_stage', 'integer', 'NO', '1'),
        ('concerns', 'jsonb', 'NO', '''[]''::jsonb'),
        ('custom_concerns', 'jsonb', 'NO', '''[]''::jsonb'),
        ('top_concerns', 'jsonb', 'NO', '''[]''::jsonb'),
        ('feelings_by_concern', 'jsonb', 'NO', '''{}''::jsonb'),
        ('custom_feelings_by_concern', 'jsonb', 'NO', '''{}''::jsonb'),
        ('noticed_changes', 'jsonb', 'NO', '''[]''::jsonb'),
        ('custom_changes', 'jsonb', 'NO', '''[]''::jsonb'),
        ('impact_level', 'text', 'NO', '''''::text'),
        ('needs', 'jsonb', 'NO', '''[]''::jsonb'),
        ('need_details', 'jsonb', 'NO', '''{}''::jsonb'),
        ('custom_need', 'text', 'NO', '''''::text'),
        ('primary_need', 'text', 'NO', '''''::text'),
        ('chosen_direction', 'text', 'NO', '''''::text'),
        ('created_at', 'timestamp with time zone', 'NO', 'timezone(''utc''::text, now())'),
        ('updated_at', 'timestamp with time zone', 'NO', 'timezone(''utc''::text, now())'),
        ('completed_at', 'timestamp with time zone', 'YES', 'NONE')
) AS expected(column_name, expected_data_type, expected_nullability, expected_default)
LEFT JOIN information_schema.columns c
    ON c.table_schema = 'public' 
   AND c.table_name = 'ucheck_assessment_drafts' 
   AND c.column_name = expected.column_name
ORDER BY expected.column_name;


-- ============================================================================
-- BLOCK 6: FOREIGN KEY AND CONSTRAINT AUDIT (EXPANDED TO ALL 11 TABLES)
-- Purpose: Inspect primary keys, foreign keys, and unique constraints across
--          all 11 core tables involved in Migration 008 and Migration 009.
-- Catalogs: information_schema.table_constraints, key_column_usage, referential_constraints,
--           constraint_column_usage
--
-- Cross-Schema Foreign Key Join Identity (Block 6A):
--   - The join explicitly binds source table schema (tc.table_schema) and source table name
--     (tc.table_name) into key_column_usage (kcu).
--   - The referenced key-column usage (rkcu) is joined via unique constraint name and ordinal position.
--   - To avoid matching solely by constraint name and ordinal position, rkcu is explicitly bound
--     to constraint_column_usage (ccu) on table_schema, table_name, and column_name.
--   - This ensures composite foreign keys are paired 1-to-1 without Cartesian row multiplication.
--   - If information_schema cannot authoritatively establish the referenced table identity,
--     constraint_identity_status explicitly returns 'MANUAL REVIEW REQUIRED'.
--
-- DIRECT CATALOG INSPECTION & METADATA VISIBILITY (Block 6B):
--   - information_schema views restrict rows to objects the active database role has permissions on.
--   - If the executing database role lacks SELECT privilege on the auth schema, cross-schema foreign
--     keys referencing auth.users may appear blank or omitted in information_schema.
--   - Do NOT classify an empty foreign key result caused by metadata visibility limitations
--     as definitive proof that a constraint does not exist.
--   - Block 6B provides direct pg_catalog.pg_constraint inspection, which is less dependent on
--     ANSI SQL information_schema view filtering. However, results must still be reviewed under
--     the actual Production execution role and permissions.
--
-- Technical Classification of Findings:
--   1. Missing Required Tables or Columns: HARD STOP.
--   2. Schema Incompatibility Preventing Subqueries from Functioning: HARD STOP.
--      (e.g., column data type mismatch preventing plans.id = plan_id).
--   3. Missing Expected Foreign Keys: DATA INTEGRITY WARNING (Human Review).
--      Technical Note: PostgreSQL RLS subqueries (e.g.,
--      `EXISTS (SELECT 1 FROM tasks t WHERE t.id = task_id AND t.user_id = auth.uid())`)
--      evaluate at query runtime via index or sequential scans. PostgreSQL does NOT
--      require an active relational foreign key constraint for an RLS subquery to
--      execute. However, missing foreign keys mean orphaned or mismatched records could
--      exist, representing data integrity risks that require human review.
--      Missing FKs alone do NOT automatically fail migration execution.
--
-- Additional Policy Logic Reminders:
--   - plan_items UPDATE Policy:
--     USING: checks only `p.id = plan_id AND p.user_id = auth.uid()`
--     WITH CHECK: checks both `p.id = plan_id AND p.user_id = auth.uid()` AND
--                            `t.id = task_id AND t.user_id = auth.uid()`
--     This ensures users can update existing plan items while strictly preventing
--     assignment of tasks owned by other users.
--   - self_check_observations Policy:
--     checkin_id: strictly requires `c.user_id = auth.uid()`.
--     tracker_id: allows `t.user_id = auth.uid() OR t.user_id IS NULL` (system templates).
--   - User ID Immutability:
--     Migration 009 comments mention immutability, but the migration body itself does
--     not implement a dedicated immutability mechanism (e.g. trigger or column constraint).
--     Reviewers must not claim this property is enforced by Migration 009 alone.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- BLOCK 6A: Information Schema Constraint Inventory (With Strict Join Identity)
-- ----------------------------------------------------------------------------
SELECT 
    tc.table_schema AS source_table_schema,
    tc.table_name AS source_table_name, 
    tc.constraint_name, 
    tc.constraint_type,
    kcu.column_name AS source_column_name, 
    kcu.ordinal_position AS column_position,
    CASE 
        WHEN tc.constraint_type = 'FOREIGN KEY' THEN COALESCE(rkcu.table_schema, ccu.table_schema) 
        ELSE NULL 
    END AS foreign_table_schema,
    CASE 
        WHEN tc.constraint_type = 'FOREIGN KEY' THEN COALESCE(rkcu.table_name, ccu.table_name) 
        ELSE NULL 
    END AS foreign_table_name,
    CASE 
        WHEN tc.constraint_type = 'FOREIGN KEY' THEN COALESCE(rkcu.column_name, ccu.column_name) 
        ELSE NULL 
    END AS foreign_column_name,
    CASE 
        WHEN tc.constraint_type <> 'FOREIGN KEY' THEN 'LOCAL CONSTRAINT'
        WHEN rkcu.column_name IS NOT NULL AND ccu.column_name IS NOT NULL THEN 'VERIFIED (Bound to referenced table via CCU metadata)'
        WHEN rkcu.column_name IS NOT NULL THEN 'MANUAL REVIEW (Referenced table not bound via CCU)'
        ELSE 'MANUAL REVIEW (Referenced metadata restricted or incomplete in information_schema; inspect via Block 6B)'
    END AS constraint_identity_status
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON kcu.constraint_schema = tc.constraint_schema
   AND kcu.constraint_name = tc.constraint_name 
   AND kcu.table_schema = tc.table_schema
   AND kcu.table_name = tc.table_name
LEFT JOIN information_schema.referential_constraints AS rc
    ON rc.constraint_schema = tc.constraint_schema
   AND rc.constraint_name = tc.constraint_name
LEFT JOIN information_schema.key_column_usage AS rkcu
    ON rkcu.constraint_schema = rc.unique_constraint_schema
   AND rkcu.constraint_name = rc.unique_constraint_name 
   AND rkcu.ordinal_position = kcu.position_in_unique_constraint
LEFT JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_schema = tc.constraint_schema
   AND ccu.constraint_name = tc.constraint_name
   AND ccu.table_schema = rkcu.table_schema
   AND ccu.table_name = rkcu.table_name
   AND ccu.column_name = rkcu.column_name
WHERE tc.table_schema = 'public'
  AND tc.table_name IN (
    'plan_items',
    'plans',
    'tasks',
    'self_check_observations',
    'self_check_daily_checkins',
    'self_check_trackers',
    'recovery_notes',
    'self_check_notice_state',
    'weekly_reflections',
    'tool_notes',
    'ucheck_assessment_drafts'
  )
ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name, kcu.ordinal_position;


-- ----------------------------------------------------------------------------
-- BLOCK 6B: Direct pg_catalog Constraint Inventory (Direct Catalog Inspection)
-- Purpose: Direct PostgreSQL catalog inspection that is less dependent on
--          SQL-standard information_schema visibility restrictions.
-- Note: Unlike information_schema views (which filter rows based on ANSI SQL table
--       privilege grants), pg_catalog tables expose system dictionary records directly.
--       However, results must still be reviewed under the actual Production execution
--       role and permissions, as role-level row security or catalog access policies on
--       managed platforms can influence visibility.
-- ----------------------------------------------------------------------------
SELECT 
    src_ns.nspname AS source_table_schema,
    src_cl.relname AS source_table_name,
    c.conname AS constraint_name,
    CASE c.contype
        WHEN 'p' THEN 'PRIMARY KEY'
        WHEN 'f' THEN 'FOREIGN KEY'
        WHEN 'u' THEN 'UNIQUE'
        WHEN 'c' THEN 'CHECK'
        ELSE c.contype::text
    END AS constraint_type,
    src_att.attname AS source_column_name,
    kcu_pos.ord AS column_position,
    ref_ns.nspname AS foreign_table_schema,
    ref_cl.relname AS foreign_table_name,
    ref_att.attname AS foreign_column_name
FROM pg_catalog.pg_constraint c
JOIN pg_catalog.pg_class src_cl 
    ON src_cl.oid = c.conrelid
JOIN pg_catalog.pg_namespace src_ns 
    ON src_ns.oid = src_cl.relnamespace
CROSS JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS kcu_pos(attnum, ord)
JOIN pg_catalog.pg_attribute src_att 
    ON src_att.attrelid = c.conrelid AND src_att.attnum = kcu_pos.attnum
LEFT JOIN pg_catalog.pg_class ref_cl 
    ON ref_cl.oid = c.confrelid
LEFT JOIN pg_catalog.pg_namespace ref_ns 
    ON ref_ns.oid = ref_cl.relnamespace
LEFT JOIN LATERAL (
    SELECT confkey_attnum.attnum, confkey_attnum.ord
    FROM unnest(c.confkey) WITH ORDINALITY AS confkey_attnum(attnum, ord)
) ref_pos ON ref_pos.ord = kcu_pos.ord
LEFT JOIN pg_catalog.pg_attribute ref_att 
    ON ref_att.attrelid = c.confrelid AND ref_att.attnum = ref_pos.attnum
WHERE src_ns.nspname = 'public'
  AND src_cl.relname IN (
    'plan_items',
    'plans',
    'tasks',
    'self_check_observations',
    'self_check_daily_checkins',
    'self_check_trackers',
    'recovery_notes',
    'self_check_notice_state',
    'weekly_reflections',
    'tool_notes',
    'ucheck_assessment_drafts'
  )
ORDER BY source_table_name, constraint_type, constraint_name, column_position;
