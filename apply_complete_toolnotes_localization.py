import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('toolNotes.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

assert '\r\n' not in content, "CRLF found in toolNotes.js before update!"

# 1. Update t() function signature
t_target = """    function t(path, fallback = '') {
        if (window.TempoI18n && typeof window.TempoI18n.t === 'function') {
            return window.TempoI18n.t(path, {}, fallback);
        }
        if (typeof window.t === 'function') {
            return window.t(path, {}, fallback);
        }
        return fallback;
    }"""

t_replacement = """    function t(path, params = {}, fallback = '') {
        if (typeof params === 'string') {
            fallback = params;
            params = {};
        }
        if (window.TempoI18n && typeof window.TempoI18n.t === 'function') {
            return window.TempoI18n.t(path, params, fallback);
        }
        if (typeof window.t === 'function') {
            return window.t(path, params, fallback);
        }
        return fallback;
    }"""

assert t_target in content, "t_target not found!"
content = content.replace(t_target, t_replacement, 1)

# 2. Update setCreationType placeholder logic
set_type_target = """        if (textarea) {
            textarea.placeholder = currentCreationType === 'day'
                ? 'Write reflections, reminders, or general observations for the day...'
                : 'Write notes, research links, outlines, or next action steps for this task...';
        }"""

set_type_replacement = """        if (textarea) {
            textarea.placeholder = currentCreationType === 'day'
                ? t('toolNotes.pageContentPlaceholderDay', isViLocale() ? 'Ghi lại suy nghĩ, lời nhắc hoặc những điều bạn muốn lưu giữ trong ngày...' : 'Write reflections, reminders, or general observations for the day...')
                : t('toolNotes.contentPlaceholderTask', isViLocale() ? 'Viết ghi chú, dàn ý hoặc các bước hành động tiếp theo cho task này...' : 'Write research notes, outlines, or next action steps for this task...');
        }"""

assert set_type_target in content, "set_type_target not found!"
content = content.replace(set_type_target, set_type_replacement, 1)

# 3. Update handleCreateFormSubmit feedback messages
form_submit_target = """        if (!content) {
            if (feedback) {
                feedback.innerHTML = `<span class="text-rose-600 font-bold">⚠️ Please enter some note content before saving.</span>`;
            }
            if (textarea) textarea.focus();
            return;
        }"""

form_submit_replacement = """        if (!content) {
            if (feedback) {
                feedback.innerHTML = `<span class="text-rose-600 font-bold">⚠️ ${escapeHTML(t('toolNotes.validationContentMissing', isViLocale() ? 'Vui lòng nhập nội dung ghi chú.' : 'Please enter note content.'))}</span>`;
            }
            if (textarea) textarea.focus();
            return;
        }"""

assert form_submit_target in content, "form_submit_target not found!"
content = content.replace(form_submit_target, form_submit_replacement, 1)

date_submit_target = """            if (!dateVal) {
                if (feedback) {
                    feedback.innerHTML = `<span class="text-rose-600 font-bold">⚠️ Please select a valid date.</span>`;
                }
                return;
            }"""

date_submit_replacement = """            if (!dateVal) {
                if (feedback) {
                    feedback.innerHTML = `<span class="text-rose-600 font-bold">⚠️ ${escapeHTML(t('toolNotes.validationDateMissing', isViLocale() ? 'Vui lòng chọn ngày hợp lệ.' : 'Please select a date.'))}</span>`;
                }
                return;
            }"""

assert date_submit_target in content, "date_submit_target not found!"
content = content.replace(date_submit_target, date_submit_replacement, 1)

task_submit_target = """            if (!taskId) {
                if (feedback) {
                    feedback.innerHTML = `<span class="text-rose-600 font-bold">⚠️ Please select an associated task.</span>`;
                }
                return;
            }"""

task_submit_replacement = """            if (!taskId) {
                if (feedback) {
                    feedback.innerHTML = `<span class="text-rose-600 font-bold">⚠️ ${escapeHTML(t('toolNotes.validationTaskMissing', isViLocale() ? 'Vui lòng chọn một công việc.' : 'Please select an associated task.'))}</span>`;
                }
                return;
            }"""

assert task_submit_target in content, "task_submit_target not found!"
content = content.replace(task_submit_target, task_submit_replacement, 1)

# 4. Update openNoteDetailModal labels
detail_modal_target = """                    <!-- Complete Note Content (Untruncated) -->
                    <div class="space-y-2">
                        <span class="text-xs font-bold uppercase tracking-wider text-[#8C827A]">Full Content</span>"""

detail_modal_replacement = """                    <!-- Complete Note Content (Untruncated) -->
                    <div class="space-y-2">
                        <span class="text-xs font-bold uppercase tracking-wider text-[#8C827A]">${escapeHTML(t('toolNotes.fullContent', isViLocale() ? 'Nội dung đầy đủ' : 'Full Content'))}</span>"""

assert detail_modal_target in content, "detail_modal_target not found!"
content = content.replace(detail_modal_target, detail_modal_replacement, 1)

detail_modal_btn_target = """                        <button type="button"
                                onclick="window.TempoToolNotes.confirmDeleteNote('${escapeHTML(String(note.id))}')"
                                class="px-4 py-2 rounded-xl text-xs font-bold text-rose-600 hover:text-white hover:bg-rose-600 border border-rose-200 hover:border-rose-600 transition cursor-pointer inline-flex items-center gap-1.5">
                            <span>🗑️ Delete</span>
                        </button>
                        <div class="flex items-center space-x-2">
                            <button type="button"
                                    onclick="window.TempoToolNotes.closeModal()"
                                    class="px-4 py-2 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] hover:bg-stone-100 transition cursor-pointer">
                                Close
                            </button>"""

detail_modal_btn_replacement = """                        <button type="button"
                                onclick="window.TempoToolNotes.confirmDeleteNote('${escapeHTML(String(note.id))}')"
                                class="px-4 py-2 rounded-xl text-xs font-bold text-rose-600 hover:text-white hover:bg-rose-600 border border-rose-200 hover:border-rose-600 transition cursor-pointer inline-flex items-center gap-1.5">
                            <span>🗑️ ${escapeHTML(t('toolNotes.delete', isViLocale() ? 'Xóa' : 'Delete'))}</span>
                        </button>
                        <div class="flex items-center space-x-2">
                            <button type="button"
                                    onclick="window.TempoToolNotes.closeModal()"
                                    class="px-4 py-2 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] hover:bg-stone-100 transition cursor-pointer">
                                ${escapeHTML(t('toolNotes.close', isViLocale() ? 'Đóng' : 'Close'))}
                            </button>"""

assert detail_modal_btn_target in content, "detail_modal_btn_target not found!"
content = content.replace(detail_modal_btn_target, detail_modal_btn_replacement, 1)

# 5. Replace section 8: renderDayNotesListHTML, renderTaskNotesListHTML, renderToolNotesPage
renderer_start_marker = "    // =========================================================================\n    // 8. TOOL NOTES PAGE RENDERER (Full Workspace)\n    // ========================================================================="
renderer_end_marker = "    // Escape key listener for closing modals\n    if (typeof window !== 'undefined') {"

start_pos = content.find(renderer_start_marker)
end_pos = content.find(renderer_end_marker)
assert start_pos != -1, "renderer_start_marker not found!"
assert end_pos != -1, "renderer_end_marker not found!"

new_renderer_section = """    // =========================================================================
    // 8. TOOL NOTES PAGE RENDERER (Full Workspace)
    // =========================================================================

    function renderDayNotesListHTML(dayNotes) {
        if (!dayNotes || dayNotes.length === 0) {
            return `
                <div class="py-12 px-4 text-center space-y-3 bg-[#FAF7F4] border border-dashed border-stone-200 rounded-2xl" data-tempo-ui="day-notes-empty">
                    <div class="w-10 h-10 mx-auto rounded-xl bg-[#F9E8E2] text-[#B87561] flex items-center justify-center text-lg shadow-2xs">📝</div>
                    <div class="space-y-1">
                        <h4 class="font-heading text-sm font-bold text-[#202124]">${escapeHTML(t('toolNotes.emptyDayNotesTitle', isViLocale() ? 'Chưa có ghi chú theo ngày nào.' : 'No day notes yet.'))}</h4>
                        <p class="text-xs text-[#6F6B68] max-w-xs mx-auto">${escapeHTML(t('toolNotes.emptyDayNotesDesc', isViLocale() ? 'Ghi lại suy nghĩ, mức năng lượng hoặc những cảm nhận của bạn mỗi ngày.' : 'Track thoughts, energy levels, or gentle reflections for any day.'))}</p>
                    </div>
                    <button type="button" 
                            onclick="window.TempoToolNotes.setCreationType('day'); const ta = document.getElementById('textarea-note-content'); if (ta) { ta.scrollIntoView({ behavior: 'smooth', block: 'center' }); ta.focus(); }" 
                            class="px-3.5 py-1.5 rounded-xl font-bold text-xs bg-[#C88E7D] hover:bg-[#B97F6E] text-white shadow-2xs transition cursor-pointer">
                        ${escapeHTML(t('toolNotes.addDayNoteBtn', isViLocale() ? '+ Thêm note theo ngày' : '+ Add a Day Note'))}
                    </button>
                </div>
            `;
        }

        // Group notes by date
        const groups = {};
        dayNotes.forEach(n => {
            const d = n.date || (n.createdAt ? getLocalDateStr(n.createdAt) : 'Other');
            if (!groups[d]) groups[d] = [];
            groups[d].push(n);
        });

        const sortedDates = Object.keys(groups).sort((a, b) => b.localeCompare(a));
        const dayBadge = t('toolNotes.tabDayNote', isViLocale() ? 'Note theo ngày' : 'Day Note');
        const viewDetailsText = t('toolNotes.viewDetails', isViLocale() ? 'Xem chi tiết →' : 'View details →');
        const clickToExpandText = t('toolNotes.clickToExpand', isViLocale() ? 'Nhấn để mở rộng' : 'Click to expand');

        return sortedDates.map(dateKey => {
            const dateNotes = groups[dateKey];
            const headerLabel = formatDisplayDate(dateKey);

            return `
                <div class="space-y-2" data-date-group="${escapeHTML(dateKey)}">
                    <!-- Date Header -->
                    <div class="flex items-center space-x-2 text-xs font-bold text-[#554741] sticky top-0 bg-white/95 backdrop-blur-2xs py-1 z-10 border-b border-stone-100">
                        <span class="text-[#B87561]">📅</span>
                        <span>${escapeHTML(headerLabel)}</span>
                        <span class="text-[10px] text-[#8C827A] font-medium">(${dateNotes.length})</span>
                    </div>

                    <!-- Cards in this group -->
                    <div class="space-y-2">
                        ${dateNotes.map(n => {
                            const timeStr = formatNoteTime(n);
                            const textPreview = escapeHTML(n.text || n.content || '');
                            const safeId = escapeHTML(String(n.id));

                            return `
                                <div onclick="window.TempoToolNotes.openNoteDetailModal('${safeId}')"
                                     class="bg-[#FEFAF8] hover:bg-white border border-[#EBDCD3] hover:border-[#C88E7D] rounded-2xl p-3.5 space-y-2 shadow-2xs hover:shadow-xs transition cursor-pointer group"
                                     data-day-note-id="${safeId}"
                                     title="${escapeHTML(clickToExpandText)}">
                                    <div class="flex items-center justify-between gap-2">
                                        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#F9E8E2] text-[#B87561] shrink-0 uppercase tracking-wider">
                                            ${escapeHTML(dayBadge)}
                                        </span>
                                        ${timeStr ? `<span class="text-[11px] text-[#8C827A] font-medium">${escapeHTML(timeStr)}</span>` : ''}
                                    </div>
                                    ${n.title ? `<h5 class="text-xs sm:text-sm font-bold text-[#202124] leading-snug break-words">${escapeHTML(n.title)}</h5>` : ''}
                                    <p class="text-xs sm:text-[13px] text-[#4A4540] font-medium leading-relaxed line-clamp-2 break-words group-hover:text-[#202124] transition-colors">
                                        ${textPreview}
                                    </p>
                                    <div class="flex items-center justify-between pt-1 text-[11px] text-[#8C827A] border-t border-stone-100/70">
                                        <span class="group-hover:text-[#C88E7D] transition-colors font-medium">${escapeHTML(viewDetailsText)}</span>
                                        <span class="text-[10px] text-stone-400">${escapeHTML(clickToExpandText)}</span>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderTaskNotesListHTML(taskNotes) {
        if (!taskNotes || taskNotes.length === 0) {
            return `
                <div class="py-12 px-4 text-center space-y-3 bg-[#FAF7F4] border border-dashed border-stone-200 rounded-2xl" data-tempo-ui="task-notes-empty">
                    <div class="w-10 h-10 mx-auto rounded-xl bg-[#FEF3C7] text-[#92400E] flex items-center justify-center text-lg shadow-2xs">📋</div>
                    <div class="space-y-1">
                        <h4 class="font-heading text-sm font-bold text-[#202124]">${escapeHTML(t('toolNotes.emptyTaskNotesTitle', isViLocale() ? 'Chưa có ghi chú công việc nào.' : 'No task notes yet.'))}</h4>
                        <p class="text-xs text-[#6F6B68] max-w-xs mx-auto">${escapeHTML(t('toolNotes.emptyTaskNotesDesc', isViLocale() ? 'Liên kết ghi chú nghiên cứu, công thức hoặc các bước thực hiện với kế hoạch làm việc.' : 'Attach specific research notes, formulas, or steps to your working plan tasks.'))}</p>
                    </div>
                    <button type="button" 
                            onclick="window.TempoToolNotes.setCreationType('task'); const ta = document.getElementById('textarea-note-content'); if (ta) { ta.scrollIntoView({ behavior: 'smooth', block: 'center' }); ta.focus(); }" 
                            class="px-3.5 py-1.5 rounded-xl font-bold text-xs bg-[#C88E7D] hover:bg-[#B97F6E] text-white shadow-2xs transition cursor-pointer">
                        ${escapeHTML(t('toolNotes.addTaskNoteBtn', isViLocale() ? '+ Thêm note theo task' : '+ Add a Task Note'))}
                    </button>
                </div>
            `;
        }

        const taskBadge = t('toolNotes.badgeTaskNote', isViLocale() ? 'NOTE THEO TASK' : 'TASK NOTE');
        const viewDetailsText = t('toolNotes.viewDetails', isViLocale() ? 'Xem chi tiết →' : 'View details →');
        const clickToExpandText = t('toolNotes.clickToExpand', isViLocale() ? 'Nhấn để mở rộng' : 'Click to expand');

        return taskNotes.map(n => {
            const timeStr = formatNoteTime(n);
            const textPreview = escapeHTML(n.text || n.content || '');
            const safeId = escapeHTML(String(n.id));
            const rawTaskName = n.taskName || (isViLocale() ? 'Công việc Học tập' : 'Study Task');
            const taskTitle = escapeHTML(rawTaskName);

            // Determine card title:
            // If user supplied a custom title, display it as-is.
            // If default or empty or starting with 'Note for ' or 'Note cho ', localize dynamically to Note cho {taskName} / Note for {taskName}.
            let displayTitle = '';
            if (n.title && !n.title.startsWith('Note for ') && !n.title.startsWith('Note cho ')) {
                displayTitle = n.title;
            } else {
                displayTitle = t('toolNotes.noteForTask', { taskName: rawTaskName }, isViLocale() ? (`Note cho ${rawTaskName}`) : (`Note for ${rawTaskName}`));
            }

            return `
                <div onclick="window.TempoToolNotes.openNoteDetailModal('${safeId}')"
                     class="bg-[#FEFAF8] hover:bg-white border border-[#EBDCD3] hover:border-[#C88E7D] rounded-2xl p-3.5 space-y-2 shadow-2xs hover:shadow-xs transition cursor-pointer group"
                     data-task-note-id="${safeId}"
                     title="${escapeHTML(clickToExpandText)}">
                    <div class="flex items-center justify-between gap-2">
                        <div class="flex items-center space-x-1.5 min-w-0">
                            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FEF3C7] text-[#92400E] shrink-0 uppercase tracking-wider">
                                ${escapeHTML(taskBadge)}
                            </span>
                            <span class="text-xs font-bold text-[#202124] truncate flex items-center gap-1">
                                <span>📌</span>
                                <span class="truncate">${taskTitle}</span>
                            </span>
                        </div>
                        ${timeStr ? `<span class="text-[11px] text-[#8C827A] font-medium shrink-0">${escapeHTML(timeStr)}</span>` : ''}
                    </div>
                    ${displayTitle ? `<h5 class="text-xs sm:text-sm font-bold text-[#202124] leading-snug break-words">${escapeHTML(displayTitle)}</h5>` : ''}
                    <p class="text-xs sm:text-[13px] text-[#4A4540] font-medium leading-relaxed line-clamp-2 break-words group-hover:text-[#202124] transition-colors">
                        ${textPreview}
                    </p>
                    <div class="flex items-center justify-between pt-1 text-[11px] text-[#8C827A] border-t border-stone-100/70">
                        <span class="group-hover:text-[#C88E7D] transition-colors font-medium">${escapeHTML(viewDetailsText)}</span>
                        <span class="text-[10px] text-stone-400">${escapeHTML(clickToExpandText)}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderToolNotesPage() {
        const root = document.getElementById('tool-notes-root');
        if (!root) return;

        // Preserve in-progress form inputs if user was typing when language switched
        const existingTitleInput = document.getElementById('input-note-title');
        const draftTitle = existingTitleInput ? existingTitleInput.value : '';
        const existingTextarea = document.getElementById('textarea-note-content');
        const draftContent = existingTextarea ? existingTextarea.value : '';
        const existingDateInput = document.getElementById('input-note-date');
        const draftDate = existingDateInput && existingDateInput.value ? existingDateInput.value : '';
        const existingTaskSelect = document.getElementById('select-note-task');
        const draftTaskId = existingTaskSelect ? existingTaskSelect.value : '';

        const notes = loadNotes();
        const dayNotes = notes.filter(n => !(n.taskId || n.category === 'task' || n.type === 'task'));
        const taskNotes = notes.filter(n => !!(n.taskId || n.category === 'task' || n.type === 'task'));
        const availableTasks = getAvailableTasks();
        const todayStr = getTodayLocalDateStr();

        const backToDashText = t('toolNotes.backToDashboard', isViLocale() ? '← Trở về Dashboard' : '← Back to Dashboard');
        const pageTitleText = t('toolNotes.pageTitle', isViLocale() ? 'Notes Tools' : 'Notes Tool');
        const pageSubtitleText = t('toolNotes.pageSubtitle', isViLocale() ? 'Không gian riêng để lưu giữ những suy nghĩ hằng ngày và ghi chú cho các task học tập của bạn.' : 'A calm, dedicated space to keep your daily reflections and academic task notes organized.');
        const sectionCreateText = t('toolNotes.sectionCreateNotes', isViLocale() ? 'Tạo ghi chú' : 'Create Notes');
        const tabDayText = t('toolNotes.tabDayNote', isViLocale() ? 'Note theo ngày' : 'Day Note');
        const tabTaskText = t('toolNotes.tabTaskNote', isViLocale() ? 'Note theo task' : 'Task Note');
        const titleLabelText = t('toolNotes.noteTitleLabel', isViLocale() ? 'Tiêu đề (không bắt buộc)' : 'Note Title (optional)');
        const titlePlaceholderText = t('toolNotes.noteTitlePlaceholder', isViLocale() ? 'VD: Suy nghĩ hôm nay, Tóm tắt bài giảng...' : 'e.g. Daily reflection, Lecture summary...');
        const dateLabelText = t('toolNotes.calendarDateLabel', isViLocale() ? 'Ngày ghi chú' : 'Calendar Date');
        const dateHelperText = t('toolNotes.pageDateHelper', isViLocale() ? 'Ngày mặc định là hôm nay. Bạn có thể chọn ngày khác nếu cần.' : "Defaults to today's local date. You can select another date if needed.");
        const taskLabelText = t('toolNotes.associatedTaskLabel', isViLocale() ? 'Công việc Học tập liên kết' : 'Associated Study Task');
        const selectTaskPlaceholder = t('toolNotes.selectTaskPlaceholder', isViLocale() ? '-- Chọn một task từ kế hoạch --' : '-- Select a task from your plan --');
        const noActiveTasksText = t('toolNotes.noActiveTasks', isViLocale() ? 'Chưa có task nào trong kế hoạch' : 'No active tasks in your plan');
        const contentLabelText = t('toolNotes.noteContentLabel', isViLocale() ? 'Nội dung ghi chú' : 'Note Content');
        const contentPlaceholderText = currentCreationType === 'day'
            ? t('toolNotes.pageContentPlaceholderDay', isViLocale() ? 'Ghi lại suy nghĩ, lời nhắc hoặc những điều bạn muốn lưu giữ trong ngày...' : 'Write reflections, reminders, or general observations for the day...')
            : t('toolNotes.contentPlaceholderTask', isViLocale() ? 'Viết ghi chú, dàn ý hoặc các bước hành động tiếp theo cho task này...' : 'Write research notes, outlines, or next action steps for this task...');
        const cancelBtnText = t('toolNotes.cancelAction', isViLocale() ? 'Hủy' : 'Cancel');
        const saveBtnText = t('toolNotes.saveNoteAction', isViLocale() ? 'Lưu ghi chú' : 'Save Note');
        const headingDayText = t('toolNotes.headingDayNotes', isViLocale() ? 'Note theo ngày' : 'Day Notes');
        const groupedByDateText = t('toolNotes.groupedByDate', isViLocale() ? 'Nhóm theo ngày' : 'Grouped by date');
        const headingTaskText = t('toolNotes.headingTaskNotes', isViLocale() ? 'Note theo task' : 'Task Notes');
        const attachedToTasksText = t('toolNotes.attachedToTasks', isViLocale() ? 'Được liên kết với task' : 'Attached to tasks');

        root.innerHTML = `
            <!-- Navigation Return Bar -->
            <div class="flex items-center justify-between pb-3">
                <button type="button" 
                        id="btn-tool-notes-back" 
                        onclick="if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') window.TempoApp.navigateTo('today'); else window.location.hash = '#today';"
                        class="inline-flex items-center space-x-1.5 text-xs sm:text-sm font-semibold text-[#6F6B68] hover:text-[#202124] transition cursor-pointer">
                    <span>${escapeHTML(backToDashText)}</span>
                </button>
            </div>

            <!-- Page Title -->
            <div class="space-y-1 pb-4">
                <div class="flex items-center space-x-2">
                    <span class="text-2xl sm:text-3xl">📝</span>
                    <h1 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">${escapeHTML(pageTitleText)}</h1>
                </div>
                <p class="text-xs sm:text-sm text-[#6F6B68]">
                    ${escapeHTML(pageSubtitleText)}
                </p>
            </div>

            <!-- 1. Dedicated Note Creation Section -->
            <div class="bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:p-6 shadow-xs space-y-4 mb-6" data-tempo-ui="tool-notes-create-section">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-stone-100">
                    <div class="flex items-center space-x-2">
                        <span class="text-lg">✏️</span>
                        <h2 class="font-heading text-base sm:text-lg font-bold text-[#202124]">${escapeHTML(sectionCreateText)}</h2>
                    </div>
                    <!-- Type Selector Pills -->
                    <div class="inline-flex p-1 bg-[#FAF7F4] border border-[#EAE4DF] rounded-2xl space-x-1" role="tablist">
                        <button type="button" 
                                id="pill-type-day"
                                onclick="window.TempoToolNotes.setCreationType('day')"
                                class="px-4 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${currentCreationType === 'day' ? 'bg-[#C88E7D] text-white shadow-2xs' : 'text-[#6F6B68] hover:text-[#202124]'}">
                            📝 ${escapeHTML(tabDayText)}
                        </button>
                        <button type="button" 
                                id="pill-type-task"
                                onclick="window.TempoToolNotes.setCreationType('task')"
                                class="px-4 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${currentCreationType === 'task' ? 'bg-[#C88E7D] text-white shadow-2xs' : 'text-[#6F6B68] hover:text-[#202124]'}">
                            📋 ${escapeHTML(tabTaskText)}
                        </button>
                    </div>
                </div>

                <!-- Form -->
                <form id="tool-notes-create-form" onsubmit="event.preventDefault(); window.TempoToolNotes.handleCreateFormSubmit();" class="space-y-4">
                    <!-- Note Title Field -->
                    <div class="space-y-1.5">
                        <label for="input-note-title" class="block text-xs font-bold text-[#554741]">
                            ${escapeHTML(titleLabelText)}
                        </label>
                        <input type="text" 
                               id="input-note-title" 
                               placeholder="${escapeHTML(titlePlaceholderText)}"
                               class="w-full max-w-md px-3.5 py-2 text-xs sm:text-sm rounded-xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white transition" />
                    </div>

                    <!-- Day Note Date Field -->
                    <div id="form-group-day-date" class="${currentCreationType === 'day' ? 'block' : 'hidden'} space-y-1.5">
                        <label for="input-note-date" class="block text-xs font-bold text-[#554741]">
                            ${escapeHTML(dateLabelText)}
                        </label>
                        <div class="flex items-center gap-2 max-w-xs">
                            <input type="date" 
                                   id="input-note-date" 
                                   value="${escapeHTML(draftDate || todayStr)}"
                                   class="w-full px-3.5 py-2 text-xs sm:text-sm rounded-xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white transition" />
                        </div>
                        <p class="text-[11px] text-[#8C827A]">${escapeHTML(dateHelperText)}</p>
                    </div>

                    <!-- Task Note Selector Field -->
                    <div id="form-group-task-select" class="${currentCreationType === 'task' ? 'block' : 'hidden'} space-y-1.5">
                        <label for="select-note-task" class="block text-xs font-bold text-[#554741]">
                            ${escapeHTML(taskLabelText)}
                        </label>
                        <select id="select-note-task" 
                                class="w-full max-w-md px-3.5 py-2 text-xs sm:text-sm rounded-xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white transition">
                            <option value="" disabled ${!draftTaskId ? 'selected' : ''}>${escapeHTML(selectTaskPlaceholder)}</option>
                            ${availableTasks.length === 0 ? `
                                <option value="" disabled>${escapeHTML(noActiveTasksText)}</option>
                            ` : availableTasks.map(tItem => `
                                <option value="${escapeHTML(tItem.id)}" ${tItem.id === draftTaskId ? 'selected' : ''}>${escapeHTML(tItem.name)}${tItem.deadlineDate ? ` (Due ${tItem.deadlineDate})` : ''}</option>
                            `).join('')}
                        </select>
                        <p class="text-[11px] text-[#8C827A]">${escapeHTML(t('toolNotes.associatedTaskHelper', isViLocale() ? 'Được điền từ kế hoạch làm việc và các công việc hiện tại của bạn.' : 'Populated from your working plan and current tasks.'))}</p>
                    </div>

                    <!-- Note Textarea -->
                    <div class="space-y-1.5">
                        <label for="textarea-note-content" class="block text-xs font-bold text-[#554741]">
                            ${escapeHTML(contentLabelText)}
                        </label>
                        <textarea id="textarea-note-content" 
                                  rows="3" 
                                  placeholder="${escapeHTML(contentPlaceholderText)}"
                                  class="w-full p-3.5 text-xs sm:text-sm rounded-2xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white resize-y min-h-[90px] transition placeholder:text-stone-400"></textarea>
                    </div>

                    <!-- Feedback & Actions -->
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
                        <div id="create-note-feedback" class="text-xs font-medium text-stone-500 min-h-[20px]"></div>
                        <div class="flex items-center space-x-2.5 self-end sm:self-auto">
                            <button type="button" 
                                    onclick="window.TempoToolNotes.resetCreateForm()"
                                    class="px-4 py-2 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] hover:bg-[#FAF7F4] transition cursor-pointer">
                                ${escapeHTML(cancelBtnText)}
                            </button>
                            <button type="submit" 
                                    id="btn-save-note-submit"
                                    class="px-5 py-2 rounded-xl font-bold text-xs bg-[#C88E7D] hover:bg-[#B97F6E] text-white shadow-2xs transition cursor-pointer inline-flex items-center gap-1.5">
                                <span>${escapeHTML(saveBtnText)}</span>
                            </button>
                        </div>
                    </div>
                </form>
            </div>

            <!-- 2. Two-Column Notes Display -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start" data-tempo-ui="tool-notes-two-columns">
                <!-- LEFT PANEL: Day Notes -->
                <div class="bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:p-6 shadow-xs space-y-4" data-tempo-ui="tool-notes-day-panel">
                    <div class="flex items-center justify-between pb-2 border-b border-stone-100">
                        <div class="flex items-center space-x-2">
                            <span class="text-lg">📝</span>
                            <h3 class="font-heading text-base sm:text-lg font-bold text-[#202124]">
                                ${escapeHTML(headingDayText)}
                            </h3>
                            <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-[#F9E8E2] text-[#B87561]" id="day-notes-count-badge">
                                ${dayNotes.length}
                            </span>
                        </div>
                        <span class="text-xs text-[#8C827A]">${escapeHTML(groupedByDateText)}</span>
                    </div>

                    <!-- Scrollable List of Day Notes -->
                    <div class="overflow-y-auto max-h-[580px] space-y-4 pr-1.5 custom-scrollbar" data-tempo-ui="day-notes-scroll-container">
                        ${renderDayNotesListHTML(dayNotes)}
                    </div>
                </div>

                <!-- RIGHT PANEL: Task Notes -->
                <div class="bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:p-6 shadow-xs space-y-4" data-tempo-ui="tool-notes-task-panel">
                    <div class="flex items-center justify-between pb-2 border-b border-stone-100">
                        <div class="flex items-center space-x-2">
                            <span class="text-lg">📋</span>
                            <h3 class="font-heading text-base sm:text-lg font-bold text-[#202124]">
                                ${escapeHTML(headingTaskText)}
                            </h3>
                            <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-[#FEF3C7] text-[#92400E]" id="task-notes-count-badge">
                                ${taskNotes.length}
                            </span>
                        </div>
                        <span class="text-xs text-[#8C827A]">${escapeHTML(attachedToTasksText)}</span>
                    </div>

                    <!-- Scrollable List of Task Notes -->
                    <div class="overflow-y-auto max-h-[580px] space-y-3 pr-1.5 custom-scrollbar" data-tempo-ui="task-notes-scroll-container">
                        ${renderTaskNotesListHTML(taskNotes)}
                    </div>
                </div>
            </div>
        `;

        // Restore drafts
        if (draftTitle) {
            const tEl = document.getElementById('input-note-title');
            if (tEl) tEl.value = draftTitle;
        }
        if (draftContent) {
            const cEl = document.getElementById('textarea-note-content');
            if (cEl) cEl.value = draftContent;
        }
    }
\n"""

content = content[:start_pos] + new_renderer_section + content[end_pos:]

assert '\r' not in content, "CRLF found in toolNotes.js after update!"

with open('toolNotes.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print(f"Updated toolNotes.js successfully! Total LF lines: {content.count(chr(10))}")
