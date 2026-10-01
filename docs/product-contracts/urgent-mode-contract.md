# PRODUCT CONTRACT: URGENT MODE (EMODE)

> **STATUS: APPROVED & FROZEN (DEVELOPMENT-TIME REGRESSION PROTECTION)**  
> **Target Audience:** Developers, AI Coding Agents, Product Reviewers  
> **Scope:** Runtime behavior, layout hierarchy, visual invariants, and state architecture of Urgent Mode.  
> **Internal Identifier:** `MODES.EMERGENCY` / `"emergency"` (legacy/internal).  
> **User-Facing UI Label:** `"Urgent Mode"`.

---

## 1. Core Principle & Purpose
Urgent Mode is an **EXECUTION-FIRST WORKSPACE** designed for acute academic deadline triage and intense pressure.

- **Primary Goal:** Immediate, calm, step-by-step academic execution.
- **Mode Philosophy:** Mode is **context**, not permanent hero content. Urgent Home must never be overwhelmed with marketing banners, oversized greeting heroes, or generic productivity tools.
- **Relationship with Other Modes:**
  - **Default Home:** Continuity / neutral student dashboard.
  - **Recovery Mode:** Slow down, check in, restore energy.
  - **Urgent Mode:** Focused execution on what must happen now.
  - **SOS:** Separate safety layer. Urgent Mode is **NOT** SOS.

---

## 2. Desktop Layout Hierarchy (~65 / 35 Execution Core)

Urgent Mode Home renders a stable, asymmetric two-column composition on desktop:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [⚡ Urgent Mode ▾]                                                   [Date] │
├──────────────────────────────────────────────┬──────────────────────────────┤
│ PRIMARY EXECUTION AREA (~65%)                │ YOUR PLAN FOR TODAY (~35%)   │
│ (Warm Peach Gradient, border-2 border-warm)  │ (White structured panel)     │
│                                              │                              │
│ [● YOUR TASK FOR NOW]                  [NOW] │ Completion Progress (e.g. 1/3│
│                                              │ View / Edit Plan →           │
│ Hi, {username} 👋                            │                              │
│ Task Title (font-extrabold, 2xl/3xl)         │ Ordered Timeline:            │
│ Actionable Next Step / Subtask               │ ✓ COMPLETED                  │
│                                              │ ● NOW                        │
│ due time · estimate · action-step progress   │ ○ UP NEXT                    │
│                                              │                              │
│ [ Focus on this task → ]  [ View task → ]    │                              │
├──────────────────────────────────────────────┴──────────────────────────────┤
│ DEDICATED SUPPORT ROW                                                       │
│ ┌──────────────────────────────────────────┬──────────────────────────────┐ │
│ │ Feeling overwhelmed?                     │ Focus now                    │ │
│ │ Quick Stress Relief  |  Breathing        │ Start Focus →                │ │
│ └──────────────────────────────────────────┴──────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ LOWER PRIORITY: TEMPO POSTS (Lightweight Community Feed)                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Visual & Structural Invariants

1. **Top Context Bar:**
   - Interactive mode button: `[⚡ Urgent Mode ▾]`.
   - Formatted local date display.
   - **NO separate greeting hero banner** above the workspace.
   - **NO oversized decorative hero ring** or multi-line motivational banner.
   - Vertical whitespace must remain compact (`space-y-5`).

2. **Primary Execution Area (Left Column, ~65%):**
   - **Visual Emphasis:** Soft warm peach gradient (`bg-gradient-to-br from-[#FFF9F5] via-[#FFF3EB] to-[#FFEFE6]`), warm border (`border-2 border-[#FFD2BA]`), and subtle warm accent shapes (`bg-[#FF6B2C]/5 blur-2xl`).
   - Clearly stands out from the neutral white right column.
   - **Greeting Placement:** `Hi, {username} 👋` is placed **inside** this card directly below the badge row and above the task title.
   - **Greeting Hierarchy:** Visually secondary context (`text-xs sm:text-sm font-semibold text-[#6F6B68]`).
   - **Task Title Focus:** Task title is the primary visual anchor (`font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight`).
   - **Action Steps:** Actionable next step or subtask rendered directly below task title.
   - **Metadata Row:** Deadline, duration estimate, and step count.
   - **CTAs:** Primary `Focus on this task →` (launches Focus Zone with current task) and secondary `View task →` (opens Plan Workspace).

3. **Your Plan for Today (Right Column, ~35%):**
   - Clean, white structured card (`bg-white border border-[#EAE4DF] rounded-3xl`).
   - Progress bar and summary (`X of Y completed`).
   - `View / Edit Plan →` navigation link.
   - Vertical timeline with state badges: `Completed` (strikethrough), `NOW`, and `UP NEXT`.

4. **Dedicated Support Row:**
   - Positioned directly below the 65/35 execution workspace.
   - Left card: `Feeling overwhelmed?` offering `Quick Stress Relief` and `Breathing`.
   - Right card: `Focus now` offering `Start Focus →` (quick entry).

5. **Lower Priority Social Feed:**
   - Tempo Posts rendered as preview cards at the bottom.
   - Zero editorial blog categories or reading times.

6. **Prohibited Additions in Urgent Home:**
   - **DO NOT** inject generic `Tempo Tools` grid.
   - **DO NOT** inject `Learn & Solve` accordion or educational modules.
   - **DO NOT** inject `Self-Check` cards.
   - **DO NOT** inject generic account/guest invitation banners.

---

## 4. Urgent Mode Control & Dropdown

- **Interactive Trigger:** Button `#btn-home-mode-selector` with `aria-haspopup="true"`.
- **Destination Menu:** Popover menu `#home-mode-selector-dropdown`.
  - Lists valid switch destinations: **Recovery Mode**, **Unclear Mode**, and **Take a break from modes** (Default).
  - **Excludes Active Mode:** When already in Urgent Mode, Urgent Mode is not repeated in the dropdown.
  - **Excludes SOS:** SOS is an emergency safety hotline, not a Tempo operating mode.
  - Keyboard accessible: closes on `Escape` key or click outside.
- **Persistence:** Internal identifier remains `"emergency"`. Never store `mode = "urgent"` in `localStorage` or backend databases.

---

## 5. Urgent Home State Machine

Urgent Mode Home supports exactly seven defined states within the stable execution shell:

| State Key | Trigger Condition | Primary Left Card Presentation |
|---|---|---|
| `PLAN_INCOMPLETE` | Setup stage unfinished / plan unconfirmed | Warm card showing current setup step title with `Continue building my plan →` |
| `ACTIVE_TODAY` | Confirmed plan with tasks planned for today | Warm card `YOUR TASK FOR NOW` with internal greeting, task title, action step, and focus CTAs |
| `TODAY_COMPLETE` | All tasks planned for today completed | Warm card `TODAY'S WORK DONE` with internal greeting and next scheduled work preview |
| `NO_WORK_TODAY` | Confirmed plan, but no tasks scheduled for today | Warm card `SCHEDULE OVERVIEW` with internal greeting and next work date preview |
| `TIME_ENDED_WITH_INCOMPLETE_WORK` | Planned availability window expired with open work | Warm card `PLANNED WINDOW ENDED` with `Stop for today` and `Keep working` choices |
| `PLAN_STALE` | Past-date tasks remain incomplete without review | Warm card `SCHEDULE UPDATE NEEDED` listing overdue tasks with `Review & update plan →` |
| `PLAN_COMPLETE` | All planned tasks across all dates finished | Warm card `ACUTE CRISIS CLEARED` with `Shift to Recovery Mode →` recommendation |

### State Invariant Rules:
- States change only the **content of the primary card**.
- States **MUST NOT** replace Urgent Home with full-page takeover screens or giant warning/completion hero walls.
- States **MUST NOT** alter the outer 65/35 shell, top utility row, support row, or community feed.

---

## 6. Non-Visual Semantic Test Hooks
To enable durable testing without CSS class fragility or text lock-in, the following semantic attributes are maintained:
- `data-tempo-ui="urgent-home-shell"`: Outer container for Urgent Home.
- `data-tempo-ui="urgent-left-col"`: Left column (~65%).
- `data-tempo-ui="urgent-primary"`: Primary state card container.
- `data-tempo-ui="urgent-task-now"`: Active `YOUR TASK FOR NOW` card.
- `data-tempo-ui="urgent-plan-today"`: Right column (~35%) plan container.
- `data-tempo-ui="urgent-support"`: Dedicated support row.
- `data-tempo-ui="urgent-posts"`: Community posts section.
- `data-tempo-ui="mode-selector-btn"`: Interactive mode button.

---

## 7. Future Developer & AI Agent Rules

> [!IMPORTANT]
> **MANDATORY VERIFICATION:**
> Any future task modifying `mode.js`, Urgent Mode rendering, or shared home shell CSS **MUST** run:
> ```powershell
> & "python.exe" test_urgent_mode_contract.py
> ```
> If this test fails, the agent/developer **MUST NOT** resolve the failure by loosening, editing, or deleting this contract or the test. The implementation must be fixed to adhere to this contract.
>
> Changes to this contract require explicit written approval from the product owner.
