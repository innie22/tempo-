with open('urmodeFlow.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

assert '\r' not in content, "urmodeFlow.js must be strictly LF"

# 1. Update showFirstTaskExecutionPopup
target_func = """    function showFirstTaskExecutionPopup() {
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
    }"""

replace_func = """    function showFirstTaskExecutionPopup() {
        activeModalView = 'first_task_choice';
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const topTask = (selectedWorkTaskId && tasks.find(t => String(t.id) === String(selectedWorkTaskId))) || tasks.find(t => !t.completed) || tasks[0];

        if (!topTask) {
            closeModal('plan-workspace');
            return;
        }

        let durStr = isViLocale() ? '30 phút' : '30 min';
        if (topTask) {
            if (topTask.durationMinutes === 90 || topTask.duration === 90 || topTask.estimateMinutes === 90 || topTask.durationLabel === '1.5 hr' || topTask.durationLabel === '1,5 giờ' || topTask.durationLabel === '1.5h') {
                durStr = isViLocale() ? '1,5 giờ' : '1.5 hr';
            } else if (topTask.durationMinutes) {
                durStr = formatDuration(topTask.durationMinutes);
            } else if (typeof formatTaskDuration === 'function') {
                durStr = formatTaskDuration(topTask);
            } else if (topTask.durationLabel) {
                durStr = topTask.durationLabel;
            }
        }

        let deadlineDisplay = '';
        if (topTask.hasDeadline && topTask.deadlineDate) {
            const formattedDeadline = formatDeadline(topTask.deadlineDate, topTask.deadlineTime);
            deadlineDisplay = `${isViLocale() ? 'Deadline:' : 'Due:'} ${formattedDeadline}`;
        } else {
            deadlineDisplay = window.t ? window.t('workspace.dueNoFixedDeadline', {}, (isViLocale() ? 'Deadline: Chưa có deadline' : 'Due: No fixed deadline')) : (isViLocale() ? 'Deadline: Chưa có deadline' : 'Due: No fixed deadline');
        }

        const subtasks = Array.isArray(topTask.subtasks) ? topTask.subtasks : [];

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${window.t ? window.t('workspace.firstTaskExecutionUpper', {}, 'FIRST TASK EXECUTION') : (isViLocale() ? 'BẮT ĐẦU TASK ĐẦU TIÊN' : 'FIRST TASK EXECUTION')}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${window.t ? window.t('workspace.yourFirstTaskIs', {}, 'Your first task is…') : (isViLocale() ? 'Task đầu tiên của bạn là…' : 'Your first task is…')}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('plan-workspace')"
                        aria-label="${window.t ? window.t('common.close', {}, 'Close dialog') : (isViLocale() ? 'Đóng' : 'Close dialog')}"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="${window.t ? window.t('common.close', {}, 'Close dialog') : (isViLocale() ? 'Đóng' : 'Close dialog')}">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Task Card -->
            <div class="p-4 rounded-2xl border-2 border-[#D79277] bg-[#FFF9F5] space-y-2">
                <div class="flex items-center justify-between">
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#D79277] text-white">
                        ${window.t ? window.t('workspace.readyNowBadge', {}, 'READY NOW') : (isViLocale() ? 'SẴN SÀNG THỰC HIỆN' : 'READY NOW')}
                    </span>
                    <span class="text-xs text-stone-500 font-medium">~${escapeHTML(durStr)}</span>
                </div>
                <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124]">
                    ${escapeHTML(topTask.name || topTask.title)}
                </h3>
                <div class="text-xs text-[#6F6B68] flex items-center space-x-2">
                    <span>📅 ${escapeHTML(deadlineDisplay)}</span>
                </div>
                ${subtasks.length > 0 ? `
                    <div class="pt-2 border-t border-stone-200/60 space-y-1">
                        <div class="text-[11px] font-bold uppercase tracking-wider text-stone-500">${subtasks.length} ${isViLocale() ? 'bước' : (subtasks.length === 1 ? 'step' : 'steps')}:</div>
                        ${subtasks.slice(0, 3).map((s, i) => `
                            <div class="text-xs text-stone-700 truncate">• ${escapeHTML(s.title || s.name)}</div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>

            <!-- Action Buttons: Do this task, Choose another task, Later -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-wrap items-center justify-between gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('plan-workspace')"
                        class="px-4 py-2 rounded-xl font-semibold text-xs text-stone-500 hover:text-stone-800 transition cursor-pointer">
                    ${window.t ? window.t('workspace.laterBtn', {}, 'Later') : (isViLocale() ? 'Để sau' : 'Later')}
                </button>
                <div class="flex items-center space-x-2.5">
                    <button type="button" onclick="window.TempoUrmodeFlow.showTaskSelectionPopup()"
                            class="px-4 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs transition cursor-pointer">
                        ${window.t ? window.t('workspace.chooseAnotherTaskBtn', {}, 'Choose another task') : (isViLocale() ? 'Chọn task khác' : 'Choose another task')}
                    </button>
                    <button type="button" onclick="window.TempoUrmodeFlow.launchFocusForTask('${topTask.id}')"
                            class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm transition cursor-pointer">
                        ${window.t ? window.t('workspace.doThisTaskBtn', {}, 'Do this task →') : (isViLocale() ? 'Bắt đầu task này →' : 'Do this task →')}
                    </button>
                </div>
            </div>
        `;

        showModalContent(html);
    }"""

assert target_func in content, "target_func not found in urmodeFlow.js"
content = content.replace(target_func, replace_func, 1)

# 2. Update onLanguageChange
target_lang = """            } else if (activeModalView === 'start_working_plan') {
                showStartWorkingPopup();
            }"""

replace_lang = """            } else if (activeModalView === 'start_working_plan') {
                showStartWorkingPopup();
            } else if (activeModalView === 'first_task_choice') {
                showFirstTaskExecutionPopup();
            }"""

assert target_lang in content, "target_lang not found in urmodeFlow.js"
content = content.replace(target_lang, replace_lang, 1)

assert '\r' not in content, "urmodeFlow.js must retain strictly LF line endings"

with open('urmodeFlow.js', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("urmodeFlow.js successfully patched for first task execution modal!")
