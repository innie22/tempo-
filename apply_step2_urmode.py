import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('urmodeFlow.js', 'r', encoding='utf-8', newline='') as f:
    text = f.read()

assert '\r\n' not in text, "urmodeFlow.js has CRLF!"

new_step2 = """    // Step 2: Adjust retained tasks & add new tasks
    function renderAdjustmentStep2Tasks() {
        activeModalView = 'adjust_tasks';
        const kept = adjustmentDraft.retainedTasks.filter(t => t._keep);

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${window.t ? window.t('workspace.adjustPlanStep2', {}, 'STEP 2 OF 3 · ADJUST PLAN') : (isViLocale() ? 'BƯỚC 2/3 · ĐIỀU CHỈNH PLAN' : 'STEP 2 OF 3 · ADJUST PLAN')}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${window.t ? window.t('workspace.adjustEstimatesAndAddTasks', {}, 'Adjust estimates & add new tasks') : (isViLocale() ? 'Điều chỉnh thời lượng & thêm task mới' : 'Adjust estimates & add new tasks')}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.handleAdjustmentStep2Back()"
                        aria-label="${window.t ? window.t('common.back', {}, 'Back') : (isViLocale() ? 'Quay lại' : 'Back')}"
                        title="${window.t ? window.t('common.back', {}, 'Back') : (isViLocale() ? 'Quay lại' : 'Back')}"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer">
                    ←
                </button>
            </div>

            <!-- Retained tasks list -->
            <div class="space-y-2 max-h-56 sm:max-h-60 overflow-y-auto pr-1 py-1">
                <div class="text-[11px] font-bold uppercase tracking-wider text-stone-500">
                    ${window.t ? window.t('workspace.retainedTasksCount', { count: kept.length }, `RETAINED TASKS (${kept.length}):`) : (isViLocale() ? `CÁC TASK ĐƯỢC GIỮ LẠI (${kept.length}):` : `RETAINED TASKS (${kept.length}):`)}
                </div>
                ${kept.map(t => `
                    <div class="p-3 rounded-2xl border border-stone-200 bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 text-xs">
                        <div class="min-w-0 flex-1">
                            <span class="font-bold text-stone-800 truncate block">${escapeHTML(t.name || t.title)}</span>
                        </div>
                        <div class="flex items-center gap-2 shrink-0 flex-wrap">
                            <div class="flex items-center space-x-1.5">
                                <label for="adjust-due-${t.id}" class="text-[11px] font-semibold text-stone-500">
                                    ${window.t ? window.t('workspace.duePrefixLabel', {}, 'Due:') : (isViLocale() ? 'Deadline:' : 'Due:')}
                                </label>
                                <input type="date"
                                       id="adjust-due-${t.id}"
                                       value="${t.deadlineDate || ''}"
                                       onchange="window.TempoUrmodeFlow.updateRetainedDueDate('${t.id}', this.value)"
                                       oninput="window.TempoUrmodeFlow.updateRetainedDueDate('${t.id}', this.value)"
                                       class="px-2.5 py-1.5 rounded-xl border border-stone-300 text-xs text-stone-700 bg-white focus:outline-none focus:ring-1 focus:ring-[#D79277]" />
                            </div>
                            <select id="adjust-dur-${t.id}"
                                    onchange="window.TempoUrmodeFlow.updateRetainedDuration('${t.id}', this.value)"
                                    class="px-2.5 py-1.5 rounded-xl border border-stone-300 text-xs font-medium text-stone-700 bg-white focus:outline-none focus:ring-1 focus:ring-[#D79277]">
                                <option value="15" ${t.durationMinutes === 15 ? 'selected' : ''}>${isViLocale() ? '15 phút' : '15 min'}</option>
                                <option value="30" ${t.durationMinutes === 30 ? 'selected' : ''}>${isViLocale() ? '30 phút' : '30 min'}</option>
                                <option value="45" ${t.durationMinutes === 45 ? 'selected' : ''}>${isViLocale() ? '45 phút' : '45 min'}</option>
                                <option value="60" ${t.durationMinutes === 60 ? 'selected' : ''}>${isViLocale() ? '1 giờ' : '1 hr'}</option>
                                <option value="90" ${t.durationMinutes === 90 ? 'selected' : ''}>${isViLocale() ? '1,5 giờ' : '1.5 hr'}</option>
                                <option value="120" ${t.durationMinutes === 120 ? 'selected' : ''}>${isViLocale() ? '2 giờ' : '2 hr'}</option>
                            </select>
                        </div>
                    </div>
                `).join('')}
            </div>

            <!-- Add new task section -->
            <div class="p-3.5 bg-stone-50 border border-stone-200 rounded-2xl space-y-2.5 pt-2.5">
                <div class="text-[11px] font-bold uppercase tracking-wider text-stone-600">
                    ${window.t ? window.t('workspace.addNewTaskUpper', {}, '+ ADD NEW TASK:') : (isViLocale() ? '+ THÊM TASK MỚI:' : '+ ADD NEW TASK:')}
                </div>
                <div class="flex flex-wrap sm:flex-nowrap items-center gap-2">
                    <input type="text" id="adjust-new-task-name"
                           placeholder="${window.t ? window.t('workspace.taskNamePlaceholderEllipsis', {}, 'Task name...') : (isViLocale() ? 'Tên task...' : 'Task name...')}"
                           class="flex-1 min-w-[130px] px-3 py-1.5 rounded-xl border border-stone-300 text-xs bg-white text-stone-800 placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-[#D79277]" />
                    <div class="flex items-center space-x-1.5 shrink-0">
                        <label for="adjust-new-task-due" class="text-[11px] font-semibold text-stone-500">
                            ${window.t ? window.t('workspace.duePrefixLabel', {}, 'Due:') : (isViLocale() ? 'Deadline:' : 'Due:')}
                        </label>
                        <input type="date" id="adjust-new-task-due"
                               class="px-2.5 py-1.5 rounded-xl border border-stone-300 text-xs text-stone-700 bg-white focus:outline-none focus:ring-1 focus:ring-[#D79277]" />
                    </div>
                    <select id="adjust-new-task-dur"
                            class="px-2.5 py-1.5 rounded-xl border border-stone-300 text-xs text-stone-700 bg-white focus:outline-none focus:ring-1 focus:ring-[#D79277] shrink-0">
                        <option value="15">${isViLocale() ? '15 phút' : '15 min'}</option>
                        <option value="30" selected>${isViLocale() ? '30 phút' : '30 min'}</option>
                        <option value="45">${isViLocale() ? '45 phút' : '45 min'}</option>
                        <option value="60">${isViLocale() ? '1 giờ' : '1 hr'}</option>
                        <option value="90">${isViLocale() ? '1,5 giờ' : '1.5 hr'}</option>
                        <option value="120">${isViLocale() ? '2 giờ' : '2 hr'}</option>
                    </select>
                    <button type="button" onclick="window.TempoUrmodeFlow.addNewAdjustmentTask()"
                            class="px-3.5 py-1.5 rounded-xl bg-[#D79277] text-white font-bold text-xs hover:bg-[#C68166] transition cursor-pointer shrink-0">
                        ${window.t ? window.t('workspace.addPlain', {}, (isViLocale() ? 'Thêm' : 'Add')) : (isViLocale() ? 'Thêm' : 'Add')}
                    </button>
                </div>
                ${adjustmentDraft.newTasks.length > 0 ? `
                    <div id="adjust-new-tasks-list" class="space-y-1.5 pt-1">
                        ${adjustmentDraft.newTasks.map((nt, idx) => {
                            const dueFormatted = nt.hasDeadline && nt.deadlineDate ? (window.TempoI18n ? window.TempoI18n.formatCalendarDate(nt.deadlineDate, isViLocale() ? 'vi' : 'en') : nt.deadlineDate) : '';
                            const dueStr = dueFormatted ? ` • ${isViLocale() ? 'Deadline:' : 'Due:'} ${dueFormatted}` : '';
                            const durLabel = (nt.durationMinutes === 90) ? (isViLocale() ? '1,5 giờ' : '1.5 hr') : formatDuration(nt.durationMinutes);
                            return `
                                <div class="flex items-center justify-between text-xs text-stone-700 bg-white px-3 py-2 rounded-xl border border-stone-200">
                                    <div class="truncate mr-2 font-medium">
                                        <span class="text-[#D79277] font-bold">+</span> ${escapeHTML(nt.name)}
                                        <span class="text-stone-500 font-normal">(~${escapeHTML(durLabel)}${escapeHTML(dueStr)})</span>
                                    </div>
                                    <button type="button" onclick="window.TempoUrmodeFlow.removeAdjustmentNewTask(${idx})" class="text-stone-400 hover:text-rose-600 p-0.5 cursor-pointer shrink-0" title="${isViLocale() ? 'Xóa task' : 'Remove task'}">✕</button>
                                </div>
                            `;
                        }).join('')}
                    </div>
                ` : ''}
            </div>

            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-between gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.handleAdjustmentStep2Back()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs transition cursor-pointer">
                    ← ${window.t ? window.t('common.back', {}, 'Back') : (isViLocale() ? 'Quay lại' : 'Back')}
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.handleAdjustmentStep2Next()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm transition cursor-pointer">
                    ${window.t ? window.t('workspace.nextProposePlan', {}, 'Next: Propose plan →') : (isViLocale() ? 'Tiếp theo: Đề xuất plan →' : 'Next: Propose plan →')}
                </button>
            </div>
        `;

        showModalContent(html);
    }\n\n"""

idx1 = text.find('    // Step 2: Adjust retained tasks & add new tasks\n    function renderAdjustmentStep2Tasks() {')
assert idx1 != -1, "renderAdjustmentStep2Tasks not found!"
idx2 = text.find('    function syncStep2InputsFromDom()')
assert idx2 != -1, "syncStep2InputsFromDom not found!"

text = text[:idx1] + new_step2 + text[idx2:]

# Update onLanguageChange listener to also re-render Step 2
old_listener = """    if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
        window.TempoI18n.onLanguageChange(() => {
            if (activeModalView === 'adjust_keep') {
                renderAdjustmentStep1Keep();
            }
        });
    }"""

new_listener = """    if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
        window.TempoI18n.onLanguageChange(() => {
            if (activeModalView === 'adjust_keep') {
                renderAdjustmentStep1Keep();
            } else if (activeModalView === 'adjust_tasks') {
                const draftName = document.getElementById('adjust-new-task-name')?.value || '';
                const draftDue = document.getElementById('adjust-new-task-due')?.value || '';
                const draftDur = document.getElementById('adjust-new-task-dur')?.value || '30';
                syncStep2InputsFromDom();
                renderAdjustmentStep2Tasks();
                const newNameInput = document.getElementById('adjust-new-task-name');
                const newDueInput = document.getElementById('adjust-new-task-due');
                const newDurInput = document.getElementById('adjust-new-task-dur');
                if (newNameInput && draftName) newNameInput.value = draftName;
                if (newDueInput && draftDue) newDueInput.value = draftDue;
                if (newDurInput && draftDur) newDurInput.value = draftDur;
            }
        });
    }"""

assert old_listener in text, "old_listener not found in urmodeFlow.js"
text = text.replace(old_listener, new_listener, 1)

assert '\r\n' not in text, "urmodeFlow.js has CRLF after changes!"

with open('urmodeFlow.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print("urmodeFlow.js updated successfully with Step 2 localization! (LF only)")
