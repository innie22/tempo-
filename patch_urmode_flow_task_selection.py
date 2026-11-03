with open('urmodeFlow.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

assert '\r' not in content, "urmodeFlow.js must be strictly LF"

# 1. Update showTaskSelectionPopup
target_func = """    function showTaskSelectionPopup() {
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
    }"""

replace_func = """    function showTaskSelectionPopup() {
        activeModalView = 'select_another_task';
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan).filter(t => !t.completed);

        function formatTaskCardDuration(t) {
            if (t.durationMinutes === 90 || t.duration === 90 || t.estimateMinutes === 90 || t.durationLabel === '1.5 hr' || t.durationLabel === '1,5 giờ' || t.durationLabel === '1.5h') {
                return isViLocale() ? '1,5 giờ' : '1.5 hr';
            }
            if (t.durationMinutes) {
                return formatDuration(t.durationMinutes);
            }
            if (typeof formatTaskDuration === 'function') {
                return formatTaskDuration(t);
            }
            return t.durationLabel || (isViLocale() ? '30 phút' : '30 min');
        }

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${window.t ? window.t('workspace.taskSelectionUpper', {}, 'TASK SELECTION') : (isViLocale() ? 'CHỌN TASK' : 'TASK SELECTION')}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${window.t ? window.t('workspace.selectTaskToWorkOn', {}, 'Select a task to work on') : (isViLocale() ? 'Chọn task bạn muốn thực hiện' : 'Select a task to work on')}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.showFirstTaskExecutionPopup()"
                        aria-label="${window.t ? window.t('common.back', {}, 'Back') : (isViLocale() ? 'Quay lại' : 'Back')}"
                        title="${window.t ? window.t('common.back', {}, 'Back') : (isViLocale() ? 'Quay lại' : 'Back')}"
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
                                <div class="font-bold text-stone-800 truncate">${escapeHTML(t.name || t.title)}</div>
                                <div class="text-[11px] text-stone-500">~${escapeHTML(formatTaskCardDuration(t))}</div>
                            </div>
                        </div>
                        <span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-stone-100 text-stone-700 shrink-0">
                            ${window.t ? window.t('workspace.selectTaskWithArrow', {}, 'Select →') : (isViLocale() ? 'Chọn →' : 'Select →')}
                        </span>
                    </div>
                `).join('')}
            </div>

            <div class="pt-4 border-t border-[#EAE4DF]/80 flex justify-end">
                <button type="button" onclick="window.TempoUrmodeFlow.showFirstTaskExecutionPopup()"
                        class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs transition cursor-pointer">
                    ${window.t ? window.t('common.back', {}, 'Back') : (isViLocale() ? 'Quay lại' : 'Back')}
                </button>
            </div>
        `;

        showModalContent(html);
    }"""

assert target_func in content, "target_func not found in urmodeFlow.js"
content = content.replace(target_func, replace_func, 1)

# 2. Update onLanguageChange
target_lang = """            } else if (activeModalView === 'first_task_choice') {
                showFirstTaskExecutionPopup();
            }"""

replace_lang = """            } else if (activeModalView === 'first_task_choice') {
                showFirstTaskExecutionPopup();
            } else if (activeModalView === 'select_another_task') {
                showTaskSelectionPopup();
            }"""

assert target_lang in content, "target_lang not found in urmodeFlow.js"
content = content.replace(target_lang, replace_lang, 1)

assert '\r' not in content, "urmodeFlow.js must retain strictly LF line endings"

with open('urmodeFlow.js', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("urmodeFlow.js successfully patched for task selection modal!")
