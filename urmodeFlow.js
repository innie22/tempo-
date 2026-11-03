/**
 * Tempo Urmode Flow Controller
 * File: urmodeFlow.js
 * 
 * Implements the agreed Urmode entry, Working Plan, task execution,
 * reset, review, and adjustment flows:
 * 
 * 1. Explicit Entry & Reset Popup Trigger (Entry Home, Mode Dropdowns, Change Mode Modal)
 * 2. Three dynamic cases based on actual persisted plan state:
 *    - Case 1: First-time user / user without a Working Plan (Reset path, Build path, Close path)
 *    - Case 2: Existing Working Plan with no overdue tasks (Review summary -> Keep / Adjust)
 *    - Case 3: Existing Working Plan with overdue tasks (Review summary with OVERDUE flags, Dashboard overdue notice & completion)
 * 3. Quick task creation popup ("Finish & focus now" -> Focus Zone, X returns to dashboard)
 * 4. Working Plan Setup Flow completion -> "Your task for now" popup -> Break-task flow
 * 5. Break-task flow over Working Plan tool page -> Start working on your plan -> Focus Zone
 * 6. Non-destructive Working Plan Adjustment flow
 */

window.TempoUrmodeFlow = (function() {
    // -------------------------------------------------------------------------
    // INTERNAL STATE
    // -------------------------------------------------------------------------
    let shouldShowResetOnEntry = false;
    let activeModalView = null; // null | 'reset' | 'are_you_ready' | 'quick_task' | 'review_summary' | 'keep_plan_task' | 'breakdown' | 'start_working_plan' | 'select_another_task' | 'confirm_selected_task' | 'adjust_keep' | 'adjust_tasks' | 'adjust_time' | 'adjust_propose'
    
    let currentFlowCase = 'NO_PLAN'; // 'NO_PLAN' | 'PLAN_NO_OVERDUE' | 'PLAN_WITH_OVERDUE'
    let currentBreakdownTaskId = null;
    let processedBreakdownTaskIds = new Set();
    let selectedWorkTaskId = null;
    let isSubmitting = false;

    // AI Help & Subtask Inline Edit State
    let aiHelpLoading = false;
    let aiHelpError = null;
    let aiHelpSuccess = null;
    let aiConfirmReplace = null;
    let editingSubtaskId = null;

    // Adjustment flow in-memory draft
    let adjustmentDraft = {
        retainedTasks: [],
        newTasks: [],
        availabilityDays: [],
        proposedPlan: null
    };

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

    // Helper: Format duration minutes into human-readable label
    function formatDuration(mins) {
        if (!mins || mins <= 0) mins = 30;
        const h = Math.floor(mins / 60);
        const m = mins % 60;
        if (isViLocale()) {
            if (h > 0 && m > 0) return `${h} giờ ${m} phút`;
            if (h > 0) return `${h} giờ`;
            return `${m} phút`;
        }
        if (h > 0 && m > 0) return `${h} hr ${m} min`;
        if (h > 0) return `${h} hr`;
        return `${m} min`;
    }

    function formatTaskDuration(t) {
        let mins = 0;
        if (typeof t.durationMinutes === 'number' && t.durationMinutes > 0) {
            mins = t.durationMinutes;
        } else if (typeof t.duration === 'number' && t.duration > 0) {
            mins = t.duration;
        } else if (typeof t.estimateMinutes === 'number' && t.estimateMinutes > 0) {
            mins = t.estimateMinutes;
        } else if (typeof t.durationLabel === 'string') {
            const str = t.durationLabel.trim().toLowerCase();
            const hMatch = str.match(/(\d+(?:\.\d+)?)\s*(?:h|hr|hour|giờ)/);
            const mMatch = str.match(/(\d+)\s*(?:m|min|minute|phút)/);
            if (hMatch) mins += parseFloat(hMatch[1]) * 60;
            if (mMatch) mins += parseInt(mMatch[1], 10);
            if (mins > 0) mins = Math.round(mins);
        }
        if (!mins || mins <= 0) mins = 30;
        return formatDuration(mins);
    }

    // Helper: Human deadline
    function formatDeadline(dateStr, timeStr) {
        if (window.TempoI18n && typeof window.TempoI18n.formatDeadline === 'function') {
            return window.TempoI18n.formatDeadline(dateStr, timeStr);
        }
        if (!dateStr) return 'No fixed deadline';
        try {
            const [y, m, d] = dateStr.split('-').map(Number);
            const date = new Date(y, m - 1, d);
            const monthDay = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            if (timeStr) {
                return `${monthDay} · ${timeStr}`;
            }
            return monthDay;
        } catch (e) {
            return `${dateStr}${timeStr ? ' · ' + timeStr : ''}`;
        }
    }

    // -------------------------------------------------------------------------
    // PLAN CONTEXT & TASK UTILITIES
    // -------------------------------------------------------------------------

    function getActiveWorkingPlan() {
        let plan = null;
        if (window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            plan = window.TempoPlanStore.getActivePlan('emergency');
        }
        if (!plan && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            plan = window.TempoEmergencyFlow.getConfirmedPlan();
        }
        return plan;
    }

    function getAllPlanTasks(plan) {
        if (!plan) return [];
        const items = [];
        const seenIds = new Set();

        if (Array.isArray(plan.plannedTasks)) {
            plan.plannedTasks.forEach(pt => {
                if (pt && pt.task && pt.task.id && !seenIds.has(pt.task.id)) {
                    seenIds.add(pt.task.id);
                    items.push({
                        ...pt.task,
                        _dayDate: pt.dayDate || null,
                        _dayLabel: pt.dayLabel || null,
                        _startTime: pt.startTime || null,
                        _endTime: pt.endTime || null,
                        _executionBadge: pt.executionBadge || 'UP NEXT'
                    });
                }
            });
        }

        if (Array.isArray(plan.unarrangedTasks)) {
            plan.unarrangedTasks.forEach(u => {
                const t = (u && u.task) ? u.task : u;
                if (t && t.id && !seenIds.has(t.id)) {
                    seenIds.add(t.id);
                    items.push({
                        ...t,
                        _dayDate: null,
                        _dayLabel: null,
                        _startTime: null,
                        _endTime: null,
                        _executionBadge: 'Not scheduled'
                    });
                }
            });
        }

        if (Array.isArray(plan.tasks)) {
            plan.tasks.forEach(t => {
                if (t && t.id && !seenIds.has(t.id)) {
                    seenIds.add(t.id);
                    items.push({
                        ...t,
                        _dayDate: null,
                        _dayLabel: null,
                        _startTime: null,
                        _endTime: null,
                        _executionBadge: 'Not scheduled'
                    });
                }
            });
        }

        return items;
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

    function formatScheduledDateLabel(dateStr, isVi = false) {
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
            return isViBool ? `Ngày mai · ${calDate}` : `Tomorrow · ${calDate}`;
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
        } else if (task._dayDate || task.dayDate || task.scheduledDate) {
            dayDate = task._dayDate || task.dayDate || task.scheduledDate;
            endTime = task._endTime || task.endTime;
        } else if (plan && Array.isArray(plan.plannedTasks)) {
            const pt = plan.plannedTasks.find(p => p.task && (p.task.id === task.id || p.id === task.id));
            if (pt && pt.dayDate) {
                dayDate = pt.dayDate;
                endTime = pt.endTime || pt.scheduledEndTime;
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

    function determinePlanCase() {
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);

        if (!plan || tasks.length === 0) {
            currentFlowCase = 'NO_PLAN';
            return 'NO_PLAN';
        }

        const overdue = tasks.filter(t => isTaskOverdue(t, plan));
        if (overdue.length > 0) {
            currentFlowCase = 'PLAN_WITH_OVERDUE';
            return 'PLAN_WITH_OVERDUE';
        }

        currentFlowCase = 'PLAN_NO_OVERDUE';
        return 'PLAN_NO_OVERDUE';
    }

    // -------------------------------------------------------------------------
    // ENTRY TRIGGER & FLAG CONSUMPTION
    // -------------------------------------------------------------------------

    function queueResetPopup() {
        shouldShowResetOnEntry = true;
    }

    function shouldShowReset() {
        return shouldShowResetOnEntry;
    }

    function consumeResetFlag() {
        const flag = shouldShowResetOnEntry;
        shouldShowResetOnEntry = false;
        return flag;
    }

    // -------------------------------------------------------------------------
    // MODAL WRAPPER & DISMISSAL
    // -------------------------------------------------------------------------

    function getModalRoot() {
        let modal = document.getElementById('modal-urmode-flow');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'modal-urmode-flow';
            modal.className = 'fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-3 sm:p-6 overflow-y-auto hidden';
            modal.setAttribute('role', 'dialog');
            modal.setAttribute('aria-modal', 'true');
            document.body.appendChild(modal);
        }
        return modal;
    }

    function closeModal(destination = 'dashboard') {
        const modal = getModalRoot();
        modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
        activeModalView = null;
        currentResetCase = null;
        isSubmitting = false;
        aiHelpLoading = false;
        aiHelpError = null;
        aiHelpSuccess = null;
        aiConfirmReplace = null;
        editingSubtaskId = null;

        if (destination === 'dashboard') {
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('today');
            }
            if (window.TempoMode && typeof window.TempoMode.renderEmodeHome === 'function') {
                window.TempoMode.renderEmodeHome();
            }
        } else if (destination === 'plan-workspace') {
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('plan-workspace');
            }
            if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
                window.TempoPlanWorkspace.render();
            }
        }
    }

    function showModalContent(html) {
        const modal = getModalRoot();
        modal.innerHTML = `
            <div class="tempo-card max-w-xl sm:max-w-2xl w-full my-auto bg-[#FEFAF4] rounded-3xl sm:rounded-[28px] p-6 sm:p-8 space-y-5 relative shadow-2xl border border-[#EAE4DF] animate-scale-up">
                ${html}
            </div>
        `;
        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    // -------------------------------------------------------------------------
    // 1. RESET POPUP (On Explicit Entry)
    // -------------------------------------------------------------------------

    let currentResetCase = null;

    function showResetPopup(forcedCase) {
        const caseType = forcedCase || currentResetCase || determinePlanCase();
        currentResetCase = caseType;
        activeModalView = 'reset';

        const isVi = isViLocale();

        let badgeText = '';
        let titleText = '';
        let bodyText = '';
        let primaryBtnText = window.t
            ? window.t('workspace.yesTakeQuickResetBtn', {}, isVi ? 'Có, tôi muốn lấy lại bình tĩnh một chút →' : 'Yes, take a quick reset →')
            : (isVi ? 'Có, tôi muốn lấy lại bình tĩnh một chút →' : 'Yes, take a quick reset →');
        let secondaryBtnText = '';

        if (caseType === 'PLAN_NO_OVERDUE') {
            badgeText = window.t
                ? window.t('workspace.workingPlanActiveBadge', {}, isVi ? 'PLAN ĐANG HOẠT ĐỘNG' : 'WORKING PLAN ACTIVE')
                : (isVi ? 'PLAN ĐANG HOẠT ĐỘNG' : 'WORKING PLAN ACTIVE');
            titleText = window.t
                ? window.t('workspace.reviewAndResetWorkingPlanTitle', {}, isVi ? 'Xem lại và điều chỉnh plan của bạn' : 'Review and reset your Working Plan')
                : (isVi ? 'Xem lại và điều chỉnh plan của bạn' : 'Review and reset your Working Plan');
            bodyText = window.t
                ? window.t('workspace.workingPlanActiveBody', {}, isVi ? 'Bạn đã có một plan đang hoạt động. Hãy dành 2 phút tập thở để lấy lại sự tập trung, hoặc xem lại và tiếp tục kế hoạch hiện tại của bạn.' : 'You already have an active Working Plan saved. Take a 2-minute reset to ground your focus, or review and keep your existing plan.')
                : (isVi ? 'Bạn đã có một plan đang hoạt động. Hãy dành 2 phút tập thở để lấy lại sự tập trung, hoặc xem lại và tiếp tục kế hoạch hiện tại của bạn.' : 'You already have an active Working Plan saved. Take a 2-minute reset to ground your focus, or review and keep your existing plan.');
            secondaryBtnText = window.t
                ? window.t('workspace.reviewYourPlanBtn', {}, isVi ? 'Xem lại plan' : 'Review your plan')
                : (isVi ? 'Xem lại plan' : 'Review your plan');
        } else if (caseType === 'PLAN_WITH_OVERDUE') {
            badgeText = window.t
                ? window.t('workspace.planUpdateNeededBadge', {}, isVi ? 'PLAN CẦN ĐƯỢC CẬP NHẬT' : 'PLAN UPDATE NEEDED')
                : (isVi ? 'PLAN CẦN ĐƯỢC CẬP NHẬT' : 'PLAN UPDATE NEEDED');
            titleText = window.t
                ? window.t('workspace.reviewAndResetWorkingPlanTitle', {}, isVi ? 'Xem lại và điều chỉnh plan của bạn' : 'Review and reset your Working Plan')
                : (isVi ? 'Xem lại và điều chỉnh plan của bạn' : 'Review and reset your Working Plan');
            bodyText = window.t
                ? window.t('workspace.planUpdateNeededBody', {}, isVi ? 'Bạn có một số task đã quá deadline cần được xem lại. Hãy dành chút thời gian để lấy lại bình tĩnh, hoặc xem lại các task và điều chỉnh lịch trình của mình nhé.' : 'You have tasks with overdue deadlines that need your attention. Take a quick reset to calm down, or review your tasks and adjust your schedule.')
                : (isVi ? 'Bạn có một số task đã quá deadline cần được xem lại. Hãy dành chút thời gian để lấy lại bình tĩnh, hoặc xem lại các task và điều chỉnh lịch trình của mình nhé.' : 'You have tasks with overdue deadlines that need your attention. Take a quick reset to calm down, or review your tasks and adjust your schedule.');
            secondaryBtnText = window.t
                ? window.t('workspace.reviewYourPlanBtn', {}, isVi ? 'Xem lại plan' : 'Review your plan')
                : (isVi ? 'Xem lại plan' : 'Review your plan');
        } else {
            // NO_PLAN
            badgeText = window.t
                ? window.t('workspace.groundedStartBadge', {}, isVi ? 'KHỞI ĐẦU ĐIỀM TĨNH' : 'GROUNDED START')
                : (isVi ? 'KHỞI ĐẦU ĐIỀM TĨNH' : 'GROUNDED START');
            titleText = window.t
                ? window.t('workspace.groundedStartTitle', {}, isVi ? 'Dành một chút thời gian để lấy lại bình tĩnh?' : 'Take a moment to reset?')
                : (isVi ? 'Dành một chút thời gian để lấy lại bình tĩnh?' : 'Take a moment to reset?');
            bodyText = window.t
                ? window.t('workspace.groundedStartBody', {}, isVi ? 'Những tình huống khẩn cấp sẽ nhẹ nhàng hơn rất nhiều khi bạn tạm dừng lại một chút. Bạn có muốn dành 2 phút tập thở để làm dịu thần kinh trước khi sắp xếp các task không?' : 'Urgent situations feel much lighter when you pause first. Would you like a 2-minute reset to calm your nervous system before organizing your tasks?')
                : (isVi ? 'Những tình huống khẩn cấp sẽ nhẹ nhàng hơn rất nhiều khi bạn tạm dừng lại một chút. Bạn có muốn dành 2 phút tập thở để làm dịu thần kinh trước khi sắp xếp các task không?' : 'Urgent situations feel much lighter when you pause first. Would you like a 2-minute reset to calm your nervous system before organizing your tasks?');
            secondaryBtnText = window.t
                ? window.t('workspace.buildMyPlanBtn', {}, isVi ? 'Lên plan của tôi' : 'Build my plan')
                : (isVi ? 'Lên plan của tôi' : 'Build my plan');
        }

        const featureBoxBreathing = window.t
            ? window.t('workspace.boxBreathingFeature', {}, isVi ? 'Tập thở trong 2 phút' : '2 min box breathing')
            : (isVi ? 'Tập thở trong 2 phút' : '2 min box breathing');
        const featureGroundsFocus = window.t
            ? window.t('workspace.groundsFocusFeature', {}, isVi ? 'Giúp bạn lấy lại sự tập trung' : 'Grounds focus')
            : (isVi ? 'Giúp bạn lấy lại sự tập trung' : 'Grounds focus');
        const featureNoRush = window.t
            ? window.t('workspace.noRushFeature', {}, isVi ? 'Không cần vội' : 'No rush')
            : (isVi ? 'Không cần vội' : 'No rush');

        const primaryBtnFormatted = primaryBtnText.endsWith('→') ? primaryBtnText : (primaryBtnText + ' →');

        const html = `
            <!-- Header -->
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${badgeText}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${titleText}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.handleResetClose()"
                        aria-label="${window.t ? window.t('common.close', {}, isVi ? 'Đóng' : 'Close dialog') : (isVi ? 'Đóng' : 'Close dialog')}"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="${window.t ? window.t('common.close', {}, isVi ? 'Đóng' : 'Close dialog') : (isVi ? 'Đóng' : 'Close dialog')}">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Mascot & Body Row -->
            <div class="flex flex-col sm:flex-row items-center sm:items-start gap-4 py-2">
                <div class="w-20 h-20 rounded-2xl bg-[#FFE9DC] flex items-center justify-center shrink-0 shadow-xs">
                    <img src="assets/practice-breathing-mascot.png" alt="Reset Breathing" class="w-16 h-16 object-contain pointer-events-none select-none" />
                </div>
                <div class="space-y-2 text-center sm:text-left">
                    <p class="text-sm sm:text-base text-[#484541] leading-relaxed">
                        ${bodyText}
                    </p>
                    <div class="text-xs text-[#8C8782] flex items-center justify-center sm:justify-start gap-2 pt-1">
                        <span>🌱 ${featureBoxBreathing}</span>
                        <span>•</span>
                        <span>${featureGroundsFocus}</span>
                        <span>•</span>
                        <span>${featureNoRush}</span>
                    </div>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.handleResetNoOrPlan()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                    ${secondaryBtnText}
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.handleResetYes()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                    <span>${primaryBtnFormatted}</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }

    function handleResetYes() {
        closeModal(null); // Keep modal open in background / don't reset dashboard
        if (window.TempoStressRelief && typeof window.TempoStressRelief.openBreathing === 'function') {
            window.TempoStressRelief.openBreathing({
                context: 'emergency_reset',
                onReady: () => {
                    showAreYouReadyPopup();
                }
            });
        } else {
            showAreYouReadyPopup();
        }
    }

    function handleResetNoOrPlan() {
        const caseType = determinePlanCase();
        closeModal(null);

        if (caseType === 'NO_PLAN') {
            startSetupFlow();
        } else {
            showReviewSummaryPopup();
        }
    }

    function handleResetClose() {
        closeModal('dashboard');
    }

    // -------------------------------------------------------------------------
    // 2. "ARE YOU READY?" POPUP (Post-Breathing Checkpoint)
    // -------------------------------------------------------------------------

    function showAreYouReadyPopup() {
        activeModalView = 'are_you_ready';
        const caseType = determinePlanCase();
        const isVi = isViLocale();

        const badgeText = window.t
            ? window.t('workspace.groundedCheckpointBadge', {}, isVi ? 'ĐIỂM DỪNG ĐIỀM TĨNH' : 'GROUNDED CHECKPOINT')
            : (isVi ? 'ĐIỂM DỪNG ĐIỀM TĨNH' : 'GROUNDED CHECKPOINT');
        const titleText = window.t
            ? window.t('workspace.areYouReadyTitle', {}, isVi ? 'Bạn đã sẵn sàng chưa?' : 'Are you ready?')
            : (isVi ? 'Bạn đã sẵn sàng chưa?' : 'Are you ready?');
        const bodyText = window.t
            ? window.t('workspace.areYouReadyBody', {}, isVi ? 'Bạn vừa dành thời gian để thở và lấy lại bình tĩnh. Bạn cảm thấy thế nào về việc bắt đầu với Kế hoạch Làm việc bây giờ?' : 'You took a moment to breathe and reset. How do you feel about moving into your Working Plan now?')
            : (isVi ? 'Bạn vừa dành thời gian để thở và lấy lại bình tĩnh. Bạn cảm thấy thế nào về việc bắt đầu với Kế hoạch Làm việc bây giờ?' : 'You took a moment to breathe and reset. How do you feel about moving into your Working Plan now?');
        const subText = window.t
            ? window.t('workspace.areYouReadySub', {}, isVi ? 'Nếu bạn vẫn cảm thấy quá tải, bạn có thể quay lại nghỉ ngơi thêm bất cứ lúc nào.' : 'If you still feel overwhelmed, you can return to take another pause or rest anytime.')
            : (isVi ? 'Nếu bạn vẫn cảm thấy quá tải, bạn có thể quay lại nghỉ ngơi thêm bất cứ lúc nào.' : 'If you still feel overwhelmed, you can return to take another pause or rest anytime.');
        const notYetBtnText = window.t
            ? window.t('workspace.notYetReturnResetBtn', {}, isVi ? 'Chưa, quay lại tập thở' : 'Not yet, return to reset')
            : (isVi ? 'Chưa, quay lại tập thở' : 'Not yet, return to reset');
        const readyBtnText = window.t
            ? window.t('workspace.yesImReadyBtn', {}, isVi ? 'Có, tôi đã sẵn sàng →' : "Yes, I'm ready →")
            : (isVi ? 'Có, tôi đã sẵn sàng →' : "Yes, I'm ready →");
        const closeBtnText = window.t
            ? window.t('common.close', {}, isVi ? 'Đóng' : 'Close dialog')
            : (isVi ? 'Đóng' : 'Close dialog');

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-emerald-700 block">
                        ${badgeText}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${titleText}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        aria-label="${escapeHTML(closeBtnText)}"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="${escapeHTML(closeBtnText)}">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <div class="py-3 text-center sm:text-left space-y-2">
                <p class="text-sm sm:text-base text-[#484541] leading-relaxed">
                    ${bodyText}
                </p>
                <p class="text-xs text-[#8C8782]">
                    ${subText}
                </p>
            </div>

            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.showResetPopup()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                    ${notYetBtnText}
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.handleAreYouReadyYes()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                    <span>${readyBtnText}</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }

    let isHandlingAreYouReady = false;
    function handleAreYouReadyYes() {
        if (isHandlingAreYouReady) return;
        isHandlingAreYouReady = true;
        try {
            const caseType = determinePlanCase();
            closeModal(null);

            if (caseType === 'NO_PLAN') {
                startSetupFlow();
            } else {
                showReviewSummaryPopup();
            }
        } finally {
            setTimeout(() => { isHandlingAreYouReady = false; }, 300);
        }
    }

    // -------------------------------------------------------------------------
    // 3. START WORKING PLAN SETUP FLOW
    // -------------------------------------------------------------------------

    function startSetupFlow() {
        closeModal(null);
        if (window.TempoEmergencyFlow) {
            if (window.TempoEmergencyFlow.startFreshPlan) {
                window.TempoEmergencyFlow.startFreshPlan();
            }
            window.TempoEmergencyFlow.goToStage('reality-check');
        }
        if (window.TempoApp) {
            window.TempoApp.navigateTo('emergency');
        }
    }

    // -------------------------------------------------------------------------
    // 4. QUICK TASK CREATION POPUP
    // -------------------------------------------------------------------------

    function openQuickTaskModal() {
        activeModalView = 'quick_task';
        const now = new Date();
        const pad = n => String(n).padStart(2, '0');
        const defaultTime = `${pad((now.getHours() + 2) % 24)}:00`;
        const todayStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        QUICK TASK EXECUTION
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        Execute a task now
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        aria-label="Close dialog"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <form id="form-quick-task" onsubmit="window.TempoUrmodeFlow.handleQuickTaskSubmit(event)" class="space-y-4 py-2">
                <!-- Task Name -->
                <div class="space-y-1.5">
                    <label for="quick-task-name" class="block text-xs font-bold text-[#484541] uppercase tracking-wider">
                        Task Name <span class="text-rose-500">*</span>
                    </label>
                    <input type="text" id="quick-task-name" required autofocus
                           placeholder="e.g. Finish economics chapter 4 notes"
                           class="w-full px-4 py-2.5 rounded-xl border border-[#D1C7BD] bg-white text-sm text-[#202124] placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-[#D79277] focus:border-transparent transition" />
                </div>

                <!-- Duration Picker -->
                <div class="space-y-1.5">
                    <label class="block text-xs font-bold text-[#484541] uppercase tracking-wider">
                        Estimated Duration
                    </label>
                    <div class="flex flex-wrap items-center gap-2" id="quick-task-duration-group">
                        <button type="button" onclick="window.TempoUrmodeFlow.selectQuickDuration(15, this)"
                                class="quick-duration-pill px-3 py-1.5 rounded-full text-xs font-bold border border-stone-200 bg-white text-stone-700 hover:border-[#D79277] transition cursor-pointer">
                            15 min
                        </button>
                        <button type="button" onclick="window.TempoUrmodeFlow.selectQuickDuration(30, this)"
                                class="quick-duration-pill px-3 py-1.5 rounded-full text-xs font-bold border-2 border-[#D79277] bg-[#FFE9DC] text-[#B83D08] transition cursor-pointer">
                            30 min
                        </button>
                        <button type="button" onclick="window.TempoUrmodeFlow.selectQuickDuration(45, this)"
                                class="quick-duration-pill px-3 py-1.5 rounded-full text-xs font-bold border border-stone-200 bg-white text-stone-700 hover:border-[#D79277] transition cursor-pointer">
                            45 min
                        </button>
                        <button type="button" onclick="window.TempoUrmodeFlow.selectQuickDuration(60, this)"
                                class="quick-duration-pill px-3 py-1.5 rounded-full text-xs font-bold border border-stone-200 bg-white text-stone-700 hover:border-[#D79277] transition cursor-pointer">
                            1 hr
                        </button>
                    </div>
                    <input type="hidden" id="quick-task-duration" value="30" />
                </div>

                <!-- Optional Deadline -->
                <div class="space-y-2 pt-1 border-t border-stone-100">
                    <label class="inline-flex items-center space-x-2 cursor-pointer select-none">
                        <input type="checkbox" id="quick-task-has-deadline" onchange="window.TempoUrmodeFlow.toggleQuickDeadlineInputs(this.checked)"
                               class="w-4 h-4 rounded text-[#D79277] focus:ring-[#D79277] border-gray-300 cursor-pointer" />
                        <span class="text-xs font-semibold text-[#484541]">Add a deadline for this task</span>
                    </label>

                    <div id="quick-task-deadline-fields" class="hidden flex flex-wrap items-center gap-2 pt-1">
                        <input type="date" id="quick-task-deadline-date" value="${todayStr}"
                               class="px-3 py-1.5 rounded-xl border border-[#D1C7BD] text-xs font-medium text-[#202124] focus:ring-1 focus:ring-[#D79277] focus:outline-none" />
                        <input type="time" id="quick-task-deadline-time" value="${defaultTime}"
                               class="px-3 py-1.5 rounded-xl border border-[#D1C7BD] text-xs font-medium text-[#202124] focus:ring-1 focus:ring-[#D79277] focus:outline-none" />
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                    <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                            class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                        Cancel
                    </button>
                    <button type="submit" id="btn-quick-task-submit"
                            class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                        <span>Finish & focus now →</span>
                    </button>
                </div>
            </form>
        `;

        showModalContent(html);
    }

    function selectQuickDuration(mins, btn) {
        const input = document.getElementById('quick-task-duration');
        if (input) input.value = mins;
        document.querySelectorAll('.quick-duration-pill').forEach(el => {
            el.className = 'quick-duration-pill px-3 py-1.5 rounded-full text-xs font-bold border border-stone-200 bg-white text-stone-700 hover:border-[#D79277] transition cursor-pointer';
        });
        if (btn) {
            btn.className = 'quick-duration-pill px-3 py-1.5 rounded-full text-xs font-bold border-2 border-[#D79277] bg-[#FFE9DC] text-[#B83D08] transition cursor-pointer';
        }
    }

    function toggleQuickDeadlineInputs(checked) {
        const box = document.getElementById('quick-task-deadline-fields');
        if (box) {
            box.classList.toggle('hidden', !checked);
        }
    }

    function handleQuickTaskSubmit(e) {
        if (e) e.preventDefault();
        if (isSubmitting) return;

        const nameInput = document.getElementById('quick-task-name');
        const taskName = nameInput ? nameInput.value.trim() : '';
        if (!taskName) return;

        const durInput = document.getElementById('quick-task-duration');
        const durationMinutes = parseInt(durInput?.value || '30', 10) || 30;

        const hasDeadline = document.getElementById('quick-task-has-deadline')?.checked || false;
        const deadlineDate = hasDeadline ? document.getElementById('quick-task-deadline-date')?.value || null : null;
        const deadlineTime = hasDeadline ? document.getElementById('quick-task-deadline-time')?.value || null : null;

        isSubmitting = true;

        const now = new Date();
        const pad = n => String(n).padStart(2, '0');
        const todayStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

        const newTask = {
            id: 'task-quick-' + Date.now(),
            name: taskName,
            description: '',
            hasDeadline: Boolean(hasDeadline && deadlineDate),
            deadlineDate: deadlineDate,
            deadlineTime: deadlineTime,
            durationMinutes: durationMinutes,
            durationLabel: formatDuration(durationMinutes),
            completed: false,
            isInProgress: true,
            subtasks: []
        };

        // Persist task into confirmedPlan (or create a clean minimal Working Plan)
        let plan = getActiveWorkingPlan();
        if (!plan) {
            plan = {
                id: 'plan_quick_' + Date.now(),
                planId: 'plan_quick_' + Date.now(),
                planType: 'emergency',
                title: 'Working Plan',
                plannedTasks: [
                    {
                        dayDate: todayStr,
                        dayLabel: 'Today',
                        startTime: '10:00 AM',
                        endTime: '11:00 AM',
                        executionBadge: 'DO THIS FIRST',
                        task: newTask
                    }
                ],
                unarrangedTasks: [],
                tasks: [newTask],
                availabilityDays: [
                    { date: todayStr, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }
                ]
            };
        } else {
            if (!Array.isArray(plan.plannedTasks)) plan.plannedTasks = [];
            if (!Array.isArray(plan.tasks)) plan.tasks = [];

            plan.plannedTasks.unshift({
                dayDate: todayStr,
                dayLabel: 'Today',
                startTime: 'Now',
                executionBadge: 'DO THIS FIRST',
                task: newTask
            });
            plan.tasks.unshift(newTask);
        }

        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            window.TempoPlanStore.saveActivePlan('emergency', plan);
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
            window.TempoEmergencyFlow.setConfirmedPlan(plan);
        }

        closeModal('dashboard');

        // Launch Focus Zone for this quick task
        if (window.TempoFocusZone && typeof window.TempoFocusZone.open === 'function') {
            window.TempoFocusZone.open({ taskId: newTask.id });
        } else if (window.TempoMode && typeof window.TempoMode.startTaskFocus === 'function') {
            window.TempoMode.startTaskFocus(newTask.id);
        }
    }

    // -------------------------------------------------------------------------
    // 5. REVIEW SUMMARY POPUP (Existing Working Plan)
    // -------------------------------------------------------------------------

    function formatExecutionBadge(rawBadge, isVi) {
        if (!rawBadge) return isVi ? 'TIẾP THEO' : 'UP NEXT';
        const normalized = String(rawBadge).trim().toUpperCase();
        if (normalized === 'UP NEXT') {
            return window.t
                ? window.t('workspace.badgeUpNext', {}, isVi ? 'TIẾP THEO' : 'UP NEXT')
                : (isVi ? 'TIẾP THEO' : 'UP NEXT');
        }
        if (normalized === 'THEN') {
            return window.t
                ? window.t('workspace.badgeThen', {}, isVi ? 'SAU ĐÓ' : 'THEN')
                : (isVi ? 'SAU ĐÓ' : 'THEN');
        }
        if (normalized === 'LATER') {
            return window.t
                ? window.t('workspace.badgeLater', {}, isVi ? 'ĐỂ SAU' : 'LATER')
                : (isVi ? 'ĐỂ SAU' : 'LATER');
        }
        if (normalized === 'OVERDUE') {
            return window.t
                ? window.t('workspace.badgeOverdue', {}, isVi ? 'QUÁ HẠN' : 'OVERDUE')
                : (isVi ? 'QUÁ HẠN' : 'OVERDUE');
        }
        return rawBadge;
    }

    function showReviewSummaryPopup() {
        activeModalView = 'review_summary';
        const isVi = isViLocale();
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const overdueCount = tasks.filter(t => isTaskOverdue(t, plan)).length;

        const badgeText = window.t
            ? window.t('workspace.workingPlanReviewBadge', {}, isVi ? 'XEM LẠI PLAN' : 'WORKING PLAN REVIEW')
            : (isVi ? 'XEM LẠI PLAN' : 'WORKING PLAN REVIEW');
        const titleText = window.t
            ? window.t('workspace.workingPlanSummaryTitle', {}, isVi ? 'Tổng quan kế hoạch làm việc' : 'Your Working Plan Summary')
            : (isVi ? 'Tổng quan kế hoạch làm việc' : 'Your Working Plan Summary');
        const closeBtnText = window.t
            ? window.t('common.close', {}, isVi ? 'Đóng' : 'Close dialog')
            : (isVi ? 'Đóng' : 'Close dialog');

        const overdueCountText = window.t
            ? (isVi
                ? window.t('workspace.tasksOverdueCount', { count: overdueCount }, `${overdueCount} task đã quá hạn:`)
                : (overdueCount === 1
                    ? window.t('workspace.taskOverdueSingleCount', { count: overdueCount }, '1 task overdue:')
                    : window.t('workspace.tasksOverdueCount', { count: overdueCount }, `${overdueCount} tasks overdue:`)))
            : (isVi ? `${overdueCount} task đã quá hạn:` : (overdueCount === 1 ? '1 task overdue:' : `${overdueCount} tasks overdue:`));

        const overdueDescText = window.t
            ? window.t('workspace.overdueWarningDesc', {}, isVi ? 'Một số task đã quá ngày lên lịch hoặc deadline. Bạn có thể giữ lại hoặc điều chỉnh lịch trình.' : 'Some tasks passed their planned date or deadline. You can keep them or adjust your schedule.')
            : (isVi ? 'Một số task đã quá ngày lên lịch hoặc deadline. Bạn có thể giữ lại hoặc điều chỉnh lịch trình.' : 'Some tasks passed their planned date or deadline. You can keep them or adjust your schedule.');

        const overdueBadgeText = window.t
            ? window.t('workspace.badgeOverdue', {}, isVi ? 'QUÁ HẠN' : 'OVERDUE')
            : (isVi ? 'QUÁ HẠN' : 'OVERDUE');

        const noDeadlineText = window.t
            ? window.t('workspace.noFixedDeadlineLabel', {}, isVi ? 'Chưa có deadline' : 'No fixed deadline')
            : (isVi ? 'Chưa có deadline' : 'No fixed deadline');

        const adjustPlanBtnText = window.t
            ? window.t('workspace.adjustMyPlanBtn', {}, isVi ? 'Điều chỉnh plan' : 'Adjust my plan')
            : (isVi ? 'Điều chỉnh plan' : 'Adjust my plan');

        const keepPlanBtnText = window.t
            ? window.t('workspace.keepThePlanBtn', {}, isVi ? 'Giữ nguyên plan →' : 'Keep the plan →')
            : (isVi ? 'Giữ nguyên plan →' : 'Keep the plan →');

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${badgeText}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${titleText}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        aria-label="${closeBtnText}"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="${closeBtnText}">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Overdue Warning Banner if applicable -->
            ${overdueCount > 0 ? `
                <div class="p-3 bg-amber-50 border border-amber-200/80 rounded-2xl flex items-center space-x-3 text-xs text-amber-900">
                    <span class="text-base shrink-0">⚠️</span>
                    <div>
                        <strong class="font-bold">${overdueCountText}</strong>
                        <span>${overdueDescText}</span>
                    </div>
                </div>
            ` : ''}

            <!-- Task List -->
            <div class="max-h-64 sm:max-h-72 overflow-y-auto space-y-2 pr-1 py-1">
                ${tasks.map((t, idx) => {
                    const overdue = isTaskOverdue(t, plan);
                    const deadlineStr = t.hasDeadline && t.deadlineDate ? formatDeadline(t.deadlineDate, t.deadlineTime) : noDeadlineText;
                    const durStr = t.durationLabel || formatDuration(t.durationMinutes);
                    const isDone = t.completed === true;

                    return `
                        <div class="p-3 rounded-2xl border ${overdue ? 'border-amber-300 bg-amber-50/40' : 'border-stone-200 bg-white'} flex items-center justify-between text-xs transition">
                            <div class="flex items-center space-x-2.5 min-w-0 flex-1 mr-2">
                                <span class="font-bold text-stone-400 w-5 shrink-0 text-center">${idx + 1}.</span>
                                <div class="min-w-0">
                                    <div class="font-bold text-stone-800 truncate ${isDone ? 'line-through text-stone-400' : ''}">
                                        ${escapeHTML(t.name)}
                                    </div>
                                    <div class="text-[11px] text-stone-500 flex items-center space-x-2 mt-0.5">
                                        <span>${escapeHTML(deadlineStr)}</span>
                                        <span>•</span>
                                        <span>~${escapeHTML(durStr)}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="flex items-center space-x-1.5 shrink-0">
                                ${overdue ? `
                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                                        ${overdueBadgeText}
                                    </span>
                                ` : ''}
                                ${isDone ? `
                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700">
                                        ✓ ${isVi ? 'Đã xong' : 'Done'}
                                    </span>
                                ` : `
                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-stone-100 text-stone-600">
                                        ${escapeHTML(formatExecutionBadge(t._executionBadge || 'UP NEXT', isVi))}
                                    </span>
                                `}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>

            <!-- Action Buttons: Keep Plan vs Adjust Plan -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.startAdjustmentFlow()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                    ${adjustPlanBtnText}
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.showKeepPlanTaskPopup()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                    <span>${keepPlanBtnText}</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }

    function showKeepPlanTaskPopup() {
        activeModalView = 'keep_plan_task';
        const isVi = isViLocale();
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const topTask = tasks.find(t => !t.completed) || tasks[0];

        if (!topTask) {
            closeModal('dashboard');
            return;
        }

        const noDeadlineText = window.t
            ? window.t('workspace.noFixedDeadlineLabel', {}, isVi ? 'Chưa có deadline' : 'No fixed deadline')
            : (isVi ? 'Chưa có deadline' : 'No fixed deadline');

        const deadlineStr = topTask.hasDeadline && topTask.deadlineDate 
            ? formatDeadline(topTask.deadlineDate, topTask.deadlineTime) 
            : noDeadlineText;
        const durStr = topTask.durationLabel || formatDuration(topTask.durationMinutes);
        const subtasks = Array.isArray(topTask.subtasks) ? topTask.subtasks : [];

        const badgeText = window.t
            ? window.t('workspace.yourTaskForNowBadge', {}, isVi ? 'TASK HIỆN TẠI CỦA BẠN' : 'YOUR TASK FOR NOW')
            : (isVi ? 'TASK HIỆN TẠI CỦA BẠN' : 'YOUR TASK FOR NOW');

        const headingText = window.t
            ? window.t('workspace.yourTaskForNowHeading', {}, isVi ? 'Task bạn nên thực hiện lúc này là…' : 'Your task for now is…')
            : (isVi ? 'Task bạn nên thực hiện lúc này là…' : 'Your task for now is…');

        const doThisFirstText = window.t
            ? window.t('workspace.doThisFirstPriority', {}, isVi ? 'ƯU TIÊN LÀM TRƯỚC' : 'DO THIS FIRST')
            : (isVi ? 'ƯU TIÊN LÀM TRƯỚC' : 'DO THIS FIRST');

        const dueLabelText = window.t
            ? window.t('workspace.duePrefixLabel', {}, 'Deadline:')
            : 'Deadline:';

        const laterBtnText = window.t
            ? window.t('workspace.laterBtn', {}, isVi ? 'Để sau' : 'Later')
            : (isVi ? 'Để sau' : 'Later');

        const focusNowBtnText = window.t
            ? window.t('workspace.focusNowBtn', {}, isVi ? 'Tập trung ngay →' : 'Focus now →')
            : (isVi ? 'Tập trung ngay →' : 'Focus now →');

        const closeBtnText = window.t
            ? window.t('common.close', {}, isVi ? 'Đóng' : 'Close dialog')
            : (isVi ? 'Đóng' : 'Close dialog');

        const actionStepsText = isVi ? 'Các bước thực hiện:' : 'Action steps:';

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${badgeText}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${headingText}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        aria-label="${closeBtnText}"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="${closeBtnText}">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Task Summary Card -->
            <div class="p-4 rounded-2xl border-2 border-[#D79277] bg-[#FFF9F5] space-y-2">
                <div class="flex items-center justify-between">
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#D79277] text-white">
                        ${doThisFirstText}
                    </span>
                    <span class="text-xs text-stone-500 font-medium">~${escapeHTML(durStr)}</span>
                </div>
                <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124]">
                    ${escapeHTML(topTask.name || topTask.title)}
                </h3>
                <div class="text-xs text-[#6F6B68] flex items-center space-x-2">
                    <span>📅 ${dueLabelText} ${escapeHTML(deadlineStr)}</span>
                </div>

                ${subtasks.length > 0 ? `
                    <div class="pt-2 border-t border-stone-200/60 space-y-1">
                        <div class="text-[11px] font-bold uppercase tracking-wider text-stone-500">${actionStepsText}</div>
                        ${subtasks.map(s => `
                            <div class="flex items-center space-x-2 text-xs text-stone-700">
                                <span>${s.completed ? '✓' : '○'}</span>
                                <span class="${s.completed ? 'line-through text-stone-400' : ''}">${escapeHTML(s.title || s.name)}</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>

            <!-- Action Buttons: Focus Now vs Later -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                    ${laterBtnText}
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.launchFocusForTask('${topTask.id}')"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                    <span>${focusNowBtnText}</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }

    function launchFocusForTask(taskId) {
        closeModal('dashboard');
        if (window.TempoFocusZone && typeof window.TempoFocusZone.open === 'function') {
            window.TempoFocusZone.open({ taskId });
        } else if (window.TempoMode && typeof window.TempoMode.startTaskFocus === 'function') {
            window.TempoMode.startTaskFocus(taskId);
        }
    }

    // -------------------------------------------------------------------------
    // 6. OVERDUE TASK ACTIONS ON DASHBOARD
    // -------------------------------------------------------------------------

    function markOverdueTaskFinished(taskId) {
        if (!taskId) return;
        if (window.TempoMode && typeof window.TempoMode.toggleTaskCompletion === 'function') {
            window.TempoMode.toggleTaskCompletion(taskId);
        } else if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.toggleTaskCompleted === 'function') {
            window.TempoEmergencyFlow.toggleTaskCompleted(taskId);
        }
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("Đã đánh dấu hoàn thành task quá hạn.");
        }
        if (window.TempoMode && typeof window.TempoMode.renderEmodeHome === 'function') {
            window.TempoMode.renderEmodeHome();
        }
    }

    // -------------------------------------------------------------------------
    // 7. POST-SAVE "YOUR TASK FOR NOW" & BREAK-TASK FLOW
    // -------------------------------------------------------------------------

    let lastPostSavePlan = null;

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
            deadlineDisplay = `Deadline: ${formattedDate}`;
        } else {
            deadlineDisplay = window.t ? window.t('workspace.dueNoFixedDeadline', {}, (isViLocale() ? 'Deadline: Chưa có deadline' : 'Deadline: No fixed deadline')) : (isViLocale() ? 'Deadline: Chưa có deadline' : 'Deadline: No fixed deadline');
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
    }

    function startBreakTaskFlow(firstTaskId) {
        processedBreakdownTaskIds = new Set();
        currentBreakdownTaskId = firstTaskId;
        aiHelpLoading = false;
        aiHelpError = null;
        aiHelpSuccess = null;
        aiConfirmReplace = null;
        editingSubtaskId = null;

        // Transition background to Working Plan tool page
        if (window.TempoApp) {
            window.TempoApp.navigateTo('plan-workspace');
        }

        // If guest user triggered sign-in modal, suppress it so breakdown popup remains primary
        const signInModal = document.getElementById('modal-sign-in');
        if (signInModal && !signInModal.classList.contains('hidden')) {
            signInModal.classList.add('hidden');
        }

        renderBreakTaskPopup(firstTaskId);
    }

    function renderBreakTaskPopup(taskId) {
        activeModalView = 'breakdown';
        currentBreakdownTaskId = taskId;

        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const task = tasks.find(t => String(t.id) === String(taskId)) || tasks[0];

        if (!task) {
            showStartWorkingPopup();
            return;
        }

        const subtasks = Array.isArray(task.subtasks) ? task.subtasks : [];
        const durStr = task.durationLabel || formatDuration(task.durationMinutes);

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${isViLocale() ? 'CHIA NHỎ TASK' : 'STEP BREAKDOWN'}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${isViLocale() ? 'Chia nhỏ task: ' : 'Break down: '}${escapeHTML(task.name)}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('plan-workspace')"
                        aria-label="Close dialog"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="Close and stay in Working Plan">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Task Metadata & AI Action Button -->
            <div class="flex items-center justify-between gap-2 flex-wrap">
                <div class="text-xs text-stone-500 flex items-center space-x-2">
                    <span>⏱ ${isViLocale() ? 'Tổng dự tính: ~' : 'Total estimate: ~'}${escapeHTML(durStr)}</span>
                    <span>•</span>
                    <span>${isViLocale() ? 'Thêm 2 đến 4 bước hành động cụ thể' : 'Add 2 to 4 concrete action steps'}</span>
                </div>
                ${aiHelpLoading ? `
                    <button type="button" disabled id="btn-ai-help-breakdown"
                            class="px-2.5 py-1 rounded-lg text-xs font-bold text-[#B83D08] bg-[#FFE9DC] border border-[#FF6B2C]/30 flex items-center space-x-1.5 opacity-80 cursor-wait">
                        <svg class="animate-spin h-3.5 w-3.5 text-[#B83D08]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                        </svg>
                        <span>${isViLocale() ? 'Đang xử lý...' : 'Thinking...'}</span>
                    </button>
                ` : `
                    <button type="button" id="btn-ai-help-breakdown" onclick="window.TempoUrmodeFlow.triggerAiHelp('${task.id}')"
                            class="px-2.5 py-1 rounded-lg text-xs font-bold text-[#B83D08] bg-[#FFE9DC] hover:bg-[#FFD2BA] transition flex items-center space-x-1.5 shadow-xs border border-[#FF6B2C]/30 cursor-pointer"
                            title="${isViLocale() ? 'Nhận gợi ý bước hành động AI cho task này' : 'Get AI action step suggestions for this task'}">
                        <span>✨</span>
                        <span>${isViLocale() ? 'AI Hỗ trợ' : 'AI Help'}</span>
                    </button>
                `}
            </div>

            <!-- AI Help Notice / Choice Banner -->
            ${aiHelpError ? `
                <div class="p-2.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center justify-between gap-2 animate-fade-in">
                    <div class="flex items-center space-x-1.5 min-w-0">
                        <span class="shrink-0">⚠️</span>
                        <span>${escapeHTML(aiHelpError)}</span>
                    </div>
                    <button type="button" onclick="window.TempoUrmodeFlow.dismissAiNotice()" class="text-rose-500 hover:text-rose-800 text-xs font-bold p-0.5 shrink-0 cursor-pointer">✕</button>
                </div>
            ` : ''}

            ${aiHelpSuccess ? `
                <div class="p-2.5 bg-[#FFF8F2] border border-[#FFD2BA] rounded-xl text-xs text-[#8B3814] flex items-center justify-between gap-2 animate-fade-in">
                    <div class="flex items-center space-x-1.5 min-w-0">
                        <span class="shrink-0">✨</span>
                        <span>${escapeHTML(aiHelpSuccess)}</span>
                    </div>
                    <button type="button" onclick="window.TempoUrmodeFlow.dismissAiNotice()" class="text-[#B83D08] hover:text-[#712708] text-xs font-bold p-0.5 shrink-0 cursor-pointer">✕</button>
                </div>
            ` : ''}

            ${aiConfirmReplace ? `
                <div class="p-3 bg-[#FFF8F2] border border-[#FFD2BA] rounded-xl text-xs text-[#8B3814] space-y-2 animate-fade-in">
                    <div class="flex items-center justify-between">
                        <span class="font-bold flex items-center space-x-1">
                            <span>✨</span>
                            <span>You already have ${subtasks.length} action steps</span>
                        </span>
                        <button type="button" onclick="window.TempoUrmodeFlow.dismissAiNotice()" class="text-stone-400 hover:text-stone-600 text-xs font-bold p-0.5 cursor-pointer">✕</button>
                    </div>
                    <p class="text-stone-600">Choose how you'd like to apply AI suggestions:</p>
                    <div class="flex flex-wrap items-center gap-2 pt-1">
                        <button type="button" onclick="window.TempoUrmodeFlow.applyAiAddMissing('${task.id}')"
                                class="px-2.5 py-1 rounded-lg bg-white border border-[#FF6B2C]/40 text-[#B83D08] font-bold text-xs hover:bg-[#FFE9DC] transition cursor-pointer">
                            + Add missing steps
                        </button>
                        <button type="button" onclick="window.TempoUrmodeFlow.applyAiReplaceAll('${task.id}')"
                                class="px-2.5 py-1 rounded-lg bg-[#FF6B2C] text-white font-bold text-xs hover:bg-[#B83D08] transition cursor-pointer">
                            Replace with AI steps
                        </button>
                    </div>
                </div>
            ` : ''}

            <!-- Subtask List -->
            <div class="space-y-2 max-h-52 overflow-y-auto pr-1" id="breakdown-subtask-list">
                ${subtasks.length === 0 ? `
                    <div class="p-3 bg-stone-50 rounded-xl text-xs text-stone-500 italic text-center">
                        ${window.t ? window.t('workspace.breakdownEmptyState', {}, (isViLocale() ? 'Chưa có bước thực hiện nào. Hãy thêm bước đầu tiên bên dưới hoặc chọn ✨ AI hỗ trợ.' : 'No action steps added yet. Add your first step below or click ✨ AI Help.')) : (isViLocale() ? 'Chưa có bước thực hiện nào. Hãy thêm bước đầu tiên bên dưới hoặc chọn ✨ AI hỗ trợ.' : 'No action steps added yet. Add your first step below or click ✨ AI Help.')}
                    </div>
                ` : subtasks.map((s, idx) => `
                    ${editingSubtaskId === s.id ? `
                        <div class="p-2 rounded-xl border border-[#FF6B2C] bg-[#FFFBF8] flex items-center gap-2 text-xs">
                            <span class="font-bold text-[#FF6B2C] shrink-0">${idx + 1}.</span>
                            <input type="text" id="edit-subtask-input-${s.id}" value="${escapeHTML(s.title)}"
                                   onkeydown="if(event.key==='Enter'){event.preventDefault();window.TempoUrmodeFlow.saveEditSubtask('${task.id}', '${s.id}');}else if(event.key==='Escape'){window.TempoUrmodeFlow.cancelEditSubtask();}"
                                   class="flex-1 px-2.5 py-1 rounded-lg border border-stone-300 text-xs text-stone-800 bg-white focus:outline-none focus:ring-1 focus:ring-[#FF6B2C]" />
                            <button type="button" onclick="window.TempoUrmodeFlow.saveEditSubtask('${task.id}', '${s.id}')"
                                    class="px-2.5 py-1 rounded-lg bg-[#FF6B2C] text-white font-bold text-[11px] hover:bg-[#B83D08] transition cursor-pointer shrink-0">
                                Save
                            </button>
                            <button type="button" onclick="window.TempoUrmodeFlow.cancelEditSubtask()"
                                    class="px-2 py-1 rounded-lg text-stone-500 hover:text-stone-800 text-[11px] font-semibold transition cursor-pointer shrink-0">
                                Cancel
                            </button>
                        </div>
                    ` : `
                        <div class="p-2.5 rounded-xl border border-stone-200 bg-white flex items-center justify-between text-xs group hover:border-stone-300 transition">
                            <label class="flex items-center space-x-2.5 flex-1 min-w-0 cursor-pointer select-none">
                                <input type="checkbox"
                                       id="breakdown-subtask-checkbox-${s.id}"
                                       ${s.completed ? 'checked' : ''}
                                       onclick="event.stopPropagation()"
                                       onchange="window.TempoUrmodeFlow.setSubtaskCompleted('${task.id}', '${s.id}', this.checked)"
                                       class="w-4 h-4 rounded border-stone-300 text-[#FF6B2C] focus:ring-[#FF6B2C] cursor-pointer shrink-0"
                                       title="${s.completed ? 'Mark step as incomplete' : 'Mark step as done'}">
                                <span class="font-medium text-xs truncate pr-2 transition ${s.completed ? 'line-through text-stone-400' : 'text-stone-800'}">
                                    ${idx + 1}. ${escapeHTML(s.title)}
                                </span>
                            </label>
                            <div class="flex items-center space-x-1 shrink-0">
                                <button type="button" onclick="window.TempoUrmodeFlow.startEditSubtask('${s.id}')"
                                        class="text-stone-400 hover:text-[#FF6B2C] transition cursor-pointer px-1 py-0.5 text-[11px] font-semibold"
                                        title="Edit step">
                                    Edit
                                </button>
                                <button type="button" onclick="window.TempoUrmodeFlow.removeSubtask('${task.id}', '${s.id}')"
                                        class="text-stone-400 hover:text-rose-600 transition cursor-pointer px-1 py-0.5"
                                        title="Remove step">
                                    ✕
                                </button>
                            </div>
                        </div>
                    `}
                `).join('')}
            </div>

            <!-- Add Subtask Input Form -->
            <div class="flex items-center space-x-2 pt-1">
                <input type="text" id="breakdown-subtask-input"
                       placeholder="${isViLocale() ? 'VD: Viết đoạn mở đầu (15 phút)' : 'e.g. Draft opening paragraph (15 min)'}"
                       onkeydown="if(event.key==='Enter'){event.preventDefault();window.TempoUrmodeFlow.addSubtask('${task.id}');}"
                       class="flex-1 px-3.5 py-2 rounded-xl border border-stone-300 text-xs text-stone-800 placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-[#D79277]" />
                <button type="button" onclick="window.TempoUrmodeFlow.addSubtask('${task.id}')"
                        class="px-4 py-2 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-700 font-bold text-xs transition cursor-pointer">
                    ${isViLocale() ? '+ Thêm bước' : '+ Add step'}
                </button>
            </div>

            <!-- Actions Row: Do this task, Break more tasks, View my plan, Later -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-wrap items-center justify-between gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('plan-workspace')"
                        class="px-4 py-2 rounded-xl font-semibold text-xs text-stone-500 hover:text-stone-800 transition cursor-pointer">
                    ${isViLocale() ? 'Để sau' : 'Later'}
                </button>
                <div class="flex flex-wrap items-center gap-2 sm:gap-2.5">
                    <button type="button" id="btn-view-my-plan" onclick="window.TempoUrmodeFlow.viewMyPlan('${task.id}')"
                            class="px-4 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] hover:text-[#202124] border border-[#EAE4DF] shadow-2xs transition cursor-pointer">
                        ${isViLocale() ? 'Xem kế hoạch' : 'View my plan'}
                    </button>
                    <button type="button" onclick="window.TempoUrmodeFlow.handleBreakMoreTasks('${task.id}')"
                            class="px-4 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs transition cursor-pointer">
                        ${isViLocale() ? 'Chia thêm task →' : 'Break more tasks →'}
                    </button>
                    <button type="button" onclick="window.TempoUrmodeFlow.launchFocusForTask('${task.id}')"
                            class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm transition cursor-pointer">
                        ${isViLocale() ? 'Làm ngay →' : 'Do this task →'}
                    </button>
                </div>
            </div>
        `;

        showModalContent(html);
    }

    /**
     * Generates 2-4 concrete, small, actionable steps tailored to the given task context.
     */
    function generateTaskActionSteps(task) {
        if (!task) return [];
        const name = (task.name || task.title || '').trim();
        const desc = (task.description || task.notes || '').trim();
        const combined = (name + ' ' + desc).toLowerCase();

        let rawSuggestions = [];

        // 1. Math / Statistics / Problem Sets / Quantitative Homework
        if (/\b(statistic|stats|problem set|pset|math|calculus|algebra|physics|equation|formula|homework|exercise|quantitative)\b/.test(combined)) {
            rawSuggestions = [
                { title: 'Identify required problem numbers and review assignment criteria (15 min)', durationMinutes: 15 },
                { title: 'Review lecture notes and write down relevant formulas (20 min)', durationMinutes: 20 },
                { title: 'Solve the first problem step-by-step on scratch paper (25 min)', durationMinutes: 25 },
                { title: 'Check calculations and format final solutions (20 min)', durationMinutes: 20 }
            ];
        }
        // 2. Programming / Coding / Software / Debugging / Labs
        else if (/\b(code|coding|program|programming|bug|debug|lab|software|dev|github|script|algorithm|frontend|backend|api)\b/.test(combined)) {
            rawSuggestions = [
                { title: 'Review problem statement and expected inputs/outputs (15 min)', durationMinutes: 15 },
                { title: 'Outline core logic and pseudo-code on paper or in comments (20 min)', durationMinutes: 20 },
                { title: 'Implement working logic for first module and test locally (30 min)', durationMinutes: 30 },
                { title: 'Verify edge cases and prepare submission files (15 min)', durationMinutes: 15 }
            ];
        }
        // 3. Writing / Essays / Reports / Papers / Proposals / Literature Reviews
        else if (/\b(essay|paper|report|thesis|proposal|draft|write|writing|article|manuscript|dissertation)\b/.test(combined)) {
            rawSuggestions = [
                { title: 'Open prompt/rubric and paste outline into blank document (15 min)', durationMinutes: 15 },
                { title: 'Write 3 bullet points for each main section or argument (25 min)', durationMinutes: 25 },
                { title: 'Draft introduction and write the first body section (30 min)', durationMinutes: 30 },
                { title: 'Proofread flow, check word count, and verify citations (20 min)', durationMinutes: 20 }
            ];
        }
        // 4. Reading / Study / Textbooks / Literature
        else if (/\b(read|reading|chapter|book|textbook|literature|monograph)\b/.test(combined)) {
            rawSuggestions = [
                { title: 'Skim table of contents, headings, and chapter summary (10 min)', durationMinutes: 10 },
                { title: 'Read first half and highlight 3 core concepts (25 min)', durationMinutes: 25 },
                { title: 'Finish reading and draft short paragraph summary (20 min)', durationMinutes: 20 },
                { title: 'Review highlighted notes and prepare questions (10 min)', durationMinutes: 10 }
            ];
        }
        // 5. Exams / Quizzes / Tests / Midterm / Final Prep
        else if (/\b(exam|test|quiz|midterm|final|prep|revision)\b/.test(combined)) {
            rawSuggestions = [
                { title: 'Gather lecture notes, syllabus topics, and past exams (15 min)', durationMinutes: 15 },
                { title: 'Complete 3 practice questions without looking at solutions (30 min)', durationMinutes: 30 },
                { title: 'Review incorrect answers and clarify weak concepts (25 min)', durationMinutes: 25 },
                { title: 'Create a one-page summary sheet of key definitions (20 min)', durationMinutes: 20 }
            ];
        }
        // 6. Presentations / Slides / Talks / Speeches
        else if (/\b(presentation|slide|slides|deck|powerpoint|keynote|talk|speech|pitch)\b/.test(combined)) {
            rawSuggestions = [
                { title: 'Determine central message and outline 5 key slide topics (20 min)', durationMinutes: 20 },
                { title: 'Add bullet points, diagrams, and visual figures to slides (30 min)', durationMinutes: 30 },
                { title: 'Write speaker notes and talking transitions (15 min)', durationMinutes: 15 },
                { title: 'Conduct one uninterrupted rehearsal out loud (15 min)', durationMinutes: 15 }
            ];
        }
        // 7. Email / Correspondence / Applications
        else if (/\b(email|mail|message|contact|advisor|prof|professor|apply|application|form|submit)\b/.test(combined)) {
            rawSuggestions = [
                { title: 'Draft 3-sentence message stating main question clearly (10 min)', durationMinutes: 10 },
                { title: 'Attach necessary documents and verify recipient address (5 min)', durationMinutes: 5 },
                { title: 'Review tone and proofread before sending (5 min)', durationMinutes: 5 }
            ];
        }
        // 8. General task fallback (customized using task name)
        else {
            const cleanName = name || 'task';
            rawSuggestions = [
                { title: `Gather materials and review guidelines for "${cleanName}" (15 min)`, durationMinutes: 15 },
                { title: `Complete the first 25 minutes of focused work on "${cleanName}" (25 min)`, durationMinutes: 25 },
                { title: `Review progress and address remaining items (20 min)`, durationMinutes: 20 },
                { title: `Do final review and prepare for completion (15 min)`, durationMinutes: 15 }
            ];
        }

        // Adjust durations if task has a total duration
        if (typeof task.durationMinutes === 'number' && task.durationMinutes > 0 && rawSuggestions.length > 0) {
            const totalEst = task.durationMinutes;
            const portion = Math.max(5, Math.round(totalEst / rawSuggestions.length / 5) * 5);
            rawSuggestions.forEach(s => {
                s.durationMinutes = portion;
            });
        }

        return rawSuggestions;
    }

    /**
     * Centralized subtask persistence helper ensuring in-memory plan and stores stay synchronized.
     */
    function saveTaskSubtasks(plan, taskId, subtasks) {
        if (!plan) plan = getActiveWorkingPlan();
        if (!plan) return;

        let targetTask = null;
        if (Array.isArray(plan.plannedTasks)) {
            const pt = plan.plannedTasks.find(p => p.task && String(p.task.id) === String(taskId));
            if (pt) targetTask = pt.task;
        }
        if (!targetTask && Array.isArray(plan.tasks)) {
            targetTask = plan.tasks.find(t => String(t.id) === String(taskId));
        }
        if (!targetTask && Array.isArray(plan.unarrangedTasks)) {
            targetTask = plan.unarrangedTasks.find(t => {
                const tObj = (t && t.task) ? t.task : t;
                return tObj && String(tObj.id) === String(taskId);
            });
            if (targetTask && targetTask.task) targetTask = targetTask.task;
        }

        if (targetTask) {
            targetTask.subtasks = subtasks;

            if (Array.isArray(plan.tasks)) {
                const tMatch = plan.tasks.find(t => String(t.id) === String(taskId));
                if (tMatch && tMatch !== targetTask) {
                    tMatch.subtasks = subtasks;
                }
            }

            if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
                window.TempoPlanStore.saveActivePlan('emergency', plan);
                window.TempoPlanStore.updateTaskState(taskId, { subtasks: subtasks });
            }
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                window.TempoEmergencyFlow.setConfirmedPlan(plan);
            }
        }
    }

    /**
     * AI Help Trigger: Generates tailored action steps with loading and duplicate-checking behavior.
     */
    async function triggerAiHelp(taskId) {
        if (aiHelpLoading) return;

        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const task = tasks.find(t => String(t.id) === String(taskId)) || tasks[0];
        if (!task) return;

        aiHelpLoading = true;
        aiHelpError = null;
        aiHelpSuccess = null;
        aiConfirmReplace = null;
        renderBreakTaskPopup(taskId);

        // Breathing delay for clear visual feedback of loading state
        await new Promise(r => setTimeout(r, 300));

        try {
            const suggestions = generateTaskActionSteps(task);
            if (!Array.isArray(suggestions) || suggestions.length === 0) {
                throw new Error("No suggestions could be generated.");
            }

            const existingSteps = Array.isArray(task.subtasks) ? task.subtasks : [];

            if (existingSteps.length === 0) {
                // No existing steps: add suggestions directly
                const newSteps = suggestions.map((s, idx) => ({
                    id: 'sub-ai-' + Date.now() + '-' + idx,
                    title: s.title,
                    durationMinutes: s.durationMinutes || null,
                    completed: false
                }));

                saveTaskSubtasks(plan, taskId, newSteps);
                aiHelpLoading = false;
                aiHelpSuccess = `Added ${newSteps.length} action steps tailored to this task.`;
                renderBreakTaskPopup(taskId);
            } else {
                // Existing steps present: avoid duplicates
                const normalize = str => (str || '').toLowerCase().replace(/[^a-z0-9]/g, '');
                const existingNormalized = existingSteps.map(s => normalize(s.title));

                const missingSuggestions = suggestions.filter(s => {
                    const norm = normalize(s.title);
                    return !existingNormalized.some(eNorm => eNorm.includes(norm) || norm.includes(eNorm));
                });

                if (missingSuggestions.length > 0) {
                    if (existingSteps.length + missingSuggestions.length <= 4) {
                        // Few existing steps: add missing steps directly without duplicating
                        const newSteps = [
                            ...existingSteps,
                            ...missingSuggestions.map((s, idx) => ({
                                id: 'sub-ai-' + Date.now() + '-' + idx,
                                title: s.title,
                                durationMinutes: s.durationMinutes || null,
                                completed: false
                            }))
                        ];
                        saveTaskSubtasks(plan, taskId, newSteps);
                        aiHelpLoading = false;
                        aiHelpSuccess = `Added ${missingSuggestions.length} new step${missingSuggestions.length > 1 ? 's' : ''}. Existing steps were kept.`;
                        renderBreakTaskPopup(taskId);
                    } else {
                        // Several steps already exist: present clear choice
                        aiHelpLoading = false;
                        aiConfirmReplace = { taskId, suggestions, missingSuggestions };
                        renderBreakTaskPopup(taskId);
                    }
                } else {
                    // All generated steps are already represented
                    aiHelpLoading = false;
                    aiHelpSuccess = `All suggested steps are already present in your list.`;
                    renderBreakTaskPopup(taskId);
                }
            }
        } catch (err) {
            console.error('[TempoUrmodeFlow] AI Help generation error:', err);
            aiHelpLoading = false;
            aiHelpError = "AI suggestions couldn't be generated right now. You can add steps manually below.";
            renderBreakTaskPopup(taskId);
        }
    }

    function applyAiAddMissing(taskId) {
        if (!aiConfirmReplace || !aiConfirmReplace.missingSuggestions) {
            dismissAiNotice();
            return;
        }
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const task = tasks.find(t => String(t.id) === String(taskId));
        if (!task) return;

        const existingSteps = Array.isArray(task.subtasks) ? task.subtasks : [];
        const toAdd = aiConfirmReplace.missingSuggestions.slice(0, Math.max(1, 4 - existingSteps.length));
        const newSteps = [
            ...existingSteps,
            ...toAdd.map((s, idx) => ({
                id: 'sub-ai-' + Date.now() + '-' + idx,
                title: s.title,
                durationMinutes: s.durationMinutes || null,
                completed: false
            }))
        ];

        saveTaskSubtasks(plan, taskId, newSteps);
        aiConfirmReplace = null;
        aiHelpSuccess = `Added ${toAdd.length} missing step${toAdd.length > 1 ? 's' : ''}.`;
        renderBreakTaskPopup(taskId);
    }

    function applyAiReplaceAll(taskId) {
        if (!aiConfirmReplace || !aiConfirmReplace.suggestions) {
            dismissAiNotice();
            return;
        }
        const plan = getActiveWorkingPlan();
        const newSteps = aiConfirmReplace.suggestions.map((s, idx) => ({
            id: 'sub-ai-' + Date.now() + '-' + idx,
            title: s.title,
            durationMinutes: s.durationMinutes || null,
            completed: false
        }));

        saveTaskSubtasks(plan, taskId, newSteps);
        aiConfirmReplace = null;
        aiHelpSuccess = `Replaced steps with ${newSteps.length} fresh AI suggestions.`;
        renderBreakTaskPopup(taskId);
    }

    function dismissAiNotice() {
        aiHelpError = null;
        aiHelpSuccess = null;
        aiConfirmReplace = null;
        renderBreakTaskPopup(currentBreakdownTaskId);
    }

    function startEditSubtask(subtaskId) {
        editingSubtaskId = subtaskId;
        renderBreakTaskPopup(currentBreakdownTaskId);
        setTimeout(() => {
            const input = document.getElementById('edit-subtask-input-' + subtaskId);
            if (input) {
                input.focus();
                input.select();
            }
        }, 50);
    }

    function saveEditSubtask(taskId, subtaskId) {
        const input = document.getElementById('edit-subtask-input-' + subtaskId);
        const newTitle = input ? input.value.trim() : '';
        if (!newTitle) return;

        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const task = tasks.find(t => String(t.id) === String(taskId));
        if (!task || !Array.isArray(task.subtasks)) return;

        const updated = task.subtasks.map(s => {
            if (String(s.id) === String(subtaskId)) {
                return { ...s, title: newTitle };
            }
            return s;
        });

        saveTaskSubtasks(plan, taskId, updated);
        editingSubtaskId = null;
        renderBreakTaskPopup(taskId);
    }

    function cancelEditSubtask() {
        editingSubtaskId = null;
        renderBreakTaskPopup(currentBreakdownTaskId);
    }

    function addSubtask(taskId) {
        const input = document.getElementById('breakdown-subtask-input');
        const text = input ? input.value.trim() : '';
        if (!text) return;

        const plan = getActiveWorkingPlan();
        if (!plan) return;

        const tasks = getAllPlanTasks(plan);
        const task = tasks.find(t => String(t.id) === String(taskId));
        if (!task) return;

        const existing = Array.isArray(task.subtasks) ? task.subtasks : [];
        const newSteps = [
            ...existing,
            {
                id: 'sub-' + Date.now() + '-' + Math.random().toString(36).substr(2, 4),
                title: text,
                completed: false
            }
        ];

        saveTaskSubtasks(plan, taskId, newSteps);
        aiHelpError = null;
        aiHelpSuccess = null;
        aiConfirmReplace = null;
        editingSubtaskId = null;
        renderBreakTaskPopup(taskId);
    }

    function removeSubtask(taskId, subtaskId) {
        const plan = getActiveWorkingPlan();
        if (!plan) return;

        const tasks = getAllPlanTasks(plan);
        const task = tasks.find(t => String(t.id) === String(taskId));
        if (!task || !Array.isArray(task.subtasks)) return;

        const newSteps = task.subtasks.filter(s => String(s.id) !== String(subtaskId));
        saveTaskSubtasks(plan, taskId, newSteps);
        aiHelpError = null;
        aiHelpSuccess = null;
        aiConfirmReplace = null;
        editingSubtaskId = null;
        renderBreakTaskPopup(taskId);
    }

    async function setSubtaskCompleted(taskId, subtaskId, isCompleted) {
        if (!taskId || !subtaskId) return;
        const targetCompleted = Boolean(isCompleted);

        const plan = getActiveWorkingPlan();
        if (!plan) return;

        const tasks = getAllPlanTasks(plan);
        const task = tasks.find(t => String(t.id) === String(taskId));
        if (!task || !Array.isArray(task.subtasks)) return;

        const sub = task.subtasks.find(s => String(s.id) === String(subtaskId));
        if (sub) {
            sub.completed = targetCompleted;
            saveTaskSubtasks(plan, taskId, task.subtasks);

            if (window.TempoPlanStore && typeof window.TempoPlanStore.updateSubtaskState === 'function') {
                await window.TempoPlanStore.updateSubtaskState(taskId, subtaskId, { completed: targetCompleted });
            }

            // Sync with mode.js active home if present
            if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
                window.TempoMode.renderActiveModeHome();
            }

            // Re-render break task popup
            renderBreakTaskPopup(taskId);
        }
    }

    function refreshBreakTaskSubtasks(taskId) {
        if (activeModalView === 'breakdown' && (!taskId || String(currentBreakdownTaskId) === String(taskId))) {
            renderBreakTaskPopup(currentBreakdownTaskId);
        }
    }

    function handleBreakMoreTasks(currentId) {
        processedBreakdownTaskIds.add(String(currentId));

        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const nextEligible = tasks.find(t => !t.completed && !processedBreakdownTaskIds.has(String(t.id)) && !processedBreakdownTaskIds.has(t.id));

        if (nextEligible) {
            renderBreakTaskPopup(nextEligible.id);
        } else {
            showStartWorkingPopup();
        }
    }

    function viewMyPlan(taskId) {
        closeModal('plan-workspace');
    }

    // -------------------------------------------------------------------------
    // 8. "START WORKING ON YOUR PLAN" POPUP & TASK SELECTION
    // -------------------------------------------------------------------------

    function showStartWorkingPopup() {
        activeModalView = 'start_working_plan';
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const topTask = tasks.find(t => !t.completed) || tasks[0];

        let durStr = isViLocale() ? '30 phút' : '30 min';
        if (topTask) {
            if (topTask.durationMinutes === 90 || topTask.duration === 90 || topTask.estimateMinutes === 90 || topTask.durationLabel === '1.5 hr' || topTask.durationLabel === '1,5 giờ') {
                durStr = isViLocale() ? '1,5 giờ' : '1.5 hr';
            } else if (topTask.durationMinutes) {
                durStr = formatDuration(topTask.durationMinutes);
            } else if (typeof formatTaskDuration === 'function') {
                durStr = formatTaskDuration(topTask);
            } else if (topTask.durationLabel) {
                durStr = topTask.durationLabel;
            }
        }

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${window.t ? window.t('workspace.readyToWorkUpper', {}, 'READY TO WORK') : (isViLocale() ? 'SẴN SÀNG BẮT ĐẦU' : 'READY TO WORK')}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${window.t ? window.t('workspace.startWorkingOnPlanTitle', {}, 'Start working on your plan?') : (isViLocale() ? 'Bắt đầu làm việc nhé?' : 'Start working on your plan?')}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('plan-workspace')"
                        aria-label="${window.t ? window.t('common.close', {}, 'Close dialog') : (isViLocale() ? 'Đóng' : 'Close dialog')}"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="${window.t ? window.t('common.close', {}, 'Close dialog') : (isViLocale() ? 'Đóng' : 'Close dialog')}">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <div class="py-3 text-center sm:text-left space-y-2">
                <p class="text-sm sm:text-base text-[#484541] leading-relaxed">
                    ${window.t ? window.t('workspace.startWorkingOnPlanDesc', {}, 'Your working plan is ready. Would you like to start right away on your first task?') : (isViLocale() ? 'Kế hoạch làm việc của bạn đã sẵn sàng. Bạn muốn bắt đầu với task đầu tiên ngay bây giờ không?' : 'Your working plan is ready. Would you like to start right away on your first task?')}
                </p>
                ${topTask ? `
                    <div class="p-3 bg-[#FFF9F5] border border-[#FFD2BA] rounded-2xl flex items-center justify-between text-xs">
                        <span class="font-bold text-[#202124]">${window.t ? window.t('workspace.firstTaskPrefix', {}, 'First task:') : (isViLocale() ? 'Task đầu tiên:' : 'First task:')} ${escapeHTML(topTask.name || topTask.title)}</span>
                        <span class="text-[#8C8782]">~${escapeHTML(durStr)}</span>
                    </div>
                ` : ''}
            </div>

            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-wrap items-center justify-between gap-3">
                <div class="flex items-center space-x-2">
                    <button type="button" onclick="window.TempoUrmodeFlow.closeModal('plan-workspace')"
                            class="px-4 py-2 rounded-xl font-semibold text-xs text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ${window.t ? window.t('workspace.laterBtn', {}, 'Later') : (isViLocale() ? 'Để sau' : 'Later')}
                    </button>
                    <button type="button" onclick="window.TempoUrmodeFlow.restartBreakdownFlow()"
                            class="px-4 py-2 rounded-xl font-semibold text-xs text-[#D79277] hover:underline transition cursor-pointer">
                        ${window.t ? window.t('workspace.breakMoreTasksBtn', {}, 'Break more tasks') : (isViLocale() ? 'Chia nhỏ thêm task' : 'Break more tasks')}
                    </button>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.showFirstTaskExecutionPopup()"
                        class="btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center space-x-2 transition cursor-pointer">
                    <span>${window.t ? window.t('workspace.yesStartWorkingBtn', {}, 'Yes, start working →') : (isViLocale() ? 'Có, bắt đầu thôi →' : 'Yes, start working →')}</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }

    function restartBreakdownFlow() {
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const nextUnbroken = tasks.find(t => !t.completed && (!Array.isArray(t.subtasks) || t.subtasks.length === 0));
        const target = nextUnbroken || tasks.find(t => !t.completed) || tasks[0];
        if (target) {
            renderBreakTaskPopup(target.id);
        } else {
            closeModal('plan-workspace');
        }
    }

    function showFirstTaskExecutionPopup() {
        activeModalView = 'first_task_choice';
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan);
        const topTask = (selectedWorkTaskId && tasks.find(t => String(t.id) === String(selectedWorkTaskId))) || tasks.find(t => !t.completed) || tasks[0];

        if (!topTask) {
            closeModal('plan-workspace');
            return;
        }

        let durStr = isViLocale() ? '30 phút' : '30 min';
        if (topTask) {
            if (topTask.durationMinutes === 90 || topTask.duration === 90 || topTask.estimateMinutes === 90 || topTask.durationLabel === '1.5 hr' || topTask.durationLabel === '1,5 giờ' || topTask.durationLabel === '1.5h') {
                durStr = isViLocale() ? '1,5 giờ' : '1.5 hr';
            } else if (topTask.durationMinutes) {
                durStr = formatDuration(topTask.durationMinutes);
            } else if (typeof formatTaskDuration === 'function') {
                durStr = formatTaskDuration(topTask);
            } else if (topTask.durationLabel) {
                durStr = topTask.durationLabel;
            }
        }

        let deadlineDisplay = '';
        if (topTask.hasDeadline && topTask.deadlineDate) {
            const formattedDeadline = formatDeadline(topTask.deadlineDate, topTask.deadlineTime);
            deadlineDisplay = `Deadline: ${formattedDeadline}`;
        } else {
            deadlineDisplay = window.t ? window.t('workspace.dueNoFixedDeadline', {}, (isViLocale() ? 'Deadline: Chưa có deadline' : 'Deadline: No fixed deadline')) : (isViLocale() ? 'Deadline: Chưa có deadline' : 'Deadline: No fixed deadline');
        }

        const subtasks = Array.isArray(topTask.subtasks) ? topTask.subtasks : [];

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${window.t ? window.t('workspace.firstTaskExecutionUpper', {}, 'FIRST TASK EXECUTION') : (isViLocale() ? 'BẮT ĐẦU TASK ĐẦU TIÊN' : 'FIRST TASK EXECUTION')}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${window.t ? window.t('workspace.yourFirstTaskIs', {}, 'Your first task is…') : (isViLocale() ? 'Task đầu tiên của bạn là…' : 'Your first task is…')}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('plan-workspace')"
                        aria-label="${window.t ? window.t('common.close', {}, 'Close dialog') : (isViLocale() ? 'Đóng' : 'Close dialog')}"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="${window.t ? window.t('common.close', {}, 'Close dialog') : (isViLocale() ? 'Đóng' : 'Close dialog')}">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Task Card -->
            <div class="p-4 rounded-2xl border-2 border-[#D79277] bg-[#FFF9F5] space-y-2">
                <div class="flex items-center justify-between">
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#D79277] text-white">
                        ${window.t ? window.t('workspace.readyNowBadge', {}, 'READY NOW') : (isViLocale() ? 'SẴN SÀNG THỰC HIỆN' : 'READY NOW')}
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
                        <div class="text-[11px] font-bold uppercase tracking-wider text-stone-500">${subtasks.length} ${isViLocale() ? 'bước' : (subtasks.length === 1 ? 'step' : 'steps')}:</div>
                        ${subtasks.slice(0, 3).map((s, i) => `
                            <div class="text-xs text-stone-700 truncate">• ${escapeHTML(s.title || s.name)}</div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>

            <!-- Action Buttons: Do this task, Choose another task, Later -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-wrap items-center justify-between gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('plan-workspace')"
                        class="px-4 py-2 rounded-xl font-semibold text-xs text-stone-500 hover:text-stone-800 transition cursor-pointer">
                    ${window.t ? window.t('workspace.laterBtn', {}, 'Later') : (isViLocale() ? 'Để sau' : 'Later')}
                </button>
                <div class="flex items-center space-x-2.5">
                    <button type="button" onclick="window.TempoUrmodeFlow.showTaskSelectionPopup()"
                            class="px-4 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs transition cursor-pointer">
                        ${window.t ? window.t('workspace.chooseAnotherTaskBtn', {}, 'Choose another task') : (isViLocale() ? 'Chọn task khác' : 'Choose another task')}
                    </button>
                    <button type="button" onclick="window.TempoUrmodeFlow.launchFocusForTask('${topTask.id}')"
                            class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm transition cursor-pointer">
                        ${window.t ? window.t('workspace.doThisTaskBtn', {}, 'Do this task →') : (isViLocale() ? 'Bắt đầu task này →' : 'Do this task →')}
                    </button>
                </div>
            </div>
        `;

        showModalContent(html);
    }

    function showTaskSelectionPopup() {
        activeModalView = 'select_another_task';
        const plan = getActiveWorkingPlan();
        const tasks = getAllPlanTasks(plan).filter(t => !t.completed);

        function formatTaskCardDuration(t) {
            if (t.durationMinutes === 90 || t.duration === 90 || t.estimateMinutes === 90 || t.durationLabel === '1.5 hr' || t.durationLabel === '1,5 giờ' || t.durationLabel === '1.5h') {
                return isViLocale() ? '1,5 giờ' : '1.5 hr';
            }
            if (t.durationMinutes) {
                return formatDuration(t.durationMinutes);
            }
            if (typeof formatTaskDuration === 'function') {
                return formatTaskDuration(t);
            }
            return t.durationLabel || (isViLocale() ? '30 phút' : '30 min');
        }

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${window.t ? window.t('workspace.taskSelectionUpper', {}, 'TASK SELECTION') : (isViLocale() ? 'CHỌN TASK' : 'TASK SELECTION')}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${window.t ? window.t('workspace.selectTaskToWorkOn', {}, 'Select a task to work on') : (isViLocale() ? 'Chọn task bạn muốn thực hiện' : 'Select a task to work on')}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.showFirstTaskExecutionPopup()"
                        aria-label="${window.t ? window.t('common.back', {}, 'Back') : (isViLocale() ? 'Quay lại' : 'Back')}"
                        title="${window.t ? window.t('common.back', {}, 'Back') : (isViLocale() ? 'Quay lại' : 'Back')}"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer">
                    ←
                </button>
            </div>

            <div class="max-h-64 overflow-y-auto space-y-2 pr-1 py-1">
                ${tasks.map((t, idx) => `
                    <div onclick="window.TempoUrmodeFlow.selectWorkTaskAndConfirm('${t.id}')"
                         class="p-3 rounded-2xl border border-stone-200 bg-white hover:border-[#D79277] hover:bg-[#FFF9F5] transition cursor-pointer flex items-center justify-between text-xs">
                        <div class="flex items-center space-x-2.5 min-w-0 flex-1 mr-2">
                            <span class="font-bold text-stone-400 w-5 shrink-0 text-center">${idx + 1}.</span>
                            <div class="min-w-0">
                                <div class="font-bold text-stone-800 truncate">${escapeHTML(t.name || t.title)}</div>
                                <div class="text-[11px] text-stone-500">~${escapeHTML(formatTaskCardDuration(t))}</div>
                            </div>
                        </div>
                        <span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-stone-100 text-stone-700 shrink-0">
                            ${window.t ? window.t('workspace.selectTaskWithArrow', {}, 'Select →') : (isViLocale() ? 'Chọn →' : 'Select →')}
                        </span>
                    </div>
                `).join('')}
            </div>

            <div class="pt-4 border-t border-[#EAE4DF]/80 flex justify-end">
                <button type="button" onclick="window.TempoUrmodeFlow.showFirstTaskExecutionPopup()"
                        class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs transition cursor-pointer">
                    ${window.t ? window.t('common.back', {}, 'Back') : (isViLocale() ? 'Quay lại' : 'Back')}
                </button>
            </div>
        `;

        showModalContent(html);
    }

    function selectWorkTaskAndConfirm(taskId) {
        selectedWorkTaskId = taskId;
        showFirstTaskExecutionPopup();
    }

    // -------------------------------------------------------------------------
    // 9. WORKING PLAN ADJUSTMENT FLOW (Non-Destructive until saved)
    // -------------------------------------------------------------------------

    function getTaskDueDateISO(task) {
        if (!task) return '';
        if (task.deadlineDate && typeof task.deadlineDate === 'string') {
            const trimmed = task.deadlineDate.trim();
            if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) return trimmed;
        }
        if (task.deadline && typeof task.deadline === 'string') {
            const datePart = task.deadline.split(' ')[0].trim();
            if (/^\d{4}-\d{2}-\d{2}$/.test(datePart)) return datePart;
        }
        return '';
    }

    function startAdjustmentFlow(customPlan) {
        const plan = customPlan || getActiveWorkingPlan() || (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.getActivePlan === 'function' ? window.TempoPlanWorkspace.getActivePlan() : null);
        const tasks = getAllPlanTasks(plan);

        // Pre-populate adjustment draft with existing plan tasks (preserving all IDs and state)
        adjustmentDraft = {
            originalPlan: plan,
            retainedTasks: tasks.map(t => {
                const dateIso = getTaskDueDateISO(t);
                return {
                    ...t,
                    _keep: true,
                    hasDeadline: Boolean(dateIso && t.hasDeadline !== false),
                    deadlineDate: dateIso || null,
                    deadlineTime: t.deadlineTime || (dateIso ? '23:59' : null),
                    deadline: dateIso ? `${dateIso} ${t.deadlineTime || '23:59'}` : null
                };
            }),
            newTasks: [],
            availabilityDays: (plan && Array.isArray(plan.availabilityDays)) ? JSON.parse(JSON.stringify(plan.availabilityDays)) : [],
            proposedPlan: null
        };

        renderAdjustmentStep1Keep();
    }

    // Step 1: Choose which existing tasks to keep
    function renderAdjustmentStep1Keep() {
        activeModalView = 'adjust_keep';
        const tasks = adjustmentDraft.retainedTasks;

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${window.t ? window.t('workspace.adjustPlanStep1', {}, 'STEP 1 OF 3 · ADJUST PLAN') : (isViLocale() ? 'BƯỚC 1/3 · ĐIỀU CHỈNH PLAN' : 'STEP 1 OF 3 · ADJUST PLAN')}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${window.t ? window.t('workspace.chooseTasksToKeep', {}, 'Choose tasks to keep') : (isViLocale() ? 'Chọn các task muốn giữ lại' : 'Choose tasks to keep')}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal(window.location.hash.includes('plan-workspace') ? 'plan-workspace' : 'dashboard')"
                        aria-label="${window.t ? window.t('workspace.cancelAdjustment', {}, 'Cancel adjustment') : (isViLocale() ? 'Hủy điều chỉnh' : 'Cancel adjustment')}"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="${window.t ? window.t('workspace.cancelAdjustment', {}, 'Cancel adjustment') : (isViLocale() ? 'Hủy điều chỉnh' : 'Cancel adjustment')}">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <p class="text-xs sm:text-sm text-stone-600">
                ${window.t ? window.t('workspace.chooseTasksToKeepDesc', {}, 'Select the tasks you still need to complete. Overdue or completed tasks can be removed or kept.') : (isViLocale() ? 'Chọn những task bạn vẫn cần hoàn thành. Bạn có thể giữ lại hoặc loại bỏ các task đã quá hạn hoặc hoàn thành.' : 'Select the tasks you still need to complete. Overdue or completed tasks can be removed or kept.')}
            </p>

            <div class="max-h-60 overflow-y-auto space-y-2 pr-1 py-1">
                ${tasks.map(t => {
                    const overdue = isTaskOverdue(t, adjustmentDraft.originalPlan);
                    return `
                        <label class="p-3 rounded-2xl border ${overdue ? 'border-amber-300 bg-amber-50/40' : 'border-stone-200 bg-white'} flex items-center justify-between text-xs cursor-pointer select-none">
                            <div class="flex items-center space-x-2.5 min-w-0 flex-1 mr-2">
                                <input type="checkbox" ${t._keep ? 'checked' : ''}
                                       onchange="window.TempoUrmodeFlow.toggleRetainedTask('${t.id}', this.checked)"
                                       class="w-4 h-4 rounded text-[#D79277] focus:ring-[#D79277] border-gray-300 cursor-pointer" />
                                <div class="min-w-0">
                                    <span class="font-bold text-stone-800 truncate block">${escapeHTML(t.name || t.title)}</span>
                                    <span class="text-[11px] text-stone-500">~${escapeHTML(formatTaskDuration(t))}</span>
                                </div>
                            </div>
                            ${overdue ? `
                                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200 shrink-0">
                                    ${window.t ? window.t('workspace.priorityOverdueUpper', {}, 'OVERDUE') : (isViLocale() ? 'TRỄ DEADLINE' : 'OVERDUE')}
                                </span>
                            ` : ''}
                        </label>
                    `;
                }).join('')}
            </div>

            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-between gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal(window.location.hash.includes('plan-workspace') ? 'plan-workspace' : 'dashboard')"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs transition cursor-pointer">
                    ${window.t ? window.t('workspace.cancelAdjustment', {}, 'Cancel adjustment') : (isViLocale() ? 'Hủy điều chỉnh' : 'Cancel adjustment')}
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.renderAdjustmentStep2Tasks()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm transition cursor-pointer">
                    ${window.t ? window.t('workspace.nextAdjustAddTasks', {}, 'Next: Adjust & add tasks →') : (isViLocale() ? 'Tiếp theo: Điều chỉnh & thêm task →' : 'Next: Adjust & add tasks →')}
                </button>
            </div>
        `;

        showModalContent(html);
    }

    function toggleRetainedTask(taskId, isKept) {
        const item = adjustmentDraft.retainedTasks.find(t => String(t.id) === String(taskId));
        if (item) {
            item._keep = isKept;
        }
    }

    // Step 2: Date Formatting & Parsing Helpers
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
        const isoMatch = val.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
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
        const enTextMatch = val.match(/^([a-zA-Z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})$/i);
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
        const numMatch = val.match(/^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})$/);
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
                                    ${window.t ? window.t('workspace.duePrefixLabel', {}, 'Deadline:') : 'Deadline:'}
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
                            ${window.t ? window.t('workspace.duePrefixLabel', {}, 'Deadline:') : 'Deadline:'}
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
                            const dueStr = dueFormatted ? ` • Deadline: ${dueFormatted}` : '';
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

    function handleAdjustmentStep2Back() {
        syncStep2InputsFromDom();
        renderAdjustmentStep1Keep();
    }

    function handleAdjustmentStep2Next() {
        syncStep2InputsFromDom();
        renderAdjustmentStep3Proposal();
    }

    function updateRetainedDueDate(taskId, dateVal) {
        if (!adjustmentDraft || !Array.isArray(adjustmentDraft.retainedTasks)) return;
        const item = adjustmentDraft.retainedTasks.find(t => String(t.id) === String(taskId));
        if (item) {
            const raw = (dateVal || '').trim();
            const iso = parseStep2DateInput(raw) || (raw.match(/^\d{4}-\d{2}-\d{2}$/) ? raw : '');
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
    }

    function updateRetainedDuration(taskId, mins) {
        if (!adjustmentDraft || !Array.isArray(adjustmentDraft.retainedTasks)) return;
        const item = adjustmentDraft.retainedTasks.find(t => String(t.id) === String(taskId));
        if (item) {
            item.durationMinutes = parseInt(mins, 10);
            item.durationLabel = formatDuration(item.durationMinutes);
        }
    }

    function addNewAdjustmentTask() {
        const nameInput = document.getElementById('adjust-new-task-name');
        const durInput = document.getElementById('adjust-new-task-dur');
        const dueInput = document.getElementById('adjust-new-task-due');
        const name = nameInput ? nameInput.value.trim() : '';
        if (!name) return;

        // Sync existing retained inputs from DOM before re-rendering
        syncStep2InputsFromDom();

        const dur = parseInt(durInput?.value || '30', 10);
        const rawDue = dueInput ? (dueInput.dataset.iso || parseStep2DateInput(dueInput.value) || dueInput.value || '').trim() : '';
        const dueDate = parseStep2DateInput(rawDue) || (rawDue.match(/^\d{4}-\d{2}-\d{2}$/) ? rawDue : '');
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
    }

    function removeAdjustmentNewTask(idx) {
        syncStep2InputsFromDom();
        adjustmentDraft.newTasks.splice(idx, 1);
        renderAdjustmentStep2Tasks();
    }

    // Step 3: Confirm updated plan proposal
    function renderAdjustmentStep3Proposal() {
        activeModalView = 'adjust_propose';
        const kept = adjustmentDraft.retainedTasks.filter(t => t._keep);
        const allAdjustedTasks = [...kept, ...adjustmentDraft.newTasks];

        const now = new Date();
        const pad = n => String(n).padStart(2, '0');
        const todayStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

        // Create clean proposed updated plan structure
        const updatedPlan = {
            id: adjustmentDraft.originalPlan?.id || ('plan_' + Date.now()),
            planId: adjustmentDraft.originalPlan?.planId || ('plan_' + Date.now()),
            planType: 'emergency',
            title: 'Working Plan',
            plannedTasks: allAdjustedTasks.map((t, idx) => ({
                dayDate: todayStr,
                dayLabel: 'Today',
                startTime: idx === 0 ? 'Now' : null,
                executionBadge: idx === 0 ? 'DO THIS FIRST' : 'UP NEXT',
                task: t
            })),
            unarrangedTasks: [],
            tasks: allAdjustedTasks,
            availabilityDays: adjustmentDraft.availabilityDays.length > 0 ? adjustmentDraft.availabilityDays : [
                { date: todayStr, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }
            ]
        };

        adjustmentDraft.proposedPlan = updatedPlan;

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${window.t ? window.t('workspace.adjustPlanStep3', {}, 'STEP 3 OF 3 · CONFIRM UPDATED PLAN') : (isViLocale() ? 'BƯỚC 3/3 · XÁC NHẬN PLAN MỚI' : 'STEP 3 OF 3 · CONFIRM UPDATED PLAN')}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${window.t ? window.t('workspace.proposedUpdatedPlan', {}, 'Proposed Updated Plan') : (isViLocale() ? 'Plan mới được đề xuất' : 'Proposed Updated Plan')}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.renderAdjustmentStep2Tasks()"
                        aria-label="${window.t ? window.t('common.back', {}, 'Back') : (isViLocale() ? 'Quay lại' : 'Back')}"
                        title="${window.t ? window.t('common.back', {}, 'Back') : (isViLocale() ? 'Quay lại' : 'Back')}"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer">
                    ←
                </button>
            </div>

            <p class="text-xs sm:text-sm text-stone-600">
                ${window.t ? window.t('workspace.adjustPlanStep3Desc', {}, 'Here is your updated working plan. Your original plan is preserved until you confirm and save.') : (isViLocale() ? 'Đây là kế hoạch làm việc đã được điều chỉnh. Kế hoạch ban đầu sẽ được giữ nguyên cho đến khi bạn xác nhận và lưu thay đổi.' : 'Here is your updated working plan. Your original plan is preserved until you confirm and save.')}
            </p>

            <div class="max-h-60 overflow-y-auto space-y-2 pr-1 py-1">
                ${allAdjustedTasks.map((t, idx) => {
                    let dueStr = '';
                    if (t.hasDeadline && t.deadlineDate) {
                        const formattedDate = formatStep2DisplayDate(t.deadlineDate);
                        dueStr = `Deadline: ${formattedDate}`;
                    } else {
                        dueStr = window.t ? window.t('workspace.noFixedDeadlineStep3', {}, (isViLocale() ? 'Chưa có deadline cố định' : 'No fixed deadline')) : (isViLocale() ? 'Chưa có deadline cố định' : 'No fixed deadline');
                    }
                    const durLabel = (t.durationMinutes === 90) ? (isViLocale() ? '1,5 giờ' : '1.5 hr') : formatDuration(t.durationMinutes || 30);
                    const badgeText = idx === 0 
                        ? (window.t ? window.t('workspace.doThisFirstUpper', {}, (isViLocale() ? 'LÀM ĐẦU TIÊN' : 'DO THIS FIRST')) : (isViLocale() ? 'LÀM ĐẦU TIÊN' : 'DO THIS FIRST'))
                        : (window.t ? window.t('workspace.upNextUpper', {}, (isViLocale() ? 'TIẾP THEO' : 'UP NEXT')) : (isViLocale() ? 'TIẾP THEO' : 'UP NEXT'));

                    return `
                        <div class="p-3 rounded-2xl border border-stone-200 bg-white flex items-center justify-between text-xs">
                            <div class="flex items-center space-x-2.5 min-w-0 flex-1 mr-2">
                                <span class="font-bold text-stone-400 w-5 shrink-0 text-center">${idx + 1}.</span>
                                <div class="min-w-0">
                                    <span class="font-bold text-stone-800 truncate block">${escapeHTML(t.name || t.title)}</span>
                                    <div class="text-[11px] text-stone-500 flex items-center space-x-2 mt-0.5">
                                        <span>${escapeHTML(dueStr)}</span>
                                        <span>•</span>
                                        <span>~${escapeHTML(durLabel)}</span>
                                    </div>
                                </div>
                            </div>
                            <span class="px-2.5 py-1 rounded-full text-[10px] font-bold ${idx === 0 ? 'bg-[#D79277] text-white' : 'bg-stone-100 text-stone-600'}">
                                ${escapeHTML(badgeText)}
                            </span>
                        </div>
                    `;
                }).join('')}
            </div>

            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-between gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.renderAdjustmentStep2Tasks()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs transition cursor-pointer">
                    ← ${window.t ? window.t('common.back', {}, 'Back') : (isViLocale() ? 'Quay lại' : 'Back')}
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.saveAdjustmentPlan()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm transition cursor-pointer">
                    ${window.t ? window.t('workspace.saveUpdatedPlan', {}, (isViLocale() ? 'Lưu Plan mới →' : 'Save updated plan →')) : (isViLocale() ? 'Lưu Plan mới →' : 'Save updated plan →')}
                </button>
            </div>
        `;

        showModalContent(html);
    }

    function saveAdjustmentPlan() {
        if (!adjustmentDraft.proposedPlan) return;

        const updatedPlan = adjustmentDraft.proposedPlan;

        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            window.TempoPlanStore.saveActivePlan('emergency', updatedPlan);
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
            window.TempoEmergencyFlow.setConfirmedPlan(updatedPlan);
        }

        if (window.TempoMode && typeof window.TempoMode.renderEmodeHome === 'function') {
            window.TempoMode.renderEmodeHome();
        }
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
        }

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("Đã cập nhật và lưu Kế hoạch Làm việc thành công.");
        }

        // Proceed to break-down prompt (Section 4 Step 7)
        showTaskForNowPopupAfterSave(updatedPlan);
    }

    // -------------------------------------------------------------------------
    // PUBLIC API
    // -------------------------------------------------------------------------

    if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
        window.TempoI18n.onLanguageChange(() => {
            if (activeModalView === 'reset') {
                showResetPopup(currentResetCase);
            } else if (activeModalView === 'are_you_ready') {
                showAreYouReadyPopup();
            } else if (activeModalView === 'review_summary') {
                showReviewSummaryPopup();
            } else if (activeModalView === 'keep_plan_task') {
                showKeepPlanTaskPopup();
            } else if (activeModalView === 'adjust_keep') {
                renderAdjustmentStep1Keep();
            } else if (activeModalView === 'adjust_tasks') {
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
            } else if (activeModalView === 'adjust_propose') {
                renderAdjustmentStep3Proposal();
            } else if (activeModalView === 'post_save_task_now') {
                showTaskForNowPopupAfterSave(lastPostSavePlan);
            } else if (activeModalView === 'start_working_plan') {
                showStartWorkingPopup();
            } else if (activeModalView === 'first_task_choice') {
                showFirstTaskExecutionPopup();
            } else if (activeModalView === 'select_another_task') {
                showTaskSelectionPopup();
            } else if (activeModalView === 'breakdown') {
                if (currentBreakdownTaskId) {
                    renderBreakTaskPopup(currentBreakdownTaskId);
                }
            }
        });
    }

    return {
        // Entry Trigger & Session Flags
        queueResetPopup,
        shouldShowReset,
        consumeResetFlag,
        showResetPopup,
        closeModal,

        // Reset Popup Paths
        handleResetYes,
        handleResetNoOrPlan,
        handleResetClose,
        showAreYouReadyPopup,
        handleAreYouReadyYes,
        startSetupFlow,

        // Quick Task Creation
        openQuickTaskModal,
        selectQuickDuration,
        toggleQuickDeadlineInputs,
        handleQuickTaskSubmit,

        // Review & Execution
        showReviewSummaryPopup,
        showKeepPlanTaskPopup,
        launchFocusForTask,
        markOverdueTaskFinished,

        // Breakdown & Start Working
        showTaskForNowPopupAfterSave,
        startBreakTaskFlow,
        renderBreakTaskPopup,
        addSubtask,
        removeSubtask,
        startEditSubtask,
        saveEditSubtask,
        cancelEditSubtask,
        setSubtaskCompleted,
        refreshBreakTaskSubtasks,
        triggerAiHelp,
        applyAiAddMissing,
        applyAiReplaceAll,
        dismissAiNotice,
        generateTaskActionSteps,
        handleBreakMoreTasks,
        viewMyPlan,
        showStartWorkingPopup,
        restartBreakdownFlow,
        showFirstTaskExecutionPopup,
        showTaskSelectionPopup,
        selectWorkTaskAndConfirm,

        // Working Plan Adjustment
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
        handleStep2NewTaskPickerChange,
        updateRetainedDuration,
        updateRetainedDueDate,
        handleAdjustmentStep2Back,
        handleAdjustmentStep2Next,
        addNewAdjustmentTask,
        removeAdjustmentNewTask,
        renderAdjustmentStep3Proposal,
        saveAdjustmentPlan,

        // State & Inspection
        determinePlanCase,
        getActiveWorkingPlan,
        getAllPlanTasks,
        isTaskOverdue,
        isTaskMissedSchedule,
        getTaskState,
        formatScheduledDateLabel,
        getLocalTodayISO,
        formatTaskDuration
    };
})();
