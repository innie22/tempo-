import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('urmodeFlow.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

start_marker = 'function showReviewSummaryPopup() {'
end_marker = '    function showKeepPlanTaskPopup() {'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print('ERROR: markers not found')
    sys.exit(1)

replacement_function = '''function formatExecutionBadge(rawBadge, isVi) {
        if (!rawBadge) return isVi ? 'TIẾP THEO' : 'UP NEXT';
        const normalized = String(rawBadge).trim().toUpperCase();
        if (normalized === 'UP NEXT') {
            return window.t
                ? window.t('workspace.badgeUpNext', {}, isVi ? 'TIẾP THEO' : 'UP NEXT')
                : (isVi ? 'TIẾP THEO' : 'UP NEXT');
        }
        if (normalized === 'THEN') {
            return window.t
                ? window.t('workspace.badgeThen', {}, isVi ? 'SAU ĐÓ' : 'THEN')
                : (isVi ? 'SAU ĐÓ' : 'THEN');
        }
        if (normalized === 'LATER') {
            return window.t
                ? window.t('workspace.badgeLater', {}, isVi ? 'ĐỂ SAU' : 'LATER')
                : (isVi ? 'ĐỂ SAU' : 'LATER');
        }
        if (normalized === 'OVERDUE') {
            return window.t
                ? window.t('workspace.badgeOverdue', {}, isVi ? 'QUÁ HẠN' : 'OVERDUE')
                : (isVi ? 'QUÁ HẠN' : 'OVERDUE');
        }
        return rawBadge;
    }

    function showReviewSummaryPopup() {
        activeModalView = 'review_summary';
        const isVi = isViLocale();
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const overdueCount = tasks.filter(t => isTaskOverdue(t, plan)).length;

        const badgeText = window.t
            ? window.t('workspace.workingPlanReviewBadge', {}, isVi ? 'XEM LẠI PLAN' : 'WORKING PLAN REVIEW')
            : (isVi ? 'XEM LẠI PLAN' : 'WORKING PLAN REVIEW');
        const titleText = window.t
            ? window.t('workspace.workingPlanSummaryTitle', {}, isVi ? 'Tổng quan kế hoạch làm việc' : 'Your Working Plan Summary')
            : (isVi ? 'Tổng quan kế hoạch làm việc' : 'Your Working Plan Summary');
        const closeBtnText = window.t
            ? window.t('common.close', {}, isVi ? 'Đóng' : 'Close dialog')
            : (isVi ? 'Đóng' : 'Close dialog');

        const overdueCountText = window.t
            ? (isVi
                ? window.t('workspace.tasksOverdueCount', { count: overdueCount }, `${overdueCount} task đã quá hạn:`)
                : (overdueCount === 1
                    ? window.t('workspace.taskOverdueSingleCount', { count: overdueCount }, '1 task overdue:')
                    : window.t('workspace.tasksOverdueCount', { count: overdueCount }, `${overdueCount} tasks overdue:`)))
            : (isVi ? `${overdueCount} task đã quá hạn:` : (overdueCount === 1 ? '1 task overdue:' : `${overdueCount} tasks overdue:`));

        const overdueDescText = window.t
            ? window.t('workspace.overdueWarningDesc', {}, isVi ? 'Một số task đã quá ngày lên lịch hoặc deadline. Bạn có thể giữ lại hoặc điều chỉnh lịch trình.' : 'Some tasks passed their planned date or deadline. You can keep them or adjust your schedule.')
            : (isVi ? 'Một số task đã quá ngày lên lịch hoặc deadline. Bạn có thể giữ lại hoặc điều chỉnh lịch trình.' : 'Some tasks passed their planned date or deadline. You can keep them or adjust your schedule.');

        const overdueBadgeText = window.t
            ? window.t('workspace.badgeOverdue', {}, isVi ? 'QUÁ HẠN' : 'OVERDUE')
            : (isVi ? 'QUÁ HẠN' : 'OVERDUE');

        const noDeadlineText = window.t
            ? window.t('workspace.noFixedDeadlineLabel', {}, isVi ? 'Chưa có deadline' : 'No fixed deadline')
            : (isVi ? 'Chưa có deadline' : 'No fixed deadline');

        const adjustPlanBtnText = window.t
            ? window.t('workspace.adjustMyPlanBtn', {}, isVi ? 'Điều chỉnh plan' : 'Adjust my plan')
            : (isVi ? 'Điều chỉnh plan' : 'Adjust my plan');

        const keepPlanBtnText = window.t
            ? window.t('workspace.keepThePlanBtn', {}, isVi ? 'Giữ nguyên plan →' : 'Keep the plan →')
            : (isVi ? 'Giữ nguyên plan →' : 'Keep the plan →');

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${badgeText}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${titleText}
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

            <!-- Overdue Warning Banner if applicable -->
            ${overdueCount > 0 ? `
                <div class="p-3 bg-amber-50 border border-amber-200/80 rounded-2xl flex items-center space-x-3 text-xs text-amber-900">
                    <span class="text-base shrink-0">⚠️</span>
                    <div>
                        <strong class="font-bold">${overdueCountText}</strong>
                        <span>${overdueDescText}</span>
                    </div>
                </div>
            ` : ''}

            <!-- Task List -->
            <div class="max-h-64 sm:max-h-72 overflow-y-auto space-y-2 pr-1 py-1">
                ${tasks.map((t, idx) => {
                    const overdue = isTaskOverdue(t, plan);
                    const deadlineStr = t.hasDeadline && t.deadlineDate ? formatDeadline(t.deadlineDate, t.deadlineTime) : noDeadlineText;
                    const durStr = t.durationLabel || formatDuration(t.durationMinutes);
                    const isDone = t.completed === true;

                    return `
                        <div class="p-3 rounded-2xl border ${overdue ? 'border-amber-300 bg-amber-50/40' : 'border-stone-200 bg-white'} flex items-center justify-between text-xs transition">
                            <div class="flex items-center space-x-2.5 min-w-0 flex-1 mr-2">
                                <span class="font-bold text-stone-400 w-5 shrink-0 text-center">${idx + 1}.</span>
                                <div class="min-w-0">
                                    <div class="font-bold text-stone-800 truncate ${isDone ? 'line-through text-stone-400' : ''}">
                                        ${escapeHTML(t.name)}
                                    </div>
                                    <div class="text-[11px] text-stone-500 flex items-center space-x-2 mt-0.5">
                                        <span>${escapeHTML(deadlineStr)}</span>
                                        <span>•</span>
                                        <span>~${escapeHTML(durStr)}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="flex items-center space-x-1.5 shrink-0">
                                ${overdue ? `
                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                                        ${overdueBadgeText}
                                    </span>
                                ` : ''}
                                ${isDone ? `
                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700">
                                        ✓ ${isVi ? 'Đã xong' : 'Done'}
                                    </span>
                                ` : `
                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-stone-100 text-stone-600">
                                        ${escapeHTML(formatExecutionBadge(t._executionBadge || 'UP NEXT', isVi))}
                                    </span>
                                `}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>

            <!-- Action Buttons: Keep Plan vs Adjust Plan -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.startAdjustmentFlow()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                    ${adjustPlanBtnText}
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.showKeepPlanTaskPopup()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                    <span>${keepPlanBtnText}</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }

'''

content = content[:start_idx] + replacement_function + content[end_idx:]

# Update onLanguageChange
target_onlang = '''            if (activeModalView === 'reset') {
                showResetPopup(currentResetCase);
            } else if (activeModalView === 'adjust_keep') {'''

replacement_onlang = '''            if (activeModalView === 'reset') {
                showResetPopup(currentResetCase);
            } else if (activeModalView === 'review_summary') {
                showReviewSummaryPopup();
            } else if (activeModalView === 'adjust_keep') {'''

if target_onlang not in content:
    print('ERROR: target_onlang not found in content')
    sys.exit(1)

content = content.replace(target_onlang, replacement_onlang, 1)

with open('urmodeFlow.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print('Successfully updated urmodeFlow.js')
