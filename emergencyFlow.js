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
        'breakdown',
        'handoff'
    ];

    // Core Flow State Model (Prototype in-memory state)
    let tasks = [];
    let assessmentIndex = 0;
    let availabilityDays = [];
    let confirmedPlan = null;
    let breakdownIndex = 0;
    let showSubtaskDurations = true;
    let ignoredDeadlineWarnings = new Set();
    let moveModalState = null;
    let removeDayModalState = null;
    let editEstimateModalState = null;
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
            'breakdown': 'Step Breakdown',
            'handoff': 'Plan Ready'
        };
        return names[stage] || 'Setup';
    }

    async function init() {
        bindEvents();
        initDefaultAvailability();

        // Restore active plan or draft from TempoPlanStore
        if (window.TempoPlanStore) {
            try {
                // 1. Check for active confirmed plan (check synchronous cache first for zero latency)
                let activePlan = typeof window.TempoPlanStore.getActivePlan === 'function' 
                    ? window.TempoPlanStore.getActivePlan('emergency') 
                    : null;
                if (!activePlan) {
                    activePlan = await window.TempoPlanStore.loadActivePlan('emergency');
                }

                if (activePlan && Array.isArray(activePlan.plannedTasks) && activePlan.plannedTasks.length > 0) {
                    confirmedPlan = activePlan;
                    const allTasksMap = new Map();
                    activePlan.plannedTasks.forEach(item => {
                        if (item && item.task) allTasksMap.set(item.task.id, item.task);
                    });
                    if (Array.isArray(activePlan.unallocatedTasks)) {
                        activePlan.unallocatedTasks.forEach(task => {
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
                    console.log("[TempoEmergencyFlow] Restored active plan from storage with", tasks.length, "tasks. Stage:", currentStage);

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
                        if (draft.currentStage && STAGES.includes(draft.currentStage)) {
                            currentStage = draft.currentStage;
                        }
                        console.log("[TempoEmergencyFlow] Restored draft setup at stage:", currentStage);
                    }
                }
            } catch (err) {
                console.warn("[TempoEmergencyFlow] Storage restoration notice:", err);
            }
        }

        // If the emergency screen is currently active in DOM, render the restored stage
        const screen = document.getElementById('screen-emergency');
        if (screen && !screen.classList.contains('hidden')) {
            goToStage(currentStage);
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
                        <span class="px-3 py-1 rounded-full text-xs font-extrabold bg-[#FFE9DC] text-[#B83D08] uppercase tracking-wider">
                            Active Emergency Plan
                        </span>
                        <span class="text-xs font-bold text-[#6F6B68]">${confirmedPlan.plannedTasks.length} task${confirmedPlan.plannedTasks.length === 1 ? '' : 's'} scheduled</span>
                    </div>
                    <div class="space-y-1">
                        <h4 class="font-heading text-lg font-bold text-[#202124]">You have an active Emergency Plan</h4>
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
                        <h4 class="font-heading text-lg font-bold text-[#202124]">Pick up where you left off?</h4>
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
                if (removeDayModalState) {
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

        // Show target stage container
        const targetEl = document.getElementById(`emergency-stage-${stageName}`);
        if (targetEl) {
            targetEl.classList.remove('hidden');
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
        const phases = {
            'reset': ['entry'],
            'organize': ['reality-check', 'prioritize', 'priority-review'],
            'plan': ['available-time', 'feasibility', 'generating', 'plan-review'],
            'ready': ['breakdown', 'handoff']
        };

        const activePhaseKey = Object.keys(phases).find(key => phases[key].includes(stage)) || 'reset';

        ['reset', 'organize', 'plan', 'ready'].forEach(key => {
            const pill = document.getElementById(`em-phase-${key}`);
            if (!pill) return;
            if (key === activePhaseKey) {
                pill.className = 'px-3 py-1 rounded-full bg-[#FFE9DC] text-[#B83D08] font-bold text-[11px] uppercase tracking-wider transition-colors';
            } else {
                pill.className = 'px-3 py-1 rounded-full text-[#8E8A85] font-semibold text-[11px] uppercase tracking-wider transition-colors';
            }
        });
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
            case 'breakdown':
                renderBreakdown();
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

        // Default deadline: tomorrow at 21:00
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const defaultDateStr = tomorrow.toISOString().split('T')[0];

        container.innerHTML = `
            <div class="max-w-2xl mx-auto py-8 sm:py-10 space-y-6">
                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">EMERGENCY MODE</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        Reality Check
                    </h2>
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">
                        Get everything out of your head.
                    </h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68] max-w-md mx-auto leading-relaxed">
                        Add what you need to get done. We'll organize it next.
                    </p>
                </div>

                <!-- Input Card -->
                <div class="bg-white border border-[#EAE4DF] rounded-[22px] p-5 sm:p-6 space-y-4 shadow-sm">
                    <div class="space-y-1.5">
                        <label for="rc-task-name" class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                            What do you need to get done?
                        </label>
                        <input id="rc-task-name" type="text" placeholder="e.g. Marketing Report, Statistics Lab, Chapter 4 Reading..."
                               class="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#FF6B2C] bg-[#FFFDFB]">
                    </div>

                    <!-- Deadline Inputs -->
                    <div class="space-y-2">
                        <label class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                            Deadline
                        </label>
                        <div class="flex flex-wrap items-center gap-3">
                            <input id="rc-deadline-date" type="date" value="${defaultDateStr}"
                                   class="px-3.5 py-2 text-xs border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-[#FF6B2C] bg-white">
                            <input id="rc-deadline-time" type="time" value="21:00"
                                   class="px-3.5 py-2 text-xs border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-[#FF6B2C] bg-white">
                            <label class="flex items-center space-x-2 text-xs text-[#6F6B68] cursor-pointer pl-1">
                                <input id="rc-no-deadline-cb" type="checkbox" onchange="window.TempoEmergencyFlow.toggleNoDeadline(this.checked)"
                                       class="rounded text-[#FF6B2C] focus:ring-[#FF6B2C]">
                                <span>No fixed deadline</span>
                            </label>
                        </div>
                    </div>

                    <!-- Add Button & Sample Shortcut -->
                    <div class="pt-2 flex items-center justify-between">
                        <button onclick="window.TempoEmergencyFlow.addRealityCheckTask()" 
                                class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs shadow-sm flex items-center space-x-1.5 transition">
                            <span>+ Add task</span>
                        </button>
                        <button onclick="window.TempoEmergencyFlow.loadSampleTasks()" class="text-xs text-[#FF6B2C] hover:underline font-medium">
                            + Load 3 sample tasks
                        </button>
                    </div>
                </div>

                <!-- Added Tasks List -->
                <div class="space-y-3">
                    <div class="flex items-center justify-between px-1">
                        <h4 class="text-xs font-bold uppercase tracking-wider text-[#6F6B68]">
                            Added Tasks (<span id="rc-task-count">${tasks.length}</span>)
                        </h4>
                    </div>

                    <div id="rc-tasks-list" class="space-y-2.5">
                        ${renderTaskListHTML()}
                    </div>
                </div>

                <!-- Primary CTA -->
                <div class="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-[#EAE4DF]">
                    <button onclick="window.TempoEmergencyFlow.goToStage('entry')" 
                            class="text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition">
                        ← Back to Reset
                    </button>
                    <button id="btn-rc-continue" onclick="window.TempoEmergencyFlow.continueFromRealityCheck()"
                            ${tasks.length === 0 ? 'disabled' : ''}
                            class="${tasks.length === 0 ? 'opacity-50 cursor-not-allowed bg-stone-300 text-stone-500' : 'btn-primary'} px-7 py-3.5 rounded-xl font-bold text-sm shadow-sm flex items-center space-x-2 transition">
                        <span>I've added everything</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    function renderTaskListHTML() {
        if (tasks.length === 0) {
            return `
                <div class="p-6 bg-white/70 border border-dashed border-[#EAE4DF] rounded-2xl text-center text-xs text-[#6F6B68]">
                    No tasks added yet. Enter your tasks above to get them out of your head.
                </div>
            `;
        }

        return tasks.map(t => {
            const deadlineText = t.hasDeadline 
                ? formatHumanDeadline(t.deadlineDate, t.deadlineTime)
                : '🌱 No fixed deadline';

            return `
                <div class="p-3.5 bg-white border border-[#EAE4DF] hover:border-[#D8D2CD] rounded-2xl flex items-center justify-between gap-3 shadow-sm transition">
                    <div class="space-y-1 min-w-0">
                        <h5 class="text-xs sm:text-sm font-bold text-[#202124] truncate">${escapeHTML(t.name)}</h5>
                        <p class="text-[11px] text-[#6F6B68] flex items-center space-x-1">
                            <span>🕒</span>
                            <span>${deadlineText}</span>
                        </p>
                    </div>
                    <div class="flex items-center space-x-2 shrink-0">
                        <button onclick="window.TempoEmergencyFlow.editRealityCheckTask('${t.id}')" 
                                class="px-2.5 py-1 text-[11px] font-semibold text-gray-600 hover:text-gray-900 hover:bg-stone-100 rounded-lg transition">
                            Edit
                        </button>
                        <button onclick="window.TempoEmergencyFlow.removeRealityCheckTask('${t.id}')" 
                                class="px-2.5 py-1 text-[11px] font-semibold text-rose-600 hover:text-rose-800 hover:bg-rose-50 rounded-lg transition">
                            Remove
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
            if (window.TempoApp) window.TempoApp.showToast("Please enter a task name.");
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

        const newName = prompt("Edit task name:", task.name);
        if (newName && newName.trim()) {
            task.name = newName.trim();
            renderRealityCheck();
            scheduleDraftAutosave();
        }
    }

    function loadSampleTasks() {
        const today = new Date();
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);

        const todayStr = today.toISOString().split('T')[0];
        const tomorrowStr = tomorrow.toISOString().split('T')[0];

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
            if (window.TempoApp) window.TempoApp.showToast("Please add at least one task to continue.");
            return;
        }
        assessmentIndex = 0;
        goToStage('prioritize');
    }

    // =========================================================================
    // STAGE 3: PRIORITIZE + ESTIMATE (One-Task-At-A-Time Assessment)
    // =========================================================================
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
        const relativeDueText = task.hasDeadline
            ? calculateRelativeDueText(task.deadlineDate, task.deadlineTime)
            : 'No fixed deadline (explore at your own pace)';

        container.innerHTML = `
            <div class="max-w-2xl mx-auto py-8 sm:py-10 space-y-6">
                <!-- Secondary Back Navigation -->
                <div class="flex items-center justify-between">
                    ${assessmentIndex > 0 
                        ? `<button onclick="window.TempoEmergencyFlow.previousAssessmentTask()" class="inline-flex items-center text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition py-1 group"><span class="mr-1.5 group-hover:-translate-x-0.5 transition-transform">←</span><span>Previous task</span></button>`
                        : `<button onclick="window.TempoEmergencyFlow.goToStage('reality-check')" class="inline-flex items-center text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition py-1 group"><span class="mr-1.5 group-hover:-translate-x-0.5 transition-transform">←</span><span>Back to Reality Check</span></button>`
                    }
                </div>

                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">PRIORITIZE & ESTIMATE</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        Let's figure out what needs your attention first.
                    </h2>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">
                        We'll look at one task at a time.
                    </p>
                </div>

                <!-- Progress Pill -->
                <div class="flex items-center justify-between text-xs text-[#6F6B68] px-1">
                    <span class="font-bold text-[#FF6B2C]">Task ${assessmentIndex + 1} of ${tasks.length}</span>
                    <span>${Math.round(((assessmentIndex + 1) / tasks.length) * 100)}% evaluated</span>
                </div>

                <!-- Task Card Preview -->
                <div class="bg-[#FFF8F2] border border-[#FFD2BA]/60 rounded-2xl p-4 sm:p-5 space-y-1">
                    <span class="text-[10px] font-bold uppercase tracking-wider text-[#B83D08]">Current Task</span>
                    <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124]">${escapeHTML(task.name)}</h3>
                    <p class="text-xs text-[#6F6B68] flex items-center space-x-1.5">
                        <span>🕒</span>
                        <span class="font-semibold text-gray-800">${relativeDueText}</span>
                    </p>
                </div>

                <!-- 4 Questions Card -->
                <div class="bg-white border border-[#EAE4DF] rounded-[22px] p-5 sm:p-7 space-y-6 shadow-sm">
                    <!-- Q1: Importance -->
                    <div class="space-y-2">
                        <label class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                            1. How important is this task?
                        </label>
                        <div class="grid grid-cols-3 gap-2.5">
                            ${['High', 'Medium', 'Low'].map(opt => `
                                <div onclick="window.TempoEmergencyFlow.setAssessmentOption('importance', '${opt}')"
                                     class="em-choice-pill p-3 rounded-xl text-center text-xs font-semibold ${task.importance === opt ? 'em-choice-pill--selected' : 'text-gray-700'}">
                                    ${opt}
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Q2: Consequences -->
                    <div class="space-y-2">
                        <label class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                            2. What happens if it's late or unfinished?
                        </label>
                        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                            ${['Big consequences', 'Some consequences', 'Not much', 'Not sure'].map(opt => `
                                <div onclick="window.TempoEmergencyFlow.setAssessmentOption('consequence', '${opt}')"
                                     class="em-choice-pill p-3 rounded-xl text-center text-xs font-semibold ${task.consequence === opt ? 'em-choice-pill--selected' : 'text-gray-700'}">
                                    ${opt}
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Q3: Flexibility (Multi-select) -->
                    <div class="space-y-2">
                        <label class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                            3. Can anything about this task change? <span class="text-[11px] font-normal text-[#6F6B68]">(Select all that apply)</span>
                        </label>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            ${[
                                'Reduce what I need to do',
                                'Ask someone for help',
                                'Move / negotiate the deadline',
                                'Probably not',
                                'Not sure'
                            ].map(opt => {
                                const isSelected = task.flexibility && task.flexibility.includes(opt);
                                return `
                                    <div onclick="window.TempoEmergencyFlow.toggleAssessmentFlexibility('${opt}')"
                                         class="em-choice-pill p-3 rounded-xl flex items-center justify-between text-xs font-medium ${isSelected ? 'em-choice-pill--selected' : 'text-gray-700'}">
                                        <span>${opt}</span>
                                        <span>${isSelected ? '✓' : '+'}</span>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>

                    <!-- Q4: User Estimated Duration -->
                    <div class="space-y-2 pt-2 border-t border-gray-100">
                        <div class="space-y-0.5">
                            <label class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                                4. How long do you think you'll need?
                            </label>
                            <p class="text-xs text-[#6F6B68]">A rough estimate is enough. You can adjust this later.</p>
                        </div>
                        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 pt-1">
                            ${[
                                { label: '30 min', val: 30 },
                                { label: '1h', val: 60 },
                                { label: '2h', val: 120 },
                                { label: '3h', val: 180 },
                                { label: 'Custom', val: 'custom' },
                                { label: 'Not sure', val: 'unknown' }
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
                                         class="em-choice-pill p-2.5 rounded-xl text-center text-xs font-semibold ${isSelected ? 'em-choice-pill--selected' : 'text-gray-700'}">
                                        ${dur.label}
                                    </div>
                                `;
                            }).join('')}
                        </div>

                        <!-- Custom duration input box -->
                        <div id="em-custom-duration-box" class="${task.isCustomDuration ? '' : 'hidden'} pt-2 space-y-1.5">
                            <label class="block text-xs font-semibold text-gray-700">Custom estimate</label>
                            <div class="flex items-center space-x-2">
                                <input id="em-custom-value-input" type="number" min="1" step="any"
                                       value="${task.customDurationValue || 45}"
                                       oninput="window.TempoEmergencyFlow.handleCustomDurationChange(this.value, null)"
                                       placeholder="Value"
                                       class="w-24 px-3 py-1.5 text-xs border border-gray-300 rounded-lg text-center font-bold focus:ring-1 focus:ring-[#FF6B2C] focus:outline-none">
                                <select id="em-custom-unit-select"
                                        onchange="window.TempoEmergencyFlow.handleCustomDurationChange(null, this.value)"
                                        class="px-3 py-1.5 text-xs border border-gray-300 rounded-lg bg-white font-semibold focus:ring-1 focus:ring-[#FF6B2C] focus:outline-none">
                                    <option value="minutes" ${(task.customDurationUnit || 'minutes') === 'minutes' ? 'selected' : ''}>minutes</option>
                                    <option value="hours" ${task.customDurationUnit === 'hours' ? 'selected' : ''}>hours</option>
                                    <option value="days" ${task.customDurationUnit === 'days' ? 'selected' : ''}>days</option>
                                    <option value="weeks" ${task.customDurationUnit === 'weeks' ? 'selected' : ''}>weeks</option>
                                    <option value="months" ${task.customDurationUnit === 'months' ? 'selected' : ''}>months</option>
                                </select>
                            </div>
                            <p class="text-[11px] text-[#6F6B68] font-medium" id="em-custom-preview-label">
                                Current estimate: <strong>${task.durationLabel || '45 minutes'}</strong>
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Navigation Controls -->
                <div class="pt-2 flex items-center justify-between">
                    ${assessmentIndex > 0 
                        ? `<button onclick="window.TempoEmergencyFlow.previousAssessmentTask()" class="text-xs font-semibold text-[#6F6B68] hover:text-[#202124]">← Previous task</button>`
                        : `<button onclick="window.TempoEmergencyFlow.goToStage('reality-check')" class="text-xs font-semibold text-[#6F6B68] hover:text-[#202124]">← Reality Check</button>`
                    }
                    <button onclick="window.TempoEmergencyFlow.saveAssessmentAndNext()" 
                            class="btn-primary px-7 py-3 rounded-xl font-bold text-xs sm:text-sm shadow-sm flex items-center space-x-1.5 transition">
                        <span>${assessmentIndex === tasks.length - 1 ? 'Review Priority Categories →' : 'Save & next task →'}</span>
                    </button>
                </div>
            </div>
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
            preview.innerHTML = `Current estimate: <strong>${task.durationLabel}</strong>`;
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

        const categories = [
            { key: 'DO_FIRST', label: '🔴 DO FIRST', badge: 'bg-rose-50 text-rose-800 border-rose-200', desc: 'Urgent pressure with high impact. Needs immediate focus.' },
            { key: 'PLAN', label: '🟡 PLAN', badge: 'bg-amber-50 text-amber-800 border-amber-200', desc: 'Important work. Schedule dedicated blocks before deadlines.' },
            { key: 'REDUCE_HELP', label: '🟠 REDUCE / GET HELP', badge: 'bg-orange-50 text-orange-800 border-orange-200', desc: 'Scope can be trimmed, simplified, or delegated with peer help.' },
            { key: 'LATER', label: '⚪ LATER', badge: 'bg-stone-100 text-stone-700 border-stone-200', desc: 'Lower immediate stakes. Can be safely addressed after the crunch.' }
        ];

        container.innerHTML = `
            <div class="max-w-2xl mx-auto py-8 sm:py-10 space-y-6">
                <!-- Secondary Back Navigation -->
                <div class="flex items-center justify-between">
                    <button onclick="window.TempoEmergencyFlow.goToStage('prioritize')" 
                            class="inline-flex items-center text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition py-1 group">
                        <span class="mr-1.5 group-hover:-translate-x-0.5 transition-transform">←</span>
                        <span>Back to Assessment</span>
                    </button>
                </div>

                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">PRIORITY REVIEW</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        Suggested Organization
                    </h2>
                    <p class="text-xs sm:text-sm text-[#6F6B68] max-w-md mx-auto leading-relaxed">
                        Here is how Tempo grouped your tasks based on your answers. You can change any category if something feels off.
                    </p>
                </div>

                <!-- Category Groups -->
                <div class="space-y-5">
                    ${categories.map(cat => {
                        const catTasks = tasks.filter(t => t.priorityCategory === cat.key);
                        return `
                            <div class="bg-white border border-[#EAE4DF] rounded-2xl p-4 sm:p-5 space-y-3 shadow-sm">
                                <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                                    <div class="space-y-0.5">
                                        <span class="px-2.5 py-0.5 rounded-full text-xs font-bold border ${cat.badge}">${cat.label}</span>
                                        <p class="text-[11px] text-[#6F6B68] mt-1">${cat.desc}</p>
                                    </div>
                                    <span class="text-xs font-bold text-gray-500">${catTasks.length} task${catTasks.length === 1 ? '' : 's'}</span>
                                </div>

                                <div class="space-y-2">
                                    ${catTasks.length === 0 ? `<p class="text-xs text-gray-400 italic py-1">No tasks in this category.</p>` : ''}
                                    ${catTasks.map(t => `
                                        <div class="p-3 bg-[#FFFDFB] border border-[#EAE4DF] rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                                            <div class="space-y-1 min-w-0">
                                                <h5 class="text-xs sm:text-sm font-bold text-[#202124] truncate">${escapeHTML(t.name)}</h5>
                                                <p class="text-[11px] text-[#6F6B68] flex items-center space-x-2">
                                                    <span>🕒 ${t.hasDeadline ? formatHumanDeadline(t.deadlineDate, t.deadlineTime) : 'No fixed deadline'}</span>
                                                    <span>•</span>
                                                    <span>⏱️ ~${t.durationLabel}</span>
                                                </p>
                                            </div>
                                            <!-- Reassign Dropdown -->
                                            <div class="shrink-0 flex items-center space-x-1.5">
                                                <label class="text-[10px] text-gray-500 uppercase font-semibold">Category:</label>
                                                <select onchange="window.TempoEmergencyFlow.reassignTaskCategory('${t.id}', this.value)"
                                                        class="text-xs font-semibold border border-gray-200 rounded-lg px-2 py-1 bg-white text-gray-800 focus:outline-none focus:ring-1 focus:ring-[#FF6B2C]">
                                                    <option value="DO_FIRST" ${t.priorityCategory === 'DO_FIRST' ? 'selected' : ''}>DO FIRST</option>
                                                    <option value="PLAN" ${t.priorityCategory === 'PLAN' ? 'selected' : ''}>PLAN</option>
                                                    <option value="REDUCE_HELP" ${t.priorityCategory === 'REDUCE_HELP' ? 'selected' : ''}>REDUCE / HELP</option>
                                                    <option value="LATER" ${t.priorityCategory === 'LATER' ? 'selected' : ''}>LATER</option>
                                                </select>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>

                <!-- Navigation Controls -->
                <div class="pt-4 flex items-center justify-between border-t border-[#EAE4DF]">
                    <button onclick="window.TempoEmergencyFlow.goToStage('prioritize')" class="text-xs font-semibold text-[#6F6B68] hover:text-[#202124]">
                        ← Back to Assessment
                    </button>
                    <button onclick="window.TempoEmergencyFlow.goToStage('available-time')" 
                            class="btn-primary px-7 py-3 rounded-xl font-bold text-xs sm:text-sm shadow-sm flex items-center space-x-1.5 transition">
                        <span>Continue to Available Time →</span>
                    </button>
                </div>
            </div>
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
    function formatDayLabel(dateStr) {
        const today = new Date();
        const todayStr = today.toISOString().split('T')[0];
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const tomorrowStr = tomorrow.toISOString().split('T')[0];

        const [y, m, d] = dateStr.split('-').map(Number);
        const targetDate = new Date(y, m - 1, d);

        const monthDay = targetDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }).toUpperCase();
        const weekday = targetDate.toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase();

        if (dateStr === todayStr) {
            return `TODAY · ${monthDay}`;
        } else if (dateStr === tomorrowStr) {
            return `TOMORROW · ${monthDay}`;
        } else {
            return `${weekday} · ${monthDay}`;
        }
    }

    function getSuggestedNextDayStr() {
        if (!availabilityDays || availabilityDays.length === 0) {
            const today = new Date();
            return today.toISOString().split('T')[0];
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
        const today = new Date();
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);

        const todayStr = today.toISOString().split('T')[0];
        const tomorrowStr = tomorrow.toISOString().split('T')[0];

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

        const totalAvailableMin = calculateTotalAvailableMinutes();
        const totalWorkloadMin = calculateTotalWorkloadMinutes();
        const unknownCount = getUnknownTasksCount();
        const allUnavailable = availabilityDays.length > 0 && availabilityDays.every(d => d.isUnavailable);
        const todayStr = new Date().toISOString().split('T')[0];

        container.innerHTML = `
            <div class="max-w-2xl mx-auto py-8 sm:py-10 space-y-6">
                <!-- Secondary Back Navigation -->
                <div class="flex items-center justify-between">
                    <button onclick="window.TempoEmergencyFlow.goToStage('priority-review')" 
                            class="inline-flex items-center text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition py-1 group">
                        <span class="mr-1.5 group-hover:-translate-x-0.5 transition-transform">←</span>
                        <span>Back to Priority Review</span>
                    </button>
                </div>

                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">AVAILABLE TIME</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        When can you actually work on this?
                    </h2>
                    <p class="text-xs sm:text-sm text-[#6F6B68] max-w-md mx-auto leading-relaxed">
                        Tell Tempo when you're available. We'll build the plan around your time — not the other way around.
                    </p>
                </div>

                <!-- Shortcuts Card -->
                <div class="p-3 bg-white border border-[#EAE4DF] rounded-2xl flex flex-wrap items-center justify-between gap-2 text-xs">
                    <span class="font-semibold text-gray-700">Quick shortcuts:</span>
                    <div class="flex flex-wrap gap-2">
                        <button onclick="window.TempoEmergencyFlow.shortcutFreeRestOfToday()" 
                                class="px-3 py-1.5 bg-[#FFF4EC] text-[#B83D08] hover:bg-[#FFE8D9] rounded-xl font-bold transition">
                            ⚡ Free for rest of today
                        </button>
                        <button onclick="window.TempoEmergencyFlow.shortcutCopyTodayToTomorrow()" 
                                class="px-3 py-1.5 bg-stone-100 text-stone-700 hover:bg-stone-200 rounded-xl font-semibold transition">
                            📋 Copy today to tomorrow
                        </button>
                    </div>
                </div>

                <!-- All Unavailable Notice Banner (if all days unavailable) -->
                ${allUnavailable ? `
                    <div class="p-4 bg-amber-50 border border-amber-200 rounded-2xl text-center space-y-2 text-xs text-amber-900">
                        <p class="font-bold">You haven't added any available work time yet.</p>
                        <p class="text-amber-800">Add at least one time block so Tempo can organize your tasks effectively.</p>
                        <button onclick="window.TempoEmergencyFlow.restoreAllAvailability()" 
                                class="px-4 py-2 bg-amber-200 hover:bg-amber-300 font-bold rounded-xl text-amber-900 transition">
                            Reset default availability
                        </button>
                    </div>
                ` : ''}

                <!-- Date Blocks -->
                <div class="space-y-4">
                    ${availabilityDays.map((day, dayIndex) => {
                        const isToday = day.date === todayStr;

                        if (day.isUnavailable) {
                            return `
                                <div class="bg-[#FAF8F5] border border-[#EAE4DF] border-dashed rounded-[22px] p-5 space-y-3 shadow-sm">
                                    <div class="flex items-center justify-between pb-2 border-b border-gray-200">
                                        <div class="flex items-center space-x-2">
                                            <span class="font-heading text-xs font-extrabold tracking-wider text-gray-500 uppercase">${day.label}</span>
                                            <span class="px-2 py-0.5 bg-stone-200 text-stone-600 rounded-md text-[10px] font-bold">NOT AVAILABLE</span>
                                        </div>
                                        <div class="flex items-center space-x-2">
                                            <span class="text-xs font-bold text-gray-400">0h total</span>
                                            ${!isToday ? `
                                                <button onclick="window.TempoEmergencyFlow.openRemoveDayModal(${dayIndex})"
                                                        class="text-[11px] text-rose-500 hover:text-rose-700 font-semibold transition ml-1"
                                                        title="Remove this day from planning window">
                                                    Remove day
                                                </button>
                                            ` : ''}
                                        </div>
                                    </div>
                                    <p class="text-xs text-[#6F6B68]">
                                        You marked this day as unavailable. No tasks will be scheduled here.
                                    </p>
                                    <div class="flex items-center space-x-3">
                                        <button onclick="window.TempoEmergencyFlow.toggleDayUnavailable(${dayIndex})"
                                                class="text-xs text-[#FF6B2C] hover:underline font-bold flex items-center space-x-1">
                                            <span>+ Add availability for this day</span>
                                        </button>
                                    </div>
                                </div>
                            `;
                        }

                        const dayMinutes = calculateDayMinutes(day);

                        return `
                            <div class="bg-white border border-[#EAE4DF] rounded-[22px] p-5 space-y-3 shadow-sm">
                                <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                                    <span class="font-heading text-xs font-extrabold tracking-wider text-[#FF6B2C] uppercase">${day.label}</span>
                                    <div class="flex items-center space-x-3">
                                        <span class="text-xs font-bold text-gray-600">${formatDayTotalDisplay(dayMinutes)}</span>
                                        <button onclick="window.TempoEmergencyFlow.toggleDayUnavailable(${dayIndex})"
                                                class="text-[11px] text-gray-400 hover:text-stone-700 font-semibold transition"
                                                title="Mark day as unavailable">
                                            Mark day as not available
                                        </button>
                                        ${!isToday ? `
                                            <button onclick="window.TempoEmergencyFlow.openRemoveDayModal(${dayIndex})"
                                                    class="text-[11px] text-rose-500 hover:text-rose-700 font-semibold transition"
                                                    title="Remove this day from planning window">
                                                Remove day
                                            </button>
                                        ` : ''}
                                    </div>
                                </div>

                                <!-- Time Blocks List -->
                                <div class="space-y-2.5">
                                    ${day.blocks.map((block, bIdx) => {
                                        const hasOverlapWithPrev = bIdx > 0 && parseTimeToMinutes(block.start) < parseTimeToMinutes(day.blocks[bIdx - 1].end);
                                        return `
                                            <div class="flex items-center justify-between p-2.5 bg-[#FFFDFB] border border-[#EAE4DF] rounded-xl gap-2 text-xs">
                                                <div class="flex items-center space-x-2">
                                                    <span>From</span>
                                                    <input type="time" value="${block.start}" 
                                                           onchange="window.TempoEmergencyFlow.updateBlockTime(${dayIndex}, '${block.id}', this.value, null)"
                                                           class="px-2 py-1 border border-gray-200 rounded-lg bg-white font-semibold">
                                                    <span>to</span>
                                                    <input type="time" value="${block.end}" 
                                                           onchange="window.TempoEmergencyFlow.updateBlockTime(${dayIndex}, '${block.id}', null, this.value)"
                                                           class="px-2 py-1 border border-gray-200 rounded-lg bg-white font-semibold">
                                                    ${hasOverlapWithPrev ? `
                                                        <span class="text-[10px] text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200 font-semibold" title="Overlapping minutes are deduplicated automatically">
                                                            Overlaps
                                                        </span>
                                                    ` : ''}
                                                </div>
                                                <div class="flex items-center space-x-2">
                                                    <span class="text-[11px] font-bold text-[#FF6B2C]">${formatDurationMinutes(block.minutes)}</span>
                                                    ${day.blocks.length > 1 ? `
                                                        <button onclick="window.TempoEmergencyFlow.removeTimeBlock(${dayIndex}, '${block.id}')"
                                                                class="text-gray-400 hover:text-rose-600 p-1 rounded-md text-sm">✕</button>
                                                    ` : ''}
                                                </div>
                                            </div>
                                        `;
                                    }).join('')}
                                </div>

                                <button onclick="window.TempoEmergencyFlow.addTimeBlock(${dayIndex})" 
                                        class="text-xs text-[#FF6B2C] hover:underline font-bold pt-1 flex items-center space-x-1">
                                    <span>+ Add another time block</span>
                                </button>
                            </div>
                        `;
                    }).join('')}

                    <!-- + Add another day Button / Control -->
                    <div class="pt-1">
                        ${isAddingDay ? `
                            <div class="bg-white border-2 border-dashed border-[#FF6B2C]/40 rounded-[22px] p-5 space-y-3.5 shadow-sm animate-fade-in">
                                <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                                    <h4 class="font-heading text-xs font-bold uppercase tracking-wider text-[#202124]">
                                        Add availability for
                                    </h4>
                                    <button onclick="window.TempoEmergencyFlow.cancelAddDay()" 
                                            class="text-xs font-semibold text-gray-400 hover:text-gray-600">✕ Cancel</button>
                                </div>
                                <div class="flex flex-col sm:flex-row sm:items-center gap-3">
                                    <div class="space-y-1 flex-1">
                                        <label for="em-add-day-input" class="block text-[11px] font-medium text-[#6F6B68]">Select date:</label>
                                        <input id="em-add-day-input" type="date" min="${todayStr}"
                                               value="${getSuggestedNextDayStr()}"
                                               class="w-full sm:w-auto px-3 py-2 border border-gray-200 rounded-xl bg-white font-semibold text-xs text-gray-800 focus:outline-none focus:ring-1 focus:ring-[#FF6B2C]">
                                    </div>
                                    <div class="sm:pt-5">
                                        <button onclick="window.TempoEmergencyFlow.confirmAddDay()"
                                                class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs shadow-sm flex items-center space-x-1.5 transition">
                                            <span>Add day</span>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ` : `
                            <button onclick="window.TempoEmergencyFlow.startAddDay()" 
                                    class="w-full py-3.5 border-2 border-dashed border-[#EAE4DF] hover:border-[#FF6B2C] hover:bg-[#FFF4EC]/40 rounded-[22px] text-xs font-bold text-[#FF6B2C] flex items-center justify-center space-x-2 transition">
                                <span class="text-base leading-none">+</span>
                                <span>Add another day</span>
                            </button>
                        `}
                    </div>
                </div>

                <!-- Availability vs Workload Live Counter -->
                <div class="p-4 bg-[#FFF8F2] border border-[#FFD2BA]/70 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
                    <div>
                        <span class="font-bold text-[#202124]">Total Available Time:</span>
                        <span class="font-extrabold text-[#B83D08] ml-1">${formatDurationMinutes(totalAvailableMin)}</span>
                    </div>
                    <div>
                        <span class="font-bold text-[#202124]">Estimated Tasks Workload:</span>
                        <span class="font-extrabold text-[#FF6B2C] ml-1">${formatDurationMinutes(totalWorkloadMin)}</span>
                        ${unknownCount > 0 ? `<span class="text-[11px] text-gray-500 font-medium ml-1">(+${unknownCount} not fixed)</span>` : ''}
                    </div>
                </div>

                <!-- Navigation Controls -->
                <div class="pt-4 flex items-center justify-between border-t border-[#EAE4DF]">
                    <button onclick="window.TempoEmergencyFlow.goToStage('priority-review')" class="text-xs font-semibold text-[#6F6B68] hover:text-[#202124]">
                        ← Back to Priority Review
                    </button>
                    <button onclick="window.TempoEmergencyFlow.continueFromAvailableTime()" 
                            class="btn-primary px-7 py-3 rounded-xl font-bold text-xs sm:text-sm shadow-sm flex items-center space-x-1.5 transition">
                        <span>Check Feasibility & Build Plan →</span>
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
        const input = document.getElementById('em-add-day-input');
        if (!input || !input.value) {
            if (window.TempoApp) window.TempoApp.showToast("Please choose a date.");
            return;
        }

        const selectedDateStr = input.value;
        const today = new Date();
        const todayStr = today.toISOString().split('T')[0];

        // 1. Past date check
        if (selectedDateStr < todayStr) {
            if (window.TempoApp) window.TempoApp.showToast("Cannot add a date in the past. Today is the earliest valid date.");
            return;
        }

        // 2. Duplicate date check
        const exists = availabilityDays.some(d => d.date === selectedDateStr);
        if (exists) {
            if (window.TempoApp) window.TempoApp.showToast("This date is already in your planning window.");
            return;
        }

        // 3. Add day with simple initial availability state
        const newDay = {
            date: selectedDateStr,
            label: formatDayLabel(selectedDateStr),
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

    function formatRemoveDayModalDate(day) {
        if (!day || !day.date) return day ? day.label : '';
        const today = new Date();
        const todayStr = today.toISOString().split('T')[0];
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const tomorrowStr = tomorrow.toISOString().split('T')[0];

        const parts = day.date.split('-');
        if (parts.length === 3) {
            const y = parseInt(parts[0], 10);
            const m = parseInt(parts[1], 10);
            const d = parseInt(parts[2], 10);
            const targetDate = new Date(y, m - 1, d);
            const monthDay = targetDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            const weekday = targetDate.toLocaleDateString('en-US', { weekday: 'short' });

            let relative = '';
            if (day.date === todayStr) relative = 'Today';
            else if (day.date === tomorrowStr) relative = 'Tomorrow';
            else relative = weekday;

            return `${monthDay} · ${relative}`;
        }
        return day.label || day.date;
    }

    function getRemoveDayModalCopy(day) {
        const blockCount = (day.blocks ? day.blocks.length : 0);
        if (blockCount === 0) {
            return "This day will be removed from your planning window.";
        } else if (blockCount === 1) {
            return "Removing this day will also remove the 1 availability block you've added for it.";
        } else {
            return `Removing this day will also remove the ${blockCount} availability blocks you've added for it.`;
        }
    }

    function renderRemoveDayModalHTML() {
        if (!removeDayModalState) return '';
        const day = availabilityDays[removeDayModalState.dayIndex];
        if (!day) return '';

        const dateDisplay = formatRemoveDayModalDate(day);
        const blockCopy = getRemoveDayModalCopy(day);

        return `
            <div class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in"
                 onclick="if (event.target === this) window.TempoEmergencyFlow.closeRemoveDayModal()">
                <div class="bg-white border border-[#EAE4DF] rounded-[22px] max-w-md w-full p-6 space-y-4 shadow-2xl animate-scale-up"
                     role="dialog" aria-modal="true" aria-labelledby="em-remove-day-title">
                    <div class="flex items-center justify-between pb-3 border-b border-gray-100">
                        <h3 id="em-remove-day-title" class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">
                            Remove this day?
                        </h3>
                        <button onclick="window.TempoEmergencyFlow.closeRemoveDayModal()"
                                class="text-gray-400 hover:text-gray-600 text-lg p-1 transition"
                                aria-label="Close dialog">✕</button>
                    </div>

                    <div class="space-y-3">
                        <p class="font-heading text-sm sm:text-base font-bold text-[#FF6B2C]">
                            ${escapeHTML(dateDisplay)}
                        </p>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                            ${escapeHTML(blockCopy)}
                        </p>
                    </div>

                    <div class="pt-3 flex items-center justify-end space-x-3 border-t border-gray-100">
                        <button id="em-remove-day-cancel-btn"
                                onclick="window.TempoEmergencyFlow.closeRemoveDayModal()"
                                class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs sm:text-sm font-semibold text-gray-700 hover:bg-stone-50 transition">
                            Cancel
                        </button>
                        <button id="em-remove-day-confirm-btn"
                                onclick="window.TempoEmergencyFlow.confirmRemoveDay()"
                                class="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs sm:text-sm shadow-sm transition">
                            Remove day
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function openRemoveDayModal(dayIndex) {
        const day = availabilityDays[dayIndex];
        if (!day) return;

        const today = new Date();
        const todayStr = today.toISOString().split('T')[0];
        if (day.date === todayStr) {
            if (window.TempoApp) window.TempoApp.showToast("Today cannot be removed from your planning window.");
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
                    window.TempoApp.showToast("Adjusted start time forward so it's not in the past.");
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

    function formatDayTotalDisplay(mins) {
        if (mins <= 0) return '0h total';
        return `${formatDurationMinutes(mins)} total`;
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

    function recalculateTimelineSlotsPreservingOrder() {
        if (!confirmedPlan || !confirmedPlan.plannedTasks) return;

        // Group planned tasks by Day and re-sequence within available slots
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
                });
                return;
            }

            // Merged intervals for this day
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

            let intvIdx = 0;
            let currentPos = merged.length > 0 ? merged[0].start : 0;

            dayTasks.forEach(item => {
                if (item.task.isUnknownDuration || item.task.isLongTerm || !item.task.durationMinutes) {
                    item.startTime = null;
                    item.endTime = null;
                    item.startMin = null;
                    item.endMin = null;
                    item.isOverCapacity = false;
                    return;
                }

                const neededMin = item.task.durationMinutes;

                while (intvIdx < merged.length && currentPos >= merged[intvIdx].end) {
                    intvIdx++;
                    if (intvIdx < merged.length) {
                        currentPos = merged[intvIdx].start;
                    }
                }

                if (intvIdx < merged.length && currentPos + neededMin <= merged[intvIdx].end + 30) {
                    const startM = currentPos;
                    const endM = startM + neededMin;
                    item.startTime = formatMinutesToTimeString(startM);
                    item.endTime = formatMinutesToTimeString(endM);
                    item.startMin = startM;
                    item.endMin = endM;
                    item.isOverCapacity = false;
                    currentPos += neededMin;
                } else {
                    item.startTime = null;
                    item.endTime = null;
                    item.startMin = null;
                    item.endMin = null;
                    item.isOverCapacity = true;
                }
            });
        });

        // Recalculate execution badges and check deadline conflicts
        confirmedPlan.plannedTasks.forEach((item, idx) => {
            item.executionBadge = idx === 0 ? 'UP NEXT' : (idx === 1 ? 'THEN' : 'LATER');
            item.hasDeadlineConflict = checkDeadlineConflict(item.task, item.dayDate, item.endMin || 1440);
        });
    }

    function renderPlanReview() {
        const container = document.getElementById('emergency-stage-plan-review');
        if (!container || !confirmedPlan) return;

        // Group planned tasks by Day in order of availabilityDays
        const daysMap = {};
        availabilityDays.forEach(day => {
            daysMap[day.label] = [];
        });
        confirmedPlan.plannedTasks.forEach((item, idx) => {
            if (!daysMap[item.dayLabel]) {
                daysMap[item.dayLabel] = [];
            }
            daysMap[item.dayLabel].push({ ...item, globalIndex: idx });
        });

        const activeDayLabels = Object.keys(daysMap).filter(label => daysMap[label].length > 0);
        const hasSavedActive = !!(confirmedPlan && confirmedPlan.plannedTasks && confirmedPlan.plannedTasks.length > 0 && window.TempoPlanStore && window.TempoPlanStore.getActivePlan('emergency'));
        const returnToHandoff = viewingFromHandoff || hasSavedActive;

        container.innerHTML = `
            <div class="max-w-2xl mx-auto py-8 sm:py-10 space-y-6">
                <!-- Secondary Back Navigation -->
                <div class="flex items-center justify-between">
                    <button onclick="${returnToHandoff ? "window.TempoEmergencyFlow.goToStage('handoff')" : "window.TempoEmergencyFlow.navigateBackFromPlan()"}" 
                            class="inline-flex items-center text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition py-1 group">
                        <span class="mr-1.5 group-hover:-translate-x-0.5 transition-transform">←</span>
                        <span>${returnToHandoff ? "Back to plan overview" : "Back to availability"}</span>
                    </button>
                </div>

                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">EMERGENCY PLAN</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        Your Emergency Plan
                    </h2>
                    <p class="text-xs sm:text-sm text-[#6F6B68] max-w-md mx-auto leading-relaxed">
                        Here's a starting point based on what you told us. You can reorder, move between days, or adjust estimates anytime.
                    </p>
                </div>

                <!-- Unallocated Tasks Notice (if any) -->
                ${confirmedPlan.unallocatedTasks && confirmedPlan.unallocatedTasks.length > 0 ? `
                    <div class="p-4 bg-amber-50 border border-amber-200 rounded-2xl space-y-2 text-xs text-amber-900">
                        <div class="flex items-center space-x-2 font-bold">
                            <span>⚠️</span>
                            <span>${confirmedPlan.unallocatedTasks.length} task${confirmedPlan.unallocatedTasks.length === 1 ? '' : 's'} need more available working blocks</span>
                        </div>
                        <p class="text-amber-800">
                            We scheduled what fits first. The following work still needs dedicated time: 
                            <strong>${confirmedPlan.unallocatedTasks.map(t => t.name).join(', ')}</strong>.
                        </p>
                        <button onclick="window.TempoEmergencyFlow.navigateBackFromPlan()" 
                                class="text-xs font-bold text-[#B83D08] underline">
                            + Add more availability to fit everything
                        </button>
                    </div>
                ` : ''}

                <!-- Lightweight Timeline -->
                <div class="space-y-6">
                    ${activeDayLabels.length === 0 ? `
                        <div class="p-8 bg-white border border-[#EAE4DF] rounded-[22px] text-center text-xs text-gray-500">
                            No tasks scheduled in plan. Return to Reality Check to add tasks.
                        </div>
                    ` : activeDayLabels.map(dayLabel => `
                        <div class="space-y-3">
                            <h4 class="font-heading text-xs font-extrabold tracking-wider text-[#FF6B2C] uppercase px-1">
                                ${dayLabel}
                            </h4>

                            <div class="space-y-3">
                                ${daysMap[dayLabel].map(item => {
                                    const badgeClass = item.executionBadge === 'UP NEXT'
                                        ? 'badge-up-next'
                                        : (item.executionBadge === 'THEN' ? 'badge-then' : 'badge-later');

                                    const isWarned = item.hasDeadlineConflict && !ignoredDeadlineWarnings.has(item.task.id);

                                    return `
                                        <div class="em-timeline-card p-4 sm:p-5 space-y-3 shadow-sm">
                                            <!-- Top Meta Row -->
                                            <div class="flex items-center justify-between">
                                                <div class="flex items-center space-x-2">
                                                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase ${badgeClass}">
                                                        ${item.executionBadge}
                                                    </span>
                                                    ${item.startTime && item.endTime ? `
                                                        <span class="text-xs font-extrabold text-[#202124]">
                                                            ${item.startTime} – ${item.endTime}
                                                        </span>
                                                    ` : (item.task.isUnknownDuration ? `
                                                        <span class="px-2 py-0.5 bg-stone-100 text-stone-600 rounded text-[11px] font-semibold">
                                                            Flexible / Untimed
                                                        </span>
                                                    ` : (item.isOverCapacity ? `
                                                        <span class="px-2 py-0.5 bg-amber-100 text-amber-800 rounded text-[11px] font-semibold">
                                                            Scheduled (Beyond available blocks)
                                                        </span>
                                                    ` : `
                                                        <span class="px-2 py-0.5 bg-stone-100 text-stone-600 rounded text-[11px] font-semibold">
                                                            Flexible
                                                        </span>
                                                    `))}
                                                </div>
                                                <div class="flex items-center space-x-1.5">
                                                    <!-- Explicit Move Control (Mobile & Keyboard Accessible) -->
                                                    <button onclick="window.TempoEmergencyFlow.openMoveTaskModal(${item.globalIndex})"
                                                            class="px-2.5 py-1 text-xs font-bold border border-gray-200 hover:border-[#FF6B2C] hover:bg-[#FFF4EC] text-gray-700 hover:text-[#B83D08] rounded-lg transition flex items-center space-x-1"
                                                            title="Move task to another day or position">
                                                        <span>Move</span>
                                                        <span class="text-[10px]">⇄</span>
                                                    </button>
                                                    <!-- Move Up / Down Accessible Controls -->
                                                    <button onclick="window.TempoEmergencyFlow.movePlanTask(${item.globalIndex}, -1)"
                                                            ${item.globalIndex === 0 ? 'disabled class="opacity-20 cursor-not-allowed px-2 py-1 text-xs font-bold"' : 'class="hover:bg-stone-100 rounded text-gray-700 px-2 py-1 text-xs font-bold"'}
                                                            title="Move earlier">▲</button>
                                                    <button onclick="window.TempoEmergencyFlow.movePlanTask(${item.globalIndex}, 1)"
                                                            ${item.globalIndex === confirmedPlan.plannedTasks.length - 1 ? 'disabled class="opacity-20 cursor-not-allowed px-2 py-1 text-xs font-bold"' : 'class="hover:bg-stone-100 rounded text-gray-700 px-2 py-1 text-xs font-bold"'}
                                                            title="Move later">▼</button>
                                                </div>
                                            </div>

                                            <!-- Task Details -->
                                            <div class="space-y-1">
                                                <h4 class="font-heading text-base font-bold text-[#202124]">${escapeHTML(item.task.name)}</h4>
                                                <p class="text-xs text-[#6F6B68] flex items-center space-x-2">
                                                    <span>Estimate: <strong>${item.task.durationLabel || 'Not sure'}</strong></span>
                                                    <span>•</span>
                                                    <span>Due: ${item.task.hasDeadline ? formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime) : 'No fixed deadline'}</span>
                                                    <span>•</span>
                                                    <button onclick="window.TempoEmergencyFlow.openEditEstimateModal(${item.globalIndex})" 
                                                            class="text-[#FF6B2C] hover:underline font-semibold text-[11px]">
                                                        Edit estimate
                                                    </button>
                                                </p>
                                            </div>

                                            <!-- Deadline Warning Banner if reordered past deadline -->
                                            ${isWarned ? `
                                                <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                                    <span>⚠️ ${escapeHTML(item.task.name)} is due on ${formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime)}. Moving it here may risk its deadline.</span>
                                                    <button onclick="window.TempoEmergencyFlow.ignoreDeadlineWarning('${item.task.id}')"
                                                            class="px-2.5 py-1 bg-amber-200 hover:bg-amber-300 text-amber-900 font-bold rounded-lg text-[10px] shrink-0">
                                                        Keep my order
                                                    </button>
                                                </div>
                                            ` : ''}
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>

                <!-- Confirmation Card -->
                ${returnToHandoff ? `
                    <div class="p-5 bg-white border border-[#EAE4DF] rounded-[22px] space-y-4 text-center shadow-sm">
                        <div class="space-y-1">
                            <h4 class="font-heading text-base font-bold text-[#202124]">Plan is updated and saved</h4>
                            <p class="text-xs text-[#6F6B68]">Any adjustments you make are automatically saved.</p>
                        </div>
                        <div class="pt-1 flex flex-col sm:flex-row items-center justify-center gap-3">
                            <button onclick="window.TempoEmergencyFlow.goToStage('handoff')" 
                                    class="btn-primary w-full sm:w-auto px-6 py-3 rounded-xl font-bold text-xs sm:text-sm shadow-sm transition">
                                Return to Plan Overview →
                            </button>
                            <button onclick="window.TempoEmergencyFlow.launchFocusZone()" 
                                    class="w-full sm:w-auto px-5 py-3 rounded-xl border border-[#FF6B2C] text-[#FF6B2C] hover:bg-[#FFE9DC] text-xs font-bold transition">
                                Start Focus Zone →
                            </button>
                            <button onclick="window.TempoEmergencyFlow.confirmPlanAndProceed()" 
                                    class="w-full sm:w-auto px-4 py-3 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                                Review Step Breakdown
                            </button>
                        </div>
                    </div>
                ` : `
                    <div class="p-5 bg-white border border-[#EAE4DF] rounded-[22px] space-y-4 text-center shadow-sm">
                        <div class="space-y-1">
                            <h4 class="font-heading text-base font-bold text-[#202124]">Does this plan feel workable?</h4>
                            <p class="text-xs text-[#6F6B68]">You can change it again later as you make progress.</p>
                        </div>
                        <button onclick="window.TempoEmergencyFlow.confirmPlanAndProceed()" 
                                class="btn-primary w-full py-3.5 rounded-xl font-bold text-sm shadow-md flex items-center justify-center space-x-2 transition">
                            <span>Use this plan →</span>
                        </button>
                    </div>
                `}
            </div>

            <!-- Move Task Modal Dialog (if active) -->
            ${renderMoveTaskModalHTML()}

            <!-- User-Edited Plan Warning Modal (if active) -->
            ${renderPlanEditWarningModalHTML()}

            <!-- Edit Estimate Modal Dialog (if active) -->
            ${renderEditEstimateModalHTML()}
        `;
    }

    function renderPlanEditWarningModalHTML() {
        if (!showPlanEditWarningModal) return '';

        return `
            <div class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
                <div class="bg-white border border-[#EAE4DF] rounded-[22px] max-w-md w-full p-6 space-y-4 shadow-2xl">
                    <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                        <h3 class="font-heading text-sm sm:text-base font-extrabold text-[#202124]">
                            Plan Modified
                        </h3>
                        <button onclick="window.TempoEmergencyFlow.cancelPlanEditWarning()" 
                                class="text-gray-400 hover:text-gray-600 text-lg p-1"
                                title="Close">✕</button>
                    </div>

                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        You've made changes to this plan. Updating your availability may require Tempo to rebuild parts of it.
                    </p>

                    <div class="pt-3 flex flex-col-reverse sm:flex-row items-center justify-end gap-2 border-t border-gray-100">
                        <button onclick="window.TempoEmergencyFlow.cancelPlanEditWarning()"
                                class="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                            Cancel
                        </button>
                        <button onclick="window.TempoEmergencyFlow.confirmPlanEditWarningAndGoBack()"
                                class="btn-primary w-full sm:w-auto px-5 py-2.5 rounded-xl font-bold text-xs shadow-sm transition">
                            Continue editing availability
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

        return `
            <div class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                <div class="bg-white border border-[#EAE4DF] rounded-[22px] max-w-md w-full p-6 space-y-5 shadow-2xl">
                    <div class="flex items-center justify-between pb-3 border-b border-gray-100">
                        <h3 class="font-heading text-base font-extrabold text-[#202124]">
                            Move Task
                        </h3>
                        <button onclick="window.TempoEmergencyFlow.closeMoveTaskModal()" 
                                class="text-gray-400 hover:text-gray-600 text-lg p-1">✕</button>
                    </div>

                    <div class="space-y-4 text-xs">
                        <div>
                            <span class="text-gray-500 font-medium">Task:</span>
                            <p class="text-sm font-bold text-[#202124] mt-0.5">${escapeHTML(item.task.name)}</p>
                            <p class="text-gray-500 text-[11px]">Estimate: ~${item.task.durationLabel} • Due: ${item.task.hasDeadline ? formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime) : 'No fixed deadline'}</p>
                        </div>

                        <div class="space-y-1">
                            <label class="block font-bold text-gray-700 uppercase tracking-wider text-[10px]">Select Target Day:</label>
                            <select id="em-move-target-day" onchange="window.TempoEmergencyFlow.updateMoveModalPreview(this.value, null)"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-xl bg-white font-semibold text-xs focus:ring-1 focus:ring-[#FF6B2C] focus:outline-none">
                                ${availabilityDays.map(day => {
                                    const isSelected = day.date === moveModalState.targetDayDate;
                                    const availText = day.isUnavailable ? '(Unavailable)' : `(${formatDurationMinutes(calculateDayMinutes(day))} available)`;
                                    return `<option value="${day.date}" ${isSelected ? 'selected' : ''}>${day.label} ${availText}</option>`;
                                }).join('')}
                            </select>
                        </div>

                        <div class="space-y-1">
                            <label class="block font-bold text-gray-700 uppercase tracking-wider text-[10px]">Position in day:</label>
                            <select id="em-move-target-pos" onchange="window.TempoEmergencyFlow.updateMoveModalPreview(null, this.value)"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-xl bg-white font-semibold text-xs focus:ring-1 focus:ring-[#FF6B2C] focus:outline-none">
                                <option value="first" ${moveModalState.targetPosition === 'first' ? 'selected' : ''}>Start of this day</option>
                                <option value="last" ${moveModalState.targetPosition === 'last' ? 'selected' : ''}>End of this day</option>
                            </select>
                        </div>

                        <!-- Conflict / Feasibility Preview Warnings -->
                        <div id="em-move-modal-warnings" class="space-y-2">
                            ${renderMoveModalWarningsHTML(item, moveModalState.targetDayDate)}
                        </div>
                    </div>

                    <div class="pt-2 flex items-center justify-end space-x-2 border-t border-gray-100">
                        <button onclick="window.TempoEmergencyFlow.closeMoveTaskModal()"
                                class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                            Cancel
                        </button>
                        <button onclick="window.TempoEmergencyFlow.executeMoveTask()"
                                class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs shadow-sm transition">
                            Keep my choice & Move
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function renderMoveModalWarningsHTML(item, targetDate) {
        const targetDay = availabilityDays.find(d => d.date === targetDate);
        if (!targetDay) return '';

        const warnings = [];

        // 1. Availability check
        if (targetDay.isUnavailable) {
            warnings.push(`
                <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-xs">
                    ⚠️ <strong>Day is unavailable:</strong> You marked this day as unavailable. This task will be scheduled as flexible/untimed unless availability is added.
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
                        ⚠️ <strong>Time limit note:</strong> This day has ~${formatDurationMinutes(Math.max(0, remainingMin))} remaining, but this task needs ~${item.task.durationLabel}.
                    </div>
                `);
            }
        }

        // 2. Deadline check
        if (item.task.hasDeadline && item.task.deadlineDate && targetDate > item.task.deadlineDate) {
            warnings.push(`
                <div class="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-900 text-xs">
                    ⚠️ <strong>Deadline warning:</strong> This task is due on ${formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime)}. Moving it to ${targetDay.label} places it after its deadline.
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
                if (window.TempoApp) window.TempoApp.showToast("Please enter a valid estimate duration greater than 0.");
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

        const task = item.task;

        return `
            <div class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in"
                 onclick="if (event.target === this) window.TempoEmergencyFlow.closeEditEstimateModal()">
                <div class="bg-white border border-[#EAE4DF] rounded-[22px] max-w-md w-full p-6 space-y-5 shadow-2xl animate-scale-up"
                     role="dialog" aria-modal="true" aria-labelledby="em-edit-estimate-title">
                    <div class="flex items-center justify-between pb-3 border-b border-gray-100">
                        <h3 id="em-edit-estimate-title" class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">
                            Edit time estimate
                        </h3>
                        <button onclick="window.TempoEmergencyFlow.closeEditEstimateModal()"
                                class="text-gray-400 hover:text-gray-600 text-lg p-1 transition"
                                aria-label="Close dialog">✕</button>
                    </div>

                    <div class="space-y-4">
                        <div>
                            <span class="text-[11px] font-bold text-gray-500 uppercase tracking-wider block">Task</span>
                            <p class="text-sm font-extrabold text-[#202124] mt-0.5">${escapeHTML(task.name)}</p>
                        </div>

                        <div class="space-y-2">
                            <label class="block text-xs font-semibold text-gray-700">
                                How long do you think this task will take?
                            </label>
                            <div class="flex items-center space-x-2">
                                <input id="em-edit-estimate-value" type="number" min="0.1" step="any"
                                       value="${isNotSure ? '' : (value !== '' && value !== null && value !== undefined ? value : '')}"
                                       ${isNotSure ? 'disabled' : ''}
                                       placeholder="e.g. 1.5"
                                       class="w-28 px-3 py-2 text-xs sm:text-sm border border-gray-300 rounded-xl text-center font-bold text-[#202124] focus:ring-1 focus:ring-[#FF6B2C] focus:outline-none transition ${isNotSure ? 'opacity-40 bg-stone-100 cursor-not-allowed' : 'bg-white'}">
                                <select id="em-edit-estimate-unit"
                                        ${isNotSure ? 'disabled' : ''}
                                        class="px-3 py-2 text-xs sm:text-sm border border-gray-300 rounded-xl bg-white font-semibold text-[#202124] focus:ring-1 focus:ring-[#FF6B2C] focus:outline-none transition ${isNotSure ? 'opacity-40 bg-stone-100 cursor-not-allowed' : ''}">
                                    <option value="minutes" ${unit === 'minutes' ? 'selected' : ''}>minutes</option>
                                    <option value="hours" ${unit === 'hours' ? 'selected' : ''}>hours</option>
                                    <option value="days" ${unit === 'days' ? 'selected' : ''}>days</option>
                                    <option value="weeks" ${unit === 'weeks' ? 'selected' : ''}>weeks</option>
                                    <option value="months" ${unit === 'months' ? 'selected' : ''}>months</option>
                                </select>
                            </div>
                        </div>

                        <div class="pt-1">
                            <label class="inline-flex items-center space-x-2 cursor-pointer select-none">
                                <input type="checkbox" id="em-edit-estimate-notsure"
                                       ${isNotSure ? 'checked' : ''}
                                       onchange="window.TempoEmergencyFlow.toggleEditEstimateNotSure(this.checked)"
                                       class="w-4 h-4 rounded text-[#FF6B2C] focus:ring-[#FF6B2C] border-gray-300">
                                <span class="text-xs sm:text-sm font-medium text-gray-700">I'm not sure yet</span>
                            </label>
                        </div>
                    </div>

                    <div class="pt-3 flex items-center justify-end space-x-3 border-t border-gray-100">
                        <button id="em-edit-estimate-cancel-btn"
                                onclick="window.TempoEmergencyFlow.closeEditEstimateModal()"
                                class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs sm:text-sm font-semibold text-gray-700 hover:bg-stone-50 transition">
                            Cancel
                        </button>
                        <button id="em-edit-estimate-save-btn"
                                onclick="window.TempoEmergencyFlow.saveEditEstimate()"
                                class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-sm transition">
                            Save estimate
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function confirmPlanAndProceed() {
        if (!confirmedPlan || confirmedPlan.plannedTasks.length === 0) {
            goToStage('reality-check');
            return;
        }

        // Persist confirmed active plan to durable store
        if (window.TempoPlanStore) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }

        breakdownIndex = 0;
        showAiSuggestions = false;
        currentAiSuggestions = [];
        aiSuggestionError = false;
        goToStage('breakdown');
    }

    // =========================================================================
    // STAGE 8: BREAK DOWN TASKS (In Plan Execution Order)
    // =========================================================================
    function renderBreakdown() {
        const container = document.getElementById('emergency-stage-breakdown');
        if (!container || !confirmedPlan || !confirmedPlan.plannedTasks) return;

        if (breakdownIndex >= confirmedPlan.plannedTasks.length) {
            startWorking();
            return;
        }

        const planItem = confirmedPlan.plannedTasks[breakdownIndex];
        const task = planItem.task;

        // Initialize subtasks array if not present
        if (!task.subtasks) {
            task.subtasks = [];
        }

        const totalSubtasksCount = task.subtasks.length;
        const estimatedSubtasks = task.subtasks.filter(s => typeof s.durationMinutes === 'number' && s.durationMinutes > 0);
        const unestimatedCount = totalSubtasksCount - estimatedSubtasks.length;
        const totalKnownSubtaskMin = estimatedSubtasks.reduce((sum, s) => sum + s.durationMinutes, 0);
        const allSubtasksEstimated = totalSubtasksCount > 0 && unestimatedCount === 0;

        container.innerHTML = `
            <div class="max-w-2xl mx-auto py-8 sm:py-10 space-y-6">
                <!-- Secondary Back Navigation & Task Stepper -->
                <div class="flex items-center justify-between">
                    <button onclick="window.TempoEmergencyFlow.goToStage('plan-review')" 
                            class="inline-flex items-center text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition py-1 group">
                        <span class="mr-1.5 group-hover:-translate-x-0.5 transition-transform">←</span>
                        <span>Back to Emergency Plan</span>
                    </button>
                    <div class="flex items-center space-x-2 text-xs">
                        ${breakdownIndex > 0 ? `
                            <button onclick="window.TempoEmergencyFlow.breakdownPreviousTask()" 
                                    class="text-xs font-semibold text-[#6F6B68] hover:text-[#202124] px-2.5 py-1 rounded-lg border border-gray-200 hover:bg-stone-50 transition">
                                ← Previous task
                            </button>
                        ` : ''}
                        ${breakdownIndex < confirmedPlan.plannedTasks.length - 1 ? `
                            <button onclick="window.TempoEmergencyFlow.breakdownNextTask()" 
                                    class="text-xs font-semibold text-[#FF6B2C] hover:text-[#B83D08] px-2.5 py-1 rounded-lg border border-[#FF6B2C]/30 hover:bg-[#FFE9DC]/50 transition">
                                Next task →
                            </button>
                        ` : ''}
                    </div>
                </div>

                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">STEP BREAKDOWN</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        ${breakdownIndex === 0 ? "Let's make your first task easier to start." : `Break down task ${breakdownIndex + 1} of ${confirmedPlan.plannedTasks.length}`}
                    </h2>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">
                        Task ${breakdownIndex + 1} of ${confirmedPlan.plannedTasks.length} in your planned schedule.
                    </p>
                </div>

                <!-- Planned Task Header Card -->
                <div class="bg-[#FFF8F2] border border-[#FFD2BA]/70 rounded-[22px] p-5 sm:p-6 space-y-2">
                    <div class="flex items-center space-x-2">
                        <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase badge-up-next">
                            ${planItem.executionBadge}
                        </span>
                        <span class="text-xs text-[#6F6B68]">
                            ${planItem.startTime && planItem.endTime ? `Scheduled for ${planItem.startTime} – ${planItem.endTime}` : 'Scheduled: Flexible / Untimed'}
                        </span>
                    </div>
                    <h3 class="font-heading text-xl font-bold text-[#202124]">${escapeHTML(task.name)}</h3>
                    <p class="text-xs text-[#6F6B68]">
                        Due: ${task.hasDeadline ? formatHumanDeadline(task.deadlineDate, task.deadlineTime) : 'No fixed deadline'} • Estimated total: <strong>${task.durationLabel || 'Not sure'}</strong>
                    </p>
                </div>

                <!-- Active Steps Editor (Default Manual Breakdown) -->
                <div class="bg-white border border-[#EAE4DF] rounded-[22px] p-5 sm:p-6 space-y-4 shadow-sm">
                    <!-- Card Header: Title + Action buttons -->
                    <div class="flex items-center justify-between pb-2 border-b border-gray-100 flex-wrap gap-2">
                        <div class="flex items-center space-x-2">
                            <h4 class="font-heading text-sm font-bold text-[#202124]">Concrete Action Steps</h4>
                            <span class="text-xs text-[#8E8A85]">(${totalSubtasksCount})</span>
                        </div>
                        <div class="flex items-center space-x-2">
                            <!-- On-Demand AI Help Button -->
                            <button type="button" 
                                    onclick="window.TempoEmergencyFlow.toggleAiHelp()" 
                                    class="px-2.5 py-1 rounded-lg text-xs font-bold text-[#B83D08] bg-[#FFE9DC] hover:bg-[#FFD2BA] transition flex items-center space-x-1.5 shadow-sm border border-[#FF6B2C]/30"
                                    title="Get AI starter suggestions for this task">
                                <span>✨</span>
                                <span>AI Help</span>
                            </button>
                            <!-- Show / Hide Subtask Times Toggle -->
                            <button type="button" 
                                    onclick="window.TempoEmergencyFlow.toggleSubtaskDurations()" 
                                    class="text-xs text-[#6F6B68] hover:text-[#202124] font-medium flex items-center space-x-1 pl-1">
                                <span>⏱️ Times:</span>
                                <span class="font-bold underline">${showSubtaskDurations ? 'Hide' : 'Show'}</span>
                            </button>
                        </div>
                    </div>

                    <!-- "I Already Know" Acknowledgment Banner (if user marked this task) -->
                    ${task.alreadyKnowWhatToDo ? `
                        <div class="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center justify-between">
                            <div class="flex items-center space-x-2">
                                <span class="text-emerald-600 font-bold">✓</span>
                                <span>You've indicated you already know what to do next for this task.</span>
                            </div>
                            <button onclick="window.TempoEmergencyFlow.toggleAlreadyKnowWhatToDo(false)" 
                                    class="text-[11px] text-emerald-700 hover:text-emerald-900 underline font-semibold shrink-0 ml-2">
                                Reset
                            </button>
                        </div>
                    ` : ''}

                    <!-- On-Demand AI Help Suggestions Card -->
                    ${showAiSuggestions ? `
                        <div class="p-4 bg-[#FFFBF8] border border-[#FFD2BA] rounded-2xl space-y-3 animate-fade-in shadow-sm">
                            <div class="flex items-center justify-between pb-1 border-b border-[#FFE9DC]">
                                <div class="flex items-center space-x-1.5">
                                    <span class="text-sm">✨</span>
                                    <h5 class="text-xs font-bold text-[#202124]">Suggested steps for this task</h5>
                                </div>
                                <button onclick="window.TempoEmergencyFlow.closeAiHelp()" 
                                        class="text-xs text-[#8E8A85] hover:text-[#202124] p-1 font-bold" 
                                        title="Dismiss suggestions">✕</button>
                            </div>
                            ${aiSuggestionError ? `
                                <p class="text-xs text-stone-600 bg-stone-100 p-2.5 rounded-xl">
                                    AI suggestions aren't available right now. You can keep breaking this task down yourself.
                                </p>
                            ` : currentAiSuggestions.length === 0 ? `
                                <p class="text-xs text-[#6F6B68]">All suggested steps have been added or already exist.</p>
                            ` : `
                                <div class="space-y-2">
                                    ${currentAiSuggestions.map((sug, sugIdx) => `
                                        <div class="p-2.5 bg-white border border-[#EAE4DF] rounded-xl flex items-center justify-between gap-2 text-xs">
                                            <div class="flex items-center space-x-2 flex-1 min-w-0">
                                                <span class="w-1.5 h-1.5 rounded-full bg-[#FF6B2C] shrink-0"></span>
                                                <span class="font-medium text-[#202124] truncate">${escapeHTML(sug.title)}</span>
                                            </div>
                                            <div class="flex items-center space-x-2 shrink-0">
                                                ${sug.durationMinutes ? `<span class="text-[11px] text-[#6F6B68] font-semibold">${formatSubtaskDurationDisplay(sug.durationMinutes)}</span>` : ''}
                                                <button onclick="window.TempoEmergencyFlow.acceptAiSuggestion(${sugIdx})" 
                                                        class="px-2.5 py-1 bg-stone-100 hover:bg-[#FFE9DC] hover:text-[#B83D08] font-bold text-[11px] rounded-lg border border-stone-200 hover:border-[#FF6B2C]/40 transition">
                                                    + Add
                                                </button>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                                <div class="flex items-center justify-between pt-1 text-xs">
                                    <button onclick="window.TempoEmergencyFlow.acceptAllAiSuggestions()" 
                                            class="btn-primary px-3 py-1.5 rounded-xl font-bold text-xs shadow-sm">
                                        Add all suggestions
                                    </button>
                                    <button onclick="window.TempoEmergencyFlow.closeAiHelp()" 
                                            class="text-xs text-[#8E8A85] hover:text-[#202124] underline">
                                        Dismiss
                                    </button>
                                </div>
                            `}
                        </div>
                    ` : ''}

                    <!-- Subtask Comparison / Mismatch Notice -->
                    ${(() => {
                        if (!showSubtaskDurations || totalSubtasksCount === 0 || estimatedSubtasks.length === 0) {
                            return '';
                        }

                        // Case 1: Incomplete estimates (one or more subtasks lack a duration estimate)
                        if (unestimatedCount > 0) {
                            const stepWord = unestimatedCount === 1 ? "1 step doesn't" : `${unestimatedCount} steps don't`;
                            return `
                                <div class="p-3.5 bg-stone-50 border border-stone-200 rounded-xl text-xs text-stone-800 space-y-1">
                                    <p>
                                        Your estimated steps currently add up to <strong>${formatDurationMinutes(totalKnownSubtaskMin)}</strong> (partial &mdash; ${stepWord} have a time estimate yet). 
                                        Your main task estimate is <strong>${task.durationLabel || 'Not sure'}</strong>.
                                    </p>
                                </div>
                            `;
                        }

                        // Case 2: All subtasks have estimates
                        if (allSubtasksEstimated) {
                            const isDismissed = dismissedMismatchForTask[task.id] === true;
                            const isFiniteTask = !task.isUnknownDuration && !task.isLongTerm && typeof task.durationMinutes === 'number' && task.durationMinutes > 0;
                            const hasDifference = isFiniteTask ? totalKnownSubtaskMin !== task.durationMinutes : true;

                            if (hasDifference && !isDismissed) {
                                return `
                                    <div class="p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 space-y-2">
                                        <p>
                                            Your step estimates add up to about <strong>${formatDurationMinutes(totalKnownSubtaskMin)}</strong>. 
                                            Your main task estimate is currently <strong>${task.durationLabel || 'Not sure'}</strong>.
                                        </p>
                                        <div class="flex flex-wrap gap-2 pt-1">
                                            <button onclick="window.TempoEmergencyFlow.syncTaskDurationFromSteps(${totalKnownSubtaskMin})" 
                                                    class="px-2.5 py-1 bg-amber-200 hover:bg-amber-300 font-bold rounded-lg text-[11px] transition">
                                                Update task estimate to ${formatDurationMinutes(totalKnownSubtaskMin)}
                                            </button>
                                            ${isFiniteTask ? `
                                                <button onclick="window.TempoEmergencyFlow.keepTaskDurationMismatch()" 
                                                        class="px-2.5 py-1 bg-white border border-amber-300 text-amber-900 font-semibold rounded-lg text-[11px] hover:bg-amber-100/50 transition">
                                                    Keep ${task.durationLabel}
                                                </button>
                                            ` : ''}
                                        </div>
                                    </div>
                                `;
                            } else if (!hasDifference) {
                                return `
                                    <div class="p-2.5 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center space-x-2">
                                        <span>✓</span>
                                        <span>Your step estimates add up to <strong>${formatDurationMinutes(totalKnownSubtaskMin)}</strong>, matching your main task estimate.</span>
                                    </div>
                                `;
                            }
                        }

                        return '';
                    })()}

                    <!-- Steps List -->
                    <div class="space-y-2.5">
                        ${task.subtasks.length === 0 ? `
                            <div class="p-4 bg-stone-50 border border-dashed border-[#EAE4DF] rounded-xl text-center space-y-1">
                                <p class="text-xs text-[#6F6B68]">No concrete steps added yet.</p>
                                <p class="text-[11px] text-[#8E8A85]">Add a first action below, or click <button type="button" onclick="window.TempoEmergencyFlow.toggleAiHelp()" class="text-[#FF6B2C] font-bold hover:underline">✨ AI Help</button> for ideas.</p>
                            </div>
                        ` : task.subtasks.map((step, sIdx) => `
                            <div class="p-3 bg-[#FFFDFB] border border-[#EAE4DF] rounded-xl flex items-center justify-between gap-3 text-xs">
                                <div class="flex items-center space-x-2.5 flex-1 min-w-0">
                                    <span class="w-5 h-5 rounded-full bg-[#FFE9DC] text-[#B83D08] font-bold text-[10px] flex items-center justify-center shrink-0">
                                        ${sIdx + 1}
                                    </span>
                                    <span class="font-medium text-[#202124] truncate">${escapeHTML(step.title)}</span>
                                </div>

                                <div class="flex items-center space-x-2 shrink-0">
                                    ${showSubtaskDurations ? (
                                        step.durationMinutes && step.durationMinutes > 0 ? `
                                            <button type="button" 
                                                    onclick="window.TempoEmergencyFlow.openSubtaskDurationEditor(${sIdx})"
                                                    class="text-[11px] font-bold text-stone-700 bg-stone-100 hover:bg-[#FFE9DC] hover:text-[#B83D08] px-2.5 py-1 rounded-lg border border-stone-200 hover:border-[#FF6B2C]/40 transition flex items-center space-x-1"
                                                    title="Click to edit estimate for this step">
                                                <span>${formatSubtaskDurationDisplay(step.durationMinutes)}</span>
                                            </button>
                                        ` : `
                                            <button type="button" 
                                                    onclick="window.TempoEmergencyFlow.openSubtaskDurationEditor(${sIdx})"
                                                    class="text-[11px] font-semibold text-[#FF6B2C] hover:text-[#B83D08] bg-[#FFF8F2] hover:bg-[#FFE9DC] border border-dashed border-[#FF6B2C]/50 px-2.5 py-1 rounded-lg transition flex items-center space-x-1"
                                                    title="Click to add time estimate for this step">
                                                + Add time
                                            </button>
                                        `
                                    ) : ''}

                                    <button onclick="window.TempoEmergencyFlow.moveSubtask(${sIdx}, -1)" ${sIdx === 0 ? 'disabled class="opacity-20"' : 'class="hover:bg-stone-100 rounded px-1"'} title="Move step up">▲</button>
                                    <button onclick="window.TempoEmergencyFlow.moveSubtask(${sIdx}, 1)" ${sIdx === task.subtasks.length - 1 ? 'disabled class="opacity-20"' : 'class="hover:bg-stone-100 rounded px-1"'} title="Move step down">▼</button>
                                    <button onclick="window.TempoEmergencyFlow.removeSubtask(${sIdx})" class="text-gray-400 hover:text-rose-600 px-1" title="Remove step">✕</button>
                                </div>
                            </div>
                        `).join('')}
                    </div>

                    <!-- Add Step Input -->
                    <div class="pt-2 flex flex-col sm:flex-row items-center gap-2">
                        <input id="em-new-step-title" type="text" placeholder="Add next small action..."
                               onkeydown="if(event.key === 'Enter') window.TempoEmergencyFlow.addSubtask()"
                               class="w-full px-3 py-2 text-xs border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-[#FF6B2C] bg-[#FFFDFB]">
                        ${showSubtaskDurations ? `
                            <input id="em-new-step-duration" type="number" min="5" step="5" placeholder="Mins (opt)"
                                   onkeydown="if(event.key === 'Enter') window.TempoEmergencyFlow.addSubtask()"
                                   class="w-24 px-2 py-2 text-xs border border-gray-200 rounded-xl text-center bg-white">
                        ` : ''}
                        <button onclick="window.TempoEmergencyFlow.addSubtask()" 
                                class="btn-primary w-full sm:w-auto px-4 py-2 rounded-xl text-xs font-bold shrink-0">
                            + Add step
                        </button>
                    </div>

                    <!-- Footer Helper / "I Already Know" Action -->
                    <div class="flex items-center justify-between pt-1 border-t border-gray-100/60 text-xs flex-wrap gap-2">
                        <span class="text-[11px] text-[#8E8A85]">Subtask estimates are optional and always editable.</span>
                        ${!task.alreadyKnowWhatToDo ? `
                            <button type="button" 
                                    onclick="window.TempoEmergencyFlow.toggleAlreadyKnowWhatToDo(true)" 
                                    class="text-[11px] font-semibold text-[#6F6B68] hover:text-[#202124] transition py-0.5 px-2 rounded-lg hover:bg-stone-100 flex items-center space-x-1"
                                    title="Indicate that you already know what to do without extra breakdown">
                                <span>✓</span>
                                <span>I already know what to do</span>
                            </button>
                        ` : `
                            <span class="text-[11px] font-bold text-emerald-700 flex items-center space-x-1">
                                <span>✓</span>
                                <span>No further breakdown needed</span>
                            </span>
                        `}
                    </div>
                </div>

                <!-- Post-Breakdown Action Decision / Bottom Navigation Card -->
                <div class="p-5 bg-white border border-[#EAE4DF] rounded-[22px] space-y-3 shadow-sm text-center">
                    <div class="space-y-1">
                        <h4 class="font-heading text-sm font-bold text-[#202124]">
                            ${task.subtasks.length > 0 || task.alreadyKnowWhatToDo ? `✨ "${escapeHTML(task.name)}" is ready to execute.` : `Ready to finish "${escapeHTML(task.name)}"?`}
                        </h4>
                        <p class="text-xs text-[#6F6B68]">
                            ${breakdownIndex < confirmedPlan.plannedTasks.length - 1 
                                ? 'Save your plan whenever you\'re ready, or break down the next task.' 
                                : 'All tasks are organized. Save your plan to finish setup and choose what to do next.'}
                        </p>
                    </div>

                    <div class="pt-2 flex flex-wrap items-center justify-center gap-3">
                        ${breakdownIndex > 0 ? `
                            <button onclick="window.TempoEmergencyFlow.breakdownPreviousTask()" 
                                    class="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                                ← Previous task
                            </button>
                        ` : ''}
                        <button id="btn-em-save-plan" onclick="window.TempoEmergencyFlow.savePlan()" 
                                class="btn-primary w-full sm:w-auto px-7 py-3 rounded-xl font-bold text-xs sm:text-sm shadow-md transition flex items-center justify-center space-x-2">
                            <span>Save Emergency Plan →</span>
                        </button>
                        ${breakdownIndex < confirmedPlan.plannedTasks.length - 1 ? `
                            <button onclick="window.TempoEmergencyFlow.breakdownNextTask()" 
                                    class="w-full sm:w-auto px-5 py-3 rounded-xl border border-[#FF6B2C] text-[#FF6B2C] hover:bg-[#FFE9DC] text-xs font-bold transition">
                                Break down next task →
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>

            <!-- Subtask Duration Editor Modal (if active) -->
            ${renderSubtaskDurationEditorModal()}
        `;
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

    function addSubtask() {
        const titleInput = document.getElementById('em-new-step-title');
        const durInput = document.getElementById('em-new-step-duration');

        const title = titleInput ? titleInput.value.trim() : '';
        if (!title) return;

        const dur = durInput && durInput.value ? parseInt(durInput.value, 10) || null : null;

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

    function moveSubtask(sIdx, dir) {
        const planItem = confirmedPlan && confirmedPlan.plannedTasks ? confirmedPlan.plannedTasks[breakdownIndex] : null;
        if (!planItem) return;
        const target = sIdx + dir;
        if (target < 0 || target >= planItem.task.subtasks.length) return;

        const temp = planItem.task.subtasks[sIdx];
        planItem.task.subtasks[sIdx] = planItem.task.subtasks[target];
        planItem.task.subtasks[target] = temp;
        editingSubtaskIndex = null;
        renderBreakdown();
        scheduleDraftAutosave();
        if (window.TempoPlanStore && confirmedPlan) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }
    }

    function toggleSubtaskDurations() {
        showSubtaskDurations = !showSubtaskDurations;
        renderBreakdown();
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
        if (confirmedPlan && confirmedPlan.plannedTasks && breakdownIndex < confirmedPlan.plannedTasks.length - 1) {
            breakdownIndex++;
            showAiSuggestions = false;
            currentAiSuggestions = [];
            aiSuggestionError = false;
            renderBreakdown();
            scheduleDraftAutosave(true);
        } else {
            savePlan();
        }
    }

    function breakdownPreviousTask() {
        if (breakdownIndex > 0) {
            breakdownIndex--;
            showAiSuggestions = false;
            currentAiSuggestions = [];
            aiSuggestionError = false;
            renderBreakdown();
            scheduleDraftAutosave(true);
        }
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
                window.TempoApp.showToast("All tasks in this Emergency Plan are completed! Great job.");
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
        viewingFromHandoff = true;
        goToStage('plan-review');
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

        const saveBtn = document.getElementById('btn-em-save-plan');
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
                window.TempoApp.showToast("Emergency Plan saved successfully.");
            }

            goToStage('handoff');
        } catch (err) {
            console.error("[TempoEmergencyFlow] Failed to save active plan:", err);
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = origBtnText;
            }
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Could not save plan right now. Please try again.");
            } else {
                alert("Could not save plan right now. Please check your connection and try again.");
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

        // Ensure active plan is completely saved in durable storage
        if (window.TempoPlanStore) {
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
        }

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
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">EMERGENCY PLAN READY</span>
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
                                Estimated duration: ~${focusTask.durationLabel || 'Flexible'} • Due: ${focusTask.hasDeadline ? formatHumanDeadline(focusTask.deadlineDate, focusTask.deadlineTime) : 'No fixed deadline'}
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
                            You've completed every task in this Emergency Plan. Take a moment to acknowledge your hard work.
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
                        View / Edit Emergency Plan
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

    function formatDurationMinutes(mins) {
        if (!mins || mins <= 0) return '0m';
        if (mins < 60) return `${mins}m`;
        const h = Math.floor(mins / 60);
        const m = mins % 60;
        return m > 0 ? `${h}h ${m}m` : `${h}h`;
    }

    function formatMinutesToHHMM(mins) {
        const h = Math.floor(mins / 60) % 24;
        const m = mins % 60;
        return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
    }

    function formatHumanDeadline(dateStr, timeStr) {
        if (!dateStr) return 'No fixed deadline';
        try {
            const date = new Date(`${dateStr}T${timeStr || '23:59'}`);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + (timeStr ? ` at ${timeStr}` : '');
        } catch (e) {
            return `${dateStr} ${timeStr || ''}`;
        }
    }

    function calculateRelativeDueText(dateStr, timeStr) {
        if (!dateStr) return 'No fixed deadline';
        try {
            const target = new Date(`${dateStr}T${timeStr || '23:59'}`);
            const now = new Date();
            const diffMs = target - now;
            const diffHours = Math.round(diffMs / (1000 * 60 * 60));

            if (diffHours < 0) return 'Deadline passed';
            if (diffHours <= 12) return `Due in ${diffHours} hour${diffHours === 1 ? '' : 's'}`;
            if (diffHours <= 24) return `Due tonight / tomorrow morning`;
            const diffDays = Math.ceil(diffHours / 24);
            if (diffDays === 1) return `Due tomorrow`;
            return `Due in ${diffDays} days`;
        } catch (e) {
            return `Due ${dateStr}`;
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
        return confirmedPlan;
    }

    function getAvailabilityDays() {
        return availabilityDays;
    }

    function toggleTaskCompleted(taskId) {
        let task = tasks.find(t => t.id === taskId);
        if (!task && confirmedPlan && confirmedPlan.plannedTasks) {
            const item = confirmedPlan.plannedTasks.find(pt => pt.task.id === taskId);
            if (item) task = item.task;
        }
        if (task) {
            task.completed = !task.completed;
            if (task.completed) {
                task.isInProgress = false;
            }
            if (window.TempoPlanStore) {
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

    function setTaskInProgress(taskId, inProgress = true) {
        let task = tasks.find(t => t.id === taskId);
        if (!task && confirmedPlan && confirmedPlan.plannedTasks) {
            const item = confirmedPlan.plannedTasks.find(pt => pt.task.id === taskId);
            if (item) task = item.task;
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
        getAvailabilityDays,
        toggleTaskCompleted,
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
        // Plan Review & Editing
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
        confirmPlanAndProceed,
        // Breakdown
        generateSuggestedSteps,
        startCustomBreakdown,
        skipBreakdownForCurrentTask,
        addSubtask,
        removeSubtask,
        moveSubtask,
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
        clearSubtaskDuration
    };
})();
