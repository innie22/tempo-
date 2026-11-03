/**
 * Tempo Emergency Mode Flow Controller
 * 
 * Multi-Stage Academic Triage Architecture:
 * 1. Entry (Optional Reset / Settle decision)
 * 2. Reality Check (Brain dump: tasks & deadlines only)
 * 3. Prioritize + Estimate (1-task-at-a-time assessment: importance, consequences, flexibility, user duration)
 * 4. Priority Review (Deterministic suggestions: DO FIRST, PLAN, REDUCE/GET HELP, LATER + reassignable)
 * 5. Available Time (Relevant dates from today through deadlines, customizable time blocks)
 * 6. Feasibility Check (Compares workload vs available time before deadlines; surfaces conflicts gently)
 * 7. Emergency Plan Generation & Review (Lightweight timeline, execution order UP NEXT/THEN/LATER, manual reorder with deadline warnings, duration editing with preview)
 * 8. Break Down Tasks (In confirmed plan execution order, optional subtask times with Show/Hide toggle, mismatch notices, stop anytime)
 * 9. Start Working Handoff (Clean handoff state ready for future Focus Zone)
 */

window.TempoEmergencyFlow = (function() {
    // Current Flow Stage
    let currentStage = 'entry';

    const STAGES = [
        'entry',
        'reality-check',
        'prioritize',
        'priority-review',
        'available-time',
        'feasibility',
        'generating',
        'plan-review',
        'handoff'
    ];

    // Core Flow State Model (Prototype in-memory state)
    let tasks = [];
    let assessmentIndex = 0;
    let availabilityDays = [];

    function getTodayISO() {
        if (window.TempoI18n && typeof window.TempoI18n.getLocalTodayISO === 'function') {
            return window.TempoI18n.getLocalTodayISO();
        }
        try {
            return new Intl.DateTimeFormat('en-CA', {
                timeZone: 'Asia/Ho_Chi_Minh',
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            }).format(new Date());
        } catch (e) {
            const d = new Date();
            const pad = n => String(n).padStart(2, '0');
            return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
        }
    }

    function getTomorrowISO() {
        if (window.TempoI18n && typeof window.TempoI18n.getLocalTomorrowISO === 'function') {
            return window.TempoI18n.getLocalTomorrowISO();
        }
        const todayStr = getTodayISO();
        const parts = todayStr.split('-').map(Number);
        if (parts.length === 3 && !isNaN(parts[0]) && !isNaN(parts[1]) && !isNaN(parts[2])) {
            const nextDate = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2] + 1));
            const pad = n => String(n).padStart(2, '0');
            return `${nextDate.getUTCFullYear()}-${pad(nextDate.getUTCMonth() + 1)}-${pad(nextDate.getUTCDate())}`;
        }
        const d = new Date();
        d.setDate(d.getDate() + 1);
        const pad = n => String(n).padStart(2, '0');
        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    }

    function isViLocale() {
        if (window.TempoI18n && typeof window.TempoI18n.getLanguage === 'function') {
            return window.TempoI18n.getLanguage() === 'vi';
        }
        if (window.TempoI18n && typeof window.TempoI18n.getCurrentLanguage === 'function') {
            return window.TempoI18n.getCurrentLanguage() === 'vi';
        }
        try {
            const stored = localStorage.getItem('tempo_language') || localStorage.getItem('tempo_auth_lang') || localStorage.getItem('tempo_lang');
            if (stored === 'vi' || stored === 'en') return stored === 'vi';
        } catch (e) {}
        return true;
    }

    let confirmedPlan = null;
    let breakdownIndex = 0;
    let showSubtaskDurations = true;
    let ignoredDeadlineWarnings = new Set();
    let moveModalState = null;
    let removeDayModalState = null;
    let editEstimateModalState = null;
    let editingRealityCheckTaskId = null;
    let deadlineModalState = null;
    let isAddingDay = false;
    let planHasUserEdits = false;
    let showPlanEditWarningModal = false;
    let editingSubtaskIndex = null;
    let dismissedMismatchForTask = {};
    let showAiSuggestions = false;
    let currentAiSuggestions = [];
    let aiSuggestionError = false;
    let viewingFromHandoff = false;

    // Autosave timer
    let autosaveTimer = null;

    function scheduleDraftAutosave(immediate = false) {
        if (autosaveTimer) {
            clearTimeout(autosaveTimer);
            autosaveTimer = null;
        }

        const performSave = () => {
            // Once the plan is saved and we are at handoff, draft must remain cleared
            if (currentStage === 'handoff') return;

            if (window.TempoPlanStore && typeof window.TempoPlanStore.saveDraft === 'function') {
                window.TempoPlanStore.saveDraft('emergency', {
                    currentStage,
                    tasks,
                    assessmentIndex,
                    availabilityDays,
                    breakdownIndex,
                    confirmedPlan,
                    dismissedMismatchForTask,
                    planHasUserEdits
                });
            }
        };

        if (immediate) {
            performSave();
        } else {
            autosaveTimer = setTimeout(performSave, 400);
        }
    }

    function formatStageName(stage) {
        const names = {
            'entry': 'Settle',
            'reality-check': 'Reality Check',
            'prioritize': 'Prioritize & Estimate',
            'priority-review': 'Priority Review',
            'available-time': 'Available Time',
            'feasibility': 'Feasibility Check',
            'plan-review': 'Plan Review',
            'handoff': 'Plan Ready'
        };
        return names[stage] || 'Setup';
    }

    function applyTaskUpdates(taskId, updates) {
        if (!taskId || !updates) return null;

        // 1. Update matching task in tasks array
        const task = tasks.find(t => t.id === taskId);
        if (task) {
            Object.assign(task, updates);
        }

        // 2. If deadline was updated, clear any previous ignore for this task so warnings can surface
        if ('deadlineDate' in updates || 'deadlineTime' in updates || 'hasDeadline' in updates) {
            ignoredDeadlineWarnings.delete(taskId);
        }

        // 3. Update matching task in confirmedPlan if exists (without altering schedule slots or order)
        if (confirmedPlan) {
            if (Array.isArray(confirmedPlan.plannedTasks)) {
                confirmedPlan.plannedTasks.forEach(item => {
                    if (item && item.task && item.task.id === taskId) {
                        Object.assign(item.task, updates);
                        // Re-evaluate deadline conflict without modifying scheduled time or slot ordering
                        item.hasDeadlineConflict = checkDeadlineConflict(
                            item.task,
                            item.dayDate,
                            item.endMin || 1440
                        );
                    }
                });
            }
            if (Array.isArray(confirmedPlan.unallocatedTasks)) {
                confirmedPlan.unallocatedTasks.forEach(t => {
                    const target = (t && t.task) ? t.task : t;
                    if (target && target.id === taskId) {
                        Object.assign(target, updates);
                    }
                });
            }
            if (Array.isArray(confirmedPlan.unarrangedTasks)) {
                confirmedPlan.unarrangedTasks.forEach(t => {
                    const target = (t && t.task) ? t.task : t;
                    if (target && target.id === taskId) {
                        Object.assign(target, updates);
                    }
                });
            }
        }

        // 4. Persist to TempoPlanStore write-through caching layer
        if (window.TempoPlanStore && typeof window.TempoPlanStore.updateTaskState === 'function') {
            window.TempoPlanStore.updateTaskState(taskId, updates);
            if (confirmedPlan && typeof window.TempoPlanStore.getActivePlan === 'function' && window.TempoPlanStore.getActivePlan('emergency')) {
                window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
            }
        }

        // 5. Autosave draft
        scheduleDraftAutosave(true);

        return task;
    }

    async function restorePlanState() {
        if (!window.TempoPlanStore) return;
        try {
            // 1. Check for active confirmed plan
            let activePlan = typeof window.TempoPlanStore.getActivePlan === 'function' 
                ? window.TempoPlanStore.getActivePlan('emergency') 
                : null;
            if (!activePlan && typeof window.TempoPlanStore.loadActivePlan === 'function') {
                activePlan = await window.TempoPlanStore.loadActivePlan('emergency');
            }

            if (activePlan && ((Array.isArray(activePlan.plannedTasks) && activePlan.plannedTasks.length > 0) || (Array.isArray(activePlan.unarrangedTasks) && activePlan.unarrangedTasks.length > 0))) {
                confirmedPlan = activePlan;
                if (!confirmedPlan.unarrangedTasks) confirmedPlan.unarrangedTasks = [];
                const allTasksMap = new Map();
                if (Array.isArray(activePlan.plannedTasks)) {
                    activePlan.plannedTasks.forEach(item => {
                        if (item && item.task) allTasksMap.set(item.task.id, item.task);
                    });
                }
                if (Array.isArray(activePlan.unallocatedTasks)) {
                    activePlan.unallocatedTasks.forEach(task => {
                        if (task) allTasksMap.set(task.id, task);
                    });
                }
                if (Array.isArray(activePlan.unarrangedTasks)) {
                    activePlan.unarrangedTasks.forEach(task => {
                        if (task) allTasksMap.set(task.id, task);
                    });
                }
                tasks = Array.from(allTasksMap.values());
                if (Array.isArray(activePlan.availabilityDays) && activePlan.availabilityDays.length > 0) {
                    availabilityDays = activePlan.availabilityDays;
                }
                let savedStage = null;
                try {
                    savedStage = localStorage.getItem('tempo_emergency_stage');
                } catch (e) {}

                if (savedStage === 'handoff') {
                    currentStage = 'handoff';
                } else if (savedStage === 'plan-review') {
                    currentStage = 'plan-review';
                } else {
                    currentStage = 'handoff';
                }
                console.log("[TempoEmergencyFlow] Restored active plan from store with", tasks.length, "tasks. Stage:", currentStage);

                const isEmScreen = (window.location.hash === '#emergency') || 
                                   (document.getElementById('screen-emergency') && !document.getElementById('screen-emergency').classList.contains('hidden'));
                if (isEmScreen) {
                    goToStage(currentStage);
                }
            } else {
                // 2. Check for draft in progress
                const draft = await window.TempoPlanStore.loadDraft('emergency');
                if (draft) {
                    if (Array.isArray(draft.tasks)) tasks = draft.tasks;
                    if (typeof draft.assessmentIndex === 'number') assessmentIndex = draft.assessmentIndex;
                    if (Array.isArray(draft.availabilityDays) && draft.availabilityDays.length > 0) availabilityDays = draft.availabilityDays;
                    if (typeof draft.breakdownIndex === 'number') breakdownIndex = draft.breakdownIndex;
                    if (draft.dismissedMismatchForTask) dismissedMismatchForTask = draft.dismissedMismatchForTask;
                    if (typeof draft.planHasUserEdits === 'boolean') planHasUserEdits = draft.planHasUserEdits;
                    if (draft.confirmedPlan) confirmedPlan = draft.confirmedPlan;
                    if (draft.currentStage === 'breakdown') {
                        currentStage = 'plan-review';
                    } else if (draft.currentStage && STAGES.includes(draft.currentStage)) {
                        currentStage = draft.currentStage;
                    }
                    console.log("[TempoEmergencyFlow] Restored draft setup at stage:", currentStage);
                    const isEmScreen = (window.location.hash === '#emergency') || 
                                       (document.getElementById('screen-emergency') && !document.getElementById('screen-emergency').classList.contains('hidden'));
                    if (isEmScreen) {
                        goToStage(currentStage);
                    }
                } else {
                    confirmedPlan = null;
                }
            }
        } catch (err) {
            console.warn("[TempoEmergencyFlow] Storage restoration notice:", err);
        }
    }

    function resetFlowState() {
        confirmedPlan = null;
        tasks = [];
        currentStage = 'entry';
        assessmentIndex = 0;
        breakdownIndex = 0;
        initDefaultAvailability();
        const screen = document.getElementById('screen-emergency');
        if (screen && !screen.classList.contains('hidden')) {
            goToStage('entry');
        }
    }

    async function init() {
        bindEvents();
        initDefaultAvailability();
        await restorePlanState();

        if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
            window.TempoI18n.onLanguageChange(onLanguageChange);
        }

        // If the emergency screen is currently active in DOM, render the restored stage
        const screen = document.getElementById('screen-emergency');
        if (screen && !screen.classList.contains('hidden')) {
            goToStage(currentStage);
        }
    }

    function onLanguageChange(lang) {
        updatePhaseIndicator(currentStage);
        if (currentStage === 'reality-check') {
            renderRealityCheck();
        } else if (currentStage === 'prioritize') {
            renderAssessmentTask();
        } else if (currentStage === 'priority-review') {
            renderPriorityReview();
        } else if (currentStage === 'available-time') {
            renderAvailableTime();
        } else if (currentStage === 'plan-review') {
            renderPlanReview();
        } else if (currentStage === 'entry') {
            renderEntryState();
        }
    }

    function startSettle() {
        if (window.TempoStressRelief && typeof window.TempoStressRelief.openBreathing === 'function') {
            window.TempoStressRelief.openBreathing({
                context: 'emergency',
                onReady: () => {
                    goToStage('reality-check');
                }
            });
        } else {
            goToStage('reality-check');
        }
    }

    function skipSettle() {
        goToStage('reality-check');
    }

    function renderEntryState() {
        bindEntryEvents();
        const resumeBox = document.getElementById('em-entry-resume-container');
        if (!resumeBox) return;

        const hasActive = confirmedPlan && confirmedPlan.plannedTasks && confirmedPlan.plannedTasks.length > 0;
        const hasDraft = window.TempoPlanStore && window.TempoPlanStore.hasDraft('emergency') && tasks.length > 0 && currentStage !== 'entry';

        if (hasActive) {
            resumeBox.innerHTML = `
                <div class="bg-white border-2 border-[#FF6B2C] rounded-[22px] p-6 space-y-4 shadow-sm">
                    <div class="flex items-center justify-between">
                        <span class="px-3 py-1 rounded-full text-xs font-extrabold bg-[#DCE7DF] text-[#2B4B39] uppercase tracking-wider">
                            ${isViLocale() ? 'Working Plan đang hoạt động' : 'Active Working Plan'}
                        </span>
                        <span class="text-xs font-bold text-[#6F6B68]">${confirmedPlan.plannedTasks.length} task${confirmedPlan.plannedTasks.length === 1 ? '' : 's'} scheduled</span>
                    </div>
                    <div class="space-y-1">
                        <h4 class="font-heading text-lg font-bold text-[#202124]">${isViLocale() ? 'Bạn đang có một Working Plan hoạt động' : 'You have an active Working Plan'}</h4>
                        <p class="text-xs sm:text-sm text-[#6F6B68]">
                            Your plan is active and safely saved. You can jump directly into it, or start fresh with a new plan.
                        </p>
                    </div>
                    <div class="pt-2 flex flex-col sm:flex-row items-center gap-3">
                        <button onclick="window.TempoEmergencyFlow.goToStage('handoff')" 
                                class="btn-primary w-full sm:w-auto px-6 py-3 rounded-xl font-bold text-xs sm:text-sm shadow-sm transition">
                            Resume Active Plan →
                        </button>
                        <button onclick="window.TempoEmergencyFlow.promptStartFresh()" 
                                class="w-full sm:w-auto px-5 py-3 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                            Start a New Plan
                        </button>
                    </div>
                </div>
            `;
            resumeBox.classList.remove('hidden');
        } else if (hasDraft) {
            resumeBox.innerHTML = `
                <div class="bg-white border border-[#FFD2BA] bg-[#FFFBF8] rounded-[22px] p-6 space-y-4 shadow-sm">
                    <div class="flex items-center space-x-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-[#FF6B2C]"></span>
                        <span class="text-xs font-extrabold uppercase tracking-wider text-[#B83D08]">Saved Setup in Progress</span>
                    </div>
                    <div class="space-y-1">
                        <h4 class="font-heading text-lg font-bold text-[#202124]">Tiếp tục nơi bạn vừa dừng lại nhé?</h4>
                        <p class="text-xs sm:text-sm text-[#6F6B68]">
                            You have an unfinished setup with ${tasks.length} task${tasks.length === 1 ? '' : 's'} saved at <strong>${formatStageName(currentStage)}</strong>.
                        </p>
                    </div>
                    <div class="pt-2 flex flex-col sm:flex-row items-center gap-3">
                        <button onclick="window.TempoEmergencyFlow.resumeDraft()" 
                                class="btn-primary w-full sm:w-auto px-6 py-3 rounded-xl font-bold text-xs sm:text-sm shadow-sm transition">
                            Resume Setup (${formatStageName(currentStage)}) →
                        </button>
                        <button onclick="window.TempoEmergencyFlow.promptStartFresh()" 
                                class="w-full sm:w-auto px-5 py-3 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                            Start Fresh
                        </button>
                    </div>
                </div>
            `;
            resumeBox.classList.remove('hidden');
        } else {
            resumeBox.innerHTML = '';
            resumeBox.classList.add('hidden');
        }
    }

    function resumeDraft() {
        goToStage(currentStage || 'reality-check');
    }

    function promptStartFresh() {
        const hasActive = confirmedPlan && confirmedPlan.plannedTasks && confirmedPlan.plannedTasks.length > 0;
        const msg = hasActive 
            ? "Starting a new plan will archive your current active plan. Are you sure you want to start fresh?"
            : "Are you sure you want to discard your saved draft and start fresh?";
        if (confirm(msg)) {
            startFreshPlan();
        }
    }

    function startFreshPlan() {
        if (window.TempoPlanStore) {
            window.TempoPlanStore.archiveActivePlan('emergency');
            window.TempoPlanStore.clearDraft('emergency');
        }
        tasks = [];
        assessmentIndex = 0;
        breakdownIndex = 0;
        confirmedPlan = null;
        planHasUserEdits = false;
        dismissedMismatchForTask = {};
        initDefaultAvailability();
        goToStage('reality-check');
    }

    function bindEntryEvents() {
        const btnSettleYes = document.getElementById('btn-em-settle-yes');
        const btnSettleNo = document.getElementById('btn-em-settle-no');

        if (btnSettleYes) {
            btnSettleYes.onclick = startSettle;
        }

        if (btnSettleNo) {
            btnSettleNo.onclick = skipSettle;
        }
    }

    function bindEvents() {
        // Entry Stage Settle Decision
        bindEntryEvents();

        // Keyboard Escape listener for modals
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                if (deadlineModalState) {
                    closeDeadlineModal();
                } else if (editingRealityCheckTaskId) {
                    cancelRealityCheckTaskEdit();
                } else if (removeDayModalState) {
                    closeRemoveDayModal();
                } else if (editEstimateModalState) {
                    closeEditEstimateModal();
                } else if (moveModalState) {
                    closeMoveTaskModal();
                } else if (showPlanEditWarningModal) {
                    cancelPlanEditWarning();
                }
            }
        });
    }

    function goToStage(stageName) {
        if (stageName === 'breakdown') {
            stageName = confirmedPlan ? 'handoff' : 'plan-review';
        }
        if (!STAGES.includes(stageName)) {
            stageName = 'entry';
        }
        currentStage = stageName;

        try {
            localStorage.setItem('tempo_emergency_stage', stageName);
        } catch (e) {}

        // Autosave draft on stage transitions (unless at handoff where plan is finalized)
        if (stageName !== 'handoff') {
            scheduleDraftAutosave(true);
        }

        // Hide all stage containers
        STAGES.forEach(stage => {
            const el = document.getElementById(`emergency-stage-${stage}`);
            if (el) el.classList.add('hidden');
        });

        // Ensure removed breakdown stage container stays hidden and empty
        const breakdownEl = document.getElementById('emergency-stage-breakdown');
        if (breakdownEl) {
            breakdownEl.classList.add('hidden');
            breakdownEl.innerHTML = '';
        }

        // Show target stage container
        const targetEl = document.getElementById(`emergency-stage-${stageName}`);
        if (targetEl) {
            targetEl.classList.remove('hidden');
        }

        // Apply or remove Reality Check / Prioritize Estimate page background (Light Sage Green derived from #8EA28F)
        if (stageName === 'reality-check') {
            document.body.classList.add('reality-check-active');
            const screen = document.getElementById('screen-emergency');
            if (screen) screen.classList.add('reality-check-active');
        } else {
            document.body.classList.remove('reality-check-active');
            const screen = document.getElementById('screen-emergency');
            if (screen) screen.classList.remove('reality-check-active');
        }

        if (stageName === 'prioritize') {
            document.body.classList.add('prioritize-estimate-active');
            const screen = document.getElementById('screen-emergency');
            if (screen) screen.classList.add('prioritize-estimate-active');
        } else {
            document.body.classList.remove('prioritize-estimate-active');
            const screen = document.getElementById('screen-emergency');
            if (screen) screen.classList.remove('prioritize-estimate-active');
        }

        if (stageName === 'priority-review') {
            document.body.classList.add('priority-review-active');
            const screen = document.getElementById('screen-emergency');
            if (screen) screen.classList.add('priority-review-active');
        } else {
            document.body.classList.remove('priority-review-active');
            const screen = document.getElementById('screen-emergency');
            if (screen) screen.classList.remove('priority-review-active');
        }

        if (stageName === 'available-time') {
            document.body.classList.add('available-time-active');
            const screen = document.getElementById('screen-emergency');
            if (screen) screen.classList.add('available-time-active');
        } else {
            document.body.classList.remove('available-time-active');
            const screen = document.getElementById('screen-emergency');
            if (screen) screen.classList.remove('available-time-active');
        }

        if (stageName === 'plan-review') {
            document.body.classList.add('plan-review-active');
            const screen = document.getElementById('screen-emergency');
            if (screen) screen.classList.add('plan-review-active');
        } else {
            document.body.classList.remove('plan-review-active');
            const screen = document.getElementById('screen-emergency');
            if (screen) screen.classList.remove('plan-review-active');
        }

        // Update Lightweight Phase Indicator
        updatePhaseIndicator(stageName);

        // Render stage-specific views
        renderStageView(stageName);

        // Smooth scroll to top of emergency screen
        const screen = document.getElementById('screen-emergency');
        if (screen) {
            screen.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    function updatePhaseIndicator(stage) {
        const isVi = isViLocale();
        const phases = {
            'reset': ['entry'],
            'organize': ['reality-check', 'prioritize', 'priority-review'],
            'plan': ['available-time', 'feasibility', 'generating', 'plan-review'],
            'ready': ['handoff']
        };

        const phaseLabels = {
            'reset': isVi ? 'Thư giãn' : 'RESET',
            'organize': isVi ? 'Sắp xếp' : 'ORGANIZE',
            'plan': isVi ? 'Lên kế hoạch' : 'PLAN',
            'ready': isVi ? 'Sẵn sàng' : 'READY'
        };

        const activePhaseKey = Object.keys(phases).find(key => phases[key].includes(stage)) || 'reset';

        ['reset', 'organize', 'plan', 'ready'].forEach(key => {
            const pill = document.getElementById(`em-phase-${key}`);
            if (!pill) return;
            pill.textContent = phaseLabels[key];
            if (key === activePhaseKey) {
                if (stage === 'reality-check' || stage === 'prioritize' || stage === 'priority-review' || stage === 'available-time' || stage === 'plan-review') {
                    pill.className = 'px-3 py-1 rounded-full bg-[#DCE7DF] text-[#2B4B39] border border-[#8EA28F]/40 font-bold text-[11px] uppercase tracking-wider transition-colors';
                } else {
                    pill.className = 'px-3 py-1 rounded-full bg-[#FFE9DC] text-[#B83D08] font-bold text-[11px] uppercase tracking-wider transition-colors';
                }
            } else {
                pill.className = 'px-3 py-1 rounded-full text-[#8E8A85] font-semibold text-[11px] uppercase tracking-wider transition-colors';
            }
        });

        // Flow Shell Header labels
        const backHomeEl = document.getElementById('em-header-back-home');
        if (backHomeEl) {
            backHomeEl.textContent = isVi ? 'Về trang chủ' : 'Back to Home';
        }
        const sosLabelEl = document.getElementById('em-header-sos-label');
        if (sosLabelEl) {
            sosLabelEl.textContent = isVi ? 'Hỗ trợ SOS' : 'SOS Support';
        }
    }

    function renderStageView(stage) {
        switch (stage) {
            case 'entry':
                renderEntryState();
                break;
            case 'reality-check':
                renderRealityCheck();
                break;
            case 'prioritize':
                renderAssessmentTask();
                break;
            case 'priority-review':
                renderPriorityReview();
                break;
            case 'available-time':
                renderAvailableTime();
                break;
            case 'feasibility':
                renderFeasibilityCheck();
                break;
            case 'generating':
                renderGeneratingPlan();
                break;
            case 'plan-review':
                renderPlanReview();
                break;
            case 'handoff':
                renderHandoff();
                break;
        }
    }

    // =========================================================================
    // STAGE 2: REALITY CHECK (Brain Dump Only)
    // =========================================================================
    function renderRealityCheck() {
        const container = document.getElementById('emergency-stage-reality-check');
        if (!container) return;
        const isVi = isViLocale();

        // Default deadline: tomorrow at 21:00
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const defaultDateStr = getTomorrowISO();

        const existingTaskName = document.getElementById('rc-task-name')?.value || '';

        container.innerHTML = `
            <div class="max-w-2xl mx-auto py-8 sm:py-10 space-y-6">
                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#4A6B5D]">${isVi ? 'CHẾ ĐỘ KHẨN CẤP' : 'URGENT MODE'}</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        ${isVi ? 'Trút bỏ suy nghĩ' : 'Reality Check'}
                    </h2>
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">
                        ${isVi ? 'Đưa mọi điều đang khiến bạn bận tâm ra khỏi đầu.' : 'Get everything out of your head.'}
                    </h3>
                    <p class="text-xs sm:text-sm text-[#5C665F] max-w-md mx-auto leading-relaxed">
                        ${isVi ? "Liệt kê những việc bạn cần hoàn thành. Tempo sẽ giúp bạn sắp xếp chúng." : "Add what you need to get done. We'll organize it next."}
                    </p>
                </div>

                <!-- Input Card -->
                <div class="bg-white border border-[#D5DED7] rounded-[22px] p-5 sm:p-6 space-y-4 shadow-xs">
                    <div class="space-y-1.5">
                        <label for="rc-task-name" class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                            ${isVi ? 'Bạn cần hoàn thành những việc gì?' : 'What do you need to get done?'}
                        </label>
                        <input id="rc-task-name" type="text" value="${escapeHTML(existingTaskName)}"
                               placeholder="${isVi ? 'VD: Báo cáo Marketing, Bài tập Thống kê, Đọc chương 4...' : 'e.g. Marketing Report, Statistics Lab, Chapter 4 Reading...'}"
                               class="w-full px-4 py-3 text-sm border border-[#CAD5CD] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#8EA28F] focus:border-[#8EA28F] bg-[#FEFDFB] text-[#202124] placeholder-[#8E8A85]">
                    </div>

                    <!-- Deadline Inputs -->
                    <div class="space-y-2">
                        <label class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                            Deadline
                        </label>
                        <div class="flex flex-wrap items-center gap-3">
                            <input id="rc-deadline-date" type="date" value="${defaultDateStr}"
                                   class="px-3.5 py-2 text-xs border border-[#CAD5CD] rounded-xl focus:outline-none focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] bg-white text-[#202124]">
                            <input id="rc-deadline-time" type="time" value="21:00"
                                   class="px-3.5 py-2 text-xs border border-[#CAD5CD] rounded-xl focus:outline-none focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] bg-white text-[#202124]">
                            <label class="flex items-center space-x-2 text-xs text-[#5C665F] cursor-pointer pl-1">
                                <input id="rc-no-deadline-cb" type="checkbox" onchange="window.TempoEmergencyFlow.toggleNoDeadline(this.checked)"
                                       class="rounded text-[#4A6B5D] focus:ring-[#8EA28F] border-gray-300">
                                <span>${isVi ? 'Chưa có deadline' : 'No fixed deadline'}</span>
                            </label>
                        </div>
                    </div>

                    <!-- Add Button & Sample Shortcut -->
                    <div class="pt-2 flex items-center justify-between">
                        <button onclick="window.TempoEmergencyFlow.addRealityCheckTask()" 
                                class="bg-[#4A6B5D] hover:bg-[#3D5A4E] text-white px-5 py-2.5 rounded-xl font-bold text-xs shadow-xs flex items-center space-x-1.5 transition cursor-pointer">
                            <span>${isVi ? '+ Thêm task' : '+ Add task'}</span>
                        </button>
                        <button onclick="window.TempoEmergencyFlow.loadSampleTasks()" class="text-xs text-[#4A6B5D] hover:text-[#385347] hover:underline font-semibold transition cursor-pointer">
                            ${isVi ? '+ Thêm 3 task mẫu' : '+ Load 3 sample tasks'}
                        </button>
                    </div>
                </div>

                <!-- Added Tasks List -->
                <div class="space-y-3">
                    <div class="flex items-center justify-between px-1">
                        <h4 class="text-xs font-bold uppercase tracking-wider text-[#5C665F]">
                            ${isVi ? 'Task đã thêm' : 'Added Tasks'} (<span id="rc-task-count">${tasks.length}</span>)
                        </h4>
                    </div>

                    <div id="rc-tasks-list" class="space-y-2.5">
                        ${renderTaskListHTML()}
                    </div>
                </div>

                <!-- Primary CTA -->
                <div class="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-[#D5DED7]">
                    <button onclick="window.TempoEmergencyFlow.goToStage('entry')" 
                            class="text-xs font-semibold text-[#5C665F] hover:text-[#202124] transition cursor-pointer">
                        ${isVi ? '← Quay lại Thư giãn' : '← Back to Reset'}
                    </button>
                    <button id="btn-rc-continue" onclick="window.TempoEmergencyFlow.continueFromRealityCheck()"
                            ${tasks.length === 0 ? 'disabled' : ''}
                            class="${tasks.length === 0 ? 'opacity-50 cursor-not-allowed bg-stone-300 text-stone-500' : 'bg-[#4A6B5D] hover:bg-[#3D5A4E] text-white shadow-xs cursor-pointer'} px-7 py-3.5 rounded-xl font-bold text-sm flex items-center space-x-2 transition">
                        <span>${isVi ? 'Tôi đã thêm tất cả' : "I've added everything"}</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    function renderTaskListHTML() {
        const isVi = isViLocale();
        if (tasks.length === 0) {
            return `
                <div class="p-6 bg-white/80 border border-dashed border-[#CAD5CD] rounded-2xl text-center text-xs text-[#5C665F]">
                    ${isVi ? 'Chưa có task nào. Hãy nhập những task cần làm ở phía trên nhé.' : 'No tasks added yet. Enter your tasks above to get them out of your head.'}
                </div>
            `;
        }

        return tasks.map(t => {
            if (editingRealityCheckTaskId === t.id) {
                return `
                    <div class="p-4 sm:p-5 bg-white border-2 border-[#8EA28F]/60 rounded-2xl shadow-xs space-y-4 transition" data-task-id="${t.id}" data-editing="true">
                        <div class="space-y-1">
                            <label for="em-edit-rc-name-${t.id}" class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                                ${isVi ? 'Tên task' : 'Task Name'}
                            </label>
                            <input id="em-edit-rc-name-${t.id}" type="text"
                                   value="${escapeHTML(t.name)}"
                                   placeholder="${isVi ? 'Bạn cần hoàn thành những việc gì?' : 'What do you need to get done?'}"
                                   class="w-full px-3.5 py-2.5 text-xs sm:text-sm font-semibold border border-[#CAD5CD] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#8EA28F] focus:border-[#8EA28F] bg-white text-[#202124]">
                            <div id="em-edit-rc-error-${t.id}" class="text-[11px] text-rose-500 font-semibold hidden pt-0.5"></div>
                        </div>

                        <div class="space-y-1.5">
                            <label class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                                Deadline
                            </label>
                            <div class="flex flex-wrap items-center gap-2.5">
                                <input id="em-edit-rc-date-${t.id}" type="date" value="${t.deadlineDate || ''}"
                                       ${!t.hasDeadline ? 'disabled' : ''}
                                       class="px-3 py-1.5 text-xs border border-[#CAD5CD] rounded-xl focus:outline-none focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] font-medium transition ${!t.hasDeadline ? 'opacity-40 bg-stone-100 cursor-not-allowed' : 'bg-white'}">
                                <input id="em-edit-rc-time-${t.id}" type="time" value="${t.deadlineTime || ''}"
                                       ${!t.hasDeadline ? 'disabled' : ''}
                                       class="px-3 py-1.5 text-xs border border-[#CAD5CD] rounded-xl focus:outline-none focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] font-medium transition ${!t.hasDeadline ? 'opacity-40 bg-stone-100 cursor-not-allowed' : 'bg-white'}">
                                <label class="flex items-center space-x-1.5 text-xs text-[#5C665F] cursor-pointer select-none pl-1">
                                    <input id="em-edit-rc-nodeadline-${t.id}" type="checkbox"
                                           ${!t.hasDeadline ? 'checked' : ''}
                                           onchange="window.TempoEmergencyFlow.toggleRcEditNoDeadline('${t.id}', this.checked)"
                                           class="w-4 h-4 rounded text-[#4A6B5D] focus:ring-[#8EA28F] border-gray-300">
                                    <span>${isVi ? 'Chưa có deadline' : 'No fixed deadline'}</span>
                                </label>
                            </div>
                        </div>

                        <div class="flex items-center justify-end space-x-2 pt-1 border-t border-[#D5DED7]">
                            <button onclick="window.TempoEmergencyFlow.cancelRealityCheckTaskEdit()"
                                    class="px-3.5 py-1.5 text-xs font-semibold text-gray-600 hover:text-gray-900 hover:bg-stone-200/60 rounded-xl transition cursor-pointer">
                                ${isVi ? 'Hủy' : 'Cancel'}
                            </button>
                            <button onclick="window.TempoEmergencyFlow.saveRealityCheckTaskEdit('${t.id}')"
                                    class="bg-[#4A6B5D] hover:bg-[#3D5A4E] text-white px-4 py-1.5 text-xs font-bold rounded-xl shadow-xs transition cursor-pointer">
                                ${isVi ? 'Lưu' : 'Save'}
                            </button>
                        </div>
                    </div>
                `;
            }

            const deadlineText = t.hasDeadline 
                ? `Deadline ${formatHumanDeadline(t.deadlineDate, t.deadlineTime, isVi)}`
                : (isVi ? '🌱 Chưa có deadline' : '🌱 No fixed deadline');

            return `
                <div class="p-3.5 bg-white border border-[#D5DED7] hover:border-[#CAD5CD] rounded-2xl flex items-center justify-between gap-3 shadow-2xs transition" data-task-id="${t.id}">
                    <div class="space-y-1 min-w-0">
                        <h5 class="text-xs sm:text-sm font-bold text-[#202124] truncate">${escapeHTML(t.name)}</h5>
                        <p class="text-[11px] text-[#5C665F] flex items-center space-x-1">
                            <span>🕒</span>
                            <span>${deadlineText}</span>
                        </p>
                    </div>
                    <div class="flex items-center space-x-2 shrink-0">
                        <button onclick="window.TempoEmergencyFlow.editRealityCheckTask('${t.id}')" 
                                class="px-2.5 py-1 text-[11px] font-semibold text-gray-600 hover:text-gray-900 hover:bg-stone-100 rounded-lg transition cursor-pointer">
                            ${isVi ? 'Sửa' : 'Edit'}
                        </button>
                        <button onclick="window.TempoEmergencyFlow.removeRealityCheckTask('${t.id}')" 
                                class="px-2.5 py-1 text-[11px] font-semibold text-rose-600 hover:text-rose-800 hover:bg-rose-50 rounded-lg transition cursor-pointer">
                            ${isVi ? 'Xóa' : 'Remove'}
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    function toggleNoDeadline(isNoDeadline) {
        const dateInput = document.getElementById('rc-deadline-date');
        const timeInput = document.getElementById('rc-deadline-time');
        if (dateInput && timeInput) {
            dateInput.disabled = isNoDeadline;
            timeInput.disabled = isNoDeadline;
            dateInput.classList.toggle('opacity-40', isNoDeadline);
            timeInput.classList.toggle('opacity-40', isNoDeadline);
        }
    }

    function addRealityCheckTask() {
        const nameInput = document.getElementById('rc-task-name');
        const dateInput = document.getElementById('rc-deadline-date');
        const timeInput = document.getElementById('rc-deadline-time');
        const noDeadlineCb = document.getElementById('rc-no-deadline-cb');

        const name = nameInput ? nameInput.value.trim() : '';
        if (!name) {
            if (window.TempoApp) window.TempoApp.showToast("Vui lòng nhập tên công việc.");
            return;
        }

        const hasDeadline = !noDeadlineCb || !noDeadlineCb.checked;
        const deadlineDate = hasDeadline && dateInput ? dateInput.value : null;
        const deadlineTime = hasDeadline && timeInput ? timeInput.value : null;

        const newTask = {
            id: 'task_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
            name: name,
            hasDeadline: hasDeadline,
            deadlineDate: deadlineDate,
            deadlineTime: deadlineTime,
            importance: 'High',
            consequence: 'Big consequences',
            flexibility: ['Probably not'],
            durationMinutes: 60,
            durationLabel: '1h',
            priorityCategory: 'DO_FIRST',
            isBrokenDown: false,
            alreadyKnowWhatToDo: false,
            subtasks: []
        };

        tasks.push(newTask);
        renderRealityCheck();
        scheduleDraftAutosave();
    }

    function removeRealityCheckTask(taskId) {
        tasks = tasks.filter(t => t.id !== taskId);
        renderRealityCheck();
        scheduleDraftAutosave();
    }

    function editRealityCheckTask(taskId) {
        const task = tasks.find(t => t.id === taskId);
        if (!task) return;

        editingRealityCheckTaskId = taskId;
        renderRealityCheck();

        setTimeout(() => {
            const input = document.getElementById(`em-edit-rc-name-${taskId}`);
            if (input) {
                input.focus();
                input.select();
            }
        }, 40);
    }

    function cancelRealityCheckTaskEdit() {
        editingRealityCheckTaskId = null;
        renderRealityCheck();
    }

    function toggleRcEditNoDeadline(taskId, isChecked) {
        const dateInput = document.getElementById(`em-edit-rc-date-${taskId}`);
        const timeInput = document.getElementById(`em-edit-rc-time-${taskId}`);
        if (dateInput && timeInput) {
            dateInput.disabled = isChecked;
            timeInput.disabled = isChecked;
            dateInput.classList.toggle('opacity-40', isChecked);
            dateInput.classList.toggle('bg-stone-100', isChecked);
            dateInput.classList.toggle('cursor-not-allowed', isChecked);
            timeInput.classList.toggle('opacity-40', isChecked);
            timeInput.classList.toggle('bg-stone-100', isChecked);
            timeInput.classList.toggle('cursor-not-allowed', isChecked);
            if (!isChecked && !dateInput.value) {
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1);
                dateInput.value = getTomorrowISO();
                if (!timeInput.value) timeInput.value = '21:00';
            }
        }
    }

    function saveRealityCheckTaskEdit(taskId) {
        const nameInput = document.getElementById(`em-edit-rc-name-${taskId}`);
        const dateInput = document.getElementById(`em-edit-rc-date-${taskId}`);
        const timeInput = document.getElementById(`em-edit-rc-time-${taskId}`);
        const noDeadlineCb = document.getElementById(`em-edit-rc-nodeadline-${taskId}`);
        const errDiv = document.getElementById(`em-edit-rc-error-${taskId}`);

        const newName = nameInput ? nameInput.value.trim() : '';
        if (!newName) {
            if (errDiv) {
                errDiv.textContent = "Vui lòng nhập tên công việc.";
                errDiv.classList.remove('hidden');
            }
            if (nameInput) nameInput.focus();
            return;
        }

        const isNoDeadline = noDeadlineCb ? noDeadlineCb.checked : false;
        const hasDeadline = !isNoDeadline;
        const deadlineDate = hasDeadline && dateInput ? (dateInput.value || null) : null;
        const deadlineTime = hasDeadline && timeInput ? (timeInput.value || null) : null;

        applyTaskUpdates(taskId, {
            name: newName,
            hasDeadline: hasDeadline,
            deadlineDate: deadlineDate,
            deadlineTime: deadlineTime
        });

        editingRealityCheckTaskId = null;
        renderRealityCheck();
    }

    function loadSampleTasks() {
        const todayStr = getTodayISO();
        const tomorrowStr = getTomorrowISO();

        tasks = [
            {
                id: 'task_sample_1',
                name: 'Statistics Assignment (Problem Set 4)',
                hasDeadline: true,
                deadlineDate: todayStr,
                deadlineTime: '21:00',
                importance: 'High',
                consequence: 'Big consequences',
                flexibility: ['Probably not'],
                durationMinutes: 90,
                durationLabel: '1h 30m',
                priorityCategory: 'DO_FIRST',
                isBrokenDown: false,
                alreadyKnowWhatToDo: false,
                subtasks: []
            },
            {
                id: 'task_sample_2',
                name: 'Marketing Report Final Draft',
                hasDeadline: true,
                deadlineDate: tomorrowStr,
                deadlineTime: '09:00',
                importance: 'High',
                consequence: 'Big consequences',
                flexibility: ['Reduce what I need to do'],
                durationMinutes: 120,
                durationLabel: '2h',
                priorityCategory: 'DO_FIRST',
                isBrokenDown: false,
                alreadyKnowWhatToDo: false,
                subtasks: []
            },
            {
                id: 'task_sample_3',
                name: 'Biology Chapter 6 Notes',
                hasDeadline: false,
                deadlineDate: null,
                deadlineTime: null,
                importance: 'Medium',
                consequence: 'Some consequences',
                flexibility: ['Ask someone for help'],
                durationMinutes: 60,
                durationLabel: '1h',
                priorityCategory: 'PLAN',
                isBrokenDown: false,
                alreadyKnowWhatToDo: false,
                subtasks: []
            }
        ];

        renderRealityCheck();
        scheduleDraftAutosave();
    }

    function continueFromRealityCheck() {
        if (tasks.length === 0) {
            const isVi = isViLocale();
            if (window.TempoApp) window.TempoApp.showToast(isVi ? "Vui lòng thêm ít nhất một task để tiếp tục." : "Please add at least one task to continue.");
            return;
        }
        assessmentIndex = 0;
        goToStage('prioritize');
    }

    // =========================================================================
    // STAGE 3: PRIORITIZE + ESTIMATE (One-Task-At-A-Time Assessment)
    // =========================================================================
    function formatTaskDurationDisplay(task, isVi = isViLocale()) {
        if (!task) return '';
        if (task.isUnknownDuration) {
            return isVi ? 'Không chắc' : 'Not sure';
        }
        if (task.isCustomDuration) {
            const val = task.customDurationValue || 45;
            const unit = task.customDurationUnit || 'minutes';
            if (isVi) {
                const unitMap = { minutes: 'phút', hours: 'giờ', days: 'ngày', weeks: 'tuần', months: 'tháng' };
                return `${val} ${unitMap[unit] || unit}`;
            } else {
                if (unit === 'minutes') return `${val} min`;
                if (unit === 'hours') return val === 1 ? '1 hour' : `${val} hours`;
                if (unit === 'days') return val === 1 ? '1 day' : `${val} days`;
                if (unit === 'weeks') return val === 1 ? '1 week' : `${val} weeks`;
                if (unit === 'months') return val === 1 ? '1 month' : `${val} months`;
                return `${val} ${unit}`;
            }
        }
        if (task.durationMinutes) {
            const mins = task.durationMinutes;
            if (isVi) {
                if (mins < 60) return `${mins} phút`;
                const h = Math.floor(mins / 60);
                const m = mins % 60;
                return m > 0 ? `${h} giờ ${m} phút` : `${h} giờ`;
            } else {
                return formatDurationMinutes(mins);
            }
        }
        return isVi ? 'Không chắc' : 'Not sure';
    }

    function renderAssessmentTask() {
        const container = document.getElementById('emergency-stage-prioritize');
        if (!container) return;

        if (tasks.length === 0) {
            goToStage('reality-check');
            return;
        }

        if (assessmentIndex >= tasks.length) {
            assessmentIndex = tasks.length - 1;
        }

        const task = tasks[assessmentIndex];
        const isVi = isViLocale();
        const relativeDueText = task.hasDeadline
            ? calculateRelativeDueText(task.deadlineDate, task.deadlineTime, isVi)
            : (isVi ? 'Chưa có deadline (linh hoạt theo tiến độ của bạn)' : 'No fixed deadline (explore at your own pace)');

        container.innerHTML = `
            <div class="max-w-2xl mx-auto py-8 sm:py-10 space-y-6">
                <!-- Secondary Back Navigation -->
                <div class="flex items-center justify-between">
                    ${assessmentIndex > 0 
                        ? `<button onclick="window.TempoEmergencyFlow.previousAssessmentTask()" class="inline-flex items-center text-xs font-semibold text-[#5C665F] hover:text-[#202124] transition py-1 group"><span class="mr-1.5 group-hover:-translate-x-0.5 transition-transform">←</span><span>${isVi ? 'Task trước' : 'Previous task'}</span></button>`
                        : `<button onclick="window.TempoEmergencyFlow.goToStage('reality-check')" class="inline-flex items-center text-xs font-semibold text-[#5C665F] hover:text-[#202124] transition py-1 group"><span class="mr-1.5 group-hover:-translate-x-0.5 transition-transform">←</span><span>${isVi ? 'Quay lại Trút bỏ suy nghĩ' : 'Back to Reality Check'}</span></button>`
                    }
                </div>

                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#3D6B52]">${isVi ? 'ƯU TIÊN & ƯỚC LƯỢNG' : 'PRIORITIZE & ESTIMATE'}</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        ${isVi ? 'Hãy xác định những việc cần được ưu tiên trước.' : "Let's figure out what needs your attention first."}
                    </h2>
                    <p class="text-xs sm:text-sm text-[#5C665F]">
                        ${isVi ? 'Chúng ta sẽ xem xét từng task một.' : "We'll look at one task at a time."}
                    </p>
                </div>

                <!-- Progress Pill -->
                <div class="flex items-center justify-between text-xs text-[#5C665F] px-1">
                    <span class="font-bold text-[#446A7B]">${isVi ? `Task ${assessmentIndex + 1}/${tasks.length}` : `Task ${assessmentIndex + 1} of ${tasks.length}`}</span>
                    <span>${isVi ? `Đã đánh giá ${Math.round(((assessmentIndex + 1) / tasks.length) * 100)}%` : `${Math.round(((assessmentIndex + 1) / tasks.length) * 100)}% evaluated`}</span>
                </div>

                <!-- Task Card Preview: Warm Blush subtle highlight -->
                <div class="bg-[#FCF6F2] border border-[#ECC9BA] rounded-2xl p-4 sm:p-5 space-y-1 shadow-2xs">
                    <span class="text-[10px] font-bold uppercase tracking-wider text-[#8A5645]">${isVi ? 'TASK HIỆN TẠI' : 'CURRENT TASK'}</span>
                    <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124]">${escapeHTML(task.name)}</h3>
                    <p class="text-xs text-[#5C665F] flex items-center space-x-1.5 flex-wrap">
                        <span>🕒</span>
                        <span class="font-semibold text-gray-800">${relativeDueText}</span>
                        <span>•</span>
                        <button type="button"
                                onclick="window.TempoEmergencyFlow.openDeadlineModal('${task.id}')"
                                class="text-[#446A7B] hover:text-[#2D4D5C] hover:underline font-semibold text-[11px] transition cursor-pointer">
                            ${isVi ? 'Sửa Deadline' : 'Edit deadline'}
                        </button>
                    </p>
                </div>

                <!-- 4 Questions Card -->
                <div class="bg-white border border-[#E2DDD7] rounded-[22px] p-5 sm:p-7 space-y-6 shadow-sm">
                    <!-- Q1: Importance -->
                    <div class="space-y-2">
                        <label class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                            ${isVi ? '1. TASK NÀY QUAN TRỌNG NHƯ THẾ NÀO?' : '1. HOW IMPORTANT IS THIS TASK?'}
                        </label>
                        <div class="grid grid-cols-3 gap-2.5">
                            ${[
                                { val: 'High', label: isVi ? 'Cao' : 'High' },
                                { val: 'Medium', label: isVi ? 'Trung bình' : 'Medium' },
                                { val: 'Low', label: isVi ? 'Thấp' : 'Low' }
                            ].map(opt => `
                                <div onclick="window.TempoEmergencyFlow.setAssessmentOption('importance', '${opt.val}')"
                                     class="em-choice-pill p-3 rounded-xl text-center text-xs font-semibold ${task.importance === opt.val ? 'em-choice-pill--blush-selected' : 'text-gray-700'}">
                                    ${opt.label}
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Q2: Consequences -->
                    <div class="space-y-2">
                        <label class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                            ${isVi ? '2. ĐIỀU GÌ XẢY RA NẾU TASK BỊ TRỄ HOẶC CHƯA HOÀN THÀNH?' : "2. WHAT HAPPENS IF IT'S LATE OR UNFINISHED?"}
                        </label>
                        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                            ${[
                                { val: 'Big consequences', label: isVi ? 'Hậu quả nghiêm trọng' : 'Big consequences' },
                                { val: 'Some consequences', label: isVi ? 'Có một số hậu quả' : 'Some consequences' },
                                { val: 'Not much', label: isVi ? 'Không đáng kể' : 'Not much' },
                                { val: 'Not sure', label: isVi ? 'Không chắc' : 'Not sure' }
                            ].map(opt => `
                                <div onclick="window.TempoEmergencyFlow.setAssessmentOption('consequence', '${opt.val}')"
                                     class="em-choice-pill p-3 rounded-xl text-center text-xs font-semibold ${task.consequence === opt.val ? 'em-choice-pill--blush-selected' : 'text-gray-700'}">
                                    ${opt.label}
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Q3: Flexibility (Multi-select) -->
                    <div class="space-y-2">
                        <label class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                            ${isVi ? '3. CÓ ĐIỀU GÌ Ở TASK NÀY CÓ THỂ THAY ĐỔI ĐƯỢC KHÔNG?' : '3. CAN ANYTHING ABOUT THIS TASK CHANGE?'}
                            <span class="text-[11px] font-normal text-[#5C665F]">(${isVi ? 'CHỌN TẤT CẢ ĐÁP ÁN PHÙ HỢP' : 'SELECT ALL THAT APPLY'})</span>
                        </label>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            ${[
                                { val: 'Reduce what I need to do', label: isVi ? 'Giảm bớt khối lượng việc cần làm' : 'Reduce what I need to do' },
                                { val: 'Ask someone for help', label: isVi ? 'Nhờ người khác hỗ trợ' : 'Ask someone for help' },
                                { val: 'Move / negotiate the deadline', label: isVi ? 'Dời / thương lượng lại Deadline' : 'Move / negotiate the deadline' },
                                { val: 'Probably not', label: isVi ? 'Hầu như không thể thay đổi' : 'Probably not' },
                                { val: 'Not sure', label: isVi ? 'Không chắc' : 'Not sure' }
                            ].map(opt => {
                                const isSelected = task.flexibility && task.flexibility.includes(opt.val);
                                return `
                                    <div onclick="window.TempoEmergencyFlow.toggleAssessmentFlexibility('${opt.val}')"
                                         class="em-choice-pill p-3 rounded-xl flex items-center justify-between text-xs font-medium ${isSelected ? 'em-choice-pill--sage-selected' : 'text-gray-700'}">
                                        <span>${opt.label}</span>
                                        <span class="font-bold">${isSelected ? '✓' : '+'}</span>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>

                    <!-- Q4: User Estimated Duration -->
                    <div class="space-y-2 pt-2 border-t border-gray-100">
                        <div class="space-y-0.5">
                            <label class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                                ${isVi ? '4. Bạn nghĩ mình sẽ cần bao nhiêu thời gian?' : "4. How long do you think you'll need?"}
                            </label>
                            <p class="text-xs text-[#5C665F]">${isVi ? 'Chỉ cần ước lượng gần đúng. Bạn có thể điều chỉnh sau.' : 'A rough estimate is enough. You can adjust this later.'}</p>
                        </div>
                        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 pt-1">
                            ${[
                                { label: isVi ? '30 phút' : '30 min', val: 30 },
                                { label: isVi ? '1 giờ' : '1h', val: 60 },
                                { label: isVi ? '2 giờ' : '2h', val: 120 },
                                { label: isVi ? '3 giờ' : '3h', val: 180 },
                                { label: isVi ? 'Tùy chỉnh' : 'Custom', val: 'custom' },
                                { label: isVi ? 'Không chắc' : 'Not sure', val: 'unknown' }
                            ].map(dur => {
                                let isSelected = false;
                                if (dur.val === 'custom') {
                                    isSelected = !!task.isCustomDuration;
                                } else if (dur.val === 'unknown') {
                                    isSelected = !!task.isUnknownDuration;
                                } else {
                                    isSelected = !task.isCustomDuration && !task.isUnknownDuration && task.durationMinutes === dur.val;
                                }
                                return `
                                    <div onclick="window.TempoEmergencyFlow.setAssessmentDuration('${dur.val}')"
                                         class="em-choice-pill p-2.5 rounded-xl text-center text-xs font-semibold ${isSelected ? 'em-choice-pill--sage-selected' : 'text-gray-700'}">
                                        ${dur.label}
                                    </div>
                                `;
                            }).join('')}
                        </div>

                        <!-- Custom duration input box -->
                        <div id="em-custom-duration-box" class="${task.isCustomDuration ? '' : 'hidden'} pt-2 space-y-1.5">
                            <label class="block text-xs font-semibold text-gray-700">${isVi ? 'Ước lượng tùy chỉnh' : 'Custom estimate'}</label>
                            <div class="flex items-center space-x-2">
                                <input id="em-custom-value-input" type="number" min="1" step="any"
                                       value="${task.customDurationValue || 45}"
                                       oninput="window.TempoEmergencyFlow.handleCustomDurationChange(this.value, null)"
                                       placeholder="${isVi ? 'Số lượng' : 'Value'}"
                                       class="w-24 px-3 py-1.5 text-xs border border-gray-300 rounded-lg text-center font-bold focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] focus:outline-none">
                                <select id="em-custom-unit-select"
                                        onchange="window.TempoEmergencyFlow.handleCustomDurationChange(null, this.value)"
                                        class="px-3 py-1.5 text-xs border border-gray-300 rounded-lg bg-white font-semibold focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] focus:outline-none">
                                    <option value="minutes" ${(task.customDurationUnit || 'minutes') === 'minutes' ? 'selected' : ''}>${isVi ? 'phút' : 'minutes'}</option>
                                    <option value="hours" ${task.customDurationUnit === 'hours' ? 'selected' : ''}>${isVi ? 'giờ' : 'hours'}</option>
                                    <option value="days" ${task.customDurationUnit === 'days' ? 'selected' : ''}>${isVi ? 'ngày' : 'days'}</option>
                                    <option value="weeks" ${task.customDurationUnit === 'weeks' ? 'selected' : ''}>${isVi ? 'tuần' : 'weeks'}</option>
                                    <option value="months" ${task.customDurationUnit === 'months' ? 'selected' : ''}>${isVi ? 'tháng' : 'months'}</option>
                                </select>
                            </div>
                            <p class="text-[11px] text-[#5C665F] font-medium" id="em-custom-preview-label">
                                ${isVi ? 'Ước lượng hiện tại:' : 'Current estimate:'} <strong>${formatTaskDurationDisplay(task, isVi)}</strong>
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Navigation Controls -->
                <div class="pt-2 flex items-center justify-between">
                    ${assessmentIndex > 0 
                        ? `<button onclick="window.TempoEmergencyFlow.previousAssessmentTask()" class="text-xs font-semibold text-[#5C665F] hover:text-[#202124] transition cursor-pointer">← ${isVi ? 'Task trước' : 'Previous task'}</button>`
                        : `<button onclick="window.TempoEmergencyFlow.goToStage('reality-check')" class="text-xs font-semibold text-[#5C665F] hover:text-[#202124] transition cursor-pointer">← ${isVi ? 'Quay lại Trút bỏ suy nghĩ' : 'Back to Reality Check'}</button>`
                    }
                    <button onclick="window.TempoEmergencyFlow.saveAssessmentAndNext()" 
                            class="bg-[#4A6B5D] hover:bg-[#3D5A4E] text-white px-7 py-3.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs flex items-center space-x-1.5 transition cursor-pointer">
                        <span>${assessmentIndex === tasks.length - 1 ? (isVi ? 'Xem các nhóm ưu tiên →' : 'Review Priority Categories →') : (isVi ? 'Lưu & task tiếp theo →' : 'Save & next task →')}</span>
                    </button>
                </div>
            </div>

            <!-- Deadline Modal Dialog (if active) -->
            ${renderDeadlineModalHTML()}
        `;
    }

    function setAssessmentOption(field, value) {
        if (!tasks[assessmentIndex]) return;
        tasks[assessmentIndex][field] = value;
        if (field === 'importance' || field === 'consequence') {
            tasks[assessmentIndex].hasManualPriority = false;
        }
        renderAssessmentTask();
    }

    function toggleAssessmentFlexibility(option) {
        if (!tasks[assessmentIndex]) return;
        let flex = tasks[assessmentIndex].flexibility || [];
        if (flex.includes(option)) {
            flex = flex.filter(item => item !== option);
        } else {
            flex.push(option);
        }
        tasks[assessmentIndex].flexibility = flex;
        tasks[assessmentIndex].hasManualPriority = false;
        renderAssessmentTask();
    }

    function applyCustomDuration(task) {
        const val = task.customDurationValue || 45;
        const unit = task.customDurationUnit || 'minutes';

        if (unit === 'minutes') {
            task.durationMinutes = Math.round(val);
            task.isLongTerm = false;
            task.durationLabel = `${val} min`;
        } else if (unit === 'hours') {
            task.durationMinutes = Math.round(val * 60);
            task.isLongTerm = false;
            task.durationLabel = val === 1 ? '1 hour' : `${val} hours`;
        } else if (unit === 'days') {
            task.durationMinutes = null;
            task.isLongTerm = true;
            task.durationLabel = val === 1 ? '1 day' : `${val} days`;
        } else if (unit === 'weeks') {
            task.durationMinutes = null;
            task.isLongTerm = true;
            task.durationLabel = val === 1 ? '1 week' : `${val} weeks`;
        } else if (unit === 'months') {
            task.durationMinutes = null;
            task.isLongTerm = true;
            task.durationLabel = val === 1 ? '1 month' : `${val} months`;
        }
        task.isUnknownDuration = false;
    }

    function setAssessmentDuration(val) {
        if (!tasks[assessmentIndex]) return;
        const task = tasks[assessmentIndex];

        if (val === 'custom') {
            task.isCustomDuration = true;
            task.isUnknownDuration = false;
            task.customDurationValue = task.customDurationValue || 45;
            task.customDurationUnit = task.customDurationUnit || 'minutes';
            applyCustomDuration(task);
        } else if (val === 'unknown') {
            task.isUnknownDuration = true;
            task.isCustomDuration = false;
            task.isLongTerm = false;
            task.durationMinutes = null;
            task.durationLabel = 'Not sure';
        } else {
            const numericMin = parseInt(val, 10);
            task.isCustomDuration = false;
            task.isUnknownDuration = false;
            task.isLongTerm = false;
            task.durationMinutes = numericMin;
            task.durationLabel = formatDurationMinutes(numericMin);
        }
        renderAssessmentTask();
    }

    function handleCustomDurationChange(value, unit) {
        if (!tasks[assessmentIndex]) return;
        const task = tasks[assessmentIndex];

        if (value !== null && value !== undefined) {
            const num = parseFloat(value);
            if (!isNaN(num) && num > 0) {
                task.customDurationValue = num;
            }
        }
        if (unit !== null && unit !== undefined) {
            if (['minutes', 'hours', 'days', 'weeks', 'months'].includes(unit)) {
                task.customDurationUnit = unit;
            }
        }
        applyCustomDuration(task);

        const preview = document.getElementById('em-custom-preview-label');
        if (preview) {
            const isVi = isViLocale();
            preview.innerHTML = `${isVi ? 'Ước lượng hiện tại:' : 'Current estimate:'} <strong>${formatTaskDurationDisplay(task, isVi)}</strong>`;
        }
    }

    function saveAssessmentAndNext() {
        if (assessmentIndex < tasks.length - 1) {
            assessmentIndex++;
            renderAssessmentTask();
            scheduleDraftAutosave(true);
        } else {
            // Apply deterministic initial classification
            applyDeterministicClassification();
            goToStage('priority-review');
        }
    }

    function previousAssessmentTask() {
        if (assessmentIndex > 0) {
            assessmentIndex--;
            renderAssessmentTask();
            scheduleDraftAutosave(true);
        }
    }

    // =========================================================================
    // STAGE 4: PRIORITY REVIEW (Suggested Organization + User Reassignable)
    // =========================================================================
    function applyDeterministicClassification() {
        tasks.forEach(t => {
            if (t.hasManualPriority) return;
            const flex = t.flexibility || [];
            const hasFlexibility = flex.includes('Reduce what I need to do') || flex.includes('Ask someone for help') || flex.includes('Move / negotiate the deadline');

            if (hasFlexibility && t.consequence !== 'Big consequences') {
                t.priorityCategory = 'REDUCE_HELP';
            } else if (t.consequence === 'Big consequences' || (t.importance === 'High' && t.hasDeadline && isDueSoon(t.deadlineDate))) {
                t.priorityCategory = 'DO_FIRST';
            } else if (t.importance === 'High' || t.consequence === 'Some consequences') {
                t.priorityCategory = 'PLAN';
            } else if (t.consequence === 'Not much' || t.importance === 'Low') {
                t.priorityCategory = 'LATER';
            } else {
                t.priorityCategory = 'PLAN';
            }
        });
    }

    function renderPriorityReview() {
        const container = document.getElementById('emergency-stage-priority-review');
        if (!container) return;

        const isVi = isViLocale();

        const categories = [
            { 
                key: 'DO_FIRST', 
                label: isVi ? 'LÀM TRƯỚC' : 'DO FIRST', 
                icon: '🔴', 
                badge: 'bg-[#FDF2EC] text-[#783626] border-[#ECC9BA]', 
                cardBorder: 'border-[#E7D6CE]',
                desc: isVi ? 'Áp lực cấp bách và có ảnh hưởng lớn. Cần được ưu tiên ngay.' : 'Urgent pressure with high impact. Needs immediate focus.' 
            },
            { 
                key: 'PLAN', 
                label: isVi ? 'LÊN KẾ HOẠCH' : 'PLAN', 
                icon: '🟢', 
                badge: 'bg-[#EDF4EF] text-[#244634] border-[#8EA28F]/40', 
                cardBorder: 'border-[#D5E2D9]',
                desc: isVi ? 'Công việc quan trọng. Hãy dành thời gian cụ thể để hoàn thành trước Deadline.' : 'Important work. Schedule dedicated blocks before deadlines.' 
            },
            { 
                key: 'REDUCE_HELP', 
                label: isVi ? 'GIẢM BỚT / NHỜ HỖ TRỢ' : 'REDUCE / GET HELP', 
                icon: '🔵', 
                badge: 'bg-[#EEF4F7] text-[#2B4E5E] border-[#93AFBC]/40', 
                cardBorder: 'border-[#D4E3EA]',
                desc: isVi ? 'Phạm vi việc có thể thu gọn, đơn giản hóa hoặc nhờ người khác hỗ trợ.' : 'Scope can be trimmed, simplified, or delegated with peer help.' 
            },
            { 
                key: 'LATER', 
                label: isVi ? 'LÀM SAU' : 'LATER', 
                icon: '⚪', 
                badge: 'bg-[#F5F3F0] text-[#55524E] border-[#DDD8D2]', 
                cardBorder: 'border-[#EAE4DF]',
                desc: isVi ? 'Ít cấp bách hơn ở thời điểm này. Có thể xử lý an tâm sau khi vượt qua giai đoạn cao điểm.' : 'Lower immediate stakes. Can be safely addressed after the crunch.' 
            }
        ];

        container.innerHTML = `
            <div class="max-w-2xl mx-auto py-8 sm:py-10 space-y-6">
                <!-- Secondary Back Navigation -->
                <div class="flex items-center justify-between">
                    <button onclick="window.TempoEmergencyFlow.goToStage('prioritize')" 
                            class="inline-flex items-center text-xs font-semibold text-[#5C665F] hover:text-[#202124] transition py-1 group cursor-pointer">
                        <span class="mr-1.5 group-hover:-translate-x-0.5 transition-transform">←</span>
                        <span>${isVi ? 'Quay lại phần đánh giá' : 'Back to Assessment'}</span>
                    </button>
                </div>

                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#3D6B52]">${isVi ? 'XEM LẠI MỨC ĐỘ ƯU TIÊN' : 'PRIORITY REVIEW'}</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        ${isVi ? 'Cách sắp xếp được đề xuất' : 'Suggested Organization'}
                    </h2>
                    <p class="text-xs sm:text-sm text-[#5C665F] max-w-md mx-auto leading-relaxed">
                        ${isVi ? 'Đây là cách Tempo phân nhóm các task dựa trên câu trả lời của bạn. Bạn có thể thay đổi nhóm nếu cảm thấy chưa phù hợp.' : 'Here is how Tempo grouped your tasks based on your answers. You can change any category if something feels off.'}
                    </p>
                </div>

                <!-- Category Groups -->
                <div class="space-y-5">
                    ${categories.map(cat => {
                        const catTasks = tasks.filter(t => t.priorityCategory === cat.key);
                        const countText = isVi ? `${catTasks.length} task` : `${catTasks.length} task${catTasks.length === 1 ? '' : 's'}`;
                        return `
                            <div class="bg-white border ${cat.cardBorder} rounded-2xl p-4 sm:p-5 space-y-3 shadow-2xs">
                                <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                                    <div class="space-y-0.5">
                                        <span class="px-2.5 py-0.5 rounded-full text-xs font-bold border ${cat.badge}">${cat.icon} ${cat.label}</span>
                                        <p class="text-[11px] text-[#5C665F] mt-1">${cat.desc}</p>
                                    </div>
                                    <span class="text-xs font-bold text-[#5C665F]">${countText}</span>
                                </div>

                                <div class="space-y-2">
                                    ${catTasks.length === 0 ? `<p class="text-xs text-gray-400 italic py-1">${isVi ? 'Chưa có task nào trong nhóm này.' : 'No tasks in this category.'}</p>` : ''}
                                    ${catTasks.map(t => {
                                        const dueText = t.hasDeadline
                                            ? `Deadline ${formatHumanDeadline(t.deadlineDate, t.deadlineTime, isVi)}`
                                            : (isVi ? 'Chưa có deadline' : 'No fixed deadline');
                                        return `
                                            <div class="p-3 bg-[#FCFBF9] border border-[#E8E3DF] rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                                                <div class="space-y-1 min-w-0">
                                                    <h5 class="text-xs sm:text-sm font-bold text-[#202124] truncate">${escapeHTML(t.name)}</h5>
                                                    <p class="text-[11px] text-[#5C665F] flex items-center space-x-1.5 flex-wrap">
                                                        <span>🕒 ${dueText}</span>
                                                        <button type="button"
                                                                onclick="window.TempoEmergencyFlow.openDeadlineModal('${t.id}')"
                                                                class="text-[#446A7B] hover:text-[#2D4D5C] hover:underline font-semibold text-[11px] transition cursor-pointer">
                                                            ${isVi ? 'Sửa Deadline' : 'Edit'}
                                                        </button>
                                                        <span>•</span>
                                                        <span>⏱️ ~${formatTaskDurationDisplay(t, isVi)}</span>
                                                    </p>
                                                </div>
                                                <!-- Reassign Dropdown -->
                                                <div class="shrink-0 flex items-center space-x-1.5">
                                                    <label class="text-[10px] text-gray-500 uppercase font-semibold">${isVi ? 'PHÂN LOẠI:' : 'CATEGORY:'}</label>
                                                    <select onchange="window.TempoEmergencyFlow.reassignTaskCategory('${t.id}', this.value)"
                                                            class="text-xs font-semibold border border-gray-200 rounded-lg px-2.5 py-1 bg-white text-gray-800 focus:outline-none focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] cursor-pointer">
                                                        <option value="DO_FIRST" ${t.priorityCategory === 'DO_FIRST' ? 'selected' : ''}>${isVi ? 'LÀM TRƯỚC' : 'DO FIRST'}</option>
                                                        <option value="PLAN" ${t.priorityCategory === 'PLAN' ? 'selected' : ''}>${isVi ? 'LÊN KẾ HOẠCH' : 'PLAN'}</option>
                                                        <option value="REDUCE_HELP" ${t.priorityCategory === 'REDUCE_HELP' ? 'selected' : ''}>${isVi ? 'GIẢM BỚT / NHỜ HỖ TRỢ' : 'REDUCE / HELP'}</option>
                                                        <option value="LATER" ${t.priorityCategory === 'LATER' ? 'selected' : ''}>${isVi ? 'LÀM SAU' : 'LATER'}</option>
                                                    </select>
                                                </div>
                                            </div>
                                        `;
                                    }).join('')}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>

                <!-- Navigation Controls -->
                <div class="pt-4 flex items-center justify-between border-t border-[#EAE4DF]">
                    <button onclick="window.TempoEmergencyFlow.goToStage('prioritize')" class="text-xs font-semibold text-[#5C665F] hover:text-[#202124] transition cursor-pointer">
                        ← ${isVi ? 'Quay lại phần đánh giá' : 'Back to Assessment'}
                    </button>
                    <button onclick="window.TempoEmergencyFlow.goToStage('available-time')" 
                            class="bg-[#4A6B5D] hover:bg-[#3D5A4E] text-white px-7 py-3.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs flex items-center space-x-1.5 transition cursor-pointer">
                        <span>${isVi ? 'Tiếp tục đến Thời gian làm việc →' : 'Continue to Available Time →'}</span>
                    </button>
                </div>
            </div>

            <!-- Deadline Modal Dialog (if active) -->
            ${renderDeadlineModalHTML()}
        `;
    }

    function reassignTaskCategory(taskId, newCat) {
        const task = tasks.find(t => t.id === taskId);
        if (task) {
            task.priorityCategory = newCat;
            task.hasManualPriority = true;
            renderPriorityReview();
            scheduleDraftAutosave(true);
        }
    }

    // =========================================================================
    // STAGE 5: AVAILABLE TIME (When Can You Actually Work?)
    // =========================================================================
    function formatDayLabel(dateStr, isVi = isViLocale()) {
        const todayStr = getTodayISO();
        const tomorrowStr = getTomorrowISO();

        const [y, m, d] = dateStr.split('-').map(Number);
        const targetDate = new Date(y, m - 1, d);

        if (isVi) {
            const viWeekdays = ['CN', 'THỨ 2', 'THỨ 3', 'THỨ 4', 'THỨ 5', 'THỨ 6', 'THỨ 7'];
            const viWeekday = viWeekdays[targetDate.getDay()] || '';
            const monthDay = `${d} THG ${m}`;

            if (dateStr === todayStr) {
                return `HÔM NAY · ${monthDay}`;
            } else if (dateStr === tomorrowStr) {
                return `NGÀY MAI · ${monthDay}`;
            } else {
                return `${viWeekday} · ${monthDay}`;
            }
        } else {
            const enMonths = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
            const enWeekdays = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
            const enMonth = enMonths[targetDate.getMonth()] || targetDate.toLocaleDateString('en-US', { month: 'short' }).toUpperCase();
            const weekday = enWeekdays[targetDate.getDay()] || targetDate.toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase();
            const monthDay = `${enMonth} ${d}`;

            if (dateStr === todayStr) {
                return `TODAY · ${monthDay}`;
            } else if (dateStr === tomorrowStr) {
                return `TOMORROW · ${monthDay}`;
            } else {
                return `${weekday} · ${monthDay}`;
            }
        }
    }

    function getSuggestedNextDayStr() {
        if (!availabilityDays || availabilityDays.length === 0) {
            const today = new Date();
            return getTodayISO();
        }
        const sortedDates = availabilityDays.map(d => d.date).sort();
        const maxDateStr = sortedDates[sortedDates.length - 1];
        const [y, m, d] = maxDateStr.split('-').map(Number);
        const nextDate = new Date(y, m - 1, d + 1);
        const nextY = nextDate.getFullYear();
        const nextM = String(nextDate.getMonth() + 1).padStart(2, '0');
        const nextD = String(nextDate.getDate()).padStart(2, '0');
        return `${nextY}-${nextM}-${nextD}`;
    }

    function initDefaultAvailability() {
        // If availability is already loaded and valid, don't clobber it
        if (Array.isArray(availabilityDays) && availabilityDays.length > 0) {
            return;
        }

        // Try to load persisted availabilityDays from confirmedPlan, localStorage tempo_availability_days, or tempo_working_plan
        try {
            if (confirmedPlan && Array.isArray(confirmedPlan.availabilityDays) && confirmedPlan.availabilityDays.length > 0) {
                availabilityDays = JSON.parse(JSON.stringify(confirmedPlan.availabilityDays));
                return;
            }
            const storedAvail = localStorage.getItem('tempo_availability_days');
            if (storedAvail) {
                const parsed = JSON.parse(storedAvail);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    availabilityDays = parsed;
                    return;
                }
            }
            const storedPlan = localStorage.getItem('tempo_working_plan');
            if (storedPlan) {
                const parsed = JSON.parse(storedPlan);
                if (parsed && Array.isArray(parsed.availabilityDays) && parsed.availabilityDays.length > 0) {
                    availabilityDays = parsed.availabilityDays;
                    return;
                }
            }
        } catch(e) {}

        const today = new Date();
        const todayStr = getTodayISO();
        const tomorrowStr = getTomorrowISO();

        const todayLabel = formatDayLabel(todayStr);
        const tomorrowLabel = formatDayLabel(tomorrowStr);

        // Ensure today's default block doesn't start in the past
        const currentMin = today.getHours() * 60 + today.getMinutes();
        let todayStartMin = Math.max(19 * 60, Math.ceil(currentMin / 15) * 15);
        if (todayStartMin >= 23 * 60) {
            todayStartMin = Math.max(0, Math.ceil(currentMin / 15) * 15);
            if (todayStartMin >= 1435) todayStartMin = 1425;
        }
        const todayStartStr = formatMinutesToHHMM(todayStartMin);
        const todayEndStr = todayStartMin >= 1380 ? '23:59' : '23:00';

        availabilityDays = [
            {
                date: todayStr,
                label: todayLabel,
                isUnavailable: false,
                preservedBlocks: [],
                blocks: [
                    { id: 'b_1', start: todayStartStr, end: todayEndStr, minutes: computeTimeDifferenceMinutes(todayStartStr, todayEndStr) }
                ]
            },
            {
                date: tomorrowStr,
                label: tomorrowLabel,
                isUnavailable: false,
                preservedBlocks: [],
                blocks: [
                    { id: 'b_2', start: '09:00', end: '12:00', minutes: 180 },
                    { id: 'b_3', start: '14:00', end: '17:00', minutes: 180 }
                ]
            }
        ];
    }

    function renderAvailableTime() {
        const container = document.getElementById('emergency-stage-available-time');
        if (!container) return;

        const isVi = isViLocale();
        const totalAvailableMin = calculateTotalAvailableMinutes();
        const totalWorkloadMin = calculateTotalWorkloadMinutes();
        const unknownCount = getUnknownTasksCount();
        const allUnavailable = availabilityDays.length > 0 && availabilityDays.every(d => d.isUnavailable);
        const todayStr = getTodayISO();

        container.innerHTML = `
            <div class="max-w-2xl mx-auto py-8 sm:py-10 space-y-6">
                <!-- Secondary Back Navigation -->
                <div class="flex items-center justify-between">
                    <button onclick="window.TempoEmergencyFlow.goToStage('priority-review')" 
                            class="inline-flex items-center text-xs font-semibold text-[#5C665F] hover:text-[#202124] transition py-1 group cursor-pointer">
                        <span class="mr-1.5 group-hover:-translate-x-0.5 transition-transform">←</span>
                        <span>${isVi ? 'Quay lại phần phân loại ưu tiên' : 'Back to Priority Review'}</span>
                    </button>
                </div>

                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#3D6B52]">${isVi ? 'THỜI GIAN CÓ THỂ SẮP XẾP' : 'AVAILABLE TIME'}</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        ${isVi ? 'Bạn thực sự có thể dành thời gian làm việc khi nào?' : 'When can you actually work on this?'}
                    </h2>
                    <p class="text-xs sm:text-sm text-[#5C665F] max-w-md mx-auto leading-relaxed">
                        ${isVi ? 'Cho Tempo biết thời gian bạn có thể làm việc. Chúng tôi sẽ xây dựng kế hoạch dựa trên lịch trình của bạn — không phải ngược lại.' : "Tell Tempo when you're available. We'll build the plan around your time — not the other way around."}
                    </p>
                </div>

                <!-- Shortcuts Card -->
                <div class="p-3 bg-white border border-[#E8E3DF] rounded-2xl flex flex-wrap items-center justify-between gap-2 text-xs shadow-2xs">
                    <span class="font-semibold text-gray-700">${isVi ? 'Thao tác nhanh' : 'Quick shortcuts'}:</span>
                    <div class="flex flex-wrap gap-2">
                        <button type="button" onclick="window.TempoEmergencyFlow.shortcutFreeRestOfToday()" 
                                class="px-3.5 py-1.5 bg-[#FDF2EC] text-[#783626] border border-[#ECC9BA] hover:bg-[#FAE8DE] rounded-xl font-bold transition cursor-pointer">
                            ⚡ ${isVi ? 'Rảnh trong thời gian còn lại hôm nay' : 'Free for rest of today'}
                        </button>
                        <button type="button" onclick="window.TempoEmergencyFlow.shortcutCopyTodayToTomorrow()" 
                                class="px-3.5 py-1.5 bg-[#EEF4F7] text-[#2B4E5E] border border-[#93AFBC]/40 hover:bg-[#E1EDF2] rounded-xl font-semibold transition cursor-pointer">
                            📋 ${isVi ? 'Sao chép lịch hôm nay sang ngày mai' : 'Copy today to tomorrow'}
                        </button>
                    </div>
                </div>

                <!-- All Unavailable Notice Banner (if all days unavailable) -->
                ${allUnavailable ? `
                    <div class="p-4 bg-[#FDF2EC] border border-[#ECC9BA] rounded-2xl text-center space-y-2 text-xs text-[#783626]">
                        <p class="font-bold">${isVi ? 'Bạn chưa thêm thời gian làm việc nào.' : "You haven't added any available work time yet."}</p>
                        <p class="text-stone-600">${isVi ? 'Hãy thêm ít nhất một khung giờ để Tempo có thể sắp xếp các task hiệu quả.' : 'Add at least one time block so Tempo can organize your tasks effectively.'}</p>
                        <button onclick="window.TempoEmergencyFlow.restoreAllAvailability()" 
                                class="px-4 py-2 bg-[#EDF4EF] hover:bg-[#DCE7DF] font-bold rounded-xl text-[#244634] border border-[#8EA28F]/40 transition cursor-pointer">
                            ${isVi ? 'Khôi phục thời gian mặc định' : 'Reset default availability'}
                        </button>
                    </div>
                ` : ''}

                <!-- Date Blocks -->
                <div class="space-y-4">
                    ${availabilityDays.map((day, dayIndex) => {
                        const isToday = day.date === todayStr;
                        const dayLabel = formatDayLabel(day.date, isVi);

                        if (day.isUnavailable) {
                            return `
                                <div class="bg-[#FAF8F5] border border-[#EAE4DF] border-dashed rounded-[22px] p-5 space-y-3 shadow-2xs">
                                    <div class="flex items-center justify-between pb-2 border-b border-gray-200">
                                        <div class="flex items-center space-x-2">
                                            <span class="font-heading text-xs font-extrabold tracking-wider text-gray-500 uppercase">${dayLabel}</span>
                                            <span class="px-2 py-0.5 bg-stone-200 text-stone-600 rounded-md text-[10px] font-bold">${isVi ? 'KHÔNG THỂ LÀM VIỆC' : 'NOT AVAILABLE'}</span>
                                        </div>
                                        <div class="flex items-center space-x-2">
                                            <span class="text-xs font-bold text-gray-400">0h ${isVi ? 'tổng thời gian' : 'total'}</span>
                                            ${!isToday ? `
                                                <button onclick="window.TempoEmergencyFlow.openRemoveDayModal(${dayIndex})"
                                                        class="text-[11px] text-[#A34336] hover:text-[#802D22] font-semibold transition ml-1 cursor-pointer"
                                                        title="${isVi ? 'Xóa ngày này khỏi khung thời gian lập kế hoạch' : 'Remove this day from planning window'}">
                                                    ${isVi ? 'Xóa ngày' : 'Remove day'}
                                                </button>
                                            ` : ''}
                                        </div>
                                    </div>
                                    <p class="text-xs text-[#5C665F]">
                                        ${isVi ? 'Bạn đã đánh dấu ngày này không thể làm việc. Tempo sẽ không sắp xếp task vào ngày này.' : 'You marked this day as unavailable. No tasks will be scheduled here.'}
                                    </p>
                                    <div class="flex items-center space-x-3">
                                        <button onclick="window.TempoEmergencyFlow.toggleDayUnavailable(${dayIndex})"
                                                class="text-xs text-[#4A6B5D] hover:text-[#385549] hover:underline font-bold flex items-center space-x-1 cursor-pointer">
                                            <span>${isVi ? '+ Thêm thời gian làm việc cho ngày này' : '+ Add availability for this day'}</span>
                                        </button>
                                    </div>
                                </div>
                            `;
                        }

                        const dayMinutes = calculateDayMinutes(day);

                        return `
                            <div class="bg-white border border-[#E8E3DF] rounded-[22px] p-5 space-y-3 shadow-2xs">
                                <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                                    <span class="font-heading text-xs font-extrabold tracking-wider text-[#2B4B39] uppercase">${dayLabel}</span>
                                    <div class="flex items-center space-x-3">
                                        <span class="text-xs font-bold text-gray-600">${formatDayTotalDisplay(dayMinutes, isVi)}</span>
                                        <button onclick="window.TempoEmergencyFlow.toggleDayUnavailable(${dayIndex})"
                                                class="text-[11px] text-[#5C665F] hover:text-[#202124] font-semibold transition cursor-pointer"
                                                title="${isVi ? 'Đánh dấu ngày không thể làm việc' : 'Mark day as not available'}">
                                            ${isVi ? 'Đánh dấu ngày không thể làm việc' : 'Mark day as not available'}
                                        </button>
                                        ${!isToday ? `
                                            <button onclick="window.TempoEmergencyFlow.openRemoveDayModal(${dayIndex})"
                                                    class="text-[11px] text-[#A34336] hover:text-[#802D22] font-semibold transition cursor-pointer"
                                                    title="${isVi ? 'Xóa ngày này khỏi khung thời gian lập kế hoạch' : 'Remove this day from planning window'}">
                                                ${isVi ? 'Xóa ngày' : 'Remove day'}
                                            </button>
                                        ` : ''}
                                    </div>
                                </div>

                                <!-- Time Blocks List -->
                                <div class="space-y-2.5">
                                    ${day.blocks.map((block, bIdx) => {
                                        const hasOverlapWithPrev = bIdx > 0 && parseTimeToMinutes(block.start) < parseTimeToMinutes(day.blocks[bIdx - 1].end);
                                        return `
                                            <div class="flex items-center justify-between p-2.5 bg-[#FCFBF9] border border-[#E8E3DF] rounded-xl gap-2 text-xs">
                                                <div class="flex items-center space-x-2">
                                                    <span class="font-medium text-gray-700">${isVi ? 'Từ' : 'From'}</span>
                                                    <input type="time" value="${block.start}" 
                                                           onchange="window.TempoEmergencyFlow.updateBlockTime(${dayIndex}, '${block.id}', this.value, null)"
                                                           class="px-2 py-1 border border-gray-200 rounded-lg bg-white font-semibold text-gray-800 focus:outline-none focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F]">
                                                    <span class="font-medium text-gray-700">${isVi ? 'đến' : 'to'}</span>
                                                    <input type="time" value="${block.end}" 
                                                           onchange="window.TempoEmergencyFlow.updateBlockTime(${dayIndex}, '${block.id}', null, this.value)"
                                                           class="px-2 py-1 border border-gray-200 rounded-lg bg-white font-semibold text-gray-800 focus:outline-none focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F]">
                                                    ${hasOverlapWithPrev ? `
                                                        <span class="text-[10px] text-[#783626] bg-[#FDF2EC] px-1.5 py-0.5 rounded border border-[#ECC9BA] font-semibold" 
                                                              title="${isVi ? 'Thời gian trùng nhau sẽ được tự động gộp' : 'Overlapping minutes are deduplicated automatically'}">
                                                            ${isVi ? 'Trùng giờ' : 'Overlaps'}
                                                        </span>
                                                    ` : ''}
                                                </div>
                                                <div class="flex items-center space-x-2">
                                                    <span class="text-[11px] font-bold text-[#446A7B]">${formatDurationMinutes(block.minutes, isVi)}</span>
                                                    ${day.blocks.length > 1 ? `
                                                        <button onclick="window.TempoEmergencyFlow.removeTimeBlock(${dayIndex}, '${block.id}')"
                                                                class="text-gray-400 hover:text-[#A34336] p-1 rounded-md text-sm transition cursor-pointer"
                                                                title="${isVi ? 'Xóa khung giờ này' : 'Remove this time block'}">✕</button>
                                                    ` : ''}
                                                </div>
                                            </div>
                                        `;
                                    }).join('')}
                                </div>

                                <button onclick="window.TempoEmergencyFlow.addTimeBlock(${dayIndex})" 
                                        class="text-xs text-[#4A6B5D] hover:text-[#385549] hover:underline font-bold pt-1 flex items-center space-x-1 cursor-pointer">
                                    <span>${isVi ? '+ Thêm khung giờ khác' : '+ Add another time block'}</span>
                                </button>
                            </div>
                        `;
                    }).join('')}

                    <!-- + Add another day Button / Control -->
                    <div class="pt-1">
                        ${isAddingDay ? `
                            <div class="bg-white border-2 border-dashed border-[#8EA28F]/50 rounded-[22px] p-5 space-y-3.5 shadow-2xs animate-fade-in">
                                <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                                    <h4 class="font-heading text-xs font-bold uppercase tracking-wider text-[#202124]">
                                        ${isVi ? 'Thêm thời gian làm việc cho ngày' : 'Add availability for'}
                                    </h4>
                                    <button onclick="window.TempoEmergencyFlow.cancelAddDay()" 
                                            class="text-xs font-semibold text-gray-400 hover:text-gray-600 cursor-pointer">✕ ${isVi ? 'Hủy' : 'Cancel'}</button>
                                </div>
                                <div class="flex flex-col sm:flex-row sm:items-center gap-3">
                                    <div class="space-y-1 flex-1">
                                        <label for="em-add-day-input" class="block text-[11px] font-medium text-[#5C665F]">${isVi ? 'Chọn ngày:' : 'Select date:'}</label>
                                        <input id="em-add-day-input" type="date" min="${todayStr}"
                                               value="${getSuggestedNextDayStr()}"
                                               class="w-full sm:w-auto px-3 py-2 border border-gray-200 rounded-xl bg-white font-semibold text-xs text-gray-800 focus:outline-none focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F]">
                                    </div>
                                    <div class="sm:pt-5">
                                        <button onclick="window.TempoEmergencyFlow.confirmAddDay()"
                                                class="bg-[#4A6B5D] hover:bg-[#3D5A4E] text-white px-5 py-2.5 rounded-xl font-bold text-xs shadow-xs flex items-center space-x-1.5 transition cursor-pointer">
                                            <span>${isVi ? 'Thêm ngày' : 'Add day'}</span>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ` : `
                            <button onclick="window.TempoEmergencyFlow.startAddDay()" 
                                    class="w-full py-3.5 border-2 border-dashed border-[#D5E2D9] hover:border-[#8EA28F] hover:bg-[#EDF4EF]/50 rounded-[22px] text-xs font-bold text-[#4A6B5D] flex items-center justify-center space-x-2 transition cursor-pointer">
                                <span class="text-base leading-none">+</span>
                                <span>${isVi ? 'Thêm ngày khác' : 'Add another day'}</span>
                            </button>
                        `}
                    </div>
                </div>

                <!-- Availability vs Workload Live Counter -->
                <div class="p-4 bg-[#FCFBF9] border border-[#E8E3DF] rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-3 text-xs shadow-2xs">
                    <div>
                        <span class="font-bold text-[#202124]">${isVi ? 'Tổng thời gian có thể làm việc:' : 'Total Available Time:'}</span>
                        <span class="font-extrabold text-[#244634] ml-1">${formatDurationMinutes(totalAvailableMin, isVi)}</span>
                    </div>
                    <div>
                        <span class="font-bold text-[#202124]">${isVi ? 'Ước lượng thời lượng task:' : 'Estimated Tasks Workload:'}</span>
                        <span class="font-extrabold text-[#446A7B] ml-1">${formatDurationMinutes(totalWorkloadMin, isVi)}</span>
                        ${unknownCount > 0 ? `<span class="text-[11px] text-[#5C665F] font-medium ml-1">(${isVi ? `+${unknownCount} chưa cố định` : `+${unknownCount} not fixed`})</span>` : ''}
                    </div>
                </div>

                <!-- Navigation Controls -->
                <div class="pt-4 flex items-center justify-between border-t border-[#EAE4DF]">
                    <button onclick="window.TempoEmergencyFlow.goToStage('priority-review')" class="text-xs font-semibold text-[#5C665F] hover:text-[#202124] transition cursor-pointer">
                        ${isVi ? '← Quay lại phần phân loại ưu tiên' : '← Back to Priority Review'}
                    </button>
                    <button onclick="window.TempoEmergencyFlow.continueFromAvailableTime()" 
                            class="bg-[#4A6B5D] hover:bg-[#3D5A4E] text-white px-7 py-3.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs flex items-center space-x-1.5 transition cursor-pointer">
                        <span>${isVi ? 'Kiểm tra tính khả thi & Tạo kế hoạch →' : 'Check Feasibility & Build Plan →'}</span>
                    </button>
                </div>
            </div>
            ${renderRemoveDayModalHTML()}
        `;
    }

    function startAddDay() {
        isAddingDay = true;
        renderAvailableTime();
        setTimeout(() => {
            const input = document.getElementById('em-add-day-input');
            if (input) input.focus();
        }, 50);
    }

    function cancelAddDay() {
        isAddingDay = false;
        renderAvailableTime();
    }

    function confirmAddDay() {
        const isVi = isViLocale();
        const input = document.getElementById('em-add-day-input');
        if (!input || !input.value) {
            if (window.TempoApp) window.TempoApp.showToast(isVi ? "Vui lòng chọn ngày." : "Please choose a date.");
            return;
        }

        const selectedDateStr = input.value;
        const todayStr = getTodayISO();

        // 1. Past date check
        if (selectedDateStr < todayStr) {
            if (window.TempoApp) window.TempoApp.showToast(isVi ? "Không thể chọn ngày trong quá khứ. Hôm nay là ngày sớm nhất hợp lệ." : "Cannot add a date in the past. Today is the earliest valid date.");
            return;
        }

        // 2. Duplicate date check
        const exists = availabilityDays.some(d => d.date === selectedDateStr);
        if (exists) {
            if (window.TempoApp) window.TempoApp.showToast(isVi ? "Ngày này đã có trong khoảng thời gian lập kế hoạch." : "This date is already in your planning window.");
            return;
        }

        // 3. Add day with simple initial availability state
        const newDay = {
            date: selectedDateStr,
            label: formatDayLabel(selectedDateStr, isVi),
            isUnavailable: false,
            preservedBlocks: [],
            blocks: [
                { id: 'b_' + Date.now(), start: '09:00', end: '12:00', minutes: 180 }
            ]
        };

        availabilityDays.push(newDay);
        // 4. Auto-sort chronologically
        availabilityDays.sort((a, b) => a.date.localeCompare(b.date));

        isAddingDay = false;
        renderAvailableTime();
    }

    function formatRemoveDayModalDate(day, isVi = isViLocale()) {
        if (!day || !day.date) return day ? day.label : '';
        const todayStr = getTodayISO();
        const tomorrowStr = getTomorrowISO();

        const parts = day.date.split('-');
        if (parts.length === 3) {
            const y = parseInt(parts[0], 10);
            const m = parseInt(parts[1], 10);
            const d = parseInt(parts[2], 10);
            const targetDate = new Date(y, m - 1, d);

            if (isVi) {
                const viWeekdays = ['Chủ Nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7'];
                const weekday = viWeekdays[targetDate.getDay()] || '';
                let relative = '';
                if (day.date === todayStr) relative = 'Hôm nay';
                else if (day.date === tomorrowStr) relative = 'Ngày mai';
                else relative = weekday;
                return `${d} thg ${m} · ${relative}`;
            } else {
                const monthDay = targetDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                const weekday = targetDate.toLocaleDateString('en-US', { weekday: 'short' });
                let relative = '';
                if (day.date === todayStr) relative = 'Today';
                else if (day.date === tomorrowStr) relative = 'Tomorrow';
                else relative = weekday;
                return `${monthDay} · ${relative}`;
            }
        }
        return day.label || day.date;
    }

    function getRemoveDayModalCopy(day, isVi = isViLocale()) {
        const blockCount = (day.blocks ? day.blocks.length : 0);
        if (isVi) {
            if (blockCount === 0) {
                return "Ngày này sẽ được xóa khỏi khoảng thời gian lập kế hoạch của bạn.";
            } else if (blockCount === 1) {
                return "Xóa ngày này cũng sẽ xóa 1 khung giờ làm việc bạn đã tạo cho ngày.";
            } else {
                return `Xóa ngày này cũng sẽ xóa ${blockCount} khung giờ làm việc bạn đã tạo cho ngày.`;
            }
        } else {
            if (blockCount === 0) {
                return "This day will be removed from your planning window.";
            } else if (blockCount === 1) {
                return "Removing this day will also remove the 1 availability block you've added for it.";
            } else {
                return `Removing this day will also remove the ${blockCount} availability blocks you've added for it.`;
            }
        }
    }

    function renderRemoveDayModalHTML() {
        if (!removeDayModalState) return '';
        const day = availabilityDays[removeDayModalState.dayIndex];
        if (!day) return '';

        const isVi = isViLocale();
        const dateDisplay = formatRemoveDayModalDate(day, isVi);
        const blockCopy = getRemoveDayModalCopy(day, isVi);

        return `
            <div class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in"
                 onclick="if (event.target === this) window.TempoEmergencyFlow.closeRemoveDayModal()">
                <div class="bg-white border border-[#EAE4DF] rounded-[22px] max-w-md w-full p-6 space-y-4 shadow-2xl animate-scale-up"
                     role="dialog" aria-modal="true" aria-labelledby="em-remove-day-title">
                    <div class="flex items-center justify-between pb-3 border-b border-gray-100">
                        <h3 id="em-remove-day-title" class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">
                            ${isVi ? 'Xóa ngày này?' : 'Remove this day?'}
                        </h3>
                        <button onclick="window.TempoEmergencyFlow.closeRemoveDayModal()"
                                class="text-gray-400 hover:text-gray-600 text-lg p-1 transition cursor-pointer"
                                aria-label="Close dialog">✕</button>
                    </div>

                    <div class="space-y-3">
                        <p class="font-heading text-sm sm:text-base font-bold text-[#2B4B39]">
                            ${escapeHTML(dateDisplay)}
                        </p>
                        <p class="text-xs sm:text-sm text-[#5C665F] leading-relaxed">
                            ${escapeHTML(blockCopy)}
                        </p>
                    </div>

                    <div class="pt-3 flex items-center justify-end space-x-3 border-t border-gray-100">
                        <button id="em-remove-day-cancel-btn"
                                onclick="window.TempoEmergencyFlow.closeRemoveDayModal()"
                                class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs sm:text-sm font-semibold text-gray-700 hover:bg-stone-50 transition cursor-pointer">
                            ${isVi ? 'Hủy' : 'Cancel'}
                        </button>
                        <button id="em-remove-day-confirm-btn"
                                onclick="window.TempoEmergencyFlow.confirmRemoveDay()"
                                class="px-5 py-2.5 rounded-xl bg-[#9E3E34] hover:bg-[#852E25] text-white font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer">
                            ${isVi ? 'Xóa ngày' : 'Remove day'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function openRemoveDayModal(dayIndex) {
        const day = availabilityDays[dayIndex];
        if (!day) return;

        const isVi = isViLocale();
        const todayStr = getTodayISO();
        if (day.date === todayStr) {
            if (window.TempoApp) window.TempoApp.showToast(isVi ? "Không thể xóa ngày hôm nay khỏi khoảng thời gian lập kế hoạch." : "Today cannot be removed from your planning window.");
            return;
        }

        removeDayModalState = { dayIndex };
        renderAvailableTime();
        setTimeout(() => {
            const cancelBtn = document.getElementById('em-remove-day-cancel-btn');
            if (cancelBtn) cancelBtn.focus();
        }, 50);
    }

    function closeRemoveDayModal() {
        removeDayModalState = null;
        renderAvailableTime();
    }

    function confirmRemoveDay() {
        if (!removeDayModalState) return;
        const { dayIndex } = removeDayModalState;
        if (dayIndex >= 0 && dayIndex < availabilityDays.length) {
            availabilityDays.splice(dayIndex, 1);
            scheduleDraftAutosave(true);
        }
        removeDayModalState = null;
        renderAvailableTime();
    }

    function removeDay(dayIndex) {
        openRemoveDayModal(dayIndex);
    }

    function sortAndDeduplicateDayBlocks(day) {
        if (!day || !day.blocks) return;
        day.blocks.sort((a, b) => parseTimeToMinutes(a.start) - parseTimeToMinutes(b.start));
        day.blocks.forEach(b => {
            b.minutes = computeTimeDifferenceMinutes(b.start, b.end);
        });
    }

    function updateBlockTime(dayIndex, blockId, newStart, newEnd) {
        const day = availabilityDays[dayIndex];
        if (!day) return;
        const block = day.blocks.find(b => b.id === blockId);
        if (!block) return;

        if (newStart !== null) block.start = newStart;
        if (newEnd !== null) block.end = newEnd;

        // Prevent today's blocks from starting in the past
        if (dayIndex === 0) {
            const now = new Date();
            const currentMin = now.getHours() * 60 + now.getMinutes();
            const startMin = parseTimeToMinutes(block.start);
            if (startMin < currentMin) {
                const rounded = Math.min(1425, Math.ceil(currentMin / 15) * 15);
                block.start = formatMinutesToHHMM(rounded);
                if (window.TempoApp) {
                    window.TempoApp.showToast(isViLocale() ? "Đã tự động điều chỉnh giờ bắt đầu về phía trước để không ở trong quá khứ." : "Adjusted start time forward so it's not in the past.");
                }
            }
        }

        // Ensure end time is strictly after start time
        if (parseTimeToMinutes(block.end) <= parseTimeToMinutes(block.start)) {
            const adjustedEnd = Math.min(1439, parseTimeToMinutes(block.start) + 60);
            block.end = formatMinutesToHHMM(adjustedEnd);
        }

        sortAndDeduplicateDayBlocks(day);
        renderAvailableTime();
    }

    function addTimeBlock(dayIndex) {
        const day = availabilityDays[dayIndex];
        if (!day) return;

        let defaultStart = '18:00';
        let defaultEnd = '20:00';

        if (dayIndex === 0) {
            const now = new Date();
            const currentMin = now.getHours() * 60 + now.getMinutes();
            const lastEndMin = day.blocks.length > 0 ? Math.max(...day.blocks.map(b => parseTimeToMinutes(b.end))) : currentMin;
            const nextAvailableMin = Math.max(Math.ceil(currentMin / 15) * 15, lastEndMin);
            const startMin = Math.min(1380, nextAvailableMin);
            defaultStart = formatMinutesToHHMM(startMin);
            defaultEnd = formatMinutesToHHMM(Math.min(1439, startMin + 120));
        }

        day.blocks.push({
            id: 'b_' + Date.now(),
            start: defaultStart,
            end: defaultEnd,
            minutes: computeTimeDifferenceMinutes(defaultStart, defaultEnd)
        });
        sortAndDeduplicateDayBlocks(day);
        renderAvailableTime();
    }

    function removeTimeBlock(dayIndex, blockId) {
        const day = availabilityDays[dayIndex];
        if (!day) return;
        day.blocks = day.blocks.filter(b => b.id !== blockId);
        renderAvailableTime();
    }

    function toggleDayUnavailable(dayIndex) {
        const day = availabilityDays[dayIndex];
        if (!day) return;

        if (!day.isUnavailable) {
            day.isUnavailable = true;
            day.preservedBlocks = [...day.blocks];
            day.blocks = [];
        } else {
            day.isUnavailable = false;
            if (day.preservedBlocks && day.preservedBlocks.length > 0) {
                day.blocks = [...day.preservedBlocks];
            } else {
                if (dayIndex === 0) {
                    const now = new Date();
                    const currentMin = now.getHours() * 60 + now.getMinutes();
                    const roundedMin = Math.min(1380, Math.ceil(currentMin / 15) * 15);
                    const startStr = formatMinutesToHHMM(roundedMin);
                    const endStr = roundedMin >= 1380 ? '23:59' : '23:00';
                    day.blocks = [{ id: 'b_today_' + Date.now(), start: startStr, end: endStr, minutes: computeTimeDifferenceMinutes(startStr, endStr) }];
                } else {
                    day.blocks = [{ id: 'b_day_' + Date.now(), start: '09:00', end: '12:00', minutes: 180 }];
                }
            }
            sortAndDeduplicateDayBlocks(day);
        }
        renderAvailableTime();
    }

    function restoreAllAvailability() {
        availabilityDays.forEach((day, idx) => {
            day.isUnavailable = false;
            if (day.preservedBlocks && day.preservedBlocks.length > 0) {
                day.blocks = [...day.preservedBlocks];
            } else {
                if (idx === 0) {
                    const now = new Date();
                    const currentMin = now.getHours() * 60 + now.getMinutes();
                    const roundedMin = Math.min(1380, Math.ceil(currentMin / 15) * 15);
                    const startStr = formatMinutesToHHMM(roundedMin);
                    day.blocks = [{ id: 'b_today_' + Date.now(), start: startStr, end: '23:00', minutes: computeTimeDifferenceMinutes(startStr, '23:00') }];
                } else {
                    day.blocks = [
                        { id: 'b_tom1_' + Date.now(), start: '09:00', end: '12:00', minutes: 180 },
                        { id: 'b_tom2_' + Date.now(), start: '14:00', end: '17:00', minutes: 180 }
                    ];
                }
            }
            sortAndDeduplicateDayBlocks(day);
        });
        renderAvailableTime();
    }

    function shortcutFreeRestOfToday() {
        const now = new Date();
        const currentMin = now.getHours() * 60 + now.getMinutes();
        const roundedMin = Math.min(1380, Math.ceil(currentMin / 15) * 15);
        const startStr = formatMinutesToHHMM(roundedMin);
        const endStr = roundedMin >= 1380 ? '23:59' : '23:00';

        if (availabilityDays[0]) {
            availabilityDays[0].isUnavailable = false;
            availabilityDays[0].blocks = [
                {
                    id: 'b_today_rest_' + Date.now(),
                    start: startStr,
                    end: endStr,
                    minutes: computeTimeDifferenceMinutes(startStr, endStr)
                }
            ];
            sortAndDeduplicateDayBlocks(availabilityDays[0]);
            renderAvailableTime();
        }
    }

    function shortcutCopyTodayToTomorrow() {
        if (availabilityDays[0] && availabilityDays[1]) {
            availabilityDays[1].isUnavailable = availabilityDays[0].isUnavailable;
            availabilityDays[1].blocks = availabilityDays[0].blocks.map((b, i) => ({
                id: 'b_tom_' + i + '_' + Date.now(),
                start: b.start,
                end: b.end,
                minutes: b.minutes
            }));
            sortAndDeduplicateDayBlocks(availabilityDays[1]);
            renderAvailableTime();
        }
    }

    function calculateTotalAvailableMinutes() {
        return availabilityDays.reduce((sum, day) => sum + calculateDayMinutes(day), 0);
    }

    function calculateDayMinutes(day) {
        if (!day || day.isUnavailable || !day.blocks || day.blocks.length === 0) return 0;
        
        // Convert blocks to intervals and filter valid positive ranges
        const intervals = day.blocks
            .map(b => ({
                start: parseTimeToMinutes(b.start),
                end: parseTimeToMinutes(b.end)
            }))
            .filter(intv => intv.end > intv.start);

        if (intervals.length === 0) return 0;

        // Sort intervals by start time
        intervals.sort((a, b) => a.start - b.start);

        // Merge overlapping intervals to get true non-overlapping union
        const merged = [];
        let curr = { ...intervals[0] };

        for (let i = 1; i < intervals.length; i++) {
            const next = intervals[i];
            if (next.start < curr.end) {
                curr.end = Math.max(curr.end, next.end);
            } else {
                merged.push(curr);
                curr = { ...next };
            }
        }
        merged.push(curr);

        return merged.reduce((sum, intv) => sum + (intv.end - intv.start), 0);
    }

    function formatDayTotalDisplay(mins, isVi = isViLocale()) {
        const totalWord = isVi ? 'tổng thời gian' : 'total';
        if (mins <= 0) return `0h ${totalWord}`;
        return `${formatDurationMinutes(mins, isVi)} ${totalWord}`;
    }

    function calculateTotalWorkloadMinutes() {
        return tasks
            .filter(t => !t.isUnknownDuration && !t.isLongTerm && typeof t.durationMinutes === 'number' && t.durationMinutes > 0)
            .reduce((sum, t) => sum + t.durationMinutes, 0);
    }

    function getUnknownTasksCount() {
        return tasks.filter(t => t.isUnknownDuration || t.isLongTerm || !t.durationMinutes).length;
    }

    function continueFromAvailableTime() {
        const workload = calculateTotalWorkloadMinutes();
        const available = calculateTotalAvailableMinutes();

        if (available === 0 || workload > available) {
            goToStage('feasibility');
        } else {
            goToStage('generating');
        }
    }

    // =========================================================================
    // STAGE 6: FEASIBILITY CHECK (Calmly Surfacing Workload Conflicts)
    // =========================================================================
    function renderFeasibilityCheck() {
        const container = document.getElementById('emergency-stage-feasibility');
        if (!container) return;

        const workloadMin = calculateTotalWorkloadMinutes();
        const availableMin = calculateTotalAvailableMinutes();
        const unknownCount = getUnknownTasksCount();
        const deficitMin = workloadMin - availableMin;

        container.innerHTML = `
            <div class="max-w-2xl mx-auto py-8 sm:py-10 space-y-6">
                <!-- Secondary Back Navigation -->
                <div class="flex items-center justify-between">
                    <button onclick="window.TempoEmergencyFlow.goToStage('available-time')" 
                            class="inline-flex items-center text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition py-1 group">
                        <span class="mr-1.5 group-hover:-translate-x-0.5 transition-transform">←</span>
                        <span>Back to available time</span>
                    </button>
                </div>

                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#B83D08]">FEASIBILITY CHECK</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        ${availableMin === 0 ? "You haven't scheduled available time." : "There's more work than available time."}
                    </h2>
                    <p class="text-xs sm:text-sm text-[#6F6B68] max-w-md mx-auto leading-relaxed">
                        Your known tasks need about <strong>${formatDurationMinutes(workloadMin)}</strong>${unknownCount > 0 ? ` plus <strong>${unknownCount} task${unknownCount === 1 ? '' : 's'} without a fixed estimate</strong>` : ''}. 
                        You currently have about <strong>${formatDurationMinutes(availableMin)}</strong> available before the nearest deadlines.
                    </p>
                </div>

                <!-- Comparison Visual Card -->
                <div class="bg-white border border-[#EAE4DF] rounded-[22px] p-6 space-y-4 shadow-sm">
                    <div class="space-y-3">
                        <div>
                            <div class="flex items-center justify-between text-xs font-bold text-gray-700 pb-1">
                                <span>Known Estimated Workload</span>
                                <span class="text-[#FF6B2C]">${formatDurationMinutes(workloadMin)}</span>
                            </div>
                            <div class="w-full bg-stone-100 rounded-full h-3 overflow-hidden">
                                <div class="bg-[#FF6B2C] h-full rounded-full" style="width: 100%"></div>
                            </div>
                            ${unknownCount > 0 ? `
                                <p class="text-[11px] text-[#6F6B68] mt-1 italic">
                                    * Note: Includes ${unknownCount} task${unknownCount === 1 ? '' : 's'} with "Not sure" or multi-day scope.
                                </p>
                            ` : ''}
                        </div>

                        <div>
                            <div class="flex items-center justify-between text-xs font-bold text-gray-700 pb-1">
                                <span>Available Working Time</span>
                                <span class="text-emerald-700">${formatDurationMinutes(availableMin)}</span>
                            </div>
                            <div class="w-full bg-stone-100 rounded-full h-3 overflow-hidden">
                                <div class="bg-emerald-500 h-full rounded-full" style="width: ${workloadMin > 0 ? Math.min(100, Math.round((availableMin / workloadMin) * 100)) : (availableMin > 0 ? 100 : 0)}%"></div>
                            </div>
                        </div>

                        <div class="p-3 bg-[#FFF4EC] border border-[#FFD2BA] rounded-xl text-xs text-[#B83D08] flex items-center justify-between font-semibold">
                            <span>Unallocated time gap:</span>
                            <span class="font-bold">${deficitMin > 0 ? `~${formatDurationMinutes(deficitMin)} deficit` : (availableMin === 0 ? 'No time scheduled' : 'Balanced')}</span>
                        </div>
                    </div>
                </div>

                <!-- Calm Options Choices -->
                <div class="space-y-3">
                    <p class="text-xs font-bold uppercase tracking-wider text-[#202124] text-center">
                        How would you like to handle this?
                    </p>

                    <div class="space-y-2.5">
                        <button onclick="window.TempoEmergencyFlow.goToStage('available-time')" 
                                class="w-full p-4 bg-white border border-[#EAE4DF] hover:border-[#FF6B2C] rounded-2xl flex items-center justify-between text-left transition hover:shadow-sm">
                            <div>
                                <h5 class="text-xs sm:text-sm font-bold text-[#202124]">Adjust my available time</h5>
                                <p class="text-xs text-[#6F6B68]">Open up extra evening or morning hours if your schedule allows.</p>
                            </div>
                            <span class="text-[#FF6B2C] font-bold text-sm">→</span>
                        </button>

                        <button onclick="window.TempoEmergencyFlow.goToStage('priority-review')" 
                                class="w-full p-4 bg-white border border-[#EAE4DF] hover:border-[#FF6B2C] rounded-2xl flex items-center justify-between text-left transition hover:shadow-sm">
                            <div>
                                <h5 class="text-xs sm:text-sm font-bold text-[#202124]">Reduce or postpone some tasks</h5>
                                <p class="text-xs text-[#6F6B68]">Move non-essential tasks to REDUCE/GET HELP or LATER.</p>
                            </div>
                            <span class="text-[#FF6B2C] font-bold text-sm">→</span>
                        </button>

                        <button onclick="window.TempoEmergencyFlow.goToStage('generating')" 
                                class="btn-primary w-full p-4 rounded-2xl flex items-center justify-between text-left transition shadow-md">
                            <div>
                                <h5 class="text-xs sm:text-sm font-bold text-white">Build the best plan with what I have →</h5>
                                <p class="text-xs text-white/90">Allocate what fits first; keep any unscheduled work clearly visible.</p>
                            </div>
                            <span class="text-white font-bold text-sm">→</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // STAGE 7: EMERGENCY PLAN GENERATION & REVIEW (Lightweight Timeline)
    // =========================================================================
    function renderGeneratingPlan() {
        const container = document.getElementById('emergency-stage-generating');
        if (!container) return;

        container.innerHTML = `
            <div class="max-w-md mx-auto py-16 text-center space-y-6">
                <div class="w-16 h-16 rounded-full bg-[#FFE9DC] border-2 border-[#FF6B2C] flex items-center justify-center mx-auto text-2xl animate-spin">
                    ⏳
                </div>
                <div class="space-y-2">
                    <h3 class="font-heading text-2xl font-bold text-[#202124]">Building your plan...</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">
                        Looking at deadlines, priorities, and the time you have available.
                    </p>
                </div>
            </div>
        `;

        // Generate plan deterministically after short pause for pleasant feel
        setTimeout(() => {
            buildDeterministicPlan();
            goToStage('plan-review');
        }, 600);
    }

    function buildDeterministicPlan() {
        planHasUserEdits = false;
        showPlanEditWarningModal = false;
        ignoredDeadlineWarnings.clear();

        // Priority order for sorting: DO_FIRST (1) -> PLAN (2) -> REDUCE_HELP (3) -> LATER (4)
        const rankMap = { 'DO_FIRST': 1, 'PLAN': 2, 'REDUCE_HELP': 3, 'LATER': 4 };

        // Separate known-duration finite tasks and unknown/flexible duration tasks
        const finiteTasks = tasks.filter(t => !t.isUnknownDuration && !t.isLongTerm && typeof t.durationMinutes === 'number' && t.durationMinutes > 0);
        const flexibleTasks = tasks.filter(t => t.isUnknownDuration || t.isLongTerm || !t.durationMinutes);

        const sortedFiniteTasks = [...finiteTasks].sort((a, b) => {
            const rankA = rankMap[a.priorityCategory] || 2;
            const rankB = rankMap[b.priorityCategory] || 2;
            if (rankA !== rankB) return rankA - rankB;

            // Same priority: sort by deadline urgency
            if (a.hasDeadline && b.hasDeadline) {
                return (a.deadlineDate + (a.deadlineTime || '23:59')).localeCompare(b.deadlineDate + (b.deadlineTime || '23:59'));
            }
            if (a.hasDeadline && !b.hasDeadline) return -1;
            if (!a.hasDeadline && b.hasDeadline) return 1;
            return 0;
        });

        const plannedTasks = [];
        const unallocatedTasks = [];

        // Build sequential available slots from active days
        const activeDays = availabilityDays.filter(d => !d.isUnavailable);
        let availableSlots = [];
        activeDays.forEach(day => {
            // Use merged intervals to avoid duplicate slot overlaps
            const intervals = day.blocks
                .map(b => ({ start: parseTimeToMinutes(b.start), end: parseTimeToMinutes(b.end) }))
                .filter(intv => intv.end > intv.start);
            intervals.sort((a, b) => a.start - b.start);

            const merged = [];
            let curr = intervals[0] ? { ...intervals[0] } : null;
            for (let i = 1; i < intervals.length; i++) {
                const next = intervals[i];
                if (next.start < curr.end) {
                    curr.end = Math.max(curr.end, next.end);
                } else {
                    merged.push(curr);
                    curr = { ...next };
                }
            }
            if (curr) merged.push(curr);

            merged.forEach(slot => {
                availableSlots.push({
                    dayDate: day.date,
                    dayLabel: day.label,
                    startMin: slot.start,
                    endMin: slot.end,
                    remainingMin: slot.end - slot.start
                });
            });
        });

        // Allocate finite tasks sequentially into slots
        let currentSlotIndex = 0;

        sortedFiniteTasks.forEach(task => {
            const neededMin = task.durationMinutes;
            let allocated = false;

            while (currentSlotIndex < availableSlots.length) {
                const slot = availableSlots[currentSlotIndex];
                if (slot.remainingMin >= 15) {
                    const startMinutes = slot.endMin - slot.remainingMin;
                    const durationToUse = Math.min(neededMin, slot.remainingMin);
                    const endMinutes = startMinutes + durationToUse;

                    slot.remainingMin -= durationToUse;

                    plannedTasks.push({
                        task: task,
                        dayDate: slot.dayDate,
                        dayLabel: slot.dayLabel,
                        startTime: formatMinutesToTimeString(startMinutes),
                        endTime: formatMinutesToTimeString(endMinutes),
                        startMin: startMinutes,
                        endMin: endMinutes,
                        isOverCapacity: false,
                        executionBadge: plannedTasks.length === 0 ? 'UP NEXT' : (plannedTasks.length === 1 ? 'THEN' : 'LATER'),
                        hasDeadlineConflict: checkDeadlineConflict(task, slot.dayDate, endMinutes)
                    });

                    allocated = true;
                    if (slot.remainingMin < 15) {
                        currentSlotIndex++;
                    }
                    break;
                } else {
                    currentSlotIndex++;
                }
            }

            if (!allocated) {
                unallocatedTasks.push(task);
                // Also add to plannedTasks so user can see and move it, marked as over capacity
                const fallbackDay = activeDays[activeDays.length - 1] || availabilityDays[0];
                plannedTasks.push({
                    task: task,
                    dayDate: fallbackDay ? fallbackDay.date : '',
                    dayLabel: fallbackDay ? fallbackDay.label : '',
                    startTime: null,
                    endTime: null,
                    startMin: null,
                    endMin: null,
                    isOverCapacity: true,
                    executionBadge: plannedTasks.length === 0 ? 'UP NEXT' : (plannedTasks.length === 1 ? 'THEN' : 'LATER'),
                    hasDeadlineConflict: checkDeadlineConflict(task, fallbackDay ? fallbackDay.date : '', 1440)
                });
            }
        });

        // Place flexible / unknown-duration tasks into plannedTasks without fabricating times
        const defaultFlexibleDay = activeDays[0] || availabilityDays[0];
        flexibleTasks.forEach(task => {
            plannedTasks.push({
                task: task,
                dayDate: defaultFlexibleDay ? defaultFlexibleDay.date : '',
                dayLabel: defaultFlexibleDay ? defaultFlexibleDay.label : '',
                startTime: null,
                endTime: null,
                startMin: null,
                endMin: null,
                isOverCapacity: false,
                executionBadge: plannedTasks.length === 0 ? 'UP NEXT' : (plannedTasks.length === 1 ? 'THEN' : 'LATER'),
                hasDeadlineConflict: checkDeadlineConflict(task, defaultFlexibleDay ? defaultFlexibleDay.date : '', 1440)
            });
        });

        confirmedPlan = {
            plannedTasks: plannedTasks,
            unallocatedTasks: unallocatedTasks,
            unarrangedTasks: [],
            totalWorkloadMinutes: calculateTotalWorkloadMinutes(),
            totalAvailableMinutes: calculateTotalAvailableMinutes()
        };

        recalculateTimelineSlotsPreservingOrder();
    }

    function checkDeadlineConflict(task, plannedDate, plannedEndMinutes) {
        if (!task.hasDeadline || !task.deadlineDate) return false;
        if (plannedDate > task.deadlineDate) return true;
        if (plannedDate === task.deadlineDate && task.deadlineTime) {
            const deadlineMin = parseTimeToMinutes(task.deadlineTime);
            return plannedEndMinutes > deadlineMin;
        }
        return false;
    }

    // Normalizes contiguous and overlapping availability blocks for planning without double-counting or bridging genuine gaps
    function getNormalizedWindowsForDay(day) {
        if (!day || day.isUnavailable || !day.blocks || day.blocks.length === 0) {
            return [];
        }
        const intervals = day.blocks
            .map(b => ({ start: parseTimeToMinutes(b.start), end: parseTimeToMinutes(b.end) }))
            .filter(intv => intv.end > intv.start);
        if (intervals.length === 0) return [];
        intervals.sort((a, b) => a.start - b.start);

        const merged = [];
        let curr = { ...intervals[0] };
        for (let i = 1; i < intervals.length; i++) {
            const next = intervals[i];
            if (next.start <= curr.end) {
                // Contiguous or overlapping: merge and extend end
                curr.end = Math.max(curr.end, next.end);
            } else {
                // Genuine gap: preserve gap, do not bridge
                merged.push(curr);
                curr = { ...next };
            }
        }
        merged.push(curr);
        return merged;
    }

    // Tempo default 45/15 rhythm: 45m focus, 15m break; final focus <= 45m; no break after task finishes
    function calculateTaskWorkRhythm(durationMinutes) {
        if (!durationMinutes || durationMinutes <= 0) {
            return { totalSpan: 0, focusedMinutes: 0, chunks: [], breaksCount: 0, breakMinutes: 0, segments: [] };
        }
        const chunks = [];
        let rem = durationMinutes;
        while (rem > 0) {
            const chunk = Math.min(rem, 45);
            chunks.push(chunk);
            rem -= chunk;
        }
        const segments = [];
        for (let i = 0; i < chunks.length; i++) {
            segments.push({ type: 'focus', duration: chunks[i] });
            if (i < chunks.length - 1) {
                segments.push({ type: 'break', duration: 15 });
            }
        }
        const breakMinutes = (chunks.length - 1) * 15;
        return {
            totalSpan: durationMinutes + breakMinutes,
            focusedMinutes: durationMinutes,
            chunks: chunks,
            breaksCount: Math.max(0, chunks.length - 1),
            breakMinutes: breakMinutes,
            segments: segments
        };
    }

    function recalculateTimelineSlotsPreservingOrder() {
        if (!confirmedPlan || !confirmedPlan.plannedTasks) return;

        // Group planned tasks by Day and re-sequence within normalized windows
        availabilityDays.forEach(day => {
            const isUnavailable = day.isUnavailable;
            const dayTasks = confirmedPlan.plannedTasks.filter(item => item.dayDate === day.date);

            if (isUnavailable || !day.blocks || day.blocks.length === 0) {
                dayTasks.forEach(item => {
                    item.startTime = null;
                    item.endTime = null;
                    item.startMin = null;
                    item.endMin = null;
                    item.isOverCapacity = !item.task.isUnknownDuration && !item.task.isLongTerm;
                    item.rhythm = null;
                });
                return;
            }

            const mergedWindows = getNormalizedWindowsForDay(day);
            if (mergedWindows.length === 0) {
                dayTasks.forEach(item => {
                    item.startTime = null;
                    item.endTime = null;
                    item.startMin = null;
                    item.endMin = null;
                    item.isOverCapacity = !item.task.isUnknownDuration && !item.task.isLongTerm;
                    item.rhythm = null;
                });
                return;
            }

            let wIdx = 0;
            const now = new Date();
            const todayISO = (typeof getTodayISOString === 'function') ? getTodayISOString() : (now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0') + '-' + String(now.getDate()).padStart(2, '0'));
            const isToday = day.date === todayISO;
            const currentMinNow = isToday ? (now.getHours() * 60 + now.getMinutes()) : 0;
            let currentPos = mergedWindows[0].start;

            dayTasks.forEach(item => {
                const isItemDone = item.task && (item.task.completed === true || item.task.isCompleted === true || item.task.status === 'completed');
                if (isToday && !isItemDone && currentPos < currentMinNow) {
                    currentPos = Math.min(currentMinNow, mergedWindows[wIdx] ? mergedWindows[wIdx].end : currentMinNow);
                }
                if (item.task.isUnknownDuration || item.task.isLongTerm || !item.task.durationMinutes) {
                    item.startTime = null;
                    item.endTime = null;
                    item.startMin = null;
                    item.endMin = null;
                    item.isOverCapacity = false;
                    item.rhythm = null;
                    return;
                }

                const rhythm = calculateTaskWorkRhythm(item.task.durationMinutes);
                item.rhythm = rhythm;
                const neededSpan = rhythm.totalSpan;

                let placed = false;
                while (wIdx < mergedWindows.length) {
                    const win = mergedWindows[wIdx];
                    if (currentPos < win.start) {
                        currentPos = win.start;
                    }
                    if (isToday && !isItemDone && currentPos < currentMinNow) {
                        currentPos = currentMinNow;
                    }
                    if (currentPos + neededSpan <= win.end) {
                        item.startMin = currentPos;
                        item.endMin = currentPos + neededSpan;
                        item.startTime = formatMinutesToTimeString(item.startMin);
                        item.endTime = formatMinutesToTimeString(item.endMin);
                        item.isOverCapacity = false;
                        if (item.task) {
                            item.task.scheduledDate = item.dayDate;
                            item.task.dayDate = item.dayDate;
                            item.task._dayDate = item.dayDate;
                            item.task.scheduledStartTime = item.startTime;
                            item.task.scheduledEndTime = item.endTime;
                            item.task.startTime = item.startTime;
                            item.task.endTime = item.endTime;
                            item.task._endTime = item.endTime;
                        }

                        // Transition into ~30 min recovery between completed tasks
                        currentPos = item.endMin + 30;
                        placed = true;
                        break;
                    } else if (currentPos + 15 <= win.end) {
                        item.startMin = currentPos;
                        item.endMin = Math.min(currentPos + Math.min(neededSpan, item.task.durationMinutes || 60), win.end);
                        if (item.endMin <= item.startMin) item.endMin = win.end;
                        item.startTime = formatMinutesToTimeString(item.startMin);
                        item.endTime = formatMinutesToTimeString(item.endMin);
                        item.isOverCapacity = false;
                        if (item.task) {
                            item.task.scheduledDate = item.dayDate;
                            item.task.dayDate = item.dayDate;
                            item.task._dayDate = item.dayDate;
                            item.task.scheduledStartTime = item.startTime;
                            item.task.scheduledEndTime = item.endTime;
                            item.task.startTime = item.startTime;
                            item.task.endTime = item.endTime;
                            item.task._endTime = item.endTime;
                        }
                        currentPos = item.endMin + 15;
                        placed = true;
                        break;
                    } else {
                        // Cannot fit in current window; check next window on this day
                        wIdx++;
                        if (wIdx < mergedWindows.length) {
                            currentPos = mergedWindows[wIdx].start;
                            if (isToday && !isItemDone && currentPos < currentMinNow) {
                                currentPos = currentMinNow;
                            }
                        }
                    }
                }

                if (!placed) {
                    item.startTime = null;
                    item.endTime = null;
                    item.startMin = null;
                    item.endMin = null;
                    item.isOverCapacity = true;
                    if (item.task) {
                        item.task.scheduledDate = item.dayDate;
                        item.task.dayDate = item.dayDate;
                        item.task._dayDate = item.dayDate;
                    }
                }
            });
        });

        // Recalculate execution badges and check deadline conflicts
        confirmedPlan.plannedTasks.forEach((item, idx) => {
            item.executionBadge = idx === 0 ? 'UP NEXT' : (idx === 1 ? 'THEN' : 'LATER');
            item.hasDeadlineConflict = checkDeadlineConflict(item.task, item.dayDate, item.endMin || 1440);
        });
    }

    function persistCurrentPlan() {
        if (!confirmedPlan) return;
        confirmedPlan.availabilityDays = availabilityDays;
        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function' && window.TempoPlanStore.getActivePlan('emergency')) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }
        scheduleDraftAutosave(true);
    }

    // =========================================================================
    // DRAG AND DROP TASK REORDERING & DAY MOVING
    // =========================================================================
    let draggedGlobalIndex = null;
    let isDraggingTask = false;

    function handleDragStart(e, globalIndex) {
        // Prevent drag initiation from buttons, links, or form controls inside the card
        if (e.target && e.target.closest && e.target.closest('button, input, select, textarea, a, .btn-primary')) {
            e.preventDefault();
            return false;
        }
        draggedGlobalIndex = globalIndex;
        isDraggingTask = true;
        document.body.classList.add('is-dragging-card');
        if (e.dataTransfer) {
            e.dataTransfer.setData('text/plain', String(globalIndex));
            e.dataTransfer.effectAllowed = 'move';
        }
        const card = e.currentTarget.closest('.em-timeline-card') || e.currentTarget;
        if (card) {
            card.classList.add('em-card-dragging', 'opacity-60', 'border-dashed', 'border-[#FF6B2C]', 'shadow-lg');
            card.classList.remove('opacity-40');
        }
        const handle = card ? card.querySelector('.em-drag-handle') : null;
        if (handle) {
            handle.classList.add('is-grabbing');
        }
    }

    function handleDragOver(e) {
        e.preventDefault();
        if (e.dataTransfer) {
            e.dataTransfer.dropEffect = 'move';
        }
    }

    function handleDragEnter(e) {
        e.preventDefault();
        const card = e.currentTarget.closest('.em-timeline-card');
        if (card && draggedGlobalIndex !== null) {
            const targetIdx = parseInt(card.getAttribute('data-global-index'), 10);
            if (!isNaN(targetIdx) && targetIdx !== draggedGlobalIndex) {
                card.classList.add('em-drop-target', 'bg-orange-50/60', 'border-[#FF6B2C]');
                if (draggedGlobalIndex > targetIdx) {
                    card.classList.add('border-t-2', 'border-t-[#FF6B2C]');
                    card.classList.remove('border-b-2', 'border-b-[#FF6B2C]');
                } else {
                    card.classList.add('border-b-2', 'border-b-[#FF6B2C]');
                    card.classList.remove('border-t-2', 'border-t-[#FF6B2C]');
                }
            }
        }
    }

    function handleDragLeave(e) {
        const card = e.currentTarget.closest('.em-timeline-card');
        if (card) {
            if (e.relatedTarget && card.contains(e.relatedTarget)) return;
            card.classList.remove('em-drop-target', 'bg-orange-50/60', 'border-[#FF6B2C]', 'border-t-2', 'border-t-[#FF6B2C]', 'border-b-2', 'border-b-[#FF6B2C]');
        }
    }

    function clearTaskDragStyles() {
        draggedGlobalIndex = null;
        isDraggingTask = false;
        document.body.classList.remove('is-dragging-card');
        document.querySelectorAll('.em-timeline-card').forEach(el => {
            el.classList.remove(
                'em-card-dragging',
                'opacity-60',
                'opacity-40',
                'shadow-lg',
                'border-dashed',
                'em-drop-target',
                'bg-orange-50/60',
                'border-[#FF6B2C]',
                'border-t-2',
                'border-t-[#FF6B2C]',
                'border-b-2',
                'border-b-[#FF6B2C]'
            );
        });
        document.querySelectorAll('.em-drag-handle').forEach(h => {
            h.classList.remove('is-grabbing');
        });
    }

    function handleDrop(e, targetGlobalIndex) {
        e.preventDefault();
        e.stopPropagation();
        let fromIdx = draggedGlobalIndex;
        if (fromIdx === null && e.dataTransfer) {
            const raw = e.dataTransfer.getData('text/plain');
            if (raw) fromIdx = parseInt(raw, 10);
        }
        clearTaskDragStyles();

        if (fromIdx !== null && !isNaN(fromIdx) && fromIdx !== targetGlobalIndex) {
            reorderPlannedTasks(fromIdx, targetGlobalIndex);
        }
    }

    function handleDropOnDay(e, dayDate) {
        e.preventDefault();
        e.stopPropagation();
        let fromIdx = draggedGlobalIndex;
        if (fromIdx === null && e.dataTransfer) {
            const raw = e.dataTransfer.getData('text/plain');
            if (raw) fromIdx = parseInt(raw, 10);
        }
        clearTaskDragStyles();

        if (fromIdx !== null && !isNaN(fromIdx) && dayDate) {
            moveTaskToDay(fromIdx, dayDate);
        }
    }

    function handleDragEnd(e) {
        clearTaskDragStyles();
    }

    function reorderPlannedTasks(fromIndex, toIndex) {
        if (!confirmedPlan || !confirmedPlan.plannedTasks) return;
        if (fromIndex < 0 || fromIndex >= confirmedPlan.plannedTasks.length) return;
        if (toIndex < 0 || toIndex >= confirmedPlan.plannedTasks.length) return;
        if (fromIndex === toIndex) return;

        const targetItem = confirmedPlan.plannedTasks[toIndex];
        const targetDayDate = targetItem.dayDate;
        const targetDayLabel = targetItem.dayLabel;

        const [movedItem] = confirmedPlan.plannedTasks.splice(fromIndex, 1);
        movedItem.dayDate = targetDayDate;
        movedItem.dayLabel = targetDayLabel;

        confirmedPlan.plannedTasks.splice(toIndex, 0, movedItem);

        planHasUserEdits = true;
        recalculateTimelineSlotsPreservingOrder();
        persistCurrentPlan();
        renderPlanReview();
    }

    function moveTaskToDay(fromIndex, dayDate) {
        if (!confirmedPlan || !confirmedPlan.plannedTasks) return;
        if (fromIndex < 0 || fromIndex >= confirmedPlan.plannedTasks.length) return;
        const targetDay = availabilityDays.find(d => d.date === dayDate);
        if (!targetDay) return;

        const [movedItem] = confirmedPlan.plannedTasks.splice(fromIndex, 1);
        movedItem.dayDate = dayDate;
        movedItem.dayLabel = targetDay.label;

        let lastDayIdx = -1;
        for (let i = 0; i < confirmedPlan.plannedTasks.length; i++) {
            if (confirmedPlan.plannedTasks[i].dayDate === dayDate) {
                lastDayIdx = i;
            }
        }
        if (lastDayIdx >= 0) {
            confirmedPlan.plannedTasks.splice(lastDayIdx + 1, 0, movedItem);
        } else {
            const targetDayIdx = availabilityDays.findIndex(d => d.date === dayDate);
            let insertIdx = confirmedPlan.plannedTasks.length;
            for (let i = 0; i < confirmedPlan.plannedTasks.length; i++) {
                const dayIdx = availabilityDays.findIndex(d => d.date === confirmedPlan.plannedTasks[i].dayDate);
                if (dayIdx > targetDayIdx) {
                    insertIdx = i;
                    break;
                }
            }
            confirmedPlan.plannedTasks.splice(insertIdx, 0, movedItem);
        }

        planHasUserEdits = true;
        recalculateTimelineSlotsPreservingOrder();
        persistCurrentPlan();
        renderPlanReview();
    }

    // =========================================================================
    // "DO THIS TASK LATER" & SCHEDULING MODAL
    // =========================================================================
    let scheduleModalState = null;

    function openScheduleModal(taskIndex) {
        if (!confirmedPlan || !confirmedPlan.plannedTasks || !confirmedPlan.plannedTasks[taskIndex]) return;
        const item = confirmedPlan.plannedTasks[taskIndex];
        scheduleModalState = {
            task: item.task,
            sourceType: 'arranged',
            sourceIndex: taskIndex,
            selectedWindowKey: null,
            isAddingTime: false,
            newTimeDate: getSuggestedNextDayStr(),
            newTimeStart: '18:00',
            newTimeEnd: '21:00'
        };
        const firstWin = getFirstAvailableWindowKey();
        if (firstWin) scheduleModalState.selectedWindowKey = firstWin;
        renderPlanReview();
    }

    function openScheduleModalForUnarranged(unarrangedIndex) {
        if (!confirmedPlan || !confirmedPlan.unarrangedTasks || !confirmedPlan.unarrangedTasks[unarrangedIndex]) return;
        const task = confirmedPlan.unarrangedTasks[unarrangedIndex];
        scheduleModalState = {
            task: task,
            sourceType: 'unarranged',
            sourceIndex: unarrangedIndex,
            selectedWindowKey: null,
            isAddingTime: false,
            newTimeDate: getSuggestedNextDayStr(),
            newTimeStart: '18:00',
            newTimeEnd: '21:00'
        };
        const firstWin = getFirstAvailableWindowKey();
        if (firstWin) scheduleModalState.selectedWindowKey = firstWin;
        renderPlanReview();
    }

    function closeScheduleModal() {
        scheduleModalState = null;
        renderPlanReview();
    }

    function selectScheduleWindow(windowKey) {
        if (!scheduleModalState) return;
        scheduleModalState.selectedWindowKey = windowKey;
        renderPlanReview();
    }

    function toggleModalAddTime() {
        if (!scheduleModalState) return;
        scheduleModalState.isAddingTime = !scheduleModalState.isAddingTime;
        renderPlanReview();
    }

    function cancelModalAddTime() {
        if (!scheduleModalState) return;
        scheduleModalState.isAddingTime = false;
        renderPlanReview();
    }

    function getFirstAvailableWindowKey() {
        for (const day of availabilityDays) {
            if (day.isUnavailable) continue;
            const windows = getNormalizedWindowsForDay(day);
            if (windows.length > 0) {
                return `${day.date}|${windows[0].start}|${windows[0].end}`;
            }
        }
        return null;
    }

    function saveModalAddedTime() {
        if (!scheduleModalState) return;
        const dateEl = document.getElementById('em-modal-add-date');
        const startEl = document.getElementById('em-modal-add-start');
        const endEl = document.getElementById('em-modal-add-end');

        const dateVal = dateEl ? dateEl.value : scheduleModalState.newTimeDate;
        const startVal = startEl ? startEl.value : scheduleModalState.newTimeStart;
        const endVal = endEl ? endEl.value : scheduleModalState.newTimeEnd;

        if (!dateVal || !startVal || !endVal) {
            if (window.TempoApp) window.TempoApp.showToast("Please provide date, start time, and end time.");
            return;
        }

        const todayStr = getTodayISO();
        if (dateVal < todayStr) {
            if (window.TempoApp) window.TempoApp.showToast("Không thể thêm khung giờ trong quá khứ.");
            return;
        }

        const startMin = parseTimeToMinutes(startVal);
        const endMin = parseTimeToMinutes(endVal);
        if (endMin <= startMin) {
            if (window.TempoApp) window.TempoApp.showToast("Thời gian kết thúc phải sau thời gian bắt đầu.");
            return;
        }

        let day = availabilityDays.find(d => d.date === dateVal);
        if (!day) {
            day = {
                date: dateVal,
                label: formatDayLabel(dateVal),
                isUnavailable: false,
                preservedBlocks: [],
                blocks: []
            };
            availabilityDays.push(day);
            availabilityDays.sort((a, b) => a.date.localeCompare(b.date));
        } else {
            day.isUnavailable = false;
            if (!day.blocks) day.blocks = [];
        }

        day.blocks.push({
            id: 'b_' + Date.now(),
            start: startVal,
            end: endVal,
            minutes: endMin - startMin
        });

        const normWins = getNormalizedWindowsForDay(day);
        const matchingWin = normWins.find(w => w.start <= startMin && w.end >= endMin) || normWins[0];
        if (matchingWin) {
            scheduleModalState.selectedWindowKey = `${day.date}|${matchingWin.start}|${matchingWin.end}`;
        }

        scheduleModalState.isAddingTime = false;
        persistCurrentPlan();
        renderPlanReview();
    }

    function scheduleTaskAsUnarranged() {
        if (!scheduleModalState || !confirmedPlan) return;
        const { sourceType, sourceIndex, task } = scheduleModalState;

        if (sourceType === 'arranged') {
            if (confirmedPlan.plannedTasks && confirmedPlan.plannedTasks[sourceIndex]) {
                const [removed] = confirmedPlan.plannedTasks.splice(sourceIndex, 1);
                if (!confirmedPlan.unarrangedTasks) confirmedPlan.unarrangedTasks = [];
                if (!confirmedPlan.unarrangedTasks.some(t => t.id === removed.task.id)) {
                    confirmedPlan.unarrangedTasks.push(removed.task);
                }
            }
        }

        scheduleModalState = null;
        planHasUserEdits = true;
        recalculateTimelineSlotsPreservingOrder();
        persistCurrentPlan();
        renderPlanReview();
    }

    function executeScheduleTask() {
        if (!scheduleModalState || !confirmedPlan) return;
        const { sourceType, sourceIndex, task, selectedWindowKey } = scheduleModalState;

        if (!selectedWindowKey) {
            if (window.TempoApp) window.TempoApp.showToast("Please choose an available time window, or choose 'I'll figure it out later'.");
            return;
        }

        const [targetDate] = selectedWindowKey.split('|');
        const targetDay = availabilityDays.find(d => d.date === targetDate);
        if (!targetDay) return;

        if (sourceType === 'unarranged') {
            if (confirmedPlan.unarrangedTasks && confirmedPlan.unarrangedTasks[sourceIndex]) {
                confirmedPlan.unarrangedTasks.splice(sourceIndex, 1);
            }
            confirmedPlan.plannedTasks.push({
                task: task,
                dayDate: targetDate,
                dayLabel: targetDay.label,
                startTime: null,
                endTime: null,
                startMin: null,
                endMin: null,
                isOverCapacity: false,
                executionBadge: 'LATER',
                hasDeadlineConflict: false
            });
        } else {
            const item = confirmedPlan.plannedTasks[sourceIndex];
            if (item) {
                item.dayDate = targetDate;
                item.dayLabel = targetDay.label;
            }
        }

        scheduleModalState = null;
        planHasUserEdits = true;
        recalculateTimelineSlotsPreservingOrder();
        persistCurrentPlan();
        renderPlanReview();
    }

    function renderScheduleModalHTML() {
        if (!scheduleModalState) return '';
        const { task, selectedWindowKey, isAddingTime, newTimeDate, newTimeStart, newTimeEnd } = scheduleModalState;
        if (!task) return '';
        const isVi = isViLocale();

        const availableOptions = [];
        availabilityDays.forEach(day => {
            if (day.isUnavailable) return;
            const windows = getNormalizedWindowsForDay(day);
            windows.forEach(w => {
                const winKey = `${day.date}|${w.start}|${w.end}`;
                const dayPlanned = confirmedPlan && confirmedPlan.plannedTasks
                    ? confirmedPlan.plannedTasks.filter(p => p.dayDate === day.date && p.task.id !== task.id)
                    : [];
                let occupiedMin = 0;
                dayPlanned.forEach(p => {
                    if (p.task.durationMinutes) {
                        const r = calculateTaskWorkRhythm(p.task.durationMinutes);
                        occupiedMin += r.totalSpan + 30;
                    }
                });
                const totalCap = w.end - w.start;
                const remainingMin = Math.max(0, totalCap - occupiedMin);

                let isAfterDeadline = false;
                if (task.hasDeadline && task.deadlineDate) {
                    if (day.date > task.deadlineDate) {
                        isAfterDeadline = true;
                    } else if (day.date === task.deadlineDate && task.deadlineTime) {
                        const dMin = parseTimeToMinutes(task.deadlineTime);
                        if (w.start >= dMin) {
                            isAfterDeadline = true;
                        }
                    }
                }

                availableOptions.push({
                    key: winKey,
                    dayDate: day.date,
                    dayLabel: formatDayLabel(day.date, isVi),
                    startMin: w.start,
                    endMin: w.end,
                    startStr: formatMinutesToTimeString(w.start),
                    endStr: formatMinutesToTimeString(w.end),
                    remainingMin: remainingMin,
                    totalCap: totalCap,
                    isAfterDeadline: isAfterDeadline
                });
            });
        });

        let selectedOption = availableOptions.find(opt => opt.key === selectedWindowKey);
        const hasDeadlineRisk = selectedOption ? selectedOption.isAfterDeadline : false;
        const todayStr = getTodayISO();

        return `
            <div class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in"
                 onclick="if (event.target === this) window.TempoEmergencyFlow.closeScheduleModal()">
                <div class="bg-white border border-[#D5DED7] rounded-[22px] max-w-md w-full p-6 space-y-5 shadow-2xl animate-scale-up"
                     role="dialog" aria-modal="true" aria-labelledby="em-schedule-modal-title">
                    <!-- Header -->
                    <div class="flex items-center justify-between pb-3 border-b border-gray-100">
                        <h3 id="em-schedule-modal-title" class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">
                            ${isVi ? 'Bạn muốn làm việc này khi nào?' : 'When would you like to do this?'}
                        </h3>
                        <button onclick="window.TempoEmergencyFlow.closeScheduleModal()"
                                class="text-gray-400 hover:text-gray-600 text-lg p-1 transition cursor-pointer"
                                aria-label="Close dialog">✕</button>
                    </div>

                    <!-- Task Info -->
                    <div class="space-y-1">
                        <h4 class="font-heading text-base font-bold text-[#202124]">${escapeHTML(task.name)}</h4>
                        <p class="text-xs text-[#5C665F] flex items-center space-x-2 flex-wrap">
                            <span>Deadline: <strong>${task.hasDeadline ? formatHumanDeadline(task.deadlineDate, task.deadlineTime, isVi) : (isVi ? 'Chưa có deadline' : 'No fixed deadline')}</strong></span>
                            <span>•</span>
                            <span>${isVi ? 'Thời lượng dự kiến:' : 'Estimate:'} <strong>${task.durationLabel || (isVi ? 'Chưa rõ' : 'Not sure')}</strong></span>
                        </p>
                    </div>

                    <!-- Availability Options List -->
                    <div class="space-y-2">
                        <label class="block font-bold text-[#4A6B5D] uppercase tracking-wider text-[11px]">
                            ${isVi ? 'THỜI GIAN CÓ THỂ LÀM VIỆC CỦA BẠN' : 'YOUR AVAILABLE TIME'}
                        </label>
                        ${availableOptions.length === 0 ? `
                            <p class="text-xs text-gray-500 italic py-1">${isVi ? 'Chưa có khung giờ làm việc nào. Hãy thêm thời gian bên dưới.' : 'No availability blocks added yet. Add available time below.'}</p>
                        ` : `
                            <div class="space-y-2 max-h-52 overflow-y-auto pr-1">
                                ${availableOptions.map(opt => {
                                    const isChecked = opt.key === selectedWindowKey;
                                    return `
                                        <label class="flex items-start space-x-3 p-3 rounded-xl border ${isChecked ? 'border-[#8EA28F] bg-[#EDF4EF]' : 'border-gray-200 hover:border-gray-300'} cursor-pointer transition">
                                            <input type="radio" name="em_schedule_window" value="${opt.key}"
                                                   ${isChecked ? 'checked' : ''}
                                                   onchange="window.TempoEmergencyFlow.selectScheduleWindow('${opt.key}')"
                                                   class="mt-1 text-[#4A6B5D] focus:ring-[#8EA28F]">
                                            <div class="flex-1">
                                                <div class="font-extrabold text-xs text-[#202124]">${opt.dayLabel}</div>
                                                <div class="text-xs text-[#5C665F] font-medium">${opt.startStr} – ${opt.endStr}</div>
                                                <div class="text-[11px] text-gray-500 mt-0.5">${formatDurationMinutes(opt.remainingMin)} ${isVi ? 'còn trống' : 'remaining'}</div>
                                            </div>
                                        </label>
                                    `;
                                }).join('')}
                            </div>
                        `}
                    </div>

                    <!-- Deadline Warning if selected window is after deadline -->
                    ${hasDeadlineRisk ? `
                        <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 font-medium">
                            ⚠️ ${isVi ? 'Khung giờ này nằm sau Deadline của task.' : "This time is after the task's deadline."}
                        </div>
                    ` : ''}

                    <!-- Inline Add Available Time Editor -->
                    ${isAddingTime ? `
                        <div class="p-3.5 bg-stone-50 border border-stone-200 rounded-xl space-y-3">
                            <div class="text-[11px] font-bold text-gray-700 uppercase tracking-wider">${isVi ? 'THÊM THỜI GIAN LÀM VIỆC' : 'ADD AVAILABLE TIME'}</div>
                            <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                                <div>
                                    <label class="block text-[10px] font-bold text-gray-600 uppercase">${isVi ? 'Ngày' : 'Date'}</label>
                                    <input type="date" id="em-modal-add-date" value="${newTimeDate}" min="${todayStr}"
                                           class="w-full px-2.5 py-1.5 border border-gray-300 rounded-lg text-xs bg-white">
                                </div>
                                <div>
                                    <label class="block text-[10px] font-bold text-gray-600 uppercase">${isVi ? 'Từ' : 'From'}</label>
                                    <input type="time" id="em-modal-add-start" value="${newTimeStart}"
                                           class="w-full px-2.5 py-1.5 border border-gray-300 rounded-lg text-xs bg-white">
                                </div>
                                <div>
                                    <label class="block text-[10px] font-bold text-gray-600 uppercase">${isVi ? 'Đến' : 'To'}</label>
                                    <input type="time" id="em-modal-add-end" value="${newTimeEnd}"
                                           class="w-full px-2.5 py-1.5 border border-gray-300 rounded-lg text-xs bg-white">
                                </div>
                            </div>
                            <div class="flex items-center justify-end space-x-2 pt-1">
                                <button type="button" onclick="window.TempoEmergencyFlow.cancelModalAddTime()"
                                        class="px-3 py-1.5 text-xs text-gray-600 hover:text-gray-900 font-semibold cursor-pointer">
                                    ${isVi ? 'Hủy' : 'Cancel'}
                                </button>
                                <button type="button" onclick="window.TempoEmergencyFlow.saveModalAddedTime()"
                                        class="px-3.5 py-1.5 bg-[#4A6B5D] hover:bg-[#3D5A4E] text-white text-xs font-bold rounded-lg transition shadow-2xs cursor-pointer">
                                    ${isVi ? 'Thêm giờ' : 'Add time'}
                                </button>
                            </div>
                        </div>
                    ` : `
                        <div>
                            <button type="button" onclick="window.TempoEmergencyFlow.toggleModalAddTime()"
                                    class="text-xs font-bold text-[#4A6B5D] hover:text-[#3D5A4E] hover:underline flex items-center space-x-1 cursor-pointer">
                                <span>${isVi ? '+ Thêm thời gian làm việc' : '+ Add available time'}</span>
                            </button>
                        </div>
                    `}

                    <!-- "I'll figure it out later" -->
                    <div class="pt-1">
                        <button type="button" onclick="window.TempoEmergencyFlow.scheduleTaskAsUnarranged()"
                                class="text-xs font-semibold text-[#5C665F] hover:text-[#244634] underline transition cursor-pointer">
                            ${isVi ? 'Tôi sẽ tính sau' : "I'll figure it out later"}
                        </button>
                    </div>

                    <!-- Footer Actions -->
                    <div class="pt-3 flex items-center justify-end space-x-3 border-t border-gray-100">
                        <button type="button" onclick="window.TempoEmergencyFlow.closeScheduleModal()"
                                class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs sm:text-sm font-semibold text-gray-700 hover:bg-stone-50 transition cursor-pointer">
                            ${isVi ? 'Hủy' : 'Cancel'}
                        </button>
                        <button type="button" onclick="window.TempoEmergencyFlow.executeScheduleTask()"
                                class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-[#4A6B5D] hover:bg-[#3D5A4E] text-white shadow-xs transition cursor-pointer">
                            ${isVi ? 'Xếp lịch task' : 'Schedule task'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function renderPlanReview() {
        const container = document.getElementById('emergency-stage-plan-review');
        if (!container || !confirmedPlan) return;
        const isVi = isViLocale();

        // Group planned tasks by Day in order of availabilityDays
        const daysMap = {};
        availabilityDays.forEach(day => {
            daysMap[day.date] = { dayObj: day, tasks: [] };
        });
        confirmedPlan.plannedTasks.forEach((item, idx) => {
            const targetDate = item.dayDate || (availabilityDays.find(d => d.label === item.dayLabel)?.date) || (availabilityDays[0] ? availabilityDays[0].date : '');
            if (!daysMap[targetDate]) {
                const dayObj = availabilityDays.find(d => d.date === targetDate) || { date: targetDate, label: formatDayLabel(targetDate, isVi) };
                daysMap[targetDate] = { dayObj, tasks: [] };
            }
            daysMap[targetDate].tasks.push({ ...item, globalIndex: idx });
        });

        const activeDayDates = Object.keys(daysMap).filter(dateKey => daysMap[dateKey].tasks.length > 0);
        const hasSavedActive = !!(confirmedPlan && confirmedPlan.plannedTasks && confirmedPlan.plannedTasks.length > 0 && window.TempoPlanStore && window.TempoPlanStore.getActivePlan('emergency'));
        const returnToHandoff = viewingFromHandoff || hasSavedActive;

        container.innerHTML = `
            <div class="max-w-2xl mx-auto py-8 sm:py-10 space-y-6">
                <!-- Secondary Back Navigation -->
                <div class="flex items-center justify-between">
                    <button onclick="${returnToHandoff ? "window.TempoEmergencyFlow.goToStage('handoff')" : "window.TempoEmergencyFlow.navigateBackFromPlan()"}" 
                            class="inline-flex items-center text-xs font-semibold text-[#5C665F] hover:text-[#202124] transition py-1 group cursor-pointer">
                        <span class="mr-1.5 group-hover:-translate-x-0.5 transition-transform">←</span>
                        <span>${returnToHandoff 
                            ? (isVi ? 'Quay lại tổng quan kế hoạch' : 'Back to plan overview') 
                            : (isVi ? 'Quay lại phần thời gian có thể sắp xếp' : 'Back to availability')}</span>
                    </button>
                </div>

                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#4A6B5D]">WORKING PLAN</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        ${isVi ? 'Working Plan của bạn' : 'Your Working Plan'}
                    </h2>
                    <p class="text-xs sm:text-sm text-[#5C665F] max-w-md mx-auto leading-relaxed">
                        ${isVi 
                            ? 'Đây là kế hoạch gợi ý dựa trên thông tin bạn cung cấp. Bạn có thể sắp xếp lại thứ tự, chuyển task giữa các ngày hoặc điều chỉnh thời lượng bất cứ lúc nào.' 
                            : "Here's a starting point based on what you told us. You can reorder, move between days, or adjust estimates anytime."}
                    </p>
                </div>

                <!-- Unallocated Tasks Notice (if any) -->
                ${confirmedPlan.unallocatedTasks && confirmedPlan.unallocatedTasks.length > 0 ? `
                    <div class="p-4 bg-amber-50 border border-amber-200 rounded-2xl space-y-2 text-xs text-amber-900 shadow-xs">
                        <div class="flex items-center space-x-2 font-bold">
                            <span>⚠️</span>
                            <span>${confirmedPlan.unallocatedTasks.length} task${!isVi && confirmedPlan.unallocatedTasks.length > 1 ? 's' : ''} ${isVi ? 'cần thêm thời gian làm việc' : 'need more available working blocks'}</span>
                        </div>
                        <p class="text-amber-800">
                            ${isVi ? 'Chúng tôi đã ưu tiên sắp xếp những việc vừa với khung giờ. Các việc sau vẫn cần thêm thời gian: ' : 'We scheduled what fits first. The following work still needs dedicated time: '}
                            <strong>${confirmedPlan.unallocatedTasks.map(t => escapeHTML(t.name)).join(', ')}</strong>.
                        </p>
                        <button onclick="window.TempoEmergencyFlow.navigateBackFromPlan()" 
                                class="text-xs font-bold text-[#446A7B] hover:text-[#2F4D5B] underline cursor-pointer">
                            ${isVi ? '+ Thêm thời gian làm việc để xếp hết các task' : '+ Add more availability to fit everything'}
                        </button>
                    </div>
                ` : ''}

                <!-- Lightweight Timeline -->
                <div class="space-y-6">
                    ${activeDayDates.length === 0 ? `
                        <div class="p-8 bg-white border border-[#D5DED7] rounded-[22px] text-center text-xs text-[#5C665F]">
                            ${isVi ? 'Không có task nào trong kế hoạch. Hãy quay lại phần Trút bỏ suy nghĩ để thêm task.' : 'No tasks scheduled in plan. Return to Reality Check to add tasks.'}
                        </div>
                    ` : activeDayDates.map(dayDate => {
                        const dayEntry = daysMap[dayDate];
                        const dayObj = dayEntry ? dayEntry.dayObj : null;
                        const dayTasks = dayEntry ? dayEntry.tasks : [];
                        const dayLabelFormatted = formatDayLabel(dayDate, isVi);
                        const hasDayConflict = dayTasks.some(item => item.isOverCapacity);
                        const isToday = dayDate === getTodayISO();
                        const isTomorrow = dayDate === getTomorrowISO();

                        const conflictMsg = isToday
                            ? (isVi ? 'Các task được lên lịch hôm nay vượt quá tổng thời gian bạn có thể dành ra.' : 'Tasks scheduled for TODAY exceed available capacity.')
                            : (isTomorrow
                                ? (isVi ? 'Các task được lên lịch ngày mai vượt quá tổng thời gian bạn có thể dành ra.' : 'Tasks scheduled for TOMORROW exceed available capacity.')
                                : (isVi ? `Các task được lên lịch ${dayLabelFormatted} vượt quá tổng thời gian bạn có thể dành ra.` : `Tasks scheduled for ${dayLabelFormatted} exceed available capacity.`));

                        return `
                        <div class="space-y-3"
                             ondragover="window.TempoEmergencyFlow.handleDragOver(event)"
                             ondrop="window.TempoEmergencyFlow.handleDropOnDay(event, '${dayDate}')">
                            <div class="flex items-center justify-between px-1">
                                <h4 class="font-heading text-xs font-extrabold tracking-wider text-[#4A6B5D] uppercase">
                                    ${dayLabelFormatted}
                                </h4>
                            </div>

                            ${hasDayConflict ? `
                                <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-center space-x-2">
                                    <span>⚠️</span>
                                    <span><strong>${isVi ? 'Xung đột thời gian:' : 'Availability conflict:'}</strong> ${conflictMsg}</span>
                                </div>
                            ` : ''}

                            <div class="space-y-3">
                                ${dayTasks.map((item, dIdx) => {
                                    const nextItem = dayTasks[dIdx + 1];
                                    const badgeClass = item.executionBadge === 'UP NEXT'
                                        ? 'bg-[#DCE7DF] text-[#244634] border border-[#8EA28F]/40'
                                        : (item.executionBadge === 'THEN' 
                                            ? 'bg-[#E3EDF2] text-[#244759] border border-[#93AFBC]/40' 
                                            : 'bg-[#FAF2EE] text-[#7B4B3B] border border-[#ECC9BA]/50');

                                    const badgeText = item.executionBadge === 'UP NEXT'
                                        ? (isVi ? 'TIẾP THEO' : 'UP NEXT')
                                        : (item.executionBadge === 'THEN'
                                            ? (isVi ? 'SAU ĐÓ' : 'THEN')
                                            : (isVi ? 'LÀM SAU' : 'LATER'));

                                    const isWarned = item.hasDeadlineConflict && !ignoredDeadlineWarnings.has(item.task.id);

                                    return `
                                        <div class="em-timeline-card group p-4 sm:p-5 space-y-3 shadow-xs hover:shadow-md transition-all border border-[#D5DED7] hover:border-[#CAD5CD] rounded-[22px] bg-white cursor-default"
                                             data-global-index="${item.globalIndex}"
                                             data-task-id="${item.task.id}"
                                             draggable="true"
                                             ondragstart="window.TempoEmergencyFlow.handleDragStart(event, ${item.globalIndex})"
                                             ondragover="window.TempoEmergencyFlow.handleDragOver(event)"
                                             ondragenter="window.TempoEmergencyFlow.handleDragEnter(event)"
                                             ondragleave="window.TempoEmergencyFlow.handleDragLeave(event)"
                                             ondrop="window.TempoEmergencyFlow.handleDrop(event, ${item.globalIndex})"
                                             ondragend="window.TempoEmergencyFlow.handleDragEnd(event)">
                                            <!-- Top Meta Row -->
                                            <div class="flex items-center justify-between">
                                                <div class="flex items-center space-x-2">
                                                    <!-- Subtle Drag Handle -->
                                                    <div class="em-drag-handle flex items-center justify-center text-stone-400 group-hover:text-stone-700 hover:text-[#244634] hover:bg-[#EDF4EF] px-1.5 py-1 rounded-md select-none transition-colors mr-0.5 cursor-grab active:cursor-grabbing"
                                                         title="${isVi ? 'Kéo để thay đổi thứ tự ưu tiên' : 'Drag to change execution order'}"
                                                         aria-label="${isVi ? 'Kéo để thay đổi thứ tự ưu tiên' : 'Drag to change execution order'}"
                                                         tabindex="0"
                                                         data-drag-handle="true">
                                                        <span class="text-sm font-bold tracking-widest leading-none select-none pointer-events-none">⋮⋮</span>
                                                    </div>
                                                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold tracking-wider uppercase border ${badgeClass}">
                                                        ${badgeText}
                                                    </span>
                                                    ${item.startTime && item.endTime ? `
                                                        <span class="text-xs font-extrabold text-[#202124]">
                                                            ${item.startTime} – ${item.endTime}
                                                        </span>
                                                    ` : (item.task.isUnknownDuration ? `
                                                        <span class="px-2 py-0.5 bg-stone-100 text-stone-600 rounded text-[11px] font-semibold">
                                                            ${isVi ? 'Linh hoạt / Chưa xếp giờ' : 'Flexible / Untimed'}
                                                        </span>
                                                    ` : (item.isOverCapacity ? `
                                                        <span class="px-2 py-0.5 bg-amber-100 text-amber-800 rounded text-[11px] font-semibold">
                                                            ⚠️ ${isVi ? 'Đã lên lịch (Vượt quá khung giờ)' : 'Scheduled (Beyond available blocks)'}
                                                        </span>
                                                    ` : `
                                                        <span class="px-2 py-0.5 bg-stone-100 text-stone-600 rounded text-[11px] font-semibold">
                                                            ${isVi ? 'Linh hoạt' : 'Flexible'}
                                                        </span>
                                                    `))}
                                                </div>
                                                <div class="flex items-center space-x-1.5">
                                                    <!-- "Do this task later" Action -->
                                                    <button type="button" onclick="window.TempoEmergencyFlow.openScheduleModal(${item.globalIndex})"
                                                            class="px-3 py-1.5 text-xs font-bold border border-[#D5DED7] hover:border-[#8EA28F] hover:bg-[#EDF4EF] text-[#3D4842] hover:text-[#244634] rounded-xl transition flex items-center space-x-1 shadow-2xs cursor-pointer"
                                                            title="${isVi ? 'Để task này làm sau' : 'Do this task later'}">
                                                        <span>${isVi ? 'Để task này làm sau' : 'Do this task later'}</span>
                                                    </button>
                                                </div>
                                            </div>

                                            <!-- Task Details -->
                                            <div class="space-y-1">
                                                <h4 class="font-heading text-base font-bold text-[#202124]">${escapeHTML(item.task.name)}</h4>
                                                <p class="text-xs text-[#5C665F] flex items-center space-x-1.5 flex-wrap">
                                                    <span>${isVi ? 'Thời lượng dự kiến:' : 'Estimate:'} <strong>${item.task.durationLabel || (isVi ? 'Chưa rõ' : 'Not sure')}</strong></span>
                                                    <button onclick="window.TempoEmergencyFlow.openEditEstimateModal(${item.globalIndex})" 
                                                            class="text-[#446A7B] hover:text-[#2F4D5B] hover:underline font-semibold text-[11px] cursor-pointer">
                                                        ${isVi ? 'Sửa thời lượng' : 'Edit estimate'}
                                                    </button>
                                                    <span>•</span>
                                                    <span>Deadline: ${item.task.hasDeadline ? formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime, isVi) : (isVi ? 'Chưa có deadline' : 'No fixed deadline')}</span>
                                                    <button onclick="window.TempoEmergencyFlow.openDeadlineModal('${item.task.id}')" 
                                                            class="text-[#446A7B] hover:text-[#2F4D5B] hover:underline font-semibold text-[11px] cursor-pointer">
                                                        ${isVi ? 'Sửa Deadline' : 'Edit deadline'}
                                                    </button>
                                                </p>
                                                ${item.rhythm && item.rhythm.breaksCount > 0 ? `
                                                    <div class="text-[11px] text-[#5C665F] flex items-center space-x-1 font-medium bg-[#FEFDFB] px-2.5 py-1 rounded-lg border border-[#D5DED7] w-fit mt-1">
                                                        <span class="text-[#4A6B5D] font-bold">${isVi ? 'Nhịp làm việc:' : 'Cadence:'}</span>
                                                        <span>${item.rhythm.chunks.map((c, i) => `${c}m ${isVi ? 'tập trung' : 'focus'}${i < item.rhythm.chunks.length - 1 ? (isVi ? ' + 15m nghỉ ngơi' : ' + 15m break') : ''}`).join(' • ')}</span>
                                                    </div>
                                                ` : ''}
                                            </div>

                                            <!-- Availability Conflict Banner if task exceeds day availability -->
                                            ${item.isOverCapacity ? `
                                                <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                                    <span>⚠️ <strong>${isVi ? 'Xung đột thời gian:' : 'Availability conflict:'}</strong> ${isVi ? 'Thứ tự này cần nhiều thời gian hơn quỹ thời gian hiện có của bạn trong ngày này.' : 'This order needs more time than your current availability on this day.'}</span>
                                                    <button type="button" onclick="window.TempoEmergencyFlow.openScheduleModal(${item.globalIndex})"
                                                            class="px-2.5 py-1 bg-amber-200 hover:bg-amber-300 text-amber-900 font-bold rounded-lg text-[10px] shrink-0 cursor-pointer">
                                                        ${isVi ? 'Để task này làm sau' : 'Do this task later'}
                                                    </button>
                                                </div>
                                            ` : ''}

                                            <!-- Deadline Warning Banner if reordered past deadline -->
                                            ${isWarned ? `
                                                <div data-deadline-warning="true" class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                                    <span>⚠️ <strong>${isVi ? 'Rủi ro Deadline:' : 'Deadline risk:'}</strong> ${isVi 
                                                        ? `Với thứ tự này, ${escapeHTML(item.task.name)} có Deadline vào ${formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime, true)} và có thể hoàn thành sau Deadline.` 
                                                        : `With this order, ${escapeHTML(item.task.name)} is due on ${formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime, false)} and may finish after its deadline.`}</span>
                                                    <button onclick="window.TempoEmergencyFlow.ignoreDeadlineWarning('${item.task.id}')"
                                                            class="px-2.5 py-1 bg-amber-200 hover:bg-amber-300 text-amber-900 font-bold rounded-lg text-[10px] shrink-0 cursor-pointer">
                                                        ${isVi ? 'Giữ nguyên thứ tự của tôi' : 'Keep my order'}
                                                    </button>
                                                </div>
                                            ` : ''}
                                        </div>

                                        <!-- 30m Recovery Indicator between adjacent completed tasks -->
                                        ${nextItem && item.endTime && nextItem.startTime ? `
                                            <div class="flex items-center justify-center py-0.5">
                                                <span class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#FAF2EE] text-[#7B4B3B] text-[11px] font-medium border border-[#ECC9BA]/60">
                                                    <span>🌱</span>
                                                    <span class="font-bold">${isVi ? '30m hồi phục' : '30m recovery'}</span>
                                                    <span class="text-[#ECC9BA]">•</span>
                                                    <span>${item.endTime} – ${nextItem.startTime}</span>
                                                </span>
                                            </div>
                                        ` : ''}
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    `;
                    }).join('')}
                </div>

                <!-- Dedicated UNARRANGED Section (if any) -->
                ${confirmedPlan.unarrangedTasks && confirmedPlan.unarrangedTasks.length > 0 ? `
                    <div class="space-y-3 pt-2">
                        <div class="px-1">
                            <h4 class="font-heading text-xs font-extrabold tracking-wider text-[#4A6B5D] uppercase">
                                ${isVi ? `Tasks chưa xếp lịch (${confirmedPlan.unarrangedTasks.length})` : `Unarranged Tasks (${confirmedPlan.unarrangedTasks.length})`}
                            </h4>
                            <p class="text-xs text-[#5C665F]">
                                ${isVi ? 'Các task này chưa được ấn định khung giờ cụ thể. Bạn có thể xếp lịch cho chúng bất cứ lúc nào.' : "These tasks are not currently scheduled into a specific time window. You can schedule them whenever you're ready."}
                            </p>
                        </div>
                        <div class="space-y-2">
                            ${confirmedPlan.unarrangedTasks.map((t, uIdx) => `
                                <div class="p-4 bg-white border border-[#D5DED7] rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
                                    <div>
                                        <div class="font-bold text-sm text-[#202124]">${escapeHTML(t.name)}</div>
                                        <div class="text-xs text-[#5C665F] mt-0.5">
                                            <span>${isVi ? 'Thời lượng dự kiến:' : 'Estimate:'} ~${t.durationLabel || (isVi ? 'Chưa rõ' : 'Not sure')}</span>
                                            <span class="mx-1">•</span>
                                            <span>Deadline: ${t.hasDeadline ? formatHumanDeadline(t.deadlineDate, t.deadlineTime, isVi) : (isVi ? 'Chưa có deadline' : 'No fixed deadline')}</span>
                                        </div>
                                    </div>
                                    <button onclick="window.TempoEmergencyFlow.openScheduleModalFromUnarranged(${uIdx})"
                                            class="px-3.5 py-1.5 bg-[#EDF4EF] hover:bg-[#DCE7DF] text-[#2B4B39] font-bold text-xs rounded-xl border border-[#8EA28F]/40 transition shrink-0 self-start sm:self-auto flex items-center space-x-1 shadow-2xs cursor-pointer">
                                        <span>${isVi ? 'Xếp lịch task' : 'Schedule task'}</span>
                                        <span>→</span>
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Confirmation Card -->
                ${returnToHandoff ? `
                    <div class="p-5 bg-white border border-[#D5DED7] rounded-[22px] space-y-4 text-center shadow-xs">
                        <div class="space-y-1">
                            <h4 class="font-heading text-base font-bold text-[#202124]">${isVi ? 'Kế hoạch đã được cập nhật và lưu' : 'Plan is updated and saved'}</h4>
                            <p class="text-xs text-[#5C665F]">${isVi ? 'Mọi thay đổi bạn thực hiện đều được tự động lưu lại.' : 'Any adjustments you make are automatically saved.'}</p>
                        </div>
                        <div class="pt-1 flex flex-col sm:flex-row items-center justify-center gap-3">
                            <button onclick="window.TempoEmergencyFlow.goToStage('handoff')" 
                                     class="w-full sm:w-auto px-6 py-3 rounded-xl font-bold text-xs sm:text-sm bg-[#4A6B5D] hover:bg-[#3D5A4E] text-white shadow-xs transition cursor-pointer">
                                ${isVi ? 'Quay lại Tổng quan Kế hoạch →' : 'Return to Plan Overview →'}
                            </button>
                            <button onclick="window.TempoEmergencyFlow.launchFocusZone()" 
                                     class="w-full sm:w-auto px-5 py-3 rounded-xl border border-[#4A6B5D] text-[#4A6B5D] hover:bg-[#EDF4EF] text-xs font-bold transition cursor-pointer">
                                ${isVi ? 'Bắt đầu Focus Zone →' : 'Start Focus Zone →'}
                            </button>
                        </div>
                    </div>
                ` : `
                    <div class="p-5 bg-white border border-[#D5DED7] rounded-[22px] space-y-4 text-center shadow-xs">
                        <div class="space-y-1">
                            <h4 class="font-heading text-base font-bold text-[#202124]">${isVi ? 'Bạn thấy kế hoạch này đã ổn chưa?' : 'Does this plan feel workable?'}</h4>
                            <p class="text-xs text-[#5C665F]">${isVi ? 'Bạn có thể điều chỉnh lại bất cứ lúc nào trong quá trình làm việc.' : 'You can change it again later as you make progress.'}</p>
                        </div>
                        <button id="btn-em-use-plan" onclick="window.TempoEmergencyFlow.savePlan()" 
                                 class="w-full py-3.5 rounded-xl font-bold text-sm bg-[#4A6B5D] hover:bg-[#3D5A4E] text-white shadow-xs flex items-center justify-center space-x-2 transition cursor-pointer">
                            <span>${isVi ? 'Sử dụng kế hoạch này →' : 'Use this plan →'}</span>
                        </button>
                    </div>
                `}
            </div>

            <!-- Schedule Task Modal Dialog (if active) -->
            ${renderScheduleModalHTML()}

            <!-- Move Task Modal Dialog (if active) -->
            ${renderMoveTaskModalHTML()}

            <!-- User-Edited Plan Warning Modal (if active) -->
            ${renderPlanEditWarningModalHTML()}

            <!-- Edit Estimate Modal Dialog (if active) -->
            ${renderEditEstimateModalHTML()}

            <!-- Deadline Modal Dialog (if active) -->
            ${renderDeadlineModalHTML()}
        `;
    }

    function renderPlanEditWarningModalHTML() {
        if (!showPlanEditWarningModal) return '';
        const isVi = isViLocale();

        return `
            <div class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
                <div class="bg-white border border-[#D5DED7] rounded-[22px] max-w-md w-full p-6 space-y-4 shadow-2xl">
                    <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                        <h3 class="font-heading text-sm sm:text-base font-extrabold text-[#202124]">
                            ${isVi ? 'Kế hoạch đã được chỉnh sửa' : 'Plan Modified'}
                        </h3>
                        <button onclick="window.TempoEmergencyFlow.cancelPlanEditWarning()" 
                                class="text-gray-400 hover:text-gray-600 text-lg p-1 cursor-pointer"
                                title="${isVi ? 'Đóng' : 'Close'}">✕</button>
                    </div>

                    <p class="text-xs sm:text-sm text-[#5C665F] leading-relaxed">
                        ${isVi ? 'Bạn đã thực hiện các thay đổi trên kế hoạch này. Việc cập nhật lại thời gian có thể làm thay đổi các phần đã sắp xếp.' : "You've made changes to this plan. Updating your availability may require Tempo to rebuild parts of it."}
                    </p>

                    <div class="pt-3 flex flex-col-reverse sm:flex-row items-center justify-end gap-2 border-t border-gray-100">
                        <button onclick="window.TempoEmergencyFlow.cancelPlanEditWarning()"
                                class="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition cursor-pointer">
                            ${isVi ? 'Hủy' : 'Cancel'}
                        </button>
                        <button onclick="window.TempoEmergencyFlow.confirmPlanEditWarningAndGoBack()"
                                class="w-full sm:w-auto px-5 py-2.5 rounded-xl font-bold text-xs bg-[#4A6B5D] hover:bg-[#3D5A4E] text-white shadow-xs transition cursor-pointer">
                            ${isVi ? 'Tiếp tục sửa thời gian' : 'Continue editing availability'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function navigateBackFromPlan() {
        if (planHasUserEdits) {
            showPlanEditWarningModal = true;
            renderPlanReview();
        } else {
            goToStage('available-time');
        }
    }

    function confirmPlanEditWarningAndGoBack() {
        showPlanEditWarningModal = false;
        goToStage('available-time');
    }

    function cancelPlanEditWarning() {
        showPlanEditWarningModal = false;
        renderPlanReview();
    }

    function renderMoveTaskModalHTML() {
        if (!moveModalState || !confirmedPlan || !confirmedPlan.plannedTasks) return '';
        const item = confirmedPlan.plannedTasks[moveModalState.taskIndex];
        if (!item) return '';
        const isVi = isViLocale();

        return `
            <div class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                <div class="bg-white border border-[#D5DED7] rounded-[22px] max-w-md w-full p-6 space-y-5 shadow-2xl">
                    <div class="flex items-center justify-between pb-3 border-b border-gray-100">
                        <h3 class="font-heading text-base font-extrabold text-[#202124]">
                            ${isVi ? 'Di chuyển task' : 'Move Task'}
                        </h3>
                        <button onclick="window.TempoEmergencyFlow.closeMoveTaskModal()" 
                                class="text-gray-400 hover:text-gray-600 text-lg p-1 cursor-pointer">✕</button>
                    </div>

                    <div class="space-y-4 text-xs">
                        <div>
                            <span class="text-[#5C665F] font-medium">Task:</span>
                            <p class="text-sm font-bold text-[#202124] mt-0.5">${escapeHTML(item.task.name)}</p>
                            <p class="text-[#5C665F] text-[11px]">${isVi ? 'Thời lượng dự kiến:' : 'Estimate:'} ~${item.task.durationLabel || (isVi ? 'Chưa rõ' : 'Not sure')} • Deadline: ${item.task.hasDeadline ? formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime, isVi) : (isVi ? 'Chưa có deadline' : 'No fixed deadline')}</p>
                        </div>

                        <div class="space-y-1">
                            <label class="block font-bold text-gray-700 uppercase tracking-wider text-[10px]">${isVi ? 'Chọn ngày chuyển đến:' : 'Select Target Day:'}</label>
                            <select id="em-move-target-day" onchange="window.TempoEmergencyFlow.updateMoveModalPreview(this.value, null)"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-xl bg-white font-semibold text-xs focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] focus:outline-none">
                                ${availabilityDays.map(day => {
                                    const isSelected = day.date === moveModalState.targetDayDate;
                                    const dayNameFormatted = formatDayLabel(day.date, isVi);
                                    const availText = day.isUnavailable 
                                        ? (isVi ? '(Không thể làm việc)' : '(Unavailable)') 
                                        : (isVi ? `(${formatDurationMinutes(calculateDayMinutes(day))} có thể làm việc)` : `(${formatDurationMinutes(calculateDayMinutes(day))} available)`);
                                    return `<option value="${day.date}" ${isSelected ? 'selected' : ''}>${dayNameFormatted} ${availText}</option>`;
                                }).join('')}
                            </select>
                        </div>

                        <div class="space-y-1">
                            <label class="block font-bold text-gray-700 uppercase tracking-wider text-[10px]">${isVi ? 'Vị trí trong ngày:' : 'Position in day:'}</label>
                            <select id="em-move-target-pos" onchange="window.TempoEmergencyFlow.updateMoveModalPreview(null, this.value)"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-xl bg-white font-semibold text-xs focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] focus:outline-none">
                                <option value="first" ${moveModalState.targetPosition === 'first' ? 'selected' : ''}>${isVi ? 'Đầu ngày' : 'Start of this day'}</option>
                                <option value="last" ${moveModalState.targetPosition === 'last' ? 'selected' : ''}>${isVi ? 'Cuối ngày' : 'End of this day'}</option>
                            </select>
                        </div>

                        <!-- Conflict / Feasibility Preview Warnings -->
                        <div id="em-move-modal-warnings" class="space-y-2">
                            ${renderMoveModalWarningsHTML(item, moveModalState.targetDayDate, isVi)}
                        </div>
                    </div>

                    <div class="pt-2 flex items-center justify-end space-x-2 border-t border-gray-100">
                        <button onclick="window.TempoEmergencyFlow.closeMoveTaskModal()"
                                class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition cursor-pointer">
                            ${isVi ? 'Hủy' : 'Cancel'}
                        </button>
                        <button onclick="window.TempoEmergencyFlow.executeMoveTask()"
                                class="px-5 py-2.5 rounded-xl font-bold text-xs bg-[#4A6B5D] hover:bg-[#3D5A4E] text-white shadow-xs transition cursor-pointer">
                            ${isVi ? 'Giữ lựa chọn & Di chuyển' : 'Keep my choice & Move'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function renderMoveModalWarningsHTML(item, targetDate, isVi = isViLocale()) {
        const targetDay = availabilityDays.find(d => d.date === targetDate);
        if (!targetDay) return '';

        const warnings = [];

        // 1. Availability check
        if (targetDay.isUnavailable) {
            warnings.push(`
                <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-xs">
                    ⚠️ <strong>${isVi ? 'Ngày không thể làm việc:' : 'Day is unavailable:'}</strong> ${isVi ? 'Bạn đã đánh dấu ngày này không thể làm việc. Task sẽ được xếp ở trạng thái linh hoạt/chưa có giờ cố định trừ khi bạn thêm thời gian làm việc.' : 'You marked this day as unavailable. This task will be scheduled as flexible/untimed unless availability is added.'}
                </div>
            `);
        } else {
            const dayAvailableMin = calculateDayMinutes(targetDay);
            const otherTasksDuration = confirmedPlan.plannedTasks
                .filter((p, i) => i !== moveModalState.taskIndex && p.dayDate === targetDate)
                .reduce((sum, p) => sum + (p.task.durationMinutes || 0), 0);
            const remainingMin = dayAvailableMin - otherTasksDuration;
            const taskMin = item.task.durationMinutes || 0;

            if (!item.task.isUnknownDuration && !item.task.isLongTerm && taskMin > remainingMin) {
                warnings.push(`
                    <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-xs">
                        ⚠️ <strong>${isVi ? 'Lưu ý thời gian:' : 'Time limit note:'}</strong> ${isVi ? `Ngày này chỉ còn khoảng ${formatDurationMinutes(Math.max(0, remainingMin))} trống, nhưng task này cần khoảng ${item.task.durationLabel}.` : `This day has ~${formatDurationMinutes(Math.max(0, remainingMin))} remaining, but this task needs ~${item.task.durationLabel}.`}
                    </div>
                `);
            }
        }

        // 2. Deadline check
        if (item.task.hasDeadline && item.task.deadlineDate && targetDate > item.task.deadlineDate) {
            const targetDayLabel = formatDayLabel(targetDate, isVi);
            warnings.push(`
                <div class="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-900 text-xs">
                    ⚠️ <strong>${isVi ? 'Cảnh báo Deadline:' : 'Deadline warning:'}</strong> ${isVi ? `Task này có Deadline vào ${formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime, true)}. Di chuyển sang ${targetDayLabel} sẽ khiến task bị quá Deadline.` : `This task is due on ${formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime, false)}. Moving it to ${targetDay.label} places it after its deadline.`}
                </div>
            `);
        }

        return warnings.join('');
    }

    function openMoveTaskModal(taskIndex) {
        if (!confirmedPlan || !confirmedPlan.plannedTasks || !confirmedPlan.plannedTasks[taskIndex]) return;
        const taskItem = confirmedPlan.plannedTasks[taskIndex];
        moveModalState = {
            taskIndex: taskIndex,
            targetDayDate: taskItem.dayDate,
            targetPosition: 'last'
        };
        renderPlanReview();
    }

    function closeMoveTaskModal() {
        moveModalState = null;
        renderPlanReview();
    }

    function updateMoveModalPreview(targetDate, targetPos) {
        if (!moveModalState) return;
        if (targetDate) moveModalState.targetDayDate = targetDate;
        if (targetPos) moveModalState.targetPosition = targetPos;

        const warnEl = document.getElementById('em-move-modal-warnings');
        if (warnEl && confirmedPlan && confirmedPlan.plannedTasks[moveModalState.taskIndex]) {
            warnEl.innerHTML = renderMoveModalWarningsHTML(confirmedPlan.plannedTasks[moveModalState.taskIndex], moveModalState.targetDayDate);
        }
    }

    function executeMoveTask() {
        if (!moveModalState || !confirmedPlan || !confirmedPlan.plannedTasks) return;
        const { taskIndex, targetDayDate, targetPosition } = moveModalState;
        if (taskIndex < 0 || taskIndex >= confirmedPlan.plannedTasks.length) return;

        const [movedItem] = confirmedPlan.plannedTasks.splice(taskIndex, 1);
        const targetDay = availabilityDays.find(d => d.date === targetDayDate);
        movedItem.dayDate = targetDayDate;
        movedItem.dayLabel = targetDay ? targetDay.label : movedItem.dayLabel;

        // Find indices of tasks belonging to targetDayDate in the remaining plannedTasks
        const targetDayIndices = [];
        confirmedPlan.plannedTasks.forEach((p, idx) => {
            if (p.dayDate === targetDayDate) targetDayIndices.push(idx);
        });

        if (targetDayIndices.length === 0) {
            const targetDayIdx = availabilityDays.findIndex(d => d.date === targetDayDate);
            let insertIdx = confirmedPlan.plannedTasks.length;
            for (let i = 0; i < confirmedPlan.plannedTasks.length; i++) {
                const dayIdx = availabilityDays.findIndex(d => d.date === confirmedPlan.plannedTasks[i].dayDate);
                if (dayIdx > targetDayIdx) {
                    insertIdx = i;
                    break;
                }
            }
            confirmedPlan.plannedTasks.splice(insertIdx, 0, movedItem);
        } else {
            if (targetPosition === 'first') {
                confirmedPlan.plannedTasks.splice(targetDayIndices[0], 0, movedItem);
            } else {
                const lastIdx = targetDayIndices[targetDayIndices.length - 1];
                confirmedPlan.plannedTasks.splice(lastIdx + 1, 0, movedItem);
            }
        }

        moveModalState = null;
        planHasUserEdits = true;
        recalculateTimelineSlotsPreservingOrder();
        if (window.TempoPlanStore && confirmedPlan && window.TempoPlanStore.getActivePlan('emergency')) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }
        renderPlanReview();
    }

    function movePlanTask(index, direction) {
        if (!confirmedPlan || !confirmedPlan.plannedTasks) return;
        const targetIndex = index + direction;
        if (targetIndex < 0 || targetIndex >= confirmedPlan.plannedTasks.length) return;

        const currentItem = confirmedPlan.plannedTasks[index];
        const targetItem = confirmedPlan.plannedTasks[targetIndex];

        // If swapping across different days, update the dayDate to match the target's day
        if (currentItem.dayDate !== targetItem.dayDate) {
            currentItem.dayDate = targetItem.dayDate;
            currentItem.dayLabel = targetItem.dayLabel;
        }

        const temp = confirmedPlan.plannedTasks[index];
        confirmedPlan.plannedTasks[index] = confirmedPlan.plannedTasks[targetIndex];
        confirmedPlan.plannedTasks[targetIndex] = temp;

        planHasUserEdits = true;
        // Re-assign execution badges & update timeline slots while preserving order
        recalculateTimelineSlotsPreservingOrder();
        if (window.TempoPlanStore && confirmedPlan && window.TempoPlanStore.getActivePlan('emergency')) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }
        renderPlanReview();
    }

    function ignoreDeadlineWarning(taskId) {
        ignoredDeadlineWarnings.add(taskId);
        planHasUserEdits = true;
        if (window.TempoPlanStore && confirmedPlan && window.TempoPlanStore.getActivePlan('emergency')) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }
        renderPlanReview();
    }

    function openEditEstimateModal(taskIndex) {
        if (!confirmedPlan || !confirmedPlan.plannedTasks || !confirmedPlan.plannedTasks[taskIndex]) return;
        const item = confirmedPlan.plannedTasks[taskIndex];
        const task = item.task;
        if (!task) return;

        let initialIsNotSure = !!task.isUnknownDuration;
        let initialValue = 1;
        let initialUnit = 'hours';

        if (initialIsNotSure) {
            initialValue = '';
            initialUnit = 'hours';
        } else if (task.isLongTerm) {
            if (task.customDurationValue && task.customDurationUnit) {
                initialValue = task.customDurationValue;
                initialUnit = task.customDurationUnit;
            } else if (task.durationLabel) {
                const match = task.durationLabel.match(/(\d+(?:\.\d+)?)\s*(day|week|month)s?/i);
                if (match) {
                    initialValue = parseFloat(match[1]);
                    initialUnit = match[2].toLowerCase() + 's';
                } else {
                    initialValue = 1;
                    initialUnit = 'days';
                }
            } else {
                initialValue = 1;
                initialUnit = 'days';
            }
        } else if (task.customDurationValue && task.customDurationUnit) {
            initialValue = task.customDurationValue;
            initialUnit = task.customDurationUnit;
        } else if (task.durationMinutes !== null && task.durationMinutes !== undefined) {
            const mins = task.durationMinutes;
            if (mins % 60 === 0) {
                initialValue = mins / 60;
                initialUnit = 'hours';
            } else if (mins % 30 === 0) {
                initialValue = mins / 60;
                initialUnit = 'hours';
            } else if (mins % 15 === 0 && mins >= 60) {
                initialValue = mins / 60;
                initialUnit = 'hours';
            } else if (mins < 60) {
                initialValue = mins;
                initialUnit = 'minutes';
            } else {
                initialValue = mins;
                initialUnit = 'minutes';
            }
        }

        editEstimateModalState = {
            taskIndex: taskIndex,
            task: task,
            value: initialValue,
            unit: initialUnit,
            isNotSure: initialIsNotSure,
            isSubmitting: false
        };

        renderPlanReview();
        setTimeout(() => {
            if (initialIsNotSure) {
                const cb = document.getElementById('em-edit-estimate-notsure');
                if (cb) cb.focus();
            } else {
                const valInput = document.getElementById('em-edit-estimate-value');
                if (valInput) {
                    valInput.focus();
                    valInput.select();
                }
            }
        }, 50);
    }

    function closeEditEstimateModal() {
        editEstimateModalState = null;
        renderPlanReview();
    }

    function toggleEditEstimateNotSure(isChecked) {
        if (!editEstimateModalState) return;
        editEstimateModalState.isNotSure = isChecked;

        const valInput = document.getElementById('em-edit-estimate-value');
        const unitSelect = document.getElementById('em-edit-estimate-unit');

        if (valInput && unitSelect) {
            valInput.disabled = isChecked;
            unitSelect.disabled = isChecked;
            if (isChecked) {
                valInput.classList.add('opacity-40', 'bg-stone-100', 'cursor-not-allowed');
                unitSelect.classList.add('opacity-40', 'bg-stone-100', 'cursor-not-allowed');
            } else {
                valInput.classList.remove('opacity-40', 'bg-stone-100', 'cursor-not-allowed');
                unitSelect.classList.remove('opacity-40', 'bg-stone-100', 'cursor-not-allowed');
                if (!valInput.value || parseFloat(valInput.value) <= 0) {
                    valInput.value = editEstimateModalState.value || 1;
                }
                valInput.focus();
            }
        }
    }

    function saveEditEstimate() {
        if (!editEstimateModalState || editEstimateModalState.isSubmitting) return;
        const { taskIndex, isNotSure } = editEstimateModalState;
        const item = confirmedPlan && confirmedPlan.plannedTasks ? confirmedPlan.plannedTasks[taskIndex] : null;
        if (!item || !item.task) {
            closeEditEstimateModal();
            return;
        }

        const task = item.task;

        if (isNotSure) {
            task.isUnknownDuration = true;
            task.isCustomDuration = false;
            task.isLongTerm = false;
            task.durationMinutes = null;
            task.durationLabel = 'Not sure';
            task.customDurationValue = null;
            task.customDurationUnit = null;
        } else {
            const valInput = document.getElementById('em-edit-estimate-value');
            const unitSelect = document.getElementById('em-edit-estimate-unit');
            const rawVal = valInput ? parseFloat(valInput.value) : editEstimateModalState.value;
            const selectedUnit = unitSelect ? unitSelect.value : editEstimateModalState.unit;

            if (isNaN(rawVal) || rawVal <= 0) {
                if (window.TempoApp) window.TempoApp.showToast("Vui lòng nhập thời lượng dự tính hợp lệ lớn hơn 0.");
                return;
            }

            editEstimateModalState.isSubmitting = true;

            task.isUnknownDuration = false;
            task.isCustomDuration = true;
            task.customDurationValue = rawVal;
            task.customDurationUnit = selectedUnit;

            if (selectedUnit === 'minutes') {
                const mins = Math.max(1, Math.round(rawVal));
                task.durationMinutes = mins;
                task.isLongTerm = false;
                task.durationLabel = formatDurationMinutes(mins);
            } else if (selectedUnit === 'hours') {
                const mins = Math.max(1, Math.round(rawVal * 60));
                task.durationMinutes = mins;
                task.isLongTerm = false;
                task.durationLabel = formatDurationMinutes(mins);
            } else if (selectedUnit === 'days') {
                task.durationMinutes = null;
                task.isLongTerm = true;
                task.durationLabel = rawVal === 1 ? '1 day' : `${rawVal} days`;
            } else if (selectedUnit === 'weeks') {
                task.durationMinutes = null;
                task.isLongTerm = true;
                task.durationLabel = rawVal === 1 ? '1 week' : `${rawVal} weeks`;
            } else if (selectedUnit === 'months') {
                task.durationMinutes = null;
                task.isLongTerm = true;
                task.durationLabel = rawVal === 1 ? '1 month' : `${rawVal} months`;
            }
        }

        // 1. Sync matching shared task in `tasks` array
        const sharedTask = tasks.find(t => t.id === task.id);
        if (sharedTask) {
            sharedTask.isUnknownDuration = task.isUnknownDuration;
            sharedTask.isCustomDuration = task.isCustomDuration;
            sharedTask.isLongTerm = task.isLongTerm;
            sharedTask.durationMinutes = task.durationMinutes;
            sharedTask.durationLabel = task.durationLabel;
            sharedTask.customDurationValue = task.customDurationValue;
            sharedTask.customDurationUnit = task.customDurationUnit;
        }

        // 2. Persist updated task through durable TempoPlanStore layer
        if (window.TempoPlanStore) {
            if (typeof window.TempoPlanStore.updateTaskState === 'function') {
                window.TempoPlanStore.updateTaskState(task.id, {
                    durationMinutes: task.durationMinutes,
                    durationLabel: task.durationLabel,
                    isUnknownDuration: task.isUnknownDuration,
                    isLongTerm: task.isLongTerm
                });
            }
            if (window.TempoPlanStore.getActivePlan('emergency')) {
                window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
            }
        }

        // 3. Mark user edits without silently recalculating schedule/order
        planHasUserEdits = true;
        scheduleDraftAutosave(true);

        // 4. Close modal and re-render plan review
        editEstimateModalState = null;
        renderPlanReview();
    }

    function promptEditPlanDuration(taskIndex) {
        openEditEstimateModal(taskIndex);
    }

    function renderEditEstimateModalHTML() {
        if (!editEstimateModalState) return '';
        const { taskIndex, isNotSure, value, unit } = editEstimateModalState;
        const item = confirmedPlan && confirmedPlan.plannedTasks ? confirmedPlan.plannedTasks[taskIndex] : null;
        if (!item || !item.task) return '';
        const isVi = isViLocale();
        const task = item.task;

        return `
            <div class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in"
                 onclick="if (event.target === this) window.TempoEmergencyFlow.closeEditEstimateModal()">
                <div class="bg-white border border-[#D5DED7] rounded-[22px] max-w-md w-full p-6 space-y-5 shadow-2xl animate-scale-up"
                     role="dialog" aria-modal="true" aria-labelledby="em-edit-estimate-title">
                    <div class="flex items-center justify-between pb-3 border-b border-gray-100">
                        <h3 id="em-edit-estimate-title" class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">
                            ${isVi ? 'Sửa thời lượng dự kiến' : 'Edit time estimate'}
                        </h3>
                        <button onclick="window.TempoEmergencyFlow.closeEditEstimateModal()"
                                class="text-gray-400 hover:text-gray-600 text-lg p-1 transition cursor-pointer"
                                aria-label="Close dialog">✕</button>
                    </div>

                    <div class="space-y-4">
                        <div>
                            <span class="text-[11px] font-bold text-gray-500 uppercase tracking-wider block">Task</span>
                            <p class="text-sm font-extrabold text-[#202124] mt-0.5">${escapeHTML(task.name)}</p>
                        </div>

                        <div class="space-y-2">
                            <label class="block text-xs font-semibold text-gray-700">
                                ${isVi ? 'Bạn nghĩ task này sẽ mất bao lâu?' : 'How long do you think this task will take?'}
                            </label>
                            <div class="flex items-center space-x-2">
                                <input id="em-edit-estimate-value" type="number" min="0.1" step="any"
                                       value="${isNotSure ? '' : (value !== '' && value !== null && value !== undefined ? value : '')}"
                                       ${isNotSure ? 'disabled' : ''}
                                       placeholder="${isVi ? 'VD: 1.5' : 'e.g. 1.5'}"
                                       class="w-28 px-3 py-2 text-xs sm:text-sm border border-gray-300 rounded-xl text-center font-bold text-[#202124] focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] focus:outline-none transition ${isNotSure ? 'opacity-40 bg-stone-100 cursor-not-allowed' : 'bg-white'}">
                                <select id="em-edit-estimate-unit"
                                        ${isNotSure ? 'disabled' : ''}
                                        class="px-3 py-2 text-xs sm:text-sm border border-gray-300 rounded-xl bg-white font-semibold text-[#202124] focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] focus:outline-none transition ${isNotSure ? 'opacity-40 bg-stone-100 cursor-not-allowed' : ''}">
                                    <option value="minutes" ${unit === 'minutes' ? 'selected' : ''}>${isVi ? 'phút' : 'minutes'}</option>
                                    <option value="hours" ${unit === 'hours' ? 'selected' : ''}>${isVi ? 'giờ' : 'hours'}</option>
                                    <option value="days" ${unit === 'days' ? 'selected' : ''}>${isVi ? 'ngày' : 'days'}</option>
                                    <option value="weeks" ${unit === 'weeks' ? 'selected' : ''}>${isVi ? 'tuần' : 'weeks'}</option>
                                    <option value="months" ${unit === 'months' ? 'selected' : ''}>${isVi ? 'tháng' : 'months'}</option>
                                </select>
                            </div>
                        </div>

                        <div class="pt-1">
                            <label class="inline-flex items-center space-x-2 cursor-pointer select-none">
                                <input type="checkbox" id="em-edit-estimate-notsure"
                                       ${isNotSure ? 'checked' : ''}
                                       onchange="window.TempoEmergencyFlow.toggleEditEstimateNotSure(this.checked)"
                                       class="w-4 h-4 rounded text-[#4A6B5D] focus:ring-[#8EA28F] border-gray-300">
                                <span class="text-xs sm:text-sm font-medium text-gray-700">${isVi ? 'Tôi chưa chắc chắn' : "I'm not sure yet"}</span>
                            </label>
                        </div>
                    </div>

                    <div class="pt-3 flex items-center justify-end space-x-3 border-t border-gray-100">
                        <button id="em-edit-estimate-cancel-btn"
                                onclick="window.TempoEmergencyFlow.closeEditEstimateModal()"
                                class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs sm:text-sm font-semibold text-gray-700 hover:bg-stone-50 transition cursor-pointer">
                            ${isVi ? 'Hủy' : 'Cancel'}
                        </button>
                        <button id="em-edit-estimate-save-btn"
                                onclick="window.TempoEmergencyFlow.saveEditEstimate()"
                                class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-[#4A6B5D] hover:bg-[#3D5A4E] text-white shadow-xs transition cursor-pointer">
                            ${isVi ? 'Lưu thời lượng' : 'Save estimate'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function openDeadlineModal(taskId) {
        let task = tasks.find(t => t.id === taskId);
        if (!task && confirmedPlan && confirmedPlan.plannedTasks) {
            const item = confirmedPlan.plannedTasks.find(pt => pt.task && pt.task.id === taskId);
            if (item) task = item.task;
        }
        if (!task && confirmedPlan && confirmedPlan.unallocatedTasks) {
            task = confirmedPlan.unallocatedTasks.find(t => t && t.id === taskId);
        }
        if (!task) return;

        let initialDate = task.deadlineDate || '';
        let initialTime = task.deadlineTime || '';
        if (!task.hasDeadline || !initialDate) {
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            if (!initialDate) initialDate = getTomorrowISO();
            if (!initialTime) initialTime = '21:00';
        }

        deadlineModalState = {
            taskId: task.id,
            taskName: task.name,
            hasDeadline: !!task.hasDeadline,
            deadlineDate: initialDate,
            deadlineTime: initialTime,
            isSubmitting: false
        };

        renderStageView(currentStage);

        setTimeout(() => {
            if (!task.hasDeadline) {
                const cb = document.getElementById('em-modal-nodeadline');
                if (cb) cb.focus();
            } else {
                const dInput = document.getElementById('em-modal-deadline-date');
                if (dInput) dInput.focus();
            }
        }, 50);
    }

    function closeDeadlineModal() {
        deadlineModalState = null;
        renderStageView(currentStage);
    }

    function toggleDeadlineModalNoDeadline(isChecked) {
        if (!deadlineModalState) return;
        deadlineModalState.hasDeadline = !isChecked;

        const dateInput = document.getElementById('em-modal-deadline-date');
        const timeInput = document.getElementById('em-modal-deadline-time');
        if (dateInput && timeInput) {
            dateInput.disabled = isChecked;
            timeInput.disabled = isChecked;
            dateInput.classList.toggle('opacity-40', isChecked);
            dateInput.classList.toggle('bg-stone-100', isChecked);
            dateInput.classList.toggle('cursor-not-allowed', isChecked);
            timeInput.classList.toggle('opacity-40', isChecked);
            timeInput.classList.toggle('bg-stone-100', isChecked);
            timeInput.classList.toggle('cursor-not-allowed', isChecked);
            if (!isChecked && !dateInput.value) {
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1);
                dateInput.value = getTomorrowISO();
                if (!timeInput.value) timeInput.value = '21:00';
            }
        }
    }

    function saveDeadlineModal() {
        if (!deadlineModalState || deadlineModalState.isSubmitting) return;

        const dateInput = document.getElementById('em-modal-deadline-date');
        const timeInput = document.getElementById('em-modal-deadline-time');
        const noDeadlineCb = document.getElementById('em-modal-nodeadline');

        const isNoDeadline = noDeadlineCb ? noDeadlineCb.checked : false;
        const hasDeadline = !isNoDeadline;
        const deadlineDate = hasDeadline && dateInput ? (dateInput.value || null) : null;
        const deadlineTime = hasDeadline && timeInput ? (timeInput.value || null) : null;

        const taskId = deadlineModalState.taskId;

        applyTaskUpdates(taskId, {
            hasDeadline: hasDeadline,
            deadlineDate: deadlineDate,
            deadlineTime: deadlineTime
        });

        deadlineModalState = null;
        renderStageView(currentStage);
    }

    function renderDeadlineModalHTML() {
        if (!deadlineModalState) return '';
        const { taskName, hasDeadline, deadlineDate, deadlineTime } = deadlineModalState;
        const isVi = isViLocale();

        return `
            <div class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in"
                 onclick="if (event.target === this) window.TempoEmergencyFlow.closeDeadlineModal()">
                <div class="bg-white border border-[#EAE4DF] rounded-[22px] max-w-md w-full p-6 space-y-5 shadow-2xl animate-scale-up"
                     role="dialog" aria-modal="true" aria-labelledby="em-edit-deadline-title">
                    <div class="flex items-center justify-between pb-3 border-b border-gray-100">
                        <h3 id="em-edit-deadline-title" class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">
                            ${isVi ? 'Sửa Deadline' : 'Edit deadline'}
                        </h3>
                        <button onclick="window.TempoEmergencyFlow.closeDeadlineModal()"
                                class="text-gray-400 hover:text-gray-600 text-lg p-1 transition cursor-pointer"
                                aria-label="Close dialog">✕</button>
                    </div>

                    <div class="space-y-4">
                        <div>
                            <span class="text-[11px] font-bold text-gray-500 uppercase tracking-wider block">Task</span>
                            <p class="text-sm font-extrabold text-[#202124] mt-0.5">${escapeHTML(taskName)}</p>
                        </div>

                        <div class="space-y-2">
                            <label class="block text-xs font-semibold text-gray-700">
                                ${isVi ? 'Ngày & giờ Deadline' : 'Due date & time'}
                            </label>
                            <div class="flex flex-wrap items-center gap-2.5">
                                <input id="em-modal-deadline-date" type="date" value="${deadlineDate || ''}"
                                       ${!hasDeadline ? 'disabled' : ''}
                                       class="px-3.5 py-2 text-xs sm:text-sm border border-gray-300 rounded-xl font-medium text-[#202124] focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] focus:outline-none transition ${!hasDeadline ? 'opacity-40 bg-stone-100 cursor-not-allowed' : 'bg-white'}">
                                <input id="em-modal-deadline-time" type="time" value="${deadlineTime || ''}"
                                       ${!hasDeadline ? 'disabled' : ''}
                                       class="px-3.5 py-2 text-xs sm:text-sm border border-gray-300 rounded-xl font-medium text-[#202124] focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] focus:outline-none transition ${!hasDeadline ? 'opacity-40 bg-stone-100 cursor-not-allowed' : 'bg-white'}">
                            </div>
                        </div>

                        <div class="pt-1">
                            <label class="inline-flex items-center space-x-2 cursor-pointer select-none">
                                <input type="checkbox" id="em-modal-nodeadline"
                                       ${!hasDeadline ? 'checked' : ''}
                                       onchange="window.TempoEmergencyFlow.toggleDeadlineModalNoDeadline(this.checked)"
                                       class="w-4 h-4 rounded text-[#4A6B5D] focus:ring-[#8EA28F] border-gray-300">
                                <span class="text-xs sm:text-sm font-medium text-gray-700">${isVi ? 'Chưa có deadline' : 'No fixed deadline'}</span>
                            </label>
                        </div>
                    </div>

                    <div class="pt-3 flex items-center justify-end space-x-3 border-t border-gray-100">
                        <button id="em-edit-deadline-cancel-btn"
                                onclick="window.TempoEmergencyFlow.closeDeadlineModal()"
                                class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs sm:text-sm font-semibold text-gray-700 hover:bg-stone-50 transition cursor-pointer">
                            ${isVi ? 'Hủy' : 'Cancel'}
                        </button>
                        <button id="em-edit-deadline-save-btn"
                                onclick="window.TempoEmergencyFlow.saveDeadlineModal()"
                                class="bg-[#4A6B5D] hover:bg-[#3D5A4E] text-white px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer">
                            ${isVi ? 'Lưu thay đổi' : 'Save changes'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    async function confirmPlanAndProceed() {
        if (!confirmedPlan || !confirmedPlan.plannedTasks || confirmedPlan.plannedTasks.length === 0) {
            goToStage('reality-check');
            return;
        }

        await savePlan();
    }

    function reviewStepBreakdown() {
        // Step Breakdown page has been removed from Urmode workflow
        goToStage(confirmedPlan ? 'handoff' : 'plan-review');
    }

    // =========================================================================
    // STAGE 8: BREAK DOWN TASKS (Removed from workflow)
    // =========================================================================
    function renderBreakdown() {
        const container = document.getElementById('emergency-stage-breakdown');
        if (container) {
            container.innerHTML = '';
            container.classList.add('hidden');
        }
        goToStage(confirmedPlan ? 'handoff' : 'plan-review');
    }

    function formatSubtaskDurationDisplay(mins) {
        if (!mins || mins <= 0) return '—';
        if (mins < 60) return `${mins} min`;
        const h = Math.floor(mins / 60);
        const m = mins % 60;
        return m > 0 ? `${h}h ${m}m` : `${h}h`;
    }

    function renderSubtaskDurationEditorModal() {
        if (editingSubtaskIndex === null) return '';
        const planItem = confirmedPlan ? confirmedPlan.plannedTasks[breakdownIndex] : null;
        if (!planItem || !planItem.task.subtasks || !planItem.task.subtasks[editingSubtaskIndex]) return '';

        const step = planItem.task.subtasks[editingSubtaskIndex];
        const sIdx = editingSubtaskIndex;

        let initialVal = '';
        let initialUnit = 'minutes';
        if (step.durationMinutes && step.durationMinutes > 0) {
            if (step.durationMinutes >= 60 && step.durationMinutes % 60 === 0) {
                initialVal = step.durationMinutes / 60;
                initialUnit = 'hours';
            } else {
                initialVal = step.durationMinutes;
                initialUnit = 'minutes';
            }
        }

        return `
            <div class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
                <div class="bg-white border border-[#EAE4DF] rounded-[22px] max-w-xs w-full p-5 space-y-4 shadow-2xl">
                    <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                        <h4 class="font-heading text-xs font-bold uppercase tracking-wider text-[#202124]">
                            Step Estimate
                        </h4>
                        <button onclick="window.TempoEmergencyFlow.closeSubtaskDurationEditor()" 
                                class="text-gray-400 hover:text-gray-600 text-sm p-1"
                                title="Close">✕</button>
                    </div>

                    <div class="space-y-1">
                        <span class="text-[10px] uppercase font-bold text-gray-400">Step:</span>
                        <p class="text-xs font-bold text-[#202124] truncate">${escapeHTML(step.title)}</p>
                    </div>

                    <div class="space-y-1.5">
                        <label class="block text-[11px] font-semibold text-gray-700">Duration estimate:</label>
                        <div class="flex items-center space-x-2">
                            <input id="em-subtask-edit-val" type="number" min="1" step="any"
                                   value="${initialVal}"
                                   placeholder="e.g. 15"
                                   onkeydown="if(event.key === 'Enter') window.TempoEmergencyFlow.saveSubtaskDuration(${sIdx})"
                                   class="w-20 px-3 py-1.5 text-xs border border-gray-300 rounded-xl text-center font-bold focus:ring-1 focus:ring-[#FF6B2C] focus:outline-none">
                            <select id="em-subtask-edit-unit"
                                    class="flex-1 px-3 py-1.5 text-xs border border-gray-300 rounded-xl bg-white font-semibold focus:ring-1 focus:ring-[#FF6B2C] focus:outline-none">
                                <option value="minutes" ${initialUnit === 'minutes' ? 'selected' : ''}>minutes</option>
                                <option value="hours" ${initialUnit === 'hours' ? 'selected' : ''}>hours</option>
                            </select>
                        </div>
                    </div>

                    <div class="pt-2 flex items-center justify-between border-t border-gray-100">
                        <button onclick="window.TempoEmergencyFlow.clearSubtaskDuration(${sIdx})"
                                class="text-xs text-stone-500 hover:text-rose-600 font-semibold underline transition">
                            No estimate
                        </button>
                        <div class="flex items-center space-x-2">
                            <button onclick="window.TempoEmergencyFlow.closeSubtaskDurationEditor()"
                                    class="px-3 py-1.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-600 hover:bg-stone-50 transition">
                                Cancel
                            </button>
                            <button onclick="window.TempoEmergencyFlow.saveSubtaskDuration(${sIdx})"
                                    class="btn-primary px-4 py-1.5 rounded-xl font-bold text-xs shadow-sm transition">
                                Save
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    function openSubtaskDurationEditor(sIdx) {
        editingSubtaskIndex = sIdx;
        renderBreakdown();
        setTimeout(() => {
            const input = document.getElementById('em-subtask-edit-val');
            if (input) {
                input.focus();
                input.select();
            }
        }, 50);
    }

    function closeSubtaskDurationEditor() {
        editingSubtaskIndex = null;
        renderBreakdown();
    }

    function saveSubtaskDuration(sIdx) {
        const planItem = confirmedPlan ? confirmedPlan.plannedTasks[breakdownIndex] : null;
        if (!planItem || !planItem.task.subtasks || !planItem.task.subtasks[sIdx]) return;

        const inputEl = document.getElementById('em-subtask-edit-val');
        const unitEl = document.getElementById('em-subtask-edit-unit');
        if (!inputEl) return;

        const rawVal = parseFloat(inputEl.value);
        const unit = unitEl ? unitEl.value : 'minutes';

        if (isNaN(rawVal) || rawVal <= 0) {
            if (window.TempoApp) {
                window.TempoApp.showToast("Please enter a valid estimate greater than 0, or click 'No estimate'.");
            }
            return;
        }

        let finalMinutes = 0;
        if (unit === 'hours') {
            finalMinutes = Math.round(rawVal * 60);
        } else {
            finalMinutes = Math.round(rawVal);
        }

        planItem.task.subtasks[sIdx].durationMinutes = finalMinutes;
        if (planItem.task) {
            dismissedMismatchForTask[planItem.task.id] = false;
        }
        editingSubtaskIndex = null;
        renderBreakdown();
        scheduleDraftAutosave();
        if (window.TempoPlanStore && confirmedPlan) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }
    }

    function clearSubtaskDuration(sIdx) {
        const planItem = confirmedPlan ? confirmedPlan.plannedTasks[breakdownIndex] : null;
        if (!planItem || !planItem.task.subtasks || !planItem.task.subtasks[sIdx]) return;

        planItem.task.subtasks[sIdx].durationMinutes = null;
        if (planItem.task) {
            dismissedMismatchForTask[planItem.task.id] = false;
        }
        editingSubtaskIndex = null;
        renderBreakdown();
        scheduleDraftAutosave();
        if (window.TempoPlanStore && confirmedPlan) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }
    }

    // Context-aware AI Suggestions generator
    function generateAiSuggestionsForTask(task) {
        const lower = (task.name || '').toLowerCase();
        let rawSuggestions = [];

        if (lower.includes('report') || lower.includes('essay') || lower.includes('paper') || lower.includes('thesis') || lower.includes('writing') || lower.includes('draft') || lower.includes('article')) {
            rawSuggestions = [
                { title: 'Open rubric and paste prompt into a clean doc', durationMinutes: 15 },
                { title: 'Write bullet outline for the 3 main sections', durationMinutes: 25 },
                { title: 'Draft rough introduction and first body paragraph', durationMinutes: 30 },
                { title: 'Proofread and check reference citations', durationMinutes: 20 }
            ];
        } else if (lower.includes('lab') || lower.includes('code') || lower.includes('project') || lower.includes('program') || lower.includes('bug') || lower.includes('app') || lower.includes('software') || lower.includes('dev')) {
            rawSuggestions = [
                { title: 'Review failing test case or assignment criteria', durationMinutes: 15 },
                { title: 'Outline pseudo-code solution for core logic', durationMinutes: 20 },
                { title: 'Implement working fix and test locally', durationMinutes: 30 },
                { title: 'Check edge cases and prepare submission files', durationMinutes: 15 }
            ];
        } else if (lower.includes('read') || lower.includes('reading') || lower.includes('chapter') || lower.includes('book') || lower.includes('article') || lower.includes('literature') || lower.includes('study')) {
            rawSuggestions = [
                { title: 'Skim headings, section summaries, and key figures', durationMinutes: 15 },
                { title: 'Read first half and note 3 important concepts', durationMinutes: 25 },
                { title: 'Finish reading and draft short summary of key takeaways', durationMinutes: 20 }
            ];
        } else if (lower.includes('exam') || lower.includes('quiz') || lower.includes('test') || lower.includes('midterm') || lower.includes('final') || lower.includes('prep')) {
            rawSuggestions = [
                { title: 'Gather lecture slides, notes, and past problem sets', durationMinutes: 15 },
                { title: 'Solve 3 practice problems without consulting solutions', durationMinutes: 30 },
                { title: 'Review incorrect answers and make flashcards for weak spots', durationMinutes: 20 }
            ];
        } else if (lower.includes('presentation') || lower.includes('slides') || lower.includes('speech') || lower.includes('talk')) {
            rawSuggestions = [
                { title: 'Identify core message and outline 5 key slides', durationMinutes: 20 },
                { title: 'Fill in bullet points and select clear visual diagrams', durationMinutes: 30 },
                { title: 'Do one uninterrupted practice run out loud', durationMinutes: 15 }
            ];
        } else if (lower.includes('email') || lower.includes('message') || lower.includes('contact') || lower.includes('advisor') || lower.includes('prof') || lower.includes('professor')) {
            rawSuggestions = [
                { title: 'Draft concise 3-sentence message stating the question clearly', durationMinutes: 10 },
                { title: 'Attach relevant syllabus/files and review tone', durationMinutes: 5 }
            ];
        } else {
            rawSuggestions = [
                { title: 'Clear workspace and open only the materials needed for this task', durationMinutes: 10 },
                { title: 'Complete first 20 minutes of focused preliminary work', durationMinutes: 20 },
                { title: 'Review progress and finish remaining requirements', durationMinutes: 25 }
            ];
        }

        const existingTitles = new Set((task.subtasks || []).map(s => (s.title || '').trim().toLowerCase()));
        const filtered = rawSuggestions.filter(s => !existingTitles.has(s.title.trim().toLowerCase()));

        if (filtered.length === 0) {
            return [
                { title: 'Review what you have completed so far and verify requirements', durationMinutes: 15 },
                { title: 'Perform final polish and wrap up this task', durationMinutes: 20 }
            ];
        }
        return filtered;
    }

    function toggleAiHelp() {
        if (showAiSuggestions) {
            closeAiHelp();
            return;
        }
        openAiHelp();
    }

    function openAiHelp() {
        const planItem = confirmedPlan && confirmedPlan.plannedTasks ? confirmedPlan.plannedTasks[breakdownIndex] : null;
        if (!planItem) return;
        try {
            currentAiSuggestions = generateAiSuggestionsForTask(planItem.task);
            aiSuggestionError = false;
            showAiSuggestions = true;
        } catch (err) {
            console.error('AI Help generation error:', err);
            aiSuggestionError = true;
            showAiSuggestions = true;
        }
        renderBreakdown();
    }

    function closeAiHelp() {
        showAiSuggestions = false;
        currentAiSuggestions = [];
        aiSuggestionError = false;
        renderBreakdown();
    }

    function acceptAiSuggestion(index) {
        const planItem = confirmedPlan && confirmedPlan.plannedTasks ? confirmedPlan.plannedTasks[breakdownIndex] : null;
        if (!planItem || !currentAiSuggestions[index]) return;
        const sug = currentAiSuggestions[index];

        if (!planItem.task.subtasks) planItem.task.subtasks = [];
        planItem.task.subtasks.push({
            id: 'sub_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
            title: sug.title,
            durationMinutes: sug.durationMinutes || null
        });

        if (planItem.task) {
            dismissedMismatchForTask[planItem.task.id] = false;
        }

        currentAiSuggestions.splice(index, 1);
        if (currentAiSuggestions.length === 0) {
            showAiSuggestions = false;
        }
        renderBreakdown();
        scheduleDraftAutosave();
        if (window.TempoPlanStore && confirmedPlan) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }
    }

    function acceptAllAiSuggestions() {
        const planItem = confirmedPlan && confirmedPlan.plannedTasks ? confirmedPlan.plannedTasks[breakdownIndex] : null;
        if (!planItem || !currentAiSuggestions || currentAiSuggestions.length === 0) return;

        if (!planItem.task.subtasks) planItem.task.subtasks = [];
        currentAiSuggestions.forEach((sug, idx) => {
            planItem.task.subtasks.push({
                id: 'sub_' + Date.now() + '_' + idx,
                title: sug.title,
                durationMinutes: sug.durationMinutes || null
            });
        });

        if (planItem.task) {
            dismissedMismatchForTask[planItem.task.id] = false;
        }

        currentAiSuggestions = [];
        showAiSuggestions = false;
        renderBreakdown();
        scheduleDraftAutosave();
        if (window.TempoPlanStore && confirmedPlan) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }
    }

    function toggleAlreadyKnowWhatToDo(flag) {
        const planItem = confirmedPlan && confirmedPlan.plannedTasks ? confirmedPlan.plannedTasks[breakdownIndex] : null;
        if (!planItem) return;
        planItem.task.alreadyKnowWhatToDo = (flag !== undefined) ? flag : !planItem.task.alreadyKnowWhatToDo;
        renderBreakdown();
        scheduleDraftAutosave();
        if (window.TempoPlanStore && confirmedPlan) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }
    }

    // Kept for backward compatibility with existing tests
    function generateSuggestedSteps() {
        openAiHelp();
    }

    function startCustomBreakdown() {
        const planItem = confirmedPlan && confirmedPlan.plannedTasks ? confirmedPlan.plannedTasks[breakdownIndex] : null;
        if (!planItem) return;
        if (!planItem.task.subtasks) planItem.task.subtasks = [];
        if (planItem.task.subtasks.length === 0) {
            planItem.task.subtasks.push({
                id: 'sub_' + Date.now(),
                title: 'Open notes & review initial requirements',
                durationMinutes: 15
            });
        }
        renderBreakdown();
        scheduleDraftAutosave();
        if (window.TempoPlanStore && confirmedPlan) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }
    }

    function skipBreakdownForCurrentTask() {
        toggleAlreadyKnowWhatToDo(true);
    }

    function addSubtask(optionalTitle, optionalDur) {
        const titleInput = document.getElementById('em-new-step-title');
        const durInput = document.getElementById('em-new-step-duration');

        const title = (optionalTitle && typeof optionalTitle === 'string') 
            ? optionalTitle.trim() 
            : (titleInput ? titleInput.value.trim() : '');
        if (!title) return;

        const dur = (typeof optionalDur === 'number') 
            ? optionalDur 
            : (durInput && durInput.value ? parseInt(durInput.value, 10) || null : null);

        const planItem = confirmedPlan && confirmedPlan.plannedTasks ? confirmedPlan.plannedTasks[breakdownIndex] : null;
        if (!planItem) return;

        if (!planItem.task.subtasks) planItem.task.subtasks = [];
        planItem.task.subtasks.push({
            id: 'sub_' + Date.now(),
            title: title,
            durationMinutes: dur
        });

        if (planItem.task) {
            dismissedMismatchForTask[planItem.task.id] = false;
        }

        renderBreakdown();
        scheduleDraftAutosave();
        if (window.TempoPlanStore && confirmedPlan) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }

        setTimeout(() => {
            const nextInput = document.getElementById('em-new-step-title');
            if (nextInput) nextInput.focus();
        }, 50);
    }

    function removeSubtask(sIdx) {
        const planItem = confirmedPlan && confirmedPlan.plannedTasks ? confirmedPlan.plannedTasks[breakdownIndex] : null;
        if (!planItem) return;
        planItem.task.subtasks.splice(sIdx, 1);
        if (editingSubtaskIndex === sIdx) {
            editingSubtaskIndex = null;
        } else if (editingSubtaskIndex !== null && editingSubtaskIndex > sIdx) {
            editingSubtaskIndex--;
        }
        if (planItem.task) {
            dismissedMismatchForTask[planItem.task.id] = false;
        }
        renderBreakdown();
        scheduleDraftAutosave();
        if (window.TempoPlanStore && confirmedPlan) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }
    }

    // =========================================================================
    // SUBTASK DRAG AND DROP REORDERING
    // =========================================================================
    let draggedSubtaskIndex = null;
    let touchSubtaskStartIdx = null;
    let touchSubtaskLastTargetIdx = null;

    function handleSubtaskDragStart(e, sIdx) {
        draggedSubtaskIndex = sIdx;
        if (e.dataTransfer) {
            e.dataTransfer.setData('text/plain', String(sIdx));
            e.dataTransfer.effectAllowed = 'move';
        }
        const card = e.currentTarget.closest('.em-subtask-item') || e.currentTarget;
        if (card) {
            card.classList.add('opacity-40', 'border-dashed', 'border-[#FF6B2C]');
        }
    }

    function handleSubtaskDragOver(e) {
        e.preventDefault();
        if (e.dataTransfer) {
            e.dataTransfer.dropEffect = 'move';
        }
    }

    function handleSubtaskDragEnter(e) {
        e.preventDefault();
        const card = e.currentTarget.closest('.em-subtask-item');
        if (card) {
            const targetIdx = parseInt(card.getAttribute('data-subtask-index'), 10);
            let fromIdx = draggedSubtaskIndex;
            if (fromIdx !== null && !isNaN(fromIdx) && fromIdx !== targetIdx) {
                card.classList.add('bg-orange-50/60', 'border-[#FF6B2C]');
                if (fromIdx > targetIdx) {
                    card.classList.add('border-t-2', 'border-t-[#FF6B2C]');
                } else {
                    card.classList.add('border-b-2', 'border-b-[#FF6B2C]');
                }
            }
        }
    }

    function handleSubtaskDragLeave(e) {
        const card = e.currentTarget.closest('.em-subtask-item');
        if (card) {
            card.classList.remove('bg-orange-50/60', 'border-[#FF6B2C]', 'border-t-2', 'border-t-[#FF6B2C]', 'border-b-2', 'border-b-[#FF6B2C]');
        }
    }

    function handleSubtaskDrop(e, targetIdx) {
        e.preventDefault();
        e.stopPropagation();
        let fromIdx = draggedSubtaskIndex;
        if (fromIdx === null && e.dataTransfer) {
            const raw = e.dataTransfer.getData('text/plain');
            if (raw) fromIdx = parseInt(raw, 10);
        }
        draggedSubtaskIndex = null;
        clearSubtaskDragStyles();

        if (fromIdx !== null && !isNaN(fromIdx) && fromIdx !== targetIdx) {
            reorderSubtasks(fromIdx, targetIdx);
        }
    }

    function handleSubtaskDragEnd(e) {
        draggedSubtaskIndex = null;
        clearSubtaskDragStyles();
    }

    function clearSubtaskDragStyles() {
        document.querySelectorAll('.em-subtask-item').forEach(el => {
            el.classList.remove(
                'opacity-40',
                'border-dashed',
                'bg-orange-50/60',
                'border-[#FF6B2C]',
                'border-t-2',
                'border-t-[#FF6B2C]',
                'border-b-2',
                'border-b-[#FF6B2C]'
            );
        });
    }

    function handleSubtaskTouchStart(e, sIdx) {
        touchSubtaskStartIdx = sIdx;
        touchSubtaskLastTargetIdx = null;
        const card = e.currentTarget.closest('.em-subtask-item');
        if (card) {
            card.classList.add('opacity-40', 'border-dashed', 'border-[#FF6B2C]');
        }
    }

    function handleSubtaskTouchMove(e) {
        if (touchSubtaskStartIdx === null) return;
        if (e.touches && e.touches.length > 0) {
            if (e.cancelable) e.preventDefault();
            const touch = e.touches[0];
            const el = document.elementFromPoint(touch.clientX, touch.clientY);
            const card = el ? el.closest('.em-subtask-item') : null;

            document.querySelectorAll('.em-subtask-item').forEach(c => {
                const idx = parseInt(c.getAttribute('data-subtask-index'), 10);
                if (idx !== touchSubtaskStartIdx) {
                    c.classList.remove('bg-orange-50/60', 'border-[#FF6B2C]', 'border-t-2', 'border-t-[#FF6B2C]', 'border-b-2', 'border-b-[#FF6B2C]');
                }
            });

            if (card) {
                const targetIdx = parseInt(card.getAttribute('data-subtask-index'), 10);
                if (!isNaN(targetIdx) && targetIdx !== touchSubtaskStartIdx) {
                    touchSubtaskLastTargetIdx = targetIdx;
                    card.classList.add('bg-orange-50/60', 'border-[#FF6B2C]');
                    if (touchSubtaskStartIdx > targetIdx) {
                        card.classList.add('border-t-2', 'border-t-[#FF6B2C]');
                    } else {
                        card.classList.add('border-b-2', 'border-b-[#FF6B2C]');
                    }
                } else {
                    touchSubtaskLastTargetIdx = null;
                }
            }
        }
    }

    function handleSubtaskTouchEnd(e) {
        const fromIdx = touchSubtaskStartIdx;
        const toIdx = touchSubtaskLastTargetIdx;
        touchSubtaskStartIdx = null;
        touchSubtaskLastTargetIdx = null;
        clearSubtaskDragStyles();

        if (fromIdx !== null && toIdx !== null && fromIdx !== toIdx) {
            reorderSubtasks(fromIdx, toIdx);
        }
    }

    function handleSubtaskTouchCancel(e) {
        touchSubtaskStartIdx = null;
        touchSubtaskLastTargetIdx = null;
        clearSubtaskDragStyles();
    }

    function reorderSubtasks(fromIndex, toIndex) {
        const planItem = confirmedPlan && confirmedPlan.plannedTasks ? confirmedPlan.plannedTasks[breakdownIndex] : null;
        if (!planItem || !planItem.task || !planItem.task.subtasks) return;
        if (fromIndex < 0 || fromIndex >= planItem.task.subtasks.length) return;
        if (toIndex < 0 || toIndex >= planItem.task.subtasks.length) return;
        if (fromIndex === toIndex) return;

        const [movedStep] = planItem.task.subtasks.splice(fromIndex, 1);
        planItem.task.subtasks.splice(toIndex, 0, movedStep);

        const sharedTask = tasks.find(t => t.id === planItem.task.id);
        if (sharedTask) {
            sharedTask.subtasks = planItem.task.subtasks;
        }

        editingSubtaskIndex = null;
        renderBreakdown();
        scheduleDraftAutosave();

        if (window.TempoPlanStore) {
            if (typeof window.TempoPlanStore.updateTaskState === 'function') {
                window.TempoPlanStore.updateTaskState(planItem.task.id, {
                    subtasks: planItem.task.subtasks
                });
            }
            if (confirmedPlan) {
                window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
            }
        }
    }

    function moveSubtask(sIdx, dir) {
        reorderSubtasks(sIdx, sIdx + dir);
    }

    function toggleSubtaskDurations() {
        showSubtaskDurations = !showSubtaskDurations;
        renderBreakdown();
    }

    function setSubtaskCompleted(taskId, subtaskId, isCompleted) {
        if (!taskId || !subtaskId) return;
        const targetCompleted = Boolean(isCompleted);
        const sTaskId = String(taskId);
        const sSubtaskId = String(subtaskId);

        if (confirmedPlan && Array.isArray(confirmedPlan.plannedTasks)) {
            const pt = confirmedPlan.plannedTasks.find(p => p.task && String(p.task.id) === sTaskId);
            if (pt && pt.task && Array.isArray(pt.task.subtasks)) {
                const s = pt.task.subtasks.find(sub => String(sub.id) === sSubtaskId);
                if (s) s.completed = targetCompleted;
            }
        }
        if (Array.isArray(tasks)) {
            const t = tasks.find(tsk => String(tsk.id) === sTaskId);
            if (t && Array.isArray(t.subtasks)) {
                const s = t.subtasks.find(sub => String(sub.id) === sSubtaskId);
                if (s) s.completed = targetCompleted;
            }
        }
    }

    function syncTaskDurationFromSteps(totalMinutes) {
        const planItem = confirmedPlan && confirmedPlan.plannedTasks ? confirmedPlan.plannedTasks[breakdownIndex] : null;
        if (!planItem) return;
        planItem.task.durationMinutes = totalMinutes;
        planItem.task.durationLabel = formatDurationMinutes(totalMinutes);
        planItem.task.isUnknownDuration = false;
        planItem.task.isLongTerm = false;
        planHasUserEdits = true;
        recalculateTimelineSlotsPreservingOrder();
        renderBreakdown();
        scheduleDraftAutosave();
        if (window.TempoPlanStore && confirmedPlan) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }
    }

    function keepTaskDurationMismatch() {
        const planItem = confirmedPlan ? confirmedPlan.plannedTasks[breakdownIndex] : null;
        if (planItem && planItem.task) {
            dismissedMismatchForTask[planItem.task.id] = true;
        }
        renderBreakdown();
        scheduleDraftAutosave();
        if (window.TempoPlanStore && confirmedPlan) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }
    }

    function breakdownNextTask() {
        goToStage(confirmedPlan ? 'handoff' : 'plan-review');
    }

    function breakdownPreviousTask() {
        goToStage('plan-review');
    }

    /**
     * Determines the next task to work on in Focus Zone according to priority:
     * 1. In-progress task (if one already exists)
     * 2. First unfinished task in the Emergency Plan's saved execution order
     * 3. null if all tasks in the Emergency Plan are completed
     */
    function getNextFocusTask() {
        if (!confirmedPlan || !Array.isArray(confirmedPlan.plannedTasks) || confirmedPlan.plannedTasks.length === 0) {
            return null;
        }

        const isTaskDone = (t) => {
            if (!t) return false;
            return !!(t.completed || t.execution_status === 'completed' || t.status === 'completed');
        };

        const isTaskInProgress = (t) => {
            if (!t || isTaskDone(t)) return false;
            return !!(t.isInProgress || t.inProgress || t.execution_status === 'in_progress' || t.status === 'in_progress');
        };

        // 1. In-progress task
        for (const item of confirmedPlan.plannedTasks) {
            const task = item.task || item;
            if (isTaskInProgress(task)) {
                return { planItem: item, task: task };
            }
        }

        // 2. First unfinished task in execution order
        for (const item of confirmedPlan.plannedTasks) {
            const task = item.task || item;
            if (!isTaskDone(task)) {
                return { planItem: item, task: task };
            }
        }

        // 3. All tasks completed
        return null;
    }

    /**
     * Launches Focus Zone for a specific task or the prioritized next task.
     * Preserves mode and uses shared task ID.
     */
    function launchFocusZone(taskId) {
        let targetTask = null;
        if (taskId) {
            const item = confirmedPlan && confirmedPlan.plannedTasks 
                ? confirmedPlan.plannedTasks.find(pt => (pt.task && pt.task.id === taskId) || pt.id === taskId) 
                : null;
            if (item) {
                targetTask = item.task || item;
            }
        }
        if (!targetTask) {
            const nextFocus = getNextFocusTask();
            targetTask = nextFocus ? nextFocus.task : null;
        }

        if (!targetTask) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Tất cả công việc trong Kế hoạch Khẩn cấp đã hoàn thành! Bạn làm rất tốt.");
            }
            return;
        }

        if (window.TempoFocusZone && typeof window.TempoFocusZone.open === 'function') {
            window.TempoFocusZone.open({ taskId: targetTask.id });
        } else {
            console.warn("[TempoEmergencyFlow] TempoFocusZone is not available.");
        }
    }

    /**
     * Secondary choice 1: View / Edit Emergency Plan
     * Opens the review screen without resetting setup or clearing the plan.
     */
    function viewPlan() {
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.open === 'function') {
            window.TempoPlanWorkspace.open();
        } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('plan-workspace');
        } else {
            window.location.hash = '#plan-workspace';
        }
    }

    /**
     * Secondary choice 2: Return to Home Dashboard
     * Navigates to main dashboard in Emergency Mode with active plan preserved.
     */
    function returnHome() {
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('today');
        } else {
            window.location.hash = '#today';
        }
    }

    /**
     * Save Plan: The action that COMPLETES the Emergency Plan setup.
     * Durably persists the plan via TempoPlanStore, clears draft, and transitions to completion screen.
     */
    async function savePlan() {
        if (!confirmedPlan || !confirmedPlan.plannedTasks || confirmedPlan.plannedTasks.length === 0) {
            console.warn("[TempoEmergencyFlow] No confirmed plan to save.");
            goToStage('reality-check');
            return;
        }

        const saveBtn = document.getElementById('btn-em-use-plan') || document.getElementById('btn-em-save-plan');
        let origBtnText = '';
        if (saveBtn) {
            origBtnText = saveBtn.innerHTML;
            saveBtn.disabled = true;
            saveBtn.innerHTML = `
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                <span>Saving plan...</span>
            `;
        }

        try {
            if (!Array.isArray(confirmedPlan.tasks)) {
                confirmedPlan.tasks = confirmedPlan.plannedTasks ? confirmedPlan.plannedTasks.map(pt => pt.task).filter(Boolean) : [];
            }
            if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
                await window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
                if (typeof window.TempoPlanStore.clearDraft === 'function') {
                    window.TempoPlanStore.clearDraft('emergency');
                }
            } else {
                localStorage.setItem('tempo_active_emergency_plan', JSON.stringify(confirmedPlan));
                localStorage.removeItem('tempo_emergency_draft');
            }

            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = origBtnText;
            }

            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Đã lưu Kế hoạch Làm việc thành công.");
            }

            if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.showTaskForNowPopupAfterSave === 'function') {
                window.TempoUrmodeFlow.showTaskForNowPopupAfterSave(confirmedPlan);
            } else {
                goToStage('handoff');
            }
        } catch (err) {
            console.error("[TempoEmergencyFlow] Failed to save active plan:", err);
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = origBtnText;
            }
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("We couldn't save your plan yet. Your work is still here — try saving again.", 5000);
            }
        }
    }

    /**
     * Backward-compatible entrypoint: If taskId passed, launches focus; else saves plan.
     */
    function startWorking(taskId) {
        if (taskId) {
            launchFocusZone(taskId);
        } else {
            savePlan();
        }
    }

    // =========================================================================
    // STAGE 9: START WORKING HANDOFF (Completion Screen / Choice Point)
    // =========================================================================
    function renderHandoff() {
        const container = document.getElementById('emergency-stage-handoff');
        if (!container || !confirmedPlan || !confirmedPlan.plannedTasks) return;

        const nextFocus = getNextFocusTask();
        const focusItem = nextFocus ? nextFocus.planItem : null;
        const focusTask = nextFocus ? nextFocus.task : null;

        // Upcoming queue contains all tasks EXCEPT the currently focused one
        const upcomingTasks = confirmedPlan.plannedTasks.filter(item => {
            const t = item.task || item;
            return !focusTask || t.id !== focusTask.id;
        });

        // Determine first immediate action
        let firstImmediateAction = 'Begin first 25-minute focused work block.';
        if (focusTask && Array.isArray(focusTask.subtasks) && focusTask.subtasks.length > 0) {
            const unfinishedSubtask = focusTask.subtasks.find(s => !s.completed);
            firstImmediateAction = unfinishedSubtask ? unfinishedSubtask.title : focusTask.subtasks[0].title;
        }

        container.innerHTML = `
            <div class="max-w-2xl mx-auto py-8 sm:py-10 space-y-6">
                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#4A6B5D]">${isViLocale() ? 'WORKING PLAN ĐÃ SẴN SÀNG' : 'WORKING PLAN READY'}</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        Your plan is saved.
                    </h2>
                    <p class="text-xs sm:text-sm text-[#6F6B68] max-w-md mx-auto leading-relaxed">
                        You've turned everything into a clear, doable plan. You're in control—choose what you'd like to do next.
                    </p>
                </div>

                <!-- Active Focus Card OR All-Completed Celebration Card -->
                ${focusTask ? `
                    <div class="bg-white border-2 border-[#FF6B2C] rounded-[22px] p-6 space-y-4 shadow-sm">
                        <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                            <span class="px-3 py-1 rounded-full text-xs font-extrabold ${focusTask.isInProgress ? 'bg-amber-100 text-amber-800' : 'bg-[#FFE9DC] text-[#B83D08]'} uppercase tracking-wider">
                                ${focusTask.isInProgress ? '⚡ In Progress' : '✨ Current Focus'}
                            </span>
                            ${focusItem && focusItem.startTime && focusItem.endTime ? `
                                <span class="text-xs font-bold text-[#FF6B2C]">Scheduled: ${focusItem.startTime} – ${focusItem.endTime}</span>
                            ` : `
                                <span class="text-xs font-bold text-[#6F6B68]">Planned execution queue</span>
                            `}
                        </div>

                        <div class="space-y-1">
                            <h3 class="font-heading text-xl font-bold text-[#202124]">${escapeHTML(focusTask.name)}</h3>
                            <p class="text-xs text-[#6F6B68]">
                                Estimated duration: ~${focusTask.durationLabel || 'Flexible'} • Deadline: ${focusTask.hasDeadline ? formatHumanDeadline(focusTask.deadlineDate, focusTask.deadlineTime, isViLocale()) : (isViLocale() ? 'Chưa có deadline' : 'No fixed deadline')}
                            </p>
                        </div>

                        <!-- First Immediate Action -->
                        <div class="p-4 bg-[#FFF8F2] border border-[#FFD2BA] rounded-xl space-y-1">
                            <span class="text-[11px] font-bold uppercase tracking-wider text-[#B83D08]">Your Next Action:</span>
                            <p class="text-xs font-semibold text-[#202124]">${escapeHTML(firstImmediateAction)}</p>
                        </div>
                    </div>
                ` : `
                    <div class="bg-white border-2 border-emerald-500 rounded-[22px] p-6 text-center space-y-3 shadow-sm">
                        <div class="w-12 h-12 mx-auto rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 text-2xl font-bold">
                            ✓
                        </div>
                        <h3 class="font-heading text-xl font-bold text-[#202124]">All planned tasks completed!</h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] max-w-md mx-auto">
                            You've completed every task in this Working Plan. Take a moment to acknowledge your hard work.
                        </p>
                    </div>
                `}

                <!-- Upcoming Planned Queue -->
                ${upcomingTasks.length > 0 ? `
                    <div class="bg-white border border-[#EAE4DF] rounded-[22px] p-5 space-y-3 shadow-sm">
                        <h4 class="text-xs font-bold uppercase tracking-wider text-[#6F6B68]">Up Next in Your Plan</h4>
                        <div class="space-y-2">
                            ${upcomingTasks.map(item => {
                                const t = item.task || item;
                                const isDone = !!(t.completed || t.execution_status === 'completed');
                                return `
                                    <div class="p-3 bg-[#FFFDFB] border border-[#EAE4DF] rounded-xl flex items-center justify-between text-xs ${isDone ? 'opacity-60 bg-stone-50' : ''}">
                                        <div class="space-y-0.5">
                                            <h5 class="font-bold text-[#202124] ${isDone ? 'line-through text-gray-500' : ''}">${escapeHTML(t.name)}</h5>
                                            <p class="text-[11px] text-[#6F6B68]">
                                                ${item.startTime && item.endTime ? `${item.startTime} – ${item.endTime} • ` : ''}~${t.durationLabel || 'Flexible'}
                                            </p>
                                        </div>
                                        <span class="px-2 py-0.5 rounded text-[10px] font-bold ${isDone ? 'bg-emerald-100 text-emerald-800' : (item.executionBadge === 'THEN' ? 'bg-[#FBF0E4] text-[#9A5B13]' : 'bg-[#F3F1EF] text-[#6F6B68]')}">
                                            ${isDone ? 'COMPLETED' : (item.executionBadge || 'UP NEXT')}
                                        </span>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Supportive Guidance Notice -->
                <div class="p-4 bg-stone-50 border border-[#EAE4DF] rounded-2xl text-center space-y-1.5 text-xs text-[#6F6B68]">
                    <p class="font-semibold text-[#202124]">
                        You can adjust your plan or switch between tasks anytime.
                    </p>
                    <p>When you're ready, jump into Focus Zone for timed work blocks with restful breaks.</p>
                </div>

                <!-- Navigation Controls (3 Explicit Choices) -->
                <div class="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
                    ${focusTask ? `
                        <button id="btn-em-start-focus" onclick="window.TempoEmergencyFlow.launchFocusZone()" 
                                class="btn-primary w-full sm:w-auto px-7 py-3.5 rounded-xl font-bold text-xs sm:text-sm shadow-md transition order-1 sm:order-2">
                            Start working now with Tempo Focus Zone →
                        </button>
                    ` : `
                        <button disabled class="w-full sm:w-auto px-7 py-3.5 rounded-xl font-semibold text-xs sm:text-sm bg-gray-100 text-gray-400 cursor-not-allowed border border-gray-200 order-1 sm:order-2">
                            All tasks completed
                        </button>
                    `}
                    <button id="btn-em-view-edit-plan" onclick="window.TempoEmergencyFlow.viewPlan()" 
                            class="w-full sm:w-auto px-5 py-3.5 rounded-xl border border-gray-200 text-xs font-semibold text-[#202124] hover:bg-stone-50 transition order-2 sm:order-1">
                        ${isVi ? 'Xem / Sửa Working Plan' : 'View / Edit Working Plan'}
                    </button>
                    <button id="btn-em-return-home" onclick="window.TempoEmergencyFlow.returnHome()" 
                            class="w-full sm:w-auto px-5 py-3.5 text-xs font-semibold text-[#6F6B68] hover:text-[#202124] hover:bg-stone-100/60 rounded-xl transition order-3">
                        Return to Home Dashboard →
                    </button>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // UTILITY & HELPER FUNCTIONS
    // =========================================================================
    function parseTimeToMinutes(timeStr) {
        if (!timeStr) return 0;
        const [h, m] = timeStr.split(':').map(Number);
        return (h * 60) + (m || 0);
    }

    function formatMinutesToTimeString(totalMinutes) {
        const hours = Math.floor(totalMinutes / 60) % 24;
        const mins = totalMinutes % 60;
        const period = hours >= 12 ? 'PM' : 'AM';
        const displayHours = hours % 12 === 0 ? 12 : hours % 12;
        return `${displayHours}:${String(mins).padStart(2, '0')} ${period}`;
    }

    function computeTimeDifferenceMinutes(startStr, endStr) {
        const start = parseTimeToMinutes(startStr);
        const end = parseTimeToMinutes(endStr);
        return end >= start ? (end - start) : (1440 - start + end);
    }

    function formatDurationMinutes(mins, isVi = false) {
        if (!mins || mins <= 0) return isVi ? '0 phút' : '0m';
        if (mins < 60) return isVi ? `${mins} phút` : `${mins}m`;
        const h = Math.floor(mins / 60);
        const m = mins % 60;
        if (isVi) {
            return m > 0 ? `${h} giờ ${m} phút` : `${h} giờ`;
        }
        return m > 0 ? `${h}h ${m}m` : `${h}h`;
    }

    function formatMinutesToHHMM(mins) {
        const h = Math.floor(mins / 60) % 24;
        const m = mins % 60;
        return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
    }

    function formatTime12Hour(timeStr) {
        if (!timeStr) return '';
        if (timeStr.toLowerCase().includes('am') || timeStr.toLowerCase().includes('pm')) return timeStr;
        const parts = timeStr.split(':');
        if (parts.length < 2) return timeStr;
        let h = parseInt(parts[0], 10);
        const m = parts[1];
        if (isNaN(h)) return timeStr;
        const ampm = h >= 12 ? 'PM' : 'AM';
        h = h % 12;
        if (h === 0) h = 12;
        return `${h}:${m} ${ampm}`;
    }

    function formatHumanDeadline(dateStr, timeStr, isVi = isViLocale()) {
        if (!dateStr) return isVi ? 'Chưa có deadline' : 'No fixed deadline';
        try {
            const [y, m, d] = dateStr.split('-').map(Number);
            const date = new Date(y, m - 1, d);
            const monthDay = isVi
                ? `${d} thg ${m}`
                : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            if (timeStr) {
                return `${monthDay} · ${formatTime12Hour(timeStr)}`;
            }
            return monthDay;
        } catch (e) {
            return `${dateStr}${timeStr ? ' · ' + timeStr : ''}`;
        }
    }

    function calculateRelativeDueText(dateStr, timeStr, isVi = isViLocale()) {
        if (!dateStr) return isVi ? 'Chưa có deadline' : 'No fixed deadline';
        try {
            const target = new Date(`${dateStr}T${timeStr || '23:59'}`);
            const now = new Date();
            const diffMs = target - now;
            const diffHours = Math.round(diffMs / (1000 * 60 * 60));

            if (diffHours < 0) return isVi ? 'Đã quá Deadline' : 'Deadline passed';
            if (diffHours <= 12) {
                return isVi
                    ? `Deadline trong ${diffHours} giờ tới`
                    : `Due in ${diffHours} hour${diffHours === 1 ? '' : 's'}`;
            }
            if (diffHours <= 24) {
                return isVi
                    ? `Deadline tối nay / sáng mai`
                    : `Due tonight / tomorrow morning`;
            }
            const diffDays = Math.ceil(diffHours / 24);
            if (diffDays === 1) {
                return isVi ? `Deadline ngày mai` : `Due tomorrow`;
            }
            return isVi ? `Deadline trong ${diffDays} ngày tới` : `Due in ${diffDays} days`;
        } catch (e) {
            return isVi ? `Deadline ${dateStr}` : `Due ${dateStr}`;
        }
    }

    function isDueSoon(dateStr) {
        if (!dateStr) return false;
        try {
            const target = new Date(dateStr);
            const now = new Date();
            const diffDays = (target - now) / (1000 * 60 * 60 * 24);
            return diffDays <= 1.5;
        } catch (e) {
            return false;
        }
    }

    function escapeHTML(str) {
        if (!str) return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function getCurrentStage() {
        return currentStage;
    }

    function getTasks() {
        return tasks;
    }

    function getConfirmedPlan() {
        if (confirmedPlan) {
            const currentUid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') 
                ? window.TempoAuth.getCurrentUserId() : null;
            if (currentUid) {
                if (confirmedPlan.userId && confirmedPlan.userId !== currentUid) return null;
                if (confirmedPlan.user_id && confirmedPlan.user_id !== currentUid) return null;
                if (!confirmedPlan.userId && !confirmedPlan.user_id) return null;
            }
            if (!Array.isArray(confirmedPlan.availabilityDays) || confirmedPlan.availabilityDays.length === 0) {
                confirmedPlan.availabilityDays = availabilityDays;
            }
        }
        return confirmedPlan;
    }

    function getAvailabilityDays() {
        if (!Array.isArray(availabilityDays) || availabilityDays.length === 0) {
            try {
                const storedAvail = localStorage.getItem('tempo_availability_days');
                if (storedAvail) {
                    const parsed = JSON.parse(storedAvail);
                    if (Array.isArray(parsed) && parsed.length > 0) {
                        availabilityDays = parsed;
                    }
                }
            } catch(e) {}
        }
        return availabilityDays;
    }

    function setAvailabilityDays(days) {
        if (Array.isArray(days)) {
            availabilityDays = days;
            if (confirmedPlan) {
                confirmedPlan.availabilityDays = days;
            }
            try {
                localStorage.setItem('tempo_availability_days', JSON.stringify(days));
            } catch(e) {}
        }
    }

    function setConfirmedPlan(plan) {
        if (plan) {
            const currentUid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') 
                ? window.TempoAuth.getCurrentUserId() : null;
            if (currentUid && !plan.userId) {
                plan.userId = currentUid;
                plan.user_id = currentUid;
            }
        }
        confirmedPlan = plan;
        if (plan && Array.isArray(plan.plannedTasks)) {
            tasks = plan.plannedTasks.map(pt => pt.task).filter(Boolean);
        } else if (plan && Array.isArray(plan.tasks)) {
            tasks = [...plan.tasks];
        }
        if (plan && Array.isArray(plan.availabilityDays)) {
            availabilityDays = plan.availabilityDays;
            try {
                localStorage.setItem('tempo_availability_days', JSON.stringify(availabilityDays));
            } catch(e) {}
        }
    }

    function isTaskCompleted(taskId) {
        const sTaskId = String(taskId);
        let task = tasks.find(t => String(t.id) === sTaskId);
        if (!task && confirmedPlan) {
            if (confirmedPlan.plannedTasks) {
                const item = confirmedPlan.plannedTasks.find(pt => pt.task && String(pt.task.id) === sTaskId);
                if (item) task = item.task;
            }
            if (!task && confirmedPlan.unarrangedTasks) {
                const item = confirmedPlan.unarrangedTasks.find(t => String(t && t.task ? t.task.id : t.id) === sTaskId);
                if (item) task = item.task || item;
            }
            if (!task && confirmedPlan.unallocatedTasks) {
                const item = confirmedPlan.unallocatedTasks.find(t => String(t && t.task ? t.task.id : t.id) === sTaskId);
                if (item) task = item.task || item;
            }
            if (!task && confirmedPlan.tasks) {
                task = confirmedPlan.tasks.find(t => t && String(t.id) === sTaskId);
            }
        }
        if (!task && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            const storePlan = window.TempoPlanStore.getActivePlan('emergency');
            if (storePlan) {
                if (storePlan.plannedTasks) {
                    const item = storePlan.plannedTasks.find(pt => pt.task && String(pt.task.id) === sTaskId);
                    if (item) task = item.task;
                }
                if (!task && storePlan.unarrangedTasks) {
                    const item = storePlan.unarrangedTasks.find(t => String(t && t.task ? t.task.id : t.id) === sTaskId);
                    if (item) task = item.task || item;
                }
                if (!task && storePlan.unallocatedTasks) {
                    const item = storePlan.unallocatedTasks.find(t => String(t && t.task ? t.task.id : t.id) === sTaskId);
                    if (item) task = item.task || item;
                }
                if (!task && storePlan.tasks) {
                    task = storePlan.tasks.find(t => t && String(t.id) === sTaskId);
                }
            }
        }
        return !!(task && task.completed === true);
    }

    function setTaskCompleted(taskId, completed = true) {
        const sTaskId = String(taskId);
        let task = tasks.find(t => String(t.id) === sTaskId);
        if (!task && confirmedPlan) {
            if (confirmedPlan.plannedTasks) {
                const item = confirmedPlan.plannedTasks.find(pt => pt.task && String(pt.task.id) === sTaskId);
                if (item) task = item.task;
            }
            if (!task && confirmedPlan.unarrangedTasks) {
                const item = confirmedPlan.unarrangedTasks.find(t => String(t && t.task ? t.task.id : t.id) === sTaskId);
                if (item) task = item.task || item;
            }
            if (!task && confirmedPlan.unallocatedTasks) {
                const item = confirmedPlan.unallocatedTasks.find(t => String(t && t.task ? t.task.id : t.id) === sTaskId);
                if (item) task = item.task || item;
            }
            if (!task && confirmedPlan.tasks) {
                task = confirmedPlan.tasks.find(t => t && String(t.id) === sTaskId);
            }
        }
        if (!task && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            const storePlan = window.TempoPlanStore.getActivePlan('emergency');
            if (storePlan) {
                if (storePlan.plannedTasks) {
                    const item = storePlan.plannedTasks.find(pt => pt.task && String(pt.task.id) === sTaskId);
                    if (item) task = item.task;
                }
                if (!task && storePlan.unarrangedTasks) {
                    const item = storePlan.unarrangedTasks.find(t => String(t && t.task ? t.task.id : t.id) === sTaskId);
                    if (item) task = item.task || item;
                }
                if (!task && storePlan.unallocatedTasks) {
                    const item = storePlan.unallocatedTasks.find(t => String(t && t.task ? t.task.id : t.id) === sTaskId);
                    if (item) task = item.task || item;
                }
                if (!task && storePlan.tasks) {
                    task = storePlan.tasks.find(t => t && String(t.id) === sTaskId);
                }
                if (task && !confirmedPlan) confirmedPlan = storePlan;
            }
        }
        if (task) {
            task.completed = !!completed;
            if (task.completed) {
                task.isInProgress = false;
            }
            if (window.TempoPlanStore && typeof window.TempoPlanStore.updateTaskState === 'function') {
                window.TempoPlanStore.updateTaskState(taskId, {
                    completed: task.completed,
                    isInProgress: task.isInProgress
                });
            }
            scheduleDraftAutosave(true);
            return task.completed;
        }
        return false;
    }

    function toggleTaskCompleted(taskId) {
        const current = isTaskCompleted(taskId);
        return setTaskCompleted(taskId, !current);
    }

    function setTaskInProgress(taskId, inProgress = true) {
        let task = tasks.find(t => t.id === taskId);
        if (!task && confirmedPlan && confirmedPlan.plannedTasks) {
            const item = confirmedPlan.plannedTasks.find(pt => pt.task && pt.task.id === taskId);
            if (item) task = item.task;
        }
        if (!task && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            const storePlan = window.TempoPlanStore.getActivePlan('emergency');
            if (storePlan && storePlan.plannedTasks) {
                const item = storePlan.plannedTasks.find(pt => pt.task && pt.task.id === taskId);
                if (item) {
                    task = item.task;
                    if (!confirmedPlan) confirmedPlan = storePlan;
                }
            }
        }
        if (task) {
            task.isInProgress = inProgress;
            if (window.TempoPlanStore) {
                window.TempoPlanStore.updateTaskState(taskId, {
                    isInProgress: task.isInProgress
                });
            }
            scheduleDraftAutosave(true);
        }
    }

    return {
        init,
        goToStage,
        getCurrentStage,
        getTasks,
        getConfirmedPlan,
        setConfirmedPlan,
        setAvailabilityDays,
        getAvailabilityDays,
        toggleTaskCompleted,
        setTaskCompleted,
        isTaskCompleted,
        setTaskInProgress,
        // Active Plan / Draft Safeguards
        promptStartFresh,
        startFreshPlan,
        resumeDraft,
        // Entry / Settle
        startSettle,
        skipSettle,
        // Reality Check
        addRealityCheckTask,
        removeRealityCheckTask,
        editRealityCheckTask,
        cancelRealityCheckTaskEdit,
        toggleRcEditNoDeadline,
        saveRealityCheckTaskEdit,
        loadSampleTasks,
        toggleNoDeadline,
        continueFromRealityCheck,
        // Assessment
        setAssessmentOption,
        toggleAssessmentFlexibility,
        setAssessmentDuration,
        handleCustomDurationChange,
        handleCustomHoursChange: (val) => handleCustomDurationChange(val, 'hours'),
        saveAssessmentAndNext,
        previousAssessmentTask,
        // Priority Review
        reassignTaskCategory,
        // Available Time
        updateBlockTime,
        addTimeBlock,
        removeTimeBlock,
        toggleDayUnavailable,
        restoreAllAvailability,
        shortcutFreeRestOfToday,
        shortcutCopyTodayToTomorrow,
        startAddDay,
        cancelAddDay,
        confirmAddDay,
        openRemoveDayModal,
        closeRemoveDayModal,
        confirmRemoveDay,
        removeDay,
        continueFromAvailableTime,
        // Plan Review Drag & Drop & Scheduling
        buildDeterministicPlan,
        getNormalizedWindowsForDay,
        calculateTaskWorkRhythm,
        recalculateTimelineSlotsPreservingOrder,
        renderPlanReview,
        handleDragStart,
        handleDragOver,
        handleDragEnter,
        handleDragLeave,
        handleDrop,
        handleDropOnDay,
        handleDragEnd,
        clearTaskDragStyles,
        isDraggingTask: () => isDraggingTask,
        reorderPlannedTasks,
        moveTaskToDay,
        openScheduleModal,
        openScheduleModalForUnarranged,
        openScheduleModalFromUnarranged: openScheduleModalForUnarranged,
        closeScheduleModal,
        selectScheduleWindow,
        toggleModalAddTime,
        cancelModalAddTime,
        saveModalAddedTime,
        scheduleTaskAsUnarranged,
        executeScheduleTask,
        getScheduleModalState: () => scheduleModalState,
        navigateBackFromPlan,
        confirmPlanEditWarningAndGoBack,
        cancelPlanEditWarning,
        openMoveTaskModal,
        closeMoveTaskModal,
        updateMoveModalPreview,
        executeMoveTask,
        movePlanTask,
        ignoreDeadlineWarning,
        openEditEstimateModal,
        closeEditEstimateModal,
        toggleEditEstimateNotSure,
        saveEditEstimate,
        promptEditPlanDuration,
        openDeadlineModal,
        closeDeadlineModal,
        toggleDeadlineModalNoDeadline,
        saveDeadlineModal,
        confirmPlanAndProceed,
        reviewStepBreakdown,
        // Breakdown
        generateSuggestedSteps,
        startCustomBreakdown,
        skipBreakdownForCurrentTask,
        addSubtask,
        removeSubtask,
        setSubtaskCompleted,
        moveSubtask,
        reorderSubtasks,
        handleSubtaskDragStart,
        handleSubtaskDragOver,
        handleSubtaskDragEnter,
        handleSubtaskDragLeave,
        handleSubtaskDrop,
        handleSubtaskDragEnd,
        handleSubtaskTouchStart,
        handleSubtaskTouchMove,
        handleSubtaskTouchEnd,
        handleSubtaskTouchCancel,
        toggleSubtaskDurations,
        syncTaskDurationFromSteps,
        keepTaskDurationMismatch,
        breakdownNextTask,
        breakdownPreviousTask,
        toggleAiHelp,
        openAiHelp,
        closeAiHelp,
        acceptAiSuggestion,
        acceptAllAiSuggestions,
        toggleAlreadyKnowWhatToDo,
        startWorking,
        savePlan,
        launchFocusZone,
        viewPlan,
        returnHome,
        getNextFocusTask,
        openSubtaskDurationEditor,
        closeSubtaskDurationEditor,
        saveSubtaskDuration,
        clearSubtaskDuration,
        restorePlanState,
        resetFlowState,
        onLanguageChange
    };
})();
