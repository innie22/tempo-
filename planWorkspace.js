/**
 * Tempo Shared Plan Workspace (MVP)
 * File: planWorkspace.js
 * 
 * Post-setup View & Edit Plan experience for an existing saved Emergency Plan.
 * Operates directly on the shared active plan and tasks without recreating or cloning.
 */

window.TempoPlanWorkspace = (function() {
    let selectedTaskId = null;
    let isEditingDeadline = false;
    let showAddSubtaskInput = false;
    let activeModal = null; // null | 'add-task' | 'fit-task-prompt' | 'adjust-availability' | 'reschedule' | 'deadline-plan-reorder-confirm' | 'edit-task-note'
    let pendingAddedTask = null;
    let rescheduleTaskId = null;
    let rescheduleSelectedWindow = null;
    let rescheduleShowAddTime = false;
    let adjustAvailShowAdd = false;
    let pendingClearTaskId = null;
    let isActionProcessing = false;
    let activeLabelMenuTaskId = null;
    let pendingDeadlineEdit = null;
    let pendingNoteTaskId = null;

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

    // Helper: Format minutes into human-readable duration
    function formatDuration(mins) {
        if (!mins || mins <= 0) return '0m';
        const h = Math.floor(mins / 60);
        const m = mins % 60;
        if (h > 0 && m > 0) return `${h}h ${m}m`;
        if (h > 0) return `${h}h`;
        return `${m}m`;
    }

    // Helper: 12-hour format
    function formatTime12H(timeStr) {
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

    // Helper: Parse HH:MM to minutes
    function parseTimeToMinutes(str) {
        if (!str || typeof str !== 'string') return 0;
        const parts = str.split(':');
        return (parseInt(parts[0], 10) || 0) * 60 + (parseInt(parts[1], 10) || 0);
    }

    // Helper: Format minutes to HH:MM (24-hour)
    function formatMinutesToTimeString(min) {
        const h = Math.floor(min / 60);
        const m = min % 60;
        return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
    }

    // Helper: Format Month Day (e.g. Oct 17)
    function formatMonthDay(dateStr) {
        if (!dateStr) return '';
        try {
            const clean = dateStr.split('T')[0];
            const parts = clean.split('-');
            if (parts.length === 3) {
                const date = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }
        } catch(e) {}
        return dateStr;
    }

    // Helper: Human deadline
    function formatDeadline(dateStr, timeStr) {
        if (window.TempoI18n && typeof window.TempoI18n.formatDeadline === 'function') {
            return window.TempoI18n.formatDeadline(dateStr, timeStr);
        }
        if (!dateStr) return 'No fixed deadline';
        if (dateStr.includes(' ') && !timeStr) {
            const parts = dateStr.split(' ');
            dateStr = parts[0];
            timeStr = parts[1];
        }
        try {
            const [y, m, d] = dateStr.split('-').map(Number);
            const date = new Date(y, m - 1, d);
            const monthDay = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            if (timeStr) {
                return `${monthDay} · ${formatTime12H(timeStr)}`;
            }
            return monthDay;
        } catch (e) {
            return `${dateStr}${timeStr ? ' · ' + timeStr : ''}`;
        }
    }

    // Helper: Today ISO string YYYY-MM-DD
    function getTodayISO() {
        return new Date().toISOString().split('T')[0];
    }

        // Reference plan generator matching the UI specification
    function getDefaultReferencePlan() {
        const todayStr = getTodayISO();
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const tomorrowStr = tomorrow.toISOString().split('T')[0];

        const defaultPlan = {
            id: 'plan_tempo_working_default',
            planId: 'plan_tempo_working_default',
            planType: 'emergency',
            title: 'Tempo Working Plan',
            plannedTasks: [
                {
                    dayDate: todayStr,
                    dayLabel: 'Today, Month day',
                    startTime: '3:00 PM',
                    endTime: '5:30 PM',
                    executionBadge: 'Now',
                    task: {
                        id: 'task-marketing-research',
                        name: 'Marketing Research',
                        hasDeadline: true,
                        deadlineDate: '2026-10-17',
                        deadlineTime: '21:00',
                        deadline: '2026-10-17 21:00',
                        durationMinutes: 150,
                        durationLabel: '2h 30m',
                        completed: false,
                        isInProgress: true,
                        description: 'Create a sheet to manage references',
                        subtasks: [
                            { id: 'sub-1', title: 'Subtask 1: Outline', completed: false, durationMinutes: 30 },
                            { id: 'sub-2', title: 'Subtask 2: Literature Review', completed: false, durationMinutes: 45 },
                            { id: 'sub-3', title: 'Subtask 3: Research Gap', completed: false, durationMinutes: 30 },
                            { id: 'sub-4', title: 'Subtask 4: Methodology', completed: false, durationMinutes: 20 },
                            { id: 'sub-5', title: 'Subtask 5: Data Analysis', completed: false, durationMinutes: 15 },
                            { id: 'sub-6', title: 'Subtask 6: Summary Report', completed: false, durationMinutes: 10 }
                        ]
                    }
                },
                {
                    dayDate: todayStr,
                    dayLabel: 'Today, Month day',
                    startTime: '3:00 PM',
                    endTime: '5:30 PM',
                    executionBadge: 'Later',
                    task: {
                        id: 'task-event-proposal',
                        name: 'Event Proposal',
                        hasDeadline: true,
                        deadlineDate: '2026-10-18',
                        deadlineTime: '22:00',
                        deadline: '2026-10-18 22:00',
                        durationMinutes: 150,
                        durationLabel: '2h 30m',
                        completed: false,
                        isInProgress: false,
                        description: 'Coordinate with design team for event collateral',
                        subtasks: [
                            { id: 'sub-ep-1', title: 'Subtask 1: Budget Draft', completed: false, durationMinutes: 45 },
                            { id: 'sub-ep-2', title: 'Subtask 2: Venue Options', completed: false, durationMinutes: 60 },
                            { id: 'sub-ep-3', title: 'Subtask 3: Guest List', completed: false, durationMinutes: 45 }
                        ]
                    }
                },
                {
                    dayDate: tomorrowStr,
                    dayLabel: 'Month Day',
                    startTime: '9:00 AM',
                    endTime: '11:30 AM',
                    executionBadge: 'Later',
                    task: {
                        id: 'task-edit-video',
                        name: 'Edit Video',
                        hasDeadline: true,
                        deadlineDate: '2026-10-20',
                        deadlineTime: '22:00',
                        deadline: '2026-10-20 22:00',
                        durationMinutes: 150,
                        durationLabel: '2h 30m',
                        completed: false,
                        isInProgress: false,
                        description: 'Export in 1080p format for social channels',
                        subtasks: []
                    }
                }
            ],
            unarrangedTasks: [
                {
                    id: 'task-client-sync',
                    name: 'Client Follow-up',
                    hasDeadline: false,
                    durationMinutes: 60,
                    durationLabel: '1h',
                    completed: false,
                    subtasks: []
                },
                {
                    id: 'task-deck-review',
                    name: 'Review Pitch Deck',
                    hasDeadline: false,
                    durationMinutes: 45,
                    durationLabel: '45m',
                    completed: false,
                    subtasks: []
                },
                {
                    id: 'task-team-catchup',
                    name: 'Team Sync & Retrospective',
                    hasDeadline: false,
                    durationMinutes: 30,
                    durationLabel: '30m',
                    completed: false,
                    subtasks: []
                }
            ],
            tasks: []
        };
        defaultPlan.tasks = [
            ...defaultPlan.plannedTasks.map(pt => pt.task),
            ...defaultPlan.unarrangedTasks
        ];
        return defaultPlan;
    }

    // Load active plan from TempoPlanStore, TempoEmergencyFlow, or local storage
    function getActivePlan() {
        let plan = null;
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            plan = window.TempoEmergencyFlow.getConfirmedPlan();
        }
        if (!plan && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            plan = window.TempoPlanStore.getActivePlan('emergency') || window.TempoPlanStore.getActivePlan('recovery') || window.TempoPlanStore.getActivePlan('default');
        }
        if (!plan) {
            try {
                const saved = localStorage.getItem('tempo_working_plan') || localStorage.getItem('tempo_store_active_emergency_guest');
                if (saved) plan = JSON.parse(saved);
            } catch(e) {}
        }
        if (plan) {
            if (!Array.isArray(plan.plannedTasks)) plan.plannedTasks = [];
            if (!Array.isArray(plan.unarrangedTasks)) plan.unarrangedTasks = [];
            if (!Array.isArray(plan.tasks)) plan.tasks = [];
        }
        if (!plan || (plan.plannedTasks.length === 0 && plan.unarrangedTasks.length === 0 && plan.tasks.length === 0)) {
            plan = getDefaultReferencePlan();
        }
        return plan;
    }

    // Save active plan to TempoPlanStore & localStorage
    function persistPlan(plan) {
        if (!plan) return;
        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            window.TempoPlanStore.saveActivePlan('emergency', plan);
            window.TempoPlanStore.saveActivePlan('recovery', plan);
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
            window.TempoEmergencyFlow.setConfirmedPlan(plan);
        }
        try {
            localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
        } catch(e) {}
        if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
            window.TempoMode.renderActiveModeHome();
        }
    }

    /**
     * AI Planner: Reorganize and fit tasks into schedule based on priorities and deadlines
     */
    function reorganizePlanWithPlanner(plan) {
        if (!plan || !Array.isArray(plan.plannedTasks)) return;

        // Separate completed vs active planned tasks
        const completedItems = plan.plannedTasks.filter(item => item.task && item.task.completed);
        const activeItems = plan.plannedTasks.filter(item => !item.task || !item.task.completed);

        // Sort active tasks:
        // 1. Now tasks (rank 1) before Later tasks (rank 3)
        // 2. Within same rank: sort by deadline urgency (earlier deadline first)
        activeItems.sort((aItem, bItem) => {
            const a = aItem.task || {};
            const b = bItem.task || {};
            const isNowA = a.userLabel === 'Now' || a.priorityCategory === 'DO_FIRST';
            const isNowB = b.userLabel === 'Now' || b.priorityCategory === 'DO_FIRST';
            const isLaterA = a.userLabel === 'Later' || a.priorityCategory === 'LATER';
            const isLaterB = b.userLabel === 'Later' || b.priorityCategory === 'LATER';
            const rankA = isNowA ? 1 : (isLaterA ? 3 : 2);
            const rankB = isNowB ? 1 : (isLaterB ? 3 : 2);

            if (rankA !== rankB) return rankA - rankB;

            const hasDeadA = !!(a.hasDeadline && a.deadlineDate);
            const hasDeadB = !!(b.hasDeadline && b.deadlineDate);
            if (hasDeadA && hasDeadB) {
                const cmp = (a.deadlineDate + (a.deadlineTime || '23:59')).localeCompare(b.deadlineDate + (b.deadlineTime || '23:59'));
                if (cmp !== 0) return cmp;
            } else if (hasDeadA && !hasDeadB) {
                return -1;
            } else if (!hasDeadA && hasDeadB) {
                return 1;
            }
            return 0;
        });

        // Sequential slot allocation based on available days
        let availabilityDays = null;
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getAvailabilityDays === 'function') {
            availabilityDays = window.TempoEmergencyFlow.getAvailabilityDays();
        }
        const activeDays = (availabilityDays || []).filter(d => !d.isUnavailable && d.blocks && d.blocks.length > 0);

        if (activeDays.length > 0) {
            const slots = [];
            activeDays.forEach(day => {
                const intervals = (day.blocks || [])
                    .map(b => ({
                        start: parseTimeToMinutes(b.start),
                        end: parseTimeToMinutes(b.end)
                    }))
                    .filter(intv => intv.end > intv.start)
                    .sort((x, y) => x.start - y.start);

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
                    slots.push({
                        dayDate: day.date,
                        dayLabel: day.label,
                        startMin: slot.start,
                        endMin: slot.end,
                        remainingMin: slot.end - slot.start
                    });
                });
            });

            let currentSlotIdx = 0;
            activeItems.forEach((item, idx) => {
                const task = item.task || {};
                const neededMin = task.durationMinutes || 60;
                let allocated = false;

                while (currentSlotIdx < slots.length) {
                    const slot = slots[currentSlotIdx];
                    if (slot.remainingMin >= 15) {
                        const startMinutes = slot.endMin - slot.remainingMin;
                        const durationToUse = Math.min(neededMin, slot.remainingMin);
                        const endMinutes = startMinutes + durationToUse;
                        slot.remainingMin -= durationToUse;

                        item.dayDate = slot.dayDate;
                        item.dayLabel = slot.dayLabel;
                        item.startMin = startMinutes;
                        item.endMin = endMinutes;
                        item.startTime = formatMinutesToTimeString(startMinutes);
                        item.endTime = formatMinutesToTimeString(endMinutes);
                        item.isOverCapacity = false;
                        item.executionBadge = (idx === 0 || task.userLabel === 'Now') ? 'Now' : 'Later';

                        allocated = true;
                        if (slot.remainingMin < 15) currentSlotIdx++;
                        break;
                    } else {
                        currentSlotIdx++;
                    }
                }

                if (!allocated) {
                    const fallbackDay = activeDays[activeDays.length - 1] || activeDays[0];
                    item.dayDate = fallbackDay ? fallbackDay.date : item.dayDate;
                    item.dayLabel = fallbackDay ? fallbackDay.label : item.dayLabel;
                    item.executionBadge = task.userLabel === 'Now' ? 'Now' : 'Later';
                }
            });
        } else {
            activeItems.forEach((item, idx) => {
                const task = item.task || {};
                item.executionBadge = (idx === 0 || task.userLabel === 'Now') ? 'Now' : 'Later';
            });
        }

        plan.plannedTasks = [...activeItems, ...completedItems];

        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
            window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
        }

        persistPlan(plan);

        if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
            window.TempoMode.renderActiveModeHome();
        }
    }

    /**
     * Resolve default task for Global "Start Focus Now" (Section 7)
     * Hierarchy:
     * 1. If an unfinished task is currently IN PROGRESS: suggest that task.
     * 2. Otherwise: suggest first unfinished ARRANGED task in current execution order for today.
     * 3. Do NOT automatically pull an UNARRANGED task.
     * 4. If no appropriate task planned for today: return null (do not push future task automatically).
     */
    function resolveDefaultFocusTask(plan) {
        if (!plan || !plan.plannedTasks || plan.plannedTasks.length === 0) return null;

        const todayStr = getTodayISO();

        // 1. Unfinished task in progress
        const inProgressItem = plan.plannedTasks.find(pt => pt.task && pt.task.isInProgress && !pt.task.completed);
        if (inProgressItem) return inProgressItem.task;

        // 2. First unfinished arranged task planned for today
        const todayTasks = plan.plannedTasks.filter(pt => pt.dayDate === todayStr && pt.task && !pt.task.completed);
        if (todayTasks.length > 0) {
            return todayTasks[0].task;
        }

        // 4. No task planned today -> do not push future task automatically
        return null;
    }

        /**
     * Navigation: Return to Home
     */
    function navigateHome() {
        document.body.style.backgroundColor = '';
        const mainEl = document.querySelector('main');
        if (mainEl) mainEl.style.backgroundColor = '';
        if (window.TempoMode && typeof window.TempoMode.syncModeDOM === 'function') {
            window.TempoMode.syncModeDOM(window.TempoMode.getMode());
        }
        if (window.TempoMode && typeof window.TempoMode.navigateToActiveDashboard === 'function') {
            window.TempoMode.navigateToActiveDashboard();
        } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('today');
        } else {
            window.location.hash = '#today';
        }
    }

    /**
     * Start Adjust Plan flow
     */
    function startAdjustPlan() {
        if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.startAdjustmentFlow === 'function') {
            window.TempoUrmodeFlow.startAdjustmentFlow();
        } else if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.openPlanReviewModal === 'function') {
            window.TempoEmergencyFlow.openPlanReviewModal();
        } else {
            openAdjustAvailabilityModal();
        }
    }

    /**
     * Delete active plan
     */
    function promptDeletePlan() {
        activeModal = 'delete-plan-confirm';
        render();
    }

    function closeDeletePlanConfirm() {
        if (isActionProcessing) return;
        activeModal = null;
        render();
    }

    function executeDeletePlan() {
        if (isActionProcessing) return;
        isActionProcessing = true;

        try {
            if (window.TempoPlanStore && typeof window.TempoPlanStore.archiveActivePlan === 'function') {
                window.TempoPlanStore.archiveActivePlan('emergency');
                window.TempoPlanStore.archiveActivePlan('recovery');
                window.TempoPlanStore.archiveActivePlan('default');
            }

            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.resetFlowState === 'function') {
                window.TempoEmergencyFlow.resetFlowState();
            }

            try {
                localStorage.removeItem('tempo_working_plan');
                localStorage.removeItem('tempo_active_plan');
                localStorage.removeItem('tempo_store_active_emergency_guest');
            } catch(e) {}

            activeModal = null;

            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Your Working Plan has been deleted.");
            }

            navigateHome();
        } finally {
            isActionProcessing = false;
        }
    }

    function deletePlan() {
        promptDeletePlan();
    }

    /**
     * Open Workspace
     */
    function open() {
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('plan-workspace');
        } else {
            window.location.hash = '#plan-workspace';
        }
        render();
    }

    /**
     * Global Start Focus Now
     */
    function startGlobalFocus() {
        const plan = getActivePlan();
        const defaultTask = resolveDefaultFocusTask(plan);

        if (defaultTask && window.TempoFocusZone) {
            window.TempoFocusZone.open({ taskId: defaultTask.id });
        } else if (window.TempoFocusZone) {
            // No task planned for today -> open quick entry allowing choice or focus without task
            window.TempoFocusZone.openQuickEntry();
        }
    }

    /**
     * Start Focus for a specific task
     */
    function startTaskFocus(taskId) {
        if (window.TempoFocusZone) {
            window.TempoFocusZone.open({ taskId: taskId });
        }
    }

        /**
     * Toggle task completion on shared task
     */
    function toggleTaskComplete(taskId, e) {
        if (e && e.stopPropagation) e.stopPropagation();
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        let pt = plan.plannedTasks ? plan.plannedTasks.find(item => item.task && item.task.id === taskId) : null;
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => (t.task ? t.task.id === taskId : t.id === taskId));
            if (task && task.task) task = task.task;
        }

        if (task) {
            task.completed = !task.completed;
            if (task.completed) {
                task.isInProgress = false;
                task.executionStatus = 'completed';
                task.completedAt = Date.now();

                // If the selected task became completed, select the next appropriate active task
                if (selectedTaskId === taskId) {
                    const allActive = [];
                    if (Array.isArray(plan.plannedTasks)) {
                        plan.plannedTasks.forEach(item => {
                            if (item.task && !item.task.completed && item.task.id !== taskId) {
                                allActive.push(item.task);
                            }
                        });
                    }
                    if (Array.isArray(plan.unarrangedTasks)) {
                        plan.unarrangedTasks.forEach(u => {
                            const t = u.task ? u.task : u;
                            if (t && !t.completed && t.id !== taskId) {
                                allActive.push(t);
                            }
                        });
                    }
                    if (allActive.length > 0) {
                        selectedTaskId = allActive[0].id;
                    }
                }
            } else {
                task.executionStatus = 'pending';
                delete task.completedAt;
                selectedTaskId = taskId;
            }

            // Sync with TempoEmergencyFlow explicitly
            if (window.TempoEmergencyFlow) {
                if (typeof window.TempoEmergencyFlow.setTaskCompleted === 'function') {
                    window.TempoEmergencyFlow.setTaskCompleted(taskId, task.completed);
                } else if (typeof window.TempoEmergencyFlow.toggleTaskCompleted === 'function') {
                    const cur = (window.TempoEmergencyFlow.isTaskCompleted && window.TempoEmergencyFlow.isTaskCompleted(taskId));
                    if (cur !== task.completed) {
                        window.TempoEmergencyFlow.toggleTaskCompleted(taskId);
                    }
                }
            }

            // Sync with planStore
            if (window.TempoPlanStore && typeof window.TempoPlanStore.updateTaskState === 'function') {
                window.TempoPlanStore.updateTaskState(taskId, {
                    completed: task.completed,
                    isInProgress: task.isInProgress,
                    executionStatus: task.executionStatus
                });
            }

            // Sync mock state for Rmode if applicable
            try {
                let mockTasks = {};
                try {
                    mockTasks = JSON.parse(localStorage.getItem('tempo_rmode_mock_tasks') || '{}');
                } catch(e) {}
                if (taskId === 'task-marketing-research') mockTasks['rmode-mock-1'] = task.completed;
                if (taskId === 'task-event-proposal') mockTasks['rmode-mock-2'] = task.completed;
                if (taskId === 'task-edit-video') mockTasks['rmode-mock-3'] = task.completed;
                mockTasks[taskId] = task.completed;
                localStorage.setItem('tempo_rmode_mock_tasks', JSON.stringify(mockTasks));
            } catch(e) {}

            persistPlan(plan);
            render();

            if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
                window.TempoMode.renderActiveModeHome();
            }
        }
    }

    /**
     * Select a task to view/edit in the Detail Drawer
     */
    function selectTask(taskId) {
        selectedTaskId = taskId;
        isEditingDeadline = false;
        render();
    }

    /**
     * Close the Detail Drawer
     */
    function closeDrawer() {
        selectedTaskId = null;
        isEditingDeadline = false;
        render();
    }

    /**
     * Inline Deadline Edit toggle
     */
    function toggleDeadlineEdit() {
        isEditingDeadline = !isEditingDeadline;
        render();
    }

    /**
     * Save inline deadline edit
     */
    function saveDeadlineEdit(taskId) {
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        let ptItem = null;
        ptItem = (plan.plannedTasks || []).find(item => item.task && item.task.id === taskId);
        if (ptItem) task = ptItem.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }
        if (!task) return;

        const dateInput = document.getElementById('pw-edit-deadline-date');
        const timeInput = document.getElementById('pw-edit-deadline-time');
        const noFixedCheck = document.getElementById('pw-edit-no-deadline');

        const hasNoFixed = noFixedCheck ? noFixedCheck.checked : false;
        const dateVal = dateInput ? dateInput.value : '';
        const timeVal = timeInput ? timeInput.value : '';

        const hasDeadline = !hasNoFixed && !!dateVal;
        const newDate = hasNoFixed ? null : (dateVal || null);
        const newTime = hasNoFixed ? null : (timeVal || '23:59');

        const oldDate = task.deadlineDate;
        const oldTime = task.deadlineTime || '23:59';
        const oldHasDeadline = !!task.hasDeadline;

        if (hasDeadline === oldHasDeadline && newDate === oldDate && newTime === oldTime) {
            isEditingDeadline = false;
            render();
            return;
        }

        // Check if new deadline creates a conflict or alters relative priority/urgency of tasks
        let createsConflict = false;
        if (ptItem && hasDeadline && newDate) {
            if (ptItem.dayDate && ptItem.dayDate > newDate) {
                createsConflict = true;
            } else if (ptItem.dayDate && ptItem.dayDate === newDate && ptItem.endTime && ptItem.endTime > newTime) {
                createsConflict = true;
            }
        }

        let altersPriorityOrder = false;
        const activeTasks = (plan.plannedTasks || [])
            .filter(item => item.task && !item.task.completed)
            .map(item => item.task);

        const currentIdx = activeTasks.findIndex(t => t.id === taskId);
        if (currentIdx !== -1 && hasDeadline && newDate) {
            const newDeadlineStr = newDate + ' ' + newTime;
            // Check if there is any task scheduled before current task that now has a later deadline
            for (let i = 0; i < currentIdx; i++) {
                const beforeTask = activeTasks[i];
                if (beforeTask.hasDeadline && beforeTask.deadlineDate) {
                    const beforeDeadlineStr = beforeTask.deadlineDate + ' ' + (beforeTask.deadlineTime || '23:59');
                    if (newDeadlineStr < beforeDeadlineStr) {
                        altersPriorityOrder = true;
                        break;
                    }
                } else if (!beforeTask.hasDeadline) {
                    altersPriorityOrder = true;
                    break;
                }
            }
            if (!altersPriorityOrder) {
                for (let i = currentIdx + 1; i < activeTasks.length; i++) {
                    const afterTask = activeTasks[i];
                    if (afterTask.hasDeadline && afterTask.deadlineDate) {
                        const afterDeadlineStr = afterTask.deadlineDate + ' ' + (afterTask.deadlineTime || '23:59');
                        if (newDeadlineStr > afterDeadlineStr) {
                            altersPriorityOrder = true;
                            break;
                        }
                    }
                }
            }
        }

        if (createsConflict || altersPriorityOrder) {
            pendingDeadlineEdit = {
                taskId: taskId,
                hasDeadline: hasDeadline,
                deadlineDate: newDate,
                deadlineTime: newTime
            };
            activeModal = 'deadline-plan-reorder-confirm';
            render();
            return;
        }

        // Save directly if no material conflict
        applyDeadlineChange(taskId, hasDeadline, newDate, newTime, false);
    }

    function confirmDeadlineWithReorder() {
        if (!pendingDeadlineEdit) return;
        applyDeadlineChange(pendingDeadlineEdit.taskId, pendingDeadlineEdit.hasDeadline, pendingDeadlineEdit.deadlineDate, pendingDeadlineEdit.deadlineTime, true);
    }

    function confirmDeadlineWithoutReorder() {
        if (!pendingDeadlineEdit) return;
        applyDeadlineChange(pendingDeadlineEdit.taskId, pendingDeadlineEdit.hasDeadline, pendingDeadlineEdit.deadlineDate, pendingDeadlineEdit.deadlineTime, false);
    }

    function cancelDeadlineConfirm() {
        pendingDeadlineEdit = null;
        activeModal = null;
        render();
    }

    function applyDeadlineChange(taskId, hasDeadline, newDate, newTime, shouldReorder) {
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        const pt = (plan.plannedTasks || []).find(item => item.task && item.task.id === taskId);
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }
        if (!task) return;

        task.hasDeadline = hasDeadline;
        task.deadlineDate = newDate;
        task.deadlineTime = newTime;
        task.deadline = hasDeadline ? `${newDate} ${newTime || '23:59'}` : null;

        // Update shared task in tasks array
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getTasks === 'function') {
            const rawTasks = window.TempoEmergencyFlow.getTasks();
            const shared = rawTasks.find(t => t.id === taskId);
            if (shared) {
                shared.hasDeadline = task.hasDeadline;
                shared.deadlineDate = task.deadlineDate;
                shared.deadlineTime = task.deadlineTime;
                shared.deadline = task.deadline;
            }
        }

        if (shouldReorder) {
            reorganizePlanWithPlanner(plan);
        } else {
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
                window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
            }
            persistPlan(plan);
            if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
                window.TempoMode.renderActiveModeHome();
            }
        }

        isEditingDeadline = false;
        pendingDeadlineEdit = null;
        activeModal = null;
        render();
    }

    /**
     * Label (Now / Later) dropdown and AI replan
     */
    function toggleLabelMenu(taskId, event) {
        if (event) {
            event.stopPropagation();
        }
        activeLabelMenuTaskId = (activeLabelMenuTaskId === taskId ? null : taskId);
        render();
    }

    function setTaskLabel(taskId, newLabel) {
        activeLabelMenuTaskId = null;
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        const pt = (plan.plannedTasks || []).find(item => item.task && item.task.id === taskId);
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }
        if (!task) return;

        task.userLabel = newLabel;
        task.priorityCategory = (newLabel === 'Now') ? 'DO_FIRST' : 'LATER';

        // Update shared task
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getTasks === 'function') {
            const raw = window.TempoEmergencyFlow.getTasks();
            const shared = raw.find(t => t.id === taskId);
            if (shared) {
                shared.userLabel = newLabel;
                shared.priorityCategory = task.priorityCategory;
            }
        }

        reorganizePlanWithPlanner(plan);
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(`Priority updated to ${newLabel}. Plan reorganized.`);
        }
        render();
    }

    /**
     * Open Break Task modal
     */
    function openBreakTaskModal(taskId) {
        const targetId = taskId || selectedTaskId;
        if (!targetId) return;
        if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.renderBreakTaskPopup === 'function') {
            window.TempoUrmodeFlow.renderBreakTaskPopup(targetId);
        } else if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.startBreakTaskFlow === 'function') {
            window.TempoUrmodeFlow.startBreakTaskFlow(targetId);
        } else if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.reviewStepBreakdown === 'function') {
            window.TempoEmergencyFlow.reviewStepBreakdown(targetId);
        }
    }

    /**
     * Task Notes management
     */
    function openNoteEditor(taskId) {
        pendingNoteTaskId = taskId || selectedTaskId;
        activeModal = 'edit-task-note';
        render();
    }

    function saveNote(taskId) {
        const targetId = taskId || pendingNoteTaskId || selectedTaskId;
        if (!targetId) return;

        const input = document.getElementById('pw-note-editor-text');
        const text = input ? input.value : '';

        const plan = getActivePlan();
        let targetTask = null;
        if (plan && plan.plannedTasks) {
            const pt = plan.plannedTasks.find(item => item.task && item.task.id === targetId);
            if (pt) targetTask = pt.task;
        }
        if (!targetTask && plan && plan.unarrangedTasks) {
            targetTask = plan.unarrangedTasks.find(t => t.id === targetId);
        }
        const taskName = targetTask ? targetTask.name : 'Academic Task';

        if (window.TempoToolNotes && typeof window.TempoToolNotes.saveTaskNote === 'function') {
            window.TempoToolNotes.saveTaskNote(targetId, taskName, text);
        }

        if (targetTask) {
            targetTask.note = text.trim();
            targetTask.description = text.trim();
        }

        persistPlan(plan);
        activeModal = null;
        pendingNoteTaskId = null;
        render();
    }

    function deleteNote(taskId) {
        const targetId = taskId || pendingNoteTaskId || selectedTaskId;
        if (!targetId) return;

        if (window.TempoToolNotes && typeof window.TempoToolNotes.deleteTaskNote === 'function') {
            window.TempoToolNotes.deleteTaskNote(targetId);
        }

        const plan = getActivePlan();
        if (plan && plan.plannedTasks) {
            const pt = plan.plannedTasks.find(item => item.task && item.task.id === targetId);
            if (pt && pt.task) {
                pt.task.note = '';
                pt.task.description = '';
            }
        }
        if (plan && plan.unarrangedTasks) {
            const u = plan.unarrangedTasks.find(t => t.id === targetId);
            if (u) {
                u.note = '';
                u.description = '';
            }
        }

        persistPlan(plan);
        activeModal = null;
        pendingNoteTaskId = null;
        render();
    }

    function closeModal() {
        activeModal = null;
        pendingDeadlineEdit = null;
        pendingNoteTaskId = null;
        render();
    }

    /**
     * Open Tempo Estimate Editor for task (reuses existing modal)
     */
    function openEstimateEdit(taskId) {
        const plan = getActivePlan();
        if (!plan) return;

        const taskIndex = plan.plannedTasks.findIndex(pt => pt.task && pt.task.id === taskId);
        if (taskIndex !== -1 && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.openEditEstimateModal === 'function') {
            window.TempoEmergencyFlow.openEditEstimateModal(taskIndex);
        } else if (window.TempoApp) {
            window.TempoApp.showToast("Edit estimate via plan review.");
        }
    }

        /**
     * Remove task from plan
     */
    function promptClearTask(taskId) {
        pendingClearTaskId = taskId || selectedTaskId;
        activeModal = 'clear-task-confirm';
        render();
    }

    function closeClearTaskConfirm() {
        if (isActionProcessing) return;
        activeModal = null;
        pendingClearTaskId = null;
        render();
    }

    function executeClearTask() {
        if (isActionProcessing) return;
        isActionProcessing = true;

        try {
            const taskId = pendingClearTaskId || selectedTaskId;
            if (!taskId) {
                activeModal = null;
                render();
                return;
            }

            const plan = getActivePlan();
            if (!plan) {
                activeModal = null;
                render();
                return;
            }

            // Check plannedTasks
            if (Array.isArray(plan.plannedTasks)) {
                const ptIdx = plan.plannedTasks.findIndex(pt => pt.task && pt.task.id === taskId);
                if (ptIdx !== -1) {
                    plan.plannedTasks.splice(ptIdx, 1);
                    if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
                        window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
                    }
                }
            }

            // Check unarrangedTasks
            if (Array.isArray(plan.unarrangedTasks)) {
                const unIdx = plan.unarrangedTasks.findIndex(t => (t.task ? t.task.id === taskId : t.id === taskId));
                if (unIdx !== -1) {
                    plan.unarrangedTasks.splice(unIdx, 1);
                }
            }

            // Check tasks
            if (Array.isArray(plan.tasks)) {
                const tIdx = plan.tasks.findIndex(t => t.id === taskId);
                if (tIdx !== -1) {
                    plan.tasks.splice(tIdx, 1);
                }
            }

            // Auto-select next available task
            if (selectedTaskId === taskId) {
                const remaining = [];
                if (Array.isArray(plan.plannedTasks)) {
                    plan.plannedTasks.forEach(item => {
                        if (item.task) remaining.push(item.task);
                    });
                }
                if (Array.isArray(plan.unarrangedTasks)) {
                    plan.unarrangedTasks.forEach(u => {
                        const t = u.task ? u.task : u;
                        if (t) remaining.push(t);
                    });
                }
                const activeRemaining = remaining.find(t => !t.completed);
                selectedTaskId = activeRemaining ? activeRemaining.id : (remaining.length > 0 ? remaining[0].id : null);
            }

            persistPlan(plan);
            activeModal = null;
            pendingClearTaskId = null;
            render();
        } finally {
            isActionProcessing = false;
        }
    }

    function removeTask(taskId) {
        promptClearTask(taskId);
    }

    function toggleAddSubtaskInput() {
        showAddSubtaskInput = !showAddSubtaskInput;
        render();
    }

    /**
     * Subtask management inside drawer
     */
    function addSubtask(taskId) {
        const input = document.getElementById('pw-new-subtask-title');
        const title = input ? input.value.trim() : '';
        if (!title) return;

        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        const pt = plan.plannedTasks.find(item => item.task && item.task.id === taskId);
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }
        if (!task) return;

        if (!Array.isArray(task.subtasks)) task.subtasks = [];
        task.subtasks.push({
            id: 'sub_' + Date.now(),
            title: title,
            durationMinutes: 15,
            completed: false
        });

        persistPlan(plan);
        render();
    }

    function removeSubtask(taskId, subtaskId) {
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        const pt = plan.plannedTasks.find(item => item.task && item.task.id === taskId);
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }
        if (!task || !task.subtasks) return;

        task.subtasks = task.subtasks.filter(s => s.id !== subtaskId);
        persistPlan(plan);
        render();
    }

    function setSubtaskCompleted(taskId, subtaskId, isCompleted) {
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        if (Array.isArray(plan.plannedTasks)) {
            const pt = plan.plannedTasks.find(item => item.task && String(item.task.id) === String(taskId));
            if (pt) task = pt.task;
        }
        if (!task && Array.isArray(plan.unarrangedTasks)) {
            const u = plan.unarrangedTasks.find(item => String(item && item.task ? item.task.id : item.id) === String(taskId));
            if (u) task = u.task || u;
        }
        if (!task && Array.isArray(plan.tasks)) {
            task = plan.tasks.find(t => String(t.id) === String(taskId));
        }
        if (!task || !Array.isArray(task.subtasks)) return;

        const sub = task.subtasks.find(s => String(s.id) === String(subtaskId));
        if (sub) {
            sub.completed = Boolean(isCompleted);
            persistPlan(plan);
            if (window.TempoPlanStore && typeof window.TempoPlanStore.updateSubtaskState === 'function') {
                window.TempoPlanStore.updateSubtaskState(taskId, subtaskId, { completed: sub.completed });
            }
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                window.TempoEmergencyFlow.setConfirmedPlan(plan);
            }
            if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
                window.TempoMode.renderActiveModeHome();
            }
            render();
        }
    }

    function toggleSubtask(taskId, subtaskId) {
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        if (Array.isArray(plan.plannedTasks)) {
            const pt = plan.plannedTasks.find(item => item.task && String(item.task.id) === String(taskId));
            if (pt) task = pt.task;
        }
        if (!task && Array.isArray(plan.unarrangedTasks)) {
            const u = plan.unarrangedTasks.find(item => String(item && item.task ? item.task.id : item.id) === String(taskId));
            if (u) task = u.task || u;
        }
        if (!task && Array.isArray(plan.tasks)) {
            task = plan.tasks.find(t => String(t.id) === String(taskId));
        }
        if (!task || !Array.isArray(task.subtasks)) return;

        const sub = task.subtasks.find(s => String(s.id) === String(subtaskId));
        if (sub) {
            sub.completed = !sub.completed;
            persistPlan(plan);
            if (window.TempoPlanStore && typeof window.TempoPlanStore.updateSubtaskState === 'function') {
                window.TempoPlanStore.updateSubtaskState(taskId, subtaskId, { completed: sub.completed });
            }
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                window.TempoEmergencyFlow.setConfirmedPlan(plan);
            }
            if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
                window.TempoMode.renderActiveModeHome();
            }
            render();
        }
    }

    function reorderDrawerSubtask(taskId, fromIdx, toIdx) {
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        const pt = plan.plannedTasks.find(item => item.task && item.task.id === taskId);
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }
        if (!task || !task.subtasks) return;
        if (fromIdx < 0 || fromIdx >= task.subtasks.length || toIdx < 0 || toIdx >= task.subtasks.length) return;

        const [moved] = task.subtasks.splice(fromIdx, 1);
        task.subtasks.splice(toIdx, 0, moved);

        persistPlan(plan);
        render();
    }

    // =========================================================================
    // TASK DRAG AND DROP REORDERING
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
        const card = e.currentTarget.closest('.workspace-task-card') || e.currentTarget;
        if (card) {
            card.classList.add('em-card-dragging', 'opacity-60', 'border-dashed', 'border-[#FF6B2C]', 'shadow-lg');
            card.classList.remove('opacity-40');
        }
        const handle = card ? card.querySelector('.workspace-drag-handle') : null;
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
        const card = e.currentTarget.closest('.workspace-task-card');
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
        const card = e.currentTarget.closest('.workspace-task-card');
        if (card) {
            if (e.relatedTarget && card.contains(e.relatedTarget)) return;
            card.classList.remove('em-drop-target', 'bg-orange-50/60', 'border-[#FF6B2C]', 'border-t-2', 'border-t-[#FF6B2C]', 'border-b-2', 'border-b-[#FF6B2C]');
        }
    }

    function clearTaskDragStyles() {
        draggedGlobalIndex = null;
        isDraggingTask = false;
        document.body.classList.remove('is-dragging-card');
        document.querySelectorAll('.workspace-task-card').forEach(el => {
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
        document.querySelectorAll('.workspace-drag-handle').forEach(h => {
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
            reorderTasks(fromIdx, targetGlobalIndex);
        }
    }

    function handleDragEnd(e) {
        clearTaskDragStyles();
    }

    function reorderTasks(fromIndex, toIndex) {
        const plan = getActivePlan();
        if (!plan || !plan.plannedTasks) return;
        if (fromIndex < 0 || fromIndex >= plan.plannedTasks.length) return;
        if (toIndex < 0 || toIndex >= plan.plannedTasks.length) return;
        if (fromIndex === toIndex) return;

        const targetItem = plan.plannedTasks[toIndex];
        const targetDayDate = targetItem.dayDate;
        const targetDayLabel = targetItem.dayLabel;

        const [movedItem] = plan.plannedTasks.splice(fromIndex, 1);
        movedItem.dayDate = targetDayDate;
        if (targetDayLabel) movedItem.dayLabel = targetDayLabel;

        plan.plannedTasks.splice(toIndex, 0, movedItem);

        persistPlan(plan);
        render();
    }

    /**
     * Scheduling / Rescheduling Modal
     */
    function openRescheduleModal(taskId) {
        rescheduleTaskId = taskId;
        rescheduleSelectedWindow = null;
        rescheduleShowAddTime = false;
        activeModal = 'reschedule';
        render();
    }

    function closeRescheduleModal() {
        activeModal = null;
        rescheduleTaskId = null;
        render();
    }

    function scheduleTaskAsUnarranged(taskId) {
        const plan = getActivePlan();
        if (!plan) return;

        const ptIdx = plan.plannedTasks.findIndex(pt => pt.task && pt.task.id === taskId);
        if (ptIdx !== -1) {
            const [item] = plan.plannedTasks.splice(ptIdx, 1);
            const task = item.task;
            task.scheduledDate = null;
            task.startTime = null;
            task.endTime = null;
            task.executionBadge = null;

            if (!plan.unarrangedTasks) plan.unarrangedTasks = [];
            if (!plan.unarrangedTasks.some(t => t.id === task.id)) {
                plan.unarrangedTasks.push(task);
            }

            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
                window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
            }

            persistPlan(plan);
        }

        activeModal = null;
        rescheduleTaskId = null;
        render();
    }

    function executeReschedule(taskId, targetDayDate) {
        const plan = getActivePlan();
        if (!plan) return;

        // Is it currently planned or unarranged?
        let task = null;
        const ptIdx = plan.plannedTasks.findIndex(pt => pt.task && pt.task.id === taskId);
        if (ptIdx !== -1) {
            const [item] = plan.plannedTasks.splice(ptIdx, 1);
            task = item.task;
        } else if (plan.unarrangedTasks) {
            const unIdx = plan.unarrangedTasks.findIndex(t => (t && t.task ? t.task.id : t.id) === taskId);
            if (unIdx !== -1) {
                const [item] = plan.unarrangedTasks.splice(unIdx, 1);
                task = item && item.task ? item.task : item;
            }
        }

        if (task && targetDayDate) {
            // Find target day label
            let dayLabel = targetDayDate;
            const todayStr = getTodayISO();
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            const tomorrowStr = tomorrow.toISOString().split('T')[0];

            if (targetDayDate === todayStr) dayLabel = 'TODAY';
            else if (targetDayDate === tomorrowStr) dayLabel = 'TOMORROW';

            plan.plannedTasks.push({
                task: task,
                dayDate: targetDayDate,
                dayLabel: dayLabel,
                startTime: null,
                endTime: null,
                isOverCapacity: false,
                executionBadge: 'LATER',
                hasDeadlineConflict: false
            });

            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
                window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
            }

            persistPlan(plan);
        }

        activeModal = null;
        rescheduleTaskId = null;
        render();
    }

    /**
     * Add Task Modal
     */
    function openAddTaskModal() {
        activeModal = 'add-task';
        pendingAddedTask = null;
        render();
    }

    function closeAddTaskModal() {
        activeModal = null;
        pendingAddedTask = null;
        render();
    }

    function submitAddTask() {
        const nameInput = document.getElementById('pw-add-task-name');
        const name = nameInput ? nameInput.value.trim() : '';
        if (!name) {
            alert('Please enter a task name.');
            return;
        }

        const dateInput = document.getElementById('pw-add-task-date');
        const timeInput = document.getElementById('pw-add-task-time');
        const noFixedCheck = document.getElementById('pw-add-task-no-deadline');

        const durValInput = document.getElementById('pw-add-task-dur-val');
        const durUnitInput = document.getElementById('pw-add-task-dur-unit');
        const notSureCheck = document.getElementById('pw-add-task-dur-not-sure');

        const hasNoFixed = noFixedCheck ? noFixedCheck.checked : false;
        const notSure = notSureCheck ? notSureCheck.checked : false;

        let durationMinutes = null;
        if (!notSure && durValInput && durValInput.value) {
            const val = parseFloat(durValInput.value);
            const unit = durUnitInput ? durUnitInput.value : 'hours';
            if (val > 0) {
                durationMinutes = unit === 'hours' ? Math.round(val * 60) : Math.round(val);
            }
        }

        const newTask = {
            id: 'task_' + Date.now(),
            name: name,
            deadlineDate: hasNoFixed ? null : (dateInput ? dateInput.value || null : null),
            deadlineTime: hasNoFixed ? null : (timeInput ? timeInput.value || '23:59' : null),
            hasDeadline: !hasNoFixed && dateInput && !!dateInput.value,
            durationMinutes: durationMinutes || 60,
            durationLabel: durationMinutes ? formatDuration(durationMinutes) : '1h',
            isUnknownDuration: !durationMinutes,
            subtasks: [],
            completed: false,
            isInProgress: false,
            executionStatus: 'pending',
            importance: 'HIGH',
            consequence: 'Standard',
            flexibility: 'SOME'
        };

        pendingAddedTask = newTask;
        activeModal = 'fit-task-prompt';
        render();
    }

    function handleFitTaskChoice(choice) {
        if (!pendingAddedTask) return;
        const plan = getActivePlan();
        if (!plan) return;

        if (choice === 'fit') {
            // Find earliest day in availability
            const todayStr = getTodayISO();
            let targetDay = todayStr;
            if (plan.availabilityDays && plan.availabilityDays.length > 0) {
                targetDay = plan.availabilityDays[0].date;
            }

            plan.plannedTasks.push({
                task: pendingAddedTask,
                dayDate: targetDay,
                dayLabel: targetDay === todayStr ? 'TODAY' : targetDay,
                startTime: null,
                endTime: null,
                isOverCapacity: false,
                executionBadge: 'LATER',
                hasDeadlineConflict: false
            });

            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
                window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
            }
        } else {
            // Leave unscheduled
            if (!plan.unarrangedTasks) plan.unarrangedTasks = [];
            plan.unarrangedTasks.push(pendingAddedTask);
        }

        // Also add to raw tasks array
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getTasks === 'function') {
            const rawTasks = window.TempoEmergencyFlow.getTasks();
            rawTasks.push(pendingAddedTask);
        }

        persistPlan(plan);
        activeModal = null;
        pendingAddedTask = null;
        render();
    }

    /**
     * Adjust Availability Modal
     */
    function openAdjustAvailabilityModal() {
        activeModal = 'adjust-availability';
        adjustAvailShowAdd = false;
        render();
    }

    function closeAdjustAvailabilityModal() {
        activeModal = null;
        render();
    }

    function addAvailabilityBlockInline() {
        const dateInput = document.getElementById('pw-avail-add-date');
        const startInput = document.getElementById('pw-avail-add-start');
        const endInput = document.getElementById('pw-avail-add-end');

        const date = dateInput ? dateInput.value : '';
        const start = startInput ? startInput.value : '';
        const end = endInput ? endInput.value : '';

        if (!date || !start || !end) {
            alert('Please select date, start time, and end time.');
            return;
        }

        const plan = getActivePlan();
        if (!plan) return;

        if (!plan.availabilityDays) plan.availabilityDays = [];
        let day = plan.availabilityDays.find(d => d.date === date);
        if (!day) {
            day = {
                date: date,
                label: date,
                isUnavailable: false,
                blocks: []
            };
            plan.availabilityDays.push(day);
        }

        if (!Array.isArray(day.blocks)) day.blocks = [];
        day.blocks.push({
            id: 'b_' + Date.now(),
            start: start,
            end: end
        });

        // Recalculate
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
            window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
        }

        persistPlan(plan);
        adjustAvailShowAdd = false;
        render();
    }

    function removeAvailabilityBlock(dayDate, blockId) {
        const plan = getActivePlan();
        if (!plan || !plan.availabilityDays) return;

        const day = plan.availabilityDays.find(d => d.date === dayDate);
        if (day && day.blocks) {
            day.blocks = day.blocks.filter(b => b.id !== blockId);
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
                window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
            }
            persistPlan(plan);
            render();
        }
    }

    /**
     * MAIN RENDER FUNCTION: Tempo Working Plan (Two-column layout matching reference)
     */
    function render() {
        const root = document.getElementById('plan-workspace-root');
        if (!root) return;

        // Ensure light blue background on body and main
        document.body.style.backgroundColor = '#EFFAFF';
        const mainEl = document.querySelector('main');
        if (mainEl) mainEl.style.backgroundColor = '#EFFAFF';

        const plan = getActivePlan();
        if (!plan) return;

        const plannedTasks = plan.plannedTasks || [];
        const unarrangedTasks = (plan.unarrangedTasks || []).map(u => (u && u.task ? u.task : u));

        // Group tasks into active vs completed
        const activePlanned = plannedTasks.filter(pt => pt.task && !pt.task.completed);
        const activeUnarranged = unarrangedTasks.filter(t => !t.completed);

        const completedPlanned = plannedTasks.filter(pt => pt.task && pt.task.completed).map(pt => ({
            task: pt.task,
            startTime: pt.startTime || pt.scheduledStartTime,
            endTime: pt.endTime || pt.scheduledEndTime,
            dayLabel: pt.dayLabel,
            dayDate: pt.dayDate
        }));
        const completedUnarranged = unarrangedTasks.filter(t => t.completed).map(t => ({
            task: t,
            startTime: null,
            endTime: null,
            dayLabel: null,
            dayDate: null
        }));

        const allCompleted = [...completedPlanned, ...completedUnarranged];
        allCompleted.sort((a, b) => (b.task.completedAt || 0) - (a.task.completedAt || 0));

        // Total count and completed count
        const totalTasksCount = plannedTasks.length + unarrangedTasks.length;
        const completedTasksCount = allCompleted.length;
        const progressPercent = totalTasksCount > 0 ? Math.round((completedTasksCount / totalTasksCount) * 100) : 0;

        // Auto-select active task if selectedTaskId is unset or missing
        const allTasksFlat = [];
        plannedTasks.forEach(pt => { if (pt.task) allTasksFlat.push(pt.task); });
        unarrangedTasks.forEach(t => { if (t) allTasksFlat.push(t); });

        if (!selectedTaskId || !allTasksFlat.some(t => t.id === selectedTaskId)) {
            const firstActive = activePlanned.length > 0 ? activePlanned[0].task : (activeUnarranged.length > 0 ? activeUnarranged[0] : null);
            if (firstActive) {
                selectedTaskId = firstActive.id;
            } else if (allCompleted.length > 0) {
                selectedTaskId = allCompleted[0].task.id;
            } else if (allTasksFlat.length > 0) {
                selectedTaskId = allTasksFlat[0].id;
            }
        }

        // Find currently selected task and its scheduled metadata
        let selectedTask = allTasksFlat.find(t => t.id === selectedTaskId);
        let selectedPlanItem = plannedTasks.find(pt => pt.task && pt.task.id === selectedTaskId);

        // Group active planned tasks by dayDate
        const todayStr = getTodayISO();
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const tomorrowStr = tomorrow.toISOString().split('T')[0];

        const daysMap = {};
        activePlanned.forEach((item, globalIdx) => {
            item.globalIndex = globalIdx;
            const dDate = item.dayDate || 'unscheduled';
            let dLabel = item.dayLabel;
            if (!dLabel) {
                if (dDate === todayStr) dLabel = 'Today, Month day';
                else if (dDate === tomorrowStr) dLabel = 'Tomorrow, Month day';
                else dLabel = formatMonthDay(dDate);
            }

            if (!daysMap[dDate]) {
                daysMap[dDate] = { label: dLabel, date: dDate, items: [] };
            }
            daysMap[dDate].items.push(item);
        });

        // Determine badge for selected task
        const isSelectedNow = selectedTask && (
            selectedTask.userLabel === 'Now' ||
            selectedTask.priorityCategory === 'DO_FIRST' ||
            (selectedPlanItem && (selectedPlanItem.executionBadge === 'Now' || selectedPlanItem.planPositionBadge === 'DO THIS' || selectedPlanItem.globalIndex === 0))
        );
        const selectedBadgeLabel = selectedTask ? (selectedTask.completed ? 'Done' : (isSelectedNow ? 'Now' : 'Later')) : '';

        // Schedule string for detail header
        let detailScheduleStr = 'Today, Month day 3:00 PM to 5:30 PM';
        if (selectedPlanItem && (selectedPlanItem.startTime || selectedPlanItem.scheduledStartTime) && (selectedPlanItem.endTime || selectedPlanItem.scheduledEndTime)) {
            const sStart = formatTime12H(selectedPlanItem.startTime || selectedPlanItem.scheduledStartTime);
            const sEnd = formatTime12H(selectedPlanItem.endTime || selectedPlanItem.scheduledEndTime);
            const dLabel = selectedPlanItem.dayLabel || (selectedPlanItem.dayDate === todayStr ? 'Today, Month day' : formatMonthDay(selectedPlanItem.dayDate));
            detailScheduleStr = `${dLabel} ${sStart} to ${sEnd}`;
        } else if (selectedTask) {
            detailScheduleStr = `Flexible schedule · ~${selectedTask.durationLabel || '1h'}`;
        }

        const selectedSubtaskCount = selectedTask && Array.isArray(selectedTask.subtasks) ? selectedTask.subtasks.length : 0;
        const selectedCompletedSubtasks = selectedTask && Array.isArray(selectedTask.subtasks) ? selectedTask.subtasks.filter(s => s.completed).length : 0;
        const savedNoteObj = selectedTask && window.TempoToolNotes ? window.TempoToolNotes.getNoteForTask(selectedTask.id) : null;
        const selectedNoteText = savedNoteObj ? savedNoteObj.text : (selectedTask && selectedTask.note && selectedTask.note !== 'Create a sheet to manage references' ? selectedTask.note : '');

        root.innerHTML = `
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 sm:py-5 space-y-6" data-tempo-ui="tempo-working-plan">
                <!-- Top-Left Navigation Control -->
                <div class="flex items-center justify-between">
                    <button id="plan-workspace-back-home"
                            type="button"
                            onclick="window.TempoPlanWorkspace.navigateHome()" 
                            class="text-xs sm:text-sm font-semibold text-[#6F6B68] hover:text-[#202124] flex items-center space-x-1.5 transition py-1 cursor-pointer group"
                            title="Return to Home">
                        <span class="group-hover:-translate-x-0.5 transition-transform">←</span>
                        <span>Return Home</span>
                    </button>
                </div>

                <!-- Centered Page Title -->
                <div class="text-center">
                    <h1 class="font-heading text-3xl sm:text-4xl md:text-[42px] font-extrabold text-[#DBA590] tracking-tight">
                        Tempo Working Plan
                    </h1>
                </div>

                <!-- Progress Bar and Action Buttons Row -->
                <div class="flex flex-col md:flex-row items-center justify-between gap-4 pt-1 pb-2">
                    <!-- Progress Bar & Count -->
                    <div class="flex items-center space-x-3 w-full md:w-auto">
                        <div class="w-48 sm:w-64 md:w-72 h-3.5 bg-[#CCD3D5] rounded-full overflow-hidden flex items-center p-0.5">
                            <div class="bg-[#D99E87] h-full rounded-full transition-all duration-300"
                                 style="width: ${progressPercent}%; min-width: ${progressPercent > 0 ? '12px' : '8px'};"></div>
                        </div>
                        <span class="text-xs sm:text-sm font-medium text-[#6F6B68] shrink-0">
                            ${completedTasksCount}/${totalTasksCount} Tasks
                        </span>
                    </div>

                    <!-- Header Plan Action CTAs -->
                    <div class="flex flex-wrap items-center gap-2 sm:gap-2.5 shrink-0 justify-center">
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.openAddTaskModal()"
                                class="px-3.5 sm:px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#92A491] hover:bg-[#829381] shadow-2xs transition cursor-pointer">
                            Add task
                        </button>
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.openAdjustAvailabilityModal()"
                                class="px-3.5 sm:px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#8AA8B7] hover:bg-[#7A98A7] shadow-2xs transition cursor-pointer">
                            Add availability
                        </button>
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.startAdjustPlan()"
                                class="px-3.5 sm:px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#D99E87] hover:bg-[#C98E77] shadow-2xs transition cursor-pointer">
                            Adjust Plan
                        </button>
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.promptDeletePlan()"
                                class="px-3.5 sm:px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#C53B27] hover:bg-[#B03422] shadow-2xs transition cursor-pointer">
                            Delete my plan
                        </button>
                    </div>
                </div>

                <!-- Main Two-Column Layout -->
                <div class="flex flex-col lg:flex-row gap-6 lg:gap-8 items-start">
                    <!-- LEFT COLUMN: Scrollable Task List -->
                    <div class="w-full lg:w-[48%] flex flex-col">
                        <div id="plan-workspace-task-list"
                             class="max-h-[calc(100vh-230px)] min-h-[460px] overflow-y-auto overflow-x-hidden pr-2 sm:pr-3 space-y-6 plan-custom-scroll">
                            ${Object.keys(daysMap).map((dDate, gIdx) => {
                                const group = daysMap[dDate];
                                return `
                                    <div class="space-y-3.5">
                                        <!-- Date Heading -->
                                        <h3 class="font-heading font-extrabold text-base sm:text-lg text-[#D9A18B]">
                                            ${escapeHTML(group.label)}
                                        </h3>

                                        <!-- Tasks in this Day -->
                                        <div class="space-y-3">
                                            ${group.items.map(item => {
                                                const task = item.task;
                                                const isSelected = selectedTaskId === task.id;
                                                const isNow = item.executionBadge === 'Now' || item.planPositionBadge === 'DO THIS' || item.globalIndex === 0;
                                                const badgeClass = isNow ? 'bg-[#D99E87] text-white' : 'bg-[#E8ECF1] text-[#7B96A6]';
                                                const badgeText = isNow ? 'Now' : 'Later';

                                                const startTime = item.startTime || item.scheduledStartTime;
                                                const endTime = item.endTime || item.scheduledEndTime;
                                                const subCount = Array.isArray(task.subtasks) ? task.subtasks.length : 0;
                                                const compSubCount = Array.isArray(task.subtasks) ? task.subtasks.filter(s => s.completed).length : 0;

                                                return `
                                                    <div class="flex items-center gap-3 sm:gap-4" data-task-row="${task.id}">
                                                        <!-- Time Slot on Left -->
                                                        <div class="w-16 sm:w-20 text-center shrink-0 flex flex-col items-center justify-center text-xs font-bold text-[#D9A18B] leading-tight">
                                                            ${startTime && endTime ? `
                                                                <span>${formatTime12H(startTime)}</span>
                                                                <span class="my-0.5">|</span>
                                                                <span>${formatTime12H(endTime)}</span>
                                                            ` : `
                                                                <span>Flexible</span>
                                                            `}
                                                        </div>

                                                        <!-- Task Card on Right -->
                                                        <div class="flex-1 min-w-0 bg-[#FDFBF6] hover:bg-white border ${isSelected ? 'border-2 border-[#D99E87]' : 'border-[#E3C7A5]'} rounded-2xl p-4 sm:p-5 transition shadow-2xs cursor-pointer"
                                                             onclick="window.TempoPlanWorkspace.selectTask('${task.id}')">
                                                            <div class="flex items-center justify-between gap-2 pb-1.5">
                                                                <div class="flex items-center space-x-2.5 min-w-0">
                                                                    <!-- Checkbox -->
                                                                    <button type="button"
                                                                            onclick="window.TempoPlanWorkspace.toggleTaskComplete('${task.id}', event)"
                                                                            class="w-5 h-5 rounded-lg border flex items-center justify-center text-xs font-bold transition shrink-0 ${task.completed ? 'bg-[#92A491] border-[#92A491] text-white' : 'border-[#E3C7A5] bg-white text-transparent hover:border-[#D99E87]'}"
                                                                            title="Mark complete">
                                                                        ✓
                                                                    </button>
                                                                    <!-- Title -->
                                                                    <h4 class="font-heading text-base font-bold text-[#202124] truncate ${task.completed ? 'line-through text-stone-400' : ''}">
                                                                        ${escapeHTML(task.name)}
                                                                    </h4>
                                                                </div>
                                                                <!-- Status Badge with Interactive Dropdown -->
                                                                <div class="relative inline-block" data-label-menu-container>
                                                                    <button type="button"
                                                                            onclick="event.stopPropagation(); window.TempoPlanWorkspace.toggleLabelMenu('${task.id}', event);"
                                                                            class="px-3 py-0.5 rounded-full text-xs font-bold ${badgeClass} shrink-0 cursor-pointer hover:opacity-90 transition flex items-center space-x-1"
                                                                            title="Change priority: Now or Later">
                                                                        <span>${badgeText}</span>
                                                                        <span class="text-[9px] opacity-75">▾</span>
                                                                    </button>
                                                                    ${activeLabelMenuTaskId === task.id ? `
                                                                        <div class="absolute right-0 top-full mt-1 z-30 bg-white border border-[#E3C7A5] rounded-xl shadow-lg py-1 w-28 text-xs font-semibold overflow-hidden"
                                                                             onclick="event.stopPropagation();">
                                                                            <button type="button"
                                                                                    onclick="window.TempoPlanWorkspace.setTaskLabel('${task.id}', 'Now');"
                                                                                    class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${isNow ? 'font-bold text-[#D99E87]' : ''}">
                                                                                <span>Now</span>
                                                                                ${isNow ? '<span>✓</span>' : ''}
                                                                            </button>
                                                                            <button type="button"
                                                                                    onclick="window.TempoPlanWorkspace.setTaskLabel('${task.id}', 'Later');"
                                                                                    class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${!isNow ? 'font-bold text-[#7B96A6]' : ''}">
                                                                                <span>Later</span>
                                                                                ${!isNow ? '<span>✓</span>' : ''}
                                                                            </button>
                                                                        </div>
                                                                    ` : ''}
                                                                </div>
                                                            </div>

                                                            <!-- Due date and subtasks -->
                                                            <div class="pl-7 space-y-0.5 text-xs text-[#6F6B68]">
                                                                <div>Due: ${formatDeadline(task.deadlineDate || task.deadline, task.deadlineTime)}</div>
                                                                <div>${compSubCount}/${subCount} subtasks</div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                `;
                                            }).join('')}
                                        </div>

                                        ${gIdx < Object.keys(daysMap).length - 1 ? `
                                            <hr class="border-[#EEE9E7] my-3" />
                                        ` : ''}
                                    </div>
                                `;
                            }).join('')}

                            <!-- Unarranged Active Tasks if any -->
                            ${activeUnarranged.length > 0 ? `
                                <div class="space-y-3.5 pt-2">
                                    <h3 class="font-heading font-extrabold text-base sm:text-lg text-[#D9A18B]">
                                        Flexible / Unscheduled
                                    </h3>
                                    <div class="space-y-3">
                                        ${activeUnarranged.map(task => {
                                            const isSelected = selectedTaskId === task.id;
                                            const subCount = Array.isArray(task.subtasks) ? task.subtasks.length : 0;
                                            const compSubCount = Array.isArray(task.subtasks) ? task.subtasks.filter(s => s.completed).length : 0;

                                            return `
                                                <div class="flex items-center gap-3 sm:gap-4" data-task-row="${task.id}">
                                                    <div class="w-16 sm:w-20 text-center shrink-0 flex flex-col items-center justify-center text-xs font-bold text-[#D9A18B] leading-tight">
                                                        <span>~${task.durationLabel || '1h'}</span>
                                                    </div>
                                                    <div class="flex-1 min-w-0 bg-[#FDFBF6] hover:bg-white border ${isSelected ? 'border-2 border-[#D99E87]' : 'border-[#E3C7A5]'} rounded-2xl p-4 sm:p-5 transition shadow-2xs cursor-pointer"
                                                         onclick="window.TempoPlanWorkspace.selectTask('${task.id}')">
                                                        <div class="flex items-center justify-between gap-2 pb-1.5">
                                                            <div class="flex items-center space-x-2.5 min-w-0">
                                                                <button type="button"
                                                                        onclick="window.TempoPlanWorkspace.toggleTaskComplete('${task.id}', event)"
                                                                        class="w-5 h-5 rounded-lg border flex items-center justify-center text-xs font-bold transition shrink-0 ${task.completed ? 'bg-[#92A491] border-[#92A491] text-white' : 'border-[#E3C7A5] bg-white text-transparent hover:border-[#D99E87]'}"
                                                                        title="Mark complete">
                                                                    ✓
                                                                </button>
                                                                <h4 class="font-heading text-base font-bold text-[#202124] truncate ${task.completed ? 'line-through text-stone-400' : ''}">
                                                                    ${escapeHTML(task.name)}
                                                                </h4>
                                                            </div>
                                                            <!-- Status Badge with Interactive Dropdown -->
                                                            <div class="relative inline-block" data-label-menu-container>
                                                                <button type="button"
                                                                        onclick="event.stopPropagation(); window.TempoPlanWorkspace.toggleLabelMenu('${task.id}', event);"
                                                                        class="px-3 py-0.5 rounded-full text-xs font-bold bg-[#E8ECF1] text-[#7B96A6] shrink-0 cursor-pointer hover:opacity-90 transition flex items-center space-x-1"
                                                                        title="Change priority: Now or Later">
                                                                    <span>Later</span>
                                                                    <span class="text-[9px] opacity-75">▾</span>
                                                                </button>
                                                                ${activeLabelMenuTaskId === task.id ? `
                                                                    <div class="absolute right-0 top-full mt-1 z-30 bg-white border border-[#E3C7A5] rounded-xl shadow-lg py-1 w-28 text-xs font-semibold overflow-hidden"
                                                                         onclick="event.stopPropagation();">
                                                                        <button type="button"
                                                                                onclick="window.TempoPlanWorkspace.setTaskLabel('${task.id}', 'Now');"
                                                                                class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124]">
                                                                            <span>Now</span>
                                                                        </button>
                                                                        <button type="button"
                                                                                onclick="window.TempoPlanWorkspace.setTaskLabel('${task.id}', 'Later');"
                                                                                class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] font-bold text-[#7B96A6]">
                                                                            <span>Later</span>
                                                                            <span>✓</span>
                                                                        </button>
                                                                    </div>
                                                                ` : ''}
                                                            </div>
                                                        </div>
                                                        <div class="pl-7 space-y-0.5 text-xs text-[#6F6B68]">
                                                            <div>Due: ${formatDeadline(task.deadlineDate || task.deadline, task.deadlineTime)}</div>
                                                            <div>${compSubCount}/${subCount} subtasks</div>
                                                        </div>
                                                    </div>
                                                </div>
                                            `;
                                        }).join('')}
                                    </div>
                                </div>
                            ` : ''}

                            <!-- DONE SECTION: Only rendered when tasks are completed -->
                            ${allCompleted.length > 0 ? `
                                <div class="pt-4 border-t border-[#EEE9E7] space-y-3.5" data-tempo-ui="done-section">
                                    <h3 class="font-heading font-extrabold text-base sm:text-lg text-[#92A491] flex items-center space-x-2">
                                        <span>Done</span>
                                        <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#E8EFE8] text-[#556B54]">(${allCompleted.length})</span>
                                    </h3>
                                    <div class="space-y-3">
                                        ${allCompleted.map(item => {
                                            const task = item.task;
                                            const isSelected = selectedTaskId === task.id;
                                            const subCount = Array.isArray(task.subtasks) ? task.subtasks.length : 0;
                                            const compSubCount = Array.isArray(task.subtasks) ? task.subtasks.filter(s => s.completed).length : 0;
                                            const startTime = item.startTime;
                                            const endTime = item.endTime;

                                            return `
                                                <div class="flex items-center gap-3 sm:gap-4 opacity-80 hover:opacity-100 transition" data-task-row="${task.id}">
                                                    <div class="w-16 sm:w-20 text-center shrink-0 flex flex-col items-center justify-center text-xs font-bold text-[#92A491] leading-tight">
                                                        ${startTime && endTime ? `
                                                            <span>${formatTime12H(startTime)}</span>
                                                            <span class="my-0.5">|</span>
                                                            <span>${formatTime12H(endTime)}</span>
                                                        ` : `
                                                            <span>--</span>
                                                        `}
                                                    </div>
                                                    <div class="flex-1 min-w-0 bg-[#FDFBF6] hover:bg-white border ${isSelected ? 'border-2 border-[#92A491]' : 'border-[#E3C7A5]'} rounded-2xl p-4 sm:p-5 transition shadow-2xs cursor-pointer"
                                                         onclick="window.TempoPlanWorkspace.selectTask('${task.id}')">
                                                        <div class="flex items-center justify-between gap-2 pb-1.5">
                                                            <div class="flex items-center space-x-2.5 min-w-0">
                                                                <button type="button"
                                                                        onclick="window.TempoPlanWorkspace.toggleTaskComplete('${task.id}', event)"
                                                                        class="w-5 h-5 rounded-lg border bg-[#92A491] border-[#92A491] text-white flex items-center justify-center text-xs font-bold transition shrink-0"
                                                                        title="Mark incomplete">
                                                                    ✓
                                                                </button>
                                                                <h4 class="font-heading text-base font-bold text-stone-400 line-through truncate">
                                                                    ${escapeHTML(task.name)}
                                                                </h4>
                                                            </div>
                                                            <span class="px-3 py-0.5 rounded-full text-xs font-bold bg-[#E8EFE8] text-[#556B54] shrink-0">
                                                                Done
                                                            </span>
                                                        </div>
                                                        <div class="pl-7 space-y-0.5 text-xs text-[#6F6B68]">
                                                            <div>Due: ${formatDeadline(task.deadlineDate || task.deadline, task.deadlineTime)}</div>
                                                            <div>${compSubCount}/${subCount} subtasks</div>
                                                        </div>
                                                    </div>
                                                </div>
                                            `;
                                        }).join('')}
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>

                    <!-- Vertical Column Divider -->
                    <div class="hidden lg:block w-px bg-[#EFF3F6] self-stretch my-2"></div>

                    <!-- RIGHT COLUMN: Selected Task Details -->
                    <div class="w-full lg:w-[48%] lg:sticky lg:top-20">
                        ${selectedTask ? `
                            <div class="bg-[#FDFBF6] border border-[#E3C7A5] rounded-3xl p-6 sm:p-7 space-y-4 shadow-sm" data-tempo-ui="selected-task-card">
                                <!-- Schedule Header -->
                                <div class="text-xs sm:text-sm font-bold text-[#D9A18B] tracking-wide">
                                    ${escapeHTML(detailScheduleStr)}
                                </div>

                                <!-- Title and Badge -->
                                <div class="flex items-center justify-between gap-3 pb-1">
                                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] ${selectedTask.completed ? 'line-through text-stone-400' : ''}">
                                        ${escapeHTML(selectedTask.name)}
                                    </h2>
                                    <!-- Status Badge with Interactive Dropdown -->
                                    <div class="relative inline-block" data-label-menu-container>
                                        <button type="button"
                                                ${selectedBadgeLabel === 'Done' ? '' : `onclick="event.stopPropagation(); window.TempoPlanWorkspace.toggleLabelMenu('${selectedTask.id}', event);"`}
                                                class="px-3 py-0.5 rounded-full text-xs font-bold ${selectedBadgeLabel === 'Now' ? 'bg-[#D99E87] text-white' : (selectedBadgeLabel === 'Done' ? 'bg-[#92A491] text-white' : 'bg-[#E8ECF1] text-[#7B96A6]')} shrink-0 ${selectedBadgeLabel !== 'Done' ? 'cursor-pointer hover:opacity-90 transition flex items-center space-x-1' : ''}"
                                                title="${selectedBadgeLabel === 'Done' ? 'Completed task' : 'Change priority: Now or Later'}">
                                            <span>${selectedBadgeLabel}</span>
                                            ${selectedBadgeLabel !== 'Done' ? '<span class="text-[9px] opacity-75">▾</span>' : ''}
                                        </button>
                                        ${activeLabelMenuTaskId === selectedTask.id && selectedBadgeLabel !== 'Done' ? `
                                            <div class="absolute right-0 top-full mt-1 z-30 bg-white border border-[#E3C7A5] rounded-xl shadow-lg py-1 w-28 text-xs font-semibold overflow-hidden"
                                                 onclick="event.stopPropagation();">
                                                <button type="button"
                                                        onclick="window.TempoPlanWorkspace.setTaskLabel('${selectedTask.id}', 'Now');"
                                                        class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${selectedBadgeLabel === 'Now' ? 'font-bold text-[#D99E87]' : ''}">
                                                    <span>Now</span>
                                                    ${selectedBadgeLabel === 'Now' ? '<span>✓</span>' : ''}
                                                </button>
                                                <button type="button"
                                                        onclick="window.TempoPlanWorkspace.setTaskLabel('${selectedTask.id}', 'Later');"
                                                        class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${selectedBadgeLabel === 'Later' ? 'font-bold text-[#7B96A6]' : ''}">
                                                    <span>Later</span>
                                                    ${selectedBadgeLabel === 'Later' ? '<span>✓</span>' : ''}
                                                </button>
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>

                                <!-- Due Date Row -->
                                <div class="flex items-center space-x-2 text-xs sm:text-sm text-[#6F6B68]">
                                    <span>Due: ${formatDeadline(selectedTask.deadlineDate || selectedTask.deadline, selectedTask.deadlineTime)}</span>
                                    <button type="button"
                                            onclick="window.TempoPlanWorkspace.toggleDeadlineEdit()"
                                            class="text-[#D99E87] font-semibold hover:underline cursor-pointer">
                                        ${isEditingDeadline ? 'Cancel' : 'Edit due day'}
                                    </button>
                                </div>

                                <!-- Inline Deadline Editor -->
                                ${isEditingDeadline ? `
                                    <div class="p-3 bg-white border border-[#E3C7A5] rounded-xl space-y-2 text-xs">
                                        <div class="grid grid-cols-2 gap-2">
                                            <div>
                                                <label class="block text-[10px] text-gray-500 font-semibold mb-0.5">Date</label>
                                                <input id="pw-edit-deadline-date" type="date" value="${selectedTask.deadlineDate || (selectedTask.deadline ? selectedTask.deadline.split(' ')[0] : '')}" class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                            </div>
                                            <div>
                                                <label class="block text-[10px] text-gray-500 font-semibold mb-0.5">Time</label>
                                                <input id="pw-edit-deadline-time" type="time" value="${selectedTask.deadlineTime || (selectedTask.deadline ? selectedTask.deadline.split(' ')[1] : '23:59')}" class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                            </div>
                                        </div>
                                        <div class="flex items-center space-x-2">
                                            <input id="pw-edit-no-deadline" type="checkbox" ${!selectedTask.hasDeadline ? 'checked' : ''} class="rounded text-[#D99E87]">
                                            <label for="pw-edit-no-deadline" class="text-xs text-stone-700">No fixed deadline</label>
                                        </div>
                                        <div class="flex justify-end pt-1">
                                            <button type="button"
                                                    onclick="window.TempoPlanWorkspace.saveDeadlineEdit('${selectedTask.id}')"
                                                    class="px-3 py-1 bg-[#D99E87] text-white rounded-lg text-xs font-bold hover:bg-[#C98E77]">
                                                Save deadline
                                            </button>
                                        </div>
                                    </div>
                                ` : ''}

                                <!-- Subtasks Count Row -->
                                <div class="flex items-center space-x-2 text-xs sm:text-sm text-[#6F6B68]">
                                    <span>${selectedCompletedSubtasks}/${selectedSubtaskCount} subtasks</span>
                                    <button type="button"
                                            onclick="window.TempoPlanWorkspace.openBreakTaskModal('${selectedTask.id}')"
                                            class="text-[#D99E87] font-semibold hover:underline cursor-pointer">
                                        Edit subtask
                                    </button>
                                </div>

                                <!-- Subtask List with Custom Scrollbar -->
                                <div class="max-h-40 overflow-y-auto space-y-2 pr-2 plan-custom-scroll">
                                    ${(selectedTask.subtasks || []).map(step => `
                                        <div class="flex items-center space-x-2.5 text-xs sm:text-sm text-[#4A4540]">
                                            <button type="button"
                                                    onclick="window.TempoPlanWorkspace.toggleSubtask('${selectedTask.id}', '${step.id}')"
                                                    class="w-4 h-4 rounded border border-[#E3C7A5] flex items-center justify-center text-[10px] font-bold transition shrink-0 ${step.completed ? 'bg-[#92A491] border-[#92A491] text-white' : 'bg-white border-[#E3C7A5] text-transparent hover:border-[#D99E87]'}"
                                                    title="Toggle subtask">
                                                ✓
                                            </button>
                                            <span class="${step.completed ? 'line-through text-stone-400' : ''}">${escapeHTML(step.title)}</span>
                                        </div>
                                    `).join('')}
                                </div>

                                <!-- Note Row -->
                                ${selectedNoteText ? `
                                    <div class="text-xs sm:text-sm text-[#4A4540] pt-1 flex items-start justify-between gap-2 bg-[#F6F4EE]/60 border border-[#EAE4DF] rounded-xl p-2.5">
                                        <div class="min-w-0 flex-1">
                                            <strong class="text-[#D9A18B]">Note:</strong> <span class="whitespace-pre-line text-[#4A4540]">${escapeHTML(selectedNoteText)}</span>
                                        </div>
                                        <button type="button"
                                                onclick="window.TempoPlanWorkspace.openNoteEditor('${selectedTask.id}')"
                                                class="text-[#D99E87] hover:text-[#C98E77] text-xs font-semibold shrink-0 cursor-pointer flex items-center space-x-1"
                                                title="Edit note">
                                            <span>Edit note</span>
                                            <span>✎</span>
                                        </button>
                                    </div>
                                ` : `
                                    <div class="pt-1">
                                        <button type="button"
                                                onclick="window.TempoPlanWorkspace.openNoteEditor('${selectedTask.id}')"
                                                class="text-xs font-bold text-[#D9A18B] hover:underline cursor-pointer flex items-center space-x-1">
                                            <span>+ Create a note</span>
                                        </button>
                                    </div>
                                `}

                                <!-- Action Buttons (2x2 grid) -->
                                <div class="grid grid-cols-2 gap-3 pt-3">
                                    <!-- 1. Mark as done -->
                                    <button type="button"
                                            onclick="window.TempoPlanWorkspace.toggleTaskComplete('${selectedTask.id}')"
                                            class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#92A491] hover:bg-[#829381] shadow-2xs transition text-center cursor-pointer">
                                        ${selectedTask.completed ? 'Mark as active' : 'Mark as done'}
                                    </button>

                                    <!-- 2. Focus now -->
                                    <button type="button"
                                            onclick="window.TempoPlanWorkspace.startTaskFocus('${selectedTask.id}')"
                                            class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#D7A690] hover:bg-[#C98E77] shadow-2xs transition flex items-center justify-center space-x-1.5 cursor-pointer">
                                        <span>▶ Focus now</span>
                                    </button>

                                    <!-- 3. Reschedule -->
                                    <button type="button"
                                            onclick="window.TempoPlanWorkspace.openRescheduleModal('${selectedTask.id}')"
                                            class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#3A4B3D] bg-white border border-[#8D9B8A] hover:bg-stone-50 transition text-center cursor-pointer">
                                        Reschedule
                                    </button>

                                    <!-- 4. Clear this task -->
                                    <button type="button"
                                            onclick="window.TempoPlanWorkspace.promptClearTask('${selectedTask.id}')"
                                            class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#C53B27] bg-white border border-[#D99E87] hover:bg-rose-50/40 transition text-center cursor-pointer">
                                        Clear this task
                                    </button>
                                </div>
                            </div>
                        ` : `
                            <div class="bg-[#FDFBF6] border border-[#E3C7A5] rounded-3xl p-8 text-center text-xs text-[#6F6B68] space-y-2">
                                <div class="font-bold text-[#202124] text-sm">No task selected</div>
                                <p>Select a task on the left or click "Add task" above.</p>
                            </div>
                        `}
                    </div>
                </div>
            </div>

            <!-- Modals Container -->
            ${renderModalsHTML(plan)}
        `;
    }


        /**
     * Render Modals (Add Task, Prompt, Reschedule, Adjust Availability)
     */
    function renderModalsHTML(plan) {
        if (!activeModal) return '';

        if (activeModal === 'add-task') {
            const todayStr = getTodayISO();
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            const tomorrowStr = tomorrow.toISOString().split('T')[0];

            return `
                <div class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-md w-full">
                        <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                            <h3 class="font-heading text-lg font-bold text-[#202124]">${window.t ? window.t('workspace.addTaskModalTitle', {}, 'Add a task') : 'Add a task'}</h3>
                            <button onclick="window.TempoPlanWorkspace.closeAddTaskModal()" class="text-gray-400 hover:text-gray-600 text-sm">✕</button>
                        </div>

                        <div class="space-y-4 text-xs">
                            <div class="space-y-1">
                                <label class="block font-bold text-gray-700">${window.t ? window.t('workspace.taskName', {}, 'Task Name') : 'Task Name'}</label>
                                <input id="pw-add-task-name" type="text" placeholder="${window.t ? window.t('workspace.taskNamePlaceholder', {}, 'e.g. Research Literature Review') : 'e.g. Research Literature Review'}"
                                       class="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-1 focus:ring-[#FF6B2C] focus:outline-none">
                            </div>

                            <div class="space-y-1.5">
                                <label class="block font-bold text-gray-700">${window.t ? window.t('workspace.deadlineUpper', {}, 'Deadline') : 'Deadline'}</label>
                                <div class="grid grid-cols-2 gap-2">
                                    <input id="pw-add-task-date" type="date" value="${tomorrowStr}"
                                           class="px-2.5 py-1.5 border border-gray-300 rounded-xl text-xs">
                                    <input id="pw-add-task-time" type="time" value="17:00"
                                           class="px-2.5 py-1.5 border border-gray-300 rounded-xl text-xs">
                                </div>
                                <div class="flex items-center space-x-2 pt-1">
                                    <input id="pw-add-task-no-deadline" type="checkbox"
                                           onchange="document.getElementById('pw-add-task-date').disabled = this.checked; document.getElementById('pw-add-task-time').disabled = this.checked;"
                                           class="rounded text-[#FF6B2C]">
                                    <label for="pw-add-task-no-deadline" class="text-stone-600">${window.t ? window.t('workspace.noFixedDeadline', {}, 'No fixed deadline') : 'No fixed deadline'}</label>
                                </div>
                            </div>

                            <div class="space-y-1.5">
                                <label class="block font-bold text-gray-700">${window.t ? window.t('workspace.focusedEstimate', {}, 'Focused-work Estimate') : 'Focused-work Estimate'}</label>
                                <div class="flex items-center space-x-2">
                                    <input id="pw-add-task-dur-val" type="number" min="0.5" step="0.5" value="1.5"
                                           class="w-20 px-3 py-1.5 border border-gray-300 rounded-xl text-center font-bold">
                                    <select id="pw-add-task-dur-unit" class="flex-1 px-3 py-1.5 border border-gray-300 rounded-xl bg-white">
                                        <option value="hours" selected>${window.t ? window.t('common.hours', {}, 'hours') : 'hours'}</option>
                                        <option value="minutes">${window.t ? window.t('common.minutes', {}, 'minutes') : 'minutes'}</option>
                                    </select>
                                </div>
                                <div class="flex items-center space-x-2 pt-1">
                                    <input id="pw-add-task-dur-not-sure" type="checkbox"
                                           onchange="document.getElementById('pw-add-task-dur-val').disabled = this.checked;"
                                           class="rounded text-[#FF6B2C]">
                                    <label for="pw-add-task-dur-not-sure" class="text-stone-600">${window.t ? window.t('workspace.notSureYet', {}, 'Not sure yet') : 'Not sure yet'}</label>
                                </div>
                            </div>
                        </div>

                        <div class="pt-3 border-t border-gray-100 flex items-center justify-end space-x-2">
                            <button onclick="window.TempoPlanWorkspace.closeAddTaskModal()" 
                                    class="px-4 py-2 border border-gray-200 text-xs font-semibold text-gray-600 rounded-xl hover:bg-stone-50">
                                ${window.t ? window.t('common.cancel', {}, 'Cancel') : 'Cancel'}
                            </button>
                            <button onclick="window.TempoPlanWorkspace.submitAddTask()"
                                    class="btn-primary px-5 py-2 rounded-xl font-bold text-xs shadow-sm">
                                ${window.t ? window.t('workspace.addTaskBtn', {}, 'Add task') : 'Add task'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        if (activeModal === 'fit-task-prompt' && pendingAddedTask) {
            return `
                <div class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-sm w-full text-center">
                        <div class="w-12 h-12 rounded-2xl bg-[#FFE9DC] text-[#FF6B2C] flex items-center justify-center text-xl mx-auto">
                            ✓
                        </div>
                        <div class="space-y-1">
                            <h3 class="font-heading text-lg font-bold text-[#202124]">${window.t ? window.t('workspace.taskAdded', {}, 'Task added') : 'Task added'}</h3>
                            <p class="text-xs text-[#6F6B68]">${window.t ? window.t('workspace.taskReadyDesc', { name: escapeHTML(pendingAddedTask.name) }, '"' + escapeHTML(pendingAddedTask.name) + '" is ready.') : ('"' + escapeHTML(pendingAddedTask.name) + '" is ready.')}</p>
                        </div>

                        <div class="pt-2 space-y-2">
                            <button onclick="window.TempoPlanWorkspace.handleFitTaskChoice('fit')"
                                    class="btn-primary w-full py-3 rounded-xl font-bold text-xs shadow-md transition">
                                ${window.t ? window.t('workspace.fitIntoPlan', {}, 'Fit it into my plan') : 'Fit it into my plan'}
                            </button>
                            <button onclick="window.TempoPlanWorkspace.handleFitTaskChoice('unscheduled')"
                                    class="w-full py-2.5 rounded-xl border border-gray-200 bg-white text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                                ${window.t ? window.t('workspace.leaveUnscheduled', {}, 'Leave it unscheduled for now') : 'Leave it unscheduled for now'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        if (activeModal === 'reschedule' && rescheduleTaskId) {
            let task = null;
            const pt = plan.plannedTasks ? plan.plannedTasks.find(item => item.task && item.task.id === rescheduleTaskId) : null;
            if (pt) task = pt.task;
            if (!task && plan.unarrangedTasks) {
                task = plan.unarrangedTasks.find(t => t.id === rescheduleTaskId);
            }
            if (!task) return '';

            const days = plan.availabilityDays || [];

            return `
                <div class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-md w-full">
                        <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                            <div>
                                <h3 class="font-heading text-lg font-bold text-[#202124]">${window.t ? window.t('workspace.rescheduleTaskModalTitle', {}, 'Reschedule task') : 'Reschedule task'}</h3>
                                <p class="text-xs text-[#6F6B68] truncate max-w-xs">${escapeHTML(task.name)}</p>
                            </div>
                            <button onclick="window.TempoPlanWorkspace.closeRescheduleModal()" class="text-gray-400 hover:text-gray-600 text-sm">✕</button>
                        </div>

                        <div class="space-y-3 text-xs">
                            <span class="block font-bold text-gray-700 uppercase text-[10px] tracking-wider">${window.t ? window.t('workspace.yourAvailableTime', {}, 'YOUR AVAILABLE TIME') : 'YOUR AVAILABLE TIME'}</span>

                            <div class="space-y-2 max-h-48 overflow-y-auto pr-1">
                                ${days.map(d => `
                                    <label class="p-3 rounded-xl border border-gray-200 hover:border-[#FF6B2C] bg-white hover:bg-orange-50/30 transition flex items-center space-x-3 cursor-pointer">
                                        <input type="radio" name="pw_reschedule_day" value="${d.date}"
                                               ${rescheduleSelectedWindow === d.date ? 'checked' : ''}
                                               onchange="window.TempoPlanWorkspace.selectRescheduleWindow('${d.date}')"
                                               class="text-[#FF6B2C] focus:ring-[#FF6B2C]">
                                        <div class="flex-1">
                                            <span class="font-bold text-[#202124] block">${escapeHTML(d.label || d.date)}</span>
                                            <span class="text-[11px] text-[#6F6B68]">
                                                ${d.blocks && d.blocks.length > 0 ? d.blocks.map(b => `${formatTime12H(b.start)} – ${formatTime12H(b.end)}`).join(', ') : (window.t ? window.t('workspace.noTimeBlocks', {}, 'No time blocks defined') : 'No time blocks defined')}
                                            </span>
                                        </div>
                                    </label>
                                `).join('')}
                            </div>

                            <!-- I'll figure it out later option -->
                            <div class="pt-2 border-t border-gray-100">
                                <button onclick="window.TempoPlanWorkspace.scheduleTaskAsUnarranged('${task.id}')"
                                        class="w-full py-2.5 rounded-xl border border-dashed border-stone-300 hover:border-[#FF6B2C] bg-stone-50 hover:bg-white text-xs font-semibold text-stone-700 text-center transition">
                                    ${window.t ? window.t('workspace.figureOutLater', {}, "I'll figure it out later (Move to Unscheduled)") : "I'll figure it out later (Move to Unscheduled)"}
                                </button>
                            </div>
                        </div>

                        <div class="pt-3 border-t border-gray-100 flex items-center justify-end space-x-2">
                            <button onclick="window.TempoPlanWorkspace.closeRescheduleModal()"
                                    class="px-4 py-2 border border-gray-200 text-xs font-semibold text-gray-600 rounded-xl hover:bg-stone-50">
                                ${window.t ? window.t('common.cancel', {}, 'Cancel') : 'Cancel'}
                            </button>
                            <button onclick="window.TempoPlanWorkspace.executeReschedule('${task.id}', window.TempoPlanWorkspace.getRescheduleSelectedWindow())"
                                    class="btn-primary px-5 py-2 rounded-xl font-bold text-xs shadow-sm">
                                ${window.t ? window.t('workspace.schedule', {}, 'Schedule') : 'Schedule'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        if (activeModal === 'adjust-availability') {
            const days = plan.availabilityDays || [];

            return `
                <div class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
                        <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                            <h3 class="font-heading text-lg font-bold text-[#202124]">${window.t ? window.t('workspace.yourAvailableTimeTitle', {}, 'Your available time') : 'Your available time'}</h3>
                            <button onclick="window.TempoPlanWorkspace.closeAdjustAvailabilityModal()" class="text-gray-400 hover:text-gray-600 text-sm">✕</button>
                        </div>

                        <div class="space-y-4 text-xs">
                            ${days.map(d => `
                                <div class="p-3.5 bg-stone-50 rounded-2xl border border-stone-100 space-y-2">
                                    <div class="flex items-center justify-between font-bold text-stone-800">
                                        <span>${escapeHTML(d.label || d.date)}</span>
                                        <span class="text-[10px] text-stone-500 uppercase tracking-wider">${d.date}</span>
                                    </div>

                                    <div class="space-y-1.5">
                                        ${(d.blocks || []).map(b => `
                                            <div class="p-2 bg-white rounded-xl border border-gray-200 flex items-center justify-between">
                                                <span class="font-semibold text-[#202124]">${formatTime12H(b.start)} – ${formatTime12H(b.end)}</span>
                                                <button onclick="window.TempoPlanWorkspace.removeAvailabilityBlock('${d.date}', '${b.id}')"
                                                        class="text-stone-400 hover:text-rose-600 text-xs px-1">✕</button>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            `).join('')}

                            <!-- Add availability block form -->
                            <div class="p-3.5 bg-[#FFF8F2] border border-[#FFD2BA] rounded-2xl space-y-2">
                                <span class="font-bold text-[#B83D08] block text-[11px] uppercase tracking-wider">${window.t ? window.t('workspace.addTimeWindow', {}, '+ Add Available Time Window') : '+ Add Available Time Window'}</span>
                                <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                                    <div>
                                        <label class="block text-[10px] text-stone-600 font-semibold mb-0.5">${window.t ? window.t('common.date', {}, 'Date') : 'Date'}</label>
                                        <input id="pw-avail-add-date" type="date" value="${getTodayISO()}"
                                               class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                    </div>
                                    <div>
                                        <label class="block text-[10px] text-stone-600 font-semibold mb-0.5">${window.t ? window.t('common.from', {}, 'From') : 'From'}</label>
                                        <input id="pw-avail-add-start" type="time" value="18:00"
                                               class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                    </div>
                                    <div>
                                        <label class="block text-[10px] text-stone-600 font-semibold mb-0.5">${window.t ? window.t('common.to', {}, 'To') : 'To'}</label>
                                        <input id="pw-avail-add-end" type="time" value="22:00"
                                               class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                    </div>
                                </div>
                                <button onclick="window.TempoPlanWorkspace.addAvailabilityBlockInline()"
                                        class="btn-primary w-full py-1.5 rounded-lg text-xs font-bold mt-1">
                                    ${window.t ? window.t('workspace.addWindowBtn', {}, 'Add window') : 'Add window'}
                                </button>
                            </div>
                        </div>

                        <div class="pt-3 border-t border-gray-100 flex justify-end">
                            <button onclick="window.TempoPlanWorkspace.closeAdjustAvailabilityModal()"
                                    class="btn-primary px-6 py-2 rounded-xl font-bold text-xs shadow-sm">
                                ${window.t ? window.t('common.done', {}, 'Done') : 'Done'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        if (activeModal === 'clear-task-confirm') {
            return `
                <div id="modal-clear-task-confirm"
                     onclick="if (event.target === this) window.TempoPlanWorkspace.closeClearTaskConfirm();"
                     class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4"
                     role="dialog"
                     aria-modal="true"
                     aria-labelledby="clear-task-title">
                    <div class="tempo-card bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-md w-full relative">
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.closeClearTaskConfirm()"
                                class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer"
                                title="Close"
                                aria-label="Close">✕</button>
                        <div class="space-y-2 pr-6">
                            <h3 id="clear-task-title" class="font-heading text-lg sm:text-xl font-bold text-[#202124]">Clear this task?</h3>
                            <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                                This task will be removed from your Working Plan. This action cannot be undone.
                            </p>
                        </div>
                        <div class="flex items-center justify-end space-x-3 pt-2">
                            <button type="button"
                                    onclick="window.TempoPlanWorkspace.closeClearTaskConfirm()"
                                    class="px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-600 hover:text-stone-900 border border-transparent hover:bg-stone-50 transition cursor-pointer">
                                Cancel
                            </button>
                            <button type="button"
                                    id="btn-confirm-clear-task"
                                    ${isActionProcessing ? 'disabled' : ''}
                                    onclick="window.TempoPlanWorkspace.executeClearTask()"
                                    class="px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#C53B27] hover:bg-[#B03422] text-white shadow-sm transition cursor-pointer inline-flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed">
                                Clear task
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        if (activeModal === 'delete-plan-confirm') {
            return `
                <div id="modal-delete-plan-confirm"
                     onclick="if (event.target === this) window.TempoPlanWorkspace.closeDeletePlanConfirm();"
                     class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4"
                     role="dialog"
                     aria-modal="true"
                     aria-labelledby="delete-plan-title">
                    <div class="tempo-card bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-md w-full relative">
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.closeDeletePlanConfirm()"
                                class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer"
                                title="Close"
                                aria-label="Close">✕</button>
                        <div class="space-y-2 pr-6">
                            <h3 id="delete-plan-title" class="font-heading text-lg sm:text-xl font-bold text-[#202124]">Delete your plan?</h3>
                            <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                                This will permanently delete your Working Plan and its scheduled tasks. This action cannot be undone.
                            </p>
                        </div>
                        <div class="flex items-center justify-end space-x-3 pt-2">
                            <button type="button"
                                    onclick="window.TempoPlanWorkspace.closeDeletePlanConfirm()"
                                    class="px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-600 hover:text-stone-900 border border-transparent hover:bg-stone-50 transition cursor-pointer">
                                Cancel
                            </button>
                            <button type="button"
                                    id="btn-confirm-delete-plan"
                                    ${isActionProcessing ? 'disabled' : ''}
                                    onclick="window.TempoPlanWorkspace.executeDeletePlan()"
                                    class="px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#C53B27] hover:bg-[#B03422] text-white shadow-sm transition cursor-pointer inline-flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed">
                                Delete my plan
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        if (activeModal === 'deadline-plan-reorder-confirm') {
            return `
                <div id="modal-deadline-reorder-confirm"
                     onclick="if (event.target === this) window.TempoPlanWorkspace.cancelDeadlineConfirm();"
                     class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4"
                     role="dialog"
                     aria-modal="true"
                     aria-labelledby="deadline-reorder-title">
                    <div class="tempo-card bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-md w-full relative">
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.cancelDeadlineConfirm()"
                                class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer"
                                title="Close"
                                aria-label="Close">✕</button>
                        <div class="space-y-2 pr-6">
                            <h3 id="deadline-reorder-title" class="font-heading text-lg sm:text-xl font-bold text-[#202124]">Update your plan?</h3>
                            <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                                Changing this deadline may affect the order of your tasks. Would you like Tempo to adjust your task priorities and reorganize your plan?
                            </p>
                        </div>
                        <div class="flex flex-col-reverse sm:flex-row items-center justify-end gap-2.5 sm:space-x-3 pt-2">
                            <button type="button"
                                    id="btn-keep-current-priorities"
                                    onclick="window.TempoPlanWorkspace.confirmDeadlineWithoutReorder()"
                                    class="w-full sm:w-auto px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-700 bg-stone-100 hover:bg-stone-200 border border-stone-200 transition cursor-pointer text-center">
                                Keep current priorities
                            </button>
                            <button type="button"
                                    id="btn-confirm-update-plan"
                                    onclick="window.TempoPlanWorkspace.confirmDeadlineWithReorder()"
                                    class="w-full sm:w-auto px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#D99E87] hover:bg-[#C98E77] text-white shadow-sm transition cursor-pointer text-center">
                                Yes, update my plan
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        if (activeModal === 'edit-task-note') {
            const noteTaskId = pendingNoteTaskId || selectedTaskId;
            const currentPlan = getActivePlan();
            let targetTask = null;
            if (currentPlan && currentPlan.plannedTasks) {
                const pt = currentPlan.plannedTasks.find(item => item.task && item.task.id === noteTaskId);
                if (pt) targetTask = pt.task;
            }
            if (!targetTask && currentPlan && currentPlan.unarrangedTasks) {
                targetTask = currentPlan.unarrangedTasks.find(t => t.id === noteTaskId);
            }
            const savedNoteObj = window.TempoToolNotes ? window.TempoToolNotes.getNoteForTask(noteTaskId) : null;
            const existingNoteText = savedNoteObj ? savedNoteObj.text : (targetTask && targetTask.note && targetTask.note !== 'Create a sheet to manage references' ? targetTask.note : '');

            return `
                <div id="modal-edit-task-note"
                     onclick="if (event.target === this) window.TempoPlanWorkspace.closeModal();"
                     class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4"
                     role="dialog"
                     aria-modal="true"
                     aria-labelledby="note-editor-title">
                    <div class="tempo-card bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-4 shadow-2xl max-w-md w-full relative">
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.closeModal()"
                                class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer"
                                title="Close"
                                aria-label="Close">✕</button>
                        <div class="space-y-1 pr-6">
                            <h3 id="note-editor-title" class="font-heading text-lg sm:text-xl font-bold text-[#202124]">
                                ${existingNoteText ? 'Edit Task Note' : 'Create Task Note'}
                            </h3>
                            <p class="text-xs text-[#6F6B68]">
                                Note for <strong class="text-[#202124]">${escapeHTML(targetTask ? targetTask.name : 'Task')}</strong>
                            </p>
                        </div>
                        <div class="space-y-2">
                            <textarea id="pw-note-editor-text"
                                      rows="4"
                                      placeholder="Add notes, links, or context for this task..."
                                      class="w-full px-3.5 py-2.5 text-xs sm:text-sm border border-stone-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#D99E87] focus:border-transparent text-[#202124] resize-y">${escapeHTML(existingNoteText)}</textarea>
                        </div>
                        <div class="flex items-center justify-between pt-2">
                            ${existingNoteText ? `
                                <button type="button"
                                        onclick="window.TempoPlanWorkspace.deleteNote('${noteTaskId}')"
                                        class="text-xs font-semibold text-red-600 hover:text-red-700 hover:underline cursor-pointer">
                                    Delete note
                                </button>
                            ` : '<div></div>'}
                            <div class="flex items-center space-x-2">
                                <button type="button"
                                        onclick="window.TempoPlanWorkspace.closeModal()"
                                        class="px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold text-stone-600 hover:bg-stone-100 transition cursor-pointer">
                                    Cancel
                                </button>
                                <button type="button"
                                        id="btn-save-task-note"
                                        onclick="window.TempoPlanWorkspace.saveNote('${noteTaskId}')"
                                        class="px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#D99E87] hover:bg-[#C98E77] text-white shadow-sm transition cursor-pointer">
                                    Save note
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        return '';
    }

    function selectRescheduleWindow(date) {
        rescheduleSelectedWindow = date;
    }

    function getRescheduleSelectedWindow() {
        return rescheduleSelectedWindow;
    }

    function updateTaskName(taskId, newName) {
        if (!newName || !newName.trim()) return;
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        const pt = plan.plannedTasks.find(item => item.task && item.task.id === taskId);
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }
        if (!task) return;

        task.name = newName.trim();

        // Sync with shared tasks array
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getTasks === 'function') {
            const raw = window.TempoEmergencyFlow.getTasks();
            const shared = raw.find(t => t.id === taskId);
            if (shared) shared.name = task.name;
        }

        persistPlan(plan);
        render();
    }

    function saveTaskDeadline(taskId, newDate, newTime, hasDeadline = true) {
        const plan = getActivePlan();
        if (!plan) return;
        const task = (plan.tasks || []).find(t => t.id === taskId) ||
                     (plan.plannedTasks || []).map(pt => pt.task).find(t => t && t.id === taskId) ||
                     (plan.unarrangedTasks || []).map(u => u.task).find(t => t && t.id === taskId);
        if (task) {
            task.deadlineDate = newDate;
            task.deadlineTime = newTime;
            task.hasDeadline = hasDeadline;
            task.deadline = hasDeadline ? `${newDate} ${newTime || '23:59'}` : null;
            persistPlan(plan);
            render();
        }
    }

    function scheduleUnarrangedTask(taskId, targetDate, startTime, endTime) {
        const plan = getActivePlan();
        if (!plan) return;
        const unarrangedIdx = (plan.unarrangedTasks || []).findIndex(u => (u && u.task ? u.task.id : u.id) === taskId);
        if (unarrangedIdx === -1) return;
        const [removed] = plan.unarrangedTasks.splice(unarrangedIdx, 1);
        const task = removed && removed.task ? removed.task : removed;
        task.planBadge = 'LATER';
        plan.plannedTasks.push({
            dayDate: targetDate,
            dayLabel: targetDate,
            task: task,
            allocatedMinutes: task.durationMinutes || 45,
            scheduledStartTime: startTime || '14:00',
            scheduledEndTime: endTime || '15:00',
            planPositionBadge: 'LATER',
            hasDeadlineRisk: false
        });
        persistPlan(plan);
        render();
    }

    function addNewTask(taskData) {
        const plan = getActivePlan();
        if (!plan) return;
        const taskId = 'task-' + Date.now();
        const newTask = {
            id: taskId,
            name: taskData.name || 'New Task',
            deadlineDate: taskData.deadlineDate || null,
            deadlineTime: taskData.deadlineTime || null,
            deadline: taskData.deadlineDate ? `${taskData.deadlineDate} ${taskData.deadlineTime || '23:59'}` : null,
            hasDeadline: !!taskData.deadlineDate,
            durationMinutes: taskData.estimateMinutes || 45,
            durationLabel: `${taskData.estimateMinutes || 45}m`,
            completed: false,
            isInProgress: false,
            subtasks: []
        };
        if (!plan.tasks) plan.tasks = [];
        plan.tasks.push(newTask);
        if (taskData.fitIntoPlan) {
            plan.plannedTasks.push({
                dayDate: getTodayISO(),
                dayLabel: 'TODAY',
                task: newTask,
                allocatedMinutes: newTask.durationMinutes,
                scheduledStartTime: '16:00',
                scheduledEndTime: '17:00',
                planPositionBadge: 'LATER',
                hasDeadlineRisk: false
            });
        } else {
            if (!plan.unarrangedTasks) plan.unarrangedTasks = [];
            plan.unarrangedTasks.push({
                task: newTask,
                isUnarranged: true,
                reason: 'Unscheduled'
            });
        }
        persistPlan(plan);
        render();
        return newTask;
    }

    if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
        window.TempoI18n.onLanguageChange(() => {
            const wsScreen = document.getElementById('screen-plan-workspace');
            if (wsScreen && !wsScreen.classList.contains('hidden')) {
                render();
            }
        });
    }

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (activeModal === 'clear-task-confirm') {
                closeClearTaskConfirm();
            } else if (activeModal === 'delete-plan-confirm') {
                closeDeletePlanConfirm();
            } else if (activeModal === 'deadline-plan-reorder-confirm') {
                cancelDeadlineConfirm();
            } else if (activeModal === 'edit-task-note') {
                closeModal();
            }
        }
    });

    document.addEventListener('click', function(e) {
        if (activeLabelMenuTaskId) {
            const insideMenu = e.target && e.target.closest && e.target.closest('[data-label-menu-container]');
            if (!insideMenu) {
                activeLabelMenuTaskId = null;
                render();
            }
        }
    });

    return {
        startAdjustPlan,
        promptDeletePlan,
        closeDeletePlanConfirm,
        executeDeletePlan,
        deletePlan,
        toggleAddSubtaskInput,
        getActivePlan,
        open,
        render,
        navigateHome,
        startGlobalFocus,
        startTaskFocus,
        toggleTaskComplete,
        selectTask,
        closeDrawer,
        toggleDeadlineEdit,
        saveDeadlineEdit,
        saveTaskDeadline,
        openEstimateEdit,
        promptClearTask,
        closeClearTaskConfirm,
        executeClearTask,
        removeTask,
        addSubtask,
        removeSubtask,
        toggleSubtask,
        setSubtaskCompleted,
        reorderDrawerSubtask,
        handleDragStart,
        handleDragOver,
        handleDragEnter,
        handleDragLeave,
        handleDrop,
        handleDragEnd,
        clearTaskDragStyles,
        isDraggingTask: () => isDraggingTask,
        reorderTasks,
        openRescheduleModal,
        closeRescheduleModal,
        selectRescheduleWindow,
        getRescheduleSelectedWindow,
        scheduleTaskAsUnarranged,
        scheduleUnarrangedTask,
        executeReschedule,
        openAddTaskModal,
        closeAddTaskModal,
        submitAddTask,
        handleFitTaskChoice,
        addNewTask,
        openAdjustAvailabilityModal,
        closeAdjustAvailabilityModal,
        addAvailabilityBlockInline,
        removeAvailabilityBlock,
        updateTaskName,
        // Label & AI Replan
        toggleLabelMenu,
        setTaskLabel,
        // Deadline Confirmation Modal
        confirmDeadlineWithReorder,
        confirmDeadlineWithoutReorder,
        cancelDeadlineConfirm,
        // Break Task
        openBreakTaskModal,
        // Task Notes
        openNoteEditor,
        saveNote,
        deleteNote,
        closeModal
    };
})();
