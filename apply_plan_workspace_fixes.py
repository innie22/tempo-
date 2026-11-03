import sys

with open('planWorkspace.js', 'rb') as f:
    content = f.read().decode('utf-8')

# Ensure LF line endings for planWorkspace.js
content = content.replace('\r\n', '\n')

# 1. Update getDefaultReferencePlan to include availabilityDays
old_def_plan = """        const defaultPlan = {
            id: 'plan_tempo_working_default',
            planId: 'plan_tempo_working_default',
            planType: 'emergency',
            title: 'Tempo Working Plan',
            plannedTasks: ["""

new_def_plan = """        const defaultPlan = {
            id: 'plan_tempo_working_default',
            planId: 'plan_tempo_working_default',
            planType: 'emergency',
            title: 'Tempo Working Plan',
            availabilityDays: [
                {
                    date: todayStr,
                    label: formatScheduledDateLabel(todayStr),
                    isUnavailable: false,
                    blocks: [
                        { id: 'b_today_1', start: '14:00', end: '18:00', minutes: 240 },
                        { id: 'b_today_2', start: '19:00', end: '23:00', minutes: 240 }
                    ]
                },
                {
                    date: tomorrowStr,
                    label: formatScheduledDateLabel(tomorrowStr),
                    isUnavailable: false,
                    blocks: [
                        { id: 'b_tom_1', start: '09:00', end: '12:00', minutes: 180 },
                        { id: 'b_tom_2', start: '14:00', end: '17:00', minutes: 180 }
                    ]
                }
            ],
            plannedTasks: ["""

if old_def_plan in content:
    content = content.replace(old_def_plan, new_def_plan)
    print("1. Added availabilityDays to getDefaultReferencePlan")
else:
    print("WARNING: old_def_plan not found")

# 2. Update getActivePlan & persistPlan
old_get_active = """    // Load active plan from TempoPlanStore, TempoEmergencyFlow, or local storage
    function getActivePlan() {
        let plan = null;
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            plan = window.TempoEmergencyFlow.getConfirmedPlan();
        }
        if (!plan && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            plan = window.TempoPlanStore.getActivePlan('emergency') || window.TempoPlanStore.getActivePlan('recovery') || window.TempoPlanStore.getActivePlan('default');
        }
        if (!plan) {
            try {
                const saved = localStorage.getItem('tempo_working_plan') || localStorage.getItem('tempo_store_active_emergency_guest');
                if (saved) plan = JSON.parse(saved);
            } catch(e) {}
        }
        if (plan) {
            if (!Array.isArray(plan.plannedTasks)) plan.plannedTasks = [];
            if (!Array.isArray(plan.unarrangedTasks)) plan.unarrangedTasks = [];
            if (!Array.isArray(plan.tasks)) plan.tasks = [];
        }
        if (!plan || (plan.plannedTasks.length === 0 && plan.unarrangedTasks.length === 0 && plan.tasks.length === 0)) {
            plan = getDefaultReferencePlan();
        }
        return plan;
    }

    // Save active plan to TempoPlanStore & localStorage
    async function persistPlan(plan) {
        if (!plan) return;
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
            window.TempoEmergencyFlow.setConfirmedPlan(plan);
        }
        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            try {
                await window.TempoPlanStore.saveActivePlan('emergency', plan);
                await window.TempoPlanStore.saveActivePlan('recovery', plan);
            } catch (err) {
                console.error('[TempoPlanWorkspace] Error saving plan to store:', err);
                throw err;
            }
        }
        try {
            localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
        } catch(e) {}
        if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
            window.TempoMode.renderActiveModeHome();
        }
    }"""

new_get_active = """    // Load active plan from TempoPlanStore, TempoEmergencyFlow, or local storage
    function getActivePlan() {
        let plan = null;
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            plan = window.TempoEmergencyFlow.getConfirmedPlan();
        }
        if (!plan && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            plan = window.TempoPlanStore.getActivePlan('emergency') || window.TempoPlanStore.getActivePlan('recovery') || window.TempoPlanStore.getActivePlan('default');
        }
        if (!plan) {
            try {
                const saved = localStorage.getItem('tempo_working_plan') || localStorage.getItem('tempo_store_active_emergency_guest');
                if (saved) plan = JSON.parse(saved);
            } catch(e) {}
        }
        if (plan) {
            if (!Array.isArray(plan.plannedTasks)) plan.plannedTasks = [];
            if (!Array.isArray(plan.unarrangedTasks)) plan.unarrangedTasks = [];
            if (!Array.isArray(plan.tasks)) plan.tasks = [];
        }
        if (!plan || (plan.plannedTasks.length === 0 && plan.unarrangedTasks.length === 0 && plan.tasks.length === 0)) {
            plan = getDefaultReferencePlan();
        }

        // CRUCIAL: Ensure plan.availabilityDays is populated & synchronized
        if (!Array.isArray(plan.availabilityDays) || plan.availabilityDays.length === 0) {
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getAvailabilityDays === 'function') {
                const efAvail = window.TempoEmergencyFlow.getAvailabilityDays();
                if (Array.isArray(efAvail) && efAvail.length > 0) {
                    plan.availabilityDays = JSON.parse(JSON.stringify(efAvail));
                }
            }
            if (!Array.isArray(plan.availabilityDays) || plan.availabilityDays.length === 0) {
                try {
                    const savedAvail = localStorage.getItem('tempo_availability_days');
                    if (savedAvail) plan.availabilityDays = JSON.parse(savedAvail);
                } catch(e) {}
            }
            if (!Array.isArray(plan.availabilityDays) || plan.availabilityDays.length === 0) {
                const todayStr = getLocalTodayISO();
                const tomorrowStr = getLocalTomorrowISO();
                plan.availabilityDays = [
                    {
                        date: todayStr,
                        label: formatScheduledDateLabel(todayStr),
                        isUnavailable: false,
                        blocks: [
                            { id: 'b_today_1', start: '14:00', end: '18:00', minutes: 240 },
                            { id: 'b_today_2', start: '19:00', end: '23:00', minutes: 240 }
                        ]
                    },
                    {
                        date: tomorrowStr,
                        label: formatScheduledDateLabel(tomorrowStr),
                        isUnavailable: false,
                        blocks: [
                            { id: 'b_tom_1', start: '09:00', end: '12:00', minutes: 180 },
                            { id: 'b_tom_2', start: '14:00', end: '17:00', minutes: 180 }
                        ]
                    }
                ];
            }
        }
        return plan;
    }

    // Save active plan to TempoPlanStore & localStorage
    async function persistPlan(plan) {
        if (!plan) return;

        // Ensure availabilityDays is saved in plan, localStorage, and emergencyFlow
        if (Array.isArray(plan.availabilityDays) && plan.availabilityDays.length > 0) {
            try {
                localStorage.setItem('tempo_availability_days', JSON.stringify(plan.availabilityDays));
            } catch(e) {}
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setAvailabilityDays === 'function') {
                window.TempoEmergencyFlow.setAvailabilityDays(plan.availabilityDays);
            }
        }

        // Save to localStorage FIRST so data is never lost even if remote fails
        try {
            localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
        } catch(e) {}

        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
            window.TempoEmergencyFlow.setConfirmedPlan(plan);
        }
        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            try {
                await window.TempoPlanStore.saveActivePlan('emergency', plan);
                await window.TempoPlanStore.saveActivePlan('recovery', plan);
            } catch (err) {
                console.error('[TempoPlanWorkspace] Error saving plan to store:', err);
            }
        }
        if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
            window.TempoMode.renderActiveModeHome();
        }
    }"""

if old_get_active in content:
    content = content.replace(old_get_active, new_get_active)
    print("2. Updated getActivePlan and persistPlan")
else:
    print("WARNING: old_get_active not found")

# 3. In reorganizePlanWithPlanner
old_reorg_avail = """        // Sequential slot allocation based on available days
        let availabilityDays = null;
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getAvailabilityDays === 'function') {
            availabilityDays = window.TempoEmergencyFlow.getAvailabilityDays();
        }
        const activeDays = (availabilityDays || []).filter(d => !d.isUnavailable && d.blocks && d.blocks.length > 0);"""

new_reorg_avail = """        // Sequential slot allocation based on available days
        let availabilityDays = (plan && Array.isArray(plan.availabilityDays) && plan.availabilityDays.length > 0)
            ? plan.availabilityDays
            : ((window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getAvailabilityDays === 'function')
                ? window.TempoEmergencyFlow.getAvailabilityDays()
                : []);
        const activeDays = (availabilityDays || []).filter(d => !d.isUnavailable && d.blocks && d.blocks.length > 0);"""

if old_reorg_avail in content:
    content = content.replace(old_reorg_avail, new_reorg_avail)
    print("3. Updated reorganizePlanWithPlanner availabilityDays lookup")

old_reorg_fallback = """                if (!allocated) {
                    const fallbackDay = activeDays[activeDays.length - 1] || activeDays[0];
                    item.dayDate = fallbackDay ? fallbackDay.date : item.dayDate;
                    item.dayLabel = fallbackDay ? fallbackDay.label : item.dayLabel;
                    item.executionBadge = task.userLabel === 'Now' ? 'Now' : 'Later';
                }"""

new_reorg_fallback = """                if (!allocated) {
                    const fallbackDay = activeDays[activeDays.length - 1] || activeDays[0];
                    item.dayDate = item.dayDate || (fallbackDay ? fallbackDay.date : null);
                    item.dayLabel = item.dayLabel || (fallbackDay ? fallbackDay.label : null);
                    item.executionBadge = task.userLabel === 'Now' ? 'Now' : 'Later';
                }"""

if old_reorg_fallback in content:
    content = content.replace(old_reorg_fallback, new_reorg_fallback)
    print("3b. Updated fallbackDay allocation to preserve existing dayDate")

# 4. In openRescheduleModal & selectRescheduleSlot
old_open_resched = """    function openRescheduleModal(taskId) {
        rescheduleTaskId = taskId;
        selectedTaskId = taskId;
        rescheduleSelectedWindow = null;
        rescheduleSelectedSlot = null;
        rescheduleShowAddTime = false;
        activeModal = 'reschedule';
        render();
    }"""

new_open_resched = """    function openRescheduleModal(taskId) {
        rescheduleTaskId = taskId;
        selectedTaskId = taskId;
        rescheduleSelectedWindow = null;
        rescheduleSelectedSlot = null;
        rescheduleShowAddTime = false;
        activeModal = 'reschedule';

        const plan = getActivePlan();
        if (plan) {
            let taskItem = (plan.plannedTasks || []).find(pt => pt.task && (pt.task.id === taskId || pt.id === taskId));
            const tDate = taskItem ? taskItem.dayDate : null;
            const tStart = taskItem ? (taskItem.startTime || taskItem.scheduledStartTime) : null;
            const tEnd = taskItem ? (taskItem.endTime || taskItem.scheduledEndTime) : null;
            if (tDate) {
                rescheduleSelectedWindow = tDate;
                rescheduleSelectedSlot = {
                    id: `slot_${tDate}`,
                    date: tDate,
                    start: tStart,
                    end: tEnd
                };
            }
        }
        render();
    }"""

if old_open_resched in content:
    content = content.replace(old_open_resched, new_open_resched)
    print("4. Updated openRescheduleModal to pre-select task's scheduled slot")

old_select_slot = """    function selectRescheduleSlot(date, slotId, start, end) {
        rescheduleSelectedSlot = {
            id: slotId,
            date: date,
            start: start || null,
            end: end || null
        };
        rescheduleSelectedWindow = date;
    }"""

new_select_slot = """    function selectRescheduleSlot(date, slotId, start, end) {
        rescheduleSelectedSlot = {
            id: slotId,
            date: date,
            start: start || null,
            end: end || null
        };
        rescheduleSelectedWindow = date;

        // Visually update radios and labels without destroying the DOM
        const labels = document.querySelectorAll('label[data-reschedule-slot-label]');
        labels.forEach(lbl => {
            const radio = lbl.querySelector('input[type="radio"]');
            if (!radio) return;
            const rSlotId = radio.getAttribute('data-slot-id');
            const rDate = radio.getAttribute('data-date');
            const isMatch = (slotId && rSlotId === slotId) || (!slotId && rDate === date);
            radio.checked = isMatch;
            if (isMatch) {
                lbl.className = 'p-3 rounded-xl border border-[#FF6B2C] bg-orange-50/40 ring-1 ring-[#FF6B2C]/30 transition flex items-center space-x-3 cursor-pointer';
            } else {
                lbl.className = 'p-3 rounded-xl border border-gray-200 hover:border-[#FF6B2C] bg-white hover:bg-orange-50/20 transition flex items-center space-x-3 cursor-pointer';
            }
        });
    }"""

if old_select_slot in content:
    content = content.replace(old_select_slot, new_select_slot)
    print("4b. Updated selectRescheduleSlot for clean UI sync")

# 5. In saveRescheduleAvailability: make async & await persistPlan
old_save_avail = """    function saveRescheduleAvailability() {"""
new_save_avail = """    async function saveRescheduleAvailability() {"""
content = content.replace(old_save_avail, new_save_avail, 1)

old_save_persist = """        // Save Availability
        persistPlan(plan);"""
new_save_persist = """        // Save Availability
        await persistPlan(plan);"""
content = content.replace(old_save_persist, new_save_persist, 1)
print("5. Made saveRescheduleAvailability async and await persistPlan")

# 6. In executeReschedule: preserve taskStart and taskEnd
old_exec_sync = """            // 3. Sync with TempoEmergencyFlow
            if (window.TempoEmergencyFlow) {
                if (typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                    window.TempoEmergencyFlow.setConfirmedPlan(plan);
                }
                if (typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
                    window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
                }
            }"""

new_exec_sync = """            // 3. Sync with TempoEmergencyFlow
            if (window.TempoEmergencyFlow) {
                if (typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                    window.TempoEmergencyFlow.setConfirmedPlan(plan);
                }
                if (typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
                    window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
                }
            }

            // Guarantee explicit scheduled times are preserved
            if (taskStart && taskEnd) {
                newPlannedItem.startTime = taskStart;
                newPlannedItem.endTime = taskEnd;
                newPlannedItem.scheduledStartTime = taskStart;
                newPlannedItem.scheduledEndTime = taskEnd;
                if (task) {
                    task.startTime = taskStart;
                    task.endTime = taskEnd;
                    task.scheduledStartTime = taskStart;
                    task.scheduledEndTime = taskEnd;
                }
            }"""

if old_exec_sync in content:
    content = content.replace(old_exec_sync, new_exec_sync)
    print("6. Updated executeReschedule to guarantee explicit scheduled times are preserved")

# 7. In Reschedule Modal render HTML:
old_modal_selection = """            // Default selection if not already set or if previous selection is no longer valid
            if (!rescheduleSelectedSlot && availableSlots.length > 0) {
                rescheduleSelectedSlot = availableSlots[0];
                rescheduleSelectedWindow = availableSlots[0].date;
            } else if (rescheduleSelectedSlot) {
                const match = availableSlots.find(s => s.id === rescheduleSelectedSlot.id || (s.date === rescheduleSelectedSlot.date && (!rescheduleSelectedSlot.start || s.start === rescheduleSelectedSlot.start)));
                if (match) {
                    rescheduleSelectedSlot = match;
                    rescheduleSelectedWindow = match.date;
                } else if (availableSlots.length > 0) {
                    rescheduleSelectedSlot = availableSlots[0];
                    rescheduleSelectedWindow = availableSlots[0].date;
                } else {
                    rescheduleSelectedSlot = null;
                    rescheduleSelectedWindow = null;
                }
            }"""

new_modal_selection = """            // Default selection if not already set or match against task scheduled date
            if (!rescheduleSelectedSlot && availableSlots.length > 0) {
                const taskScheduledDate = pt ? pt.dayDate : (task.scheduledDate || task.dayDate);
                const taskStartTime = pt ? (pt.startTime || pt.scheduledStartTime) : (task.startTime || task.scheduledStartTime);
                const match = availableSlots.find(s => s.date === taskScheduledDate && (!taskStartTime || s.start === taskStartTime))
                           || availableSlots.find(s => s.date === taskScheduledDate)
                           || availableSlots[0];
                rescheduleSelectedSlot = match;
                rescheduleSelectedWindow = match.date;
            } else if (rescheduleSelectedSlot) {
                const match = availableSlots.find(s => s.id === rescheduleSelectedSlot.id)
                           || availableSlots.find(s => s.date === rescheduleSelectedSlot.date && (!rescheduleSelectedSlot.start || s.start === rescheduleSelectedSlot.start))
                           || availableSlots.find(s => s.date === rescheduleSelectedSlot.date)
                           || availableSlots[0];
                if (match) {
                    rescheduleSelectedSlot = match;
                    rescheduleSelectedWindow = match.date;
                }
            }"""

if old_modal_selection in content:
    content = content.replace(old_modal_selection, new_modal_selection)
    print("7. Updated modal slot selection matching")

old_modal_label = """                                        <label onclick="window.TempoPlanWorkspace.selectRescheduleSlot('${s.date}', '${s.id}', '${s.start || ''}', '${s.end || ''}'); window.TempoPlanWorkspace.render();"
                                               class="p-3 rounded-xl border ${isChecked ? 'border-[#FF6B2C] bg-orange-50/40 ring-1 ring-[#FF6B2C]/30' : 'border-gray-200 hover:border-[#FF6B2C] bg-white hover:bg-orange-50/20'} transition flex items-center space-x-3 cursor-pointer">
                                            <input type="radio" name="pw_reschedule_day" value="${s.date}"
                                                   data-slot-id="${s.id}" data-date="${s.date}" data-start="${s.start || ''}" data-end="${s.end || ''}"
                                                   ${isChecked ? 'checked' : ''}
                                                   onchange="window.TempoPlanWorkspace.selectRescheduleSlot('${s.date}', '${s.id}', '${s.start || ''}', '${s.end || ''}')"
                                                   class="text-[#FF6B2C] focus:ring-[#FF6B2C]">"""

new_modal_label = """                                        <label data-reschedule-slot-label
                                               onclick="window.TempoPlanWorkspace.selectRescheduleSlot('${s.date}', '${s.id}', '${s.start || ''}', '${s.end || ''}')"
                                               class="p-3 rounded-xl border ${isChecked ? 'border-[#FF6B2C] bg-orange-50/40 ring-1 ring-[#FF6B2C]/30' : 'border-gray-200 hover:border-[#FF6B2C] bg-white hover:bg-orange-50/20'} transition flex items-center space-x-3 cursor-pointer">
                                            <input type="radio" name="pw_reschedule_day" value="${s.date}"
                                                   data-slot-id="${s.id}" data-date="${s.date}" data-start="${s.start || ''}" data-end="${s.end || ''}"
                                                   ${isChecked ? 'checked' : ''}
                                                   class="text-[#FF6B2C] focus:ring-[#FF6B2C]">"""

if old_modal_label in content:
    content = content.replace(old_modal_label, new_modal_label)
    print("7b. Updated modal radio label to prevent DOM destruction during click")

# Replace tomorrow.toISOString().split('T')[0] in planWorkspace.js
content = content.replace("const tomorrowStr = tomorrow.toISOString().split('T')[0];", "const tomorrowStr = getLocalTomorrowISO();")

# Export persistPlan and getActivePlan on window.TempoPlanWorkspace
if "openRescheduleModal," in content and "persistPlan," not in content:
    content = content.replace("openRescheduleModal,", "openRescheduleModal,\n        persistPlan,\n        getActivePlan,")
    print("8. Exported persistPlan and getActivePlan")

with open('planWorkspace.js', 'wb') as f:
    f.write(content.encode('utf-8'))
print("planWorkspace.js successfully written with LF line endings!")
