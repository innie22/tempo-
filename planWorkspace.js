/**
 * Tempo Shared Plan Workspace (MVP)
 * File: planWorkspace.js
 * 
 * Post-setup View & Edit Plan experience for an existing saved Emergency Plan.
 * Operates directly on the shared active plan and tasks without recreating or cloning.
 */

window.TempoPlanWorkspace = (function() {
    let selectedTaskId = null;
    let isEditingDeadline = false;
    let showAddSubtaskInput = false;
    let activeModal = null; // null | 'add-task' | 'fit-task-prompt' | 'adjust-availability' | 'reschedule' | 'deadline-plan-reorder-confirm' | 'edit-task-note'
    let pendingAddedTask = null;
    let rescheduleTaskId = null;
    let rescheduleSelectedWindow = null;
    let rescheduleSelectedSlot = null;
    let rescheduleShowAddTime = false;
    let adjustAvailShowAdd = false;
    let repeatConfigDate = null;
    let pendingClearTaskId = null;
    let isActionProcessing = false;
    let activeLabelMenuTaskId = null;
    let pendingDeadlineEdit = null;
    let pendingNoteTaskId = null;

    // Helper: Escape HTML
    function escapeHTML(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Helper: Format minutes into human-readable duration
    function formatDuration(mins) {
        if (!mins || mins <= 0) return '0m';
        const h = Math.floor(mins / 60);
        const m = mins % 60;
        if (h > 0 && m > 0) return `${h}h ${m}m`;
        if (h > 0) return `${h}h`;
        return `${m}m`;
    }

    // Helper: 12-hour format
    function formatTime12H(timeStr) {
        if (!timeStr) return '';
        if (timeStr.toLowerCase().includes('am') || timeStr.toLowerCase().includes('pm')) return timeStr;
        const parts = timeStr.split(':');
        if (parts.length < 2) return timeStr;
        let h = parseInt(parts[0], 10);
        const m = parts[1];
        if (isNaN(h)) return timeStr;
        const ampm = h >= 12 ? 'PM' : 'AM';
        h = h % 12;
        if (h === 0) h = 12;
        return `${h}:${m} ${ampm}`;
    }

    // Helper: Parse HH:MM or 12-hour AM/PM to minutes (with optional isEnd for 24:00/00:00 end of day)
    function parseTimeToMinutes(str, isEnd) {
        if (!str || typeof str !== 'string') return 0;
        const trimmed = str.trim();
        if (isEnd && (trimmed === '24:00' || trimmed === '00:00')) {
            return 1440;
        }
        const isPM = /pm$/i.test(trimmed);
        const isAM = /am$/i.test(trimmed);
        const cleanStr = trimmed.replace(/\s*(am|pm)$/i, '');
        const parts = cleanStr.split(':');
        let hours = parseInt(parts[0], 10) || 0;
        const minutes = parseInt(parts[1], 10) || 0;
        if (isPM && hours < 12) hours += 12;
        if (isAM && hours === 12) hours = 0;
        const totalMinutes = hours * 60 + minutes;
        if (isEnd && totalMinutes === 0 && (hours === 0 && minutes === 0 && (trimmed === '00:00' || trimmed === '12:00 am' || trimmed === '12:00am'))) {
            return 1440;
        }
        return totalMinutes;
    }

    // Helper: Normalize date to YYYY-MM-DD
    function normalizeDateISO(dateInput) {
        if (!dateInput) return '';
        if (typeof dateInput !== 'string') {
            if (dateInput instanceof Date && !isNaN(dateInput)) {
                const pad = n => String(n).padStart(2, '0');
                return `${dateInput.getFullYear()}-${pad(dateInput.getMonth() + 1)}-${pad(dateInput.getDate())}`;
            }
            return '';
        }
        const clean = dateInput.split(/[T ]/)[0].trim();
        if (/^\d{4}-\d{2}-\d{2}$/.test(clean)) {
            return clean;
        }
        const parsed = new Date(clean);
        if (!isNaN(parsed.getTime())) {
            const pad = n => String(n).padStart(2, '0');
            return `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())}`;
        }
        return clean;
    }

    /**
     * Clean up expired availability slots in Tempo Working Plan
     * - Past dates: Remove all availability slots belonging to dates before today.
     * - Today: Remove only time slots whose end time has already passed.
     * - Ongoing slots: Keep slots that have started but have not ended yet.
     * - Future slots: Keep all upcoming availability slots unchanged.
     */
    function cleanupExpiredAvailability(plan, refDate, refTime) {
        if (!plan || !Array.isArray(plan.availabilityDays)) {
            return false;
        }

        const todayStr = refDate || getLocalTodayISO();
        const currentTimeStr = refTime || getLocalCurrentTimeStr();
        const currentMinutes = parseTimeToMinutes(currentTimeStr, false);

        let changed = false;
        const cleanedDays = [];

        for (const day of plan.availabilityDays) {
            if (!day) continue;
            const cleanDate = normalizeDateISO(day.date);
            if (!cleanDate) continue;

            // 1. Past dates: Remove all availability slots belonging to dates before today
            if (cleanDate < todayStr) {
                changed = true;
                continue;
            }

            // 2. Today: Remove only time slots whose end time has already passed
            if (cleanDate === todayStr) {
                const originalBlocks = Array.isArray(day.blocks) ? day.blocks : [];
                const validBlocks = originalBlocks.filter(block => {
                    if (!block || !block.end) return false;
                    const endMinutes = parseTimeToMinutes(block.end, true);
                    const hasPassed = endMinutes <= currentMinutes;
                    return !hasPassed;
                });

                if (validBlocks.length !== originalBlocks.length) {
                    changed = true;
                }

                // Do not delete an entire availability day if it still contains valid future/ongoing time slots
                if (validBlocks.length > 0) {
                    cleanedDays.push({
                        ...day,
                        date: cleanDate,
                        blocks: validBlocks
                    });
                } else {
                    changed = true;
                }
                continue;
            }

            // 3. Future dates (cleanDate > todayStr): Keep all upcoming availability slots unchanged
            cleanedDays.push({
                ...day,
                date: cleanDate
            });
        }

        if (cleanedDays.length !== plan.availabilityDays.length) {
            changed = true;
        }

        if (changed) {
            plan.availabilityDays = cleanedDays;
        }

        return changed;
    }

    /**
     * Recurrence & Copy helpers for Availability
     */
    function getRecurringRules() {
        try {
            const saved = localStorage.getItem('tempo_availability_recurring_rules');
            if (saved) {
                const parsed = JSON.parse(saved);
                if (Array.isArray(parsed)) return parsed;
            }
        } catch (e) {}
        const plan = getActivePlan();
        if (plan && Array.isArray(plan.recurringAvailabilityRules)) {
            return plan.recurringAvailabilityRules;
        }
        return [];
    }

    function saveRecurringRule(rule) {
        const rules = getRecurringRules().filter(r => r.id !== rule.id && r.sourceDate !== rule.sourceDate);
        rules.push(rule);
        try {
            localStorage.setItem('tempo_availability_recurring_rules', JSON.stringify(rules));
        } catch (e) {}
        const plan = getActivePlan();
        if (plan) {
            plan.recurringAvailabilityRules = rules;
        }
        return rules;
    }

    function disableRecurringRule(sourceDate) {
        const rules = getRecurringRules();
        const rule = rules.find(r => r.sourceDate === sourceDate || (r.startDate && r.startDate === sourceDate));
        if (rule) {
            rule.enabled = false;
            try {
                localStorage.setItem('tempo_availability_recurring_rules', JSON.stringify(rules));
            } catch (e) {}
            const plan = getActivePlan();
            if (plan) {
                plan.recurringAvailabilityRules = rules;
                const todayStr = getLocalTodayISO();
                (plan.availabilityDays || []).forEach(day => {
                    if (day.date >= todayStr && Array.isArray(day.blocks)) {
                        day.blocks = day.blocks.filter(b => !String(b.id).startsWith(`b_rec_${rule.id}`));
                    }
                });
            }
        }
        return rules;
    }

    function getRecurringRuleForDate(dateStr) {
        const rules = getRecurringRules();
        return rules.find(r => r.enabled !== false && (r.sourceDate === dateStr || r.startDate === dateStr));
    }

    function applyRecurringRulesToPlan(plan) {
        if (!plan) return false;
        if (!Array.isArray(plan.availabilityDays)) plan.availabilityDays = [];

        const rules = getRecurringRules().filter(r => r.enabled !== false && Array.isArray(r.slots) && r.slots.length > 0);
        if (rules.length === 0) return false;

        const todayStr = getLocalTodayISO();
        let changed = false;

        rules.forEach(rule => {
            if (!rule.startDate) return;
            const [sY, sM, sD] = rule.startDate.split('-').map(Number);
            let curDate = new Date(sY, sM - 1, sD);

            while (curDate.getDay() !== rule.weekday) {
                curDate.setDate(curDate.getDate() + 1);
            }

            const maxWeeks = 8;
            const maxDate = new Date(curDate.getTime() + maxWeeks * 7 * 86400000);
            const pad = n => String(n).padStart(2, '0');

            while (curDate <= maxDate) {
                const dateStr = `${curDate.getFullYear()}-${pad(curDate.getMonth() + 1)}-${pad(curDate.getDate())}`;

                if (rule.endDate && dateStr > rule.endDate) {
                    break;
                }

                if (dateStr >= todayStr) {
                    let day = plan.availabilityDays.find(d => d.date === dateStr);
                    if (!day) {
                        day = {
                            date: dateStr,
                            label: formatScheduledDateLabel(dateStr, isViLocale()) || dateStr,
                            isUnavailable: false,
                            blocks: []
                        };
                        plan.availabilityDays.push(day);
                        changed = true;
                    }
                    if (!Array.isArray(day.blocks)) day.blocks = [];

                    rule.slots.forEach((s, sIdx) => {
                        const exists = day.blocks.some(b => b.start === s.start && b.end === s.end);
                        if (!exists) {
                            day.blocks.push({
                                id: `b_rec_${rule.id}_${dateStr}_${sIdx}`,
                                start: s.start,
                                end: s.end
                            });
                            changed = true;
                        }
                    });
                    day.blocks.sort((a, b) => a.start.localeCompare(b.start));
                }

                curDate.setDate(curDate.getDate() + 7);
            }
        });

        if (changed) {
            plan.availabilityDays.sort((a, b) => a.date.localeCompare(b.date));
        }
        return changed;
    }

    function copyTodayAvailabilityToTomorrow() {
        const plan = getActivePlan();
        if (!plan) return;

        const todayStr = getLocalTodayISO();
        const tomorrowStr = getLocalTomorrowISO();

        const todayDay = (plan.availabilityDays || []).find(d => d.date === todayStr);
        const todayBlocks = todayDay && Array.isArray(todayDay.blocks) ? todayDay.blocks : [];

        if (todayBlocks.length === 0) {
            const noMsg = window.t ? window.t('workspace.noWorkingHours', {}, 'No working hours available to copy.') : 'No working hours available to copy.';
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast(noMsg);
            } else {
                alert(noMsg);
            }
            return;
        }

        if (!Array.isArray(plan.availabilityDays)) plan.availabilityDays = [];
        let tomorrowDay = plan.availabilityDays.find(d => d.date === tomorrowStr);
        if (!tomorrowDay) {
            tomorrowDay = {
                date: tomorrowStr,
                label: formatScheduledDateLabel(tomorrowStr, isViLocale()) || tomorrowStr,
                isUnavailable: false,
                blocks: []
            };
            plan.availabilityDays.push(tomorrowDay);
            plan.availabilityDays.sort((a, b) => a.date.localeCompare(b.date));
        }
        if (!Array.isArray(tomorrowDay.blocks)) tomorrowDay.blocks = [];

        let copiedCount = 0;
        todayBlocks.forEach(b => {
            const exists = tomorrowDay.blocks.some(tb => tb.start === b.start && tb.end === b.end);
            if (!exists) {
                tomorrowDay.blocks.push({
                    id: 'b_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
                    start: b.start,
                    end: b.end
                });
                copiedCount++;
            }
        });

        tomorrowDay.blocks.sort((a, b) => a.start.localeCompare(b.start));
        persistPlan(plan);

        const successMsg = window.t ? window.t('workspace.copiedSuccessfully', {}, 'Working hours copied successfully.') : 'Working hours copied successfully.';
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(successMsg);
        } else {
            alert(successMsg);
        }
        render();
    }

    function openRepeatWeeklyModal(dateStr) {
        repeatConfigDate = dateStr;
        activeModal = 'repeat-weekly-config';
        render();
    }

    function closeRepeatWeeklyModal() {
        activeModal = 'adjust-availability';
        repeatConfigDate = null;
        render();
    }

    function confirmRepeatWeekly() {
        if (!repeatConfigDate) return;
        const plan = getActivePlan();
        if (!plan) return;

        const repeatEveryWeekCb = document.getElementById('pw-repeat-every-week');
        const startDateInput = document.getElementById('pw-repeat-start-date');
        const endDateInput = document.getElementById('pw-repeat-end-date');

        const enabled = repeatEveryWeekCb ? repeatEveryWeekCb.checked : true;
        const startDate = startDateInput ? startDateInput.value.trim() : repeatConfigDate;
        const endDate = endDateInput ? endDateInput.value.trim() : '';

        if (!enabled) {
            disableRecurringRule(repeatConfigDate);
            persistPlan(plan);
            const disabledMsg = isViLocale() ? 'Đã tắt lặp lại hàng tuần.' : 'Weekly recurrence disabled.';
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast(disabledMsg);
            }
            closeRepeatWeeklyModal();
            return;
        }

        const day = (plan.availabilityDays || []).find(d => d.date === repeatConfigDate);
        const dayBlocks = day && Array.isArray(day.blocks) ? day.blocks : [];

        if (dayBlocks.length === 0) {
            const noMsg = window.t ? window.t('workspace.noWorkingHours', {}, 'No working hours available to copy.') : 'No working hours available to copy.';
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast(noMsg);
            } else {
                alert(noMsg);
            }
            return;
        }

        const [sY, sM, sD] = startDate.split('-').map(Number);
        const sDateObj = new Date(sY, sM - 1, sD);
        const weekday = sDateObj.getDay();

        const existingRule = getRecurringRuleForDate(repeatConfigDate);
        const rule = {
            id: existingRule ? existingRule.id : 'rec_' + Date.now(),
            sourceDate: repeatConfigDate,
            weekday: weekday,
            slots: dayBlocks.map(b => ({ start: b.start, end: b.end })),
            startDate: startDate,
            endDate: endDate || null,
            enabled: true,
            createdAt: Date.now()
        };

        saveRecurringRule(rule);
        applyRecurringRulesToPlan(plan);
        persistPlan(plan);

        const successMsg = isViLocale() ? 'Đã cài đặt lặp lại hàng tuần thành công.' : 'Weekly recurrence configured successfully.';
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(successMsg);
        } else {
            alert(successMsg);
        }
        closeRepeatWeeklyModal();
    }

    // Helper: Format minutes to HH:MM (24-hour)
    function formatMinutesToTimeString(min) {
        const h = Math.floor(min / 60);
        const m = min % 60;
        return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
    }

    // Helper: Check deadline conflict
    function checkDeadlineConflict(task, plannedDate, plannedEndMinutes) {
        if (!task || !task.hasDeadline || !task.deadlineDate) return false;
        if (plannedDate > task.deadlineDate) return true;
        if (plannedDate === task.deadlineDate && task.deadlineTime) {
            const deadlineMin = parseTimeToMinutes(task.deadlineTime);
            return (plannedEndMinutes || 1440) > deadlineMin;
        }
        return false;
    }

    // Helper: Format Month Day (e.g. Oct 17)
    function formatMonthDay(dateStr) {
        if (!dateStr) return '';
        try {
            const clean = dateStr.split('T')[0];
            const parts = clean.split('-');
            if (parts.length === 3) {
                const date = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }
        } catch(e) {}
        return dateStr;
    }

    // Helper: Human deadline
    function formatDeadline(dateStr, timeStr) {
        if (window.TempoI18n && typeof window.TempoI18n.formatDeadline === 'function') {
            return window.TempoI18n.formatDeadline(dateStr, timeStr);
        }
        if (!dateStr) return isViLocale() ? 'Chưa có deadline' : 'No deadline';
        if (dateStr.includes(' ') && !timeStr) {
            const parts = dateStr.split(' ');
            dateStr = parts[0];
            timeStr = parts[1];
        }
        try {
            const [y, m, d] = dateStr.split('-').map(Number);
            const date = new Date(y, m - 1, d);
            const monthDay = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            if (timeStr) {
                return `${monthDay} · ${formatTime12H(timeStr)}`;
            }
            return monthDay;
        } catch (e) {
            return `${dateStr}${timeStr ? ' · ' + timeStr : ''}`;
        }
    }

    function isViLocale() {
        if (window.TempoI18n && typeof window.TempoI18n.getLanguage === 'function') {
            return window.TempoI18n.getLanguage() === 'vi';
        }
        try {
            const saved = localStorage.getItem('tempo_language');
            if (saved) return saved === 'vi';
        } catch (e) {}
        return false;
    }

    function t(path, params, fallback) {
        if (window.TempoI18n && typeof window.TempoI18n.t === 'function') {
            return window.TempoI18n.t(path, params, fallback);
        }
        if (typeof window.t === 'function') {
            return window.t(path, params, fallback);
        }
        return fallback;
    }

    function getLocalTodayISO() {
        if (window.TempoI18n && typeof window.TempoI18n.getLocalTodayISO === 'function') {
            return window.TempoI18n.getLocalTodayISO();
        }
        try {
            return new Intl.DateTimeFormat('en-CA', {
                timeZone: 'Asia/Ho_Chi_Minh',
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            }).format(new Date());
        } catch (e) {
            const d = new Date();
            const pad = n => String(n).padStart(2, '0');
            return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
        }
    }

    function getLocalTomorrowISO() {
        if (window.TempoI18n && typeof window.TempoI18n.getLocalTomorrowISO === 'function') {
            return window.TempoI18n.getLocalTomorrowISO();
        }
        const todayStr = getLocalTodayISO();
        const parts = todayStr.split('-').map(Number);
        if (parts.length === 3 && !isNaN(parts[0]) && !isNaN(parts[1]) && !isNaN(parts[2])) {
            const nextDate = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2] + 1));
            const pad = n => String(n).padStart(2, '0');
            return `${nextDate.getUTCFullYear()}-${pad(nextDate.getUTCMonth() + 1)}-${pad(nextDate.getUTCDate())}`;
        }
        const d = new Date();
        d.setDate(d.getDate() + 1);
        const pad = n => String(n).padStart(2, '0');
        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    }

    function getLocalCurrentTimeStr() {
        try {
            return new Intl.DateTimeFormat('en-GB', {
                timeZone: 'Asia/Ho_Chi_Minh',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            }).format(new Date());
        } catch (e) {
            const d = new Date();
            const pad = n => String(n).padStart(2, '0');
            return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
        }
    }

    function formatScheduledDateLabel(dateStr, isVi = isViLocale()) {
        if (window.TempoI18n && typeof window.TempoI18n.formatScheduledDateLabel === 'function') {
            return window.TempoI18n.formatScheduledDateLabel(dateStr, isVi);
        }
        if (!dateStr || typeof dateStr !== 'string') return '';
        const cleanDate = dateStr.split(/[T ]/)[0].trim();
        if (!cleanDate || cleanDate === 'unscheduled') return '';

        const isViBool = (typeof isVi === 'boolean') ? isVi : (isVi === 'vi');
        const targetLang = isViBool ? 'vi' : 'en';

        let calDate = '';
        if (window.TempoI18n && typeof window.TempoI18n.formatCalendarDate === 'function') {
            calDate = window.TempoI18n.formatCalendarDate(cleanDate, targetLang);
        } else {
            const parts = cleanDate.split('-');
            if (parts.length === 3) {
                const pad = n => String(n).padStart(2, '0');
                const day = pad(parts[2]);
                const month = pad(parts[1]);
                const year = parts[0];
                const enMonths = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                const mIdx = parseInt(parts[1], 10) - 1;
                calDate = isViBool ? `${day}/${month}/${year}` : `${enMonths[mIdx] || ''} ${day}, ${year}`;
            } else {
                calDate = cleanDate;
            }
        }

        const todayStr = getLocalTodayISO();
        const tomorrowStr = getLocalTomorrowISO();

        if (cleanDate === todayStr) {
            return isViBool ? `Hôm nay · ${calDate}` : `Today · ${calDate}`;
        }
        if (cleanDate === tomorrowStr) {
            return isViBool ? (calDate ? `Ngày mai · ${calDate}` : 'Ngày mai') : (calDate ? `Tomorrow · ${calDate}` : 'Tomorrow');
        }

        return calDate;
    }

    function isTaskOverdue(taskOrPt, plan) {
        const task = (taskOrPt && taskOrPt.task) ? taskOrPt.task : taskOrPt;
        if (!task || task.completed === true || task.isCompleted === true || task.status === 'completed') return false;

        const hasDeadline = task.hasDeadline !== false && Boolean(task.deadlineDate || task.deadline);
        if (!hasDeadline) return false;

        const deadlineDate = task.deadlineDate || (typeof task.deadline === 'string' ? task.deadline.split(/[T ]/)[0] : null);
        if (!deadlineDate) return false;

        const todayStr = getLocalTodayISO();
        if (deadlineDate < todayStr) return true;
        if (deadlineDate > todayStr) return false;

        // Deadline is today -> check time
        const deadlineTime = task.deadlineTime || (typeof task.deadline === 'string' && task.deadline.includes(' ') ? task.deadline.split(' ')[1] : null);
        if (!deadlineTime) return false;

        const currentTimeStr = getLocalCurrentTimeStr();
        return deadlineTime.substring(0, 5) < currentTimeStr.substring(0, 5);
    }

    function isTaskMissedSchedule(taskOrPt, plan) {
        const task = (taskOrPt && taskOrPt.task) ? taskOrPt.task : taskOrPt;
        if (!task || task.completed === true || task.isCompleted === true || task.status === 'completed') return false;
        if (isTaskOverdue(task, plan)) return false;

        // Resolve scheduled date and time
        let dayDate = null;
        let endTime = null;

        if (taskOrPt && taskOrPt.dayDate) {
            dayDate = taskOrPt.dayDate;
            endTime = taskOrPt.endTime || taskOrPt.scheduledEndTime;
        } else if (plan && Array.isArray(plan.plannedTasks)) {
            const pt = plan.plannedTasks.find(p => p.task && (p.task.id === task.id || p.id === task.id));
            if (pt && pt.dayDate) {
                dayDate = pt.dayDate;
                endTime = pt.endTime || pt.scheduledEndTime;
            }
        }
        if (!dayDate) {
            if (task._dayDate || task.dayDate || task.scheduledDate) {
                dayDate = task._dayDate || task.dayDate || task.scheduledDate;
                endTime = task._endTime || task.endTime;
            }
        }

        if (!dayDate || dayDate === 'unscheduled') return false;

        const todayStr = getLocalTodayISO();
        if (dayDate < todayStr) return true;
        if (dayDate > todayStr) return false;

        // Today: check if scheduled end time has passed
        if (endTime) {
            let time24 = endTime;
            if (typeof endTime === 'string') {
                const lower = endTime.toLowerCase().trim();
                if (lower.includes('am') || lower.includes('pm')) {
                    const isPm = lower.includes('pm');
                    const clean = lower.replace(/am|pm/g, '').trim();
                    const [hStr, mStr] = clean.split(':');
                    let h = parseInt(hStr, 10);
                    const m = mStr ? mStr.padStart(2, '0') : '00';
                    if (isPm && h < 12) h += 12;
                    if (!isPm && h === 12) h = 0;
                    time24 = `${String(h).padStart(2, '0')}:${m}`;
                }
            }
            const currentTimeStr = getLocalCurrentTimeStr();
            if (time24.substring(0, 5) < currentTimeStr.substring(0, 5)) {
                return true;
            }
        }

        return false;
    }

    function getTaskState(taskOrPt, plan) {
        const task = (taskOrPt && taskOrPt.task) ? taskOrPt.task : taskOrPt;
        if (!task) return 'UNKNOWN';
        if (task.completed === true || task.isCompleted === true || task.status === 'completed') {
            return 'Done';
        }
        if (isTaskOverdue(taskOrPt, plan)) {
            return 'Overdue';
        }
        if (isTaskMissedSchedule(taskOrPt, plan)) {
            return 'Missed Schedule';
        }
        const dayDate = (taskOrPt && taskOrPt.dayDate) || task.dayDate || task._dayDate || task.scheduledDate;
        const todayStr = getLocalTodayISO();
        if (dayDate) {
            if (dayDate === todayStr) return 'Today';
            if (dayDate > todayStr) return 'Upcoming';
        }
        return 'Upcoming';
    }

    let pwDismissedMissedSchedule = new Set();

    function isMissedSchedulePromptDismissed(taskId, currentScheduledDate) {
        if (!taskId) return false;
        if (pwDismissedMissedSchedule.has(String(taskId))) {
            return true;
        }
        if (window.TempoMode && typeof window.TempoMode.isMissedSchedulePromptDismissed === 'function') {
            if (window.TempoMode.isMissedSchedulePromptDismissed(taskId, currentScheduledDate)) return true;
        }
        try {
            const stored = JSON.parse(localStorage.getItem('tempo_dismissed_missed_schedule') || '{}');
            const entry = stored[String(taskId)];
            if (entry && entry.scheduledDate === currentScheduledDate) {
                return true;
            }
        } catch (e) {}
        return false;
    }

    function dismissMissedSchedulePrompt(taskId, currentScheduledDate) {
        if (!taskId) return;
        pwDismissedMissedSchedule.add(String(taskId));
        if (window.TempoMode && typeof window.TempoMode.dismissMissedSchedulePrompt === 'function') {
            window.TempoMode.dismissMissedSchedulePrompt(taskId, currentScheduledDate);
        }
        try {
            const stored = JSON.parse(localStorage.getItem('tempo_dismissed_missed_schedule') || '{}');
            stored[String(taskId)] = {
                scheduledDate: currentScheduledDate,
                dismissedAt: Date.now()
            };
            localStorage.setItem('tempo_dismissed_missed_schedule', JSON.stringify(stored));
        } catch (e) {}
    }

    function clearMissedScheduleDismissal(taskId) {
        if (!taskId) return;
        pwDismissedMissedSchedule.delete(String(taskId));
        if (window.TempoMode && typeof window.TempoMode.clearMissedScheduleDismissal === 'function') {
            window.TempoMode.clearMissedScheduleDismissal(taskId);
        }
        try {
            const stored = JSON.parse(localStorage.getItem('tempo_dismissed_missed_schedule') || '{}');
            delete stored[String(taskId)];
            localStorage.setItem('tempo_dismissed_missed_schedule', JSON.stringify(stored));
        } catch (e) {}
    }

    // Helper: Today ISO string YYYY-MM-DD
    function getTodayISO() {
        return getLocalTodayISO();
    }

        // Reference plan generator matching the UI specification
    function getDefaultReferencePlan() {
        const todayStr = getLocalTodayISO();
        const tomorrowStr = getLocalTomorrowISO();

        const defaultPlan = {
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
                }
            ],
            plannedTasks: [
                {
                    dayDate: todayStr,
                    dayLabel: formatScheduledDateLabel(todayStr),
                    startTime: '3:00 PM',
                    endTime: '5:30 PM',
                    executionBadge: 'Now',
                    task: {
                        id: 'task-marketing-research',
                        name: 'Marketing Research',
                        hasDeadline: true,
                        deadlineDate: '2026-10-17',
                        deadlineTime: '21:00',
                        deadline: '2026-10-17 21:00',
                        durationMinutes: 150,
                        durationLabel: '2h 30m',
                        completed: false,
                        isInProgress: true,
                        description: 'Create a sheet to manage references',
                        subtasks: [
                            { id: 'sub-1', title: 'Subtask 1: Outline', completed: false, durationMinutes: 30 },
                            { id: 'sub-2', title: 'Subtask 2: Literature Review', completed: false, durationMinutes: 45 },
                            { id: 'sub-3', title: 'Subtask 3: Research Gap', completed: false, durationMinutes: 30 },
                            { id: 'sub-4', title: 'Subtask 4: Methodology', completed: false, durationMinutes: 20 },
                            { id: 'sub-5', title: 'Subtask 5: Data Analysis', completed: false, durationMinutes: 15 },
                            { id: 'sub-6', title: 'Subtask 6: Summary Report', completed: false, durationMinutes: 10 }
                        ]
                    }
                },
                {
                    dayDate: todayStr,
                    dayLabel: formatScheduledDateLabel(todayStr),
                    startTime: '3:00 PM',
                    endTime: '5:30 PM',
                    executionBadge: 'Later',
                    task: {
                        id: 'task-event-proposal',
                        name: 'Event Proposal',
                        hasDeadline: true,
                        deadlineDate: '2026-10-18',
                        deadlineTime: '22:00',
                        deadline: '2026-10-18 22:00',
                        durationMinutes: 150,
                        durationLabel: '2h 30m',
                        completed: false,
                        isInProgress: false,
                        description: 'Coordinate with design team for event collateral',
                        subtasks: [
                            { id: 'sub-ep-1', title: 'Subtask 1: Budget Draft', completed: false, durationMinutes: 45 },
                            { id: 'sub-ep-2', title: 'Subtask 2: Venue Options', completed: false, durationMinutes: 60 },
                            { id: 'sub-ep-3', title: 'Subtask 3: Guest List', completed: false, durationMinutes: 45 }
                        ]
                    }
                },
                {
                    dayDate: tomorrowStr,
                    dayLabel: formatScheduledDateLabel(tomorrowStr),
                    startTime: '9:00 AM',
                    endTime: '11:30 AM',
                    executionBadge: 'Later',
                    task: {
                        id: 'task-edit-video',
                        name: 'Edit Video',
                        hasDeadline: true,
                        deadlineDate: '2026-10-20',
                        deadlineTime: '22:00',
                        deadline: '2026-10-20 22:00',
                        durationMinutes: 150,
                        durationLabel: '2h 30m',
                        completed: false,
                        isInProgress: false,
                        description: 'Export in 1080p format for social channels',
                        subtasks: []
                    }
                }
            ],
            unarrangedTasks: [
                {
                    id: 'task-client-sync',
                    name: 'Client Follow-up',
                    hasDeadline: false,
                    durationMinutes: 60,
                    durationLabel: '1h',
                    completed: false,
                    subtasks: []
                },
                {
                    id: 'task-deck-review',
                    name: 'Review Pitch Deck',
                    hasDeadline: false,
                    durationMinutes: 45,
                    durationLabel: '45m',
                    completed: false,
                    subtasks: []
                },
                {
                    id: 'task-team-catchup',
                    name: 'Team Sync & Retrospective',
                    hasDeadline: false,
                    durationMinutes: 30,
                    durationLabel: '30m',
                    completed: false,
                    subtasks: []
                }
            ],
            tasks: []
        };
        defaultPlan.tasks = [
            ...defaultPlan.plannedTasks.map(pt => pt.task),
            ...defaultPlan.unarrangedTasks
        ];
        return defaultPlan;
    }

    // Load active plan from TempoPlanStore, TempoEmergencyFlow, or local storage
    function getActivePlan() {
        const currentUserId = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') 
            ? window.TempoAuth.getCurrentUserId() 
            : ((window.TempoPlanStore && typeof window.TempoPlanStore.getUserId === 'function') ? window.TempoPlanStore.getUserId() : 'guest');
        const isAuthenticated = !!(currentUserId && currentUserId !== 'guest');

        let plan = null;
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            plan = window.TempoEmergencyFlow.getConfirmedPlan();
        }
        if (!plan && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            plan = window.TempoPlanStore.getActivePlan('emergency') || window.TempoPlanStore.getActivePlan('recovery') || window.TempoPlanStore.getActivePlan('default');
        }
        if (!plan) {
            try {
                const key = isAuthenticated ? `tempo_working_plan_${currentUserId}` : 'tempo_working_plan';
                const saved = localStorage.getItem(key);
                if (saved) plan = JSON.parse(saved);
            } catch(e) {}
        }
        if (plan) {
            if (isAuthenticated) {
                if (plan.userId && plan.userId !== currentUserId) return null;
                if (plan.user_id && plan.user_id !== currentUserId) return null;
                if (!plan.userId && !plan.user_id) return null;
            }
            if (!Array.isArray(plan.plannedTasks)) plan.plannedTasks = [];
            if (!Array.isArray(plan.unarrangedTasks)) plan.unarrangedTasks = [];
            if (!Array.isArray(plan.tasks)) plan.tasks = [];

            // Ensure plan.availabilityDays is populated & synchronized
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
            }
        }
        // Invariant: NEVER automatically inject default or sample tasks.
        // Return null or plan with legitimate user tasks only.
        return plan;
    }

    // Save active plan to TempoPlanStore & localStorage
    async function persistPlan(plan) {
        if (!plan) return;

        // Ensure availabilityDays is saved in plan, localStorage, and emergencyFlow
        if (Array.isArray(plan.availabilityDays)) {
            try {
                localStorage.setItem('tempo_availability_days', JSON.stringify(plan.availabilityDays));
            } catch(e) {}
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setAvailabilityDays === 'function') {
                window.TempoEmergencyFlow.setAvailabilityDays(plan.availabilityDays);
            }
        }

        // Save to user-scoped storage FIRST so data is never lost even if remote fails
        try {
            const currentUserId = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') 
                ? window.TempoAuth.getCurrentUserId() 
                : ((window.TempoPlanStore && typeof window.TempoPlanStore.getUserId === 'function') ? window.TempoPlanStore.getUserId() : 'guest');
            if (currentUserId && currentUserId !== 'guest') {
                plan.userId = currentUserId;
                plan.user_id = currentUserId;
                localStorage.setItem(`tempo_working_plan_${currentUserId}`, JSON.stringify(plan));
            } else {
                localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
            }
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
    }

    /**
     * AI Planner: Reorganize and fit tasks into schedule based on priorities and deadlines
     */
    function reorganizePlanWithPlanner(plan) {
        if (!plan || !Array.isArray(plan.plannedTasks)) return;

        // Separate completed vs active planned tasks
        const completedItems = plan.plannedTasks.filter(item => item.task && item.task.completed);
        const activeItems = plan.plannedTasks.filter(item => !item.task || !item.task.completed);

        // Sort active tasks:
        // 1. Now tasks (rank 1) before Later tasks (rank 3)
        // 2. Within same rank: sort by deadline urgency (earlier deadline first)
        activeItems.sort((aItem, bItem) => {
            const a = aItem.task || {};
            const b = bItem.task || {};
            const isNowA = a.userLabel === 'Now' || a.priorityCategory === 'DO_FIRST';
            const isNowB = b.userLabel === 'Now' || b.priorityCategory === 'DO_FIRST';
            const isLaterA = a.userLabel === 'Later' || a.priorityCategory === 'LATER';
            const isLaterB = b.userLabel === 'Later' || b.priorityCategory === 'LATER';
            const rankA = isNowA ? 1 : (isLaterA ? 3 : 2);
            const rankB = isNowB ? 1 : (isLaterB ? 3 : 2);

            if (rankA !== rankB) return rankA - rankB;

            const hasDeadA = !!(a.hasDeadline && a.deadlineDate);
            const hasDeadB = !!(b.hasDeadline && b.deadlineDate);
            if (hasDeadA && hasDeadB) {
                const cmp = (a.deadlineDate + (a.deadlineTime || '23:59')).localeCompare(b.deadlineDate + (b.deadlineTime || '23:59'));
                if (cmp !== 0) return cmp;
            } else if (hasDeadA && !hasDeadB) {
                return -1;
            } else if (!hasDeadA && hasDeadB) {
                return 1;
            }
            return 0;
        });

        // Sequential slot allocation based on available days
        let availabilityDays = (plan && Array.isArray(plan.availabilityDays) && plan.availabilityDays.length > 0)
            ? plan.availabilityDays
            : ((window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getAvailabilityDays === 'function')
                ? window.TempoEmergencyFlow.getAvailabilityDays()
                : []);
        const activeDays = (availabilityDays || []).filter(d => !d.isUnavailable && d.blocks && d.blocks.length > 0);

        if (activeDays.length > 0) {
            const slots = [];
            activeDays.forEach(day => {
                const intervals = (day.blocks || [])
                    .map(b => ({
                        start: parseTimeToMinutes(b.start),
                        end: parseTimeToMinutes(b.end)
                    }))
                    .filter(intv => intv.end > intv.start)
                    .sort((x, y) => x.start - y.start);

                const merged = [];
                let curr = intervals[0] ? { ...intervals[0] } : null;
                for (let i = 1; i < intervals.length; i++) {
                    const next = intervals[i];
                    if (next.start < curr.end) {
                        curr.end = Math.max(curr.end, next.end);
                    } else {
                        merged.push(curr);
                        curr = { ...next };
                    }
                }
                if (curr) merged.push(curr);

                merged.forEach(slot => {
                    slots.push({
                        dayDate: day.date,
                        dayLabel: day.label,
                        startMin: slot.start,
                        endMin: slot.end,
                        remainingMin: slot.end - slot.start
                    });
                });
            });

            let currentSlotIdx = 0;
            activeItems.forEach((item, idx) => {
                const task = item.task || {};
                const neededMin = task.durationMinutes || 60;
                let allocated = false;

                while (currentSlotIdx < slots.length) {
                    const slot = slots[currentSlotIdx];
                    if (slot.remainingMin >= 15) {
                        const startMinutes = slot.endMin - slot.remainingMin;
                        const durationToUse = Math.min(neededMin, slot.remainingMin);
                        const endMinutes = startMinutes + durationToUse;
                        slot.remainingMin -= durationToUse;

                        item.dayDate = slot.dayDate;
                        item.dayLabel = slot.dayLabel;
                        item.startMin = startMinutes;
                        item.endMin = endMinutes;
                        item.startTime = formatMinutesToTimeString(startMinutes);
                        item.endTime = formatMinutesToTimeString(endMinutes);
                        item.isOverCapacity = false;
                        item.executionBadge = (idx === 0 || task.userLabel === 'Now') ? 'Now' : 'Later';

                        allocated = true;
                        if (slot.remainingMin < 15) currentSlotIdx++;
                        break;
                    } else {
                        currentSlotIdx++;
                    }
                }

                if (!allocated) {
                    const fallbackDay = activeDays[activeDays.length - 1] || activeDays[0];
                    item.dayDate = item.dayDate || (fallbackDay ? fallbackDay.date : null);
                    item.dayLabel = item.dayLabel || (fallbackDay ? fallbackDay.label : null);
                    item.executionBadge = task.userLabel === 'Now' ? 'Now' : 'Later';
                }
            });
        } else {
            activeItems.forEach((item, idx) => {
                const task = item.task || {};
                item.executionBadge = (idx === 0 || task.userLabel === 'Now') ? 'Now' : 'Later';
            });
        }

        plan.plannedTasks = [...activeItems, ...completedItems];

        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
            window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
        }

        persistPlan(plan);

        if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
            window.TempoMode.renderActiveModeHome();
        }
    }

    /**
     * Resolve default task for Global "Start Focus Now" (Section 7)
     * Hierarchy:
     * 1. If an unfinished task is currently IN PROGRESS: suggest that task.
     * 2. Otherwise: suggest first unfinished ARRANGED task in current execution order for today.
     * 3. Do NOT automatically pull an UNARRANGED task.
     * 4. If no appropriate task planned for today: return null (do not push future task automatically).
     */
    function resolveDefaultFocusTask(plan) {
        if (!plan || !plan.plannedTasks || plan.plannedTasks.length === 0) return null;

        const todayStr = getTodayISO();

        // 1. Unfinished task in progress
        const inProgressItem = plan.plannedTasks.find(pt => pt.task && pt.task.isInProgress && !pt.task.completed);
        if (inProgressItem) return inProgressItem.task;

        // 2. First unfinished arranged task planned for today
        const todayTasks = plan.plannedTasks.filter(pt => pt.dayDate === todayStr && pt.task && !pt.task.completed);
        if (todayTasks.length > 0) {
            return todayTasks[0].task;
        }

        // 4. No task planned today -> do not push future task automatically
        return null;
    }

        /**
     * Navigation: Return to Home
     */
    function navigateHome() {
        document.body.style.backgroundColor = '';
        const mainEl = document.querySelector('main');
        if (mainEl) mainEl.style.backgroundColor = '';
        if (window.TempoMode && typeof window.TempoMode.syncModeDOM === 'function') {
            window.TempoMode.syncModeDOM(window.TempoMode.getMode());
        }
        if (window.TempoMode && typeof window.TempoMode.navigateToActiveDashboard === 'function') {
            window.TempoMode.navigateToActiveDashboard();
        } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('today');
        } else {
            window.location.hash = '#today';
        }
    }

    /**
     * Start Adjust Plan flow
     */
    function startAdjustPlan() {
        // Clear any open workspace-internal modal to prevent state conflicts
        activeModal = null;
        render();

        const plan = getActivePlan();
        if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.startAdjustmentFlow === 'function') {
            window.TempoUrmodeFlow.startAdjustmentFlow(plan);
        } else if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.startAdjustmentFlow === 'function') {
            window.TempoEmergencyFlow.startAdjustmentFlow(plan);
        } else {
            console.error('[TempoPlanWorkspace] Unable to start Adjust Plan: startAdjustmentFlow handler not found.');
        }
    }

    /**
     * Delete active plan
     */
    function promptDeletePlan() {
        activeModal = 'delete-plan-confirm';
        render();
    }

    function closeDeletePlanConfirm() {
        if (isActionProcessing) return;
        activeModal = null;
        render();
    }

    function executeDeletePlan() {
        if (isActionProcessing) return;
        isActionProcessing = true;

        try {
            if (window.TempoPlanStore && typeof window.TempoPlanStore.archiveActivePlan === 'function') {
                window.TempoPlanStore.archiveActivePlan('emergency');
                window.TempoPlanStore.archiveActivePlan('recovery');
                window.TempoPlanStore.archiveActivePlan('default');
            }

            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.resetFlowState === 'function') {
                window.TempoEmergencyFlow.resetFlowState();
            }

            try {
                const currentUserId = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') 
                    ? window.TempoAuth.getCurrentUserId() 
                    : ((window.TempoPlanStore && typeof window.TempoPlanStore.getUserId === 'function') ? window.TempoPlanStore.getUserId() : 'guest');
                if (currentUserId && currentUserId !== 'guest') {
                    localStorage.removeItem(`tempo_working_plan_${currentUserId}`);
                    localStorage.removeItem(`tempo_rmode_mock_tasks_${currentUserId}`);
                }
                localStorage.removeItem('tempo_working_plan');
                localStorage.removeItem('tempo_active_plan');
                localStorage.removeItem('tempo_store_active_emergency_guest');
            } catch(e) {}

            activeModal = null;

            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Your Working Plan has been deleted.");
            }

            navigateHome();
        } finally {
            isActionProcessing = false;
        }
    }

    function deletePlan() {
        promptDeletePlan();
    }

    /**
     * Open Workspace
     */
    function open() {
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
    }

    /**
     * Global Start Focus Now
     */
    function startGlobalFocus() {
        const plan = getActivePlan();
        const defaultTask = resolveDefaultFocusTask(plan);

        if (defaultTask && window.TempoFocusZone) {
            window.TempoFocusZone.open({ taskId: defaultTask.id });
        } else if (window.TempoFocusZone) {
            // No task planned for today -> open quick entry allowing choice or focus without task
            window.TempoFocusZone.openQuickEntry();
        }
    }

    /**
     * Start Focus for a specific task
     */
    function startTaskFocus(taskId) {
        if (window.TempoFocusZone) {
            window.TempoFocusZone.open({ taskId: taskId });
        }
    }

        /**
     * Toggle task completion on shared task
     */
    function toggleTaskComplete(taskId, e) {
        if (e && e.stopPropagation) e.stopPropagation();
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        let pt = plan.plannedTasks ? plan.plannedTasks.find(item => item.task && item.task.id === taskId) : null;
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => (t.task ? t.task.id === taskId : t.id === taskId));
            if (task && task.task) task = task.task;
        }

        if (task) {
            task.completed = !task.completed;
            if (task.completed) {
                task.isInProgress = false;
                task.executionStatus = 'completed';
                task.completedAt = Date.now();
                clearMissedScheduleDismissal(taskId);

                // If the selected task became completed, select the next appropriate active task
                if (selectedTaskId === taskId) {
                    const allActive = [];
                    if (Array.isArray(plan.plannedTasks)) {
                        plan.plannedTasks.forEach(item => {
                            if (item.task && !item.task.completed && item.task.id !== taskId) {
                                allActive.push(item.task);
                            }
                        });
                    }
                    if (Array.isArray(plan.unarrangedTasks)) {
                        plan.unarrangedTasks.forEach(u => {
                            const t = u.task ? u.task : u;
                            if (t && !t.completed && t.id !== taskId) {
                                allActive.push(t);
                            }
                        });
                    }
                    if (allActive.length > 0) {
                        selectedTaskId = allActive[0].id;
                    }
                }
            } else {
                task.executionStatus = 'pending';
                delete task.completedAt;
                selectedTaskId = taskId;
            }

            // Sync with TempoEmergencyFlow explicitly
            if (window.TempoEmergencyFlow) {
                if (typeof window.TempoEmergencyFlow.setTaskCompleted === 'function') {
                    window.TempoEmergencyFlow.setTaskCompleted(taskId, task.completed);
                } else if (typeof window.TempoEmergencyFlow.toggleTaskCompleted === 'function') {
                    const cur = (window.TempoEmergencyFlow.isTaskCompleted && window.TempoEmergencyFlow.isTaskCompleted(taskId));
                    if (cur !== task.completed) {
                        window.TempoEmergencyFlow.toggleTaskCompleted(taskId);
                    }
                }
            }

            // Sync with planStore
            if (window.TempoPlanStore && typeof window.TempoPlanStore.updateTaskState === 'function') {
                window.TempoPlanStore.updateTaskState(taskId, {
                    completed: task.completed,
                    isInProgress: task.isInProgress,
                    executionStatus: task.executionStatus
                });
            }

            // Sync mock state for Rmode if applicable
            try {
                let mockTasks = {};
                try {
                    mockTasks = JSON.parse(localStorage.getItem('tempo_rmode_mock_tasks') || '{}');
                } catch(e) {}
                if (taskId === 'task-marketing-research') mockTasks['rmode-mock-1'] = task.completed;
                if (taskId === 'task-event-proposal') mockTasks['rmode-mock-2'] = task.completed;
                if (taskId === 'task-edit-video') mockTasks['rmode-mock-3'] = task.completed;
                mockTasks[taskId] = task.completed;
                localStorage.setItem('tempo_rmode_mock_tasks', JSON.stringify(mockTasks));
            } catch(e) {}

            persistPlan(plan);
            render();

            if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
                window.TempoMode.renderActiveModeHome();
            }
        }
    }

    /**
     * Select a task to view/edit in the Detail Drawer
     */
    function selectTask(taskId) {
        selectedTaskId = taskId;
        isEditingDeadline = false;
        render();
    }

    /**
     * Close the Detail Drawer
     */
    function closeDrawer() {
        selectedTaskId = null;
        isEditingDeadline = false;
        render();
    }

    /**
     * Inline Deadline Edit toggle
     */
    function toggleDeadlineEdit() {
        isEditingDeadline = !isEditingDeadline;
        render();
    }

    /**
     * Save inline deadline edit
     */
    function saveDeadlineEdit(taskId) {
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        let ptItem = null;
        ptItem = (plan.plannedTasks || []).find(item => item.task && item.task.id === taskId);
        if (ptItem) task = ptItem.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }
        if (!task) return;

        const dateInput = document.getElementById('pw-edit-deadline-date');
        const timeInput = document.getElementById('pw-edit-deadline-time');
        const noFixedCheck = document.getElementById('pw-edit-no-deadline');

        const hasNoFixed = noFixedCheck ? noFixedCheck.checked : false;
        const dateVal = dateInput ? dateInput.value : '';
        const timeVal = timeInput ? timeInput.value : '';

        const hasDeadline = !hasNoFixed && !!dateVal;
        const newDate = hasNoFixed ? null : (dateVal || null);
        const newTime = hasNoFixed ? null : (timeVal || '23:59');

        const oldDate = task.deadlineDate;
        const oldTime = task.deadlineTime || '23:59';
        const oldHasDeadline = !!task.hasDeadline;

        if (hasDeadline === oldHasDeadline && newDate === oldDate && newTime === oldTime) {
            isEditingDeadline = false;
            render();
            return;
        }

        // Check if new deadline creates a conflict or alters relative priority/urgency of tasks
        let createsConflict = false;
        if (ptItem && hasDeadline && newDate) {
            if (ptItem.dayDate && ptItem.dayDate > newDate) {
                createsConflict = true;
            } else if (ptItem.dayDate && ptItem.dayDate === newDate && ptItem.endTime && ptItem.endTime > newTime) {
                createsConflict = true;
            }
        }

        let altersPriorityOrder = false;
        const activeTasks = (plan.plannedTasks || [])
            .filter(item => item.task && !item.task.completed)
            .map(item => item.task);

        const currentIdx = activeTasks.findIndex(t => t.id === taskId);
        if (currentIdx !== -1 && hasDeadline && newDate) {
            const newDeadlineStr = newDate + ' ' + newTime;
            // Check if there is any task scheduled before current task that now has a later deadline
            for (let i = 0; i < currentIdx; i++) {
                const beforeTask = activeTasks[i];
                if (beforeTask.hasDeadline && beforeTask.deadlineDate) {
                    const beforeDeadlineStr = beforeTask.deadlineDate + ' ' + (beforeTask.deadlineTime || '23:59');
                    if (newDeadlineStr < beforeDeadlineStr) {
                        altersPriorityOrder = true;
                        break;
                    }
                } else if (!beforeTask.hasDeadline) {
                    altersPriorityOrder = true;
                    break;
                }
            }
            if (!altersPriorityOrder) {
                for (let i = currentIdx + 1; i < activeTasks.length; i++) {
                    const afterTask = activeTasks[i];
                    if (afterTask.hasDeadline && afterTask.deadlineDate) {
                        const afterDeadlineStr = afterTask.deadlineDate + ' ' + (afterTask.deadlineTime || '23:59');
                        if (newDeadlineStr > afterDeadlineStr) {
                            altersPriorityOrder = true;
                            break;
                        }
                    }
                }
            }
        }

        if (createsConflict || altersPriorityOrder) {
            pendingDeadlineEdit = {
                taskId: taskId,
                hasDeadline: hasDeadline,
                deadlineDate: newDate,
                deadlineTime: newTime
            };
            activeModal = 'deadline-plan-reorder-confirm';
            render();
            return;
        }

        // Save directly if no material conflict
        applyDeadlineChange(taskId, hasDeadline, newDate, newTime, false);
    }

    function confirmDeadlineWithReorder() {
        if (!pendingDeadlineEdit) return;
        applyDeadlineChange(pendingDeadlineEdit.taskId, pendingDeadlineEdit.hasDeadline, pendingDeadlineEdit.deadlineDate, pendingDeadlineEdit.deadlineTime, true);
    }

    function confirmDeadlineWithoutReorder() {
        if (!pendingDeadlineEdit) return;
        applyDeadlineChange(pendingDeadlineEdit.taskId, pendingDeadlineEdit.hasDeadline, pendingDeadlineEdit.deadlineDate, pendingDeadlineEdit.deadlineTime, false);
    }

    function cancelDeadlineConfirm() {
        pendingDeadlineEdit = null;
        activeModal = null;
        render();
    }

    function applyDeadlineChange(taskId, hasDeadline, newDate, newTime, shouldReorder) {
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        const pt = (plan.plannedTasks || []).find(item => item.task && item.task.id === taskId);
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }
        if (!task) return;

        task.hasDeadline = hasDeadline;
        task.deadlineDate = newDate;
        task.deadlineTime = newTime;
        task.deadline = hasDeadline ? `${newDate} ${newTime || '23:59'}` : null;
        delete task.isOverdue;
        task.isOverdue = false;

        // Update shared task in tasks array
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getTasks === 'function') {
            const rawTasks = window.TempoEmergencyFlow.getTasks();
            const shared = rawTasks.find(t => t.id === taskId);
            if (shared) {
                shared.hasDeadline = task.hasDeadline;
                shared.deadlineDate = task.deadlineDate;
                shared.deadlineTime = task.deadlineTime;
                shared.deadline = task.deadline;
                delete shared.isOverdue;
                shared.isOverdue = false;
            }
        }

        if (shouldReorder) {
            reorganizePlanWithPlanner(plan);
        } else {
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
                window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
            }
            persistPlan(plan);
            if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
                window.TempoMode.renderActiveModeHome();
            }
        }

        isEditingDeadline = false;
        pendingDeadlineEdit = null;
        activeModal = null;
        render();
    }

    /**
     * Label (Now / Later) dropdown and AI replan
     */
    function toggleLabelMenu(taskId, event) {
        if (event) {
            event.stopPropagation();
        }
        activeLabelMenuTaskId = (activeLabelMenuTaskId === taskId ? null : taskId);
        render();
    }

    function setTaskLabel(taskId, newLabel) {
        activeLabelMenuTaskId = null;
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        const pt = (plan.plannedTasks || []).find(item => item.task && item.task.id === taskId);
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }
        if (!task) return;

        task.userLabel = newLabel;
        task.priorityCategory = (newLabel === 'Now') ? 'DO_FIRST' : 'LATER';

        // Update shared task
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getTasks === 'function') {
            const raw = window.TempoEmergencyFlow.getTasks();
            const shared = raw.find(t => t.id === taskId);
            if (shared) {
                shared.userLabel = newLabel;
                shared.priorityCategory = task.priorityCategory;
            }
        }

        reorganizePlanWithPlanner(plan);
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(`Priority updated to ${newLabel}. Plan reorganized.`);
        }
        render();
    }

    /**
     * Open Break Task modal
     */
    function openBreakTaskModal(taskId) {
        const targetId = taskId || selectedTaskId;
        if (!targetId) return;
        if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.renderBreakTaskPopup === 'function') {
            window.TempoUrmodeFlow.renderBreakTaskPopup(targetId);
        } else if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.startBreakTaskFlow === 'function') {
            window.TempoUrmodeFlow.startBreakTaskFlow(targetId);
        } else if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.reviewStepBreakdown === 'function') {
            window.TempoEmergencyFlow.reviewStepBreakdown(targetId);
        }
    }

    /**
     * Task Notes management
     */
    function openNoteEditor(taskId) {
        pendingNoteTaskId = taskId || selectedTaskId;
        activeModal = 'edit-task-note';
        render();
    }

    function saveNote(taskId) {
        const targetId = taskId || pendingNoteTaskId || selectedTaskId;
        if (!targetId) return;

        const input = document.getElementById('pw-note-editor-text');
        const text = input ? input.value : '';

        const plan = getActivePlan();
        let targetTask = null;
        if (plan && plan.plannedTasks) {
            const pt = plan.plannedTasks.find(item => item.task && item.task.id === targetId);
            if (pt) targetTask = pt.task;
        }
        if (!targetTask && plan && plan.unarrangedTasks) {
            targetTask = plan.unarrangedTasks.find(t => t.id === targetId);
        }
        const taskName = targetTask ? targetTask.name : 'Academic Task';

        if (window.TempoToolNotes && typeof window.TempoToolNotes.saveTaskNote === 'function') {
            window.TempoToolNotes.saveTaskNote(targetId, taskName, text);
        }

        if (targetTask) {
            targetTask.note = text.trim();
            targetTask.description = text.trim();
        }

        persistPlan(plan);
        activeModal = null;
        pendingNoteTaskId = null;
        render();
    }

    function deleteNote(taskId) {
        const targetId = taskId || pendingNoteTaskId || selectedTaskId;
        if (!targetId) return;

        if (window.TempoToolNotes && typeof window.TempoToolNotes.deleteTaskNote === 'function') {
            window.TempoToolNotes.deleteTaskNote(targetId);
        }

        const plan = getActivePlan();
        if (plan && plan.plannedTasks) {
            const pt = plan.plannedTasks.find(item => item.task && item.task.id === targetId);
            if (pt && pt.task) {
                pt.task.note = '';
                pt.task.description = '';
            }
        }
        if (plan && plan.unarrangedTasks) {
            const u = plan.unarrangedTasks.find(t => t.id === targetId);
            if (u) {
                u.note = '';
                u.description = '';
            }
        }

        persistPlan(plan);
        activeModal = null;
        pendingNoteTaskId = null;
        render();
    }

    function closeModal() {
        activeModal = null;
        pendingDeadlineEdit = null;
        pendingNoteTaskId = null;
        render();
    }

    /**
     * Open Tempo Estimate Editor for task (reuses existing modal)
     */
    function openEstimateEdit(taskId) {
        const plan = getActivePlan();
        if (!plan) return;

        const taskIndex = plan.plannedTasks.findIndex(pt => pt.task && pt.task.id === taskId);
        if (taskIndex !== -1 && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.openEditEstimateModal === 'function') {
            window.TempoEmergencyFlow.openEditEstimateModal(taskIndex);
        } else if (window.TempoApp) {
            window.TempoApp.showToast("Edit estimate via plan review.");
        }
    }

        /**
     * Remove task from plan
     */
    function promptClearTask(taskId) {
        pendingClearTaskId = taskId || selectedTaskId;
        activeModal = 'clear-task-confirm';
        render();
    }

    function closeClearTaskConfirm() {
        if (isActionProcessing) return;
        activeModal = null;
        pendingClearTaskId = null;
        render();
    }

    function executeClearTask() {
        if (isActionProcessing) return;
        isActionProcessing = true;

        try {
            const taskId = pendingClearTaskId || selectedTaskId;
            if (!taskId) {
                activeModal = null;
                render();
                return;
            }

            const plan = getActivePlan();
            if (!plan) {
                activeModal = null;
                render();
                return;
            }

            // Check plannedTasks
            if (Array.isArray(plan.plannedTasks)) {
                const ptIdx = plan.plannedTasks.findIndex(pt => pt.task && pt.task.id === taskId);
                if (ptIdx !== -1) {
                    plan.plannedTasks.splice(ptIdx, 1);
                    if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
                        window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
                    }
                }
            }

            // Check unarrangedTasks
            if (Array.isArray(plan.unarrangedTasks)) {
                const unIdx = plan.unarrangedTasks.findIndex(t => (t.task ? t.task.id === taskId : t.id === taskId));
                if (unIdx !== -1) {
                    plan.unarrangedTasks.splice(unIdx, 1);
                }
            }

            // Check tasks
            if (Array.isArray(plan.tasks)) {
                const tIdx = plan.tasks.findIndex(t => t.id === taskId);
                if (tIdx !== -1) {
                    plan.tasks.splice(tIdx, 1);
                }
            }

            // Auto-select next available task
            if (selectedTaskId === taskId) {
                const remaining = [];
                if (Array.isArray(plan.plannedTasks)) {
                    plan.plannedTasks.forEach(item => {
                        if (item.task) remaining.push(item.task);
                    });
                }
                if (Array.isArray(plan.unarrangedTasks)) {
                    plan.unarrangedTasks.forEach(u => {
                        const t = u.task ? u.task : u;
                        if (t) remaining.push(t);
                    });
                }
                const activeRemaining = remaining.find(t => !t.completed);
                selectedTaskId = activeRemaining ? activeRemaining.id : (remaining.length > 0 ? remaining[0].id : null);
            }

            persistPlan(plan);
            activeModal = null;
            pendingClearTaskId = null;
            render();
        } finally {
            isActionProcessing = false;
        }
    }

    function removeTask(taskId) {
        promptClearTask(taskId);
    }

    function toggleAddSubtaskInput() {
        showAddSubtaskInput = !showAddSubtaskInput;
        render();
    }

    /**
     * Subtask management inside drawer
     */
    function addSubtask(taskId) {
        const input = document.getElementById('pw-new-subtask-title');
        const title = input ? input.value.trim() : '';
        if (!title) return;

        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        const pt = plan.plannedTasks.find(item => item.task && item.task.id === taskId);
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }
        if (!task) return;

        if (!Array.isArray(task.subtasks)) task.subtasks = [];
        task.subtasks.push({
            id: 'sub_' + Date.now(),
            title: title,
            durationMinutes: 15,
            completed: false
        });

        persistPlan(plan);
        render();
    }

    function removeSubtask(taskId, subtaskId) {
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        const pt = plan.plannedTasks.find(item => item.task && item.task.id === taskId);
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }
        if (!task || !task.subtasks) return;

        task.subtasks = task.subtasks.filter(s => s.id !== subtaskId);
        persistPlan(plan);
        render();
    }

    function setSubtaskCompleted(taskId, subtaskId, isCompleted) {
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        if (Array.isArray(plan.plannedTasks)) {
            const pt = plan.plannedTasks.find(item => item.task && String(item.task.id) === String(taskId));
            if (pt) task = pt.task;
        }
        if (!task && Array.isArray(plan.unarrangedTasks)) {
            const u = plan.unarrangedTasks.find(item => String(item && item.task ? item.task.id : item.id) === String(taskId));
            if (u) task = u.task || u;
        }
        if (!task && Array.isArray(plan.tasks)) {
            task = plan.tasks.find(t => String(t.id) === String(taskId));
        }
        if (!task || !Array.isArray(task.subtasks)) return;

        const sub = task.subtasks.find(s => String(s.id) === String(subtaskId));
        if (sub) {
            sub.completed = Boolean(isCompleted);
            persistPlan(plan);
            if (window.TempoPlanStore && typeof window.TempoPlanStore.updateSubtaskState === 'function') {
                window.TempoPlanStore.updateSubtaskState(taskId, subtaskId, { completed: sub.completed });
            }
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                window.TempoEmergencyFlow.setConfirmedPlan(plan);
            }
            if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
                window.TempoMode.renderActiveModeHome();
            }
            render();
        }
    }

    function toggleSubtask(taskId, subtaskId) {
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        if (Array.isArray(plan.plannedTasks)) {
            const pt = plan.plannedTasks.find(item => item.task && String(item.task.id) === String(taskId));
            if (pt) task = pt.task;
        }
        if (!task && Array.isArray(plan.unarrangedTasks)) {
            const u = plan.unarrangedTasks.find(item => String(item && item.task ? item.task.id : item.id) === String(taskId));
            if (u) task = u.task || u;
        }
        if (!task && Array.isArray(plan.tasks)) {
            task = plan.tasks.find(t => String(t.id) === String(taskId));
        }
        if (!task || !Array.isArray(task.subtasks)) return;

        const sub = task.subtasks.find(s => String(s.id) === String(subtaskId));
        if (sub) {
            sub.completed = !sub.completed;
            persistPlan(plan);
            if (window.TempoPlanStore && typeof window.TempoPlanStore.updateSubtaskState === 'function') {
                window.TempoPlanStore.updateSubtaskState(taskId, subtaskId, { completed: sub.completed });
            }
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                window.TempoEmergencyFlow.setConfirmedPlan(plan);
            }
            if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
                window.TempoMode.renderActiveModeHome();
            }
            render();
        }
    }

    function reorderDrawerSubtask(taskId, fromIdx, toIdx) {
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        const pt = plan.plannedTasks.find(item => item.task && item.task.id === taskId);
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }
        if (!task || !task.subtasks) return;
        if (fromIdx < 0 || fromIdx >= task.subtasks.length || toIdx < 0 || toIdx >= task.subtasks.length) return;

        const [moved] = task.subtasks.splice(fromIdx, 1);
        task.subtasks.splice(toIdx, 0, moved);

        persistPlan(plan);
        render();
    }

    // =========================================================================
    // TASK DRAG AND DROP REORDERING
    // =========================================================================
    let draggedGlobalIndex = null;
    let isDraggingTask = false;

    function handleDragStart(e, globalIndex) {
        // Prevent drag initiation from buttons, links, or form controls inside the card
        if (e.target && e.target.closest && e.target.closest('button, input, select, textarea, a, .btn-primary')) {
            e.preventDefault();
            return false;
        }
        draggedGlobalIndex = globalIndex;
        isDraggingTask = true;
        document.body.classList.add('is-dragging-card');
        if (e.dataTransfer) {
            e.dataTransfer.setData('text/plain', String(globalIndex));
            e.dataTransfer.effectAllowed = 'move';
        }
        const card = e.currentTarget.closest('.workspace-task-card') || e.currentTarget;
        if (card) {
            card.classList.add('em-card-dragging', 'opacity-60', 'border-dashed', 'border-[#FF6B2C]', 'shadow-lg');
            card.classList.remove('opacity-40');
        }
        const handle = card ? card.querySelector('.workspace-drag-handle') : null;
        if (handle) {
            handle.classList.add('is-grabbing');
        }
    }

    function handleDragOver(e) {
        e.preventDefault();
        if (e.dataTransfer) {
            e.dataTransfer.dropEffect = 'move';
        }
    }

    function handleDragEnter(e) {
        e.preventDefault();
        const card = e.currentTarget.closest('.workspace-task-card');
        if (card && draggedGlobalIndex !== null) {
            const targetIdx = parseInt(card.getAttribute('data-global-index'), 10);
            if (!isNaN(targetIdx) && targetIdx !== draggedGlobalIndex) {
                card.classList.add('em-drop-target', 'bg-orange-50/60', 'border-[#FF6B2C]');
                if (draggedGlobalIndex > targetIdx) {
                    card.classList.add('border-t-2', 'border-t-[#FF6B2C]');
                    card.classList.remove('border-b-2', 'border-b-[#FF6B2C]');
                } else {
                    card.classList.add('border-b-2', 'border-b-[#FF6B2C]');
                    card.classList.remove('border-t-2', 'border-t-[#FF6B2C]');
                }
            }
        }
    }

    function handleDragLeave(e) {
        const card = e.currentTarget.closest('.workspace-task-card');
        if (card) {
            if (e.relatedTarget && card.contains(e.relatedTarget)) return;
            card.classList.remove('em-drop-target', 'bg-orange-50/60', 'border-[#FF6B2C]', 'border-t-2', 'border-t-[#FF6B2C]', 'border-b-2', 'border-b-[#FF6B2C]');
        }
    }

    function clearTaskDragStyles() {
        draggedGlobalIndex = null;
        isDraggingTask = false;
        document.body.classList.remove('is-dragging-card');
        document.querySelectorAll('.workspace-task-card').forEach(el => {
            el.classList.remove(
                'em-card-dragging',
                'opacity-60',
                'opacity-40',
                'shadow-lg',
                'border-dashed',
                'em-drop-target',
                'bg-orange-50/60',
                'border-[#FF6B2C]',
                'border-t-2',
                'border-t-[#FF6B2C]',
                'border-b-2',
                'border-b-[#FF6B2C]'
            );
        });
        document.querySelectorAll('.workspace-drag-handle').forEach(h => {
            h.classList.remove('is-grabbing');
        });
    }

    function handleDrop(e, targetGlobalIndex) {
        e.preventDefault();
        e.stopPropagation();
        let fromIdx = draggedGlobalIndex;
        if (fromIdx === null && e.dataTransfer) {
            const raw = e.dataTransfer.getData('text/plain');
            if (raw) fromIdx = parseInt(raw, 10);
        }
        clearTaskDragStyles();

        if (fromIdx !== null && !isNaN(fromIdx) && fromIdx !== targetGlobalIndex) {
            reorderTasks(fromIdx, targetGlobalIndex);
        }
    }

    function handleDragEnd(e) {
        clearTaskDragStyles();
    }

    function reorderTasks(fromIndex, toIndex) {
        const plan = getActivePlan();
        if (!plan || !plan.plannedTasks) return;
        if (fromIndex < 0 || fromIndex >= plan.plannedTasks.length) return;
        if (toIndex < 0 || toIndex >= plan.plannedTasks.length) return;
        if (fromIndex === toIndex) return;

        const targetItem = plan.plannedTasks[toIndex];
        const targetDayDate = targetItem.dayDate;
        const targetDayLabel = targetItem.dayLabel;

        const [movedItem] = plan.plannedTasks.splice(fromIndex, 1);
        movedItem.dayDate = targetDayDate;
        if (targetDayLabel) movedItem.dayLabel = targetDayLabel;

        plan.plannedTasks.splice(toIndex, 0, movedItem);

        persistPlan(plan);
        render();
    }

    /**
     * Scheduling / Rescheduling Modal
     */
    function openRescheduleModal(taskId) {
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
    }

    function closeRescheduleModal() {
        activeModal = null;
        rescheduleTaskId = null;
        rescheduleSelectedWindow = null;
        rescheduleSelectedSlot = null;
        rescheduleShowAddTime = false;
        render();
    }

    function toggleRescheduleAddTime(show) {
        rescheduleShowAddTime = Boolean(show);
        render();
    }

    function selectRescheduleSlot(date, slotId, start, end) {
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
    }

    async function saveRescheduleAvailability() {
        const dateInput = document.getElementById('pw-resched-avail-date');
        const startInput = document.getElementById('pw-resched-avail-start');
        const endInput = document.getElementById('pw-resched-avail-end');
        const errorContainer = document.getElementById('pw-resched-avail-error');

        const showError = (msg) => {
            if (errorContainer) {
                errorContainer.textContent = msg;
                errorContainer.classList.remove('hidden');
            } else {
                alert(msg);
            }
        };

        const date = dateInput ? dateInput.value.trim() : '';
        const start = startInput ? startInput.value.trim() : '';
        const end = endInput ? endInput.value.trim() : '';
        const isVi = isViLocale();

        // 1. Required fields
        if (!date || !start || !end) {
            showError(isVi ? 'Vui lòng nhập đầy đủ ngày, thời gian bắt đầu và thời gian kết thúc.' : 'Please enter date, start time, and end time.');
            return;
        }

        // 2. End time must be later than start time
        if (end <= start) {
            showError(isVi ? 'Thời gian kết thúc phải sau thời gian bắt đầu.' : 'End time must be later than start time.');
            return;
        }

        // 3. Do not allow past time slots
        const todayStr = getLocalTodayISO();
        const currentTimeStr = getLocalCurrentTimeStr();

        if (date < todayStr) {
            showError(isVi ? 'Không thể thêm thời gian làm việc cho ngày đã qua.' : 'Cannot add availability for a past date.');
            return;
        }
        if (date === todayStr && end <= currentTimeStr) {
            showError(isVi ? 'Không thể thêm thời gian làm việc trong quá khứ.' : 'Cannot add availability for past time.');
            return;
        }

        const plan = getActivePlan();
        if (!plan) return;

        // 4. Prevent duplicate or overlapping availability slots
        if (!plan.availabilityDays) plan.availabilityDays = [];
        let day = plan.availabilityDays.find(d => d.date === date);

        if (day && Array.isArray(day.blocks)) {
            const exactMatch = day.blocks.find(b => b.start === start && b.end === end);
            if (exactMatch) {
                // Exact slot already exists -> select it directly
                rescheduleSelectedSlot = {
                    id: exactMatch.id,
                    date: date,
                    start: start,
                    end: end
                };
                rescheduleSelectedWindow = date;
                rescheduleShowAddTime = false;
                render();
                return;
            }

            const overlapping = day.blocks.filter(b => start < b.end && end > b.start);
            if (overlapping.length > 0) {
                // Merge new slot with overlapping blocks seamlessly
                let mergedStart = start;
                let mergedEnd = end;
                overlapping.forEach(b => {
                    if (b.start < mergedStart) mergedStart = b.start;
                    if (b.end > mergedEnd) mergedEnd = b.end;
                });
                day.blocks = day.blocks.filter(b => !(start < b.end && end > b.start));
                const mergedId = overlapping[0].id || ('b_' + Date.now());
                day.blocks.push({
                    id: mergedId,
                    start: mergedStart,
                    end: mergedEnd
                });
                day.blocks.sort((a, b) => a.start.localeCompare(b.start));

                await persistPlan(plan);

                rescheduleSelectedSlot = {
                    id: mergedId,
                    date: date,
                    start: mergedStart,
                    end: mergedEnd
                };
                rescheduleSelectedWindow = date;
                rescheduleShowAddTime = false;
                render();
                return;
            }
        }

        // 5. Check conflicts with existing scheduled tasks (excluding the task currently being rescheduled)
        if (Array.isArray(plan.plannedTasks)) {
            for (const pt of plan.plannedTasks) {
                const t = pt.task;
                if (!t || t.completed === true || t.isCompleted === true || t.status === 'completed') continue;
                if (t.id === rescheduleTaskId) continue;
                if (pt.dayDate === date) {
                    const ptStart = pt.startTime || pt.scheduledStartTime;
                    const ptEnd = pt.endTime || pt.scheduledEndTime;
                    if (ptStart && ptEnd) {
                        if (start < ptEnd && end > ptStart) {
                            showError(isVi
                                ? `Khung giờ này trùng với task đã lên lịch: "${t.name}" (${formatTime12H(ptStart)} – ${formatTime12H(ptEnd)}).`
                                : `This time slot conflicts with an already scheduled task: "${t.name}" (${formatTime12H(ptStart)} – ${formatTime12H(ptEnd)}).`);
                            return;
                        }
                    }
                }
            }
        }

        // 6. Validation passed -> create or update day in existing Availability
        if (!day) {
            day = {
                date: date,
                label: formatScheduledDateLabel(date, isVi) || date,
                isUnavailable: false,
                blocks: []
            };
            plan.availabilityDays.push(day);
            plan.availabilityDays.sort((a, b) => a.date.localeCompare(b.date));
        }

        if (!Array.isArray(day.blocks)) day.blocks = [];
        const newBlockId = 'b_' + Date.now();
        day.blocks.push({
            id: newBlockId,
            start: start,
            end: end
        });
        day.blocks.sort((a, b) => a.start.localeCompare(b.start));

        // Sync with TempoEmergencyFlow so it has updated availability
        if (window.TempoEmergencyFlow) {
            if (typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                window.TempoEmergencyFlow.setConfirmedPlan(plan);
            }
            if (typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
                window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
            }
        }

        // Save Availability
        await persistPlan(plan);

        // Make the newly added slot selectable in the current Reschedule Modal
        rescheduleSelectedSlot = {
            id: newBlockId,
            date: date,
            start: start,
            end: end
        };
        rescheduleSelectedWindow = date;
        rescheduleShowAddTime = false;
        render();
    }

    async function scheduleTaskAsUnarranged(taskId) {
        const plan = getActivePlan();
        if (!plan) return;

        const ptIdx = plan.plannedTasks.findIndex(pt => pt.task && pt.task.id === taskId);
        if (ptIdx !== -1) {
            const [item] = plan.plannedTasks.splice(ptIdx, 1);
            const task = item.task;
            task.scheduledDate = null;
            task.dayDate = null;
            task._dayDate = null;
            task.startTime = null;
            task.endTime = null;
            task._endTime = null;
            task.scheduledStartTime = null;
            task.scheduledEndTime = null;
            task.executionBadge = null;

            if (!plan.unarrangedTasks) plan.unarrangedTasks = [];
            if (!plan.unarrangedTasks.some(t => t.id === task.id)) {
                plan.unarrangedTasks.push(task);
            }

            if (window.TempoEmergencyFlow) {
                if (typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                    window.TempoEmergencyFlow.setConfirmedPlan(plan);
                }
                if (typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
                    window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
                }
            }

            clearMissedScheduleDismissal(taskId);
            await persistPlan(plan);
        }

        activeModal = null;
        rescheduleTaskId = null;
        rescheduleSelectedSlot = null;
        rescheduleSelectedWindow = null;
        render();
    }

    async function executeReschedule(taskId, targetSlotOrDay) {
        const errorContainer = document.getElementById('pw-reschedule-error');
        const scheduleBtn = document.getElementById('btn-execute-reschedule');
        const isVi = isViLocale();

        const showModalError = (msg) => {
            if (errorContainer) {
                errorContainer.textContent = msg;
                errorContainer.classList.remove('hidden');
            } else {
                alert(msg);
            }
        };

        const hideModalError = () => {
            if (errorContainer) {
                errorContainer.textContent = '';
                errorContainer.classList.add('hidden');
            }
        };

        hideModalError();

        const plan = getActivePlan();
        if (!plan) {
            showModalError(isVi ? 'Không tìm thấy kế hoạch làm việc.' : 'Working plan not found.');
            return;
        }

        // Resolve selected slot
        let selectedSlot = null;
        if (targetSlotOrDay && typeof targetSlotOrDay === 'object') {
            selectedSlot = targetSlotOrDay;
        } else if (rescheduleSelectedSlot && rescheduleSelectedSlot.date) {
            selectedSlot = rescheduleSelectedSlot;
        } else {
            // Check DOM checked radio
            const checkedRadio = document.querySelector('input[name="pw_reschedule_slot"]:checked') ||
                                 document.querySelector('input[name="pw_reschedule_day"]:checked');
            if (checkedRadio) {
                const rDate = checkedRadio.getAttribute('data-date') || checkedRadio.value;
                const rStart = checkedRadio.getAttribute('data-start') || '';
                const rEnd = checkedRadio.getAttribute('data-end') || '';
                const rSlotId = checkedRadio.getAttribute('data-slot-id') || checkedRadio.value;
                selectedSlot = {
                    id: rSlotId,
                    date: rDate,
                    start: rStart || null,
                    end: rEnd || null
                };
            } else if (typeof targetSlotOrDay === 'string' && targetSlotOrDay) {
                selectedSlot = {
                    id: `day_${targetSlotOrDay}`,
                    date: targetSlotOrDay,
                    start: null,
                    end: null
                };
            }
        }

        if (!selectedSlot || !selectedSlot.date) {
            showModalError(isVi ? 'Vui lòng chọn một khung thời gian làm việc.' : 'Please select an available time slot.');
            return;
        }

        // If slot start/end was not provided, try to find from plan.availabilityDays
        if ((!selectedSlot.start || !selectedSlot.end) && plan.availabilityDays) {
            const dayObj = plan.availabilityDays.find(d => d.date === selectedSlot.date);
            if (dayObj && Array.isArray(dayObj.blocks) && dayObj.blocks.length > 0) {
                const blk = selectedSlot.id ? dayObj.blocks.find(b => b.id === selectedSlot.id) : dayObj.blocks[0];
                const chosen = blk || dayObj.blocks[0];
                if (chosen) {
                    selectedSlot.start = chosen.start;
                    selectedSlot.end = chosen.end;
                    selectedSlot.id = chosen.id;
                }
            }
        }

        // Locate task
        let task = null;
        const ptIdx = Array.isArray(plan.plannedTasks) ? plan.plannedTasks.findIndex(pt => pt.task && pt.task.id === taskId) : -1;
        if (ptIdx !== -1) {
            task = plan.plannedTasks[ptIdx].task;
        } else if (Array.isArray(plan.unarrangedTasks)) {
            const unIdx = plan.unarrangedTasks.findIndex(t => (t && t.task ? t.task.id : t.id) === taskId);
            if (unIdx !== -1) {
                const u = plan.unarrangedTasks[unIdx];
                task = u && u.task ? u.task : u;
            }
        } else if (Array.isArray(plan.tasks)) {
            task = plan.tasks.find(t => t.id === taskId);
        }

        if (!task) {
            showModalError(isVi ? 'Không tìm thấy task cần xếp lại lịch.' : 'Task to reschedule was not found.');
            return;
        }

        // Show loading state on button
        if (scheduleBtn) {
            scheduleBtn.disabled = true;
            scheduleBtn.classList.add('opacity-75', 'cursor-not-allowed');
            scheduleBtn.setAttribute('data-original-text', scheduleBtn.innerHTML);
            scheduleBtn.innerHTML = `
                <span class="inline-flex items-center space-x-1.5">
                    <svg class="animate-spin h-3.5 w-3.5 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>${isVi ? 'Đang lên lịch...' : 'Scheduling...'}</span>
                </span>
            `;
        }

        try {
            // Remove task from old plannedTasks or unarrangedTasks
            if (ptIdx !== -1) {
                plan.plannedTasks.splice(ptIdx, 1);
            }
            if (Array.isArray(plan.unarrangedTasks)) {
                plan.unarrangedTasks = plan.unarrangedTasks.filter(t => (t && t.task ? t.task.id : t.id) !== taskId);
            }

            // Calculate task start and end times within the chosen slot
            const targetDate = selectedSlot.date;
            const todayStr = getLocalTodayISO();
            const currentTimeStr = getLocalCurrentTimeStr();
            const durationMin = typeof task.durationMinutes === 'number' && task.durationMinutes > 0 ? task.durationMinutes : 60;

            let taskStart = selectedSlot.start || null;
            let taskEnd = selectedSlot.end || null;
            let startMin = null;
            let endMin = null;

            if (taskStart && taskEnd) {
                let slotStartMin = parseTimeToMinutes(taskStart);
                let slotEndMin = parseTimeToMinutes(taskEnd);

                // If scheduled for Today and currentTime has passed slot start (but not slot end), adjust start
                if (targetDate === todayStr) {
                    const currentMin = parseTimeToMinutes(currentTimeStr);
                    if (currentMin > slotStartMin && currentMin < slotEndMin) {
                        slotStartMin = currentMin;
                    }
                }

                startMin = slotStartMin;
                endMin = Math.min(slotStartMin + durationMin, slotEndMin);
                if (endMin <= startMin) endMin = slotEndMin;

                taskStart = formatMinutesToTimeString(startMin);
                taskEnd = formatMinutesToTimeString(endMin);
            }

            // 1. Update the task object itself
            task.scheduledDate = targetDate;
            task.dayDate = targetDate;
            task._dayDate = targetDate;
            task.scheduledStartTime = taskStart;
            task.scheduledEndTime = taskEnd;
            task.startTime = taskStart;
            task.endTime = taskEnd;
            task._endTime = taskEnd;
            task.completed = false;
            task.isCompleted = false;

            // Preserve all deadline / due date fields strictly!
            // task.hasDeadline, task.deadlineDate, task.deadlineTime, task.deadline are NOT modified!

            // 2. Add to plan.plannedTasks
            const dayLabel = formatScheduledDateLabel(targetDate, isVi) || targetDate;
            const newPlannedItem = {
                task: task,
                dayDate: targetDate,
                date: targetDate,
                dayLabel: dayLabel,
                startTime: taskStart,
                endTime: taskEnd,
                scheduledStartTime: taskStart,
                scheduledEndTime: taskEnd,
                startMin: startMin,
                endMin: endMin,
                startMinutes: startMin,
                endMinutes: endMin,
                executionBadge: 'LATER',
                isOverCapacity: false,
                hasDeadlineConflict: checkDeadlineConflict(task, targetDate, endMin || 1440)
            };
            plan.plannedTasks.push(newPlannedItem);

            // Also ensure raw tasks array in plan has updated task
            if (Array.isArray(plan.tasks)) {
                const tIdx = plan.tasks.findIndex(t => t.id === taskId);
                if (tIdx !== -1) {
                    plan.tasks[tIdx] = task;
                } else {
                    plan.tasks.push(task);
                }
            }

            // 3. Sync with TempoEmergencyFlow
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
            }

            // 4. Clear missed schedule prompt dismissal for this task
            clearMissedScheduleDismissal(taskId);

            // 5. Persist to storage & remote database (throws if failed)
            await persistPlan(plan);

            // 6. Success -> close modal and refresh UI
            activeModal = null;
            rescheduleTaskId = null;
            rescheduleSelectedSlot = null;
            rescheduleSelectedWindow = null;
            rescheduleShowAddTime = false;
            selectedTaskId = taskId; // Select rescheduled task in Working Plan view

            render();

            if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
                window.TempoMode.renderActiveModeHome();
            }
        } catch (err) {
            console.error("[TempoPlanWorkspace] Reschedule failed:", err);
            // Failed: keep modal open, preserve selection, display clear error message
            if (scheduleBtn) {
                scheduleBtn.disabled = false;
                scheduleBtn.classList.remove('opacity-75', 'cursor-not-allowed');
                const orig = scheduleBtn.getAttribute('data-original-text');
                scheduleBtn.innerHTML = orig || (window.t ? window.t('workspace.schedule', {}, 'Schedule') : 'Schedule');
            }
            showModalError(isVi
                ? `Không thể xếp lại lịch cho task. ${err.message || 'Vui lòng thử lại.'}`
                : `Could not reschedule task. ${err.message || 'Please try again.'}`);
        }
    }

    function keepCurrentSchedule(taskId) {
        if (!taskId) return;
        const plan = getActivePlan();
        let targetPt = null;
        if (plan && Array.isArray(plan.plannedTasks)) {
            targetPt = plan.plannedTasks.find(pt => pt.task && (pt.task.id === taskId || pt.id === taskId));
        }
        const sDate = targetPt?.dayDate || getLocalTodayISO();
        dismissMissedSchedulePrompt(taskId, sDate);
        render();
        if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
            window.TempoMode.renderActiveModeHome();
        }
    }

    /**
     * Add Task Modal
     */
    function openAddTaskModal() {
        activeModal = 'add-task';
        pendingAddedTask = null;
        render();
    }

    function closeAddTaskModal() {
        activeModal = null;
        pendingAddedTask = null;
        render();
    }

    function submitAddTask() {
        const nameInput = document.getElementById('pw-add-task-name');
        const name = nameInput ? nameInput.value.trim() : '';
        if (!name) {
            alert('Please enter a task name.');
            return;
        }

        const dateInput = document.getElementById('pw-add-task-date');
        const timeInput = document.getElementById('pw-add-task-time');
        const noFixedCheck = document.getElementById('pw-add-task-no-deadline');

        const durValInput = document.getElementById('pw-add-task-dur-val');
        const durUnitInput = document.getElementById('pw-add-task-dur-unit');
        const notSureCheck = document.getElementById('pw-add-task-dur-not-sure');

        const hasNoFixed = noFixedCheck ? noFixedCheck.checked : false;
        const notSure = notSureCheck ? notSureCheck.checked : false;

        let durationMinutes = null;
        if (!notSure && durValInput && durValInput.value) {
            const val = parseFloat(durValInput.value);
            const unit = durUnitInput ? durUnitInput.value : 'hours';
            if (val > 0) {
                durationMinutes = unit === 'hours' ? Math.round(val * 60) : Math.round(val);
            }
        }

        const newTask = {
            id: 'task_' + Date.now(),
            name: name,
            deadlineDate: hasNoFixed ? null : (dateInput ? dateInput.value || null : null),
            deadlineTime: hasNoFixed ? null : (timeInput ? timeInput.value || '23:59' : null),
            hasDeadline: !hasNoFixed && dateInput && !!dateInput.value,
            durationMinutes: durationMinutes || 60,
            durationLabel: durationMinutes ? formatDuration(durationMinutes) : '1h',
            isUnknownDuration: !durationMinutes,
            subtasks: [],
            completed: false,
            isInProgress: false,
            executionStatus: 'pending',
            importance: 'HIGH',
            consequence: 'Standard',
            flexibility: 'SOME'
        };

        pendingAddedTask = newTask;
        activeModal = 'fit-task-prompt';
        render();
    }

    function handleFitTaskChoice(choice) {
        if (!pendingAddedTask) return;
        const plan = getActivePlan();
        if (!plan) return;

        if (choice === 'fit') {
            // Find earliest day in availability
            const todayStr = getTodayISO();
            let targetDay = todayStr;
            if (plan.availabilityDays && plan.availabilityDays.length > 0) {
                targetDay = plan.availabilityDays[0].date;
            }

            plan.plannedTasks.push({
                task: pendingAddedTask,
                dayDate: targetDay,
                dayLabel: formatScheduledDateLabel(targetDay, isViLocale()) || (targetDay === todayStr ? 'TODAY' : targetDay),
                startTime: null,
                endTime: null,
                isOverCapacity: false,
                executionBadge: 'LATER',
                hasDeadlineConflict: false
            });

            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
                window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
            }
        } else {
            // Leave unscheduled
            if (!plan.unarrangedTasks) plan.unarrangedTasks = [];
            plan.unarrangedTasks.push(pendingAddedTask);
        }

        // Also add to raw tasks array
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getTasks === 'function') {
            const rawTasks = window.TempoEmergencyFlow.getTasks();
            rawTasks.push(pendingAddedTask);
        }

        persistPlan(plan);
        activeModal = null;
        pendingAddedTask = null;
        render();
    }

    /**
     * Adjust Availability Modal
     */
    function openAdjustAvailabilityModal() {
        const plan = getActivePlan();
        if (plan) {
            const c1 = cleanupExpiredAvailability(plan);
            const c2 = applyRecurringRulesToPlan(plan);
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
    }

    function addAvailabilityBlockInline() {
        const dateInput = document.getElementById('pw-avail-add-date');
        const startInput = document.getElementById('pw-avail-add-start');
        const endInput = document.getElementById('pw-avail-add-end');

        const date = dateInput ? dateInput.value : '';
        const start = startInput ? startInput.value : '';
        const end = endInput ? endInput.value : '';

        if (!date || !start || !end) {
            alert('Please select date, start time, and end time.');
            return;
        }

        const plan = getActivePlan();
        if (!plan) return;

        if (!plan.availabilityDays) plan.availabilityDays = [];
        let day = plan.availabilityDays.find(d => d.date === date);
        if (!day) {
            day = {
                date: date,
                label: date,
                isUnavailable: false,
                blocks: []
            };
            plan.availabilityDays.push(day);
        }

        if (!Array.isArray(day.blocks)) day.blocks = [];
        day.blocks.push({
            id: 'b_' + Date.now(),
            start: start,
            end: end
        });

        // Recalculate
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
            window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
        }

        persistPlan(plan);
        adjustAvailShowAdd = false;
        render();
    }

    function removeAvailabilityBlock(dayDate, blockId) {
        const plan = getActivePlan();
        if (!plan || !plan.availabilityDays) return;

        const day = plan.availabilityDays.find(d => d.date === dayDate);
        if (day && day.blocks) {
            day.blocks = day.blocks.filter(b => b.id !== blockId);
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
                window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
            }
            persistPlan(plan);
            render();
        }
    }

    /**
     * MAIN RENDER FUNCTION: Tempo Working Plan (Two-column layout matching reference)
     */
    function render() {
        const root = document.getElementById('plan-workspace-root');
        if (!root) return;

        // Ensure light blue background on body and main
        document.body.style.backgroundColor = '#EFFAFF';
        const mainEl = document.querySelector('main');
        if (mainEl) mainEl.style.backgroundColor = '#EFFAFF';

        let plan = getActivePlan();
        if (!plan) {
            const currentUserId = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') 
                ? window.TempoAuth.getCurrentUserId() 
                : 'guest';
            plan = {
                id: `plan_${currentUserId}_working`,
                title: 'Tempo Working Plan',
                availabilityDays: [],
                plannedTasks: [],
                unarrangedTasks: [],
                tasks: []
            };
        }

        // Automatically clean up expired availability slots on load/render
        const availExpiredChanged = cleanupExpiredAvailability(plan);
        const availRecurringChanged = applyRecurringRulesToPlan(plan);
        if (availExpiredChanged || availRecurringChanged) {
            persistPlan(plan);
        }

        const plannedTasks = plan.plannedTasks || [];
        const unarrangedTasks = (plan.unarrangedTasks || []).map(u => (u && u.task ? u.task : u));

        // Group tasks into active vs completed
        const activePlanned = plannedTasks.filter(pt => pt.task && !pt.task.completed);
        const activeUnarranged = unarrangedTasks.filter(t => !t.completed);

        const completedPlanned = plannedTasks.filter(pt => pt.task && pt.task.completed).map(pt => ({
            task: pt.task,
            startTime: pt.startTime || pt.scheduledStartTime,
            endTime: pt.endTime || pt.scheduledEndTime,
            dayLabel: pt.dayLabel,
            dayDate: pt.dayDate
        }));
        const completedUnarranged = unarrangedTasks.filter(t => t.completed).map(t => ({
            task: t,
            startTime: null,
            endTime: null,
            dayLabel: null,
            dayDate: null
        }));

        const allCompleted = [...completedPlanned, ...completedUnarranged];
        allCompleted.sort((a, b) => (b.task.completedAt || 0) - (a.task.completedAt || 0));

        // Total count and completed count
        const totalTasksCount = plannedTasks.length + unarrangedTasks.length;
        const completedTasksCount = allCompleted.length;
        const progressPercent = totalTasksCount > 0 ? Math.round((completedTasksCount / totalTasksCount) * 100) : 0;

        // Auto-select active task if selectedTaskId is unset or missing
        const allTasksFlat = [];
        plannedTasks.forEach(pt => { if (pt.task) allTasksFlat.push(pt.task); });
        unarrangedTasks.forEach(t => { if (t) allTasksFlat.push(t); });

        if (!selectedTaskId || !allTasksFlat.some(t => t.id === selectedTaskId)) {
            const firstActive = activePlanned.length > 0 ? activePlanned[0].task : (activeUnarranged.length > 0 ? activeUnarranged[0] : null);
            if (firstActive) {
                selectedTaskId = firstActive.id;
            } else if (allCompleted.length > 0) {
                selectedTaskId = allCompleted[0].task.id;
            } else if (allTasksFlat.length > 0) {
                selectedTaskId = allTasksFlat[0].id;
            }
        }

        // Find currently selected task and its scheduled metadata
        let selectedTask = allTasksFlat.find(t => t.id === selectedTaskId);
        let selectedPlanItem = plannedTasks.find(pt => pt.task && pt.task.id === selectedTaskId);

        // Group active planned tasks by dayDate
        const todayStr = getLocalTodayISO();
        const tomorrowStr = getLocalTomorrowISO();

        const daysMap = {};
        activePlanned.forEach((item, globalIdx) => {
            item.globalIndex = globalIdx;
            const dDate = item.dayDate || (item.task && item.task.scheduledDate) || 'unscheduled';
            const isVi = isViLocale();
            let dLabel = dDate !== 'unscheduled' ? formatScheduledDateLabel(dDate, isVi) : (item.dayLabel || (isVi ? 'Lịch linh hoạt' : 'Flexible'));

            if (!daysMap[dDate]) {
                daysMap[dDate] = { label: dLabel, date: dDate, items: [] };
            }
            daysMap[dDate].items.push(item);
        });

        // Determine badge for selected task
        const isSelectedNow = selectedTask && (
            selectedTask.userLabel === 'Now' ||
            selectedTask.priorityCategory === 'DO_FIRST' ||
            (selectedPlanItem && (selectedPlanItem.executionBadge === 'Now' || selectedPlanItem.planPositionBadge === 'DO THIS' || selectedPlanItem.globalIndex === 0))
        );
        const isSelectedDone = selectedTask && (selectedTask.completed === true || selectedTask.isCompleted === true || selectedTask.status === 'completed');
        const selectedBadgeLabel = selectedTask ? (isSelectedDone ? (isViLocale() ? 'Hoàn thành' : 'Done') : (isSelectedNow ? (isViLocale() ? 'Làm ngay' : 'Do now') : (isViLocale() ? 'Để sau' : 'Later'))) : '';

        // Schedule string for detail header
        let detailScheduleStr = isViLocale() ? `Lịch linh hoạt · ~${selectedTask?.durationLabel || '1h'}` : `Flexible schedule · ~${selectedTask?.durationLabel || '1h'}`;
        if (selectedPlanItem) {
            const itemDayDate = selectedPlanItem.dayDate;
            const sDateLabel = itemDayDate ? formatScheduledDateLabel(itemDayDate, isViLocale()) : '';
            if ((selectedPlanItem.startTime || selectedPlanItem.scheduledStartTime) && (selectedPlanItem.endTime || selectedPlanItem.scheduledEndTime)) {
                const sStart = formatTime12H(selectedPlanItem.startTime || selectedPlanItem.scheduledStartTime);
                const sEnd = formatTime12H(selectedPlanItem.endTime || selectedPlanItem.scheduledEndTime);
                detailScheduleStr = `${sDateLabel || formatScheduledDateLabel(todayStr, isViLocale())} ${sStart} to ${sEnd}`;
            } else if (sDateLabel) {
                detailScheduleStr = `${sDateLabel}, ${isViLocale() ? 'Đã lên lịch' : 'Scheduled'}`;
            }
        } else if (selectedTask) {
            detailScheduleStr = isViLocale() ? `Lịch linh hoạt · ~${selectedTask.durationLabel || '1h'}` : `Flexible schedule · ~${selectedTask.durationLabel || '1h'}`;
        }

        const selectedSubtaskCount = selectedTask && Array.isArray(selectedTask.subtasks) ? selectedTask.subtasks.length : 0;
        const selectedCompletedSubtasks = selectedTask && Array.isArray(selectedTask.subtasks) ? selectedTask.subtasks.filter(s => s.completed).length : 0;
        const savedNoteObj = selectedTask && window.TempoToolNotes ? window.TempoToolNotes.getNoteForTask(selectedTask.id) : null;
        const selectedNoteText = savedNoteObj ? savedNoteObj.text : (selectedTask && selectedTask.note && selectedTask.note !== 'Create a sheet to manage references' ? selectedTask.note : '');

        // Contextual Prompt for Missed Scheduled Tasks
        const missedItems = activePlanned.filter(pt => {
            const t = pt.task;
            if (!t || t.completed === true || t.isCompleted === true || t.status === 'completed') return false;
            if (isTaskOverdue(t, plan)) return false;
            if (!isTaskMissedSchedule(pt, plan)) return false;
            return !isMissedSchedulePromptDismissed(t.id, pt.dayDate);
        });

        let missedScheduleBannerHTML = '';
        if (missedItems.length > 0) {
            const currentMissed = missedItems[0];
            const missedTask = currentMissed.task;
            const taskName = missedTask.name || 'Scheduled Task';
            const isVi = isViLocale();
            const schedDateFormatted = window.TempoI18n && typeof window.TempoI18n.formatCalendarDate === 'function'
                ? window.TempoI18n.formatCalendarDate(currentMissed.dayDate, isVi ? 'vi' : 'en')
                : formatScheduledDateLabel(currentMissed.dayDate, isVi);
            let deadlineClause = '';
            if (missedTask.hasDeadline && missedTask.deadlineDate) {
                const dueDateFormatted = window.TempoI18n && typeof window.TempoI18n.formatCalendarDate === 'function'
                    ? window.TempoI18n.formatCalendarDate(missedTask.deadlineDate, isVi ? 'vi' : 'en')
                    : missedTask.deadlineDate;
                deadlineClause = isVi ? ` Deadline vẫn là ngày ${dueDateFormatted}.` : ` Your deadline is still ${dueDateFormatted}.`;
            }
            const promptDescription = isVi
                ? `Task này đã được sắp xếp vào ngày ${schedDateFormatted} nhưng chưa được hoàn thành.${deadlineClause} Bạn có muốn xếp lại lịch không?`
                : `This task was scheduled for ${schedDateFormatted}, but it hasn't been completed yet.${deadlineClause} Would you like to reschedule it?`;

            missedScheduleBannerHTML = `
                <!-- Contextual Prompt: Missed Scheduled Task -->
                <div class="rounded-2xl p-4 sm:p-5 soft-card-shadow transition flex flex-col md:flex-row md:items-center justify-between gap-4 border"
                     style="background-color: #fbf9f6; border-color: #c9c2bc;"
                     data-tempo-ui="missed-schedule-prompt">
                    <div class="space-y-1.5 flex-1 min-w-0">
                        <div class="flex items-center space-x-2">
                            <span class="w-2 h-2 rounded-full bg-[#7A6D65] inline-block"></span>
                            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#7A6D65] text-white">
                                ${isVi ? 'TASK QUÁ LỊCH' : 'MISSED SCHEDULE'}
                            </span>
                            <span class="text-xs font-bold text-stone-700 truncate">• ${escapeHTML(taskName)}</span>
                        </div>
                        <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#484541] tracking-tight leading-snug">
                            ${isVi ? 'Task này đã bị quá lịch' : 'You missed this scheduled task'}
                        </h3>
                        <p class="text-xs sm:text-sm text-[#5D5954] leading-relaxed">
                            ${escapeHTML(promptDescription)}
                        </p>
                    </div>
                    <div class="flex flex-wrap items-center gap-2.5 shrink-0 pt-2 md:pt-0">
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.openRescheduleModal('${missedTask.id}')"
                                class="px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#D99E87] hover:bg-[#C98E77] shadow-2xs transition cursor-pointer">
                            ${isVi ? 'Xếp lại lịch' : 'Reschedule task'}
                        </button>
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.keepCurrentSchedule('${missedTask.id}')"
                                class="px-4 py-2 rounded-xl font-bold text-xs sm:text-sm bg-white hover:bg-stone-50 text-stone-700 border border-stone-300 shadow-2xs transition cursor-pointer">
                            ${isVi ? 'Giữ lịch hiện tại' : 'Keep current schedule'}
                        </button>
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.toggleTaskComplete('${missedTask.id}')"
                                class="px-4 py-2 rounded-xl font-bold text-xs sm:text-sm bg-white hover:bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-2xs transition cursor-pointer">
                            ${isVi ? 'Đánh dấu hoàn thành' : 'Mark as done'}
                        </button>
                    </div>
                </div>
            `;
        }

        root.innerHTML = `
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 sm:py-5 space-y-6" data-tempo-ui="tempo-working-plan">
                <!-- Top-Left Navigation Control -->
                <div class="flex items-center justify-between">
                    <button id="plan-workspace-back-home"
                            type="button"
                            onclick="window.TempoPlanWorkspace.navigateHome()" 
                            class="text-xs sm:text-sm font-semibold text-[#6F6B68] hover:text-[#202124] flex items-center space-x-1.5 transition py-1 cursor-pointer group"
                            title="${isViLocale() ? '← Về trang chủ' : 'Return Home'}">
                        <span class="group-hover:-translate-x-0.5 transition-transform">←</span>
                        <span>${isViLocale() ? 'Về trang chủ' : 'Return Home'}</span>
                    </button>
                </div>

                <!-- Centered Page Title -->
                <div class="text-center">
                    <h1 class="font-heading text-3xl sm:text-4xl md:text-[42px] font-extrabold text-[#DBA590] tracking-tight">
                        Tempo Working Plan
                    </h1>
                </div>

                <!-- Progress Bar and Action Buttons Row -->
                <div class="flex flex-col md:flex-row items-center justify-between gap-4 pt-1 pb-2">
                    <!-- Progress Bar & Count -->
                    <div class="flex items-center space-x-3 w-full md:w-auto">
                        <div class="w-48 sm:w-64 md:w-72 h-3.5 bg-[#CCD3D5] rounded-full overflow-hidden flex items-center p-0.5">
                            <div class="bg-[#D99E87] h-full rounded-full transition-all duration-300"
                                 style="width: ${progressPercent}%; min-width: ${progressPercent > 0 ? '12px' : '8px'};"></div>
                        </div>
                        <span class="text-xs sm:text-sm font-medium text-[#6F6B68] shrink-0" data-tempo-ui="tasks-progress-counter">
                            ${completedTasksCount}/${totalTasksCount} ${isViLocale() ? 'task' : 'Tasks'}
                        </span>
                    </div>

                    <!-- Header Plan Action CTAs -->
                    <div class="flex flex-wrap items-center gap-2 sm:gap-2.5 shrink-0 justify-center">
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.openAddTaskModal()"
                                class="px-3.5 sm:px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#92A491] hover:bg-[#829381] shadow-2xs transition cursor-pointer">
                            ${isViLocale() ? 'Thêm task' : 'Add task'}
                        </button>
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.openAdjustAvailabilityModal()"
                                class="px-3.5 sm:px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#8AA8B7] hover:bg-[#7A98A7] shadow-2xs transition cursor-pointer">
                            ${isViLocale() ? 'Thêm thời gian làm việc' : 'Add availability'}
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
                    </div>
                </div>

                ${missedScheduleBannerHTML}

                <!-- Main Two-Column Layout -->
                <div class="flex flex-col lg:flex-row gap-6 lg:gap-8 items-start">
                    <!-- LEFT COLUMN: Scrollable Task List -->
                    <div class="w-full lg:w-[48%] flex flex-col">
                        <div id="plan-workspace-task-list"
                             class="max-h-[calc(100vh-230px)] min-h-[460px] overflow-y-auto overflow-x-hidden pr-2 sm:pr-3 space-y-6 plan-custom-scroll">
                            ${totalTasksCount === 0 ? `
                                <div class="p-8 sm:p-10 text-center border border-dashed border-[#D8C7B5] rounded-3xl bg-white/60 space-y-3.5 my-4">
                                    <div class="text-3xl">📋</div>
                                    <h4 class="font-heading font-extrabold text-base sm:text-lg text-[#202124]">${isViLocale() ? 'Chưa có task nào trong kế hoạch' : 'No tasks in your working plan yet'}</h4>
                                    <p class="text-xs sm:text-sm text-[#6F6B68] max-w-sm mx-auto">${isViLocale() ? 'Hãy bấm "+ Thêm task" ở trên hoặc chọn nạp task mẫu để bắt đầu.' : 'Click "+ Add Task" above or choose to load sample tasks to get started.'}</p>
                                    <div class="pt-2 flex items-center justify-center gap-2.5">
                                        <button type="button"
                                                onclick="window.TempoPlanWorkspace.openAddTaskModal()"
                                                class="px-4 py-2 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#D99E87] hover:bg-[#C98E77] transition cursor-pointer">
                                            ${isViLocale() ? '+ Thêm task' : '+ Add Task'}
                                        </button>
                                        <button type="button"
                                                onclick="window.TempoPlanWorkspace.loadSampleTasks()"
                                                class="px-4 py-2 rounded-xl font-semibold text-xs sm:text-sm text-[#6F6B68] hover:text-[#202124] bg-stone-100 hover:bg-stone-200 transition cursor-pointer">
                                            ${isViLocale() ? '+ Nạp task mẫu' : '+ Load sample tasks'}
                                        </button>
                                    </div>
                                </div>
                            ` : ''}
                            ${Object.keys(daysMap).sort((a, b) => {
                                if (a === 'unscheduled') return 1;
                                if (b === 'unscheduled') return -1;
                                return a.localeCompare(b);
                            }).map((dDate, gIdx) => {
                                const group = daysMap[dDate];
                                return `
                                    <div class="space-y-3.5">
                                        <!-- Date Heading -->
                                        <h3 class="font-heading font-extrabold text-base sm:text-lg text-[#D9A18B]">
                                            ${escapeHTML(group.label)}
                                        </h3>

                                        <!-- Tasks in this Day -->
                                        <div class="space-y-3">
                                            ${group.items.map(item => {
                                                const task = item.task;
                                                const isSelected = selectedTaskId === task.id;
                                                const isNow = item.executionBadge === 'Now' || item.planPositionBadge === 'DO THIS' || item.globalIndex === 0;
                                                const badgeClass = isNow ? 'bg-[#D99E87] text-white' : 'bg-[#E8ECF1] text-[#7B96A6]';
                                                const badgeText = isNow ? (isViLocale() ? 'Làm ngay' : 'Do now') : (isViLocale() ? 'Để sau' : 'Later');

                                                const startTime = item.startTime || item.scheduledStartTime;
                                                const endTime = item.endTime || item.scheduledEndTime;
                                                const subCount = Array.isArray(task.subtasks) ? task.subtasks.length : 0;
                                                const compSubCount = Array.isArray(task.subtasks) ? task.subtasks.filter(s => s.completed).length : 0;

                                                return `
                                                    <div class="flex items-center gap-3 sm:gap-4" data-task-row="${task.id}">
                                                        <!-- Time Slot on Left -->
                                                        <div class="w-16 sm:w-20 text-center shrink-0 flex flex-col items-center justify-center text-xs font-bold text-[#D9A18B] leading-tight">
                                                            ${startTime && endTime ? `
                                                                <span>${formatTime12H(startTime)}</span>
                                                                <span class="my-0.5">|</span>
                                                                <span>${formatTime12H(endTime)}</span>
                                                            ` : `
                                                                <span>Flexible</span>
                                                            `}
                                                        </div>

                                                        <!-- Task Card on Right -->
                                                        <div class="flex-1 min-w-0 bg-[#FDFBF6] hover:bg-white border ${isSelected ? 'border-2 border-[#D99E87]' : 'border-[#E3C7A5]'} rounded-2xl p-4 sm:p-5 transition shadow-2xs cursor-pointer"
                                                             onclick="window.TempoPlanWorkspace.selectTask('${task.id}')">
                                                            <div class="flex items-center justify-between gap-2 pb-1.5">
                                                                <div class="flex items-center space-x-2.5 min-w-0">
                                                                    <!-- Checkbox -->
                                                                    <button type="button"
                                                                            onclick="window.TempoPlanWorkspace.toggleTaskComplete('${task.id}', event)"
                                                                            class="w-5 h-5 rounded-lg border flex items-center justify-center text-xs font-bold transition shrink-0 ${task.completed ? 'bg-[#92A491] border-[#92A491] text-white' : 'border-[#E3C7A5] bg-white text-transparent hover:border-[#D99E87]'}"
                                                                            title="Mark complete">
                                                                        ✓
                                                                    </button>
                                                                    <!-- Title -->
                                                                    <h4 class="font-heading text-base font-bold text-[#202124] truncate ${task.completed ? 'line-through text-stone-400' : ''}">
                                                                        ${escapeHTML(task.name)}
                                                                    </h4>
                                                                </div>
                                                                <!-- Status Badge with Interactive Dropdown -->
                                                                <div class="relative inline-block" data-label-menu-container>
                                                                    <button type="button"
                                                                            onclick="event.stopPropagation(); window.TempoPlanWorkspace.toggleLabelMenu('${task.id}', event);"
                                                                            class="px-3 py-0.5 rounded-full text-xs font-bold ${badgeClass} shrink-0 cursor-pointer hover:opacity-90 transition flex items-center space-x-1"
                                                                            title="Change priority: Now or Later">
                                                                        <span>${badgeText}</span>
                                                                        <span class="text-[9px] opacity-75">▾</span>
                                                                    </button>
                                                                    ${activeLabelMenuTaskId === task.id ? `
                                                                        <div class="absolute right-0 top-full mt-1 z-30 bg-white border border-[#E3C7A5] rounded-xl shadow-lg py-1 w-28 text-xs font-semibold overflow-hidden"
                                                                             onclick="event.stopPropagation();">
                                                                            <button type="button"
                                                                                    onclick="window.TempoPlanWorkspace.setTaskLabel('${task.id}', 'Now');"
                                                                                    class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${isNow ? 'font-bold text-[#D99E87]' : ''}">
                                                                                <span>${isViLocale() ? 'Làm ngay' : 'Do now'}</span>
                                                                                ${isNow ? '<span>✓</span>' : ''}
                                                                            </button>
                                                                            <button type="button"
                                                                                    onclick="window.TempoPlanWorkspace.setTaskLabel('${task.id}', 'Later');"
                                                                                    class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${!isNow ? 'font-bold text-[#7B96A6]' : ''}">
                                                                                <span>${isViLocale() ? 'Để sau' : 'Later'}</span>
                                                                                ${!isNow ? '<span>✓</span>' : ''}
                                                                            </button>
                                                                        </div>
                                                                    ` : ''}
                                                                </div>
                                                            </div>

                                                            <!-- Due date and subtasks -->
                                                            <div class="pl-7 space-y-0.5 text-xs text-[#6F6B68]">
                                                                <div class="flex items-center space-x-1.5 flex-wrap">
                                                                    <span>Deadline: ${formatDeadline(task.deadlineDate || task.deadline, task.deadlineTime)}</span>
                                                                    ${isTaskOverdue(task) ? `<span class="px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">${(window.t ? window.t('modes.urgent.overdueBadge') : null) || (isViLocale() ? 'TRỄ DEADLINE' : 'OVERDUE')}</span>` : ''}
                                                                    ${!isTaskOverdue(task) && isTaskMissedSchedule(item || task, plan) ? `<span class="px-1.5 py-0.2 rounded text-[10px] font-bold bg-stone-100 text-stone-700 border border-stone-300">${isViLocale() ? 'TASK QUÁ LỊCH' : 'MISSED SCHEDULE'}</span>` : ''}
                                                                </div>
                                                                ${subCount > 0 ? `<div>${compSubCount}/${subCount} ${isViLocale() ? 'subtask' : 'Subtasks'}</div>` : ''}
                                                            </div>
                                                        </div>
                                                    </div>
                                                `;
                                            }).join('')}
                                        </div>

                                        ${gIdx < Object.keys(daysMap).length - 1 ? `
                                            <hr class="border-[#EEE9E7] my-3" />
                                        ` : ''}
                                    </div>
                                `;
                            }).join('')}

                            <!-- Unarranged Active Tasks if any -->
                            ${activeUnarranged.length > 0 ? `
                                <div class="space-y-3.5 pt-2">
                                    <h3 class="font-heading font-extrabold text-base sm:text-lg text-[#D9A18B]">
                                        ${isViLocale() ? 'Linh hoạt / Chưa lên lịch' : 'Flexible / Unscheduled'}
                                    </h3>
                                    <div class="space-y-3">
                                        ${activeUnarranged.map(task => {
                                            const isSelected = selectedTaskId === task.id;
                                            const subCount = Array.isArray(task.subtasks) ? task.subtasks.length : 0;
                                            const compSubCount = Array.isArray(task.subtasks) ? task.subtasks.filter(s => s.completed).length : 0;

                                            return `
                                                <div class="flex items-center gap-3 sm:gap-4" data-task-row="${task.id}">
                                                    <div class="w-16 sm:w-20 text-center shrink-0 flex flex-col items-center justify-center text-xs font-bold text-[#D9A18B] leading-tight">
                                                        <span>~${task.durationLabel || '1h'}</span>
                                                    </div>
                                                    <div class="flex-1 min-w-0 bg-[#FDFBF6] hover:bg-white border ${isSelected ? 'border-2 border-[#D99E87]' : 'border-[#E3C7A5]'} rounded-2xl p-4 sm:p-5 transition shadow-2xs cursor-pointer"
                                                         onclick="window.TempoPlanWorkspace.selectTask('${task.id}')">
                                                        <div class="flex items-center justify-between gap-2 pb-1.5">
                                                            <div class="flex items-center space-x-2.5 min-w-0">
                                                                <button type="button"
                                                                        onclick="window.TempoPlanWorkspace.toggleTaskComplete('${task.id}', event)"
                                                                        class="w-5 h-5 rounded-lg border flex items-center justify-center text-xs font-bold transition shrink-0 ${task.completed ? 'bg-[#92A491] border-[#92A491] text-white' : 'border-[#E3C7A5] bg-white text-transparent hover:border-[#D99E87]'}"
                                                                        title="Mark complete">
                                                                    ✓
                                                                </button>
                                                                <h4 class="font-heading text-base font-bold text-[#202124] truncate ${task.completed ? 'line-through text-stone-400' : ''}">
                                                                    ${escapeHTML(task.name)}
                                                                </h4>
                                                            </div>
                                                            <!-- Status Badge with Interactive Dropdown -->
                                                            <div class="relative inline-block" data-label-menu-container>
                                                                <button type="button"
                                                                        onclick="event.stopPropagation(); window.TempoPlanWorkspace.toggleLabelMenu('${task.id}', event);"
                                                                        class="px-3 py-0.5 rounded-full text-xs font-bold bg-[#E8ECF1] text-[#7B96A6] shrink-0 cursor-pointer hover:opacity-90 transition flex items-center space-x-1"
                                                                        title="${isViLocale() ? 'Thay đổi mức độ ưu tiên: Làm ngay hoặc Để sau' : 'Change priority: Now or Later'}">
                                                                    <span>${isViLocale() ? 'Để sau' : 'Later'}</span>
                                                                    <span class="text-[9px] opacity-75">▾</span>
                                                                </button>
                                                                ${activeLabelMenuTaskId === task.id ? `
                                                                    <div class="absolute right-0 top-full mt-1 z-30 bg-white border border-[#E3C7A5] rounded-xl shadow-lg py-1 w-28 text-xs font-semibold overflow-hidden"
                                                                         onclick="event.stopPropagation();">
                                                                        <button type="button"
                                                                                onclick="window.TempoPlanWorkspace.setTaskLabel('${task.id}', 'Now');"
                                                                                class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124]">
                                                                            <span>${isViLocale() ? 'Làm ngay' : 'Do now'}</span>
                                                                        </button>
                                                                        <button type="button"
                                                                                onclick="window.TempoPlanWorkspace.setTaskLabel('${task.id}', 'Later');"
                                                                                class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] font-bold text-[#7B96A6]">
                                                                            <span>${isViLocale() ? 'Để sau' : 'Later'}</span>
                                                                            <span>✓</span>
                                                                        </button>
                                                                    </div>
                                                                ` : ''}
                                                            </div>
                                                        </div>
                                                        <div class="pl-7 space-y-0.5 text-xs text-[#6F6B68]">
                                                            <div class="flex items-center space-x-1.5 flex-wrap">
                                                                <span>Deadline: ${formatDeadline(task.deadlineDate || task.deadline, task.deadlineTime)}</span>
                                                                ${isTaskOverdue(task) ? `<span class="px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">${(window.t ? window.t('modes.urgent.overdueBadge') : null) || (isViLocale() ? 'TRỄ DEADLINE' : 'OVERDUE')}</span>` : ''}
                                                                ${!isTaskOverdue(task) && isTaskMissedSchedule(task, plan) ? `<span class="px-1.5 py-0.2 rounded text-[10px] font-bold bg-stone-100 text-stone-700 border border-stone-300">${isViLocale() ? 'TASK QUÁ LỊCH' : 'MISSED SCHEDULE'}</span>` : ''}
                                                            </div>
                                                            ${subCount > 0 ? `<div>${compSubCount}/${subCount} ${isViLocale() ? 'subtask' : 'Subtasks'}</div>` : ''}
                                                        </div>
                                                    </div>
                                                </div>
                                            `;
                                        }).join('')}
                                    </div>
                                </div>
                            ` : ''}

                            <!-- DONE SECTION: Only rendered when tasks are completed -->
                            ${allCompleted.length > 0 ? `
                                <div class="pt-4 border-t border-[#EEE9E7] space-y-3.5" data-tempo-ui="done-section">
                                    <h3 class="font-heading font-extrabold text-base sm:text-lg text-[#92A491] flex items-center space-x-2">
                                        <span>${isViLocale() ? 'Đã hoàn thành' : 'Completed'}</span>
                                        <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#E8EFE8] text-[#556B54]">(${allCompleted.length})</span>
                                    </h3>
                                    <div class="space-y-3">
                                        ${allCompleted.map(item => {
                                            const task = item.task;
                                            const isSelected = selectedTaskId === task.id;
                                            const subCount = Array.isArray(task.subtasks) ? task.subtasks.length : 0;
                                            const compSubCount = Array.isArray(task.subtasks) ? task.subtasks.filter(s => s.completed).length : 0;
                                            const startTime = item.startTime;
                                            const endTime = item.endTime;

                                            return `
                                                <div class="flex items-center gap-3 sm:gap-4 opacity-80 hover:opacity-100 transition" data-task-row="${task.id}">
                                                    <div class="w-16 sm:w-20 text-center shrink-0 flex flex-col items-center justify-center text-xs font-bold text-[#92A491] leading-tight">
                                                        ${startTime && endTime ? `
                                                            <span>${formatTime12H(startTime)}</span>
                                                            <span class="my-0.5">|</span>
                                                            <span>${formatTime12H(endTime)}</span>
                                                        ` : `
                                                            <span>--</span>
                                                        `}
                                                    </div>
                                                    <div class="flex-1 min-w-0 bg-[#FDFBF6] hover:bg-white border ${isSelected ? 'border-2 border-[#92A491]' : 'border-[#E3C7A5]'} rounded-2xl p-4 sm:p-5 transition shadow-2xs cursor-pointer"
                                                         onclick="window.TempoPlanWorkspace.selectTask('${task.id}')">
                                                        <div class="flex items-center justify-between gap-2 pb-1.5">
                                                            <div class="flex items-center space-x-2.5 min-w-0">
                                                                <button type="button"
                                                                        onclick="window.TempoPlanWorkspace.toggleTaskComplete('${task.id}', event)"
                                                                        class="w-5 h-5 rounded-lg border bg-[#92A491] border-[#92A491] text-white flex items-center justify-center text-xs font-bold transition shrink-0"
                                                                        title="Mark incomplete">
                                                                    ✓
                                                                </button>
                                                                <h4 class="font-heading text-base font-bold text-stone-400 line-through truncate">
                                                                    ${escapeHTML(task.name)}
                                                                </h4>
                                                            </div>
                                                            <span class="px-3 py-0.5 rounded-full text-xs font-bold bg-[#E8EFE8] text-[#556B54] shrink-0">
                                                                ${isViLocale() ? 'Hoàn thành' : 'Done'}
                                                            </span>
                                                        </div>
                                                        <div class="pl-7 space-y-0.5 text-xs text-[#6F6B68]">
                                                            <div>Deadline: ${formatDeadline(task.deadlineDate || task.deadline, task.deadlineTime)}</div>
                                                            <div>${compSubCount}/${subCount} ${isViLocale() ? 'subtask' : 'Subtasks'}</div>
                                                        </div>
                                                    </div>
                                                </div>
                                            `;
                                        }).join('')}
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>

                    <!-- Vertical Column Divider -->
                    <div class="hidden lg:block w-px bg-[#EFF3F6] self-stretch my-2"></div>

                    <!-- RIGHT COLUMN: Selected Task Details -->
                    <div class="w-full lg:w-[48%] lg:sticky lg:top-20">
                        ${selectedTask ? `
                            <div class="bg-[#FDFBF6] border border-[#E3C7A5] rounded-3xl p-6 sm:p-7 space-y-4 shadow-sm" data-tempo-ui="selected-task-card">
                                <!-- Schedule Header -->
                                <div class="text-xs sm:text-sm font-bold text-[#D9A18B] tracking-wide">
                                    ${escapeHTML(detailScheduleStr)}
                                </div>

                                <!-- Title and Badge -->
                                <div class="flex items-center justify-between gap-3 pb-1">
                                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] ${selectedTask.completed ? 'line-through text-stone-400' : ''}">
                                        ${escapeHTML(selectedTask.name)}
                                    </h2>
                                    <!-- Status Badge with Interactive Dropdown -->
                                    <div class="relative inline-block" data-label-menu-container>
                                        <button type="button"
                                                ${isSelectedDone ? '' : `onclick="event.stopPropagation(); window.TempoPlanWorkspace.toggleLabelMenu('${selectedTask.id}', event);"`}
                                                class="px-3 py-0.5 rounded-full text-xs font-bold ${isSelectedNow ? 'bg-[#D99E87] text-white' : (isSelectedDone ? 'bg-[#92A491] text-white' : 'bg-[#E8ECF1] text-[#7B96A6]')} shrink-0 ${!isSelectedDone ? 'cursor-pointer hover:opacity-90 transition flex items-center space-x-1' : ''}"
                                                title="${isSelectedDone ? (isViLocale() ? 'Công việc đã hoàn thành' : 'Completed task') : (isViLocale() ? 'Thay đổi mức độ ưu tiên: Làm ngay hoặc Để sau' : 'Change priority: Now or Later')}">
                                            <span>${selectedBadgeLabel}</span>
                                            ${!isSelectedDone ? '<span class="text-[9px] opacity-75">▾</span>' : ''}
                                        </button>
                                        ${activeLabelMenuTaskId === selectedTask.id && !isSelectedDone ? `
                                            <div class="absolute right-0 top-full mt-1 z-30 bg-white border border-[#E3C7A5] rounded-xl shadow-lg py-1 w-28 text-xs font-semibold overflow-hidden"
                                                 onclick="event.stopPropagation();">
                                                <button type="button"
                                                        onclick="window.TempoPlanWorkspace.setTaskLabel('${selectedTask.id}', 'Now');"
                                                        class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${isSelectedNow ? 'font-bold text-[#D99E87]' : ''}">
                                                    <span>${isViLocale() ? 'Làm ngay' : 'Do now'}</span>
                                                    ${isSelectedNow ? '<span>✓</span>' : ''}
                                                </button>
                                                <button type="button"
                                                        onclick="window.TempoPlanWorkspace.setTaskLabel('${selectedTask.id}', 'Later');"
                                                        class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${!isSelectedNow ? 'font-bold text-[#7B96A6]' : ''}">
                                                    <span>${isViLocale() ? 'Để sau' : 'Later'}</span>
                                                    ${!isSelectedNow ? '<span>✓</span>' : ''}
                                                </button>
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>

                                <!-- Due Date Row -->
                                <div class="flex items-center space-x-2 text-xs sm:text-sm text-[#6F6B68]">
                                    <span>Deadline: ${formatDeadline(selectedTask.deadlineDate || selectedTask.deadline, selectedTask.deadlineTime)}</span>
                                    ${isTaskOverdue(selectedTask) ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">${(window.t ? window.t('modes.urgent.overdueBadge') : null) || (isViLocale() ? 'TRỄ DEADLINE' : 'OVERDUE')}</span>` : ''}
                                    ${!isTaskOverdue(selectedTask) && isTaskMissedSchedule(selectedPlanItem || selectedTask, plan) ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-stone-100 text-stone-700 border border-stone-300">${isViLocale() ? 'TASK QUÁ LỊCH' : 'MISSED SCHEDULE'}</span>` : ''}
                                    <button type="button"
                                            onclick="window.TempoPlanWorkspace.toggleDeadlineEdit()"
                                            class="text-[#D99E87] font-semibold hover:underline cursor-pointer">
                                        ${isEditingDeadline ? (isViLocale() ? 'Hủy' : 'Cancel') : (isViLocale() ? 'Sửa deadline' : 'Edit deadline')}
                                    </button>
                                </div>

                                <!-- Inline Deadline Editor -->
                                ${isEditingDeadline ? `
                                    <div class="p-3 bg-white border border-[#E3C7A5] rounded-xl space-y-2 text-xs">
                                        <div class="grid grid-cols-2 gap-2">
                                            <div>
                                                <label class="block text-[10px] text-gray-500 font-semibold mb-0.5">${isViLocale() ? 'Ngày' : 'Date'}</label>
                                                <input id="pw-edit-deadline-date" type="date" value="${selectedTask.deadlineDate || (selectedTask.deadline ? selectedTask.deadline.split(' ')[0] : '')}" class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                            </div>
                                            <div>
                                                <label class="block text-[10px] text-gray-500 font-semibold mb-0.5">${isViLocale() ? 'Giờ' : 'Time'}</label>
                                                <input id="pw-edit-deadline-time" type="time" value="${selectedTask.deadlineTime || (selectedTask.deadline ? selectedTask.deadline.split(' ')[1] : '23:59')}" class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                            </div>
                                        </div>
                                        <div class="flex items-center space-x-2">
                                            <input id="pw-edit-no-deadline" type="checkbox" ${!selectedTask.hasDeadline ? 'checked' : ''} class="rounded text-[#D99E87]">
                                            <label for="pw-edit-no-deadline" class="text-xs text-stone-700">${isViLocale() ? 'Chưa có deadline' : 'No deadline'}</label>
                                        </div>
                                        <div class="flex justify-end pt-1">
                                            <button type="button"
                                                    onclick="window.TempoPlanWorkspace.saveDeadlineEdit('${selectedTask.id}')"
                                                    class="px-3 py-1 bg-[#D99E87] text-white rounded-lg text-xs font-bold hover:bg-[#C98E77]">
                                                ${isViLocale() ? 'Lưu deadline' : 'Save deadline'}
                                            </button>
                                        </div>
                                    </div>
                                ` : ''}

                                <!-- Subtasks Count Row -->
                                <div class="flex items-center space-x-2 text-xs sm:text-sm text-[#6F6B68]">
                                    ${selectedSubtaskCount > 0 ? `<span>${selectedCompletedSubtasks}/${selectedSubtaskCount} ${isViLocale() ? 'subtask' : 'Subtasks'}</span>` : ''}
                                    <button type="button"
                                            onclick="window.TempoPlanWorkspace.openBreakTaskModal('${selectedTask.id}')"
                                            class="text-[#D99E87] font-semibold hover:underline cursor-pointer">
                                        ${isViLocale() ? (selectedSubtaskCount > 0 ? 'Chia nhỏ task' : '+ Chia nhỏ task') : (selectedSubtaskCount > 0 ? 'Break down task' : '+ Break down task')}
                                    </button>
                                </div>

                                <!-- Subtask List with Custom Scrollbar -->
                                ${selectedSubtaskCount > 0 ? `
                                    <div class="max-h-40 overflow-y-auto space-y-2 pr-2 plan-custom-scroll">
                                        ${(selectedTask.subtasks || []).map(step => `
                                            <div class="flex items-center space-x-2.5 text-xs sm:text-sm text-[#4A4540]">
                                                <button type="button"
                                                        onclick="window.TempoPlanWorkspace.toggleSubtask('${selectedTask.id}', '${step.id}')"
                                                        class="w-4 h-4 rounded border border-[#E3C7A5] flex items-center justify-center text-[10px] font-bold transition shrink-0 ${step.completed ? 'bg-[#92A491] border-[#92A491] text-white' : 'bg-white border-[#E3C7A5] text-transparent hover:border-[#D99E87]'}"
                                                        title="Toggle subtask">
                                                    ✓
                                                </button>
                                                <span class="${step.completed ? 'line-through text-stone-400' : ''}">${escapeHTML(step.title)}</span>
                                            </div>
                                        `).join('')}
                                    </div>
                                ` : ''}

                                <!-- Note Row -->
                                ${selectedNoteText ? `
                                    <div class="text-xs sm:text-sm text-[#4A4540] pt-1 flex items-start justify-between gap-2 bg-[#F6F4EE]/60 border border-[#EAE4DF] rounded-xl p-2.5">
                                        <div class="min-w-0 flex-1">
                                            <strong class="text-[#D9A18B]">${isViLocale() ? 'Ghi chú:' : 'Note:'}</strong> <span class="whitespace-pre-line text-[#4A4540]">${escapeHTML(selectedNoteText)}</span>
                                        </div>
                                        <button type="button"
                                                onclick="window.TempoPlanWorkspace.openNoteEditor('${selectedTask.id}')"
                                                class="text-[#D99E87] hover:text-[#C98E77] text-xs font-semibold shrink-0 cursor-pointer flex items-center space-x-1"
                                                title="${isViLocale() ? 'Chỉnh sửa ghi chú' : 'Edit note'}">
                                            <span>${isViLocale() ? 'Chỉnh sửa ghi chú' : 'Edit note'}</span>
                                            <span>✎</span>
                                        </button>
                                    </div>
                                ` : `
                                    <div class="pt-1">
                                        <button type="button"
                                                onclick="window.TempoPlanWorkspace.openNoteEditor('${selectedTask.id}')"
                                                class="text-xs font-bold text-[#D9A18B] hover:underline cursor-pointer flex items-center space-x-1">
                                            <span>${isViLocale() ? '+ Thêm ghi chú' : '+ Add note'}</span>
                                        </button>
                                    </div>
                                `}

                                <!-- Action Buttons (2x2 grid) -->
                                <div class="grid grid-cols-2 gap-3 pt-3">
                                    <!-- 1. Mark as done -->
                                    <button type="button"
                                            onclick="window.TempoPlanWorkspace.toggleTaskComplete('${selectedTask.id}')"
                                            class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#92A491] hover:bg-[#829381] shadow-2xs transition text-center cursor-pointer">
                                        ${selectedTask.completed ? (isViLocale() ? 'Đang thực hiện' : 'Mark as active') : (isViLocale() ? 'Hoàn thành' : 'Mark as done')}
                                    </button>

                                    <!-- 2. Focus now -->
                                    <button type="button"
                                            onclick="window.TempoPlanWorkspace.startTaskFocus('${selectedTask.id}')"
                                            class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#D7A690] hover:bg-[#C98E77] shadow-2xs transition flex items-center justify-center space-x-1.5 cursor-pointer">
                                        <span>▶ ${isViLocale() ? 'Làm task' : 'Focus now'}</span>
                                    </button>

                                    <!-- 3. Reschedule -->
                                    <button type="button"
                                            onclick="window.TempoPlanWorkspace.openRescheduleModal('${selectedTask.id}')"
                                            class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#3A4B3D] bg-white border border-[#8D9B8A] hover:bg-stone-50 transition text-center cursor-pointer">
                                        ${isViLocale() ? 'Đổi lịch' : 'Reschedule'}
                                    </button>

                                    <!-- 4. Clear this task -->
                                    <button type="button"
                                            onclick="window.TempoPlanWorkspace.promptClearTask('${selectedTask.id}')"
                                            class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#C53B27] bg-white border border-[#D99E87] hover:bg-rose-50/40 transition text-center cursor-pointer">
                                        ${isViLocale() ? 'Xóa task này' : 'Clear this task'}
                                    </button>
                                </div>
                            </div>
                        ` : `
                            <div class="bg-[#FDFBF6] border border-[#E3C7A5] rounded-3xl p-8 text-center text-xs text-[#6F6B68] space-y-2">
                                <div class="font-bold text-[#202124] text-sm">${isViLocale() ? 'Chưa chọn task nào' : 'No task selected'}</div>
                                <p>${isViLocale() ? 'Chọn một task ở cột bên trái hoặc bấm \"+ Thêm task\" ở trên.' : 'Select a task on the left or click \"+ Add Task\" above.'}</p>
                            </div>
                        `}
                    </div>
                </div>
            </div>

            <!-- Modals Container -->
            ${renderModalsHTML(plan)}
        `;
    }


        /**
     * Render Modals (Add Task, Prompt, Reschedule, Adjust Availability)
     */
    function renderModalsHTML(plan) {
        if (!activeModal) return '';

        if (activeModal === 'add-task') {
            const todayStr = getTodayISO();
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            const tomorrowStr = getLocalTomorrowISO();

            return `
                <div class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-md w-full">
                        <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                            <h3 class="font-heading text-lg font-bold text-[#202124]">${window.t ? window.t('workspace.addTaskModalTitle', {}, 'Add a task') : 'Add a task'}</h3>
                            <button onclick="window.TempoPlanWorkspace.closeAddTaskModal()" class="text-gray-400 hover:text-gray-600 text-sm">✕</button>
                        </div>

                        <div class="space-y-4 text-xs">
                            <div class="space-y-1">
                                <label class="block font-bold text-gray-700">${window.t ? window.t('workspace.taskName', {}, 'Task Name') : 'Task Name'}</label>
                                <input id="pw-add-task-name" type="text" placeholder="${window.t ? window.t('workspace.taskNamePlaceholder', {}, 'e.g. Research Literature Review') : 'e.g. Research Literature Review'}"
                                       class="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-1 focus:ring-[#FF6B2C] focus:outline-none">
                            </div>

                            <div class="space-y-1.5">
                                <label class="block font-bold text-gray-700">${window.t ? window.t('workspace.deadlineUpper', {}, 'Deadline') : 'Deadline'}</label>
                                <div class="grid grid-cols-2 gap-2">
                                    <input id="pw-add-task-date" type="date" value="${tomorrowStr}"
                                           class="px-2.5 py-1.5 border border-gray-300 rounded-xl text-xs">
                                    <input id="pw-add-task-time" type="time" value="17:00"
                                           class="px-2.5 py-1.5 border border-gray-300 rounded-xl text-xs">
                                </div>
                                <div class="flex items-center space-x-2 pt-1">
                                    <input id="pw-add-task-no-deadline" type="checkbox"
                                           onchange="document.getElementById('pw-add-task-date').disabled = this.checked; document.getElementById('pw-add-task-time').disabled = this.checked;"
                                           class="rounded text-[#FF6B2C]">
                                    <label for="pw-add-task-no-deadline" class="text-stone-600">${window.t ? window.t('workspace.noFixedDeadline', {}, 'No fixed deadline') : 'No fixed deadline'}</label>
                                </div>
                            </div>

                            <div class="space-y-1.5">
                                <label class="block font-bold text-gray-700">${window.t ? window.t('workspace.focusedEstimate', {}, 'Focused-work Estimate') : 'Focused-work Estimate'}</label>
                                <div class="flex items-center space-x-2">
                                    <input id="pw-add-task-dur-val" type="number" min="0.5" step="0.5" value="1.5"
                                           class="w-20 px-3 py-1.5 border border-gray-300 rounded-xl text-center font-bold">
                                    <select id="pw-add-task-dur-unit" class="flex-1 px-3 py-1.5 border border-gray-300 rounded-xl bg-white">
                                        <option value="hours" selected>${window.t ? window.t('common.hours', {}, 'hours') : 'hours'}</option>
                                        <option value="minutes">${window.t ? window.t('common.minutes', {}, 'minutes') : 'minutes'}</option>
                                    </select>
                                </div>
                                <div class="flex items-center space-x-2 pt-1">
                                    <input id="pw-add-task-dur-not-sure" type="checkbox"
                                           onchange="document.getElementById('pw-add-task-dur-val').disabled = this.checked;"
                                           class="rounded text-[#FF6B2C]">
                                    <label for="pw-add-task-dur-not-sure" class="text-stone-600">${window.t ? window.t('workspace.notSureYet', {}, 'Not sure yet') : 'Not sure yet'}</label>
                                </div>
                            </div>
                        </div>

                        <div class="pt-3 border-t border-gray-100 flex items-center justify-end space-x-2">
                            <button onclick="window.TempoPlanWorkspace.closeAddTaskModal()" 
                                    class="px-4 py-2 border border-gray-200 text-xs font-semibold text-gray-600 rounded-xl hover:bg-stone-50">
                                ${window.t ? window.t('common.cancel', {}, 'Cancel') : 'Cancel'}
                            </button>
                            <button onclick="window.TempoPlanWorkspace.submitAddTask()"
                                    class="btn-primary px-5 py-2 rounded-xl font-bold text-xs shadow-sm">
                                ${window.t ? window.t('workspace.addTaskBtn', {}, 'Add task') : 'Add task'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        if (activeModal === 'fit-task-prompt' && pendingAddedTask) {
            return `
                <div class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-sm w-full text-center">
                        <div class="w-12 h-12 rounded-2xl bg-[#FFE9DC] text-[#FF6B2C] flex items-center justify-center text-xl mx-auto">
                            ✓
                        </div>
                        <div class="space-y-1">
                            <h3 class="font-heading text-lg font-bold text-[#202124]">${window.t ? window.t('workspace.taskAdded', {}, 'Task added') : 'Task added'}</h3>
                            <p class="text-xs text-[#6F6B68]">${window.t ? window.t('workspace.taskReadyDesc', { name: escapeHTML(pendingAddedTask.name) }, '"' + escapeHTML(pendingAddedTask.name) + '" is ready.') : ('"' + escapeHTML(pendingAddedTask.name) + '" is ready.')}</p>
                        </div>

                        <div class="pt-2 space-y-2">
                            <button onclick="window.TempoPlanWorkspace.handleFitTaskChoice('fit')"
                                    class="btn-primary w-full py-3 rounded-xl font-bold text-xs shadow-md transition">
                                ${window.t ? window.t('workspace.fitIntoPlan', {}, 'Fit it into my plan') : 'Fit it into my plan'}
                            </button>
                            <button onclick="window.TempoPlanWorkspace.handleFitTaskChoice('unscheduled')"
                                    class="w-full py-2.5 rounded-xl border border-gray-200 bg-white text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                                ${window.t ? window.t('workspace.leaveUnscheduled', {}, 'Leave it unscheduled for now') : 'Leave it unscheduled for now'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        if (activeModal === 'reschedule' && rescheduleTaskId) {
            let task = null;
            const pt = plan.plannedTasks ? plan.plannedTasks.find(item => item.task && (item.task.id === rescheduleTaskId || item.id === rescheduleTaskId || item.taskId === rescheduleTaskId)) : null;
            if (pt) task = pt.task;
            if (!task && plan.unarrangedTasks) {
                const u = plan.unarrangedTasks.find(t => (t && t.task ? (t.task.id === rescheduleTaskId || t.id === rescheduleTaskId) : t.id === rescheduleTaskId));
                if (u) task = u.task ? u.task : u;
            }
            if (!task && plan.unallocatedTasks) {
                const u = plan.unallocatedTasks.find(t => (t && t.task ? (t.task.id === rescheduleTaskId || t.id === rescheduleTaskId) : t.id === rescheduleTaskId));
                if (u) task = u.task ? u.task : u;
            }
            if (!task && plan.tasks) {
                task = plan.tasks.find(t => t.id === rescheduleTaskId);
            }
            if (!task) return '';

            const days = plan.availabilityDays || [];
            const availableSlots = [];
            const todayStr = getLocalTodayISO();
            const currentTimeStr = getLocalCurrentTimeStr();

            days.forEach(d => {
                if (!d || d.date < todayStr) return; // Exclude past dates from reschedule options
                if (Array.isArray(d.blocks) && d.blocks.length > 0) {
                    d.blocks.forEach(b => {
                        // For today, exclude time blocks that have already ended
                        if (d.date === todayStr && b.end && b.end <= currentTimeStr) {
                            return;
                        }
                        availableSlots.push({
                            id: b.id,
                            date: d.date,
                            start: b.start,
                            end: b.end,
                            dayLabel: formatScheduledDateLabel(d.date, isViLocale()) || d.label || d.date,
                            timeLabel: `${formatTime12H(b.start)} – ${formatTime12H(b.end)}`
                        });
                    });
                } else if (d.date > todayStr) {
                    availableSlots.push({
                        id: `day_${d.date}`,
                        date: d.date,
                        start: null,
                        end: null,
                        dayLabel: formatScheduledDateLabel(d.date, isViLocale()) || d.label || d.date,
                        timeLabel: window.t ? window.t('workspace.noTimeBlocks', {}, 'No time blocks defined') : 'No time blocks defined'
                    });
                }
            });

            // Default selection if not already set or match against task scheduled date
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
            }
            const currentSelectedSlotId = rescheduleSelectedSlot ? rescheduleSelectedSlot.id : '';

            return `
                <div class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-md w-full">
                        <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                            <div>
                                <h3 class="font-heading text-lg font-bold text-[#202124]">${window.t ? window.t('workspace.rescheduleTaskModalTitle', {}, 'Reschedule task') : 'Reschedule task'}</h3>
                                <p class="text-xs text-[#6F6B68] truncate max-w-xs">${escapeHTML(task.name)}</p>
                            </div>
                            <button onclick="window.TempoPlanWorkspace.closeRescheduleModal()" class="text-gray-400 hover:text-gray-600 text-sm">✕</button>
                        </div>

                        <div class="space-y-3 text-xs">
                            <span class="block font-bold text-gray-700 uppercase text-[10px] tracking-wider">${window.t ? window.t('workspace.yourAvailableTime', {}, 'YOUR AVAILABLE TIME') : 'YOUR AVAILABLE TIME'}</span>

                            <div class="space-y-2 max-h-48 overflow-y-auto pr-1">
                                ${availableSlots.length > 0 ? availableSlots.map(s => {
                                    const isChecked = s.id === currentSelectedSlotId || (!currentSelectedSlotId && s.date === rescheduleSelectedWindow);
                                    return `
                                        <label data-reschedule-slot-label
                                               onclick="window.TempoPlanWorkspace.selectRescheduleSlot('${s.date}', '${s.id}', '${s.start || ''}', '${s.end || ''}')"
                                               class="p-3 rounded-xl border ${isChecked ? 'border-[#FF6B2C] bg-orange-50/40 ring-1 ring-[#FF6B2C]/30' : 'border-gray-200 hover:border-[#FF6B2C] bg-white hover:bg-orange-50/20'} transition flex items-center space-x-3 cursor-pointer">
                                            <input type="radio" name="pw_reschedule_day" value="${s.date}"
                                                   data-slot-id="${s.id}" data-date="${s.date}" data-start="${s.start || ''}" data-end="${s.end || ''}"
                                                   ${isChecked ? 'checked' : ''}
                                                   class="text-[#FF6B2C] focus:ring-[#FF6B2C]">
                                            <div class="flex-1">
                                                <span class="font-bold text-[#202124] block">${escapeHTML(s.dayLabel)}</span>
                                                <span class="text-[11px] text-[#6F6B68] block">${escapeHTML(s.timeLabel)}</span>
                                            </div>
                                        </label>
                                    `;
                                }).join('') : `
                                    <div class="p-3.5 text-center rounded-xl border border-dashed border-stone-200 bg-stone-50/60 text-stone-500 text-xs">
                                        ${isViLocale() ? 'Chưa có khung giờ làm việc khả dụng trong tương lai. Vui lòng thêm thời gian làm việc bên dưới.' : 'No available upcoming time slots. Please add availability below.'}
                                    </div>
                                `}
                            </div>

                            <!-- Add Availability Button & Inline Form -->
                            ${!rescheduleShowAddTime ? `
                                <div class="pt-1">
                                    <button type="button"
                                            id="btn-reschedule-add-availability"
                                            onclick="window.TempoPlanWorkspace.toggleRescheduleAddTime(true)"
                                            class="w-full py-2.5 px-3 rounded-xl border border-dashed border-[#D99E87] hover:border-[#C98E77] bg-[#FFF8F2] hover:bg-[#FFEEDB] text-[#B83D08] text-xs font-bold transition flex items-center justify-center space-x-1.5 cursor-pointer">
                                        <span>${isViLocale() ? '+ Thêm thời gian làm việc' : '+ Add availability'}</span>
                                    </button>
                                </div>
                            ` : `
                                <div class="p-3.5 bg-[#FFF8F2] border border-[#FFD2BA] rounded-2xl space-y-2.5 animate-fade-in" id="reschedule-add-avail-form">
                                    <div class="flex items-center justify-between">
                                        <span class="font-bold text-[#B83D08] block text-[11px] uppercase tracking-wider">
                                            ${isViLocale() ? 'Thêm thời gian làm việc' : 'Add availability'}
                                        </span>
                                        <button type="button" onclick="window.TempoPlanWorkspace.toggleRescheduleAddTime(false)" class="text-stone-400 hover:text-stone-600 text-xs font-bold p-0.5 cursor-pointer">✕</button>
                                    </div>

                                    <!-- Validation Error Message Container -->
                                    <div id="pw-resched-avail-error" class="hidden text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-xl p-2.5 font-medium animate-fade-in"></div>

                                    <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                                        <div>
                                            <label class="block text-[10px] text-stone-600 font-semibold mb-0.5">${isViLocale() ? 'Ngày' : 'Date'}</label>
                                            <input id="pw-resched-avail-date" type="date" value="${getLocalTodayISO()}"
                                                   class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg bg-white">
                                        </div>
                                        <div>
                                            <label class="block text-[10px] text-stone-600 font-semibold mb-0.5">${isViLocale() ? 'Thời gian bắt đầu' : 'Start time'}</label>
                                            <input id="pw-resched-avail-start" type="time" value="14:00"
                                                   class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg bg-white">
                                        </div>
                                        <div>
                                            <label class="block text-[10px] text-stone-600 font-semibold mb-0.5">${isViLocale() ? 'Thời gian kết thúc' : 'End time'}</label>
                                            <input id="pw-resched-avail-end" type="time" value="16:00"
                                                   class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg bg-white">
                                        </div>
                                    </div>

                                    <div class="flex items-center justify-end space-x-2 pt-1">
                                        <button type="button"
                                                onclick="window.TempoPlanWorkspace.toggleRescheduleAddTime(false)"
                                                class="px-3 py-1.5 border border-gray-200 text-xs font-semibold text-gray-600 rounded-lg hover:bg-stone-50 cursor-pointer">
                                            ${isViLocale() ? 'Hủy' : 'Cancel'}
                                        </button>
                                        <button type="button"
                                                id="btn-save-reschedule-availability"
                                                onclick="window.TempoPlanWorkspace.saveRescheduleAvailability()"
                                                class="px-3.5 py-1.5 bg-[#D99E87] hover:bg-[#C98E77] text-white text-xs font-bold rounded-lg shadow-2xs transition cursor-pointer">
                                            ${isViLocale() ? 'Lưu thời gian làm việc' : 'Save availability'}
                                        </button>
                                    </div>
                                </div>
                            `}

                            <!-- I'll figure it out later option -->
                            <div class="pt-2 border-t border-gray-100">
                                <button onclick="window.TempoPlanWorkspace.scheduleTaskAsUnarranged('${task.id}')"
                                        class="w-full py-2.5 rounded-xl border border-dashed border-stone-300 hover:border-[#FF6B2C] bg-stone-50 hover:bg-white text-xs font-semibold text-stone-700 text-center transition">
                                    ${window.t ? window.t('workspace.figureOutLater', {}, "I'll figure it out later (Move to Unscheduled)") : "I'll figure it out later (Move to Unscheduled)"}
                                </button>
                            </div>
                        </div>

                        <!-- Reschedule Error Banner -->
                        <div id="pw-reschedule-error" class="hidden text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-xl p-2.5 font-medium animate-fade-in"></div>

                        <div class="pt-3 border-t border-gray-100 flex items-center justify-end space-x-2">
                            <button type="button" onclick="window.TempoPlanWorkspace.closeRescheduleModal()"
                                    class="px-4 py-2 border border-gray-200 text-xs font-semibold text-gray-600 rounded-xl hover:bg-stone-50 cursor-pointer">
                                ${window.t ? window.t('common.cancel', {}, 'Cancel') : 'Cancel'}
                            </button>
                            <button type="button"
                                    id="btn-execute-reschedule"
                                    onclick="window.TempoPlanWorkspace.executeReschedule('${task.id}')"
                                    class="btn-primary px-5 py-2 rounded-xl font-bold text-xs shadow-sm cursor-pointer transition">
                                ${window.t ? window.t('workspace.schedule', {}, 'Schedule') : 'Schedule'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        if (activeModal === 'repeat-weekly-config' && repeatConfigDate) {
            const day = (plan.availabilityDays || []).find(d => d.date === repeatConfigDate);
            const dayBlocks = day && Array.isArray(day.blocks) ? day.blocks : [];
            const existingRule = getRecurringRuleForDate(repeatConfigDate);
            const dayLabel = formatScheduledDateLabel(repeatConfigDate, isViLocale()) || repeatConfigDate;

            return `
                <div id="modal-repeat-weekly"
                     onclick="if (event.target === this) window.TempoPlanWorkspace.closeRepeatWeeklyModal();"
                     class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4"
                     role="dialog"
                     aria-modal="true">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-md w-full relative">
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.closeRepeatWeeklyModal()"
                                class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer"
                                title="Close">✕</button>

                        <div class="space-y-1 pr-6">
                            <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124]">
                                ${window.t ? window.t('workspace.repeatWeekly', {}, 'Repeat Weekly') : 'Repeat Weekly'}
                            </h3>
                            <p class="text-xs text-[#6F6B68]">
                                ${escapeHTML(dayLabel)} (${repeatConfigDate})
                            </p>
                        </div>

                        <!-- Current pattern summary -->
                        <div class="p-3 bg-[#FDFBF6] border border-[#E3C7A5] rounded-xl space-y-1.5 text-xs">
                            <div class="font-semibold text-stone-700">
                                ${isViLocale() ? 'Khung giờ lặp lại:' : 'Working hours pattern:'}
                            </div>
                            <div class="text-[#202124] font-medium space-y-0.5">
                                ${dayBlocks.length > 0 ? dayBlocks.map(b => `<div>• ${formatTime12H(b.start)} – ${formatTime12H(b.end)}</div>`).join('') : `<div class="italic text-stone-400">${window.t ? window.t('workspace.noWorkingHours', {}, 'No working hours available.') : 'No working hours available.'}</div>`}
                            </div>
                        </div>

                        <!-- Recurrence Form Settings -->
                        <div class="space-y-3.5 text-xs">
                            <!-- Repeat every week checkbox -->
                            <div class="flex items-center space-x-2.5">
                                <input id="pw-repeat-every-week"
                                       type="checkbox"
                                       ${!existingRule || existingRule.enabled !== false ? 'checked' : ''}
                                       class="w-4 h-4 rounded text-[#D99E87] focus:ring-[#D99E87] cursor-pointer">
                                <label for="pw-repeat-every-week" class="font-bold text-stone-800 cursor-pointer">
                                    ${window.t ? window.t('workspace.repeatEveryWeek', {}, 'Repeat every week') : 'Repeat every week'}
                                </label>
                            </div>

                            <!-- Start date -->
                            <div>
                                <label class="block text-[11px] font-semibold text-stone-600 mb-1">
                                    ${window.t ? window.t('workspace.startDate', {}, 'Start date') : 'Start date'}
                                </label>
                                <input id="pw-repeat-start-date"
                                       type="date"
                                       value="${existingRule?.startDate || repeatConfigDate}"
                                       class="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:outline-none focus:ring-1 focus:ring-[#D99E87]">
                            </div>

                            <!-- End date (optional) -->
                            <div>
                                <label class="block text-[11px] font-semibold text-stone-600 mb-1">
                                    ${window.t ? window.t('workspace.endDate', {}, 'End date (optional)') : 'End date (optional)'}
                                </label>
                                <input id="pw-repeat-end-date"
                                       type="date"
                                       value="${existingRule?.endDate || ''}"
                                       placeholder="YYYY-MM-DD"
                                       class="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:outline-none focus:ring-1 focus:ring-[#D99E87]">
                                <span class="text-[10px] text-stone-400 mt-0.5 block">
                                    ${isViLocale() ? 'Để trống nếu muốn lặp lại liên tục.' : 'Leave empty for ongoing weekly recurrence.'}
                                </span>
                            </div>
                        </div>

                        <!-- Action buttons -->
                        <div class="flex items-center justify-end space-x-3 pt-2 border-t border-gray-100">
                            <button type="button"
                                    onclick="window.TempoPlanWorkspace.closeRepeatWeeklyModal()"
                                    class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-600 hover:text-stone-900 border border-transparent hover:bg-stone-50 transition cursor-pointer">
                                ${window.t ? window.t('workspace.cancel', {}, 'Cancel') : 'Cancel'}
                            </button>
                            <button type="button"
                                    id="btn-confirm-repeat-weekly"
                                    onclick="window.TempoPlanWorkspace.confirmRepeatWeekly()"
                                    class="btn-primary px-5 py-2 rounded-xl text-xs font-bold shadow-sm transition cursor-pointer">
                                ${window.t ? window.t('workspace.confirm', {}, 'Confirm') : 'Confirm'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        if (activeModal === 'adjust-availability') {
            const days = plan.availabilityDays || [];

            return `
                <div class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
                        <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                            <h3 class="font-heading text-lg font-bold text-[#202124]">${window.t ? window.t('workspace.yourAvailableTimeTitle', {}, 'Your available time') : 'Your available time'}</h3>
                            <button onclick="window.TempoPlanWorkspace.closeAdjustAvailabilityModal()" class="text-gray-400 hover:text-gray-600 text-sm">✕</button>
                        </div>

                        <div class="space-y-4 text-xs">
                            ${days.map(d => {
                                const todayStr = getLocalTodayISO();
                                const isToday = (d.date === todayStr);
                                const dayBlocks = Array.isArray(d.blocks) ? d.blocks : [];
                                const recurringRule = getRecurringRuleForDate(d.date);
                                const isRecurring = !!recurringRule && recurringRule.enabled !== false;

                                return `
                                    <div class="p-3.5 bg-stone-50 rounded-2xl border border-stone-100 space-y-2.5" data-avail-day="${d.date}">
                                        <div class="flex flex-wrap items-center justify-between gap-2 font-bold text-stone-800">
                                            <div class="flex items-center space-x-2">
                                                <span class="text-xs sm:text-sm text-[#202124]">${escapeHTML(formatScheduledDateLabel(d.date, isViLocale()) || d.label || d.date)}</span>
                                                <span class="text-[10px] text-stone-500 uppercase tracking-wider">${d.date}</span>
                                                ${isRecurring ? `
                                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#E8EFE8] text-[#556B54] border border-[#C5D8C3]" title="${window.t ? window.t('workspace.repeatEveryWeek', {}, 'Repeat every week') : 'Repeat every week'}">
                                                        🔄 ${isViLocale() ? 'Hàng tuần' : 'Weekly'}
                                                    </span>
                                                ` : ''}
                                            </div>

                                            <!-- Day Actions -->
                                            <div class="flex items-center space-x-1.5 shrink-0">
                                                ${isToday ? `
                                                    <button type="button"
                                                            id="btn-copy-to-tomorrow"
                                                            onclick="window.TempoPlanWorkspace.copyTodayAvailabilityToTomorrow()"
                                                            class="px-2.5 py-1 rounded-xl text-xs font-semibold text-[#688270] bg-[#E8EFE8] hover:bg-[#D5E4D4] border border-[#CCDCCD] transition cursor-pointer flex items-center space-x-1"
                                                            title="${window.t ? window.t('workspace.copyToTomorrow', {}, 'Copy to Tomorrow') : 'Copy to Tomorrow'}">
                                                        <span>📋</span>
                                                        <span>${window.t ? window.t('workspace.copyToTomorrow', {}, 'Copy to Tomorrow') : 'Copy to Tomorrow'}</span>
                                                    </button>
                                                ` : ''}
                                                <button type="button"
                                                        data-repeat-day="${d.date}"
                                                        onclick="window.TempoPlanWorkspace.openRepeatWeeklyModal('${d.date}')"
                                                        class="px-2.5 py-1 rounded-xl text-xs font-semibold ${isRecurring ? 'text-amber-800 bg-amber-100 border border-amber-300 hover:bg-amber-200' : 'text-[#8C6D62] bg-[#F7EFEA] hover:bg-[#EFE3DC] border border-[#E8D7CE]'} transition cursor-pointer flex items-center space-x-1"
                                                        title="${window.t ? window.t('workspace.repeatWeekly', {}, 'Repeat Weekly') : 'Repeat Weekly'}">
                                                    <span>🔄</span>
                                                    <span>${window.t ? window.t('workspace.repeatWeekly', {}, 'Repeat Weekly') : 'Repeat Weekly'}</span>
                                                </button>
                                            </div>
                                        </div>

                                        <div class="space-y-1.5">
                                            ${dayBlocks.length > 0 ? dayBlocks.map(b => `
                                                <div class="p-2 bg-white rounded-xl border border-gray-200 flex items-center justify-between">
                                                    <span class="font-semibold text-[#202124]">${formatTime12H(b.start)} – ${formatTime12H(b.end)}</span>
                                                    <button onclick="window.TempoPlanWorkspace.removeAvailabilityBlock('${d.date}', '${b.id}')"
                                                            class="text-stone-400 hover:text-rose-600 text-xs px-1"
                                                            title="Remove">✕</button>
                                                </div>
                                            `).join('') : `
                                                <div class="text-[11px] text-stone-400 italic py-1">
                                                    ${window.t ? window.t('workspace.noWorkingHours', {}, 'No working hours available to copy.') : 'No working hours available.'}
                                                </div>
                                            `}
                                        </div>
                                    </div>
                                `;
                            }).join('')}

                            <!-- Add availability block form -->
                            <div class="p-3.5 bg-[#FFF8F2] border border-[#FFD2BA] rounded-2xl space-y-2">
                                <span class="font-bold text-[#B83D08] block text-[11px] uppercase tracking-wider">${window.t ? window.t('workspace.addTimeWindow', {}, '+ Add Available Time Window') : '+ Add Available Time Window'}</span>
                                <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                                    <div>
                                        <label class="block text-[10px] text-stone-600 font-semibold mb-0.5">${window.t ? window.t('common.date', {}, 'Date') : 'Date'}</label>
                                        <input id="pw-avail-add-date" type="date" value="${getTodayISO()}"
                                               class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                    </div>
                                    <div>
                                        <label class="block text-[10px] text-stone-600 font-semibold mb-0.5">${window.t ? window.t('common.from', {}, 'From') : 'From'}</label>
                                        <input id="pw-avail-add-start" type="time" value="18:00"
                                               class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                    </div>
                                    <div>
                                        <label class="block text-[10px] text-stone-600 font-semibold mb-0.5">${window.t ? window.t('common.to', {}, 'To') : 'To'}</label>
                                        <input id="pw-avail-add-end" type="time" value="22:00"
                                               class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                    </div>
                                </div>
                                <button onclick="window.TempoPlanWorkspace.addAvailabilityBlockInline()"
                                        class="btn-primary w-full py-1.5 rounded-lg text-xs font-bold mt-1">
                                    ${window.t ? window.t('workspace.addWindowBtn', {}, 'Add window') : 'Add window'}
                                </button>
                            </div>
                        </div>

                        <div class="pt-3 border-t border-gray-100 flex justify-end">
                            <button onclick="window.TempoPlanWorkspace.closeAdjustAvailabilityModal()"
                                    class="btn-primary px-6 py-2 rounded-xl font-bold text-xs shadow-sm">
                                ${window.t ? window.t('common.done', {}, 'Done') : 'Done'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        if (activeModal === 'clear-task-confirm') {
            return `
                <div id="modal-clear-task-confirm"
                     onclick="if (event.target === this) window.TempoPlanWorkspace.closeClearTaskConfirm();"
                     class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4"
                     role="dialog"
                     aria-modal="true"
                     aria-labelledby="clear-task-title">
                    <div class="tempo-card bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-md w-full relative">
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.closeClearTaskConfirm()"
                                class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer"
                                title="${isViLocale() ? 'Đóng' : 'Close'}"
                                aria-label="${isViLocale() ? 'Đóng' : 'Close'}">✕</button>
                        <div class="space-y-2 pr-6">
                            <h3 id="clear-task-title" class="font-heading text-lg sm:text-xl font-bold text-[#202124]">${isViLocale() ? 'Xác nhận gỡ task' : 'Clear Task Confirmation'}</h3>
                            <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                                ${isViLocale() ? 'Task này sẽ được gỡ khỏi Kế hoạch làm việc của bạn. Hành động này không thể hoàn tác.' : 'This task will be removed from your Working Plan. This action cannot be undone.'}
                            </p>
                        </div>
                        <div class="flex items-center justify-end space-x-3 pt-2">
                            <button type="button"
                                    onclick="window.TempoPlanWorkspace.closeClearTaskConfirm()"
                                    class="px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-600 hover:text-stone-900 border border-transparent hover:bg-stone-50 transition cursor-pointer">
                                ${isViLocale() ? 'Hủy' : 'Cancel'}
                            </button>
                            <button type="button"
                                    id="btn-confirm-clear-task"
                                    ${isActionProcessing ? 'disabled' : ''}
                                    onclick="window.TempoPlanWorkspace.executeClearTask()"
                                    class="px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#C53B27] hover:bg-[#B03422] text-white shadow-sm transition cursor-pointer inline-flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed">
                                ${isViLocale() ? 'Xóa task này' : 'Clear task'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        if (activeModal === 'delete-plan-confirm') {
            return `
                <div id="modal-delete-plan-confirm"
                     onclick="if (event.target === this) window.TempoPlanWorkspace.closeDeletePlanConfirm();"
                     class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4"
                     role="dialog"
                     aria-modal="true"
                     aria-labelledby="delete-plan-title">
                    <div class="tempo-card bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-md w-full relative">
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.closeDeletePlanConfirm()"
                                class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer"
                                title="Close"
                                aria-label="Close">✕</button>
                        <div class="space-y-2 pr-6">
                            <h3 id="delete-plan-title" class="font-heading text-lg sm:text-xl font-bold text-[#202124]">${isViLocale() ? 'Xóa plan của bạn?' : 'Delete your plan?'}</h3>
                            <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                                ${isViLocale() ? 'Hành động này sẽ xóa vĩnh viễn Working Plan và các task đã lên lịch. Thao tác này không thể hoàn tác.' : 'This will permanently delete your Working Plan and its scheduled tasks. This action cannot be undone.'}
                            </p>
                        </div>
                        <div class="flex items-center justify-end space-x-3 pt-2">
                            <button type="button"
                                    onclick="window.TempoPlanWorkspace.closeDeletePlanConfirm()"
                                    class="px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-600 hover:text-stone-900 border border-transparent hover:bg-stone-50 transition cursor-pointer">
                                ${isViLocale() ? 'Hủy' : 'Cancel'}
                            </button>
                            <button type="button"
                                    id="btn-confirm-delete-plan"
                                    ${isActionProcessing ? 'disabled' : ''}
                                    onclick="window.TempoPlanWorkspace.executeDeletePlan()"
                                    class="px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#C53B27] hover:bg-[#B03422] text-white shadow-sm transition cursor-pointer inline-flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed">
                                ${isViLocale() ? 'Xóa plan' : 'Delete my plan'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        if (activeModal === 'deadline-plan-reorder-confirm') {
            return `
                <div id="modal-deadline-reorder-confirm"
                     onclick="if (event.target === this) window.TempoPlanWorkspace.cancelDeadlineConfirm();"
                     class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4"
                     role="dialog"
                     aria-modal="true"
                     aria-labelledby="deadline-reorder-title">
                    <div class="tempo-card bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-md w-full relative">
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.cancelDeadlineConfirm()"
                                class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer"
                                title="${isViLocale() ? 'Đóng' : 'Close'}"
                                aria-label="${isViLocale() ? 'Đóng' : 'Close'}">✕</button>
                        <div class="space-y-2 pr-6">
                            <div class="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                                ${isViLocale() ? 'Trùng Deadline' : 'Deadline Conflict'}
                            </div>
                            <h3 id="deadline-reorder-title" class="font-heading text-lg sm:text-xl font-bold text-[#202124]">${isViLocale() ? 'Sắp xếp lại Deadline' : 'Deadline Reorder'}</h3>
                            <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                                ${isViLocale() ? 'Thay đổi deadline này có thể ảnh hưởng đến thứ tự các task. Bạn có muốn Tempo sắp xếp lại thứ tự ưu tiên và kế hoạch của mình không?' : 'Changing this deadline may affect the order of your tasks. Would you like Tempo to adjust your task priorities and reorganize your plan?'}
                            </p>
                        </div>
                        <div class="flex flex-col-reverse sm:flex-row items-center justify-end gap-2.5 sm:space-x-3 pt-2">
                            <button type="button"
                                    id="btn-keep-current-priorities"
                                    onclick="window.TempoPlanWorkspace.confirmDeadlineWithoutReorder()"
                                    class="w-full sm:w-auto px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-700 bg-stone-100 hover:bg-stone-200 border border-stone-200 transition cursor-pointer text-center">
                                ${isViLocale() ? 'Giữ thứ tự hiện tại' : 'Keep current priorities'}
                            </button>
                            <button type="button"
                                    id="btn-confirm-update-plan"
                                    onclick="window.TempoPlanWorkspace.confirmDeadlineWithReorder()"
                                    class="w-full sm:w-auto px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#D99E87] hover:bg-[#C98E77] text-white shadow-sm transition cursor-pointer text-center">
                                ${isViLocale() ? 'Sắp xếp lại Deadline' : 'Yes, update my plan'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        if (activeModal === 'edit-task-note') {
            const noteTaskId = pendingNoteTaskId || selectedTaskId;
            const currentPlan = getActivePlan();
            let targetTask = null;
            if (currentPlan && currentPlan.plannedTasks) {
                const pt = currentPlan.plannedTasks.find(item => item.task && item.task.id === noteTaskId);
                if (pt) targetTask = pt.task;
            }
            if (!targetTask && currentPlan && currentPlan.unarrangedTasks) {
                targetTask = currentPlan.unarrangedTasks.find(t => t.id === noteTaskId);
            }
            const savedNoteObj = window.TempoToolNotes ? window.TempoToolNotes.getNoteForTask(noteTaskId) : null;
            const existingNoteText = savedNoteObj ? savedNoteObj.text : (targetTask && targetTask.note && targetTask.note !== 'Create a sheet to manage references' ? targetTask.note : '');

            return `
                <div id="modal-edit-task-note"
                     onclick="if (event.target === this) window.TempoPlanWorkspace.closeModal();"
                     class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4"
                     role="dialog"
                     aria-modal="true"
                     aria-labelledby="note-editor-title">
                    <div class="tempo-card bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-4 shadow-2xl max-w-md w-full relative">
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.closeModal()"
                                class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer"
                                title="Close"
                                aria-label="Close">✕</button>
                        <div class="space-y-1 pr-6">
                            <h3 id="note-editor-title" class="font-heading text-lg sm:text-xl font-bold text-[#202124]">
                                ${isViLocale() ? 'Chỉnh sửa ghi chú' : (existingNoteText ? 'Edit Task Note' : 'Create Task Note')}
                            </h3>
                            <p class="text-xs text-[#6F6B68]">
                                ${isViLocale() ? 'Ghi chú cho' : 'Note for'} <strong class="text-[#202124]">${escapeHTML(targetTask ? targetTask.name : 'Task')}</strong>
                            </p>
                        </div>
                        <div class="space-y-2">
                            <textarea id="pw-note-editor-text"
                                      rows="4"
                                      placeholder="${isViLocale() ? 'Thêm ghi chú, liên kết hoặc thông tin cho task này...' : 'Add notes, links, or context for this task...'}"
                                      class="w-full px-3.5 py-2.5 text-xs sm:text-sm border border-stone-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#D99E87] focus:border-transparent text-[#202124] resize-y">${escapeHTML(existingNoteText)}</textarea>
                        </div>
                        <div class="flex items-center justify-between pt-2">
                            ${existingNoteText ? `
                                <button type="button"
                                        onclick="window.TempoPlanWorkspace.deleteNote('${noteTaskId}')"
                                        class="text-xs font-semibold text-red-600 hover:text-red-700 hover:underline cursor-pointer">
                                    ${isViLocale() ? 'Xóa ghi chú' : 'Delete note'}
                                </button>
                            ` : '<div></div>'}
                            <div class="flex items-center space-x-2">
                                <button type="button"
                                        onclick="window.TempoPlanWorkspace.closeModal()"
                                        class="px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold text-stone-600 hover:bg-stone-100 transition cursor-pointer">
                                    ${isViLocale() ? 'Hủy' : 'Cancel'}
                                </button>
                                <button type="button"
                                        id="btn-save-task-note"
                                        onclick="window.TempoPlanWorkspace.saveNote('${noteTaskId}')"
                                        class="px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#D99E87] hover:bg-[#C98E77] text-white shadow-sm transition cursor-pointer">
                                    ${isViLocale() ? 'Lưu ghi chú' : 'Save note'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        return '';
    }

    function selectRescheduleWindow(date) {
        rescheduleSelectedWindow = date;
        const plan = getActivePlan();
        if (plan && plan.availabilityDays) {
            const day = plan.availabilityDays.find(d => d.date === date);
            if (day && Array.isArray(day.blocks) && day.blocks.length > 0) {
                const b = day.blocks[0];
                rescheduleSelectedSlot = {
                    id: b.id,
                    date: date,
                    start: b.start,
                    end: b.end
                };
                return;
            }
        }
        rescheduleSelectedSlot = {
            id: `day_${date}`,
            date: date,
            start: null,
            end: null
        };
    }

    function getRescheduleSelectedWindow() {
        return rescheduleSelectedWindow || (rescheduleSelectedSlot ? rescheduleSelectedSlot.date : null);
    }

    function getRescheduleSelectedSlot() {
        return rescheduleSelectedSlot;
    }

    function updateTaskName(taskId, newName) {
        if (!newName || !newName.trim()) return;
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        const pt = plan.plannedTasks.find(item => item.task && item.task.id === taskId);
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }
        if (!task) return;

        task.name = newName.trim();

        // Sync with shared tasks array
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getTasks === 'function') {
            const raw = window.TempoEmergencyFlow.getTasks();
            const shared = raw.find(t => t.id === taskId);
            if (shared) shared.name = task.name;
        }

        persistPlan(plan);
        render();
    }

    function saveTaskDeadline(taskId, newDate, newTime, hasDeadline = true) {
        const plan = getActivePlan();
        if (!plan) return;
        const task = (plan.tasks || []).find(t => t.id === taskId) ||
                     (plan.plannedTasks || []).map(pt => pt.task).find(t => t && t.id === taskId) ||
                     (plan.unarrangedTasks || []).map(u => u.task).find(t => t && t.id === taskId);
        if (task) {
            task.deadlineDate = newDate;
            task.deadlineTime = newTime;
            task.hasDeadline = hasDeadline;
            task.deadline = hasDeadline ? `${newDate} ${newTime || '23:59'}` : null;
            delete task.isOverdue;
            task.isOverdue = false;

            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getTasks === 'function') {
                const rawTasks = window.TempoEmergencyFlow.getTasks();
                const shared = rawTasks.find(t => t.id === taskId);
                if (shared) {
                    shared.hasDeadline = task.hasDeadline;
                    shared.deadlineDate = task.deadlineDate;
                    shared.deadlineTime = task.deadlineTime;
                    shared.deadline = task.deadline;
                    delete shared.isOverdue;
                    shared.isOverdue = false;
                }
            }

            persistPlan(plan);
            if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
                window.TempoMode.renderActiveModeHome();
            }
            render();
        }
    }

    function scheduleUnarrangedTask(taskId, targetDate, startTime, endTime) {
        const plan = getActivePlan();
        if (!plan) return;
        const unarrangedIdx = (plan.unarrangedTasks || []).findIndex(u => (u && u.task ? u.task.id : u.id) === taskId);
        if (unarrangedIdx === -1) return;
        const [removed] = plan.unarrangedTasks.splice(unarrangedIdx, 1);
        const task = removed && removed.task ? removed.task : removed;
        task.planBadge = 'LATER';
        plan.plannedTasks.push({
            dayDate: targetDate,
            dayLabel: targetDate,
            task: task,
            allocatedMinutes: task.durationMinutes || 45,
            scheduledStartTime: startTime || '14:00',
            scheduledEndTime: endTime || '15:00',
            planPositionBadge: 'LATER',
            hasDeadlineRisk: false
        });
        persistPlan(plan);
        render();
    }

    function addNewTask(taskData) {
        let plan = getActivePlan();
        if (!plan) {
            const currentUserId = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') 
                ? window.TempoAuth.getCurrentUserId() 
                : 'guest';
            plan = {
                id: `plan_${currentUserId}_${Date.now()}`,
                title: 'Tempo Working Plan',
                availabilityDays: [],
                plannedTasks: [],
                unarrangedTasks: [],
                tasks: []
            };
        }
        const taskId = 'task-' + Date.now();
        const newTask = {
            id: taskId,
            name: taskData.name || 'New Task',
            deadlineDate: taskData.deadlineDate || null,
            deadlineTime: taskData.deadlineTime || null,
            deadline: taskData.deadlineDate ? `${taskData.deadlineDate} ${taskData.deadlineTime || '23:59'}` : null,
            hasDeadline: !!taskData.deadlineDate,
            durationMinutes: taskData.estimateMinutes || 45,
            durationLabel: `${taskData.estimateMinutes || 45}m`,
            completed: false,
            isInProgress: false,
            subtasks: []
        };
        if (!plan.tasks) plan.tasks = [];
        plan.tasks.push(newTask);
        if (taskData.fitIntoPlan) {
            plan.plannedTasks.push({
                dayDate: getTodayISO(),
                dayLabel: formatScheduledDateLabel(getTodayISO(), isViLocale()) || 'TODAY',
                task: newTask,
                allocatedMinutes: newTask.durationMinutes,
                scheduledStartTime: '16:00',
                scheduledEndTime: '17:00',
                planPositionBadge: 'LATER',
                hasDeadlineRisk: false
            });
        } else {
            if (!plan.unarrangedTasks) plan.unarrangedTasks = [];
            plan.unarrangedTasks.push({
                task: newTask,
                isUnarranged: true,
                reason: 'Unscheduled'
            });
        }
        persistPlan(plan);
        render();
        return newTask;
    }

    if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
        window.TempoI18n.onLanguageChange(() => {
            const wsScreen = document.getElementById('screen-plan-workspace');
            if (wsScreen && !wsScreen.classList.contains('hidden')) {
                render();
            }
        });
    }

    document.addEventListener('keydown', function(e) {
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
    });

    document.addEventListener('click', function(e) {
        if (activeLabelMenuTaskId) {
            const insideMenu = e.target && e.target.closest && e.target.closest('[data-label-menu-container]');
            if (!insideMenu) {
                activeLabelMenuTaskId = null;
                render();
            }
        }
    });

    function loadSampleTasks() {
        const samplePlan = getDefaultReferencePlan();
        persistPlan(samplePlan);
        render();
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(isViLocale() ? 'Đã nạp 3 task mẫu vào kế hoạch.' : 'Loaded 3 sample tasks into your plan.');
        }
    }

    function resetWorkspaceState() {
        selectedTaskId = null;
        pendingAddedTask = null;
        activeModal = null;
    }

    return {
        loadSampleTasks,
        resetWorkspaceState,
        getDefaultReferencePlan,
        startAdjustPlan,
        promptDeletePlan,
        closeDeletePlanConfirm,
        executeDeletePlan,
        deletePlan,
        toggleAddSubtaskInput,
        getActivePlan,
        open,
        render,
        navigateHome,
        startGlobalFocus,
        startTaskFocus,
        toggleTaskComplete,
        selectTask,
        closeDrawer,
        toggleDeadlineEdit,
        saveDeadlineEdit,
        saveTaskDeadline,
        openEstimateEdit,
        promptClearTask,
        closeClearTaskConfirm,
        executeClearTask,
        removeTask,
        addSubtask,
        removeSubtask,
        toggleSubtask,
        setSubtaskCompleted,
        reorderDrawerSubtask,
        handleDragStart,
        handleDragOver,
        handleDragEnter,
        handleDragLeave,
        handleDrop,
        handleDragEnd,
        clearTaskDragStyles,
        isDraggingTask: () => isDraggingTask,
        reorderTasks,
        openRescheduleModal,
        persistPlan,
        getActivePlan,
        closeRescheduleModal,
        toggleRescheduleAddTime,
        saveRescheduleAvailability,
        selectRescheduleSlot,
        getRescheduleSelectedSlot,
        selectRescheduleWindow,
        getRescheduleSelectedWindow,
        scheduleTaskAsUnarranged,
        scheduleUnarrangedTask,
        executeReschedule,
        openAddTaskModal,
        closeAddTaskModal,
        submitAddTask,
        handleFitTaskChoice,
        addNewTask,
        openAdjustAvailabilityModal,
        closeAdjustAvailabilityModal,
        cleanupExpiredAvailability,
        copyTodayAvailabilityToTomorrow,
        openRepeatWeeklyModal,
        closeRepeatWeeklyModal,
        confirmRepeatWeekly,
        getRecurringRules,
        saveRecurringRule,
        disableRecurringRule,
        applyRecurringRulesToPlan,
        addAvailabilityBlockInline,
        removeAvailabilityBlock,
        updateTaskName,
        // Label & AI Replan
        toggleLabelMenu,
        setTaskLabel,
        // Deadline Confirmation Modal
        confirmDeadlineWithReorder,
        confirmDeadlineWithoutReorder,
        cancelDeadlineConfirm,
        // Break Task
        openBreakTaskModal,
        // Task Notes
        openNoteEditor,
        saveNote,
        deleteNote,
        closeModal,
        formatScheduledDateLabel,
        isTaskOverdue,
        isTaskMissedSchedule,
        getTaskState,
        isMissedSchedulePromptDismissed,
        dismissMissedSchedulePrompt,
        clearMissedScheduleDismissal,
        keepCurrentSchedule,
        getLocalTodayISO,
        getLocalTomorrowISO
    };
})();
