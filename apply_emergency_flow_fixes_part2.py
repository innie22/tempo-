import sys

with open('emergencyFlow.js', 'rb') as f:
    content = f.read().decode('utf-8')

# Ensure CRLF line endings
content = content.replace('\r\n', '\n')

# 1. In loadSampleTasks:
old_load_sample = """    function loadSampleTasks() {
        const today = new Date();
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);

        const todayStr = getTodayISO();
        const tomorrowStr = tomorrow.toISOString().split('T')[0];"""
new_load_sample = """    function loadSampleTasks() {
        const todayStr = getTodayISO();
        const tomorrowStr = getTomorrowISO();"""
if old_load_sample in content:
    content = content.replace(old_load_sample, new_load_sample)
    print("Replaced loadSampleTasks dates")
else:
    print("WARNING: old_load_sample not found")

# 2. In formatDayLabel:
old_format_day = """    function formatDayLabel(dateStr) {
        const today = new Date();
        const todayStr = getTodayISO();
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const tomorrowStr = tomorrow.toISOString().split('T')[0];

        const [y, m, d] = dateStr.split('-').map(Number);
        const targetDate = new Date(y, m - 1, d);

        const monthDay = targetDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }).toUpperCase();
        const weekday = targetDate.toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase();

        if (dateStr === todayStr) {
            return `TODAY · ${monthDay}`;
        } else if (dateStr === tomorrowStr) {
            return `TOMORROW · ${monthDay}`;
        } else {
            return `${weekday} · ${monthDay}`;
        }
    }"""
new_format_day = """    function formatDayLabel(dateStr) {
        if (window.TempoI18n && typeof window.TempoI18n.formatScheduledDateLabel === 'function') {
            const isVi = (typeof window.TempoI18n.getCurrentLanguage === 'function') ? (window.TempoI18n.getCurrentLanguage() === 'vi') : true;
            const formatted = window.TempoI18n.formatScheduledDateLabel(dateStr, isVi);
            if (formatted) return formatted;
        }
        const todayStr = getTodayISO();
        const tomorrowStr = getTomorrowISO();

        const [y, m, d] = dateStr.split('-').map(Number);
        const targetDate = new Date(y, m - 1, d);

        const monthDay = targetDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }).toUpperCase();
        const weekday = targetDate.toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase();

        if (dateStr === todayStr) {
            return `TODAY · ${monthDay}`;
        } else if (dateStr === tomorrowStr) {
            return `TOMORROW · ${monthDay}`;
        } else {
            return `${weekday} · ${monthDay}`;
        }
    }"""
if old_format_day in content:
    content = content.replace(old_format_day, new_format_day)
    print("Replaced formatDayLabel")
else:
    print("WARNING: old_format_day not found")

# 3. In initDefaultAvailability:
old_init_avail = """    function initDefaultAvailability() {
        const today = new Date();
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);

        const todayStr = getTodayISO();
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
    print("WARNING: old_init_avail not found")

# 4. In getConfirmedPlan and setConfirmedPlan:
old_get_set = """    function getConfirmedPlan() {
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
new_get_set = """    function getConfirmedPlan() {
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
if old_get_set in content:
    content = content.replace(old_get_set, new_get_set)
    print("Replaced getConfirmedPlan and setConfirmedPlan")
else:
    print("WARNING: old_get_set not found")

# Replace remaining .toISOString().split('T')[0] in emergencyFlow.js
content = content.replace("tomorrow.toISOString().split('T')[0]", "getTomorrowISO()")
content = content.replace("today.toISOString().split('T')[0]", "getTodayISO()")
content = content.replace("new Date().toISOString().split('T')[0]", "getTodayISO()")

# Convert to CRLF
content = content.replace('\n', '\r\n')
with open('emergencyFlow.js', 'wb') as f:
    f.write(content.encode('utf-8'))
print("emergencyFlow.js part 2 successfully written with CRLF line endings!")
