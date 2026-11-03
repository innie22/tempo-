import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. Update mode.js
with open('mode.js', 'rb') as f:
    raw = f.read()

assert b'\r\n' not in raw, 'mode.js must have 0 CRLF'
content = raw.decode('utf-8')

old_stale_block = '''        const currentOverdue = staleTasks[0];
        const overdueTask = currentOverdue?.task;
        const taskName = overdueTask?.name || 'Overdue Task';

        return `
            <div class="urgent-card-now from-[#FFF9F5] border-[#FFD2BA] rounded-3xl p-6 sm:p-7 soft-card-shadow relative overflow-hidden transition flex flex-col justify-between" style="background-color: #faeddb; border: 1px solid #000000; min-height: 290px;" data-tempo-ui="urgent-task-now">
                <div class="relative z-10 space-y-3">
                    <!-- Badge Row: OVERDUE TASK -->
                    <div class="flex items-center justify-between mb-3.5">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-amber-600 inline-block"></span>
                            <span class="px-4 py-1.5 rounded-full text-xs font-bold bg-amber-600 text-white shadow-2xs">
                                ${isViLocale() ? 'TASK QUÁ HẠN' : 'OVERDUE TASK'}
                            </span>
                            <span class="text-[11px] font-bold uppercase tracking-wider text-[#B83D08] sr-only">SCHEDULE UPDATE NEEDED</span>
                            <span class="sr-only">Your plan needs an update.</span>
                        </div>
                    </div>

                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68] sr-only">
                        ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                    </div>

                    <!-- Title Block -->
                    <div class="space-y-1">
                        <h3 class="font-heading text-2xl sm:text-[34px] font-extrabold text-[#484541] tracking-tight leading-snug">
                            ${isViLocale() ? 'Task này đã quá hạn' : 'This task is overdue'}
                        </h3>
                    </div>

                    <!-- Status Description / Message -->
                    <div class="flex items-center space-x-2.5 my-2">
                        <div class="w-4 h-4 rounded border-2 border-amber-600/60 bg-transparent flex items-center justify-center shrink-0 text-amber-700 text-[10px] font-bold">!</div>
                        <p class="italic text-sm sm:text-base font-medium text-[#5D5954]">
                            Looks like this task has passed its due date. Would you like to clear it, mark it as done, or update it?
                        </p>
                    </div>

                    <!-- Overdue Task Info Box -->
                    <div class="p-3.5 bg-white/90 rounded-2xl border border-[#FFD2BA] text-xs text-amber-950 space-y-1.5 my-1">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-stone-800 text-sm sm:text-base">• ${escapeHTML(taskName)}</span>
                            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-amber-100 text-amber-800 border border-amber-300">OVERDUE</span>
                        </div>
                        <div class="text-stone-500 text-[11px] flex flex-wrap items-center gap-2">
                            ${currentOverdue?.dayDate ? `<span>${isViLocale() ? 'Đã lên lịch:' : 'Was scheduled:'} ${escapeHTML(formatScheduledDateLabel(currentOverdue.dayDate, isViLocale()))}</span>` : ''}
                            ${overdueTask?.hasDeadline && overdueTask?.deadlineDate ? `<span>• ${isViLocale() ? 'Deadline:' : 'Due:'} ${window.TempoI18n ? window.TempoI18n.formatDeadline(overdueTask.deadlineDate, overdueTask.deadlineTime) : formatHumanDeadline(overdueTask.deadlineDate, overdueTask.deadlineTime)}</span>` : ''}
                            ${overdueTask?.durationLabel ? `<span>• ~${escapeHTML(overdueTask.durationLabel)}</span>` : ''}
                        </div>
                    </div>
                </div>

                <!-- Action Buttons Row (Clear task, Mark as done, Edit task) -->
                <div class="relative z-10 pt-4 border-t border-[#E8D9C5] flex flex-wrap items-center gap-3">
                    <button type="button" onclick="window.TempoMode.promptClearOverdueTask('${overdueTask?.id}')"
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-rose-50 text-rose-700 border border-rose-200 shadow-2xs inline-flex items-center transition cursor-pointer">
                        ${isViLocale() ? 'Xóa task này' : 'Clear task'}
                    </button>
                    <button type="button" onclick="window.TempoMode.markOverdueTaskDone('${overdueTask?.id}')"
                            class="btn-primary btn-terracotta bg-emerald-600 px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center transition cursor-pointer">
                        <span class="sr-only">Mark this task as finished - </span><span>${isViLocale() ? 'Đánh dấu hoàn thành' : 'Mark as done'}</span>
                    </button>
                    <button type="button" onclick="window.TempoApp.navigateTo('plan-workspace'); if (window.TempoPlanWorkspace && window.TempoPlanWorkspace.selectTask) { window.TempoPlanWorkspace.selectTask('${overdueTask?.id}'); }"
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center transition cursor-pointer">
                        <span class="sr-only">Update my plan - </span><span>${isViLocale() ? 'Chỉnh sửa task' : 'Edit task'}</span>
                    </button>
                </div>
            </div>
        `;'''

new_stale_block = '''        const currentOverdue = staleTasks[0];
        const overdueTask = currentOverdue?.task;
        const taskName = overdueTask?.name || 'Overdue Task';
        const isVi = typeof isViLocale === 'function' ? isViLocale() : false;

        const taskOverdueHeading = (window.t ? window.t('modes.urgent.taskOverdue') : null) || (isVi ? 'TASK TRỄ DEADLINE' : 'TASK OVERDUE');
        const thisTaskIsOverdue = (window.t ? window.t('modes.urgent.thisTaskIsOverdue') : null) || (isVi ? 'Task này đã trễ Deadline' : 'This task is overdue');
        const taskOverdueDesc = (window.t ? window.t('modes.urgent.taskOverdueDesc') : null) || (isVi ? 'Task này đã trễ deadline. Bạn muốn xóa, đánh dấu hoàn thành hay cập nhật lại?' : 'Looks like this task has passed its due date. Would you like to clear it, mark it as done, or update it?');
        const overdueBadgeText = (window.t ? window.t('modes.urgent.overdueBadge') : null) || (isVi ? 'TRỄ DEADLINE' : 'OVERDUE');
        const scheduledLabelText = (window.t ? window.t('modes.urgent.scheduledLabel') : null) || (isVi ? 'Ngày lên lịch:' : 'Scheduled:');
        const deadlineLabelText = (window.t ? window.t('modes.urgent.deadlineLabel') : null) || 'Deadline:';
        const clearThisTaskText = (window.t ? window.t('modes.urgent.clearThisTask') : null) || (isVi ? 'Xóa task này' : 'Clear this task');
        const markAsDoneText = (window.t ? window.t('modes.urgent.markAsDone') : null) || (isVi ? 'Hoàn thành' : 'Mark as done');
        const editTaskText = (window.t ? window.t('modes.urgent.editTask') : null) || (isVi ? 'Chỉnh sửa task' : 'Edit task');

        return `
            <div class="urgent-card-now from-[#FFF9F5] border-[#FFD2BA] rounded-3xl p-6 sm:p-7 soft-card-shadow relative overflow-hidden transition flex flex-col justify-between" style="background-color: #faeddb; border: 1px solid #000000; min-height: 290px;" data-tempo-ui="urgent-task-now">
                <div class="relative z-10 space-y-3">
                    <!-- Badge Row: OVERDUE TASK -->
                    <div class="flex items-center justify-between mb-3.5">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-amber-600 inline-block"></span>
                            <span class="px-4 py-1.5 rounded-full text-xs font-bold bg-amber-600 text-white shadow-2xs">
                                ${taskOverdueHeading}
                            </span>
                            <span class="text-[11px] font-bold uppercase tracking-wider text-[#B83D08] sr-only">SCHEDULE UPDATE NEEDED</span>
                            <span class="sr-only">Your plan needs an update.</span>
                        </div>
                    </div>

                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68] sr-only">
                        ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                    </div>

                    <!-- Title Block -->
                    <div class="space-y-1">
                        <h3 class="font-heading text-2xl sm:text-[34px] font-extrabold text-[#484541] tracking-tight leading-snug">
                            ${thisTaskIsOverdue}
                        </h3>
                    </div>

                    <!-- Status Description / Message -->
                    <div class="flex items-center space-x-2.5 my-2">
                        <div class="w-4 h-4 rounded border-2 border-amber-600/60 bg-transparent flex items-center justify-center shrink-0 text-amber-700 text-[10px] font-bold">!</div>
                        <p class="italic text-sm sm:text-base font-medium text-[#5D5954]">
                            ${taskOverdueDesc}
                        </p>
                    </div>

                    <!-- Overdue Task Info Box -->
                    <div class="p-3.5 bg-white/90 rounded-2xl border border-[#FFD2BA] text-xs text-amber-950 space-y-1.5 my-1">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-stone-800 text-sm sm:text-base">• ${escapeHTML(taskName)}</span>
                            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-amber-100 text-amber-800 border border-amber-300">${overdueBadgeText}</span>
                        </div>
                        <div class="text-stone-500 text-[11px] flex flex-wrap items-center gap-2">
                            ${currentOverdue?.dayDate ? `<span>${scheduledLabelText} ${escapeHTML(formatScheduledDateLabel(currentOverdue.dayDate, isVi ? 'vi' : 'en'))}</span>` : ''}
                            ${overdueTask?.hasDeadline && overdueTask?.deadlineDate ? `<span>• ${deadlineLabelText} ${window.TempoI18n ? window.TempoI18n.formatDeadline(overdueTask.deadlineDate, overdueTask.deadlineTime) : formatHumanDeadline(overdueTask.deadlineDate, overdueTask.deadlineTime)}</span>` : ''}
                            ${overdueTask?.durationLabel ? `<span>• ~${escapeHTML(overdueTask.durationLabel)}</span>` : ''}
                        </div>
                    </div>
                </div>

                <!-- Action Buttons Row (Clear task, Mark as done, Edit task) -->
                <div class="relative z-10 pt-4 border-t border-[#E8D9C5] flex flex-wrap items-center gap-3">
                    <button type="button" onclick="window.TempoMode.promptClearOverdueTask('${overdueTask?.id}')"
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-rose-50 text-rose-700 border border-rose-200 shadow-2xs inline-flex items-center transition cursor-pointer">
                        ${clearThisTaskText}
                    </button>
                    <button type="button" onclick="window.TempoMode.markOverdueTaskDone('${overdueTask?.id}')"
                            class="btn-primary btn-terracotta bg-emerald-600 px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center transition cursor-pointer">
                        <span class="sr-only">Mark this task as finished - </span><span>${markAsDoneText}</span>
                    </button>
                    <button type="button" onclick="window.TempoApp.navigateTo('plan-workspace'); if (window.TempoPlanWorkspace && window.TempoPlanWorkspace.selectTask) { window.TempoPlanWorkspace.selectTask('${overdueTask?.id}'); }"
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center transition cursor-pointer">
                        <span class="sr-only">Update my plan - </span><span>${editTaskText}</span>
                    </button>
                </div>
            </div>
        `;'''

assert old_stale_block in content, 'old_stale_block not found in mode.js'
content = content.replace(old_stale_block, new_stale_block, 1)

# Also update overdue badges in mode.js
# 1. line 7404
old_badge_1 = "${item.isOverdue ? `<span class=\"px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300\">OVERDUE</span>` : ''}"
new_badge_1 = "${item.isOverdue ? `<span class=\"px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300\">${(window.t ? window.t('modes.urgent.overdueBadge') : null) || (isViLocale() ? 'TRỄ DEADLINE' : 'OVERDUE')}</span>` : ''}"
assert old_badge_1 in content, 'old_badge_1 not found in mode.js'
content = content.replace(old_badge_1, new_badge_1, 1)

# 2. line 8329
old_badge_2 = "${isTaskOverdue(task) ? `<span class=\"px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300\">OVERDUE</span>` : ''}"
new_badge_2 = "${isTaskOverdue(task) ? `<span class=\"px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300\">${(window.t ? window.t('modes.urgent.overdueBadge') : null) || (isViLocale() ? 'TRỄ DEADLINE' : 'OVERDUE')}</span>` : ''}"
assert old_badge_2 in content, 'old_badge_2 not found in mode.js'
content = content.replace(old_badge_2, new_badge_2, 1)

# 3. line 9335
old_badge_3 = "${isTaskOverdue(task) ? `<span class=\"px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300\">${isViLocale() ? 'QUÁ HẠN' : 'OVERDUE'}</span>` : ''}"
new_badge_3 = "${isTaskOverdue(task) ? `<span class=\"px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300\">${(window.t ? window.t('modes.urgent.overdueBadge') : null) || (isViLocale() ? 'TRỄ DEADLINE' : 'OVERDUE')}</span>` : ''}"
assert old_badge_3 in content, 'old_badge_3 not found in mode.js'
content = content.replace(old_badge_3, new_badge_3, 1)

new_raw = content.encode('utf-8')
assert b'\r\n' not in new_raw, 'mode.js must remain strictly LF'
with open('mode.js', 'wb') as f:
    f.write(new_raw)

print(f'Successfully updated mode.js! Lines: {len(new_raw.split(b"\n"))}')

# 2. Update planWorkspace.js
with open('planWorkspace.js', 'rb') as f:
    raw_pw = f.read()

assert b'\r\n' not in raw_pw, 'planWorkspace.js must have 0 CRLF'
content_pw = raw_pw.decode('utf-8')

old_pw_badge_1 = "${isTaskOverdue(task) ? `<span class=\"px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300\">${isViLocale() ? 'QUÁ HẠN' : 'OVERDUE'}</span>` : ''}"
new_pw_badge_1 = "${isTaskOverdue(task) ? `<span class=\"px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300\">${(window.t ? window.t('modes.urgent.overdueBadge') : null) || (isViLocale() ? 'TRỄ DEADLINE' : 'OVERDUE')}</span>` : ''}"
assert content_pw.count(old_pw_badge_1) == 2, 'old_pw_badge_1 should appear 2 times in planWorkspace.js'
content_pw = content_pw.replace(old_pw_badge_1, new_pw_badge_1)

old_pw_badge_2 = "${isTaskOverdue(selectedTask) ? `<span class=\"px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300\">${isViLocale() ? 'QUÁ HẠN' : 'OVERDUE'}</span>` : ''}"
new_pw_badge_2 = "${isTaskOverdue(selectedTask) ? `<span class=\"px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300\">${(window.t ? window.t('modes.urgent.overdueBadge') : null) || (isViLocale() ? 'TRỄ DEADLINE' : 'OVERDUE')}</span>` : ''}"
assert old_pw_badge_2 in content_pw, 'old_pw_badge_2 not found in planWorkspace.js'
content_pw = content_pw.replace(old_pw_badge_2, new_pw_badge_2, 1)

new_raw_pw = content_pw.encode('utf-8')
assert b'\r\n' not in new_raw_pw, 'planWorkspace.js must remain strictly LF'
with open('planWorkspace.js', 'wb') as f:
    f.write(new_raw_pw)

print(f'Successfully updated planWorkspace.js! Lines: {len(new_raw_pw.split(b"\n"))}')

# 3. Update urmodeFlow.js
with open('urmodeFlow.js', 'rb') as f:
    raw_uf = f.read()

assert b'\r\n' not in raw_uf, 'urmodeFlow.js must have 0 CRLF'
content_uf = raw_uf.decode('utf-8')

old_uf_badge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-amber-100 text-amber-800 border border-amber-300">\n                                                OVERDUE\n                                            </span>'
new_uf_badge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-amber-100 text-amber-800 border border-amber-300">\n                                                ${(window.t ? window.t(\'modes.urgent.overdueBadge\') : null) || (typeof isViLocale === \'function\' && isViLocale() ? \'TRỄ DEADLINE\' : \'OVERDUE\')}\n                                            </span>'

if old_uf_badge in content_uf:
    content_uf = content_uf.replace(old_uf_badge, new_uf_badge)
    new_raw_uf = content_uf.encode('utf-8')
    assert b'\r\n' not in new_raw_uf, 'urmodeFlow.js must remain strictly LF'
    with open('urmodeFlow.js', 'wb') as f:
        f.write(new_raw_uf)
    print(f'Successfully updated urmodeFlow.js!')
