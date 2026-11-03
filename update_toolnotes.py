import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('toolNotes.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

assert '\r\n' not in content, "CRLF found in toolNotes.js before update!"

# 1. Add t() helper and activeModalCleanup
helper_target = """    if (typeof window !== 'undefined' && typeof window.isViLocale !== 'function') {
        window.isViLocale = isViLocale;
    }

    // State for Note Creation Form on Tool Notes Page
    let currentCreationType = 'day'; // 'day' | 'task'
    let isSavingNote = false;

    // Active modal state
    let activeModalNoteId = null;"""

helper_replacement = """    if (typeof window !== 'undefined' && typeof window.isViLocale !== 'function') {
        window.isViLocale = isViLocale;
    }

    function t(path, fallback = '') {
        if (window.TempoI18n && typeof window.TempoI18n.t === 'function') {
            return window.TempoI18n.t(path, {}, fallback);
        }
        if (typeof window.t === 'function') {
            return window.t(path, {}, fallback);
        }
        return fallback;
    }

    // State for Note Creation Form on Tool Notes Page
    let currentCreationType = 'day'; // 'day' | 'task'
    let isSavingNote = false;

    // Active modal state
    let activeModalNoteId = null;
    let activeModalCleanup = null;"""

assert helper_target in content, "helper_target not found in toolNotes.js!"
content = content.replace(helper_target, helper_replacement, 1)

# 2. Update closeModal() to call activeModalCleanup
close_target = """    function closeModal() {
        const root = document.getElementById('tool-notes-modal-root');
        if (root) root.innerHTML = '';
        activeModalNoteId = null;
    }"""

close_replacement = """    function closeModal() {
        if (typeof activeModalCleanup === 'function') {
            try { activeModalCleanup(); } catch (e) {}
            activeModalCleanup = null;
        }
        const root = document.getElementById('tool-notes-modal-root');
        if (root) root.innerHTML = '';
        activeModalNoteId = null;
    }"""

assert close_target in content, "close_target not found in toolNotes.js!"
content = content.replace(close_target, close_replacement, 1)

# 3. Replace openCreateNoteModal
start_str = "    function openCreateNoteModal(defaultType = 'day', defaultDate = null) {"
end_str = "    // =========================================================================\n    // 8. TOOL NOTES PAGE RENDERER"

start_idx = content.find(start_str)
end_idx = content.find(end_str)
assert start_idx != -1, "start_str not found!"
assert end_idx != -1, "end_str not found!"

new_open_modal = """    function openCreateNoteModal(defaultType = 'day', defaultDate = null) {
        if (typeof activeModalCleanup === 'function') {
            try { activeModalCleanup(); } catch (e) {}
            activeModalCleanup = null;
        }

        const root = getOrCreateModalRoot();
        const availableTasks = getAvailableTasks();
        const initialDate = defaultDate ? getLocalDateStr(defaultDate) : getTodayLocalDateStr();
        let selectedType = defaultType === 'task' ? 'task' : 'day';

        // State preservation across type switching and dynamic language switching
        let currentTitle = '';
        let currentContent = '';
        let currentDate = initialDate;
        let currentTaskId = '';

        function snapshotInputs() {
            const titleEl = document.getElementById('modal-input-title');
            if (titleEl) currentTitle = titleEl.value;
            const textEl = document.getElementById('modal-textarea-content');
            if (textEl) currentContent = textEl.value;
            const dateEl = document.getElementById('modal-input-date');
            if (dateEl && dateEl.value) currentDate = dateEl.value;
            const taskEl = document.getElementById('modal-select-task');
            if (taskEl && taskEl.value) currentTaskId = taskEl.value;
        }

        function renderModalBody() {
            const isDay = selectedType === 'day';
            const modalTitle = t('toolNotes.createNotesTitle', isViLocale() ? 'Tạo Notes' : 'Create Notes');
            const tabDay = t('toolNotes.tabDayNote', isViLocale() ? 'Note theo ngày' : 'Day Note');
            const tabTask = t('toolNotes.tabTaskNote', isViLocale() ? 'Note theo task' : 'Task Note');
            const titleLabel = t('toolNotes.noteTitleLabel', isViLocale() ? 'Tiêu đề (không bắt buộc)' : 'Note Title (optional)');
            const titlePlaceholder = t('toolNotes.noteTitlePlaceholder', isViLocale() ? 'VD: Suy nghĩ hôm nay, Tóm tắt bài giảng...' : 'e.g. Daily reflection, Lecture summary...');
            const dateLabel = t('toolNotes.calendarDateLabel', isViLocale() ? 'Ngày ghi chú' : 'Calendar Date');
            const dateHelper = t('toolNotes.dateHelperText', isViLocale() ? 'Ngày được tự động điền theo hôm nay. Bạn có thể thay đổi nếu muốn tạo ghi chú cho ngày khác.' : "Prefilled with today's date. You can change it if creating for another day.");
            const taskLabel = t('toolNotes.associatedTaskLabel', isViLocale() ? 'Công việc Học tập liên kết' : 'Associated Study Task');
            const selectTaskPlaceholder = t('toolNotes.selectTaskPlaceholder', isViLocale() ? '-- Chọn một task từ kế hoạch --' : '-- Select a task from your plan --');
            const noActiveTasksText = t('toolNotes.noActiveTasks', isViLocale() ? 'Chưa có task nào trong kế hoạch' : 'No active tasks in your plan');
            const contentLabel = t('toolNotes.noteContentLabel', isViLocale() ? 'Nội dung ghi chú' : 'Note Content');
            const contentPlaceholder = isDay
                ? t('toolNotes.contentPlaceholderDay', isViLocale() ? 'Viết những suy nghĩ, lời nhắc hoặc điều bạn muốn ghi lại trong ngày...' : 'Write reflections, reminders, or general observations for the day...')
                : t('toolNotes.contentPlaceholderTask', isViLocale() ? 'Viết ghi chú, dàn ý hoặc các bước hành động tiếp theo cho task này...' : 'Write research notes, outlines, or next action steps for this task...');
            const cancelText = t('toolNotes.cancelAction', isViLocale() ? 'Hủy' : 'Cancel');
            const saveText = t('toolNotes.saveNoteAction', isViLocale() ? 'Lưu ghi chú' : 'Save Note');

            root.innerHTML = `
                <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs transition-opacity" 
                     id="note-create-backdrop"
                     onclick="if (event.target === this) window.TempoToolNotes.closeModal();">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl max-w-lg w-full p-6 sm:p-7 shadow-xl space-y-4 animate-in fade-in zoom-in-95 relative" 
                         role="dialog" 
                         aria-modal="true">
                        
                        <!-- Header -->
                        <div class="flex items-center justify-between pb-3 border-b border-stone-100">
                            <div class="flex items-center space-x-2">
                                <span class="text-xl">✏️</span>
                                <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124]" id="modal-heading-title">${escapeHTML(modalTitle)}</h3>
                            </div>
                            <button type="button" 
                                    onclick="window.TempoToolNotes.closeModal()"
                                    aria-label="Close"
                                    class="text-stone-400 hover:text-stone-700 w-8 h-8 rounded-full flex items-center justify-center hover:bg-stone-100 transition cursor-pointer">
                                ✕
                            </button>
                        </div>

                        <!-- Type Selector Pills -->
                        <div class="flex items-center justify-center">
                            <div class="inline-flex p-1 bg-[#FAF7F4] border border-[#EAE4DF] rounded-2xl space-x-1">
                                <button type="button" 
                                        id="modal-pill-day"
                                        class="px-4 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${isDay ? 'bg-[#C88E7D] text-white shadow-2xs' : 'text-[#6F6B68] hover:text-[#202124]'}">
                                    📝 ${escapeHTML(tabDay)}
                                </button>
                                <button type="button" 
                                        id="modal-pill-task"
                                        class="px-4 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${!isDay ? 'bg-[#C88E7D] text-white shadow-2xs' : 'text-[#6F6B68] hover:text-[#202124]'}">
                                    📋 ${escapeHTML(tabTask)}
                                </button>
                            </div>
                        </div>

                        <!-- Form -->
                        <form id="modal-create-note-form" class="space-y-4">
                            <!-- Note Title Field -->
                            <div class="space-y-1.5">
                                <label for="modal-input-title" class="block text-xs font-bold text-[#554741]">
                                    ${escapeHTML(titleLabel)}
                                </label>
                                <input type="text" 
                                       id="modal-input-title" 
                                       placeholder="${escapeHTML(titlePlaceholder)}"
                                       class="w-full px-3.5 py-2 text-xs sm:text-sm rounded-xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white" />
                            </div>

                            <!-- Day Note Date Field -->
                            <div id="modal-group-date" class="${isDay ? 'block' : 'hidden'} space-y-1.5">
                                <label for="modal-input-date" class="block text-xs font-bold text-[#554741]">${escapeHTML(dateLabel)}</label>
                                <input type="date" 
                                       id="modal-input-date" 
                                       value="${escapeHTML(currentDate)}"
                                       class="w-full px-3.5 py-2 text-xs sm:text-sm rounded-xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white" />
                                <p class="text-[11px] text-[#8C827A]">${escapeHTML(dateHelper)}</p>
                            </div>

                            <!-- Task Note Selector Field -->
                            <div id="modal-group-task" class="${!isDay ? 'block' : 'hidden'} space-y-1.5">
                                <label for="modal-select-task" class="block text-xs font-bold text-[#554741]">${escapeHTML(taskLabel)}</label>
                                <select id="modal-select-task" 
                                        class="w-full px-3.5 py-2 text-xs sm:text-sm rounded-xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white">
                                    <option value="" disabled ${!currentTaskId ? 'selected' : ''}>${escapeHTML(selectTaskPlaceholder)}</option>
                                    ${availableTasks.length === 0 ? `
                                        <option value="" disabled>${escapeHTML(noActiveTasksText)}</option>
                                    ` : availableTasks.map(tItem => `
                                        <option value="${escapeHTML(tItem.id)}" ${tItem.id === currentTaskId ? 'selected' : ''}>${escapeHTML(tItem.name)}${tItem.deadlineDate ? ` (Due ${tItem.deadlineDate})` : ''}</option>
                                    `).join('')}
                                </select>
                            </div>

                            <!-- Note Content Textarea -->
                            <div class="space-y-1.5">
                                <label for="modal-textarea-content" class="block text-xs font-bold text-[#554741]">${escapeHTML(contentLabel)}</label>
                                <textarea id="modal-textarea-content" 
                                          rows="3" 
                                          placeholder="${escapeHTML(contentPlaceholder)}"
                                          class="w-full p-3.5 text-xs sm:text-sm rounded-2xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white resize-y min-h-[90px]"></textarea>
                            </div>

                            <div id="modal-create-feedback" class="text-xs font-semibold text-rose-600 min-h-[16px]"></div>

                            <!-- Actions -->
                            <div class="flex items-center justify-end space-x-2 pt-2 border-t border-stone-100">
                                <button type="button" 
                                        onclick="window.TempoToolNotes.closeModal()"
                                        id="modal-btn-cancel"
                                        class="px-4 py-2 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] hover:bg-stone-100 transition cursor-pointer">
                                    ${escapeHTML(cancelText)}
                                </button>
                                <button type="submit" 
                                        id="modal-btn-submit"
                                        class="px-5 py-2 rounded-xl font-bold text-xs bg-[#C88E7D] hover:bg-[#B97F6E] text-white shadow-2xs transition cursor-pointer">
                                    ${escapeHTML(saveText)}
                                </button>
                            </div>
                        </form>

                    </div>
                </div>
            `;

            // Restore preserved title and content
            const titleInput = document.getElementById('modal-input-title');
            if (titleInput && currentTitle) {
                titleInput.value = currentTitle;
            }
            const contentTextarea = document.getElementById('modal-textarea-content');
            if (contentTextarea && currentContent) {
                contentTextarea.value = currentContent;
            }

            // Attach pill click events
            const pDay = document.getElementById('modal-pill-day');
            const pTask = document.getElementById('modal-pill-task');
            if (pDay) pDay.onclick = () => {
                snapshotInputs();
                selectedType = 'day';
                renderModalBody();
            };
            if (pTask) pTask.onclick = () => {
                snapshotInputs();
                selectedType = 'task';
                renderModalBody();
            };

            // Attach form submission
            const form = document.getElementById('modal-create-note-form');
            if (form) {
                form.onsubmit = (e) => {
                    e.preventDefault();
                    if (isSavingNote) return;

                    const ta = document.getElementById('modal-textarea-content');
                    const textVal = ta ? ta.value.trim() : '';
                    const fb = document.getElementById('modal-create-feedback');
                    if (!textVal) {
                        if (fb) fb.innerText = t('toolNotes.validationContentMissing', isViLocale() ? 'Vui lòng nhập nội dung ghi chú.' : 'Please enter note content.');
                        if (ta) ta.focus();
                        return;
                    }

                    const tInput = document.getElementById('modal-input-title');
                    const customTitleVal = tInput ? tInput.value.trim() : '';

                    isSavingNote = true;
                    try {
                        if (selectedType === 'day') {
                            const dInput = document.getElementById('modal-input-date');
                            const dVal = dInput ? dInput.value.trim() : getTodayLocalDateStr();
                            if (!dVal) {
                                if (fb) fb.innerText = t('toolNotes.validationDateMissing', isViLocale() ? 'Vui lòng chọn ngày hợp lệ.' : 'Please select a date.');
                                isSavingNote = false;
                                return;
                            }
                            saveDayNote(textVal, dVal, null, customTitleVal);
                        } else {
                            const tSelect = document.getElementById('modal-select-task');
                            const tId = tSelect ? tSelect.value.trim() : '';
                            if (!tId) {
                                if (fb) fb.innerText = t('toolNotes.validationTaskMissing', isViLocale() ? 'Vui lòng chọn một công việc.' : 'Please select an associated task.');
                                isSavingNote = false;
                                return;
                            }
                            const tName = tSelect.options[tSelect.selectedIndex]?.text || (isViLocale() ? 'Công việc Học tập' : 'Study Task');
                            saveTaskNote(tId, tName, textVal, null, customTitleVal);
                        }
                        closeModal();
                    } finally {
                        isSavingNote = false;
                    }
                };
            }
        }

        // Subscribe to language change while modal is open
        const unsubscribeLang = window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function'
            ? window.TempoI18n.onLanguageChange(() => {
                snapshotInputs();
                renderModalBody();
            })
            : null;

        activeModalCleanup = () => {
            if (typeof unsubscribeLang === 'function') {
                try { unsubscribeLang(); } catch (e) {}
            }
        };

        renderModalBody();
    }\n\n"""

content = content[:start_idx] + new_open_modal + content[end_idx:]

assert '\r' not in content, "CRLF introduced into toolNotes.js!"

with open('toolNotes.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print(f"Successfully updated toolNotes.js! Total LF lines: {content.count(chr(10))}")
