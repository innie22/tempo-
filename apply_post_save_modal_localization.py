import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('urmodeFlow.js', 'r', encoding='utf-8', newline='') as f:
    text = f.read()

assert '\r\n' not in text, "urmodeFlow.js has CRLF before patch!"

# Locate showTaskForNowPopupAfterSave
idx_fn = text.find('    function showTaskForNowPopupAfterSave(plan) {')
assert idx_fn != -1, "showTaskForNowPopupAfterSave not found!"

idx_next = text.find('    function startBreakTaskFlow(firstTaskId) {')
assert idx_next != -1, "startBreakTaskFlow not found!"

new_post_save_code = """    let lastPostSavePlan = null;

    function showTaskForNowPopupAfterSave(plan) {
        if (plan) lastPostSavePlan = plan;
        const confirmed = plan || lastPostSavePlan || getActiveWorkingPlan();
        const tasks = getAllPlanTasks(confirmed);
        const topTask = tasks.find(t => !t.completed) || tasks[0];

        if (!topTask) {
            closeModal('dashboard');
            return;
        }

        activeModalView = 'post_save_task_now';
        const durStr = (topTask.durationMinutes === 90) ? (isViLocale() ? '1,5 giờ' : '1.5 hr') : (topTask.durationMinutes ? formatDuration(topTask.durationMinutes) : (topTask.durationLabel || '30 min'));
        
        let deadlineDisplay = '';
        if (topTask.hasDeadline && topTask.deadlineDate) {
            const formattedDate = formatStep2DisplayDate(topTask.deadlineDate);
            deadlineDisplay = `${isViLocale() ? 'Deadline:' : 'Due:'} ${formattedDate}`;
        } else {
            deadlineDisplay = window.t ? window.t('workspace.dueNoFixedDeadline', {}, (isViLocale() ? 'Deadline: Chưa có deadline' : 'Due: No fixed deadline')) : (isViLocale() ? 'Deadline: Chưa có deadline' : 'Due: No fixed deadline');
        }

        const subtasks = Array.isArray(topTask.subtasks) ? topTask.subtasks : [];

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${window.t ? window.t('workspace.planConfirmedAndSavedUpper', {}, 'PLAN CONFIRMED & SAVED') : (isViLocale() ? 'PLAN ĐÃ ĐƯỢC XÁC NHẬN & LƯU' : 'PLAN CONFIRMED & SAVED')}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${window.t ? window.t('workspace.yourTaskForNow', {}, 'Your task for now') : (isViLocale() ? 'Task tiếp theo của bạn' : 'Your task for now')}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        aria-label="${window.t ? window.t('common.close', {}, 'Close dialog') : (isViLocale() ? 'Đóng' : 'Close dialog')}"
                        title="${window.t ? window.t('common.close', {}, 'Close dialog') : (isViLocale() ? 'Đóng' : 'Close dialog')}"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Task Highlight Card -->
            <div class="p-4 rounded-2xl border-2 border-[#D79277] bg-[#FFF9F5] space-y-2">
                <div class="flex items-center justify-between">
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#D79277] text-white">
                        ${window.t ? window.t('workspace.doThisFirstPriority', {}, (isViLocale() ? 'ƯU TIÊN LÀM TRƯỚC' : 'DO THIS FIRST')) : (isViLocale() ? 'ƯU TIÊN LÀM TRƯỚC' : 'DO THIS FIRST')}
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
                        <div class="text-[11px] font-bold uppercase tracking-wider text-stone-500">
                            ${subtasks.length} ${isViLocale() ? 'subtask' : (subtasks.length === 1 ? 'action step' : 'action steps')}:
                        </div>
                        ${subtasks.map((s, idx) => `
                            <div class="flex items-center space-x-2 text-xs text-stone-700">
                                <span>${s.completed ? '✓' : '○'}</span>
                                <span class="${s.completed ? 'line-through text-stone-400' : ''}">${escapeHTML(s.title || s.name)}</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>

            <!-- Question: Break down this task? -->
            <div class="py-2 space-y-1 text-center sm:text-left">
                <h4 class="font-bold text-sm sm:text-base text-stone-800">
                    ${window.t ? window.t('workspace.breakDownQuestion', {}, 'Would you like to break down this task into smaller steps?') : (isViLocale() ? 'Bạn có muốn chia nhỏ task này thành các bước dễ thực hiện hơn không?' : 'Would you like to break down this task into smaller steps?')}
                </h4>
                <p class="text-xs text-stone-500">
                    ${window.t ? window.t('workspace.breakDownDesc', {}, 'Breaking big tasks into 10–15 min steps prevents freeze and makes starting effortless.') : (isViLocale() ? 'Chia task lớn thành những bước nhỏ từ 10–15 phút giúp bạn dễ bắt đầu hơn và tránh cảm giác quá tải.' : 'Breaking big tasks into 10–15 min steps prevents freeze and makes starting effortless.')}
                </p>
            </div>

            <!-- Action Buttons -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.showStartWorkingPopup()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                    ${window.t ? window.t('workspace.noStartWorking', {}, (isViLocale() ? 'Không, bắt đầu làm' : 'No, start working')) : (isViLocale() ? 'Không, bắt đầu làm' : 'No, start working')}
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.startBreakTaskFlow('${topTask.id}')"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                    <span>${window.t ? window.t('workspace.breakDownTaskBtn', {}, (isViLocale() ? 'Chia nhỏ task →' : 'Break down task →')) : (isViLocale() ? 'Chia nhỏ task →' : 'Break down task →')}</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }\n\n"""

text = text[:idx_fn] + new_post_save_code + text[idx_next:]

# Update onLanguageChange to re-render post_save_task_now
old_listener = """            } else if (activeModalView === 'adjust_propose') {
                renderAdjustmentStep3Proposal();
            }
        });"""

new_listener = """            } else if (activeModalView === 'adjust_propose') {
                renderAdjustmentStep3Proposal();
            } else if (activeModalView === 'post_save_task_now') {
                showTaskForNowPopupAfterSave(lastPostSavePlan);
            }
        });"""

assert old_listener in text, "old_listener not found!"
text = text.replace(old_listener, new_listener, 1)

assert '\r\n' not in text, "urmodeFlow.js has CRLF after patch!"

with open('urmodeFlow.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print("urmodeFlow.js updated successfully with Plan Confirmed & Saved modal localization! (LF only)")
