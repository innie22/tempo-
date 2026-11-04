import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('planWorkspace.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update activeModal declaration
old_decl = """    let activeModal = null; // null | 'add-task' | 'fit-task-prompt' | 'adjust-availability' | 'reschedule' | 'deadline-plan-reorder-confirm' | 'edit-task-note'"""
new_decl = """    let activeModal = null; // null | 'add-task' | 'fit-task-prompt' | 'adjust-availability' | 'add-available-time' | 'reschedule' | 'repeat-weekly-config' | 'clear-task-confirm' | 'delete-plan-confirm' | 'deadline-plan-reorder-confirm' | 'edit-task-note'
    let isEditingTaskTitle = false;"""
assert old_decl in content, "Failed to match old_decl"
content = content.replace(old_decl, new_decl, 1)

# 2. Update open()
old_open = """    function open() {
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('plan-workspace');
        } else {
            window.location.hash = '#plan-workspace';
        }
        const plan = getActivePlan();
        if (plan) {
            const changed = cleanupExpiredAvailability(plan);
            if (changed) {
                persistPlan(plan);
            }
        }
        render();
    }"""
new_open = """    function open() {
        resetWorkspaceState();
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('plan-workspace');
        } else {
            window.location.hash = '#plan-workspace';
        }
        const plan = getActivePlan();
        if (plan) {
            const changed = cleanupExpiredAvailability(plan);
            if (changed) {
                persistPlan(plan);
            }
        }
        render();
    }"""
assert old_open in content, "Failed to match old_open"
content = content.replace(old_open, new_open, 1)

# 3. Update selectTask()
old_select = """    function selectTask(taskId) {
        selectedTaskId = taskId;
        isEditingDeadline = false;
        render();
    }"""
new_select = """    function selectTask(taskId) {
        selectedTaskId = taskId;
        isEditingDeadline = false;
        isEditingEstimate = false;
        isEditingTaskTitle = false;
        activeModal = null;
        render();
    }"""
assert old_select in content, "Failed to match old_select"
content = content.replace(old_select, new_select, 1)

# 4. Update toggleDeadlineEdit and add openDeadlineEdit
old_deadline_edit = """    function toggleDeadlineEdit() {
        isEditingDeadline = !isEditingDeadline;
        render();
    }"""
new_deadline_edit = """    function toggleDeadlineEdit(forceState) {
        if (typeof forceState === 'boolean') {
            isEditingDeadline = forceState;
        } else {
            isEditingDeadline = !isEditingDeadline;
        }
        if (isEditingDeadline) {
            activeModal = null;
            isEditingEstimate = false;
            isEditingTaskTitle = false;
        }
        render();
        if (isEditingDeadline) {
            const dateInput = document.getElementById('pw-edit-deadline-date');
            if (dateInput) dateInput.focus();
        }
    }

    function openDeadlineEdit(taskId) {
        if (taskId) selectedTaskId = taskId;
        toggleDeadlineEdit(true);
    }"""
assert old_deadline_edit in content, "Failed to match old_deadline_edit"
content = content.replace(old_deadline_edit, new_deadline_edit, 1)

# 5. Add toggleTaskTitleEdit, openEditTaskModal, saveTaskTitleEdit, update openBreakTaskModal
old_break_task = """    function openBreakTaskModal(taskId) {
        const targetId = taskId || selectedTaskId;
        if (!targetId) return;
        if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.renderBreakTaskPopup === 'function') {
            window.TempoUrmodeFlow.renderBreakTaskPopup(targetId, 'plan-workspace');
        } else if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.startBreakTaskFlow === 'function') {
            window.TempoUrmodeFlow.startBreakTaskFlow(targetId);
        } else if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.reviewStepBreakdown === 'function') {
            window.TempoEmergencyFlow.reviewStepBreakdown(targetId);
        }
    }"""

new_break_task = """    function toggleTaskTitleEdit(forceState) {
        if (typeof forceState === 'boolean') {
            isEditingTaskTitle = forceState;
        } else {
            isEditingTaskTitle = !isEditingTaskTitle;
        }
        if (isEditingTaskTitle) {
            activeModal = null;
            isEditingDeadline = false;
            isEditingEstimate = false;
        }
        render();
        if (isEditingTaskTitle) {
            const input = document.getElementById('pw-edit-task-title-input');
            if (input) {
                input.focus();
                input.select();
            }
        }
    }

    function openEditTaskModal(taskId) {
        if (taskId) selectedTaskId = taskId;
        toggleTaskTitleEdit(true);
    }

    function saveTaskTitleEdit(taskId) {
        const input = document.getElementById('pw-edit-task-title-input');
        const newName = input ? input.value.trim() : '';
        if (!newName) {
            alert(isViLocale() ? 'Tên task không được để trống.' : 'Task name cannot be empty.');
            return;
        }
        updateTaskName(taskId, newName);
        isEditingTaskTitle = false;
        render();
    }

    function openBreakTaskModal(taskId) {
        activeModal = null;
        isEditingDeadline = false;
        isEditingEstimate = false;
        isEditingTaskTitle = false;
        const targetId = taskId || selectedTaskId;
        if (!targetId) return;
        if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.renderBreakTaskPopup === 'function') {
            window.TempoUrmodeFlow.renderBreakTaskPopup(targetId, 'plan-workspace');
        } else if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.startBreakTaskFlow === 'function') {
            window.TempoUrmodeFlow.startBreakTaskFlow(targetId);
        } else if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.reviewStepBreakdown === 'function') {
            window.TempoEmergencyFlow.reviewStepBreakdown(targetId);
        }
    }"""
assert old_break_task in content, "Failed to match old_break_task"
content = content.replace(old_break_task, new_break_task, 1)

# 6. Update openNoteEditor
old_note_editor = """    function openNoteEditor(taskId) {
        pendingNoteTaskId = taskId || selectedTaskId;
        activeModal = 'edit-task-note';
        render();
    }"""
new_note_editor = """    function openNoteEditor(taskId) {
        const targetId = taskId || selectedTaskId;
        if (!targetId) return;
        if (taskId) selectedTaskId = taskId;
        isEditingDeadline = false;
        isEditingEstimate = false;
        isEditingTaskTitle = false;
        pendingNoteTaskId = targetId;
        activeModal = 'edit-task-note';
        render();
    }"""
assert old_note_editor in content, "Failed to match old_note_editor"
content = content.replace(old_note_editor, new_note_editor, 1)

# 7. Update toggleEstimateEdit & openEstimateEdit
old_estimate_fns = """    function toggleEstimateEdit() {
        isEditingEstimate = !isEditingEstimate;
        render();
    }

    function openEstimateEdit(taskId) {
        if (taskId) selectedTaskId = taskId;
        isEditingEstimate = true;
        render();
    }"""
new_estimate_fns = """    function toggleEstimateEdit(forceState) {
        if (typeof forceState === 'boolean') {
            isEditingEstimate = forceState;
        } else {
            isEditingEstimate = !isEditingEstimate;
        }
        if (isEditingEstimate) {
            activeModal = null;
            isEditingDeadline = false;
            isEditingTaskTitle = false;
        }
        render();
    }

    function openEstimateEdit(taskId) {
        if (taskId) selectedTaskId = taskId;
        toggleEstimateEdit(true);
    }"""
assert old_estimate_fns in content, "Failed to match old_estimate_fns"
content = content.replace(old_estimate_fns, new_estimate_fns, 1)

# 8. Update promptClearTask
old_prompt_clear = """    function promptClearTask(taskId) {
        pendingClearTaskId = taskId || selectedTaskId;
        activeModal = 'clear-task-confirm';
        render();
    }"""
new_prompt_clear = """    function promptClearTask(taskId) {
        pendingClearTaskId = taskId || selectedTaskId;
        if (taskId) selectedTaskId = taskId;
        isEditingDeadline = false;
        isEditingEstimate = false;
        isEditingTaskTitle = false;
        activeModal = 'clear-task-confirm';
        render();
    }"""
assert old_prompt_clear in content, "Failed to match old_prompt_clear"
content = content.replace(old_prompt_clear, new_prompt_clear, 1)

# 9. Update openRescheduleModal
old_open_resched = """    function openRescheduleModal(taskId) {
        rescheduleTaskId = taskId;
        selectedTaskId = taskId;
        rescheduleSelectedWindow = null;
        rescheduleSelectedSlot = null;
        rescheduleShowAddTime = false;
        activeModal = 'reschedule';"""
new_open_resched = """    function openRescheduleModal(taskId) {
        rescheduleTaskId = taskId;
        selectedTaskId = taskId;
        rescheduleSelectedWindow = null;
        rescheduleSelectedSlot = null;
        rescheduleShowAddTime = false;
        isEditingDeadline = false;
        isEditingEstimate = false;
        isEditingTaskTitle = false;
        activeModal = 'reschedule';"""
assert old_open_resched in content, "Failed to match old_open_resched"
content = content.replace(old_open_resched, new_open_resched, 1)

# 10. Update openAddTaskModal
old_open_add_task = """    function openAddTaskModal() {
        activeModal = 'add-task';
        pendingAddedTask = null;
        render();
    }"""
new_open_add_task = """    function openAddTaskModal() {
        isEditingDeadline = false;
        isEditingEstimate = false;
        isEditingTaskTitle = false;
        activeModal = 'add-task';
        pendingAddedTask = null;
        render();
    }"""
assert old_open_add_task in content, "Failed to match old_open_add_task"
content = content.replace(old_open_add_task, new_open_add_task, 1)

# 11. Update openAdjustAvailabilityModal & Add openAddAvailableTimeModal + submitAddAvailableTime
old_adjust_avail_block = """    function openAdjustAvailabilityModal() {
        const plan = getActivePlan();
        if (plan) {
            const c2 = applyRecurringRulesToPlan(plan);
            const c1 = cleanupExpiredAvailability(plan);
            if (c1 || c2) {
                persistPlan(plan);
            }
        }
        activeModal = 'adjust-availability';
        adjustAvailShowAdd = false;
        render();
    }

    function closeAdjustAvailabilityModal() {
        activeModal = null;
        render();
    }"""

new_adjust_avail_block = """    function openAdjustAvailabilityModal() {
        const plan = getActivePlan();
        if (plan) {
            const c2 = applyRecurringRulesToPlan(plan);
            const c1 = cleanupExpiredAvailability(plan);
            if (c1 || c2) {
                persistPlan(plan);
            }
        }
        isEditingDeadline = false;
        isEditingEstimate = false;
        isEditingTaskTitle = false;
        activeModal = 'adjust-availability';
        adjustAvailShowAdd = false;
        render();
    }

    function closeAdjustAvailabilityModal() {
        activeModal = null;
        render();
    }

    function openAddAvailableTimeModal() {
        const plan = getActivePlan();
        if (plan) {
            const c2 = applyRecurringRulesToPlan(plan);
            const c1 = cleanupExpiredAvailability(plan);
            if (c1 || c2) {
                persistPlan(plan);
            }
        }
        isEditingDeadline = false;
        isEditingEstimate = false;
        isEditingTaskTitle = false;
        activeModal = 'add-available-time';
        render();
    }

    function closeAddAvailableTimeModal() {
        activeModal = null;
        render();
    }

    function submitAddAvailableTime() {
        const dateInput = document.getElementById('pw-add-avail-date');
        const startInput = document.getElementById('pw-add-avail-start');
        const endInput = document.getElementById('pw-add-avail-end');
        const repeatCb = document.getElementById('pw-add-avail-repeat');
        const errEl = document.getElementById('pw-add-avail-error');

        function showError(msg) {
            if (errEl) {
                errEl.textContent = msg;
                errEl.classList.remove('hidden');
            } else {
                alert(msg);
            }
        }

        const date = dateInput ? dateInput.value : '';
        const start = startInput ? startInput.value : '';
        const end = endInput ? endInput.value : '';
        const isRepeat = repeatCb ? repeatCb.checked : false;

        if (!date || !start || !end) {
            showError(isViLocale() ? 'Vui lòng chọn ngày, giờ bắt đầu và giờ kết thúc.' : 'Please select date, start time, and end time.');
            return;
        }

        const todayStr = getLocalTodayISO();
        if (date < todayStr) {
            showError(isViLocale() ? 'Không thể thêm thời gian làm việc cho ngày đã qua.' : 'Cannot add availability for a past date.');
            return;
        }

        const startMin = parseTimeToMinutes(start);
        const endMin = parseTimeToMinutes(end);
        if (endMin <= startMin) {
            showError(isViLocale() ? 'Giờ kết thúc phải sau giờ bắt đầu.' : 'End time must be after start time.');
            return;
        }

        if (date === todayStr) {
            const curTimeStr = getLocalCurrentTimeStr();
            const curMin = parseTimeToMinutes(curTimeStr);
            if (endMin <= curMin) {
                showError(isViLocale() ? 'Khung giờ này đã trôi qua hôm nay. Vui lòng chọn khung giờ trong tương lai.' : 'This time block has already passed for today. Please select a future time.');
                return;
            }
        }

        const plan = getActivePlan();
        if (!plan) return;

        if (!plan.availabilityDays) plan.availabilityDays = [];
        let day = plan.availabilityDays.find(d => d.date === date);
        if (!day) {
            day = {
                date: date,
                label: formatScheduledDateLabel(date, isViLocale()) || date,
                isUnavailable: false,
                blocks: []
            };
            plan.availabilityDays.push(day);
            plan.availabilityDays.sort((a, b) => a.date.localeCompare(b.date));
        }

        if (!Array.isArray(day.blocks)) day.blocks = [];
        day.blocks.push({
            id: 'b_' + Date.now(),
            start: start,
            end: end
        });

        if (isRepeat) {
            saveRecurringRule(date, true, date, '');
        }

        reorganizePlanWithPlanner(plan);
        const curUid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') ? window.TempoAuth.getCurrentUserId() : null;
        localStorage.setItem(getAvailabilityDaysStorageKey(), JSON.stringify(plan.availabilityDays));
        if (!curUid || curUid === 'guest') {
            localStorage.setItem('tempo_availability_days', JSON.stringify(plan.availabilityDays));
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setAvailabilityDays === 'function') {
            window.TempoEmergencyFlow.setAvailabilityDays(plan.availabilityDays);
        }
        persistPlan(plan);

        activeModal = null;
        render();

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(isViLocale() ? 'Đã thêm thời gian làm việc thành công.' : 'Available time added successfully.');
        }
    }"""
assert old_adjust_avail_block in content, "Failed to match old_adjust_avail_block"
content = content.replace(old_adjust_avail_block, new_adjust_avail_block, 1)

# 12. Update Header buttons
old_header_btns = """                    <!-- Header Plan Action CTAs -->
                    <div class="flex flex-wrap items-center gap-2 sm:gap-2.5 shrink-0 justify-center">
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.openAddTaskModal()"
                                class="px-3.5 sm:px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#92A491] hover:bg-[#829381] shadow-2xs transition cursor-pointer">
                            ${isViLocale() ? 'Thêm task' : 'Add task'}
                        </button>
                        <button type="button"
                                id="btn-edit-working-hours"
                                onclick="window.TempoPlanWorkspace.openAdjustAvailabilityModal()"
                                class="px-3.5 sm:px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#8AA8B7] hover:bg-[#7A98A7] shadow-2xs transition cursor-pointer">
                            ${isViLocale() ? 'Chỉnh sửa giờ làm việc' : 'Edit Working Hours'}
                        </button>
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.startAdjustPlan()"
                                class="px-3.5 sm:px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#D99E87] hover:bg-[#C98E77] shadow-2xs transition cursor-pointer">
                            ${isViLocale() ? 'Điều chỉnh plan' : 'Adjust Plan'}
                        </button>
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.promptDeletePlan()"
                                class="px-3.5 sm:px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#C53B27] hover:bg-[#B03422] shadow-2xs transition cursor-pointer">
                            ${isViLocale() ? 'Xóa plan' : 'Delete my plan'}
                        </button>
                    </div>"""

new_header_btns = """                    <!-- Header Plan Action CTAs -->
                    <div class="flex flex-wrap items-center gap-2 sm:gap-2.5 shrink-0 justify-center">
                        <button type="button"
                                id="btn-create-new-task"
                                onclick="window.TempoPlanWorkspace.openAddTaskModal()"
                                class="px-3.5 sm:px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#92A491] hover:bg-[#829381] shadow-2xs transition cursor-pointer"
                                data-action="create-new-task">
                            ${isViLocale() ? '+ Tạo task mới' : '+ Create a new task'}
                        </button>
                        <button type="button"
                                id="btn-add-available-time"
                                onclick="window.TempoPlanWorkspace.openAddAvailableTimeModal()"
                                class="px-3.5 sm:px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#D99E87] hover:bg-[#C98E77] shadow-2xs transition cursor-pointer"
                                data-action="add-available-time">
                            ${isViLocale() ? '+ Thêm thời gian làm việc' : '+ Add Available Time'}
                        </button>
                        <button type="button"
                                id="btn-edit-working-hours"
                                onclick="window.TempoPlanWorkspace.openAdjustAvailabilityModal()"
                                class="px-3.5 sm:px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#8AA8B7] hover:bg-[#7A98A7] shadow-2xs transition cursor-pointer"
                                data-action="edit-working-hours">
                            ${isViLocale() ? 'Chỉnh sửa giờ làm việc' : 'Edit Working Hours'}
                        </button>
                        <button type="button"
                                id="btn-adjust-plan"
                                onclick="window.TempoPlanWorkspace.startAdjustPlan()"
                                class="px-3.5 sm:px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#A38A7E] hover:bg-[#937A6E] shadow-2xs transition cursor-pointer">
                            ${isViLocale() ? 'Điều chỉnh plan' : 'Adjust Plan'}
                        </button>
                        <button type="button"
                                id="btn-delete-plan"
                                onclick="window.TempoPlanWorkspace.promptDeletePlan()"
                                class="px-3.5 sm:px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#C53B27] hover:bg-[#B03422] shadow-2xs transition cursor-pointer">
                            ${isViLocale() ? 'Xóa plan' : 'Delete my plan'}
                        </button>
                    </div>"""
assert old_header_btns in content, "Failed to match old_header_btns"
content = content.replace(old_header_btns, new_header_btns, 1)

# 13. Update Quick Working Hours row
old_quick_row = """                        <!-- Working Hours Summary & Quick Edit Row -->
                        <div class="flex items-center justify-between p-3 bg-white/80 border border-[#E3C7A5] rounded-2xl mb-4 text-xs shadow-2xs">
                            <div class="flex items-center space-x-2 text-[#4A4540]">
                                <span class="font-bold uppercase tracking-wider text-[#D9A18B]">⏰ ${isViLocale() ? 'Giờ làm việc' : 'Working Hours'}:</span>
                                <span class="font-semibold text-stone-700">${(plan.availabilityDays || []).filter(d => !d.isUnavailable && d.blocks && d.blocks.length > 0).length} ${isViLocale() ? 'ngày có lịch làm việc' : 'scheduled days'}</span>
                            </div>
                            <button type="button"
                                    id="pw-btn-quick-edit-hours"
                                    onclick="window.TempoPlanWorkspace.openAdjustAvailabilityModal()"
                                    class="text-[#D99E87] hover:text-[#C98E77] font-bold hover:underline flex items-center space-x-1 cursor-pointer">
                                <span>✎</span>
                                <span>${isViLocale() ? 'Chỉnh sửa giờ làm việc' : 'Edit Working Hours'}</span>
                            </button>
                        </div>"""

new_quick_row = """                        <!-- Working Hours Summary & Quick Actions Row -->
                        <div class="flex flex-wrap items-center justify-between gap-2 p-3 bg-white/80 border border-[#E3C7A5] rounded-2xl mb-4 text-xs shadow-2xs">
                            <div class="flex items-center space-x-2 text-[#4A4540]">
                                <span class="font-bold uppercase tracking-wider text-[#D9A18B]">⏰ ${isViLocale() ? 'Giờ làm việc' : 'Working Hours'}:</span>
                                <span class="font-semibold text-stone-700">${(plan.availabilityDays || []).filter(d => !d.isUnavailable && d.blocks && d.blocks.length > 0).length} ${isViLocale() ? 'ngày có lịch làm việc' : 'scheduled days'}</span>
                            </div>
                            <div class="flex items-center space-x-2.5">
                                <button type="button"
                                        id="pw-btn-quick-add-time"
                                        onclick="window.TempoPlanWorkspace.openAddAvailableTimeModal()"
                                        class="text-[#D99E87] hover:text-[#C98E77] font-bold hover:underline flex items-center space-x-1 cursor-pointer"
                                        data-action="add-available-time">
                                    <span>+</span>
                                    <span>${isViLocale() ? 'Thêm thời gian làm việc' : 'Add Available Time'}</span>
                                </button>
                                <span class="text-stone-300">|</span>
                                <button type="button"
                                        id="pw-btn-quick-edit-hours"
                                        onclick="window.TempoPlanWorkspace.openAdjustAvailabilityModal()"
                                        class="text-[#8AA8B7] hover:text-[#7A98A7] font-bold hover:underline flex items-center space-x-1 cursor-pointer"
                                        data-action="edit-working-hours">
                                    <span>✎</span>
                                    <span>${isViLocale() ? 'Chỉnh sửa giờ làm việc' : 'Edit Working Hours'}</span>
                                </button>
                            </div>
                        </div>"""
assert old_quick_row in content, "Failed to match old_quick_row"
content = content.replace(old_quick_row, new_quick_row, 1)

# 14. Update Selected Task Details Title & Action Buttons
old_selected_title = """                                <!-- Title and Badge -->
                                <div class="flex items-center justify-between gap-3 pb-1">
                                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] ${selectedTask.completed ? 'line-through text-stone-400' : ''}">
                                        ${escapeHTML(selectedTask.name)}
                                    </h2>
                                    <!-- Status Badge with Interactive Dropdown -->"""

new_selected_title = """                                <!-- Title and Badge -->
                                <div class="flex items-center justify-between gap-3 pb-1">
                                    ${isEditingTaskTitle ? `
                                        <div class="flex items-center gap-2 flex-1 min-w-0">
                                            <input id="pw-edit-task-title-input"
                                                   type="text"
                                                   value="${escapeHTML(selectedTask.name || '')}"
                                                   class="w-full px-3 py-1.5 text-base font-bold text-[#202124] border border-[#D99E87] rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-[#D99E87]"
                                                   onkeydown="if(event.key==='Enter') window.TempoPlanWorkspace.saveTaskTitleEdit('${selectedTask.id}'); if(event.key==='Escape') window.TempoPlanWorkspace.toggleTaskTitleEdit();" />
                                            <button type="button"
                                                    id="pw-btn-save-task-title"
                                                    onclick="window.TempoPlanWorkspace.saveTaskTitleEdit('${selectedTask.id}')"
                                                    class="px-3 py-1.5 bg-[#D99E87] text-white rounded-xl text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                                ${isViLocale() ? 'Lưu' : 'Save'}
                                            </button>
                                            <button type="button"
                                                    id="pw-btn-cancel-task-title"
                                                    onclick="window.TempoPlanWorkspace.toggleTaskTitleEdit()"
                                                    class="px-2.5 py-1.5 border border-stone-300 text-stone-600 rounded-xl text-xs font-bold hover:bg-stone-100 cursor-pointer">
                                                ${isViLocale() ? 'Hủy' : 'Cancel'}
                                            </button>
                                        </div>
                                    ` : `
                                        <div class="flex items-center gap-2 group flex-1 min-w-0">
                                            <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] truncate ${selectedTask.completed ? 'line-through text-stone-400' : ''}">
                                                ${escapeHTML(selectedTask.name)}
                                            </h2>
                                            <button type="button"
                                                    id="pw-btn-edit-task"
                                                    onclick="window.TempoPlanWorkspace.toggleTaskTitleEdit()"
                                                    class="text-[#D99E87] hover:text-[#C98E77] text-xs font-semibold p-1 hover:bg-[#F3EDE2] rounded-md transition cursor-pointer inline-flex items-center space-x-1"
                                                    title="${isViLocale() ? 'Chỉnh sửa task' : 'Edit task'}"
                                                    data-action="edit-task">
                                                <span>✎</span>
                                                <span class="text-[11px] font-bold">${isViLocale() ? 'Sửa task' : 'Edit task'}</span>
                                            </button>
                                        </div>
                                    `}
                                    <!-- Status Badge with Interactive Dropdown -->"""
assert old_selected_title in content, "Failed to match old_selected_title"
content = content.replace(old_selected_title, new_selected_title, 1)

# 15. Update Selected Task Deadline button
old_deadline_btn = """                                    <button type="button"
                                            onclick="window.TempoPlanWorkspace.toggleDeadlineEdit()"
                                            class="text-[#D99E87] font-semibold hover:underline cursor-pointer">
                                        ${isEditingDeadline ? (isViLocale() ? 'Hủy' : 'Cancel') : (isViLocale() ? 'Sửa deadline' : 'Edit deadline')}
                                    </button>"""
new_deadline_btn = """                                    <button type="button"
                                            id="pw-btn-edit-deadline"
                                            onclick="window.TempoPlanWorkspace.toggleDeadlineEdit()"
                                            class="text-[#D99E87] font-semibold hover:underline cursor-pointer"
                                            data-action="edit-deadline">
                                        ${isEditingDeadline ? (isViLocale() ? 'Hủy' : 'Cancel') : (isViLocale() ? 'Sửa deadline' : 'Edit deadline')}
                                    </button>"""
assert old_deadline_btn in content, "Failed to match old_deadline_btn"
content = content.replace(old_deadline_btn, new_deadline_btn, 1)

# 16. Update Selected Task Subtask button
old_subtask_btn = """                                    <button type="button"
                                            onclick="window.TempoPlanWorkspace.openBreakTaskModal('${selectedTask.id}')"
                                            class="text-[#D99E87] font-semibold hover:underline cursor-pointer">
                                        ${isViLocale() ? (selectedSubtaskCount > 0 ? 'Chia nhỏ task' : '+ Chia nhỏ task') : (selectedSubtaskCount > 0 ? 'Break down task' : '+ Break down task')}
                                    </button>"""
new_subtask_btn = """                                    <button type="button"
                                            id="pw-btn-add-subtask"
                                            onclick="window.TempoPlanWorkspace.openBreakTaskModal('${selectedTask.id}')"
                                            class="text-[#D99E87] font-semibold hover:underline cursor-pointer flex items-center space-x-1"
                                            data-action="add-subtask">
                                        <span>${isViLocale() ? (selectedSubtaskCount > 0 ? 'Chia nhỏ task' : '+ Chia nhỏ task') : (selectedSubtaskCount > 0 ? 'Break down task' : '+ Break down task')}</span>
                                    </button>"""
assert old_subtask_btn in content, "Failed to match old_subtask_btn"
content = content.replace(old_subtask_btn, new_subtask_btn, 1)

# 17. Update Selected Task Note buttons
old_note_btn1 = """                                        <button type="button"
                                                onclick="window.TempoPlanWorkspace.openNoteEditor('${selectedTask.id}')"
                                                class="text-[#D99E87] hover:text-[#C98E77] text-xs font-semibold shrink-0 cursor-pointer flex items-center space-x-1"
                                                title="${isViLocale() ? 'Chỉnh sửa ghi chú' : 'Edit note'}">
                                            <span>${isViLocale() ? 'Chỉnh sửa ghi chú' : 'Edit note'}</span>
                                            <span>✎</span>
                                        </button>"""
new_note_btn1 = """                                        <button type="button"
                                                id="pw-btn-add-note"
                                                onclick="window.TempoPlanWorkspace.openNoteEditor('${selectedTask.id}')"
                                                class="text-[#D99E87] hover:text-[#C98E77] text-xs font-semibold shrink-0 cursor-pointer flex items-center space-x-1"
                                                title="${isViLocale() ? 'Chỉnh sửa ghi chú' : 'Edit note'}"
                                                data-action="add-note">
                                            <span>${isViLocale() ? 'Chỉnh sửa ghi chú' : 'Edit note'}</span>
                                            <span>✎</span>
                                        </button>"""
assert old_note_btn1 in content, "Failed to match old_note_btn1"
content = content.replace(old_note_btn1, new_note_btn1, 1)

old_note_btn2 = """                                        <button type="button"
                                                onclick="window.TempoPlanWorkspace.openNoteEditor('${selectedTask.id}')"
                                                class="text-xs font-bold text-[#D9A18B] hover:underline cursor-pointer flex items-center space-x-1">
                                            <span>${isViLocale() ? '+ Thêm ghi chú' : '+ Add note'}</span>
                                        </button>"""
new_note_btn2 = """                                        <button type="button"
                                                id="pw-btn-add-note"
                                                onclick="window.TempoPlanWorkspace.openNoteEditor('${selectedTask.id}')"
                                                class="text-xs font-bold text-[#D9A18B] hover:underline cursor-pointer flex items-center space-x-1"
                                                data-action="add-note">
                                            <span>${isViLocale() ? '+ Thêm ghi chú' : '+ Add note'}</span>
                                        </button>"""
assert old_note_btn2 in content, "Failed to match old_note_btn2"
content = content.replace(old_note_btn2, new_note_btn2, 1)

# 18. Update Selected Task Reschedule & Delete buttons
old_resched_btn = """                                    <!-- 3. Reschedule -->
                                    <button type="button"
                                            onclick="window.TempoPlanWorkspace.openRescheduleModal('${selectedTask.id}')"
                                            class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#3A4B3D] bg-white border border-[#8D9B8A] hover:bg-stone-50 transition text-center cursor-pointer">
                                        ${isViLocale() ? 'Đổi lịch' : 'Reschedule'}
                                    </button>"""
new_resched_btn = """                                    <!-- 3. Reschedule -->
                                    <button type="button"
                                            id="pw-btn-reschedule-task"
                                            onclick="window.TempoPlanWorkspace.openRescheduleModal('${selectedTask.id}')"
                                            class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#3A4B3D] bg-white border border-[#8D9B8A] hover:bg-stone-50 transition text-center cursor-pointer"
                                            data-action="reschedule-task">
                                        ${isViLocale() ? 'Đổi lịch' : 'Reschedule'}
                                    </button>"""
assert old_resched_btn in content, "Failed to match old_resched_btn"
content = content.replace(old_resched_btn, new_resched_btn, 1)

old_clear_btn = """                                    <!-- 4. Clear this task -->
                                    <button type="button"
                                            onclick="window.TempoPlanWorkspace.promptClearTask('${selectedTask.id}')"
                                            class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#C53B27] bg-white border border-[#D99E87] hover:bg-rose-50/40 transition text-center cursor-pointer">
                                        ${isViLocale() ? 'Xóa task này' : 'Clear this task'}
                                    </button>"""
new_clear_btn = """                                    <!-- 4. Clear this task -->
                                    <button type="button"
                                            id="pw-btn-delete-task"
                                            onclick="window.TempoPlanWorkspace.promptClearTask('${selectedTask.id}')"
                                            class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#C53B27] bg-white border border-[#D99E87] hover:bg-rose-50/40 transition text-center cursor-pointer"
                                            data-action="delete-task">
                                        ${isViLocale() ? 'Xóa task này' : 'Clear this task'}
                                    </button>"""
assert old_clear_btn in content, "Failed to match old_clear_btn"
content = content.replace(old_clear_btn, new_clear_btn, 1)

# 19. Update renderModalsHTML to include add-available-time and backdrop clicks
old_add_task_modal_head = """                <div class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">"""
new_add_task_modal_head = """                <div id="add-task-modal" class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4" onclick="if (event.target === this) window.TempoPlanWorkspace.closeAddTaskModal();" role="dialog" aria-modal="true">"""
assert old_add_task_modal_head in content, "Failed to match old_add_task_modal_head"
content = content.replace(old_add_task_modal_head, new_add_task_modal_head, 1)

old_resched_modal_head = """                <div class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-md w-full">"""
new_resched_modal_head = """                <div id="reschedule-modal" class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4" onclick="if (event.target === this) window.TempoPlanWorkspace.closeRescheduleModal();" role="dialog" aria-modal="true">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-md w-full" onclick="event.stopPropagation();">"""
assert old_resched_modal_head in content, "Failed to match old_resched_modal_head"
content = content.replace(old_resched_modal_head, new_resched_modal_head, 1)

old_adjust_avail_modal_head = """                <div id="adjust-availability-modal" class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">"""
new_adjust_avail_modal_head = """                <div id="adjust-availability-modal" class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4" onclick="if (event.target === this) window.TempoPlanWorkspace.closeAdjustAvailabilityModal();" role="dialog" aria-modal="true">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto" onclick="event.stopPropagation();">"""
assert old_adjust_avail_modal_head in content, "Failed to match old_adjust_avail_modal_head"
content = content.replace(old_adjust_avail_modal_head, new_adjust_avail_modal_head, 1)

# Add add-available-time modal rendering before adjust-availability
add_avail_modal_code = """
        if (activeModal === 'add-available-time') {
            return `
                <div id="add-available-time-modal"
                     class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4"
                     onclick="if (event.target === this) window.TempoPlanWorkspace.closeAddAvailableTimeModal();"
                     role="dialog"
                     aria-modal="true"
                     aria-labelledby="add-avail-modal-title">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-md w-full"
                         onclick="event.stopPropagation();">
                        <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                            <div>
                                <h3 id="add-avail-modal-title" class="font-heading text-lg font-bold text-[#202124]">
                                    ${isViLocale() ? 'Thêm thời gian làm việc' : 'Add Available Time'}
                                </h3>
                                <p class="text-xs text-[#6F6B68] mt-0.5">
                                    ${isViLocale() ? 'Thêm một khung giờ làm việc mới để sắp xếp các task của bạn.' : 'Add a new available working window to organize your tasks.'}
                                </p>
                            </div>
                            <button type="button"
                                    onclick="window.TempoPlanWorkspace.closeAddAvailableTimeModal()"
                                    class="text-gray-400 hover:text-gray-600 text-sm cursor-pointer"
                                    aria-label="${isViLocale() ? 'Đóng' : 'Close'}">✕</button>
                        </div>

                        <!-- Validation Error Message Container -->
                        <div id="pw-add-avail-error" class="hidden text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-xl p-2.5 font-medium"></div>

                        <div class="space-y-3.5 text-xs">
                            <div>
                                <label class="block text-[11px] font-bold text-stone-700 uppercase tracking-wider mb-1">
                                    ${isViLocale() ? 'Ngày làm việc' : 'Date'}
                                </label>
                                <input id="pw-add-avail-date"
                                       type="date"
                                       value="${getLocalTodayISO()}"
                                       min="${getLocalTodayISO()}"
                                       class="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl bg-white focus:border-[#D99E87] focus:outline-none">
                            </div>

                            <div class="grid grid-cols-2 gap-3">
                                <div>
                                    <label class="block text-[11px] font-bold text-stone-700 uppercase tracking-wider mb-1">
                                        ${isViLocale() ? 'Giờ bắt đầu' : 'Start Time'}
                                    </label>
                                    <input id="pw-add-avail-start"
                                           type="time"
                                           value="18:00"
                                           class="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl bg-white focus:border-[#D99E87] focus:outline-none">
                                </div>
                                <div>
                                    <label class="block text-[11px] font-bold text-stone-700 uppercase tracking-wider mb-1">
                                        ${isViLocale() ? 'Giờ kết thúc' : 'End Time'}
                                    </label>
                                    <input id="pw-add-avail-end"
                                           type="time"
                                           value="21:00"
                                           class="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl bg-white focus:border-[#D99E87] focus:outline-none">
                                </div>
                            </div>

                            <div class="pt-1 flex items-center space-x-2">
                                <input id="pw-add-avail-repeat"
                                       type="checkbox"
                                       class="rounded text-[#D99E87] focus:ring-[#D99E87]">
                                <label for="pw-add-avail-repeat" class="text-xs text-stone-700 font-medium cursor-pointer">
                                    ${isViLocale() ? 'Lặp lại hàng tuần vào ngày này' : 'Repeat weekly on this day'}
                                </label>
                            </div>
                        </div>

                        <div class="pt-3 border-t border-gray-100 flex items-center justify-end space-x-2.5">
                            <button type="button"
                                    onclick="window.TempoPlanWorkspace.closeAddAvailableTimeModal()"
                                    class="px-4 py-2 rounded-xl font-semibold text-xs text-stone-600 hover:bg-stone-100 transition cursor-pointer">
                                ${isViLocale() ? 'Hủy' : 'Cancel'}
                            </button>
                            <button type="button"
                                    id="btn-submit-add-available-time"
                                    onclick="window.TempoPlanWorkspace.submitAddAvailableTime()"
                                    class="btn-primary px-6 py-2 rounded-xl font-bold text-xs bg-[#D99E87] hover:bg-[#C98E77] text-white shadow-sm transition cursor-pointer">
                                ${isViLocale() ? 'Thêm thời gian làm việc' : 'Add Available Time'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }
"""
old_render_adjust = """        if (activeModal === 'adjust-availability') {"""
assert old_render_adjust in content, "Failed to match old_render_adjust"
content = content.replace(old_render_adjust, add_avail_modal_code + "\n        if (activeModal === 'adjust-availability') {", 1)

# 20. Update keydown Escape handler
old_keydown = """    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (activeModal === 'clear-task-confirm') {
                closeClearTaskConfirm();
            } else if (activeModal === 'delete-plan-confirm') {
                closeDeletePlanConfirm();
            } else if (activeModal === 'deadline-plan-reorder-confirm') {
                cancelDeadlineConfirm();
            } else if (activeModal === 'edit-task-note') {
                closeModal();
            }
        }
    });"""

new_keydown = """    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (activeModal === 'add-available-time') {
                closeAddAvailableTimeModal();
            } else if (activeModal === 'adjust-availability') {
                closeAdjustAvailabilityModal();
            } else if (activeModal === 'add-task') {
                closeAddTaskModal();
            } else if (activeModal === 'reschedule') {
                closeRescheduleModal();
            } else if (activeModal === 'repeat-weekly-config') {
                closeRepeatWeeklyModal();
            } else if (activeModal === 'clear-task-confirm') {
                closeClearTaskConfirm();
            } else if (activeModal === 'delete-plan-confirm') {
                closeDeletePlanConfirm();
            } else if (activeModal === 'deadline-plan-reorder-confirm') {
                cancelDeadlineConfirm();
            } else if (activeModal === 'edit-task-note') {
                closeModal();
            } else if (isEditingTaskTitle) {
                toggleTaskTitleEdit(false);
            } else if (isEditingEstimate) {
                toggleEstimateEdit(false);
            } else if (isEditingDeadline) {
                toggleDeadlineEdit(false);
            }
        }
    });"""
assert old_keydown in content, "Failed to match old_keydown"
content = content.replace(old_keydown, new_keydown, 1)

# 21. Update resetWorkspaceState
old_reset_ws = """    function resetWorkspaceState() {
        selectedTaskId = null;
        pendingAddedTask = null;
        activeModal = null;
    }"""
new_reset_ws = """    function resetWorkspaceState() {
        selectedTaskId = null;
        pendingAddedTask = null;
        activeModal = null;
        isEditingDeadline = false;
        isEditingEstimate = false;
        isEditingTaskTitle = false;
        rescheduleTaskId = null;
        rescheduleSelectedWindow = null;
        rescheduleSelectedSlot = null;
        rescheduleShowAddTime = false;
        repeatConfigDate = null;
        pendingClearTaskId = null;
        pendingDeadlineChange = null;
        pendingNoteTaskId = null;
        noteTaskId = null;
    }"""
assert old_reset_ws in content, "Failed to match old_reset_ws"
content = content.replace(old_reset_ws, new_reset_ws, 1)

# 22. Update return exports
old_exports = """        openAdjustAvailabilityModal,
        closeAdjustAvailabilityModal,
        saveWorkingHoursChanges,"""

new_exports = """        openAdjustAvailabilityModal,
        closeAdjustAvailabilityModal,
        openAddAvailableTimeModal,
        closeAddAvailableTimeModal,
        submitAddAvailableTime,
        toggleTaskTitleEdit,
        openEditTaskModal,
        saveTaskTitleEdit,
        openDeadlineEdit,
        saveWorkingHoursChanges,"""
assert old_exports in content, "Failed to match old_exports"
content = content.replace(old_exports, new_exports, 1)

# Verify pure LF
content = content.replace('\r\n', '\n')

with open('planWorkspace.js', 'wb') as f:
    f.write(content.encode('utf-8'))

print("Updated planWorkspace.js successfully!")
