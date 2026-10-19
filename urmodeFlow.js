/**
 * Tempo Urmode Flow Controller
 * File: urmodeFlow.js
 * 
 * Implements the agreed Urmode entry, Working Plan, task execution,
 * reset, review, and adjustment flows:
 * 
 * 1. Explicit Entry & Reset Popup Trigger (Entry Home, Mode Dropdowns, Change Mode Modal)
 * 2. Three dynamic cases based on actual persisted plan state:
 *    - Case 1: First-time user / user without a Working Plan (Reset path, Build path, Close path)
 *    - Case 2: Existing Working Plan with no overdue tasks (Review summary -> Keep / Adjust)
 *    - Case 3: Existing Working Plan with overdue tasks (Review summary with OVERDUE flags, Dashboard overdue notice & completion)
 * 3. Quick task creation popup ("Finish & focus now" -> Focus Zone, X returns to dashboard)
 * 4. Working Plan Setup Flow completion -> "Your task for now" popup -> Break-task flow
 * 5. Break-task flow over Working Plan tool page -> Start working on your plan -> Focus Zone
 * 6. Non-destructive Working Plan Adjustment flow
 */

window.TempoUrmodeFlow = (function() {
    // -------------------------------------------------------------------------
    // INTERNAL STATE
    // -------------------------------------------------------------------------
    let shouldShowResetOnEntry = false;
    let activeModalView = null; // null | 'reset' | 'are_you_ready' | 'quick_task' | 'review_summary' | 'keep_plan_task' | 'breakdown' | 'start_working_plan' | 'select_another_task' | 'confirm_selected_task' | 'adjust_keep' | 'adjust_tasks' | 'adjust_time' | 'adjust_propose'
    
    let currentFlowCase = 'NO_PLAN'; // 'NO_PLAN' | 'PLAN_NO_OVERDUE' | 'PLAN_WITH_OVERDUE'
    let currentBreakdownTaskId = null;
    let processedBreakdownTaskIds = new Set();
    let selectedWorkTaskId = null;
    let isSubmitting = false;

    // AI Help & Subtask Inline Edit State
    let aiHelpLoading = false;
    let aiHelpError = null;
    let aiHelpSuccess = null;
    let aiConfirmReplace = null;
    let editingSubtaskId = null;

    // Adjustment flow in-memory draft
    let adjustmentDraft = {
        retainedTasks: [],
        newTasks: [],
        availabilityDays: [],
        proposedPlan: null
    };

    // Helper: Escape HTML
    function escapeHTML(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Helper: Format duration minutes into human-readable label
    function formatDuration(mins) {
        if (!mins || mins <= 0) return '30 min';
        const h = Math.floor(mins / 60);
        const m = mins % 60;
        if (h > 0 && m > 0) return `${h} hr ${m} min`;
        if (h > 0) return `${h} hr`;
        return `${m} min`;
    }

    // Helper: Human deadline
    function formatDeadline(dateStr, timeStr) {
        if (window.TempoI18n && typeof window.TempoI18n.formatDeadline === 'function') {
            return window.TempoI18n.formatDeadline(dateStr, timeStr);
        }
        if (!dateStr) return 'No fixed deadline';
        try {
            const [y, m, d] = dateStr.split('-').map(Number);
            const date = new Date(y, m - 1, d);
            const monthDay = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            if (timeStr) {
                return `${monthDay} · ${timeStr}`;
            }
            return monthDay;
        } catch (e) {
            return `${dateStr}${timeStr ? ' · ' + timeStr : ''}`;
        }
    }

    // -------------------------------------------------------------------------
    // PLAN CONTEXT & TASK UTILITIES
    // -------------------------------------------------------------------------

    function getActiveWorkingPlan() {
        let plan = null;
        if (window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            plan = window.TempoPlanStore.getActivePlan('emergency');
        }
        if (!plan && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            plan = window.TempoEmergencyFlow.getConfirmedPlan();
        }
        return plan;
    }

    function getAllPlanTasks(plan) {
        if (!plan) return [];
        const items = [];
        const seenIds = new Set();

        if (Array.isArray(plan.plannedTasks)) {
            plan.plannedTasks.forEach(pt => {
                if (pt && pt.task && pt.task.id && !seenIds.has(pt.task.id)) {
                    seenIds.add(pt.task.id);
                    items.push({
                        ...pt.task,
                        _dayDate: pt.dayDate || null,
                        _dayLabel: pt.dayLabel || null,
                        _startTime: pt.startTime || null,
                        _endTime: pt.endTime || null,
                        _executionBadge: pt.executionBadge || 'UP NEXT'
                    });
                }
            });
        }

        if (Array.isArray(plan.unarrangedTasks)) {
            plan.unarrangedTasks.forEach(u => {
                const t = (u && u.task) ? u.task : u;
                if (t && t.id && !seenIds.has(t.id)) {
                    seenIds.add(t.id);
                    items.push({
                        ...t,
                        _dayDate: null,
                        _dayLabel: null,
                        _startTime: null,
                        _endTime: null,
                        _executionBadge: 'Not scheduled'
                    });
                }
            });
        }

        if (Array.isArray(plan.tasks)) {
            plan.tasks.forEach(t => {
                if (t && t.id && !seenIds.has(t.id)) {
                    seenIds.add(t.id);
                    items.push({
                        ...t,
                        _dayDate: null,
                        _dayLabel: null,
                        _startTime: null,
                        _endTime: null,
                        _executionBadge: 'Not scheduled'
                    });
                }
            });
        }

        return items;
    }

    function isTaskOverdue(task, plan) {
        if (!task || task.completed === true) return false;

        const now = new Date();
        const pad = n => String(n).padStart(2, '0');
        const todayStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
        const currentTimeStr = `${pad(now.getHours())}:${pad(now.getMinutes())}`;

        // 1. Fixed deadline passed
        if (task.hasDeadline && task.deadlineDate) {
            if (task.deadlineDate < todayStr) return true;
            if (task.deadlineDate === todayStr && task.deadlineTime && task.deadlineTime < currentTimeStr) {
                return true;
            }
        }

        // 2. Scheduled date in plan passed without completion
        if (task._dayDate && task._dayDate < todayStr) {
            return true;
        }

        // Check plan.plannedTasks matching this task
        if (plan && Array.isArray(plan.plannedTasks)) {
            const pt = plan.plannedTasks.find(p => p.task && p.task.id === task.id);
            if (pt && pt.dayDate && pt.dayDate < todayStr) {
                return true;
            }
        }

        return false;
    }

    function determinePlanCase() {
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);

        if (!plan || tasks.length === 0) {
            currentFlowCase = 'NO_PLAN';
            return 'NO_PLAN';
        }

        const overdue = tasks.filter(t => isTaskOverdue(t, plan));
        if (overdue.length > 0) {
            currentFlowCase = 'PLAN_WITH_OVERDUE';
            return 'PLAN_WITH_OVERDUE';
        }

        currentFlowCase = 'PLAN_NO_OVERDUE';
        return 'PLAN_NO_OVERDUE';
    }

    // -------------------------------------------------------------------------
    // ENTRY TRIGGER & FLAG CONSUMPTION
    // -------------------------------------------------------------------------

    function queueResetPopup() {
        shouldShowResetOnEntry = true;
    }

    function shouldShowReset() {
        return shouldShowResetOnEntry;
    }

    function consumeResetFlag() {
        const flag = shouldShowResetOnEntry;
        shouldShowResetOnEntry = false;
        return flag;
    }

    // -------------------------------------------------------------------------
    // MODAL WRAPPER & DISMISSAL
    // -------------------------------------------------------------------------

    function getModalRoot() {
        let modal = document.getElementById('modal-urmode-flow');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'modal-urmode-flow';
            modal.className = 'fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-3 sm:p-6 overflow-y-auto hidden';
            modal.setAttribute('role', 'dialog');
            modal.setAttribute('aria-modal', 'true');
            document.body.appendChild(modal);
        }
        return modal;
    }

    function closeModal(destination = 'dashboard') {
        const modal = getModalRoot();
        modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
        activeModalView = null;
        isSubmitting = false;
        aiHelpLoading = false;
        aiHelpError = null;
        aiHelpSuccess = null;
        aiConfirmReplace = null;
        editingSubtaskId = null;

        if (destination === 'dashboard') {
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('today');
            }
            if (window.TempoMode && typeof window.TempoMode.renderEmodeHome === 'function') {
                window.TempoMode.renderEmodeHome();
            }
        } else if (destination === 'plan-workspace') {
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('plan-workspace');
            }
            if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
                window.TempoPlanWorkspace.render();
            }
        }
    }

    function showModalContent(html) {
        const modal = getModalRoot();
        modal.innerHTML = `
            <div class="tempo-card max-w-xl sm:max-w-2xl w-full my-auto bg-[#FEFAF4] rounded-3xl sm:rounded-[28px] p-6 sm:p-8 space-y-5 relative shadow-2xl border border-[#EAE4DF] animate-scale-up">
                ${html}
            </div>
        `;
        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    // -------------------------------------------------------------------------
    // 1. RESET POPUP (On Explicit Entry)
    // -------------------------------------------------------------------------

    function showResetPopup() {
        const caseType = determinePlanCase();
        activeModalView = 'reset';

        let badgeText = 'GROUNDED START';
        let titleText = 'Take a moment to reset?';
        let bodyText = "Urgent situations feel much lighter when you pause first. Would you like a 2-minute reset to calm your nervous system before organizing your tasks?";
        let primaryBtnText = 'Yes, take a quick reset';
        let secondaryBtnText = 'Build my plan';

        if (caseType === 'PLAN_NO_OVERDUE') {
            badgeText = 'WORKING PLAN ACTIVE';
            titleText = 'Review and reset your Working Plan';
            bodyText = 'You already have an active Working Plan saved. Take a 2-minute reset to ground your focus, or review and keep your existing plan.';
            secondaryBtnText = 'Review your plan';
        } else if (caseType === 'PLAN_WITH_OVERDUE') {
            badgeText = 'PLAN UPDATE NEEDED';
            titleText = 'Review and reset your Working Plan';
            bodyText = 'You have tasks with overdue deadlines that need your attention. Take a quick reset to calm down, or review your tasks and adjust your schedule.';
            secondaryBtnText = 'Review your plan';
        }

        const html = `
            <!-- Header -->
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${badgeText}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${titleText}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.handleResetClose()"
                        aria-label="Close dialog"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="Close and stay in Urmode">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Mascot & Body Row -->
            <div class="flex flex-col sm:flex-row items-center sm:items-start gap-4 py-2">
                <div class="w-20 h-20 rounded-2xl bg-[#FFE9DC] flex items-center justify-center shrink-0 shadow-xs">
                    <img src="assets/practice-breathing-mascot.png" alt="Reset Breathing" class="w-16 h-16 object-contain pointer-events-none select-none" />
                </div>
                <div class="space-y-2 text-center sm:text-left">
                    <p class="text-sm sm:text-base text-[#484541] leading-relaxed">
                        ${bodyText}
                    </p>
                    <div class="text-xs text-[#8C8782] flex items-center justify-center sm:justify-start gap-2 pt-1">
                        <span>🌱 2 min box breathing</span>
                        <span>•</span>
                        <span>Grounds focus</span>
                        <span>•</span>
                        <span>No rush</span>
                    </div>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.handleResetNoOrPlan()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                    ${secondaryBtnText}
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.handleResetYes()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                    <span>${primaryBtnText} →</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }

    function handleResetYes() {
        closeModal(null); // Keep modal open in background / don't reset dashboard
        if (window.TempoStressRelief && typeof window.TempoStressRelief.openBreathing === 'function') {
            window.TempoStressRelief.openBreathing({
                context: 'emergency_reset',
                onReady: () => {
                    showAreYouReadyPopup();
                }
            });
        } else {
            showAreYouReadyPopup();
        }
    }

    function handleResetNoOrPlan() {
        const caseType = determinePlanCase();
        closeModal(null);

        if (caseType === 'NO_PLAN') {
            startSetupFlow();
        } else {
            showReviewSummaryPopup();
        }
    }

    function handleResetClose() {
        closeModal('dashboard');
    }

    // -------------------------------------------------------------------------
    // 2. "ARE YOU READY?" POPUP (Post-Breathing Checkpoint)
    // -------------------------------------------------------------------------

    function showAreYouReadyPopup() {
        activeModalView = 'are_you_ready';
        const caseType = determinePlanCase();

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-emerald-700 block">
                        GROUNDED CHECKPOINT
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        Are you ready?
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        aria-label="Close dialog"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <div class="py-3 text-center sm:text-left space-y-2">
                <p class="text-sm sm:text-base text-[#484541] leading-relaxed">
                    You took a moment to breathe and reset. How do you feel about moving into your Working Plan now?
                </p>
                <p class="text-xs text-[#8C8782]">
                    If you still feel overwhelmed, you can return to take another pause or rest anytime.
                </p>
            </div>

            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.showResetPopup()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                    Not yet, return to reset
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.handleAreYouReadyYes()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                    <span>Yes, I'm ready →</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }

    let isHandlingAreYouReady = false;
    function handleAreYouReadyYes() {
        if (isHandlingAreYouReady) return;
        isHandlingAreYouReady = true;
        try {
            const caseType = determinePlanCase();
            closeModal(null);

            if (caseType === 'NO_PLAN') {
                startSetupFlow();
            } else {
                showReviewSummaryPopup();
            }
        } finally {
            setTimeout(() => { isHandlingAreYouReady = false; }, 300);
        }
    }

    // -------------------------------------------------------------------------
    // 3. START WORKING PLAN SETUP FLOW
    // -------------------------------------------------------------------------

    function startSetupFlow() {
        closeModal(null);
        if (window.TempoEmergencyFlow) {
            if (window.TempoEmergencyFlow.startFreshPlan) {
                window.TempoEmergencyFlow.startFreshPlan();
            }
            window.TempoEmergencyFlow.goToStage('reality-check');
        }
        if (window.TempoApp) {
            window.TempoApp.navigateTo('emergency');
        }
    }

    // -------------------------------------------------------------------------
    // 4. QUICK TASK CREATION POPUP
    // -------------------------------------------------------------------------

    function openQuickTaskModal() {
        activeModalView = 'quick_task';
        const now = new Date();
        const pad = n => String(n).padStart(2, '0');
        const defaultTime = `${pad((now.getHours() + 2) % 24)}:00`;
        const todayStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        QUICK TASK EXECUTION
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        Execute a task now
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        aria-label="Close dialog"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <form id="form-quick-task" onsubmit="window.TempoUrmodeFlow.handleQuickTaskSubmit(event)" class="space-y-4 py-2">
                <!-- Task Name -->
                <div class="space-y-1.5">
                    <label for="quick-task-name" class="block text-xs font-bold text-[#484541] uppercase tracking-wider">
                        Task Name <span class="text-rose-500">*</span>
                    </label>
                    <input type="text" id="quick-task-name" required autofocus
                           placeholder="e.g. Finish economics chapter 4 notes"
                           class="w-full px-4 py-2.5 rounded-xl border border-[#D1C7BD] bg-white text-sm text-[#202124] placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-[#D79277] focus:border-transparent transition" />
                </div>

                <!-- Duration Picker -->
                <div class="space-y-1.5">
                    <label class="block text-xs font-bold text-[#484541] uppercase tracking-wider">
                        Estimated Duration
                    </label>
                    <div class="flex flex-wrap items-center gap-2" id="quick-task-duration-group">
                        <button type="button" onclick="window.TempoUrmodeFlow.selectQuickDuration(15, this)"
                                class="quick-duration-pill px-3 py-1.5 rounded-full text-xs font-bold border border-stone-200 bg-white text-stone-700 hover:border-[#D79277] transition cursor-pointer">
                            15 min
                        </button>
                        <button type="button" onclick="window.TempoUrmodeFlow.selectQuickDuration(30, this)"
                                class="quick-duration-pill px-3 py-1.5 rounded-full text-xs font-bold border-2 border-[#D79277] bg-[#FFE9DC] text-[#B83D08] transition cursor-pointer">
                            30 min
                        </button>
                        <button type="button" onclick="window.TempoUrmodeFlow.selectQuickDuration(45, this)"
                                class="quick-duration-pill px-3 py-1.5 rounded-full text-xs font-bold border border-stone-200 bg-white text-stone-700 hover:border-[#D79277] transition cursor-pointer">
                            45 min
                        </button>
                        <button type="button" onclick="window.TempoUrmodeFlow.selectQuickDuration(60, this)"
                                class="quick-duration-pill px-3 py-1.5 rounded-full text-xs font-bold border border-stone-200 bg-white text-stone-700 hover:border-[#D79277] transition cursor-pointer">
                            1 hr
                        </button>
                    </div>
                    <input type="hidden" id="quick-task-duration" value="30" />
                </div>

                <!-- Optional Deadline -->
                <div class="space-y-2 pt-1 border-t border-stone-100">
                    <label class="inline-flex items-center space-x-2 cursor-pointer select-none">
                        <input type="checkbox" id="quick-task-has-deadline" onchange="window.TempoUrmodeFlow.toggleQuickDeadlineInputs(this.checked)"
                               class="w-4 h-4 rounded text-[#D79277] focus:ring-[#D79277] border-gray-300 cursor-pointer" />
                        <span class="text-xs font-semibold text-[#484541]">Add a deadline for this task</span>
                    </label>

                    <div id="quick-task-deadline-fields" class="hidden flex flex-wrap items-center gap-2 pt-1">
                        <input type="date" id="quick-task-deadline-date" value="${todayStr}"
                               class="px-3 py-1.5 rounded-xl border border-[#D1C7BD] text-xs font-medium text-[#202124] focus:ring-1 focus:ring-[#D79277] focus:outline-none" />
                        <input type="time" id="quick-task-deadline-time" value="${defaultTime}"
                               class="px-3 py-1.5 rounded-xl border border-[#D1C7BD] text-xs font-medium text-[#202124] focus:ring-1 focus:ring-[#D79277] focus:outline-none" />
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                    <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                            class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                        Cancel
                    </button>
                    <button type="submit" id="btn-quick-task-submit"
                            class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                        <span>Finish & focus now →</span>
                    </button>
                </div>
            </form>
        `;

        showModalContent(html);
    }

    function selectQuickDuration(mins, btn) {
        const input = document.getElementById('quick-task-duration');
        if (input) input.value = mins;
        document.querySelectorAll('.quick-duration-pill').forEach(el => {
            el.className = 'quick-duration-pill px-3 py-1.5 rounded-full text-xs font-bold border border-stone-200 bg-white text-stone-700 hover:border-[#D79277] transition cursor-pointer';
        });
        if (btn) {
            btn.className = 'quick-duration-pill px-3 py-1.5 rounded-full text-xs font-bold border-2 border-[#D79277] bg-[#FFE9DC] text-[#B83D08] transition cursor-pointer';
        }
    }

    function toggleQuickDeadlineInputs(checked) {
        const box = document.getElementById('quick-task-deadline-fields');
        if (box) {
            box.classList.toggle('hidden', !checked);
        }
    }

    function handleQuickTaskSubmit(e) {
        if (e) e.preventDefault();
        if (isSubmitting) return;

        const nameInput = document.getElementById('quick-task-name');
        const taskName = nameInput ? nameInput.value.trim() : '';
        if (!taskName) return;

        const durInput = document.getElementById('quick-task-duration');
        const durationMinutes = parseInt(durInput?.value || '30', 10) || 30;

        const hasDeadline = document.getElementById('quick-task-has-deadline')?.checked || false;
        const deadlineDate = hasDeadline ? document.getElementById('quick-task-deadline-date')?.value || null : null;
        const deadlineTime = hasDeadline ? document.getElementById('quick-task-deadline-time')?.value || null : null;

        isSubmitting = true;

        const now = new Date();
        const pad = n => String(n).padStart(2, '0');
        const todayStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

        const newTask = {
            id: 'task-quick-' + Date.now(),
            name: taskName,
            description: '',
            hasDeadline: Boolean(hasDeadline && deadlineDate),
            deadlineDate: deadlineDate,
            deadlineTime: deadlineTime,
            durationMinutes: durationMinutes,
            durationLabel: formatDuration(durationMinutes),
            completed: false,
            isInProgress: true,
            subtasks: []
        };

        // Persist task into confirmedPlan (or create a clean minimal Working Plan)
        let plan = getActiveWorkingPlan();
        if (!plan) {
            plan = {
                id: 'plan_quick_' + Date.now(),
                planId: 'plan_quick_' + Date.now(),
                planType: 'emergency',
                title: 'Working Plan',
                plannedTasks: [
                    {
                        dayDate: todayStr,
                        dayLabel: 'Today',
                        startTime: '10:00 AM',
                        endTime: '11:00 AM',
                        executionBadge: 'DO THIS FIRST',
                        task: newTask
                    }
                ],
                unarrangedTasks: [],
                tasks: [newTask],
                availabilityDays: [
                    { date: todayStr, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }
                ]
            };
        } else {
            if (!Array.isArray(plan.plannedTasks)) plan.plannedTasks = [];
            if (!Array.isArray(plan.tasks)) plan.tasks = [];

            plan.plannedTasks.unshift({
                dayDate: todayStr,
                dayLabel: 'Today',
                startTime: 'Now',
                executionBadge: 'DO THIS FIRST',
                task: newTask
            });
            plan.tasks.unshift(newTask);
        }

        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            window.TempoPlanStore.saveActivePlan('emergency', plan);
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
            window.TempoEmergencyFlow.setConfirmedPlan(plan);
        }

        closeModal('dashboard');

        // Launch Focus Zone for this quick task
        if (window.TempoFocusZone && typeof window.TempoFocusZone.open === 'function') {
            window.TempoFocusZone.open({ taskId: newTask.id });
        } else if (window.TempoMode && typeof window.TempoMode.startTaskFocus === 'function') {
            window.TempoMode.startTaskFocus(newTask.id);
        }
    }

    // -------------------------------------------------------------------------
    // 5. REVIEW SUMMARY POPUP (Existing Working Plan)
    // -------------------------------------------------------------------------

    function showReviewSummaryPopup() {
        activeModalView = 'review_summary';
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const overdueCount = tasks.filter(t => isTaskOverdue(t, plan)).length;

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        WORKING PLAN REVIEW
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        Your Working Plan Summary
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        aria-label="Close dialog"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Overdue Warning Banner if applicable -->
            ${overdueCount > 0 ? `
                <div class="p-3 bg-amber-50 border border-amber-200/80 rounded-2xl flex items-center space-x-3 text-xs text-amber-900">
                    <span class="text-base shrink-0">⚠️</span>
                    <div>
                        <strong class="font-bold">${overdueCount} task${overdueCount === 1 ? '' : 's'} overdue:</strong>
                        <span>Some tasks passed their planned date or deadline. You can keep them or adjust your schedule.</span>
                    </div>
                </div>
            ` : ''}

            <!-- Task List -->
            <div class="max-h-64 sm:max-h-72 overflow-y-auto space-y-2 pr-1 py-1">
                ${tasks.map((t, idx) => {
                    const overdue = isTaskOverdue(t, plan);
                    const deadlineStr = t.hasDeadline && t.deadlineDate ? formatDeadline(t.deadlineDate, t.deadlineTime) : 'No fixed deadline';
                    const durStr = t.durationLabel || formatDuration(t.durationMinutes);
                    const isDone = t.completed === true;

                    return `
                        <div class="p-3 rounded-2xl border ${overdue ? 'border-amber-300 bg-amber-50/40' : 'border-stone-200 bg-white'} flex items-center justify-between text-xs transition">
                            <div class="flex items-center space-x-2.5 min-w-0 flex-1 mr-2">
                                <span class="font-bold text-stone-400 w-5 shrink-0 text-center">${idx + 1}.</span>
                                <div class="min-w-0">
                                    <div class="font-bold text-stone-800 truncate ${isDone ? 'line-through text-stone-400' : ''}">
                                        ${escapeHTML(t.name)}
                                    </div>
                                    <div class="text-[11px] text-stone-500 flex items-center space-x-2 mt-0.5">
                                        <span>${escapeHTML(deadlineStr)}</span>
                                        <span>•</span>
                                        <span>~${escapeHTML(durStr)}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="flex items-center space-x-1.5 shrink-0">
                                ${overdue ? `
                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                                        OVERDUE
                                    </span>
                                ` : ''}
                                ${isDone ? `
                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700">
                                        ✓ Done
                                    </span>
                                ` : `
                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-stone-100 text-stone-600">
                                        ${escapeHTML(t._executionBadge || 'UP NEXT')}
                                    </span>
                                `}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>

            <!-- Action Buttons: Keep Plan vs Adjust Plan -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.startAdjustmentFlow()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                    Adjust my plan
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.showKeepPlanTaskPopup()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                    <span>Keep the plan →</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }

    function showKeepPlanTaskPopup() {
        activeModalView = 'keep_plan_task';
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const topTask = tasks.find(t => !t.completed) || tasks[0];

        if (!topTask) {
            closeModal('dashboard');
            return;
        }

        const deadlineStr = topTask.hasDeadline && topTask.deadlineDate ? formatDeadline(topTask.deadlineDate, topTask.deadlineTime) : 'No fixed deadline';
        const durStr = topTask.durationLabel || formatDuration(topTask.durationMinutes);
        const subtasks = Array.isArray(topTask.subtasks) ? topTask.subtasks : [];

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        YOUR TASK FOR NOW
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        Your task for now is…
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        aria-label="Close dialog"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Task Summary Card -->
            <div class="p-4 rounded-2xl border-2 border-[#D79277] bg-[#FFF9F5] space-y-2">
                <div class="flex items-center justify-between">
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#D79277] text-white">
                        DO THIS FIRST
                    </span>
                    <span class="text-xs text-stone-500 font-medium">~${escapeHTML(durStr)}</span>
                </div>
                <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124]">
                    ${escapeHTML(topTask.name)}
                </h3>
                <div class="text-xs text-[#6F6B68] flex items-center space-x-2">
                    <span>📅 Due: ${escapeHTML(deadlineStr)}</span>
                </div>

                ${subtasks.length > 0 ? `
                    <div class="pt-2 border-t border-stone-200/60 space-y-1">
                        <div class="text-[11px] font-bold uppercase tracking-wider text-stone-500">Action steps:</div>
                        ${subtasks.map(s => `
                            <div class="flex items-center space-x-2 text-xs text-stone-700">
                                <span>${s.completed ? '✓' : '○'}</span>
                                <span class="${s.completed ? 'line-through text-stone-400' : ''}">${escapeHTML(s.title)}</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>

            <!-- Action Buttons: Focus Now vs Later -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                    Later
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.launchFocusForTask('${topTask.id}')"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                    <span>Focus now →</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }

    function launchFocusForTask(taskId) {
        closeModal('dashboard');
        if (window.TempoFocusZone && typeof window.TempoFocusZone.open === 'function') {
            window.TempoFocusZone.open({ taskId });
        } else if (window.TempoMode && typeof window.TempoMode.startTaskFocus === 'function') {
            window.TempoMode.startTaskFocus(taskId);
        }
    }

    // -------------------------------------------------------------------------
    // 6. OVERDUE TASK ACTIONS ON DASHBOARD
    // -------------------------------------------------------------------------

    function markOverdueTaskFinished(taskId) {
        if (!taskId) return;
        if (window.TempoMode && typeof window.TempoMode.toggleTaskCompletion === 'function') {
            window.TempoMode.toggleTaskCompletion(taskId);
        } else if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.toggleTaskCompleted === 'function') {
            window.TempoEmergencyFlow.toggleTaskCompleted(taskId);
        }
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("Overdue task marked as finished.");
        }
        if (window.TempoMode && typeof window.TempoMode.renderEmodeHome === 'function') {
            window.TempoMode.renderEmodeHome();
        }
    }

    // -------------------------------------------------------------------------
    // 7. POST-SAVE "YOUR TASK FOR NOW" & BREAK-TASK FLOW
    // -------------------------------------------------------------------------

    function showTaskForNowPopupAfterSave(plan) {
        const confirmed = plan || getActiveWorkingPlan();
        const tasks = getAllPlanTasks(confirmed);
        const topTask = tasks.find(t => !t.completed) || tasks[0];

        if (!topTask) {
            closeModal('dashboard');
            return;
        }

        activeModalView = 'post_save_task_now';
        const durStr = topTask.durationLabel || formatDuration(topTask.durationMinutes);
        const deadlineStr = topTask.hasDeadline && topTask.deadlineDate ? formatDeadline(topTask.deadlineDate, topTask.deadlineTime) : 'No fixed deadline';
        const subtasks = Array.isArray(topTask.subtasks) ? topTask.subtasks : [];

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        PLAN CONFIRMED & SAVED
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        Your task for now
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        aria-label="Close dialog"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Task Highlight Card -->
            <div class="p-4 rounded-2xl border-2 border-[#D79277] bg-[#FFF9F5] space-y-2">
                <div class="flex items-center justify-between">
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#D79277] text-white">
                        DO THIS FIRST
                    </span>
                    <span class="text-xs text-stone-500 font-medium">~${escapeHTML(durStr)}</span>
                </div>
                <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124]">
                    ${escapeHTML(topTask.name)}
                </h3>
                <div class="text-xs text-[#6F6B68] flex items-center space-x-2">
                    <span>📅 Due: ${escapeHTML(deadlineStr)}</span>
                </div>

                ${subtasks.length > 0 ? `
                    <div class="pt-2 border-t border-stone-200/60 space-y-1">
                        <div class="text-[11px] font-bold uppercase tracking-wider text-stone-500">${subtasks.length} action step${subtasks.length === 1 ? '' : 's'}:</div>
                        ${subtasks.map((s, idx) => `
                            <div class="flex items-center space-x-2 text-xs text-stone-700">
                                <span>${s.completed ? '✓' : '○'}</span>
                                <span class="${s.completed ? 'line-through text-stone-400' : ''}">${escapeHTML(s.title)}</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>

            <!-- Question: Break down this task? -->
            <div class="py-2 space-y-1 text-center sm:text-left">
                <h4 class="font-bold text-sm sm:text-base text-stone-800">
                    Would you like to break down this task into smaller steps?
                </h4>
                <p class="text-xs text-stone-500">
                    Breaking big tasks into 10–15 min steps prevents freeze and makes starting effortless.
                </p>
            </div>

            <!-- Action Buttons -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.showStartWorkingPopup()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                    No, start working
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.startBreakTaskFlow('${topTask.id}')"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                    <span>Break down task →</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }

    function startBreakTaskFlow(firstTaskId) {
        processedBreakdownTaskIds = new Set();
        currentBreakdownTaskId = firstTaskId;
        aiHelpLoading = false;
        aiHelpError = null;
        aiHelpSuccess = null;
        aiConfirmReplace = null;
        editingSubtaskId = null;

        // Transition background to Working Plan tool page
        if (window.TempoApp) {
            window.TempoApp.navigateTo('plan-workspace');
        }

        // If guest user triggered sign-in modal, suppress it so breakdown popup remains primary
        const signInModal = document.getElementById('modal-sign-in');
        if (signInModal && !signInModal.classList.contains('hidden')) {
            signInModal.classList.add('hidden');
        }

        renderBreakTaskPopup(firstTaskId);
    }

    function renderBreakTaskPopup(taskId) {
        activeModalView = 'breakdown';
        currentBreakdownTaskId = taskId;

        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const task = tasks.find(t => String(t.id) === String(taskId)) || tasks[0];

        if (!task) {
            showStartWorkingPopup();
            return;
        }

        const subtasks = Array.isArray(task.subtasks) ? task.subtasks : [];
        const durStr = task.durationLabel || formatDuration(task.durationMinutes);

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        STEP BREAKDOWN
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        Break down: ${escapeHTML(task.name)}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('plan-workspace')"
                        aria-label="Close dialog"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="Close and stay in Working Plan">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Task Metadata & AI Action Button -->
            <div class="flex items-center justify-between gap-2 flex-wrap">
                <div class="text-xs text-stone-500 flex items-center space-x-2">
                    <span>⏱ Total estimate: ~${escapeHTML(durStr)}</span>
                    <span>•</span>
                    <span>Add 2 to 4 concrete action steps</span>
                </div>
                ${aiHelpLoading ? `
                    <button type="button" disabled id="btn-ai-help-breakdown"
                            class="px-2.5 py-1 rounded-lg text-xs font-bold text-[#B83D08] bg-[#FFE9DC] border border-[#FF6B2C]/30 flex items-center space-x-1.5 opacity-80 cursor-wait">
                        <svg class="animate-spin h-3.5 w-3.5 text-[#B83D08]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                        </svg>
                        <span>Thinking...</span>
                    </button>
                ` : `
                    <button type="button" id="btn-ai-help-breakdown" onclick="window.TempoUrmodeFlow.triggerAiHelp('${task.id}')"
                            class="px-2.5 py-1 rounded-lg text-xs font-bold text-[#B83D08] bg-[#FFE9DC] hover:bg-[#FFD2BA] transition flex items-center space-x-1.5 shadow-xs border border-[#FF6B2C]/30 cursor-pointer"
                            title="Get AI action step suggestions for this task">
                        <span>✨</span>
                        <span>AI Help</span>
                    </button>
                `}
            </div>

            <!-- AI Help Notice / Choice Banner -->
            ${aiHelpError ? `
                <div class="p-2.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center justify-between gap-2 animate-fade-in">
                    <div class="flex items-center space-x-1.5 min-w-0">
                        <span class="shrink-0">⚠️</span>
                        <span>${escapeHTML(aiHelpError)}</span>
                    </div>
                    <button type="button" onclick="window.TempoUrmodeFlow.dismissAiNotice()" class="text-rose-500 hover:text-rose-800 text-xs font-bold p-0.5 shrink-0 cursor-pointer">✕</button>
                </div>
            ` : ''}

            ${aiHelpSuccess ? `
                <div class="p-2.5 bg-[#FFF8F2] border border-[#FFD2BA] rounded-xl text-xs text-[#8B3814] flex items-center justify-between gap-2 animate-fade-in">
                    <div class="flex items-center space-x-1.5 min-w-0">
                        <span class="shrink-0">✨</span>
                        <span>${escapeHTML(aiHelpSuccess)}</span>
                    </div>
                    <button type="button" onclick="window.TempoUrmodeFlow.dismissAiNotice()" class="text-[#B83D08] hover:text-[#712708] text-xs font-bold p-0.5 shrink-0 cursor-pointer">✕</button>
                </div>
            ` : ''}

            ${aiConfirmReplace ? `
                <div class="p-3 bg-[#FFF8F2] border border-[#FFD2BA] rounded-xl text-xs text-[#8B3814] space-y-2 animate-fade-in">
                    <div class="flex items-center justify-between">
                        <span class="font-bold flex items-center space-x-1">
                            <span>✨</span>
                            <span>You already have ${subtasks.length} action steps</span>
                        </span>
                        <button type="button" onclick="window.TempoUrmodeFlow.dismissAiNotice()" class="text-stone-400 hover:text-stone-600 text-xs font-bold p-0.5 cursor-pointer">✕</button>
                    </div>
                    <p class="text-stone-600">Choose how you'd like to apply AI suggestions:</p>
                    <div class="flex flex-wrap items-center gap-2 pt-1">
                        <button type="button" onclick="window.TempoUrmodeFlow.applyAiAddMissing('${task.id}')"
                                class="px-2.5 py-1 rounded-lg bg-white border border-[#FF6B2C]/40 text-[#B83D08] font-bold text-xs hover:bg-[#FFE9DC] transition cursor-pointer">
                            + Add missing steps
                        </button>
                        <button type="button" onclick="window.TempoUrmodeFlow.applyAiReplaceAll('${task.id}')"
                                class="px-2.5 py-1 rounded-lg bg-[#FF6B2C] text-white font-bold text-xs hover:bg-[#B83D08] transition cursor-pointer">
                            Replace with AI steps
                        </button>
                    </div>
                </div>
            ` : ''}

            <!-- Subtask List -->
            <div class="space-y-2 max-h-52 overflow-y-auto pr-1" id="breakdown-subtask-list">
                ${subtasks.length === 0 ? `
                    <div class="p-3 bg-stone-50 rounded-xl text-xs text-stone-500 italic text-center">
                        No action steps added yet. Add your first step below or click ✨ AI Help.
                    </div>
                ` : subtasks.map((s, idx) => `
                    ${editingSubtaskId === s.id ? `
                        <div class="p-2 rounded-xl border border-[#FF6B2C] bg-[#FFFBF8] flex items-center gap-2 text-xs">
                            <span class="font-bold text-[#FF6B2C] shrink-0">${idx + 1}.</span>
                            <input type="text" id="edit-subtask-input-${s.id}" value="${escapeHTML(s.title)}"
                                   onkeydown="if(event.key==='Enter'){event.preventDefault();window.TempoUrmodeFlow.saveEditSubtask('${task.id}', '${s.id}');}else if(event.key==='Escape'){window.TempoUrmodeFlow.cancelEditSubtask();}"
                                   class="flex-1 px-2.5 py-1 rounded-lg border border-stone-300 text-xs text-stone-800 bg-white focus:outline-none focus:ring-1 focus:ring-[#FF6B2C]" />
                            <button type="button" onclick="window.TempoUrmodeFlow.saveEditSubtask('${task.id}', '${s.id}')"
                                    class="px-2.5 py-1 rounded-lg bg-[#FF6B2C] text-white font-bold text-[11px] hover:bg-[#B83D08] transition cursor-pointer shrink-0">
                                Save
                            </button>
                            <button type="button" onclick="window.TempoUrmodeFlow.cancelEditSubtask()"
                                    class="px-2 py-1 rounded-lg text-stone-500 hover:text-stone-800 text-[11px] font-semibold transition cursor-pointer shrink-0">
                                Cancel
                            </button>
                        </div>
                    ` : `
                        <div class="p-2.5 rounded-xl border border-stone-200 bg-white flex items-center justify-between text-xs group hover:border-stone-300 transition">
                            <label class="flex items-center space-x-2.5 flex-1 min-w-0 cursor-pointer select-none">
                                <input type="checkbox"
                                       id="breakdown-subtask-checkbox-${s.id}"
                                       ${s.completed ? 'checked' : ''}
                                       onclick="event.stopPropagation()"
                                       onchange="window.TempoUrmodeFlow.setSubtaskCompleted('${task.id}', '${s.id}', this.checked)"
                                       class="w-4 h-4 rounded border-stone-300 text-[#FF6B2C] focus:ring-[#FF6B2C] cursor-pointer shrink-0"
                                       title="${s.completed ? 'Mark step as incomplete' : 'Mark step as done'}">
                                <span class="font-medium text-xs truncate pr-2 transition ${s.completed ? 'line-through text-stone-400' : 'text-stone-800'}">
                                    ${idx + 1}. ${escapeHTML(s.title)}
                                </span>
                            </label>
                            <div class="flex items-center space-x-1 shrink-0">
                                <button type="button" onclick="window.TempoUrmodeFlow.startEditSubtask('${s.id}')"
                                        class="text-stone-400 hover:text-[#FF6B2C] transition cursor-pointer px-1 py-0.5 text-[11px] font-semibold"
                                        title="Edit step">
                                    Edit
                                </button>
                                <button type="button" onclick="window.TempoUrmodeFlow.removeSubtask('${task.id}', '${s.id}')"
                                        class="text-stone-400 hover:text-rose-600 transition cursor-pointer px-1 py-0.5"
                                        title="Remove step">
                                    ✕
                                </button>
                            </div>
                        </div>
                    `}
                `).join('')}
            </div>

            <!-- Add Subtask Input Form -->
            <div class="flex items-center space-x-2 pt-1">
                <input type="text" id="breakdown-subtask-input"
                       placeholder="e.g. Draft opening paragraph (15 min)"
                       onkeydown="if(event.key==='Enter'){event.preventDefault();window.TempoUrmodeFlow.addSubtask('${task.id}');}"
                       class="flex-1 px-3.5 py-2 rounded-xl border border-stone-300 text-xs text-stone-800 placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-[#D79277]" />
                <button type="button" onclick="window.TempoUrmodeFlow.addSubtask('${task.id}')"
                        class="px-4 py-2 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-700 font-bold text-xs transition cursor-pointer">
                    + Add step
                </button>
            </div>

            <!-- Actions Row: Do this task, Break more tasks, View my plan, Later -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-wrap items-center justify-between gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('plan-workspace')"
                        class="px-4 py-2 rounded-xl font-semibold text-xs text-stone-500 hover:text-stone-800 transition cursor-pointer">
                    Later
                </button>
                <div class="flex flex-wrap items-center gap-2 sm:gap-2.5">
                    <button type="button" id="btn-view-my-plan" onclick="window.TempoUrmodeFlow.viewMyPlan('${task.id}')"
                            class="px-4 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] hover:text-[#202124] border border-[#EAE4DF] shadow-2xs transition cursor-pointer">
                        View my plan
                    </button>
                    <button type="button" onclick="window.TempoUrmodeFlow.handleBreakMoreTasks('${task.id}')"
                            class="px-4 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs transition cursor-pointer">
                        Break more tasks →
                    </button>
                    <button type="button" onclick="window.TempoUrmodeFlow.launchFocusForTask('${task.id}')"
                            class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm transition cursor-pointer">
                        Do this task →
                    </button>
                </div>
            </div>
        `;

        showModalContent(html);
    }

    /**
     * Generates 2-4 concrete, small, actionable steps tailored to the given task context.
     */
    function generateTaskActionSteps(task) {
        if (!task) return [];
        const name = (task.name || task.title || '').trim();
        const desc = (task.description || task.notes || '').trim();
        const combined = (name + ' ' + desc).toLowerCase();

        let rawSuggestions = [];

        // 1. Math / Statistics / Problem Sets / Quantitative Homework
        if (/\b(statistic|stats|problem set|pset|math|calculus|algebra|physics|equation|formula|homework|exercise|quantitative)\b/.test(combined)) {
            rawSuggestions = [
                { title: 'Identify required problem numbers and review assignment criteria (15 min)', durationMinutes: 15 },
                { title: 'Review lecture notes and write down relevant formulas (20 min)', durationMinutes: 20 },
                { title: 'Solve the first problem step-by-step on scratch paper (25 min)', durationMinutes: 25 },
                { title: 'Check calculations and format final solutions (20 min)', durationMinutes: 20 }
            ];
        }
        // 2. Programming / Coding / Software / Debugging / Labs
        else if (/\b(code|coding|program|programming|bug|debug|lab|software|dev|github|script|algorithm|frontend|backend|api)\b/.test(combined)) {
            rawSuggestions = [
                { title: 'Review problem statement and expected inputs/outputs (15 min)', durationMinutes: 15 },
                { title: 'Outline core logic and pseudo-code on paper or in comments (20 min)', durationMinutes: 20 },
                { title: 'Implement working logic for first module and test locally (30 min)', durationMinutes: 30 },
                { title: 'Verify edge cases and prepare submission files (15 min)', durationMinutes: 15 }
            ];
        }
        // 3. Writing / Essays / Reports / Papers / Proposals / Literature Reviews
        else if (/\b(essay|paper|report|thesis|proposal|draft|write|writing|article|manuscript|dissertation)\b/.test(combined)) {
            rawSuggestions = [
                { title: 'Open prompt/rubric and paste outline into blank document (15 min)', durationMinutes: 15 },
                { title: 'Write 3 bullet points for each main section or argument (25 min)', durationMinutes: 25 },
                { title: 'Draft introduction and write the first body section (30 min)', durationMinutes: 30 },
                { title: 'Proofread flow, check word count, and verify citations (20 min)', durationMinutes: 20 }
            ];
        }
        // 4. Reading / Study / Textbooks / Literature
        else if (/\b(read|reading|chapter|book|textbook|literature|monograph)\b/.test(combined)) {
            rawSuggestions = [
                { title: 'Skim table of contents, headings, and chapter summary (10 min)', durationMinutes: 10 },
                { title: 'Read first half and highlight 3 core concepts (25 min)', durationMinutes: 25 },
                { title: 'Finish reading and draft short paragraph summary (20 min)', durationMinutes: 20 },
                { title: 'Review highlighted notes and prepare questions (10 min)', durationMinutes: 10 }
            ];
        }
        // 5. Exams / Quizzes / Tests / Midterm / Final Prep
        else if (/\b(exam|test|quiz|midterm|final|prep|revision)\b/.test(combined)) {
            rawSuggestions = [
                { title: 'Gather lecture notes, syllabus topics, and past exams (15 min)', durationMinutes: 15 },
                { title: 'Complete 3 practice questions without looking at solutions (30 min)', durationMinutes: 30 },
                { title: 'Review incorrect answers and clarify weak concepts (25 min)', durationMinutes: 25 },
                { title: 'Create a one-page summary sheet of key definitions (20 min)', durationMinutes: 20 }
            ];
        }
        // 6. Presentations / Slides / Talks / Speeches
        else if (/\b(presentation|slide|slides|deck|powerpoint|keynote|talk|speech|pitch)\b/.test(combined)) {
            rawSuggestions = [
                { title: 'Determine central message and outline 5 key slide topics (20 min)', durationMinutes: 20 },
                { title: 'Add bullet points, diagrams, and visual figures to slides (30 min)', durationMinutes: 30 },
                { title: 'Write speaker notes and talking transitions (15 min)', durationMinutes: 15 },
                { title: 'Conduct one uninterrupted rehearsal out loud (15 min)', durationMinutes: 15 }
            ];
        }
        // 7. Email / Correspondence / Applications
        else if (/\b(email|mail|message|contact|advisor|prof|professor|apply|application|form|submit)\b/.test(combined)) {
            rawSuggestions = [
                { title: 'Draft 3-sentence message stating main question clearly (10 min)', durationMinutes: 10 },
                { title: 'Attach necessary documents and verify recipient address (5 min)', durationMinutes: 5 },
                { title: 'Review tone and proofread before sending (5 min)', durationMinutes: 5 }
            ];
        }
        // 8. General task fallback (customized using task name)
        else {
            const cleanName = name || 'task';
            rawSuggestions = [
                { title: `Gather materials and review guidelines for "${cleanName}" (15 min)`, durationMinutes: 15 },
                { title: `Complete the first 25 minutes of focused work on "${cleanName}" (25 min)`, durationMinutes: 25 },
                { title: `Review progress and address remaining items (20 min)`, durationMinutes: 20 },
                { title: `Do final review and prepare for completion (15 min)`, durationMinutes: 15 }
            ];
        }

        // Adjust durations if task has a total duration
        if (typeof task.durationMinutes === 'number' && task.durationMinutes > 0 && rawSuggestions.length > 0) {
            const totalEst = task.durationMinutes;
            const portion = Math.max(5, Math.round(totalEst / rawSuggestions.length / 5) * 5);
            rawSuggestions.forEach(s => {
                s.durationMinutes = portion;
            });
        }

        return rawSuggestions;
    }

    /**
     * Centralized subtask persistence helper ensuring in-memory plan and stores stay synchronized.
     */
    function saveTaskSubtasks(plan, taskId, subtasks) {
        if (!plan) plan = getActiveWorkingPlan();
        if (!plan) return;

        let targetTask = null;
        if (Array.isArray(plan.plannedTasks)) {
            const pt = plan.plannedTasks.find(p => p.task && String(p.task.id) === String(taskId));
            if (pt) targetTask = pt.task;
        }
        if (!targetTask && Array.isArray(plan.tasks)) {
            targetTask = plan.tasks.find(t => String(t.id) === String(taskId));
        }
        if (!targetTask && Array.isArray(plan.unarrangedTasks)) {
            targetTask = plan.unarrangedTasks.find(t => {
                const tObj = (t && t.task) ? t.task : t;
                return tObj && String(tObj.id) === String(taskId);
            });
            if (targetTask && targetTask.task) targetTask = targetTask.task;
        }

        if (targetTask) {
            targetTask.subtasks = subtasks;

            if (Array.isArray(plan.tasks)) {
                const tMatch = plan.tasks.find(t => String(t.id) === String(taskId));
                if (tMatch && tMatch !== targetTask) {
                    tMatch.subtasks = subtasks;
                }
            }

            if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
                window.TempoPlanStore.saveActivePlan('emergency', plan);
                window.TempoPlanStore.updateTaskState(taskId, { subtasks: subtasks });
            }
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                window.TempoEmergencyFlow.setConfirmedPlan(plan);
            }
        }
    }

    /**
     * AI Help Trigger: Generates tailored action steps with loading and duplicate-checking behavior.
     */
    async function triggerAiHelp(taskId) {
        if (aiHelpLoading) return;

        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const task = tasks.find(t => String(t.id) === String(taskId)) || tasks[0];
        if (!task) return;

        aiHelpLoading = true;
        aiHelpError = null;
        aiHelpSuccess = null;
        aiConfirmReplace = null;
        renderBreakTaskPopup(taskId);

        // Breathing delay for clear visual feedback of loading state
        await new Promise(r => setTimeout(r, 300));

        try {
            const suggestions = generateTaskActionSteps(task);
            if (!Array.isArray(suggestions) || suggestions.length === 0) {
                throw new Error("No suggestions could be generated.");
            }

            const existingSteps = Array.isArray(task.subtasks) ? task.subtasks : [];

            if (existingSteps.length === 0) {
                // No existing steps: add suggestions directly
                const newSteps = suggestions.map((s, idx) => ({
                    id: 'sub-ai-' + Date.now() + '-' + idx,
                    title: s.title,
                    durationMinutes: s.durationMinutes || null,
                    completed: false
                }));

                saveTaskSubtasks(plan, taskId, newSteps);
                aiHelpLoading = false;
                aiHelpSuccess = `Added ${newSteps.length} action steps tailored to this task.`;
                renderBreakTaskPopup(taskId);
            } else {
                // Existing steps present: avoid duplicates
                const normalize = str => (str || '').toLowerCase().replace(/[^a-z0-9]/g, '');
                const existingNormalized = existingSteps.map(s => normalize(s.title));

                const missingSuggestions = suggestions.filter(s => {
                    const norm = normalize(s.title);
                    return !existingNormalized.some(eNorm => eNorm.includes(norm) || norm.includes(eNorm));
                });

                if (missingSuggestions.length > 0) {
                    if (existingSteps.length + missingSuggestions.length <= 4) {
                        // Few existing steps: add missing steps directly without duplicating
                        const newSteps = [
                            ...existingSteps,
                            ...missingSuggestions.map((s, idx) => ({
                                id: 'sub-ai-' + Date.now() + '-' + idx,
                                title: s.title,
                                durationMinutes: s.durationMinutes || null,
                                completed: false
                            }))
                        ];
                        saveTaskSubtasks(plan, taskId, newSteps);
                        aiHelpLoading = false;
                        aiHelpSuccess = `Added ${missingSuggestions.length} new step${missingSuggestions.length > 1 ? 's' : ''}. Existing steps were kept.`;
                        renderBreakTaskPopup(taskId);
                    } else {
                        // Several steps already exist: present clear choice
                        aiHelpLoading = false;
                        aiConfirmReplace = { taskId, suggestions, missingSuggestions };
                        renderBreakTaskPopup(taskId);
                    }
                } else {
                    // All generated steps are already represented
                    aiHelpLoading = false;
                    aiHelpSuccess = `All suggested steps are already present in your list.`;
                    renderBreakTaskPopup(taskId);
                }
            }
        } catch (err) {
            console.error('[TempoUrmodeFlow] AI Help generation error:', err);
            aiHelpLoading = false;
            aiHelpError = "AI suggestions couldn't be generated right now. You can add steps manually below.";
            renderBreakTaskPopup(taskId);
        }
    }

    function applyAiAddMissing(taskId) {
        if (!aiConfirmReplace || !aiConfirmReplace.missingSuggestions) {
            dismissAiNotice();
            return;
        }
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const task = tasks.find(t => String(t.id) === String(taskId));
        if (!task) return;

        const existingSteps = Array.isArray(task.subtasks) ? task.subtasks : [];
        const toAdd = aiConfirmReplace.missingSuggestions.slice(0, Math.max(1, 4 - existingSteps.length));
        const newSteps = [
            ...existingSteps,
            ...toAdd.map((s, idx) => ({
                id: 'sub-ai-' + Date.now() + '-' + idx,
                title: s.title,
                durationMinutes: s.durationMinutes || null,
                completed: false
            }))
        ];

        saveTaskSubtasks(plan, taskId, newSteps);
        aiConfirmReplace = null;
        aiHelpSuccess = `Added ${toAdd.length} missing step${toAdd.length > 1 ? 's' : ''}.`;
        renderBreakTaskPopup(taskId);
    }

    function applyAiReplaceAll(taskId) {
        if (!aiConfirmReplace || !aiConfirmReplace.suggestions) {
            dismissAiNotice();
            return;
        }
        const plan = getActiveWorkingPlan();
        const newSteps = aiConfirmReplace.suggestions.map((s, idx) => ({
            id: 'sub-ai-' + Date.now() + '-' + idx,
            title: s.title,
            durationMinutes: s.durationMinutes || null,
            completed: false
        }));

        saveTaskSubtasks(plan, taskId, newSteps);
        aiConfirmReplace = null;
        aiHelpSuccess = `Replaced steps with ${newSteps.length} fresh AI suggestions.`;
        renderBreakTaskPopup(taskId);
    }

    function dismissAiNotice() {
        aiHelpError = null;
        aiHelpSuccess = null;
        aiConfirmReplace = null;
        renderBreakTaskPopup(currentBreakdownTaskId);
    }

    function startEditSubtask(subtaskId) {
        editingSubtaskId = subtaskId;
        renderBreakTaskPopup(currentBreakdownTaskId);
        setTimeout(() => {
            const input = document.getElementById('edit-subtask-input-' + subtaskId);
            if (input) {
                input.focus();
                input.select();
            }
        }, 50);
    }

    function saveEditSubtask(taskId, subtaskId) {
        const input = document.getElementById('edit-subtask-input-' + subtaskId);
        const newTitle = input ? input.value.trim() : '';
        if (!newTitle) return;

        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const task = tasks.find(t => String(t.id) === String(taskId));
        if (!task || !Array.isArray(task.subtasks)) return;

        const updated = task.subtasks.map(s => {
            if (String(s.id) === String(subtaskId)) {
                return { ...s, title: newTitle };
            }
            return s;
        });

        saveTaskSubtasks(plan, taskId, updated);
        editingSubtaskId = null;
        renderBreakTaskPopup(taskId);
    }

    function cancelEditSubtask() {
        editingSubtaskId = null;
        renderBreakTaskPopup(currentBreakdownTaskId);
    }

    function addSubtask(taskId) {
        const input = document.getElementById('breakdown-subtask-input');
        const text = input ? input.value.trim() : '';
        if (!text) return;

        const plan = getActiveWorkingPlan();
        if (!plan) return;

        const tasks = getAllPlanTasks(plan);
        const task = tasks.find(t => String(t.id) === String(taskId));
        if (!task) return;

        const existing = Array.isArray(task.subtasks) ? task.subtasks : [];
        const newSteps = [
            ...existing,
            {
                id: 'sub-' + Date.now() + '-' + Math.random().toString(36).substr(2, 4),
                title: text,
                completed: false
            }
        ];

        saveTaskSubtasks(plan, taskId, newSteps);
        aiHelpError = null;
        aiHelpSuccess = null;
        aiConfirmReplace = null;
        editingSubtaskId = null;
        renderBreakTaskPopup(taskId);
    }

    function removeSubtask(taskId, subtaskId) {
        const plan = getActiveWorkingPlan();
        if (!plan) return;

        const tasks = getAllPlanTasks(plan);
        const task = tasks.find(t => String(t.id) === String(taskId));
        if (!task || !Array.isArray(task.subtasks)) return;

        const newSteps = task.subtasks.filter(s => String(s.id) !== String(subtaskId));
        saveTaskSubtasks(plan, taskId, newSteps);
        aiHelpError = null;
        aiHelpSuccess = null;
        aiConfirmReplace = null;
        editingSubtaskId = null;
        renderBreakTaskPopup(taskId);
    }

    async function setSubtaskCompleted(taskId, subtaskId, isCompleted) {
        if (!taskId || !subtaskId) return;
        const targetCompleted = Boolean(isCompleted);

        const plan = getActiveWorkingPlan();
        if (!plan) return;

        const tasks = getAllPlanTasks(plan);
        const task = tasks.find(t => String(t.id) === String(taskId));
        if (!task || !Array.isArray(task.subtasks)) return;

        const sub = task.subtasks.find(s => String(s.id) === String(subtaskId));
        if (sub) {
            sub.completed = targetCompleted;
            saveTaskSubtasks(plan, taskId, task.subtasks);

            if (window.TempoPlanStore && typeof window.TempoPlanStore.updateSubtaskState === 'function') {
                await window.TempoPlanStore.updateSubtaskState(taskId, subtaskId, { completed: targetCompleted });
            }

            // Sync with mode.js active home if present
            if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
                window.TempoMode.renderActiveModeHome();
            }

            // Re-render break task popup
            renderBreakTaskPopup(taskId);
        }
    }

    function refreshBreakTaskSubtasks(taskId) {
        if (activeModalView === 'breakdown' && (!taskId || String(currentBreakdownTaskId) === String(taskId))) {
            renderBreakTaskPopup(currentBreakdownTaskId);
        }
    }

    function handleBreakMoreTasks(currentId) {
        processedBreakdownTaskIds.add(String(currentId));

        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const nextEligible = tasks.find(t => !t.completed && !processedBreakdownTaskIds.has(String(t.id)) && !processedBreakdownTaskIds.has(t.id));

        if (nextEligible) {
            renderBreakTaskPopup(nextEligible.id);
        } else {
            showStartWorkingPopup();
        }
    }

    function viewMyPlan(taskId) {
        closeModal('plan-workspace');
    }

    // -------------------------------------------------------------------------
    // 8. "START WORKING ON YOUR PLAN" POPUP & TASK SELECTION
    // -------------------------------------------------------------------------

    function showStartWorkingPopup() {
        activeModalView = 'start_working_plan';
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const topTask = tasks.find(t => !t.completed) || tasks[0];

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        READY TO WORK
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        Start working on your plan?
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('plan-workspace')"
                        aria-label="Close dialog"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="Close and stay in Working Plan">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <div class="py-3 text-center sm:text-left space-y-2">
                <p class="text-sm sm:text-base text-[#484541] leading-relaxed">
                    Your working plan is ready. Would you like to start right away on your first task?
                </p>
                ${topTask ? `
                    <div class="p-3 bg-[#FFF9F5] border border-[#FFD2BA] rounded-2xl flex items-center justify-between text-xs">
                        <span class="font-bold text-[#202124]">First task: ${escapeHTML(topTask.name)}</span>
                        <span class="text-[#8C8782]">~${escapeHTML(topTask.durationLabel || formatDuration(topTask.durationMinutes))}</span>
                    </div>
                ` : ''}
            </div>

            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-wrap items-center justify-between gap-3">
                <div class="flex items-center space-x-2">
                    <button type="button" onclick="window.TempoUrmodeFlow.closeModal('plan-workspace')"
                            class="px-4 py-2 rounded-xl font-semibold text-xs text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        Later
                    </button>
                    <button type="button" onclick="window.TempoUrmodeFlow.restartBreakdownFlow()"
                            class="px-4 py-2 rounded-xl font-semibold text-xs text-[#D79277] hover:underline transition cursor-pointer">
                        Break more tasks
                    </button>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.showFirstTaskExecutionPopup()"
                        class="btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center space-x-2 transition cursor-pointer">
                    <span>Yes, start working →</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }

    function restartBreakdownFlow() {
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const nextUnbroken = tasks.find(t => !t.completed && (!Array.isArray(t.subtasks) || t.subtasks.length === 0));
        const target = nextUnbroken || tasks.find(t => !t.completed) || tasks[0];
        if (target) {
            renderBreakTaskPopup(target.id);
        } else {
            closeModal('plan-workspace');
        }
    }

    function showFirstTaskExecutionPopup() {
        activeModalView = 'first_task_choice';
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const topTask = (selectedWorkTaskId && tasks.find(t => String(t.id) === String(selectedWorkTaskId))) || tasks.find(t => !t.completed) || tasks[0];

        if (!topTask) {
            closeModal('plan-workspace');
            return;
        }

        const durStr = topTask.durationLabel || formatDuration(topTask.durationMinutes);
        const deadlineStr = topTask.hasDeadline && topTask.deadlineDate ? formatDeadline(topTask.deadlineDate, topTask.deadlineTime) : 'No fixed deadline';
        const subtasks = Array.isArray(topTask.subtasks) ? topTask.subtasks : [];

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        FIRST TASK EXECUTION
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        Your first task is…
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('plan-workspace')"
                        aria-label="Close dialog"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="Close and stay in Working Plan">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Task Card -->
            <div class="p-4 rounded-2xl border-2 border-[#D79277] bg-[#FFF9F5] space-y-2">
                <div class="flex items-center justify-between">
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#D79277] text-white">
                        READY NOW
                    </span>
                    <span class="text-xs text-stone-500 font-medium">~${escapeHTML(durStr)}</span>
                </div>
                <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124]">
                    ${escapeHTML(topTask.name)}
                </h3>
                <div class="text-xs text-[#6F6B68] flex items-center space-x-2">
                    <span>📅 Due: ${escapeHTML(deadlineStr)}</span>
                </div>
                ${subtasks.length > 0 ? `
                    <div class="pt-2 border-t border-stone-200/60 space-y-1">
                        <div class="text-[11px] font-bold uppercase tracking-wider text-stone-500">${subtasks.length} step${subtasks.length === 1 ? '' : 's'}:</div>
                        ${subtasks.slice(0, 3).map((s, i) => `
                            <div class="text-xs text-stone-700 truncate">• ${escapeHTML(s.title)}</div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>

            <!-- Action Buttons: Do this task, Choose another task, Later -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-wrap items-center justify-between gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('plan-workspace')"
                        class="px-4 py-2 rounded-xl font-semibold text-xs text-stone-500 hover:text-stone-800 transition cursor-pointer">
                    Later
                </button>
                <div class="flex items-center space-x-2.5">
                    <button type="button" onclick="window.TempoUrmodeFlow.showTaskSelectionPopup()"
                            class="px-4 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs transition cursor-pointer">
                        Choose another task
                    </button>
                    <button type="button" onclick="window.TempoUrmodeFlow.launchFocusForTask('${topTask.id}')"
                            class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm transition cursor-pointer">
                        Do this task →
                    </button>
                </div>
            </div>
        `;

        showModalContent(html);
    }

    function showTaskSelectionPopup() {
        activeModalView = 'select_another_task';
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan).filter(t => !t.completed);

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        TASK SELECTION
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        Select a task to work on
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.showFirstTaskExecutionPopup()"
                        aria-label="Back"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer">
                    ←
                </button>
            </div>

            <div class="max-h-64 overflow-y-auto space-y-2 pr-1 py-1">
                ${tasks.map((t, idx) => `
                    <div onclick="window.TempoUrmodeFlow.selectWorkTaskAndConfirm('${t.id}')"
                         class="p-3 rounded-2xl border border-stone-200 bg-white hover:border-[#D79277] hover:bg-[#FFF9F5] transition cursor-pointer flex items-center justify-between text-xs">
                        <div class="flex items-center space-x-2.5 min-w-0 flex-1 mr-2">
                            <span class="font-bold text-stone-400 w-5 shrink-0 text-center">${idx + 1}.</span>
                            <div class="min-w-0">
                                <div class="font-bold text-stone-800 truncate">${escapeHTML(t.name)}</div>
                                <div class="text-[11px] text-stone-500">~${escapeHTML(t.durationLabel || formatDuration(t.durationMinutes))}</div>
                            </div>
                        </div>
                        <span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-stone-100 text-stone-700 shrink-0">
                            Select →
                        </span>
                    </div>
                `).join('')}
            </div>

            <div class="pt-4 border-t border-[#EAE4DF]/80 flex justify-end">
                <button type="button" onclick="window.TempoUrmodeFlow.showFirstTaskExecutionPopup()"
                        class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs transition cursor-pointer">
                    Back
                </button>
            </div>
        `;

        showModalContent(html);
    }

    function selectWorkTaskAndConfirm(taskId) {
        selectedWorkTaskId = taskId;
        showFirstTaskExecutionPopup();
    }

    // -------------------------------------------------------------------------
    // 9. WORKING PLAN ADJUSTMENT FLOW (Non-Destructive until saved)
    // -------------------------------------------------------------------------

    function getTaskDueDateISO(task) {
        if (!task) return '';
        if (task.deadlineDate && typeof task.deadlineDate === 'string') {
            const trimmed = task.deadlineDate.trim();
            if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) return trimmed;
        }
        if (task.deadline && typeof task.deadline === 'string') {
            const datePart = task.deadline.split(' ')[0].trim();
            if (/^\d{4}-\d{2}-\d{2}$/.test(datePart)) return datePart;
        }
        return '';
    }

    function startAdjustmentFlow() {
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);

        // Pre-populate adjustment draft with existing plan tasks (preserving all IDs and state)
        adjustmentDraft = {
            originalPlan: plan,
            retainedTasks: tasks.map(t => {
                const dateIso = getTaskDueDateISO(t);
                return {
                    ...t,
                    _keep: true,
                    hasDeadline: Boolean(dateIso && t.hasDeadline !== false),
                    deadlineDate: dateIso || null,
                    deadlineTime: t.deadlineTime || (dateIso ? '23:59' : null),
                    deadline: dateIso ? `${dateIso} ${t.deadlineTime || '23:59'}` : null
                };
            }),
            newTasks: [],
            availabilityDays: (plan && Array.isArray(plan.availabilityDays)) ? JSON.parse(JSON.stringify(plan.availabilityDays)) : [],
            proposedPlan: null
        };

        renderAdjustmentStep1Keep();
    }

    // Step 1: Choose which existing tasks to keep
    function renderAdjustmentStep1Keep() {
        activeModalView = 'adjust_keep';
        const tasks = adjustmentDraft.retainedTasks;

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        STEP 1 OF 3 • ADJUST PLAN
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        Choose tasks to keep
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        aria-label="Cancel adjustment"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="Cancel adjustment (keeps existing plan)">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <p class="text-xs sm:text-sm text-stone-600">
                Select the tasks you still need to complete. Overdue or completed tasks can be removed or kept.
            </p>

            <div class="max-h-60 overflow-y-auto space-y-2 pr-1 py-1">
                ${tasks.map(t => {
                    const overdue = isTaskOverdue(t, adjustmentDraft.originalPlan);
                    return `
                        <label class="p-3 rounded-2xl border ${overdue ? 'border-amber-300 bg-amber-50/40' : 'border-stone-200 bg-white'} flex items-center justify-between text-xs cursor-pointer select-none">
                            <div class="flex items-center space-x-2.5 min-w-0 flex-1 mr-2">
                                <input type="checkbox" ${t._keep ? 'checked' : ''}
                                       onchange="window.TempoUrmodeFlow.toggleRetainedTask('${t.id}', this.checked)"
                                       class="w-4 h-4 rounded text-[#D79277] focus:ring-[#D79277] border-gray-300 cursor-pointer" />
                                <div class="min-w-0">
                                    <span class="font-bold text-stone-800 truncate block">${escapeHTML(t.name)}</span>
                                    <span class="text-[11px] text-stone-500">~${escapeHTML(t.durationLabel || formatDuration(t.durationMinutes))}</span>
                                </div>
                            </div>
                            ${overdue ? `
                                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200 shrink-0">
                                    OVERDUE
                                </span>
                            ` : ''}
                        </label>
                    `;
                }).join('')}
            </div>

            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-between gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs transition cursor-pointer">
                    Cancel adjustment
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.renderAdjustmentStep2Tasks()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm transition cursor-pointer">
                    Next: Adjust & add tasks →
                </button>
            </div>
        `;

        showModalContent(html);
    }

    function toggleRetainedTask(taskId, isKept) {
        const item = adjustmentDraft.retainedTasks.find(t => String(t.id) === String(taskId));
        if (item) {
            item._keep = isKept;
        }
    }

    // Step 2: Adjust retained tasks & add new tasks
    function renderAdjustmentStep2Tasks() {
        activeModalView = 'adjust_tasks';
        const kept = adjustmentDraft.retainedTasks.filter(t => t._keep);

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        STEP 2 OF 3 • ADJUST PLAN
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        Adjust estimates & add new tasks
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.handleAdjustmentStep2Back()"
                        aria-label="Back"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer">
                    ←
                </button>
            </div>

            <!-- Retained tasks list -->
            <div class="space-y-2 max-h-56 sm:max-h-60 overflow-y-auto pr-1 py-1">
                <div class="text-[11px] font-bold uppercase tracking-wider text-stone-500">Retained Tasks (${kept.length}):</div>
                ${kept.map(t => `
                    <div class="p-3 rounded-2xl border border-stone-200 bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 text-xs">
                        <div class="min-w-0 flex-1">
                            <span class="font-bold text-stone-800 truncate block">${escapeHTML(t.name)}</span>
                        </div>
                        <div class="flex items-center gap-2 shrink-0 flex-wrap">
                            <div class="flex items-center space-x-1.5">
                                <label for="adjust-due-${t.id}" class="text-[11px] font-semibold text-stone-500">Due:</label>
                                <input type="date"
                                       id="adjust-due-${t.id}"
                                       value="${t.deadlineDate || ''}"
                                       onchange="window.TempoUrmodeFlow.updateRetainedDueDate('${t.id}', this.value)"
                                       oninput="window.TempoUrmodeFlow.updateRetainedDueDate('${t.id}', this.value)"
                                       class="px-2.5 py-1.5 rounded-xl border border-stone-300 text-xs text-stone-700 bg-white focus:outline-none focus:ring-1 focus:ring-[#D79277]" />
                            </div>
                            <select id="adjust-dur-${t.id}"
                                    onchange="window.TempoUrmodeFlow.updateRetainedDuration('${t.id}', this.value)"
                                    class="px-2.5 py-1.5 rounded-xl border border-stone-300 text-xs font-medium text-stone-700 bg-white focus:outline-none focus:ring-1 focus:ring-[#D79277]">
                                <option value="15" ${t.durationMinutes === 15 ? 'selected' : ''}>15 min</option>
                                <option value="30" ${t.durationMinutes === 30 ? 'selected' : ''}>30 min</option>
                                <option value="45" ${t.durationMinutes === 45 ? 'selected' : ''}>45 min</option>
                                <option value="60" ${t.durationMinutes === 60 ? 'selected' : ''}>1 hr</option>
                                <option value="90" ${t.durationMinutes === 90 ? 'selected' : ''}>1.5 hr</option>
                                <option value="120" ${t.durationMinutes === 120 ? 'selected' : ''}>2 hr</option>
                            </select>
                        </div>
                    </div>
                `).join('')}
            </div>

            <!-- Add new task section -->
            <div class="p-3.5 bg-stone-50 border border-stone-200 rounded-2xl space-y-2.5 pt-2.5">
                <div class="text-[11px] font-bold uppercase tracking-wider text-stone-600">+ Add new task:</div>
                <div class="flex flex-wrap sm:flex-nowrap items-center gap-2">
                    <input type="text" id="adjust-new-task-name" placeholder="Task name..."
                           class="flex-1 min-w-[130px] px-3 py-1.5 rounded-xl border border-stone-300 text-xs bg-white text-stone-800 placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-[#D79277]" />
                    <div class="flex items-center space-x-1.5 shrink-0">
                        <label for="adjust-new-task-due" class="text-[11px] font-semibold text-stone-500">Due:</label>
                        <input type="date" id="adjust-new-task-due"
                               class="px-2.5 py-1.5 rounded-xl border border-stone-300 text-xs text-stone-700 bg-white focus:outline-none focus:ring-1 focus:ring-[#D79277]" />
                    </div>
                    <select id="adjust-new-task-dur"
                            class="px-2.5 py-1.5 rounded-xl border border-stone-300 text-xs text-stone-700 bg-white focus:outline-none focus:ring-1 focus:ring-[#D79277] shrink-0">
                        <option value="30">30 min</option>
                        <option value="45">45 min</option>
                        <option value="60">1 hr</option>
                        <option value="90">1.5 hr</option>
                    </select>
                    <button type="button" onclick="window.TempoUrmodeFlow.addNewAdjustmentTask()"
                            class="px-3.5 py-1.5 rounded-xl bg-[#D79277] text-white font-bold text-xs hover:bg-[#C68166] transition cursor-pointer shrink-0">
                        Add
                    </button>
                </div>
                ${adjustmentDraft.newTasks.length > 0 ? `
                    <div id="adjust-new-tasks-list" class="space-y-1.5 pt-1">
                        ${adjustmentDraft.newTasks.map((nt, idx) => {
                            const dueStr = nt.hasDeadline && nt.deadlineDate ? ` • Due: ${formatDeadline(nt.deadlineDate, nt.deadlineTime)}` : '';
                            return `
                                <div class="flex items-center justify-between text-xs text-stone-700 bg-white px-3 py-2 rounded-xl border border-stone-200">
                                    <div class="truncate mr-2 font-medium">
                                        <span class="text-[#D79277] font-bold">+</span> ${escapeHTML(nt.name)}
                                        <span class="text-stone-500 font-normal">(~${escapeHTML(nt.durationLabel)}${escapeHTML(dueStr)})</span>
                                    </div>
                                    <button type="button" onclick="window.TempoUrmodeFlow.removeAdjustmentNewTask(${idx})" class="text-stone-400 hover:text-rose-600 p-0.5 cursor-pointer shrink-0" title="Remove task">✕</button>
                                </div>
                            `;
                        }).join('')}
                    </div>
                ` : ''}
            </div>

            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-between gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.handleAdjustmentStep2Back()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs transition cursor-pointer">
                    ← Back
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.handleAdjustmentStep2Next()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm transition cursor-pointer">
                    Next: Propose plan →
                </button>
            </div>
        `;

        showModalContent(html);
    }

    function syncStep2InputsFromDom() {
        if (!adjustmentDraft || !Array.isArray(adjustmentDraft.retainedTasks)) return;
        const kept = adjustmentDraft.retainedTasks.filter(t => t._keep);
        kept.forEach(t => {
            const dueInput = document.getElementById(`adjust-due-${t.id}`);
            if (dueInput) {
                updateRetainedDueDate(t.id, dueInput.value);
            }
            const durSelect = document.getElementById(`adjust-dur-${t.id}`);
            if (durSelect) {
                updateRetainedDuration(t.id, durSelect.value);
            }
        });
    }

    function handleAdjustmentStep2Back() {
        syncStep2InputsFromDom();
        renderAdjustmentStep1Keep();
    }

    function handleAdjustmentStep2Next() {
        syncStep2InputsFromDom();
        renderAdjustmentStep3Proposal();
    }

    function updateRetainedDueDate(taskId, dateVal) {
        if (!adjustmentDraft || !Array.isArray(adjustmentDraft.retainedTasks)) return;
        const item = adjustmentDraft.retainedTasks.find(t => String(t.id) === String(taskId));
        if (item) {
            const val = (dateVal || '').trim();
            if (val) {
                item.hasDeadline = true;
                item.deadlineDate = val;
                if (!item.deadlineTime) {
                    item.deadlineTime = '23:59';
                }
                item.deadline = `${item.deadlineDate} ${item.deadlineTime}`;
            } else {
                item.hasDeadline = false;
                item.deadlineDate = null;
                item.deadlineTime = null;
                item.deadline = null;
            }
        }
    }

    function updateRetainedDuration(taskId, mins) {
        if (!adjustmentDraft || !Array.isArray(adjustmentDraft.retainedTasks)) return;
        const item = adjustmentDraft.retainedTasks.find(t => String(t.id) === String(taskId));
        if (item) {
            item.durationMinutes = parseInt(mins, 10);
            item.durationLabel = formatDuration(item.durationMinutes);
        }
    }

    function addNewAdjustmentTask() {
        const nameInput = document.getElementById('adjust-new-task-name');
        const durInput = document.getElementById('adjust-new-task-dur');
        const dueInput = document.getElementById('adjust-new-task-due');
        const name = nameInput ? nameInput.value.trim() : '';
        if (!name) return;

        // Sync existing retained inputs from DOM before re-rendering
        syncStep2InputsFromDom();

        const dur = parseInt(durInput?.value || '30', 10);
        const dueDate = dueInput ? (dueInput.value || '').trim() : '';
        const hasDeadline = Boolean(dueDate);

        adjustmentDraft.newTasks.push({
            id: 'task-adj-' + Date.now() + '-' + Math.random().toString(36).substr(2, 4),
            name: name,
            durationMinutes: dur,
            durationLabel: formatDuration(dur),
            hasDeadline: hasDeadline,
            deadlineDate: hasDeadline ? dueDate : null,
            deadlineTime: hasDeadline ? '23:59' : null,
            deadline: hasDeadline ? `${dueDate} 23:59` : null,
            completed: false,
            isInProgress: false,
            subtasks: []
        });

        renderAdjustmentStep2Tasks();
    }

    function removeAdjustmentNewTask(idx) {
        syncStep2InputsFromDom();
        adjustmentDraft.newTasks.splice(idx, 1);
        renderAdjustmentStep2Tasks();
    }

    // Step 3: Propose updated plan & Save
    function renderAdjustmentStep3Proposal() {
        activeModalView = 'adjust_propose';
        const kept = adjustmentDraft.retainedTasks.filter(t => t._keep);
        const allAdjustedTasks = [...kept, ...adjustmentDraft.newTasks];

        const now = new Date();
        const pad = n => String(n).padStart(2, '0');
        const todayStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

        // Create clean proposed updated plan structure
        const updatedPlan = {
            id: adjustmentDraft.originalPlan?.id || ('plan_' + Date.now()),
            planId: adjustmentDraft.originalPlan?.planId || ('plan_' + Date.now()),
            planType: 'emergency',
            title: 'Working Plan',
            plannedTasks: allAdjustedTasks.map((t, idx) => ({
                dayDate: todayStr,
                dayLabel: 'Today',
                startTime: idx === 0 ? 'Now' : null,
                executionBadge: idx === 0 ? 'DO THIS FIRST' : 'UP NEXT',
                task: t
            })),
            unarrangedTasks: [],
            tasks: allAdjustedTasks,
            availabilityDays: adjustmentDraft.availabilityDays.length > 0 ? adjustmentDraft.availabilityDays : [
                { date: todayStr, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }
            ]
        };

        adjustmentDraft.proposedPlan = updatedPlan;

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        STEP 3 OF 3 • CONFIRM UPDATED PLAN
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        Proposed Updated Plan
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.renderAdjustmentStep2Tasks()"
                        aria-label="Back"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer">
                    ←
                </button>
            </div>

            <p class="text-xs sm:text-sm text-stone-600">
                Here is your updated working plan. Your original plan is preserved until you confirm and save.
            </p>

            <div class="max-h-60 overflow-y-auto space-y-2 pr-1 py-1">
                ${allAdjustedTasks.map((t, idx) => {
                    const dueStr = t.hasDeadline && t.deadlineDate ? `Due: ${formatDeadline(t.deadlineDate, t.deadlineTime)}` : 'No fixed deadline';
                    return `
                        <div class="p-3 rounded-2xl border border-stone-200 bg-white flex items-center justify-between text-xs">
                            <div class="flex items-center space-x-2.5 min-w-0 flex-1 mr-2">
                                <span class="font-bold text-stone-400 w-5 shrink-0 text-center">${idx + 1}.</span>
                                <div class="min-w-0">
                                    <span class="font-bold text-stone-800 truncate block">${escapeHTML(t.name)}</span>
                                    <div class="text-[11px] text-stone-500 flex items-center space-x-2 mt-0.5">
                                        <span>${escapeHTML(dueStr)}</span>
                                        <span>•</span>
                                        <span>~${escapeHTML(t.durationLabel || formatDuration(t.durationMinutes))}</span>
                                    </div>
                                </div>
                            </div>
                            <span class="px-2.5 py-1 rounded-full text-[10px] font-bold ${idx === 0 ? 'bg-[#D79277] text-white' : 'bg-stone-100 text-stone-600'}">
                                ${idx === 0 ? 'DO THIS FIRST' : 'UP NEXT'}
                            </span>
                        </div>
                    `;
                }).join('')}
            </div>

            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-between gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.renderAdjustmentStep2Tasks()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs transition cursor-pointer">
                    ← Back
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.saveAdjustmentPlan()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm transition cursor-pointer">
                    Save updated plan →
                </button>
            </div>
        `;

        showModalContent(html);
    }

    function saveAdjustmentPlan() {
        if (!adjustmentDraft.proposedPlan) return;

        const updatedPlan = adjustmentDraft.proposedPlan;

        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            window.TempoPlanStore.saveActivePlan('emergency', updatedPlan);
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
            window.TempoEmergencyFlow.setConfirmedPlan(updatedPlan);
        }

        if (window.TempoMode && typeof window.TempoMode.renderEmodeHome === 'function') {
            window.TempoMode.renderEmodeHome();
        }
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
        }

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("Working Plan updated and saved successfully.");
        }

        // Proceed to break-down prompt (Section 4 Step 7)
        showTaskForNowPopupAfterSave(updatedPlan);
    }

    // -------------------------------------------------------------------------
    // PUBLIC API
    // -------------------------------------------------------------------------

    return {
        // Entry Trigger & Session Flags
        queueResetPopup,
        shouldShowReset,
        consumeResetFlag,
        showResetPopup,
        closeModal,

        // Reset Popup Paths
        handleResetYes,
        handleResetNoOrPlan,
        handleResetClose,
        showAreYouReadyPopup,
        handleAreYouReadyYes,
        startSetupFlow,

        // Quick Task Creation
        openQuickTaskModal,
        selectQuickDuration,
        toggleQuickDeadlineInputs,
        handleQuickTaskSubmit,

        // Review & Execution
        showReviewSummaryPopup,
        showKeepPlanTaskPopup,
        launchFocusForTask,
        markOverdueTaskFinished,

        // Breakdown & Start Working
        showTaskForNowPopupAfterSave,
        startBreakTaskFlow,
        renderBreakTaskPopup,
        addSubtask,
        removeSubtask,
        startEditSubtask,
        saveEditSubtask,
        cancelEditSubtask,
        setSubtaskCompleted,
        refreshBreakTaskSubtasks,
        triggerAiHelp,
        applyAiAddMissing,
        applyAiReplaceAll,
        dismissAiNotice,
        generateTaskActionSteps,
        handleBreakMoreTasks,
        viewMyPlan,
        showStartWorkingPopup,
        restartBreakdownFlow,
        showFirstTaskExecutionPopup,
        showTaskSelectionPopup,
        selectWorkTaskAndConfirm,

        // Working Plan Adjustment
        startAdjustmentFlow,
        renderAdjustmentStep1Keep,
        toggleRetainedTask,
        renderAdjustmentStep2Tasks,
        updateRetainedDuration,
        updateRetainedDueDate,
        handleAdjustmentStep2Back,
        handleAdjustmentStep2Next,
        addNewAdjustmentTask,
        removeAdjustmentNewTask,
        renderAdjustmentStep3Proposal,
        saveAdjustmentPlan,

        // State & Inspection
        determinePlanCase,
        getActiveWorkingPlan,
        getAllPlanTasks,
        isTaskOverdue
    };
})();
