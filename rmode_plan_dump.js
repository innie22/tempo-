function renderRecoveryWorkingPlanSection(confirmedPlan, todayStr) {
        if (!todayStr) todayStr = getTodayISOString();

        // Shared plan resolution
        function hasValidTasks(p) {
            return Boolean(p && (
                (Array.isArray(p.plannedTasks) && p.plannedTasks.length > 0) ||
                (Array.isArray(p.tasks) && p.tasks.length > 0) ||
                (Array.isArray(p.unarrangedTasks) && p.unarrangedTasks.length > 0)
            ));
        }

        let plan = hasValidTasks(confirmedPlan) ? confirmedPlan : null;
        if (!plan && window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.getActivePlan === 'function') {
            const p = window.TempoPlanWorkspace.getActivePlan();
            if (hasValidTasks(p)) plan = p;
        }
        if (!plan && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            const p = window.TempoPlanStore.getActivePlan('recovery') || window.TempoPlanStore.getActivePlan('emergency') || window.TempoPlanStore.getActivePlan('default');
            if (hasValidTasks(p)) plan = p;
        }
        if (!plan && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            const p = window.TempoEmergencyFlow.getConfirmedPlan();
            if (hasValidTasks(p)) plan = p;
        }
        if (!plan) {
            try {
                const savedPlan = localStorage.getItem('tempo_working_plan') || localStorage.getItem('tempo_store_active_emergency_guest');
                if (savedPlan) {
                    const parsed = JSON.parse(savedPlan);
                    if (hasValidTasks(parsed)) plan = parsed;
                }
            } catch (e) {}
        }
        if (!plan && window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.getDefaultReferencePlan === 'function') {
            plan = window.TempoPlanWorkspace.getDefaultReferencePlan();
        }

        let plannedList = [];
        if (plan && Array.isArray(plan.plannedTasks) && plan.plannedTasks.length > 0) {
            plannedList = plan.plannedTasks;
        } else if (plan && Array.isArray(plan.tasks) && plan.tasks.length > 0) {
            plannedList = plan.tasks.map((t, idx) => ({
                dayDate: t.scheduledDate || t.deadlineDate || (idx < 2 ? todayStr : null),
                task: t
            }));
        }

        const unarrangedList = (plan && Array.isArray(plan.unarrangedTasks)) ? plan.unarrangedTasks : [];
        const completedList = (plan && (Array.isArray(plan.completedTasks) ? plan.completedTasks : (Array.isArray(plan.doneTasks) ? plan.doneTasks : []))) || [];

        let allItems = [];
        const seenTaskIds = new Set();

        if (plannedList.length > 0) {
            plannedList.forEach((pt, index) => {
                const t = (pt && pt.task) ? pt.task : (pt || {});
                const taskId = t.id || pt.id || `task-${index}`;
                seenTaskIds.add(String(taskId));
                const isToday = (pt.dayDate === todayStr);
                const isCompleted = isTaskExplicitlyCompleted(pt);
                const subCount = (Array.isArray(t.subtasks) && t.subtasks.length > 0) ? t.subtasks.length : 0;
                const subDone = (Array.isArray(t.subtasks) && t.subtasks.length > 0) ? t.subtasks.filter(s => isTaskExplicitlyCompleted(s)).length : 0;
                const targetDayDate = pt.dayDate || t.scheduledDate || (isToday ? todayStr : null);
                const schedDateLabel = targetDayDate ? formatScheduledDateLabel(targetDayDate, isViLocale()) : '';
                const headerDateLabel = schedDateLabel || (targetDayDate ? formatPlanDateHeader(targetDayDate, targetDayDate) : (isViLocale() ? 'Lịch linh hoạt' : 'Flexible schedule'));

                let timeHeader = pt.timeBlock;
                if (!timeHeader) {
                    if (pt.startTime && pt.endTime) {
                        timeHeader = `${headerDateLabel}, ${formatTime12H(pt.startTime)} to ${formatTime12H(pt.endTime)}`;
                    } else if (pt.startTime) {
                        timeHeader = `${headerDateLabel}, ${formatTime12H(pt.startTime)}`;
                    } else if (pt.dayDate) {
                        timeHeader = `${headerDateLabel}, ${isViLocale() ? 'Đã lên lịch' : 'Scheduled'}`;
                    } else {
                        timeHeader = isViLocale() ? 'Lịch linh hoạt' : 'Flexible schedule';
                    }
                }

                let tag = 'Later';
                let tagClass = 'bg-[#E2EDF2] text-[#4F7A8A]';
                if (t.userLabel === 'Now' || pt.executionBadge === 'Now' || t.priorityCategory === 'DO_FIRST' || (isToday && index === 0)) {
                    tag = 'Now';
                    tagClass = 'bg-[#D79277] text-white';
                } else if (t.userLabel === 'Then' || (isToday && index === 1)) {
                    tag = 'Then';
                    tagClass = 'bg-[#F7E7D4] text-[#A6753A]';
                }

                let dueDateStr = isViLocale() ? 'Deadline: Sắp tới' : 'Due: Upcoming';
                if (t.dueDate) {
                    dueDateStr = `${isViLocale() ? 'Deadline:' : 'Due:'} ${t.dueDate}`;
                } else if (t.deadlineDate) {
                    const formattedDDate = formatPlanDateHeader(t.deadlineDate, t.deadlineDate);
                    const timePart = t.deadlineTime ? ` - ${formatTime12H(t.deadlineTime)}` : '';
                    dueDateStr = `${isViLocale() ? 'Deadline:' : 'Due:'} ${formattedDDate}${timePart}`;
                } else if (t.deadline) {
                    dueDateStr = `${isViLocale() ? 'Deadline:' : 'Due:'} ${t.deadline}`;
                }

                const taskIsOverdue = isTaskOverdue(t, plan);
                const taskIsMissed = !taskIsOverdue && isTaskMissedSchedule(pt, plan);

                allItems.push({
                    id: taskId,
                    task: t,
                    name: t.name || t.title || 'Untitled Task',
                    date: targetDayDate,
                    dayLabel: pt.dayLabel || headerDateLabel,
                    headerDateLabel: headerDateLabel,
                    timeHeader: timeHeader,
                    tag: tag,
                    tagClass: tagClass,
                    dueDate: dueDateStr,
                    isOverdue: taskIsOverdue,
                    isMissedSchedule: taskIsMissed,
                    subtasksText: `${subDone}/${subCount} ${isViLocale() ? 'bước nhỏ' : 'subtasks'}`,
                    completed: isCompleted
                });
            });
        }

        // Include any explicitly completed unarranged tasks in allItems so they show up in Done column
        unarrangedList.forEach((u, uIdx) => {
            const t = (u && u.task) ? u.task : u;
            const taskId = t.id || u.id || `unarranged-${uIdx}`;
            if (seenTaskIds.has(String(taskId))) return;
            const isCompleted = isTaskExplicitlyCompleted(u);
            if (isCompleted) {
                seenTaskIds.add(String(taskId));
                const subCount = (Array.isArray(t.subtasks) && t.subtasks.length > 0) ? t.subtasks.length : 0;
                const subDone = (Array.isArray(t.subtasks) && t.subtasks.length > 0) ? t.subtasks.filter(s => isTaskExplicitlyCompleted(s)).length : 0;
                allItems.push({
                    id: taskId,
                    task: t,
                    name: t.name || t.title || 'Untitled Task',
                    date: t.deadlineDate || todayStr,
                    dayLabel: 'Flexible',
                    headerDateLabel: 'Completed',
                    timeHeader: 'Flexible Schedule',
                    tag: 'Done',
                    tagClass: 'bg-[#E8EFE8] text-[#556B54]',
                    dueDate: t.deadlineDate ? `${isViLocale() ? 'Deadline:' : 'Due:'} ${formatPlanDateHeader(t.deadlineDate, t.deadlineDate)}` : (isViLocale() ? 'Chưa có deadline' : 'Flexible schedule'),
                    subtasksText: `${subDone}/${subCount} subtasks`,
                    completed: true
                });
            }
        });

        // Also include any tasks from plan.completedTasks or plan.doneTasks if not already present
        completedList.forEach((c, cIdx) => {
            const t = (c && c.task) ? c.task : c;
            const taskId = t.id || c.id || `completed-${cIdx}`;
            if (seenTaskIds.has(String(taskId))) return;
            seenTaskIds.add(String(taskId));
            const subCount = (Array.isArray(t.subtasks) && t.subtasks.length > 0) ? t.subtasks.length : 0;
            const subDone = (Array.isArray(t.subtasks) && t.subtasks.length > 0) ? t.subtasks.filter(s => isTaskExplicitlyCompleted(s)).length : 0;
            allItems.push({
                id: taskId,
                task: t,
                name: t.name || t.title || 'Untitled Task',
                date: c.dayDate || t.deadlineDate || todayStr,
                dayLabel: c.dayLabel || 'Completed',
                headerDateLabel: 'Completed',
                timeHeader: 'Completed Task',
                tag: 'Done',
                tagClass: 'bg-[#E8EFE8] text-[#556B54]',
                dueDate: t.deadlineDate ? `${isViLocale() ? 'Deadline:' : 'Due:'} ${formatPlanDateHeader(t.deadlineDate, t.deadlineDate)}` : (isViLocale() ? 'Hoàn thành' : 'Completed'),
                subtasksText: `${subDone}/${subCount} subtasks`,
                completed: true
            });
        });

        // Fallback default tasks if absolutely no tasks were loaded
        if (allItems.length === 0) {
            let mockState = {};
            try {
                mockState = JSON.parse(localStorage.getItem('tempo_rmode_mock_tasks') || '{}');
            } catch (e) {}

            const m1Done = (typeof mockState['task-marketing-research'] === 'boolean') ? mockState['task-marketing-research'] : (typeof mockState['rmode-mock-1'] === 'boolean' ? mockState['rmode-mock-1'] : false);
            const m2Done = (typeof mockState['task-event-proposal'] === 'boolean') ? mockState['task-event-proposal'] : (typeof mockState['rmode-mock-2'] === 'boolean' ? mockState['rmode-mock-2'] : false);
            const m3Done = (typeof mockState['task-edit-video'] === 'boolean') ? mockState['task-edit-video'] : (typeof mockState['rmode-mock-3'] === 'boolean' ? mockState['rmode-mock-3'] : false);

            const tmrw = new Date();
            tmrw.setDate(tmrw.getDate() + 1);
            const tmrwStr = getLocalTomorrowISO();

            allItems = [
                {
                    id: 'task-marketing-research',
                    name: 'Marketing Research',
                    date: todayStr,
                    dayLabel: formatScheduledDateLabel(todayStr, isViLocale()),
                    headerDateLabel: formatScheduledDateLabel(todayStr, isViLocale()),
                    timeHeader: isViLocale() ? `${formatScheduledDateLabel(todayStr, isViLocale())}, 14:00 đến 16:00` : `${formatScheduledDateLabel(todayStr, isViLocale())}, 2:00 PM to 4:00 PM`,
                    tag: isViLocale() ? 'Làm ngay' : 'Now',
                    tagClass: 'bg-[#D79277] text-white',
                    dueDate: isViLocale() ? 'Deadline: 17 thg 10, 2026 - 21:00' : 'Due: Oct 17, 2026 - 9:00 PM',
                    subtasksText: isViLocale() ? '0/6 bước nhỏ' : '0/6 action steps',
                    completed: m1Done
                },
                {
                    id: 'task-event-proposal',
                    name: 'Event Proposal',
                    date: todayStr,
                    dayLabel: formatScheduledDateLabel(todayStr, isViLocale()),
                    headerDateLabel: formatScheduledDateLabel(todayStr, isViLocale()),
                    timeHeader: isViLocale() ? `${formatScheduledDateLabel(todayStr, isViLocale())}, 17:00 đến 19:00` : `${formatScheduledDateLabel(todayStr, isViLocale())}, 5:00 PM to 7:00 PM`,
                    tag: isViLocale() ? 'Sau đó' : 'Then',
                    tagClass: 'bg-[#F7E7D4] text-[#A6753A]',
                    dueDate: isViLocale() ? 'Deadline: 18 thg 10, 2026 - 10:00' : 'Due: Oct 18, 2026 - 10:00 AM',
                    subtasksText: isViLocale() ? '0/3 bước nhỏ' : '0/3 action steps',
                    completed: m2Done
                },
                {
                    id: 'task-edit-video',
                    name: 'Edit Video',
                    date: tmrwStr,
                    dayLabel: formatScheduledDateLabel(tmrwStr, isViLocale()),
                    headerDateLabel: formatScheduledDateLabel(tmrwStr, isViLocale()),
                    timeHeader: isViLocale() ? `${formatScheduledDateLabel(tmrwStr, isViLocale())}, 13:00 đến 17:00` : `${formatScheduledDateLabel(tmrwStr, isViLocale())}, 1:00 PM to 5:00 PM`,
                    tag: isViLocale() ? 'Sau nữa' : 'Later',
                    tagClass: 'bg-[#E2EDF2] text-[#4F7A8A]',
                    dueDate: isViLocale() ? 'Deadline: 20 thg 10, 2026 - 22:00' : 'Due: Oct 20, 2026 - 10:00 PM',
                    subtasksText: isViLocale() ? '0/3 bước nhỏ' : '0/3 action steps',
                    completed: m3Done
                }
            ];
        }

        const totalCount = Math.max(allItems.length, (plannedList.length + unarrangedList.length) || 6);
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
                                title="${isDone ? 'Đánh dấu chưa xong' : 'Đánh dấu hoàn thành'}">
                            ${isDone ? '✓' : ''}
                        </button>
                        <div class="flex-1 min-w-0 pointer-events-auto">
                            <div class="flex items-center justify-between gap-2">
                                <h5 class="text-base font-extrabold truncate ${isDone ? 'line-through opacity-60 text-stone-400' : 'text-[#484541]'}">
                                    ${escapeHTML(item.name)}
                                </h5>
                                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${isDone ? 'bg-[#E8EFE8] text-[#556B54]' : item.tagClass} shrink-0">
                                    ${isDone ? (isViLocale() ? 'Đã xong' : 'Done') : escapeHTML(item.tag)}
                                </span>
                            </div>
                            <p class="text-xs text-[#7B7672] mt-1 flex items-center gap-1.5 flex-wrap">
                                <span>${escapeHTML(item.dueDate)}</span>
                                ${item.isOverdue ? `<span class="px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">${(window.t ? window.t('modes.urgent.overdueBadge') : null) || (isViLocale() ? 'TRỄ DEADLINE' : 'OVERDUE')}</span>` : ''}
                                ${(!item.isOverdue && item.isMissedSchedule) ? `<span class="px-1.5 py-0.2 rounded text-[10px] font-bold bg-stone-100 text-stone-700 border border-stone-300">${isViLocale() ? 'TASK QUÁ LỊCH' : 'MISSED SCHEDULE'}</span>` : ''}
                            </p>
                            <p class="text-xs text-[#7B7672] mt-0.5">
                                ${escapeHTML(item.subtasksText)}
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }

        return `
            <div class="recovery-working-plan-card bg-[#FEFAF4] rounded-3xl p-6 sm:p-7 shadow-xs border border-white/60 space-y-4 max-w-full min-w-0" data-tempo-ui="recovery-working-plan" id="recovery-working-plan">
                <!-- Header -->
                <div class="flex items-center justify-between pb-1 shrink-0">
                    <h3 class="font-heading text-2xl font-extrabold text-[#484541] tracking-tight">
                        <span class="sr-only">${isViLocale() ? 'Kế hoạch làm việc của bạn - ' : 'Your plan for today - '}</span>${isViLocale() ? (window.t ? window.t('modes.urgent.workingPlanTitle', {}, 'Working Plan') : 'Working Plan') : 'Working Plan'}
                    </h3>
                    <button type="button"
                            onclick="if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('plan-workspace'); } else { window.location.hash = '#plan-workspace'; }"
                            class="px-4 py-1.5 rounded-full text-xs font-bold bg-[#D79277] hover:bg-[#C68166] text-white shadow-2xs transition cursor-pointer">
                        <span class="sr-only">${isViLocale() ? 'Xem / Chỉnh sửa kế hoạch - ' : 'View / Edit Plan - '}</span><span>${window.t ? window.t('modes.urgent.editPlan', {}, (isViLocale() ? 'Sửa plan' : 'Edit Plan')) : (isViLocale() ? 'Sửa plan' : 'Edit Plan')}</span>
                    </button>
                </div>

                <!-- Overall Progress Bar -->
                <div class="flex items-center space-x-3 pb-2 shrink-0">
                    <div class="flex-1 h-2 bg-[#E0DDD9] rounded-full overflow-hidden">
                        <div class="h-full bg-[#D79277] rounded-full transition-all duration-300" style="width: ${progressPercent}%;"></div>
                    </div>
                    <span class="text-xs font-semibold text-[#6F6B68] shrink-0">${completedCount}/${totalCount} ${isViLocale() ? 'task' : 'tasks'}</span>
                </div>

                <!-- Two-Column Container (Left: Tasks, Right: Task Done) -->
                <div class="recovery-working-plan-scroll flex-1 min-h-0 overflow-x-auto overflow-y-auto pr-1 pb-1"
                     data-tempo-ui="recovery-plan-scroll-container">
                    <div class="recovery-plan-columns grid flex flex-row items-stretch h-full gap-4 md:gap-5 w-full min-w-0 pt-1"
                         data-tempo-ui="recovery-plan-columns">

                        <!-- Left Column: Tasks (all incomplete tasks) -->
                        <div class="recovery-plan-column flex flex-col h-full min-w-0 flex-1"
                             data-tempo-ui="recovery-date-column"
                             data-tempo-column="tasks">
                            <div class="text-xs sm:text-sm font-extrabold text-[#55504A] uppercase tracking-wider flex items-center justify-between pb-2 shrink-0">
                                <span>${isViLocale() ? 'CÔNG VIỆC' : 'TASKS'}</span>
                                <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#F3EFEA] text-[#7B7672]">(${incompleteTasks.length})</span>
                            </div>
                            <div class="recovery-column-tasks flex-1 min-h-0 overflow-y-auto space-y-4 pr-1.5" data-tempo-ui="recovery-column-task-list">
                                ${incompleteTasks.length > 0 ? incompleteTasks.map(renderTaskCard).join('') : `
                                    <div class="p-4 text-xs text-[#8C8782] italic text-center border border-dashed border-[#D8C7B5] rounded-2xl bg-white/50">
                                        ${isViLocale() ? 'Không có task nào đang chờ' : 'No pending tasks'}
                                    </div>
                                `}
                            </div>
                        </div>

                        <!-- Vertical Divider -->
                        <div class="recovery-plan-divider flex justify-center items-stretch shrink-0 self-stretch px-1" aria-hidden="true">
                            <div class="w-1.5 bg-[#D2D6D8] rounded-full self-stretch my-1"></div>
                        </div>

                        <!-- Right Column: Task Done (all completed tasks) -->
                        <div class="recovery-plan-column flex flex-col h-full min-w-0 flex-1"
                             data-tempo-ui="recovery-done-column"
                             data-tempo-column="done">
                            <div class="text-xs sm:text-sm font-extrabold text-[#7B9688] uppercase tracking-wider flex items-center justify-between pb-2 shrink-0">
                                <span>${isViLocale() ? 'VIỆC ĐÃ XONG' : 'TASK DONE'}</span>
                                <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#EBF1ED] text-[#4A6B5D]">(${completedTasks.length})</span>
                            </div>
                            <div class="recovery-column-tasks flex-1 min-h-0 overflow-y-auto space-y-4 pr-1.5" data-tempo-ui="recovery-column-task-list">
                                ${completedTasks.length > 0 ? completedTasks.map(renderTaskCard).join('') : `
                                    <div class="p-4 text-xs text-[#8C8782] italic text-center border border-dashed border-[#D8C7B5] rounded-2xl bg-white/50">
                                        ${isViLocale() ? 'Công việc đã hoàn thành sẽ xuất hiện tại đây' : 'Completed tasks will appear here'}
                                    </div>
                                `}
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        `;
    }


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
                    timeHeader: 'Hôm nay, 14:00 đến 16:00',
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
                    timeHeader: 'Hôm nay, 17:00 đến 19:00',
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
                        item.dueDate = `${isViLocale() ? 'Deadline:' : 'Due:'} ${formatPlanDateHeader(task.deadlineDate, task.deadlineDate)}`;
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
                        dayDate: task.deadlineDate || getLocalTodayISO(),
                        dayLabel: 'Hôm nay',
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
        if (typeof renderActiveModeHome === 'function') {
            renderActiveModeHome();
        }
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
            taskInfo.task.deadlineTime = time || taskInfo.task.deadlineTime || '';
            taskInfo.task.deadline = taskInfo.task.deadlineTime ? `${date} ${taskInfo.task.deadlineTime}` : date;
        }

        delete taskInfo.task.isOverdue;
        taskInfo.task.isOverdue = false;

        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.hasDeadline = taskInfo.task.hasDeadline;
            taskInfo.plannedItem.task.deadlineDate = taskInfo.task.deadlineDate;
            taskInfo.plannedItem.task.deadlineTime = taskInfo.task.deadlineTime;
            taskInfo.plannedItem.task.deadline = taskInfo.task.deadline;
            delete taskInfo.plannedItem.task.isOverdue;
            taskInfo.plannedItem.task.isOverdue = false;
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
        if (!confirm('Bạn có chắc chắn muốn xóa task này khỏi kế hoạch không?')) return;
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
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.openRescheduleModal === 'function') {
            window.TempoPlanWorkspace.openRescheduleModal(taskId);
        }
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('tool-workplan', taskId);
        } else {
            window.location.hash = '#tool-workplan';
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
        let detailScheduleStr = isViLocale() ? `Lịch linh hoạt • ~${task.durationLabel || '1h'}` : `Flexible schedule • ~${task.durationLabel || '1h'}`;
        const itemDayDate = (plannedItem && plannedItem.dayDate) || task.dayDate || task._dayDate;
        const itemSchedLabel = itemDayDate ? formatScheduledDateLabel(itemDayDate, isViLocale()) : '';
        if (plannedItem && plannedItem.timeHeader) {
            detailScheduleStr = plannedItem.timeHeader;
        } else if (plannedItem && plannedItem.startTime && plannedItem.endTime) {
            detailScheduleStr = `${itemSchedLabel || formatScheduledDateLabel(getLocalTodayISO(), isViLocale())}, ${formatTime12H(plannedItem.startTime)} to ${formatTime12H(plannedItem.endTime)}`;
        } else if (itemSchedLabel) {
            detailScheduleStr = `${itemSchedLabel}, ${isViLocale() ? 'Đã lên lịch' : 'Scheduled'}`;
        } else if (task.timeHeader) {
            detailScheduleStr = task.timeHeader;
        } else if (task.deadlineDate) {
            detailScheduleStr = `${isViLocale() ? 'Deadline:' : 'Due:'} ${formatPlanDateHeader(task.deadlineDate, task.deadlineDate)}`;
        }

        // Priority Badge (dynamically evaluated from task or plannedItem)
        let priorityBadge = 'Later';
        if (task.userLabel === 'Now' || (plannedItem && (plannedItem.tag === 'Now' || plannedItem.executionBadge === 'Now'))) {
            priorityBadge = 'Now';
        } else if (task.userLabel === 'Then' || (plannedItem && (plannedItem.tag === 'Then' || plannedItem.executionBadge === 'Then'))) {
            priorityBadge = 'Then';
        }

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
                            aria-label="${isViLocale() ? 'Đóng chi tiết task' : 'Close task detail'}">
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
                                            title="${isViLocale() ? 'Chỉnh sửa tên task' : 'Edit task name'}">
                                        ✎
                                    </button>
                                </div>
                            `}
                        </div>

                        <!-- Priority Badge with Dropdown -->
                        <div class="relative inline-block shrink-0">
                            <button type="button"
                                    ${isDone ? '' : `onclick="event.stopPropagation(); window.TempoMode.toggleRmodeDetailLabelMenu();"`}
                                    class="px-3 py-0.5 rounded-full text-xs font-bold ${isDone ? 'bg-[#92A491] text-white' : (priorityBadge === 'Now' ? 'bg-[#D99E87] text-white' : (priorityBadge === 'Then' ? 'bg-[#F7E7D4] text-[#A6753A]' : 'bg-[#E8ECF1] text-[#7B96A6]'))} shrink-0 ${!isDone ? 'cursor-pointer hover:opacity-90 transition flex items-center space-x-1' : ''}"
                                    title="${isDone ? 'Completed task' : 'Change priority'}">
                                <span>${isDone ? (isViLocale() ? 'Hoàn thành' : 'Done') : (priorityBadge === 'Now' ? (isViLocale() ? 'Làm ngay' : 'Now') : (priorityBadge === 'Then' ? (isViLocale() ? 'Sau đó' : 'Then') : (priorityBadge === 'Later' ? (isViLocale() ? 'Để sau' : 'Later') : priorityBadge)))}</span>
                                ${!isDone ? '<span class="text-[9px] opacity-75">▾</span>' : ''}
                            </button>
                            ${isRmodeDetailLabelMenuOpen && !isDone ? `
                                <div class="absolute right-0 top-full mt-1 z-30 bg-white border border-[#E3C7A5] rounded-xl shadow-lg py-1 w-28 text-xs font-semibold overflow-hidden"
                                     onclick="event.stopPropagation();">
                                    <button type="button"
                                            onclick="window.TempoMode.setRmodeDetailTaskLabel('${task.id}', 'Now');"
                                            class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${priorityBadge === 'Now' ? 'font-bold text-[#D99E87]' : ''}">
                                        <span>${isViLocale() ? 'Làm ngay' : 'Now'}</span>
                                        ${priorityBadge === 'Now' ? '<span>✓</span>' : ''}
                                    </button>
                                    <button type="button"
                                            onclick="window.TempoMode.setRmodeDetailTaskLabel('${task.id}', 'Then');"
                                            class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${priorityBadge === 'Then' ? 'font-bold text-[#A6753A]' : ''}">
                                        <span>${isViLocale() ? 'Sau đó' : 'Then'}</span>
                                        ${priorityBadge === 'Then' ? '<span>✓</span>' : ''}
                                    </button>
                                    <button type="button"
                                            onclick="window.TempoMode.setRmodeDetailTaskLabel('${task.id}', 'Later');"
                                            class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${priorityBadge === 'Later' ? 'font-bold text-[#7B96A6]' : ''}">
                                        <span>${isViLocale() ? 'Sau nữa' : 'Later'}</span>
                                        ${priorityBadge === 'Later' ? '<span>✓</span>' : ''}
                                    </button>
                                </div>
                            ` : ''}
                        </div>
                    </div>

                    <!-- Due Date Row -->
                    <div class="flex items-center space-x-2 text-xs sm:text-sm text-[#6F6B68]">
                        <span>${isViLocale() ? 'Deadline:' : 'Due:'} ${escapeHTML(formatRmodeDeadline(task.deadlineDate || task.deadline, task.deadlineTime))}</span>
                        ${isTaskOverdue(task) ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">${(window.t ? window.t('modes.urgent.overdueBadge') : null) || (isViLocale() ? 'TRỄ DEADLINE' : 'OVERDUE')}</span>` : ''}
                        ${(!isTaskOverdue(task) && isTaskMissedSchedule(plannedItem || task)) ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-stone-100 text-stone-700 border border-stone-300">${isViLocale() ? 'TASK QUÁ LỊCH' : 'MISSED SCHEDULE'}</span>` : ''}
                        <button type="button"
                                onclick="window.TempoMode.toggleRmodeDetailDeadlineEdit()"
                                class="text-[#D99E87] font-semibold hover:underline cursor-pointer">
                            ${isRmodeDetailEditingDeadline ? (isViLocale() ? 'Hủy' : 'Cancel') : (isViLocale() ? 'Sửa deadline' : 'Edit deadline')}
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
                                <label for="rmode-edit-no-deadline" class="text-xs text-stone-700">${isViLocale() ? 'Chưa có deadline' : 'No fixed deadline'}</label>
                            </div>
                            <div class="flex justify-end pt-1">
                                <button type="button"
                                        onclick="window.TempoMode.saveRmodeDetailDeadlineEdit('${task.id}')"
                                        class="px-3 py-1 bg-[#D99E87] text-white rounded-lg text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                    ${isViLocale() ? 'Lưu deadline' : 'Save deadline'}
                                </button>
                            </div>
                        </div>
                    ` : ''}

                    <!-- Subtasks Count Row & Controls -->
                    <div class="flex items-center justify-between text-xs sm:text-sm text-[#6F6B68]">
                        ${totalSubtasks > 0 ? `<span>${completedSubtasks}/${totalSubtasks} ${isViLocale() ? 'bước đã xong' : 'action steps completed'}</span>` : '<span></span>'}
                        <button type="button"
                                onclick="window.TempoMode.toggleRmodeDetailAddSubtask()"
                                class="text-[#D99E87] font-semibold hover:underline cursor-pointer flex items-center space-x-1">
                            <span>${isViLocale() ? '+ Thêm bước nhỏ' : '+ Add action step'}</span>
                        </button>
                    </div>

                    <!-- Add Subtask Input Form -->
                    ${isRmodeDetailAddingSubtask ? `
                        <div class="flex items-center gap-2 p-2.5 bg-white border border-[#E3C7A5] rounded-xl">
                            <input id="rmode-new-subtask-title" 
                                   type="text" 
                                   placeholder="${isViLocale() ? 'Nhập tên bước hành động mới...' : 'Enter new action step...'}"
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
                                            title="${isViLocale() ? 'Đánh dấu bước nhỏ' : 'Toggle step'}">
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
                                                title="${isViLocale() ? 'Chỉnh sửa bước nhỏ' : 'Edit step'}">✎</button>
                                    `}
                                </div>
                                <button type="button" 
                                        onclick="window.TempoMode.removeRmodeDetailSubtask('${task.id}', '${step.id}')"
                                        class="text-stone-300 hover:text-rose-500 text-xs px-1.5 transition opacity-60 group-hover:opacity-100 cursor-pointer"
                                        title="${isViLocale() ? 'Xóa bước nhỏ' : 'Delete step'}">
                                    ✕
                                </button>
                            </div>
                        `).join('') : `
                            <div class="text-xs text-stone-400 italic py-1">${isViLocale() ? 'Chưa có bước nhỏ nào' : 'No subtasks yet'}</div>
                        `}
                    </div>

                    <!-- Note Row -->
                    ${isRmodeDetailEditingNote ? `
                        <div class="p-3 bg-white border border-[#E3C7A5] rounded-xl space-y-2 text-xs">
                            <label class="block text-[10px] text-gray-500 font-semibold">${isViLocale() ? 'Ghi chú Công việc / Mô tả' : 'Task Note / Description'}</label>
                            <textarea id="rmode-note-editor-text" 
                                      rows="3" 
                                      class="w-full p-2 text-xs border border-gray-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-[#D99E87]"
                                      placeholder="${isViLocale() ? 'Thêm chi tiết, liên kết hoặc ghi chú cho task này...' : 'Add details, links, or notes for this task...'}">${escapeHTML(noteText)}</textarea>
                            <div class="flex justify-between items-center pt-1">
                                ${noteText ? `
                                    <button type="button" 
                                            onclick="window.TempoMode.deleteRmodeDetailNote('${task.id}')"
                                            class="text-xs text-rose-600 hover:underline cursor-pointer">
                                        ${isViLocale() ? 'Xóa ghi chú' : 'Delete note'}
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
                                        ${isViLocale() ? 'Lưu ghi chú' : 'Save note'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    ` : (noteText ? `
                        <div class="text-xs sm:text-sm text-[#4A4540] pt-1 flex items-start justify-between gap-2 bg-[#F6F4EE]/60 border border-[#EAE4DF] rounded-xl p-2.5">
                            <div class="min-w-0 flex-1">
                                <strong class="text-[#D9A18B]">${isViLocale() ? 'Ghi chú:' : 'Note:'}</strong> <span class="whitespace-pre-line text-[#4A4540]">${escapeHTML(noteText)}</span>
                            </div>
                            <button type="button"
                                    onclick="window.TempoMode.toggleRmodeDetailNoteEdit()"
                                    class="text-[#D99E87] hover:text-[#C98E77] text-xs font-semibold shrink-0 cursor-pointer flex items-center space-x-1"
                                    title="${isViLocale() ? 'Chỉnh sửa ghi chú' : 'Edit note'}">
                                <span>${isViLocale() ? 'Chỉnh sửa ghi chú' : 'Edit note'}</span>
                                <span>✎</span>
                            </button>
                        </div>
                    ` : `
                        <div class="pt-1">
                            <button type="button"
                                    onclick="window.TempoMode.toggleRmodeDetailNoteEdit()"
                                    class="text-xs font-bold text-[#D9A18B] hover:underline cursor-pointer flex items-center space-x-1">
                                <span>${isViLocale() ? '+ Thêm ghi chú' : '+ Add note'}</span>
                            </button>
                        </div>
                    `)}

                    <!-- Action Buttons (2x2 grid) -->
                    <div class="grid grid-cols-2 gap-3 pt-3">
                        <!-- 1. Mark as done / active -->
                        <button type="button"
                                onclick="window.TempoMode.toggleRmodeDetailTaskComplete('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#92A491] hover:bg-[#829381] shadow-2xs transition text-center cursor-pointer">
                            ${isDone ? (isViLocale() ? 'Đang thực hiện' : 'Mark as active') : (isViLocale() ? 'Hoàn thành' : 'Mark as done')}
                        </button>

                        <!-- 2. Focus now -->
                        <button type="button"
                                onclick="window.TempoMode.handleRmodeTaskFocus('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#D7A690] hover:bg-[#C98E77] shadow-2xs transition flex items-center justify-center space-x-1.5 cursor-pointer">
                            <span>▶ ${isViLocale() ? 'Làm ngay' : 'Focus now'}</span>
                        </button>

                        <!-- 3. Reschedule -->
                        <button type="button"
                                onclick="window.TempoMode.handleRmodeTaskReschedule('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#3A4B3D] bg-white border border-[#8D9B8A] hover:bg-stone-50 transition text-center cursor-pointer">
                            ${isViLocale() ? 'Đổi lịch' : 'Reschedule'}
                        </button>

                        <!-- 4. Clear this task -->
                        <button type="button"
                                onclick="window.TempoMode.promptClearRmodeTask('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#C53B27] bg-white border border-[#D99E87] hover:bg-rose-50/40 transition text-center cursor-pointer">
                            ${isViLocale() ? 'Xóa task này' : 'Clear this task'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // URMODE (EMERGENCY) TASK DETAIL POPUP MODAL (REUSING WORKPLAN UI & ACTIONS)
    // =========================================================================

    let activeUrmodeDetailTaskId = null;
    let isUrmodeDetailEditingTitle = false;
    let isUrmodeDetailEditingDeadline = false;
    let isUrmodeDetailEditingNote = false;
    let isUrmodeDetailLabelMenuOpen = false;
    let isUrmodeDetailAddingSubtask = false;
    let editingUrmodeSubtaskId = null;

    const renderedUrmodeTasksMap = new Map();

    function getUrmodeActivePlan() {
        let plan = null;
        if (window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            plan = window.TempoPlanStore.getActivePlan('emergency');
        }
        if ((!plan || !plan.plannedTasks || plan.plannedTasks.length === 0) && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            const flowPlan = window.TempoEmergencyFlow.getConfirmedPlan();
            if (flowPlan && flowPlan.plannedTasks && flowPlan.plannedTasks.length > 0) plan = flowPlan;
        }
        if ((!plan || !plan.plannedTasks || plan.plannedTasks.length === 0) && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            const defPlan = window.TempoPlanStore.getActivePlan('default');
            if (defPlan && defPlan.plannedTasks && defPlan.plannedTasks.length > 0) plan = defPlan;
        }
        if ((!plan || !plan.plannedTasks || plan.plannedTasks.length === 0) && window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.getActivePlan === 'function') {
            const wsPlan = window.TempoPlanWorkspace.getActivePlan();
            if (wsPlan && wsPlan.plannedTasks && wsPlan.plannedTasks.length > 0) plan = wsPlan;
        }
        if (!plan || !plan.plannedTasks || plan.plannedTasks.length === 0) {
            try {
                const saved = localStorage.getItem('tempo_working_plan') || localStorage.getItem('tempo_store_active_emergency_guest');
                if (saved) {
                    const parsed = JSON.parse(saved);
                    if (parsed && Array.isArray(parsed.plannedTasks) && parsed.plannedTasks.length > 0) plan = parsed;
                }
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

    function getUrmodeTaskData(taskId) {
        if (!taskId) return null;
        const sTaskId = String(taskId);
        const plan = getUrmodeActivePlan();
        let matchedTask = null;
        let matchedPlanItem = null;
        const renderedItem = renderedUrmodeTasksMap.get(sTaskId);

        // 1. Direct match from currently rendered task cards map
        if (renderedItem) {
            matchedPlanItem = renderedItem;
            if (renderedItem.task) matchedTask = renderedItem.task;
            else matchedTask = renderedItem;
        }

        // 2. Search in plan.plannedTasks
        if (!matchedTask && plan && Array.isArray(plan.plannedTasks)) {
            for (const pt of plan.plannedTasks) {
                const t = pt.task || pt;
                if (t && (String(t.id) === sTaskId || String(pt.id) === sTaskId || String(pt.taskId) === sTaskId)) {
                    matchedTask = t;
                    matchedPlanItem = pt;
                    break;
                }
            }
        }

        // 3. Search in unarrangedTasks
        if (!matchedTask && plan && Array.isArray(plan.unarrangedTasks)) {
            for (const u of plan.unarrangedTasks) {
                const t = u.task || u;
                if (t && (String(t.id) === sTaskId || String(u.id) === sTaskId)) {
                    matchedTask = t;
                    matchedPlanItem = u;
                    break;
                }
            }
        }

        // 4. Search in unallocatedTasks
        if (!matchedTask && plan && Array.isArray(plan.unallocatedTasks)) {
            for (const u of plan.unallocatedTasks) {
                const t = u.task || u;
                if (t && (String(t.id) === sTaskId || String(u.id) === sTaskId)) {
                    matchedTask = t;
                    matchedPlanItem = u;
                    break;
                }
            }
        }

        // 5. Search in plan.tasks
        if (!matchedTask && plan && Array.isArray(plan.tasks)) {
            for (const t of plan.tasks) {
                if (t && String(t.id) === sTaskId) {
                    matchedTask = t;
                    break;
                }
            }
        }

        // 6. Search in completedTasks or doneTasks
        if (!matchedTask && plan) {
            const cList = Array.isArray(plan.completedTasks) ? plan.completedTasks : (Array.isArray(plan.doneTasks) ? plan.doneTasks : []);
            for (const c of cList) {
                const t = c.task || c;
                if (t && (String(t.id) === sTaskId || String(c.id) === sTaskId)) {
                    matchedTask = t;
                    matchedPlanItem = c;
                    break;
                }
            }
        }

        // 7. Fallback for mock tasks
        const mockTasks = {
            'task-marketing-research': {
                id: 'task-marketing-research',
                name: 'Marketing Research',
                title: 'Marketing Research',
                hasDeadline: true,
                deadlineDate: '2026-10-17',
                deadlineTime: '21:00',
                deadline: '2026-10-17 21:00',
                durationLabel: '2h 30m',
                userLabel: 'Now',
                completed: false,
                description: 'Create a sheet to manage references',
                note: 'Create a sheet to manage references',
                subtasks: [
                    { id: 'sub-1', title: 'Subtask 1: Outline', completed: false, durationMinutes: 30 },
                    { id: 'sub-2', title: 'Subtask 2: Literature Review', completed: false, durationMinutes: 45 },
                    { id: 'sub-3', title: 'Subtask 3: Research Gap', completed: false, durationMinutes: 30 },
                    { id: 'sub-4', title: 'Subtask 4: Methodology', completed: false, durationMinutes: 20 },
                    { id: 'sub-5', title: 'Subtask 5: Data Analysis', completed: false, durationMinutes: 15 },
                    { id: 'sub-6', title: 'Subtask 6: Summary Report', completed: false, durationMinutes: 10 }
                ]
            },
            'task-event-proposal': {
                id: 'task-event-proposal',
                name: 'Event Proposal',
                title: 'Event Proposal',
                hasDeadline: true,
                deadlineDate: '2026-10-18',
                deadlineTime: '22:00',
                deadline: '2026-10-18 22:00',
                durationLabel: '2h 30m',
                userLabel: 'Then',
                completed: false,
                description: 'Coordinate with design team for event collateral',
                note: 'Coordinate with design team for event collateral',
                subtasks: [
                    { id: 'ep-sub-1', title: 'Subtask 1: Budget Draft', completed: false, durationMinutes: 45 },
                    { id: 'ep-sub-2', title: 'Subtask 2: Venue Options', completed: false, durationMinutes: 60 },
                    { id: 'ep-sub-3', title: 'Subtask 3: Guest List', completed: false, durationMinutes: 45 }
                ]
            },
            'task-edit-video': {
                id: 'task-edit-video',
                name: 'Edit Video',
                title: 'Edit Video',
                hasDeadline: true,
                deadlineDate: '2026-10-20',
                deadlineTime: '22:00',
                deadline: '2026-10-20 22:00',
                durationLabel: '2h 30m',
                userLabel: 'Later',
                completed: false,
                description: 'Export in 1080p format for social channels',
                note: 'Export in 1080p format for social channels',
                subtasks: []
            }
        };

        if (!matchedTask && mockTasks[sTaskId]) {
            matchedTask = mockTasks[sTaskId];
        }

        if (!matchedTask && window.TempoToolNotes && typeof window.TempoToolNotes.getAvailableTasks === 'function') {
            const avail = window.TempoToolNotes.getAvailableTasks();
            const found = avail.find(t => t && String(t.id) === sTaskId);
            if (found) {
                matchedTask = found;
            }
        }

        if (matchedTask) {
            try {
                const mockTasksState = JSON.parse(localStorage.getItem('tempo_rmode_mock_tasks') || '{}');
                if (typeof mockTasksState[sTaskId] === 'boolean') {
                    matchedTask.completed = mockTasksState[sTaskId];
                }
            } catch (e) {}
        }

        return { plan, task: matchedTask, plannedItem: matchedPlanItem || renderedItem };
    }

    function persistUrmodePlanData(plan, task) {
        if (task) {
            if (renderedUrmodeTasksMap.has(String(task.id))) {
                const item = renderedUrmodeTasksMap.get(String(task.id));
                if (item) {
                    item.task = task;
                    item.name = task.name || item.name;
                    item.completed = !!task.completed;
                    if (task.deadlineDate) {
                        item.dueDate = `${isViLocale() ? 'Deadline:' : 'Due:'} ${formatPlanDateHeader(task.deadlineDate, task.deadlineDate)}`;
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
                        dayDate: task.deadlineDate || getLocalTodayISO(),
                        dayLabel: 'Hôm nay',
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

        // Also sync mock tasks in localStorage if applicable
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

        renderEmodeHome();
        if (typeof renderActiveModeHome === 'function') {
            renderActiveModeHome();
        }
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
        }
    }

    function openUrmodeTaskDetailModal(taskId) {
        activeUrmodeDetailTaskId = taskId;
        isUrmodeDetailEditingTitle = false;
        isUrmodeDetailEditingDeadline = false;
        isUrmodeDetailEditingNote = false;
        isUrmodeDetailLabelMenuOpen = false;
        isUrmodeDetailAddingSubtask = false;
        editingUrmodeSubtaskId = null;
        renderUrmodeTaskDetailModalDOM();
    }

    function closeUrmodeTaskDetailModal() {
        activeUrmodeDetailTaskId = null;
        isUrmodeDetailEditingTitle = false;
        isUrmodeDetailEditingDeadline = false;
        isUrmodeDetailEditingNote = false;
        isUrmodeDetailLabelMenuOpen = false;
        isUrmodeDetailAddingSubtask = false;
        editingUrmodeSubtaskId = null;
        const globalRoot = document.getElementById('urmode-task-modal-global-root');
        if (globalRoot) {
            globalRoot.innerHTML = '';
        }
        renderUrmodeTaskDetailModalDOM();
    }

    function isUrmodeTaskDetailModalOpen() {
        return Boolean(activeUrmodeDetailTaskId);
    }

    function renderUrmodeTaskDetailModalDOM() {
        let root = document.getElementById('urmode-task-modal-root');
        if (!root || root.closest('.hidden')) {
            let globalRoot = document.getElementById('urmode-task-modal-global-root');
            if (!globalRoot) {
                globalRoot = document.createElement('div');
                globalRoot.id = 'urmode-task-modal-global-root';
                document.body.appendChild(globalRoot);
            }
            globalRoot.innerHTML = renderUrmodeTaskDetailModalHTML();
            return;
        }
        root.innerHTML = renderUrmodeTaskDetailModalHTML();
    }

    function toggleUrmodeDetailTitleEdit() {
        isUrmodeDetailEditingTitle = !isUrmodeDetailEditingTitle;
        renderUrmodeTaskDetailModalDOM();
        if (isUrmodeDetailEditingTitle) {
            setTimeout(() => {
                const input = document.getElementById('urmode-edit-title-input');
                if (input) {
                    input.focus();
                    input.select();
                }
            }, 50);
        }
    }

    function saveUrmodeDetailTitleEdit(taskId) {
        const input = document.getElementById('urmode-edit-title-input');
        const newTitle = input ? input.value.trim() : '';
        if (!newTitle) return;

        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        taskInfo.task.name = newTitle;
        taskInfo.task.title = newTitle;
        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.name = newTitle;
            taskInfo.plannedItem.task.title = newTitle;
        }

        isUrmodeDetailEditingTitle = false;
        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function toggleUrmodeDetailDeadlineEdit() {
        isUrmodeDetailEditingDeadline = !isUrmodeDetailEditingDeadline;
        renderUrmodeTaskDetailModalDOM();
    }

    function saveUrmodeDetailDeadlineEdit(taskId) {
        const dateInput = document.getElementById('urmode-edit-deadline-date');
        const timeInput = document.getElementById('urmode-edit-deadline-time');
        const noDeadlineInput = document.getElementById('urmode-edit-no-deadline');

        const noDeadline = noDeadlineInput ? noDeadlineInput.checked : false;
        const date = dateInput ? dateInput.value : '';
        const time = timeInput ? timeInput.value : '';

        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        if (noDeadline) {
            taskInfo.task.hasDeadline = false;
            taskInfo.task.deadlineDate = '';
            taskInfo.task.deadlineTime = '';
            taskInfo.task.deadline = 'No fixed deadline';
        } else {
            taskInfo.task.hasDeadline = true;
            taskInfo.task.deadlineDate = date;
            taskInfo.task.deadlineTime = time || taskInfo.task.deadlineTime || '';
            taskInfo.task.deadline = taskInfo.task.deadlineTime ? `${date} ${taskInfo.task.deadlineTime}` : date;
        }

        delete taskInfo.task.isOverdue;
        taskInfo.task.isOverdue = false;

        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.hasDeadline = taskInfo.task.hasDeadline;
            taskInfo.plannedItem.task.deadlineDate = taskInfo.task.deadlineDate;
            taskInfo.plannedItem.task.deadlineTime = taskInfo.task.deadlineTime;
            taskInfo.plannedItem.task.deadline = taskInfo.task.deadline;
            delete taskInfo.plannedItem.task.isOverdue;
            taskInfo.plannedItem.task.isOverdue = false;
        }

        isUrmodeDetailEditingDeadline = false;
        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function toggleUrmodeDetailNoteEdit() {
        isUrmodeDetailEditingNote = !isUrmodeDetailEditingNote;
        renderUrmodeTaskDetailModalDOM();
        if (isUrmodeDetailEditingNote) {
            setTimeout(() => {
                const textarea = document.getElementById('urmode-note-editor-text');
                if (textarea) {
                    textarea.focus();
                    textarea.select();
                }
            }, 50);
        }
    }

    function saveUrmodeDetailNote(taskId) {
        const input = document.getElementById('urmode-note-editor-text');
        const text = input ? input.value.trim() : '';
        const taskInfo = getUrmodeTaskData(taskId);
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

        isUrmodeDetailEditingNote = false;
        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function deleteUrmodeDetailNote(taskId) {
        const taskInfo = getUrmodeTaskData(taskId);
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

        isUrmodeDetailEditingNote = false;
        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function toggleUrmodeDetailTaskComplete(taskId) {
        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        const currentDone = !!taskInfo.task.completed;
        const newDone = !currentDone;

        taskInfo.task.completed = newDone;
        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.completed = newDone;
        }

        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function toggleUrmodeDetailSubtask(taskId, subtaskId) {
        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task || !Array.isArray(taskInfo.task.subtasks)) return;

        const step = taskInfo.task.subtasks.find(s => s && String(s.id) === String(subtaskId));
        if (step) {
            step.completed = !step.completed;
            persistUrmodePlanData(taskInfo.plan, taskInfo.task);
            renderUrmodeTaskDetailModalDOM();
        }
    }

    function toggleUrmodeDetailAddSubtask() {
        isUrmodeDetailAddingSubtask = !isUrmodeDetailAddingSubtask;
        renderUrmodeTaskDetailModalDOM();
        if (isUrmodeDetailAddingSubtask) {
            setTimeout(() => {
                const input = document.getElementById('urmode-new-subtask-title');
                if (input) input.focus();
            }, 50);
        }
    }

    function addUrmodeDetailSubtask(taskId) {
        const input = document.getElementById('urmode-new-subtask-title');
        const title = input ? input.value.trim() : '';
        if (!title) return;

        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        if (!Array.isArray(taskInfo.task.subtasks)) {
            taskInfo.task.subtasks = [];
        }

        const newSubtask = {
            id: `urmode-sub-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
            title: title,
            completed: false,
            durationMinutes: 15
        };

        taskInfo.task.subtasks.push(newSubtask);
        if (taskInfo.plannedItem && taskInfo.plannedItem.task && taskInfo.plannedItem.task !== taskInfo.task) {
            if (!Array.isArray(taskInfo.plannedItem.task.subtasks)) taskInfo.plannedItem.task.subtasks = [];
            taskInfo.plannedItem.task.subtasks.push(newSubtask);
        }

        isUrmodeDetailAddingSubtask = false;
        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function removeUrmodeDetailSubtask(taskId, subtaskId) {
        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task || !Array.isArray(taskInfo.task.subtasks)) return;

        taskInfo.task.subtasks = taskInfo.task.subtasks.filter(s => s && String(s.id) !== String(subtaskId));
        if (taskInfo.plannedItem && taskInfo.plannedItem.task && Array.isArray(taskInfo.plannedItem.task.subtasks)) {
            taskInfo.plannedItem.task.subtasks = taskInfo.plannedItem.task.subtasks.filter(s => s && String(s.id) !== String(subtaskId));
        }

        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function toggleUrmodeDetailSubtaskEdit(subtaskId) {
        editingUrmodeSubtaskId = subtaskId;
        renderUrmodeTaskDetailModalDOM();
        if (subtaskId) {
            setTimeout(() => {
                const input = document.getElementById(`urmode-edit-subtask-input-${subtaskId}`);
                if (input) {
                    input.focus();
                    input.select();
                }
            }, 50);
        }
    }

    function saveUrmodeDetailSubtaskTitle(taskId, subtaskId) {
        const input = document.getElementById(`urmode-edit-subtask-input-${subtaskId}`);
        const newTitle = input ? input.value.trim() : '';
        if (!newTitle) return;

        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task || !Array.isArray(taskInfo.task.subtasks)) return;

        const step = taskInfo.task.subtasks.find(s => s && String(s.id) === String(subtaskId));
        if (step) {
            step.title = newTitle;
        }

        editingUrmodeSubtaskId = null;
        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function toggleUrmodeDetailLabelMenu() {
        isUrmodeDetailLabelMenuOpen = !isUrmodeDetailLabelMenuOpen;
        renderUrmodeTaskDetailModalDOM();
    }

    function setUrmodeDetailTaskLabel(taskId, newLabel) {
        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        taskInfo.task.userLabel = newLabel;
        if (taskInfo.plannedItem) {
            taskInfo.plannedItem.tag = newLabel;
            taskInfo.plannedItem.executionBadge = newLabel;
        }

        isUrmodeDetailLabelMenuOpen = false;
        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function promptClearUrmodeTask(taskId) {
        if (!confirm('Bạn có chắc chắn muốn xóa task này khỏi kế hoạch không?')) return;
        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.plan) {
            closeUrmodeTaskDetailModal();
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

        closeUrmodeTaskDetailModal();
        persistUrmodePlanData(plan);
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast('Task removed from working plan.');
        }
    }

    function handleUrmodeTaskFocus(taskId) {
        closeUrmodeTaskDetailModal();
        startTaskFocus(taskId);
    }

    function handleUrmodeTaskReschedule(taskId) {
        closeUrmodeTaskDetailModal();
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.openRescheduleModal === 'function') {
            window.TempoPlanWorkspace.openRescheduleModal(taskId);
        }
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('tool-workplan', taskId);
        } else {
            window.location.hash = '#tool-workplan';
        }
    }

    function renderUrmodeTaskDetailModalHTML() {
        if (!activeUrmodeDetailTaskId) return '';

        const taskInfo = getUrmodeTaskData(activeUrmodeDetailTaskId);
        if (!taskInfo || !taskInfo.task) return '';

        const task = taskInfo.task;
        const plannedItem = taskInfo.plannedItem;
        const isDone = !!task.completed;

        // Schedule string
        let detailScheduleStr = isViLocale() ? `Lịch linh hoạt • ~${task.durationLabel || '1h'}` : `Flexible schedule • ~${task.durationLabel || '1h'}`;
        const itemDayDate = (plannedItem && plannedItem.dayDate) || task.dayDate || task._dayDate;
        const itemSchedLabel = itemDayDate ? formatScheduledDateLabel(itemDayDate, isViLocale()) : '';
        if (plannedItem && plannedItem.timeHeader) {
            detailScheduleStr = plannedItem.timeHeader;
        } else if (plannedItem && plannedItem.startTime && plannedItem.endTime) {
            detailScheduleStr = `${itemSchedLabel || formatScheduledDateLabel(getLocalTodayISO(), isViLocale())}, ${formatTime12H(plannedItem.startTime)} to ${formatTime12H(plannedItem.endTime)}`;
        } else if (itemSchedLabel) {
            detailScheduleStr = `${itemSchedLabel}, ${isViLocale() ? 'Đã lên lịch' : 'Scheduled'}`;
        } else if (task.timeHeader) {
            detailScheduleStr = task.timeHeader;
        } else if (task.deadlineDate) {
            detailScheduleStr = `${isViLocale() ? 'Deadline:' : 'Due:'} ${formatPlanDateHeader(task.deadlineDate, task.deadlineDate)}`;
        }

        // Priority Badge (dynamically evaluated from task or plannedItem)
        let priorityBadge = 'Up Next';
        if (task.userLabel === 'Now' || (plannedItem && (plannedItem.tag === 'Now' || plannedItem.executionBadge === 'Now' || plannedItem.isNow))) {
            priorityBadge = 'Now';
        } else if (task.userLabel === 'Then' || task.userLabel === 'Up Next' || (plannedItem && (plannedItem.tag === 'Then' || plannedItem.tag === 'Up Next' || plannedItem.executionBadge === 'Then' || plannedItem.executionBadge === 'Up Next'))) {
            priorityBadge = 'Up Next';
        } else if (task.userLabel === 'Later' || (plannedItem && (plannedItem.tag === 'Later' || plannedItem.executionBadge === 'Later' || plannedItem.isUnscheduled))) {
            priorityBadge = 'Later';
        }
        if (isDone) priorityBadge = 'Done';

        // Subtasks calculations
        const subtasks = Array.isArray(task.subtasks) ? task.subtasks : [];
        const totalSubtasks = subtasks.length;
        const completedSubtasks = subtasks.filter(s => s && s.completed).length;

        // Note / Description
        const noteText = (task.note || task.description || (window.TempoToolNotes && window.TempoToolNotes.getTaskNote ? window.TempoToolNotes.getTaskNote(task.id) : '') || '').trim();

        return `
            <div id="urmode-task-detail-modal" 
                 class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-stone-900/50 backdrop-blur-xs transition-all duration-150"
                 onclick="if(event.target === this) window.TempoMode.closeUrmodeTaskDetailModal();"
                 role="dialog"
                 aria-modal="true"
                 aria-labelledby="urmode-task-modal-title">
                
                <div class="bg-[#FDFBF6] border border-[#E3C7A5] rounded-3xl p-6 sm:p-7 max-w-lg w-full max-h-[90vh] overflow-y-auto space-y-4 shadow-xl relative text-left"
                     onclick="event.stopPropagation();">
                    
                    <!-- Close Button (✕) -->
                    <button type="button" 
                            onclick="window.TempoMode.closeUrmodeTaskDetailModal()"
                            class="absolute top-5 right-5 w-8 h-8 rounded-full bg-[#F3EDE2] hover:bg-[#EAE0D1] text-[#6B5E51] hover:text-[#2D2823] flex items-center justify-center text-sm font-bold transition cursor-pointer"
                            aria-label="${isViLocale() ? 'Đóng chi tiết công việc' : 'Close task detail'}">
                        ✕
                    </button>

                    <!-- Schedule Header -->
                    <div class="text-xs sm:text-sm font-bold text-[#D9A18B] tracking-wide pr-8">
                        ${escapeHTML(detailScheduleStr)}
                    </div>

                    <!-- Title and Priority Badge Row -->
                    <div class="flex items-center justify-between gap-3 pb-1">
                        <div class="flex-1 min-w-0 pr-2">
                            ${isUrmodeDetailEditingTitle ? `
                                <div class="flex items-center gap-2">
                                    <input id="urmode-edit-title-input" 
                                           type="text" 
                                           value="${escapeHTML(task.name || '')}" 
                                           class="w-full px-3 py-1.5 text-base font-bold text-[#202124] border border-[#D99E87] rounded-xl bg-white focus:outline-hidden focus:ring-2 focus:ring-[#D99E87]"
                                           onkeydown="if(event.key==='Enter') window.TempoMode.saveUrmodeDetailTitleEdit('${task.id}'); if(event.key==='Escape') window.TempoMode.toggleUrmodeDetailTitleEdit();" />
                                    <button type="button" 
                                            onclick="window.TempoMode.saveUrmodeDetailTitleEdit('${task.id}')"
                                            class="px-3 py-1.5 bg-[#D99E87] text-white rounded-xl text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                        Save
                                    </button>
                                    <button type="button" 
                                            onclick="window.TempoMode.toggleUrmodeDetailTitleEdit()"
                                            class="px-2.5 py-1.5 border border-stone-300 text-stone-600 rounded-xl text-xs font-bold hover:bg-stone-100 cursor-pointer">
                                        Cancel
                                    </button>
                                </div>
                            ` : `
                                <div class="flex items-center gap-2 group">
                                    <h2 id="urmode-task-modal-title" class="font-heading text-xl sm:text-2xl font-bold text-[#202124] truncate ${isDone ? 'line-through text-stone-400' : ''}">
                                        ${escapeHTML(task.name || 'Untitled Task')}
                                    </h2>
                                    <button type="button" 
                                            onclick="window.TempoMode.toggleUrmodeDetailTitleEdit()" 
                                            class="text-[#D99E87] hover:text-[#C98E77] text-xs font-semibold p-1 hover:bg-[#F3EDE2] rounded-md transition cursor-pointer" 
                                            title="${isViLocale() ? 'Chỉnh sửa tên task' : 'Edit task name'}">
                                        ✎
                                    </button>
                                </div>
                            `}
                        </div>

                        <!-- Priority Badge with Dropdown -->
                        <div class="relative inline-block shrink-0">
                            <button type="button"
                                    ${isDone ? 'disabled' : `onclick="window.TempoMode.toggleUrmodeDetailLabelMenu()"`}
                                    class="px-3 py-1 rounded-full text-xs font-bold transition flex items-center space-x-1 ${
                                        isDone
                                            ? 'bg-[#E8EFE8] text-[#556B54]'
                                            : (priorityBadge === 'Now' ? 'bg-[#D79277] text-white hover:bg-[#C98E77]' : (priorityBadge === 'Up Next' || priorityBadge === 'Then' ? 'bg-[#D3DFE4] text-[#5A6B73] hover:bg-[#C5D3D9]' : 'bg-[#EAE4DF] text-[#78716C] hover:bg-[#DDD6D0]'))
                                    } ${isDone ? 'cursor-default' : 'cursor-pointer'}">
                                <span>${isDone ? (isViLocale() ? 'Hoàn thành' : 'Done') : (priorityBadge === 'Now' ? (isViLocale() ? 'Làm ngay' : 'Now') : (priorityBadge === 'Later' ? (isViLocale() ? 'Để sau' : 'Later') : (priorityBadge || 'Up Next')))}</span>
                                ${!isDone ? '<span class="text-[10px] ml-0.5">▾</span>' : ''}
                            </button>

                            ${(!isDone && isUrmodeDetailLabelMenuOpen) ? `
                                <div class="absolute right-0 mt-1.5 w-32 bg-white border border-[#EAE4DF] rounded-xl shadow-lg z-20 py-1 text-xs">
                                    <button type="button"
                                            onclick="window.TempoMode.setUrmodeDetailTaskLabel('${task.id}', 'Now');"
                                            class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${priorityBadge === 'Now' ? 'font-bold text-[#D79277]' : ''}">
                                        <span>${isViLocale() ? 'Làm ngay' : 'Now'}</span>
                                        ${priorityBadge === 'Now' ? '<span>✓</span>' : ''}
                                    </button>
                                    <button type="button"
                                            onclick="window.TempoMode.setUrmodeDetailTaskLabel('${task.id}', 'Up Next');"
                                            class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${(priorityBadge === 'Up Next' || priorityBadge === 'Then') ? 'font-bold text-[#5A6B73]' : ''}">
                                        <span>Up Next</span>
                                        ${(priorityBadge === 'Up Next' || priorityBadge === 'Then') ? '<span>✓</span>' : ''}
                                    </button>
                                    <button type="button"
                                            onclick="window.TempoMode.setUrmodeDetailTaskLabel('${task.id}', 'Later');"
                                            class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${priorityBadge === 'Later' ? 'font-bold text-[#78716C]' : ''}">
                                        <span>${isViLocale() ? 'Sau nữa' : 'Later'}</span>
                                        ${priorityBadge === 'Later' ? '<span>✓</span>' : ''}
                                    </button>
                                </div>
                            ` : ''}
                        </div>
                    </div>

                    <!-- Due Date Row -->
                    <div class="flex items-center space-x-2 text-xs sm:text-sm text-[#6F6B68]">
                        <span>${isViLocale() ? 'Deadline:' : 'Due:'} ${escapeHTML(formatRmodeDeadline(task.deadlineDate || task.deadline, task.deadlineTime))}</span>
                        ${isTaskOverdue(task) ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">${(window.t ? window.t('modes.urgent.overdueBadge') : null) || (isViLocale() ? 'TRỄ DEADLINE' : 'OVERDUE')}</span>` : ''}
                        ${(!isTaskOverdue(task) && isTaskMissedSchedule(plannedItem || task)) ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-stone-100 text-stone-700 border border-stone-300">${isViLocale() ? 'TASK QUÁ LỊCH' : 'MISSED SCHEDULE'}</span>` : ''}
                        <button type="button"
                                onclick="window.TempoMode.toggleUrmodeDetailDeadlineEdit()"
                                class="text-[#D99E87] font-semibold hover:underline cursor-pointer">
                            ${isUrmodeDetailEditingDeadline ? (isViLocale() ? 'Hủy' : 'Cancel') : (isViLocale() ? 'Sửa deadline' : 'Edit deadline')}
                        </button>
                    </div>

                    <!-- Inline Deadline Editor -->
                    ${isUrmodeDetailEditingDeadline ? `
                        <div class="p-3 bg-white border border-[#E3C7A5] rounded-xl space-y-2 text-xs">
                            <div class="grid grid-cols-2 gap-2">
                                <div>
                                    <label class="block text-[10px] text-gray-500 font-semibold mb-0.5">Date</label>
                                    <input id="urmode-edit-deadline-date" type="date" value="${task.deadlineDate || (task.deadline ? task.deadline.split(' ')[0] : '')}" class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                </div>
                                <div>
                                    <label class="block text-[10px] text-gray-500 font-semibold mb-0.5">Time</label>
                                    <input id="urmode-edit-deadline-time" type="time" value="${task.deadlineTime || (task.deadline && task.deadline.includes(':') ? task.deadline.split(' ')[1] : '23:59')}" class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                </div>
                            </div>
                            <div class="flex items-center space-x-2">
                                <input id="urmode-edit-no-deadline" type="checkbox" ${task.hasDeadline === false ? 'checked' : ''} class="rounded text-[#D99E87]">
                                <label for="urmode-edit-no-deadline" class="text-xs text-stone-700">${isViLocale() ? 'Chưa có deadline' : 'No fixed deadline'}</label>
                            </div>
                            <div class="flex justify-end pt-1">
                                <button type="button"
                                        onclick="window.TempoMode.saveUrmodeDetailDeadlineEdit('${task.id}')"
                                        class="px-3 py-1 bg-[#D99E87] text-white rounded-lg text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                    ${isViLocale() ? 'Lưu deadline' : 'Save deadline'}
                                </button>
                            </div>
                        </div>
                    ` : ''}

                    <!-- Subtasks Count Row & Controls -->
                    <div class="flex items-center justify-between text-xs sm:text-sm text-[#6F6B68]">
                        ${totalSubtasks > 0 ? `<span>${completedSubtasks}/${totalSubtasks} ${isViLocale() ? 'bước đã xong' : 'action steps completed'}</span>` : '<span></span>'}
                        <button type="button"
                                onclick="window.TempoMode.toggleUrmodeDetailAddSubtask()"
                                class="text-[#D99E87] font-semibold hover:underline cursor-pointer flex items-center space-x-1">
                            <span>${isViLocale() ? '+ Thêm bước nhỏ' : '+ Add action step'}</span>
                        </button>
                    </div>

                    <!-- Add Subtask Input Form -->
                    ${isUrmodeDetailAddingSubtask ? `
                        <div class="flex items-center gap-2 p-2.5 bg-white border border-[#E3C7A5] rounded-xl">
                            <input id="urmode-new-subtask-title" 
                                   type="text" 
                                   placeholder="${isViLocale() ? 'Nhập tên bước hành động mới...' : 'Enter new action step...'}"
                                   class="flex-1 px-2.5 py-1 text-xs border border-gray-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-[#D99E87]"
                                   onkeydown="if(event.key==='Enter') window.TempoMode.addUrmodeDetailSubtask('${task.id}'); if(event.key==='Escape') window.TempoMode.toggleUrmodeDetailAddSubtask();" />
                            <button type="button" 
                                    onclick="window.TempoMode.addUrmodeDetailSubtask('${task.id}')"
                                    class="px-3 py-1 bg-[#D99E87] text-white rounded-lg text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                Add
                            </button>
                            <button type="button" 
                                    onclick="window.TempoMode.toggleUrmodeDetailAddSubtask()"
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
                                            onclick="window.TempoMode.toggleUrmodeDetailSubtask('${task.id}', '${step.id}')"
                                            class="w-4 h-4 rounded border border-[#E3C7A5] flex items-center justify-center text-[10px] font-bold transition shrink-0 cursor-pointer ${step.completed ? 'bg-[#92A491] border-[#92A491] text-white' : 'bg-white border-[#E3C7A5] text-transparent hover:border-[#D99E87]'}"
                                            title="${isViLocale() ? 'Đánh dấu bước nhỏ' : 'Toggle step'}">
                                        ✓
                                    </button>
                                    ${editingUrmodeSubtaskId === step.id ? `
                                        <div class="flex items-center gap-1.5 flex-1 min-w-0">
                                            <input id="urmode-edit-subtask-input-${step.id}" 
                                                   type="text" 
                                                   value="${escapeHTML(step.title || '')}" 
                                                   class="flex-1 px-2 py-0.5 text-xs border border-[#D99E87] rounded-md bg-white focus:outline-hidden"
                                                   onkeydown="if(event.key==='Enter') window.TempoMode.saveUrmodeDetailSubtaskTitle('${task.id}', '${step.id}'); if(event.key==='Escape') window.TempoMode.toggleUrmodeDetailSubtaskEdit(null);" />
                                            <button type="button" 
                                                    onclick="window.TempoMode.saveUrmodeDetailSubtaskTitle('${task.id}', '${step.id}')" 
                                                    class="text-xs text-[#D99E87] font-bold px-1 hover:underline cursor-pointer">Save</button>
                                            <button type="button" 
                                                    onclick="window.TempoMode.toggleUrmodeDetailSubtaskEdit(null)" 
                                                    class="text-xs text-stone-500 px-1 hover:underline cursor-pointer">Cancel</button>
                                        </div>
                                    ` : `
                                        <span class="truncate ${step.completed ? 'line-through text-stone-400' : ''}">${escapeHTML(step.title)}</span>
                                        <button type="button" 
                                                onclick="window.TempoMode.toggleUrmodeDetailSubtaskEdit('${step.id}')" 
                                                class="opacity-0 group-hover:opacity-100 text-[#D99E87] hover:text-[#C98E77] text-xs font-semibold px-1 transition cursor-pointer" 
                                                title="${isViLocale() ? 'Chỉnh sửa bước nhỏ' : 'Edit step'}">
                                            ✎
                                        </button>
                                    `}
                                </div>
                                <button type="button"
                                        onclick="window.TempoMode.removeUrmodeDetailSubtask('${task.id}', '${step.id}')"
                                        class="opacity-0 group-hover:opacity-100 text-stone-400 hover:text-rose-600 text-xs px-1.5 py-0.5 rounded transition cursor-pointer"
                                        title="${isViLocale() ? 'Xóa bước nhỏ' : 'Delete step'}">
                                    ✕
                                </button>
                            </div>
                        `).join('') : `
                            <div class="p-3 text-xs text-stone-400 italic text-center border border-dashed border-[#EDE2D5] rounded-xl bg-white/40">
                                No subtasks yet
                            </div>
                        `}
                    </div>

                    <!-- Note / Description Section -->
                    ${isUrmodeDetailEditingNote ? `
                        <div class="p-3 bg-white border border-[#E3C7A5] rounded-xl space-y-2">
                            <label class="block text-xs font-bold text-[#D9A18B]">${isViLocale() ? 'Ghi chú Công việc' : 'Task Note'}</label>
                            <textarea id="urmode-note-editor-text" 
                                      rows="3" 
                                      class="w-full p-2 text-xs border border-gray-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-[#D99E87]"
                                      placeholder="${isViLocale() ? 'Thêm chi tiết, liên kết hoặc ghi chú cho task này...' : 'Add details, links, or notes for this task...'}">${escapeHTML(noteText)}</textarea>
                            <div class="flex justify-between items-center pt-1">
                                ${noteText ? `
                                    <button type="button" 
                                            onclick="window.TempoMode.deleteUrmodeDetailNote('${task.id}')"
                                            class="text-xs text-rose-600 hover:underline cursor-pointer">
                                        ${isViLocale() ? 'Xóa ghi chú' : 'Delete note'}
                                    </button>
                                ` : '<div></div>'}
                                <div class="flex space-x-2">
                                    <button type="button" 
                                            onclick="window.TempoMode.toggleUrmodeDetailNoteEdit()"
                                            class="px-2.5 py-1 text-xs text-stone-600 border border-stone-300 rounded-lg hover:bg-stone-100 cursor-pointer">
                                        Cancel
                                    </button>
                                    <button type="button" 
                                            onclick="window.TempoMode.saveUrmodeDetailNote('${task.id}')"
                                            class="px-3 py-1 bg-[#D99E87] text-white rounded-lg text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                        ${isViLocale() ? 'Lưu ghi chú' : 'Save note'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    ` : (noteText ? `
                        <div class="text-xs sm:text-sm text-[#4A4540] pt-1 flex items-start justify-between gap-2 bg-[#F6F4EE]/60 border border-[#EAE4DF] rounded-xl p-2.5">
                            <div class="min-w-0 flex-1">
                                <strong class="text-[#D9A18B]">${isViLocale() ? 'Ghi chú:' : 'Note:'}</strong> <span class="whitespace-pre-line text-[#4A4540]">${escapeHTML(noteText)}</span>
                            </div>
                            <button type="button"
                                    onclick="window.TempoMode.toggleUrmodeDetailNoteEdit()"
                                    class="text-[#D99E87] hover:text-[#C98E77] text-xs font-semibold shrink-0 cursor-pointer flex items-center space-x-1"
                                    title="${isViLocale() ? 'Chỉnh sửa ghi chú' : 'Edit note'}">
                                <span>${isViLocale() ? 'Chỉnh sửa ghi chú' : 'Edit note'}</span>
                                <span>✎</span>
                            </button>
                        </div>
                    ` : `
                        <div class="pt-1">
                            <button type="button"
                                    onclick="window.TempoMode.toggleUrmodeDetailNoteEdit()"
                                    class="text-xs font-bold text-[#D9A18B] hover:underline cursor-pointer flex items-center space-x-1">
                                <span>${isViLocale() ? '+ Tạo ghi chú' : '+ Add note'}</span>
                            </button>
                        </div>
                    `)}

                    <!-- Action Buttons (2x2 grid) -->
                    <div class="grid grid-cols-2 gap-3 pt-3">
                        <!-- 1. Mark as done / active -->
                        <button type="button"
                                onclick="window.TempoMode.toggleUrmodeDetailTaskComplete('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#92A491] hover:bg-[#829381] shadow-2xs transition text-center cursor-pointer">
                            ${isDone ? (isViLocale() ? 'Đang thực hiện' : 'Mark as active') : (isViLocale() ? 'Hoàn thành' : 'Mark as done')}
                        </button>

                        <!-- 2. Focus now -->
                        <button type="button"
                                onclick="window.TempoMode.handleUrmodeTaskFocus('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#D7A690] hover:bg-[#C98E77] shadow-2xs transition flex items-center justify-center space-x-1.5 cursor-pointer">
                            <span>▶ ${isViLocale() ? 'Làm ngay' : 'Focus now'}</span>
                        </button>

                        <!-- 3. Reschedule -->
                        <button type="button"
                                onclick="window.TempoMode.handleUrmodeTaskReschedule('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#3A4B3D] bg-white border border-[#8D9B8A] hover:bg-stone-50 transition text-center cursor-pointer">
                            ${isViLocale() ? 'Đổi lịch' : 'Reschedule'}
                        </button>

                        <!-- 4. Clear this task -->
                        <button type="button"
                                onclick="window.TempoMode.promptClearUrmodeTask('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#C53B27] bg-white border border-[#D99E87] hover:bg-rose-50/40 transition text-center cursor-pointer">
                            ${isViLocale() ? 'Xóa task này' : 'Clear this task'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    