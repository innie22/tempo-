with open('urmodeFlow.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

assert '\r' not in content, "urmodeFlow.js must be strictly LF"

# 1. Update showStartWorkingPopup
target_start_func = """    function showStartWorkingPopup() {
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
    }"""

replace_start_func = """    function showStartWorkingPopup() {
        activeModalView = 'start_working_plan';
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const topTask = tasks.find(t => !t.completed) || tasks[0];

        let durStr = isViLocale() ? '30 phút' : '30 min';
        if (topTask) {
            if (topTask.durationMinutes === 90 || topTask.duration === 90 || topTask.estimateMinutes === 90 || topTask.durationLabel === '1.5 hr' || topTask.durationLabel === '1,5 giờ') {
                durStr = isViLocale() ? '1,5 giờ' : '1.5 hr';
            } else if (topTask.durationMinutes) {
                durStr = formatDuration(topTask.durationMinutes);
            } else if (typeof formatTaskDuration === 'function') {
                durStr = formatTaskDuration(topTask);
            } else if (topTask.durationLabel) {
                durStr = topTask.durationLabel;
            }
        }

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${window.t ? window.t('workspace.readyToWorkUpper', {}, 'READY TO WORK') : (isViLocale() ? 'SẴN SÀNG BẮT ĐẦU' : 'READY TO WORK')}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${window.t ? window.t('workspace.startWorkingOnPlanTitle', {}, 'Start working on your plan?') : (isViLocale() ? 'Bắt đầu làm việc nhé?' : 'Start working on your plan?')}
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

            <div class="py-3 text-center sm:text-left space-y-2">
                <p class="text-sm sm:text-base text-[#484541] leading-relaxed">
                    ${window.t ? window.t('workspace.startWorkingOnPlanDesc', {}, 'Your working plan is ready. Would you like to start right away on your first task?') : (isViLocale() ? 'Kế hoạch làm việc của bạn đã sẵn sàng. Bạn muốn bắt đầu với task đầu tiên ngay bây giờ không?' : 'Your working plan is ready. Would you like to start right away on your first task?')}
                </p>
                ${topTask ? `
                    <div class="p-3 bg-[#FFF9F5] border border-[#FFD2BA] rounded-2xl flex items-center justify-between text-xs">
                        <span class="font-bold text-[#202124]">${window.t ? window.t('workspace.firstTaskPrefix', {}, 'First task:') : (isViLocale() ? 'Task đầu tiên:' : 'First task:')} ${escapeHTML(topTask.name || topTask.title)}</span>
                        <span class="text-[#8C8782]">~${escapeHTML(durStr)}</span>
                    </div>
                ` : ''}
            </div>

            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-wrap items-center justify-between gap-3">
                <div class="flex items-center space-x-2">
                    <button type="button" onclick="window.TempoUrmodeFlow.closeModal('plan-workspace')"
                            class="px-4 py-2 rounded-xl font-semibold text-xs text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ${window.t ? window.t('workspace.laterBtn', {}, 'Later') : (isViLocale() ? 'Để sau' : 'Later')}
                    </button>
                    <button type="button" onclick="window.TempoUrmodeFlow.restartBreakdownFlow()"
                            class="px-4 py-2 rounded-xl font-semibold text-xs text-[#D79277] hover:underline transition cursor-pointer">
                        ${window.t ? window.t('workspace.breakMoreTasksBtn', {}, 'Break more tasks') : (isViLocale() ? 'Chia nhỏ thêm task' : 'Break more tasks')}
                    </button>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.showFirstTaskExecutionPopup()"
                        class="btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center space-x-2 transition cursor-pointer">
                    <span>${window.t ? window.t('workspace.yesStartWorkingBtn', {}, 'Yes, start working →') : (isViLocale() ? 'Có, bắt đầu thôi →' : 'Yes, start working →')}</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }"""

assert target_start_func in content, "target_start_func not found in urmodeFlow.js"
content = content.replace(target_start_func, replace_start_func, 1)

# 2. Update onLanguageChange
target_lang_change = """            } else if (activeModalView === 'post_save_task_now') {
                showTaskForNowPopupAfterSave(lastPostSavePlan);
            }"""

replace_lang_change = """            } else if (activeModalView === 'post_save_task_now') {
                showTaskForNowPopupAfterSave(lastPostSavePlan);
            } else if (activeModalView === 'start_working_plan') {
                showStartWorkingPopup();
            }"""

assert target_lang_change in content, "target_lang_change not found in urmodeFlow.js"
content = content.replace(target_lang_change, replace_lang_change, 1)

assert '\r' not in content, "urmodeFlow.js must retain strictly LF line endings"

with open('urmodeFlow.js', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("urmodeFlow.js successfully patched!")
