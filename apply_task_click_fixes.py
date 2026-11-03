with open('mode.js', 'r', encoding='utf-8') as f:
    content = f.read()

assert '\r\n' not in content, "mode.js has CRLF before edit!"

# 1. Update renderTaskCard and add renderedRmodeTasksMap registration in renderRecoveryWorkingPlanSection
old_render_task_card_section = '''        const totalCount = Math.max(allItems.length, (plannedList.length + unarrangedList.length) || 6);
        const completedTasks = allItems.filter(item => item.completed);
        const incompleteTasks = allItems.filter(item => !item.completed);
        const completedCount = completedTasks.length;
        const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

        function renderTaskCard(item) {
            const isDone = !!item.completed;
            return `
                <div class="space-y-1.5" data-task-id="${item.id}">
                    <div class="text-xs font-bold text-[#55504A]">
                        ${escapeHTML(item.timeHeader)}
                    </div>
                    <div onclick="window.TempoMode.openRmodeTaskDetailModal('${item.id}')"
                         role="button"
                         tabindex="0"
                         aria-label="View task details for ${escapeHTML(item.name)}"
                         onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); window.TempoMode.openRmodeTaskDetailModal('${item.id}'); }"
                         class="border border-[#D8C7B5] rounded-2xl p-4 bg-white hover:bg-stone-50/70 hover:border-[#D79277]/60 hover:shadow-xs transition flex items-start space-x-3 group cursor-pointer ${isDone ? 'opacity-85' : ''}">
                        <button type="button" 
                                onclick="event.stopPropagation(); window.TempoMode.toggleTaskCompletion('${item.id}')"
                                class="w-5 h-5 rounded border ${isDone ? 'bg-[#7B9688] border-[#7B9688] text-white' : 'border-[#C8B39E] bg-white hover:border-[#D79277]'} flex items-center justify-center shrink-0 mt-0.5 cursor-pointer transition"
                                title="${isDone ? 'Mark incomplete' : 'Mark complete'}">
                            ${isDone ? '✓' : ''}
                        </button>
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center justify-between gap-2">
                                <h5 class="text-base font-extrabold truncate ${isDone ? 'line-through opacity-60 text-stone-400' : 'text-[#484541]'}">
                                    ${escapeHTML(item.name)}
                                </h5>
                                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${isDone ? 'bg-[#E8EFE8] text-[#556B54]' : item.tagClass} shrink-0">
                                    ${isDone ? 'Done' : escapeHTML(item.tag)}
                                </span>
                            </div>
                            <p class="text-xs text-[#7B7672] mt-1">
                                ${escapeHTML(item.dueDate)}
                            </p>
                            <p class="text-xs text-[#7B7672] mt-0.5">
                                ${escapeHTML(item.subtasksText)}
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }'''

new_render_task_card_section = '''        const totalCount = Math.max(allItems.length, (plannedList.length + unarrangedList.length) || 6);
        const completedTasks = allItems.filter(item => item.completed);
        const incompleteTasks = allItems.filter(item => !item.completed);
        const completedCount = completedTasks.length;
        const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

        // Register all rendered items in map so every single card is guaranteed accessible by ID
        renderedRmodeTasksMap.clear();
        allItems.forEach((item, idx) => {
            renderedRmodeTasksMap.set(String(item.id), item);
            renderedRmodeTasksMap.set(String(idx), item);
            if (item.task && item.task.id) {
                renderedRmodeTasksMap.set(String(item.task.id), item);
            }
        });

        function renderTaskCard(item) {
            const isDone = !!item.completed;
            const safeId = escapeHTML(item.id);
            return `
                <div class="space-y-1.5 recovery-task-card-group" data-task-id="${safeId}">
                    <div class="text-xs font-bold text-[#55504A] cursor-pointer hover:text-[#D79277] transition select-none inline-block"
                         onclick="window.TempoMode.openRmodeTaskDetailModal('${safeId}')"
                         title="View task details for ${escapeHTML(item.name)}">
                        ${escapeHTML(item.timeHeader)}
                    </div>
                    <div onclick="if (!event.target.closest('button[data-task-toggle]')) { window.TempoMode.openRmodeTaskDetailModal('${safeId}'); }"
                         role="button"
                         tabindex="0"
                         aria-label="View task details for ${escapeHTML(item.name)}"
                         onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); window.TempoMode.openRmodeTaskDetailModal('${safeId}'); }"
                         class="border border-[#D8C7B5] rounded-2xl p-4 bg-white hover:bg-stone-50/70 hover:border-[#D79277]/60 hover:shadow-xs transition flex items-start space-x-3 group cursor-pointer ${isDone ? 'opacity-85' : ''}">
                        <button type="button" 
                                data-task-toggle="true"
                                onclick="event.stopPropagation(); window.TempoMode.toggleTaskCompletion('${safeId}')"
                                class="w-5 h-5 rounded border ${isDone ? 'bg-[#7B9688] border-[#7B9688] text-white' : 'border-[#C8B39E] bg-white hover:border-[#D79277]'} flex items-center justify-center shrink-0 mt-0.5 cursor-pointer transition select-none"
                                title="${isDone ? 'Mark incomplete' : 'Mark complete'}">
                            ${isDone ? '✓' : ''}
                        </button>
                        <div class="flex-1 min-w-0 pointer-events-auto">
                            <div class="flex items-center justify-between gap-2">
                                <h5 class="text-base font-extrabold truncate ${isDone ? 'line-through opacity-60 text-stone-400' : 'text-[#484541]'}">
                                    ${escapeHTML(item.name)}
                                </h5>
                                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${isDone ? 'bg-[#E8EFE8] text-[#556B54]' : item.tagClass} shrink-0">
                                    ${isDone ? 'Done' : escapeHTML(item.tag)}
                                </span>
                            </div>
                            <p class="text-xs text-[#7B7672] mt-1">
                                ${escapeHTML(item.dueDate)}
                            </p>
                            <p class="text-xs text-[#7B7672] mt-0.5">
                                ${escapeHTML(item.subtasksText)}
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }'''

assert old_render_task_card_section in content, "Could not find old_render_task_card_section!"
content = content.replace(old_render_task_card_section, new_render_task_card_section, 1)

# 2. Update getRmodeActivePlan, getRmodeTaskData, persistRmodePlanData, and priorityBadge handling
old_plan_data_section = '''    let activeRmodeDetailTaskId = null;
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
    }'''

new_plan_data_section = '''    let activeRmodeDetailTaskId = null;
    let isRmodeDetailEditingTitle = false;
    let isRmodeDetailEditingDeadline = false;
    let isRmodeDetailEditingNote = false;
    let isRmodeDetailLabelMenuOpen = false;
    let isRmodeDetailAddingSubtask = false;
    let editingRmodeSubtaskId = null;

    // Shared map storing every rendered task card from the active dashboard view
    const renderedRmodeTasksMap = new Map();

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
            plan = window.TempoPlanStore.getActivePlan('recovery') || window.TempoPlanStore.getActivePlan('emergency') || window.TempoPlanStore.getActivePlan('default');
        }
        if (!plan && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            plan = window.TempoEmergencyFlow.getConfirmedPlan();
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
            if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.getDefaultReferencePlan === 'function') {
                plan = window.TempoPlanWorkspace.getDefaultReferencePlan();
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
        const renderedItem = renderedRmodeTasksMap.get(sTaskId);

        // 1. Direct match from currently rendered task cards map
        if (renderedItem) {
            matchedTask = renderedItem.task || renderedItem;
            matchedPlanItem = renderedItem;
        }

        // 2. Search plan collections across all possible ID fields
        if (plan) {
            if (Array.isArray(plan.plannedTasks)) {
                for (const pt of plan.plannedTasks) {
                    const t = pt.task || pt;
                    if (t && (String(t.id) === sTaskId || String(pt.id) === sTaskId || String(pt.taskId) === sTaskId)) {
                        matchedTask = t;
                        matchedPlanItem = pt;
                        break;
                    }
                }
            }
            if (!matchedTask && Array.isArray(plan.unarrangedTasks)) {
                for (const u of plan.unarrangedTasks) {
                    const t = u.task || u;
                    if (t && (String(t.id) === sTaskId || String(u.id) === sTaskId)) {
                        matchedTask = t;
                        matchedPlanItem = u;
                        break;
                    }
                }
            }
            if (!matchedTask && Array.isArray(plan.unallocatedTasks)) {
                for (const u of plan.unallocatedTasks) {
                    const t = u.task || u;
                    if (t && (String(t.id) === sTaskId || String(u.id) === sTaskId)) {
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
            if (!matchedTask && Array.isArray(plan.completedTasks)) {
                for (const c of plan.completedTasks) {
                    const t = c.task || c;
                    if (t && (String(t.id) === sTaskId || String(c.id) === sTaskId)) {
                        matchedTask = t;
                        matchedPlanItem = c;
                        break;
                    }
                }
            }
            if (!matchedTask && Array.isArray(plan.doneTasks)) {
                for (const d of plan.doneTasks) {
                    const t = d.task || d;
                    if (t && (String(t.id) === sTaskId || String(d.id) === sTaskId)) {
                        matchedTask = t;
                        matchedPlanItem = d;
                        break;
                    }
                }
            }
        }

        // 3. Fallback definitions for canonical mock tasks
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
        }

        // 4. Construct complete task from rendered item if still missing
        if (!matchedTask && renderedItem) {
            matchedTask = {
                id: sTaskId,
                name: renderedItem.name || 'Untitled Task',
                completed: !!renderedItem.completed,
                deadlineDate: renderedItem.date || '',
                timeHeader: renderedItem.timeHeader || '',
                userLabel: renderedItem.tag || 'Later',
                subtasks: [],
                description: ''
            };
        }

        // 5. Ensure critical properties exist
        if (matchedTask) {
            if (!matchedTask.id) matchedTask.id = sTaskId;
            if (!matchedTask.name) matchedTask.name = (renderedItem && renderedItem.name) ? renderedItem.name : 'Untitled Task';
            if (!Array.isArray(matchedTask.subtasks)) matchedTask.subtasks = [];
            if (!matchedTask.timeHeader && renderedItem && renderedItem.timeHeader) {
                matchedTask.timeHeader = renderedItem.timeHeader;
            }
            if (!matchedTask.userLabel && renderedItem && renderedItem.tag) {
                matchedTask.userLabel = renderedItem.tag;
            }
            try {
                const mockTasks = JSON.parse(localStorage.getItem('tempo_rmode_mock_tasks') || '{}');
                if (typeof mockTasks[matchedTask.id] === 'boolean') {
                    matchedTask.completed = mockTasks[matchedTask.id];
                } else if (typeof mockTasks[sTaskId] === 'boolean') {
                    matchedTask.completed = mockTasks[sTaskId];
                }
            } catch (e) {}
        }

        return { plan, task: matchedTask, plannedItem: matchedPlanItem || renderedItem };
    }

    function persistRmodePlanData(plan, task) {
        if (task) {
            // Update in-memory map
            if (renderedRmodeTasksMap.has(String(task.id))) {
                const item = renderedRmodeTasksMap.get(String(task.id));
                if (item) {
                    item.task = task;
                    item.name = task.name || item.name;
                    item.completed = !!task.completed;
                    if (task.deadlineDate) {
                        item.dueDate = `Due: ${formatPlanDateHeader(task.deadlineDate, task.deadlineDate)}`;
                    }
                    if (Array.isArray(task.subtasks)) {
                        const doneCount = task.subtasks.filter(s => s && s.completed).length;
                        item.subtasksText = `${doneCount}/${task.subtasks.length} subtasks`;
                    }
                }
            }
        }

        if (plan) {
            if (task) {
                let found = false;
                if (Array.isArray(plan.plannedTasks)) {
                    for (const pt of plan.plannedTasks) {
                        const t = pt.task || pt;
                        if (t && (String(t.id) === String(task.id) || String(pt.id) === String(task.id))) {
                            found = true;
                            if (pt.task) Object.assign(pt.task, task);
                            else Object.assign(pt, task);
                            break;
                        }
                    }
                }
                if (!found && Array.isArray(plan.unarrangedTasks)) {
                    for (const u of plan.unarrangedTasks) {
                        const t = u.task || u;
                        if (t && (String(t.id) === String(task.id) || String(u.id) === String(task.id))) {
                            found = true;
                            if (u.task) Object.assign(u.task, task);
                            else Object.assign(u, task);
                            break;
                        }
                    }
                }
                if (!found && Array.isArray(plan.tasks)) {
                    for (const t of plan.tasks) {
                        if (t && String(t.id) === String(task.id)) {
                            found = true;
                            Object.assign(t, task);
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
                const mockMap = {
                    'task-marketing-research': 'rmode-mock-1',
                    'task-event-proposal': 'rmode-mock-2',
                    'task-edit-video': 'rmode-mock-3'
                };
                if (mockMap[task.id]) {
                    mockTasks[mockMap[task.id]] = !!task.completed;
                }
                localStorage.setItem('tempo_rmode_mock_tasks', JSON.stringify(mockTasks));
            } catch (e) {}
        }

        renderRmodeHome();
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
        }
    }'''

assert old_plan_data_section in content, "Could not find old_plan_data_section!"
content = content.replace(old_plan_data_section, new_plan_data_section, 1)

# 3. Update priorityBadge in renderRmodeTaskDetailModalHTML
old_badge_calc = '''        // Priority Badge
        const priorityBadge = task.userLabel === 'Now' ? 'Now' : (task.userLabel === 'Then' ? 'Then' : 'Later');'''

new_badge_calc = '''        // Priority Badge (dynamically evaluated from task or plannedItem)
        let priorityBadge = 'Later';
        if (task.userLabel === 'Now' || (plannedItem && (plannedItem.tag === 'Now' || plannedItem.executionBadge === 'Now'))) {
            priorityBadge = 'Now';
        } else if (task.userLabel === 'Then' || (plannedItem && (plannedItem.tag === 'Then' || plannedItem.executionBadge === 'Then'))) {
            priorityBadge = 'Then';
        }'''

assert old_badge_calc in content, "Could not find old_badge_calc!"
content = content.replace(old_badge_calc, new_badge_calc, 1)

# 4. Update priority badge styling in modal header
old_badge_btn = '''                        <!-- Priority Badge with Dropdown -->
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
                        </div>'''

new_badge_btn = '''                        <!-- Priority Badge with Dropdown -->
                        <div class="relative inline-block shrink-0">
                            <button type="button"
                                    ${isDone ? '' : `onclick="event.stopPropagation(); window.TempoMode.toggleRmodeDetailLabelMenu();"`}
                                    class="px-3 py-0.5 rounded-full text-xs font-bold ${isDone ? 'bg-[#92A491] text-white' : (priorityBadge === 'Now' ? 'bg-[#D99E87] text-white' : (priorityBadge === 'Then' ? 'bg-[#F7E7D4] text-[#A6753A]' : 'bg-[#E8ECF1] text-[#7B96A6]'))} shrink-0 ${!isDone ? 'cursor-pointer hover:opacity-90 transition flex items-center space-x-1' : ''}"
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
                                            onclick="window.TempoMode.setRmodeDetailTaskLabel('${task.id}', 'Then');"
                                            class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${priorityBadge === 'Then' ? 'font-bold text-[#A6753A]' : ''}">
                                        <span>Then</span>
                                        ${priorityBadge === 'Then' ? '<span>✓</span>' : ''}
                                    </button>
                                    <button type="button"
                                            onclick="window.TempoMode.setRmodeDetailTaskLabel('${task.id}', 'Later');"
                                            class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${priorityBadge === 'Later' ? 'font-bold text-[#7B96A6]' : ''}">
                                        <span>Later</span>
                                        ${priorityBadge === 'Later' ? '<span>✓</span>' : ''}
                                    </button>
                                </div>
                            ` : ''}
                        </div>'''

assert old_badge_btn in content, "Could not find old_badge_btn!"
content = content.replace(old_badge_btn, new_badge_btn, 1)

# Ensure LF
content = content.replace('\r\n', '\n')
assert '\r\n' not in content, "Output has CRLF!"

with open('mode.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("Successfully applied task click and data fixes to mode.js!")
