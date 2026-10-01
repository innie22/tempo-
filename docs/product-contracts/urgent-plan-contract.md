# PRODUCT CONTRACT: URGENT PLAN (EPLAN)

> **STATUS: APPROVED & FROZEN (DEVELOPMENT-TIME REGRESSION PROTECTION)**  
> **Target Audience:** Developers, AI Coding Agents, Product Reviewers  
> **Scope:** Creation flow, plan data model, post-save editing, task identity, and scheduling invariants.  
> **Internal Plan Type:** `plan_type = "emergency"` (legacy/internal Eplan).  
> **User-Facing UI Label:** `"Urgent Plan"`.

---

## 1. Core Principle & Purpose
Urgent Plan is an acute crisis triage plan built to manage heavy workloads and imminent deadlines step by step.

- **Primary Philosophy:** The plan provides an **authoritative, realistic schedule** grounded in user-provided available time blocks and honest estimates.
- **Dynamic User Data:** **USER DATA IS NOT FROZEN.** Users can freely create, adjust, complete, uncomplete, add, review, and finish tasks. The *architecture, rules, and semantic data contracts* are frozen, not the data itself.

---

## 2. Established 10-Stage Creation Flow
The Urgent Plan setup wizard follows a strict 10-stage progression managed in `emergencyFlow.js`:

```
1. Settle / Reset Checkpoint (entry)
       ↓
2. Reality Check (reality-check) — Rapid task dump
       ↓
3. Prioritize Assessment (prioritize) — Rough duration & deadline tags
       ↓
4. Priority Review & Buckets (priority-review) — DO FIRST vs THEN vs LATER
       ↓
5. Available Time Entry (available-time) — Daily available time blocks
       ↓
6. Feasibility & Workload Check (feasibility) — Workload vs available time validation
       ↓
7. Generating Plan (generating) — Algorithmic schedule allocation
       ↓
8. Urgent Plan Review & Schedule (plan-review) — Reviewing the daily schedule
       ↓
9. Step Breakdown (breakdown) — Breaking initial tasks into bite-sized actionable steps
       ↓
10. Start Working Handoff (handoff) — Confirmation and redirection to execution
```

Developers and agents must **NOT** redesign, skip, or merge these stages during unrelated tasks.

---

## 3. Plan Workspace (Post-Save View & Edit Experience)

Once confirmed, the Urgent Plan is viewed and edited in the Plan Workspace (`planWorkspace.js`), accessible via `View / Edit Plan →` from Urgent Home.

### Workspace Layout & Invariants:
1. **Left Main Area:**
   - Date-grouped timeline with scheduled start/end times and priority badges (`DO THIS FIRST`, `THEN`, `LATER`).
   - Execution status toggles (`Completed`, `NOW`, `UP NEXT`).
   - `NOT SCHEDULED YET` section for unarranged or newly added tasks.
   - `Global Focus` CTA (suggests first unfinished task for today without reranking the plan).
   - `Add a task` modal entry.
2. **Right Task Detail Drawer (`#task-detail-drawer`):**
   - Displays task name, scheduled time block, deadline, duration estimate, and action steps (subtasks).
   - Task-specific `Focus on this task →` CTA opening Focus Zone.
   - Direct inline subtask management (adding, checking off, removing steps).
   - Direct deadline editing and estimate adjustment.
3. **Drawer Closing & Return:**
   - Navigating back to Home preserves identical active plan data without triggering setup reload.

---

## 4. Plan Data Invariants

1. **Shared Task Identity:**
   - Tasks carry stable unique identifiers (`id` / `taskId`).
   - When a task is added or scheduled, its ID is preserved across references in `TempoPlanStore`, `TempoEmergencyFlow`, and `TempoFocusZone`.
   - **NO duplicate task entities** may be created when switching modes or moving between setup and workspace.

2. **Cross-Reference Completion Continuity:**
   - Toggling a task as complete in Urgent Home, Plan Workspace, or Focus Zone updates `task.completed = true` everywhere.
   - Subtask completion is tracked on `task.subtasks[]` and updates the action steps progress indicator across all views.

3. **Subtask & Estimate Integrity:**
   - Subtasks remain strictly bound to their parent task.
   - Duration estimates (`durationMinutes`, `durationLabel`) remain attached to the task object.

4. **Authoritative Execution Order:**
   - Plan task order is determined by the confirmed schedule.
   - **NO SILENT RERANKING:** Actions like starting focus, changing a deadline, or adding a subtask must NEVER automatically reorder the user's planned tasks.
   - **NO SILENT RESCHEDULING:** Tasks never silently jump dates without explicit user confirmation.

5. **Stale Plan Handling:**
   - If scheduled dates pass while tasks remain incomplete, the plan transitions into `PLAN_STALE`.
   - Incomplete past tasks are presented calmly under `SCHEDULE UPDATE NEEDED` in Urgent Home.
   - The user is invited to review and adjust their schedule via Plan Workspace without automatic destructive changes.

6. **Persistence Schema Compatibility:**
   - The persisted `planType` property must remain `"emergency"`.
   - **DO NOT** migrate or rename saved records to `plan_type = "urgent"`.
   - Legacy stored plans must load and parse reliably without schema exceptions.

---

## 5. Non-Visual Semantic Test Hooks
- `data-tempo-ui="plan-workspace"`: Root container for the Plan Workspace.
- `data-tempo-ui="plan-timeline"`: Scheduled task list container.
- `data-tempo-ui="plan-drawer"`: Task detail drawer.

---

## 6. Future Developer & AI Agent Rules

> [!IMPORTANT]
> **MANDATORY VERIFICATION:**
> Any future task modifying `emergencyFlow.js`, `planStore.js`, `planWorkspace.js`, or planning algorithms **MUST** run:
> ```powershell
> & "python.exe" test_urgent_plan_contract.py
> ```
> If this test fails, the agent/developer **MUST NOT** solve the failure by weakening, editing, or deleting this contract or the test. The implementation must be fixed to adhere to this contract.
>
> Changes to this contract require explicit written approval from the product owner.
