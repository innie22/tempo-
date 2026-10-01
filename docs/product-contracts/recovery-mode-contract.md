# PRODUCT CONTRACT: RECOVERY MODE

> **STATUS: APPROVED & FROZEN (DEVELOPMENT-TIME REGRESSION PROTECTION)**  
> **Target Audience:** Developers, AI Coding Agents, Product Reviewers  
> **Scope:** Runtime behavior, layout hierarchy, self-check semantics, recovery tools, and non-diagnostic philosophy.  
> **Internal Identifier:** `MODES.RECOVERY` / `"recovery"`.  
> **User-Facing UI Label:** `"Recovery Mode"`.

---

## 1. Core Principle & Purpose
Recovery Mode provides a quiet, low-pressure, supportive space for students recovering from burnout, overload, or acute deadline crunches.

- **Primary Goal:** Slow down, check in, rebuild a sustainable personal rhythm, and restore energy.
- **What Recovery Mode is NOT:**
  - **NOT** a productivity emergency mode or high-pressure triage tool.
  - **NOT** a "Recovery Plan" with mandatory task quotas.
  - **NOT** a diagnostic psychological evaluation or clinical assessment tool.
  - **NOT** a stress score, mental health grade, or shame-based streak monitor.
- **Guiding Tone:** Calm, Clear, Warm, Supportive, and Non-Judgmental.

---

## 2. Recovery Home Layout Hierarchy

Recovery Home employs a calm, supportive layout tailored to reflection and gradual recovery:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [🌱 Recovery Mode ▾]                                                 [Date] │
├─────────────────────────────────────────────────────────────────────────────┤
│ Optional Dismissible Intro Banner ("You're in Recovery Mode")               │
├──────────────────────────────────────────────┬──────────────────────────────┤
│ LEFT COLUMN (~65% on Desktop)                │ RIGHT COLUMN (~35%)          │
│                                              │                              │
│ 1. SELF-CHECK (Primary Hero Card)            │ 2. RECOVERY NOTE             │
│    - User-defined signs/trackers             │    - Private reflections     │
│    - Consistency (streak represents habit,   │    - Editable custom prompts │
│      never performance or shame)             │                              │
│    - One-click daily check-in                │ 3. RECENTLY                  │
│                                              │    - Honest personal history │
├──────────────────────────────────────────────┴──────────────────────────────┤
│ 4. WEEKLY REVIEW SHELL (Contextual when eligible weekly review is ready)    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. TODAY SECTION (Shared real tasks; honest empty state if nothing planned) │
├─────────────────────────────────────────────────────────────────────────────┤
│ 6. RECOVERY SHARED ECOSYSTEM                                                │
│    - Recovery Tools: Focus Zone, Quick Relief, Breathing, Standalone Break  │
│    - Learn & Solve (Stress Loop, Recovery Rhythm, Self-Compassion)          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 7. LOWER PRIORITY: TEMPO POSTS (Lightweight Community Feed)                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Visual Identity Invariants

1. **Palette & Atmosphere:**
   - Soft, natural, muted tones with sage/emerald accents (`bg-[#EDF7F1]`, `text-[#166545]`, `border-[#CDE9DA]`).
   - Clean stone backgrounds (`bg-[#FAFAF9]`).
2. **Prohibited Visual Treatments:**
   - **DO NOT** make the entire interface saturated green or clinical hospital-themed.
   - **DO NOT** use danger-red alerts for standard Recovery states.
   - **DO NOT** convert Recovery into a generic meditation/yoga novelty app with floating clouds or excessive pastel decorations.
   - **DO NOT** introduce a permanent, oversized decorative Recovery hero banner. Mode = Context.

---

## 4. Feature Invariants & Ethics

### A. Optional Setup & Exploration
- Recovery setup and onboarding are **STRICTLY OPTIONAL**.
- Users must never be forced through a mandatory "Recovery Plan" wizard.
- Exploration of Recovery tools (Breathing, Quick Relief, Focus Zone, Tempo Break) must remain immediately accessible without prior setup.

### B. Self-Check Semantics
- Self-check enables personal observation of self-defined signs and trackers over time.
- **NO DIAGNOSTIC SCORE:** The system must never calculate a mental-health index, burnout severity percentage, or clinical score.
- **NO SHAME-BASED STREAKS:** Streaks indicate personal consistency, not performance. Missed days must never be punished or highlighted with negative framing.

### C. Recovery Note
- Private, personal reflection space.
- Must never be converted into a public post, mandatory journal, or productivity rating.
- Custom prompt options must remain user-editable.
- Legitimate bug fixes to option management (e.g. "Add option does not work") are encouraged and preserve this contract.

### D. Weekly Review
- Weekly Review surfaces raw, objective self-check observations from the past week.
- The student evaluates their own week; the algorithm never renders a diagnostic verdict.
- Weekly Review is contextual and dismissible—never permanently forced.

### E. Recovery Pattern Engine
- Operates on a conservative, respectful interpretation model.
- Surfaces gentle observations based on the user's personal baseline.
- Must never claim medical certainty or infer psychological crises.
- Must never trigger automatic mode switching. Interpretation remains with the user.

### F. Mode Switching & Data Protection
- Switching out of Recovery Mode to Default, Urgent, or Unclear preserves all Recovery data.
- Returning to Recovery restores Self-Check history, Recovery Notes, and Weekly Review state intact.
- The application must never automatically switch modes based on wellbeing metrics.

### G. Strict SOS Separation
- **Recovery Mode is NOT SOS.**
- SOS is an independent, immediate-safety external support mechanism.
- SOS must never be relegated to a Recovery sub-mode or gated behind Recovery setup.
- Recovery must never log or surface user SOS history.

---

## 5. Non-Visual Semantic Test Hooks
- `data-tempo-ui="recovery-home-shell"`: Container for Recovery Home.
- `data-tempo-ui="recovery-self-check"`: Primary Self-Check card.
- `data-tempo-ui="recovery-note"`: Recovery Note card.
- `data-tempo-ui="recovery-recently"`: Recently card.
- `data-tempo-ui="recovery-weekly-review"`: Contextual Weekly Review container.
- `data-tempo-ui="recovery-today"`: Today task continuity section.
- `data-tempo-ui="recovery-tools"`: Recovery tools & Learn & Solve container.
- `data-tempo-ui="recovery-posts"`: Community posts section.
- `data-tempo-ui="mode-selector-btn"`: Mode trigger button.

---

## 6. Future Developer & AI Agent Rules

> [!IMPORTANT]
> **MANDATORY VERIFICATION:**
> Any future task modifying `mode.js`, `recoverySelfCheck.js`, `recoveryNote.js`, `weeklyReview.js`, or Recovery styling **MUST** run:
> ```powershell
> & "python.exe" test_recovery_mode_contract.py
> ```
> If this test fails, the agent/developer **MUST NOT** solve the failure by weakening, editing, or deleting this contract or the test. The implementation must be fixed to adhere to this contract.
>
> Changes to this contract require explicit written approval from the product owner.
