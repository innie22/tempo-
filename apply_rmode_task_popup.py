import re

with open('mode.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Verify LF line endings currently
assert '\r\n' not in content, "mode.js has CRLF before modifications!"

modal_code = '''
    // =========================================================================
    // RMODE TASK DETAIL POPUP MODAL (REUSING WORKPLAN TASK DETAIL UI & ACTIONS)
    // =========================================================================

    let activeRmodeDetailTaskId = null;
    let isRmodeDetailEditingTitle = false;
    let isRmodeDetailEditingDeadline = false;
    let isRmodeDetailEditingNote = false;
    let isRmodeDetailLabelMenuOpen = false;
    let isRmodeDetailAddingSubtask = false;
    let editingRmodeSubtaskId = null;

    function formatRmodeDeadline(dateStr, timeStr) {
        if (window.TempoI18n && typeof window.TempoI18n.formatDeadline === 'function') {
            return window.TempoI18n.formatDeadline(dateStr, timeStr);
        }
        if (!dateStr || dateStr === 'No fixed deadline') return 'No fixed deadline';
        if (dateStr.includes(' ') && !timeStr) {
            const parts = dateStr.split(' ');
            dateStr = parts[0];
            timeStr = parts[1];
        }
        try {
            const [y, m, d] = dateStr.split('-').map(Number);
            if (!y || !m || !d) return dateStr;
            const date = new Date(y, m - 1, d);
            const monthDay = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            if (timeStr) {
                let [h, min] = timeStr.split(':').map(Number);
                const ampm = h >= 12 ? 'PM' : 'AM';
                h = h % 12 || 12;
                const minStr = String(min).padStart(2, '0');
                return `${monthDay} - ${h}:${minStr} ${ampm}`;
            }
            return monthDay;
        } catch (e) {
            return dateStr;
        }
    }

    function getRmodeActivePlan() {
        let plan = null;
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.getActivePlan === 'function') {
            plan = window.TempoPlanWorkspace.getActivePlan();
        }
        if (!plan && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            plan = window.TempoPlanStore.getActivePlan('recovery') || window.TempoPlanStore.getActivePlan('emergency');
        }
        if (!plan) {
            try {
                const saved = localStorage.getItem('tempo_working_plan') || localStorage.getItem('tempo_store_active_emergency_guest');
                if (saved) plan = JSON.parse(saved);
            } catch (e) {}
        }
        if (plan) {
            if (!Array.isArray(plan.plannedTasks)) plan.plannedTasks = [];
            if (!Array.isArray(plan.unarrangedTasks)) plan.unarrangedTasks = [];
            if (!Array.isArray(plan.tasks)) plan.tasks = [];
        }
        if (!plan || (plan.plannedTasks.length === 0 && plan.unarrangedTasks.length === 0 && plan.tasks.length === 0)) {
            if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.getDefaultPlan === 'function') {
                plan = window.TempoPlanWorkspace.getDefaultPlan();
            }
        }
        return plan;
    }

    function getRmodeTaskData(taskId) {
        if (!taskId) return null;
        const sTaskId = String(taskId);
        const plan = getRmodeActivePlan();
        let matchedTask = null;
        let matchedPlanItem = null;

        if (plan) {
            if (Array.isArray(plan.plannedTasks)) {
                for (const pt of plan.plannedTasks) {
                    const t = pt.task || pt;
                    if (t && String(t.id) === sTaskId) {
                        matchedTask = t;
                        matchedPlanItem = pt;
                        break;
                    }
                }
            }
            if (!matchedTask && Array.isArray(plan.unarrangedTasks)) {
                for (const u of plan.unarrangedTasks) {
                    const t = u.task || u;
                    if (t && String(t.id) === sTaskId) {
                        matchedTask = t;
                        matchedPlanItem = u;
                        break;
                    }
                }
            }
            if (!matchedTask && Array.isArray(plan.tasks)) {
                for (const t of plan.tasks) {
                    if (t && String(t.id) === sTaskId) {
                        matchedTask = t;
                        break;
                    }
                }
            }
        }

        // If not found in plan collections, check mock fallback definitions
        if (!matchedTask) {
            const mockMap = {
                'rmode-mock-1': 'task-marketing-research',
                'rmode-mock-2': 'task-event-proposal',
                'rmode-mock-3': 'task-edit-video'
            };
            const canonicalId = mockMap[sTaskId] || sTaskId;
            if (canonicalId === 'task-marketing-research') {
                matchedTask = {
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
                    timeHeader: 'Today, 2:00 PM to 4:00 PM',
                    userLabel: 'Now',
                    description: 'Create a sheet to manage references',
                    subtasks: [
                        { id: 'sub-1', title: 'Subtask 1: Outline', completed: false, durationMinutes: 30 },
                        { id: 'sub-2', title: 'Subtask 2: Literature Review', completed: false, durationMinutes: 45 },
                        { id: 'sub-3', title: 'Subtask 3: Research Gap', completed: false, durationMinutes: 30 },
                        { id: 'sub-4', title: 'Subtask 4: Methodology', completed: false, durationMinutes: 20 },
                        { id: 'sub-5', title: 'Subtask 5: Data Analysis', completed: false, durationMinutes: 15 },
                        { id: 'sub-6', title: 'Subtask 6: Summary Report', completed: false, durationMinutes: 10 }
                    ]
                };
            } else if (canonicalId === 'task-event-proposal') {
                matchedTask = {
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
                    timeHeader: 'Today, 5:00 PM to 7:00 PM',
                    userLabel: 'Then',
                    description: 'Coordinate with design team for event collateral',
                    subtasks: [
                        { id: 'sub-ep-1', title: 'Subtask 1: Budget Draft', completed: false, durationMinutes: 45 },
                        { id: 'sub-ep-2', title: 'Subtask 2: Venue Options', completed: false, durationMinutes: 60 },
                        { id: 'sub-ep-3', title: 'Subtask 3: Guest List', completed: false, durationMinutes: 45 }
                    ]
                };
            } else if (canonicalId === 'task-edit-video') {
                matchedTask = {
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
                    timeHeader: 'Tomorrow, 1:00 PM to 5:00 PM',
                    userLabel: 'Later',
                    description: 'Export in 1080p format for social channels',
                    subtasks: []
                };
            }

            // Sync with mock completed state if stored
            try {
                const mockTasks = JSON.parse(localStorage.getItem('tempo_rmode_mock_tasks') || '{}');
                if (matchedTask && typeof mockTasks[matchedTask.id] === 'boolean') {
                    matchedTask.completed = mockTasks[matchedTask.id];
                } else if (matchedTask && typeof mockTasks[sTaskId] === 'boolean') {
                    matchedTask.completed = mockTasks[sTaskId];
                }
            } catch (e) {}
        }

        return { plan, task: matchedTask, plannedItem: matchedPlanItem };
    }

    function persistRmodePlanData(plan, task) {
        if (plan) {
            if (task) {
                let found = false;
                if (Array.isArray(plan.plannedTasks)) {
                    for (const pt of plan.plannedTasks) {
                        const t = pt.task || pt;
                        if (t && String(t.id) === String(task.id)) {
                            found = true;
                            if (pt.task) Object.assign(pt.task, task);
                            break;
                        }
                    }
                }
                if (!found && Array.isArray(plan.unarrangedTasks)) {
                    for (const u of plan.unarrangedTasks) {
                        const t = u.task || u;
                        if (t && String(t.id) === String(task.id)) {
                            found = true;
                            if (u.task) Object.assign(u.task, task);
                            else Object.assign(u, task);
                            break;
                        }
                    }
                }
                if (!found) {
                    if (!Array.isArray(plan.plannedTasks)) plan.plannedTasks = [];
                    plan.plannedTasks.push({
                        dayDate: task.deadlineDate || new Date().toISOString().split('T')[0],
                        dayLabel: 'Today',
                        startTime: '2:00 PM',
                        endTime: '4:00 PM',
                        executionBadge: task.userLabel || 'Now',
                        task: task
                    });
                }
            }

            try {
                localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
            } catch (e) {}

            if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
                window.TempoPlanStore.saveActivePlan('emergency', plan);
                window.TempoPlanStore.saveActivePlan('recovery', plan);
            }
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                window.TempoEmergencyFlow.setConfirmedPlan(plan);
            }
        }

        // Also sync tempo_rmode_mock_tasks if applicable
        if (task) {
            try {
                let mockTasks = JSON.parse(localStorage.getItem('tempo_rmode_mock_tasks') || '{}');
                mockTasks[task.id] = !!task.completed;
                localStorage.setItem('tempo_rmode_mock_tasks', JSON.stringify(mockTasks));
            } catch (e) {}
        }

        renderRmodeHome();
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
        }
    }

    function openRmodeTaskDetailModal(taskId) {
        activeRmodeDetailTaskId = taskId;
        isRmodeDetailEditingTitle = false;
        isRmodeDetailEditingDeadline = false;
        isRmodeDetailEditingNote = false;
        isRmodeDetailLabelMenuOpen = false;
        isRmodeDetailAddingSubtask = false;
        editingRmodeSubtaskId = null;
        renderRmodeTaskDetailModalDOM();
    }

    function closeRmodeTaskDetailModal() {
        activeRmodeDetailTaskId = null;
        isRmodeDetailEditingTitle = false;
        isRmodeDetailEditingDeadline = false;
        isRmodeDetailEditingNote = false;
        isRmodeDetailLabelMenuOpen = false;
        isRmodeDetailAddingSubtask = false;
        editingRmodeSubtaskId = null;
        renderRmodeTaskDetailModalDOM();
    }

    function isRmodeTaskDetailModalOpen() {
        return Boolean(activeRmodeDetailTaskId);
    }

    function renderRmodeTaskDetailModalDOM() {
        const root = document.getElementById('rmode-task-modal-root');
        if (root) {
            root.innerHTML = renderRmodeTaskDetailModalHTML();
        }
    }

    function toggleRmodeDetailTitleEdit() {
        isRmodeDetailEditingTitle = !isRmodeDetailEditingTitle;
        renderRmodeTaskDetailModalDOM();
        if (isRmodeDetailEditingTitle) {
            setTimeout(() => {
                const input = document.getElementById('rmode-edit-title-input');
                if (input) {
                    input.focus();
                    input.select();
                }
            }, 50);
        }
    }

    function saveRmodeDetailTitleEdit(taskId) {
        const input = document.getElementById('rmode-edit-title-input');
        const newTitle = input ? input.value.trim() : '';
        if (!newTitle) return;

        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        taskInfo.task.name = newTitle;
        taskInfo.task.title = newTitle;
        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.name = newTitle;
            taskInfo.plannedItem.task.title = newTitle;
        }

        isRmodeDetailEditingTitle = false;
        persistRmodePlanData(taskInfo.plan, taskInfo.task);
        renderRmodeTaskDetailModalDOM();
    }

    function toggleRmodeDetailDeadlineEdit() {
        isRmodeDetailEditingDeadline = !isRmodeDetailEditingDeadline;
        renderRmodeTaskDetailModalDOM();
    }

    function saveRmodeDetailDeadlineEdit(taskId) {
        const dateInput = document.getElementById('rmode-edit-deadline-date');
        const timeInput = document.getElementById('rmode-edit-deadline-time');
        const noDeadlineInput = document.getElementById('rmode-edit-no-deadline');

        const noDeadline = noDeadlineInput ? noDeadlineInput.checked : false;
        const date = dateInput ? dateInput.value : '';
        const time = timeInput ? timeInput.value : '';

        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        if (noDeadline) {
            taskInfo.task.hasDeadline = false;
            taskInfo.task.deadlineDate = '';
            taskInfo.task.deadlineTime = '';
            taskInfo.task.deadline = 'No fixed deadline';
        } else {
            taskInfo.task.hasDeadline = true;
            taskInfo.task.deadlineDate = date;
            taskInfo.task.deadlineTime = time;
            taskInfo.task.deadline = time ? `${date} ${time}` : date;
        }

        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.hasDeadline = taskInfo.task.hasDeadline;
            taskInfo.plannedItem.task.deadlineDate = taskInfo.task.deadlineDate;
            taskInfo.plannedItem.task.deadlineTime = taskInfo.task.deadlineTime;
            taskInfo.plannedItem.task.deadline = taskInfo.task.deadline;
        }

        isRmodeDetailEditingDeadline = false;
        persistRmodePlanData(taskInfo.plan, taskInfo.task);
        renderRmodeTaskDetailModalDOM();
    }

    function toggleRmodeDetailNoteEdit() {
        isRmodeDetailEditingNote = !isRmodeDetailEditingNote;
        renderRmodeTaskDetailModalDOM();
        if (isRmodeDetailEditingNote) {
            setTimeout(() => {
                const textarea = document.getElementById('rmode-note-editor-text');
                if (textarea) {
                    textarea.focus();
                    textarea.select();
                }
            }, 50);
        }
    }

    function saveRmodeDetailNote(taskId) {
        const input = document.getElementById('rmode-note-editor-text');
        const text = input ? input.value.trim() : '';
        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        taskInfo.task.note = text;
        taskInfo.task.description = text;
        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.note = text;
            taskInfo.plannedItem.task.description = text;
        }

        if (window.TempoToolNotes && typeof window.TempoToolNotes.saveTaskNote === 'function') {
            window.TempoToolNotes.saveTaskNote(taskId, taskInfo.task.name || 'Task', text);
        }

        isRmodeDetailEditingNote = false;
        persistRmodePlanData(taskInfo.plan, taskInfo.task);
        renderRmodeTaskDetailModalDOM();
    }

    function deleteRmodeDetailNote(taskId) {
        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        taskInfo.task.note = '';
        taskInfo.task.description = '';
        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.note = '';
            taskInfo.plannedItem.task.description = '';
        }

        if (window.TempoToolNotes && typeof window.TempoToolNotes.deleteTaskNote === 'function') {
            window.TempoToolNotes.deleteTaskNote(taskId);
        }

        isRmodeDetailEditingNote = false;
        persistRmodePlanData(taskInfo.plan, taskInfo.task);
        renderRmodeTaskDetailModalDOM();
    }

    function toggleRmodeDetailTaskComplete(taskId) {
        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        const newCompleted = !taskInfo.task.completed;
        taskInfo.task.completed = newCompleted;
        setTaskCompletionStatus(taskId, newCompleted);
        renderRmodeTaskDetailModalDOM();
    }

    function toggleRmodeDetailSubtask(taskId, subtaskId) {
        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;
        if (!Array.isArray(taskInfo.task.subtasks)) taskInfo.task.subtasks = [];

        const sub = taskInfo.task.subtasks.find(s => String(s.id) === String(subtaskId));
        if (sub) {
            sub.completed = !sub.completed;
            persistRmodePlanData(taskInfo.plan, taskInfo.task);
            renderRmodeTaskDetailModalDOM();
        }
    }

    function toggleRmodeDetailAddSubtask() {
        isRmodeDetailAddingSubtask = !isRmodeDetailAddingSubtask;
        renderRmodeTaskDetailModalDOM();
        if (isRmodeDetailAddingSubtask) {
            setTimeout(() => {
                const input = document.getElementById('rmode-new-subtask-title');
                if (input) input.focus();
            }, 50);
        }
    }

    function addRmodeDetailSubtask(taskId) {
        const input = document.getElementById('rmode-new-subtask-title');
        const title = input ? input.value.trim() : '';
        if (!title) return;

        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;
        if (!Array.isArray(taskInfo.task.subtasks)) taskInfo.task.subtasks = [];

        taskInfo.task.subtasks.push({
            id: 'sub_' + Date.now(),
            title: title,
            durationMinutes: 15,
            completed: false
        });

        isRmodeDetailAddingSubtask = false;
        persistRmodePlanData(taskInfo.plan, taskInfo.task);
        renderRmodeTaskDetailModalDOM();
    }

    function removeRmodeDetailSubtask(taskId, subtaskId) {
        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task || !Array.isArray(taskInfo.task.subtasks)) return;

        taskInfo.task.subtasks = taskInfo.task.subtasks.filter(s => String(s.id) !== String(subtaskId));
        persistRmodePlanData(taskInfo.plan, taskInfo.task);
        renderRmodeTaskDetailModalDOM();
    }

    function toggleRmodeDetailSubtaskEdit(subtaskId) {
        editingRmodeSubtaskId = subtaskId;
        renderRmodeTaskDetailModalDOM();
        if (subtaskId) {
            setTimeout(() => {
                const input = document.getElementById(`rmode-edit-subtask-input-${subtaskId}`);
                if (input) {
                    input.focus();
                    input.select();
                }
            }, 50);
        }
    }

    function saveRmodeDetailSubtaskTitle(taskId, subtaskId) {
        const input = document.getElementById(`rmode-edit-subtask-input-${subtaskId}`);
        const newTitle = input ? input.value.trim() : '';
        if (!newTitle) return;

        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task || !Array.isArray(taskInfo.task.subtasks)) return;

        const sub = taskInfo.task.subtasks.find(s => String(s.id) === String(subtaskId));
        if (sub) {
            sub.title = newTitle;
            editingRmodeSubtaskId = null;
            persistRmodePlanData(taskInfo.plan, taskInfo.task);
            renderRmodeTaskDetailModalDOM();
        }
    }

    function toggleRmodeDetailLabelMenu() {
        isRmodeDetailLabelMenuOpen = !isRmodeDetailLabelMenuOpen;
        renderRmodeTaskDetailModalDOM();
    }

    function setRmodeDetailTaskLabel(taskId, newLabel) {
        isRmodeDetailLabelMenuOpen = false;
        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        taskInfo.task.userLabel = newLabel;
        taskInfo.task.priorityCategory = (newLabel === 'Now') ? 'DO_FIRST' : 'LATER';
        if (taskInfo.plannedItem) {
            taskInfo.plannedItem.executionBadge = newLabel;
        }

        persistRmodePlanData(taskInfo.plan, taskInfo.task);
        renderRmodeTaskDetailModalDOM();
    }

    function promptClearRmodeTask(taskId) {
        if (!confirm('Are you sure you want to clear this task from your plan?')) return;
        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.plan) {
            closeRmodeTaskDetailModal();
            return;
        }

        const plan = taskInfo.plan;
        if (Array.isArray(plan.plannedTasks)) {
            plan.plannedTasks = plan.plannedTasks.filter(item => {
                const t = item.task || item;
                return t && String(t.id) !== String(taskId);
            });
        }
        if (Array.isArray(plan.unarrangedTasks)) {
            plan.unarrangedTasks = plan.unarrangedTasks.filter(item => {
                const t = item.task || item;
                return t && String(t.id) !== String(taskId);
            });
        }
        if (Array.isArray(plan.tasks)) {
            plan.tasks = plan.tasks.filter(t => t && String(t.id) !== String(taskId));
        }

        closeRmodeTaskDetailModal();
        persistRmodePlanData(plan);
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast('Task removed from working plan.');
        }
    }

    function handleRmodeTaskFocus(taskId) {
        closeRmodeTaskDetailModal();
        startTaskFocus(taskId);
    }

    function handleRmodeTaskReschedule(taskId) {
        closeRmodeTaskDetailModal();
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('tool-workplan');
            setTimeout(() => {
                if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.openRescheduleModal === 'function') {
                    window.TempoPlanWorkspace.openRescheduleModal(taskId);
                }
            }, 100);
        } else if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.openRescheduleModal === 'function') {
            window.TempoPlanWorkspace.openRescheduleModal(taskId);
        }
    }

    function renderRmodeTaskDetailModalHTML() {
        if (!activeRmodeDetailTaskId) return '';

        const taskInfo = getRmodeTaskData(activeRmodeDetailTaskId);
        if (!taskInfo || !taskInfo.task) return '';

        const task = taskInfo.task;
        const plannedItem = taskInfo.plannedItem;
        const isDone = !!task.completed;

        // Schedule string
        let detailScheduleStr = 'Today, Scheduled';
        if (plannedItem && plannedItem.timeHeader) {
            detailScheduleStr = plannedItem.timeHeader;
        } else if (plannedItem && plannedItem.startTime && plannedItem.endTime) {
            detailScheduleStr = `${plannedItem.dayLabel || 'Today'}, ${formatTime12H(plannedItem.startTime)} to ${formatTime12H(plannedItem.endTime)}`;
        } else if (task.timeHeader) {
            detailScheduleStr = task.timeHeader;
        } else if (task.deadlineDate) {
            detailScheduleStr = `Due: ${formatPlanDateHeader(task.deadlineDate, task.deadlineDate)}`;
        } else {
            detailScheduleStr = `Flexible schedule • ~${task.durationLabel || '1h'}`;
        }

        // Priority Badge
        const priorityBadge = task.userLabel === 'Now' ? 'Now' : (task.userLabel === 'Then' ? 'Then' : 'Later');

        // Subtasks calculations
        const subtasks = Array.isArray(task.subtasks) ? task.subtasks : [];
        const totalSubtasks = subtasks.length;
        const completedSubtasks = subtasks.filter(s => s && s.completed).length;

        // Note / Description
        const noteText = (task.note || task.description || (window.TempoToolNotes && window.TempoToolNotes.getTaskNote ? window.TempoToolNotes.getTaskNote(task.id) : '') || '').trim();

        return `
            <div id="rmode-task-detail-modal" 
                 class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-stone-900/50 backdrop-blur-xs transition-all duration-150"
                 onclick="if(event.target === this) window.TempoMode.closeRmodeTaskDetailModal();"
                 role="dialog"
                 aria-modal="true"
                 aria-labelledby="rmode-task-modal-title">
                
                <div class="bg-[#FDFBF6] border border-[#E3C7A5] rounded-3xl p-6 sm:p-7 max-w-lg w-full max-h-[90vh] overflow-y-auto space-y-4 shadow-xl relative text-left"
                     onclick="event.stopPropagation();">
                    
                    <!-- Close Button (✕) -->
                    <button type="button" 
                            onclick="window.TempoMode.closeRmodeTaskDetailModal()"
                            class="absolute top-5 right-5 w-8 h-8 rounded-full bg-[#F3EDE2] hover:bg-[#EAE0D1] text-[#6B5E51] hover:text-[#2D2823] flex items-center justify-center text-sm font-bold transition cursor-pointer"
                            aria-label="Close task details">
                        ✕
                    </button>

                    <!-- Schedule Header -->
                    <div class="text-xs sm:text-sm font-bold text-[#D9A18B] tracking-wide pr-8">
                        ${escapeHTML(detailScheduleStr)}
                    </div>

                    <!-- Title and Priority Badge Row -->
                    <div class="flex items-center justify-between gap-3 pb-1">
                        <div class="flex-1 min-w-0 pr-2">
                            ${isRmodeDetailEditingTitle ? `
                                <div class="flex items-center gap-2">
                                    <input id="rmode-edit-title-input" 
                                           type="text" 
                                           value="${escapeHTML(task.name || '')}" 
                                           class="w-full px-3 py-1.5 text-base font-bold text-[#202124] border border-[#D99E87] rounded-xl bg-white focus:outline-hidden focus:ring-2 focus:ring-[#D99E87]"
                                           onkeydown="if(event.key==='Enter') window.TempoMode.saveRmodeDetailTitleEdit('${task.id}'); if(event.key==='Escape') window.TempoMode.toggleRmodeDetailTitleEdit();" />
                                    <button type="button" 
                                            onclick="window.TempoMode.saveRmodeDetailTitleEdit('${task.id}')"
                                            class="px-3 py-1.5 bg-[#D99E87] text-white rounded-xl text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                        Save
                                    </button>
                                    <button type="button" 
                                            onclick="window.TempoMode.toggleRmodeDetailTitleEdit()"
                                            class="px-2.5 py-1.5 border border-stone-300 text-stone-600 rounded-xl text-xs font-bold hover:bg-stone-100 cursor-pointer">
                                        Cancel
                                    </button>
                                </div>
                            ` : `
                                <div class="flex items-center gap-2 group">
                                    <h2 id="rmode-task-modal-title" class="font-heading text-xl sm:text-2xl font-bold text-[#202124] truncate ${isDone ? 'line-through text-stone-400' : ''}">
                                        ${escapeHTML(task.name || 'Untitled Task')}
                                    </h2>
                                    <button type="button" 
                                            onclick="window.TempoMode.toggleRmodeDetailTitleEdit()" 
                                            class="text-[#D99E87] hover:text-[#C98E77] text-xs font-semibold p-1 hover:bg-[#F3EDE2] rounded-md transition cursor-pointer" 
                                            title="Edit task title">
                                        ✎
                                    </button>
                                </div>
                            `}
                        </div>

                        <!-- Priority Badge with Dropdown -->
                        <div class="relative inline-block shrink-0">
                            <button type="button"
                                    ${isDone ? '' : `onclick="event.stopPropagation(); window.TempoMode.toggleRmodeDetailLabelMenu();"`}
                                    class="px-3 py-0.5 rounded-full text-xs font-bold ${isDone ? 'bg-[#92A491] text-white' : (priorityBadge === 'Now' ? 'bg-[#D99E87] text-white' : 'bg-[#E8ECF1] text-[#7B96A6]')} shrink-0 ${!isDone ? 'cursor-pointer hover:opacity-90 transition flex items-center space-x-1' : ''}"
                                    title="${isDone ? 'Completed task' : 'Change priority'}">
                                <span>${isDone ? 'Done' : priorityBadge}</span>
                                ${!isDone ? '<span class="text-[9px] opacity-75">▾</span>' : ''}
                            </button>
                            ${isRmodeDetailLabelMenuOpen && !isDone ? `
                                <div class="absolute right-0 top-full mt-1 z-30 bg-white border border-[#E3C7A5] rounded-xl shadow-lg py-1 w-28 text-xs font-semibold overflow-hidden"
                                     onclick="event.stopPropagation();">
                                    <button type="button"
                                            onclick="window.TempoMode.setRmodeDetailTaskLabel('${task.id}', 'Now');"
                                            class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${priorityBadge === 'Now' ? 'font-bold text-[#D99E87]' : ''}">
                                        <span>Now</span>
                                        ${priorityBadge === 'Now' ? '<span>✓</span>' : ''}
                                    </button>
                                    <button type="button"
                                            onclick="window.TempoMode.setRmodeDetailTaskLabel('${task.id}', 'Later');"
                                            class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${priorityBadge === 'Later' ? 'font-bold text-[#7B96A6]' : ''}">
                                        <span>Later</span>
                                        ${priorityBadge === 'Later' ? '<span>✓</span>' : ''}
                                    </button>
                                </div>
                            ` : ''}
                        </div>
                    </div>

                    <!-- Due Date Row -->
                    <div class="flex items-center space-x-2 text-xs sm:text-sm text-[#6F6B68]">
                        <span>Due: ${escapeHTML(formatRmodeDeadline(task.deadlineDate || task.deadline, task.deadlineTime))}</span>
                        <button type="button"
                                onclick="window.TempoMode.toggleRmodeDetailDeadlineEdit()"
                                class="text-[#D99E87] font-semibold hover:underline cursor-pointer">
                            ${isRmodeDetailEditingDeadline ? 'Cancel' : 'Edit due day'}
                        </button>
                    </div>

                    <!-- Inline Deadline Editor -->
                    ${isRmodeDetailEditingDeadline ? `
                        <div class="p-3 bg-white border border-[#E3C7A5] rounded-xl space-y-2 text-xs">
                            <div class="grid grid-cols-2 gap-2">
                                <div>
                                    <label class="block text-[10px] text-gray-500 font-semibold mb-0.5">Date</label>
                                    <input id="rmode-edit-deadline-date" type="date" value="${task.deadlineDate || (task.deadline ? task.deadline.split(' ')[0] : '')}" class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                </div>
                                <div>
                                    <label class="block text-[10px] text-gray-500 font-semibold mb-0.5">Time</label>
                                    <input id="rmode-edit-deadline-time" type="time" value="${task.deadlineTime || (task.deadline && task.deadline.includes(':') ? task.deadline.split(' ')[1] : '23:59')}" class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                </div>
                            </div>
                            <div class="flex items-center space-x-2">
                                <input id="rmode-edit-no-deadline" type="checkbox" ${task.hasDeadline === false ? 'checked' : ''} class="rounded text-[#D99E87]">
                                <label for="rmode-edit-no-deadline" class="text-xs text-stone-700">No fixed deadline</label>
                            </div>
                            <div class="flex justify-end pt-1">
                                <button type="button"
                                        onclick="window.TempoMode.saveRmodeDetailDeadlineEdit('${task.id}')"
                                        class="px-3 py-1 bg-[#D99E87] text-white rounded-lg text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                    Save deadline
                                </button>
                            </div>
                        </div>
                    ` : ''}

                    <!-- Subtasks Count Row & Controls -->
                    <div class="flex items-center justify-between text-xs sm:text-sm text-[#6F6B68]">
                        <span>${completedSubtasks}/${totalSubtasks} subtasks</span>
                        <button type="button"
                                onclick="window.TempoMode.toggleRmodeDetailAddSubtask()"
                                class="text-[#D99E87] font-semibold hover:underline cursor-pointer flex items-center space-x-1">
                            <span>+ Add subtask</span>
                        </button>
                    </div>

                    <!-- Add Subtask Input Form -->
                    ${isRmodeDetailAddingSubtask ? `
                        <div class="flex items-center gap-2 p-2.5 bg-white border border-[#E3C7A5] rounded-xl">
                            <input id="rmode-new-subtask-title" 
                                   type="text" 
                                   placeholder="Enter new subtask title..."
                                   class="flex-1 px-2.5 py-1 text-xs border border-gray-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-[#D99E87]"
                                   onkeydown="if(event.key==='Enter') window.TempoMode.addRmodeDetailSubtask('${task.id}'); if(event.key==='Escape') window.TempoMode.toggleRmodeDetailAddSubtask();" />
                            <button type="button" 
                                    onclick="window.TempoMode.addRmodeDetailSubtask('${task.id}')"
                                    class="px-3 py-1 bg-[#D99E87] text-white rounded-lg text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                Add
                            </button>
                            <button type="button" 
                                    onclick="window.TempoMode.toggleRmodeDetailAddSubtask()"
                                    class="px-2 py-1 text-xs text-stone-500 hover:text-stone-800 cursor-pointer">
                                ✕
                            </button>
                        </div>
                    ` : ''}

                    <!-- Subtask List -->
                    <div class="max-h-48 overflow-y-auto space-y-2 pr-1.5 plan-custom-scroll">
                        ${subtasks.length > 0 ? subtasks.map(step => `
                            <div class="flex items-center justify-between space-x-2 text-xs sm:text-sm text-[#4A4540] group bg-white/70 hover:bg-white p-2 rounded-xl border border-[#EDE2D5] transition">
                                <div class="flex items-center space-x-2.5 min-w-0 flex-1">
                                    <button type="button"
                                            onclick="window.TempoMode.toggleRmodeDetailSubtask('${task.id}', '${step.id}')"
                                            class="w-4 h-4 rounded border border-[#E3C7A5] flex items-center justify-center text-[10px] font-bold transition shrink-0 cursor-pointer ${step.completed ? 'bg-[#92A491] border-[#92A491] text-white' : 'bg-white border-[#E3C7A5] text-transparent hover:border-[#D99E87]'}"
                                            title="Toggle subtask">
                                        ✓
                                    </button>
                                    ${editingRmodeSubtaskId === step.id ? `
                                        <div class="flex items-center gap-1.5 flex-1 min-w-0">
                                            <input id="rmode-edit-subtask-input-${step.id}" 
                                                   type="text" 
                                                   value="${escapeHTML(step.title || '')}" 
                                                   class="flex-1 px-2 py-0.5 text-xs border border-[#D99E87] rounded-md bg-white focus:outline-hidden"
                                                   onkeydown="if(event.key==='Enter') window.TempoMode.saveRmodeDetailSubtaskTitle('${task.id}', '${step.id}'); if(event.key==='Escape') window.TempoMode.toggleRmodeDetailSubtaskEdit(null);" />
                                            <button type="button" 
                                                    onclick="window.TempoMode.saveRmodeDetailSubtaskTitle('${task.id}', '${step.id}')" 
                                                    class="text-xs text-[#D99E87] font-bold px-1 hover:underline cursor-pointer">Save</button>
                                            <button type="button" 
                                                    onclick="window.TempoMode.toggleRmodeDetailSubtaskEdit(null)" 
                                                    class="text-xs text-stone-500 px-1 hover:underline cursor-pointer">Cancel</button>
                                        </div>
                                    ` : `
                                        <span class="truncate ${step.completed ? 'line-through text-stone-400' : ''}">${escapeHTML(step.title)}</span>
                                        <button type="button" 
                                                onclick="window.TempoMode.toggleRmodeDetailSubtaskEdit('${step.id}')" 
                                                class="text-stone-400 hover:text-[#D99E87] text-[11px] px-1 opacity-0 group-hover:opacity-100 transition cursor-pointer" 
                                                title="Edit subtask">✎</button>
                                    `}
                                </div>
                                <button type="button" 
                                        onclick="window.TempoMode.removeRmodeDetailSubtask('${task.id}', '${step.id}')"
                                        class="text-stone-300 hover:text-rose-500 text-xs px-1.5 transition opacity-60 group-hover:opacity-100 cursor-pointer"
                                        title="Delete subtask">
                                    ✕
                                </button>
                            </div>
                        `).join('') : `
                            <div class="text-xs text-stone-400 italic py-1">No subtasks yet</div>
                        `}
                    </div>

                    <!-- Note Row -->
                    ${isRmodeDetailEditingNote ? `
                        <div class="p-3 bg-white border border-[#E3C7A5] rounded-xl space-y-2 text-xs">
                            <label class="block text-[10px] text-gray-500 font-semibold">Task Note / Description</label>
                            <textarea id="rmode-note-editor-text" 
                                      rows="3" 
                                      class="w-full p-2 text-xs border border-gray-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-[#D99E87]"
                                      placeholder="Add details, links, or notes for this task...">${escapeHTML(noteText)}</textarea>
                            <div class="flex justify-between items-center pt-1">
                                ${noteText ? `
                                    <button type="button" 
                                            onclick="window.TempoMode.deleteRmodeDetailNote('${task.id}')"
                                            class="text-xs text-rose-600 hover:underline cursor-pointer">
                                        Delete note
                                    </button>
                                ` : '<div></div>'}
                                <div class="flex space-x-2">
                                    <button type="button" 
                                            onclick="window.TempoMode.toggleRmodeDetailNoteEdit()"
                                            class="px-2.5 py-1 text-xs text-stone-600 border border-stone-300 rounded-lg hover:bg-stone-100 cursor-pointer">
                                        Cancel
                                    </button>
                                    <button type="button" 
                                            onclick="window.TempoMode.saveRmodeDetailNote('${task.id}')"
                                            class="px-3 py-1 bg-[#D99E87] text-white rounded-lg text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                        Save note
                                    </button>
                                </div>
                            </div>
                        </div>
                    ` : (noteText ? `
                        <div class="text-xs sm:text-sm text-[#4A4540] pt-1 flex items-start justify-between gap-2 bg-[#F6F4EE]/60 border border-[#EAE4DF] rounded-xl p-2.5">
                            <div class="min-w-0 flex-1">
                                <strong class="text-[#D9A18B]">Note:</strong> <span class="whitespace-pre-line text-[#4A4540]">${escapeHTML(noteText)}</span>
                            </div>
                            <button type="button"
                                    onclick="window.TempoMode.toggleRmodeDetailNoteEdit()"
                                    class="text-[#D99E87] hover:text-[#C98E77] text-xs font-semibold shrink-0 cursor-pointer flex items-center space-x-1"
                                    title="Edit note">
                                <span>Edit note</span>
                                <span>✎</span>
                            </button>
                        </div>
                    ` : `
                        <div class="pt-1">
                            <button type="button"
                                    onclick="window.TempoMode.toggleRmodeDetailNoteEdit()"
                                    class="text-xs font-bold text-[#D9A18B] hover:underline cursor-pointer flex items-center space-x-1">
                                <span>+ Create a note</span>
                            </button>
                        </div>
                    `)}

                    <!-- Action Buttons (2x2 grid) -->
                    <div class="grid grid-cols-2 gap-3 pt-3">
                        <!-- 1. Mark as done / active -->
                        <button type="button"
                                onclick="window.TempoMode.toggleRmodeDetailTaskComplete('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#92A491] hover:bg-[#829381] shadow-2xs transition text-center cursor-pointer">
                            ${isDone ? 'Mark as active' : 'Mark as done'}
                        </button>

                        <!-- 2. Focus now -->
                        <button type="button"
                                onclick="window.TempoMode.handleRmodeTaskFocus('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#D7A690] hover:bg-[#C98E77] shadow-2xs transition flex items-center justify-center space-x-1.5 cursor-pointer">
                            <span>▶ Focus now</span>
                        </button>

                        <!-- 3. Reschedule -->
                        <button type="button"
                                onclick="window.TempoMode.handleRmodeTaskReschedule('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#3A4B3D] bg-white border border-[#8D9B8A] hover:bg-stone-50 transition text-center cursor-pointer">
                            Reschedule
                        </button>

                        <!-- 4. Clear this task -->
                        <button type="button"
                                onclick="window.TempoMode.promptClearRmodeTask('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#C53B27] bg-white border border-[#D99E87] hover:bg-rose-50/40 transition text-center cursor-pointer">
                            Clear this task
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
'''

# Target insertion point: after line 6832 `    }` for `renderRecoveryWorkingPlanSection`
target_needle = '        `;\n    }\n\n    function renderRecoveryCommunityCard() {'
replacement = '        `;\n    }\n' + modal_code + '\n    function renderRecoveryCommunityCard() {'

assert target_needle in content, "Could not find insertion target for modal code!"
content = content.replace(target_needle, replacement, 1)

# Export in TempoMode return object
export_needle = '        getUmodeDayNotesForToday,\n        EPLAN_STATES\n    };'
export_replacement = '''        getUmodeDayNotesForToday,
        openRmodeTaskDetailModal,
        closeRmodeTaskDetailModal,
        isRmodeTaskDetailModalOpen,
        renderRmodeTaskDetailModalHTML,
        renderRmodeTaskDetailModalDOM,
        toggleRmodeDetailTitleEdit,
        saveRmodeDetailTitleEdit,
        toggleRmodeDetailDeadlineEdit,
        saveRmodeDetailDeadlineEdit,
        toggleRmodeDetailNoteEdit,
        saveRmodeDetailNote,
        deleteRmodeDetailNote,
        toggleRmodeDetailTaskComplete,
        toggleRmodeDetailSubtask,
        toggleRmodeDetailAddSubtask,
        addRmodeDetailSubtask,
        removeRmodeDetailSubtask,
        toggleRmodeDetailSubtaskEdit,
        saveRmodeDetailSubtaskTitle,
        toggleRmodeDetailLabelMenu,
        setRmodeDetailTaskLabel,
        promptClearRmodeTask,
        handleRmodeTaskFocus,
        handleRmodeTaskReschedule,
        EPLAN_STATES
    };'''

assert export_needle in content, "Could not find export needle in mode.js!"
content = content.replace(export_needle, export_replacement, 1)

# Update Escape key listener
escape_needle = '''document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && window.TempoMode && typeof window.TempoMode.closeClearOverdueTaskModal === 'function') {
        window.TempoMode.closeClearOverdueTaskModal();
    }
});'''

escape_replacement = '''document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        if (window.TempoMode && typeof window.TempoMode.isRmodeTaskDetailModalOpen === 'function' && window.TempoMode.isRmodeTaskDetailModalOpen()) {
            window.TempoMode.closeRmodeTaskDetailModal();
            return;
        }
        if (window.TempoMode && typeof window.TempoMode.closeClearOverdueTaskModal === 'function') {
            window.TempoMode.closeClearOverdueTaskModal();
        }
    }
});'''

assert escape_needle in content, "Could not find escape needle in mode.js!"
content = content.replace(escape_needle, escape_replacement, 1)

# Ensure pure LF line endings
content = content.replace('\r\n', '\n')
assert '\r\n' not in content, "Result has CRLF!"

with open('mode.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("Successfully updated mode.js with pure LF line endings!")
