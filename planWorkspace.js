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
    let activeModal = null; // null | 'add-task' | 'fit-task-prompt' | 'adjust-availability' | 'reschedule'
    let pendingAddedTask = null;
    let rescheduleTaskId = null;
    let rescheduleSelectedWindow = null;
    let rescheduleShowAddTime = false;
    let adjustAvailShowAdd = false;

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

    // Helper: Human deadline
    function formatDeadline(dateStr, timeStr) {
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

    // Load active plan from TempoPlanStore or TempoEmergencyFlow
    function getActivePlan() {
        let plan = null;
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            plan = window.TempoEmergencyFlow.getConfirmedPlan();
        }
        if (!plan && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            plan = window.TempoPlanStore.getActivePlan('emergency');
        }
        if (plan) {
            if (!Array.isArray(plan.plannedTasks)) plan.plannedTasks = [];
            if (!Array.isArray(plan.unarrangedTasks)) plan.unarrangedTasks = [];
            if (!Array.isArray(plan.tasks)) plan.tasks = [];
        }
        return plan;
    }

    // Save active plan to TempoPlanStore
    function persistPlan(plan) {
        if (!plan) return;
        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            window.TempoPlanStore.saveActivePlan('emergency', plan);
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
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('today');
        } else {
            window.location.hash = '#today';
        }
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
        if (e) e.stopPropagation();
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        const pt = plan.plannedTasks.find(item => item.task && item.task.id === taskId);
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }

        if (task) {
            task.completed = !task.completed;
            if (task.completed) {
                task.isInProgress = false;
                task.executionStatus = 'completed';
            } else {
                task.executionStatus = 'pending';
            }

            // Sync with TempoEmergencyFlow
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.toggleTaskCompleted === 'function') {
                window.TempoEmergencyFlow.toggleTaskCompleted(taskId);
            }

            // Sync with planStore
            if (window.TempoPlanStore && typeof window.TempoPlanStore.updateTaskState === 'function') {
                window.TempoPlanStore.updateTaskState(taskId, {
                    completed: task.completed,
                    isInProgress: task.isInProgress,
                    executionStatus: task.executionStatus
                });
            }

            persistPlan(plan);
            render();
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
        renderDrawer();
    }

    /**
     * Save inline deadline edit
     */
    function saveDeadlineEdit(taskId) {
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        const pt = plan.plannedTasks.find(item => item.task && item.task.id === taskId);
        if (pt) task = pt.task;
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

        if (hasNoFixed) {
            task.hasDeadline = false;
            task.deadlineDate = null;
            task.deadlineTime = null;
        } else {
            task.hasDeadline = !!dateVal;
            task.deadlineDate = dateVal || null;
            task.deadlineTime = timeVal || '23:59';
        }

        // Update shared task in tasks array
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getTasks === 'function') {
            const rawTasks = window.TempoEmergencyFlow.getTasks();
            const shared = rawTasks.find(t => t.id === taskId);
            if (shared) {
                shared.hasDeadline = task.hasDeadline;
                shared.deadlineDate = task.deadlineDate;
                shared.deadlineTime = task.deadlineTime;
            }
        }

        // Recheck deadline conflicts without reordering
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
            window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
        }

        persistPlan(plan);
        isEditingDeadline = false;
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
    function removeTask(taskId) {
        if (!confirm("Are you sure you want to remove this task from your Urgent Plan?")) return;

        const plan = getActivePlan();
        if (!plan) return;

        // Check plannedTasks
        const ptIdx = plan.plannedTasks.findIndex(pt => pt.task && pt.task.id === taskId);
        if (ptIdx !== -1) {
            plan.plannedTasks.splice(ptIdx, 1);
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
                window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
            }
        }

        // Check unarrangedTasks
        const unIdx = plan.unarrangedTasks ? plan.unarrangedTasks.findIndex(t => t.id === taskId) : -1;
        if (unIdx !== -1) {
            plan.unarrangedTasks.splice(unIdx, 1);
        }

        if (selectedTaskId === taskId) {
            selectedTaskId = null;
        }

        persistPlan(plan);
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

    function toggleSubtask(taskId, subtaskId) {
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        const pt = plan.plannedTasks.find(item => item.task && item.task.id === taskId);
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }
        if (!task || !task.subtasks) return;

        const sub = task.subtasks.find(s => s.id === subtaskId);
        if (sub) {
            sub.completed = !sub.completed;
            persistPlan(plan);
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
     * MAIN RENDER FUNCTION
     */
    function render() {
        const root = document.getElementById('plan-workspace-root');
        if (!root) return;

        const plan = getActivePlan();
        if (!plan || (!plan.plannedTasks && !plan.unarrangedTasks)) {
            root.innerHTML = `
                <div class="max-w-xl mx-auto py-16 text-center space-y-5">
                    <div class="w-16 h-16 rounded-3xl bg-[#FFE9DC] text-[#FF6B2C] flex items-center justify-center text-3xl mx-auto shadow-sm">
                        📋
                    </div>
                    <div class="space-y-1.5">
                        <h2 class="font-heading text-2xl font-bold text-[#202124]">No active Urgent Plan found</h2>
                        <p class="text-xs sm:text-sm text-[#6F6B68]">
                            You don't have an active Urgent Plan right now. Create one to get clear, realistic guidance.
                        </p>
                    </div>
                    <div class="pt-2 flex items-center justify-center gap-3">
                        <button onclick="window.TempoPlanWorkspace.navigateHome()" class="px-5 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 bg-white hover:bg-stone-50 transition">
                            ← Home
                        </button>
                        <button onclick="window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('entry');" class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs shadow-md transition">
                            Create an Urgent Plan →
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        const plannedTasks = plan.plannedTasks || [];
        const unarrangedTasks = (plan.unarrangedTasks || []).map(u => (u && u.task ? u.task : u));

        // Real Summary Metrics
        const totalTasksCount = plannedTasks.length + unarrangedTasks.length;
        const completedTasksCount = plannedTasks.filter(pt => pt.task && pt.task.completed).length +
                                    unarrangedTasks.filter(t => t.completed).length;

        let totalFocusedMinutes = 0;
        let unestimatedTasksCount = 0;

        plannedTasks.forEach(pt => {
            if (pt.task) {
                if (pt.task.durationMinutes && pt.task.durationMinutes > 0) {
                    totalFocusedMinutes += pt.task.durationMinutes;
                } else {
                    unestimatedTasksCount++;
                }
            }
        });
        unarrangedTasks.forEach(t => {
            if (t.durationMinutes && t.durationMinutes > 0) {
                totalFocusedMinutes += t.durationMinutes;
            } else {
                unestimatedTasksCount++;
            }
        });

        const durationSummary = `~${formatDuration(totalFocusedMinutes)} focused work${unestimatedTasksCount > 0 ? ` (+${unestimatedTasksCount} unestimated)` : ''}`;

        // Group arranged tasks by date
        const todayStr = getTodayISO();
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const tomorrowStr = tomorrow.toISOString().split('T')[0];

        const daysMap = {};
        plannedTasks.forEach((item, globalIdx) => {
            item.globalIndex = globalIdx;
            const dDate = item.dayDate || 'unscheduled';
            let dLabel = item.dayLabel || dDate;
            if (dDate === todayStr) dLabel = 'TODAY';
            else if (dDate === tomorrowStr) dLabel = 'TOMORROW';

            if (!daysMap[dDate]) {
                daysMap[dDate] = { label: dLabel, date: dDate, items: [] };
            }
            daysMap[dDate].items.push(item);
        });

        // Separate active vs completed
        const completedArranged = plannedTasks.filter(pt => pt.task && pt.task.completed);
        const completedUnarranged = unarrangedTasks.filter(t => t.completed);
        const allCompleted = [...completedArranged.map(pt => pt.task), ...completedUnarranged];

        // Is drawer active?
        const isDrawerOpen = !!selectedTaskId;
        let selectedTask = null;
        let selectedPlanItem = null;

        if (selectedTaskId) {
            selectedPlanItem = plannedTasks.find(pt => pt.task && pt.task.id === selectedTaskId);
            if (selectedPlanItem) selectedTask = selectedPlanItem.task;
            if (!selectedTask) {
                selectedTask = unarrangedTasks.find(t => t.id === selectedTaskId);
            }
        }

        root.innerHTML = `
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
                <!-- TOP HEADER -->
                <div class="space-y-4 pb-4 border-b border-[#EAE4DF]">
                    <div class="flex items-center justify-between">
                        <!-- Navigation: Strictly "← Home" -->
                        <button id="plan-workspace-back-home"
                                onclick="window.TempoPlanWorkspace.navigateHome()" 
                                class="text-xs font-semibold text-[#6F6B68] hover:text-[#202124] flex items-center space-x-1.5 transition py-1 group"
                                title="Return to Home Dashboard">
                            <span class="group-hover:-translate-x-0.5 transition-transform">←</span>
                            <span>Home</span>
                        </button>
                    </div>

                    <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
                        <div class="space-y-1">
                            <span class="text-[11px] font-extrabold uppercase tracking-widest text-[#FF6B2C] block">YOUR URGENT PLAN</span>
                            <h1 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                                Here's what you're working through right now.
                            </h1>
                            <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[#6F6B68] font-medium pt-1">
                                <span>${totalTasksCount} task${totalTasksCount === 1 ? '' : 's'}</span>
                                <span>•</span>
                                <span>${durationSummary}</span>
                                <span>•</span>
                                <span>${completedTasksCount} completed</span>
                            </div>
                        </div>

                        <!-- Header Action CTAs -->
                        <div class="flex flex-wrap items-center gap-2.5 shrink-0">
                            <!-- Primary: Start Focus Now -->
                            <button id="plan-workspace-start-focus"
                                    onclick="window.TempoPlanWorkspace.startGlobalFocus()"
                                    class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-md inline-flex items-center space-x-2 transition">
                                <span>▶ Start Focus Now</span>
                            </button>
                            <!-- Secondary: Add Task -->
                            <button onclick="window.TempoPlanWorkspace.openAddTaskModal()"
                                    class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 bg-white hover:bg-stone-50 transition">
                                + Add task
                            </button>
                            <!-- Secondary: Adjust Availability -->
                            <button onclick="window.TempoPlanWorkspace.openAdjustAvailabilityModal()"
                                    class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 bg-white hover:bg-stone-50 transition">
                                Adjust availability
                            </button>
                        </div>
                    </div>
                </div>

                <!-- MAIN WORKSPACE LAYOUT (Timeline | Drawer) -->
                <div class="grid grid-cols-1 ${isDrawerOpen ? 'lg:grid-cols-12' : ''} gap-8 items-start">
                    <!-- TIMELINE COLUMN -->
                    <div class="${isDrawerOpen ? 'lg:col-span-7' : 'max-w-4xl mx-auto w-full'} space-y-8">
                        ${Object.keys(daysMap).map(dDate => {
                            const group = daysMap[dDate];
                            const activeItems = group.items.filter(pt => pt.task && !pt.task.completed);

                            if (activeItems.length === 0 && group.items.length > 0) {
                                // All items in this day completed
                                return `
                                    <div class="space-y-3">
                                        <div class="flex items-center justify-between pb-1 border-b border-gray-200/80">
                                            <h3 class="font-heading text-xs font-bold uppercase tracking-wider text-[#6F6B68]">
                                                ${escapeHTML(group.label)} · ${escapeHTML(group.date)}
                                            </h3>
                                            <span class="text-[11px] font-semibold text-emerald-700">All planned work done ✓</span>
                                        </div>
                                    </div>
                                `;
                            }

                            return `
                                <div class="space-y-4">
                                    <!-- Day Header -->
                                    <div class="flex items-center justify-between pb-1 border-b border-gray-200/80">
                                        <div class="flex items-center space-x-2">
                                            <span class="w-2.5 h-2.5 rounded-full bg-[#FF6B2C]"></span>
                                            <h3 class="font-heading text-xs font-bold uppercase tracking-wider text-[#202124]">
                                                ${escapeHTML(group.label)} · ${escapeHTML(group.date)}
                                            </h3>
                                        </div>
                                        <span class="text-[11px] font-medium text-[#6F6B68]">
                                            ${activeItems.length} active task${activeItems.length === 1 ? '' : 's'}
                                        </span>
                                    </div>

                                    <!-- Tasks in Day -->
                                    <div class="space-y-3">
                                        ${activeItems.map((item, idx) => {
                                            const task = item.task;
                                            const isSelected = selectedTaskId === task.id;
                                            const badgeLabel = item.planPositionBadge || (item.globalIndex === 0 ? 'DO THIS' : (item.globalIndex === 1 ? 'THEN' : 'LATER'));
                                            const badgeClass = badgeLabel === 'DO THIS' ? 'bg-[#FFE9DC] text-[#B83D08]' : (badgeLabel === 'THEN' ? 'bg-orange-100 text-[#B83D08]' : 'bg-stone-100 text-stone-700');
                                            const subtaskCount = Array.isArray(task.subtasks) ? task.subtasks.length : 0;
                                            const completedSubtasks = Array.isArray(task.subtasks) ? task.subtasks.filter(s => s.completed).length : 0;

                                            return `
                                                <div class="p-4 sm:p-5 rounded-2xl border transition-all cursor-pointer ${isSelected ? 'border-2 border-[#FF6B2C] bg-[#FFFBF8] shadow-sm' : 'border-[#EAE4DF] bg-white hover:border-gray-300 shadow-xs'}"
                                                     onclick="window.TempoPlanWorkspace.selectTask('${task.id}')">
                                                    <!-- Top Card Meta Row -->
                                                    <div class="flex items-center justify-between gap-2 pb-2">
                                                        <div class="flex items-center space-x-2 min-w-0">
                                                            <!-- Drag Handle -->
                                                            <div class="cursor-grab text-gray-400 hover:text-gray-700 px-1 py-0.5 rounded text-xs select-none" title="Drag to reorder">
                                                                ⋮⋮
                                                            </div>
                                                            <!-- Checkbox -->
                                                            <button type="button" 
                                                                    onclick="window.TempoPlanWorkspace.toggleTaskComplete('${task.id}', event)"
                                                                    class="w-5 h-5 rounded-lg border flex items-center justify-center text-xs font-bold transition shrink-0 ${task.completed ? 'bg-emerald-600 border-emerald-600 text-white' : 'border-stone-300 hover:border-[#FF6B2C] bg-white text-transparent'}"
                                                                    title="Mark complete">
                                                                ✓
                                                            </button>
                                                            <!-- Plan Position Badge -->
                                                            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider ${badgeClass} shrink-0">
                                                                ${badgeLabel}
                                                            </span>
                                                        </div>

                                                        <!-- Scheduled Time -->
                                                        <div class="text-right shrink-0">
                                                            ${(item.startTime || item.scheduledStartTime) && (item.endTime || item.scheduledEndTime) ? `
                                                                <span class="text-xs font-bold text-[#202124]">
                                                                    ${item.startTime || item.scheduledStartTime} – ${item.endTime || item.scheduledEndTime}
                                                                </span>
                                                            ` : `
                                                                <span class="text-xs font-medium text-[#6F6B68]">
                                                                    ~${task.durationLabel || 'Flexible'}
                                                                </span>
                                                            `}
                                                        </div>
                                                    </div>

                                                    <!-- Task Title & Badges -->
                                                    <div class="space-y-1 pt-1">
                                                        <div class="flex items-baseline justify-between gap-3">
                                                            <h4 class="font-heading text-base font-bold text-[#202124] ${task.completed ? 'line-through text-gray-400' : ''}">
                                                                ${escapeHTML(task.name)}
                                                            </h4>
                                                        </div>

                                                        <!-- Meta Info Line -->
                                                        <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-[#6F6B68]">
                                                            <span>Estimate: ~${task.durationLabel || 'Flexible'}</span>
                                                            <span>•</span>
                                                            <span>Due: ${formatDeadline(task.deadlineDate || task.deadline, task.deadlineTime)}</span>
                                                            ${subtaskCount > 0 ? `
                                                                <span>•</span>
                                                                <span>${completedSubtasks}/${subtaskCount} action steps</span>
                                                            ` : ''}
                                                        </div>
                                                    </div>

                                                    <!-- Deadline Warning if flagged -->
                                                    ${item.hasDeadlineConflict ? `
                                                        <div class="mt-2.5 p-2 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-center space-x-1.5">
                                                            <span>⚠️</span>
                                                            <span><strong>May finish after deadline</strong></span>
                                                        </div>
                                                    ` : ''}

                                                    <!-- Bottom Action Row -->
                                                    <div class="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between">
                                                        <div class="flex items-center space-x-2">
                                                            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${task.completed ? 'bg-emerald-100 text-emerald-800' : (task.isInProgress ? 'bg-amber-100 text-amber-800' : 'bg-stone-100 text-stone-600')}">
                                                                ${task.completed ? '✓ Completed' : (task.isInProgress ? '● In progress' : 'Not started')}
                                                            </span>
                                                        </div>

                                                        <div class="flex items-center space-x-2">
                                                            <button type="button" 
                                                                    onclick="event.stopPropagation(); window.TempoPlanWorkspace.startTaskFocus('${task.id}')"
                                                                    class="btn-primary px-3.5 py-1.5 rounded-xl font-bold text-xs shadow-xs inline-flex items-center space-x-1 transition">
                                                                <span>${task.isInProgress ? 'Continue Focus' : 'Start'}</span>
                                                                <span>→</span>
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            `;
                                        }).join('')}
                                    </div>

                                    <!-- Add another task button -->
                                    <button onclick="window.TempoPlanWorkspace.openAddTaskModal()"
                                            class="w-full py-2.5 rounded-xl border border-dashed border-stone-300 hover:border-[#FF6B2C] text-xs font-semibold text-stone-600 hover:text-[#FF6B2C] bg-[#FFFDFB] hover:bg-white transition flex items-center justify-center space-x-1">
                                        <span>+ Add another task to this plan</span>
                                    </button>
                                </div>
                            `;
                        }).join('')}

                        <!-- NOT SCHEDULED YET (UNARRANGED SECTION) -->
                        <div class="space-y-4 pt-4 border-t border-gray-200">
                            <div class="flex items-center justify-between pb-1">
                                <h3 class="font-heading text-xs font-bold uppercase tracking-wider text-[#6F6B68]">
                                    NOT SCHEDULED YET
                                </h3>
                                <span class="text-[11px] font-medium text-[#6F6B68]">
                                    ${unarrangedTasks.filter(t => !t.completed).length} unscheduled
                                </span>
                            </div>

                            ${unarrangedTasks.filter(t => !t.completed).length === 0 ? `
                                <div class="p-4 bg-stone-50 border border-dashed border-[#EAE4DF] rounded-2xl text-center text-xs text-[#8E8A85]">
                                    All active tasks have been placed into your schedule.
                                </div>
                            ` : `
                                <div class="space-y-3">
                                    ${unarrangedTasks.filter(t => !t.completed).map(task => `
                                        <div class="p-4 rounded-2xl border border-stone-200 bg-white hover:border-[#FF6B2C]/50 transition flex items-center justify-between gap-3 shadow-xs cursor-pointer"
                                             onclick="window.TempoPlanWorkspace.selectTask('${task.id}')">
                                            <div class="min-w-0 pr-2">
                                                <h4 class="font-bold text-sm text-[#202124] truncate">${escapeHTML(task.name)}</h4>
                                                <div class="flex items-center space-x-2 text-[11px] text-[#6F6B68] pt-0.5">
                                                    <span>Estimate: ~${task.durationLabel || 'Flexible'}</span>
                                                    <span>•</span>
                                                    <span>Due: ${formatDeadline(task.deadlineDate || task.deadline, task.deadlineTime)}</span>
                                                </div>
                                            </div>
                                            <button type="button" 
                                                    onclick="event.stopPropagation(); window.TempoPlanWorkspace.openRescheduleModal('${task.id}')"
                                                    class="btn-primary px-3.5 py-1.5 rounded-xl font-bold text-xs shadow-xs shrink-0 transition">
                                                Schedule task →
                                            </button>
                                        </div>
                                    `).join('')}
                                </div>
                            `}
                        </div>

                        <!-- COMPLETED TASKS COLLAPSIBLE SECTION -->
                        ${allCompleted.length > 0 ? `
                            <div class="pt-4 border-t border-gray-200">
                                <details class="group bg-white border border-[#EAE4DF] rounded-2xl p-4 transition-all">
                                    <summary class="flex items-center justify-between cursor-pointer font-heading text-xs font-bold text-[#6F6B68] uppercase tracking-wider select-none">
                                        <span class="flex items-center space-x-2">
                                            <span>✓</span>
                                            <span>COMPLETED (${allCompleted.length})</span>
                                        </span>
                                        <span class="text-xs group-open:rotate-180 transition-transform">▼</span>
                                    </summary>
                                    <div class="pt-3 space-y-2">
                                        ${allCompleted.map(task => `
                                            <div class="p-2.5 bg-stone-50 rounded-xl border border-stone-200 flex items-center justify-between text-xs opacity-75">
                                                <div class="flex items-center space-x-2 min-w-0">
                                                    <span class="text-emerald-600 font-bold">✓</span>
                                                    <span class="line-through text-stone-500 font-medium truncate">${escapeHTML(task.name)}</span>
                                                </div>
                                                <button type="button" 
                                                        onclick="window.TempoPlanWorkspace.toggleTaskComplete('${task.id}', event)"
                                                        class="text-[11px] text-stone-500 hover:text-[#202124] underline">
                                                    Undo
                                                </button>
                                            </div>
                                        `).join('')}
                                    </div>
                                </details>
                            </div>
                        ` : ''}
                    </div>

                    <!-- TASK DETAIL DRAWER COLUMN (Desktop side drawer / Mobile modal) -->
                    ${isDrawerOpen && selectedTask ? `
                        <div id="plan-workspace-drawer" class="lg:col-span-5 fixed inset-0 z-50 bg-black/40 lg:bg-transparent lg:static lg:z-auto flex justify-end">
                            <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 space-y-5 shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto lg:sticky lg:top-24">
                                <!-- Drawer Header -->
                                <div class="flex items-center justify-between pb-3 border-b border-gray-100">
                                    <div class="flex items-center space-x-2">
                                        <span class="text-sm font-bold tracking-widest text-gray-400">⋮⋮</span>
                                        <h3 class="font-heading text-base font-bold text-[#202124]">Edit Task</h3>
                                    </div>
                                    <button onclick="window.TempoPlanWorkspace.closeDrawer()" 
                                            class="text-gray-400 hover:text-gray-600 p-1 text-sm font-bold"
                                            title="Close drawer">✕</button>
                                </div>

                                <!-- Task Title & Completion -->
                                <div class="space-y-2">
                                    <div class="flex items-start space-x-3">
                                        <button type="button" 
                                                onclick="window.TempoPlanWorkspace.toggleTaskComplete('${selectedTask.id}', event)"
                                                class="w-6 h-6 rounded-lg border mt-0.5 flex items-center justify-center text-xs font-bold transition shrink-0 ${selectedTask.completed ? 'bg-emerald-600 border-emerald-600 text-white' : 'border-stone-300 hover:border-[#FF6B2C] bg-white text-transparent'}">
                                            ✓
                                        </button>
                                        <div class="flex-1">
                                            <input id="pw-drawer-task-name" 
                                                   type="text" 
                                                   value="${escapeHTML(selectedTask.name)}"
                                                   onblur="window.TempoPlanWorkspace.updateTaskName('${selectedTask.id}', this.value)"
                                                   class="font-heading text-lg font-bold text-[#202124] w-full px-2 py-1 border border-transparent hover:border-gray-200 focus:border-[#FF6B2C] rounded-lg focus:outline-none">
                                        </div>
                                    </div>
                                    <div class="flex items-center space-x-2 pl-9 text-xs">
                                        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${selectedTask.completed ? 'bg-emerald-100 text-emerald-800' : (selectedTask.isInProgress ? 'bg-amber-100 text-amber-800' : 'bg-stone-100 text-stone-700')}">
                                            ${selectedTask.completed ? 'COMPLETED' : (selectedTask.isInProgress ? 'IN PROGRESS' : 'NOT STARTED')}
                                        </span>
                                    </div>
                                </div>

                                <!-- SCHEDULED TIME -->
                                <div class="p-3.5 bg-stone-50 rounded-2xl space-y-1.5 border border-stone-100 text-xs">
                                    <div class="flex items-center justify-between">
                                        <span class="text-[10px] font-bold uppercase tracking-wider text-gray-400">SCHEDULED</span>
                                        <button onclick="window.TempoPlanWorkspace.openRescheduleModal('${selectedTask.id}')"
                                                class="text-xs font-semibold text-[#FF6B2C] hover:underline">
                                            Reschedule
                                        </button>
                                    </div>
                                    <p class="font-bold text-stone-800">
                                        ${selectedPlanItem && (selectedPlanItem.startTime || selectedPlanItem.scheduledStartTime) && (selectedPlanItem.endTime || selectedPlanItem.scheduledEndTime) ? 
                                            `${selectedPlanItem.dayLabel || selectedPlanItem.dayDate} · ${selectedPlanItem.startTime || selectedPlanItem.scheduledStartTime} – ${selectedPlanItem.endTime || selectedPlanItem.scheduledEndTime}` : 
                                            'Not scheduled yet'}
                                    </p>
                                </div>

                                <!-- DEADLINE (INLINE EDIT) -->
                                <div class="p-3.5 bg-stone-50 rounded-2xl space-y-2 border border-stone-100 text-xs">
                                    <div class="flex items-center justify-between">
                                        <span class="text-[10px] font-bold uppercase tracking-wider text-gray-400">DEADLINE</span>
                                        <button onclick="window.TempoPlanWorkspace.toggleDeadlineEdit()"
                                                class="text-xs font-semibold text-[#FF6B2C] hover:underline">
                                            ${isEditingDeadline ? 'Cancel' : 'Edit'}
                                        </button>
                                    </div>

                                    ${!isEditingDeadline ? `
                                        <p class="font-bold text-stone-800">
                                            ${formatDeadline(selectedTask.deadlineDate || selectedTask.deadline, selectedTask.deadlineTime)}
                                        </p>
                                    ` : `
                                        <div class="space-y-2 pt-1">
                                            <div class="grid grid-cols-2 gap-2">
                                                <div>
                                                    <label class="block text-[10px] text-gray-500 font-semibold mb-0.5">Date</label>
                                                    <input id="pw-edit-deadline-date" type="date" value="${selectedTask.deadlineDate || (selectedTask.deadline ? selectedTask.deadline.split(' ')[0] : '')}"
                                                           class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                                </div>
                                                <div>
                                                    <label class="block text-[10px] text-gray-500 font-semibold mb-0.5">Time</label>
                                                    <input id="pw-edit-deadline-time" type="time" value="${selectedTask.deadlineTime || (selectedTask.deadline ? selectedTask.deadline.split(' ')[1] : '23:59')}"
                                                           class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                                </div>
                                            </div>
                                            <div class="flex items-center space-x-2">
                                                <input id="pw-edit-no-deadline" type="checkbox" ${!selectedTask.hasDeadline ? 'checked' : ''}
                                                       class="rounded text-[#FF6B2C] focus:ring-[#FF6B2C]">
                                                <label for="pw-edit-no-deadline" class="text-xs text-stone-700">No fixed deadline</label>
                                            </div>
                                            <div class="flex justify-end space-x-2 pt-1">
                                                <button onclick="window.TempoPlanWorkspace.saveDeadlineEdit('${selectedTask.id}')"
                                                        class="btn-primary px-3 py-1 rounded-lg text-xs font-bold">
                                                    Save deadline
                                                </button>
                                            </div>
                                        </div>
                                    `}
                                </div>

                                <!-- ESTIMATE -->
                                <div class="p-3.5 bg-stone-50 rounded-2xl space-y-1.5 border border-stone-100 text-xs">
                                    <div class="flex items-center justify-between">
                                        <span class="text-[10px] font-bold uppercase tracking-wider text-gray-400">ESTIMATE</span>
                                        <button onclick="window.TempoPlanWorkspace.openEstimateEdit('${selectedTask.id}')"
                                                class="text-xs font-semibold text-[#FF6B2C] hover:underline">
                                            Edit
                                        </button>
                                    </div>
                                    <p class="font-bold text-stone-800">
                                        ~${selectedTask.durationLabel || 'Flexible focused work'}
                                    </p>
                                </div>

                                <!-- ACTION STEPS (SUBTASKS) -->
                                <div class="space-y-2 pt-2">
                                    <div class="flex items-center justify-between">
                                        <span class="text-xs font-bold text-[#202124] uppercase tracking-wider">
                                            ACTION STEPS (${selectedTask.subtasks ? selectedTask.subtasks.length : 0})
                                        </span>
                                    </div>

                                    <div class="space-y-2">
                                        ${(selectedTask.subtasks || []).map((step, sIdx) => `
                                            <div class="p-2.5 bg-[#FFFDFB] border border-[#EAE4DF] rounded-xl flex items-center justify-between gap-2 text-xs">
                                                <div class="flex items-center space-x-2 min-w-0">
                                                    <span class="text-gray-300 font-bold text-xs select-none">⋮⋮</span>
                                                    <button type="button" 
                                                            onclick="window.TempoPlanWorkspace.toggleSubtask('${selectedTask.id}', '${step.id}')"
                                                            class="w-4 h-4 rounded border flex items-center justify-center text-[10px] font-bold transition shrink-0 ${step.completed ? 'bg-emerald-600 border-emerald-600 text-white' : 'border-stone-300 text-transparent'}">
                                                        ✓
                                                    </button>
                                                    <span class="font-medium text-[#202124] truncate ${step.completed ? 'line-through text-stone-400' : ''}">
                                                        ${escapeHTML(step.title)}
                                                    </span>
                                                </div>
                                                <div class="flex items-center space-x-1.5 shrink-0">
                                                    <span class="text-[10px] font-semibold text-stone-500 bg-stone-100 px-1.5 py-0.5 rounded">
                                                        ${step.durationMinutes || 15}m
                                                    </span>
                                                    <button onclick="window.TempoPlanWorkspace.removeSubtask('${selectedTask.id}', '${step.id}')"
                                                            class="text-stone-400 hover:text-rose-600 px-1 text-xs">✕</button>
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>

                                    <!-- Add Step Input -->
                                    <div class="flex items-center gap-2 pt-1">
                                        <input id="pw-new-subtask-title" type="text" placeholder="Add next step..."
                                               onkeydown="if(event.key === 'Enter') window.TempoPlanWorkspace.addSubtask('${selectedTask.id}')"
                                               class="w-full px-3 py-1.5 text-xs border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-[#FF6B2C]">
                                        <button onclick="window.TempoPlanWorkspace.addSubtask('${selectedTask.id}')"
                                                class="px-3 py-1.5 bg-stone-100 hover:bg-stone-200 text-stone-800 rounded-xl text-xs font-bold shrink-0">
                                            + Add
                                        </button>
                                    </div>
                                </div>

                                <!-- DRAWER ACTIONS FOOTER -->
                                <div class="pt-4 border-t border-gray-100 flex flex-col gap-2.5">
                                    <button onclick="window.TempoPlanWorkspace.startTaskFocus('${selectedTask.id}')"
                                            class="btn-primary w-full py-3 rounded-xl font-bold text-xs sm:text-sm shadow-md transition flex items-center justify-center space-x-1.5">
                                        <span>▶ Start Focus on this task</span>
                                    </button>

                                    <button onclick="window.TempoPlanWorkspace.removeTask('${selectedTask.id}')"
                                            class="w-full py-2 text-xs font-semibold text-rose-600 hover:text-rose-800 hover:bg-rose-50 rounded-xl transition">
                                        Remove from plan
                                    </button>
                                </div>
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>

            <!-- MODALS -->
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
                            <h3 class="font-heading text-lg font-bold text-[#202124]">Add a task</h3>
                            <button onclick="window.TempoPlanWorkspace.closeAddTaskModal()" class="text-gray-400 hover:text-gray-600 text-sm">✕</button>
                        </div>

                        <div class="space-y-4 text-xs">
                            <div class="space-y-1">
                                <label class="block font-bold text-gray-700">Task Name</label>
                                <input id="pw-add-task-name" type="text" placeholder="e.g. Research Literature Review"
                                       class="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-1 focus:ring-[#FF6B2C] focus:outline-none">
                            </div>

                            <div class="space-y-1.5">
                                <label class="block font-bold text-gray-700">Deadline</label>
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
                                    <label for="pw-add-task-no-deadline" class="text-stone-600">No fixed deadline</label>
                                </div>
                            </div>

                            <div class="space-y-1.5">
                                <label class="block font-bold text-gray-700">Focused-work Estimate</label>
                                <div class="flex items-center space-x-2">
                                    <input id="pw-add-task-dur-val" type="number" min="0.5" step="0.5" value="1.5"
                                           class="w-20 px-3 py-1.5 border border-gray-300 rounded-xl text-center font-bold">
                                    <select id="pw-add-task-dur-unit" class="flex-1 px-3 py-1.5 border border-gray-300 rounded-xl bg-white">
                                        <option value="hours" selected>hours</option>
                                        <option value="minutes">minutes</option>
                                    </select>
                                </div>
                                <div class="flex items-center space-x-2 pt-1">
                                    <input id="pw-add-task-dur-not-sure" type="checkbox"
                                           onchange="document.getElementById('pw-add-task-dur-val').disabled = this.checked;"
                                           class="rounded text-[#FF6B2C]">
                                    <label for="pw-add-task-dur-not-sure" class="text-stone-600">Not sure yet</label>
                                </div>
                            </div>
                        </div>

                        <div class="pt-3 border-t border-gray-100 flex items-center justify-end space-x-2">
                            <button onclick="window.TempoPlanWorkspace.closeAddTaskModal()" 
                                    class="px-4 py-2 border border-gray-200 text-xs font-semibold text-gray-600 rounded-xl hover:bg-stone-50">
                                Cancel
                            </button>
                            <button onclick="window.TempoPlanWorkspace.submitAddTask()"
                                    class="btn-primary px-5 py-2 rounded-xl font-bold text-xs shadow-sm">
                                Add task
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
                            <h3 class="font-heading text-lg font-bold text-[#202124]">Task added</h3>
                            <p class="text-xs text-[#6F6B68]">"${escapeHTML(pendingAddedTask.name)}" is ready.</p>
                        </div>

                        <div class="pt-2 space-y-2">
                            <button onclick="window.TempoPlanWorkspace.handleFitTaskChoice('fit')"
                                    class="btn-primary w-full py-3 rounded-xl font-bold text-xs shadow-md transition">
                                Fit it into my plan
                            </button>
                            <button onclick="window.TempoPlanWorkspace.handleFitTaskChoice('unscheduled')"
                                    class="w-full py-2.5 rounded-xl border border-gray-200 bg-white text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                                Leave it unscheduled for now
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
                                <h3 class="font-heading text-lg font-bold text-[#202124]">Reschedule task</h3>
                                <p class="text-xs text-[#6F6B68] truncate max-w-xs">${escapeHTML(task.name)}</p>
                            </div>
                            <button onclick="window.TempoPlanWorkspace.closeRescheduleModal()" class="text-gray-400 hover:text-gray-600 text-sm">✕</button>
                        </div>

                        <div class="space-y-3 text-xs">
                            <span class="block font-bold text-gray-700 uppercase text-[10px] tracking-wider">YOUR AVAILABLE TIME</span>

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
                                                ${d.blocks && d.blocks.length > 0 ? d.blocks.map(b => `${formatTime12H(b.start)} – ${formatTime12H(b.end)}`).join(', ') : 'No time blocks defined'}
                                            </span>
                                        </div>
                                    </label>
                                `).join('')}
                            </div>

                            <!-- I'll figure it out later option -->
                            <div class="pt-2 border-t border-gray-100">
                                <button onclick="window.TempoPlanWorkspace.scheduleTaskAsUnarranged('${task.id}')"
                                        class="w-full py-2.5 rounded-xl border border-dashed border-stone-300 hover:border-[#FF6B2C] bg-stone-50 hover:bg-white text-xs font-semibold text-stone-700 text-center transition">
                                    I'll figure it out later (Move to Unscheduled)
                                </button>
                            </div>
                        </div>

                        <div class="pt-3 border-t border-gray-100 flex items-center justify-end space-x-2">
                            <button onclick="window.TempoPlanWorkspace.closeRescheduleModal()"
                                    class="px-4 py-2 border border-gray-200 text-xs font-semibold text-gray-600 rounded-xl hover:bg-stone-50">
                                Cancel
                            </button>
                            <button onclick="window.TempoPlanWorkspace.executeReschedule('${task.id}', window.TempoPlanWorkspace.getRescheduleSelectedWindow())"
                                    class="btn-primary px-5 py-2 rounded-xl font-bold text-xs shadow-sm">
                                Schedule
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
                            <h3 class="font-heading text-lg font-bold text-[#202124]">Your available time</h3>
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
                                <span class="font-bold text-[#B83D08] block text-[11px] uppercase tracking-wider">+ Add Available Time Window</span>
                                <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                                    <div>
                                        <label class="block text-[10px] text-stone-600 font-semibold mb-0.5">Date</label>
                                        <input id="pw-avail-add-date" type="date" value="${getTodayISO()}"
                                               class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                    </div>
                                    <div>
                                        <label class="block text-[10px] text-stone-600 font-semibold mb-0.5">From</label>
                                        <input id="pw-avail-add-start" type="time" value="18:00"
                                               class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                    </div>
                                    <div>
                                        <label class="block text-[10px] text-stone-600 font-semibold mb-0.5">To</label>
                                        <input id="pw-avail-add-end" type="time" value="22:00"
                                               class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                    </div>
                                </div>
                                <button onclick="window.TempoPlanWorkspace.addAvailabilityBlockInline()"
                                        class="btn-primary w-full py-1.5 rounded-lg text-xs font-bold mt-1">
                                    Add window
                                </button>
                            </div>
                        </div>

                        <div class="pt-3 border-t border-gray-100 flex justify-end">
                            <button onclick="window.TempoPlanWorkspace.closeAdjustAvailabilityModal()"
                                    class="btn-primary px-6 py-2 rounded-xl font-bold text-xs shadow-sm">
                                Done
                            </button>
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

    return {
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
        removeTask,
        addSubtask,
        removeSubtask,
        toggleSubtask,
        reorderDrawerSubtask,
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
        updateTaskName
    };
})();
