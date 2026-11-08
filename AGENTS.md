# TEMPO — REPOSITORY HYGIENE & DEVELOPMENT GOVERNANCE

## 1. Context & Purpose
Tempo is an interactive university student wellbeing and stress triage web application.
Following the major cleanup merged into `main` via PR #1 (commit `8138617`), the repository must remain clean, lean, maintainable, and production-ready.

All AI agents and contributors must strictly adhere to these governance rules. Do not solve development problems by generating more scripts, more copies, more patches, or more temporary files.

---

## 2. Core Principles
1. **Reuse Existing Files & Components:** Search the repository before creating new files. Modify existing implementations in place.
2. **Single Source of Truth:** One feature must have one canonical, maintainable implementation.
3. **Keep Repository Simple & Predictable:** Prioritize maintainability over creating unnecessary abstractions.
4. **Zero Lingering Artifacts:** Never leave temporary scripts, logs, experimental files, or backups in the repository.
5. **Preserve Production Functionality:** Never modify unrelated modules, production configuration, or existing uncommitted changes.

---

## 3. File Creation Policy
Before creating any file:
- Search for an existing file serving that purpose.
- Implement the functionality within an existing module whenever feasible.
- Create a new file only when separation provides a distinct architectural benefit.

### Prohibited File Patterns
Never create:
- Suffix variants: `*_fixed.*`, `*_final.*`, `*_v2.*`, `*_backup.*`, `*_test_copy.*`
- Debugging scripts: `debug_*.*`, `fix_*.*`, `apply_*.*`, `temp_*.*`
- Duplicate SQL files, alternate schema snapshots, or duplicate migration drafts
- Multiple parallel implementations of the same component
- Unrequested documentation, extra READMEs, screenshots, test exports, or logs in the source tree

Use Git history to track iterations; never use filenames as versioning.

---

## 4. Development Artifacts Handling
- Keep all temporary development artifacts (scratch scripts, debug dumps, logs, test outputs) **outside the repository** in external scratch directories.
- If a temporary file must exist inside the workspace temporarily:
  1. Keep it in an explicitly designated temporary directory.
  2. Ensure it is ignored by Git.
  3. Remove it immediately after the task is completed.
  4. Verify no untracked files remain.

---

## 5. Git & Repository Protection
The following rules are mandatory:
- **Never** run `git clean`.
- **Never** delete large groups of files automatically.
- **Never** rewrite Git history or force-push (`--force`).
- **Never** modify, switch, or delete branches without explicit authorization.
- **Never** commit or push automatically.
- **Always** inspect the current branch and working tree before making modifications.
- **Always** preserve existing uncommitted user changes.

---

## 6. Supabase & Production Safety
Tempo uses Supabase for authentication and database persistence.
- **Canonical Migrations Only:** Store executable migrations strictly in `supabase/migrations/` using proper sequence numbering.
- **Separate Evidence Queries:** Keep diagnostic or evidence SQL queries completely separate from migration files.
- **Zero Unauthorized DB Mutation:** Never execute SQL, DDL, DML, or migrations against Supabase Production without explicit approval.
- **Preserve Production Settings:** Never modify production environment variables, RLS policies, triggers, or deployment configuration without explicit authorization.

---

## 7. Architecture & Code Quality
- Follow existing architectural patterns and naming conventions.
- Keep components modular, lightweight, and focused.
- Do not refactor unrelated modules opportunistically.
- Keep dependencies minimal; do not install packages without clear technical justification.

---

## 8. Pre-Completion Repository Hygiene Check
Before completing any task, verify:
1. Were unnecessary files created?
2. Were duplicate files or implementations introduced?
3. Were temporary scripts, logs, or outputs removed?
4. Were unrelated modules modified?
5. Were production configurations and Supabase files preserved?
6. Are all changes relevant to the requested task?

---

## 9. Mandatory Task Completion Report
At the end of every development task, provide a concise report using this exact structure:

### Development Summary
- Features or modules modified.
- Existing files reused.
- New files created, with reasons.
- Files removed, with reasons.

### Repository Hygiene
- Temporary artifacts created.
- Temporary artifacts removed.
- Duplicate files detected.
- `.gitignore` changes, if any.

### Production Safety
- Whether production configuration was modified.
- Whether Supabase schema or data was modified.
- Whether migrations were executed.
- Whether deployment configuration was modified.

### Git Status
- Current branch.
- Number of modified files.
- Number of added files.
- Number of deleted files.
- Whether changes are committed or pushed.
