import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('toolNotes.js', 'rb') as f:
    raw = f.read()

assert b'\r\n' not in raw, 'toolNotes.js must be LF'
content = raw.decode('utf-8')

# 1. Add isViLocale helper right inside the IIFE
old_header = """window.TempoToolNotes = (function () {
    'use strict';

    // State for Note Creation Form on Tool Notes Page
    let currentCreationType = 'day'; // 'day' | 'task'
    let isSavingNote = false;"""

new_header = """window.TempoToolNotes = (function () {
    'use strict';

    // Localization helper
    function isViLocale() {
        return !window.TempoI18n || typeof window.TempoI18n.getLanguage !== 'function' || window.TempoI18n.getLanguage() === 'vi';
    }

    if (typeof window !== 'undefined' && typeof window.isViLocale !== 'function') {
        window.isViLocale = isViLocale;
    }

    // State for Note Creation Form on Tool Notes Page
    let currentCreationType = 'day'; // 'day' | 'task'
    let isSavingNote = false;"""

assert old_header in content, 'old_header not found in toolNotes.js'
content = content.replace(old_header, new_header, 1)

# 2. Update saveDayNote signature and title assignment
old_save_day = """    function saveDayNote(text, dateStr, existingNoteId) {
        const trimmed = (text || '').trim();
        if (!trimmed) return null;

        const targetDate = dateStr ? getLocalDateStr(dateStr) : getTodayLocalDateStr();
        const now = new Date();
        const nowIso = now.toISOString();
        const notes = loadNotes();
        const uid = getUserId();

        let savedNote = null;

        if (existingNoteId) {
            const idx = notes.findIndex(n => String(n.id) === String(existingNoteId));
            if (idx !== -1) {
                notes[idx].text = trimmed;
                notes[idx].content = trimmed;
                notes[idx].date = targetDate;
                notes[idx].title = `Day Note - ${targetDate}`;
                notes[idx].updatedAt = nowIso;
                savedNote = notes[idx];
            }
        }

        if (!savedNote) {
            savedNote = {
                id: 'day_note_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
                type: 'day',
                category: 'day',
                date: targetDate,
                text: trimmed,
                content: trimmed,
                title: `Day Note - ${targetDate}`,
                user_id: uid,
                createdAt: nowIso,
                updatedAt: nowIso
            };
            notes.unshift(savedNote);
        }"""

new_save_day = """    function saveDayNote(text, dateStr, existingNoteId, customTitle) {
        const trimmed = (text || '').trim();
        if (!trimmed) return null;

        const targetDate = dateStr ? getLocalDateStr(dateStr) : getTodayLocalDateStr();
        const now = new Date();
        const nowIso = now.toISOString();
        const notes = loadNotes();
        const uid = getUserId();

        let savedNote = null;

        if (existingNoteId) {
            const idx = notes.findIndex(n => String(n.id) === String(existingNoteId));
            if (idx !== -1) {
                notes[idx].text = trimmed;
                notes[idx].content = trimmed;
                notes[idx].date = targetDate;
                if (customTitle && customTitle.trim()) {
                    notes[idx].title = customTitle.trim();
                } else if (!notes[idx].title) {
                    notes[idx].title = `Day Note - ${targetDate}`;
                }
                notes[idx].updatedAt = nowIso;
                savedNote = notes[idx];
            }
        }

        if (!savedNote) {
            const finalTitle = (customTitle && customTitle.trim()) ? customTitle.trim() : `Day Note - ${targetDate}`;
            savedNote = {
                id: 'day_note_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
                type: 'day',
                category: 'day',
                date: targetDate,
                text: trimmed,
                content: trimmed,
                title: finalTitle,
                user_id: uid,
                createdAt: nowIso,
                updatedAt: nowIso
            };
            notes.unshift(savedNote);
        }"""

assert old_save_day in content, 'old_save_day not found in toolNotes.js'
content = content.replace(old_save_day, new_save_day, 1)

# 3. Update saveTaskNote signature and title assignment
old_save_task = """    function saveTaskNote(taskId, taskName, text, existingNoteId) {
        const trimmed = (text || '').trim();
        const sId = taskId ? String(taskId) : null;
        if (!sId || !trimmed) return null;

        const now = new Date();
        const nowIso = now.toISOString();
        const notes = loadNotes();
        const uid = getUserId();

        let savedNote = null;

        if (existingNoteId) {
            const idx = notes.findIndex(n => String(n.id) === String(existingNoteId));
            if (idx !== -1) {
                notes[idx].taskId = sId;
                notes[idx].taskName = taskName || notes[idx].taskName || (isViLocale() ? 'Công việc Học tập' : 'Study Task');
                notes[idx].title = `Note for ${notes[idx].taskName}`;
                notes[idx].text = trimmed;
                notes[idx].content = trimmed;
                notes[idx].updatedAt = nowIso;
                savedNote = notes[idx];
            }
        }

        if (!savedNote) {
            const existingTaskNoteIdx = notes.findIndex(n => String(n.taskId) === sId);
            if (existingTaskNoteIdx !== -1) {
                notes[existingTaskNoteIdx].text = trimmed;
                notes[existingTaskNoteIdx].content = trimmed;
                notes[existingTaskNoteIdx].taskName = taskName || notes[existingTaskNoteIdx].taskName || (isViLocale() ? 'Công việc Học tập' : 'Study Task');
                notes[existingTaskNoteIdx].title = `Note for ${notes[existingTaskNoteIdx].taskName}`;
                notes[existingTaskNoteIdx].updatedAt = nowIso;
                savedNote = notes[existingTaskNoteIdx];
            } else {
                savedNote = {
                    id: 'tool_note_task_' + sId + '_' + Date.now().toString(36),
                    taskId: sId,
                    taskName: taskName || (isViLocale() ? 'Công việc Học tập' : 'Study Task'),
                    title: `Note for ${taskName || (isViLocale() ? 'Công việc Học tập' : 'Study Task')}`,
                    type: 'task',
                    category: 'task',
                    date: getTodayLocalDateStr(),
                    text: trimmed,
                    content: trimmed,
                    user_id: uid,
                    createdAt: nowIso,
                    updatedAt: nowIso
                };
                notes.unshift(savedNote);
            }
        }"""

new_save_task = """    function saveTaskNote(taskId, taskName, text, existingNoteId, customTitle) {
        const trimmed = (text || '').trim();
        const sId = taskId ? String(taskId) : null;
        if (!sId || !trimmed) return null;

        const now = new Date();
        const nowIso = now.toISOString();
        const notes = loadNotes();
        const uid = getUserId();

        let savedNote = null;

        if (existingNoteId) {
            const idx = notes.findIndex(n => String(n.id) === String(existingNoteId));
            if (idx !== -1) {
                notes[idx].taskId = sId;
                notes[idx].taskName = taskName || notes[idx].taskName || (isViLocale() ? 'Công việc Học tập' : 'Study Task');
                if (customTitle && customTitle.trim()) {
                    notes[idx].title = customTitle.trim();
                } else {
                    notes[idx].title = `Note for ${notes[idx].taskName}`;
                }
                notes[idx].text = trimmed;
                notes[idx].content = trimmed;
                notes[idx].updatedAt = nowIso;
                savedNote = notes[idx];
            }
        }

        if (!savedNote) {
            const existingTaskNoteIdx = notes.findIndex(n => String(n.taskId) === sId);
            if (existingTaskNoteIdx !== -1) {
                notes[existingTaskNoteIdx].text = trimmed;
                notes[existingTaskNoteIdx].content = trimmed;
                notes[existingTaskNoteIdx].taskName = taskName || notes[existingTaskNoteIdx].taskName || (isViLocale() ? 'Công việc Học tập' : 'Study Task');
                if (customTitle && customTitle.trim()) {
                    notes[existingTaskNoteIdx].title = customTitle.trim();
                } else {
                    notes[existingTaskNoteIdx].title = `Note for ${notes[existingTaskNoteIdx].taskName}`;
                }
                notes[existingTaskNoteIdx].updatedAt = nowIso;
                savedNote = notes[existingTaskNoteIdx];
            } else {
                const defaultTitle = `Note for ${taskName || (isViLocale() ? 'Công việc Học tập' : 'Study Task')}`;
                savedNote = {
                    id: 'tool_note_task_' + sId + '_' + Date.now().toString(36),
                    taskId: sId,
                    taskName: taskName || (isViLocale() ? 'Công việc Học tập' : 'Study Task'),
                    title: (customTitle && customTitle.trim()) ? customTitle.trim() : defaultTitle,
                    type: 'task',
                    category: 'task',
                    date: getTodayLocalDateStr(),
                    text: trimmed,
                    content: trimmed,
                    user_id: uid,
                    createdAt: nowIso,
                    updatedAt: nowIso
                };
                notes.unshift(savedNote);
            }
        }"""

assert old_save_task in content, 'old_save_task not found in toolNotes.js'
content = content.replace(old_save_task, new_save_task, 1)

# 4. Update handleCreateFormSubmit on page
old_form_submit = """        if (currentCreationType === 'day') {
            const dateInput = document.getElementById('input-note-date');
            const dateVal = dateInput ? dateInput.value.trim() : getTodayLocalDateStr();
            if (!dateVal) {
                if (feedback) {
                    feedback.innerHTML = `<span class="text-rose-600 font-bold">⚠️ Please select a valid date.</span>`;
                }
                return;
            }

            isSavingNote = true;
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.classList.add('opacity-70', 'cursor-not-allowed');
                submitBtn.innerHTML = `<span>Saving...</span>`;
            }

            try {
                saveDayNote(content, dateVal);
                if (textarea) textarea.value = '';"""

new_form_submit = """        const titleInput = document.getElementById('input-note-title');
        const customTitleVal = titleInput ? titleInput.value.trim() : '';

        if (currentCreationType === 'day') {
            const dateInput = document.getElementById('input-note-date');
            const dateVal = dateInput ? dateInput.value.trim() : getTodayLocalDateStr();
            if (!dateVal) {
                if (feedback) {
                    feedback.innerHTML = `<span class="text-rose-600 font-bold">⚠️ Please select a valid date.</span>`;
                }
                return;
            }

            isSavingNote = true;
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.classList.add('opacity-70', 'cursor-not-allowed');
                submitBtn.innerHTML = `<span>Saving...</span>`;
            }

            try {
                saveDayNote(content, dateVal, null, customTitleVal);
                if (textarea) textarea.value = '';
                if (titleInput) titleInput.value = '';"""

assert old_form_submit in content, 'old_form_submit not found in toolNotes.js'
content = content.replace(old_form_submit, new_form_submit, 1)

# Also update task note branch in handleCreateFormSubmit
old_task_branch = """            try {
                saveTaskNote(taskId, taskName, content);
                if (textarea) textarea.value = '';"""

new_task_branch = """            try {
                saveTaskNote(taskId, taskName, content, null, customTitleVal);
                if (textarea) textarea.value = '';
                if (titleInput) titleInput.value = '';"""

assert old_task_branch in content, 'old_task_branch not found in toolNotes.js'
content = content.replace(old_task_branch, new_task_branch, 1)

# 5. Add title field in tool-notes-create-form
old_form_date_field = """                <!-- Form -->
                <form id="tool-notes-create-form" onsubmit="event.preventDefault(); window.TempoToolNotes.handleCreateFormSubmit();" class="space-y-4">
                    <!-- Day Note Date Field -->"""

new_form_date_field = """                <!-- Form -->
                <form id="tool-notes-create-form" onsubmit="event.preventDefault(); window.TempoToolNotes.handleCreateFormSubmit();" class="space-y-4">
                    <!-- Note Title Field -->
                    <div class="space-y-1.5">
                        <label for="input-note-title" class="block text-xs font-bold text-[#554741]">
                            ${isViLocale() ? 'Tiêu đề ghi chú (tùy chọn)' : 'Note Title (optional)'}
                        </label>
                        <input type="text" 
                               id="input-note-title" 
                               placeholder="${isViLocale() ? 'VD: Suy nghĩ hôm nay, Tóm tắt bài giảng...' : 'e.g. Daily reflection, Lecture summary...'}"
                               class="w-full max-w-md px-3.5 py-2 text-xs sm:text-sm rounded-xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white transition" />
                    </div>

                    <!-- Day Note Date Field -->"""

assert old_form_date_field in content, 'old_form_date_field not found in toolNotes.js'
content = content.replace(old_form_date_field, new_form_date_field, 1)

# 6. Add title field and double-click prevention in openCreateNoteModal
old_modal_form = """                        <!-- Form -->
                        <form id="modal-create-note-form" class="space-y-4">
                            <!-- Day Note Date Field -->"""

new_modal_form = """                        <!-- Form -->
                        <form id="modal-create-note-form" class="space-y-4">
                            <!-- Note Title Field -->
                            <div class="space-y-1.5">
                                <label for="modal-input-title" class="block text-xs font-bold text-[#554741]">
                                    ${isViLocale() ? 'Tiêu đề ghi chú (tùy chọn)' : 'Note Title (optional)'}
                                </label>
                                <input type="text" 
                                       id="modal-input-title" 
                                       placeholder="${isViLocale() ? 'VD: Suy nghĩ hôm nay, Tóm tắt bài giảng...' : 'e.g. Daily reflection, Lecture summary...'}"
                                       class="w-full px-3.5 py-2 text-xs sm:text-sm rounded-xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white" />
                            </div>

                            <!-- Day Note Date Field -->"""

assert old_modal_form in content, 'old_modal_form not found in toolNotes.js'
content = content.replace(old_modal_form, new_modal_form, 1)

# Modal form onsubmit handler
old_modal_submit = """            // Attach form submission
            const form = document.getElementById('modal-create-note-form');
            if (form) {
                form.onsubmit = (e) => {
                    e.preventDefault();
                    const ta = document.getElementById('modal-textarea-content');
                    const textVal = ta ? ta.value.trim() : '';
                    const fb = document.getElementById('modal-create-feedback');
                    if (!textVal) {
                        if (fb) fb.innerText = 'Please enter note content.';
                        if (ta) ta.focus();
                        return;
                    }

                    if (selectedType === 'day') {
                        const dInput = document.getElementById('modal-input-date');
                        const dVal = dInput ? dInput.value.trim() : getTodayLocalDateStr();
                        if (!dVal) {
                            if (fb) fb.innerText = 'Please select a date.';
                            return;
                        }
                        saveDayNote(textVal, dVal);
                    } else {
                        const tSelect = document.getElementById('modal-select-task');
                        const tId = tSelect ? tSelect.value.trim() : '';
                        if (!tId) {
                            if (fb) fb.innerText = 'Please select an associated task.';
                            return;
                        }
                        const tName = tSelect.options[tSelect.selectedIndex]?.text || (isViLocale() ? 'Công việc Học tập' : 'Study Task');
                        saveTaskNote(tId, tName, textVal);
                    }
                    closeModal();
                };
            }"""

new_modal_submit = """            // Attach form submission
            const form = document.getElementById('modal-create-note-form');
            if (form) {
                form.onsubmit = (e) => {
                    e.preventDefault();
                    if (isSavingNote) return;

                    const ta = document.getElementById('modal-textarea-content');
                    const textVal = ta ? ta.value.trim() : '';
                    const fb = document.getElementById('modal-create-feedback');
                    if (!textVal) {
                        if (fb) fb.innerText = isViLocale() ? 'Vui lòng nhập nội dung ghi chú.' : 'Please enter note content.';
                        if (ta) ta.focus();
                        return;
                    }

                    const titleInput = document.getElementById('modal-input-title');
                    const customTitleVal = titleInput ? titleInput.value.trim() : '';

                    isSavingNote = true;
                    try {
                        if (selectedType === 'day') {
                            const dInput = document.getElementById('modal-input-date');
                            const dVal = dInput ? dInput.value.trim() : getTodayLocalDateStr();
                            if (!dVal) {
                                if (fb) fb.innerText = isViLocale() ? 'Vui lòng chọn ngày hợp lệ.' : 'Please select a date.';
                                isSavingNote = false;
                                return;
                            }
                            saveDayNote(textVal, dVal, null, customTitleVal);
                        } else {
                            const tSelect = document.getElementById('modal-select-task');
                            const tId = tSelect ? tSelect.value.trim() : '';
                            if (!tId) {
                                if (fb) fb.innerText = isViLocale() ? 'Vui lòng chọn một công việc.' : 'Please select an associated task.';
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
            }"""

assert old_modal_submit in content, 'old_modal_submit not found in toolNotes.js'
content = content.replace(old_modal_submit, new_modal_submit, 1)

# 7. Add language change listener in toolNotes.js
old_init_block = """    function init() {
        renderToolNotesPage();
    }"""

new_init_block = """    function init() {
        renderToolNotesPage();
    }

    if (typeof window !== 'undefined' && window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
        window.TempoI18n.onLanguageChange(() => {
            const root = document.getElementById('tool-notes-root');
            if (root) {
                renderToolNotesPage();
            }
        });
    }"""

assert old_init_block in content, 'old_init_block not found in toolNotes.js'
content = content.replace(old_init_block, new_init_block, 1)

new_raw = content.encode('utf-8')
assert b'\r\n' not in new_raw, 'toolNotes.js must remain strictly LF'

with open('toolNotes.js', 'wb') as f:
    f.write(new_raw)

print(f'Successfully updated toolNotes.js! Lines: {len(new_raw.split(b"\n"))}')
