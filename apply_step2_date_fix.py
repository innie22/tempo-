import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('urmodeFlow.js', 'r', encoding='utf-8', newline='') as f:
    text = f.read()

assert '\r\n' not in text, "urmodeFlow.js has CRLF before patch!"

# Find renderAdjustmentStep2Tasks
idx_step2 = text.find('    // Step 2: Adjust retained tasks & add new tasks\n    function renderAdjustmentStep2Tasks() {')
assert idx_step2 != -1, "renderAdjustmentStep2Tasks not found!"

# Find handleAdjustmentStep2Back
idx_back = text.find('    function handleAdjustmentStep2Back() {')
assert idx_back != -1, "handleAdjustmentStep2Back not found!"

# Replace from idx_step2 to idx_back with new functions:
new_step2_block = """    // Step 2: Date Formatting & Parsing Helpers
    function formatStep2DisplayDate(isoStr) {
        if (!isoStr || typeof isoStr !== 'string') return '';
        const clean = isoStr.trim();
        if (!clean) return '';
        if (window.TempoI18n && typeof window.TempoI18n.formatCalendarDate === 'function') {
            return window.TempoI18n.formatCalendarDate(clean, isViLocale() ? 'vi' : 'en');
        }
        const parts = clean.split('-');
        if (parts.length === 3) {
            const y = parts[0];
            const m = parts[1].padStart(2, '0');
            const d = parts[2].padStart(2, '0');
            if (isViLocale()) {
                return `${d}/${m}/${y}`;
            } else {
                const enMonths = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                const mName = enMonths[parseInt(m, 10) - 1] || m;
                return `${mName} ${d}, ${y}`;
            }
        }
        return clean;
    }

    function parseStep2DateInput(inputVal) {
        if (!inputVal || typeof inputVal !== 'string') return '';
        const val = inputVal.trim();
        if (!val) return '';

        // 1. Check ISO YYYY-MM-DD
        const isoMatch = val.match(/^(\\d{4})-(\\d{1,2})-(\\d{1,2})$/);
        if (isoMatch) {
            const y = parseInt(isoMatch[1], 10);
            const m = parseInt(isoMatch[2], 10);
            const d = parseInt(isoMatch[3], 10);
            if (y >= 1900 && y <= 2100 && m >= 1 && m <= 12 && d >= 1 && d <= 31) {
                return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            }
        }

        // 2. Check English textual date: e.g. "Nov 02, 2026", "Nov 2, 2026", "November 2, 2026"
        const enMonthsMap = {
            jan: 1, january: 1,
            feb: 2, february: 2,
            mar: 3, march: 3,
            apr: 4, april: 4,
            may: 5,
            jun: 6, june: 6,
            jul: 7, july: 7,
            aug: 8, august: 8,
            sep: 9, sept: 9, september: 9,
            oct: 10, october: 10,
            nov: 11, november: 11,
            dec: 12, december: 12
        };
        const enTextMatch = val.match(/^([a-zA-Z]{3,9})\\s+(\\d{1,2})(?:st|nd|rd|th)?,?\\s+(\\d{4})$/i);
        if (enTextMatch) {
            const monthKey = enTextMatch[1].toLowerCase();
            const m = enMonthsMap[monthKey];
            const d = parseInt(enTextMatch[2], 10);
            const y = parseInt(enTextMatch[3], 10);
            if (m && d >= 1 && d <= 31 && y >= 1900 && y <= 2100) {
                return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            }
        }

        // 3. Numeric format with slash/dash/dot: e.g. "02/11/2026", "2/11/2026", "02-11-2026"
        const numMatch = val.match(/^(\\d{1,2})[\\/\\-\\.](\\d{1,2})[\\/\\-\\.](\\d{4})$/);
        if (numMatch) {
            let p1 = parseInt(numMatch[1], 10);
            let p2 = parseInt(numMatch[2], 10);
            const y = parseInt(numMatch[3], 10);

            let d, m;
            if (isViLocale()) {
                // Strictly DD/MM/YYYY in Vietnamese
                d = p1;
                m = p2;
            } else {
                if (p1 > 12) {
                    d = p1;
                    m = p2;
                } else if (p2 > 12) {
                    m = p1;
                    d = p2;
                } else {
                    m = p1;
                    d = p2;
                }
            }

            if (m >= 1 && m <= 12 && d >= 1 && d <= 31 && y >= 1900 && y <= 2100) {
                return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            }
        }

        return '';
    }

    function handleStep2DateInput(taskId, inputEl) {
        if (!inputEl) return;
        const val = inputEl.value.trim();
        const picker = document.getElementById(`adjust-due-picker-${taskId}`);
        if (!val) {
            inputEl.dataset.iso = '';
            if (picker) picker.value = '';
            updateRetainedDueDate(taskId, '');
            return;
        }
        const iso = parseStep2DateInput(val);
        if (iso) {
            inputEl.dataset.iso = iso;
            if (picker) picker.value = iso;
            updateRetainedDueDate(taskId, iso);
        }
    }

    function handleStep2DateBlur(taskId, inputEl) {
        if (!inputEl) return;
        const val = inputEl.value.trim();
        if (!val) {
            inputEl.dataset.iso = '';
            inputEl.value = '';
            updateRetainedDueDate(taskId, '');
            return;
        }
        const iso = inputEl.dataset.iso || parseStep2DateInput(val);
        if (iso) {
            inputEl.dataset.iso = iso;
            inputEl.value = formatStep2DisplayDate(iso);
            const picker = document.getElementById(`adjust-due-picker-${taskId}`);
            if (picker) picker.value = iso;
            updateRetainedDueDate(taskId, iso);
        } else {
            const item = adjustmentDraft?.retainedTasks?.find(t => String(t.id) === String(taskId));
            if (item && item.deadlineDate) {
                inputEl.dataset.iso = item.deadlineDate;
                inputEl.value = formatStep2DisplayDate(item.deadlineDate);
            } else {
                inputEl.dataset.iso = '';
                inputEl.value = '';
                updateRetainedDueDate(taskId, '');
            }
        }
    }

    function handleStep2PickerChange(taskId, isoVal) {
        const textInput = document.getElementById(`adjust-due-${taskId}`);
        const cleanIso = (isoVal || '').trim();
        if (textInput) {
            textInput.dataset.iso = cleanIso;
            textInput.value = formatStep2DisplayDate(cleanIso);
        }
        updateRetainedDueDate(taskId, cleanIso);
    }

    function handleStep2NewTaskDateInput(inputEl) {
        if (!inputEl) return;
        const val = inputEl.value.trim();
        const picker = document.getElementById('adjust-new-task-due-picker');
        if (!val) {
            inputEl.dataset.iso = '';
            if (picker) picker.value = '';
            return;
        }
        const iso = parseStep2DateInput(val);
        if (iso) {
            inputEl.dataset.iso = iso;
            if (picker) picker.value = iso;
        }
    }

    function handleStep2NewTaskDateBlur(inputEl) {
        if (!inputEl) return;
        const val = inputEl.value.trim();
        if (!val) {
            inputEl.dataset.iso = '';
            inputEl.value = '';
            return;
        }
        const iso = inputEl.dataset.iso || parseStep2DateInput(val);
        if (iso) {
            inputEl.dataset.iso = iso;
            inputEl.value = formatStep2DisplayDate(iso);
            const picker = document.getElementById('adjust-new-task-due-picker');
            if (picker) picker.value = iso;
        } else {
            inputEl.dataset.iso = '';
            inputEl.value = '';
        }
    }

    function handleStep2NewTaskPickerChange(isoVal) {
        const textInput = document.getElementById('adjust-new-task-due');
        const cleanIso = (isoVal || '').trim();
        if (textInput) {
            textInput.dataset.iso = cleanIso;
            textInput.value = formatStep2DisplayDate(cleanIso);
        }
    }

    // Step 2: Adjust retained tasks & add new tasks
    function renderAdjustmentStep2Tasks() {
        activeModalView = 'adjust_tasks';
        const kept = adjustmentDraft.retainedTasks.filter(t => t._keep);
        const datePlaceholder = window.t ? window.t('workspace.datePlaceholderStep2', {}, (isViLocale() ? 'dd/mm/yyyy' : 'MMM DD, YYYY')) : (isViLocale() ? 'dd/mm/yyyy' : 'MMM DD, YYYY');

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
                ${kept.map(t => {
                    const displayDue = formatStep2DisplayDate(t.deadlineDate);
                    return `
                    <div class="p-3 rounded-2xl border border-stone-200 bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 text-xs">
                        <div class="min-w-0 flex-1">
                            <span class="font-bold text-stone-800 truncate block">${escapeHTML(t.name || t.title)}</span>
                        </div>
                        <div class="flex items-center gap-2 shrink-0 flex-wrap">
                            <div class="flex items-center space-x-1.5">
                                <label for="adjust-due-${t.id}" class="text-[11px] font-semibold text-stone-500">
                                    ${window.t ? window.t('workspace.duePrefixLabel', {}, 'Due:') : (isViLocale() ? 'Deadline:' : 'Due:')}
                                </label>
                                <div class="relative inline-flex items-center">
                                    <input type="text"
                                           id="adjust-due-${t.id}"
                                           data-iso="${t.deadlineDate || ''}"
                                           value="${escapeHTML(displayDue)}"
                                           placeholder="${escapeHTML(datePlaceholder)}"
                                           oninput="window.TempoUrmodeFlow.handleStep2DateInput('${t.id}', this)"
                                           onchange="window.TempoUrmodeFlow.handleStep2DateBlur('${t.id}', this)"
                                           onblur="window.TempoUrmodeFlow.handleStep2DateBlur('${t.id}', this)"
                                           class="pl-2.5 pr-7 py-1.5 rounded-xl border border-stone-300 text-xs text-stone-700 bg-white focus:outline-none focus:ring-1 focus:ring-[#D79277] w-[115px] sm:w-[125px]" />
                                    <input type="date"
                                           id="adjust-due-picker-${t.id}"
                                           tabindex="-1"
                                           aria-hidden="true"
                                           value="${t.deadlineDate || ''}"
                                           onchange="window.TempoUrmodeFlow.handleStep2PickerChange('${t.id}', this.value)"
                                           class="absolute right-1 w-6 h-6 opacity-0 cursor-pointer z-10" />
                                    <span class="absolute right-2 pointer-events-none text-stone-400 text-xs select-none">
                                        📅
                                    </span>
                                </div>
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
                `;}).join('')}
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
                        <div class="relative inline-flex items-center">
                            <input type="text"
                                   id="adjust-new-task-due"
                                   data-iso=""
                                   value=""
                                   placeholder="${escapeHTML(datePlaceholder)}"
                                   oninput="window.TempoUrmodeFlow.handleStep2NewTaskDateInput(this)"
                                   onchange="window.TempoUrmodeFlow.handleStep2NewTaskDateBlur(this)"
                                   onblur="window.TempoUrmodeFlow.handleStep2NewTaskDateBlur(this)"
                                   class="pl-2.5 pr-7 py-1.5 rounded-xl border border-stone-300 text-xs text-stone-700 bg-white focus:outline-none focus:ring-1 focus:ring-[#D79277] w-[115px] sm:w-[125px]" />
                            <input type="date"
                                   id="adjust-new-task-due-picker"
                                   tabindex="-1"
                                   aria-hidden="true"
                                   value=""
                                   onchange="window.TempoUrmodeFlow.handleStep2NewTaskPickerChange(this.value)"
                                   class="absolute right-1 w-6 h-6 opacity-0 cursor-pointer z-10" />
                            <span class="absolute right-2 pointer-events-none text-stone-400 text-xs select-none">
                                📅
                            </span>
                        </div>
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
                            const dueFormatted = nt.hasDeadline && nt.deadlineDate ? formatStep2DisplayDate(nt.deadlineDate) : '';
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
    }

    function syncStep2InputsFromDom() {
        if (!adjustmentDraft || !Array.isArray(adjustmentDraft.retainedTasks)) return;
        const kept = adjustmentDraft.retainedTasks.filter(t => t._keep);
        kept.forEach(t => {
            const dueInput = document.getElementById(`adjust-due-${t.id}`);
            if (dueInput) {
                const iso = dueInput.dataset.iso || parseStep2DateInput(dueInput.value) || '';
                updateRetainedDueDate(t.id, iso);
            }
            const durSelect = document.getElementById(`adjust-dur-${t.id}`);
            if (durSelect) {
                updateRetainedDuration(t.id, durSelect.value);
            }
        });
    }

"""

text = text[:idx_step2] + new_step2_block + text[idx_back:]

# Also update updateRetainedDueDate
old_update_due = """    function updateRetainedDueDate(taskId, dateVal) {
        if (!adjustmentDraft || !Array.isArray(adjustmentDraft.retainedTasks)) return;
        const item = adjustmentDraft.retainedTasks.find(t => String(t.id) === String(taskId));
        if (item) {
            const val = (dateVal || '').trim();
            if (val) {
                item.hasDeadline = true;
                item.deadlineDate = val;
                if (!item.deadlineTime) {
                    item.deadlineTime = '23:59';
                }
                item.deadline = `${item.deadlineDate} ${item.deadlineTime}`;
            } else {
                item.hasDeadline = false;
                item.deadlineDate = null;
                item.deadlineTime = null;
                item.deadline = null;
            }
        }
    }"""

new_update_due = """    function updateRetainedDueDate(taskId, dateVal) {
        if (!adjustmentDraft || !Array.isArray(adjustmentDraft.retainedTasks)) return;
        const item = adjustmentDraft.retainedTasks.find(t => String(t.id) === String(taskId));
        if (item) {
            const raw = (dateVal || '').trim();
            const iso = parseStep2DateInput(raw) || (raw.match(/^\\d{4}-\\d{2}-\\d{2}$/) ? raw : '');
            if (iso) {
                item.hasDeadline = true;
                item.deadlineDate = iso;
                if (!item.deadlineTime) {
                    item.deadlineTime = '23:59';
                }
                item.deadline = `${item.deadlineDate} ${item.deadlineTime}`;
            } else {
                item.hasDeadline = false;
                item.deadlineDate = null;
                item.deadlineTime = null;
                item.deadline = null;
            }
        }
    }"""

assert old_update_due in text, "old_update_due not found!"
text = text.replace(old_update_due, new_update_due, 1)

# Also update addNewAdjustmentTask
old_add_task = """    function addNewAdjustmentTask() {
        const nameInput = document.getElementById('adjust-new-task-name');
        const durInput = document.getElementById('adjust-new-task-dur');
        const dueInput = document.getElementById('adjust-new-task-due');
        const name = nameInput ? nameInput.value.trim() : '';
        if (!name) return;

        // Sync existing retained inputs from DOM before re-rendering
        syncStep2InputsFromDom();

        const dur = parseInt(durInput?.value || '30', 10);
        const dueDate = dueInput ? (dueInput.value || '').trim() : '';
        const hasDeadline = Boolean(dueDate);

        adjustmentDraft.newTasks.push({
            id: 'task-adj-' + Date.now() + '-' + Math.random().toString(36).substr(2, 4),
            name: name,
            durationMinutes: dur,
            durationLabel: formatDuration(dur),
            hasDeadline: hasDeadline,
            deadlineDate: hasDeadline ? dueDate : null,
            deadlineTime: hasDeadline ? '23:59' : null,
            deadline: hasDeadline ? `${dueDate} 23:59` : null,
            completed: false,
            isInProgress: false,
            subtasks: []
        });

        renderAdjustmentStep2Tasks();
    }"""

new_add_task = """    function addNewAdjustmentTask() {
        const nameInput = document.getElementById('adjust-new-task-name');
        const durInput = document.getElementById('adjust-new-task-dur');
        const dueInput = document.getElementById('adjust-new-task-due');
        const name = nameInput ? nameInput.value.trim() : '';
        if (!name) return;

        // Sync existing retained inputs from DOM before re-rendering
        syncStep2InputsFromDom();

        const dur = parseInt(durInput?.value || '30', 10);
        const rawDue = dueInput ? (dueInput.dataset.iso || parseStep2DateInput(dueInput.value) || dueInput.value || '').trim() : '';
        const dueDate = parseStep2DateInput(rawDue) || (rawDue.match(/^\\d{4}-\\d{2}-\\d{2}$/) ? rawDue : '');
        const hasDeadline = Boolean(dueDate);

        adjustmentDraft.newTasks.push({
            id: 'task-adj-' + Date.now() + '-' + Math.random().toString(36).substr(2, 4),
            name: name,
            durationMinutes: dur,
            durationLabel: formatDuration(dur),
            hasDeadline: hasDeadline,
            deadlineDate: hasDeadline ? dueDate : null,
            deadlineTime: hasDeadline ? '23:59' : null,
            deadline: hasDeadline ? `${dueDate} 23:59` : null,
            completed: false,
            isInProgress: false,
            subtasks: []
        });

        renderAdjustmentStep2Tasks();
    }"""

assert old_add_task in text, "old_add_task not found!"
text = text.replace(old_add_task, new_add_task, 1)

# Also update onLanguageChange listener to preserve and translate draft due date
old_listener = """            } else if (activeModalView === 'adjust_tasks') {
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
            }"""

new_listener = """            } else if (activeModalView === 'adjust_tasks') {
                const draftName = document.getElementById('adjust-new-task-name')?.value || '';
                const newDueEl = document.getElementById('adjust-new-task-due');
                const draftDueIso = newDueEl ? (newDueEl.dataset.iso || parseStep2DateInput(newDueEl.value) || '') : '';
                const draftDur = document.getElementById('adjust-new-task-dur')?.value || '30';
                syncStep2InputsFromDom();
                renderAdjustmentStep2Tasks();
                const newNameInput = document.getElementById('adjust-new-task-name');
                const newDueInput = document.getElementById('adjust-new-task-due');
                const newDuePicker = document.getElementById('adjust-new-task-due-picker');
                const newDurInput = document.getElementById('adjust-new-task-dur');
                if (newNameInput && draftName) newNameInput.value = draftName;
                if (newDueInput && draftDueIso) {
                    newDueInput.dataset.iso = draftDueIso;
                    newDueInput.value = formatStep2DisplayDate(draftDueIso);
                    if (newDuePicker) newDuePicker.value = draftDueIso;
                }
                if (newDurInput && draftDur) newDurInput.value = draftDur;
            }"""

assert old_listener in text, "old_listener not found!"
text = text.replace(old_listener, new_listener, 1)

# Export new helper functions
old_exports = """        // Working Plan Adjustment
        startAdjustmentFlow,
        renderAdjustmentStep1Keep,
        toggleRetainedTask,
        renderAdjustmentStep2Tasks,"""

new_exports = """        // Working Plan Adjustment
        startAdjustmentFlow,
        renderAdjustmentStep1Keep,
        toggleRetainedTask,
        renderAdjustmentStep2Tasks,
        formatStep2DisplayDate,
        parseStep2DateInput,
        handleStep2DateInput,
        handleStep2DateBlur,
        handleStep2PickerChange,
        handleStep2NewTaskDateInput,
        handleStep2NewTaskDateBlur,
        handleStep2NewTaskPickerChange,"""

assert old_exports in text, "old_exports not found!"
text = text.replace(old_exports, new_exports, 1)

assert '\r\n' not in text, "urmodeFlow.js has CRLF after patch!"

with open('urmodeFlow.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print("urmodeFlow.js updated successfully with localized Step 2 date formatting! (LF only)")
