import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('urmodeFlow.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

start_marker = 'function showKeepPlanTaskPopup() {'
end_marker = '    function launchFocusForTask(taskId) {'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print('ERROR: markers for showKeepPlanTaskPopup not found')
    sys.exit(1)

replacement_function = '''function showKeepPlanTaskPopup() {
        activeModalView = 'keep_plan_task';
        const isVi = isViLocale();
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const topTask = tasks.find(t => !t.completed) || tasks[0];

        if (!topTask) {
            closeModal('dashboard');
            return;
        }

        const noDeadlineText = window.t
            ? window.t('workspace.noFixedDeadlineLabel', {}, isVi ? 'Chưa có deadline' : 'No fixed deadline')
            : (isVi ? 'Chưa có deadline' : 'No fixed deadline');

        const deadlineStr = topTask.hasDeadline && topTask.deadlineDate 
            ? formatDeadline(topTask.deadlineDate, topTask.deadlineTime) 
            : noDeadlineText;
        const durStr = topTask.durationLabel || formatDuration(topTask.durationMinutes);
        const subtasks = Array.isArray(topTask.subtasks) ? topTask.subtasks : [];

        const badgeText = window.t
            ? window.t('workspace.yourTaskForNowBadge', {}, isVi ? 'TASK HIỆN TẠI CỦA BẠN' : 'YOUR TASK FOR NOW')
            : (isVi ? 'TASK HIỆN TẠI CỦA BẠN' : 'YOUR TASK FOR NOW');

        const headingText = window.t
            ? window.t('workspace.yourTaskForNowHeading', {}, isVi ? 'Task bạn nên thực hiện lúc này là…' : 'Your task for now is…')
            : (isVi ? 'Task bạn nên thực hiện lúc này là…' : 'Your task for now is…');

        const doThisFirstText = window.t
            ? window.t('workspace.doThisFirstPriority', {}, isVi ? 'ƯU TIÊN LÀM TRƯỚC' : 'DO THIS FIRST')
            : (isVi ? 'ƯU TIÊN LÀM TRƯỚC' : 'DO THIS FIRST');

        const dueLabelText = window.t
            ? window.t('workspace.duePrefixLabel', {}, isVi ? 'Deadline:' : 'Due:')
            : (isVi ? 'Deadline:' : 'Due:');

        const laterBtnText = window.t
            ? window.t('workspace.laterBtn', {}, isVi ? 'Để sau' : 'Later')
            : (isVi ? 'Để sau' : 'Later');

        const focusNowBtnText = window.t
            ? window.t('workspace.focusNowBtn', {}, isVi ? 'Tập trung ngay →' : 'Focus now →')
            : (isVi ? 'Tập trung ngay →' : 'Focus now →');

        const closeBtnText = window.t
            ? window.t('common.close', {}, isVi ? 'Đóng' : 'Close dialog')
            : (isVi ? 'Đóng' : 'Close dialog');

        const actionStepsText = isVi ? 'Các bước thực hiện:' : 'Action steps:';

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${badgeText}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${headingText}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        aria-label="${closeBtnText}"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="${closeBtnText}">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Task Summary Card -->
            <div class="p-4 rounded-2xl border-2 border-[#D79277] bg-[#FFF9F5] space-y-2">
                <div class="flex items-center justify-between">
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#D79277] text-white">
                        ${doThisFirstText}
                    </span>
                    <span class="text-xs text-stone-500 font-medium">~${escapeHTML(durStr)}</span>
                </div>
                <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124]">
                    ${escapeHTML(topTask.name || topTask.title)}
                </h3>
                <div class="text-xs text-[#6F6B68] flex items-center space-x-2">
                    <span>📅 ${dueLabelText} ${escapeHTML(deadlineStr)}</span>
                </div>

                ${subtasks.length > 0 ? `
                    <div class="pt-2 border-t border-stone-200/60 space-y-1">
                        <div class="text-[11px] font-bold uppercase tracking-wider text-stone-500">${actionStepsText}</div>
                        ${subtasks.map(s => `
                            <div class="flex items-center space-x-2 text-xs text-stone-700">
                                <span>${s.completed ? '✓' : '○'}</span>
                                <span class="${s.completed ? 'line-through text-stone-400' : ''}">${escapeHTML(s.title || s.name)}</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>

            <!-- Action Buttons: Focus Now vs Later -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                    ${laterBtnText}
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.launchFocusForTask('${topTask.id}')"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                    <span>${focusNowBtnText}</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }

'''

content = content[:start_idx] + replacement_function + content[end_idx:]

target_onlang = '''            } else if (activeModalView === 'review_summary') {
                showReviewSummaryPopup();
            } else if (activeModalView === 'adjust_keep') {'''

replacement_onlang = '''            } else if (activeModalView === 'review_summary') {
                showReviewSummaryPopup();
            } else if (activeModalView === 'keep_plan_task') {
                showKeepPlanTaskPopup();
            } else if (activeModalView === 'adjust_keep') {'''

if target_onlang not in content:
    print('ERROR: target_onlang not found in content')
    sys.exit(1)

content = content.replace(target_onlang, replacement_onlang, 1)

with open('urmodeFlow.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print('Successfully updated urmodeFlow.js with Your Task for Now modal localization')
