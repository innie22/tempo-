import sys

with open('emergencyFlow.js', 'rb') as f:
    content = f.read().decode('utf-8')

# Ensure CRLF
if '\r\n' in content:
    eol = '\r\n'
else:
    eol = '\n'

print("Detected EOL:", repr(eol))

# 1. Add getTodayISO and getTomorrowISO helpers
target_anchor = "let availabilityDays = [];"
replacement_anchor = f"""let availabilityDays = [];

    function getTodayISO() {{
        if (window.TempoI18n && typeof window.TempoI18n.getLocalTodayISO === 'function') {{
            return window.TempoI18n.getLocalTodayISO();
        }}
        try {{
            return new Intl.DateTimeFormat('en-CA', {{
                timeZone: 'Asia/Ho_Chi_Minh',
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            }}).format(new Date());
        }} catch (e) {{
            const d = new Date();
            const pad = n => String(n).padStart(2, '0');
            return `${{d.getFullYear()}}-${{pad(d.getMonth() + 1)}}-${{pad(d.getDate())}}`;
        }}
    }}

    function getTomorrowISO() {{
        if (window.TempoI18n && typeof window.TempoI18n.getLocalTomorrowISO === 'function') {{
            return window.TempoI18n.getLocalTomorrowISO();
        }}
        const todayStr = getTodayISO();
        const parts = todayStr.split('-').map(Number);
        if (parts.length === 3 && !isNaN(parts[0]) && !isNaN(parts[1]) && !isNaN(parts[2])) {{
            const nextDate = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2] + 1));
            const pad = n => String(n).padStart(2, '0');
            return `${{nextDate.getUTCFullYear()}}-${{pad(nextDate.getUTCMonth() + 1)}}-${{pad(nextDate.getUTCDate())}}`;
        }}
        const d = new Date();
        d.setDate(d.getDate() + 1);
        const pad = n => String(n).padStart(2, '0');
        return `${{d.getFullYear()}}-${{pad(d.getMonth() + 1)}}-${{pad(d.getDate())}}`;
    }}"""

if target_anchor in content:
    content = content.replace(target_anchor, replacement_anchor, 1)
    print("Added getTodayISO and getTomorrowISO helpers")
else:
    print("ERROR: target_anchor not found")
    sys.exit(1)

# Check replacing instances
# 537: const defaultDateStr = tomorrow.toISOString().split('T')[0];
content = content.replace("const defaultDateStr = tomorrow.toISOString().split('T')[0];", "const defaultDateStr = getTomorrowISO();")

# 803: dateInput.value = tomorrow.toISOString().split('T')[0];
content = content.replace("dateInput.value = tomorrow.toISOString().split('T')[0];", "dateInput.value = getTomorrowISO();")

# 847-848:
old_847 = """        const today = new Date();
        const todayStr = today.toISOString().split('T')[0];
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const tomorrowStr = tomorrow.toISOString().split('T')[0];"""
new_847 = """        const todayStr = getTodayISO();
        const tomorrowStr = getTomorrowISO();"""
if old_847 in content:
    content = content.replace(old_847, new_847)
    print("Replaced 847-848")
else:
    print("WARNING: old_847 not found directly, checking normalized")

# 1370-1375 in formatDayLabel:
old_1370 = """    function formatDayLabel(dateStr) {
        const today = new Date();
        const todayStr = today.toISOString().split('T')[0];
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const tomorrowStr = tomorrow.toISOString().split('T')[0];"""
new_1370 = """    function formatDayLabel(dateStr) {
        if (window.TempoI18n && typeof window.TempoI18n.formatScheduledDateLabel === 'function') {
            const isVi = (typeof window.TempoI18n.getCurrentLanguage === 'function') ? (window.TempoI18n.getCurrentLanguage() === 'vi') : true;
            const formatted = window.TempoI18n.formatScheduledDateLabel(dateStr, isVi);
            if (formatted) return formatted;
        }
        const todayStr = getTodayISO();
        const tomorrowStr = getTomorrowISO();"""
if old_1370 in content:
    content = content.replace(old_1370, new_1370)
    print("Replaced 1370 in formatDayLabel")
else:
    print("WARNING: old_1370 not found directly")

# 1394: return today.toISOString().split('T')[0];
content = content.replace("return today.toISOString().split('T')[0];", "return getTodayISO();")

# 1406-1448: initDefaultAvailability
old_init_avail = """    function initDefaultAvailability() {
        const today = new Date();
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);

        const todayStr = today.toISOString().split('T')[0];
        const tomorrowStr = tomorrow.toISOString().split('T')[0];

        const todayLabel = formatDayLabel(todayStr);
        const tomorrowLabel = formatDayLabel(tomorrowStr);

        // Ensure today's default block doesn't start in the past
        const currentMin = today.getHours() * 60 + today.getMinutes();
        let todayStartMin = Math.max(19 * 60, Math.ceil(currentMin / 15) * 15);
        if (todayStartMin >= 23 * 60) {
            todayStartMin = Math.max(0, Math.ceil(currentMin / 15) * 15);
            if (todayStartMin >= 1435) todayStartMin = 1425;
        }
        const todayStartStr = formatMinutesToHHMM(todayStartMin);
        const todayEndStr = todayStartMin >= 1380 ? '23:59' : '23:00';

        availabilityDays = [
            {
                date: todayStr,
                label: todayLabel,
                isUnavailable: false,
                preservedBlocks: [],
                blocks: [
                    { id: 'b_1', start: todayStartStr, end: todayEndStr, minutes: computeTimeDifferenceMinutes(todayStartStr, todayEndStr) }
                ]
            },
            {
                date: tomorrowStr,
                label: tomorrowLabel,
                isUnavailable: false,
                preservedBlocks: [],
                blocks: [
                    { id: 'b_2', start: '09:00', end: '12:00', minutes: 180 },
                    { id: 'b_3', start: '14:00', end: '17:00', minutes: 180 }
                ]
            }
        ];
    }"""

new_init_avail = """    function initDefaultAvailability() {
        // If availability is already loaded and valid, don't clobber it
        if (Array.isArray(availabilityDays) && availabilityDays.length > 0) {
            return;
        }

        // Try to load persisted availabilityDays from confirmedPlan, localStorage tempo_availability_days, or tempo_working_plan
        try {
            if (confirmedPlan && Array.isArray(confirmedPlan.availabilityDays) && confirmedPlan.availabilityDays.length > 0) {
                availabilityDays = JSON.parse(JSON.stringify(confirmedPlan.availabilityDays));
                return;
            }
            const storedAvail = localStorage.getItem('tempo_availability_days');
            if (storedAvail) {
                const parsed = JSON.parse(storedAvail);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    availabilityDays = parsed;
                    return;
                }
            }
            const storedPlan = localStorage.getItem('tempo_working_plan');
            if (storedPlan) {
                const parsed = JSON.parse(storedPlan);
                if (parsed && Array.isArray(parsed.availabilityDays) && parsed.availabilityDays.length > 0) {
                    availabilityDays = parsed.availabilityDays;
                    return;
                }
            }
        } catch(e) {}

        const today = new Date();
        const todayStr = getTodayISO();
        const tomorrowStr = getTomorrowISO();

        const todayLabel = formatDayLabel(todayStr);
        const tomorrowLabel = formatDayLabel(tomorrowStr);

        // Ensure today's default block doesn't start in the past
        const currentMin = today.getHours() * 60 + today.getMinutes();
        let todayStartMin = Math.max(19 * 60, Math.ceil(currentMin / 15) * 15);
        if (todayStartMin >= 23 * 60) {
            todayStartMin = Math.max(0, Math.ceil(currentMin / 15) * 15);
            if (todayStartMin >= 1435) todayStartMin = 1425;
        }
        const todayStartStr = formatMinutesToHHMM(todayStartMin);
        const todayEndStr = todayStartMin >= 1380 ? '23:59' : '23:00';

        availabilityDays = [
            {
                date: todayStr,
                label: todayLabel,
                isUnavailable: false,
                preservedBlocks: [],
                blocks: [
                    { id: 'b_1', start: todayStartStr, end: todayEndStr, minutes: computeTimeDifferenceMinutes(todayStartStr, todayEndStr) }
                ]
            },
            {
                date: tomorrowStr,
                label: tomorrowLabel,
                isUnavailable: false,
                preservedBlocks: [],
                blocks: [
                    { id: 'b_2', start: '09:00', end: '12:00', minutes: 180 },
                    { id: 'b_3', start: '14:00', end: '17:00', minutes: 180 }
                ]
            }
        ];
    }"""

if old_init_avail in content:
    content = content.replace(old_init_avail, new_init_avail)
    print("Replaced initDefaultAvailability")
else:
    print("WARNING: old_init_avail not found directly")

# 1458: const todayStr = new Date().toISOString().split('T')[0];
content = content.replace("const todayStr = new Date().toISOString().split('T')[0];", "const todayStr = getTodayISO();")

# 1697: const todayStr = today.toISOString().split('T')[0];
content = content.replace("const todayStr = today.toISOString().split('T')[0];", "const todayStr = getTodayISO();")

# 1734-1737:
old_1734 = """        const todayStr = today.toISOString().split('T')[0];
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const tomorrowStr = tomorrow.toISOString().split('T')[0];"""
new_1734 = """        const todayStr = getTodayISO();
        const tomorrowStr = getTomorrowISO();"""
if old_1734 in content:
    content = content.replace(old_1734, new_1734)
    print("Replaced 1734-1737")

# 1822: const todayStr = today.toISOString().split('T')[0];
content = content.replace("const todayStr = today.toISOString().split('T')[0];", "const todayStr = getTodayISO();")

# 2861: const todayStr = new Date().toISOString().split('T')[0];
content = content.replace("const todayStr = new Date().toISOString().split('T')[0];", "const todayStr = getTodayISO();")

# 3026: const todayStr = new Date().toISOString().split('T')[0];
content = content.replace("const todayStr = new Date().toISOString().split('T')[0];", "const todayStr = getTodayISO();")

# 4024: if (!initialDate) initialDate = tomorrow.toISOString().split('T')[0];
content = content.replace("if (!initialDate) initialDate = tomorrow.toISOString().split('T')[0];", "if (!initialDate) initialDate = getTomorrowISO();")

# 4073: dateInput.value = tomorrow.toISOString().split('T')[0];
content = content.replace("dateInput.value = tomorrow.toISOString().split('T')[0];", "dateInput.value = getTomorrowISO();")

# Check getConfirmedPlan and setConfirmedPlan
old_get_confirmed = """    function getConfirmedPlan() {
        return confirmedPlan;
    }

    function getAvailabilityDays() {
        return availabilityDays;
    }

    function setConfirmedPlan(plan) {
        confirmedPlan = plan;
        if (plan && Array.isArray(plan.plannedTasks)) {
            tasks = plan.plannedTasks.map(pt => pt.task).filter(Boolean);
        } else if (plan && Array.isArray(plan.tasks)) {
            tasks = [...plan.tasks];
        }
        if (plan && Array.isArray(plan.availabilityDays) && plan.availabilityDays.length > 0) {
            availabilityDays = plan.availabilityDays;
        }
    }"""

new_get_confirmed = """    function getConfirmedPlan() {
        if (confirmedPlan) {
            if (!Array.isArray(confirmedPlan.availabilityDays) || confirmedPlan.availabilityDays.length === 0) {
                confirmedPlan.availabilityDays = availabilityDays;
            }
        }
        return confirmedPlan;
    }

    function getAvailabilityDays() {
        if (!Array.isArray(availabilityDays) || availabilityDays.length === 0) {
            try {
                const storedAvail = localStorage.getItem('tempo_availability_days');
                if (storedAvail) {
                    const parsed = JSON.parse(storedAvail);
                    if (Array.isArray(parsed) && parsed.length > 0) {
                        availabilityDays = parsed;
                    }
                }
            } catch(e) {}
        }
        return availabilityDays;
    }

    function setAvailabilityDays(days) {
        if (Array.isArray(days) && days.length > 0) {
            availabilityDays = days;
            if (confirmedPlan) {
                confirmedPlan.availabilityDays = days;
            }
            try {
                localStorage.setItem('tempo_availability_days', JSON.stringify(days));
            } catch(e) {}
        }
    }

    function setConfirmedPlan(plan) {
        confirmedPlan = plan;
        if (plan && Array.isArray(plan.plannedTasks)) {
            tasks = plan.plannedTasks.map(pt => pt.task).filter(Boolean);
        } else if (plan && Array.isArray(plan.tasks)) {
            tasks = [...plan.tasks];
        }
        if (plan && Array.isArray(plan.availabilityDays) && plan.availabilityDays.length > 0) {
            availabilityDays = plan.availabilityDays;
            try {
                localStorage.setItem('tempo_availability_days', JSON.stringify(availabilityDays));
            } catch(e) {}
        }
    }"""

if old_get_confirmed in content:
    content = content.replace(old_get_confirmed, new_get_confirmed)
    print("Replaced getConfirmedPlan / setConfirmedPlan and added setAvailabilityDays")
else:
    print("WARNING: old_get_confirmed not found directly")

# In exports: add setAvailabilityDays
if "setConfirmedPlan," in content and "setAvailabilityDays," not in content:
    content = content.replace("setConfirmedPlan,", "setConfirmedPlan,\n        setAvailabilityDays,")
    print("Exported setAvailabilityDays")

# In recalculateTimelineSlotsPreservingOrder:
old_recalc_start = """    function recalculateTimelineSlotsPreservingOrder() {
        if (!confirmedPlan || !confirmedPlan.plannedTasks) return;

        // Group planned tasks by Day and re-sequence within normalized windows
        availabilityDays.forEach(day => {"""

new_recalc_start = """    function recalculateTimelineSlotsPreservingOrder() {
        if (!confirmedPlan || !confirmedPlan.plannedTasks) return;

        // Ensure availabilityDays includes any date that has planned tasks
        if (confirmedPlan && Array.isArray(confirmedPlan.plannedTasks)) {
            confirmedPlan.plannedTasks.forEach(pt => {
                const d = pt.dayDate || (pt.task && pt.task.scheduledDate);
                if (d && d !== 'unscheduled' && !availabilityDays.some(day => day.date === d)) {
                    availabilityDays.push({
                        date: d,
                        label: (window.TempoI18n && typeof window.TempoI18n.formatScheduledDateLabel === 'function')
                            ? window.TempoI18n.formatScheduledDateLabel(d)
                            : formatDayLabel(d),
                        isUnavailable: false,
                        blocks: pt.startTime && pt.endTime ? [{
                            id: 'b_' + Date.now(),
                            start: pt.startTime,
                            end: pt.endTime,
                            minutes: computeTimeDifferenceMinutes(pt.startTime, pt.endTime)
                        }] : []
                    });
                }
            });
            availabilityDays.sort((a, b) => a.date.localeCompare(b.date));
        }

        // Group planned tasks by Day and re-sequence within normalized windows
        availabilityDays.forEach(day => {"""

if old_recalc_start in content:
    content = content.replace(old_recalc_start, new_recalc_start)
    print("Updated recalculateTimelineSlotsPreservingOrder to ensure all task dates are kept in availabilityDays")

# In recalculateTimelineSlotsPreservingOrder placed = false:
old_not_placed = """                if (!placed) {
                    item.startTime = null;
                    item.endTime = null;
                    item.startMin = null;
                    item.endMin = null;
                    item.isOverCapacity = true;
                    if (item.task) {
                        item.task.scheduledDate = item.dayDate;
                        item.task.dayDate = item.dayDate;
                        item.task._dayDate = item.dayDate;
                    }
                }"""

new_not_placed = """                if (!placed) {
                    const hasExplicitTimes = item.startTime && item.endTime && item.startMin !== null && item.endMin !== null;
                    if (!hasExplicitTimes) {
                        item.startTime = null;
                        item.endTime = null;
                        item.startMin = null;
                        item.endMin = null;
                    }
                    item.isOverCapacity = true;
                    if (item.task) {
                        item.task.scheduledDate = item.dayDate;
                        item.task.dayDate = item.dayDate;
                        item.task._dayDate = item.dayDate;
                        if (hasExplicitTimes) {
                            item.task.startTime = item.startTime;
                            item.task.endTime = item.endTime;
                            item.task.scheduledStartTime = item.startTime;
                            item.task.scheduledEndTime = item.endTime;
                        }
                    }
                }"""

if old_not_placed in content:
    content = content.replace(old_not_placed, new_not_placed)
    print("Updated not placed handler to preserve explicit times")

# Restore plan state check localStorage tempo_working_plan
old_restore_check = """            let activePlan = (typeof window.TempoPlanStore.getActivePlan === 'function')
                ? window.TempoPlanStore.getActivePlan('emergency')
                : null;
            if (!activePlan && typeof window.TempoPlanStore.loadActivePlan === 'function') {
                activePlan = await window.TempoPlanStore.loadActivePlan('emergency');
            }"""

new_restore_check = """            let activePlan = (typeof window.TempoPlanStore.getActivePlan === 'function')
                ? window.TempoPlanStore.getActivePlan('emergency')
                : null;
            if (!activePlan && typeof window.TempoPlanStore.loadActivePlan === 'function') {
                activePlan = await window.TempoPlanStore.loadActivePlan('emergency');
            }
            if (!activePlan) {
                try {
                    const saved = localStorage.getItem('tempo_working_plan');
                    if (saved) activePlan = JSON.parse(saved);
                } catch(e) {}
            }"""

if old_restore_check in content:
    content = content.replace(old_restore_check, new_restore_check)
    print("Updated restorePlanState to check localStorage tempo_working_plan")

# Save file with CRLF
content = content.replace('\r\n', '\n').replace('\n', '\r\n')
with open('emergencyFlow.js', 'wb') as f:
    f.write(content.encode('utf-8'))
print("emergencyFlow.js successfully saved with CRLF line endings!")
